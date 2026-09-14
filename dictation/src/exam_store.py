"""Exam bank storage and its local HTTP API.

Two halves, matching the split the player already uses:

``ExamStore``     reads ``exams/<slug>/exam.json`` off disk and audits it, the way
                  ``CourseStore`` reads ``courses/<id>/manifest.json``.
``ExamProgress``  per-question history in the same SQLite file the notebook uses,
                  so a learner's exam record lives beside their vocabulary and notes
                  instead of in a second store with its own backup story.
``ExamApiMixin``  the ``/api/exams*`` routes, mixed into the request handler next to
                  ``LearningApiMixin``.

Why a wrong-answer book rather than only attempts
-------------------------------------------------
Scores are the thing a learner asks for and the least useful thing to keep. What
makes a past paper worth re-opening is the set of questions they got wrong, which
questions they got right *by guessing*, and when those are due again. So every
answer is written twice: once as an immutable row in the attempt (what happened in
that sitting) and once folded into a per-question record (streak, last outcome,
next review date). ``/api/exams/<id>/review`` reads the second one.

Guessing is recorded because a lucky 25% is not knowledge. The client sends
``confidence`` with each answer in practice mode; a correct-but-guessed answer
advances nothing and stays in the review queue.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import date, datetime, timedelta
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import SplitResult, parse_qs, unquote

from exam_schema import (
    EXAM_SLUG_PATTERN,
    audit_exam,
    iter_questions,
    question_index,
    score_answers,
)

MAX_ANSWERS_PER_REQUEST = 500

EXAM_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS exam_attempts (
    id           TEXT PRIMARY KEY,
    exam_id      TEXT NOT NULL,
    exam_slug    TEXT NOT NULL,
    mode         TEXT NOT NULL,
    scope        TEXT NOT NULL DEFAULT '',
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    elapsed_ms   INTEGER NOT NULL DEFAULT 0,
    score_json   TEXT,
    -- The questions this sitting actually put in front of the learner. Empty means
    -- the whole paper. Without it, a perfect round of 問題1 scores 6 out of the
    -- paper's 176 points and the history list reports 3%.
    question_ids TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_exam_attempts_exam ON exam_attempts(exam_id, started_at DESC);

CREATE TABLE IF NOT EXISTS exam_answers (
    attempt_id  TEXT NOT NULL,
    question_id TEXT NOT NULL,
    chosen      INTEGER,
    correct     INTEGER NOT NULL DEFAULT 0,
    confidence  TEXT NOT NULL DEFAULT '',
    elapsed_ms  INTEGER NOT NULL DEFAULT 0,
    answered_at TEXT NOT NULL,
    PRIMARY KEY (attempt_id, question_id),
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exam_question_state (
    exam_id     TEXT NOT NULL,
    question_id TEXT NOT NULL,
    seen        INTEGER NOT NULL DEFAULT 0,
    wrong       INTEGER NOT NULL DEFAULT 0,
    guessed     INTEGER NOT NULL DEFAULT 0,
    streak      INTEGER NOT NULL DEFAULT 0,
    last_chosen INTEGER,
    last_result TEXT NOT NULL DEFAULT '',
    last_at     TEXT NOT NULL DEFAULT '',
    due_on      TEXT NOT NULL DEFAULT '',
    marked      INTEGER NOT NULL DEFAULT 0,
    note        TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (exam_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_exam_state_due ON exam_question_state(exam_id, due_on);
"""

#: Days until a question is due again, indexed by correct-and-confident streak.
#: Short and few: a past paper has 105 questions, not 10,000 flashcards, and a
#: learner sitting one is usually weeks from an exam date, not years.
REVIEW_INTERVALS = (1, 3, 7, 16, 35)

VALID_MODES = frozenset({"practice", "exam", "review"})
VALID_CONFIDENCE = frozenset({"", "sure", "unsure", "guess"})


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


class ExamStore:
    """Lists and loads exams from an ``exams/`` directory.

    Layout mirrors ``courses/``::

        exams/
          2022-07-N1/
            exam.json          <- the only file the player needs
            answer-key.txt     <- the key as printed, kept for re-checking
            exam-meta.json     <- importer input
            pages/p02.json …   <- transcription source of truth
    """

    def __init__(self, exams_root: Path) -> None:
        self.root = Path(exams_root)

    def list_exams(self) -> list[dict[str, Any]]:
        if not self.root.is_dir():
            return []
        summaries: list[dict[str, Any]] = []
        for directory in sorted(self.root.iterdir()):
            if not directory.is_dir() or not EXAM_SLUG_PATTERN.fullmatch(directory.name):
                continue
            try:
                from studio_artifacts import resolve_exam_manifest_path

                path = resolve_exam_manifest_path(directory)
            except Exception:
                path = directory / "exam.json"
            if not path or not path.is_file():
                continue
            try:
                exam = self._load_json(path)
            except Exception as exc:  # noqa: BLE001 - one broken exam must not hide the rest
                summaries.append(
                    {
                        "slug": directory.name,
                        "title": directory.name,
                        "broken": True,
                        "error": str(exc),
                    }
                )
                continue
            report = audit_exam(exam)
            summaries.append(
                {
                    "slug": directory.name,
                    "examId": exam.get("examId"),
                    "level": exam.get("level"),
                    "title": exam.get("title"),
                    "sessionLabel": exam.get("sessionLabel"),
                    "questionCount": exam.get("questionCount"),
                    "totalPoints": exam.get("totalPoints"),
                    "durationSec": exam.get("durationSec"),
                    "contentRevision": exam.get("contentRevision"),
                    "sections": [
                        {
                            "id": section.get("id"),
                            "title": section.get("title"),
                            "localTitle": section.get("localTitle"),
                            "kind": section.get("kind"),
                            "questionCount": section.get("questionCount"),
                            "audioRequired": section.get("audioRequired"),
                        }
                        for section in exam.get("sections") or []
                    ],
                    "quality": {"status": report["status"], **report["summary"]},
                    "broken": bool(report["summary"]["errors"]),
                }
            )
        return summaries

    def get_exam(self, slug: str) -> dict[str, Any] | None:
        path = self.exam_path(slug)
        if path is None:
            return None
        exam = self._load_json(path)
        report = audit_exam(exam)
        exam["quality"] = {
            "status": report["status"],
            "blocked": bool(report["summary"]["errors"]),
            **report["summary"],
        }
        exam["slug"] = slug
        return exam

    def exam_path(self, slug: str) -> Path | None:
        """Resolve ``slug`` to its ``exam.json``, refusing anything that escapes the root.

        The slug arrives from a URL. ``EXAM_SLUG_PATTERN`` already excludes ``/``,
        ``\\`` and ``..``, and the resolved path is then checked to be inside the
        root, so a future loosening of the pattern cannot turn into a traversal.
        """
        if not EXAM_SLUG_PATTERN.fullmatch(slug or ""):
            return None
        folder = (self.root / slug).resolve()
        try:
            folder.relative_to(self.root.resolve())
        except ValueError:
            return None
        if not folder.is_dir():
            return None
        try:
            from studio_artifacts import resolve_exam_manifest_path

            candidate = resolve_exam_manifest_path(folder)
            if candidate and candidate.is_file():
                return candidate
        except Exception:
            pass
        candidate = folder / "exam.json"
        return candidate if candidate.is_file() else None

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"{path.name} must contain a JSON object.")
        return data


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------


class ExamProgress:
    """Attempts, answers and the wrong-answer book, in the learning database.

    Takes the ``LearningStore``'s own connection and lock rather than opening a
    second connection to the same file. The server is a ``ThreadingHTTPServer`` and
    the connection is created with ``check_same_thread=False``, so every statement
    has to run under that one re-entrant lock; a second connection would instead
    meet the first one's write transaction and raise "database is locked".
    """

    def __init__(self, connection: sqlite3.Connection, lock: threading.RLock | None = None) -> None:
        self.connection = connection
        self.lock = lock if lock is not None else threading.RLock()
        with self.lock:
            self.connection.executescript(EXAM_SCHEMA_SQL)
            self._migrate()
            self.connection.commit()

    def _migrate(self) -> None:
        """Add columns that arrived after a database was already created.

        ``CREATE TABLE IF NOT EXISTS`` is a no-op once the table exists, so a learner
        who used an earlier build keeps the old shape and every later INSERT fails on
        a missing column. Adding columns idempotently here is the whole migration
        story this feature needs; nothing is ever dropped or rewritten.
        """
        existing = {
            row["name"] for row in self.connection.execute("PRAGMA table_info(exam_attempts)")
        }
        if "abandoned_at" not in existing:
            self.connection.execute("ALTER TABLE exam_attempts ADD COLUMN abandoned_at TEXT")
        if "scope" not in existing:
            self.connection.execute("ALTER TABLE exam_attempts ADD COLUMN scope TEXT NOT NULL DEFAULT ''")
        if "question_ids" not in existing:
            self.connection.execute(
                "ALTER TABLE exam_attempts ADD COLUMN question_ids TEXT NOT NULL DEFAULT ''"
            )

    @classmethod
    def from_learning_store(cls, store: Any) -> "ExamProgress":
        """Share the notebook's connection so exam history lands in the same file."""
        return cls(store._connection, store.lock)

    # ---- attempts ----

    def start_attempt(self, exam: dict[str, Any], slug: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            mode = str(payload.get("mode") or "practice").strip()
            if mode not in VALID_MODES:
                raise ValueError(f"mode must be one of {', '.join(sorted(VALID_MODES))}.")
            scope = str(payload.get("scope") or "").strip()[:200]

            # The client sends the queue it built. Unknown ids are dropped rather than
            # rejected: a stale page holding an older revision of the paper should still
            # be able to record a sitting for the questions that do still exist.
            known = set(question_index(exam))
            requested = payload.get("questionIds")
            scoped = (
                [str(item) for item in requested if str(item) in known]
                if isinstance(requested, list)
                else []
            )
            if isinstance(requested, list) and not scoped:
                raise ValueError("questionIds contained no question belonging to this exam.")

            attempt_id = uuid.uuid4().hex
            started = now_iso()
            self.connection.execute(
                "INSERT INTO exam_attempts (id, exam_id, exam_slug, mode, scope, started_at, question_ids) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt_id,
                    str(exam.get("examId")),
                    slug,
                    mode,
                    scope,
                    started,
                    json.dumps(scoped) if scoped else "",
                ),
            )
            self.connection.commit()
            return {
                "id": attempt_id,
                "examId": exam.get("examId"),
                "mode": mode,
                "scope": scope,
                "startedAt": started,
                "questionCount": len(scoped) or len([q for q in known if not question_index(exam)[q].get("example")]),
            }

    def record_answers(
        self,
        exam: dict[str, Any],
        attempt_id: str,
        answers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Write a batch of answers and fold each into the question's review record."""
        with self.lock:
            if len(answers) > MAX_ANSWERS_PER_REQUEST:
                raise ValueError(f"At most {MAX_ANSWERS_PER_REQUEST} answers per request.")
            row = self.connection.execute(
                "SELECT exam_id, mode, abandoned_at, finished_at FROM exam_attempts WHERE id = ?", (attempt_id,)
            ).fetchone()
            if row is None:
                raise KeyError(attempt_id)
            if row["abandoned_at"] or row["finished_at"]:
                raise ValueError("This attempt is already closed.")
            exam_id = str(exam.get("examId"))
            if str(row["exam_id"]) != exam_id:
                raise ValueError("This attempt belongs to a different exam.")

            index = question_index(exam)
            stamp = now_iso()
            written = 0
            mode = row["mode"]
            for entry in answers:
                if not isinstance(entry, dict):
                    raise ValueError("Each answer must be an object.")
                question_id = str(entry.get("questionId") or "")
                question = index.get(question_id)
                if question is None:
                    raise ValueError(f"Unknown questionId: {question_id!r}")
                if question.get("example"):
                    continue  # the paper's worked example is not answered

                chosen = _choice(entry.get("chosen"), int(question.get("choiceCount") or 4))
                confidence = str(entry.get("confidence") or "").strip()
                if confidence not in VALID_CONFIDENCE:
                    raise ValueError(f"confidence must be one of {', '.join(sorted(VALID_CONFIDENCE - {''}))}.")
                elapsed = _non_negative_int(entry.get("elapsedMs"))
                answer = question.get("answer")
                correct = 1 if (chosen is not None and answer is not None and chosen == answer) else 0

                prev = self.connection.execute(
                    "SELECT chosen FROM exam_answers WHERE attempt_id = ? AND question_id = ?",
                    (attempt_id, question_id),
                ).fetchone()

                self.connection.execute(
                    "INSERT INTO exam_answers (attempt_id, question_id, chosen, correct, confidence, "
                    "elapsed_ms, answered_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(attempt_id, question_id) DO UPDATE SET "
                    "chosen=excluded.chosen, correct=excluded.correct, confidence=excluded.confidence, "
                    "elapsed_ms=excluded.elapsed_ms, answered_at=excluded.answered_at",
                    (attempt_id, question_id, chosen, correct, confidence, elapsed, stamp),
                )
                # In exam mode, review state is never updated until finish_attempt.
                # In practice mode, fold only if this question has not yet been answered in this attempt.
                if mode != "exam" and prev is None:
                    self._fold_into_review(exam_id, question_id, chosen, bool(correct), confidence, stamp)
                written += 1

            self.connection.commit()
            return {"attemptId": attempt_id, "recorded": written}

    def finish_attempt(self, exam: dict[str, Any], attempt_id: str, elapsed_ms: Any = None) -> dict[str, Any]:
        with self.lock:
            row = self.connection.execute(
                "SELECT * FROM exam_attempts WHERE id = ?", (attempt_id,)
            ).fetchone()
            if row is None:
                raise KeyError(attempt_id)

            if row["abandoned_at"]:
                raise ValueError("This attempt was abandoned.")
            if str(row["exam_id"]) != str(exam.get("examId")):
                raise ValueError("This attempt belongs to a different exam.")

            # Idempotent finish: return existing score and timestamp if already finished
            if row["finished_at"] and row["score_json"]:
                return {
                    "attemptId": attempt_id,
                    "finishedAt": row["finished_at"],
                        "abandonedAt": row["abandoned_at"],
                    "score": json.loads(row["score_json"]),
                }

            answered = {
                str(entry["question_id"]): entry["chosen"]
                for entry in self.connection.execute(
                    "SELECT question_id, chosen FROM exam_answers WHERE attempt_id = ?", (attempt_id,)
                )
            }
            scoped = _scope_ids(row)
            score = score_answers(exam, answered, only=scoped)
            finished = now_iso()
            self.connection.execute(
                "UPDATE exam_attempts SET finished_at = ?, elapsed_ms = ?, score_json = ? WHERE id = ?",
                (finished, _non_negative_int(elapsed_ms), json.dumps(score, ensure_ascii=False), attempt_id),
            )

            # In exam mode, fold final answers into review upon finishing
            if row["mode"] == "exam":
                exam_id = str(exam.get("examId"))
                for entry in self.connection.execute(
                    "SELECT question_id, chosen, correct, confidence, answered_at FROM exam_answers WHERE attempt_id = ?",
                    (attempt_id,),
                ):
                    self._fold_into_review(
                        exam_id,
                        str(entry["question_id"]),
                        entry["chosen"],
                        bool(entry["correct"]),
                        str(entry["confidence"] or ""),
                        str(entry["answered_at"] or finished),
                    )

            self.connection.commit()
            return {"attemptId": attempt_id, "finishedAt": finished, "score": score}

    def abandon_attempt(self, attempt_id):
        with self.lock,self.connection:
            row=self.connection.execute('SELECT * FROM exam_attempts WHERE id=?',(attempt_id,)).fetchone()
            if row is None:raise KeyError(attempt_id)
            if row['finished_at']:raise ValueError('A finished attempt cannot be abandoned.')
            stamp=row['abandoned_at'] or now_iso()
            self.connection.execute('UPDATE exam_attempts SET abandoned_at=? WHERE id=?',(stamp,attempt_id))
            return {'attemptId':attempt_id,'abandonedAt':stamp}

    def progress(self, exam_id, question_count):
        with self.lock:
            row=self.connection.execute("SELECT * FROM exam_attempts WHERE exam_id=? AND finished_at IS NULL AND abandoned_at IS NULL ORDER BY started_at DESC,rowid DESC LIMIT 1",(exam_id,)).fetchone()
            if row is None:return {'status':'not-started','activeAttempt':None}
            count=self.connection.execute('SELECT COUNT(*) FROM exam_answers WHERE attempt_id=?',(row['id'],)).fetchone()[0]
            return {'status':'in-progress','activeAttempt':{'id':row['id'],'answeredCount':count,'questionCount':len(json.loads(row['question_ids'])) if row['question_ids'] else question_count}}

    def list_attempts(self, exam_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.connection.execute(
                # rowid breaks the tie: started_at has one-second resolution, and two
                # attempts in the same second would otherwise come back in an order
                # SQLite is free to change, so "the latest attempt" would be a coin flip.
                "SELECT * FROM exam_attempts WHERE exam_id = ? "
                "ORDER BY started_at DESC, rowid DESC LIMIT ?",
                (exam_id, max(1, min(int(limit), 200))),
            ).fetchall()
            attempts = []
            for row in rows:
                score = None
                if row["score_json"]:
                    try:
                        score = json.loads(row["score_json"])
                    except json.JSONDecodeError:
                        score = None
                attempts.append(
                    {
                        "id": row["id"],
                        "mode": row["mode"],
                        "scope": row["scope"],
                        "startedAt": row["started_at"],
                        "finishedAt": row["finished_at"],
                        "abandonedAt": row["abandoned_at"],
                        "elapsedMs": row["elapsed_ms"],
                        "totals": (score or {}).get("totals"),
                        "sections": (score or {}).get("sections"),
                    }
                )
            return attempts

    def get_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        with self.lock:
            row = self.connection.execute("SELECT * FROM exam_attempts WHERE id = ?", (attempt_id,)).fetchone()
            if row is None:
                return None
            answers = [
                {
                    "questionId": entry["question_id"],
                    "chosen": entry["chosen"],
                    "correct": bool(entry["correct"]),
                    "confidence": entry["confidence"],
                    "elapsedMs": entry["elapsed_ms"],
                    "answeredAt": entry["answered_at"],
                }
                for entry in self.connection.execute(
                    "SELECT * FROM exam_answers WHERE attempt_id = ? ORDER BY answered_at", (attempt_id,)
                )
            ]
            score = json.loads(row["score_json"]) if row["score_json"] else None
            return {
                "id": row["id"],
                "examId": row["exam_id"],
                "examSlug": row["exam_slug"],
                "mode": row["mode"],
                "scope": row["scope"],
                "startedAt": row["started_at"],
                "finishedAt": row["finished_at"],
                        "abandonedAt": row["abandoned_at"],
                "elapsedMs": row["elapsed_ms"],
                "score": score,
                "answers": answers,
                "questionIds": json.loads(row["question_ids"]) if row["question_ids"] else [],
            }

        # ---- review book ----

    def _fold_into_review(
        self,
        exam_id: str,
        question_id: str,
        chosen: int | None,
        correct: bool,
        confidence: str,
        stamp: str,
    ) -> None:
        row = self.connection.execute(
            "SELECT * FROM exam_question_state WHERE exam_id = ? AND question_id = ?",
            (exam_id, question_id),
        ).fetchone()
        skipped = chosen is None
        seen = (row["seen"] if row else 0) + 1
        wrong = (row["wrong"] if row else 0) + (0 if (correct or skipped) else 1)
        guessed = (row["guessed"] if row else 0) + (1 if confidence == "guess" else 0)
        streak = row["streak"] if row else 0

        # A right answer the learner admits was a guess is not evidence of knowing it.
        # It keeps its place in the queue instead of being pushed weeks away.
        #
        # "Ran out of time" and "picked the wrong option" are also different facts.
        # Both come back tomorrow, but only the second means there is a wrong idea to
        # unlearn, so only the second counts toward `wrong` and toward the wrong-answer
        # book the learner opens to see what they actually misunderstand.
        if correct and confidence != "guess":
            streak += 1
            result = "correct"
        elif correct:
            result = "guessed"
        elif skipped:
            streak = 0
            result = "skipped"
        else:
            streak = 0
            result = "wrong"

        interval = REVIEW_INTERVALS[min(streak, len(REVIEW_INTERVALS) - 1)] if streak else 1
        due = (date.today() + timedelta(days=interval)).isoformat()

        self.connection.execute(
            "INSERT INTO exam_question_state (exam_id, question_id, seen, wrong, guessed, streak, "
            "last_chosen, last_result, last_at, due_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(exam_id, question_id) DO UPDATE SET seen=excluded.seen, wrong=excluded.wrong, "
            "guessed=excluded.guessed, streak=excluded.streak, last_chosen=excluded.last_chosen, "
            "last_result=excluded.last_result, last_at=excluded.last_at, due_on=excluded.due_on",
            (exam_id, question_id, seen, wrong, guessed, streak, chosen, result, stamp, due),
        )

    def get_review(self, exam_id: str) -> dict[str, Any]:
        with self.lock:
            rows = self.connection.execute(
                "SELECT * FROM exam_question_state WHERE exam_id = ?", (exam_id,)
            ).fetchall()
            today = today_iso()
            states = {}
            for row in rows:
                states[str(row["question_id"])] = {
                    "seen": row["seen"],
                    "wrong": row["wrong"],
                    "guessed": row["guessed"],
                    "streak": row["streak"],
                    "lastChosen": row["last_chosen"],
                    "lastResult": row["last_result"],
                    "lastAt": row["last_at"],
                    "dueOn": row["due_on"],
                    "due": bool(row["due_on"] and row["due_on"] <= today),
                    "marked": bool(row["marked"]),
                    "note": row["note"],
                }
            return {"today": today, "questions": states}

    def set_mark(self, exam_id: str, question_id: str, marked: bool, note: str | None = None) -> dict[str, Any]:
        with self.lock:
            existing = self.connection.execute(
                "SELECT note FROM exam_question_state WHERE exam_id = ? AND question_id = ?",
                (exam_id, question_id),
            ).fetchone()
            text = (str(note) if note is not None else (existing["note"] if existing else ""))[:2000]
            self.connection.execute(
                "INSERT INTO exam_question_state (exam_id, question_id, marked, note) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(exam_id, question_id) DO UPDATE SET marked=excluded.marked, note=excluded.note",
                (exam_id, question_id, 1 if marked else 0, text),
            )
            self.connection.commit()
            return {"questionId": question_id, "marked": bool(marked), "note": text}

    def reset_exam(self, exam_id: str) -> dict[str, Any]:
        """Forget every attempt and review record for one exam."""
        with self.lock:
            attempts = [
                row["id"]
                for row in self.connection.execute("SELECT id FROM exam_attempts WHERE exam_id = ?", (exam_id,))
            ]
            self.connection.executemany(
                "DELETE FROM exam_answers WHERE attempt_id = ?", [(attempt,) for attempt in attempts]
            )
            self.connection.execute("DELETE FROM exam_attempts WHERE exam_id = ?", (exam_id,))
            self.connection.execute("DELETE FROM exam_question_state WHERE exam_id = ?", (exam_id,))
            self.connection.commit()
            return {"examId": exam_id, "attemptsRemoved": len(attempts)}

    def get_stats(self, exam: dict[str, Any]) -> dict[str, Any]:
        exam_id = str(exam.get("examId"))
        review = self.get_review(exam_id)["questions"]
        attempts = self.list_attempts(exam_id, limit=200)
        finished = [attempt for attempt in attempts if attempt["finishedAt"]]

        by_part: dict[str, dict[str, Any]] = {}
        for section, part, question in iter_questions(exam):
            if question.get("example"):
                continue
            row = by_part.setdefault(
                str(part.get("id")),
                {
                    "partId": part.get("id"),
                    "sectionId": section.get("id"),
                    "number": part.get("number"),
                    "kind": part.get("kind"),
                    "localTitle": part.get("localTitle"),
                    "questions": 0,
                    "seen": 0,
                    "wrong": 0,
                    "due": 0,
                    "marked": 0,
                },
            )
            row["questions"] += 1
            state = review.get(str(question.get("id")))
            if state:
                row["seen"] += 1 if state["seen"] else 0
                row["wrong"] += 1 if state["lastResult"] == "wrong" else 0
                row["due"] += 1 if state["due"] else 0
                row["marked"] += 1 if state["marked"] else 0

        return {
            "examId": exam_id,
            "attempts": len(attempts),
            "finishedAttempts": len(finished),
            "bestPercent": max(
                [float((attempt["totals"] or {}).get("percent") or 0) for attempt in finished], default=0.0
            ),
            "latest": finished[0] if finished else None,
            "wrongCount": sum(1 for state in review.values() if state["lastResult"] == "wrong"),
            "skippedCount": sum(1 for state in review.values() if state["lastResult"] == "skipped"),
            "guessedCount": sum(1 for state in review.values() if state["lastResult"] == "guessed"),
            "dueCount": sum(1 for state in review.values() if state["due"]),
            "markedCount": sum(1 for state in review.values() if state["marked"]),
            "parts": sorted(by_part.values(), key=lambda row: (str(row["sectionId"]), int(row["number"] or 0))),
        }


def _scope_ids(row: Any) -> set[str] | None:
    """The question ids an attempt was scoped to, or None for the whole paper."""
    try:
        raw = row["question_ids"]
    except (IndexError, KeyError):
        return None
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return {str(item) for item in parsed} if isinstance(parsed, list) and parsed else None


def _choice(value: Any, choice_count: int) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        chosen = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"chosen must be an integer or null, got {value!r}") from None
    if not 1 <= chosen <= choice_count:
        raise ValueError(f"chosen must be between 1 and {choice_count}, got {chosen}.")
    return chosen


def _non_negative_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(number, 86_400_000))  # a day, so a stuck timer cannot store nonsense


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


class ExamApiMixin:
    """``/api/exams*`` routing.

    Mixed into the same handler as ``LearningApiMixin`` and behind the same
    ``SecurityContext`` gate, so an exam record is protected exactly like the
    vocabulary notebook: loopback Host, session token on every call including reads,
    and Origin plus Fetch Metadata on writes.
    """

    exam_store: ExamStore
    exam_progress: ExamProgress

    # -- helpers --

    def _exam_or_404(self, slug: str) -> dict[str, Any] | None:
        try:
            exam = self.exam_store.get_exam(slug)
        except Exception as exc:  # noqa: BLE001
            self.send_learning_json({"error": f"exam could not be read: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return None
        if exam is None:
            self.send_learning_json({"error": "exam not found"}, HTTPStatus.NOT_FOUND)
            return None
        return exam

    @staticmethod
    def _slug_from(path: str, prefix: str, suffix: str = "") -> str | None:
        if not path.startswith(prefix):
            return None
        rest = path[len(prefix) :]
        if suffix:
            if not rest.endswith(suffix):
                return None
            rest = rest[: -len(suffix)]
        return unquote(rest) if rest and "/" not in rest else None

    # -- GET --

    def handle_exam_get(self, parsed: SplitResult) -> bool:
        path = parsed.path

        if path == "/api/exams":
            listing=self.exam_store.list_exams()
            for item in listing:
                item['progress']=self.exam_progress.progress(str(item.get('examId')),item.get('questionCount',0))
            self.send_learning_json({"exams": listing})
            return True

        if path == '/api/exams/review-summary':
            summaries=[]
            for item in self.exam_store.list_exams():
                review=self.exam_progress.get_review(str(item.get('examId')))['questions']
                questions=[{'questionId':key,**value} for key,value in review.items()]
                summaries.append({'examSlug':item['slug'],'examId':item.get('examId'),
                                  'wrongCount':sum(q['lastResult']=='wrong' for q in questions),'questions':questions})
            self.send_learning_json({'exams':summaries});return True

        slug = self._slug_from(path, "/api/exams/")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            if exam["quality"].get("blocked"):
                # Same fail-closed rule the course loader applies: an exam whose audit
                # found errors is not served for study, because a wrong answer key
                # teaches the wrong answer.
                self.send_learning_json(
                    {
                        "error": "This exam failed its quality audit and will not be served.",
                        "quality": exam["quality"],
                    },
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                )
                return True
            self.send_learning_json({"exam": exam})
            return True

        slug = self._slug_from(path, "/api/exams/", "/attempts")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            params = parse_qs(parsed.query)
            limit = int(params.get("limit", ["50"])[0] or 50)
            self.send_learning_json(
                {"attempts": self.exam_progress.list_attempts(str(exam.get("examId")), limit)}
            )
            return True

        slug = self._slug_from(path, "/api/exams/", "/review")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            self.send_learning_json({"review": self.exam_progress.get_review(str(exam.get("examId")))})
            return True

        slug = self._slug_from(path, "/api/exams/", "/stats")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            self.send_learning_json({"stats": self.exam_progress.get_stats(exam)})
            return True

        if path.startswith("/api/exam-attempts/"):
            attempt_id = unquote(path[len("/api/exam-attempts/") :])
            attempt = self.exam_progress.get_attempt(attempt_id) if attempt_id else None
            if attempt is None:
                self.send_learning_json({"error": "attempt not found"}, HTTPStatus.NOT_FOUND)
                return True
            self.send_learning_json({"attempt": attempt})
            return True

        return False

    # -- POST --

    def handle_exam_post(self, parsed: SplitResult) -> bool:
        path = parsed.path

        if path.startswith('/api/exam-attempts/') and path.endswith('/abandon'):
            attempt_id=unquote(path[len('/api/exam-attempts/'):-len('/abandon')])
            try:result=self.exam_progress.abandon_attempt(attempt_id)
            except KeyError:self.send_learning_json({'error':'attempt not found'},HTTPStatus.NOT_FOUND)
            except ValueError as exc:self.send_learning_json({'error':str(exc)},HTTPStatus.BAD_REQUEST)
            else:self.send_learning_json(result)
            return True

        slug = self._slug_from(path, "/api/exams/", "/attempts")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            try:
                attempt = self.exam_progress.start_attempt(exam, slug, self.read_learning_json())
            except ValueError as exc:
                self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return True
            self.send_learning_json({"attempt": attempt}, HTTPStatus.CREATED)
            return True

        slug = self._slug_from(path, "/api/exams/", "/answers")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            try:
                payload = self.read_learning_json()
                attempt_id = str(payload.get("attemptId") or "")
                answers = payload.get("answers")
                if not isinstance(answers, list):
                    raise ValueError("answers must be an array.")
                result = self.exam_progress.record_answers(exam, attempt_id, answers)
            except KeyError:
                self.send_learning_json({"error": "attempt not found"}, HTTPStatus.NOT_FOUND)
                return True
            except ValueError as exc:
                self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return True
            self.send_learning_json({"ok": True, **result})
            return True

        slug = self._slug_from(path, "/api/exams/", "/finish")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            try:
                payload = self.read_learning_json()
                result = self.exam_progress.finish_attempt(
                    exam, str(payload.get("attemptId") or ""), payload.get("elapsedMs")
                )
            except KeyError:
                self.send_learning_json({"error": "attempt not found"}, HTTPStatus.NOT_FOUND)
                return True
            except ValueError as exc:
                self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return True
            self.send_learning_json({"ok": True, **result})
            return True

        slug = self._slug_from(path, "/api/exams/", "/mark")
        if slug is not None:
            exam = self._exam_or_404(slug)
            if exam is None:
                return True
            try:
                payload = self.read_learning_json()
                question_id = str(payload.get("questionId") or "")
                if question_id not in question_index(exam):
                    raise ValueError(f"Unknown questionId: {question_id!r}")
                item = self.exam_progress.set_mark(
                    str(exam.get("examId")),
                    question_id,
                    bool(payload.get("marked")),
                    payload.get("note"),
                )
            except ValueError as exc:
                self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return True
            self.send_learning_json({"ok": True, "item": item})
            return True

        return False

    # -- DELETE --

    def handle_exam_delete(self, parsed: SplitResult) -> bool:
        slug = self._slug_from(parsed.path, "/api/exams/", "/progress")
        if slug is None:
            return False
        exam = self._exam_or_404(slug)
        if exam is None:
            return True
        self.send_learning_json({"ok": True, **self.exam_progress.reset_exam(str(exam.get("examId")))})
        return True


def check_exam_qualification(exam: dict[str, Any]) -> tuple[bool, list[str]]:
    """Qualification service for exam publishing and practice.

    Verifies that an exam passes schema audits, has at least one question,
    and all scored questions have verified correct answers and valid choices.
    """
    reasons: list[str] = []
    if not isinstance(exam, dict):
        return False, ["exam.not_object"]

    report = audit_exam(exam, require_answers=True)
    if report["summary"]["errors"] > 0:
        for issue in report.get("issues", []):
            if issue.get("severity") == "error":
                reasons.append(f"audit.{issue.get('code')}: {issue.get('message')}")

    total_q = sum(
        len(part.get("questions") or [])
        for section in exam.get("sections") or []
        if isinstance(section, dict)
        for part in section.get("parts") or []
        if isinstance(part, dict)
    )
    if total_q == 0:
        reasons.append("exam.questions_missing: Exam has no questions.")

    return len(reasons) == 0, reasons


def check_paper_version_qualification(conn: sqlite3.Connection, paper_version_id: str) -> tuple[bool, list[str]]:
    """Database paper version qualification service.

    Enforces that paper version has sections, parts, and questions with valid
    stems, correct answers, and matching options.
    """
    reasons: list[str] = []
    pv = conn.execute("SELECT * FROM paper_versions WHERE id = ?", (paper_version_id,)).fetchone()
    if not pv:
        return False, ["paper_version.not_found"]

    sections = conn.execute("SELECT id FROM paper_sections WHERE paper_version_id = ?", (paper_version_id,)).fetchall()
    if not sections:
        return False, ["paper_version.sections_missing"]

    section_ids = [s["id"] for s in sections]
    placeholders = ",".join("?" * len(section_ids))
    parts = conn.execute(
        f"SELECT id FROM paper_parts WHERE paper_section_id IN ({placeholders})",
        tuple(section_ids),
    ).fetchall()
    if not parts:
        return False, ["paper_version.parts_missing"]

    part_ids = [p["id"] for p in parts]
    part_placeholders = ",".join("?" * len(part_ids))
    blocks = conn.execute(
        f"SELECT question_group_version_id FROM paper_blocks WHERE paper_part_id IN ({part_placeholders})",
        tuple(part_ids),
    ).fetchall()
    if not blocks:
        return False, ["paper_version.blocks_missing"]

    qgv_ids = [b["question_group_version_id"] for b in blocks]
    qgv_placeholders = ",".join("?" * len(qgv_ids))
    questions = conn.execute(
        f"SELECT * FROM question_versions WHERE question_group_version_id IN ({qgv_placeholders})",
        tuple(qgv_ids),
    ).fetchall()
    if not questions:
        return False, ["paper_version.questions_missing"]

    for q in questions:
        qid = q["id"]
        if not str(q["stem_text"] or "").strip():
            reasons.append(f"question.{qid}.stem_missing")
        raw_ans = q["correct_answer_json"]
        if not raw_ans:
            reasons.append(f"question.{qid}.answer_missing")
            continue
        try:
            ans_data = json.loads(raw_ans)
            if not ans_data:
                reasons.append(f"question.{qid}.answer_empty")
        except Exception:
            reasons.append(f"question.{qid}.answer_invalid_json")

        opts = conn.execute(
            "SELECT option_key, is_correct FROM option_versions WHERE question_version_id = ?",
            (qid,),
        ).fetchall()
        if not opts:
            reasons.append(f"question.{qid}.options_missing")
        else:
            correct_opts = [o for o in opts if o["is_correct"]]
            if not correct_opts:
                reasons.append(f"question.{qid}.correct_option_missing")

    return len(reasons) == 0, reasons

