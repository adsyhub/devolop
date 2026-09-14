"""Local-only SQLite backend for the learner's personal vocab notebook, notes, and study streak.

This is an optional companion to the static PWA player: `web/app.js` keeps working purely
from `localStorage` when this backend is absent (static hosting, offline use). When the
player happens to be opened through `serve_course.py` (same-origin `/api/*`), the frontend
also mirrors vocab/notes/activity writes here so a personal notebook can span multiple course
previews instead of being siloed per static-site origin.
"""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import SplitResult, unquote

MAX_JSON_BODY = 64 * 1024

SCHEMA = """
CREATE TABLE IF NOT EXISTS vocab (
    id TEXT PRIMARY KEY,
    term TEXT NOT NULL,
    reading TEXT,
    meaning TEXT,
    note TEXT,
    course_id TEXT,
    sentence_id TEXT,
    source_text TEXT,
    mastered INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    sentence_id TEXT NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    starred INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(course_id, sentence_id)
);

CREATE TABLE IF NOT EXISTS streak (
    day TEXT PRIMARY KEY
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningStore:
    """Owns a single SQLite file holding vocab, per-sentence notes, and study-activity days."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.lock = threading.RLock()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(db_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.connection = self._connection
        with self.lock:
            self._connection.executescript(SCHEMA)
            self._connection.commit()

    def close(self) -> None:
        with self.lock:
            self._connection.close()

    # ---- vocab ----

    def list_vocab(self) -> list[dict[str, Any]]:
        with self.lock:
            rows = self._connection.execute("SELECT * FROM vocab ORDER BY created_at DESC").fetchall()
            return [_row_to_vocab(row) for row in rows]

    def create_vocab(self, payload: dict[str, Any]) -> dict[str, Any]:
        term = _field_or_existing(payload, "term", None, "term", max_length=500)
        if not term:
            raise ValueError("term is required.")
        reading = _field_or_existing(payload, "reading", None, "reading")
        meaning = _field_or_existing(payload, "meaning", None, "meaning")
        note = _field_or_existing(payload, "note", None, "note")
        course_id = _field_or_existing(payload, "courseId", None, "course_id", max_length=200)
        sentence_id = _field_or_existing(payload, "sentenceId", None, "sentence_id", max_length=200)
        source_text = _field_or_existing(payload, "sourceText", None, "source_text", max_length=2000)
        entry_id = f"v_{secrets.token_hex(12)}"
        timestamp = now_iso()
        with self.lock:
            self._connection.execute(
                """
                INSERT INTO vocab
                    (id, term, reading, meaning, note, course_id, sentence_id, source_text, mastered, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (entry_id, term, reading, meaning, note, course_id, sentence_id, source_text, timestamp, timestamp),
            )
            self._connection.commit()
            return self._get_vocab(entry_id)

    def update_vocab(self, entry_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            existing = self._connection.execute("SELECT * FROM vocab WHERE id = ?", (entry_id,)).fetchone()
            if existing is None:
                raise KeyError(entry_id)
            term = _field_or_existing(payload, "term", existing, "term", max_length=500)
            if not term:
                raise ValueError("term is required.")
            reading = _field_or_existing(payload, "reading", existing, "reading")
            meaning = _field_or_existing(payload, "meaning", existing, "meaning")
            note = _field_or_existing(payload, "note", existing, "note")
            mastered = bool(payload["mastered"]) if "mastered" in payload else bool(existing["mastered"])
            self._connection.execute(
                """
                UPDATE vocab SET term = ?, reading = ?, meaning = ?, note = ?, mastered = ?, updated_at = ?
                WHERE id = ?
                """,
                (term, reading, meaning, note, 1 if mastered else 0, now_iso(), entry_id),
            )
            self._connection.commit()
            return self._get_vocab(entry_id)

    def delete_vocab(self, entry_id: str) -> None:
        with self.lock:
            cursor = self._connection.execute("DELETE FROM vocab WHERE id = ?", (entry_id,))
            self._connection.commit()
            if cursor.rowcount == 0:
                raise KeyError(entry_id)

    def _get_vocab(self, entry_id: str) -> dict[str, Any] | None:
        row = self._connection.execute("SELECT * FROM vocab WHERE id = ?", (entry_id,)).fetchone()
        return _row_to_vocab(row) if row else None

    # ---- notes ----

    def list_notes(self) -> list[dict[str, Any]]:
        with self.lock:
            rows = self._connection.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
            return [_row_to_note(row) for row in rows]

    def upsert_note(self, course_id: str, sentence_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        course_id = (course_id or "").strip()
        sentence_id = (sentence_id or "").strip()
        if not course_id or not sentence_id:
            raise ValueError("courseId and sentenceId are required.")
        timestamp = now_iso()
        with self.lock:
            existing = self._connection.execute(
                "SELECT * FROM notes WHERE course_id = ? AND sentence_id = ?",
                (course_id, sentence_id),
            ).fetchone()
            text = _field_or_existing(payload, "text", existing, "text")
            starred = bool(payload["starred"]) if "starred" in payload else bool(existing["starred"] if existing else False)
            entry_id = existing["id"] if existing else f"n_{secrets.token_hex(12)}"
            created_at = existing["created_at"] if existing else timestamp
            self._connection.execute(
                """
                INSERT INTO notes (id, course_id, sentence_id, text, starred, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(course_id, sentence_id) DO UPDATE SET
                    text = excluded.text, starred = excluded.starred, updated_at = excluded.updated_at
                """,
                (entry_id, course_id, sentence_id, text, 1 if starred else 0, created_at, timestamp),
            )
            self._connection.commit()
            row = self._connection.execute(
                "SELECT * FROM notes WHERE course_id = ? AND sentence_id = ?",
                (course_id, sentence_id),
            ).fetchone()
            return _row_to_note(row)

    def delete_note(self, course_id: str, sentence_id: str) -> None:
        with self.lock:
            cursor = self._connection.execute(
                "DELETE FROM notes WHERE course_id = ? AND sentence_id = ?",
                (course_id, sentence_id),
            )
            self._connection.commit()
            if cursor.rowcount == 0:
                raise KeyError(f"{course_id}/{sentence_id}")

    # ---- activity ----

    def list_activity(self) -> list[str]:
        with self.lock:
            rows = self._connection.execute("SELECT day FROM streak ORDER BY day ASC").fetchall()
            return [row["day"] for row in rows]

    def record_activity(self, day: str) -> list[str]:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day or ""):
            raise ValueError("day must be formatted as YYYY-MM-DD.")
        with self.lock:
            self._connection.execute("INSERT OR IGNORE INTO streak (day) VALUES (?)", (day,))
            self._connection.commit()
            return self.list_activity()


def _row_to_vocab(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "term": row["term"],
        "reading": row["reading"] or "",
        "meaning": row["meaning"] or "",
        "note": row["note"] or "",
        "courseId": row["course_id"] or "",
        "sentenceId": row["sentence_id"] or "",
        "sourceText": row["source_text"] or "",
        "mastered": bool(row["mastered"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_note(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "courseId": row["course_id"],
        "sentenceId": row["sentence_id"],
        "text": row["text"] or "",
        "starred": bool(row["starred"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _field_or_existing(
    payload: dict[str, Any],
    key: str,
    existing: sqlite3.Row | None,
    column: str,
    *,
    max_length: int = 4000,
) -> str:
    if key in payload and payload[key] is not None:
        value = str(payload[key]).strip()
        if len(value) > max_length:
            raise ValueError(f"{key} is too long (max {max_length} characters).")
        return value
    if existing is not None:
        return existing[column] or ""
    return ""


class LearningApiMixin:
    """HTTP routing for the local vocab/notes/streak API.

    Mixed into a `BaseHTTPRequestHandler` subclass that also provides a `store: LearningStore`
    class attribute and its own `end_headers()` (for shared security headers).

    Routing only — authorization happens before dispatch, in the handler's
    `authorized_api()` (see `security_context.SecurityContext`). This class used
    to carry its own `learning_same_origin()` check that compared `Origin`
    against an expected origin rebuilt from the request's own `Host` header;
    since an attacker controls both, the comparison always succeeded for a
    DNS-rebound page and the reads were not gated at all. Both problems are fixed
    by checking against the address the server actually bound to, which the mixin
    has no way to know — hence the move out to the handler.
    """

    store: LearningStore

    def handle_learning_get(self, parsed: SplitResult) -> bool:
        if parsed.path == "/api/health":
            self.send_learning_json({"ok": True})
            return True
        if parsed.path == "/api/vocab":
            self.send_learning_json({"items": self.store.list_vocab()})
            return True
        if parsed.path == "/api/notes":
            self.send_learning_json({"items": self.store.list_notes()})
            return True
        if parsed.path == "/api/activity":
            self.send_learning_json({"days": self.store.list_activity()})
            return True
        return False

    def handle_learning_post(self, parsed: SplitResult) -> bool:
        if parsed.path == "/api/vocab":
            try:
                item = self.store.create_vocab(self.read_learning_json())
            except ValueError as exc:
                self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return True
            self.send_learning_json({"item": item}, HTTPStatus.CREATED)
            return True
        if parsed.path == "/api/activity":
            try:
                payload = self.read_learning_json()
                day = str(payload.get("day") or "").strip() or datetime.now().astimezone().date().isoformat()
                days = self.store.record_activity(day)
            except ValueError as exc:
                self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return True
            self.send_learning_json({"days": days})
            return True
        return False

    def handle_learning_patch(self, parsed: SplitResult) -> bool:
        prefix = "/api/vocab/"
        if not parsed.path.startswith(prefix):
            return False
        entry_id = unquote(parsed.path[len(prefix) :])
        try:
            item = self.store.update_vocab(entry_id, self.read_learning_json())
        except KeyError:
            self.send_learning_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return True
        except ValueError as exc:
            self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return True
        self.send_learning_json({"item": item})
        return True

    def handle_learning_put(self, parsed: SplitResult) -> bool:
        prefix = "/api/notes/"
        if not parsed.path.startswith(prefix):
            return False
        parts = parsed.path[len(prefix) :].split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            self.send_learning_json(
                {"error": "notes path must be /api/notes/<courseId>/<sentenceId>"}, HTTPStatus.BAD_REQUEST
            )
            return True
        course_id, sentence_id = unquote(parts[0]), unquote(parts[1])
        try:
            item = self.store.upsert_note(course_id, sentence_id, self.read_learning_json())
        except ValueError as exc:
            self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return True
        self.send_learning_json({"item": item})
        return True

    def handle_learning_delete(self, parsed: SplitResult) -> bool:
        vocab_prefix = "/api/vocab/"
        notes_prefix = "/api/notes/"
        if parsed.path.startswith(vocab_prefix):
            entry_id = unquote(parsed.path[len(vocab_prefix) :])
            try:
                self.store.delete_vocab(entry_id)
            except KeyError:
                self.send_learning_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return True
            self.send_learning_json({"ok": True})
            return True
        if parsed.path.startswith(notes_prefix):
            parts = parsed.path[len(notes_prefix) :].split("/", 1)
            if len(parts) != 2 or not parts[0] or not parts[1]:
                self.send_learning_json(
                    {"error": "notes path must be /api/notes/<courseId>/<sentenceId>"}, HTTPStatus.BAD_REQUEST
                )
                return True
            course_id, sentence_id = unquote(parts[0]), unquote(parts[1])
            try:
                self.store.delete_note(course_id, sentence_id)
            except KeyError:
                self.send_learning_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return True
            self.send_learning_json({"ok": True})
            return True
        return False

    def read_learning_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError as exc:
            raise ValueError("Invalid Content-Length.") from exc
        if length < 2 or length > MAX_JSON_BODY:
            raise ValueError("JSON request body is empty or too large.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid UTF-8 JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def send_learning_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class CourseStore:
    """Read-only access and metadata enumeration for installed courses.

    Respects immutable versioning via resolve_course_manifest_path(folder),
    falling back transparently to legacy courses/<id>/manifest.json.
    """

    def __init__(self, courses_root: Path) -> None:
        self.courses_root = Path(courses_root).expanduser().resolve()

    def get_manifest_path(self, course_id: str) -> Path | None:
        decoded = unquote(str(course_id or "")).strip()
        if not decoded or decoded in {".", ".."} or Path(decoded).name != decoded:
            return None
        folder = self.courses_root / decoded
        if not folder.is_dir():
            return None
        try:
            from studio_artifacts import resolve_course_manifest_path

            manifest_path = resolve_course_manifest_path(folder)
            if manifest_path and manifest_path.is_file():
                return manifest_path
        except Exception:
            manifest_path = folder / "manifest.json"
            if manifest_path.is_file():
                return manifest_path
        return None

    def get_course(self, course_id: str) -> dict[str, Any] | None:
        manifest_path = self.get_manifest_path(course_id)
        if manifest_path is None:
            return None
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None

    def list_courses(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not self.courses_root.is_dir():
            return rows
        try:
            from studio_artifacts import resolve_course_manifest_path
        except Exception:
            resolve_course_manifest_path = lambda f: f / "manifest.json"  # noqa: E731

        for folder in sorted(self.courses_root.iterdir()):
            if not folder.is_dir():
                continue
            manifest_path = resolve_course_manifest_path(folder)
            if not manifest_path or not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(manifest, dict):
                continue

            sentences = manifest.get("sentences")
            sentences_list = sentences if isinstance(sentences, list) else []
            sentence_count = len(sentences_list)
            practice_count = sum(
                1 for s in sentences_list
                if isinstance(s, dict) and s.get("practiceEligible", True) is not False
            )

            media = manifest.get("media") if isinstance(manifest.get("media"), dict) else None
            if media:
                media_kind = "remote"
                media_provider = str(media.get("provider") or "")
                media_control = str(media.get("control") or "full")
                page_url = str(media.get("pageUrl") or "")
            else:
                media_kind = "audio"
                media_provider = ""
                media_control = ""
                page_url = ""

            level = ""
            name_upper = folder.name.upper()
            title = str(manifest.get("title") or "")
            title_upper = title.upper()
            for lvl in ["N1", "N2", "N3", "N4", "N5"]:
                if f"-{lvl}" in name_upper or f"_{lvl}" in name_upper or lvl in title_upper:
                    level = lvl
                    break

            quality_report_path = folder / "quality-report.json"
            if quality_report_path.is_file():
                try:
                    quality = json.loads(quality_report_path.read_text(encoding="utf-8"))
                except Exception:
                    quality = {"status": "unknown"}
            elif isinstance(manifest.get("quality"), dict):
                quality = manifest["quality"]
            else:
                quality = {"status": "passed"}

            review = manifest.get("review") if isinstance(manifest.get("review"), dict) else {}

            row = {
                "id": folder.name,
                "name": folder.name,
                "title": title,
                "audio": str(manifest.get("audio") or ""),
                "sentences": sentence_count,
                "practiceSentenceCount": practice_count,
                "level": level,
                "mediaKind": media_kind,
                "mediaProvider": media_provider,
                "mediaControl": media_control,
                "pageUrl": page_url,
                "quality": quality,
                "review": review,
            }
            rows.append(row)
        return rows
