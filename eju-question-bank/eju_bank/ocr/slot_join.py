"""Join booklet questions to 正解表 slots, verified against the booklet itself.

Two of the pipeline's biggest losses come from the same conservatism. A section
whose 解答欄 numbering has one unexplained hole had *everything above the hole*
discarded, because a lost 解答欄 label can shift the pairing and a shifted answer
marks a correct answer wrong. And a page whose boxed margin numbers did not count
out exactly against the questions parsed on it got no slots at all, for the same
reason. Between them that is most of what the bank is still missing.

Both refusals were made blind. There is an independent check available: **the
answer the key gives must be one of the options the booklet printed for that
question.** A correct pairing passes it almost always — measured across 2255
published questions, only 7 failed.

But passing it is not on its own evidence about the *pairing*, and an earlier
version of this module treated it as if it were. The check only discriminates
when different questions printed different option sets. Where every question
offers 1–4 and every keyed answer is one of 1–4 — the common case — a pairing
shifted by one agrees exactly as well as the true one. A section of four such
questions scores 4/4 either way, so 4/4 says nothing.

So the evidence is split in two, and both halves are required:

``answer.value_in_options``
    the keyed answer is one of the options read for that question. Necessary:
    a pairing that fails it is wrong. Not sufficient: passing it may be free.
``answer.mapping_verified``
    the same test, applied to the shifted rivals this section is at risk of.
    The pairing is witnessed only when every rival *fails* — that is, only when
    the booklet's option sets could actually have told them apart.

Where the margin numbers were read, a proposal must also reproduce them
exactly; those are printed on the page and they are the strongest anchor here.

Nothing here relaxes what reaches a learner: a section that cannot clear both
halves is dropped exactly as before, and what it achieved is recorded.
"""

from __future__ import annotations

from typing import Any

from .assemble_from_ocr import SECTIONS, resolve_slot

# 少于这么多道题可核，就没有统计意义，按老规矩丢弃。
MIN_CHECKABLE = 3
# 整段通过率门槛：留一道的余量给 OCR 把某个选项读漏的情况。
# 这个门槛本身不构成配对证据 —— 那要看错位的对手假设能不能被同一个检查否掉，
# 见 distinguishes()。
MIN_RATE = 0.9


def _prefix(item: dict[str, Any]) -> str | None:
    return SECTIONS.get(item.get("section") or "", (None, None, None))[0]


def by_section(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Questions grouped by answer-key section, kept in printed order."""
    out: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        prefix = _prefix(item)
        if prefix:
            out.setdefault(prefix, []).append(item)
    return out


def option_agreement(
    pairs: list[tuple[dict[str, Any], str]], answers: dict[str, str]
) -> tuple[int, int]:
    """How many proposed (question, ref) pairs the booklet's own options confirm.

    Returns ``(confirmed, checkable)``. A pair is checkable only when the key has
    an answer for that ref and the booklet read options for that question; other
    pairs say nothing either way and are not counted in the denominator.
    """
    confirmed = checkable = 0
    for item, ref in pairs:
        answer = answers.get(ref)
        options = item.get("options") or {}
        if answer is None or not options:
            continue
        checkable += 1
        if str(answer) in options:
            confirmed += 1
    return confirmed, checkable


def passes(confirmed: int, checkable: int) -> bool:
    """Did the *values* agree well enough? Says nothing about the pairing."""
    return checkable >= MIN_CHECKABLE and confirmed >= MIN_RATE * checkable


def shifted_rivals(
    pairs: list[tuple[dict[str, Any], str]]
) -> list[list[tuple[dict[str, Any], str]]]:
    """The misalignments this section is actually at risk of.

    The risk being guarded against is a lost or doubled 解答欄 label, which
    slides the questions against the refs from that point on. So the rivals are
    the same questions and the same refs, offset — in both directions, since a
    doubled label shifts the opposite way from a dropped one.
    """
    items = [item for item, _ref in pairs]
    refs = [ref for _item, ref in pairs]
    rivals = []
    for shift in range(1, len(pairs)):
        overlap = len(pairs) - shift
        rivals.append([(items[i], refs[i + shift]) for i in range(overlap)])
        rivals.append([(items[i + shift], refs[i]) for i in range(overlap)])
    return rivals


def distinguishes(
    pairs: list[tuple[dict[str, Any], str]], answers: dict[str, str]
) -> bool:
    """Could the options check have told this pairing from a shifted one?

    This is the half that was missing. ``option_agreement`` asks whether each
    keyed answer is among the options read for the question it was paired with;
    a section where every question printed 1–4 answers yes for *every* offset,
    so a perfect score there is compatible with being wrong by one throughout.

    The pairing is witnessed only when every shifted rival fails the same test
    the proposal passed. Where the option sets genuinely differ between
    questions that happens immediately — one shift and the answers stop landing.
    Where they do not, no amount of agreement is evidence, and the section is
    left unverified rather than accepted for free.
    """
    return not any(passes(*option_agreement(rival, answers))
                   for rival in shifted_rivals(pairs))


def join_sections(
    items: list[dict[str, Any]], full_answers: dict[str, str], trusted: dict[str, int],
) -> tuple[set[str], int, dict[str, str]]:
    """Decide each section's join and its above-the-run answers in one judgement.

    These two questions cannot be answered separately, and trying to was the
    mistake: confirming the answers above a numbering hole needs questions with
    解答欄 numbers, while filling in those numbers needs answers to check against.
    Asked separately, each waits for the other and almost nothing moves.

    Asked together they are one hypothesis about the section — *the key was read
    whole, and its 解答欄 pair with the printed questions in order* — and that
    hypothesis has a single test: the answers must land among the options the
    booklet printed. Where the margin numbers were read they must also reproduce
    them exactly. A section passes as a whole or not at all, because the risk
    being tested (one lost label shifting everything after it) is a property of
    the section.

    ``full_answers`` is the key's complete reading, above-run entries included.
    Mutates accepted items to carry their 解答欄 number. Returns
    ``(accepted prefixes, slots filled, {prefix: what happened})``.
    """
    accepted: set[str] = set()
    filled = 0
    report: dict[str, str] = {}

    counts: dict[str, int] = {}
    for ref in full_answers:
        counts[ref.partition(":")[0]] = counts.get(ref.partition(":")[0], 0) + 1

    for prefix, group in by_section(items).items():
        total = counts.get(prefix, 0)
        if not total:
            continue
        limit = trusted.get(prefix, 0)
        above = total > limit
        existing = [(item, resolve_slot(item)) for item in group]
        missing = [item for item, slot in existing if not slot]

        proposal: list[tuple[dict[str, Any], str]] | None = None
        if missing and len(group) == total:
            # 题数与正解表欄位数相等：顺序配对被唯一确定，而且"数目相等"本身就说明
            # 既没漏题也没重复读。
            proposal = [(item, str(index)) for index, item in enumerate(group, 1)]
            clash = [1 for item, slot in proposal
                     if (seen := resolve_slot(item)) and int(seen) != int(slot)]
            if clash:
                report[prefix] = (
                    f"「{prefix}」段题数与欄位数都是 {total}，但顺序配对与已读到的框号有 "
                    f"{len(clash)} 处冲突，不采用——框号印在原页上，它说了算。")
                continue

        pairs = [(item, f"{prefix}:{int(slot)}")
                 for item, slot in (proposal or existing) if slot]
        confirmed, checkable = option_agreement(pairs, full_answers)
        if not passes(confirmed, checkable):
            if above or proposal:
                report[prefix] = (
                    f"「{prefix}」段未通过题册反验：可核 {checkable} 道"
                    f"（需 {MIN_CHECKABLE} 道）、通过 {confirmed} 道，未达 {MIN_RATE:.0%}。"
                    + ("缺口之上的答案不采用。" if above else "")
                    + ("顺序配对不采用。" if proposal else ""))
            continue

        # 值对得上还不够：错位的对手假设也得被同一个检查否掉，否则这份一致率
        # 与配对无关，不能拿来放行。
        if (above or proposal) and not distinguishes(pairs, full_answers):
            report[prefix] = (
                f"「{prefix}」段的选项域分不出错位：{checkable} 道可核的题读到的选项"
                "大致相同，把配对整体挪一位同样能得到这个一致率，所以它不是配对的证据。"
                "映射保持未验证。"
                + ("缺口之上的答案不采用。" if above else "")
                + ("顺序配对不采用。" if proposal else ""))
            continue

        what = []
        if above:
            accepted.add(prefix)
            what.append(f"采用缺口之上的 {total - limit} 条答案")
        if proposal:
            for item, slot in proposal:
                if not resolve_slot(item):
                    item["boxed_slot"] = slot
                    item["slotSource"] = "SECTION_SEQUENCE"
                    filled += 1
            what.append(f"按小节顺序补全 {len(missing)} 个欄号")
        if what:
            report[prefix] = (
                f"「{prefix}」段{'、'.join(what)}：题册为 {checkable} 道读到了选项，"
                f"其中 {confirmed} 道的正解确实在选项里（{confirmed}/{checkable}）；"
                "而且把配对挪一位后这些正解就落不进选项里了——能分辨错位，"
                "这一致率才算配对的证据。")
    return accepted, filled, report
