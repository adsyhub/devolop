"""Page contracts the machine can attest, and the attestation itself.

:mod:`eju_bank.ocr.page_contracts` writes drafts that are deliberately
unsignable: they name their gaps and wait for a person. That is the right shape
for a reviewer working through a booklet by hand, and it is why nothing has ever
been published — 6514 booklet pages will not be hand-signed.

This module adds the other half. A page whose every element the machine can
*actually verify* gets a contract plus an attestation recording which checks
passed and against what evidence. A page with anything unverified stays a draft.

What an attestation claims, and nothing more:

``text.verbatim_ocr``
    each block's stem, its shared material, and every cell of its options appear
    verbatim in that page's cached OCR transcription, whose digest is recorded —
    the text was read, not composed. Options printed as a table row are stored
    with their column headings (``A 日本　B ドイツ``), so the check is per cell:
    the rendering arranges what was read, it does not add to it.
``answer.from_official_key``
    every question's ``answerRef`` resolves in the session's 正解表, whose
    digest is recorded — the answer came from the official key.
``answer.is_a_read_option``
    the keyed answer is one of the options OCR actually read on the page — the
    key and the page agree about what the choices are.
``coverage.text_order_only``
    region identities are text-order placeholders, **not** verified page
    geometry. OCR reads characters, not coordinates. This check exists to state
    the limitation inside the record rather than let the bbox imply otherwise.

A machine attestation is therefore strictly weaker than a human signature, says
so in the data, and never borrows the word. :meth:`eju_bank.review.ContentWorkspace.attest_page`
refuses a contract whose attestation does not re-derive from the workspace, and
a human signing the same page later replaces the attestation with the real
thing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..constants import PAGE_CONTRACT_VERSION
from ..util import digest_json, sha256_file
from .answer_key_contracts import PLACEHOLDER_BBOX, REGION_EVIDENCE
from .assemble_from_ocr import FORM_SECTIONS, SECTIONS, resolve_slot

GRADE = "MACHINE_VERIFIED"
ATTESTATION_VERSION = 2

# 检查项的登记表。证明里出现表外的 ID 一律不认 —— 一个没人实现过的检查名读起来
# 和真检查一样可信，这是伪造证明最省事的入口。
CHECK_REGISTRY = frozenset({
    "text.verbatim_ocr",
    "answer.from_official_key",
    # 答案值合法（正解在这道题读到的选项里）。必要，但**不**构成配对证据：
    # 所有题选项域相同时，错位配对同样通过。见 slot_join.distinguishes()。
    "answer.value_in_options",
    # 这道题的解答欄号有独立依据：原页印着的框号/题号，或经反验能分辨错位的
    # 顺序补号。发布必需。
    "answer.mapping_verified",
    "coverage.text_order_only",
})

# 旧名。留着是为了读得懂历史数据，但它不满足任何必需项：当初签发它的依据
# （选项域一致率）已被证明不能证明配对，所以带旧名的证明要重新评估，不能直接沿用。
LEGACY_CHECKS = frozenset({"answer.is_a_read_option"})

CHECKS = ("text.verbatim_ocr", "answer.from_official_key",
          "answer.value_in_options", "answer.mapping_verified",
          "coverage.text_order_only")

# 按角色登记的必需集合。缺一项就不发证明。
REQUIRED_CHECKS = {
    "QUESTION_BOOKLET": frozenset(CHECKS),
    "ANSWER_KEY": frozenset({"answer.from_official_key", "coverage.text_order_only"}),
}

# 算合同摘要时排除的字段：证明自身，以及不属于业务正文、由保存环节写入的东西。
# sourceFileHash 由 save_page 在合同建好之后才补上，放进摘要会让摘要永远对不上。
NOT_CONTENT = ("attestation", "sourceFileHash", "reviewedBy", "reviewedAt")


def _normalise(text: str) -> str:
    """Text in the form stems are built in, with whitespace collapsed away.

    The comparison has to happen in the block parser's own canonical form, or
    every stem containing a circled option marker would look like it came from
    nowhere: the parser rewrites ``$\\textcircled{1}$`` to ``①`` while reading.
    """
    from .question_blocks import canonical_text

    return "".join(canonical_text(str(text)).split())


def _cache_path(work_dir: Path, page: int) -> Path:
    return work_dir / "ocr_cache" / f"p{page:04d}.json"


def page_ocr_text(work_dir: Path, page: int) -> str:
    path = _cache_path(work_dir, page)
    if not path.is_file():
        return ""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    parts = [raw.get("raw_text") or "", raw.get("raw_passage") or "", raw.get("raw_flat") or ""]
    for block in raw.get("passage_ast") or []:
        if isinstance(block, dict) and block.get("value"):
            parts.append(str(block["value"]))
    return "\n".join(parts)


def contract_digest(contract: dict[str, Any]) -> str:
    """A digest over the business body of a page contract.

    This is what ties an attestation to the page it is about. Without it the
    attestation is a statement with no subject: it re-derives from itself, so
    the stem can be rewritten underneath it and it still "holds".

    The fields in :data:`NOT_CONTENT` are excluded — the attestation itself
    (which would be circular) and the bookkeeping that the save path writes
    after the contract is built. Everything a learner would see is included:
    stems, options, answer references, dispositions and region semantics.
    """
    return digest_json({k: v for k, v in contract.items() if k not in NOT_CONTENT})


def mapping_evidence(item: dict[str, Any]) -> str | None:
    """On what basis this question's 解答欄 number was established.

    Recorded per block so the answer at the end of the chain can be traced back
    to something printed on the page, rather than to a number the pipeline found
    convenient. ``None`` means there is no basis and the question cannot be
    attested.
    """
    if item.get("slotSource") == "SECTION_SEQUENCE":
        # slot_join 补的号。它只在错位的对手假设能被否掉时才补，见 distinguishes()。
        return "SECTION_SEQUENCE_DISTINGUISHED"
    section = item.get("section")
    if section in SECTIONS and SECTIONS[section][2]:
        # 这类小节把 問N 直接印成解答欄号，题号本身就是锚点。
        return "PRINTED_LABEL"
    if item.get("boxed_slot"):
        return "PRINTED_SLOT"
    if item.get("slot"):
        return "INLINE_SLOT"
    return None


def attestation(
    work_dir: Path, page: int, *, answer_cache: Path | None, checks: list[str],
    extra: dict[str, Any] | None = None, contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The record of what was verified for this page, and against what."""
    cache = _cache_path(work_dir, page)
    payload = {
        "schemaVersion": ATTESTATION_VERSION,
        "grade": GRADE,
        "checks": sorted(checks),
        "contractDigest": contract_digest(contract) if contract is not None else None,
        "regionEvidence": REGION_EVIDENCE,
        "evidence": {
            "ocrCache": cache.name if cache.is_file() else None,
            "ocrCacheSha256": sha256_file(cache) if cache.is_file() else None,
            "answerKeyCache": str(answer_cache) if answer_cache else None,
        },
        # 这条断言的边界，写在记录里面，而不是留给读者推断。
        "notAsserted": [
            "区域几何未验证：bbox 是整页正文占位，区域身份来自文字顺序。",
            "未经人工逐页与原页比对。",
        ],
    }
    if extra:
        payload.update(extra)
    payload["payloadDigest"] = digest_json(
        {k: v for k, v in payload.items() if k != "payloadDigest"})
    return payload


def build_question_contract(
    work_dir: Path, page: int, *, forms: list[str], items: list[dict[str, Any]],
    answers: dict[str, str], math_items: list[dict[str, Any]] | None = None,
    answer_cache: Path | None = None,
) -> dict[str, Any]:
    """One QUESTION_BOOKLET page contract, attested when fully verified.

    ``items`` are this page's entries from
    :func:`eju_bank.ocr.assemble_from_ocr.collect_questions`. Every printed
    question the machine cannot verify becomes an ``ignored`` block naming the
    reason, so the page still accounts for everything it shows; only the pages
    where nothing is left unexplained carry an attestation.
    """
    ocr_text = _normalise(page_ocr_text(work_dir, page))

    def span_text(item: dict[str, Any]) -> str:
        """The OCR of every page this question occupies.

        A question whose options run onto the next page has its text spread over
        both, so checking it against one page alone would report the second half
        as coming from nowhere.
        """
        pages = [int(n) for n in (item.get("pages") or []) if n] or [page]
        if pages == [page]:
            return ocr_text
        return _normalise("\n".join(page_ocr_text(work_dir, n) for n in pages))
    blocks: list[dict[str, Any]] = []
    region_ids: list[str] = []
    issues: list[dict[str, Any]] = []
    unverified: list[str] = []

    def add(block: dict[str, Any]) -> None:
        rid = f"p{page:04d}-text-{len(blocks) + 1:02d}"
        region_ids.append(rid)
        block["regionIds"] = [rid]
        block["bbox"] = list(PLACEHOLDER_BBOX)
        block["readingOrder"] = len(blocks) + 1
        blocks.append(block)

    shared = next((i.get("context") for i in items if i.get("context")), None)
    material_key: str | None = None
    if shared:
        # 材料块必须声明它属于哪个 form：同一本理科题册里物理/化学/生物是三个 form，
        # 一段共用材料只服务于印着它的那一节。
        section = next((i.get("section") for i in items if i.get("context")), None)
        prefix = SECTIONS.get(section or "", (None, None, None))[0]
        owner = next((f for f in forms if prefix and prefix in FORM_SECTIONS.get(f, set())), None)
        if not owner:
            issues.append({"severity": "error", "code": "block.material_form_unknown",
                           "message": f"共用材料所属小节「{section or '未知'}」对不上本卷任何 form。"})
        # 共用材料常常印在父題那一页，子問落到下一页。只核本页会把它判成"来自无处"，
        # 整页因此降级成草稿，连带丢掉这一页本来可发布的题。按用到它的那些題所占的
        # 页面来核。
        holders = [i for i in items if i.get("context") == shared]
        material_pages = sorted({int(n) for i in holders
                                 for n in (i.get("contextPages") or i.get("pages") or [page])})
        material_text = _normalise("\n".join(
            page_ocr_text(work_dir, n) for n in (material_pages or [page])))
        if material_text and _normalise(shared) not in material_text:
            issues.append({"severity": "error", "code": "block.text_not_in_ocr",
                           "message": "共用材料的文字在相关页面的 OCR 文本中找不到，"
                                      "无法断言逐字转写。"})
        material_key = f"p{page:04d}-material"
        add({"kind": "material", "localKey": material_key,
             "formCode": owner or "", "groupCode": "OCR",
             "contentAst": [{"type": "text", "value": shared}]})

    for item in items:
        section = item.get("section")
        prefix = SECTIONS.get(section or "", (None, None, None))[0]
        form = next((f for f in forms if prefix and prefix in FORM_SECTIONS.get(f, set())), None)
        label = item.get("label") or ""
        slot = resolve_slot(item)
        ref = f"{prefix}:{int(slot)}" if slot and prefix else ""
        answer = answers.get(ref) if ref else None
        options = item.get("options") or {}

        why = None
        if not form:
            why = f"小节「{section or '未知'}」不属于本卷的任何 form"
        elif not ref:
            why = "没读到解答欄号，无法与正解表对应"
        elif answer is None:
            why = f"解答欄 {slot} 在正解表里查不到答案"
        elif str(answer) not in options:
            why = f"正解表给的答案 {answer} 不在本页读到的选项里"
        elif not mapping_evidence(item):
            # 值合法不等于配对成立。没有印在原页上的锚点、也没有经反验的顺序补号
            # 的题，映射未验证 —— 收录它等于把一个没有依据的对应当成事实。
            why = "解答欄号没有独立依据（原页框号/题号缺失，顺序补号也未通过反验）"
        elif not item.get("stem"):
            why = "没读到题干"
        elif (text := span_text(item)) and _normalise(item["stem"]) not in text:
            why = "题干文字在它所占页面的 OCR 文本中找不到，无法断言逐字转写"
        else:
            # 选项也要核。表格型选项存成「A 日本　B ドイツ」，是把读到的格子按列名
            # 排好，没有添字，所以逐格核对 —— 整串核对会因为列名而必然失败。
            cells = item.get("option_cells") or {}
            span = span_text(item)
            stray = []
            for key, option_text in options.items():
                # 表格型选项核它读到的格子；普通选项核整串。
                pieces = cells.get(key) or [option_text]
                stray += [x for x in pieces
                          if _normalise(x) and _normalise(x) not in span]
            if span and stray:
                why = (f"有 {len(stray)} 个选项片段在本页 OCR 文本中找不到，"
                       "无法断言逐字转写")

        if why:
            unverified.append(f"{label or '（无题号）'}：{why}")
            add({"kind": "ignored", "localKey": f"p{page:04d}-unverified-{len(blocks) + 1:02d}",
                 "reason": f"{label or '（无题号）'}：{why}。本次发布不收录这一题。"})
            continue

        # 用到这段共用材料的子问要指名它。不指名的话，前端把「无人引用的材料」
        # 当作整组共用，于是那段对话会挂在同页每一道无关的题上面。
        refs_to_material = [material_key] if material_key and item.get("context") == shared else []
        add({"kind": "question", "localKey": f"p{page:04d}-q{len(blocks) + 1:02d}",
             "formCode": form, "sectionCode": SECTIONS[section][1], "groupCode": "OCR",
             "printedLabel": label or f"問{slot}", "answerRef": ref,
             "stemAst": [{"type": "text", "value": item["stem"]}],
             "options": [{"key": k, "contentAst": [{"type": "text", "value": v}]}
                         for k, v in options.items()],
             "answerSpec": {"type": "SINGLE_CHOICE"}, "materialRefs": refs_to_material,
             "answerRefEvidence": mapping_evidence(item)})

    for item in math_items or []:
        slots = list(item.get("key_slots") or [])
        group, question = item["group"], item["question"]
        ref = f"{group}:{question}" if question else group
        label = f"{group} 問{question}" if question else f"第{group}問"
        form = next((f for f in forms if f.startswith("MATHEMATICS")), None)
        # 一道数学大題的题干常常跨页印刷，解析器记下了它占的所有页。
        # 逐字校验要在这些页的文本上做，否则跨页题永远"在本页找不到"。
        spread = _normalise("\n".join(
            page_ocr_text(work_dir, int(n)) for n in (item.get("pages") or [page])))
        why = None
        if not form:
            why = "本卷没有数学 form"
        elif not slots:
            why = "正解表没有给出这一問的欄位"
        elif not item.get("stem"):
            why = "没读到题干"
        else:
            # 逐行核对：题干由这些原始行拼成，每一行都必须确实印在它所占的页上。
            missing = [line for line in (item.get("source_lines") or [])
                       if spread and _normalise(line) and _normalise(line) not in spread]
            if missing:
                why = (f"题干有 {len(missing)} 行在它所占页面的 OCR 文本中找不到，"
                       "无法断言逐字转写")
        if why:
            unverified.append(f"{label}：{why}")
            add({"kind": "ignored", "localKey": f"p{page:04d}-unverified-math-{len(blocks) + 1:02d}",
                 "reason": f"{label}：{why}。本次发布不收录这一題。"})
            continue
        add({"kind": "question", "localKey": f"math-{group.lower()}"
             + (f"-q{int(question):02d}" if question else ""),
             "formCode": form, "sectionCode": "MAIN", "groupCode": group,
             "printedLabel": label, "answerRef": ref,
             "stemAst": [{"type": "text", "value": item["stem"]}], "options": [],
             "answerSpec": {"type": "DIGIT_GRID", "slots": slots}, "materialRefs": []})

    if not blocks:
        add({"kind": "ignored", "localKey": f"p{page:04d}-ignored",
             "reason": "OCR 未在此页读到题目；可能是说明页、空白页或版式未支持，待人工确认。"})
        issues.append({"severity": "error", "code": "page.no_question_read",
                       "message": "本页没有读到题目。请对照原页确认它确实不含题目。"})

    has_question = any(b["kind"] == "question" for b in blocks)
    contract: dict[str, Any] = {
        "schemaVersion": PAGE_CONTRACT_VERSION,
        "page": page,
        "sourceFileRole": "QUESTION_BOOKLET",
        "blocks": blocks,
        "coverage": {
            "inkRegions": len(region_ids), "accountedRegions": len(region_ids),
            "regionIds": list(region_ids), "accountedRegionIds": list(region_ids),
            "regionEvidence": REGION_EVIDENCE,
        },
        "issues": issues,
    }
    if unverified:
        contract["excludedOnThisPage"] = unverified
    if issues or not has_question:
        # 有未解释的问题，或这一页没有一道可发布的题：保持草稿，不附证明。
        contract["needsReview"] = True
    else:
        contract["attestation"] = attestation(
            work_dir, page, answer_cache=answer_cache, checks=list(CHECKS),
            extra={"excludedOnThisPage": len(unverified)}, contract=contract)
    return contract


def attest_answer_key_contract(
    contract: dict[str, Any], work_dir: Path, *, answer_cache: Path | None
) -> dict[str, Any]:
    """Attach an attestation to an answer-key contract that has no open issues."""
    if contract.get("issues"):
        contract["needsReview"] = True
        return contract
    contract["attestation"] = attestation(
        work_dir, contract["page"], answer_cache=answer_cache,
        checks=["answer.from_official_key", "coverage.text_order_only"],
        contract=contract)
    return contract


def verify_attestation(contract: dict[str, Any], *,
                       work_dir: Path | None = None) -> list[str]:
    """Re-derive what the attestation claims. Returns the problems found.

    Three things have to hold, and only the first of them used to be checked:

    1. the attestation is internally consistent — its own digest re-derives;
    2. it is *about this contract* — ``contractDigest`` re-derives from the
       business body, so an edited stem or a swapped ``answerRef`` invalidates
       it. Self-consistency alone proves nothing: recomputing ``payloadDigest``
       after a forgery is one line;
    3. its evidence still exists and still has the content it recorded. Given
       ``work_dir``, the OCR cache is re-hashed and compared. A digest of a file
       nobody ever reads back is a decoration.

    The check set is closed: an ID outside :data:`CHECK_REGISTRY` is refused
    rather than ignored, and the role's required set must be present in full.
    """
    problems: list[str] = []
    att = contract.get("attestation")
    if not isinstance(att, dict):
        return ["合约没有附带机器证明"]
    if att.get("grade") != GRADE:
        problems.append(f"未知的证明等级 {att.get('grade')!r}")
    if att.get("regionEvidence") != REGION_EVIDENCE:
        problems.append("证明没有声明区域证据的性质")
    expected = digest_json({k: v for k, v in att.items() if k != "payloadDigest"})
    if att.get("payloadDigest") != expected:
        problems.append("证明内容与其摘要不一致")

    # ② 证明必须绑定这份合同的正文。
    bound = att.get("contractDigest")
    if not bound:
        problems.append("证明没有绑定合同正文（缺 contractDigest），无法判断它说的是哪一页")
    elif bound != contract_digest(contract):
        problems.append("合同正文与证明记录的摘要不一致：正文在签发之后被改过")

    # ③ 检查项集合是封闭的，且必须覆盖本角色的必需集合。
    listed = att.get("checks")
    if not isinstance(listed, list) or not listed:
        problems.append("证明没有列出任何检查项")
    else:
        unknown = sorted(set(listed) - CHECK_REGISTRY)
        legacy = sorted(set(listed) & LEGACY_CHECKS)
        if legacy:
            problems.append(
                "证明使用了已废止的检查项 " + "、".join(legacy)
                + "：它当初的依据不能证明题答配对，须按新策略重新评估")
        if [u for u in unknown if u not in LEGACY_CHECKS]:
            problems.append("证明列出了未登记的检查项 "
                            + "、".join(u for u in unknown if u not in LEGACY_CHECKS))
        required = REQUIRED_CHECKS.get(contract.get("sourceFileRole") or "")
        if required is None:
            problems.append(f"未知的页面角色 {contract.get('sourceFileRole')!r}")
        elif missing := sorted(required - set(listed)):
            problems.append("证明缺少本角色的必需检查项 " + "、".join(missing))

    # ④ 证据必须还在，而且内容没变。
    if work_dir is not None:
        recorded = (att.get("evidence") or {}).get("ocrCacheSha256")
        cache = _cache_path(Path(work_dir), int(contract.get("page") or 0))
        if recorded:
            if not cache.is_file():
                problems.append("证明引用的 OCR 缓存已经不在工作区里")
            elif sha256_file(cache) != recorded:
                problems.append("OCR 缓存的内容与证明记录的摘要不一致：证据在签发之后被改过")
        elif "text.verbatim_ocr" in (listed or []):
            problems.append("证明声称逐字转写，却没有记录所依据的 OCR 缓存摘要")
    if contract.get("needsReview"):
        problems.append("草稿合约不能附带证明")
    if contract.get("issues"):
        problems.append("仍有未解决的问题")
    coverage = contract.get("coverage") or {}
    if coverage.get("regionEvidence") != REGION_EVIDENCE:
        problems.append("coverage 没有声明区域证据的性质")
    region_ids = coverage.get("regionIds")
    if not isinstance(region_ids, list) or not region_ids:
        problems.append("coverage.regionIds 缺失")
        return problems
    used: list[str] = []
    for block in contract.get("blocks") or []:
        refs = block.get("regionIds") or ([block["regionId"]] if block.get("regionId") else [])
        if not refs:
            problems.append(f"块 {block.get('localKey')!r} 没有区域身份")
        used.extend(refs)
    if len(used) != len(set(used)) or set(used) != set(region_ids):
        problems.append("区域与块不是一一对应")
    return problems
