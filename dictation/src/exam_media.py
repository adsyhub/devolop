"""Safe resolution of optional course-built listening audio for exam papers."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_PART_PATTERN = re.compile(r"問題\s*([1-5])")
_QUESTION_PATTERN = re.compile(r"(\d{1,2})番")
_QUESTION_REFERENCE_PREFIXES = ("は", "も", "目", "の", "が", "を", "に", "と", "から", "まで")


def _safe_filename(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    name = value.strip().replace("\\", "/")
    if not name or "/" in name or name in {".", ".."}:
        return None
    return name


class ExamMediaResolver:
    """Resolve a validated linkage to exactly one course audio file."""

    def __init__(self, course_store: Any) -> None:
        self.course_store = course_store
        self._hash_cache: dict[tuple[str, int, int], str] = {}

    def describe(
        self,
        exam_slug: str,
        exam: dict[str, Any],
        *,
        include_cues: bool = True,
    ) -> dict[str, Any]:
        delivery, _, _, manifest = self._locate(exam_slug, exam)
        if include_cues and delivery.get("status") == "ready" and manifest is not None:
            cues = _build_listening_cues(exam, manifest)
            delivery["cues"] = cues
            delivery["cueCount"] = len(cues)
            delivery["cueSource"] = "course-sentences"
        return delivery

    def resolve_audio(self, exam_slug: str, exam: dict[str, Any]) -> Path | None:
        delivery, audio_path, expected_hash, _ = self._locate(exam_slug, exam)
        if delivery.get("status") != "ready" or audio_path is None or expected_hash is None:
            return None
        try:
            if self._hash_file(audio_path) != expected_hash:
                return None
        except OSError:
            return None
        return audio_path

    def _locate(
        self, exam_slug: str, exam: dict[str, Any]
    ) -> tuple[dict[str, Any], Path | None, str | None, dict[str, Any] | None]:
        media = exam.get("listeningMedia")
        if media is None:
            return {"available": False, "status": "unconfigured"}, None, None, None
        if not isinstance(media, dict):
            return {"available": False, "status": "manifest-invalid"}, None, None, None

        course_slug = media.get("courseSlug")
        expected_hash = media.get("expectedSha256")
        expected_bytes = media.get("expectedBytes")
        if (
            media.get("kind") != "course-audio"
            or not isinstance(course_slug, str)
            or not _SLUG_PATTERN.fullmatch(course_slug)
            or not isinstance(expected_hash, str)
            or not _SHA256_PATTERN.fullmatch(expected_hash)
            or isinstance(expected_bytes, bool)
            or not isinstance(expected_bytes, int)
            or expected_bytes <= 0
        ):
            return self._unavailable(course_slug, "manifest-invalid")

        manifest_path = self.course_store.get_manifest_path(course_slug)
        if manifest_path is None:
            return self._unavailable(course_slug, "course-missing")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return self._unavailable(course_slug, "manifest-invalid")

        filename = _safe_filename(manifest.get("audio"))
        if filename is None:
            return self._unavailable(course_slug, "manifest-invalid")
        course_dir = manifest_path.parent.resolve()
        audio_path = (course_dir / filename).resolve()
        try:
            audio_path.relative_to(course_dir)
        except ValueError:
            return self._unavailable(course_slug, "manifest-invalid")
        if not audio_path.is_file():
            return self._unavailable(course_slug, "file-missing")
        try:
            actual_bytes = audio_path.stat().st_size
        except OSError:
            return self._unavailable(course_slug, "file-missing")
        if actual_bytes != expected_bytes:
            return self._unavailable(course_slug, "size-mismatch")

        metadata = manifest.get("buildMetadata")
        if isinstance(metadata, dict):
            if metadata.get("sourceAudioSha256") not in {None, expected_hash}:
                return self._unavailable(course_slug, "hash-mismatch")
            if metadata.get("sourceAudioBytes") not in {None, expected_bytes}:
                return self._unavailable(course_slug, "size-mismatch")

        return (
            {
                "kind": "course-audio",
                "courseSlug": course_slug,
                "available": True,
                "status": "ready",
                "url": f"/exam-media/{exam_slug}/audio",
                "bytes": actual_bytes,
                "revision": expected_hash,
            },
            audio_path,
            expected_hash,
            manifest,
        )

    @staticmethod
    def _unavailable(
        course_slug: Any, status: str
    ) -> tuple[dict[str, Any], Path | None, str | None, dict[str, Any] | None]:
        delivery: dict[str, Any] = {
            "kind": "course-audio",
            "available": False,
            "status": status,
        }
        if isinstance(course_slug, str):
            delivery["courseSlug"] = course_slug
        return delivery, None, None, None

    def _hash_file(self, audio_path: Path) -> str:
        stat = audio_path.stat()
        cache_key = (str(audio_path), stat.st_size, stat.st_mtime_ns)
        cached = self._hash_cache.get(cache_key)
        if cached is not None:
            return cached
        digest = hashlib.sha256()
        with audio_path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        value = digest.hexdigest()
        self._hash_cache[cache_key] = value
        return value


def _source_text(sentence: dict[str, Any]) -> str:
    value = sentence.get("sourceText") or sentence.get("jaText") or ""
    return unicodedata.normalize("NFKC", str(value)).strip()


def _sentence_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sentence in manifest.get("sentences") or []:
        if not isinstance(sentence, dict):
            continue
        try:
            start = float(sentence.get("startTime"))
            end = float(sentence.get("endTime"))
        except (TypeError, ValueError):
            continue
        if start < 0 or end <= start:
            continue
        rows.append({"start": start, "end": end, "text": _source_text(sentence)})
    return rows


def _part_hint(text: str) -> int | None:
    match = _PART_PATTERN.search(text)
    if match:
        return int(match.group(1))
    # ASR often hears 二 as に. These phrases identify the affected section
    # without treating an ordinary occurrence of 問題に as a section heading.
    if "問題に" in text and ("選択肢を読" in text or "読む時間" in text or "まず質問" in text):
        return 2
    if "長めの話" in text:
        return 5
    if "まず文を聞いて" in text and "返事" in text:
        return 4
    if "全体として" in text or "話の前に質問" in text:
        return 3
    return None


def _part_starts(rows: list[dict[str, Any]], part_numbers: list[int]) -> dict[int, int]:
    starts: dict[int, int] = {}
    cursor = 0
    for number in part_numbers:
        found = next(
            (index for index in range(cursor, len(rows)) if _part_hint(rows[index]["text"]) == number),
            None,
        )
        if found is None:
            continue
        starts[number] = found
        cursor = found + 1
    return starts


def _question_label(text: str) -> int | None:
    if text.startswith("一番"):
        remainder = text[2:].lstrip("。、,. ")
        if not remainder.startswith(_QUESTION_REFERENCE_PREFIXES):
            return 1
    matches = list(_QUESTION_PATTERN.finditer(text))
    # Section instructions mention "1番、2番" together; neither is the start of
    # an actual question. A real cue contains one leading label only.
    if len(matches) != 1 or "問題用紙" in text:
        return None
    match = matches[0]
    prefix = text[: match.start()].strip("。、,. ")
    if prefix and not prefix.endswith("では始めます"):
        return None
    remainder = text[match.end() :].lstrip("。、,. ")
    if remainder.startswith(_QUESTION_REFERENCE_PREFIXES):
        return None
    return int(match.group(1))


def _question_label_at(rows: list[dict[str, Any]], index: int) -> int | None:
    text = rows[index]["text"]
    label = _question_label(text)
    if label is not None:
        return label
    # ASR sometimes puts the digit at the end of one sentence and ``番`` at the
    # start of the next ("…では始めます1" / "番テレビで…"). The latter is the
    # useful seek point because it begins the question scenario.
    if text.startswith("番") and index > 0:
        match = re.search(r"(\d{1,2})\s*$", rows[index - 1]["text"])
        if match:
            return int(match.group(1))
    return None


def _next_question_after_repeated_prompt(
    rows: list[dict[str, Any]], start: int, stop: int
) -> int | None:
    """Infer a missing label from the repeated prompt at the end of 問題1/2.

    Those sections read the question once before the dialogue and once after it.
    ASR occasionally drops the following ``2番`` marker, but the duplicated prompt
    remains a stable boundary in the 精听 transcript.
    """
    for later in range(start + 1, stop):
        repeated = rows[later]["text"].strip("。?？!！ ")
        if len(repeated) < 8:
            continue
        for earlier in range(start, later):
            first = rows[earlier]["text"].strip("。?？!！ ")
            if repeated == first or first.endswith(repeated):
                return later + 1 if later + 1 < stop else None
    return None


def _question_starts(
    rows: list[dict[str, Any]],
    *,
    part_number: int,
    question_count: int,
    start: int,
    stop: int,
) -> dict[int, tuple[int, str]]:
    candidates: list[tuple[int, int]] = []
    for index in range(start + 1, stop):
        label = _question_label_at(rows, index)
        if label is not None:
            candidates.append((index, label))

    found: dict[int, tuple[int, str]] = {}
    cursor = start + 1
    for number in range(1, question_count + 1):
        candidate = next(((index, label) for index, label in candidates if index >= cursor and label == number), None)
        if candidate is None:
            continue
        index, _ = candidate
        found[number] = (index, "question-marker")
        cursor = index + 1

    if 1 not in found:
        begin = next(
            (index for index in range(start + 1, stop) if "では始めます" in rows[index]["text"]),
            None,
        )
        if begin is not None:
            text = rows[begin]["text"]
            inferred = begin if text.rstrip().endswith("では始めます") is False else begin + 1
            if inferred < stop:
                found[1] = (inferred, "section-start")

    # 問題1 and 問題2 repeat their prompts, which lets us recover an omitted
    # marker without guessing from equal-duration slices.
    if part_number in {1, 2}:
        for number in range(2, question_count + 1):
            if number in found or number - 1 not in found:
                continue
            previous = found[number - 1][0]
            following = min((index for n, (index, _) in found.items() if n > number), default=stop)
            inferred = _next_question_after_repeated_prompt(rows, previous, following)
            if inferred is not None:
                found[number] = (inferred, "repeated-prompt")

    # The final JLPT integrated item contains one shared dialogue followed by two
    # sub-questions. Both answer-sheet entries should seek to the same dialogue.
    if part_number == 5 and question_count == 4 and 3 in found and 4 not in found:
        found[4] = (found[3][0], "shared-dialogue")
    return found


def _align_question_markers(
    rows: list[dict[str, Any]], parts: list[tuple[int, list[dict[str, Any]]]]
) -> dict[tuple[int, int], int]:
    """Globally align imperfect ASR labels to the paper's known question order."""
    observed = [
        (index, label)
        for index in range(len(rows))
        if (label := _question_label_at(rows, index)) is not None
    ]
    expected = [
        (part_number, ordinal, ordinal)
        for part_number, questions in parts
        for ordinal in range(1, len(questions) + 1)
        # The fourth answer-sheet entry in 問題5 shares the spoken 3番 passage.
        if not (part_number == 5 and len(questions) == 4 and ordinal == 4)
    ]

    @lru_cache(maxsize=None)
    def solve(expected_index: int, observed_index: int) -> tuple[int, tuple[tuple[int, int], ...]]:
        if expected_index >= len(expected) or observed_index >= len(observed):
            return 0, ()
        best_score = -1
        best_pairs: tuple[tuple[int, int], ...] = ()
        if expected[expected_index][2] == observed[observed_index][1]:
            score, pairs = solve(expected_index + 1, observed_index + 1)
            best_score = score + 1
            best_pairs = ((expected_index, observed_index),) + pairs
        for next_expected, next_observed in (
            (expected_index, observed_index + 1),
            (expected_index + 1, observed_index),
        ):
            score, pairs = solve(next_expected, next_observed)
            if score > best_score:
                best_score, best_pairs = score, pairs
        return best_score, best_pairs

    _, pairs = solve(0, 0)
    return {
        (expected[expected_index][0], expected[expected_index][1]): observed[observed_index][0]
        for expected_index, observed_index in pairs
    }


def _build_listening_cues(exam: dict[str, Any], manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map exam question ids to the 精听 course's sentence timeline."""
    rows = _sentence_rows(manifest)
    if not rows:
        return {}

    parts: list[tuple[int, list[dict[str, Any]]]] = []
    for section in exam.get("sections") or []:
        if not isinstance(section, dict) or not section.get("audioRequired"):
            continue
        for part in section.get("parts") or []:
            if not isinstance(part, dict):
                continue
            number = part.get("number")
            questions = [q for q in part.get("questions") or [] if isinstance(q, dict)]
            if isinstance(number, int) and questions:
                parts.append((number, questions))
    if not parts:
        return {}

    starts = _part_starts(rows, [number for number, _ in parts])
    aligned = _align_question_markers(rows, parts)
    for position, (part_number, _) in enumerate(parts):
        if part_number in starts:
            continue
        first = aligned.get((part_number, 1))
        if first is not None:
            starts[part_number] = max(-1, first - 1)
            continue
        previous_markers = [
            index
            for previous_number, _ in parts[:position]
            for (number, _), index in aligned.items()
            if number == previous_number
        ]
        starts[part_number] = max(previous_markers) if previous_markers else -1

    # A severely clipped transcript may have lost every marker in a section.
    # Preserve ordering by making any duplicate fallback boundary advance at
    # least one sentence; the per-question estimates below then stay monotonic.
    previous_start = -1
    for part_number, _ in parts:
        starts[part_number] = max(previous_start + 1, starts.get(part_number, previous_start + 1))
        previous_start = starts[part_number]
    cues: dict[str, dict[str, Any]] = {}
    for position, (part_number, questions) in enumerate(parts):
        part_start = starts.get(part_number)
        if part_start is None:
            continue
        next_starts = [starts[number] for number, _ in parts[position + 1 :] if number in starts]
        part_stop = min(next_starts) if next_starts else len(rows)
        located = _question_starts(
            rows,
            part_number=part_number,
            question_count=len(questions),
            start=part_start,
            stop=part_stop,
        )
        for ordinal in range(1, len(questions) + 1):
            aligned_index = aligned.get((part_number, ordinal))
            if aligned_index is not None and part_start < aligned_index < part_stop:
                located[ordinal] = (aligned_index, "question-marker")
        if part_number == 5 and len(questions) == 4 and 3 in located:
            located[4] = (located[3][0], "shared-dialogue")
        # Keep every question locatable even when ASR swallowed a spoken number.
        # Estimates are constrained by the nearest real markers and snapped to a
        # sentence boundary from the 精听 timeline; they are never arbitrary file
        # offsets. The delivery method tells the UI/debugger which cues were exact.
        for ordinal in range(1, len(questions) + 1):
            if ordinal in located:
                continue
            earlier = max((number for number in located if number < ordinal), default=0)
            later = min((number for number in located if number > ordinal), default=len(questions) + 1)
            lower_index = located[earlier][0] if earlier else max(0, part_start)
            upper_index = located[later][0] if later <= len(questions) else min(part_stop, len(rows) - 1)
            if upper_index <= lower_index:
                upper_index = min(part_stop - 1, lower_index + 1)
            fraction = (ordinal - earlier) / max(1, later - earlier)
            lower_time = rows[lower_index]["start"]
            upper_time = rows[upper_index]["start"]
            target = lower_time + (upper_time - lower_time) * fraction
            estimated = min(
                range(lower_index, max(lower_index + 1, upper_index + 1)),
                key=lambda index: abs(rows[index]["start"] - target),
            )
            located[ordinal] = (estimated, "estimated-timeline")
        distinct_starts = sorted({index for index, _ in located.values()})
        for ordinal, question in enumerate(questions, start=1):
            located_row = located.get(ordinal)
            question_id = question.get("id")
            if located_row is None or not isinstance(question_id, str) or not question_id:
                continue
            row_index, method = located_row
            later = next((index for index in distinct_starts if index > row_index), part_stop)
            end = rows[later]["start"] if later < len(rows) else rows[-1]["end"]
            cues[question_id] = {
                "startSec": round(max(0.0, rows[row_index]["start"] - 0.25), 3),
                "endSec": round(max(rows[row_index]["end"], end), 3),
                "method": method,
            }
    return cues
