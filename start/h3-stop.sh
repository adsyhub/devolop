#!/usr/bin/env bash
# ==============================================================================
# MiniMax H3 —— 停止入口
#   实体: H3/stop_workbench.sh、H3/stop_comfyui.sh
# 用法:
#   ./h3-stop.sh               工作台和后端都停（默认）
#   ./h3-stop.sh workbench     只停 7860 工作台
#   ./h3-stop.sh comfyui       只停 8188 后端
#   ./h3-stop.sh --status      只看两个服务和四张卡的状态，不停任何服务
# ==============================================================================
set -euo pipefail

H3_DIR="/workspace/Develop/H3"

usage() { awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"; }

case "${1:-all}" in
    -h|--help) usage; exit 0 ;;
    --status)  exec /opt/conda/bin/python3 "${H3_DIR}/service_manager.py" status ;;
    workbench) exec "${H3_DIR}/stop_workbench.sh" ;;
    comfyui)   exec "${H3_DIR}/stop_comfyui.sh" ;;
    all)       "${H3_DIR}/stop_workbench.sh"; exec "${H3_DIR}/stop_comfyui.sh" ;;
    *)
        echo "未知参数: $1" >&2
        usage >&2
        exit 2
        ;;
esac
