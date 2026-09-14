"""Commercial content-rights ledger bound to a course release."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from course_schema import is_remote_media_manifest

from build_deepseek_offline_bundle import load_json, sha256_file, write_json


LICENSE_SCHEMA_VERSION = 1
REQUIRED_ASSET_TYPES = frozenset({"audio", "questions", "transcript", "translation", "explanation"})
LICENSE_BASES = frozenset({"owned", "licensed", "written_permission", "public_domain"})


class RemoteMediaNotLicensable(ValueError):
    """An online-video course has no rights to record, because we hold none."""


def create_license_ledger(manifest: dict[str, Any]) -> dict[str, Any]:
    # A ledger asserts what we are permitted to redistribute. For an online-video
    # course the honest answer is "nothing", and writing a ledger anyway would create
    # a document that looks like a rights claim over someone else's video.
    if is_remote_media_manifest(manifest):
        raise RemoteMediaNotLicensable(
            "在线视频课程不能建立版权台账：媒体不属于我们，不可再分发。"
            " / Cannot create a rights ledger for an online-video course: the media is not ours."
        )
    course_id, revision, audio_hash = manifest_binding(manifest)
    return {
        "schemaVersion": LICENSE_SCHEMA_VERSION,
        "type": "commercial-content-rights-ledger",
        "status": "in_progress",
        "courseId": course_id,
        "contentRevision": revision,
        "sourceAudioSha256": audio_hash,
        "approvedBy": "",
        "approvedAt": None,
        "legalAttestation": False,
        "assets": [
            {
                "assetId": f"course-{asset_type}",
                "assetTypes": [asset_type],
                "source": "",
                "rightsHolder": "",
                "licenseBasis": "",
                "commercialUse": False,
                "derivativeWorks": False,
                "territories": [],
                "validFrom": "",
                "validUntil": None,
                "takedownContact": "",
                "status": "pending",
                "evidence": [],
            }
            for asset_type in sorted(REQUIRED_ASSET_TYPES)
        ],
    }


def audit_license_ledger(
    manifest: dict[str, Any],
    ledger: dict[str, Any],
    *,
    ledger_path: Path,
    today: date | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    course_id, revision, audio_hash = manifest_binding(manifest)
    today = today or date.today()

    if ledger.get("schemaVersion") != LICENSE_SCHEMA_VERSION or ledger.get("type") != "commercial-content-rights-ledger":
        add_issue(issues, "license.schema_invalid", "Unsupported license ledger schema or type.")
    for field, expected in (
        ("courseId", course_id),
        ("contentRevision", revision),
        ("sourceAudioSha256", audio_hash),
    ):
        if ledger.get(field) != expected:
            add_issue(issues, f"license.{field}_mismatch", f"{field} is not bound to this manifest.")

    covered: set[str] = set()
    assets = ledger.get("assets")
    if not isinstance(assets, list) or not assets:
        add_issue(issues, "license.assets_missing", "At least one rights entry is required.")
        assets = []
    seen_asset_ids: set[str] = set()
    for index, asset in enumerate(assets):
        start_issue_count = len(issues)
        if not isinstance(asset, dict):
            add_issue(issues, "license.asset_invalid", "Rights entry must be an object.", index)
            continue
        asset_id = str(asset.get("assetId") or "").strip()
        if not asset_id or asset_id in seen_asset_ids:
            add_issue(issues, "license.asset_id_invalid", "assetId is missing or duplicated.", index)
        seen_asset_ids.add(asset_id)
        raw_types = asset.get("assetTypes")
        asset_types = {str(item) for item in raw_types} if isinstance(raw_types, list) else set()
        if not asset_types or not asset_types <= REQUIRED_ASSET_TYPES:
            add_issue(issues, "license.asset_types_invalid", "assetTypes are missing or unsupported.", index)
        if asset.get("status") != "verified":
            add_issue(issues, "license.asset_unverified", "Rights entry status must be verified.", index)
        if not str(asset.get("source") or "").strip():
            add_issue(issues, "license.source_missing", "Content source is required.", index)
        if not str(asset.get("rightsHolder") or "").strip():
            add_issue(issues, "license.rights_holder_missing", "Rights holder is required.", index)
        if asset.get("licenseBasis") not in LICENSE_BASES:
            add_issue(issues, "license.basis_invalid", "licenseBasis is missing or unsupported.", index)
        if asset.get("commercialUse") is not True:
            add_issue(issues, "license.commercial_use_missing", "Commercial-use rights must be explicit.", index)
        if asset.get("derivativeWorks") is not True:
            add_issue(issues, "license.derivatives_missing", "Derivative-work rights must be explicit.", index)
        territories = asset.get("territories")
        if not isinstance(territories, list) or not territories or any(not str(item).strip() for item in territories):
            add_issue(issues, "license.territories_missing", "At least one sales territory is required.", index)
        if not str(asset.get("takedownContact") or "").strip():
            add_issue(issues, "license.takedown_contact_missing", "A takedown contact is required.", index)

        valid_from = parse_date(asset.get("validFrom"))
        if valid_from is None or valid_from > today:
            add_issue(issues, "license.valid_from_invalid", "validFrom must be a date not later than today.", index)
        valid_until_raw = asset.get("validUntil")
        if valid_until_raw not in (None, ""):
            valid_until = parse_date(valid_until_raw)
            if valid_until is None or valid_until < today:
                add_issue(issues, "license.expired", "The commercial-use right is expired or invalid.", index)

        evidence = asset.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            add_issue(issues, "license.evidence_missing", "At least one local evidence file is required.", index)
        else:
            for evidence_index, item in enumerate(evidence):
                validate_evidence(item, ledger_path, issues, index, evidence_index)

        if len(issues) == start_issue_count:
            covered.update(asset_types)

    missing_types = sorted(REQUIRED_ASSET_TYPES - covered)
    if missing_types:
        add_issue(issues, "license.coverage_missing", f"No verified rights entry covers: {', '.join(missing_types)}")
    if ledger.get("status") != "verified":
        add_issue(issues, "license.not_finalized", "Ledger status must be verified after finalization.")
    if not str(ledger.get("approvedBy") or "").strip():
        add_issue(issues, "license.approver_missing", "A named rights approver is required.")
    if not valid_iso_datetime(ledger.get("approvedAt")):
        add_issue(issues, "license.approved_at_missing", "A valid approvedAt timestamp is required.")
    if ledger.get("legalAttestation") is not True:
        add_issue(issues, "license.attestation_missing", "Explicit commercial-rights attestation is required.")

    return {
        "schemaVersion": 1,
        "status": "verified" if not issues else "incomplete",
        "summary": {
            "assets": len(assets),
            "coveredTypes": sorted(covered),
            "missingTypes": missing_types,
            "issues": len(issues),
        },
        "issues": issues,
    }


def finalize_license_ledger(
    manifest: dict[str, Any],
    ledger: dict[str, Any],
    *,
    ledger_path: Path,
    approved_by: str,
) -> dict[str, Any]:
    approved_by = approved_by.strip()
    if not approved_by:
        raise ValueError("Rights approver name is required.")
    ledger["status"] = "verified"
    ledger["approvedBy"] = approved_by
    ledger["approvedAt"] = datetime.now(timezone.utc).isoformat()
    ledger["legalAttestation"] = True
    report = audit_license_ledger(manifest, ledger, ledger_path=ledger_path)
    if report["status"] != "verified":
        ledger["status"] = "in_progress"
        ledger["approvedBy"] = ""
        ledger["approvedAt"] = None
        ledger["legalAttestation"] = False
        raise ValueError(format_license_blockers(report))
    return ledger


def validate_evidence(
    item: Any,
    ledger_path: Path,
    issues: list[dict[str, Any]],
    asset_index: int,
    evidence_index: int,
) -> None:
    if not isinstance(item, dict):
        add_issue(issues, "license.evidence_invalid", f"Evidence {evidence_index} must be an object.", asset_index)
        return
    raw_path = str(item.get("path") or "").strip().replace("\\", "/")
    posix = PurePosixPath(raw_path)
    if not raw_path or posix.is_absolute() or ".." in posix.parts or any(":" in part for part in posix.parts):
        add_issue(issues, "license.evidence_path_unsafe", f"Evidence {evidence_index} path is unsafe.", asset_index)
        return
    evidence_path = ledger_path.parent.joinpath(*posix.parts).resolve()
    ledger_root = ledger_path.parent.resolve()
    if ledger_root not in evidence_path.parents or not evidence_path.is_file():
        add_issue(issues, "license.evidence_file_missing", f"Evidence {evidence_index} file is missing.", asset_index)
        return
    expected_digest = str(item.get("sha256") or "").lower()
    if len(expected_digest) != 64 or any(character not in "0123456789abcdef" for character in expected_digest):
        add_issue(issues, "license.evidence_digest_invalid", f"Evidence {evidence_index} SHA-256 is invalid.", asset_index)
    elif sha256_file(evidence_path) != expected_digest:
        add_issue(issues, "license.evidence_digest_mismatch", f"Evidence {evidence_index} SHA-256 does not match.", asset_index)
    if not str(item.get("description") or "").strip():
        add_issue(issues, "license.evidence_description_missing", f"Evidence {evidence_index} needs a description.", asset_index)


def manifest_binding(manifest: dict[str, Any]) -> tuple[str, str, str]:
    course_id = str(manifest.get("courseId") or "")
    revision = str(manifest.get("contentRevision") or "")
    audio_hash = str(manifest.get("buildMetadata", {}).get("sourceAudioSha256") or "")
    if not course_id or not revision or not audio_hash:
        raise ValueError("Manifest needs courseId, contentRevision, and source audio hash.")
    return course_id, revision, audio_hash


def parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def valid_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def add_issue(
    issues: list[dict[str, Any]], code: str, message: str, asset_index: int | None = None
) -> None:
    issue: dict[str, Any] = {"code": code, "message": message}
    if asset_index is not None:
        issue["assetIndex"] = asset_index
    issues.append(issue)


def format_license_blockers(report: dict[str, Any]) -> str:
    summary = report["summary"]
    return (
        "Commercial rights are incomplete: "
        f"covered={','.join(summary['coveredTypes']) or 'none'}, "
        f"missing={','.join(summary['missingTypes']) or 'none'}, issues={summary['issues']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage commercial content-rights evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--manifest", required=True)
    init_parser.add_argument("--out", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--manifest", required=True)
    audit_parser.add_argument("--ledger", required=True)
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--manifest", required=True)
    finalize_parser.add_argument("--ledger", required=True)
    finalize_parser.add_argument("--approved-by", required=True)
    finalize_parser.add_argument("--attest-commercial-rights", action="store_true", required=True)
    args = parser.parse_args()

    manifest = load_json(Path(args.manifest).expanduser().resolve())
    if args.command == "init":
        output = Path(args.out).expanduser().resolve()
        if output.exists():
            raise SystemExit(f"License ledger already exists: {output}")
        write_json(output, create_license_ledger(manifest))
        print(f"License ledger initialized: {output}")
        return

    ledger_path = Path(args.ledger).expanduser().resolve()
    ledger = load_json(ledger_path)
    if args.command == "finalize":
        try:
            finalize_license_ledger(manifest, ledger, ledger_path=ledger_path, approved_by=args.approved_by)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        write_json(ledger_path, ledger)
        print(f"Commercial rights verified: {ledger_path}")
    else:
        report = audit_license_ledger(manifest, ledger, ledger_path=ledger_path)
        print(format_license_blockers(report) if report["status"] != "verified" else "Commercial rights: verified")
        if report["status"] != "verified":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
