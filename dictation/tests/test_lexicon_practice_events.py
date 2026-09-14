"""Group feedback stays inside the session, and a skip is not an answer.

Covers LEX-10 and LEX-11: `answers` used to withhold the result while `stats` and
`mistakes` already reported it, the public choice ids were the authored ones (the
correct option of a generated item is literally called `answer`), and a session where
every task was skipped still submitted as `completed`.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

from lexicon_api import LexiconServices  # noqa: E402
from lexicon_exercise import choice_alias, public_question, questions_for, review_content_hash  # noqa: E402
from lexicon_fixtures import make_pack, make_word_pack  # noqa: E402
from lexicon_practice_store import ConflictError  # noqa: E402
from lexicon_schema import prepare_pack  # noqa: E402
from lexicon_store import LexiconStore  # noqa: E402
from local_backend import LearningStore  # noqa: E402
from test_lexicon_api import write_pack  # noqa: E402


def reviewed_choice_pack():
    """A word pack whose meaning question is genuinely reviewed, so it can be served."""
    pack = make_word_pack()
    spec = {
        "type": "meaning", "mode": "choice", "variantKey": "meaning-authored",
        "prompt": "「承る」在本条中的意思是：",
        "choices": [
            {"id": "answer", "label": "恭听、接受", "rationale": "本条释义。"},
            {"id": "other-0", "label": "承担费用", "rationale": "与本条义项无关。"},
        ],
        "acceptedAnswers": ["answer"],
        "explanation": "本条取「恭听」义。",
        "evidence": {"method": "authored"},
    }
    spec["reviewStatus"] = "reviewed"
    spec["review"] = {"method": "manual", "reviewer": "审核人",
                      "reviewedAt": "2026-01-05T00:00:00+00:00",
                      "contentHash": review_content_hash(spec)}
    pack["entries"][0]["exerciseTemplates"] = [spec]
    return prepare_pack(pack)


class PracticeHarness:
    """Fixture and helpers shared by the practice suites; not a test case itself."""

    def build(self, word_pack):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        write_pack(self.root / "lexicon", "words", word_pack)
        write_pack(self.root / "lexicon", "grammar", make_pack())
        self.store = LearningStore(self.root / "learning.sqlite3"); self.addCleanup(self.store.close)
        self.s = LexiconServices(self.store, LexiconStore(self.root / "lexicon"))

    def session(self, **payload):
        return self.s.practice.create({"kind": "word", "count": 1, "packSlugs": ["words"], **payload})

    def answer(self, session, value, operation, **extra):
        state = self.s.practice.get(session["id"])["state"]
        cursor = state["queue"][state["cursor"]]
        return self.s.practice.answer(session["id"], {**cursor, "answer": value, **extra}, operation)

    def drain(self, session, prefix="op_drain"):
        """Answer every remaining task, including retries a wrong answer queued.

        Choice order is seeded from the session id, so which option is correct varies;
        a test that assumes one answer finishes the queue is flaky by construction.
        """
        published = {item["id"]: item for item in self.s.practice.get(session["id"])["items"]}
        for index in range(60):
            state = self.s.practice.get(session["id"])["state"]
            if state["cursor"] >= len(state["queue"]):
                return
            task = state["queue"][state["cursor"]]
            question = published[task["itemId"]]
            if question["mode"] == "choice":
                value = question["choices"][0]["id"]
            elif question["mode"] == "self":
                value = {"grade": "good"}
            elif question["mode"] == "order":
                value = [token["id"] for token in question["tokens"]]
            else:
                value = "うけたまわる"
            self.answer(session, value, f"{prefix}_{index}")


class PracticeEventTests(PracticeHarness, unittest.TestCase):
    def setUp(self):
        self.build(reviewed_choice_pack())

    # ---- LEX-10 -----------------------------------------------------------
    def test_the_public_choice_id_carries_no_answer_meaning(self):
        session = self.session(types=["meaning"])
        published = session["items"][0]
        ids = [choice["id"] for choice in published["choices"]]
        # The authored id of the correct option is "answer"; publishing it gives the
        # answer away regardless of how the options are ordered.
        self.assertNotIn("answer", ids)
        for value in ids:
            self.assertRegex(value, r"^c_[0-9a-f]{16}$")
        self.assertEqual(len(set(ids)), len(ids))

    def test_a_public_choice_id_still_scores_against_the_private_one(self):
        session = self.session(types=["meaning"])
        published = session["items"][0]
        private = self.store.connection.execute(
            "SELECT items_json FROM lex_sessions WHERE id = ?", (session["id"],)).fetchone()
        self.assertIn('"answer"', private["items_json"], "the private id is kept server-side")
        aliases = choice_alias(
            [q for q in questions_for(self.s.lexicon.get_pack("words"), self.s.lexicon.get_pack("words")["entries"][0])
             if q["type"] == "meaning"][0], session["id"])
        result = self.answer(session, aliases["answer"], "op_choice")["result"]
        self.assertEqual(result["classification"], "correct")
        # Feedback speaks the same public ids, so the UI can match them up.
        self.assertEqual({c["id"] for c in result["choices"]}, set(a for a in aliases.values()))

    def test_the_alias_does_not_leak_across_sessions(self):
        first, second = self.session(types=["meaning"]), self.session(types=["meaning"])
        self.assertNotEqual([c["id"] for c in first["items"][0]["choices"]],
                            [c["id"] for c in second["items"][0]["choices"]])

    def test_group_feedback_is_not_readable_from_any_other_route(self):
        session = self.session(types=["reading"], feedback="end")
        result = self.answer(session, "まちがい", "op_end")["result"]
        self.assertNotIn("correct", result)
        self.assertEqual(self.s.practice.mistakes(), [])
        self.assertEqual(self.s.practice.stats()["totalAttempts"], 0)
        history = self.s.practice.get(session["id"])
        self.assertNotIn("result", history["attempts"][0])
        self.s.practice.submit(session["id"])
        self.assertEqual(len(self.s.practice.mistakes()), 1)
        self.assertEqual(self.s.practice.stats()["totalAttempts"], 1)

    def test_an_unsubmitted_group_session_does_not_hide_other_sessions(self):
        finished = self.session(types=["reading"])
        self.answer(finished, "うけたまわる", "op_done")
        self.s.practice.submit(finished["id"])
        pending = self.session(types=["reading"], feedback="end")
        self.answer(pending, "まちがい", "op_pending")
        # Only the unsubmitted session is withheld; earlier work stays visible.
        self.assertEqual(self.s.practice.stats()["totalAttempts"], 1)

    def test_self_assessment_cannot_be_combined_with_group_feedback(self):
        with self.assertRaises(ValueError) as caught:
            self.session(types=["recall"], feedback="end")
        self.assertIn("自评", str(caught.exception))

    # ---- LEX-11 -----------------------------------------------------------
    def test_skipping_everything_does_not_submit_as_complete(self):
        session = self.session(types=["reading"])
        for index in range(3):
            self.answer(session, None, f"op_skip_{index}", skipped=True)
        with self.assertRaises(ConflictError) as caught:
            self.s.practice.submit(session["id"])
        self.assertIn("跳过", str(caught.exception))
        report = self.s.practice.submit(session["id"], {"acceptSkipped": True})
        self.assertEqual(report["status"], "completed_with_skips")
        summary = report["summary"]
        self.assertEqual((summary["answered"], summary["skipped"], summary["remaining"]), (0, 1, 1))
        self.assertFalse(summary["complete"])

    def test_answering_a_skipped_task_clears_it_from_the_unfinished_set(self):
        session = self.session(types=["reading"])
        self.answer(session, None, "op_skip", skipped=True)
        self.answer(session, "うけたまわる", "op_real")
        report = self.s.practice.submit(session["id"])
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["summary"]["answered"], 1)
        self.assertEqual(report["summary"]["skipped"], 0)
        self.assertTrue(report["summary"]["complete"])

    def test_the_report_counts_entries_not_tasks(self):
        session = self.s.practice.create(
            {"kind": "word", "count": 4, "packSlugs": ["words"], "types": ["reading", "meaning"]})
        # Skipping re-queues the task, so drain the queue rather than its initial length.
        for index in range(40):
            state = self.s.practice.get(session["id"])["state"]
            if state["cursor"] >= len(state["queue"]):
                break
            self.answer(session, None, f"op_e_{index}", skipped=True)
        report = self.s.practice.submit(session["id"], {"acceptSkipped": True})
        # Two directions of one entry are two tasks but one entry (§10.4).
        self.assertEqual(report["summary"]["entries"], 0)
        self.assertGreaterEqual(report["summary"]["processed"], 2)
        self.assertEqual(report["summary"]["answered"], 0)

    def test_two_directions_of_one_entry_count_as_one_entry(self):
        session = self.s.practice.create(
            {"kind": "word", "count": 4, "packSlugs": ["words"], "types": ["reading", "meaning"]})
        published = {item["id"]: item for item in session["items"]}
        for index in range(40):
            state = self.s.practice.get(session["id"])["state"]
            if state["cursor"] >= len(state["queue"]):
                break
            cursor = state["queue"][state["cursor"]]
            question = published[cursor["itemId"]]
            value = "うけたまわる" if question["mode"] == "input" else question["choices"][0]["id"]
            self.answer(session, value, f"op_two_{index}")
        report = self.s.practice.submit(session["id"], {"acceptSkipped": True})
        self.assertGreaterEqual(report["summary"]["answered"], 2)
        self.assertEqual(report["summary"]["entries"], 1)


class DraftPracticeTests(PracticeHarness, unittest.TestCase):
    """Unreviewed content is not verified practice, but it is still practice (§6.1).

    Withholding it from the accuracy is correct; withholding it from the learner turned a
    twelve-type practice module into a four-type one, which is not what the gate is for.
    """

    def setUp(self):
        # The shipped situation: a generated template marked `verified`, whose own
        # evidence records that no person read it.
        pack = make_word_pack()
        spec = {
            "type": "meaning", "mode": "choice", "variantKey": "meaning-generated",
            "prompt": "「承る」在本条中的意思是：",
            "choices": [
                {"id": "answer", "label": "恭听、接受", "rationale": "本条释义。"},
                {"id": "other-0", "label": "承担费用", "rationale": "与本条义项无关。"},
            ],
            "acceptedAnswers": ["answer"],
            "explanation": "本条取「恭听」义。",
            "reviewStatus": "verified",
            "evidence": {"method": "generated", "notHumanReview": True},
        }
        pack["entries"][0]["exerciseTemplates"] = [spec]
        self.build(prepare_pack(pack))

    def test_an_unreviewed_type_is_refused_by_default(self):
        with self.assertRaises(ValueError) as caught:
            self.session(types=["meaning"])
        self.assertIn("未审核", str(caught.exception))

    def test_the_refusal_names_the_draft_path_and_how_many_are_there(self):
        with self.assertRaises(ValueError) as caught:
            self.session(types=["meaning"])
        message = str(caught.exception)
        # A dead end with no next step is what this replaces.
        self.assertIn("包含未审核题目", message)
        self.assertIn("不计入正式正确率", message)

    def test_asking_for_drafts_builds_the_session(self):
        session = self.session(types=["meaning"], includeDrafts=True)
        self.assertEqual(len(session["items"]), 1)
        self.assertEqual(session["draftCount"], 1)
        self.assertTrue(session["items"][0]["draft"])
        self.assertIn("不计入正式正确率", session["items"][0]["draftReason"])

    def test_a_draft_answer_is_recorded_but_moves_nothing(self):
        session = self.session(types=["meaning"], includeDrafts=True)
        choice = session["items"][0]["choices"][0]["id"]
        result = self.answer(session, choice, "op_draft")["result"]
        self.assertTrue(result["draft"])
        self.assertFalse(result["srsApplied"])
        self.assertIn("不推进长期复习", result["draftNotice"])
        # Not in the accuracy, not in the mistake book, and no card was created.
        self.assertEqual(self.s.practice.stats()["totalAttempts"], 0)
        self.assertEqual(self.s.practice.stats()["draftAttempts"], 1)
        self.assertEqual(self.s.practice.mistakes(), [])
        self.assertEqual(self.store.list_vocab(), [])

    def test_the_report_counts_drafts_separately(self):
        session = self.session(types=["meaning"], includeDrafts=True)
        self.drain(session)
        report = self.s.practice.submit(session["id"], {"acceptSkipped": True})
        self.assertGreaterEqual(report["summary"]["draft"], 1)
        self.assertEqual(report["summary"]["objectiveCount"], 0)
        self.assertIsNone(report["summary"]["accuracy"])

    def test_a_reviewed_question_in_a_draft_session_still_counts(self):
        session = self.s.practice.create({
            "kind": "word", "count": 4, "packSlugs": ["words"],
            "types": ["reading", "meaning"], "includeDrafts": True})
        published = {item["id"]: item for item in session["items"]}
        reading = next(item for item in session["items"] if item["type"] == "reading")
        self.assertFalse(reading.get("draft"), "reading is reviewed content")
        self.drain(session, "op_mix")
        stats = self.s.practice.stats()
        # A wrong draft answer is retried, so the draft count is however many attempts
        # it took; what matters is that exactly one answer reached the formal figures.
        self.assertEqual(stats["totalAttempts"], 1, "only the reviewed answer counts")
        self.assertGreaterEqual(stats["draftAttempts"], 1)
        self.assertEqual(self.store.list_vocab()[0]["promptType"], "reading",
                         "only the reviewed direction produced a card")
        self.assertEqual(len(self.store.list_vocab()), 1)

    def test_a_withdrawn_question_is_not_a_draft_and_stays_out(self):
        session = self.session(types=["meaning"], includeDrafts=True)
        record = self.s.practice.feedback(
            session["id"], {"itemId": session["items"][0]["id"], "message": "答案错了"})
        self.s.practice.resolve_feedback(record["id"], {"resolution": "confirmed", "resolvedBy": "审核人"})
        with self.assertRaises(ValueError) as caught:
            self.session(types=["meaning"], includeDrafts=True)
        # Withdrawn means wrong, not merely unreviewed: no opt-in reaches it.
        self.assertIn("review.withdrawn", str(caught.exception))


class FeedbackTriageTests(PracticeHarness, unittest.TestCase):
    def setUp(self):
        self.build(reviewed_choice_pack())

    """LEX-15: a reported problem gets a recorded decision, and a withdrawal is honoured."""

    def report_problem(self, session, message="答案不对"):
        item = session["items"][0]["id"]
        return self.s.practice.feedback(session["id"], {"itemId": item, "message": message})

    def test_a_report_records_what_identifies_the_question(self):
        session = self.session(types=["reading"])
        record = self.report_problem(session)
        stored = self.s.practice.feedback_items()[0]
        self.assertEqual(stored["status"], "open")
        # Entry plus type alone cannot tell two questions or two answer versions apart.
        self.assertTrue(stored["sourceRef"].startswith("lex:"))
        self.assertEqual(stored["exerciseType"], "reading")
        self.assertTrue(stored["answerVersion"])
        self.assertEqual(stored["questionId"], record["id"] and stored["questionId"])

    def test_a_decision_needs_a_verdict_and_a_person(self):
        session = self.session(types=["reading"])
        record = self.report_problem(session)
        for bad in ({"resolution": "maybe", "resolvedBy": "我"}, {"resolution": "confirmed"}):
            with self.assertRaises(ValueError):
                self.s.practice.resolve_feedback(record["id"], bad)

    def test_rejecting_a_report_closes_it_without_withdrawing_anything(self):
        session = self.session(types=["reading"])
        record = self.report_problem(session)
        outcome = self.s.practice.resolve_feedback(
            record["id"], {"resolution": "rejected", "resolvedBy": "审核人", "note": "题目没有问题"})
        self.assertEqual(outcome["status"], "resolved")
        self.assertNotIn("withdrawn", outcome)
        self.assertEqual(self.s.practice.withdrawn_questions(), set())
        stored = self.s.practice.feedback_items()[0]
        self.assertEqual((stored["resolution"], stored["resolvedBy"]), ("rejected", "审核人"))
        self.assertTrue(stored["resolvedAt"])

    def test_confirming_a_report_withdraws_the_question_from_new_sessions(self):
        session = self.session(types=["reading"])
        record = self.report_problem(session)
        self.s.practice.resolve_feedback(
            record["id"], {"resolution": "confirmed", "resolvedBy": "审核人", "note": "读音错了"})
        self.assertIn(session["items"][0]["id"], self.s.practice.withdrawn_questions())
        with self.assertRaises(ValueError) as caught:
            self.session(types=["reading"])
        self.assertIn("withdrawn", str(caught.exception))

    def test_an_active_session_is_told_rather_than_blocked(self):
        session = self.session(types=["reading"])
        record = self.report_problem(session)
        self.s.practice.resolve_feedback(record["id"], {"resolution": "confirmed", "resolvedBy": "审核人"})
        live = self.s.practice.get(session["id"])
        self.assertTrue(live["items"][0]["unavailable"])
        self.assertIn("跳过", live["items"][0]["unavailableReason"])
        self.assertEqual(live["withdrawnItems"], [session["items"][0]["id"]])

    def test_a_withdrawn_answer_stays_in_history_but_stops_counting(self):
        session = self.session(types=["reading"])
        self.answer(session, "まちがい", "op_wrong")
        self.assertEqual(self.s.practice.stats()["totalAttempts"], 1)
        self.assertEqual(len(self.s.practice.mistakes()), 1)

        record = self.report_problem(session)
        self.s.practice.resolve_feedback(record["id"], {"resolution": "confirmed", "resolvedBy": "审核人"})

        stats = self.s.practice.stats()
        self.assertEqual(stats["totalAttempts"], 0, "the accuracy no longer includes it")
        self.assertEqual(stats["withdrawnAttempts"], 1, "…but it is still counted as history")
        self.assertEqual(self.s.practice.mistakes(), [], "the mistake row was recounted away")
        rows = self.store.connection.execute(
            "SELECT validity FROM lex_attempts").fetchall()
        self.assertEqual([row[0] for row in rows], ["withdrawn"], "the row itself is kept")

    def test_a_review_the_bad_answer_drove_gets_a_proposal_not_a_replay(self):
        session = self.session(types=["reading"])
        applied = self.answer(session, "うけたまわる", "op_scored")["result"]
        self.assertTrue(applied["srsApplied"])
        before = self.store._get_vocab(applied["vocabId"])

        record = self.report_problem(session)
        outcome = self.s.practice.resolve_feedback(
            record["id"], {"resolution": "confirmed", "resolvedBy": "审核人"})

        self.assertEqual(len(outcome["corrections"]), 1)
        proposal = outcome["corrections"][0]
        self.assertEqual(proposal["vocabId"], applied["vocabId"])
        self.assertEqual(proposal["laterEvents"], 0)
        self.assertEqual(proposal["action"], "restore-previous-state")
        # Proposed, not applied: the schedule is not rewritten behind the learner.
        after = self.store._get_vocab(applied["vocabId"])
        self.assertEqual(after["srsRepetitions"], before["srsRepetitions"])
        self.assertEqual(after["nextReviewAt"], before["nextReviewAt"])
        self.assertEqual(self.s.practice.corrections()[0]["vocabId"], applied["vocabId"])
        self.assertEqual(self.s.practice.stats()["pendingCorrections"], 1)

    def test_a_card_reviewed_again_since_gets_a_compensating_proposal(self):
        session = self.session(types=["reading"])
        applied = self.answer(session, "うけたまわる", "op_scored")["result"]
        self.store.grade_vocab_review(applied["vocabId"], "good", "op_later")

        record = self.report_problem(session)
        outcome = self.s.practice.resolve_feedback(
            record["id"], {"resolution": "confirmed", "resolvedBy": "审核人"})
        proposal = outcome["corrections"][0]
        self.assertGreaterEqual(proposal["laterEvents"], 1)
        # Rolling back would discard the review done since, so a compensating entry is
        # the only honest option (§10.3).
        self.assertEqual(proposal["action"], "record-compensating-event")


if __name__ == "__main__":
    unittest.main()


class ResumeSkippedRegressionTests(PracticeHarness, unittest.TestCase):
    def setUp(self):self.build(make_word_pack())

    def test_resume_allocates_a_new_round_and_keeps_one_long_term_review(self):
        session=self.session(types=['reading'])
        for i in range(3):self.answer(session,None,'skip_'+str(i),skipped=True)
        state=self.s.practice.get(session['id'])['state'];item=state['skipped'][0]
        resumed=self.s.practice.resume_skipped(session['id'],{'itemIds':[item]})
        self.assertEqual(resumed['state']['queue'][-1],{'itemId':item,'round':3})
        repeated=self.s.practice.resume_skipped(session['id'],{'itemIds':[item]})
        self.assertEqual(repeated['version'],resumed['version'])
        question=self.s.practice.get(session['id'],offline=True)['items'][0]
        receipt=self.answer(session,question['acceptedAnswers'][0],'real_answer')
        self.assertTrue(receipt['result']['srsApplied'])
        report=self.s.practice.submit(session['id'])
        self.assertEqual(report['summary']['answered'],1)
        self.assertEqual(report['summary']['skipped'],0)
        self.assertEqual(report['summary']['accuracy'],100)
        self.assertEqual(self.s.practice.stats()['totalAttempts'],1)
        self.assertEqual(len(self.store.list_vocab()),1)
