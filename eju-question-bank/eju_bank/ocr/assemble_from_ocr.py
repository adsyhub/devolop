"""Build paper questions from what OCR actually read, never from a template.

The booklet side of the rebuild. Two things make a question publishable:

1. Its stem and its complete option run were read off the page
   (:mod:`eju_bank.ocr.question_blocks`).
2. Its printed number joins to a verified answer from the 正解表
   (:mod:`eju_bank.ocr.answer_table`).

Only sections where that join is *provable* are assembled. In the 日本語
booklet the printed 問N is itself the 解答欄 number, so 読解 問1 is
``READING:1`` — a direct, checkable join. Sections whose 題号 restarts per
大題 (理科, 総合科目) do not have that property; they are collected but left
without answers, so the publish gate drops them rather than pairing by guess.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Booklet section headings -> (answerRef prefix, sectionCode, joins by 題号?).
# 「直接对接」means the printed question number is the answer-sheet number.
SECTIONS: dict[str, tuple[str, str, bool]] = {
    "読解": ("READING", "READING", True),
    "聴読解": ("LISTENING_COMPREHENSION", "LISTENING", True),
    "聴解": ("LISTENING", "LISTENING", True),
    "記述": ("WRITING", "WRITING", False),
    "物理": ("PHYSICS", "MAIN", False),
    "化学": ("CHEMISTRY", "MAIN", False),
    "生物": ("BIOLOGY", "MAIN", False),
    "総合科目": ("JW", "MAIN", False),
}

# 每个 form 只接受属于它的小节。用显式表而不是按前缀字符串匹配：
# JAPANESE_JA 的小节叫 READING / LISTENING，字面上与 "JAPANESE" 对不上。
FORM_SECTIONS: dict[str, set[str]] = {
    "JAPANESE_JA": {"READING", "LISTENING", "LISTENING_COMPREHENSION", "WRITING"},
    "PHYSICS_JA": {"PHYSICS"}, "PHYSICS_EN": {"PHYSICS"},
    "CHEMISTRY_JA": {"CHEMISTRY"}, "CHEMISTRY_EN": {"CHEMISTRY"},
    "BIOLOGY_JA": {"BIOLOGY"}, "BIOLOGY_EN": {"BIOLOGY"},
    "JAPAN_AND_WORLD_JA": {"JW"}, "JAPAN_AND_WORLD_EN": {"JW"},
}

_HEADING = re.compile(
    r"^\s*(" + "|".join(re.escape(k) for k in SECTIONS) + r")\s*(?:問題)?\s*$", re.M)
_LABEL_NUMBER = re.compile(r"^問(\d+)$")


def _page_number(path: Path) -> int:
    return int(path.stem.lstrip("p"))


def resolve_slot(item: dict[str, Any]) -> str | None:
    """This question's 解答欄 number, from the most reliable source available.

    Which source is most reliable depends on how the section numbers itself:

    * 日本語 prints 問N *as* the 解答欄 number, so the label wins there;
    * 理科 / 総合科目 restart 問N inside each 大題, so only the boxed number in
      the right margin (or a number printed inline in the stem) can be used.
    """
    section = item.get("section")
    if not section or section not in SECTIONS:
        return None
    direct = SECTIONS[section][2]
    label_slot = None
    match = _LABEL_NUMBER.match(item.get("label") or "")
    if match:
        label_slot = match.group(1)
    if direct:
        return label_slot or item.get("slot") or item.get("boxed_slot")
    return item.get("boxed_slot") or item.get("slot")


def _consecutive_run(candidates: list[int], last: int) -> tuple[list[int], int]:
    """Pick the 解答欄 numbers that continue this section's consecutive run.

    Within a section the printed 解答欄 numbers run 1, 2, 3, … with no gaps, so
    the only credible next value is ``last + 1``. Insisting on that discards the
    noise the margin strip picks up — the page marker 「理科一11」, the footer
    page number, an option number that leans into the margin — without having
    to locate any of them geometrically.

    The run advances even when the page's counts later fail to match, so the
    following page resynchronises instead of losing the rest of the section.
    """
    accepted: list[int] = []
    expected = last + 1
    for number in candidates:
        if number == expected:
            accepted.append(number)
            expected += 1
    return accepted, expected - 1


def _page_slots(work_dir: Path, number: int) -> list[int]:
    path = work_dir / "slot_cache" / f"p{number:04d}.json"
    if not path.is_file():
        return []
    try:
        return [int(n) for n in json.loads(path.read_text(encoding="utf-8")).get("slots", [])]
    except Exception:
        return []


# 单科题册没有内部小节标题（页眉是「総合科目一5」这种带页码的形式），
# 整本就是一个小节，由来源的 subject 给出。理科与日本語必须靠标题分节。
DEFAULT_SECTION_BY_SUBJECT = {
    "JAPAN_AND_WORLD": "総合科目",
}


def collect_questions(work_dir: Path, *, default_section: str | None = None) -> list[dict[str, Any]]:
    """Every question the booklet OCR states outright, tagged with its section.

    The section is carried forward from the last heading seen, which is how the
    booklet is laid out: a bare 「読解」 page starts that section.

    Where the boxed 解答欄 numbers were read for a page (``slot_cache/``) and
    their count matches the questions found on that page, each question is given
    its printed slot. That is the authoritative join to the 正解表. A page whose
    counts disagree is left without slots rather than paired off by position —
    one missed question would shift every answer after it.
    """
    from .question_blocks import parse_page

    folder = work_dir / "ocr_cache"
    if not folder.exists():
        return []
    collected: list[dict[str, Any]] = []
    section: str | None = default_section
    last_slot = 0
    # 一道题的题干常常印在一页末尾、选项落到下一页开头。逐页独立解析会把它整道丢掉，
    # 连它印着的解答欄号一起丢。未闭合的块交给下一页续上。
    carry: dict[str, Any] | None = None
    for path in sorted(folder.glob("p*.json"), key=_page_number):
        try:
            raw = json.loads(path.read_text(encoding="utf-8")).get("raw_text") or ""
        except Exception:
            continue
        number = _page_number(path)
        head = "\n".join(raw.splitlines()[:4])
        for match in _HEADING.finditer(head):
            if match.group(1) != section:
                section = match.group(1)
                last_slot = 0        # 解答欄 restarts at 1 in each section
        questions, carry = parse_page(raw, carry=carry, page=number)
        slots, last_slot = _consecutive_run(_page_slots(work_dir, number), last_slot)
        paired = slots if len(slots) == len(questions) else [None] * len(questions)
        prefix = SECTIONS[section][0] if section in SECTIONS else None
        for question, slot in zip(questions, paired):
            pages = [p for p in (question.get("pages") or []) if p] or [number]
            collected.append({
                **question,
                "section": section,
                "answer_prefix": prefix,
                # 跨页题按它开始的那一页记账：那是它的题号与解答欄印着的地方。
                "page": min(pages),
                "pages": sorted(set(pages)),
                "boxed_slot": str(slot) if slot is not None else None,
            })
    return collected


MATH_FORMS = {
    "MATHEMATICS_COURSE_1_JA", "MATHEMATICS_COURSE_1_EN",
    "MATHEMATICS_COURSE_2_JA", "MATHEMATICS_COURSE_2_EN",
}


def build_math(
    work_dir: Path, parsed_answers: dict[str, Any], *, source_id: str, form_code: str, stable_id,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Mathematics goes its own way: digit-grid blanks, several per printed 問."""
    from .math_questions import build_math_questions, collect_math_questions

    return build_math_questions(
        collect_math_questions(work_dir), parsed_answers,
        source_id=source_id, form_code=form_code, stable_id=stable_id)


def build_questions(
    collected: list[dict[str, Any]],
    answers: dict[str, str],
    *,
    source_id: str,
    form_code: str,
    stable_id,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Turn collected OCR questions into paper questions with verified answers.

    Returns the questions and a count of what was left out and why. A question
    is emitted only when its answer is verified and present among its options;
    everything else is reported, never padded.
    """
    from .content_ast import nodes_from_parts, nodes_from_text

    stats = {"emitted": 0, "no_section": 0, "other_form": 0, "no_join": 0,
             "no_answer": 0, "answer_not_an_option": 0, "content_defect": 0}
    questions: list[dict[str, Any]] = []
    allowed = FORM_SECTIONS.get(form_code)

    for item in collected:
        section = item.get("section")
        if not section or section not in SECTIONS:
            stats["no_section"] += 1
            continue
        prefix, section_code, direct = SECTIONS[section]
        # 这一小节不属于当前 form（同一本理科题册里物理/化学/生物是三个 form）
        if allowed is not None and prefix not in allowed:
            stats["other_form"] += 1
            continue

        slot = resolve_slot(item)
        if not slot:
            stats["no_join"] += 1
            continue

        answer_ref = f"{prefix}:{int(slot)}"
        answer = answers.get(answer_ref)
        if answer is None:
            stats["no_answer"] += 1
            continue
        if str(answer) not in item["options"]:
            stats["answer_not_an_option"] += 1
            continue

        if item.get("defects"):
            stats["content_defect"] = stats.get("content_defect", 0) + 1
            continue

        local_key = f"{prefix.lower()}-q-{int(slot):02d}"
        # 题面按读到的结构交付：公式是 inlineMath，二维表是 table，下線部是
        # underline。压成一个 text 节点是全库 0 图 0 公式 0 表格的直接原因
        # （审计 F11/F12/F31）。
        stem_ast = nodes_from_parts(item.get("stem_parts") or
                                    [{"type": "text", "value": item["stem"]}])
        questions.append({
            "questionId": stable_id("q_", source_id, form_code, local_key),
            "localKey": local_key,
            "printedLabel": item.get("label") or f"問{slot}",
            "sectionCode": section_code,
            "answerRef": answer_ref,
            "stemAst": stem_ast,
            "options": [
                {"key": key, "contentAst": nodes_from_text(text) or
                 [{"type": "text", "value": text}]}
                for key, text in item["options"].items()
            ],
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": {"optionKey": str(answer)},
            "materialRefs": [],
            "evidence": [{
                "sourceFileRole": "QUESTION_BOOKLET",
                "page": item["page"],
                "bbox": [0.1, 0.1, 0.9, 0.9],
            }],
            "_context": item.get("context"),
        })
        stats["emitted"] += 1

    return questions, stats


# ---------------------------------------------------------------------------
# 页面合同：给复核台的草稿
# ---------------------------------------------------------------------------

def form_code_for(section: str, forms: list[str]) -> str | None:
    """Which of this source's forms owns a booklet section."""
    prefix = SECTIONS.get(section, (None, None, None))[0]
    if not prefix:
        return None
    for form in forms:
        if prefix in FORM_SECTIONS.get(form, set()):
            return form
    return None


def write_page_contracts(
    work_dir: Path,
    *,
    forms: list[str],
    answers: dict[str, str] | None = None,
    default_section: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Write one contract draft per booklet page that OCR could read.

    A page that already has a saved revision in the database is never touched
    here — a person may have edited or signed it, and a regenerated draft would
    quietly discard that work. Only files on disk are written, and only when
    ``overwrite`` allows it.
    """
    from .page_contracts import build_page_contract, contract_path

    collected = collect_questions(work_dir, default_section=default_section)
    by_page: dict[int, list[dict[str, Any]]] = {}
    for item in collected:
        by_page.setdefault(item["page"], []).append(item)

    # 数学的题干跨页、欄位来自正解表，用它自己的收集器另算一份，
    # 挂在该题起始页上。
    math_by_page: dict[int, list[dict[str, Any]]] = {}
    if any(f in MATH_FORMS for f in forms):
        from .math_answers import slots_for
        from .math_questions import collect_math_questions
        from .verified_answers import load_math_answers

        math_answers, _ = load_math_answers(work_dir)
        course = next(f for f in forms if f in MATH_FORMS).rsplit("_", 1)[0]
        for item in collect_math_questions(work_dir):
            # 欄位以正解表为准：题干里的矩阵、根号等写法读不出字母，而正解表
            # 逐格列出了它们。读不到就留空并在合同里记 issue，不猜。
            blanks = slots_for(math_answers, course, item["group"], item["question"])
            item = {**item, "key_slots": list(blanks)}
            if item["pages"]:
                math_by_page.setdefault(item["pages"][0], []).append(item)

    cache = work_dir / "ocr_cache"
    pages = sorted(int(f.stem.lstrip("p")) for f in cache.glob("p*.json")) if cache.is_dir() else []
    written = skipped = 0
    for page in pages:
        target = contract_path(work_dir, "QUESTION_BOOKLET", page)
        if target.exists() and not overwrite:
            skipped += 1
            continue
        items = by_page.get(page, [])
        section = next((i.get("section") for i in items if i.get("section")), default_section)
        contract = build_page_contract(
            work_dir, "QUESTION_BOOKLET", page,
            form_code=form_code_for(section or "", forms) or (forms[0] if forms else None),
            questions=items, answers=answers,
            math_questions=math_by_page.get(page, []))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1
    return {"pages": len(pages), "written": written, "skipped": skipped,
            "questions": len(collected)}
