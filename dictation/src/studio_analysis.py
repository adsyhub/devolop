"""Structured analysis engine for courses, drafts, lexicon, and exams.

Produces structured CheckResults and Issues according to:
- 4-value check results: pass / fail / unknown / not_applicable
- Stable Issue IDs grouped by (subject, revision, code, location)
- Markdown summaries derived deterministically from structured JSON, never the reverse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from bundle_quality import audit_manifest, looks_corrupted
from quality_issues import (
    CheckResult,
    Issue,
    SubjectRef,
    check_to_dict,
    issue_to_dict,
)
from quality_policy import evaluate_personal_learning_policy


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_content_sha256(content: Any) -> str:
    serialized = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass
class AnalysisReport:
    schema_version: int = 1
    subject: SubjectRef = field(default_factory=lambda: SubjectRef("unknown", "unknown"))
    quality_decision: str = "unknown"
    check_results: list[CheckResult] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    markdown_report: str = ""
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "subject": {
                "kind": self.subject.kind,
                "id": self.subject.id,
                "revision": self.subject.revision,
            },
            "qualityDecision": self.quality_decision,
            "checkResults": [check_to_dict(c) for c in self.check_results],
            "issues": [issue_to_dict(i) for i in self.issues],
            "summary": self.summary,
            "markdownReport": self.markdown_report,
            "createdAt": self.created_at,
        }


def analyze_manifest(
    manifest: dict[str, Any],
    *,
    subject_id: str = "course",
    require_enrichment: bool = False,
    existing_revision: str | None = None,
) -> AnalysisReport:
    """Analyze a course manifest producing 4-value check results and structured issues."""
    content_rev = existing_revision or compute_content_sha256(manifest)
    subject = SubjectRef(kind="course", id=subject_id, revision=content_rev)

    raw_audit = audit_manifest(manifest, require_enrichment=require_enrichment)
    audit_summary = raw_audit.get("summary") or {}
    raw_issues = raw_audit.get("issues") or []

    check_results: list[CheckResult] = []
    issues: list[Issue] = []

    # 1. Structural Schema Check
    sentences = manifest.get("sentences")
    if not isinstance(sentences, list) or len(sentences) == 0:
        check_results.append(
            CheckResult(
                subject=subject,
                check_id="schema.sentence_count",
                result="fail",
                severity="blocking",
                blocked_capabilities=["preview", "dictation_scoring", "full_study"],
                reason_code="zero_sentences",
                observed={"count": len(sentences) if isinstance(sentences, list) else 0},
            )
        )
    else:
        check_results.append(
            CheckResult(
                subject=subject,
                check_id="schema.sentence_count",
                result="pass",
                severity="notice",
                observed={"count": len(sentences)},
            )
        )

    # 2. Map legacy issues into structured CheckResults and Issues
    for raw in raw_issues:
        code = str(raw.get("code") or "general_error")
        location = str(raw.get("location") or "")
        message = str(raw.get("message") or "")
        severity = "blocking" if raw.get("severity") == "error" else "warning"

        # Determine blocked capabilities
        if "audio" in code or "timing" in code or "source" in code:
            blocked = ["dictation_scoring", "full_study"]
        elif "translation" in code or "explanation" in code:
            blocked = ["full_study"]
        else:
            blocked = ["dictation_scoring"]

        cr = CheckResult(
            subject=SubjectRef(kind="sentence", id=location or subject_id, revision=content_rev),
            check_id=f"audit.{code}",
            result="fail",
            severity=severity,
            blocked_capabilities=blocked,
            reason_code=code,
            observed={"message": message, "location": location},
        )
        check_results.append(cr)

        # Issue ID stable across runs for same location + code
        issue_key = f"{subject_id}:{location}:{code}"
        stable_id = f"iss_{hashlib.sha256(issue_key.encode('utf-8')).hexdigest()[:16]}"

        iss = Issue(
            id=stable_id,
            subject=cr.subject,
            code=code,
            severity=severity,
            status="open",
            blocked_capabilities=blocked,
            message=message,
            suggested_action="auto_repair" if severity == "warning" else "manual_review",
        )
        issues.append(iss)

    # 3. Check for missing or corrupted enrichment per sentence
    if isinstance(sentences, list):
        for idx, s in enumerate(sentences):
            if not isinstance(s, dict):
                continue
            s_id = str(s.get("id") or f"s_{idx}")
            s_subject = SubjectRef(kind="sentence", id=s_id, revision=content_rev)

            zh = s.get("zhTranslation") or s.get("translation")
            exp = s.get("explanationText") or s.get("explanation")

            if not zh or not str(zh).strip():
                check_results.append(
                    CheckResult(
                        subject=s_subject,
                        check_id="enrichment.translation_present",
                        result="unknown",
                        severity="warning",
                        blocked_capabilities=["full_study"],
                        reason_code="missing_translation",
                    )
                )
            elif looks_corrupted(str(zh)):
                check_results.append(
                    CheckResult(
                        subject=s_subject,
                        check_id="enrichment.translation_valid",
                        result="fail",
                        severity="blocking",
                        blocked_capabilities=["full_study"],
                        reason_code="corrupted_translation",
                        observed={"value": str(zh)},
                    )
                )

            if not exp or not str(exp).strip():
                check_results.append(
                    CheckResult(
                        subject=s_subject,
                        check_id="enrichment.explanation_present",
                        result="unknown",
                        severity="warning",
                        blocked_capabilities=["full_study"],
                        reason_code="missing_explanation",
                    )
                )
            elif looks_corrupted(str(exp)):
                check_results.append(
                    CheckResult(
                        subject=s_subject,
                        check_id="enrichment.explanation_valid",
                        result="fail",
                        severity="blocking",
                        blocked_capabilities=["full_study"],
                        reason_code="corrupted_explanation",
                        observed={"value": str(exp)},
                    )
                )

    # 4. Evaluate quality decision based on checks
    eval_result = evaluate_personal_learning_policy(check_results)
    quality_decision = eval_result["decision"]

    blocking_count = sum(1 for c in check_results if c.result == "fail" and c.severity == "blocking")
    warning_count = sum(1 for c in check_results if c.severity == "warning" and c.result in {"fail", "unknown"})
    pass_count = sum(1 for c in check_results if c.result == "pass")

    summary = {
        "errors": blocking_count,
        "warnings": warning_count,
        "passes": pass_count,
        "totalChecks": len(check_results),
        "totalIssues": len(issues),
        "allowedCapabilities": eval_result["allowedCapabilities"],
        "blockedCapabilities": eval_result["blockedCapabilities"],
    }

    # 5. Build derived Markdown
    md_lines = [
        f"# 质量分析报告: {manifest.get('title') or subject_id}",
        f"- **质量裁决**: `{quality_decision}`",
        f"- **检查总数**: {len(check_results)} (通过: {pass_count}, 阻断错误: {blocking_count}, 警告: {warning_count})",
        f"- **可用能力**: {', '.join(eval_result['allowedCapabilities']) or '无'}",
        "",
        "## 结构化诊断项",
    ]
    if not issues:
        md_lines.append("✓ 未发现阻断性或警告级别质量问题。")
    else:
        for iss in issues[:30]:
            icon = "❌" if iss.severity == "blocking" else "⚠️"
            md_lines.append(f"- {icon} **[{iss.code}]** {iss.message} (`{iss.subject.id}`)")
        if len(issues) > 30:
            md_lines.append(f"- *(另有 {len(issues) - 30} 个诊断项已折叠)*")

    report_md = "\n".join(md_lines)

    return AnalysisReport(
        subject=subject,
        quality_decision=quality_decision,
        check_results=check_results,
        issues=issues,
        summary=summary,
        markdown_report=report_md,
    )

