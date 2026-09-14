"""Tests for studio_assets ingestion, hashing, and deduplication."""

from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest

from studio_job_store import StudioJobStore
from studio_assets import AssetManager


class StudioAssetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.db_path = self.root / "studio.sqlite3"
        self.store = StudioJobStore(self.db_path)
        self.assets_root = self.root / "assets"
        self.manager = AssetManager(self.store, self.assets_root)
        self.addCleanup(self._temp.cleanup)

    def test_ingest_stream_computes_sha256_and_stores_file(self) -> None:
        content = b"Sample audio payload data for dictation"
        stream = io.BytesIO(content)

        asset = self.manager.ingest_stream(stream, "sample.mp3", "audio")

        self.assertTrue(asset.id.startswith("ast_"))
        self.assertTrue(asset.stored_path.is_file())
        self.assertEqual(asset.stored_path.read_bytes(), content)
        self.assertFalse(asset.is_duplicate)

        # Ingest the same content again -> should be detected as duplicate
        stream2 = io.BytesIO(content)
        asset2 = self.manager.ingest_stream(stream2, "sample.mp3", "audio")
        self.assertTrue(asset2.is_duplicate)
        self.assertEqual(asset.id, asset2.id)
        self.assertEqual(asset.stored_path, asset2.stored_path)

    def test_find_reusable_job(self) -> None:
        content = b"Another test content"
        asset = self.manager.ingest_stream(io.BytesIO(content), "doc.pdf", "pdf")

        params = {"model": "qwen27", "language": "ja"}
        self.store.create_job(
            job_id="job-existing",
            asset_id=asset.id,
            target_type="course",
            params=params,
        )
        self.store.update_job_status(
            "job-existing",
            execution_status="completed",
            outcome_code="installed",
        )

        reusable = self.manager.find_reusable_job(
            asset_id=asset.id,
            target_type="course",
            policy_id="personal-learning-v1",
            params=params,
        )
        self.assertIsNotNone(reusable)
        self.assertEqual(reusable["id"], "job-existing")

