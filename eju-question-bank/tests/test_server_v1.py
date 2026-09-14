from conftest import install_fixture_media
import json
import threading
import time
import urllib.request
import http.client
from pathlib import Path
import pytest
from eju_bank.server import create_server
from eju_bank.publish import publish_file

PORT = 8779

@pytest.fixture
def running_server(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("db")
    db_file = db_dir / "eju.db"
    
    install_fixture_media(db_dir / "media")
    # Publish synthetic paper
    publish_file(Path("tests/fixtures/synthetic_paper.json"), db_file, channel="PUBLIC")
    
    httpd = create_server(db_file, port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()
        httpd.database.close()


def req(url, path, method="GET", body=None, headers=None):
    h = dict(headers or {})
    data = json.dumps(body).encode("utf-8") if body is not None else None
    if data and "Content-Type" not in h:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def test_api_health(running_server):
    s, d = req(running_server, "/api/v1/health")
    assert s == 200
    assert d["status"] == "ok"

def test_api_papers_and_sanitization(running_server):
    s, d = req(running_server, "/api/v1/papers")
    assert s == 200
    assert len(d["papers"]) >= 1
    paper_id = d["papers"][0]["paperId"]

    # Outline
    s, d_out = req(running_server, f"/api/v1/papers/{paper_id}/outline")
    assert s == 200
    assert "forms" in d_out["outline"]

    # Questions query
    s, d_q = req(running_server, f"/api/v1/papers/{paper_id}/questions?form=PHYSICS_JA")
    assert s == 200
    assert len(d_q["questions"]) == 1
    q = d_q["questions"][0]
    assert "correctAnswer" not in q

def test_session_lifecycle(running_server):
    s, d = req(running_server, "/api/v1/papers")
    paper_id = d["papers"][0]["paperId"]

    # 1. Create Practice Session
    s, sess = req(running_server, "/api/v1/sessions", method="POST", body={
        "paperId": paper_id,
        "selectedForms": ["PHYSICS_JA"],
        "mode": "PRACTICE"
    })
    assert s == 201
    sess_id = sess["sessionId"]

    # 2. Query questions
    s, q_res = req(running_server, f"/api/v1/papers/{paper_id}/questions?form=PHYSICS_JA")
    q_id = q_res["questions"][0]["questionId"]

    # 3. Batch responses
    s, d_batch = req(running_server, f"/api/v1/sessions/{sess_id}/responses:batch", method="POST", body={
        "items": [{"questionId": q_id, "response": {"type": "SINGLE_CHOICE", "optionKey": "1"}}]
    })
    assert s == 200
    assert d_batch["saved"] == 1

    # 4. Pause & Resume
    s, d_pause = req(running_server, f"/api/v1/sessions/{sess_id}:pause", method="POST", body={})
    assert s == 200 and d_pause["status"] == "PAUSED"
    s, d_resume = req(running_server, f"/api/v1/sessions/{sess_id}:resume", method="POST", body={})
    assert s == 200 and d_resume["status"] == "IN_PROGRESS"

    # 5. Submit
    s, d_submit = req(running_server, f"/api/v1/sessions/{sess_id}:submit", method="POST", body={})
    assert s == 200
    res = d_submit["result"]
    assert res["scoreKind"] == "RAW_PRACTICE"
    assert res["officialScale"] is False

    # 6. Bookmarks and Notes
    s, _ = req(running_server, f"/api/v1/questions/{q_id}/bookmark", method="PUT", body={"note": "Test bm"})
    assert s == 200
    s, bms = req(running_server, "/api/v1/bookmarks")
    assert s == 200 and any(b["questionId"] == q_id for b in bms["bookmarks"])

    s, _ = req(running_server, f"/api/v1/questions/{q_id}/note", method="PUT", body={"note": "Test note"})
    assert s == 200
    s, note_res = req(running_server, f"/api/v1/questions/{q_id}/note")
    assert s == 200 and note_res["note"] == "Test note"


def test_route_strictness_and_transfer_encoding(running_server):
    # Trailing extra segments should return 404
    s, d = req(running_server, "/api/v1/sessions/123:submit/extra", method="POST", body={})
    assert s == 404
    assert d["error"]["code"] == "NOT_FOUND"
    assert "requestId" in d["error"]

    s, d = req(running_server, "/api/v1/papers/test_paper/outline/extra")
    assert s == 404
    assert d["error"]["code"] == "NOT_FOUND"

    s, d = req(running_server, "/api/v1/unknown_endpoint")
    assert s == 404
    assert d["error"]["code"] == "NOT_FOUND"

    # Unsupported Transfer-Encoding should return 422
    s, d = req(running_server, "/api/v1/sessions", method="POST", body={}, headers={"Transfer-Encoding": "chunked"})
    assert s == 422
    assert "Transfer-Encoding" in d["error"]["message"]
