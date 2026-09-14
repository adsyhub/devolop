"""制作期的质量发现：结构化、由服务端定级、按依赖组隔离。

整卷复核原来的产物是一个 JSON 文件和一行日志，发布照常进行。于是它报出的疑点
既不改变任何结果，也没有状态可言 —— 它是一份没人读的报告。更糟的是它在失败时
的说法：一批调用超时、模型返回 ``{}``、题号对不上，findings 都是空的，而空的
findings 被当作"全卷无疑点"说给用户听。**没检查**和**检查通过**是两件事。

这个模块把复核结果变成可处置的东西：

* :class:`Coverage` 记录到底检查了多少、失败了多少。覆盖不全时结论是 UNKNOWN，
  不是 PASS。
* :func:`classify` 由服务端定级，而不是采信检测器自报的严重程度。模型说某题被
  截断，那是**信号**；服务端能独立复核的（占位文字、答案不在选项里）才升到
  BLOCKER，复核不了的留在 SUSPECT。模型没报问题同样不等于验证通过。
* :func:`quarantine_scope` 把要隔离的范围算成题目集合。隔离的单位是依赖组，不是
  整卷：一道题的疑点不该让另外三十道已验证的题一起下架。

规范对应：§6.2 按证据决定、§6.3 findings 结构、§6.5 局部隔离与完整率。
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from .util import digest_json

SEVERITIES = ("BLOCKER", "SUSPECT", "WARNING", "INFO")

STATUSES = (
    "OPEN", "AUTO_REPAIR_PENDING", "REPAIRING", "RESOLVED_AUTO", "QUARANTINED",
    "WAITING_INPUT", "RESOLVED_HUMAN", "DISMISSED_WITH_EVIDENCE", "SUPERSEDED",
)

# 会把题目挡在发布之外的严重程度。WARNING/INFO 不影响题目能不能用。
BLOCKING = ("BLOCKER", "SUSPECT")

# 检测器报的 kind → 服务端的 code，以及服务端能不能独立复核它。
#
# ``CONFIRMABLE`` 的两类有确定性的复核办法，服务端自己算一遍：算得实就是 BLOCKER，
# 算不实就是检测器看错了，按"有证据地驳回"处理。其余的服务端复核不了 —— 判断
# "这句话是不是被截断了"需要原页，而这里只有组装后的文本 —— 所以它们停在 SUSPECT：
# 高风险、未证实，按规范 §6.3 隔离而不是当作已证实的错误。
DETECTOR_CODES: dict[str, tuple[str, bool]] = {
    "placeholder": ("content.placeholder_text", True),
    "answer_missing": ("answer.value_not_in_options", True),
    "truncated": ("content.truncated_text", False),
    "broken_math": ("content.broken_math", False),
    "inconsistent": ("content.internally_inconsistent", False),
}

# 残留占位文字的样子。这些是组装器自己会写进去的占位符，以及 OCR 读不到内容时
# 常见的替代文本 —— 它们出现在成品里，就说明这一题的内容没有真正读到。
_PLACEHOLDER = re.compile(
    r"選択肢\s*[（(]\s*\d+\s*[）)]|选项\s*[（(]\s*\d+\s*[）)]"
    r"|待录入|待錄入|待输入|未读取|未識別|TODO|PLACEHOLDER|\bTBD\b",
    re.IGNORECASE)


class Coverage:
    """一次检测跑了多少、成了多少。覆盖不全时结论只能是 UNKNOWN。

    这是 F06 里最容易被忽略的一半。检测器失败时 findings 是空的，而空 findings
    和"检查过，没问题"在数据上长得一模一样。把分母记下来，两者才分得开。
    """

    def __init__(self, planned: int = 0, completed: int = 0, failed: int = 0,
                 cancelled: bool = False) -> None:
        self.planned = planned
        self.completed = completed
        self.failed = failed
        self.cancelled = cancelled

    @property
    def complete(self) -> bool:
        return (self.planned > 0 and self.completed == self.planned
                and not self.failed and not self.cancelled)

    @property
    def result(self) -> str:
        """这次检测的结论：PASS / FAIL / UNKNOWN，按规范 §6.2 的四值。"""
        if self.planned == 0:
            return "NOT_APPLICABLE"
        if self.cancelled or self.failed:
            return "FAIL" if self.completed == 0 else "UNKNOWN"
        return "PASS" if self.completed == self.planned else "UNKNOWN"

    def explain(self) -> str:
        if self.planned == 0:
            return "本次没有可复核的题目。"
        if self.result == "PASS":
            return f"复核覆盖 {self.completed}/{self.planned} 批，完整。"
        parts = [f"复核只覆盖 {self.completed}/{self.planned} 批"]
        if self.failed:
            parts.append(f"{self.failed} 批失败")
        if self.cancelled:
            parts.append("中途取消")
        return "，".join(parts) + "。未覆盖的部分结论未知，不能当作没有问题。"

    def as_dict(self) -> dict[str, Any]:
        return {"planned": self.planned, "completed": self.completed,
                "failed": self.failed, "cancelled": self.cancelled,
                "result": self.result, "explanation": self.explain()}


def _question_index(paper: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for form in paper.get("forms") or []:
        for group in form.get("groups") or []:
            for question in group.get("questions") or []:
                qid = question.get("questionId")
                if qid:
                    index[str(qid)] = question
    return index


def _text_of(question: dict[str, Any]) -> str:
    from .proofread import _plain

    parts = [_plain(question.get("stemAst"))]
    for option in question.get("options") or []:
        parts.append(_plain(option.get("contentAst")))
    return " ".join(p for p in parts if p)


def confirm_placeholder(question: dict[str, Any]) -> str | None:
    """占位文字确实留在成品里了吗？留在成品里就是已证实的问题。"""
    found = _PLACEHOLDER.findall(_text_of(question))
    if not found:
        return None
    return f"题干或选项里留着占位文字「{found[0]}」，这一题的内容没有真正读到。"


def confirm_answer_missing(question: dict[str, Any]) -> str | None:
    """标出的正解真的不在读到的选项编号里吗？

    这一条服务端算得准，而且它是已证实的发布规则违反：答案落在选项之外，这道题
    无论如何都判不对。数字格题没有选项域，不适用。
    """
    answer = question.get("correctAnswer") or {}
    key = answer.get("optionKey")
    if key is None:
        return None
    keys = {str(o.get("key")) for o in question.get("options") or []}
    if not keys or str(key) in keys:
        return None
    return f"标出的正解 {key} 不在本题读到的选项 {sorted(keys)} 里。"


CONFIRMERS = {
    "content.placeholder_text": confirm_placeholder,
    "answer.value_not_in_options": confirm_answer_missing,
}


def dedup_key(source_id: str, generation: int, target_key: str, code: str,
              input_digest: str) -> str:
    """同一处问题在同一代次里只算一项，重复检测不制造重复待办。"""
    return digest_json([source_id, generation, target_key, code, input_digest])


def finding(*, source_id: str, generation: int, target_key: str, code: str,
            severity: str, status: str, summary: str, input_digest: str,
            detector: dict[str, Any], target_kind: str = "QUESTION",
            evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """一条结构化的发现，按规范 §6.3 的字段。"""
    if severity not in SEVERITIES:
        raise ValueError(f"Unknown severity {severity!r}")
    if status not in STATUSES:
        raise ValueError(f"Unknown status {status!r}")
    key = dedup_key(source_id, generation, target_key, code, input_digest)
    return {
        "findingId": "finding_" + key[:24],
        "sourceId": source_id,
        "generation": generation,
        "target": {"kind": target_kind, "key": target_key},
        "code": code,
        "severity": severity,
        "status": status,
        "summary": summary,
        "inputDigest": input_digest,
        "detector": detector,
        "evidence": evidence or {},
        "dedupKey": key,
    }


def classify(raw: Iterable[dict[str, Any]], paper: dict[str, Any], *,
             source_id: str, generation: int, input_digest: str,
             detector_version: str = "1") -> list[dict[str, Any]]:
    """把检测器报的信号变成服务端定级的 findings。

    检测器（这里是文字模型）说什么不直接采信，它报的是**哪里可能有问题**，不是
    **问题有多严重**。服务端能独立算的就算一遍：

    * 算得实 → BLOCKER，已证实违反发布规则；
    * 算不实 → DISMISSED_WITH_EVIDENCE，检测器看错了，留痕但不制造待办；
    * 算不了 → SUSPECT，高风险未证实，按 §6.3 隔离而不是放行。

    去重按 ``dedupKey``：同一题的同一类问题被报两次只留一条。
    """
    index = _question_index(paper)
    out: dict[str, dict[str, Any]] = {}
    for item in raw or []:
        qid = str(item.get("questionId") or "")
        kind = str(item.get("kind") or "")
        mapped = DETECTOR_CODES.get(kind)
        question = index.get(qid)
        if not mapped or question is None:
            # 题号不在这份卷里，或类别不认识：检测器在编，不当成发现。
            continue
        code, confirmable = mapped
        detail = str(item.get("detail") or "")[:400]
        detector = {"id": "proofread-paper", "version": detector_version,
                    "reportedKind": kind, "model": item.get("reviewModel"),
                    "detail": detail}

        if confirmable:
            confirmed = CONFIRMERS[code](question)
            if confirmed:
                severity, status, summary = "BLOCKER", "QUARANTINED", confirmed
            else:
                severity, status = "INFO", "DISMISSED_WITH_EVIDENCE"
                summary = (f"检测器报了「{kind}」，服务端按规则复核后不成立，"
                           "本次不据此隔离。")
        else:
            severity, status = "SUSPECT", "QUARANTINED"
            summary = (f"检测器报了「{kind}」：{detail or '未给出说明'}。"
                       "服务端无法独立证实或否定它，按未验证处理。")

        record = finding(source_id=source_id, generation=generation, target_key=qid,
                         code=code, severity=severity, status=status, summary=summary,
                         input_digest=input_digest, detector=detector)
        out.setdefault(record["dedupKey"], record)
    return list(out.values())


def dependency_groups(paper: dict[str, Any]) -> dict[str, set[str]]:
    """共用材料 → 依赖它的题目集合。

    隔离的单位不总是单题（规范 §6.5）。一段阅读材料对应五个小问时，材料缺一段，
    五题都受影响 —— 只把其中一题拿掉，剩下四题指着一段残缺的材料，照样是错的。
    """
    groups: dict[str, set[str]] = {}
    for form in paper.get("forms") or []:
        for group in form.get("groups") or []:
            for question in group.get("questions") or []:
                qid = str(question.get("questionId") or "")
                for ref in question.get("materialRefs") or []:
                    groups.setdefault(str(ref), set()).add(qid)
    return groups


def expand_to_dependency_groups(quarantined: set[str],
                                findings: Iterable[dict[str, Any]],
                                paper: dict[str, Any]) -> tuple[set[str], dict[str, str]]:
    """把材料级的问题扩散到依赖它的全部题目。

    只有材料本身出问题才扩散。一道题自己的题干被截断，与它共用一段文章的其他题
    并没有问题 —— 把它们一起隔离是用覆盖率换来的虚假安全。所以扩散的依据是
    finding 的目标是不是那段材料，而不是"它们碰巧在同一组里"。
    """
    groups = dependency_groups(paper)
    expanded = set(quarantined)
    reasons: dict[str, str] = {}
    for item in findings or []:
        if item.get("target", {}).get("kind") != "MATERIAL":
            continue
        key = str(item["target"]["key"])
        dependents = groups.get(key) or set()
        for qid in dependents:
            if qid not in expanded:
                expanded.add(qid)
                reasons[qid] = (f"本题依赖的共用材料「{key}」未能确认"
                                f"（{item.get('summary') or '材料存在疑点'}），"
                                f"同组 {len(dependents)} 题一并隔离。")
    return expanded, reasons


def quarantine_scope(findings: Iterable[dict[str, Any]]) -> set[str]:
    """哪些题不能进入本次发布。

    只有 BLOCKER 和 SUSPECT 算数：前者已证实违反发布规则，后者高风险且服务端
    证实不了。WARNING/INFO 不影响题目能不能用，被有证据驳回的更不影响。

    隔离到题为止，不牵连整卷 —— 规范 §6.5：一道题的疑点不该让另外三十道已验证
    的题一起下架。
    """
    return {str(f["target"]["key"]) for f in findings or []
            # 只收题目。材料、页面这些目标不是题号，它们通过依赖组扩散到题上，
            # 见 expand_to_dependency_groups()——把材料 ID 直接当题号会污染隔离清单。
            if f.get("target", {}).get("kind", "QUESTION") == "QUESTION"
            and f.get("severity") in BLOCKING
            and f.get("status") not in {"DISMISSED_WITH_EVIDENCE", "SUPERSEDED",
                                        "RESOLVED_AUTO", "RESOLVED_HUMAN"}}


def summarise(findings: Iterable[dict[str, Any]], coverage: Coverage) -> dict[str, Any]:
    """给任务结果和工作台用的汇总。隔离量和覆盖率一起报，缺一个都会误导。"""
    findings = list(findings or [])
    by_severity: dict[str, int] = {}
    for item in findings:
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1
    quarantined = quarantine_scope(findings)
    return {
        "total": len(findings),
        "bySeverity": by_severity,
        "quarantinedQuestions": sorted(quarantined),
        "coverage": coverage.as_dict(),
    }


def resolve_quarantine(findings: Iterable[dict[str, Any]],
                       paper: dict[str, Any]) -> tuple[set[str], dict[str, str]]:
    """本次要隔离哪些题，以及每一题的理由。

    先按 finding 自己的目标算，再把材料级的问题扩散到整个依赖组。理由逐题保留：
    隔离要留下处置和原因，不能只留下一个数字（规范 §6.5）。
    """
    direct = quarantine_scope(findings)
    reasons = {str(f["target"]["key"]): f["summary"] for f in findings or []
               if str(f["target"]["key"]) in direct}
    expanded, extra = expand_to_dependency_groups(direct, findings, paper)
    reasons.update(extra)
    return expanded, reasons
