"""Transcription prompts.

Tuned on the actual target: JLPT preparation books published in Japan. A single
page mixes Japanese (with furigana ruby over nearly every kanji), English,
Simplified Chinese and Korean glosses, boxed grammar panels, numbered drills with
fill-in blanks, and an answer strip. Two failure modes dominate if you just ask a
VLM to "read the page":

* it translates instead of transcribing -- Japanese silently comes back as
  Chinese, destroying exactly what we wanted to capture;
* it drops or inlines furigana inconsistently, so half the readings vanish.

Both are addressed explicitly below.
"""

from __future__ import annotations

_FURIGANA_INLINE = """\
- Furigana (the small kana printed above or below a kanji) is data, not
  decoration. Put it in parentheses immediately after its kanji group:
  北(きた)へ行(い)く. If a word has no furigana printed, add none -- never guess."""

_FURIGANA_DROP = """\
- Furigana (the small kana printed above or below a kanji) is decoration here:
  skip it entirely and transcribe only the main line of text."""

_BODY = """\
Rules:
- Transcribe EVERY character exactly as printed. Do NOT translate, summarise,
  correct, romanise, or comment. This page mixes Japanese, English, Chinese and
  Korean: each block stays in the language it was printed in.
{furigana}
- Reading order is the order a human reads: finish a block before moving on.
  A block set vertically (縦書き) reads top-to-bottom, right-to-left; emit it as
  ordinary horizontal lines.
- Headings and grammar-point titles -> `##`. Keep bracket forms as printed:
  《》「」『』【】（）〜.
- Keep printed list markers exactly: ①②③④⑤, 1. 2., (1), a. b., ・.
- Transcribe EVERY block on the page, including ones set beside or around the
  main text: boxed grammar-connection panels, margin notes, vertical side tabs,
  and the answer strip. Skipping a side panel because the body text reads fine
  without it is the single most common failure -- do not do it.
- A boxed panel -> a Markdown blockquote, each line prefixed with `> `, placed at
  the point in the reading order where it appears.
- Fill-in-the-blank rules or boxes -> `____` (four underscores). Underlined words
  stay plain text; do not mark them up.
- Tables -> GitHub Markdown tables, every cell preserved, empty cells left empty.
- The page number, running head, side tab, and the answer strip at the foot of
  the page each go on their own line wrapped in an HTML comment:
  `<!-- footer: ... -->` for anything at the bottom or in the margin,
  `<!-- header: ... -->` for anything above the body text.
- Illustrations/photos -> `![](figure)` on its own line. Invent no caption, but
  do transcribe any text printed inside the figure.
- If the page carries no text at all, output exactly: <!-- blank page -->

Output only the Markdown for this page. No preamble, no explanation, and do not
wrap the whole page in a code fence."""

_HEAD = "You are a document transcription engine. Transcribe this scanned page into Markdown.\n\n"

JA_DOC_PROMPT = _HEAD + _BODY.format(furigana=_FURIGANA_INLINE)
JA_DOC_PROMPT_NO_RUBY = _HEAD + _BODY.format(furigana=_FURIGANA_DROP)

JA_LAYOUT_PROMPT = """\
Please output the layout information from the PDF image, including each layout \
element's bbox, its category, and the corresponding text content within the bbox.

1. Bbox format: [x1, y1, x2, y2]
2. Layout Categories: ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', \
'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title']
3. Text Extraction & Formatting Rules:
    - Picture: omit the text field.
    - Formula: LaTeX.
    - Table: HTML.
    - Others: Markdown.
    - Transcribe verbatim and never translate: the page mixes Japanese, English,
      Chinese and Korean. Attach furigana in parentheses after its kanji.
4. Sort the elements into human reading order.
5. Output one JSON array. No extra commentary."""

PROMPTS = {
    "doc": JA_DOC_PROMPT,
    "doc-no-ruby": JA_DOC_PROMPT_NO_RUBY,
    "layout": JA_LAYOUT_PROMPT,
}


def prompt_for(style: str) -> str:
    """Look up a prompt by name; an unknown ``style`` is used as a literal prompt."""
    return PROMPTS.get(style, style)


BOX_PROMPT = """\
This image is the RIGHT-HAND STRIP of a Japanese grammar textbook page, cropped
at full scan resolution.

Transcribe ONLY the content printed inside boxed panels: the dashed or
solid-outlined "connection" charts that show which parts of speech and which
conjugated forms a grammar pattern attaches to. Include whatever else is printed
inside the same box -- labelled examples, a cross-reference to another page, a
marker flagging an incorrect usage.

Ignore everything else on the strip: ordinary body text, example sentences that
are not inside a box, translations, headings, page numbers, running heads and
illustrations.

Rules:
- Transcribe verbatim, exactly what THIS image shows. Never translate. Never
  supply a pattern from memory or from these instructions: if you cannot read
  something, omit it rather than guessing at a plausible grammar point.
- Keep 〜 ・ 「」 （） ＋ / and any arrows or brackets as printed.
- A chart that brackets several endings against one stem keeps every branch, one
  per line, in the printed order.
- Keep the small labels that mark an example or a wrong usage on the line they
  introduce.
- Skip furigana (the tiny kana set beside a kanji); transcribe the main
  characters only.
- Output every line as a SINGLE-level Markdown blockquote, prefixed with exactly
  `> `. Never nest (`> >`).
- Separate two different boxes with one blank line.
- If this strip contains no boxed panel at all, output exactly: <!-- no box -->

Output only the blockquote lines (or the no-box marker). No preamble."""

PROMPTS["box"] = BOX_PROMPT
