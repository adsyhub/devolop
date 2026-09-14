"""dots.ocr backend -- 1.7B model built specifically for document parsing.

Returns a JSON array of layout elements (bbox + category + text) rather than a
wall of Markdown, so headers/footers/tables stay separable downstream. Needs
``trust_remote_code``; we force SDPA attention because flash-attn has no Windows
wheels.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from PIL import Image

from .base import PageResult, SequentialBatchMixin

_CATEGORY_PREFIX = {
    "Title": "# ",
    "Section-header": "## ",
    "List-item": "- ",
}


def _blocks_to_markdown(blocks: list[dict]) -> str:
    lines: list[str] = []
    for block in blocks:
        category = block.get("category", "Text")
        text = (block.get("text") or "").strip()
        if category == "Picture":
            lines.append("![](figure)")
            continue
        if not text:
            continue
        if category in ("Page-header", "Page-footer"):
            tag = "header" if category == "Page-header" else "footer"
            lines.append(f"<!-- {tag}: {text} -->")
            continue
        if category == "Formula":
            lines.append(f"$$\n{text}\n$$")
            continue
        lines.append(_CATEGORY_PREFIX.get(category, "") + text)
    return "\n\n".join(lines)


def _parse_layout_json(raw: str) -> list[dict]:
    """dots.ocr returns a JSON array, sometimes wrapped in a code fence."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        return []
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return [b for b in parsed if isinstance(b, dict)]


class DotsOcrBackend(SequentialBatchMixin):
    name = "dots-ocr"

    def __init__(
        self,
        model_id: str = "rednote-hilab/dots.ocr",
        *,
        device: str = "cuda",
        dtype: str = "bfloat16",
        max_new_tokens: int = 8192,
        attn: str = "sdpa",
        **_ignored,
    ) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor

        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self._torch = torch

        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=getattr(torch, dtype),
            attn_implementation=attn,
            device_map=device,
            trust_remote_code=True,
        )
        self.model.eval()
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        self.device = str(self.model.device)

    def describe(self) -> dict:
        return {
            "backend": self.name,
            "model_id": self.model_id,
            "device": self.device,
            "max_new_tokens": self.max_new_tokens,
        }

    def transcribe(self, image_path: Path, *, prompt: str) -> PageResult:
        page = int(image_path.stem.split("-")[-1])
        started = time.perf_counter()
        try:
            with Image.open(image_path) as raw:
                image = raw.convert("RGB")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": str(image_path)},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.processor(
                text=[text], images=[image], return_tensors="pt", padding=True
            ).to(self.model.device)

            with self._torch.inference_mode():
                generated = self.model.generate(
                    **inputs, max_new_tokens=self.max_new_tokens, do_sample=False
                )
            trimmed = generated[0][inputs.input_ids.shape[1] :]
            out = self.processor.decode(trimmed, skip_special_tokens=True)

            blocks = _parse_layout_json(out)
            markdown = _blocks_to_markdown(blocks) if blocks else out.strip()
            return PageResult(
                page=page,
                markdown=markdown,
                blocks=blocks,
                seconds=time.perf_counter() - started,
            )
        except Exception as exc:
            return PageResult(
                page=page,
                markdown="",
                seconds=time.perf_counter() - started,
                error=f"{type(exc).__name__}: {exc}",
            )
