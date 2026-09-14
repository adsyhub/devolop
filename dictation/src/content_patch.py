"""Apply reviewable, source-bound content corrections to course manifests."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from course_schema import content_revision
from language_support import (
    manifest_language_code,
    set_source_text,
    set_translation_text,
    source_text,
    transcript_text,
    translation_text,
)


def sentences_digest(sentences: list[Any]) -> str:
    encoded = json.dumps(
        sentences,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def apply_content_patch(
    manifest: dict[str, Any],
    patch: dict[str, Any],
    *,
    patch_name: str,
) -> dict[str, Any]:
    """Return a patched copy after validating source digest and operation bounds."""
    sentences = manifest.get("sentences")
    if not isinstance(sentences, list):
        raise ValueError("Manifest must contain a sentences array.")
    if patch.get("schemaVersion") != 1:
        raise ValueError("Only content patch schemaVersion 1 is supported.")

    expected_digest = str(patch.get("sourceSentencesDigest") or "")
    actual_digest = sentences_digest(sentences)
    if not expected_digest or expected_digest != actual_digest:
        raise ValueError(
            "Content patch source digest mismatch; refusing to apply it to a different manifest."
        )

    operations = patch.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("Content patch must contain at least one operation.")

    result = copy.deepcopy(manifest)
    language = manifest_language_code(result)
    result_sentences = result["sentences"]
    normalized_operations: list[tuple[int, int, list[dict[str, Any]]]] = []
    for operation_index, operation in enumerate(operations):
        if not isinstance(operation, dict) or operation.get("type") != "replace_range":
            raise ValueError(f"Operation {operation_index} must be replace_range.")
        try:
            start = int(operation["startIndex"])
            end = int(operation["endIndex"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Operation {operation_index} has invalid indexes.") from exc
        if start < 0 or end < start or end >= len(result_sentences):
            raise ValueError(f"Operation {operation_index} range is out of bounds.")

        expected_start = operation.get("expectedStartTime")
        expected_end = operation.get("expectedEndTime")
        if expected_start is not None and result_sentences[start].get("startTime") != expected_start:
            raise ValueError(f"Operation {operation_index} start boundary does not match.")
        if expected_end is not None and result_sentences[end].get("endTime") != expected_end:
            raise ValueError(f"Operation {operation_index} end boundary does not match.")

        replacement = operation.get("items")
        if not isinstance(replacement, list) or not replacement:
            raise ValueError(f"Operation {operation_index} replacement items are empty.")
        normalized_items: list[dict[str, Any]] = []
        preserved_item: dict[str, Any] | None = None
        if start == end and len(replacement) == 1:
            current_item = result_sentences[start]
            if isinstance(current_item, dict):
                preserved_item = current_item
        previous_end: float | None = None
        for item_index, item in enumerate(replacement):
            if not isinstance(item, dict):
                raise ValueError(f"Operation {operation_index} item {item_index} is not an object.")
            normalized = copy.deepcopy(preserved_item) if preserved_item is not None else {}
            normalized.update(copy.deepcopy(item))
            try:
                item_start = float(normalized["startTime"])
                item_end = float(normalized["endTime"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Operation {operation_index} item {item_index} has invalid timestamps."
                ) from exc
            if item_start < 0 or item_end <= item_start:
                raise ValueError(f"Operation {operation_index} item {item_index} has invalid duration.")
            if previous_end is not None and item_start < previous_end:
                raise ValueError(f"Operation {operation_index} replacement items overlap.")
            text = source_text(normalized, language)
            if not text:
                raise ValueError(f"Operation {operation_index} item {item_index} has no source text.")
            set_source_text(normalized, text, language)
            if "translationText" in item:
                set_translation_text(normalized, item.get("translationText"))
            elif "zhTranslation" in item:
                set_translation_text(normalized, item.get("zhTranslation"))
            elif "translationText" in normalized or "zhTranslation" in normalized:
                set_translation_text(normalized, translation_text(normalized))
            previous_end = item_end
            normalized_items.append(normalized)
        normalized_operations.append((start, end, normalized_items))

    ordered = sorted(normalized_operations, key=lambda item: item[0])
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] <= previous[1]:
            raise ValueError("Content patch operations overlap.")

    for start, end, replacement in reversed(ordered):
        result_sentences[start : end + 1] = replacement

    result["transcriptText"] = transcript_text(result_sentences, language)
    result["contentRevision"] = content_revision(result_sentences, language)
    result.pop("quality", None)
    metadata = result.setdefault("buildMetadata", {})
    history = metadata.setdefault("contentPatches", [])
    if not isinstance(history, list):
        raise ValueError("buildMetadata.contentPatches must be an array when present.")
    history.append(
        {
            "name": Path(patch_name).name,
            "sourceSentencesDigest": actual_digest,
            "resultSentencesDigest": sentences_digest(result_sentences),
            "description": str(patch.get("description") or "").strip(),
            "evidence": patch.get("evidence") if isinstance(patch.get("evidence"), dict) else {},
        }
    )
    return result
