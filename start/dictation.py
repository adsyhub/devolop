#!/usr/bin/env python3
"""听写练习网页 —— 启动入口（Python 版，等价于 dictation.sh）。

项目: /workspace/Develop/dictation
实体: dictation/start_dictation.py
地址: http://127.0.0.1:4173  (端口固定，被占用时会报错而不换端口)

用法（参数原样透传给 start_dictation.py）::

    python dictation.py
    python dictation.py --no-browser
    python dictation.py --port 4180
    python dictation.py --manifest /workspace/Develop/dictation/courses/librivox-test/manifest.json
    python dictation.py --allow-failed-course

停止: 在本窗口按 Ctrl+C。若窗口已被强杀，端口 4173 由启动器派生的子进程
src/serve_course.py 持有，要杀那个子进程而不是启动器，并等几秒再重启。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("/workspace/Develop/dictation")
ENTRY = PROJECT_DIR / "start_dictation.py"

# 播放器和启动器只用标准库，但 PATH 上的 python3 可能指向别的项目的虚拟环境，
# 所以显式挑一个可用的 3.10+ 解释器。可用 DICTATION_PYTHON 覆盖。
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

    try:
        from _cleaner import clean_processes_and_ports, extract_port
        port = extract_port(argv, 4173)
        clean_processes_and_ports(
            patterns=["start_dictation.py", "serve_course.py"],
            ports=[port],
        )
    except Exception as e:
        print(f"[start] 清理旧进程提示: {e}", file=sys.stderr)

    cmd = [pick_python(), ENTRY.name, *argv]
    print(f"[start] cd {PROJECT_DIR} && {' '.join(cmd)}", flush=True)
    try:
        # cwd 必须是项目目录：start_dictation.py 按自身位置定位 src/ 和 courses/。
        return subprocess.call(cmd, cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
