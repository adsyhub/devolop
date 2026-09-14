"""Safe patch validation, CAS conflict detection, and deterministic auto-repair.

Implements section 8 of docs/DICTATION_WORKBENCH_AUTOMATION_PLAN.md:
- Whitelisted operations: replace_field, normalize_text
- CAS expectedValueHash checking against base revision
- Post-patch verification: refusal if sentence count decreases or new errors are introduced.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import unicodedata
from typing import Any

from bundle_quality import audit_manifest
from studio_analysis import compute_content_sha256

ALLOWED_FIELDS = {
    "zhTranslation",
    "translation",
    "explanationText",
    "explanation",
    "sourceText",
    "notes",
}


class PatchError(Exception):
    """Base patch exception."""


class RevisionMismatchError(PatchError):
    """Patch base revision does not match current target revision."""


class CasConflictError(PatchError):
    """Current field value does not match expected CAS hash."""


class PatchValidationError(PatchError):
    """Patch failed post-application validation or caused regression."""


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


@dataclass
class PatchOp:
    op: str  # replace_field | normalize_text
    item_id: str
    field: str
    value: str
    expected_value_hash: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "itemId": self.item_id,
            "field": self.field,
            "value": self.value,
            "expectedValueHash": self.expected_value_hash,
            "evidenceRefs": self.evidence_refs,
        }


@dataclass
class Patch:
    patch_id: str
    subject_id: str
    base_revision: str
    operations: list[PatchOp]
    issue_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "patchId": self.patch_id,
            "subjectId": self.subject_id,
            "baseRevision": self.base_revision,
            "issueIds": self.issue_ids,
            "operations": [op.to_dict() for op in self.operations],
        }


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace and Unicode."""
    if not text:
        return ""
    # NFC normalizes combining characters without altering fullwidth punctuation
    normalized = unicodedata.normalize("NFC", text)
    # Strip carriage returns and collapse irregular whitespace
    lines = [line.strip() for line in normalized.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()


def apply_patch(
    manifest: dict[str, Any],
    patch: Patch,
    *,
    current_revision: str | None = None,
) -> tuple[dict[str, Any], bool, str]:
    """Validate and apply a Patch with CAS check and regression prevention."""
    manifest_copy = copy.deepcopy(manifest)
    actual_rev = current_revision or compute_content_sha256(manifest)

    # 1. Verify base revision
    if patch.base_revision and patch.base_revision != actual_rev:
        raise RevisionMismatchError(
            f"Base revision mismatch: patch expects {patch.base_revision}, current is {actual_rev}"
        )

    sentences = manifest_copy.get("sentences")
    if not isinstance(sentences, list):
        raise PatchError("Manifest has no valid sentences list")

    original_sentence_count = len(sentences)
    sentence_map = {str(s.get("id") or idx): s for idx, s in enumerate(sentences) if isinstance(s, dict)}

    # 2. Apply operations with field validation and CAS checking
    for op in patch.operations:
        if op.field not in ALLOWED_FIELDS:
            raise PatchValidationError(f"Field '{op.field}' is not in allowed whitelist {ALLOWED_FIELDS}")

        target_sentence = sentence_map.get(op.item_id)
        if not target_sentence:
            raise PatchValidationError(f"Sentence with id '{op.item_id}' not found in manifest")

        current_val = str(target_sentence.get(op.field) or "")
        if op.expected_value_hash:
            actual_val_hash = sha256_text(current_val)
            if actual_val_hash != op.expected_value_hash:
                raise CasConflictError(
                    f"CAS mismatch for {op.item_id}.{op.field}: expected {op.expected_value_hash}, got {actual_val_hash}"
                )

        target_sentence[op.field] = op.value

    # 3. Post-application verification: audit manifest (regression prevention)
    orig_audit = audit_manifest(manifest, require_enrichment=False)
    orig_errors = int(orig_audit.get("summary", {}).get("errors") or 0)
    new_audit = audit_manifest(manifest_copy, require_enrichment=False)
    new_errors = int(new_audit.get("summary", {}).get("errors") or 0)
    if new_errors > orig_errors:
        raise PatchValidationError(f"Patch introduced {new_errors - orig_errors} new validation errors")

    if len(manifest_copy.get("sentences", [])) < original_sentence_count:
        raise PatchValidationError("Patch resulted in reduced sentence count")

    return manifest_copy, True, "Patch applied successfully"


def apply_deterministic_repairs(manifest: dict[str, Any]) -> tuple[dict[str, Any], list[PatchOp]]:
    """Clean up whitespace, Unicode anomalies, and obvious corrupted artifacts.

    Returns (repaired_manifest, list_of_applied_patch_ops).
    """
    manifest_copy = copy.deepcopy(manifest)
    sentences = manifest_copy.get("sentences")
    if not isinstance(sentences, list):
        return manifest, []

    ops: list[PatchOp] = []

    for idx, s in enumerate(sentences):
        if not isinstance(s, dict):
            continue
        s_id = str(s.get("id") or idx)

        for fld in ("sourceText", "zhTranslation", "explanationText"):
            val = s.get(fld)
            if isinstance(val, str) and val:
                cleaned = normalize_whitespace(val)
                if cleaned != val:
                    op = PatchOp(
                        op="normalize_text",
                        item_id=s_id,
                        field=fld,
                        value=cleaned,
                        expected_value_hash=sha256_text(val),
                    )
                    ops.append(op)
                    s[fld] = cleaned

    return manifest_copy, ops
