"""Range regressions for the server side (206 / 416 / suffix ranges).

Deliberately runs against a 32-byte fixture rather than the real course audio, so
the arithmetic is checkable by eye and the suite stays fast.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from support import FIXTURE_AUDIO, RunningServer, write_course


class RangeRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        root = Path(self._temp.name)
        self.manifest = write_course(root / "course")
        self.data_dir = root / "data"
        self.addCleanup(self._temp.cleanup)

    def range_request(self, server: RunningServer, value: str) -> tuple[int, bytes]:
        return server.request("GET", "/audio.mp3", headers={"Range": value})

    def test_explicit_range_returns_exactly_those_bytes(self) -> None:
        with RunningServer(self.manifest, self.data_dir) as server:
            status, body = self.range_request(server, "bytes=4-9")
            self.assertEqual(status, 206)
            self.assertEqual(body, FIXTURE_AUDIO[4:10])

    def test_open_ended_range_runs_to_the_end(self) -> None:
        with RunningServer(self.manifest, self.data_dir) as server:
            status, body = self.range_request(server, "bytes=28-")
            self.assertEqual(status, 206)
            self.assertEqual(body, FIXTURE_AUDIO[28:])

    def test_suffix_range_returns_the_tail(self) -> None:
        with RunningServer(self.manifest, self.data_dir) as server:
            status, body = self.range_request(server, "bytes=-5")
            self.assertEqual(status, 206)
            self.assertEqual(body, FIXTURE_AUDIO[-5:])

    def test_range_past_the_end_is_unsatisfiable(self) -> None:
        with RunningServer(self.manifest, self.data_dir) as server:
            status, _ = self.range_request(server, "bytes=999-1000")
            self.assertEqual(status, 416)

    def test_repeated_seeks_stay_consistent(self) -> None:
        with RunningServer(self.manifest, self.data_dir) as server:
            for start in range(0, 32, 7):
                with self.subTest(start=start):
                    status, body = self.range_request(server, f"bytes={start}-{start + 3}")
                    self.assertEqual(status, 206)
                    self.assertEqual(body, FIXTURE_AUDIO[start:start + 4])

    def test_range_request_still_requires_a_valid_host(self) -> None:
        with RunningServer(self.manifest, self.data_dir) as server:
            status, _ = server.request(
                "GET", "/audio.mp3", host="evil.com", headers={"Range": "bytes=0-3"}
            )
            self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
