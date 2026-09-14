#!/usr/bin/env python3
"""High-throughput multi-core image remastering engine for EJU scanned pages.

Whitens backgrounds to pure #ffffff, sharpens strokes, and crops listening visual materials.
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eju_bank.image_remaster import remaster_image_file


def _process_one_page(task: tuple[str, str, bool, bool]) -> bool:
    src_str, dst_str, tight, strip_hf = task
    src = Path(src_str)
    dst = Path(dst_str)
    if dst.exists() and dst.stat().st_size > 0:
        return False
    try:
        remaster_image_file(src, dst, tight_crop=tight, strip_header_footer=strip_hf)
        return True
    except Exception as e:
        print(f"Error remastering {src.name}: {e}", file=sys.stderr)
        return False


def main():
    work_root = PROJECT_ROOT / "work"
    ja_sessions = sorted([d for d in work_root.iterdir() if d.is_dir() and "-japanese" in d.name])

    tasks = []
    for s_dir in ja_sessions:
        render_parent = s_dir / "renders" / "question_booklet"
        if not render_parent.exists():
            continue
        qb_dirs = [d for d in render_parent.iterdir() if d.is_dir()]
        if not qb_dirs:
            continue
        qb_dir = qb_dirs[0]
        remaster_dir = s_dir / "remastered_renders"
        remaster_dir.mkdir(parents=True, exist_ok=True)

        for p_dir in qb_dir.iterdir():
            if p_dir.is_dir() and p_dir.name.startswith("page-"):
                try:
                    p_num = int(p_dir.name.split("-")[1])
                    raw = p_dir / "full-180dpi.png"
                    if raw.exists():
                        out = remaster_dir / f"remastered_p{p_num:04d}.png"
                        is_listening = p_num >= 31
                        tasks.append((str(raw), str(out), is_listening, is_listening))
                except (ValueError, IndexError):
                    continue

    print(f"Collected {len(tasks)} page remastering tasks across {len(ja_sessions)} Japanese sessions.")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(_process_one_page, tasks, chunksize=10))

    elapsed = time.time() - t0
    remastered_count = sum(1 for r in results if r)
    cached_count = len(results) - remastered_count
    print(f"Done in {elapsed:.1f}s: {remastered_count} remastered, {cached_count} already cached.")


if __name__ == "__main__":
    main()
