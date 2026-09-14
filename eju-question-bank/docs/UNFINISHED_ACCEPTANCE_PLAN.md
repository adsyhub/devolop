# 剩余工作实施检查表与验收方案

基线：2026-09-07。对应 [详细实现规格](UNFINISHED_IMPLEMENTATION_SPEC.md)。以下勾选框全部表示**后续实现任务**，不是本次已完成结果。每包验收同时检查当前已有能力没有退化。

## 1. 已执行的基线检查

| 检查 | 本次结果 | 结论范围 |
|---|---|---|
| `pytest -q -ra` | 49 passed，0 skipped，退出码 0 | 现有测试通过；尚未覆盖所有剩余需求 |
| 正式库只读查询 | schema v4；1 卷/1 版本/57 题/6 会话；integrity=ok，外键异常 0 | 数据结构可读取，不证明内容正确 |
| `python scripts/sync_schemas.py --check` | 退出失败：`Schema resource is stale: common.schema.json` | 打包资源未就绪 |
| 调用 `schema_issues('page-contract', example)` | `KeyError: 'page-contract.schema.json'` | 当前运行时校验器不能直接用于该合同 |
| 检查顶层 `$id` | source-manifest、page-contract、paper、content-inventory 均缺失 | 文件复制后仍需修正 registry 前提 |
| 覆盖集合反例 | 不同 region ID、相同计数，页面返回 passed | 区域语义校验未实现 |
| 伪 MP3 反例 | 普通文本文件返回 1000ms、0Hz | 音频探测失败未阻断 |

证据快照见 [JSON 基线记录](evidence/UNFINISHED_BASELINE_2026-09-07.json)。本次未运行真实 OCR、未逐页签署、未修订正式题库。未完成干净 wheel 安装、性能基准或完整 HTTP 故障矩阵。

额外反例只在内存或临时目录执行。后续复现示例：

```bash
cd /workspace/Develop/eju-question-bank
python scripts/sync_schemas.py --check
```

```python
# 当前预期暴露覆盖校验缺口；IMP-02 完成后应返回 failed。
import json
from pathlib import Path
from eju_bank.page_contract import validate_page_contract

page = json.loads(Path("examples/page-contract-question.json").read_text())
page["coverage"] = {
    "inkRegions": 1,
    "accountedRegions": 1,
    "regionIds": ["a"],
    "accountedRegionIds": ["b"],
}
print(validate_page_contract(page)["status"])
```

## 2. 执行清单

### IMP-01：Schema 与格式

- [ ] 统一 `$id/$ref`、共享定义、嵌套结构限制，资源随 wheel 安装。
- [ ] 校验接入 source/page/inventory/assemble/audit/publish/import 入口。
- [ ] v1 显式迁移为待复核候选，未知字段/版本策略写入文档。
- [ ] 草稿 schema 与可签署 schema 分开；错误定位不回显正文。
- [ ] 表格 AST、ruby、公式、图片在编辑/学习/复盘一致渲染。

### IMP-02：来源与发布门禁

- [ ] 独立结构 baseline、区域集合与全部页处置入库并签署。
- [ ] inventoryId 唯一绑定、C1/C2 隔离、规则配置版本化。
- [ ] COMPLETE/PARTIAL/SECTION/MOCK 按证据派生。
- [ ] 发布/撤回并发安全，清单同步可重试。
- [ ] SYNTHETIC 限定测试/示例通道；恢复交付检查证书。

### IMP-03：媒体

- [ ] 媒体存储原子写入、实际类型及 hash 验证。
- [ ] 元信息、来源关系、旋转/DPI/bbox、引用归属持久化。
- [ ] 同一个 mediaRoot 用于裁图、发布、交付和备份。
- [ ] 停用、新会话、旧会话、历史复盘权限明确并验证。
- [ ] 派生文件清理保留全部历史/草稿/任务引用。

### IMP-04：真实内容

- [ ] 2023 旧卷继续隔离，来源差异登记并关联旧题版本。
- [ ] 56 页题册和 8 页答案册全部有签署或有证据的处置。
- [ ] 每题原文/选项/公式/图/材料/答案逐项核实。
- [ ] 新旧题身份映射审核，旧历史不被覆盖。
- [ ] 新版本附来源、结构、页面、答案、媒体及浏览器证据。
- [ ] 2024 五项资料缺口逐套登记；未到位项保持阻塞。

### IMP-05：OCR 与缓存

- [ ] 渲染/OCR 完整缓存身份、产物摘要和版本信息。
- [ ] 每页每次 attempt 持久化，旧文件不能无条件复用。
- [ ] 单页重试、失败重试、取消/恢复命令可用。
- [ ] 原始模型输出与候选分离，原子写入质量报告。
- [ ] 异常 PDF、像素/磁盘/GPU 限制和错误分类。

### IMP-06：导入与任务

- [ ] 导入向导可选目标、检测重复、显示缺资料。
- [ ] worker 与 HTTP 解耦，资源并发上限和租约恢复。
- [ ] 页级任务进度、错误、重试、取消及产物入口。
- [ ] 不可信上传、路径限制、体积上限和幂等创建。

### IMP-07：复核编辑与纠错

- [ ] 复杂块、答案格、表格、选项图片和跨页材料编辑。
- [ ] revision diff、并发合并、显式撤回与原因。
- [ ] 学习报告问题→维护→修订→发布→关闭全流程。
- [ ] 发布预检显示全部 blocker；旧候选按钮及时失效。
- [ ] 批量处理不绕过逐页签署。

### IMP-08：会话可靠性

- [ ] 保存控制器按 session/generation 隔离。
- [ ] 三方合并 409、响应丢失重试、跨标签页通知。
- [ ] progress/note 版本控制及 libraryInstanceId 草稿隔离。
- [ ] 保存退出/暂停退出/放弃动作与失败恢复。
- [ ] 服务端到期封卷、未确认草稿说明和幂等结果。

### IMP-09：分区、组题与导航

- [ ] sections 模型和服务端选区校验。
- [ ] 条件组题预览冻结版本/材料/顺序/seed。
- [ ] 材料原子选取、题数扩展说明、展开后数量限制。
- [ ] 单题/整卷/未答/存疑、前后题、缺格定位。
- [ ] 移动导航、字体、共享材料与作文游标恢复。

### IMP-10：解析与翻译

- [ ] 独立 revision、适用题版本、作者/来源/审核状态。
- [ ] 管理编辑、签署、撤回及旧题适用性检查。
- [ ] 已提交复盘获取、可选逐题揭示状态与防泄漏。
- [ ] 结果固定 revision，最新解析显式切换。

### IMP-11：音频

- [ ] 删除伪时长成功降级，可靠探测与依赖诊断。
- [ ] 音频导入、派生、cue 及多题/视觉材料关联。
- [ ] cue 越界/重复/重叠/缺映射阻断。
- [ ] 播放器、失败重试、重播/变速和刷新恢复。
- [ ] 模考分区/播放权限由服务端验证。
- [ ] GET/HEAD/Range 协议与授权测试。

### IMP-12：记述

- [ ] 字数口径、题目范围、草稿与空作文状态。
- [ ] rubric 来源、适用版本与审核。
- [ ] 自评/人工评阅/修订独立保存，原答卷不可变。
- [ ] 全文复盘、批注、评价来源清晰，不混入客观分。

### IMP-13：统计与复习

- [ ] 提交事实唯一记录；首答/重练/提示后答题分离。
- [ ] 独立题数/作答次数/未答/答错口径固定。
- [ ] 复习事件、错因、调整日期、掌握/回退历史。
- [ ] 日历、目标、周报、样本量和时区。
- [ ] 活跃时长去重，汇总可重建。

### IMP-14：查询与列表

- [ ] 学习检索投影、完整筛选、稳定 cursor。
- [ ] 收藏/错题/历史取消固定 200 条截断。
- [ ] 快速筛选不被旧请求覆盖、跨页选择行为明确。
- [ ] 停用题保留个人记录、禁止开新练习。
- [ ] 历史只查摘要，详情按需加载。

### IMP-15：API

- [ ] 精确路由、所有字段/体积/类型校验。
- [ ] 未提交白名单 DTO、旧 API 别名同步约束。
- [ ] 本地管理授权与 ADR 一致；远程登录/退出可用。
- [ ] 媒体方法权限和错误码一致、错误不泄漏路径。
- [ ] 发布渠道缓存语义、跨 workspace 写入正确。

### IMP-16：数据管理

- [ ] 同一工作区一致快照及 backup manifest。
- [ ] 学习运行包/完整制作包与引用覆盖。
- [ ] 备份列表、验证、下载、恢复新目录和试启动。
- [ ] 学习报告打印/JSON/CSV 导出及范围限制。
- [ ] 导入预检、冲突预览、不覆盖当前库。

### IMP-17：自动验证

- [ ] 新反例和故障矩阵转成有意义的自动回归。
- [ ] 全科合成材料含音频/复杂 AST/异常输入。
- [ ] unit/API、browser、wheel、private-source 四层分离。
- [ ] 本机验证入口及选定托管平台 CI 接入。
- [ ] 浏览器 job 不静默跳过；失败产物无真实资料。

### IMP-18：安装与手册

- [ ] wheel 资源齐全；工作区路径统一解析。
- [ ] 干净 venv、非项目 cwd、只读安装目录测试。
- [ ] 离线学习/公式/图/历史/备份验证。
- [ ] Linux/Windows 实测记录、extras/doctor 按能力分层。
- [ ] 使用说明、流水线、升级/恢复和 ADR 更新。

### IMP-19：性能与可访问性

- [ ] 大库基准数据/测量脚本与报告。
- [ ] 固定版本分页、图片懒加载、短事务/索引。
- [ ] 键盘、焦点、读屏状态、非颜色提示。
- [ ] 360px/200% 缩放/打印与阅读偏好。

### IMP-20：日志与保留

- [ ] 请求/任务结构化日志与耗时/errorCode。
- [ ] 正文/答案/密钥/路径脱敏检查。
- [ ] 缓存/日志/备份独立保留策略与 dry-run。
- [ ] 清理不破坏历史，诊断可关联恢复手册。

## 3. 自动验收矩阵

表中的测试文件是**建议新增或扩展位置**；不存在的文件不表示已经提交。

| 场景 ID | 输入/动作 | 必须观察到的结果 | 建议位置 |
|---|---|---|---|
| A01 | 非项目目录调用安装包 schema validator | 所有 `$ref` 离线解析成功 | `test_schema_runtime.py`、wheel job |
| A02 | page=true、嵌套错误 AST、重复 slot、超深 children | 稳定校验错误，不能 500 或签署 | `test_page_contract.py` |
| A03 | v1 旧合同缺区域证据→迁移 | 原文件 hash 不变；新草稿待复核 | `test_content_migrations.py` |
| A04 | table cell 含 AST/公式/图片 | 三个页面渲染一致，无对象字符串 | `test_review_browser.py` |
| B01 | region 集合不同但计数相同 | `coverage` 校验失败 | `test_page_contract.py` |
| B02 | 候选缺整科/题/材料；所有现有页均签署 | 与独立 baseline 对账失败 | `test_content_review.py` |
| B03 | PARTIAL 改 COMPLETE；普通来源改 SYNTHETIC | 拒绝提升可信度/免审发布 | `test_assemble_publish.py` |
| B04 | 相同回次/科目/语言的数学 C1、C2，发布 C1 | 仅 C1 inventory 更新 | `test_inventory_cli.py` |
| B05 | 两线程发布同 revision；审批同时撤回 | 不重复版本；撤回后不能发布 | `test_publication_concurrency.py` |
| B06 | 发布成功后 JSON 投影写入失败→重试 | DB 发布唯一，清单最终同步且不误清 blocker | `test_content_review.py` |
| C01 | 自定义 mediaRoot，裁图→发布→GET | 全链路使用该路径 | `test_assets_audio.py`、API |
| C02 | 选项/表格嵌套图缺文件或 hash 错 | 发布失败，定位具体节点 | `test_assemble_publish.py` |
| C03 | 90/180/270 度来源 bbox 裁图 | 与合成页面预期区域一致 | `test_assets_audio.py` |
| C04 | 停用版本后新练习/已有 session/result | 按停用原因执行交付策略 | `test_delivery_lifecycle.py` |
| C05 | 无当前卷引用但旧历史/草稿引用媒体→清理 | 文件保留，报告保留原因 | `test_asset_retention.py` |
| D01 | 改图片/hash/DPI/prompt/model/validator | 正确缓存失效；相同输入命中 | `test_ocr_pipeline.py` |
| D02 | 页 2 超时、页 1 完成、页 3 可处理 | 逐页报告；只重试指定失败页 | `test_ocr_pipeline.py` |
| D03 | worker 中断/输出半文件→恢复 | lease 回收；半文件不命中；审核页不被覆盖 | `test_jobs.py` |
| D04 | 加密/损坏/极大 PDF、磁盘不足 | 明确拒绝或 BLOCKED，不丢来源记录 | `test_pdf_limits.py` |
| E01 | 上传伪扩展名/超限/逃逸路径/重复 hash | 明确响应；来源关系及存储去重正确 | `test_import_jobs.py` |
| E02 | OCR 运行时同时保存答案 | 答案接口正常响应且数据确认 | `test_job_isolation.py` |
| F01 | 报告问题→修改→复核→新版本发布 | issue 关联修订版后关闭，旧历史不变 | `test_review_browser.py` |
| F02 | 两页面编辑同一 baseRevision | 第二写入 409，修改不静默丢失 | `test_content_review.py` |
| F03 | 已 approve 后切源/改内容/撤回签署 | 前端旧 publish 禁用；绕 UI 请求也拒绝 | `test_review_browser.py` |
| G01 | 保存请求延迟期间再次改答案 | 第二次编辑最终确认，旧请求不清新 dirty | `test_browser_learning.py` |
| G02 | 保存成功但响应被丢弃后刷新重发 | 同 requestId 返回原回执，无重复事件 | `test_session_reliability.py` |
| G03 | 两标签分别改同题为不同答案 | 出现冲突选择；解决后保存成功 | `test_session_conflicts_browser.py` |
| G04 | 慢请求中切 session，旧请求随后返回 | 新会话 UI/版本/草稿不受污染 | `test_session_conflicts_browser.py` |
| G05 | 断网临近截止；关闭浏览器到期后恢复 | 以截止前已确认答案封卷，草稿可核对 | `test_session_deadlines.py` |
| G06 | 暂停/放弃/已提交时写答案或进度 | 拒绝；原状态和结果不变 | `test_session_reliability.py` |
| G07 | 同端口换数据库后恢复本机草稿 | libraryInstanceId 隔离，不串会话或笔记 | `test_browser_learning.py` |
| H01 | SECTION 选读解后提交其他区答案 | 服务端拒绝越区写入 | `test_section_sessions.py` |
| H02 | 10 题目标碰到共享材料/atomic group | 展示实际数量，完整上下文及顺序固定 | `test_learning_collections.py` |
| H03 | 预览后发布新版/停用题再创建 | 固定预览版；停用时拒绝并解释 | `test_learning_collections.py` |
| H04 | 数字格部分填→切视图→刷新→交卷检查 | 部分填写状态、缺格和题号一致 | `test_browser_learning.py` |
| I01 | DRAFT/REVIEWED/WITHDRAWN 解析 | 按状态交付；旧结果 revision 可追踪 | `test_review_content.py` |
| I02 | 未提交 MOCK 请求题库/检索/解析/旧 API | 无标准答案、解析正文、答案证据 | `test_learner_payloads.py` |
| I03 | PRACTICE 揭示答案后再答对 | 保存 reveal 事件，不当作无提示首答 | `test_learning_statistics.py` |
| J01 | 文本伪 MP3、坏文件、探测依赖缺失 | 明确失败；不得估算成功时长 | `test_assets_audio.py` |
| J02 | cue 越界/重复/缺题/跨轨乱序/重叠无理由 | 定位问题且不修改输入对象 | `test_audio_mapping.py` |
| J03 | 合成音频播放、seek、断网重试、刷新 | cue/位置/允许速率恢复 | `test_browser_audio.py` |
| J04 | MOCK 刷新重置播放次数或跳下一分区 | 服务端拒绝或恢复既有状态 | `test_section_sessions.py` |
| K01 | 空作文、emoji/换行、边界长度 | 状态和字数前后端一致 | `test_essay_review.py` |
| K02 | 自评→人工评阅→更正评阅 | 正文/旧意见不变，新 revision 可见 | `test_essay_browser.py` |
| L01 | 同题错→对→错，重复调用 submit | 1 道独立题/3 次作答；无重复 facts | `test_learning_statistics.py` |
| L02 | 首答空、第二次有答、先看答案、题目换版 | 按明确口径统计且分母可解释 | `test_learning_statistics.py` |
| L03 | 调复习日、标掌握、跨午夜再次错 | 完整事件链、时区正确、状态回退 | `test_review_schedule.py` |
| M01 | 201+ 收藏/错题/历史，连续翻页 | 无截断/重复/遗漏，恢复收藏准确 | `test_learning_pagination.py` |
| M02 | 检索请求 A 慢，随后 B 快 | 页面最终显示 B | `test_browser_learning.py` |
| N01 | workspace A 启动，cwd 指向 B，写清单/备份 | 只使用 A；B 文件 hash 不变 | `test_workspace_isolation.py` |
| N02 | 发布同内容到不同 channel | 明确渠道效果/拒绝原因，不能误报成功 | `test_assemble_publish.py` |
| O01 | 并发写入/发布时备份，恢复新目录 | 数据/媒体/清单引用一致，旧结果可读 | `test_backup_migrations.py` |
| O02 | 仅草稿或音频引用媒体缺失 | 完整制作包校验失败 | `test_backup_migrations.py` |
| O03 | 损坏 ZIP/缺 DB/重复项/穿越/超限 | 恢复失败且原目标字节不变 | `test_ops.py` |
| O04 | 笔记含换行、引号、CSV 公式前缀→导出 | CSV 正确转义且不会当作公式执行 | `test_data_exports.py` |
| P01 | wheel 在新 venv/不同 cwd/断网启动 | schema、字体、媒体、历史及备份可用 | wheel job |
| P02 | 浏览器依赖未安装 | browser job 明确失败，不能全绿 skip | CI 配置验收 |
| Q01 | 大库负载下搜索/保存/首屏 | 达到约定预算或附明确差距报告 | `benchmarks/` |
| Q02 | 键盘/360px/200% 缩放/模态框焦点 | 核心流程可用，焦点不丢失 | browser+人工记录 |
| R01 | 日志中注入作文/答案/密钥特征串 | 日志/诊断导出无该内容 | `test_logging_privacy.py` |
| R02 | 清理缓存、日志和备份保留 | 历史媒体及最后有效恢复点可用 | `test_retention.py` |

## 4. HTTP 与媒体边界矩阵

此处描述项目目标行为；实施时把具体状态码写入接口合同，再用于所有等价路由。媒体 HTTP 标准细节由实现阶段对照权威协议文档校验，本次没有外网协议核查。

| 维度 | 测试组合 | 目标 |
|---|---|---|
| 路由 | 正确路径、尾随额外片段、编码片段、旧 API 别名 | 精确匹配，未知路由 404，不误触发 submit |
| JSON | 数组/标量/非法 UTF-8/空对象/未知字段/深度超限 | 稳定 4xx，不 500、不静默 coercion |
| 数值 | 负值、0、超上限、布尔、字符串、非有限数 | 严格类型与边界校验 |
| 请求长度 | 无长度、负长度、超限、声明长度与传输不符 | 合同定义处理；超时/超限无部分业务写入 |
| 认证 | 无 token、错误 token、有效 cookie、过期 cookie | 管理/API/媒体策略一致，退出后不可继续访问受保护接口 |
| Host/Origin | loopback、allowlist、伪 Host、不同端口 Origin、无 Origin | 按本地/远程策略校验；无 Origin 不替代身份验证 |
| 媒体 GET | 完整文件、缺资产、停用、草稿、损坏文件 | 交付/拒绝符合引用策略；MIME/长度正确 |
| 媒体 HEAD | 与 GET 同地址/授权；带 Range/缺资产 | 无 body；状态/header 与选定协议行为一致 |
| 单 Range | `bytes=0-0`、`bytes=2-`、`bytes=-4`、end 超文件尾 | 合法范围交付准确字节与 Content-Range |
| 非法 Range | 起点超过末尾、start>end、`bytes=-0`、空范围、多范围、零字节文件 | 明确支持范围；不可满足返回 416；不意外传整文件 |
| 文件路径 | `..`、绝对路径、符号链接逃逸、非法 assetId | 拒绝系统文件读取，不泄漏绝对路径 |
| 发布 | CLI/DB/admin、不同 channel、相同 revision、多并发 | 相同权限门、可解释幂等，无错乱版本 |
| 错误信息 | 来源不存在、provider 异常、SQL busy、坏合同 | 稳定 code/requestId，消息不含用户正文/密钥/内部路径 |

## 5. 数据迁移与真实内容人工验收

### 5.1 每次数据库迁移

1. 从测试夹具建立空库、v1/v2/v3/v4 及本轮前一版数据库；对实际版本中存在的表记录行数与内容 hash。
2. 生成快照后迁移，验证 integrity、foreign keys、不可变触发器、唯一约束及新默认值。
3. 再次迁移无数据变化；注入中途失败，schema 与业务数据一并回滚；比支持版本更高的库拒绝打开。
4. 从迁移前后读取同一个 session/result，题版本和原始答卷一致；统计变更通过版本号说明，不覆盖原结果。
5. 若新增表或引用影响备份，必须同步 verify/restore 与完整制作包测试。

### 5.2 真实页核对模板

逐页记录建议放 `work/{source}/review-evidence/`，不提交公开 CI。

| 字段 | 填写内容 |
|---|---|
| 来源身份 | inventoryId、sourceId、文件 role/hash、物理页码 |
| 区域 | regionId、bbox、坐标系/旋转、保留/忽略及原因 |
| 题目 | form/section/group、原题号、localKey/questionId、前后顺序 |
| 原文 | 题干/选项/公式/标注/跨页材料逐项确认或问题 ID |
| 图表 | 资产 hash、归属节点、截图对照和完整性 |
| 答案 | 独立答案页/区域、answerRef、格位或选项、核对方式 |
| 修订 | base/current revision、差异、旧题身份对应 |
| 签署 | reviewer、确认时间、内容摘要、未解决问题 |

2023 需要 64 个物理页都有处置记录；一页可多题，一题可多页。真正空白/说明页需要原图与处置理由，不能为补覆盖率随意填 ignored。签署不是录入名字即可证明正确，验收人员需实际逐项对照。

### 5.3 每套真实卷的最终门

- 全部必需来源 hash 可验证，明确适用回次、课程和规则配置。
- 独立结构 baseline 与全部题号、页、材料、答案对账通过。
- 签署及审批未过期，必要图片/音频真实可用。
- 从浏览器完成允许的 PRACTICE/SECTION/MOCK 流程；不支持的模式明确不可用。
- 新旧版本差异和历史兼容可解释；inventory 仅更新对应条目。
- 备份并恢复后重读该卷及同一历史结果，内容/媒体不丢失。

## 6. 交付记录模板

```text
工作包：IMP-xx
状态：未开始 / 实施中 / 待验收 / 已完成 / 外部阻塞
修改文件：
代码版本：commit 或文件 hash 清单
数据库迁移：
自动检查：命令、环境、passed/failed/skipped、报告位置
人工验收：场景 ID、操作人员、日期、证据位置
资料依赖：缺少的具体文件/规则/确认事项
兼容性：旧库、旧会话、旧内容的验证结果
剩余事项：
完成日期：
```

只在全部必要证据齐备后勾选“已完成”。资料缺失、平台未测、只有合成 E2E 等情况保留具体边界，不用一个总测试通过数掩盖它们。
