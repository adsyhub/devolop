#!/usr/bin/env bash
# ==============================================================================
# MiniMax H3 视频生成工作台 Web 前端启动脚本
# 默认端口: 7860
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/workbench.pid"
LOG_FILE="${SCRIPT_DIR}/workbench.log"
PORT="${WORKBENCH_PORT:-7860}"
HOST="${WORKBENCH_HOST:-0.0.0.0}"

# 1. 确保后台 ComfyUI 引擎已就绪
COMFY_RUNNING=0
if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
    COMFY_RUNNING=1
fi

if [ "${COMFY_RUNNING}" -eq 0 ]; then
    echo "检测到 MiniMax H3 ComfyUI 后端尚未运行，正在自动拉起..."
    "${SCRIPT_DIR}/start_comfyui.sh"
    sleep 3
fi

# 2. 检查工作台是否已在运行
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p "${OLD_PID}" > /dev/null 2>&1; then
        echo "MiniMax H3 工作台已经在运行中 (PID: ${OLD_PID})"
        echo "👉 正在自动为您在浏览器中打开: http://localhost:${PORT} ..."
        python3 -c "import webbrowser; webbrowser.open('http://localhost:${PORT}')" 2>/dev/null || true
        exit 0
    else
        rm -f "${PID_FILE}"
    fi
fi

echo "=========================================================="
echo "启动 MiniMax H3 视频生成 Studio 工作台..."
echo "访问地址: http://${HOST}:${PORT}"
echo "后端对接: http://127.0.0.1:8188"
echo "日志文件: ${LOG_FILE}"
echo "=========================================================="

cd "${SCRIPT_DIR}"
nohup /opt/conda/bin/python web_app.py \
    < /dev/null > "${LOG_FILE}" 2>&1 &

NEW_PID=$!
disown "${NEW_PID}" 2>/dev/null || true
echo "${NEW_PID}" > "${PID_FILE}"

sleep 2
if ps -p "${NEW_PID}" > /dev/null 2>&1; then
    echo "工作台启动成功！PID: ${NEW_PID}"
    echo "👉 正在自动为您在浏览器中打开: http://localhost:${PORT} ..."
    python3 -c "import webbrowser; webbrowser.open('http://localhost:${PORT}')" 2>/dev/null || true
else
    echo "启动可能失败，请查看日志: cat ${LOG_FILE}"
fi

