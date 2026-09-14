"""Link imported exams to local course audio without trusting filenames alone.

Run with --dry-run first. --write is intentionally required before metadata or
exam artifacts are replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from exam_schema import audit_exam, prepare_exam  # noqa: E402


def safe_filename(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    name = value.strip().replace("\\", "/")
    return name if name and "/" not in name and name not in {".", ".."} else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def build_binding(course_dir: Path) -> dict[str, Any]:
    manifest = read_json(course_dir / "manifest.json")
    filename = safe_filename(manifest.get("audio"))
    if filename is None:
        raise ValueError("course manifest has no safe local audio filename")
    audio = course_dir / filename
    if not audio.is_file():
        raise ValueError(f"course audio is missing: {filename}")
    expected_bytes = audio.stat().st_size
    expected_hash = sha256_file(audio)
    metadata = manifest.get("buildMetadata")
    if isinstance(metadata, dict):
        claimed_hash = metadata.get("sourceAudioSha256")
        claimed_bytes = metadata.get("sourceAudioBytes")
        if claimed_hash is not None and claimed_hash != expected_hash:
            raise ValueError("course manifest sourceAudioSha256 does not match the audio file")
        if claimed_bytes is not None and claimed_bytes != expected_bytes:
            raise ValueError("course manifest sourceAudioBytes does not match the audio file")
    return {
        "kind": "course-audio",
        "courseSlug": course_dir.name,
        "expectedSha256": expected_hash,
        "expectedBytes": expected_bytes,
    }


def link_one(exam_dir: Path, course_dir: Path, *, write: bool, force: bool) -> str:
    meta_path = exam_dir / "exam-meta.json"
    artifact_path = exam_dir / "exam.json"
    if not meta_path.is_file() or not artifact_path.is_file():
        return "skipped: exam-meta.json or exam.json is missing"
    try:
        binding = build_binding(course_dir)
        meta = read_json(meta_path)
        existing = meta.get("listeningMedia")
        if existing and existing != binding and not force:
            return "skipped: existing linkage differs (pass --force to replace)"
        artifact = read_json(artifact_path)
        artifact["listeningMedia"] = binding
        prepared = prepare_exam(artifact)
        report = audit_exam(prepared)
        if report["summary"]["errors"]:
            return f"failed: linked artifact has {report['summary']['errors']} audit errors"
        if write:
            meta["listeningMedia"] = binding
            write_json_atomic(meta_path, meta)
            write_json_atomic(artifact_path, prepared)
        return "linked" if write else "would link"
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return f"failed: {error}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind exams to verified local course audio.")
    parser.add_argument("--exams-root", type=Path, default=PROJECT_ROOT / "exams")
    parser.add_argument("--courses-root", type=Path, default=PROJECT_ROOT / "courses")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--exam", help="Exam directory slug to bind.")
    selector.add_argument("--all-by-slug", action="store_true", help="Bind every exam with a same-slug course.")
    parser.add_argument("--course", help="Course slug for --exam.")
    parser.add_argument("--write", action="store_true", help="Atomically replace metadata and exam.json.")
    parser.add_argument("--dry-run", action="store_true", help="Print intended changes without writing.")
    parser.add_argument("--force", action="store_true", help="Replace a different existing linkage.")
    args = parser.parse_args()
    if args.exam and not args.course:
        parser.error("--course is required with --exam")
    write = bool(args.write and not args.dry_run)

    pairs: list[tuple[Path, Path]] = []
    if args.exam:
        pairs.append((args.exams_root / args.exam, args.courses_root / args.course))
    elif args.exams_root.is_dir() and args.courses_root.is_dir():
        for exam_dir in sorted(args.exams_root.iterdir()):
            course_dir = args.courses_root / exam_dir.name
            if exam_dir.is_dir() and course_dir.is_dir():
                pairs.append((exam_dir, course_dir))

    if not pairs:
        print("No matching exam/course pairs found.")
        return 1
    counts = {"linked": 0, "would": 0, "skipped": 0, "failed": 0}
    for exam_dir, course_dir in pairs:
        result = link_one(exam_dir, course_dir, write=write, force=args.force)
        print(f"{exam_dir.name}: {result}")
        key = "linked" if result == "linked" else "would" if result == "would link" else result.split(":", 1)[0]
        counts[key] += 1
    print(f"Summary: {counts['linked']} linked, {counts['would']} planned, {counts['skipped']} skipped, {counts['failed']} failed.")
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
