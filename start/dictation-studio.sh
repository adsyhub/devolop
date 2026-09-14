#!/usr/bin/env bash
# ==============================================================================
# 图形化制课工作台 —— 启动入口
#   项目: /workspace/Develop/dictation
#   实体: dictation/src/studio_server.py
#   地址: http://127.0.0.1:4174   (仅回环，每次请求都要会话令牌)
# 这是"做课"的界面，不是"练课"的界面；练习用 ./dictation.sh (4173)。
# 三种入口: 拖音频 (ASR→翻译讲解→审计→装库) / 粘视频链接 / 拖 PDF (本地 OCR)。
# 参数透传，例如:
#   ./dictation-studio.sh --no-browser
#   ./dictation-studio.sh --port 4175
#   ./dictation-studio.sh --workspace /abs/path/studio-work
#   ./dictation-studio.sh --config /abs/path/providers.json
# 默认工作区 dictation/studio-work/，装课目标为听写课程库，模型 profile 只能取自
# dictation/config/providers.json —— 页面无权自己构造 provider（cli/command 会起子进程）。
# 停止: 在本窗口按 Ctrl+C。
# ==============================================================================
set -euo pipefail

PROJECT_DIR="/workspace/Develop/dictation"
PYTHON="${DICTATION_PYTHON:-/opt/conda/bin/python3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${PYTHON}" "${SCRIPT_DIR}/_cleaner.py" --port 4174 --pattern "studio_server.py" "$@" || true

cd "${PROJECT_DIR}"
exec "${PYTHON}" src/studio_server.py "$@"
