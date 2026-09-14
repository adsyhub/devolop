# EJU Question Bank

一个与外层听写项目完全隔离的 EJU PDF 题库流水线。运行时只使用本目录的
`eju_bank` 包、独立工作目录和独立 SQLite 数据库。

## 当前内容与使用说明

v0.2.0 的已落地修正、验证证据与保留边界见 [本轮修正记录](docs/FIXES_2026-09-08.md)。此前的 [2026-09-07 审查报告](docs/CURRENT_IMPLEMENTATION_REVIEW_2026-09-07.md) 保留为历史快照。

2023理科的已有版本因原卷与题文差异标记为待复核，暂停新练习并保留历史。
更新后的续答、答案复盘、专项练习、收藏笔记、复核发布与备份操作见
[使用说明](docs/USER_GUIDE.md)。所有计划项的执行状态见
[实施台账](docs/IMPLEMENTATION_STATUS.md)。前端层级、路由与制作台重构方案见
[前端重构方案](docs/FRONTEND_REDESIGN_2026-09-10.md)。题库内容真实性调查、
已编造答案的清理与真实 OCR 工具链见 [内容真实性记录](docs/CONTENT_INTEGRITY_2026-09-10.md)。
页面合同、复核签署通路的补完与制作工作台见
[pipeline 补完记录](docs/PIPELINE_COMPLETION_2026-09-10.md)；制作台入口 `start/eju_studio.py`。
把已核验内容经真实复核链发布、以及一个会把正确答案判为错误的正解表解析缺陷的修复，见
[内容发布记录](docs/CONTENT_RELEASE_2026-09-11.md)；驱动脚本 `scripts/attest_and_publish.py`。
制作台拆成制课 / 课程库 / 复核编辑器 / 运维四个模块，以及「上传 PDF 一键做卷」那条
流水线（含模型档位、三种校对、真题详解草稿）见
[制作台改版](docs/STUDIO_MODULES_2026-09-11.md)；入口仍是 `start/eju_studio.py`。

工作台的当前流程、前端与自动复核缺口，以及“默认自动制作、人工复核手动开启”的
后续代码改造规范，见 [工作台自动化优化方案（2026-09-12）](docs/STUDIO_AUTOMATION_OPTIMIZATION_SPEC_2026-09-12.md)。
该文档包含源码与只读数据基线、数据模型/API、实施工作包和验收用例；属于待实施方案。

## 已实现

- 来源 PDF/答案文件 SHA-256 清单和版权状态；
- 全页 PDF probe：页面尺寸、旋转、文字层、图像块、墨量、疑似空白页；
- 自动应用逐页旋转的全页图和重叠高分辨率切片；
- 逐页缓存和断点续跑；
- OpenAI-compatible 本地视觉模型与命令行 OCR provider；
- bbox、内容 AST、公式、图形、表格、答案格的页面合同；
- 可变数量单选、数学 A-Z 数字格、记述三类答案；
- 答案 PDF 独立提取和一一映射；
- deterministic assemble、stable ID、content revision 和 fail-closed audit；
- PRIVATE/PUBLIC/COMMERCIAL 授权门禁；
- 不可变 SQLite 发布版本；
- 不向浏览器发送正确答案的练习 API 和最小 Web UI；
- 原始正确数/正确率报告，明确不冒充官方等化分数。

## 安装

0.2.0 对照 20 个工作包的逐项交付、尚未完成的细则、正式库历史保全与恢复证据见
[本轮完整交付记录](docs/IMPLEMENTATION_DELIVERY_2026-09-08.md)。数据库当前为 v8。

```powershell
cd C:\path\to\Develop\eju-question-bank
python -m pip install -e ".[pdf,dev]"
```

也可以不安装，直接在本目录运行 `python -m eju_bank`。

安装包运行时可将代码与数据分开：

```bash
python -m pip install ".[pdf,audio]"
eju-bank --workspace /absolute/path/to/eju-question-bank serve --port 8765
```

全局 `--workspace`、`--config` 放在子命令前。默认数据为工作区中的
`library/eju.db`、`library/media`、`content/content-inventory.json`。配置示例：

```json
{"workspace":"../my-data","database":"library/eju.db","media":"library/media","inventory":"content/content-inventory.json"}
```

workspace 相对于配置文件目录，其余数据路径相对于 workspace；显式 CLI 数据参数优先。
默认服务仅监听本机，本机管理操作不需要任何口令；只有 `--allow-remote` 才要求访问令牌。服务自动启动独立制作 worker。
`EJU_ALLOW_SYNTHETIC=1` 是显式隔离开发选项，正式工作区不使用它绕过审核。

完整发布验证：

```bash
python -m pip install ".[pdf,audio,dev,browser]"
python -m playwright install chromium
python scripts/verify_release.py
```

该入口验证源码、Chromium 流程及 wheel 安装后的跨目录启动；源码变化会使校验失败。
结果见 `docs/evidence/release-2026-09-08.json`。本轮实测 Linux，Windows 尚未验收。

## 2023 年第 2 回理科样本

### 1. 建立来源清单

```powershell
python -m eju_bank source-init `
  --session 2023-2 `
  --subject SCIENCE `
  --language ja `
  --syllabus-version 2015 `
  --question-booklet "sources\2023令和5年第2回理科.pdf" `
  --answer-key "sources\2023令和5年第2回理科答案.pdf" `
  --rights-status PRIVATE_STUDY `
  --rights-note "用户提供的个人学习副本；未取得公开传播授权。" `
  --out work\2023-2-science\source-manifest.json
```

### 2. Probe

```powershell
python -m eju_bank probe `
  --manifest work\2023-2-science\source-manifest.json `
  --out work\2023-2-science\probe.json
```

### 3. 渲染

```powershell
python -m eju_bank render `
  --manifest work\2023-2-science\source-manifest.json `
  --role QUESTION_BOOKLET `
  --out work\2023-2-science\renders

python -m eju_bank render `
  --manifest work\2023-2-science\source-manifest.json `
  --role ANSWER_KEY `
  --out work\2023-2-science\renders
```

同一命令重跑会复用已存在的 PNG。测试少量页面可加：

```powershell
--pages "1,3,24,42,56"
```

### 4. OCR/VLM

复制 `config/providers.example.json` 为本机配置。以 Ollama 的 OpenAI-compatible
端点为例：

```powershell
python -m eju_bank extract `
  --manifest work\2023-2-science\source-manifest.json `
  --render-index work\2023-2-science\renders\render-index-question_booklet.json `
  --provider-config config\providers.json `
  --provider qwen-transformers `
  --out work\2023-2-science\pages
```

使用已有 `.venv-ocr` 时，可以把上面的 `python` 换成
`..\.venv-ocr\Scripts\python.exe`。如果使用 Ollama，则将 provider 改为
`qwen-ollama`。本地 7B 配置默认要求启动前至少有 21000 MiB 空闲显存，避免 Windows
WDDM 在另一个 OCR 任务占用显卡时悄悄换页；需要更小模型时可以按实际显存调整该值。

答案页使用 `render-index-answer_key.json` 再运行一次。无论模型返回什么，每页都会先
经过 contract validator；无效页面写入质量报告，不能直接发布。

### 5. 审核、答案 ledger、组装

```powershell
python -m eju_bank validate-pages --pages work\2023-2-science\pages

python -m eju_bank answers-from-pages `
  --pages work\2023-2-science\pages `
  --out work\2023-2-science\answers.json

python -m eju_bank assemble `
  --manifest work\2023-2-science\source-manifest.json `
  --pages work\2023-2-science\pages `
  --answers work\2023-2-science\answers.json `
  --out work\2023-2-science\paper.json

python -m eju_bank audit --paper work\2023-2-science\paper.json
```

### 6. 复核、私人发布和练习

真实来源的页面需先在内容复核台逐页签署，再签署整卷。下列 `publish` 命令只接受
包含当前复核证书的题卷；未经复核的原始 `assemble` 产物不能直接发布。
也可直接在复核台完成私人发布，详见 [使用说明](docs/USER_GUIDE.md)。

```powershell
python -m eju_bank publish `
  --paper work\2023-2-science\paper.json `
  --database library\eju.db `
  --channel PRIVATE

python -m eju_bank serve --database library\eju.db
```

打开 `http://127.0.0.1:8765`。

## 测试

```powershell
pytest
```

`tests/test_real_2023_science_pdf.py` 会在项目内 `sources` 中存在两份样本时，实际检查
56/8 页、90 度旋转、无文字层，并渲染物理/化学/生物和答案代表页。

## 项目文档

- [尚未完成内容的详细实现规格（20 个工作包）](docs/UNFINISHED_IMPLEMENTATION_SPEC.md)
- [剩余工作实施检查表与验收方案](docs/UNFINISHED_ACCEPTANCE_PLAN.md)
- [当前使用说明](docs/USER_GUIDE.md)
- [全量完善工作执行台账](docs/IMPLEMENTATION_STATUS.md)

- 学习、复盘、错题、听力与内容维护的功能完善清单：
  [docs/FUNCTIONAL_IMPROVEMENT_PLAN.md](docs/FUNCTIONAL_IMPROVEMENT_PLAN.md)
- 最新源码、真实数据复核结果与分阶段整改计划（2026-09-07）：
  [docs/PROJECT_REVIEW_2026-09-07.md](docs/PROJECT_REVIEW_2026-09-07.md)
- 完整题库的现状、目标架构、任务拆分和验收标准：
  [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- PDF/OCR/组卷合同说明：[docs/PIPELINE.md](docs/PIPELINE.md)
