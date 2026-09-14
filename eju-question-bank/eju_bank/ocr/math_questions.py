"""Collect mathematics questions from a booklet's OCR, one per printed 問.

EJU mathematics prints a 大題 numeral, then 問1 / 問2, each with lettered blanks
spread over its sub-questions::

    I
    問2 2つの袋A, Bがある。…
        (1) …確率は $\\frac{J}{KL}$ である。
        (2) …確率は $\\frac{M}{N}$ である。

One 問 owns all of those blanks, which is how the 正解表 groups them too, so a
question is assembled per (大題, 問) with the whole stem — sub-questions
included — and its blanks taken from the key.

The blanks are *not* read off the stem. A stem prints them inside LaTeX but also
carries ordinary variable names and the 大題 numeral in the same shape, so a
bare ``I`` cannot be told apart there. What the stem does give is a check: every
blank letter it shows unambiguously (inside ``\\boxed{}`` or ``\\frac{}{}``)
must be one the key also lists. A stem that references a letter the key does not
have means the two were not read off the same question, and the pairing is
refused.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# 大題标题有时独占一行，有时后面接一整句说明
# （「II 次の各問題文中のA～Pには、…」），两种都要认。
_GROUP_LINE = re.compile(r"^\s*([ⅠⅡⅢⅣⅤ]|I{1,3}|IV|V)(?:\s*$|\s+(?=[^\s0-9]))")
# 说明句里直接印出了这个大題的欄位范围：「A～Pには」。这是正解表之外的一份独立证据。
_GROUP_RANGE = re.compile(r"([A-Z])\s*[～~〜]\s*([A-Z])")
_QUESTION_HEAD = re.compile(r"^[問问间]\s*([0-9]{1,2})\s*(.*)$")
_SUB_HEAD = re.compile(r"^[\(（]\s*([0-9]{1,2})\s*[\)）]\s*(.*)$")
_FOOTER = re.compile(r"^(?:数学\s*[-ー―－]\s*[0-9]+|[-ー―\s]*[0-9]{1,3}[-ー―\s]*"
                     r"|[-ー―\s]*計算欄\s*\(memo\)\s*[-ー―\s]*)$")
_ROMAN_NORMAL = {"Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV", "Ⅴ": "V"}

# 无歧义的欄位写法：只有这两种能确定是欄位而不是变量名。
# 2007 年前的题册把空格印成 \text{A} / \text{BC}，不是 \boxed{}。少认这一种，
# 整个年代的数学题都读不出自己的欄位。
_BOXED = re.compile(r"\\(?:boxed|fbox|text|mathrm)\{([A-Z]{1,8})\}")
_FRAC = re.compile(r"\\frac\{([^}]*)\}\{([^}]*)\}")
_LETTERS = re.compile(r"(?<![A-Za-z])([A-Z]{1,8})(?![A-Za-z])")


# 数学题册的 PDF 末尾常常附印正解表。那些页读起来像一串「字母 数字」，
# 被当成题干会造出重复的 (大題, 問)，把审计里的唯一性检查撞掉。
_ANSWER_PAGE = (
    "正解表", "解答番号", "The Correct Answers", "コース1 Course", "コース2 Course",
)


def looks_like_answer_page(raw: str) -> bool:
    """Whether this page is a printed answer key rather than booklet content."""
    if any(marker in raw for marker in _ANSWER_PAGE):
        return True
    # 没有明确标题时看密度：整页几乎只有「字母 数字」行。
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if len(lines) < 4:
        return False
    rows = sum(1 for l in lines if re.fullmatch(r"(?:[ⅠⅡⅢⅣⅤIV]+\s*)?(?:[問问间]\s*\d+\s*)?"
                                                r"(?:[A-Z]{1,8}\s+-?[-0-9]{1,8}\s*)+", l))
    return rows >= max(4, len(lines) * 0.6)

def stem_slot_letters(stem: str) -> set[str]:
    """The blank letters this stem shows unambiguously."""
    found: set[str] = set()
    for match in _BOXED.finditer(stem):
        found.update(match.group(1))
    for numerator, denominator in _FRAC.findall(stem):
        for part in (numerator, denominator):
            for run in _LETTERS.findall(part):
                found.update(run)
    return found


def collect_math_questions(work_dir: Path) -> list[dict[str, Any]]:
    """One entry per printed (大題, 問), with its full stem and page span.

    Questions run across pages — a 問 often continues past a 計算欄 spread — so
    this walks the whole booklet rather than treating pages independently.
    """
    cache = work_dir / "ocr_cache"
    if not cache.is_dir():
        return []

    collected: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    group = ""
    group_range: dict[str, set[str]] = {}

    def close() -> None:
        nonlocal current
        if current and current["stem_lines"]:
            stem = " ".join(current["stem_lines"]).strip()
            collected.append({
                "group": current["group"], "question": current["question"],
                "stem": stem, "pages": sorted(current["pages"]),
                "stem_letters": stem_slot_letters(stem),
                # 题干是逐行拼接、并给子問补了「(N) 」的，整串不会是页面文本的子串。
                # 把真正读到的原始行留下，想核对"这些字确实印在这些页上"才有依据。
                "source_lines": list(current["source_lines"]),
            })
        current = None

    for path in sorted(cache.glob("p*.json"), key=lambda p: int(p.stem.lstrip("p"))):
        try:
            raw = json.loads(path.read_text(encoding="utf-8")).get("raw_text") or ""
        except Exception:
            continue
        page = int(path.stem.lstrip("p"))
        if looks_like_answer_page(raw):
            close()          # 正解表页：题册内容到此为止
            continue
        for raw_line in raw.splitlines():
            line = raw_line.replace("　", " ").strip()
            if not line or _FOOTER.match(line):
                continue
            head = _GROUP_LINE.match(line)
            if head:
                close()
                group = _ROMAN_NORMAL.get(head.group(1), head.group(1))
                # 有些大題整题只有一组欄位、不带「問N」。先开一个無問号的塊；
                # 若随后真的出现 問N，close() 会把它顶掉。
                declared = _GROUP_RANGE.search(line)
                group_range[group] = (
                    {chr(c) for c in range(ord(declared.group(1)), ord(declared.group(2)) + 1)}
                    if declared else set())
                current = {"group": group, "question": "", "stem_lines": [],
                           "source_lines": [], "pages": {page}}
                continue
            question = _QUESTION_HEAD.match(line)
            if question:
                close()
                current = {"group": group, "question": question.group(1),
                           "stem_lines": [question.group(2)] if question.group(2) else [],
                           "source_lines": [line], "pages": {page}}
                continue
            if current is None:
                continue
            sub = _SUB_HEAD.match(line)
            current["stem_lines"].append(f"({sub.group(1)}) {sub.group(2)}" if sub else line)
            current["source_lines"].append(line)
            current["pages"].add(page)
    close()

    # (大題, 問) 必须唯一：重复会撞掉审计的 questionId / answerRef 唯一性检查。
    # 保留第一次出现的，其余丢弃 —— 重复只可能来自误读，不是真有两个同号題。
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for item in collected:
        key = (item["group"], item["question"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    for item in unique:
        item["group_range"] = sorted(group_range.get(item["group"]) or ())
    return unique


def closed_groups(collected: list[dict[str, Any]], parsed_answers: dict[str, Any],
                  course: str, stats: dict[str, int] | None = None) -> dict[str, dict[str, str]]:
    """大題 whose questions' stem letters exactly account for the key's letters.

    The pre-2007 key prints mathematics as a transposed table whose header
    colspans OCR cannot recover, so it yields ``大題 → letter → answer`` and
    nothing about which 問 owns which letter. The booklet supplies that: each 問
    prints its own blanks. Taking it on trust would risk a 問 published with
    fewer blanks than it has, so a 大題 is used only when the union of its
    questions' stem letters equals the key's letter set for that 大題 exactly —
    nothing missing, nothing extra, nothing claimed twice.
    """
    groups = (parsed_answers.get("groups") or {}).get(course) or {}
    if not groups:
        return {}
    seen: dict[str, list[set[str]]] = {}
    for item in collected:
        if item.get("group") in groups:
            seen.setdefault(item["group"], []).append(set(item.get("stem_letters") or ()))
    out: dict[str, dict[str, str]] = {}
    for group, letter_sets in seen.items():
        union: set[str] = set()
        overlap = False
        for one in letter_sets:
            if union & one:
                overlap = True
            union |= one
        if not overlap and union == set(groups[group]):
            out[group] = dict(groups[group])
        elif stats is not None:
            stats["group_not_closed"] = stats.get("group_not_closed", 0) + 1
    return out


def build_math_questions(
    collected: list[dict[str, Any]],
    parsed_answers: dict[str, Any],
    *,
    source_id: str,
    form_code: str,
    stable_id,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Pair each printed 問 with the blanks the key gives it.

    A question is emitted only when the key lists blanks for its (大題, 問) and
    every blank the stem shows is among them. Anything else is counted and
    dropped — a mathematics answer is per blank, so a shifted pairing would mark
    every blank of that question wrongly.
    """
    from .math_answers import slots_for

    course = form_code.rsplit("_", 1)[0] if form_code.endswith(("_JA", "_EN")) else form_code
    stats = {"emitted": 0, "no_slots": 0, "letters_disagree": 0, "no_stem": 0,
             "from_group_closure": 0, "group_not_closed": 0}
    questions: list[dict[str, Any]] = []
    closed = closed_groups(collected, parsed_answers, course, stats)

    for item in collected:
        blanks = slots_for(parsed_answers, course, item["group"], item["question"])
        if not blanks and item["group"] in closed:
            # 这份正解表只给得出「大題 → 字母 → 答案」，給不出「哪些字母属于哪个問」
            # （它的表头 colspan 不可用）。每個問的欄位改由题干印出的字母给出，
            # 而 closed_groups 已经验明这个大題的各問字母并集恰好等于它的字母全集 ——
            # 闭合才用，所以不会有哪一格被漏掉或被安到别的問上。
            blanks = {letter: closed[item["group"]][letter]
                      for letter in sorted(item["stem_letters"])}
            if blanks:
                stats["from_group_closure"] += 1
        if not blanks:
            stats["no_slots"] += 1
            continue
        if not item["stem"]:
            stats["no_stem"] += 1
            continue
        # 题干里无歧义地出现的字母，必须都在正解表给出的欄位里。
        if item["stem_letters"] and not item["stem_letters"] <= set(blanks):
            stats["letters_disagree"] += 1
            continue

        slots = list(blanks)
        # 大題整题只有一组欄位时没有問号，localKey 与 answerRef 都省掉那一段。
        suffix = f"-q{int(item['question']):02d}" if item["question"] else ""
        local_key = f"math-{item['group'].lower()}{suffix}"
        questions.append({
            "questionId": stable_id("q_", source_id, form_code, local_key),
            "localKey": local_key,
            "printedLabel": (f"{item['group']} 問{item['question']}" if item["question"]
                             else f"第{item['group']}問"),
            "sectionCode": "MAIN",
            "answerRef": f"{item['group']}:{item['question']}" if item["question"] else item["group"],
            "stemAst": [{"type": "text", "value": item["stem"]}],
            "options": [],
            "answerSpec": {"type": "DIGIT_GRID", "slots": slots},
            "correctAnswer": {"tokens": {slot: blanks[slot] for slot in slots}},
            # 来源标记：闸门只放行标了这个的答案。发布前会摘掉。
            "_answerSource": "answer-key",
            "materialRefs": [],
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET",
                          "page": item["pages"][0], "bbox": [0.1, 0.1, 0.9, 0.9]}],
        })
        stats["emitted"] += 1

    return questions, stats
