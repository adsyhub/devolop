"""Upgrade a course manifest to the stable commercial content model."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_deepseek_offline_bundle import load_json, sha256_file, write_json
from bundle_quality import audit_manifest, enforce_quality_gate
from course_schema import prepare_course_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Add stable IDs, content types, and practice metadata.")
    parser.add_argument("--manifest", required=True, help="Source manifest JSON.")
    parser.add_argument("--out", required=True, help="Upgraded manifest JSON.")
    parser.add_argument("--audio", help="Audio used to derive a stable course ID and verify continuity.")
    parser.add_argument("--strict-quality", action="store_true", help="Fail if automated checks return warnings.")
    parser.add_argument("--force", action="store_true", help="Overwrite the output file.")
    args = parser.parse_args()

    source_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.out).expanduser().resolve()
    if output_path.exists() and not args.force:
        raise SystemExit(f"Output already exists: {output_path}. Use --force to overwrite.")

    audio_hash = None
    if args.audio:
        audio_path = Path(args.audio).expanduser().resolve()
        if not audio_path.is_file():
            raise SystemExit(f"Audio file not found: {audio_path}")
        audio_hash = sha256_file(audio_path)

    prepared = prepare_course_manifest(load_json(source_path), audio_sha256=audio_hash)
    report = audit_manifest(prepared, require_enrichment=True)
    try:
        enforce_quality_gate(report, strict=args.strict_quality)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    prepared["quality"] = {"status": report["status"], **report["summary"]}
    write_json(output_path, prepared)
    write_json(output_path.with_suffix(".quality-report.json"), report)

    print(f"Prepared manifest: {output_path}")
    print(f"Course ID: {prepared['courseId']}")
    print(f"Content revision: {prepared['contentRevision']}")
    print(
        f"Practice: {prepared['practiceSentenceCount']} / "
        f"{len(prepared['sentences'])} audio segments"
    )
    print(
        f"Quality: {report['status']} "
        f"(errors={report['summary']['errors']}, warnings={report['summary']['warnings']})"
    )


if __name__ == "__main__":
    main()
