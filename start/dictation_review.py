#!/usr/bin/env python3
"""逐句人工复核控制台 —— 启动入口（Python 版，等价于 dictation-review.sh）。

项目: /workspace/Develop/dictation
实体: dictation/src/review_server.py
地址: http://127.0.0.1:4180   (仅回环)

用途: 对一门课逐句听审、勾字段、留签名，产出人工复核记录。

--manifest 和 --review 是必填参数::

    python dictation_review.py \\
        --manifest /workspace/Develop/dictation/courses/2010-12-N2/manifest.json \\
        --review   /workspace/Develop/dictation/out/2010-12-N2-review.json \\
        --reviewer "你的名字"          # 仅在新建复核文件时需要

可选参数: --organization、--host、--port（默认 4180）。

停止: 在本窗口按 Ctrl+C。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("/workspace/Develop/dictation")
ENTRY = PROJECT_DIR / "src" / "review_server.py"

CANDIDATES = ("/opt/conda/bin/python3", "/usr/bin/python3")


def pick_python() -> str:
    override = os.environ.get("DICTATION_PYTHON")
    if override:
        return override
    for candidate in CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return sys.executable


def main(argv: list[str]) -> int:
    if not ENTRY.exists():
        print(f"找不到启动入口: {ENTRY}", file=sys.stderr)
        return 1
    if not argv:
        print(__doc__, file=sys.stderr)
        print("需要 --manifest 和 --review 两个参数。", file=sys.stderr)
        return 2

    try:
        from _cleaner import clean_processes_and_ports, extract_port
        port = extract_port(argv, 4180)
        clean_processes_and_ports(
            patterns=["review_server.py"],
            ports=[port],
        )
    except Exception as e:
        print(f"[start] 清理旧进程提示: {e}", file=sys.stderr)

    cmd = [pick_python(), "src/review_server.py", *argv]
    print(f"[start] cd {PROJECT_DIR} && {' '.join(cmd)}", flush=True)
    try:
        return subprocess.call(cmd, cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
