"""机器校验：把流水线已经读到的东西写成页面合同，并逐页记下机器证明。

这段判断原来只长在 ``scripts/attest_and_publish.py`` 里。制课台要走同一条路，
两处各写一份必然会分叉 —— 分叉的后果不是样式不一致，是同一套卷在命令行和
在页面上过的闸门不一样。所以判断搬进包里，脚本改为从这里 import，
两条路共用同一份实现。

机器证明比人的签名弱，而且它说得出自己弱在哪：卷子一路带着
``reviewGrade: MACHINE_ATTESTED`` 到学习者屏幕上。任何一处都没有设
``allow_synthetic``，也没有标 SYNTHETIC —— 它得满足和手签卷一样的复核证书要求。
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .audit import review_content_digest
from .constants import MACHINE_REVIEWER
from .ocr.answer_key_contracts import build_all as build_answer_contracts
from .ocr.answer_key_contracts import (
    above_run_answers, answer_ocr_folder, parse_pages as parse_answer_pages)
from .ocr.assemble_from_ocr import (
    DEFAULT_SECTION_BY_SUBJECT, MATH_FORMS, collect_questions)
from .ocr.attested_contracts import (
    CHECKS, attest_answer_key_contract, attestation, build_question_contract)
from .ocr.math_questions import collect_math_questions
from .ocr.slot_join import join_sections
from .ocr.verified_answers import load_math_answers
from .review import ContentWorkspace
from .util import canonical_json, stable_id


def human_locked(current: dict) -> bool:
    """Does this page carry human work that the pipeline must not overwrite?

    Two kinds, and the second is the one that used to be lost. A signature is
    obvious. A page a person edited and saved *without* signing is not obvious —
    it has no ``signed_by`` — and before revisions recorded their author it was
    indistinguishable from a machine draft, so the next automatic run replaced
    it. An unsigned draft is still somebody's work and still the more recent
    judgement about that page.

    Protection is not the same as qualification: see :func:`publishable`. A
    draft is kept, but it is not published on the strength of having been typed.
    """
    signed = current.get("signedBy")
    if signed and signed != MACHINE_REVIEWER:
        return True
    return current.get("actorKind") == "HUMAN"


def publishable(current: dict) -> bool:
    """Is this human-held page actually cleared for release?

    Only a real signature qualifies. An unsigned draft is protected from being
    overwritten and excluded from the published scope at the same time — those
    are different questions and collapsing them either destroys work or
    publishes unreviewed edits.
    """
    signed = current.get("signedBy")
    return bool(signed) and signed != MACHINE_REVIEWER


def already_cleared(current: dict, contract: dict) -> bool:
    """Is this machine-owned page already cleared with exactly this contract?

    Re-running the pipeline over a source that has not changed should be a
    no-op, not a fresh revision of every page: a new revision revokes the
    certificates built on the old one, so churn here means re-approving papers
    that nobody touched.

    Only about machine-owned pages. A human-held page is decided by
    :func:`human_locked` before this is asked — "not byte-identical to what the
    machine would write" is not a licence to overwrite a person's edit.
    """
    if current.get("signedBy") != MACHINE_REVIEWER or not contract.get("attestation"):
        return False
    stored = {k: v for k, v in (current.get("contract") or {}).items() if k != "sourceFileHash"}
    return canonical_json(stored) == canonical_json(contract)


def booklet_pages(work: Path) -> list[int]:
    return sorted(int("".join(c for c in p.stem if c.isdigit()))
                  for p in (work / "ocr_cache").glob("p*.json"))


def clear_source(workspace: ContentWorkspace, work: Path, manifest: dict, *,
                 verbose: bool = False) -> dict:
    """Write contracts and attest every page that fully verifies."""
    source_id = manifest["sourceId"]
    forms = list(manifest.get("expectedForms") or [])
    subject = manifest.get("subject") or ""
    # 答案与题目要在同一套判断下定稿，所以分三步走，而不是各读一遍：
    #   ① 把正解表整页解析出来，连缺口之上的条目一并留着当"提议"
    #   ② 用题册自己印的选项反验这些提议，以及反验按小节顺序补欄号的提议
    #   ③ 依裁决定稿答案合约，题目合约再用这同一套答案
    # 这两处反验共用一个依据：正解表给的答案必须在题册读到的选项里。配对错位时
    # 多数题会对不上，所以整段的一致率就是"没有错位"的证据。
    raw_contracts, trusted, _notes = parse_answer_pages(work, forms=forms)
    baseline_answers = {
        str(b["answerRef"]): str(b.get("correctOption") or "")
        for c in raw_contracts.values() for b in c["blocks"]
        if b.get("kind") == "answer-entry" and b.get("answerType") == "SINGLE_CHOICE"
        and int(str(b["answerRef"]).partition(":")[2] or 0) <= trusted.get(
            str(b["answerRef"]).partition(":")[0], 0)
    }
    provisional = above_run_answers(raw_contracts, trusted)

    math_answers: dict = {}
    if any(f in MATH_FORMS for f in forms):
        math_answers, _ = load_math_answers(work)

    items = collect_questions(work, default_section=DEFAULT_SECTION_BY_SUBJECT.get(subject))

    full_answers = {**baseline_answers,
                    **{f"{pre}:{slot}": ans
                       for pre, slots in provisional.items() for slot, ans in slots.items()}}
    accepted, filled, join_report = join_sections(items, full_answers, trusted)
    answer_contracts = build_answer_contracts(work, forms=forms,
                                              accepted_provisional=accepted,
                                              evidence=join_report)
    answers = {
        str(b["answerRef"]): str(b.get("correctOption") or "")
        for c in answer_contracts.values() for b in c["blocks"]
        if b.get("kind") == "answer-entry" and b.get("answerType") == "SINGLE_CHOICE"
    }
    by_page: dict[int, list[dict]] = defaultdict(list)
    for item in items:
        by_page[int(item["page"])].append(item)

    # 数学题的欄位必须与答案台账取自同一处。从 load_math_answers 取会出错：它跨页
    # 跨目录合并，而台账是逐页建的 —— 同一問的欄位分布在两页时，题目声明 8 格、
    # 台账只有 4 格，组卷的 "Digit answer must cover exact slots" 就会拦下整卷。
    math_tokens: dict[str, dict[str, str]] = {}
    for contract in answer_contracts.values():
        for block in contract["blocks"]:
            if block.get("kind") == "answer-entry" and block.get("answerType") == "DIGIT_GRID":
                math_tokens.setdefault(str(block["answerRef"]), {}).update(block.get("tokens") or {})
    math_by_page: dict[int, list[dict]] = defaultdict(list)
    if math_tokens:
        for item in collect_math_questions(work):
            ref = f"{item['group']}:{item['question']}" if item["question"] else item["group"]
            entry = dict(item, key_slots=list(math_tokens.get(ref) or {}))
            math_by_page[int(item["pages"][0])].append(entry)

    answer_cache = answer_ocr_folder(work)
    cleared: dict[str, list[int]] = {"QUESTION_BOOKLET": [], "ANSWER_KEY": []}
    stats = {"booklet_pages": 0, "booklet_attested": 0,
             "answer_pages": 0, "answer_attested": 0, "errors": [], "unchanged": 0,
             "provisional_accepted": sorted(accepted), "slots_filled": filled,
             "join_report": join_report,
             # 人工持有、本次自动流程没有碰的页。带签名的照旧进发布范围；
             # 只存了草稿的留着但不发布，并在这里说清楚。
             "human_held": [], "human_drafts": []}

    def handled_by_hand(role: str, page: int, current: dict) -> bool:
        """人工持有的页：保留原样，并按是否签署决定它进不进发布范围。"""
        if not human_locked(current):
            return False
        stats["human_held"].append({"role": role, "page": page,
                                    "signedBy": current.get("signedBy"),
                                    "authoredBy": current.get("authoredBy")})
        if publishable(current):
            cleared[role].append(page)
        else:
            stats["human_drafts"].append({"role": role, "page": page,
                                          "authoredBy": current.get("authoredBy")})
        return True

    for page in booklet_pages(work):
        contract = build_question_contract(
            work, page, forms=forms, items=by_page.get(page, []), answers=answers,
            math_items=math_by_page.get(page, []), answer_cache=answer_cache)
        stats["booklet_pages"] += 1
        try:
            current = workspace.read_page(source_id, "QUESTION_BOOKLET", page)
            if handled_by_hand("QUESTION_BOOKLET", page, current):
                continue
            if already_cleared(current, contract):
                # 与现有的已证明版本逐字相同：再存一遍只会多一个修订版。
                cleared["QUESTION_BOOKLET"].append(page)
                stats["booklet_attested"] += 1
                stats["unchanged"] += 1
                continue
            saved = workspace.save_page(source_id, "QUESTION_BOOKLET", page,
                                        contract, current["revisionId"],
                                        reviewer=MACHINE_REVIEWER)
            if contract.get("attestation"):
                workspace.attest_page(source_id, "QUESTION_BOOKLET", page, saved["revisionId"])
                cleared["QUESTION_BOOKLET"].append(page)
                stats["booklet_attested"] += 1
        except Exception as exc:
            stats["errors"].append(f"题册 p{page}: {type(exc).__name__}: {exc}")

    for page, contract in sorted(answer_contracts.items()):
        contract = attest_answer_key_contract(contract, work, answer_cache=answer_cache)
        stats["answer_pages"] += 1
        try:
            current = workspace.read_page(source_id, "ANSWER_KEY", page)
            if handled_by_hand("ANSWER_KEY", page, current):
                continue
            if already_cleared(current, contract):
                stats["answer_attested"] += 1
                stats["unchanged"] += 1
                if any(b["kind"] == "answer-entry" for b in contract["blocks"]):
                    cleared["ANSWER_KEY"].append(page)
                continue
            saved = workspace.save_page(source_id, "ANSWER_KEY", page,
                                        contract, current["revisionId"],
                                        reviewer=MACHINE_REVIEWER)
            if contract.get("attestation"):
                workspace.attest_page(source_id, "ANSWER_KEY", page, saved["revisionId"])
                stats["answer_attested"] += 1
                # 只有真带本卷答案条目的页才进发布范围：一页「别科答案，与本卷无关」
                # 是个诚实的处置，但它对这份卷的答案台账没有贡献。
                if any(b["kind"] == "answer-entry" for b in contract["blocks"]):
                    cleared["ANSWER_KEY"].append(page)
        except Exception as exc:
            stats["errors"].append(f"答案 p{page}: {type(exc).__name__}: {exc}")

    # 两道题争同一个解答欄时，没有任何依据能判断哪一道拥有它，配错就等于判错。
    # 两道都不收录，并在各自页面上写明理由 —— 组卷的唯一性闸门也正是这样要求的。
    owners: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for page in cleared["QUESTION_BOOKLET"]:
        contract = workspace.read_page(source_id, "QUESTION_BOOKLET", page)["contract"]
        for block in contract["blocks"]:
            if block.get("kind") == "question" and block.get("answerRef"):
                owners[f"{block.get('formCode')}|{block['answerRef']}"].append(
                    (page, block["localKey"]))
    contested = {k: v for k, v in owners.items() if len(v) > 1}
    if contested:
        pages = {page for holders in contested.values() for page, _ in holders}
        drop = {(page, key) for holders in contested.values() for page, key in holders}
        for page in sorted(pages):
            current = workspace.read_page(source_id, "QUESTION_BOOKLET", page)
            if human_locked(current):
                # 这一页归人。争用要报给人，不能由自动流程改写他的页面。
                stats.setdefault("contested_human_held", []).append(
                    {"role": "QUESTION_BOOKLET", "page": page})
                continue
            contract = dict(current["contract"])
            blocks = []
            dropped: list[str] = []
            for block in contract["blocks"]:
                if (page, block.get("localKey")) in drop:
                    reason = (f"{block.get('printedLabel') or block['localKey']}："
                              f"解答欄 {block['answerRef']} 同时被本卷的多道题读到，"
                              "无法确定它属于哪一道，这些题都不收录。")
                    dropped.append(reason)
                    blocks.append({
                        "kind": "ignored", "localKey": block["localKey"],
                        "bbox": block["bbox"], "regionIds": block["regionIds"],
                        "readingOrder": block.get("readingOrder"),
                        "reason": reason})
                else:
                    blocks.append(block)
            contract["blocks"] = blocks
            if not any(b["kind"] == "question" for b in blocks):
                cleared["QUESTION_BOOKLET"].remove(page)
                stats["booklet_attested"] -= 1
                continue
            # 正文刚被改过，证明必须跟着重新签发：它绑的是签发那一刻的正文摘要，
            # 原样留着会被 verify_attestation 判为「签发之后被改过」，于是整个来源
            # 一页都清不出来。重签是诚实的 —— 留下的题仍逐字出自本页 OCR、答案仍
            # 出自正解表，被拿掉的那些连同理由一并记进本页的排除清单。
            excluded = list(contract.get("excludedOnThisPage") or []) + dropped
            contract["excludedOnThisPage"] = excluded
            previous = contract.get("attestation") or {}
            contract["attestation"] = attestation(
                work, page, answer_cache=answer_cache,
                checks=list(previous.get("checks") or CHECKS),
                extra={"excludedOnThisPage": len(excluded)}, contract=contract)
            saved = workspace.save_page(source_id, "QUESTION_BOOKLET", page,
                                        contract, current["revisionId"],
                                        reviewer=MACHINE_REVIEWER)
            workspace.attest_page(source_id, "QUESTION_BOOKLET", page, saved["revisionId"])
        stats["contested"] = len(contested)

    stats["cleared"] = cleared
    stats["form_refs"] = {}
    for form in forms:
        seen = set()
        for page in cleared["QUESTION_BOOKLET"]:
            for block in workspace.read_page(source_id, "QUESTION_BOOKLET", page)["contract"]["blocks"]:
                if block.get("kind") == "question" and block.get("formCode") == form and block.get("answerRef"):
                    seen.add(block["answerRef"])
        # 题册上读到欄号、但正解表没有答案的题，也证明这个欄号存在。
        for item in items:
            from eju_bank.ocr.assemble_from_ocr import SECTIONS, resolve_slot, FORM_SECTIONS
            prefix = SECTIONS.get(item.get("section") or "", (None,))[0]
            slot = resolve_slot(item)
            if prefix and slot and prefix in FORM_SECTIONS.get(form, set()):
                seen.add(f"{prefix}:{int(slot)}")
        if seen:
            stats["form_refs"][form] = sorted(seen)
    return stats

def quarantine_questions(workspace: ContentWorkspace, manifest: dict, cleared: dict,
                         reasons: dict[str, str]) -> dict:
    """把隔离掉的题在页面合同里改成 ignored，并写下为什么。

    隔离不是把题删掉。规范 §6.5 说得很明确：每一道期望题目都必须有一种处置，
    解析失败不能改写成"本页没有这道题"。所以被隔离的题留在合同里，变成带理由的
    ``ignored`` 块 —— 页面仍然对它所显示的一切有交代，只是这一题不进本次发布。

    走的是和争用解答欄同一条路：改合同、重新证明、重新组装。人工持有的页不动，
    机器不能为了发布顺利去改人的页面。
    """
    source_id = manifest["sourceId"]
    excluded: list[str] = []
    skipped_human: list[dict] = []
    emptied: list[int] = []

    for page in list(cleared.get("QUESTION_BOOKLET") or []):
        current = workspace.read_page(source_id, "QUESTION_BOOKLET", page)
        contract = current["contract"]
        hits = []
        for block in contract.get("blocks") or []:
            if block.get("kind") != "question":
                continue
            qid = stable_id("q_", source_id, block.get("formCode"), block.get("localKey"))
            if qid in reasons:
                hits.append((block, qid))
        if not hits:
            continue
        if human_locked(current):
            # 这一页归人。隔离要报给人，不能由自动流程改写他的页面。
            skipped_human.append({"page": page,
                                  "questions": [qid for _b, qid in hits]})
            continue

        contract = dict(contract)
        drop = {block["localKey"] for block, _qid in hits}
        blocks = []
        for block in contract["blocks"]:
            if block.get("kind") == "question" and block.get("localKey") in drop:
                qid = stable_id("q_", source_id, block.get("formCode"), block["localKey"])
                blocks.append({
                    "kind": "ignored", "localKey": block["localKey"],
                    "bbox": block["bbox"], "regionIds": block["regionIds"],
                    "readingOrder": block.get("readingOrder"),
                    "reason": f"{block.get('printedLabel') or block['localKey']}："
                              f"{reasons[qid]} 本次发布不收录这一题。"})
                excluded.append(qid)
            else:
                blocks.append(block)
        contract["blocks"] = blocks
        contract.pop("attestation", None)
        if not any(b["kind"] == "question" for b in blocks):
            # 整页的题都被隔离了：这一页对本次发布没有贡献，退出发布范围。
            cleared["QUESTION_BOOKLET"].remove(page)
            emptied.append(page)
            continue
        contract["attestation"] = attestation(
            work_dir_of(workspace, source_id), page,
            answer_cache=None, checks=list(CHECKS),
            extra={"quarantined": sorted(drop)}, contract=contract)
        saved = workspace.save_page(source_id, "QUESTION_BOOKLET", page, contract,
                                    current["revisionId"], reviewer=MACHINE_REVIEWER)
        workspace.attest_page(source_id, "QUESTION_BOOKLET", page, saved["revisionId"])

    return {"excluded": sorted(set(excluded)), "emptiedPages": emptied,
            "humanHeld": skipped_human}


def work_dir_of(workspace: ContentWorkspace, source_id: str) -> Path:
    """这个来源的工作目录 —— 证明所引用的产物就放在那里。"""
    path, _manifest = workspace.source(source_id)
    return path.parent


def baseline_and_candidate(workspace: ContentWorkspace, manifest: dict, cleared: dict, *,
                           form_refs: dict | None = None,
                           reviewer: str = MACHINE_REVIEWER) -> dict:
    """签署结构基线并组装候选卷。停在"可以签整卷"这一步。

    拆出这一半是为了让制课台能在组装之后、签整卷之前读一遍卷子：疑点清单要在
    内容定稿前摆到人面前，签完再报就晚了。
    """
    source_id = manifest["sourceId"]
    forms = list(manifest.get("expectedForms") or [])
    structure, _paper, _ids = workspace.proposed_structure(
        source_id, cleared_pages=cleared, expected_forms=forms, form_refs=form_refs)
    workspace.sign_source_structure(source_id, structure, reviewer)
    scope, candidate, why = choose_scope(workspace, source_id)
    return {"structure": structure, "candidate": candidate, "scope": scope,
            "scopeReason": why,
            "contentDigest": review_content_digest(candidate["paper"])}


def choose_scope(workspace: ContentWorkspace, source_id: str) -> tuple[str, dict, str]:
    """够得上完整卷就发完整卷，够不上才发部分卷。

    自动发布原来写死 ``REVIEWED_PARTIAL``。那在当时是诚实的 —— 没有哪一套卷全都
    认得出来 —— 但它把"这一次没认全"变成了"这套卷永远是部分卷"：识别改好之后，
    同一批资料仍然只能发部分卷，因为没有任何一条路会去试完整卷。

    完整性不由这里判断。``candidate(scope="FULL")`` 已经把门禁写全了：正解表列出
    的每一个解答欄都要有题目收录、页数要对得上、听力要有音轨、结构基线要匹配。
    所以直接试一次 —— 过了就是真的完整，没过就带着原因退回部分卷。
    """
    from .errors import ContractError, QualityGateError

    try:
        candidate = workspace.candidate(source_id, "FULL")
        return "FULL", candidate, "正解表列出的解答欄全部收录，完整性门禁全部通过。"
    except (QualityGateError, ContractError) as exc:
        why = f"未达完整卷条件（{type(exc).__name__}: {str(exc)[:200]}），按已验证范围发部分卷。"
    return "REVIEWED_PARTIAL", workspace.candidate(source_id, "REVIEWED_PARTIAL"), why


def approve_and_publish(workspace: ContentWorkspace, source_id: str, candidate: dict,
                        content_digest: str, *, channel: str,
                        scope: str = "REVIEWED_PARTIAL",
                        reviewer: str = MACHINE_REVIEWER) -> dict:
    """签署整卷并发布已组装的范围。``scope`` 必须与组装候选时用的一致。"""
    review = workspace.approve_paper(source_id, content_digest, reviewer, True, scope)
    result = workspace.publish_review(review["reviewId"], channel)
    return {"paperId": result["paperId"], "paperVersionId": result["paperVersionId"],
            "version": result["version"],
            "questions": candidate["paper"].get("questionCount"),
            "grade": candidate["paper"].get("reviewGrade"),
            "completeness": candidate["paper"].get("completeness")}


def publish_source(workspace: ContentWorkspace, manifest: dict, cleared: dict, *,
                   channel: str, form_refs: dict | None = None) -> dict:
    """Baseline, assemble, approve and publish what was cleared."""
    staged = baseline_and_candidate(workspace, manifest, cleared, form_refs=form_refs)
    return approve_and_publish(workspace, manifest["sourceId"], staged["candidate"],
                               staged["contentDigest"], channel=channel,
                               scope=staged["scope"])
