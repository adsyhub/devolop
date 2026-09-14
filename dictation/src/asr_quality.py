"""Restore ASR diagnostics from segments.raw.json to a publish manifest."""

from __future__ import annotations

import math
from typing import Any

from language_support import manifest_language_code, source_text


def attach_asr_quality(manifest: dict[str, Any], raw_metadata: dict[str, Any]) -> int:
    sentences = manifest.get("sentences")
    raw_segments = raw_metadata.get("segments")
    if not isinstance(sentences, list) or not isinstance(raw_segments, list):
        raise ValueError("Manifest sentences and raw segments must both be arrays.")
    if len(sentences) != len(raw_segments):
        raise ValueError(f"Sentence count mismatch: manifest={len(sentences)} raw={len(raw_segments)}")

    attached = 0
    language = manifest_language_code(manifest)
    for index, (sentence, raw) in enumerate(zip(sentences, raw_segments, strict=True)):
        if not isinstance(sentence, dict) or not isinstance(raw, dict):
            raise ValueError(f"Sentence {index} or raw segment is not an object.")
        for field in ("startTime", "endTime"):
            if sentence.get(field) != raw.get(field):
                raise ValueError(f"Sentence {index} does not match raw segment field {field}.")
        if source_text(sentence, language) != source_text(raw, language):
            raise ValueError(f"Sentence {index} does not match raw segment source text.")

        avg_logprob = finite_number(raw.get("avgLogprob"))
        no_speech_probability = finite_number(raw.get("noSpeechProb"))
        compression_ratio = finite_number(raw.get("compressionRatio"))
        if avg_logprob is not None:
            sentence["confidence"] = round(max(0.0, min(1.0, math.exp(avg_logprob))), 4)
        sentence["asrQuality"] = {
            "avgLogprob": avg_logprob,
            "noSpeechProbability": no_speech_probability,
            "compressionRatio": compression_ratio,
        }
        attached += 1

    manifest.setdefault("buildMetadata", {})["asrQualityAttached"] = True
    return attached


def finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
