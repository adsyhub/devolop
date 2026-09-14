# Complete pipeline helper for JLPT N1 listening courses.
from __future__ import annotations
import glob, json, os, re, subprocess, sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from language_support import manifest_language_code, set_source_text, source_text
from bundle_quality import audit_manifest

def get_n1_audio_files() -> list[dict]:
    src_dir = PROJECT_DIR / "dist" / "N1听力音频（2010.7-2022.07）"
    files = sorted(glob.glob(str(src_dir / "*.mp3")))
    results = []
    for f in files:
        name = os.path.basename(f)
        m = re.search(r"N1-(\d{4})\.(\d{1,2})", name)
        if not m:
            continue
        year = int(m.group(1))
        month = int(m.group(2))
        slug = f"{year:04d}-{month:02d}-N1"
        title = f"JLPT N1 听力 {year}年{month}月"
        results.append({
            "audio_path": Path(f),
            "filename": name,
            "year": year,
            "month": month,
            "slug": slug,
            "title": title,
            "work_dir": PROJECT_DIR / "n1-jingting-work" / slug,
        })
    return results

def apply_asr_fixes(slug: str) -> int:
    work_dir = PROJECT_DIR / "n1-jingting-work" / slug
    manifest_path = work_dir / "manifest.transcribed.json"
    if not manifest_path.exists():
        print(f"[{slug}] No manifest.transcribed.json found.")
        return 0

    terms_path = PROJECT_DIR / "scripts" / "n2_asr_terms.json"
    terms_data = json.loads(terms_path.read_text(encoding="utf-8"))
    rules = terms_data.get("replacements", [])

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    language = manifest_language_code(manifest)
    sentences = manifest.get("sentences", [])

    edits = []
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            continue
        before = source_text(sentence, language)
        after = before
        applied = []
        for rule in rules:
            if rule["from"] in after:
                after = after.replace(rule["from"], rule["to"])
                applied.append(f"{rule['from']}->{rule['to']}")
        if after != before:
            set_source_text(sentence, after, language)
            edits.append({
                "sentenceIndex": index,
                "rules": applied,
                "before": before,
                "after": after,
            })

    if edits:
        joined = "".join(source_text(s, language) for s in sentences if isinstance(s, dict))
        manifest["transcriptText"] = joined
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        corrections_path = work_dir / "asr-corrections.json"
        corrections_path.write_text(
            json.dumps({
                "schemaVersion": 1,
                "manifest": str(manifest_path),
                "edits": edits,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[{slug}] Applied {len(edits)} ASR corrections.")
    else:
        print(f"[{slug}] No ASR corrections needed.")
    return len(edits)

def make_batches(slug: str) -> list[Path]:
    work_dir = PROJECT_DIR / "n1-jingting-work" / slug
    info = next((i for i in get_n1_audio_files() if i["slug"] == slug), None)
    if not info:
        raise ValueError(f"Unknown slug {slug}")

    handoff_dir = work_dir / "handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    out_zip = work_dir / "course.zip"

    cmd = [
        sys.executable,
        "-X", "utf8",
        str(PROJECT_DIR / "src" / "build_course.py"),
        "--audio", str(info["audio_path"]),
        "--title", info["title"],
        "--language", "ja",
        "--kind", "manual",
        "--handoff-dir", str(handoff_dir),
        "--batch-size", "25",
        "--work-dir", str(work_dir),
        "--out", str(out_zip),
        "--force",
        "--resume",
        "--no-normalize",
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    batch_files = sorted(glob.glob(str(work_dir / "deepseek_batches" / "batch_*.json")))
    print(f"[{slug}] Prepared {len(batch_files)} batches.")
    return [Path(p) for p in batch_files]

def build_and_install(slug: str) -> bool:
    work_dir = PROJECT_DIR / "n1-jingting-work" / slug
    info = next((i for i in get_n1_audio_files() if i["slug"] == slug), None)
    if not info:
        raise ValueError(f"Unknown slug {slug}")

    handoff_dir = work_dir / "handoff"
    out_zip = work_dir / "course.zip"

    print(f"[{slug}] Building course ZIP...")
    cmd = [
        sys.executable,
        "-X", "utf8",
        str(PROJECT_DIR / "src" / "build_course.py"),
        "--audio", str(info["audio_path"]),
        "--title", info["title"],
        "--language", "ja",
        "--kind", "manual",
        "--handoff-dir", str(handoff_dir),
        "--batch-size", "25",
        "--work-dir", str(work_dir),
        "--out", str(out_zip),
        "--force",
        "--resume",
        "--no-normalize",
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"[{slug}] Build failed (code {res.returncode}):\n{res.stderr}\n{res.stdout}")
        return False

    print(f"[{slug}] Installing into courses/{slug}...")
    install_cmd = [
        sys.executable,
        "-X", "utf8",
        str(PROJECT_DIR / "src" / "install_course.py"),
        str(out_zip),
        "--name", slug,
        "--force",
    ]
    res_inst = subprocess.run(install_cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    if res_inst.returncode != 0:
        print(f"[{slug}] Install failed (code {res_inst.returncode}):\n{res_inst.stderr}\n{res_inst.stdout}")
        return False

    print(f"[{slug}] Successfully built and installed!")
    return True

if __name__ == "__main__":
    for item in get_n1_audio_files():
        print(f"{item['slug']:<12} {item['title']:<25} {item['filename']}")
