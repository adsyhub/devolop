#!/usr/bin/env python3
"""Expose Antigravity's one-shot CLI through the pipeline's stdin/stdout contract."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


def find_agy() -> str:
    installed = shutil.which("agy")
    if installed:
        return installed
    bundled = Path.home() / ".gemini" / "bin" / "agy"
    if bundled.is_file() and os.access(bundled, os.X_OK):
        return str(bundled)
    raise FileNotFoundError("Antigravity CLI (agy) is not installed")


def main() -> int:
    prompt = sys.stdin.read()
    if not prompt.strip():
        print("Antigravity bridge received an empty prompt", file=sys.stderr)
        return 2

    command = [
        find_agy(),
        "--output-format",
        "text",
        "--sandbox",
        "--dangerously-skip-permissions",
        "--disable-slash-commands",
        "--print-timeout",
        "15m",
    ]
    filtered_args: list[str] = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg == "--mode":
            skip_next = True
            continue
        if arg.startswith("--mode="):
            continue
        filtered_args.append(arg)
    command.extend(filtered_args)
    command.append(f"--print={prompt}")
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=920,
        check=False,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if stdout:
        sys.stdout.write(stdout)
    if stderr:
        sys.stderr.write(stderr)

    combined = f"{stdout}\n{stderr}".lower()
    if "authentication required" in combined or "please sign in" in combined:
        return 3
    return completed.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
