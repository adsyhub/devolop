"""Serve the commercial dictation web player with an existing course manifest.

Also serves an optional local-only JSON API (`/api/vocab`, `/api/notes`, `/api/activity`) backed
by `local_backend.LearningStore`, so the player's vocab notebook / notes / streak can persist to
a durable SQLite file shared across course previews instead of being siloed per-origin in
`localStorage`. The web player works fully without this: see `local_backend.py` and README.md.

The same server also hosts the JLPT question bank at `/exam.html` with its `/api/exams*`
routes (`exam_store.py`). It shares this process because it shares everything that matters:
the same loopback security context, the same SQLite file, and the same origin — so a learner's
exam record sits beside their vocabulary instead of in a second app with its own port,
its own token and its own backup story.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import sys
import tempfile
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from bundle_quality import audit_manifest
from course_schema import is_remote_media_manifest
from error_contract import E_COURSE_QUALITY, make_error
from exam_api_v1 import ExamV1ApiMixin
from exam_db import ExamDatabase
from exam_engine import ExamEngine
from exam_rights import RightsModule
from exam_store import ExamApiMixin, ExamProgress, ExamStore
from lexicon_store import LexiconApiMixin, LexiconStore
from lexicon_api import LexiconWorkspaceMixin, LexiconServices
from local_backend import CourseStore, LearningApiMixin, LearningStore
from security_context import SecurityContext, token_from_environment


# The one place the player's CSP is written. `src/web/index.html` carries a copy in a
# <meta> tag for the file:// and static-hosting cases and `src/web/_headers` carries a
# third for a CDN; a test parses all three and fails if they drift apart, because a
# policy that differs between how the page is served is a policy nobody can reason about.
#
# Every remote host below is here for one reason and no other:
#   script-src  www.youtube.com   the IFrame Player API loader (/iframe_api)
#               s.ytimg.com       the widget bundle that loader pulls in
#   frame-src   www.youtube-nocookie.com, www.youtube.com   the embedded player itself
#               player.vimeo.com, player.bilibili.com       the other two framed tiers
#   img-src     i.ytimg.com, img.youtube.com                video thumbnails
#   connect-src www.youtube.com   the player's own stats/config XHRs
# frame-ancestors 'none' STAYS: it governs who may frame *us*, not whom we may frame.
# Stable product routes. The address bar is part of the product: a learner who
# bookmarks a workspace should get a path naming that workspace, not the .html
# file that happens to implement it today. The old file names keep working, so
# no existing link or bookmark breaks.
PRODUCT_ROUTES = {
    "/": "/home.html",
    "/listening": "/index.html",
    "/exams": "/exam.html",
    "/me": "/me.html",
    "/lexicon": "/lexicon.html",
}

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://www.youtube.com https://s.ytimg.com; "
    "style-src 'self'; "
    "img-src 'self' data: https://i.ytimg.com https://img.youtube.com; "
    "media-src 'self' blob:; "
    "connect-src 'self' https://www.youtube.com; "
    "frame-src https://www.youtube-nocookie.com https://www.youtube.com "
    "https://player.vimeo.com https://player.bilibili.com; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    """Loopback preview server that can restart without waiting out TCP TIME_WAIT."""

    allow_reuse_address = True


class PreviewServer:
    """Owns the preview directory, the HTTP server and the learning store.

    Split out of ``main()`` so tests can start a real server on an ephemeral port
    and exercise the actual request path, rather than asserting against a
    reimplementation of it.
    """

    def __init__(self, server: ThreadingHTTPServer, store: LearningStore,
                 course_store: CourseStore, temp_dir: tempfile.TemporaryDirectory,
                 security: SecurityContext, manifest: dict[str, Any],
                 manifest_path: Path, exam_store: ExamStore | None = None) -> None:
        self._server = server
        self._store = store
        self._course_store = course_store
        self._exam_store = exam_store
        self._temp_dir = temp_dir
        self.security = security
        self._exam_db = ExamDatabase(self._store.connection, self._store.lock)
        self._rights_module = RightsModule(self._exam_db)
        self._exam_engine = ExamEngine(self._exam_db, self._rights_module)
        # Active manifest — protected by a reentrant lock so GET and POST /api/courses/switch
        # don't race with each other or with static-file serving.
        self._manifest_lock = threading.RLock()
        self._manifest: dict[str, Any] = manifest
        self._manifest_path: Path = manifest_path

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"

    def serve_forever(self) -> None:
        self._server.serve_forever()

    def shutdown(self) -> None:
        self._server.shutdown()

    def close(self) -> None:
        self._server.server_close()
        self._store.close()
        self._temp_dir.cleanup()

    # ------------------------------------------------------------------
    # Course-switching helpers (called from PreviewHandler)
    # ------------------------------------------------------------------

    def get_active_manifest(self) -> dict[str, Any]:
        with self._manifest_lock:
            return dict(self._manifest)

    def switch_course(self, course_id: str, *, allow_failed_course: bool = False) -> dict[str, Any]:
        """Hot-swap the active course manifest.  Thread-safe.

        Loads, audits, and injects the new manifest into the temp preview
        directory so that a page reload picks it up immediately.  Returns the
        new manifest's quality summary.

        Raises:
            KeyError  – course_id not found in the courses directory.
            SystemExit – (caught and re-raised as RuntimeError) if the course
                         fails its quality audit and allow_failed_course is False.
        """
        manifest_path = self._course_store.get_manifest_path(course_id)
        if manifest_path is None:
            raise KeyError(course_id)
        manifest = load_json(manifest_path)
        report = audit_manifest(manifest, require_enrichment=True)
        summary = report["summary"]
        errors = int(summary.get("errors", 0))
        manifest["quality"] = {
            "status": report["status"],
            "blocked": bool(errors),
            "developmentBypass": bool(errors and allow_failed_course),
            **summary,
        }
        if errors and not allow_failed_course:
            raise RuntimeError(
                f"Course '{course_id}' failed quality audit ({errors} errors). "
                "Pass allow_failed_course=True to load it anyway."
            )
        preview_dir = Path(self._temp_dir.name)
        # Write new manifest and re-link audio atomically enough for our use-case.
        (preview_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        # An online-video course has no local media by design: there is nothing to
        # copy, and demanding a file here is exactly what would make it unopenable.
        if not is_remote_media_manifest(manifest):
            audio_name = safe_audio_name(manifest.get("audio"))
            audio_src = manifest_path.parent / audio_name
            if audio_src.resolve() != (preview_dir / audio_name).resolve():
                shutil.copy2(audio_src, preview_dir / audio_name)
        with self._manifest_lock:
            self._manifest = manifest
            self._manifest_path = manifest_path
        return manifest["quality"]


def build_preview_server(
    manifest_path: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 4173,
    data_dir: Path | None = None,
    courses_root: Path | None = None,
    exams_root: Path | None = None,
    lexicon_root: Path | None = None,
    allow_failed_course: bool = False,
    token: str | None = None,
) -> PreviewServer:
    """Assemble a preview server, refusing to serve a course that failed its audit.

    FND-001's fail-closed rule lives here. Previously the audit ran, its verdict
    was attached to the manifest as ``quality``, and the course was then served
    regardless — so the default course, which fails with 90 errors, opened as if
    it were fine and learners practised against corrupted enrichment. An audit
    whose result cannot block anything is decoration.
    """
    manifest = load_json(manifest_path)
    report = audit_manifest(manifest, require_enrichment=True)
    summary = report["summary"]
    manifest["quality"] = {"status": report["status"], **summary}

    errors = int(summary.get("errors", 0))
    if errors and not allow_failed_course:
        error = make_error(
            E_COURSE_QUALITY,
            stage="course-load",
            retryable=False,
            user_action="Repair or replace this course before studying it. To inspect it anyway, "
            "restart with --allow-failed-course (development preview only).",
        )
        raise SystemExit(
            f"[{error.code}] Course failed its quality audit: {errors} errors, "
            f"{summary.get('warnings', 0)} warnings.\n"
            f"  manifest    : {manifest_path}\n"
            f"  issueCounts : {json.dumps(summary.get('issueCounts', {}), ensure_ascii=False)}\n"
            f"  diagnosticId: {error.diagnosticId}\n"
            f"  {error.userAction}"
        )
    # A course opened through the development bypass stays labelled as such all
    # the way to the UI, so a preview can never be mistaken for a release.
    manifest["quality"]["blocked"] = bool(errors)
    manifest["quality"]["developmentBypass"] = bool(errors and allow_failed_course)

    remote_media = is_remote_media_manifest(manifest)
    audio_name = "" if remote_media else safe_audio_name(manifest.get("audio"))
    audio_path = None if remote_media else manifest_path.parent / audio_name
    if audio_path is not None and not audio_path.exists():
        raise SystemExit(f"Audio file not found next to manifest: {audio_path}")

    web_dir = Path(__file__).resolve().parent / "web"
    if not web_dir.is_dir():
        raise SystemExit(f"Web player not found: {web_dir}")

    resolved_data_dir = data_dir if data_dir is not None else default_data_dir()
    store = LearningStore(resolved_data_dir / "learning.sqlite3")

    # CourseStore: defaults to the ``courses/`` sibling of the project root
    # (two levels above this source file).
    resolved_courses_root = courses_root if courses_root is not None else (
        Path(__file__).resolve().parent.parent / "courses"
    )
    course_store = CourseStore(resolved_courses_root)

    # Exams live beside courses, in the project's ``exams/`` directory. A missing
    # directory is not an error: a learner may only ever use the dictation player,
    # and ``list_exams`` simply returns nothing.
    resolved_exams_root = exams_root if exams_root is not None else (
        Path(__file__).resolve().parent.parent / "exams"
    )
    exam_store = ExamStore(resolved_exams_root)
    exam_progress = ExamProgress.from_learning_store(store)

    # Lexicon packs live in the project's ``lexicon/`` directory. Like exams, a
    # missing directory is not an error: ``list_packs`` simply returns nothing.
    resolved_lexicon_root = lexicon_root if lexicon_root is not None else (
        Path(__file__).resolve().parent.parent / "lexicon"
    )
    lexicon_store = LexiconStore(resolved_lexicon_root)

    mimetypes.add_type("application/manifest+json", ".webmanifest")
    temp_dir = tempfile.TemporaryDirectory(prefix="dictation-preview-")
    preview_dir = Path(temp_dir.name)
    for asset in web_dir.iterdir():
        if asset.is_file():
            shutil.copy2(asset, preview_dir / asset.name)
    (preview_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if audio_path is not None:
        shutil.copy2(audio_path, preview_dir / audio_name)

    preview_server = PreviewServer(
        server=None,  # filled in below after binding
        store=store,
        course_store=course_store,
        temp_dir=temp_dir,
        security=None,  # filled in below
        manifest=manifest,
        manifest_path=manifest_path,
        exam_store=exam_store,
    )

    class BoundHandler(PreviewHandler):
        pass

    BoundHandler.store = store
    BoundHandler.exam_store = exam_store
    BoundHandler.exam_progress = exam_progress
    BoundHandler.lexicon_store = lexicon_store
    BoundHandler.lexicon_services = LexiconServices(store, lexicon_store)
    BoundHandler.exam_engine = preview_server._exam_engine
    BoundHandler.rights_module = preview_server._rights_module
    BoundHandler.preview_server = preview_server  # type: ignore[attr-defined]

    handler = lambda *handler_args, **kwargs: BoundHandler(  # noqa: E731
        *handler_args,
        directory=str(preview_dir),
        **kwargs,
    )
    server = LocalThreadingHTTPServer((host, port), handler)

    # The security context must describe the port we actually bound to, which is
    # only known after binding when port 0 was requested.
    security = SecurityContext(host, int(server.server_address[1]), token or token_from_environment())
    BoundHandler.security = security

    # Back-fill the fields that required the bound port.
    preview_server._server = server
    preview_server.security = security
    return preview_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview a dictation manifest in the local web player.")
    parser.add_argument(
        "manifest",
        nargs="?",
        default=str(Path(__file__).resolve().parent.parent / "courses" / "2010-12-N2" / "manifest.json"),
    )
    parser.add_argument("--host", default="127.0.0.1", help="Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=4173, help="Default: 4173")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Where the local vocab/notes/streak SQLite file lives. Default: a per-user local app-data "
        "directory (see default_data_dir()) — deliberately outside the repo, since a repo that lives "
        "inside a synced folder (OneDrive/Dropbox/etc.) can leave the sync client holding a transient "
        "lock on a freshly-written SQLite file, causing intermittent 'file in use' failures.",
    )
    parser.add_argument(
        "--allow-failed-course",
        action="store_true",
        help="Development preview only: open a course that failed its quality audit. The player "
        "keeps showing it as not releasable.",
    )
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("The local preview server may only bind to localhost: it now also serves a personal-data API.")

    preview = build_preview_server(
        Path(args.manifest).expanduser().resolve(),
        host=args.host,
        port=args.port,
        data_dir=Path(args.data_dir).expanduser().resolve() if args.data_dir else None,
        allow_failed_course=args.allow_failed_course,
    )
    print(f"Preview: http://{args.host}:{preview.port}/")
    print(f"Local vocab/notes/streak data: {preview._store.db_path}")
    if args.allow_failed_course:
        print("WARNING: --allow-failed-course is set. This course is NOT releasable.", file=sys.stderr)
    print("Press Ctrl+C to stop.")
    try:
        preview.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        preview.close()


class PreviewHandler(LexiconWorkspaceMixin, LexiconApiMixin, ExamV1ApiMixin, ExamApiMixin, LearningApiMixin, SimpleHTTPRequestHandler):
    security: SecurityContext
    preview_server: "PreviewServer"

    def log_message(self, format: str, *args: Any) -> None:
        """Do not let a detached/closed console break otherwise valid HTTP responses."""
        try:
            super().log_message(format, *args)
        except (OSError, ValueError):
            pass

    def deny(self, reason: str) -> None:
        """Refuse a request without telling the caller anything useful.

        The reason is a fixed vocabulary from `SecurityContext`, never an echo of
        the caller's own headers: reflecting the rejected Host or Origin back
        would hand a prober a free oracle for mapping the allowlist.
        """
        self.log_message("denied %s %s (%s)", self.command, self.path, reason)
        self.send_response(HTTPStatus.FORBIDDEN)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def authorized_api(self, parsed) -> bool:
        decision = self.security.authorize_api(self.headers, method=self.command, path=parsed.path)
        if not decision.allowed:
            self.deny(decision.reason)
            return False
        return True

    def send_session_bootstrap(self) -> None:
        """Hand the same-origin page its session token.

        This is the only place the token crosses the wire. It never appears in a
        URL, a log line, or an error page, so it cannot be picked up from browser
        history, a proxy log, or a screenshot.
        """
        decision = self.security.authorize_bootstrap(self.headers)
        if not decision.allowed:
            self.deny(decision.reason)
            return
        self.send_learning_json({"token": self.security.token})

    # ------------------------------------------------------------------
    # Course-picker API routes
    # ------------------------------------------------------------------

    def handle_courses_get(self, parsed) -> bool:
        """Handle GET /api/courses and GET /api/courses/<id>/manifest."""
        path = parsed.path

        if path == "/api/courses":
            courses = self.preview_server._course_store.list_courses()
            self.send_learning_json({"courses": courses})
            return True

        prefix = "/api/courses/"
        if path.startswith(prefix) and path.endswith("/manifest"):
            from urllib.parse import unquote
            course_id = unquote(path[len(prefix):-len("/manifest")])
            if not course_id:
                self.send_learning_json({"error": "course id is required"}, HTTPStatus.BAD_REQUEST)
                return True
            manifest_path = self.preview_server._course_store.get_manifest_path(course_id)
            if manifest_path is None:
                self.send_learning_json({"error": "course not found"}, HTTPStatus.NOT_FOUND)
                return True
            try:
                manifest = load_json(manifest_path)
                report = audit_manifest(manifest, require_enrichment=True)
                summary = report["summary"]
                manifest["quality"] = {
                    "status": report["status"],
                    "blocked": bool(int(summary.get("errors", 0))),
                    "developmentBypass": False,
                    **summary,
                }
            except Exception as exc:  # noqa: BLE001
                self.send_learning_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return True
            self.send_learning_json({"manifest": manifest})
            return True

        return False

    def handle_courses_post(self, parsed) -> bool:
        """Handle POST /api/courses/switch — hot-swap the active course."""
        if parsed.path != "/api/courses/switch":
            return False
        try:
            payload = self.read_learning_json()
        except ValueError as exc:
            self.send_learning_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return True
        course_id = str(payload.get("courseId") or "").strip()
        if not course_id:
            self.send_learning_json({"error": "courseId is required"}, HTTPStatus.BAD_REQUEST)
            return True
        try:
            quality = self.preview_server.switch_course(course_id)
        except KeyError:
            self.send_learning_json({"error": f"course '{course_id}' not found"}, HTTPStatus.NOT_FOUND)
            return True
        except RuntimeError as exc:
            self.send_learning_json({"error": str(exc)}, HTTPStatus.UNPROCESSABLE_ENTITY)
            return True
        self.send_learning_json({"ok": True, "courseId": course_id, "quality": quality})
        return True

    # ------------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path.startswith("/api/"):
            if parsed.path == "/api/session/bootstrap":
                self.send_session_bootstrap()
                return
            if not self.authorized_api(parsed):
                return
            if self.handle_lexicon_workspace(parsed):
                return
            if self.handle_courses_get(parsed):
                return
            if self.handle_exam_v1_get(parsed):
                return
            if self.handle_exam_get(parsed):
                return
            if self.handle_lexicon_get(parsed):
                return
            if self.handle_deck_get(parsed):
                return
            if not self.handle_learning_get(parsed):
                self.send_error(HTTPStatus.NOT_FOUND)
            return
        # Course text and audio are personal-adjacent and should not be readable
        # by a rebound origin either.
        static_decision = self.security.authorize_static(self.headers)
        if not static_decision.allowed:
            self.deny(static_decision.reason)
            return
        if self.headers.get("Range") and self.serve_range_request(include_body=True):
            return
        if self.rewrite_root():
            return
        super().do_GET()

    def rewrite_root(self) -> bool:
        """Map a stable product route onto the page that implements it.

        ``SimpleHTTPRequestHandler`` hands ``/`` to ``index.html``, which is the
        精听 board rather than the application's front door. Rewriting the path
        here (rather than renaming files) keeps ``/index.html`` a working direct
        link to the player and leaves the directory layout alone. The same goes
        for the other three workspaces: ``/listening``, ``/exams``, ``/me`` and
        ``/lexicon`` are the addresses the README hands out.

        Returns True when the request has already been answered — a redirect —
        in which case the caller must not also run the file server.
        """
        parsed = urlsplit(self.path)
        path = parsed.path
        query = f"?{parsed.query}" if parsed.query else ""

        if path in {"", "/"}:
            self.path = PRODUCT_ROUTES["/"] + query
            return False

        # One canonical spelling per route. ``/listening/`` is the same workspace
        # as ``/listening``, and letting both resolve gives the same page two
        # URLs — two sets of history entries, two cache keys, and a learner who
        # cannot tell why their progress looks different on one of them.
        if path.endswith("/") and path.rstrip("/") in PRODUCT_ROUTES:
            self.send_response(HTTPStatus.PERMANENT_REDIRECT)
            self.send_header("Location", path.rstrip("/") + query)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True

        target = PRODUCT_ROUTES.get(path)
        if target is not None:
            self.path = target + query
        return False

    def do_HEAD(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path.startswith("/api/"):
            if not self.authorized_api(parsed):
                return
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        static_decision = self.security.authorize_static(self.headers)
        if not static_decision.allowed:
            self.deny(static_decision.reason)
            return
        if self.headers.get("Range") and self.serve_range_request(include_body=False):
            return
        if self.rewrite_root():
            return
        super().do_HEAD()

    def serve_range_request(self, *, include_body: bool) -> bool:
        """Answer a Range request with a real 206 Partial Content response.

        `SimpleHTTPRequestHandler` has no Range support at all: it always serves the whole
        file with a 200. For a 20MB+ audio file, that leaves the browser's `<audio>` element
        holding a connection open past the point where it actually stopped reading (it only
        wanted the first chunk for `preload="metadata"`), which can keep the request looking
        perpetually "pending" to tools that wait for real network idle (e.g. Playwright's
        `wait_until="networkidle"`). Serving a real 206 for just the requested bytes avoids
        that entirely, and matches the browser's actual expectations for a seekable media file.
        """
        file_path = self.translate_path(self.path)
        if not os.path.isfile(file_path):
            return False
        size = os.path.getsize(file_path)
        try:
            start, end, partial = parse_range_header(self.headers.get("Range"), size)
        except ValueError:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True
        length = end - start + 1
        content_type = self.guess_type(file_path)
        self.send_response(HTTPStatus.PARTIAL_CONTENT if partial else HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if not include_body:
            return True
        try:
            with open(file_path, "rb") as source:
                source.seek(start)
                remaining = length
                while remaining:
                    block = source.read(min(64 * 1024, remaining))
                    if not block:
                        break
                    self.wfile.write(block)
                    remaining -= len(block)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            # The client (e.g. an <audio preload="metadata"> element that only wanted the
            # first chunk) closed the connection before we finished streaming. That's normal
            # for a partial-content response, not an error — swallow it so socketserver's
            # default handler doesn't dump a full traceback to stderr for routine disconnects.
            pass
        return True

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if not self.authorized_api(parsed):
            return
        if self.handle_lexicon_workspace(parsed):
            return
        if self.handle_courses_post(parsed):
            return
        if self.handle_exam_v1_post(parsed):
            return
        if self.handle_exam_post(parsed):
            return
        if self.handle_deck_post(parsed):
            return
        if not self.handle_learning_post(parsed):
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if not self.authorized_api(parsed):
            return
        if self.handle_lexicon_workspace(parsed):
            return
        if self.handle_deck_patch(parsed):
            return
        if not self.handle_learning_patch(parsed):
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if not self.authorized_api(parsed):
            return
        if self.handle_lexicon_workspace(parsed):
            return
        if self.handle_exam_v1_put(parsed):
            return
        if not self.handle_learning_put(parsed):
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if not self.authorized_api(parsed):
            return
        if self.handle_lexicon_workspace(parsed):
            return
        if self.handle_exam_delete(parsed):
            return
        if self.handle_deck_delete(parsed):
            return
        if not self.handle_learning_delete(parsed):
            self.send_error(HTTPStatus.NOT_FOUND)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        super().end_headers()


def default_data_dir() -> Path:
    """Where the vocab/notes/streak SQLite file lives when `--data-dir` isn't given.

    Deliberately a per-user *local* app-data directory rather than a folder next to this
    script: this repo commonly lives inside a cloud-synced folder (OneDrive/Dropbox/iCloud
    Drive), and those sync clients routinely hold a brief exclusive lock on a small file right
    after it's written — which showed up here as intermittent "file in use" / connection
    failures against a freshly created SQLite database during rapid local testing.
    `%LOCALAPPDATA%` (Windows) and `~/.local/share` (elsewhere) are explicitly meant for
    local-only data and are not synced by any of those clients.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
    return base / "dictation-preview"


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


def safe_audio_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit("manifest.audio is missing.")
    normalized = value.strip().replace("\\", "/")
    if "/" in normalized or normalized in {".", ".."}:
        raise SystemExit("manifest.audio must be a safe filename next to the manifest.")
    return normalized


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Manifest must be a JSON object.")
    return data


if __name__ == "__main__":
    main()
