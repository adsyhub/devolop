# 听写练习软件

这是一个本地运行的多语言精听与听写网页。支持“逐句精听”与“全文精听”，可连续播放整段音频并按课程时间轴同步显示原文与已有翻译，并支持划词加入生词本或记笔记。项目已经整理为“启动入口、程序源码、课程内容、项目资料、文档、发布包”六个部分。

## 快速启动

电脑需要安装 Python 3.10 或更高版本。播放器本身只使用 Python 标准库，不需要额外安装依赖。

在项目目录运行：

```powershell
python .\start_dictation.py
```

启动器会执行以下操作：

1. 固定使用 `http://127.0.0.1:4173`。端口被占用时会报告占用情况并停止，**不会**
   自动换端口——学习进度按 origin（含端口）隔离，换端口等于打开一份空进度。
2. 生成本次会话的令牌并交给服务，然后验证令牌链路确实可用。
3. 对课程运行质量审计；**审计有错误的课程会被拒绝打开**（见下方）。
4. 检查课程清单和音频能否正常读取，再用默认浏览器打开网页。
5. 把生词、笔记和打卡记录保存在本机应用数据目录。

学习结束后，在启动窗口按 `Ctrl+C` 关闭服务。

### 内容质量门

课程只要自动审计有 **1 个以上错误**就不会打开，启动器会打印错误码
`E-COURSE-QUALITY`、问题分类统计和一个诊断 ID。这是有意为之：此前审计结果只是
附加在清单上的一个字段，损坏的课程照常打开，学习者会对着错误内容练习。

要在明知内容有问题的情况下检查课程，可以显式绕过：

```powershell
python .\start_dictation.py --allow-failed-course
```

绕过时页面会持续显示红色「内容未通过质量门：不可发布」提示，不会伪装成正常课程。

**当前状态**：两门课都能正常打开——`courses/2010-12-N2` 审计 0 错误 / 0 警告，
`courses/librivox-test` 0 错误 / 95 警告（缺翻译和讲解，不影响打开）。
这些数字由 `src/implementation_facts.py` 实测生成，以 `implementation-facts.json` 为准，
**不要手写**；决策背景见 [docs/ADR.md](docs/ADR.md)。

## 界面层次

打开 `http://127.0.0.1:4173` 是应用首页。精听、真题与词汇语法是三个独立学习工作区，
“我的”是跨模式资产中心，不把它们伪装成同一页里的模式 Tab：

```
学习模式选择
├── 🎧 精听工作区   ── 视频 / 音频课程 ──→ 逐句听写 / 全文精听
├── 📝 真题工作区   ── 等级 ──→ 按卷 / 专题 / 模考 ──→ 答题与报告
└── 📚 词汇语法工作区 ── 等级 ──→ 内容包 ──→ 教材单元 ──→ 条目

跨模式资产：🗂 我的 ── 错题集 / 生词本 / 收藏笔记 / 学习分析
```

**精听**分两类：视频课在原站播放（YouTube / 哔哩哔哩 / Vimeo，可盲听遮画面），
音频课完全离线。进板块先看到课程列表，点「开始学习」才进练习界面。

课程大厅支持按标题搜索、媒体类别、JLPT 等级、质量状态和学习状态筛选，也可按名称、
更新时间或掌握进度排序。课程卡会区分“已练习”和“已掌握”：只听过或看过答案只记作
曝光，不会误判为掌握；独立答对后才进入句子复习调度。质量检测、人工审听、版权核验和
浏览器验收未完成的课程会直接显示待处理状态。

**我的**现在是独立页面（`me.html` + `personal.js`），不再借用精听页的弹窗和课程初始化。
四个模块在同一界面切换。其中「错题集」同时收听写错句和 JLPT 真题错题——界面合并，
两边各取各的数据源；从精听错句可切换到对应课程和句子继续练习。

每一层都能用地址栏直达：

| 地址 | 落到哪 |
|---|---|
| `/` | 首页 |
| `/listening#/listening` | 精听课程列表（全部） |
| `/listening#/listening/video` | 精听 · 只看视频课 |
| `/listening#/listening/audio` | 精听 · 只看音频课 |
| `/listening#/practice` | 当前精听课程的练习界面 |
| `/me#/mistakes/dictation` | 我的 · 精听错句 |
| `/me#/mistakes/exam` | 我的 · 真题错题 |
| `/me#/vocab` | 我的 · 生词本 |
| `/me#/notes` | 我的 · 收藏笔记 |
| `/me#/analytics` | 我的 · 学习分析 |
| `/exams#/exam/<名称>?mode=review&scope=wrong` | 某套真题的错题复习 |
| `/lexicon` | 词汇语法 · 内容包列表 |
| `/lexicon#/pack/<包名>` | 某个内容包，按教材单元浏览 |

旧的 `index.html` / `exam.html` / `lexicon.html` 地址仍可打开；新链接统一使用稳定产品路径。

存储位置与键盘快捷键收在顶栏右侧的「⋯」菜单里。

## JLPT 题库

启动后除了听写页面，同一个端口上还有一套 JLPT 真题解题系统：

```text
http://127.0.0.1:4173/exams
```

也可以从首页选择「JLPT 真题模式」进入。两个学习工作区只通过首页切换，避免离开时
误以为当前练习状态会带入另一模式。三种练习方式：

- **逐题练习**——完成所选范围并交卷后统一判题、看答案，可写笔记、加标记；
- **计时模考**——作答时不显示对错，有倒计时和答题卡，交卷后出报告；
- **错题复习**——只抽做错、蒙对、标记过或今天该复习的题，完成整组后统一反馈。

范围可以选全卷、某一部分或某一道大题，计分只按练习范围算。作答时可以标注「蒙的」，
蒙对的题不计入掌握、继续留在复习队列。

题库卡片会显示未开始、进行中、已完成等状态；未交卷练习可以从做题记录继续，也可以放弃。
专题训练可按整套真题为单位选择纳入几套卷，题型内不会把一套卷拆开，默认仍练全部来源卷。

已导入 `exams/2022-07-N1/`（2022 年 7 月 N1，105 题 176 分）。听力部分只有选项，
没有配套音频，页面会明确标注。

导入新真题、题目数据结构和接口说明见 [docs/JLPT_EXAM.md](docs/JLPT_EXAM.md)。

## 词汇与语法

第三个工作区，按 JLPT 级别组织词条与语法条目：

```text
http://127.0.0.1:4173/lexicon
```

词和语法是**同一种内容**，用 `kind` 区分而不是两个模块：一个词条是「見出し語＋読み＋
词性＋释义＋例句＋级别＋出处」，一个语法条目是「文型＋接続＋释义＋例句＋级别＋出处」，
差异只有两个字段。共享的是稳定 ID、级别分组、来源追溯、审计规则和（将来的）复习队列——
学习者需要知道的是今天要复习 52 条，不是欠了 40 个词和 12 条语法。

**当前能力**：

- **查询**：本地 JMdict 词典（约 21.9 万词目）＋教材内容包＋个人条目，三个来源合并成一份
  游标分页的结果，去活用还原和罗马字输入都支持。搜索框会说明本次实际查询了哪些来源；
  词典未安装时不假装覆盖了它。安装 / 更新词典是显式动作，查词永不联网。
- **详情**：中文学习释义与词典英文释义分开展示；词典条目按「表记 → 读音 → 义项」逐层
  选择，只列出该组合真正允许的义项，收藏记录所选组合与词典版本。
- **学习**：两条路径。**顺序学习**——选一个单元或整个内容包，逐条过：看到完整内容
  （表记、读音、词性、释义、接续、例句、朗读），逐条决定「加入复习」还是「已会，跳过」，
  可选先遮住释义自测；进度会保存，关掉再回来接着学。**学习计划**——按范围、方向、
  每日额度、顺序与学习时区每天自动投放。两者与专项练习产出的是**同一张卡**：一个条目的
  一种能力只有一份复习进度。学过的条目进入「今日背诵」，按 SM-2 调度。
- **练习**：按题型组题、即时或整组反馈、跳过与本轮巩固、错题本、问题反馈与撤回处理。
- **离线**：本地服务停止后，已缓存的内容包仍可浏览、查询与查看条目详情；已准备的离线
  题包可本地判分，重连后核验。作答与提示先写入 IndexedDB 再发送。

**尚未完成**：内容包里 2,085 条自动生成的题目模板尚未人工审核，因此暂不计入正式客观
练习；界面会按题型说明原因。真实浏览器端到端验收尚未进行。剩余工作见
[docs/词汇语法模块未完成项详细实现文档.md](docs/词汇语法模块未完成项详细实现文档.md)。

内容包放在 `lexicon/<包名>/`，制作流程见
[docs/LEXICON_PIPELINE.md](docs/LEXICON_PIPELINE.md)，整体方案见
[docs/LEXICON.md](docs/LEXICON.md)，当前生效的契约见
[docs/ADR.md](docs/ADR.md) 的 ADR-LEX-007 与 ADR-LEX-008。

**版权边界**：从教材 OCR 得来的内容包不可再分发——OCR 只改变载体，不改变权利状态。
教材正文、目次转写和匹配映射都不进版本库，也不进任何发布制品；这是强制检查，
不是一个可以改的标志位（ADR-LEX-006）。

## 常用参数

打开另一门课程：

```powershell
python .\start_dictation.py --manifest ".\courses\其他课程\manifest.json"
```

只启动服务、不自动打开浏览器：

```powershell
python .\start_dictation.py --no-browser
```

指定端口（注意：换端口 = 换一份独立的学习进度）：

```powershell
python .\start_dictation.py --port 4180
```

## 测试

```powershell
python .\run_tests.py            # 全部（Python + Service Worker）
python .\run_tests.py security   # 只跑安全回归
```

Service Worker 的缓存与 Range 测试需要 Node。Node 缺失时会**报错而不是跳过**，
因为这两块逻辑没有其他覆盖方式。

刷新文档引用的事实数字：

```powershell
python .\src\implementation_facts.py
```

## 目录说明

```text
dictation/
├─ start_dictation.py       # 唯一推荐的日常启动入口
├─ src/                     # Python 源码、播放器和审核页面
├─ config/                  # provider 配置模板（哪个模型跑构建）
├─ courses/                 # 可直接运行的课程清单与音频
├─ exams/                   # 已导入的 JLPT 真题
├─ lexicon/                 # 词汇 / 语法内容包（正文不进版本库）
├─ assets/                  # 内容补丁、版权台账和发布配置样例
├─ docs/                    # 流水线说明、产品分析和商业化文档
├─ dist/                    # 已生成的候选发布包
├─ requirements.txt         # 本地转写、繁转简和 yt-dlp 的可选依赖
└─ PROJECT_STRUCTURE.md     # 完整整理记录与维护说明
```

更详细的文件用途、清理结果和维护规则见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)。

## 导入新真题（可选）

```powershell
python -m pip install pymupdf pillow          # 只有导入时需要
python src\exam_import.py render   --pdf "dist\某某真题.pdf" --out .\exam-work\pages
#   逐页转写成 exams\<名称>\pages\pNN.json，答案抄成 answer-key.txt
python src\exam_import.py assemble --pages exams\<名称>\pages `
                                    --key exams\<名称>\answer-key.txt `
                                    --meta exams\<名称>\exam-meta.json `
                                    --out exams\<名称>\exam.json
```

扫描件通常没有可用的文字层（去水印会破坏字体的 ToUnicode 表），所以页面必须看图转写；
`render` 会为每页额外输出三条高分辨率横条，专门用来逐字确认假名。完整流程见
[docs/JLPT_EXAM.md](docs/JLPT_EXAM.md)。

「看图转写」这一步可以交给本地视觉大模型，见下一节。

## 用本地大模型 OCR 把扫描 PDF 转成文档（可选）

本机四个模型的完整分工、端口、听写两阶段生成以及 GLM-OCR → GLM-4.6V →
Flash-Next 异常页复核流程，见 [docs/LOCAL_MODEL_PIPELINES.md](docs/LOCAL_MODEL_PIPELINES.md)。

图片型 PDF → Markdown / JSON，全程离线不上传。默认 Qwen2.5-VL-7B，需要一块
显存 ≥ 16 GB 的 N 卡（环境已建在 `.venv-ocr\`）。

```powershell
cd src
..\.venv-ocr\Scripts\python.exe -m pdf_ocr probe "..\dist\某本书.pdf"
..\.venv-ocr\Scripts\python.exe -m pdf_ocr run "..\dist\某本书.pdf" -o ..\out\某本书 --mark-ruby-lines
```

产物是 `document.md`（给人读）和 `document.json`（给大模型改）。**每转完一页就落盘**，
中断后重跑同一条命令会接着跑，不会重来。选型对比、显存实测和参数说明见
[docs/PDF_OCR.md](docs/PDF_OCR.md)。

## 用在线视频做听力（可选）

课程的媒体可以是网上的视频，比如 YouTube 的日语新闻。**视频从不下载到本地**：
本地只留时间轴、逐句文本，和我们自己生成的翻译讲解。

```powershell
# 有站点字幕就用站点字幕，没有就临时取音频做本地转写（音频用完立即删除）
python .\src\build_video_course.py --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" `
  --language ja --profile deepseek
```

也可以在工作台里做：`python .\src\studio_server.py` → 切到「在线视频」标签 →
粘贴链接 → 探测 → 开始制作。

课程做好后照常打开，逐句听写、逐句循环、盲听、变速都能用：

```powershell
python .\start_dictation.py --manifest .\courses\<课程名>\manifest.json
```

不同站点开放给页面的能力差别很大，播放器会直说这门课属于哪一档：

| 档位 | 站点 | 精听能做到什么 |
|---|---|---|
| 可完全控制 | YouTube、Vimeo | 逐句自动循环、盲听、听 N 遍、变速 |
| 只能重载定位 | 哔哩哔哩等 | 可反复重播某句，但没有自动循环 |
| 需在原站播放 | 拒绝被嵌入的站点 | 逐句字幕 + 听写题 + 「在原站 mm:ss 打开」 |

**版权**：这类课程被标记为不可再分发，`release_readiness.py` 和 `content_license.py`
会明确拒绝它们。自己学可以，打包分发不行。

抓站点字幕和临时取音频需要可选依赖 `yt-dlp`（`pip install yt-dlp`）；
用你自己的 `.srt` 文件建课则不需要。完整说明见 [docs/VIDEO_COURSES.md](docs/VIDEO_COURSES.md)。

## 构建新课程（可选）

### 图形界面

不想记命令行参数就用工作台：

```powershell
python .\src\studio_server.py
```

浏览器会打开 `http://127.0.0.1:4174`，统一支持三种入口：

- 拖入音频：ASR → 翻译讲解 → 质量审计 → 一键装入听写课程库；
- 粘贴视频链接：站点字幕 + 本地 ASR 双源核验 → 翻译讲解 → 自动装入课程库；
- 拖入 PDF：本地多模型 OCR → 异常页复核 → 自动识别真题/词汇/语法 → 结构化审阅草稿。

PDF 的结果会显示产物目录、实际使用的模型、异常页和质检状态。具备完整印刷答案证据与文字层目录的试卷/教材，质检通过后直接自动装库；无明确答案或结构异常的内容自动隔离，仅在需要时按问题排查。

**工作台不能替你构造模型配置**：它只能从 `config/providers.json` 里已有的 profile 里选。
`cli` 和 `command` 两种 provider 会起子进程，如果允许网页自己指定命令，任何拿到同源立足点的
攻击者就能在你机器上执行任意程序。配置文件是你亲手编辑的所以可信，请求体永远不可信。

工作台会在加载时实时检测模型状态：本地 HTTP 模型必须能返回已加载的模型，CLI/命令必须已安装，
云端 profile 必须已经设置它声明的 Key 环境变量。不可用项仍显示原因但不能选择；启动服务、安装
CLI 或设置凭据后，点右上角「刷新模型状态」即可更新。订阅型 Codex CLI 也作为只读、临时会话的
具名 profile 保留在示例配置中。

音频和 PDF 走上传，不走路径——服务端没有任何读取或列举任意路径的接口。PDF 默认使用
`local-pdf-quality`：GLM-OCR 全页识别 → GLM-4.6V 异常页复核 → Flash-Next 最终疑难页。
云端视觉管线继续保留，但必须由你在页面中显式选择；本地服务掉线不会静默上传页面。

### 命令行

构建入口是 `src/build_course.py`。**它不预设任何模型**：转写用什么、翻译讲解用什么，
都在运行时决定，可以是云端 API、本机跑的模型、你已经订阅的 AI CLI，或者干脆不用 API。

先挑一个 provider：

```powershell
copy .\config\providers.example.json .\config\providers.json
python .\src\build_course.py --list-profiles
```

然后按你手上有的东西选一条：

```powershell
# 云端 API（密钥只放环境变量，不进配置文件、不进命令行）
$env:DEEPSEEK_API_KEY = "sk-..."
python .\src\build_course.py --audio .\in.mp3 --profile deepseek --install

# 本机跑的模型，不需要任何密钥
python .\src\build_course.py --audio .\in.mp3 --profile ollama --install

# 把订阅的 AI CLI 当 API 用
python .\src\build_course.py --audio .\in.mp3 --kind cli --command "claude -p" --install

# 完全不用 API：写出提示词文件，你在任意聊天窗口里回答后再 --resume
python .\src\build_course.py --audio .\in.mp3 --kind manual --handoff-dir .\handoff
```

转写同样可换：本地 `faster-whisper`、云端音频 API、任意转写命令，或直接导入已有字幕
（`--transcript subs.srt`，此时完全不需要 ASR 模型）。

依赖是**按需**的。文本模型一个包都不用装（全部走标准库 urllib 或子进程）；
只有本地转写和繁转简需要：

```powershell
python -m pip install -r .\requirements.txt
```

构建完可以直接装进 `courses/` 并播放：

```powershell
python .\src\install_course.py .\my-course.zip --name my-course
python .\src\install_course.py --list
python .\start_dictation.py --manifest ".\courses\my-course\manifest.json"
```

完整说明、各 provider 的接法和排错表见 [docs/COURSE_PIPELINE.md](docs/COURSE_PIPELINE.md)。
内容修复、质量检查、人工审核和重新打包工具也统一放在 `src/` 中。

> `src/build_deepseek_offline_bundle.py` 仍可运行，但已是薄兼容层。它现在要求显式的
> `--deepseek-model`：过去那个写死的默认模型名意味着构建会指向一个谁也说不清的目标，
> 并在名字失效后到第一个批次才失败。

## 数据与安全

- 本地服务只监听 `127.0.0.1`，不要将它改成局域网或公网地址。
- 默认学习数据库位于 `%LOCALAPPDATA%\dictation-preview\learning.sqlite3`，不在项目目录内。
- `dist/2010-12-N2-commercial-candidate.zip` 是技术候选包，不代表相关课程内容已经取得商业授权。

### 本地 API 的防护边界

`/api/*` 的**读和写**都要求本次会话的令牌，`Host` 必须是服务实际绑定的回环地址。
令牌由启动器生成、经继承的环境变量交给服务，不进命令行、URL 或日志；页面通过
同源的 `/api/session/bootstrap` 取得，只驻留在内存中。

**防的是**：远程网页、DNS rebinding、误连到本机未知服务的客户端。

**不防的是**：与你同权限运行的本机恶意进程、浏览器扩展、系统级恶意软件。这些
已经拥有你自己的文件访问权限，不在本边界内。

### 学习数据的离线边界

- 生词、笔记、打卡、学习日志和 SRS 复习使用浏览器持久化 outbox：断网时先在本地生效，
  联网后按依赖顺序重放；删除墓碑会阻止旧服务端快照把已删除内容复活。服务端写入接受
  客户端操作 ID，重复重放不会重复打卡或重复推进 SRS。
- 当前 outbox 与进度快照仍保存在当前浏览器 profile 的 `localStorage`，还没有迁移到
  IndexedDB，也没有实现跨浏览器 profile 的合并。长期存储权威边界仍需签署
  [ADR-STORE-001](docs/ADR.md)。清理浏览器站点数据前请先备份本地 SQLite 数据库。
- 默认课程 `2010-12-N2` 内容确实损坏。恢复候选存在但未通过听审，且覆盖音频更少，
  按合同不自动切换。
