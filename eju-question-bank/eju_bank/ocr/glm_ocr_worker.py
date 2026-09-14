"""Dedicated local GLM-OCR worker for high-precision Japanese & formula document extraction.

Loads GLM-OCR (0.9B) on CUDA, extracts structured text, and parses reading passages
into standard EJU question bank AST nodes (paragraph, text, ruby, underline, lineBreak).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_MODEL_DIR = Path("/data/storage/migrated/ecgegg-models/GLM-OCR")


class GlmOcrWorker:
    """Inference engine for GLM-OCR document and reading passage transcription."""

    def __init__(
        self,
        model_path: Path | str | None = None,
        *,
        device: str = "cuda:2",
        torch_dtype: str = "bfloat16",
        cache_dir: Path | str | None = None,
    ) -> None:
        self.model_path = Path(model_path or DEFAULT_MODEL_DIR).resolve()
        self.device = device
        self.torch_dtype = torch_dtype
        self.cache_dir = Path(cache_dir).resolve() if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._model = None
        self._processor = None
        self._torch = None

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._processor is not None:
            return

        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        self._torch = torch
        dtype = getattr(torch, self.torch_dtype, torch.bfloat16)

        # Fallback to cuda:0 if configured device not available
        target_device = self.device
        if target_device.startswith("cuda") and not torch.cuda.is_available():
            target_device = "cpu"
            dtype = torch.float32

        self._processor = AutoProcessor.from_pretrained(str(self.model_path))
        self._model = AutoModelForImageTextToText.from_pretrained(
            str(self.model_path),
            torch_dtype=dtype,
            device_map=target_device,
        )
        self._model.eval()

    def transcribe_image(self, image_path: Path | str, *, task_prompt: str = "Text Recognition:") -> str:
        """Run OCR on a single image file, using cache if available."""
        img_p = Path(image_path).resolve()
        if not img_p.exists():
            raise FileNotFoundError(f"Image not found: {img_p}")

        # Check cache
        cache_file = None
        if self.cache_dir:
            import hashlib
            file_hash = hashlib.sha256(img_p.read_bytes()).hexdigest()
            cache_file = self.cache_dir / f"{file_hash[:2]}" / f"{file_hash}.txt"
            if cache_file.exists():
                return cache_file.read_text(encoding="utf-8")

        self._ensure_loaded()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "url": str(img_p)},
                    {"type": "text", "text": task_prompt},
                ],
            }
        ]

        inputs = self._processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device)
        inputs.pop("token_type_ids", None)

        with self._torch.inference_mode():
            generated_ids = self._model.generate(**inputs, max_new_tokens=4096)

        out_text = self._processor.decode(
            generated_ids[0][inputs["input_ids"].shape[1] :],
            skip_special_tokens=True,
        ).strip()

        # Save to cache
        if cache_file:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(out_text, encoding="utf-8")

        return out_text

    def parse_reading_page(self, raw_text: str) -> dict[str, Any]:
        """Parse raw OCR text into passage text, notes/citation, question stem and options."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            return {"passage_ast": [], "stem": None, "options": []}

        passage_lines: list[str] = []
        options: dict[str, str] = {}
        stem_candidates: list[str] = []

        # Regular expressions for question and option detection
        q_stem_pat = re.compile(
            r"^(?:問\s*[0-9１-９]+|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVXLCDMivxlcdm]+[\s\.\、\:]|[1-9１-９]\s*番|下線部|本文|筆者|次の文章は)",
            re.I,
        )
        opt_pat = re.compile(r"^([1-4１-４])[\.\、\s]\s*(.*)$")

        in_options = False
        for line in lines:
            # Skip page footer e.g. "-43-" or "日本語-12"
            if re.fullmatch(r"^[-ー―\s]*\d+[-ー―\s]*$", line) or re.fullmatch(r"^日本語[-ー―\d\s]+$", line):
                continue

            # Check if option line
            opt_m = opt_pat.match(line)
            if opt_m:
                in_options = True
                key = opt_m.group(1).translate(str.maketrans("１２３４", "1234"))
                options[key] = opt_m.group(2).strip()
                continue

            if in_options:
                # Continuation of last option
                if options:
                    last_k = list(options.keys())[-1]
                    options[last_k] += " " + line
                continue

            # Check if question stem
            if (
                q_stem_pat.match(line)
                or "選べ" in line
                or "答えはどれですか" in line
                or "どうしてですか" in line
                or "どのようなことですか" in line
                or "どのような状況でしたか" in line
                or "何を意味していますか" in line
            ):
                stem_candidates.append(line)
                continue

            passage_lines.append(line)

        # Build AST for passage
        passage_ast: list[dict[str, Any]] = []
        curr_p = []
        for pline in passage_lines:
            # Markdown table
            if pline.startswith("|") and pline.endswith("|"):
                if curr_p:
                    passage_ast.append({"type": "paragraph", "value": "\n".join(curr_p)})
                    curr_p = []
                # Keep table representation or raw paragraph
                passage_ast.append({"type": "paragraph", "value": pline})
            else:
                curr_p.append(pline)

        if curr_p:
            passage_ast.append({"type": "paragraph", "value": "\n".join(curr_p)})

        return {
            "passage_ast": passage_ast,
            "raw_passage": "\n\n".join(passage_lines),
            "stem": " ".join(stem_candidates) if stem_candidates else None,
            "options": options,
        }
