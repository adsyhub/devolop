#!/usr/bin/env bash
# ==============================================================================
# MiniMax H3 / ComfyUI 后端 —— 启动入口（只需要后端引擎时用）
#   项目: /workspace/Develop/H3
#   实体: H3/start_comfyui.sh -> H3/ComfyUI/main.py
#   地址: http://127.0.0.1:8188
#   GPU:  start_comfyui.sh 写死 CUDA_VISIBLE_DEVICES=3 并注释为 H100，但这台机器上
#         GPU 3 是 RTX 6000 Ada 48GB，H100 80GB 是 GPU 0（用 ./h3-stop.sh --status 核对）。
#         要用 H100 请显式指定: CUDA_VISIBLE_DEVICES=0 ./h3-comfyui.sh
#   输出: /data/storage/outputs/minimax-h3
#   后台运行: PID 写 H3/comfyui.pid，日志 H3/comfyui.log
# 用环境变量配置（原脚本不接受命令行参数）:
#   CUDA_VISIBLE_DEVICES=0 PORT=8288 HOST=127.0.0.1 ./h3-comfyui.sh
# 想用命令行参数（--gpu / --port / --host）请改用: python h3_comfyui.py
# 注意: h3-workbench.sh 会自动拉起它，一般不必单独启动。
# 停止: ./h3-stop.sh comfyui
# ==============================================================================
set -euo pipefail

usage() { awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"; }

case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") ;;
    *)
        echo "h3-comfyui.sh 不接受命令行参数：底层的 H3/start_comfyui.sh 只读环境变量。" >&2
        echo "用 CUDA_VISIBLE_DEVICES=/PORT=/HOST=，或改用 python h3_comfyui.py --gpu/--port/--host。" >&2
        exit 2
        ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[start] 启动前先停止清理旧的 ComfyUI 后端..."
"${SCRIPT_DIR}/h3-stop.sh" comfyui >/dev/null 2>&1 || true
"${PYTHON:-/opt/conda/bin/python3}" "${SCRIPT_DIR}/_cleaner.py" --port "${PORT:-8188}" --pattern "ComfyUI/main.py" || true

exec /workspace/Develop/H3/start_comfyui.sh
