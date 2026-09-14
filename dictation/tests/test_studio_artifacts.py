"""Tests for studio_artifacts immutable versioning and atomic current pointer."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from studio_artifacts import (
    commit_artifact_from_staging,
    list_artifact_versions,
    resolve_course_audio_path,
    resolve_course_manifest_path,
    rollback_artifact,
)


class StudioArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.target_dir = self.root / "courses" / "sample-course"
        self.target_dir.mkdir(parents=True)
        self.addCleanup(self._temp.cleanup)

    def test_legacy_fallback_when_no_current_json(self) -> None:
        legacy_manifest = self.target_dir / "manifest.json"
        legacy_manifest.write_text(json.dumps({"title": "Legacy Course"}), encoding="utf-8")
        resolved = resolve_course_manifest_path(self.target_dir)
        self.assertEqual(resolved, legacy_manifest)

    def test_commit_staging_and_resolve_version(self) -> None:
        staging_dir = self.root / "staging-01"
        staging_dir.mkdir(parents=True)
        (staging_dir / "manifest.json").write_text(json.dumps({"title": "Version 1"}), encoding="utf-8")
        (staging_dir / "audio.mp3").write_bytes(b"audio-data-1")

        result = commit_artifact_from_staging(self.target_dir, staging_dir)
        rev1 = result["artifactRevision"]
        self.assertTrue(rev1)

        # Check current.json exists and resolves to version dir
        current_file = self.target_dir / "current.json"
        self.assertTrue(current_file.is_file())
        resolved = resolve_course_manifest_path(self.target_dir)
        self.assertIsNotNone(resolved)
        self.assertIn(rev1, str(resolved))

        # Check audio resolution
        audio_resolved = resolve_course_audio_path(self.target_dir, "audio.mp3")
        self.assertIsNotNone(audio_resolved)
        self.assertEqual(audio_resolved.read_bytes(), b"audio-data-1")

        # Commit Version 2
        staging_dir2 = self.root / "staging-02"
        staging_dir2.mkdir(parents=True)
        (staging_dir2 / "manifest.json").write_text(json.dumps({"title": "Version 2"}), encoding="utf-8")
        (staging_dir2 / "audio.mp3").write_bytes(b"audio-data-2")

        result2 = commit_artifact_from_staging(self.target_dir, staging_dir2)
        rev2 = result2["artifactRevision"]
        self.assertNotEqual(rev1, rev2)

        # Current should now be rev2
        resolved2 = resolve_course_manifest_path(self.target_dir)
        self.assertIn(rev2, str(resolved2))

        # Test rollback to rev1
        versions = list_artifact_versions(self.target_dir)
        self.assertEqual(len(versions), 2)
        self.assertTrue(any(v["isCurrent"] and v["artifactRevision"] == rev2 for v in versions))

        rollback_artifact(self.target_dir, rev1)
        resolved_after_rollback = resolve_course_manifest_path(self.target_dir)
        self.assertIn(rev1, str(resolved_after_rollback))


if __name__ == "__main__":
    unittest.main()

