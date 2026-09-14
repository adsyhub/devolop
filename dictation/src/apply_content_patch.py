"""Apply a source-bound content patch and regenerate its quality report."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_deepseek_offline_bundle import load_json, write_json
from bundle_quality import audit_manifest
from content_patch import apply_content_patch


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply an auditable correction patch to a course manifest.")
    parser.add_argument("manifest", help="Source manifest JSON.")
    parser.add_argument("patch", help="Content patch JSON.")
    parser.add_argument("--out", required=True, help="Patched manifest path.")
    parser.add_argument("--force", action="store_true", help="Overwrite output files.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    patch_path = Path(args.patch).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    report_path = out_path.with_name(f"{out_path.stem}.quality-report.json")
    for path in (out_path, report_path):
        if path.exists() and not args.force:
            raise SystemExit(f"Output already exists: {path}. Use --force to overwrite.")

    manifest = load_json(manifest_path)
    patch = load_json(patch_path)
    try:
        result = apply_content_patch(manifest, patch, patch_name=patch_path.name)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    report = audit_manifest(result, require_enrichment=True)
    result["quality"] = {"status": report["status"], **report["summary"]}
    write_json(out_path, result)
    write_json(report_path, report)
    print(f"Patched manifest: {out_path}")
    print(f"Sentences: {len(result['sentences'])}")
    print(
        f"Quality: {report['status']} "
        f"(errors={report['summary']['errors']}, warnings={report['summary']['warnings']})"
    )


if __name__ == "__main__":
    main()
