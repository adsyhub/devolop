"""Turn ``pdf_ocr`` page Markdown into draft ``pages/pNN.json`` for ``exam_import``.

``src/pdf_ocr`` reads a scanned page and returns Markdown; ``src/exam_import`` wants
one JSON file per page in its block format. This is the join between them, and it
does only the part that is mechanical: recognising a 問題N heading, an item number,
a run of four choices, a （注N） gloss, and a page footer.

What it deliberately does NOT do
--------------------------------
Decide anything it cannot see. A line it cannot classify becomes passage text and an
``issues`` entry naming the line, because the alternative -- guessing -- produces a
page that looks finished and is wrong. Underlines, ★ positions and furigana come
through only if the OCR prompt preserved them; this file never invents them.

The output is a *draft*. Every page still has to be read against its rendered image
before ``assemble`` is trusted, and ``assemble`` itself re-checks the answer counts.
Treat a page with a non-empty ``issues`` list as unreviewed.

    python src/exam_ocr_to_pages.py --ocr exam-work/2024-12-N1/ocr \
                                    --out exams/2024-12-N1/pages --level N1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exam_schema import CHOICE_COUNT  # noqa: E402
from pdf_ocr.assemble import clean_page  # noqa: E402

# 問題1 is written 問題１, 問題 1 and 問題1 across these papers; the number may be
# full-width. Everything is normalised to NFKC before matching so one pattern serves.
PART_RE = re.compile(r"^#*\s*問題\s*(\d{1,2})\b[　\s]*(.*)$")
# An item opens with its printed number: "1." "1、" "12．" or a circled form.
ITEM_RE = re.compile(r"^(\d{1,2})\s*[.、．:：]\s*(.*)$")
# A choice line opens with 1-4 and a separator, or a circled digit.
CHOICE_RE = re.compile(r"^([1-4])\s*[.、．　\s]\s*(.+)$")
# Circled numerals must be read BEFORE NFKC: it rewrites ① to "1" and ㊱ to "36",
# losing the separator ITEM_RE needs, so a circled item would stop looking like one.
CIRCLED_RE = re.compile(r"^([①-⑳㉑-㉟㊱-㊿])\s*(.*)$")
NOTE_RE = re.compile(r"^[（(]\s*注\s*\d*\s*[)）]")
FOOTER_RE = re.compile(r"^<!--\s*footer:\s*(.*?)\s*-->$")
HEADER_RE = re.compile(r"^<!--\s*header:\s*(.*?)\s*-->$")
FIGURE_RE = re.compile(r"^!\[\]\(figure\)\s*$")
BLANK_PAGE_RE = re.compile(r"^<!--\s*blank page\s*-->$")
# 聴解 items are labelled 1番 / 2番 / 例, not by a running question number.
BAN_RE = re.compile(r"^(例|\d{1,2}\s*番)\s*(.*)$")
# The 聴解 booklet's running head is where the section change is printed. The 2024
# papers head it in English ("D Listening 問題用紙 (2024-2) N2") rather than 聴解, and
# without a match every 1番 item is scored as a written question with no number.
# Only running heads are tested against this, so the English word cannot be tripped
# by body text.
LISTENING_HEADER_RE = re.compile(r"聴\s*解|listening", re.IGNORECASE)
# 問題7/9 cloze passages carry a boxed number; the choices page repeats it bare.
CLOZE_RE = re.compile(r"【\s*(\d{1,2})\s*】")


def _circled_value(char: str) -> int:
    """The number a circled numeral denotes (① -> 1, ㊱ -> 36)."""
    return int(unicodedata.normalize("NFKC", char))


def _strip_fences(markdown: str) -> str:
    """Drop the ```markdown wrapper the model adds despite being told not to."""
    text = markdown.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    lines = lines[1:]
    while lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return "\n".join(lines).strip()


def _normalise(line: str) -> str:
    """NFKC so 問題１/１. match, but keep 《》｜★＿ which NFKC would not touch anyway."""
    return unicodedata.normalize("NFKC", line).strip()


class _PageBuilder:
    """Accumulates blocks for one page, flushing passage text when a block ends."""

    def __init__(self, page: int, level: str) -> None:
        self.page = page
        self.level = level
        self.blocks: list[dict[str, Any]] = []
        self.issues: list[str] = []
        self.page_label: str | None = None
        self.section_header: str | None = None
        self.part: int | None = None
        self._passage: list[str] = []
        self._question: dict[str, Any] | None = None
        self._choices: list[str] = []
        self._seen_listening = False

    # -- flushing -------------------------------------------------------------
    def flush_passage(self) -> None:
        text = "\n".join(self._passage).strip()
        self._passage = []
        if text:
            self.blocks.append({"kind": "passage", "partNumber": self.part, "text": text})

    def flush_question(self) -> None:
        if self._question is None:
            self._choices = []
            return
        question = self._question
        question["choices"] = list(self._choices)
        self._question = None
        self._choices = []
        expected = int(question.pop("_choiceCount", CHOICE_COUNT))
        got = len(question["choices"])
        if got and got != expected:
            self.issues.append(
                f"Q{question.get('questionNumber') or question.get('label')}: "
                f"{got} choices transcribed, expected {expected}. Check the page image."
            )
        self.blocks.append(question)

    def flush_all(self) -> None:
        self.flush_question()
        self.flush_passage()

    # -- line handlers --------------------------------------------------------
    def open_part(self, number: int, rest: str) -> None:
        self.flush_all()
        self.part = number
        self.blocks.append(
            {"kind": "part-instruction", "partNumber": number, "text": f"問題{number}　{rest}".strip()}
        )

    def open_question(self, *, number: int | None, label: str | None, text: str) -> None:
        self.flush_question()
        self.flush_passage()
        question: dict[str, Any] = {"kind": "question", "partNumber": self.part, "text": text}
        if number is not None:
            question["questionNumber"] = number
        if label is not None:
            question["label"] = label
        question["_choiceCount"] = CHOICE_COUNT
        self._question = question

    def wants_choice(self) -> bool:
        """True when a question is open and its choice run is not yet full."""
        return self._question is not None and len(self._choices) < CHOICE_COUNT

    def add_choice(self, index: int, text: str) -> bool:
        """Attach a choice to the open question. False if there is no question open."""
        if self._question is None:
            return False
        if index != len(self._choices) + 1:
            self.issues.append(
                f"Q{self._question.get('questionNumber') or self._question.get('label')}: "
                f"choice numbered {index} arrived at position {len(self._choices) + 1}; "
                "the printed numbering may be wrong or a choice was dropped."
            )
        self._choices.append(text.strip())
        return True

    def add_text(self, line: str) -> None:
        if self._question is not None and not self._choices:
            # A question stem wrapped onto a second line before its choices.
            self._question["text"] = f"{self._question['text']}{line}".strip()
            return
        if self._question is not None:
            # Text after a full choice run belongs to whatever comes next.
            self.flush_question()
        self._passage.append(line)

    def result(self) -> dict[str, Any]:
        self.flush_all()
        page: dict[str, Any] = {"page": self.page, "blocks": self.blocks}
        if self.page_label:
            page["pageLabel"] = self.page_label
        if self.section_header:
            page["sectionHeader"] = self.section_header
        page["issues"] = self.issues
        return page


def convert_page(markdown: str, *, page: int, level: str) -> dict[str, Any]:
    """Parse one page of OCR Markdown into the exam page-block format."""
    builder = _PageBuilder(page, level)
    body = _strip_fences(markdown)

    for raw in body.splitlines():
        circled = CIRCLED_RE.match(raw.strip())
        line = _normalise(raw)
        if not line:
            continue

        if circled:
            value = _circled_value(circled.group(1))
            rest = _normalise(circled.group(2))
            if 1 <= value <= CHOICE_COUNT and builder.wants_choice():
                builder.add_choice(value, rest)
            else:
                builder.open_question(number=value, label=None, text=rest)
            continue

        if BLANK_PAGE_RE.match(line):
            continue

        footer = FOOTER_RE.match(line)
        if footer:
            digits = re.search(r"\d+", footer.group(1))
            if digits:
                builder.page_label = digits.group(0)
            continue
        header = HEADER_RE.match(line)
        if header:
            if LISTENING_HEADER_RE.search(header.group(1)):
                builder.section_header = header.group(1)
            continue

        if FIGURE_RE.match(line):
            builder.flush_question()
            builder.blocks.append({"kind": "figure", "partNumber": builder.part, "text": "（図）"})
            continue

        part = PART_RE.match(line)
        if part:
            number = int(part.group(1))
            if builder._seen_listening or LISTENING_HEADER_RE.search(part.group(2)):
                builder._seen_listening = True
            builder.open_part(number, part.group(2))
            continue

        if NOTE_RE.match(line):
            builder.flush_question()
            builder.flush_passage()
            builder.blocks.append({"kind": "note", "partNumber": builder.part, "text": line})
            continue

        ban = BAN_RE.match(line)
        if ban:
            label = ban.group(1).replace(" ", "")
            builder.open_question(number=None, label=label, text=ban.group(2).strip())
            continue

        choice = CHOICE_RE.match(line)
        item = ITEM_RE.match(line)
        # "1. ..." is ambiguous: it opens item 1 and also numbers choice 1. A choice
        # only ever follows an open question that still wants choices, so prefer that
        # reading when one is waiting and the number continues the run.
        if choice and builder.wants_choice():
            if builder.add_choice(int(choice.group(1)), choice.group(2)):
                continue
        if item:
            builder.open_question(number=int(item.group(1)), label=None, text=item.group(2).strip())
            continue
        if choice:
            builder.issues.append(f"Choice-looking line with no question open: {line!r}")
            builder.add_text(line)
            continue

        builder.add_text(line)

    return builder.result()


def convert_directory(ocr_dir: Path, out_dir: Path, *, level: str) -> list[dict[str, Any]]:
    """Convert every cached OCR page, writing pNN.json and returning a summary."""
    pages_dir = ocr_dir / "pages"
    if not pages_dir.is_dir():
        raise SystemExit(f"No OCR pages under {pages_dir}. Run `python -m pdf_ocr run` first.")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Two passes, because whether the opening pages belong to the paper can only
    # be decided once a 問題 heading has been seen further in. The summary stays
    # in page order either way -- it is read alongside the render.
    converted: list[tuple[int, dict[str, Any] | None, str | None]] = []
    for cached in sorted(pages_dir.glob("page-*.json")):
        data = json.loads(cached.read_text(encoding="utf-8"))
        number = int(data["page"])
        if data.get("error"):
            converted.append((number, None, f"OCR error: {data['error']}"))
            continue
        # The cache holds the model's unprocessed output. document.md is what a
        # reviewer reads a page against, so the draft has to be built from the
        # same cleaned text -- otherwise a reasoning model's ``<think>`` block
        # becomes passage text in a page that looks finished.
        page = convert_page(clean_page(data.get("markdown", "")), page=number, level=level)
        converted.append((number, page, None))

    first_heading = next(
        (i for i, (_, page, _) in enumerate(converted)
         if page and any(b["kind"] == "part-instruction" for b in page["blocks"])),
        None,
    )

    summary: list[dict[str, Any]] = []
    for index, (number, page, error) in enumerate(converted):
        if error is not None:
            summary.append({"page": number, "written": False, "issues": [error]})
            continue
        # A paper opens with its cover (問題用紙・注意事項・受験番号). That is not exam
        # content, and assemble_exam refuses any block before the first 問題
        # heading -- so writing these pages guarantees an import error on every
        # paper whose scan includes the cover. All 47 reviewed papers start their
        # page set at the first 問題 heading; this makes the draft do the same.
        # Only skipped when a heading was found somewhere, so a paper the reader
        # could not classify still comes through whole rather than vanishing.
        if first_heading is not None and index < first_heading:
            summary.append({
                "page": number,
                "written": False,
                "issues": ["Front matter before the first 問題 heading; not part of the page set. "
                           f"Check page {number} of the render if you expected content here."],
            })
            continue
        target = out_dir / f"p{number:02d}.json"
        target.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        questions = [b for b in page["blocks"] if b["kind"] == "question"]
        summary.append(
            {
                "page": number,
                "written": True,
                "blocks": len(page["blocks"]),
                "questions": len(questions),
                "issues": page["issues"],
            }
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ocr", required=True, type=Path, help="pdf_ocr output dir (contains pages/)")
    parser.add_argument("--out", required=True, type=Path, help="exams/<slug>/pages")
    parser.add_argument("--level", default="N1", choices=["N1", "N2", "N3", "N4", "N5"])
    args = parser.parse_args(argv)

    summary = convert_directory(args.ocr, args.out, level=args.level)
    written = [row for row in summary if row["written"]]
    flagged = [row for row in summary if row["issues"]]
    total_questions = sum(row.get("questions", 0) for row in written)
    print(f"  pages    : {len(written)} written to {args.out}")
    print(f"  questions: {total_questions} draft items")
    print(f"  flagged  : {len(flagged)} page(s) need a human read")
    for row in flagged:
        print(f"    p{row['page']:02d}: " + "; ".join(row["issues"][:3]))
    print("\nThese pages are DRAFTS. Read each against its rendered image before assembling.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
