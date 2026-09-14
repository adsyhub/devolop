"""Backend registry. Backends are imported lazily: choosing Ollama must not
require torch to be installed, and vice versa."""

from __future__ import annotations

from .base import OcrBackend, PageResult

BACKENDS = {
    "qwen-vl": ("pdf_ocr.backends.qwen_vl", "QwenVLBackend"),
    "dots-ocr": ("pdf_ocr.backends.dots_ocr", "DotsOcrBackend"),
    "ollama": ("pdf_ocr.backends.ollama_vl", "OllamaBackend"),
    "openai-vlm": ("pdf_ocr.backends.openai_vlm", "OpenAICompatVLMBackend"),
}

# Each backend's natural prompt style: dots.ocr is trained to emit layout JSON,
# the general VLMs are asked for Markdown directly.
DEFAULT_PROMPT_STYLE = {
    "qwen-vl": "doc",
    "dots-ocr": "layout",
    "ollama": "doc",
    "openai-vlm": "doc",
}


def load_backend(name: str, **kwargs) -> OcrBackend:
    import importlib

    if name not in BACKENDS:
        raise SystemExit(f"Unknown backend {name!r}. Choose from: {', '.join(BACKENDS)}")
    module_name, class_name = BACKENDS[name]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)(**kwargs)


__all__ = ["BACKENDS", "DEFAULT_PROMPT_STYLE", "OcrBackend", "PageResult", "load_backend"]
