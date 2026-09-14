"""RightsModule and Content Permission Gate.

Enforces:
- R01: Content without APPROVED rights cannot be published.
- R02: Expired licenses cannot create new practice sessions.
- R03: When translation permission is off, translation fields are withheld.
- R04: When audio permission is off, audio stream credentials are withheld.
- R05 / S06: Suspend/publish operations write immutable audit logs.
- R06: Revoked rights refuse media signature tokens.
- S01: Learner role cannot access admin APIs.
- S03: Media tokens are short-lived.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from exam_db import ExamDatabase


class UserRole(str, Enum):
    LEARNER = "LEARNER"
    CONTENT_EDITOR = "CONTENT_EDITOR"
    ANSWER_REVIEWER = "ANSWER_REVIEWER"
    RIGHTS_REVIEWER = "RIGHTS_REVIEWER"
    PUBLISHER = "PUBLISHER"
    ADMIN = "ADMIN"


class RightsStatus(str, Enum):
    UNAPPROVED = "UNAPPROVED"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


ADMIN_ROLES = frozenset({
    UserRole.CONTENT_EDITOR.value,
    UserRole.ANSWER_REVIEWER.value,
    UserRole.RIGHTS_REVIEWER.value,
    UserRole.PUBLISHER.value,
    UserRole.ADMIN.value,
})


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RightsModule:
    """Central authority on rights and permissions."""

    def __init__(self, db: ExamDatabase, token_secret: str = "jlpt-media-secret") -> None:
        self.db = db
        self.secret = token_secret.encode("utf-8")

    # ---- User Permissions ----

    def assert_admin_access(self, role: str) -> None:
        """S01: Learners cannot access admin interfaces."""
        if role not in ADMIN_ROLES:
            raise PermissionError("Access denied: only administrative roles can access this API.")

    def assert_can_review_answer(self, created_by: str, reviewer_id: str) -> None:
        """Anti-conflict: Same user cannot enter and review the answer."""
        if created_by and created_by == reviewer_id:
            raise ValueError("The creator of the question cannot also review its answer.")

    # ---- Rights Gating ----

    def get_source_license(self, content_source_id: str) -> dict[str, Any] | None:
        row = self.db.connection.execute(
            "SELECT * FROM licenses WHERE content_source_id = ? ORDER BY created_at DESC LIMIT 1",
            (content_source_id,),
        ).fetchone()
        return dict(row) if row else None

    def can_publish(self, content_source_id: str) -> tuple[bool, str]:
        """R01: Content without APPROVED rights cannot be published."""
        lic = self.get_source_license(content_source_id)
        if not lic:
            return False, "No license record exists for this content source."
        if lic["rights_status"] != RightsStatus.APPROVED.value:
            return False, f"Rights status is {lic['rights_status']!r}, must be 'APPROVED'."
        now = now_utc_iso()
        if lic["valid_until"] < now:
            return False, f"License expired at {lic['valid_until']}."
        return True, ""

    def can_start_session(self, content_source_id: str) -> tuple[bool, str]:
        """R02: Expired or unapproved licenses cannot start a new session."""
        lic = self.get_source_license(content_source_id)
        if not lic:
            return False, "No license found for this content."
        if lic["rights_status"] != RightsStatus.APPROVED.value:
            return False, f"Content rights status is {lic['rights_status']}, cannot start practice."
        now = now_utc_iso()
        if lic["valid_until"] < now:
            return False, f"License expired on {lic['valid_until']}, cannot start practice."
        return True, ""

    def sanitize_delivery_dto(self, dto: dict[str, Any], content_source_id: str) -> dict[str, Any]:
        """R03/R04: Strip translation and audio stream when permission is off."""
        lic = self.get_source_license(content_source_id)
        translation_allowed = bool(lic and lic.get("translation_allowed"))
        audio_allowed = bool(lic and lic.get("audio_streaming_allowed"))

        # Deep clone or filter dictionary
        cleaned = json.loads(json.dumps(dto))

        def _clean_node(node: Any) -> None:
            if isinstance(node, dict):
                if not translation_allowed:
                    node.pop("translation_zh", None)
                    node.pop("translationZh", None)
                if not audio_allowed:
                    node.pop("audio_url", None)
                    node.pop("audioUrl", None)
                    node.pop("audio_token", None)
                    node.pop("audioToken", None)
                for v in node.values():
                    _clean_node(v)
            elif isinstance(node, list):
                for item in node:
                    _clean_node(item)

        _clean_node(cleaned)
        return cleaned

    # ---- Media Signing ----

    def generate_media_token(self, content_source_id: str, media_id: str, ttl_sec: int = 300) -> str:
        """S03 / R06: Generate a short-lived HMAC media token; refuse if revoked or unapproved."""
        lic = self.get_source_license(content_source_id)
        if not lic or lic["rights_status"] in (RightsStatus.REVOKED.value, RightsStatus.UNAPPROVED.value):
            raise PermissionError(f"Cannot generate media token: license is {lic['rights_status'] if lic else 'MISSING'}.")
        if not lic.get("audio_streaming_allowed"):
            raise PermissionError("Audio streaming is not allowed under current license.")

        expires_at = int(time.time()) + ttl_sec
        message = f"{content_source_id}:{media_id}:{expires_at}".encode("utf-8")
        signature = hmac.new(self.secret, message, hashlib.sha256).hexdigest()
        return f"{expires_at}.{signature}"

    def verify_media_token(self, content_source_id: str, media_id: str, token: str) -> bool:
        """Verify the short-lived token."""
        try:
            exp_str, sig = token.split(".", 1)
            expires_at = int(exp_str)
        except Exception:
            return False
        if time.time() > expires_at:
            return False  # Expired (S03)
        message = f"{content_source_id}:{media_id}:{expires_at}".encode("utf-8")
        expected = hmac.new(self.secret, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)

    # ---- Audit Logging ----

    def log_audit(self, actor_id: str, action: str, target_type: str, target_id: str, details: dict[str, Any] | None = None) -> str:
        """R05 / S06: Write immutable audit log."""
        log_id = uuid.uuid4().hex
        now = now_utc_iso()
        self.db.connection.execute(
            "INSERT INTO audit_logs (id, actor_id, action, target_type, target_id, details_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (log_id, actor_id, action, target_type, target_id, json.dumps(details or {}), now),
        )
        self.db.connection.commit()
        return log_id

