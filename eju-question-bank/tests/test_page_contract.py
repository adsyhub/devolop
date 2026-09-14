from __future__ import annotations

from eju_bank.page_contract import validate_page_contract


def valid_page() -> dict:
    return {
        "schemaVersion": 1,
        "page": 3,
        "sourceFileRole": "QUESTION_BOOKLET",
        "blocks": [
            {
                "kind": "question",
                "localKey": "physics-i-q1",
                "formCode": "PHYSICS_JA",
                "sectionCode": "MAIN",
                "groupCode": "I",
                "printedLabel": "問1",
                "answerRef": "PHYSICS:1",
                "stemAst": [
                    {"type": "text", "value": "次の式を選びなさい。"},
                    {"type": "inlineMath", "latex": "F=ma"},
                    {"type": "figure", "sourceBbox": [0.2, 0.3, 0.8, 0.6]},
                ],
                "options": [
                    {"key": str(index), "contentAst": [{"type": "inlineMath", "latex": str(index)}]}
                    for index in range(1, 7)
                ],
                "answerSpec": {"type": "SINGLE_CHOICE"},
                "materialRefs": [],
                "bbox": [0.08, 0.15, 0.92, 0.88],
            }
        ],
        "coverage": {"inkRegions": 1, "accountedRegions": 1},
    }


def test_page_contract_accepts_variable_option_count() -> None:
    assert validate_page_contract(valid_page())["status"] == "passed"


def test_page_contract_fails_closed_on_coverage_and_bbox() -> None:
    page = valid_page()
    page["coverage"]["accountedRegions"] = 0
    page["blocks"][0]["bbox"] = [0, 0, 2, 1]
    report = validate_page_contract(page)
    assert report["status"] == "failed"
    assert {item["code"] for item in report["issues"]} >= {
        "page.coverage_incomplete",
        "block.bbox_invalid",
    }


def test_page_contract_region_ids_exact_set_match() -> None:
    page = valid_page()
    page["coverage"]["regionIds"] = ["r1", "r2"]
    page["coverage"]["accountedRegionIds"] = ["r1", "r3"]
    report = validate_page_contract(page)
    assert report["status"] == "failed"
    assert any(i["code"] == "page.coverage_regions_mismatch" for i in report["issues"])


