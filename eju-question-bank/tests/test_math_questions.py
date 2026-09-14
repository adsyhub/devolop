"""Mathematics questions pair a printed 問 with the blanks the key gives it."""
import json

from eju_bank.ocr.math_questions import (
    build_math_questions, collect_math_questions, looks_like_answer_page,
    stem_slot_letters,
)


def _stable_id(prefix, *parts):
    return prefix + "-".join(parts)


BOOKLET = {
    3: "数学-2\n\nI\n\n問1 $P = 10a^2$ とする。\n\n(1) $P = \\frac{A}{B}$ である。\n",
    4: "- 計算欄 (memo) -\n",
    5: "数学－4\n\n問2 2つの袋A, Bがある。\n\n(1) 確率は $\\frac{J}{KL}$ である。\n",
    # The booklet PDF often reprints the answer key at the end.
    9: ("<数 学> Mathematics\n\nコース1 Course 1\n問Q. 解答番号 row 正解A.\n\n"
        "I 問1 ABCD 5723\nEFGH 5435\n問2 JKL 925\nMN 25\n"),
}

ANSWERS = {"courses": {"MATHEMATICS_COURSE_1": {
    ("I", "1"): {"A": "5", "B": "7"},
    ("I", "2"): {"J": "9", "K": "2", "L": "5"},
}}}


def _write(tmp_path, pages):
    folder = tmp_path / "ocr_cache"
    folder.mkdir(parents=True)
    for number, raw in pages.items():
        (folder / f"p{number:04d}.json").write_text(
            json.dumps({"raw_text": raw}, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_slot_letters_come_from_unambiguous_notation_only():
    assert stem_slot_letters("$P = \\frac{A}{BC}$ である") == {"A", "B", "C"}
    assert stem_slot_letters("$\\boxed{H}$ が答え") == {"H"}
    # A bare capital is a variable name or a 大題 numeral just as often.
    assert stem_slot_letters("$P$ より小さい整数のうち最大のものは I である") == set()


def test_a_reprinted_answer_key_page_is_not_read_as_questions():
    assert looks_like_answer_page(BOOKLET[9]) is True
    assert looks_like_answer_page(BOOKLET[5]) is False


def test_collects_one_entry_per_printed_question(tmp_path):
    items = collect_math_questions(_write(tmp_path, BOOKLET))
    assert [(i["group"], i["question"]) for i in items] == [("I", "1"), ("I", "2")]
    assert items[1]["pages"] == [5]


def test_blanks_come_from_the_key_and_the_stem_only_checks_them(tmp_path):
    items = collect_math_questions(_write(tmp_path, BOOKLET))
    questions, stats = build_math_questions(
        items, ANSWERS, source_id="s", form_code="MATHEMATICS_COURSE_1_JA",
        stable_id=_stable_id)
    assert stats["emitted"] == 2
    first = questions[0]
    assert first["answerSpec"] == {"type": "DIGIT_GRID", "slots": ["A", "B"]}
    assert first["correctAnswer"] == {"tokens": {"A": "5", "B": "7"}}
    assert first["answerRef"] == "I:1"


def test_a_stem_referencing_a_blank_the_key_lacks_is_refused(tmp_path):
    """Disagreement means the two were not read off the same question."""
    pages = {3: "I\n\n問1 $P = \\frac{X}{Y}$ である。\n"}
    items = collect_math_questions(_write(tmp_path, pages))
    questions, stats = build_math_questions(
        items, ANSWERS, source_id="s", form_code="MATHEMATICS_COURSE_1_JA",
        stable_id=_stable_id)
    assert questions == []
    assert stats["letters_disagree"] == 1


def test_a_question_the_key_says_nothing_about_is_dropped(tmp_path):
    pages = {3: "V\n\n問9 $P = \\frac{A}{B}$ である。\n"}
    items = collect_math_questions(_write(tmp_path, pages))
    questions, stats = build_math_questions(
        items, ANSWERS, source_id="s", form_code="MATHEMATICS_COURSE_1_JA",
        stable_id=_stable_id)
    assert questions == []
    assert stats["no_slots"] == 1


def test_a_group_without_a_question_number_is_one_question(tmp_path):
    pages = {3: "III\n\n$P = \\frac{A}{B}$ である。\n"}
    answers = {"courses": {"MATHEMATICS_COURSE_1": {("III", ""): {"A": "1", "B": "1"}}}}
    items = collect_math_questions(_write(tmp_path, pages))
    questions, stats = build_math_questions(
        items, answers, source_id="s", form_code="MATHEMATICS_COURSE_1_JA",
        stable_id=_stable_id)
    assert stats["emitted"] == 1
    assert questions[0]["answerRef"] == "III"
    assert questions[0]["printedLabel"] == "第III問"


def test_duplicate_group_and_question_are_collapsed(tmp_path):
    """Duplicates can only come from a misread, and they break audit uniqueness."""
    pages = {3: "I\n\n問1 $\\frac{A}{B}$ である。\n", 4: "I\n\n問1 $\\frac{A}{B}$ である。\n"}
    items = collect_math_questions(_write(tmp_path, pages))
    assert len(items) == 1
