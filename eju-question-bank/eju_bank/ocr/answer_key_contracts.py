"""Turn the OCR'd 正解表 into per-page ``answer-entry`` page contracts.

:meth:`eju_bank.review.ContentWorkspace.candidate` builds a release's answer
ledger from the signed ``ANSWER_KEY`` page contracts and nowhere else, which is
the right rule — a paper's answers should come from the same reviewed evidence
as its questions, not from a parallel side channel. The OCR chain, though, read
the 正解表 into ``answer_ocr/pNNNN.json`` and handed the refs straight to the
assembler, so no answer page ever became a contract and no release could be
assembled.

This module closes that gap. Each answer-key page is parsed on its own so every
entry records the page it was actually read from, and only the sections that
belong to this source's forms are emitted — a session's key covers all four
subject groups, and a physics release has no business carrying 日本語 answers.

What the blocks claim is deliberately narrow. Region identities are
text-order placeholders, not verified page geometry: OCR reads characters, not
coordinates, so the contract says ``regionEvidence: TEXT_ORDER_ONLY`` and keeps
the whole-body placeholder bbox. Nothing here asserts where on the page an
answer sits; it asserts only which answer the page states, which is what the
ledger needs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..constants import PAGE_CONTRACT_VERSION
from .assemble_from_ocr import FORM_SECTIONS, MATH_FORMS

# OCR 不给坐标。块仍需一个 bbox 满足 schema，就用整页正文占位，并在合约里说明。
PLACEHOLDER_BBOX = [0.08, 0.08, 0.92, 0.92]
REGION_EVIDENCE = "TEXT_ORDER_ONLY"


def contract_path(work_dir: Path, page: int) -> Path:
    return work_dir / "pages" / f"p{page:04d}-answer_key.json"


def _page_number(path: Path) -> int:
    digits = "".join(c for c in path.stem if c.isdigit())
    return int(digits) if digits else 0


def form_for_prefix(prefix: str, forms: list[str]) -> str | None:
    """Which of this source's forms owns an answer-key section prefix."""
    for form in forms:
        if prefix in FORM_SECTIONS.get(form, set()):
            return form
    return None


def parse_one_capture(raw: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any], list[str]]:
    """One *capture* of an answer page: ``(choice refs, math parse, problems)``.

    Both readings of the page are used, exactly as
    :func:`eju_bank.ocr.verified_answers.load_verified_answers` does: the flat
    capture carries the section headings printed outside the table markup, the
    structured capture carries the merged header cells. The structured reading
    wins where both speak.
    """
    from . import answer_key as flat
    from . import answer_table as structured
    from .math_answers import parse_math_answers

    html = raw.get("raw_text", "") or ""
    text = raw.get("raw_flat") or ("" if "<table" in html.lower() else html)
    refs: dict[str, str] = {}
    problems: list[str] = []

    # 同一页有两套互不依赖的读法：扁平文本和表格结构。把它们当成互相校验的两次
    # 独立测量 —— 都读到同一欄而答案不同时，谁也不能仲裁，那一欄就不采用。这比
    # 让其中一方无条件覆盖另一方可靠得多：覆盖只会让错的那个安静地赢。
    flat_refs: dict[str, str] = {}
    table_refs: dict[str, str] = {}
    if text:
        try:
            parsed = flat.parse_answer_key(text)
            flat_refs = flat.to_answer_refs(parsed)
            problems.extend(f"文本: {p}" for p in parsed.get("problems", []))
        except Exception as exc:
            problems.append(f"文本: 解析失败 {exc}")
    if "<table" in html.lower():
        try:
            parsed = structured.parse_answer_tables(
                html, default_section=structured.heading_in_text(text),
                section_order=structured.headings_in_text(text))
            table_refs = structured.to_answer_refs(parsed)
            problems.extend(f"表格: {p}" for p in parsed.get("problems", []))
        except Exception as exc:
            problems.append(f"表格: 解析失败 {exc}")
    refs.update(table_refs)
    refs.update(flat_refs)
    for ref in set(flat_refs) & set(table_refs):
        if flat_refs[ref] != table_refs[ref]:
            refs.pop(ref, None)
            prefix = ref.partition(":")[0]
            problems.append(
                f"{prefix}: 解答欄 {ref.partition(':')[2]} 两种读法不一致"
                f"（文本 {flat_refs[ref]} / 表格 {table_refs[ref]}），这一欄不采用")

    math: dict[str, Any] = {"courses": {}, "problems": []}
    flat_text = raw.get("raw_flat") or raw.get("raw_text") or ""
    if "コース" in flat_text:
        try:
            math = parse_math_answers(flat_text)
            problems.extend(f"数学: {p}" for p in math.get("problems", []))
        except Exception as exc:
            problems.append(f"数学: 解析失败 {exc}")
    return refs, math, problems


def parse_answer_page(raws: list[dict[str, Any]] | dict[str, Any]
                      ) -> tuple[dict[str, str], dict[str, Any], list[str]]:
    """One answer page read from every capture there is, merged by agreement.

    A page is transcribed twice at different resolutions (see
    ``scripts/reocr_answer_keys.py``): the 180 dpi pass these tables were first
    read at drops digits out of dense numeric rows, and a 400 dpi pass of the
    same page recovers them — one 読解 section went from 15 answers for 16
    解答欄 to 16 for 16.

    The captures are treated as independent measurements, not as a preferred
    source and a fallback. A 解答欄 only one capture read is taken from it; a
    解答欄 both read and disagree about is taken from neither, because nothing
    here can adjudicate and a wrong answer marks a correct answer wrong. So a
    second capture can add slots or withdraw doubtful ones, never silently
    replace one answer with another.
    """
    if isinstance(raws, dict):
        raws = [raws]
    per_capture: list[dict[str, str]] = []
    math: dict[str, Any] = {"courses": {}, "problems": []}
    problems: list[str] = []
    for index, raw in enumerate(raws):
        refs, one_math, one_problems = parse_one_capture(raw)
        per_capture.append(refs)
        label = f"{raw.get('ocrDpi') or 180}dpi"
        problems.extend(f"{label} {p}" for p in one_problems)
        for course, groups in (one_math.get("courses") or {}).items():
            math["courses"].setdefault(course, {}).update(groups)
    merged: dict[str, str] = {}
    for refs in per_capture:
        merged.update(refs)
    for ref in set().union(*per_capture) if per_capture else set():
        values = {refs[ref] for refs in per_capture if ref in refs}
        if len(values) > 1:
            merged.pop(ref, None)
            problems.append(
                f"{ref.partition(':')[0]}: 解答欄 {ref.partition(':')[2]} 两次识别给出不同的正解"
                f"（{sorted(values)}），这一欄不采用")
    return merged, math, problems


def build_answer_key_contract(
    page: int, raws: list[dict[str, Any]] | dict[str, Any], *, forms: list[str]
) -> dict[str, Any]:
    """One ANSWER_KEY page contract carrying only this source's forms' answers."""
    refs, math, problems = parse_answer_page(raws)
    blocks: list[dict[str, Any]] = []
    region_ids: list[str] = []
    issues: list[dict[str, Any]] = []
    other_subjects = 0

    def region(order: int) -> str:
        rid = f"p{page:04d}-text-{order:02d}"
        region_ids.append(rid)
        return rid

    def add(block: dict[str, Any]) -> None:
        block["regionIds"] = [region(len(blocks) + 1)]
        block["bbox"] = list(PLACEHOLDER_BBOX)
        blocks.append(block)

    for ref in sorted(refs, key=lambda r: (r.split(":")[0], int(r.split(":")[1]))):
        prefix = ref.split(":")[0]
        form = form_for_prefix(prefix, forms)
        if not form:
            other_subjects += 1
            continue
        add({"kind": "answer-entry", "formCode": form, "answerRef": ref,
             "answerType": "SINGLE_CHOICE", "correctOption": str(refs[ref])})

    math_forms = [f for f in forms if f in MATH_FORMS]
    for form in math_forms:
        course = form.rsplit("_", 1)[0] if form.endswith(("_JA", "_EN")) else form
        for (group, question), blanks in sorted(
                (math.get("courses", {}).get(course) or {}).items()):
            if not blanks:
                continue
            ref = f"{group}:{question}" if question else group
            add({"kind": "answer-entry", "formCode": form, "answerRef": ref,
                 "answerType": "DIGIT_GRID",
                 "tokens": {str(k): str(v) for k, v in blanks.items()}})

    if other_subjects:
        # 同回次的正解表覆盖四个科目群。别科的段落在这一页上真实存在，
        # 必须有一个处置，而不是默默当它不存在。
        add({"kind": "ignored", "localKey": f"p{page:04d}-other-subjects",
             "reason": f"本页还有 {other_subjects} 条属于其他科目群的答案；"
                       "本卷只登记自己 form 的小节，其余由对应科目的卷登记。"})

    if not blocks:
        add({"kind": "ignored", "localKey": f"p{page:04d}-no-answers",
             "reason": "本页没有读到属于本卷的答案条目（可能是封面、说明或别科页）。"})
        issues.append({"severity": "error", "code": "page.no_answer_read",
                       "message": "本页未读到本卷的答案条目，待人工确认它确实不含本卷答案。"})

    # 一页正解表同时印着四个科目群，也同时印着本卷的几个小节。一条抱怨只说明
    # 它所指的那一个小节没读好，既不牵连别科，也不牵连同页的其他小节。所以按
    # 小节记账：谁出问题就丢谁的条目（在 build_all 里统一执行），整页不因此作废。
    notes: list[str] = []
    disputes: dict[str, list[str]] = {}
    for problem in problems:
        prefix = problem_section(problem)
        if prefix and any(prefix in FORM_SECTIONS.get(f, set()) for f in forms):
            disputes.setdefault(prefix, []).append(problem)
        elif prefix is None and _unattributable_is_ours(problem, forms):
            # 连它说的是哪一段都读不出来，又可能与本卷有关：按本卷所有小节存疑处理
            # 会把整卷清空，代价过大；记为备注，由解答欄连续性校验兜底。
            notes.append(problem)
        else:
            notes.append(problem)

    return {
        "schemaVersion": PAGE_CONTRACT_VERSION,
        "page": page,
        "sourceFileRole": "ANSWER_KEY",
        "otherSubjectNotes": notes,
        "sectionDisputes": {k: v for k, v in disputes.items()},
        "blocks": blocks,
        "coverage": {
            "inkRegions": len(region_ids),
            "accountedRegions": len(region_ids),
            "regionIds": list(region_ids),
            "accountedRegionIds": list(region_ids),
            # 区域身份来自文字顺序，不是检出的页面几何。写明白，不让读者误解。
            "regionEvidence": REGION_EVIDENCE,
        },
        "issues": issues,
    }


def problem_section(problem: str) -> str | None:
    """Which printed section a parser complaint is about, if it names one.

    Complaints carry the heading in one of their colon-separated segments
    (``文本: 読解: 题号 16 个与答案 15 个不匹配``), so each segment is tried against
    the heading table.
    """
    from .answer_key import section_prefix

    for segment in (part.strip() for part in re.split(r"[：:]", str(problem))):
        if not segment:
            continue
        prefix = section_prefix(segment)
        if prefix:
            return prefix
    return None


def _unattributable_is_ours(problem: str, forms: list[str]) -> bool:
    """Could a complaint that names no section still concern these forms?"""
    if "コース" in str(problem) or "数学" in str(problem):
        return any(form in MATH_FORMS for form in forms)
    return True


_UNREADABLE_SLOT = re.compile(r"解答番号\s*(\d+)\s*的正解读不出")


def explained_gaps(contracts: dict[int, dict[str, Any]]) -> dict[str, set[int]]:
    """Slots the parser reported as present-but-unreadable, per section.

    ``物理 解答番号 4 的正解读不出`` says the 解答欄 label was read and its answer
    cell was not. That is a missing answer, not a misread one, and it explains a
    gap in the slot run without implying anything shifted.
    """
    out: dict[str, set[int]] = {}
    for contract in contracts.values():
        for prefix, problems in (contract.get("sectionDisputes") or {}).items():
            for problem in problems:
                found = _UNREADABLE_SLOT.search(str(problem))
                if found:
                    out.setdefault(prefix, set()).add(int(found.group(1)))
    return out


# 一个小节的解答欄不从 1 起，实测只有一种版式：聴読解与聴解印在同一张正解表上
# 连号（聴読解 1–12、聴解 13–27）。写成明表，而不是「接在任何小节后面都行」——
# 后者会把某个小节开头被漏读的情形也一并放行，那正是 run-from-1 要拦的东西。
SECTION_CONTINUES = {"LISTENING": "LISTENING_COMPREHENSION"}


def _run_start(prefix: str, found: set[int], all_slots: dict[str, set[int]]) -> int:
    """一个小节的可信连续段允许从哪个解答欄号开始。

    通常是 1：EJU 的解答欄按小节从 1 编号，段落起点高于 1 正是「开头的欄号被
    漏读」的特征，而那恰恰是这道检查要拦的。

    例外只有连号的聴解：它的首号由文档自己说出 —— 必须正好等于聴読解最后一个
    解答欄加一。若聴解自己的首行被漏读，它会从加二处开始，这条检查照样拒绝。
    """
    low = min(found)
    if low == 1:
        return 1
    previous = all_slots.get(SECTION_CONTINUES.get(prefix) or "")
    if previous and max(previous) + 1 == low:
        return low
    return 1


def trusted_runs(contracts: dict[int, dict[str, Any]],
                 explained: dict[str, set[int]] | None = None,
                 ) -> tuple[dict[str, int], dict[str, str]]:
    """How far each answer section can be trusted, and why it stops there.

    Every way the answer-key parsers can fail discards the row it was reading
    rather than guessing, so a complaint never yields a *wrong* answer — only a
    missing one. One dangerous case survives that discipline: if OCR loses a
    解答欄 label and an answer cell from the same row, the counts still agree and
    the surviving labels pair with the wrong answers. A lost label always leaves
    a hole in the slot numbering, and EJU numbers each section's 解答欄 from 1
    without holes, so the run from 1 to the first *unexplained* hole is sound and
    anything above it is not.

    Holes the parser explained — a slot whose answer cell it says it could not
    read — are stepped over: the label was read there, so nothing shifted.

    Returns ``({prefix: highest trusted slot}, {prefix: why it stops})``.
    """
    explained = explained or {}
    slots: dict[str, set[int]] = {}
    for contract in contracts.values():
        for block in contract.get("blocks", []):
            if block.get("kind") != "answer-entry" or block.get("answerType") != "SINGLE_CHOICE":
                continue
            prefix, _, slot = str(block.get("answerRef") or "").partition(":")
            if slot.isdigit():
                slots.setdefault(prefix, set()).add(int(slot))
    trusted, notes = {}, {}
    for prefix, found in slots.items():
        skip = explained.get(prefix, set())
        start = _run_start(prefix, found, slots)
        limit = start - 1
        while limit + 1 in found or limit + 1 in skip:
            limit += 1
        trusted[prefix] = limit
        if limit < max(found):
            notes[prefix] = (
                f"正解表的「{prefix}」段从 {start} 连续到 {limit}（空缺的 {sorted(skip & set(range(start, limit + 1)))[:4] or '无'} "
                f"是正解表自己没印清、解析器已报告的）；第 {limit + 1} 号既没读到也没有说明，"
                f"而更大的号（最大 {max(found)}）仍有读到。解答欄号本应自 {start} 起连续，"
                f"无法解释的缺口说明有欄号丢失，它之后的号可能与答案错位，因此只采用前 {limit} 个。")
    return trusted, notes


def drop_untrusted(contract: dict[str, Any], trusted: dict[str, int],
                   notes: dict[str, str], accepted: set[str] | None = None,
                   evidence: dict[str, str] | None = None) -> dict[str, Any]:
    """Resolve the answer entries above each section's trusted run.

    A section named in ``accepted`` keeps them, flagged for what they are: the
    caller confirmed them against the booklet's own printed options (see
    :mod:`eju_bank.ocr.slot_join`), which is independent evidence that nothing
    shifted across the hole. Every other section drops them with the reason.
    """
    accepted = accepted or set()
    kept, dropped, held = [], {}, {}
    for block in contract.get("blocks", []):
        prefix, _, slot = str(block.get("answerRef") or "").partition(":")
        above = (block.get("kind") == "answer-entry"
                 and block.get("answerType") == "SINGLE_CHOICE"
                 and slot.isdigit() and int(slot) > trusted.get(prefix, 0))
        if above and prefix not in accepted:
            dropped[prefix] = dropped.get(prefix, 0) + 1
            continue
        if above:
            # 这一条在欄号缺口之上，靠题册选项反验才被采用。照实标注，不混进
            # "正解表直接读出" 的那一类里。
            block = {**block, "answerEvidence": "ABOVE_RUN_CONFIRMED_BY_BOOKLET"}
            held[prefix] = held.get(prefix, 0) + 1
        kept.append(block)
    if held:
        contract["provisionalSections"] = {
            prefix: (evidence or {}).get(prefix, "题册选项反验通过") for prefix in held}
    if not dropped:
        contract["blocks"] = kept
        return contract
    page = contract["page"]
    for prefix, count in sorted(dropped.items()):
        kept.append({"kind": "ignored", "localKey": f"p{page:04d}-untrusted-{prefix.lower()}",
                     "reason": f"本页「{prefix}」段有 {count} 条答案不采用。"
                               + notes.get(prefix, "解答欄号不连续，无法确认对应关系。"),
                     "bbox": list(PLACEHOLDER_BBOX)})
    region_ids = []
    for order, block in enumerate(kept, 1):
        rid = f"p{page:04d}-text-{order:02d}"
        block["regionIds"] = [rid]
        block["readingOrder"] = order
        region_ids.append(rid)
    contract["blocks"] = kept
    contract["coverage"] = {**contract["coverage"], "inkRegions": len(region_ids),
                            "accountedRegions": len(region_ids), "regionIds": region_ids,
                            "accountedRegionIds": list(region_ids)}
    return contract


def answer_ocr_folder(work_dir: Path) -> Path | None:
    """The OCR cache for this source's registered ANSWER_KEY bytes.

    A session's key is one document; sources that had it registered for them
    read the session owner's cache, which is the same file's transcription.
    """
    from .verified_answers import answer_folders

    for folder in answer_folders(work_dir):
        if any(folder.glob("p*.json")):
            return folder
        high = folder.parent / (folder.name + "_hi")
        if high.is_dir() and any(high.glob("p*.json")):
            return folder
    return None


def captures(work_dir: Path, page: int) -> list[dict[str, Any]]:
    """Every transcription of one answer-key page, coarse pass first."""
    from .verified_answers import answer_folders

    out: list[dict[str, Any]] = []
    for folder in answer_folders(work_dir):
        for name in (folder, folder.parent / (folder.name + "_hi")):
            path = name / f"p{page:04d}.json"
            if path.is_file():
                try:
                    out.append(json.loads(path.read_text(encoding="utf-8")))
                except Exception:
                    continue
        if out:
            break
    return out


def parse_pages(work_dir: Path, *, forms: list[str]
                ) -> tuple[dict[int, dict[str, Any]], dict[str, int], dict[str, str]]:
    """Every cached answer page parsed, plus the run analysis, before any dropping."""
    folder = answer_ocr_folder(work_dir)
    if not folder:
        return {}, {}, {}
    # 页号要从两次识别的目录取并集：某些页只有高分辨率那一遍读到了
    # （粗读那次漏掉了），只按粗读目录枚举就永远看不到它们。
    numbers = {n for d in (folder, folder.parent / (folder.name + "_hi"))
               if d.is_dir() for path in d.glob("p*.json")
               if (n := _page_number(path))}
    out: dict[int, dict[str, Any]] = {}
    for page in sorted(numbers):
        raws = captures(work_dir, page)
        if not raws:
            continue
        out[page] = build_answer_key_contract(page, raws, forms=forms)
    # 解析器报告的逐欄缺失是"已解释的缺口"：标签读到了、答案格没读出来，不蕴含错位。
    trusted, notes = trusted_runs(out, explained_gaps(out))
    return out, trusted, notes


def above_run_answers(contracts: dict[int, dict[str, Any]], trusted: dict[str, int]
                      ) -> dict[str, dict[int, str]]:
    """``{prefix: {slot: answer}}`` for the entries that sit above each trusted run.

    These are the answers the run check stops at. They are not wrong by
    construction — a hole in the numbering only means a *possible* shift — so
    they are offered for the booklet cross-check rather than thrown away
    unexamined.
    """
    out: dict[str, dict[int, str]] = {}
    for contract in contracts.values():
        for block in contract.get("blocks", []):
            if block.get("kind") != "answer-entry" or block.get("answerType") != "SINGLE_CHOICE":
                continue
            prefix, _, slot = str(block.get("answerRef") or "").partition(":")
            if slot.isdigit() and int(slot) > trusted.get(prefix, 0):
                out.setdefault(prefix, {})[int(slot)] = str(block.get("correctOption") or "")
    return out


def build_all(work_dir: Path, *, forms: list[str],
              accepted_provisional: set[str] | None = None,
              evidence: dict[str, str] | None = None) -> dict[int, dict[str, Any]]:
    """``{page: contract}`` for every cached answer-key page, run-check applied.

    ``accepted_provisional`` names the sections whose above-the-run answers the
    caller has confirmed against the booklet; without it the run check truncates
    as before.
    """
    out, trusted, notes = parse_pages(work_dir, forms=forms)
    for page in list(out):
        out[page] = drop_untrusted(out[page], trusted, notes,
                                   accepted_provisional, evidence)
    return out
