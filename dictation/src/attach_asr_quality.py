"""CLI for attaching raw ASR diagnostics to an existing manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from asr_quality import attach_asr_quality
from build_deepseek_offline_bundle import load_json, write_json
from bundle_quality import audit_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach ASR confidence and diagnostics to a manifest.")
    parser.add_argument("manifest", help="Input manifest JSON.")
    parser.add_argument("raw_segments", help="segments.raw.json produced from the same transcription.")
    parser.add_argument("--out", help="Output manifest. Default: <manifest>.review.json")
    parser.add_argument("--force", action="store_true", help="Overwrite output files.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    raw_path = Path(args.raw_segments).expanduser().resolve()
    out_path = (
        Path(args.out).expanduser().resolve()
        if args.out
        else manifest_path.with_name(f"{manifest_path.stem}.review.json")
    )
    report_path = out_path.with_name(f"{out_path.stem}.quality-report.json")
    for path in (out_path, report_path):
        if path.exists() and not args.force:
            raise SystemExit(f"Output already exists: {path}. Use --force to overwrite.")

    manifest = load_json(manifest_path)
    raw_metadata = load_json(raw_path)
    attached = attach_asr_quality(manifest, raw_metadata)
    report = audit_manifest(manifest, require_enrichment=True)
    manifest["quality"] = {"status": report["status"], **report["summary"]}
    write_json(out_path, manifest)
    write_json(report_path, report)
    print(f"ASR diagnostics attached: {attached}")
    print(f"Manifest: {out_path}")
    print(f"Quality: {report['status']} (errors={report['summary']['errors']}, warnings={report['summary']['warnings']})")


if __name__ == "__main__":
    main()
