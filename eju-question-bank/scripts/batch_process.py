#!/usr/bin/env python3
"""Batch process all EJU PAPER PDFs through the question bank pipeline.

Usage:
    python scripts/batch_process.py source-init   # Phase 1: create source manifests
    python scripts/batch_process.py probe          # Phase 2: probe all PDFs
    python scripts/batch_process.py render         # Phase 3: render all PDFs
    python scripts/batch_process.py extract        # Phase 4: OCR/VLM extract
    python scripts/batch_process.py assemble       # Phase 5: assemble papers
    python scripts/batch_process.py status         # Show progress summary
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

@dataclass
class ExamFile:
    """A parsed PAPER PDF file."""
    path: Path
    year: int
    session: int  # 1 or 2
    subject: str  # SCIENCE, MATHEMATICS, JAPAN_AND_WORLD, JAPANESE
    role: str     # QUESTION_BOOKLET, ANSWER_KEY, TRANSCRIPT
    course: str | None = None  # COURSE_1, COURSE_2 for math
    language: str = "ja"

    @property
    def session_code(self) -> str:
        return f"{self.year}-{self.session}"

    @property
    def work_dir_name(self) -> str:
        subject_map = {
            ("MATHEMATICS", "COURSE_1"): "math-c1",
            ("MATHEMATICS", "COURSE_2"): "math-c2",
            "SCIENCE": "science",
            "JAPAN_AND_WORLD": "japan-world",
            "JAPANESE": "japanese",
        }
        key = (self.subject, self.course) if self.course else self.subject
        short = subject_map.get(key, self.subject.lower())
        return f"{self.year}-{self.session}-{short}"

    @property
    def inventory_id(self) -> str:
        subject_map = {
            ("MATHEMATICS", "COURSE_1"): "math-c1",
            ("MATHEMATICS", "COURSE_2"): "math-c2",
            "SCIENCE": "science",
            "JAPAN_AND_WORLD": "japan-world",
            "JAPANESE": "japanese",
        }
        key = (self.subject, self.course) if self.course else self.subject
        short = subject_map.get(key, self.subject.lower())
        return f"eju-{self.year}-{self.session}-{short}-{self.language}"

    @property
    def expected_forms(self) -> list[str]:
        lang = self.language.upper()
        if self.subject == "SCIENCE":
            return [f"PHYSICS_{lang}", f"CHEMISTRY_{lang}", f"BIOLOGY_{lang}"]
        if self.subject == "MATHEMATICS":
            return [f"MATHEMATICS_{self.course}_{lang}"]
        if self.subject == "JAPAN_AND_WORLD":
            return [f"JAPAN_AND_WORLD_{lang}"]
        if self.subject == "JAPANESE":
            return ["JAPANESE_JA"]
        return []

    @property
    def syllabus_version(self) -> str:
        if self.subject == "JAPANESE":
            return "japanese-2015" if self.year >= 2015 else "japanese-2002"
        return "basic-2015" if self.year >= 2015 else "basic-2002"


@dataclass
class ExamSession:
    """A grouped exam session with question booklet + optional answer key."""
    year: int
    session: int
    subject: str
    course: str | None
    language: str
    question_booklet: ExamFile | None = None
    answer_key: ExamFile | None = None
    transcript: ExamFile | None = None
    audio_files: list[Path] = field(default_factory=list)

    @property
    def session_code(self) -> str:
        return f"{self.year}-{self.session}"

    @property
    def work_dir_name(self) -> str:
        if self.question_booklet:
            return self.question_booklet.work_dir_name
        subject_map = {
            ("MATHEMATICS", "COURSE_1"): "math-c1",
            ("MATHEMATICS", "COURSE_2"): "math-c2",
            "SCIENCE": "science",
            "JAPAN_AND_WORLD": "japan-world",
            "JAPANESE": "japanese",
        }
        key = (self.subject, self.course) if self.course else self.subject
        short = subject_map.get(key, self.subject.lower())
        return f"{self.year}-{self.session}-{short}"

    @property
    def inventory_id(self) -> str:
        if self.question_booklet:
            return self.question_booklet.inventory_id
        return ""


def parse_year_session(name: str) -> tuple[int, int]:
    """Extract year and session number from filename."""
    # Extract Western year
    m = re.match(r"(\d{4})", name)
    if not m:
        raise ValueError(f"Cannot parse year from: {name}")
    year = int(m.group(1))

    # Extract session (第1回/第2回/第一回/第二回)
    session_match = re.search(r"第([12一二])回", name)
    if session_match:
        s = session_match.group(1)
        session = 1 if s in ("1", "一") else 2
    else:
        # 2024 and some years have only one session
        session = 1
    return year, session


def is_answer_file(name: str) -> bool:
    """Check if the filename indicates an answer key."""
    return "答案" in name


def scan_math1(paper_dir: Path) -> list[ExamFile]:
    """Scan EJU文科数学（数学1）."""
    folder = paper_dir / "EJU文科数学（数学1）"
    if not folder.exists():
        return []
    files = []
    for pdf in sorted(folder.glob("*.pdf")):
        year, session = parse_year_session(pdf.name)
        role = "ANSWER_KEY" if is_answer_file(pdf.name) else "QUESTION_BOOKLET"
        files.append(ExamFile(
            path=pdf, year=year, session=session,
            subject="MATHEMATICS", role=role, course="COURSE_1"
        ))
    return files


def scan_math2(paper_dir: Path) -> list[ExamFile]:
    """Scan EJU理科数学（数学2）, skipping (1) duplicates."""
    folder = paper_dir / "EJU理科数学（数学2）"
    if not folder.exists():
        return []
    files = []
    for pdf in sorted(folder.glob("*.pdf")):
        # Skip duplicate (1) files
        if "(1)" in pdf.name:
            continue
        year, session = parse_year_session(pdf.name)
        role = "ANSWER_KEY" if is_answer_file(pdf.name) else "QUESTION_BOOKLET"
        files.append(ExamFile(
            path=pdf, year=year, session=session,
            subject="MATHEMATICS", role=role, course="COURSE_2"
        ))
    return files


def scan_science(paper_dir: Path) -> list[ExamFile]:
    """Scan EJU理综."""
    folder = paper_dir / "EJU理综"
    if not folder.exists():
        return []
    files = []
    for pdf in sorted(folder.glob("*.pdf")):
        year, session = parse_year_session(pdf.name)
        role = "ANSWER_KEY" if is_answer_file(pdf.name) else "QUESTION_BOOKLET"
        files.append(ExamFile(
            path=pdf, year=year, session=session,
            subject="SCIENCE", role=role
        ))
    return files


def scan_japan_world(paper_dir: Path) -> list[ExamFile]:
    """Scan EJU文综."""
    folder = paper_dir / "EJU文综"
    if not folder.exists():
        return []
    files = []
    for pdf in sorted(folder.glob("*.pdf")):
        year, session = parse_year_session(pdf.name)
        role = "ANSWER_KEY" if is_answer_file(pdf.name) else "QUESTION_BOOKLET"
        files.append(ExamFile(
            path=pdf, year=year, session=session,
            subject="JAPAN_AND_WORLD", role=role
        ))
    return files


def scan_japanese(paper_dir: Path) -> list[ExamFile]:
    """Scan EJU日语 (questions, answers, transcripts)."""
    base = paper_dir / "EJU日语"
    if not base.exists():
        return []
    files = []

    # Questions and answers
    questions_dir = base / "EJU日语题目"
    if questions_dir.exists():
        for pdf in sorted(questions_dir.glob("*.pdf")):
            year, session = parse_year_session(pdf.name)
            role = "ANSWER_KEY" if is_answer_file(pdf.name) else "QUESTION_BOOKLET"
            files.append(ExamFile(
                path=pdf, year=year, session=session,
                subject="JAPANESE", role=role
            ))

    # Transcripts
    transcript_dir = base / "EJU日语听力原文"
    if transcript_dir.exists():
        for pdf in sorted(transcript_dir.glob("*.pdf")):
            year, session = parse_year_session(pdf.name)
            files.append(ExamFile(
                path=pdf, year=year, session=session,
                subject="JAPANESE", role="TRANSCRIPT"
            ))

    return files


def discover_audio(paper_dir: Path) -> dict[tuple[int, int], list[Path]]:
    """Discover audio files for Japanese sessions."""
    audio_dir = paper_dir / "EJU日语" / "EJU日语听力音频"
    result: dict[tuple[int, int], list[Path]] = {}
    if not audio_dir.exists():
        return result

    # Top-level MP3s (e.g., 2024年令和6年日语音频.mp3)
    for mp3 in audio_dir.glob("*.mp3"):
        try:
            year, session = parse_year_session(mp3.name)
            result.setdefault((year, session), []).append(mp3)
        except ValueError:
            pass

    # Subdirectories with audio files
    for subdir in sorted(audio_dir.iterdir()):
        if not subdir.is_dir():
            continue
        try:
            year, session = parse_year_session(subdir.name)
        except ValueError:
            continue
        audio_files = sorted(subdir.glob("*.mp3")) + sorted(subdir.glob("*.m4a")) + sorted(subdir.glob("*.wav"))
        if audio_files:
            result.setdefault((year, session), []).extend(audio_files)

    return result


def group_into_sessions(files: list[ExamFile], audio: dict[tuple[int, int], list[Path]] | None = None) -> list[ExamSession]:
    """Group parsed files into exam sessions."""
    sessions: dict[str, ExamSession] = {}

    for f in files:
        key = f"{f.year}-{f.session}-{f.subject}-{f.course or ''}"
        if key not in sessions:
            sessions[key] = ExamSession(
                year=f.year, session=f.session,
                subject=f.subject, course=f.course,
                language=f.language
            )
        s = sessions[key]
        if f.role == "QUESTION_BOOKLET":
            s.question_booklet = f
        elif f.role == "ANSWER_KEY":
            s.answer_key = f
        elif f.role == "TRANSCRIPT":
            s.transcript = f

    # Attach audio to Japanese sessions
    if audio:
        for key, s in sessions.items():
            if s.subject == "JAPANESE":
                audio_key = (s.year, s.session)
                if audio_key in audio:
                    s.audio_files = audio[audio_key]

    return sorted(sessions.values(), key=lambda s: (s.year, s.session, s.subject, s.course or ""))


def discover_all(paper_dir: Path) -> list[ExamSession]:
    """Discover all exam sessions from PAPER directory."""
    paper_dir = Path(paper_dir).resolve()
    all_files: list[ExamFile] = []
    all_files.extend(scan_math1(paper_dir))
    all_files.extend(scan_math2(paper_dir))
    all_files.extend(scan_science(paper_dir))
    all_files.extend(scan_japan_world(paper_dir))
    all_files.extend(scan_japanese(paper_dir))

    audio = discover_audio(paper_dir)
    return group_into_sessions(all_files, audio)


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

def ensure_sources_link(session: ExamSession, project_root: Path) -> dict[str, Path]:
    """Create sources/ symlinks or copies for the session's PDFs."""
    sources_dir = project_root / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    result = {}
    for role, exam_file in [("QUESTION_BOOKLET", session.question_booklet),
                             ("ANSWER_KEY", session.answer_key)]:
        if exam_file is None:
            continue
        target = sources_dir / exam_file.path.name
        if not target.exists():
            # Create symlink to avoid copying large files
            target.symlink_to(exam_file.path.resolve())
        result[role] = target
    return result


def run_source_init(session: ExamSession, project_root: Path) -> dict[str, Any] | None:
    """Create source manifest for a session."""
    from eju_bank.source import create_source_manifest

    work_dir = project_root / "work" / session.work_dir_name
    manifest_path = work_dir / "source-manifest.json"

    # Skip if already exists
    if manifest_path.exists():
        from eju_bank.util import load_json
        return load_json(manifest_path)

    if session.question_booklet is None:
        return None

    work_dir.mkdir(parents=True, exist_ok=True)
    sources = ensure_sources_link(session, project_root)

    qb_path = sources.get("QUESTION_BOOKLET")
    ak_path = sources.get("ANSWER_KEY")
    if qb_path is None:
        return None

    manifest = create_source_manifest(
        session=session.session_code,
        subject=session.subject,
        language=session.language,
        syllabus_version=session.question_booklet.syllabus_version,
        question_booklet=qb_path,
        answer_key=ak_path,
        rights_status="PRIVATE_STUDY",
        rights_note=f"EJU {session.session_code} {session.subject} personal study copy",
        output_path=manifest_path,
    )
    # Add inventory and expected forms
    manifest["inventoryId"] = session.inventory_id
    ef = session.question_booklet.expected_forms
    manifest["expectedForms"] = ef
    from eju_bank.util import write_json
    write_json(manifest_path, manifest)
    return manifest


def run_probe(session: ExamSession, project_root: Path) -> dict[str, Any] | None:
    """Probe PDFs for a session."""
    from eju_bank.pdf_pipeline import probe_manifest
    from eju_bank.util import load_json

    work_dir = project_root / "work" / session.work_dir_name
    manifest_path = work_dir / "source-manifest.json"
    probe_path = work_dir / "probe.json"

    if not manifest_path.exists():
        return None
    if probe_path.exists():
        return load_json(probe_path)

    return probe_manifest(manifest_path, probe_path)


def run_render(session: ExamSession, project_root: Path, role: str = "QUESTION_BOOKLET") -> dict[str, Any] | None:
    """Render PDF pages for a session."""
    from eju_bank.pdf_pipeline import render_manifest
    from eju_bank.util import load_json

    work_dir = project_root / "work" / session.work_dir_name
    manifest_path = work_dir / "source-manifest.json"
    render_dir = work_dir / "renders"
    index_path = render_dir / f"render-index-{role.lower()}.json"

    if not manifest_path.exists():
        return None

    # Check if role exists in manifest
    manifest = load_json(manifest_path)
    roles = [f["role"] for f in manifest.get("files", [])]
    if role not in roles:
        return None

    if index_path.exists():
        return load_json(index_path)

    return render_manifest(manifest_path, role=role, output_dir=render_dir)


def run_extract(session: ExamSession, project_root: Path, provider_name: str,
                role: str = "QUESTION_BOOKLET", provider_instance: Any | None = None) -> dict[str, Any] | None:
    """Extract page contracts using VLM."""
    from eju_bank.ocr.pipeline import extract_pages
    from eju_bank.util import load_json

    work_dir = project_root / "work" / session.work_dir_name
    manifest_path = work_dir / "source-manifest.json"
    render_dir = work_dir / "renders"
    pages_dir = work_dir / "pages"
    index_path = render_dir / f"render-index-{role.lower()}.json"
    quality_path = pages_dir / f"quality-report-{role.lower()}.json"

    if not manifest_path.exists() or not index_path.exists():
        return None

    # Skip if already extracted successfully
    if quality_path.exists():
        report = load_json(quality_path)
        if report.get("status") == "passed":
            return report

    config_path = project_root / "config" / "providers.json"

    return extract_pages(
        manifest_path=manifest_path,
        render_index_path=index_path,
        output_dir=pages_dir,
        provider=provider_instance,
        provider_config=config_path if provider_instance is None else None,
        provider_name=provider_name if provider_instance is None else None,
        retry_failed=True,
    )


def run_assemble(session: ExamSession, project_root: Path) -> dict[str, Any] | None:
    """Assemble paper from extracted pages."""
    from eju_bank.assemble import assemble_paper
    from eju_bank.answers import answers_from_page_contracts
    from eju_bank.util import load_json, write_json

    work_dir = project_root / "work" / session.work_dir_name
    manifest_path = work_dir / "source-manifest.json"
    pages_dir = work_dir / "pages"
    answers_path = work_dir / "answers.json"
    paper_path = work_dir / "paper.json"

    if not manifest_path.exists() or not pages_dir.exists():
        return None

    # Skip if already assembled
    if paper_path.exists():
        return load_json(paper_path)

    # Generate answers from pages if not yet done
    if not answers_path.exists():
        answers = answers_from_page_contracts(pages_dir)
        write_json(answers_path, answers)

    answer_ledger = answers_path if answers_path.exists() else None

    return assemble_paper(
        manifest_path=manifest_path,
        pages_dir=pages_dir,
        answer_ledger_path=answer_ledger,
        output_path=paper_path,
    )


# ---------------------------------------------------------------------------
# Inventory management
# ---------------------------------------------------------------------------

def update_inventory(sessions: list[ExamSession], project_root: Path) -> None:
    """Update content-inventory.json with all sessions."""
    from eju_bank.util import load_json, write_json, utc_now

    inv_path = project_root / "content" / "content-inventory.json"
    if inv_path.exists():
        inventory = load_json(inv_path)
    else:
        inventory = {"schemaVersion": 1, "updatedAt": utc_now(), "items": []}

    existing_ids = {item["inventoryId"] for item in inventory["items"]}

    for s in sessions:
        if s.question_booklet is None:
            continue
        inv_id = s.inventory_id
        if inv_id in existing_ids:
            continue

        blocking = []
        if s.answer_key is None:
            blocking.append("MISSING_ANSWER")
        if s.subject == "JAPANESE" and not s.audio_files:
            blocking.append("MISSING_AUDIO")

        required_files = ["QUESTION_BOOKLET", "ANSWER_KEY"]
        if s.subject == "JAPANESE":
            required_files.append("AUDIO")

        optional_files = []
        if s.subject == "JAPANESE":
            optional_files.append("TRANSCRIPT")

        status = "DISCOVERED"
        if s.question_booklet:
            status = "RECEIVED"

        item = {
            "inventoryId": inv_id,
            "session": s.session_code,
            "subject": s.subject,
            "language": s.language,
            "syllabusId": s.question_booklet.syllabus_version,
            "requiredFiles": required_files,
            "optionalFiles": optional_files,
            "rightsStatus": "PRIVATE_STUDY",
            "pipelineStatus": status,
            "expectedForms": s.question_booklet.expected_forms,
            "blockingIssues": blocking,
            "notes": f"{s.year}年第{s.session}回 {s.subject}"
                     + (f" Course {s.course[-1]}" if s.course else ""),
        }
        inventory["items"].append(item)
        existing_ids.add(inv_id)

    inventory["updatedAt"] = utc_now()
    inv_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(inv_path, inventory)
    print(f"  Inventory: {len(inventory['items'])} items total")


# ---------------------------------------------------------------------------
# Status reporting
# ---------------------------------------------------------------------------

def show_status(sessions: list[ExamSession], project_root: Path) -> None:
    """Print progress summary."""
    from eju_bank.util import load_json

    stats = {
        "total": 0, "has_qb": 0, "has_ak": 0,
        "manifested": 0, "probed": 0, "rendered": 0,
        "extracted": 0, "assembled": 0,
    }
    by_subject: dict[str, dict[str, int]] = {}

    for s in sessions:
        stats["total"] += 1
        subj_key = f"{s.subject}" + (f"_{s.course}" for _ in [0] if s.course).__next__() if s.course else s.subject
        if subj_key not in by_subject:
            by_subject[subj_key] = {"total": 0, "has_ak": 0, "manifested": 0, "probed": 0,
                                     "rendered": 0, "extracted": 0, "assembled": 0}
        by_subject[subj_key]["total"] += 1

        if s.question_booklet:
            stats["has_qb"] += 1
        if s.answer_key:
            stats["has_ak"] += 1
            by_subject[subj_key]["has_ak"] += 1

        work_dir = project_root / "work" / s.work_dir_name
        if (work_dir / "source-manifest.json").exists():
            stats["manifested"] += 1
            by_subject[subj_key]["manifested"] += 1
        if (work_dir / "probe.json").exists():
            stats["probed"] += 1
            by_subject[subj_key]["probed"] += 1
        if (work_dir / "renders" / "render-index-question_booklet.json").exists():
            stats["rendered"] += 1
            by_subject[subj_key]["rendered"] += 1
        quality = work_dir / "pages" / "quality-report-question_booklet.json"
        if quality.exists():
            stats["extracted"] += 1
            by_subject[subj_key]["extracted"] += 1
        if (work_dir / "paper.json").exists():
            stats["assembled"] += 1
            by_subject[subj_key]["assembled"] += 1

    print("\n=== EJU Batch Processing Status ===\n")
    print(f"Total sessions discovered: {stats['total']}")
    print(f"  With question booklet:   {stats['has_qb']}")
    print(f"  With answer key:         {stats['has_ak']}")
    print(f"  Source manifests created: {stats['manifested']}")
    print(f"  Probed:                  {stats['probed']}")
    print(f"  Rendered:                {stats['rendered']}")
    print(f"  Extracted (OCR):         {stats['extracted']}")
    print(f"  Assembled:               {stats['assembled']}")

    print(f"\n{'Subject':<25} {'Total':>6} {'Ans':>6} {'Mnfst':>6} {'Probe':>6} {'Rndr':>6} {'OCR':>6} {'Asm':>6}")
    print("-" * 85)
    for subj, s in sorted(by_subject.items()):
        print(f"{subj:<25} {s['total']:>6} {s['has_ak']:>6} {s['manifested']:>6} {s['probed']:>6} {s['rendered']:>6} {s['extracted']:>6} {s['assembled']:>6}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    paper_dir = PROJECT_ROOT / "PAPER"
    provider_name = sys.argv[2] if len(sys.argv) > 2 else "glm4v-local"

    print(f"Discovering PAPER directory: {paper_dir}")
    sessions = discover_all(paper_dir)
    print(f"Found {len(sessions)} exam sessions\n")

    if command == "status":
        show_status(sessions, PROJECT_ROOT)
        return

    if command == "source-init":
        print("=== Phase 1: Source Init ===\n")
        update_inventory(sessions, PROJECT_ROOT)
        ok, fail = 0, 0
        for s in sessions:
            if s.question_booklet is None:
                continue
            try:
                result = run_source_init(s, PROJECT_ROOT)
                if result:
                    ok += 1
                    print(f"  ✓ {s.work_dir_name}: {result['sourceId']}")
            except Exception as e:
                fail += 1
                print(f"  ✗ {s.work_dir_name}: {e}")
        print(f"\nDone: {ok} succeeded, {fail} failed")
        return

    if command == "probe":
        print("=== Phase 2: Probe ===\n")
        ok, fail, skip = 0, 0, 0
        for s in sessions:
            work_dir = PROJECT_ROOT / "work" / s.work_dir_name
            if not (work_dir / "source-manifest.json").exists():
                skip += 1
                continue
            try:
                result = run_probe(s, PROJECT_ROOT)
                if result:
                    total_pages = sum(f.get("pageCount", 0) for f in result.get("files", []))
                    ok += 1
                    print(f"  ✓ {s.work_dir_name}: {total_pages} pages")
            except Exception as e:
                fail += 1
                print(f"  ✗ {s.work_dir_name}: {e}")
        print(f"\nDone: {ok} probed, {fail} failed, {skip} skipped")
        return

    if command == "render":
        print("=== Phase 3: Render ===\n")
        ok, fail, skip = 0, 0, 0
        for s in sessions:
            work_dir = PROJECT_ROOT / "work" / s.work_dir_name
            if not (work_dir / "source-manifest.json").exists():
                skip += 1
                continue
            try:
                # Render question booklet
                result = run_render(s, PROJECT_ROOT, "QUESTION_BOOKLET")
                if result:
                    print(f"  ✓ {s.work_dir_name} QB: {len(result.get('pages', []))} pages")
                # Render answer key if exists
                result2 = run_render(s, PROJECT_ROOT, "ANSWER_KEY")
                if result2:
                    print(f"  ✓ {s.work_dir_name} AK: {len(result2.get('pages', []))} pages")
                ok += 1
            except Exception as e:
                fail += 1
                print(f"  ✗ {s.work_dir_name}: {e}")
        print(f"\nDone: {ok} rendered, {fail} failed, {skip} skipped")
        return

    if command == "extract":
        print(f"=== Phase 4: Extract (provider: {provider_name}) ===\n")
        # Filter support
        filter_str = None
        answers_only = False
        for arg in sys.argv[2:]:
            if arg == "--answers-only":
                answers_only = True
            elif not arg.startswith("--") and arg != provider_name:
                filter_str = arg
            elif arg.startswith("--filter="):
                filter_str = arg.split("=", 1)[1]

        target_sessions = sessions
        if filter_str:
            target_sessions = [s for s in target_sessions if filter_str.lower() in s.work_dir_name.lower()]
            print(f"Filtered by '{filter_str}': {len(target_sessions)} sessions selected")
        if answers_only:
            target_sessions = [s for s in target_sessions if s.answer_key is not None]
            print(f"Filtered by --answers-only: {len(target_sessions)} sessions selected")

        from eju_bank.ocr.providers import provider_from_config
        config_path = PROJECT_ROOT / "config" / "providers.json"
        print(f"Loading provider {provider_name} once for all sessions...")
        provider_instance = provider_from_config(config_path, provider_name)
        print("Provider loaded and ready for batch inference.\n")

        ok, fail, skip = 0, 0, 0
        for s in target_sessions:
            work_dir = PROJECT_ROOT / "work" / s.work_dir_name
            index_path = work_dir / "renders" / "render-index-question_booklet.json"
            if not index_path.exists():
                skip += 1
                continue
            try:
                result = run_extract(s, PROJECT_ROOT, provider_name, "QUESTION_BOOKLET", provider_instance=provider_instance)
                if result:
                    pages = result.get("pages", [])
                    passed = sum(1 for p in pages if p.get("status") == "passed")
                    print(f"  ✓ {s.work_dir_name} QB: {passed}/{len(pages)} pages passed")
                # Extract answer key
                ak_index = work_dir / "renders" / "render-index-answer_key.json"
                if ak_index.exists():
                    result2 = run_extract(s, PROJECT_ROOT, provider_name, "ANSWER_KEY", provider_instance=provider_instance)
                    if result2:
                        pages = result2.get("pages", [])
                        passed = sum(1 for p in pages if p.get("status") == "passed")
                        print(f"  ✓ {s.work_dir_name} AK: {passed}/{len(pages)} pages passed")
                ok += 1
            except Exception as e:
                fail += 1
                print(f"  ✗ {s.work_dir_name}: {e}")
                traceback.print_exc()
        print(f"\nDone: {ok} extracted, {fail} failed, {skip} skipped")
        return

    if command == "assemble":
        print("=== Phase 5: Assemble ===\n")
        ok, fail, skip = 0, 0, 0
        for s in sessions:
            work_dir = PROJECT_ROOT / "work" / s.work_dir_name
            pages_dir = work_dir / "pages"
            if not pages_dir.exists():
                skip += 1
                continue
            try:
                result = run_assemble(s, PROJECT_ROOT)
                if result:
                    forms = result.get("forms", [])
                    total_q = sum(
                        len(g.get("questions", []))
                        for f in forms for g in f.get("groups", [])
                    )
                    print(f"  ✓ {s.work_dir_name}: {len(forms)} forms, {total_q} questions")
                    ok += 1
            except Exception as e:
                fail += 1
                print(f"  ✗ {s.work_dir_name}: {e}")
        print(f"\nDone: {ok} assembled, {fail} failed, {skip} skipped")
        return

    print(f"Unknown command: {command}")
    print(__doc__)
    sys.exit(1)


if __name__ == "__main__":
    main()

