"""把浏览器拖进来的原卷 PDF 落到工作区里。

制作台原来要求先把文件放进工作区、再在表单里手打相对路径。那对批量处理脚本
是对的（文件本来就在 PAPER/ 下），对"拖一个 PDF 进来就开工"不是。所以这里
开一个窄口子：只接受 PDF，只写进 ``incoming/``，名字由服务端决定。

页面给的文件名只当**提示**用：它参与推断年份与科目，但不直接当路径。落盘名
由内容哈希加一段清洗过的原名拼成，所以同一份文件重复上传不会堆出两份，
而 ``../`` 之类的路径片段根本走不到文件系统这一层。
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any

from .errors import ContractError
from .paper_naming import describe

INCOMING = "incoming"
MAX_BYTES = 150_000_000
PDF_MAGIC = b"%PDF-"

# 允许留在落盘名里的字符：中日文、拉丁字母、数字、连字符。其余一律折成 '-'。
_KEEP = re.compile(r"[^0-9A-Za-z　-ヿ一-鿿._-]+")


def safe_stem(name: str) -> str:
    """把页面给的名字压成一段能安全落盘的词干。"""
    base = unicodedata.normalize("NFC", (name or "").rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
    if base.lower().endswith(".pdf"):
        base = base[:-4]
    cleaned = _KEEP.sub("-", base).strip("-._")
    return cleaned[:80] or "upload"


def store(root: Path, filename: str, data: bytes) -> dict[str, Any]:
    """校验并落盘一份上传的 PDF，返回工作区相对路径与推断结果。"""
    if not isinstance(data, bytes) or not data:
        raise ContractError("Upload is empty")
    if len(data) > MAX_BYTES:
        raise ContractError("Upload exceeds the 150 MB limit for one source file")
    if not data.lstrip()[:len(PDF_MAGIC)].startswith(PDF_MAGIC):
        # 后缀是谁都能改的，文件头不是。只收真 PDF。
        raise ContractError("Only PDF source files can be uploaded here")
    digest = hashlib.sha256(data).hexdigest()
    folder = Path(root) / INCOMING
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{digest[:16]}-{safe_stem(filename)}.pdf"
    if not target.is_file():
        # 同名同内容就不重写：重写会让已经指向它的来源清单的哈希核验多跑一遍。
        temporary = target.with_suffix(".pdf.part")
        temporary.write_bytes(data)
        temporary.replace(target)
    return {
        "uploadId": f"{INCOMING}/{target.name}",
        "fileName": (filename or target.name).rsplit("/", 1)[-1],
        "storedName": target.name,
        "sizeBytes": len(data),
        "sha256": digest,
        "detected": describe(filename or target.name),
    }


def resolve(root: Path, upload_id: str) -> Path:
    """把上传句柄换回真实路径。只认 ``incoming/`` 下的文件。"""
    if not isinstance(upload_id, str) or not upload_id.startswith(INCOMING + "/"):
        raise ContractError("Unknown upload handle")
    path = (Path(root) / upload_id).resolve()
    folder = (Path(root) / INCOMING).resolve()
    if not path.is_relative_to(folder) or not path.is_file():
        raise ContractError("This upload is no longer in the workspace")
    return path
