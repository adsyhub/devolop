from __future__ import annotations

import json
from pathlib import Path

import pytest

from eju_bank.answers import parse_answer_text
from eju_bank.assemble import assemble_paper
from eju_bank.audit import audit_paper, prepare_paper
from eju_bank.db import Database
from eju_bank.errors import RightsError, QualityGateError
from eju_bank.publish import assert_publish_rights
from eju_bank.source import create_source_manifest
from eju_bank.util import write_json


def make_source(tmp_path: Path) -> Path:
    question = tmp_path / "question.pdf"
    answer = tmp_path / "answer.pdf"
    question.write_bytes(b"test question source")
    answer.write_bytes(b"test answer source")
    manifest = tmp_path / "source-manifest.json"
    create_source_manifest(
        session="2023-2",
        subject="SCIENCE",
        language="ja",
        syllabus_version="2015",
        question_booklet=question,
        answer_key=answer,
        rights_status="PRIVATE_STUDY",
        rights_note="unit test",
        output_path=manifest,
    )
    return manifest


def make_pages(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    page = {
        "schemaVersion": 1,
        "page": 3,
        "sourceFileRole": "QUESTION_BOOKLET",
        "blocks": [
            {
                "kind": "material",
                "localKey": "physics-i-context",
                "formCode": "PHYSICS_JA",
                "groupCode": "I",
                "contentAst": [{"type": "text", "value": "質量 m の物体を考える。"}],
                "bbox": [0.08, 0.12, 0.92, 0.30],
                "readingOrder": 1,
            },
            {
                "kind": "question",
                "localKey": "physics-i-q1",
                "formCode": "PHYSICS_JA",
                "sectionCode": "MAIN",
                "groupCode": "I",
                "printedLabel": "問1",
                "answerRef": "PHYSICS:1",
                "stemAst": [{"type": "text", "value": "正しいものを選びなさい。"}],
                "options": [
                    {"key": str(index), "contentAst": [{"type": "inlineMath", "latex": f"x_{index}"}]}
                    for index in range(1, 7)
                ],
                "answerSpec": {"type": "SINGLE_CHOICE"},
                "materialRefs": ["physics-i-context"],
                "bbox": [0.08, 0.31, 0.92, 0.90],
                "readingOrder": 2,
            },
        ],
        "coverage": {"inkRegions": 2, "accountedRegions": 2},
        "issues": [],
    }
    write_json(pages / "p0003-question_booklet.json", page)
    return pages


def test_assemble_publish_and_server_side_grading(tmp_path: Path) -> None:
    manifest = make_source(tmp_path)
    pages = make_pages(tmp_path)
    ledger = parse_answer_text("objective PHYSICS_JA PHYSICS:1 6")
    answers = tmp_path / "answers.json"
    write_json(answers, ledger)
    output = tmp_path / "paper.json"
    paper = assemble_paper(
        manifest_path=manifest,
        pages_dir=pages,
        answer_ledger_path=answers,
        output_path=output,
    )
    assert audit_paper(paper)["status"] == "passed"
    assert paper["forms"][0]["groups"][0]["questions"][0]["correctAnswer"] == {"optionKey": "6"}

    database = Database(tmp_path / "library.db")
    try:
        with pytest.raises(QualityGateError):
            database.publish(paper, channel="PRIVATE")
        # This fixture uses fabricated PDF bytes; mark it explicitly as synthetic.
        paper["contentKind"] = "SYNTHETIC"
        paper = prepare_paper(paper)
        published = database.publish(paper, channel="PRIVATE")
        assert published["version"] == 1
        delivery = database.get_paper(paper["paperId"])
        assert "correctAnswer" not in delivery["forms"][0]["groups"][0]["questions"][0]
        session = database.create_session(paper["paperId"], ["PHYSICS_JA"], mode="PRACTICE")
        question_id = paper["forms"][0]["groups"][0]["questions"][0]["questionId"]
        database.record_response(
            session["sessionId"], question_id, {"type": "SINGLE_CHOICE", "optionKey": "6"}
        )
        result = database.submit_session(session["sessionId"])
        assert result["scoreKind"] == "RAW_PRACTICE"
        assert result["officialScale"] is False
        assert result["objectiveAccuracy"] == 1.0
    finally:
        database.close()


def test_private_source_cannot_be_publicly_published(tmp_path: Path) -> None:
    manifest = json.loads(make_source(tmp_path).read_text(encoding="utf-8"))
    paper = {"source": {"rights": manifest["rights"]}}
    with pytest.raises(RightsError):
        assert_publish_rights(paper, "PUBLIC")

