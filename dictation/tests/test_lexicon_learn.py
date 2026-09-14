"""Studying an entry creates its review card, without needing a plan first.

「今日背诵」only shows cards a plan has already introduced and that are due, so with no
plan it is empty, and 「学习本单元」went to the plan form. Reading through a unit
therefore meant opening each of its entries by hand. `introduce()` is the missing
primitive: "I have studied this" turns into a card now, through the same identity path a
plan uses, so the two never produce two cards for one ability (ADR-LEX-007).
"""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

from lexicon_api import LexiconServices  # noqa: E402
from lexicon_exercise import source_ref  # noqa: E402
from lexicon_fixtures import make_pack, make_word_pack  # noqa: E402
from lexicon_schema import content_revision  # noqa: E402
from lexicon_store import LexiconStore  # noqa: E402
from local_backend import LearningStore, source_card_id  # noqa: E402
from test_lexicon_api import write_pack  # noqa: E402


class LearnWalkthroughTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.words = make_word_pack()
        self.grammar = make_pack()
        write_pack(self.root / "lexicon", "words", self.words)
        write_pack(self.root / "lexicon", "grammar", self.grammar)
        self.store = LearningStore(self.root / "learning.sqlite3"); self.addCleanup(self.store.close)
        self.s = LexiconServices(self.store, LexiconStore(self.root / "lexicon"))
        self.ref = f"lex:{self.words['packId']}#{self.words['entries'][0]['id']}"

    def introduce(self, refs=None, types=None):
        pairs = list(self.s.practice.entries({"sourceRefs": refs or [self.ref]}))
        return self.s.learning.introduce(pairs, types or ["recall"])

    def test_studying_an_entry_puts_it_in_the_review_queue(self):
        # The state a new learner is in: no plan, nothing due.
        self.assertEqual(self.s.learning.today()["count"], 0)
        result = self.introduce()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["skipped"], [])
        card = result["items"][0]
        self.assertEqual((card["sourceRef"], card["promptType"], card["variantKey"]),
                         (self.ref, "recall", "default"))
        # Due now, and reachable with no plan at all (LEX-06's unplanned source).
        queue = self.s.learning.today()
        self.assertEqual(queue["count"], 1)
        self.assertEqual(queue["items"][0]["id"], card["id"])

    def test_the_card_is_the_same_one_a_plan_would_have_served(self):
        card = self.introduce()["items"][0]
        deck = self.store.create_deck({"dailyNew": 5, "studyTimezone": "UTC"}, self.words)
        self.s.learning.save_settings(deck["id"], {"packSlugs": ["words"], "promptTypes": ["recall"]})
        served = self.store.serve_deck(deck["id"], self.s.learning.pack(deck["id"]))["items"]
        # One ability, one card, whichever route reached it first.
        self.assertEqual([item["id"] for item in served], [card["id"]])
        self.assertEqual(
            self.store.connection.execute(
                "SELECT COUNT(*) FROM vocab WHERE source_ref = ?", (self.ref,)).fetchone()[0], 1)

    def test_studying_the_same_entry_twice_does_not_reset_its_progress(self):
        card = self.introduce()["items"][0]
        graded = self.store.grade_vocab_review(card["id"], "good", "op_first")
        again = self.introduce()
        self.assertEqual(again["count"], 1)
        self.assertEqual(again["items"][0]["srsRepetitions"], graded["srsRepetitions"])
        self.assertEqual(again["items"][0]["nextReviewAt"], graded["nextReviewAt"])

    def test_several_directions_can_be_learned_at_once(self):
        result = self.introduce(types=["recall", "production", "reading"])
        self.assertEqual(
            sorted(item["promptType"] for item in result["items"]),
            ["production", "reading", "recall"])
        for item in result["items"]:
            self.assertEqual(item["variantKey"], "default")

    def test_a_direction_the_entry_cannot_support_is_reported_not_invented(self):
        # A grammar entry has no reading to write, so `reading` is not offered for it.
        grammar_ref = f"lex:{self.grammar['packId']}#{self.grammar['entries'][0]['id']}"
        result = self.introduce([grammar_ref], ["reading"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["skipped"], [
            {"sourceRef": grammar_ref, "headword": self.grammar["entries"][0]["headword"],
             "reason": "no-direction"}])

    def test_an_unknown_direction_is_refused(self):
        with self.assertRaises(ValueError):
            self.introduce(types=["nonsense"])

    def test_a_deleted_card_is_not_resurrected_by_studying_the_entry_again(self):
        card = self.introduce()["items"][0]
        self.store.delete_vocab(card["id"], "op_delete")
        result = self.introduce()
        # Studying is not an undo: the deletion was deliberate (LEX-02, §5.1.3).
        self.assertEqual(result["count"], 0)
        self.assertIsNone(self.store._get_vocab(card["id"]))

    def test_a_grammar_cloze_direction_keeps_its_example_variant(self):
        grammar_ref = f"lex:{self.grammar['packId']}#{self.grammar['entries'][0]['id']}"
        result = self.introduce([grammar_ref], ["cloze"])
        self.assertEqual(len(result["items"]), 1)
        card = result["items"][0]
        # The variant is the example's, not a positional number, so adding an example
        # later does not renumber this card (§4.2).
        self.assertEqual(card["variantKey"], "cloze-ex1")
        self.assertEqual(card["id"], source_card_id(grammar_ref, "cloze", "cloze-ex1"))

    def test_a_personal_entry_can_be_learned_too(self):
        self.s.practice.save_user_entry(
            {"sourceRef": "user:mine", "headword": "自造词", "gloss": {"zh": "自己加的"}})
        result = self.introduce(["user:mine"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["term"], "自造词")

    def test_the_whole_unit_can_be_learned_in_one_call(self):
        refs = [source_ref(self.grammar, entry) for entry in self.grammar["entries"]]
        result = self.introduce(refs, ["recall"])
        self.assertEqual(result["count"], len(refs))
        self.assertEqual(self.s.learning.today()["count"], len(refs))

    def test_a_content_revision_is_recorded_so_refreshes_keep_the_history(self):
        card = self.introduce()["items"][0]
        self.assertEqual(card["sourceRevision"], self.words["contentRevision"])
        self.assertNotEqual(card["meaning"], "订正后的释义")
        revised = copy.deepcopy(self.words)
        revised["entries"][0]["gloss"]["zh"] = "订正后的释义"
        # A hand-written revision fails the audit, which blocks the pack: the refresh
        # has to be a real revision for this to test what it says it tests.
        revised["contentRevision"] = content_revision(revised)
        write_pack(self.root / "lexicon", "words", revised)
        self.s.lexicon = LexiconStore(self.root / "lexicon")
        self.s.learning.lexicon = self.s.lexicon
        self.s.practice.lexicon = self.s.lexicon
        graded = self.store.grade_vocab_review(card["id"], "good", "op_g")
        refreshed = self.introduce()["items"][0]
        self.assertEqual(refreshed["meaning"], "订正后的释义")
        self.assertEqual(refreshed["srsRepetitions"], graded["srsRepetitions"])


class LearnRouteTests(unittest.TestCase):
    """The HTTP surface the walkthrough actually calls."""

    def setUp(self):
        from support import RunningServer, write_course
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        manifest = write_course(root / "courses/demo")
        self.words = make_word_pack()
        write_pack(root / "lexicon", "words", self.words)
        self.server = RunningServer(manifest, root / "data", lexicon_root=root / "lexicon")
        self.server.__enter__(); self.addCleanup(lambda: self.server.__exit__(None, None, None))
        self.ref = f"lex:{self.words['packId']}#{self.words['entries'][0]['id']}"

    def call(self, method, path, body=None):
        import json
        code, data = self.server.request(
            method, path, origin=f"http://127.0.0.1:{self.server.port}", body=body)
        return code, json.loads(data) if data else {}

    def test_the_route_introduces_and_reports_what_it_could_not_find(self):
        code, result = self.call("POST", "/api/lexicon/introduce", {
            "sourceRefs": [self.ref, "lex:Not-installed#w_" + "a" * 24], "promptTypes": ["recall"]})
        self.assertEqual(code, 200, result)
        self.assertEqual(result["count"], 1)
        # A reference the installed packs cannot resolve is named, not silently dropped.
        self.assertEqual(result["missing"], ["lex:Not-installed#w_" + "a" * 24])

    def test_the_route_validates_its_input(self):
        for bad in ({"sourceRefs": []}, {"sourceRefs": "not-a-list"},
                    {"sourceRefs": [1, 2]}, {"sourceRefs": [self.ref], "promptTypes": "recall"},
                    {"sourceRefs": [self.ref], "promptTypes": ["nope"]}):
            code, _ = self.call("POST", "/api/lexicon/introduce", bad)
            self.assertEqual(code, 400, bad)

    def test_a_card_introduced_over_http_is_due_and_gradeable(self):
        _code, result = self.call("POST", "/api/lexicon/introduce",
                                  {"sourceRefs": [self.ref], "promptTypes": ["recall"]})
        card = result["items"][0]
        _code, today = self.call("GET", "/api/lexicon/today")
        self.assertIn(card["id"], [item["id"] for item in today["items"]])
        code, graded = self.call("POST", "/api/vocab/review", {
            "vocabId": card["id"], "grade": "good", "expectedReviewVersion": card["reviewVersion"]})
        self.assertEqual(code, 200, graded)
        self.assertEqual(graded["item"]["srsRepetitions"], 1)


if __name__ == "__main__":
    unittest.main()
