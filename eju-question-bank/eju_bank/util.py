"""Small deterministic and filesystem-safe helpers."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .errors import ContractError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path | str, *, chunk_size: int = 1024 * 1024) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: Any, length: int = 24) -> str:
    return prefix + digest_json(list(parts))[:length]


def load_json(path: Path | str) -> Any:
    path = Path(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"JSON file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path | str, value: Any) -> None:
    """Atomically write UTF-8 JSON so interrupted jobs never leave half a page."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def resolve_manifest_file(manifest_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = manifest_path.parent / candidate
    return candidate.resolve()


def parse_page_selection(value: str | None, total_pages: int) -> list[int]:
    """Return one-based pages from `1,3,8-12`; None means every page."""
    if value is None or not value.strip():
        return list(range(1, total_pages + 1))
    pages: set[int] = set()
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            try:
                start, end = int(left), int(right)
            except ValueError as exc:
                raise ContractError(f"Invalid page range: {part!r}") from exc
            if start > end:
                raise ContractError(f"Page range is backwards: {part!r}")
            pages.update(range(start, end + 1))
        else:
            try:
                pages.add(int(part))
            except ValueError as exc:
                raise ContractError(f"Invalid page number: {part!r}") from exc
    invalid = sorted(page for page in pages if page < 1 or page > total_pages)
    if invalid:
        raise ContractError(f"Pages outside 1-{total_pages}: {invalid}")
    return sorted(pages)
