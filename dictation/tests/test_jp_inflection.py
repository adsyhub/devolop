"""Deinflection chains, romanisation and the limits around both (LEX-18, §9.3).

The rules already produced multi-step candidates, but only the last step's part of
speech survived, so a chain could continue from a completed dictionary form and invent
a base that no rule sequence actually justifies.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jp_inflection import MAX_QUERY, deinflect, normalize, roman_candidates, romanize  # noqa: E402


def bases(surface, **kwargs):
    return {candidate["text"] for candidate in deinflect(surface, **kwargs)}


def chain_for(surface, target):
    found = [c for c in deinflect(surface) if c["text"] == target]
    return min(found, key=lambda c: (len(c["chain"]), c["cost"])) if found else None


class DeinflectionTests(unittest.TestCase):
    def test_one_step_forms_reach_their_dictionary_form(self):
        cases = {
            "たべました": "たべる", "読みます": "読む", "書かない": "書く",
            "急げば": "急ぐ", "話した": "話す", "待とう": "待つ",
            "死ななかった": "死ぬ", "遊びません": "遊ぶ",
            "高くない": "高い", "勉強しました": "勉強する", "行った": "行く",
        }
        for surface, expected in cases.items():
            with self.subTest(surface):
                self.assertIn(expected, bases(surface))

    def test_multi_step_chains_are_reached_through_derived_stems(self):
        # 食べさせられる is causative-passive: two derived steps before the dictionary form.
        chain = chain_for("食べさせられる", "食べる")
        self.assertIsNotNone(chain)
        self.assertEqual(len(chain["chain"]), 2)
        self.assertIn("読む", bases("読んでいる"))
        self.assertIn("する", bases("してしまった") | bases("している"))

    def test_a_completed_dictionary_form_is_not_inflected_further(self):
        # たべました → たべる is a polite past, a finished form. Continuing from it used to
        # yield たぶ, a base no rule sequence justifies.
        self.assertNotIn("たぶ", bases("たべました"))
        self.assertNotIn("よまる", bases("読みました"))

    def test_every_step_records_its_classes_depth_and_cost(self):
        chain = chain_for("食べさせられる", "食べる")
        self.assertEqual([step["depth"] for step in chain["steps"]], [1, 2])
        self.assertEqual(chain["steps"][0]["from"], "surface")
        for step in chain["steps"]:
            self.assertTrue(step["to"])
            self.assertGreater(step["cost"], 0)
            self.assertTrue(step["ending"])
        self.assertEqual(chain["cost"], sum(step["cost"] for step in chain["steps"]))

    def test_the_shortest_chain_wins_for_one_base(self):
        for candidate in deinflect("食べさせられる"):
            same = [c for c in deinflect("食べさせられる")
                    if c["text"] == candidate["text"] and c["pos"] == candidate["pos"]]
            self.assertEqual(len(same), 1, "one chain per (form, part of speech)")

    def test_candidate_growth_is_bounded(self):
        self.assertLessEqual(len(deinflect("食べさせられていました")), 96)
        self.assertLessEqual(max(len(c["chain"]) for c in deinflect("食べさせられている")), 3)
        self.assertLessEqual(max(len(c["chain"]) for c in deinflect("読んでいる", max_depth=1)), 1)

    def test_an_over_long_query_is_refused_rather_than_expanded(self):
        with self.assertRaises(ValueError):
            deinflect("あ" * (MAX_QUERY + 1))

    def test_the_surface_form_is_always_a_candidate(self):
        self.assertIn("たべる", bases("たべる"))
        self.assertEqual(deinflect("たべる")[0]["chain"], [])


class RomanisationTests(unittest.TestCase):
    def test_geminate_consonants_are_doubled(self):
        self.assertEqual(romanize("きって"), "kitte")
        self.assertEqual(romanize("いっぱい"), "ippai")
        self.assertEqual(romanize("まっちゃ"), "matcha")

    def test_long_vowels_are_carried_through(self):
        self.assertEqual(romanize("ケーキ"), "keeki")
        self.assertEqual(romanize("コーヒー"), "koohii")

    def test_moraic_n_is_distinguished_from_the_na_row(self):
        # しんあい and しない are different words; a bare "n" collapses them.
        self.assertEqual(romanize("しんあい"), "shin'ai")
        self.assertEqual(romanize("しない"), "shinai")
        self.assertNotEqual(romanize("しんあい"), romanize("しない"))

    def test_palatalised_syllables_use_their_digraph(self):
        self.assertEqual(romanize("きょう"), "kyou")
        self.assertEqual(romanize("ぎゅうにゅう"), "gyuunyuu")
        self.assertEqual(romanize("しゃしん"), "shashin")

    def test_loanword_syllables_are_not_split_into_two_moras(self):
        self.assertEqual(romanize("ファイル"), "fairu")
        self.assertEqual(romanize("ウェブ"), "webu")
        self.assertEqual(romanize("パーティー"), "paatii")

    def test_katakana_and_hiragana_romanise_alike(self):
        self.assertEqual(romanize("トウキョウ"), romanize("とうきょう"))

    def test_typed_aliases_reach_the_stored_spelling(self):
        for typed, expected in [("sinbun", "shinbun"), ("tyotto", "chotto"),
                                ("tukue", "tsukue"), ("huton", "futon"),
                                ("zikan", "jikan"), ("syashin", "shashin")]:
            with self.subTest(typed):
                self.assertIn(expected, roman_candidates(typed))

    def test_both_moraic_n_spellings_are_offered(self):
        # An index built by an older romanizer stored the plain form; both must match.
        self.assertEqual(set(roman_candidates("senpai")), {"senpai", "sempai"})
        self.assertIn("shinai", roman_candidates("shin'ai"))

    def test_long_vowel_spellings_are_offered_both_ways(self):
        candidates = roman_candidates("toukyou")
        self.assertIn("toukyou", candidates)
        self.assertIn("tookyoo", candidates)

    def test_an_unsupported_spelling_returns_itself_and_is_not_corrected(self):
        # No guessing: an unknown string stays unknown rather than becoming another word.
        self.assertEqual(roman_candidates("qqq"), ["qqq"])

    def test_an_over_long_romaji_query_is_refused(self):
        with self.assertRaises(ValueError):
            roman_candidates("a" * 65)


class NormalisationTests(unittest.TestCase):
    def test_width_case_and_wave_dashes_are_folded(self):
        self.assertEqual(normalize("ＡＢＣ"), "abc")
        self.assertEqual(normalize("〜ている"), "ている")
        self.assertEqual(normalize("  spaced   out  "), "spaced out")

    def test_katakana_folds_to_hiragana_only_when_asked(self):
        self.assertEqual(normalize("カタカナ", reading=True), "かたかな")
        self.assertEqual(normalize("カタカナ"), "カタカナ")


if __name__ == "__main__":
    unittest.main()
