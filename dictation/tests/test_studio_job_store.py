"""Tests for studio_job_store SQLite persistence and lease management."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import json

from studio_job_store import StudioJobStore


class StudioJobStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._temp.name) / "test_studio.sqlite3"
        self.store = StudioJobStore(self.db_path)
        self.addCleanup(self.store.close)
        self.addCleanup(self._temp.cleanup)

    def test_job_lifecycle_and_events(self) -> None:
        job = self.store.create_job(
            job_id="job-001",
            target_type="audio",
            params={"language": "ja"},
        )
        self.assertEqual(job["id"], "job-001")
        self.assertEqual(job["executionStatus"], "queued")

        # Update job
        updated = self.store.update_job(
            "job-001",
            execution_status="running",
            outcome_code="processing",
        )
        self.assertEqual(updated["executionStatus"], "running")
        self.assertEqual(updated["outcomeCode"], "processing")
        self.assertEqual(updated["version"], 2)

        # Append events
        seq1 = self.store.append_event("job-001", "stage_started", {"stage": "extract"})
        seq2 = self.store.append_event("job-001", "stage_completed", {"stage": "extract"})
        self.assertGreater(seq2, seq1)

        events, next_seq = self.store.get_events("job-001", after_seq=0)
        self.assertGreaterEqual(len(events), 2)
        self.assertEqual(events[-1]["seq"], seq2)

    def test_lease_fencing(self) -> None:
        self.store.create_job("job-002", "audio")
        self.store.register_step("step-001", "job-002", "transcribe")

        # Worker 1 acquires lease
        ok, epoch1 = self.store.acquire_lease("step-001", "worker-1", lease_duration_sec=1)
        self.assertTrue(ok)
        self.assertEqual(epoch1, 1)

        # Worker 2 tries to acquire immediately; should fail because lease is active
        ok2, epoch2 = self.store.acquire_lease("step-001", "worker-2", lease_duration_sec=10)
        self.assertFalse(ok2)

        # Worker 1 completes with valid epoch
        done = self.store.complete_step("step-001", "worker-1", epoch1, status="completed", result_ref="artifact-1")
        self.assertTrue(done)

        # Stale epoch completion should fail
        done_stale = self.store.complete_step("step-001", "worker-1", 999, status="completed")
        self.assertFalse(done_stale)

    def test_idempotency(self) -> None:
        self.store.record_idempotency("build", "req-123", "sha-abc", {"jobId": "job-123"})
        existing = self.store.check_idempotency("build", "req-123", "sha-abc")
        self.assertEqual(existing, {"jobId": "job-123"})

        with self.assertRaises(ValueError):
            self.store.check_idempotency("build", "req-123", "sha-different")

    def test_import_legacy_builds(self) -> None:
        builds_dir = Path(self._temp.name) / "builds"
        b1 = builds_dir / "b-01"
        b1.mkdir(parents=True)
        (b1 / "build-result.json").write_text(json.dumps({
            "kind": "grammar",
            "status": "needs_review",
            "reviewRequired": True,
            "title": "Legacy Grammar",
        }))

        b2 = builds_dir / "b-02"
        b2.mkdir(parents=True)  # missing result

        count = self.store.import_legacy_builds(builds_dir)
        self.assertEqual(count, 2)
        j1 = self.store.get_job("b-01")
        self.assertIsNotNone(j1)
        self.assertEqual(j1["targetType"], "grammar")
        self.assertEqual(j1["availabilityStatus"], "quarantined")

        j2 = self.store.get_job("b-02")
        self.assertIsNotNone(j2)
        self.assertEqual(j2["outcomeCode"], "interrupted")


if __name__ == "__main__":
    unittest.main()

