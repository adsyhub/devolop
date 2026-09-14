#!/usr/bin/env bash
# ==============================================================================
# MiniMax H3 视频生成工作台 —— 启动入口（日常用这个）
#   项目: /workspace/Develop/H3
#   实体: H3/start_workbench.sh -> H3/web_app.py
#   地址: http://127.0.0.1:7860
#   依赖: 会自动检测并拉起后端 ComfyUI (http://127.0.0.1:8188)
#   后台运行: PID 写 H3/workbench.pid，日志 H3/workbench.log
# 用环境变量配置（原脚本不接受命令行参数）:
#   WORKBENCH_PORT=7870 ./h3-workbench.sh
#   WORKBENCH_HOST=127.0.0.1 ./h3-workbench.sh
# 想用命令行参数（--gpu / --no-browser）请改用 Python 版: python h3_workbench.py
# 停止: ./h3-stop.sh
# ==============================================================================
set -euo pipefail

usage() { awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"; }

case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") ;;
    *)
        echo "h3-workbench.sh 不接受命令行参数：底层的 H3/start_workbench.sh 只读环境变量。" >&2
        echo "用 WORKBENCH_PORT=... 这类环境变量，或改用 python h3_workbench.py --gpu/--no-browser。" >&2
        exit 2
        ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[start] 启动前先停止清理旧的 H3 工作台与 ComfyUI 后端..."
"${SCRIPT_DIR}/h3-stop.sh" all >/dev/null 2>&1 || true
"${PYTHON:-/opt/conda/bin/python3}" "${SCRIPT_DIR}/_cleaner.py" --port 7860 --port 8188 --pattern "web_app.py" --pattern "ComfyUI/main.py" || true

exec /workspace/Develop/H3/start_workbench.sh
