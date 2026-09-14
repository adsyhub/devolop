"""SEC-001 regressions: DNS rebinding, token enforcement, and read protection.

`test_forged_host_and_origin_cannot_write` is the one that matters most. Against
the pre-fix server it passed a forged pair straight through and the write landed
in the learner's database; it is kept here so that hole can never silently
reopen.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from support import RunningServer, write_course


class SecurityContextRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        root = Path(self._temp.name)
        self.manifest = write_course(root / "course")
        self.data_dir = root / "data"
        self.addCleanup(self._temp.cleanup)

    def server(self) -> RunningServer:
        return RunningServer(self.manifest, self.data_dir)

    # ---- DNS rebinding ----

    def test_forged_host_and_origin_cannot_write(self) -> None:
        """The exact attack the old check waved through.

        A page on evil.com whose DNS points at 127.0.0.1 sends a self-consistent
        Host/Origin pair. The old code rebuilt the expected origin *from the Host
        header*, so the pair always agreed and the write succeeded.
        """
        with self.server() as server:
            status, _ = server.request(
                "POST",
                "/api/vocab",
                host="evil.com",
                origin="http://evil.com",
                body={"term": "攻撃"},
            )
            self.assertEqual(status, 403)

            # And nothing was written.
            status, payload = server.request("GET", "/api/vocab")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload)["items"], [])

    def test_forged_host_cannot_read(self) -> None:
        """Reads were not gated at all before: /api/vocab had no check whatsoever."""
        with self.server() as server:
            status, _ = server.request("GET", "/api/vocab", host="evil.com", origin="http://evil.com")
            self.assertEqual(status, 403)

    def test_forged_host_cannot_read_course_content(self) -> None:
        with self.server() as server:
            status, _ = server.request("GET", "/manifest.json", host="evil.com")
            self.assertEqual(status, 403)

    # ---- token enforcement ----

    def test_missing_token_is_rejected_for_reads_and_writes(self) -> None:
        with self.server() as server:
            for method, path, body in [
                ("GET", "/api/vocab", None),
                ("GET", "/api/notes", None),
                ("GET", "/api/activity", None),
                ("POST", "/api/vocab", {"term": "x"}),
            ]:
                with self.subTest(method=method, path=path):
                    status, _ = server.request(method, path, token=None, body=body)
                    self.assertEqual(status, 403)

    def test_wrong_token_is_rejected(self) -> None:
        with self.server() as server:
            status, _ = server.request("GET", "/api/vocab", token="not-the-token")
            self.assertEqual(status, 403)

    def test_valid_host_and_token_are_allowed(self) -> None:
        with self.server() as server:
            status, payload = server.request(
                "POST",
                "/api/vocab",
                origin=f"http://127.0.0.1:{server.port}",
                body={"term": "勉強", "meaning": "study"},
            )
            self.assertEqual(status, 201)
            self.assertEqual(json.loads(payload)["item"]["term"], "勉強")

    def test_localhost_host_header_is_accepted(self) -> None:
        """Browsers send whichever name the user typed; both reach the same socket."""
        with self.server() as server:
            status, _ = server.request("GET", "/api/vocab", host=f"localhost:{server.port}")
            self.assertEqual(status, 200)

    def test_write_from_cross_site_fetch_metadata_is_rejected(self) -> None:
        """Even with a leaked token, a cross-site request is refused."""
        with self.server() as server:
            status, _ = server.request(
                "POST",
                "/api/vocab",
                headers={"Sec-Fetch-Site": "cross-site"},
                body={"term": "x"},
            )
            self.assertEqual(status, 403)

    def test_write_with_foreign_origin_is_rejected(self) -> None:
        with self.server() as server:
            status, _ = server.request("POST", "/api/vocab", origin="http://evil.com", body={"term": "x"})
            self.assertEqual(status, 403)

    # ---- bootstrap ----

    def test_bootstrap_returns_token_to_same_origin_page(self) -> None:
        with self.server() as server:
            status, payload = server.request("GET", "/api/session/bootstrap", token=None)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(payload)["token"], server.token)

    def test_bootstrap_refuses_forged_host(self) -> None:
        with self.server() as server:
            status, _ = server.request("GET", "/api/session/bootstrap", host="evil.com", token=None)
            self.assertEqual(status, 403)

    def test_bootstrap_refuses_cross_site_fetch(self) -> None:
        with self.server() as server:
            status, _ = server.request(
                "GET", "/api/session/bootstrap", token=None, headers={"Sec-Fetch-Site": "cross-site"}
            )
            self.assertEqual(status, 403)

    def test_bootstrap_refuses_navigation(self) -> None:
        """A token must be fetched by script, never landed on as a document."""
        with self.server() as server:
            status, _ = server.request(
                "GET", "/api/session/bootstrap", token=None, headers={"Sec-Fetch-Dest": "document"}
            )
            self.assertEqual(status, 403)

    def test_denial_does_not_echo_the_rejected_headers(self) -> None:
        """A rejection must not confirm what the allowlist contains."""
        with self.server() as server:
            _, payload = server.request("GET", "/api/vocab", host="evil.com")
            self.assertNotIn(b"evil.com", payload)
            self.assertNotIn(str(server.port).encode(), payload)

    def test_token_never_appears_in_a_denied_response(self) -> None:
        with self.server() as server:
            _, payload = server.request("GET", "/api/vocab", token="wrong")
            self.assertNotIn(server.token.encode(), payload)


if __name__ == "__main__":
    unittest.main()
