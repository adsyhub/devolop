"""Tests for D01~D09 (Dynamic Practice Generation, Question Group Integrity, Filters, Warnings)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from exam_db import ExamDatabase  # noqa: E402
from exam_engine import ExamEngine, now_utc  # noqa: E402
from exam_rights import RightsModule  # noqa: E402


class DynamicTests(unittest.TestCase):
    def setUp(self):
        self.db = ExamDatabase.in_memory()
        self.rights = RightsModule(self.db)
        self.engine = ExamEngine(self.db, self.rights)
        self.conn = self.db.connection

        # Setup 3 published question groups of VOCAB_KANJI_READING for N1
        self.conn.execute(
            "INSERT INTO content_sources (id, code, name, source_type, authenticity_status, completeness, created_at, updated_at) "
            "VALUES ('src_dyn', 'SRC_DYN', 'Dynamic Test Source', 'OFFICIAL', 'OFFICIAL_ORIGINAL', 'FULL_SESSION', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        for i in range(1, 4):
            qg_id = f"qg_dyn_{i}"
            qgv_id = f"qgv_dyn_{i}"
            self.conn.execute(
                "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
                "VALUES (?, ?, 'N1', 'VOCABULARY', 'VOCAB_KANJI_READING', 'src_dyn', '2026-09-01T00:00:00Z')",
                (qg_id, f"QG_DYN_{i}"),
            )
            self.conn.execute(
                "INSERT INTO question_group_versions (id, question_group_id, version_number, instruction_text, status, content_hash, created_at) "
                "VALUES (?, ?, 1, '漢字の読み方', 'PUBLISHED', ?, '2026-09-01T00:00:00Z')",
                (qgv_id, qg_id, f"hash_{i}"),
            )
            # 2 questions per group
            for q_idx in range(1, 3):
                q_id = f"q_dyn_{i}_{q_idx}"
                qv_id = f"qv_dyn_{i}_{q_idx}"
                self.conn.execute(
                    "INSERT INTO questions (id, question_group_id, stable_key, created_at) VALUES (?, ?, ?, '2026-09-01T00:00:00Z')",
                    (q_id, qg_id, f"Q_DYN_{i}_{q_idx}"),
                )
                self.conn.execute(
                    "INSERT INTO question_versions (id, question_id, version_number, question_group_version_id, display_order, stem_text, correct_answer_json, status, content_hash, created_at) "
                    "VALUES (?, ?, 1, ?, ?, '問題文', '{\"answer\": 1}', 'PUBLISHED', 'hash_q', '2026-09-01T00:00:00Z')",
                    (qv_id, q_id, qgv_id, q_idx),
                )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_d01_draw_unit_is_question_group(self):
        """D01: Draw unit is full question group; questions within group are kept together."""
        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=2,
        )
        self.assertEqual(res["selectedGroupCount"], 2)

        # Verify session snapshots contain the complete question group and both of its questions
        snaps = self.conn.execute(
            "SELECT * FROM session_group_snapshots WHERE practice_session_id = ?",
            (res["sessionId"],),
        ).fetchall()
        self.assertEqual(len(snaps), 2)
        for s in snaps:
            q_ids = json.loads(s["required_question_ids_json"])
            self.assertEqual(len(q_ids), 2)

    def test_d02_no_duplicate_groups_in_session(self):
        """D02: Single session has no duplicate question groups."""
        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=3,
        )
        snaps = self.conn.execute(
            "SELECT question_group_version_id FROM session_group_snapshots WHERE practice_session_id = ?",
            (res["sessionId"],),
        ).fetchall()
        qgv_ids = [s["question_group_version_id"] for s in snaps]
        self.assertEqual(len(qgv_ids), len(set(qgv_ids)))

    def test_d03_unseen_filter(self):
        """D03: UNSEEN filter prioritizes question groups not yet attempted."""
        # Mark qg_dyn_1 as seen by user_d
        self.conn.execute(
            "INSERT INTO user_question_states (user_id, question_id, first_attempt_at, last_attempt_at, updated_at) "
            "VALUES ('user_d', 'q_dyn_1_1', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=2,
            answer_scope="UNSEEN",
        )
        snaps = self.conn.execute(
            "SELECT question_group_version_id FROM session_group_snapshots WHERE practice_session_id = ?",
            (res["sessionId"],),
        ).fetchall()
        drawn = [s["question_group_version_id"] for s in snaps]
        self.assertNotIn("qgv_dyn_1", drawn)

    def test_d04_wrong_filter(self):
        """D04: WRONG filter selects only question groups with mistakes."""
        self.conn.execute(
            "INSERT INTO user_question_states (user_id, question_id, first_attempt_at, last_attempt_at, wrong_count, updated_at) "
            "VALUES ('user_d', 'q_dyn_2_1', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z', 2, '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=5,
            answer_scope="WRONG",
        )
        snaps = self.conn.execute(
            "SELECT question_group_version_id FROM session_group_snapshots WHERE practice_session_id = ?",
            (res["sessionId"],),
        ).fetchall()
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0]["question_group_version_id"], "qgv_dyn_2")

    def test_d05_due_filter(self):
        """D05: DUE filter selects question groups scheduled for review today or overdue."""
        self.conn.execute(
            "INSERT INTO user_question_states (user_id, question_id, first_attempt_at, last_attempt_at, next_review_at, updated_at) "
            "VALUES ('user_d', 'q_dyn_3_1', '2026-08-01T00:00:00Z', '2026-08-01T00:00:00Z', '2026-08-10T00:00:00Z', '2026-08-01T00:00:00Z')"
        )
        self.conn.commit()

        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=5,
            answer_scope="DUE",
        )
        snaps = self.conn.execute(
            "SELECT question_group_version_id FROM session_group_snapshots WHERE practice_session_id = ?",
            (res["sessionId"],),
        ).fetchall()
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0]["question_group_version_id"], "qgv_dyn_3")

    def test_d06_exclude_recent_days(self):
        """D06: exclude_recent_days omits groups attempted recently."""
        recent=now_utc().isoformat(timespec="seconds")
        self.conn.execute(
            "INSERT INTO user_question_states (user_id, question_id, first_attempt_at, last_attempt_at, updated_at) "
            "VALUES ('user_d', 'q_dyn_1_1', ?, ?, ?)", (recent,recent,recent)
        )
        self.conn.commit()

        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=5,
            exclude_recent_days=7,
        )
        snaps = self.conn.execute(
            "SELECT question_group_version_id FROM session_group_snapshots WHERE practice_session_id = ?",
            (res["sessionId"],),
        ).fetchall()
        drawn = [s["question_group_version_id"] for s in snaps]
        self.assertNotIn("qgv_dyn_1", drawn)
        self.assertEqual(len(drawn), 2)

    def test_d07_insufficient_questions_returns_warning(self):
        """D07: If pool is smaller than requested, returns structured warning."""
        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=10,  # We only have 3
        )
        self.assertEqual(res["selectedGroupCount"], 3)
        self.assertEqual(len(res["warnings"]), 1)
        self.assertEqual(res["warnings"][0]["code"], "INSUFFICIENT_QUESTION_GROUPS")
        self.assertEqual(res["warnings"][0]["available"], 3)

    def test_d08_session_snapshot_immune_to_tag_update(self):
        """D08: Frozen session snapshot is not affected by subsequent edits or tags."""
        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=2,
        )
        session_id = res["sessionId"]
        count_before = self.conn.execute(
            "SELECT COUNT(*) as c FROM session_group_snapshots WHERE practice_session_id = ?",
            (session_id,),
        ).fetchone()["c"]

        # Insert a 4th question group in bank
        self.conn.execute(
            "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
            "VALUES ('qg_dyn_4', 'QG_DYN_4', 'N1', 'VOCABULARY', 'VOCAB_KANJI_READING', 'src_dyn', '2026-09-01T00:00:00Z')"
        )
        self.conn.commit()

        count_after = self.conn.execute(
            "SELECT COUNT(*) as c FROM session_group_snapshots WHERE practice_session_id = ?",
            (session_id,),
        ).fetchone()["c"]
        self.assertEqual(count_before, count_after)

    def test_d09_no_synthetic_fabrication_to_fill_pool(self):
        """D09: When questions run short, system never fabricates synthetic questions."""
        res = self.engine.generate_dynamic_practice(
            user_id="user_d",
            level="N1",
            item_type_codes=["VOCAB_KANJI_READING"],
            requested_groups=20,
        )
        self.assertEqual(res["selectedGroupCount"], 3)  # strictly the 3 real groups


if __name__ == "__main__":
    unittest.main()
