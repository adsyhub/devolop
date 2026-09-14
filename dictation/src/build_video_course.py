r"""Build a listening course from an online video, without ever keeping the video.

    URL  ->  site captions (yt-dlp, captions only)      ->  segments
         \-> no captions? temporary audio -> local ASR  ->  segments  (audio deleted)
         ->  sentence merge  ->  text provider  ->  stable content model
         ->  quality gate  ->  courses/<name>/manifest.json

This is a different FRONT END onto the machinery in :mod:`build_course`, not a second
copy of it: the provider resolution, the transcription driver, the enrichment batching
and the audit are all imported from there and from their own modules. What is new is
where the transcript comes from and the fact that there is no local media file at the
end — the manifest carries a ``media`` block instead of an ``audio`` filename.

The copyright position is structural, not a promise in a comment:

* the video is never downloaded;
* when captions are missing, audio is extracted to a temporary directory that
  :func:`media_sources.temporary_audio` deletes in a ``finally`` block, including on
  failure, before enrichment even begins;
* the resulting course is marked non-redistributable, and ``release_readiness`` and
  ``content_license`` refuse it.

Minimal runs::

    # Japanese news with the site's own captions
    python src/build_video_course.py --url "https://www.youtube.com/watch?v=..." --profile deepseek

    # No captions available: transcribe locally, audio is deleted straight after
    python src/build_video_course.py --url "https://..." --transcript asr --asr-profile japanese-accurate

    # A subtitle file you already have
    python src/build_video_course.py --transcript file --subtitles talk.srt \
        --page-url "https://www.youtube.com/watch?v=..." --profile deepseek

Provider selection here is by PROFILE NAME only. The ad-hoc ``--kind/--model/--command``
flags live in ``build_course.py``; this entry point deliberately does not grow them,
so that the studio GUI can drive it with the same argv it already trusts.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import difflib
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import build_course
from bundle_io import load_json, safe_filename, write_json
from bundle_quality import audit_manifest
from content_patch import apply_content_patch
from course_schema import prepare_course_manifest
from enrichment import (
    generate_results,
    merge_results_into_manifest,
    results_used_stub,
    write_batches,
)
from language_support import (
    SUPPORTED_LANGUAGE_CODES,
    normalize_language_code,
    transcript_text,
    upgrade_manifest_language,
)
from media_sources import (
    MediaSourceError,
    Segment,
    clean_segments,
    control_label,
    fetch_subtitles,
    parse_media_url,
    parse_subtitles,
    probe_media,
    segments_to_sentences,
    sniff_subtitle_format,
    temporary_audio,
    ytdlp_available,
)
from provider_config import (
    ConfigError,
    list_profiles,
    load_config_file,
    resolve_asr_provider,
    resolve_text_provider,
)
from sentence_segmentation import merge_sentence_fragments
from text_providers import build_text_provider, provider_env_summary
from video_segmentation import segment_video_subtitles

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_COURSES_DIR = PROJECT_DIR / "courses"
TRANSCRIPT_SOURCES = ("verified", "auto", "subs", "asr", "file")
TRANSCRIPT_REVIEW_CODES = frozenset(
    {
        "sentence.transcript_review_flag",
        "sentence.low_confidence",
        "sentence.marker_run_suspicious",
    }
)
CORRECTION_SUGGESTION_PATTERNS = (
    re.compile(
        r"(?:应为|應為|应修正为|應修正為|原词为|原詞為|正确(?:写法|说法)?为)"
        r"\s*[「『“\"']([^」』”\"'，。；（）()]{1,50})[」』”\"']"
    ),
    re.compile(
        r"(?:可能原词为|可能原詞為|推测为|推測為)"
        r"\s*[「『“\"']([^」』”\"'，。；（）()]{1,50})[」』”\"']"
    ),
)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config, config_path = load_config_file(args.config)

    if args.list_profiles:
        build_course.print_profiles(config, config_path)
        return 0

    ref = resolve_reference(args)
    clip = parse_clip(args.clip)

    # Resolving the text provider before anything is fetched means a missing model or
    # API key fails in the first second rather than after a five-minute download.
    text_config = (
        None
        if args.no_enrich
        else resolve_text_provider(config=config, profile=args.profile, overrides={})
    )

    probe = probe_video(args, ref)
    title = choose_title(args, probe, ref)
    name = args.name.strip() if args.name and args.name.strip() else safe_filename(title)
    courses_dir = (
        Path(args.courses_dir).expanduser().resolve() if args.courses_dir else DEFAULT_COURSES_DIR
    )
    destination = courses_dir / name
    work_dir = (
        Path(args.work_dir).expanduser().resolve()
        if args.work_dir
        else PROJECT_DIR / "video-work" / name
    )

    print(f"Config     : {config_path or '(none found; using flags and environment only)'}")
    print(f"Video      : {ref.page_url}")
    print(f"Provider   : {ref.provider}  (control tier: {ref.control})")
    print(f"             {control_label(ref.control)}")
    if ref.control != "full":
        print("             注意：这一档做不了自动逐句循环，精听要靠手动重播。")
    if probe.get("durationSec"):
        print(f"Duration   : {build_course.format_timestamp(probe['durationSec'])}")
    print(f"Transcript : {args.transcript}")
    print(f"Enrichment : {provider_env_summary(text_config) if text_config else 'disabled (--no-enrich)'}")
    print(f"Title      : {title}")
    print(f"Course dir : {destination}")
    print(f"Work dir   : {work_dir}")
    if clip:
        print(f"Clip       : {build_course.format_timestamp(clip[0])} - {build_course.format_timestamp(clip[1])}")

    if args.dry_run:
        print("\nDry run: nothing was fetched, transcribed, called, or written.")
        return 0

    if destination.exists() and not args.force:
        raise SystemExit(f"Course folder already exists: {destination}. Use --force to replace it.")

    work_dir.mkdir(parents=True, exist_ok=True)
    if args.transcript == "verified":
        sentences, transcript_meta = collect_verified_sentences(
            args=args,
            ref=ref,
            config=config,
            work_dir=work_dir,
            clip=clip,
            probe=probe,
            title=title,
        )
    else:
        segments, transcript_meta = collect_segments(args, ref, config, work_dir, clip)
        require_segments(segments)
        sentences = sentences_from_segments(segments, transcript_meta, probe, announce=True)

    if not sentences:
        raise SystemExit(
            "没有得到任何可用的句子。/ No usable sentences were produced.\n"
            "  字幕可能是空的，或者剪辑窗口把内容全部排除了。"
        )
    language = transcript_meta["language"]

    manifest = assemble_manifest(
        ref=ref,
        title=title,
        language=language,
        sentences=sentences,
        clip=clip,
        probe=probe,
        transcript_meta=transcript_meta,
    )

    text_provider = None
    if text_config is not None:
        text_provider = build_text_provider(text_config)
        text_provider.preflight()
        run_enrichment(manifest, text_config, text_provider, work_dir, args)

    manifest = prepare_course_manifest(manifest)
    manifest = apply_configured_content_patches(manifest, args.content_patch)
    manifest["transcriptText"] = transcript_text(manifest["sentences"], language)

    report = audit_manifest(manifest, require_enrichment=not args.no_enrich)
    build_course.print_quality_summary(report)
    correction_review = build_transcript_correction_review(
        manifest,
        report,
        transcript_meta.get("verification"),
    )
    correction_review_path = work_dir / "transcript-correction-review.json"
    write_json(correction_review_path, correction_review)
    manifest["buildMetadata"]["transcriptReview"] = {
        "status": correction_review["status"],
        "candidateCount": correction_review["candidateCount"],
        "artifact": correction_review_path.name,
        "courseId": manifest["courseId"],
        "contentRevision": manifest["contentRevision"],
    }
    print(
        f"Transcript review: {correction_review['candidateCount']} candidate(s) -> "
        f"{correction_review_path}"
    )
    errors = int(report.get("summary", {}).get("errors") or 0)
    warnings = int(report.get("summary", {}).get("warnings") or 0)
    if errors and not args.allow_failed:
        raise SystemExit(
            f"Refusing to install a course with {errors} quality error(s).\n"
            "  The player would refuse to open it anyway.\n"
            "  Pass --allow-failed to write it for inspection regardless."
        )
    if warnings and args.strict_quality:
        raise SystemExit(f"--strict-quality: refusing to install with {warnings} warning(s).")

    install(destination, manifest, ref, transcript_meta, text_config, args)
    print_summary(destination, manifest, ref, transcript_meta)
    return 0


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------


def resolve_reference(args: argparse.Namespace):
    """Work out which page this course belongs to, whichever path we are on."""
    page = args.url or args.page_url
    if args.transcript == "file":
        if not args.subtitles:
            raise SystemExit("--transcript file requires --subtitles <file>.")
        page = args.page_url or args.url
        if not page:
            raise SystemExit(
                "--transcript file also requires --page-url, so the course knows which "
                "video its timings belong to."
            )
    if not page:
        raise SystemExit("--url is required.")
    return parse_media_url(page)


def parse_clip(values: list[str] | None) -> tuple[float, float] | None:
    if not values:
        return None
    start, end = (parse_time(value) for value in values)
    if start < 0 or end <= start:
        raise SystemExit(f"--clip must be increasing and non-negative, got {values[0]} {values[1]}.")
    return (start, end)


def parse_time(value: str) -> float:
    """Accept seconds, mm:ss or h:mm:ss — all three appear in the wild."""
    text = str(value).strip()
    if not text:
        raise SystemExit("A time value cannot be empty.")
    parts = text.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        seconds = 0.0
        for part in parts:
            seconds = seconds * 60 + float(part)
        return seconds
    except ValueError as exc:
        raise SystemExit(f"Cannot read the time {value!r}. Use seconds, mm:ss or h:mm:ss.") from exc


def probe_video(args: argparse.Namespace, ref) -> dict[str, Any]:
    """Read title/duration/caption inventory, tolerating a machine without yt-dlp."""
    if args.transcript == "file":
        return {}
    if not ytdlp_available(args.ytdlp):
        # Not fatal yet: --transcript file never needs yt-dlp, and the caller may only
        # have wanted --dry-run. The paths that truly need it fail with their own message.
        print("Warning    : yt-dlp 未安装，无法读取视频信息。/ yt-dlp not available.", file=sys.stderr)
        return {}
    try:
        return probe_media(ref.page_url, ytdlp=args.ytdlp)
    except MediaSourceError as exc:
        # "Unsupported URL" means yt-dlp has no extractor for this site at all: there
        # is no caption track and no audio stream to reach, so every path below will
        # fail too. Saying so here — before a caption attempt and an audio attempt
        # each fail on their own — is the difference between one clear answer and
        # three confusing ones.
        if "Unsupported URL" in str(exc):
            raise SystemExit(
                f"yt-dlp 不支持这个站点，无法取字幕，也无法取音频。\n"
                f"  链接：{ref.page_url}\n"
                "  这通常意味着它不是一个媒体平台（页面里的音视频由脚本动态加载，\n"
                "  没有可发现的媒体地址），而不是它禁止嵌入。\n"
                "  可行的替代：\n"
                "    · 换成该内容在 YouTube 等平台上的原始出处；\n"
                "    · 或自己拿到字幕文件后用："
                "--transcript file --subtitles <文件> --page-url <链接>\n"
                " / yt-dlp has no extractor for this site: neither captions nor audio "
                "can be reached. This is not an embedding restriction."
            ) from exc
        print(f"Warning    : 读取视频信息失败，继续。/ probe failed: {exc}", file=sys.stderr)
        return {}


def choose_title(args: argparse.Namespace, probe: dict[str, Any], ref) -> str:
    for candidate in (args.title, probe.get("title"), ref.video_id, ref.provider):
        text = str(candidate or "").strip()
        if text:
            return text[:200]
    return "video-course"


# --------------------------------------------------------------------------
# Transcript
# --------------------------------------------------------------------------


def collect_segments(
    args: argparse.Namespace,
    ref,
    config: dict[str, Any],
    work_dir: Path,
    clip: tuple[float, float] | None,
) -> tuple[list[Segment], dict[str, Any]]:
    """Return cleaned segments plus a record of where they came from."""
    if args.transcript == "file":
        return from_subtitle_file(args, clip)

    if args.transcript in {"auto", "subs"}:
        subtitle = from_site_subtitles(args, ref, work_dir, clip)
        if subtitle is not None:
            return subtitle

    if args.transcript == "subs":
        raise SystemExit(
            "站点没有可用字幕，而 --transcript subs 要求必须用字幕。\n"
            "  改用 --transcript auto（没有字幕就本地转写）或 --transcript asr。\n"
            " / No usable captions and --transcript subs forbids the ASR fallback."
        )
    if args.no_audio_fetch:
        raise SystemExit(
            "站点没有可用字幕，而 --no-audio-fetch 禁止了临时取音频转写。\n"
            "  去掉 --no-audio-fetch，或自己提供 --subtitles 文件。\n"
            " / No captions available and --no-audio-fetch forbids the temporary-audio path."
        )

    return from_local_asr(args, ref, config, work_dir, clip)


def subtitle_languages(args: argparse.Namespace) -> list[str]:
    languages = [part.strip() for part in str(args.sub_langs or "").split(",") if part.strip()]
    if languages:
        return languages
    return ["ja", "en"] if args.language in {"auto", None} else [args.language]


def from_site_subtitles(
    args: argparse.Namespace,
    ref,
    work_dir: Path,
    clip: tuple[float, float] | None,
) -> tuple[list[Segment], dict[str, Any]] | None:
    """Fetch and clean the preferred site track, or return ``None``."""
    languages = subtitle_languages(args)
    print(f"\n正在查找站点字幕（{', '.join(languages)}）… / looking for site captions")
    track = fetch_subtitles(
        ref.page_url,
        languages=languages,
        work_dir=work_dir,
        ytdlp=args.ytdlp,
    )
    if track is None:
        return None

    kind_label = "人工字幕" if track.kind == "manual" else "自动字幕"
    print(f"找到{kind_label}：{track.language} ({track.format}) / found {track.kind} captions")
    language = resolve_language(args.language, track.language)
    segments = clean_segments(
        parse_subtitles(track.text, fmt=track.format),
        language=language,
        clip=clip,
        # Only auto-captions carry the rolling-window artifact. Collapsing a manual
        # track can eat a genuinely repeated phrase, so the flag follows the source.
        rolling_window=(track.kind == "auto"),
    )
    return segments, {
        "language": language,
        "transcriptSource": "site-subtitles",
        "subtitle": {"language": track.language, "kind": track.kind, "format": track.format},
    }


def require_segments(segments: list[Segment]) -> None:
    if not segments:
        raise SystemExit(
            "没有得到任何可用的句子。/ No usable sentences were produced.\n"
            "  字幕可能是空的，或者剪辑窗口把内容全部排除了。"
        )


def sentences_from_segments(
    segments: list[Segment],
    transcript_meta: dict[str, Any],
    probe: dict[str, Any],
    *,
    announce: bool,
) -> list[dict[str, Any]]:
    """Run the source-appropriate deterministic sentence segmentation."""
    language = transcript_meta["language"]
    source_type = transcript_meta.get("transcriptSource")
    if source_type in {"site-subtitles", "imported-file"}:
        sentences, seg_meta = segment_video_subtitles(
            segments,
            language=language,
            media_duration=float(probe.get("durationSec") or 0.0),
        )
        transcript_meta["segmentation"] = seg_meta
        if announce:
            print(
                f"Sentences  : {len(sentences)} (re-segmented from {len(segments)} raw cues; "
                f"resolution: {seg_meta['timeResolution']}, forced cuts: {seg_meta['forcedCuts']})"
            )
        return sentences

    sentences = merge_sentence_fragments(segments_to_sentences(segments, language), language)
    if announce:
        print(f"Sentences  : {len(sentences)} (merged from {len(segments)} raw segments)")
    return sentences


def collect_verified_sentences(
    *,
    args: argparse.Namespace,
    ref,
    config: dict[str, Any],
    work_dir: Path,
    clip: tuple[float, float] | None,
    probe: dict[str, Any],
    title: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compare site captions with independent local ASR and keep the safer source.

    This stage deliberately does not ask a generative text model to rewrite the
    transcript. Selection is deterministic and its evidence is persisted before
    translation/explanation begins.
    """
    if args.no_audio_fetch:
        raise SystemExit(
            "--transcript verified requires temporary audio for an independent local-ASR check; "
            "remove --no-audio-fetch or choose --transcript subs."
        )

    candidates: list[dict[str, Any]] = []
    subtitle = from_site_subtitles(args, ref, work_dir, clip)
    if subtitle is not None:
        subtitle_segments, subtitle_meta = subtitle
        if subtitle_segments:
            candidates.append(
                make_transcript_candidate(
                    segments=subtitle_segments,
                    transcript_meta=subtitle_meta,
                    ref=ref,
                    title=title,
                    clip=clip,
                    probe=probe,
                )
            )

    asr_segments, asr_meta = from_local_asr(args, ref, config, work_dir, clip)
    if asr_segments:
        candidates.append(
            make_transcript_candidate(
                segments=asr_segments,
                transcript_meta=asr_meta,
                ref=ref,
                title=title,
                clip=clip,
                probe=probe,
            )
        )
    if not candidates:
        require_segments([])

    selected = min(candidates, key=transcript_candidate_rank)
    evidence = build_transcript_verification(candidates, selected)
    selected_meta = selected["transcriptMeta"]
    selected_meta["verification"] = evidence
    evidence_path = work_dir / "transcript-verification.json"
    write_json(evidence_path, evidence)

    print("\nTranscript verification:")
    for candidate in candidates:
        quality = candidate["quality"]
        marker = "selected" if candidate is selected else "not selected"
        print(
            f"  {candidate['key']}: errors={quality['errors']}, "
            f"warnings={quality['warnings']}, adjusted={candidate['adjustedWarnings']} "
            f"-> {marker}"
        )
    if evidence.get("comparison"):
        print(f"  normalized text agreement: {evidence['comparison']['textSimilarity']:.3f}")
    print(f"  evidence: {evidence_path}")
    print(f"Sentences  : {len(selected['sentences'])} (verified source: {selected['key']})")
    return selected["sentences"], selected_meta


def make_transcript_candidate(
    *,
    segments: list[Segment],
    transcript_meta: dict[str, Any],
    ref,
    title: str,
    clip: tuple[float, float] | None,
    probe: dict[str, Any],
) -> dict[str, Any]:
    meta = dict(transcript_meta)
    sentences = sentences_from_segments(segments, meta, probe, announce=False)
    if not sentences:
        require_segments([])
    candidate_manifest = assemble_manifest(
        ref=ref,
        title=title,
        language=meta["language"],
        sentences=sentences,
        clip=clip,
        probe=probe,
        transcript_meta=meta,
    )
    candidate_manifest = prepare_course_manifest(candidate_manifest)
    candidate_manifest["transcriptText"] = transcript_text(
        candidate_manifest["sentences"], meta["language"]
    )
    report = audit_manifest(candidate_manifest, require_enrichment=False)
    summary = report["summary"]
    source_penalty = 1 if meta.get("subtitle", {}).get("kind") == "auto" else 0
    key = transcript_candidate_key(meta)
    return {
        "key": key,
        "sentences": sentences,
        "transcriptMeta": meta,
        "rawSegmentCount": len(segments),
        "sourcePenalty": source_penalty,
        "adjustedWarnings": int(summary.get("warnings") or 0) + source_penalty,
        "quality": {
            "status": report["status"],
            "errors": int(summary.get("errors") or 0),
            "warnings": int(summary.get("warnings") or 0),
            "issueCounts": summary.get("issueCounts") or {},
        },
    }


def transcript_candidate_key(meta: dict[str, Any]) -> str:
    if meta.get("transcriptSource") == "site-subtitles":
        return f"site-subtitles:{meta.get('subtitle', {}).get('kind') or 'unknown'}"
    return str(meta.get("transcriptSource") or "unknown")


def transcript_candidate_rank(candidate: dict[str, Any]) -> tuple[int, int, int]:
    """Fewer errors/warnings wins; ties prefer manual captions, then local ASR.

    Automatic captions receive one warning-equivalent penalty. This makes an ASR
    result with one ordinary alignment warning beat a superficially clean auto
    track, which is important because homophones are invisible to structural
    validation. A real quality error always outranks that preference.
    """
    key = candidate["key"]
    source_order = 0 if key == "site-subtitles:manual" else 1 if key == "asr" else 2
    return (
        int(candidate["quality"]["errors"]),
        int(candidate["adjustedWarnings"]),
        source_order,
    )


def build_transcript_verification(
    candidates: list[dict[str, Any]], selected: dict[str, Any]
) -> dict[str, Any]:
    public_candidates = [
        {
            "key": candidate["key"],
            "rawSegmentCount": candidate["rawSegmentCount"],
            "sentenceCount": len(candidate["sentences"]),
            "sourcePenalty": candidate["sourcePenalty"],
            "adjustedWarnings": candidate["adjustedWarnings"],
            "quality": candidate["quality"],
        }
        for candidate in candidates
    ]
    evidence: dict[str, Any] = {
        "schemaVersion": 1,
        "type": "transcript-source-verification",
        "mode": "dual-source" if len(candidates) > 1 else "single-source-fallback",
        "selected": selected["key"],
        "selectionRule": (
            "fewest quality errors, then warnings plus a one-point automatic-caption "
            "penalty; ties prefer manual captions, local ASR, then automatic captions"
        ),
        "candidates": public_candidates,
    }
    if len(candidates) == 2:
        left_text = candidate_text(candidates[0]["sentences"], candidates[0]["transcriptMeta"]["language"])
        right_text = candidate_text(candidates[1]["sentences"], candidates[1]["transcriptMeta"]["language"])
        evidence["comparison"] = {
            "left": candidates[0]["key"],
            "right": candidates[1]["key"],
            "textSimilarity": round(
                difflib.SequenceMatcher(None, left_text, right_text, autojunk=False).ratio(),
                4,
            ),
            "normalizedCharacterCounts": [len(left_text), len(right_text)],
        }
    return evidence


def candidate_text(sentences: list[dict[str, Any]], language: str) -> str:
    text = transcript_text(sentences, language)
    return "".join(character for character in text if character.isalnum())


def from_subtitle_file(
    args: argparse.Namespace, clip: tuple[float, float] | None
) -> tuple[list[Segment], dict[str, Any]]:
    path = Path(args.subtitles).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"Subtitle file not found: {path}")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    fmt = sniff_subtitle_format(text)
    language = resolve_language(args.language, "")
    print(f"\n使用本地字幕文件：{path.name} ({fmt}) / using a local subtitle file")
    segments = clean_segments(
        parse_subtitles(text, fmt=fmt),
        language=language,
        clip=clip,
        # A file the user supplied is assumed hand-made unless they say otherwise;
        # the collapse is the transform that can lose real content.
        rolling_window=args.rolling_window,
    )
    return segments, {
        "language": language,
        "transcriptSource": "imported-file",
        "subtitle": {"language": language, "kind": "manual", "format": fmt},
    }


def from_local_asr(
    args: argparse.Namespace,
    ref,
    config: dict[str, Any],
    work_dir: Path,
    clip: tuple[float, float] | None,
) -> tuple[list[Segment], dict[str, Any]]:
    """Transcribe locally from audio that is deleted before this function returns."""
    asr_config = resolve_asr_provider(
        config=config, profile=args.asr_profile, overrides={}, language=args.language
    )
    cache_path = work_dir / "asr-transcript.json"
    cache_key = asr_config.cache_key()
    cached = load_asr_cache(cache_path, ref.page_url, cache_key) if args.resume else None

    if cached is not None:
        print(f"\n复用与当前视频和 ASR 配置绑定的本地转写：{cache_path}")
        detected = str(cached.get("detectedLanguage") or asr_config.language)
        language = resolve_language(args.language, detected)
        raw = [
            Segment(start=float(item["start"]), end=float(item["end"]), text=str(item["text"]))
            for item in cached["segments"]
        ]
    else:
        provider = build_asr_provider_checked(asr_config)
        if args.transcript == "verified":
            print("\n为核验站点字幕，临时取音频做独立本地 ASR。")
        elif args.transcript == "asr":
            print("\n按要求跳过站点字幕，临时取音频做本地转写。")
        else:
            print("\n站点没有字幕，改为临时取音频做本地转写。")
        print("音频只存在于这次构建期间，转写结束立即删除，视频本身不会下载。")
        print(" / Extracting audio temporarily for local ASR. It is deleted afterwards.")

        with temporary_audio(ref.page_url, work_dir=work_dir, ytdlp=args.ytdlp) as audio_path:
            print(f"临时音频 / temporary audio: {audio_path.name}")
            transcription = build_course.run_transcription(provider, audio_path)
            detected = transcription.language or asr_config.language
            language = resolve_language(args.language, detected)
            raw = [
                Segment(start=float(s.start), end=float(s.end), text=str(s.text))
                for s in transcription.segments
            ]
        print("临时音频已删除。/ Temporary audio deleted.")
        write_json(
            cache_path,
            {
                "schemaVersion": 1,
                "type": "online-video-asr-cache",
                "pageUrl": ref.page_url,
                "asrConfig": cache_key,
                "detectedLanguage": detected,
                "segments": [
                    {"start": segment.start, "end": segment.end, "text": segment.text}
                    for segment in raw
                ],
            },
        )
        print(f"ASR cache   : {cache_path}")

    segments = clean_segments(
        raw,
        language=language,
        clip=clip,
        # ASR output is already one utterance per segment; there is no rolling window
        # to collapse, and running the collapse would only risk eating a repetition.
        rolling_window=False,
    )
    return segments, {
        "language": language,
        "transcriptSource": "asr",
        "asr": {"kind": asr_config.kind, "config": cache_key},
    }


def load_asr_cache(
    path: Path,
    page_url: str,
    asr_config: dict[str, Any],
) -> dict[str, Any] | None:
    """Return a source-bound ASR cache only when every required field is valid."""
    if not path.is_file():
        return None
    try:
        cached = load_json(path)
        if (
            cached.get("schemaVersion") != 1
            or cached.get("type") != "online-video-asr-cache"
            or cached.get("pageUrl") != page_url
            or cached.get("asrConfig") != asr_config
        ):
            return None
        segments = cached.get("segments")
        if not isinstance(segments, list) or not segments:
            return None
        for item in segments:
            if not isinstance(item, dict) or not str(item.get("text") or "").strip():
                return None
            start = float(item["start"])
            end = float(item["end"])
            if start < 0 or end <= start:
                return None
        return cached
    except (KeyError, TypeError, ValueError):
        return None


def build_asr_provider_checked(asr_config: Any):
    from asr_providers import build_asr_provider

    provider = build_asr_provider(asr_config)
    provider.preflight()
    return provider


def resolve_language(requested: str | None, detected: str) -> str:
    """Prefer what the user asked for, fall back to what the source reported."""
    for candidate in (requested, detected):
        text = str(candidate or "").strip()
        if not text or text == "auto":
            continue
        try:
            return normalize_language_code(text)
        except ValueError:
            continue
    return "ja"


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


def assemble_manifest(
    *,
    ref,
    title: str,
    language: str,
    sentences: list[dict[str, Any]],
    clip: tuple[float, float] | None,
    probe: dict[str, Any],
    transcript_meta: dict[str, Any],
) -> dict[str, Any]:
    today = _datetime.date.today().isoformat()
    media = ref.to_manifest_media(
        duration=float(probe.get("durationSec") or 0.0),
        uploader=str(probe.get("uploader") or ""),
        clip=clip,
        retrieved_at=today,
        notes=(
            "Timings, translations and explanations are ours; the transcript text derives "
            "from the site's captions or from local transcription. The media itself is never "
            "stored and this course is not redistributable."
        ),
    )
    manifest: dict[str, Any] = {
        "schemaVersion": 1,
        "title": title,
        "sourceLanguage": language,
        "media": media,
        "sentences": sentences,
        "buildMetadata": {
            "transcriptSource": transcript_meta["transcriptSource"],
            "retrievedAt": today,
            "mediaProbe": {
                "title": probe.get("title", ""),
                "uploader": probe.get("uploader", ""),
                "durationSec": probe.get("durationSec", 0.0),
                "extractor": probe.get("extractor", ""),
                "subtitles": probe.get("subtitles", []),
            },
        },
    }
    for key in ("subtitle", "asr", "segmentation", "verification"):
        if key in transcript_meta:
            manifest["buildMetadata"][key] = transcript_meta[key]
    upgrade_manifest_language(manifest, language)
    return manifest


def run_enrichment(
    manifest: dict[str, Any],
    text_config: Any,
    text_provider: Any,
    work_dir: Path,
    args: argparse.Namespace,
) -> None:
    """Translation and explanation, through exactly the same batching build_course uses."""
    batches_dir = work_dir / "batches"
    results_dir = batches_dir / "results"
    batches = write_batches(
        manifest, batches_dir, batch_size=text_config.batch_size, force=not args.resume
    )
    if not batches:
        raise SystemExit("No sentences with text to enrich.")
    print(f"\nBatches    : {len(batches)} in {batches_dir}")
    generate_results(
        text_provider,
        batches,
        results_dir,
        resume=args.resume,
        keep_going=args.keep_going,
        sleep=text_config.sleep,
        retries=text_config.retries,
    )
    stats = merge_results_into_manifest(manifest, results_dir)
    print(
        f"Merged     : files={stats['files']}, translations={stats['translations']}, "
        f"explanations={stats['explanations']}, models={stats['models'] or ['(unreported)']}"
    )
    if results_used_stub(results_dir) and not args.allow_stub_enrichment:
        raise SystemExit(
            "Refusing to build a course whose explanations came from a stub provider.\n"
            "  The 'echo' provider writes placeholders, not teaching content.\n"
            "  Re-run with a real provider, or pass --allow-stub-enrichment."
        )
    manifest["buildMetadata"]["enrichment"] = {
        "provider": text_config.describe(),
        "batches": len(batches),
    }


def apply_configured_content_patches(
    manifest: dict[str, Any], patch_values: list[str] | None
) -> dict[str, Any]:
    """Apply explicitly approved, digest-bound transcript corrections in order."""
    result = manifest
    for value in patch_values or []:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"Content patch not found: {path}")
        try:
            result = apply_content_patch(result, load_json(path), patch_name=path.name)
        except ValueError as exc:
            raise SystemExit(f"Content patch refused ({path.name}): {exc}") from exc
        print(f"Content patch: applied {path.name}")
    return result


def build_transcript_correction_review(
    manifest: dict[str, Any],
    report: dict[str, Any],
    verification: dict[str, Any] | None,
) -> dict[str, Any]:
    """Turn transcript-related audit warnings into an actionable review artifact."""
    sentences = manifest.get("sentences")
    sentences = sentences if isinstance(sentences, list) else []
    issue_map: dict[int, list[dict[str, str]]] = {}
    for issue in report.get("issues") or []:
        if not isinstance(issue, dict) or issue.get("code") not in TRANSCRIPT_REVIEW_CODES:
            continue
        try:
            index_value = issue.get("sentenceIndex", issue.get("itemIndex"))
            index = int(index_value)
        except (KeyError, TypeError, ValueError):
            continue
        issue_map.setdefault(index, []).append(
            {"code": str(issue.get("code") or ""), "message": str(issue.get("message") or "")}
        )

    language = str(manifest.get("sourceLanguage") or "ja")
    items: list[dict[str, Any]] = []
    for index in sorted(issue_map):
        if index < 0 or index >= len(sentences) or not isinstance(sentences[index], dict):
            continue
        sentence = sentences[index]
        explanation = str(sentence.get("explanationText") or "").strip()
        suggestions = extract_correction_suggestions(explanation)
        items.append(
            {
                "index": index,
                "sentenceId": str(sentence.get("id") or ""),
                "startTime": sentence.get("startTime"),
                "endTime": sentence.get("endTime"),
                "sourceText": transcript_text([sentence], language),
                "explanationText": explanation,
                "reasons": issue_map[index],
                "suggestions": suggestions,
                "status": "pending",
            }
        )

    status = "needs_review" if items else "passed"
    return {
        "schemaVersion": 1,
        "type": "transcript-correction-review",
        "status": status,
        "courseId": manifest.get("courseId"),
        "contentRevision": manifest.get("contentRevision"),
        "transcriptSource": manifest.get("buildMetadata", {}).get("transcriptSource"),
        "verification": {
            "mode": verification.get("mode"),
            "selected": verification.get("selected"),
            "comparison": verification.get("comparison"),
        }
        if isinstance(verification, dict)
        else None,
        "candidateCount": len(items),
        "items": items,
    }


def extract_correction_suggestions(explanation: str) -> list[str]:
    suggestions: list[str] = []
    for pattern in CORRECTION_SUGGESTION_PATTERNS:
        for match in pattern.finditer(explanation):
            value = match.group(1).strip()
            if value and value not in suggestions:
                suggestions.append(value)
    return suggestions


def install(
    destination: Path,
    manifest: dict[str, Any],
    ref,
    transcript_meta: dict[str, Any],
    text_config: Any,
    args: argparse.Namespace,
) -> None:
    """Write the course folder. There is no media file to copy — that is the point."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.installing"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        write_json(staging / "manifest.json", manifest)
        write_json(staging / "install-source.json", {
            "kind": "online-video",
            "provider": ref.provider,
            "control": ref.control,
            "videoId": ref.video_id,
            "pageUrl": ref.page_url,
            "transcriptSource": transcript_meta["transcriptSource"],
            "retrievedAt": manifest["buildMetadata"]["retrievedAt"],
            # describe() reports environment variable NAMES, never their values.
            "enrichment": text_config.describe() if text_config is not None else None,
            "asr": transcript_meta.get("asr"),
            "verification": transcript_meta.get("verification"),
            "contentPatches": manifest.get("buildMetadata", {}).get("contentPatches", []),
            "redistributable": False,
            "note": "媒体从未下载或存储；本课程不可再分发。"
                    " / The media was never downloaded or stored; this course is not redistributable.",
        })
        if destination.exists():
            replaced = destination.parent / f".{destination.name}.replaced"
            if replaced.exists():
                shutil.rmtree(replaced)
            destination.rename(replaced)
            staging.rename(destination)
            shutil.rmtree(replaced, ignore_errors=True)
        else:
            staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def print_summary(destination: Path, manifest: dict[str, Any], ref, transcript_meta: dict[str, Any]) -> None:
    print("\n" + "=" * 68)
    print(f"课程已写入 / course written: {destination}")
    print(f"  句数 / sentences      : {len(manifest['sentences'])}")
    print(f"  来源 / transcript from: {transcript_meta['transcriptSource']}")
    print(f"  控制档 / control tier : {ref.control} — {control_label(ref.control)}")
    print("  媒体 / media          : 未下载，未存储 (never downloaded, never stored)")
    print("  再分发 / redistribute  : 否 / no")
    print("\n打开这门课 / open it with:")
    print(f"  python start_dictation.py --manifest \"{destination / 'manifest.json'}\"")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_video_course.py",
        description="用在线视频做听力课程，不下载视频。/ Build a listening course from an online video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--url", help="视频页面链接 / the video page URL")
    parser.add_argument("--page-url", help="配合 --subtitles 使用：字幕属于哪个页面")
    parser.add_argument("--subtitles", help="本地 .srt/.vtt/.json3 字幕文件")
    parser.add_argument(
        "--transcript",
        choices=TRANSCRIPT_SOURCES,
        default="auto",
        help=(
            "verified=站点字幕与本地 ASR 双源核验；auto=有字幕用字幕，没有就本地转写；"
            "subs=只用站点字幕；asr=直接本地转写；file=用 --subtitles"
        ),
    )
    parser.add_argument(
        "--no-audio-fetch",
        action="store_true",
        help="禁止 auto 回退到临时取音频转写（没有字幕时直接失败）",
    )
    parser.add_argument("--sub-langs", default="", help="字幕语言优先顺序，逗号分隔，如 ja,ja-JP,en")
    parser.add_argument("--language", default="auto", help=f"源语言，默认 auto。可选：{', '.join(SUPPORTED_LANGUAGE_CODES)}")
    parser.add_argument("--title", help="课程标题，默认用视频标题")
    parser.add_argument("--name", help="courses/<name> 文件夹名，默认由标题生成")
    parser.add_argument("--courses-dir", help=f"课程库目录，默认 {DEFAULT_COURSES_DIR}")
    parser.add_argument("--clip", nargs=2, metavar=("START", "END"), help="只学视频的这一段，支持秒或 mm:ss")
    parser.add_argument("--profile", help="翻译讲解用的文本 profile 名")
    parser.add_argument("--asr-profile", help="本地转写用的 ASR profile 名")
    parser.add_argument("--config", help="provider 配置文件，默认 config/providers.json")
    parser.add_argument("--no-enrich", action="store_true", help="不生成翻译与讲解")
    parser.add_argument("--allow-stub-enrichment", action="store_true", help="允许用占位桩产物打包")
    parser.add_argument(
        "--rolling-window",
        action="store_true",
        help="对 --transcript file 的字幕也做滚动窗口去重（自动字幕导出的文件才需要）",
    )
    parser.add_argument("--ytdlp", help="yt-dlp 可执行文件路径")
    parser.add_argument("--work-dir", help="中间产物目录，默认 video-work/<name>")
    parser.add_argument(
        "--content-patch",
        action="append",
        default=[],
        help="在审计前应用已审核且 source-digest 绑定的修正 JSON；可重复",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="复用与当前视频/ASR/文本 provider 输入摘要一致的转写和 enrichment",
    )
    parser.add_argument("--keep-going", action="store_true", help="单批失败后继续")
    parser.add_argument("--strict-quality", action="store_true", help="有警告也拒绝安装")
    parser.add_argument("--allow-failed", action="store_true", help="即使审计有错误也写入课程（仅供排查）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不抓取不调用不写入")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的课程文件夹")
    parser.add_argument("--list-profiles", action="store_true", help="列出配置里可用的 profile")
    args = parser.parse_args(argv)

    if not args.list_profiles and not (args.url or args.page_url):
        parser.error("--url is required (or --page-url with --transcript file).")
    if args.transcript == "file" and not args.subtitles:
        parser.error("--transcript file requires --subtitles.")
    if args.language != "auto" and args.language not in SUPPORTED_LANGUAGE_CODES:
        parser.error(f"Unsupported --language {args.language!r}. Choose from: {', '.join(SUPPORTED_LANGUAGE_CODES)}.")
    return args


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConfigError, MediaSourceError) as error:
        raise SystemExit(str(error)) from error
