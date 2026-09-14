"""A contract drafted from OCR must carry the reading and refuse to be signed."""
import json

import pytest

from eju_bank.errors import QualityGateError
from eju_bank.ocr.page_contracts import build_page_contract, contract_path
from eju_bank.page_contract import validate_page_contract


def _question(**over):
    item = {
        "label": "問1", "stem": "次の文章の内容と合っているものはどれですか。",
        "options": {"1": "甲", "2": "乙", "3": "丙", "4": "丁"},
        "section": "読解", "answer_prefix": "READING", "page": 33,
        "boxed_slot": None, "slot": None, "context": None,
    }
    item.update(over)
    return item


def test_draft_carries_the_questions_it_read(tmp_path):
    contract = build_page_contract(
        tmp_path, "QUESTION_BOOKLET", 33, form_code="JAPANESE_JA",
        questions=[_question()], answers={"READING:1": "3"})
    blocks = [b for b in contract["blocks"] if b["kind"] == "question"]
    assert len(blocks) == 1
    assert blocks[0]["printedLabel"] == "問1"
    assert blocks[0]["answerRef"] == "READING:1"
    assert [o["key"] for o in blocks[0]["options"]] == ["1", "2", "3", "4"]
    assert "READING:1 = 3" in blocks[0]["notes"]


def test_draft_can_never_be_signed(tmp_path):
    """needsReview plus open issues are what stop a machine reading from passing."""
    contract = build_page_contract(
        tmp_path, "QUESTION_BOOKLET", 33, form_code="JAPANESE_JA",
        questions=[_question()], answers={"READING:1": "3"})
    assert contract["needsReview"] is True
    assert contract["issues"], "a draft must name what a person still has to establish"
    codes = {i["code"] for i in contract["issues"]}
    assert "page.region_evidence_required" in codes


def test_region_evidence_is_never_invented(tmp_path):
    """OCR reads text, not page geometry; regionIds must come from a person."""
    contract = build_page_contract(
        tmp_path, "QUESTION_BOOKLET", 33, form_code="JAPANESE_JA",
        questions=[_question()], answers={})
    assert "regionIds" not in contract["coverage"]
    assert contract["coverage"]["accountedRegions"] == 0
    assert all("regionIds" not in b and "regionId" not in b for b in contract["blocks"])


def test_detected_ink_regions_are_reported_as_unaccounted(tmp_path):
    """With regions detected and none assigned, coverage must read as incomplete."""
    (tmp_path / "probe.json").write_text(json.dumps({
        "files": [{"role": "QUESTION_BOOKLET",
                   "pages": [{"page": 33, "imageBlocks": 3, "inkRatio": 0.11}]}]
    }), encoding="utf-8")
    contract = build_page_contract(
        tmp_path, "QUESTION_BOOKLET", 33, form_code="JAPANESE_JA",
        questions=[_question()], answers={})
    assert contract["coverage"] == {"inkRegions": 3, "accountedRegions": 0}
    result = validate_page_contract(contract)
    assert result["status"] != "passed"
    assert any(i["code"] == "page.coverage_incomplete" for i in result["issues"])


def test_shared_passage_becomes_one_material_block(tmp_path):
    passage = "企業や消費者が，市場の外で社会に不利益をもたらすことを「外部不経済」という。"
    contract = build_page_contract(
        tmp_path, "QUESTION_BOOKLET", 8, form_code="JAPAN_AND_WORLD_JA",
        questions=[_question(label="問7(1)", context=passage, section="総合科目",
                             answer_prefix="JW", boxed_slot="14"),
                   _question(label="問7(2)", context=passage, section="総合科目",
                             answer_prefix="JW", boxed_slot="15")],
        answers={"JW:14": "1", "JW:15": "4"})
    materials = [b for b in contract["blocks"] if b["kind"] == "material"]
    assert len(materials) == 1, "one passage shared by two sub-questions, recorded once"
    assert materials[0]["contentAst"][0]["value"] == passage
    refs = [b["answerRef"] for b in contract["blocks"] if b["kind"] == "question"]
    assert refs == ["JW:14", "JW:15"]


def test_a_question_without_a_slot_is_flagged_not_guessed(tmp_path):
    contract = build_page_contract(
        tmp_path, "QUESTION_BOOKLET", 5, form_code="PHYSICS_JA",
        questions=[_question(label="問3", section="物理", answer_prefix="PHYSICS")],
        answers={"PHYSICS:8": "3"})
    block = next(b for b in contract["blocks"] if b["kind"] == "question")
    assert "answerRef" not in block
    assert any(i["code"] == "block.answer_ref_unknown" for i in contract["issues"])


def test_a_page_with_nothing_read_gets_an_ignored_block_and_an_issue(tmp_path):
    contract = build_page_contract(
        tmp_path, "QUESTION_BOOKLET", 1, form_code=None, questions=[], answers={})
    assert [b["kind"] for b in contract["blocks"]] == ["ignored"]
    assert contract["blocks"][0]["reason"]
    assert any(i["code"] == "page.no_question_read" for i in contract["issues"])


def test_contract_path_matches_what_the_review_workbench_reads(tmp_path):
    assert contract_path(tmp_path, "QUESTION_BOOKLET", 7).name == "p0007-question_booklet.json"
    assert contract_path(tmp_path, "ANSWER_KEY", 12).name == "p0012-answer_key.json"
