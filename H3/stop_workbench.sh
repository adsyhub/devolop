#!/usr/bin/env bash
# ==============================================================================
# MiniMax H3 视频生成工作台 Web 前端停止脚本
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/workbench.pid"

if [ ! -f "${PID_FILE}" ]; then
    echo "未找到 workbench.pid，检查是否有孤立进程..."
    PIDS=$(pgrep -f "web_app.py" || true)
    if [ -n "${PIDS}" ]; then
        echo "终止 web_app.py 进程: ${PIDS}"
        kill -9 ${PIDS}
    else
        echo "没有运行中的工作台进程。"
    fi
    exit 0
fi

PID=$(cat "${PID_FILE}")
echo "正在停止 MiniMax H3 工作台 (PID: ${PID})..."

if ps -p "${PID}" > /dev/null 2>&1; then
    kill "${PID}" 2>/dev/null || true
    for i in {1..5}; do
        if ! ps -p "${PID}" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    if ps -p "${PID}" > /dev/null 2>&1; then
        echo "进程未退出，强制终止 (SIGKILL)..."
        kill -9 "${PID}" 2>/dev/null || true
    fi
fi

rm -f "${PID_FILE}"
echo "MiniMax H3 工作台已成功停止。"

