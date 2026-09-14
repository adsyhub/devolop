"""Regression tests for the book-specific N2 reconciliation pass."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location(
    "repair_n2_grammar_pages", ROOT / "scripts" / "repair_n2_grammar_pages.py"
)
assert SPEC and SPEC.loader
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


class BoxRecoveryTests(unittest.TestCase):
    def test_every_ledger_entry_has_a_reviewed_connection_transcription(self) -> None:
        ledger = [headword for titles in repair.HEADWORDS.values() for headword in titles]
        self.assertEqual(set(ledger), set(repair.REVIEWED_CONNECTIONS))
        for headword in ledger:
            self.assertTrue(repair.REVIEWED_CONNECTIONS[headword], headword)
            for token in repair.REVIEWED_CONNECTIONS[headword]:
                repair.parse_connection_line(token)

    def test_equal_counts_bind_the_independent_box_channel(self) -> None:
        paired = repair.pair_box_groups(
            ["病気がち", "忘れっぽい"],
            "> Nがち\n> Vますがち\n\n> Nっぽい\n> Vまっぽい／Aっぽい",
        )
        self.assertEqual(paired[0]["connectionRaw"], ["Nがち", "Vますがち"])

        entry = repair.build_entry(
            18,
            2,
            "テストがち",
            ["私は病気がちだった。"],
            paired[0],
        )
        self.assertEqual(entry["connectionRaw"], ["Nがち", "Vますがち"])
        self.assertEqual(entry["connectionSource"], "box")
        self.assertNotIn("repair.connection_inferred", [flag["code"] for flag in entry.get("flags", [])])

    def test_single_entry_page_merges_split_frame_fragments(self) -> None:
        paired = repair.pair_box_groups(
            ["仕事の話は抜きにして"],
            "> Nは\n> N(を)\n\n> N(を)\n> Vれない",
        )
        self.assertEqual(paired[0]["connectionRaw"], ["Nは", "N(を)", "Vれない"])

    def test_count_mismatch_never_shifts_frames_by_position(self) -> None:
        paired = repair.pair_box_groups(
            ["帰れるものなら", "暑いものだから", "知らなかったんだもの"],
            "> Vものだから\n\n> Vもの",
        )
        self.assertEqual(paired, [None, None, None])

    def test_struck_kana_ocr_is_normalized_from_reviewed_crop(self) -> None:
        self.assertEqual(
            repair.corrected_connection_tokens(["Aあげ", "naあげ", "Vたあげ", "Vまっぽい／Aっぽい"]),
            ["Aげ", "naげ", "Vたげ", "Vますっぽい／Aっぽい"],
        )


if __name__ == "__main__":
    unittest.main()
