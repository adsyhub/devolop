"""Read the mathematics half of the 正解表, where answers are per-blank.

EJU mathematics is a mark-sheet of lettered blanks, so the key lists the blank
letters and the digits that fill them::

    コース1 Course 1
    問 Q. 解答番号 row 正解 A.

    I 問 1 ABCD 5723
           EFGH 5435
           I 2
      問 2 JKL 925

``ABCD 5723`` means A=5, B=7, C=2, D=3 — the letters and the digits line up one
for one. A minus sign occupies a blank of its own, so ``DE -3`` is D='-', E='3'.

The letters are taken from here rather than from the booklet on purpose. A
booklet stem prints them inside LaTeX (``\\frac{J}{KL}``, ``\\boxed{H}``) but
also contains ordinary variable names and 大題 numerals in the same shape, so a
bare ``I`` is ambiguous there and unambiguous here.

A row whose letters and digits disagree in length is reported, never split by
guesswork: mis-slicing one row would put every later answer on the wrong blank.
"""

from __future__ import annotations

import re
from typing import Any

from ..constants import ALLOWED_DIGIT_TOKENS

COURSE_PREFIX = {"コース1": "MATHEMATICS_COURSE_1", "コース2": "MATHEMATICS_COURSE_2"}

_COURSE = re.compile(r"コース\s*([12])")
_GROUP = re.compile(r"^\s*([ⅠⅡⅢⅣⅤ]|I{1,3}V?|IV|V)\b")
_QUESTION = re.compile(r"[問问间]\s*([0-9]+)")
# 「ABCD 5723」／「DE -3」：字母串 + 由数字和负号组成的值。
_ROW = re.compile(r"(?<![A-Za-z])([A-Z]{1,8})\s+(-?[-0-9]{1,8})(?![0-9])")
_ROMAN_NORMAL = {"Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV", "Ⅴ": "V"}


def _tokens(value: str) -> list[str] | None:
    """Split a printed answer into one token per blank, or None if it cannot be."""
    out: list[str] = []
    for char in value:
        if char not in ALLOWED_DIGIT_TOKENS:
            return None
        out.append(char)
    return out or None


def parse_math_answers(text: str) -> dict[str, Any]:
    """``{"courses": {prefix: {(group, question): {letter: token}}}, "problems": [...]}``"""
    courses: dict[str, dict[tuple[str, str], dict[str, str]]] = {}
    problems: list[str] = []
    course: str | None = None
    group = question = ""

    for raw_line in (text or "").splitlines():
        line = raw_line.replace("　", " ").strip()
        if not line:
            continue

        found_course = _COURSE.search(line)
        if found_course:
            course = COURSE_PREFIX[f"コース{found_course.group(1)}"]
            group = question = ""
            continue
        if course is None:
            continue

        # 「I 2」是「欄位 I = 2」，不是大題 I —— 罗马数字与欄位字母同形。
        # 判据：行首若能直接解析成「字母 数字」，这就是数据行。
        head = None if _ROW.match(line) else _GROUP.match(line)
        if head:
            group = _ROMAN_NORMAL.get(head.group(1), head.group(1))
            # 問号必须随大題重置。有些大題（III、IV）整题只有一组欄位、不带
            # 「問N」；沿用上一个大題的問号会把它们错标成「III 問2」，
            # 等于把欄位安到别的題上。
            question = ""
        found_q = _QUESTION.search(line)
        if found_q:
            question = found_q.group(1)

        for letters, value in _ROW.findall(line):
            tokens = _tokens(value)
            if tokens is None:
                problems.append(f"{course} {group}問{question}: 「{letters} {value}」含非法字符，未采用")
                continue
            if len(tokens) != len(letters):
                problems.append(
                    f"{course} {group}問{question}: 「{letters} {value}」"
                    f"字母 {len(letters)} 个与数字 {len(tokens)} 个不匹配，未采用")
                continue
            bucket = courses.setdefault(course, {}).setdefault((group, question), {})
            for letter, token in zip(letters, tokens):
                bucket[letter] = token

    vertical = parse_math_vertical(text)
    problems.extend(vertical["problems"])
    return {"courses": courses, "groups": vertical["groups"], "problems": problems}


_DASHES = "—–ー一−ｰ-"
_LETTER = re.compile(r"^[A-Z]$")
_SLOT_HEAD = re.compile(r"^解答[棚欄桐]")
_ANSWER_HEAD = re.compile(r"^[答荅]$")


def _token(line: str) -> str | None:
    """One printed blank's value, or None when this line is not one.

    A minus sign fills a blank of its own and OCR renders it as any of a handful
    of dashes — including the kanji 一, which is why reading the run as digits
    alone stopped at the first negative answer.
    """
    text = line.strip()
    if len(text) != 1:
        return None
    if text in _DASHES:
        return "-"
    return text if text.isdigit() else None


def parse_math_vertical(text: str) -> dict[str, Any]:
    """Read the transposed mathematics key, the one printed as a column table.

    Through 2006 the key prints mathematics as a table read down the page, and
    OCR flattens it to one cell per line::

        I            ← 大題 names, in order
        II
        問1           ← 問 labels, which cannot be aligned to blanks:
        問2              OCR's colspan estimates are unusable (measured: 2 of
        …                42 header blocks aligned), so they are not used
        解答棚
        A B C D E A B C D E F G H I J      ← one letter per line
        答
        1 4 1 3 5 7 1 8 2 2 3 3 1 4 3      ← one value per line

    Letters and values line up one for one, and the count of letters says how
    many values to take — which is what keeps the 別解 note printed underneath
    ("AB=23または46") from being swallowed as more answers.

    Blank letters restart at A in each 大題, so a return to A is a self-evident
    大題 boundary; the 大題 names read above the block supply the order. Blocks
    and names that do not count out are left alone rather than guessed at.

    Returns ``{"groups": {course: {group: {letter: token}}}, "problems": [...]}``.
    """
    groups: dict[str, dict[str, dict[str, str]]] = {}
    problems: list[str] = []
    lines = [l.replace("　", " ").strip() for l in (text or "").splitlines()]
    lines = [l for l in lines if l]
    course: str | None = None
    pending_names: list[str] = []
    last_group: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        found_course = _COURSE.search(line)
        if found_course:
            course = COURSE_PREFIX[f"コース{found_course.group(1)}"]
            pending_names = []
            index += 1
            continue
        head = _GROUP.match(line)
        if head and not _SLOT_HEAD.match(line):
            pending_names.append(_ROMAN_NORMAL.get(head.group(1), head.group(1)))
            index += 1
            continue
        if not _SLOT_HEAD.match(line):
            index += 1
            continue

        cursor = index + 1
        letters: list[str] = []
        while cursor < len(lines) and _LETTER.match(lines[cursor]):
            letters.append(lines[cursor])
            cursor += 1
        if not letters or cursor >= len(lines) or not _ANSWER_HEAD.match(lines[cursor]):
            index = cursor + 1
            pending_names = []
            continue
        cursor += 1
        values: list[str] = []
        while cursor < len(lines) and len(values) < len(letters):
            token = _token(lines[cursor])
            if token is None:
                break
            values.append(token)
            cursor += 1
        if len(values) != len(letters):
            problems.append(
                f"{course or '(无课程)'}: 解答欄 {len(letters)} 个字母只读到 {len(values)} 个答案"
                f"（{''.join(letters)}），这一块不采用")
            index = cursor
            pending_names = []
            continue

        runs: list[list[int]] = []
        for position, letter in enumerate(letters):
            if letter == "A" or not runs:
                runs.append([])
            runs[-1].append(position)
        names = pending_names[-len(runs):] if len(pending_names) >= len(runs) else []
        if not names and len(runs) == 1 and letters[0] != "A" and last_group:
            # 大題跨块续印时不重复标题，而字母没有从 A 重启正说明它还是同一个大題。
            names = [last_group]
        if not names:
            problems.append(
                f"{course or '(无课程)'}: 这一块分出 {len(runs)} 个大題，但上方只读到 "
                f"{len(pending_names)} 个大題名（{pending_names}），不采用")
            index = cursor
            pending_names = []
            continue
        for name, run in zip(names, runs):
            bucket = groups.setdefault(course or "", {}).setdefault(name, {})
            for position in run:
                bucket[letters[position]] = values[position]
            last_group = name
        pending_names = []
        index = cursor
    return {"groups": groups, "problems": problems}


def to_answer_refs(parsed: dict[str, Any]) -> dict[str, str]:
    """Flatten to ``{"<COURSE>:<GROUP>:<QUESTION>:<LETTER>": token}``.

    The blank letter is part of the reference because a mathematics question
    owns several blanks and each is marked separately.
    """
    refs: dict[str, str] = {}
    for course, groups in parsed.get("courses", {}).items():
        for (group, question), blanks in groups.items():
            for letter, token in blanks.items():
                refs[f"{course}:{group}:{question}:{letter}"] = token
    return refs


def slots_for(parsed: dict[str, Any], course: str, group: str, question: str) -> dict[str, str]:
    """The blanks one printed question owns, in printed order."""
    return dict(parsed.get("courses", {}).get(course, {}).get((group, question), {}))
