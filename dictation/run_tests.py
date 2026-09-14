"""FND-002A: the single test entry point.

ADR-BUILD-001 (Python half): stay on stdlib `unittest`. The player itself runs on
the standard library alone, and the plan's requirement is one main entry point,
not a specific runner — adding pytest would buy little here and would make the
test suite the only thing in the project needing an install step.

    python run_tests.py            # everything
    python run_tests.py security   # only tests/test_security*.py

Exits non-zero on any failure, and treats a suite that discovered nothing as a
failure too: "0 tests, 0 failures" is how this project previously reported that
its entire suite had been deleted.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_DIR / "tests"


def run_python(pattern: str) -> tuple[int, int]:
    sys.path.insert(0, str(TESTS_DIR))
    sys.path.insert(0, str(PROJECT_DIR / "src"))

    suite = unittest.defaultTestLoader.discover(str(TESTS_DIR), pattern=pattern)
    count = suite.countTestCases()
    if count == 0:
        print(f"NO PYTHON TESTS RAN (pattern {pattern!r}) — refusing to report success.", file=sys.stderr)
        return 1, 0

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print(f"\n{len(result.skipped)} skipped:")
        for test, reason in result.skipped:
            print(f"  {test}: {reason}")
    return (0 if result.wasSuccessful() else 1), count


def run_node() -> tuple[int, str]:
    """Run the service-worker tests, which need a JavaScript runtime.

    Node is not required to *run* the player — the whole point of the project is
    that it works on the standard library alone — so its absence is reported
    loudly rather than treated as a pass. A suite that quietly skips the only
    tests covering the cache and Range logic is how this project ended up with
    zero tests in the first place.
    """
    if shutil.which("node") is None:
        return 1, "node not found: the service-worker tests could not run"
    print("\n" + "=" * 70)
    print("service worker (node:test)")
    print("=" * 70)
    sys.stdout.flush()  # otherwise the child's output lands above this header
    completed = subprocess.run(
        ["node", "--test", "tests/*.test.mjs"],
        cwd=PROJECT_DIR,
    )
    return completed.returncode, ""


def main(argv: list[str]) -> int:
    selector = argv[0] if argv else None
    if selector == "browser":
        return subprocess.run([sys.executable,str(PROJECT_DIR / "scripts/verify_lexicon_browser.py")],cwd=PROJECT_DIR).returncode
    pattern = f"test_{selector}*.py" if selector else "test_*.py"

    python_status, python_count = run_python(pattern)

    # A selector means "run this slice"; only the full run insists on both halves.
    if selector:
        return python_status

    node_status, node_note = run_node()
    if node_note:
        print(f"\nWARNING: {node_note}", file=sys.stderr)

    print(f"\npython: {python_count} tests, {'ok' if python_status == 0 else 'FAILED'}")
    print(f"node  : {'ok' if node_status == 0 else 'FAILED'}")
    return python_status or node_status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
