"""Turn an OCR'd textbook into a ``pack.json`` this project can serve.

Three commands, deliberately separate, because only the middle one needs a human:

    extract   OCR document.json → lexicon/<slug>/pages/p<NNNN>.json   (machine, then edited)
    assemble  pages + units.txt + entry-keys.json → pack.json          (mechanical)
    validate  audit an assembled pack.json                             (mechanical)

Same split as ``exam_import.py``, for the same reason: the reading step cannot be made
reliable, so it is isolated where a person can correct it, and everything on either side
of it must be repeatable without judgement calls.

Why extraction is not the same job as reading
---------------------------------------------
``docs/PDF_OCR.md`` measured this book: at the resolutions that finish in an evening, the
furigana are ~12px tall and the model *invents* them rather than reading them. So the
extractor's job is not "recover the text". It is: find the structure, keep every piece of
raw evidence next to the field it produced, and say loudly where it is unsure. Five
specific traps, each of which this book actually sprang:

1. **Unit numbering.** ``第1週``, ``第一週`` and ``第２週`` all appear in the OCR of the
   same book. Left alone they become three different units, split at random. Everything
   is normalised to ``(week, day)`` integers; a page that will not parse stops the run
   instead of being guessed at.

2. **The 目次 count is the ledger.** ``units.txt`` is transcribed by a person from the
   printed table of contents. If the assembled unit has a different number of entries,
   OCR dropped a block — and a learner studying half a grammar table has no way to
   discover which half is missing. That is an error, never a warning.

3. **``> `` lines and ``<!-- ruby: -->`` comments are data.** The OCR's second pass
   merges the floating connection boxes and example translations in as quoted lines, and
   turns furigana into HTML comments. Dropping them as Markdown noise drops the
   connection tables. But ruby comments are only ever *hints*: they are recorded under
   ``rubyHints`` and never written into a ``reading`` field.

4. **Connection abbreviations are not Japanese.** The page prints ``Aくて / naで /
   Vたくて``; this book's OCR read ``naで`` as ``なで``. ``connectionRaw`` keeps what was
   printed for line-by-line checking, and ``assemble`` maps it through the book's own
   legend (``lexicon_schema.CONNECTION_FORMS``). An unknown abbreviation is an error.

5. **``pack.json`` is a build product.** Fix typos in ``pages/`` and re-run assemble.

Page JSON contract (one file per page, ``p<NNNN>.json``)
--------------------------------------------------------
    {
      "page": 18,
      "unitHeader": {"week": 1, "day": 1, "title": "熱っぽい"},
      "blocks": [ {block}, ... ],
      "issues": [ {"severity": "error", "code": "...", "message": "...", "blockId": "..."} ]
    }

``type`` is one of ``entry`` (one item), ``unit-header``, ``note``, ``exercise`` (the Day
7 practice test — that belongs to the question bank, not here) and ``front-matter``.

An ``issue`` with severity ``error`` blocks every entry on that page from reaching
``pack.json``; ``warning`` ships with the entry as a flag.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from distribution_policy import audit_entry_key_registry  # noqa: E402
from lexicon_schema import (  # noqa: E402
    ConnectionError_,
    SLUG_PATTERN,
    audit_pack,
    default_card_templates,
    parse_connection_line,
    prepare_pack,
)

REGISTRY_VERSION = 1

#: The practice test that closes every week. It is a JLPT-format exercise with an answer
#: key, which is the question bank's job — importing it here would be the same content in
#: two stores with two ideas of what a correct answer is.
EXERCISE_DAY = 7

_KANJI_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

_WEEK = re.compile(r"第\s*([0-9０-９一二三四五六七八九十]+)\s*週")
_DAY = re.compile(r"^\s*([0-9０-９一二三四五六七八九十]+)\s*日目\s*(.*)$")
_RUBY_COMMENT = re.compile(r"<!--\s*ruby:\s*(.*?)\s*-->")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_QUOTE_LINE = re.compile(r"^\s*>\s?")
_FENCE = re.compile(r"^\s*```")
_PARAPHRASE = re.compile(r"[（(]\s*=\s*(.+?)\s*[)）]")
_EXAMPLE_MARK = re.compile(r"^\s*れい\s*")
#: A line that is nothing but space-separated kana runs: the furigana row, delivered by
#: the OCR's second pass as if it were a line of body text.
_KANA_RESIDUE = re.compile(r"(?:[぀-ヿ]{1,8}[ 　]+){1,}[぀-ヿ]{1,8}")

_KANA = re.compile(r"[぀-ゟ゠-ヿ]")
_HANGUL = re.compile(r"[가-힯ᄀ-ᇿ]")
_HAN = re.compile(r"[一-鿿]")
_LATIN = re.compile(r"[A-Za-z]")
_SENTENCE_END = re.compile(r"[。？！?!]\s*$")

#: Lines the page prints that are not content: page furniture, the practice section, the
#: cross-references to the answer booklet.
_FURNITURE = re.compile(
    r"^\s*(?:<!--\s*(?:footer|header|box|blank page)|練習|答えは|\(答えは|（答えは|左ページ|前の日|"
    r"実戦問題|\d+\s*[■・]|[■・]\s*\d+|Week\s+\d|第\s*\d+\s*周)"
)


class ImportError_(Exception):
    """A failure that must stop the run rather than degrade the output."""


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------


def normalize_number(text: str) -> int | None:
    """``"1"`` / ``"２"`` / ``"一"`` → ``1``.

    Trap 1. All three spellings of every week number appear in this book's OCR, so a
    literal comparison silently produces three units where there is one.
    """
    raw = unicodedata.normalize("NFKC", str(text or "")).strip()
    if not raw:
        return None
    if raw.isdigit():
        return int(raw)
    if raw == "十":
        return 10
    if len(raw) == 2 and raw[0] == "十" and raw[1] in _KANJI_DIGITS:
        return 10 + _KANJI_DIGITS[raw[1]]
    if len(raw) == 2 and raw[1] == "十" and raw[0] in _KANJI_DIGITS:
        return _KANJI_DIGITS[raw[0]] * 10
    if len(raw) == 1 and raw in _KANJI_DIGITS:
        return _KANJI_DIGITS[raw]
    return None


def unit_id(week: int, day: int) -> str:
    return f"w{week}d{day}"


def script_of(text: str) -> str:
    """Which language a printed line is in, by script.

    The book prints every example with Japanese, English, Chinese and Korean versions
    stacked with no labels, so the script is the only signal there is. Japanese always
    carries kana in this book; Chinese never does.
    """
    stripped = str(text or "")
    if _HANGUL.search(stripped):
        return "ko"
    if _KANA.search(stripped):
        return "ja"
    if _HAN.search(stripped):
        return "zh"
    if _LATIN.search(stripped):
        return "en"
    return "unknown"


def strip_ruby_fragments(line: str) -> tuple[str, list[str]]:
    """Split a line into its text and the furigana fragments OCR merged into it.

    The second OCR pass reads the furigana row as if it were part of the translation
    line, giving ``"わたし こ ころ びょうき I tended to get sick"``. The kana run is
    dropped from the text and returned separately, as a hint — never as a reading.
    """
    hints: list[str] = []
    text = line
    while True:
        match = re.match(r"^\s*((?:[぀-ヿ]{1,8}\s+){1,8})(?=[A-Za-z一-鿿가-힯])", text)
        if not match:
            break
        hints.extend(match.group(1).split())
        text = text[match.end() :]
    return text.strip(), hints


def clean_line(line: str) -> tuple[str, list[str]]:
    """Strip quoting, HTML comments and merged furigana; return text plus ruby hints."""
    hints = [fragment for match in _RUBY_COMMENT.finditer(line) for fragment in match.group(1).split()]
    text = _HTML_COMMENT.sub("", line)
    text = _QUOTE_LINE.sub("", text)
    text, merged = strip_ruby_fragments(text)
    hints.extend(merged)
    return text.strip(), hints


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------


def extract_pages(
    document: dict[str, Any],
    *,
    exercise_day: int = EXERCISE_DAY,
    kind: str = "grammar",
) -> list[dict[str, Any]]:
    """OCR ``document.json`` → one page record per page, in printed order."""
    if kind not in {"grammar", "word"}:
        raise ImportError_(f"Unsupported lexicon kind {kind!r}.")
    pages = document.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ImportError_("The OCR document has no pages.")

    extracted: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None  # the unit whose spread we are inside

    for source in pages:
        if not isinstance(source, dict):
            continue
        number = int(source.get("page") or 0)
        markdown = str(source.get("markdown") or "")
        box = str(source.get("box") or "")

        header = _find_unit_header(markdown)
        printed_week = _printed_week(markdown)
        if header is not None:
            current = header
        elif printed_week is not None and (current is None or printed_week != current.get("week")):
            # A page that opens a week the extractor is not already inside, but whose
            # ``M日目`` line did not survive the scan. Carrying on under the previous
            # unit would file this unit's entries under the last one — a silent
            # mis-attribution, which is worse than an unimported page because the entries
            # do appear, in the wrong lesson.
            extracted.append(_unattributed_page(number, printed_week))
            current = None
            continue
        elif current is None:
            extracted.append(_front_matter_page(number))
            continue

        unit = dict(current) if current else None
        if unit and unit.get("day") == exercise_day:
            extracted.append(_exercise_page(number, unit))
            continue

        page = _extract_lesson_page(
            number,
            markdown,
            box,
            unit,
            started_here=header is not None,
            kind=kind,
        )
        extracted.append(page)

    return extracted


def _find_unit_header(markdown: str) -> dict[str, Any] | None:
    """Return ``{week, day, title}`` if this page opens a unit.

    A unit's left page prints ``第N週 <week title>`` and ``M日目 <unit title>``; its right
    page prints neither and continues the same unit.
    """
    lines = [clean_line(line)[0] for line in markdown.split("\n")[:12]]
    week = None
    for line in lines:
        match = _WEEK.search(line)
        if match:
            week = normalize_number(match.group(1))
            break
    for line in lines:
        match = _DAY.match(line)
        if not match:
            continue
        day = normalize_number(match.group(1))
        if day is None or week is None:
            continue
        title = match.group(2).strip()
        return {"week": week, "day": day, "title": _japanese_head(title)}
    return None


def _japanese_head(title: str) -> str:
    """The unit title, without the English / Chinese / Korean versions printed after it.

    ``"かゆくてたまらない I can't stand the itchiness 痒得难以忍受 가려워서"`` → the first
    part. The book sets them on one line with no separator, so the split is at the first
    run of Latin or Hangul.
    """
    match = re.search(r"[A-Za-z가-힯]", title)
    head = title[: match.start()] if match else title
    return head.strip(" 　·・|")


def _printed_week(markdown: str) -> int | None:
    """The 第N週 running head, if this page prints one."""
    for line in markdown.split("\n")[:12]:
        match = _WEEK.search(clean_line(line)[0])
        if match:
            return normalize_number(match.group(1))
    return None


def _unattributed_page(number: int, week: int) -> dict[str, Any]:
    return {
        "page": number,
        "unitHeader": None,
        "blocks": [],
        "issues": [
            {
                "severity": "error",
                "code": "extract.unit_header_missing",
                "message": f"This page opens week {week} but no 「N日目」 line survived the scan. "
                "Write unitHeader in by hand; entries here belong to a unit that cannot be named.",
            }
        ],
    }


def _front_matter_page(number: int) -> dict[str, Any]:
    return {
        "page": number,
        "unitHeader": None,
        "blocks": [{"id": f"p{number:04d}-b1", "sourceAnchor": f"pdf:{number}:block:1", "type": "front-matter"}],
        "issues": [],
    }


def _exercise_page(number: int, unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "page": number,
        "unitHeader": {**unit},
        "blocks": [{"id": f"p{number:04d}-b1", "sourceAnchor": f"pdf:{number}:block:1", "type": "exercise"}],
        "issues": [],
    }


def _extract_lesson_page(
    number: int,
    markdown: str,
    box: str,
    unit: dict[str, Any] | None,
    *,
    started_here: bool,
    kind: str = "grammar",
) -> dict[str, Any]:
    """Split one lesson page into entry blocks.

    An entry opens with its 見出し語 printed alone on a line and runs until the next one.
    The connection table is set in a floating box beside it, which the OCR delivers on a
    separate channel (``box``); those groups are matched to entries by order, and a count
    mismatch is reported rather than zipped together optimistically.
    """
    issues: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    lines = markdown.split("\n")

    if started_here and unit:
        blocks.append(
            {
                "id": f"p{number:04d}-b1",
                "sourceAnchor": f"pdf:{number}:block:1",
                "type": "unit-header",
                "week": unit["week"],
                "day": unit["day"],
                "title": unit["title"],
            }
        )

    groups = _split_entry_groups(lines, skip_header=started_here)
    box_groups = _split_box_groups(box)
    sparse_box_index = 0

    for index, group in enumerate(groups):
        block_number = len(blocks) + 1
        block = _build_entry_block(number, block_number, group)
        if block is None:
            continue
        if len(box_groups) == len(groups):
            box_group = box_groups[index]
        elif not block.get("connectionRaw") and sparse_box_index < len(box_groups):
            # Some OCR pages expose only the floating boxes that the body pass missed.
            # In that sparse case a body-connected entry must not consume the next box;
            # it belongs to the next entry lacking a connection.
            box_group = box_groups[sparse_box_index]
            sparse_box_index += 1
        else:
            box_group = None
        if box_group:
            if not block.get("connectionRaw") and box_group["connectionRaw"]:
                # The connection table floats beside the example column and the
                # whole-page pass loses it often enough that docs/PDF_OCR.md calls it out
                # by name; the box channel is the second reading of the same region.
                block["connectionRaw"] = list(box_group["connectionRaw"])
                block["connectionSource"] = "box"
            for language, text in box_group["gloss"].items():
                block["gloss"].setdefault(language, text)
            block["notes"].extend(box_group["notes"])
        blocks.append(block)

    for block in blocks:
        if block.get("type") != "entry":
            continue
        if not str(block.get("headword") or "").strip():
            _issue(
                issues,
                "error",
                "extract.headword_missing",
                "An entry block was found with no headword; the printed 見出し語 was lost.",
                block["id"],
            )
        if kind == "grammar" and not block.get("connectionRaw"):
            _issue(
                issues,
                "error",
                "extract.connection_missing",
                "No connection table found for this entry. The floating box is the part "
                "whole-page OCR drops most often; check the crop before editing.",
                block["id"],
            )
        if not block.get("examples"):
            _issue(issues, "warning", "extract.examples_missing", "No example sentence found.", block["id"])
        elif not any(example.get("zh") for example in block["examples"]):
            _issue(issues, "warning", "extract.translation_missing", "No Chinese translation found.", block["id"])
        if not (block.get("gloss") or {}).get("zh"):
            _issue(
                issues,
                "warning",
                "extract.gloss_zh_missing",
                "No Chinese gloss for the entry itself. Check the printed page and add it "
                "to pages/ before assembly.",
                block["id"],
            )

    entry_blocks = [block for block in blocks if block.get("type") == "entry"]
    if unit and started_here and not entry_blocks:
        _issue(
            issues,
            "error",
            "extract.unit_empty",
            f"Unit {unit_id(unit['week'], unit['day'])} opens here but no entry could be read from the page.",
        )
    if entry_blocks and len(box_groups) and len(box_groups) != len(entry_blocks):
        _issue(
            issues,
            "warning",
            "extract.box_count_mismatch",
            f"{len(entry_blocks)} entries but {len(box_groups)} connection boxes on this page; "
            "the pairing may be off by one.",
        )

    return {
        "page": number,
        "unitHeader": {**unit} if unit else None,
        "blocks": blocks,
        "issues": issues,
    }


def _split_entry_groups(lines: list[str], *, skip_header: bool) -> list[list[str]]:
    """Group a page's lines by headword line.

    The headword rule is positional as well as textual: the book prints the 見出し語 on
    its own line with vertical space under it, so a candidate must be *followed by a
    blank line*. Without that test the ``れい`` phrase lists — 「子どもっぽい / 男っぽい／
    女っぽい / 油っぽい／水っぽい」, which are examples *of* the pattern printed directly
    under it — each look exactly like a headword, and one entry becomes eight.
    """
    groups: list[list[str]] = []
    current: list[str] | None = None
    seen_header = not skip_header

    for index, raw in enumerate(lines):
        # ``pdf_ocr`` appends the independently recognised floating-box channel to
        # ``markdown`` after this sentinel as well as exposing it through ``box``.
        # Reading past it parses connection legends as extra lesson entries, then
        # pairs those invented entries with the same boxes a second time.
        if re.match(r"^\s*<!--\s*box\s*-->\s*$", raw, re.IGNORECASE):
            break
        if _FENCE.match(raw):
            continue
        text, _hints = clean_line(raw)
        if not text:
            continue
        if not seen_header:
            if _DAY.match(text):
                seen_header = True
            continue
        if _FURNITURE.match(text) or _WEEK.search(text) and len(text) < 30:
            # 練習 marks the end of the teaching column: everything after it on the page
            # is the day's exercise, which belongs to the question bank.
            if re.match(r"^\s*練習", text):
                break
            continue
        if _is_headword(text) and (
            _followed_by_blank(lines, index)
            or _followed_by_matching_sentence(lines, index, text)
        ):
            current = [text]
            groups.append(current)
            continue
        if current is None:
            continue
        current.append(text)
    return groups


def _followed_by_blank(lines: list[str], index: int) -> bool:
    """Is the next printed line on the page blank? Measured on raw lines.

    Raw, not cleaned: a ``<!-- ruby: … -->`` comment cleans away to nothing but occupies
    a printed line, and the space under a headword is what distinguishes it from the
    first item of the list printed under a connection table.
    """
    following = lines[index + 1] if index + 1 < len(lines) else ""
    return not following.strip()


def _followed_by_matching_sentence(lines: list[str], index: int, candidate: str) -> bool:
    """Recover a title-band entry when OCR swallowed the following blank line.

    The printed title is a concrete fragment repeated (and underlined) in its first
    Japanese example.  Requiring that repetition keeps labels such as ``硬`` and the
    introductory speech bubbles from becoming entries while recovering titles such as
    ``車はもとより自転車も`` whose next scanned line is a style marker rather than the
    expected empty line.
    """
    needle = re.sub(r"[\s　]", "", candidate)
    if len(needle) < 3:
        return False
    checked = 0
    for raw in lines[index + 1 :]:
        if re.match(r"^\s*<!--\s*box\s*-->\s*$", raw, re.IGNORECASE):
            break
        text, _hints = clean_line(raw)
        if not text:
            continue
        checked += 1
        compact = re.sub(r"[\s　]", "", text)
        if script_of(text) == "ja" and _SENTENCE_END.search(text) and needle in compact:
            return True
        if checked >= 8:
            break
    return False


def _is_headword(text: str) -> bool:
    """A line that is a 見出し語 rather than an example, translation or note.

    Short, Japanese, no sentence punctuation, no gloss parenthesis, no ``／`` alternation.
    Deliberately strict: a missed headword becomes a visible ``headword_missing`` error,
    while a greedy rule silently cuts one entry into three and nothing says so.
    """
    if len(text) > 24 or script_of(text) != "ja":
        return False
    if _SENTENCE_END.search(text) or "、" in text or "=" in text:
        return False
    if "／" in text or "/" in text:
        return False
    if _KANA_RESIDUE.fullmatch(text):
        # "かれ なに い" — the furigana row, read as if it were a line of its own.
        return False
    if _EXAMPLE_MARK.match(text) or text.startswith(("◆", "◇", "※", "！", "!")):
        return False
    if _looks_like_connection(text):
        return False
    return True


def _looks_like_connection(text: str) -> bool:
    try:
        parse_connection_line(text)
    except ConnectionError_:
        return False
    return True


def _build_entry_block(page: int, index: int, group: list[str]) -> dict[str, Any] | None:
    """Turn one headword-led run of lines into an ``entry`` block."""
    if not group:
        return None
    headword, *rest = group
    block: dict[str, Any] = {
        "id": f"p{page:04d}-b{index}",
        "sourceAnchor": f"pdf:{page}:block:{index}",
        "type": "entry",
        "headword": headword,
        "gloss": {},
        "connectionRaw": [],
        "examples": [],
        "notes": [],
        "rubyHints": [],
        "continuesOnNextPage": False,
    }

    pending: dict[str, Any] | None = None
    for line in rest:
        if _looks_like_connection(line):
            block["connectionRaw"].append(line)
            continue
        if _EXAMPLE_MARK.match(line):
            block["notes"].append(line)
            continue

        language = script_of(line)
        paraphrase = _PARAPHRASE.search(line)
        # The book prints the plain-Japanese restatement inline, "…たまらない。(=とても…)",
        # so the sentence does not end at its own full stop until that is taken off.
        body = _PARAPHRASE.sub("", line).strip()
        if language == "ja" and _SENTENCE_END.search(body):
            pending = {"ja": body, "paraphrase": paraphrase.group(1) if paraphrase else ""}
            block["examples"].append(pending)
            continue
        if pending is not None and language in {"zh", "en", "ko"} and not pending.get(language):
            pending[language] = line
            continue
        if language == "ja":
            block["notes"].append(line)

    for example in block["examples"]:
        for language in ("zh", "en", "ko", "paraphrase"):
            example.setdefault(language, "")
    return block


#: Where a grammar item's meaning is actually printed. Not beside the headword — in the
#: side box, as 「〜という意味。/ Meaning "…" / 意思是"…" / 〜라는 의미」. Keeping only the
#: connection lines out of that box (the first version of this function) threw away the
#: one place in the book each item's gloss exists.
_MEANING_MARKERS = {
    "zh": ("意思", "意味", "含义"),
    "en": ("meaning", "means"),
    "ko": ("의미", "뜻"),
}


def _split_box_groups(box: str) -> list[dict[str, Any]]:
    """The floating boxes, one record per box.

    A box holds three things that are not interchangeable: the connection table, a gloss
    of the pattern, and ``れい`` lists of further phrases using it.
    """
    groups: list[dict[str, Any]] = []
    for chunk in re.split(r"\n\s*\n", box.strip()):
        record: dict[str, Any] = {"connectionRaw": [], "gloss": {}, "notes": []}
        for raw in chunk.split("\n"):
            text, _hints = clean_line(raw)
            if not text:
                continue
            if _looks_like_connection(text):
                record["connectionRaw"].append(text)
                continue
            language = script_of(text)
            markers = _MEANING_MARKERS.get(language)
            if markers and any(marker in text.lower() for marker in markers) and language not in record["gloss"]:
                record["gloss"][language] = text
                continue
            record["notes"].append(text)
        if record["connectionRaw"] or record["gloss"]:
            groups.append(record)
    return groups


def _issue(
    issues: list[dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    block_id: str | None = None,
) -> None:
    issue: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if block_id:
        issue["blockId"] = block_id
    issues.append(issue)


# ---------------------------------------------------------------------------
# units.txt — the ledger a person transcribes from the printed 目次
# ---------------------------------------------------------------------------


def parse_units_file(text: str) -> list[dict[str, Any]]:
    """Parse the hand-transcribed table of contents.

    One unit per line, ``#`` comments ignored::

        第1週 1日目 熱っぽい 4
        第1週 2日目 空を飛びたいんだもの 3

    The trailing integer is the number of entries printed in that unit. It is the whole
    reason the file exists: without an independent count, a unit that lost a block to OCR
    looks exactly like a unit that was short to begin with.
    """
    units: list[dict[str, Any]] = []
    uncounted: list[int] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        week_match = _WEEK.search(line)
        day_match = re.search(r"([0-9０-９一二三四五六七八九十]+)\s*日目", line)
        count_match = re.search(r"(\d+)\s*$", line)
        if week_match and day_match and line.rstrip().endswith("?"):
            # `?` is how the template says "nobody has counted this unit yet". It is
            # called out separately because the alternative — writing a plausible number
            # to make the run pass — turns the one independent check in this pipeline
            # into a copy of the thing it is checking.
            uncounted.append(number)
            continue
        if not (week_match and day_match and count_match):
            raise ImportError_(
                f"units.txt line {number} is not '第N週 M日目 <title> <count>': {raw.strip()!r}"
            )
        week = normalize_number(week_match.group(1))
        day = normalize_number(day_match.group(1))
        if week is None or day is None:
            raise ImportError_(f"units.txt line {number} has an unreadable week or day: {raw.strip()!r}")
        title = line[day_match.end() : count_match.start()].strip()
        units.append(
            {
                "unitId": unit_id(week, day),
                "week": week,
                "day": day,
                "label": f"第{week}週 {day}日目",
                "title": title,
                "expectedEntries": int(count_match.group(1)),
            }
        )
    if uncounted:
        raise ImportError_(
            f"{len(uncounted)} units in units.txt still have no entry count (lines "
            f"{uncounted[:10]}{' …' if len(uncounted) > 10 else ''}).\n"
            "Open the book at that unit, count the 見出し語 boxes printed in it, and replace "
            "the '?'. This number cannot be taken from the OCR: it exists precisely to catch "
            "the blocks the OCR dropped."
        )
    if not units:
        raise ImportError_("units.txt is empty; nothing can be reconciled against it.")
    duplicates = sorted({unit["unitId"] for unit in units if [u["unitId"] for u in units].count(unit["unitId"]) > 1})
    if duplicates:
        raise ImportError_(f"units.txt lists these units more than once: {', '.join(duplicates)}")
    return units


# ---------------------------------------------------------------------------
# entry-keys.json — the identity registry
# ---------------------------------------------------------------------------


def load_registry(path: Path, pack_id: str) -> dict[str, Any]:
    if not path.is_file():
        return {"schemaVersion": REGISTRY_VERSION, "packId": pack_id, "nextKey": 1, "entries": []}
    registry = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(registry.get("entries"), list):
        raise ImportError_(f"{path} is not an entry-key registry.")
    if str(registry.get("packId") or "") != pack_id:
        raise ImportError_(
            f"{path} belongs to pack {registry.get('packId')!r}, not {pack_id!r}. "
            "The packId is an immutable namespace; renaming the directory does not change it."
        )
    return registry


def save_registry(path: Path, registry: dict[str, Any]) -> None:
    verdict = audit_entry_key_registry(registry)
    if not verdict["passed"]:
        # The registry is the one pack file that is committed. A headword or a dictionary
        # id in it would put the book's own selection of items into version control.
        raise ImportError_(
            "Refusing to write an entry-key registry carrying content fields: "
            + ", ".join(verdict["offenders"])
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_keys(
    registry: dict[str, Any],
    anchors: list[str],
    *,
    accept_new: bool,
) -> tuple[dict[str, str], list[str]]:
    """Map each ``sourceAnchor`` to its frozen ``entryKey``.

    A new anchor is reported, not quietly assigned: re-running ``extract`` after a change
    to the page splitter renumbers blocks, and letting that mint a fresh key would hand
    every learner a brand-new card for an entry they have been studying for a month. The
    fix for a moved entry is to repoint its existing key, which is a reviewable one-line
    diff in ``entry-keys.json``.
    """
    known = {str(item.get("sourceAnchor")): str(item.get("entryKey")) for item in registry.get("entries") or []}
    unknown = [anchor for anchor in anchors if anchor not in known]
    if unknown and not accept_new:
        return known, unknown

    next_key = int(registry.get("nextKey") or 1)
    for anchor in unknown:
        key = f"e{next_key:04d}"
        next_key += 1
        registry.setdefault("entries", []).append({"entryKey": key, "sourceAnchor": anchor})
        known[anchor] = key
    registry["nextKey"] = next_key
    registry["entries"] = sorted(registry.get("entries") or [], key=lambda item: str(item.get("entryKey")))
    return known, []


# ---------------------------------------------------------------------------
# assemble
# ---------------------------------------------------------------------------


def load_pages(pages_dir: Path) -> list[dict[str, Any]]:
    if not pages_dir.is_dir():
        raise ImportError_(f"No pages directory: {pages_dir}")
    pages: list[dict[str, Any]] = []
    for path in sorted(pages_dir.glob("p*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(page, dict):
            raise ImportError_(f"{path.name} must contain a JSON object.")
        pages.append(page)
    if not pages:
        raise ImportError_(f"No page files in {pages_dir}")
    return sorted(pages, key=lambda page: int(page.get("page") or 0))


def assemble_pack(
    pages: list[dict[str, Any]],
    units: list[dict[str, Any]],
    registry: dict[str, Any],
    meta: dict[str, Any],
    *,
    accept_new_keys: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pages + ledger + registry → ``(pack, assembly report)``.

    Everything that can fail closed does. The reconciliation against ``units.txt`` runs
    last and reports every mismatched unit at once, because "you are three entries short
    somewhere in 48 units" is not an actionable message.
    """
    pack_id = str(meta.get("packId") or "")
    if not pack_id:
        raise ImportError_("pack-meta.json must set packId.")

    blocked_pages = {
        int(page.get("page") or 0)
        for page in pages
        if any(str(issue.get("severity")) == "error" for issue in page.get("issues") or [])
    }

    collected: list[dict[str, Any]] = []
    for page in pages:
        page_number = int(page.get("page") or 0)
        header = page.get("unitHeader")
        if not isinstance(header, dict):
            continue
        week, day = normalize_number(str(header.get("week"))), normalize_number(str(header.get("day")))
        if week is None or day is None:
            raise ImportError_(f"Page {page_number} has an unreadable unit header: {header!r}")
        if day == EXERCISE_DAY:
            continue
        for block in page.get("blocks") or []:
            if not isinstance(block, dict) or block.get("type") != "entry":
                continue
            collected.append(
                {
                    "block": block,
                    "page": page_number,
                    "unitId": unit_id(week, day),
                    "blocked": page_number in blocked_pages,
                    "issues": [issue for issue in page.get("issues") or [] if issue.get("blockId") == block.get("id")],
                }
            )

    anchors = [str(item["block"].get("sourceAnchor") or item["block"].get("id")) for item in collected]
    keys, unregistered = resolve_keys(registry, anchors, accept_new=accept_new_keys)
    if unregistered:
        raise ImportError_(
            f"{len(unregistered)} entries have no frozen entryKey, e.g. {unregistered[:5]}.\n"
            "Re-run with --accept-new-keys only when these really are new entries, and review the "
            "entry-keys.json diff. If an existing entry merely moved, repoint its sourceAnchor instead."
        )

    entries: list[dict[str, Any]] = []
    connection_errors: list[str] = []
    for item in collected:
        if item["blocked"]:
            continue
        block = item["block"]
        anchor = str(block.get("sourceAnchor") or block.get("id"))
        try:
            entry = _entry_from_block(block, keys[anchor], item["unitId"], item["page"], meta)
        except ConnectionError_ as exc:
            connection_errors.append(f"{block.get('id')}: {exc}")
            continue
        entries.append(entry)

    if connection_errors:
        raise ImportError_(
            "Connections that the book's legend does not define:\n  "
            + "\n  ".join(connection_errors)
            + "\nFix the abbreviation in pages/, or add it to lexicon_schema.CONNECTION_FORMS "
            "if the book really prints it."
        )

    by_unit: dict[str, list[str]] = {}
    for entry in entries:
        by_unit.setdefault(str(entry.pop("_unitId")), []).append(str(entry["entryKey"]))

    pack_units = [
        {
            "unitId": unit["unitId"],
            "label": unit["label"],
            "title": unit["title"],
            "entryIds": by_unit.get(unit["unitId"], []),
        }
        for unit in units
    ]

    pack = prepare_pack(
        {
            "packId": pack_id,
            "kind": str(meta.get("kind") or "grammar"),
            "level": str(meta.get("level") or ""),
            "title": str(meta.get("title") or ""),
            "attribution": meta.get("attribution") or {},
            "dictionary": meta.get("dictionary"),
            "units": pack_units,
            "entries": entries,
        }
    )

    report = _reconcile(pack, units, collected, blocked_pages)
    return pack, report


def _entry_from_block(
    block: dict[str, Any],
    entry_key: str,
    unit: str,
    page: int,
    meta: dict[str, Any],
) -> dict[str, Any]:
    connection = [item for raw in block.get("connectionRaw") or [] for item in parse_connection_line(raw)]
    examples = []
    for index, example in enumerate(block.get("examples") or []):
        if not isinstance(example, dict):
            continue
        example_id = str(example.get("exampleId") or f"ex{index + 1}")
        if not SLUG_PATTERN.fullmatch(example_id):
            example_id = f"ex{index + 1}"
        japanese = str(example.get("ja") or "")
        built = {
            "exampleId": example_id,
            "ja": japanese,
            "zh": str(example.get("zh") or ""),
            "en": str(example.get("en") or ""),
            "ko": str(example.get("ko") or ""),
            "paraphrase": str(example.get("paraphrase") or ""),
        }
        # A reading only travels when the page file says where it came from. Readings
        # the OCR guessed are not carried forward under any circumstances.
        if example.get("reading") and str(example.get("readingSource") or "") in {"dictionary", "manual"}:
            built["reading"] = str(example["reading"])
            built["readingSource"] = str(example["readingSource"])
        marked = mark_cloze(japanese, str(block.get("headword") or ""))
        if marked:
            built["markedJa"] = marked
        examples.append(built)

    entry: dict[str, Any] = {
        "entryKey": entry_key,
        "kind": str(meta.get("kind") or "grammar"),
        "level": str(meta.get("level") or ""),
        "headword": str(block.get("headword") or "").strip(),
        "unitId": unit,
        "gloss": {
            language: str(value)
            for language, value in (block.get("gloss") or {}).items()
            if str(value or "").strip()
        },
        "examples": examples,
        "source": {"pdfPages": [page], "blockIds": [str(block.get("id") or "")]},
        "flags": [
            {"severity": "warning", "code": str(issue.get("code") or ""), "message": str(issue.get("message") or "")}
            for issue in block.get("flags") or []
        ],
        "_unitId": unit,
    }
    if entry["kind"] == "grammar":
        entry["grammar"] = {
            "connection": [{key: value for key, value in item.items() if key != "tail"} for item in connection],
            "notes": "\n".join(str(note) for note in block.get("notes") or []),
            "confusables": list(block.get("confusables") or []),
        }
    entry["cardTemplates"] = default_card_templates(entry)
    for example in entry["examples"]:
        example.pop("markedJa", None)
    return entry


def mark_cloze(sentence: str, headword: str) -> str:
    """Blank out the pattern inside an example, or return ``""`` if it cannot be found.

    A grammar card is worth having only if the blank lands on the pattern being taught.
    When the printed sentence uses a variant the headword does not literally contain, no
    cloze is produced and the entry ships with its ``recall`` card alone — an entry with
    a blank in the wrong place teaches the wrong thing more effectively than no card.
    """
    core = re.sub(r"[〜～~（）()]", "", str(headword or "")).strip()
    if not core or len(core) < 2:
        return ""
    index = str(sentence or "").find(core)
    if index < 0:
        return ""
    return f"{sentence[:index]}⟦{core}⟧{sentence[index + len(core):]}"


def _reconcile(
    pack: dict[str, Any],
    units: list[dict[str, Any]],
    collected: list[dict[str, Any]],
    blocked_pages: set[int],
) -> dict[str, Any]:
    """Compare what was assembled against what the printed 目次 says exists.

    Trap 2, and the reason this returns rows rather than a boolean: an off-by-one in one
    unit and a whole missing unit are different failures with different fixes.
    """
    actual = {str(unit["unitId"]): len(unit.get("entryIds") or []) for unit in pack.get("units") or []}
    rows: list[dict[str, Any]] = []
    for unit in units:
        expected = int(unit["expectedEntries"])
        found = actual.get(unit["unitId"], 0)
        rows.append(
            {
                "unitId": unit["unitId"],
                "label": unit["label"],
                "expected": expected,
                "found": found,
                "ok": expected == found,
            }
        )

    extra = sorted(set(actual) - {unit["unitId"] for unit in units})
    mismatched = [row for row in rows if not row["ok"]]
    return {
        "schemaVersion": 1,
        "packId": pack.get("packId"),
        "contentRevision": pack.get("contentRevision"),
        "entries": pack.get("entryCount"),
        "unitsExpected": len(units),
        "unitsAssembled": len(actual),
        "blockedPages": sorted(blocked_pages),
        "blockedEntries": sum(1 for item in collected if item["blocked"]),
        "unitsNotInLedger": extra,
        "mismatched": mismatched,
        "ok": not mismatched and not extra and not blocked_pages,
    }


def format_reconciliation(report: dict[str, Any]) -> str:
    lines = [
        f"  units    : {report['unitsAssembled']} assembled / {report['unitsExpected']} in units.txt",
        f"  entries  : {report['entries']}",
    ]
    if report["blockedPages"]:
        lines.append(
            f"  blocked  : {report['blockedEntries']} entries on pages {report['blockedPages']} "
            "(those pages still carry error-level issues)"
        )
    for row in report["mismatched"]:
        lines.append(f"    {row['unitId']:<8} {row['label']}: 目次 says {row['expected']}, assembled {row['found']}")
    for unit in report["unitsNotInLedger"]:
        lines.append(f"    {unit:<8} assembled but not listed in units.txt")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_audit(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"  status   : {report['status']}")
    print(f"  entries  : {summary['entries']}   units: {summary['units']}")
    print(f"  errors   : {summary['errors']}   warnings: {summary['warnings']}")
    for issue in report["issues"][:80]:
        ref = f" [{issue['ref']}]" if issue.get("ref") else ""
        print(f"    {issue['severity']:<7} {issue['code']}{ref}: {issue['message']}")
    if len(report["issues"]) > 80:
        print(f"    … {len(report['issues']) - 80} more")


def _write_pages(pages: Iterable[dict[str, Any]], out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for page in pages:
        path = out_dir / f"p{int(page['page']):04d}.json"
        path.write_text(json.dumps(page, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    extract = commands.add_parser("extract", help="OCR document.json → pages/p<NNNN>.json")
    extract.add_argument("--document", required=True, type=Path)
    extract.add_argument("--out", required=True, type=Path, help="the pack directory")
    extract.add_argument("--kind", choices=["grammar", "word"], default="grammar")
    extract.add_argument("--force", action="store_true", help="overwrite pages that were edited by hand")

    assemble = commands.add_parser("assemble", help="pages + units.txt + entry-keys.json → pack.json")
    assemble.add_argument("--pack", required=True, type=Path, help="the pack directory")
    assemble.add_argument("--accept-new-keys", action="store_true", help="mint entryKeys for new anchors")
    assemble.add_argument("--allow-failed-audit", action="store_true", help="write despite audit errors (inspection)")

    validate = commands.add_parser("validate", help="audit an assembled pack.json")
    validate.add_argument("--pack", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.command == "extract":
        document = json.loads(args.document.read_text(encoding="utf-8"))
        pages = extract_pages(document, kind=args.kind)
        out_dir = args.out / "pages"
        if out_dir.exists() and any(out_dir.glob("p*.json")) and not args.force:
            print(
                f"{out_dir} already holds page files. They are the human-editable source of "
                "truth, so extract will not overwrite them; pass --force if that is what you want.",
                file=sys.stderr,
            )
            return 1
        written = _write_pages(pages, out_dir)
        errors = sum(
            1 for page in pages for issue in page["issues"] if issue.get("severity") == "error"
        )
        warnings = sum(
            1 for page in pages for issue in page["issues"] if issue.get("severity") == "warning"
        )
        entries = sum(1 for page in pages for block in page["blocks"] if block.get("type") == "entry")
        print(f"Wrote {written} page files into {out_dir}")
        print(f"  entry blocks: {entries}")
        print(f"  issues      : {errors} errors, {warnings} warnings")
        print("  Entries on a page with an error-level issue will not reach pack.json until it is resolved.")
        return 0

    if args.command == "assemble":
        pack_dir: Path = args.pack
        registry_path = pack_dir / "entry-keys.json"
        try:
            meta = json.loads((pack_dir / "pack-meta.json").read_text(encoding="utf-8"))
            units = parse_units_file((pack_dir / "units.txt").read_text(encoding="utf-8"))
            registry = load_registry(registry_path, str(meta.get("packId") or ""))
            pages = load_pages(pack_dir / "pages")
            pack, reconciliation = assemble_pack(
                pages, units, registry, meta, accept_new_keys=args.accept_new_keys
            )
            supplement_path = pack_dir / "learning-supplement.json"
            if supplement_path.exists():
                from lexicon_content import supplement_pack
                pack = supplement_pack(pack, json.loads(supplement_path.read_text(encoding="utf-8")))
            # Supplementing changes the pack, and therefore its revision. Stamping the
            # report before that is how the shipped grammar pack ended up carrying a
            # report for a revision it no longer is (LEX-14, §2.2).
            reconciliation["contentRevision"] = pack["contentRevision"]
        except ImportError_ as exc:
            # Every refusal in this pipeline names what to do next, so it prints as a
            # message rather than as a traceback with the message buried in it.
            print(f"\n{exc}", file=sys.stderr)
            return 1
        except FileNotFoundError as exc:
            print(f"\nMissing input: {exc.filename}", file=sys.stderr)
            return 1

        # The registry is source data and is written first: a failure after this point
        # must not let the next run hand an existing key to a different entry.
        save_registry(registry_path, registry)

        print(f"Assembled {pack['entryCount']} entries in {pack['unitCount']} units.")
        print(format_reconciliation(reconciliation))
        audit = audit_pack(pack)
        _print_audit(audit)

        if not reconciliation["ok"]:
            print(
                "\nRefusing to write a pack that does not match the printed 目次. A unit that is "
                "short by one entry is a block OCR dropped, and a learner cannot discover which "
                "half of a grammar table is missing.",
                file=sys.stderr,
            )
            return 1
        if audit["summary"]["errors"] and not args.allow_failed_audit:
            print(
                "\nRefusing to write a pack that failed its audit. Fix pages/, or pass "
                "--allow-failed-audit to inspect the result.",
                file=sys.stderr,
            )
            return 1
        # One publish unit: the pack and everything describing it, or neither. A plain
        # `write_text` also truncates in place, so an interrupted write left a pack that
        # could not be parsed at all (§6.5).
        from lexicon_schema import publish_pack
        publish_pack(pack_dir, {
            "pack.json": pack,
            "match-report.json": reconciliation,
            "quality-report.json": {"contentRevision": pack["contentRevision"], **audit},
        }, revision=pack["contentRevision"])
        print(f"\nWrote {pack_dir / 'pack.json'}  (contentRevision {pack['contentRevision'][:16]}…)")
        print(f"Reports published at the same revision; manifest in {pack_dir / 'publish.json'}")
        return 0

    if args.command == "validate":
        path = args.pack if args.pack.is_file() else args.pack / "pack.json"
        pack = json.loads(path.read_text(encoding="utf-8"))
        report = audit_pack(pack)
        _print_audit(report)
        return 1 if report["summary"]["errors"] else 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
