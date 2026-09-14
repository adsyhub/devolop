"""Probe and index all 2024 source booklets."""

from pathlib import Path
from eju_bank.source import create_source_manifest
from eju_bank.pdf_pipeline import probe_manifest

def main():
    ROOT = Path(__file__).resolve().parents[1]
    sources_dir = ROOT / "sources"
    work_root = ROOT / "work"
    
    targets = [
        {
            "id": "2024-1-science",
            "session": "2024-1",
            "subject": "SCIENCE",
            "language": "ja",
            "syllabus": "basic-2015",
            "booklet": sources_dir / "2024令和6年理科.pdf",
        },
        {
            "id": "2024-1-math-c1",
            "session": "2024-1",
            "subject": "MATHEMATICS",
            "language": "ja",
            "syllabus": "basic-2015",
            "booklet": sources_dir / "2024令和6年数学1(1).pdf",
        },
        {
            "id": "2024-1-math-c2",
            "session": "2024-1",
            "subject": "MATHEMATICS",
            "language": "ja",
            "syllabus": "basic-2015",
            "booklet": sources_dir / "2024令和6年数学2.pdf",
        },
        {
            "id": "2024-1-japan-world",
            "session": "2024-1",
            "subject": "JAPAN_AND_WORLD",
            "language": "ja",
            "syllabus": "basic-2015",
            "booklet": sources_dir / "2024令和6年综合科目.pdf",
        },
        {
            "id": "2024-1-japanese",
            "session": "2024-1",
            "subject": "JAPANESE",
            "language": "ja",
            "syllabus": "japanese-2015",
            "booklet": sources_dir / "2024令和6年日语.pdf",
        },
    ]
    
    for t in targets:
        t_work = work_root / t["id"]
        t_work.mkdir(parents=True, exist_ok=True)
        manifest_path = t_work / "source-manifest.json"
        if not manifest_path.exists():
            create_source_manifest(
                session=t["session"],
                subject=t["subject"],
                language=t["language"],
                syllabus_version=t["syllabus"],
                question_booklet=t["booklet"],
                answer_key=None, rights_status="PRIVATE_STUDY",
                rights_note=f"EJU {t['session']} {t['subject']} source trial run",
                output_path=manifest_path,
            )
        probe_path = t_work / "probe.json"
        probe_res = probe_manifest(manifest_path, probe_path)
        print(f"Probed {t['id']}: {probe_res['files'][0]['pageCount']} pages, ")
    
    print("All 2024 source booklets probed and manifest-indexed successfully!")


if __name__ == "__main__":
    main()
