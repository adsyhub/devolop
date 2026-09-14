#!/usr/bin/env python3
"""Read every 正解表 page a second time, at higher resolution.

What the bank is still missing is now almost entirely answer-key reading, not
joining: measured across the non-mathematics sources, 697 questions sit in
sections where the key yielded fewer 解答欄 than the booklet printed questions,
and another 382 sit in sections the key yielded nothing for. The pairing logic
already confirms what *was* read — one 総合科目 section scored 22 of 22 against
the booklet's own options — so the slots simply were not recognised.

These are dense numeric tables rendered at 180 dpi. A dropped digit there is a
resolution problem, and the failure it causes is visible in the parser's own
complaints ("題号 16 个与答案 15 个不匹配"). So this renders each answer page again
at 400 dpi and transcribes it into ``answer_ocr_hi/`` beside the original.

Nothing overwrites the first reading. Two independent captures of the same page
are worth more than either alone: :func:`eju_bank.ocr.answer_key_contracts.parse_answer_page`
merges them and refuses any 解答欄 the two readings disagree about, so the second
pass can only add slots or withdraw doubtful ones — never quietly replace one
answer with another.

    python scripts/reocr_answer_keys.py            # 所有自带答案册的来源
    python scripts/reocr_answer_keys.py --sessions 2003-1-japanese
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eju_bank.ocr.local_vision import transcribe
from eju_bank.pdf_pipeline import render_manifest
from eju_bank.util import write_json

DEFAULT_URL = "http://127.0.0.1:8102/v1/chat/completions"
DEFAULT_MODEL = "zai-org/GLM-OCR"
TABLE_PROMPT = "Convert the tables on this page to HTML, preserving rowspan and colspan."
TEXT_PROMPT = "Text Recognition:"
DPI = 400


def owns_answer_key(manifest: dict) -> bool:
    """Only the source that actually filed the PDF renders it.

    A session's key is one document registered onto every source of that
    session; transcribing it once per source would repeat the same work up to
    five times for the same bytes.
    """
    return any(f.get("role") == "ANSWER_KEY" and not f.get("registeredFrom")
               for f in manifest.get("files", []))


def page_number(path: Path) -> int:
    digits = "".join(c for c in path.parent.name if c.isdigit())
    return int(digits) if digits else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work-root", type=Path, default=ROOT / "work")
    parser.add_argument("--sessions", nargs="*")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--dpi", type=int, default=DPI)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    dirs = sorted(d for d in args.work_root.iterdir() if d.is_dir())
    if args.sessions:
        dirs = [d for d in dirs if d.name in set(args.sessions)]

    jobs: list[tuple[Path, Path, int]] = []
    for work in dirs:
        manifest_path = work / "source-manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not owns_answer_key(manifest):
            continue
        out_dir = work / "renders_hi"
        try:
            render_manifest(manifest_path, role="ANSWER_KEY", output_dir=out_dir,
                            full_dpi=args.dpi, tile_count=1)
        except Exception as exc:
            print(f"[render] {work.name}: {type(exc).__name__}: {exc}", flush=True)
            continue
        for image in sorted((out_dir / "answer_key").rglob(f"page-*/full-{args.dpi}dpi.png")):
            number = page_number(image)
            target = work / "answer_ocr_hi" / f"p{number:04d}.json"
            if number and (args.force or not target.is_file()):
                jobs.append((image, work, number))

    print(f"来源 {len(dirs)} 个 · 待重读 {len(jobs)} 页 · {args.dpi} dpi · 并发 {args.concurrency}",
          flush=True)
    if not jobs:
        print("没有需要重读的页面。", flush=True)
        return 0

    done = [0]
    failed = [0]
    started = time.time()

    def run(job: tuple[Path, Path, int]) -> None:
        image, work, number = job
        try:
            html = transcribe(image.read_bytes(), prompt=TABLE_PROMPT,
                              url=args.url, model=args.model, timeout=args.timeout)
            flat = transcribe(image.read_bytes(), prompt=TEXT_PROMPT,
                              url=args.url, model=args.model, timeout=args.timeout)
            write_json(work / "answer_ocr_hi" / f"p{number:04d}.json",
                       {"raw_text": html, "raw_flat": flat, "ocrModel": args.model,
                        "ocrPage": number, "ocrDpi": args.dpi, "ocrPrompt": TABLE_PROMPT})
        except Exception as exc:
            failed[0] += 1
            print(f"[fail] {work.name} p{number}: {type(exc).__name__}: {exc}", flush=True)
        done[0] += 1
        if done[0] % 20 == 0 or done[0] == len(jobs):
            rate = done[0] / max(time.time() - started, 0.001)
            print(f"  {done[0]}/{len(jobs)} 页 · {rate:.2f} 页/秒 · 失败 {failed[0]}", flush=True)

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        list(pool.map(run, jobs))

    print(f"完成：{done[0] - failed[0]} 页成功，{failed[0]} 页失败，"
          f"用时 {(time.time() - started) / 60:.1f} 分钟", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
