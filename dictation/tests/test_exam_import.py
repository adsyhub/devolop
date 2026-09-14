"""Assembling a paper from transcribed pages plus its printed answer key.

The importer's job is to be mechanically right about the things a human reader
gets wrong at 2am: a passage split across a page break, a choice list split
across a page break, questions printed on the page *before* the leaflet they ask
about, and an answer key whose count silently disagrees with the pages. Every one
of those is a test here, because each of them, uncaught, shifts answers onto the
wrong questions and the learner has no way to see it.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from exam_import import (  # noqa: E402
    ImportError_,
    assemble_exam,
    load_pages,
    main,
    parse_answer_key,
)
from exam_schema import audit_exam  # noqa: E402

META = {"level": "N1", "title": "Import fixture", "sessionLabel": "2022年7月", "durationSec": 3600}


def block(kind, **fields):
    base = {
        "kind": kind,
        "partNumber": None,
        "label": None,
        "text": "",
        "questionNumber": None,
        "choices": None,
        "vertical": False,
        "continuesFromPreviousPage": False,
        "continuesOnNextPage": False,
    }
    base.update(fields)
    return base


def question_block(number, prompt="<u>問い</u>", part=1, **fields):
    return block(
        "question",
        partNumber=part,
        questionNumber=number,
        text=prompt,
        choices=["1つめ", "2つめ", "3つめ", "4つめ"],
        **fields,
    )


def page(number, blocks, **fields):
    doc = {"page": number, "pageLabel": f"第{number - 1}页", "sectionHeader": None, "blocks": blocks, "issues": []}
    doc.update(fields)
    return doc


BASIC_KEY = """
note      仅供参考
written   1-2   1   14
listening 1     2   3
"""


def basic_pages():
    return [
        page(2, [
            block("part-instruction", partNumber=1, text="問題1　読み方を選びなさい。"),
            question_block(1),
            question_block(2),
        ]),
        page(25, [
            block("section-header", text="第三部分　聴解"),
            block("part-instruction", partNumber=1, text="問題1　まず質問を聞いてください。"),
            question_block(None, prompt="", part=1, label="1番"),
        ], sectionHeader="第三部分　聴解"),
    ]


class AnswerKeyTests(unittest.TestCase):
    def test_ranges_expand_to_one_answer_per_question(self):
        key = parse_answer_key("written 1-6 1 133424")
        self.assertEqual([key["written"][n]["answer"] for n in range(1, 7)], [1, 3, 3, 4, 2, 4])
        self.assertTrue(all(key["written"][n]["points"] == 1.0 for n in range(1, 7)))

    def test_a_single_question_range_is_allowed(self):
        key = parse_answer_key("written 7 2 3")
        self.assertEqual(key["written"][7], {"answer": 3, "points": 2.0})

    def test_a_range_whose_length_disagrees_with_its_digits_is_rejected(self):
        """The failure this catches shifts every later answer by one."""
        with self.assertRaises(ImportError_) as caught:
            parse_answer_key("written 1-6 1 13342")
        self.assertIn("6 questions but 5 answers", str(caught.exception))

    def test_a_question_listed_in_two_ranges_is_rejected(self):
        with self.assertRaises(ImportError_):
            parse_answer_key("written 1-6 1 133424\nwritten 6-8 1 424")

    def test_an_ordering_must_be_a_permutation(self):
        with self.assertRaises(ImportError_):
            parse_answer_key("written 36 2 4\norder 36 3341")

    def test_comments_and_blank_lines_are_ignored(self):
        key = parse_answer_key("# comment\n\nwritten 1 1 2   # trailing\n")
        self.assertEqual(key["written"][1]["answer"], 2)

    def test_an_unknown_directive_is_rejected_rather_than_skipped(self):
        with self.assertRaises(ImportError_):
            parse_answer_key("written 1 1 2\nlisening 1 1 3")

    def test_a_key_with_no_answers_is_rejected(self):
        with self.assertRaises(ImportError_):
            parse_answer_key("note 只有说明")

    def test_a_dispute_attaches_to_its_question_without_changing_the_answer(self):
        """These keys are 非标准答案; a contested entry is annotated, never rewritten."""
        exam = assemble_exam(
            basic_pages(),
            parse_answer_key(BASIC_KEY + "\ndispute 2 原文更支持选项 3。"),
            META,
        )
        written = exam["sections"][0]["parts"][0]["questions"]
        self.assertEqual(written[1]["answer"], 4, "the printed key still decides the answer")
        self.assertEqual(written[1]["keyNote"], "原文更支持选项 3。")
        self.assertEqual(written[0]["keyNote"], "")

    def test_a_dispute_for_a_question_that_does_not_exist_is_refused(self):
        with self.assertRaises(ImportError_):
            assemble_exam(basic_pages(), parse_answer_key(BASIC_KEY + "\ndispute 9 nope"), META)

    def test_a_dispute_line_needs_both_a_number_and_text(self):
        for bad in ("dispute 58", "dispute foo bar"):
            with self.assertRaises(ImportError_):
                parse_answer_key(f"written 1 1 2\n{bad}")

    def test_the_note_is_carried_through(self):
        key = parse_answer_key("note 答案非标准答案\nwritten 1 1 2")
        self.assertEqual(key["note"], "答案非标准答案")


class AssemblyTests(unittest.TestCase):
    def assemble(self, pages, key_text=BASIC_KEY, meta=None):
        return assemble_exam(pages, parse_answer_key(key_text), meta or META)

    def test_a_basic_paper_assembles_and_passes_its_audit(self):
        exam = self.assemble(basic_pages())
        report = audit_exam(exam)
        self.assertEqual(report["status"], "passed", report["issues"])
        self.assertEqual(exam["questionCount"], 3)
        self.assertEqual(exam["totalPoints"], 4.0)

    def test_written_and_listening_land_in_different_sections(self):
        exam = self.assemble(basic_pages())
        kinds = [section["kind"] for section in exam["sections"]]
        self.assertEqual(kinds, ["language-knowledge", "listening"])
        self.assertTrue(exam["sections"][1]["audioRequired"])

    def test_answers_are_applied_by_printed_number_for_written_questions(self):
        exam = self.assemble(basic_pages())
        written = exam["sections"][0]["parts"][0]["questions"]
        self.assertEqual([q["number"] for q in written], [1, 2])
        self.assertEqual([q["answer"] for q in written], [1, 4])

    def test_listening_answers_are_applied_positionally(self):
        """聴解 numbering restarts per 問題, so position is the only stable key."""
        exam = self.assemble(basic_pages())
        listening = exam["sections"][1]["parts"][0]["questions"]
        self.assertEqual([q["answer"] for q in listening], [3])
        self.assertEqual([q["number"] for q in listening], [1])

    def test_a_worked_example_is_kept_but_never_scored(self):
        pages = basic_pages()
        pages[1]["blocks"].insert(2, question_block(None, prompt="", part=1, label="例"))
        exam = self.assemble(pages)
        listening = exam["sections"][1]["parts"][0]["questions"]
        self.assertEqual([q["label"] for q in listening], ["例", "1番"])
        self.assertTrue(listening[0]["example"])
        self.assertIsNone(listening[0]["answer"])
        self.assertEqual(listening[0]["points"], 0.0)
        # The single listening answer still belongs to 1番, not to the example.
        self.assertEqual(listening[1]["answer"], 3)

    def test_a_passage_split_across_a_page_break_is_rejoined_mid_sentence(self):
        pages = [
            page(21, [
                block("part-instruction", partNumber=12, text="問題12　次の文章を読んで答えなさい。"),
                block("passage", partNumber=12, text="人間もまたそんな生命に助けられ、あるいは支えられ",
                      continuesOnNextPage=True),
            ]),
            page(22, [
                block("passage", partNumber=12, text="て生きている。これは共生関係とも呼べる。",
                      continuesFromPreviousPage=True),
                block("note", partNumber=12, label="(注1)", text="（注1）共生：ともに生きること"),
                question_block(1, part=12),
            ]),
        ]
        exam = assemble_exam(pages, parse_answer_key("written 1 3 2"), META)
        passages = exam["sections"][0]["parts"][0]["passages"]
        self.assertEqual(len(passages), 1)
        self.assertIn("あるいは支えられて生きている。", passages[0]["text"])
        self.assertEqual(passages[0]["notes"], ["（注1）共生：ともに生きること"])
        self.assertEqual(passages[0]["pages"], [21, 22])

    def test_a_choice_list_split_across_a_page_break_is_rejoined(self):
        pages = [
            page(29, [
                block("part-instruction", partNumber=2, text="問題2"),
                block("question", partNumber=2, label="6番", questionNumber=6,
                      choices=["負担のない働き方", "食品ロスを減らす"], continuesOnNextPage=True),
            ], sectionHeader="第三部分　聴解"),
            page(30, [
                block("question", partNumber=2, label="6番", questionNumber=6,
                      choices=["売り上げを伸ばす", "客に満足してもらう"], continuesFromPreviousPage=True),
            ]),
        ]
        exam = assemble_exam(pages, parse_answer_key("listening 2 1 4"), META)
        questions = exam["sections"][0]["parts"][0]["questions"]
        self.assertEqual(len(questions), 1)
        self.assertEqual(len(questions[0]["choices"]), 4)
        self.assertEqual(questions[0]["choices"][3], "客に満足してもらう")

    def test_unlabelled_cloze_items_are_not_merged_into_one(self):
        """問題7 prints only choice lists; every block there has a null label.

        Merging on label alone collapsed all four items into question 41 and lost
        42-44 entirely, which the answer key then reported as missing.
        """
        pages = [
            page(9, [
                block("part-instruction", partNumber=7, text="問題7　文章を読んで【41】から【44】を選びなさい。"),
                block("passage", partNumber=7, text="本文に【41】と【42】と【43】と【44】がある。"),
            ]),
            page(10, [
                question_block(n, prompt="", part=7, continuesFromPreviousPage=True)
                for n in (41, 42, 43, 44)
            ]),
        ]
        exam = assemble_exam(pages, parse_answer_key("written 41-44 1 3211"), META)
        questions = exam["sections"][0]["parts"][0]["questions"]
        self.assertEqual([q["number"] for q in questions], [41, 42, 43, 44])
        self.assertEqual([q["answer"] for q in questions], [3, 2, 1, 1])
        # An item whose only printed content is its boxed number still gets a prompt.
        self.assertEqual([q["prompt"] for q in questions], ["【41】", "【42】", "【43】", "【44】"])

    def test_questions_printed_before_their_leaflet_still_link_to_it(self):
        """問題13 prints its questions on the left page and the leaflet on the right."""
        pages = [
            page(23, [
                block("part-instruction", partNumber=13, text="問題13　右のページは案内である。"),
                question_block(1, part=13),
                question_block(2, part=13),
            ]),
            page(24, [
                block("passage", partNumber=13, label="案内", text="| A | 30,000円以上 |\n| B | 30,000円未満 |"),
            ]),
        ]
        exam = assemble_exam(pages, parse_answer_key("written 1-2 2 12"), META)
        part = exam["sections"][0]["parts"][0]
        passage_id = part["passages"][0]["id"]
        self.assertTrue(all(q["passageIds"] == [passage_id] for q in part["questions"]))

    def test_an_integrated_reading_question_sees_both_texts(self):
        pages = [
            page(20, [
                block("part-instruction", partNumber=11, text="問題11　AとBの文章を読んで答えなさい。"),
                block("passage", partNumber=11, label="A", text="Aの本文。"),
                block("passage", partNumber=11, label="B", text="Bの本文。"),
                question_block(1, part=11),
            ]),
        ]
        exam = assemble_exam(pages, parse_answer_key("written 1 3 2"), META)
        part = exam["sections"][0]["parts"][0]
        self.assertEqual(len(part["passages"]), 2)
        self.assertEqual(len(part["questions"][0]["passageIds"]), 2)

    def test_each_question_follows_its_own_labelled_passage(self):
        pages = [
            page(11, [
                block("part-instruction", partNumber=8, text="問題8"),
                block("passage", partNumber=8, label="(1)", text="一つめの本文。"),
                question_block(1, part=8, label="(1)"),
                block("passage", partNumber=8, label="(2)", text="二つめの本文。"),
                question_block(2, part=8, label="(2)"),
            ]),
        ]
        exam = assemble_exam(pages, parse_answer_key("written 1-2 2 31"), META)
        part = exam["sections"][0]["parts"][0]
        first, second = part["passages"]
        self.assertEqual(part["questions"][0]["passageIds"], [first["id"]])
        self.assertEqual(part["questions"][1]["passageIds"], [second["id"]])

    def test_a_sentence_composition_ordering_reaches_the_question(self):
        pages = [
            page(8, [
                block("part-instruction", partNumber=6, text="問題6　★に入るものを選びなさい。"),
                question_block(36, prompt="私は＿＿＿＿、＿＿★＿＿と思う。", part=6),
            ]),
        ]
        exam = assemble_exam(pages, parse_answer_key("written 36 2 4\norder 36 3241"), META)
        question = exam["sections"][0]["parts"][0]["questions"][0]
        self.assertEqual(question["answerOrder"], [3, 2, 4, 1])
        report = audit_exam(exam)
        self.assertEqual(report["summary"]["errors"], 0, report["issues"])
        # Only 問題6 was imported, so the numbering starts at 36 rather than 1.
        self.assertIn("exam.numbering_partial", {issue["code"] for issue in report["issues"]})

    def test_a_figure_attaches_to_the_question_it_follows(self):
        pages = basic_pages()
        pages[1]["blocks"].append(block("figure", partNumber=1, text="（枠内に三つのイラスト）"))
        exam = self.assemble(pages)
        listening = exam["sections"][1]["parts"][0]["questions"]
        self.assertEqual(listening[-1]["figureNote"], "（枠内に三つのイラスト）")


class MismatchTests(unittest.TestCase):
    """The importer must fail loudly rather than shift answers onto wrong questions."""

    def test_a_listening_count_mismatch_is_refused(self):
        with self.assertRaises(ImportError_) as caught:
            assemble_exam(basic_pages(), parse_answer_key("written 1-2 1 14\nlistening 1 2 34"), META)
        self.assertIn("2 answers", str(caught.exception))
        self.assertIn("1 scored questions", str(caught.exception))

    def test_an_answer_for_a_question_no_page_contains_is_refused(self):
        with self.assertRaises(ImportError_) as caught:
            assemble_exam(basic_pages(), parse_answer_key("written 1-3 1 143\nlistening 1 2 3"), META)
        self.assertIn("[3]", str(caught.exception))

    def test_a_question_with_no_answer_in_the_key_is_refused(self):
        pages = basic_pages()
        pages[0]["blocks"].append(question_block(3))
        with self.assertRaises(ImportError_):
            assemble_exam(pages, parse_answer_key(BASIC_KEY), META)

    def test_a_listening_part_missing_from_the_key_is_refused(self):
        with self.assertRaises(ImportError_):
            assemble_exam(basic_pages(), parse_answer_key("written 1-2 1 14"), META)

    def test_an_unknown_level_is_refused_rather_than_guessed(self):
        with self.assertRaises(ImportError_):
            assemble_exam(basic_pages(), parse_answer_key(BASIC_KEY), {**META, "level": "N9"})

    def test_a_block_before_any_heading_is_refused(self):
        pages = [page(2, [question_block(1, part=None)])]
        with self.assertRaises(ImportError_):
            assemble_exam(pages, parse_answer_key("written 1 1 2"), META)


class LoadPagesTests(unittest.TestCase):
    def test_pages_are_ordered_numerically_not_lexically(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            for number in (2, 10, 9):
                (directory / f"p{number:02d}.json").write_text(
                    json.dumps(page(number, [])), encoding="utf-8"
                )
            self.assertEqual([doc["page"] for doc in load_pages(directory)], [2, 9, 10])

    def test_an_empty_directory_is_an_error(self):
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(ImportError_):
                load_pages(Path(raw))

    def test_a_file_that_is_not_a_page_is_an_error(self):
        with tempfile.TemporaryDirectory() as raw:
            (Path(raw) / "p02.json").write_text('{"nope": true}', encoding="utf-8")
            with self.assertRaises(ImportError_):
                load_pages(Path(raw))


class CliTests(unittest.TestCase):
    def test_assemble_writes_an_exam_and_validate_accepts_it(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pages_dir = root / "pages"
            pages_dir.mkdir()
            for doc in basic_pages():
                (pages_dir / f"p{doc['page']:02d}.json").write_text(
                    json.dumps(doc, ensure_ascii=False), encoding="utf-8"
                )
            (root / "key.txt").write_text(BASIC_KEY, encoding="utf-8")
            (root / "meta.json").write_text(json.dumps(META), encoding="utf-8")
            out = root / "exams" / "fixture" / "exam.json"

            status = main([
                "assemble", "--pages", str(pages_dir), "--key", str(root / "key.txt"),
                "--meta", str(root / "meta.json"), "--out", str(out),
            ])
            self.assertEqual(status, 0)
            self.assertTrue(out.is_file())
            self.assertEqual(main(["validate", "--exam", str(out)]), 0)

    def test_assemble_refuses_to_write_an_exam_that_failed_its_audit(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pages_dir = root / "pages"
            pages_dir.mkdir()
            pages = copy.deepcopy(basic_pages())
            pages[0]["blocks"][1]["choices"] = ["only", "three", "choices"]
            for doc in pages:
                (pages_dir / f"p{doc['page']:02d}.json").write_text(
                    json.dumps(doc, ensure_ascii=False), encoding="utf-8"
                )
            (root / "key.txt").write_text(BASIC_KEY, encoding="utf-8")
            (root / "meta.json").write_text(json.dumps(META), encoding="utf-8")
            out = root / "exam.json"

            status = main([
                "assemble", "--pages", str(pages_dir), "--key", str(root / "key.txt"),
                "--meta", str(root / "meta.json"), "--out", str(out),
            ])
            self.assertEqual(status, 1)
            self.assertFalse(out.exists())


class ShippedExamTests(unittest.TestCase):
    """The real 2022年7月 N1 paper, if it is present in this checkout."""

    EXAM = PROJECT_DIR / "exams" / "2022-07-N1" / "exam.json"

    def setUp(self):
        if not self.EXAM.is_file():
            self.skipTest("exams/2022-07-N1/exam.json is not present")
        self.exam = json.loads(self.EXAM.read_text(encoding="utf-8"))

    def test_it_passes_its_audit(self):
        report = audit_exam(self.exam)
        self.assertEqual(report["status"], "passed", report["issues"])

    def test_it_has_the_question_counts_the_printed_key_implies(self):
        counts = {
            (section["kind"], part["number"]): len(
                [q for q in part["questions"] if not q["example"]]
            )
            for section in self.exam["sections"]
            for part in section["parts"]
        }
        # 第一部分 1-44, 第二部分 45-68, 第三部分 6+7+6+13+3.
        self.assertEqual(sum(v for (kind, _), v in counts.items() if kind == "language-knowledge"), 44)
        self.assertEqual(sum(v for (kind, _), v in counts.items() if kind == "reading"), 24)
        self.assertEqual(
            [counts[("listening", n)] for n in (1, 2, 3, 4, 5)], [6, 7, 6, 13, 3]
        )

    def test_every_section_is_worth_about_sixty_points(self):
        """The key says it was weighted so each section totals roughly 60."""
        from exam_schema import score_answers

        report = score_answers(self.exam, {})
        for section in report["sections"]:
            self.assertGreaterEqual(section["points"], 55.0, section["title"])
            self.assertLessEqual(section["points"], 65.0, section["title"])

    def test_the_reordering_answers_agree_with_the_ordering_rows(self):
        for section in self.exam["sections"]:
            for part in section["parts"]:
                if part["kind"] != "sentence-composition":
                    continue
                for question in part["questions"]:
                    star = question.get("answerStar", 3)
                    self.assertEqual(
                        question["answerOrder"][star - 1],
                        question["answer"],
                        f"{question['answerSheetLabel']}: fragment on the ★ blank",
                    )


if __name__ == "__main__":
    unittest.main()
