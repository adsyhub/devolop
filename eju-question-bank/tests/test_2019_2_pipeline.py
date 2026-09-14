import json
import pytest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from eju_bank.page_contract import validate_ast
from scripts.assemble_explanations import (
    assemble_math_c1_explanations,
    assemble_math_c2_explanations,
    assemble_science_explanations,
    convert_solution_to_ast,
)


def test_2019_2_files_exist():
    """Verify all 2019-2 explanation files exist."""
    work_dir = PROJECT_ROOT / "work"
    c1_path = work_dir / "2019-2-math-c1/explanations.json"
    c2_path = work_dir / "2019-2-math-c2/explanations.json"
    sci_path = work_dir / "2019-2-science/explanations.json"

    assert c1_path.exists(), f"Missing {c1_path}"
    assert c2_path.exists(), f"Missing {c2_path}"
    assert sci_path.exists(), f"Missing {sci_path}"


def test_2019_2_math_c1_structure():
    """Test Math Course 1 sections and AST validation."""
    c1_path = PROJECT_ROOT / "work/2019-2-math-c1/explanations.json"
    data = json.loads(c1_path.read_text(encoding="utf-8"))
    assert data["session"] == "2019-2"
    assert len(data["sections"]) == 8

    mapped = assemble_math_c1_explanations(data)
    assert len(mapped) == 8
    for key, payload in mapped.items():
        assert payload["kind"] == "EXPLANATION"
        assert payload["language"] == "zh"
        assert len(payload["points"]) > 0
        issues = validate_ast(payload["contentAst"], ref=key)
        assert not issues, f"AST validation failed for {key}: {issues}"


def test_2019_2_math_c2_structure():
    """Test Math Course 2 sections and AST validation."""
    c2_path = PROJECT_ROOT / "work/2019-2-math-c2/explanations.json"
    data = json.loads(c2_path.read_text(encoding="utf-8"))
    assert data["session"] == "2019-2"
    assert len(data["sections"]) == 8

    mapped = assemble_math_c2_explanations(data)
    assert len(mapped) == 8
    for key, payload in mapped.items():
        assert payload["kind"] == "EXPLANATION"
        assert payload["language"] == "zh"
        assert len(payload["points"]) > 0
        issues = validate_ast(payload["contentAst"], ref=key)
        assert not issues, f"AST validation failed for {key}: {issues}"


def test_2019_2_science_structure():
    """Test Science questions (Physics 19, Chemistry 20, Biology 18) and AST validation."""
    sci_path = PROJECT_ROOT / "work/2019-2-science/explanations.json"
    data = json.loads(sci_path.read_text(encoding="utf-8"))
    assert data["session"] == "2019-2"
    assert len(data["forms"]["PHYSICS_JA"]) == 19
    assert len(data["forms"]["CHEMISTRY_JA"]) == 20
    assert len(data["forms"]["BIOLOGY_JA"]) == 18

    mapped = assemble_science_explanations(data)
    assert len(mapped) == 57  # 19 + 20 + 18
    for key, payload in mapped.items():
        assert payload["kind"] == "EXPLANATION"
        assert payload["language"] == "zh"
        assert len(payload["points"]) > 0
        issues = validate_ast(payload["contentAst"], ref=key)
        assert not issues, f"AST validation failed for {key}: {issues}"


def test_2019_2_markdown_docs():
    """Verify generated Markdown solution documents."""
    docs_dir = PROJECT_ROOT / "docs/explanations"
    expected_docs = [
        "2019-2-math-c1-solutions.md",
        "2019-2-math-c2-solutions.md",
        "2019-2-physics-solutions.md",
        "2019-2-chemistry-solutions.md",
        "2019-2-biology-solutions.md",
        "2019-2-pipeline-guide.md",
    ]
    for doc in expected_docs:
        f = docs_dir / doc
        assert f.exists() and f.stat().st_size > 500, f"Doc {doc} missing or too small"
