#!/usr/bin/env bash
# ==============================================================================
# 听写练习网页 —— 启动入口
#   项目: /workspace/Develop/dictation
#   实体: dictation/start_dictation.py
#   地址: http://127.0.0.1:4173  (端口固定，被占用时会报错而不换端口)
# 参数透传，例如:
#   ./dictation.sh --no-browser
#   ./dictation.sh --port 4180
#   ./dictation.sh --manifest /workspace/Develop/dictation/courses/librivox-test/manifest.json
#   ./dictation.sh --allow-failed-course
# 停止: 在本窗口按 Ctrl+C。若窗口已关闭，服务由子进程 src/serve_course.py 持有
#       4173 端口，需要杀掉那个子进程而不是启动器。
# ==============================================================================
set -euo pipefail

PROJECT_DIR="/workspace/Develop/dictation"
PYTHON="${DICTATION_PYTHON:-/opt/conda/bin/python3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${PYTHON}" "${SCRIPT_DIR}/_cleaner.py" --port 4173 --pattern "start_dictation.py" --pattern "serve_course.py" "$@" || true

cd "${PROJECT_DIR}"
exec "${PYTHON}" start_dictation.py "$@"
