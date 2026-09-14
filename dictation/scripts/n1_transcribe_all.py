# Transcribe all N1 listening mp3 files.
from __future__ import annotations
import glob, json, os, re, subprocess, sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
src_dir = PROJECT_DIR / 'dist' / 'N1听力音频（2010.7-2022.07）'
files = sorted(glob.glob(str(src_dir / '*.mp3')))

print(f'Found {len(files)} N1 audio files.')
for f in files:
    name = os.path.basename(f)
    m = re.search(r'N1-(\d{4})\.(\d{1,2})', name)
    if not m:
        continue
    year = int(m.group(1))
    month = int(m.group(2))
    slug = f'{year:04d}-{month:02d}-N1'
    title = f'JLPT N1 听力 {year}年{month}月'
    work_dir = PROJECT_DIR / 'n1-jingting-work' / slug
    manifest_transcribed = work_dir / 'manifest.transcribed.json'
    if manifest_transcribed.exists():
        print(f'SKIP {slug} (already transcribed)')
        continue
    print(f'=== Transcribing {slug} <- {name} ===')
    work_dir.mkdir(parents=True, exist_ok=True)
    out_zip = work_dir / 'course.zip'
    cmd = [
        sys.executable,
        '-X', 'utf8',
        str(PROJECT_DIR / 'src' / 'build_course.py'),
        '--audio', f,
        '--title', title,
        '--language', 'ja',
        '--no-enrich',
        '--work-dir', str(work_dir),
        '--out', str(out_zip),
        '--force',
    ]
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    res = subprocess.run(cmd, env=env)
    print(f'{slug} exit={res.returncode}')
print('ALL TRANSCRIPTIONS COMPLETED.')
