#!/usr/bin/env python3
"""EJU Image Remastering & OCR Text Extraction Pipeline.

Optimizes exam booklet imagery by:
1. Whitening scanned paper backgrounds to pure #ffffff and removing noise.
2. Sharpening ink strokes and text contours with unsharp masking.
3. Tightly cropping diagram/table regions to eliminate wasted borders.
4. Extracting reading comprehension text with local GLM-OCR into structured AST paragraphs.
5. Ingesting remastered images into AssetStore (library/media/) and updating published papers.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any
from PIL import Image

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eju_bank.assets import AssetStore
from eju_bank.db import Database
from eju_bank.image_remaster import (
    clean_and_whiten_image,
    crop_and_whiten_figure,
    crop_tight_bbox,
    detect_reading_illustrations,
    remaster_image_file,
    render_table_to_svg,
)
from eju_bank.ocr.glm_ocr_worker import GlmOcrWorker
from eju_bank.util import load_json, write_json


def remaster_session_pages(
    work_dir: Path,
    store: AssetStore,
    ocr_worker: GlmOcrWorker | None = None,
    *,
    ocr_reading_pages: bool = True,
    max_ocr_pages: int = 30,
) -> tuple[dict[int, str], dict[int, dict[str, Any]]]:
    """Process all rendered pages for a work session: remaster images and OCR reading text.

    Returns:
        remastered_page_assets: {page_number: assetId}
        page_ocr_data: {page_number: {"passage_ast": [...], "stem": ..., "options": {...}}}
    """
    remastered_page_assets: dict[int, str] = {}
    page_ocr_data: dict[int, dict[str, Any]] = {}

    render_parent = work_dir / "renders" / "question_booklet"
    if not render_parent.exists():
        return remastered_page_assets, page_ocr_data

    qb_dirs = [d for d in render_parent.iterdir() if d.is_dir()]
    if not qb_dirs:
        return remastered_page_assets, page_ocr_data

    qb_render_dir = qb_dirs[0]
    page_dirs = sorted(
        [d for d in qb_render_dir.iterdir() if d.is_dir() and d.name.startswith("page-")],
        key=lambda d: int(d.name.split("-")[1]),
    )

    remaster_dir = work_dir / "remastered_renders"
    remaster_dir.mkdir(parents=True, exist_ok=True)

    for p_dir in page_dirs:
        try:
            p_num = int(p_dir.name.split("-")[1])
        except (ValueError, IndexError):
            continue

        raw_img_path = p_dir / "full-180dpi.png"
        if not raw_img_path.exists():
            continue

        # 1. Remaster image: Whitening & edge sharpening
        remastered_img_path = remaster_dir / f"remastered_p{p_num:04d}.png"
        if not remastered_img_path.exists():
            # Apply tight crop for listening visual pages (P31+), soft crop for text pages
            is_listening_fig = p_num >= 31
            remaster_image_file(raw_img_path, remastered_img_path, tight_crop=is_listening_fig, strip_header_footer=is_listening_fig)

        # Ingest to AssetStore
        meta = store.put_file(remastered_img_path, mime_type="image/png")
        remastered_page_assets[p_num] = meta["assetId"]

        # 2. Extract illustrations / diagrams for reading comprehension pages (typically P5 to P30)
        fig_assets: list[dict[str, Any]] = []
        if 5 <= p_num <= max_ocr_pages:
            ocr_cache_file = work_dir / "ocr_cache" / f"p{p_num:04d}.json"
            existing_ocr = load_json(ocr_cache_file) if ocr_cache_file.exists() else None
            try:
                fig_boxes = detect_reading_illustrations(raw_img_path, ocr_data=existing_ocr)
                # Remove any stale figures from previous runs
                for stale_fig in remaster_dir.glob(f"remastered_p{p_num:04d}_fig*.png"):
                    stale_fig.unlink(missing_ok=True)

                if fig_boxes:
                    with Image.open(raw_img_path) as im:
                        orig_w, orig_h = im.size
                    for f_idx, box in enumerate(fig_boxes, 1):
                        fig_img_path = remaster_dir / f"remastered_p{p_num:04d}_fig{f_idx:02d}.png"
                        cropped_fig = crop_and_whiten_figure(raw_img_path, box)
                        cropped_fig.save(str(fig_img_path), "PNG", optimize=True)
                        fig_meta = store.put_file(fig_img_path, mime_type="image/png")
                        fig_assets.append({
                            "assetId": fig_meta["assetId"],
                            "sourceBbox": [
                                round(box[0] / orig_w, 4),
                                round(box[1] / orig_h, 4),
                                round(box[2] / orig_w, 4),
                                round(box[3] / orig_h, 4),
                            ],
                            "alt": f"読解 第{p_num}ページ 挿絵図版",
                        })
            except Exception as e:
                print(f"    [WARN] Illustration detection failed for {work_dir.name} p{p_num}: {e}")

        # 3. OCR reading comprehension pages (typically P5 to P30)
        if 5 <= p_num <= max_ocr_pages:
            ocr_cache_file = work_dir / "ocr_cache" / f"p{p_num:04d}.json"
            if ocr_cache_file.exists():
                cached = load_json(ocr_cache_file)
                if fig_assets:
                    cached["figures"] = fig_assets
                    write_json(ocr_cache_file, cached)
                elif "figures" in cached:
                    # Clean up false positive figures recorded in previous runs
                    del cached["figures"]
                    write_json(ocr_cache_file, cached)
                page_ocr_data[p_num] = cached
            elif ocr_reading_pages and ocr_worker:
                try:
                    raw_ocr_text = ocr_worker.transcribe_image(remastered_img_path)
                    parsed = ocr_worker.parse_reading_page(raw_ocr_text)
                    if fig_assets:
                        parsed["figures"] = fig_assets
                    page_ocr_data[p_num] = parsed
                    ocr_cache_file.parent.mkdir(parents=True, exist_ok=True)
                    write_json(ocr_cache_file, parsed)
                except Exception as e:
                    print(f"    [WARN] OCR failed for {work_dir.name} p{p_num}: {e}")

    return remastered_page_assets, page_ocr_data


def main():
    parser = argparse.ArgumentParser(description="Remaster exam images and extract reading passages.")
    parser.add_argument("--session", type=str, help="Specific session name (e.g. 2023-1-japanese)")
    parser.add_argument("--all-japanese", action="store_true", help="Process all Japanese sessions")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of sessions to process")
    parser.add_argument("--device", type=str, default="cuda:2", help="CUDA device for GLM-OCR")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR, only remaster images")
    args = parser.parse_args()

    work_root = PROJECT_ROOT / "work"
    media_dir = PROJECT_ROOT / "library" / "media"
    store = AssetStore(media_dir)

    ocr_worker = None
    if not args.no_ocr:
        print(f"Initializing GLM-OCR Worker on {args.device}...")
        ocr_worker = GlmOcrWorker(device=args.device, cache_dir=PROJECT_ROOT / "library" / "ocr_cache")

    if args.session:
        session_dirs = [work_root / args.session]
    elif args.all_japanese:
        session_dirs = sorted([d for d in work_root.iterdir() if d.is_dir() and "-japanese" in d.name])[: args.limit]
    else:
        # Default: latest Japanese sessions (2023-1, 2023-2, 2024-1)
        target_names = ["2024-1-japanese", "2023-2-japanese", "2023-1-japanese"]
        session_dirs = [work_root / name for name in target_names if (work_root / name).exists()]

    print(f"Target sessions to remaster ({len(session_dirs)}): {[d.name for d in session_dirs]}\n")

    for s_dir in session_dirs:
        print(f"Processing {s_dir.name}...")
        t0 = time.time()
        assets, ocr_data = remaster_session_pages(s_dir, store, ocr_worker)
        elapsed = time.time() - t0
        print(f"  ✓ Remastered {len(assets)} pages, OCR extracted {len(ocr_data)} pages in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
