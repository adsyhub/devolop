"""OpenAI-compatible multimodal backend for already-running local VLMs.

This is the bridge to vLLM and llama.cpp services.  It keeps model weights out
of this process, sends one rendered page as a data URL, and records the endpoint
and model id (never a secret) in the OCR provenance.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .base import PageResult, SequentialBatchMixin


def _flatten_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(part.get("text") or "")
            for part in content
            if isinstance(part, dict) and part.get("type") in {None, "text", "output_text"}
        )
    return ""


class OpenAICompatVLMBackend(SequentialBatchMixin):
    """Read page images through ``POST /v1/chat/completions``."""

    name = "openai-vlm"

    def __init__(
        self,
        model_id: str = "zai-org/GLM-OCR",
        *,
        base_url: str = "http://127.0.0.1:8102/v1",
        api_key_env: str = "",
        max_new_tokens: int = 3072,
        timeout: int = 600,
        repetition_penalty: float = 1.0,
        **_ignored: Any,
    ) -> None:
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.max_new_tokens = max_new_tokens
        self.timeout = timeout
        self.repetition_penalty = repetition_penalty

    def describe(self) -> dict[str, Any]:
        described: dict[str, Any] = {
            "backend": self.name,
            "model_id": self.model_id,
            "base_url": self.base_url,
            "max_new_tokens": self.max_new_tokens,
        }
        if self.api_key_env:
            described["api_key_env"] = self.api_key_env
        return described

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key_env:
            key = os.environ.get(self.api_key_env, "").strip()
            if not key:
                raise RuntimeError(f"Environment variable {self.api_key_env} is empty.")
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def transcribe(self, image_path: Path, *, prompt: str) -> PageResult:
        page = int(image_path.stem.split("-")[-1])
        started = time.perf_counter()
        try:
            mime = mimetypes.guess_type(image_path.name)[0] or "image/png"
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            payload: dict[str, Any] = {
                "model": self.model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime};base64,{encoded}"},
                            },
                        ],
                    }
                ],
                "temperature": 0,
                "max_tokens": self.max_new_tokens,
                "stream": False,
            }
            if self.repetition_penalty != 1.0:
                payload["repetition_penalty"] = self.repetition_penalty
            request = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers=self._headers(),
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.load(response)
            choices = body.get("choices")
            message = choices[0].get("message") if isinstance(choices, list) and choices else None
            markdown = _flatten_content(message.get("content") if isinstance(message, dict) else None)
            if not markdown.strip():
                raise RuntimeError("OpenAI-compatible VLM returned empty content.")
            return PageResult(
                page=page,
                markdown=markdown.strip(),
                seconds=time.perf_counter() - started,
            )
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                detail = ""
            return PageResult(
                page=page,
                markdown="",
                seconds=time.perf_counter() - started,
                error=f"HTTP {exc.code}: {detail or exc.reason}",
            )
        except Exception as exc:
            return PageResult(
                page=page,
                markdown="",
                seconds=time.perf_counter() - started,
                error=f"{type(exc).__name__}: {exc}",
            )
