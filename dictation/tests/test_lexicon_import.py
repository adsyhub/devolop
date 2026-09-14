"""The import pipeline: extraction, the 目次 ledger, and frozen identity.

These are the five traps ``lexicon_import`` exists to stop, one class each. They are
written against a synthetic OCR document in the same shape as the real one — same three
spellings of a week number, same ``> `` quoted boxes, same ``<!-- ruby: -->`` comments,
same ``naで`` mis-read — because those are the failures this book actually produced, not
hypotheses about what OCR might do.

None of the text here is copied from the textbook.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from lexicon_fixtures import make_meta  # noqa: E402
from lexicon_import import (  # noqa: E402
    ImportError_,
    assemble_pack,
    clean_line,
    extract_pages,
    load_registry,
    mark_cloze,
    normalize_number,
    parse_units_file,
    resolve_keys,
    save_registry,
    unit_id,
)
from lexicon_schema import audit_pack  # noqa: E402

# --- a synthetic OCR document ----------------------------------------------

LESSON_LEFT = """第1週 テストしゅう

1日目 ためしの日 A test day 测试日 테스트 날

〜てたまらない

これはためしてたまらない文です。(=とてもためしたい)
<!-- ruby: ぶん -->
これは ためし This is a test sentence.
これは ためし 这是一个测试句子。
이것은 테스트 문장입니다.
Aくて
naで
Vたくて

〜がち

しけんはわすれがちだ。
I tend to forget the test.
考试容易被忘记。

<!-- footer: 14 -->

<!-- box -->
> Nがち
> Vますがち
> れい ありがち
"""

LESSON_RIGHT = """〜っぽい

このコートはやすっぽい。
This coat looks cheap.
这件大衣看上去很低档。

練習Ⅰ ただしいほうに〇をつけなさい。
① これは (a. っぽい b. がち) だ。

<!-- box -->
> Nっぽい
"""

EXERCISE_PAGE = """第1週 テストしゅう

7日目 実戦問題

問題1 つぎの文の（ ）に入れるのに最もよいものを、一つえらびなさい。
"""


def document(*, week_spelling: str = "第1週") -> dict:
    left = LESSON_LEFT.replace("第1週", week_spelling, 1)
    return {
        "pages": [
            {"page": 1, "markdown": "テスト教材\n\n<!-- footer: 1 -->", "box": ""},
            {"page": 2, "markdown": left, "box": _box_of(left)},
            {"page": 3, "markdown": LESSON_RIGHT, "box": _box_of(LESSON_RIGHT)},
            {"page": 4, "markdown": EXERCISE_PAGE, "box": ""},
        ]
    }


def _box_of(markdown: str) -> str:
    marker = "<!-- box -->"
    return markdown.split(marker, 1)[1].strip() if marker in markdown else ""


def pages_of(**kwargs) -> list[dict]:
    return extract_pages(document(**kwargs))


UNITS = "第1週 1日目 ためしの日 3\n"


class NormalisationTests(unittest.TestCase):
    """Trap 1: this book's OCR spells the same week number three different ways."""

    def test_all_three_spellings_normalise_to_one_number(self):
        self.assertEqual(normalize_number("1"), 1)
        self.assertEqual(normalize_number("２"), 2)
        self.assertEqual(normalize_number("一"), 1)
        self.assertEqual(normalize_number("十二"), 12)

    def test_the_same_unit_written_three_ways_is_one_unit(self):
        ids = {
            pages_of(week_spelling=spelling)[1]["unitHeader"]["week"]
            for spelling in ("第1週", "第一週", "第２週".replace("２", "１"))
        }
        self.assertEqual(ids, {1})

    def test_an_unreadable_number_is_not_guessed(self):
        self.assertIsNone(normalize_number("？"))
        self.assertIsNone(normalize_number(""))

    def test_unit_ids_are_stable_across_spellings(self):
        self.assertEqual(unit_id(1, 4), "w1d4")


class QuotedDataTests(unittest.TestCase):
    """Trap 3: ``> `` lines and ruby comments are data, and ruby is only ever a hint."""

    def test_a_quoted_box_line_becomes_a_connection_not_a_blockquote(self):
        page = pages_of()[2]
        entry = next(block for block in page["blocks"] if block["type"] == "entry")
        self.assertEqual(entry["connectionRaw"], ["Nっぽい"])
        self.assertEqual(entry.get("connectionSource"), "box")

    def test_ruby_comments_are_stripped_from_the_text(self):
        text, hints = clean_line("これは文です。<!-- ruby: ぶん -->")
        self.assertEqual(text, "これは文です。")
        self.assertEqual(hints, ["ぶん"])

    def test_furigana_merged_into_a_translation_line_is_removed(self):
        text, hints = clean_line("わたし こ ころ I tended to get sick.")
        self.assertEqual(text, "I tended to get sick.")
        self.assertEqual(hints, ["わたし", "こ", "ころ"])

    def test_no_reading_field_is_ever_produced_by_extraction(self):
        """docs/PDF_OCR.md: at this book's furigana size the model invents readings."""
        for page in pages_of():
            for block in page["blocks"]:
                for example in block.get("examples") or []:
                    self.assertNotIn("reading", example)


class ExtractionTests(unittest.TestCase):
    def test_entries_are_split_at_their_headwords(self):
        headwords = [
            block["headword"]
            for page in pages_of()
            for block in page["blocks"]
            if block["type"] == "entry"
        ]
        self.assertEqual(headwords, ["〜てたまらない", "〜がち", "〜っぽい"])

    def test_the_unit_continues_onto_the_right_hand_page(self):
        pages = pages_of()
        self.assertEqual(pages[1]["unitHeader"], pages[2]["unitHeader"])
        self.assertIsNone(pages[2]["blocks"][0].get("week"))

    def test_translations_are_separated_by_script(self):
        entry = next(block for block in pages_of()[1]["blocks"] if block["type"] == "entry")
        example = entry["examples"][0]
        self.assertEqual(example["ja"], "これはためしてたまらない文です。")
        self.assertEqual(example["paraphrase"], "とてもためしたい")
        self.assertEqual(example["en"], "This is a test sentence.")
        self.assertEqual(example["zh"], "这是一个测试句子。")
        self.assertEqual(example["ko"], "이것은 테스트 문장입니다.")

    def test_the_day_seven_practice_test_is_not_imported(self):
        """It is a JLPT-format exercise with a key; that is the question bank's job."""
        page = pages_of()[3]
        self.assertEqual([block["type"] for block in page["blocks"]], ["exercise"])

    def test_the_practice_section_of_a_lesson_page_is_dropped(self):
        page = pages_of()[2]
        text = json.dumps(page, ensure_ascii=False)
        self.assertNotIn("練習", text)
        self.assertNotIn("a. っぽい", text)

    def test_front_matter_before_the_first_unit_carries_no_entries(self):
        page = pages_of()[0]
        self.assertEqual([block["type"] for block in page["blocks"]], ["front-matter"])

    def test_a_page_whose_day_line_was_lost_is_not_filed_under_the_previous_unit(self):
        """Silently inheriting the last unit files entries under the wrong lesson."""
        doc = document()
        doc["pages"].append(
            {"page": 5, "markdown": "第2週 つぎのしゅう\n\n〜わけだ\n\nこれはわけだ文です。\n", "box": ""}
        )
        page = extract_pages(doc)[-1]
        self.assertIsNone(page["unitHeader"])
        self.assertEqual(page["blocks"], [])
        self.assertEqual(
            [issue["code"] for issue in page["issues"]], ["extract.unit_header_missing"]
        )

    def test_a_missing_connection_is_an_error_on_the_page(self):
        doc = document()
        doc["pages"][1]["box"] = ""
        doc["pages"][1]["markdown"] = doc["pages"][1]["markdown"].replace("Aくて\nnaで\nVたくて\n", "")
        page = extract_pages(doc)[1]
        codes = {issue["code"] for issue in page["issues"]}
        self.assertIn("extract.connection_missing", codes)
        self.assertTrue(any(issue["severity"] == "error" for issue in page["issues"]))

    def test_word_draft_does_not_require_a_grammar_connection_table(self):
        doc = document()
        doc["pages"][1]["box"] = ""
        doc["pages"][1]["markdown"] = doc["pages"][1]["markdown"].replace(
            "Aくて\nnaで\nVたくて\n", ""
        )
        page = extract_pages(doc, kind="word")[1]
        codes = {issue["code"] for issue in page["issues"]}
        self.assertNotIn("extract.connection_missing", codes)


class LedgerTests(unittest.TestCase):
    """Trap 2: the count from the printed 目次 is the only independent check there is."""

    def test_units_file_parses_week_day_title_and_count(self):
        units = parse_units_file("# comment\n第1週 1日目 ためしの日 3\n第１週 ２日目 つぎの日 4\n")
        self.assertEqual([unit["unitId"] for unit in units], ["w1d1", "w1d2"])
        self.assertEqual([unit["expectedEntries"] for unit in units], [3, 4])
        self.assertEqual(units[0]["title"], "ためしの日")

    def test_a_malformed_ledger_line_stops_the_run(self):
        with self.assertRaises(ImportError_):
            parse_units_file("第1週 1日目 ためしの日\n")

    def test_an_uncounted_unit_is_named_rather_than_treated_as_zero(self):
        """`?` must not degrade into a number: the check would then verify itself."""
        with self.assertRaises(ImportError_) as caught:
            parse_units_file("第1週 1日目 ためしの日 ?\n第1週 2日目 つぎの日 3\n")
        self.assertIn("no entry count", str(caught.exception))
        self.assertIn("[1]", str(caught.exception))

    def test_a_duplicated_unit_stops_the_run(self):
        with self.assertRaises(ImportError_):
            parse_units_file("第1週 1日目 a 3\n第1週 1日目 b 3\n")

    def test_a_count_mismatch_is_reported_per_unit_and_fails(self):
        units = parse_units_file("第1週 1日目 ためしの日 4\n")
        registry = {"schemaVersion": 1, "packId": make_meta()["packId"], "nextKey": 1, "entries": []}
        _pack, report = assemble_pack(pages_of(), units, registry, make_meta(), accept_new_keys=True)
        self.assertFalse(report["ok"])
        self.assertEqual(report["mismatched"][0]["expected"], 4)
        self.assertEqual(report["mismatched"][0]["found"], 3)

    def test_a_matching_ledger_assembles_cleanly(self):
        units = parse_units_file(UNITS)
        registry = {"schemaVersion": 1, "packId": make_meta()["packId"], "nextKey": 1, "entries": []}
        pack, report = assemble_pack(pages_of(), units, registry, make_meta(), accept_new_keys=True)
        self.assertTrue(report["ok"], report)
        self.assertEqual(pack["entryCount"], 3)
        self.assertEqual(audit_pack(pack)["summary"]["errors"], 0, audit_pack(pack)["issues"])

    def test_an_entry_on_a_page_with_errors_never_reaches_the_pack(self):
        pages = pages_of()
        pages[1]["issues"].append({"severity": "error", "code": "extract.manual", "message": "unsure"})
        units = parse_units_file("第1週 1日目 ためしの日 1\n")
        registry = {"schemaVersion": 1, "packId": make_meta()["packId"], "nextKey": 1, "entries": []}
        pack, report = assemble_pack(pages, units, registry, make_meta(), accept_new_keys=True)
        self.assertEqual(pack["entryCount"], 1)
        self.assertEqual(report["blockedEntries"], 2)
        self.assertFalse(report["ok"])


class ConnectionMappingTests(unittest.TestCase):
    """Trap 4: the abbreviations are a notation, and this book's OCR mangles them."""

    def _assemble(self, pages):
        units = parse_units_file(UNITS)
        registry = {"schemaVersion": 1, "packId": make_meta()["packId"], "nextKey": 1, "entries": []}
        return assemble_pack(pages, units, registry, make_meta(), accept_new_keys=True)

    def test_abbreviations_become_structured_slots(self):
        pack, _report = self._assemble(pages_of())
        connection = pack["entries"][0]["grammar"]["connection"]
        self.assertEqual(
            [(item["slot"], item["display"]) for item in connection],
            [("i-adjective", "イAくて"), ("na-adjective", "ナAで"), ("verb-desiderative", "Vたくて")],
        )

    def test_the_ocr_confusion_stops_the_assembly(self):
        pages = pages_of()
        entry = next(block for block in pages[1]["blocks"] if block["type"] == "entry")
        entry["connectionRaw"] = ["なで"]
        with self.assertRaises(ImportError_) as caught:
            self._assemble(pages)
        self.assertIn("naで", str(caught.exception))


class IdentityTests(unittest.TestCase):
    """The registry is what keeps a re-extraction from re-issuing everyone's cards."""

    def test_a_new_anchor_is_refused_without_the_explicit_flag(self):
        registry = {"schemaVersion": 1, "packId": "p", "nextKey": 1, "entries": []}
        _known, unknown = resolve_keys(registry, ["pdf:2:block:2"], accept_new=False)
        self.assertEqual(unknown, ["pdf:2:block:2"])
        self.assertEqual(registry["entries"], [])

    def test_accepting_new_keys_assigns_them_monotonically(self):
        registry = {"schemaVersion": 1, "packId": "p", "nextKey": 1, "entries": []}
        known, unknown = resolve_keys(registry, ["pdf:2:block:2", "pdf:2:block:5"], accept_new=True)
        self.assertEqual(unknown, [])
        self.assertEqual(sorted(known.values()), ["e0001", "e0002"])
        self.assertEqual(registry["nextKey"], 3)

    def test_a_known_anchor_keeps_its_key_on_a_second_run(self):
        registry = {
            "schemaVersion": 1,
            "packId": "p",
            "nextKey": 9,
            "entries": [{"entryKey": "e0008", "sourceAnchor": "pdf:2:block:2"}],
        }
        known, unknown = resolve_keys(registry, ["pdf:2:block:2"], accept_new=True)
        self.assertEqual(known["pdf:2:block:2"], "e0008")
        self.assertEqual(unknown, [])
        self.assertEqual(registry["nextKey"], 9)

    def test_repointing_an_anchor_preserves_the_entry_id(self):
        """A re-extraction that renumbers blocks must move keys, not mint them."""
        units = parse_units_file(UNITS)
        registry = {"schemaVersion": 1, "packId": make_meta()["packId"], "nextKey": 1, "entries": []}
        first, _ = assemble_pack(pages_of(), units, registry, make_meta(), accept_new_keys=True)

        moved = pages_of()
        for page in moved:
            for block in page["blocks"]:
                if "sourceAnchor" in block:
                    block["sourceAnchor"] = block["sourceAnchor"].replace(":block:", ":blk:")
        for item in registry["entries"]:
            item["sourceAnchor"] = item["sourceAnchor"].replace(":block:", ":blk:")

        second, _ = assemble_pack(moved, units, registry, make_meta(), accept_new_keys=False)
        self.assertEqual(
            [entry["id"] for entry in first["entries"]],
            [entry["id"] for entry in second["entries"]],
        )

    def test_a_registry_from_another_pack_is_refused(self):
        with tempfile.TemporaryDirectory() as workspace:
            path = Path(workspace) / "entry-keys.json"
            path.write_text(json.dumps({"packId": "other", "entries": []}), encoding="utf-8")
            with self.assertRaises(ImportError_):
                load_registry(path, "mine")

    def test_writing_a_registry_with_content_fields_is_refused(self):
        with tempfile.TemporaryDirectory() as workspace:
            path = Path(workspace) / "entry-keys.json"
            with self.assertRaises(ImportError_):
                save_registry(
                    path,
                    {
                        "schemaVersion": 1,
                        "packId": "p",
                        "nextKey": 2,
                        "entries": [{"entryKey": "e0001", "sourceAnchor": "a", "headword": "〜がち"}],
                    },
                )
            self.assertFalse(path.exists())


class ClozeTests(unittest.TestCase):
    def test_the_blank_lands_on_the_pattern(self):
        self.assertEqual(mark_cloze("これはがちだ。", "〜がち"), "これは⟦がち⟧だ。")

    def test_no_card_is_produced_when_the_pattern_is_not_in_the_sentence(self):
        """A blank in the wrong place teaches the wrong thing very efficiently."""
        self.assertEqual(mark_cloze("まったく別の文です。", "〜がち"), "")

    def test_a_cloze_card_is_generated_for_every_markable_example(self):
        units = parse_units_file(UNITS)
        registry = {"schemaVersion": 1, "packId": make_meta()["packId"], "nextKey": 1, "entries": []}
        pack, _report = assemble_pack(pages_of(), units, registry, make_meta(), accept_new_keys=True)
        prompts = [template["promptType"] for template in pack["entries"][0]["cardTemplates"]]
        self.assertEqual(prompts, ["recall", "cloze"])


if __name__ == "__main__":
    unittest.main()
