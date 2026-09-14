"""Tests for quality_issues and quality_policy modules."""

from __future__ import annotations

import unittest
from quality_issues import CheckResult, Issue, SubjectRef, issue_from_legacy_manifest_issue
from quality_policy import evaluate_course_quality, evaluate_lexicon_quality, evaluate_exam_quality


class QualityPolicyTests(unittest.TestCase):
    def test_check_result_and_issue_creation(self) -> None:
        subject = SubjectRef(kind="course_sentence", id="s-001", revision="rev1")
        check = CheckResult(
            checkId="transcript.source_alignment",
            result="pass",
            subject=subject,
            severity="blocking",
            blockedCapabilities=["dictation_scoring"],
        )
        d = check.to_dict()
        self.assertEqual(d["checkId"], "transcript.source_alignment")
        self.assertEqual(d["result"], "pass")
        self.assertEqual(d["subject"]["id"], "s-001")

    def test_issue_from_legacy_manifest_issue(self) -> None:
        subject = SubjectRef(kind="course", id="2010-12-N2", revision="revA")
        leg = {
            "severity": "error",
            "code": "sentence.timestamp_invalid",
            "message": "Bad timestamp",
            "sentenceIndex": 2,
        }
        issue = issue_from_legacy_manifest_issue(leg, subject, sentence_id="s-003")
        self.assertEqual(issue.severity, "blocking")
        self.assertEqual(issue.code, "sentence.timestamp_invalid")
        self.assertIn("dictation_scoring", issue.blockedCapabilities)
        self.assertEqual(issue.location.get("sentenceId"), "s-003")

    def test_evaluate_course_quality_clean(self) -> None:
        eval_res = evaluate_course_quality([], has_audio=True)
        self.assertEqual(eval_res["decision"], "passed")
        self.assertTrue(eval_res["capabilities"]["preview"])
        self.assertTrue(eval_res["capabilities"]["dictation_scoring"])
        self.assertTrue(eval_res["capabilities"]["full_study"])
        self.assertFalse(eval_res["capabilities"]["distribution"])

    def test_evaluate_course_quality_corrupt_enrichment(self) -> None:
        subject = SubjectRef(kind="course", id="test-c", revision="rev1")
        issue = Issue(
            id="iss1",
            code="sentence.enrichment_corrupt",
            severity="blocking",
            subject=subject,
            blockedCapabilities=["full_study"],
            message="Corrupted translation",
        )
        eval_res = evaluate_course_quality([issue], has_audio=True)
        self.assertEqual(eval_res["decision"], "rejected")
        self.assertFalse(eval_res["capabilities"]["full_study"])

    def test_evaluate_lexicon_and_exam_quality(self) -> None:
        lex_res = evaluate_lexicon_quality({"entries": [{"term": "test"}]})
        self.assertEqual(lex_res["decision"], "passed")
        self.assertTrue(lex_res["capabilities"]["full_study"])

        exam_res = evaluate_exam_quality({"questions": [{"id": "q1", "answer": "1"}]})
        self.assertEqual(exam_res["decision"], "passed")
        self.assertTrue(exam_res["capabilities"]["exam_scoring"])

        exam_no_ans = evaluate_exam_quality({"questions": [{"id": "q1"}]})
        self.assertEqual(exam_no_ans["decision"], "limited")
        self.assertFalse(exam_no_ans["capabilities"]["exam_scoring"])


if __name__ == "__main__":
    unittest.main()

