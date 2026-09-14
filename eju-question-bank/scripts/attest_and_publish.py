#!/usr/bin/env python3
"""Drive the real review pipeline for sources the machine can fully verify.

This is the path that was missing. The extraction chain produced honest content
and the review chain could publish it, but nothing connected the two: no page
ever became a contract, so no page was ever cleared, so no release was ever
assembled, and the library sat at zero practicable papers.

For each source this script writes page contracts from the OCR the pipeline
already has, records a machine attestation on the pages where every element
checks out, derives a structure baseline from exactly those pages, then walks
the ordinary ``candidate → approve → publish`` path. Every gate stays in force.
Nothing is marked SYNTHETIC and ``allow_synthetic`` is never set, so the paper
has to satisfy the same review certificate a hand-signed one does.

A machine attestation is weaker than a human signature and says so: the paper
carries ``reviewGrade: MACHINE_ATTESTED`` all the way to the learner's screen.

    python scripts/attest_and_publish.py --database library/eju.db --limit 1
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eju_bank.attest import clear_source, publish_source
from eju_bank.db import Database
from eju_bank.review import ContentWorkspace

# 判断本身住在 eju_bank/attest.py：制课台走的是同一条路，两处各留一份必然分叉。


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", type=Path, default=ROOT / "library/eju.db")
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--media-dir", type=Path, default=None)
    parser.add_argument("--source", action="append", default=[],
                        help="work 目录名，可重复；默认全部")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--channel", default="PRIVATE")
    parser.add_argument("--clear-only", action="store_true",
                        help="只写合约与证明，不组卷发布")
    args = parser.parse_args()

    database = Database(args.database, media_dir=args.media_dir,
                        workspace_root=args.workspace_root)
    workspace = ContentWorkspace(args.workspace_root, database)
    names = args.source or [p.parent.name for p in
                            sorted((args.workspace_root / "work").glob("*/source-manifest.json"))]
    if args.limit:
        names = names[:args.limit]

    started = time.time()
    published = skipped = failed = 0
    total_questions = 0
    for index, name in enumerate(names, 1):
        work = args.workspace_root / "work" / name
        manifest_path = work / "source-manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        try:
            stats = clear_source(workspace, work, manifest)
        except Exception as exc:
            failed += 1
            print(f"[{index:3d}/{len(names)}] ✗ {name:24s} 合约阶段 {type(exc).__name__}: {exc}")
            continue
        cleared = stats["cleared"]
        note = (f"题册 {stats['booklet_attested']}/{stats['booklet_pages']} 页"
                f" · 答案 {stats['answer_attested']}/{stats['answer_pages']} 页")
        if args.clear_only:
            print(f"[{index:3d}/{len(names)}] · {name:24s} {note}")
            continue
        if not cleared["QUESTION_BOOKLET"] or not cleared["ANSWER_KEY"]:
            skipped += 1
            print(f"[{index:3d}/{len(names)}] – {name:24s} {note} → 无可发布页，跳过")
            continue
        try:
            out = publish_source(workspace, manifest, cleared, channel=args.channel,
                                 form_refs=stats.get("form_refs"))
            published += 1
            total_questions += out["questions"] or 0
            print(f"[{index:3d}/{len(names)}] ✓ {name:24s} {note} → {out['paperId']} "
                  f"v{out['version']} {out['questions']} 题 {out['grade']} {out['completeness']}")
        except Exception as exc:
            failed += 1
            print(f"[{index:3d}/{len(names)}] ✗ {name:24s} {note} → "
                  f"{type(exc).__name__}: {str(exc)[:160]}")
            if stats["errors"]:
                print(f"      合约阶段前 2 条问题: {stats['errors'][:2]}")

    database.close()
    print(f"\n发布 {published} 套，跳过 {skipped}，失败 {failed}，"
          f"题目 {total_questions}，耗时 {time.time()-started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
