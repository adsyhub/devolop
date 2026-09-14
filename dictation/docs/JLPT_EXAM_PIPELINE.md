# JLPT 试卷真题制作流水线与操作指南

本指南详细说明如何将一套 JLPT 真题（扫描版 PDF + 卷末答案）制作成可在听写/题库系统（`/exam.html`）中运行的高质量 `exam.json` 试卷。

```text
真题 PDF ──► 1. render 渲染切片 ──► 2. 逐页转写 pages/pNN.json + 答案 answer-key.txt
         ──► 3. assemble 自动拼装 ──► 4. validate 质量审计门闸 ──► 5. exam.json
```

- **制作入口**：[`src/exam_import.py`](../src/exam_import.py)
- **数据结构与审计规则**：[`src/exam_schema.py`](../src/exam_schema.py)
- **渲染器实现**：[`src/web/exam_markup.js`](../src/web/exam_markup.js)
- **参考范例**：[`exams/2022-07-N1/`](../exams/2022-07-N1/)

---

## 1. 为什么需要这套制作流水线？

市面上流通的真题 PDF 大多是去水印的扫描件，**内嵌字体子集没有任何可用的 `ToUnicode` 映射表**：
- 使用 `pdftotext` 抽取 34 页 PDF 通常只能得到约 3000 个乱码字符，日文字符几乎全丢；
- 使用 PyMuPDF 等工具抽取出的字符码位带有不可预知的偏移量；
- 若直接把整份 PDF 丢给大模型提取完整试卷，极易发生**漏题、题号错位、清浊音混淆（`は/ば/ぱ`、`つ/っ`）、长文跨页截断损坏**。

为了解决以上问题，本项目设计了**三阶段分离流水线**：
1. **机械切片（`render`）**：自动将 PDF 每页渲染为全局版面图与 3 张高分辨率重叠横条图，消除模型对假名细节的辨识盲区；
2. **结构化转写（`pages/*.json` + `answer-key.txt`）**：由人或多模态大模型逐页独立转写，每页单独记录疑难点（`issues`）；
3. **确定性拼装与审计（`assemble` + `validate`）**：由程序严格执行跨页缝合、阅读题与短文关联、答案按题号/位置挂载，并在题目与答案数量不一致时**强制报错终止（Fail-Closed）**。

> [!IMPORTANT]
> **零容忍与 Fail-Closed 原则**
> 答案表抄错一位或漏转写一页，会导致后续题目答案全部串位。学习者在刷题时无法察觉答案错误，会把错答案当真答案背诵。
> 因此，`assemble` 与 `audit_exam` 绝不进行“容错猜测”；审计有任何 `error` 的试卷在后端直接拒绝提供服务（HTTP 422）。

---

## 2. 目录规范与文件清单

每套真题在 `exams/` 下建立一个独立的文件夹，命名格式推荐为 `<年>-<月>-<级别>`（例如 `2022-07-N1`）：

```text
exams/2022-07-N1/
├── exam-meta.json       # 试卷元信息（标题、级别、考试年份、时长、PDF 哈希与版权声明）
├── answer-key.txt       # 照抄卷末答案表（文本格式，带题号范围、分值、排序校验）
├── pages/               # 逐页转写事实来源（每页一个 JSON，人与模型唯一维护的文件）
│   ├── p01.json
│   ├── p02.json
│   └── ...
└── exam.json            # 最终生成的试卷文件（由 assemble 生成，严禁直接手改）
```

### 为什么保留 `pages/` 而不是直接手改 `exam.json`？
`exam.json` 是编译生成物。题目 ID（如 `q_3a8b...`）和文章 ID（如 `p_f4c1...`）是由内容哈希派生且绝对稳定的。
如果发现试卷中有错别字，应当修改对应的 `pages/pNN.json`，然后重新执行 `assemble`。这样可以确保修改单道题的错字**不会破坏学习者在其他题目上的刷题进度、笔记与错题本记录**。

---

## 3. 详细制作执行流程（分步指南）

### 步骤 0：准备制作环境与依赖

日常刷题只依赖 Python 标准库，但**制作新试卷**需要图像渲染依赖：

```powershell
python -m pip install pymupdf pillow
```

---

### 步骤 1：PDF 图像切片（`render`）

将真题扫描件放置于工作目录（如 `dist/` 或临时目录），运行切片命令：

```powershell
python src\exam_import.py render --pdf "dist\n1 2022.07真题.pdf" --out .\exam-work\2022-07-N1\pages
```

**切片产物说明**：
- `pNN.png`：整页预览图（150 dpi），用于全局版面定位、确定大题与题号归属；
- `pNN_a.png`（顶部 0%~40%）、`pNN_b.png`（中部 34%~72%）、`pNN_c.png`（底部 66%~100%）：三张 260 dpi 重叠横条图。
  - **为什么需要横条图**：A4 页面在整页缩放下，日文的清音、浊音、半浊音（`は/ば/ぱ`）以及促音（`つ/っ`）极易失真。重叠横条图将文本有效放大 3 倍，且上下重叠 6%~8%，确保接缝处的文字不丢失。

---

### 步骤 2：编写试卷元数据（`exam-meta.json`）

在试卷目录下创建 `exam-meta.json`：

```json
{
  "level": "N1",
  "title": "2022年7月 日本語能力試験 N1",
  "sessionLabel": "2022年7月",
  "uiLanguage": "zh-Hans",
  "durationSec": 10800,
  "source": {
    "kind": "pdf-scan",
    "fileName": "2022年7月N1真题完整版.pdf",
    "sha256": "5fd5fa261f883340adc5b67ffc9c00d40c1ab51f18eda6928ac546ea45c84176",
    "pageCount": 34,
    "contentPages": "2-33 (questions), 34 (answer key)",
    "importedOn": "2026-08-31",
    "importer": "src/exam_import.py",
    "rights": "Personal study copy supplied by the user. The JLPT paper is copyright JEES/Japan Foundation; this exam.json is not cleared for redistribution or sale."
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `level` | string | `N1` / `N2` / `N3` / `N4` / `N5` |
| `title` | string | 试卷完整显示标题 |
| `sessionLabel` | string | 考试批次（如 `2022年7月`） |
| `durationSec` | number | 模考总倒计时秒数（N1 通常为 10800 秒 / 180 分钟） |
| `source` | object | 记录来源 PDF 的文件名、SHA256、页数及个人学习版权说明 |

---

### 步骤 3：编写卷末答案表（`answer-key.txt`）

`answer-key.txt` 采用纯文本格式，**严格照抄真题最后一页的答案与计分表格**，每一行对应表格的一格，便于人工肉眼核对：

```text
# 2022年7月 日本語能力試験 N1 — 答案
note 此处给出的计分准则仅限参考，实际考试采用尺度得点方式。答案非标准答案，仅供参考。

# ---- 第一部分 言語知識（文字・語彙・文法） ----
written   1-6     1   133424
written   7-13    1   4221133
written   14-19   1   424331
written   20-25   1   231214
written   26-35   2   2314123422
written   36-40   2   41324
written   41-44   1   3211

# 排序题选项排列顺序（4个片段的完整顺序，用于与第3空 ★ 的答案交叉验证）
order     36      3241
order     37      2413
order     38      4231
order     39      3124
order     40      1342

# ---- 第二部分 読解 ----
written   45-48   2   3143
written   49-57   2   331322144
written   58-60   3   143
written   61-62   3   23
written   63-66   3   4124
written   67-68   2   12

# ---- 第三部分 聴解 ----
# 听力答案按顺序每题一位数字（位置绑定）
listening 1       1   321232
listening 2       1   2322313
listening 3       2   441413
listening 4       2   3312233111312
listening 5       3   421
```

#### 指令格式说明：
1. `written <起始题号>-<结束题号> <分值/题> <连续答案数字>`
   - 例：`written 1-6 1 133424` 表示 1~6 题每题 1 分，答案依次为 1, 3, 3, 4, 2, 4。
2. `order <题号> <1-4的排列顺序>`
   - 例：`order 36 3241`。
   - **自动校验规则**：JLPT 排序题的星号 `★` **固定位于第 3 个空位**。因此，`order` 第 3 位数字（如 `4`）必须与上面 `written 36` 的答案数字严格相等，否则组装时自动报错拦截。
3. `listening <大题号> <分值/题> <连续答案数字>`
   - 听力题每道大题重新从 1 开始编号，且問題5 会出现一个听力材料拆成 質問1、質問2 的情况（如 1番 1 题 + 2番 2 题 = 3 个答案 `421`），因此听力答案采用**位置顺序绑定**。
4. `note <说明文本>`
   - 记录计分参考说明，该说明会随试卷下发并在成绩报告中展示。

---

### 步骤 4：逐页转写（`pages/pNN.json`）

为 PDF 的每一页编写一个对应的 `pNN.json`（例如第 2 页对应 `p02.json`）。

#### 页面根结构：
```json
{
  "page": 2,
  "pageLabel": "第1页",
  "sectionHeader": null,
  "blocks": [ ... ],
  "issues": [
    "Q3 stem: the long vowel mark in チーム is printed as a short hyphen (チ-ム); transcribed as チーム."
  ]
}
```

#### `blocks` 块类型完全速查表：

| `kind` | 作用 | 必备字段 | 可选字段 |
|---|---|---|---|
| `part-instruction` | 开启一个大题（如「問題1 …」） | `partNumber`, `text` | `vertical` |
| `passage` | 阅读正文、A/B 对比篇章、案内宣传单 | `text` | `label`, `vertical`, `continuesFromPreviousPage`, `continuesOnNextPage` |
| `note` | 篇章词汇注释（如 `（注1）…`），**自动挂载到前序短文** | `text` | `label` |
| `question` | 单道小题 | `text` (题干), `choices` | `questionNumber`, `label`, `choiceCount`, `vertical`, `continuesFromPreviousPage`, `continuesOnNextPage` |
| `figure` | 无法用文字表达的插图说明（挂载到前序题目或篇章） | `text` | 无 |
| `section-header` | 切换大模块（如「第三部分　聴解」） | `text` | 无 |

---

## 4. 特殊题型转写标准与规范

### 4.1 文本标记规则（Text Markup）

所有文本（题干、短文、选项）均为纯 UTF-8 文本，支持以下 6 种特殊排版标记：

| 标记写法 | 显示效果 | 使用场景 |
|---|---|---|
| `<u>勇敢</u>` | <u>勇敢</u>（下划线） | **漢字読み（問題1）** 与 **言い換え類義（問題3）** 划线单词 |
| `｜漢字《かんじ》` | 带振假名注音（Ruby） | 试卷原文印刷的假名注音。**注意：前缀必须是全角竖线 `｜`（U+FF5C）** |
| `【41】` | 方框题号 | **文章の文法（問題7）** 完形填空中的框内题号 |
| `＿＿★＿＿` 或 `★` | 带星号的填空位 | **文の組み立て（問題6）** 排序题 |
| `\| a \| b \|`<br>`\| --- \| --- \|` | 格式化表格 | **情報検索（問題13）** 的宣传单、价目表 |
| `> 提示内容` | 引用/边框提示框 | 宣传单底部的注意事项框 |

> [!WARNING]
> 1. **振假名竖线必须全角**：表格使用半角 `|` 作为单元格分隔符，振假名若使用半角 `|` 会导致表格解析彻底崩溃。
> 2. **标签必须成对闭合**：`<u>` 必须对应 `</u>`，`《》` 必须闭合，缺少闭合标签会被审计直接拦截。
> 3. **严禁混入任何 HTML 标签**：除 `<u>` 外，严禁输入 `<script>`、`<span>`、`<br>` 等 HTML 标签。

---

### 4.2 各种题型转写示例

#### ① 文字・词汇题（問題1 - 問題4）
```json
{
  "kind": "question",
  "partNumber": 1,
  "questionNumber": 1,
  "text": "<u>勇敢</u>に戦う主人公に子どもたちは夢中だ。",
  "choices": [
    "ゆうかん",
    "ゆうがん",
    "ゆうけん",
    "ゆうげん"
  ]
}
```

#### ② 排序题（問題6）
```json
{
  "kind": "question",
  "partNumber": 6,
  "questionNumber": 36,
  "text": "「私が30年間歌手を続けてこられたのは、ファンの方の支えがあったからです。＿＿＿＿、＿＿＿＿、＿＿★＿＿、＿＿＿＿歌い続けたいと思っています。」",
  "choices": [
    "限り",
    "ファンの皆さんが",
    "応援してくれる",
    "いる"
  ]
}
```

#### ③ 文章语法（問題7 完形填空）
- **特点**：短文在一页，4 道题的选项在下一页。题目在卷面上没有题干，只有方框题号。
- **前一页（短文页）**：
  ```json
  {
    "kind": "passage",
    "partNumber": 7,
    "text": "立場が人をつくる。…【41】に行って驚くのは、二歳児の姿です。…"
  }
  ```
- **后一页（选项页）**：
  ```json
  {
    "kind": "question",
    "partNumber": 7,
    "questionNumber": 41,
    "text": "",
    "choices": ["保育園", "ある保育園", "そうした保育園", "それ以外の保育園"],
    "continuesFromPreviousPage": true
  }
  ```
  *(注：`assemble` 遇到 prompt 为空的完形填空题，会自动将其填充为 `【41】` 并关联该短文)*

#### ④ 短文/中文/长文阅读（問題8 - 問題12）
- 若一段短文配多道题，写一个 `passage` 块，紧随其后写多个 `question` 块：
  ```json
  {
    "kind": "passage",
    "partNumber": 9,
    "label": "(1)",
    "text": "こちらは文章の本文です……"
  },
  {
    "kind": "note",
    "partNumber": 9,
    "text": "（注1）単語：ことばの意味"
  },
  {
    "kind": "question",
    "partNumber": 9,
    "questionNumber": 49,
    "text": "筆者はどのように考えているか。",
    "choices": ["...", "...", "...", "..."]
  }
  ```

#### ⑤ 跨页长文处理（Passage Across Pages）
- **前一页末尾**：
  ```json
  {
    "kind": "passage",
    "partNumber": 10,
    "text": "文章前半部分内容，句子未完",
    "continuesOnNextPage": true
  }
  ```
- **后一页开头**：
  ```json
  {
    "kind": "passage",
    "partNumber": 10,
    "text": "结在后半部分，继续讲述……",
    "continuesFromPreviousPage": true
  }
  ```
  *(注：`assemble` 缝合跨页短文时**中间不加任何空格或换行**，实现句中无缝拼接)*

#### ⑥ 信息检索（問題13 宣传单表格）
```json
{
  "kind": "passage",
  "partNumber": 13,
  "label": "案内",
  "text": "2022年度 外部講座受講料補助について\n\n|  | 一つの講座の受講料 | 補助金額 |\n| --- | --- | --- |\n| A | 30,000円以上 | 25,000円 |\n| B | 30,000円未満 | 10,000円 |\n\n> 提出締め切り：2023年2月15日"
}
```

#### ⑦ 听力题（聴解 問題1 - 問題5）
真题 PDF 仅印有听力选项或空白答题栏，题干与录音由听力音频播放：
- **開啟听力部分**：在第 25 页等听力起始页添加 `section-header`：
  ```json
  {
    "kind": "section-header",
    "text": "第三部分　聴解"
  }
  ```
- **問題1 / 問題2（有印刷选项）**：
  ```json
  {
    "kind": "question",
    "partNumber": 1,
    "label": "1番",
    "text": "",
    "questionNumber": 1,
    "choices": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"]
  }
  ```
  *(若包含试卷自带的「例題/例」，设置 `label: "例"`，不设置 `questionNumber`，程序会自动标记为不计分例题)*
- **問題3 / 問題4（无印刷选项，卷面空白）**：
  ```json
  {
    "kind": "question",
    "partNumber": 4,
    "label": "1番",
    "text": "",
    "questionNumber": 1,
    "choices": [],
    "choiceCount": 3
  }
  ```
  > [!IMPORTANT]
  > **聴解 問題4 是三选一！**
  > 問題4（即時応答）题干要求「1から3の中から選んでください」，必须显式声明 `"choiceCount": 3`，页面只渲染 3 个选项按钮。
- **問題5（综合理解）**：
  1番 为纯听力单题；2番 分为 質問1 和 質問2，转写为两个独立题：
  ```json
  {
    "kind": "question",
    "partNumber": 5,
    "label": "2番 質問1",
    "text": "質問1",
    "questionNumber": 2,
    "choices": ["1番の部屋", "2番の部屋", "3番の部屋", "4番の部屋"]
  },
  {
    "kind": "question",
    "partNumber": 5,
    "label": "2番 質問2",
    "text": "質問2",
    "questionNumber": 3,
    "choices": ["1番の部屋", "2番の部屋", "3番の部屋", "4番の部屋"]
  }
  ```

---

### 步骤 5：组装试卷（`assemble`）

编写完成所有 `pages/pNN.json` 与 `answer-key.txt`、`exam-meta.json` 后，执行组装：

```powershell
python src\exam_import.py assemble `
  --pages exams\2022-07-N1\pages `
  --key   exams\2022-07-N1\answer-key.txt `
  --meta  exams\2022-07-N1\exam-meta.json `
  --out   exams\2022-07-N1\exam.json
```

**组装器会自动完成**：
1. 校验每页 JSON 格式与大题归属；
2. 跨页短文（`passage`）与跨页选项（`choices`）自动缝合；
3. 将每道小题正确绑定到其对应的篇章 ID（`passageIds`）；
4. 完形填空题自动补充 `【41】` 等方框 Prompt；
5. 解析 `answer-key.txt` 并将答案与分值精确注入每一道题；
6. 生成确定性稳定 ID（`examId`, `passageId`, `questionId`）；
7. 计算整卷与各大题总分、题目总数及内容指纹（`contentRevision`）；
8. 运行 `audit_exam`，只有 **0 errors** 时才会将 `exam.json` 写入磁盘。

> [!TIP]
> 如果组装报错中止，请根据控制台输出定位是哪一页或哪一道题出现问题。若仅为了调试检查中间状态，可临时加上 `--allow-failed-audit` 参数生成文件，但**严禁将未通过审计的文件用于发布**。

---

### 步骤 6：核对与测试验证（`validate` & `test`）

#### 1. 独立审计核验
```powershell
python src\exam_import.py validate --exam exams\2022-07-N1\exam.json
```
控制台应输出：
```text
  status   : passed
  questions: 105
  errors   : 0   warnings: 0
```

#### 2. 运行题库自动化测试套件
```powershell
python run_tests.py exam
```
确保包含导入、审计、计分、API 及渲染器的所有测试全部通过（通过数通常为 40+ 项测试）。

#### 3. 本地启动真题演练
```powershell
python start_dictation.py
```
在浏览器中打开控制台输出的题库地址（`http://127.0.0.1:4173/exam.html`）：
- 检查试卷列表是否正常显示该套试卷；
- 进入「逐题练习」，随意答题测试反馈与解析展示；
- 进入「计时模考」，交卷测试计分报告与各 Section 得分分布；
- 检查错题本是否正常沉淀做错的题目。

---

## 5. 多模态大模型（Vision LLM）辅助转写实战指南

利用 Claude 3.7 Sonnet、GPT-4o 或 Gemini 2.5 Pro 等多模态大模型转写页面，可大幅提升制作效率。

### 推荐工作流：
1. 先运行 `render` 命令生成每页的 `pNN.png` 及 `pNN_a/b/c.png`；
2. 每次向模型提供：**1 张整页图（用于全局结构） + 1~3 张高分辨率切片横条图（用于字形确认）**；
3. 设定以下系统提示词（System Prompt）。

### 🤖 LLM 逐页转写 System Prompt 模板

````markdown
You are an expert Japanese exam transcriber specializing in JLPT papers.
Your task is to transcribe scanned JLPT exam pages into precise JSON format adhering to the project schema.

## Output JSON Schema for single page:
```json
{
  "page": <integer: PDF page number>,
  "pageLabel": "<string: the printed page label at footer, e.g. 第1页>",
  "sectionHeader": "<string or null: e.g. 第三部分　聴解>",
  "blocks": [
    {
      "kind": "part-instruction" | "passage" | "note" | "question" | "figure" | "section-header",
      "partNumber": <integer or null: e.g. 1 for 問題1>,
      "label": <string or null: e.g. (1), A, 1番, 例>,
      "text": "<string: prompt text or passage body>",
      "questionNumber": <integer or null: the printed question number e.g. 1>,
      "choices": ["choice 1", "choice 2", "choice 3", "choice 4"] | null,
      "choiceCount": 4, // 3 for 聴解 問題4
      "vertical": false,
      "continuesFromPreviousPage": false,
      "continuesOnNextPage": false
    }
  ],
  "issues": [
    "<string: describe any ambiguous glyph, scan defect, or layout quirk observed>"
  ]
}
```

## Critical Rules:
1. Underlines: For 問題1 (漢字読み) and 問題3 (言い換え類義), enclose the underlined word in `<u>...</u>`, e.g. `<u>勇敢</u>に戦う`.
2. Furigana / Ruby: Printed furigana MUST use full-width bar `｜` (U+FF5C) and `《》`, e.g. `｜釘《くぎ》`. Never use ASCII `|`.
3. Cloze questions (問題7): The cloze passage has `【41】` in text. The choices on next page have empty `text: ""` and `questionNumber: 41`.
4. Sentence ordering (問題6): Star blank should be written as `＿＿★＿＿`.
5. Listening (聴解):
   - 問題1/2: `text` is empty `""`, `label` is `"1番"`, `choices` contains the 4 printed choices.
   - 問題3: `choices: []`.
   - 問題4: `choices: []`, `choiceCount: 3`.
   - 問題5: 1番 has `choices: []`; 2番 is split into two question blocks with label `"2番 質問1"` and `"2番 質問2"`.
6. Tables & Callouts: In 問題13 leaflets, format tables as Markdown pipe tables (`| A | 30,000円 |`) and callout boxes with `> `.
7. Accuracy: Verify small kana (っ/つ) and diacritics (ば/ぱ/は) using high-resolution crop bands. Report any doubts in `issues`.
8. ONLY output valid, raw JSON. No markdown codefence wrapping if possible, or standard json codeblock.
````

---

## 6. 常见审计错误与排错速查表（Troubleshooting）

| 审计错误代码（Issue Code） | 产生原因 | 修复方法 |
|---|---|---|
| `exam.numbering_gap` | 笔试题号中间出现断层（如从 12 直接跳到 15） | 漏转写了某页，或某道题的 `questionNumber` 抄错。 |
| `question.underline_missing` | 問題1 或 問題3 题目中没有包含 `<u>...</u>` | 补全题干划线词的 `<u>...</u>` 标记。 |
| `question.underline_unbalanced` | `<u>` 与 `</u>` 数量不匹配 | 检查是否有未闭合的 `<u>` 标签。 |
| `question.ruby_unbalanced` | 振假名 `《` 与 `》` 数量不匹配 | 检查振假名标记，确保格式为 `｜漢字《かんじ》`。 |
| `question.stray_markup` | 文本中出现了除了 `<u>` 以外的 HTML 标签（如 `<br>`） | 删除多余 HTML 标签，换行直接使用 `\n`。 |
| `question.choice_count` | 选项数量与 `choiceCount` 声明不符（默认应为 4 个） | 检查选项数组是否漏项或多项；跨页选项需设置 `continuesOnNextPage`。 |
| `question.spoken_choices_present` | 听力无印刷题声明了空选项，但填入了文字 | 检查是否把听力录音文本误填入了 `choices`。 |
| `question.order_answer_mismatch` | 排序题 `order` 行的第 3 位与 `written` 答案不一致 | 核对扫描件，确认 `order` 四个选项顺序与卷末答案是否抄错。 |
| `question.order_invalid` | 排序题 `order` 不是 1~4 的排列（如出现了重复数字） | 修正 `answer-key.txt` 中的 `order` 序号排列。 |
| `listening count mismatch` | 听力大题的答案位数与转写的小题总数不相等 | 核对该大题在试卷中包含的小题数，排查是否有漏写或多写的 `question` 块。 |
| `answer for question ... no page contains` | 答案表中包含了页面上不存在的题号 | 通常是某页未被转写，或题号范围（如 `1-6`）写多。 |

---

## 7. 支持新级别（N2 / N3 等）的扩展说明

目前 `src/exam_import.py` 内置了 `N1` 的大题题型与小题结构定义。若制作 **N2 / N3** 真题：
1. 打开 [`src/exam_import.py`](../src/exam_import.py)；
2. 在 `JLPT_STRUCTURE` 字典中添加对应级别的配置：

```python
JLPT_STRUCTURE: dict[str, list[dict[str, Any]]] = {
    "N1": [ ... ],
    "N2": [
        {
            "id": "s1",
            "kind": "language-knowledge",
            "title": "言語知識（文字・語彙・文法）",
            "localTitle": "第一部分　语言知识（文字・词汇・语法）",
            "parts": {
                1: "kanji-reading",
                2: "orthography",           # N2 包含漢字表記
                3: "word-formation",        # N2 包含語形成
                4: "context-vocabulary",
                5: "paraphrase",
                6: "usage",
                7: "grammar-form",
                8: "sentence-composition",
                9: "text-grammar",
            },
        },
        # ... 配置第二部分 reading 与第三部分 listening
    ],
}
```
配置完成后即可无缝执行全部导入与组装流程。

