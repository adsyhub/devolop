"""Image remastering and adaptive visual enhancement for EJU exam scans.

Provides:
1. Adaptive background normalization (removes yellow cast, scanner noise, uneven illumination).
2. Ink contrast stretching and edge sharpening (unsharp masking).
3. Tight visual bounding box detection and cropping (eliminates blank margins).
4. Responsive vector SVG generation for tabular materials and diagrams.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def clean_and_whiten_image(
    image: np.ndarray | Image.Image | Path | str,
    *,
    clip_percentile: float = 0.5,
    gamma: float = 0.9,
    sharpen: bool = True,
) -> Image.Image:
    """Normalize paper background to pure white and sharpen text/ink strokes."""
    if isinstance(image, (str, Path)):
        img_np = cv2.imread(str(image))
        if img_np is None:
            raise FileNotFoundError(f"Cannot read image at {image}")
    elif isinstance(image, Image.Image):
        img_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    else:
        img_np = image.copy()

    # If already grayscale or 3-channel
    if len(img_np.shape) == 2:
        gray = img_np
    else:
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    # 1. Background illumination estimation via morphological dilation
    # Captures uneven lighting across the scanned page
    kernel_size = 31
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    bg_illumination = cv2.morphologyEx(gray, cv2.MORPH_DILATE, kernel)
    # Ensure background estimation does not drop into dark ink/drawing regions
    bg_safe = np.maximum(bg_illumination, 180)

    # 2. Illumination compensation: divide image by background
    diff = cv2.absdiff(bg_safe, gray)
    norm = 255 - diff

    # 3. Soft contrast stretch: push background (>230) to 255, dark text to true black
    p_low = np.percentile(norm, clip_percentile)
    p_high = np.percentile(norm, 100 - clip_percentile)
    if p_high > p_low:
        stretched = np.clip((norm.astype(np.float32) - p_low) / (p_high - p_low) * 255.0, 0, 255).astype(np.uint8)
    else:
        stretched = norm

    # Threshold roll-off to guarantee pure white paper background
    stretched[stretched > 235] = 255

    # Gamma correction to enhance thin ink strokes
    if gamma != 1.0:
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype(np.uint8)
        stretched = cv2.LUT(stretched, table)

    pil_img = Image.fromarray(stretched)

    # 4. Optional subtle unsharp masking for crisp text edges
    if sharpen:
        pil_img = pil_img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=3))

    return pil_img


def crop_tight_bbox(
    image: Image.Image | np.ndarray,
    *,
    margin: int = 20,
    dark_threshold: int = 240,
    strip_header_footer: bool = False,
) -> Image.Image:
    """Detect ink content boundaries and crop with clean margin, removing wasted border."""
    if isinstance(image, Image.Image):
        gray = np.array(image.convert("L"))
        source_pil = image
    else:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        source_pil = Image.fromarray(gray)

    h, w = gray.shape

    # Find dark ink pixels
    ink_mask = gray < dark_threshold

    # Exclude outermost margins or running header/footer
    m_h_top = int(h * 0.065) if strip_header_footer else int(h * 0.02)
    m_h_bot = int(h * 0.065) if strip_header_footer else int(h * 0.02)
    m_w = int(w * 0.03)

    ink_mask[:m_h_top, :] = False
    ink_mask[h - m_h_bot :, :] = False
    ink_mask[:, :m_w] = False
    ink_mask[:, w - m_w :] = False

    coords = np.argwhere(ink_mask)
    if coords.size == 0:
        return source_pil

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    # Add margins with bounds clamping
    x0 = max(0, int(x_min) - margin)
    y0 = max(0, int(y_min) - margin)
    x1 = min(w, int(x_max) + margin)
    y1 = min(h, int(y_max) + margin)

    if (x1 - x0) < 50 or (y1 - y0) < 50:
        return source_pil

    return source_pil.crop((x0, y0, x1, y1))


def detect_reading_illustrations(
    image: Image.Image | np.ndarray | Path | str,
    ocr_data: dict[str, Any] | None = None,
    *,
    min_core_dim: int = 65,
    min_area: int = 2500,
    max_aspect_ratio: float = 4.5,
    margin_ratio_x: float = 0.05,
    margin_ratio_y: float = 0.05,
) -> list[tuple[int, int, int, int]]:
    """Detect non-text visual diagrams, drawings, and illustrations on reading comprehension pages.

    Differentiates text lines (small uniform height ~25-35px) from diagrams/illustrations
    (large 2D area, non-text graphics, shading, leader lines, or boxed visuals).
    Automatically incorporates associated pointer lines and caption annotations (e.g. '*白目：...').

    Returns:
        List of bounding boxes (x0, y0, x1, y1) in page coordinate space.
    """
    if ocr_data:
        # Fast exit for instruction covers, blank placeholders, and pure question pages
        raw = ocr_data.get("raw_passage", "") or ""
        opts = ocr_data.get("options", {}) or {}
        pass_ast = ocr_data.get("passage_ast", []) or []
        if "読解問題" in raw and "説明" in raw:
            return []
        if "問題はありません" in raw:
            return []
        if len(opts) > 0 and len(pass_ast) == 0:
            return []

    if isinstance(image, (str, Path)):
        gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise FileNotFoundError(f"Cannot read image at {image}")
    elif isinstance(image, Image.Image):
        gray = np.array(image.convert("L"))
    else:
        gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape

    # 1. Binarize to isolate ink strokes and shaded halftone patterns
    _, thresh = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY_INV)

    # 2. Exclude outermost margins (headers, footers, outer scanner noise)
    m_x = int(w * margin_ratio_x)
    m_y = int(h * margin_ratio_y)
    mask = np.zeros_like(thresh)
    mask[m_y : h - m_y, m_x : w - m_x] = thresh[m_y : h - m_y, m_x : w - m_x]

    # 3. Connected components analysis
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

    core_boxes = []
    for i in range(1, num_labels):
        x, y, cw, ch, area = stats[i]
        # Ignore small characters, spine artifacts, page edges, or divider lines
        if cw < 40 or ch < 40:
            continue
        aspect = max(cw / ch, ch / cw)
        if aspect > max_aspect_ratio:
            continue

        density = area / (cw * ch)
        # Filter 1: Reject hollow wireframe borders (announcement boxes, page borders, instruction boxes)
        if (cw > 0.55 * w and ch > 0.25 * h and density < 0.06) or density < 0.025:
            continue

        # Filter 2: Real diagram core requires 2D dimensions and non-trivial area
        if cw >= 120 and ch >= 100 and area >= min_area:
            if cw < w * 0.90 and ch < h * 0.65:
                # Exclude top header titles
                if y < h * 0.15 and ch < 180 and cw > w * 0.4:
                    continue
                core_boxes.append((int(x), int(y), int(x + cw), int(y + ch)))

    if not core_boxes:
        return []

    # 4. Cluster nearby visual core components (merge vertically and horizontally close elements)
    merged = []
    for box in sorted(core_boxes, key=lambda b: b[1]):
        if not merged:
            merged.append(list(box))
        else:
            last = merged[-1]
            if box[1] <= last[3] + 60 and box[0] <= last[2] + 150 and box[2] >= last[0] - 150:
                last[0] = min(last[0], box[0])
                last[1] = min(last[1], box[1])
                last[2] = max(last[2], box[2])
                last[3] = max(last[3], box[3])
            else:
                merged.append(list(box))

    # 5. Expand figure regions to include leader lines, arrows, and associated caption annotations
    final_figures: list[tuple[int, int, int, int]] = []
    for fx0, fy0, fx1, fy1 in merged:
        band_y0 = max(m_y, fy0 - 35)
        band_y1 = min(h - m_y, fy1 + 35)

        band_comps = []
        for i in range(1, num_labels):
            x, y, cw, ch, area = stats[i]
            if y >= band_y0 and y + ch <= band_y1:
                # Include elements within reasonable horizontal distance to the diagram core
                if x + cw >= fx0 - 250 and x <= fx1 + 180:
                    band_comps.append((int(x), int(y), int(x + cw), int(y + ch)))

        if band_comps:
            bx0 = max(0, min(c[0] for c in band_comps) - 15)
            by0 = max(0, min(c[1] for c in band_comps) - 15)
            bx1 = min(w, max(c[2] for c in band_comps) + 15)
            by1 = min(h, max(c[3] for c in band_comps) + 15)
            # Ensure final box is a localized figure, not the whole page
            if (bx1 - bx0) < w * 0.90 and (by1 - by0) < h * 0.65:
                final_figures.append((bx0, by0, bx1, by1))

    return final_figures


def crop_and_whiten_figure(
    image: Image.Image | np.ndarray | Path | str,
    bbox: tuple[int, int, int, int],
    *,
    padding: int = 15,
) -> Image.Image:
    """Crop an illustration region tightly with padding and normalize to clean pure-white background."""
    if isinstance(image, (str, Path)):
        pil_img = Image.open(str(image)).convert("RGB")
    elif isinstance(image, Image.Image):
        pil_img = image.convert("RGB")
    else:
        pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    w, h = pil_img.size
    x0, y0, x1, y1 = bbox
    cx0 = max(0, int(x0) - padding)
    cy0 = max(0, int(y0) - padding)
    cx1 = min(w, int(x1) + padding)
    cy1 = min(h, int(y1) + padding)

    cropped = pil_img.crop((cx0, cy0, cx1, cy1))
    return clean_and_whiten_image(cropped)


def remaster_image_file(
    source_path: Path,
    output_path: Path,
    *,
    tight_crop: bool = True,
    strip_header_footer: bool = False,
    scale_factor: float = 1.0,
) -> Path:
    """Read a scanned image, apply whitening, noise reduction, and optional tight crop."""
    cleaned = clean_and_whiten_image(source_path)
    if tight_crop:
        cleaned = crop_tight_bbox(cleaned, strip_header_footer=strip_header_footer)

    if scale_factor != 1.0 and scale_factor > 0:
        new_w = int(cleaned.width * scale_factor)
        new_h = int(cleaned.height * scale_factor)
        cleaned = cleaned.resize((new_w, new_h), Image.Resampling.LANCZOS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.save(str(output_path), "PNG", optimize=True)
    return output_path


def render_table_to_svg(
    rows: list[list[str]],
    *,
    title: str = "",
    col_widths: list[int] | None = None,
    cell_height: int = 38,
    font_size: int = 14,
) -> str:
    """Generate a crisp, responsive SVG table diagram for tabular EJU listening/reading data."""
    if not rows:
        return "<svg></svg>"

    num_cols = max(len(r) for r in rows)
    if not col_widths:
        col_widths = [140] + [90] * (num_cols - 1)
    if len(col_widths) < num_cols:
        col_widths.extend([90] * (num_cols - len(col_widths)))

    total_width = sum(col_widths[:num_cols]) + 40
    title_offset = 45 if title else 20
    total_height = title_offset + len(rows) * cell_height + 25

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} {total_height}" '
        f'width="100%" style="max-width: {total_width}px; font-family: -apple-system, BlinkMacSystemFont, '
        f'\'Hiragino Sans\', \'Yu Gothic\', sans-serif; background: #ffffff;">',
        f'<rect width="{total_width}" height="{total_height}" fill="#ffffff" rx="6"/>',
    ]

    if title:
        svg_parts.append(
            f'<text x="20" y="28" font-size="{font_size + 2}" font-weight="bold" fill="#1f2937">'
            f'{html.escape(title)}</text>'
        )

    # Render table header & cells
    curr_y = title_offset
    for r_idx, row in enumerate(rows):
        is_header = (r_idx == 0)
        curr_x = 20
        bg_color = "#f3f4f6" if is_header else ("#ffffff" if r_idx % 2 == 1 else "#f9fafb")
        text_color = "#111827" if is_header else "#374151"
        font_weight = "bold" if is_header else "normal"

        for c_idx, cell_text in enumerate(row):
            w = col_widths[c_idx] if c_idx < len(col_widths) else 90
            svg_parts.append(
                f'<rect x="{curr_x}" y="{curr_y}" width="{w}" height="{cell_height}" '
                f'fill="{bg_color}" stroke="#d1d5db" stroke-width="1"/>'
            )
            cell_str = str(cell_text).strip()
            if cell_str in {"○", "△", "×", "1", "2", "3", "4", "A", "B", "C", "D"}:
                text_x = curr_x + w / 2
                anchor = 'text-anchor="middle"'
            else:
                text_x = curr_x + 10
                anchor = 'text-anchor="start"'

            svg_parts.append(
                f'<text x="{text_x}" y="{curr_y + cell_height / 2 + 5}" font-size="{font_size}" '
                f'font-weight="{font_weight}" fill="{text_color}" {anchor}>'
                f'{html.escape(cell_str)}</text>'
            )
            curr_x += w
        curr_y += cell_height

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
