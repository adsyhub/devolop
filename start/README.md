# 启动入口总目录

`/workspace/Develop` 下所有项目的启动代码都在这里集中登记。每个服务都有 **`.sh` 和 `.py`
两个等价入口**，用哪个都行，参数原样透传给真正的入口程序：

- `.sh` —— `./dictation.sh`，Linux/macOS 终端最省事。
- `.py` —— `python dictation.py`，不依赖 bash（Windows 也能跑），行为与 `.sh` 一致。

两者操作的是同一套 pid 文件和端口，可以混用：用 `.sh` 起、用 `.py` 停没有问题。
所有启动器在拉起新服务前均会自动检测并安全清理对应的旧进程、残留 worker 并释放端口，避免端口冲突。

**这里放的是启动器，不是被搬过来的原文件。** 三个项目的启动代码都用
`Path(__file__).parent` / `SCRIPT_DIR` 定位自己的项目根目录（找 `src/`、`courses/`、
`ComfyUI/`、`library/eju.db` 等），文件一旦离开原目录就会全部失效。所以本目录的脚本
`cd` 回项目目录再执行原入口——效果与在项目里手敲一致，同时启动代码只有一份，不会分叉。

## 一览

| 项目 | shell 入口 | python 入口 | 地址 | 真正的入口 | 停止 |
| --- | --- | --- | --- | --- | --- |
| 听写练习网页（练课） | `./dictation.sh` | `python dictation.py` | http://127.0.0.1:4173 | [dictation/start_dictation.py](../dictation/start_dictation.py) | 窗口内 `Ctrl+C` |
| 制课工作台（做课） | `./dictation-studio.sh` | `python dictation_studio.py` | http://127.0.0.1:4174 | [dictation/src/studio_server.py](../dictation/src/studio_server.py) | 窗口内 `Ctrl+C` |
| 人工复核控制台 | `./dictation-review.sh` | `python dictation_review.py` | http://127.0.0.1:4180 | [dictation/src/review_server.py](../dictation/src/review_server.py) | 窗口内 `Ctrl+C` |
| EJU 题库 | `./eju-bank.sh` | `python eju_bank.py` | http://127.0.0.1:8765 | [eju_bank/cli.py](../eju-question-bank/eju_bank/cli.py) → `serve` | 窗口内 `Ctrl+C` |
| H3 视频工作台 | `./h3-workbench.sh` | `python h3_workbench.py` | http://127.0.0.1:7860 | [H3/web_app.py](../H3/web_app.py) | `./h3-stop.sh` / `python h3_stop.py` |
| H3 的 ComfyUI 后端 | `./h3-comfyui.sh` | `python h3_comfyui.py` | http://127.0.0.1:8188 | [H3/ComfyUI/main.py](../H3/ComfyUI/main.py) | `./h3-stop.sh comfyui` |

端口分配（都只监听回环）：**4173 练课 / 4174 做课 / 4180 复核 / 7860 H3 工作台 /
8188 ComfyUI / 8765 EJU**。4173 和 4174 是两个不同的界面，别弄混：在 4174 把课做好装进
课程库，再用 4173 打开来练。

两套入口走的是项目里两条已有的实现：`.sh` 调 [H3/start_workbench.sh](../H3/start_workbench.sh)、
[H3/start_comfyui.sh](../H3/start_comfyui.sh)，`.py` 调
[H3/service_manager.py](../H3/service_manager.py) 的 `ServiceManager`（纯标准库）。
启动逻辑没有被抄成第三份。

H3 两个服务在后台运行（`nohup` + pid 文件），前两个在前台运行，关掉窗口即结束。

## 听写练习 —— `./dictation.sh`

```bash
./dictation.sh                       # 打开默认的 2010-12-N2 课程并自动开浏览器
./dictation.sh --no-browser          # 只起服务
./dictation.sh --manifest /workspace/Develop/dictation/courses/librivox-test/manifest.json
./dictation.sh --allow-failed-course # 明知内容有问题时强行打开（页面会一直显示红色警告）

python dictation.py                  # 同上，Python 版
python dictation.py --no-browser
```

- 端口固定 4173，**被占用时会报错退出，不会自动换端口**——学习进度按 origin（含端口）
  隔离，换端口等于开一份空进度。
- 课程审计有 1 个以上错误就拒绝打开，报 `E-COURSE-QUALITY`。
- 服务真正的监听者是启动器 `spawn` 出来的子进程 `src/serve_course.py`。窗口被强杀后端口
  仍被占用时，要杀那个**子进程**，而不是启动器；杀完等几秒再启，否则端口还没释放。
- 生词/笔记/打卡写在 `/root/.local/share/dictation-preview/learning.sqlite3`（真实数据）。

## 制课工作台 —— `./dictation-studio.sh`

"做课"的图形界面，不想记一堆命令行参数就用它。

```bash
./dictation-studio.sh                # 打开 http://127.0.0.1:4174
./dictation-studio.sh --no-browser
./dictation-studio.sh --port 4175
./dictation-studio.sh --workspace /abs/path/studio-work

python dictation_studio.py           # 同上，Python 版
```

- 三种入口：拖音频（ASR → 翻译讲解 → 质量审计 → 一键装入课程库）、粘贴视频链接
  （站点字幕 + 本地 ASR 双源核验）、拖 PDF（本地多模型 OCR → 异常页复核 → 结构化草稿）。
- 默认工作区 `dictation/studio-work/`（uploads / builds / analyses 都在里面）。
- **模型 profile 只能从 `dictation/config/providers.json` 里已有的条目里选**，页面无权自己
  构造 provider —— `cli` 和 `command` 两种 provider 会起子进程，让网页指定命令等于把同源
  立足点变成任意代码执行。该文件已存在，不用先复制示例。
- 页面加载时会实时检测模型可用性；启动本地模型或装好 CLI 后点右上角「刷新模型状态」。
- 课做好后用 `./dictation.sh --manifest .../courses/<课程名>/manifest.json` 打开来练。

## 人工复核控制台 —— `./dictation-review.sh`

逐句听审、勾字段、留签名，产出人工复核记录。`--manifest` 和 `--review` 必填：

```bash
./dictation-review.sh \
  --manifest /workspace/Develop/dictation/courses/2010-12-N2/manifest.json \
  --review   /workspace/Develop/dictation/out/2010-12-N2-review.json \
  --reviewer "你的名字"              # 仅在新建复核文件时需要

python dictation_review.py --manifest ... --review ...   # 同上，Python 版
```

不带参数执行会直接打印用法并退出，不会起一个半残的服务。

## EJU 题库 —— `./eju-bank.sh`

```bash
./eju-bank.sh                        # 8765 端口，仅监听本机
./eju-bank.sh --port 8800
EJU_WORKSPACE=/abs/path/data ./eju-bank.sh   # 换数据工作区

python eju_bank.py                   # 同上，Python 版
python eju_bank.py --port 8800
```

- 终端会打印 `Local administration token: ...`，网页里的管理操作需要粘贴它。
- 会自己起一个独立的制作 worker 子进程，退出时一并回收。
- 默认数据：工作区内的 `library/eju.db`、`library/media`、`content/content-inventory.json`。

这个项目本来没有启动脚本，只能手敲 `python -m eju_bank serve`；本目录的脚本就是它的入口。

## MiniMax H3 —— `./h3-workbench.sh`

```bash
./h3-workbench.sh                    # 工作台 7860，并自动拉起后端 ComfyUI 8188
./h3-comfyui.sh                      # 只起后端引擎
./h3-stop.sh                         # 两个都停
./h3-stop.sh workbench               # 只停工作台

python h3_workbench.py               # 同上，Python 版
python h3_comfyui.py
python h3_stop.py
python h3_stop.py --status           # 看两个服务和四张卡的状态
./h3-stop.sh --status                # 同上
```

- **H3 的 `.sh` 入口不接受命令行参数**，因为底层的 `start_workbench.sh` / `start_comfyui.sh`
  只读环境变量、完全不读 argv。包装器会拦下多余参数并报错，而不是让参数被静默丢弃、
  服务照常按默认值启动。要用 `--gpu` / `--port` / `--no-browser` 就走 Python 版。
  `--help` 在两套入口都只打印说明，不会启动服务。

- **GPU 默认值有个坑**：`start_comfyui.sh` 写死 `CUDA_VISIBLE_DEVICES=3`、
  `service_manager.py` 的 `DEFAULT_GPU_ID` 也是 `"3"`，两处都注释成"H100 80GB"，
  但这台机器现在 **GPU 0 才是 H100 80GB，GPU 3 是 RTX 6000 Ada 48GB**
  （`python h3_stop.py --status` 可核对）。所以：
  - `.sh` 入口会真的绑到 GPU 3 那张 48GB 卡，要用 H100 得显式指定
    `CUDA_VISIBLE_DEVICES=0 ./h3-comfyui.sh`；
  - `.py` 入口不采用那个过时默认值，改为沿用 `H3/current_gpu.json` 里按 **UUID** 记录的
    当前绑定卡（现在正是 H100），临时换卡用 `python h3_comfyui.py --gpu 1`。
  - 想永久改绑：`/opt/conda/bin/python3 /workspace/Develop/H3/service_manager.py switch-gpu --gpu 0`，
    它会改写 `current_gpu.json`，`.py` 入口下次启动即生效。
- 端口改法：`WORKBENCH_PORT=7870 ./h3-workbench.sh`、`PORT=8288 ./h3-comfyui.sh`；
  Python 版用 `python h3_comfyui.py --port 8288`。
- 日志和 pid 都留在项目目录：`H3/workbench.log`、`H3/comfyui.log`、`H3/*.pid`。
- 视频输出目录 `/data/storage/outputs/minimax-h3`。
- `H3/service_manager.py` 还能查状态、切 GPU（`switch-gpu` 会改写 `current_gpu.json`）。

## 解释器

两套入口都显式使用 `/opt/conda/bin/python3`（3.11.10），因为 PATH 上的 `python3` 目前指向
`/workspace/ECGegg/.venv/`，直接用会跑错环境。要换解释器：

```bash
DICTATION_PYTHON=/path/to/python ./dictation.sh     # 或 python dictation.py
EJU_PYTHON=/path/to/python ./eju-bank.sh            # 或 python eju_bank.py
```

`h3_*.py` 用哪个解释器启动都可以，它内部照样按 `service_manager.py` 的规则选
`/opt/conda/bin/python` 来跑 ComfyUI 和 web_app。

## 不属于启动、故意没收进来的

- `dictation/src/serve_course.py` —— 播放器服务本体，但它由 `start_dictation.py` 派生并托管
  （令牌、审计、端口检查都在启动器里），不该单独起，所以不给它入口。
- `dictation/run_tests.py`（测试入口）、`eju-question-bank/scripts/verify_release.py`（发布校验）、
  `dictation/scripts/verify_lexicon_browser.py`（浏览器校验）
- `dictation/scripts/*`、`eju-question-bank/scripts/*` 里的一次性流水线脚本（OCR、批量转写、建课）
- `H3/generate_video.py`、`H3/example_control.py` —— 命令行出片工具，不是常驻服务

上面的清单是把 Develop 全树按 `serve_forever` / `uvicorn.run` / `http.server` 扫过一遍得到的，
除此之外没有别的服务入口。

## 怎么跑

```bash
cd /workspace/Develop/start
./dictation.sh                 # shell 版；./ 不能省
bash ./dictation.sh            # 等价写法，不要求执行权限
python dictation.py            # Python 版
/opt/conda/bin/python3 dictation.py   # 想指定解释器时
```

也可以不进这个目录，直接用绝对路径：`/workspace/Develop/start/dictation.sh`。
所有脚本都已 `chmod +x`。

新增项目时，在这里加一对同样风格的 `.sh` / `.py` 启动器并补进上面的表格。
