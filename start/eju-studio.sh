#!/usr/bin/env bash
# EJU 题库制作台 —— 启动入口（Shell 版，等价于 eju_studio.py）。
#
# 项目: /workspace/Develop/eju-question-bank
# 地址: http://127.0.0.1:8765/studio   （本机访问不需要口令）
#
# 用法:
#   ./eju-studio.sh
#   ./eju-studio.sh --port 8800
#   EJU_WORKSPACE=/abs/path/to/data ./eju-studio.sh
#
# 停止: Ctrl+C
set -euo pipefail
exec "${EJU_PYTHON:-/opt/conda/bin/python3}" "$(dirname "$0")/eju_studio.py" "$@"
