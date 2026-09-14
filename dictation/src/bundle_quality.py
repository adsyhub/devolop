"""Validation and publish-readiness checks for dictation course bundles."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import PurePosixPath
from typing import Any

from course_schema import (
    CONTENT_MODEL_VERSION,
    CONTENT_TYPES,
    COURSE_ID_PATTERN,
    MEDIA_CONTROLS,
    MEDIA_PROVIDERS,
    SENTENCE_ID_PATTERN,
    infer_content_type,
    is_web_url,
)
from language_support import (
    language_profile,
    manifest_language_code,
    normalize_language_code,
    source_text,
    transcript_text,
    translation_text,
)


TRANSCRIPT_REVIEW_PHRASES = (
    "略显不自然",
    "音频切分中的重复",
    "原句表达略不自然",
    "误转写",
    "误识别",
    "转写问题",
    "需要先人工校对日文",
    "需要先人工校对原文",
)


def audit_manifest(
    manifest: dict[str, Any],
    *,
    require_enrichment: bool,
) -> dict[str, Any]:
    """Return a JSON-serializable quality report without mutating *manifest*."""
    issues: list[dict[str, Any]] = []
    sentences = manifest.get("sentences")

    if manifest.get("schemaVersion") != 1:
        add_issue(issues, "error", "schema.unsupported", "Only schemaVersion 1 is supported.")
    if not str(manifest.get("title") or "").strip():
        add_issue(issues, "error", "manifest.title_missing", "A non-empty title is required.")
    clip = validate_media_source(manifest, issues)
    try:
        language = manifest_language_code(manifest)
    except ValueError as exc:
        add_issue(issues, "error", "manifest.language_unsupported", str(exc))
        language = "ja"
    validate_language_metadata(manifest, language, issues)

    if not isinstance(sentences, list) or not sentences:
        add_issue(issues, "error", "manifest.sentences_missing", "A non-empty sentences array is required.")
        sentences = []

    validate_content_model(manifest, sentences, issues)

    previous_end: float | None = None
    marker_run = 0
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            add_issue(issues, "error", "sentence.not_object", "Sentence must be an object.", index)
            continue

        text = source_text(sentence, language)
        if not text:
            add_issue(issues, "error", "sentence.text_missing", "Source-language text is empty.", index)

        content_type = sentence.get("contentType") or infer_content_type(text, language)
        marker_run = marker_run + 1 if content_type == "marker" else 0
        if marker_run == 8:
            add_issue(
                issues,
                "warning",
                "sentence.marker_run_suspicious",
                "Eight consecutive marker-only segments suggest ASR hallucination or bad segmentation.",
                index,
            )

        start = finite_number(sentence.get("startTime"))
        end = finite_number(sentence.get("endTime"))
        if start is None or end is None:
            add_issue(issues, "error", "sentence.timestamp_invalid", "Timestamps must be finite numbers.", index)
            previous_end = None
        else:
            if start < 0:
                add_issue(issues, "error", "sentence.start_negative", "startTime cannot be negative.", index)
            if end <= start:
                add_issue(issues, "error", "sentence.duration_invalid", "endTime must be greater than startTime.", index)
            else:
                duration = end - start
                if duration < 0.35 and not is_valid_short_utterance(text, language):
                    add_issue(issues, "warning", "sentence.very_short", "Segment is shorter than 350 ms; verify alignment.", index)
                if duration > 30:
                    add_issue(issues, "warning", "sentence.very_long", "Segment is longer than 30 seconds; consider splitting it.", index)
            if previous_end is not None and start < previous_end - 0.05:
                add_issue(
                    issues,
                    "warning",
                    "sentence.overlap",
                    f"Segment overlaps the previous segment by {previous_end - start:.3f}s.",
                    index,
                )
            if clip is not None and (end <= clip["startTime"] or start >= clip["endTime"]):
                # A warning, not an error: the sentence is still playable — the video
                # it points into is the whole video, not the clip — it is just outside
                # the window the course claims to cover. Refusing to open the course
                # over that would be out of proportion to the harm.
                add_issue(
                    issues,
                    "warning",
                    "sentence.outside_clip",
                    f"Segment lies outside the study window "
                    f"[{clip['startTime']:.3f}s, {clip['endTime']:.3f}s].",
                    index,
                )
            previous_end = end

        confidence = sentence.get("confidence")
        if confidence is not None:
            confidence_value = finite_number(confidence)
            if confidence_value is None or not 0 <= confidence_value <= 1:
                add_issue(issues, "error", "sentence.confidence_invalid", "confidence must be between 0 and 1.", index)
            elif confidence_value < 0.6:
                add_issue(issues, "warning", "sentence.low_confidence", "Low ASR confidence; human review is recommended.", index)

        translation = translation_text(sentence)
        explanation = str(sentence.get("explanationText") or "").strip()
        corrupt_fields = [
            field
            for field, value in (("zhTranslation", translation), ("explanationText", explanation))
            if value and looks_corrupted(value)
        ]
        if corrupt_fields:
            add_issue(
                issues,
                "error",
                "sentence.enrichment_corrupt",
                f"Enrichment appears corrupted: {', '.join(corrupt_fields)}.",
                index,
            )

        if require_enrichment:
            if not translation:
                add_issue(issues, "warning", "sentence.translation_missing", "Translation is empty.", index)
            if not explanation:
                add_issue(issues, "warning", "sentence.explanation_missing", "Learning explanation is empty.", index)
            elif any(phrase in explanation for phrase in TRANSCRIPT_REVIEW_PHRASES):
                add_issue(
                    issues,
                    "warning",
                    "sentence.transcript_review_flag",
                    "The explanation itself says the source transcript may be wrong.",
                    index,
                )

    validate_segmentation(manifest, sentences, language, issues)

    transcript = str(manifest.get("transcriptText") or "")
    expected_transcript = transcript_text(sentences, language)
    if sentences and transcript != expected_transcript:
        add_issue(
            issues,
            "warning",
            "manifest.transcript_mismatch",
            "transcriptText does not exactly match the concatenated sentence text.",
        )

    severity_counts = Counter(issue["severity"] for issue in issues)
    code_counts = Counter(issue["code"] for issue in issues)
    status = "failed" if severity_counts["error"] else "needs_review" if severity_counts["warning"] else "passed"
    return {
        "schemaVersion": 1,
        "status": status,
        "summary": {
            "sentences": len(sentences),
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "issueCounts": dict(sorted(code_counts.items())),
        },
        "issues": issues,
    }


# --------------------------------------------------------------------------
# Sentence boundaries
# --------------------------------------------------------------------------

# Every other check in this module looks at one sentence at a time. The defect
# these catch is invisible that way: a course cut at the caption renderer's line
# width contains no individually suspicious sentence — only the distribution
# gives it away. Measured on this project's own courses, a width-capped course
# puts 29–39% of its sentences on a single length with a 13–53x cliff to the next
# one, while 39 ASR-segmented audio courses peak at 6.4% with a cliff of at most
# 4.0. See docs/VIDEO_COURSE_PIPELINE.md section 12.

_SENTENCE_TERMINALS = "。！？!?"
_SENTENCE_CLOSERS = "」』）)]】〉》”’\"'"
_PARTICLE_STARTS = ("を", "が", "は", "の", "に", "で", "と", "も", "や", "へ", "から", "まで", "より", "ので", "けど", "ても")
_DANGLING_ENDS = ("の", "を", "が", "は", "に", "で", "と", "も", "や", "へ", "から", "まで", "て", "など", "という")

# A caption line width lives here; a deliberate target length also produces a mode
# here, so share alone is not enough to tell them apart — hence the cliff test.
WIDTH_CAP_RANGE = range(18, 23)
WIDTH_CAP_SHARE = 0.25
WIDTH_CAP_CLIFF = 8.0
WIDTH_CAP_CLIFF_SHARE = 0.08
WIDTH_CAP_MIN_SENTENCES = 20

MAX_PRACTICE_CHARS = 45
MIN_PRACTICE_CHARS = 8
IMPLAUSIBLE_CHARS_PER_SECOND = 20.0
UNTERMINATED_SHARE = 0.50
UNTERMINATED_SHARE_TOKEN = 0.30
FORCED_CUT_SHARE = 0.10

# Only these sources are cut from display lines. ASR output is segmented on
# pauses, so its lack of terminal punctuation and its long utterances are
# properties of the recogniser, not evidence of a broken boundary — running the
# text checks over 39 existing audio courses would bury the real signal.
SUBTITLE_SOURCES = frozenset({"site-subtitles", "imported-file"})


def validate_segmentation(
    manifest: dict[str, Any],
    sentences: list[Any],
    language: str,
    issues: list[dict[str, Any]],
) -> None:
    """Flag sentences that are display lines rather than sentences."""
    entries: list[tuple[int, str]] = []
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            continue
        text = source_text(sentence, language).strip()
        if text:
            entries.append((index, text))
    if not entries:
        return

    metadata = manifest.get("buildMetadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    segmentation = metadata.get("segmentation")
    segmentation = segmentation if isinstance(segmentation, dict) else {}

    check_width_cap([text for _, text in entries], issues)
    check_speech_rate(sentences, language, issues)

    # A character count is only a length in a language written without spaces.
    # 45 characters of English is eight words, which is a short sentence, so the
    # cap would fire on perfectly good material.
    capped_length = not language_profile(language).uses_spaces

    if str(metadata.get("transcriptSource") or "") not in SUBTITLE_SOURCES:
        return

    unterminated = 0
    for index, text in entries:
        stripped = text.rstrip(_SENTENCE_CLOSERS)
        terminated = bool(stripped) and stripped[-1] in _SENTENCE_TERMINALS
        if not terminated:
            unterminated += 1
        body = text[:-1] if terminated else text
        if any(
            position + 4 < len(body)
            for position, char in enumerate(body)
            if char in _SENTENCE_TERMINALS
        ):
            add_issue(
                issues,
                "warning",
                "sentence.multi_sentence",
                "Segment contains more than one complete sentence; it should be split.",
                index,
            )
        if capped_length and len(text) > MAX_PRACTICE_CHARS:
            add_issue(
                issues,
                "warning",
                "sentence.over_length",
                f"Segment is {len(text)} characters; over {MAX_PRACTICE_CHARS} is not practisable.",
                index,
            )
        if (
            not terminated
            and len(text) < MIN_PRACTICE_CHARS
            and (text.startswith(_PARTICLE_STARTS) or text.endswith(_DANGLING_ENDS))
        ):
            add_issue(
                issues,
                "warning",
                "sentence.fragment",
                "Segment looks like the middle of a sentence, not a sentence.",
                index,
            )

    resolution = str(segmentation.get("timeResolution") or "")
    limit = UNTERMINATED_SHARE_TOKEN if resolution == "token" else UNTERMINATED_SHARE
    if unterminated > len(entries) * limit:
        add_issue(
            issues,
            "warning",
            "course.unterminated_ratio",
            f"{unterminated} of {len(entries)} segments have no sentence-final punctuation "
            f"(over {limit:.0%}); the transcript may be cut at display-line boundaries.",
        )

    forced = segmentation.get("forcedCuts")
    if isinstance(forced, (int, float)) and forced > len(entries) * FORCED_CUT_SHARE:
        add_issue(
            issues,
            "warning",
            "course.forced_cut_ratio",
            f"{int(forced)} of {len(entries)} sentence boundaries had no real cut point "
            "and were forced at the length cap.",
        )


def check_width_cap(texts: list[str], issues: list[dict[str, Any]]) -> None:
    """Reject a course whose sentence lengths carry a rendering-width fingerprint."""
    if len(texts) < WIDTH_CAP_MIN_SENTENCES:
        return
    histogram = Counter(len(text) for text in texts)
    peak_length = max(WIDTH_CAP_RANGE, key=lambda length: histogram.get(length, 0))
    peak = histogram.get(peak_length, 0)
    if not peak:
        return
    share = peak / len(texts)
    # A cap does not merely make one length common, it makes the next length
    # nearly absent: 297 sentences at 19 characters and 9 at 20.
    cliff = peak / max(histogram.get(peak_length + 1, 0), 1)
    capped = share > WIDTH_CAP_SHARE or (
        cliff >= WIDTH_CAP_CLIFF and share >= WIDTH_CAP_CLIFF_SHARE
    )
    if capped:
        add_issue(
            issues,
            "error",
            "course.width_capped",
            f"{peak} of {len(texts)} segments are exactly {peak_length} characters "
            f"({share:.0%}, {cliff:.0f}x the next length). These are caption display "
            "lines, not sentences; re-segment the course.",
        )


def check_speech_rate(
    sentences: list[Any], language: str, issues: list[dict[str, Any]]
) -> None:
    """Flag text and timeline that have come apart.

    Applies to every course, not only subtitle-derived ones: no speaker says 20
    characters a second, so this only ever fires when a transform rewrote a
    segment's text without moving its timestamps with it.
    """
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            continue
        text = source_text(sentence, language).strip()
        start = finite_number(sentence.get("startTime"))
        end = finite_number(sentence.get("endTime"))
        if not text or start is None or end is None or end <= start:
            continue
        rate = len(text) / (end - start)
        if rate > IMPLAUSIBLE_CHARS_PER_SECOND:
            add_issue(
                issues,
                "warning",
                "sentence.rate_implausible",
                f"{len(text)} characters in {end - start:.2f}s ({rate:.0f}/s) is faster "
                "than speech; the text and the timeline disagree.",
                index,
            )


def validate_content_model(
    manifest: dict[str, Any],
    sentences: list[Any],
    issues: list[dict[str, Any]],
) -> None:
    """Validate upgraded fields when a manifest opts into the stable model."""
    if manifest.get("contentModelVersion") is None:
        return
    if manifest.get("contentModelVersion") != CONTENT_MODEL_VERSION:
        add_issue(issues, "error", "content_model.unsupported", "Unsupported contentModelVersion.")
    if not COURSE_ID_PATTERN.fullmatch(str(manifest.get("courseId") or "")):
        add_issue(issues, "error", "content_model.course_id_invalid", "courseId is missing or invalid.")

    seen_ids: set[str] = set()
    eligible_count = 0
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            continue
        sentence_id = str(sentence.get("id") or "")
        if not SENTENCE_ID_PATTERN.fullmatch(sentence_id):
            add_issue(issues, "error", "sentence.id_invalid", "Stable sentence id is missing or invalid.", index)
        elif sentence_id in seen_ids:
            add_issue(issues, "error", "sentence.id_duplicate", "Stable sentence id is duplicated.", index)
        seen_ids.add(sentence_id)

        if sentence.get("contentType") not in CONTENT_TYPES:
            add_issue(issues, "error", "sentence.content_type_invalid", "contentType is missing or unsupported.", index)
        if not isinstance(sentence.get("practiceEligible"), bool):
            add_issue(issues, "error", "sentence.practice_eligible_invalid", "practiceEligible must be boolean.", index)
        elif sentence["practiceEligible"]:
            eligible_count += 1

    if eligible_count < 1:
        add_issue(issues, "error", "manifest.practice_queue_empty", "At least one practice-eligible sentence is required.")
    if manifest.get("practiceSentenceCount") != eligible_count:
        add_issue(issues, "error", "manifest.practice_count_mismatch", "practiceSentenceCount does not match the sentences.")
    revision = str(manifest.get("contentRevision") or "")
    if not re_full_sha256(revision):
        add_issue(issues, "error", "manifest.content_revision_invalid", "contentRevision must be a SHA-256 digest.")


def validate_language_metadata(
    manifest: dict[str, Any],
    resolved_language: str,
    issues: list[dict[str, Any]],
) -> None:
    """Reject contradictory language declarations that could poison AI caches."""
    declarations: list[tuple[str, Any]] = []
    if manifest.get("sourceLanguage"):
        declarations.append(("sourceLanguage", manifest["sourceLanguage"]))
    language = manifest.get("language")
    if isinstance(language, dict) and language.get("code"):
        declarations.append(("language.code", language["code"]))
    locales = manifest.get("locales")
    if isinstance(locales, dict) and locales.get("source"):
        declarations.append(("locales.source", locales["source"]))
    metadata = manifest.get("buildMetadata")
    if isinstance(metadata, dict) and metadata.get("detectedLanguage"):
        declarations.append(("buildMetadata.detectedLanguage", metadata["detectedLanguage"]))
    for field, value in declarations:
        try:
            declared = normalize_language_code(value)
        except ValueError:
            continue
        if declared != resolved_language:
            add_issue(
                issues,
                "error",
                "manifest.language_mismatch",
                f"{field} declares {value!r}, but the resolved source language is {resolved_language!r}.",
            )
    if isinstance(metadata, dict) and metadata.get("detectedLanguageProbability") is not None:
        probability = finite_number(metadata["detectedLanguageProbability"])
        if probability is None or not 0 <= probability <= 1:
            add_issue(
                issues,
                "error",
                "manifest.language_probability_invalid",
                "detectedLanguageProbability must be between 0 and 1.",
            )
        elif probability < 0.75:
            add_issue(
                issues,
                "warning",
                "manifest.language_low_confidence",
                "Whisper source-language detection confidence is below 75%; verify the language manually.",
            )


def re_full_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def enforce_quality_gate(report: dict[str, Any], *, strict: bool) -> None:
    """Raise ValueError when a report is not safe to publish."""
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    errors = int(summary.get("errors") or 0)
    warnings = int(summary.get("warnings") or 0)
    if errors:
        raise ValueError(f"Quality gate failed with {errors} error(s). See quality-report.json.")
    if strict and warnings:
        raise ValueError(f"Strict quality gate failed with {warnings} warning(s). See quality-report.json.")


def validate_media_source(
    manifest: dict[str, Any], issues: list[dict[str, Any]]
) -> dict[str, float] | None:
    """Check the one media description a course is allowed to carry.

    A course names its media exactly once: ``audio`` for a local file, ``media`` for
    an online video that is never downloaded. Carrying both is not an ambiguity to
    resolve by preferring one — it is two different courses in a single file, and
    whichever the player happened to pick, half the manifest would be describing
    something the learner is not hearing.

    Returns the validated study window of a remote course so the sentence loop can
    flag segments outside it, or None when there is no window to check against.
    """
    has_audio = "audio" in manifest
    has_media = "media" in manifest

    if has_audio and has_media:
        add_issue(
            issues,
            "error",
            "manifest.media_and_audio_conflict",
            'A manifest declares either "audio" (a local file) or "media" (an online video), not both.',
        )
        return None
    if not has_audio and not has_media:
        add_issue(
            issues,
            "error",
            "manifest.audio_missing",
            'A course must declare either "audio" (a local file) or "media" (an online video).',
        )
        return None
    if has_audio:
        validate_audio_path(manifest.get("audio"), issues)
        return None

    media = manifest.get("media")
    if not isinstance(media, dict):
        add_issue(issues, "error", "manifest.media_invalid", '"media" must be an object.')
        return None

    provider = str(media.get("provider") or "").strip().lower()
    if provider not in MEDIA_PROVIDERS:
        add_issue(
            issues,
            "error",
            "manifest.media_provider_unknown",
            f"Unsupported media.provider {media.get('provider')!r}; "
            f"supported: {', '.join(sorted(MEDIA_PROVIDERS))}.",
        )

    control = str(media.get("control") or "").strip().lower()
    if control not in MEDIA_CONTROLS:
        add_issue(
            issues,
            "error",
            "manifest.media_invalid",
            f"Unsupported media.control {media.get('control')!r}; "
            f"supported: {', '.join(sorted(MEDIA_CONTROLS))}.",
        )

    if not is_web_url(media.get("pageUrl")):
        add_issue(
            issues,
            "error",
            "manifest.media_page_url_missing",
            "media.pageUrl must be an http(s) URL identifying the video page.",
        )
    if control != "external" and not is_web_url(media.get("embedUrl")):
        # Every tier above "external" is a framed player. Without an embed URL the
        # course would advertise seeking and then render an empty box.
        add_issue(
            issues,
            "error",
            "manifest.media_embed_missing",
            'media.embedUrl is required unless media.control is "external".',
        )

    attribution = media.get("attribution")
    if isinstance(attribution, dict) and attribution.get("redistributable"):
        # We hold no rights to the media and the transcript derives from the site's
        # captions. A manifest claiming otherwise is a licensing defect, and the one
        # place it can still be caught cheaply is here.
        add_issue(
            issues,
            "error",
            "manifest.media_redistributable_claim",
            "An online-video course can never be redistributable: the media is not ours.",
        )

    clip = media.get("clip")
    if clip is None:
        return None
    start = finite_number(clip.get("startTime")) if isinstance(clip, dict) else None
    end = finite_number(clip.get("endTime")) if isinstance(clip, dict) else None
    if start is None or end is None or start < 0 or end <= start:
        add_issue(
            issues,
            "error",
            "manifest.media_clip_invalid",
            "media.clip must be {startTime, endTime} with 0 <= startTime < endTime.",
        )
        return None
    return {"startTime": start, "endTime": end}


def validate_audio_path(value: Any, issues: list[dict[str, Any]]) -> None:
    if not isinstance(value, str) or not value.strip():
        add_issue(issues, "error", "manifest.audio_missing", "A non-empty audio path is required.")
        return
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
        add_issue(issues, "error", "manifest.audio_unsafe", "Audio must be a safe filename at ZIP root.")


def finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def looks_corrupted(value: str) -> bool:
    """Detect replacement characters and question-mark mojibake without flagging normal questions."""
    compact = "".join(value.split())
    if not compact:
        return False
    if "\ufffd" in compact:
        return True
    ascii_questions = compact.count("?")
    return ascii_questions >= 3 and ascii_questions / len(compact) >= 0.25


def is_valid_short_utterance(value: str, language: str = "ja") -> bool:
    compact = "".join(value.split()).strip("。.!！?？、,")
    if not compact:
        return False
    if compact.isdigit():
        return True
    common = {
        "ja": {"はい", "いいえ", "うん", "ええ", "あ", "え", "へえ"},
        "en": {"yes", "no", "ok", "okay", "oh", "hi"},
        "fr": {"oui", "non", "bon", "ah"},
        "ko": {"네", "아니요", "응", "어", "아"},
        "es": {"sí", "no", "vale", "ah"},
    }
    return compact.casefold() in common.get(language, set())


def add_issue(
    issues: list[dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    sentence_index: int | None = None,
) -> None:
    issue: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if sentence_index is not None:
        issue["sentenceIndex"] = sentence_index
    issues.append(issue)
