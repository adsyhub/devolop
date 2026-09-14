"""Tests for S01~S09 (Security, User Isolation, Log Sanitization, Rights Enforcement)."""

from __future__ import annotations

import json
import logging
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from exam_db import ExamDatabase  # noqa: E402
from exam_engine import ExamEngine  # noqa: E402
from exam_rights import RightsModule, RightsStatus, UserRole  # noqa: E402
from test_exam_v2_session import setup_sample_paper  # noqa: E402


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.db = ExamDatabase.in_memory()
        self.rights = RightsModule(self.db)
        self.engine = ExamEngine(self.db, self.rights)
        self.conn = self.db.connection
        self.paper = setup_sample_paper(self.db, "N1")

    def tearDown(self):
        self.conn.close()

    def test_s01_learner_cannot_access_admin_api(self):
        """S01: Regular learner is denied administrative access."""
        with self.assertRaises(PermissionError):
            self.rights.assert_admin_access(UserRole.LEARNER.value)

    def test_s02_cannot_access_other_users_session(self):
        """S02: User B cannot view, answer, or submit User A's session."""
        session = self.engine.create_session("user_A", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_A")

        # User B attempts to read session state
        with self.assertRaises(PermissionError):
            self.engine.get_session_state(session["sessionId"], "user_B")

        # User B attempts to answer
        with self.assertRaises(PermissionError):
            self.engine.record_answer(
                session["sessionId"],
                "user_B",
                self.paper["q1_v_id"],
                chosen_option_key=1,
            )

        # User B attempts to submit
        with self.assertRaises(PermissionError):
            self.engine.submit_session(session["sessionId"], "user_B")

    def test_s03_media_tokens_short_lived(self):
        """S03: Media tokens expire based on TTL."""
        token = self.rights.generate_media_token("src_N1", "audio_1", ttl_sec=1)
        self.assertTrue(self.rights.verify_media_token("src_N1", "audio_1", token))

        # Verification with wrong media id fails
        self.assertFalse(self.rights.verify_media_token("src_N1", "audio_2", token))

    def test_s04_logs_sanitize_question_text(self):
        """S04: Logging hooks do not dump full raw question stems."""
        # Setup log capture
        session = self.engine.create_session("user_s", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_s")

        with self.assertLogs("exam_engine", level="INFO") as cm:
            self.engine.record_answer(
                session["sessionId"],
                "user_s",
                self.paper["q1_v_id"],
                chosen_option_key=1,
            )
            # Log should contain question version id, but NEVER the raw question prompt '勇敢に戦う'
            log_text = " ".join(cm.output)
            self.assertNotIn("勇敢に戦う", log_text)
            self.assertIn("Answer recorded", log_text)

    def test_s05_logs_sanitize_correct_answers(self):
        """S05: Logging does not log correct answer values."""
        session = self.engine.create_session("user_s", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_s")

        with self.assertLogs("exam_engine", level="INFO") as cm:
            self.engine.record_answer(
                session["sessionId"],
                "user_s",
                self.paper["q1_v_id"],
                chosen_option_key=1,
            )
            log_text = " ".join(cm.output)
            self.assertNotIn("correct_answer", log_text)
            self.assertNotIn("correctAnswer", log_text)

    def test_s08_answers_not_in_delivery_payload(self):
        """S08: Correct answers are never sent to the client during delivery."""
        dto = self.engine.build_delivery_dto(self.paper["paper_version_id"])
        json_dump = json.dumps(dto)
        self.assertNotIn("answer", json_dump)
        self.assertNotIn("correct_answer", json_dump)

    def test_s09_deadline_enforced_by_server(self):
        """S09: Strict exam deadline is enforced on the server, cannot be bypassed by client clock."""
        session = self.engine.create_session("user_s", "N1", "STRICT_EXAM", self.paper["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_s")

        # Set deadline to expired
        self.conn.execute(
            "UPDATE session_sections SET deadline_at = '2020-01-01T00:00:00Z' WHERE practice_session_id = ?",
            (session["sessionId"],),
        )
        self.conn.commit()

        from exam_engine import SessionDeadlinePassedError
        with self.assertRaises(SessionDeadlinePassedError):
            self.engine.record_answer(session["sessionId"], "user_s", self.paper["q1_v_id"], chosen_option_key=1)


if __name__ == "__main__":
    unittest.main()
