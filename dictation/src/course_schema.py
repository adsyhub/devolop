"""Stable course identifiers and practice metadata for commercial manifests."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from typing import Any

from language_support import (
    source_text,
    translation_text,
    upgrade_manifest_language,
)


CONTENT_MODEL_VERSION = 1
CONTENT_TYPES = frozenset({"dialogue", "prompt", "option", "marker", "instruction"})
SENTENCE_ID_PATTERN = re.compile(r"^s_[0-9a-f]{24}$")
COURSE_ID_PATTERN = re.compile(r"^c_[0-9a-f]{24}$")

#: A course describes its media with exactly one of two keys: "audio" for a local
#: file next to the manifest, or "media" for an online video we never download.
#: "remote" is the only media kind that exists; the field is kept so a future kind
#: (a local video, say) cannot be mistaken for this one.
REMOTE_MEDIA_KIND = "remote"
MEDIA_PROVIDERS = frozenset({"youtube", "bilibili", "vimeo", "generic"})
#: How much of a real 精听 session the site actually allows. Never promote a course
#: to a higher tier than its site supports: "full" means play/pause/seek/rate can be
#: driven from the page, "seek-reload" means only reloading the frame at a timestamp,
#: and "external" means the site refuses to be framed at all.
MEDIA_CONTROLS = frozenset({"full", "seek-reload", "external"})
_WEB_URL_SCHEMES = ("http://", "https://")
_RETRIEVED_AT_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

_MARKER_PATTERNS = (
    re.compile(r"^[0-9]+$"),
    re.compile(r"^[0-9]+番$"),
    re.compile(r"^問題[0-9]+$"),
)
_OPTION_PATTERN = re.compile(r"^[0-9]+[.．、)]\s*\S+")
_LETTER_OPTION_PATTERN = re.compile(r"^[A-Da-d][.)．、]\s*\S+")
_GENERIC_MARKER_PATTERN = re.compile(
    r"^(?:question|pregunta|frage|domanda|quest[aã]o|문제)[0-9]+$",
    re.IGNORECASE,
)
_INSTRUCTION_FRAGMENTS = (
    "問題用紙",
    "試験を始め",
    "話を聞いてください",
    "音を聞いてください",
    "選んでください",
    "ここでちょっと休みましょう",
    "では、また続けます",
    "ではまた続けます",
)
_MULTILINGUAL_INSTRUCTIONS = {
    "en": ("listen and", "choose the", "select the", "answer the", "repeat after"),
    "fr": ("écoutez", "choisissez", "sélectionnez", "répondez", "répétez"),
    "ko": ("들으세요", "선택하세요", "고르세요", "대답하세요", "따라 하세요"),
    "es": ("escucha", "escuche", "elige", "selecciona", "responde", "repite"),
    "de": ("hören sie", "wählen sie", "beantworten sie"),
    "it": ("ascolta", "scegli", "rispondi", "ripeti"),
    "pt": ("ouça", "escute", "escolha", "responda", "repita"),
    "zh": ("请听", "请选择", "回答问题", "请回答"),
}


def prepare_course_manifest(
    manifest: dict[str, Any],
    *,
    audio_sha256: str | None = None,
) -> dict[str, Any]:
    """Return a copy upgraded with persistent IDs and practice metadata.

    Existing valid IDs are deliberately preserved when text or timing is edited.
    New IDs are deterministic so rerunning the upgrade is idempotent.
    """
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be an object.")
    prepared = copy.deepcopy(manifest)
    sentences = prepared.get("sentences")
    if not isinstance(sentences, list) or not sentences:
        raise ValueError("Manifest must contain a non-empty sentences array.")
    language = upgrade_manifest_language(prepared)

    # A course that claimed both a local file and an online video would have two
    # possible timelines and two possible courseId namespaces; a course claiming
    # neither would silently become unplayable at the last possible moment.
    has_audio = _declares(prepared, "audio")
    has_media = _declares(prepared, "media")
    if has_audio and has_media:
        raise ValueError(
            'A manifest declares either "audio" (a local file) or "media" (an online video), not both.'
        )
    if not has_audio and not has_media:
        raise ValueError(
            'A manifest must declare either "audio" (a local file) or "media" (an online video).'
        )
    media = normalize_remote_media(prepared["media"]) if has_media else None
    if media is not None:
        prepared["media"] = media

    build_metadata = prepared.get("buildMetadata")
    if not isinstance(build_metadata, dict):
        build_metadata = {}
        prepared["buildMetadata"] = build_metadata

    normalized_audio_hash = _normalized_sha256(audio_sha256)
    if normalized_audio_hash:
        build_metadata["sourceAudioSha256"] = normalized_audio_hash
    else:
        normalized_audio_hash = _normalized_sha256(build_metadata.get("sourceAudioSha256"))

    course_id = prepared.get("courseId")
    if course_id is not None and not COURSE_ID_PATTERN.fullmatch(str(course_id)):
        raise ValueError(f"Invalid courseId: {course_id!r}")
    if not course_id:
        if media is not None:
            # An online video has no bytes of ours to hash, so identity comes from
            # the video itself plus the study window. Rebuilding the same video (a
            # better transcript, a new translation pass) must land on the same
            # courseId, or the learner's progress and notes would be orphaned.
            namespace = json.dumps(
                {
                    "provider": media["provider"],
                    "videoId": media["videoId"],
                    "pageUrl": media["pageUrl"],
                    "clip": media.get("clip"),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        else:
            namespace = normalized_audio_hash or json.dumps(
                {
                    "title": str(prepared.get("title") or ""),
                    "audio": str(prepared.get("audio") or ""),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        course_id = "c_" + hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:24]
        prepared["courseId"] = course_id

    used_ids: set[str] = set()
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            raise ValueError(f"Sentence {index} must be an object.")

        sentence_id = sentence.get("id")
        if sentence_id is not None and not SENTENCE_ID_PATTERN.fullmatch(str(sentence_id)):
            raise ValueError(f"Sentence {index} has an invalid id: {sentence_id!r}")
        if not sentence_id:
            identity = json.dumps(
                {
                    "courseId": course_id,
                    "startTime": sentence.get("startTime"),
                    "endTime": sentence.get("endTime"),
                    "sourceText": source_text(sentence, language),
                    "ordinal": index,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            sentence_id = "s_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
            sentence["id"] = sentence_id
        if sentence_id in used_ids:
            raise ValueError(f"Duplicate sentence id: {sentence_id}")
        used_ids.add(str(sentence_id))

        content_type = sentence.get("contentType")
        if content_type is None:
            content_type = infer_content_type(source_text(sentence, language), language)
            sentence["contentType"] = content_type
        elif content_type not in CONTENT_TYPES:
            raise ValueError(f"Sentence {index} has unsupported contentType: {content_type!r}")

        practice_eligible = sentence.get("practiceEligible")
        if practice_eligible is None:
            sentence["practiceEligible"] = content_type != "marker"
        elif not isinstance(practice_eligible, bool):
            raise ValueError(f"Sentence {index} practiceEligible must be boolean.")

    prepared["contentModelVersion"] = CONTENT_MODEL_VERSION
    prepared["practiceSentenceCount"] = sum(
        1 for sentence in sentences if sentence.get("practiceEligible") is not False
    )
    prepared["contentRevision"] = content_revision(sentences, language)

    review = prepared.get("review")
    if not isinstance(review, dict):
        review = {}
        prepared["review"] = review
    review.setdefault("humanListening", "pending")
    review.setdefault("commercialRights", "unverified")
    review.setdefault("browserAcceptance", "pending")
    return prepared


def media_kind(manifest: Any) -> str:
    """Return "remote" for an online-video course and "audio" for a local one.

    Presence of the key decides, never its truthiness: a manifest carrying an empty
    "audio" string is a *broken local* course and must keep earning
    manifest.audio_missing from the audit instead of being relabelled as remote.
    """
    return REMOTE_MEDIA_KIND if _declares(manifest, "media") else "audio"


def is_remote_media_manifest(manifest: Any) -> bool:
    """True when the media is an online video we do not hold and never download."""
    return _declares(manifest, "media")


def remote_media(manifest: Any) -> dict[str, Any] | None:
    """Return the media block of an online-video course, or None.

    Callers get None both for a local course and for a malformed media value, so a
    summary or a report can describe a course without having to trust it first.
    """
    if not isinstance(manifest, dict):
        return None
    media = manifest.get("media")
    return media if isinstance(media, dict) else None


def normalize_remote_media(media: Any) -> dict[str, Any]:
    """Validate and canonicalise a media block, raising ValueError on anything unusable.

    This must be a fixed point: prepare_course_manifest is idempotent, and the
    remote courseId is derived from provider/videoId/pageUrl/clip, so a normaliser
    that kept changing its own output would keep changing a course's identity.
    Unknown keys are preserved in order, so a future media field does not have to be
    taught to this function just to survive it.
    """
    if not isinstance(media, dict):
        raise ValueError('"media" must be an object describing an online video.')

    kind = str(media.get("kind") or REMOTE_MEDIA_KIND).strip()
    if kind != REMOTE_MEDIA_KIND:
        raise ValueError(f'Unsupported media.kind: {kind!r}. Only "{REMOTE_MEDIA_KIND}" exists today.')

    provider = str(media.get("provider") or "").strip().lower()
    if provider not in MEDIA_PROVIDERS:
        raise ValueError(
            f"Unsupported media.provider: {media.get('provider')!r}. "
            f"Supported: {', '.join(sorted(MEDIA_PROVIDERS))}."
        )
    control = str(media.get("control") or "").strip().lower()
    if control not in MEDIA_CONTROLS:
        raise ValueError(
            f"Unsupported media.control: {media.get('control')!r}. "
            f"Supported: {', '.join(sorted(MEDIA_CONTROLS))}."
        )

    video_id = str(media.get("videoId") or "").strip()
    if not video_id and provider != "generic":
        raise ValueError(
            f"media.videoId is required for provider {provider!r}; "
            'only "generic" pages may leave it empty.'
        )

    page_url = _required_web_url(media.get("pageUrl"), "media.pageUrl")
    embed_url = _optional_web_url(media.get("embedUrl"), "media.embedUrl")
    if control != "external" and not embed_url:
        # Every tier above "external" is a framed player, and there is nothing to
        # frame without an embed URL. Accepting one here would ship a course that
        # advertises seeking and then shows an empty box.
        raise ValueError('media.embedUrl is required unless media.control is "external".')

    normalized: dict[str, Any] = {
        "kind": REMOTE_MEDIA_KIND,
        "provider": provider,
        "control": control,
        "videoId": video_id,
        "pageUrl": page_url,
        "embedUrl": embed_url,
        "durationSec": _seconds(media.get("durationSec"), "media.durationSec", default=0.0),
        "uploader": str(media.get("uploader") or "").strip(),
    }
    if media.get("clip") is not None:
        normalized["clip"] = _normalize_clip(media["clip"])
    normalized["attribution"] = _normalize_attribution(media.get("attribution"))
    for key, value in media.items():
        if key not in normalized and key != "clip":
            normalized[key] = copy.deepcopy(value)
    return normalized


def is_web_url(value: Any) -> bool:
    """True for an absolute http(s) URL with no whitespace or control characters.

    The player turns these into an iframe src and an "open at mm:ss" link, so a
    javascript:/data: URL sitting in course data would be a script-injection route
    that the page's own CSP never sees coming.
    """
    url = str(value or "")
    if not url.startswith(_WEB_URL_SCHEMES):
        return False
    return not any(character.isspace() or ord(character) < 0x20 for character in url)


def _required_web_url(value: Any, field: str) -> str:
    url = str(value or "").strip()
    if not url:
        raise ValueError(f"{field} is required for an online-video course.")
    return _checked_web_url(url, field)


def _optional_web_url(value: Any, field: str) -> str:
    url = str(value or "").strip()
    return _checked_web_url(url, field) if url else ""


def _checked_web_url(url: str, field: str) -> str:
    if not is_web_url(url):
        raise ValueError(f"{field} must be an absolute http(s) URL without whitespace, got {url!r}.")
    return url


def _normalize_clip(clip: Any) -> dict[str, float]:
    """Normalise the optional study window inside a longer video.

    media.clip only narrows which part of the video the course covers. Sentence
    times stay absolute on the original video timeline, so nothing here is ever
    subtracted from them.
    """
    if not isinstance(clip, dict):
        raise ValueError("media.clip must be an object with startTime and endTime.")
    start = _seconds(clip.get("startTime"), "media.clip.startTime")
    end = _seconds(clip.get("endTime"), "media.clip.endTime")
    if start < 0 or end <= start:
        raise ValueError(f"media.clip must satisfy 0 <= startTime < endTime, got {start} and {end}.")
    return {"startTime": start, "endTime": end}


def _normalize_attribution(attribution: Any) -> dict[str, Any]:
    """Record where the media came from, and force redistributable to False.

    An online-video course holds no redistribution right by construction: the media
    stays on the site and the transcript derives from the site's captions. A builder
    that set this to True - out of optimism, or by copying a local course - would
    carry a rights claim we cannot support all the way into the licence ledger, so
    the value is not trusted here, it is overwritten.
    """
    if attribution is not None and not isinstance(attribution, dict):
        raise ValueError("media.attribution must be an object.")
    source = attribution if isinstance(attribution, dict) else {}
    retrieved_at = str(source.get("retrievedAt") or "").strip()
    if retrieved_at and not _RETRIEVED_AT_PATTERN.fullmatch(retrieved_at):
        raise ValueError(f"media.attribution.retrievedAt must be YYYY-MM-DD, got {retrieved_at!r}.")
    normalized: dict[str, Any] = {
        "sourceName": str(source.get("sourceName") or "").strip(),
        "rightsHolder": str(source.get("rightsHolder") or "").strip(),
        "retrievedAt": retrieved_at,
        "redistributable": False,
        "notes": str(source.get("notes") or "").strip(),
    }
    for key, value in source.items():
        if key not in normalized:
            normalized[key] = copy.deepcopy(value)
    return normalized


def _seconds(value: Any, field: str, *, default: float | None = None) -> float:
    if value is None and default is not None:
        return default
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number of seconds, got {value!r}.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number of seconds, got {value!r}.")
    if number < 0:
        raise ValueError(f"{field} must not be negative, got {number}.")
    return number


def _declares(manifest: Any, key: str) -> bool:
    return isinstance(manifest, dict) and key in manifest and manifest[key] is not None


def infer_content_type(value: str, language: str = "ja") -> str:
    compact = "".join(str(value).split()).strip("。！？?!")
    if any(pattern.fullmatch(compact) for pattern in _MARKER_PATTERNS) or _GENERIC_MARKER_PATTERN.fullmatch(compact):
        return "marker"
    if _OPTION_PATTERN.match(compact) or _LETTER_OPTION_PATTERN.match(str(value).strip()):
        return "option"
    lower = str(value).casefold()
    fragments = _INSTRUCTION_FRAGMENTS if language == "ja" else _MULTILINGUAL_INSTRUCTIONS.get(language, ())
    if any(fragment.casefold() in lower for fragment in fragments):
        return "instruction"
    return "dialogue"


def content_revision(sentences: list[dict[str, Any]], language: str = "ja") -> str:
    fields = []
    for sentence in sentences:
        fields.append(
            {
                "id": sentence.get("id"),
                "startTime": sentence.get("startTime"),
                "endTime": sentence.get("endTime"),
                "sourceText": source_text(sentence, language),
                "translationText": translation_text(sentence),
                "explanationText": sentence.get("explanationText"),
                "contentType": sentence.get("contentType"),
                "practiceEligible": sentence.get("practiceEligible"),
            }
        )
    payload = json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_sha256(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    return text if re.fullmatch(r"[0-9a-f]{64}", text) else None
