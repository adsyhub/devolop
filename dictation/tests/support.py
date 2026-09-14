"""Shared fixtures for the P0 regression suite.

Two rules from the plan shape this module:

* tests must not depend on the real 21.5MB course audio, and
* tests must not sleep and hope.

So courses here are tiny generated fixtures, and the server is started on an
ephemeral port and waited on by polling its own socket.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from serve_course import build_preview_server  # noqa: E402
from security_context import TOKEN_HEADER  # noqa: E402

# A 32-byte payload is enough to exercise Range arithmetic (start, end, suffix,
# unsatisfiable) and keeps every assertion readable.
FIXTURE_AUDIO = bytes(range(32))


def make_sentence(index: int, text: str) -> dict[str, Any]:
    return {
        "id": f"s_{index:04d}",
        "startTime": float(index * 2),
        "endTime": float(index * 2 + 2),
        "jaText": text,
        "zhTranslation": "这是一个测试。",
        "explanationText": "テスト用の短い文です。",
    }


def write_course(directory: Path, *, sentences: list[dict[str, Any]] | None = None,
                 course_id: str = "c_test", audio: bytes = FIXTURE_AUDIO) -> Path:
    """Write a minimal course whose manifest passes the quality audit cleanly."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "audio.mp3").write_bytes(audio)
    if sentences is None:
        sentences = [make_sentence(0, "これはテストです。"), make_sentence(1, "音声は短いです。")]
    manifest = {
        "schemaVersion": 1,
        "courseId": course_id,
        "title": "Test course",
        "audio": "audio.mp3",
        "sourceLanguage": "ja",
        "contentRevision": "a" * 64,
        "sentences": sentences,
        # audit_manifest warns unless this exactly matches the concatenated text.
        "transcriptText": "".join(str(item.get("jaText") or "") for item in sentences),
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def corrupt_sentence() -> dict[str, Any]:
    """A sentence the audit rejects, for exercising the fail-closed gate."""
    return {
        "id": "s_bad",
        "startTime": 5.0,
        "endTime": 4.0,  # endTime must be greater than startTime
        "jaText": "",  # source text is required
        "zhTranslation": "",
    }


class RunningServer:
    """A preview server on an ephemeral port, torn down on context exit."""

    def __init__(self, manifest_path: Path, data_dir: Path, *, allow_failed_course: bool = False,
                 token: str = "test-token", exams_root: Path | None = None,
                 lexicon_root: Path | None = None) -> None:
        self.preview = build_preview_server(
            manifest_path,
            host="127.0.0.1",
            port=0,
            data_dir=data_dir,
            exams_root=exams_root,
            lexicon_root=lexicon_root,
            allow_failed_course=allow_failed_course,
            token=token,
        )
        self.token = token
        self._thread = threading.Thread(target=self.preview.serve_forever, daemon=True)

    def __enter__(self) -> "RunningServer":
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.preview.shutdown()
        self._thread.join(timeout=5)
        self.preview.close()

    @property
    def port(self) -> int:
        return self.preview.port

    @property
    def host_header(self) -> str:
        return f"127.0.0.1:{self.port}"

    def request(
        self,
        method: str,
        path: str,
        *,
        host: str | None = None,
        origin: str | None = None,
        token: str | None = "valid",
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, bytes]:
        """Issue a raw request, returning (status, body).

        `host` and `origin` default to the genuine values; pass them explicitly to
        forge them. `token="valid"` sends the real one, `None` sends none, and any
        other string is sent verbatim.
        """
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Host", host if host is not None else self.host_header)
        if origin is not None:
            request.add_header("Origin", origin)
        if token == "valid":
            request.add_header(TOKEN_HEADER, self.token)
        elif token is not None:
            request.add_header(TOKEN_HEADER, token)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
