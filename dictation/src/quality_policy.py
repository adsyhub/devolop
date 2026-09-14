"""Policy evaluation for content capabilities and quality decisions.

Per docs/DICTATION_WORKBENCH_AUTOMATION_PLAN.md:
Decisions:
  - passed: all required checks passed with evidence
  - limited: baseline capability passed (e.g. dictation), but optional features (e.g. full explanation) missing
  - rejected: blocking errors exist
  - unknown: insufficient evidence
"""

from __future__ import annotations

from typing import Any
from quality_issues import CheckResult, Issue


DEFAULT_POLICY_ID = "personal-learning-v1"


def evaluate_course_quality(
    issues: list[Issue],
    *,
    has_audio: bool = True,
    policy_id: str = DEFAULT_POLICY_ID,
) -> dict[str, Any]:
    """Evaluate a course's issues against a quality policy to determine capabilities and quality decision."""
    blocking_issues = [i for i in issues if i.severity == "blocking" and i.status == "open"]
    warning_issues = [i for i in issues if i.severity == "warning" and i.status == "open"]

    blocked_caps = set()
    for i in issues:
        if i.status == "open":
            blocked_caps.update(i.blockedCapabilities)

    can_preview = has_audio and ("preview" not in blocked_caps)
    can_dictation = has_audio and ("dictation_scoring" not in blocked_caps) and not any(
        i.code.startswith("sentence.timestamp") or i.code.startswith("sentence.text_missing")
        for i in blocking_issues
    )
    can_full_study = can_dictation and ("full_study" not in blocked_caps) and not any(
        i.code.startswith("sentence.enrichment") for i in blocking_issues
    )
    # Distribution is always false unless explicit human verification / licensing holds
    can_distribute = False

    capabilities = {
        "preview": can_preview,
        "dictation_scoring": can_dictation,
        "full_study": can_full_study,
        "exam_scoring": False,
        "distribution": can_distribute,
    }

    if blocking_issues:
        decision = "rejected"
    elif can_full_study and not warning_issues:
        decision = "passed"
    elif can_dictation:
        decision = "limited"
    else:
        decision = "rejected"

    return {
        "policyId": policy_id,
        "decision": decision,
        "capabilities": capabilities,
        "issuesSummary": {
            "total": len(issues),
            "blocking": len(blocking_issues),
            "warning": len(warning_issues),
        },
    }


def evaluate_lexicon_quality(
    pack: dict[str, Any],
    *,
    policy_id: str = DEFAULT_POLICY_ID,
) -> dict[str, Any]:
    entries = pack.get("entries", [])
    has_entries = len(entries) > 0
    capabilities = {
        "preview": True,
        "dictation_scoring": False,
        "full_study": has_entries,
        "exam_scoring": False,
        "distribution": False,
    }
    decision = "passed" if has_entries else "limited"
    return {
        "policyId": policy_id,
        "decision": decision,
        "capabilities": capabilities,
    }


def evaluate_exam_quality(
    exam: dict[str, Any],
    *,
    policy_id: str = DEFAULT_POLICY_ID,
) -> dict[str, Any]:
    questions = exam.get("questions", [])
    has_questions = len(questions) > 0
    has_keys = bool(exam.get("answerKey") or any(q.get("answer") for q in questions if isinstance(q, dict)))
    capabilities = {
        "preview": True,
        "dictation_scoring": False,
        "full_study": False,
        "exam_scoring": has_questions and has_keys,
        "distribution": False,
    }
    decision = "passed" if (has_questions and has_keys) else "limited" if has_questions else "rejected"
    return {
        "policyId": policy_id,
        "decision": decision,
        "capabilities": capabilities,
    }


def evaluate_personal_learning_policy(
    check_results: list[CheckResult],
    *,
    policy_id: str = DEFAULT_POLICY_ID,
) -> dict[str, Any]:
    """Evaluate CheckResults against the personal learning policy."""
    blocking = [c for c in check_results if c.severity == "blocking" and c.result == "fail"]
    warnings = [c for c in check_results if c.severity == "warning" and c.result in {"fail", "unknown"}]

    blocked_caps = set()
    for c in check_results:
        if c.result in {"fail", "unknown"}:
            blocked_caps.update(c.blockedCapabilities)

    allowed_caps = [
        cap
        for cap in ("preview", "dictation_scoring", "full_study", "exam_scoring")
        if cap not in blocked_caps
    ]

    if blocking:
        decision = "rejected"
    elif "full_study" in allowed_caps and not warnings:
        decision = "passed"
    elif "dictation_scoring" in allowed_caps:
        decision = "limited"
    elif "preview" in allowed_caps:
        decision = "limited"
    else:
        decision = "rejected"

    return {
        "policyId": policy_id,
        "decision": decision,
        "allowedCapabilities": allowed_caps,
        "blockedCapabilities": list(blocked_caps),
        "blockingCount": len(blocking),
        "warningCount": len(warnings),
    }
