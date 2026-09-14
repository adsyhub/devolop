#!/usr/bin/env python3
"""Read-only inventory of workbench assets, artifacts, quality decisions, and duplicates.

Matches the baseline requirements in docs/DICTATION_WORKBENCH_AUTOMATION_PLAN.md.
Never alters files, runs destructive tasks, or reads secrets.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from bundle_quality import audit_manifest
    from lexicon_schema import audit_pack
    from lexicon_exercise import qualification, review_state
    from exam_schema import audit_exam
except ImportError as exc:
    sys.stderr.write(f"Warning: could not import audit modules: {exc}\n")
    audit_manifest = None  # type: ignore
    audit_pack = None  # type: ignore
    qualification = None  # type: ignore
    review_state = None  # type: ignore
    audit_exam = None  # type: ignore


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json_safe(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def collect_inventory(root: Path) -> dict[str, Any]:
    courses_dir = root / "courses"
    lexicon_dir = root / "lexicon"
    exams_dir = root / "exams"
    builds_dir = root / "studio-work" / "builds"

    # 1. Courses
    course_items = []
    course_quality_counts = Counter()
    course_issue_counts = Counter()
    total_sentences = 0
    total_workbench_reviewed = 0
    pending_courses = 0

    if courses_dir.is_dir():
        for manifest_path in sorted(courses_dir.glob("*/manifest.json")):
            data = read_json_safe(manifest_path)
            if not data or not isinstance(data, dict):
                continue
            course_id = manifest_path.parent.name
            title = str(data.get("title") or course_id)
            sentences = [s for s in data.get("sentences", []) if isinstance(s, dict)]
            total_sentences += len(sentences)

            # Workbench edits
            bmeta = data.get("buildMetadata") if isinstance(data.get("buildMetadata"), dict) else {}
            edits = bmeta.get("workbenchEdits") if isinstance(bmeta.get("workbenchEdits"), dict) else {}
            recorded = edits.get("sentenceIds") if isinstance(edits.get("sentenceIds"), list) else []
            known_ids = {str(s.get("id") or "") for s in sentences}
            reviewed = (
                len(set(map(str, recorded)) & known_ids)
                if recorded
                else min(len(sentences), int(edits.get("count") or 0))
            )
            total_workbench_reviewed += reviewed
            is_pending = reviewed < len(sentences)
            if is_pending:
                pending_courses += 1

            # Quality audit
            audit_status = "unknown"
            course_issues = []
            if audit_manifest:
                report = audit_manifest(data, require_enrichment=True)
                audit_status = report.get("status", "unknown")
                for issue in report.get("issues", []):
                    code = issue.get("code", "unknown")
                    course_issue_counts[code] += 1
                    course_issues.append(code)
            course_quality_counts[audit_status] += 1

            manifest_hash = file_sha256(manifest_path)
            audio_name = str(data.get("audio") or "")
            audio_path = manifest_path.parent / audio_name if audio_name else None
            audio_hash = file_sha256(audio_path) if (audio_path and audio_path.is_file()) else ""

            course_items.append({
                "id": course_id,
                "title": title,
                "sentences": len(sentences),
                "workbenchReviewed": reviewed,
                "pending": is_pending,
                "qualityStatus": audit_status,
                "manifestSha256": manifest_hash,
                "audioSha256": audio_hash,
                "issueCodes": sorted(set(course_issues)),
            })

    # 2. PDF Drafts
    draft_items = []
    draft_status_counts = Counter()
    draft_kind_counts = Counter()
    review_required_count = 0
    total_draft_pages = 0
    total_build_folders = 0

    if builds_dir.is_dir():
        for build_folder in sorted(builds_dir.iterdir()):
            if not build_folder.is_dir():
                continue
            total_build_folders += 1
            result_path = build_folder / "build-result.json"
            if not result_path.is_file():
                draft_items.append({
                    "buildId": build_folder.name,
                    "hasResult": False,
                    "status": "missing_result",
                })
                continue
            result = read_json_safe(result_path) or {}
            status = str(result.get("status", "unknown"))
            draft_status_counts[status] += 1
            kind = str(result.get("kind", "unknown"))
            draft_kind_counts[kind] += 1
            review_req = bool(result.get("reviewRequired"))
            if review_req:
                review_required_count += 1

            pages_count = 0
            draft_path_str = result.get("draftPath")
            if draft_path_str:
                pages_dir = Path(draft_path_str) / "pages"
                if not pages_dir.is_dir() and not Path(draft_path_str).is_absolute():
                    pages_dir = root / draft_path_str / "pages"
                if pages_dir.is_dir():
                    pages_count = len(list(pages_dir.glob("*.json")))
            total_draft_pages += pages_count

            draft_items.append({
                "buildId": build_folder.name,
                "hasResult": True,
                "kind": kind,
                "status": status,
                "reviewRequired": review_req,
                "pages": pages_count,
            })

    # 3. Lexicon
    lexicon_items = []
    lexicon_quality_counts = Counter()
    lexicon_states = Counter()
    lexicon_reasons = Counter()
    total_entries = 0
    total_templates = 0
    total_qualified_templates = 0

    if lexicon_dir.is_dir():
        for pack_path in sorted(lexicon_dir.glob("*/pack.json")):
            pack = read_json_safe(pack_path)
            if not pack or not isinstance(pack, dict):
                continue
            pack_id = pack_path.parent.name
            entries = pack.get("entries", [])
            total_entries += len(entries)

            pack_quality = "unknown"
            if audit_pack:
                report = audit_pack(pack)
                pack_quality = report.get("status", "unknown")
            lexicon_quality_counts[pack_quality] += 1

            pack_templates = 0
            pack_qualified = 0
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                for tmpl in entry.get("exerciseTemplates", []):
                    pack_templates += 1
                    total_templates += 1
                    if qualification:
                        passed, codes = qualification(tmpl)
                        if passed:
                            pack_qualified += 1
                            total_qualified_templates += 1
                        for c in codes:
                            lexicon_reasons[c] += 1
                    if review_state:
                        lexicon_states[review_state(tmpl)] += 1

            lexicon_items.append({
                "packId": pack_id,
                "entries": len(entries),
                "templates": pack_templates,
                "qualifiedTemplates": pack_qualified,
                "qualityStatus": pack_quality,
            })

    # 4. Exams
    exam_items = []
    exam_quality_counts = Counter()
    if exams_dir.is_dir():
        for exam_path in sorted(exams_dir.glob("*/exam.json")):
            exam_data = read_json_safe(exam_path)
            if not exam_data or not isinstance(exam_data, dict):
                continue
            exam_id = exam_path.parent.name
            exam_quality = "unknown"
            if audit_exam:
                report = audit_exam(exam_data)
                exam_quality = report.get("status", "unknown")
            exam_quality_counts[exam_quality] += 1
            exam_items.append({
                "examId": exam_id,
                "qualityStatus": exam_quality,
            })

    # 5. Duplicates detection by sha256
    sha_map: dict[str, list[str]] = {}
    for search_dir in [courses_dir, root / "studio-work"]:
        if not search_dir.is_dir():
            continue
        for p in search_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".mp3", ".m4a", ".wav", ".mp4", ".pdf", ".json"}:
                if ".git" in p.parts or "node_modules" in p.parts:
                    continue
                try:
                    if p.stat().st_size > 100 * 1024 * 1024:
                        continue
                    h = file_sha256(p)
                    sha_map.setdefault(h, []).append(str(p.relative_to(root)))
                except Exception:
                    pass
    duplicates = {h: paths for h, paths in sha_map.items() if len(paths) > 1}

    return {
        "summary": {
            "courses": {
                "count": len(course_items),
                "totalSentences": total_sentences,
                "workbenchReviewed": total_workbench_reviewed,
                "pendingCourses": pending_courses,
                "quality": dict(course_quality_counts),
                "topIssues": dict(course_issue_counts.most_common(10)),
            },
            "pdfDrafts": {
                "totalFolders": total_build_folders,
                "results": len(draft_items),
                "reviewRequired": review_required_count,
                "totalPages": total_draft_pages,
                "statusCounts": dict(draft_status_counts),
                "kinds": dict(draft_kind_counts),
            },
            "lexicon": {
                "packs": len(lexicon_items),
                "entries": total_entries,
                "templates": total_templates,
                "qualifiedTemplates": total_qualified_templates,
                "quality": dict(lexicon_quality_counts),
                "states": dict(lexicon_states),
                "reasons": dict(lexicon_reasons),
            },
            "exams": {
                "count": len(exam_items),
                "quality": dict(exam_quality_counts),
            },
            "duplicateCount": len(duplicates),
        },
        "courses": course_items,
        "drafts": draft_items,
        "lexicon": lexicon_items,
        "exams": exam_items,
        "duplicates": duplicates,
    }


def format_markdown(data: dict[str, Any]) -> str:
    s = data["summary"]
    lines = [
        "# Dictation Workbench Assets & Quality Inventory",
        "",
        "## 1. Courses",
        f"- Installed courses: {s['courses']['count']}",
        f"- Total sentences: {s['courses']['totalSentences']}",
        f"- Sentences with workbench edit record: {s['courses']['workbenchReviewed']}",
        f"- Courses marked pending by legacy logic: {s['courses']['pendingCourses']}",
        f"- Quality audit (require_enrichment=True): {s['courses']['quality']}",
        f"- Top issues: {s['courses']['topIssues']}",
        "",
        "## 2. PDF Drafts",
        f"- Total build folders: {s['pdfDrafts']['totalFolders']}",
        f"- Builds with results: {s['pdfDrafts']['results']}",
        f"- Marked reviewRequired: {s['pdfDrafts']['reviewRequired']}",
        f"- Total draft pages: {s['pdfDrafts']['totalPages']}",
        f"- Kinds: {s['pdfDrafts']['kinds']}",
        f"- Statuses: {s['pdfDrafts']['statusCounts']}",
        "",
        "## 3. Lexicon",
        f"- Packs: {s['lexicon']['packs']}",
        f"- Entries: {s['lexicon']['entries']}",
        f"- Authored templates: {s['lexicon']['templates']}",
        f"- Formally qualified templates: {s['lexicon']['qualifiedTemplates']}",
        f"- Pack quality: {s['lexicon']['quality']}",
        f"- Review states: {s['lexicon']['states']}",
        "",
        "## 4. Exams",
        f"- Exam files: {s['exams']['count']}",
        f"- Quality statuses: {s['exams']['quality']}",
        "",
        "## 5. Duplicate Hashes",
        f"- Duplicate content groups identified: {s['duplicateCount']}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Workbench assets and quality inventory.")
    parser.add_argument("--json", action="store_true", help="Output as JSON.")
    parser.add_argument("--markdown", action="store_true", help="Output as Markdown.")
    parser.add_argument("--out", type=str, default="", help="Optional output file path.")
    parser.add_argument("--root", type=str, default=str(PROJECT_ROOT), help="Project root directory.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    data = collect_inventory(root)

    if args.json or (not args.markdown and not args.out.endswith(".md")):
        out_str = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        out_str = format_markdown(data)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_str, encoding="utf-8")
        print(f"Wrote inventory to {out_path}")
    else:
        print(out_str)


if __name__ == "__main__":
    main()

