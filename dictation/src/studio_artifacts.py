"""Unified artifact versioning, immutable storage, and atomic current pointer.

Implements section 12.1 and B03 of docs/DICTATION_WORKBENCH_AUTOMATION_PLAN.md:
- Separates artifactRevision, contentRevision, and answerVersion.
- Immutable layout: <target_dir>/versions/<artifactRevision>/ + <target_dir>/current.json.
- Atomic commit via os.replace on temporary pointer file.
- Backward compatibility: transparent fallback to root manifest.json / pack.json / exam.json when current.json is absent.
- Provides shared resolution functions for courses, lexicon, and exams.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any


CURRENT_SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_directory_artifact_revision(directory: Path) -> str:
    """Compute deterministic SHA256 of all relevant files in directory (excluding current.json, logs, backups)."""
    h = hashlib.sha256()
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            rel = p.relative_to(directory).as_posix()
            if rel.startswith(".") or rel.startswith("versions") or rel in {"current.json", "install-source.json"}:
                continue
            h.update(rel.encode("utf-8"))
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ Resolvers

def resolve_course_manifest_path(course_dir: Path) -> Path | None:
    """Resolve manifest.json for course_dir respecting current.json pointer if present."""
    if not course_dir.is_dir():
        return None
    current_file = course_dir / "current.json"
    if current_file.is_file():
        try:
            cur = json.loads(current_file.read_text(encoding="utf-8-sig"))
            rev = str(cur.get("artifactRevision") or "")
            if rev:
                versioned = course_dir / "versions" / rev / "manifest.json"
                if versioned.is_file():
                    return versioned
        except Exception:
            pass
    fallback = course_dir / "manifest.json"
    return fallback if fallback.is_file() else None


def resolve_course_audio_path(course_dir: Path, audio_filename: str) -> Path | None:
    """Resolve audio file inside course_dir respecting current.json pointer if present."""
    if not course_dir.is_dir() or not audio_filename:
        return None
    current_file = course_dir / "current.json"
    if current_file.is_file():
        try:
            cur = json.loads(current_file.read_text(encoding="utf-8-sig"))
            rev = str(cur.get("artifactRevision") or "")
            if rev:
                versioned = course_dir / "versions" / rev / audio_filename
                if versioned.is_file():
                    return versioned
        except Exception:
            pass
    fallback = course_dir / audio_filename
    return fallback if fallback.is_file() else None


def resolve_lexicon_pack_path(pack_dir: Path) -> Path | None:
    """Resolve pack.json for pack_dir respecting current.json pointer if present."""
    if not pack_dir.is_dir():
        return None
    current_file = pack_dir / "current.json"
    if current_file.is_file():
        try:
            cur = json.loads(current_file.read_text(encoding="utf-8-sig"))
            rev = str(cur.get("artifactRevision") or "")
            if rev:
                versioned = pack_dir / "versions" / rev / "pack.json"
                if versioned.is_file():
                    return versioned
        except Exception:
            pass
    fallback = pack_dir / "pack.json"
    return fallback if fallback.is_file() else None


def resolve_exam_manifest_path(exam_dir: Path) -> Path | None:
    """Resolve exam.json for exam_dir respecting current.json pointer if present."""
    if not exam_dir.is_dir():
        return None
    current_file = exam_dir / "current.json"
    if current_file.is_file():
        try:
            cur = json.loads(current_file.read_text(encoding="utf-8-sig"))
            rev = str(cur.get("artifactRevision") or "")
            if rev:
                versioned = exam_dir / "versions" / rev / "exam.json"
                if versioned.is_file():
                    return versioned
        except Exception:
            pass
    fallback = exam_dir / "exam.json"
    return fallback if fallback.is_file() else None


# ------------------------------------------------------------------ Install & Commit

def commit_artifact_from_staging(
    target_dir: Path,
    staging_dir: Path,
    *,
    manifest_name: str = "manifest.json",
    content_revision: str = "",
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically commit an artifact from staging into target_dir under an immutable version."""
    target_dir = Path(target_dir).resolve()
    staging_dir = Path(staging_dir).resolve()

    manifest_file = staging_dir / manifest_name
    if not manifest_file.is_file():
        raise ValueError(f"Staging directory missing {manifest_name}: {staging_dir}")

    artifact_revision = compute_directory_artifact_revision(staging_dir)
    versions_dir = target_dir / "versions"
    version_dir = versions_dir / artifact_revision
    version_dir.mkdir(parents=True, exist_ok=True)

    # Copy files into immutable version directory
    for item in staging_dir.iterdir():
        dest = version_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    # Also keep legacy root projection for tools not yet using current.json
    for item in staging_dir.iterdir():
        if item.name == "versions" or item.name == "current.json":
            continue
        root_dest = target_dir / item.name
        if item.is_dir():
            pass
        else:
            shutil.copy2(item, root_dest)

    # Write temporary pointer and atomic replace
    now = utc_now_iso()
    pointer_data = {
        "schemaVersion": CURRENT_SCHEMA_VERSION,
        "artifactRevision": artifact_revision,
        "contentRevision": content_revision or artifact_revision,
        "manifestName": manifest_name,
        "installedAt": now,
        "metadata": extra_meta or {},
    }
    tmp_ptr = target_dir / f".current.json.tmp.{os.getpid()}"
    tmp_ptr.write_text(json.dumps(pointer_data, ensure_ascii=False, indent=2), encoding="utf-8")
    current_ptr = target_dir / "current.json"
    os.replace(tmp_ptr, current_ptr)

    return {
        "targetDir": str(target_dir),
        "artifactRevision": artifact_revision,
        "contentRevision": content_revision or artifact_revision,
        "manifestPath": str(version_dir / manifest_name),
        "currentPointer": str(current_ptr),
        "installedAt": now,
    }


def list_artifact_versions(target_dir: Path) -> list[dict[str, Any]]:
    versions: list[dict[str, Any]] = []
    v_dir = target_dir / "versions"
    if not v_dir.is_dir():
        return versions

    current_rev = ""
    c_ptr = target_dir / "current.json"
    if c_ptr.is_file():
        try:
            current_rev = json.loads(c_ptr.read_text(encoding="utf-8-sig")).get("artifactRevision", "")
        except Exception:
            pass

    for d in sorted(v_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if d.is_dir():
            rev = d.name
            versions.append({
                "artifactRevision": rev,
                "path": str(d),
                "isCurrent": (rev == current_rev),
                "mtime": d.stat().st_mtime,
            })
    return versions


def rollback_artifact(target_dir: Path, target_revision: str) -> bool:
    """Atomically rollback current.json to a previously installed version directory."""
    target_dir = Path(target_dir).resolve()
    version_dir = target_dir / "versions" / target_revision
    if not version_dir.is_dir():
        raise ValueError(f"Version {target_revision} does not exist in {target_dir / 'versions'}")

    current_ptr = target_dir / "current.json"
    existing = {}
    if current_ptr.is_file():
        try:
            existing = json.loads(current_ptr.read_text(encoding="utf-8-sig"))
        except Exception:
            pass

    existing["artifactRevision"] = target_revision
    existing["rolledBackAt"] = utc_now_iso()

    tmp_ptr = target_dir / f".current.json.tmp.{os.getpid()}"
    tmp_ptr.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_ptr, current_ptr)
    return True

