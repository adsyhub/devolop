"""Asset ingestion, streaming upload, sha256 hashing, and deduplication.

Manages raw incoming materials (audio files, video URLs, PDF documents):
- Saves uploaded files into content-addressable storage `studio-work/assets/<sha256[:2]>/<sha256>/<filename>`
- Computes sha256 incrementally during streaming without holding full file in memory.
- Registers assets in StudioJobStore's `assets` table.
- Detects exact duplicates and reuses existing assets and completed jobs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, BinaryIO

from bundle_io import safe_filename
from studio_job_store import StudioJobStore


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StoredAsset:
    id: str
    source_kind: str
    source_sha256: str
    canonical_source_key: str
    stored_path: Path
    metadata: dict[str, Any]
    is_duplicate: bool = False


class AssetManager:
    """Manages content-addressed asset storage and deduplication."""

    def __init__(self, store: StudioJobStore, assets_root: Path) -> None:
        self.store = store
        self.assets_root = Path(assets_root).expanduser().resolve()
        self.assets_root.mkdir(parents=True, exist_ok=True)

    def ingest_stream(
        self,
        stream: BinaryIO,
        filename: str,
        source_kind: str,
        *,
        max_bytes: int = 1024 * 1024 * 1024,
        chunk_size: int = 64 * 1024,
        extra_metadata: dict[str, Any] | None = None,
    ) -> StoredAsset:
        """Stream data to a temp file, calculate sha256, and atomically move to CAS storage."""
        clean_name = safe_filename(filename) or "upload.bin"
        tmp_dir = self.assets_root / ".staging"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"upload_{os.getpid()}_{datetime.now().timestamp()}_{clean_name}"

        hasher = hashlib.sha256()
        bytes_read = 0

        try:
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = stream.read(chunk_size)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    if bytes_read > max_bytes:
                        raise ValueError(f"Uploaded file exceeds maximum allowed size of {max_bytes} bytes")
                    hasher.update(chunk)
                    f.write(chunk)

            sha256_hex = hasher.hexdigest()
            return self._finalize_asset(
                tmp_path=tmp_path,
                sha256_hex=sha256_hex,
                clean_name=clean_name,
                source_kind=source_kind,
                size_bytes=bytes_read,
                extra_metadata=extra_metadata,
            )
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def ingest_file(
        self,
        file_path: Path,
        source_kind: str,
        extra_metadata: dict[str, Any] | None = None,
    ) -> StoredAsset:
        """Ingest an existing local file into CAS storage."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Source file not found: {path}")

        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(64 * 1024):
                hasher.update(chunk)

        sha256_hex = hasher.hexdigest()
        clean_name = safe_filename(path.name) or "file.bin"

        # If already exists in CAS, reuse without copying
        target_dir = self.assets_root / sha256_hex[:2] / sha256_hex
        final_path = target_dir / clean_name
        if not final_path.is_file():
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, final_path)

        return self._register_record(
            sha256_hex=sha256_hex,
            clean_name=clean_name,
            final_path=final_path,
            source_kind=source_kind,
            size_bytes=path.stat().st_size,
            extra_metadata=extra_metadata,
        )

    def _finalize_asset(
        self,
        tmp_path: Path,
        sha256_hex: str,
        clean_name: str,
        source_kind: str,
        size_bytes: int,
        extra_metadata: dict[str, Any] | None = None,
    ) -> StoredAsset:
        target_dir = self.assets_root / sha256_hex[:2] / sha256_hex
        final_path = target_dir / clean_name

        is_dup = False
        if final_path.is_file():
            is_dup = True
            tmp_path.unlink(missing_ok=True)
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp_path), str(final_path))

        return self._register_record(
            sha256_hex=sha256_hex,
            clean_name=clean_name,
            final_path=final_path,
            source_kind=source_kind,
            size_bytes=size_bytes,
            extra_metadata=extra_metadata,
            is_duplicate=is_dup,
        )

    def _register_record(
        self,
        sha256_hex: str,
        clean_name: str,
        final_path: Path,
        source_kind: str,
        size_bytes: int,
        extra_metadata: dict[str, Any] | None = None,
        is_duplicate: bool = False,
    ) -> StoredAsset:
        existing = self.store.get_asset_by_sha256(sha256_hex)
        if existing and Path(existing["stored_path"]).is_file():
            return StoredAsset(
                id=existing["id"],
                source_kind=existing["source_kind"],
                source_sha256=existing["source_sha256"],
                canonical_source_key=existing.get("canonical_source_key") or sha256_hex,
                stored_path=Path(existing["stored_path"]),
                metadata=existing.get("metadata") or {},
                is_duplicate=True,
            )

        asset_id = f"ast_{sha256_hex[:16]}"
        meta = {
            "filename": clean_name,
            "sizeBytes": size_bytes,
            **(extra_metadata or {}),
        }
        self.store.register_asset(
            asset_id=asset_id,
            source_kind=source_kind,
            source_sha256=sha256_hex,
            canonical_source_key=sha256_hex,
            stored_path=str(final_path),
            metadata=meta,
        )
        return StoredAsset(
            id=asset_id,
            source_kind=source_kind,
            source_sha256=sha256_hex,
            canonical_source_key=sha256_hex,
            stored_path=final_path,
            metadata=meta,
            is_duplicate=is_duplicate,
        )

    def find_reusable_job(
        self,
        asset_id: str,
        target_type: str,
        policy_id: str,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Find a previous completed job for the same asset and configuration."""
        jobs = self.store.list_jobs(execution_status="completed", target_type=target_type)
        params_str = json.dumps(params, sort_keys=True)
        for job in jobs:
            if job.get("assetId") == asset_id and job.get("policyId") == policy_id:
                job_params = job.get("params") or {}
                if json.dumps(job_params, sort_keys=True) == params_str:
                    return job
        return None

