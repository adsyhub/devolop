from __future__ import annotations

import pytest

from eju_bank.errors import ContractError
from eju_bank.grading import grade_response
from eju_bank.selection import validate_form_selection


def paper_with_forms(*codes: str) -> dict:
    return {"forms": [{"formCode": code} for code in codes]}


def test_science_mock_requires_two_and_excludes_japan_world() -> None:
    paper = paper_with_forms("PHYSICS_JA", "CHEMISTRY_JA", "JAPAN_AND_WORLD_JA")
    assert validate_form_selection(paper, ["PHYSICS_JA", "CHEMISTRY_JA"], mode="MOCK")
    with pytest.raises(ContractError, match="exactly two"):
        validate_form_selection(paper, ["PHYSICS_JA"], mode="MOCK")
    with pytest.raises(ContractError, match="cannot be selected"):
        validate_form_selection(
            paper, ["PHYSICS_JA", "CHEMISTRY_JA", "JAPAN_AND_WORLD_JA"], mode="MOCK"
        )


def test_digit_grid_is_exact_and_preserves_leading_zero() -> None:
    question = {
        "answerSpec": {"type": "DIGIT_GRID", "slots": ["A", "B", "C"]},
        "correctAnswer": {"tokens": {"A": "-", "B": "0", "C": "4"}},
    }
    assert grade_response(
        question, {"type": "DIGIT_GRID", "tokens": {"A": "-", "B": "0", "C": "4"}}
    )["correct"]
    assert not grade_response(
        question, {"type": "DIGIT_GRID", "tokens": {"A": "-", "B": "4"}}
    )["correct"]

