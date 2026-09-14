"""Mathematics answers are per blank; the letters and digits must line up."""
from eju_bank.ocr.math_answers import parse_math_answers, slots_for, to_answer_refs

# Trimmed from the OCR of a 2015 answer key. 「I 2」 is the blank I, not 大題 I.
REAL = """<数 学> Mathematics

コース1 Course 1
問Q. 解答番号 row 正解A.

I 問1 ABCD 5723
EFGH 5435
I 2
問2 JKL 925
MN 25

II 問1 A 1
BC 43
DE -3

III  AB 11
CDEF 2257

コース2 Course 2
問Q. 解答番号 row 正解A.

I 問1 A 9
"""


def test_letters_and_digits_pair_one_for_one():
    parsed = parse_math_answers(REAL)
    first = slots_for(parsed, "MATHEMATICS_COURSE_1", "I", "1")
    assert first == {"A": "5", "B": "7", "C": "2", "D": "3",
                     "E": "5", "F": "4", "G": "3", "H": "5", "I": "2"}


def test_a_minus_sign_occupies_its_own_blank():
    parsed = parse_math_answers(REAL)
    second = slots_for(parsed, "MATHEMATICS_COURSE_1", "II", "1")
    assert second["D"] == "-"
    assert second["E"] == "3"


def test_a_roman_numeral_line_is_told_from_a_blank_row():
    """「I 2」 fills blank I; 「III  AB 11」 opens 大題 III."""
    parsed = parse_math_answers(REAL)
    groups = parsed["courses"]["MATHEMATICS_COURSE_1"]
    assert ("I", "1") in groups and "I" in groups[("I", "1")]
    assert ("III", "") in groups, "a 大題 with no 問 keeps an empty question number"
    assert groups[("III", "")]["A"] == "1"


def test_question_number_resets_with_the_group():
    """Carrying 問2 into 大題 III would put its blanks on the wrong question."""
    groups = parse_math_answers(REAL)["courses"]["MATHEMATICS_COURSE_1"]
    assert ("III", "2") not in groups


def test_courses_are_kept_apart():
    refs = to_answer_refs(parse_math_answers(REAL))
    assert refs["MATHEMATICS_COURSE_1:I:1:A"] == "5"
    assert refs["MATHEMATICS_COURSE_2:I:1:A"] == "9"


def test_a_row_that_does_not_line_up_is_reported_not_split():
    parsed = parse_math_answers("コース1 Course 1\n解答番号 正解\nI 問1 ABC 12\n")
    assert parsed["courses"] == {}
    assert any("不匹配" in p for p in parsed["problems"])


def test_text_without_a_course_heading_yields_nothing():
    assert parse_math_answers("I 問1 ABCD 5723\n")["courses"] == {}
