"""Tests for studio_pipeline execution, lease fencing, checkpoint resume, and cancellation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import time
import unittest

from studio_job_store import StudioJobStore
from studio_resources import SlotManager
from studio_pipeline import (
    PipelineRunner,
    PipelineContext,
    PipelineCancelled,
    PipelineFencingError,
    BudgetExhaustedError,
)


class StudioPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.db_path = self.root / "studio.sqlite3"
        self.store = StudioJobStore(self.db_path)
        self.slot_manager = SlotManager(gpu_concurrency=1, cpu_concurrency=2)
        self.runner = PipelineRunner(self.store, self.slot_manager, max_workers=2)
        self.addCleanup(self._temp.cleanup)

    def test_pipeline_executes_stages_and_records_checkpoints(self) -> None:
        job_id = "job-test-01"
        self.store.create_job(job_id=job_id, target_type="course", params={"title": "Test 1"})

        executed_stages = []

        def handle_stage(ctx: PipelineContext, name: str):
            executed_stages.append(name)
            return {"ran": name, "timestamp": time.time()}

        handlers = {
            "ingest": lambda c: handle_stage(c, "ingest"),
            "extract": lambda c: handle_stage(c, "extract"),
            "validate": lambda c: {"qualityDecision": "passed"},
            "install": lambda c: {"availabilityStatus": "installed"},
        }

        work_dir = self.root / "work-01"
        future = self.runner.submit_job(job_id, handlers, work_dir)
        result = future.result(timeout=5.0)

        self.assertEqual(result["status"], "completed")
        self.assertIn("ingest", executed_stages)
        self.assertIn("extract", executed_stages)

        job = self.store.get_job(job_id)
        self.assertEqual(job["execution_status"], "completed")
        self.assertEqual(job["quality_decision"], "passed")
        self.assertEqual(job["availability_status"], "installed")

        # Checkpoints exist
        self.assertTrue((work_dir / "checkpoint_ingest.json").is_file())
        self.assertTrue((work_dir / "checkpoint_extract.json").is_file())

    def test_pipeline_cancellation_aborts_execution(self) -> None:
        job_id = "job-cancel-01"
        self.store.create_job(job_id=job_id, target_type="course")

        def slow_stage(ctx: PipelineContext):
            time.sleep(0.3)
            ctx.check_cancelled()
            return {"status": "ok"}

        handlers = {
            "ingest": lambda c: {"status": "ingested"},
            "extract": slow_stage,
            "structure": lambda c: {"status": "should_not_run"},
        }

        work_dir = self.root / "work-cancel"
        future = self.runner.submit_job(job_id, handlers, work_dir)

        # Trigger cancel
        time.sleep(0.05)
        self.runner.cancel_job(job_id)

        result = future.result(timeout=5.0)
        self.assertEqual(result["status"], "cancelled")

        job = self.store.get_job(job_id)
        self.assertEqual(job["execution_status"], "cancelled")

        # structure step should not have run
        step = self.store.get_step(job_id, "structure")
        self.assertIsNone(step)

    def test_pipeline_budget_limit_exceeded(self) -> None:
        job_id = "job-budget-01"
        self.store.create_job(job_id=job_id, target_type="course")
        self.store.set_job_budget(job_id, limit={"model_calls": 2})

        def calling_stage(ctx: PipelineContext):
            ctx.consume_budget("model_calls", 1)
            ctx.consume_budget("model_calls", 1)
            # 3rd call should trigger BudgetExhaustedError
            ctx.consume_budget("model_calls", 1)
            return {}

        handlers = {
            "extract": calling_stage,
        }

        work_dir = self.root / "work-budget"
        future = self.runner.submit_job(job_id, handlers, work_dir)
        with self.assertRaises(BudgetExhaustedError):
            future.result(timeout=5.0)

        job = self.store.get_job(job_id)
        self.assertEqual(job["execution_status"], "failed")
        self.assertEqual(job["outcome_code"], "budget_exhausted")

    def test_checkpoint_resumption_skips_completed_stages(self) -> None:
        job_id = "job-resume-01"
        self.store.create_job(job_id=job_id, target_type="course")
        work_dir = self.root / "work-resume"
        work_dir.mkdir(parents=True)

        # Pre-seed a completed stage checkpoint
        chk_data = {"ingested_files": ["audio.mp3"]}
        (work_dir / "checkpoint_ingest.json").write_text(json.dumps(chk_data), encoding="utf-8")
        self.store.upsert_step(job_id, "ingest", status="completed", checkpoint_ref="checkpoint_ingest.json")

        ingest_called = []
        extract_called = []

        handlers = {
            "ingest": lambda c: ingest_called.append(True) or {},
            "extract": lambda c: extract_called.append(c.state.get("ingest", {}).get("ingested_files")) or {},
        }

        future = self.runner.submit_job(job_id, handlers, work_dir)
        result = future.result(timeout=5.0)

        self.assertEqual(result["status"], "completed")
        # ingest should NOT have been re-executed
        self.assertEqual(len(ingest_called), 0)
        # extract should have executed and received restored state from checkpoint
        self.assertEqual(len(extract_called), 1)
        self.assertEqual(extract_called[0], ["audio.mp3"])

    def test_recover_stale_jobs(self) -> None:
        job_id = "job-stale-01"
        self.store.create_job(job_id=job_id, target_type="course")
        # Insert a step that was running with an expired lease
        step_id = f"{job_id}:extract"
        conn = self.store._get_connection()
        conn.execute(
            """
            INSERT INTO job_steps (id, job_id, stage, status, lease_owner, lease_epoch, lease_expires_at)
            VALUES (?, ?, ?, 'running', 'dead-worker', 1, datetime('now', '-10 minutes'))
            """,
            (step_id, job_id, "extract"),
        )

        recovered = self.runner.recover_stale_jobs()
        self.assertIn(job_id, recovered)
        job = self.store.get_job(job_id)
        self.assertEqual(job["execution_status"], "retry_scheduled")
