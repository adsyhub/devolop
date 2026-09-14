#!/usr/bin/env python3
"""图形化制课工作台 —— 启动入口（Python 版，等价于 dictation-studio.sh）。

项目: /workspace/Develop/dictation
实体: dictation/src/studio_server.py
地址: http://127.0.0.1:4174   (仅回环，每次请求都要会话令牌)

这是"做课"的界面，不是"练课"的界面 —— 练习用 dictation.py (4173)。
三种入口: 拖音频 (ASR → 翻译讲解 → 质量审计 → 装入课程库) / 粘视频链接 / 拖 PDF (本地 OCR)。

用法（参数原样透传给 studio_server.py）::

    python dictation_studio.py
    python dictation_studio.py --no-browser
    python dictation_studio.py --port 4175
    python dictation_studio.py --workspace /abs/path/studio-work
    python dictation_studio.py --config /abs/path/providers.json

默认工作区是 dictation/studio-work/；模型 profile 只能取自 dictation/config/providers.json，
页面无权自己构造 provider（`cli` / `command` 两种 provider 会起子进程）。
没有配置文件时工作台会照常启动，但没有可选的 profile。

停止: 在本窗口按 Ctrl+C。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("/workspace/Develop/dictation")
ENTRY = PROJECT_DIR / "src" / "studio_server.py"

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
        port = extract_port(argv, 4174)
        clean_processes_and_ports(
            patterns=["studio_server.py"],
            ports=[port],
        )
    except Exception as e:
        print(f"[start] 清理旧进程提示: {e}", file=sys.stderr)

    cmd = [pick_python(), "src/studio_server.py", *argv]
    print(f"[start] cd {PROJECT_DIR} && {' '.join(cmd)}", flush=True)
    try:
        # cwd 用项目目录：studio_server.py 按 __file__ 定位 PROJECT_DIR，但它的
        # 兄弟模块是扁平 import，必须由脚本路径把 src/ 带进 sys.path。
        return subprocess.call(cmd, cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
