"""
Repack an offline dictation bundle from a manifest and its audio file.

The output ZIP will contain manifest.json and the audio file at the path named
by manifest["audio"].
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from build_deepseek_offline_bundle import build_zip, sha256_file, verify_zip, write_json
from bundle_quality import audit_manifest, enforce_quality_gate
from course_schema import prepare_course_manifest
from language_support import manifest_language_code, source_text


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    manifest = load_json(manifest_path)
    if isinstance(manifest.get("media"), dict):
        raise SystemExit(
            "在线视频课程没有可重新打包的媒体，而且不可再分发。"
            " / An online-video course has no media to repack and is not redistributable."
        )
    audio_name = validate_audio_name(manifest.get("audio"))
    audio_path = Path(args.audio).expanduser().resolve() if args.audio else manifest_path.parent / audio_name

    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")
    manifest = prepare_course_manifest(manifest, audio_sha256=sha256_file(audio_path))
    validate_manifest(manifest)
    if out_path.exists() and not args.force:
        raise SystemExit(f"Output already exists: {out_path}. Use --force to overwrite.")

    report = audit_manifest(manifest, require_enrichment=not args.no_enrichment)
    try:
        enforce_quality_gate(report, strict=args.strict_quality)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    manifest["quality"] = {"status": report["status"], **report["summary"]}
    web_dir = Path(__file__).resolve().parent / "web"
    with tempfile.TemporaryDirectory(prefix="dictation-repack-") as temp_dir:
        temp_path = Path(temp_dir)
        publish_manifest_path = temp_path / "manifest.json"
        quality_report_path = temp_path / "quality-report.json"
        write_json(publish_manifest_path, manifest)
        write_json(quality_report_path, report)
        build_zip(
            publish_manifest_path,
            audio_path,
            audio_name,
            out_path,
            quality_report_path=quality_report_path,
            web_dir=web_dir,
            force=True,
        )
    verify_zip(out_path)

    print(f"ZIP written: {out_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Audio: {audio_path} -> {audio_name}")
    print(f"Sentences: {len(manifest.get('sentences', []))}")
    print(f"Quality: {report['status']} (errors={report['summary']['errors']}, warnings={report['summary']['warnings']})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repack offline dictation manifest and audio into ZIP.")
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON.")
    parser.add_argument("--audio", help="Audio file path. Default: manifest folder + manifest audio name.")
    parser.add_argument("--out", required=True, help="Output ZIP path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output ZIP.")
    parser.add_argument("--strict-quality", action="store_true", help="Refuse to package manifests with warnings.")
    parser.add_argument("--no-enrichment", action="store_true", help="Do not require translations and explanations.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected a JSON object: {path}")
    return data


def validate_audio_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit('manifest must contain a non-empty "audio" string.')
    audio_name = value.strip().replace("\\", "/")
    path = PurePosixPath(audio_name)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"Unsafe audio path in manifest: {value!r}")
    if len(path.parts) != 1:
        raise SystemExit(
            f"This app bundle format expects the audio file at ZIP root, got: {value!r}"
        )
    return audio_name


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schemaVersion") != 1:
        raise SystemExit("Only schemaVersion 1 is supported.")
    sentences = manifest.get("sentences")
    if not isinstance(sentences, list) or not sentences:
        raise SystemExit("manifest must contain a non-empty sentences array.")

    language = manifest_language_code(manifest)
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            raise SystemExit(f"Sentence {index} must be an object.")
        for key in ("startTime", "endTime"):
            if key not in sentence:
                raise SystemExit(f"Sentence {index} is missing {key}.")
        if not source_text(sentence, language):
            raise SystemExit(f"Sentence {index} is missing sourceText.")
        try:
            start = float(sentence["startTime"])
            end = float(sentence["endTime"])
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"Sentence {index} has invalid timestamps.") from exc
        if end <= start:
            raise SystemExit(f"Sentence {index} must have endTime > startTime.")


if __name__ == "__main__":
    main()
