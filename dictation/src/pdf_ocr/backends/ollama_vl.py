"""Ollama backend -- any local vision model, no Python ML stack required.

The escape hatch: if the CUDA/transformers install ever breaks, `ollama pull
qwen2.5vl:7b` and this backend keeps the pipeline running. Talks plain HTTP over
urllib, matching this repo's rule that a provider never adds a dependency.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from .base import PageResult, SequentialBatchMixin


class OllamaBackend(SequentialBatchMixin):
    name = "ollama"

    def __init__(
        self,
        model_id: str = "qwen2.5vl:7b",
        *,
        host: str = "http://127.0.0.1:11434",
        max_new_tokens: int = 3072,
        timeout: int = 600,
        **_ignored,
    ) -> None:
        self.model_id = model_id
        self.host = host.rstrip("/")
        self.max_new_tokens = max_new_tokens
        self.timeout = timeout
        self._check_reachable()

    def _check_reachable(self) -> None:
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=10) as resp:
                tags = json.load(resp)
        except urllib.error.URLError as exc:
            raise SystemExit(
                f"Cannot reach Ollama at {self.host}: {exc}. Start it with `ollama serve`."
            ) from exc
        names = {m.get("name", "") for m in tags.get("models", [])}
        if self.model_id not in names and f"{self.model_id}:latest" not in names:
            raise SystemExit(
                f"Ollama has no model {self.model_id!r}. Pull it: ollama pull {self.model_id}"
            )

    def describe(self) -> dict:
        return {
            "backend": self.name,
            "model_id": self.model_id,
            "host": self.host,
            "max_new_tokens": self.max_new_tokens,
        }

    def transcribe(self, image_path: Path, *, prompt: str) -> PageResult:
        page = int(image_path.stem.split("-")[-1])
        started = time.perf_counter()
        try:
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            payload = json.dumps(
                {
                    "model": self.model_id,
                    "prompt": prompt,
                    "images": [encoded],
                    "stream": False,
                    "options": {"temperature": 0, "num_predict": self.max_new_tokens},
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                f"{self.host}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                body = json.load(resp)
            return PageResult(
                page=page,
                markdown=(body.get("response") or "").strip(),
                seconds=time.perf_counter() - started,
            )
        except Exception as exc:
            return PageResult(
                page=page,
                markdown="",
                seconds=time.perf_counter() - started,
                error=f"{type(exc).__name__}: {exc}",
            )
