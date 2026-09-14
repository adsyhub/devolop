#!/usr/bin/env python3
"""EJU 题库制作台 —— 启动入口（Python 版）。

项目: /workspace/Develop/eju-question-bank
实体: python -m eju_bank serve   (同一服务，制作台在 /studio 路径下)
地址: http://127.0.0.1:8765/studio

这是"做题库"的界面，不是"练题"的界面 —— 练题用 eju_bank.py 的 /practice。
两者同一个服务、同一个数据库，但界面和进度口径分开：制作台管的是"这套卷做到
哪一步了"，学习页面管的是"我练到哪了"。本机访问不需要任何口令。

制作台分四个模块，各是一个页面：

    制课        /studio          拖 PDF 进来，一条流水线做到可练的卷
    课程库      /studio/library  来源清单与单套卷的八个阶段
    复核编辑器  /studio/editor   逐页对照原图核对、签署
    运维        /studio/ops      跨来源的任务、内容问题、备份

**制课**是一键那条：上传题册（有答案册就一起传），确认年度/回次/科目，
挑好模型，后台一条任务依次做完

    登记 → 探测 → 渲染 → 读文本 → 读解答欄号 → 校对·复读异常页
        → 页面合同与机器校验 → 组装与预检 → 校对·复核整卷 → 发布 → 真题详解草稿

四个环节可以各挑各的模型：OCR 首轮、复读异常页、复核整卷、写详解。
档位只能取自 eju-question-bank/config/providers.json，页面无权自己填模型地址；
视觉档位一律只走回环地址 —— 原页图是受版权的原卷扫描，不出本机。

这条路**没有放松任何闸门**：走的是和手签卷一样的 candidate → approve → publish，
签名用保留身份 machine:eju-ocr-pipeline，所以卷子带着 reviewGrade:
MACHINE_ATTESTED 到学习者屏幕上 —— 机器读了什么、人还没看什么，学习者看得到。
想要人工复核就勾「停在待复核」，任务在组装预检后停下，等人去复核编辑器逐页签。
真题详解一律存成 DRAFT，不改成 REVIEWED 就一个字都到不了学习者眼前。

**课程库**是逐步来的地方：某一步单独重跑、结构手填、某一版单独签署都在那里做。
按 docs/PIPELINE.md 的状态流分八个阶段，来源列表每行显示这套卷卡在哪一步：

    ① 登记与授权  ② 导入文件  ③ 探测与渲染  ④ 提取与逐页复核
    ⑤ 签署来源结构  ⑥ 组装与预检  ⑦ 签署整卷  ⑧ 发布

用法（参数原样透传给 serve 子命令）::

    python eju_studio.py
    python eju_studio.py --no-browser
    python eju_studio.py --port 8800
    python eju_studio.py --database /abs/path/eju.db --media-dir /abs/path/media

换数据工作区（--workspace 是全局参数，必须排在子命令之前，故用环境变量传）::

    EJU_WORKSPACE=/abs/path/to/data python eju_studio.py

制课要用到本机推理服务（默认 8100/8101/8102/8103）；哪个档位在线，制课页
右上角的状态条会说。服务没起的档位在下拉里是灰的，选不了但看得见。

停止: 在本窗口按 Ctrl+C。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

PROJECT_DIR = Path("/workspace/Develop/eju-question-bank")
PACKAGE = "eju_bank"
STUDIO_PATH = "/studio"

# PATH 上的 python3 可能指向别的项目的虚拟环境；显式挑解释器，可用 EJU_PYTHON 覆盖。
CANDIDATES = ("/opt/conda/bin/python3", "/usr/bin/python3")

# 服务启动时会打印监听地址；抓到地址就把制作台开出来。
_ADDRESS = re.compile(r"http://(?:127\.0\.0\.1|localhost|0\.0\.0\.0):(\d+)")


def pick_python() -> str:
    override = os.environ.get("EJU_PYTHON")
    if override:
        return override
    for candidate in CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return sys.executable


def open_studio_when_ready(port: int, delay: float = 1.5) -> None:
    """Open the workbench once the server has had a moment to bind."""
    def run() -> None:
        time.sleep(delay)
        webbrowser.open(f"http://127.0.0.1:{port}{STUDIO_PATH}")
    threading.Thread(target=run, daemon=True).start()


def port_from(argv: list[str]) -> int:
    for index, value in enumerate(argv):
        if value == "--port" and index + 1 < len(argv):
            try:
                return int(argv[index + 1])
            except ValueError:
                break
        if value.startswith("--port="):
            try:
                return int(value.split("=", 1)[1])
            except ValueError:
                break
    return 8765


def main(argv: list[str]) -> int:
    if not (PROJECT_DIR / PACKAGE / "__main__.py").exists():
        print(f"找不到 {PACKAGE} 包: {PROJECT_DIR / PACKAGE}", file=sys.stderr)
        return 1

    try:
        from _cleaner import clean_processes_and_ports
        port = port_from(argv)
        clean_processes_and_ports(
            patterns=["eju_bank.*serve", "eju_bank.worker"],
            ports=[port],
        )
    except Exception as e:
        print(f"[start] 清理旧进程提示: {e}", file=sys.stderr)

    argv = list(argv)
    # --no-browser 是本启动器自己的开关，不透传给 serve。
    wants_browser = "--no-browser" not in argv
    argv = [a for a in argv if a != "--no-browser"]

    global_args: list[str] = []
    workspace = os.environ.get("EJU_WORKSPACE")
    if workspace:
        global_args += ["--workspace", workspace]

    cmd = [pick_python(), "-m", PACKAGE, *global_args, "serve", *argv]
    print(f"[start] cd {PROJECT_DIR} && {' '.join(cmd)}", flush=True)
    print(f"[start] 制作台 http://127.0.0.1:{port_from(argv)}{STUDIO_PATH}", flush=True)
    if wants_browser:
        open_studio_when_ready(port_from(argv))
    try:
        # cwd 必须是项目目录：未安装时靠它找到 eju_bank 包，默认数据路径也相对于它。
        return subprocess.call(cmd, cwd=PROJECT_DIR)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
