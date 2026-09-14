"""Collect the answers a source can actually prove, from the OCR'd 正解表.

The 正解表 is one document for the whole examination, so a source without its
own answer-key PDF can still be scored from a sibling source of the same
session — each subject only reads its own sections, so nothing crosses over.

Both readings of each answer-key page are used. The plain-text capture supplies
section headings printed outside the table markup; the structured capture
supplies the merged header cells, which is the only record of how many 解答欄 a
single question owns. The structured reading wins where both speak.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_folder(folder: Path, refs: dict[str, str]) -> list[str]:
    """Read one answer-key cache folder, merging every capture of each page.

    Delegates to :func:`eju_bank.ocr.answer_key_contracts.parse_answer_page` so
    there is one reading of the 正解表 and not two that can drift: the same
    flat/structured cross-check and the same 180/400 dpi agreement rule apply
    here as on the path that publishes.
    """
    from .answer_key_contracts import parse_answer_page

    problems: list[str] = []
    for path in sorted(folder.glob("p*.json")):
        raws = []
        for candidate in (path, folder.parent / (folder.name + "_hi") / path.name):
            if candidate.is_file():
                try:
                    raws.append(json.loads(candidate.read_text(encoding="utf-8")))
                except Exception as exc:
                    problems.append(f"{candidate.name}: 读取失败 {exc}")
        if not raws:
            continue
        try:
            page_refs, _math, page_problems = parse_answer_page(raws)
        except Exception as exc:
            problems.append(f"{path.name}: 解析失败 {exc}")
            continue
        refs.update(page_refs)
        problems.extend(f"{path.name} {p}" for p in page_problems)
    return problems


def answer_folders(work_dir: Path) -> list[Path]:
    """This source's answer-key cache, then its same-session siblings'."""
    folders = [work_dir / "answer_ocr"]
    parts = work_dir.name.split("-")
    if len(parts) >= 2:
        prefix = "-".join(parts[:2]) + "-"
        for sibling in sorted(work_dir.parent.glob(prefix + "*")):
            candidate = sibling / "answer_ocr"
            if sibling != work_dir and candidate.is_dir():
                folders.append(candidate)
    return [f for f in folders if f.is_dir()]


def load_verified_answers(work_dir: Path) -> tuple[dict[str, str], list[str]]:
    """``({answerRef: answer}, problems)`` for one source."""
    refs: dict[str, str] = {}
    problems: list[str] = []
    folders = answer_folders(work_dir)
    if not folders:
        return refs, ["没有答案册 OCR（answer_ocr/），本回次无法产出可验证答案"]
    for folder in folders:
        problems.extend(_read_folder(folder, refs))
    return refs, problems


def load_math_answers(work_dir: Path) -> tuple[dict[str, Any], list[str]]:
    """The mathematics half of the 正解表 for one source's session.

    Mathematics answers are per lettered blank rather than per question, so they
    are parsed separately from the multiple-choice sections and returned in the
    shape :func:`eju_bank.ocr.math_questions.build_math_questions` expects.

    The flat capture is used: the mathematics table prints one blank run per
    line (``ABCD 5723``), which survives plain text intact, and unlike the
    multiple-choice key it carries no merged header cells to preserve.
    """
    from .math_answers import parse_math_answers

    merged: dict[str, Any] = {"courses": {}, "groups": {}, "problems": []}
    for folder in answer_folders(work_dir):
        for path in sorted(folder.glob("p*.json")):
            try:
                page = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                merged["problems"].append(f"{path.name}: 读取失败 {exc}")
                continue
            text = page.get("raw_flat") or page.get("raw_text") or ""
            if "コース" not in text:
                continue
            parsed = parse_math_answers(text)
            for course, groups in parsed["courses"].items():
                merged["courses"].setdefault(course, {}).update(groups)
            # 2007 年前的转置版式只给得出「大題 → 字母 → 答案」，走 groups 这一路。
            for course, groups in (parsed.get("groups") or {}).items():
                for group, blanks in groups.items():
                    merged["groups"].setdefault(course, {}).setdefault(group, {}).update(blanks)
            merged["problems"].extend(f"{path.name}: {p}" for p in parsed["problems"])
    return merged, merged["problems"]
