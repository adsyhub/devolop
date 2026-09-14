"""Tests for RightsModule (R01~R06, S01, S03, S06)."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from exam_db import ExamDatabase  # noqa: E402
from exam_rights import RightsModule, RightsStatus, UserRole  # noqa: E402


class RightsTests(unittest.TestCase):
    def setUp(self):
        self.db = ExamDatabase.in_memory()
        self.rights = RightsModule(self.db)
        self.conn = self.db.connection

        # Insert a test content source
        self.conn.execute(
            "INSERT INTO content_sources (id, code, name, source_type, authenticity_status, completeness, created_at, updated_at) "
            "VALUES ('src_r', 'SRC_R', 'Rights Test Source', 'OFFICIAL', 'OFFICIAL_ORIGINAL', 'FULL_SESSION', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

    def test_s01_learner_cannot_access_admin_api(self):
        """S01: Regular learner cannot access administrative endpoints."""
        with self.assertRaises(PermissionError):
            self.rights.assert_admin_access(UserRole.LEARNER.value)

        # Admin roles succeed
        self.rights.assert_admin_access(UserRole.ADMIN.value)
        self.rights.assert_admin_access(UserRole.CONTENT_EDITOR.value)
        self.rights.assert_admin_access(UserRole.RIGHTS_REVIEWER.value)

    def test_r01_unapproved_cannot_publish(self):
        """R01: Content without APPROVED rights cannot be published."""
        # 1. No license -> cannot publish
        ok, msg = self.rights.can_publish("src_r")
        self.assertFalse(ok)

        # 2. UNAPPROVED license -> cannot publish
        self.conn.execute(
            "INSERT INTO licenses (id, content_source_id, rights_status, valid_from, valid_until, created_at, updated_at) "
            "VALUES ('lic_unapproved', 'src_r', 'UNAPPROVED', '2026-01-01T00:00:00Z', '2027-01-01T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()
        ok, msg = self.rights.can_publish("src_r")
        self.assertFalse(ok)
        self.assertIn("UNAPPROVED", msg)

        # 3. APPROVED license -> can publish
        self.conn.execute("UPDATE licenses SET rights_status = 'APPROVED' WHERE id = 'lic_unapproved'")
        self.conn.commit()
        ok, msg = self.rights.can_publish("src_r")
        self.assertTrue(ok)

    def test_r02_expired_license_cannot_start_session(self):
        """R02: Expired licenses cannot start a new practice session."""
        # License expired yesterday
        self.conn.execute(
            "INSERT INTO licenses (id, content_source_id, rights_status, valid_from, valid_until, created_at, updated_at) "
            "VALUES ('lic_expired', 'src_r', 'APPROVED', '2025-01-01T00:00:00Z', '2025-12-31T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()
        ok, msg = self.rights.can_start_session("src_r")
        self.assertFalse(ok)
        self.assertIn("expired", msg)

    def test_r03_translation_disabled_strips_translation(self):
        """R03: When translation permission is disabled, translation is removed from DTO."""
        self.conn.execute(
            "INSERT INTO licenses (id, content_source_id, rights_status, translation_allowed, valid_from, valid_until, created_at, updated_at) "
            "VALUES ('lic_no_trans', 'src_r', 'APPROVED', 0, '2026-01-01T00:00:00Z', '2030-01-01T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

        sample_dto = {
            "title": "Passage 1",
            "text": "日本語の文章",
            "translation_zh": "日文文章（受版权保护）",
            "questions": [
                {"id": "q1", "prompt": "問題1", "translationZh": "问题1翻译"}
            ]
        }
        cleaned = self.rights.sanitize_delivery_dto(sample_dto, "src_r")
        self.assertNotIn("translation_zh", cleaned)
        self.assertNotIn("translationZh", cleaned["questions"][0])
        self.assertEqual(cleaned["text"], "日本語の文章")

    def test_r04_audio_disabled_strips_credentials(self):
        """R04: When audio permission is disabled, audio credentials are removed from DTO."""
        self.conn.execute(
            "INSERT INTO licenses (id, content_source_id, rights_status, audio_streaming_allowed, valid_from, valid_until, created_at, updated_at) "
            "VALUES ('lic_no_audio', 'src_r', 'APPROVED', 0, '2026-01-01T00:00:00Z', '2030-01-01T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

        sample_dto = {
            "audioUrl": "/media/listening_01.mp3",
            "audioToken": "secret_token_123",
        }
        cleaned = self.rights.sanitize_delivery_dto(sample_dto, "src_r")
        self.assertNotIn("audioUrl", cleaned)
        self.assertNotIn("audioToken", cleaned)

    def test_r05_and_s06_audit_logging(self):
        """R05 / S06: Suspend, publish, and status changes write immutable audit logs."""
        log_id = self.rights.log_audit(
            actor_id="user_admin_1",
            action="SUSPEND_PAPER",
            target_type="PAPER_VERSION",
            target_id="pv_123",
            details={"reason": "Rights expired"},
        )
        row = self.conn.execute("SELECT * FROM audit_logs WHERE id = ?", (log_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["actor_id"], "user_admin_1")
        self.assertEqual(row["action"], "SUSPEND_PAPER")

    def test_r06_and_s03_media_token_generation_and_verification(self):
        """R06 & S03: Short-lived media tokens, refused if revoked."""
        # 1. License with audio streaming allowed
        self.conn.execute(
            "INSERT INTO licenses (id, content_source_id, rights_status, audio_streaming_allowed, valid_from, valid_until, created_at, updated_at) "
            "VALUES ('lic_audio_ok', 'src_r', 'APPROVED', 1, '2026-01-01T00:00:00Z', '2030-01-01T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

        token = self.rights.generate_media_token("src_r", "audio_track_01", ttl_sec=300)
        self.assertTrue(self.rights.verify_media_token("src_r", "audio_track_01", token))
        self.assertFalse(self.rights.verify_media_token("src_r", "different_track", token))

        # 2. R06: If license revoked, generation is refused
        self.conn.execute("UPDATE licenses SET rights_status = 'REVOKED' WHERE id = 'lic_audio_ok'")
        self.conn.commit()
        with self.assertRaises(PermissionError):
            self.rights.generate_media_token("src_r", "audio_track_01")


if __name__ == "__main__":
    unittest.main()

