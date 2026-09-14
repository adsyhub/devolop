#!/usr/bin/env python3
"""Suspend published papers whose content or answers were never verified.

Two things make a published paper unfit for practice:

* its options are the literal placeholders ``選択肢 (1)`` … — no real content
  was ever read off the page;
* it carries no review certificate, so nobody signed off on it.

Both are true of everything the old ``build_and_publish_all.py`` wrote: it
fabricated stems, options and correct answers (``(q_num % 5) + 1`` and friends)
and called ``db.publish`` directly, bypassing the review pipeline.

Suspension is the project's own mechanism (``set_delivery_state``): the version
stays in the library, learners keep their history, and the paper simply stops
being offered for new practice. Nothing is deleted.

The inventory is corrected in the same pass. The old script marked every entry
``PUBLISHED``, which claims an acceptance that never happened.

Run with ``--apply`` to make the change; without it, nothing is written.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eju_bank.db import Database
from eju_bank.inventory import load_inventory, save_inventory

PLACEHOLDER_NOTE = (
    "内容未经复核：题干为模板、选项为占位符「選択肢 (n)」、正确答案由题号算式生成，"
    "并且没有任何复核签署记录。已停止新练习，历史作答与内容均保留。"
    "重新开放需要走 OCR → 逐页复核签署 → 结构签署 → 整卷签署 → 发布。"
)
UNSIGNED_NOTE = (
    "没有复核签署记录：该版本绕过了逐页复核与整卷审批流程。已停止新练习，"
    "历史作答与内容均保留。"
)


def is_placeholder(paper: dict) -> bool:
    options = [
        node.get("value", "")
        for form in paper.get("forms", [])
        for group in form.get("groups", [])
        for question in group.get("questions", [])
        for option in (question.get("options") or [])
        for node in (option.get("contentAst") or [])
        if isinstance(node, dict) and node.get("type") == "text"
    ]
    return bool(options) and all(o.startswith("選択肢 (") for o in options)


def latest_published(db: Database) -> list[dict]:
    rows = db.connection.execute(
        "SELECT p.stable_code, p.title, pv.id AS version_id, pv.version_number, pv.payload_json, "
        "ds.state AS delivery_state "
        "FROM papers p JOIN paper_versions pv ON pv.paper_id = p.id "
        "LEFT JOIN paper_delivery_state ds ON ds.paper_version_id = pv.id "
        "WHERE pv.status = 'PUBLISHED' AND pv.version_number = "
        "(SELECT MAX(x.version_number) FROM paper_versions x "
        " WHERE x.paper_id = p.id AND x.status = 'PUBLISHED') "
        "ORDER BY p.stable_code").fetchall()
    return [dict(r) for r in rows]


def has_certificate(db: Database, version_id: str) -> bool:
    if not db.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='paper_reviews'").fetchone():
        return False
    payload = json.loads(db.connection.execute(
        "SELECT payload_json FROM paper_versions WHERE id=?", (version_id,)).fetchone()[0])
    review = (payload.get("reviewSummary") or {}).get("reviewId")
    if not review:
        return False
    return bool(db.connection.execute(
        "SELECT 1 FROM paper_reviews WHERE id=?", (review,)).fetchone())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=PROJECT_ROOT / "library/eju.db")
    parser.add_argument("--media-dir", type=Path, default=PROJECT_ROOT / "library/media")
    parser.add_argument("--inventory", type=Path,
                        default=PROJECT_ROOT / "content/content-inventory.json")
    parser.add_argument("--apply", action="store_true", help="真正写入；不加则只报告")
    parser.add_argument("--keep", nargs="*", default=[],
                        help="即使未签署也保持开放的 stableCode（例如已人工确认的卷）")
    args = parser.parse_args()

    db = Database(args.database, media_dir=args.media_dir, allow_synthetic=True)
    keep = set(args.keep)
    placeholder: list[dict] = []
    unsigned: list[dict] = []
    fine: list[dict] = []

    for row in latest_published(db):
        paper = json.loads(row["payload_json"])
        if row["stable_code"] in keep:
            fine.append(row)
        elif is_placeholder(paper):
            placeholder.append(row)
        elif not has_certificate(db, row["version_id"]):
            unsigned.append(row)
        else:
            fine.append(row)

    print(f"已发布的最新版本 {len(placeholder) + len(unsigned) + len(fine)} 套：")
    print(f"  占位内容（题干模板 + 选项占位 + 编造答案）: {len(placeholder)} 套")
    print(f"  无复核签署（内容可能真实，但没人签过字）  : {len(unsigned)} 套")
    print(f"  保持开放                                  : {len(fine)} 套")
    for row in fine:
        print(f"      · {row['stable_code']}")

    already = sum(1 for r in placeholder + unsigned if r["delivery_state"] == "SUSPENDED")
    if already:
        print(f"  （其中 {already} 套此前已是 SUSPENDED）")

    if not args.apply:
        print("\n未加 --apply，没有写入任何改动。")
        db.close()
        return 0

    changed = 0
    for row in placeholder:
        if row["delivery_state"] != "SUSPENDED":
            db.set_delivery_state(row["version_id"], "SUSPENDED", PLACEHOLDER_NOTE)
            changed += 1
    for row in unsigned:
        if row["delivery_state"] != "SUSPENDED":
            db.set_delivery_state(row["version_id"], "SUSPENDED", UNSIGNED_NOTE)
            changed += 1
    print(f"\n已停止新练习: {changed} 套（版本、内容与学习记录全部保留）")

    # 清单里那些声称已验收的状态同样要纠正。
    if args.inventory.is_file():
        inventory = load_inventory(args.inventory)
        corrected = 0
        for item in inventory.get("items", []):
            if item.get("pipelineStatus") == "PUBLISHED":
                item["pipelineStatus"] = "RECEIVED"
                item["blockingIssues"] = sorted(set(item.get("blockingIssues") or []))
                item["notes"] = ((item.get("notes") or "") +
                                 " 流水线状态已从 PUBLISHED 纠正为 RECEIVED：此前的发布未经复核签署。").strip()
                corrected += 1
        if corrected:
            save_inventory(inventory, args.inventory)
        print(f"清单流水线状态纠正: {corrected} 条 PUBLISHED → RECEIVED")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
