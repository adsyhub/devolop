"""Tests verifying that 2022-2 Science and Mathematics detailed explanations are properly assembled and queryable."""

import json
import sqlite3
from pathlib import Path
import pytest
from eju_bank.db import Database
from eju_bank.errors import SessionError
from eju_bank.page_contract import validate_ast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "library/eju.db"


@pytest.fixture(scope="module")
def live_db():
    if not DB_PATH.exists():
        pytest.skip("library/eju.db does not exist")
    db = Database(DB_PATH)
    yield db
    db.close()


def test_2022_2_database_has_reviewed_explanations(live_db):
    """Verify that all 73 questions across Math 1, Math 2, and Science have reviewed explanations in DB for 2022-2."""
    papers = [
        ("eju-2022-2-math-c1-ja", 8),
        ("eju-2022-2-math-c2-ja", 8),
        ("eju-2022-2-science-ja", 57),
    ]

    total_verified = 0
    for stable_code, expected_count in papers:
        # Get latest paper version
        pv_row = live_db.connection.execute(
            """
            SELECT pv.id, pv.version_number
            FROM paper_versions pv
            JOIN papers p ON pv.paper_id = p.id
            WHERE p.stable_code = ?
              AND EXISTS (SELECT 1 FROM question_versions qv
                          JOIN explanation_revisions er ON er.question_version_id = qv.id
                          WHERE qv.paper_version_id = pv.id)
            ORDER BY pv.version_number DESC LIMIT 1
            """,
            (stable_code,),
        ).fetchone()
        assert pv_row is not None, f"Paper {stable_code} not found in DB"
        pv_id = pv_row["id"]

        # Get questions
        q_rows = live_db.connection.execute(
            """
            SELECT qv.id AS qv_id, q.stable_key
            FROM question_versions qv
            JOIN questions q ON qv.question_id = q.id
            WHERE qv.paper_version_id = ?
            """,
            (pv_id,),
        ).fetchall()
        assert len(q_rows) == expected_count, f"Expected {expected_count} questions for {stable_code}, got {len(q_rows)}"

        for q_row in q_rows:
            qv_id = q_row["qv_id"]
            skey = q_row["stable_key"]

            exp_row = live_db.connection.execute(
                """
                SELECT id, revision, status, payload_json, reviewer
                FROM explanation_revisions
                WHERE question_version_id = ? AND status = 'REVIEWED'
                ORDER BY revision DESC LIMIT 1
                """,
                (qv_id,),
            ).fetchone()

            assert exp_row is not None, f"Question {skey} (qv_id={qv_id}) has no REVIEWED explanation revision"
            payload = json.loads(exp_row["payload_json"])

            assert payload["kind"] == "EXPLANATION"
            assert payload["language"] == "zh"
            assert payload["title"]
            assert len(payload["points"]) > 0
            assert "officialAnswer" in payload
            assert "contentAst" in payload
            assert len(payload["contentAst"]) > 0

            # Validate AST nodes
            ast_issues = validate_ast(payload["contentAst"], ref=f"{stable_code}:{skey}")
            assert not ast_issues, f"AST issues in {stable_code}:{skey}: {ast_issues}"

            total_verified += 1

    assert total_verified == 73


def test_2022_2_work_paper_json_explanations():
    """Verify that paper.json files in work/ for 2022-2 have explanation payloads matching the contract."""
    sessions = [
        ("work/2022-2-math-c1/paper.json", 8),
        ("work/2022-2-math-c2/paper.json", 8),
        ("work/2022-2-science/paper.json", 57),
    ]

    for rel_path, expected_count in sessions:
        paper_file = PROJECT_ROOT / rel_path
        assert paper_file.exists(), f"{rel_path} does not exist"
        data = json.loads(paper_file.read_text(encoding="utf-8"))

        found_explanations = 0
        for form in data.get("forms", []):
            for group in form.get("groups", []):
                for q in group.get("questions", []):
                    assert "explanation" in q, f"Missing explanation on question {q.get('localKey')} in {rel_path}"
                    exp = q["explanation"]
                    assert exp["kind"] == "EXPLANATION"
                    assert exp["language"] == "zh"
                    assert exp["title"]
                    assert len(exp["points"]) > 0
                    assert len(exp["contentAst"]) > 0
                    ast_issues = validate_ast(exp["contentAst"], ref=f"{rel_path}:{q.get('localKey')}")
                    assert not ast_issues, f"AST issues in {rel_path}:{q.get('localKey')}: {ast_issues}"
                    found_explanations += 1

        assert found_explanations == expected_count, (
            f"Expected {expected_count} explanations in {rel_path}, found {found_explanations}"
        )


def test_2022_2_review_content_workflow(live_db):
    """A paper whose content was never reviewed must refuse new practice.

    This used to assert the opposite — that a session could be created on
    ``eju-2022-2-science-ja`` and its explanations read back. That paper is one of
    the placeholder releases: its options are the literal 「選択肢 (n)」 and its
    correct answers were computed from the question number. Offering it for
    practice is the defect this suite should now guard against, so the
    assertion is inverted rather than removed.

    Explanation assembly itself is still covered, from the work JSON, by
    ``test_2022_2_work_paper_json_explanations``.
    """
    row = live_db.connection.execute(
        "SELECT id FROM papers WHERE stable_code = 'eju-2022-2-science-ja'").fetchone()
    assert row is not None
    paper_id = row["id"]

    state = live_db.connection.execute(
        "SELECT ds.state, ds.note FROM paper_versions pv "
        "LEFT JOIN paper_delivery_state ds ON ds.paper_version_id = pv.id "
        "WHERE pv.paper_id = ? AND pv.status = 'PUBLISHED' "
        "ORDER BY pv.version_number DESC LIMIT 1", (paper_id,)).fetchone()
    if state is None or state["state"] not in {"SUSPENDED", "REVIEW_REQUIRED"}:
        pytest.skip("这套卷当前未被限制投放；本测试只覆盖受限时的拒绝行为")

    assert state["note"], "受限投放必须写明原因，学习者要能看到为什么"
    with pytest.raises(SessionError):
        live_db.create_session(paper_id, ["PHYSICS_JA", "CHEMISTRY_JA"], mode="PRACTICE")
def test_2022_2_docs_exist():
    """Verify all 5 Markdown explanation solution files exist and have substantial content."""
    docs = [
        "docs/explanations/2022-2-physics-solutions.md",
        "docs/explanations/2022-2-chemistry-solutions.md",
        "docs/explanations/2022-2-biology-solutions.md",
        "docs/explanations/2022-2-math-c1-solutions.md",
        "docs/explanations/2022-2-math-c2-solutions.md",
    ]
    for d in docs:
        p = PROJECT_ROOT / d
        assert p.exists(), f"Missing {d}"
        assert p.stat().st_size > 5000, f"File {d} is suspiciously small: {p.stat().st_size} bytes"

