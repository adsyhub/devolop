"""Audit an existing dictation manifest before it is published."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bundle_quality import audit_manifest, enforce_quality_gate


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a dictation manifest and optionally enforce a strict gate.")
    parser.add_argument("manifest", help="Path to manifest.json.")
    parser.add_argument("--output", help="Quality report path. Default: <manifest>.quality-report.json")
    parser.add_argument("--no-enrichment", action="store_true", help="Do not require translations and explanations.")
    parser.add_argument("--strict", action="store_true", help="Return a failure exit code for warnings as well as errors.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else manifest_path.with_name(f"{manifest_path.stem}.quality-report.json")
    )
    manifest = load_json(manifest_path)
    report = audit_manifest(manifest, require_enrichment=not args.no_enrichment)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = report["summary"]
    print(
        f"Quality: {report['status']} | sentences={summary['sentences']} "
        f"errors={summary['errors']} warnings={summary['warnings']}"
    )
    print(f"Report: {output_path}")
    try:
        enforce_quality_gate(report, strict=args.strict)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected a JSON object: {path}")
    return data


if __name__ == "__main__":
    main()
