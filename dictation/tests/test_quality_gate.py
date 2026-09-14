"""FND-001 regressions: a failed course must not open.

The audit already existed and already reported the default course as failed with
90 errors. What was missing was any consequence: the verdict was attached to the
manifest and the course was served anyway.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from support import RunningServer, corrupt_sentence, write_course

from serve_course import build_preview_server


class QualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.data_dir = self.root / "data"
        self.addCleanup(self._temp.cleanup)

    def failing_course(self) -> Path:
        return write_course(
            self.root / "bad",
            sentences=[
                {
                    "id": "s_0001",
                    "start": 0.0,
                    "end": 2.0,
                    "jaText": "これはテストです。",
                    "zhTranslation": "这是一个测试。",
                    "explanation": "テスト。",
                },
                corrupt_sentence(),
            ],
        )

    def test_failed_course_refuses_to_start(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            build_preview_server(self.failing_course(), port=0, data_dir=self.data_dir)
        message = str(caught.exception)
        self.assertIn("E-COURSE-QUALITY", message)
        self.assertIn("--allow-failed-course", message)

    def test_failure_message_carries_a_diagnostic_id(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            build_preview_server(self.failing_course(), port=0, data_dir=self.data_dir)
        self.assertIn("diagnosticId", str(caught.exception))

    def test_explicit_bypass_opens_the_course_but_marks_it_blocked(self) -> None:
        preview = build_preview_server(
            self.failing_course(), port=0, data_dir=self.data_dir, allow_failed_course=True, token="t"
        )
        try:
            self.assertGreater(preview.port, 0)
        finally:
            preview.close()

    def test_bypassed_course_is_labelled_not_releasable_in_the_manifest(self) -> None:
        """The player must be able to keep saying so; a preview is not a release."""
        manifest = self.failing_course()
        with RunningServer(manifest, self.data_dir, allow_failed_course=True) as server:
            status, payload = server.request("GET", "/manifest.json")
            self.assertEqual(status, 200)
            quality = json.loads(payload)["quality"]
            self.assertEqual(quality["status"], "failed")
            self.assertTrue(quality["blocked"])
            self.assertTrue(quality["developmentBypass"])

    def test_clean_course_starts_and_is_not_marked_blocked(self) -> None:
        manifest = write_course(self.root / "good")
        with RunningServer(manifest, self.data_dir) as server:
            status, payload = server.request("GET", "/manifest.json")
            self.assertEqual(status, 200)
            quality = json.loads(payload)["quality"]
            self.assertFalse(quality["blocked"])
            self.assertFalse(quality["developmentBypass"])


class DefaultCourseTests(unittest.TestCase):
    """The shipped course is the reason this gate exists."""

    def test_default_course_passes_quality_gate(self) -> None:

        project = Path(__file__).resolve().parent.parent
        manifest_path = project / "courses" / "2010-12-N2" / "manifest.json"
        if not manifest_path.is_file():
            self.skipTest("default course not present")
        sys.path.insert(0, str(project / "src"))
        from bundle_quality import audit_manifest

        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        report = audit_manifest(manifest, require_enrichment=True)
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertIn(report["status"], ("passed", "needs_review"))


if __name__ == "__main__":
    unittest.main()
