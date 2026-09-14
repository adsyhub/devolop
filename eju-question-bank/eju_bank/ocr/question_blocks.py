"""Segment one OCR'd exam page into question blocks.

Grounded in the two option layouts that actually occur in this project's OCR
output (surveyed over the cached pages under ``work/*/ocr_cache``):

* ``$\\textcircled{1}$ 野菜の値段が…``  — circled numbers rendered as LaTeX
  (総合科目 / 理科 booklets)
* ``1. 優れた個人が…``                  — plain numbered lines (日本語 booklets)

Both are recognised. A block is only reported as a question when its stem
carries an explicit selection instruction, which is what keeps front-matter
pages ("1. 解答は，解答用紙に鉛筆（HB）で記入してください。") from being read as
a four-option question.

Nothing here invents content: a page with no recognisable question yields an
empty list, and a block whose options are not a complete 1..N run is dropped.
"""

from __future__ import annotations

import re
from typing import Any

# 「…の中から1つ選びなさい。14」— the trailing number is the answer-sheet slot
# (解答欄), which is the reliable join key against the printed 正解表.
_SELECT_PHRASES = (
    "選びなさい", "選べ", "選んで", "答えなさい", "答えはどれ", "どれですか",
    "最も適当", "最も適切", "正しいもの", "不適切なもの",
)
# 日本語の読解は「筆者は何が一番大切だと言っていますか。」のように、
# 「選びなさい」を書かずに疑問文で終わることが多い。設問の頭（問N）が
# 付いている塊に限って、疑問文もそのまま設問として受け入れる。
_INTERROGATIVE = re.compile(r"(?:か|ですか|ますか)\s*[。\.]?\s*$")

_QUESTION_HEAD = re.compile(r"^問\s*([0-9]{1,2})[\.\s、]*(.*)$")
_SUBQUESTION_HEAD = re.compile(r"^[\(（]\s*([0-9]{1,2})\s*[\)）]\s*(.*)$")
# 「…の中から一つ選びなさい。 1 N」— 解答欄号后面常常还印着答案的单位（N, m, J,
# hPa, kg·m/s, ℃, %）。原来的式子要求数字落在字符串末尾，于是带单位的那一批
# 全都读不出欄号，只能退回到页边数字的连号推定（见 assemble_from_ocr）。单位是
# 一小段拉丁字母/记号，不含日文，这一点足以把它与正文分开。
# 单位必须以非数字开头，否则「。 1 2」会被读成「欄号 1、单位 2」。
_UNIT = r"[A-Za-z°℃%％Ωμµ\$\\][A-Za-z°℃%％Ωμµ·/\^\-0-9\s\{\}\$\\]{0,15}"
_SLOT_TAIL = re.compile(rf"(?:。|\.)\s*([0-9]{{1,3}})\s*(?:{_UNIT})?$")
# 「化学の問題はこれで終わりです。解答欄の21～75は空欄のままにしてください。」
# 这类结束声明印在最后一题的选项之后，会被当成正文续到最后一个选项里。
_END_DECLARATION = re.compile(
    r"(?:問題はこれで終わり|の問題はこれで|解答欄の\s*[0-9]+\s*[～~〜]\s*[0-9]+"
    r"|解答欄\s*[A-Z]\s*[～~〜]\s*[A-Z]\s*は空欄)")
# 版心页码印成「-62-」或「理科一2」。裸的「5」也曾按同一条规则丢掉，但它同样是
# 解答欄号印在题干下面的样子（問5 … / 5 / 选项表）。两者靠形状分不开，所以裸数字
# 留到 parse_page 按上下文判断：题干说了「選びなさい」而选项还没出现的位置，就是
# 答案框的位置（审计 F18）。
_FOOTER = re.compile(
    r"^(?:[-ー―\s]+[0-9]{1,3}[-ー―\s]*|[-ー―\s]*[0-9]{1,3}[-ー―\s]+"
    r"|(?:日本語|総合科目|理科|数学|物理|化学|生物)\s*[-ー―一]\s*[0-9]{1,3}\s*)$"
)
_BARE_NUMBER = re.compile(r"^[0-9]{1,3}$")
_FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


# 表格按它自己的内部结构吃：一段段 thead/tbody，或裸的 tr。`</table>` 常常缺失
# （OCR 只给到 `</tbody>` 就接着排正文），所以它是可选的 —— 但不能因此一路吃到
# 文末，那会把表格后面的下一道题吞掉。一个 <table> 里出现两组 thead+tbody 也见过
# （题干表和选项表被并成一个元素），重复组把它们一并收进来。
_HTML_TABLE = re.compile(
    r"<table\b[^>]*>"
    r"(?:\s*<(?:thead|tbody)\b.*?</(?:thead|tbody)>|\s*<tr\b.*?</tr>)*"
    r"\s*(?:</table>)?", re.I | re.S)
_HTML_ROW = re.compile(r"<tr\b[^>]*>(.*?)(?:</tr>|(?=<tr\b)|$)", re.I | re.S)
_HTML_CELL = re.compile(r"<(t[dh])\b([^>]*)>(.*?)(?:</\1>|(?=<t[dh]\b)|$)", re.I | re.S)
_HTML_TAG = re.compile(r"<[^>]*>")
_HTML_SPAN = re.compile(r"\b(rowspan|colspan)\s*=\s*\"?([0-9]{1,2})\"?", re.I)

# 二维比较表也会以 LaTeX 数组印出来，选项圈号排在表头那一行：
#   \begin{array}{c|c|c|c|c} \hline ⟦1⟧ & ⟦2⟧ & ⟦3⟧ & ⟦4⟧ \\ \hline
#   \frac{f_1}{f_0} & \sqrt{...} & ... \end{array}
# 原来它整块落进正文，于是四个选项各自只剩一个 `&`，全部数值挤进最后一个选项。
_LATEX_TABLE = re.compile(
    r"\$?\$?\s*\\begin\{(array|tabular)\}\s*(?:\{[^{}]*\})?(.*?)\\end\{\1\}\s*\$?\$?",
    re.S)
_LATEX_RULE = re.compile(r"\\(?:hline|toprule|midrule|bottomrule|cline\{[^}]*\})")
_LATEX_COMMAND = re.compile(r"\\[A-Za-z]+")


def _cell_text(value: str) -> str:
    """A table cell reduced to one line, with ``|`` dropped so rows stay parsable."""
    return " ".join(str(value).replace("|", " ").split())


def _html_table_rows(block: str) -> list[list[dict[str, Any]]]:
    """One OCR'd HTML table as structured rows.

    The header flag and the row/column spans are kept, because a comparison grid
    without its column names is a bare list of numbers: 案例 E 的人口/GDP/貿易額
    三列，去掉表头就没人知道 128 是什么。They travel with the cell rather than as
    a separate header row so a two-row ``<thead>`` survives intact.
    """
    rows: list[list[dict[str, Any]]] = []
    for row in _HTML_ROW.finditer(block):
        cells: list[dict[str, Any]] = []
        for tag, attrs, body in _HTML_CELL.findall(row.group(1)):
            cell: dict[str, Any] = {"value": _cell_text(_HTML_TAG.sub("", body))}
            if tag.lower() == "th":
                cell["header"] = True
            for name, number in _HTML_SPAN.findall(attrs or ""):
                span = int(number)
                if span > 1:
                    cell[name.lower()] = span
            cells.append(cell)
        if cells:
            rows.append(cells)
    return rows


def _latex_table_rows(body: str) -> list[list[dict[str, Any]]]:
    """One LaTeX ``array``/``tabular`` body as structured rows.

    A cell that still carries a LaTeX command is wrapped back into ``$…$`` so the
    downstream AST builder can turn it into a real formula instead of shipping
    ``\\sqrt{\\frac{2}{3}}`` as prose.
    """
    rows: list[list[dict[str, Any]]] = []
    for raw_row in re.split(r"\\\\", _LATEX_RULE.sub(" ", body)):
        cells = [_cell_text(cell) for cell in raw_row.split("&")]
        if not any(cells):
            continue
        rows.append([{"value": f"${c}$" if _LATEX_COMMAND.search(c) else c}
                     for c in cells])
    return rows


def _rows_to_pipes(rows: list[list[dict[str, Any]]]) -> list[str]:
    return ["| " + " | ".join(c["value"] for c in row) + " |" for row in rows]


def _normalise(raw: str, tables: dict[tuple[str, ...], list] | None = None) -> list[str]:
    """One list of page lines with option markers reduced to a single form.

    Tables are rewritten as Markdown pipe rows so everything downstream — the
    option reader and the verbatim-OCR check alike — sees one shape. When
    ``tables`` is given, the structured form of each table is recorded there
    under its pipe rows, so the caller can rebuild a real ``table`` node instead
    of flattening the grid into prose.
    """
    text = raw.replace("　", " ")
    # $\textcircled{3}$ / \textcircled{3} / ③  ->  ⟦3⟧
    text = re.sub(r"\$?\\textcircled\s*\{\s*([0-9])\s*\}\$?", r"⟦\1⟧", text)
    for index, glyph in enumerate("①②③④⑤⑥⑦⑧⑨", start=1):
        text = text.replace(glyph, f"⟦{index}⟧")

    def replace(rows: list[list[dict[str, Any]]]) -> str:
        pipes = _rows_to_pipes(rows)
        if not pipes:
            return " "
        if tables is not None:
            tables[tuple(pipes)] = rows
        return "\n" + "\n".join(pipes) + "\n"

    text = _HTML_TABLE.sub(lambda m: replace(_html_table_rows(m.group(0))), text)
    text = _LATEX_TABLE.sub(lambda m: replace(_latex_table_rows(m.group(2))), text)
    lines = []
    for line in text.splitlines():
        line = line.translate(_FULLWIDTH_DIGITS).strip()
        if not line or line in {"$", "$$"} or _FOOTER.match(line):
            continue
        lines.append(line)
    return lines


_MARKER = re.compile(r"^⟦([0-9])⟧\s*(.*)$")
_PLAIN_MARKER = re.compile(r"^([0-9])\s*[\.、]\s*(.+)$")


def _option_marker(line: str) -> tuple[str, str] | None:
    match = _MARKER.match(line)
    if match:
        return match.group(1), match.group(2).strip()
    match = _PLAIN_MARKER.match(line)
    if match:
        return match.group(1), match.group(2).strip()
    return None


_TABLE_SEPARATOR = re.compile(r"^\|[\s:\-|]+\|$")


def _table_cells(line: str) -> list[str] | None:
    """The cells of a Markdown-style table row, or None if this is not one.

    The OCR renders 総合科目 comparison options as a table: a header naming the
    columns, then one row per choice. Recognising the row shape is what lets
    those questions be read at all — treated as prose they carry no options and
    the whole question is dropped.
    """
    text = line.strip()
    if not (text.startswith("|") and text.endswith("|")) or len(text) < 3:
        return None
    if _TABLE_SEPARATOR.match(text):
        return []
    return [cell.strip() for cell in text[1:-1].split("|")]


def _labelled(header: list[str], cells: list[str]) -> tuple[str, str | None]:
    """Render one option row under its column names, or say why it cannot be.

    ``| ⟦3⟧ | 日本 | ドイツ |`` under ``| | A | B |`` reads as ``A 日本　B ドイツ``.
    Dropping the header would leave a bare list of country names with nothing
    saying which column each belongs to, which is the whole content of the
    question.

    Cell 0 holds the option marker, so the header's cell 0 names no column and
    has to be blank. When it is not — 案例 D 的 ``| p | q |`` 配 ``| ⟦1⟧ | 2 |``
    —— 原表的 ``p`` 列根本没有被读出来，圈号占了它的位置，剩下的值会被安到错的
    列名下面，六个选项于是变成三对重复的 ``q 2``。那种行不能当作可用选项，返回
    缺陷说明，由调用方拒收整道题。
    """
    values = cells[1:]
    joined = "　".join(v for v in values if v)
    if not header:
        return joined, None
    if len(header) != len(cells):
        return joined, f"选项行有 {len(cells)} 格，表头有 {len(header)} 列，对不上"
    if header[0]:
        return joined, (f"表头第一列名为「{header[0]}」，但这一列被选项圈号占用，"
                        "原表至少有一列没有读出来")
    return ("　".join(f"{label} {value}".strip()
                      for label, value in zip(header[1:], values)
                      if label or value), None)


def _split_inline_markers(line: str) -> list[str]:
    """A page may print several options on one line; split before each ⟦n⟧."""
    if line.count("⟦") <= 1:
        return [line]
    parts = re.split(r"(?=⟦[0-9]⟧)", line)
    return [p.strip() for p in parts if p.strip()]


def _marker_row(cells: list[str]) -> list[str] | None:
    """The option keys of a row that is nothing but option markers, else None.

    A comparison grid printed the other way round puts ⟦1⟧…⟦4⟧ along the top and
    one row per compared quantity underneath. Read as an ordinary option row it
    produces four options, the first holding the rest of the header and the last
    swallowing every value on the page — 案例 C.
    """
    filled = [c for c in cells if c]
    if len(filled) < 2:
        return None
    keys = []
    for cell in filled:
        match = _MARKER.fullmatch(cell)
        if not match or match.group(2).strip():
            return None
        keys.append(match.group(1))
    return keys if keys == [str(n) for n in range(1, len(keys) + 1)] else None


def _read_horizontal_options(block: dict[str, Any] | None, keys: list[str],
                             rows: list[list[str]]) -> None:
    """Turn a transposed candidate grid into one option per column.

    Each following row is one compared quantity: an optional row name, then one
    value per option. ``f₁/f₀ √(2/3)　A₁/A₀ 2/3`` is option ①. A row whose value
    count does not match the number of options is a row that was not read whole,
    and a candidate assembled from it would be a guess — so the mismatch is
    recorded as a defect instead.
    """
    if block is None:
        return
    columns: dict[str, list[str]] = {key: [] for key in keys}
    cells_seen: dict[str, list[str]] = {key: [] for key in keys}
    for row in rows:
        values = row[-len(keys):] if len(row) >= len(keys) else []
        name = " ".join(row[: len(row) - len(values)]).strip()
        if len(values) != len(keys):
            block.setdefault("defects", []).append(
                f"横向候选表的「{name or '某一行'}」行读到 {len(row)} 格，"
                f"与 {len(keys)} 个候选对不上")
            continue
        for key, value in zip(keys, values):
            if value:
                columns[key].append(f"{name} {value}".strip() if name else value)
                cells_seen[key].append(value)
    for key in keys:
        if columns[key]:
            block["options"][key] = "　".join(columns[key])
            block.setdefault("option_cells", {})[key] = cells_seen[key]


_CJK = re.compile(r"[　-ヿ㐀-䶿一-鿿＀-￯]")


def _join_lines(lines: list[str]) -> str:
    """Join OCR lines without inserting a space inside a wrapped Japanese word.

    The booklet hard-wraps mid-word — ``…に答えなさ`` / ``い。ただし…`` — and joining
    on a blank turned every wrap into ``答えなさ い。``. Latin text still needs the
    space, so the separator is decided by the characters actually meeting.
    """
    out = ""
    for line in lines:
        if not line:
            continue
        if out and not (_CJK.search(out[-1]) and _CJK.search(line[0])):
            out += " "
        out += line
    return out


_CIRCLED = "①②③④⑤⑥⑦⑧⑨"


def _restore(text: str) -> str:
    """Put the readable circled glyphs back after internal normalisation."""
    return re.sub(r"⟦([0-9])⟧", lambda m: _CIRCLED[int(m.group(1)) - 1], text)

def canonical_text(raw: str) -> str:
    """Page text reduced to the single form this parser reads stems in.

    Stems are built from :func:`_normalise` output and handed back through
    :func:`_restore`, so a stem is never a byte-for-byte substring of the raw
    OCR capture — ``$\\textcircled{1}$`` has become ``①`` along the way. Anything
    wanting to check that a stem really came from a page has to compare in this
    same form, which is what this exposes.
    """
    return _restore(" ".join(_normalise(raw)))


def _restore_parts(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Readable copies of ordered stem/material parts, circled glyphs restored."""
    out: list[dict[str, Any]] = []
    for part in parts:
        if part["type"] == "table":
            out.append({"type": "table",
                        "rows": [[{**cell, "value": _restore(cell["value"])} for cell in row]
                                 for row in part["rows"]]})
        elif part["value"].strip():
            out.append({"type": "text", "value": _restore(part["value"])})
    return out


def _duplicate_options(options: dict[str, str]) -> str | None:
    """Are two choices indistinguishable as stored? Then one of them is not read.

    A run of options that is complete and correctly numbered still says nothing
    about whether the choices differ. 案例 D 通过了个数检查，因为丢的是文字不是
    选项；40 道题的选项文本完全相同。A choice that is only a stray symbol carries
    no content either, so both shapes are reported here.
    """
    seen: dict[str, str] = {}
    for key, text in options.items():
        stripped = "".join(str(text).split())
        if not stripped or not re.search(r"[0-9A-Za-z぀-鿿]", stripped):
            return f"选项 {key} 没有可读内容（{text.strip()!r}）"
        if stripped in seen:
            return f"选项 {seen[stripped]} 与 {key} 的文本完全相同（{text.strip()!r}）"
        seen[stripped] = key
    return None


def _finish(block: dict[str, Any]) -> dict[str, Any] | None:
    """Turn a raw block into a question, or None when it is not one.

    A question that *is* a question but whose content did not survive reading
    comes back with ``defects`` filled in rather than as ``None``. The two cases
    are not the same and must not be conflated: a page with no question on it is
    accounted for, while a question silently dropped leaves a hole nothing counts
    (审计 F24).
    """
    stem = _join_lines(block["stem_lines"]).strip()
    options: dict[str, str] = block["options"]
    if not stem or not options:
        return None
    if not any(phrase in stem for phrase in _SELECT_PHRASES):
        # 逐句检查是否有疑问句收尾；整段拼接后句尾可能被正文覆盖。
        sentences = [x for x in re.split(r"[。\n]", stem) if x.strip()]
        if not any(_INTERROGATIVE.search(x + "。") for x in sentences):
            return None
    keys = sorted(options, key=int)
    # Options must be a complete run starting at 1; a gap means the page was
    # read incompletely and pairing answers to it would be a guess.
    if keys != [str(n) for n in range(1, len(keys) + 1)] or len(keys) < 2:
        return None

    slot = None
    slot_match = _SLOT_TAIL.search(stem)
    if slot_match:
        slot = slot_match.group(1)
        stem = stem[: slot_match.start()].rstrip() + "。"
    parts = _restore_parts(block.get("stem_parts") or [])
    # 欄号（和它的单位）是版面标记，不是题干的一部分：从最后一段文字里也去掉它。
    if slot_match and parts and parts[-1]["type"] == "text":
        trimmed = _SLOT_TAIL.sub("。", parts[-1]["value"]).strip()
        if trimmed:
            parts[-1] = {"type": "text", "value": trimmed}
        else:
            parts.pop()
    defects = list(block.get("defects") or [])
    if duplicate := _duplicate_options(options):
        defects.append(duplicate)
    return {
        "label": block["label"],
        "number": block["number"],
        "sub": block.get("sub"),
        "slot": slot,
        "stem": _restore(stem),
        "stem_parts": parts,
        "context": _restore(_join_lines(block.get("context") or []).strip()) or None,
        "context_parts": _restore_parts(block.get("context_parts") or []),
        "options": {k: _restore(options[k]) for k in keys},
        "option_cells": {k: [_restore(c) for c in v]
                         for k, v in (block.get("option_cells") or {}).items() if k in options},
        "defects": defects,
        "pages": list(block.get("pages") or []),
        "contextPages": list(block.get("contextPages") or []),
    }


def _is_unfinished(block: dict[str, Any]) -> bool:
    """Does this block read like a question whose options are still to come?

    A 問 whose stem asks the reader to choose but whose options are absent, or
    stop short of a complete 1..N run, is a question continued on the next page.
    Today it is simply dropped — :func:`_finish` refuses an incomplete option run
    — and with it goes the printed 解答欄 that would have joined its section.
    """
    stem = _join_lines(block.get("stem_lines") or []).strip()
    if not stem or not any(phrase in stem for phrase in _SELECT_PHRASES):
        return False
    keys = sorted(block.get("options") or {}, key=int)
    return keys != [str(n) for n in range(1, len(keys) + 1)] or len(keys) < 2


def parse_page(raw_text: str, *, carry: dict[str, Any] | None = None,
               page: int | None = None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Every question this page states outright, plus what is still open.

    Returns ``(questions, carry)``. The carry holds a block whose options had not
    arrived by the end of the page (``block``) and the 問 whose sub-questions are
    still running (``parentNumber`` / ``parentContext``); pass it back in for the
    next page. A carried block the next page does not continue is dropped exactly
    as before.
    """
    tables: dict[tuple[str, ...], list] = {}
    lines = _normalise(raw_text or "", tables)
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    last_key: str | None = None
    # 上一页交下来的状态：可能有一个未闭合的块，也可能只是一个还在管辖范围内的
    # 父级题号（「問7 …下の問い(1)～(3)に答えなさい」的 (1) 在上一页就闭合了，
    # (2) 落到这一页）。父级丢了不只是题号变成「問?」—— 那段本该共用的文章也会
    # 跟着丢，子问就成了无法作答的题。
    parent_number: str | None = (carry or {}).get("parentNumber")
    parent_context: list[str] = list((carry or {}).get("parentContext") or [])
    # 共用材料印在父題那一页，子問可能落到下一页。记住材料出自哪些页，
    # 否则"这些字确实印在这些页上"的核对会在错的页面上做。
    parent_pages: list[int] = list((carry or {}).get("parentPages") or [])
    pending = (carry or {}).get("block")
    if pending:
        # 这一页开头接着印选项，或者接着印子问 (N)，都算续上；
        # 否则按老规矩当它不是题目。
        opener = next((x for x in lines if x), None)
        probe = (_table_cells(opener) or [None])[0] if opener and _table_cells(opener) else opener
        continues = bool(probe) and bool(_option_marker(probe) or _SUBQUESTION_HEAD.match(probe))
        if continues:
            current = pending
            last_key = (max(pending.get("options") or {"0": ""}, key=int)
                        if pending.get("options") else None)
            if pending.get("number"):
                parent_number = pending["number"]
            if pending.get("sub") is None and not pending.get("options"):
                parent_context = list(pending.get("stem_lines") or [])
                parent_pages = [int(n) for n in (pending.get("pages") or []) if n]
            elif pending.get("context"):
                parent_context = list(pending["context"])
                parent_pages = [int(n) for n in (pending.get("contextPages") or []) if n]
        else:
            blocks.append(pending)
    # 「問7 次の文章を読み，下の問い(1),(2)に答えなさい。」+ 一段共用文章，
    # 后面跟 (1) (2) 各自的选项。那段文章是子问共用的材料，不是某一问的题干。

    def flush() -> None:
        nonlocal current, last_key
        if current:
            blocks.append(current)
        current = None
        last_key = None

    def start(number: str | None, sub: str | None, rest: str, context: list[str],
              context_pages: list[int] | None = None,
              context_parts: list[dict[str, Any]] | None = None) -> None:
        nonlocal current, last_key
        flush()
        label = f"問{number}" if number else "問?"
        if sub:
            label += f"({sub})"
        current = {
            "label": label, "number": number, "sub": sub,
            "stem_lines": [rest] if rest else [],
            "stem_parts": [{"type": "text", "value": rest}] if rest else [],
            "options": {}, "option_cells": {}, "defects": [],
            "context": list(context), "context_parts": list(context_parts or []),
            "pages": [page] if page else [],
            "contextPages": list(context_pages or ([page] if page and context else [])),
        }
        last_key = None

    # 一段表格的行先攒着，因为它是什么要看后面跟什么：跟选项行就是选项表的表头，
    # 不跟就是题干里的数据表。原来第二种情况被当成表头覆盖掉，案例 E 的人口、
    # GDP、貿易額整张表就是这样消失的（审计 F08）。
    buffered: list[list[str]] = []
    # 这一页第一个 問N 之前的正文。理科题册把「A 次の図のように，長さ1.2m，
    # 重さ10Nの…糸2の張力は20Nであった」印在 問1 前面，那是这道题的全部已知条件；
    # 原来 current is None 时整段被丢掉，题目就只剩「Wは何Nか」（审计 F02）。
    preamble: list[str] = []
    preamble_parts: list[dict[str, Any]] = []

    def flush_table() -> None:
        """A buffered table nobody claimed as option headings is stem content."""
        nonlocal buffered
        if not buffered:
            return
        pipes = ["| " + " | ".join(row) + " |" for row in buffered]
        rows = tables.get(tuple(pipes)) or [[{"value": c} for c in row] for row in buffered]
        target_lines, target_parts = ((current["stem_lines"], current["stem_parts"])
                                      if current is not None else (preamble, preamble_parts))
        target_lines.extend(pipes)
        target_parts.append({"type": "table", "rows": rows})
        buffered = []

    def add_text(line: str) -> None:
        target_lines, target_parts = ((current["stem_lines"], current["stem_parts"])
                                      if current is not None else (preamble, preamble_parts))
        target_lines.append(line)
        target_parts.append({"type": "text", "value": line})

    # 横向候选表正在累积时，后面的行是它的数值行，不是新的表格。
    horizontal: list[str] | None = None

    def close_horizontal() -> None:
        nonlocal horizontal, buffered, last_key
        if horizontal is None:
            return
        _read_horizontal_options(current, horizontal, buffered)
        horizontal, buffered, last_key = None, [], None

    for line in lines:
        cells = _table_cells(line)
        if cells is not None:
            if not cells:
                continue                      # 分隔行 |:---|:---|
            keys = _marker_row(cells)
            if keys and current is not None:
                # 圈号自己排成一行：这是横向候选表的表头，下面几行才是每个候选的
                # 取值（案例 C）。原来它走的是纵向分支，四个选项各自只剩一个 `&`。
                close_horizontal()
                flush_table()
                horizontal, buffered = keys, []
                continue
            if horizontal is not None:
                buffered.append(cells)
                continue
            marker = _option_marker(cells[0]) if cells[0] else None
            if marker and current is not None:
                # 表头只可能是紧挨着的一两行列名。攒了更多行的，是题干数据表，
                # 先把它交给题干，选项不借用它的列名。
                if len(buffered) > 2:
                    flush_table()
                header = buffered[-1] if buffered else []
                key, inline = marker
                rest, defect = _labelled(header, cells)
                text = " ".join(x for x in (inline, rest) if x)
                current["options"][key] = text
                if defect:
                    current.setdefault("defects", []).append(f"选项 {key}：{defect}")
                # 表格型选项的文本是把读到的格子按列名排好的，整串不会原样出现在
                # 页面文本里。把格子本身留下来，想核对"这些字确实印在这页上"才有依据。
                current.setdefault("option_cells", {})[key] = [
                    c for c in ([inline] + list(cells[1:])) if c]
                last_key = key
            else:
                buffered.append(cells)
            continue

        close_horizontal()
        flush_table()

        if _END_DECLARATION.search(line):
            # 「化学の問題はこれで終わりです。解答欄の21～75は…」这类结束声明印在
            # 最后一题的选项之后，原来会被续进最后一个选项里（审计 F16）。
            flush()
            continue

        head = _QUESTION_HEAD.match(line)
        if head and not _option_marker(line):
            parent_number = head.group(1)
            parent_context = []
            start(parent_number, None, head.group(2), list(preamble),
                  [page] if page and preamble else [], list(preamble_parts))
            preamble, preamble_parts = [], []
            continue

        sub = _SUBQUESTION_HEAD.match(line)
        if sub:
            # 第一个子问出现时，父级块里累积的文字是共用材料。
            if current and current["sub"] is None and not current["options"]:
                parent_context = list(current["stem_lines"])
                parent_pages = [int(n) for n in (current.get("pages") or []) if n]
                parent_context_parts = list(current.get("stem_parts") or [])
            else:
                parent_context_parts = None
            start(parent_number, sub.group(1), sub.group(2),
                  parent_context or list(preamble), parent_pages or ([page] if page else []),
                  parent_context_parts if parent_context else list(preamble_parts))
            if not parent_context:
                preamble, preamble_parts = [], []
            continue

        if _BARE_NUMBER.match(line):
            # 解答欄号印在题干与选项之间；同样形状的页码印在别处。只在"题干已经
            # 要求作答、选项还没开始"这一个位置上收下它，其余一律当页码丢掉。
            if (current is not None and not current["options"]
                    and any(p in _join_lines(current["stem_lines"]) for p in _SELECT_PHRASES)):
                add_text(line)
            continue

        for piece in _split_inline_markers(line):
            marker = _option_marker(piece)
            if marker and current is not None:
                key, text = marker
                current["options"][key] = text
                last_key = key
            elif last_key is not None and current is not None:
                current["options"][last_key] += " " + piece
            else:
                add_text(piece)

    close_horizontal()
    flush_table()

    if current is not None and page and page not in (current.get("pages") or []):
        current.setdefault("pages", []).append(page)
    tail = current if current is not None and _is_unfinished(current) else None
    if tail is None:
        flush()
    else:
        current = None
    state = {"block": tail, "parentNumber": parent_number, "parentContext": parent_context,
             "parentPages": parent_pages}
    if tail is None and parent_number is None:
        state = None
    return [q for q in (_finish(b) for b in blocks) if q], state


def parse_questions(raw_text: str) -> list[dict[str, Any]]:
    """One page on its own — the questions it completes, nothing carried over."""
    questions, _ = parse_page(raw_text)
    return questions
