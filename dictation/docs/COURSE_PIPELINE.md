# 课程制作流水线

从一段音频到一门可以打开的课程，中间没有任何写死的模型名。转写用什么、翻译讲解用什么，
都在运行时决定。

```
音频 ──► ASR provider ──► 分句合并 ──► 文本 provider ──► 简体规范化
     ──► 稳定内容模型 ──► 质量门 ──► 校验过的 ZIP ──► 装进 courses/
```

入口：[`src/build_course.py`](../src/build_course.py)。
安装：[`src/install_course.py`](../src/install_course.py)。
局部返修：[`src/repair_enrichment.py`](../src/repair_enrichment.py)。

> 要**照着做**而不是理解设计，看 [LISTENING_COURSE_RUNBOOK.md](LISTENING_COURSE_RUNBOOK.md)：
> 分诊、逐步命令、每步的判断标准和失败处置。本文只讲为什么这样设计。

---

## 0. 图形界面（不想碰命令行就看这一节）

```powershell
python .\src\studio_server.py
```

浏览器打开 `http://127.0.0.1:4174`，三步：拖入音频 → 选转写模型和翻译模型 → 构建完点「装入课程库」。
构建日志实时显示，可以随时停止。

界面能做的事就是本文档第 1–4 节那条命令行流水线，一个参数不多一个不少。它**不能**做的事：

- **不能自己指定模型地址、模型名或命令**，只能从 `config/providers.json` 里已有的 profile 中选。
  `cli` 和 `command` 两种 provider 会起子进程；如果允许网页传命令进来，任何拿到同源立足点的攻击者
  就能在你机器上执行任意程序。配置文件是你亲手编辑的所以可信，请求体永远不可信。
  测试里有一条专门验证这点：请求体里塞 `command` / `model` / `baseUrl` 一律不会进入构建参数。
- **不能读取任意路径**。音频走上传接口，服务端没有列目录或读文件的端点，也就没有穿越面。
  上传后的文件名由服务端生成，客户端传来的文件名只作为显示用的元数据。

安全边界与播放器完全一致（回环 Host 白名单 + 每次调用都要会话令牌 + 写操作校验 Origin 和
Fetch Metadata），挡的是远程网页、DNS rebinding 和误连的本地客户端；挡不住已经以你的身份
运行的进程——这一点和播放器一样，写在这里是因为它不该被含糊过去。

构建跑在**子进程**里而不是线程里：可以真正停掉，输出天然可流式读取，而且模型代码崩溃
（比如本文档 3.3 节那个段错误）只会带走子进程，不会带走服务。

常用参数：

```powershell
python .\src\studio_server.py --port 4174 --no-browser
python .\src\studio_server.py --courses-dir .\courses --config .\config\providers.json
```

工作区默认在 `studio-work/`（已 gitignore），里面是上传的音频和构建产物。

复核编辑器可直接通过 `http://127.0.0.1:4174/editor.html` 打开。它会列出全部尚未逐句或逐页
确认的构建草稿与已装课程、显示复核进度，并允许手动选择当前编辑和整课分析目标。模型分析
只产生报告；只有人工保存句子或页面才会推进复核进度。

---

## 1. 先决定用什么模型

**这个项目不提供默认模型。** 网络类 provider 没有模型名会在启动时就报错，并列出三种设置方式，
而不是跑到第一个批次才失败。

配置解析顺序，后者覆盖前者：

```
内置形状默认值  →  配置文件里的 profile  →  环境变量  →  命令行参数
```

配置文件按顺序查找第一个存在的：

1. `--config <路径>`
2. `$env:DICTATION_PROVIDERS_CONFIG`
3. `config/providers.json`（项目级，已 gitignore）
4. `%APPDATA%\dictation\providers.json`（用户级）

开始用：

```powershell
copy .\config\providers.example.json .\config\providers.json
python .\src\build_course.py --list-profiles
```

### 密钥规则

配置文件里写的是**存放密钥的环境变量名**（`apiKeyEnv`），不是密钥本身。
文件里出现字面量 `apiKey` / `token` / `secret` 会被直接拒绝加载——配置文件会被提交、
被分享、被贴进 issue。

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."     # 密钥只存在于你的 shell
```

指向 `127.0.0.1` 的本地服务不需要密钥；指向公网又没有 `apiKeyEnv` 会被拒绝，
因为那几乎总是配错了。

---

## 2. 文本 provider：六种接法

| kind | 用来接什么 | 需要装什么 |
|---|---|---|
| `openai-compat` | 任何 `POST {baseUrl}/chat/completions`：DeepSeek、OpenAI、Groq、OpenRouter、SiliconFlow，**以及**本地的 Ollama shim / LM Studio / llama.cpp / vLLM / LocalAI | 无 |
| `anthropic` | Messages API | 无 |
| `ollama` | Ollama 原生 `/api/chat` | 无 |
| `cli` | **把订阅席位当 API**：跑一条命令，从 stdout 读答案 | 那条命令本身 |
| `manual` | 完全不自动化：写出提示词文件，你在任何聊天窗口里回答 | 无 |
| `echo` | 离线占位桩，测试和搭骨架用 | 无 |

传输层全部用标准库 `urllib` 或子进程。**没有任何厂商 SDK**，所以加一个 provider 不会加一个依赖。

### 2.1 云端 API

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
python .\src\build_course.py --audio .\in.mp3 --profile deepseek
```

不用配置文件也行：

```powershell
python .\src\build_course.py --audio .\in.mp3 `
  --kind openai-compat `
  --base-url "https://api.deepseek.com/v1" `
  --model "deepseek-chat" `
  --api-key-env DEEPSEEK_API_KEY
```

> 404 通常意味着 base URL 少了 `/v1`，报错里会直接提示这一点。

### 2.2 本地模型

本地模型在这里不是特例，就是一个普通的 `baseUrl`：

```powershell
# Ollama（原生 API，能用 format:json）
python .\src\build_course.py --audio .\in.mp3 --profile ollama

# Ollama / LM Studio / llama.cpp / vLLM 的 OpenAI 兼容端口
python .\src\build_course.py --audio .\in.mp3 `
  --kind openai-compat --base-url "http://127.0.0.1:1234/v1" --model "local-model" `
  --batch-size 8 --timeout 900
```

本地模型的上下文通常比云端小，**把 `--batch-size` 调小**（8～10）比调大更容易成功。

### 2.3 用订阅的 AI 当 API（`cli`）

订阅席位不是 API key，但它是一个能回答提示词的进程。任何「读 stdin、把答案打到 stdout」
的命令都能接：

```powershell
python .\src\build_course.py --audio .\in.mp3 `
  --kind cli --command "claude -p --output-format text" `
  --batch-size 8 --sleep 1
```

命令里可用的占位符：

| 占位符 | 替换成 |
|---|---|
| `{prompt_file}` | 系统提示词 + 批次提示词的完整文件路径 |
| `{system_file}` / `{user_file}` | 分开的两份 |
| `{model}` | profile 里的 `model`（如果设了） |
| `{batch}` | 批次文件名，方便命令自己记日志 |

命令里**没有** `{prompt_file}` 或 `{user_file}` 时，提示词走 stdin——多数一次性 CLI 是这样用的。

命令永远不经过 shell（`shell=False`），所以引号写错不会变成注入。
子进程环境里会强制 UTF-8，否则 Windows 上中文会被控制台代码页打成乱码。

### 2.4 完全不用 API（`manual`）

```powershell
python .\src\build_course.py --audio .\in.mp3 --kind manual --handoff-dir .\handoff
```

第一次运行会写出 `handoff\batch_001.prompt.txt` 等文件然后停下，并列出还缺哪些回复。
把每个 `.prompt.txt` 贴进任何聊天窗口，把模型返回的 JSON 存成同名的 `.reply.json`，然后：

```powershell
python .\src\build_course.py --audio .\in.mp3 --kind manual --handoff-dir .\handoff --resume
```

已经答好的批次会被复用，所以一门课可以分几次做完，全程不需要任何 key。

### 2.5 占位桩（`echo`）

`echo` 只写可见的占位文字，**不编造译文**。流水线默认拒绝打包它的产物：

```
Refusing to package a course whose explanations came from a stub provider.
```

要做骨架可以加 `--allow-stub-enrichment`，产物会被显式标记为不可发布
（`review.humanListening = "blocked"`）。

---

## 3. ASR provider：四种接法

| kind | 用来接什么 | 需要装什么 |
|---|---|---|
| `faster-whisper` | 本地 CTranslate2 Whisper | `faster-whisper` |
| `openai-audio` | 任何 `POST {baseUrl}/audio/transcriptions`（需支持 `verbose_json` 分段时间戳） | 无 |
| `command` | 任何写出 JSON / SRT / VTT 的转写工具 | 那个工具 |
| `import` | 直接用你已经有的转写文件 | 无 |

### 3.1 按语言自动选转写模型

最好的转写模型是分语言的。配置里的 `asrLanguageProfiles` 把语言码映射到 profile，
给了 `--language` 就自动选对应的模型：

```json
"asrLanguageProfiles": { "ja": "japanese-accurate", "en": "english-accurate" }
```

```powershell
python .\src\build_course.py --audio .\jp.mp3 --language ja   # -> japanese-accurate
python .\src\build_course.py --audio .\en.mp3 --language en   # -> english-accurate
python .\src\build_course.py --audio .\other.mp3              # auto -> 兜底 local-whisper-cuda
```

当前配置两个语言都路由到 large-v3——见下一节，这是复测之后的选择。想按语言换成
速度优先的模型，把值改成 `japanese-fast` / `english-fast` 即可，路由机制本身不区分快慢。

规则：

- 显式 `--asr-profile` 永远优先，路由只是默认值；
- `jp`/`en-US` 这类别名会归一化后再路由；
- **`--language auto` 不路由**。音频没读之前语言是未知的，拿日语模型转英语比慢更糟。
  这时用 `defaultAsrProfile`，命令行会明确打印它没有路由；
- 每次运行都会打印实际选中的 profile，不会静默换模型。

### 3.2 三个 profile 的实测取舍

同一段 5.2 分钟日语音频，RTX 4500 Ada，float16：

| profile | 模型 | 耗时 | 段数 | 中位段长 | <0.35s 的段 | >15s 的段 |
|---|---|---|---|---|---|---|
| `local-whisper-cuda` | large-v3 | 22.1s（14x） | 59 | 4.22s | 0 | 1 |
| `japanese-fast`（调参前） | kotoba-v2.0-faster | 5.0s（63x） | 78 | 3.36s | 2 | 2 |
| `japanese-fast`（出厂参数） | kotoba-v2.0-faster | 7.2s（44x） | 70 | 3.67s | 1 | **0** |

结论要说清楚：

- **kotoba 快 4 倍以上**，这一条至今成立；
- **但它的时间戳更差**。蒸馏解码器用时间戳精度换速度，会出现「0.02 秒的段里塞
  60 个字」这种物理上不可能的切分；
- 出厂参数里的 `maxSpeechDurationS: 20` 把超长段清到 0，但**清不掉超短段**——
  段时间戳来自解码器而不是 VAD，VAD 参数管不到它；
- 对听写课程来说段边界就是产品。质量门会把这些标成 `sentence.very_short` 警告，
  不会静默混进课程，但你需要知道它们存在。

**后来在整套 N2 音频上复测，推翻了「kotoba 日语文本质量更好」这个假设。**
数字记在 `config/providers.json` 两个 profile 的 `description` 里：

- 与经 5 轮人工修补的 N2 课程比，`japanese-accurate`（large-v3）一致率 **93.9%**，
  `japanese-fast`（kotoba）只有 **57.5%**；
- kotoba 在这段音频上**漏掉约 19% 的字**，时间轴覆盖也少 4.4 个百分点；
- 换一个 beam size 重跑，kotoba 的自我一致率只有 **44%**——它的输出本身就不稳定；
- 26 个段短于 0.35 秒，20 个段的语速物理上不可能。

所以现在的取舍是：**做成品一律用 `japanese-accurate` / `english-accurate`；
`japanese-fast` / `english-fast` 只用来出草稿或试跑流水线。**
上面那张 5.2 分钟的表衡量的是速度和段边界，不是识字准确率——两张表要一起看，
只看第一张会得出相反的结论，这正是当初的错。

### 3.3 kotoba 不能用词级时间戳

`kotoba-whisper-v2.0-faster` 的 CTranslate2 转换没有可用的 alignment heads，
向它索要词级时间戳会让**进程直接段错误**（实测 exit 139），不是抛异常。
段错误在进程内捕获不了，所以这条限制写在 profile 上：

```json
"supportsWordTimestamps": false
```

配上它，`--word-timestamps` 会在启动时被拒绝并说明原因。
`large-v3` 和 `Systran/faster-distil-whisper-large-v3` 都实测正常，不受此限制。

### 3.4 解码与 VAD 参数

`assets/content_patches/` 记录的历史问题——51 秒的幻觉集群、重复片段、
「一段停顿被编码成 35 秒的单句话」——都不是识字准确率问题，换模型解决不了。
它们由解码策略决定，现在这些开关都在 profile 里：

| 字段 | 默认 | 治什么 |
|---|---|---|
| `conditionOnPreviousText` | `true` | 设 `false` 切断重复循环，蒸馏模型尤其需要 |
| `hallucinationSilenceThreshold` | 不设 | 设 2.0 左右丢弃静音段上的幻觉 |
| `noRepeatNgramSize` | `0` | 设 5 左右压制重复片段 |
| `repetitionPenalty` | `1.0` | 同上，另一条路径 |
| `noSpeechThreshold` | `0.6` | 判静音的阈值 |
| `logProbThreshold` | `-1.0` | 低置信度段的丢弃线 |
| `compressionRatioThreshold` | `2.4` | 检测退化重复输出 |
| `initialPrompt` | 不设 | 喂题型术语，稳住格式化提示语 |
| `vadOptions.maxSpeechDurationS` | 无限 | **就是那个 35 秒单句**，设 20-25 |
| `vadOptions.minSilenceDurationMs` | `2000` | 2 秒才切，听力题停顿常常短于此 |
| `vadOptions.minSpeechDurationMs` | `0` | 丢弃过短的语音区 |
| `vadOptions.speechPadMs` | `400` | 语音区前后留白 |

默认值与 faster-whisper 自身一致，所以不设这些字段的旧 profile 行为不变。
这些参数都进 `cache_key()`，改了以后 `--resume` 会拒绝复用旧转写。

```powershell
# 本地，无 GPU 也能跑（默认 device=auto / int8）
python .\src\build_course.py --audio .\in.mp3 --asr-profile local-whisper-cpu --profile ollama

# 有 NVIDIA GPU
python .\src\build_course.py --audio .\in.mp3 --asr-model large-v3 --asr-device cuda --asr-compute-type float16

# 云端转写
python .\src\build_course.py --audio .\in.mp3 --asr-profile groq-whisper

# whisper.cpp 之类的外部命令
python .\src\build_course.py --audio .\in.mp3 `
  --asr-command "whisper-cli -m models\ggml-large-v3.bin -f {audio} -oj -of {output_stem}"

# 已有字幕，跳过转写
python .\src\build_course.py --audio .\in.mp3 --transcript .\subs.srt --language ja
```

`import` 和 `command` 能读：Whisper `verbose_json`、whisper.cpp JSON（毫秒 offsets）、
transformers 的 `timestamp` 数组、`{start,end,text}` 数组、本项目自己的 `segments.raw.json`、
SRT、WebVTT。读不懂时会明确说读不懂，并列出支持的格式——不会静默产出空课程。

> 纯文本转写没有时间轴，**不能**做成听写课程，工具会直接拒绝。

---

## 4. 安装与播放

```powershell
# 边构建边安装
python .\src\build_course.py --audio .\in.mp3 --profile deepseek --install --course-name my-course

# 或者事后安装已有的 ZIP
python .\src\install_course.py .\my-course.zip --name my-course

# 看装了哪些课（状态是**当场重新审计**出来的，不是读清单里自报的字段）
python .\src\install_course.py --list

python .\start_dictation.py --manifest ".\courses\my-course\manifest.json"
```

安装时只解出 `manifest.json`、清单指定的音频和质量报告。ZIP 里那份 web 播放器**故意不装**——
播放器由 `src/web/` 提供，每门课再存一份只会各自漂移。

安装前会先跑一次审计，有错误就拒绝安装（`--allow-failed` 可绕过），因为启动器本来也会拒绝打开它，
在安装时发现比在上课时发现好。

---

## 5. 断点续跑

```powershell
python .\src\build_course.py --audio .\in.mp3 --profile deepseek --resume
```

`--resume` 复用工作目录里的转写和批次结果，但会先校验：

- 缓存的转写属于**同一个音频**（比对 SHA-256），否则拒绝；
- ASR 设置**没有变过**（比对 `transcriptionConfig`），否则拒绝并打印两边差异；
- 每个批次结果的 `sourceDigest` 与当前批次一致，否则重跑那一批。

换了模型或换了音频想复用旧转写，这三道校验会挡住——这正是它们存在的意义。

---

## 6. 只返修，不重做

音频不用重新转写，只重生成坏掉或缺失的翻译讲解：

```powershell
python .\src\repair_enrichment.py .\courses\x\manifest.json --dry-run --include-missing
python .\src\repair_enrichment.py .\courses\x\manifest.json --profile ollama --include-missing
```

返修用的 provider 和构建时用的**不必是同一个**，返修记录会写进
`buildMetadata.enrichmentRepairs`。返修同样拒绝 `echo`：用占位符去修乱码只会把乱码藏起来。

---

## 7. 课程带着自己的来历

每门课的 `buildMetadata` 里记着它是怎么来的，`courses/<name>/install-source.json` 里也有一份：

```json
{
  "asr": { "kind": "faster-whisper", "model": "large-v3", "device": "cuda" },
  "enrichment": {
    "provider": { "kind": "openai-compat", "model": "deepseek-chat", "apiKeyEnv": "DEEPSEEK_API_KEY" },
    "models": ["deepseek-chat"],
    "translations": 517,
    "usage": { "totalTokens": 412330 },
    "stub": false
  }
}
```

记的是**环境变量名**，永远不是密钥值。

---

## 8. 常用参数速查

| 参数 | 作用 |
|---|---|
| `--list-profiles` | 看当前配置定义了哪些 profile |
| `--dry-run` | 打印解析后的方案就停，不转写、不调用、不写文件 |
| `--no-enrich` | 只转写，不做翻译讲解（此时不要求任何文本模型） |
| `--no-normalize` | 跳过繁转简 |
| `--strict-quality` | 有警告也拒绝打包，不只是有错误才拒绝 |
| `--keep-going` | 单个批次失败后继续跑完其余批次 |
| `--extra-body '{"...":...}'` | 往每个请求体里合并额外字段（thinking、top_p 之类） |
| `--no-json-mode` | 不向端点索要 JSON 响应格式（有些本地服务不支持） |

环境变量覆盖：`DICTATION_TEXT_PROFILE`、`DICTATION_TEXT_KIND`、`DICTATION_TEXT_MODEL`、
`DICTATION_TEXT_BASE_URL`、`DICTATION_TEXT_API_KEY_ENV`、`DICTATION_TEXT_BATCH_SIZE`，
以及对应的 `DICTATION_ASR_*`。

---

## 9. 排错

| 症状 | 原因和处理 |
|---|---|
| `No model set for text provider kind ...` | 这是设计行为，不是 bug。用 `--model`、`DICTATION_TEXT_MODEL` 或 profile 指定 |
| `HTTP 404 ... needs its /v1 suffix` | base URL 少了 `/v1` |
| `HTTP 401/403` | `apiKeyEnv` 指的那个环境变量在当前 shell 里没设 |
| `Command not found on PATH` | `cli` provider 的命令不在 PATH，用绝对路径 |
| `Cannot resume: ASR settings changed` | 换过 ASR 设置，去掉 `--resume` 或改回原设置 |
| 质量门报 `sentence.enrichment_corrupt` | 译文里混进了原文字符或替换字符；`repair_enrichment.py` 可以只修这些句子 |
| 本地模型批次总是失败 | 上下文不够，把 `--batch-size` 降到 8 或更低 |
| `Refusing to package ... stub provider` | 你用的是 `echo`，换真模型，或明确加 `--allow-stub-enrichment` |

---

## 10. 在二级编辑页维护课程与待复核草稿

启动 `python src/studio_server.py` 后，工作台提供两组只允许本机访问的维护功能：

- “本地模型”面板调用受信任的 `/workspace/ECGegg/scripts/start_models.sh` 和
  `stop_models.sh`，显示四个推理端点的实时状态与启动日志。浏览器不能传入命令或地址。
- “已装课程”里的“查看 / 编辑”会跳转到独立的 `editor.html?course=...` 二级页面，按句展示原文、翻译、讲解、时间轴、置信度与练习属性。
  手动保存会同步兼容字段，重算 `transcriptText`、`contentRevision` 和质量报告。
- 构建区的 PDF “待复核”结果提供“打开复核编辑器”，跳转到
  `editor.html?build=...`。编辑器把扫描原页、OCR 原文和真题/语法/单词结构化 JSON
  并排展示，支持逐页手动修正。服务重启后，已有的待复核草稿仍会重新载入。
- 模型辅助修改只接受 `config/providers.json` 中已有且当前可用的文本 profile。
  模型会接着当前编辑框中的人工改动做复合编辑；结果先成为候选稿，必须再次点击保存才会写入。
- 二级编辑页的“整课模型分析”会把全部句子或全部结构化页面按上下文容量分批送给所选模型，
  再执行一次全局汇总。报告列出跨课程重复错误、同音字风险、翻译/讲解一致性、结构缺失和
  修改优先级；分析过程不改写内容，报告保存在 `studio-work/analyses/<analysis-id>/report.md`，
  页面刷新或工作台重启后仍可恢复。
- 每次保存前，旧 `manifest.json` 会复制到课程目录下的 `.workbench-backups/`；
  草稿页也在其 `pages/.workbench-backups/` 留存旧版。编辑页面携带内容摘要，过期页面不能覆盖更新后的文件。
