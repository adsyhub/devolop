"""Normalize generated Chinese learning content to Simplified Chinese."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_deepseek_offline_bundle import load_json, write_json
from bundle_quality import audit_manifest, enforce_quality_gate
from chinese_localization import OPENCC_CONFIG, TARGET_LOCALE, convert_manifest, load_opencc_converter


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert course translations and explanations to zh-Hans-CN.")
    parser.add_argument("--manifest", required=True, help="Source manifest JSON.")
    parser.add_argument("--out", required=True, help="Normalized manifest JSON.")
    parser.add_argument("--strict-quality", action="store_true", help="Fail if automated checks return warnings.")
    parser.add_argument("--force", action="store_true", help="Overwrite the output file.")
    args = parser.parse_args()

    source_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.out).expanduser().resolve()
    if output_path.exists() and not args.force:
        raise SystemExit(f"Output already exists: {output_path}. Use --force to overwrite.")

    try:
        converter = load_opencc_converter()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    converted, changed_fields = convert_manifest(load_json(source_path), converter)
    report = audit_manifest(converted, require_enrichment=True)
    try:
        enforce_quality_gate(report, strict=args.strict_quality)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    converted["quality"] = {"status": report["status"], **report["summary"]}
    write_json(output_path, converted)
    write_json(output_path.with_suffix(".quality-report.json"), report)

    print(f"Normalized manifest: {output_path}")
    print(f"Locale: {TARGET_LOCALE} (OpenCC {OPENCC_CONFIG})")
    print(f"Changed fields: {changed_fields}")
    print(f"Content revision: {converted['contentRevision']}")
    print(
        f"Quality: {report['status']} "
        f"(errors={report['summary']['errors']}, warnings={report['summary']['warnings']})"
    )


if __name__ == "__main__":
    main()
