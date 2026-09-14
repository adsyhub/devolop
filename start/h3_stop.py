#!/usr/bin/env python3
"""MiniMax H3 —— 停止入口（Python 版，等价于 h3-stop.sh）。

实体: H3/service_manager.py 的 ServiceManager.stop_all / stop_workbench / stop_backend
先 SIGTERM，等不退再 SIGKILL，并清理 pid 文件。

用法::

    python h3_stop.py              # 工作台和后端都停（默认）
    python h3_stop.py workbench    # 只停 7860 工作台
    python h3_stop.py comfyui      # 只停 8188 后端
    python h3_stop.py --status     # 只看状态，不停任何服务
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

H3_DIR = Path("/workspace/Develop/H3")
sys.path.insert(0, str(H3_DIR))

from service_manager import ServiceManager  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="停止 MiniMax H3 服务。")
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=["all", "workbench", "comfyui"],
        help="要停的服务，默认 all。",
    )
    parser.add_argument("--status", action="store_true", help="只打印各服务状态，不执行停止。")
    args = parser.parse_args(argv)

    manager = ServiceManager(base_dir=H3_DIR)

    if args.status:
        manager.print_status()
        return 0

    if args.target == "workbench":
        ok = manager.stop_workbench()
    elif args.target == "comfyui":
        ok = manager.stop_backend()
    else:
        ok = manager.stop_all()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
