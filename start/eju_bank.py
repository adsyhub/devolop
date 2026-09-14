#!/usr/bin/env python3
"""EJU 题库 —— 启动入口（Python 版，等价于 eju-bank.sh）。

项目: /workspace/Develop/eju-question-bank
实体: python -m eju_bank serve   (eju_bank/cli.py -> eju_bank/server.py: serve)
地址: http://127.0.0.1:8765      (默认仅监听本机)

启动后终端会打印一行 "Local administration token: ..."，网页里的管理操作需要它。
服务会自己带起独立的制作 worker 子进程，退出时一并回收。

用法（参数原样透传给 serve 子命令）::

    python eju_bank.py
    python eju_bank.py --port 8800
    python eju_bank.py --database /abs/path/eju.db --media-dir /abs/path/media

换数据工作区（--workspace 是全局参数，必须排在子命令之前，故用环境变量传）::

    EJU_WORKSPACE=/abs/path/to/data python eju_bank.py

停止: 在本窗口按 Ctrl+C。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("/workspace/Develop/eju-question-bank")
PACKAGE = "eju_bank"

# PATH 上的 python3 可能指向别的项目的虚拟环境；这里显式挑解释器，可用 EJU_PYTHON 覆盖。
CANDIDATES = ("/opt/conda/bin/python3", "/usr/bin/python3")


def pick_python() -> str:
    override = os.environ.get("EJU_PYTHON")
    if override:
        return override
    for candidate in CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return sys.executable


def main(argv: list[str]) -> int:
    if not (PROJECT_DIR / PACKAGE / "__main__.py").exists():
        print(f"找不到 {PACKAGE} 包: {PROJECT_DIR / PACKAGE}", file=sys.stderr)
        return 1

    try:
        from _cleaner import clean_processes_and_ports, extract_port
        port = extract_port(argv, 8765)
        clean_processes_and_ports(
            patterns=["eju_bank.*serve", "eju_bank.worker"],
            ports=[port],
        )
    except Exception as e:
        print(f"[start] 清理旧进程提示: {e}", file=sys.stderr)

    global_args: list[str] = []
    workspace = os.environ.get("EJU_WORKSPACE")
    if workspace:
        global_args += ["--workspace", workspace]

    cmd = [pick_python(), "-m", PACKAGE, *global_args, "serve", *argv]
    print(f"[start] cd {PROJECT_DIR} && {' '.join(cmd)}", flush=True)
    try:
        # cwd 必须是项目目录：未安装时靠它找到 eju_bank 包，默认数据路径也相对于它。
        return subprocess.call(cmd, cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
