"""工作台的状态必须来自一份权威快照，而且读它不能改数据。

对应规范 F08 / W10。原来前端自己拼状态：清单的 pipelineStatus、任务列表、本次
会话的变量，三者不一致时以谁为准没有定义。更要命的是它拿 ``/candidate`` 当读
接口——那个接口会真的组装一遍并把 ``paper.json`` 写回工作目录，于是"看一眼列表"
等于"给每一行跑一次组装"。

这里钉住两件事：快照说的是实话，以及读它没有副作用（规范 §11.3）。
"""

from __future__ import annotations

import json

import pymupdf
import pytest

from eju_bank.constants import MACHINE_REVIEWER
from eju_bank.db import Database
from eju_bank.ocr.attested_contracts import REQUIRED_CHECKS, attestation
from eju_bank.review import ContentWorkspace
from eju_bank.source import create_source_manifest
from eju_bank.studio_summary import source_summary, studio_summary
from eju_bank.util import write_json


@pytest.fixture
def workspace(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    for name, text in [("question.pdf", "Choose: 1 or 2"), ("answer.pdf", "Answer: 2")]:
        doc = pymupdf.open()
        doc.new_page().insert_text((50, 50), text)
        doc.save(sources / name)
        doc.close()
    manifest = create_source_manifest(
        session="test", subject="SCIENCE", language="ja", syllabus_version="2015",
        question_booklet=sources / "question.pdf", answer_key=sources / "answer.pdf",
        rights_status="PRIVATE_STUDY", rights_note="Test only",
        output_path=tmp_path / "work/test/source-manifest.json")
    manifest["inventoryId"] = "fixture-source"
    manifest["expectedForms"] = ["PHYSICS_JA"]
    write_json(tmp_path / "work/test/source-manifest.json", manifest)
    write_json(tmp_path / "work/test/ocr_cache/p0001.json",
               {"raw_text": "Choose one. ① 1 ② 2", "ocrModel": "test"})
    db = Database(tmp_path / "library/eju.db")
    yield ContentWorkspace(tmp_path, db), db, manifest["sourceId"], tmp_path / "work/test"
    db.close()


def _booklet_contract(work_dir):
    block = {"kind": "question", "localKey": "q1", "formCode": "PHYSICS_JA",
             "groupCode": "I", "answerRef": "PHYSICS:1", "printedLabel": "1",
             "bbox": [.08, .08, .92, .92],
             "stemAst": [{"type": "text", "value": "Choose one."}],
             "options": [{"key": str(i), "contentAst": [{"type": "text", "value": str(i)}]}
                         for i in (1, 2)],
             "answerSpec": {"type": "SINGLE_CHOICE"}, "materialRefs": [],
             "answerRefEvidence": "PRINTED_SLOT",
             "regionIds": ["p0001-text-01"], "readingOrder": 1}
    contract = {"schemaVersion": 2, "page": 1, "sourceFileRole": "QUESTION_BOOKLET",
                "blocks": [block],
                "coverage": {"inkRegions": 1, "accountedRegions": 1,
                             "regionIds": ["p0001-text-01"],
                             "accountedRegionIds": ["p0001-text-01"],
                             "regionEvidence": "TEXT_ORDER_ONLY"},
                "issues": []}
    contract["attestation"] = attestation(
        work_dir, 1, answer_cache=None,
        checks=sorted(REQUIRED_CHECKS["QUESTION_BOOKLET"]), contract=contract)
    return contract


def _attest(ws, source_id, work_dir):
    current = ws.read_page(source_id, "QUESTION_BOOKLET", 1)
    saved = ws.save_page(source_id, "QUESTION_BOOKLET", 1,
                         _booklet_contract(work_dir), current["revisionId"],
                         reviewer=MACHINE_REVIEWER)
    return ws.attest_page(source_id, "QUESTION_BOOKLET", 1, saved["revisionId"])


def test_a_fresh_source_is_not_reported_as_published(workspace):
    """什么都没做的来源：未发布、未检查，下一步说得出是什么。"""
    ws, db, source_id, _work = workspace
    summary = source_summary(ws, db, source_id)

    assert summary["publicationState"] == "NOT_PUBLISHED"
    assert summary["qualityState"] == "UNCHECKED"
    assert summary["manualState"] == "OFF"
    assert summary["nextAction"]["type"] == "WAITING_INPUT"
    assert summary["published"] is None
    # 期望题量没有证据，覆盖率就是未知——不能用已识别题数充当分母。
    assert summary["coverage"]["expectedQuestions"] is None
    assert summary["coverage"]["ratio"] is None


def test_reading_the_summary_has_no_side_effects(workspace):
    """读状态不能产生修订、结构、批准或发布。"""
    ws, db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)

    def snapshot():
        return {t: db.connection.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("page_revisions", "source_structure_revisions",
                          "paper_reviews", "paper_versions",
                          "paper_review_revocations")}

    before = snapshot()
    paper_before = (work_dir / "paper.json").read_bytes() if (work_dir / "paper.json").is_file() else None

    for _ in range(3):
        source_summary(ws, db, source_id)
        studio_summary(ws, db)

    assert snapshot() == before, "读 summary 改了数据库"
    paper_after = (work_dir / "paper.json").read_bytes() if (work_dir / "paper.json").is_file() else None
    assert paper_after == paper_before, "读 summary 重写了组装产物"


def test_human_pages_show_up_as_manual_state(workspace):
    """人留下的修订要在状态里看得见，而不是被当成机器产物。"""
    ws, db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)

    contract = json.loads(json.dumps(_booklet_contract(work_dir)))
    contract["blocks"][0]["stemAst"] = [{"type": "text", "value": "人工草稿"}]
    contract.pop("attestation", None)
    current = ws.read_page(source_id, "QUESTION_BOOKLET", 1)
    ws.save_page(source_id, "QUESTION_BOOKLET", 1, contract,
                 current["revisionId"], reviewer="审校 A")

    summary = source_summary(ws, db, source_id)
    assert summary["manualState"] == "EDITING"
    assert summary["pages"]["humanDraft"] == 1
    assert summary["pages"]["machineAttested"] == 0


def test_an_incomplete_proofread_is_not_reported_as_verified(workspace):
    """复核只跑成一半时，内容状态不能是 VERIFIED。"""
    ws, db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    write_json(work_dir / "quality-findings.json", {
        "total": 0, "bySeverity": {}, "quarantinedQuestions": [],
        "coverage": {"planned": 4, "completed": 1, "failed": 3,
                     "result": "UNKNOWN", "explanation": "只覆盖 1/4 批"},
    })
    summary = source_summary(ws, db, source_id)
    assert summary["qualityState"] != "VERIFIED"
    assert summary["findings"]["coverage"]["result"] == "UNKNOWN"
    assert summary["nextAction"]["type"] == "RETRY_SCHEDULED"


def test_quarantined_questions_are_counted_separately(workspace):
    """隔离量要单独报出来，不能混进"已验证"。"""
    ws, db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    write_json(work_dir / "quality-findings.json", {
        "total": 2, "bySeverity": {"SUSPECT": 2},
        "quarantinedQuestions": ["q_a", "q_b"],
        "coverage": {"planned": 1, "completed": 1, "failed": 0,
                     "result": "PASS", "explanation": "完整"},
    })
    summary = source_summary(ws, db, source_id)
    assert summary["coverage"]["quarantinedQuestions"] == 2
    assert summary["findings"]["bySeverity"]["SUSPECT"] == 2
    assert summary["qualityState"] == "PARTIAL_VERIFIED"


def test_studio_summary_states_its_basis(workspace):
    """汇总必须说明统计口径，否则数字会被读成它不是的东西。"""
    ws, db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    overview = studio_summary(ws, db)
    assert overview["counts"]["total"] == 1
    assert overview["basis"]
    assert overview["sources"][0]["sourceId"] == source_id


def test_one_broken_source_does_not_blank_the_overview(workspace):
    """一套卷读不出来，不该让整个首屏空白。"""
    ws, db, _source_id, _work = workspace
    (ws.root / "work/broken").mkdir(parents=True)
    write_json(ws.root / "work/broken/source-manifest.json",
               {"sourceId": "src_broken", "session": "x"})
    overview = studio_summary(ws, db)
    assert overview["counts"]["total"] == 2
    broken = [r for r in overview["sources"] if r["sourceId"] == "src_broken"]
    assert broken and broken[0]["executionState"] == "FAILED"
    assert "error" in broken[0]
