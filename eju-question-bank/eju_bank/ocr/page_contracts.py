"""Turn what OCR read on a page into a page-contract draft for human review.

This is the link that was missing. The extraction chain produced honest content
but wrote a finished paper straight to the library, so the review workbench had
nothing to look at and no page was ever signed. A page contract is what the
workbench reads, edits and signs, and what the deterministic assembler consumes.

A draft written here is deliberately **unsignable**:

* ``needsReview`` is set, and :func:`eju_bank.review.sign_page` refuses a
  contract that carries it;
* ``issues`` records exactly what a person still has to establish — region
  evidence above all. OCR reads text, not page geometry, so it cannot say which
  detected ink region each block came from, and the signing gate requires that
  every region have exactly one block disposition.

So the draft carries the reading and names its own gaps. Signing stays a human
act, which is the whole point of the pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..constants import PAGE_CONTRACT_VERSION

# OCR gives no coordinates. A block still needs a bbox to satisfy the schema, so
# a draft gets this whole-body placeholder and says so in issues; the reviewer
# drags the real region in the workbench.
PLACEHOLDER_BBOX = [0.08, 0.08, 0.92, 0.92]

_ROLE_SUFFIX = {"QUESTION_BOOKLET": "question_booklet", "ANSWER_KEY": "answer_key"}


def contract_path(work_dir: Path, role: str, page: int) -> Path:
    return work_dir / "pages" / f"p{page:04d}-{_ROLE_SUFFIX.get(role, role.lower())}.json"


def _probe_page(work_dir: Path, role: str, page: int) -> dict[str, Any]:
    probe = work_dir / "probe.json"
    if not probe.is_file():
        return {}
    try:
        data = json.loads(probe.read_text(encoding="utf-8"))
    except Exception:
        return {}
    for entry in data.get("files", []):
        if entry.get("role") != role:
            continue
        for row in entry.get("pages", []):
            if row.get("page") == page:
                return row
    return {}


def build_page_contract(
    work_dir: Path,
    role: str,
    page: int,
    *,
    form_code: str | None,
    questions: list[dict[str, Any]],
    answers: dict[str, str] | None = None,
    math_questions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """One page's contract draft from the questions OCR read on that page.

    ``questions`` are entries from :func:`eju_bank.ocr.assemble_from_ocr.collect_questions`
    that belong to this page. An empty list yields an ``ignored`` block whose
    reason says the page held no readable question — which is a claim a reviewer
    still has to confirm against the scan, so it is an issue too.
    """
    answers = answers or {}
    probe = _probe_page(work_dir, role, page)
    blocks: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    order = 0

    def add_issue(code: str, message: str, ref: str | None = None) -> None:
        entry = {"severity": "error", "code": code, "message": message}
        if ref:
            entry["ref"] = ref
        issues.append(entry)

    # 同一页的多个子问共用一段材料，只放一次。
    shared = next((q.get("context") for q in questions if q.get("context")), None)
    if shared:
        order += 1
        blocks.append({
            "kind": "material",
            "localKey": f"p{page:04d}-material",
            "formCode": form_code or "",
            "groupCode": "OCR",
            "readingOrder": order,
            "contentAst": [{"type": "text", "value": shared}],
            "bbox": list(PLACEHOLDER_BBOX),
        })

    from .assemble_from_ocr import resolve_slot

    for item in questions:
        order += 1
        # 与组卷共用同一套欄号解析：两处若各写一份，早晚会漂移。
        slot = resolve_slot(item)
        answer_ref = f"{item.get('answer_prefix')}:{int(slot)}" if slot and item.get("answer_prefix") else ""
        local_key = f"p{page:04d}-q{order:02d}"
        block: dict[str, Any] = {
            "kind": "question",
            "localKey": local_key,
            "formCode": form_code or "",
            "groupCode": "OCR",
            "readingOrder": order,
            "printedLabel": item.get("label") or "",
            "bbox": list(PLACEHOLDER_BBOX),
            "stemAst": [{"type": "text", "value": item["stem"]}],
            "options": [
                {"key": key, "contentAst": [{"type": "text", "value": text}]}
                for key, text in (item.get("options") or {}).items()
            ],
            "answerSpec": {"type": "SINGLE_CHOICE"},
        }
        if answer_ref:
            block["answerRef"] = answer_ref
        else:
            add_issue("block.answer_ref_unknown",
                      f"{block['printedLabel'] or local_key}：没读到解答欄号，无法与正解表对应，"
                      "请对照原页填写 answerRef。", local_key)
        blocks.append(block)

        if answer_ref and answer_ref in answers:
            # 答案册里查到了；正确答案不写进页面合同（那是答案册的职责），
            # 但把它记下来让复核人知道这一题是可判分的。
            block.setdefault("notes", f"正解表 {answer_ref} = {answers[answer_ref]}")
        elif answer_ref:
            add_issue("block.answer_missing",
                      f"{block['printedLabel'] or local_key}：解答欄 {slot} 在正解表里查不到答案。",
                      local_key)

    # 数学：一個問占多個欄位，欄位由正解表给出，所以这里只记题干与题号，
    # 答案不进页面合同（那是答案册的职责）。
    for item in math_questions or []:
        order += 1
        suffix = f"-q{int(item['question']):02d}" if item["question"] else ""
        local_key = f"math-{item['group'].lower()}{suffix}"
        blocks.append({
            "kind": "question",
            "localKey": local_key,
            "formCode": form_code or "",
            "groupCode": item["group"],
            "readingOrder": order,
            "printedLabel": (f"{item['group']} 問{item['question']}" if item["question"]
                             else f"第{item['group']}問"),
            "answerRef": (f"{item['group']}:{item['question']}" if item["question"]
                          else item["group"]),
            "bbox": list(PLACEHOLDER_BBOX),
            "stemAst": [{"type": "text", "value": item["stem"]}],
            "options": [],
            "answerSpec": {"type": "DIGIT_GRID",
                           "slots": list(item.get("key_slots") or sorted(item["stem_letters"]))},
        })
        if not (item.get("key_slots") or item["stem_letters"]):
            add_issue("block.digit_slots_unknown",
                      f"{item['group']} 問{item['question'] or '（整题）'}："
                      "题干里没读到无歧义的欄位字母，请对照原页确认这一問的解答欄。", local_key)

    if not blocks:
        blocks.append({
            "kind": "ignored",
            "localKey": f"p{page:04d}-ignored",
            "readingOrder": 1,
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "reason": "OCR 未在此页读到题目；可能是说明页、空白页或版式未支持，待人工确认。",
        })
        add_issue("page.no_question_read",
                  "本页没有读到题目。请对照原页确认它确实不含题目，再登记为空白/非题目页。")

    # 区域证据只能由人给：OCR 读文字，不读页面几何。签署闸门要求每个区域恰好
    # 对应一个块的处置，所以这里绝不预填 regionIds。
    add_issue("page.region_evidence_required",
              f"区域证据待人工填写（PROBE 检出图像块 {probe.get('imageBlocks', '?')} 个，"
              f"墨量 {probe.get('inkRatio', '?')}）。请在复核台逐块指定来源区域 ID 与实际 bbox。")

    return {
        "schemaVersion": PAGE_CONTRACT_VERSION,
        "page": page,
        "sourceFileRole": role,
        "blocks": blocks,
        "coverage": {
            "inkRegions": int(probe.get("imageBlocks") or 0),
            "accountedRegions": 0,
        },
        "issues": issues,
        # sign_page 见到它就拒绝签署：草稿永远不能被当成已核对的内容。
        "needsReview": True,
    }
