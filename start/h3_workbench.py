#!/usr/bin/env python3
"""MiniMax H3 视频生成工作台 —— 启动入口（Python 版，等价于 h3-workbench.sh）。

项目: /workspace/Develop/H3
实体: H3/service_manager.py 的 ServiceManager.start_all -> web_app.py + ComfyUI/main.py
地址: 工作台 http://127.0.0.1:7860 ，后端 http://127.0.0.1:8188
GPU:  默认沿用 H3/current_gpu.json 里当前绑定的卡（按 UUID，不受枚举顺序影响；
      目前是 GPU 0 的 H100 80GB）。注意 service_manager.py 的 DEFAULT_GPU_ID="3"
      和 start_comfyui.sh 的 CUDA_VISIBLE_DEVICES=3 都注释成 H100，但这台机器上
      GPU 3 是 RTX 6000 Ada 48GB —— 那个默认值已经过时，所以这里不采用它。

后端 ComfyUI 未运行时会自动先拉起。两个服务都在后台运行，pid 写 H3/*.pid，
日志写 H3/comfyui.log 和 H3/workbench.log，本脚本启动完就退出。

这里不重写 bash 脚本里的 pid/日志逻辑，而是复用项目自带的 ServiceManager：
它是纯标准库实现，用的是同一套 pid 文件和端口，所以 .sh 和 .py 两条路可以混用
（用 .sh 起、用 .py 停也没问题）。

用法::

    python h3_workbench.py
    python h3_workbench.py --no-browser
    python h3_workbench.py --gpu 0        # 临时换卡（编号或 UUID）

停止: python h3_stop.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

H3_DIR = Path("/workspace/Develop/H3")
sys.path.insert(0, str(H3_DIR))

from service_manager import ServiceManager  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="启动 MiniMax H3 工作台（含后端 ComfyUI）。")
    parser.add_argument(
        "--gpu",
        default=None,
        help="后端使用的 GPU 编号或 UUID。默认沿用 H3/current_gpu.json 里当前绑定的卡"
        "（目前是 H100 80GB，按 UUID 绑定）。",
    )
    parser.add_argument("--no-browser", action="store_true", help="启动后不自动打开浏览器。")
    args = parser.parse_args(argv)

    manager = ServiceManager(base_dir=H3_DIR)
    print("[start] 启动前先停止清理旧的 H3 工作台与 ComfyUI 后端...", flush=True)
    try:
        manager.stop_all()
        from _cleaner import clean_processes_and_ports
        clean_processes_and_ports(
            patterns=["web_app.py", "ComfyUI/main.py"],
            ports=[7860, 8188],
            verbose=False,
        )
    except Exception as e:
        print(f"[start] 清理旧进程提示: {e}", file=sys.stderr)

    ok = manager.start_all(gpu_id=args.gpu, open_browser=not args.no_browser)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
