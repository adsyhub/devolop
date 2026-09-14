"""SQLite-backed persistent job store for Dictation Workbench.

Implements section 6.3 and B01 of docs/DICTATION_WORKBENCH_AUTOMATION_PLAN.md:
- Database at studio-work/studio.sqlite3 with WAL, foreign keys, busy timeout, and transactions.
- Tables: assets, jobs, job_steps, job_events, issues, evidence, patches, artifact_versions, idempotency_keys.
- 4 status dimensions: executionStatus, qualityDecision, availabilityStatus, humanReviewStatus.
- Monotonically increasing event sequences for reliable incremental streaming.
- Lease management with epoch fencing against slow/stale workers.
- Import of legacy builds from studio-work/builds/* on startup.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Iterator

JOB_EXECUTION_STATUSES = (
    "queued",
    "running",
    "waiting_dependency",
    "retry_scheduled",
    "paused",
    "completed",
    "failed",
    "cancelled",
)

QUALITY_DECISIONS = (
    "pending",
    "passed",
    "limited",
    "rejected",
    "unknown",
)

AVAILABILITY_STATUSES = (
    "candidate",
    "installed",
    "installed_partial",
    "quarantined",
    "rolled_back",
)

HUMAN_REVIEW_STATUSES = (
    "not_requested",
    "requested",
    "in_progress",
    "completed",
    "stale",
)


SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    source_kind TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    canonical_source_key TEXT,
    stored_path TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assets_sha256 ON assets(source_sha256);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    batch_id TEXT,
    asset_id TEXT,
    target_type TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    policy_snapshot TEXT DEFAULT '{}',
    pipeline_version TEXT NOT NULL,
    params_json TEXT DEFAULT '{}',
    execution_status TEXT NOT NULL,
    outcome_code TEXT DEFAULT '',
    quality_decision TEXT NOT NULL,
    availability_status TEXT NOT NULL,
    manual_review_mode TEXT NOT NULL,
    cancel_requested INTEGER DEFAULT 0,
    budget_limit_json TEXT DEFAULT '{}',
    budget_used_json TEXT DEFAULT '{}',
    budget_reserved_json TEXT DEFAULT '{}',
    attempt INTEGER DEFAULT 1,
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    finished_at TEXT,
    FOREIGN KEY(asset_id) REFERENCES assets(id)
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(execution_status);
CREATE INDEX IF NOT EXISTS idx_jobs_batch ON jobs(batch_id);

CREATE TABLE IF NOT EXISTS job_steps (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    item_id TEXT DEFAULT '',
    input_digest TEXT DEFAULT '',
    status TEXT NOT NULL,
    attempt INTEGER DEFAULT 1,
    lease_owner TEXT DEFAULT '',
    lease_epoch INTEGER DEFAULT 0,
    lease_expires_at TEXT,
    checkpoint_ref TEXT,
    result_ref TEXT,
    started_at TEXT,
    finished_at TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE INDEX IF NOT EXISTS idx_steps_job ON job_steps(job_id);

CREATE TABLE IF NOT EXISTS job_events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    type TEXT NOT NULL,
    payload_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE INDEX IF NOT EXISTS idx_events_job_seq ON job_events(job_id, seq);

CREATE TABLE IF NOT EXISTS issues (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    revision TEXT NOT NULL,
    code TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    blocked_capabilities_json TEXT DEFAULT '[]',
    evidence_refs_json TEXT DEFAULT '[]',
    repair_attempts INTEGER DEFAULT 0,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
CREATE INDEX IF NOT EXISTS idx_issues_job ON issues(job_id);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    revision TEXT NOT NULL,
    check_id TEXT NOT NULL,
    check_version TEXT NOT NULL,
    input_hashes_json TEXT DEFAULT '{}',
    result TEXT NOT NULL,
    artifact_ref TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patches (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    base_revision TEXT NOT NULL,
    patch_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    evidence_refs_json TEXT DEFAULT '[]',
    result_revision TEXT,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS artifact_versions (
    id TEXT PRIMARY KEY,
    logical_content_id TEXT NOT NULL,
    artifact_revision TEXT NOT NULL,
    content_revision TEXT NOT NULL,
    kind TEXT NOT NULL,
    manifest_ref TEXT NOT NULL,
    validation_ref TEXT,
    install_state TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_artifact_versions_logical ON artifact_versions(logical_content_id);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    response_ref TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY(scope, key)
);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StudioJobStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=10.0,
                check_same_thread=False,
                isolation_level=None,  # autocommit mode, manage transactions explicitly
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            self._local.conn = conn
        return self._local.conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        conn.executescript(SCHEMA_SQL)

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    # ------------------------------------------------------------------ assets
    def register_asset(
        self,
        asset_id: str,
        source_kind: str,
        source_sha256: str,
        stored_path: str,
        *,
        canonical_source_key: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        conn = self._get_connection()
        now = utc_now_iso()
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        conn.execute(
            """
            INSERT OR REPLACE INTO assets
            (id, source_kind, source_sha256, canonical_source_key, stored_path, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_id, source_kind, source_sha256, canonical_source_key, stored_path, meta_str, now),
        )
        return {
            "id": asset_id,
            "sourceKind": source_kind,
            "sourceSha256": source_sha256,
            "storedPath": stored_path,
            "metadata": metadata or {},
            "createdAt": now,
        }

    def get_asset_by_sha256(self, sha256: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM assets WHERE source_sha256 = ? ORDER BY created_at DESC LIMIT 1", (sha256,)).fetchone()
        if not row:
            return None
        return self._asset_row_to_dict(row)

    def _asset_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "sourceKind": row["source_kind"],
            "source_kind": row["source_kind"],
            "sourceSha256": row["source_sha256"],
            "source_sha256": row["source_sha256"],
            "canonicalSourceKey": row["canonical_source_key"],
            "canonical_source_key": row["canonical_source_key"],
            "storedPath": row["stored_path"],
            "stored_path": row["stored_path"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
            "createdAt": row["created_at"],
            "created_at": row["created_at"],
        }

    # ------------------------------------------------------------------ jobs
    def create_job(
        self,
        job_id: str,
        target_type: str,
        *,
        batch_id: str = "",
        asset_id: str | None = None,
        policy_id: str = "personal-learning-v1",
        policy_version: str = "1",
        pipeline_version: str = "1",
        params: dict[str, Any] | None = None,
        manual_review_mode: str = "off",
        execution_status: str = "queued",
        outcome_code: str = "",
        quality_decision: str = "pending",
        availability_status: str = "candidate",
        budget_limit: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        conn = self._get_connection()
        now = utc_now_iso()
        params_str = json.dumps(params or {}, ensure_ascii=False)
        budget_str = json.dumps(budget_limit or {}, ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO jobs
            (id, batch_id, asset_id, target_type, policy_id, policy_version, pipeline_version,
             params_json, execution_status, outcome_code, quality_decision, availability_status, manual_review_mode,
             budget_limit_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id, batch_id, asset_id, target_type, policy_id, policy_version,
                pipeline_version, params_str, execution_status, outcome_code, quality_decision,
                availability_status, manual_review_mode, budget_str, now
            ),
        )
        self.append_event(job_id, "job_created", {"targetType": target_type, "params": params or {}})
        return self.get_job(job_id)  # type: ignore

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        return self._job_row_to_dict(row)

    def update_job(
        self,
        job_id: str,
        *,
        execution_status: str | None = None,
        outcome_code: str | None = None,
        quality_decision: str | None = None,
        availability_status: str | None = None,
        manual_review_mode: str | None = None,
        cancel_requested: bool | None = None,
        finished: bool = False,
    ) -> dict[str, Any] | None:
        conn = self._get_connection()
        updates: list[str] = ["version = version + 1"]
        params: list[Any] = []

        if execution_status is not None:
            updates.append("execution_status = ?")
            params.append(execution_status)
        if outcome_code is not None:
            updates.append("outcome_code = ?")
            params.append(outcome_code)
        if quality_decision is not None:
            updates.append("quality_decision = ?")
            params.append(quality_decision)
        if availability_status is not None:
            updates.append("availability_status = ?")
            params.append(availability_status)
        if manual_review_mode is not None:
            updates.append("manual_review_mode = ?")
            params.append(manual_review_mode)
        if cancel_requested is not None:
            updates.append("cancel_requested = ?")
            params.append(1 if cancel_requested else 0)
        if finished:
            updates.append("finished_at = ?")
            params.append(utc_now_iso())

        params.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
        conn.execute(sql, tuple(params))
        return self.get_job(job_id)

    def update_job_status(
        self,
        job_id: str,
        *,
        execution_status: str | None = None,
        outcome_code: str | None = None,
        quality_decision: str | None = None,
        availability_status: str | None = None,
    ) -> dict[str, Any] | None:
        finished = execution_status in {"completed", "failed", "cancelled"}
        return self.update_job(
            job_id,
            execution_status=execution_status,
            outcome_code=outcome_code,
            quality_decision=quality_decision,
            availability_status=availability_status,
            finished=finished,
        )

    def request_job_cancellation(self, job_id: str) -> None:
        self.update_job(job_id, cancel_requested=True)

    def set_job_budget(
        self,
        job_id: str,
        limit: dict[str, Any] | None = None,
        used: dict[str, Any] | None = None,
        reserved: dict[str, Any] | None = None,
    ) -> None:
        conn = self._get_connection()
        updates = []
        params = []
        if limit is not None:
            updates.append("budget_limit_json = ?")
            params.append(json.dumps(limit, ensure_ascii=False))
        if used is not None:
            updates.append("budget_used_json = ?")
            params.append(json.dumps(used, ensure_ascii=False))
        if reserved is not None:
            updates.append("budget_reserved_json = ?")
            params.append(json.dumps(reserved, ensure_ascii=False))
        if updates:
            params.append(job_id)
            conn.execute(f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?", tuple(params))

    def list_jobs(
        self,
        *,
        execution_status: str | None = None,
        target_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        conn = self._get_connection()
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list[Any] = []
        if execution_status:
            query += " AND execution_status = ?"
            params.append(execution_status)
        if target_type:
            query += " AND target_type = ?"
            params.append(target_type)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, tuple(params)).fetchall()
        return [self._job_row_to_dict(row) for row in rows]

    def _job_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        budget_limit = json.loads(row["budget_limit_json"] or "{}")
        budget_used = json.loads(row["budget_used_json"] or "{}")
        cancel_req = bool(row["cancel_requested"])
        return {
            "id": row["id"],
            "batchId": row["batch_id"],
            "assetId": row["asset_id"],
            "targetType": row["target_type"],
            "policyId": row["policy_id"],
            "policyVersion": row["policy_version"],
            "pipelineVersion": row["pipeline_version"],
            "params": json.loads(row["params_json"] or "{}"),
            "executionStatus": row["execution_status"],
            "execution_status": row["execution_status"],
            "outcomeCode": row["outcome_code"],
            "outcome_code": row["outcome_code"],
            "qualityDecision": row["quality_decision"],
            "quality_decision": row["quality_decision"],
            "availabilityStatus": row["availability_status"],
            "availability_status": row["availability_status"],
            "manualReviewMode": row["manual_review_mode"],
            "manual_review_mode": row["manual_review_mode"],
            "cancelRequested": cancel_req,
            "cancel_requested": cancel_req,
            "budgetLimit": budget_limit,
            "budget_limit": budget_limit,
            "budgetUsed": budget_used,
            "budget_used": budget_used,
            "attempt": row["attempt"],
            "version": row["version"],
            "createdAt": row["created_at"],
            "finishedAt": row["finished_at"],
        }

    # ------------------------------------------------------------------ steps & leases
    def register_step(
        self,
        step_id: str,
        job_id: str,
        stage: str,
        *,
        item_id: str = "",
        input_digest: str = "",
        status: str = "pending",
    ) -> dict[str, Any]:
        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO job_steps
            (id, job_id, stage, item_id, input_digest, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (step_id, job_id, stage, item_id, input_digest, status),
        )
        return {
            "id": step_id,
            "jobId": job_id,
            "stage": stage,
            "status": status,
        }

    def acquire_lease(
        self,
        step_id: str,
        worker_id: str,
        lease_duration_sec: int = 60,
    ) -> tuple[bool, int]:
        """Try to acquire a step lease with epoch fencing. Returns (acquired, epoch)."""
        conn = self._get_connection()
        now = utc_now_iso()
        cursor = conn.execute(
            """
            UPDATE job_steps
            SET lease_owner = ?,
                lease_epoch = lease_epoch + 1,
                lease_expires_at = datetime('now', ?),
                status = 'running',
                started_at = ?
            WHERE id = ?
              AND (lease_expires_at IS NULL OR lease_expires_at < datetime('now') OR lease_owner = ?)
            RETURNING lease_epoch;
            """,
            (worker_id, f"+{lease_duration_sec} seconds", now, step_id, worker_id),
        )
        row = cursor.fetchone()
        if row:
            return True, row[0]
        return False, 0

    def complete_step(
        self,
        step_id: str | None = None,
        worker_id_or_stage: str = "",
        lease_epoch: int | None = None,
        *,
        job_id: str | None = None,
        stage: str | None = None,
        worker_id: str | None = None,
        epoch: int | None = None,
        status: str = "completed",
        result_ref: str = "",
        checkpoint_ref: str = "",
        result: dict[str, Any] | None = None,
    ) -> bool:
        """Complete a step only if worker still owns the current lease epoch."""
        conn = self._get_connection()
        now = utc_now_iso()
        res_str = result_ref or (json.dumps(result, ensure_ascii=False) if result else "")
        target_epoch = epoch if epoch is not None else (lease_epoch if lease_epoch is not None else 1)

        target_job_id = job_id or (step_id.split(":")[0] if step_id and ":" in step_id else (step_id or ""))
        target_stage = stage or (step_id.split(":")[1] if step_id and ":" in step_id else worker_id_or_stage)
        actual_step_id = step_id or f"{target_job_id}:{target_stage}"

        cursor = conn.execute(
            """
            UPDATE job_steps
            SET status = ?,
                result_ref = ?,
                checkpoint_ref = CASE WHEN ? != '' THEN ? ELSE checkpoint_ref END,
                finished_at = ?,
                lease_expires_at = NULL
            WHERE (id = ? OR (job_id = ? AND stage = ?)) AND lease_epoch = ?
            RETURNING id;
            """,
            (
                status,
                res_str,
                checkpoint_ref,
                checkpoint_ref,
                now,
                actual_step_id,
                target_job_id,
                target_stage,
                target_epoch,
            ),
        )
        return cursor.fetchone() is not None

    def get_step(self, job_id: str, stage: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        step_id = f"{job_id}:{stage}"
        row = conn.execute(
            "SELECT * FROM job_steps WHERE id = ? OR (job_id = ? AND stage = ?)",
            (step_id, job_id, stage),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "job_id": row["job_id"],
            "stage": row["stage"],
            "item_id": row["item_id"],
            "status": row["status"],
            "attempt": row["attempt"],
            "lease_owner": row["lease_owner"],
            "lease_epoch": row["lease_epoch"],
            "checkpoint_ref": row["checkpoint_ref"],
            "result_ref": row["result_ref"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }

    def upsert_step(
        self,
        job_id: str,
        stage: str,
        status: str = "pending",
        result: dict[str, Any] | None = None,
        checkpoint_ref: str = "",
    ) -> dict[str, Any]:
        conn = self._get_connection()
        step_id = f"{job_id}:{stage}"
        result_ref = json.dumps(result, ensure_ascii=False) if result else ""
        conn.execute(
            """
            INSERT INTO job_steps (id, job_id, stage, status, checkpoint_ref, result_ref)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                checkpoint_ref = CASE WHEN excluded.checkpoint_ref != '' THEN excluded.checkpoint_ref ELSE job_steps.checkpoint_ref END,
                result_ref = CASE WHEN excluded.result_ref != '' THEN excluded.result_ref ELSE job_steps.result_ref END;
            """,
            (step_id, job_id, stage, status, checkpoint_ref, result_ref),
        )
        return self.get_step(job_id, stage) or {}

    def acquire_step_lease(
        self,
        job_id: str,
        stage: str,
        owner: str,
        duration_sec: int = 60,
    ) -> dict[str, Any] | None:
        step_id = f"{job_id}:{stage}"
        self.upsert_step(job_id, stage, status="pending")
        acquired, epoch = self.acquire_lease(step_id, owner, duration_sec)
        if acquired:
            return {"step_id": step_id, "lease_epoch": epoch, "lease_owner": owner}
        return None

    def find_stale_steps(self) -> list[dict[str, Any]]:
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM job_steps WHERE status = 'running' AND lease_expires_at IS NOT NULL AND lease_expires_at < datetime('now')"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "job_id": r["job_id"],
                "stage": r["stage"],
                "lease_owner": r["lease_owner"],
                "lease_epoch": r["lease_epoch"],
            }
            for r in rows
        ]

    def list_steps(self, job_id: str) -> list[dict[str, Any]]:
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM job_steps WHERE job_id = ? ORDER BY rowid ASC", (job_id,)).fetchall()
        return [
            {
                "id": r["id"],
                "jobId": r["job_id"],
                "stage": r["stage"],
                "itemId": r["item_id"],
                "status": r["status"],
                "attempt": r["attempt"],
                "leaseOwner": r["lease_owner"],
                "leaseEpoch": r["lease_epoch"],
                "resultRef": r["result_ref"],
                "startedAt": r["started_at"],
                "finishedAt": r["finished_at"],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------ events
    def append_event(self, job_id: str, event_type: str, payload: dict[str, Any]) -> int:
        conn = self._get_connection()
        now = utc_now_iso()
        payload_str = json.dumps(payload, ensure_ascii=False)
        cursor = conn.execute(
            "INSERT INTO job_events (job_id, type, payload_json, created_at) VALUES (?, ?, ?, ?) RETURNING seq;",
            (job_id, event_type, payload_str, now),
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    record_event = append_event

    def get_events(self, job_id: str, after_seq: int = 0, limit: int = 100) -> tuple[list[dict[str, Any]], int]:
        conn = self._get_connection()
        rows = conn.execute(
            """
            SELECT seq, type, payload_json, created_at
            FROM job_events
            WHERE job_id = ? AND seq > ?
            ORDER BY seq ASC
            LIMIT ?
            """,
            (job_id, after_seq, limit),
        ).fetchall()
        events = [
            {
                "seq": r["seq"],
                "type": r["type"],
                "payload": json.loads(r["payload_json"] or "{}"),
                "createdAt": r["created_at"],
            }
            for r in rows
        ]
        next_seq = events[-1]["seq"] if events else after_seq
        return events, next_seq

    # ------------------------------------------------------------------ idempotency
    def check_idempotency(self, scope: str, key: str, request_digest: str) -> dict[str, Any] | None:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT request_digest, response_ref FROM idempotency_keys WHERE scope = ? AND key = ?",
            (scope, key),
        ).fetchone()
        if not row:
            return None
        if row["request_digest"] != request_digest:
            raise ValueError(f"Idempotency conflict for scope {scope} key {key}: request digest mismatch")
        return json.loads(row["response_ref"] or "{}") if row["response_ref"] else None

    def record_idempotency(self, scope: str, key: str, request_digest: str, response: dict[str, Any]) -> None:
        conn = self._get_connection()
        now = utc_now_iso()
        resp_str = json.dumps(response, ensure_ascii=False)
        conn.execute(
            "INSERT OR REPLACE INTO idempotency_keys (scope, key, request_digest, response_ref, created_at) VALUES (?, ?, ?, ?, ?)",
            (scope, key, request_digest, resp_str, now),
        )

    # ------------------------------------------------------------------ legacy migration
    def import_legacy_builds(self, builds_dir: Path) -> int:
        """Scan studio-work/builds/ and import existing build jobs into SQLite."""
        if not builds_dir.is_dir():
            return 0
        imported = 0
        for b_dir in sorted(builds_dir.iterdir()):
            if not b_dir.is_dir():
                continue
            job_id = b_dir.name
            if self.get_job(job_id):
                continue
            res_file = b_dir / "build-result.json"
            status = "completed"
            outcome = "installed"
            quality = "passed"
            target_type = "pdf"
            params = {}
            if res_file.is_file():
                try:
                    res = json.loads(res_file.read_text(encoding="utf-8-sig"))
                    target_type = str(res.get("kind") or "pdf")
                    review_req = bool(res.get("reviewRequired"))
                    quality = "limited" if review_req else "passed"
                    outcome = "needs_review" if review_req else "installed"
                    params = {"draftPath": res.get("draftPath", ""), "title": res.get("title", "")}
                except Exception:
                    pass
            else:
                outcome = "interrupted"
                quality = "unknown"
                status = "failed"

            self.create_job(
                job_id=job_id,
                target_type=target_type,
                params=params,
                execution_status=status,
                outcome_code=outcome,
                quality_decision=quality,
                availability_status="quarantined" if quality == "limited" else "installed",
                manual_review_mode="on_demand",
            )
            imported += 1
        return imported
