"""Background pipeline stage execution, lease fencing, cancellation, and resume.

Implements the unified 10-stage execution pipeline:
ingest -> preflight -> extract -> structure -> enrich -> validate -> repair -> assemble -> verify_artifact -> install

Separates the four state dimensions:
- executionStatus: queued / running / waiting_dependency / retry_scheduled / paused / completed / failed / cancelled
- qualityDecision: pending / passed / limited / rejected / unknown
- availabilityStatus: candidate / installed / installed_partial / quarantined / rolled_back
- humanReviewStatus: not_requested / requested / in_progress / completed / stale
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable

from studio_job_store import (
    StudioJobStore,
    JOB_EXECUTION_STATUSES,
    QUALITY_DECISIONS,
    AVAILABILITY_STATUSES,
    HUMAN_REVIEW_STATUSES,
)
from studio_resources import SlotManager, get_slot_manager, ResourceTimeoutError, ResourceCancelledError

logger = logging.getLogger("studio_pipeline")

PIPELINE_STAGES = (
    "ingest",
    "preflight",
    "extract",
    "structure",
    "enrich",
    "validate",
    "repair",
    "assemble",
    "verify_artifact",
    "install",
)

GPU_STAGES = {"extract", "enrich", "repair"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PipelineCancelled(Exception):
    """Execution was interrupted by a cancellation request."""


class PipelineFencingError(Exception):
    """Execution was superseded by a newer lease epoch."""


class BudgetExhaustedError(Exception):
    """Job execution budget limits were exceeded."""


@dataclass
class PipelineContext:
    job_id: str
    store: StudioJobStore
    slot_manager: SlotManager
    worker_id: str
    work_dir: Path
    params: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    lease_epoch: int = 1

    def is_cancelled(self) -> bool:
        job = self.store.get_job(self.job_id)
        if not job:
            return True
        return bool(job.get("cancel_requested"))

    def check_cancelled(self) -> None:
        if self.is_cancelled():
            raise PipelineCancelled(f"Job {self.job_id} cancellation requested")

    def log(self, message: str, event_type: str = "log", payload: dict[str, Any] | None = None) -> None:
        data = {"message": message, **(payload or {})}
        self.store.record_event(self.job_id, event_type, data)
        logger.info("[%s] %s: %s", self.job_id, event_type, message)

    def consume_budget(self, kind: str, amount: int = 1) -> None:
        """Track and decrement execution budget."""
        job = self.store.get_job(self.job_id)
        if not job:
            return
        budget_limit = job.get("budget_limit") or {}
        budget_used = job.get("budget_used") or {}

        used_val = int(budget_used.get(kind, 0)) + amount
        budget_used[kind] = used_val

        limit_val = budget_limit.get(kind)
        if limit_val is not None and used_val > int(limit_val):
            self.store.update_job_status(
                self.job_id,
                execution_status="failed",
                outcome_code="budget_exhausted",
            )
            raise BudgetExhaustedError(f"Budget exceeded for {kind}: {used_val} > {limit_val}")

        self.store.set_job_budget(self.job_id, used=budget_used)


StageHandler = Callable[[PipelineContext], dict[str, Any]]


class PipelineRunner:
    """Manages background job workers, checkpoint resumption, and cancellations."""

    def __init__(
        self,
        store: StudioJobStore,
        slot_manager: SlotManager | None = None,
        max_workers: int = 4,
    ) -> None:
        self.store = store
        self.slot_manager = slot_manager or get_slot_manager()
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="studio_worker",
        )
        self._active_jobs: dict[str, concurrent.futures.Future] = {}
        self._lock = threading.RLock()

    def submit_job(
        self,
        job_id: str,
        stage_handlers: dict[str, StageHandler],
        work_dir: Path,
        params: dict[str, Any] | None = None,
    ) -> concurrent.futures.Future:
        with self._lock:
            if job_id in self._active_jobs and not self._active_jobs[job_id].done():
                return self._active_jobs[job_id]

            worker_id = f"worker-{os.getpid()}-{threading.get_ident()}-{time.monotonic()}"
            future = self.executor.submit(
                self._run_job_lifecycle,
                job_id,
                stage_handlers,
                work_dir,
                worker_id,
                params or {},
            )
            self._active_jobs[job_id] = future
            return future

    def cancel_job(self, job_id: str) -> bool:
        """Mark job cancelled and attempt to abort running future."""
        with self._lock:
            self.store.request_job_cancellation(job_id)
            future = self._active_jobs.get(job_id)
            if future and not future.done():
                future.cancel()
                self.store.record_event(job_id, "cancel_requested", {"time": utc_now_iso()})
                return True
            return False

    def recover_stale_jobs(self) -> list[str]:
        """Detect expired leases on startup and reset or fail them."""
        recovered: list[str] = []
        stale_steps = self.store.find_stale_steps()
        for step in stale_steps:
            job_id = step["job_id"]
            self.store.record_event(
                job_id,
                "lease_recovered",
                {"step_id": step["id"], "stage": step["stage"], "recovered_at": utc_now_iso()},
            )
            self.store.update_job_status(
                job_id,
                execution_status="retry_scheduled",
                outcome_code="stale_lease_recovered",
            )
            recovered.append(job_id)
        return recovered

    def _run_job_lifecycle(
        self,
        job_id: str,
        stage_handlers: dict[str, StageHandler],
        work_dir: Path,
        worker_id: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Runs the stages sequentially with lease fencing and cancellation checks."""
        ctx = PipelineContext(
            job_id=job_id,
            store=self.store,
            slot_manager=self.slot_manager,
            worker_id=worker_id,
            work_dir=work_dir,
            params=params,
        )

        try:
            ctx.check_cancelled()
            self.store.update_job_status(job_id, execution_status="running")
            ctx.log(f"Job started with worker {worker_id}", "job_started")

            # Determine stages to run
            for stage in PIPELINE_STAGES:
                ctx.check_cancelled()

                handler = stage_handlers.get(stage)
                if not handler:
                    # Record step as not_applicable instead of pretending it ran
                    self.store.upsert_step(
                        job_id=job_id,
                        stage=stage,
                        status="not_applicable",
                        result={"skipped": True, "reason": "no_stage_handler"},
                    )
                    continue

                # Check if step has already completed in a prior attempt (checkpoint resume)
                existing_step = self.store.get_step(job_id, stage)
                if existing_step and existing_step.get("status") == "completed" and existing_step.get("checkpoint_ref"):
                    ctx.log(f"Stage '{stage}' checkpoint reused from {existing_step['checkpoint_ref']}", "checkpoint_reused")
                    # Restore state from checkpoint if available
                    chk_file = work_dir / existing_step["checkpoint_ref"]
                    if chk_file.is_file():
                        try:
                            ctx.state[stage] = json.loads(chk_file.read_text(encoding="utf-8"))
                        except Exception:
                            pass
                    continue

                # Acquire step lease with epoch fencing
                lease = self.store.acquire_step_lease(job_id=job_id, stage=stage, owner=worker_id)
                if not lease:
                    raise PipelineFencingError(f"Could not acquire lease for stage {stage} on job {job_id}")
                ctx.lease_epoch = lease["lease_epoch"]

                resource_kind = "gpu" if stage in GPU_STAGES else "cpu"
                ctx.log(f"Entering stage '{stage}' (resource: {resource_kind})", "stage_start")

                # Acquire resource slot
                with self.slot_manager.acquire(
                    resource_type=resource_kind,
                    owner_id=f"{job_id}:{stage}",
                    timeout=300.0,
                    cancel_checker=ctx.is_cancelled,
                ):
                    ctx.check_cancelled()
                    stage_result = handler(ctx)
                    ctx.state[stage] = stage_result

                # Check fence epoch before committing step completion
                refreshed = self.store.get_step(job_id, stage)
                if not refreshed or refreshed.get("lease_epoch") != ctx.lease_epoch:
                    raise PipelineFencingError(f"Lease expired/superseded during stage {stage}")

                # Save checkpoint file
                work_dir.mkdir(parents=True, exist_ok=True)
                chk_name = f"checkpoint_{stage}.json"
                (work_dir / chk_name).write_text(
                    json.dumps(stage_result or {}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                self.store.complete_step(
                    job_id=job_id,
                    stage=stage,
                    epoch=ctx.lease_epoch,
                    checkpoint_ref=chk_name,
                    result=stage_result,
                )
                ctx.log(f"Stage '{stage}' completed successfully", "stage_done")

            # Finalize job outcome
            ctx.check_cancelled()
            final_avail = ctx.state.get("install", {}).get("availabilityStatus", "installed")
            final_qual = ctx.state.get("validate", {}).get("qualityDecision", "passed")
            outcome_code = "installed" if final_avail == "installed" else "quarantined"

            self.store.update_job_status(
                job_id,
                execution_status="completed",
                quality_decision=final_qual,
                availability_status=final_avail,
                outcome_code=outcome_code,
            )
            ctx.log("Job completed successfully", "job_completed", {"outcomeCode": outcome_code})
            return {"status": "completed", "outcomeCode": outcome_code, "state": ctx.state}

        except PipelineCancelled:
            ctx.log("Job execution was cancelled", "job_cancelled")
            self.store.update_job_status(
                job_id,
                execution_status="cancelled",
                outcome_code="cancelled",
            )
            return {"status": "cancelled", "outcomeCode": "cancelled"}

        except BudgetExhaustedError as exc:
            ctx.log(f"Job budget exhausted: {exc}", "budget_exhausted")
            self.store.update_job_status(
                job_id,
                execution_status="failed",
                outcome_code="budget_exhausted",
            )
            raise

        except Exception as exc:
            logger.exception("Job %s failed: %s", job_id, exc)
            ctx.log(f"Job failed with error: {exc}", "job_failed", {"error": str(exc)})
            self.store.update_job_status(
                job_id,
                execution_status="failed",
                outcome_code="failed",
            )
            raise
