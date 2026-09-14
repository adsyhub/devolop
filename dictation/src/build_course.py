r"""The course build pipeline, with every model chosen at run time.

    audio  ->  ASR provider  ->  sentence merge  ->  text provider
           ->  Simplified-Chinese normalization  ->  stable content model
           ->  quality gate  ->  verified ZIP  ->  (optional) installed course

No model name appears in this file. Both providers are resolved from
``config/providers.json``, environment variables and flags (see
:mod:`provider_config`), so switching from a hosted API to a local runtime, to an
AI CLI you already pay for, or to a transcript you produced elsewhere, is a
command-line change rather than a code change.

Minimal runs, one per style of provider::

    # hosted API, key read from the named environment variable
    python src/build_course.py --audio in.mp3 --profile deepseek

    # a model running on this machine, no key at all
    python src/build_course.py --audio in.mp3 \
        --kind openai-compat --base-url http://127.0.0.1:11434/v1 --model qwen2.5:7b

    # a subscription CLI used as the API
    python src/build_course.py --audio in.mp3 --kind cli --command "claude -p"

    # no automation: answer prompt files by hand in any chat window
    python src/build_course.py --audio in.mp3 --kind manual --handoff-dir .\handoff

Run ``--list-profiles`` to see what the current config offers, and ``--dry-run``
to print the resolved plan without transcribing or calling anything.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from asr_providers import AsrError, Transcription, build_asr_provider, split_long_segments
from bundle_io import (
    build_zip,
    confidence_from_logprob,
    files_have_same_content,
    format_timestamp,
    load_json,
    normalize_text,
    safe_audio_name,
    safe_filename,
    sha256_file,
    write_json,
)
from bundle_quality import audit_manifest, enforce_quality_gate
from chinese_localization import convert_manifest, load_opencc_converter
from course_schema import prepare_course_manifest
from enrichment import (
    generate_results,
    merge_results_into_manifest,
    results_used_stub,
    write_batches,
)
from language_support import (
    SUPPORTED_LANGUAGE_CODES,
    manifest_language_code,
    normalize_language_code,
    set_source_text,
    transcript_text,
    translation_text,
    upgrade_manifest_language,
)
from provider_config import (
    ASR_KINDS,
    TEXT_KINDS,
    ConfigError,
    asr_profile_for_language,
    list_profiles,
    load_config_file,
    resolve_asr_provider,
    resolve_text_provider,
)
from sentence_segmentation import merge_sentence_fragments
from text_providers import build_text_provider, provider_env_summary

PROJECT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = Path(__file__).resolve().parent / "web"

SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".mp4",
    ".webm",
    ".mpeg",
    ".mpga",
    ".ogg",
    ".opus",
    ".flac",
}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config, config_path = load_config_file(args.config)

    if args.list_profiles:
        print_profiles(config, config_path)
        return 0

    # A transcribe-only run never reaches a text model, so it must not be made to
    # name one: --no-enrich with no model configured is a legitimate build.
    text_config = (
        None
        if args.no_enrich
        else resolve_text_provider(config=config, profile=args.profile, overrides=text_overrides(args))
    )
    asr_config = resolve_asr_provider(
        config=config,
        profile=args.asr_profile,
        overrides=asr_overrides(args),
        language=args.language,
    )

    audio_path = resolve_audio(args.audio)
    title = args.title.strip() if args.title and args.title.strip() else audio_path.stem.strip() or "dictation-course"
    out_path = resolve_output_path(audio_path, args.out, title)
    work_dir = (
        Path(args.work_dir).expanduser().resolve()
        if args.work_dir
        else out_path.with_suffix("").with_name(f"{out_path.stem}-work").resolve()
    )

    print(f"Config     : {config_path or '(none found; using flags and environment only)'}")
    print(f"ASR        : {asr_config.kind} " + summarize_asr(asr_config))
    routed = asr_profile_for_language(config, args.language)
    if routed and not args.asr_profile and routed == asr_config.label:
        print(f"             (routed by language {args.language!r} -> profile {routed!r})")
    elif config.get("asrLanguageProfiles") and not args.asr_profile and not routed:
        print(
            "             (no language routing: --language is 'auto' or unmapped; "
            "pass --language to route)"
        )
    print(f"Enrichment : {provider_env_summary(text_config) if text_config else 'disabled (--no-enrich)'}")
    print(f"Audio      : {audio_path}")
    print(f"Title      : {title}")
    print(f"Work dir   : {work_dir}")
    print(f"Output ZIP : {out_path}")

    if args.dry_run:
        print("\nDry run: nothing was transcribed, called, or written.")
        return 0

    if out_path.exists() and not args.force:
        raise SystemExit(f"Output ZIP already exists: {out_path}. Use --force to overwrite.")

    asr_provider = build_asr_provider(asr_config)
    asr_provider.preflight()
    text_provider = None
    if text_config is not None:
        text_provider = build_text_provider(text_config)
        text_provider.preflight()

    work_dir.mkdir(parents=True, exist_ok=True)
    audio_name = safe_audio_name(audio_path)
    bundle_audio_path = work_dir / audio_name
    ensure_audio_copied(audio_path, bundle_audio_path)

    transcribed_manifest_path = work_dir / "manifest.transcribed.json"
    raw_segments_path = work_dir / "segments.raw.json"
    final_manifest_path = work_dir / "manifest.json"
    batches_dir = work_dir / "deepseek_batches"
    results_dir = batches_dir / "results"

    if args.resume and transcribed_manifest_path.exists():
        print(f"\nReusing transcription: {transcribed_manifest_path}")
        manifest = load_json(transcribed_manifest_path)
        validate_resume_manifest(manifest, bundle_audio_path, asr_config)
    else:
        print("")
        transcription = run_transcription(asr_provider, bundle_audio_path)
        manifest = manifest_from_transcription(
            transcription,
            title=title,
            audio_name=audio_name,
            audio_path=bundle_audio_path,
            asr_config=asr_config,
            raw_segments_path=raw_segments_path,
        )
        write_json(transcribed_manifest_path, manifest)

    # Also migrates a resumed v1 Japanese manifest without changing its stable
    # ids, so sourceText/locales exist for every later stage.
    upgrade_manifest_language(manifest)

    enrichment_meta: dict[str, Any] = {"enabled": not args.no_enrich}
    if text_provider is not None:
        batches = write_batches(
            manifest, batches_dir, batch_size=text_config.batch_size, force=not args.resume
        )
        if not batches:
            raise SystemExit("No sentences with text to enrich.")
        print(f"\nBatches: {len(batches)} in {batches_dir}")
        run_stats = generate_results(
            text_provider,
            batches,
            results_dir,
            resume=args.resume,
            keep_going=args.keep_going,
            sleep=text_config.sleep,
            retries=text_config.retries,
        )
        merge_stats = merge_results_into_manifest(manifest, results_dir)
        print(
            f"Merged: files={merge_stats['files']}, translations={merge_stats['translations']}, "
            f"explanations={merge_stats['explanations']}, models={merge_stats['models'] or ['(unreported)']}"
        )
        used_stub = results_used_stub(results_dir)
        if used_stub and not args.allow_stub_enrichment:
            raise SystemExit(
                "Refusing to package a course whose explanations came from a stub provider.\n"
                "  The 'echo' provider writes placeholders, not teaching content; packaging it\n"
                "  would put text in front of a learner that no model or person ever wrote.\n"
                "  Re-run with a real provider, or pass --allow-stub-enrichment for a scaffold\n"
                "  that is explicitly marked unpublishable."
            )
        enrichment_meta.update(
            {
                "provider": text_config.describe(),
                "models": merge_stats["models"],
                "translations": merge_stats["translations"],
                "explanations": merge_stats["explanations"],
                "generatedBatches": run_stats["generated"],
                "reusedBatches": run_stats["reused"],
                "usage": run_stats["usage"],
                "stub": used_stub,
            }
        )

        if not args.no_normalize:
            try:
                manifest, changed_fields = convert_manifest(manifest, load_opencc_converter())
            except RuntimeError as exc:
                raise SystemExit(
                    f"{exc}\n  Install requirements.txt, or pass --no-normalize to skip the\n"
                    "  Traditional-to-Simplified pass (the manifest then keeps whatever the model wrote)."
                ) from exc
            print(f"Normalized Chinese: locale=zh-Hans-CN, changedFields={changed_fields}")
            enrichment_meta["normalized"] = True
        else:
            enrichment_meta["normalized"] = False
            print("Skipping Simplified-Chinese normalization (--no-normalize).")
    else:
        print("\nSkipping enrichment (--no-enrich): the course will have no translations.")

    manifest = prepare_course_manifest(manifest, audio_sha256=sha256_file(bundle_audio_path))
    build_metadata = manifest.setdefault("buildMetadata", {})
    build_metadata["asr"] = asr_config.describe()
    build_metadata["enrichment"] = enrichment_meta
    if enrichment_meta.get("stub"):
        manifest.setdefault("review", {})["humanListening"] = "blocked"

    quality_report = audit_manifest(manifest, require_enrichment=not args.no_enrich)
    quality_report_path = work_dir / "quality-report.json"
    write_json(quality_report_path, quality_report)
    print_quality_summary(quality_report)
    try:
        enforce_quality_gate(quality_report, strict=args.strict_quality)
    except ValueError as exc:
        raise SystemExit(f"{exc}\n  Inspect {quality_report_path} for the per-sentence issue list.") from exc

    manifest["quality"] = {"status": quality_report["status"], **quality_report["summary"]}
    write_json(final_manifest_path, manifest)

    build_zip(
        final_manifest_path,
        bundle_audio_path,
        audio_name,
        out_path,
        quality_report_path=quality_report_path,
        web_dir=WEB_DIR,
        force=True,
    )
    print_summary(out_path, final_manifest_path, raw_segments_path, manifest)

    if args.install is not None:
        from install_course import install_bundle

        destination = install_bundle(
            out_path,
            courses_dir=Path(args.install) if args.install else PROJECT_DIR / "courses",
            course_name=args.course_name,
            force=args.force,
            allow_failed=args.allow_stub_enrichment,
        )
        print(f"\nInstalled course: {destination}")
        print(f'Play it with: python .\\start_dictation.py --manifest "{destination / "manifest.json"}"')
    return 0


# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------


def run_transcription(provider: Any, audio_path: Path) -> Transcription:
    state = {"bucket": -1}

    def progress(*, current_time: float, total_duration: float, count: int) -> None:
        if total_duration > 0:
            percent = min(100.0, max(0.0, current_time / total_duration) * 100.0)
            bucket = int(percent)
            if bucket == state["bucket"]:
                return
            state["bucket"] = bucket
            print(
                f"\rTranscribing: {percent:6.2f}% | "
                f"{format_timestamp(min(current_time, total_duration))} / {format_timestamp(total_duration)} | "
                f"segments={count}",
                end="",
                flush=True,
            )
        elif count != state["bucket"]:
            state["bucket"] = count
            print(f"\rTranscribing: segments={count}", end="", flush=True)

    print(f"Transcribing with {provider.config.kind}...")
    transcription = provider.transcribe(audio_path, progress=progress)
    if state["bucket"] >= 0:
        print("")
    print(f"Segments: {len(transcription.segments)}")
    if provider.config.max_segment_seconds > 0:
        transcription.segments, splits = split_long_segments(
            transcription.segments, max_seconds=provider.config.max_segment_seconds
        )
        if splits:
            print(
                f"Split {splits} over-long segment(s) at internal pauses "
                f"(> {provider.config.max_segment_seconds:g}s) -> {len(transcription.segments)} segments"
            )
    return transcription


def manifest_from_transcription(
    transcription: Transcription,
    *,
    title: str,
    audio_name: str,
    audio_path: Path,
    asr_config: Any,
    raw_segments_path: Path,
) -> dict[str, Any]:
    detected = transcription.language or asr_config.language
    try:
        source_language = normalize_language_code(detected)
    except ValueError as exc:
        raise SystemExit(
            f"{exc}\n  Set --language to one of: {', '.join(SUPPORTED_LANGUAGE_CODES)}."
        ) from exc

    if transcription.duration > 0:
        print(f"Audio duration: {format_timestamp(transcription.duration)}")

    sentences: list[dict[str, Any]] = []
    raw_segments: list[dict[str, Any]] = []
    for segment in transcription.segments:
        text = normalize_text(segment.text)
        if not text:
            continue
        start = round(float(segment.start), 3)
        end = round(max(float(segment.end), start + asr_config.min_duration), 3)
        item: dict[str, Any] = {
            "startTime": start,
            "endTime": end,
            "sourceText": text,
            "translationText": "",
            "zhTranslation": "",
        }
        set_source_text(item, text, source_language)
        confidence = confidence_from_logprob(segment.avg_logprob)
        if confidence is not None:
            item["confidence"] = confidence

        raw_item = dict(item)
        raw_item.update(
            {
                "avgLogprob": segment.avg_logprob,
                "noSpeechProb": segment.no_speech_prob,
                "compressionRatio": segment.compression_ratio,
            }
        )
        if segment.words:
            raw_item["words"] = segment.words

        sentences.append(item)
        raw_segments.append(raw_item)

    if not sentences:
        raise SystemExit(
            "No speech segments were produced. Check the audio file and the --language setting."
        )

    raw_count = len(sentences)
    sentences = merge_sentence_fragments(sentences, source_language)

    manifest = {
        "schemaVersion": 1,
        "title": title,
        "audio": audio_name,
        "sourceLanguage": source_language,
        "transcriptText": transcript_text(sentences, source_language),
        "sentences": sentences,
        "buildMetadata": {
            "sourceAudioSha256": sha256_file(audio_path),
            "sourceAudioBytes": audio_path.stat().st_size,
            "detectedLanguage": source_language,
            "detectedLanguageProbability": transcription.language_probability,
            "transcriptionConfig": asr_config.cache_key(),
        },
    }
    upgrade_manifest_language(manifest, source_language)

    write_json(
        raw_segments_path,
        {
            "provider": transcription.provider,
            "language": source_language,
            "languageProbability": transcription.language_probability,
            "duration": transcription.duration,
            "segments": raw_segments,
        },
    )
    print(f"Sentences: {len(sentences)} (merged from {raw_count} raw segments)")
    return manifest


def validate_resume_manifest(manifest: dict[str, Any], audio_path: Path, asr_config: Any) -> None:
    metadata = manifest.get("buildMetadata")
    if not isinstance(metadata, dict):
        raise SystemExit(
            "Cannot safely resume: manifest.transcribed.json has no buildMetadata.\n"
            "  Run once without --resume to create a verifiable cache."
        )
    expected_hash = str(metadata.get("sourceAudioSha256") or "")
    if not expected_hash or expected_hash != sha256_file(audio_path):
        raise SystemExit("Cannot resume: the cached transcription belongs to a different audio file.")
    cached_config = metadata.get("transcriptionConfig")
    if cached_config != asr_config.cache_key():
        raise SystemExit(
            "Cannot resume: ASR settings changed since the cached transcription.\n"
            f"  cached : {json.dumps(cached_config, ensure_ascii=False, sort_keys=True)}\n"
            f"  current: {json.dumps(asr_config.cache_key(), ensure_ascii=False, sort_keys=True)}\n"
            "  Run without --resume, or restore the previous ASR settings."
        )


def ensure_audio_copied(audio_path: Path, bundle_audio_path: Path) -> None:
    if bundle_audio_path.exists() and files_have_same_content(audio_path, bundle_audio_path):
        return
    bundle_audio_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(audio_path, bundle_audio_path)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_course.py",
        description="Build a dictation course from audio using any ASR and any text model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Provider resolution, last wins:\n"
            "  built-in shape defaults -> config profile -> environment -> these flags\n"
            "No model is hard-coded; a network provider with no model is a startup error.\n"
        ),
    )
    parser.add_argument("--audio", help="Input audio file.")
    parser.add_argument("--title", help="Course title. Default: the audio file stem.")
    parser.add_argument("--out", help="Output ZIP path or folder.")
    parser.add_argument("--work-dir", help="Where transcripts, batches and results are kept.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output.")
    parser.add_argument("--resume", action="store_true", help="Reuse a valid cached transcription and results.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved plan and stop.")
    parser.add_argument("--list-profiles", action="store_true", help="List the profiles the config defines.")

    provider = parser.add_argument_group("text provider (translations and explanations)")
    provider.add_argument("--config", help="Provider config file. Default: config/providers.json.")
    provider.add_argument("--profile", help="Named text profile from the config.")
    provider.add_argument("--kind", choices=TEXT_KINDS, help="Text provider kind.")
    provider.add_argument("--model", help="Model name. Required for network kinds; no default exists.")
    provider.add_argument("--base-url", help="API base URL, local runtimes included.")
    provider.add_argument("--api-key-env", help="NAME of the env var holding the key, never the key itself.")
    provider.add_argument("--command", help='Command for --kind cli, e.g. "claude -p".')
    provider.add_argument("--handoff-dir", help="Prompt/reply folder for --kind manual.")
    provider.add_argument("--batch-size", type=int, help="Sentences per request.")
    provider.add_argument("--max-tokens", type=int, help="Max output tokens per request.")
    provider.add_argument("--temperature", type=float, help="Sampling temperature, 0-2.")
    provider.add_argument("--retries", type=int, help="Attempts per batch.")
    provider.add_argument("--sleep", type=float, help="Seconds between batches.")
    provider.add_argument("--timeout", type=float, help="Per-request timeout in seconds.")
    provider.add_argument("--no-json-mode", action="store_true", help="Do not request a JSON response format.")
    provider.add_argument("--extra-body", help="JSON object merged into every request body.")
    provider.add_argument("--keep-going", action="store_true", help="Continue after a failed batch.")
    provider.add_argument("--no-enrich", action="store_true", help="Transcribe only; no translations.")
    provider.add_argument("--no-normalize", action="store_true", help="Skip the Traditional-to-Simplified pass.")
    provider.add_argument(
        "--allow-stub-enrichment",
        action="store_true",
        help="Package placeholder explanations, marked unpublishable. For scaffolding only.",
    )

    asr = parser.add_argument_group("ASR provider (audio to timed segments)")
    asr.add_argument("--asr-profile", help="Named ASR profile from the config.")
    asr.add_argument("--asr-kind", choices=ASR_KINDS, help="ASR provider kind.")
    asr.add_argument("--asr-model", help="ASR model name or path.")
    asr.add_argument("--asr-base-url", help="Base URL for --asr-kind openai-audio.")
    asr.add_argument("--asr-api-key-env", help="NAME of the env var holding the ASR key.")
    asr.add_argument("--asr-command", help="Command for --asr-kind command.")
    asr.add_argument("--transcript", help="Existing transcript for --asr-kind import (JSON/SRT/VTT).")
    asr.add_argument("--asr-device", help="faster-whisper device: auto, cpu, or cuda.")
    asr.add_argument("--asr-compute-type", help="faster-whisper compute type, e.g. int8 or float16.")
    asr.add_argument("--asr-timeout", type=float, help="ASR timeout in seconds.")
    asr.add_argument("--language", help="Source language code, or auto.")
    asr.add_argument("--beam-size", type=int, help="Whisper beam size.")
    asr.add_argument("--no-vad", action="store_true", help="Disable the VAD filter.")
    asr.add_argument("--word-timestamps", action="store_true", help="Keep word timings in segments.raw.json.")
    asr.add_argument("--min-duration", type=float, help="Minimum segment duration in seconds.")
    asr.add_argument("--strict-quality", action="store_true", help="Refuse to publish on warnings, not just errors.")

    install = parser.add_argument_group("install")
    install.add_argument(
        "--install",
        nargs="?",
        const="",
        default=None,
        metavar="COURSES_DIR",
        help="After building, unpack into courses/ (or the given folder) so it is playable.",
    )
    install.add_argument("--course-name", help="Folder name under courses/. Default: from the title.")

    args = parser.parse_args(argv)
    if not args.list_profiles and not args.audio:
        parser.error("--audio is required (or use --list-profiles).")
    if args.language and args.language != "auto":
        try:
            args.language = normalize_language_code(args.language)
        except ValueError as exc:
            parser.error(str(exc))
    return args


def text_overrides(args: argparse.Namespace) -> dict[str, Any]:
    overrides: dict[str, Any] = {
        "kind": args.kind,
        "model": args.model,
        "baseUrl": args.base_url,
        "apiKeyEnv": args.api_key_env,
        "command": args.command,
        "handoffDir": args.handoff_dir,
        "batchSize": args.batch_size,
        "maxTokens": args.max_tokens,
        "temperature": args.temperature,
        "retries": args.retries,
        "sleep": args.sleep,
        "timeout": args.timeout,
    }
    if args.no_json_mode:
        overrides["jsonMode"] = False
    if args.extra_body:
        try:
            parsed = json.loads(args.extra_body)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"--extra-body is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ConfigError("--extra-body must be a JSON object.")
        overrides["extraBody"] = parsed
    return overrides


def asr_overrides(args: argparse.Namespace) -> dict[str, Any]:
    overrides: dict[str, Any] = {
        "kind": args.asr_kind,
        "model": args.asr_model,
        "baseUrl": args.asr_base_url,
        "apiKeyEnv": args.asr_api_key_env,
        "command": args.asr_command,
        "transcript": args.transcript,
        "device": args.asr_device,
        "computeType": args.asr_compute_type,
        "timeout": args.asr_timeout,
        "language": args.language,
        "beamSize": args.beam_size,
        "minDuration": args.min_duration,
    }
    if args.no_vad:
        overrides["vadFilter"] = False
    if args.word_timestamps:
        overrides["wordTimestamps"] = True
    if args.transcript and not args.asr_kind:
        overrides["kind"] = "import"
    if args.asr_command and not args.asr_kind:
        overrides["kind"] = "command"
    return overrides


def resolve_audio(value: str) -> Path:
    audio_path = Path(value).expanduser().resolve()
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")
    if audio_path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise SystemExit(
            f"Unsupported audio extension: {audio_path.suffix}. "
            f"Use one of: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
        )
    return audio_path


def resolve_output_path(audio_path: Path, out_value: str | None, title: str) -> Path:
    default_name = f"{safe_filename(title)}-course.zip"
    if not out_value:
        return audio_path.with_name(default_name).resolve()

    raw_out = Path(out_value).expanduser()
    text = str(out_value).strip()
    looks_like_folder = (
        text.endswith(("\\", "/"))
        or (raw_out.exists() and raw_out.is_dir())
        or raw_out.suffix == ""
    )
    if looks_like_folder:
        return (raw_out / default_name).resolve()
    if raw_out.suffix.lower() != ".zip":
        return raw_out.with_suffix(".zip").resolve()
    return raw_out.resolve()


def summarize_asr(asr_config: Any) -> str:
    parts = []
    if asr_config.model:
        parts.append(f"model={asr_config.model}")
    if asr_config.base_url:
        parts.append(f"baseUrl={asr_config.base_url}")
    if asr_config.command:
        parts.append(f"command={asr_config.command[0]}")
    if asr_config.transcript_path:
        parts.append(f"transcript={asr_config.transcript_path}")
    if asr_config.kind == "faster-whisper":
        parts.append(f"device={asr_config.device}/{asr_config.compute_type}")
    parts.append(f"language={asr_config.language}")
    return ", ".join(parts)


def print_profiles(config: dict[str, Any], config_path: Path | None) -> None:
    profiles = list_profiles(config)
    print(f"Config: {config_path or '(no config file found)'}")
    print(f"Default text profile: {config.get('defaultTextProfile') or '(none)'}")
    print(f"Default ASR profile : {config.get('defaultAsrProfile') or '(none)'}")
    for family in ("text", "asr"):
        names = profiles[family]
        print(f"\n{family} profiles ({len(names)}):")
        for name in names:
            entry = config.get(f"{family}Profiles", {}).get(name, {})
            detail = ", ".join(
                f"{key}={entry[key]}"
                for key in ("kind", "model", "baseUrl", "apiKeyEnv")
                if entry.get(key)
            )
            print(f"  {name}: {detail or '(inherits defaults)'}")
    if config_path is None:
        print(
            "\nNo config file yet. Copy config/providers.example.json to config/providers.json\n"
            "and edit it, or pass every setting on the command line."
        )


def print_quality_summary(report: dict[str, Any]) -> None:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    print(
        f"Quality: status={report.get('status', 'unknown')}, "
        f"errors={summary.get('errors', 0)}, warnings={summary.get('warnings', 0)}"
    )


def print_summary(out_path: Path, manifest_path: Path, raw_segments_path: Path, manifest: dict[str, Any]) -> None:
    sentences = manifest.get("sentences") if isinstance(manifest.get("sentences"), list) else []
    zh_count = sum(1 for item in sentences if isinstance(item, dict) and translation_text(item))
    explanations = sum(
        1 for item in sentences if isinstance(item, dict) and str(item.get("explanationText") or "").strip()
    )
    print("")
    print("Done.")
    print(f"ZIP          : {out_path}")
    print(f"Manifest     : {manifest_path}")
    print(f"Raw segments : {raw_segments_path}")
    print(f"Sentences    : {len(sentences)}")
    print(f"Language     : {manifest_language_code(manifest)}")
    print(f"Translations : {zh_count}")
    print(f"Explanations : {explanations}")


if __name__ == "__main__":
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    try:
        raise SystemExit(main())
    except (AsrError, ConfigError) as error:
        print(f"\n{error}", file=sys.stderr)
        raise SystemExit(2) from error
