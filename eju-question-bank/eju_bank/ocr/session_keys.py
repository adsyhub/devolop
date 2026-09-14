"""Register the session-wide 正解表 on every source of that session.

EJU publishes one answer document per examination session, covering all four
subject groups in one booklet. Only 65 of 215 source manifests happen to list
it, because whoever filed the sources attached it to one subject and left the
siblings without. The assembler already reads across siblings for answers, but
:meth:`eju_bank.review.ContentWorkspace.candidate` refuses to assemble a release
unless the source itself declares an ``ANSWER_KEY`` file — so 111 sources that
have a perfectly good answer document cannot reach a release at all.

Registering it is recording a fact, not inventing one: the file already exists
on disk, the session's other manifests already point at it, and every name a
session uses for it hashes to the same bytes. This module finds that file and
adds it to the manifests that omit it, leaving everything else untouched.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..source import resolve_manifest_file
from ..util import sha256_file, write_json

ROLE = "ANSWER_KEY"


def _manifests(work_root: Path) -> list[tuple[Path, dict[str, Any]]]:
    out = []
    for path in sorted(work_root.glob("*/source-manifest.json")):
        try:
            out.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return out


def session_answer_keys(work_root: Path) -> dict[str, dict[str, Any]]:
    """``{session: file entry}`` for every session that has an answer document.

    A session may list the same bytes under several names (``…第1回答案.pdf`` and
    ``…第1回数学1答案.pdf`` are copies). The entry whose file resolves and whose
    hash still matches wins, preferring the name without a subject in it so the
    registered entry reads as what it is: the whole session's key.
    """
    found: dict[str, list[tuple[int, Path, dict[str, Any]]]] = {}
    for path, manifest in _manifests(work_root):
        session = str(manifest.get("session") or "")
        for item in manifest.get("files", []):
            if item.get("role") != ROLE:
                continue
            try:
                resolved = resolve_manifest_file(path, str(item.get("path") or ""))
            except Exception:
                continue
            if not resolved.is_file() or sha256_file(resolved) != str(item.get("sha256") or "").lower():
                continue
            # 文件名里带科目的是抄本，优先用不带科目的那个名字。
            subject_in_name = any(tag in str(item.get("fileName") or "")
                                  for tag in ("数学", "理科", "日语", "日本語", "総合", "综合"))
            found.setdefault(session, []).append((1 if subject_in_name else 0, resolved, item))
    result = {}
    for session, entries in found.items():
        entries.sort(key=lambda e: (e[0], str(e[1])))
        result[session] = dict(entries[0][2])
    return result


def register_session_answer_key(
    manifest_path: Path, entry: dict[str, Any], source_path: Path, *, dry_run: bool = False
) -> bool:
    """Add ``entry`` as this manifest's ANSWER_KEY. Returns whether it changed.

    The stored path is rewritten relative to this manifest so the file resolves
    from here, and the hash is re-read from disk rather than copied, so a stale
    hash in the donor manifest cannot propagate.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(f.get("role") == ROLE for f in manifest.get("files", [])):
        return False
    import os

    relative = os.path.relpath(source_path.resolve(), manifest_path.parent.resolve())
    new = {
        "role": ROLE,
        "path": relative,
        "fileName": source_path.name,
        "sizeBytes": source_path.stat().st_size,
        "sha256": sha256_file(source_path),
        # 这一条是登记来的：文件属于整个回次，不是这套卷独有的附件。
        "registeredFrom": "SESSION_ANSWER_KEY",
    }
    if new["sha256"] != str(entry.get("sha256") or "").lower():
        raise ValueError(f"{source_path} hash changed since it was discovered")
    manifest["files"] = list(manifest["files"]) + [new]
    if not dry_run:
        write_json(manifest_path, manifest)
    return True


def register_all(work_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Register each session's answer document on the sources that lack one."""
    keys = session_answer_keys(work_root)
    added, skipped, missing = [], [], []
    for path, manifest in _manifests(work_root):
        session = str(manifest.get("session") or "")
        if any(f.get("role") == ROLE for f in manifest.get("files", [])):
            skipped.append(path.parent.name)
            continue
        entry = keys.get(session)
        if not entry:
            missing.append((path.parent.name, session))
            continue
        donor = None
        for donor_path, donor_manifest in _manifests(work_root):
            if str(donor_manifest.get("session")) != session:
                continue
            for item in donor_manifest.get("files", []):
                if item.get("role") == ROLE and item.get("sha256") == entry.get("sha256"):
                    try:
                        candidate = resolve_manifest_file(donor_path, str(item["path"]))
                    except Exception:
                        continue
                    if candidate.is_file():
                        donor = candidate
                        break
            if donor:
                break
        if not donor:
            missing.append((path.parent.name, session))
            continue
        if register_session_answer_key(path, entry, donor, dry_run=dry_run):
            added.append(path.parent.name)
    return {"added": added, "alreadyHad": skipped, "noSessionKey": missing,
            "sessionsWithKey": sorted(keys)}
