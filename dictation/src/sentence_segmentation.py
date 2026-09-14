from __future__ import annotations

from typing import Any

from language_support import language_profile, normalize_language_code, source_text, set_source_text

TRAILING_CLOSERS = "」』）)]】〉》\"'"


def merge_sentence_fragments(
    items: list[dict[str, Any]],
    language: str = "ja",
) -> list[dict[str, Any]]:
    """Merge Whisper fragments ending at a language-appropriate soft pause."""
    code = normalize_language_code(language)
    merged: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []

    for item in items:
        pending.append(dict(item))
        if not is_continuation_fragment(source_text(item, code), code):
            merged.append(merge_pending_items(pending, code))
            pending = []

    if pending:
        merged.append(merge_pending_items(pending, code))

    return merged


def is_continuation_fragment(value: Any, language: str = "ja") -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    text = text.rstrip(TRAILING_CLOSERS).rstrip()
    return text.endswith(language_profile(language).continuation_endings)


def merge_pending_items(items: list[dict[str, Any]], language: str = "ja") -> dict[str, Any]:
    if not items:
        raise ValueError("items must not be empty")
    if len(items) == 1:
        return dict(items[0])

    merged = dict(items[0])
    merged["endTime"] = items[-1].get("endTime", merged.get("endTime"))
    code = normalize_language_code(language)
    joiner = " " if language_profile(code).uses_spaces else ""
    text = joiner.join(clean_text(source_text(item, code)) for item in items)
    legacy_japanese = code == "ja" and all("sourceText" not in item for item in items)
    if legacy_japanese:
        merged["jaText"] = text
    else:
        set_source_text(merged, text, code)

    confidences = []
    for item in items:
        try:
            confidences.append(float(item["confidence"]))
        except (KeyError, TypeError, ValueError):
            continue
    if confidences:
        merged["confidence"] = round(min(confidences), 4)

    return merged


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
