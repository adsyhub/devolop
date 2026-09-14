"""
Create an offline multilingual dictation ZIP bundle.

Default mode is optimized for an NVIDIA RTX Ada GPU:
  faster-whisper large-v3 + CUDA + float16

Install:
  python -m pip install faster-whisper

Example:
  python tools/create_offline_bundle.py ^
    --audio "C:\\Users\\cribug\\Downloads\\2010骞?2链圢2.mp3" ^
    --title "2010骞?2链圢2" ^
    --out "C:\\Users\\cribug\\Documents\\Codex\\2010-12-N2-large-v3.zip"
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from language_support import (
    SUPPORTED_LANGUAGE_CODES,
    normalize_language_code,
    set_source_text,
    transcript_text,
    upgrade_manifest_language,
)
from sentence_segmentation import merge_sentence_fragments


def configure_cuda_dll_search() -> None:
    """Make CUDA runtime DLLs visible to faster-whisper on Windows."""
    if os.name != "nt":
        return

    candidates: list[Path] = []
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        candidates.append(Path(cuda_path) / "bin")

    candidates.extend(
        [
            Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\bin"),
            Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin"),
            Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin"),
        ]
    )

    for candidate in candidates:
        if (candidate / "cublas64_12.dll").exists():
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(candidate))
            os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")
            return


configure_cuda_dll_search()

from faster_whisper import WhisperModel


SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".mp4",
    ".webm",
    ".mpeg",
    ".mpga",
}


def main() -> None:
    args = parse_args()
    audio_path = Path(args.audio).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    work_dir = Path(args.work_dir).expanduser().resolve() if args.work_dir else None

    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")
    if audio_path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        raise SystemExit(
            f"Unsupported audio extension: {audio_path.suffix}. "
            f"Use one of: {', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}"
        )

    if work_dir is None:
        with tempfile.TemporaryDirectory(prefix="dictation-bundle-") as tmp:
            create_bundle(audio_path, out_path, Path(tmp), args)
    else:
        work_dir.mkdir(parents=True, exist_ok=True)
        create_bundle(audio_path, out_path, work_dir, args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an offline dictation ZIP bundle.")
    parser.add_argument("--audio", required=True, help="Input audio file path.")
    parser.add_argument("--title", required=True, help="Project title shown in the app.")
    parser.add_argument("--out", required=True, help="Output ZIP path.")
    parser.add_argument("--work-dir", help="Optional working directory to keep manifest and raw segments.")
    parser.add_argument("--model", default="large-v3", help="faster-whisper model name. Default: large-v3.")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu", "auto"], help="Default: cuda.")
    parser.add_argument("--compute-type", default="float16", help="Default: float16. Fallback: int8_float16 or int8.")
    parser.add_argument(
        "--language",
        default="ja",
        help="Source language code, or auto. Supported: " + ", ".join(SUPPORTED_LANGUAGE_CODES) + ".",
    )
    parser.add_argument("--beam-size", type=int, default=5, help="Beam size. Default: 5.")
    parser.add_argument("--no-vad", action="store_true", help="Disable VAD filter.")
    parser.add_argument("--word-timestamps", action="store_true", help="Keep word timestamps in segments.raw.json.")
    parser.add_argument("--min-duration", type=float, default=0.2, help="Minimum segment duration in seconds.")
    args = parser.parse_args()
    if args.language != "auto":
        try:
            args.language = normalize_language_code(args.language)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    return args


def create_bundle(audio_path: Path, out_path: Path, work_dir: Path, args: argparse.Namespace) -> None:
    audio_name = safe_audio_name(audio_path)
    bundle_audio_path = work_dir / audio_name
    raw_segments_path = work_dir / "segments.raw.json"
    manifest_path = work_dir / "manifest.json"

    print(f"Copying audio: {audio_path}")
    shutil.copyfile(audio_path, bundle_audio_path)

    print(
        "Loading faster-whisper model "
        f"model={args.model}, device={args.device}, compute_type={args.compute_type}"
    )
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)

    print("Transcribing...")
    segments_iter, info = model.transcribe(
        str(bundle_audio_path),
        language=None if args.language == "auto" else args.language,
        beam_size=args.beam_size,
        vad_filter=not args.no_vad,
        word_timestamps=args.word_timestamps,
    )

    detected_language = getattr(info, "language", None) or ("ja" if args.language == "auto" else args.language)
    try:
        source_language = normalize_language_code(detected_language)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    duration = float(getattr(info, "duration", 0.0) or 0.0)
    if duration > 0:
        print(f"Audio duration: {format_timestamp(duration)}")
    else:
        print("Audio duration: unknown")

    sentences: list[dict[str, Any]] = []
    raw_segments: list[dict[str, Any]] = []

    progress_bucket = -1
    seen_segments = 0

    for segment in segments_iter:
        seen_segments += 1
        progress_bucket = print_transcription_progress(
            current_time=float(getattr(segment, "end", 0.0) or 0.0),
            total_duration=duration,
            segment_count=seen_segments,
            last_bucket=progress_bucket,
        )
        text = normalize_text(segment.text)
        if not text:
            continue

        start = round(float(segment.start), 3)
        end = round(max(float(segment.end), start + args.min_duration), 3)
        confidence = confidence_from_logprob(segment.avg_logprob)

        item: dict[str, Any] = {
            "startTime": start,
            "endTime": end,
            "sourceText": text,
            "translationText": "",
            "zhTranslation": "",
        }
        set_source_text(item, text, source_language)
        if confidence is not None:
            item["confidence"] = confidence

        raw_item: dict[str, Any] = {
            **item,
            "avgLogprob": segment.avg_logprob,
            "noSpeechProb": segment.no_speech_prob,
            "compressionRatio": segment.compression_ratio,
        }
        if args.word_timestamps:
            raw_item["words"] = [
                {
                    "start": round(float(word.start), 3),
                    "end": round(float(word.end), 3),
                    "word": word.word,
                    "probability": round(float(word.probability), 4),
                }
                for word in (segment.words or [])
            ]

        sentences.append(item)
        raw_segments.append(raw_item)

    finish_transcription_progress(duration, seen_segments)

    if not sentences:
        raise SystemExit("No speech segments were generated. Check the audio file and language setting.")

    raw_sentence_count = len(sentences)
    sentences = merge_sentence_fragments(sentences, source_language)

    manifest = {
        "schemaVersion": 1,
        "title": args.title,
        "audio": audio_name,
        "sourceLanguage": source_language,
        "transcriptText": transcript_text(sentences, source_language),
        "sentences": sentences,
        "buildMetadata": {
            "detectedLanguage": source_language,
            "detectedLanguageProbability": getattr(info, "language_probability", None),
        },
    }
    upgrade_manifest_language(manifest, source_language)

    raw_metadata = {
        "model": args.model,
        "device": args.device,
        "computeType": args.compute_type,
        "language": source_language,
        "languageProbability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "segments": raw_segments,
    }

    raw_segments_path.write_text(json.dumps(raw_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "manifest.json")
        zf.write(bundle_audio_path, audio_name)

    print("")
    print("Done.")
    print(f"ZIP: {out_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Raw segments: {raw_segments_path}")
    print(f"Sentences: {len(sentences)} (raw segments: {raw_sentence_count})")
    print(f"Audio duration: {getattr(info, 'duration', 'unknown')} seconds")
    print(f"Detected language: {getattr(info, 'language', args.language)}")


def safe_audio_name(audio_path: Path) -> str:
    suffix = audio_path.suffix.lower()
    if suffix == ".mpeg" or suffix == ".mpga":
        suffix = ".mp3"
    return f"audio{suffix}"


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def confidence_from_logprob(avg_logprob: float | None) -> float | None:
    if avg_logprob is None:
        return None
    return round(max(0.0, min(1.0, math.exp(avg_logprob))), 4)


def format_timestamp(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        return "--:--"

    total_seconds = int(round(seconds))
    minutes, sec = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:d}:{sec:02d}"


def print_transcription_progress(
    *,
    current_time: float,
    total_duration: float,
    segment_count: int,
    last_bucket: int,
) -> int:
    if total_duration > 0 and math.isfinite(total_duration):
        clamped_time = min(max(current_time, 0.0), total_duration)
        percent = min(100.0, (clamped_time / total_duration) * 100.0)
        bucket = int(percent)
        if bucket == last_bucket:
            return last_bucket

        print(
            "\r"
            f"Transcribing: {percent:6.2f}% | "
            f"{format_timestamp(clamped_time)} / {format_timestamp(total_duration)} | "
            f"segments={segment_count}",
            end="",
            flush=True,
        )
        return bucket

    if segment_count == last_bucket:
        return last_bucket

    print(f"\rTranscribing: segments={segment_count}", end="", flush=True)
    return segment_count


def finish_transcription_progress(total_duration: float, segment_count: int) -> None:
    if total_duration > 0 and math.isfinite(total_duration):
        print(
            "\r"
            f"Transcribing: 100.00% | "
            f"{format_timestamp(total_duration)} / {format_timestamp(total_duration)} | "
            f"segments={segment_count}"
        )
    else:
        print(f"\rTranscribing: segments={segment_count}")


if __name__ == "__main__":
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    main()

