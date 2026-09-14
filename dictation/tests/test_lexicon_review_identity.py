"""One ability is one card, a deletion stays deleted, and one operation counts once.

These cover the P0 findings LEX-01, LEX-02 and LEX-03: the plan and the practice
session used to mint two different SRS cards for the same recall ability, deleting a
card only removed a row that the next answer rebuilt, and an operation id was trusted
without checking what it was an operation for.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

from lexicon_api import LexiconServices  # noqa: E402
from lexicon_exercise import questions_for, review_target  # noqa: E402
from lexicon_fixtures import make_word_pack  # noqa: E402
from lexicon_practice_store import ConflictError  # noqa: E402
from lexicon_store import LexiconStore  # noqa: E402
from local_backend import DeletedCardError, LearningStore, ReviewConflictError, source_card_id  # noqa: E402
from test_lexicon_api import write_pack  # noqa: E402

# The clock is real, so review timestamps have to be in the past to be accepted.
EARLIER = "2026-01-05T09:00:00+00:00"
LATER = "2026-01-05T18:00:00+00:00"


class ReviewIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.words = make_word_pack()
        write_pack(self.root / "lexicon", "words", self.words)
        self.store = LearningStore(self.root / "learning.sqlite3"); self.addCleanup(self.store.close)
        self.s = LexiconServices(self.store, LexiconStore(self.root / "lexicon"))

    def deck(self, **settings):
        deck = self.store.create_deck({"dailyNew": 5, "studyTimezone": "UTC"}, self.words)
        self.s.learning.save_settings(deck["id"], {"packSlugs": ["words"], **settings})
        return deck["id"]

    def practise(self, exercise_type, answer, operation_id, **payload):
        session = self.s.practice.create(
            {"types": [exercise_type], "kind": "word", "count": 1, "packSlugs": ["words"]}
        )
        cursor = session["state"]["queue"][session["state"]["cursor"]]
        return self.s.practice.answer(
            session["id"], {**cursor, "answer": answer, "version": session["version"], **payload}, operation_id
        )

    def source_cards(self):
        return self.store.connection.execute(
            "SELECT id, prompt_type, variant_key FROM vocab WHERE source_ref <> '' ORDER BY prompt_type"
        ).fetchall()

    # ---- LEX-01 ------------------------------------------------------------
    def test_the_plan_and_a_practice_session_share_one_recall_card(self):
        deck = self.deck(promptTypes=["recall"])
        served = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"]
        result = self.practise("recall", {"grade": "good"}, "op_recall")["result"]
        self.assertEqual([(row["prompt_type"], row["variant_key"]) for row in self.source_cards()],
                         [("recall", "default")])
        self.assertEqual(result["vocabId"], served[0]["id"])

    def test_different_directions_of_one_entry_stay_separate_cards(self):
        self.practise("recall", {"grade": "good"}, "op_recall")
        self.practise("reading", "うけたまわる", "op_reading")
        self.assertEqual([(row["prompt_type"], row["variant_key"]) for row in self.source_cards()],
                         [("reading", "default"), ("recall", "default")])

    def test_a_reading_card_keeps_its_direction_when_it_comes_due(self):
        result = self.practise("reading", "うけたまわる", "op_reading")["result"]
        # A correct answer schedules the card forward; wind it back to the day it is due.
        self.store.connection.execute(
            "UPDATE vocab SET next_review_at = ? WHERE id = ?", (EARLIER, result["vocabId"])
        )
        self.store.connection.commit()
        due = [card for card in self.store.due_vocab() if card["id"] == result["vocabId"]]
        self.assertEqual(len(due), 1)
        snapshot = due[0]["cardPayload"]["exercise"]
        # Reviewing this as a plain flip card would silently drop the reading direction.
        self.assertEqual((snapshot["type"], snapshot["mode"]), ("reading", "input"))
        self.assertEqual(due[0]["promptType"], "reading")
        self.assertEqual(due[0]["cardPayload"]["reviewTarget"], snapshot["reviewTarget"])

    def test_the_adapter_and_the_plan_agree_on_every_target(self):
        pack = self.s.lexicon.get_pack("words"); entry = pack["entries"][0]
        for question in questions_for(pack, entry):
            target = question["reviewTarget"]
            self.assertEqual(
                target, review_target(target["sourceRef"], target["promptType"], target["variantKey"])
            )
        deck = self.deck(quotaUnit="entry", promptTypes=["production"])
        served = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"]
        # "Capability exists but the plan has zero cards" is not an acceptable outcome.
        self.assertEqual([(c["promptType"], c["variantKey"]) for c in served], [("production", "default")])

    def test_a_plan_served_reading_card_carries_the_question_it_reviews(self):
        deck = self.deck(quotaUnit="entry", promptTypes=["reading"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        snapshot = card["cardPayload"]["template"]["exercise"]
        # Without the snapshot this card would come due as a flip card and lose its direction.
        self.assertEqual((snapshot["type"], snapshot["mode"]), ("reading", "input"))
        self.assertEqual(snapshot["reviewTarget"]["promptType"], "reading")

    # ---- LEX-02 ------------------------------------------------------------
    def test_a_deleted_card_is_not_rebuilt_by_practice_or_by_the_plan(self):
        deck = self.deck(promptTypes=["recall"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        self.store.delete_vocab(card["id"], "op_delete")

        replay = self.practise("recall", {"grade": "good"}, "op_after_delete")["result"]
        self.assertFalse(replay["srsApplied"])
        self.assertIn("已删除", replay["srsConflict"])
        self.store.sync_deck_pack(deck, self.s.learning.pack(deck))
        self.store.serve_deck(deck, self.s.learning.pack(deck))
        self.assertIsNone(self.store._get_vocab(card["id"]))
        # The answer itself is still recorded; only the scheduling was refused.
        self.assertEqual(
            self.store.connection.execute("SELECT COUNT(*) FROM lex_attempts").fetchone()[0], 1
        )

    def test_deleting_twice_is_the_same_deletion_and_restoring_is_explicit(self):
        deck = self.deck(promptTypes=["recall"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        first = self.store.delete_vocab(card["id"], "op_delete")
        again = self.store.delete_vocab(card["id"], "op_delete")
        self.assertEqual(first["tombstoneVersion"], again["tombstoneVersion"])
        self.assertTrue(again["duplicate"])

        with self.assertRaises(ReviewConflictError):
            self.store.restore_vocab(card["id"], first["tombstoneVersion"] + 5)
        self.store.restore_vocab(card["id"], first["tombstoneVersion"])
        row = self.store.connection.execute(
            "SELECT introduced_at FROM lex_deck_cards WHERE deck_id = ?", (deck,)
        ).fetchone()
        self.assertEqual(row["introduced_at"], "")

    def test_grading_a_deleted_card_is_refused_rather_than_recreating_it(self):
        deck = self.deck(promptTypes=["recall"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        self.store.delete_vocab(card["id"], "op_delete")
        with self.assertRaises(DeletedCardError):
            self.store.grade_vocab_review(card["id"], "good", "op_replay", EARLIER)

    def test_batch_delete_and_restore_behave_like_the_single_card_paths(self):
        deck = self.deck(promptTypes=["recall"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        # A list where a dict is expected must not reach the database layer.
        result = self.store.batch_update_vocab("delete", [card["id"]], {"operationIds": ["op_wrong_shape"]})
        self.assertEqual(result["updated"], 1)
        self.assertIsNone(self.store._get_vocab(card["id"]))

        self.store.batch_update_vocab("restore", [card["id"], "v_missing"], {})
        row = self.store.connection.execute(
            "SELECT introduced_at FROM lex_deck_cards WHERE deck_id = ?", (deck,)
        ).fetchone()
        self.assertEqual(row["introduced_at"], "")

    def test_a_card_with_no_content_source_can_also_be_deleted_for_good(self):
        item = self.store.create_vocab({"term": "手入力", "meaning": "手动加入"})
        self.store.delete_vocab(item["id"], "op_manual")
        tombstone = self.store.connection.execute(
            "SELECT source_ref FROM lex_card_tombstones WHERE vocab_id = ?", (item["id"],)
        ).fetchone()
        self.assertEqual(tombstone["source_ref"], f"vocab:{item['id']}")

    # ---- LEX-03 ------------------------------------------------------------
    def test_two_tabs_holding_the_same_review_version_cannot_both_advance(self):
        deck = self.deck(promptTypes=["recall"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        stale = card["reviewVersion"]
        self.store.grade_vocab_review(card["id"], "good", "op_tab_one", EARLIER, stale)
        with self.assertRaises(ReviewConflictError):
            self.store.grade_vocab_review(card["id"], "good", "op_tab_two", LATER, stale)

    def test_a_content_refresh_does_not_invalidate_an_in_flight_grade(self):
        deck = self.deck(promptTypes=["recall"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        revised = make_word_pack()
        revised["entries"][0]["gloss"]["zh"] = "订正后的释义"
        revised["contentRevision"] = "f" * 64
        self.store.sync_deck_pack(deck, revised)
        # updated_at moved, review_version did not: the queued grade is still valid.
        self.store.grade_vocab_review(card["id"], "good", "op_after_refresh", EARLIER, card["reviewVersion"])

    def test_an_operation_id_only_ever_replays_its_own_request(self):
        deck = self.deck(promptTypes=["recall"])
        card = self.store.serve_deck(deck, self.s.learning.pack(deck))["items"][0]
        first = self.store.grade_vocab_review(card["id"], "good", "op_once", EARLIER)
        self.assertEqual(self.store.grade_vocab_review(card["id"], "good", "op_once", EARLIER), first)
        with self.assertRaises(ReviewConflictError):
            self.store.grade_vocab_review(card["id"], "easy", "op_once", EARLIER)
        other = self.store.create_vocab({"term": "別", "meaning": "另一张"})
        with self.assertRaises(ReviewConflictError):
            self.store.grade_vocab_review(other["id"], "good", "op_once", EARLIER)

    def test_a_practice_operation_id_is_checked_against_its_answer(self):
        first = self.practise("reading", "うけたまわる", "op_answer")
        self.assertTrue(first["result"]["srsApplied"])
        session = first["session"]
        cursor = {"itemId": session["attempts"][0]["itemId"], "round": 0}
        with self.assertRaises(ConflictError):
            self.s.practice.answer(session["id"], {**cursor, "answer": "ちがう"}, "op_answer")

    def test_a_hint_is_a_sequenced_replayable_event(self):
        session = self.s.practice.create(
            {"types": ["reading"], "kind": "word", "count": 1, "packSlugs": ["words"]}
        )
        item = session["state"]["queue"][0]["itemId"]
        first = self.s.practice.expose(session["id"], {"itemId": item, "round": 0}, "op_hint")
        replay = self.s.practice.expose(session["id"], {"itemId": item, "round": 0}, "op_hint")
        self.assertEqual(first["sequence"], replay["sequence"])
        self.assertTrue(replay["duplicate"])
        with self.assertRaises(ConflictError):
            self.s.practice.expose(session["id"], {"itemId": item, "round": 1}, "op_hint")
        answer = self.s.practice.answer(
            session["id"], {"itemId": item, "round": 0, "answer": "うけたまわる"}, "op_answer"
        )
        # The hint has to come before the answer it assisted, by sequence, not by clock.
        self.assertGreater(answer["result"]["sequence"], first["sequence"])
        self.assertEqual(answer["result"]["classification"], "assisted")


if __name__ == "__main__":
    unittest.main()
