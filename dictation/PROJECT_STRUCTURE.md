# 听写项目整理与维护说明

最后整理日期：2026-08-19
最后更新日期：2026-08-31（JLPT 题库，见第 13 节）

> 本文第 1–9 节记录的是 2026-08-19 的目录整理。第 5 节「已删除或移出的内容」中
> 关于测试的部分**已过时**：测试已在 2026-08-20 重建，见第 10 节。

## 1. 整理目标

本次整理将项目从“开发、测试、中间数据和发布证据混放在根目录”的状态，调整为清晰的运行结构：

- 根目录只保留启动入口、依赖配置和主要说明。
- 所有程序源码集中到 `src/`。
- 可直接学习的课程集中到 `courses/`。
- 内容修订记录与版权资料集中到 `assets/`。
- 产品文档集中到 `docs/`。
- 可交付的候选 ZIP 集中到 `dist/`。
- 测试代码、缓存、重复音频和构建中间产物已移除。

## 2. 当前目录结构

```text
dictation/
├─ start_dictation.py
├─ README.md
├─ PROJECT_STRUCTURE.md
├─ requirements.txt
├─ .env.example
├─ .gitignore
│
├─ src/
│  ├─ serve_course.py
│  ├─ local_backend.py
│  ├─ bundle_quality.py
│  ├─ course_schema.py
│  ├─ language_support.py
│  ├─ build_deepseek_offline_bundle.py
│  ├─ review_server.py
│  ├─ 其他内容处理与发布工具
│  ├─ web/
│  └─ review_web/
│
├─ courses/
│  └─ 2010-12-N2/
│     ├─ manifest.json
│     └─ audio.mp3
│
├─ assets/
│  ├─ content_patches/
│  ├─ licenses/
│  │  └─ 2010-12-N2-v11.license.json
│  └─ release_approvals.example.json
│
├─ docs/
│  ├─ COMMERCIAL_ROADMAP.md
│  └─ MARKET_ANALYSIS.md
│
└─ dist/
   └─ 2010-12-N2-commercial-candidate.zip
```

## 3. 日常运行所需文件

运行当前听写课程只依赖以下内容：

| 路径 | 用途 |
|---|---|
| `start_dictation.py` | 推荐的唯一启动入口；选择端口、检查课程和音频、启动浏览器 |
| `src/serve_course.py` | 本地 HTTP 服务、音频 Range 请求和学习 API |
| `src/local_backend.py` | 生词、笔记和打卡的 SQLite 存储 |
| `src/web/` | 首页、听写播放器、题库页面、样式、脚本、图标和 Service Worker |
| `src/bundle_quality.py` | 启动前检查课程清单质量 |
| `src/course_schema.py` | 课程数据结构辅助逻辑 |
| `src/language_support.py` | 多语言字段和规范化逻辑 |
| `courses/2010-12-N2/` | 当前课程的清单和音频 |

播放器运行只使用 Python 标准库，不要求安装 `requirements.txt` 中的构建依赖。

## 4. 源码分类

### 4.1 运行与界面

- `serve_course.py`：本地播放器服务。
- `local_backend.py`：本地学习数据后端。
- `web/app.js`：精听页面编排、播放器交互和路由；课程只在进入练习时加载。
- `web/personal.js`：独立“我的”页面编排；跨课程读取错题、生词、笔记和分析，不初始化播放器。
- `web/progress_model.js`：听写尝试、只听曝光、掌握状态和句子复习调度的统一模型。
- `web/dictation_scoring.js`：多语言答案规范化、相似度、逐字符差异和提示生成。
- `web/course_library_model.js`：课程搜索、分类、质量/审核状态和学习状态筛选。
- `web/learning_data.js`：离线写入队列、依赖顺序和删除墓碑同步。
- `web/media_adapters.js`：本地音频、YouTube、嵌入框架和仅外链媒体的统一播放接口。
- `review_server.py`、`review_web/`：人工逐句审核工具。

### 4.2 课程生成

- `build_deepseek_offline_bundle.py`：完整课程生成管线。
- `make_zip.py`：从音频生成课程包。
- `sentence_segmentation.py`：语句片段合并。
- `language_support.py`：来源语言处理。
- `chinese_localization.py`、`normalize_chinese.py`：简体中文规范化。
- `course_schema.py`：课程清单结构与稳定 ID。

### 4.3 质量与内容修复

- `bundle_quality.py`、`audit_bundle.py`：课程质量检查。
- `asr_quality.py`、`attach_asr_quality.py`：转写质量信息。
- `content_patch.py`、`apply_content_patch.py`：可追踪内容修订。
- `repair_enrichment.py`：翻译和讲解修复。
- `human_review.py`：人工审核记录。

### 4.4 发布与授权

- `prepare_commercial_manifest.py`：准备商业候选清单。
- `repack_offline_bundle.py`：重新打包离线课程。
- `content_license.py`：版权台账检查。
- `release_evidence.py`、`release_readiness.py`：发布证据与就绪状态检查。
- `generate_pwa_icons.py`：重新生成 PWA 图标；需要单独安装 Pillow。

## 5. 已删除或移出的内容

本次移除了以下不参与日常运行的内容：

- 16 个 `test_*.py` 单元测试文件。
- `e2e_browser_test.py` 浏览器自动化测试脚本。
- `requirements-dev.txt` 测试依赖清单。
- `.venv/` 可重新创建的虚拟环境，原大小约 427 MB。
- `__pycache__/` Python 字节码缓存。
- `data-work/`、`scratch-verify-data/` 和 `local-data/` 临时工作目录。
- 原 `data/` 中的原始分段、重转写结果、多个历史 manifest、质量报告和重复音频。
- 原 `release/` 中的 E2E 截图、浏览器报告、就绪报告和审核截图。
- 旧版重复版权台账 `2010-12-N2.license.json`。
- 已失效的旧构建快捷脚本 `run`。
- 已过期并引用被删除测试文件的发布检查文档。

保留原则：当前可运行课程使用的 `manifest.json` 和 `audio.mp3` 已在删除旧 `data/` 前迁移到 `courses/2010-12-N2/`；正式候选 ZIP 已迁移到 `dist/`。

体积较大的缓存和中间目录通过 Windows 回收站移除，必要时可以在清空回收站前恢复。测试源码等小型文本文件已直接从项目中删除。

## 6. 启动与停止

启动：

```powershell
python .\start_dictation.py
```

启动器会在打开浏览器前检查：

- `manifest.json` 是否存在且可读取；
- manifest 是否指定了有效音频文件；
- HTTP 服务是否已就绪；
- 音频请求是否返回 `audio/*` 类型和足够的数据。

停止：在启动窗口按 `Ctrl+C`。

学习数据默认保存在：

```text
%LOCALAPPDATA%\dictation-preview\learning.sqlite3
```

项目整理不会删除该数据库。

## 7. 添加新课程

每门课程单独建立一个文件夹，至少包含清单和清单中指定的音频文件：

```text
courses/
└─ my-course/
   ├─ manifest.json
   └─ audio.mp3
```

运行：

```powershell
python .\start_dictation.py --manifest ".\courses\my-course\manifest.json"
```

不要直接双击 `src/web/index.html`，因为 `file://` 会阻止课程 JSON、Service Worker 和部分音频功能。

## 8. 维护规则

1. 不要把新的测试输出、转写缓存或临时数据库放回根目录。
2. 课程构建的工作目录使用名称后缀 `-work`，`.gitignore` 会忽略这类目录。
3. 每个课程文件夹只保留最终 `manifest.json`、实际音频和确有必要的课程附件。
4. 内容修订证据放在 `assets/content_patches/`，版权台账放在 `assets/licenses/`。
5. 最终 ZIP 放在 `dist/`，不要把截图和临时验收报告混入该目录。
6. 修改目录后同步检查 `start_dictation.py`、`src/serve_course.py` 和本文档中的路径。

## 9. 发布状态说明

`dist/2010-12-N2-commercial-candidate.zip` 是已有的技术候选包。技术文件完整并不等于内容已取得商业授权；在公开发布或销售前，仍应核实 `assets/licenses/` 中的权利信息和外部授权证据。

## 10. Phase 0 改进（2026-08-20）

按 `docs/Miraa_可吸收能力分析与项目改进执行方案_v1.0.docx` 的 Phase 0 实施。
决策记录见 [docs/ADR.md](docs/ADR.md)，事实数字见 `implementation-facts.json`。

### 10.1 新增文件

| 路径 | 用途 |
|---|---|
| `run_tests.py` | 唯一测试入口（Python `unittest` + Node `node:test`） |
| `tests/` | P0 回归测试 |
| `src/security_context.py` | 本地 API 授权：Host 白名单 + 会话令牌 + Fetch Metadata |
| `src/error_contract.py` | 最小错误合同 `{code, stage, retryable, userAction, diagnosticId}` |
| `src/snapshot_evidence.py` | 证据快照与 SHA-256 清单，含 SQLite Backup API 一致副本 |
| `src/content_candidate.py` | 内容候选段级 diff 与 alias 生成（只产报告，不切课程） |
| `src/implementation_facts.py` | 生成 `implementation-facts.json` |
| `docs/ADR.md` | 已签署与未签署的架构决策 |
| `assets/evidence/` | 入库的哈希清单（快照本体在 `assets/snapshots/`，不入库） |
| `assets/content_candidates/` | 候选包 diff 报告与 alias 表 |

### 10.2 行为变化

- **端口**：默认从「每次随机」改为固定 `4173`；被占用时报告并退出，不静默换端口。
- **质量门**：审计有错误的课程拒绝启动，需 `--allow-failed-course` 显式绕过。
- **本地 API**：读写都要求会话令牌与合法 Host（此前读接口完全无保护，写接口的
  同源判断可被伪造 Host 绕过，已实测复现）。
- **Service Worker**：manifest 改网络优先；课程缓存改两阶段可恢复切换；Range
  改流式读取。

### 10.3 维护规则补充

7. 文档中的测试数、课程段数和质量状态只能引用 `implementation-facts.json`，
   改动后重新运行 `python src/implementation_facts.py`。
8. `docs/COMMERCIAL_ROADMAP.md` 与 `docs/MARKET_ANALYSIS.md` 尚未按本次改进复核，
   其中引用的测试数与课程统计可能仍是旧值，暂不作为事实来源。

## 11. 课程流水线可插拔化（2026-08-31）

按 [ADR-MODEL-001](docs/ADR.md) 实施：构建流水线不再内置任何模型名。
使用说明见 [docs/COURSE_PIPELINE.md](docs/COURSE_PIPELINE.md)。

### 11.1 新增文件

| 路径 | 用途 |
|---|---|
| `src/build_course.py` | 课程构建主入口，ASR 与文本模型均运行时解析 |
| `src/provider_config.py` | provider 解析：配置文件 → 环境变量 → 命令行；密钥只存变量名 |
| `src/text_providers.py` | 六种文本 provider：OpenAI 兼容 / Anthropic / Ollama / CLI / 手工交接 / 占位桩 |
| `src/asr_providers.py` | 四种 ASR provider：本地 faster-whisper / 音频 API / 任意命令 / 导入转写 |
| `src/enrichment.py` | 与 provider 无关的批次生成、校验与回填 |
| `src/install_course.py` | ZIP → `courses/<name>/`，安装前重新审计 |
| `src/bundle_io.py` | 原先散在构建器里的 JSON/哈希/ZIP 工具 |
| `config/providers.example.json` | provider 配置模板（22 个可用 profile 示例） |
| `docs/COURSE_PIPELINE.md` | 流水线说明、各 provider 接法与排错表 |
| `tests/test_provider_resolution.py` | 配置优先级、缺模型报错、密钥不外泄 |
| `tests/test_model_providers.py` | 各 provider 的实际请求/响应形状（打本地桩服务） |
| `tests/test_course_pipeline.py` | 端到端构建、断点续跑、批次摘要校验、安装 |

### 11.2 行为变化

- **模型**：不再有默认模型。网络类 provider 缺模型是**启动期错误**，不是第一个批次才失败。
- **本地可用**：ASR 默认从 `cuda`/`float16` 改为 `auto`/`int8`，没有 NVIDIA GPU 也能构建。
- **依赖**：`openai` SDK 已移除，文本 provider 全部走标准库；`requirements.txt` 只剩本地
  转写与繁转简两项，且都是可选的。
- **安装**：新增 ZIP → `courses/` 这一步。此前构建产物到可播放课程之间是空白，只能手工解压。
- **来历**：每门课的 `buildMetadata.asr` / `buildMetadata.enrichment` 和
  `courses/<name>/install-source.json` 记录它是哪个 provider、哪个模型做的（只记环境变量名）。
- **占位桩**：`echo` 产物默认拒绝打包，需显式 `--allow-stub-enrichment`。
- **子进程编码**：`cli` 与 `command` provider 强制子进程 UTF-8。此前 Windows 上中文会被
  控制台代码页打成替换字符，一路到最终审计才暴露。

### 11.3 维护规则补充

9. 新增 provider 时只改 `text_providers.py` / `asr_providers.py` 与
   `provider_config.py` 的 kind 列表，不要把模型名写回任何其他源文件。
10. `config/providers.json` 是每台机器自己的，已 gitignore；改动示例请改
    `config/providers.example.json`，它有测试保证能加载并解析。
11. 密钥永远只以环境变量名的形式出现在配置和清单里。带字面量密钥的配置会被拒绝加载。

## 12. 图形化制课工作台（2026-08-31）

### 12.1 新增文件

| 路径 | 用途 |
|---|---|
| `src/studio_server.py` | 仅监听回环的统一制课工作台服务，默认端口 4174 |
| `src/build_pdf_course.py` | PDF 多模型 OCR、类型路由及真题/词汇/语法审阅草稿编排器 |
| `src/studio_web/` | 工作台页面（index.html / studio.css / studio.js） |
| `tests/test_studio_server.py` | 授权、provider 注入、上传、构建生命周期回归 |

### 12.2 两条不可让步的边界

1. **页面不能构造 provider，只能选 profile 名。** `cli` 与 `command` 两种 provider 会起
   子进程；接受请求体里的命令等于把同源立足点升级成任意代码执行。配置文件可信（人编辑的），
   请求体不可信（永远）。测试 `test_a_command_in_the_request_body_is_ignored_entirely`
   验证请求体里的 `command`/`model`/`baseUrl`/`handoffDir` 一律不进入构建参数。
2. **音频与 PDF 走上传，不走路径。** 没有任何读取或列举路径的端点，因此没有穿越面。
   落盘文件名由服务端生成，客户端文件名只当元数据；PDF 还检查文件签名。

授权直接复用 `src/security_context.py`（与播放器同一套：回环 Host 白名单 + 每次调用会话令牌
+ 写操作校验 Origin 与 Fetch Metadata），比 `review_server.py` 自带的那套更严。

### 12.3 设计说明

- 构建跑在**子进程**而非线程：可真正取消，输出天然流式，模型代码崩溃（如 kotoba 的词级
  时间戳段错误）只带走子进程。
- 子进程环境里剔除 `DICTATION_SESSION_TOKEN`：构建会运行第三方模型代码和 CLI 工具，
  没有理由让它继承授权本服务的令牌。
- 工作区默认 `studio-work/`（已 gitignore），存上传文件与构建产物。
- 内容编辑不在此实现，那是 `review_server.py` 的职责，不重复造。

### 12.4 PDF 工作台边界

- 页面只能选择 `visionPipelines` 的名字。实际端点、模型和密钥环境变量来自可信配置；
  请求体里的 `model` / `baseUrl` / `command` 被忽略。
- 默认本地质量链为 GLM-OCR → GLM-4.6V → Qwen3.8-Flash-Next，后两层只重读
  `quality-report.json` 标出的异常页。显式选择云端视觉链时才会上传页面。
- PDF 自动任务只写 `studio-work/builds/<job>/artifact/` 下的审阅草稿。答案表与教材目录
  数量没有独立证据时状态固定为 `needs_review`，不能直接安装。

### 12.5 维护规则补充

12. 工作台新增任何接口前先问：它是否让浏览器获得了「描述一个 provider」的能力。若是，不要加。
13. 页面不得使用内联事件处理器，CSP 是 `script-src 'self'`，测试会检查。

## 13. JLPT 题库（2026-08-31）

在听写播放器之外增加一套 JLPT 真题解题系统。使用说明见
[docs/JLPT_EXAM.md](docs/JLPT_EXAM.md)，决策记录见 [ADR-EXAM-001](docs/ADR.md)。

### 13.1 新增文件

| 路径 | 用途 |
|---|---|
| `src/exam_schema.py` | 题库数据结构、稳定 ID、质量审计与计分（对应课程的 `course_schema` + `bundle_quality`） |
| `src/exam_import.py` | PDF → 页面图片 → 逐页转写 → `exam.json` 的导入管线，三个子命令 `render` / `assemble` / `validate` |
| `src/exam_store.py` | `ExamStore`（读盘）、`ExamProgress`（作答记录与错题本）、`ExamApiMixin`（`/api/exams*` 路由） |
| `src/web/exam.html` | 题库页面 |
| `src/web/exam.css` | 题库样式（复用 `app.css` 的设计变量） |
| `src/web/exam.js` | 三种练习方式、答题卡、计分报告、错题本 |
| `src/web/exam_markup.js` | 题目文本 → DOM 的渲染器，单独拆出以便单测 |
| `exams/2022-07-N1/` | 2022 年 7 月 N1：`exam.json`、`answer-key.txt`、`exam-meta.json`、`pages/` |
| `tests/exam_fixtures.py` | 题库测试夹具 |
| `tests/test_exam_schema.py` | 审计规则与计分 |
| `tests/test_exam_import.py` | 答案表解析、跨页拼接、数量对不上时必须报错 |
| `tests/test_exam_api.py` | 接口、错题本、授权边界、路径穿越 |
| `tests/exam_markup.test.mjs` | 渲染器，含注入回归与「整套真题都能渲染」 |
| `docs/JLPT_EXAM.md` | 题库说明与导入流程 |
| `docs/JLPT_EXAM_PIPELINE.md` | 题库制作流水线与执行指南（分步命令、转写规范、LLM 提示词与排错） |

### 13.2 行为变化

- **同一个服务**：题库挂在播放器的同一进程、同一端口、同一 SQLite 文件上。作答记录
  和生词本、笔记放在一起，不另起一个有自己端口、自己令牌、自己备份问题的应用。
- **质量门**：`audit_exam` 有错误的卷子拒绝提供（HTTP 422），和课程的 fail-closed 规则一致。
  答案抄错比加载失败更糟——学的是错答案，而且发现不了。
- **计分按练习范围**：只练一道大题，就按这道大题计分。
- **Service Worker**：`SHELL_ASSETS` 增加题库三个文件，缓存版本升到 `dictation-shell-v21`。
- **启动器**：`start_dictation.py` 多打印一行题库地址。

### 13.3 维护规则补充

14. `exam.json` 是生成物。改错字改 `exams/<名称>/pages/` 再重新 `assemble`，不要手改
    `exam.json`；题目 ID 由内容派生且稳定，改一道题不会影响其余题目的作答记录。
15. 导入时答案数量与页面题数对不上必须报错停下，不允许放宽成警告。答案串位之后
    学习者没有任何办法发现。
16. 题目正文永远不经过 `innerHTML`。新增任何渲染分支前先问：这段文字是转写出来的
    数据吗？是就必须走 `exam_markup.js` 的 `createElement` 路径。
17. 振假名标记用全角竖线 `｜`（U+FF5C），不要改回半角——半角会和表格分隔符冲突。

## 14. 在线视频课程（2026-08-31）

按 [ADR-VIDEO-001](docs/ADR.md) 实施：课程的媒体可以是网上的视频，**视频从不下载**。
使用说明见 [docs/VIDEO_COURSES.md](docs/VIDEO_COURSES.md)。

### 14.1 新增文件

| 路径 | 用途 |
|---|---|
| `src/media_sources.py` | 唯一知道视频站点存在的模块：URL 识别与硬化、SRT/VTT/json3 解析、字幕清洗、yt-dlp 封装 |
| `src/build_video_course.py` | 在线视频建课入口，复用 `build_course.py` 的转写、enrichment 与质量门 |
| `src/web/media_adapters.js` | 播放适配器：本地音频 / YouTube / 可嵌入 / 仅外链，四种实现同一套接口 |
| `docs/VIDEO_COURSES.md` | 版权立场、三档控制、两个入口、精听流程、排错表 |
| `tests/test_media_sources.py` | URL 拒绝、字幕解析、滚动窗口去重、yt-dlp 桩 |
| `tests/test_video_course_pipeline.py` | 端到端建课（桩 yt-dlp + 桩文本模型） |
| `tests/test_remote_media_schema.py` | `media` 块规范化、审计新错误码、本地课不变 |
| `tests/test_remote_media_player.py` | 无本地媒体的课程可服务；CSP 三份副本一致 |
| `tests/media_adapters.test.mjs` | 适配器状态机、rAF 时钟、降级路径 |

### 14.2 两条不可让步的边界

1. **一门课只声明一次媒体。** `audio`（本地文件）与 `media`（在线视频）二选一，
   两个都有是**错误**而不是可合并的状态：那是一个文件里的两门课，播放器无论选哪个，
   另一半清单描述的都是学习者没在听的东西。`prepare_course_manifest` 和
   `audit_manifest` 各自独立拦一次。

2. **在线视频课程永不可再分发。** `media.attribution.redistributable` 由
   `normalize_remote_media` 强制改写为 `false`，清单声称可分发会被审计判为错误
   （`manifest.media_redistributable_claim`），`release_readiness.py` 与
   `content_license.py` 明确拒绝这类课程。第 9 节那句「技术文件完整不等于取得授权」
   在这里是强制的，不是提醒。

### 14.3 行为变化

- **三档控制**：`media.control` 取 `full` / `seek-reload` / `external`，分别对应
  「可完全控制」「只能重载定位」「站点拒绝嵌入」。UI 直说这门课属于哪一档。
  **一个点了没反应的循环按钮，比没有这个按钮糟得多。**
- **播放器解耦**：`app.js` 原先 37 处直接操作 `<audio>` 元素，现在统一走
  `media` 适配器句柄。接口刻意做成 HTMLMediaElement 的形状，本地音频课行为不变。
- **盲听默认开启**：听写模式下遮住画面，声音照常播放。新闻视频常把答案以字幕烧在
  画面里；嵌入播放器一律带 `cc_load_policy=0`，也不显示站点自己的字幕。
- **循环边界容差**：本地 `<audio>` 用 20ms，远程播放器（时钟靠 rAF 采样、seek 是异步的）
  用 120ms，并加了 seek 未落定时的抑制，否则会连发 seek 变成卡顿而不是循环。
- **变速吸附**：YouTube 只接受固定档位。吸附规则是**不超过所求的最大可用档**，
  不是最近邻——最近邻会把 0.8x 吸到 1.0x，等于对「放慢一点」这个请求完全没有响应。
- **CSP**：播放器页面放宽了 `script-src`（`www.youtube.com`、`s.ytimg.com`）、
  `frame-src`、`img-src`、`connect-src`。`frame-ancestors 'none'` **不变**——
  它管的是谁可以嵌入我们。工作台的 CSP 完全未动。
- **Service Worker**：`SHELL_ASSETS` 增加 `media_adapters.js`，缓存版本升到
  `dictation-shell-v22`。远程课只缓存 manifest，跨源媒体永不进 Cache Storage。
- **工作台**：新增 `POST /api/video/probe` 与 `POST /api/video/builds`，
  页面多一个「在线视频」标签。视频课直接写进 `courses/`，没有 ZIP，因此没有装入步骤。
- **可选依赖**：`yt-dlp`。只有抓站点字幕和临时取音频两条路径需要，
  用本地字幕文件建课不需要。未安装时给出 `pip install yt-dlp` 并停下。

### 14.4 维护规则补充

18. 视频站点的 URL 规则只写在 `src/media_sources.py`。别处再长出一个 URL 正则，
    就是这个项目开始对「什么是一个 YouTube 链接」有两种说法的时刻。
19. 临时音频只能经 `media_sources.temporary_audio` 取得。它在 `finally` 里删掉整个
    临时目录（`.part` 残留一并带走），异常路径同样删。不要绕过它直接调 yt-dlp 取音频。
20. 句子时间轴永远是视频的**绝对时间**。`media.clip` 只是过滤条件，任何地方都不要
    减去 `clip.startTime`——少减一处就是每次定位都偏。
21. CSP 有三份副本（`serve_course.py` 的 `CONTENT_SECURITY_POLICY`、`index.html` 的
    meta、`_headers`）。只改 `serve_course.py` 那份然后同步另外两份；
    `tests/test_remote_media_player.py` 会逐条比对，`<meta>` 那份只允许缺
    `frame-ancestors`（该指令在 meta 里本就无效）。
22. 滚动窗口去重（`clean_segments(rolling_window=True)`）只对**自动字幕**开。
    人工字幕没有这个伪影，而合并会吃掉真实的重复。`fetch_subtitles` 知道拿到的是
    哪一种，`clean_segments` 不猜。
23. 工作台新增任何接收 URL 的接口前先问：这个字符串会不会进 argv。会就必须先过
    `parse_media_url`，并且进 argv 的是它重建出的规范 URL，不是请求体里的原串。


## 15. 界面分层：首页 → 板块 → 分类 → 课程 → 学习（2026-09-01）

改造前，播放器顶栏平铺八个同级按钮（打卡与分析、笔记、生词本、错题本、课程面板、
JLPT 题库、快捷键、存储位置），四个个人功能各自是一个独立 `<dialog>`；题库页在另一
个页面，个人数据在那边完全够不着。学习者要自己在这排按钮里拼出「哪个是练习、哪个
是考试、哪个是我的记录」。

现在是两个独立学习工作区，加一个跨模式资产中心：

| 板块 | 入口 | 承载 |
|---|---|---|
| **精听工作区** | `/listening#/listening` | 课程库（视频/音频）→ 逐句精听、全文精听 |
| **真题工作区** | `/exams` | 逐题练习、计时模考、错题复习 |
| **我的学习中心** | `/me#/<模块>` | 跨模式错题、生词、笔记和分析；不是第三种练法 |

### 15.1 变化

- **工作区顶栏**：精听和真题不再作为相邻 Tab。中间只显示当前工作区与“切换学习模式”，
  切换时先回首页；左侧保留工作区局部控件，右侧保留状态和“我的”。
- **稳定产品路径**：服务端把 `/listening`、`/exams`、`/me` 分别映射到 `index.html`、
  `exam.html`、`me.html`，
  旧 `index.html` / `exam.html` 深链继续兼容；带末尾斜杠的地址用 308 规范化，防止相对资源
  被解析到不存在的子目录。
- **个人中心独立**：`me.html` + `personal.js` 承载错题、生词、笔记和分析，页面进入时不加载
  当前精听课程、播放器或题库答题状态。旧精听页个人中心 hash 会自动迁移到 `/me`。
- **深链**：`/me#/mistakes`、`/me#/vocab`、`/me#/analytics/logs`、`/me#/mistakes/exam` 等直接落到
  对应模块或子标签；题库页的「我的」
  就是 `/me#/mistakes`。反向有 `/exams#/exam/<slug>?mode=review&scope=wrong`，
  从错题集一键进某套卷的错题复习。
- **真题错题接入**：`真题错题本` 标签以前是写死的空列表。现在按卷聚合
  `/api/exams/review-summary` 中 `lastResult` 为 `wrong` / `skipped` / `guessed` 的题
  ——和题库页 `错题复习` 的判定同一条规则，两边计数不会打架。
- **切换课程复活**：`CoursePicker` 一直在找 `#course-picker-button`，而这个按钮从来
  没写进 HTML，功能是死的。现在它在「更多」菜单里，后端可用时由 `CoursePicker.init`
  取消隐藏。
- **离线学习数据**：`web/learning_data.js` 管理持久化 outbox、删除墓碑与重放；
  `web/personal_data_tools.js` 承担生词导入解析和去重。写操作先本地生效，服务端用客户端
  操作 ID 保证打卡和 SRS 重放幂等。
- **练习队列分层**：`coursePracticeIndexes` 永远保存课程完整句序，`practiceIndexes` 只表示
  当前练习队列。错题专项退出后可恢复整课，笔记序号与统计分母不再被专项队列污染。
- **Service Worker**：外壳缓存包含个人数据同步和导入工具脚本，断网时个人中心仍可启动。

### 15.2 设计说明

**领域数据不强行合表**。「我的」把四个模块摆到一起，取数仍按领域区分：听写侧读
`/api/mistakes`、`/api/vocab`、`/api/notes`、`/api/analytics`，真题侧读
`/api/exams/review-summary`。合并成一张统一表要迁移历史数据，而两边的「错题」本来
就不是一个概念——听写错的是句子，真题错的是选项。界面统一足够解决割裂感。

**真题错题不在开机时拉**。开机只算听写错题和到期生词；打开「真题错题」时才请求
一次 `/api/exams/review-summary`。后端用单次查询聚合所有待复习题，再补齐试卷标题与等级，
避免客户端对每套卷分别请求 `/review` 的 N+1 扇出。

**分析口径显式化**。趋势、热力图和日志日期按浏览器提交的 `local_day` 归日，不再把 UTC
日期误当本地日期；“当前课程”和“全部精听”是明确可切换的范围。手动打卡只记录行为，
不会伪造练习句数或学习时长。

### 15.3 维护规则补充

24. 新功能先判断它属于精听、真题还是跨模式资产。学习动作只能进入一个工作区；
    顶栏不得重新添加精听/真题互切 Tab，跨模式切换统一回首页。
25. 个人模块的面板内容改 id 之前，先 grep `app.js`。四个模块合并时刻意保留了原有
    id，就是为了让各自的渲染函数不必知道自己住在哪个弹窗里。
26. `index.html` 与 `exam.html` 使用同一套 `.mode-context` 结构，但工作区颜色和局部控件不同。
    公共结构改动需要同步，不能重新把两套业务操作混到一起。

### 15.4 第二轮：把层级真正做出来

第一轮只是把顶栏收成三个入口，进去之后仍然是一层。这一轮补上中间的层级。

| 路由 | 落到哪 |
|---|---|
| `/` | `home.html`，两张学习模式主卡 + 我的学习中心 |
| `/listening#/listening[/video\|/audio]` | 精听课程库，按视频/音频分类 |
| `/listening#/practice` | 当前精听课程的练习界面 |
| `/me#/<模块>[/<子标签>]` | `me.html` 独立个人中心，不依赖当前课程即可打开 |
| `/exams#/level/N2` | 该等级的练法选择（按卷练习 / 专题练习） |
| `/exams#/level/N2/papers` | 按卷练习：选择该等级的一套真题 |
| `/exams#/level/N2/topics` | 专题练习：大类（言語知識 / 読解 / 聴解） |
| `/exams#/exam/<slug>?mode=&scope=` | 某套真题的指定练习方式 |

**新增文件**

| 路径 | 用途 |
|---|---|
| `src/web/home.html` | 应用首页：两种学习模式主卡，以及独立的跨模式资产入口 |
| `src/web/home.js` | 首页脚本。分别汇总课程、真题、精听错句与真题错题，不加载播放器 |

**练习中的课程切换是就地展开，不是导航**。顶栏「课程库」按钮原本把人踢回
`#/listening`——正在练的那一句就丢了。现在它是个 disclosure，在按钮下方竖列展开课程
（按视频/音频分组，当前课程标「正在学习」），底部留一条「浏览全部课程 →」通向完整
课程库。课程卡片和下拉行共用同一个 `switchTo()`。

**index.html 拆成两个视图**：`#view-library`（分类切换 + 课程网格）与
`#view-practice`（原有的 `.layout`，整块下移一层缩进）。`showView()` 负责切换，
并顺手收掉只在练习界面有意义的控件（课程面板开关、返回课程库按钮、致命错误横幅）。

**CoursePicker 被 Library 取代**。以前选课是「更多」菜单里的一个弹窗列表，和课程库
是同一件事的两种做法。现在只有 Library 一处列课程，弹窗与菜单项一并删掉。顺带修好
两个旧 bug：`course.language` 是对象不是字符串，旧卡片渲染出 `[object Object]`；
`#course-picker-button` 从来没写进 HTML，那个模块一直在找一个不存在的按钮。

**JLPT 板块的第二层是等级**。真题列表上方有一排 N1 / N2 / N3… 标签，和精听的
视频/音频分类共用 `.category-switch` 样式——两个板块的第二层长得一样，学习者不用
学两遍。标签由 `/api/exams` 的 `level` 字段生成（`LEVEL_ORDER` 定死 N1→N5 的顺序，
之外的等级排在后面，没有 `level` 的卷归入「其他」），所以导入 N2 / N3 真题后标签
自动出现，不需要改代码。

**JLPT 板块的第三层是练法**。选完等级后先问「怎么练」，而不是直接给一堆卷子：

- **按卷练习** —— 先选一套真题，再选择逐题、计时或错题复习及练习范围。
- **专题练习** —— 把该等级若干套卷的同一题型合并成一个连续题库。配置页可按**整套真题**
  设置来源卷数量，默认全量；减少数量时优先选择较新的卷，并始终保留所选卷在该题型下的全部题目。

**第四层是题型**。进入某个大类后再按题型细分：N1 的 聴解 拆成 課題理解 120 题 /
要点理解 133 题 / 概要理解 117 题 / 即时应答 269 题 / 综合理解 78 题，顶上留一张
「全部聴解」卡保留整类连刷。

进入专题配置页后不再重复列出每套来源卷的 section / part；范围只保留「本专题」、错题、
到期和已标记。逐题练习与错题复习均在完成整组并交卷后统一判题，作答过程中不提前揭晓。

每套真题卡片通过 `/api/exams` 的 `progress` 摘要显示未开始、进行中和已完成状态。未交卷的
attempt 保存原始 `questionIds` 与逐题答案，可从首道未答题继续；用户也可显式放弃，放弃记录
不会计分。按卷配置页在存在进行中记录时禁止重复开卷，必须先继续或放弃。

分组键是 `part.kind`，**绝不是 問題 编号**。编号在不同卷式之间会平移——「词汇填空」
在 N1 是 問題2、在 N2 是 問題4——按编号分组会把同一个练习拆成两堆、又把两个练习并成
一堆。`kind`（`context-vocabulary`）是与卷式无关的身份，`localTitle` 只是它的显示名。

跨卷合并的做法是**造一个虚拟试卷**（`buildTopicExam`）：把各卷同名 section 的 parts
串成一个 section，外形和普通试卷一模一样。于是队列构建、题目渲染、答题卡、计分报告
全部不用改——它们只认识「一份试卷」。这条路走得通的前提是**题目 id 是内容哈希、
跨卷全局唯一**（实测 2115 题零碰撞）；section id 是 `s1/s2/s3`，会撞，所以分组用
section 标题（20 套 N1 卷的 `聴解` 拼写完全一致），part id 前缀源卷 slug。

落库仍然按题回源。`/api/exams/<slug>/answers` 要求 attemptId 且必须属于该卷，所以
一次专题练习会给**每套涉及的源卷各开一个 attempt**（首次答到该卷的题时懒创建），
交卷时逐个 finish。这样专题练习和整卷模考喂的是同一份错题本与 SRS 记录，而不是
另起一套统计。

### 15.5 一条关键的启动顺序改动

`bootstrap()` 原本是一条直线，`bootstrap().catch(showFatalError)` 兜底——课程审计
不过就整页红屏。有了课程库之后这是错的：**课程打不开的时候，正是最需要去列表里换一门
课的时候**。`courses/2010-12-N2` 当前就是 90 错误的阻断状态。

所以 `bootstrap()` 拆成两半：外壳（导航、路由、课程库、个人中心）无条件起来，
`loadActiveCourse()` 的失败被接住存进 `state.courseError`，只在路由到 `#/practice`
时才显示。`stableCourseId(null)` 相应返回 `""`——空 courseId 本来就是各处「没有课程」
的既有约定。

### 15.6 维护规则补充

27. 新页面要进 `sw.js` 的 `SHELL_ASSETS`，并且**必须同时升 `SHELL_CACHE` 版本号**。
    外壳是 cache-first 的，不升版本等于新界面永远到不了老用户。
28. `/api/courses` 返回的 `language` 是对象，`mediaKind` 是 `"remote"`（视频）或
    `"audio"`（本地音频）。渲染前先想清楚拿的是哪个字段。
29. 别在 `bootstrap()` 的外壳那一半里依赖 `state.manifest`。课程可能没加载成功，
    而外壳必须照常起来。
30. 给 `<dialog>` 写样式时，`display` 必须挂在 `[open]` 上。UA 样式表只用一条
    `dialog:not([open]) { display: none }` 隐藏关闭的对话框，而作者样式无条件压过
    UA 来源——写死一个 `display` 就等于让对话框关不掉（`close()` 照常执行，元素照常
    留在页面上）。`tests/dialog_css.test.mjs` 会扫所有能匹配到 dialog 的规则。
33. 前端没有构建步骤，编辑器和浏览器之间没有任何东西检查代码是否还能解析。
    `tests/web_integrity.test.mjs` 补上这一层：每个 `src/web/*.js` 能否编译、
    每个页面脚本引用的 id 是否真的存在、有没有重复 id。改完前端**必须**跑
    `python run_tests.py`——语法错的 app.js 在浏览器里的表现是「顶栏在、下面全空白」，
    没有任何报错指向根因。
34. `bootstrap()` 里 `applyRoute({ withData: false })` 必须留在第一个 `await` 之前。
    两个视图默认都是 hidden，靠它打开其中一个；放到数据加载之后，任何一个请求卡住
    （不是失败，是卡住）都会让整页只剩一条顶栏，而且不会抛错。

32. 跨卷合并真题时，分组键只能用 `section.title`（大类）和 `part.kind`（题型）。
    section id 是 `s1/s2/s3`，跨卷必撞；問題 编号跨卷式会平移。两个都不能当键。

31. 从「我的」跳到某一句，一律走 `goToPractice(index)`，不要自己 `closePersonalCenter()`
    加 `selectSentence()`。个人中心浮在课程库之上，只关弹窗会把人留在课程库里，
    而选中的句子在隐藏的练习视图里——看上去就是「点了没反应」。

## 16. 本地大模型 OCR：扫描 PDF → 数字化文档（2026-09-02）

把图片型 PDF 交给**本地视觉大模型**转成 Markdown / JSON，全程离线。使用与选型说明见
[docs/PDF_OCR.md](docs/PDF_OCR.md)。

### 16.1 新增文件

| 路径 | 用途 |
|---|---|
| `src/pdf_ocr/render.py` | PDF → 页面图片。整页单图的扫描书直接抽出原 JPEG（无损、更快），否则按 DPI 光栅化 |
| `src/pdf_ocr/prompts.py` | 转写 prompt。为「日英中韩四语混排 + 振り仮名」的 JLPT 教材调过 |
| `src/pdf_ocr/backends/qwen_vl.py` | Qwen2.5-VL（transformers，默认） |
| `src/pdf_ocr/backends/dots_ocr.py` | dots.ocr，输出 `bbox + category + text` 版面 JSON |
| `src/pdf_ocr/backends/ollama_vl.py` | Ollama 兜底，只用 urllib，不碰 torch |
| `src/pdf_ocr/assemble.py` | 拼 document.md / document.json，并给可疑页打 flag |
| `src/pdf_ocr/__main__.py` | CLI：`probe` / `run` |
| `scripts/resume_pdf_ocr.cmd` | 续跑脚本，配合计划任务 `ResumePdfOcrN2` |
| `tests/test_pdf_ocr.py` | 页选择、续跑缓存、复读检测、产物拼装（不需要 GPU 与模型） |
| `.venv-ocr/` | 独立虚拟环境（CUDA torch），已 gitignore，不影响项目原有 Python |

### 16.2 和 `exam_import.py` 的关系

`exam_import.py` 故意留了一个洞：`render` 和 `assemble` 之间那一步「读页面」，
它自己不做，要人或大模型来做。**`pdf_ocr` 补的就是这个洞。**

但两者产物不同，别搞混：

- `pdf_ocr` 出的是**通用** Markdown / JSON —— 一页一段文字，给人读、给大模型改。
- `exam_import` 要的是**结构化**的 `p<NN>.json` 区块契约（`question` / `passage` /
  `part-instruction`…），带题号、选项、跨页续接标记。

所以 `pdf_ocr` 的 `document.json` 是喂给模型去产出 `p<NN>.json` 的**原料**，不是
它的替代品。这次处理的是语法教材（不是真题），走不到 exam.json 那条路。

### 16.3 维护规则补充

33. `--max-pixels` 不要凭「模型支持多大就给多大」来设。24 GB 卡上超过 3.2 MP，
    Windows/WDDM **不报 OOM**，而是把显存换页到系统内存，速度塌 7 倍（48 s/页 → 335 s/页）。
    默认值取的是实测装得下的最大值。
34. 分辨率不够时不要再要求模型标振り仮名。看不清它就**编**，比不标更糟。
    `doc-no-ruby` 和默认分辨率是配套的。
35. 每转完一页立刻落盘 `pages/page-NNNN.json`。长文档一定会被打断（限额、断电、
    手滑 Ctrl-C），续跑能力不是锦上添花。
36. 复读（`repetition-loop`）先当成「模型没看清」来治，不要先加 `--repetition-penalty`。
    实测本书 5 处复读全在密排的接続小方框上：penalty 1.05 压不住（有一页反而从 3648 字
    涨到 11193 字），而 `--max-pixels 6422528` 重跑不但消除复读，还多捞回约 28% 内容。
    penalty 压的是症状，分辨率解的是根因。
37. 整页 OCR 会**系统性丢掉浮动的侧栏方框**（本书的语法接続框），而且是整块不输出、
    不报错。加强 prompt 没用（试过），根因是整页要缩放才装得下显存，框里小字先失效。
    解法是 `pdf_ocr boxes` 二次通道：裁右半幅（3.07 MP，不缩放）单独读，
    以 `<!-- box -->` 追加合并，不覆盖正文。~11 s/页 vs 整本 6.4 MP 重跑 ~9.5 h。
38. 给模型看空白图会让它**凭空编内容**（空白页编出了活用表）。凡是"可能没内容"的
    二次通道，先用墨量阈值挡掉（`--min-ink`），程序自己回答，不要问模型。
39. **prompt 里不要写具体的目标语言示例**。box prompt 里举的 `Vない/Vている/Aい+うちに`
    被原样抄进了另一页的输出。要描述结构，不要给样例——样例会变成幻觉的种子。
40. **无损提取内嵌图会绕过页面的 `/Rotate`。** `render.py` 为扫描书走「整页单图直接抽
    原 JPEG」的快路径，但那条路不经过 PyMuPDF 的渲染，页面 `/Rotate` 不会被应用；
    `get_pixmap` 那条路会。日文扫描书大量存成 `/Rotate 180`：本批五本里有三本是
    （N1级汉字 209/212 页、N2级汉字 251/254、N2级词汇 251/251），而且**两本是混的**
    （各有 3 页 `/Rotate 0`），所以必须逐页读 `page.rotation`，不能按书一刀切。
    漏掉它不会报错，只会把 717 页倒着喂给模型，OCR 结果静默作废。
41. 新书开跑前先看一页图再决定 prompt。本批五本里两本是汉字表、两本是题库、一本是
    语法书，只有语法书和 N2 対策 那本像；`boxes` 二次通道对这五本**不适用**
    （它们的方框本身就是正文，跑 box 只会增加过度捕获噪声）。

## 17. 词汇与语法模块（2026-09-02 起；查询 / 学习 / 练习已落地）

按 JLPT 级别组织的**词条与语法条目**，与精听、真题并列的第三类内容。方案见
[docs/LEXICON.md](docs/LEXICON.md)，制作流程见
[docs/LEXICON_PIPELINE.md](docs/LEXICON_PIPELINE.md)，ADR-LEX-001…006 见
[docs/ADR.md](docs/ADR.md)。

本节从 **Phase A（只读链路）** 开始记录，往后合并了词典层与查词、背诵与 SRS、专项练习
与离线能力。当前生效的契约——复习目标身份、事件版本、审核四态、删除语义、先持久化再
发送——见 [docs/ADR.md](docs/ADR.md) 的 **ADR-LEX-007 / ADR-LEX-008**；剩余工作见
[docs/词汇语法模块未完成项详细实现文档.md](docs/词汇语法模块未完成项详细实现文档.md)。

### 17.1 新增文件

| 路径 | 用途 |
|---|---|
| `src/lexicon_schema.py` | 条目数据结构、稳定 ID、接続记法、`prepare_pack` / `audit_pack`（对应 `exam_schema.py`） |
| `src/lexicon_import.py` | OCR 产物 → `pack.json`，三个子命令 `extract` / `assemble` / `validate` |
| `src/lexicon_store.py` | `LexiconStore`（读盘与包内搜索）、`LexiconApiMixin`（`/api/lexicon*` 路由） |
| `src/distribution_policy.py` | 通用发布边界：教材包拒绝进入发布制品，词典层校验署名与字段许可 |
| `src/web/lexicon.html` | 词汇语法工作区（包列表 / 单元浏览 / 包内查词） |
| `src/web/lexicon.css` | 词汇语法样式（复用 `app.css` 的设计变量） |
| `src/web/lexicon.js` | 工作区编排 |
| `src/web/lexicon_markup.js` | 条目文本 → DOM 的渲染器，单独拆出以便单测 |
| `lexicon/N2-grammar-soumatome/` | 第一个内容包（`pack-meta.json` 与 `entry-keys.json` 进库，正文不进） |
| `tests/lexicon_fixtures.py` | 词包测试夹具（自造条目，非教材正文） |
| `tests/test_lexicon_schema.py` | 身份稳定性、审计规则、版权边界 |
| `tests/test_lexicon_import.py` | 单元编号归一、目次对账、接続映射、身份注册表 |
| `tests/test_lexicon_api.py` | 接口、搜索、fail-closed、授权边界、路径穿越 |
| `tests/lexicon_markup.test.mjs` | 渲染器，含注入回归与挖空泄漏回归 |
| `docs/LEXICON_PIPELINE.md` | 制作流水线与执行指南 |

后续批次新增的文件：

| 路径 | 用途 |
|---|---|
| `src/lexicon_content.py` | 学习补充与单词包生成；生成器只写 `machine_checked`，不自授审核 |
| `src/lexicon_exercise.py` | 题目构造与判分；`review_target()` / `answer_version()` / 审核资格 |
| `src/lexicon_index.py` | 内存内容索引，带可供游标校验的 `revision` |
| `src/lexicon_search.py` | 教材 / 词典 / 个人条目的多源游标分页查询 |
| `src/lexicon_learning.py` | 计划设置、方向展开、去重的今日队列 |
| `src/lexicon_practice_store.py` | 专项会话、幂等作答、错题、问题反馈与撤回、个人备份 |
| `src/lexicon_api.py` | 工作区 API（查询、详情、计划、会话、同步、词典安装作业） |
| `src/lexicon_migrations.py` | 有序迁移列表 v1–v5，逐版记录，失败可重跑 |
| `src/dictionary_build.py` | JMdict → SQLite；版本目录 + `current.json` 指针发布 |
| `src/dictionary_store.py` | 只读词典查询、表记/读音/义项兼容性、降级状态 |
| `src/dictionary_jobs.py` | 可查询 / 可取消 / 重启后可识别的词典安装作业 |
| `src/jp_inflection.py` | 归一化、罗马字、去活用候选（含每步词性与代价） |
| `src/web/learning_store.js` | IndexedDB：卡片快照、会话、待发操作 |
| `src/web/learning_cards.js` | 三个页面共用的个人卡片仓库与变更广播 |
| `src/web/lexicon_scoring.js` | 判分的浏览器镜像，与 Python 共用向量 |
| `src/web/lookup_panel.js` | 划词查询；宿主用 `window.LexLookupHost` 声明权限与上下文 |
| `assets/lexicon_seed/word-keys.json` | 单词种子 → entryKey 的身份注册表（一次分配，永不移动） |
| `assets/lexicon_seed/word-adjudications.json` | 匹配歧义的人工裁决（持久，不每次重做） |
| `scripts/lexicon_search_bench.py` | 按卡片规模记录查询延迟（记录数据，不断言阈值） |

改动的既有文件：`src/serve_course.py`（mixin、路由、`/lexicon` 入口）、
`src/release_readiness.py`（接入发布策略）、`src/web/sw.js`（`SHELL_ASSETS`、缓存版本升到
`dictation-shell-v42`）、`src/web/home.html` 与 `home.js`（第三个板块）、
`src/web/app.css`（板块网格改 `auto-fit`、新板块配色）、`start_dictation.py`（多打印一行地址）、
`tests/support.py`（测试服务器接受 `lexicon_root`）、`tests/web_integrity.test.mjs`（三个工作区）。

### 17.2 行为变化

- **同一个服务**：词包挂在播放器的同一进程、同一端口、同一令牌上，和课程、题库并列。
- **一套 schema**：词和语法用 `kind` tagged union 区分，不是两个模块（ADR-LEX-001）。
- **质量门**：`audit_pack` 有错误的包拒绝提供（HTTP 422），与课程、题库的 fail-closed 一致。
- **身份与正文分离**：`entryId` 只由 `packId + entryKey` 派生，订正错字或移动单元不会切断
  学习者的复习历史（ADR-LEX-003）。
- **读音只认来源**：没有 `readingSource` 的读音一律丢弃。OCR 看不清振り仮名时会编，
  编出来的比不标更糟（ADR-LEX-002，[docs/PDF_OCR.md](docs/PDF_OCR.md) 有实测）。
- **版权边界**：教材包不可再分发是强制的，不是一个可以改的标志位；正文、目次转写和
  匹配映射都不进版本库（ADR-LEX-006）。
- **首页**：第三个板块「词汇语法模式」。「我的」仍是跨模式资产，不是第四种练法。
- **Service Worker**：`SHELL_ASSETS` 覆盖词汇语法的全部前端文件。`/api/lexicon/packs`
  与单包响应按 revision 写入 `dictation-lexicon-packs-v1`，用「先写完整数据、再切指针」
  发布，所以中断的写入不会替换掉仍可用的旧副本；其余 `/api/lexicon/*` 仍只走网络。
  页面直接读这个缓存，实现停服后的离线浏览、查询与条目详情。
- **一个能力一张卡**：`reviewTarget = (sourceRef, promptType, variantKey)` 决定长期
  SRS 身份，题目 ID 与答案版本各自独立。计划发卡、顺序学习与专项练习经同一适配器
  （ADR-LEX-007）。
- **学习不必先建计划**：`POST /api/lexicon/introduce` 把「我学过这条」直接变成复习卡，
  走的是 `_materialize_source_card()`——与计划投放同一条身份路径，因此不会出现两张卡。
  没有计划归属的到期卡由 `today()` 的第二个来源覆盖（LEX-06）。
- **删除是意图**：`lex_card_tombstones` 记录删除，内容刷新、计划同步与离线回放都避让它；
  恢复是带版本核对的显式动作。
- **生成不是审核**：`draft → machine_checked → reviewed → withdrawn`。历史上的
  `verified` 按 `machine_checked` 读取，因此两个包共 2,085 条自动模板暂不计入正式练习，
  `capabilities()` 按题型给出原因码。
- **先持久化再发送**：浏览器把操作写入 IndexedDB 后才发请求，回执与待发标记在同一事务
  应用；4xx 业务错误移入 rejected 归档，不重放也不阻塞队列。

### 17.3 维护规则补充

42. `pack.json` 是生成物。改错字改 `lexicon/<包>/pages/` 再重新 `assemble`，不要手改
    `pack.json`——`contentRevision` 对不上会被审计直接拒绝。
43. `units.txt` 里的条目数**必须翻着书数**，不能从 OCR 推。它存在的唯一理由就是抓 OCR
    整块丢失的情况；用同一份 OCR 生成它，等于让检查项去核对它自己。没数过写 `?`。
44. 条目正文永远不经过 `innerHTML`，走 `lexicon_markup.js` 的 `createElement` 路径。
    本模块在题库的 `｜漢字《かんじ》` 之外新增两个标记：`【…】` 接続占位、`⟦…⟧` 挖空。
45. `entry-keys.json` 是唯一进版本库的包文件，只能有 `entryKey / sourceAnchor /
    retired / aliasOf`。加一个「方便调试」的 headword 字段，就是把教材的选词提交上去。
46. 重新 `extract` 之后不要顺手 `--accept-new-keys`。块号变了要把旧 key 指向新 anchor，
    否则学习者已经背了一个月的条目会收到一批全新卡片。
47. 发布检查只扫制品，不扫工作树。开发机上有从自己买的书做出来的包是正常的；一个总是
    失败的检查等于没有检查。
