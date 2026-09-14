"""The answer-key parser must read real 正解表 rows and refuse to guess."""
from eju_bank.ocr.answer_key import parse_answer_key, to_answer_refs

# Trimmed from the OCR of work/2002-1-japanese/answer_ocr/p0002.json.
REAL_PAGE = """平成14年度(2002年度)日本留学試験(第1回)試験問題 正解表

〈日本語〉

聴解

問 1番 2番 3番 4番 5番
答 2 4 4 4 2

読解

問 1 問2 問3 問4 問5
答 1 3 4 1 1

〈理科〉

物理

解答欄 1 2 3 4 5
答 3* 3 5 5 2
"""


def test_pairs_header_and_answer_rows():
    parsed = parse_answer_key(REAL_PAGE)
    assert parsed["problems"] == []
    assert parsed["sections"]["聴解"] == {"1": "2", "2": "4", "3": "4", "4": "4", "5": "2"}
    assert parsed["sections"]["読解"]["1"] == "1"
    assert parsed["sections"]["読解"]["3"] == "4"
    # A footnote marker on a printed answer must not change the answer.
    assert parsed["sections"]["物理"]["1"] == "3"


def test_maps_sections_to_answer_refs():
    refs = to_answer_refs(parse_answer_key(REAL_PAGE))
    assert refs["LISTENING:1"] == "2"
    assert refs["READING:4"] == "1"
    assert refs["PHYSICS:5"] == "2"


def test_mismatched_row_is_reported_not_guessed():
    """Four question numbers with three answers means the table was misread."""
    parsed = parse_answer_key("読解\n問 1 問2 問3 問4\n答 1 3 4\n")
    assert parsed["sections"] == {}
    assert len(parsed["problems"]) == 1
    assert "不匹配" in parsed["problems"][0]


def test_answer_row_without_header_is_reported():
    parsed = parse_answer_key("読解\n答 1 3 4 1\n")
    assert parsed["sections"] == {}
    assert parsed["problems"]


def test_unknown_section_is_not_assigned_to_a_guessed_form():
    parsed = parse_answer_key("謎の科目\n問 1 問2\n答 3 4\n")
    assert parsed["sections"]["謎の科目"] == {"1": "3", "2": "4"}
    assert to_answer_refs(parsed) == {}


def test_spaced_subject_heading_is_recognised():
    """The printed key typesets two-character subjects as 「化 学」「生 物」."""
    parsed = parse_answer_key("化 学\n解答欄 1 2 3\n答 4 2 6\n生 物\n解答欄 1 2\n答 3 1\n")
    refs = to_answer_refs(parsed)
    assert refs["CHEMISTRY:1"] == "4"
    assert refs["CHEMISTRY:3"] == "6"
    assert refs["BIOLOGY:2"] == "1"


def test_ocr_confusing_the_label_characters_still_reads_the_rows():
    """Scans render 「解答欄」 as 「解答桐」 and 「問」 as 「间」."""
    parsed = parse_answer_key("物理\n解答桐 1 2 3\n答 3 5 2\n")
    assert to_answer_refs(parsed) == {"PHYSICS:1": "3", "PHYSICS:2": "5", "PHYSICS:3": "2"}
    spaced = parse_answer_key("読解\n间 問1 問2\n答 1 4\n")
    assert to_answer_refs(spaced) == {"READING:1": "1", "READING:2": "4"}
