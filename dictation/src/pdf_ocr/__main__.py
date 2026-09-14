"""CLI: scanned PDF -> Markdown + JSON, using a local vision model.

    python -m pdf_ocr probe  "book.pdf"
    python -m pdf_ocr run    "book.pdf" -o out/book --pages 1-20
    python -m pdf_ocr run    "book.pdf" -o out/book --retry-flagged

Every page is cached to ``<out>/pages/page-NNNN.json`` the moment it finishes, so
a run killed halfway resumes where it stopped instead of paying for those pages
again.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Allow `python src/pdf_ocr/__main__.py` as well as `python -m pdf_ocr`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "pdf_ocr"

from pdf_ocr.assemble import (
    BLANK_MARKER,
    NO_BOX_MARKER,
    _strip_control_tokens,
    box_is_degenerate,
    write_outputs,
)
from pdf_ocr.backends import BACKENDS, DEFAULT_PROMPT_STYLE, load_backend
from pdf_ocr.backends.base import PageResult
from pdf_ocr.prompts import prompt_for
from pdf_ocr.render import crop_column, extract_page_text_layer, pdf_summary, render_pdf


def parse_pages(spec: str | None, total: int) -> list[int] | None:
    """'1-20', '3', '1,4,9-12' -> sorted 1-based page numbers. None = all."""
    if not spec or spec == "all":
        return None
    wanted: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            wanted.update(range(int(lo), int(hi) + 1))
        else:
            wanted.add(int(part))
    return sorted(n for n in wanted if 1 <= n <= total)


def _cache_path(out_dir: Path, page: int) -> Path:
    return out_dir / "pages" / f"page-{page:04d}.json"


def load_cached(out_dir: Path, page: int) -> PageResult | None:
    path = _cache_path(out_dir, page)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return PageResult(
        page=data["page"],
        markdown=data.get("markdown", ""),
        blocks=data.get("blocks", []),
        seconds=data.get("seconds", 0.0),
        error=data.get("error"),
        backend=data.get("backend") if isinstance(data.get("backend"), dict) else {},
    )


def save_cached(out_dir: Path, result: PageResult) -> None:
    path = _cache_path(out_dir, result.page)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "page": result.page,
                "markdown": result.markdown,
                "blocks": result.blocks,
                "seconds": result.seconds,
                "error": result.error,
                "backend": result.backend,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _box_path(out_dir: Path, page: int) -> Path:
    return out_dir / "boxes" / f"page-{page:04d}.json"


def load_box(out_dir: Path, page: int) -> str | None:
    """Read one cached box crop, without the model's reasoning scaffolding.

    Stripping here rather than at merge time covers the caches already on disk
    and every consumer at once -- merge_box, box_is_degenerate and
    box_is_suspicious all judge the box by its text. Left raw, a crop whose real
    answer is ``<!-- no box -->`` no longer equals NO_BOX_MARKER once a reasoning
    model wraps it, so an empty crop gets appended to the page as if it were a
    connection chart, and the degeneracy checks score English prose instead of
    the chart they were written for.
    """
    path = _box_path(out_dir, page)
    if not path.exists():
        return None
    try:
        box = json.loads(path.read_text(encoding="utf-8")).get("box")
    except json.JSONDecodeError:
        return None
    return _strip_control_tokens(box).strip() if isinstance(box, str) else box


def load_all_boxes(out_dir: Path, total: int) -> dict[int, str]:
    found = {}
    for number in range(1, total + 1):
        box = load_box(out_dir, number)
        if box is not None:
            found[number] = box
    return found


def save_box(out_dir: Path, page: int, box: str, seconds: float, note: str | None) -> None:
    path = _box_path(out_dir, page)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"page": page, "box": box, "seconds": round(seconds, 2), "note": note},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _load_selected_backend(args: argparse.Namespace):
    """Translate shared CLI flags into one lazily loaded OCR backend."""
    if args.backend == "ollama":
        kwargs = {"max_new_tokens": args.max_new_tokens}
        if getattr(args, "ollama_host", None):
            kwargs["host"] = args.ollama_host
    elif args.backend == "openai-vlm":
        kwargs = {
            "max_new_tokens": args.max_new_tokens,
            "timeout": args.server_timeout,
            "repetition_penalty": getattr(args, "repetition_penalty", 1.0),
        }
        if args.server_base_url:
            kwargs["base_url"] = args.server_base_url
        if args.server_api_key_env:
            kwargs["api_key_env"] = args.server_api_key_env
    else:
        kwargs = {
            "device": args.device,
            "max_new_tokens": args.max_new_tokens,
            "repetition_penalty": getattr(args, "repetition_penalty", 1.0),
        }
        if args.backend == "qwen-vl" and getattr(args, "max_pixels", None) is not None:
            kwargs["max_pixels"] = args.max_pixels
    if args.model:
        kwargs["model_id"] = args.model
    return load_backend(args.backend, **kwargs)


def cmd_boxes(args: argparse.Namespace) -> int:
    """Second pass: re-read the right-hand strip at native resolution.

    Whole-page OCR has to downscale to fit the visual-token budget, and the
    floated grammar-connection panels are the first thing to become illegible --
    they get dropped silently. Cropping the strip keeps them at full scan
    resolution for the same cost.
    """
    from PIL import Image

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"No such PDF: {pdf_path}")
    out_dir = Path(args.out)
    images_dir = out_dir / "images"
    if not images_dir.exists():
        raise SystemExit(f"No page images in {images_dir}. Run `pdf_ocr run` first.")

    summary = pdf_summary(pdf_path)
    pages = parse_pages(args.pages, summary["pages"])
    crops = crop_column(images_dir, out_dir / "crops", fraction=args.fraction, pages=pages)
    print(f"{len(crops)} crop(s) at {args.fraction:.0%} width in {out_dir / 'crops'}", flush=True)

    todo = [c for c in crops if load_box(out_dir, c.number) is None]
    print(f"  {len(crops) - len(todo)} cached, {len(todo)} to read", flush=True)
    if not todo:
        return 0

    # A crop with no ink cannot hold a box. Asking the model anyway invites it to
    # invent one -- on the blank page of this book it produced a conjugation table
    # out of nothing. Cheaper and safer to answer that case ourselves.
    import numpy as np

    blank = []
    for crop in list(todo):
        with Image.open(crop.path) as img:
            ink = (np.array(img.convert("L")) < 160).mean()
        if ink < args.min_ink:
            save_box(out_dir, crop.number, NO_BOX_MARKER, 0.0, f"blank crop (ink={ink:.5f})")
            todo.remove(crop)
            blank.append(crop.number)
    if blank:
        print(f"  {len(blank)} blank crop(s) answered without the model: {blank}", flush=True)

    backend = _load_selected_backend(args)
    print(f"  {json.dumps(backend.describe(), ensure_ascii=False)}", flush=True)
    prompt = prompt_for("box")

    started = time.perf_counter()
    for position, crop in enumerate(todo, 1):
        result = backend.transcribe(crop.path, prompt=prompt)
        note = result.error
        if box_is_degenerate(result.markdown):
            # Greedy decoding latched onto the bracket glyph. Nudging the penalty
            # changes the tie-break; retrying unchanged would loop identically.
            original_penalty = getattr(backend, "repetition_penalty", 1.0)
            backend.repetition_penalty = args.retry_penalty
            retry = backend.transcribe(crop.path, prompt=prompt)
            backend.repetition_penalty = original_penalty
            if not box_is_degenerate(retry.markdown):
                note = f"recovered by repetition_penalty={args.retry_penalty}"
                result = retry
            else:
                note = "degenerate after retry; not merged"
        save_box(out_dir, crop.number, result.markdown, result.seconds, note)
        elapsed = time.perf_counter() - started
        remaining = (elapsed / position) * (len(todo) - position)
        got = "no box" if NO_BOX_MARKER in result.markdown else f"{len(result.markdown)} chars"
        print(
            f"  [{position}/{len(todo)}] p{crop.number:>4} {got:>12} "
            f"{result.seconds:>5.1f}s | eta {remaining / 60:.1f}m",
            flush=True,
        )
    print("\nDone. Re-run `pdf_ocr run ...` to merge them into document.md/json.")
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    print(json.dumps(pdf_summary(Path(args.pdf)), ensure_ascii=False, indent=2))
    return 0


def _flagged_pages(out_dir: Path) -> list[int]:
    report = out_dir / "quality-report.json"
    if not report.exists():
        return []
    return json.loads(report.read_text(encoding="utf-8")).get("flagged_pages", [])


def cmd_run(args: argparse.Namespace) -> int:
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"No such PDF: {pdf_path}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = pdf_summary(pdf_path)
    pages = parse_pages(args.pages, summary["pages"])

    if summary["has_text_layer"] and not args.force:
        print(
            f"PDF has embedded text layer ({summary['text_layer_chars_sampled']} chars sampled). "
            f"Extracting text layer directly with coordinates...",
            flush=True,
        )
        import pymupdf
        doc = pymupdf.open(pdf_path)
        pages_to_extract = pages or list(range(1, summary["pages"] + 1))
        for p_num in pages_to_extract:
            if load_cached(out_dir, p_num) is None:
                text, blocks = extract_page_text_layer(doc, p_num - 1)
                res = PageResult(
                    page=p_num,
                    markdown=text if text else (BLANK_MARKER if len(text) == 0 else ""),
                    blocks=blocks,
                    seconds=0.01,
                    backend={"name": "text-layer", "model": "embedded-pdf-text"},
                )
                save_cached(out_dir, res)
        doc.close()

    if args.retry_flagged:
        flagged = _flagged_pages(out_dir)
        if not flagged:
            print("No flagged pages to retry.")
            return 0
        pages = flagged
        cand_dir = out_dir / "candidates"
        cand_dir.mkdir(exist_ok=True)
        for page in flagged:
            old_res = load_cached(out_dir, page)
            if old_res:
                save_cached(cand_dir, old_res)
            _cache_path(out_dir, page).unlink(missing_ok=True)
        print(f"Retrying {len(flagged)} flagged page(s): {flagged}")

    print(f"Rendering {pdf_path.name} ({summary['pages']} pages) ...", flush=True)
    rendered = render_pdf(
        pdf_path,
        out_dir / "images",
        dpi=args.dpi,
        pages=pages,
        max_edge=args.max_edge,
        grayscale=args.grayscale,
    )
    print(f"  {len(rendered)} page image(s) ready in {out_dir / 'images'}", flush=True)

    todo = [p for p in rendered if load_cached(out_dir, p.number) is None]
    print(f"  {len(rendered) - len(todo)} cached, {len(todo)} to transcribe", flush=True)

    backend = None
    if todo:
        print(
            f"Loading backend {args.backend} ({args.model or 'default model'}) ...",
            flush=True,
        )
        backend = _load_selected_backend(args)
        print(f"  {json.dumps(backend.describe(), ensure_ascii=False)}", flush=True)

    style = args.prompt or DEFAULT_PROMPT_STYLE.get(args.backend, "doc")
    prompt = prompt_for(style)

    started = time.perf_counter()
    done = 0
    for offset in range(0, len(todo), args.batch_size):
        chunk = todo[offset : offset + args.batch_size]
        results = backend.transcribe_batch([p.path for p in chunk], prompt=prompt)
        for result in results:
            result.backend = backend.describe()
            cand_path = _cache_path(out_dir / "candidates", result.page)
            if cand_path.exists():
                prev_res = load_cached(out_dir / "candidates", result.page)
                if prev_res and not prev_res.error and result.error:
                    print(f"  [candidate-retention] p{result.page} new attempt errored; keeping previous candidate", flush=True)
                    result = prev_res
                elif prev_res and len(result.markdown.strip()) == 0 and len(prev_res.markdown.strip()) > 0:
                    print(f"  [candidate-retention] p{result.page} new attempt empty; keeping previous candidate", flush=True)
                    result = prev_res
            save_cached(out_dir, result)
            done += 1
            elapsed = time.perf_counter() - started
            remaining = (elapsed / done) * (len(todo) - done)
            status = "ok " if result.ok else "ERR"
            print(
                f"  [{done}/{len(todo)}] p{result.page:>4} {status} "
                f"{len(result.markdown):>5} chars {result.seconds:>5.1f}s "
                f"| eta {remaining / 60:.1f}m",
                flush=True,
            )
            if result.error:
                print(f"        {result.error}", file=sys.stderr, flush=True)

    # Assemble from every page cached in this output directory, not just the ones
    # this invocation touched. --retry-flagged and --pages both narrow `rendered`
    # to a handful of pages; assembling from that would overwrite a finished
    # document.md with only the pages that were just redone.
    results = [
        r
        for number in range(1, summary["pages"] + 1)
        if (r := load_cached(out_dir, number)) is not None
    ]
    observed_backends: list[dict] = []
    for result in results:
        if result.backend and result.backend not in observed_backends:
            observed_backends.append(result.backend)
    if len(observed_backends) > 1:
        backend_summary = {"backend": "mixed", "members": observed_backends}
    elif observed_backends:
        backend_summary = observed_backends[0]
    elif backend:
        backend_summary = backend.describe()
    else:
        backend_summary = {"backend": args.backend, "note": "all pages served from legacy cache"}

    report = write_outputs(
        out_dir,
        results,
        source=summary,
        backend=backend_summary,
        drop_running_heads=args.drop_running_heads,
        mark_ruby=args.mark_ruby_lines,
        boxes=load_all_boxes(out_dir, summary["pages"]),
    )

    print(
        f"\nDone. {report['pages_transcribed']} pages, {report['total_chars']} chars, "
        f"{report['total_seconds']}s model time."
    )
    if report["flagged_pages"]:
        # Page-level and box-level flags need different fixes. Suggesting
        # --retry-flagged for a box problem would re-OCR body text that is fine
        # and leave the box exactly as it was.
        by_flag: dict[str, list[int]] = {}
        for row in report["pages"]:
            for flag in row["flags"]:
                by_flag.setdefault(flag, []).append(row["page"])
        print(f"Flagged {len(report['flagged_pages'])} page(s):")
        for flag, numbers in sorted(by_flag.items()):
            print(f"  {flag}: {numbers}")
        page_level = [f for f in by_flag if not f.startswith("box-")]
        if page_level:
            print(f"  Re-OCR those pages: python -m pdf_ocr run <pdf> -o {out_dir} --retry-flagged")
        if any(f.startswith("box-") for f in by_flag):
            print(
                f"  Box flags are about the side-panel pass, not the body text. "
                f"Delete those {out_dir / 'boxes'}/page-NNNN.json and re-run "
                f"`pdf_ocr boxes`; a degenerate box is already excluded from document.md."
            )
    print(
        f"  {out_dir / 'document.md'}\n"
        f"  {out_dir / 'document.json'}\n"
        f"  {out_dir / 'quality-report.json'}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf_ocr",
        description=(
            "Turn a scanned PDF into LLM-editable Markdown + JSON with a local vision model."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser(
        "probe", help="Report page count, metadata and whether a text layer exists."
    )
    probe.add_argument("pdf")
    probe.set_defaults(func=cmd_probe)

    run = sub.add_parser("run", help="Render, transcribe and assemble.")
    run.add_argument("pdf")
    run.add_argument("-o", "--out", required=True, help="Output directory.")
    run.add_argument("--backend", default="qwen-vl", choices=sorted(BACKENDS))
    run.add_argument("--model", default=None, help="Override the backend default model id.")
    run.add_argument("--pages", default=None, help="e.g. 1-20 or 1,4,9-12. Default: all.")
    run.add_argument("--device", default="cuda")
    run.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Raster DPI when a page is not a single embedded image.",
    )
    run.add_argument(
        "--max-edge", type=int, default=None, help="Downscale page images to this longest edge."
    )
    run.add_argument("--grayscale", action="store_true", help="Render pages as grayscale.")
    run.add_argument(
        "--max-pixels",
        type=int,
        default=None,
        help=(
            "Visual-token budget per page (qwen-vl); pixels/784 = tokens. "
            "Default 3211264 is the most a 24 GB card fits -- raising it makes "
            "furigana legible but spills to system RAM and is ~7x slower."
        ),
    )
    run.add_argument("--max-new-tokens", type=int, default=3072)
    run.add_argument(
        "--repetition-penalty",
        type=float,
        default=1.0,
        help=(
            "Decoding is greedy, so a plain --retry-flagged reproduces a loop "
            "exactly. Nudge this to ~1.05 on a retry to break out of one. Keep it "
            "at 1.0 otherwise: Japanese repeats particles legitimately."
        ),
    )
    run.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Pages decoded together (qwen-vl). 4 is roughly 3x faster on a 24 GB card.",
    )
    run.add_argument(
        "--prompt", default=None, help="Prompt style ('doc', 'layout') or a literal prompt."
    )
    run.add_argument(
        "--drop-running-heads",
        action="store_true",
        help="Strip header/footer comments from document.md.",
    )
    run.add_argument(
        "--mark-ruby-lines",
        action="store_true",
        help=(
            "Wrap stranded furigana lines (a kana-only line under a line with kanji) "
            "in <!-- ruby: ... --> so readers can skip them. Nothing is deleted."
        ),
    )
    run.add_argument(
        "--retry-flagged",
        action="store_true",
        help="Re-OCR only the pages the last report flagged.",
    )
    run.add_argument(
        "--force", action="store_true", help="OCR even if the PDF already has a text layer."
    )
    run.add_argument("--ollama-host", default=None)
    run.add_argument(
        "--server-base-url",
        default=None,
        help="OpenAI-compatible VLM base URL, e.g. http://127.0.0.1:8102/v1.",
    )
    run.add_argument(
        "--server-api-key-env",
        default=None,
        help="NAME of the API-key environment variable for --backend openai-vlm.",
    )
    run.add_argument("--server-timeout", type=int, default=600)
    run.set_defaults(func=cmd_run)

    boxes = sub.add_parser(
        "boxes",
        help="Second pass: re-read the right-hand strip at native resolution to "
        "recover the grammar-connection panels whole-page OCR drops.",
    )
    boxes.add_argument("pdf")
    boxes.add_argument("-o", "--out", required=True, help="The same output directory as `run`.")
    boxes.add_argument("--pages", default=None, help="e.g. 1-20 or 1,4,9-12. Default: all.")
    boxes.add_argument(
        "--fraction",
        type=float,
        default=0.5,
        help="Fraction of page width to keep, from the right edge (default 0.5 = 3.07 MP).",
    )
    boxes.add_argument(
        "--min-ink",
        type=float,
        default=0.002,
        help="Crops with less ink than this are answered '<!-- no box -->' without "
        "asking the model, which would otherwise invent a panel.",
    )
    boxes.add_argument("--device", default="cuda")
    boxes.add_argument("--backend", default="qwen-vl", choices=sorted(BACKENDS))
    boxes.add_argument("--model", default=None)
    boxes.add_argument("--max-pixels", type=int, default=3_211_264)
    boxes.add_argument("--max-new-tokens", type=int, default=768)
    boxes.add_argument("--ollama-host", default=None)
    boxes.add_argument("--server-base-url", default=None)
    boxes.add_argument("--server-api-key-env", default=None)
    boxes.add_argument("--server-timeout", type=int, default=600)
    boxes.add_argument(
        "--retry-penalty",
        type=float,
        default=1.15,
        help="Repetition penalty used only to retry a box read that looped.",
    )
    boxes.set_defaults(func=cmd_boxes)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
