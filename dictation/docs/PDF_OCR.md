# 本地大模型 OCR：扫描版 PDF → Markdown / JSON

把图片型（扫描）PDF 交给**本地视觉大模型**转成大模型可读可编辑的文档。全程离线，
不上传任何一页。为日语学习资料（JLPT 教材、真题）调过 prompt：一页里同时出现
日文假名汉字＋振り仮名、英文、简体中文、韩文时也不会被"翻译掉"。

代码在 [src/pdf_ocr/](../src/pdf_ocr/)。

## 选型：本地 OCR 大模型怎么挑

| 模型 | 参数量 | 适合 | 说明 |
| --- | --- | --- | --- |
| **Qwen2.5-VL-7B-Instruct** | 7B | **默认，推荐** | transformers 原生支持，不需要 `trust_remote_code`、不需要 flash-attn（Windows 上没有轮子）。日/中/韩 OCR 都强，24 GB 显存放得下 bf16 + 整页原图。 |
| **GLM-OCR（本机服务）** | 0.9B | **批量首轮 OCR** | 用 `openai-vlm` 调用 `127.0.0.1:8102`，不在当前 Python 进程重复加载权重。 |
| **GLM-4.6V-Flash（本机服务）** | 9B | **异常页与复杂版面复核** | 用 `openai-vlm` 调用 `127.0.0.1:8101`；适合对首轮 flagged 页给第二意见。 |
| Qwen2.5-VL-3B-Instruct | 3B | 显存小 / 要快 | 同一套代码，`--model Qwen/Qwen2.5-VL-3B-Instruct`。约快一倍，密排振り仮名会掉一些。 |
| dots.ocr | 1.7B | 版面还原优先 | 专做文档解析，直接吐 `bbox + category + text` 的 JSON，页眉页脚表格天然分离。小、快；但要 `trust_remote_code`。 |
| PaddleOCR-VL / MinerU | 0.9B+ | — | 效果好，但 Windows + Python 3.13 上 PaddlePaddle 装起来很痛，没纳入默认路径。 |
| 传统 OCR（Tesseract/PaddleOCR） | — | 不推荐用于本资料 | 纯文字识别，没有版面理解，振り仮名会和正文混成一行乱码。 |

结论：**Windows + 单卡 24 GB，用 Qwen2.5-VL-7B**。要更快就换 3B，要版面 JSON 就用 dots.ocr。

## 环境

已经装好在 `.venv-ocr/`（独立虚拟环境，不动项目原有的 Python）：

```
torch 2.6.0+cu124      transformers 4.57.6
torchvision 0.21.0     accelerate / pymupdf / pillow
```

重建的话：

```powershell
python -m venv .venv-ocr
.venv-ocr\Scripts\python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
.venv-ocr\Scripts\python.exe -m pip install "transformers>=4.51,<5" accelerate pymupdf pillow huggingface_hub hf_transfer safetensors sentencepiece
```

> cu124 是刻意选的：显卡驱动 537.70 报 CUDA 12.2，cu124 靠 CUDA minor version
> compatibility 能跑；而 cu124 在 Python 3.13 上只有 torch 2.6.0 这一个版本。

## 用法

```powershell
cd C:\Users\cribug\OneDrive\Desktop\dictation\src

# 先看看这个 PDF 是什么货色（有没有文字层、多少页）
..\.venv-ocr\Scripts\python.exe -m pdf_ocr probe "..\dist\某本书.pdf"

# 跑前 20 页试水
..\.venv-ocr\Scripts\python.exe -m pdf_ocr run "..\dist\某本书.pdf" -o ..\out\某本书 --pages 1-20 --batch-size 4

# 整本
..\.venv-ocr\Scripts\python.exe -m pdf_ocr run "..\dist\某本书.pdf" -o ..\out\某本书 --batch-size 4
```

### 产物

```
out/某本书/
  document.md            整本的 Markdown，页与页之间 <!-- page: N --> + ---
  document.json          每页一条：markdown / blocks / 耗时 / 错误，喂给大模型用这个
  quality-report.json    每页字数、假名汉字占比、复读检测、flags
  pages/page-NNNN.json   单页缓存
  images/page-NNNN.png   页面图
```

### 断点续跑

**每转完一页就立刻落盘到 `pages/page-NNNN.json`。** 跑到一半被 Ctrl-C、断电、
或者用量到顶，重跑同一条命令会跳过已完成的页，只补没做的。这是为长文档故意设计的。

### 重做识别差的页

`quality-report.json` 会给可疑页打 flag：`error`（报错）、`empty`（空）、
`repetition-loop`（大模型复读）、`very-short`（字数异常少）。

```powershell
# 推荐：提分辨率重跑（治本）
..\.venv-ocr\Scripts\python.exe -m pdf_ocr run "..\dist\某本书.pdf" -o ..\out\某本书 `
    --retry-flagged --max-pixels 6422528
```

> **重跑必须改动点什么。** 解码是贪心的（`do_sample=False`），同样输入必然产出同样输出
> ——**原样重跑复读页，会一字不差地再复读一次**。

**复读是症状，不是病。** 本书 5 页复读，全部发生在密排的「接続」小方框上：
分辨率不够时那个框半清不楚，模型就开始枚举活用形停不下来。实测页 38：

| 处理 | 结果 | 耗时 |
| --- | --- | --- |
| 原样重跑 | 照样复读 | — |
| `--repetition-penalty 1.05` | **还是复读**，有一页反而更长（3648 → 11193 字） | 48 s |
| `--repetition-penalty 1.15` | 复读消失，1136 字 | 48 s |
| **`--max-pixels 6422528`** | **复读消失，1455 字**（方框真读出来了） | 318 s |

提分辨率不但消除复读，还**多捞回约 28% 的内容**——因为它解决的是模型"看不清"这个
根因，而 penalty 只是压住症状。几页的量，318 s/页完全划算。
`--repetition-penalty` 留作备选（日语本来就大量重复助词，调太高会开始吃字），
平时保持 `1.0`。

## 常用参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--backend` | `qwen-vl` | `qwen-vl` / `dots-ocr` / `ollama` / `openai-vlm` |
| `--model` | 各 backend 自带 | 换模型，如 `Qwen/Qwen2.5-VL-3B-Instruct` |
| `--server-base-url` | `127.0.0.1:8102/v1` | `openai-vlm` 的 vLLM / llama.cpp OpenAI 兼容端点 |
| `--batch-size` | 1 | 同时解码几页。解码是显存带宽瓶颈，24 GB 上开 4 大约快 3 倍 |
| `--max-pixels` | 3211264 | 每页视觉 token 预算（÷784 得 token 数）。见下面「分辨率这道坎」 |
| `--max-new-tokens` | 3072 | 单页输出上限 |
| `--prompt` | `doc` | `doc`（振り仮名转成 `北(きた)`）/ `doc-no-ruby`（丢掉振り仮名，更准）/ `layout` |
| `--pages` | 全部 | `1-20`、`3`、`1,4,9-12` |
| `--drop-running-heads` | off | 从 document.md 里抹掉页眉页脚注释 |
| `--mark-ruby-lines` | off | 把游离的振り仮名行包成 `<!-- ruby: ... -->`。**不删任何字** |

## 分辨率这道坎（实测，RTX 4500 Ada 24 GB）

7B 权重 bf16 占 16.6 GB。视觉塔的注意力开销随 `--max-pixels` **超线性**增长，
单页峰值显存实测：

| `--max-pixels` | 视觉 token | 峰值显存 | 单页耗时 |
| --- | --- | --- | --- |
| 1,003,520 | 1,242 | 17.2 GB | — |
| 1,605,632 | 2,022 | 18.0 GB | — |
| 2,408,448 | 3,060 | 19.5 GB | — |
| **3,211,264** | **4,052** | **21.5 GB** | **~48 s** |
| 6,422,528 | 7,868 | **33.8 GB** ⚠ | ~335 s |

**超过 ~3.2 MP 这张卡就不够用了。要命的是 Windows/WDDM 不会报 OOM**，
而是悄悄把显存换页到系统内存，程序照跑，速度塌掉 7 倍。所以默认值取的是
"真正装得下的最大值"，不是"模型能接受的最大值"。

同理，`--batch-size` 在这台机器上几乎没有收益：解码本该是显存带宽瓶颈（开 batch
能接近线性提速），但显存已经贴着天花板，batch 4 实测只有 15.3 tok/s vs batch 1 的
12.1 tok/s。**换更小的模型（3B）比开 batch 有用得多。**

### 振り仮名怎么处理

这本书几乎每个汉字上都有振り仮名，字高只有约 12 px。实测：

* `--max-pixels 3211264`（默认）：振り仮名**看不清**。此时若还用 `--prompt doc`
  要求标注读音，模型会**编**读音 —— 比不标更糟。所以默认配套用 `doc-no-ruby`。
* `--max-pixels 6422528` + `--prompt doc`：读音确实能读出来，但会另起一行输出
  （`北へ行くにしたがって` 下面单独一行 `きたい`），并不是要求的 `北(きた)`；
  而且整本要跑 ~14 小时。

结论：**要正文，用默认配置；要读音，得换硬件或换模型**，别在这张卡上硬来。

### 游离的振り仮名行

即使用了 `doc-no-ruby`，模型还是会把半看清的振り仮名单独甩一行出来：

```
この本の使い方
ほんつかかた            ← 这行
```

实测本书约 **17%** 的非空行是这种噪声。加 `--mark-ruby-lines` 会把它们包成
`<!-- ruby: ほんつかかた -->`：

* **不删字**，读音还在，人和大模型都能一眼跳过；
* 判据是「纯假名 + 上一行含汉字 + 长度 ≤ 60」。真正的假名句子几乎都带句读
  （`。、`），所以不会被误伤；单页缓存 `pages/*.json` 永远存原样，改判了重拼一次就行。

## 断点续跑的定时任务

本次已注册一个 Windows 计划任务，在 2026-09-02 06:35 重跑一次续跑命令：

```powershell
schtasks /query /tn ResumePdfOcrN2        # 看状态
schtasks /run   /tn ResumePdfOcrN2        # 立刻跑一次
schtasks /delete /tn ResumePdfOcrN2 /f    # 不需要了就删掉
```

它执行 [scripts/resume_pdf_ocr.cmd](../scripts/resume_pdf_ocr.cmd)，跑的就是上面那条
`run` 命令。因为有单页缓存，**已经转好的页会跳过**；整本已经跑完的话它只是重新
拼一次 document.md / document.json 就退出。日志追加在 `out/N2-grammar/resume.log`。

## 二次通道：把被丢掉的接続框捞回来

**整页 OCR 会系统性丢掉浮在右侧的语法接続框。** 抽查页 22/45/92，框全部整块缺失——
不是识别错，是根本没输出。原因还是分辨率：整页要缩到 3.2 MP 才装得下显存，框里的小字
第一个变得不可读，模型就把整块放弃了。

```powershell
# 先跑正文（如果还没跑）
..\.venv-ocr\Scripts\python.exe -m pdf_ocr run   "..\dist\某本书.pdf" -o ..\out\某本书
# 再补框
..\.venv-ocr\Scripts\python.exe -m pdf_ocr boxes "..\dist\某本书.pdf" -o ..\out\某本书
# 重跑 run 把框合并进产物（正文全缓存，不重跑模型）
..\.venv-ocr\Scripts\python.exe -m pdf_ocr run   "..\dist\某本书.pdf" -o ..\out\某本书 --mark-ruby-lines
```

**为什么这样比整本高分辨率重跑好**：框在右半幅，裁右 50% 得 1032×2976 = **3.07 MP**，
正好在显存安全线内，于是**完全不缩放**——框以原始扫描分辨率进模型。整本 6.4 MP 重跑要
~9.5 小时，这条通道 ~11 s/页，全书约 **35 分钟**。

产物落在 `boxes/page-NNNN.json`，合并时以 `<!-- box -->` 标记追加到该页正文之后，
**不覆盖正文**。

### 两个必须挡住的坑

**一、空白页会凭空造内容。** 页 16 是全白页，box 通道却编出了 `1. て形 / 2. た形 /
3. ている形…`，还跑了 62 秒。所以 `--min-ink`（默认 0.002）会先量裁剪区墨量，
**没墨的页直接由程序答 `<!-- no box -->`，根本不问模型**。全书只有 2 页触发。

**二、prompt 里写具体例子会被抄进结果。** 我最初在 prompt 里举了
`Vない / Vている / Aい + うちに` 当例子，结果页 92（讲 際して/基づいて 的）输出里
直接混进了这一行——那是页 38 的语法点。**box prompt 里不能出现任何具体的日语语法示例**，
只能抽象描述。

无框但有正文的页（如前言页）不会造假，但会倒出正文碎片；这种过度捕获由
`box-suspicious` flag 标出（判据：总长 > 600 字，或 ≥3 行超过 30 字），不静默混入。

**三、框上的复读是"临界"的，不是确定的。** 接続框里把多个词尾用大括号并到一个词干上，
那个括号正好是贪心解码的临界点：要么读出分支，要么latch住复读到 token 上限。
**同一张裁剪图，验证时干净、生产跑时复读**——bf16 + SDPA 在不同调用形状下不是逐位
确定的。所以做了两层：

* 生成时：`box_is_degenerate` 一旦命中，**自动带 `--retry-penalty`（默认 1.15）重跑一次**；
* 合并时：**再查一次**，退化的框直接不合并（正文是好的，不能被复读污染）。

实测 157 页中 10 页首次退化，自动重试后全部恢复干净。因为这是临界现象而非确定性 bug，
检查必须放在合并时，不能只放在生成时。

## 和 `exam_import.py` 的关系

`src/exam_import.py` 的 `render` 和 `assemble` 之间故意留了一步「读页面」不做，
交给人或大模型。**本工具补的就是这一步**，但它出的是通用 Markdown / JSON，
不是 `exam_import` 要的 `p<NN>.json` 区块契约（带题号、选项、跨页续接标记）。
所以 `document.json` 是喂给模型去产出 `p<NN>.json` 的原料，不是它的替代品。

## Ollama 兜底

万一 CUDA/transformers 这套环境哪天坏了：

```powershell
winget install Ollama.Ollama
ollama pull qwen2.5vl:7b
..\.venv-ocr\Scripts\python.exe -m pdf_ocr run "..\dist\某本书.pdf" -o ..\out\某本书 --backend ollama
```

这条路只用 urllib 说话，不碰 torch —— 和本仓库"加 provider 不加依赖"的惯例一致。

## 扫描件倒置（`/Rotate 180`）

日文扫描书经常整本存成 `/Rotate 180`。**本工具的无损快路径（整页单图直接抽原 JPEG）
不经过渲染器，所以不会自动应用页面旋转**——`render.py` 里已按 `page.rotation` 逐页
补正，但如果你改动那段代码，这是最容易再次踩到的坑：漏掉它不报错，只是把整本倒着
喂给模型。

实测本批五本：

| 书 | 页数 | `/Rotate` |
| --- | --- | --- |
| N1级汉字 | 212 | **180 × 209**，0 × 3（混） |
| N1级词汇 | 221 | 0 |
| N1级语法 | 202 | 0 |
| 新完全掌握N2级汉字 | 254 | **180 × 251**，0 × 3（混） |
| 新完全掌握N2级词汇 | 251 | **180 × 251** |

注意有两本是**混的**，所以要逐页判断，不能按书设一个全局参数。

自查一本书的朝向：

```powershell
..\.venv-ocr\Scripts\python.exe -c "import pymupdf,collections;d=pymupdf.open(r'..\dist\某本书.pdf');print(collections.Counter(d[i].rotation for i in range(d.page_count)))"
```
