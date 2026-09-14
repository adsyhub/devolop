from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from conftest import install_fixture_media
from eju_bank.db import Database
from eju_bank.errors import ContractError
from eju_bank.publish import publish_file
from eju_bank.server import create_server


@pytest.fixture
def db_with_paper(tmp_path: Path):
    db_file = tmp_path / "eju.db"
    install_fixture_media(tmp_path / "media")
    publish_file(Path("tests/fixtures/synthetic_paper.json"), db_file, channel="PUBLIC")
    database = Database(db_file)
    yield database
    database.close()


def test_content_issue_lifecycle(db_with_paper: Database):
    db = db_with_paper
    paper = db.list_papers()[0]
    questions = db.get_paper_questions(paper["paperId"])["questions"]
    q1 = questions[0]
    q_id = q1["questionId"]

    # 1. Report issue with valid parameters
    issue = db.report_content_issue(
        q_id,
        "There is a typo in question text line 2",
        issue_type="TEXT",
        paper_version_id=paper["paperVersionId"],
    )
    issue_id = issue["issueId"]
    assert issue["status"] == "OPEN"
    assert issue["issueType"] == "TEXT"

    # 2. Reject too short description
    with pytest.raises(ContractError):
        db.report_content_issue(q_id, "Bad")

    # 3. Reject invalid issue type
    with pytest.raises(ContractError):
        db.report_content_issue(q_id, "Valid description text", issue_type="INVALID_TYPE")

    # 4. Reject mismatch between question and paper_version_id
    with pytest.raises(ContractError):
        db.report_content_issue(q_id, "Valid description text", paper_version_id="pv_nonexistent")

    # 5. List issues
    issues = db.list_content_issues(status="OPEN")
    assert len(issues) >= 1
    assert any(iss["issueId"] == issue_id for iss in issues)

    # 6. Status transition
    updated = db.update_content_issue_status(issue_id, "TRIAGED", reason="Confirmed by maintainer")
    assert updated["status"] == "TRIAGED"
    assert updated["statusReason"] == "Confirmed by maintainer"

    # Invalid status
    with pytest.raises(ContractError):
        db.update_content_issue_status(issue_id, "BOGUS_STATUS")


@pytest.fixture
def running_server_content(tmp_path: Path):
    db_file = tmp_path / "eju.db"
    install_fixture_media(tmp_path / "media")
    publish_file(Path("tests/fixtures/synthetic_paper.json"), db_file, channel="PUBLIC")
    httpd = create_server(db_file, port=0, workspace_root=tmp_path)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()
        httpd.database.close()


def _req(url: str, path: str, method: str = "GET", body: dict | None = None):
    h = {}
    data = json.dumps(body).encode("utf-8") if body is not None else None
    if data:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def test_content_issue_http_endpoints(running_server_content):
    base_url = running_server_content
    status, d_p = _req(base_url, "/api/v1/papers")
    paper_id = d_p["papers"][0]["paperId"]
    status, d_q = _req(base_url, f"/api/v1/papers/{paper_id}/questions")
    q_id = d_q["questions"][0]["questionId"]

    # 1. Report issue via HTTP
    status, body = _req(base_url, "/api/v1/content-issues", method="POST", body={
        "questionId": q_id,
        "description": "Figure 1 has blurry resolution",
        "issueType": "FIGURE",
    })
    assert status == 201
    issue_id = body["issue"]["issueId"]
    assert body["issue"]["status"] == "OPEN"

    # 2. List content issues via HTTP
    status, body = _req(base_url, f"/api/v1/content-issues?questionId={q_id}")
    assert status == 200
    assert len(body["issues"]) >= 1
    assert any(iss["issueId"] == issue_id for iss in body["issues"])

    # 3. Update status via HTTP
    status, body = _req(base_url, f"/api/v1/admin/content-issues/{issue_id}", method="PUT", body={
        "status": "IN_PROGRESS",
        "reason": "Designer reviewing high-res vector source",
    })
    assert status == 200
    assert body["issue"]["status"] == "IN_PROGRESS"
