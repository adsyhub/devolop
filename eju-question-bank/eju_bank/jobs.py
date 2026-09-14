"""Background jobs and execution tracking for imports, rendering, and extraction."""

from __future__ import annotations

import json
import uuid
from typing import Any
from pathlib import Path

from datetime import datetime, timedelta, timezone
from .errors import ContractError
from .util import canonical_json, utc_now


# MAKE_PAPER 是制课台那条一键流水线：它自己把 PROBE→RENDER→OCR→校对→组装→发布
# 依次做完，而不是排出一串子任务 —— worker 同一时刻只跑一个任务，排子任务会让它们
# 永远等在队列里。
JOB_TYPES = frozenset({
    "IMPORT_SOURCE", "PROBE", "RENDER", "EXTRACT", "BACKUP",
    "OCR_TEXT", "OCR_SLOTS", "OCR_CONTRACTS", "MAKE_PAPER",
})

VALID_JOB_STATUSES = {
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "PARTIAL_FAILED",
    "FAILED",
    "CANCEL_REQUESTED",
    "CANCELLED",
    "INTERRUPTED",
}


class JobManager:
    @staticmethod
    def create_job(
        database: Any,
        job_type: str,
        target_id: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if job_type not in JOB_TYPES:
            raise ContractError("Unsupported job type")
        if not isinstance(target_id, str) or not target_id.strip() or len(target_id) > 200 or not isinstance(params, dict):
            raise ContractError("Invalid job target or parameters")
        if job_type not in JOB_TYPES or not isinstance(target_id,str) or not target_id or len(target_id)>200 or not isinstance(params,dict):raise ContractError('Invalid job request')
        if any(k.lower() in {'token','apikey','api_key','authorization','cookie'} for k in params):raise ContractError('Secrets must be configured in environment variables')
        existing=database.connection.execute("SELECT id FROM jobs WHERE job_type=? AND target_id=? AND params_json=? AND status IN ('QUEUED','RUNNING')",(job_type,target_id,canonical_json(params))).fetchone()
        if existing:return JobManager.get_job(database,existing[0])
        job_id = "job_" + uuid.uuid4().hex[:16]
        now = utc_now()
        initial_progress = {"percent": 0, "stage": "QUEUED", "pagesTotal": 0, "pagesCompleted": 0, "pagesFailed": 0}
        database.connection.execute(
            "INSERT INTO jobs (id, job_type, target_id, status, params_json, progress_json, created_at, updated_at) "
            "VALUES (?, ?, ?, 'QUEUED', ?, ?, ?, ?)",
            (job_id, job_type, target_id, canonical_json(params), canonical_json(initial_progress), now, now),
        )
        database.connection.execute(
            "INSERT INTO job_events (id, job_id, event_type, details_json, created_at) VALUES (?, ?, 'CREATED', ?, ?)",
            (str(uuid.uuid4()), job_id, canonical_json({"params": params}), now),
        )
        return JobManager.get_job(database, job_id)

    @staticmethod
    def get_job(database: Any, job_id: str) -> dict[str, Any]:
        row = database.connection.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        if not row:
            raise KeyError(job_id)
        events = database.connection.execute(
            "SELECT event_type, details_json, created_at FROM job_events WHERE job_id = ? ORDER BY created_at ASC",
            (job_id,),
        ).fetchall()
        return {
            "jobId": row["id"],
            "jobType": row["job_type"],
            "targetId": row["target_id"],
            "status": row["status"],
            "params": json.loads(row["params_json"]),
            "progress": json.loads(row["progress_json"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "events": [
                {"eventType": e["event_type"], "details": json.loads(e["details_json"]), "createdAt": e["created_at"]}
                for e in events
            ],
        }

    @staticmethod
    def list_jobs(
        database: Any,
        target_id: str | None = None,
        status: str | None = None,
        cursor: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        if type(cursor) is not int or cursor < 0 or type(limit) is not int or not 1 <= limit <= 100:
            raise ContractError("Invalid job pagination")
        if status and status not in VALID_JOB_STATUSES: raise ContractError("Invalid job status")
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list[Any] = []
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, cursor])
        rows = database.connection.execute(query, params).fetchall()
        items = []
        for r in rows:
            items.append({
                "jobId": r["id"],
                "jobType": r["job_type"],
                "targetId": r["target_id"],
                "status": r["status"],
                "progress": json.loads(r["progress_json"]),
                "createdAt": r["created_at"],
                "updatedAt": r["updated_at"],
            })
        return {"jobs": items, "cursor": cursor, "limit": limit, "nextCursor": cursor + len(items) if len(items) == limit else None}

    @staticmethod
    def update_progress(
        database: Any,
        job_id: str,
        progress: dict[str, Any],
        status: str | None = None,
    ) -> None:
        current=JobManager.get_job(database,job_id)['status']
        transitions={'QUEUED':{'RUNNING','CANCELLED'},'RUNNING':{'SUCCEEDED','PARTIAL_FAILED','FAILED','CANCEL_REQUESTED','CANCELLED','INTERRUPTED'},'CANCEL_REQUESTED':{'CANCELLED','INTERRUPTED','SUCCEEDED','FAILED'}}
        if status and status != current and status not in transitions.get(current,set()):
            raise ContractError('Invalid job state transition')
        now = utc_now()
        if status:
            if status not in VALID_JOB_STATUSES:
                raise ContractError(f"Invalid job status: {status}")
            database.connection.execute(
                "UPDATE jobs SET progress_json = ?, status = ?, updated_at = ? WHERE id = ?",
                (canonical_json(progress), status, now, job_id),
            )
            database.connection.execute(
                "INSERT INTO job_events (id, job_id, event_type, details_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), job_id, f"STATUS_{status}", canonical_json(progress), now),
            )
        else:
            database.connection.execute(
                "UPDATE jobs SET progress_json = ?, updated_at = ? WHERE id = ?",
                (canonical_json(progress), now, job_id),
            )

    @staticmethod
    def retry_job(
        database: Any,
        job_id: str,
        pages: list[int] | None = None,
        failed_only: bool = False,
    ) -> dict[str, Any]:
        if type(failed_only) is not bool or (pages is not None and (not isinstance(pages,list) or not pages or len(pages)>3000 or any(type(p) is not int or not 1 <= p <= 3000 for p in pages))):
            raise ContractError("Invalid retry selection")
        job = JobManager.get_job(database, job_id)
        if job["status"] not in {"FAILED", "PARTIAL_FAILED", "CANCELLED", "INTERRUPTED"}:
            raise ContractError(f"Job {job_id} is in status {job['status']} and cannot be retried")
        if type(failed_only) is not bool or (pages is not None and (not isinstance(pages,list) or not pages or not all(type(p) is int and p>0 for p in pages))):raise ContractError('Invalid retry selection')
        now = utc_now()
        progress = job["progress"]
        progress["percent"] = 0
        progress["stage"] = "QUEUED"
        progress["retrying"] = True
        progress["retryPages"] = pages or []
        progress["failedOnly"] = failed_only
        database.connection.execute(
            "UPDATE jobs SET status = 'QUEUED', progress_json = ?, updated_at = ? WHERE id = ?",
            (canonical_json(progress), now, job_id),
        )
        database.connection.execute(
            "INSERT INTO job_events (id, job_id, event_type, details_json, created_at) VALUES (?, ?, 'RETRY', ?, ?)",
            (str(uuid.uuid4()), job_id, canonical_json({"pages": pages, "failedOnly": failed_only}), now),
        )
        return JobManager.get_job(database, job_id)

    @staticmethod
    def cancel_job(
        database: Any,
        job_id: str,
        reason: str = "User requested cancellation",
    ) -> dict[str, Any]:
        job = JobManager.get_job(database, job_id)
        if not isinstance(reason,str) or not reason.strip() or len(reason)>500: raise ContractError("Invalid cancellation reason")
        if job["status"] in {"SUCCEEDED", "FAILED", "PARTIAL_FAILED", "CANCELLED", "INTERRUPTED"}:
            raise ContractError(f"Job {job_id} is already completed with status {job['status']}")
        now = utc_now()
        database.connection.execute(
            "UPDATE jobs SET status = CASE WHEN status='QUEUED' THEN 'CANCELLED' ELSE 'CANCEL_REQUESTED' END, updated_at = ? WHERE id = ? AND status IN ('QUEUED','RUNNING','CANCEL_REQUESTED')",
            (now, job_id),
        )
        database.connection.execute(
            "INSERT INTO job_events (id, job_id, event_type, details_json, created_at) VALUES (?, ?, 'CANCEL', ?, ?)",
            (str(uuid.uuid4()), job_id, canonical_json({"reason": reason}), now),
        )
        return JobManager.get_job(database, job_id)


def _atomic(method):
    def run(database, *args, **kwargs):
        with database._transaction():
            return method(database, *args, **kwargs)
    return run

for _name in ('create_job','update_progress','retry_job','cancel_job'):
    setattr(JobManager, _name, staticmethod(_atomic(getattr(JobManager, _name))))
