"""Versioned raw practice scoring, including unanswered objective questions."""
from __future__ import annotations
from typing import Any
from .audit import iter_questions

SCORING_VERSION = 3


def grade_response(question: dict[str, Any], response: Any) -> dict[str, Any]:
    answer_type = question.get("answerSpec", {}).get("type")
    if answer_type == "ESSAY":
        text = response.get("text", "") if isinstance(response, dict) else ""
        return {"status": "PENDING_REVIEW" if text.strip() else "UNANSWERED", "answered": bool(text.strip()), "correct": None,"essayStatus":"ANSWERED_PENDING_REVIEW" if text.strip() else "EMPTY","characterCount":len(text),"characterCountVersion":"CODE_POINT_V1"}
    if not isinstance(response, dict) or response.get("type") != answer_type:
        return {"status": "UNANSWERED", "answered": False, "correct": False}
    correct = question.get("correctAnswer") or {}
    if answer_type == "SINGLE_CHOICE":
        chosen = response.get("optionKey") or ""
        return {"status": "GRADED" if chosen else "UNANSWERED", "answered": bool(chosen),
                "correct": bool(chosen) and chosen == correct.get("optionKey")}
    expected = correct.get("tokens") or {}
    actual = response.get("tokens") or {}
    return {"status": "GRADED" if actual else "UNANSWERED", "answered": bool(actual),
            "complete": set(actual) == set(expected),
            "correct": bool(expected) and actual == expected,
            "slotResults": {slot: actual.get(slot) == token for slot, token in expected.items()}}


def grade_paper(paper: dict[str, Any], responses: dict[str, Any], *,
                selected_forms: list[str] | None = None) -> dict[str, Any]:
    selected = set(selected_forms if selected_forms is not None else [f.get("formCode") for f in paper.get("forms", [])])
    rows, per_form = [], {}
    for form, _, question in iter_questions(paper):
        code = form["formCode"]
        if code not in selected:
            continue
        result = grade_response(question, responses.get(question["questionId"]))
        rows.append({"questionId": question["questionId"], "formCode": code, **result})
        stats = per_form.setdefault(code, {"objective": 0, "correct": 0, "answered": 0,
                                          "unanswered": 0, "wrong": 0, "essayPending": 0, "essayUnanswered": 0})
        if question["answerSpec"]["type"] == "ESSAY":
            stats["essayPending" if result["answered"] else "essayUnanswered"] += 1
        else:
            stats["objective"] += 1
            stats["correct"] += int(result["correct"])
            stats["answered"] += int(result["answered"])
            stats["unanswered"] += int(not result["answered"])
            stats["wrong"] += int(result["answered"] and not result["correct"])
    total = sum(s["objective"] for s in per_form.values())
    correct = sum(s["correct"] for s in per_form.values())
    answered = sum(s["answered"] for s in per_form.values())
    return {"scoringVersion": SCORING_VERSION, "scoreKind": "RAW_PRACTICE", "officialScale": False,
            "objectiveCorrect": correct, "objectiveTotal": total, "objectiveAnswered": answered,
            "objectiveUnanswered": total - answered, "objectiveWrong": answered - correct,
            "objectiveAccuracy": round(correct / total, 4) if total else None,
            "answeredAccuracy": round(correct / answered, 4) if answered else None,
            "essayPending": sum(s["essayPending"] for s in per_form.values()),
            "essayEmpty":sum(s["essayUnanswered"] for s in per_form.values()),
            "essayUnanswered": sum(s["essayUnanswered"] for s in per_form.values()),
            "perForm": per_form, "questions": rows}
