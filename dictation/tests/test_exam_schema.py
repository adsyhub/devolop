"""Schema, audit and scoring rules for the JLPT question bank.

The audit is the gate that decides whether an exam is served at all, so these
tests are mostly about what it must *refuse*. A question bank that silently
serves a wrong answer key is worse than one that refuses to load: the learner
memorises the wrong answer and has no way to notice.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from exam_fixtures import make_exam, scorable  # noqa: E402
from exam_schema import (  # noqa: E402
    answer_sheet_label,
    audit_exam,
    content_revision,
    iter_questions,
    prepare_exam,
    question_index,
    score_answers,
)


def codes(report):
    return {issue["code"] for issue in report["issues"]}


class PrepareExamTests(unittest.TestCase):
    def test_a_clean_exam_passes_its_audit(self):
        report = audit_exam(make_exam())
        self.assertEqual(report["status"], "passed", report["issues"])
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(report["summary"]["warnings"], 0)

    def test_ids_are_deterministic_across_runs(self):
        first = make_exam()
        second = make_exam()
        self.assertEqual(
            [question["id"] for _, _, question in iter_questions(first)],
            [question["id"] for _, _, question in iter_questions(second)],
        )
        self.assertEqual(first["examId"], second["examId"])

    def test_existing_ids_survive_a_reprepare(self):
        """Fixing a typo must not orphan the learner's history for every other item."""
        exam = make_exam()
        before = [question["id"] for _, _, question in iter_questions(exam)]
        exam["sections"][0]["parts"][0]["questions"][0]["prompt"] = "<u>勇敢</u>に戦った。"
        after = [question["id"] for _, _, question in iter_questions(prepare_exam(exam))]
        self.assertEqual(before, after)

    def test_content_revision_tracks_answers_not_just_text(self):
        exam = make_exam()
        changed = copy.deepcopy(exam)
        changed["sections"][0]["parts"][0]["questions"][0]["answer"] = 2
        self.assertNotEqual(content_revision(exam), content_revision(changed))

    def test_sequence_and_totals_are_derived(self):
        exam = make_exam()
        self.assertEqual(exam["questionCount"], 8)
        self.assertEqual([q["sequence"] for _, _, q in iter_questions(exam)], list(range(1, 9)))
        self.assertEqual(exam["totalPoints"], 11.0)
        self.assertEqual(exam["answeredKeyCount"], 7)

    def test_listening_labels_do_not_collide_with_written_numbers(self):
        exam = make_exam()
        labels = [question["answerSheetLabel"] for _, _, question in iter_questions(exam)]
        self.assertEqual(len(labels), len(set(labels)), f"duplicate answer-sheet labels: {labels}")
        self.assertIn("1-1", labels)  # 聴解 問題1 1番
        self.assertIn("4-1", labels)  # 聴解 問題4 1番, which would otherwise also be "1"

    def test_answer_sheet_label_falls_back_to_the_printed_label(self):
        section = {"kind": "listening"}
        part = {"number": 5}
        self.assertEqual(answer_sheet_label(section, part, {"number": None, "label": "例"}), "例")

    def test_duplicate_question_ids_are_rejected_outright(self):
        exam = make_exam()
        first = exam["sections"][0]["parts"][0]["questions"][0]
        exam["sections"][0]["parts"][0]["questions"][1]["id"] = first["id"]
        with self.assertRaises(ValueError):
            prepare_exam(exam)


class AuditTests(unittest.TestCase):
    def test_a_missing_answer_is_an_error(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][0]["answer"] = None
        self.assertIn("question.answer_missing", codes(audit_exam(exam)))

    def test_an_answer_outside_the_choice_range_is_an_error(self):
        exam = make_exam()
        # 聴解 問題4 offers three choices; "4" is a real transcription slip, not a
        # hypothetical one, and it would mark every learner wrong.
        listening = exam["sections"][2]["parts"][1]["questions"][0]
        listening["answer"] = 4
        report = audit_exam(exam)
        self.assertIn("question.answer_out_of_range", codes(report))

    def test_three_choice_listening_items_are_accepted(self):
        exam = make_exam()
        listening = exam["sections"][2]["parts"][1]["questions"][0]
        self.assertEqual(listening["choiceCount"], 3)
        self.assertEqual(audit_exam(exam)["summary"]["errors"], 0)

    def test_a_written_question_with_three_printed_choices_is_an_error(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][0]["choices"].pop()
        self.assertIn("question.choice_count", codes(audit_exam(exam)))

    def test_a_hole_in_the_written_numbering_is_an_error(self):
        """A missing number between the first and last is a page that never arrived."""
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][1]["number"] = 9
        report = audit_exam(exam)
        self.assertIn("exam.numbering_gap", codes(report))
        self.assertEqual(report["summary"]["errors"], 1, report["issues"])

    def test_numbering_that_starts_above_one_is_only_a_warning(self):
        """Importing a single 問題 is legitimate; it just is not the whole paper."""
        exam = make_exam()
        for offset, question in enumerate(scorable(exam)):
            if question.get("number") is not None:
                question["number"] = question["number"] + 30
        report = audit_exam(exam)
        self.assertIn("exam.numbering_partial", codes(report))
        self.assertEqual(report["summary"]["errors"], 0, report["issues"])

    def test_a_kanji_reading_question_must_underline_its_word(self):
        """A stripped watermark can take the printed rule with it, and then the
        four readings refer to a word the learner cannot identify."""
        exam = make_exam()
        question = exam["sections"][0]["parts"][0]["questions"][0]
        question["prompt"] = question["prompt"].replace("<u>", "").replace("</u>", "")
        self.assertIn("question.underline_missing", codes(audit_exam(exam)))

    def test_other_part_kinds_are_not_required_to_underline_anything(self):
        exam = make_exam()
        self.assertNotIn("question.underline_missing", codes(audit_exam(exam)))
        reading = exam["sections"][1]["parts"][0]["questions"][0]
        self.assertNotIn("<u>", reading["prompt"])

    def test_a_dispute_note_is_checked_like_any_other_displayed_text(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][0]["keyNote"] = "怪しい<script>alert(1)</script>"
        self.assertIn("question.stray_markup", codes(audit_exam(exam)))

    def test_a_dispute_note_changes_the_content_revision(self):
        """The service worker must not keep serving a cached exam without the note."""
        exam = make_exam()
        before = content_revision(exam)
        exam["sections"][0]["parts"][0]["questions"][0]["keyNote"] = "答案存疑"
        self.assertNotEqual(before, content_revision(exam))

    def test_a_duplicate_written_number_is_an_error(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][1]["number"] = 1
        self.assertIn("question.number_duplicate", codes(audit_exam(exam)))

    def test_unbalanced_underline_markup_is_an_error(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][0]["prompt"] = "<u>勇敢に戦う。"
        self.assertIn("question.underline_unbalanced", codes(audit_exam(exam)))

    def test_a_stray_html_tag_never_reaches_the_renderer(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][0]["prompt"] = "危ない<script>alert(1)</script>"
        self.assertIn("question.stray_markup", codes(audit_exam(exam)))

    def test_an_illegible_glyph_is_a_warning_not_an_error(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][0]["prompt"] = "<u>読めない〓字</u>"
        report = audit_exam(exam)
        self.assertIn("question.illegible_glyph", codes(report))
        self.assertEqual(report["summary"]["errors"], 0)

    def test_a_sentence_composition_item_needs_a_full_ordering(self):
        exam = make_exam()
        exam["sections"][0]["parts"][1]["questions"][0]["answerOrder"] = [1, 2, 3]
        self.assertIn("question.order_invalid", codes(audit_exam(exam)))

    def test_an_ordering_that_contradicts_the_answer_is_flagged(self):
        """★ defaults to the third blank, so order[2] and the answer must agree."""
        exam = make_exam()
        exam["sections"][0]["parts"][1]["questions"][0]["answerOrder"] = [3, 2, 1, 4]
        report = audit_exam(exam)
        self.assertIn("question.order_answer_mismatch", codes(report))

    def test_a_paper_may_star_a_blank_other_than_the_third(self):
        """2024年7月 N2 問題8 stars the second blank; that must not read as a mismatch."""
        exam = make_exam()
        question = exam["sections"][0]["parts"][1]["questions"][0]
        question["answerOrder"] = [3, 2, 1, 4]
        question["answerStar"] = 2
        question["answer"] = 2
        report = audit_exam(exam)
        self.assertNotIn("question.order_answer_mismatch", codes(report))
        self.assertNotIn("question.order_star_invalid", codes(report))

    def test_a_star_outside_the_printed_blanks_is_an_error(self):
        exam = make_exam()
        question = exam["sections"][0]["parts"][1]["questions"][0]
        question["answerStar"] = 5
        self.assertIn("question.order_star_invalid", codes(audit_exam(exam)))

    def test_a_question_pointing_at_a_missing_passage_is_an_error(self):
        exam = make_exam()
        exam["sections"][1]["parts"][0]["questions"][0]["passageIds"] = ["p_deadbeefdeadbeefdeadbeef"]
        self.assertIn("question.passage_missing", codes(audit_exam(exam)))

    def test_a_reading_question_linked_to_nothing_is_flagged(self):
        exam = make_exam()
        exam["sections"][1]["parts"][0]["questions"][0]["passageIds"] = []
        self.assertIn("question.passage_unlinked", codes(audit_exam(exam)))

    def test_a_part_kind_from_the_wrong_section_is_an_error(self):
        exam = make_exam()
        exam["sections"][0]["parts"][0]["kind"] = "short-passage"
        self.assertIn("part.kind_section_mismatch", codes(audit_exam(exam)))

    def test_printed_choices_contradicting_choicesSpoken_is_an_error(self):
        exam = make_exam()
        question = exam["sections"][2]["parts"][1]["questions"][0]
        question["choices"] = ["ア", "イ", "ウ"]
        self.assertIn("question.spoken_choices_present", codes(audit_exam(exam)))

    def test_a_scored_example_is_an_error(self):
        exam = make_exam()
        exam["sections"][2]["parts"][0]["questions"][0]["points"] = 1.0
        self.assertIn("question.example_scored", codes(audit_exam(exam)))

    def test_question_count_must_match_reality(self):
        exam = make_exam()
        exam["questionCount"] = 99
        self.assertIn("exam.question_count_mismatch", codes(audit_exam(exam)))


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.exam = make_exam()
        self.questions = scorable(self.exam)

    def test_a_perfect_sheet_earns_every_point(self):
        answers = {question["id"]: question["answer"] for question in self.questions}
        totals = score_answers(self.exam, answers)["totals"]
        self.assertEqual(totals["earned"], self.exam["totalPoints"])
        self.assertEqual(totals["percent"], 100.0)
        self.assertEqual(totals["unanswered"], 0)

    def test_an_empty_sheet_earns_nothing_and_is_all_unanswered(self):
        totals = score_answers(self.exam, {})["totals"]
        self.assertEqual(totals["earned"], 0.0)
        self.assertEqual(totals["wrong"], 0)
        self.assertEqual(totals["unanswered"], len(self.questions))

    def test_unanswered_is_reported_apart_from_wrong(self):
        """"Ran out of time" and "got it wrong" are different facts about a sitting."""
        first, second = self.questions[0], self.questions[1]
        answers = {first["id"]: (first["answer"] % 4) + 1}
        totals = score_answers(self.exam, answers)["totals"]
        self.assertEqual(totals["wrong"], 1)
        self.assertEqual(totals["unanswered"], len(self.questions) - 1)
        self.assertNotIn(second["id"], answers)

    def test_the_worked_example_is_never_scored(self):
        example = next(q for q in self.exam["sections"][2]["parts"][0]["questions"] if q["example"])
        report = score_answers(self.exam, {example["id"]: 1})
        self.assertNotIn(example["id"], {row["id"] for row in report["questions"]})
        self.assertEqual(report["totals"]["questions"], len(self.questions))

    def test_points_follow_the_paper_not_the_question_count(self):
        report = score_answers(self.exam, {})
        by_id = {row["id"]: row for row in report["parts"]}
        self.assertEqual(by_id["s1-m1"]["points"], 2.0)   # 2 questions x 1 point
        self.assertEqual(by_id["s1-m6"]["points"], 2.0)   # 1 question  x 2 points
        self.assertEqual(by_id["s2-m9"]["points"], 4.0)   # 2 questions x 2 points

    def test_sections_are_scored_separately(self):
        answers = {question["id"]: question["answer"] for question in self.questions}
        report = score_answers(self.exam, answers)
        by_id = {row["id"]: row for row in report["sections"]}
        self.assertEqual(by_id["s1"]["earned"], 4.0)
        self.assertEqual(by_id["s2"]["earned"], 4.0)
        self.assertEqual(by_id["s3"]["earned"], 3.0)

    def test_an_out_of_range_choice_is_treated_as_unanswered(self):
        question = self.questions[0]
        totals = score_answers(self.exam, {question["id"]: 99})["totals"]
        self.assertEqual(totals["wrong"], 0)
        self.assertEqual(totals["unanswered"], len(self.questions))

    def test_the_scoring_caveat_travels_with_the_score(self):
        report = score_answers(self.exam, {})
        self.assertEqual(report["scoringNote"], "仅供参考")

    def test_question_index_covers_every_question(self):
        index = question_index(self.exam)
        self.assertEqual(len(index), self.exam["questionCount"])


class ExamQualificationTests(unittest.TestCase):
    def test_clean_exam_is_qualified(self):
        from exam_store import check_exam_qualification
        exam = make_exam()
        qualified, reasons = check_exam_qualification(exam)
        self.assertTrue(qualified)
        self.assertEqual(reasons, [])

    def test_exam_with_missing_answers_is_not_qualified(self):
        from exam_store import check_exam_qualification
        exam = make_exam()
        exam["sections"][0]["parts"][0]["questions"][0]["answer"] = None
        qualified, reasons = check_exam_qualification(exam)
        self.assertFalse(qualified)
        self.assertTrue(any("answer_missing" in r for r in reasons))

    def test_exam_with_no_questions_is_not_qualified(self):
        from exam_store import check_exam_qualification
        exam = make_exam()
        exam["sections"] = []
        qualified, reasons = check_exam_qualification(exam)
        self.assertFalse(qualified)


if __name__ == "__main__":
    unittest.main()

