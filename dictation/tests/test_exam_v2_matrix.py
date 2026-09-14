"""Tests for K01~K08 (Level and Item Type Matrix constraints) and V06 (Immutable Versions)."""

from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from exam_db import ExamDatabase  # noqa: E402
from exam_models import (  # noqa: E402
    ITEM_TYPE_MATRIX,
    VALID_LEVELS,
    ItemTypeSpec,
    Level,
    ScoreSection,
    TestSection,
    validate_item_type,
    validate_level,
)


class MatrixTests(unittest.TestCase):
    def setUp(self):
        self.db = ExamDatabase.in_memory()
        self.conn = self.db.connection

    def test_k01_public_api_only_accepts_n1_n2(self):
        """K01: Public interface only accepts N1 and N2."""
        self.assertEqual(validate_level("N1"), "N1")
        self.assertEqual(validate_level("N2"), "N2")
        for bad in ["N3", "N4", "N5", "N0", "other", ""]:
            with self.assertRaises(ValueError):
                validate_level(bad)

    def test_k02_admin_only_allows_n1_n2(self):
        """K02: Admin/backend models strictly enforce N1/N2."""
        self.assertEqual(VALID_LEVELS, {"N1", "N2"})
        with self.assertRaises(ValueError):
            validate_item_type("N3", "VOCAB_KANJI_READING")

    def test_k03_n1_refuses_orthography(self):
        """K03: N1 cannot use VOCAB_ORTHOGRAPHY (表記)."""
        with self.assertRaises(ValueError) as ctx:
            validate_item_type("N1", "VOCAB_ORTHOGRAPHY")
        self.assertIn("not allowed in N1", str(ctx.exception))

        # But N2 is allowed
        spec = validate_item_type("N2", "VOCAB_ORTHOGRAPHY")
        self.assertEqual(spec.code, "VOCAB_ORTHOGRAPHY")

    def test_k04_n1_refuses_word_formation(self):
        """K04: N1 cannot use VOCAB_WORD_FORMATION (語形成)."""
        with self.assertRaises(ValueError) as ctx:
            validate_item_type("N1", "VOCAB_WORD_FORMATION")
        self.assertIn("not allowed in N1", str(ctx.exception))

        # But N2 is allowed
        spec = validate_item_type("N2", "VOCAB_WORD_FORMATION")
        self.assertEqual(spec.code, "VOCAB_WORD_FORMATION")

    def test_k05_n2_refuses_reading_long(self):
        """K05: N2 cannot use READING_LONG (长篇阅读)."""
        with self.assertRaises(ValueError) as ctx:
            validate_item_type("N2", "READING_LONG")
        self.assertIn("not allowed in N2", str(ctx.exception))

        # But N1 is allowed
        spec = validate_item_type("N1", "READING_LONG")
        self.assertEqual(spec.code, "READING_LONG")

    def test_k06_listening_matrix_valid(self):
        """K06: N1 and N2 listening matrix is correct, and verbal expressions are forbidden."""
        listening_types = [
            "LISTENING_TASK_BASED",
            "LISTENING_KEY_POINTS",
            "LISTENING_GENERAL_OUTLINE",
            "LISTENING_QUICK_RESPONSE",
            "LISTENING_INTEGRATED",
        ]
        for ltype in listening_types:
            spec_n1 = validate_item_type("N1", ltype)
            spec_n2 = validate_item_type("N2", ltype)
            self.assertEqual(spec_n1.test_section, TestSection.LISTENING)
            self.assertEqual(spec_n2.score_section, ScoreSection.LISTENING)

        # LISTENING_VERBAL_EXPRESSIONS is forbidden for both N1 and N2
        with self.assertRaises(ValueError):
            validate_item_type("N1", "LISTENING_VERBAL_EXPRESSIONS")
        with self.assertRaises(ValueError):
            validate_item_type("N2", "LISTENING_VERBAL_EXPRESSIONS")

    def test_k07_invalid_combination_rejected_by_server(self):
        """K07: Unknown or invalid combinations are rejected by server validation."""
        with self.assertRaises(ValueError):
            validate_item_type("N1", "NON_EXISTENT_TYPE")

    def test_k08_invalid_combination_rejected_by_db(self):
        """K08: Database CHECK constraints prevent invalid combinations."""
        # Insert prerequisite content_source
        self.conn.execute(
            "INSERT INTO content_sources (id, code, name, source_type, authenticity_status, completeness, created_at, updated_at) "
            "VALUES ('src_1', 'SRC_001', 'Test Source', 'OFFICIAL', 'OFFICIAL_ORIGINAL', 'FULL_SESSION', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )

        # 1. N3 level in DB must fail
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
                "VALUES ('qg_bad_level', 'QG_001', 'N3', 'VOCABULARY', 'VOCAB_KANJI_READING', 'src_1', '2026-09-01T00:00:00Z')"
            )

        # 2. N1 with VOCAB_ORTHOGRAPHY must fail
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
                "VALUES ('qg_bad_n1', 'QG_002', 'N1', 'VOCABULARY', 'VOCAB_ORTHOGRAPHY', 'src_1', '2026-09-01T00:00:00Z')"
            )

        # 3. N1 with VOCAB_WORD_FORMATION must fail
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
                "VALUES ('qg_bad_n1_wf', 'QG_003', 'N1', 'VOCABULARY', 'VOCAB_WORD_FORMATION', 'src_1', '2026-09-01T00:00:00Z')"
            )

        # 4. N2 with READING_LONG must fail
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
                "VALUES ('qg_bad_n2_rl', 'QG_004', 'N2', 'READING', 'READING_LONG', 'src_1', '2026-09-01T00:00:00Z')"
            )

        # 5. Valid N1 and N2 question groups must succeed
        self.conn.execute(
            "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
            "VALUES ('qg_ok_n1', 'QG_005', 'N1', 'READING', 'READING_LONG', 'src_1', '2026-09-01T00:00:00Z')"
        )
        self.conn.execute(
            "INSERT INTO question_groups (id, stable_code, level, learning_subject, item_type_code, content_source_id, created_at) "
            "VALUES ('qg_ok_n2', 'QG_006', 'N2', 'VOCABULARY', 'VOCAB_ORTHOGRAPHY', 'src_1', '2026-09-01T00:00:00Z')"
        )
        row = self.conn.execute("SELECT COUNT(*) as c FROM question_groups").fetchone()
        self.assertEqual(row["c"], 2)

    def test_v06_published_version_immutable(self):
        """V06: Published paper and group versions cannot be modified (trigger fails)."""
        self.conn.execute(
            "INSERT INTO content_sources (id, code, name, source_type, authenticity_status, completeness, created_at, updated_at) "
            "VALUES ('src_2', 'SRC_002', 'Source 2', 'OFFICIAL', 'OFFICIAL_ORIGINAL', 'FULL_SESSION', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )
        self.conn.execute(
            "INSERT INTO papers (id, stable_code, title, level, content_source_id, completeness, created_at) "
            "VALUES ('p_1', 'P_001', 'Test Paper', 'N1', 'src_2', 'FULL_SESSION', '2026-09-01T00:00:00Z')"
        )
        self.conn.execute(
            "INSERT INTO paper_versions (id, paper_id, version_number, title, status, content_hash, created_at, published_at) "
            "VALUES ('pv_1', 'p_1', 1, 'Version 1 Published', 'PUBLISHED', 'hash123', '2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')"
        )

        # Attempting to UPDATE a published paper version must raise Integrity/DatabaseError
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            self.conn.execute("UPDATE paper_versions SET title = 'Tampered' WHERE id = 'pv_1'")
        self.assertIn("Cannot update a published paper version", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

