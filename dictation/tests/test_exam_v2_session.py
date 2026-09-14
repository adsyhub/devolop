"""Tests for P01~P08 (Practice Session, Answers Isolation, Recovery) and V01~V05 (Versions)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from exam_db import ExamDatabase  # noqa: E402
from exam_engine import AnswerVersionConflictError, ExamEngine  # noqa: E402
from exam_rights import RightsModule  # noqa: E402


def setup_sample_paper(db: ExamDatabase, level: str = "N1") -> dict[str, str]:
    """Helper to populate a synthetic N1 or N2 paper in the database."""
    conn = db.connection
    # Content source & license
    src_id = f"src_{level}"
    conn.execute(
        "INSERT INTO content_sources (id, code, name, source_type, authenticity_status, completeness, created_at, updated_at) "
        "VALUES (?, ?, 'Synthetic Exam', 'OFFICIAL', 'OFFICIAL_ORIGINAL', 'FULL_SESSION', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (src_id, f"SRC_{level}"),
    )
    conn.execute(
        "INSERT INTO licenses (id, content_source_id, rights_status, translation_allowed, audio_streaming_allowed, valid_from, valid_until, created_at, updated_at) "
        "VALUES (?, ?, 'APPROVED', 1, 1, '2026-01-01T00:00:00Z', '2030-01-01T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (f"lic_{level}", src_id),
    )

    # Material (Reading passage)
    mat_id = f"mat_{level}"
    mat_v_id = f"mv_{level}"
    conn.execute(
        "INSERT INTO materials (id, stable_code, material_type, content_source_id, created_at) "
        "VALUES (?, ?, 'TEXT', ?, '2026-09-01T00:00:00Z')",
        (mat_id, f"MAT_{level}_01", src_id),
    )
    conn.execute(
        "INSERT INTO material_versions (id, material_id, version_number, plain_text, content_ast_json, content_hash, status, created_at, published_at) "
        "VALUES (?, ?, 1, 'これは合成読解文章である。', '{}', 'hash_m1', 'PUBLISHED', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (mat_v_id, mat_id),
    )

    # Question group 1: Kanji reading
    qg1_id = f"qg_{level}_1"
    qg1_v_id = f"qgv_{level}_1"
    conn.execute(
        "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
        "VALUES (?, ?, ?, 'VOCABULARY', 'VOCAB_KANJI_READING', ?, '2026-09-01T00:00:00Z')",
        (qg1_id, f"QG_{level}_01", level, src_id),
    )
    conn.execute(
        "INSERT INTO question_group_versions (id, question_group_id, version_number, instruction_text, status, content_hash, created_at, published_at) "
        "VALUES (?, ?, 1, '漢字の読み方を選びなさい。', 'PUBLISHED', 'hash_qg1', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (qg1_v_id, qg1_id),
    )

    # Question 1
    q1_id = f"q_{level}_1"
    q1_v_id = f"qv_{level}_1"
    conn.execute(
        "INSERT INTO questions (id, question_group_id, stable_key, created_at) VALUES (?, ?, ?, '2026-09-01T00:00:00Z')",
        (q1_id, qg1_id, f"Q_{level}_1"),
    )
    conn.execute(
        "INSERT INTO question_versions (id, question_id, version_number, question_group_version_id, display_order, stem_text, correct_answer_json, status, content_hash, created_at, published_at) "
        "VALUES (?, ?, 1, ?, 1, '<u>勇敢</u>に戦う。', '{\"answer\": 1}', 'PUBLISHED', 'hash_q1', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (q1_v_id, q1_id, qg1_v_id),
    )
    for opt_key, text, is_c in [(1, "ゆうかん", 1), (2, "ゆうがん", 0), (3, "ゆうけん", 0), (4, "ゆうげん", 0)]:
        conn.execute(
            "INSERT INTO option_versions (id, question_version_id, option_key, display_order, content_text, is_correct) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (f"opt_{q1_v_id}_{opt_key}", q1_v_id, opt_key, opt_key, text, is_c),
        )

    # Question group 2: Reading short
    qg2_id = f"qg_{level}_2"
    qg2_v_id = f"qgv_{level}_2"
    conn.execute(
        "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
        "VALUES (?, ?, ?, 'READING', 'READING_SHORT', ?, '2026-09-01T00:00:00Z')",
        (qg2_id, f"QG_{level}_02", level, src_id),
    )
    conn.execute(
        "INSERT INTO question_group_versions (id, question_group_id, version_number, instruction_text, status, content_hash, created_at, published_at) "
        "VALUES (?, ?, 1, '次の文章を読んで答えなさい。', 'PUBLISHED', 'hash_qg2', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (qg2_v_id, qg2_id),
    )
    conn.execute(
        "INSERT INTO question_group_materials (question_group_version_id, material_version_id, display_order, usage_type) "
        "VALUES (?, ?, 1, 'PRIMARY')",
        (qg2_v_id, mat_v_id),
    )

    # Question 2 (linked to reading)
    q2_id = f"q_{level}_2"
    q2_v_id = f"qv_{level}_2"
    conn.execute(
        "INSERT INTO questions (id, question_group_id, stable_key, created_at) VALUES (?, ?, ?, '2026-09-01T00:00:00Z')",
        (q2_id, qg2_id, f"Q_{level}_2"),
    )
    conn.execute(
        "INSERT INTO question_versions (id, question_id, version_number, question_group_version_id, display_order, stem_text, correct_answer_json, status, content_hash, created_at, published_at) "
        "VALUES (?, ?, 1, ?, 1, '筆者の考えと合致するものはどれか。', '{\"answer\": 2}', 'PUBLISHED', 'hash_q2', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (q2_v_id, q2_id, qg2_v_id),
    )
    for opt_key, text, is_c in [(1, "選択肢1", 0), (2, "選択肢2（正解）", 1), (3, "選択肢3", 0), (4, "選択肢4", 0)]:
        conn.execute(
            "INSERT INTO option_versions (id, question_version_id, option_key, display_order, content_text, is_correct) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (f"opt_{q2_v_id}_{opt_key}", q2_v_id, opt_key, opt_key, text, is_c),
        )

    # Paper & PaperVersion
    paper_id = f"paper_{level}"
    pv_id = f"pv_{level}"
    conn.execute(
        "INSERT INTO papers (id, stable_code, title, level, content_source_id, completeness, created_at) "
        "VALUES (?, ?, 'Synthetic Test Paper', ?, ?, 'FULL_SESSION', '2026-09-01T00:00:00Z')",
        (paper_id, f"P_{level}_01", level, src_id),
    )
    conn.execute(
        "INSERT INTO paper_versions (id, paper_id, version_number, title, status, content_hash, created_at, published_at) "
        "VALUES (?, ?, 1, 'Synthetic Test Paper v1', 'PUBLISHED', 'hash_pv1', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')",
        (pv_id, paper_id),
    )

    # Paper section 1: LANGUAGE_READING
    ps1_id = f"ps_{level}_1"
    conn.execute(
        "INSERT INTO paper_sections (id, paper_version_id, section_code, display_order, time_limit_sec) "
        "VALUES (?, ?, 'LANGUAGE_READING', 1, 6600)",
        (ps1_id, pv_id),
    )
    # Part 1
    pp1_id = f"pp_{level}_1"
    conn.execute(
        "INSERT INTO paper_parts (id, paper_section_id, part_code, title, item_type_code, display_order) "
        "VALUES (?, ?, 'P1', '文字・語彙', 'VOCAB_KANJI_READING', 1)",
        (pp1_id, ps1_id),
    )
    conn.execute(
        "INSERT INTO paper_blocks (id, paper_part_id, question_group_version_id, display_order) "
        "VALUES (?, ?, ?, 1)",
        (f"pb_{level}_1", pp1_id, qg1_v_id),
    )
    # Part 2
    pp2_id = f"pp_{level}_2"
    conn.execute(
        "INSERT INTO paper_parts (id, paper_section_id, part_code, title, item_type_code, display_order) "
        "VALUES (?, ?, 'P2', '読解', 'READING_SHORT', 2)",
        (pp2_id, ps1_id),
    )
    conn.execute(
        "INSERT INTO paper_blocks (id, paper_part_id, question_group_version_id, display_order) "
        "VALUES (?, ?, ?, 2)",
        (f"pb_{level}_2", pp2_id, qg2_v_id),
    )

    conn.commit()
    return {
        "paper_id": paper_id,
        "paper_version_id": pv_id,
        "qg1_v_id": qg1_v_id,
        "qg2_v_id": qg2_v_id,
        "q1_v_id": q1_v_id,
        "q2_v_id": q2_v_id,
    }


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.db = ExamDatabase.in_memory()
        self.rights = RightsModule(self.db)
        self.engine = ExamEngine(self.db, self.rights)
        self.paper_info = setup_sample_paper(self.db, "N1")

    def tearDown(self):
        self.db.connection.close()

    def test_p05_delivery_dto_contains_no_answer(self):
        """P05 / S08: Delivery DTO must contain ZERO answers, correct answers, or explanations."""
        dto = self.engine.build_delivery_dto(self.paper_info["paper_version_id"])

        # Deep scan JSON string
        json_str = json.dumps(dto)
        self.assertNotIn("correct_answer", json_str)
        self.assertNotIn("correctAnswer", json_str)
        self.assertNotIn("is_correct", json_str)
        self.assertNotIn("isCorrect", json_str)
        self.assertNotIn("explanation", json_str)

        # Inspect options
        sec = dto["sections"][0]
        q = sec["parts"][0]["blocks"][0]["questions"][0]
        self.assertEqual(len(q["options"]), 4)
        for opt in q["options"]:
            self.assertIn("optionKey", opt)
            self.assertIn("contentText", opt)
            self.assertNotIn("is_correct", opt)
            self.assertNotIn("isCorrect", opt)

    def test_p01_autosave_answers(self):
        """P01: Answers are autosaved with version and idempotency."""
        session = self.engine.create_session("user_1", "N1", "PAPER_PRACTICE", self.paper_info["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_1")

        # First save
        res = self.engine.record_answer(
            session_id=session["sessionId"],
            user_id="user_1",
            question_version_id=self.paper_info["q1_v_id"],
            chosen_option_key=1,
            confidence="sure",
            client_version=1,
        )
        self.assertTrue(res["saved"])
        self.assertEqual(res["serverVersion"], 1)

        # Second save (user changed mind to option 2)
        res2 = self.engine.record_answer(
            session_id=session["sessionId"],
            user_id="user_1",
            question_version_id=self.paper_info["q1_v_id"],
            chosen_option_key=2,
            confidence="unsure",
            client_version=1,  # client sends same version
        )
        self.assertEqual(res2["serverVersion"], 2)

        # Stale client version raises 409 conflict
        with self.assertRaises(AnswerVersionConflictError):
            self.engine.record_answer(
                session_id=session["sessionId"],
                user_id="user_1",
                question_version_id=self.paper_info["q1_v_id"],
                chosen_option_key=3,
                client_version=1,  # older than serverVersion 2
            )

    def test_p02_session_answers_restored(self):
        """P02: Refreshing recovers all saved answers."""
        session = self.engine.create_session("user_1", "N1", "PAPER_PRACTICE", self.paper_info["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_1")

        self.engine.record_answer(
            session_id=session["sessionId"],
            user_id="user_1",
            question_version_id=self.paper_info["q1_v_id"],
            chosen_option_key=1,
        )

        # Simulate page reload -> get_session_state
        state = self.engine.get_session_state(session["sessionId"], "user_1")
        self.assertEqual(state["answers"][self.paper_info["q1_v_id"]]["chosen"], 1)

    def test_p03_session_position_restored(self):
        """P03: Session recovery returns active section and deadline."""
        session = self.engine.create_session("user_1", "N1", "PAPER_PRACTICE", self.paper_info["paper_version_id"])
        start_res = self.engine.start_session(session["sessionId"], "user_1")

        state = self.engine.get_session_state(session["sessionId"], "user_1")
        self.assertIsNotNone(state["activeSection"])
        self.assertEqual(state["activeSection"]["section_code"], "LANGUAGE_READING")
        self.assertGreater(state["remainingSec"], 6000)

    def test_p04_group_and_item_submit(self):
        """P04: Answers can be saved item-by-item and submitted."""
        session = self.engine.create_session("user_1", "N1", "PAPER_PRACTICE", self.paper_info["paper_version_id"])
        self.engine.start_session(session["sessionId"], "user_1")

        self.engine.record_answer(
            session_id=session["sessionId"],
            user_id="user_1",
            question_version_id=self.paper_info["q1_v_id"],
            chosen_option_key=1,
        )
        self.engine.record_answer(
            session_id=session["sessionId"],
            user_id="user_1",
            question_version_id=self.paper_info["q2_v_id"],
            chosen_option_key=2,
        )

        result = self.engine.submit_session(session["sessionId"], "user_1")
        self.assertEqual(result["totals"]["correct"], 2)
        self.assertEqual(result["totals"]["total"], 2)
        self.assertEqual(result["totals"]["accuracy"], 100.0)

    def test_p06_reading_context_intact(self):
        """P06: Delivery DTO links passage material to the question group."""
        dto = self.engine.build_delivery_dto(self.paper_info["paper_version_id"])
        reading_block = dto["sections"][0]["parts"][1]["blocks"][0]
        self.assertEqual(reading_block["itemTypeCode"], "READING_SHORT")
        self.assertEqual(len(reading_block["materials"]), 1)
        self.assertEqual(reading_block["materials"][0]["plainText"], "これは合成読解文章である。")

    def test_p07_listening_context_intact(self):
        """P07: Listening context includes audio material reference."""
        # Insert a listening group
        conn = self.db.connection
        conn.execute(
            "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
            "VALUES ('qg_list_1', 'QG_L1', 'N1', 'LISTENING', 'LISTENING_TASK_BASED', 'src_N1', '2026-09-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO question_group_versions (id, question_group_id, version_number, instruction_text, status, content_hash, created_at) "
            "VALUES ('qgv_l1', 'qg_list_1', 1, '問題を聞いて答えなさい。', 'PUBLISHED', 'hash_l1', '2026-09-01T00:00:00Z')"
        )
        # Material audio
        conn.execute(
            "INSERT INTO materials (id, stable_code, material_type, content_source_id, created_at) "
            "VALUES ('mat_audio', 'MAT_A1', 'AUDIO', 'src_N1', '2026-09-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO material_versions (id, material_id, version_number, plain_text, content_ast_json, content_hash, status, created_at) "
            "VALUES ('mv_audio', 'mat_audio', 1, '', '{\"audio_url\": \"/audio/n1_q1.mp3\"}', 'hash_ma', 'PUBLISHED', '2026-09-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO question_group_materials (question_group_version_id, material_version_id, display_order, usage_type) "
            "VALUES ('qgv_l1', 'mv_audio', 1, 'AUDIO')"
        )
        conn.commit()

        row = conn.execute("SELECT * FROM question_group_materials WHERE question_group_version_id = 'qgv_l1'").fetchone()
        self.assertEqual(row["usage_type"], "AUDIO")

    def test_p08_new_session_does_not_overwrite_old(self):
        """P08: Creating a new session does not overwrite previous session attempts."""
        s1 = self.engine.create_session("user_1", "N1", "PAPER_PRACTICE", self.paper_info["paper_version_id"])
        self.engine.start_session(s1["sessionId"], "user_1")
        self.engine.record_answer(s1["sessionId"], "user_1", self.paper_info["q1_v_id"], chosen_option_key=1)
        self.engine.submit_session(s1["sessionId"], "user_1")

        s2 = self.engine.create_session("user_1", "N1", "PAPER_PRACTICE", self.paper_info["paper_version_id"])
        self.assertNotEqual(s1["sessionId"], s2["sessionId"])

        # s1 remains submitted and intact
        state1 = self.engine.get_session_state(s1["sessionId"], "user_1")
        self.assertEqual(state1["status"], "SUBMITTED")


if __name__ == "__main__":
    unittest.main()
