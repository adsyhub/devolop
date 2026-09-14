"""Validate official EJU subject/course choices for mock sessions."""

from __future__ import annotations

from typing import Any

from .constants import BASIC_SUBJECTS, FORM_SPECS, SCIENCE_SUBJECTS
from .errors import ContractError


def validate_form_selection(
    paper: dict[str, Any], selected_form_codes: list[str], *, mode: str = "MOCK"
) -> list[str]:
    if mode not in {"MOCK", "PRACTICE", "SECTION"}:
        raise ContractError("mode must be MOCK, PRACTICE or SECTION")
    if not selected_form_codes:
        raise ContractError("At least one form must be selected")
    if len(selected_form_codes) != len(set(selected_form_codes)):
        raise ContractError("A form cannot be selected twice")
    available = {str(form.get("formCode")) for form in paper.get("forms") or []}
    missing = sorted(set(selected_form_codes) - available)
    if missing:
        raise ContractError(f"Selected forms are not in this paper: {missing}")
    specs = [FORM_SPECS[code] for code in selected_form_codes]
    by_subject: dict[str, int] = {}
    for spec in specs:
        by_subject[spec.subject] = by_subject.get(spec.subject, 0) + 1
    duplicate_subjects = sorted(subject for subject, count in by_subject.items() if count > 1)
    if duplicate_subjects:
        raise ContractError(f"Cannot choose multiple variants of one subject: {duplicate_subjects}")
    if mode == "MOCK":
        science = [spec for spec in specs if spec.subject in SCIENCE_SUBJECTS]
        has_world = any(spec.subject == "JAPAN_AND_WORLD" for spec in specs)
        if science and len(science) != 2:
            raise ContractError("A science mock must select exactly two of physics, chemistry and biology")
        if science and has_world:
            raise ContractError("Science and Japan and the World cannot be selected in the same mock")
        math = [spec for spec in specs if spec.subject == "MATHEMATICS"]
        if len(math) > 1:
            raise ContractError("Select only one mathematics course")
        languages = {spec.language for spec in specs if spec.subject in BASIC_SUBJECTS}
        if len(languages) > 1:
            raise ContractError("Basic academic subjects in one mock must use the same exam language")
    return selected_form_codes

