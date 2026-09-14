#!/usr/bin/env python3
"""Run real OCR over rendered EJU booklet and answer-key pages.

Talks to a running OpenAI-compatible vision server (GLM-OCR by default) instead of
loading a second copy of the model in-process, and writes one cache file per page:

    work/<session>/ocr_cache/pNNNN.json     question booklet, parsed
    work/<session>/answer_ocr/pNNNN.json    answer key, raw text only

Question-booklet pages are parsed with the project's own
``GlmOcrWorker.parse_reading_page`` so the cache stays byte-compatible with what
``build_and_publish_all.py`` already reads. Answer-key pages are kept as raw text;
turning them into verified answers is a separate, auditable step.

Resumable: a page that already has a non-empty cache entry is skipped.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eju_bank.ocr.glm_ocr_worker import GlmOcrWorker
from eju_bank.util import write_json

DEFAULT_URL = "http://127.0.0.1:8102/v1/chat/completions"
DEFAULT_MODEL = "zai-org/GLM-OCR"

_parser = GlmOcrWorker.__new__(GlmOcrWorker)  # parse_reading_page needs no loaded model
_print_lock = threading.Lock()


def log(*args: Any) -> None:
    with _print_lock:
        print(*args, flush=True)


# 题册要纯文本；答案表要结构。正解表用合并单元格表达「一问占几个解答欄」
# （<td colspan="2">A</td>），压成纯文本后这个信息就没了，題号与解答欄再也对不上。
PROMPTS = {
    "question_booklet": "Text Recognition:",
    "answer_key": "Convert the tables on this page to HTML, preserving rowspan and colspan.",
}


def transcribe(image: Path, *, url: str, model: str, timeout: int,
               prompt: str = "Text Recognition:", retries: int = 3) -> str:
    """One page through the vision server. Retries transient failures."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode()}},
            {"type": "text", "text": prompt},
        ]}],
        "max_tokens": 4096,
        "temperature": 0.0,
    }).encode()
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.load(response)["choices"][0]["message"]["content"]
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"OCR failed after {retries} attempts: {last}")


def page_number(path: Path) -> int:
    return int(path.parent.name.split("-")[-1])


def pages_for(work_dir: Path, role: str) -> list[Path]:
    root = work_dir / "renders" / role
    if not root.exists():
        return []
    return sorted(root.rglob("page-*/full-*dpi.png"), key=page_number)


def cache_path(work_dir: Path, role: str, number: int) -> Path:
    folder = "ocr_cache" if role == "question_booklet" else "answer_ocr"
    return work_dir / folder / f"p{number:04d}.json"


def already_done(target: Path, role: str) -> bool:
    if not target.is_file():
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return False
    if role == "question_booklet":
        # An entry with neither passage nor stem nor options carries nothing; redo it.
        return bool(data.get("raw_passage") or data.get("stem") or data.get("options"))
    # An answer key needs both readings; one captured with an older prompt lacks
    # the table structure and must be redone.
    return (bool(data.get("raw_text")) and bool(data.get("raw_flat"))
            and data.get("ocrPrompt") == PROMPTS["answer_key"])


def handle_page(image: Path, work_dir: Path, role: str, args: argparse.Namespace) -> str:
    number = page_number(image)
    target = cache_path(work_dir, role, number)
    if not args.force and already_done(target, role):
        return "skip"
    raw = transcribe(image, url=args.url, model=args.model, timeout=args.timeout,
                     prompt=PROMPTS.get(role, "Text Recognition:"))
    if role == "question_booklet":
        parsed = _parser.parse_reading_page(raw)
        parsed["raw_text"] = raw
        parsed["ocrModel"] = args.model
        parsed["ocrPage"] = number
        # Keep figures recorded by the remaster pipeline; only text is refreshed here.
        if target.is_file():
            try:
                previous = json.loads(target.read_text(encoding="utf-8"))
                if "figures" in previous:
                    parsed["figures"] = previous["figures"]
            except Exception:
                pass
        write_json(target, parsed)
    else:
        # 两种读法互补，都保留：HTML 保住嵌套的解答欄结构（一问占几欄），
        # 纯文本保住落在 <table> 标记之外的小节标题（聴解 / 読解 …）。
        flat = transcribe(image, url=args.url, model=args.model, timeout=args.timeout,
                          prompt=PROMPTS["question_booklet"])
        write_json(target, {"raw_text": raw, "raw_flat": flat,
                            "ocrModel": args.model, "ocrPage": number,
                            "ocrPrompt": PROMPTS["answer_key"]})
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, default=PROJECT_ROOT / "work")
    parser.add_argument("--sessions", nargs="*", help="work 目录名，留空表示全部")
    parser.add_argument("--roles", nargs="*", default=["question_booklet", "answer_key"])
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--concurrency", type=int, default=2, help="vLLM 的 max-num-seqs 通常是 2")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--limit-pages", type=int, default=0, help="每个来源最多处理多少页，0 表示不限")
    parser.add_argument("--force", action="store_true", help="忽略已有缓存重新识别")
    args = parser.parse_args()

    dirs = sorted(d for d in args.work_root.iterdir() if d.is_dir())
    if args.sessions:
        wanted = set(args.sessions)
        dirs = [d for d in dirs if d.name in wanted]

    jobs: list[tuple[Path, Path, str]] = []
    for work_dir in dirs:
        for role in args.roles:
            found = pages_for(work_dir, role)
            if args.limit_pages:
                found = found[: args.limit_pages]
            jobs.extend((image, work_dir, role) for image in found)

    todo = [j for j in jobs if args.force or not already_done(cache_path(j[1], j[2], page_number(j[0])), j[2])]
    log(f"来源 {len(dirs)} 个 · 页面 {len(jobs)} 张 · 待识别 {len(todo)} 张 · 并发 {args.concurrency}")
    if not todo:
        log("没有需要识别的页面。")
        return 0

    started = time.time()
    done = failed = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(handle_page, image, wd, role, args): (image, wd, role)
                   for image, wd, role in todo}
        for future in as_completed(futures):
            image, work_dir, role = futures[future]
            try:
                future.result()
            except Exception as exc:
                failed += 1
                log(f"  [FAIL] {work_dir.name}/{role}/p{page_number(image):04d}: {exc}")
            done += 1
            if done % 25 == 0 or done == len(todo):
                rate = done / max(time.time() - started, 1e-9)
                remaining = (len(todo) - done) / max(rate, 1e-9)
                log(f"  {done}/{len(todo)} 页 · {rate:.2f} 页/秒 · 失败 {failed} · 预计剩余 {remaining/60:.0f} 分钟")

    log(f"完成：{done - failed} 页成功，{failed} 页失败，用时 {(time.time()-started)/60:.1f} 分钟")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
