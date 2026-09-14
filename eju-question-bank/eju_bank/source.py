"""Source manifests and immutable input identity."""

from __future__ import annotations

from pathlib import Path
import os
from typing import Any

from .constants import FILE_ROLES, RIGHTS_STATUSES, SOURCE_MANIFEST_VERSION, SOURCE_SUBJECTS
from .errors import ContractError
from .util import resolve_manifest_file, sha256_file, stable_id, utc_now, write_json


def file_record(path: Path, role: str, *, stored_path: str | None = None) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if role not in FILE_ROLES:
        raise ContractError(f"Unsupported source file role: {role}")
    if not path.is_file():
        raise ContractError(f"Source file does not exist: {path}")
    return {
        "role": role,
        "path": stored_path if stored_path is not None else str(path),
        "fileName": path.name,
        "sizeBytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def create_source_manifest(
    *,
    session: str,
    subject: str,
    language: str,
    syllabus_version: str,
    question_booklet: Path,
    answer_key: Path | None,
    rights_status: str,
    rights_note: str,
    output_path: Path,
) -> dict[str, Any]:
    subject = subject.upper()
    if subject not in SOURCE_SUBJECTS:
        raise ContractError(f"Unsupported source subject: {subject}")
    if language not in {"ja", "en"}:
        raise ContractError("language must be 'ja' or 'en'")
    if subject == "JAPANESE" and language != "ja":
        raise ContractError("The EJU Japanese subject is administered in Japanese only.")
    if rights_status not in RIGHTS_STATUSES:
        raise ContractError(f"Unsupported rights status: {rights_status}")

    output_path = output_path.expanduser().resolve()
    question_booklet = question_booklet.expanduser().resolve()
    files = [file_record(question_booklet, "QUESTION_BOOKLET", stored_path=Path(os.path.relpath(question_booklet, output_path.parent)).as_posix())]
    if answer_key is not None:
        files.append(file_record(answer_key, "ANSWER_KEY", stored_path=Path(os.path.relpath(answer_key.expanduser().resolve(), output_path.parent)).as_posix()))
    source_id = stable_id("src_", "EJU", session, subject, files[0]["sha256"])
    manifest = {
        "schemaVersion": SOURCE_MANIFEST_VERSION,
        "sourceId": source_id,
        "examFamily": "EJU",
        "session": session,
        "subject": subject,
        "language": language,
        "syllabusVersion": str(syllabus_version),
        "files": files,
        "rights": {"status": rights_status, "note": rights_note},
        "createdAt": utc_now(),
    }
    validate_source_manifest(manifest, output_path, verify_files=True)
    write_json(output_path, manifest)
    return manifest


from .schema_validation import require_schema


def validate_source_manifest(
    manifest: dict[str, Any], manifest_path: Path, *, verify_files: bool = False
) -> None:
    require_schema("source-manifest", manifest)
    if manifest.get("schemaVersion") != SOURCE_MANIFEST_VERSION:
        raise ContractError(f"Only source manifest version {SOURCE_MANIFEST_VERSION} is supported.")
    if manifest.get("examFamily") != "EJU":
        raise ContractError("source manifest examFamily must be EJU")
    if str(manifest.get("subject")) not in SOURCE_SUBJECTS:
        raise ContractError(f"Invalid source subject: {manifest.get('subject')!r}")
    if manifest.get("language") not in {"ja", "en"}:
        raise ContractError("Invalid source language")
    rights = manifest.get("rights")
    if not isinstance(rights, dict) or rights.get("status") not in RIGHTS_STATUSES:
        raise ContractError("A valid rights.status is required")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ContractError("source manifest needs at least one file")
    roles = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise ContractError(f"files[{index}] must be an object")
        role = item.get("role")
        if role not in FILE_ROLES:
            raise ContractError(f"files[{index}] has invalid role {role!r}")
        roles.append(role)
        digest = str(item.get("sha256") or "").lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ContractError(f"files[{index}] has invalid SHA-256")
        if verify_files:
            path = resolve_manifest_file(manifest_path, str(item.get("path") or ""))
            if not path.is_file():
                raise ContractError(f"Source file is missing: {path}")
            if sha256_file(path) != digest:
                raise ContractError(f"Source file hash changed: {path}")
    if "QUESTION_BOOKLET" not in roles:
        raise ContractError("source manifest needs a QUESTION_BOOKLET")


def source_file(manifest: dict[str, Any], manifest_path: Path, role: str) -> Path:
    matches = [item for item in manifest.get("files", []) if item.get("role") == role]
    if len(matches) != 1:
        raise ContractError(f"Expected exactly one {role} file, found {len(matches)}")
    return resolve_manifest_file(manifest_path, str(matches[0]["path"]))

