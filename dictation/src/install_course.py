"""Turn a built ZIP into a course the launcher can actually open.

Building produced a verified ZIP and then stopped, leaving the last step - "now
unzip it into ``courses/``, but only the manifest and the audio, not the bundled
web player" - as folklore. That gap is why a freshly built course was not yet a
playable one.

What this does, in order:

1. verifies the ZIP the same way the builder does (no absolute paths, no ``..``,
   manifest present, audio non-empty);
2. audits the manifest and refuses to install a course with errors, matching the
   launcher's own quality gate rather than discovering the problem at play time;
3. extracts *only* ``manifest.json``, the audio the manifest names, and the
   quality report - the ZIP's copy of the player is deliberately left behind;
4. swaps the finished folder into place, so an interrupted install cannot leave a
   half-written course where the launcher will find it.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from bundle_io import safe_filename, verify_zip, write_json
from bundle_quality import audit_manifest
from course_schema import is_remote_media_manifest
from studio_artifacts import resolve_course_manifest_path, compute_directory_artifact_revision, CURRENT_SCHEMA_VERSION, utc_now_iso

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_COURSES_DIR = PROJECT_DIR / "courses"

#: Everything else in the bundle - the player, icons, the service worker - is
#: served from src/web at run time and must not be duplicated per course.
INSTALLED_EXTRAS = ("quality-report.json",)


class InstallError(SystemExit):
    pass


def install_bundle(
    zip_path: Path,
    *,
    courses_dir: Path | None = None,
    course_name: str | None = None,
    force: bool = False,
    allow_failed: bool = False,
    versioned: bool = False,
) -> Path:
    zip_path = Path(zip_path).expanduser().resolve()
    if not zip_path.is_file():
        raise InstallError(f"Bundle not found: {zip_path}")
    courses_dir = Path(courses_dir).expanduser().resolve() if courses_dir else DEFAULT_COURSES_DIR
    verify_zip(zip_path)

    with zipfile.ZipFile(zip_path) as bundle:
        manifest = json.loads(bundle.read("manifest.json").decode("utf-8-sig"))
        # An online-video bundle carries no media member at all: the video is never
        # downloaded, so there is nothing to extract and nothing to name-check.
        remote_media = is_remote_media_manifest(manifest)
        audio_name = "" if remote_media else str(manifest.get("audio") or "")
        if not remote_media:
            _reject_unsafe_name(audio_name)

        report = audit_manifest(manifest, require_enrichment=False)
        errors = int(report.get("summary", {}).get("errors") or 0)
        if errors and not allow_failed:
            raise InstallError(
                f"Refusing to install: the manifest has {errors} quality error(s).\n"
                "  The launcher would refuse to open this course anyway.\n"
                f"  Inspect it with: python src\\audit_bundle.py --manifest <manifest>\n"
                "  Pass --allow-failed to install it for inspection regardless."
            )

        name = _resolve_course_name(course_name, manifest, zip_path)
        destination = courses_dir / name
        if destination.exists() and not force:
            raise InstallError(f"Course folder already exists: {destination}. Use --force to replace it.")

        courses_dir.mkdir(parents=True, exist_ok=True)
        staging = courses_dir / f".{name}.installing"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)

        try:
            _extract_member(bundle, "manifest.json", staging)
            if not remote_media:
                _extract_member(bundle, audio_name, staging)
            for extra in INSTALLED_EXTRAS:
                if extra in bundle.namelist():
                    _extract_member(bundle, extra, staging)
            write_json(staging / "install-source.json", _install_record(zip_path, manifest, report))

            if versioned:
                art_rev = compute_directory_artifact_revision(staging)
                v_dir = staging / "versions" / art_rev
                v_dir.mkdir(parents=True, exist_ok=True)
                for m in list(staging.iterdir()):
                    if m.name != "versions":
                        if m.is_dir():
                            shutil.copytree(m, v_dir / m.name)
                        else:
                            shutil.copy2(m, v_dir / m.name)
                ptr = {
                    "schemaVersion": CURRENT_SCHEMA_VERSION,
                    "artifactRevision": art_rev,
                    "contentRevision": str(manifest.get("contentRevision") or art_rev),
                    "manifestName": "manifest.json",
                    "installedAt": utc_now_iso(),
                }
                (staging / "current.json").write_text(json.dumps(ptr, ensure_ascii=False, indent=2), encoding="utf-8")

            if destination.exists():
                previous = courses_dir / f".{name}.replaced"
                if previous.exists():
                    shutil.rmtree(previous)
                destination.rename(previous)
                staging.rename(destination)
                shutil.rmtree(previous)
            else:
                staging.rename(destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    return destination


def _install_record(zip_path: Path, manifest: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    build_metadata = manifest.get("buildMetadata") if isinstance(manifest.get("buildMetadata"), dict) else {}
    return {
        "sourceBundle": zip_path.name,
        "courseId": manifest.get("courseId"),
        "contentRevision": manifest.get("contentRevision"),
        "quality": report.get("summary"),
        # Which models produced this course travels with the course, so the
        # question is answerable from the installed folder alone.
        "asr": build_metadata.get("asr"),
        "enrichment": build_metadata.get("enrichment"),
    }


def _resolve_course_name(course_name: str | None, manifest: dict[str, Any], zip_path: Path) -> str:
    candidate = (course_name or "").strip() or str(manifest.get("title") or "").strip() or zip_path.stem
    name = safe_filename(candidate).replace(" ", "-")
    _reject_unsafe_name(name)
    return name


def _reject_unsafe_name(value: str) -> None:
    if not value.strip():
        raise InstallError("The bundle names an empty file or course.")
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
        raise InstallError(f"Unsafe name in bundle: {value!r}")


def _extract_member(bundle: zipfile.ZipFile, name: str, destination: Path) -> None:
    _reject_unsafe_name(name)
    target = destination / name
    with bundle.open(name) as source, target.open("wb") as sink:
        shutil.copyfileobj(source, sink)


def classify_course(
    name: str,
    title: str,
    media_kind: str = "audio",
    manifest: dict[str, Any] | None = None,
) -> tuple[str, str, str, str, str]:
    """Classify a course into (category, category_name, subcategory, subcategory_name, level).

    Categories:
      - intensive: 精听课程
          - audio: 音频精听 (includes JLPT 听力精听 and other audio listening)
          - video: 视频精听 (news and remote video listening)
      - pdf: PDF课程
          - jlpt: JLPT真题 (PDF exam papers / question bank, not audio dictation)
          - textbook: 课本和课本PDF (textbooks and vocabulary/grammar packs from PDF)
    """
    name_upper = name.upper()
    title_upper = title.upper()
    name_lower = name.lower()
    title_lower = title.lower()

    # Detect level if any
    level = ""
    for lvl in ["N1", "N2", "N3", "N4", "N5"]:
        if f"-{lvl}" in name_upper or f"_{lvl}" in name_upper or lvl in title_upper:
            level = lvl
            break

    # Check whether this course is a PDF document/exam package (no audio dictation stream)
    is_pdf_source = False
    if manifest and isinstance(manifest, dict):
        source_kind = str(manifest.get("sourceKind") or "").lower()
        kind = str(manifest.get("kind") or "").lower()
        if source_kind in {"pdf", "ocr", "textbook", "exam"} or kind in {
            "exam", "grammar", "word", "document", "pdf-upload",
        }:
            is_pdf_source = True
        elif manifest.get("sourcePdf") or manifest.get("pdf"):
            is_pdf_source = True

    # 1. PDF courses (only when source is PDF and not audio dictation)
    if is_pdf_source:
        is_jlpt = bool(re.match(r"^\d{4}-\d{2}-N\d", name, re.IGNORECASE)) or "JLPT" in title_upper or "真题" in title
        if is_jlpt:
            return ("pdf", "PDF课程", "jlpt", "JLPT真题", level or "N1")
        return ("pdf", "PDF课程", "textbook", "课本和课本PDF", level)

    # 2. Video Intensive Listening (精听课程 · 视频精听)
    is_video = (
        media_kind == "remote"
        or any(tag in name_lower for tag in ["nhk", "tbs", "ann", "news", "video", "youtube"])
        or (
            manifest
            and isinstance(manifest.get("media"), dict)
            and manifest.get("media", {}).get("provider") in ["youtube", "bilibili", "video"]
        )
    )
    if is_video:
        return ("intensive", "精听课程", "video", "视频精听", level)

    # 3. Audio Intensive Listening (精听课程 · 音频精听, including JLPT 听力精听)
    return ("intensive", "精听课程", "audio", "音频精听", level)


def list_courses(courses_dir: Path) -> list[dict[str, Any]]:
    """Describe installed courses by auditing them, not by trusting them.

    A manifest carries a self-reported ``quality`` block, and this project has
    already been bitten once by reading that field instead of re-running the
    audit: a corrupted course claimed to be fine and opened anyway. So the status
    below is measured here, every time.
    """
    rows: list[dict[str, Any]] = []
    if not courses_dir.is_dir():
        return rows
    for folder in sorted(courses_dir.iterdir()):
        manifest_path = resolve_course_manifest_path(folder)
        if not manifest_path or not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            rows.append({"name": folder.name, "title": "(unreadable manifest)", "sentences": 0, "status": "broken"})
            continue
        report = audit_manifest(manifest, require_enrichment=False)
        summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        sentences = manifest.get("sentences")
        media_kind = "remote" if isinstance(manifest.get("media"), dict) else "audio"
        cat, cat_name, subcat, subcat_name, level = classify_course(
            folder.name, manifest.get("title") or "", media_kind, manifest
        )
        rows.append(
            {
                "name": folder.name,
                "title": manifest.get("title") or "",
                "sentences": len(sentences) if isinstance(sentences, list) else 0,
                "category": cat,
                "categoryName": cat_name,
                "subcategory": subcat,
                "subcategoryName": subcat_name,
                "level": level,
                "mediaKind": media_kind,
                "mediaProvider": (manifest.get("media") or {}).get("provider", "")
                if isinstance(manifest.get("media"), dict) else "",
                "status": report.get("status") or "unknown",
                "errors": summary.get("errors"),
                "warnings": summary.get("warnings"),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="install_course.py",
        description="Install a built course ZIP into courses/ so the launcher can open it.",
    )
    parser.add_argument("bundle", nargs="?", help="Path to the course ZIP.")
    parser.add_argument("--courses-dir", help=f"Destination root. Default: {DEFAULT_COURSES_DIR}")
    parser.add_argument("--name", help="Folder name to install as. Default: derived from the title.")
    parser.add_argument("--force", action="store_true", help="Replace an existing course folder.")
    parser.add_argument(
        "--allow-failed",
        action="store_true",
        help="Install even when the manifest has quality errors. The launcher will still refuse to open it.",
    )
    parser.add_argument("--list", action="store_true", help="List installed courses and exit.")
    args = parser.parse_args(argv)

    courses_dir = Path(args.courses_dir).expanduser().resolve() if args.courses_dir else DEFAULT_COURSES_DIR

    if args.list:
        rows = list_courses(courses_dir)
        if not rows:
            print(f"No courses installed in {courses_dir}")
            return 0
        print(f"Courses in {courses_dir} (status re-audited now, not read from the manifest):")
        for row in rows:
            counts = ""
            if row.get("errors") is not None:
                counts = f", errors={row['errors']}, warnings={row.get('warnings', 0)}"
            print(f"  {row['name']:<28} {row['sentences']:>4} sentences  [{row['status']}{counts}]  {row['title']}")
        return 0

    if not args.bundle:
        parser.error("a bundle path is required (or use --list)")

    destination = install_bundle(
        Path(args.bundle),
        courses_dir=courses_dir,
        course_name=args.name,
        force=args.force,
        allow_failed=args.allow_failed,
    )
    print(f"Installed: {destination}")
    print(f'Play it with: python .\\start_dictation.py --manifest "{destination / "manifest.json"}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
