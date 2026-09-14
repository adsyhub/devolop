"""Inventory tracking and verification for EJU question bank targets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import PIPELINE_STATUSES, RIGHTS_STATUSES
from .errors import ContractError
from .util import load_json, utc_now, write_json

from .schema_validation import require_schema

DEFAULT_INVENTORY_PATH = Path("content/content-inventory.json")


def load_inventory(inventory_path: Path | None = None) -> dict[str, Any]:
    path = (inventory_path or DEFAULT_INVENTORY_PATH).expanduser().resolve()
    if not path.exists():
        return {
            "schemaVersion": 1,
            "updatedAt": utc_now(),
            "items": [],
        }
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ContractError(f"Invalid inventory file format at {path}")
    require_schema("content-inventory", data)
    return data


def save_inventory(data: dict[str, Any], inventory_path: Path | None = None) -> None:
    path = (inventory_path or DEFAULT_INVENTORY_PATH).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updatedAt"] = utc_now()
    require_schema("content-inventory", data)
    write_json(path, data)


def get_inventory_item(inventory_id: str, inventory_path: Path | None = None) -> dict[str, Any] | None:
    data = load_inventory(inventory_path)
    for item in data.get("items", []):
        if item.get("inventoryId") == inventory_id:
            return item
    return None


def upsert_inventory_item(item: dict[str, Any], inventory_path: Path | None = None) -> dict[str, Any]:
    required = [
        "inventoryId",
        "session",
        "subject",
        "language",
        "syllabusId",
        "requiredFiles",
        "rightsStatus",
        "pipelineStatus",
        "expectedForms",
    ]
    for key in required:
        if key not in item:
            raise ContractError(f"Inventory item missing required field: {key}")
    if item["rightsStatus"] not in RIGHTS_STATUSES:
        raise ContractError(f"Invalid rightsStatus in inventory item: {item['rightsStatus']}")
    if item["pipelineStatus"] not in PIPELINE_STATUSES:
        raise ContractError(f"Invalid pipelineStatus in inventory item: {item['pipelineStatus']}")

    data = load_inventory(inventory_path)
    items = data.setdefault("items", [])
    found = False
    for idx, existing in enumerate(items):
        if existing.get("inventoryId") == item["inventoryId"]:
            items[idx] = item
            found = True
            break
    if not found:
        items.append(item)
    save_inventory(data, inventory_path)
    return item


def inventory_status_summary(inventory_path: Path | None = None) -> dict[str, Any]:
    data = load_inventory(inventory_path)
    items = data.get("items", [])
    total = len(items)
    by_status: dict[str, int] = {}
    blocked_count = 0
    published_count = 0
    complete_count = 0
    for item in items:
        status = str(item.get("pipelineStatus") or "UNKNOWN")
        by_status[status] = by_status.get(status, 0) + 1
        if status == "PUBLISHED" or item.get("publishedVersionId"):
            published_count += 1
        if item.get("blockingIssues") or status.startswith("BLOCKED") or status.startswith("MISSING") or status.endswith("FAILED"):
            blocked_count += 1
        if item.get("completeness") == "COMPLETE" and item.get("reviewState") == "REVIEWED" and not item.get("blockingIssues") and (status == "PUBLISHED" or item.get("publishedVersionId")):
            complete_count += 1

    return {
        "total": total,
        "published": published_count,
        "blocked": blocked_count,
        "complete": complete_count,
        "publicationRate": round(published_count / total, 4) if total else 0.0,
        "completionRate": round(complete_count / total, 4) if total else 0.0,
        "byStatus": by_status,
        "items": items,
        "updatedAt": data.get("updatedAt"),
    }
