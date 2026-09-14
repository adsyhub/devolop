"""Read an EJU 正解表 that OCR captured as HTML, keeping the merged cells.

The printed key is a nested table. Flattened to plain text it loses the one
thing the mapping depends on — how many 解答欄 a single question owns::

    <tr><td rowspan="3">問</td><td colspan="5">Ⅰ</td><td colspan="5">Ⅱ</td>…</tr>
    <tr><td>問1</td>…<td>問5</td><td colspan="2">A</td><td colspan="2">B</td>…</tr>
    <tr><td>解答欄</td><td>1</td><td>2</td>…<td>13</td></tr>
    <tr><td>答</td><td>3*</td><td>3</td>…<td>3</td></tr>

Here 問1..問5 take one 解答欄 each while A and B take two apiece. This module
expands rowspan/colspan into a real grid, then reads each 解答欄 column back to
the question label above it, so a question that owns several slots is reported
with all of them.

Nothing is inferred: a table with no 解答欄 row, or whose 答 row does not line
up with it, is reported as a problem instead of being partially guessed.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any

# OCR 常把「欄」认成形近字（实测「解答桐」）。这一行由「解答」开头且后面跟一串
# 数字唯一确定，所以只要求前两字是「解答」，后面最多两个非数字字符。
_SLOT_ROW = re.compile(r"^解答[^0-9]{0,2}$")
_ANSWER_ROW = re.compile(r"^(正解|答)$")
_LABEL_ROW = re.compile(r"^[問问间]$")
_FULLWIDTH = str.maketrans("０１２３４５６７８９", "0123456789")


class _TableCollector(HTMLParser):
    """Collect every <table> as a list of rows of (text, rowspan, colspan)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[tuple[str, int, int]]]] = []
        self._table: list[list[tuple[str, int, int]]] | None = None
        self._row: list[tuple[str, int, int]] | None = None
        self._cell: list[str] | None = None
        self._span = (1, 1)

    @staticmethod
    def _int(attrs: dict[str, str | None], name: str) -> int:
        try:
            value = int(str(attrs.get(name) or 1))
        except (TypeError, ValueError):
            return 1
        return value if 1 <= value <= 64 else 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        mapping = dict(attrs)
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._table is not None:
            # OCR 输出的续行常常缺 <tr>（只给一串 <td> 然后 </tr>）。
            # 浏览器会隐式开一行，不这样做整行会被丢掉。
            if self._row is None:
                self._row = []
            self._cell = []
            self._span = (self._int(mapping, "rowspan"), self._int(mapping, "colspan"))

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            text = "".join(self._cell).replace("　", " ").strip()
            self._row.append((text, self._span[0], self._span[1]))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None


def _expand(rows: list[list[tuple[str, int, int]]]) -> list[list[str]]:
    """Expand rowspan/colspan into a dense grid of cell texts."""
    grid: list[list[str | None]] = []
    for _ in rows:
        grid.append([])
    pending: dict[tuple[int, int], str] = {}

    for r, row in enumerate(rows):
        column = 0
        for text, rowspan, colspan in row:
            while (r, column) in pending:
                _place(grid, r, column, pending.pop((r, column)))
                column += 1
            for dc in range(colspan):
                _place(grid, r, column + dc, text)
                for dr in range(1, rowspan):
                    if r + dr < len(rows):
                        pending[(r + dr, column + dc)] = text
            column += colspan
        # 行末仍有被上一行纵向合并占住的列
        while (r, column) in pending:
            _place(grid, r, column, pending.pop((r, column)))
            column += 1

    width = max((len(line) for line in grid), default=0)
    return [[(cell or "") for cell in line] + [""] * (width - len(line)) for line in grid]


def _place(grid: list[list[str | None]], row: int, column: int, text: str) -> None:
    line = grid[row]
    while len(line) <= column:
        line.append(None)
    if line[column] is None:
        line[column] = text


_COL_SLOT = re.compile(r"解答(?:番号|欄|桐)")
_COL_ANSWER = re.compile(r"正解|^答")


def _heading_in(cells: list[str]) -> str | None:
    """The section this row announces, if it announces one.

    Headings appear wrapped (「〈理 科〉」) and with an English gloss appended
    (「物理 Physics」). A row carrying any digit is data, not a heading.
    """
    from .answer_key import SECTION_PREFIXES

    if not cells or any(ch.isdigit() for cell in cells for ch in cell):
        return None
    for cell in cells:
        compact = re.sub(r"\s+", "", cell).strip("〈〉<>《》")
        for name in sorted(SECTION_PREFIXES, key=len, reverse=True):
            if compact.startswith(name):
                return name
    return None

def _parse_column_layout(
    grid: list[list[str]], default_section: str | None = None
) -> tuple[list[dict[str, Any]], list[str]]:
    """Read the row-per-question 正解表: 問 / 解答番号 / 正解 across one row.

    Its header names three columns and every following row is one question::

        問 Q. | 解答番号 row | 正解 A.
        問 1  |      1      |    3
        問 2  |      2      |    2

    A 大題 that spans several rows prints its numeral once, as a ``rowspan``
    cell, so the expanded grid gives *those* rows one extra leading column and
    the rest none::

        ['II', '問1', '1', '5']     ← first row of the 大題
        ['問3', '3',  '6',  '']     ← later rows

    Reading a fixed column index under that layout is how chemistry answers
    ended up filed as physics: the two shapes disagree by one column, so rows of
    one shape read the neighbouring section's values and, where a section
    boundary fell in between, wrote them under the wrong 解答欄. Every row is
    therefore anchored on its own 問N label and the two numbers that follow it,
    which is what the printed row actually means and cannot drift.
    """
    entries: list[dict[str, Any]] = []
    problems: list[str] = []
    section: str | None = default_section
    in_block = False

    for line in grid:
        cells = [c.strip() for c in line if c.strip()]

        # 一页常常连排几个小节（読解 → 聴読解 → 聴解），每节自带一行表头。
        # 必须按小节分块：否则后面小节的行会被算到前一节，两节欄号都从 1 起，
        # 会互相覆盖 —— 那等于把答案安到别的科目上。
        heading = _heading_in(cells)
        if heading:
            section = heading
            in_block = False
            continue

        has_slot = any(_COL_SLOT.search(c) for c in line)
        has_answer = any(_COL_ANSWER.search(c.strip()) for c in line)
        if has_slot and has_answer:
            in_block = True
            continue
        if not in_block:
            continue

        # 这一行的結構是「[題号格…] 解答番号 正解」。題号格的样子随年份和版式变化
        # （問1 / Ⅰ / 1番 / 空白续行），但末尾那两个纯数字格始终是欄号与正解，
        # 而且与前面有多少格无关 —— 这正是固定列号读错邻节数值的地方。
        cells = [c.translate(_FULLWIDTH).strip() for c in line]
        cells = [c for c in cells if c]
        digits = [(i, c.rstrip("*＊").strip()) for i, c in enumerate(cells)
                  if c.rstrip("*＊").strip().isdigit()]
        if len(digits) < 2:
            continue
        if len(digits) > 2:
            # 多出来的数不知道哪个是欄号哪个是正解，配错就等于判错，直接不采用。
            problems.append(
                f"{section or '(无小节)'} 这一行读到 {len(digits)} 个数，"
                f"无法确定哪个是解答番号、哪个是正解：{cells}")
            continue
        (slot_at, slot), (_, answer) = digits
        label = next((c for c in reversed(cells[:slot_at])
                      if not c.rstrip("*＊").strip().isdigit()), None)
        entries.append({
            "section": section, "group": None,
            "label": label, "slot": slot, "answer": answer,
        })

    # 交回未合并的条目：外层 parse_answer_tables 统一做合并。
    return entries, problems


def assign_sections_by_restart(
    entries: list[dict[str, Any]], order: list[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Re-file row-per-question entries using slot restarts and the printed order.

    A section numbers its 解答番号 from 1 upward, so a row numbered 1 after a
    higher number starts the next section. Only a return to 1 counts: a slot that
    merely repeats or dips (OCR reading 問15 beside 解答番号 14 twice) is noise
    within a section, and treating it as a boundary would manufacture more blocks
    than the page has subjects. Splitting on that and walking the order the flat
    capture reported puts every row under the subject it was printed beneath,
    which heading positions in the structured capture cannot be trusted to do.

    If the number of blocks and the number of printed headings disagree, no
    section is assigned at all: a guess here silently marks a learner wrong.
    """
    if not entries:
        return entries, []
    blocks: list[list[dict[str, Any]]] = [[]]
    previous = 0
    for entry in entries:
        try:
            slot = int(entry["slot"])
        except (TypeError, ValueError):
            continue
        if slot == 1 and previous > 1 and blocks[-1]:
            blocks.append([])
        blocks[-1].append(entry)
        previous = slot
    blocks = [b for b in blocks if b]
    if len(blocks) != len(order):
        return ([{**e, "section": None} for e in entries],
                [f"正解表分出 {len(blocks)} 段，但页面只报出 {len(order)} 个小节标题"
                 f"（{order}）；无法确定哪段属于哪一科，整页不采用。"])
    out: list[dict[str, Any]] = []
    problems: list[str] = []
    for block, name in zip(blocks, order):
        # OCR 偶尔把同一行读两遍。重复而答案一致的，去重即可；答案不一致的那一欄
        # 无从判断哪个是对的，只丢那一欄，不牵连整节。欄号的缺口由下游的
        # 连续前缀校验处理，那里分得清「已解释」和「无法解释」的空缺。
        answers: dict[str, set[str]] = {}
        for entry in block:
            answers.setdefault(str(entry["slot"]), set()).add(str(entry["answer"]))
        conflicting = {slot for slot, values in answers.items() if len(values) > 1}
        if conflicting:
            problems.append(
                f"「{name}」段的解答番号 {sorted(conflicting, key=int)[:6]} 各读到多个不同的正解，"
                "无法判断哪个是印刷值，这些欄不采用。")
        seen: set[str] = set()
        for entry in block:
            slot = str(entry["slot"])
            if slot in conflicting or slot in seen:
                continue
            seen.add(slot)
            out.append({**entry, "section": name})
    return out, problems


def _label_index(line: list[str], pattern: re.Pattern[str], limit: int = 4) -> int | None:
    """Where this row's own label sits. OCR mis-estimates rowspan, so the label
    is not reliably in column 0 — but it is always within the first few cells."""
    for index, cell in enumerate(line[:limit]):
        if pattern.match(cell.translate(_FULLWIDTH).strip()):
            return index
    return None


def headings_in_text(text: str) -> list[str]:
    """Every section heading the plain-text capture announces, in printed order.

    The structured capture cannot be trusted for this. OCR emits the table's
    ``<thead>`` blocks wherever it happens to recognise them — the 化学 heading
    of one real page lands *after* several of chemistry's own rows, and 生物
    never becomes a heading row at all — so splitting the grid on heading
    position files answers under the wrong subject. The flat capture of the same
    page reads top to bottom and states the order plainly.
    """
    order: list[str] = []
    for line in (text or "").splitlines():
        found = _heading_in([line.strip()])
        if found and (not order or order[-1] != found):
            order.append(found)
    return order


def heading_in_text(text: str) -> str | None:
    """The first section heading a plain-text capture of the page announces.

    Some pages print the heading outside the table markup, so the structured
    capture has nothing to attribute its rows to. The flat capture of the same
    page still shows it.
    """
    for line in (text or "").splitlines():
        found = _heading_in([line.strip()])
        if found:
            return found
    return None


def parse_answer_tables(html: str, *, default_section: str | None = None,
                        section_order: list[str] | None = None) -> dict[str, Any]:
    """Return ``{"entries": [...], "problems": [...]}``.

    Each entry is one printed question: ``{"section", "group", "label",
    "slots", "answers"}``, carrying every 解答欄 that question owns.

    The 解答欄 → 答 pairing is authoritative and always reported. A 題号 or 大題
    header is attached only when its cell count verifiably matches the slot
    count; OCR's rowspan/colspan estimates on the merged header cells are not
    dependable, and a misaligned label would put an answer on the wrong
    question. Where it cannot be aligned, the entry keeps the slot number and
    the mismatch is listed in ``problems``.
    """
    collector = _TableCollector()
    collector.feed(html or "")
    entries: list[dict[str, Any]] = []
    problems: list[str] = []

    for table in collector.tables:
        grid = _expand(table)

        # 2009 年起的正解表是列式的：一行一题，「問 / 解答番号 / 正解」各占一列。
        # 这比早年的行式版式明确得多，优先按它读。
        column_entries, column_problems = _parse_column_layout(grid, default_section)
        if column_entries:
            if section_order:
                column_entries, order_problems = assign_sections_by_restart(
                    column_entries, section_order)
                column_problems = column_problems + order_problems
            entries.extend(column_entries)
            problems.extend(column_problems)
            continue

        for index, line in enumerate(grid):
            slot_at = _label_index(line, _SLOT_ROW)
            if slot_at is None:
                # 形态 A：日本語各节印成「問 1番 2番 …／答 3 4 …」，没有解答欄行，
                # 題号本身就是欄号。
                entries.extend(_parse_numbered_block(grid, index, problems))
                continue
            slots = [c.translate(_FULLWIDTH).strip() for c in line[slot_at + 1:]]
            slots = [c for c in slots if c.isdigit()]
            if not slots:
                continue

            answer_line = None
            for j in range(index + 1, min(index + 3, len(grid))):
                if _label_index(grid[j], _ANSWER_ROW) is not None:
                    answer_line = grid[j]
                    break
            if answer_line is None:
                problems.append(f"解答欄 {slots[0]}… 下面没有找到 答 行")
                continue
            answer_at = _label_index(answer_line, _ANSWER_ROW)
            answers = [c.strip().rstrip("*＊").strip() for c in answer_line[answer_at + 1:]]
            answers = [a for a in answers if a]
            if len(answers) != len(slots):
                problems.append(
                    f"解答欄 {len(slots)} 个与答案 {len(answers)} 个不匹配（{slots[0]}…）")
                continue

            # 解答欄 行之上、能与列数对齐的表头行才采信
            aligned: list[list[str]] = []
            for j in range(index - 1, -1, -1):
                row = grid[j]
                if not row:
                    continue
                # 区块边界：上一节的答案行，或一个独立的小节标题。越过它就串节了。
                if _label_index(row, _ANSWER_ROW) is not None:
                    break
                if len({c.strip() for c in row if c.strip()}) == 1:
                    break
                offset = _label_index(row, _LABEL_ROW)
                cells = [c.strip() for c in row[(offset + 1) if offset is not None else 1:]]
                cells = [c for c in cells if c]
                if len(cells) == len(slots):
                    aligned.append(cells)
                elif cells:
                    problems.append(
                        f"表头行与解答欄列数不一致（表头 {len(cells)} / 解答欄 {len(slots)}），"
                        f"该行題号不采用：{cells[:4]}")
                if len(aligned) >= 2:
                    break

            labels = aligned[0] if aligned else [None] * len(slots)
            groups = aligned[1] if len(aligned) > 1 else [None] * len(slots)
            section = _nearest_section(grid, index)

            for position, slot in enumerate(slots):
                entries.append({
                    "section": section,
                    "group": groups[position] if position < len(groups) else None,
                    "label": labels[position] if position < len(labels) else None,
                    "slot": slot,
                    "answer": answers[position],
                })

    # 结构化捕获里的小节标题行位置不可信，而且错法有两种：标题漂到自己数据的后面
    # （化学），或者整体错位一个区块 —— 某页 `<td>読解</td>` 之后跟的其实是聴読解的
    # 答案，逐位吻合。两种都会把答案安到别的小节，那等于判错。扁平文本是自上而下
    # 读的，它报出的小节顺序可靠；欄号回到 1 是分节点。只要有这个顺序就以它为准，
    # 不再采用表内向上找标题的结果。分块数与标题数对不上就整页不采用。
    if section_order and entries:
        entries, order_problems = assign_sections_by_restart(entries, section_order)
        problems.extend(order_problems)
    return {"entries": _merge(entries), "problems": problems}


_NUMBERED = re.compile(r"^([0-9]{1,3})\s*番?$")


def _parse_numbered_block(
    grid: list[list[str]], index: int, problems: list[str]
) -> list[dict[str, Any]]:
    """A 問-row directly above an 答-row, where the 問 numbers are the slots.

    This is how the 日本語 sections are printed: 「問 1番 2番 …／答 3 4 …」.
    There is no separate 解答欄 row, so the printed question number is the
    answer-sheet number.
    """
    line = grid[index]
    label_at = _label_index(line, _LABEL_ROW)
    if label_at is None:
        return []
    numbers = [c.translate(_FULLWIDTH).strip() for c in line[label_at + 1:]]
    numbers = [_NUMBERED.match(c).group(1) for c in numbers if _NUMBERED.match(c)]
    if not numbers:
        return []
    if index + 1 >= len(grid):
        return []
    answer_line = grid[index + 1]
    answer_at = _label_index(answer_line, _ANSWER_ROW)
    if answer_at is None:
        return []
    answers = [c.strip().rstrip("*＊").strip() for c in answer_line[answer_at + 1:]]
    answers = [a for a in answers if a]
    if len(answers) != len(numbers):
        problems.append(f"題号 {len(numbers)} 个与答案 {len(answers)} 个不匹配（問{numbers[0]}…）")
        return []
    section = _nearest_section(grid, index)
    return [
        {"section": section, "group": None, "label": f"問{number}",
         "slot": number, "answer": answer}
        for number, answer in zip(numbers, answers)
    ]

def _nearest_section(grid: list[list[str]], index: int) -> str | None:
    """The last single-cell heading above this table block (物理 / 化 学 / 読解…)."""
    for j in range(index - 1, -1, -1):
        cells = [c.strip() for c in grid[j] if c.strip()]
        if len(set(cells)) == 1 and cells and not any(ch.isdigit() for ch in cells[0]):
            text = cells[0].strip("〈〉<>《》 ")
            if text and not _LABEL_ROW.match(text) and not _SLOT_ROW.match(text) \
                    and not _ANSWER_ROW.match(text):
                return text
    return None


def _merge(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Consecutive slots under one 題号 belong to the same question."""
    merged: list[dict[str, Any]] = []
    for entry in entries:
        key = (entry["section"], entry["group"], entry["label"])
        if merged and entry["label"] and \
                (merged[-1]["section"], merged[-1]["group"], merged[-1]["label"]) == key:
            merged[-1]["slots"].append(entry["slot"])
            merged[-1]["answers"].append(entry["answer"])
            continue
        merged.append({
            "section": entry["section"], "group": entry["group"], "label": entry["label"],
            "slots": [entry["slot"]], "answers": [entry["answer"]],
        })
    return merged


def to_answer_refs(parsed: dict[str, Any]) -> dict[str, str]:
    """``{answerRef: answer}`` keyed by 解答欄 number, the authoritative slot id.

    Only sections whose printed heading is recognised are emitted, so an
    unreadable heading drops its answers instead of attaching them to a guessed
    form. Multi-slot questions contribute one entry per slot.
    """
    from .answer_key import section_prefix

    refs: dict[str, str] = {}
    for entry in parsed.get("entries", []):
        prefix = section_prefix(entry.get("section") or "")
        if not prefix:
            continue
        for slot, answer in zip(entry["slots"], entry["answers"]):
            refs[f"{prefix}:{int(slot)}"] = answer
    return refs


def slots_by_label(parsed: dict[str, Any]) -> dict[tuple[str, str], list[str]]:
    """``{(section, 題号): [解答欄…]}`` for joining booklet questions to slots.

    Only entries whose 題号 survived header alignment appear here.
    """
    index: dict[tuple[str, str], list[str]] = {}
    for entry in parsed.get("entries", []):
        section, label = entry.get("section"), entry.get("label")
        if not section or not label:
            continue
        index.setdefault((section, label), []).extend(entry["slots"])
    return index
