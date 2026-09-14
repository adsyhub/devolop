# Miraa 技术规格可吸收能力分析与现有项目改进执行方案

副标题：面向 dictation 本地多语言听写项目的非商业能力吸收、风险治理与实施路线

版本：1.0  
日期：2026-08-19  
适用读者：项目负责人、产品、前端、Python 工程、内容审核、测试与隐私负责人  
分析输入：Miraa_App_Technical_Specification_v1.0.docx 与当前工作区源码/课程/发布包  
明确排除：账号、订阅、支付、套餐、额度、购买恢复、商业权益与云端多用户体系

[[TOC]]

## 1. 执行摘要

### 1.1 总体判断

现有项目不需要推倒重写，也不适合照搬 Miraa 的云端产品形态。最值得吸收的是三条产品与数据设计主线：

1. 以同一个时间句段为中心，联动播放、原文、翻译、注音、解释、听写和 Echo 跟读。
2. 把字幕视为多轨、可修订、可追溯的基础数据，而不是一段只用于展示的文本。
3. 当 ASR、翻译、注音或解释失败、过期或可疑时，仍可回退到原文播放，保留学习连续性，并允许人工纠正。

当前项目已经具备很好的渐进式升级基础：时间戳句段、逐句听写、连续字幕播放、变速与循环、原文和翻译、静态解释、错题与进度、生词/笔记/闪卡、PWA 离线、稳定句子 ID、内容 revision、source-bound 内容补丁、人工审核工具和构建质量门。构建工具支持附加 ASR confidence/diagnostics，但当前默认 manifest 没有这些字段，旧 ZIP 也只部分具备；它们应被视为待恢复的数据血缘，而非既有完整能力。

### 1.2 先稳定、再吸收

在增加 Echo、字幕编辑或 AI 解释之前，必须先完成 Phase 0。审计发现以下问题会直接导致内容错误、数据丢失、更新失效或本地数据被恶意网页访问：

- 默认课程 manifest 自动质量检查为 failed，包含 90 个错误、56 个警告；同一音频的旧发布 ZIP 中存在一份 0 错误、0 警告的最佳已知恢复候选，但其人审仍为 pending，517 段与当前 629 段的差异也尚未解释，不能直接视为正确或可发布。
- 启动器默认每次使用随机端口，而答题进度只存 localStorage；不同端口属于不同 origin，重新启动后用户可能看到“空进度”。
- 离线新增、修改或删除的生词/笔记没有可靠同步队列；后端恢复时可能被 SQLite 全量结果覆盖，删除项也可能复活。
- Service Worker 对 manifest 使用 cache-first，可能让旧 manifest 永久阻止新 revision 被发现；更新时先删旧缓存再下载新缓存，失败后会同时失去新旧离线包。
- 本地 API 的同源判断信任 Host 请求头，已实测伪造 Host/Origin 可以写入数据；GET 数据接口也未使用会话令牌保护。
- 当前自动测试数量为 0，测试、E2E、开发依赖和部分构建证据已被删除，当前目录也没有 Git 历史可用于定位内容回退。

结论：Phase 0 是发布阻断项，不是“以后有空再做”的技术债。

### 1.3 推荐路线与投入

以下估算使用“工程人日”，包含实现、自动化、评审和直接相关的迁移演练，不含外部审批等待、大规模人工逐句听审和硬件采购。数字按第 12 章任务逐项求和，不能用多人并行减少总人日；并行只缩短日历时间。

| 阶段 | 目标 | 估算 | 退出条件 |
| --- | --- | ---: | --- |
| Phase 0 | 内容、数据、安全、缓存、测试基线稳定 | 60–94 人日 | 默认课程达到非商业测试门；数据不丢；伪造请求被拒；离线更新可恢复；自动化恢复 |
| Phase 1 | 四类 schema、ASR 血缘、模块边界、播放器收益 | 49–76 人日 | v1/v2 兼容；字幕层与 Delayed Reveal 可用；N 次重复与状态反馈稳定 |
| Phase 2 | 内容修订、注音点词与结构化解释 | 35–58 人日 | 派生层可追溯；最小编辑闭环可用；日语读音和 SRT 交换通过 |
| Phase 3 | 多课程材料库与本地 Echo | 27–44 人日 | 应用内切课；录音完整生命周期；隐私删除边界与设备兼容通过 |
| Phase 4 | 本地作者任务面板与可选 AI 追问 | 49–79 人日 | 仅在前序阶段稳定后立项；不作为核心学习链路依赖 |

核心范围（Phase 0–3）合计约 171–272 人日。若配置 1 名前端、1 名 Python/全栈和 0.5 名 QA/内容审核，并考虑依赖、返工与真机检查，建议按 21–33 个自然周规划；单一通才全职顺序实施约 35–55 个工作周。Phase 4 单独立项，不纳入首个稳定版本承诺。

Phase 0 的“阻断”针对公开、交付或长期自用的稳定版本。纯前端交互原型可开一条隔离通道，在不读取真实用户数据、不改默认课程指针、不宣称可发布的条件下，用 3–4 人日先验证 PLY-001a；原型结果不能绕过 Phase 0 发布门。

## 2. 分析方法、证据口径与边界

### 2.1 Miraa 文档的使用口径

源文档不是 Miraa 官方内部 PRD，而是基于公开资料整理的技术分析。它把证据分为 A、B、C、I 四级：

| 等级 | 含义 | 本方案使用方式 |
| --- | --- | --- |
| A | 官网、应用商店、隐私政策、条款、版本历史直接确认 | 可作为产品模式参考，但仍按本项目目标重新设计 |
| B | 官方截图或官方社交账号展示 | 可作为交互候选，需要原型验证 |
| C | 用户反馈 | 仅作为问题线索，不直接承诺实现 |
| I | 原文作者为形成技术规格提出的逻辑推断 | 仅作为本项目设计建议；阈值、接口和拓扑必须实测 |

因此，本方案吸收的是已确认的学习交互模式与通用工程原则，不照抄推断出的微服务数量、接口形状或数值 SLA。

### 2.2 现有项目审计范围

本次审计覆盖：

- 启动与运行：start_dictation.py、src/serve_course.py、src/local_backend.py。
- 学习界面：src/web/index.html、app.js、app.css、sw.js、manifest.webmanifest。
- 内容模型与质量：course_schema.py、bundle_quality.py、content_patch.py、human_review.py。
- 构建管线：build_deepseek_offline_bundle.py、ASR 质量与修订工具。
- 当前课程、旧发布 ZIP、项目文档、测试和版本状态。
- 非破坏性语法、API、Range、SQLite、ZIP CRC 和质量审计。

### 2.3 明确不吸收的范围

本方案不包含：

- 登录、注册、邮箱、区域账号、订阅、支付、套餐、额度、应用内购买和购买恢复。
- 云端账号同步、团队空间、多人协作。
- Miraa Drop 或其他附近设备传输。
- 在线视频抓取、绕过登录或 DRM、播客聚合。
- 默认运行时云 ASR/翻译。
- 自动发音评分。
- 在视频需求成立前提前开发视频横屏、全屏和双击手势。

“删除账号”的隐私思想只转化为“本地数据完整导出，并删除应用可控制的副本且披露无法控制的边界”，不引入账号体系，也不承诺法证级擦除。

### 2.4 源文档质量与解释限制

源文件共 17 个渲染页，结构化内容完整，但不是可直接复用的版式模板：多处宽表右侧越界/截断，第 9 页留白异常，第二张图框内文字重叠；第 10 章 AC01–08 存在于文档结构中，却因分页布局在 Word/XPS 渲染中未正常显示。因此本分析同时使用 OOXML 结构抽取和逐页渲染核对，引用以章节为主、页码为辅，并为每项标出 A/B/C/I 或“当前项目审计”。任何在源文档中属于 I 的阈值、接口、状态机或拓扑，都不能被表述为 Miraa 已实际采用。

## 3. 当前项目基线

### 3.1 技术与产品形态

当前项目是“预生成课程包 + 本地逐句听写 PWA”，而不是运行时录音转写应用。

- Python 标准库 ThreadingHTTPServer 提供本地静态服务、音频 Range 和学习数据 API。
- 前端为原生 HTML/CSS/JavaScript，无框架、无构建器；app.js 约 1,897 行。
- 浏览器 localStorage 保存进度及离线回退数据；SQLite 保存生词、笔记和打卡。
- faster-whisper 负责构建期 ASR，DeepSeek 兼容 API 负责翻译与解释，OpenCC 负责中文规范化。
- Service Worker 缓存应用壳、manifest 和完整课程音频。

### 3.2 已有且应保留的能力

#### 学习端

- 听写模式和连续字幕播放模式。
- 逐句播放、上一句/下一句、布尔循环、0.5–1.5 倍速、进度跳转。
- 原文和中文译文同步显示。
- 宽松、变音符号宽松和严格评分；Unicode NFKC 归一化和字符差异显示。
- 三级提示、揭晓、重试、错题跳转、完成率和会话统计。
- 星标、句子笔记、生词、搜索、CSV、随机闪卡和连续学习天数。
- IME 保护、键盘快捷键、skip link、基础 ARIA、响应式和 reduced-motion。

#### 内容与工程端

- 稳定 courseId、v1 manifest 的 `sentences[].id` 与 contentRevision；review/API 学习记录把该值称为 sentenceId，后续 schema 需显式桥接两种命名。
- 构建期音频 SHA-256、resume 校验、批次 source digest、结果数量与字段校验。
- 构建工具可附加 ASR confidence/diagnostics；当前默认 manifest 未携带，旧 ZIP 仅部分句段携带，需在迁移中补齐血缘与覆盖率报告。
- source-bound 内容补丁，防止补丁误应用到另一份 manifest。
- 自动质量审计、人工逐句审核和 ZIP 完整性检查。
- CSP、nosniff、Referrer-Policy、请求体大小限制和安全文件名。

### 3.3 已审计出的关键缺口

| 发现 | 代码/数据证据 | 直接影响 | 级别 |
| --- | --- | --- | --- |
| 默认课程质量 failed | courses/2010-12-N2/manifest.json；重新审计为 90 errors / 56 warnings | 用户直接学习错误或腐坏内容 | P0 |
| 最佳已知恢复候选只在旧 ZIP | ZIP 为 517 片段、431 练习、自动规则 0/0，但 humanListening=pending；前端资源已漂移 | 只能作为候选，需段级 diff、覆盖率和独立听审 | P0 |
| 质量失败不阻断启动 | serve_course.py 只附加 quality；app.js 仅做结构校验 | failed 内容仍正常开放 | P0 |
| 随机端口 + localStorage 进度 | start_dictation.py 默认 port=0；app.js 的 progress 不进入 SQLite | 每次启动可能看到不同进度空间 | P0 |
| 离线修改无可靠同步 | app.js 启动时二选一覆盖；失败请求无 outbox/tombstone | 新增丢失、删除复活、重复记录 | P0 |
| 本地 API 信任 Host | local_backend.py 的 learning_same_origin；伪造 Host/Origin 实测写入成功 | DNS rebinding 可读写本地学习数据 | P0 |
| manifest 循环陈旧 | app.js no-store 与 sw.js cache-first 冲突 | 新课程 revision 可能永远不可见 | P0 |
| 缓存更新非事务 | sw.js 先删旧课程缓存再 addAll 新版本 | 更新中断后无可用离线版本 | P0 |
| Range 每次读取完整音频 | sw.js 将完整缓存 Response 转 ArrayBuffer 后切片 | 21.5MB 音频反复 seek 产生不必要内存/I/O | P0 |
| 自动测试为 0 | unittest discover 返回 NO TESTS RAN；测试/E2E 已删除 | 后续重构没有安全网 | P0 |
| 无 Git/构建证据不完整 | 当前目录不是 Git 仓库；补丁链所需中间证据已删 | 回退不可追踪，旧候选构建不可复现 | P0 |
| 多课程、字幕轨、录音均缺失 | 启动参数一次只载入一个 manifest；Permissions-Policy 禁止 microphone | 无法承载材料库、Echo 和多轨派生数据 | P1/P2 |

### 3.4 当前数据流及问题位置

课程生成链路：

音频 → faster-whisper 分段 → 语言相关合并 → DeepSeek 翻译/解释 → OpenCC → ID/revision → 自动质量审计 → 离线 ZIP

日常学习链路：

start_dictation.py → 随机 localhost 端口 → serve_course.py → manifest/audio → app.js → localStorage；若 API 可用，再把部分生词/笔记/打卡镜像到 SQLite

主要问题是“多源但无统一权威与合并协议”：进度只在浏览器，生词/笔记可能同时存在浏览器和 SQLite，Service Worker 又持有独立课程版本。

## 4. 吸收判断与优先级

### 4.1 值得吸收的三类能力

#### A. 直接提升现有学习体验

- 字幕原文/译文/读音层独立控制。
- Delayed Reveal：固定延迟、句末显示、手动显示。
- N 次逐句重复、跳转步长、自动下一句、缓冲/错误状态。
- 日语读音、词级标注、上下文点词并复用现有生词 Quick Add。
- 结构化解释及 AI 不确定性提示。
- Echo 四步跟读，第一版仅本地录音与人工试听比较。

#### B. 把内容生产与学习闭环连起来

- SubtitleTrack / SubtitleSegment / TokenAnnotation 的多轨数据模型。
- 原文修订后，翻译、注音、解释自动变为 stale。
- 字幕可视编辑、SRT 导入/导出、source-bound patch。
- 多课程材料库与集合。
- 把现有构建 CLI 包装为本地任务面板。

#### C. 吸收工程纪律

- 显式任务状态、稳定错误码、可重试和分层降级。
- 本地数据生命周期、完整导出/恢复/删除。
- 隐私安全诊断，不把完整正文或录音写入普通日志。
- 性能、同步、弱网、隐私和无障碍的可重复验收口径。

### 4.2 候选能力决策矩阵

| 能力 | 当前状态 | 源证据等级 | 决策 | 落地阶段 | 核心原因 |
| --- | --- | --- | --- | --- | --- |
| 内容发布质量门 | 有审计、无启动阻断 | 当前项目审计；非 Miraa 能力 | 立即强化 | Phase 0 | 当前默认内容已回退 |
| 统一持久化与离线对账 | 部分具备 | 当前项目审计；非 Miraa 能力 | 立即重构 | Phase 0 | 存在可复现的数据丢失 |
| 本地 API 会话安全 | 部分具备 | 当前项目审计；非 Miraa 能力 | 立即修复 | Phase 0 | 存在可复现的 rebinding 写入 |
| PWA 版本与可恢复缓存切换 | 部分具备 | 当前项目审计；非 Miraa 能力 | 立即修复 | Phase 0 | 更新和离线承诺不可靠 |
| 自动化与可复现构建 | 曾有、已删除 | 当前项目审计；非 Miraa 能力 | 立即恢复 | Phase 0 | 所有后续能力的安全网 |
| 多轨字幕与派生血缘 | 无 | I：概念模型/接口推断 | 吸收为本项目设计 | Phase 1 | 是层控、注音、修订的共同地基 |
| 字幕层与 Delayed Reveal | 无 | Delayed Reveal=A；层显示=A/B；具体策略=I | 吸收 | Phase 1 | 低成本、高学习价值 |
| N 次重复/跳转/状态 | 部分具备 | 重复/慢速/跳转=A/B；具体档位=I | 增量吸收 | Phase 1 | 最贴近当前精听主线 |
| 词级标注与日语读音 | 无 | 日语读音=A/B；上下文点词=B；字段模型=I | 吸收 | Phase 2 | 直接补齐生词 reading 与上下文 |
| 结构化解释 | 有自由文本 | AI 解释=A/B；五区块结构=I | 增量吸收 | Phase 2 | 易读、可审核、可局部失效 |
| 隐私中心/诊断/无障碍 | 部分具备 | 隐私公开说明=A；NFR/实现方式=I | 横切吸收 | Phase 0–4 | 新交互不能破坏本地优先与可访问性 |
| 字幕编辑与 SRT | 后端已有 patch | 插入、SRT 支持/导出=A；完整编辑=C/I；双向导入=本项目 I | 吸收 | Phase 2 | 能复用审核/补丁工具形成闭环 |
| 多课程材料库 | 仅目录与启动参数 | 材料入口=A/B；分类=C；Collection=I | 吸收 | Phase 3 | 提升日常可用性，复用 courses |
| Echo 本地录音比较 | 无 | 四步法/录音=A；本地保留/状态机=I | 吸收 | Phase 3 | 扩展到主动输出，不引入评分风险 |
| 本地创建课程任务面板 | 有完整 CLI | 素材/任务=A/I；本地面板=本项目设计 | 后置吸收 | Phase 4 | 价值高但后台任务与模型依赖复杂 |
| 标记文本 AI 追问 | 有构建期 AI | 标记提问/追问=B；最小发送策略=I | 条件吸收 | Phase 4 | 必须主动触发、最小上下文、可删除 |
| 在线视频/播客抓取 | 无 | 入口=A/B | 暂不吸收 | — | 版权、DRM、登录与稳定性风险 |
| LRC | 无 | 格式支持=A | 首期不吸收 | — | 当前不是歌词型材料；有真实行级歌词需求后再做 |
| Miraa Drop | 无 | B；安全实现=I | 不吸收 | — | 与单机主线弱，安全/权限成本高 |
| 自动发音评分 | 无 | 未确认 | 不吸收 | — | 源文档明确不可默认推断 |
| 账号/订阅/云同步 | 无 | 商业模块 A/I | 不吸收 | — | 用户明确排除商业订阅方向 |

## 5. 目标产品与技术架构

### 5.1 产品定位保持不变

建议定位为：

“本地优先、真实音频驱动的多语言精听、听写、理解与跟读工具。”

不把它扩张成通用会议笔记、云端内容平台或账号型学习社区。所有新增能力必须至少满足一个条件：

- 提高听辨、理解、记忆或发音自我纠正。
- 提高课程内容生产、修订和质量追踪效率。
- 提高本地数据可靠性、隐私或离线可用性。

### 5.2 架构原则

采用模块化本地单体，不复制 Miraa 文档中的推断微服务。

浏览器端建议逐步拆为：

- app-shell：路由、全局状态、错误边界。
- player-engine：音频时钟、seek、repeat、buffering、播放事件。
- subtitle-engine：轨道选择、当前句、Delayed Reveal、token/ruby 渲染。
- practice-engine：听写、评分、提示、复习状态。
- learning-repository：IndexedDB/localStorage 迁移、outbox、对账状态。
- vocab-notes：生词、笔记、闪卡。
- recording-engine：MediaRecorder、录音状态、blob 生命周期。
- diagnostics：性能、错误、缓存、数据库与隐私安全导出。

Python 端建议形成服务对象，而非马上增加进程：

- CourseCatalogService：发现、验证和打开课程。
- LearningStore：进度、生词、笔记、活动、设置、迁移与备份。
- SubtitleService：轨道读取、修订、版本与 SRT。
- JobService：本地构建任务、阶段、重试、取消。
- SecurityContext：loopback Host、会话令牌、Origin/Fetch Metadata。

### 5.3 存储职责

首期明确采用“浏览器 IndexedDB 为单一浏览器 profile 的离线权威，SQLite 为 companion 在线时按逻辑数据集隔离的耐久备份与恢复副本”。原因是静态 ZIP/PWA 在离线时没有 Python API。profileId 标识可恢复的逻辑数据集；clientId 标识浏览器实例；clientEpoch 在恢复、全量重同步或客户端身份重建时轮换。SQLite 主键命名空间包含 profileId，不合并 Chrome、Edge 或不同 OS profile。正常路径只允许浏览器上行 mutation、服务端确认版本；SQLite 不主动下行覆盖。恢复必须由用户显式选择旧 profile 快照，并创建新 clientEpoch、永久过期旧 epoch；“导入为副本”则生成全新的 profileId/clientId/clientEpoch。首期不承诺跨 profile 强一致，只通过显式导出/导入完成，不建立通用双主系统。

| 存储 | 目标职责 | 禁止用途 |
| --- | --- | --- |
| SQLite | companion 可用时按 profileId 隔离的课程目录、学习数据备份、活动、设置、任务元数据、迁移版本 | 未经加密的密钥；引用浏览器私有且不可解析的 blob；无用户确认的跨 profile 合并 |
| IndexedDB | 当前浏览器 profile 的进度、生词、笔记、设置、outbox，以及句级 Echo blob+元数据同记录事务 | 无 schema version 的永久数据；跨浏览器强一致承诺；忽略配额/持久化拒绝 |
| OPFS | 仅在未来大录音/大草稿确有需要时使用 | 与 SQLite 元数据形成无法原子删除的跨存储引用 |
| Cache Storage | 带 hash 的不可变应用壳和课程媒体 | 未知 revision 的 manifest、可变学习数据 |
| localStorage | 少量非关键 UI 偏好和一次性迁移标记 | 课程进度、生词、笔记、录音、同步权威数据 |

### 5.4 四类版本化数据合同

不要把所有数据都塞进“Manifest v2”。分别定义并独立演进：

1. `course-package-v2`：可携带、可离线验证的媒体引用、字幕轨、句段、词级标注、解释和质量报告。
2. `learning-store-v1`：IndexedDB 权威学习数据及 SQLite 备份副本、mutation、tombstone 和实体版本。
3. `course-catalog-v1` / `app-settings-v1`：课程发现、缓存状态、界面语言和功能开关。
4. `author-job-v1`：构建任务、阶段、输入指纹、中间物保留和清理状态。

源文档的数据模型和状态机主要是 I 级推断；这里吸收的是清晰边界，不宣称 Miraa 使用这些字段。核心实体：

| 实体 | 必要字段 | 说明 |
| --- | --- | --- |
| Course / MediaItem | courseId, title, sourceLanguage, sourceLocale, mediaRef, durationMs, courseContentRevision, legacyContentRevision, state, requiredLayers | v1 contentRevision 映射到 courseContentRevision，并保留 legacy 来源 |
| SubtitleTrack | trackId, kind, language, trackRevision, derivedFromSourceRevision, generatorVersion, state | source 轨的派生字段为空；translation/reading 等派生轨三字段必填 |
| SubtitleSegment | segmentId, trackId, sourceSegmentId, legacySentenceId, startMs, endMs, text, sourceRevision, derivedFromSourceRevision, generatorVersion, state, rawSegmentIds | source 段要求 sourceRevision/rawSegmentIds；派生段要求 sourceSegmentId/derivedFromSourceRevision/generatorVersion/state |
| TokenAnnotation | annotationId, sourceSegmentId, start, end, surface, lemma, reading, phonetic, gloss, derivedFromSourceRevision, generatorVersion, state | 字符跨度单位由 ADR 锁定后才能冻结 schema |
| Explanation | explanationId, sourceSegmentId, summary, vocabulary, grammar, listening, caveats, derivedFromSourceRevision, generatorVersion, state | 结构化、可失效、可单独重算 |
| PracticeProgress | courseId, segmentId, legacyCourseId, legacySentenceId, attempts, bestScore, correct, revealed, hintCount, entityVersion | P0 先用 v1 `(courseId, sentences[].id)`，SCH-001 后迁到 segmentId |
| CourseState | courseId, lastSegmentId, mode, speed, entityVersion | 课程级当前位置与偏好，不重复写在逐句进度中 |
| EchoAttempt | attemptId, courseId, segmentId, sourceRevision, audioHash, recordingBlob, mimeType, durationMs, createdAt, retention | 源句或音频变化时旧录音可识别为历史尝试，不误配当前句 |
| Collection / CollectionItem | collectionId, name；collectionId, courseId, sortOrder | 以关联实体表达课程成员和排序 |
| Job | jobId, sourceFingerprint, configDigest, status, stage, progress, errorCode, attempts, retentionState, cleanupAt | status 表示生命周期，stage 表示当前处理环节 |
| LocalMutation | opId, profileId, clientId, clientEpoch, clientSequence, entityType, entityId, baseVersion, operation, payload, syncState | 浏览器到 SQLite 的离线写入与幂等回放 |
| LanguageCapabilityProfile | language, asr, translation, tokenization, reading, phonetic, structuredExplanation | supported/experimental/unsupported；控制 UI 与 requiredLayers |

关键状态：

- Course：DRAFT → PROCESSING → NEEDS_REVIEW → READY；失败进入 FAILED，用户删除进入 DELETED/ARCHIVED。
- Job.status：CREATED → QUEUED → RUNNING → COMPLETED；可 FAILED/CANCELED。RUNNING 时 stage 为 PREPARING、ASR、ENRICHING、VALIDATING、PACKAGING 或 CLEANING。
- Derived layer：FRESH / STALE / FAILED。
- Echo：IDLE → RECORDING → RECORDED → PLAYBACK / DISCARDED。
- Cache：NOT_DOWNLOADED → DOWNLOADING → READY / FAILED。
- Reconciliation：CLEAN / PENDING / CONFLICT / RESYNC_REQUIRED。

版本语义必须拆开：`schemaVersion` 表示数据合同；`courseContentRevision` 表示课程包内容（v1 `contentRevision` 的规范别名）；`sourceRevision` 表示单个源句；`derivedFromSourceRevision` 表示派生层血缘；`catalogRevision` 表示目录指针；`audioHash` 表示媒体字节。纯文本编辑不得改变 audioHash，缓存策略也不得把这些概念混为一个 revision。

迁移约束：v1 manifest 的 `sentences[].id` 原样写入 legacySentenceId，不因秒→毫秒舍入重新生成；现 review/API 中的 sentenceId 视为同一 legacy 值。新 segmentId 的算法与碰撞策略写入 schema。人工审核结论按 source digest/时间/文本重基：完全未变句段自动沿用，变化或歧义句段回到 NEEDS_REVIEW。`rawSegmentIds` 保留合并前 ASR 片段血缘，便于把低置信度诊断定位回源。当前默认 manifest 缺 confidence/asrQuality，旧 ZIP 只部分覆盖，字段必须允许 unknown，质量报告不得把 unknown 当 pass。

### 5.5 语言设置与能力矩阵

必须分开三种概念：

- interfaceLocale：界面语言，仅影响 UI 字符串、日期和数字。
- sourceLanguage/sourceLocale：学习材料原文语言与文字变体。
- SubtitleTrack.language：一个或多个翻译目标语言；首期 UI 只启用单翻译轨，模型允许后续多轨选择。

每种语言必须通过 LanguageCapabilityProfile 声明 ASR、翻译、tokenization、reading/phonetic、结构化解释的 supported、experimental 或 unsupported。首期只承诺日语 reading/ruby；英语 IPA、韩语注音、中文简繁保持在能力矩阵中，按真实课程量、质量工具和人工审核能力另行排期。RTL 布局先做兼容性设计与 smoke test，不在首期宣称完整支持。

不支持的功能在 UI 中隐藏或解释原因，不能默认所有语言都具有日语级别解析。每门课程的 requiredLayers 决定哪些 stale/failed 层会阻断发布；reading 等可选层不会因为缺失而错误阻断不需要它的课程。

### 5.6 派生数据血缘规则

这是整个升级中最重要的数据正确性规则：

1. 原文或时间边界每次修改都递增 sourceRevision。
2. translation、annotations、explanation 必须记录 derivedFromSourceRevision 和 generatorVersion。
3. derivedFromSourceRevision 不等于当前 sourceRevision 时，状态自动变为 STALE。
4. 播放器可以继续使用原文，但默认不把 stale 派生层当成最新答案展示；审核界面可查看旧值并选择局部重算。
5. 发布质量门禁止 READY 课程包含 stale 或 failed 的必需层。
6. 补丁和审核记录继续绑定 source digest/contentRevision。

## 6. Phase 0：发布阻断项

本阶段预计 6–9 个自然周（上述团队配置），不是 10 天冲刺。顺序为“可恢复备份 → 测试骨架 → 内容候选 → 存储 ADR → 数据库迁移地基 → 安全与稳定 origin 同版交付 → 对账回放 → PWA 两阶段切换 → 备份/导入安全与恢复验收”。纯 UI 原型可并行，但不能读取真实数据或替代发布门。

### 6.1 BKP-001 冻结证据并建立可恢复快照

来源：当前项目审计，非 Miraa 能力。

执行步骤：

1. 在线时使用 SQLite Backup API；做文件级离线快照时先关闭全部连接并确认无事务，再把 db 与存在的 WAL 配对复制。SHM 是可重建协调文件，不作为恢复所需权威内容；不要在连接仍写入时单独复制主库。
2. 保存当前 manifest、音频、旧 ZIP、前端资源、质量报告和构建配置的 SHA-256 清单。
3. 从当前仍能打开的 origin 导出 localStorage/IndexedDB。浏览器禁止跨 origin 枚举，因此随机旧端口的数据只能让用户从浏览器历史找到旧地址、临时重开对应端口后逐 origin 导出；无法保证自动找回未知端口、其他浏览器或已清理的数据。
4. 做一次独立目录恢复演练并记录校验和、工具版本、时间与操作者。

验收：快照只读、校验和一致；恢复副本能打开；缺失 origin 明确列为“不可自动恢复”，不写成已迁移。

### 6.2 ADR-BUILD-001 锁定工具链与 artifact 策略

在重建测试前记录 Node/Python 支持版本、package/requirements 锁文件、Playwright 浏览器版本与安装方式、前端是否引入构建器、模型/大文件 artifact 存放和依赖更新频率。当前方案采用 node:test + Playwright + 单一 Python 测试入口；若 ADR 改选其他组合，FND-002A 需同步调整，不能并存多套无主入口工具链。

### 6.3 FND-002A 恢复版本控制、测试骨架与构建证据

来源：当前项目审计，非 Miraa 能力。

执行步骤：

1. 先搜索 OneDrive 版本历史、旧工作区、发布归档和备份中的 Git、tests、E2E、requirements-dev 与构建证据；找不到时再重建，不能声称“从 Git 恢复”。
2. 初始化正式 Git 基线，制定主分支、发布 tag、课程 artifact 和大文件索引规则。
3. Python 选定 pytest（或坚持 unittest，但只保留一种主入口）覆盖 schema、质量门、patch、迁移、API、Range 和打包。
4. 前端统一选择 Node 工具链：提交 package.json、锁文件、Node 版本、浏览器安装命令；用 node:test 测纯函数，用 Playwright 做浏览器 E2E，避免两套 JavaScript 测试运行器。
5. 固定短音频、固定时钟/假媒体流和小型课程 fixture；测试不得依赖真实 21.5MB 音频或 sleep 猜时序。
6. 小型 build manifest、配置 digest、工具版本、patch 链和质量报告纳入版本控制；大型中间物可放 artifact storage，但必须留 SHA-256、索引、保留期限和取回说明。
7. 自动生成 implementation-facts.json；文档中的测试数、课程段数和质量状态只能引用该事实文件。

首批 P0 测试包括：质量失败阻断、ID 映射、Host/Origin/token、SQLite 迁移、outbox 重放、Range 206/416、Service Worker 崩溃恢复、听写/IME/seek/字幕同步。验收不是“测试数大于 0”，而是所有 P0 场景有稳定用例、主分支无跳过地执行，并能从干净检出重建或取回绑定 artifact。

### 6.4 ADR-CONTENT-001 冻结 P0 legacy ID 与 alias 合同

在任何进度迁移前决定：P0 学习键固定为 `(legacyCourseId, manifestSentenceId)`，其中 manifestSentenceId 来自 v1 `sentences[].id`；`sentenceId` 只是现 review/API 对同一值的命名。courseAliases 与 segmentAliases 都绑定源/目标 courseContentRevision、算法版本和人工确认状态。Phase 1 生成 v2 segmentId 后再执行第二次可回滚迁移，禁止 P0 预先依赖尚未冻结的 segmentId。

### 6.5 FND-001 形成最佳已知内容候选并建立 fail-closed 质量门

来源：当前项目审计，非 Miraa 产品能力。复用 bundle_quality.py、audit_bundle.py、旧 ZIP 候选和现有 ID/revision。

执行步骤：

1. 从旧 ZIP 只提取 manifest 到隔离 staging；不恢复其中已漂移的 app.js/app.css/sw.js。
2. 验证候选与当前音频 SHA-256 相同，并用当前审计工具重新检查。
3. 对当前 629 段/457 练习与候选 517 段/431 练习做时间覆盖率、空洞、文本、翻译、解释和补丁链 diff。当前默认 manifest 没有 confidence/asrQuality；旧 ZIP 仅约 505 段有 confidence、383 段有诊断，报告必须区分“缺失”与“低质量”。
4. 当前两份数据的 v1 `sentences[].id` 交集为 0，courseId 也从当前 `c_b60e098f0bd1653156e5af1a` 变为候选 `c_3184b14ea9048121a2f73f96`。产出版本绑定的 `courseAliases` 与 `segmentAliases`：先按 exact(startMs,endMs,normalizedText) 映射，再以时间 IoU + 文本相似度生成候选，歧义进入人工队列。现审计只有 314/457 个练习片段可完全匹配，禁止全量自动猜测。
5. progress、notes、vocab 按两个 alias 表迁移；无法映射项写入只读迁移档案，并允许用户导出。
6. 先升级 human review 合同：把 `listeningQuality`（听审质量）与 `distributionRights`/商业推荐拆成独立状态，移除 finalize 自动写 `commercialReleaseRecommendation=true` 的耦合。非商业技术测试只依赖前者，不借此宣称拥有分发权利。
7. 建立并启动独立逐句听审工单，记录覆盖率和复审状态；完整听审工作量按音频时长另估，不是 P0 工程退出条件。但 humanListening 未通过时只能称“技术候选/可非商业测试”，不能称 canonical 或可发布。
8. serve_course.py 对 errors>0 默认非零退出；仅显式 --allow-failed-course 允许开发预览。前端持续显示“不可发布”。
9. warning 采用“0 warning”或版本绑定 waiver artifact；waiver 至少含 courseId、courseContentRevision、segmentId、code、reviewer、reason。
10. staging 中生成课程包、质量报告和当前 web 资源；交叉校验后切换一个版本指针，保留旧指针回滚。

验收：技术候选 errors=0，warnings=0 或均有有效 waiver；courseAliases、segmentAliases、段级 diff、时间覆盖、缺失字段和听审队列都绑定 revision；听审/权利状态彼此独立；可映射学习数据无丢失/重复；失败课程普通入口被阻断；新包可追溯到音频 hash、代码 commit、质量报告与构建参数。

### 6.6 ADR-STORE-001 锁定浏览器—SQLite职责

本方案推荐并以此估算：IndexedDB 是单个浏览器 profile 的离线权威；companion SQLite 是按逻辑 profileId 隔离的在线备份/恢复副本；localStorage 只作同 origin 一次性导入。正常对账是上行 mutation + 确认，不做服务端主动覆盖；下行只发生在用户显式恢复/导入，并先预览。ADR 必须在写 outbox 前签署，记录可恢复 profileId、实例 clientId、可轮换 clientEpoch、每 profile 的版本命名空间、跨浏览器不一致边界、最大离线期、冲突策略、备份范围和回滚。若团队改选“Python companion 必需”或真正双主，DAT-001/002 必须重新估算，不能沿用本方案工期。

### 6.7 DAT-003A 先建立 SQLite 迁移地基

执行步骤：

- 使用 PRAGMA user_version 和单事务迁移；每个已发布版本都有向上迁移 fixture。
- `user_version` 高于当前二进制支持范围时 fail-closed：只允许诊断/导出，不写入也不自动降级。
- WAL 是数据库连接的持续模式，不是“写入前后开启”；设置 busy_timeout，并在维护/备份时按需 checkpoint。
- 在线备份使用 SQLite Backup API；文件级离线快照只在全部连接关闭、无活动事务时进行，并把 db 与存在的 WAL 配对保存；SHM 可重建，不当作权威备份内容。
- 每次迁移前生成并验证可恢复备份；旧二进制回滚不做数据库逆迁移，而是恢复该备份后再启动旧版本。备份保留到新版本迁移、读写和恢复演练均通过。
- 启动 quick_check；损坏时隔离原副本，不创建空库覆盖唯一数据。
- 注入杀进程、磁盘满、锁冲突和损坏副本故障，验证未提交事务不会形成半条记录。

### 6.8 SEC-001 修复 DNS rebinding 与本地会话保护

目标边界：阻止外部网页、DNS rebinding 和误连未知本地服务读写本项目数据；不宣称防住同一用户权限下的本机恶意进程、浏览器扩展或系统级恶意软件。

执行步骤：

1. 静态资源和 API 都校验 Host 必须是实际监听的 loopback 地址与端口；绝不从请求 Host 反推“期望 origin”。
2. 启动器在父进程内生成 256-bit token，通过继承管道（次选：短生命周期环境变量并在子进程读取后清除）交给服务；禁止命令行、URL、访问日志和错误页携带 token。
3. 同源应用从 `/api/session/bootstrap` 获取 token：仅有效 loopback Host、`Sec-Fetch-Site: same-origin`、无缓存网络响应；Service Worker 明确绕过该端点，token 只驻留页面内存。服务重启后 401 触发一次重新握手。
4. 除最小无敏感信息的 liveness 外，`/api/*` 的 GET/写入和 companion-ready 探针都要求 `X-Dictation-Token`。启动器自己的 readiness 使用持有的 token。
5. 写请求再校验 Origin 与 Fetch Metadata；非浏览器客户端缺 Origin 时仍必须有 token。敏感响应设 `Cache-Control: no-store`。
6. review_server 移除 URL token及其访问日志泄露；编辑接口与学习 API 使用同一安全上下文。
7. 固定端口与此修复必须同一版本上线。4173 被占用时显示进程/健康检查结果并退出或让用户选择，不自动信任、打开或写入未知进程。

验收：正确 loopback+token 允许；伪造 Host/Origin、cross-site、非 loopback、缺/错 token 的 GET/POST 均拒绝；bootstrap/health/review 路径有独立回归；静态 ZIP/PWA 在无 companion 时仍可学习，只把备份状态显示为离线。

### 6.9 DAT-001 稳定 origin 与统一浏览器学习库

执行步骤：

1. 默认 origin 固定为 `http://127.0.0.1:4173`；随机端口仅保留为显式开发模式，且必须警告会形成独立存储空间。
2. 在 IndexedDB 建立 versioned stores：practice_progress、course_state、vocab、notes、activity、settings、outbox、tombstones、sync_metadata。
3. 当前 origin 首次启动将 localStorage 复制到 IndexedDB，校验计数/digest 后写 migration marker；至少一个发布周期内保留只读旧值。其他旧 origin 只能按 BKP-001 逐 origin 导出/导入，不承诺自动枚举。
4. PracticeProgress 只保存句级结果；CourseState 单独保存 lastManifestSentenceId、mode、speed。P0 使用 ADR-CONTENT 的 `(legacyCourseId, sentences[].id)` 与 courseAliases/segmentAliases；不写尚未定义的 v2 segmentId。
5. 在此任务建立 LearningRepository 接口，先包住现有 `initLearningData/backendRequest/load*` 调用；仓库当前不存在可直接复用的 LearningRepository 类。
6. 所有 UI 写入先完成 IndexedDB 事务再反馈成功；companion 不可用不阻断本地学习。
7. 启动时读取 StorageManager.estimate，主动请求持久化但接受浏览器拒绝；私密模式、配额低、持久化未获准或 IndexedDB 事务出现 QuotaExceeded 时给出可操作提示、允许立即导出，并禁止显示“永久保存”承诺。对关键写入的事务失败不得只记录 console。

验收：同一浏览器/profile 连续重启 10 次数据一致；端口占用不静默切换 origin；同 origin 迁移可重跑且 attempts 不重复；已映射旧句保留，歧义进入报告；模拟配额拒绝、事务失败、私密模式与存储被清理时状态准确且可导出/恢复。跨浏览器一致性明确不在首期承诺中。

### 6.10 DAT-002 浏览器—SQLite 对账、outbox 与墓碑

设计规则：

- 每次浏览器 mutation 含 opId、clientId、clientSequence、baseVersion；先与实体在同一 IndexedDB 事务落盘，再异步回放。
- SQLite 使用独立 `processed_mutations(profile_id, client_id, client_epoch, client_sequence, op_id, entity_version, outcome_code, payload_digest, applied_at)`；`(profile_id, op_id)` 与 `(profile_id, client_id, client_epoch, client_sequence)` 均唯一。只保存最小结果与不可逆摘要，不保存笔记正文或删除 payload。同 opId/sequence 携带不同 digest 必须返回 E-IDEMPOTENCY-MISMATCH，不能复用旧成功。业务更新与 opId 登记在同一事务；不能只在实体保存 last_operation_id，否则 A→B→重放 A 会再次生效。
- 服务端在 `(profileId, entityType, entityId)` 命名空间分配单调 `entity_version`；updatedAt 只用于显示，不作为冲突权威。绝对状态操作优先于“增量 +1”。不同 profile 永不自动覆盖或合并。
- 低风险偏好可基于 baseVersion 明确覆盖；笔记正文冲突保存本地/备份双方副本并要求选择。
- 删除写最小 tombstone（id/type/version/deletedAt），移除正文。另建 `client_watermarks(profile_id, client_id, client_epoch, last_contiguous_sequence, acknowledged_at, status)`。首期建议最大离线期 90 天；processed mutation/tombstone 至少保留离线期加 30 天，且只有所有 active epoch 的连续 watermark 已越过对应 sequence，或该 epoch 已标 EXPIRED 并强制下次全量对账时才回收。期限在 ADR 中按真实使用频率确认。
- 多标签页用 Web Locks 或等价 leader 选举串行回放，并用 BroadcastChannel 刷新状态。

验收：生词、笔记、进度每种增删改在请求前/中/响应后故障均无丢失、重复或复活；种子固定的 50 次故障注入恢复后 outbox 清零、同 profile 版本一致；A→B→重放 A 不改变 B；同 opId 不同 digest 被拒；watermark 有空洞时不回收；过期客户端进入全量对账；两个 profile 使用相同 entityId 时彼此隔离，只有显式导入才产生预览；删除正文不出现在 processed_mutations。

### 6.11 ADR-PWA-001 与 PWA-001 可恢复的两阶段缓存

先用 ADR/性能 spike 决定音频整文件、分块或句级媒体。课程内容 revision 与音频 hash 分离：纯文本修改不得重下同一音频；音频 URL 以 SHA-256 寻址。实现：

1. 区分应用 `manifest.webmanifest`、网络优先的课程目录指针、网络优先且可校验旧值的 course package manifest，以及构建生成的不可变 shell asset manifest。
2. 下载到独立临时缓存；逐项校验 SHA-256（Content-Length 只做完整性辅助，不能替代 hash）；标记 READY 后，在一个 IndexedDB 事务更新 active registry。旧 READY 在新指针提交前保持可用；崩溃重启后按 registry 恢复并清理超时临时缓存。这里是可恢复两阶段切换，不宣称 Cache Storage 与 IndexedDB 跨存储原子。
3. 明确 Service Worker 更新协议：新旧 shell 不混用；`skipWaiting/clients.claim` 只在兼容时启用，否则提示用户刷新后切换。
4. 同一 audioHash READY 时不再下载；删除课程只删没有其他 revision 引用的媒体。
5. 检测 StorageManager.estimate/persist、配额、逐出和隐私模式；READY 每次打开做轻量存在性/metadata 验证，缺资源回退为“需重新下载”。
6. Range 优化在 spike 后选型，并在 Phase 0 实现所选方案；不能带着“每次把完整缓存音频读入 arrayBuffer”退出本阶段。测试同时覆盖在线/离线 206、suffix、416、连续 seek 和共享 audioHash。初始验收为：基准桌面浏览器请求 1MiB 范围时，单次增量 JS heap ≤8MiB，且代码路径不读取完整 21.5MB 响应；若浏览器无法稳定暴露 heap，以浏览器 trace + 分块读取字节数证明，最终阈值由 ADR 锁定。

验收：在线一次刷新内发现新目录/课程 revision；同 audioHash 刷新 20 次网络音频传输为 0；下载、校验、指针提交任一点崩溃都能打开旧 READY；缓存被浏览器逐出后 UI 不误报；临时缓存可回收，无活跃资源被误删；Range 达到上项已记录的内存/读取门。

### 6.12 DAT-003B 备份、恢复与删除边界

定义两种产物：默认“学习数据备份”以 IndexedDB 权威快照为核心，包含 profileId、clientId/epoch、实体版本、未确认 outbox、tombstone、每客户端 watermark 和设置；Echo blob 由用户显式勾选。Cache Storage/课程媒体不进入该备份，可按 audioHash 重新下载。SQLite Backup API 产物只作 companion 灾备/诊断，恢复时不得反向覆盖较新的浏览器数据；如果浏览器数据丢失，用户从备份列表选择逻辑 profile 快照后，以新 clientEpoch 恢复并把旧 epoch 标为 EXPIRED。“恢复为副本”生成新 profileId/clientId/epoch，过期 epoch 永不复活或重放。

导入先在 staging 解析并验证 schemaVersion、校验和、导出清单、大小/记录上限、路径穿越、ZIP bomb、重复 ID、未知字段策略和版本降级。验证通过后，在一个覆盖相关 object stores 的 IndexedDB 事务中替换；任意错误/中断使事务 abort，旧权威数据保持不变。随后用 mutation 回放重建 SQLite 副本，不把两份快照做“最新时间”合并。必须测试解析中断、事务中断、磁盘满、旧/新 schema 和再次恢复。

备份可能含笔记、词条和录音，未加密文件必须在导出前提示。轮换策略、保留数、WAL/临时文件和用户自建副本均在隐私中心列明。删除只承诺移除应用可控制的 IndexedDB、Cache Storage、SQLite、WAL、任务 staging 与托管备份；浏览器内部存储残留/逐出实现没有可观察验证 API，连同用户复制、系统备份、SSD 残留和外部供应商数据一起披露为不可控边界。

### 6.13 ERR-001A P0 错误合同

在功能扩张前落地最小错误对象 `{code, stage, retryable, userAction, diagnosticId}`，覆盖 E-COURSE-QUALITY、E-DB-MIGRATION、E-SEC、E-CACHE、E-IMPORT。所有 P0 阻断页给出恢复动作和诊断 ID，不显示堆栈、用户名、绝对路径、Host、token 或完整学习正文。

## 7. Phase 1：模型与播放器快速收益

### 7.1 MOD-001 渐进拆分 app.js

来源：当前项目审计；模块边界参考源文档 I 级逻辑组件，不复制其服务拓扑。

不做大爆炸重构。每次只围绕一个已被测试覆盖的功能切片：

1. 先抽纯函数：时间索引、评分、格式化、状态 reducer。
2. 再抽 player-engine，并保持现有 DOM 适配层。
3. 再把 DAT-001 建立的 LearningRepository 接入模块边界，不另造第二套存储抽象。
4. 最后抽 subtitle-engine、vocab-notes 和 diagnostics。

模块之间通过显式事件和数据对象通信，禁止任意模块直接修改全部全局 state。

验收：

- 每次拆分前后 E2E 行为一致。
- app.js 主入口只负责组合，不再承载全部业务细节。
- 不为拆模块强制引入大型框架；是否引入构建器单独做 ADR。

### 7.2 ADR-SPAN-001 冻结 TokenAnnotation 索引单位

在 course-package schema freeze 前，以前后端实现成本和 Unicode fixture 决定 span 使用 UTF-16 code unit 还是 Unicode code point，并记录 JavaScript/Python 转换函数、规范化前后文本规则与错误处理。样本必须含代理对、组合字符、全半角、emoji、换行、ruby 和标点；决定后写入 schema 与生成器版本，禁止混用。

### 7.3 SCH-001 四类 schema 的兼容层与迁移

来源：源文档第 5–6 章概念模型/接口，证据等级 I；字段、revision 和兼容策略均为本项目决策。

执行步骤：

1. 分别发布 course-package、learning-store、catalog/settings、author-job 的 schema 与版本策略；先冻结 content package，其他合同不可借“Manifest v2”隐式耦合。
2. 保留 v1 adapter：复用现有 `source_text()` / `translation_text()` 的字段优先级（如 jaText、zhTranslation），再把 sourceText/translationText/explanationText 映射为轨道/解释；用冲突 fixture 防止旧副本覆盖审核后的权威别名。v1 `sentences[].id` 保存为 legacySentenceId。
3. 时间统一为整数毫秒并记录舍入；segmentId 不因舍入变化。TokenAnnotation 索引单位 ADR 在 schema freeze 前决定，并覆盖代理对、组合字符、全半角与规范化测试。
4. 定义 sourceRevision、derivedFromSourceRevision、generatorVersion、layer state、rawSegmentIds、requiredLayers 与 unknown ASR 元数据语义。
5. patch、人工审核和进度均提供 v1 ID → v2 segmentId 重基报告；未变句自动继承，歧义句回到 NEEDS_REVIEW。
6. 课程读取、质量门、review、打包和前端全部支持 v2；至少一个版本周期双读，是否双写由迁移 ADR 决定。

验收：

- 仓库内全部 v1 课程无需手工修改即可播放；fixture 至少覆盖有/无可选字段和未知 ASR 元数据。
- 同一 v1 输入多次迁移得到相同 segmentId 与 canonical JSON digest，legacySentenceId 保持不变。
- 原文编辑后相关派生层自动 stale；未受影响句段保持 fresh。
- 质量门能定位 track/segment/derived layer。

### 7.4 LIN-001 让 ASR 诊断支持合并、拆分与重基

来源：当前项目审计，非 Miraa 能力。现 `asr_quality.py` 要求 manifest 与 raw segment 数量、时间、文本一一相等，但 builder 会先合并句段；直接引入 rawSegmentIds 会触发 ValueError 或丢失诊断。

执行：把 attach/质量逻辑从“一一对应”改为 lineage-aware 聚合；每个 source segment 记录一个或多个 rawSegmentIds、覆盖时间、聚合 confidence/警告和算法版本。拆分时按时间覆盖分配或标 NEEDS_REVIEW，合并时保留有序父列表；旧内容重基输出 matched/partial/ambiguous/unmatched。fixture 覆盖 1→1、N→1、1→N、边界微调、空洞和重叠，并与人工审核状态联动。任何未知血缘不得伪造成高置信度。

验收：现 builder 合并路径不再因数量不等报错；诊断可追到 raw 片段；拆分/合并后 source digest、低置信度和听审队列一致；重复运行结果确定。

### 7.5 PLY-001a v1 快速收益：原文/译文层与基础 Delayed Reveal

来源：Miraa §3.4、§3.5、§3.10，源文档 p7–p9；Delayed Reveal=A，层显示=A/B；本实现策略=I。

该切片可在隔离原型或 Phase 1 最早交付，不等待 SCH-001：复用现有 sourceText/translationText，提供原文/译文开关以及 immediate、manual、after_segment。设置写入现有偏好适配层，随后由 learning-store 迁移。隐藏内容不占空白、不进入可访问树；seek、换句、暂停和模式切换必须取消旧 reveal 状态。

验收：三种策略在播放、暂停、seek 和换句下无上一句泄漏；关闭层不留空位；manual 全键盘可用；读屏在 reveal 前读不到答案。

### 7.6 PLY-001b v2 层控：读音、多翻译轨与媒体时间延迟

依赖：SCH-001、PLY-001a。首期 UI 仍只启用一个翻译目标；当 package 实际包含多个 translation track 时才显示目标语言选择，不触发运行时云翻译。

功能：

- 原文、选中译文轨、读音/音标分别开关。
- 在 PLY-001a 基础上增加 `after_ms`，延迟值以媒体时间计算。
- 设置可选择全局或按课程保存。
- 隐藏内容不占空白，也不提前进入无障碍树。

关键实现：

- 以 audio.currentTime 和当前 segment 边界驱动，不使用孤立 setTimeout 作为权威时钟。
- seek、换句、调速、暂停、切轨、模式切换时取消旧 reveal 状态。
- 固定延迟以媒体时间计算；0.5x/1.5x 下行为一致。
- 保留 current source segment，即使 translation/reading 失败也能播放。

验收：

- 四种策略在正常播放、暂停、seek、调速、切轨和换句下均无上一句泄漏。
- 关闭任一层不留异常空位。
- manual 模式全键盘可操作。
- 屏幕阅读器在 reveal 前读不到隐藏答案。

### 7.7 PLY-002 N 次重复、跳转步长和状态反馈

来源：Miraa §3.5、§3.10，源文档 p7、p9；重复/慢速/跳转=A/B。以下档位是本项目原型默认值（I），需可用性测试后锁定。

功能：

- repeatCount：1、2、3、5、infinite。
- ±2 秒/±5 秒跳转；不越过课程合法边界。
- 可选“本句结束自动下一句”。
- waiting、stalled、buffering、error、ended 有可见且可访问状态。
- 速度、重复、跳转偏好持久化。

实现要点：

- 句尾比较使用统一 epsilon，避免浮点误差多播或少播。
- 快捷键在 textarea、IME composing 和 dialog 中不触发。
- sentenceIndexAtTime 从线性扫描改为预排序数组 + 二分查找。
- timeupdate 不再每次重绘所有 64 个波形节点；只在可见差异时更新。

验收：

- repeat=N 精确播放 N 次，可随时停止或切下一句。
- 冻结的 629-segment legacy/dev fixture（质量 failed，不作为普通课程入口）持续播放 30 分钟无错误高亮；另对最终技术候选运行同一用例。
- 播放、暂停、切层、点词等本地操作初始目标 P95 ≤ 250ms；这是本项目待实测目标，不是 Miraa 官方 SLA。

## 8. Phase 2：内容修订与理解闭环

先交付最小字幕修订闭环，再生成注音和结构化解释；否则错误原文会继续污染派生层。

### 8.1 EDT-001 审核台字幕编辑、patch v2 与 SRT 交换

来源：Miraa §3.8、§4.4，源文档 p8、p10；字幕插入、SRT 支持/导出=A，完整文本/时间编辑=C/I，双向导入与 patch 设计=本项目 I。它是内容正确性工具，不是普通学习功能。

分两步交付：

1. 最小版先支持原文、startMs/endMs 编辑、头尾 padding 预听、草稿恢复和 source-bound patch；复用现有 `src/review_server.py`、`src/review_web` 与 content_patch。
2. 完整版增加译文、插入、删除、拆分、合并、筛选低置信度/重叠/缺翻译/可疑字符/stale 层，以及 UTF-8 SRT 导入/导出。EDT-001A 的最小编辑和格式设计先进入 SEC-002B；只有安全用例通过后才开放 SRT 导入和结构操作。LRC 继续后置。

现有 patch 主要是非空 `replace_range`，不足以表达结构编辑。patch v2 至少包含 opId、baseContentRevision、preconditionDigest、operation、targetSegmentId、parentSegmentIds、newSegmentIds、payload、author、timestamp、reason；operation 明确区分 replace_text、move_boundary、insert、delete、split、merge。服务端检测 base revision 与目标摘要，冲突时生成可审阅差异，不以最后写入静默覆盖。拆分/合并保留父子 lineage，旧学习进度按显式规则汇总/复制并进入人工确认。

校验：非空文本、start<end、媒体范围、排序、重叠策略、最短/最长时长；原文/时间变化递增 sourceRevision 并只把受影响派生层置 STALE。SRT 是单轨、有损交换格式，不携带多轨关系、解释、token、review 或 lineage，不能作为完整备份。只有“同一轨、刚导出、未编辑、立即导入”的内部 fixture 才要求段数/文本一致、整数毫秒差≤1ms；外部 SRT 按解析/舍入报告验收。

验收：错误 digest/revision 被拒；非法块给稳定错误码且草稿不丢；保存后播放器预览新时间轴；发布前重新跑质量门；拆分/合并的 ID、派生失效和学习数据迁移均有报告。

### 8.2 ADR-LNG-001 选择日语解析来源并锁定估算

仓库当前没有日语 tokenizer/词典依赖。先用冻结样本比较至少两个可离线方案，记录 lemma/reading/未知词质量、许可证、模型/词典体积、版本固定、启动时间、构建速度、分发限制和维护成本；gloss 可来自现有构建期增强，但必须与 tokenizer 结果分层并允许 unknown。选择失败时回退到“仅 ruby/人工 reading + 现有文本选择”，不阻断原文。LNG-001 的 8–12d 是该 spike 后的暂定实施估算；若许可证、体积或质量不满足，回到 Backlog 重估而不是硬承诺。

### 8.3 LNG-001 TokenAnnotation、日语读音与上下文点词

来源：Miraa §3.4、§3.7，源文档 p7–p8；日语读音=A/B，上下文点词=B，字段模型与 span 规则=I。

目标：点击句中词查看词形、读音和句中义，并复用现有生词 Quick Add。构建期首期只为能力矩阵中 supported 的日语生成 surface、lemma、reading、gloss 和 span；前端用 ruby。无标注、unsupported 或 stale 时回退到现有文本选择。

span 必须绑定未归一化 source text；UTF-16 或 Unicode code point 由 ADR 统一，不能前后端各选一种。测试集按日文假名/汉字/标点、全半角、组合字符、代理对、emoji 与换行分层，并在文档记录课程数、句数、token 数和随机种子；“100% 不越界”只针对该冻结样本。审核台筛选缺读音、跨度越界和低质量 gloss。

无障碍：不让每个 token 默认进入 Tab 序列；使用句级导航或 roving tabindex。点词用非模态 popover/disclosure，支持 aria-expanded、Esc、轻点外部关闭和焦点恢复；只有真正模态 dialog 才锁焦点。ruby 在 NVDA/VoiceOver 中避免重复朗读。

验收：冻结样本 span 全部对应 surface；Quick Add 自动填 reading/meaning/source；无 annotation 课程仍可选字；关闭读音不留空位，400% 缩放不溢出。

### 8.4 AIX-001 构建期结构化解释与质量边界

来源：Miraa §3.7 与 §3.4，源文档 p7–p8；AI 解释=A/B，五区块结构与失效策略=本项目 I。

第一版仍在构建期生成，不增加运行时依赖。结构为 summary、vocabulary、grammar、listening、caveats；区块可缺省。输入课程文本一律视为不可信数据，不得成为系统指令；输出经 JSON schema、长度、枚举和 source digest 校验，绑定 sourceRevision/generatorVersion。UI 标注“AI 生成，可能有误”，问题报告生成 source-bound review item，不直接覆盖原文。翻译或解释失败只降级该层，原文播放/听写继续；legacy explanationText 保留回退。

验收：可选区块缺失不使整页失败；源句修改后旧解释显示 STALE；越界字段、旧 digest、超长或不合法输出被质量门拒绝；质量抽检按语言、材料类型和问题类别分层，不用单一总分掩盖弱项。

### 8.5 ERR-001B 全量错误码与分层降级

在 ERR-001A 基础上增加 E-ING、E-NET、E-ASR、E-SUB、E-TRN、E-AI、E-MIC、E-EXP、E-DB、E-SEC。每个 code 有稳定含义、retryable、用户动作、日志脱敏和测试 fixture。翻译/读音/解释失败仅隐藏对应层；编辑/导出失败保留草稿；任何提示不暴露堆栈、用户名、绝对路径、Host、token、完整正文或录音。

## 9. Phase 3：材料库与 Echo

### 9.1 LIB-001 多课程材料库

来源：Miraa §3.2、§3.9，源文档 p6、p8；材料入口=A/B，分类=C，Collection 模型=I。

目标：用户不再通过命令行参数才能换课。

依赖：DAT-002、PWA-001、SCH-001、SEC-001。当前课程量较少时，Echo 可与材料库并行；当可用课程超过约 10 门或用户确有频繁切课需求时，材料库优先级高于 Echo。该阈值是本项目排期触发器，不是 Miraa 指标。

执行步骤：

1. companion 可用时使用受 SEC-001 保护的 `/api/courses`；静态 ZIP/PWA 回退到构建时 `course-catalog.json`。两者使用同一 catalog schema，动态目录优先但不得把未验证临时目录覆盖已签名/带 hash 的静态目录。
2. 卡片展示标题、语言、时长、学习进度、缓存状态、质量状态和最近打开时间。
3. 支持搜索和用户自定义集合；JLPT 等级只作为元数据，不硬编码产品结构。
4. 只向普通学习页展示 READY 且质量门通过的课程。
5. 切课时释放旧 audio、取消 reveal/recording、刷新 track 和 progress。
6. Service Worker 以 courseId + courseContentRevision 管理文本包、以 audioHash 复用媒体，并提供按课程删除与共享媒体引用计数。

验收：

- 内部验收样本至少 20 门 fixture（含失败、缺层、多语言与重复 audioHash）可搜索、打开、返回和恢复各自位置；20 是本项目测试规模，不是 Miraa 事实。
- 切课后无旧字幕、旧音频、旧录音或旧 progress 泄漏。
- failed/pending 课程只在管理页可见。
- 离线时仅可打开 READY 缓存课程，状态说明准确。

### 9.2 ADR-ECHO-001 锁定录音保留与兼容边界

在请求麦克风前决定：支持 codec/浏览器矩阵、默认临时或保存时长、单句/总配额、达到配额后的降级、页面隐藏/设备拔出处理、是否纳入备份和跨 profile 导出格式。默认本地保留是本项目决策；任何变化都先更新 PRV-001 提示和删除验证。

### 9.3 ECH-001 Echo 四步本地跟读

来源：Miraa §3.6、§4.3、Echo 状态机、隐私权限和 AC11/12，源文档 p7、p10、p11、p14、p16；四步法/录音=A，状态机与默认本地保留=本项目 I。源公开资料未确认录音是否上传或保留，不能复用其隐私承诺。

第一版边界：

- 仅当前句段。
- 录音默认仅保存在当前浏览器 profile；这是本项目第一版决策，不是 Miraa 已确认行为。
- 原音与录音交替试听。
- 不做自动发音评分，不暗示评分。

流程：

1. Listen：播放当前句原音，可用速度和重复。
2. Understand：显示用户允许的原文、译文、读音和解释。
3. Imitate：请求麦克风权限，显示录音状态、时长和最小电平反馈。
4. Compare：明确标识“原音”和“我的录音”，允许交替播放、重录、删除和下一句。

实现：

- recording-engine 使用严格状态机。
- 检测 MediaRecorder codec，按浏览器选择 webm/ogg/mp4 等可用格式。
- EchoAttempt 的 blob 与元数据在同一个 IndexedDB 数据库事务内创建/删除，避免 SQLite 指向浏览器私有 blob。SQLite 只可备份不含 blob 的聚合学习统计；录音跨 profile 迁移必须由用户显式导出/导入。OPFS 仅在实测证明 IndexedDB 不足并完成新 ADR 后启用。
- Permissions-Policy 从 microphone=() 改为仅 self，但必须在 Phase 0 安全修复后启用。
- 权限拒绝时保留 Listen/Understand。
- UI 明确临时录音、已保存录音、保留期限和删除后的状态；默认保留时长由 ADR-ECHO-001 锁定并同步到 PRV-001B。

验收：

- 授权、拒绝、设备拔出、录音中断、页面隐藏、编码不支持均有可操作反馈。
- 录制、停止、试听、重录、删除连续循环 20 次无孤儿 blob；20 是内部验收样本。
- 删除后应用可控制的 IndexedDB 记录和临时 URL 均不存在；不承诺清除用户已导出的文件、系统备份或存储介质残留。
- iOS Safari、Chrome/Edge 桌面与至少一个 Android 浏览器通过真机检查。
- Compare 页面没有分数、星级或“AI 评测”措辞。

## 10. Phase 4：后置作者能力与可选实验

### 10.1 ADR-AI-001 锁定外部模型数据边界

在作者面板或追问立项前决定供应商、处理地区、发送字段、供应商保留/删除说明、API key 存储、请求日志、用户自带 API/本地模型回退和断网行为。未知项必须显示 unknown，不能复用 Miraa 的承诺；最小数据分类与 PRV-001B/SEC-002C 同步。

### 10.2 JOB-001 先把同步构建脚本变成可管理作业

来源：当前项目审计；源文档可见任务状态/通知为 A/I，具体 status/stage 状态机为本项目 I 级设计。

当前 builder 是面向命令行的同步长任务，默认 CUDA，可能下载大模型并通过 stdout 传递进度；不能直接套一层网页就称为可靠作业。先完成：能力探测与 CPU/无 GPU 明确提示；固定工具/模型版本；结构化事件流；作业持久化；受限 staging；子进程取消与重启恢复；同输入指纹幂等；磁盘/模型空间预检；单作业资源上限；每阶段产物 hash；失败不破坏已验证产物。首期明确只支持一条混合音轨、无说话人归属；多音轨、强背景音乐或疑似多人场景标记 NEEDS_REVIEW。

验收：命令行与作业运行器对同 fixture 生成等价 package；浏览器/父进程关闭后状态可恢复；取消后子进程与临时文件按保留策略收敛；无 CUDA 时不会无限等待或显示假进度。

### 10.3 AUT-001A/B 本地“创建课程”任务面板

来源：Miraa 素材导入=A/B、任务编排/状态机=I，源文档 p6、p10–p12；localhost 作者面板为本项目设计。

复用：build_deepseek_offline_bundle.py、resume、音频 hash、批次结果校验、质量门。

先完成 AUT-001A 的数据流、路径/子进程、权限和任务 UI 设计，经 SEC-002C 威胁复核后才进入 AUT-001B 实现。功能：

- 仅 localhost 管理页选择本地音频。
- 选择源语言、是否生成翻译/解释、模型配置。
- 创建 job，先显示 QUEUED；运行时显示 PREPARING、ASR、ENRICHING、VALIDATING、PACKAGING、CLEANING，终态为 COMPLETED/FAILED/CANCELED。
- 可取消、恢复、按层重跑；完成后进入 NEEDS_REVIEW，不直接发布。
- source SHA-256 + config digest 作为幂等键。
- 应用内任务中心显示排队、阶段、耗时、失败动作和完成状态；系统通知仅在用户主动授权后启用，拒绝通知不影响任务。

安全：

- 不允许浏览器提交任意服务器路径；使用受限文件选择和 staging 目录。
- 子进程参数使用数组，不拼接 shell。
- API key 只从环境或安全凭据读取，不鼓励 --api-key 出现在历史或进程列表。
- 明确告知哪些文本会发送给外部模型；支持关闭外部增强。

中间数据生命周期：

- 最终课程音频、manifest 与审核证据是离线学习资产，默认保留到用户从材料库/隐私中心删除；不能套用源文档“识别后删除”的云端说法。
- staging 输入副本、临时转码、raw ASR、DeepSeek batch/request/result 都登记 dataClass、retentionState、cleanupAt。建议成功并验证后 24 小时内清理；失败/取消默认最多保留 7 天供诊断，用户可立即清理或显式延长。期限须在 ADR-AI-001 与 PRV-001B 中最终确认。
- 清理失败产生 E-CLEANUP、可重试并进入隐私中心；孤儿扫描按 jobId/source hash 查找，不静默遗留。
- 外部 AI 可能收到完整句段/翻译请求；发送字段、供应商、地区、供应商保留/删除承诺必须按实际配置披露。无法确认时明确写“未知”，不借用 Miraa 的隐私承诺。

验收：

- 浏览器关闭、服务重启后任务可恢复。
- 同一音频+配置重复提交返回同一任务或明确复用。
- 失败阶段可单独重试，不重跑已验证层。
- 任何未通过质量/人工审核的课程不会进入普通材料库。
- 成功、失败、取消和重试后的 staging/批次/结果均符合 retentionState，清理审计不存在未解释孤儿。

### 10.4 AIX-002 可选的标记文本追问

来源：Miraa 标记提问/追问=B；最小上下文、发送预览和本地会话删除=本项目 I。

只有满足以下条件才进入实验：

- Phase 0 数据/安全基础完成，PRV-001B 与 SEC-002C 通过。
- 结构化解释和 source revision 已稳定。
- 用户主动触发，并看到即将发送的内容。
- 默认只发送选中文字、当前句和至多相邻句。
- 会话可删除；失败不丢问题；原文学习不依赖网络。

可先支持用户自带 API 或本地模型实验，不设计订阅、额度或云账号。

## 11. 横切质量任务

以下不是“顺手做”的检查项，均进入 Backlog、分配主责并作为相关阶段发布门。

### 11.1 PRV-001 隐私中心与数据生命周期

来源：Miraa 隐私/权限公开说明=A；本地存储、保留和删除实现=本项目 I。

建立数据清单：IndexedDB、Cache Storage、localStorage 兼容数据、SQLite、WAL/SHM、轮换备份、outbox/tombstone、Echo blob、课程媒体、任务 staging/raw/batch/result、诊断包和外部 AI。对每类标明用途、位置、是否含正文/录音、创建条件、默认保留、删除动作、备份覆盖和无法控制的副本。

功能包括分项导出、带 schema/checksum 的全量备份/恢复、分项清理和全部清理；操作前显示影响与可选先导出。导入实施大小/记录上限、schema、hash、路径穿越、ZIP bomb、重复 ID 和降级攻击检查。未加密备份明确警告敏感性，不把 API key 写入备份。删除只验证应用可观察、可控制的 IndexedDB 记录、Cache、SQLite/WAL、托管备份和任务临时物；浏览器内部逐出/存储残留没有通用验证 API，连同用户自建副本、系统备份、SSD 残留与外部供应商数据披露为不可控边界。

诊断导出默认脱敏：完整字幕/答案/笔记/录音、API key/token、用户名、绝对路径、Host、查询参数和外部请求原文均不得出现。首次录音或外部发送前说明用途；拒绝麦克风时 Listen/Understand 继续可用。

### 11.2 A11Y-001 无障碍

来源：源文档 NFR-A11Y 为 I 级建议；以下按本项目 Web 交互验收。

- 抽离语义与视觉状态；键盘顺序、跳转链接、错误关联、`lang`、名称/角色/值和可见焦点完整。
- 可见焦点对比度至少 3:1；触控目标以 24×24 CSS px 为最低、44×44 为推荐，达不到时记录豁免与邻距。
- 时间滑杆提供 aria-valuetext；字符差异有“缺少/多余/匹配”文字，不只依赖颜色/线条。
- 非模态 popover/disclosure 使用 aria-expanded、Esc、light dismiss 和焦点恢复，不锁焦点；只有 modal dialog 才使用焦点陷阱。
- 动态字幕最多每句段播报一次；缓冲、错误、录音状态用克制 live region，不能随 timeupdate 刷屏。
- Delayed Reveal 隐藏内容不在可访问树；ruby 避免重复读；Echo 录制/停止/试听状态有文本。
- 以选定的 WCAG 2.2 A/AA 为门：自动工具能检测的适用违规为 0，不按 serious/critical 严重度裁剪；其余适用成功标准用人工清单覆盖 200%/400% 缩放、高对比、reduced motion、IME、仅键盘、NVDA 与 VoiceOver。N/A 只用于成功标准确实不适用且有理由，已知适用失败不能以“后续延期”通过发布。

### 11.3 LOC-001 本地化与多端布局

把界面字符串、日期/数字和错误消息从 JavaScript/HTML 抽离；interfaceLocale、sourceLanguage 和翻译轨 language 不复用一个设置。测试中文/日文/英文长文本、注音、缺字字体、窄手机、平板、横屏和桌面；字幕字号/位置、层开关在 400% 缩放下不能遮住核心控件。RTL 首期只做镜像/方向 smoke test并声明非完整支持。英语 IPA、韩语注音和中文简繁只有能力矩阵为 supported 时才显示。

### 11.4 PERF-001 性能与可靠性指标

源文档阈值均属 I 级建议。以下也是本项目初始目标，必须先记录测试环境：浏览器/版本、OS、CPU/内存、音频输出（扬声器/蓝牙）、课程段数/时长、冷/热缓存、样本次数与统计方法；完成基准后由 ADR 调整。

| 指标 | 初始目标 | 测量方式 |
| --- | ---: | --- |
| 播放/暂停/切层/点词 P95 | ≤250ms | Performance marks；至少 100 次热路径，权限弹窗另列 |
| 字幕边界漂移 P95 | ≤250ms | audio.currentTime 对 segment 边界 + 有线输出人工样本；蓝牙另列 |
| 任务提交到可见任务卡 | ≤2s | 从用户确认到本地 JobStore 提交，不含模型排队 |
| 同 audioHash 刷新 20 次 | 音频传输 0 | 固定浏览器网络日志；20 为内部样本 |
| 断网 50 次 mutation 恢复 | 0 丢失/重复/复活 | 固定随机种子的 fault-injection E2E；50 为内部样本 |
| 默认技术候选质量 | 0 errors | 当前 audit + waiver policy；不代表人工听审通过 |
| READY 课程必需层 | stale/failed 为 0 | requiredLayers 发布门 |

字幕查找使用二分索引；长文本编辑距离使用长度上限或带阈值算法；列表达到基准规模后分页/虚拟化。Range 音频方案必须用峰值内存、首次播放、随机 seek 与离线空间共同评估。

### 11.5 OBS-001 隐私安全的可观测性

只在本地记录最小摘要：app/version、courseId、各 revision、schemaVersion、audioHash 前缀、数据库健康、迁移结果、outbox 数、缓存状态、错误 code/stage/耗时/retryable/diagnosticId 和性能 P50/P95/P99。日志保留期限和“清除诊断”进入 PRV-001。导出前再次扫描并移除正文、答案、笔记、录音、API key/token、用户名、绝对路径、Host 与外部请求原文。

### 11.6 SEC-002 分阶段覆盖导入与外部 AI

安全复核不能等到 Phase 4：

- SEC-002A-D（Phase 0 设计）先为当前备份 JSON/ZIP、课程包和 DeepSeek CLI 建立威胁模型与失败用例：大小/记录上限、路径穿越、ZIP bomb、未知 schema、课程字段 HTML/script/CSV 公式注入、API key/日志、发送字段与供应商保留披露。同源 XSS 可以读取 bootstrap token，因此所有导入文本必须以 textContent/安全组件渲染，CSP 不能替代输出编码。
- SEC-002A-V（Phase 0 验证）在 DAT-003B/FND-001 相应实现后关闭上述用例；设计评审通过不等于安全门完成。
- SEC-002B（Phase 2）覆盖 SRT、patch v2、token/解释生成输出：畸形时间块、Unicode 边界、超大文本、公式/HTML/脚本注入和 source revision 绕过。
- SEC-002C（Phase 4）覆盖作者面板与可选追问：课程文本 prompt injection、SSRF/任意路径、子进程参数、模型输出脚本、会话删除和最小上下文。

所有富文本按纯文本渲染或严格白名单；本地模型/自带 API 与外部供应商分别披露；任何安全或网络失败不降低原文学习能力。

## 12. 可执行 Backlog

| Phase | ID | 交付物 | 主责 | 估算 | 前置依赖 |
| --- | --- | --- | --- | ---: | --- |
| 0 | BKP-001 | 一致快照、hash 清单、恢复演练、origin 缺失报告 | Python + QA | 2–3d | 无 |
| 0 | ADR-BUILD-001 | Node/Python 版本、锁文件、浏览器与 artifact 策略 | 技术负责人 | 1–2d | BKP-001 |
| 0 | FND-002A | Git/依赖/pytest/node:test/Playwright/事实文件 | 工程负责人 + QA | 5–8d | BKP-001、ADR-BUILD-001 |
| 0 | ADR-CONTENT-001 | v1 id、courseAliases/segmentAliases 与听审/权利状态 | 技术负责人 + 内容审核 | 2–3d | BKP-001 |
| 0 | FND-001 | 技术候选 diff、双 alias、fail-closed、听审队列 | Python + 内容审核 | 5–8d | ADR-CONTENT-001、FND-002A |
| 0 | ADR-STORE-001 | 浏览器权威、companion 副本、离线期和冲突决策 | 技术负责人 | 1–2d | BKP-001 |
| 0 | DAT-003A | SQLite user_version、Backup API、故障迁移基线 | Python | 2–4d | ADR-STORE-001、FND-002A |
| 0 | SEC-001 | Host/token/bootstrap/Origin/review_server 安全 | Python + QA | 4–6d | FND-002A |
| 0 | DAT-001 | 稳定 origin、IndexedDB 权威学习库、同源迁移 | 前端 + Python | 4–6d | FND-001、ADR-STORE-001、DAT-003A；与 SEC-001 同版 |
| 0 | DAT-002 | processed_mutations、outbox、tombstone、对账 | 前端 + Python | 8–12d | DAT-001、SEC-001 |
| 0 | ADR-PWA-001 | manifest 分类、audioHash、Range 与更新协议 | 前端负责人 | 2–3d | FND-002A |
| 0 | PWA-001 | 两阶段 READY 指针、配额/逐出、Range 方案实现 | 前端 + QA | 8–12d | ADR-PWA-001、DAT-001 |
| 0 | ERR-001A | P0 错误合同和恢复 UI | 全栈 | 2–3d | FND-002A |
| 0 | PRV-001A | 数据清单、导出/删除合同、诊断脱敏基线 | 隐私 + 全栈 | 3–5d | BKP-001、ADR-STORE-001 |
| 0 | SEC-002A-D | 备份/课程包/当前 DeepSeek CLI 威胁设计与失败用例 | 安全 + QA | 1–2d | FND-002A、PRV-001A |
| 0 | DAT-003B | IDB 权威快照、事务恢复、SQLite 重建、删除验证 | Python + 前端 | 8–12d | DAT-003A、DAT-002、PRV-001A、SEC-002A-D |
| 0 | SEC-002A-V | 导入/XSS/CSV/密钥/外发安全门关闭 | 安全 + QA | 2–3d | DAT-003B、FND-001、SEC-002A-D |
| 1 | MOD-001 | 纯函数、player 与既有 repository 模块化 | 前端 | 5–8d | P0 E2E 基线 |
| 1 | ADR-SPAN-001 | TokenAnnotation 索引单位与 Unicode 样本 | 技术负责人 | 1–2d | FND-002A |
| 1 | LIN-001 | ASR rawSegmentIds 聚合、拆分/合并与重基 | Python + 内容工具 | 4–7d | FND-001、FND-002A |
| 1 | SCH-001 | 四类 schema、v1 adapter、revision/lineage | Python + 前端 | 15–22d | FND-001、MOD-001、ADR-SPAN-001、LIN-001；设计可并行 |
| 1 | PLY-001a | v1 原文/译文层与基础 Delayed Reveal | 前端 | 3–4d | P0 播放器 E2E；可隔离原型 |
| 1 | PLY-001b | 读音/多轨/after_ms 媒体时钟 | 前端 | 3–5d | SCH-001、PLY-001a |
| 1 | PLY-002 | N 次重复、跳转、状态、二分时间索引 | 前端 | 3–5d | MOD-001 |
| 1 | A11Y-001 | 语义、键盘、读屏、缩放与真机矩阵 | 前端 + QA | 4–6d | PLY-001a 起贯穿 |
| 1 | LOC-001 | 三语言设置、字符串抽离、多端/RTL smoke | 前端 + 产品 | 4–6d | SCH-001 设计 |
| 1 | PERF-001 | 基准环境、性能/漂移/Range 指标 | QA + 前端 | 4–6d | PLY-002、PWA-001 |
| 1 | OBS-001 | 本地最小诊断、保留与脱敏 | 全栈 | 3–5d | ERR-001A、PRV-001A |
| 2 | EDT-001A | 最小源文/时间编辑、草稿、patch v2 设计 | Python + 前端 | 7–10d | SCH-001、ERR-001A |
| 2 | ADR-LNG-001 | tokenizer/词典质量、许可、体积与回退 spike | 内容管线 + 法务/产品 | 2–4d | SCH-001 设计 |
| 2 | LNG-001 | TokenAnnotation、日语 ruby、点词 | 内容管线 + 前端 | 8–12d（暂定） | ADR-LNG-001、SCH-001、EDT-001A |
| 2 | AIX-001 | 构建期结构化解释、stale、反馈 | 内容管线 + 前端 | 6–9d | SCH-001、EDT-001A |
| 2 | ERR-001B | 全量错误码和分层降级 | 全栈 | 2–4d | ERR-001A、模块边界 |
| 2 | SEC-002B | SRT/patch/token/解释输出安全复核 | 安全 + QA | 2–4d | EDT-001A、AIX-001 设计 |
| 2 | EDT-001B | 结构编辑、SRT 导入/导出与重基实现 | Python + 前端 | 8–15d | SEC-002B、EDT-001A |
| 3 | LIB-001 | 动态/静态目录、集合、切课与共享媒体 | 全栈 | 8–12d | DAT-002、PWA-001、SCH-001、SEC-001 |
| 3 | ADR-ECHO-001 | codec、默认保留、配额与跨 profile 导出 | 产品 + 前端 + 隐私 | 1–2d | PRV-001A |
| 3 | ECH-001 | 同库录音、试听、删除、真机兼容 | 前端 + QA | 15–25d | ADR-ECHO-001、PRV-001A、SEC-001、A11Y-001 |
| 3 | PRV-001B | Echo/多课程保留、全量导入导出和删除验证 | 隐私 + 全栈 | 3–5d | LIB-001、ECH-001 |
| 4 | ADR-AI-001 | 供应商/地区/保留、最小数据与本地回退 | 产品 + 安全 + 隐私 | 1–2d | PRV-001B |
| 4 | JOB-001 | builder 作业化、资源/进程树取消/恢复/清理地基 | Python | 12–20d | SCH-001、SEC-001 |
| 4 | AUT-001A | 作者面板数据流、路径/子进程与任务 UI 设计 | Python + 前端 | 5–8d | JOB-001、LIB-001、PRV-001B |
| 4 | SEC-002C | 作者面板/追问/子进程/SSRF 安全复核 | 安全 + QA | 3–5d | ADR-AI-001、AUT-001A |
| 4 | AUT-001B | 本地作者任务中心、阶段、通知与审核入口实现 | Python + 前端 | 20–32d | AUT-001A、SEC-002C |
| 4 | AIX-002 | 最小上下文追问实验 | 全栈 + 隐私 | 8–12d | ADR-AI-001、AIX-001、SEC-002C、PRV-001B |

分阶段小计与第 1.3 节一致：Phase 0 为 60–94d，Phase 1 为 49–76d，Phase 2 为 35–58d，Phase 3 为 27–44d，Phase 4 为 49–79d。大规模人工逐句听审另行按实际音频时长、抽检率和复审轮次估算。

关键路径：`BKP-001 → ADR-BUILD-001 → FND-002A`；`ADR-CONTENT-001 + FND-002A → FND-001`；`ADR-STORE-001 → DAT-003A`，同时 `FND-001 + DAT-003A + SEC-001（与稳定 origin 同版）→ DAT-001`，再由 `DAT-001 + SEC-001 → DAT-002`；`ADR-PWA-001 + DAT-001 → PWA-001`；`PRV-001A → SEC-002A-D`，随后 `DAT-003A + DAT-002 + SEC-002A-D → DAT-003B → SEC-002A-V`；`MOD-001 ∥ LIN-001 ∥ SCH-001 设计，ADR-SPAN-001 → SCH-001 实现 → EDT-001A/AIX/LNG → SEC-002B → EDT-001B`；`DAT-002 + PWA-001 + SCH-001 → LIB-001`；`ADR-ECHO-001 + PRV-001A + SEC-001 + A11Y-001 → ECH-001`；`JOB-001 + LIB-001 + PRV-001B → AUT-001A → SEC-002C → AUT-001B/AIX-002`。

## 13. 里程碑与发布门

### 13.1 Phase 0 发布门

- [ ] 默认技术候选 errors=0；warnings 均有有效 waiver；独立听审状态单独可见，未完成时不称 canonical/可发布。
- [ ] listeningQuality 与 distributionRights/商业推荐为独立字段；finalize 不再自动把后者写为 true。
- [ ] courseAliases 与 segmentAliases 均绑定源/目标 revision；歧义项不自动迁移。
- [ ] failed 课程普通启动被阻断。
- [ ] 同一 profile 10 次重启进度一致；旧随机 origin 的可恢复/不可恢复清单已给用户。
- [ ] 两个 profile 的同名实体在 SQLite 中隔离；恢复/跨 profile 导入必须先预览并由用户确认。
- [ ] SQLite 新于当前二进制时只读 fail-closed；迁移失败可用已验证前置备份 + 旧二进制恢复，不做原地逆迁移。
- [ ] 稳定 origin 与 SEC-001 同版；端口占用不连接未知进程。
- [ ] 离线增删改 fault-injection 无丢失/重复/复活，A→B→重放 A 保持 B。
- [ ] IndexedDB 配额拒绝、事务失败、私密模式和学习存储被清理时不显示假成功，并可导出/恢复。
- [ ] 伪造 Host/Origin、缺 token 的 GET/写请求被拒绝。
- [ ] bootstrap/health/review_server 不泄露或缓存 token。
- [ ] 同 audioHash 20 次刷新不重新下载音频。
- [ ] 新缓存失败仍可使用旧离线版本。
- [ ] 缓存被逐出、配额不足和崩溃恢复状态准确。
- [ ] 1MiB 离线 Range 不再读取完整 21.5MB 响应，达到 ADR 锁定的内存/字节门。
- [ ] IDB 权威备份包含未确认 outbox/tombstone/watermark；staging 验证或恢复事务中断时旧数据不变；SQLite 由确认后的权威数据重建。
- [ ] 恶意/超大/路径穿越 ZIP 被拒；删除正文不残留在幂等结果表。
- [ ] SEC-002A-V 关闭备份/课程导入、课程字段 XSS/CSV 公式以及当前 DeepSeek CLI 的发送、日志、密钥和供应商保留用例。
- [ ] 全部 P0 自动测试在主分支无 skip 执行；构建证据可追溯。

### 13.2 Phase 1 发布门

- [ ] 四类 schema 有独立版本；v1 course package 兼容。
- [ ] v1 `sentences[].id`/review sentenceId 到 legacySentenceId 的桥接及第二阶段 segmentId 迁移可回滚。
- [ ] 1→1、N→1、1→N 的 rawSegmentIds 血缘不再触发一一对应错误，unknown 不当作 pass。
- [ ] 原文修改会使相关派生层 stale。
- [ ] PLY-001a/1b 在 seek/调速/切轨/换句下无 reveal 泄漏。
- [ ] repeat=N 精确。
- [ ] 冻结的 629-segment legacy/dev fixture 与最终技术候选均持续播放无错高亮；前者不作为普通课程入口。
- [ ] 性能达到经实测锁定的 P95。
- [ ] A11Y/LOC 的适用发布项通过；N/A 仅用于确实不适用且有理由，已知适用失败不得以延期放行。

### 13.3 Phase 2 发布门

- [ ] 日语 token span 不越界，ruby 与 Quick Add 正确。
- [ ] 结构化解释与 source revision 绑定。
- [ ] 同轨、未编辑、立即往返的内部 SRT fixture 时间差 ≤1ms；外部 SRT 有损项有报告。
- [ ] 编辑失败不丢草稿，patch digest 不匹配被拒绝。
- [ ] insert/delete/split/merge 的父子 lineage、进度重基和派生失效正确。
- [ ] SEC-002B 的恶意/超大 SRT、patch 和生成输出用例均被安全拒绝或转义。
- [ ] 翻译/读音/解释失败不阻断原文。

### 13.4 Phase 3 发布门

- [ ] 多课程切换无状态泄漏。
- [ ] 缓存可按课程管理。
- [ ] Echo 权限拒绝不阻断 Listen/Understand。
- [ ] 内部样本 20 次录制/删除无应用可控孤儿 blob。
- [ ] 真机、键盘、屏幕阅读器和 400% 缩放通过。
- [ ] Compare 不出现自动评分承诺。
- [ ] 数据导出、保留、删除和跨 profile 边界在隐私中心准确披露。

### 13.5 Phase 4 发布门

- [ ] 一条混合音轨范围、模型/硬件要求和 NEEDS_REVIEW 场景明确。
- [ ] 成功/失败/取消/重试后中间物符合 cleanupAt，清理失败可见。
- [ ] 未经质量与人工审核的课程不进入普通材料库。
- [ ] 外部发送预览、供应商/保留披露和 SEC-002C 通过。
- [ ] 拒绝系统通知不影响任务；追问失败不丢问题且不阻断原文学习。

## 14. 风险、决策与回滚

| 风险 | 预防 | 触发条件 | 回滚 |
| --- | --- | --- | --- |
| 切换技术候选导致 course/segment ID 变化 | alias + 先导出 + 时间/文本映射 + 人工歧义队列 | 无法映射或缺失音频覆盖超出批准阈值 | 保留旧课程只读入口，不迁移歧义项 |
| 模型 v2 迁移破坏旧包 | v1 adapter + 双写一个版本周期 | v1 E2E 回归 | 默认继续读取 v1 |
| outbox 对账产生冲突 | processed_mutations、单调 entityVersion、tombstone、冲突副本 | 冲突率异常或客户端 epoch 过期 | 暂停回放，强制全量对账并允许导出 |
| SW 新策略导致离线不可用 | 临时缓存 + READY registry + 可恢复两阶段指针 | 新缓存校验/提交失败 | 保留旧 READY；清理临时缓存 |
| token/Host 修复阻断正常客户端 | localhost/127 矩阵测试 | 正常启动 403 | 回滚到上个安全配置，不放开非 loopback |
| token/ruby 可访问性倒退 | roving tabindex + 真机读屏 | Tab 数量爆炸或重复朗读 | 回退句级文本渲染 |
| Echo 存储膨胀 | 默认临时、空间配额、分项删除 | 达到配额 80% | 禁止新保存但保留删除/导出 |
| AI 解释幻觉或 prompt injection | 结构 schema、digest、人工反馈、最小上下文 | 质量抽检未达标 | 回退 legacy 人工解释 |
| patch v2 结构编辑误伤内容/进度 | base revision、父子 lineage、预览和迁移报告 | diff 超阈值或歧义未清 | 放弃 patch、保留草稿并回到旧 revision |

必须建立 ADR 的决策：

1. ADR-CONTENT-001：技术候选成为 canonical 的听审阈值、v1 id/course alias/segment alias；FND-001 与 DAT-001 前签署。
2. ADR-STORE-001：确认或否决“IndexedDB 权威、SQLite 副本”、90 天离线期与冲突策略；DAT-001/outbox 前签署。
3. ADR-PWA-001：音频整文件/分块/句级媒体、shell 更新协议和配额策略；PWA-001 实现前签署。
4. ADR-SPAN-001：TokenAnnotation 使用 UTF-16 还是 Unicode code point；course-package schema freeze 前签署。
5. ADR-BUILD-001：前端构建器、Node/Python/浏览器版本与依赖更新；FND-002A 前签署。
6. ADR-ECHO-001：默认保留时长、支持 codec、配额和跨 profile 导出；ECH-001 请求权限前签署。
7. ADR-AI-001：外部 AI 数据分类、供应商、地区、保留/删除说明与本地模型回退；AUT-001A/AIX-002 前签署。

## 15. 前 10 个工作日：启动冲刺与垂直风险原型

这 10 天的目标是冻结证据、做出架构决策并把最大风险变成可重复测试，不承诺完成 60–94 人日的 Phase 0。

### Day 1–2：可恢复快照、历史搜索与决策输入

- [ ] 完成 BKP-001：SQLite 一致快照、可访问 origin 导出、hash 清单和恢复演练。
- [ ] 搜索 OneDrive/旧目录/归档中的 Git、tests、E2E 和构建证据；记录找到与缺失项。
- [ ] 建立 Git 基线、issue/ADR 编号和 implementation-facts.json 骨架。
- [ ] 签署 ADR-BUILD-001；起草 ADR-CONTENT-001、ADR-STORE-001 与 ADR-PWA-001，明确待实测问题。

### Day 3–4：内容候选审计与质量阻断垂直切片

- [ ] 只把旧 ZIP manifest 提取到 staging，核对音频 hash、当前审计和字段覆盖。
- [ ] 签署 ADR-CONTENT-001；生成 courseAliases、629↔517 段级 diff、314 个 exact match 基线和 segmentAliases 候选队列。
- [ ] 把听审质量与分发/权利推荐拆成独立状态，再启动听审队列。
- [ ] 用一个 fixture 完成 fail-closed、显式开发绕过、阻断页和自动测试。
- [ ] 输出“技术候选/听审待办”，不切换默认课程。

### Day 5：可重复测试骨架

- [ ] 固定 Python 与 Node/Playwright 依赖、锁文件和浏览器安装说明。
- [ ] 建立短音频/假时钟 fixture，跑通质量门、Range、API 和浏览器 smoke。
- [ ] P0 测试禁止 skip，失败证据进入 CI/本地统一入口。

### Day 6：安全复现与修复原型

- [ ] 把伪造 Host/Origin 写入变成先失败的回归测试。
- [ ] 原型化 Host allowlist、内存 token、no-store bootstrap、authenticated readiness 与 SW bypass。
- [ ] 覆盖 GET/POST、health、review_server 和静态资源；记录本机恶意进程不在威胁边界。

### Day 7–8：存储决策与一个端到端 mutation

- [ ] 签署 ADR-STORE-001；搭建 SQLite user_version/Backup API 基线。
- [ ] 建立 IndexedDB PracticeProgress/CourseState 与同 origin localStorage 导入 fixture。
- [ ] 完成一个“离线新增生词→outbox→processed_mutations→SQLite 副本”的垂直路径，再做删除墓碑路径。
- [ ] 验证 A→B→重放 A 仍为 B；稳定 4173 与 SEC-001 必须同版，尚未齐全时不切生产入口。

### Day 9：PWA 决策与崩溃恢复原型

- [ ] 用 21.5MB 课程和短 fixture 基准整文件/分块/句级候选，签署 ADR-PWA-001 或列出阻塞实验。
- [ ] 原型临时缓存→hash→READY registry→active pointer；在每一步强制中断并证明旧 READY 可用。
- [ ] 分开 catalog/course/webmanifest/shell asset 策略，音频 URL 使用 audioHash。

### Day 10：证据评审和 Phase 0 余量确认

- [ ] 演示质量阻断、安全利用被拒、一个离线 mutation 幂等回放和一次缓存崩溃恢复。
- [ ] 复核旧 origin 不可自动枚举、候选未听审、Range 方案和跨浏览器一致性等边界是否写清。
- [ ] 根据 spike 更新 Phase 0 剩余 4–7 周任务、主责、风险和验收，不把原型当完成项。

## 16. Definition of Done

每个任务先标风险等级：P0/数据迁移/安全/录音/导入必须满足全部适用门；纯文案或内部工具可把不适用项标 N/A，但必须写理由、批准人和日期。不能为“打满勾”制造无价值测试。

- [ ] 需求 ID、设计决策、数据迁移和回滚方案已记录。
- [ ] 单元、集成、浏览器 E2E 和必要真机测试已通过，或不适用项有可审计 N/A。
- [ ] 失败、离线、权限拒绝、刷新、重启和迁移路径已覆盖。
- [ ] 无障碍：键盘、焦点、读屏、缩放、对比度和 IME 已检查。
- [ ] 隐私：采集目的、存储位置、保留、导出和删除应用可控副本已实现；不可控边界已披露。
- [ ] 性能：测量口径和 P50/P95/P99 有记录。
- [ ] 日志和诊断不含完整学习内容、录音和密钥。
- [ ] 课程 revision、派生层状态、质量报告和构建证据一致。
- [ ] 文档反映当前事实，不引用已删除测试或过期统计。
- [ ] 发布门通过，且存在可执行回滚。

## 17. 证据索引

### 17.1 Miraa 源文档

- p3：产品原则与核心能力。
- p4：系统边界、参与者和边界假设。
- p6：素材导入与 ASR 任务。
- p7：翻译解析、播放器与 Echo。
- p8：AI 解释、字幕编辑、材料库。
- p9：设置、通知与本地化。
- p10：导入、解释、Echo、字幕导出流程。
- p11：概念模型与状态机。
- p12：逻辑组件与接口原则。
- p13：非功能指标与监控口径。
- p14：数据、隐私与权限。
- p15：异常场景。
- p16：验收后半与开放问题；源文档排版使 AC01–08 在渲染中不完整，但结构化内容存在。
- p17：证据矩阵与公开来源；用于核对 A/B/C/I 等级。

### 17.2 当前项目

- start_dictation.py：默认 manifest、随机端口、服务启动。
- src/serve_course.py：质量审计、临时复制、Range、安全头、microphone=()。
- src/local_backend.py：SQLite schema、学习 API、同源判断。
- src/web/app.js：播放器、听写、进度、学习数据镜像、离线注册。
- src/web/sw.js：应用壳、课程缓存、manifest 策略、Range。
- src/course_schema.py：稳定课程/句子 ID 与内容 revision。
- src/bundle_quality.py：自动内容质量审计。
- src/content_patch.py：source-bound 内容修订。
- src/human_review.py 与 src/review_web：逐句审核能力。
- src/build_deepseek_offline_bundle.py：ASR、翻译解释、resume、批次校验与打包。
- courses/2010-12-N2/manifest.json：当前 failed 课程。
- dist/2010-12-N2-commercial-candidate.zip：同音频的旧 0/0 质量候选 manifest 与已漂移前端。
- PROJECT_STRUCTURE.md：测试、E2E 和构建中间证据被删除的记录。
- docs/COMMERCIAL_ROADMAP.md：仍引用已不存在的测试与旧课程统计，说明文档事实已漂移。

## 18. 最终建议

首个改进版本只承诺两件事：

1. 把“本地、离线、进度可靠、内容可信”从宣传语变成可重复验证的事实。
2. 在稳定地基上交付字幕层控制、Delayed Reveal、N 次重复和日语读音点词。

字幕编辑、材料库和 Echo 随后进入第二个产品版本。本地课程创建面板与在线 AI 追问保持后置。这样既能充分吸收 Miraa 文档中最有价值的学习闭环和数据纪律，又不会把当前轻量、本地优先的项目拖入商业账号、云服务与版权风险。
