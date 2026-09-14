#!/usr/bin/env bash
# ==============================================================================
# 逐句人工复核控制台 —— 启动入口
#   项目: /workspace/Develop/dictation
#   实体: dictation/src/review_server.py
#   地址: http://127.0.0.1:4180   (仅回环)
# 用途: 对一门课逐句听审、勾字段、留签名，产出人工复核记录。
# --manifest 和 --review 是必填参数:
#   ./dictation-review.sh \
#     --manifest /workspace/Develop/dictation/courses/2010-12-N2/manifest.json \
#     --review   /workspace/Develop/dictation/out/2010-12-N2-review.json \
#     --reviewer "你的名字"        # 仅在新建复核文件时需要
# 可选: --organization、--host、--port (默认 4180)
# 停止: 在本窗口按 Ctrl+C。
# ==============================================================================
set -euo pipefail

PROJECT_DIR="/workspace/Develop/dictation"
PYTHON="${DICTATION_PYTHON:-/opt/conda/bin/python3}"

if [ "$#" -eq 0 ]; then
    echo "需要 --manifest 和 --review 两个参数。用法见本文件顶部注释，或执行:" >&2
    echo "  $0 --help" >&2
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${PYTHON}" "${SCRIPT_DIR}/_cleaner.py" --port 4180 --pattern "review_server.py" "$@" || true

cd "${PROJECT_DIR}"
exec "${PYTHON}" src/review_server.py "$@"
