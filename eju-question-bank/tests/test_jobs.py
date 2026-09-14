from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from eju_bank.db import Database
from eju_bank.errors import ContractError
from eju_bank.jobs import JobManager
from eju_bank.server import create_server


@pytest.fixture
def db(tmp_path: Path):
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


def test_job_manager_lifecycle(db: Database):
    # 1. Create job
    job = JobManager.create_job(
        db,
        job_type="IMPORT_SOURCE",
        target_id="eju-2024-1-math-c1",
        params={"role": "QUESTION_BOOKLET", "sourceRef": "relative/path.pdf"},
    )
    job_id = job["jobId"]
    assert job["status"] == "QUEUED"
    assert job["progress"]["percent"] == 0
    assert len(job["events"]) == 1
    assert job["events"][0]["eventType"] == "CREATED"

    # 2. Get job
    fetched = JobManager.get_job(db, job_id)
    assert fetched["jobId"] == job_id
    assert fetched["targetId"] == "eju-2024-1-math-c1"

    # 3. List jobs
    listed = JobManager.list_jobs(db, status="QUEUED")
    assert len(listed["jobs"]) == 1
    assert listed["jobs"][0]["jobId"] == job_id

    # Filter by target_id
    listed_target = JobManager.list_jobs(db, target_id="eju-2024-1-math-c1")
    assert len(listed_target["jobs"]) == 1
    assert len(JobManager.list_jobs(db, target_id="nonexistent")["jobs"]) == 0

    # 4. Update progress
    JobManager.update_progress(
        db,
        job_id,
        progress={"percent": 50, "pagesCompleted": 5, "pagesTotal": 10},
        status="RUNNING",
    )
    running_job = JobManager.get_job(db, job_id)
    assert running_job["status"] == "RUNNING"
    assert running_job["progress"]["percent"] == 50
    assert any(e["eventType"] == "STATUS_RUNNING" for e in running_job["events"])

    # 5. Cancel job
    cancelled = JobManager.cancel_job(db, job_id, reason="Testing cancellation")
    assert cancelled["status"] == "CANCEL_REQUESTED"
    JobManager.update_progress(db, job_id, {}, status="CANCELLED")
    assert any(e["eventType"] == "CANCEL" for e in cancelled["events"])

    # Attempt to cancel already cancelled job
    with pytest.raises(ContractError):
        JobManager.cancel_job(db, job_id)

    # 6. Retry job
    retried = JobManager.retry_job(db, job_id, pages=[1, 2], failed_only=True)
    assert retried["status"] == "QUEUED"
    assert retried["progress"]["retrying"] is True
    assert retried["progress"]["retryPages"] == [1, 2]
    assert retried["progress"]["failedOnly"] is True
    assert any(e["eventType"] == "RETRY" for e in retried["events"])


@pytest.fixture
def server_url(tmp_path: Path):
    db_file = tmp_path / "eju.db"
    httpd = create_server(db_file, port=0, workspace_root=tmp_path)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", tmp_path
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


def test_job_http_endpoints(server_url):
    base_url, ws_root = server_url

    # 1. Path traversal rejected on import
    status, body = _req(base_url, "/api/v1/admin/imports", method="POST", body={
        "sourceRef": "/etc/passwd",
        "inventoryId": "inv-1",
        "role": "QUESTION_BOOKLET",
    })
    assert status == 422
    assert "error" in body

    # A real parseable PDF and an explicitly selected inventory are required.
    import pymupdf
    from eju_bank.inventory import upsert_inventory_item
    upsert_inventory_item({'inventoryId':'inv-1','session':'TEST','subject':'SCIENCE','language':'ja',
        'syllabusId':'basic-2015','requiredFiles':['QUESTION_BOOKLET','ANSWER_KEY'],'rightsStatus':'PRIVATE_STUDY',
        'pipelineStatus':'RECEIVED','expectedForms':['PHYSICS_JA']}, ws_root/'content/content-inventory.json')
    sample_file = ws_root / 'incoming/booklet.pdf'
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    doc=pymupdf.open();page=doc.new_page();page.insert_text((40,40),'Synthetic source');doc.save(sample_file);doc.close()
    status, body = _req(base_url, '/api/v1/admin/imports', method='POST', body={
        'filePath':'incoming/booklet.pdf','inventoryId':'inv-1','role':'QUESTION_BOOKLET'})
    assert status == 202
    job_id = body['jobId']
    result = await_job(base_url, job_id)
    assert result['status'] == 'SUCCEEDED', result
    status,body = _req(base_url,'/api/v1/admin/sources')
    sid=body['sources'][0]['sourceId']
    assert result['progress']['sourceId']==sid
    status,body = _req(base_url,'/api/v1/admin/jobs',method='POST',body={'jobType':'RENDER','sourceId':sid,'role':'QUESTION_BOOKLET','pages':'1'})
    assert status==202
    assert await_job(base_url,body['jobId'])['status']=='SUCCEEDED'
    assert list((ws_root/'work').glob('*/renders/render-index-question_booklet.json'))
    # A corrupt PDF is never reported as a successful import.
    sample_file.write_bytes(b'%PDF-1.4 broken')
    status,body=_req(base_url,'/api/v1/admin/imports',method='POST',body={'filePath':'incoming/booklet.pdf','inventoryId':'inv-1','role':'ANSWER_KEY'})
    assert status==202
    assert await_job(base_url,body['jobId'])['status']=='FAILED'
    status,body=_req(base_url,'/api/v1/admin/jobs/'+body['jobId']+'/retry',method='POST',body={})
    assert status==200
    assert await_job(base_url,body['job']['jobId'])['status']=='FAILED'


def await_job(url,jid):
    import time
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        status,body=_req(url,'/api/v1/admin/jobs/'+jid)
        assert status==200
        if body['job']['status'] not in {'QUEUED','RUNNING','CANCEL_REQUESTED'}: return body['job']
        threading.Event().wait(.05)
    raise AssertionError('Background job timed out')


def test_queued_cancellation_and_lease_recovery(db,tmp_path):
    from eju_bank.job_worker import JobWorker
    from eju_bank.review import ContentWorkspace
    job=JobManager.create_job(db,'BACKUP','workspace',{})
    assert JobManager.cancel_job(db,job['jobId'])['status']=='CANCELLED'
    JobManager.retry_job(db,job['jobId'])
    worker=JobWorker(db,ContentWorkspace(tmp_path,db))
    claimed=worker._claim();assert claimed['jobId']==job['jobId']
    other=JobWorker(db,ContentWorkspace(tmp_path,db));assert other._claim() is None
    db.connection.execute("UPDATE jobs SET lease_until='2000-01-01T00:00:00Z' WHERE id=?",(job['jobId'],));db.connection.commit()
    # 租约过期：任务先记 INTERRUPTED，然后自动排回队列等下一次尝试（规范 F14）。
    # 它不会当场被领走——退避是有意的，连续故障时不该所有任务同时回来。
    assert other._claim() is None
    recovered=JobManager.get_job(db,job['jobId'])
    assert recovered['status']=='QUEUED'
    row=db.connection.execute('SELECT attempts,next_attempt_at FROM jobs WHERE id=?',(job['jobId'],)).fetchone()
    assert row['attempts']==1 and row['next_attempt_at']
    assert db.connection.execute(
        "SELECT 1 FROM job_events WHERE job_id=? AND event_type='RETRY_SCHEDULED'",
        (job['jobId'],)).fetchone()


def test_user_cancellation_is_never_auto_resumed(db,tmp_path):
    """主动取消是一个决定，不是一次故障。自动恢复不能把它复活（规范 §9.5）。"""
    from eju_bank.job_worker import JobWorker
    from eju_bank.review import ContentWorkspace
    job=JobManager.create_job(db,'BACKUP','workspace',{})
    assert JobManager.cancel_job(db,job['jobId'])['status']=='CANCELLED'
    worker=JobWorker(db,ContentWorkspace(tmp_path,db))
    for _ in range(3):
        worker._claim()
    assert JobManager.get_job(db,job['jobId'])['status']=='CANCELLED'


def test_auto_recovery_stops_at_the_retry_budget(db,tmp_path):
    """同样的输入失败三次之后就不再自动重试——无限重试只是把故障变成忙等。"""
    from eju_bank.job_worker import JobWorker
    from eju_bank.review import ContentWorkspace
    job=JobManager.create_job(db,'BACKUP','workspace',{})
    worker=JobWorker(db,ContentWorkspace(tmp_path,db))
    for _ in range(JobWorker.MAX_ATTEMPTS+2):
        # 每一轮都把它打回中断，然后让 worker 决定要不要再排一次。
        db.connection.execute(
            "UPDATE jobs SET status='INTERRUPTED',next_attempt_at=NULL WHERE id=?",
            (job['jobId'],))
        db.connection.commit()
        worker._claim()
    row=db.connection.execute('SELECT status,attempts FROM jobs WHERE id=?',(job['jobId'],)).fetchone()
    assert row['attempts']==JobWorker.MAX_ATTEMPTS
    assert row['status']=='INTERRUPTED', '超出重试预算后应当停下来等人看'
