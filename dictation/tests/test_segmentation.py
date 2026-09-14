"""Unit tests for video sentence segmentation (video_segmentation.py)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from media_sources import Segment, Token
from video_segmentation import (
    DEFAULT_PARAMS,
    RESOLUTION_CUE,
    RESOLUTION_NONE,
    RESOLUTION_TOKEN,
    SegmentationError,
    SegmentationParams,
    build_char_stream,
    resegment,
    result_to_sentences,
)


class VideoSegmentationTests(unittest.TestCase):
    def test_empty_segments(self):
        res = resegment([])
        self.assertEqual(res.sentences, ())
        self.assertEqual(res.resolution, RESOLUTION_NONE)
        self.assertEqual(res.source_cues, 0)
        sents = result_to_sentences(res, "ja")
        self.assertEqual(sents, [])

    def test_invariant_char_conservation_rule_a(self):
        # Japanese text with terminal punctuation
        text = "事件は山口県美祢市で起きました。通報は28日午後6時頃。「父が血まみれで倒れている」とのことです。"
        seg = Segment(start=0.0, end=10.0, text=text)
        res = resegment([seg], language="ja")
        sents = result_to_sentences(res, "ja")
        
        # Invariant I1: reconstructed text must equal original stream
        reconstructed = "".join(s["sourceText"] for s in sents)
        self.assertEqual(reconstructed, text)
        self.assertEqual(res.resolution, RESOLUTION_CUE)
        self.assertGreaterEqual(len(sents), 3)

    def test_rule_a_closing_brackets(self):
        # Closing quote belongs to previous sentence
        text = "「はい、わかりました。」次は天気予报です。"
        seg = Segment(start=0.0, end=5.0, text=text)
        res = resegment([seg], language="ja")
        sents = result_to_sentences(res, "ja")
        self.assertEqual(len(sents), 2)
        self.assertEqual(sents[0]["sourceText"], "「はい、わかりました。」")
        self.assertEqual(sents[1]["sourceText"], "次は天気予报です。")

    def test_rule_b_pause_threshold_with_tokens(self):
        # Segments with tokens where pause >= 0.6s triggers a split without punctuation
        tokens1 = (
            Token("本日は大変", 1.0),
            Token("晴天なり", 1.5),
        )
        tokens2 = (
            Token("明日は雨模様", 4.0),  # Gap from 1.5 to 4.0 is 2.5s >= 0.6s
            Token("となるでしょう", 4.5),
        )
        seg1 = Segment(start=1.0, end=2.0, text="本日は大変晴天なり", tokens=tokens1)
        seg2 = Segment(start=4.0, end=5.5, text="明日は雨模様となるでしょう", tokens=tokens2)
        
        res = resegment([seg1, seg2], language="ja")
        sents = result_to_sentences(res, "ja")
        self.assertEqual(res.resolution, RESOLUTION_TOKEN)
        self.assertEqual(len(sents), 2)
        self.assertEqual(sents[0]["sourceText"], "本日は大変晴天なり")
        self.assertEqual(sents[1]["sourceText"], "明日は雨模様となるでしょう")

    def test_rule_c_long_span_split(self):
        # Long span without terminal punctuation > 45 chars
        long_text = "関東地方で相次ぐ強盗事件について警察庁は指示役の特定を進めていますが容疑者のスマートフォンから複数の証拠が見つかりました"
        self.assertGreater(len(long_text), 45)
        seg = Segment(start=0.0, end=15.0, text=long_text)
        res = resegment([seg], language="ja")
        sents = result_to_sentences(res, "ja")
        
        for s in sents:
            self.assertLessEqual(len(s["sourceText"]), 45)
        reconstructed = "".join(s["sourceText"] for s in sents)
        self.assertEqual(reconstructed, long_text)

    def test_rule_d_short_isolated_fragment_is_marker(self):
        # Standalone isolated digit "1"
        seg = Segment(start=0.0, end=1.0, text="1")
        res = resegment([seg], language="ja")
        sents = result_to_sentences(res, "ja")
        self.assertEqual(len(sents), 1)
        self.assertEqual(sents[0]["contentType"], "marker")
        self.assertFalse(sents[0]["practiceEligible"])

    def test_invariants_monotonic_and_timing(self):
        # Multiple segments
        segs = [
            Segment(start=0.0, end=3.0, text="第一のニュースです。"),
            Segment(start=3.5, end=6.0, text="第二のニュースです。"),
            Segment(start=6.2, end=9.0, text="第三のニュースです。"),
        ]
        res = resegment(segs, language="ja")
        sents = result_to_sentences(res, "ja")
        self.assertEqual(len(sents), 3)
        for i in range(len(sents) - 1):
            self.assertLessEqual(sents[i]["endTime"], sents[i + 1]["startTime"])
            self.assertGreaterEqual(sents[i]["endTime"] - sents[i]["startTime"], 0.35)


if __name__ == "__main__":
    unittest.main()
