from __future__ import annotations

import pytest

from eju_bank.answers import parse_answer_text
from eju_bank.errors import ContractError


def test_variable_choice_and_digit_grid_preserve_tokens() -> None:
    ledger = parse_answer_text(
        """
        # Science may have more than four choices.
        objective PHYSICS_JA PHYSICS:1 6
        digits MATHEMATICS_COURSE_1_JA C1:III:Q1 AB=-3 CD=04
        """
    )
    assert ledger["entries"]["PHYSICS_JA|PHYSICS:1"]["correctOption"] == "6"
    tokens = ledger["entries"]["MATHEMATICS_COURSE_1_JA|C1:III:Q1"]["tokens"]
    assert tokens == {"A": "-", "B": "3", "C": "0", "D": "4"}


def test_answer_parser_rejects_duplicate_and_misaligned_digits() -> None:
    with pytest.raises(ContractError, match="Duplicate answer"):
        parse_answer_text(
            "objective PHYSICS_JA P:1 2\nobjective PHYSICS_JA P:1 3"
        )
    with pytest.raises(ContractError, match="length differs"):
        parse_answer_text("digits MATHEMATICS_COURSE_1_JA M:1 ABC=12")

