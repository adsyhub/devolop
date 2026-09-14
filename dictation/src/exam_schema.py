"""JLPT question bank: schema, stable identifiers, validation and scoring.

An *exam* is one sitting of a JLPT paper — 2022年7月 N1, say — stored as a single
``exam.json`` next to nothing else, the way a course is one ``manifest.json`` next
to its audio. The shape deliberately mirrors ``course_schema`` /
``bundle_quality``: ``prepare_exam`` assigns deterministic IDs and derived counts,
``audit_exam`` returns a report in exactly the shape ``audit_manifest`` returns, so
the fail-closed loading rule in ``serve_course.build_preview_server`` can be applied
to exams without inventing a second vocabulary for "this content is broken".

Three levels of nesting, because the paper has three:

    exam → section (第一部分/第二部分/第三部分) → part (問題N) → question

Reading questions hang off a *passage* that several of them share, so passages live
on the part and questions reference one by id. That is the whole reason questions are
not just a flat list: 問題9 prints one text and asks three things about it, and a
learner who answers question 2 must still see the text.

Text markup
-----------
Question and passage text is plain UTF-8 with four printable conventions, chosen so
the JSON stays readable and diffable and so nothing needs an HTML parser:

===============  ====================================================
``<u>…</u>``     the span the paper underlines (漢字読み, 言い換え類義)
``｜漢字《かんじ》``  furigana actually printed above the base text (full-width ｜)
``【41】``         a boxed question number printed inside a sentence
``★``            the marked blank in a 並べ替え question
===============  ====================================================

Passage text additionally carries two block conventions, because 情報検索 (問題13)
is a leaflet and reading it *is* the question — flattening its table into a run-on
line would destroy the only thing being tested:

``| a | b |``    a table row; a ``| --- | --- |`` row right after the first marks it a header
``> text``       a callout box drawn around a paragraph on the page

``<u>`` is the one HTML-looking token, and the web client renders it by building a
``<u>`` element rather than by assigning ``innerHTML`` — see ``exam.js``. Nothing in
this file emits or interprets HTML; the markup is validated here only for balance,
so a truncated transcription cannot reach the UI as a half-open tag.

Answers ship to the client
--------------------------
``answer`` stays in the payload the browser receives, in every mode. Hiding it would
be theatre: this is a single-user local tool, the learner owns the process, and the
dictation player already ships the expected transcript to the page. Offline support
is the real requirement — the service worker caches the exam, and an exam it cannot
grade offline is not an exam. Exam mode withholds the answer in the *interface* until
the paper is submitted, which is the honesty that actually matters here.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from typing import Any, Iterator

SCHEMA_VERSION = 1

EXAM_ID_PATTERN = re.compile(r"^e_[0-9a-f]{24}$")
QUESTION_ID_PATTERN = re.compile(r"^q_[0-9a-f]{24}$")
PASSAGE_ID_PATTERN = re.compile(r"^p_[0-9a-f]{24}$")
EXAM_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
LISTENING_MEDIA_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

LEVELS = ("N1", "N2", "N3", "N4", "N5")

SECTION_KINDS = frozenset({"language-knowledge", "reading", "listening"})

#: 問題 types, keyed by the ``kind`` a part declares. The Japanese name is the one
#: printed in the official 試験問題の構成; the Chinese gloss is what the UI shows.
PART_KINDS: dict[str, dict[str, str]] = {
    # 第一部分 言語知識（文字・語彙・文法）
    "kanji-reading": {"ja": "漢字読み", "zh": "汉字读音", "section": "language-knowledge"},
    "orthography": {"ja": "表記", "zh": "汉字书写", "section": "language-knowledge"},
    "word-formation": {"ja": "語形成", "zh": "词语构成", "section": "language-knowledge"},
    "context-vocabulary": {"ja": "文脈規定", "zh": "词汇填空", "section": "language-knowledge"},
    "paraphrase": {"ja": "言い換え類義", "zh": "近义替换", "section": "language-knowledge"},
    "usage": {"ja": "用法", "zh": "词语用法", "section": "language-knowledge"},
    "grammar-form": {"ja": "文法形式の判断", "zh": "语法形式判断", "section": "language-knowledge"},
    "sentence-composition": {"ja": "文の組み立て", "zh": "句子排序", "section": "language-knowledge"},
    "text-grammar": {"ja": "文章の文法", "zh": "文章语法", "section": "language-knowledge"},
    # 第二部分 読解
    "short-passage": {"ja": "内容理解（短文）", "zh": "短文理解", "section": "reading"},
    "mid-passage": {"ja": "内容理解（中文）", "zh": "中篇理解", "section": "reading"},
    "long-passage": {"ja": "内容理解（長文）", "zh": "长文理解", "section": "reading"},
    "integrated-reading": {"ja": "統合理解", "zh": "综合理解", "section": "reading"},
    "thematic": {"ja": "主張理解（長文）", "zh": "观点理解", "section": "reading"},
    "information-retrieval": {"ja": "情報検索", "zh": "信息检索", "section": "reading"},
    # 第三部分 聴解
    "task-based": {"ja": "課題理解", "zh": "课题理解", "section": "listening"},
    "comprehension-point": {"ja": "ポイント理解", "zh": "要点理解", "section": "listening"},
    "overall-comprehension": {"ja": "概要理解", "zh": "概要理解", "section": "listening"},
    "quick-response": {"ja": "即時応答", "zh": "即时应答", "section": "listening"},
    "integrated-listening": {"ja": "統合理解", "zh": "综合理解", "section": "listening"},
}

CHOICE_COUNT = 4
# Which blank carries the ★ in a 並べ替え item, 1-based. Almost every published paper
# stars the third blank, so that stays the default for the papers already imported;
# a paper that moves it (2024年7月 N2 問題8 stars the second) records its own position.
DEFAULT_STAR_POSITION = 3

#: Part kinds whose questions always carry an underlined span on the printed page.
UNDERLINED_PART_KINDS = frozenset({"kanji-reading", "orthography", "paraphrase"})

_UNDERLINE_OPEN = "<u>"
_UNDERLINE_CLOSE = "</u>"
_RUBY_OPEN = "《"
_RUBY_CLOSE = "》"
_BOX_OPEN = "【"
_BOX_CLOSE = "】"

# Any angle bracket that is not part of the one allowed pair. Transcription is done by
# a language model reading a scan, so "it emitted a stray tag" is a real failure mode,
# not a hypothetical one, and it must not reach the renderer.
_STRAY_TAG = re.compile(r"</?(?!u>)[A-Za-z][^>]*>")


# ---------------------------------------------------------------------------
# Preparation: deterministic IDs and derived fields
# ---------------------------------------------------------------------------


def prepare_exam(exam: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with stable IDs, sequence numbers and derived counts.

    Existing valid IDs are preserved, so re-running the importer after fixing a typo
    in one question does not invalidate the learner's history for the other 67.
    New IDs are derived from content, so two machines importing the same paper agree.
    """
    if not isinstance(exam, dict):
        raise ValueError("Exam must be an object.")

    prepared = copy.deepcopy(exam)
    prepared["schemaVersion"] = SCHEMA_VERSION

    sections = prepared.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("Exam must contain a non-empty sections array.")

    exam_id = prepared.get("examId")
    if exam_id is not None and not EXAM_ID_PATTERN.fullmatch(str(exam_id)):
        raise ValueError(f"Invalid examId: {exam_id!r}")
    if not exam_id:
        namespace = json.dumps(
            {
                "level": str(prepared.get("level") or ""),
                "sessionLabel": str(prepared.get("sessionLabel") or ""),
                "title": str(prepared.get("title") or ""),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        exam_id = "e_" + hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:24]
        prepared["examId"] = exam_id

    used_question_ids: set[str] = set()
    used_passage_ids: set[str] = set()
    sequence = 0

    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"Section {section_index} must be an object.")
        section.setdefault("id", f"s{section_index + 1}")
        section.setdefault("number", section_index + 1)

        parts = section.get("parts")
        if not isinstance(parts, list) or not parts:
            raise ValueError(f"Section {section.get('id')!r} must contain a non-empty parts array.")

        for part_index, part in enumerate(parts):
            if not isinstance(part, dict):
                raise ValueError(f"Part {part_index} of section {section.get('id')!r} must be an object.")
            part.setdefault("id", f"{section['id']}-m{part.get('number', part_index + 1)}")

            passages = part.get("passages")
            if passages is None:
                passages = []
                part["passages"] = passages
            if not isinstance(passages, list):
                raise ValueError(f"Part {part['id']!r} passages must be an array.")

            for passage in passages:
                if not isinstance(passage, dict):
                    raise ValueError(f"Part {part['id']!r} has a passage that is not an object.")
                passage_id = passage.get("id")
                if passage_id is not None and not PASSAGE_ID_PATTERN.fullmatch(str(passage_id)):
                    raise ValueError(f"Invalid passage id: {passage_id!r}")
                if not passage_id:
                    passage_id = "p_" + _digest(
                        {
                            "examId": exam_id,
                            "partId": part["id"],
                            "label": str(passage.get("label") or ""),
                            "text": str(passage.get("text") or ""),
                        }
                    )
                    passage["id"] = passage_id
                if passage_id in used_passage_ids:
                    raise ValueError(f"Duplicate passage id: {passage_id}")
                used_passage_ids.add(str(passage_id))
                passage.setdefault("label", None)
                passage.setdefault("notes", [])
                passage.setdefault("vertical", False)

            questions = part.get("questions")
            if not isinstance(questions, list) or not questions:
                raise ValueError(f"Part {part['id']!r} must contain a non-empty questions array.")

            for question_index, question in enumerate(questions):
                if not isinstance(question, dict):
                    raise ValueError(f"Question {question_index} of part {part['id']!r} must be an object.")

                question_id = question.get("id")
                if question_id is not None and not QUESTION_ID_PATTERN.fullmatch(str(question_id)):
                    raise ValueError(f"Invalid question id: {question_id!r}")
                if not question_id:
                    question_id = "q_" + _digest(
                        {
                            "examId": exam_id,
                            "partId": part["id"],
                            "number": question.get("number"),
                            "label": str(question.get("label") or ""),
                            "prompt": str(question.get("prompt") or ""),
                            "choices": list(question.get("choices") or []),
                            "ordinal": question_index,
                        }
                    )
                    question["id"] = question_id
                if question_id in used_question_ids:
                    raise ValueError(f"Duplicate question id: {question_id}")
                used_question_ids.add(str(question_id))

                sequence += 1
                question["sequence"] = sequence
                question.setdefault("number", None)
                question.setdefault("label", None)
                question.setdefault("passageIds", [])
                question.setdefault("choices", [])
                question.setdefault("choiceCount", CHOICE_COUNT)
                question.setdefault("choicesSpoken", not question.get("choices"))
                question.setdefault("answer", None)
                question.setdefault("answerOrder", None)
                question.setdefault("answerStar", DEFAULT_STAR_POSITION)
                question.setdefault("example", False)
                question.setdefault("keyNote", "")
                question.setdefault("vertical", False)
                question.setdefault("page", None)
                if question.get("points") is None:
                    # A worked 例 is printed for the learner to read, never scored.
                    question["points"] = 0.0 if question.get("example") else _number(
                        part.get("pointsPerQuestion"), 1.0
                    )
                question["answerSheetLabel"] = answer_sheet_label(section, part, question)

            part["questionCount"] = len(questions)

        section["questionCount"] = sum(int(part.get("questionCount") or 0) for part in parts)
        section.setdefault("audioRequired", section.get("kind") == "listening")

    prepared["questionCount"] = sequence
    prepared["totalPoints"] = round(
        sum(_number(question.get("points"), 0.0) for _, _, question in iter_questions(prepared)), 3
    )
    prepared["answeredKeyCount"] = sum(
        1 for _, _, question in iter_questions(prepared) if question.get("answer") is not None
    )
    prepared["contentRevision"] = content_revision(prepared)
    return prepared


def answer_sheet_label(section: dict[str, Any], part: dict[str, Any], question: dict[str, Any]) -> str:
    """The short label the answer-sheet grid prints in a cell.

    Written questions are numbered 1–68 across the whole paper and stand alone.
    Listening questions restart at 1 inside every 問題, so a bare "3" would appear five
    times in one grid; they get 問題-局部番号 instead.
    """
    number = question.get("number")
    if section.get("kind") == "listening":
        return f"{part.get('number')}-{number}" if number is not None else str(question.get("label") or "?")
    return str(number) if number is not None else str(question.get("label") or "?")


def content_revision(exam: dict[str, Any]) -> str:
    """A digest of everything a learner actually sees, for cache invalidation."""
    fields = []
    for section, part, question in iter_questions(exam):
        fields.append(
            {
                "sectionId": section.get("id"),
                "partId": part.get("id"),
                "id": question.get("id"),
                "number": question.get("number"),
                "prompt": question.get("prompt"),
                "choices": question.get("choices"),
                "answer": question.get("answer"),
                "answerOrder": question.get("answerOrder"),
                "answerStar": question.get("answerStar"),
                "choiceCount": question.get("choiceCount"),
                "keyNote": question.get("keyNote"),
            }
        )
    for section in exam.get("sections") or []:
        for part in section.get("parts") or []:
            for passage in part.get("passages") or []:
                fields.append({"passageId": passage.get("id"), "text": passage.get("text")})
    fields.append({"listeningMedia": exam.get("listeningMedia")})
    payload = json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def iter_questions(exam: dict[str, Any]) -> Iterator[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    """Yield ``(section, part, question)`` in printed order."""
    for section in exam.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for part in section.get("parts") or []:
            if not isinstance(part, dict):
                continue
            for question in part.get("questions") or []:
                if isinstance(question, dict):
                    yield section, part, question


def question_index(exam: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map question id → question, for grading a submitted answer sheet."""
    return {str(question.get("id")): question for _, _, question in iter_questions(exam)}


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def audit_exam(exam: dict[str, Any], *, require_answers: bool = True) -> dict[str, Any]:
    """Return a JSON-serializable quality report without mutating *exam*.

    Shape matches ``bundle_quality.audit_manifest`` exactly — ``status`` /
    ``summary.errors`` / ``summary.warnings`` / ``summary.issueCounts`` / ``issues`` —
    so the loader can refuse a broken exam with the same code path and the same
    ``E_COURSE_QUALITY``-style message it already uses for courses.
    """
    issues: list[dict[str, Any]] = []

    if exam.get("schemaVersion") != SCHEMA_VERSION:
        _issue(issues, "error", "schema.unsupported", f"Only schemaVersion {SCHEMA_VERSION} is supported.")
    if not str(exam.get("title") or "").strip():
        _issue(issues, "error", "exam.title_missing", "A non-empty title is required.")
    if str(exam.get("level") or "") not in LEVELS:
        _issue(issues, "error", "exam.level_invalid", f"level must be one of {', '.join(LEVELS)}.")
    if not EXAM_ID_PATTERN.fullmatch(str(exam.get("examId") or "")):
        _issue(issues, "error", "exam.id_invalid", "examId must look like e_<24 hex chars>.")
    _audit_listening_media(exam, issues)

    sections = exam.get("sections")
    if not isinstance(sections, list) or not sections:
        _issue(issues, "error", "exam.sections_missing", "A non-empty sections array is required.")
        sections = []

    seen_question_ids: set[str] = set()
    seen_written_numbers: set[int] = set()
    total_questions = 0

    for section in sections:
        if not isinstance(section, dict):
            _issue(issues, "error", "section.not_object", "Section must be an object.")
            continue
        section_id = str(section.get("id") or "?")
        section_kind = str(section.get("kind") or "")
        if section_kind not in SECTION_KINDS:
            _issue(issues, "error", "section.kind_invalid", f"Unknown section kind {section_kind!r}.", section_id)

        passage_ids = {
            str(passage.get("id"))
            for part in section.get("parts") or []
            if isinstance(part, dict)
            for passage in part.get("passages") or []
            if isinstance(passage, dict)
        }

        for part in section.get("parts") or []:
            if not isinstance(part, dict):
                _issue(issues, "error", "part.not_object", "Part must be an object.", section_id)
                continue
            part_id = str(part.get("id") or "?")
            part_kind = str(part.get("kind") or "")
            if part_kind not in PART_KINDS:
                _issue(issues, "error", "part.kind_invalid", f"Unknown part kind {part_kind!r}.", part_id)
            elif PART_KINDS[part_kind]["section"] != section_kind:
                _issue(
                    issues,
                    "error",
                    "part.kind_section_mismatch",
                    f"Part kind {part_kind!r} belongs to section kind "
                    f"{PART_KINDS[part_kind]['section']!r}, not {section_kind!r}.",
                    part_id,
                )
            if not str(part.get("instruction") or "").strip():
                _issue(issues, "warning", "part.instruction_missing", "The 問題 instruction line is empty.", part_id)
            if _number(part.get("pointsPerQuestion"), 0.0) <= 0:
                _issue(issues, "error", "part.points_invalid", "pointsPerQuestion must be a positive number.", part_id)

            for passage in part.get("passages") or []:
                if not isinstance(passage, dict):
                    _issue(issues, "error", "passage.not_object", "Passage must be an object.", part_id)
                    continue
                text = str(passage.get("text") or "")
                if not text.strip():
                    _issue(issues, "error", "passage.text_missing", "Passage text is empty.", str(passage.get("id")))
                _audit_markup(text, issues, "passage", str(passage.get("id") or "?"))

            questions = part.get("questions") or []
            if not questions:
                _issue(issues, "error", "part.questions_missing", "Part has no questions.", part_id)

            for question in questions:
                if not isinstance(question, dict):
                    _issue(issues, "error", "question.not_object", "Question must be an object.", part_id)
                    continue
                total_questions += 1
                question_id = str(question.get("id") or "?")

                if not QUESTION_ID_PATTERN.fullmatch(question_id):
                    _issue(issues, "error", "question.id_invalid", "id must look like q_<24 hex chars>.", question_id)
                if question_id in seen_question_ids:
                    _issue(issues, "error", "question.id_duplicate", "Duplicate question id.", question_id)
                seen_question_ids.add(question_id)

                prompt = str(question.get("prompt") or "")
                if not prompt.strip() and section_kind != "listening":
                    _issue(issues, "error", "question.prompt_missing", "Question prompt is empty.", question_id)
                _audit_markup(prompt, issues, "question", question_id)

                # A published key can be wrong. When it is disputed, the dispute is
                # recorded beside the answer rather than the answer being quietly
                # rewritten: substituting an editor's judgement for the printed key,
                # invisibly, is the same failure as a mis-keyed answer.
                key_note = str(question.get("keyNote") or "")
                _audit_markup(key_note, issues, "question", question_id)
                if key_note and question.get("answer") is None and not question.get("example"):
                    _issue(
                        issues,
                        "warning",
                        "question.key_note_without_answer",
                        "A dispute note is recorded but there is no answer to dispute.",
                        question_id,
                    )

                # 漢字読み and 言い換え類義 always underline the word being asked about.
                # A missing underline is not cosmetic: the four choices are readings or
                # synonyms of *one* word in the sentence, and without the rule the
                # learner has to guess which. It happens for real — a scan whose
                # watermark was stripped can lose the printed rule with it.
                if part_kind in UNDERLINED_PART_KINDS and _UNDERLINE_OPEN not in prompt:
                    _issue(
                        issues,
                        "error",
                        "question.underline_missing",
                        f"A {PART_KINDS[part_kind]['ja']} question must underline the word it asks about.",
                        question_id,
                    )

                choice_count = question.get("choiceCount")
                if (
                    not isinstance(choice_count, int)
                    or isinstance(choice_count, bool)
                    or not 2 <= choice_count <= CHOICE_COUNT
                ):
                    _issue(
                        issues,
                        "error",
                        "question.choice_count_invalid",
                        f"choiceCount must be an integer 2–{CHOICE_COUNT}, got {choice_count!r}.",
                        question_id,
                    )
                    choice_count = CHOICE_COUNT

                choices = question.get("choices")
                spoken = bool(question.get("choicesSpoken"))
                if not isinstance(choices, list):
                    _issue(issues, "error", "question.choices_invalid", "choices must be an array.", question_id)
                    choices = []
                if spoken:
                    if choices:
                        _issue(
                            issues,
                            "error",
                            "question.spoken_choices_present",
                            "choicesSpoken is true but printed choices are present; one of the two is wrong.",
                            question_id,
                        )
                    if section_kind != "listening":
                        _issue(
                            issues,
                            "error",
                            "question.spoken_choices_outside_listening",
                            "Only listening questions may have spoken choices.",
                            question_id,
                        )
                elif len(choices) != choice_count:
                    _issue(
                        issues,
                        "error",
                        "question.choice_count",
                        f"Expected {choice_count} printed choices, found {len(choices)}.",
                        question_id,
                    )
                for choice_index, choice in enumerate(choices):
                    if not str(choice or "").strip():
                        _issue(
                            issues,
                            "error",
                            "question.choice_empty",
                            f"Choice {choice_index + 1} is empty.",
                            question_id,
                        )
                    _audit_markup(str(choice or ""), issues, "choice", question_id)
                if len({str(choice).strip() for choice in choices}) != len(choices):
                    _issue(
                        issues,
                        "warning",
                        "question.choice_duplicate",
                        "Two choices are identical, which usually means a transcription slip.",
                        question_id,
                    )

                answer = question.get("answer")
                is_example = bool(question.get("example"))
                if answer is None:
                    # A 例 is the paper's own worked example. It is shown, never scored,
                    # and the published key does not list an answer for it.
                    if not is_example:
                        severity = "error" if require_answers else "warning"
                        _issue(issues, severity, "question.answer_missing", "No answer recorded.", question_id)
                elif is_example:
                    _issue(
                        issues,
                        "warning",
                        "question.example_has_answer",
                        "A 例 is not scored; recording an answer for it is misleading.",
                        question_id,
                    )
                elif not isinstance(answer, int) or isinstance(answer, bool) or not 1 <= answer <= choice_count:
                    _issue(
                        issues,
                        "error",
                        "question.answer_out_of_range",
                        f"answer must be an integer 1–{choice_count}, got {answer!r}.",
                        question_id,
                    )
                if is_example and _number(question.get("points"), 0.0) != 0.0:
                    _issue(
                        issues,
                        "error",
                        "question.example_scored",
                        "A 例 must be worth 0 points.",
                        question_id,
                    )

                order = question.get("answerOrder")
                star = question.get("answerStar", DEFAULT_STAR_POSITION)
                if part_kind == "sentence-composition":
                    if not isinstance(order, list) or sorted(order or []) != [1, 2, 3, 4]:
                        _issue(
                            issues,
                            "error",
                            "question.order_invalid",
                            "A 並べ替え question needs answerOrder as a permutation of 1–4.",
                            question_id,
                        )
                    elif not isinstance(star, int) or not 1 <= star <= CHOICE_COUNT:
                        _issue(
                            issues,
                            "error",
                            "question.order_star_invalid",
                            f"answerStar must be a blank number 1–{CHOICE_COUNT}, got {star!r}.",
                            question_id,
                        )
                    elif answer is not None and order[star - 1] != answer:
                        # The paper asks which fragment lands on ★. If the key's ordering
                        # row and its answer row disagree, one of them was mis-read and
                        # the learner would be marked wrong for a correct answer.
                        _issue(
                            issues,
                            "warning",
                            "question.order_answer_mismatch",
                            f"answerOrder puts fragment {order[star - 1]} on the ★ blank "
                            f"(blank {star}) but answer says {answer}.",
                            question_id,
                        )
                elif order is not None:
                    _issue(
                        issues,
                        "warning",
                        "question.order_unexpected",
                        "answerOrder is only meaningful for a 並べ替え question.",
                        question_id,
                    )

                question_passages = question.get("passageIds")
                if not isinstance(question_passages, list):
                    _issue(
                        issues,
                        "error",
                        "question.passages_invalid",
                        "passageIds must be an array.",
                        question_id,
                    )
                    question_passages = []
                for referenced in question_passages:
                    if str(referenced) not in passage_ids:
                        _issue(
                            issues,
                            "error",
                            "question.passage_missing",
                            f"passageIds entry {referenced!r} does not exist in this section.",
                            question_id,
                        )
                if part.get("passages") and not question_passages and not is_example:
                    _issue(
                        issues,
                        "warning",
                        "question.passage_unlinked",
                        "This part prints a passage but the question references none, so the "
                        "learner would be asked about a text the UI never shows.",
                        question_id,
                    )

                number = question.get("number")
                if section_kind != "listening" and isinstance(number, int) and not isinstance(number, bool):
                    if number in seen_written_numbers:
                        _issue(
                            issues,
                            "error",
                            "question.number_duplicate",
                            f"Question number {number} appears twice.",
                            question_id,
                        )
                    seen_written_numbers.add(number)

    if seen_written_numbers:
        first, last = min(seen_written_numbers), max(seen_written_numbers)
        # A hole *inside* the range is the signature of a page that never got
        # transcribed, and it is an error: the questions are simply gone. Starting
        # above 1 is a different thing — someone imported one 問題 rather than the
        # whole paper — and is only worth saying out loud.
        missing = sorted(set(range(first, last + 1)) - seen_written_numbers)
        if missing:
            _issue(
                issues,
                "error",
                "exam.numbering_gap",
                f"Written question numbers have a hole; missing {missing}. "
                f"A page was probably not transcribed.",
            )
        if first != 1:
            _issue(
                issues,
                "warning",
                "exam.numbering_partial",
                f"Written questions start at {first}, not 1, so this is part of a paper rather than all of it.",
            )

    declared = exam.get("questionCount")
    if isinstance(declared, int) and declared != total_questions:
        _issue(
            issues,
            "error",
            "exam.question_count_mismatch",
            f"questionCount says {declared} but {total_questions} questions are present.",
        )

    severity_counts = Counter(issue["severity"] for issue in issues)
    code_counts = Counter(issue["code"] for issue in issues)
    status = "failed" if severity_counts["error"] else "needs_review" if severity_counts["warning"] else "passed"
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": status,
        "summary": {
            "questions": total_questions,
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "issueCounts": dict(sorted(code_counts.items())),
        },
        "issues": issues,
    }


def _audit_listening_media(exam: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    """Validate optional local listening-media linkage without touching the filesystem."""
    media = exam.get("listeningMedia")
    if media is None:
        return
    if not isinstance(media, dict):
        _issue(
            issues,
            "error",
            "exam.listening_media_invalid",
            "listeningMedia must be an object when supplied.",
        )
        return
    if media.get("kind") != "course-audio":
        _issue(
            issues,
            "error",
            "exam.listening_media_kind_invalid",
            "listeningMedia.kind must be 'course-audio'.",
        )
    course_slug = media.get("courseSlug")
    if not isinstance(course_slug, str) or not EXAM_SLUG_PATTERN.fullmatch(course_slug):
        _issue(
            issues,
            "error",
            "exam.listening_media_slug_invalid",
            "listeningMedia.courseSlug must be a safe course slug.",
        )
    expected_hash = media.get("expectedSha256")
    if not isinstance(expected_hash, str) or not LISTENING_MEDIA_SHA256_PATTERN.fullmatch(expected_hash):
        _issue(
            issues,
            "error",
            "exam.listening_media_hash_invalid",
            "listeningMedia.expectedSha256 must be a lowercase SHA-256 digest.",
        )
    expected_bytes = media.get("expectedBytes")
    if isinstance(expected_bytes, bool) or not isinstance(expected_bytes, int) or expected_bytes <= 0:
        _issue(
            issues,
            "error",
            "exam.listening_media_bytes_invalid",
            "listeningMedia.expectedBytes must be a positive integer.",
        )


def _audit_markup(text: str, issues: list[dict[str, Any]], scope: str, ref: str) -> None:
    if text.count(_UNDERLINE_OPEN) != text.count(_UNDERLINE_CLOSE):
        _issue(issues, "error", f"{scope}.underline_unbalanced", "Unbalanced <u> markup.", ref)
    if text.count(_RUBY_OPEN) != text.count(_RUBY_CLOSE):
        _issue(issues, "error", f"{scope}.ruby_unbalanced", "Unbalanced 《》 furigana markup.", ref)
    if text.count(_BOX_OPEN) != text.count(_BOX_CLOSE):
        _issue(issues, "error", f"{scope}.box_unbalanced", "Unbalanced 【】 boxed-number markup.", ref)
    stray = _STRAY_TAG.search(text)
    if stray:
        _issue(
            issues,
            "error",
            f"{scope}.stray_markup",
            f"Only <u>…</u> is allowed; found {stray.group(0)!r}.",
            ref,
        )
    if "〓" in text:
        _issue(issues, "warning", f"{scope}.illegible_glyph", "Contains 〓, an unread character.", ref)


def _issue(
    issues: list[dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    ref: str | None = None,
) -> None:
    issue: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if ref is not None:
        issue["ref"] = ref
    issues.append(issue)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_answers(
    exam: dict[str, Any],
    answers: dict[str, Any],
    *,
    only: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Grade an answer sheet.

    *answers* maps question id → chosen option (1–4); anything absent, ``None`` or
    out of range counts as unanswered. Unanswered is scored as wrong for points but
    reported separately, because "did not reach it" and "got it wrong" are different
    problems and a learner reviewing a timed sitting needs to tell them apart.

    *only* restricts scoring to a set of question ids — the questions a session
    actually put in front of the learner. Without it, practising 問題1 alone and
    getting all six right scores 6 out of the paper's 176 points, and the history
    list reads "3%" for a perfect round. Pass ``None`` to score the whole paper.

    Points come from the paper's own 分/題 column. The 2022年7月 key ships with a
    caveat — the real exam uses 尺度得点, not raw points — which is carried through as
    ``scoringNote`` so the UI can repeat it rather than implying an official score.
    """
    per_section: list[dict[str, Any]] = []
    per_part: list[dict[str, Any]] = []
    per_question: list[dict[str, Any]] = []

    totals = {"points": 0.0, "earned": 0.0, "correct": 0, "wrong": 0, "unanswered": 0, "questions": 0}

    for section in exam.get("sections") or []:
        if not isinstance(section, dict):
            continue
        section_row = {
            "id": section.get("id"),
            "title": section.get("title"),
            "localTitle": section.get("localTitle"),
            "kind": section.get("kind"),
            "points": 0.0,
            "earned": 0.0,
            "correct": 0,
            "wrong": 0,
            "unanswered": 0,
            "questions": 0,
        }
        for part in section.get("parts") or []:
            if not isinstance(part, dict):
                continue
            part_row = {
                "id": part.get("id"),
                "sectionId": section.get("id"),
                "number": part.get("number"),
                "kind": part.get("kind"),
                "points": 0.0,
                "earned": 0.0,
                "correct": 0,
                "wrong": 0,
                "unanswered": 0,
                "questions": 0,
            }
            for question in part.get("questions") or []:
                if not isinstance(question, dict):
                    continue
                if question.get("example"):
                    continue  # the paper's worked example: displayed, never scored
                question_id = str(question.get("id"))
                if only is not None and question_id not in only:
                    continue
                points = _number(question.get("points"), 0.0)
                answer = question.get("answer")
                chosen = _choice(answers.get(question_id))

                if chosen is None:
                    outcome = "unanswered"
                elif answer is not None and chosen == answer:
                    outcome = "correct"
                else:
                    outcome = "wrong"

                earned = points if outcome == "correct" else 0.0
                for row in (section_row, part_row):
                    row["points"] += points
                    row["earned"] += earned
                    row[outcome] += 1
                    row["questions"] += 1
                totals["points"] += points
                totals["earned"] += earned
                totals[outcome] += 1
                totals["questions"] += 1

                per_question.append(
                    {
                        "id": question_id,
                        "sectionId": section.get("id"),
                        "partId": part.get("id"),
                        "sequence": question.get("sequence"),
                        "label": question.get("answerSheetLabel"),
                        "chosen": chosen,
                        "answer": answer,
                        "outcome": outcome,
                        "points": points,
                        "earned": earned,
                    }
                )
            # A scoped session touches a handful of parts. Reporting the other
            # twelve as "0 / 0, 0%" would bury the row the learner came to read.
            if part_row["questions"]:
                per_part.append(_round_row(part_row))
        if section_row["questions"]:
            per_section.append(_round_row(section_row))

    source = exam.get("source") if isinstance(exam.get("source"), dict) else {}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "examId": exam.get("examId"),
        "contentRevision": exam.get("contentRevision"),
        "totals": _round_row(totals),
        "sections": per_section,
        "parts": per_part,
        "questions": per_question,
        "scoringNote": source.get("answerKeyNote") or "",
    }


def _round_row(row: dict[str, Any]) -> dict[str, Any]:
    row["points"] = round(_number(row.get("points"), 0.0), 3)
    row["earned"] = round(_number(row.get("earned"), 0.0), 3)
    row["percent"] = round(100.0 * row["earned"] / row["points"], 1) if row["points"] else 0.0
    return row


def _choice(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        chosen = int(value)
    except (TypeError, ValueError):
        return None
    return chosen if 1 <= chosen <= CHOICE_COUNT else None


def _number(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number == number and number not in (float("inf"), float("-inf")) else default


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
