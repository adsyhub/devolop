"""FND-001b: the alias builder must never invent a mapping.

Migrating progress onto the wrong segment is worse than not migrating it: the
learner sees confident, wrong state rather than an obvious gap.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from content_candidate import (
    build_segment_aliases,
    coverage,
    field_coverage,
    normalize_text,
    segment_view,
    time_iou,
)


def make(index: int, start: float, end: float, text: str, **extra) -> dict:
    return segment_view(
        {"id": f"s_{index:04d}", "startTime": start, "endTime": end, "sourceText": text, **extra}, index
    )


class NormalizationTests(unittest.TestCase):
    def test_punctuation_and_width_differences_fold_together(self) -> None:
        self.assertEqual(normalize_text("これは、テストです。"), normalize_text("これはテストです"))
        self.assertEqual(normalize_text("ＡＢＣ"), normalize_text("abc"))

    def test_genuinely_different_text_stays_different(self) -> None:
        self.assertNotEqual(normalize_text("これはテストです"), normalize_text("あれは本です"))


class TimeIouTests(unittest.TestCase):
    def test_identical_spans_score_one(self) -> None:
        self.assertEqual(time_iou(make(0, 0, 2, "a"), make(1, 0, 2, "a")), 1.0)

    def test_disjoint_spans_score_zero(self) -> None:
        self.assertEqual(time_iou(make(0, 0, 2, "a"), make(1, 5, 7, "a")), 0.0)


class AliasBuildingTests(unittest.TestCase):
    def test_identical_segments_match_exactly(self) -> None:
        current = [make(0, 0, 2, "これはテストです"), make(1, 2, 4, "音声は短いです")]
        candidate = [make(0, 0, 2, "これはテストです"), make(1, 2, 4, "音声は短いです")]
        aliases = build_segment_aliases(current, candidate)
        self.assertEqual(len(aliases["exact"]), 2)
        self.assertEqual(aliases["suggested"], [])
        self.assertEqual(aliases["unmatched"], [])

    def test_cosmetic_punctuation_change_still_matches_exactly(self) -> None:
        current = [make(0, 0, 2, "これは、テストです。")]
        candidate = [make(0, 0, 2, "これはテストです")]
        aliases = build_segment_aliases(current, candidate)
        self.assertEqual(len(aliases["exact"]), 1)

    def test_slight_timing_drift_becomes_a_suggestion_needing_confirmation(self) -> None:
        current = [make(0, 0.00, 2.00, "これはテストです")]
        candidate = [make(0, 0.05, 2.05, "これはテストです")]
        aliases = build_segment_aliases(current, candidate)
        self.assertEqual(aliases["exact"], [])
        self.assertEqual(len(aliases["suggested"]), 1)
        self.assertTrue(aliases["suggested"][0]["requiresHumanConfirmation"])

    def test_several_plausible_partners_go_to_the_human_queue(self) -> None:
        """Two near-identical repeats must not be resolved by score."""
        current = [make(0, 0.0, 2.0, "はいそうです")]
        candidate = [make(0, 0.05, 2.0, "はいそうです"), make(1, 0.1, 2.05, "はいそうです")]
        aliases = build_segment_aliases(current, candidate)
        self.assertEqual(aliases["suggested"], [])
        self.assertEqual(len(aliases["ambiguous"]), 1)
        self.assertGreaterEqual(len(aliases["ambiguous"][0]["candidates"]), 2)

    def test_a_segment_with_no_partner_is_reported_unmatched_not_guessed(self) -> None:
        current = [make(0, 0, 2, "これはテストです"), make(1, 10, 12, "この文は候補にありません")]
        candidate = [make(0, 0, 2, "これはテストです")]
        aliases = build_segment_aliases(current, candidate)
        self.assertEqual(len(aliases["exact"]), 1)
        self.assertEqual(len(aliases["unmatched"]), 1)
        self.assertEqual(aliases["unmatched"][0]["fromId"], "s_0001")

    def test_candidate_only_segments_are_reported(self) -> None:
        current = [make(0, 0, 2, "これはテストです")]
        candidate = [make(0, 0, 2, "これはテストです"), make(1, 10, 12, "新しい文です")]
        aliases = build_segment_aliases(current, candidate)
        self.assertEqual(len(aliases["candidateOnly"]), 1)

    def test_one_candidate_segment_is_never_claimed_twice(self) -> None:
        current = [make(0, 0.0, 2.0, "はいそうです"), make(1, 0.02, 2.02, "はいそうです")]
        candidate = [make(0, 0.0, 2.0, "はいそうです")]
        aliases = build_segment_aliases(current, candidate)
        claimed = [entry["toId"] for entry in aliases["exact"] + aliases["suggested"]]
        self.assertEqual(len(claimed), len(set(claimed)))


class CoverageTests(unittest.TestCase):
    def test_gaps_longer_than_a_second_are_reported_as_holes(self) -> None:
        segments = [make(0, 0, 2, "a"), make(1, 5, 7, "b")]
        result = coverage(segments)
        self.assertEqual(result["coveredMs"], 4000)
        self.assertEqual(len(result["holes"]), 1)
        self.assertEqual(result["holes"][0]["gapMs"], 3000)

    def test_overlapping_segments_are_not_double_counted(self) -> None:
        segments = [make(0, 0, 3, "a"), make(1, 2, 5, "b")]
        self.assertEqual(coverage(segments)["coveredMs"], 5000)


class FieldCoverageTests(unittest.TestCase):
    def test_missing_confidence_is_counted_separately_from_low_confidence(self) -> None:
        segments = [
            make(0, 0, 2, "a"),  # no confidence at all
            make(1, 2, 4, "b", confidence=0.9),
            make(2, 4, 6, "c", confidence=0.2),
        ]
        result = field_coverage(segments)
        self.assertEqual(result["confidenceMissing"], 1)
        self.assertEqual(result["confidencePresent"], 2)
        self.assertEqual(result["confidenceLow"], 1)


if __name__ == "__main__":
    unittest.main()
