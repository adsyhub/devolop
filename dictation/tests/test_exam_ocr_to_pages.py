"""The OCR-Markdown -> page-block converter.

These fixtures mirror what Qwen2.5-VL actually returns for the 2023/2024 papers:
a ```markdown fence it was told not to add, full-width item numbers, circled item
numbers in 問題6, and a footer comment carrying the printed page number.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from exam_ocr_to_pages import convert_directory, convert_page  # noqa: E402


def kinds(page):
    return [block["kind"] for block in page["blocks"]]


def questions(page):
    return [block for block in page["blocks"] if block["kind"] == "question"]


class ConvertPage(unittest.TestCase):
    def test_a_vocabulary_page_becomes_instruction_plus_numbered_items(self):
        page = convert_page(
            "```markdown\n"
            "問題6　次の言葉の使い方として最もよいものを、1・2・3・4から一つ選びなさい。\n"
            "26.薄める\n"
            "1 私には難しすぎたので、コースのレベルを<u>薄めた</u>\n"
            "2 部屋が暑かったので、エアコンをつけて温度を<u>薄めた</u>\n"
            "3 スープがしょっぱかったので、水を加えて味を<u>薄めた</u>\n"
            "4 うるさいと言われたので、テレビの音量を<u>薄めた</u>\n"
            "<!-- footer: — 6 — -->\n"
            "```",
            page=7,
            level="N2",
        )
        self.assertEqual(kinds(page), ["part-instruction", "question"])
        self.assertEqual(page["pageLabel"], "6")
        item = questions(page)[0]
        self.assertEqual(item["questionNumber"], 26)
        self.assertEqual(item["partNumber"], 6)
        self.assertEqual(item["text"], "薄める")
        self.assertEqual(len(item["choices"]), 4)
        self.assertIn("<u>薄めた</u>", item["choices"][2])
        self.assertEqual(page["issues"], [])

    def test_the_code_fence_the_model_adds_is_stripped(self):
        page = convert_page("```markdown\n問題1　読み方\n```", page=1, level="N1")
        self.assertEqual(kinds(page), ["part-instruction"])
        self.assertNotIn("```", json.dumps(page, ensure_ascii=False))

    def test_a_circled_item_number_opens_an_item_not_a_choice(self):
        """NFKC turns ㊱ into '36' and eats the separator, so it is read before that."""
        page = convert_page(
            "問題6　次の文の★に入る最もよいものを選びなさい。\n"
            "㊱スピーチにおいて、ジェスチャーを使いながら話すのは＿＿ ＿＿ ★＿＿ ＿＿ 印象を悪くする。\n"
            "1 あまりに\n2 効果的である反面\n3 かえって\n4 大きすぎるジェスチャーは\n",
            page=3,
            level="N1",
        )
        item = questions(page)[0]
        self.assertEqual(item["questionNumber"], 36)
        self.assertEqual(item["choices"], ["あまりに", "効果的である反面", "かえって", "大きすぎるジェスチャーは"])
        self.assertIn("★", item["text"])

    def test_a_circled_digit_inside_a_choice_run_stays_a_choice(self):
        page = convert_page("1.あ\n①か\n②き\n③く\n④け\n", page=1, level="N1")
        self.assertEqual(questions(page)[0]["choices"], ["か", "き", "く", "け"])

    def test_a_reading_passage_keeps_its_gloss_and_hangs_the_item_after_it(self):
        page = convert_page(
            "問題9　次の文章を読んで、後の問いに答えなさい。\n"
            "「常識を疑ってみる」ということ、実はそれが学問の始まりでもあります。\n"
            "（注1）常識：世間で当たり前とされている事柄\n"
            "49.筆者によると、学問とはどのような行為か。\n"
            "1 ア\n2 イ\n3 ウ\n4 エ\n",
            page=6,
            level="N1",
        )
        self.assertEqual(kinds(page), ["part-instruction", "passage", "note", "question"])
        self.assertIn("学問の始まり", page["blocks"][1]["text"])
        self.assertTrue(page["blocks"][2]["text"].startswith("(注1)"))

    def test_a_listening_item_is_labelled_rather_than_numbered(self):
        page = convert_page(
            "問題1　まず質問を聞いてください。\n1番\n1 資料をコピーする\n2 会議室を予約する\n"
            "3 部長に確認する\n4 メールを送る\n",
            page=26,
            level="N1",
        )
        item = questions(page)[0]
        self.assertEqual(item["label"], "1番")
        self.assertNotIn("questionNumber", item)
        self.assertEqual(len(item["choices"]), 4)

    def test_a_short_choice_run_is_flagged_rather_than_silently_accepted(self):
        page = convert_page("1.あ\n1 か\n2 き\n3 く\n問題2　次\n", page=1, level="N1")
        self.assertEqual(len(questions(page)[0]["choices"]), 3)
        self.assertTrue(any("3 choices" in issue for issue in page["issues"]))

    def test_an_out_of_order_choice_number_is_flagged(self):
        """The 2023-07 N1 reprint numbers its third choice '2'; that must not pass quietly."""
        page = convert_page("1.あ\n1 か\n2 き\n2 く\n4 け\n", page=1, level="N1")
        self.assertTrue(any("arrived at position" in issue for issue in page["issues"]))
        self.assertEqual(len(questions(page)[0]["choices"]), 4)

    def test_a_stem_wrapped_onto_a_second_line_is_rejoined(self):
        page = convert_page("1.この条約が締結されると、\n農業に影響が出る。\n1 あ\n2 い\n3 う\n4 え\n", page=1, level="N1")
        self.assertEqual(questions(page)[0]["text"], "この条約が締結されると、農業に影響が出る。")

    def test_a_blank_page_yields_no_blocks(self):
        page = convert_page("<!-- blank page -->", page=2, level="N1")
        self.assertEqual(page["blocks"], [])

    def test_a_figure_becomes_a_figure_block(self):
        page = convert_page("問題1　あ\n1番\n![](figure)\n", page=26, level="N1")
        self.assertIn("figure", kinds(page))


class ConvertDirectory(unittest.TestCase):
    def test_pages_are_written_and_an_ocr_error_is_reported_not_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "ocr" / "pages"
            pages.mkdir(parents=True)
            (pages / "page-0001.json").write_text(
                json.dumps({"page": 1, "markdown": "問題1　読み\n1.あ\n1 か\n2 き\n3 く\n4 け\n"}),
                encoding="utf-8",
            )
            (pages / "page-0002.json").write_text(
                json.dumps({"page": 2, "markdown": "", "error": "CUDA out of memory"}),
                encoding="utf-8",
            )
            out = root / "pages"
            summary = convert_directory(root / "ocr", out, level="N1")

            self.assertTrue((out / "p01.json").exists())
            self.assertFalse((out / "p02.json").exists())
            self.assertEqual([row["written"] for row in summary], [True, False])
            self.assertIn("CUDA out of memory", summary[1]["issues"][0])

            written = json.loads((out / "p01.json").read_text(encoding="utf-8"))
            self.assertEqual(written["page"], 1)
            self.assertEqual(len(questions(written)), 1)

    def test_cover_page_before_the_first_heading_is_not_written(self):
        # assemble_exam rejects any block before the first 問題 heading, so a
        # cover page in the draft fails the import of every paper that has one.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "ocr" / "pages"
            pages.mkdir(parents=True)
            (pages / "page-0001.json").write_text(
                json.dumps({"page": 1, "markdown": "問題用紙\nN1\n注意\n1. 試験が始まるまで開けないでください。"}),
                encoding="utf-8",
            )
            (pages / "page-0002.json").write_text(
                json.dumps({"page": 2, "markdown": "問題1　読み\n1.あ\n1 か\n2 き\n3 く\n4 け\n"}),
                encoding="utf-8",
            )
            out = root / "pages"
            summary = convert_directory(root / "ocr", out, level="N1")

            self.assertFalse((out / "p01.json").exists())
            self.assertTrue((out / "p02.json").exists())
            self.assertFalse(summary[0]["written"])
            self.assertIn("問題", summary[0]["issues"][0])

    def test_pages_are_all_kept_when_no_heading_is_ever_found(self):
        # Skipping is only safe as "everything before the first heading". With no
        # heading at all the reader has failed, and dropping the paper would hide it.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "ocr" / "pages"
            pages.mkdir(parents=True)
            (pages / "page-0001.json").write_text(
                json.dumps({"page": 1, "markdown": "なにかの文章"}), encoding="utf-8")
            (pages / "page-0002.json").write_text(
                json.dumps({"page": 2, "markdown": "つづきの文章"}), encoding="utf-8")
            out = root / "pages"
            summary = convert_directory(root / "ocr", out, level="N1")

            self.assertTrue((out / "p01.json").exists())
            self.assertTrue((out / "p02.json").exists())
            self.assertEqual([row["written"] for row in summary], [True, True])

    def test_reasoning_scaffolding_never_reaches_the_draft(self):
        # The cache holds raw model output, so a reasoning VLM's <think> block
        # would otherwise be converted into passage text on a finished-looking page.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "ocr" / "pages"
            pages.mkdir(parents=True)
            (pages / "page-0001.json").write_text(
                json.dumps({
                    "page": 1,
                    "markdown": "<think>Got it, let me read this exam page carefully.</think>\n"
                                "<|begin_of_box|>問題1　読み\n1.あ\n1 か\n2 き\n3 く\n4 け\n<|end_of_box|>",
                }),
                encoding="utf-8",
            )
            out = root / "pages"
            convert_directory(root / "ocr", out, level="N1")

            written = (out / "p01.json").read_text(encoding="utf-8")
            self.assertNotIn("<think>", written)
            self.assertNotIn("begin_of_box", written)
            self.assertEqual(len(questions(json.loads(written))), 1)


if __name__ == "__main__":
    unittest.main()
