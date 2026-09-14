"""Questions must come from what OCR read, joined to a verified answer."""
import json

from eju_bank.ocr.assemble_from_ocr import build_questions, collect_questions


def _stable_id(prefix, *parts):
    return prefix + "-".join(parts)


READING_PAGE = """読解

問1 次の文章の内容と合っているものはどれですか。

ぶどう狩りに行きませんか。9月30日，山梨のぶどう園へ行きます。

1. 参加したい人は，前もって申し込まなければならない。
2. 参加したい人は，前日までに電話をすればよい。
3. 参加費は当日集めます。
4. 雨でも決行します。
"""


def _write_cache(tmp_path, pages):
    folder = tmp_path / "ocr_cache"
    folder.mkdir(parents=True)
    for number, raw in pages.items():
        (folder / f"p{number:04d}.json").write_text(
            json.dumps({"raw_text": raw}, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_collects_questions_under_the_heading_that_precedes_them(tmp_path):
    work = _write_cache(tmp_path, {1: READING_PAGE})
    collected = collect_questions(work)
    assert len(collected) == 1
    assert collected[0]["section"] == "読解"
    assert collected[0]["label"] == "問1"
    assert collected[0]["page"] == 1


def test_section_carries_forward_to_later_pages(tmp_path):
    later = READING_PAGE.replace("読解\n\n", "").replace("問1", "問2")
    work = _write_cache(tmp_path, {1: READING_PAGE, 2: later})
    sections = [q["section"] for q in collect_questions(work)]
    assert sections == ["読解", "読解"]


def test_reading_number_joins_directly_to_the_answer_slot(tmp_path):
    """In the 日本語 booklet the printed 問N is itself the 解答欄 number."""
    collected = collect_questions(_write_cache(tmp_path, {1: READING_PAGE}))
    questions, stats = build_questions(
        collected, {"READING:1": "2"}, source_id="s", form_code="JAPANESE_JA",
        stable_id=_stable_id)
    assert stats["emitted"] == 1
    q = questions[0]
    assert q["answerRef"] == "READING:1"
    assert q["correctAnswer"] == {"optionKey": "2"}
    assert q["stemAst"][0]["value"].startswith("次の文章の内容と")
    assert [o["key"] for o in q["options"]] == ["1", "2", "3", "4"]


def test_question_without_a_verified_answer_is_not_emitted(tmp_path):
    collected = collect_questions(_write_cache(tmp_path, {1: READING_PAGE}))
    questions, stats = build_questions(
        collected, {}, source_id="s", form_code="JAPANESE_JA", stable_id=_stable_id)
    assert questions == []
    assert stats["no_answer"] == 1


def test_answer_outside_the_option_keys_is_refused(tmp_path):
    collected = collect_questions(_write_cache(tmp_path, {1: READING_PAGE}))
    questions, stats = build_questions(
        collected, {"READING:1": "7"}, source_id="s", form_code="JAPANESE_JA",
        stable_id=_stable_id)
    assert questions == []
    assert stats["answer_not_an_option"] == 1


def test_sections_whose_numbering_restarts_are_left_unjoined(tmp_path):
    """理科 renumbers 問N per 大題, so the printed number is not the slot."""
    page = READING_PAGE.replace("読解", "物理")
    collected = collect_questions(_write_cache(tmp_path, {1: page}))
    questions, stats = build_questions(
        collected, {"PHYSICS:1": "2"}, source_id="s", form_code="PHYSICS_JA",
        stable_id=_stable_id)
    assert questions == []
    assert stats["no_join"] == 1


def test_question_with_no_heading_above_it_is_not_assigned_a_section(tmp_path):
    page = READING_PAGE.replace("読解\n\n", "")
    collected = collect_questions(_write_cache(tmp_path, {1: page}))
    questions, stats = build_questions(
        collected, {"READING:1": "2"}, source_id="s", form_code="JAPANESE_JA",
        stable_id=_stable_id)
    assert questions == []
    assert stats["no_section"] == 1


def test_missing_cache_directory_is_safe(tmp_path):
    assert collect_questions(tmp_path) == []


def test_a_form_only_takes_its_own_sections(tmp_path):
    """One 理科 booklet holds 物理 / 化学 / 生物 as three separate forms."""
    physics = READING_PAGE.replace("読解", "物理")
    collected = collect_questions(_write_cache(tmp_path, {1: physics}))
    collected[0]["boxed_slot"] = "1"

    mine, mine_stats = build_questions(
        collected, {"PHYSICS:1": "2"}, source_id="s", form_code="PHYSICS_JA",
        stable_id=_stable_id)
    assert mine_stats["emitted"] == 1
    assert mine[0]["answerRef"] == "PHYSICS:1"

    # The same page must not feed the chemistry form.
    theirs, their_stats = build_questions(
        collected, {"PHYSICS:1": "2"}, source_id="s", form_code="CHEMISTRY_JA",
        stable_id=_stable_id)
    assert theirs == []
    assert their_stats["other_form"] == 1


def test_boxed_slot_is_preferred_over_the_printed_question_number(tmp_path):
    """理科 renumbers 問N per 大題; the boxed 解答欄 number is authoritative."""
    physics = READING_PAGE.replace("読解", "物理")
    collected = collect_questions(_write_cache(tmp_path, {1: physics}))
    collected[0]["boxed_slot"] = "8"      # 問1 of the second 大題 sits at slot 8
    questions, stats = build_questions(
        collected, {"PHYSICS:8": "3", "PHYSICS:1": "1"}, source_id="s",
        form_code="PHYSICS_JA", stable_id=_stable_id)
    assert stats["emitted"] == 1
    assert questions[0]["answerRef"] == "PHYSICS:8"
    assert questions[0]["correctAnswer"] == {"optionKey": "3"}
