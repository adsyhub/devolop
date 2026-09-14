"""Rights-aware publication wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .db import Database
from .errors import RightsError
from .util import load_json


def assert_publish_rights(paper: dict[str, Any], channel: str) -> None:
    status = str((paper.get("source") or {}).get("rights", {}).get("status") or "")
    if status == "SUSPENDED":
        raise RightsError("Source rights are suspended")
    allowed = {
        "PRIVATE": {"PRIVATE_STUDY", "INTERNAL_REVIEW", "PUBLIC_LICENSED", "COMMERCIAL_LICENSED"},
        "PUBLIC": {"PUBLIC_LICENSED", "COMMERCIAL_LICENSED"},
        "COMMERCIAL": {"COMMERCIAL_LICENSED"},
    }
    if channel not in allowed:
        raise RightsError(f"Unknown publication channel: {channel}")
    if status not in allowed[channel]:
        raise RightsError(f"rights.status={status or 'missing'} does not allow {channel} publication")


def publish_file(paper_path: Path, database_path: Path, *, channel: str, media_dir=None, workspace_root=None) -> dict[str, Any]:
    paper = load_json(paper_path.expanduser().resolve())
    assert_publish_rights(paper, channel)
    database = Database(database_path,media_dir=media_dir,workspace_root=workspace_root)
    try:
        return database.publish(paper, channel=channel)
    finally:
        database.close()

