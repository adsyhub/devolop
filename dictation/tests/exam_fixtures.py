"""Exam fixtures for the question-bank tests.

Separate from ``support.py`` because that module is about courses and audio;
nothing here needs an mp3. The fixture exam is deliberately small enough to assert
on by hand and still contains every shape that has its own code path:

* a plain vocabulary item with four printed choices,
* a shared passage with two questions hanging off it,
* a 並べ替え item carrying an ``answerOrder``,
* a worked 例 that must never be scored,
* a listening item whose three choices are spoken rather than printed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from exam_schema import prepare_exam  # noqa: E402


def make_exam(*, with_answers: bool = True, title: str = "Fixture N1") -> dict[str, Any]:
    exam: dict[str, Any] = {
        "level": "N1",
        "title": title,
        "sessionLabel": "2022年7月",
        "durationSec": 3600,
        "source": {"answerKeyNote": "仅供参考"},
        "sections": [
            {
                "id": "s1",
                "kind": "language-knowledge",
                "title": "言語知識",
                "localTitle": "第一部分",
                "parts": [
                    {
                        "id": "s1-m1",
                        "number": 1,
                        "kind": "kanji-reading",
                        "instruction": "＿＿＿の言葉の読み方を選びなさい。",
                        "pointsPerQuestion": 1,
                        "passages": [],
                        "questions": [
                            {
                                "number": 1,
                                "prompt": "<u>勇敢</u>に戦う。",
                                "choices": ["ゆうかん", "ゆうがん", "ゆうけん", "ゆうげん"],
                                "answer": 1 if with_answers else None,
                            },
                            {
                                "number": 2,
                                "prompt": "<u>忠告</u>する。",
                                "choices": ["しんこく", "じゅうこく", "ちゅうこく", "じんこく"],
                                "answer": 3 if with_answers else None,
                            },
                        ],
                    },
                    {
                        "id": "s1-m6",
                        "number": 6,
                        "kind": "sentence-composition",
                        "instruction": "★に入るものを選びなさい。",
                        "pointsPerQuestion": 2,
                        "passages": [],
                        "questions": [
                            {
                                "number": 3,
                                "prompt": "私は＿＿＿＿、＿＿★＿＿、＿＿＿＿と思う。",
                                "choices": ["ア", "イ", "ウ", "エ"],
                                "answer": 4 if with_answers else None,
                                "answerOrder": [3, 2, 4, 1],
                            }
                        ],
                    },
                ],
            },
            {
                "id": "s2",
                "kind": "reading",
                "title": "読解",
                "localTitle": "第二部分",
                "parts": [
                    {
                        "id": "s2-m9",
                        "number": 9,
                        "kind": "mid-passage",
                        "instruction": "次の文章を読んで答えなさい。",
                        "pointsPerQuestion": 2,
                        "passages": [
                            {
                                "label": "(1)",
                                "text": "これはテスト用の文章である。\n二段落目もある。",
                                "notes": ["（注）テスト：試験"],
                            }
                        ],
                        "questions": [
                            {
                                "number": 4,
                                "prompt": "筆者の考えに合うのはどれか。",
                                "choices": ["ア", "イ", "ウ", "エ"],
                                "answer": 2 if with_answers else None,
                            },
                            {
                                "number": 5,
                                "prompt": "この文章の主題は何か。",
                                "choices": ["ア", "イ", "ウ", "エ"],
                                "answer": 1 if with_answers else None,
                            },
                        ],
                    }
                ],
            },
            {
                "id": "s3",
                "kind": "listening",
                "title": "聴解",
                "localTitle": "第三部分",
                "audioRequired": True,
                "parts": [
                    {
                        "id": "s3-m1",
                        "number": 1,
                        "kind": "task-based",
                        "instruction": "まず質問を聞いてください。",
                        "pointsPerQuestion": 1,
                        "passages": [],
                        "questions": [
                            {
                                "number": None,
                                "label": "例",
                                "prompt": "",
                                "choices": ["ア", "イ", "ウ", "エ"],
                                "example": True,
                                "points": 0,
                            },
                            {
                                "number": 1,
                                "label": "1番",
                                "prompt": "",
                                "choices": ["ア", "イ", "ウ", "エ"],
                                "answer": 4 if with_answers else None,
                            },
                        ],
                    },
                    {
                        "id": "s3-m4",
                        "number": 4,
                        "kind": "quick-response",
                        "instruction": "1から3の中から選んでください。",
                        "pointsPerQuestion": 2,
                        "passages": [],
                        "questions": [
                            {
                                "number": 1,
                                "label": "1番",
                                "prompt": "",
                                "choices": [],
                                "choiceCount": 3,
                                "choicesSpoken": True,
                                "answer": 3 if with_answers else None,
                            }
                        ],
                    },
                ],
            },
        ],
    }
    prepared = prepare_exam(exam)
    # Link the reading questions to their passage, the way the importer does.
    passage_id = prepared["sections"][1]["parts"][0]["passages"][0]["id"]
    for question in prepared["sections"][1]["parts"][0]["questions"]:
        question["passageIds"] = [passage_id]
    return prepared


def write_exam(exams_root: Path, slug: str = "fixture-N1", exam: dict[str, Any] | None = None) -> Path:
    """Write an exam into an ``exams/`` tree the way the importer would."""
    directory = exams_root / slug
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "exam.json"
    path.write_text(
        json.dumps(exam if exam is not None else make_exam(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def all_questions(exam: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        question
        for section in exam["sections"]
        for part in section["parts"]
        for question in part["questions"]
    ]


def scorable(exam: dict[str, Any]) -> list[dict[str, Any]]:
    return [question for question in all_questions(exam) if not question.get("example")]
