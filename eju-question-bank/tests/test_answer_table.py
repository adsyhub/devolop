"""The HTML answer table must keep merged cells and refuse to misalign labels."""
from eju_bank.ocr.answer_table import (
    parse_answer_tables, slots_by_label, to_answer_refs,
)

# Verbatim from GLM-OCR on work/2002-1-science answer key page 2. The header
# spans are what OCR produced, including its over-estimated group colspans.
SCIENCE_HTML = """<table>
<tr><td>〈理科〉</td></tr>
<tr><td>物理</td></tr>
<tr><td rowspan="3">問</td><td colspan="5">Ⅰ</td><td colspan="5">Ⅱ</td><td colspan="5">Ⅲ</td></tr>
<tr><td>問1</td><td>問2</td><td>問3</td><td>問4</td><td>問5</td>
    <td colspan="2">A</td><td colspan="2">B</td><td colspan="2">A</td><td colspan="2">B</td></tr>
<tr><td>解答欄</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td>
    <td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td></tr>
<tr><td>答</td><td>3*</td><td>3</td><td>5</td><td>5</td><td>2</td><td>2</td><td>3</td>
    <td>3</td><td>5</td><td>3</td><td>2</td><td>1</td><td>3</td></tr>
</table>"""


def test_reads_every_slot_with_its_printed_answer():
    refs = to_answer_refs(parse_answer_tables(SCIENCE_HTML))
    # 解答欄 1..13 -> 答 3* 3 5 5 2 2 3 3 5 3 2 1 3, footnote marker stripped.
    assert refs["PHYSICS:1"] == "3"
    assert refs["PHYSICS:5"] == "2"
    assert refs["PHYSICS:13"] == "3"
    assert len(refs) == 13


def test_a_question_may_own_several_slots():
    entries = parse_answer_tables(SCIENCE_HTML)["entries"]
    by_label = {(e["label"], tuple(e["slots"])) for e in entries}
    assert ("問1", ("1",)) in by_label
    # 「A」 is printed with colspan=2, so it owns two 解答欄.
    assert ("A", ("6", "7")) in by_label
    assert ("B", ("12", "13")) in by_label


def test_unalignable_header_is_reported_not_applied():
    parsed = parse_answer_tables(SCIENCE_HTML)
    # OCR gave the group row 15 columns for 13 slots; it must not be used.
    assert any("表头行与解答欄列数不一致" in p for p in parsed["problems"])
    assert all(e["group"] is None for e in parsed["entries"])


def test_section_heading_is_picked_up():
    parsed = parse_answer_tables(SCIENCE_HTML)
    assert {e["section"] for e in parsed["entries"]} == {"物理"}
    assert slots_by_label(parsed)[("物理", "問2")] == ["2"]


def test_answer_row_shorter_than_slot_row_is_refused():
    html = ("<table><tr><td>読解</td></tr>"
            "<tr><td>解答欄</td><td>1</td><td>2</td><td>3</td></tr>"
            "<tr><td>答</td><td>1</td><td>3</td></tr></table>")
    parsed = parse_answer_tables(html)
    assert parsed["entries"] == []
    assert any("不匹配" in p for p in parsed["problems"])


def test_unrecognised_section_drops_its_answers():
    html = ("<table><tr><td>謎の科目</td></tr>"
            "<tr><td>解答欄</td><td>1</td></tr>"
            "<tr><td>答</td><td>4</td></tr></table>")
    parsed = parse_answer_tables(html)
    assert parsed["entries"][0]["answers"] == ["4"]
    assert to_answer_refs(parsed) == {}


def test_empty_input_is_safe():
    assert parse_answer_tables("") == {"entries": [], "problems": []}
    assert to_answer_refs({"entries": []}) == {}


def test_ocr_confusing_the_label_character_still_reads_the_row():
    """OCR renders 「解答欄」 as 「解答桐」 on some scans; the row is still the row."""
    html = ("<table><tr><td>物理</td></tr>"
            "<tr><td>解答桐</td><td>1</td><td>2</td></tr>"
            "<tr><td>答</td><td>3</td><td>5</td></tr></table>")
    refs = to_answer_refs(parse_answer_tables(html))
    assert refs == {"PHYSICS:1": "3", "PHYSICS:2": "5"}


COLUMN_HTML = """<table border="1">
<thead><tr><th colspan="3">読解</th></tr>
<tr><th colspan="2">問</th><th>解答番号</th><th>正解</th></tr></thead>
<tbody>
<tr><td colspan="2">Ⅰ</td><td>1</td><td>2</td></tr>
<tr><td colspan="2">Ⅱ</td><td>2</td><td>3</td></tr>
<tr><th colspan="3">聴読解</th></tr>
<tr><th colspan="2">問</th><th>解答番号</th><th>正解</th></tr>
<tr><td colspan="2">1番</td><td>1</td><td>4</td></tr>
<tr><td colspan="2">2番</td><td>2</td><td>1</td></tr>
</tbody></table>"""


def test_reads_the_column_oriented_key_used_from_2009():
    """From 2009 the key prints one question per row: 問 / 解答番号 / 正解."""
    refs = to_answer_refs(parse_answer_tables(COLUMN_HTML))
    assert refs["READING:1"] == "2"
    assert refs["READING:2"] == "3"


def test_each_section_on_a_page_keeps_its_own_slots():
    """読解 and 聴読解 both number from 1; one must not overwrite the other."""
    refs = to_answer_refs(parse_answer_tables(COLUMN_HTML))
    assert refs["READING:1"] == "2"
    assert refs["LISTENING_COMPREHENSION:1"] == "4"
    assert refs["LISTENING_COMPREHENSION:2"] == "1"


def test_continuation_rows_missing_their_tr_are_still_read():
    """OCR emits a run of <td> with no opening <tr>; browsers recover, so do we."""
    html = ("<table><tr><td>物理</td></tr>"
            "<tr><th>問</th><th>解答番号</th><th>正解</th></tr>"
            "<tr><td>問 1</td><td>1</td><td>3</td></tr>"
            "<td>問 2</td><td>2</td><td>5</td></tr></table>")
    refs = to_answer_refs(parse_answer_tables(html))
    assert refs == {"PHYSICS:1": "3", "PHYSICS:2": "5"}
