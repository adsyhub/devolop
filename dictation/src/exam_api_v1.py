"""JLPT V1 API Mixin for serve_course.py.

Routes all /api/v1/* requests to ExamEngine and RightsModule with unified error contracts.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import Any
from urllib.parse import SplitResult, parse_qs, unquote

from exam_engine import (
    AnswerVersionConflictError,
    ExamEngine,
    SectionLockedError,
    SessionDeadlinePassedError,
)
from exam_rights import RightsModule, UserRole
from exam_store import check_paper_version_qualification


class ExamV1ApiMixin:
    """Provides /api/v1/* endpoint handling, mixed into RequestHandler."""

    exam_engine: ExamEngine
    rights_module: RightsModule

    def send_v1_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        """Sends unified JSON response."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_v1_error(self, code: str, message: str, status: HTTPStatus, details: dict[str, Any] | None = None) -> None:
        self.send_v1_json(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {},
                }
            },
            status=status,
        )

    def _get_user_id(self) -> str:
        # In local/session mode, use session token as local user id or default learner
        auth = self.headers.get("X-Session-Token") or "local_learner"
        return auth[:64]

    def _get_user_role(self) -> str:
        # Header or default to LEARNER
        return self.headers.get("X-User-Role") or UserRole.LEARNER.value

    # ---- Dispatchers ----

    def handle_exam_v1_get(self, parsed: SplitResult) -> bool:
        path = parsed.path
        if not path.startswith("/api/v1/"):
            return False

        user_id = self._get_user_id()

        # GET /api/v1/exam-time (E05)
        if path == "/api/v1/exam-time":
            from exam_engine import now_utc_iso
            self.send_v1_json({"serverNow": now_utc_iso()})
            return True

        # GET /api/v1/papers
        if path == "/api/v1/papers":
            params = parse_qs(parsed.query)
            level = params.get("level", [None])[0]
            conn = self.exam_engine.db.connection
            if level:
                rows = conn.execute(
                    "SELECT pv.id as paper_version_id, p.id as paper_id, p.title, p.level, p.completeness, pv.version_number "
                    "FROM paper_versions pv JOIN papers p ON p.id = pv.paper_id "
                    "WHERE p.level = ? AND pv.status = 'PUBLISHED'",
                    (level,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT pv.id as paper_version_id, p.id as paper_id, p.title, p.level, p.completeness, pv.version_number "
                    "FROM paper_versions pv JOIN papers p ON p.id = pv.paper_id "
                    "WHERE pv.status = 'PUBLISHED'"
                ).fetchall()
            self.send_v1_json({"papers": [dict(r) for r in rows]})
            return True

        # GET /api/v1/papers/:id (P05 Delivery DTO without answers)
        if path.startswith("/api/v1/papers/"):
            pv_id = unquote(path[len("/api/v1/papers/") :])
            try:
                dto = self.exam_engine.build_delivery_dto(pv_id)
                self.send_v1_json({"paper": dto})
            except KeyError:
                self.send_v1_error("PAPER_NOT_FOUND", f"Paper {pv_id} not found", HTTPStatus.NOT_FOUND)
            return True

        # GET /api/v1/sessions/:id (P02, P03 session state recovery)
        if path.startswith("/api/v1/sessions/") and not path.endswith("/report"):
            session_id = unquote(path[len("/api/v1/sessions/") :])
            try:
                state = self.exam_engine.get_session_state(session_id, user_id)
                self.send_v1_json({"session": state})
            except KeyError:
                self.send_v1_error("SESSION_NOT_FOUND", "Session not found", HTTPStatus.NOT_FOUND)
            except PermissionError as exc:
                self.send_v1_error("FORBIDDEN", str(exc), HTTPStatus.FORBIDDEN)
            return True

        # GET /api/v1/sessions/:id/report (A01~A06)
        if path.startswith("/api/v1/sessions/") and path.endswith("/report"):
            parts = path.split("/")
            session_id = unquote(parts[4])
            conn = self.exam_engine.db.connection
            row = conn.execute("SELECT * FROM result_snapshots WHERE practice_session_id = ?", (session_id,)).fetchone()
            if not row:
                self.send_v1_error("REPORT_NOT_FOUND", "Report not found or session not submitted yet", HTTPStatus.NOT_FOUND)
                return True
            self.send_v1_json({
                "report": {
                    "sessionId": session_id,
                    "correct": row["raw_correct_count"],
                    "total": row["raw_total_count"],
                    "accuracy": row["raw_accuracy"],
                    "scoreSections": json.loads(row["score_sections_json"]),
                    "createdAt": row["created_at"],
                }
            })
            return True

        return False

    def handle_exam_v1_post(self, parsed: SplitResult) -> bool:
        path = parsed.path
        if not path.startswith("/api/v1/"):
            return False

        user_id = self._get_user_id()
        user_role = self._get_user_role()

        # POST /api/v1/sessions (create session)
        if path == "/api/v1/sessions":
            try:
                payload = self.read_learning_json()
                res = self.exam_engine.create_session(
                    user_id=user_id,
                    level=payload.get("level", "N1"),
                    mode=payload.get("mode", "PAPER_PRACTICE"),
                    paper_version_id=payload.get("paperVersionId"),
                )
                self.send_v1_json({"session": res}, status=HTTPStatus.CREATED)
            except ValueError as exc:
                self.send_v1_error("INVALID_ARGUMENT", str(exc), HTTPStatus.BAD_REQUEST)
            except PermissionError as exc:
                self.send_v1_error("RIGHTS_DENIED", str(exc), HTTPStatus.FORBIDDEN)
            return True

        # POST /api/v1/sessions/:id/start
        if path.startswith("/api/v1/sessions/") and path.endswith("/start"):
            session_id = unquote(path.split("/")[4])
            try:
                res = self.exam_engine.start_session(session_id, user_id)
                self.send_v1_json({"started": res})
            except KeyError:
                self.send_v1_error("SESSION_NOT_FOUND", "Session not found", HTTPStatus.NOT_FOUND)
            except PermissionError as exc:
                self.send_v1_error("FORBIDDEN", str(exc), HTTPStatus.FORBIDDEN)
            return True

        # POST /api/v1/sessions/:id/sections/:secCode/submit (E08)
        if "/sections/" in path and path.endswith("/submit"):
            parts = path.split("/")
            session_id = unquote(parts[4])
            sec_code = unquote(parts[6])
            try:
                res = self.exam_engine.submit_section(session_id, user_id, sec_code)
                self.send_v1_json({"sectionSubmit": res})
            except KeyError:
                self.send_v1_error("NOT_FOUND", "Session or section not found", HTTPStatus.NOT_FOUND)
            except PermissionError as exc:
                self.send_v1_error("FORBIDDEN", str(exc), HTTPStatus.FORBIDDEN)
            return True

        # POST /api/v1/sessions/:id/submit (E15 idempotent submit)
        if path.startswith("/api/v1/sessions/") and path.endswith("/submit") and "/sections/" not in path:
            session_id = unquote(path.split("/")[4])
            try:
                res = self.exam_engine.submit_session(session_id, user_id)
                self.send_v1_json({"result": res})
            except KeyError:
                self.send_v1_error("SESSION_NOT_FOUND", "Session not found", HTTPStatus.NOT_FOUND)
            except PermissionError as exc:
                self.send_v1_error("FORBIDDEN", str(exc), HTTPStatus.FORBIDDEN)
            return True

        # POST /api/v1/practice/generate (D01~D09)
        if path == "/api/v1/practice/generate":
            try:
                payload = self.read_learning_json()
                res = self.exam_engine.generate_dynamic_practice(
                    user_id=user_id,
                    level=payload.get("level", "N1"),
                    item_type_codes=payload.get("itemTypeCodes", []),
                    requested_groups=int(payload.get("requestedGroups", 5)),
                    answer_scope=payload.get("answerScope", "ALL"),
                    exclude_recent_days=int(payload.get("excludeRecentDays", 0)),
                )
                self.send_v1_json(res, status=HTTPStatus.CREATED)
            except ValueError as exc:
                self.send_v1_error("INVALID_ARGUMENT", str(exc), HTTPStatus.BAD_REQUEST)
            return True

        # POST /api/v1/review/wrong-redo (A09~A11)
        if path == "/api/v1/review/wrong-redo":
            try:
                payload = self.read_learning_json()
                res = self.exam_engine.create_wrong_redo_session(
                    user_id=user_id,
                    original_session_id=str(payload.get("originalSessionId", "")),
                )
                self.send_v1_json({"session": res}, status=HTTPStatus.CREATED)
            except KeyError:
                self.send_v1_error("SESSION_NOT_FOUND", "Original session not found", HTTPStatus.NOT_FOUND)
            return True

        # POST /api/v1/admin/* (S01)
        if path.startswith("/api/v1/admin/"):
            try:
                self.rights_module.assert_admin_access(user_role)
            except PermissionError as exc:
                self.send_v1_error("ADMIN_FORBIDDEN", str(exc), HTTPStatus.FORBIDDEN)
                return True

            if path == "/api/v1/admin/publish":
                payload = self.read_learning_json()
                pv_id = payload.get("paperVersionId")
                conn = self.exam_engine.db.connection
                row = conn.execute(
                    "SELECT pv.status, p.content_source_id FROM paper_versions pv JOIN papers p ON p.id = pv.paper_id WHERE pv.id = ?",
                    (pv_id,),
                ).fetchone()
                if not row:
                    self.send_v1_error("NOT_FOUND", "Paper version not found", HTTPStatus.NOT_FOUND)
                    return True
                ok, msg = self.rights_module.can_publish(row["content_source_id"])
                if not ok:
                    self.send_v1_error("RIGHTS_NOT_APPROVED", msg, HTTPStatus.UNPROCESSABLE_ENTITY)
                    return True
                qualified, reasons = check_paper_version_qualification(conn, pv_id)
                if not qualified:
                    self.send_v1_error("EXAM_NOT_QUALIFIED", f"Paper version failed qualification checks: {'; '.join(reasons)}", HTTPStatus.UNPROCESSABLE_ENTITY)
                    return True
                if row["status"] != "PUBLISHED":
                    conn.execute("UPDATE paper_versions SET status = 'PUBLISHED' WHERE id = ?", (pv_id,))
                    conn.commit()
                    self.rights_module.log_audit(user_id, "PUBLISH_PAPER", "PAPER_VERSION", pv_id)
                self.send_v1_json({"published": True, "paperVersionId": pv_id})
                return True

            self.send_v1_error("NOT_IMPLEMENTED", "Admin action not recognized", HTTPStatus.NOT_FOUND)
            return True

        return False

    def handle_exam_v1_put(self, parsed: SplitResult) -> bool:
        path = parsed.path
        if not path.startswith("/api/v1/"):
            return False

        user_id = self._get_user_id()

        # PUT /api/v1/sessions/:id/answers/:questionVersionId (P01, E10, S09)
        if "/answers/" in path:
            parts = path.split("/")
            session_id = unquote(parts[4])
            qv_id = unquote(parts[6])
            try:
                payload = self.read_learning_json()
                idempotency_key = self.headers.get("Idempotency-Key") or payload.get("idempotencyKey")
                res = self.exam_engine.record_answer(
                    session_id=session_id,
                    user_id=user_id,
                    question_version_id=qv_id,
                    chosen_option_key=payload.get("chosen"),
                    confidence=str(payload.get("confidence", "")),
                    is_uncertain=bool(payload.get("isUncertain")),
                    idempotency_key=idempotency_key,
                    client_version=int(payload.get("answerVersion", 1)),
                )
                self.send_v1_json(res)
            except KeyError:
                self.send_v1_error("NOT_FOUND", "Session or question not found", HTTPStatus.NOT_FOUND)
            except PermissionError as exc:
                self.send_v1_error("FORBIDDEN", str(exc), HTTPStatus.FORBIDDEN)
            except SectionLockedError as exc:
                self.send_v1_error("SECTION_LOCKED", str(exc), HTTPStatus.FORBIDDEN)
            except SessionDeadlinePassedError as exc:
                self.send_v1_error("SESSION_DEADLINE_PASSED", str(exc), HTTPStatus.BAD_REQUEST)
            except AnswerVersionConflictError as exc:
                self.send_v1_error("ANSWER_VERSION_CONFLICT", str(exc), HTTPStatus.CONFLICT)
            return True

        return False

