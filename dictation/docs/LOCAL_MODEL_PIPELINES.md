# 本地模型课程制作总管线

本机的四个生成模型按能力分工，不让同一个模型同时负责“识别、改写、验收”。程序负责可重复的装配与审计，人负责最终来源核对。

## 模型分工

| 服务 | 端口 | 主要职责 | 不负责 |
| --- | ---: | --- | --- |
| Qwen3.8-27B-FP8 | 8100 | 听写课程翻译、语法与听力讲解的快速初稿 | OCR、最终来源确认 |
| GLM-4.6V-Flash | 8101 | 首轮 OCR 异常页、复杂版面、表格和接続框的视觉复核 | 批量 ASR |
| GLM-OCR | 8102 | 教材与真题扫描页的首轮 OCR | 教学内容的最终裁决 |
| Qwen3.8-Flash-Next | 8103 | 发布候选的高质量翻译讲解、疑难页第三意见 | 音频时间戳 |
| faster-whisper large-v3 | 进程内 | 日语音频 ASR 与词级时间戳 | 翻译、题目答案判断 |

`Qwen3.8-Flash-Next` 虽然不在 `/workspace` 的模型目录里，权重在 `/data/models/qwen3.8-flash-next/`，但通过同一个 OpenAI 兼容接口参与管线。

## 0. 每次制作前

```bash
# 模型服务由 ECGegg 统一管理；不带参数时四个服务并行启动
bash /workspace/ECGegg/scripts/start_models.sh

# 也可以只启动当前管线需要的模型，互相不会阻塞
bash /workspace/ECGegg/scripts/start_models.sh qwen
bash /workspace/ECGegg/scripts/start_models.sh vision
bash /workspace/ECGegg/scripts/start_models.sh ocr
bash /workspace/ECGegg/scripts/start_models.sh flash-next

# 停止方式相同：不带参数停止全部，带参数只停止一个
bash /workspace/ECGegg/scripts/stop_models.sh qwen
bash /workspace/ECGegg/scripts/stop_models.sh

# 四个端点与模型名必须全部匹配
python scripts/local_models_status.py

# 查看听写管线实际解析到的 profile
python src/build_course.py --list-profiles
```

状态检查失败就先停止，不要在半离线状态下静默切到云模型。本项目的本地 profile 不配置 API key，内容不会离开机器。

### 统一工作台

```bash
python src/studio_server.py
```

打开 `http://127.0.0.1:4174` 后可直接选择“本地音频 / 在线视频 / PDF 教材或真题”。PDF 默认
使用配置中的 `local-pdf-quality`，自动运行 GLM-OCR 首读、GLM-4.6V 异常页复核和
Flash-Next 最终疑难页，再路由成真题、语法、单词或通用 OCR 草稿。结果保存在
`studio-work/builds/<job>/artifact/` 并标为“待复核”；答案和教材目录数量不会由模型猜测。

本地音频和 PDF 都支持一次选择最多 50 个文件。文件先逐个上传并完成整批校验，再进入后台
队列；同一批次始终只运行一个制作任务，避免 ASR、OCR 和本地大模型同时争抢显存。页面会
显示每个文件的排队、制作、完成或失败状态，也可以点开任一项目查看日志，或取消尚在排队的
项目。多个文件默认分别使用各自文件名作为课程标题。

构建完成并显示“待复核”后，点击“打开复核编辑器”会进入独立二级页面，而不是在工作台首页
展开。页面按页并排显示 PDF 扫描图、OCR 原文和结构化 JSON，可人工修改，也可选择任一当前
可用的本地、CLI 或云端文本 profile 对当前人工稿继续复核。模型只回填候选稿，确认保存后才
写入文件，并自动保留上一版。已装课程的“查看 / 编辑”同样跳转二级页面，提供逐句编辑。
二级页面还提供“整课模型分析”：系统按上下文容量分批覆盖整课，再汇总共性问题与修改优先级；
该操作只生成可复制、可恢复的分析报告，不会自动修改任何句子或草稿页。
直接打开复核编辑器时，页面会列出全部尚未完成复核的构建草稿和已装课程，并显示逐页或逐句
进度。先手动选择目标，再执行局部模型复核或整课分析；每次人工保存才计入复核进度，全部保存后
目标自动退出待复核列表，单纯运行分析不会改变复核状态。

“本地模型”区域支持四个服务分别启动、停止，也支持一键并行启动或停止全部。每个模型卡片
独立显示在线状态和控制状态；一个大模型加载较慢或失败，不会再阻塞其他模型。启动/停止日志
按服务保留在工作台中，启动中的任务也可以直接停止。

工作台也会列出显式配置的云端视觉管线，但本地端点失效不会触发云端降级。音频/视频的
OpenAI、Anthropic、OpenRouter、Claude CLI 等已有订阅/API profile 保持可选。

### 订阅与云端接口继续保留

本地优先不是删除外部通道。现有 `openai-compat`、`anthropic`、`ollama`、`cli`、`manual` 和 `echo` provider 契约保持不变；`deepseek`、`openai`、`anthropic`、`openrouter`、`groq`、`siliconflow`、`claude-cli` 等 profile 继续可选。

```bash
# 云端 API（密钥仍只从环境变量读取）
python src/build_course.py --audio raw/news.mp3 --profile deepseek

# 使用已有订阅席位的 CLI；不是 API key
python src/build_course.py --audio raw/news.mp3 --profile claude-cli

# 没有 API 的任意聊天订阅，保留人工 prompt/reply 交接
python src/build_course.py --audio raw/news.mp3 --profile manual --resume
```

选择外部 provider 必须显式写 `--profile`，不会因为本地端点临时掉线而自动上传内容。这样既保留订阅模型的能力，也避免隐私边界发生静默变化。

## 1. 音频听写课程

```text
音频 → faster-whisper → 确定性分句 → Qwen27 初稿
     → 自动质量门 → Flash-Next 重生成终稿 → 人工逐句审听 → 安装
```

先用 Qwen27 快速暴露 ASR、分句和内容问题：

```bash
python src/build_course.py \
  --audio raw/news.mp3 --language ja --asr-profile japanese-accurate \
  --profile local-qwen27 --work-dir work/news \
  --out dist/news-draft.zip --force
```

原文和时间轴确认后，在同一工作目录切到 Flash-Next。`--resume` 只复用已经绑定到相同音频和 ASR 配置的转写；文本 provider 改变后，旧翻译会自动判为 stale 并重新生成：

```bash
python src/build_course.py \
  --audio raw/news.mp3 --language ja --asr-profile japanese-accurate \
  --profile local-flash-next --work-dir work/news \
  --out dist/news-final.zip --resume --force --install --course-name news
```

如果显存冲突，先让 ASR 独占一张 RTX 6000 Ada，或临时使用 `local-whisper-cpu`。不要为了同时跑四个服务而让 ASR 发生显存换页。
Linux 上通过 pip 安装的 `nvidia-cublas` / `nvidia-cudnn` 会由 ASR provider 自动发现并预加载，不需要每次手工设置 `LD_LIBRARY_PATH`。

## 2. 在线视频听写课程

工作台的成品默认走“站点字幕 + 独立 ASR”双源核验（命令行需显式写 `--transcript verified`）。结构质量错误最少的候选胜出；自动字幕有一分风险惩罚，同分时按“人工字幕 → 本地 ASR → 自动字幕”选择。选择过程写入 `transcript-verification.json`，不是由生成模型凭感觉覆盖原文。

```bash
# 快速初稿：只使用站点字幕，找不到才启用 ASR
python src/build_video_course.py --url '<video-url>' --language ja \
  --profile local-qwen27 --work-dir video-work/news --name news --force

# 已验证终稿：站点字幕与 faster-whisper 同时参与选源
python src/build_video_course.py --url '<video-url>' --language ja \
  --transcript verified --asr-profile japanese-accurate \
  --profile local-flash-next --work-dir video-work/news --name news \
  --resume --force
```

`--resume` 的 ASR 缓存绑定规范化视频 URL 和完整 ASR 配置；enrichment 结果继续绑定批次原文摘要和文本 provider 配置。任何一项变化都会判旧缓存为 stale。

Flash/Qwen 在讲解中指出“误识别、误听、应为……”时，管线会把对应句写入 `transcript-correction-review.json`。它只生成候选，不静默改原文。审核通过的修正用 source-digest 绑定补丁在同一次构建中应用：

```bash
python src/build_video_course.py --url '<video-url>' --language ja \
  --transcript verified --asr-profile japanese-accurate \
  --profile local-flash-next --work-dir video-work/news --name news \
  --content-patch assets/content_patches/news-homophone-repair.json \
  --resume --force
```

摘要不匹配时补丁会拒绝应用，避免旧索引误改新转写。视频本身不下载；临时音频在 ASR 结束后删除；远程媒体课程仍保持 `redistributable: false`。

## 3. 真题题库

```text
扫描 PDF → GLM-OCR 首读 → GLM-4.6V 复核异常页
         → Flash-Next 处理仍异常的疑难页
         → 确定性转 page JSON → 人工逐页对照 → assemble → validate
```

三层 OCR 使用相同缓存目录。每次 `--retry-flagged` 只替换质量报告标出的页面，并在单页缓存中记录实际模型：

```bash
# 第一层：专用 OCR 模型批量识别
python src/pdf_ocr/__main__.py run dist/paper.pdf -o exam-work/paper/ocr \
  --backend openai-vlm --server-base-url http://127.0.0.1:8102/v1 \
  --model zai-org/GLM-OCR --prompt doc --max-new-tokens 4096

# 第二层：视觉模型复核异常页
python src/pdf_ocr/__main__.py run dist/paper.pdf -o exam-work/paper/ocr \
  --retry-flagged --backend openai-vlm \
  --server-base-url http://127.0.0.1:8101/v1 \
  --model zai-org/GLM-4.6V-Flash --prompt doc --max-new-tokens 4096

# 第三层：只对仍被标记的疑难页使用最强模型
python src/pdf_ocr/__main__.py run dist/paper.pdf -o exam-work/paper/ocr \
  --retry-flagged --backend openai-vlm \
  --server-base-url http://127.0.0.1:8103/v1 \
  --model Qwen/Qwen3.8-Flash-Next --prompt doc --max-new-tokens 4096

# OCR Markdown → 真题页草稿
python src/exam_ocr_to_pages.py --ocr exam-work/paper/ocr \
  --out exams/<slug>/pages --level N2
```

之后人工核对 `pages/`、填写 `exam-meta.json` 与 `answer-key.txt`，再运行：

```bash
python src/exam_import.py assemble --pages exams/<slug>/pages \
  --key exams/<slug>/answer-key.txt --meta exams/<slug>/exam-meta.json \
  --out exams/<slug>/exam.json
python src/exam_import.py validate --exam exams/<slug>/exam.json
```

答案表不能由模型猜测。模型只转写看得见的内容，答案数量、跨页关系和题号由程序 fail-closed 校验。

## 4. 单词 / 语法内容包

前半段复用同一套多模型 OCR。语法书右侧接続框用 GLM-4.6V 单独读取原分辨率裁剪：

```bash
python src/pdf_ocr/__main__.py boxes dist/book.pdf -o out/book \
  --backend openai-vlm --server-base-url http://127.0.0.1:8101/v1 \
  --model zai-org/GLM-4.6V-Flash

# 正文已经缓存，这一步只重新合并 box 结果
python src/pdf_ocr/__main__.py run dist/book.pdf -o out/book \
  --backend openai-vlm --server-base-url http://127.0.0.1:8102/v1 \
  --model zai-org/GLM-OCR --mark-ruby-lines

python src/lexicon_import.py extract \
  --document out/book/document.json --out lexicon/<slug>
```

人工修正 `pages/`、填写 `units.txt` 后：

```bash
python src/lexicon_import.py assemble --pack lexicon/<slug> --accept-new-keys
python src/lexicon_import.py validate --pack lexicon/<slug>
```

词汇和语法共用这条管线，通过内容包的 `kind` 区分。OCR 文本、教材目次数量和匹配裁决不能互相充当自己的验收证据。

## 发布原则

1. 小模型做吞吐，强模型处理终稿和疑难项，视觉模型只处理需要看图的任务。
2. 模型输出永远先落入可审查的中间文件，不直接覆盖人工源文件。
3. 模型切换必须使缓存失效；每份产物记录实际 provider、模型和单页 OCR 来源。
4. 自动审计负责结构完整性，人工审核负责原文、翻译和答案的真实性。
5. 有 `error` 的产物不安装；商业发布还必须通过版权、人工审核和真实浏览器验收。
