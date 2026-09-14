"""Generating a question is not reviewing it (LEX-04).

The shipped packs carry 2,085 authored templates marked `verified` whose own evidence
records `notHumanReview: true`. These tests pin the rule that lets that state exist
without it counting as a reviewed, formally usable objective question.
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"), str(Path(__file__).parent)]

from lexicon_exercise import (  # noqa: E402
    answer_version, capabilities, qualification, questions_for,
    review_content_hash, review_state, validate_spec,
)
from lexicon_fixtures import make_word_pack  # noqa: E402
from lexicon_schema import audit_pack, prepare_pack  # noqa: E402


def choice_template(**overrides):
    spec = {
        "type": "meaning", "mode": "choice", "variantKey": "meaning-authored",
        "prompt": "「承る」在本条中的意思是：",
        "choices": [
            {"id": "a", "label": "恭听、接受", "rationale": "本条释义。"},
            {"id": "b", "label": "承担费用", "rationale": "与本条义项无关。"},
        ],
        "acceptedAnswers": ["a"],
        "explanation": "本条取「恭听」义。",
        "evidence": {"method": "generated", "notHumanReview": True},
    }
    spec.update(overrides)
    return spec


def reviewed(spec, reviewer="审核人"):
    """Attach the review record that the four-state contract actually requires."""
    spec = copy.deepcopy(spec)
    spec["reviewStatus"] = "reviewed"
    spec["review"] = {"method": "manual", "reviewer": reviewer, "reviewedAt": "2026-01-05T00:00:00+00:00",
                      "contentHash": review_content_hash(spec)}
    return spec


def auto_verified(spec, policy_id="lexicon.standard.v1", checks=None):
    """Attach the machine verification record supported by E01."""
    spec = copy.deepcopy(spec)
    spec["verification"] = {
        "status": "auto_verified",
        "policyId": policy_id,
        "contentHash": review_content_hash(spec),
        "checkRefs": ["schema.valid", "answer.deterministic"] if checks is None else checks,
        "verifiedAt": "2026-09-12T00:00:00+00:00",
    }
    return spec


def pack_with(spec):
    pack = make_word_pack()
    pack["entries"][0]["exerciseTemplates"] = [spec]
    return prepare_pack(pack)


class ContentReviewTests(unittest.TestCase):
    def test_the_legacy_verified_marker_only_ever_means_structure_checked(self):
        self.assertEqual(review_state({"reviewStatus": "verified"}), "machine_checked")
        self.assertEqual(review_state({}), "draft")
        self.assertEqual(review_state({"reviewStatus": "nonsense"}), "draft")
        qualified, codes = qualification(choice_template(reviewStatus="verified"))
        self.assertFalse(qualified)
        self.assertEqual(codes, ["review.required"])

    def test_an_unreviewed_template_is_withheld_but_still_previewable(self):
        pack = pack_with(choice_template(reviewStatus="verified"))
        entry = pack["entries"][0]
        self.assertNotIn("meaning", {q["type"] for q in questions_for(pack, entry)})
        pending = [q for q in questions_for(pack, entry, include_pending=True) if q["type"] == "meaning"]
        self.assertEqual(len(pending), 1)
        self.assertFalse(pending[0]["qualified"])

    def test_capabilities_say_which_types_are_available_and_why_not(self):
        pack = pack_with(choice_template(reviewStatus="verified"))
        result = capabilities(pack, pack["entries"][0])
        self.assertNotIn("meaning", result["types"])
        self.assertIn("meaning", result["pendingTypes"])
        self.assertEqual(result["byType"]["meaning"]["reasonCodes"], ["review.required"])
        self.assertTrue(result["byType"]["recall"]["available"])
        self.assertEqual(result["byType"]["recall"]["reasonCodes"], [])

    def test_a_real_review_record_makes_the_question_usable(self):
        pack = pack_with(reviewed(choice_template()))
        types = {q["type"] for q in questions_for(pack, pack["entries"][0])}
        self.assertIn("meaning", types)

    def test_changing_the_answer_invalidates_the_review_that_covered_it(self):
        spec = reviewed(choice_template())
        spec["acceptedAnswers"] = ["b"]
        qualified, codes = qualification(spec)
        self.assertFalse(qualified)
        self.assertEqual(codes, ["review.stale"])

    def test_a_review_without_a_named_reviewer_is_not_a_review(self):
        spec = reviewed(choice_template(), reviewer="")
        qualified, codes = qualification(spec)
        self.assertFalse(qualified)
        self.assertIn("review.reviewer_missing", codes)

    def test_the_audit_refuses_a_review_record_that_covers_other_content(self):
        spec = reviewed(choice_template())
        spec["prompt"] = "改写过的题面"
        report = audit_pack(pack_with(spec))
        self.assertIn("exercise.invalid", {issue["code"] for issue in report["issues"]})
        self.assertEqual(report["status"], "failed")

    def test_answer_version_tracks_scoring_content_and_not_the_wording(self):
        spec = choice_template()
        reworded = choice_template(prompt="换个说法问同一题：")
        self.assertEqual(answer_version(spec), answer_version(reworded))
        self.assertNotEqual(answer_version(spec), answer_version(choice_template(acceptedAnswers=["b"])))
        # The review, unlike the answer version, does cover the wording.
        self.assertNotEqual(review_content_hash(spec), review_content_hash(reworded))

    def test_a_type_cannot_borrow_an_answering_mode_it_cannot_express(self):
        with self.assertRaises(ValueError):
            validate_spec(choice_template(type="order"))
        with self.assertRaises(ValueError):
            validate_spec({**choice_template(), "mode": "self", "type": "meaning"})

    def test_a_choice_question_needs_a_wrong_option_and_distinct_labels(self):
        with self.assertRaises(ValueError):
            validate_spec(choice_template(acceptedAnswers=["a", "b"]))
        duplicated = choice_template()
        duplicated["choices"][1]["label"] = duplicated["choices"][0]["label"]
        with self.assertRaises(ValueError):
            validate_spec(duplicated)

    def test_a_multi_blank_answer_must_match_its_blank_count(self):
        spec = {"type": "cloze", "mode": "input", "variantKey": "cloze-authored",
                "prompt": "补出两个空：＿＿と＿＿", "blankCount": 2,
                "acceptedAnswers": [["一", "二"]], "explanation": "说明",
                "evidence": {"method": "generated"}}
        validate_spec(spec)
        with self.assertRaises(ValueError):
            validate_spec({**spec, "acceptedAnswers": [["一"]]})

    def test_auto_verified_valid_qualification_passes(self):
        spec = auto_verified(choice_template())
        qualified, codes = qualification(spec)
        self.assertTrue(qualified)
        self.assertEqual(codes, [])

        pack = pack_with(spec)
        types = {q["type"] for q in questions_for(pack, pack["entries"][0])}
        self.assertIn("meaning", types)

    def test_auto_verified_stale_content_hash_fails(self):
        spec = auto_verified(choice_template())
        spec["prompt"] = "改动过的题面"
        qualified, codes = qualification(spec)
        self.assertFalse(qualified)
        self.assertIn("verification.stale", codes)

    def test_auto_verified_missing_policy_id_fails(self):
        spec = auto_verified(choice_template(), policy_id="")
        qualified, codes = qualification(spec)
        self.assertFalse(qualified)
        self.assertIn("verification.policy_missing", codes)

    def test_auto_verified_missing_checks_fails(self):
        spec = auto_verified(choice_template(), checks=[])
        qualified, codes = qualification(spec)
        self.assertFalse(qualified)
        self.assertIn("verification.checks_missing", codes)

    def test_auto_verified_unsupported_type_fails(self):
        spec = auto_verified({
            "type": "usage", "mode": "choice", "variantKey": "usage-authored",
            "prompt": "使用例：＿＿",
            "choices": [{"id": "a", "label": "甲", "rationale": "甲理由"}, {"id": "b", "label": "乙", "rationale": "乙理由"}],
            "acceptedAnswers": ["a"], "explanation": "使用说明",
        })
        qualified, codes = qualification(spec)
        self.assertFalse(qualified)
        self.assertIn("verification.unsupported_type", codes)

    def test_auto_verified_hard_vetoes_are_never_bypassed(self):
        spec = auto_verified(choice_template())
        spec["reviewStatus"] = "withdrawn"
        qualified, codes = qualification(spec)
        self.assertFalse(qualified)
        self.assertIn("review.withdrawn", codes)

        spec2 = auto_verified(choice_template())
        spec2["entryStatus"] = "draft"
        qualified, codes = qualification(spec2)
        self.assertFalse(qualified)
        self.assertIn("entry.draft", codes)


if __name__ == "__main__":
    unittest.main()

