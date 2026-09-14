"""N2 past paper automated processing and extraction pipeline.

Extracts past paper PDF scans from dist/N2/ into structured exam packages:
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
from exam_schema import audit_exam, prepare_exam

# Windows Runtime OCR helper via PowerShell
PS_OCR_SCRIPT = """
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


def render_and_ocr_pdf(pdf_path: Path, work_dir: Path) -> list[str]:
    """Renders PDF pages and runs OCR, returning list of OCR texts per page (0-indexed)."""
    img_dir = work_dir / "images"
    txt_dir = work_dir / "ocr_text"
    img_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(pdf_path))
    for i, page in enumerate(doc):
        img_path = img_dir / f"p{i+1:02d}.png"
        if not img_path.exists():
            page.get_pixmap(dpi=180).save(str(img_path))

    ps_file = work_dir / "run_batch_ocr.ps1"
    ps_file.write_text(PS_OCR_SCRIPT, encoding="utf-8-sig")

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
        txt_path = txt_dir / f"p{i+1:02d}.txt"
        if txt_path.exists():
            texts.append(txt_path.read_text(encoding="utf-8"))
        else:
            texts.append("")
    return texts


def parse_slug(pdf_path: Path) -> tuple[str, str, str]:
    """Returns (slug, sessionLabel, title)."""
    name = pdf_path.name
    m = re.search(r"(\d{4})年(\d{1,2})月", name)
    if m:
        year = m.group(1)
        month = f"{int(m.group(2)):02d}"
        month_int = int(m.group(2))
    else:
        m2 = re.search(r"(\d{4})\.(\d{1,2})", name)
        if m2:
            year = m2.group(1)
            month = f"{int(m2.group(2)):02d}"
            month_int = int(m2.group(2))
        else:
            year = "2010"
            month = "12"
            month_int = 12

    slug = f"{year}-{month}-N2"
    session_label = f"{year}年{month_int}月"
    title = f"{year}年{month_int}月 日本語能力試験 N2"
    return slug, session_label, title


print("N2 pipeline module initialized.")

