"""Migration and history-preservation checks for lexicon study plans."""

from __future__ import annotations

import sqlite3
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from lexicon_fixtures import make_pack  # noqa: E402
from lexicon_migrations import MIGRATIONS, VERSION, migrate  # noqa: E402
from local_backend import LearningStore, calculate_sm2, source_card_id  # noqa: E402


class LexiconMigrationTests(unittest.TestCase):
    def test_python_scheduler_matches_the_shared_browser_vectors(self):
        fixtures = json.loads((PROJECT_DIR / "tests" / "fixtures" / "srs_cases.json").read_text())
        for fixture in fixtures:
            item = fixture["input"]
            reviewed_at = datetime.fromisoformat(fixture["reviewedAtUtc"])
            reps, interval, ease, stage, next_at = calculate_sm2(
                item["srsRepetitions"], item["srsInterval"], item["srsEase"],
                fixture["grade"], reviewed_at,
            )
            expected = fixture["expected"]
            with self.subTest(fixture["name"]):
                self.assertEqual((reps, interval, ease, stage), (
                    expected["srsRepetitions"], expected["srsInterval"],
                    expected["srsEase"], expected["srsStage"],
                ))
                self.assertEqual(next_at, expected["nextReviewAt"])

    def test_an_old_vocab_database_gains_new_columns_and_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning.sqlite3"
            conn = sqlite3.connect(path)
            conn.execute(
                """
                CREATE TABLE vocab (
                    id TEXT PRIMARY KEY, term TEXT NOT NULL, reading TEXT, meaning TEXT,
                    note TEXT, course_id TEXT, sentence_id TEXT, source_text TEXT,
                    tags TEXT NOT NULL DEFAULT '[]', level TEXT NOT NULL DEFAULT '',
                    srs_stage INTEGER NOT NULL DEFAULT 0, srs_interval INTEGER NOT NULL DEFAULT 0,
                    srs_ease REAL NOT NULL DEFAULT 2.5, srs_repetitions INTEGER NOT NULL DEFAULT 0,
                    srs_lapses INTEGER NOT NULL DEFAULT 0, next_review_at TEXT NOT NULL DEFAULT '',
                    last_reviewed_at TEXT NOT NULL DEFAULT '', mastered INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit(); conn.close()

            store = LearningStore(path)
            try:
                columns = {row[1] for row in store.connection.execute("PRAGMA table_info(vocab)")}
                self.assertTrue({"source_ref", "card_payload_json", "review_suspended"} <= columns)
                tables = {row[0] for row in store.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertTrue({"lex_decks", "lex_deck_cards", "lex_daily_batches"} <= tables)
            finally:
                store.close()

    def test_pack_refresh_changes_snapshot_but_preserves_srs(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LearningStore(Path(tmp) / "learning.sqlite3")
            try:
                pack = make_pack()
                deck = store.create_deck({"dailyNew": 1, "studyTimezone": "UTC"}, pack)
                card = store.serve_deck(deck["id"], pack)["items"][0]
                reviewed = store.grade_vocab_review(card["id"], "good", reviewed_at="2026-09-03T12:00:00Z")
                revised = make_pack()
                revised["contentRevision"] = "f" * 64
                revised["entries"][0]["gloss"]["zh"] = "订正后的释义"
                store.sync_deck_pack(deck["id"], revised)
                refreshed = store._get_vocab(card["id"])
                self.assertEqual(refreshed["srsRepetitions"], reviewed["srsRepetitions"])
                self.assertEqual(refreshed["sourceRevision"], "f" * 64)
                self.assertEqual(refreshed["meaning"], "订正后的释义")
            finally:
                store.close()

    # ---- ordered, individually recorded steps (§5.4) ----------------------
    def test_every_migration_is_recorded_separately_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning.sqlite3"
            store = LearningStore(path)
            try:
                applied = {row[0] for row in store.connection.execute("SELECT version FROM lex_schema")}
                self.assertEqual(applied, {version for version, _ in MIGRATIONS})
                # Re-running is a no-op, so a failed upgrade can simply be repeated.
                self.assertEqual(migrate(store.connection, path), [])
                tables = {row[0] for row in store.connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertTrue({"lex_card_tombstones", "lex_identity_aliases",
                                 "lex_reveals", "lex_migration_reports"} <= tables)
                columns = {row[1] for row in store.connection.execute("PRAGMA table_info(vocab)")}
                self.assertIn("review_version", columns)
            finally:
                store.close()

    def test_a_failing_step_leaves_no_marker_and_keeps_the_earlier_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning.sqlite3"
            store = LearningStore(path)
            try:
                store.connection.execute("DELETE FROM lex_schema WHERE version = ?", (VERSION,))
                store.connection.commit()

                def explode(conn, db_path):
                    raise RuntimeError("boom")

                import lexicon_migrations
                original = lexicon_migrations.MIGRATIONS
                lexicon_migrations.MIGRATIONS = original[:-1] + ((VERSION, explode),)
                try:
                    with self.assertRaises(RuntimeError):
                        migrate(store.connection, path)
                finally:
                    lexicon_migrations.MIGRATIONS = original
                applied = {row[0] for row in store.connection.execute("SELECT version FROM lex_schema")}
                self.assertNotIn(VERSION, applied)
                self.assertIn(1, applied)
                # With the real step back in place the run simply succeeds.
                self.assertEqual(migrate(store.connection, path), [VERSION])
            finally:
                store.close()

    def test_a_database_holding_only_plans_is_still_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning.sqlite3"
            store = LearningStore(path)
            try:
                store.create_deck({"dailyNew": 1, "studyTimezone": "UTC"}, make_pack())
                store.connection.execute("DELETE FROM lex_schema")
                store.connection.commit()
                migrate(store.connection, path)
            finally:
                store.close()
            # The old rule only looked at `vocab`, so a plan-only database was never saved.
            self.assertTrue(list(Path(tmp).glob("*.before-lexicon-v1.bak")))

    # ---- LEX-01 duplicate card merge (§4.4) -------------------------------
    def _legacy_duplicate(self, store, card, reviewed_at, *, note=""):
        """Recreate the `<promptType>-default` row practice used to mint before LEX-01."""
        source_ref, prompt = card["sourceRef"], card["promptType"]
        old_id = source_card_id(source_ref, prompt, f"{prompt}-default")
        store.connection.execute(
            """
            INSERT INTO vocab (id, term, reading, meaning, note, course_id, sentence_id,
              source_text, tags, level, srs_stage, srs_interval, srs_ease, srs_repetitions,
              srs_lapses, next_review_at, last_reviewed_at, mastered, entry_kind, source_ref,
              prompt_type, variant_key, card_payload_json, source_revision, review_suspended,
              review_version, created_at, updated_at)
            VALUES (?, ?, '', '', ?, '', '', '', '[]', '', 2, 6, 2.5, 4, 1, ?, ?, 0, ?, ?, ?, ?,
                    '{}', '', 0, 0, ?, ?)
            """,
            (old_id, card["term"], note, reviewed_at, reviewed_at, card["entryKind"],
             source_ref, prompt, f"{prompt}-default", reviewed_at, reviewed_at),
        )
        store.connection.execute(
            "INSERT INTO lex_review_events(operation_id, vocab_id, before_json, after_json, created_at)"
            " VALUES (?, ?, '{}', '{}', ?)", (f"op_legacy_{old_id[:8]}", old_id, reviewed_at))
        store.connection.commit()
        return old_id

    def _rerun_merge(self, store, path):
        store.connection.execute("DELETE FROM lex_schema WHERE version = 3")
        store.connection.commit()
        migrate(store.connection, path)

    def test_a_duplicate_card_is_folded_onto_the_plan_card_without_summing_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning.sqlite3"
            store = LearningStore(path)
            try:
                pack = make_pack()
                deck = store.create_deck({"dailyNew": 1, "studyTimezone": "UTC"}, pack)
                card = store.serve_deck(deck["id"], pack)["items"][0]
                store.grade_vocab_review(card["id"], "good", reviewed_at="2026-01-05T09:00:00+00:00")
                old_id = self._legacy_duplicate(store, card, "2026-01-06T09:00:00+00:00")
                self._rerun_merge(store, path)

                self.assertIsNone(store._get_vocab(old_id))
                merged = store._get_vocab(card["id"])
                # The later-reviewed side supplies the state; repetitions are never added up.
                self.assertEqual(merged["srsRepetitions"], 4)
                self.assertEqual(merged["lastReviewedAt"], "2026-01-06T09:00:00+00:00")
                events = store.connection.execute(
                    "SELECT vocab_id FROM lex_review_events").fetchall()
                self.assertEqual({row["vocab_id"] for row in events}, {card["id"]})
                alias = store.connection.execute(
                    "SELECT * FROM lex_identity_aliases WHERE old_vocab_id = ?", (old_id,)).fetchone()
                self.assertEqual(alias["canonical_vocab_id"], card["id"])
            finally:
                store.close()

    def test_a_pause_on_either_half_survives_the_merge_and_conflicts_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning.sqlite3"
            store = LearningStore(path)
            try:
                pack = make_pack()
                deck = store.create_deck({"dailyNew": 1, "studyTimezone": "UTC"}, pack)
                card = store.serve_deck(deck["id"], pack)["items"][0]
                store.update_vocab(card["id"], {"note": "计划侧的笔记"})
                old_id = self._legacy_duplicate(store, card, "2026-01-06T09:00:00+00:00", note="专项侧的笔记")
                store.connection.execute("UPDATE vocab SET review_suspended = 1 WHERE id = ?", (old_id,))
                store.connection.commit()
                self._rerun_merge(store, path)

                merged = store._get_vocab(card["id"])
                self.assertTrue(merged["reviewSuspended"])
                reports = store.connection.execute(
                    "SELECT detail_json FROM lex_migration_reports WHERE kind = 'card-merge-field-conflict'"
                ).fetchall()
                self.assertEqual(len(reports), 1)
                # Both original values are preserved so either can be restored by hand.
                self.assertEqual(sorted(json.loads(reports[0][0])["fields"]["note"]),
                                 sorted(["计划侧的笔记", "专项侧的笔记"]))
            finally:
                store.close()

    def test_a_duplicate_with_no_counterpart_is_renamed_and_keeps_its_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning.sqlite3"
            store = LearningStore(path)
            try:
                pack = make_pack()
                entry = pack["entries"][0]
                card = {"sourceRef": f"lex:{pack['packId']}#{entry['id']}", "promptType": "reading",
                        "term": entry["headword"], "entryKind": "grammar"}
                old_id = self._legacy_duplicate(store, card, "2026-01-06T09:00:00+00:00")
                deck = store.create_deck({"dailyNew": 1, "studyTimezone": "UTC"}, pack)
                store.connection.execute(
                    "INSERT INTO lex_deck_cards(deck_id, source_ref, prompt_type, variant_key, ordinal,"
                    " vocab_id, introduced_at) VALUES (?, ?, 'reading', 'reading-default', 0, ?, ?)",
                    (deck["id"], card["sourceRef"], old_id, "2026-01-06T09:00:00+00:00"))
                store.connection.commit()
                self._rerun_merge(store, path)

                canonical = source_card_id(card["sourceRef"], "reading", "default")
                self.assertIsNone(store._get_vocab(old_id))
                renamed = store._get_vocab(canonical)
                self.assertEqual(renamed["variantKey"], "default")
                self.assertEqual(renamed["srsRepetitions"], 4)
                # The plan must still point at the card. Updating the id in place would
                # trip the foreign key and detach the relation instead.
                self.assertEqual(store.connection.execute(
                    "SELECT vocab_id FROM lex_deck_cards WHERE deck_id = ? AND prompt_type = 'reading'",
                    (deck["id"],),
                ).fetchone()[0], canonical)
                self.assertEqual(store.connection.execute(
                    "SELECT reason FROM lex_identity_aliases WHERE old_vocab_id = ?",
                    (old_id,)).fetchone()[0], "auto-variant-renamed")
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
