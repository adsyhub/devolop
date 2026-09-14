"""Produce an evidence-backed release readiness report without granting approvals."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from build_deepseek_offline_bundle import load_json, sha256_file, verify_zip, write_json
from bundle_quality import audit_manifest
from course_schema import is_remote_media_manifest
from content_license import audit_license_ledger
from distribution_policy import audit_release_artifact
from human_review import audit_human_review
from release_evidence import REQUIRED_WEB_ASSETS, web_assets_sha256


SECRET_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
TEXT_SUFFIXES = {".py", ".js", ".html", ".css", ".md", ".json", ".txt", ".example"}
REQUIRED_MANUAL_BROWSER_TARGETS = {
    "iphone-safari",
    "android-chrome",
    "desktop-safari",
    "desktop-chrome",
    "desktop-edge",
}


def build_report(
    manifest: dict[str, Any],
    *,
    manifest_path: Path,
    audio_path: Path,
    web_dir: Path,
    project_dir: Path,
    approvals: dict[str, Any] | None,
    artifact_path: Path | None,
    browser_evidence: list[dict[str, Any]] | None = None,
    human_review_evidence: dict[str, Any] | None = None,
    license_ledger: dict[str, Any] | None = None,
    license_ledger_path: Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    # An online-video course is not releasable and never will be: we hold no rights
    # to the media, which lives on someone else's server, and the transcript derives
    # from that site's captions. This is a blocking check rather than a crash on the
    # missing audio file, so the report says *why* instead of failing obscurely.
    if is_remote_media_manifest(manifest):
        add_check(
            checks,
            "redistributable_media",
            False,
            "在线视频课程不可再分发：媒体不属于我们，逐句文本源自站点字幕。"
            " / An online-video course is never redistributable: the media is not ours.",
            blocking=True,
        )
        return {
            "schemaVersion": 1,
            "scope": "online-video-course",
            "status": "blocked",
            "automatedTechnicalStatus": "blocked",
            "summary": {"checks": 1, "passed": 0, "blockers": 1, "externalBlockers": 0},
            "manifest": {
                "path": str(manifest_path),
                "courseId": manifest.get("courseId"),
                "contentRevision": manifest.get("contentRevision"),
                "sentences": len(manifest.get("sentences", [])),
                "practiceSentences": manifest.get("practiceSentenceCount"),
            },
            "checks": checks,
        }

    quality = audit_manifest(manifest, require_enrichment=True)
    quality_summary = quality["summary"]
    add_check(
        checks,
        "automated_quality",
        quality["status"] == "passed",
        f"errors={quality_summary['errors']}, warnings={quality_summary['warnings']}",
        blocking=True,
    )

    audio_exists = audio_path.is_file() and audio_path.stat().st_size > 0
    add_check(checks, "audio_present", audio_exists, str(audio_path), blocking=True)
    audio_hash = sha256_file(audio_path) if audio_exists else None
    expected_hash = str(manifest.get("buildMetadata", {}).get("sourceAudioSha256") or "")
    add_check(
        checks,
        "audio_source_bound",
        bool(audio_hash and expected_hash and audio_hash == expected_hash),
        f"sha256={audio_hash or 'unavailable'}",
        blocking=True,
    )

    available_assets = {path.name for path in web_dir.iterdir() if path.is_file()} if web_dir.is_dir() else set()
    missing_assets = sorted(REQUIRED_WEB_ASSETS - available_assets)
    current_web_hash = web_assets_sha256(web_dir) if web_dir.is_dir() and available_assets else None
    add_check(
        checks,
        "web_assets",
        not missing_assets,
        "complete" if not missing_assets else f"missing={', '.join(missing_assets)}",
        blocking=True,
    )
    add_check(
        checks,
        "simplified_chinese_locale",
        manifest.get("locales", {}).get("translation") == "zh-Hans-CN",
        str(manifest.get("locales", {}).get("translation") or "missing"),
        blocking=True,
    )

    # LEXICON.md §8.3: textbook-derived packs must never reach a release artifact. The
    # check is on the *artifact*, not on the working tree — a developer's machine is
    # expected to hold packs built from books they own; what must never happen is one of
    # them being copied into something that gets published. No artifact yet means nothing
    # has been packaged, which is neither a pass nor a failure to report here.
    if artifact_path is not None and artifact_path.is_file():
        with zipfile.ZipFile(artifact_path) as archive:
            verdict = audit_release_artifact(archive.namelist())
        add_check(checks, "no_textbook_lexicon_content", verdict["passed"], verdict["detail"], blocking=True)

    leaked_files = scan_for_secrets(project_dir)
    add_check(
        checks,
        "embedded_secret_scan",
        not leaked_files,
        "no key-shaped values found" if not leaked_files else f"matches={', '.join(leaked_files)}",
        blocking=True,
    )

    if browser_evidence:
        expected_course_id = manifest.get("courseId")
        expected_revision = manifest.get("contentRevision")
        evidence_valid = all(
            item.get("status") == "passed"
            and item.get("courseId") == expected_course_id
            and item.get("contentRevision") == expected_revision
            and item.get("webAssetsSha256") == current_web_hash
            for item in browser_evidence
        )
        channels = sorted({str(item.get("browserChannel") or "unknown") for item in browser_evidence})
        profiles = sorted({str(item.get("profile") or "desktop") for item in browser_evidence})
        add_check(
            checks,
            "headless_browser_e2e",
            evidence_valid,
            (
                f"channels={', '.join(channels)}; profiles={', '.join(profiles)}; "
                f"course/revision/web-assets bound={evidence_valid}; webAssetsSha256={current_web_hash or 'unavailable'}"
            ),
            blocking=True,
        )

    if human_review_evidence is None:
        human_passed = False
        human_detail = "source-bound per-sentence evidence is missing"
    else:
        try:
            human_report = audit_human_review(manifest, human_review_evidence)
            human_passed = human_report["status"] == "approved"
            human_summary = human_report["summary"]
            human_detail = (
                f"approved={human_summary['approved']}/{human_summary['sentences']}; "
                f"pending={human_summary['pending']}; issues={human_summary['issues']}"
            )
        except ValueError as exc:
            human_passed = False
            human_detail = str(exc)
    add_check(
        checks,
        "humanListening",
        human_passed,
        human_detail,
        blocking=True,
        externally_verified=True,
    )

    if license_ledger is None or license_ledger_path is None:
        rights_passed = False
        rights_detail = "source-bound rights ledger is missing"
    else:
        try:
            rights_report = audit_license_ledger(manifest, license_ledger, ledger_path=license_ledger_path)
            rights_passed = rights_report["status"] == "verified"
            rights_summary = rights_report["summary"]
            rights_detail = (
                f"covered={','.join(rights_summary['coveredTypes']) or 'none'}; "
                f"missing={','.join(rights_summary['missingTypes']) or 'none'}; "
                f"issues={rights_summary['issues']}"
            )
        except ValueError as exc:
            rights_passed = False
            rights_detail = str(exc)
    add_check(
        checks,
        "commercialRights",
        rights_passed,
        rights_detail,
        blocking=True,
        externally_verified=True,
    )

    approval_source = approvals or manifest.get("review") or {}
    approval_requirements = {
        "browserAcceptance": "approved",
        "credentialRotation": "verified",
    }
    for name, required_status in approval_requirements.items():
        value = approval_source.get(name)
        passed, detail = audit_external_approval(name, value, required_status)
        add_check(checks, name, passed, detail, blocking=True, externally_verified=True)

    artifact: dict[str, Any] | None = None
    if artifact_path is not None:
        artifact_ok = False
        detail = str(artifact_path)
        try:
            verify_zip(artifact_path)
            artifact_ok, binding_detail = artifact_matches_sources(
                artifact_path,
                manifest=manifest,
                audio_path=audio_path,
                web_dir=web_dir,
            )
            detail = binding_detail
            artifact = {
                "path": str(artifact_path),
                "bytes": artifact_path.stat().st_size,
                "sha256": sha256_file(artifact_path),
            }
        except (OSError, SystemExit, ValueError, json.JSONDecodeError) as exc:
            detail = f"{artifact_path}: {exc}"
        add_check(checks, "release_artifact_integrity", artifact_ok, detail, blocking=True)

    blockers = [check for check in checks if check["blocking"] and check["status"] != "passed"]
    automated_blockers = [check for check in blockers if not check.get("externallyVerified")]
    external_blockers = [check for check in blockers if check.get("externallyVerified")]
    report: dict[str, Any] = {
        "schemaVersion": 1,
        "scope": "self-hosted-offline-course",
        "status": "ready" if not blockers else "blocked",
        "automatedTechnicalStatus": "passed" if not automated_blockers else "blocked",
        "summary": {
            "checks": len(checks),
            "passed": sum(check["status"] == "passed" for check in checks),
            "blockers": len(blockers),
            "externalBlockers": len(external_blockers),
        },
        "manifest": {
            "path": str(manifest_path),
            "courseId": manifest.get("courseId"),
            "contentRevision": manifest.get("contentRevision"),
            "sentences": len(manifest.get("sentences", [])),
            "practiceSentences": manifest.get("practiceSentenceCount"),
        },
        "checks": checks,
    }
    if artifact is not None:
        report["artifact"] = artifact
    return report


def artifact_matches_sources(
    artifact_path: Path,
    *,
    manifest: dict[str, Any],
    audio_path: Path,
    web_dir: Path,
) -> tuple[bool, str]:
    """Verify that a valid ZIP was built from the current release inputs."""
    expected_audio_name = str(manifest.get("audio") or "")
    web_files = sorted(
        (path for path in web_dir.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(web_dir).as_posix(),
    )
    expected_names = {"manifest.json", "quality-report.json", expected_audio_name}
    expected_names.update(path.relative_to(web_dir).as_posix() for path in web_files)
    mismatches: list[str] = []
    with zipfile.ZipFile(artifact_path) as archive:
        actual_names = set(archive.namelist())
        if actual_names != expected_names:
            missing = sorted(expected_names - actual_names)
            unexpected = sorted(actual_names - expected_names)
            if missing:
                mismatches.append(f"missing={','.join(missing)}")
            if unexpected:
                mismatches.append(f"unexpected={','.join(unexpected)}")

        packaged_manifest = json.loads(archive.read("manifest.json").decode("utf-8-sig"))
        current_comparable = dict(manifest)
        packaged_comparable = dict(packaged_manifest)
        current_comparable.pop("quality", None)
        packaged_comparable.pop("quality", None)
        if packaged_comparable != current_comparable:
            mismatches.append("manifest content differs from current source")

        if expected_audio_name in actual_names:
            with archive.open(expected_audio_name) as source:
                packaged_audio_hash = sha256_stream(source)
            if packaged_audio_hash != sha256_file(audio_path):
                mismatches.append("audio differs from current source")

        for path in web_files:
            name = path.relative_to(web_dir).as_posix()
            if name in actual_names and hashlib.sha256(archive.read(name)).hexdigest() != sha256_file(path):
                mismatches.append(f"web asset differs: {name}")

    if mismatches:
        return False, "; ".join(mismatches[:8])
    return True, "ZIP contents match current manifest, audio, quality report, and web assets"


def sha256_stream(source: Any) -> str:
    digest = hashlib.sha256()
    while block := source.read(1024 * 1024):
        digest.update(block)
    return digest.hexdigest()


def audit_external_approval(name: str, value: Any, required_status: str) -> tuple[bool, str]:
    if not isinstance(value, dict):
        return False, "structured, evidence-backed approval is missing"
    status = str(value.get("status") or "")
    evidence = str(value.get("evidence") or "").strip()
    completed = valid_iso_datetime(value.get("completedAt"))
    if name == "browserAcceptance":
        approver = str(value.get("approvedBy") or "").strip()
        matrix = value.get("matrix")
        passed_targets: set[str] = set()
        if isinstance(matrix, list):
            for item in matrix:
                if not isinstance(item, dict):
                    continue
                target = str(item.get("target") or "")
                if (
                    target in REQUIRED_MANUAL_BROWSER_TARGETS
                    and item.get("status") == "passed"
                    and valid_iso_datetime(item.get("testedAt"))
                    and str(item.get("evidence") or "").strip()
                ):
                    passed_targets.add(target)
        missing = sorted(REQUIRED_MANUAL_BROWSER_TARGETS - passed_targets)
        passed = (
            status == required_status
            and bool(approver)
            and completed
            and bool(evidence)
            and not missing
        )
        return passed, (
            f"status={status or 'missing'}, approvedBy={'present' if approver else 'missing'}, "
            f"completedAt={'valid' if completed else 'missing/invalid'}, "
            f"evidence={'present' if evidence else 'missing'}, "
            f"targets={len(passed_targets)}/{len(REQUIRED_MANUAL_BROWSER_TARGETS)}"
            + (f", missing={','.join(missing)}" if missing else "")
        )

    verifier = str(value.get("verifiedBy") or "").strip()
    passed = status == required_status and bool(verifier) and completed and bool(evidence)
    return passed, (
        f"status={status or 'missing'}, verifiedBy={'present' if verifier else 'missing'}, "
        f"completedAt={'valid' if completed else 'missing/invalid'}, "
        f"evidence={'present' if evidence else 'missing'}"
    )


def valid_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def add_check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    detail: str,
    *,
    blocking: bool,
    externally_verified: bool = False,
) -> None:
    check: dict[str, Any] = {
        "name": name,
        "status": "passed" if passed else "blocked",
        "blocking": blocking,
        "detail": detail,
    }
    if externally_verified:
        check["externallyVerified"] = True
    checks.append(check)


def scan_for_secrets(project_dir: Path) -> list[str]:
    matches: list[str] = []
    excluded_dirs = {".venv", "data", "data-work", "release", "__pycache__", ".git"}
    for path in project_dir.rglob("*"):
        if not path.is_file() or any(part in excluded_dirs for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"run", ".env.example"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if SECRET_PATTERN.search(text):
            matches.append(str(path.relative_to(project_dir)))
    return sorted(matches)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a commercial release readiness report.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--approvals", help="Completed approval evidence JSON.")
    parser.add_argument("--human-review-evidence", help="Finalized per-sentence human review JSON.")
    parser.add_argument("--license-ledger", help="Finalized commercial content-rights ledger JSON.")
    parser.add_argument("--artifact", help="Candidate ZIP to integrity-check and hash.")
    parser.add_argument(
        "--browser-evidence",
        action="append",
        default=[],
        help="Headless E2E evidence JSON; repeat for multiple browsers.",
    )
    parser.add_argument("--web-dir", default=str(Path(__file__).resolve().parent / "web"))
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    audio_path = Path(args.audio).expanduser().resolve()
    output_path = Path(args.out).expanduser().resolve()
    web_dir = Path(args.web_dir).expanduser().resolve()
    approvals = load_json(Path(args.approvals).expanduser().resolve()) if args.approvals else None
    human_review_evidence = (
        load_json(Path(args.human_review_evidence).expanduser().resolve())
        if args.human_review_evidence else None
    )
    license_ledger_path = Path(args.license_ledger).expanduser().resolve() if args.license_ledger else None
    license_ledger = load_json(license_ledger_path) if license_ledger_path else None
    browser_evidence = [load_json(Path(path).expanduser().resolve()) for path in args.browser_evidence]
    artifact_path = Path(args.artifact).expanduser().resolve() if args.artifact else None
    report = build_report(
        load_json(manifest_path),
        manifest_path=manifest_path,
        audio_path=audio_path,
        web_dir=web_dir,
        project_dir=Path(__file__).resolve().parent,
        approvals=approvals,
        artifact_path=artifact_path,
        browser_evidence=browser_evidence,
        human_review_evidence=human_review_evidence,
        license_ledger=license_ledger,
        license_ledger_path=license_ledger_path,
    )
    write_json(output_path, report)
    print(f"Readiness report: {output_path}")
    print(
        f"Status: {report['status']} "
        f"(technical={report['automatedTechnicalStatus']}, blockers={report['summary']['blockers']}, "
        f"external={report['summary']['externalBlockers']})"
    )
    for check in report["checks"]:
        if check["status"] != "passed":
            print(f"BLOCKED {check['name']}: {check['detail']}")


if __name__ == "__main__":
    main()
