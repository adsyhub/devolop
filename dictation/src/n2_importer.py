"""Comprehensive N2 exam importer and pipeline.

Builds JLPT N2 exam packages from scanned PDFs in dist/N2/:
  exams/<slug>/
    exam-meta.json
    answer-key.txt
    pages/pNN.json
    exam.json
"""

from __future__ import annotations

import argparse
import copy
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

import pymupdf

from exam_import import assemble_exam, load_pages, parse_answer_key
from exam_schema import CHOICE_COUNT, audit_exam, prepare_exam

PS_BATCH_OCR = """
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.Ocr.OcrEngine, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null

$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | select -First 1

function Await-Op($asyncOp, $type) {
    $asTask = $asTaskGeneric.MakeGenericMethod($type)
    $task = $asTask.Invoke($null, @($asyncOp))
    $task.Wait()
    return $task.Result
}

function Run-Ocr($imagePath, $langTag) {
    $file = Await-Op ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imagePath)) ([Windows.Storage.StorageFile])
    $stream = Await-Op ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await-Op ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $softwareBitmap = Await-Op ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    
    $lang = [Windows.Globalization.Language]::new($langTag)
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
    $result = Await-Op ($engine.RecognizeAsync($softwareBitmap)) ([Windows.Media.Ocr.OcrResult])
    return $result.Text
}

$inputDir = $args[0]
$outputDir = $args[1]

Get-ChildItem -Path $inputDir -Filter "*.png" | ForEach-Object {
    $num = $_.BaseName
    $txtPath = Join-Path $outputDir "$num.txt"
    if (-not (Test-Path $txtPath)) {
        $txt = Run-Ocr $_.FullName 'ja'
        [System.IO.File]::WriteAllText($txtPath, $txt, [System.Text.Encoding]::UTF8)
    }
}
"""


def get_pdf_metadata(pdf_path: Path) -> tuple[str, str, str, str, int, int]:
    name = pdf_path.name
    m = re.search(r"(\d{4})年(\d{1,2})月", name)
    if m:
        year = m.group(1)
        month_int = int(m.group(2))
    else:
        m2 = re.search(r"(\d{4})\.(\d{1,2})", name)
        if m2:
            year = m2.group(1)
            month_int = int(m2.group(2))
        else:
            year = "2010"
            month_int = 12

    slug = f"{year}-{month_int:02d}-N2"
    session_label = f"{year}年{month_int}月"
    title = f"{year}年{month_int}月 日本語能力試験 N2"

    bytes_data = pdf_path.read_bytes()
    sha256 = hashlib.sha256(bytes_data).hexdigest()
    doc = pymupdf.open(str(pdf_path))
    page_count = len(doc)
    return slug, session_label, title, sha256, len(bytes_data), page_count


def ocr_all_pages(pdf_path: Path, work_dir: Path) -> list[str]:
    img_dir = work_dir / "images"
    txt_dir = work_dir / "ocr_text"
    img_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(pdf_path))
    for i, page in enumerate(doc):
        img_path = img_dir / f"p{i+1:02d}.png"
        if not img_path.exists():
            page.get_pixmap(dpi=180).save(str(img_path))

    ps_file = work_dir / "batch_ocr.ps1"
    ps_file.write_text(PS_BATCH_OCR, encoding="utf-8-sig")

    subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps_file),
            str(img_dir.resolve()),
            str(txt_dir.resolve()),
        ],
        check=True,
        capture_output=True,
    )

    texts: list[str] = []
    for i in range(len(doc)):
        txt_file = txt_dir / f"p{i+1:02d}.txt"
        if txt_file.exists():
            texts.append(txt_file.read_text(encoding="utf-8"))
        else:
            texts.append("")
    return texts


def parse_answer_key_from_pages(texts: list[str]) -> dict[int, int]:
    """Finds and parses answer key table and explanations from OCR text."""
    answers: dict[int, int] = {}

    # Try finding the answer key table page
    for pidx, txt in enumerate(texts):
        if "真題答案" in txt or "真题答案" in txt or "答案" in txt and "語法" in txt:
            # Parse answer table items like: ( 1 ) 3 or (1) 3
            # or 1) 3
            # Also clean OCR spaces in numbers
            clean_txt = re.sub(r"\s+", " ", txt)
            matches = re.findall(r"[（(【\[]\s*(\d{1,2})\s*[)）】\]]\s*[:：=.]?\s*([1-4])", clean_txt)
            for qstr, ans in matches:
                qnum = int(qstr)
                if 1 <= qnum <= 75 and qnum not in answers:
                    answers[qnum] = int(ans)

    # Also search explanation pages
    all_exp_text = "\n".join(texts[18:])
    # Match patterns like: 【 1 】 正解: 1 or [ 1 ] 正解: 1 or 問題1 (1) 正解: 1
    exp_matches = re.findall(r"[（(【\[]?\s*(\d{1,2})\s*[)）】\]]?\s*(?:正解|答案)\s*[:：=.]?\s*([1-4])", all_exp_text)
    for qstr, ans in exp_matches:
        qnum = int(qstr)
        if 1 <= qnum <= 75 and qnum not in answers:
            answers[qnum] = int(ans)

    # In case any question 1..75 is missing, check each page's specific matches
    return answers


print("Importer initialized successfully.")

