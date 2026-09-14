#!/usr/bin/env python3
"""MiniMax H3 / ComfyUI 后端 —— 启动入口（Python 版，等价于 h3-comfyui.sh）。

项目: /workspace/Develop/H3
实体: H3/service_manager.py 的 ServiceManager.start_backend -> ComfyUI/main.py
地址: http://127.0.0.1:8188
GPU:  默认沿用 H3/current_gpu.json 里当前绑定的卡（按 UUID，不受枚举顺序影响；
      目前是 GPU 0 的 H100 80GB）。service_manager.py 的 DEFAULT_GPU_ID="3" 和
      start_comfyui.sh 的 CUDA_VISIBLE_DEVICES=3 都注释成 H100，但这台机器上
      GPU 3 是 RTX 6000 Ada 48GB —— 那个默认值已过时，所以这里不采用它。
输出: /data/storage/outputs/minimax-h3
后台运行: pid 写 H3/comfyui.pid，日志写 H3/comfyui.log

h3_workbench.py 会自动拉起后端，只想单独跑引擎时才用这个。

用法::

    python h3_comfyui.py
    python h3_comfyui.py --gpu 0          # 临时换卡（编号或 UUID）
    python h3_comfyui.py --port 8288

停止: python h3_stop.py comfyui
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

H3_DIR = Path("/workspace/Develop/H3")
sys.path.insert(0, str(H3_DIR))

from service_manager import DEFAULT_BACKEND_PORT, ServiceManager  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="只启动 MiniMax H3 的 ComfyUI 后端引擎。")
    parser.add_argument(
        "--gpu",
        default=None,
        help="使用的 GPU 编号或 UUID。默认沿用 H3/current_gpu.json 里当前绑定的卡"
        "（目前是 H100 80GB，按 UUID 绑定）。",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_BACKEND_PORT, help=f"监听端口，默认 {DEFAULT_BACKEND_PORT}。"
    )
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0。")
    args = parser.parse_args(argv)

    manager = ServiceManager(base_dir=H3_DIR)
    print("[start] 启动前先停止清理旧的 ComfyUI 后端...", flush=True)
    try:
        manager.stop_backend()
        from _cleaner import clean_processes_and_ports
        clean_processes_and_ports(
            patterns=["ComfyUI/main.py"],
            ports=[args.port],
            verbose=False,
        )
    except Exception as e:
        print(f"[start] 清理旧进程提示: {e}", file=sys.stderr)

    ok = manager.start_backend(gpu_id=args.gpu, port=args.port, host=args.host)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
