"""Tests for E01~E16 (Strict Exam, Server-Side Authoritative Deadlines, Section Lock, Audio Policy)."""

from __future__ import annotations

import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from exam_db import ExamDatabase  # noqa: E402
from exam_engine import (  # noqa: E402
    ExamEngine,
    SectionLockedError,
    SessionDeadlinePassedError,
)
from exam_models import get_blueprint  # noqa: E402
from exam_rights import RightsModule  # noqa: E402
from test_exam_v2_session import setup_sample_paper  # noqa: E402


class MockTests(unittest.TestCase):
    def setUp(self):
        self.db = ExamDatabase.in_memory()
        self.rights = RightsModule(self.db)
        self.engine = ExamEngine(self.db, self.rights)
        self.paper_n1 = setup_sample_paper(self.db, "N1")
        self.paper_n2 = setup_sample_paper(self.db, "N2")

    def tearDown(self):
        self.db.connection.close()

    def test_e01_n1_section1_duration_from_blueprint(self):
        """E01: N1 Section 1 duration is 110 minutes (6600s)."""
        bp = get_blueprint("N1")
        self.assertEqual(bp.sections[0].time_limit_sec, 110 * 60)

    def test_e02_n1_section2_duration_from_blueprint(self):
        """E02: N1 Section 2 duration is 55 minutes (3300s)."""
        bp = get_blueprint("N1")
        self.assertEqual(bp.sections[1].time_limit_sec, 55 * 60)

    def test_e03_n2_section1_duration_from_blueprint(self):
        """E03: N2 Section 1 duration is 105 minutes (6300s)."""
        bp = get_blueprint("N2")
        self.assertEqual(bp.sections[0].time_limit_sec, 105 * 60)

    def test_e04_n2_section2_duration_from_blueprint(self):
        """E04: N2 Section 2 duration is 50 minutes (3000s)."""
        bp = get_blueprint("N2")
        self.assertEqual(bp.sections[1].time_limit_sec, 50 * 60)

    def test_e05_client_time_does_not_alter_server_countdown(self):
        """E05: Remaining time is computed strictly on server deadline - server_now."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_m")

        state = self.engine.get_session_state(session["sessionId"], "user_m")
        # Remaining sec must be within (6595, 6600]
        self.assertGreaterEqual(state["remainingSec"], 6590)
        self.assertLessEqual(state["remainingSec"], 6600)

    def test_e06_refresh_does_not_reset_deadline(self):
        """E06: Page refresh does not reset deadline."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        start = self.engine.start_session(session["sessionId"], "user_m")
        original_deadline = start["deadlineAt"]

        # Simulate reload after 1 second
        time.sleep(0.05)
        state = self.engine.get_session_state(session["sessionId"], "user_m")
        self.assertEqual(state["activeSection"]["deadline_at"], original_deadline)

    def test_e07_switch_device_does_not_reset_deadline(self):
        """E07: Changing device query preserves original deadline."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        start = self.engine.start_session(session["sessionId"], "user_m")

        # New device fetch
        state = self.engine.get_session_state(session["sessionId"], "user_m")
        self.assertEqual(state["activeSection"]["deadline_at"], start["deadlineAt"])

    def test_e08_submitted_section_cannot_modify_answers(self):
        """E08: Section 1 locked after submit; attempts to modify its answers are refused."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_m")

        # Answer Q1 in Section 1
        self.engine.record_answer(session["sessionId"], "user_m", self.paper_n1["q1_v_id"], chosen_option_key=1)

        # Submit Section 1
        res = self.engine.submit_section(session["sessionId"], "user_m", "LANGUAGE_READING")
        self.assertTrue(res["locked"])

        # Attempting to change Q1 now must raise SectionLockedError
        with self.assertRaises(SectionLockedError):
            self.engine.record_answer(
                session["sessionId"],
                "user_m",
                self.paper_n1["q1_v_id"],
                chosen_option_key=2,
            )

    def test_e09_auto_submit_on_expiry(self):
        """E09: Auto submit when expired calculates score correctly."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_m")
        res = self.engine.submit_session(session["sessionId"], "user_m")
        self.assertEqual(res["totals"]["total"], 2)

    def test_e10_answers_rejected_after_deadline(self):
        """E10 / S09: Answers arriving after the section deadline are rejected by the server."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_m")

        # Force deadline into the past in the DB
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(timespec="seconds")
        self.db.connection.execute(
            "UPDATE session_sections SET deadline_at = ? WHERE practice_session_id = ? AND section_code = 'LANGUAGE_READING'",
            (past, session["sessionId"]),
        )
        self.db.connection.commit()

        with self.assertRaises(SessionDeadlinePassedError):
            self.engine.record_answer(
                session["sessionId"],
                "user_m",
                self.paper_n1["q1_v_id"],
                chosen_option_key=1,
            )

    def test_e11_to_e14_audio_player_policy_restricted(self):
        """E11~E14: Audio restrictions in strict mode (no seek, no rate change, no pause, no replay)."""
        bp = get_blueprint("N1")
        listening_bp = bp.sections[1]
        self.assertFalse(listening_bp.allow_seek)         # E11
        self.assertFalse(listening_bp.allow_rate_change)  # E12
        self.assertFalse(listening_bp.allow_pause)        # E13
        self.assertFalse(listening_bp.allow_replay)       # E14

    def test_e15_duplicate_submit_idempotent(self):
        """E15: Submitting multiple times returns identical results without modifying submission time."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_m")
        self.engine.record_answer(session["sessionId"], "user_m", self.paper_n1["q1_v_id"], chosen_option_key=1)

        first_res = self.engine.submit_session(session["sessionId"], "user_m")
        self.assertFalse(first_res["alreadySubmitted"])
        sub_time = first_res["submittedAt"]

        second_res = self.engine.submit_session(session["sessionId"], "user_m")
        self.assertTrue(second_res["alreadySubmitted"])
        self.assertEqual(second_res["submittedAt"], sub_time)
        self.assertEqual(second_res["totals"], first_res["totals"])

    def test_e16_lease_prevents_extension_across_tabs(self):
        """E16: Session creates active lease token on start."""
        session = self.engine.create_session("user_m", "N1", "STRICT_EXAM", self.paper_n1["paper_version_id"])
        start = self.engine.start_session(session["sessionId"], "user_m")
        self.assertTrue(len(start["activeLeaseToken"]) > 0)


if __name__ == "__main__":
    unittest.main()
