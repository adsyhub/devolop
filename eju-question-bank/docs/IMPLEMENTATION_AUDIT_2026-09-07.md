# 对剩余实现规格的执行情况、正确性与完整性审查

审查日期：2026-09-07。审查对象：当前目录实际文件，不是旧文档中的完成声明。

需求依据：[20 个工作包的实现规格](UNFINISHED_IMPLEMENTATION_SPEC.md)、[97 项检查项与 61 个验收场景](UNFINISHED_ACCEPTANCE_PLAN.md)。

## 1. 结论

**当前项目只做了部分针对文档的改动，尚未正确、完整实现；而且当前源码已出现阻断运行的回归，不能作为可验收版本。**

有明确的实施痕迹：新增 Schema 调用、区域集合比较、来源结构表、OCR 缓存键/attempt 代码、任务管理类、内容纠错方法、前端冲突合并等。但大量改动将旧代码与新代码同时保留，形成语法错误、重复执行、旧分支提前返回和未接通的服务链。

三个判断分别是：

| 问题 | 判断 | 依据 |
|---|---|---|
| 是否按文档开展了实现 | 是，部分开始实施 | 当前文件相对上轮代码 hash 已变化，新增 jobs.py 和相关测试 |
| 实现是否正确 | 否 | 后端/CLI/前端均存在语法阻断；坏音频、清单误更新、签署不持久化等另有局部反例 |
| 实现是否完整 | 否 | 多数工作包只有部分底层代码或没有新增闭环，真实内容仍未复核 |

按工作包的完整交付条件，目前没有一个剩余包可以凭本次证据签收为“全部完成”。这不是说项目没有现成功能：原始评分、答案映射、部分媒体/安全函数仍有独立测试通过；但全局导入失败使学习和制作主流程无法重新验收。

## 2. 实际验证结果与边界

| 验证 | 实际结果 |
|---|---|
| 全套测试 `pytest -ra -o addopts='' --tb=short` | 退出码 2，**14 个测试模块在收集阶段报错**；没有完成全套执行 |
| 编译检查 eju_bank/scripts/tests 的 Python 文件 | **5 个文件语法/缩进错误**，其中业务包 4 个、脚本 1 个 |
| `node --check eju_bank/web/app.js` | 失败，719 行 `Unexpected identifier 'key'` |
| `node --check` 另外两个自有 JS | learning.js、review.js 语法通过，不等于其页面功能 E2E 通过 |
| `python -m eju_bank --help` | 失败，导入 OCR pipeline 时发生缩进错误；无需启动服务就能复现 |
| `python scripts/sync_schemas.py --check` | 脚本自身缩进错误，无法执行同步检查 |
| 直接解析 canonical schema JSON | content-inventory、page-contract、paper 三份 JSON 非法 |
| 源 schema 与打包 schema 比较 | 上述三份不一致，打包副本仍是另一套内容 |
| 独立可导入的 6 个测试文件 | **16 passed，1 failed**；失败是已有新增用例“拒绝损坏/伪音频” |
| 临时 SQLite 运行 migrator | 可升级到 v5，但缺少新增任务/纠错/媒体来源所需表 |
| 正式数据库只读检查 | 仍为 v4，integrity=ok，1 卷/1 版本/57 题/6 会话 |

14 个收集错误不是 14 个已运行测试断言失败；不能与独立子集的 16 个通过相加得出全套通过率。旧台账的“49 passed”属于上次基线，当前已不成立。

证据文件：

- [环境、文件 hash、语法错误、Schema 与正式库快照](evidence/IMPLEMENTATION_AUDIT_2026-09-07.json)
- [全套测试原始日志](evidence/IMPLEMENTATION_AUDIT_FULL_TESTS_2026-09-07.txt)
- [独立测试子集原始日志](evidence/IMPLEMENTATION_AUDIT_ISOLATED_TESTS_2026-09-07.txt)

本次未修复业务文件、未迁移正式库、未发布或签署真实题目。运行失败后没有通过临时修补业务模块再声称主流程通过。以下局部复现只使用可导入函数、内存/临时数据库及明确说明的替身依赖。

## 3. 按严重程度排序的发现

### F01 / P0：后端、CLI、前端同时无法正常加载

位置：`eju_bank/db.py:29–30`、`ocr/pipeline.py:129–130`、`server.py:138–139`、`sessions.py:307–309`、`scripts/sync_schemas.py:19–21`、`web/app.js:715–731`。

- db.py 保留两个连续 `def __init__`，前一个没有函数体。
- OCR pipeline 保留两个连续 for，前一个没有循环体；后面还残留未结束的 transcribe 调用。
- server.py 存在无语句的 `except Exception:` 后接另一个 except。
- sessions.py 的 result.update 后保留重复字段/闭合符号。
- sync_schemas.py 的 `if args.check:` 后没有函数块。
- app.js 在尚未结束的对象字面量中插入 `const key`，后续还有重复 const/let response、catch/finally 等冲突片段。

影响：Database/Server/Session/OCR 无法导入，命令行 help 失败，浏览器主脚本无法解析。仅修掉编译器报告的第一行不够，需要完整清理新旧片段后再次做全文件语法检查。

需求映射：IMP-01/05/08/15/17/18。验收结论：阻断。

### F02 / P0：Schema 源文件损坏，运行时与源码规范不一致

位置：`schemas/page-contract.schema.json:13`、`schemas/paper.schema.json:34`、`schemas/content-inventory.schema.json:73`、`schema_validation.py:18–20`、`scripts/sync_schemas.py`。

三份 canonical 文件分别报 JSON delimiter 错误。由于 `eju_bank/schemas/` 副本不同，部分页面测试仍然可用，不能据此认定新 Schema 已部署成功。

此外，validator 新增了接受完整文件名的分支，但前面旧的 `schemas[name + '.schema.json']` 仍先执行。实测：

```text
schema_issues('page-contract', {}) -> 返回结构错误列表
schema_issues('page-contract.schema.json', {})
  -> KeyError: page-contract.schema.json.schema.json
```

影响：修复同步脚本后仍会被非法 JSON 阻断；开发目录、打包目录可能验证不同合同。完成标准应是 canonical JSON/Schema 有效、资源完全一致、所有入口与 wheel 校验通过，不能只复制文件或导入一次 validator。

需求映射：IMP-01、A01/A02/P01。验收结论：不正确、未完成。

### F03 / P1：校验器异常时整卷审计直接放过

位置：`eju_bank/audit.py:66–72`。

新增 schema 校验被 `except Exception: pass` 包围。局部故障注入让 schema_issues 抛 RuntimeError，对现有合成合法卷执行 audit_paper 仍返回 `passed`。

这是校验服务不可用时继续通过的行为，与文档要求的 fail-closed 相反。应将校验器自身异常作为阻断错误记录，既不能吞掉异常，也不能把内部路径/正文直接返回用户。

需求映射：IMP-01/02/15。验收结论：不正确。该发现是审计函数层反例，不声称已经完成 HTTP 发布绕过 E2E。

### F04 / P1：新增任务、OCR 尝试、媒体来源和纠错代码缺少数据库/接口链

位置：`migrations.py:467–485`、`jobs.py:39`、`ocr/pipeline.py:183/213/241`、`assets.py:185`、`learning.py:168`、`server.py`。

在临时空库直接执行现有 migrator，得到 schema v5；新增的只有来源结构 baseline 表，以下表不存在：

```text
jobs
job_events
extraction_page_attempts
asset_origins
content_issues
```

在该临时库调用原始 `JobManager.create_job()`，明确报 `OperationalError: no such table: jobs`。这不是“正式库还没升级”的问题，**即使按当前迁移升级到最高版本也缺表**。

同时未找到 server.py 中的 jobs/imports/content-issues 路由、JobManager 接入或后台 worker，也没有对应任务/纠错 UI。测试中出现目标 HTTP 路径不代表服务端已实现它们。

需求映射：IMP-03/05/06/07。验收结论：仅底层片段，不能运行完整业务。

### F05 / P1：坏音频拒绝逻辑被旧异常分支吞掉

位置：`eju_bank/audio.py:45–53`；`tests/test_assets_audio.py:53`。

旧 `except Exception` 仍排在新增 ImportError/MediaError/Exception 处理之前。探测异常先落入旧分支，仍按字节数估时长，后面的“抛出 MediaError”不会执行。

直接使用文本字节作为 MP3 仍返回有效结果；新增测试 `test_probe_audio_rejects_corrupted_or_fake_file` 已实际失败。这里不是“缺测试证明”，而是已有测试明确证明没有修好。

需求映射：IMP-11、J01。验收结论：不正确；cue/播放器/音频分区完整流程也尚未接通。

### F06 / P1：数学 C1 发布仍误更新 C2 清单

位置：`eju_bank/review.py:237–272`。

旧循环先按 `(session, subject, language)` 更新所有命中项并写文件；新增的 inventoryId/expectedForms 精确匹配循环之后再运行。后一个循环不会撤销前一个循环误写的 C2。

局部复现使用两个数学 inventory 项和原始 publish_review 方法，只有发布/证书依赖使用替身，清单写入使用真实临时文件：即使 manifest 明确 `inventoryId=c1`，执行后仍得到：

```text
c1 -> PUBLISHED，blockingIssues=[]
c2 -> PUBLISHED，blockingIssues=[]
```

影响：缺答案的另一门课程被误显示为已发布，并丢掉资料 blocker。数据库成功与清单同步也尚无持久化重试事件。

需求映射：IMP-02、B04/B06。验收结论：修复未生效，局部反例成立；当前完整发布 E2E 被 F01 阻断。

### F07 / P1：来源结构签署没有持久提交，且独立 baseline 仍可缺省

位置：`eju_bank/review.py:158–185`、`188–204`、`audit.py` 的 expectedStructure 检查。

`sign_source_structure()` INSERT 后没有 commit/事务包装。临时文件库中调用后 `connection.in_transaction=True`，关闭连接重新打开，结构表仍为 0 行。签署函数返回成功不等于签署已落盘；接着调用需要 BEGIN IMMEDIATE 的流程还可能冲突。

`candidate()` 在无独立结构时仍从已组装题目生成 baseline，标记 `baselineType=DERIVED` 后继续设 COMPLETE/MOCK；audit 也不拒绝 DERIVED。审计函数层用派生结构和匹配摘要构造的 SOURCE 候选仍 passed，不能发现整段未被录入的问题。

结构模型还不统一：`sign_source_structure()` 只要求 forms 真值，新测试传 forms 数组，而 `candidate()` 期待 forms 是映射并调用 `.items()`。缺少结构 schema、来源哈希/规则 revision 绑定、撤回及发布前当前依赖检查；签署方法也未接入复核 UI/HTTP。

需求映射：IMP-02、B02/B05。验收结论：不正确、不完整。

### F08 / P1：HTTP 新旧处理共存，会重复响应和重复写入

位置：`eju_bank/server.py:160–194`、`213–233`、`526–531`、`754–755`。

从源码可直接确认，health、questions 等分支保留旧 `_json(...)`，随后再次 `_json(...)`；media/outline 等旧分支也可能继续进入新分支。inventory 管理写入先调用 cwd 默认路径，再调用当前 workspace 路径。

即使先解决 F01，这些语义错误仍存在：一个 HTTP 请求可能发两份响应；跨目录操作可能先写错工作区再写正确工作区；精确路由的新分支未替换旧宽松匹配。

需求映射：IMP-15/16/18、N01。验收结论：源码确认不正确；不将被语法阻断的 HTTP 动态行为标为已实测。

### F09 / P1：OCR 计算了缓存键，但没有真正用它验证命中

位置：`eju_bank/ocr/pipeline.py:133–138`、`156–178`、`198–229`。

缓存读取仍先执行“文件存在→校验→cached→continue”，早于图片 hash 和 cache_key 计算；后面的缓存分支也不比较旧输入键与当前输入键。因此 cache key 函数测试通过并不能证明改模型/图片/prompt 会失效。

还缺：run/attempt 输出目录隔离、产物 hash 命中校验、resume_run 来源/配置归属验证、真正页级异常继续处理。provider 抛异常后直接 raise，中断整次循环；质量报告和 run 最终状态没有统一 finally 保证。

需求映射：IMP-05、D01–D03。验收结论：除 F01 语法阻断外，核心缓存/恢复设计也未完成。这里是源码逻辑检查，未通过修改该模块来运行伪修复版。

### F10 / P1：前端冲突/草稿代码不只语法损坏，还存在无效分支

位置：`web/app.js:697–707`、`829–850`。

`readDraft()` 旧 try/catch 均直接 return，新 libraryInstanceId 草稿读取位于其后，永远不会执行。保存确认处旧代码先删除 pending entry，新代码再次判断 entry 才更新 baseResponses，导致该更新条件不成立。

冲突处理虽然加入了三方比较和 generation，但无法据此判定 IMP-08 完成：旧草稿读取、base 状态确认、重复请求片段未清理，主 JS 根本无法加载，跨标签页/慢请求/截止场景没有运行通过证据。

需求映射：IMP-08、G01–G07。验收结论：不正确、未验收。

### F11 / P1：新增区域/媒体检查只完成局部条件

位置：`page_contract.py:218–260`、`assets.py:44–65`。

区域集合不一致会被拒绝，这是已落实的改进，现有相关用例通过。但集合仍是可选项，数量没有由集合派生，也没有验证区域确实对应 block/ignored 处置。局部实测：

```text
inkRegions=99、accountedRegions=99
regionIds=['a']、accountedRegionIds=['a']
validate_page_contract -> passed
```

v1→v2 会标 needsReview，但转换后缺区域证据的页面仍 passed，sign_page 也没有专门检查 needsReview。迁移告警没有形成签署门。

媒体写入新增了临时文件逻辑，但此前旧 `target.write_bytes(data)` 已对新文件写最终路径，首次写入仍不具备所要求的原子性。新来源 metadata 函数依赖缺失的 asset_origins 表，且未接入裁图调用链。

需求映射：IMP-01/02/03。验收结论：部分改进正确，整个工作包未达到完成条件。

### F12 / P1：真实题库未发生文档要求的内容交付

正式库仍是 v4，`page_revisions/paper_reviews/assets/audio_cues/extraction_runs` 均为 0；2023 版本仍为 REVIEW_REQUIRED。2024 五项继续缺独立答案，日本语另缺音频。

现状符合“保持旧错误内容隔离”的保护要求，但不是“真题修订完成”。本次没有重新逐页核对第 41 页；该来源差异结论继续以既有审查记录为依据，不扩张成对全部 57 题的错误断言。

需求映射：IMP-04。验收结论：未完成；真实内容工作和外部资料缺口仍存在。

## 4. 20 个工作包逐项核对

“已有基础”指前一版已存在的能力，不自动记为本轮剩余项已交付。所有依赖 Web/Database 的验收同时受 F01 阻断。

| 工作包 | 当前实际情况 | 判定 | 还缺的核心闭环 |
|---|---|---|---|
| IMP-01 Schema/格式/AST | 加了调用、共享引用、迁移函数、表格渲染；canonical JSON 和同步脚本损坏 | 已尝试，存在错误 | 一致有效 schema、完整入口、迁移签署门、wheel 和浏览器验证 |
| IMP-02 来源/完整度/inventory | 有 v5 结构表和方法、精确匹配新分支 | 部分实现、不正确 | 签署提交、强制独立 baseline、C1/C2 隔离、事务同步、规则版本、合成隔离 |
| IMP-03 媒体 | 新 root 参数、hash 重查、来源登记函数 | 部分实现、不正确 | 首次原子写、metadata 表及调用链、完整历史权限、保留策略 |
| IMP-04 真实内容 | 正式内容和 blocker 未改变 | 未交付、部分外部阻塞 | 2023 64 页实际核对与新发布；2024 答案/音频及逐套制作 |
| IMP-05 OCR/cache | cache key、attempt、参数和测试代码已加入 | 已尝试，无法运行 | 语法清理、真实缓存比较、attempt 表、run 隔离、异常/重试恢复 |
| IMP-06 导入/任务 | 新 jobs.py、测试；没有任务表/worker/HTTP/UI | 仅骨架 | 真正导入执行、资源隔离、租约、幂等、进度与取消 |
| IMP-07 复核/纠错 | 旧复核 UI 仍在；新纠错存储方法/测试 | 部分基础，无完整新链 | 纠错表/路由/UI、版本归属/状态事件、复杂编辑、修订发布关闭问题 |
| IMP-08 会话可靠性 | 新 generation、冲突合并、到期逻辑 | 已尝试，回归阻断 | Python/JS 正确解析、草稿读取/确认修复、跨标签/慢请求/退出测试 |
| IMP-09 分区/组题/导航 | 保留旧 selectedForms/questionIds 与集合组题 | 剩余要求未接通 | section 模型/校验、预览冻结版本、完整导航与数量扩展策略 |
| IMP-10 解析/翻译 | 旧题内解析显示与 explanation 表底座 | 未见新增完整实现 | 独立 revision/审核/撤回、revealed 状态、版本绑定 UI/API |
| IMP-11 音频 | 新异常处理分支，但旧成功降级仍先执行 | 错误且未完整接通 | 真拒绝坏文件、可靠 probe、cue 多题映射、播放器/服务端播放策略 |
| IMP-12 记述 | 原作文保存和待评阅评分保留 | 剩余要求未实现 | 字数统一、空作文、rubric 来源/版本、自评/人工批注链 |
| IMP-13 统计/目标 | 原错题状态和 schedule_review 基础 | 剩余要求未实现 | attempt facts、首答/重练口径、复习事件、时区日历/目标 |
| IMP-14 检索/分页 | 仍扫描卷 JSON；收藏/错题上限与历史摘要重算保留 | 剩余要求未实现 | 查询投影、稳定 cursor、>200 收藏完整恢复、历史按需详情 |
| IMP-15 API 边界 | 新正则分支/HEAD/工作区参数/字段脱敏 | 部分实现、不正确 | 清除旧分支、一次请求一次响应、输入/权限矩阵、授权一致性 |
| IMP-16 数据管理 | 原 ops 快照与恢复基础未变；HTTP 传参有新增 | 未见完整新交付 | 工作区一致快照、制作包、管理 UI、导出/恢复预览 |
| IMP-17 测试/CI | 增加任务、纠错、缓存、音频测试 | 验收失败 | 全套可收集执行、真实断言通过、故障矩阵、CI/发布验证入口 |
| IMP-18 安装/离线 | 原打包配置、本地 KaTeX 和文档基础保留 | 未完成验收 | CLI 可运行、schema 同步、干净 wheel/跨 cwd/Windows 验证 |
| IMP-19 性能/可访问性 | 原页面和样式基础，部分 table 渲染变更 | 未见要求的交付证据 | 大库基准、分页交付、p95/首屏、键盘/焦点/缩放验收 |
| IMP-20 日志/保留 | 原 request ID 和错误类型日志基础 | 剩余要求未实现 | 完整结构化日志、脱敏测试、保留/清理 dry-run、诊断包 |

不使用“完成率 X%”：任务大小不同，且核心运行门未通过，用新增文件数/测试数推算百分比会误导。

## 5. 哪些局部改进有正面证据

1. source/inventory/page 已调用 runtime schema；打包副本支持当前短名称 validator 调用。与上轮“完全没接入”相比有进展，但 canonical 同步损坏仍必须修复。
2. 区域集合差异能够被新增校验识别，相关单元用例通过；还缺数量/处置/签署绑定。
3. 临时空库迁移至 v5 可成功创建不可变来源结构表；不代表新增所有业务表齐备，更不代表正式库已迁移。
4. 独立子集中答案解析、基础选择/评分、部分媒体/安全以及真实 PDF 探测渲染仍通过。真实 PDF 测试验证的是页面属性和渲染，不是题文/答案逐题正确。

这些证据只能支持局部结论，不能据此把依赖它们的整条业务链标成正确完成。

## 6. 修正与重新验收的先后顺序

1. **先恢复可运行基线**：清理全部残留旧片段；Python 编译、JS 检查、canonical JSON/Schema、资源同步、CLI help 必须先通过。此阶段不发布真实卷。
2. **再修真实逻辑缺陷**：坏音频旧 except、inventory 双循环、来源签署事务与强制独立 baseline、HTTP 重复执行、OCR 命中条件、草稿/base 确认与审计吞异常。
3. **补齐数据库和连接链**：新增功能必须有迁移、服务方法、HTTP、UI/worker、异常处理和测试，不能只加类和目标测试。临时 v4→新版与空库两条路径都要验收。
4. **重新执行所有回归**：全套测试必须真正完成，不得仅看到新测试文件；再补冲突、并发发布、跨工作区、坏媒体等反例。受阻前不能宣称 49 passed 延续有效。
5. **逐包补完尚未实现功能**：按原文档依赖推进分区/解析/音频/记述、统计/分页、数据管理、CI/安装/性能/日志。
6. **独立完成真实内容线**：工具可用后执行 2023 全页人工核对，资料到位后推进 2024；合成 E2E 不替代真实签署。

当前适合的项目状态标记是“实施中，存在阻断回归，尚未通过验收”。本次只完成审查与证据归档，不改变业务完成状态。
