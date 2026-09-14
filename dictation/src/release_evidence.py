"""Deterministic bindings shared by browser evidence and release readiness."""

from __future__ import annotations

import hashlib
from pathlib import Path


REQUIRED_WEB_ASSETS = {
    "index.html",
    "app.css",
    "app.js",
    "sw.js",
    "manifest.webmanifest",
    "icon.svg",
    "icon-192.png",
    "icon-512.png",
    "_headers",
}


def web_assets_sha256(web_dir: Path) -> str:
    """Hash every file in the web directory, including its relative path."""
    web_dir = web_dir.resolve()
    if not web_dir.is_dir():
        raise ValueError(f"Web asset directory is missing: {web_dir}")
    files = sorted(
        (path for path in web_dir.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(web_dir).as_posix(),
    )
    if not files:
        raise ValueError(f"Web asset directory is empty: {web_dir}")
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(web_dir).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
