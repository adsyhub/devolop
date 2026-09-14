"""Four-value quality checks, structured issues, and evidence model.

Per docs/DICTATION_WORKBENCH_AUTOMATION_PLAN.md:
Results use four-value logic: pass / fail / unknown / not_applicable.
Issues are derived from checks with stable IDs and explicit capability impacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Literal

CHECK_RESULTS = frozenset({"pass", "fail", "unknown", "not_applicable"})
SEVERITIES = frozenset({"info", "warning", "blocking"})
CAPABILITIES = frozenset({
    "preview",
    "dictation_scoring",
    "full_study",
    "exam_scoring",
    "distribution",
})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SubjectRef:
    kind: str  # e.g. "course", "course_sentence", "lexicon_entry", "exam_question", "pdf_page"
    id: str
    revision: str = ""


@dataclass
class CheckResult:
    checkId: str
    result: Literal["pass", "fail", "unknown", "not_applicable"]
    subject: SubjectRef
    severity: Literal["info", "warning", "blocking"] = "blocking"
    checkVersion: str = "1"
    schemaVersion: int = 1
    blockedCapabilities: list[str] = field(default_factory=list)
    reasonCode: str = ""
    message: str = ""
    inputHashes: dict[str, str] = field(default_factory=dict)
    evidenceRefs: list[str] = field(default_factory=list)
    observed: Any = None
    threshold: Any = None
    createdAt: str = field(default_factory=utc_now_iso)

    def __init__(
        self,
        check_id: str | None = None,
        result: Literal["pass", "fail", "unknown", "not_applicable"] = "pass",
        subject: SubjectRef | None = None,
        severity: Literal["info", "warning", "blocking"] = "blocking",
        checkId: str | None = None,
        checkVersion: str = "1",
        schemaVersion: int = 1,
        blockedCapabilities: list[str] | None = None,
        blocked_capabilities: list[str] | None = None,
        reasonCode: str = "",
        reason_code: str = "",
        message: str = "",
        inputHashes: dict[str, str] | None = None,
        input_hashes: dict[str, str] | None = None,
        evidenceRefs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        observed: Any = None,
        threshold: Any = None,
        createdAt: str | None = None,
        created_at: str | None = None,
    ) -> None:
        self.checkId = checkId or check_id or ""
        self.result = result
        self.subject = subject or SubjectRef("unknown", "unknown")
        self.severity = severity
        self.checkVersion = checkVersion
        self.schemaVersion = schemaVersion
        self.blockedCapabilities = blockedCapabilities or blocked_capabilities or []
        self.reasonCode = reasonCode or reason_code
        self.message = message
        self.inputHashes = inputHashes or input_hashes or {}
        self.evidenceRefs = evidenceRefs or evidence_refs or []
        self.observed = observed
        self.threshold = threshold
        self.createdAt = createdAt or created_at or utc_now_iso()

    @property
    def check_id(self) -> str:
        return self.checkId

    @property
    def blocked_capabilities(self) -> list[str]:
        return self.blockedCapabilities

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["subject"] = asdict(self.subject)
        data["check_id"] = self.checkId
        data["blocked_capabilities"] = self.blockedCapabilities
        data["reason_code"] = self.reasonCode
        return data


@dataclass
class Issue:
    id: str
    code: str
    severity: Literal["info", "warning", "blocking"]
    subject: SubjectRef
    status: Literal["open", "resolved", "quarantined", "ignored"] = "open"
    blockedCapabilities: list[str] = field(default_factory=list)
    reasonCode: str = ""
    message: str = ""
    location: dict[str, Any] = field(default_factory=dict)
    evidenceRefs: list[str] = field(default_factory=list)
    repairAttempts: int = 0
    suggestedAction: str = ""
    createdAt: str = field(default_factory=utc_now_iso)

    def __init__(
        self,
        id: str,
        code: str,
        severity: Literal["info", "warning", "blocking"],
        subject: SubjectRef,
        status: Literal["open", "resolved", "quarantined", "ignored"] = "open",
        blockedCapabilities: list[str] | None = None,
        blocked_capabilities: list[str] | None = None,
        reasonCode: str = "",
        reason_code: str = "",
        message: str = "",
        location: dict[str, Any] | None = None,
        evidenceRefs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        repairAttempts: int = 0,
        suggestedAction: str = "",
        suggested_action: str = "",
        createdAt: str | None = None,
        created_at: str | None = None,
    ) -> None:
        self.id = id
        self.code = code
        self.severity = severity
        self.subject = subject
        self.status = status
        self.blockedCapabilities = blockedCapabilities or blocked_capabilities or []
        self.reasonCode = reasonCode or reason_code
        self.message = message
        self.location = location or {}
        self.evidenceRefs = evidenceRefs or evidence_refs or []
        self.repairAttempts = repairAttempts
        self.suggestedAction = suggestedAction or suggested_action
        self.createdAt = createdAt or created_at or utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["subject"] = asdict(self.subject)
        data["blocked_capabilities"] = self.blockedCapabilities
        data["reason_code"] = self.reasonCode
        data["suggested_action"] = self.suggestedAction
        return data


def check_to_dict(c: CheckResult) -> dict[str, Any]:
    return c.to_dict()


def issue_to_dict(i: Issue) -> dict[str, Any]:
    return i.to_dict()


def generate_issue_id(subject: SubjectRef, code: str, location_str: str = "") -> str:
    key = f"{subject.kind}:{subject.id}:{subject.revision}:{code}:{location_str}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def issue_from_legacy_manifest_issue(
    manifest_issue: dict[str, Any],
    subject: SubjectRef,
    sentence_id: str = "",
) -> Issue:
    code = str(manifest_issue.get("code") or "unknown")
    legacy_sev = str(manifest_issue.get("severity") or "warning").lower()
    severity = "blocking" if legacy_sev in {"error", "blocking"} else "warning" if legacy_sev == "warning" else "info"
    msg = str(manifest_issue.get("message") or "")
    sentence_idx = manifest_issue.get("sentenceIndex")

    # Map issue to affected capabilities
    blocked: list[str] = []
    if code.startswith("sentence.timestamp") or code.startswith("sentence.text_missing") or code == "sentence.not_object":
        blocked.extend(["dictation_scoring", "full_study"])
    elif code.startswith("sentence.enrichment_corrupt") or code.startswith("sentence.translation_missing") or code.startswith("sentence.explanation_missing"):
        blocked.append("full_study")
    elif code.startswith("manifest.audio_missing") or code.startswith("manifest.audio_unsafe"):
        blocked.extend(["preview", "dictation_scoring", "full_study"])

    loc: dict[str, Any] = {}
    loc_str = ""
    if sentence_id:
        loc["sentenceId"] = sentence_id
        loc_str = sentence_id
    elif sentence_idx is not None:
        loc["sentenceIndex"] = sentence_idx
        loc_str = str(sentence_idx)

    issue_id = generate_issue_id(subject, code, loc_str)
    return Issue(
        id=issue_id,
        code=code,
        severity=severity,
        subject=subject,
        status="open",
        blockedCapabilities=blocked,
        reasonCode=code,
        message=msg,
        location=loc,
    )
