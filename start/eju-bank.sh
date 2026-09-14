#!/usr/bin/env bash
# ==============================================================================
# EJU 题库 —— 启动入口
#   项目: /workspace/Develop/eju-question-bank
#   实体: python -m eju_bank serve   (eju_bank/cli.py -> eju_bank/server.py: serve)
#   地址: http://127.0.0.1:8765      (默认仅监听本机)
# 启动后终端会打印一行 "Local administration token: ..."，页面上的管理操作需要它。
# 服务会自己带起独立的制作 worker，退出时一并回收。
# 参数透传给 serve 子命令，例如:
#   ./eju-bank.sh --port 8800
#   ./eju-bank.sh --database /abs/path/eju.db --media-dir /abs/path/media
# 换数据工作区（全局参数必须在子命令之前）用环境变量:
#   EJU_WORKSPACE=/abs/path/to/data ./eju-bank.sh
# 停止: 在本窗口按 Ctrl+C。
# ==============================================================================
set -euo pipefail

PROJECT_DIR="/workspace/Develop/eju-question-bank"
PYTHON="${EJU_PYTHON:-/opt/conda/bin/python3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${PYTHON}" "${SCRIPT_DIR}/_cleaner.py" --port 8765 --pattern "eju_bank.*serve" --pattern "eju_bank.worker" "$@" || true

GLOBAL_ARGS=()
if [ -n "${EJU_WORKSPACE:-}" ]; then
    GLOBAL_ARGS+=(--workspace "${EJU_WORKSPACE}")
fi

cd "${PROJECT_DIR}"
exec "${PYTHON}" -m eju_bank "${GLOBAL_ARGS[@]}" serve "$@"
