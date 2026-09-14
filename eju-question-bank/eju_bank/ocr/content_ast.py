"""Turn what the page parser read into the AST the learning app renders.

Every published question in the bank stores its stem, its options and its
materials as a single ``text`` node — 15,931 of them, and not one ``figure``,
``inlineMath``, ``table``, ``underline`` or ``answerSlot`` (审计 §3.1). The
renderer has supported all of those the whole time; nothing upstream ever built
them. So a formula reached the learner as ``$\\frac{f_1}{f_0}$``, a comparison
grid as ``<td>``, and 「下線部」 pointed at nothing.

This module is the missing step. It is deliberately a *transcription*, not an
interpretation: it only promotes markup the OCR actually captured —

``$…$`` / ``$$…$$``   → ``inlineMath`` / ``displayMath``
``\\underline{…}`` / ``<u>…</u>``  → ``underline``
the parser's table rows        → ``table`` with its header flags and spans

Text that carries none of those stays text. Nothing is inferred from context and
nothing is added, so the node tree says exactly as much as the page did.
"""

from __future__ import annotations

import re
from typing import Any

# $$…$$ 先于 $…$，否则行间公式会被读成两个空的行内公式。
# \underline{...} 与 <u>...</u> 是原卷下線部在 OCR 里仅有的两种留痕。
_INLINE = re.compile(
    r"\$\$(?P<display>.+?)\$\$"
    r"|\$(?P<inline>[^$]+?)\$"
    r"|\\underline\s*\{(?P<underline>[^{}]*)\}"
    r"|<u\b[^>]*>(?P<utag>.*?)</u>",
    re.S | re.I)

_UNDERLINE_HINT = re.compile(r"下線部|傍線部|下線を引いた|下線が引かれ")


def has_underline_reference(text: str) -> bool:
    """Does this text point at an underline the reader has to be able to see?

    229 questions say 「下線部(1)」 while nothing in their material is underlined
    (审计 F10). The question is unanswerable in that state, so the publish gate
    needs to be able to ask.
    """
    return bool(_UNDERLINE_HINT.search(str(text or "")))


def has_underline_node(nodes: Any) -> bool:
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        if node.get("type") == "underline":
            return True
        if has_underline_node(node.get("children")):
            return True
        if node.get("type") == "table":
            for row in node.get("rows") or []:
                for cell in row:
                    if isinstance(cell, dict) and has_underline_node(cell.get("contentAst")):
                        return True
    return False


def text_nodes(text: str) -> list[dict[str, Any]]:
    """One run of prose as inline nodes, with its markup promoted.

    Emitted as a flat run of spans rather than a nested paragraph, because the
    renderer appends a node's children *after* it rather than inside it — a
    formula hung off a paragraph would land on the next line.
    """
    source = str(text or "")
    nodes: list[dict[str, Any]] = []
    position = 0

    def plain(chunk: str) -> None:
        if chunk.strip():
            nodes.append({"type": "text", "value": chunk})

    for match in _INLINE.finditer(source):
        plain(source[position:match.start()])
        position = match.end()
        if (latex := match.group("display")) is not None:
            if latex.strip():
                nodes.append({"type": "displayMath", "latex": latex.strip()})
        elif (latex := match.group("inline")) is not None:
            # 「1ドル＝100円」这种夹在文字里的美元号不是公式。要求里面至少有一个
            # LaTeX 命令、上下标或运算符，才当它是数学。
            if _looks_like_math(latex):
                nodes.append({"type": "inlineMath", "latex": latex.strip()})
            else:
                plain(f"${latex}$")
        else:
            value = (match.group("underline") if match.group("underline") is not None
                     else match.group("utag"))
            if str(value).strip():
                nodes.append({"type": "underline", "value": str(value).strip()})
    plain(source[position:])
    return nodes


_MATHY = re.compile(r"\\[A-Za-z]+|[\^_=+×÷≦≧<>]|\\\\|[0-9]\s*/\s*[0-9]")


def _looks_like_math(latex: str) -> bool:
    return bool(latex.strip()) and bool(_MATHY.search(latex))


def table_node(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """The parser's rows as a ``table`` node, header flags and spans intact."""
    out_rows: list[list[dict[str, Any]]] = []
    for row in rows:
        cells: list[dict[str, Any]] = []
        for cell in row:
            value = str(cell.get("value") or "")
            entry: dict[str, Any] = {"contentAst": text_nodes(value) or
                                     [{"type": "text", "value": value or " "}]}
            for key in ("header", "rowspan", "colspan"):
                if cell.get(key):
                    entry[key] = cell[key]
            cells.append(entry)
        if cells:
            out_rows.append(cells)
    return {"type": "table", "rows": out_rows}


def nodes_from_parts(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The ordered stem/material parts the page parser produced, as an AST.

    Parts are separated by a ``lineBreak`` so the printed paragraphing survives.
    Running them together is what turned a 対話 and its four sub-questions into
    one wall of text (审计 F11).
    """
    nodes: list[dict[str, Any]] = []
    for part in parts or []:
        if part.get("type") == "table":
            nodes.append(table_node(part.get("rows") or []))
            continue
        run = text_nodes(part.get("value") or "")
        if not run:
            continue
        if nodes and nodes[-1].get("type") != "table":
            nodes.append({"type": "lineBreak"})
        nodes.extend(run)
    return nodes


def nodes_from_text(text: str) -> list[dict[str, Any]]:
    """A single string as an AST, for callers that never had ordered parts."""
    return text_nodes(text)
