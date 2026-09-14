"""N2 Exam Builder: parses and builds complete N2 JLPT exam packages.
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
from exam_schema import CHOICE_COUNT, audit_exam, prepare_exam

# Helper script for Windows Runtime OCR
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


def extract_ocr_for_pdf(pdf_path: Path, work_dir: Path) -> tuple[list[str], int]:
    """Renders all PDF pages and runs OCR, returning list of OCR text per page."""
    img_dir = work_dir / "images"
    txt_dir = work_dir / "ocr_text"
    img_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(pdf_path))
    page_count = len(doc)
    for i, page in enumerate(doc):
        img_path = img_dir / f"p{i+1:02d}.png"
        if not img_path.exists():
            page.get_pixmap(dpi=180).save(str(img_path))

    ps_file = work_dir / "run_ocr.ps1"
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
    for i in range(page_count):
        txt_path = txt_dir / f"p{i+1:02d}.txt"
        if txt_path.exists():
            texts.append(txt_path.read_text(encoding="utf-8"))
        else:
            texts.append("")
    return texts, page_count


print("N2 builder script ready.")

