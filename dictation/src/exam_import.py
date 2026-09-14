"""Turn a scanned JLPT past paper into an ``exam.json`` this project can serve.

Three commands, deliberately separate, because only the middle one needs a human
(or a language model) in the loop:

    render    PDF → page images + high-resolution band crops
    assemble  transcribed page JSON + answer key → exam.json
    validate  audit an assembled exam.json

Why the split
-------------
The papers people actually have are watermark-stripped scans whose embedded fonts
carry no usable ``ToUnicode`` map — ``pdftotext`` on the 2022年7月 N1 paper returns
3,000 readable characters out of 34 pages, and PyMuPDF returns glyph IDs offset by a
different constant per font. There is no text layer to recover. The page has to be
*read*, and reading it is not something this file can do.

So ``render`` prepares images a reader can work from, that reader writes one JSON
file per page in the block format described below, and ``assemble`` does the part
that must be mechanical and repeatable: joining passages across page breaks, hanging
questions off the right passage, applying the answer key, and checking the result
against the key's own counts. When the next paper arrives, only the middle step is
new work.

Page JSON contract (one file per page, ``p<NN>.json``)
------------------------------------------------------
    {
      "page": 12, "pageLabel": "第11页", "sectionHeader": null,
      "blocks": [ {block}, ... ],
      "issues": ["anything the reader was unsure about"]
    }

Each block is one of:

``part-instruction``  the 問題N heading; opens a part. ``partNumber`` required.
``passage``           a reading text / A・B text / boxed leaflet. ``label`` if printed.
``note``              a （注N） gloss; attaches to the passage it follows.
``question``          one numbered item; ``questionNumber``, ``choices``, optional
                      ``choiceCount`` (3 for 聴解 問題4) and ``label`` (「1番」「例」).
``figure``            a diagram that cannot be written as text; attaches to the
                      question or passage it follows.
``section-header``    「第三部分　聴解」; switches the assembler to the listening section.

``continuesFromPreviousPage`` / ``continuesOnNextPage`` mark a passage or a choice
list split by a page break; ``assemble`` joins them back together. A passage is
rejoined with no separator, because the break falls mid-sentence.

Answer key format (``answer-key.txt``)
--------------------------------------
Plain text mirroring the key printed on the paper's last page, so it can be checked
against the scan line by line rather than trusted::

    note      此处给出的计分准则仅限参考…
    written   1-6    1  133424      # range, 分/題, one digit per question
    order     36     3241           # 並べ替え: printed order of fragments 1-4
    listening 1      1  321232      # 問題, 分/題, one digit per question in order
    dispute   58     why this key entry looks wrong, shown beside the answer

A ``dispute`` line does NOT change the answer. These keys are published as 非标准答案,
so an entry can genuinely be wrong — but silently substituting a different answer would
be the same failure it is meant to fix, only harder to notice. The note is recorded on
the question and shown to the learner once the answer is revealed, so they can see the
argument and judge it.

Listening answers are applied *positionally* — the k-th scored question in 問題N gets
the k-th digit — because 聴解 numbering restarts per 問題 and 問題5 prints one 2番 that
carries two separately-scored 質問.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exam_schema import (  # noqa: E402
    CHOICE_COUNT,
    DEFAULT_STAR_POSITION,
    PART_KINDS,
    audit_exam,
    prepare_exam,
)

# The published 問題 layout per level. Written part numbers decide which section a
# part belongs to; after the 聴解 header the numbering restarts and parts 1-5 are
# listening. Adding N2 is adding a dict entry, not editing the walker.
JLPT_STRUCTURE: dict[str, list[dict[str, Any]]] = {
    "N1": [
        {
            "id": "s1",
            "kind": "language-knowledge",
            "title": "言語知識（文字・語彙・文法）",
            "localTitle": "第一部分　语言知识（文字・词汇・语法）",
            "parts": {
                1: "kanji-reading",
                2: "context-vocabulary",
                3: "paraphrase",
                4: "usage",
                5: "grammar-form",
                6: "sentence-composition",
                7: "text-grammar",
            },
        },
        {
            "id": "s2",
            "kind": "reading",
            "title": "読解",
            "localTitle": "第二部分　阅读",
            "parts": {
                8: "short-passage",
                9: "mid-passage",
                10: "long-passage",
                11: "integrated-reading",
                12: "thematic",
                13: "information-retrieval",
            },
        },
        {
            "id": "s3",
            "kind": "listening",
            "title": "聴解",
            "localTitle": "第三部分　听力",
            "parts": {
                1: "task-based",
                2: "comprehension-point",
                3: "overall-comprehension",
                4: "quick-response",
                5: "integrated-listening",
            },
        },
    ],
    "N2": [
        {
            "id": "s1",
            "kind": "language-knowledge",
            "title": "言語知識（文字・語彙・文法）",
            "localTitle": "第一部分　语言知识（文字・词汇・语法）",
            "parts": {
                1: "kanji-reading",
                2: "orthography",
                3: "word-formation",
                4: "context-vocabulary",
                5: "paraphrase",
                6: "usage",
                7: "grammar-form",
                8: "sentence-composition",
                9: "text-grammar",
            },
        },
        {
            "id": "s2",
            "kind": "reading",
            "title": "読解",
            "localTitle": "第二部分　阅读",
            "parts": {
                10: "short-passage",
                11: "mid-passage",
                12: "integrated-reading",
                13: "thematic",
                14: "information-retrieval",
            },
        },
        {
            "id": "s3",
            "kind": "listening",
            "title": "聴解",
            "localTitle": "第三部分　听力",
            "parts": {
                1: "task-based",
                2: "comprehension-point",
                3: "overall-comprehension",
                4: "quick-response",
                5: "integrated-listening",
            },
        },
    ],
}

EXAMPLE_LABELS = frozenset({"例", "例題", "れい"})

# How the 聴解 half announces itself. The 2024 papers head their listening booklet
# in English ("D Listening 問題用紙 (2024-2) N2"); miss it and every 1番 item is
# scored as a written question, which fails with a misleading "no printed number".
LISTENING_MARKER_RE = re.compile(r"聴\s*解|听\s*力|listening", re.IGNORECASE)


def _marks_listening(text: Any) -> bool:
    return bool(LISTENING_MARKER_RE.search(str(text or "")))


class ImportError_(Exception):
    """Raised when the page files and the answer key do not describe the same paper."""


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


def render_pages(
    pdf_path: Path,
    out_dir: Path,
    *,
    page_dpi: int = 150,
    crop_dpi: int = 260,
    bands: tuple[tuple[float, float], ...] = ((0.00, 0.40), (0.34, 0.72), (0.66, 1.00)),
    max_edge: int = 1500,
) -> list[Path]:
    """Render every page to a full-page PNG plus overlapping high-resolution bands.

    The full page is for layout — which choice belongs to which question. It is not
    good enough to read kana from: a 150 dpi A4 page is ~1750px on its long edge and
    a vision model downscales it further, which is exactly where は/ば/ぱ and つ/っ
    are lost. The bands re-render at 260 dpi and crop to ~40% of the page, so the
    same text arrives at roughly three times the effective resolution, and they
    overlap so nothing falls in a seam.
    """
    try:
        import pymupdf  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on the machine
        raise ImportError_(
            "Rendering needs PyMuPDF. Install it with: python -m pip install pymupdf\n"
            "It is only needed to import a new paper, never to study one."
        ) from exc
    try:
        from PIL import Image  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on the machine
        raise ImportError_(
            "Rendering needs Pillow. Install it with: python -m pip install pillow"
        ) from exc

    import io

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with pymupdf.open(str(pdf_path)) as document:
        for index, page in enumerate(document):
            number = index + 1
            full = out_dir / f"p{number:02d}.png"
            page.get_pixmap(dpi=page_dpi).save(str(full))
            written.append(full)

            image = Image.open(io.BytesIO(page.get_pixmap(dpi=crop_dpi).tobytes("png")))
            width, height = image.size
            for band_index, (top, bottom) in enumerate(bands):
                crop = image.crop((0, int(height * top), width, int(height * bottom)))
                scale = max_edge / max(crop.size)
                if scale < 1:
                    crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
                path = out_dir / f"p{number:02d}_{'abcdefgh'[band_index]}.png"
                crop.save(str(path))
                written.append(path)
    return written


# ---------------------------------------------------------------------------
# answer key
# ---------------------------------------------------------------------------


def parse_answer_key(text: str) -> dict[str, Any]:
    """Parse the plain-text answer key into answers, points and 並べ替え orders."""
    written: dict[int, dict[str, Any]] = {}
    listening: dict[int, dict[str, Any]] = {}
    orders: dict[int, list[int]] = {}
    stars: dict[int, int] = {}
    disputes: dict[int, str] = {}
    note = ""

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        kind, _, rest = line.partition(" ")
        rest = rest.strip()

        if kind == "note":
            note = f"{note} {rest}".strip()
            continue

        if kind == "written":
            fields = rest.split()
            if len(fields) != 3:
                raise ImportError_(f"written line needs 'range points digits': {raw_line!r}")
            span, points, digits = fields
            first, _, last = span.partition("-")
            numbers = list(range(int(first), int(last or first) + 1))
            answers = _digits(digits, raw_line)
            if len(numbers) != len(answers):
                raise ImportError_(
                    f"{span} covers {len(numbers)} questions but {len(answers)} answers are given: {raw_line!r}"
                )
            for number, answer in zip(numbers, answers):
                if number in written:
                    raise ImportError_(f"Question {number} appears in two written ranges.")
                written[number] = {"answer": answer, "points": float(points)}
            continue

        if kind == "dispute":
            number, _, text = rest.partition(" ")
            if not number.isdigit() or not text.strip():
                raise ImportError_(f"dispute line needs 'question text': {raw_line!r}")
            existing = disputes.get(int(number), "")
            disputes[int(number)] = f"{existing} {text.strip()}".strip()
            continue

        if kind == "order":
            fields = rest.split()
            if len(fields) not in (2, 3):
                raise ImportError_(f"order line needs 'question digits [star]': {raw_line!r}")
            number, digits = fields[0], fields[1]
            order = _digits(digits, raw_line)
            if sorted(order) != list(range(1, CHOICE_COUNT + 1)):
                raise ImportError_(f"order must be a permutation of 1-{CHOICE_COUNT}: {raw_line!r}")
            # ★ sits on the third blank in most published 並べ替え items, but not all:
            # 2024年7月 N2 問題8 puts it on the second. Papers where it moves say so
            # explicitly, so the key's ordering row can still be cross-checked against
            # its answer row instead of the check being switched off.
            star = DEFAULT_STAR_POSITION
            if len(fields) == 3:
                if not fields[2].isdigit() or not 1 <= int(fields[2]) <= CHOICE_COUNT:
                    raise ImportError_(
                        f"order star position must be 1-{CHOICE_COUNT}: {raw_line!r}"
                    )
                star = int(fields[2])
            orders[int(number)] = order
            stars[int(number)] = star
            continue

        if kind == "listening":
            fields = rest.split()
            if len(fields) != 3:
                raise ImportError_(f"listening line needs 'part points digits': {raw_line!r}")
            part, points, digits = fields
            listening[int(part)] = {"answers": _digits(digits, raw_line), "points": float(points)}
            continue

        raise ImportError_(f"Unknown answer-key directive {kind!r}: {raw_line!r}")

    if not written and not listening:
        raise ImportError_("The answer key contains no answers.")
    return {
        "written": written,
        "listening": listening,
        "orders": orders,
        "stars": stars,
        "disputes": disputes,
        "note": note,
    }


def _digits(value: str, line: str) -> list[int]:
    if not value.isdigit():
        raise ImportError_(f"Expected a run of digits, got {value!r}: {line!r}")
    return [int(character) for character in value]


# ---------------------------------------------------------------------------
# assemble
# ---------------------------------------------------------------------------


def load_pages(pages_dir: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for path in sorted(pages_dir.glob("p*.json")):
        with path.open(encoding="utf-8") as handle:
            page = json.load(handle)
        if not isinstance(page, dict) or "blocks" not in page:
            raise ImportError_(f"{path.name} is not a page object with a blocks array.")
        page.setdefault("page", int(re.sub(r"\D", "", path.stem) or 0))
        pages.append(page)
    if not pages:
        raise ImportError_(f"No p*.json page files in {pages_dir}")
    pages.sort(key=lambda page: int(page["page"]))
    return pages


def assemble_exam(
    pages: Iterable[dict[str, Any]],
    key: dict[str, Any],
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Build an exam dict from transcribed pages plus the answer key."""
    level = str(meta.get("level") or "N1")
    structure = JLPT_STRUCTURE.get(level)
    if structure is None:
        raise ImportError_(f"No published 問題 layout recorded for level {level!r}.")

    sections = [
        {
            "id": spec["id"],
            "number": index + 1,
            "kind": spec["kind"],
            "title": spec["title"],
            "localTitle": spec["localTitle"],
            "audioRequired": spec["kind"] == "listening",
            "parts": [],
        }
        for index, spec in enumerate(structure)
    ]
    by_id = {section["id"]: section for section in sections}
    part_kind_for = {spec["id"]: spec["parts"] for spec in structure}

    listening_started = False
    current_part: dict[str, Any] | None = None
    last_emitted: dict[str, Any] | None = None  # the passage or question a figure attaches to

    for page in pages:
        page_number = int(page.get("page") or 0)
        for block in page.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            kind = block.get("kind")

            if kind == "section-header":
                if _marks_listening(block.get("text")):
                    listening_started = True
                    current_part = None
                continue
            if _marks_listening(page.get("sectionHeader")):
                listening_started = True

            part_number = block.get("partNumber")

            if kind == "part-instruction":
                current_part = _open_part(
                    by_id, part_kind_for, listening_started, part_number, block, page_number
                )
                last_emitted = None
                continue

            if current_part is None or (
                part_number is not None and int(part_number) != int(current_part["number"])
            ):
                # A page can open with a continuation whose 問題 heading was printed
                # earlier (問題2's 3番, say). Fall back to the part the block names,
                # or to the part still open from the previous page.
                if part_number is not None:
                    current_part = _open_part(
                        by_id, part_kind_for, listening_started, part_number, None, page_number
                    )
                elif current_part is None:
                    raise ImportError_(
                        f"Page {page_number} has a {kind} block before any 問題 heading was seen."
                    )

            if kind == "passage":
                last_emitted = _add_passage(current_part, block, page_number)
            elif kind == "note":
                _add_note(current_part, block)
            elif kind == "question":
                last_emitted = _add_question(current_part, block, page_number)
            elif kind == "figure":
                _add_figure(last_emitted, current_part, block)
            # "other" blocks carry nothing a learner answers; they are dropped.

    for section in sections:
        for part in section["parts"]:
            _link_passages(part)
            _fill_cloze_prompts(section, part)

    _apply_answer_key(sections, key)

    exam = {
        "schemaVersion": 1,
        "level": level,
        "title": meta.get("title") or f"{level} 過去問",
        "sessionLabel": meta.get("sessionLabel") or "",
        "language": "ja",
        "uiLanguage": meta.get("uiLanguage") or "zh-Hans",
        "durationSec": meta.get("durationSec"),
        "source": {**(meta.get("source") or {}), "answerKeyNote": key.get("note", "")},
        "sections": [section for section in sections if section["parts"]],
    }
    if meta.get("examId"):
        exam["examId"] = meta["examId"]
    if "listeningMedia" in meta:
        exam["listeningMedia"] = meta["listeningMedia"]
    return _resolve_passage_links(prepare_exam(exam))


def _open_part(
    by_id: dict[str, dict[str, Any]],
    part_kind_for: dict[str, dict[int, str]],
    listening: bool,
    part_number: Any,
    block: dict[str, Any] | None,
    page_number: int,
) -> dict[str, Any]:
    if part_number is None:
        raise ImportError_(f"Page {page_number}: a 問題 heading with no partNumber.")
    number = int(part_number)

    section_id = None
    for candidate, parts in part_kind_for.items():
        is_listening_section = by_id[candidate]["kind"] == "listening"
        if is_listening_section != listening:
            continue
        if number in parts:
            section_id = candidate
            break
    if section_id is None:
        raise ImportError_(
            f"Page {page_number}: 問題{number} is not part of the "
            f"{'listening' if listening else 'written'} half of this level's layout."
        )

    section = by_id[section_id]
    for part in section["parts"]:
        if int(part["number"]) == number:
            if block is not None and not part.get("instruction"):
                part["instruction"] = str(block.get("text") or "")
            return part

    part = {
        "id": f"{section_id}-m{number}",
        "number": number,
        "kind": part_kind_for[section_id][number],
        "title": f"問題{number}",
        "localTitle": PART_KINDS[part_kind_for[section_id][number]]["zh"],
        "instruction": str(block.get("text") or "") if block else "",
        "pointsPerQuestion": 1.0,
        "passages": [],
        "questions": [],
    }
    section["parts"].append(part)
    section["parts"].sort(key=lambda item: int(item["number"]))
    return part


def _add_passage(part: dict[str, Any], block: dict[str, Any], page_number: int) -> dict[str, Any]:
    text = str(block.get("text") or "")
    if block.get("continuesFromPreviousPage") and part["passages"]:
        previous = part["passages"][-1]
        # The break falls mid-sentence, so the halves are joined with nothing between.
        previous["text"] = previous["text"] + text
        if page_number not in previous["pages"]:
            previous["pages"].append(page_number)
        return previous

    passage = {
        "label": block.get("label"),
        "text": text,
        "notes": [],
        "vertical": bool(block.get("vertical")),
        "pages": [page_number],
    }
    part["passages"].append(passage)
    return passage


def _add_note(part: dict[str, Any], block: dict[str, Any]) -> None:
    text = str(block.get("text") or "").strip()
    if not text:
        return
    if part["passages"]:
        part["passages"][-1]["notes"].append(text)
    else:
        part.setdefault("notes", []).append(text)


def _add_question(part: dict[str, Any], block: dict[str, Any], page_number: int) -> dict[str, Any]:
    label = block.get("label")
    choices = [str(choice) for choice in (block.get("choices") or [])]

    number = block.get("questionNumber")
    if block.get("continuesFromPreviousPage"):
        # Only a question that is *identifiably* the same one continues: same printed
        # label and same printed number. Matching on label alone merged all four of
        # 問題7's unlabelled items into one, because a page that prints only choice
        # lists gives every block label null. A transcriber also sets this flag to mean
        # "my stem is on the earlier page", which is not a continuation at all — so an
        # unmatched flag has to fall through to a new question rather than guess.
        for existing in reversed(part["questions"]):
            same_label = existing.get("label") == label
            same_number = existing.get("number") == number
            if same_label and same_number and (label is not None or number is not None):
                existing["choices"].extend(choices)
                existing["choicesSpoken"] = not existing["choices"]
                if page_number not in existing["pages"]:
                    existing["pages"].append(page_number)
                return existing

    is_example = str(label or "").strip() in EXAMPLE_LABELS
    question = {
        "number": number,
        "label": label,
        "prompt": str(block.get("text") or ""),
        "choices": choices,
        "choiceCount": int(block.get("choiceCount") or CHOICE_COUNT),
        "choicesSpoken": not choices,
        "example": is_example,
        "answer": None,
        "vertical": bool(block.get("vertical")),
        "page": page_number,
        "pages": [page_number],
        "passageIds": [],
    }
    part["questions"].append(question)
    return question


def _add_figure(target: dict[str, Any] | None, part: dict[str, Any], block: dict[str, Any]) -> None:
    text = str(block.get("text") or "").strip()
    if not text:
        return
    if target is not None and "choices" in target:
        target["figureNote"] = text
    elif target is not None:
        target.setdefault("notes", []).append(text)
    elif part["passages"]:
        part["passages"][-1]["notes"].append(text)


def _link_passages(part: dict[str, Any]) -> None:
    """Record which passage(s) each question is about, by index within the part.

    Indexes, not ids: passage ids are minted by ``prepare_exam`` from the finished
    content, so they do not exist yet at this point. ``_resolve_passage_links``
    converts these to real ids once they do.
    """
    passages = part["passages"]
    if not passages:
        return

    # 統合理解 prints two texts, A and B, and every question compares them. Attaching
    # such a question to whichever text happened to be printed last would hide half
    # the material the question asks about.
    if part["kind"] in {"integrated-reading", "integrated-listening"}:
        every = list(range(len(passages)))
        for question in part["questions"]:
            question["_passageIndexes"] = list(every)
        return

    if len(passages) == 1:
        # Covers 問題13, where the leaflet is printed on the page *after* its questions.
        for question in part["questions"]:
            question["_passageIndexes"] = [0]
        return

    for question in part["questions"]:
        chosen = 0
        for index, passage in enumerate(passages):
            if min(passage["pages"]) <= min(question["pages"]):
                chosen = index
            else:
                break
        # Within one page a question follows its own passage, and 問題8/問題9 label both
        #「(1)」「(2)」; when the transcription recorded that label, trust it over position.
        if question.get("label"):
            for index, passage in enumerate(passages):
                if passage.get("label") and passage["label"] == question["label"]:
                    chosen = index
                    break
        question["_passageIndexes"] = [chosen]


def _resolve_passage_links(exam: dict[str, Any]) -> dict[str, Any]:
    """Turn the assembly-time passage indexes into the ids ``prepare_exam`` minted."""
    for section in exam.get("sections") or []:
        for part in section.get("parts") or []:
            passages = part.get("passages") or []
            for question in part.get("questions") or []:
                indexes = question.pop("_passageIndexes", None)
                if not indexes:
                    continue
                question["passageIds"] = [
                    str(passages[index]["id"])
                    for index in indexes
                    if 0 <= index < len(passages) and passages[index].get("id")
                ]
    return exam


def _fill_cloze_prompts(section: dict[str, Any], part: dict[str, Any]) -> None:
    """Give 文章の文法 items the prompt the paper actually prints for them.

    問題7 prints no question sentence at all: the item *is* the boxed 【41】 sitting in
    the passage, and the page carries only its four choices. An empty prompt would be
    a schema error and would leave the learner with four options and no question, so
    the boxed number becomes the prompt and the passage supplies the context.
    """
    if section["kind"] == "listening":
        # A 聴解 page prints the item number and nothing else. Some transcriptions put
        # that number in the text as well as the label; keeping both would render
        # "1番" twice above four choices. The label is the canonical place for it.
        for question in part["questions"]:
            if question["prompt"].strip() == str(question.get("label") or "").strip():
                question["prompt"] = ""
        return
    for question in part["questions"]:
        if question["prompt"].strip() or question.get("number") is None:
            continue
        question["prompt"] = f"【{question['number']}】"


def _apply_answer_key(sections: list[dict[str, Any]], key: dict[str, Any]) -> None:
    written = key["written"]
    listening = key["listening"]
    orders = key["orders"]
    stars = key.get("stars") or {}
    disputes = key.get("disputes") or {}
    used_written: set[int] = set()

    for section in sections:
        for part in section["parts"]:
            scored = [question for question in part["questions"] if not question["example"]]

            if section["kind"] == "listening":
                entry = listening.get(int(part["number"]))
                if entry is None:
                    raise ImportError_(f"The answer key has no listening 問題{part['number']}.")
                answers = entry["answers"]
                if len(answers) != len(scored):
                    raise ImportError_(
                        f"聴解 問題{part['number']}: the key lists {len(answers)} answers but the pages "
                        f"contain {len(scored)} scored questions. One of the two is wrong — fix it "
                        f"rather than letting the mismatch silently shift every later answer."
                    )
                part["pointsPerQuestion"] = entry["points"]
                for question, answer in zip(scored, answers):
                    question["answer"] = answer
                    question["points"] = entry["points"]
                for index, question in enumerate(scored, start=1):
                    question["number"] = index
                continue

            points: set[float] = set()
            for question in scored:
                number = question.get("number")
                if number is None:
                    raise ImportError_(
                        f"問題{part['number']} has a scored question with no printed number."
                    )
                entry = written.get(int(number))
                if entry is None:
                    raise ImportError_(f"The answer key has no answer for question {number}.")
                question["answer"] = entry["answer"]
                question["points"] = entry["points"]
                points.add(entry["points"])
                used_written.add(int(number))
                if int(number) in orders:
                    question["answerOrder"] = orders[int(number)]
                    question["answerStar"] = stars.get(int(number), DEFAULT_STAR_POSITION)
                if int(number) in disputes:
                    question["keyNote"] = disputes[int(number)]
            if points:
                part["pointsPerQuestion"] = sorted(points)[-1]
            for question in part["questions"]:
                if question["example"]:
                    question["points"] = 0.0

    unused = sorted(set(written) - used_written)
    if unused:
        raise ImportError_(
            f"The answer key lists answers for questions that no page contains: {unused}. "
            f"A page is probably missing from the transcription."
        )

    unused_orders = sorted(set(orders) - used_written)
    if unused_orders:
        raise ImportError_(f"The answer key lists 並べ替え orders for missing questions: {unused_orders}.")

    unused_disputes = sorted(set(disputes) - used_written)
    if unused_disputes:
        raise ImportError_(f"The answer key disputes questions that do not exist: {unused_disputes}.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"  status   : {report['status']}")
    print(f"  questions: {summary['questions']}")
    print(f"  errors   : {summary['errors']}   warnings: {summary['warnings']}")
    for issue in report["issues"]:
        ref = f" [{issue['ref']}]" if issue.get("ref") else ""
        print(f"    {issue['severity']:<7} {issue['code']}{ref}: {issue['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="PDF → page images and band crops")
    render.add_argument("--pdf", required=True, type=Path)
    render.add_argument("--out", required=True, type=Path)
    render.add_argument("--page-dpi", type=int, default=150)
    render.add_argument("--crop-dpi", type=int, default=260)

    assemble = commands.add_parser("assemble", help="page JSON + answer key → exam.json")
    assemble.add_argument("--pages", required=True, type=Path)
    assemble.add_argument("--key", required=True, type=Path)
    assemble.add_argument("--meta", required=True, type=Path)
    assemble.add_argument("--out", required=True, type=Path)
    assemble.add_argument(
        "--allow-failed-audit",
        action="store_true",
        help="write the file even when the audit reports errors (inspection only)",
    )

    validate = commands.add_parser("validate", help="audit an assembled exam.json")
    validate.add_argument("--exam", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.command == "render":
        written = render_pages(args.pdf, args.out, page_dpi=args.page_dpi, crop_dpi=args.crop_dpi)
        print(f"Rendered {len(written)} images into {args.out}")
        return 0

    if args.command == "assemble":
        key = parse_answer_key(args.key.read_text(encoding="utf-8"))
        meta = json.loads(args.meta.read_text(encoding="utf-8"))
        exam = assemble_exam(load_pages(args.pages), key, meta)
        report = audit_exam(exam)
        print(f"Assembled {exam['questionCount']} questions, {exam['totalPoints']} points.")
        _report(report)
        if report["summary"]["errors"] and not args.allow_failed_audit:
            print("\nRefusing to write an exam that failed its audit. Fix the pages, or pass "
                  "--allow-failed-audit to inspect the result anyway.", file=sys.stderr)
            return 1
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {args.out}")
        return 0

    if args.command == "validate":
        exam = json.loads(args.exam.read_text(encoding="utf-8"))
        report = audit_exam(exam)
        _report(report)
        return 1 if report["summary"]["errors"] else 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
