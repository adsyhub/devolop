"""Written forms, readings and senses are constrained, and the constraints are used.

The builder already stored `re_restr`, `re_nokanji`, `stagk` and `stagr`; nothing read
them, so a lookup published the record's first reading whatever matched and a favourite
of one sense overwrote a favourite of another (LEX-09, §9.2).
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

from dictionary_store import DictionaryStore  # noqa: E402
from lexicon_api import LexiconServices  # noqa: E402
from lexicon_fixtures import make_word_pack  # noqa: E402
from lexicon_practice_store import ConflictError  # noqa: E402
from lexicon_store import LexiconStore  # noqa: E402
from local_backend import LearningStore  # noqa: E402
from test_lexicon_api import write_pack  # noqa: E402

# 「大人」reads おとな or だいにん depending on the sense, and 「たいじん」only applies to
# one of them: a real shape the restrictions exist to express.
ENTRY = {
    "id": "1414870",
    "sourceRef": "dict:jmdict#1414870",
    "kind": "word",
    "headword": "大人",
    "reading": "おとな",
    "writtenForms": ["大人", "成人"],
    "readings": [
        {"text": "おとな", "restrictions": [], "noKanji": False},
        {"text": "せいじん", "restrictions": ["成人"], "noKanji": False},
        {"text": "たいじん", "restrictions": ["大人"], "noKanji": False},
    ],
    "senses": [
        {"key": "a" * 20, "gloss": ["adult"], "pos": ["n"],
         "writtenRestrictions": [], "readingRestrictions": ["おとな", "せいじん"], "notes": []},
        {"key": "b" * 20, "gloss": ["person of magnanimity"], "pos": ["n"],
         "writtenRestrictions": ["大人"], "readingRestrictions": ["たいじん"], "notes": ["archaic"]},
    ],
    "pos": ["n"],
    "common": True,
    "gloss": {"en": "adult; person of magnanimity"},
}


def build_dictionary(path: Path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE entries(id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE forms(entry_id TEXT NOT NULL, text TEXT NOT NULL, normalized TEXT NOT NULL, roman TEXT NOT NULL);
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE sense_keys(entry_id TEXT, sense_key TEXT, data TEXT, PRIMARY KEY(entry_id, sense_key));
        """
    )
    connection.execute("INSERT INTO entries VALUES (?, ?)", (ENTRY["id"], json.dumps(ENTRY, ensure_ascii=False)))
    for text, normalized in [("大人", "大人"), ("成人", "成人"), ("おとな", "おとな"),
                             ("せいじん", "せいじん"), ("たいじん", "たいじん")]:
        connection.execute("INSERT INTO forms VALUES (?, ?, ?, '')", (ENTRY["id"], text, normalized))
    connection.executemany("INSERT INTO metadata VALUES (?, ?)", [
        ("entries", "1"), ("sourceSha256", "v1"), ("fts", "none")])
    connection.commit()
    connection.close()


class SenseSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "assets/dictionary").mkdir(parents=True)
        build_dictionary(self.root / "assets/dictionary/jmdict.sqlite3")
        write_pack(self.root / "lexicon", "words", make_word_pack())
        self.store = LearningStore(self.root / "learning.sqlite3"); self.addCleanup(self.store.close)
        self.s = LexiconServices(self.store, LexiconStore(self.root / "lexicon"))
        self.dictionary = self.s.dictionary

    def test_a_reading_restricted_to_another_spelling_is_not_offered(self):
        readings = [r["text"] for r in self.dictionary.readings_for(ENTRY, "大人")]
        self.assertEqual(readings, ["おとな", "たいじん"])
        self.assertEqual([r["text"] for r in self.dictionary.readings_for(ENTRY, "成人")],
                         ["おとな", "せいじん"])

    def test_a_sense_restricted_to_another_reading_is_not_offered(self):
        senses = self.dictionary.senses_for(ENTRY, "大人", "たいじん")
        self.assertEqual([s["gloss"] for s in senses], [["person of magnanimity"]])
        self.assertEqual([s["gloss"] for s in self.dictionary.senses_for(ENTRY, "大人", "おとな")],
                         [["adult"]])

    def test_the_options_tree_only_contains_compatible_combinations(self):
        options = self.dictionary.selection_options(ENTRY)
        tree = {form["writtenForm"]: {r["reading"]: [s["gloss"][0] for s in r["senses"]]
                                      for r in form["readings"]}
                for form in options["writtenForms"]}
        self.assertEqual(tree["成人"], {"おとな": ["adult"], "せいじん": ["adult"]})
        self.assertEqual(tree["大人"]["たいじん"], ["person of magnanimity"])
        self.assertEqual(options["dictionaryVersion"], "v1")

    def test_a_lookup_reports_the_reading_of_what_actually_matched(self):
        by_form = {row["id"]: row for row in self.dictionary.search("成人")}
        hit = by_form[ENTRY["id"]]
        # The record's first reading is おとな; 成人 must not be published as たいじん.
        self.assertEqual(hit["matchedForm"], "成人")
        self.assertEqual(hit["readingCandidates"], ["おとな", "せいじん"])
        self.assertNotIn("たいじん", hit["readingCandidates"])
        self.assertEqual(hit["senseCount"], 2)

    def test_two_senses_of_one_entry_are_two_favourites(self):
        first = self.s.practice.save_user_entry({
            "sourceRef": f"dict:jmdict#{ENTRY['id']}/{'a' * 20}", "headword": "大人",
            "starred": True, "gloss": {"en": "adult"},
            "selection": {"writtenForm": "大人", "reading": "おとな",
                          "senseKeys": ["a" * 20], "dictionaryVersion": "v1"}})
        second = self.s.practice.save_user_entry({
            "sourceRef": f"dict:jmdict#{ENTRY['id']}/{'b' * 20}", "headword": "大人",
            "starred": True, "gloss": {"en": "person of magnanimity"},
            "selection": {"writtenForm": "大人", "reading": "たいじん",
                          "senseKeys": ["b" * 20], "dictionaryVersion": "v1"}})
        self.assertNotEqual(first["sourceRef"], second["sourceRef"])
        saved = {entry["sourceRef"]: entry for entry in self.s.practice.user_entries()}
        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[second["sourceRef"]]["selection"]["reading"], "たいじん")

    def test_an_invalid_sense_key_is_refused(self):
        with self.assertRaises(ValueError):
            self.s.practice.save_user_entry({
                "sourceRef": f"dict:jmdict#{ENTRY['id']}", "headword": "大人",
                "selection": {"senseKeys": ["not-a-key"]}})

    def test_an_old_favourite_is_unchosen_rather_than_the_first_sense(self):
        self.s.practice.save_user_entry({
            "sourceRef": f"dict:jmdict#{ENTRY['id']}", "headword": "大人", "starred": True})
        from lexicon_api import LexiconWorkspaceMixin
        route = LexiconWorkspaceMixin()._workspace_route(
            "GET", f"/api/dictionary/entries/{ENTRY['id']}", {}, self.s)
        self.assertFalse(route["selection"]["chosen"])
        self.assertFalse(route["selection"]["resolved"])
        self.assertEqual(route["selection"]["senses"], [])

    def test_a_changed_dictionary_offers_candidates_instead_of_substituting(self):
        stale = {"writtenForm": "大人", "reading": "おとな",
                 "senseKeys": ["c" * 20], "dictionaryVersion": "v0"}
        resolved = self.dictionary.resolve_selection(ENTRY, stale)
        self.assertFalse(resolved["resolved"])
        self.assertTrue(resolved["dictionaryChanged"])
        self.assertEqual(resolved["missingSenseKeys"], ["c" * 20])
        # Candidates to re-confirm, not an automatic swap to a different meaning.
        self.assertEqual([c["gloss"] for c in resolved["candidates"]], [["adult"]])

    def test_practising_a_chosen_sense_uses_only_that_sense(self):
        ref = f"dict:jmdict#{ENTRY['id']}/{'b' * 20}"
        self.s.practice.save_user_entry({
            "sourceRef": ref, "headword": "大人", "starred": True,
            "selection": {"writtenForm": "大人", "reading": "たいじん",
                          "senseKeys": ["b" * 20], "dictionaryVersion": "v1"}})
        entries = [entry for _pack, entry in self.s.practice.entries({"sourceRefs": [ref]})]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["reading"], "たいじん")
        self.assertEqual(entry["gloss"]["en"], "person of magnanimity")
        self.assertEqual(entry["dictRef"]["senseKeys"], ["b" * 20])
        self.assertNotIn("adult", entry["gloss"]["en"])


if __name__ == "__main__":
    unittest.main()
