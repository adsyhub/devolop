# EJU 完整题库完善计划与实施规格

> 更新提示（2026-09-07）：本文保留为目标规格，其中现状、成熟度和首轮排期已部分过时。
> 当前源码与实际数据的复核结果、问题证据和后续执行顺序，请以
> [最新项目复核与实施计划](PROJECT_REVIEW_2026-09-07.md) 为准。

> 文档状态：可执行草案（Proposed）  
> 版本：1.0  
> 基线日期：2026-09-03  
> 适用项目：`/workspace/Develop/eju-question-bank`  
> 当前实现基线：`eju-question-bank 0.1.0`

## 1. 文档目的

本文不是现有 `PIPELINE.md` 的重复说明。`PIPELINE.md` 描述“单套 PDF 如何经过 OCR、
组装和发布”；本文定义如何把当前原型完善成一套可持续维护的完整 EJU 本地题库，具体包括：

1. 明确“完整”的范围和不包含的范围；
2. 记录当前能力、已知缺口和必须先做的架构决策；
3. 给出内容、后端、前端、音频、评分、版权、安全、测试和运维规格；
4. 将工作拆成有依赖关系、完成条件和优先级的实施任务；
5. 给出阶段验收门，避免“页面能打开”被误认为“题库已经完成”。

本文是后续开发和题卷导入的主计划；页面事实合同仍以 `docs/PIPELINE.md` 为基础，二者冲突时
必须先更新本文的架构决策，再修改实现。

## 2. 结论摘要

当前项目是一个设计方向正确、边界较清楚的技术原型，但不是完整题库。

- 已有：来源哈希与版权状态、PDF probe/render、OCR provider、页面合同、答案隔离、确定性组卷、
  fail-closed 审计、不可变发布版本、SQLite、基础练习 API、服务端评分、最小 Web UI。
- 当前真实资料：仅有 `2023-2 SCIENCE` 日语理科题册及答案；页面提取目录里只有一页正式页面合同。
- 当前可发布样本：`paper-smoke.json` 只有 `PHYSICS_JA` 的 1 道题，不能代表整套理科试卷。
- 缺少：完整科目与年度内容、听解音频链路、人工复核台、图像资产交付、试卷导航、计时模考、
  历史记录、错题本、解析、数据库迁移、备份恢复、完整 API 校验和端到端测试。

项目应继续采用“本地优先、模块化单体、SQLite、静态 Web 前端”的路线完成第一版。第一阶段
不需要为了形式更换前端或后端框架；先补齐领域模型、数据迁移、媒体交付和质量门。

## 3. “完整题库”的定义

“完整”必须同时满足以下三个定义，不能只按题目数量判断。

### 3.1 能力完整

系统能够表达、导入、展示、作答和复核全部 EJU 科目及题型：

- 日本语：记述、读解、听读解、听解；
- 理科：物理、化学、生物，支持三选二的正式组合规则；
- 综合科目；
- 数学 Course 1、Course 2；
- 除日本语科目外，支持日语卷和英语卷；
- 单选、数学数字格、记述，以及材料、公式、表格、图形和音频。

### 3.2 内容清单完整

“完整”仅指 `content-inventory.json` 中已经登记、来源合法、文件齐全的目标题卷全部完成导入。
它不等于互联网上曾出现过的所有 EJU 题目，也不承诺导入 JASSO 未公开的试题。

每套目标题卷必须具有明确状态：

```text
DISCOVERED -> RIGHTS_CHECKED -> RECEIVED -> PROBED -> RENDERED
-> EXTRACTED -> REVIEWING -> REVIEWED -> ASSEMBLED -> AUDITED
-> PUBLISHED
```

任一题卷处于 `BLOCKED_RIGHTS`、`MISSING_SOURCE`、`MISSING_ANSWER`、`MISSING_AUDIO` 或
`REVIEW_FAILED` 时，清单不得显示为完成。

### 3.3 产品完整

学习者能够在不接触答案密钥的情况下完成选卷、练习/模考、断点续答、提交、查看结果、复习错题
和管理本地数据；内容维护者能够查看 OCR 证据、修订页面合同、运行质量门并发布新版本。

## 4. 官方考试边界

以下规则作为领域模型基线，需在每年升级时重新核对 JASSO：

| 科目 | 作答时间 | 官方得分范围 | 系统要求 |
|---|---:|---:|---|
| 日本语 | 125 分钟 | 读解及听解/听读解 0–400；记述 0–50 | 分区计时、音频、记述分开报告 |
| 理科 | 80 分钟 | 0–200 | 物理/化学/生物选两科；只选一科不得作为正式模考 |
| 综合科目 | 80 分钟 | 0–200 | 不得与理科同时组成正式模考 |
| 数学 | 80 分钟 | 0–200 | Course 1/2 二选一 |

日本语按“记述 30 分钟 → 读解 40 分钟 → 听读解/听解约 55 分钟”的顺序建模。除日本语外，
基础学力科目可选择日语或英语题册，同一正式模考中的基础科目语言必须保持一致。

重要版本边界：从 2026 年第 1 回起，理科、综合科目和数学应用新 syllabus。数据不能只写一个
自由文本年份，必须有可查询的 syllabus ID 和生效回次。

官方除日本语记述外使用尺度分和得点等化。项目没有 JASSO 的项目参数、考生样本和等化模型，
因此只能报告：

- 原始正确数；
- 客观题总数；
- 原始正确率；
- 分科统计；
- 记述“待人工/自评”。

界面、API 和导出中不得将这些字段命名为“官方分数”“预测官方分”或显示成官方 0–200/0–400
尺度分，除非未来获得经过验证且有授权的数据与独立验收。

官方参考：

- 科目、时间、分值和选科规则：<https://www.jasso.go.jp/ryugaku/eju/examinee/procedure/subject.html>
- 考试时间：<https://www.jasso.go.jp/ryugaku/eju/examinee/procedure/examination_time.html>
- 日本语 syllabus：<https://www.jasso.go.jp/ryugaku/eju/examinee/syllabus/japanese.html>
- 2026 年起的各科 syllabus 入口：<https://www.jasso.go.jp/ryugaku/eju/examinee/index.html>
- 得点等化说明：<https://www.jasso.go.jp/ryugaku/eju/about/score/index.html>
- 官方公开的过去问题样本：<https://www.jasso.go.jp/ryugaku/eju/examinee/pastpaper_sample/index.html>

## 5. 版权与内容来源边界

题库的技术可用性不代表题面可以公开传播。每个来源文件必须记录：

- 来源名称、取得方式和取得日期；
- 文件角色、SHA-256、页数、文件大小；
- 权利状态、权利依据、允许渠道、到期日（如有）；
- 是否允许存储、转换、公开展示、商业使用；
- 审核人和审核时间。

权利状态继续使用：

- `PRIVATE_STUDY`：仅本人本机学习；
- `INTERNAL_REVIEW`：仅内容制作和复核；
- `PUBLIC_LICENSED`：具有公开展示依据；
- `COMMERCIAL_LICENSED`：具有商业使用依据；
- `SUSPENDED`：停止交付。

新增两个操作状态：`UNKNOWN` 和 `REVIEW_REQUIRED`。这两个状态只能进入隔离区，不允许发布。

官方 FAQ 说明并非所有实际考题都会公开；官方只提供有限样本，并另行销售过去问题出版物。
因此：

1. 不自动抓取或推定未公开真题；
2. 不把购买纸书/CD 等同于获得公开传播许可；
3. `PRIVATE_STUDY` 数据库默认只绑定 `127.0.0.1`；
4. 导出包默认不包含原始 PDF、音频和答案密钥；
5. 从公共链接取得内容时仍要保存来源 URL、访问日期及适用条款证据。

参考：<https://www.jasso.go.jp/en/ryugaku/eju/faq_eju/examinee.html>

## 6. 当前实现审计

### 6.1 成熟度矩阵

| 模块 | 当前状态 | 成熟度 | 主要缺口 |
|---|---|---:|---|
| 来源登记 | SHA-256、文件角色、rights 已实现 | 70% | 无 inventory、到期日、证据附件、隔离区 |
| PDF probe/render | 全页检测、旋转、切片、缓存已实现 | 75% | 无批任务状态、磁盘配额、产物清理策略 |
| OCR/VLM | 三种 provider 与逐页缓存已实现 | 55% | 无置信度标准化、重试队列、provider 版本追踪 |
| 页面合同 | bbox、AST、coverage、题型校验已实现 | 60% | coverage 只是计数；无 schema 文件和迁移 |
| 人工复核 | 可手工编辑 JSON | 15% | 无复核 UI、差异视图、审核签署和锁定 |
| 答案处理 | 独立 ledger、一一映射已实现 | 65% | 无答案双录校验、答案证据 UI |
| 组卷/审计 | stable ID、revision、fail-closed 已实现 | 65% | 无整卷结构基线、媒体/顺序/计时完整性门 |
| 音频 | manifest 支持 `AUDIO` 角色 | 10% | 无 probe、切分、映射、Range API 和播放器 |
| 图形资源 | AST 可引用 `assetId` | 15% | 当前前端只显示占位符，无裁剪/资源表/交付 API |
| 发布 | SQLite 不可变版本和渠道门禁已实现 | 65% | 无迁移版本、归档/撤回命令、备份恢复 |
| 学习 API | 列卷、取卷、建 session、答题、提交已实现 | 45% | 无分页筛选、批量保存、放弃、历史、错题和媒体 API |
| Web 前端 | 可开卷、作答、提交 | 25% | 无计时、导航、恢复、音频、结果页、移动端完整交互 |
| 评分 | 客观题原始评分、记述待复核已实现 | 55% | 无 rubric、人工评分、题目统计和解释 |
| 测试 | 10 个核心测试及真实 PDF probe 测试 | 40% | 无 API 安全、浏览器 E2E、迁移、备份、音频、全卷 fixture |
| 运维 | 本地 CLI 可运行 | 20% | 无 doctor、结构化日志、健康详情、备份和发布清单 |

### 6.2 当前数据事实

- `sources/`：2023 年第 2 回理科题册 1 份、答案 1 份；
- `work/2023-2-science/probe.json`：题册 56 页、答案 8 页；
- `work/2023-2-science/pages/`：当前只有第 3 页题册合同；
- `paper-smoke.json`：1 个 form、1 道题；
- `eju-smoke.db`：仅用于链路演示，不能升级为正式主库；
- 没有日本语、综合科目、数学题卷，也没有听解音频。

### 6.3 必须保留的正确设计

- 模型只产生逐页事实，不能直接生成最终 `paper.json`；
- 题册提取和答案提取隔离；
- 正确答案不随 learner paper API 返回；
- 发布内容不可变，修订产生新版本；
- 所有客观题必须与答案一一映射，孤立答案必须阻断发布；
- 权利不满足时 fail closed；
- 只报告原始练习结果，不伪造官方尺度分。

## 7. 目标架构

### 7.1 总体结构

```text
sources/                 私有原始文件（不默认进入发布包）
  <source-set>/
work/                    可重建的 probe/render/OCR/review 产物
library/
  eju.db                 正式本地数据库
  media/                 内容寻址媒体资产
  backups/               数据库与清单备份
schemas/                 manifest/page/paper/API JSON Schema
eju_bank/
  ingest/                来源、probe、render、OCR、音频处理
  domain/                题卷、题目、选择规则、评分
  repository/            SQLite 与迁移
  api/                   learner/admin API
  web/                   学习者界面
  review_web/            本地内容复核界面
tests/
  fixtures/              全合成、无版权依赖的 fixture
docs/
```

现有模块无需一次性移动。先用兼容包装拆职责，每次迁移保持 CLI 和测试可用。

### 7.2 运行边界

- 默认单用户、本地离线运行；
- learner API 和 review API 同进程但不同路由权限；
- 默认仅监听 loopback；
- 开启 LAN 访问必须显式配置 token、Host allowlist 和 Origin allowlist；
- OCR 模型是可选的离线制作依赖，不是学习服务器运行依赖；
- 原始 PDF、答案 PDF、模型配置和 provider 密钥不得由静态服务器访问。

### 7.3 版本策略

必须分别版本化：

- `sourceManifestVersion`；
- `pageContractVersion`；
- `paperSchemaVersion`；
- `databaseSchemaVersion`；
- `apiVersion`；
- `promptVersion`；
- `provider/modelRevision`；
- `syllabusId`。

任何版本变化都要有迁移函数、向后兼容测试或明确的拒绝错误，不能静默解释旧数据。

## 8. 内容清单与目录规范

新增 `content/content-inventory.json`，它是“题库是否完整”的唯一统计入口。每一项至少包含：

```json
{
  "inventoryId": "eju-2023-2-science-ja",
  "session": "2023-2",
  "subject": "SCIENCE",
  "language": "ja",
  "syllabusId": "basic-2015",
  "requiredFiles": ["QUESTION_BOOKLET", "ANSWER_KEY"],
  "optionalFiles": [],
  "rightsStatus": "PRIVATE_STUDY",
  "pipelineStatus": "REVIEWING",
  "expectedForms": ["PHYSICS_JA", "CHEMISTRY_JA", "BIOLOGY_JA"],
  "blockingIssues": []
}
```

日本语条目必须将 `AUDIO` 视为听解/听读解发布的必需文件；缺少音频时可单独发布读解和记述练习，
但整套卷必须标记 `PARTIAL`，不能标记完整模考。

推荐目录：

```text
sources/<session>/<subject>/<language>/source-manifest.json
sources/<session>/<subject>/<language>/question.pdf
sources/<session>/<subject>/<language>/answer.pdf
sources/<session>/japanese/ja/audio.<ext>
work/<inventory-id>/probe.json
work/<inventory-id>/renders/
work/<inventory-id>/pages/
work/<inventory-id>/review/
work/<inventory-id>/answers.json
work/<inventory-id>/paper.json
work/<inventory-id>/audit.json
```

文件名可以规范化，但 manifest 必须保留原文件名和哈希。移动后用相对路径，禁止写入某台机器的
用户目录绝对路径。

## 9. 领域与数据模型 v2

### 9.1 题卷模型

`paper` 增加：

- `inventoryId`、`administrationRegion`、`edition`；
- `syllabusId` 和 `syllabusEffectiveFrom`；
- `completeness`：`COMPLETE | PARTIAL | SAMPLE`；
- `availableModes`：`PRACTICE | SECTION | MOCK`；
- `sectionOrder`、`timingPolicy`；
- `mediaManifestRevision`；
- `reviewSummary`；
- `rightsDeliveryPolicy`。

### 9.2 题目模型

`question` 增加：

- `ordinalInForm`、`displayNumber`、`topicTags`；
- `difficulty`（只允许人工标注或统计推导，并记录方法）；
- `explanationAst` 与独立的可见性状态；
- `assetRefs`、`audioCueRef`；
- `sourceLanguage`、`translationAst`、`translationStatus`；
- `reviewState`、`reviewedBy`、`reviewedAt`；
- `contentWarnings`；
- `scoringPolicy`。

翻译、解析和难度不是原题事实，不得混进 OCR 原文；必须带作者、版本和状态。

### 9.3 媒体模型

新增 `assets`：

- 内容寻址 ID（SHA-256）；
- MIME、字节数、尺寸或时长；
- 来源文件、页码/bbox 或音频时间段；
- rights 继承关系；
- derivative 类型（裁剪、缩略图、转码）；
- 完整性哈希。

音频 cue 至少包含：`trackId`、`startMs`、`endMs`、`leadInMs`、`replayPolicy`、`questionRefs`。
原始音频保持不变；浏览器播放使用派生文件，首版优先 Opus/WebM 与兼容性 MP3 二选一或并存。

### 9.4 数据库表

在现有表上增量迁移，至少增加：

- `schema_migrations`；
- `source_files`、`source_rights_evidence`；
- `assets`、`paper_assets`、`audio_cues`；
- `extraction_runs`、`page_revisions`、`review_decisions`；
- `paper_sections`；
- `session_events`（追加式答题事件）；
- `bookmarks`、`question_notes`、`wrong_question_state`；
- `explanations`；
- `content_inventory`；
- `backup_history`。

`responses` 可以保留当前快照，但每次修改必须同时追加 `session_events`，以支持恢复、耗时分析和审计。
不能把仅有最后一次答案的快照当成完整答题历史。

## 10. 内容制作流水线 v2

### 10.1 来源接收

新增命令：

```text
eju-bank inventory init
eju-bank source import
eju-bank source verify
eju-bank source rights
```

接收时先复制到隔离区、计算哈希、检测重复、验证文件类型，不直接信任扩展名。

### 10.2 Probe 与渲染

在现有能力上增加：

- 每页稳定的 `pageId`；
- PDF 页面渲染哈希；
- 极端尺寸、损坏对象、加密和透明层检测；
- 预估磁盘占用和可用空间检查；
- 可重复的 render profile；
- `clean --derived-only` 安全清理命令。

### 10.3 OCR/VLM

每次 extraction run 必须记录：

- provider、模型、revision、量化方式；
- prompt version、推理参数；
- 输入图片哈希、输出原文哈希；
- 开始/结束时间、耗时、重试次数、错误；
- validator 结果和人工复核状态。

模型输出始终视为“不可信候选”。即使 contract 通过，也不能自动将真实题卷标为 `REVIEWED`。

### 10.4 人工复核台

必须提供本地 review UI：左侧原页/切片，右侧结构化字段，并支持：

- bbox 高亮和缩放；
- 原文、公式、上下标、ruby、表格、图形核对；
- 跨页材料合并；
- 题号、答案引用、form/group 修正；
- issue 解决与备注；
- JSON diff；
- 保存草稿、签署复核、撤回签署；
- 快捷键和逐题导航。

复核签署生成新 revision，已签署 revision 不允许原地修改。

### 10.5 图形和表格

`figure` 不能继续只显示占位符。组卷前必须：

1. 识别题目材料、题干和每个选项中的所有必要视觉内容，包括示意图、函数/坐标图、几何图、
   实验装置、电路图、化学结构、地图、照片和图片选项；
2. 按 source page + bbox 生成无损或高质量裁剪，不得用 OCR 文字描述替代原图；
3. 将资产绑定到它实际所属的 material、stem 或 option，并保留图形与正文相对顺序；
4. 图内文字可以同时转录，但必须保留原始图像；
5. 多子图保留 `(a)/(b)` 等子图关系，图片选项逐项绑定，不能合并后丢失对应关系；
6. 记录来源页、bbox、像素尺寸、像素密度、MIME、字节数和 SHA-256；
7. 浏览器显示真实图片并允许缩放，不得只显示 `figure-placeholder`；
8. 原页有必要图片而 page contract、裁剪资产或题目引用任一缺失时，阻断发布。

复杂表格优先结构化为 AST；无法可靠结构化时保留高分辨率裁剪，并设置可访问性说明。

### 10.6 音频

新增 `audio-probe`、`audio-map`、`audio-validate`：

- 校验时长、采样率、声道、codec、静音和削波；
- 允许整轨播放，也支持经人工确认的 cue；
- 听读解必须同时绑定视觉材料；
- cue 不得越界、重叠必须有理由、题号映射必须完整；
- HTTP 支持 `Range`、`HEAD`、正确 MIME 和缓存验证；
- 音频权限不足时 API 不返回可猜测的文件路径。

### 10.7 答案双重校验

正式题卷的客观答案需满足以下任一方式：

- 两次独立录入一致；或
- OCR 录入后由人工逐题对照签署。

答案复核界面必须并排显示答案页证据和题目摘要，但 learner API 永不复用此接口。

## 11. 发布质量门

发布门分为 `SAMPLE`、`PARTIAL` 和 `COMPLETE` 三档。所有档位均要求零 error；warning 必须被显式
签署。`COMPLETE` 还必须满足：

### 11.1 来源门

- 所有必需文件存在且 SHA-256 一致；
- 权利状态允许目标 channel；
- syllabus、session、subject、language 明确；
- 不存在未处理重复文件或来源冲突。

### 11.2 页面门

- 所有题册页、答案页均有 page contract；
- 每页所有检测出的内容区域都有稳定 region ID 和处置结果；
- 不允许未解决 `unreadable`、`cropped`、`formula_uncertain`、`answer_uncertain`；
- 页序、旋转和跨页材料连续性通过检查。

### 11.3 题目门

- form 与预计清单完全一致；
- 题号无缺失、重复或跨 form 冲突；
- 每道客观题恰有一个答案，每个答案恰被使用一次；
- option key、digit-grid slot、材料引用和 asset 引用全部有效；
- 每道题至少有题面 evidence；答案至少有答案 evidence；
- 所有题目已人工签署。

### 11.4 媒体门

- 原页中影响作答的视觉内容 100% 进入 page contract，并由人工对照签署；
- 所有 material/stem/option 的 figure 与 table fallback 资产可读取且哈希一致；
- 图片的题目/选项归属、子图编号、阅读顺序与原卷一致；
- 不允许以 OCR 文字、alt 文本或占位符替代题目原图；
- 需要音频的 section 具有完整 track/cue 映射；
- 媒体权限不低于题卷交付权限；
- 媒体 API 的 Range、越权与路径穿越测试通过。

### 11.5 整卷门

- 科目时间、section 顺序和选科规则与该 syllabus 匹配；
- `COMPLETE` 模式能从头到尾完成一次浏览器 E2E；
- learner payload 中扫描确认没有 `correctAnswer`、answer ledger、源文件绝对路径；
- content revision 可重复构建：相同输入得到相同 revision；
- 审计报告、复核签署和构建清单随发布版本保存。

## 12. 后端 API v1 目标

所有响应使用统一 envelope 和稳定错误码；写接口要求 JSON content type、大小限制和严格字段校验。

### 12.1 学习者接口

```text
GET    /api/v1/health
GET    /api/v1/papers?session=&subject=&language=&status=
GET    /api/v1/papers/{paperId}
GET    /api/v1/papers/{paperId}/outline
GET    /api/v1/papers/{paperId}/questions?form=&cursor=
POST   /api/v1/sessions
GET    /api/v1/sessions/{sessionId}
POST   /api/v1/sessions/{sessionId}/responses:batch
POST   /api/v1/sessions/{sessionId}:pause
POST   /api/v1/sessions/{sessionId}:resume
POST   /api/v1/sessions/{sessionId}:abandon
POST   /api/v1/sessions/{sessionId}:submit
GET    /api/v1/sessions/{sessionId}/result
GET    /api/v1/history
GET    /api/v1/wrong-questions
PUT    /api/v1/questions/{questionId}/bookmark
PUT    /api/v1/questions/{questionId}/note
GET    /api/v1/media/{assetId}
```

### 12.2 本地维护接口

```text
GET    /api/v1/admin/inventory
POST   /api/v1/admin/jobs
GET    /api/v1/admin/jobs/{jobId}
GET    /api/v1/admin/review/pages/{pageRevisionId}
POST   /api/v1/admin/review/pages/{pageRevisionId}:sign
POST   /api/v1/admin/papers/{paperId}:audit
POST   /api/v1/admin/papers/{paperId}:publish
POST   /api/v1/admin/paper-versions/{versionId}:suspend
```

维护接口默认只允许 loopback，并使用单独的短期 admin token。不能因为应用是“本地工具”就让
浏览器任意网页通过跨源请求触发发布或读取原始题面。

### 12.3 Session 语义

- session 固定引用一个不可变 paper version；
- 创建后不能切换到新版题卷；
- `PRACTICE` 可暂停、查看即时反馈（配置允许时）和自由导航；
- `SECTION` 只计一个 section；
- `MOCK` 执行选科和计时规则，提交后不可改答案；
- 服务端保存 `startedAt`、累计 active duration、deadline 和最后活动时间；
- 客户端计时器只负责显示，服务端时间是最终依据；
- 提交必须幂等，重复提交返回同一结果。

## 13. 前端产品规格

### 13.1 题库首页

- 按年度/回次、科目、语言、syllabus、完整度筛选；
- 显示题数、音频状态、权利渠道、版本、最近练习进度；
- 清晰区分 `SAMPLE`、`PARTIAL`、`COMPLETE`；
- 支持继续上次练习，不重复创建 session。

### 13.2 开始配置

- 练习、分区练习、模考三种模式；
- 理科三选二、数学 Course 1/2、语言一致性即时校验；
- 显示考试时间、音频要求和无法组合的原因；
- 模考开始前进行音频测试。

### 13.3 答题界面

- 顶部计时、保存状态、网络/后端状态；
- 题号导航、已答/未答/标记状态；
- 公式排版、ruby、表格、可缩放图形；
- digit-grid 按印刷答题格呈现并支持键盘；
- 听解播放器遵守模式 replay policy；
- 自动保存采用去抖批量提交，离开页面前 flush；
- 页面刷新可恢复当前题号、答案和计时；
- 移动端可用，但不牺牲图表缩放和题号导航。

### 13.4 结果与复习

- 明示“原始练习统计，不是官方尺度分”；
- 总览、分 form、分 topic、已答率、正确率和用时；
- 逐题查看自己的答案、正确答案、题面证据和已审核解析；
- 记述显示 rubric、自评/人工评分状态；
- 加入错题本、收藏和笔记；
- 同一题卷版本可重练，历史结果不可覆盖。

### 13.5 可访问性

- 全键盘操作、可见焦点、语义化 label；
- 不只用颜色表达状态；
- 图像有替代说明，音频有经授权的 transcript 时可选显示；
- 支持 200% 缩放和窄屏；
- 尊重 `prefers-reduced-motion`。

## 14. 评分、解析与学习数据

### 14.1 客观题

- 单选严格比较 option key；
- 数学格严格比较 slot→token，保留前导零和负号；
- 空答与错答分开统计；
- 部分 slot 正确可以展示诊断，但整题正确规则由 `scoringPolicy` 决定并版本化。

### 14.2 日本语记述

第一版不自动宣称得分。支持：

- 保存作文正文、字数和修订次数；
- 展示与题卷版本绑定的 rubric；
- 自评或人工逐项评分；
- AI 建议只能标记为 `AI_FEEDBACK_UNVERIFIED`，与人工评分分栏；
- 不使用未经验证的 AI 数字冒充官方 0–50 分。

### 14.3 解析

解析是独立、可修订内容：

- 原题事实和解析分开存储；
- 每份解析有作者、语言、状态、revision 和来源；
- 只有 `REVIEWED` 解析默认展示；
- 解析不得泄漏到未提交的模考 session；
- 翻译同样需要显式开关和复核状态。

### 14.4 错题状态

错题本不是简单的“曾经答错”。每题状态为：

```text
NEW_WRONG -> REVIEWING -> RETRY_DUE -> MASTERED
```

重练正确不删除历史，仅更新当前掌握状态。首版可用简单间隔规则，后续再引入可配置复习算法。

## 15. 安全与隐私

P0 安全要求：

- 默认 `127.0.0.1`，非 loopback 启动需显式 `--allow-remote`；
- 校验 Host 和 Origin；
- admin 写操作要求 token；
- 禁止静态路径穿越、符号链接逃逸和任意文件读取；
- learner API 永不返回答案密钥、原始来源路径、rights 证据内部备注；
- media ID 不可转换成任意本地路径；
- 请求体、批量答案数、字段长度、作文长度均有限制；
- 日志不记录完整作文、答案密钥、token 或本地敏感路径；
- 数据库启用外键、busy timeout、WAL 策略并有一致性检查；
- 导入的 JSON、图片、PDF、音频都按不可信输入处理。

若未来变成多用户或公网服务，必须另开架构版本补充账户、鉴权、权限、限流、密码与隐私政策；
不能直接把本地版监听到 `0.0.0.0` 当成部署完成。

## 16. 测试策略

### 16.1 测试层级

1. 单元测试：合同、选择规则、评分、stable ID、rights；
2. schema/property 测试：异常 AST、答案格、bbox、路径和 JSON 边界；
3. 数据库测试：每次 migration、事务回滚、不变性、并发保存；
4. API 测试：成功、错误码、越权、幂等、payload 泄漏；
5. 媒体测试：Range、HEAD、断点播放、非法范围和权限；
6. 浏览器 E2E：首页→选卷→答题→刷新恢复→提交→结果→错题；
7. pipeline 集成：合成 PDF/音频到正式发布；
8. 真实私有样本测试：只在文件存在时运行，不进入公共 CI 产物。

### 16.2 必备 fixtures

- 每种 form 至少一题的合成完整卷；
- 单选 2/4/5 个选项；
- 数学多 slot、前导零、负号；
- 日本语记述、读解、听读解、听解；
- 跨页材料、ruby、复杂表格、图片；
- 损坏 PDF、缺页、旋转混合、空白页；
- 缺答案、重复答案、孤立答案；
- 无授权、权利暂停、资产缺失；
- 旧 schema 到新 schema 的迁移样本。

### 16.3 发布测试门

- 所有非慢速测试通过；
- 合成全卷 E2E 通过；
- 当前目标真实题卷 audit 通过；
- learner payload 泄漏扫描为零；
- migration 前后行数、外键和 content revision 校验通过；
- 备份恢复后相同 session/result 可读取。

## 17. 运维、诊断和备份

新增命令：

```text
eju-bank doctor
eju-bank db migrate
eju-bank db check
eju-bank backup create
eju-bank backup verify
eju-bank backup restore
eju-bank inventory status
eju-bank audit --all
```

`doctor` 检查 Python 版本、可选依赖、磁盘空间、数据库 schema、媒体目录、写权限和 provider
配置，但不得输出密钥。

备份包至少包含数据库、content inventory、已发布派生媒体及 manifest；原始 source 是否包含由 rights
和用户选项决定。恢复必须写到新路径并先验证，不直接覆盖当前主库。

日志采用 JSON Lines 或结构化字段，至少包含时间、级别、action、request/job ID、target ID、耗时和
结果；默认保留期与清理方式写入配置。

## 18. 实施阶段与验收

以下为单人专注开发的相对工作量估算，不是日历承诺；真实题卷人工复核时间取决于页数和质量。

### M0：基线冻结与决策（2–3 个工作日）

交付物：

- 本文批准为执行基线；
- `content-inventory.json` schema 与首批清单；
- ADR：本地单用户边界、媒体存储、schema 迁移、官方分数禁用；
- 合成全科 fixture 设计；
- 固定当前 0.1.0 行为测试。

验收：每一个“完整”的判断都能从 inventory 和 audit 得到，而不是人工口头判断。

### M1：数据模型、迁移和媒体底座（5–8 个工作日）

交付物：

- database schema version 与 migration runner；
- assets/media 表、内容寻址存储；
- figure 裁剪生成与 learner media API；
- source 相对路径规范和 rights 证据；
- doctor、db check、备份/恢复最小版本。

验收：从旧 smoke DB 迁移；发布含图题；浏览器显示真实图形；备份恢复一致。

### M2：完整内容制作与复核链（8–12 个工作日）

交付物：

- extraction run 元数据和任务状态；
- page contract v2；
- review UI；
- 答案复核；
- `COMPLETE/PARTIAL/SAMPLE` 审计门；
- 2023-2 理科 56+8 页完成复核与三科组装。

验收：2023-2 理科不是 1 题 smoke，而是 inventory 对应的整卷；所有题、答案、图形有 evidence。

### M3：学习者 MVP 完整化（8–12 个工作日）

交付物：

- API v1；
- 题库筛选、模式配置、题号导航、自动保存、恢复；
- 服务端计时与幂等提交；
- 结果页、历史、错题本、收藏、笔记；
- learner payload 安全测试。

验收：合成理科卷和 2023-2 理科卷均通过浏览器 E2E。

### M4：日本语与音频（8–15 个工作日，不含内容取得）

交付物：

- audio probe/transcode/map/validate；
- Range API 和播放器；
- 日本语四领域顺序与分区计时；
- 记述保存与 rubric；
- 无音频时的 PARTIAL 行为。

验收：合成日本语全卷 E2E；刷新后音频/session 状态可恢复；未提交前不泄漏解析或答案。

### M5：全科兼容与批量内容导入（持续阶段）

交付物：

- 综合科目、数学 C1/C2、日/英卷完整 fixture；
- 2015 与 2026 syllabus 映射；
- inventory 中所有合法目标来源逐套导入；
- 每套独立 audit 与人工签署。

验收：能力矩阵全部通过；inventory 无未解释缺项。内容取得或权利阻塞必须明确显示，不能以假题填充。

### M6：稳定发布（5–8 个工作日）

交付物：

- 完整安装/升级/回滚文档；
- 性能和长 session 测试；
- 安全审计；
- 数据恢复演练；
- release checklist 和版本说明。

验收：干净环境可安装、导入合成卷、启动、完成练习、备份和恢复；旧正式结果不丢失。

## 19. 优先级任务清单

### P0：在继续批量 OCR 前完成

| ID | 任务 | 依赖 | 完成条件 |
|---|---|---|---|
| EJU-001 | 建立 content inventory 与 schema | 无 | 能准确显示当前只有 2023-2 理科且为 REVIEWING |
| EJU-002 | 写 ADR-001 本地单用户/远程边界 | 无 | 默认 loopback 和远程启用条件明确 |
| EJU-003 | 写 ADR-002 schema/DB migration | 无 | 版本、升级、回滚策略明确 |
| EJU-004 | 建立全科合成 fixture | 001 | 13 个 form code 均至少覆盖一题 |
| EJU-005 | database schema version/migrator | 003 | 空库、旧库、重复迁移测试通过 |
| EJU-006 | 资产生成与内容寻址存储 | 004/005 | 图形不再显示 placeholder |
| EJU-007 | page contract v2 + JSON Schema | 004 | v1 迁移、错误信息和 schema 测试通过 |
| EJU-008 | 整卷结构/完整度 audit | 001/007 | smoke 无法冒充 COMPLETE |
| EJU-009 | response 严格类型/长度校验 | 004 | 非法 option、slot、作文长度被拒绝 |
| EJU-010 | Host/Origin/admin token 安全边界 | 002 | 跨站写入和远程误暴露测试通过 |
| EJU-011 | 正式库与 smoke 库分离 | 005 | `library/eju.db` 可重建，smoke 不进入正式清单 |
| EJU-012 | 2023-2 理科逐页复核 | 006–008 | 56+8 页签署，三科完整组装 |

### P1：学习产品完成

| ID | 任务 | 依赖 | 完成条件 |
|---|---|---|---|
| EJU-101 | API v1 和统一错误模型 | 005/009/010 | 合同测试通过，旧接口有迁移期 |
| EJU-102 | session 事件、暂停/恢复/放弃 | 101 | 刷新和进程重启后可继续 |
| EJU-103 | 服务端计时与模式规则 | 102 | MOCK 截止后拒绝写入并幂等提交 |
| EJU-104 | 题库首页与开始配置 | 101 | 过滤、完整度、选科校验可用 |
| EJU-105 | 答题导航与自动保存 | 102 | 状态清楚、批量保存、离开前 flush |
| EJU-106 | 结果/历史/错题/收藏/笔记 | 101–105 | 历史不可覆盖，错题可重练 |
| EJU-107 | Review UI | 006/007 | 原页与结构并排、diff、签署可用 |
| EJU-108 | 解析/翻译独立版本 | 005/101 | 未复核内容不默认展示 |
| EJU-109 | 浏览器 E2E | 104–108 | 主学习路径及恢复路径自动化 |

### P1：日本语和音频

| ID | 任务 | 依赖 | 完成条件 |
|---|---|---|---|
| EJU-120 | audio probe 与资产导入 | 006 | codec/时长/哈希入库 |
| EJU-121 | cue 映射与完整性 audit | 120 | 越界/缺题/异常重叠阻断发布 |
| EJU-122 | Range/HEAD 媒体 API | 010/120 | 浏览器 seek、非法 Range、安全测试通过 |
| EJU-123 | 听解播放器与模考策略 | 103/122 | 重播规则、恢复、错误反馈可用 |
| EJU-124 | 日本语 section 顺序/计时 | 103/123 | 30+40+约55 分钟模型可配置且受服务端约束 |
| EJU-125 | 记述 rubric 与人工/自评 | 108 | 不输出伪官方分，评分来源清楚 |

### P2：稳定性和增强

| ID | 任务 | 完成条件 |
|---|---|---|
| EJU-201 | doctor、结构化日志和 job 诊断 | 无密钥泄漏，错误可定位到 source/page/job |
| EJU-202 | 备份、验证、恢复 | 恢复演练通过且不覆盖当前库 |
| EJU-203 | 性能优化 | 大卷首次加载分页；保存与切题无明显阻塞 |
| EJU-204 | 可访问性审计 | 键盘、焦点、缩放、非颜色状态通过清单 |
| EJU-205 | 内容统计与复习调度 | 统计口径版本化，历史可重算 |
| EJU-206 | 导入/导出包 | rights-aware，默认不含原始来源和答案密钥 |

## 20. 首轮执行顺序

建议下一轮直接按以下顺序实施，不先做 UI 美化：

1. 创建 `schemas/` 和 `content/content-inventory.json`；
2. 写 4 份 ADR：运行边界、数据库迁移、媒体、评分声明；
3. 用合成内容覆盖 13 个现有 form code；
4. 给数据库加 schema migration；
5. 落地 asset 表、裁剪工具和媒体 API；
6. 将 coverage 从“数字相等”升级为 region ID 集合；
7. 增加完整度审计，让 1 题 smoke 只能标为 `SAMPLE`；
8. 实现最小 review UI；
9. 完成 2023-2 理科全页 OCR/人工复核/答案映射；
10. 再扩展 learner API 和前端；
11. 音频能力通过合成日本语 fixture 后，再导入合法的真实音频；
12. 按 inventory 逐卷生产，不并发铺开大量未经复核的 OCR 产物。

## 21. 完成定义（Definition of Done）

项目只有同时满足以下条件才可称为“完整 EJU 本地题库 1.0”：

- 本文第 3.1 节全部能力有实现和自动化测试；
- inventory 中目标条目全部为 `PUBLISHED`，或以明确的外部原因标记阻塞且不计入完成率；
- 至少一套完整卷通过每类核心链路：理科、综合科目、数学、日本语含音频；
- 2015/旧 syllabus 与 2026 新 syllabus 不会混淆；
- 所有真实内容经过人工签署，所有客观答案经过复核；
- learner API 泄漏答案/源路径测试为零；
- 完整练习和模考 E2E 通过；
- 数据库 migration、backup、restore 演练通过；
- 权利状态与交付渠道一致；
- UI 明确说明原始练习统计不是官方尺度分；
- 安装、内容制作、复核、发布、学习、备份文档齐全。

## 22. 待确认决策

这些问题不阻塞 M0 的 schema/fixture 工作，但必须在对应里程碑前确认：

1. 首版仅个人本地使用，还是需要局域网多设备同步？建议首版仅个人本地。
2. 目标内容清单包含哪些年份、回次、科目、语言？必须以用户合法持有的来源为准。
3. 是否已有日本语听解 CD/音频及使用权限？
4. 是否要求中文翻译和解析？建议作为 P1 独立内容层，不阻塞原题导入。
5. 记述采用纯自评、人工评分，还是增加非官方 AI 建议？建议先 rubric + 自评/人工。
6. 是否需要 Windows 原生运行、容器运行或两者都支持？当前文档示例偏 Windows，实际工作区为 Linux。
7. 是否需要公开或商业部署？若需要，必须先完成独立的授权和多用户安全设计。

在这些决策确定前，所有真实题卷继续保持 `PRIVATE_STUDY`，服务默认只监听 loopback。
