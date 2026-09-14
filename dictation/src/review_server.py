"""Localhost-only review console for per-sentence human listening approval."""

from __future__ import annotations

import argparse
import json
import mimetypes
import secrets
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from build_deepseek_offline_bundle import load_json, write_json
from human_review import CHECK_FIELDS, audit_human_review, create_review, finalize_review, record_item
from serve_course import safe_audio_name


MAX_JSON_BODY = 64 * 1024
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "media-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


class ReviewStore:
    def __init__(self, manifest: dict[str, Any], review_path: Path) -> None:
        self.manifest = manifest
        self.review_path = review_path
        self.lock = threading.RLock()

    def load(self) -> dict[str, Any]:
        return load_json(self.review_path)

    def session(self) -> dict[str, Any]:
        with self.lock:
            review = self.load()
            items = review.get("items") if isinstance(review.get("items"), list) else []
            counts = {status: 0 for status in ("pending", "approved", "changes_required")}
            for item in items:
                if isinstance(item, dict) and item.get("status") in counts:
                    counts[item["status"]] += 1
            return {
                "course": {
                    "title": self.manifest.get("title"),
                    "courseId": self.manifest.get("courseId"),
                    "contentRevision": self.manifest.get("contentRevision"),
                    "sourceLanguage": self.manifest.get("sourceLanguage"),
                    "language": self.manifest.get("language"),
                    "locales": self.manifest.get("locales"),
                    "sentences": self.manifest.get("sentences"),
                },
                "review": review,
                "counts": counts,
                "checkFields": list(CHECK_FIELDS),
            }

    def update_item(self, sentence_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        status = str(payload.get("status") or "")
        notes = payload.get("notes")
        checks = payload.get("checks")
        if notes is not None and not isinstance(notes, str):
            raise ValueError("notes must be a string.")
        if not isinstance(checks, dict):
            raise ValueError("checks must be an object.")
        normalized_checks = {str(key): value for key, value in checks.items()}
        with self.lock:
            review = self.load()
            record_item(
                self.manifest,
                review,
                sentence_id=sentence_id,
                status=status,
                all_checks=False,
                notes=notes,
                checks=normalized_checks,
            )
            write_json(self.review_path, review)
            return next(item for item in review["items"] if item["sentenceId"] == sentence_id)

    def finalize(self) -> dict[str, Any]:
        with self.lock:
            review = self.load()
            finalize_review(self.manifest, review)
            write_json(self.review_path, review)
            return audit_human_review(self.manifest, review)


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "DictationReview/1.0"
    store: ReviewStore
    token: str
    web_dir: Path
    audio_path: Path

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/session":
            if not self.authorized(parsed.query):
                self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            self.send_json(self.store.session())
            return
        if parsed.path == "/audio":
            if not self.authorized(parsed.query):
                self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            self.send_audio(include_body=True)
            return
        self.send_asset(parsed.path)

    def do_HEAD(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/audio" and self.authorized(parsed.query):
            self.send_audio(include_body=False)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        prefix = "/api/items/"
        if not parsed.path.startswith(prefix):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.authorized(parsed.query) or not self.same_origin():
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return
        sentence_id = unquote(parsed.path[len(prefix) :])
        try:
            item = self.store.update_item(sentence_id, self.read_json())
        except (ValueError, StopIteration) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self.send_json({"item": item})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path != "/api/finalize":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.authorized(parsed.query) or not self.same_origin():
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return
        try:
            payload = self.read_json()
            if payload.get("independentHumanReview") is not True or payload.get("commercialReleaseRecommendation") is not True:
                raise ValueError("Both explicit attestations are required.")
            report = self.store.finalize()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self.send_json({"report": report})

    def read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError as exc:
            raise ValueError("Invalid Content-Length.") from exc
        if length < 2 or length > MAX_JSON_BODY:
            raise ValueError("JSON request body is empty or too large.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid UTF-8 JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def authorized(self, query: str) -> bool:
        query_token = parse_qs(query).get("token", [""])[0]
        header_token = self.headers.get("X-Review-Token") or ""
        supplied = header_token or query_token
        return bool(supplied) and secrets.compare_digest(supplied, self.token)

    def same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return False
        expected = f"http://{self.headers.get('Host')}"
        return secrets.compare_digest(origin, expected)

    def send_asset(self, url_path: str) -> None:
        name = "index.html" if url_path in {"", "/"} else url_path.lstrip("/")
        if name not in {"index.html", "review.css", "review.js", "favicon.svg"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        path = self.web_dir / name
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_common_headers(media_type, len(data))
        self.end_headers()
        self.wfile.write(data)

    def send_audio(self, *, include_body: bool) -> None:
        size = self.audio_path.stat().st_size
        try:
            start, end, partial = parse_range_header(self.headers.get("Range"), size)
        except ValueError:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_common_headers(mimetypes.guess_type(self.audio_path.name)[0] or "audio/mpeg", 0)
            self.end_headers()
            return
        length = end - start + 1
        self.send_response(HTTPStatus.PARTIAL_CONTENT if partial else HTTPStatus.OK)
        self.send_common_headers(mimetypes.guess_type(self.audio_path.name)[0] or "audio/mpeg", length)
        self.send_header("Accept-Ranges", "bytes")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if not include_body:
            return
        with self.audio_path.open("rb") as source:
            source.seek(start)
            remaining = length
            while remaining:
                block = source.read(min(64 * 1024, remaining))
                if not block:
                    break
                self.wfile.write(block)
                remaining -= len(block)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_common_headers("application/json; charset=utf-8", len(data))
        self.end_headers()
        self.wfile.write(data)

    def send_common_headers(self, content_type: str, content_length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store")
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.client_address[0]} - {format % args}")


def parse_range_header(value: str | None, size: int) -> tuple[int, int, bool]:
    if not value:
        return 0, size - 1, False
    if not value.startswith("bytes=") or "," in value:
        raise ValueError("Only one byte range is supported.")
    spec = value[6:].strip()
    if "-" not in spec:
        raise ValueError("Invalid byte range.")
    left, right = spec.split("-", 1)
    try:
        if not left:
            suffix = int(right)
            if suffix <= 0:
                raise ValueError("Invalid suffix range.")
            start = max(0, size - suffix)
            end = size - 1
        else:
            start = int(left)
            end = int(right) if right else size - 1
            end = min(end, size - 1)
    except ValueError as exc:
        raise ValueError("Invalid byte range.") from exc
    if start < 0 or start >= size or end < start:
        raise ValueError("Unsatisfiable byte range.")
    return start, end, True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a localhost-only human course review console.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--reviewer", help="Required only when creating a new review file.")
    parser.add_argument("--organization", default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4180)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("The review console may only bind to localhost.")

    manifest_path = Path(args.manifest).expanduser().resolve()
    review_path = Path(args.review).expanduser().resolve()
    manifest = load_json(manifest_path)
    if isinstance(manifest.get("media"), dict):
        # The reviewer plays a local file per sentence; an online-video course has no
        # such file. Saying so beats "manifest.audio is missing", which reads as though
        # the course were corrupt rather than simply a different kind.
        raise SystemExit(
            "逐句审核工具目前只支持本地音频课程。这是一门在线视频课程，"
            "请用播放器打开它：python start_dictation.py --manifest <manifest>"
            " / The review tool supports local-audio courses only; this is an online-video course."
        )
    audio_name = safe_audio_name(manifest.get("audio"))
    audio_path = manifest_path.parent / audio_name
    if not audio_path.is_file():
        raise SystemExit(f"Audio file not found: {audio_path}")
    if not review_path.exists():
        if not args.reviewer:
            raise SystemExit("--reviewer is required when creating a new review file.")
        write_json(
            review_path,
            create_review(manifest, reviewer=args.reviewer, organization=args.organization),
        )
    else:
        review = load_json(review_path)
        if review.get("courseId") != manifest.get("courseId") or review.get("contentRevision") != manifest.get("contentRevision"):
            raise SystemExit("Existing review file is not bound to this manifest revision.")

    web_dir = Path(__file__).resolve().parent / "review_web"
    if not web_dir.is_dir():
        raise SystemExit(f"Review web assets not found: {web_dir}")
    token = secrets.token_urlsafe(32)
    store = ReviewStore(manifest, review_path)

    class BoundHandler(ReviewHandler):
        pass

    BoundHandler.store = store
    BoundHandler.token = token
    BoundHandler.web_dir = web_dir
    BoundHandler.audio_path = audio_path
    server = ThreadingHTTPServer((args.host, args.port), BoundHandler)
    print(f"Review console: http://{args.host}:{args.port}/?token={token}")
    print(f"Review state: {review_path}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
