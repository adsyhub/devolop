"""Qwen2.5-VL backend (transformers, local weights, CUDA).

Qwen2.5-VL is the workhorse here: first-class support in transformers (no
``trust_remote_code``, no flash-attn build -- which matters on Windows, where
flash-attn has no wheels), strong Japanese/Chinese/Korean OCR, and a 7B
checkpoint that fits bf16 on a 24 GB card alongside a full-resolution page.

Decoding is memory-bandwidth bound in principle -- the whole 16 GB of weights is
read per token no matter how many pages are in flight -- so batching ought to buy
near-linear throughput. On a 24 GB card it does not: the weights plus one page's
vision activations already crowd the card, so batching trades the bandwidth win
back for paging. Measured here, batch 4 gave 15.3 tok/s against batch 1's 12.1.
``transcribe_batch`` is kept because it costs nothing and pays off on a bigger
card; on this one, leave --batch-size at 1 and reach for a smaller model instead.
"""

from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from .base import PageResult

# A 28x28 pixel patch becomes one visual token, and the vision tower's attention
# cost grows superlinearly with them. Measured on a 24 GB RTX 4500 Ada with the
# 7B checkpoint (16.6 GB of weights), peak allocation per page was:
#
#   1.0 MP -> 17.2 GB    2.4 MP -> 19.5 GB    6.4 MP -> 33.8 GB
#   1.6 MP -> 18.0 GB    3.2 MP -> 21.5 GB
#
# Past ~3.2 MP the card is oversubscribed. Windows/WDDM does not raise OOM there;
# it silently pages to system RAM, and throughput collapses (335 s/page versus
# 48 s/page). So the default is the largest budget that genuinely fits, not the
# largest the model accepts.
DEFAULT_MAX_PIXELS = 3_211_264  # 4096 visual tokens
DEFAULT_MIN_PIXELS = 200_704  # 256 visual tokens


def _page_number(image_path: Path) -> int:
    return int(image_path.stem.split("-")[-1])


class QwenVLBackend:
    name = "qwen-vl"

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-VL-7B-Instruct",
        *,
        device: str = "cuda",
        dtype: str = "bfloat16",
        max_pixels: int = DEFAULT_MAX_PIXELS,
        min_pixels: int = DEFAULT_MIN_PIXELS,
        max_new_tokens: int = 3072,
        repetition_penalty: float = 1.0,
        attn: str = "sdpa",
        **_ignored,
    ) -> None:
        import torch
        from transformers import AutoProcessor

        try:  # transformers >= 4.49
            from transformers import Qwen2_5_VLForConditionalGeneration as _Model
        except ImportError as exc:  # pragma: no cover
            raise SystemExit(
                "This transformers build has no Qwen2.5-VL support. "
                "Upgrade: pip install -U 'transformers>=4.51'"
            ) from exc

        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.repetition_penalty = repetition_penalty
        self.max_pixels = max_pixels
        self.min_pixels = min_pixels
        self._torch = torch

        self.model = _Model.from_pretrained(
            model_id,
            dtype=getattr(torch, dtype),
            attn_implementation=attn,
            device_map=device,
        )
        self.model.eval()
        self.processor = AutoProcessor.from_pretrained(
            model_id, min_pixels=min_pixels, max_pixels=max_pixels
        )
        # Generation needs left padding, or short pages decode from pad tokens.
        self.processor.tokenizer.padding_side = "left"
        self.device = str(self.model.device)

    def describe(self) -> dict:
        return {
            "backend": self.name,
            "model_id": self.model_id,
            "device": self.device,
            "max_pixels": self.max_pixels,
            "min_pixels": self.min_pixels,
            "max_new_tokens": self.max_new_tokens,
            "repetition_penalty": self.repetition_penalty,
        }

    def _generate(self, images: list[Image.Image], prompt: str) -> list[str]:
        messages = [
            {
                "role": "user",
                "content": [{"type": "image"}, {"type": "text", "text": prompt}],
            }
        ]
        one_text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(
            text=[one_text] * len(images),
            images=images,
            return_tensors="pt",
            padding=True,
        ).to(self.model.device)

        with self._torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                repetition_penalty=self.repetition_penalty,
            )
        # Left padding means every row shares the same prompt width.
        trimmed = generated[:, inputs.input_ids.shape[1] :]
        return self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

    def transcribe_batch(self, image_paths: list[Path], *, prompt: str) -> list[PageResult]:
        if not image_paths:
            return []
        started = time.perf_counter()
        try:
            images = []
            for path in image_paths:
                with Image.open(path) as raw:
                    images.append(raw.convert("RGB"))
            outputs = self._generate(images, prompt)
        except self._torch.cuda.OutOfMemoryError:
            self._torch.cuda.empty_cache()
            if len(image_paths) == 1:
                return [
                    PageResult(
                        page=_page_number(image_paths[0]),
                        markdown="",
                        seconds=time.perf_counter() - started,
                        error="OutOfMemoryError: lower --max-pixels or --max-new-tokens",
                    )
                ]
            # Halve and retry: one oversized page should not fail its neighbours.
            middle = len(image_paths) // 2
            return self.transcribe_batch(
                image_paths[:middle], prompt=prompt
            ) + self.transcribe_batch(image_paths[middle:], prompt=prompt)
        except Exception as exc:  # a bad page must not kill a 157-page run
            elapsed = time.perf_counter() - started
            return [
                PageResult(
                    page=_page_number(path),
                    markdown="",
                    seconds=elapsed / len(image_paths),
                    error=f"{type(exc).__name__}: {exc}",
                )
                for path in image_paths
            ]

        share = (time.perf_counter() - started) / len(image_paths)
        return [
            PageResult(page=_page_number(path), markdown=text.strip(), seconds=share)
            for path, text in zip(image_paths, outputs)
        ]

    def transcribe(self, image_path: Path, *, prompt: str) -> PageResult:
        return self.transcribe_batch([image_path], prompt=prompt)[0]
