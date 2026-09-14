"""Strict prompts for OpenAI-compatible local vision providers."""

from __future__ import annotations

import json
from typing import Any
from .constants import PAGE_CONTRACT_VERSION


def page_prompt(manifest: dict[str, Any], *, page: int, role: str) -> str:
    subject = manifest.get("subject")
    form_codes = {
        "SCIENCE": ["PHYSICS_JA", "CHEMISTRY_JA", "BIOLOGY_JA"],
        "MATHEMATICS": ["MATHEMATICS_COURSE_1_JA", "MATHEMATICS_COURSE_2_JA"],
        "JAPAN_AND_WORLD": ["JAPAN_AND_WORLD_JA"],
        "JAPANESE": ["JAPANESE_JA"],
    }.get(str(subject), [])
    if manifest.get("language") == "en":
        form_codes = [code.replace("_JA", "_EN") for code in form_codes]
    skeleton = {
        "schemaVersion": PAGE_CONTRACT_VERSION,
        "page": page,
        "sourceFileRole": role,
        "blocks": [],
        "coverage": {"inkRegions": 0, "accountedRegions": 0, "regionIds": [], "accountedRegionIds": []},
        "issues": [],
    }
    return f"""You are an EJU examination transcription engine.

Input: all images are overlapping views of page {page} from role {role}.
Source subject: {subject}. Allowed form codes: {json.dumps(form_codes, ensure_ascii=False)}.

Return exactly one JSON object matching this skeleton:
{json.dumps(skeleton, ensure_ascii=False)}

Block kinds:
- material: localKey, contentAst, bbox
- question: localKey, formCode, sectionCode, groupCode, printedLabel,
  answerRef, stemAst, options, answerSpec, materialRefs, bbox
- writing-prompt: same as question but answerSpec.type is ESSAY
- answer-entry: formCode, answerRef, answerType and either correctOption or tokens, bbox
- instruction or ignored: contentAst/reason and bbox

AST nodes use text/value, inlineMath/latex, displayMath/latex, table/rows,
figure/sourceBbox, answerSlot/slot, or lineBreak. Every bbox is normalized
[x0,y0,x1,y1] relative to the full page, not a tile.

Rules:
1. Transcribe verbatim. Never translate, solve, correct, infer an answer, or fill unreadable text.
2. Preserve every exponent, subscript, sign, unit, fraction and radical in LaTeX.
3. Preserve every non-text visual that is needed to answer the question as a figure node with an
   exact sourceBbox. This includes diagrams, graphs, coordinate plots, geometry drawings,
   circuit/experimental apparatus, chemical structures, maps, photographs, and image-based
   answer options. Never replace a visual with a text description. Transcribe its printed labels
   as well, but keep the figure node so a lossless crop can be generated for the learner UI.
4. Associate each figure with the material, stem, or individual option where it appears; do not
   collapse several option images into one figure unless the printed page presents them as one panel.
5. EJU science options are variable-count; include every printed option and its printed key.
6. When role is ANSWER_KEY: you MUST extract each answer item as an "answer-entry" block (with formCode, answerRef, answerType and either correctOption or tokens, bbox). Do NOT create question or material blocks on ANSWER_KEY pages.
   When role is QUESTION_BOOKLET: transcribe questions and materials. A QUESTION_BOOKLET page must NOT contain answer-entry blocks.
7. For ANSWER_KEY, emit only answer-entry blocks belonging to source subject {subject}; ignore other subjects.
8. A repeated question/material across overlapping images is one block, never duplicated.
9. Assign a stable descriptive localKey; repeated material continuations reuse the same localKey.
10. Set coverage inkRegions to the number of meaningful regions and accountedRegions to the
   number represented by blocks. Give every region a stable regionId and every block its
   regionIds list. coverage.regionIds must equal the disjoint union of block.regionIds;
   coverage.accountedRegionIds lists the processed regions. Do not claim full coverage when something is unreadable;
   record it in issues.
11. Output JSON only, with no code fence or explanation.
"""
