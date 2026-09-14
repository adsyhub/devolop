"""Unit tests for the Punch-in, Study Logs, and Analytics features."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from local_backend import compute_streaks
from support import RunningServer, write_course


class AnalyticsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        self.manifest = write_course(self.root / "course")
        self.data_dir = self.root / "data"

    def server(self) -> RunningServer:
        return RunningServer(self.manifest, self.data_dir)

    @staticmethod
    def payload(body: bytes) -> dict[str, Any]:
        return json.loads(body.decode("utf-8"))

    def test_compute_streaks_helper(self) -> None:
        today = date.today()
        d0 = today.isoformat()
        d1 = (today - timedelta(days=1)).isoformat()
        d2 = (today - timedelta(days=2)).isoformat()
        d4 = (today - timedelta(days=4)).isoformat()
        d5 = (today - timedelta(days=5)).isoformat()
        d6 = (today - timedelta(days=6)).isoformat()
        d7 = (today - timedelta(days=7)).isoformat()

        # Consecutive 3 days up to today
        curr, max_s = compute_streaks([d0, d1, d2])
        self.assertEqual(curr, 3)
        self.assertEqual(max_s, 3)

        # Longer past streak of 4 days, current streak of 3 days
        curr, max_s = compute_streaks([d0, d1, d2, d4, d5, d6, d7])
        self.assertEqual(curr, 3)
        self.assertEqual(max_s, 4)

        # User hasn't checked in yet today, but checked in yesterday
        curr, max_s = compute_streaks([d1, d2])
        self.assertEqual(curr, 2)
        self.assertEqual(max_s, 2)

        # Empty list
        curr, max_s = compute_streaks([])
        self.assertEqual(curr, 0)
        self.assertEqual(max_s, 0)

    def test_punch_in_endpoint(self) -> None:
        """Manual punch in records note, mood, and returns current streak."""
        with self.server() as server:
            today_str = date.today().isoformat()
            status, body = server.request("POST", "/api/punch-in", body={
                "day": today_str,
                "note": "坚持打卡第一天！",
                "mood": "🔥",
                "sentencesCount": 5,
                "studyDurationMs": 120000,
            })
            self.assertEqual(status, 200, body)
            data = self.payload(body)
            self.assertTrue(data["ok"])
            self.assertEqual(data["currentStreak"], 1)
            self.assertEqual(data["punch"]["note"], "坚持打卡第一天！")
            self.assertEqual(data["punch"]["mood"], "🔥")

            # Check punch records list
            status, body = server.request("GET", "/api/punch-records")
            self.assertEqual(status, 200, body)
            records = self.payload(body)["records"]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["day"], today_str)

    def test_study_log_and_filter_endpoint(self) -> None:
        """Recording study logs allows filtering by status and course."""
        with self.server() as server:
            # 1. Record a correct answer
            status, body = server.request("POST", "/api/study-log", body={
                "courseId": "c_test",
                "sentenceId": "s_0001",
                "userInput": "正しい文",
                "isCorrect": True,
                "score": 100.0,
                "durationMs": 15000,
                "hintCount": 0,
                "mode": "dictation",
            })
            self.assertEqual(status, 201, body)
            log1 = self.payload(body)["log"]
            self.assertTrue(log1["isCorrect"])
            self.assertEqual(log1["durationMs"], 15000)

            # 2. Record a wrong answer
            status, body = server.request("POST", "/api/study-log", body={
                "courseId": "c_test",
                "sentenceId": "s_0002",
                "userInput": "間違い文",
                "isCorrect": False,
                "score": 60.0,
                "durationMs": 25000,
                "hintCount": 1,
                "mode": "dictation",
            })
            self.assertEqual(status, 201, body)

            # 3. Query all logs
            status, body = server.request("GET", "/api/study-logs?courseId=c_test")
            self.assertEqual(status, 200, body)
            data = self.payload(body)
            self.assertEqual(data["total"], 2)
            self.assertEqual(len(data["items"]), 2)

            # 4. Filter only wrong logs
            status, body = server.request("GET", "/api/study-logs?status=wrong")
            self.assertEqual(status, 200, body)
            data_wrong = self.payload(body)
            self.assertEqual(data_wrong["total"], 1)
            self.assertEqual(data_wrong["items"][0]["sentenceId"], "s_0002")

            # 5. Clear study logs
            status, body = server.request("DELETE", "/api/study-logs?courseId=c_test")
            self.assertEqual(status, 200, body)
            self.assertEqual(self.payload(body)["deleted"], 2)

            status, body = server.request("GET", "/api/study-logs")
            self.assertEqual(self.payload(body)["total"], 0)

    def test_study_log_local_day_and_date_range_filters(self) -> None:
        """Local calendar ranges must not depend on the UTC timestamp prefix."""
        with self.server() as server:
            today = date.today()
            days = [today - timedelta(days=offset) for offset in (0, 6, 8)]
            for index, local_day in enumerate(days):
                status, body = server.request("POST", "/api/study-log", body={
                    "id": f"local_log_range_{index}",
                    "courseId": "c_test",
                    "sentenceId": f"s_{index}",
                    "isCorrect": True,
                    "score": 100,
                    "localDay": local_day.isoformat(),
                })
                self.assertEqual(status, 201, body)

            status, body = server.request(
                "GET",
                f"/api/study-logs?dateFrom={days[1].isoformat()}&dateTo={days[0].isoformat()}",
            )
            self.assertEqual(status, 200, body)
            self.assertEqual(self.payload(body)["total"], 2)

            status, body = server.request(
                "GET", f"/api/study-logs?day={days[2].isoformat()}"
            )
            self.assertEqual(status, 200, body)
            self.assertEqual(self.payload(body)["items"][0]["localDay"], days[2].isoformat())

    def test_analytics_aggregation_endpoint(self) -> None:
        """Analytics endpoint aggregates summary, heatmap, trends, weak points, and diagnostics."""
        with self.server() as server:
            # Setup progress
            server.request("POST", "/api/progress", body={
                "courseId": "c_test",
                "sentenceId": "s_0001",
                "completed": True,
                "mastered": True,
                "attempts": 1,
                "lastScore": 100.0,
            })
            server.request("POST", "/api/progress", body={
                "courseId": "c_test",
                "sentenceId": "s_0002",
                "completed": True,
                "mastered": False,
                "attempts": 3,
                "lastScore": 50.0,
            })

            # Setup study log
            server.request("POST", "/api/study-log", body={
                "courseId": "c_test",
                "sentenceId": "s_0001",
                "userInput": "文1",
                "isCorrect": True,
                "score": 100.0,
                "durationMs": 10000,
            })
            server.request("POST", "/api/study-log", body={
                "courseId": "c_test",
                "sentenceId": "s_0002",
                "userInput": "文2",
                "isCorrect": False,
                "score": 50.0,
                "durationMs": 20000,
            })
            server.request("POST", "/api/study-log", body={
                "courseId": "another_course",
                "sentenceId": "s_other",
                "userInput": "別のコース",
                "isCorrect": True,
                "score": 100.0,
                "durationMs": 5000,
            })

            # Fetch analytics
            status, body = server.request("GET", "/api/analytics?courseId=c_test")
            self.assertEqual(status, 200, body)
            analytics = self.payload(body)["analytics"]

            summary = analytics["summary"]
            self.assertEqual(summary["totalPracticed"], 2)
            self.assertEqual(summary["totalMastered"], 1)
            self.assertEqual(summary["firstTryCorrect"], 1)
            self.assertEqual(summary["totalAttempts"], 2)
            self.assertEqual(summary["overallAccuracy"], 50.0)
            self.assertEqual(summary["totalDurationMs"], 30000)

            # Check heatmap
            heatmap = analytics["heatmap"]
            self.assertEqual(len(heatmap), 90)
            today_entry = heatmap[-1]
            self.assertTrue(today_entry["punched"])
            self.assertEqual(today_entry["attempts"], 2)

            # Check trends
            trends = analytics["trends"]
            self.assertIn("last7Days", trends)
            self.assertEqual(trends["last7Days"]["attempts"], 2)

            # Check weak points (s_0002 was failed)
            weak_points = analytics["weakPoints"]
            self.assertEqual(len(weak_points), 1)
            self.assertEqual(weak_points[0]["sentenceId"], "s_0002")

            # Check diagnostics
            diagnostics = analytics["diagnostics"]
            self.assertIsInstance(diagnostics, list)
            self.assertTrue(len(diagnostics) > 0)

            status, body = server.request("GET", "/api/analytics?scope=all")
            self.assertEqual(status, 200, body)
            all_analytics = self.payload(body)["analytics"]
            self.assertEqual(all_analytics["scope"], "allListening")
            self.assertEqual(all_analytics["summary"]["totalAttempts"], 3)
            self.assertEqual(all_analytics["heatmap"][-1]["attempts"], 3)


if __name__ == "__main__":
    unittest.main()
