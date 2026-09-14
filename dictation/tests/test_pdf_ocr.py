"""Regressions for the local-VLM OCR pipeline (src/pdf_ocr).

Everything here runs without a GPU, without torch and without downloading a
model: the parts worth pinning are the deterministic ones around the model --
page selection, the resume cache, the degeneracy detector that decides which
pages get re-OCR'd, and the assembly of document.md / document.json.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import support  # noqa: F401  (puts src/ on sys.path)

import pymupdf
from PIL import Image

from pdf_ocr.assemble import (
    BLANK_MARKER,
    BOX_MARKER,
    NO_BOX_MARKER,
    _repetition_ratio,
    box_is_degenerate,
    box_is_suspicious,
    clean_page,
    mark_ruby_lines,
    merge_box,
    page_report,
    write_outputs,
)
from pdf_ocr.backends.base import PageResult
from pdf_ocr.backends.dots_ocr import _blocks_to_markdown, _parse_layout_json
from pdf_ocr.backends.openai_vlm import OpenAICompatVLMBackend
from pdf_ocr.render import crop_column, pdf_summary, render_pdf
from pdf_ocr.__main__ import (
    load_all_boxes,
    load_box,
    load_cached,
    parse_pages,
    save_box,
    save_cached,
)


class ParsePagesTests(unittest.TestCase):
    def test_ranges_lists_and_singletons(self) -> None:
        self.assertEqual(parse_pages("1-5,9", 157), [1, 2, 3, 4, 5, 9])
        self.assertEqual(parse_pages("3", 157), [3])
        self.assertEqual(parse_pages("9-7", 157), [])

    def test_none_and_all_mean_every_page(self) -> None:
        self.assertIsNone(parse_pages(None, 10))
        self.assertIsNone(parse_pages("all", 10))

    def test_out_of_range_pages_are_dropped(self) -> None:
        # A --pages typo must not crash a long run, nor index past the PDF.
        self.assertEqual(parse_pages("0,1,200", 5), [1])


class CleanPageTests(unittest.TestCase):
    def test_strips_a_fence_wrapping_the_whole_page(self) -> None:
        self.assertEqual(clean_page("```markdown\n# 見出し\n本文\n```"), "# 見出し\n本文")

    def test_keeps_a_fence_that_is_only_part_of_the_page(self) -> None:
        text = "前書き\n\n```\ncode\n```"
        self.assertEqual(clean_page(text), text)

    def test_running_heads_dropped_only_on_request(self) -> None:
        page = "<!-- header: 第2週 -->\n本文\n<!-- footer: 41 -->"
        self.assertIn("第2週", clean_page(page))
        self.assertEqual(clean_page(page, drop_running_heads=True), "本文")

    def test_collapses_runs_of_blank_lines(self) -> None:
        self.assertEqual(clean_page("a\n\n\n\n\nb"), "a\n\nb")

    def test_strips_reasoning_block_and_box_tokens(self) -> None:
        # GLM-OCR's actual shape: reasoning, then the answer inside box tokens.
        page = (
            "<think>The user provided an image. It is blank, so per the rules "
            "I output the blank marker.</think>\n"
            "<|begin_of_box|><!-- blank page --><|end_of_box|>"
        )
        self.assertEqual(clean_page(page), BLANK_MARKER)

    def test_keeps_the_transcription_around_the_box_tokens(self) -> None:
        page = "<think>reasoning</think>\n<|begin_of_box|># 見出し\n本文<|end_of_box|>"
        self.assertEqual(clean_page(page), "# 見出し\n本文")

    def test_unclosed_reasoning_leaves_the_page_empty(self) -> None:
        # Token limit hit mid-reasoning: nothing was transcribed. Reporting the
        # page as empty routes it to --retry-flagged; keeping the reasoning text
        # would hide a lost page behind plausible prose.
        page = "<think>Got it, let's tackle this transcription step by step. First"
        self.assertEqual(clean_page(page), "")
        report = page_report(PageResult(page=7, markdown=page), clean_page(page))
        self.assertIn("empty", report["flags"])


class RepetitionTests(unittest.TestCase):
    def test_flags_a_decoding_loop(self) -> None:
        # The classic VLM failure on a dense page: one phrase to the token limit.
        looped = "正しい文を作りなさい。" + "につれて、" * 40
        self.assertGreater(_repetition_ratio(looped), 0.8)

    def test_ordinary_japanese_prose_is_not_flagged(self) -> None:
        prose = (
            "北へ行くにしたがって、紅葉は早くなる。予定表にしたがい、学習を進める。"
            "温度が上がるとともに、湿度も上がった。社会が変化するのに伴って、言葉も変化する。"
        )
        self.assertLess(_repetition_ratio(prose), 0.25)

    def test_short_text_is_never_flagged(self) -> None:
        self.assertEqual(_repetition_ratio("はい。" * 4), 0.0)


class MarkRubyLinesTests(unittest.TestCase):
    """The model half-reads furigana and strands it on its own line.

    Marking those lines is only safe if it never swallows real kana text, so the
    negative cases matter more than the positive one.
    """

    def test_marks_a_kana_line_stranded_under_a_kanji_line(self) -> None:
        marked = mark_ruby_lines("この本の使い方\nほんつかかた")
        self.assertEqual(marked, "この本の使い方\n<!-- ruby: ほんつかかた -->")

    def test_leaves_a_real_kana_sentence_alone(self) -> None:
        # Punctuation is the tell: ruby dumps never carry it.
        page = "私は学生です。\nこれはペンです。"
        self.assertEqual(mark_ruby_lines(page), page)

    def test_leaves_kana_alone_when_the_line_above_has_no_kanji(self) -> None:
        page = "ヒント\nひっこし"
        self.assertEqual(mark_ruby_lines(page), page)

    def test_does_not_mark_a_long_kana_passage(self) -> None:
        page = "本文\n" + "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほ" * 3
        self.assertEqual(mark_ruby_lines(page), page)

    def test_is_off_unless_requested(self) -> None:
        page = "この本の使い方\nほんつかかた"
        self.assertNotIn("<!-- ruby:", clean_page(page))
        self.assertIn("<!-- ruby:", clean_page(page, mark_ruby=True))

    def test_nothing_is_deleted(self) -> None:
        marked = mark_ruby_lines("この本の使い方\nほんつかかた")
        self.assertIn("ほんつかかた", marked)


class PageReportTests(unittest.TestCase):
    def test_error_page_is_flagged(self) -> None:
        report = page_report(PageResult(page=3, markdown="", error="OutOfMemoryError"), "")
        self.assertIn("error", report["flags"])

    def test_empty_page_is_flagged(self) -> None:
        self.assertIn("empty", page_report(PageResult(page=3, markdown=""), "")["flags"])

    def test_blank_page_marker_is_not_flagged_as_short(self) -> None:
        marker = "<!-- blank page -->"
        report = page_report(PageResult(page=3, markdown=marker), marker)
        self.assertEqual(report["flags"], [])

    def test_counts_scripts_so_a_chinese_only_page_is_visible(self) -> None:
        # If the model starts translating, kana collapses and han spikes.
        report = page_report(PageResult(page=1, markdown="あア亜a"), "あア亜a")
        self.assertEqual(report["scripts"], {"kana": 2, "han": 1, "latin": 1})


class WriteOutputsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.out = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_writes_all_three_artefacts_and_lists_flagged_pages(self) -> None:
        # Long enough not to trip the "very-short" heuristic: page 3 is the only
        # page this test means to flag.
        results = [
            PageResult(page=2, markdown="二ページ目。" + "本文が続きます。" * 6, seconds=1.0),
            PageResult(page=1, markdown="一ページ目。" + "本文が続きます。" * 6, seconds=1.0),
            PageResult(page=3, markdown="", seconds=0.5, error="boom"),
        ]
        report = write_outputs(self.out, results, source={"pages": 3}, backend={"backend": "test"})

        document = (self.out / "document.md").read_text(encoding="utf-8")
        # Pages are emitted in reading order regardless of completion order.
        self.assertLess(document.index("一ページ目"), document.index("二ページ目"))
        self.assertIn("<!-- page: 1 -->", document)

        parsed = json.loads((self.out / "document.json").read_text(encoding="utf-8"))
        self.assertEqual([p["page"] for p in parsed["pages"]], [1, 2, 3])
        self.assertEqual(parsed["pages"][2]["error"], "boom")

        self.assertEqual(report["flagged_pages"], [3])
        self.assertTrue((self.out / "quality-report.json").exists())


class ResumeCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.out = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_round_trips_a_page_so_an_interrupted_run_resumes(self) -> None:
        self.assertIsNone(load_cached(self.out, 7))
        save_cached(
            self.out,
            PageResult(page=7, markdown="本文", seconds=2.5, backend={"model_id": "local"}),
        )
        restored = load_cached(self.out, 7)
        self.assertEqual((restored.page, restored.markdown), (7, "本文"))
        self.assertEqual(restored.backend, {"model_id": "local"})

    def test_assembly_covers_every_cached_page_not_just_the_retried_ones(self) -> None:
        """A retry must not overwrite a finished document with its own subset.

        --retry-flagged narrows the run to a handful of pages. Assembling from
        that narrowed list once turned a finished 157-page document.md into a
        6-page one; only the per-page cache saved the run.
        """
        for number in range(1, 6):
            save_cached(self.out, PageResult(page=number, markdown=f"{number}ページ目の本文。" * 5))

        retried = [3]  # what a --retry-flagged pass would have re-rendered
        assembled = [
            r for n in range(1, 6) if (r := load_cached(self.out, n)) is not None
        ]
        self.assertEqual([r.page for r in assembled], [1, 2, 3, 4, 5])
        self.assertNotEqual([r.page for r in assembled], retried)

    def test_a_truncated_cache_file_is_treated_as_missing(self) -> None:
        # A run killed mid-write must be redone, not crash the next run.
        path = self.out / "pages" / "page-0007.json"
        path.parent.mkdir(parents=True)
        path.write_text('{"page": 7, "markd', encoding="utf-8")
        self.assertIsNone(load_cached(self.out, 7))


class OpenAICompatVLMTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.out = Path(self._temp.name)

    def tearDown(self) -> None:
        os.environ.pop("OCR_TEST_KEY", None)
        self._temp.cleanup()

    def test_sends_an_image_data_url_and_records_no_secret(self) -> None:
        image = self.out / "page-0007.png"
        Image.new("RGB", (8, 8), "white").save(image)
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "# 見出し\n本文"}}]}
        ).encode("utf-8")
        response.__exit__.return_value = False

        os.environ["OCR_TEST_KEY"] = "secret-value"
        backend = OpenAICompatVLMBackend(
            model_id="local-vlm",
            base_url="http://127.0.0.1:9999/v1",
            api_key_env="OCR_TEST_KEY",
            max_new_tokens=456,
        )
        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            result = backend.transcribe(image, prompt="read exactly")

        self.assertTrue(result.ok)
        self.assertEqual(result.page, 7)
        self.assertEqual(result.markdown, "# 見出し\n本文")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "local-vlm")
        self.assertEqual(payload["max_tokens"], 456)
        self.assertEqual(payload["messages"][0]["content"][0]["text"], "read exactly")
        image_url = payload["messages"][0]["content"][1]["image_url"]["url"]
        self.assertTrue(image_url.startswith("data:image/png;base64,"))
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-value")
        self.assertNotIn("secret-value", json.dumps(backend.describe()))

    def test_empty_response_is_a_page_error(self) -> None:
        image = self.out / "page-0008.png"
        Image.new("RGB", (8, 8), "white").save(image)
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": ""}}]}
        ).encode("utf-8")
        response.__exit__.return_value = False
        backend = OpenAICompatVLMBackend()
        with mock.patch("urllib.request.urlopen", return_value=response):
            result = backend.transcribe(image, prompt="read")
        self.assertFalse(result.ok)
        self.assertIn("empty content", result.error)


class DotsLayoutTests(unittest.TestCase):
    def test_parses_a_fenced_json_array(self) -> None:
        raw = '```json\n[{"category": "Title", "text": "第2週"}]\n```'
        self.assertEqual(_parse_layout_json(raw), [{"category": "Title", "text": "第2週"}])

    def test_unparseable_output_yields_no_blocks(self) -> None:
        self.assertEqual(_parse_layout_json("sorry, I cannot read this page"), [])

    def test_blocks_become_markdown_with_headers_set_aside(self) -> None:
        markdown = _blocks_to_markdown(
            [
                {"category": "Title", "text": "北へ行く"},
                {"category": "Page-footer", "text": "41"},
                {"category": "Picture"},
            ]
        )
        self.assertIn("# 北へ行く", markdown)
        self.assertIn("<!-- footer: 41 -->", markdown)
        self.assertIn("![](figure)", markdown)


class BoxPassTests(unittest.TestCase):
    """The second pass that recovers the floated grammar-connection panels.

    Whole-page OCR downscales to fit the visual-token budget and drops those
    panels silently; the crop pass reads them at native resolution. Two hazards
    are pinned here: a recovered panel must never overwrite the page it belongs
    to, and over-capture must be visible rather than silent.
    """

    def test_merge_appends_under_its_own_marker(self) -> None:
        merged = merge_box("本文です。", "> Nに\n> したがって")
        self.assertTrue(merged.startswith("本文です。"))
        self.assertIn(BOX_MARKER, merged)
        self.assertIn("> したがって", merged)

    def test_no_box_marker_merges_to_nothing(self) -> None:
        self.assertEqual(merge_box("本文です。", NO_BOX_MARKER), "本文です。")
        self.assertEqual(merge_box("本文です。", ""), "本文です。")
        self.assertEqual(merge_box("本文です。", None), "本文です。")

    def test_a_short_conjugation_chart_is_not_suspicious(self) -> None:
        self.assertFalse(box_is_suspicious("> Nに\n> 基づいて\n> 基づき\n> 基づく N"))

    def test_a_body_text_dump_is_suspicious(self) -> None:
        # What the model returns when the crop holds no box at all: on the front
        # matter of this book it dumped ~25 lines of body prose. Length is what
        # separates that from a chart, so the fixture has to be realistically long.
        dump = "\n".join(
            "> 合った文法形式かどうかを判断することができるかを問う問題です。" for _ in range(25)
        )
        self.assertGreater(len(dump), 600)
        self.assertTrue(box_is_suspicious(dump))

    def test_long_lines_alone_are_enough_to_be_suspicious(self) -> None:
        # Three prose-length lines are enough even well under the total-length cap.
        line = "これは本文の一部であって、接続の表ではありませんから、この行は箱の中身ではありません。"
        self.assertGreater(len(line), 30)
        prose = "\n".join(f"> {line}" for _ in range(3))
        self.assertLess(len(prose), 600)
        self.assertTrue(box_is_suspicious(prose))

    def test_a_looped_box_read_is_degenerate(self) -> None:
        # The bracket joining several endings to one stem is a knife-edge for
        # greedy decoding; when it latches, it repeats to the token limit.
        self.assertTrue(box_is_degenerate("> Nするに\n" + "> 〜\n" * 60))
        self.assertTrue(box_is_degenerate("> Nは\n" + "> あなたはもちろんです。\n" * 20))

    def test_a_real_chart_is_not_degenerate(self) -> None:
        chart = (
            "> Nに\n> 基づいて\n> 基づき\n> 基づく N\n> 基づいた N\n"
            "> れい 資料に基づいて\n> 考えに基づいて\n> 意見に基づいて"
        )
        self.assertFalse(box_is_degenerate(chart))

    def test_a_degenerate_box_is_never_merged(self) -> None:
        """A loop must not be appended to a page whose body text is fine."""
        page = "本文はまったく正常です。" * 4
        self.assertEqual(merge_box(page, "> Nするに\n" + "> 〜\n" * 60), page)

    def test_box_round_trips_through_its_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.assertIsNone(load_box(out, 45))
            save_box(out, 45, "> Nにしたがって", 1.5, None)
            self.assertEqual(load_box(out, 45), "> Nにしたがって")
            self.assertEqual(load_all_boxes(out, 50), {45: "> Nにしたがって"})

    def test_reasoning_scaffolding_is_stripped_when_a_box_is_read(self) -> None:
        # A reasoning VLM wraps its answer. Unstripped, an empty crop stops
        # matching NO_BOX_MARKER and gets appended to the page as a chart.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            save_box(out, 7, f"<think>no panel here</think>\n<|begin_of_box|>{NO_BOX_MARKER}"
                             "<|end_of_box|>", 1.0, None)
            self.assertEqual(load_box(out, 7), NO_BOX_MARKER)
            self.assertEqual(merge_box("本文", load_box(out, 7)), "本文")

    def test_a_real_box_survives_the_stripping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            save_box(out, 8, "<think>reading the chart</think>\n"
                             "<|begin_of_box|>> Nにしたがって<|end_of_box|>", 1.0, None)
            self.assertEqual(load_box(out, 8), "> Nにしたがって")


class RenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _text_pdf(self) -> Path:
        path = self.root / "text.pdf"
        doc = pymupdf.open()
        for _ in range(3):
            page = doc.new_page()
            page.insert_text((72, 72), "this page has a real text layer " * 8)
        doc.save(path)
        doc.close()
        return path

    def test_summary_detects_an_existing_text_layer(self) -> None:
        summary = pdf_summary(self._text_pdf())
        self.assertEqual(summary["pages"], 3)
        self.assertTrue(summary["has_text_layer"])

    def test_renders_only_the_requested_pages_and_reuses_them(self) -> None:
        images = self.root / "images"
        rendered = render_pdf(self._text_pdf(), images, pages=[2], dpi=72)
        self.assertEqual([p.number for p in rendered], [2])
        self.assertTrue((images / "page-0002.png").exists())
        self.assertFalse((images / "page-0001.png").exists())

        # Second pass must not re-rasterise what is already on disk.
        again = render_pdf(self._text_pdf(), images, pages=[2], dpi=72)
        self.assertEqual(again[0].source, "cached")

    def _rotated_pdf(self, rotation: int) -> Path:
        """A one-page PDF holding a single full-page image, with /Rotate set."""
        path = self.root / f"rot{rotation}.pdf"
        image_path = self.root / "wide.png"
        # Deliberately non-square so a 90/270 turn is visible in the dimensions.
        Image.new("L", (400, 200), 255).save(image_path)
        doc = pymupdf.open()
        page = doc.new_page(width=400, height=200)
        page.insert_image(page.rect, filename=str(image_path))
        page.set_rotation(rotation)
        doc.save(path)
        doc.close()
        return path

    def test_embedded_extraction_honours_page_rotation(self) -> None:
        """Scans of Japanese books ship upside down with /Rotate 180.

        The lossless path pulls the embedded image straight out of the PDF, which
        skips the rotation the pixmap path would have applied. Three of five books
        in this project were stored that way; missing it feeds the model inverted
        pages and the OCR is silently worthless.
        """
        upright = render_pdf(self._rotated_pdf(0), self.root / "r0", pages=[1])[0]
        turned = render_pdf(self._rotated_pdf(90), self.root / "r90", pages=[1])[0]
        self.assertEqual((upright.width, upright.height), (400, 200))
        # A quarter turn must swap the axes; if /Rotate were ignored it would not.
        self.assertEqual((turned.width, turned.height), (200, 400))

    def test_rotation_180_keeps_dimensions_but_still_renders(self) -> None:
        flipped = render_pdf(self._rotated_pdf(180), self.root / "r180", pages=[1])[0]
        self.assertEqual((flipped.width, flipped.height), (400, 200))
        self.assertTrue(flipped.path.exists())

    def test_max_edge_downscales(self) -> None:
        rendered = render_pdf(self._text_pdf(), self.root / "small", pages=[1], dpi=150, max_edge=200)
        self.assertLessEqual(max(rendered[0].width, rendered[0].height), 200)


if __name__ == "__main__":
    unittest.main()
