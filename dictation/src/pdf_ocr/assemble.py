"""Page results -> document.md, document.json, and a quality report.

Two consumers are in mind: a human skimming the Markdown, and a language model
reading the JSON. The JSON therefore carries per-page provenance (which model,
how long, what went wrong) so a later pass can re-OCR only the bad pages.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from .backends.base import PageResult

HEADER_RE = re.compile(r"^<!--\s*(header|footer):.*?-->\s*$", re.M)
BLANK_MARKER = "<!-- blank page -->"
FENCE_RE = re.compile(r"^\s*```(?:markdown|md)?\s*\n(.*)\n\s*```\s*$", re.S)
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
OPEN_THINK_RE = re.compile(r"<think>.*\Z", re.S)
BOX_TOKEN_RE = re.compile(r"<\|(?:begin|end)_of_box\|>")


def _strip_wrapping_fence(text: str) -> str:
    """Models sometimes wrap the whole page in one code fence despite the prompt."""
    match = FENCE_RE.match(text)
    return match.group(1) if match else text


def _strip_control_tokens(text: str) -> str:
    """Drop a reasoning VLM's scaffolding so it cannot be mistaken for page text.

    GLM-OCR (and any reasoning model served raw over an OpenAI-compatible port)
    emits ``<think>...</think>`` before the transcription and wraps the answer in
    ``<|begin_of_box|>...<|end_of_box|>``. Left in place that scaffolding is
    counted as page content, which breaks the very checks meant to catch a bad
    page: a blank page whose only real output is ``<!-- blank page -->`` arrives
    with 330 characters, so neither the blank marker nor the ``very-short`` flag
    fires, and ``_repetition_ratio`` scores English prose instead of the page.

    An *unclosed* ``<think>`` is the case worth being strict about: the model ran
    out of tokens while reasoning and never transcribed anything. Removing it
    leaves the page empty, which is what actually happened, and ``page_report``
    then flags it ``empty`` so ``--retry-flagged`` picks it up. Keeping the
    reasoning would hide a lost page behind plausible-looking text.
    """
    text = THINK_RE.sub("", text)
    text = OPEN_THINK_RE.sub("", text)
    return BOX_TOKEN_RE.sub("", text)


def _repetition_ratio(text: str) -> float:
    """Fraction of the text taken up by one immediately-repeated chunk.

    VLMs degenerate on dense pages by looping a phrase to the token limit. A high
    ratio here is the cheapest reliable signal that a page needs a retry.
    """
    stripped = re.sub(r"\s+", "", text)
    if len(stripped) < 80:
        return 0.0
    for size in range(4, 61):
        chunk = stripped[-size:]
        repeats = 0
        pos = len(stripped)
        while pos >= size and stripped[pos - size : pos] == chunk:
            repeats += 1
            pos -= size
        if repeats >= 6:
            return (repeats * size) / len(stripped)
    return 0.0


def _script_counts(text: str) -> dict:
    kana = han = latin = 0
    for ch in text:
        code = ord(ch)
        if 0x3040 <= code <= 0x30FF:
            kana += 1
        elif 0x4E00 <= code <= 0x9FFF:
            han += 1
        elif ch.isascii() and ch.isalpha():
            latin += 1
    return {"kana": kana, "han": han, "latin": latin}


_KANA_ONLY = re.compile(r"^[぀-ゟ゠-ヿ\s]+$")  # hiragana, katakana, ー
_HAS_KANJI = re.compile(r"[一-鿿]")


def _is_ruby_dump(line: str, previous: str) -> bool:
    """Is this line stranded furigana rather than real kana text?

    At the resolutions a 24 GB card can afford, the model half-sees the ruby
    printed over each kanji and emits it as its own line under the base text
    (``この本の使い方`` followed by ``ほんつかかた``). Two signals separate that
    from a genuine kana-only sentence: a real sentence carries punctuation, and
    stranded ruby always trails a line that had kanji in it to annotate.
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return False
    if not _KANA_ONLY.match(stripped):
        return False
    return bool(_HAS_KANJI.search(previous))


def mark_ruby_lines(markdown: str) -> str:
    """Wrap stranded furigana lines in a comment instead of deleting them.

    Non-destructive on purpose: the reading is still there for anything that
    wants it, but a reader (human or model) can skip the whole line.
    """
    out: list[str] = []
    previous = ""
    for line in markdown.split("\n"):
        if _is_ruby_dump(line, previous):
            out.append(f"<!-- ruby: {line.strip()} -->")
            continue
        if line.strip():
            previous = line
        out.append(line)
    return "\n".join(out)


def clean_page(
    markdown: str, *, drop_running_heads: bool = False, mark_ruby: bool = False
) -> str:
    text = unicodedata.normalize("NFC", markdown).strip()
    text = _strip_control_tokens(text).strip()
    text = _strip_wrapping_fence(text).strip()
    if mark_ruby:
        text = mark_ruby_lines(text)
    if drop_running_heads:
        text = HEADER_RE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def classify_page_type(cleaned: str, page_num: int = 1) -> str:
    """Classify page into one of: blank, cover, toc, content, index, exercise, answers, empty."""
    if cleaned == BLANK_MARKER:
        return "blank"
    if not cleaned or not cleaned.strip():
        return "empty"
    if page_num == 1 and len(cleaned.strip()) < 200:
        return "cover"
    norm = unicodedata.normalize("NFKC", cleaned)
    if re.search(r"(?:^|\n)\s*#*\s*(?:正解(?:一覧)?|解答(?:\s*と\s*解説)?|Answers|Answer\s*Key)", norm, re.I):
        return "answers"
    if re.search(r"(?:^|\n)\s*#*\s*(?:目次|目\s*録|目\s*录|CONTENTS|Table\s*of\s*Contents)", norm, re.I):
        return "toc"
    if re.search(r"(?:^|\n)\s*#*\s*(?:索引|INDEX|五十音順|さくいん)", norm, re.I):
        return "index"
    if re.search(r"(?:^|\n)\s*#*\s*(?:練習問題|実力養成|模擬試験|ドリル|CHECK|復習テスト)", norm, re.I):
        return "exercise"
    return "content"


def page_report(result: PageResult, cleaned: str) -> dict:
    counts = _script_counts(cleaned)
    repetition = _repetition_ratio(cleaned)
    ptype = classify_page_type(cleaned, result.page)
    flags = []
    if result.error:
        flags.append("error")
    if not result.error and not cleaned:
        flags.append("empty")
    if repetition > 0.25:
        flags.append("repetition-loop")
    if cleaned and cleaned != BLANK_MARKER and len(cleaned) < 40 and ptype not in ("blank", "cover"):
        flags.append("very-short")
    return {
        "page": result.page,
        "pageType": ptype,
        "chars": len(cleaned),
        "seconds": round(result.seconds, 2),
        "scripts": counts,
        "repetition_ratio": round(repetition, 3),
        "flags": flags,
        "error": result.error,
        "backend": result.backend,
    }


def write_outputs(
    out_dir: Path,
    results: list[PageResult],
    *,
    source: dict,
    backend: dict,
    drop_running_heads: bool = False,
    mark_ruby: bool = False,
    boxes: dict[int, str] | None = None,
) -> dict:
    """Write document.md / document.json / quality-report.json. Returns the report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    results = sorted(results, key=lambda r: r.page)

    pages_json = []
    md_parts = []
    reports = []
    for result in results:
        cleaned = clean_page(
            result.markdown, drop_running_heads=drop_running_heads, mark_ruby=mark_ruby
        )
        box = (boxes or {}).get(result.page)
        cleaned = merge_box(cleaned, box)
        report_row = page_report(result, cleaned)
        if box and box.strip() not in ("", NO_BOX_MARKER):
            if box_is_degenerate(box):
                report_row["flags"] = report_row["flags"] + ["box-degenerate"]
            elif box_is_suspicious(box):
                report_row["flags"] = report_row["flags"] + ["box-suspicious"]
        reports.append(report_row)
        pages_json.append(
            {
                "page": result.page,
                "pageType": report_row["pageType"],
                "markdown": cleaned,
                "box": box,
                "blocks": result.blocks,
                "seconds": round(result.seconds, 2),
                "error": result.error,
                "backend": result.backend,
            }
        )
        body = cleaned if cleaned else "<!-- no text recovered -->"
        md_parts.append(f"<!-- page: {result.page} -->\n\n{body}")

    document_md = "\n\n---\n\n".join(md_parts) + "\n"
    (out_dir / "document.md").write_text(document_md, encoding="utf-8")

    flagged = [r for r in reports if r["flags"]]
    total_chars = sum(r["chars"] for r in reports)
    report = {
        "source": source,
        "backend": backend,
        "pages_transcribed": len(results),
        "total_chars": total_chars,
        "mean_chars_per_page": round(total_chars / max(len(results), 1), 1),
        "total_seconds": round(sum(r["seconds"] for r in reports), 1),
        "flagged_pages": [r["page"] for r in flagged],
        "page_types": {r["page"]: r.get("pageType", "content") for r in reports},
        "pages": reports,
    }

    (out_dir / "document.json").write_text(
        json.dumps(
            {"source": source, "backend": backend, "pages": pages_json},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "quality-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


BOX_MARKER = "<!-- box -->"


def box_is_suspicious(box: str) -> bool:
    """Does this look like over-capture rather than a connection chart?

    A real chart is a stack of short stems (``Nに``, ``Vるに``, ``基づいて``).
    When the crop holds no box, the model tends to dump fragments of body text
    instead -- long, prose-like lines. Length is the cheapest separator.
    """
    lines = [ln.lstrip("> ").strip() for ln in box.split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines:
        return False
    if len(box) > 600:
        return True
    long_lines = sum(1 for ln in lines if len(ln) > 30)
    return long_lines >= 3


def box_is_degenerate(box: str) -> bool:
    """Did the box read collapse into a decoding loop?

    A connection chart brackets several endings onto one stem, and that bracket
    glyph sits on a knife-edge for greedy decoding: the model either reads the
    branches or latches on and repeats to the token limit. bf16 + SDPA is not
    bitwise reproducible across call shapes, so the same crop can go either way
    between runs -- which is why this is checked at merge time and not only when
    the text was generated.
    """
    return _repetition_ratio(box) > 0.25


def merge_box(markdown: str, box: str | None) -> str:
    """Append recovered box content to a page, clearly marked as its own block.

    A degenerate read is dropped rather than merged: appending a loop would
    corrupt a page whose body text is perfectly good.
    """
    if not box:
        return markdown
    body = box.strip()
    if not body or body == NO_BOX_MARKER or box_is_degenerate(body):
        return markdown
    return f"{markdown}\n\n{BOX_MARKER}\n{body}" if markdown else f"{BOX_MARKER}\n{body}"


NO_BOX_MARKER = "<!-- no box -->"
