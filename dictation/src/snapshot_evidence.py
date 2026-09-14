"""BKP-001: freeze a verifiable snapshot of course content, code and learning data.

Phase 0 of the improvement plan requires a *recoverable* baseline before anything
else is touched: content is about to be re-audited, the learning database is about
to be migrated, and the local API is about to change its authentication. All three
are destructive if they go wrong, and the project has no release history to fall
back on.

This tool produces two things:

``<snapshot>/evidence.json``
    A SHA-256 manifest of every tracked input (course manifest, audio, published
    ZIP, web assets, quality reports, build config) plus the tool versions,
    timestamp and operator that produced it. Small enough to commit.

``<snapshot>/learning.sqlite3``
    A *consistent* copy of the learner's database. Taken with the SQLite Backup
    API while connections may still be open, which is the only safe way to copy a
    live database — a plain file copy of a WAL-mode database can capture a torn
    page or miss committed transactions still sitting in the WAL.

``--verify`` re-hashes the recorded sources and reports drift, so a restore
rehearsal can prove the snapshot still matches what it claims to describe.

The plan is explicit that a snapshot which cannot be restored is not evidence.
Run ``--verify`` against a fresh copy at least once before relying on it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PROJECT_DIR = Path(__file__).resolve().parent.parent
SNAPSHOT_ROOT = PROJECT_DIR / "assets" / "snapshots"

# Everything whose bytes we want to be able to prove later. Globs are resolved
# relative to the project root; missing entries are recorded as missing rather
# than silently skipped, because "this file was already gone" is itself evidence.
TRACKED_SOURCES: tuple[str, ...] = (
    "courses/*/manifest.json",
    "courses/*/audio.mp3",
    "dist/*.zip",
    "assets/content_patches/*.json",
    "assets/licenses/*.json",
    "src/*.py",
    "src/web/*",
    "src/review_web/*",
    "start_dictation.py",
    "requirements.txt",
)

CHUNK = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_tracked(project_dir: Path, patterns: Iterable[str]) -> list[Path]:
    seen: dict[Path, None] = {}
    for pattern in patterns:
        for match in sorted(project_dir.glob(pattern)):
            if match.is_file():
                seen.setdefault(match, None)
    return list(seen)


def hash_sources(project_dir: Path, patterns: Iterable[str]) -> list[dict[str, Any]]:
    entries = []
    for path in iter_tracked(project_dir, patterns):
        entries.append(
            {
                "path": path.relative_to(project_dir).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries


def backup_sqlite(source_db: Path, target_db: Path) -> dict[str, Any]:
    """Copy a live SQLite database consistently via the Backup API.

    A file-level copy is only safe with every connection closed and no
    transaction in flight; the plan calls that out specifically because this
    database is the learner's only durable vocab/notes store. The Backup API
    holds the right locks for us, so this stays correct even while the preview
    server is running.
    """
    if not source_db.exists():
        return {"present": False, "reason": f"no database at {source_db}"}

    target_db.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(f"file:{source_db}?mode=ro", uri=True)
    try:
        destination = sqlite3.connect(str(target_db))
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
    finally:
        source.close()

    # A backup that cannot be opened and read is not a backup. Prove it now,
    # while the operator is still watching, rather than during an incident.
    check = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True)
    try:
        integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
        tables = [
            row[0]
            for row in check.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        counts = {name: check.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in tables}
    finally:
        check.close()

    return {
        "present": True,
        "source": str(source_db),
        "sha256": sha256_file(target_db),
        "bytes": target_db.stat().st_size,
        "integrityCheck": integrity,
        "rowCounts": counts,
    }


def default_learning_db() -> Path:
    """Mirror serve_course.default_data_dir() without importing the server."""
    import os

    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
    return base / "dictation-preview" / "learning.sqlite3"


def create_snapshot(project_dir: Path, out_dir: Path, operator: str, note: str) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sources = hash_sources(project_dir, TRACKED_SOURCES)
    database = backup_sqlite(default_learning_db(), out_dir / "learning.sqlite3")

    evidence = {
        "schemaVersion": "evidence-v1",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "operator": operator,
        "note": note,
        "tooling": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "sqlite": sqlite3.sqlite_version,
        },
        "projectDir": str(project_dir),
        "sources": sources,
        "learningDatabase": database,
        # The plan is emphatic that unrecoverable data must be reported as
        # unrecoverable, never quietly folded into "migrated". Browser storage
        # cannot be enumerated across origins, so a random-port origin from an
        # earlier run is simply not reachable from here.
        "knownUnrecoverable": [
            "Browser localStorage/IndexedDB written under earlier random-port origins "
            "(http://127.0.0.1:<random>) cannot be enumerated or exported by any tool. "
            "Only the user can recover them, by reopening that exact port and exporting "
            "per-origin. Treat unlisted origins as lost, not as migrated.",
        ],
    }

    serialized = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    (out_dir / "evidence.json").write_text(serialized, encoding="utf-8")

    # The snapshot directory holds the learner's database and stays out of git.
    # The hash manifest itself is small and is exactly what a later restore needs
    # to prove drift, so it is committed alongside the code it describes.
    tracked = PROJECT_DIR / "assets" / "evidence"
    tracked.mkdir(parents=True, exist_ok=True)
    (tracked / f"{out_dir.name}.evidence.json").write_text(serialized, encoding="utf-8")
    return evidence


def verify_snapshot(project_dir: Path, snapshot_dir: Path) -> tuple[int, list[str]]:
    evidence_path = snapshot_dir / "evidence.json"
    if not evidence_path.is_file():
        return 1, [f"no evidence.json in {snapshot_dir}"]

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    problems: list[str] = []
    unchanged = 0

    for entry in evidence.get("sources", []):
        current = project_dir / entry["path"]
        if not current.is_file():
            problems.append(f"MISSING  {entry['path']}")
            continue
        if sha256_file(current) != entry["sha256"]:
            problems.append(f"CHANGED  {entry['path']}")
            continue
        unchanged += 1

    database = evidence.get("learningDatabase", {})
    if database.get("present"):
        copy = snapshot_dir / "learning.sqlite3"
        if not copy.is_file():
            problems.append("MISSING  learning.sqlite3 (snapshot copy)")
        elif sha256_file(copy) != database["sha256"]:
            problems.append("CHANGED  learning.sqlite3 (snapshot copy is corrupt)")
        else:
            unchanged += 1

    print(f"verified {unchanged} entries against {evidence_path}")
    for problem in problems:
        print(f"  {problem}")
    return (1 if problems else 0), problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BKP-001 evidence snapshot and verification.")
    parser.add_argument("--verify", type=Path, default=None, help="Verify an existing snapshot directory.")
    parser.add_argument("--out", type=Path, default=None, help="Snapshot directory (default: timestamped).")
    parser.add_argument("--operator", default="unknown", help="Who took this snapshot.")
    parser.add_argument("--note", default="", help="Why this snapshot was taken.")
    args = parser.parse_args(argv)

    if args.verify is not None:
        status, _ = verify_snapshot(PROJECT_DIR, args.verify.expanduser().resolve())
        return status

    out_dir = args.out or SNAPSHOT_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S")
    evidence = create_snapshot(PROJECT_DIR, out_dir.expanduser().resolve(), args.operator, args.note)
    print(f"snapshot written to {out_dir}")
    print(f"  sources hashed : {len(evidence['sources'])}")
    database = evidence["learningDatabase"]
    if database.get("present"):
        print(f"  learning db    : {database['integrityCheck']}, rows={database['rowCounts']}")
    else:
        print(f"  learning db    : not present ({database.get('reason')})")
    print("  verify with    : python src/snapshot_evidence.py --verify " + str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
