from __future__ import annotations

from pathlib import Path

import pytest

from eju_bank.pdf_pipeline import probe_manifest, render_manifest
from eju_bank.source import create_source_manifest


ROOT = Path(__file__).resolve().parents[1]
QUESTION = ROOT / "sources" / "2023令和5年第2回理科.pdf"
ANSWER = ROOT / "sources" / "2023令和5年第2回理科答案.pdf"


@pytest.mark.skipif(not QUESTION.is_file() or not ANSWER.is_file(), reason="real user-provided PDFs absent")
def test_real_pdf_probe_and_representative_render(tmp_path: Path) -> None:
    manifest_path = tmp_path / "source-manifest.json"
    create_source_manifest(
        session="2023-2",
        subject="SCIENCE",
        language="ja",
        syllabus_version="2015",
        question_booklet=QUESTION,
        answer_key=ANSWER,
        rights_status="PRIVATE_STUDY",
        rights_note="user-provided private-study copy",
        output_path=manifest_path,
    )
    probe = probe_manifest(manifest_path, tmp_path / "probe.json")
    by_role = {item["role"]: item for item in probe["files"]}
    assert by_role["QUESTION_BOOKLET"]["pageCount"] == 56
    assert by_role["ANSWER_KEY"]["pageCount"] == 8
    assert {page["rotation"] for page in by_role["QUESTION_BOOKLET"]["pages"]} == {90}
    assert {page["rotation"] for page in by_role["ANSWER_KEY"]["pages"]} == {90}
    assert sum(page["textChars"] for page in by_role["QUESTION_BOOKLET"]["pages"]) == 0
    assert sum(page["textChars"] for page in by_role["ANSWER_KEY"]["pages"]) == 0

    renders = tmp_path / "renders"
    question_index = render_manifest(
        manifest_path,
        role="QUESTION_BOOKLET",
        output_dir=renders,
        pages="1,3,24,42,56",
        full_dpi=72,
        tile_dpi=72,
        tile_count=2,
    )
    answer_index = render_manifest(
        manifest_path,
        role="ANSWER_KEY",
        output_dir=renders,
        pages="3",
        full_dpi=72,
        tile_dpi=72,
        tile_count=2,
    )
    assert [item["page"] for item in question_index["pages"]] == [1, 3, 24, 42, 56]
    assert question_index["pages"][0]["sourceRotation"] == 90
    assert answer_index["pages"][0]["page"] == 3
    for index in (question_index, answer_index):
        for page in index["pages"]:
            assert (renders / page["full"]["path"]).is_file()
            assert len(page["tiles"]) == 2
