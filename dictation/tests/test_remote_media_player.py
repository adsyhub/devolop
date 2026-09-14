"""Serving an online-video course, and keeping one CSP across three files.

Two failure modes this covers are both silent, which is why they get tests rather
than a careful reading:

* the preview server used to demand a local audio file before it would start. An
  online-video course has none by design, so without this it simply refuses to open.
* the Content-Security-Policy exists in three copies — the server header, a <meta>
  tag for static hosting, and _headers for a CDN. If they drift, playback works in
  one deployment and silently fails in another, with nothing in the UI to say why.
"""

from __future__ import annotations

import json
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from serve_course import CONTENT_SECURITY_POLICY  # noqa: E402
from support import RunningServer  # noqa: E402

WEB_DIR = PROJECT_DIR / "src" / "web"


def remote_course(directory: Path) -> Path:
    """A minimal online-video course. Deliberately writes no media file at all."""
    directory.mkdir(parents=True, exist_ok=True)
    sentences = [
        {
            "id": "s_" + "0" * 24,
            "startTime": 1.0,
            "endTime": 4.0,
            "jaText": "おはようございます。",
            "sourceText": "おはようございます。",
            "zhTranslation": "早上好。",
            "translationText": "早上好。",
            "explanationText": "朝の挨拶です。",
        },
        {
            "id": "s_" + "1" * 24,
            "startTime": 4.0,
            "endTime": 8.0,
            "jaText": "今日はいい天気ですね。",
            "sourceText": "今日はいい天気ですね。",
            "zhTranslation": "今天天气真好。",
            "translationText": "今天天气真好。",
            "explanationText": "天気の話題です。",
        },
    ]
    manifest = {
        "schemaVersion": 1,
        "courseId": "c_" + "a" * 24,
        "title": "NHK ニュース",
        "sourceLanguage": "ja",
        "contentRevision": "b" * 64,
        "media": {
            "kind": "remote",
            "provider": "youtube",
            "control": "full",
            "videoId": "dQw4w9WgXcQ",
            "pageUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "embedUrl": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
            "durationSec": 612.0,
            "uploader": "NHK",
            "attribution": {
                "sourceName": "YouTube",
                "rightsHolder": "NHK",
                "retrievedAt": "2026-08-31",
                "redistributable": False,
                "notes": "",
            },
        },
        "sentences": sentences,
        "transcriptText": "".join(s["jaText"] for s in sentences),
    }
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class ServingARemoteCourseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = TemporaryDirectory(prefix="remote-player-")
        self.root = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        self.manifest = remote_course(self.root / "course")
        self.data = self.root / "data"

    def test_a_course_with_no_local_media_starts_and_serves(self) -> None:
        # The regression: build_preview_server used to exit with "Audio file not
        # found next to manifest" before it ever bound a port.
        with RunningServer(self.manifest, self.data) as server:
            status, body = server.request("GET", "/index.html")
            self.assertEqual(status, 200)
            self.assertIn(b"media_adapters.js", body)

    def test_the_manifest_reaches_the_page_with_its_media_block_intact(self) -> None:
        with RunningServer(self.manifest, self.data) as server:
            status, body = server.request("GET", "/manifest.json")
            self.assertEqual(status, 200)
            manifest = json.loads(body)
            self.assertNotIn("audio", manifest)
            self.assertEqual(manifest["media"]["provider"], "youtube")
            self.assertEqual(manifest["media"]["control"], "full")
            self.assertIs(manifest["media"]["attribution"]["redistributable"], False)

    def test_no_media_file_is_ever_copied_into_the_served_directory(self) -> None:
        with RunningServer(self.manifest, self.data) as server:
            for name in ("audio.mp3", "video.mp4", "media.webm"):
                status, _ = server.request("GET", f"/{name}")
                self.assertEqual(status, 404, f"{name} should not exist")

    def test_the_quality_gate_still_refuses_a_broken_remote_course(self) -> None:
        # Adding a new course kind must not open a hole in the fail-closed rule.
        broken = self.root / "broken"
        path = remote_course(broken)
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["media"]["control"] = "telepathy"
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(SystemExit):
            with RunningServer(path, self.data):
                pass


class ContentSecurityPolicyTests(unittest.TestCase):
    """One policy, three deployments. They have to say the same thing."""

    def setUp(self) -> None:
        self._temp = TemporaryDirectory(prefix="remote-csp-")
        self.root = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)
        self.manifest = remote_course(self.root / "course")

    @staticmethod
    def directives(policy: str) -> dict[str, set[str]]:
        parsed: dict[str, set[str]] = {}
        for chunk in policy.split(";"):
            parts = chunk.split()
            if parts:
                parsed[parts[0]] = set(parts[1:])
        return parsed

    def test_the_served_header_carries_every_host_the_player_needs(self) -> None:
        with RunningServer(self.manifest, self.root / "data") as server:
            request = urllib.request.Request(f"http://127.0.0.1:{server.port}/index.html")
            request.add_header("Host", server.host_header)
            with urllib.request.urlopen(request, timeout=5) as response:
                policy = response.headers["Content-Security-Policy"]
        directives = self.directives(policy)
        self.assertIn("https://www.youtube.com", directives["script-src"])
        self.assertIn("https://s.ytimg.com", directives["script-src"])
        self.assertIn("https://www.youtube-nocookie.com", directives["frame-src"])
        self.assertIn("'self'", directives["default-src"])
        # Framing others is not the same as letting others frame us.
        self.assertEqual(directives["frame-ancestors"], {"'none'"})
        self.assertEqual(directives["object-src"], {"'none'"})

    def test_no_directive_was_widened_to_a_wildcard_or_unsafe_inline(self) -> None:
        for name, values in self.directives(CONTENT_SECURITY_POLICY).items():
            with self.subTest(directive=name):
                self.assertNotIn("*", values)
                self.assertNotIn("'unsafe-inline'", values)
                self.assertNotIn("'unsafe-eval'", values)

    def test_the_meta_tag_and_the_cdn_headers_agree_with_the_server(self) -> None:
        meta = ""
        for line in (WEB_DIR / "index.html").read_text(encoding="utf-8").splitlines():
            if "default-src 'self'" in line and "content=" in line:
                meta = line.split('content="', 1)[1].rsplit('"', 1)[0]
                break
        self.assertTrue(meta, "no CSP meta tag found in index.html")

        cdn = ""
        for line in (WEB_DIR / "_headers").read_text(encoding="utf-8").splitlines():
            if "Content-Security-Policy:" in line:
                cdn = line.split("Content-Security-Policy:", 1)[1].strip()
                break
        self.assertTrue(cdn, "no CSP line found in _headers")

        server = self.directives(CONTENT_SECURITY_POLICY)
        # frame-ancestors is ignored inside a <meta> tag, so the meta copy is the
        # only one allowed to omit it; every other directive must match exactly.
        expected_meta = {k: v for k, v in server.items() if k != "frame-ancestors"}
        self.assertEqual(self.directives(meta), expected_meta)
        self.assertEqual(self.directives(cdn), server)


if __name__ == "__main__":
    unittest.main()
