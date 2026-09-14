# Auto batch preparer: monitors n1-jingting-work and prepares batches as soon as transcribed.
from __future__ import annotations
import glob, json, os, re, subprocess, sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))
import n1_pipeline

def prep_all_available():
    files = n1_pipeline.get_n1_audio_files()
    for item in files:
        slug = item["slug"]
        work_dir = item["work_dir"]
        manifest_transcribed = work_dir / "manifest.transcribed.json"
        if not manifest_transcribed.exists():
            continue
        batches_dir = work_dir / "deepseek_batches"
        existing_batches = list(batches_dir.glob("batch_*.json")) if batches_dir.exists() else []
        if existing_batches:
            continue
        print(f"--- Prepping batches for {slug} ---")
        n1_pipeline.apply_asr_fixes(slug)
        n1_pipeline.make_batches(slug)
        print(f"--- Finished prepping {slug} ---")

if __name__ == "__main__":
    prep_all_available()
