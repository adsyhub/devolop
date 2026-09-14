"""Source-bound, per-sentence human listening review workflow."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_deepseek_offline_bundle import load_json, write_json


REVIEW_SCHEMA_VERSION = 1
CHECK_FIELDS = (
    "transcriptMatchesAudio",
    "timingAligned",
    "translationAccurate",
    "explanationAccurate",
)
ITEM_STATUSES = frozenset({"pending", "approved", "changes_required"})


def create_review(manifest: dict[str, Any], *, reviewer: str, organization: str = "") -> dict[str, Any]:
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("Reviewer name is required.")
    course_id, revision, audio_hash, sentences = manifest_binding(manifest)
    now = utc_now()
    return {
        "schemaVersion": REVIEW_SCHEMA_VERSION,
        "type": "human-listening-review",
        "status": "in_progress",
        "courseId": course_id,
        "contentRevision": revision,
        "sourceAudioSha256": audio_hash,
        "reviewer": {"name": reviewer, "organization": organization.strip()},
        "createdAt": now,
        "completedAt": None,
        "attestation": {
            "independentHumanReview": False,
            "commercialReleaseRecommendation": False,
        },
        "items": [
            {
                "sentenceId": sentence["id"],
                "status": "pending",
                "checks": {field: False for field in CHECK_FIELDS},
                "notes": "",
                "reviewedAt": None,
            }
            for sentence in sentences
        ],
    }


def audit_human_review(manifest: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    course_id, revision, audio_hash, sentences = manifest_binding(manifest)
    expected_ids = [str(sentence["id"]) for sentence in sentences]

    if review.get("schemaVersion") != REVIEW_SCHEMA_VERSION or review.get("type") != "human-listening-review":
        add_issue(issues, "review.schema_invalid", "Unsupported human review schema or type.")
    for field, expected in (
        ("courseId", course_id),
        ("contentRevision", revision),
        ("sourceAudioSha256", audio_hash),
    ):
        if review.get(field) != expected:
            add_issue(issues, f"review.{field}_mismatch", f"{field} is not bound to this manifest.")

    reviewer = review.get("reviewer")
    if not isinstance(reviewer, dict) or not str(reviewer.get("name") or "").strip():
        add_issue(issues, "review.reviewer_missing", "A named reviewer is required.")

    items = review.get("items")
    if not isinstance(items, list):
        add_issue(issues, "review.items_missing", "Review items must be an array.")
        items = []
    seen: Counter[str] = Counter()
    pending = 0
    approved = 0
    changes_required = 0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            add_issue(issues, "review.item_invalid", "Review item must be an object.", index)
            continue
        sentence_id = str(item.get("sentenceId") or "")
        seen[sentence_id] += 1
        status = item.get("status")
        if status not in ITEM_STATUSES:
            add_issue(issues, "review.item_status_invalid", "Review status is unsupported.", index)
            continue
        if status == "approved":
            approved += 1
            checks = item.get("checks")
            if not isinstance(checks, dict) or any(checks.get(field) is not True for field in CHECK_FIELDS):
                add_issue(issues, "review.approval_checks_missing", "Approved item lacks all four explicit checks.", index)
            if not valid_iso_datetime(item.get("reviewedAt")):
                add_issue(issues, "review.reviewed_at_missing", "Approved item needs a valid reviewedAt timestamp.", index)
        elif status == "changes_required":
            changes_required += 1
            if not str(item.get("notes") or "").strip():
                add_issue(issues, "review.change_notes_missing", "Changes-required item needs reviewer notes.", index)
        else:
            pending += 1

    duplicate_ids = sorted(sentence_id for sentence_id, count in seen.items() if sentence_id and count > 1)
    missing_ids = sorted(set(expected_ids) - set(seen))
    unexpected_ids = sorted(set(seen) - set(expected_ids))
    if duplicate_ids:
        add_issue(issues, "review.sentence_duplicate", f"Duplicate sentence IDs: {duplicate_ids[:5]}")
    if missing_ids:
        add_issue(issues, "review.sentence_missing", f"Missing {len(missing_ids)} sentence reviews.")
    if unexpected_ids:
        add_issue(issues, "review.sentence_unexpected", f"Unexpected sentence IDs: {unexpected_ids[:5]}")

    attestation = review.get("attestation")
    if not isinstance(attestation, dict) or attestation.get("independentHumanReview") is not True:
        add_issue(issues, "review.independent_attestation_missing", "Independent human review attestation is required.")
    if not isinstance(attestation, dict) or attestation.get("commercialReleaseRecommendation") is not True:
        add_issue(issues, "review.release_attestation_missing", "Commercial release recommendation is required.")
    if review.get("status") != "approved":
        add_issue(issues, "review.not_finalized", "Review status must be approved after finalization.")
    if not valid_iso_datetime(review.get("completedAt")):
        add_issue(issues, "review.completed_at_missing", "A valid completedAt timestamp is required.")
    if pending:
        add_issue(issues, "review.items_pending", f"{pending} sentence reviews are still pending.")
    if changes_required:
        add_issue(issues, "review.changes_required", f"{changes_required} sentences still require changes.")

    return {
        "schemaVersion": 1,
        "status": "approved" if not issues and approved == len(expected_ids) else "incomplete",
        "summary": {
            "sentences": len(expected_ids),
            "approved": approved,
            "pending": pending,
            "changesRequired": changes_required,
            "issues": len(issues),
        },
        "issues": issues,
    }


def record_item(
    manifest: dict[str, Any],
    review: dict[str, Any],
    *,
    sentence_id: str,
    status: str,
    all_checks: bool,
    notes: str | None,
    checks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    course_id, revision, audio_hash, _ = manifest_binding(manifest)
    if any(review.get(field) != expected for field, expected in (
        ("courseId", course_id), ("contentRevision", revision), ("sourceAudioSha256", audio_hash)
    )):
        raise ValueError("Review file is not bound to this manifest.")
    if status not in ITEM_STATUSES:
        raise ValueError(f"Unsupported status: {status}")
    items = review.get("items")
    if not isinstance(items, list):
        raise ValueError("Review items are missing.")
    matches = [item for item in items if isinstance(item, dict) and item.get("sentenceId") == sentence_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one review item for sentence ID: {sentence_id}")
    item = matches[0]
    item["status"] = status
    if checks is not None:
        if set(checks) != set(CHECK_FIELDS) or any(not isinstance(value, bool) for value in checks.values()):
            raise ValueError("checks must contain exactly four boolean review fields.")
        item["checks"] = {field: checks[field] for field in CHECK_FIELDS}
    if all_checks:
        item["checks"] = {field: True for field in CHECK_FIELDS}
    if status == "approved" and any(item.get("checks", {}).get(field) is not True for field in CHECK_FIELDS):
        raise ValueError("Cannot approve a sentence until all four checks are true; pass --all-checks.")
    if notes is not None:
        item["notes"] = notes.strip()
    if status == "changes_required" and not str(item.get("notes") or "").strip():
        raise ValueError("Changes-required status needs notes.")
    item["reviewedAt"] = utc_now() if status != "pending" else None
    review["status"] = "in_progress"
    review["completedAt"] = None
    review["attestation"] = {
        "independentHumanReview": False,
        "commercialReleaseRecommendation": False,
    }
    return review


def finalize_review(manifest: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    review["status"] = "approved"
    review["completedAt"] = utc_now()
    review["attestation"] = {
        "independentHumanReview": True,
        "commercialReleaseRecommendation": True,
    }
    report = audit_human_review(manifest, review)
    if report["status"] != "approved":
        review["status"] = "in_progress"
        review["completedAt"] = None
        review["attestation"] = {
            "independentHumanReview": False,
            "commercialReleaseRecommendation": False,
        }
        raise ValueError(format_review_blockers(report))
    return review


def manifest_binding(manifest: dict[str, Any]) -> tuple[str, str, str, list[dict[str, Any]]]:
    course_id = str(manifest.get("courseId") or "")
    revision = str(manifest.get("contentRevision") or "")
    audio_hash = str(manifest.get("buildMetadata", {}).get("sourceAudioSha256") or "")
    sentences = manifest.get("sentences")
    if not course_id or not revision or not audio_hash or not isinstance(sentences, list) or not sentences:
        raise ValueError("Manifest needs courseId, contentRevision, source audio hash, and sentences.")
    if any(not isinstance(sentence, dict) or not str(sentence.get("id") or "") for sentence in sentences):
        raise ValueError("Every sentence needs a stable ID.")
    return course_id, revision, audio_hash, sentences


def add_issue(issues: list[dict[str, Any]], code: str, message: str, index: int | None = None) -> None:
    issue: dict[str, Any] = {"code": code, "message": message}
    if index is not None:
        issue["itemIndex"] = index
    issues.append(issue)


def valid_iso_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_review_blockers(report: dict[str, Any]) -> str:
    summary = report["summary"]
    return (
        "Human review is incomplete: "
        f"approved={summary['approved']}, pending={summary['pending']}, "
        f"changes_required={summary['changesRequired']}, issues={summary['issues']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage source-bound human listening reviews.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--manifest", required=True)
    init_parser.add_argument("--out", required=True)
    init_parser.add_argument("--reviewer", required=True)
    init_parser.add_argument("--organization", default="")

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--manifest", required=True)
    record_parser.add_argument("--review", required=True)
    record_parser.add_argument("--sentence-id", required=True)
    record_parser.add_argument("--status", choices=sorted(ITEM_STATUSES), required=True)
    record_parser.add_argument("--all-checks", action="store_true")
    record_parser.add_argument("--notes")

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--manifest", required=True)
    audit_parser.add_argument("--review", required=True)

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--manifest", required=True)
    finalize_parser.add_argument("--review", required=True)
    finalize_parser.add_argument("--attest-independent", action="store_true", required=True)
    finalize_parser.add_argument("--attest-release", action="store_true", required=True)

    args = parser.parse_args()
    manifest = load_json(Path(args.manifest).expanduser().resolve())
    if args.command == "init":
        output = Path(args.out).expanduser().resolve()
        if output.exists():
            raise SystemExit(f"Review file already exists: {output}")
        review = create_review(manifest, reviewer=args.reviewer, organization=args.organization)
        write_json(output, review)
        print(f"Human review initialized: {output} ({len(review['items'])} sentences)")
        return

    review_path = Path(args.review).expanduser().resolve()
    review = load_json(review_path)
    if args.command == "record":
        try:
            record_item(
                manifest,
                review,
                sentence_id=args.sentence_id,
                status=args.status,
                all_checks=args.all_checks,
                notes=args.notes,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        write_json(review_path, review)
        print(f"Recorded {args.sentence_id}: {args.status}")
    elif args.command == "finalize":
        try:
            finalize_review(manifest, review)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        write_json(review_path, review)
        print(f"Human review approved: {review_path}")
    else:
        report = audit_human_review(manifest, review)
        print(format_review_blockers(report) if report["status"] != "approved" else "Human review: approved")
        if report["status"] != "approved":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
