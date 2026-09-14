"""The `/api/exams*` routes, against a real server on an ephemeral port.

Two things are being defended here. The first is arithmetic: an attempt must score
what the learner actually answered, and the wrong-answer book must distinguish
"knew it", "guessed it", "got it wrong" and "never reached it", because those four
lead to different revision. The second is the boundary: exam history is personal
data on a loopback port, and it gets exactly the same treatment as the vocabulary
notebook — Host allowlist, session token on reads as well as writes, and no path
that will read a file outside `exams/`.
"""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from exam_fixtures import make_exam, scorable, write_exam  # noqa: E402
from support import RunningServer, write_course  # noqa: E402


class ExamApiTestCase(unittest.TestCase):
    """A server with one course and one fixture exam."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        root = Path(self._temp.name)
        manifest = write_course(root / "courses" / "demo")
        self.exams_root = root / "exams"
        self.exam = make_exam()
        write_exam(self.exams_root, "fixture-N1", self.exam)
        self.questions = scorable(self.exam)

        self.server = RunningServer(manifest, root / "data", exams_root=self.exams_root)
        self.server.__enter__()
        self.addCleanup(self._teardown)

    def _teardown(self):
        self.server.__exit__(None, None, None)
        self._temp.cleanup()

    def call(self, method, path, **kwargs):
        origin = kwargs.pop("origin", f"http://127.0.0.1:{self.server.port}")
        status, body = self.server.request(method, path, origin=origin, **kwargs)
        return status, (json.loads(body) if body else {})

    def start_attempt(self, mode="practice", scope="", question_ids=None):
        body = {"mode": mode, "scope": scope}
        if question_ids is not None:
            body["questionIds"] = question_ids
        status, data = self.call("POST", "/api/exams/fixture-N1/attempts", body=body)
        self.assertEqual(status, 201, data)
        return data["attempt"]["id"]

    def answer(self, attempt, entries):
        status, data = self.call(
            "POST", "/api/exams/fixture-N1/answers", body={"attemptId": attempt, "answers": entries}
        )
        return status, data


class ListingTests(ExamApiTestCase):
    def test_the_listing_summarises_without_shipping_every_question(self):
        status, data = self.call("GET", "/api/exams")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["exams"]), 1)
        summary = data["exams"][0]
        self.assertEqual(summary["slug"], "fixture-N1")
        self.assertEqual(summary["questionCount"], 8)
        self.assertEqual(summary["quality"]["status"], "passed")
        self.assertNotIn("parts", summary)

    def test_a_single_exam_comes_back_whole(self):
        status, data = self.call("GET", "/api/exams/fixture-N1")
        self.assertEqual(status, 200)
        self.assertEqual(data["exam"]["examId"], self.exam["examId"])
        self.assertEqual(len(data["exam"]["sections"]), 3)

    def test_a_missing_exam_is_a_404(self):
        status, _ = self.call("GET", "/api/exams/nope")
        self.assertEqual(status, 404)

    def test_an_exam_that_failed_its_audit_is_not_served_for_study(self):
        """Same fail-closed rule as courses: a bad key would teach the wrong answer."""
        broken = make_exam()
        broken["sections"][0]["parts"][0]["questions"][0]["answer"] = None
        write_exam(self.exams_root, "broken-N1", broken)

        status, data = self.call("GET", "/api/exams/broken-N1")
        self.assertEqual(status, 422)
        self.assertGreater(data["quality"]["errors"], 0)

        status, listing = self.call("GET", "/api/exams")
        by_slug = {row["slug"]: row for row in listing["exams"]}
        self.assertTrue(by_slug["broken-N1"]["broken"])
        self.assertFalse(by_slug["fixture-N1"]["broken"])

    def test_one_unreadable_exam_does_not_hide_the_others(self):
        (self.exams_root / "corrupt").mkdir(parents=True)
        (self.exams_root / "corrupt" / "exam.json").write_text("{not json", encoding="utf-8")
        status, data = self.call("GET", "/api/exams")
        self.assertEqual(status, 200)
        slugs = {row["slug"] for row in data["exams"]}
        self.assertEqual(slugs, {"fixture-N1", "corrupt"})
        self.assertTrue(next(row for row in data["exams"] if row["slug"] == "corrupt")["broken"])


class AttemptTests(ExamApiTestCase):
    def test_an_attempt_scores_what_was_actually_answered(self):
        attempt = self.start_attempt()
        first, second = self.questions[0], self.questions[1]
        status, _ = self.answer(attempt, [
            {"questionId": first["id"], "chosen": first["answer"], "confidence": "sure"},
            {"questionId": second["id"], "chosen": (second["answer"] % 4) + 1, "confidence": "unsure"},
        ])
        self.assertEqual(status, 200)

        status, data = self.call("POST", "/api/exams/fixture-N1/finish",
                                 body={"attemptId": attempt, "elapsedMs": 1234})
        self.assertEqual(status, 200)
        totals = data["score"]["totals"]
        self.assertEqual(totals["correct"], 1)
        self.assertEqual(totals["wrong"], 1)
        self.assertEqual(totals["unanswered"], len(self.questions) - 2)
        self.assertEqual(totals["earned"], first["points"])

    def test_answering_the_same_question_twice_keeps_only_the_last_choice(self):
        attempt = self.start_attempt()
        question = self.questions[0]
        wrong = (question["answer"] % 4) + 1
        self.answer(attempt, [{"questionId": question["id"], "chosen": wrong}])
        self.answer(attempt, [{"questionId": question["id"], "chosen": question["answer"]}])

        status, data = self.call("POST", "/api/exams/fixture-N1/finish", body={"attemptId": attempt})
        self.assertEqual(data["score"]["totals"]["correct"], 1)
        self.assertEqual(data["score"]["totals"]["wrong"], 0)

    def test_an_explicit_non_answer_is_recorded_without_being_marked_wrong(self):
        attempt = self.start_attempt()
        question = self.questions[0]
        status, _ = self.answer(attempt, [{"questionId": question["id"], "chosen": None}])
        self.assertEqual(status, 200)

        _, review = self.call("GET", "/api/exams/fixture-N1/review")
        record = review["review"]["questions"][question["id"]]
        self.assertEqual(record["lastResult"], "skipped")
        self.assertEqual(record["wrong"], 0)

    def test_review_summary_aggregates_all_papers_in_one_request(self):
        attempt = self.start_attempt()
        question = self.questions[0]
        wrong = (question["answer"] % question["choiceCount"]) + 1
        status, _ = self.answer(attempt, [{"questionId": question["id"], "chosen": wrong}])
        self.assertEqual(status, 200)

        status, data = self.call("GET", "/api/exams/review-summary")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["exams"]), 1)
        summary = data["exams"][0]
        self.assertEqual(summary["examSlug"], "fixture-N1")
        self.assertEqual(summary["wrongCount"], 1)
        self.assertEqual(summary["questions"][0]["questionId"], question["id"])
        self.assertEqual(summary["questions"][0]["lastResult"], "wrong")

    def test_the_worked_example_cannot_be_answered(self):
        attempt = self.start_attempt()
        example = next(
            question
            for section in self.exam["sections"]
            for part in section["parts"]
            for question in part["questions"]
            if question.get("example")
        )
        status, data = self.answer(attempt, [{"questionId": example["id"], "chosen": 1}])
        self.assertEqual(status, 200)
        self.assertEqual(data["recorded"], 0)

    def test_a_choice_outside_the_printed_range_is_rejected(self):
        attempt = self.start_attempt()
        three_choice = next(q for q in self.questions if q["choiceCount"] == 3)
        status, data = self.answer(attempt, [{"questionId": three_choice["id"], "chosen": 4}])
        self.assertEqual(status, 400)
        self.assertIn("between 1 and 3", data["error"])

    def test_an_unknown_question_id_is_rejected(self):
        attempt = self.start_attempt()
        status, _ = self.answer(attempt, [{"questionId": "q_" + "0" * 24, "chosen": 1}])
        self.assertEqual(status, 400)

    def test_an_unknown_attempt_is_a_404(self):
        status, _ = self.answer("nope", [{"questionId": self.questions[0]["id"], "chosen": 1}])
        self.assertEqual(status, 404)

    def test_an_invalid_mode_is_rejected(self):
        status, _ = self.call("POST", "/api/exams/fixture-N1/attempts", body={"mode": "cheat"})
        self.assertEqual(status, 400)

    def test_attempts_are_listed_newest_first_with_their_score(self):
        first = self.start_attempt(mode="practice", scope="問題1")
        self.call("POST", "/api/exams/fixture-N1/finish", body={"attemptId": first})
        second = self.start_attempt(mode="exam", scope="全卷")
        self.call("POST", "/api/exams/fixture-N1/finish", body={"attemptId": second})

        status, data = self.call("GET", "/api/exams/fixture-N1/attempts")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["attempts"]), 2)
        self.assertEqual(data["attempts"][0]["mode"], "exam")
        self.assertIsNotNone(data["attempts"][0]["totals"])

    def test_an_attempt_can_be_read_back_answer_by_answer(self):
        attempt = self.start_attempt()
        question = self.questions[0]
        self.answer(attempt, [{"questionId": question["id"], "chosen": question["answer"], "confidence": "sure"}])
        status, data = self.call("GET", f"/api/exam-attempts/{attempt}")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["attempt"]["answers"]), 1)
        self.assertTrue(data["attempt"]["answers"][0]["correct"])
        self.assertEqual(data["attempt"]["answers"][0]["confidence"], "sure")

    def test_an_unfinished_attempt_reports_resumable_progress(self):
        scoped = self.questions[:3]
        attempt = self.start_attempt(question_ids=[q["id"] for q in scoped])
        self.answer(attempt, [{"questionId": scoped[0]["id"], "chosen": scoped[0]["answer"]}])

        status, listing = self.call("GET", "/api/exams")
        self.assertEqual(status, 200)
        summary = next(item for item in listing["exams"] if item["slug"] == "fixture-N1")
        progress = summary["progress"]
        self.assertEqual(progress["status"], "in-progress")
        self.assertEqual(progress["activeAttempt"]["id"], attempt)
        self.assertEqual(progress["activeAttempt"]["answeredCount"], 1)
        self.assertEqual(progress["activeAttempt"]["questionCount"], 3)

        _, detail = self.call("GET", f"/api/exam-attempts/{attempt}")
        self.assertEqual(detail["attempt"]["questionIds"], [q["id"] for q in scoped])

    def test_an_unfinished_attempt_can_be_abandoned_but_not_finished_or_answered(self):
        attempt = self.start_attempt(question_ids=[self.questions[0]["id"]])
        status, data = self.call("POST", f"/api/exam-attempts/{attempt}/abandon", body={})
        self.assertEqual(status, 200, data)
        self.assertTrue(data["abandonedAt"])

        _, attempts = self.call("GET", "/api/exams/fixture-N1/attempts")
        self.assertTrue(attempts["attempts"][0]["abandonedAt"])
        status, _ = self.answer(attempt, [{"questionId": self.questions[0]["id"], "chosen": 1}])
        self.assertEqual(status, 400)
        status, _ = self.call("POST", "/api/exams/fixture-N1/finish", body={"attemptId": attempt})
        self.assertEqual(status, 400)


class ScopedAttemptTests(ExamApiTestCase):
    """A session that practises one 問題 must be scored out of that 問題."""

    def test_a_scoped_attempt_is_scored_out_of_its_own_questions(self):
        scoped = self.questions[:2]
        attempt = self.start_attempt(scope="問題1", question_ids=[q["id"] for q in scoped])
        self.answer(attempt, [{"questionId": q["id"], "chosen": q["answer"]} for q in scoped])

        status, data = self.call("POST", "/api/exams/fixture-N1/finish", body={"attemptId": attempt})
        self.assertEqual(status, 200)
        totals = data["score"]["totals"]
        self.assertEqual(totals["questions"], 2)
        self.assertEqual(totals["points"], sum(q["points"] for q in scoped))
        self.assertEqual(totals["percent"], 100.0)
        self.assertEqual(totals["unanswered"], 0)

    def test_a_scoped_report_omits_the_parts_it_never_asked_about(self):
        scoped = self.questions[:2]
        attempt = self.start_attempt(question_ids=[q["id"] for q in scoped])
        _, data = self.call("POST", "/api/exams/fixture-N1/finish", body={"attemptId": attempt})
        self.assertEqual([row["id"] for row in data["score"]["parts"]], ["s1-m1"])
        self.assertEqual([row["id"] for row in data["score"]["sections"]], ["s1"])

    def test_an_unscoped_attempt_is_still_scored_over_the_whole_paper(self):
        attempt = self.start_attempt()
        _, data = self.call("POST", "/api/exams/fixture-N1/finish", body={"attemptId": attempt})
        self.assertEqual(data["score"]["totals"]["questions"], len(self.questions))
        self.assertEqual(data["score"]["totals"]["points"], self.exam["totalPoints"])

    def test_question_ids_from_another_exam_are_refused(self):
        status, _ = self.call(
            "POST", "/api/exams/fixture-N1/attempts",
            body={"mode": "practice", "questionIds": ["q_" + "0" * 24]},
        )
        self.assertEqual(status, 400)

    def test_the_scoped_question_count_is_reported_back(self):
        scoped = self.questions[:3]
        status, data = self.call(
            "POST", "/api/exams/fixture-N1/attempts",
            body={"mode": "practice", "questionIds": [q["id"] for q in scoped]},
        )
        self.assertEqual(data["attempt"]["questionCount"], 3)

    def test_an_older_database_without_the_scope_column_is_migrated(self):
        """A learner who used an earlier build must not hit "no such column"."""
        import sqlite3

        from exam_store import ExamProgress

        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(
            "CREATE TABLE exam_attempts (id TEXT PRIMARY KEY, exam_id TEXT NOT NULL, "
            "exam_slug TEXT NOT NULL, mode TEXT NOT NULL, scope TEXT NOT NULL DEFAULT '', "
            "started_at TEXT NOT NULL, finished_at TEXT, elapsed_ms INTEGER NOT NULL DEFAULT 0, "
            "score_json TEXT);"
        )
        connection.execute(
            "INSERT INTO exam_attempts (id, exam_id, exam_slug, mode, started_at) "
            "VALUES ('old', ?, 'fixture-N1', 'practice', '2026-01-01T00:00:00+09:00')",
            (self.exam["examId"],),
        )
        connection.commit()

        progress = ExamProgress(connection)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(exam_attempts)")}
        self.assertIn("question_ids", columns)
        self.assertIn("abandoned_at", columns)
        # The pre-existing row survives and still scores, over the whole paper.
        result = progress.finish_attempt(self.exam, "old")
        self.assertEqual(result["score"]["totals"]["questions"], len(self.questions))


class ReviewBookTests(ExamApiTestCase):
    def test_a_confident_correct_answer_advances_the_streak(self):
        attempt = self.start_attempt()
        question = self.questions[0]
        self.answer(attempt, [{"questionId": question["id"], "chosen": question["answer"], "confidence": "sure"}])
        _, data = self.call("GET", "/api/exams/fixture-N1/review")
        record = data["review"]["questions"][question["id"]]
        self.assertEqual(record["lastResult"], "correct")
        self.assertEqual(record["streak"], 1)
        self.assertFalse(record["due"])

    def test_a_lucky_guess_does_not_advance_anything(self):
        """A correct-by-guess answer is not evidence of knowing it."""
        attempt = self.start_attempt()
        question = self.questions[0]
        self.answer(attempt, [{"questionId": question["id"], "chosen": question["answer"], "confidence": "guess"}])
        _, data = self.call("GET", "/api/exams/fixture-N1/review")
        record = data["review"]["questions"][question["id"]]
        self.assertEqual(record["lastResult"], "guessed")
        self.assertEqual(record["streak"], 0)

    def test_a_wrong_answer_resets_a_streak_that_had_been_building(self):
        question = self.questions[0]
        for _ in range(3):
            attempt = self.start_attempt()
            self.answer(attempt, [{"questionId": question["id"], "chosen": question["answer"], "confidence": "sure"}])
        _, data = self.call("GET", "/api/exams/fixture-N1/review")
        self.assertEqual(data["review"]["questions"][question["id"]]["streak"], 3)

        attempt = self.start_attempt()
        self.answer(attempt, [{"questionId": question["id"], "chosen": (question["answer"] % 4) + 1}])
        _, data = self.call("GET", "/api/exams/fixture-N1/review")
        record = data["review"]["questions"][question["id"]]
        self.assertEqual(record["streak"], 0)
        self.assertEqual(record["wrong"], 1)
        self.assertEqual(record["seen"], 4)

    def test_the_due_date_stretches_as_the_streak_grows(self):
        question = self.questions[0]
        seen = []
        for _ in range(3):
            attempt = self.start_attempt()
            self.answer(attempt, [{"questionId": question["id"], "chosen": question["answer"], "confidence": "sure"}])
            _, data = self.call("GET", "/api/exams/fixture-N1/review")
            seen.append(data["review"]["questions"][question["id"]]["dueOn"])
        self.assertEqual(seen, sorted(seen))
        self.assertLess(seen[0], seen[-1])

    def test_marking_and_note_survive_a_round_trip(self):
        question = self.questions[0]
        status, data = self.call("POST", "/api/exams/fixture-N1/mark",
                                 body={"questionId": question["id"], "marked": True, "note": "施錠 せじょう"})
        self.assertEqual(status, 200)
        self.assertTrue(data["item"]["marked"])

        _, review = self.call("GET", "/api/exams/fixture-N1/review")
        record = review["review"]["questions"][question["id"]]
        self.assertTrue(record["marked"])
        self.assertEqual(record["note"], "施錠 せじょう")

    def test_marking_an_unknown_question_is_rejected(self):
        status, _ = self.call("POST", "/api/exams/fixture-N1/mark",
                              body={"questionId": "q_" + "0" * 24, "marked": True})
        self.assertEqual(status, 400)

    def test_stats_count_wrong_skipped_and_marked_separately(self):
        attempt = self.start_attempt()
        wrong, skipped = self.questions[0], self.questions[1]
        self.answer(attempt, [
            {"questionId": wrong["id"], "chosen": (wrong["answer"] % 4) + 1},
            {"questionId": skipped["id"], "chosen": None},
        ])
        self.call("POST", "/api/exams/fixture-N1/mark", body={"questionId": wrong["id"], "marked": True})

        status, data = self.call("GET", "/api/exams/fixture-N1/stats")
        self.assertEqual(status, 200)
        stats = data["stats"]
        self.assertEqual(stats["wrongCount"], 1)
        self.assertEqual(stats["skippedCount"], 1)
        self.assertEqual(stats["markedCount"], 1)
        self.assertEqual(stats["attempts"], 1)

    def test_stats_break_down_by_part(self):
        status, data = self.call("GET", "/api/exams/fixture-N1/stats")
        parts = {row["partId"]: row for row in data["stats"]["parts"]}
        self.assertEqual(parts["s1-m1"]["questions"], 2)
        self.assertEqual(parts["s3-m1"]["questions"], 1)  # the 例 is not counted

    def test_resetting_removes_attempts_and_the_review_book(self):
        attempt = self.start_attempt()
        question = self.questions[0]
        self.answer(attempt, [{"questionId": question["id"], "chosen": question["answer"]}])
        self.call("POST", "/api/exams/fixture-N1/mark", body={"questionId": question["id"], "marked": True})

        status, data = self.call("DELETE", "/api/exams/fixture-N1/progress")
        self.assertEqual(status, 200)
        self.assertEqual(data["attemptsRemoved"], 1)

        _, review = self.call("GET", "/api/exams/fixture-N1/review")
        self.assertEqual(review["review"]["questions"], {})
        _, attempts = self.call("GET", "/api/exams/fixture-N1/attempts")
        self.assertEqual(attempts["attempts"], [])


class BoundaryTests(ExamApiTestCase):
    def test_reads_require_a_token_just_like_the_notebook(self):
        for path in ("/api/exams", "/api/exams/fixture-N1", "/api/exams/fixture-N1/review"):
            status, _ = self.server.request("GET", path, token=None)
            self.assertEqual(status, 403, path)

    def test_a_forged_host_is_refused(self):
        status, _ = self.server.request("GET", "/api/exams", host="evil.example")
        self.assertEqual(status, 403)

    def test_a_write_from_another_origin_is_refused(self):
        status, _ = self.server.request(
            "POST", "/api/exams/fixture-N1/attempts", origin="http://evil.example", body={"mode": "practice"}
        )
        self.assertEqual(status, 403)

    def test_a_cross_site_fetch_is_refused(self):
        status, _ = self.server.request(
            "GET", "/api/exams", headers={"Sec-Fetch-Site": "cross-site"}
        )
        self.assertEqual(status, 403)

    def test_a_slug_cannot_climb_out_of_the_exams_directory(self):
        outside = self.exams_root.parent / "secret.json"
        outside.write_text(json.dumps(make_exam()), encoding="utf-8")
        for slug in ("..%2Fsecret", "..", "%2e%2e%2f%2e%2e", "..%5Csecret"):
            status, _ = self.call("GET", f"/api/exams/{slug}")
            self.assertIn(status, (400, 404), slug)

    def test_an_attempt_cannot_be_pointed_at_a_different_exam(self):
        other = make_exam(title="Other paper")
        write_exam(self.exams_root, "other-N1", other)
        attempt = self.start_attempt()
        status, data = self.call(
            "POST", "/api/exams/other-N1/answers",
            body={"attemptId": attempt, "answers": [{"questionId": self.questions[0]["id"], "chosen": 1}]},
        )
        self.assertEqual(status, 400)
        self.assertIn("different exam", data["error"])

    def test_an_oversized_answer_batch_is_refused(self):
        attempt = self.start_attempt()
        question = self.questions[0]
        status, _ = self.answer(attempt, [{"questionId": question["id"], "chosen": 1}] * 501)
        self.assertEqual(status, 400)

    def test_a_malformed_confidence_value_is_refused(self):
        attempt = self.start_attempt()
        status, _ = self.answer(
            attempt, [{"questionId": self.questions[0]["id"], "chosen": 1, "confidence": "certain"}]
        )
        self.assertEqual(status, 400)

    def test_the_exam_page_and_its_assets_are_served(self):
        for path in ("/exam.html", "/exam.css", "/exam.js", "/exam_markup.js"):
            status, body = self.server.request("GET", path, token=None)
            self.assertEqual(status, 200, path)
            self.assertGreater(len(body), 200, path)

    def test_product_routes_keep_listening_exams_and_personal_separate(self):
        expected = {
            "/": b'id="boards"',
            "/listening": b'id="view-library"',
            "/exams": b'id="exam-main"',
            "/me": b'id="personal-main"',
        }
        for path, marker in expected.items():
            status, body = self.server.request("GET", path, token=None)
            self.assertEqual(status, 200, path)
            self.assertIn(marker, body, path)

        for path in ("/listening/", "/exams/", "/me/"):
            connection = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=5)
            try:
                connection.request("GET", path, headers={"Host": self.server.host_header})
                response = connection.getresponse()
                response.read()
                self.assertEqual(response.status, 308, path)
                self.assertEqual(response.getheader("Location"), path.rstrip("/"), path)
            finally:
                connection.close()


class NoExamsDirectoryTests(unittest.TestCase):
    def test_a_project_without_any_exams_still_serves_the_player(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = write_course(root / "courses" / "demo")
            with RunningServer(manifest, root / "data", exams_root=root / "nothing-here") as server:
                status, body = server.request("GET", "/api/exams")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)["exams"], [])


if __name__ == "__main__":
    unittest.main()
