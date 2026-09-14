"""Read-only PDF probe and deterministic, resumable page rendering."""

from __future__ import annotations

import hashlib
import shutil
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import ContractError
from .source import source_file, validate_source_manifest
from .util import digest_json, load_json, parse_page_selection, utc_now, write_json


def _pymupdf():
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - depends on optional environment
        raise ContractError(
            "PDF commands require PyMuPDF. Install with: python -m pip install -e '.[pdf]'"
        ) from exc
    return pymupdf


def _ink_ratio(page: Any) -> float:
    pymupdf = _pymupdf()
    pix = page.get_pixmap(matrix=pymupdf.Matrix(0.28, 0.28), colorspace=pymupdf.csGRAY, alpha=False)
    samples = memoryview(pix.samples)
    if not samples:
        return 0.0
    ink = sum(1 for value in samples if value < 242)
    return round(ink / len(samples), 6)


def probe_pdf(path: Path, role: str) -> dict[str, Any]:
    pymupdf = _pymupdf()
    doc = pymupdf.open(path)
    pages = []
    try:
        if doc.needs_pass or doc.page_count<1 or doc.page_count>3000: raise ContractError("PDF is encrypted, empty or exceeds the page limit")
        for index, page in enumerate(doc):
            _check_page(page,180)
            page_dict = page.get_text("dict")
            text = page.get_text("text")
            ink_ratio = _ink_ratio(page)
            image_count = sum(
                1
                for block in page_dict.get("blocks", [])
                if isinstance(block, dict) and block.get("type") == 1
            )
            pages.append(
                {
                    "page": index + 1,
                    "widthPt": round(page.rect.width, 3),
                    "heightPt": round(page.rect.height, 3),
                    "rotation": int(page.rotation),
                    "textChars": len(text.strip()),
                    "imageBlocks": image_count,
                    "inkRatio": ink_ratio,
                    "likelyBlank": ink_ratio < 0.0015,
                }
            )
        return {
            "role": role,
            "path": str(path),
            "pageCount": doc.page_count,
            "encrypted": bool(doc.needs_pass),
            "metadata": dict(doc.metadata or {}),
            "pages": pages,
        }
    finally:
        doc.close()


def probe_manifest(manifest_path: Path, output_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    manifest = load_json(manifest_path)
    validate_source_manifest(manifest, manifest_path, verify_files=True)
    reports = []
    for item in manifest["files"]:
        if item["role"] not in {"QUESTION_BOOKLET", "ANSWER_KEY"}:
            continue
        reports.append(probe_pdf(source_file(manifest, manifest_path, item["role"]), item["role"]))
    report = {
        "schemaVersion": 1,
        "sourceId": manifest["sourceId"],
        "createdAt": utc_now(),
        "files": reports,
    }
    write_json(output_path.expanduser().resolve(), report)
    return report


def _render_pixmap(page: Any, dpi: int, clip: Any | None = None) -> Any:
    scale = dpi / 72.0
    return page.get_pixmap(matrix=_pymupdf().Matrix(scale, scale), clip=clip, alpha=False)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def render_manifest(
    manifest_path: Path,
    *,
    role: str,
    output_dir: Path,
    pages: str | None = None,
    full_dpi: int = 180,
    tile_dpi: int = 320,
    tile_count: int = 3,
    overlap: float = 0.08,
    cancelled=None,
    on_progress=None,
) -> dict[str, Any]:
    if role not in {"QUESTION_BOOKLET", "ANSWER_KEY"}:
        raise ContractError("render role must be QUESTION_BOOKLET or ANSWER_KEY")
    if type(full_dpi) is not int or type(tile_dpi) is not int or not 72 <= full_dpi <= 600 or not 72 <= tile_dpi <= 600:
        raise ContractError("DPI must be between 72 and 600")
    if type(tile_count) is not int or tile_count < 1 or tile_count > 8:
        raise ContractError("tile_count must be between 1 and 8")
    if not 0 <= overlap < 0.4:
        raise ContractError("overlap must be between 0 and 0.4")

    manifest_path = manifest_path.expanduser().resolve()
    manifest = load_json(manifest_path)
    validate_source_manifest(manifest, manifest_path, verify_files=True)
    pdf_path = source_file(manifest, manifest_path, role)
    pymupdf = _pymupdf()
    doc = pymupdf.open(pdf_path)
    output_dir = output_dir.expanduser().resolve()
    if doc.needs_pass or doc.page_count<1 or doc.page_count>3000:
        doc.close();raise ContractError('PDF is encrypted, empty or exceeds the page limit')
    output_dir.mkdir(parents=True,exist_ok=True)
    profile={'sourceHash':_file_sha256(pdf_path),'role':role,'fullDpi':full_dpi,'tileDpi':tile_dpi,'tileCount':tile_count,'overlap':overlap,'renderer':pymupdf.VersionBind}
    profile_id=digest_json(profile)
    selected = parse_page_selection(pages, doc.page_count)
    records = []
    try:
        for page_number in selected:
            if cancelled and cancelled(): break
            page = doc[page_number - 1]
            _check_page(page,max(full_dpi,tile_dpi))
            if shutil.disk_usage(output_dir).free < 256*1024*1024: raise ContractError("Insufficient render disk space")
            page_dir = output_dir / role.lower() / profile_id / f"page-{page_number:04d}"
            page_dir.mkdir(parents=True, exist_ok=True)
            full_path = page_dir / f"full-{full_dpi}dpi.png"
            _save_render(full_path,lambda:_render_pixmap(page,full_dpi))

            tile_records = []
            height = page.rect.height
            nominal = height / tile_count
            for tile_index in range(tile_count):
                y0 = max(0.0, tile_index * nominal - overlap * nominal)
                y1 = min(height, (tile_index + 1) * nominal + overlap * nominal)
                clip = pymupdf.Rect(page.rect.x0, y0, page.rect.x1, y1)
                tile_path = page_dir / f"tile-{tile_index + 1:02d}-{tile_dpi}dpi.png"
                _save_render(tile_path,lambda:_render_pixmap(page,tile_dpi,clip=clip))
                tile_records.append(
                    {
                        "index": tile_index + 1,
                        "path": str(tile_path.relative_to(output_dir)).replace("\\", "/"),
                        "bboxPt": [round(clip.x0, 3), round(clip.y0, 3), round(clip.x1, 3), round(clip.y1, 3)],
                        "sha256": _file_sha256(tile_path),
                    }
                )
            records.append(
                {
                    "role": role,
                    "page": page_number,
                    "sourceRotation": int(page.rotation),
                    "pageSizePt": [round(page.rect.width, 3), round(page.rect.height, 3)],
                    "full": {
                        "path": str(full_path.relative_to(output_dir)).replace("\\", "/"),
                        "dpi": full_dpi,
                        "sha256": _file_sha256(full_path),
                    },
                    "tiles": tile_records,
                }
            )
            if on_progress: on_progress(len(records),len(selected))
    finally:
        doc.close()

    index_path = output_dir / f"render-index-{role.lower()}.json"
    existing = load_json(index_path) if index_path.exists() else {"pages": []}
    by_page = {int(item["page"]): item for item in existing.get("pages", [])} if existing.get("profileId")==profile_id else {}
    by_page.update({int(item["page"]): item for item in records})
    index = {
        "schemaVersion": 1,
        "sourceId": manifest["sourceId"],
        "role": role,
        "sourcePdf": str(pdf_path),
        "profileId":profile_id,
        "sourceHash":profile["sourceHash"],
        "createdAt": utc_now(),
        "settings": {
            "fullDpi": full_dpi,
            "tileDpi": tile_dpi,
            "tileCount": tile_count,
            "overlap": overlap,
        },
        "pages": [by_page[key] for key in sorted(by_page)],
    }
    write_json(index_path, index)
    return index


def _check_page(page,dpi):
    if page.rect.width<=0 or page.rect.height<=0 or page.rect.width*page.rect.height*(dpi/72)**2>200_000_000:
        raise ContractError('PDF page exceeds the render pixel limit')


def _save_render(path,render):
    metadata=path.with_suffix('.sha256')
    if path.is_file() and metadata.is_file() and metadata.read_text()==_file_sha256(path): return
    data=render().tobytes('png')
    fd,temporary=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as stream: stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
        metadata.write_text(hashlib.sha256(data).hexdigest())
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
