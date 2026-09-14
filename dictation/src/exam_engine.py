"""JLPT Question Bank Engine.

Implements:
- Delivery DTO (no answers before submission) & Review DTO (P05, S08)
- Authoritative server-side timer, deadlines, and multi-section state machine (E01~E10, S09)
- Section lock (E08: Section 1 locked once submitted)
- Idempotent submit (E15)
- Autosave with idempotency key and version conflict check (P01)
- Session recovery (P02, P03)
- Dynamic practice generation by question groups (D01~D09)
- Mistake redo with intact reading/listening context (A09, A10, A11)
- Result snapshot and SRS mastery state machine (A01~A06, A12)
- User isolation (S02) and log sanitization (S04, S05)
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from exam_db import ExamDatabase
from exam_models import (
    ITEM_TYPE_MATRIX,
    MasteryStatus,
    PracticeMode,
    ScoreSection,
    TestSection,
    get_blueprint,
    validate_item_type,
    validate_level,
)
from exam_rights import RightsModule

logger = logging.getLogger("exam_engine")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_utc_iso() -> str:
    return now_utc().isoformat(timespec="seconds")


def parse_iso(iso_str: str) -> datetime:
    # Handles ISO formats with Z or +00:00
    cleaned = iso_str.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


class SessionDeadlinePassedError(Exception):
    """E10 / S09: Raised when an answer arrives after the section deadline."""
    pass


class SectionLockedError(Exception):
    """E08: Raised when attempting to write answers to a locked/submitted section."""
    pass


class AnswerVersionConflictError(Exception):
    """Raised when client answerVersion is older than server's current version."""
    pass


class ExamEngine:
    """Core domain service for JLPT examinations and practice sessions."""

    def __init__(self, db: ExamDatabase, rights: RightsModule | None = None) -> None:
        self.db = db
        self.rights = rights or RightsModule(db)

    # =========================================================================
    # 1. Delivery DTO vs Review DTO (P05, S08, R03, R04)
    # =========================================================================

    def build_delivery_dto(self, paper_version_id: str, content_source_id: str | None = None) -> dict[str, Any]:
        """P05 / S08: Builds exam content for study/exam with NO correct answers or explanations."""
        conn = self.db.connection
        p_row = conn.execute(
            "SELECT pv.*, p.level, p.content_source_id, p.completeness FROM paper_versions pv "
            "JOIN papers p ON p.id = pv.paper_id WHERE pv.id = ?",
            (paper_version_id,),
        ).fetchone()
        if not p_row:
            raise KeyError(f"Paper version {paper_version_id} not found.")

        source_id = content_source_id or p_row["content_source_id"]

        sections = []
        s_rows = conn.execute(
            "SELECT * FROM paper_sections WHERE paper_version_id = ? ORDER BY display_order",
            (paper_version_id,),
        ).fetchall()

        for s in s_rows:
            parts = []
            pt_rows = conn.execute(
                "SELECT * FROM paper_parts WHERE paper_section_id = ? ORDER BY display_order",
                (s["id"],),
            ).fetchall()

            for pt in pt_rows:
                blocks = []
                b_rows = conn.execute(
                    "SELECT pb.*, qgv.instruction_text, qg.item_type_code, qg.learning_subject "
                    "FROM paper_blocks pb "
                    "JOIN question_group_versions qgv ON qgv.id = pb.question_group_version_id "
                    "JOIN question_groups qg ON qg.id = qgv.question_group_id "
                    "WHERE pb.paper_part_id = ? ORDER BY pb.display_order",
                    (pt["id"],),
                ).fetchall()

                for b in b_rows:
                    qgv_id = b["question_group_version_id"]
                    # Load materials
                    mats = []
                    m_rows = conn.execute(
                        "SELECT mv.*, qgm.usage_type, m.material_type FROM question_group_materials qgm "
                        "JOIN material_versions mv ON mv.id = qgm.material_version_id "
                        "JOIN materials m ON m.id = mv.material_id "
                        "WHERE qgm.question_group_version_id = ? ORDER BY qgm.display_order",
                        (qgv_id,),
                    ).fetchall()
                    for m in m_rows:
                        mats.append({
                            "materialId": m["material_id"],
                            "materialType": m["material_type"],
                            "plainText": m["plain_text"],
                            "contentAst": json.loads(m["content_ast_json"]),
                            "usageType": m["usage_type"],
                        })

                    # Load questions (CRITICAL: ZERO ANSWERS)
                    qs = []
                    q_rows = conn.execute(
                        "SELECT qv.*, q.id as question_id FROM question_versions qv "
                        "JOIN questions q ON q.id = qv.question_id "
                        "WHERE qv.question_group_version_id = ? ORDER BY qv.display_order",
                        (qgv_id,),
                    ).fetchall()

                    for q in q_rows:
                        # Load options without is_correct flag
                        opts = []
                        opt_rows = conn.execute(
                            "SELECT option_key, display_order, content_text FROM option_versions "
                            "WHERE question_version_id = ? ORDER BY display_order",
                            (q["id"],),
                        ).fetchall()
                        for opt in opt_rows:
                            opts.append({
                                "optionKey": opt["option_key"],
                                "displayOrder": opt["display_order"],
                                "contentText": opt["content_text"],
                            })

                        qs.append({
                            "questionId": q["question_id"],
                            "questionVersionId": q["id"],
                            "displayOrder": q["display_order"],
                            "stemText": q["stem_text"],
                            "stemAst": json.loads(q["stem_ast_json"]),
                            "options": opts,
                        })

                    blocks.append({
                        "questionGroupVersionId": qgv_id,
                        "itemTypeCode": b["item_type_code"],
                        "learningSubject": b["learning_subject"],
                        "instructionText": b["instruction_text"],
                        "materials": mats,
                        "questions": qs,
                    })

                parts.append({
                    "partId": pt["id"],
                    "partCode": pt["part_code"],
                    "title": pt["title"],
                    "itemTypeCode": pt["item_type_code"],
                    "blocks": blocks,
                })

            sections.append({
                "sectionId": s["id"],
                "sectionCode": s["section_code"],
                "displayOrder": s["display_order"],
                "timeLimitSec": s["time_limit_sec"],
                "parts": parts,
            })

        dto = {
            "paperVersionId": p_row["id"],
            "title": p_row["title"],
            "level": p_row["level"],
            "completeness": p_row["completeness"],
            "sections": sections,
        }
        # Apply rights sanitization (R03/R04)
        return self.rights.sanitize_delivery_dto(dto, source_id)

    # =========================================================================
    # 2. Session Lifecycle & Authoritative Countdown (P01~P04, E01~E10, E16)
    # =========================================================================

    def create_session(
        self,
        user_id: str,
        level: str,
        mode: str,
        paper_version_id: str | None = None,
        source_scope: str = "",
    ) -> dict[str, Any]:
        """Creates a session and freezes question group snapshots (V02, V03, V04, D08)."""
        lvl = validate_level(level)
        conn = self.db.connection

        # If paper given, check source rights (R02)
        if paper_version_id:
            p_row = conn.execute(
                "SELECT p.content_source_id FROM paper_versions pv "
                "JOIN papers p ON p.id = pv.paper_id WHERE pv.id = ?",
                (paper_version_id,),
            ).fetchone()
            if not p_row:
                raise KeyError(f"Paper version {paper_version_id} not found.")
            can_start, reason = self.rights.can_start_session(p_row["content_source_id"])
            if not can_start:
                raise PermissionError(f"Cannot start session: {reason}")

        session_id = uuid.uuid4().hex
        now = now_utc_iso()
        bp = get_blueprint(lvl)

        conn.execute(
            "INSERT INTO practice_sessions (id, user_id, level, mode, paper_version_id, status, "
            "random_seed, selection_algorithm_version, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'INITIALIZED', ?, 'v1', ?, ?)",
            (session_id, user_id, lvl, mode, paper_version_id, random.randint(10000, 99999), now, now),
        )

        # Initialize session sections based on blueprint
        for bps in bp.sections:
            sec_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO session_sections (id, practice_session_id, section_code, display_order, status) "
                "VALUES (?, ?, ?, ?, 'PENDING')",
                (sec_id, session_id, bps.section_code.value, bps.display_order),
            )

        # Freeze group snapshots if a paper is provided
        if paper_version_id:
            s_rows = conn.execute(
                "SELECT id, section_code FROM session_sections WHERE practice_session_id = ? ORDER BY display_order",
                (session_id,),
            ).fetchall()
            sec_map = {r["section_code"]: r["id"] for r in s_rows}

            # Find all blocks in the paper
            blocks = conn.execute(
                "SELECT pb.question_group_version_id, ps.section_code FROM paper_blocks pb "
                "JOIN paper_parts pp ON pp.id = pb.paper_part_id "
                "JOIN paper_sections ps ON ps.id = pp.paper_section_id "
                "WHERE ps.paper_version_id = ? ORDER BY pb.display_order",
                (paper_version_id,),
            ).fetchall()

            for idx, b in enumerate(blocks):
                snap_id = uuid.uuid4().hex
                ss_id = sec_map.get(b["section_code"], s_rows[0]["id"])
                # Fetch question ids
                q_ids = [
                    r["id"]
                    for r in conn.execute(
                        "SELECT id FROM question_versions WHERE question_group_version_id = ? ORDER BY display_order",
                        (b["question_group_version_id"],),
                    )
                ]
                conn.execute(
                    "INSERT INTO session_group_snapshots (id, practice_session_id, session_section_id, "
                    "question_group_version_id, display_order, required_question_ids_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (snap_id, session_id, ss_id, b["question_group_version_id"], idx + 1, json.dumps(q_ids), now),
                )

        conn.commit()
        return {"sessionId": session_id, "status": "INITIALIZED", "level": lvl, "mode": mode}

    def start_session(self, session_id: str, user_id: str) -> dict[str, Any]:
        """E01~E04, E16: Starts the session, initializes Section 1 authoritative deadline."""
        conn = self.db.connection
        s_row = conn.execute("SELECT * FROM practice_sessions WHERE id = ?", (session_id,)).fetchone()
        if not s_row:
            raise KeyError(session_id)
        if s_row["user_id"] != user_id:
            raise PermissionError("Access denied: session belongs to another user (S02).")

        now = now_utc()
        now_str = now.isoformat(timespec="seconds")
        bp = get_blueprint(s_row["level"])

        # First section
        first_sec = conn.execute(
            "SELECT * FROM session_sections WHERE practice_session_id = ? ORDER BY display_order ASC LIMIT 1",
            (session_id,),
        ).fetchone()

        s1_bp = bp.sections[0]
        deadline = now + timedelta(seconds=s1_bp.time_limit_sec)
        deadline_str = deadline.isoformat(timespec="seconds")

        # Lease token for multi-tab check (E16)
        lease_token = uuid.uuid4().hex

        conn.execute(
            "UPDATE session_sections SET status = 'IN_PROGRESS', started_at = ?, deadline_at = ? WHERE id = ?",
            (now_str, deadline_str, first_sec["id"]),
        )
        conn.execute(
            "UPDATE practice_sessions SET status = 'IN_PROGRESS', started_at = ?, active_lease_token = ?, updated_at = ? "
            "WHERE id = ?",
            (now_str, lease_token, now_str, session_id),
        )
        conn.commit()

        return {
            "sessionId": session_id,
            "status": "IN_PROGRESS",
            "activeLeaseToken": lease_token,
            "currentSection": first_sec["section_code"],
            "startedAt": now_str,
            "deadlineAt": deadline_str,
            "remainingSec": s1_bp.time_limit_sec,
            "serverNow": now_str,
        }

    def get_session_state(self, session_id: str, user_id: str) -> dict[str, Any]:
        """P02, P03, E05, E06, E07: Authoritative state, remaining time, answers recovery."""
        conn = self.db.connection
        s_row = conn.execute("SELECT * FROM practice_sessions WHERE id = ?", (session_id,)).fetchone()
        if not s_row:
            raise KeyError(session_id)
        if s_row["user_id"] != user_id:
            raise PermissionError("Access denied: session belongs to another user (S02).")

        server_now = now_utc()
        server_now_str = server_now.isoformat(timespec="seconds")

        # Load active section
        sec_rows = conn.execute(
            "SELECT * FROM session_sections WHERE practice_session_id = ? ORDER BY display_order",
            (session_id,),
        ).fetchall()

        active_sec = None
        for sec in sec_rows:
            if sec["status"] == "IN_PROGRESS":
                active_sec = sec
                break

        remaining_sec = 0
        if active_sec and active_sec["deadline_at"]:
            deadline = parse_iso(active_sec["deadline_at"])
            remaining_sec = max(0, int((deadline - server_now).total_seconds()))

        # Load answers
        answers_rows = conn.execute(
            "SELECT * FROM answer_records WHERE practice_session_id = ?",
            (session_id,),
        ).fetchall()

        answers_map = {}
        for a in answers_rows:
            answers_map[a["question_version_id"]] = {
                "chosen": a["chosen_option_key"],
                "isUncertain": bool(a["is_uncertain"]),
                "confidence": a["confidence"],
                "version": a["version"],
                "lastAnsweredAt": a["last_answered_at"],
            }

        return {
            "sessionId": session_id,
            "status": s_row["status"],
            "level": s_row["level"],
            "mode": s_row["mode"],
            "serverNow": server_now_str,
            "activeSection": dict(active_sec) if active_sec else None,
            "remainingSec": remaining_sec,
            "answers": answers_map,
            "sections": [dict(s) for s in sec_rows],
        }

    # =========================================================================
    # 3. Answer Recording, Validation & Optimistic Locking (P01, E08, E10, S09)
    # =========================================================================

    def record_answer(
        self,
        session_id: str,
        user_id: str,
        question_version_id: str,
        chosen_option_key: int | None,
        confidence: str = "",
        is_uncertain: bool = False,
        idempotency_key: str | None = None,
        client_version: int = 1,
    ) -> dict[str, Any]:
        """P01, E08, E10, S09: Saves an answer with deadline check and optimistic locking."""
        conn = self.db.connection
        s_row = conn.execute("SELECT * FROM practice_sessions WHERE id = ?", (session_id,)).fetchone()
        if not s_row:
            raise KeyError(session_id)
        if s_row["user_id"] != user_id:
            raise PermissionError("Access denied (S02).")

        now = now_utc()
        now_str = now.isoformat(timespec="seconds")

        # Find which section this question belongs to
        q_sec = conn.execute(
            "SELECT ss.* FROM session_sections ss "
            "JOIN session_group_snapshots sgs ON sgs.session_section_id = ss.id "
            "JOIN question_versions qv ON qv.question_group_version_id = sgs.question_group_version_id "
            "WHERE ss.practice_session_id = ? AND qv.id = ?",
            (session_id, question_version_id),
        ).fetchone()

        if q_sec:
            # E08: Check if section locked
            if q_sec["status"] == "SUBMITTED":
                raise SectionLockedError("Cannot modify answers for an already submitted section (E08).")

            # E10 / S09: Authoritative deadline check for strict exam
            if s_row["mode"] == PracticeMode.STRICT_EXAM.value and q_sec["deadline_at"]:
                deadline = parse_iso(q_sec["deadline_at"])
                if now > deadline:
                    raise SessionDeadlinePassedError(
                        f"Deadline passed at {q_sec['deadline_at']}; answer rejected by server (E10)."
                    )

        # Optimistic concurrency / version check (P01)
        existing = conn.execute(
            "SELECT * FROM answer_records WHERE practice_session_id = ? AND question_version_id = ?",
            (session_id, question_version_id),
        ).fetchone()

        new_version = 1
        if existing:
            current_version = int(existing["version"])
            if client_version < current_version:
                raise AnswerVersionConflictError(
                    f"Answer version conflict: client={client_version}, server={current_version}."
                )
            new_version = current_version + 1

        rec_id = existing["id"] if existing else uuid.uuid4().hex
        first_answered = existing["first_answered_at"] if existing else now_str

        conn.execute(
            "INSERT INTO answer_records (id, practice_session_id, question_version_id, chosen_option_key, "
            "is_uncertain, confidence, version, first_answered_at, last_answered_at, server_received_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(practice_session_id, question_version_id) DO UPDATE SET "
            "chosen_option_key = excluded.chosen_option_key, "
            "is_uncertain = excluded.is_uncertain, "
            "confidence = excluded.confidence, "
            "version = excluded.version, "
            "last_answered_at = excluded.last_answered_at, "
            "server_received_at = excluded.server_received_at",
            (
                rec_id,
                session_id,
                question_version_id,
                chosen_option_key,
                1 if is_uncertain else 0,
                confidence,
                new_version,
                first_answered,
                now_str,
                now_str,
            ),
        )

        # Log answer event (idempotency key) (S05 sanitized)
        payload_hash = hashlib.sha256(f"{chosen_option_key}:{confidence}:{is_uncertain}".encode()).hexdigest()
        event_id = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO answer_events (id, practice_session_id, question_version_id, event_type, "
            "payload_hash, idempotency_key, client_time, server_time, created_at) "
            "VALUES (?, ?, ?, 'ANSWER_SAVE', ?, ?, ?, ?, ?)",
            (event_id, session_id, question_version_id, payload_hash, idempotency_key or "", now_str, now_str, now_str),
        )
        conn.commit()

        # Note S05: Log event without including raw answer text
        logger.info("Answer recorded: session=%s question=%s version=%d", session_id, question_version_id, new_version)

        return {
            "saved": True,
            "questionVersionId": question_version_id,
            "serverVersion": new_version,
            "serverReceivedAt": now_str,
        }

    # =========================================================================
    # 4. Multi-Section State Machine & Submission (E08, E15, A01~A05, A12)
    # =========================================================================

    def submit_section(self, session_id: str, user_id: str, section_code: str) -> dict[str, Any]:
        """E08: Locks the current section, transitions to next section if present."""
        conn = self.db.connection
        s_row = conn.execute("SELECT * FROM practice_sessions WHERE id = ?", (session_id,)).fetchone()
        if not s_row:
            raise KeyError(session_id)
        if s_row["user_id"] != user_id:
            raise PermissionError("Access denied (S02).")

        now = now_utc()
        now_str = now.isoformat(timespec="seconds")
        bp = get_blueprint(s_row["level"])

        sec = conn.execute(
            "SELECT * FROM session_sections WHERE practice_session_id = ? AND section_code = ?",
            (session_id, section_code),
        ).fetchone()
        if not sec:
            raise KeyError(f"Section {section_code} not in session.")

        # Lock this section
        conn.execute(
            "UPDATE session_sections SET status = 'SUBMITTED', submitted_at = ? WHERE id = ?",
            (now_str, sec["id"]),
        )

        # Check if next section exists
        next_sec = conn.execute(
            "SELECT * FROM session_sections WHERE practice_session_id = ? AND display_order > ? ORDER BY display_order ASC LIMIT 1",
            (session_id, sec["display_order"]),
        ).fetchone()

        next_info = None
        if next_sec:
            # Look up blueprint duration for next section
            sec_bp = next(b for b in bp.sections if b.section_code.value == next_sec["section_code"])
            deadline = now + timedelta(seconds=sec_bp.time_limit_sec)
            deadline_str = deadline.isoformat(timespec="seconds")

            conn.execute(
                "UPDATE session_sections SET status = 'IN_PROGRESS', started_at = ?, deadline_at = ? WHERE id = ?",
                (now_str, deadline_str, next_sec["id"]),
            )
            next_info = {
                "sectionCode": next_sec["section_code"],
                "startedAt": now_str,
                "deadlineAt": deadline_str,
                "remainingSec": sec_bp.time_limit_sec,
            }
        conn.commit()

        return {
            "sectionCode": section_code,
            "locked": True,
            "submittedAt": now_str,
            "nextSection": next_info,
        }

    def submit_session(self, session_id: str, user_id: str) -> dict[str, Any]:
        """E15, A01~A05, A12: Idempotent session submission and ResultSnapshot computation."""
        conn = self.db.connection
        s_row = conn.execute("SELECT * FROM practice_sessions WHERE id = ?", (session_id,)).fetchone()
        if not s_row:
            raise KeyError(session_id)
        if s_row["user_id"] != user_id:
            raise PermissionError("Access denied (S02).")

        # E15 Idempotent check: if already submitted, return the existing result snapshot
        existing_snapshot = conn.execute(
            "SELECT * FROM result_snapshots WHERE practice_session_id = ?",
            (session_id,),
        ).fetchone()
        if existing_snapshot:
            return {
                "sessionId": session_id,
                "alreadySubmitted": True,
                "submittedAt": s_row["submitted_at"],
                "score": json.loads(existing_snapshot["score_sections_json"]),
                "totals": {
                    "correct": existing_snapshot["raw_correct_count"],
                    "total": existing_snapshot["raw_total_count"],
                    "accuracy": existing_snapshot["raw_accuracy"],
                },
            }

        now_str = now_utc_iso()

        # Load all answers and question keys
        answers = {
            r["question_version_id"]: r["chosen_option_key"]
            for r in conn.execute(
                "SELECT question_version_id, chosen_option_key FROM answer_records WHERE practice_session_id = ?",
                (session_id,),
            )
        }

        # Load all question versions in this session snapshot
        q_rows = conn.execute(
            "SELECT qv.id as qv_id, qv.question_id, qv.correct_answer_json, qg.learning_subject, qg.item_type_code "
            "FROM session_group_snapshots sgs "
            "JOIN question_versions qv ON qv.question_group_version_id = sgs.question_group_version_id "
            "JOIN question_group_versions qgv ON qgv.id = sgs.question_group_version_id "
            "JOIN question_groups qg ON qg.id = qgv.question_group_id "
            "WHERE sgs.practice_session_id = ?",
            (session_id,),
        ).fetchall()

        # Scoring categorized by ScoreSection (A01)
        score_by_section: dict[str, dict[str, Any]] = {
            ScoreSection.LANGUAGE_KNOWLEDGE.value: {"correct": 0, "total": 0, "points": 0.0},
            ScoreSection.READING.value: {"correct": 0, "total": 0, "points": 0.0},
            ScoreSection.LISTENING.value: {"correct": 0, "total": 0, "points": 0.0},
        }

        total_correct = 0
        total_questions = len(q_rows)

        # Fold answers into user_question_states (A12 SRS)
        for q in q_rows:
            qv_id = q["qv_id"]
            question_id = q["question_id"]
            correct_key = int(json.loads(q["correct_answer_json"]).get("answer", 1))
            chosen = answers.get(qv_id)
            is_correct = chosen is not None and (chosen == correct_key)

            if is_correct:
                total_correct += 1

            # Map to score section
            spec = ITEM_TYPE_MATRIX.get(q["item_type_code"])
            sec_name = spec.score_section.value if spec else ScoreSection.LANGUAGE_KNOWLEDGE.value
            score_by_section[sec_name]["total"] += 1
            if is_correct:
                score_by_section[sec_name]["correct"] += 1
                score_by_section[sec_name]["points"] += 1.0

            # Update SRS Mastery State Machine (A12)
            self._update_user_srs_state(user_id, question_id, is_correct, chosen is None)

        accuracy = round((total_correct / total_questions * 100), 2) if total_questions > 0 else 0.0

        # Save immutable result snapshot
        snap_id = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO result_snapshots (id, practice_session_id, calculation_version, raw_correct_count, "
            "raw_total_count, raw_accuracy, score_sections_json, item_type_stats_json, time_stats_json, created_at) "
            "VALUES (?, ?, 'v1', ?, ?, ?, ?, '{}', '{}', ?)",
            (snap_id, session_id, total_correct, total_questions, accuracy, json.dumps(score_by_section), now_str),
        )

        conn.execute(
            "UPDATE practice_sessions SET status = 'SUBMITTED', submitted_at = ?, updated_at = ? WHERE id = ?",
            (now_str, now_str, session_id),
        )
        conn.commit()

        return {
            "sessionId": session_id,
            "alreadySubmitted": False,
            "submittedAt": now_str,
            "score": score_by_section,
            "totals": {
                "correct": total_correct,
                "total": total_questions,
                "accuracy": accuracy,
            },
        }

    # =========================================================================
    # 5. SRS State Machine (A12, 20.1)
    # =========================================================================

    def _update_user_srs_state(self, user_id: str, question_id: str, is_correct: bool, is_skipped: bool) -> None:
        """A12: NEW_WRONG -> WRONG_AGAIN -> CORRECT_ON_REDO -> STABILIZING -> MASTERED."""
        conn = self.db.connection
        now_str = now_utc_iso()
        row = conn.execute(
            "SELECT * FROM user_question_states WHERE user_id = ? AND question_id = ?",
            (user_id, question_id),
        ).fetchone()

        attempt_count = (row["attempt_count"] if row else 0) + 1
        correct_count = (row["correct_count"] if row else 0) + (1 if is_correct else 0)
        wrong_count = (row["wrong_count"] if row else 0) + (1 if (not is_correct and not is_skipped) else 0)
        streak = row["streak"] if row else 0
        current_mastery = row["mastery_status"] if row else ""

        if is_skipped:
            new_mastery = current_mastery or MasteryStatus.NEW_WRONG.value
            streak = 0
            interval_days = 1
        elif is_correct:
            streak += 1
            if current_mastery in ("", MasteryStatus.NEW_WRONG.value, MasteryStatus.WRONG_AGAIN.value):
                new_mastery = MasteryStatus.CORRECT_ON_REDO.value
                interval_days = 2
            elif current_mastery == MasteryStatus.CORRECT_ON_REDO.value:
                new_mastery = MasteryStatus.STABILIZING.value
                interval_days = 7
            else:
                new_mastery = MasteryStatus.MASTERED.value
                interval_days = 30
        else:
            streak = 0
            new_mastery = MasteryStatus.WRONG_AGAIN.value if current_mastery else MasteryStatus.NEW_WRONG.value
            interval_days = 1

        next_review = (now_utc() + timedelta(days=interval_days)).isoformat(timespec="seconds")

        first_at = row["first_attempt_at"] if row else now_str
        conn.execute(
            "INSERT INTO user_question_states (user_id, question_id, first_attempt_at, last_attempt_at, "
            "attempt_count, correct_count, wrong_count, last_result, mastery_status, streak, next_review_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, question_id) DO UPDATE SET "
            "last_attempt_at = excluded.last_attempt_at, "
            "attempt_count = excluded.attempt_count, "
            "correct_count = excluded.correct_count, "
            "wrong_count = excluded.wrong_count, "
            "last_result = excluded.last_result, "
            "mastery_status = excluded.mastery_status, "
            "streak = excluded.streak, "
            "next_review_at = excluded.next_review_at, "
            "updated_at = excluded.updated_at",
            (
                user_id,
                question_id,
                first_at,
                now_str,
                attempt_count,
                correct_count,
                wrong_count,
                "correct" if is_correct else ("skipped" if is_skipped else "wrong"),
                new_mastery,
                streak,
                next_review,
                now_str,
            ),
        )

    # =========================================================================
    # 6. Dynamic Practice Generation (D01~D09)
    # =========================================================================

    def generate_dynamic_practice(
        self,
        user_id: str,
        level: str,
        item_type_codes: list[str],
        requested_groups: int = 5,
        answer_scope: str = "ALL",  # UNSEEN, WRONG, DUE, ALL
        exclude_recent_days: int = 0,
    ) -> dict[str, Any]:
        """D01~D09: Assembles dynamic practice by full question group without splitting."""
        lvl = validate_level(level)
        conn = self.db.connection

        # Validate item types
        for code in item_type_codes:
            validate_item_type(lvl, code)

        # Query eligible published question group versions
        placeholders = ",".join("?" for _ in item_type_codes)
        sql = (
            f"SELECT qgv.id as qgv_id, qg.id as qg_id, qg.item_type_code, qg.learning_subject "
            f"FROM question_group_versions qgv "
            f"JOIN question_groups qg ON qg.id = qgv.question_group_id "
            f"WHERE qg.level = ? AND qg.item_type_code IN ({placeholders}) "
            f"AND qgv.status = 'PUBLISHED' "
            f"ORDER BY qgv.created_at DESC"
        )
        params: list[Any] = [lvl] + list(item_type_codes)
        candidates = conn.execute(sql, params).fetchall()

        # Filter by exclude_recent_days (D06)
        if exclude_recent_days > 0:
            cutoff = (now_utc() - timedelta(days=exclude_recent_days)).isoformat(timespec="seconds")
            recent_qgs = {
                r["question_group_id"]
                for r in conn.execute(
                    "SELECT DISTINCT q.question_group_id FROM user_question_states uqs "
                    "JOIN questions q ON q.id = uqs.question_id "
                    "WHERE uqs.user_id = ? AND uqs.last_attempt_at >= ?",
                    (user_id, cutoff),
                )
            }
            candidates = [c for c in candidates if c["qg_id"] not in recent_qgs]

        # Filter by answer_scope (D03, D04, D05)
        if answer_scope == "UNSEEN":
            seen_qgs = {
                r["question_group_id"]
                for r in conn.execute(
                    "SELECT DISTINCT q.question_group_id FROM user_question_states uqs "
                    "JOIN questions q ON q.id = uqs.question_id WHERE uqs.user_id = ?",
                    (user_id,),
                )
            }
            candidates = [c for c in candidates if c["qg_id"] not in seen_qgs]
        elif answer_scope == "WRONG":
            wrong_qgs = {
                r["question_group_id"]
                for r in conn.execute(
                    "SELECT DISTINCT q.question_group_id FROM user_question_states uqs "
                    "JOIN questions q ON q.id = uqs.question_id WHERE uqs.user_id = ? AND uqs.wrong_count > 0",
                    (user_id,),
                )
            }
            candidates = [c for c in candidates if c["qg_id"] in wrong_qgs]
        elif answer_scope == "DUE":
            today_str = now_utc_iso()
            due_qgs = {
                r["question_group_id"]
                for r in conn.execute(
                    "SELECT DISTINCT q.question_group_id FROM user_question_states uqs "
                    "JOIN questions q ON q.id = uqs.question_id WHERE uqs.user_id = ? AND uqs.next_review_at <= ?",
                    (user_id, today_str),
                )
            }
            candidates = [c for c in candidates if c["qg_id"] in due_qgs]

        warnings = []
        # D07 / D09: If insufficient, return warning, DO NOT synthesize fake questions!
        if len(candidates) < requested_groups:
            warnings.append({
                "code": "INSUFFICIENT_QUESTION_GROUPS",
                "message": f"Requested {requested_groups} groups, but only {len(candidates)} matched filter.",
                "requested": requested_groups,
                "available": len(candidates),
            })

        chosen_groups = candidates[:requested_groups]

        # Create session with frozen snapshot (D01, D02, D08)
        session_id = uuid.uuid4().hex
        now_str = now_utc_iso()
        conn.execute(
            "INSERT INTO practice_sessions (id, user_id, level, mode, status, random_seed, selection_algorithm_version, created_at, updated_at) "
            "VALUES (?, ?, ?, 'ITEM_TYPE_PRACTICE', 'INITIALIZED', ?, 'v1', ?, ?)",
            (session_id, user_id, lvl, random.randint(1000, 9999), now_str, now_str),
        )

        sec_id = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO session_sections (id, practice_session_id, section_code, display_order, status) "
            "VALUES (?, ?, 'PRACTICE_SECTION', 1, 'IN_PROGRESS')",
            (sec_id, session_id),
        )

        for idx, g in enumerate(chosen_groups):
            snap_id = uuid.uuid4().hex
            q_ids = [
                r["id"]
                for r in conn.execute(
                    "SELECT id FROM question_versions WHERE question_group_version_id = ? ORDER BY display_order",
                    (g["qgv_id"],),
                )
            ]
            conn.execute(
                "INSERT INTO session_group_snapshots (id, practice_session_id, session_section_id, "
                "question_group_version_id, display_order, required_question_ids_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (snap_id, session_id, sec_id, g["qgv_id"], idx + 1, json.dumps(q_ids), now_str),
            )

        conn.commit()
        return {
            "sessionId": session_id,
            "status": "INITIALIZED",
            "selectedGroupCount": len(chosen_groups),
            "warnings": warnings,
        }

    # =========================================================================
    # 7. Mistake Redo Session (A09, A10, A11)
    # =========================================================================

    def create_wrong_redo_session(self, user_id: str, original_session_id: str) -> dict[str, Any]:
        """A09~A11: Creates a new session for wrong answers with intact question group context."""
        conn = self.db.connection
        orig = conn.execute("SELECT * FROM practice_sessions WHERE id = ?", (original_session_id,)).fetchone()
        if not orig:
            raise KeyError(original_session_id)

        # Find questions user got wrong in original session
        wrong_qvs = []
        for r in conn.execute(
            "SELECT qv.id, qv.correct_answer_json, ar.chosen_option_key, sgs.question_group_version_id "
            "FROM answer_records ar "
            "JOIN question_versions qv ON qv.id = ar.question_version_id "
            "JOIN session_group_snapshots sgs ON sgs.question_group_version_id = qv.question_group_version_id "
            "WHERE ar.practice_session_id = ? AND sgs.practice_session_id = ?",
            (original_session_id, original_session_id),
        ):
            correct = int(json.loads(r["correct_answer_json"]).get("answer", 1))
            if r["chosen_option_key"] is None or r["chosen_option_key"] != correct:
                wrong_qvs.append(r)

        # Unique group versions containing mistakes
        needed_groups = sorted(list({r["question_group_version_id"] for r in wrong_qvs}))

        # A09: Create a brand new session, DO NOT overwrite original session
        session_id = uuid.uuid4().hex
        now_str = now_utc_iso()
        conn.execute(
            "INSERT INTO practice_sessions (id, user_id, level, mode, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'WRONG_REDO', 'INITIALIZED', ?, ?)",
            (session_id, user_id, orig["level"], now_str, now_str),
        )

        sec_id = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO session_sections (id, practice_session_id, section_code, display_order, status) "
            "VALUES (?, ?, 'REDO_SECTION', 1, 'IN_PROGRESS')",
            (sec_id, session_id),
        )

        # A10, A11: Keep full group intact
        for idx, g_id in enumerate(needed_groups):
            snap_id = uuid.uuid4().hex
            q_ids = [
                r["id"]
                for r in conn.execute(
                    "SELECT id FROM question_versions WHERE question_group_version_id = ? ORDER BY display_order",
                    (g_id,),
                )
            ]
            conn.execute(
                "INSERT INTO session_group_snapshots (id, practice_session_id, session_section_id, "
                "question_group_version_id, display_order, required_question_ids_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (snap_id, session_id, sec_id, g_id, idx + 1, json.dumps(q_ids), now_str),
            )

        conn.commit()
        return {
            "sessionId": session_id,
            "originalSessionId": original_session_id,
            "mode": "WRONG_REDO",
            "groupCount": len(needed_groups),
        }

