"""What every OCR backend must provide."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class PageResult:
    """One transcribed page."""

    page: int  # 1-based
    markdown: str
    blocks: list[dict] = field(default_factory=list)  # layout elements, when the backend emits them
    seconds: float = 0.0
    error: str | None = None
    backend: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None


@runtime_checkable
class OcrBackend(Protocol):
    """A loaded model that can transcribe page images."""

    name: str

    def describe(self) -> dict:
        """Identity of the model, recorded in the output manifest."""
        ...

    def transcribe(self, image_path: Path, *, prompt: str) -> PageResult:
        """Transcribe one page image."""
        ...

    def transcribe_batch(self, image_paths: list[Path], *, prompt: str) -> list[PageResult]:
        """Transcribe several pages. Backends that cannot batch run them in turn."""
        ...


class SequentialBatchMixin:
    """Default ``transcribe_batch`` for backends with no real batch path."""

    def transcribe_batch(self, image_paths: list[Path], *, prompt: str) -> list[PageResult]:
        return [self.transcribe(path, prompt=prompt) for path in image_paths]
