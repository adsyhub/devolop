"""Regressions for the notebook write paths behind the new "add" forms.

The player already listed vocab and notes; what it lacked was any way to create
them outside the post-answer feedback panel. The dialogs now have their own add
forms, and they lean on three parts of the local API that nothing exercised
before: a vocab `reading`, a vocab entry that belongs to no sentence at all, and
a note written for a sentence other than the one on screen.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import quote

from support import RunningServer, write_course


class LearningNotebookApiTests(unittest.TestCase):
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

    def test_vocab_add_keeps_the_reading(self) -> None:
        """The notebook form has a reading field; the entry must come back with it."""
        with self.server() as server:
            status, body = server.request("POST", "/api/vocab", body={
                "term": "面接",
                "reading": "めんせつ",
                "meaning": "面试",
                "note": "N2 常考",
                "courseId": "c_test",
                "sentenceId": "s_0000",
                "sourceText": "これはテストです。",
            })
            self.assertEqual(status, 201, body)
            item = self.payload(body)["item"]
            self.assertEqual(item["reading"], "めんせつ")

            status, body = server.request("GET", "/api/vocab")
            self.assertEqual(status, 200, body)
            items = self.payload(body)["items"]
            self.assertEqual([entry["reading"] for entry in items], ["めんせつ"])

    def test_vocab_add_without_a_sentence_is_accepted(self) -> None:
        """A word typed straight into the notebook belongs to no sentence."""
        with self.server() as server:
            status, body = server.request("POST", "/api/vocab", body={
                "term": "留学",
                "reading": "",
                "meaning": "留学",
                "note": "",
                "courseId": "",
                "sentenceId": "",
                "sourceText": "",
            })
            self.assertEqual(status, 201, body)
            item = self.payload(body)["item"]
            self.assertEqual(item["term"], "留学")
            self.assertEqual(item["sentenceId"], "")
            self.assertEqual(item["courseId"], "")

    def test_vocab_add_still_rejects_an_empty_term(self) -> None:
        with self.server() as server:
            status, body = server.request("POST", "/api/vocab", body={"term": "   ", "meaning": "x"})
            self.assertEqual(status, 400, body)
            self.assertIn("term", self.payload(body)["error"])

    def test_note_can_be_written_for_any_sentence(self) -> None:
        """The dialog form picks a sentence by number, not whichever one is on screen."""
        with self.server() as server:
            status, body = server.request(
                "PUT", "/api/notes/c_test/s_0001", body={"text": "长音要听清", "starred": True}
            )
            self.assertEqual(status, 200, body)
            item = self.payload(body)["item"]
            self.assertEqual(item["sentenceId"], "s_0001")
            self.assertTrue(item["starred"])

            status, body = server.request("GET", "/api/notes")
            self.assertEqual(status, 200, body)
            items = self.payload(body)["items"]
            self.assertEqual([entry["sentenceId"] for entry in items], ["s_0001"])

    def test_saving_over_an_existing_note_replaces_it(self) -> None:
        """The form warns before it does this, so the overwrite had better be clean."""
        with self.server() as server:
            status, body = server.request(
                "PUT", "/api/notes/c_test/s_0001", body={"text": "第一版", "starred": True}
            )
            self.assertEqual(status, 200, body)
            first = self.payload(body)["item"]

            status, body = server.request(
                "PUT", "/api/notes/c_test/s_0001", body={"text": "第二版", "starred": False}
            )
            self.assertEqual(status, 200, body)
            second = self.payload(body)["item"]

            self.assertEqual(second["id"], first["id"])
            self.assertEqual(second["createdAt"], first["createdAt"])
            self.assertEqual(second["text"], "第二版")
            self.assertFalse(second["starred"])

            status, body = server.request("GET", "/api/notes")
            self.assertEqual(len(self.payload(body)["items"]), 1, body)

    def test_progress_upsert_and_retrieve(self) -> None:
        """Progress updates must persist in SQLite and be queryable per course."""
        with self.server() as server:
            status, body = server.request(
                "POST", "/api/progress", body={
                    "courseId": "c_test",
                    "sentenceId": "s_0001",
                    "completed": True,
                    "mastered": True,
                    "attempts": 2,
                    "lastScore": 95.5,
                }
            )
            self.assertEqual(status, 200, body)
            item = self.payload(body)["item"]
            self.assertTrue(item["completed"])
            self.assertTrue(item["mastered"])

            status, body = server.request("GET", "/api/progress?courseId=c_test")
            self.assertEqual(status, 200, body)
            progress = self.payload(body)["progress"]
            self.assertIn("s_0001", progress)
            self.assertEqual(progress["s_0001"]["attempts"], 2)
            self.assertEqual(progress["s_0001"]["lastScore"], 95.5)

    def test_progress_batch_accepts_browser_fields_without_zeroing_mastery(self) -> None:
        """Browser {correct,bestScore} history must map safely to SQLite fields."""
        with self.server() as server:
            status, body = server.request("POST", "/api/progress", body={
                "courseId": "c_test",
                "progress": {
                    "s_0001": {
                        "completed": True,
                        "correct": True,
                        "attempts": 3,
                        "bestScore": 96,
                        "reviewStage": 2,
                        "reviewInterval": 3,
                        "nextReviewAt": "2026-09-04T00:00:00.000Z",
                        "updatedAt": "2026-09-01T00:00:00.000Z",
                    }
                },
            })
            self.assertEqual(status, 200, body)
            item = self.payload(body)["progress"]["s_0001"]
            self.assertTrue(item["mastered"])
            self.assertEqual(item["bestScore"], 96)
            self.assertEqual(item["lastScore"], 96)
            self.assertEqual(item["reviewStage"], 2)

    def test_progress_batch_normalizes_utc_timestamps_before_conflict_resolution(self) -> None:
        """Equivalent Z/+00:00 timestamps must compare chronologically, not lexically."""
        with self.server() as server:
            def sync(mastered: bool, updated_at: str) -> dict[str, Any]:
                status, body = server.request("POST", "/api/progress", body={
                    "courseId": "c_test",
                    "progress": {
                        "s_0001": {
                            "completed": True,
                            "mastered": mastered,
                            "attempts": 1,
                            "updatedAt": updated_at,
                        }
                    },
                })
                self.assertEqual(status, 200, body)
                return self.payload(body)["progress"]["s_0001"]

            self.assertTrue(sync(True, "2026-09-01T00:00:01.000Z")["mastered"])
            older = sync(False, "2026-09-01T00:00:00.999Z")
            self.assertTrue(older["mastered"])
            self.assertEqual(older["updatedAt"], "2026-09-01T00:00:01+00:00")
            self.assertFalse(sync(False, "2026-09-01T00:00:02.000Z")["mastered"])

    def test_listen_exposure_does_not_create_an_attempt_or_mastery(self) -> None:
        with self.server() as server:
            status, body = server.request("POST", "/api/progress/exposure", body={
                "courseId": "c_test", "sentenceId": "s_0001",
            })
            self.assertEqual(status, 200, body)
            item = self.payload(body)["item"]
            self.assertFalse(item["mastered"])
            self.assertEqual(item["attempts"], 0)
            self.assertEqual(item["exposures"], 1)

            status, body = server.request("POST", "/api/progress/exposure", body={
                "courseId": "c_test", "sentenceId": "s_0001",
            })
            self.assertEqual(status, 200, body)
            self.assertEqual(self.payload(body)["item"]["exposures"], 2)

    def test_study_log_and_stats(self) -> None:
        """Study attempts record logs and update the stats counters."""
        with self.server() as server:
            status, body = server.request(
                "POST", "/api/study-log", body={
                    "courseId": "c_test",
                    "sentenceId": "s_0001",
                    "userInput": "これはテストです",
                    "isCorrect": True,
                    "score": 100.0,
                }
            )
            self.assertEqual(status, 201, body)
            log = self.payload(body)["log"]
            self.assertTrue(log["isCorrect"])

            status, body = server.request("GET", "/api/stats?courseId=c_test")
            self.assertEqual(status, 200, body)
            stats = self.payload(body)["stats"]
            self.assertIn("dbPath", stats)

    def test_courses_api_returns_course_list(self) -> None:
        """The /api/courses endpoint lists installed courses."""
        with self.server() as server:
            status, body = server.request("GET", "/api/courses")
            self.assertEqual(status, 200, body)
            courses = self.payload(body)["courses"]
            self.assertIsInstance(courses, list)

    def test_vocab_srs_review_grading(self) -> None:
        """SRS review updates repetitions, interval, and next review date."""
        with self.server() as server:
            # Create vocab
            status, body = server.request("POST", "/api/vocab", body={
                "term": "克服",
                "reading": "こくふく",
                "meaning": "克服",
                "tags": ["N2", "动词"],
                "level": "N2",
            })
            self.assertEqual(status, 201, body)
            item = self.payload(body)["item"]
            v_id = item["id"]
            self.assertEqual(item["tags"], ["N2", "动词"])
            self.assertEqual(item["level"], "N2")

            # Grade review: good (first time -> interval 1)
            status, body = server.request("POST", "/api/vocab/review", body={
                "id": v_id,
                "grade": "good",
            })
            self.assertEqual(status, 200, body)
            res = self.payload(body)["item"]
            self.assertEqual(res["srsRepetitions"], 1)
            self.assertEqual(res["srsInterval"], 1)
            self.assertTrue(bool(res["nextReviewAt"]))

            # Grade review: good (second time -> interval 3)
            status, body = server.request("POST", "/api/vocab/review", body={
                "id": v_id,
                "grade": "good",
            })
            self.assertEqual(status, 200, body)
            res2 = self.payload(body)["item"]
            self.assertEqual(res2["srsRepetitions"], 2)
            self.assertEqual(res2["srsInterval"], 3)

            # Grade review: again (forgot -> reset to 0, interval 1, lapses 1)
            status, body = server.request("POST", "/api/vocab/review", body={
                "id": v_id,
                "grade": "again",
            })
            self.assertEqual(status, 200, body)
            res3 = self.payload(body)["item"]
            self.assertEqual(res3["srsRepetitions"], 0)
            self.assertEqual(res3["srsInterval"], 1)
            self.assertEqual(res3["srsLapses"], 1)

    def test_offline_client_ids_and_replayed_mutations_are_idempotent(self) -> None:
        """A lost response must not duplicate words, logs, or SRS grades."""
        with self.server() as server:
            vocab_payload = {
                "id": "local_vocab_offline_1",
                "term": "再送",
                "meaning": "replay",
            }
            for _ in range(2):
                status, body = server.request("POST", "/api/vocab", body=vocab_payload)
                self.assertEqual(status, 201, body)
                self.assertEqual(self.payload(body)["item"]["id"], vocab_payload["id"])

            status, body = server.request("GET", "/api/vocab")
            self.assertEqual(status, 200, body)
            self.assertEqual(len(self.payload(body)["items"]), 1)

            log_payload = {
                "id": "local_log_offline_1",
                "courseId": "c_test",
                "sentenceId": "s_0001",
                "isCorrect": True,
                "score": 100,
                "durationMs": 1234,
            }
            for _ in range(2):
                status, body = server.request("POST", "/api/study-log", body=log_payload)
                self.assertEqual(status, 201, body)

            status, body = server.request("GET", "/api/study-logs?courseId=c_test")
            self.assertEqual(status, 200, body)
            self.assertEqual(self.payload(body)["total"], 1)

            operation_headers = {"X-Learning-Operation-Id": "op_review_replay_1"}
            review_payload = {"id": vocab_payload["id"], "grade": "good"}
            for _ in range(2):
                status, body = server.request(
                    "POST", "/api/vocab/review", body=review_payload, headers=operation_headers
                )
                self.assertEqual(status, 200, body)
                reviewed = self.payload(body)["item"]
                self.assertEqual(reviewed["srsRepetitions"], 1)
                self.assertEqual(reviewed["srsInterval"], 1)

    def test_vocab_batch_operations(self) -> None:
        """Batch operations allow tagging, mastering, and deleting in bulk."""
        with self.server() as server:
            # Create two items
            _, b1 = server.request("POST", "/api/vocab", body={"term": "単語1", "meaning": "m1"})
            _, b2 = server.request("POST", "/api/vocab", body={"term": "単語2", "meaning": "m2"})
            id1 = self.payload(b1)["item"]["id"]
            id2 = self.payload(b2)["item"]["id"]

            # Batch add tag
            status, body = server.request("POST", "/api/vocab/batch", body={
                "action": "add_tag",
                "ids": [id1, id2],
                "tag": "重要",
            })
            self.assertEqual(status, 200, body)
            items = self.payload(body)["items"]
            self.assertTrue(all("重要" in item["tags"] for item in items))

            # Batch mark mastered
            status, body = server.request("POST", "/api/vocab/batch", body={
                "action": "mark_mastered",
                "ids": [id1, id2],
            })
            self.assertEqual(status, 200, body)
            items = self.payload(body)["items"]
            self.assertTrue(all(item["mastered"] for item in items))

            # Filter by tag
            status, body = server.request("GET", f"/api/vocab?tag={quote('重要')}")
            self.assertEqual(status, 200, body)
            self.assertEqual(len(self.payload(body)["items"]), 2)

            # Batch delete
            status, body = server.request("POST", "/api/vocab/batch", body={
                "action": "delete",
                "ids": [id1, id2],
            })
            self.assertEqual(status, 200, body)
            self.assertEqual(self.payload(body)["updated"], 2)

            status, body = server.request("GET", "/api/vocab")
            self.assertEqual(len(self.payload(body)["items"]), 0)

    def test_vocab_batch_import_uses_client_ids_and_skips_duplicates(self) -> None:
        with self.server() as server:
            status, body = server.request("POST", "/api/vocab/import", body={
                "items": [
                    {"id": "local_import_1", "term": "言葉", "reading": "ことば", "meaning": "词语"},
                    {"id": "local_import_2", "term": "言葉", "reading": "ことば", "meaning": "duplicate"},
                    {"id": "local_import_3", "term": "勉強", "reading": "べんきょう", "tags": ["N2"]},
                ]
            })
            self.assertEqual(status, 200, body)
            data = self.payload(body)
            self.assertEqual(data["created"], 2)
            self.assertEqual(data["skipped"], 1)
            self.assertEqual({item["id"] for item in data["items"]}, {"local_import_1", "local_import_3"})

    def test_dictation_mistakes_and_due_reviews(self) -> None:
        """Dictation mistakes endpoint aggregates sentences needing practice."""
        with self.server() as server:
            # Record a failed attempt
            server.request("POST", "/api/progress", body={
                "courseId": "c_test",
                "sentenceId": "s_0001",
                "completed": True,
                "mastered": False,
                "attempts": 3,
                "lastScore": 60.0,
            })
            server.request("POST", "/api/study-log", body={
                "courseId": "c_test",
                "sentenceId": "s_0001",
                "userInput": "間違えた答え",
                "isCorrect": False,
                "score": 60.0,
            })

            # Check mistakes endpoint
            status, body = server.request("GET", "/api/mistakes")
            self.assertEqual(status, 200, body)
            mistakes = self.payload(body)["items"]
            self.assertEqual(len(mistakes), 1)
            self.assertEqual(mistakes[0]["sentenceId"], "s_0001")
            self.assertEqual(mistakes[0]["lastUserInput"], "間違えた答え")
            self.assertEqual(mistakes[0]["attempts"], 3)

            # Check due review endpoint
            status, body = server.request("GET", "/api/review/due")
            self.assertEqual(status, 200, body)
            data = self.payload(body)
            self.assertIn("dueVocab", data)
            self.assertIn("dueMistakes", data)
            self.assertEqual(len(data["dueMistakes"]), 1)

    def test_global_notes_and_tag_filter(self) -> None:
        """Notes can be queried globally across courses with tags and stars."""
        with self.server() as server:
            server.request("PUT", "/api/notes/c_1/s_1", body={
                "text": "语法点A",
                "tag": "语法",
                "sourceText": "例文1",
                "starred": True,
            })
            server.request("PUT", "/api/notes/c_2/s_2", body={
                "text": "连音注意",
                "tag": "听力",
                "sourceText": "例文2",
                "starred": False,
            })

            # Query all courses
            status, body = server.request("GET", "/api/notes?allCourses=true")
            self.assertEqual(status, 200, body)
            items = self.payload(body)["items"]
            self.assertEqual(len(items), 2)

            # Filter by tag
            status, body = server.request("GET", f"/api/notes?allCourses=true&tag={quote('语法')}")
            self.assertEqual(status, 200, body)
            items = self.payload(body)["items"]
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["tag"], "语法")
            self.assertEqual(items[0]["sourceText"], "例文1")


if __name__ == "__main__":
    unittest.main()
