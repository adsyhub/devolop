#!/usr/bin/env bash
# ==============================================================================
# MiniMax-H3 / ComfyUI 启动脚本
# 默认使用单卡 80GB VRAM 的 NVIDIA H100 (GPU 3)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFYUI_DIR="${SCRIPT_DIR}/ComfyUI"
LOG_FILE="${SCRIPT_DIR}/comfyui.log"
PID_FILE="${SCRIPT_DIR}/comfyui.pid"

# 默认优先使用 GPU 3 (NVIDIA H100 PCIe 80GB)
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-3}"
PORT="${PORT:-8188}"
HOST="${HOST:-0.0.0.0}"
OUTPUT_DIR="/data/storage/outputs/minimax-h3"

mkdir -p "${OUTPUT_DIR}"

if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p "${OLD_PID}" > /dev/null 2>&1; then
        echo "ComfyUI 已经在运行中 (PID: ${OLD_PID})，端口: ${PORT}"
        echo "若需停止，请执行: ./stop_comfyui.sh"
        exit 0
    else
        rm -f "${PID_FILE}"
    fi
fi

# 检查是否有其它同名进程
EXISTING_PID=$(pgrep -f "ComfyUI/main.py" || true)
if [ -n "${EXISTING_PID}" ]; then
    echo "发现正在运行的 ComfyUI 进程 (PID: ${EXISTING_PID})"
    echo "${EXISTING_PID}" > "${PID_FILE}"
    exit 0
fi

echo "=========================================================="
echo "启动 MiniMax-H3 ComfyUI 服务..."
echo "GPU 指定: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
echo "输出目录: ${OUTPUT_DIR}"
echo "监听地址: http://${HOST}:${PORT}"
echo "日志文件: ${LOG_FILE}"
echo "=========================================================="

cd "${COMFYUI_DIR}"
nohup /opt/conda/bin/python main.py \
    --listen "${HOST}" \
    --port "${PORT}" \
    --output-directory "${OUTPUT_DIR}" \
    < /dev/null > "${LOG_FILE}" 2>&1 &

NEW_PID=$!
disown "${NEW_PID}" 2>/dev/null || true
echo "${NEW_PID}" > "${PID_FILE}"
echo "服务已在后台启动，PID: ${NEW_PID}"
echo "可使用 'tail -f ${LOG_FILE}' 查看实时启动日志"
