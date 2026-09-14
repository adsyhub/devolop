"""Read source pages with a local OpenAI-compatible vision server.

Talks to a model already serving on the loopback interface rather than loading a
second copy in-process, so the workbench does not fight the running server for
GPU memory. Everything is resumable: a page whose cache entry already carries a
reading is skipped, so a cancelled job resumes where it stopped.

Two readings are taken, because each captures something the other loses:

* the booklet page as plain text — the questions and their options;
* the answer key page as HTML *and* as plain text. The HTML keeps the merged
  header cells, which is the only place that records how many 解答欄 a single
  question owns; the plain text keeps section headings that are printed outside
  the table markup.

A third pass reads the boxed 解答欄 number from each booklet page's right
margin. A whole-page transcription drops those boxes — the OCR model treats them
as graphics — so the margin is cropped first, which makes them the only thing on
the image.
"""

from __future__ import annotations

import base64
import io
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from ..util import sha256_file, write_json

DEFAULT_URL = "http://127.0.0.1:8102/v1/chat/completions"
DEFAULT_MODEL = "zai-org/GLM-OCR"

PROMPTS = {
    "text": "Text Recognition:",
    "tables": "Convert the tables on this page to HTML, preserving rowspan and colspan.",
}
# Measured against a 2002 science booklet: the right 22% captures every box,
# while 15% clips them and starts reading option numbers from the body instead.
MARGIN_FRACTION = 0.78

_ROLE_FOLDER = {"question_booklet": "ocr_cache", "answer_key": "answer_ocr"}


class Cancelled(Exception):
    """Raised when the caller asks the run to stop."""


def _post(payload: bytes, url: str, timeout: int, retries: int) -> str:
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
    raise RuntimeError(f"vision server did not answer after {retries} attempts: {last}")


def transcribe(image_bytes: bytes, *, prompt: str, url: str, model: str,
               timeout: int = 300, retries: int = 3) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {
                "url": "data:image/png;base64," + base64.b64encode(image_bytes).decode()}},
            {"type": "text", "text": prompt},
        ]}],
        "max_tokens": 4096,
        "temperature": 0.0,
    }).encode()
    return _post(payload, url, timeout, retries)


def page_number(path: Path) -> int:
    return int(path.parent.name.split("-")[-1])


def rendered_pages(work_dir: Path, role: str) -> list[Path]:
    root = work_dir / "renders" / role
    if not root.exists():
        return []
    return sorted(root.rglob("page-*/full-*dpi.png"), key=page_number)


def _cache(work_dir: Path, role: str, number: int) -> Path:
    return work_dir / _ROLE_FOLDER[role] / f"p{number:04d}.json"


def cache_identity(image: Path, model: str, role: str) -> dict[str, str]:
    """这份缓存是"用哪个模型、哪段提示词、读哪张图"得到的。

    原来复用缓存只问"文件在不在、字段齐不齐"。于是换了模型、改了提示词、重新
    渲染过原页，旧缓存照样被当成本次的结果用——而它是另一次运行的产物
    （规范 §9.4：模型/提示词/关键参数变更产生新候选产物，不静默使用旧缓存）。
    """
    from ..util import digest_json

    prompts = [PROMPTS["text"]] + ([PROMPTS["tables"]] if role == "answer_key" else [])
    return {"ocrModel": model, "promptDigest": digest_json(prompts),
            "imageSha256": sha256_file(image)}


def _identity_matches(data: dict, expected: dict) -> bool:
    """缓存的来历与本次一致吗？

    没有记来历的旧缓存按"来历不明"处理并照常复用：它们是这套机制之前留下的，
    把它们一律作废等于让整库重跑一遍 OCR，而那不是这条改动要解决的问题。来历
    记下来了、而且和本次不一样的，才重读。
    """
    recorded = {k: data.get(k) for k in ("ocrModel", "promptDigest", "imageSha256")}
    if not any(recorded.values()):
        return True
    return all(recorded[k] == expected[k] for k in expected if recorded.get(k) is not None)


def _has_reading(target: Path, role: str, expected: dict | None = None) -> bool:
    if not target.is_file():
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return False
    if expected is not None and not _identity_matches(data, expected):
        return False
    if role == "question_booklet":
        return bool(data.get("raw_passage") or data.get("stem") or data.get("options")
                    or data.get("raw_text"))
    # The answer key needs both readings; one captured without the table prompt
    # has lost the merged-cell structure and must be redone.
    return bool(data.get("raw_text")) and bool(data.get("raw_flat"))


def _read_booklet_page(image: Path, work_dir: Path, url: str, model: str, timeout: int) -> None:
    from .glm_ocr_worker import GlmOcrWorker

    number = page_number(image)
    raw = transcribe(image.read_bytes(), prompt=PROMPTS["text"], url=url, model=model, timeout=timeout)
    parsed = GlmOcrWorker.parse_reading_page(GlmOcrWorker.__new__(GlmOcrWorker), raw)
    parsed.update({"raw_text": raw, "ocrModel": model, "ocrPage": number,
                   **cache_identity(image, model, "question_booklet")})
    target = _cache(work_dir, "question_booklet", number)
    if target.is_file():
        # Figures recorded by the remaster pipeline are not ours to discard.
        try:
            previous = json.loads(target.read_text(encoding="utf-8"))
            if "figures" in previous:
                parsed["figures"] = previous["figures"]
        except Exception:
            pass
    write_json(target, parsed)


def _read_answer_page(image: Path, work_dir: Path, url: str, model: str, timeout: int) -> None:
    number = page_number(image)
    data = image.read_bytes()
    html = transcribe(data, prompt=PROMPTS["tables"], url=url, model=model, timeout=timeout)
    flat = transcribe(data, prompt=PROMPTS["text"], url=url, model=model, timeout=timeout)
    write_json(_cache(work_dir, "answer_key", number),
               {"raw_text": html, "raw_flat": flat, "ocrModel": model,
                "ocrPage": number, "ocrPrompt": PROMPTS["tables"],
                **cache_identity(image, model, "answer_key")})


def _run(jobs: list[Callable[[], None]], *, concurrency: int,
         cancelled: Callable[[], bool] | None,
         on_progress: Callable[[int, int, int], None] | None) -> dict[str, Any]:
    total = len(jobs)
    done = failed = 0
    errors: list[str] = []
    if not total:
        if on_progress:
            on_progress(0, 0, 0)
        return {"pages": 0, "completed": 0, "failed": 0, "errors": []}

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = [pool.submit(job) for job in jobs]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                failed += 1
                if len(errors) < 20:
                    errors.append(str(exc)[:300])
            done += 1
            if on_progress:
                on_progress(done, total, failed)
            if cancelled and cancelled():
                for pending in futures:
                    pending.cancel()
                raise Cancelled(f"cancelled after {done}/{total} pages")
    return {"pages": total, "completed": done - failed, "failed": failed, "errors": errors}


def ocr_source_pages(
    work_dir: Path, *, roles: list[str] | None = None, url: str | None = None,
    model: str | None = None, force: bool = False, concurrency: int = 2,
    timeout: int = 300, cancelled: Callable[[], bool] | None = None,
    on_progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, Any]:
    """Transcribe one source's rendered pages into the OCR caches."""
    url = url or DEFAULT_URL
    model = model or DEFAULT_MODEL
    roles = roles or ["question_booklet", "answer_key"]
    jobs: list[Callable[[], None]] = []
    for role in roles:
        if role not in _ROLE_FOLDER:
            continue
        for image in rendered_pages(work_dir, role):
            expected = cache_identity(image, model, role)
            if not force and _has_reading(_cache(work_dir, role, page_number(image)),
                                          role, expected):
                continue
            reader = _read_booklet_page if role == "question_booklet" else _read_answer_page
            jobs.append(lambda image=image, reader=reader: reader(image, work_dir, url, model, timeout))
    return _run(jobs, concurrency=concurrency, cancelled=cancelled, on_progress=on_progress)


def _read_margin(image: Path, work_dir: Path, url: str, model: str, timeout: int) -> None:
    from PIL import Image

    number = page_number(image)
    with Image.open(image) as full:
        width, height = full.size
        strip = full.crop((int(width * MARGIN_FRACTION), 0, width, height))
        buffer = io.BytesIO()
        strip.save(buffer, format="PNG")
    raw = transcribe(buffer.getvalue(), prompt=PROMPTS["text"], url=url, model=model, timeout=timeout)
    slots = [int(token) for token in re.findall(r"\d+", raw.replace("\n", " "))
             if 1 <= int(token) <= 120]
    write_json(work_dir / "slot_cache" / f"p{number:04d}.json",
               {"slots": slots, "raw": raw.strip(), "ocrModel": model,
                "marginFraction": MARGIN_FRACTION, "ocrPage": number})


def _has_slots(target: Path) -> bool:
    if not target.is_file():
        return False
    try:
        return "slots" in json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return False


def ocr_source_slots(
    work_dir: Path, *, url: str | None = None, model: str | None = None,
    force: bool = False, concurrency: int = 2, timeout: int = 180,
    cancelled: Callable[[], bool] | None = None,
    on_progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, Any]:
    """Read the boxed 解答欄 numbers from each booklet page's right margin."""
    url = url or DEFAULT_URL
    model = model or DEFAULT_MODEL
    jobs = [
        (lambda image=image: _read_margin(image, work_dir, url, model, timeout))
        for image in rendered_pages(work_dir, "question_booklet")
        if force or not _has_slots(work_dir / "slot_cache" / f"p{page_number(image):04d}.json")
    ]
    return _run(jobs, concurrency=concurrency, cancelled=cancelled, on_progress=on_progress)
