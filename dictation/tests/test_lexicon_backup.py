"""A personal backup restores what it contains (LEX-16, §11.1).

Version 1 exported `contexts` in a shape the import route ignored, so exporting and
re-importing silently dropped every saved sentence a favourite came from. The identity
of a reference-less entry was also a hash of the whole object, so editing a note made
the next import create a second entry instead of updating the first.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

from lexicon_api import LexiconServices  # noqa: E402
from lexicon_fixtures import make_word_pack  # noqa: E402
from lexicon_store import LexiconStore  # noqa: E402
from local_backend import LearningStore  # noqa: E402
from test_lexicon_api import write_pack  # noqa: E402

CONTEXT = {"courseId": "c1", "sentenceId": "s3", "text": "ご意見を承ります。",
           "selection": {"start": 4, "end": 7}, "sourceRevision": "rev-1"}


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.words = make_word_pack()
        write_pack(self.root / "lexicon", "words", self.words)
        self.store = LearningStore(self.root / "learning.sqlite3"); self.addCleanup(self.store.close)
        self.s = LexiconServices(self.store, LexiconStore(self.root / "lexicon"))
        self.ref = f"lex:{self.words['packId']}#{self.words['entries'][0]['id']}"

    def fresh(self):
        """A second, empty database, which is where a restore has to actually work."""
        other = LearningStore(self.root / "restored.sqlite3")
        self.addCleanup(other.close)
        return LexiconServices(other, LexiconStore(self.root / "lexicon"))

    def seed(self):
        self.s.practice.save_user_entry({
            "sourceRef": self.ref, "headword": "承る", "reading": "うけたまわる",
            "gloss": {"zh": "恭听"}, "note": "商务场合", "tags": ["敬语"], "starred": True,
            "context": CONTEXT})
        self.s.practice.save_user_entry({
            "sourceRef": "user:mine", "headword": "自造词", "gloss": {"zh": "自己加的"},
            "note": "个人笔记"})

    def test_a_round_trip_restores_notes_tags_favourites_and_contexts(self):
        self.seed()
        payload = self.s.practice.export_personal()
        self.assertEqual(payload["schemaVersion"], 2)
        self.assertEqual(len(payload["entries"]), 2)
        self.assertEqual(payload["contexts"], [{"sourceRef": self.ref, "contexts": [CONTEXT]}])

        target = self.fresh()
        result = target.practice.import_personal(payload)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["contexts"], 1)
        restored = {entry["sourceRef"]: entry for entry in target.practice.user_entries()}
        self.assertEqual(restored[self.ref]["note"], "商务场合")
        self.assertEqual(restored[self.ref]["tags"], ["敬语"])
        self.assertTrue(restored[self.ref]["starred"])
        # The context is what v1 dropped: the sentence the favourite came from.
        self.assertEqual(target.practice.contexts(self.ref), [CONTEXT])

    def test_a_version_one_file_still_imports(self):
        self.seed()
        legacy = {"schemaVersion": 1, "items": self.s.practice.user_entries(True)}
        target = self.fresh()
        self.assertEqual(target.practice.import_personal(legacy)["count"], 2)

    def test_a_newer_format_is_refused_rather_than_half_read(self):
        with self.assertRaises(ValueError):
            self.s.practice.preview_import({"schemaVersion": 99, "entries": []})

    def test_the_identity_of_a_reference_less_entry_survives_an_edit(self):
        first = self.s.practice.preview_import({"entries": [{"headword": "手動", "reading": "しゅどう"}]})
        second = self.s.practice.preview_import(
            {"entries": [{"headword": "手動", "reading": "しゅどう", "note": "改了笔记"}]})
        # Hashing the whole object made the note part of the key, so editing it created
        # a second entry on the next import.
        self.assertEqual(first["ready"][0]["sourceRef"], second["ready"][0]["sourceRef"])

    def test_the_preview_says_what_would_change(self):
        self.seed()
        payload = self.s.practice.export_personal()
        target = self.fresh()
        first = target.practice.preview_import(payload)
        self.assertEqual(len(first["added"]), 2)
        self.assertEqual(first["updated"], [])
        self.assertEqual(first["contexts"], 1)

        target.practice.import_personal(payload)
        again = target.practice.preview_import(payload)
        self.assertEqual(again["added"], [])
        self.assertEqual(len(again["updated"]), 2)

    def test_duplicates_within_one_file_are_reported_and_applied_once(self):
        entry = {"sourceRef": "user:twice", "headword": "重复"}
        preview = self.s.practice.preview_import({"entries": [entry, dict(entry, note="第二次")]})
        self.assertEqual(preview["duplicates"], ["user:twice"])
        self.assertEqual(preview["count"], 1)

    def test_an_entry_from_an_uninstalled_pack_is_flagged_but_kept(self):
        preview = self.s.practice.preview_import(
            {"entries": [{"sourceRef": "lex:Not-installed#w_" + "a" * 24, "headword": "外部条目"}]})
        self.assertEqual(len(preview["unresolvedReferences"]), 1)
        self.assertEqual(preview["count"], 1, "the note is kept even without its pack")

    def test_a_failed_import_applies_none_of_it(self):
        self.seed()
        before = {e["sourceRef"]: e["version"] for e in self.s.practice.user_entries()}
        broken = {"entries": [
            {"sourceRef": "user:ok", "headword": "先写这条"},
            {"sourceRef": "user:bad", "headword": "第二条", "tags": "not-a-list"},
        ]}
        with self.assertRaises(ValueError):
            self.s.practice.import_personal(broken)
        # Nested per-entry commits used to leave the first entry written (§11.1).
        after = {e["sourceRef"]: e["version"] for e in self.s.practice.user_entries()}
        self.assertEqual(after, before)
        self.assertNotIn("user:ok", after)

    def test_a_restore_updates_rather_than_conflicting_on_version(self):
        self.seed()
        payload = self.s.practice.export_personal()
        # Importing the same backup twice must not raise a stale-version conflict.
        self.s.practice.import_personal(payload)
        self.s.practice.import_personal(payload)
        self.assertEqual(len(self.s.practice.user_entries()), 2)

    def test_learning_data_is_only_included_when_asked_for(self):
        self.seed()
        deck = self.store.create_deck({"dailyNew": 1, "studyTimezone": "UTC"}, self.words)
        self.store.serve_deck(deck["id"], self.words)
        self.assertNotIn("learning", self.s.practice.export_personal())
        full = self.s.practice.export_personal(include_learning=True)
        self.assertIn("learning", full)
        self.assertTrue(full["learning"]["cards"])
        self.assertTrue(full["learning"]["decks"])
        self.assertIn("srs_repetitions", full["learning"]["cards"][0])
        self.assertTrue(self.s.practice.preview_import(full)["includesLearning"])


if __name__ == "__main__":
    unittest.main()
