#!/usr/bin/env python3
"""Read the boxed 解答欄 numbers printed in each booklet page's right margin.

EJU booklets print the answer-sheet number for every objective question in a
small box at the right margin::

    問3  質量Mのおもりにかかる力は…                              ┌──┐
         次の①～⑤のうちから正しいものを一つ選びなさい。          │ 8│
                                                                └──┘

That number is the authoritative join key to the 正解表, and it beats every
alternative: the printed 問N restarts inside each 大題, and the answer key's
nested header is not reliably recoverable from OCR.

A full-page transcription drops these boxes — the document OCR model treats
them as graphics. Cropping the right margin first makes them the only thing on
the image, and then they read cleanly and fast (~0.5s per page).

Writes ``work/<session>/slot_cache/pNNNN.json`` with the numbers in printed
order. Filtering the noise (a stray figure label, an option number that bleeds
into the margin) is left to the consumer, which knows the section boundaries
and can require the run to ascend.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eju_bank.util import write_json

DEFAULT_URL = "http://127.0.0.1:8102/v1/chat/completions"
DEFAULT_MODEL = "zai-org/GLM-OCR"
# Measured against 2002-1-science: the right 22% captures every box, while 15%
# clips them and starts reading option numbers from the body text instead.
MARGIN_FRACTION = 0.78

_print_lock = threading.Lock()


def log(*args: object) -> None:
    with _print_lock:
        print(*args, flush=True)


def read_margin(image: Path, *, url: str, model: str, timeout: int, retries: int = 3) -> str:
    from PIL import Image

    with Image.open(image) as full:
        width, height = full.size
        strip = full.crop((int(width * MARGIN_FRACTION), 0, width, height))
        buffer = io.BytesIO()
        strip.save(buffer, format="PNG")

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {
                "url": "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()}},
            {"type": "text", "text": "Text Recognition:"},
        ]}],
        "max_tokens": 512,
        "temperature": 0.0,
    }).encode()

    last: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, data=payload,
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)["choices"][0]["message"]["content"]
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"margin OCR failed after {retries} attempts: {last}")


def page_number(path: Path) -> int:
    return int(path.parent.name.split("-")[-1])


def pages_for(work_dir: Path) -> list[Path]:
    root = work_dir / "renders" / "question_booklet"
    if not root.exists():
        return []
    return sorted(root.rglob("page-*/full-*dpi.png"), key=page_number)


def cache_path(work_dir: Path, number: int) -> Path:
    return work_dir / "slot_cache" / f"p{number:04d}.json"


def already_done(target: Path) -> bool:
    if not target.is_file():
        return False
    try:
        return "slots" in json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return False


def handle_page(image: Path, work_dir: Path, args: argparse.Namespace) -> None:
    number = page_number(image)
    target = cache_path(work_dir, number)
    if not args.force and already_done(target):
        return
    raw = read_margin(image, url=args.url, model=args.model, timeout=args.timeout)
    # Slot numbers only; a 3-digit run in the margin is a page number, not a slot.
    slots = [int(token) for token in re.findall(r"\d+", raw.replace("\n", " "))
             if 1 <= int(token) <= 120]
    write_json(target, {"slots": slots, "raw": raw.strip(), "ocrModel": args.model,
                        "marginFraction": MARGIN_FRACTION, "ocrPage": number})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, default=PROJECT_ROOT / "work")
    parser.add_argument("--sessions", nargs="*")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    dirs = sorted(d for d in args.work_root.iterdir() if d.is_dir())
    if args.sessions:
        wanted = set(args.sessions)
        dirs = [d for d in dirs if d.name in wanted]

    jobs = [(image, work_dir) for work_dir in dirs for image in pages_for(work_dir)]
    todo = [j for j in jobs if args.force or not already_done(cache_path(j[1], page_number(j[0])))]
    log(f"来源 {len(dirs)} 个 · 页面 {len(jobs)} 张 · 待读取 {len(todo)} 张 · 并发 {args.concurrency}")
    if not todo:
        log("没有需要读取的页面。")
        return 0

    started = time.time()
    done = failed = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(handle_page, image, wd, args): (image, wd) for image, wd in todo}
        for future in as_completed(futures):
            image, work_dir = futures[future]
            try:
                future.result()
            except Exception as exc:
                failed += 1
                log(f"  [FAIL] {work_dir.name}/p{page_number(image):04d}: {exc}")
            done += 1
            if done % 100 == 0 or done == len(todo):
                rate = done / max(time.time() - started, 1e-9)
                log(f"  {done}/{len(todo)} 页 · {rate:.2f} 页/秒 · 失败 {failed} · "
                    f"预计剩余 {(len(todo) - done) / max(rate, 1e-9) / 60:.0f} 分钟")

    log(f"完成：{done - failed} 页成功，{failed} 页失败，用时 {(time.time()-started)/60:.1f} 分钟")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
