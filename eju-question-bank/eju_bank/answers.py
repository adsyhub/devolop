"""Independent answer-key parsing; answers are never inferred from question pages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .constants import ALLOWED_DIGIT_TOKENS, FORM_SPECS
from .errors import ContractError
from .page_contract import load_page_contracts
from .util import utc_now, write_json


def answer_key(form_code: str, answer_ref: str) -> str:
    return f"{form_code}|{answer_ref}"


def _add_entry(entries: dict[str, dict[str, Any]], entry: dict[str, Any], line: str) -> None:
    key = answer_key(str(entry["formCode"]), str(entry["answerRef"]))
    if key in entries:
        raise ContractError(f"Duplicate answer entry {key}: {line}")
    entries[key] = entry


def _expand_digit_assignments(assignments: Iterable[str], line: str) -> dict[str, str]:
    tokens: dict[str, str] = {}
    for assignment in assignments:
        if "=" not in assignment:
            raise ContractError(f"Digit assignment needs '=': {line}")
        labels, raw_value = assignment.split("=", 1)
        labels = labels.strip().upper()
        raw_value = raw_value.strip()
        if not labels or any(char < "A" or char > "Z" for char in labels):
            raise ContractError(f"Digit labels must be A-Z: {line}")
        if len(labels) != len(raw_value):
            raise ContractError(
                f"Digit label/value length differs ({labels} vs {raw_value!r}): {line}"
            )
        for label, token in zip(labels, raw_value):
            if token not in ALLOWED_DIGIT_TOKENS:
                raise ContractError(f"Invalid digit-grid token {token!r}: {line}")
            if label in tokens:
                raise ContractError(f"Digit slot {label} appears twice: {line}")
            tokens[label] = token
    return tokens


def parse_answer_text(text: str, *, source: str = "answer-key.txt") -> dict[str, Any]:
    """Parse fail-closed plain text directives.

    objective PHYSICS_JA PHYSICS:1 2
    digits MATHEMATICS_COURSE_1_JA C1:I:Q1 A=6 BC=24 DE=-3
    """
    entries: dict[str, dict[str, Any]] = {}
    notes: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        directive = parts[0].lower()
        if directive == "note":
            notes.append(line.removeprefix(parts[0]).strip())
            continue
        if directive == "objective" and len(parts) == 4:
            _, form_code, answer_ref, correct_option = parts
            if form_code not in FORM_SPECS:
                raise ContractError(f"Unknown formCode at line {line_number}: {form_code}")
            _add_entry(
                entries,
                {
                    "formCode": form_code,
                    "answerRef": answer_ref,
                    "answerType": "SINGLE_CHOICE",
                    "correctOption": correct_option,
                    "sourceLine": line_number,
                },
                line,
            )
            continue
        if directive == "digits" and len(parts) >= 4:
            _, form_code, answer_ref, *assignments = parts
            if form_code not in FORM_SPECS:
                raise ContractError(f"Unknown formCode at line {line_number}: {form_code}")
            _add_entry(
                entries,
                {
                    "formCode": form_code,
                    "answerRef": answer_ref,
                    "answerType": "DIGIT_GRID",
                    "tokens": _expand_digit_assignments(assignments, line),
                    "sourceLine": line_number,
                },
                line,
            )
            continue
        raise ContractError(f"Unknown or malformed answer directive at line {line_number}: {line}")
    if not entries:
        raise ContractError("Answer key contains no objective or digit entries")
    return {
        "schemaVersion": 1,
        "source": source,
        "createdAt": utc_now(),
        "notes": notes,
        "entries": entries,
    }


def answers_from_page_contracts(pages_dir: Path) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    pages = load_page_contracts(pages_dir)
    for page in pages:
        if page.get("sourceFileRole") != "ANSWER_KEY":
            continue
        for block in page.get("blocks", []):
            if block.get("kind") != "answer-entry":
                continue
            entry = {
                "formCode": block["formCode"],
                "answerRef": block["answerRef"],
                "answerType": block["answerType"],
                "sourcePage": page["page"],
                "sourceBbox": block["bbox"],
            }
            if entry["answerType"] == "SINGLE_CHOICE":
                entry["correctOption"] = str(block.get("correctOption") or "")
                if not entry["correctOption"]:
                    raise ContractError(f"Empty correctOption on answer page {page['page']}")
            else:
                raw_tokens = block.get("tokens")
                if not isinstance(raw_tokens, dict) or not raw_tokens:
                    raise ContractError(f"Empty digit tokens on answer page {page['page']}")
                entry["tokens"] = {str(key): str(value) for key, value in raw_tokens.items()}
            _add_entry(entries, entry, f"answer page {page['page']}")
    if not entries:
        raise ContractError("No answer-entry blocks found in answer page contracts")
    return {
        "schemaVersion": 1,
        "source": str(pages_dir),
        "createdAt": utc_now(),
        "notes": [],
        "entries": entries,
    }


def write_answer_ledger(path: Path, ledger: dict[str, Any]) -> None:
    write_json(path, ledger)

