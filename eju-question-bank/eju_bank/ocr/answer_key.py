"""Parse an OCR'd EJU 正解表 (official answer key) into verified answers.

EJU answer keys are printed as paired rows under a section heading::

    読解
    問 1 問2 問3 ... 問16
    答 1 3  4  ... 3

    物理
    解答欄 1 2 3 ... 13
    答     3* 3 5 ... 3

The header row names the question slots, the row that starts with 答 gives the
answers in the same order. This module pairs those rows and nothing else: it
never invents an answer, and a row it cannot pair is reported rather than
guessed, so a caller can fail closed.
"""

from __future__ import annotations

import re
from typing import Any

# Section headings as printed in the 正解表, mapped to the answerRef prefix the
# assembled paper uses. Anything not listed here is returned under its raw label
# so the caller can decide, rather than being silently dropped.
SECTION_PREFIXES = {
    "読解": "READING",
    "聴解": "LISTENING",
    "聴読解": "LISTENING_COMPREHENSION",
    "物理": "PHYSICS",
    "化学": "CHEMISTRY",
    "生物": "BIOLOGY",
    "総合科目": "JW",
    "総合": "JW",
}

_FULLWIDTH = str.maketrans("０１２３４５６７８９", "0123456789")
# OCR 常把「欄」认成形近字（实测「解答桐」）、把「問」认成「间/问」。
# 这些行由开头的标签加后面一串数字唯一确定，所以允许一两个字的形近偏差。
_HEADER_START = re.compile(r"^(?:解答[^0-9\s]{0,2}|[問问间])")
_ANSWER_START = re.compile(r"^(正解|答)")
# A printed slot is either 「問12」「12番」or a bare number.
_SLOT = re.compile(r"[問问间]\s*(\d+)|(\d+)\s*番|^(\d+)$")
# An answer token may carry a footnote marker (3*) or be a digit-grid sign.
_TOKEN = re.compile(r"^([-−]?\d+|[-−])\*?$")

# 行式正解表的題号有四种印法，实测都出现在原卷里：
#   問1 / 問 1      各科通用的小問
#   1番 / 10番      聴解・聴読解
#   Ⅰ Ⅱ … / X      大題本身（该大題只有一問时，題号与大題印在同一行）
#   X 問1           大題 + 小問
# 「答 …」「正解 …」是成对版式的答案行，绝不能当題号 —— 那会把一整行答案的
# 最后两个数读成「解答欄 + 正解」。裸数字（`10 11 12`）同样不收：它既可能是
# 題号行的一段，也可能是数据行，无从自证。两者都不匹配下面这个式子。
_ROMAN_LABEL = r"[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫIVXL]+"
_ROW_LABEL = re.compile(
    rf"^(?:{_ROMAN_LABEL}\s*)?(?:[問问间]\s*\d{{0,3}}|\d{{1,3}}\s*番)?$")


# 正解表里「Ⅰ Ⅱ Ⅲ」这类罗马数字是一节之内的大题分组，不是新的科目小节。
_ROMAN_ONLY = re.compile(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVXLCDM\s\.\,、]+$")
_CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def _looks_like_section(label: str) -> bool:
    """A standalone subject/section label, as opposed to a group marker or data row."""
    if not label or len(label) > 12 or label in ("問", "答", "正解"):
        return False
    if any(ch.isdigit() for ch in label) or _ROMAN_ONLY.match(label):
        return False
    return bool(_CJK.search(label))


def _norm(text: str) -> str:
    return text.translate(_FULLWIDTH).replace("　", " ").strip()


def _slots(line: str) -> list[str]:
    body = _HEADER_START.sub("", _norm(line), count=1)
    found: list[str] = []
    for token in body.split():
        match = _SLOT.match(token)
        if match:
            found.append(next(g for g in match.groups() if g))
    return found


def _answers(line: str) -> list[str]:
    body = _ANSWER_START.sub("", _norm(line), count=1)
    found: list[str] = []
    for token in body.split():
        match = _TOKEN.match(token)
        if match:
            found.append(match.group(1).replace("−", "-"))
    return found


def parse_answer_key(raw_text: str) -> dict[str, Any]:
    """Return ``{"sections": {label: {slot: answer}}, "problems": [...]}``.

    ``problems`` lists header/answer rows whose lengths disagree. Those slots are
    left out entirely — a mismatched row means the printed table was not read
    reliably, and guessing which column slipped would silently corrupt answers.
    """
    lines = [line for line in (_norm(l) for l in raw_text.splitlines()) if line]
    sections: dict[str, dict[str, str]] = {}
    problems: list[str] = []
    current = ""
    pending: tuple[str, list[str]] | None = None

    for line in lines:
        bare = line.strip("〈〉<>《》 ")
        # 任何独立的短标签都开启一个新小节，哪怕名字不认识。若只认已知名字，
        # OCR 把「物理」读成变体时，它下面的答案会串到上一个小节的题号上 ——
        # 那等于把答案安到错的题上，比丢掉这一节危险得多。
        if _looks_like_section(bare) and not _HEADER_START.match(line) and not _ANSWER_START.match(line):
            current = bare
            pending = None
            continue

        if _HEADER_START.match(line):
            slots = _slots(line)
            if slots:
                pending = (current, slots)
                continue

        if _ANSWER_START.match(line):
            answers = _answers(line)
            if pending is None:
                if answers:
                    problems.append(f"{current or '(无小节)'}: 答案行没有对应的题号行 · {line[:60]}")
                continue
            section, slots = pending
            pending = None
            if not answers:
                continue
            if len(answers) != len(slots):
                problems.append(
                    f"{section or '(无小节)'}: 题号 {len(slots)} 个与答案 {len(answers)} 个不匹配 · {line[:60]}")
                continue
            bucket = sections.setdefault(section or "(无小节)", {})
            for slot, answer in zip(slots, answers):
                bucket[slot] = answer

    # 行式正解表（每行一题：問N 解答欄 正解）在上面这套「題号行 + 答案行」的
    # 规则下什么也读不出。它在扁平文本里反而最好认，而且扁平文本的阅读顺序可靠 ——
    # 结构化捕获里 <thead> 的位置会漂到自己数据的后面，按它切节会把答案安到别科。
    rows = _parse_row_per_question(lines)
    for label, bucket in rows["sections"].items():
        target = sections.setdefault(label, {})
        for slot, answer in bucket.items():
            target.setdefault(slot, answer)
    problems.extend(rows["problems"])

    return {"sections": sections, "problems": problems}


_ROW_TAIL = re.compile(r"^(.*?)([0-9]{1,3})\s+([0-9]{1,2})$")


def _parse_row_per_question(lines: list[str]) -> dict[str, Any]:
    """Read the 正解表 that prints one question per line: ``問N 解答欄 正解``.

    ::

        物理
        問 解答欄 正解
        I
        問 1  1  6
        問 2  2  2
        化学
        問 1  1  5

    The two trailing integers are the 解答欄 and its 正解; whatever precedes them
    is the printed 題号, whose shape varies (``問 1`` / ``問10`` / a bare 大題
    numeral on its own line) and is not needed once the 解答欄 is known. A line
    carrying anything other than exactly two trailing integers is not a data row
    and is skipped, so headers and captions cannot become answers.
    """
    sections: dict[str, dict[str, str]] = {}
    problems: list[str] = []
    current = ""
    for line in lines:
        bare = line.strip("〈〉<>《》 ")
        if _looks_like_section(bare) and not _HEADER_START.match(line):
            current = bare
            continue
        found = _ROW_TAIL.match(line)
        if not found:
            continue
        head = found.group(1).strip()
        # 行首必须是題号，否则这只是一行恰好以两个数结尾的正文。
        if (head and not _HEADER_START.match(head)
                and not _looks_like_section(head) and not _ROW_LABEL.match(head)):
            continue
        slot, answer = found.group(2), found.group(3)
        bucket = sections.setdefault(current or "(无小节)", {})
        if slot in bucket and bucket[slot] != answer:
            problems.append(
                f"{current or '(无小节)'}: 解答欄 {slot} 读到两个不同的正解 "
                f"{bucket[slot]} 与 {answer}，这一欄不采用")
            bucket.pop(slot, None)
            continue
        bucket.setdefault(slot, answer)
    return {"sections": sections, "problems": problems}


def section_prefix(label: str) -> str | None:
    """The answerRef prefix for a printed heading, or None when unrecognised.

    Two-character subject headings are often typeset with an internal space
    (「化 学」「生 物」), so the lookup compares with whitespace removed. An
    unrecognised heading stays unrecognised rather than being mapped to a
    nearby form.
    """
    compact = re.sub(r"\s+", "", label).strip("〈〉<>《》")
    if compact in SECTION_PREFIXES:
        return SECTION_PREFIXES[compact]
    # 2009 年起的正解表在小节名后加英文注释（「物理 Physics」「生物 Biology」）。
    # 日文名在前且是权威标识，英文只是注释，按最长匹配取前缀。
    for name in sorted(SECTION_PREFIXES, key=len, reverse=True):
        if compact.startswith(name):
            return SECTION_PREFIXES[name]
    return None


def to_answer_refs(parsed: dict[str, Any]) -> dict[str, str]:
    """Flatten parsed sections into ``{answerRef: optionKey}``.

    Only sections with a known prefix are emitted; an unmapped heading is left
    for the caller to look at rather than being assigned to a guessed form.
    """
    refs: dict[str, str] = {}
    for label, slots in parsed.get("sections", {}).items():
        prefix = section_prefix(label)
        if not prefix:
            continue
        for slot, answer in slots.items():
            refs[f"{prefix}:{int(slot)}"] = answer
    return refs
