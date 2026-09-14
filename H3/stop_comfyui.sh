#!/usr/bin/env bash
# ==============================================================================
# MiniMax-H3 / ComfyUI 停止脚本
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/comfyui.pid"

if [ ! -f "${PID_FILE}" ]; then
    echo "未发现 pid 文件 (${PID_FILE})，尝试通过进程名查找..."
    PIDS=$(pgrep -f "ComfyUI/main.py" || true)
    if [ -n "${PIDS}" ]; then
        echo "发现运行中的 ComfyUI 进程: ${PIDS}，正在停止..."
        kill ${PIDS} || true
        echo "已发送停止信号"
    else
        echo "没有正在运行的 ComfyUI 进程"
    fi
    exit 0
fi

PID=$(cat "${PID_FILE}")
if ps -p "${PID}" > /dev/null 2>&1; then
    echo "正在停止 ComfyUI (PID: ${PID})..."
    kill "${PID}"
    for i in {1..10}; do
        if ! ps -p "${PID}" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    if ps -p "${PID}" > /dev/null 2>&1; then
        echo "进程未退出，强制终止 (SIGKILL)..."
        kill -9 "${PID}" || true
    fi
    rm -f "${PID_FILE}"
    echo "ComfyUI 服务已成功停止"
else
    echo "PID ${PID} 对应进程不存在，清理 pid 文件"
    rm -f "${PID_FILE}"
fi

