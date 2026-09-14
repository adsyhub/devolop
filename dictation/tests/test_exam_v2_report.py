"""Tests for A01~A12 (Score Reports, History, Mistake Redo Context, SRS State Machine)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from exam_db import ExamDatabase  # noqa: E402
from exam_engine import ExamEngine  # noqa: E402
from exam_models import ScoreSection  # noqa: E402
from exam_rights import RightsModule  # noqa: E402
from test_exam_v2_session import setup_sample_paper  # noqa: E402


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.db = ExamDatabase.in_memory()
        self.rights = RightsModule(self.db)
        self.engine = ExamEngine(self.db, self.rights)
        self.conn = self.db.connection
        self.paper = setup_sample_paper(self.db, "N1")

    def tearDown(self):
        self.conn.close()

    def test_a01_sections_scored_separately(self):
        """A01: Score is broken down by LANGUAGE_KNOWLEDGE, READING, LISTENING."""
        session = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_a")

        # Answer Q1 (Vocabulary) correctly, Q2 (Reading) incorrectly
        self.engine.record_answer(session["sessionId"], "user_a", self.paper["q1_v_id"], chosen_option_key=1)
        self.engine.record_answer(session["sessionId"], "user_a", self.paper["q2_v_id"], chosen_option_key=1)  # correct is 2

        res = self.engine.submit_session(session["sessionId"], "user_a")
        score = res["score"]
        self.assertEqual(score[ScoreSection.LANGUAGE_KNOWLEDGE.value]["correct"], 1)
        self.assertEqual(score[ScoreSection.LANGUAGE_KNOWLEDGE.value]["total"], 1)
        self.assertEqual(score[ScoreSection.READING.value]["correct"], 0)
        self.assertEqual(score[ScoreSection.READING.value]["total"], 1)
        self.assertEqual(res["totals"]["correct"], 1)
        self.assertEqual(res["totals"]["total"], 2)

    def test_a02_first_result_preserved(self):
        """A02: First attempt result snapshot is preserved."""
        # Attempt 1: 0%
        s1 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s1["sessionId"], "user_a")
        self.engine.record_answer(s1["sessionId"], "user_a", self.paper["q1_v_id"], chosen_option_key=3)
        res1 = self.engine.submit_session(s1["sessionId"], "user_a")
        self.assertEqual(res1["totals"]["correct"], 0)

        # Attempt 2: 100%
        s2 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s2["sessionId"], "user_a")
        self.engine.record_answer(s2["sessionId"], "user_a", self.paper["q1_v_id"], chosen_option_key=1)
        self.engine.record_answer(s2["sessionId"], "user_a", self.paper["q2_v_id"], chosen_option_key=2)
        res2 = self.engine.submit_session(s2["sessionId"], "user_a")
        self.assertEqual(res2["totals"]["correct"], 2)

        # Query first snapshot in DB
        first_row = self.conn.execute(
            "SELECT rs.* FROM result_snapshots rs "
            "JOIN practice_sessions ps ON ps.id = rs.practice_session_id "
            "WHERE ps.user_id = 'user_a' ORDER BY rs.created_at ASC LIMIT 1"
        ).fetchone()
        self.assertEqual(first_row["practice_session_id"], s1["sessionId"])
        self.assertEqual(first_row["raw_correct_count"], 0)

    def test_a03_latest_result_preserved(self):
        """A03: Latest attempt result snapshot is preserved."""
        s1 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s1["sessionId"], "user_a")
        self.engine.submit_session(s1["sessionId"], "user_a")

        s2 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s2["sessionId"], "user_a")
        self.engine.record_answer(s2["sessionId"], "user_a", self.paper["q1_v_id"], chosen_option_key=1)
        self.engine.submit_session(s2["sessionId"], "user_a")

        latest_row = self.conn.execute(
            "SELECT rs.* FROM result_snapshots rs "
            "JOIN practice_sessions ps ON ps.id = rs.practice_session_id "
            "WHERE ps.user_id = 'user_a' ORDER BY rs.created_at DESC, rs.rowid DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(latest_row["practice_session_id"], s2["sessionId"])
        self.assertEqual(latest_row["raw_correct_count"], 1)

    def test_a04_best_result_preserved(self):
        """A04: Best result is queried across all result snapshots."""
        # 1st attempt: 1 correct
        s1 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s1["sessionId"], "user_a")
        self.engine.record_answer(s1["sessionId"], "user_a", self.paper["q1_v_id"], chosen_option_key=1)
        self.engine.submit_session(s1["sessionId"], "user_a")

        # 2nd attempt: 2 correct
        s2 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s2["sessionId"], "user_a")
        self.engine.record_answer(s2["sessionId"], "user_a", self.paper["q1_v_id"], chosen_option_key=1)
        self.engine.record_answer(s2["sessionId"], "user_a", self.paper["q2_v_id"], chosen_option_key=2)
        self.engine.submit_session(s2["sessionId"], "user_a")

        # 3rd attempt: 0 correct
        s3 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s3["sessionId"], "user_a")
        self.engine.submit_session(s3["sessionId"], "user_a")

        best_row = self.conn.execute(
            "SELECT rs.* FROM result_snapshots rs "
            "JOIN practice_sessions ps ON ps.id = rs.practice_session_id "
            "WHERE ps.user_id = 'user_a' ORDER BY rs.raw_accuracy DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(best_row["practice_session_id"], s2["sessionId"])
        self.assertEqual(best_row["raw_accuracy"], 100.0)

    def test_a05_all_attempts_preserved(self):
        """A05: All session records and result snapshots are permanently stored."""
        for _ in range(3):
            s = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
            self.engine.start_session(s["sessionId"], "user_a")
            self.engine.submit_session(s["sessionId"], "user_a")

        count = self.conn.execute(
            "SELECT COUNT(*) as c FROM practice_sessions WHERE user_id = 'user_a'"
        ).fetchone()["c"]
        self.assertEqual(count, 3)

    def test_a06_no_fake_official_score(self):
        """A06: In absence of IRT calibrated model, no fake official scaled score is generated."""
        session = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_a")
        res = self.engine.submit_session(session["sessionId"], "user_a")

        row = self.conn.execute(
            "SELECT estimate_model_version FROM result_snapshots WHERE practice_session_id = ?",
            (session["sessionId"],),
        ).fetchone()
        self.assertIsNone(row["estimate_model_version"])
        self.assertNotIn("estimatedOfficialScore", res)

    def test_a09_wrong_redo_does_not_overwrite(self):
        """A09: Mistake redo creates a new session and does not overwrite original."""
        s1 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s1["sessionId"], "user_a")
        # Answer Q2 incorrectly
        self.engine.record_answer(s1["sessionId"], "user_a", self.paper["q1_v_id"], chosen_option_key=1)
        self.engine.record_answer(s1["sessionId"], "user_a", self.paper["q2_v_id"], chosen_option_key=3)
        self.engine.submit_session(s1["sessionId"], "user_a")

        redo = self.engine.create_wrong_redo_session("user_a", s1["sessionId"])
        self.assertNotEqual(redo["sessionId"], s1["sessionId"])
        self.assertEqual(redo["mode"], "WRONG_REDO")

        # Original session is still SUBMITTED and untouched
        orig_state = self.engine.get_session_state(s1["sessionId"], "user_a")
        self.assertEqual(orig_state["status"], "SUBMITTED")

    def test_a10_reading_redo_preserves_passage(self):
        """A10: Reading mistake redo retains the full question group and passage."""
        s1 = self.engine.create_session("user_a", "N1", "PAPER_PRACTICE", self.paper["paper_version_id"])
        self.engine.start_session(s1["sessionId"], "user_a")
        self.engine.record_answer(s1["sessionId"], "user_a", self.paper["q2_v_id"], chosen_option_key=4)  # wrong
        self.engine.submit_session(s1["sessionId"], "user_a")

        redo = self.engine.create_wrong_redo_session("user_a", s1["sessionId"])
        snaps = self.conn.execute(
            "SELECT * FROM session_group_snapshots WHERE practice_session_id = ?",
            (redo["sessionId"],),
        ).fetchall()
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0]["question_group_version_id"], self.paper["qg2_v_id"])

    def test_a11_listening_redo_preserves_audio_group(self):
        """A11: Listening mistake redo retains the full question group."""
        # Insert a listening question group with wrong answer
        self.conn.execute(
            "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
            "VALUES ('qg_ar_l', 'QG_AR_L', 'N1', 'LISTENING', 'LISTENING_TASK_BASED', 'src_N1', '2026-09-01T00:00:00Z')"
        )
        self.conn.execute(
            "INSERT INTO question_group_versions (id, question_group_id, version_number, instruction_text, status, content_hash, created_at) "
            "VALUES ('qgv_ar_l', 'qg_ar_l', 1, '聴解', 'PUBLISHED', 'hash_arl', '2026-09-01T00:00:00Z')"
        )
        self.conn.execute(
            "INSERT INTO questions (id, question_group_id, stable_key, created_at) VALUES ('q_ar_l', 'qg_ar_l', 'QL1', '2026-09-01T00:00:00Z')"
        )
        self.conn.execute(
            "INSERT INTO question_versions (id, question_id, version_number, question_group_version_id, display_order, stem_text, correct_answer_json, status, content_hash, created_at) "
            "VALUES ('qv_ar_l', 'q_ar_l', 1, 'qgv_ar_l', 1, '聴解問題', '{\"answer\": 1}', 'PUBLISHED', 'hql', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

        # Create session with this group
        s = self.engine.create_session("user_a", "N1", "ITEM_TYPE_PRACTICE")
        sec_id = self.conn.execute(
            "SELECT id FROM session_sections WHERE practice_session_id = ? LIMIT 1",
            (s["sessionId"],),
        ).fetchone()["id"]
        self.conn.execute(
            "INSERT INTO session_group_snapshots (id, practice_session_id, session_section_id, question_group_version_id, display_order, required_question_ids_json, created_at) "
            "VALUES ('snap_l', ?, ?, 'qgv_ar_l', 1, '[\"qv_ar_l\"]', '2026-09-01T00:00:00Z')",
            (s["sessionId"], sec_id),
        )
        self.conn.commit()

        self.engine.record_answer(s["sessionId"], "user_a", "qv_ar_l", chosen_option_key=2)  # wrong
        self.engine.submit_session(s["sessionId"], "user_a")

        redo = self.engine.create_wrong_redo_session("user_a", s["sessionId"])
        snaps = self.conn.execute(
            "SELECT * FROM session_group_snapshots WHERE practice_session_id = ?",
            (redo["sessionId"],),
        ).fetchall()
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0]["question_group_version_id"], "qgv_ar_l")

    def test_a12_srs_state_machine_intervals(self):
        """A12: NEW_WRONG -> CORRECT_ON_REDO -> STABILIZING -> MASTERED."""
        qid = "q_N1_1"

        # 1. First wrong attempt -> NEW_WRONG
        self.engine._update_user_srs_state("user_srs", qid, is_correct=False, is_skipped=False)
        row = self.conn.execute("SELECT * FROM user_question_states WHERE user_id = 'user_srs' AND question_id = ?", (qid,)).fetchone()
        self.assertEqual(row["mastery_status"], "NEW_WRONG")
        self.assertEqual(row["streak"], 0)

        # 2. Correct on redo -> CORRECT_ON_REDO
        self.engine._update_user_srs_state("user_srs", qid, is_correct=True, is_skipped=False)
        row = self.conn.execute("SELECT * FROM user_question_states WHERE user_id = 'user_srs' AND question_id = ?", (qid,)).fetchone()
        self.assertEqual(row["mastery_status"], "CORRECT_ON_REDO")
        self.assertEqual(row["streak"], 1)

        # 3. Next correct -> STABILIZING
        self.engine._update_user_srs_state("user_srs", qid, is_correct=True, is_skipped=False)
        row = self.conn.execute("SELECT * FROM user_question_states WHERE user_id = 'user_srs' AND question_id = ?", (qid,)).fetchone()
        self.assertEqual(row["mastery_status"], "STABILIZING")
        self.assertEqual(row["streak"], 2)

        # 4. Next correct -> MASTERED
        self.engine._update_user_srs_state("user_srs", qid, is_correct=True, is_skipped=False)
        row = self.conn.execute("SELECT * FROM user_question_states WHERE user_id = 'user_srs' AND question_id = ?", (qid,)).fetchone()
        self.assertEqual(row["mastery_status"], "MASTERED")
        self.assertEqual(row["streak"], 3)


if __name__ == "__main__":
    unittest.main()
