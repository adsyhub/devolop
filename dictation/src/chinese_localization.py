"""Reusable Simplified Chinese localization transform for course manifests."""

from __future__ import annotations

from typing import Any

from course_schema import prepare_course_manifest
from language_support import language_profile, manifest_language_code, set_translation_text, translation_text


TARGET_LOCALE = "zh-Hans-CN"
OPENCC_CONFIG = "t2s"
FIELDS = ("translationText", "explanationText")


def load_opencc_converter() -> Any:
    try:
        from opencc import OpenCC
    except ImportError as exc:
        raise RuntimeError("OpenCC is missing. Install requirements.txt first.") from exc
    return OpenCC(OPENCC_CONFIG)


def convert_manifest(manifest: dict[str, Any], converter: Any) -> tuple[dict[str, Any], int]:
    prepared = prepare_course_manifest(manifest)
    source_revision = prepared["contentRevision"]
    changed_fields = 0
    language = manifest_language_code(prepared)

    for index, sentence in enumerate(prepared["sentences"]):
        if not isinstance(sentence, dict):
            raise ValueError(f"Sentence {index} must be an object.")
        for field in FIELDS:
            value = translation_text(sentence) if field == "translationText" else sentence.get(field)
            if not isinstance(value, str) or not value:
                continue
            converted = converter.convert(value)
            if converted != value:
                if field == "translationText":
                    set_translation_text(sentence, converted)
                else:
                    sentence[field] = converted
                changed_fields += 1

    source_locale = language_profile(language).locale
    prepared.setdefault("locales", {}).update({
        "source": source_locale,
        "audio": source_locale,
        "transcript": source_locale,
        "translation": TARGET_LOCALE,
        "interface": TARGET_LOCALE,
    })
    prepared = prepare_course_manifest(prepared)
    result_revision = prepared["contentRevision"]
    build_metadata = prepared.setdefault("buildMetadata", {})
    history = build_metadata.setdefault("localizationTransforms", [])
    event = {
        "tool": "OpenCC",
        "config": OPENCC_CONFIG,
        "fields": list(FIELDS),
        "sourceContentRevision": source_revision,
        "resultContentRevision": result_revision,
        "changedFields": changed_fields,
    }
    if not history or history[-1] != event:
        history.append(event)
    return prepared, changed_fields
