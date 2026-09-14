"""PDF -> page images.

Scanned books from Pdg2Pic/FreePic2Pdf hold exactly one full-page JPEG per page.
Extracting that JPEG is lossless and much faster than re-rasterizing it, so we
do that when the layout allows and fall back to a DPI render otherwise.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

try:
    import pymupdf
except ImportError as exc:  # pragma: no cover - dependency reported by CLI
    raise SystemExit("pymupdf is required: pip install pymupdf") from exc

from PIL import Image


@dataclass(frozen=True)
class RenderedPage:
    """One page, on disk as PNG, plus how it got there."""

    index: int  # 0-based
    number: int  # 1-based, what a reader would call it
    path: Path
    width: int
    height: int
    source: str  # "embedded" | "raster"


def _sole_full_page_image(page: "pymupdf.Page") -> int | None:
    """Return the xref of the one image covering the page, or None."""
    images = page.get_images(full=True)
    if len(images) != 1:
        return None
    xref = images[0][0]
    rects = page.get_image_rects(xref)
    if len(rects) != 1:
        return None
    page_area = abs(page.rect.get_area())
    if page_area <= 0:
        return None
    # "Covers the page" with room for the hairline margins scanners leave.
    if abs(rects[0].get_area()) / page_area < 0.92:
        return None
    return xref


def render_pdf(
    pdf_path: Path,
    out_dir: Path,
    *,
    dpi: int = 300,
    pages: list[int] | None = None,
    max_edge: int | None = None,
    grayscale: bool = False,
) -> list[RenderedPage]:
    """Write one PNG per page into ``out_dir`` and describe what was written.

    ``pages`` is a list of 1-based page numbers; None means every page.
    Pages already rendered are reused, so an interrupted run resumes cheaply.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    wanted = (
        list(range(doc.page_count))
        if pages is None
        else [n - 1 for n in pages if 1 <= n <= doc.page_count]
    )

    rendered: list[RenderedPage] = []
    for index in wanted:
        page = doc[index]
        number = index + 1
        path = out_dir / f"page-{number:04d}.png"

        if path.exists():
            with Image.open(path) as probe:
                width, height = probe.size
            rendered.append(RenderedPage(index, number, path, width, height, "cached"))
            continue

        xref = _sole_full_page_image(page)
        if xref is not None:
            raw = doc.extract_image(xref)
            image = Image.open(io.BytesIO(raw["image"]))
            # Extracting the embedded JPEG bypasses the page's /Rotate, which the
            # pixmap path would have applied for us. Scans of Japanese books are
            # routinely stored upside down with /Rotate 180 -- three of five books
            # here were, and two of those mixed rotated and unrotated pages -- so
            # this has to be honoured per page, or the OCR reads them inverted.
            if page.rotation:
                image = image.rotate(-page.rotation, expand=True)
            source = "embedded"
        else:
            pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY if grayscale else pymupdf.csRGB)
            image = Image.frombytes("L" if grayscale else "RGB", (pixmap.width, pixmap.height), pixmap.samples)
            source = "raster"

        image = image.convert("L" if grayscale else "RGB")
        if max_edge and max(image.size) > max_edge:
            scale = max_edge / max(image.size)
            image = image.resize(
                (round(image.width * scale), round(image.height * scale)),
                Image.LANCZOS,
            )
        image.save(path, "PNG", optimize=True)
        rendered.append(RenderedPage(index, number, path, image.width, image.height, source))

    doc.close()
    return rendered


def pdf_summary(pdf_path: Path) -> dict:
    """Page count, metadata and whether a usable text layer already exists."""
    doc = pymupdf.open(pdf_path)
    sampled = min(doc.page_count, 10)
    text_chars = sum(len(doc[i].get_text().strip()) for i in range(sampled))
    summary = {
        "path": str(pdf_path),
        "pages": doc.page_count,
        "metadata": {k: v for k, v in (doc.metadata or {}).items() if v},
        "sampled_pages": sampled,
        "text_layer_chars_sampled": text_chars,
        "has_text_layer": text_chars > 50 * sampled,
    }
    doc.close()
    return summary


def extract_page_text_layer(doc: "pymupdf.Document", index: int) -> tuple[str, list[dict[str, Any]]]:
    """Extract embedded text and block bounding boxes from a PDF page if present."""
    page = doc[index]
    text = page.get_text("text").strip()
    raw_blocks = page.get_text("blocks")
    blocks = []
    for b in raw_blocks:
        if len(b) >= 5 and str(b[4]).strip():
            blocks.append({
                "bbox": [round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1)],
                "text": str(b[4]).strip(),
            })
    return text, blocks


def crop_column(
    images_dir: Path,
    out_dir: Path,
    *,
    fraction: float = 0.5,
    pages: list[int] | None = None,
) -> list[RenderedPage]:
    """Crop the right ``fraction`` of each page image, at native resolution.

    The grammar-connection panels this book floats on the right are set in type
    far smaller than the body text. Reading a whole page costs the model a
    downscale to fit the visual-token budget, and those panels are the first
    thing to become illegible -- they get dropped silently. A half-page crop is
    ~3.07 MP, which fits the same budget *without* any downscale, so the panel
    arrives at full scan resolution.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[RenderedPage] = []
    for path in sorted(images_dir.glob("page-*.png")):
        number = int(path.stem.split("-")[-1])
        if pages is not None and number not in pages:
            continue
        target = out_dir / path.name
        if target.exists():
            with Image.open(target) as probe:
                width, height = probe.size
            rendered.append(RenderedPage(number - 1, number, target, width, height, "cached"))
            continue
        with Image.open(path) as raw:
            image = raw.convert("L")
            left = int(image.width * (1.0 - fraction))
            crop = image.crop((left, 0, image.width, image.height))
        crop.save(target, "PNG", optimize=True)
        rendered.append(RenderedPage(number - 1, number, target, crop.width, crop.height, "crop"))
    return rendered
