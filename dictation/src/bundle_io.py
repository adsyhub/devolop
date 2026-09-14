"""Shared bundle IO: atomic JSON writes, hashing, and ZIP build/verify.

These helpers used to live inside ``build_deepseek_offline_bundle`` and were
imported from there by nine unrelated modules, which made that one file both the
DeepSeek pipeline *and* the project's utility hub. Splitting them out lets the
pipeline become provider-agnostic without breaking every importer: the old
module re-exports everything defined here.

Nothing in this module knows about models, providers, or networks.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    """Write JSON atomically so an interrupted build never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    temp_handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    temp_path = Path(temp_handle.name)
    try:
        with temp_handle:
            temp_handle.write(text)
            temp_handle.flush()
            os.fsync(temp_handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_have_same_content(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    return sha256_file(left) == sha256_file(right)


def canonical_json_sha256(data: Any) -> str:
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_jsonish(text: str) -> dict[str, Any]:
    """Recover a JSON object from model output that may be fenced or prefixed.

    Providers that cannot be pinned to a JSON response format (local runtimes,
    CLI bridges, chat UIs) routinely wrap the object in a code fence or add a
    sentence before it. Refusing those outright would rule out exactly the
    providers this project wants to support.
    """
    text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            data = json.loads(fenced.group(1))
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end <= start:
                raise
            data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("Model output must be a JSON object.")
    return data


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\|?*\x00-\x1f]+', "-", value).strip(" .-")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "dictation-course"


def safe_audio_name(audio_path: Path) -> str:
    suffix = audio_path.suffix.lower()
    if suffix in {".mpeg", ".mpga"}:
        suffix = ".mp3"
    return f"audio{suffix}"


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def confidence_from_logprob(avg_logprob: float | None) -> float | None:
    if avg_logprob is None:
        return None
    return round(max(0.0, min(1.0, math.exp(avg_logprob))), 4)


def format_timestamp(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        return "--:--"
    total_seconds = int(round(seconds))
    minutes, sec = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:d}:{sec:02d}"


def build_zip(
    manifest_path: Path,
    audio_path: Path,
    audio_name: str,
    out_path: Path,
    *,
    quality_report_path: Path | None = None,
    web_dir: Path | None = None,
    force: bool,
) -> None:
    if out_path.exists() and not force:
        raise SystemExit(f"Output already exists: {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temp_handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{out_path.name}.",
        suffix=".tmp",
        dir=out_path.parent,
        delete=False,
    )
    temp_path = Path(temp_handle.name)
    temp_handle.close()
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(manifest_path, "manifest.json")
            zf.write(audio_path, audio_name)
            if quality_report_path is not None:
                zf.write(quality_report_path, "quality-report.json")
            if web_dir is not None:
                if not web_dir.is_dir():
                    raise SystemExit(f"Web player not found: {web_dir}")
                for asset in sorted(web_dir.rglob("*")):
                    if asset.is_file():
                        zf.write(asset, asset.relative_to(web_dir).as_posix())
        verify_zip(temp_path)
        os.replace(temp_path, out_path)
    finally:
        temp_path.unlink(missing_ok=True)


def verify_zip(out_path: Path) -> None:
    with zipfile.ZipFile(out_path) as zf:
        corrupt_name = zf.testzip()
        if corrupt_name is not None:
            raise SystemExit(f"ZIP verification failed: corrupt file: {corrupt_name}")
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise SystemExit("ZIP verification failed: duplicate file names")
        for name in names:
            normalized = name.replace("\\", "/")
            parts = normalized.split("/")
            if normalized.startswith("/") or ".." in parts:
                raise SystemExit(f"ZIP verification failed: unsafe file path: {name}")
        if "manifest.json" not in names:
            raise SystemExit("ZIP verification failed: manifest.json missing")
        manifest = json.loads(zf.read("manifest.json").decode("utf-8-sig"))
        # An online-video bundle has no media member by design — the video is never
        # downloaded — so demanding one here would make every such bundle unverifiable.
        # A local course still must carry its audio, and must carry a real one.
        if not isinstance(manifest.get("media"), dict):
            audio_name = manifest.get("audio")
            if audio_name not in names:
                raise SystemExit(f"ZIP verification failed: audio missing: {audio_name}")
            if zf.getinfo(audio_name).file_size <= 0:
                raise SystemExit("ZIP verification failed: audio file is empty")
        sentences = manifest.get("sentences")
        if not isinstance(sentences, list) or not sentences:
            raise SystemExit("ZIP verification failed: no sentences")
