"""Can this question actually be answered from what is being delivered?

``audit_paper`` asks whether a paper is structurally legal: keys unique, options
numbered, refs resolvable. All 149 practisable papers pass it, and the physics
question with no figure, no given lengths and the wrong answer passes it too
(审计 F21). Structural legality and answerability are different questions and
need different gates; this module is the second one.

It asks only what can be decided from the delivered content itself:

* the stem points at a figure, and no figure was delivered;
* the stem says 「下線部」, and nothing in the material is underlined;
* the stem points at a table, and no table was delivered;
* two choices are indistinguishable, or one of them has no content;
* markup that should have become a node is still sitting in the text —
  a bare ``<td>``, a bare ``$…$``.

Each of those makes the question unanswerable *as delivered*, regardless of how
faithfully the text was transcribed. None of them is a judgement about whether
the transcription is right — that is a different claim, and this module does not
make it.
"""

from __future__ import annotations

import re
from typing import Any

from .content_ast import has_underline_node, has_underline_reference

# 「次の図のように」「図1」「グラフ」「写真」「地図」— 原卷指着一张图说话。
_FIGURE_HINT = re.compile(r"図\s*[0-9１-９]|次の図|上の図|下の図|右の図|左の図"
                          r"|グラフ|写真|模式図|地図|図示|図中|図のよう")
# 「次の表中のA～D」「表1」— 原卷指着一张表说话。
_TABLE_HINT = re.compile(r"表\s*[0-9１-９]|次の表|上の表|下の表|表中|表のよう")
# 交付文本里不该再出现的生产残留。
_HTML_LEFTOVER = re.compile(r"<\s*/?\s*(?:table|thead|tbody|tr|td|th|br|u)\b", re.I)
_LATEX_LEFTOVER = re.compile(r"\$[^$]*\\[A-Za-z]+[^$]*\$|\\(?:frac|sqrt|textcircled|begin)\b")


def _walk(nodes: Any):
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        yield node
        yield from _walk(node.get("children"))
        for row in node.get("rows") or []:
            for cell in row:
                if isinstance(cell, dict):
                    yield from _walk(cell.get("contentAst"))


def node_types(nodes: Any) -> set[str]:
    return {str(node.get("type")) for node in _walk(nodes)}


_PROSE = {"text", "paragraph", "callout", "underline"}


def plain_text(nodes: Any) -> str:
    """The prose a reader would see.

    Formula nodes are left out on purpose: their LaTeX is the node's content,
    not leftover source, and counting it as prose would make every correctly
    built formula look like the thing this module is trying to catch.
    """
    return " ".join(str(node.get("value") or "")
                    for node in _walk(nodes) if node.get("type") in _PROSE)


def unanswerable_reasons(
    *,
    stem: list[dict[str, Any]],
    options: dict[str, list[dict[str, Any]]] | None = None,
    materials: list[dict[str, Any]] | None = None,
    has_figure_asset: bool = False,
) -> list[str]:
    """Why this question cannot be answered from what is delivered. Empty is good."""
    reasons: list[str] = []
    every = list(stem) + list(materials or [])
    for nodes in (options or {}).values():
        every += list(nodes)
    types = node_types(every)
    visible = plain_text(list(stem) + list(materials or []))

    if _FIGURE_HINT.search(visible) and "figure" not in types and not has_figure_asset:
        reasons.append("题面指着原卷的图说话，但交付内容里没有图")
    if _TABLE_HINT.search(visible) and "table" not in types:
        reasons.append("题面指着原卷的表说话，但交付内容里没有表格节点")
    if has_underline_reference(visible) and not has_underline_node(every):
        reasons.append("题面提到下線部／傍線部，但材料里没有标出对应的下划线")

    seen: dict[str, str] = {}
    for key, nodes in (options or {}).items():
        text = "".join(plain_text(nodes).split())
        if not text:
            reasons.append(f"选项 {key} 没有可读内容")
            continue
        if text in seen:
            reasons.append(f"选项 {seen[text]} 与 {key} 完全相同，无法区分")
        seen[text] = key

    everything = plain_text(every)
    if _HTML_LEFTOVER.search(everything):
        reasons.append("交付文本里还留着 HTML 标签")
    if _LATEX_LEFTOVER.search(everything):
        reasons.append("交付文本里还留着未转成公式节点的 LaTeX 源码")
    return reasons
