"""Content-addressed media storage, figure cropping and asset lifecycle."""

from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path
from typing import Any

from .errors import ContractError, MediaError
from .util import utc_now

DEFAULT_MEDIA_DIR = Path("library/media")
_SAFE_ASSET_ID = re.compile(r"^[0-9a-f]{64}$")


class AssetStore:
    def __init__(self, media_dir: Path | None = None) -> None:
        self.root = (media_dir or DEFAULT_MEDIA_DIR).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for_hash(self, sha256: str, ext: str) -> Path:
        clean_ext = ext.lstrip(".").lower()
        if not re.fullmatch(r"[a-z0-9]{1,8}", clean_ext):
            raise MediaError("Invalid media extension")
        sub = self.root / sha256[:2]
        if not sub.resolve().is_relative_to(self.root): raise MediaError("Media path escapes storage")
        sub.mkdir(parents=True, exist_ok=True)
        return sub / f"{sha256}.{clean_ext}"

    def put_bytes(
        self, data: bytes, *, mime_type: str, ext: str | None = None
    ) -> dict[str, Any]:
        if len(data) > 150_000_000:
            raise MediaError("Media file exceeds maximum allowed size of 150MB")
        sha256 = hashlib.sha256(data).hexdigest()
        if not ext:
            ext = mimetypes.guess_extension(mime_type) or ".bin"
        target = self._path_for_hash(sha256, ext)
        import os
        import tempfile
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != sha256:
            fd, temporary = tempfile.mkstemp(prefix=sha256 + '.', suffix='.tmp', dir=target.parent)
            try:
                with os.fdopen(fd,'wb') as stream:
                    stream.write(data);stream.flush();os.fsync(stream.fileno())
                os.replace(temporary,target)
            finally:
                if os.path.exists(temporary):os.unlink(temporary)
        return {
            "assetId": sha256,
            "sha256": sha256,
            "mimeType": mime_type,
            "sizeBytes": len(data),
            "filePath": str(target.relative_to(self.root)).replace("\\", "/"),
            "absolutePath": target,
        }

    def put_file(self, source_path: Path, *, mime_type: str | None = None) -> dict[str, Any]:
        source = source_path.expanduser().resolve()
        if not source.is_file():
            raise MediaError(f"Source file not found: {source}")
        if source.stat().st_size>150_000_000: raise MediaError("Media file exceeds 150MB")
        mime = mime_type or mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        import os
        import tempfile
        from .util import sha256_file
        fd, temporary = tempfile.mkstemp(prefix='import-', suffix='.tmp', dir=self.root)
        digest=hashlib.sha256();size=0
        try:
            with source.open('rb') as src, os.fdopen(fd,'wb') as dst:
                while chunk:=src.read(1024*1024):
                    size+=len(chunk)
                    if size>150_000_000:raise MediaError('Media file exceeds 150MB')
                    digest.update(chunk);dst.write(chunk)
                dst.flush();os.fsync(dst.fileno())
            asset_id=digest.hexdigest()
            target=self._path_for_hash(asset_id,source.suffix or mimetypes.guess_extension(mime) or '.bin')
            if not target.is_file() or sha256_file(target)!=asset_id:os.replace(temporary,target)
            return {'assetId':asset_id,'sha256':asset_id,'mimeType':mime,'sizeBytes':size,
                    'filePath':target.relative_to(self.root).as_posix(),'absolutePath':target}
        finally:
            Path(temporary).unlink(missing_ok=True)

    def has(self, asset_id: str) -> bool:
        try:
            self.get_path(asset_id)
            return True
        except MediaError:
            return False

    def get_bytes(self, asset_id: str) -> bytes:
        return self.get_path(asset_id).read_bytes()

    def get_path(self, asset_id: str) -> Path:
        if not isinstance(asset_id,str) or not _SAFE_ASSET_ID.fullmatch(asset_id):
            raise MediaError(f"Invalid asset ID format: {asset_id}")
        # Search direct in subfolder or by sha256 prefix
        sub = self.root / asset_id[:2]
        if sub.is_dir():
            matches = [p for p in sub.glob(f"{asset_id}.*") if p.is_file() and ".tmp" not in p.name]
            if matches:
                candidate = matches[0].resolve()
                if not candidate.is_relative_to(self.root):
                    raise MediaError("Media path escapes storage")
                return candidate
        # Also check root level fallback
        matches = [p for p in self.root.glob(f"{asset_id}.*") if p.is_file() and ".tmp" not in p.name]
        if matches:
            candidate = matches[0].resolve()
            if not candidate.is_relative_to(self.root):
                raise MediaError("Media path escapes storage")
            return candidate
        raise MediaError(f"Asset not found: {asset_id}")


def clip_figure_from_pdf(
    pdf_path: Path,
    page_number: int,
    source_bbox: list[float],
    *,
    dpi: int = 300,
) -> tuple[bytes, int, int]:
    """Crops a figure directly from vector PDF page at high DPI for crisp rendering."""
    try:
        import pymupdf
    except ImportError as exc:
        raise MediaError("PyMuPDF required for figure extraction") from exc

    if not isinstance(source_bbox, list) or len(source_bbox) != 4 or any(type(v) not in (int,float) for v in source_bbox):
        raise ContractError(f"Invalid bbox: {source_bbox}")
    x0, y0, x1, y1 = [float(v) for v in source_bbox]
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ContractError(f"Bbox coordinates out of bounds: {source_bbox}")

    if type(page_number) is not int or type(dpi) is not int or not 72 <= dpi <= 600:
        raise ContractError('Invalid page number or crop DPI')
    doc = pymupdf.open(pdf_path.expanduser().resolve())
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise MediaError(f"Page number {page_number} out of range (1..{doc.page_count})")
        page = doc[page_number - 1]
        from .pdf_pipeline import _check_page
        _check_page(page,dpi)
        pw, ph = page.rect.width, page.rect.height
        clip_rect = pymupdf.Rect(x0 * pw, y0 * ph, x1 * pw, y1 * ph)
        scale = dpi / 72.0
        mat = pymupdf.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
        png_bytes = pix.tobytes("png")
        return png_bytes, pix.width, pix.height
    finally:
        doc.close()


def clip_figure_from_image(
    image_path: Path,
    source_bbox: list[float],
) -> tuple[bytes, int, int]:
    """Crops a figure from an existing rendered page image."""
    try:
        from PIL import Image
        import io
    except ImportError as exc:
        raise MediaError("Pillow required for image figure cropping") from exc

    if not isinstance(source_bbox, list) or len(source_bbox) != 4 or any(type(v) not in (int,float) for v in source_bbox):
        raise ContractError(f"Invalid bbox: {source_bbox}")
    x0, y0, x1, y1 = [float(v) for v in source_bbox]
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ContractError(f"Bbox coordinates out of bounds: {source_bbox}")

    with Image.open(image_path) as img:
        w, h = img.size
        box = (int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))
        cropped = img.crop(box)
        buf = io.BytesIO()
        cropped.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), cropped.width, cropped.height


def register_asset_origin(
    database: Any, asset_id: str, source_file_id: str, source_file_hash: str,
    page_number: int, bbox: list[float], rotation: int = 0, dpi: int = 200,
    review_revision_id: str | None = None, *, role: str = 'QUESTION_BOOKLET',
) -> str:
    """Bind an immutable crop to its verified source and producing draft revision."""
    import uuid
    from .util import canonical_json, sha256_file
    from .review import ContentWorkspace
    _, manifest = ContentWorkspace(database.workspace_root,database).source(source_file_id)
    if not any(f['role']==role and f['sha256']==source_file_hash for f in manifest['files']):
        raise ContractError('Asset origin does not match the current source')
    if type(page_number) is not int or page_number < 1 or type(dpi) is not int or not 72 <= dpi <= 600 or type(rotation) is not int or rotation not in {0,90,180,270}:
        raise ContractError('Invalid asset transform')
    if not isinstance(bbox,list) or len(bbox)!=4 or any(type(v) not in (int,float) for v in bbox) or not (0<=bbox[0]<bbox[2]<=1 and 0<=bbox[1]<bbox[3]<=1):
        raise ContractError('Invalid asset origin bbox')
    store=AssetStore(database.media_dir);path=store.get_path(asset_id)
    if sha256_file(path)!=asset_id:raise MediaError('Asset content hash mismatch')
    width=height=None
    if path.suffix.lower() in {'.png','.jpg','.jpeg','.webp'}:
        from PIL import Image
        with Image.open(path) as im: width,height=im.size;im.verify()
    origin_id='orig_'+uuid.uuid4().hex
    now=utc_now()
    with database._transaction():
        database.connection.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?)',
            (manifest['sourceId'],manifest['rights']['status'],canonical_json(manifest),now))
        if review_revision_id:
            row=database.connection.execute('SELECT source_id,role,page_number FROM page_revisions WHERE id=?',(review_revision_id,)).fetchone()
            if not row or (row['source_id'],row['role'],row['page_number'])!=(source_file_id,role,page_number):
                raise ContractError('Asset draft revision belongs to a different page')
        database.connection.execute('INSERT OR IGNORE INTO assets (id,sha256,mime_type,size_bytes,width,height,file_path,created_at) VALUES (?,?,?,?,?,?,?,?)',
            (asset_id,asset_id,mimetypes.guess_type(path.name)[0] or 'application/octet-stream',path.stat().st_size,width,height,path.relative_to(store.root).as_posix(),now))
        database.connection.execute('INSERT INTO asset_origins (id,asset_id,source_id,source_hash,role,page_number,bbox_json,transform_json,review_state,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (origin_id,asset_id,source_file_id,source_file_hash,role,page_number,canonical_json(bbox),canonical_json({'rotation':rotation,'dpi':dpi,'reviewRevisionId':review_revision_id}),'DRAFT',now))
    return origin_id
