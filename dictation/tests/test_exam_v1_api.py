"""Tests for /api/v1/* HTTP routes on the live running preview server."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from support import RunningServer, write_course  # noqa: E402
from test_exam_v2_session import setup_sample_paper  # noqa: E402


class ExamV1ApiServerTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        root = Path(self._temp.name)
        manifest = write_course(root / "courses" / "demo")
        self.data_dir = root / "data"

        self.server = RunningServer(manifest, self.data_dir)
        self.server.__enter__()
        self.addCleanup(self._teardown)

        # Seed database with sample N1 paper
        self.db = self.server.preview._exam_db
        self.paper = setup_sample_paper(self.db, "N1")

    def _teardown(self):
        self.server.__exit__(None, None, None)
        self._temp.cleanup()

    def call(self, method: str, path: str, **kwargs):
        origin = kwargs.pop("origin", f"http://127.0.0.1:{self.server.port}")
        status, body = self.server.request(method, path, origin=origin, **kwargs)
        return status, (json.loads(body) if body else {})

    def test_exam_time_endpoint(self):
        """GET /api/v1/exam-time returns server time (E05)."""
        status, data = self.call("GET", "/api/v1/exam-time")
        self.assertEqual(status, 200)
        self.assertIn("serverNow", data)

    def test_papers_list_and_delivery_dto(self):
        """GET /api/v1/papers and GET /api/v1/papers/:id returns delivery DTO without answers (P05)."""
        status, data = self.call("GET", "/api/v1/papers?level=N1")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(data["papers"]), 1)

        pv_id = self.paper["paper_version_id"]
        status, paper_data = self.call("GET", f"/api/v1/papers/{pv_id}")
        self.assertEqual(status, 200)
        paper = paper_data["paper"]
        self.assertEqual(paper["level"], "N1")

        # Must not contain correct answers (P05, S08)
        paper_str = json.dumps(paper)
        self.assertNotIn("correct_answer", paper_str)
        self.assertNotIn("correctAnswer", paper_str)

    def test_session_lifecycle_and_scoring(self):
        """Session create -> start -> answer -> submit -> report workflow."""
        pv_id = self.paper["paper_version_id"]
        q1_id = self.paper["q1_v_id"]
        q2_id = self.paper["q2_v_id"]

        # 1. Create session
        status, s_data = self.call(
            "POST",
            "/api/v1/sessions",
            body={"level": "N1", "mode": "PAPER_PRACTICE", "paperVersionId": pv_id},
        )
        self.assertEqual(status, 201)
        session_id = s_data["session"]["sessionId"]

        # 2. Start session
        status, start_data = self.call("POST", f"/api/v1/sessions/{session_id}/start")
        self.assertEqual(status, 200)
        self.assertEqual(start_data["started"]["status"], "IN_PROGRESS")

        # 3. Get session state (recovery)
        status, state_data = self.call("GET", f"/api/v1/sessions/{session_id}")
        self.assertEqual(status, 200)
        self.assertEqual(state_data["session"]["status"], "IN_PROGRESS")

        # 4. Autosave answer
        status, ans_data = self.call(
            "PUT",
            f"/api/v1/sessions/{session_id}/answers/{q1_id}",
            body={"chosen": 1, "confidence": "sure", "isUncertain": False, "answerVersion": 1},
        )
        self.assertEqual(status, 200)
        self.assertTrue(ans_data["saved"])

        # 5. Submit session
        status, sub_data = self.call("POST", f"/api/v1/sessions/{session_id}/submit")
        self.assertEqual(status, 200)
        result = sub_data["result"]
        self.assertEqual(result["totals"]["correct"], 1)

        # 6. Fetch report
        status, rep_data = self.call("GET", f"/api/v1/sessions/{session_id}/report")
        self.assertEqual(status, 200)
        report = rep_data["report"]
        self.assertEqual(report["correct"], 1)
        self.assertEqual(report["total"], 2)

    def test_dynamic_practice_generation(self):
        """POST /api/v1/practice/generate assembles question groups."""
        status, data = self.call(
            "POST",
            "/api/v1/practice/generate",
            body={
                "level": "N1",
                "itemTypeCodes": ["VOCAB_KANJI_READING"],
                "requestedGroups": 2,
            },
        )
        self.assertEqual(status, 201)
        self.assertIn("sessionId", data)

    def test_admin_api_security_gated(self):
        """POST /api/v1/admin/* refuses learners (S01)."""
        status, data = self.call(
            "POST",
            "/api/v1/admin/publish",
            body={"paperVersionId": self.paper["paper_version_id"]},
            headers={"X-User-Role": "LEARNER"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(data["error"]["code"], "ADMIN_FORBIDDEN")

    def test_admin_publish_success_and_qualification_checks(self):
        """POST /api/v1/admin/publish enforces qualification checks before publishing (E02)."""
        pv_id = self.paper["paper_version_id"]
        # Valid paper should publish successfully
        status, data = self.call(
            "POST",
            "/api/v1/admin/publish",
            body={"paperVersionId": pv_id},
            headers={"X-User-Role": "ADMIN"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(data.get("published"))

        # Create an unqualified paper version (no questions)
        conn = self.db.connection
        broken_pv = "pv_broken_no_q"
        conn.execute(
            "INSERT INTO paper_versions (id, paper_id, version_number, title, status, content_hash, created_at) "
            "VALUES (?, 'paper_N1', 99, 'Broken Paper', 'DRAFT', 'h_broken', '2026-09-01T00:00:00Z')",
            (broken_pv,),
        )
        conn.commit()

        status, data = self.call(
            "POST",
            "/api/v1/admin/publish",
            body={"paperVersionId": broken_pv},
            headers={"X-User-Role": "ADMIN"},
        )
        self.assertEqual(status, 422)
        self.assertEqual(data["error"]["code"], "EXAM_NOT_QUALIFIED")


if __name__ == "__main__":
    unittest.main()


