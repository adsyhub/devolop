# 词汇与语法模块设计方案

在精听（`courses/`）和 JLPT 真题（`exams/`）之外增加第三类内容：**按 JLPT 级别组织的
词条与语法条目**，支持查词、浏览和背诵。内容来源是 OCR 提取的 PDF 教材，词典层来源是
开放词典数据。

本文是实施方案，不是已完成状态的说明。落地后按惯例拆成使用说明与
`docs/LEXICON_PIPELINE.md`（制作流水线），并在 `PROJECT_STRUCTURE.md` 增加第 17 节。

> **当前生效的契约以 ADR 为准。** 复习目标（`reviewTarget`）与题目/答案版本的分离、
> `review_version` 乐观并发、审核四态与出题资格、删除墓碑与恢复语义、以及浏览器
> 「先持久化再发送」，均由 [ADR.md](ADR.md) 的 **ADR-LEX-007** 与 **ADR-LEX-008** 定义，落地情况见
> [词汇语法模块-验收记录](词汇语法模块-验收记录.md)。本文与之冲突处以 ADR 为准。
> 尚未实施的剩余工作见
> [词汇语法模块未完成项详细实现文档](词汇语法模块未完成项详细实现文档.md)。

---

## 0. 三个核心判断

方案的全部结构由这三条推出，其余都是细节。

### 判断一：词和语法是同一种内容，不是两个模块

一个词条是「見出し語 + 読み + 词性 + 释义 + 例句 + 级别 + 出处」，一个语法条目是
「文型 + 接続 + 释义 + 例句 + 级别 + 出处」。差异只有两个字段（`読み/品詞` 对
`接続`），共同点是全部：稳定 ID、级别分组、多语种释义、例句、来源追溯、搜索索引、
SRS 调度、离线缓存、审计规则。

所以只做**一套** schema / store / API / 页面，用 `kind: "word" | "grammar"` 区分，
kind 专属字段挂在 `word` / `grammar` 子对象里。这和 `exam_schema.py` 用
`exam → section → part → question` 一个文件描述三层嵌套是同一个取舍。

做成两个模块的代价不是多写一遍代码，是**多一套要各自维护的边界**：两条彼此独立的导入管线、两条
离线缓存策略、两个「今天该复习多少」的口径。第三个尤其糟——学习者不需要知道自己欠了
40 个词和 12 条语法，他需要知道今天要复习 52 条。

### 判断二：不同字段必须由不同来源负责，不能把 OCR 当作词典

[docs/PDF_OCR.md](PDF_OCR.md) 已经实测记录了这件事：默认分辨率下振り仮名字高只有约
12 px，**模型看不清就会编读音**，而编出来的读音比不标读音更糟。要真读出来得 6.4 MP，
整本约 14 小时且爆显存。

所以词汇模块不能靠 OCR 拿读音，也不能笼统地说「所有释义都以词典为准」。内容分成两层，
每个字段明确自己的来源：

| 层 | 来源 | 提供什么 | 可否再分发 |
|---|---|---|---|
| **词典层** `assets/dictionary/` | JMdict / KANJIDIC2（EDRDG；当前主许可为 CC BY-SA 4.0，KANJIDIC 部分字段另有条件） | 表記、読み、品詞、活用类别、英文词典义项、经许可核对后纳入的汉字信息 | **有条件可以**，须保留署名、ShareAlike 与字段级许可信息 |
| **内容包层** `lexicon/<slug>/` | OCR 的教材 | 级别归属、教材编排顺序、中文/韩文释义、例句、语法接続、近义辨析 | **不可以**（见第 8 节） |

于是 OCR 管线的任务从「识别读音」变成「**把教材里的见出し語解析成候选，再由词典与人工
裁决确定具体表記、読み和义项**」。匹配不是二值的：同形词、多读音、多义项和旧字体都可能
让一个见出し語命中多个 `entSeq`。流水线必须保留 `matched / ambiguous / unmatched /
manually-resolved` 四种状态；`ambiguous` 和 `unmatched` 都是 fail-closed 信号，未解决前不得
下发词汇包。人工决定写进独立的 `match-resolutions.json`，重跑时不得丢失。

语法条目没有对应的开放数据源，只能来自教材，因此**语法包整体不可再分发**，这是既定
事实而不是选择。

### 判断三：复习基础设施已经存在，但调度语义必须先修正

`src/local_backend.py` 里已经有：

- `vocab` 表，带 `srs_stage / srs_interval / srs_ease / srs_repetitions / srs_lapses /
  next_review_at / last_reviewed_at / mastered / level / tags`
  （[local_backend.py:125](../src/local_backend.py#L125)）
- `calculate_sm2()` 的 SM-2 风格四档调度（[local_backend.py:341](../src/local_backend.py#L341)）
- `grade_vocab_review()` 加 `vocab_review_receipts` 表做写入幂等
- `src/web/learning_data.js` 的离线 outbox、删除墓碑与顺序重放

但现状不能原样当作长期 SRS：调度器进入 `srs_stage = 3` 后会自动写 `mastered = 1`
（[local_backend.py:590](../src/local_backend.py#L590)），而 `/api/review/due` 又排除 `mastered`
（[local_backend.py:428](../src/local_backend.py#L428)），成熟卡因此永远不会再次到期。`app.js`
还保留了一份客户端算法（[app.js:542](../src/web/app.js#L542)），和 Python 实现缺少跨语言
一致性测试。

本模块复用的是**表、回执、outbox 与四档交互**，不是把现有语义视为已经冻结。Phase C 前
必须完成以下兼容迁移：

- `srs_stage = 3` 改称「成熟」，仍按 `next_review_at` 进入复习队列；
- 新增 `review_suspended` 表示学习者主动移出复习，调度器不得自动改它。迁移前先备份；
  `mastered = 1 AND last_reviewed_at = ''` 可判为人工操作，回填暂停；有复习时间的行无法区分
  自动成熟和复习后人工勾选，产品决策是恢复按 `next_review_at` 到期，同时把 ID 写入迁移报告，
  在个人中心提供一次性批量重新暂停。不能把旧 `mastered` 全量回填为暂停，否则只是换了字段名，
  自动成熟卡仍会永久消失；
- 旧 `mastered` 在兼容期只作为 `srs_stage = 3` 的派生展示值，不再参与 due 查询，也不得与
  `review_suspended` 同步；原「掌握」复选框改名为「暂停复习」，批量
  `mark_mastered / mark_unmastered` 兼容动作只切换暂停状态，不再篡改 SRS stage；
- `grade` 只接受 `again / hard / good / easy`，其他值返回 400，不做隐式状态更新；
- Python 与浏览器各保留一份纯函数 `schedule(state, grade, reviewed_at_utc)`，不得在函数内部读取
  系统时钟；两端共用一组固定时间的 JSON 测试向量，保证所有边界值完全一致。

背单词模块要做的不是另写一套队列，而是把新卡片接入修正后的同一调度契约。词和语法进入
同一张卡片表、同一个到期口径；导入与渲染仍通过 `kind` 的 tagged union 保留各自边界。

---

## 1. 数据分三层

```
词典层（共享、可分发、大）
  assets/dictionary/jmdict.sqlite3       見出し語 / 読み / 品詞 / 英文释义 / FTS5 索引
  assets/dictionary/kanjidic.sqlite3     汉字：音训读、部首、笔画
  assets/dictionary/SOURCES.md           来源、下载日期、原文件哈希、许可版本、署名与字段白名单
        ↑ 按 entSeq 引用
内容包层（一本书一个包，不可分发）
  lexicon/N2-grammar-soumatome/
    pack.json          ← 生成物，服务端实际读的东西
    pack-meta.json     ← 书名、ISBN、级别、kind、出处与授权声明（人写）
    units.txt          ← 教材目次（第N週/N日目 + 条目数），fail-closed 的对照基准（人抄）
    pages/p0038.json   ← 逐页结构化抽取，可人工编辑，重跑 assemble 不丢
    entry-keys.json    ← 条目不可变身份注册表，不含教材正文，进入版本库
    match-resolutions.json ← sourceAnchor → entSeq/表記/読み/义项，人工裁决，本地保留
    match-report.json  ← matched / ambiguous / unmatched 报告，生成物，不进入版本库
    source.pdf.sha256  ← 原始 PDF 指纹，不存 PDF 本身
        ↑ 按 entryId 引用
学习者层（learning.sqlite3，已存在）
  vocab            卡片 + 四档 SRS 状态 + 可离线渲染的卡片快照
  lex_decks        学习计划：练哪个包/级别、每日新卡数、顺序
  lex_deck_cards   计划与候选卡的多对多关系、顺序、投放状态
  lex_daily_batches 某学习日实际投放的卡，保证重复调用返回同一批
```

**为什么内容包不内嵌完整词典记录**：一个 N2 词汇包约 2000 词，整条抄进去意味着同一个
「見出し語＋読み」在 N1/N2/N3 三个包里各存一份，词典修订时三份不一致，而学习者看到的
是哪一份取决于他从哪个包点进去。引用则只有一份。代价是包在没有词典层时无法提供完整
义项、反查和全量搜索，但基础浏览与背诵仍可走下面的快照降级路径。

**为什么内容包又保留 `snapshot` 字段**：`pack.json` 里每个词条额外冗余一份
`snapshot: {reading, pos, glossEn}`。这不是重复存储，是**降级路径**：词典文件缺失或
版本对不上时，包仍可显示和背诵，只是查不了完整义项。审计会给出 `dictionaryMissing`
提示，但**不拒绝基础浏览和背诵**；需要完整词典的操作明确禁用并说明原因。snapshot 仍是
词典派生数据，必须保留字段来源、许可版本和 ShareAlike 信息，不能因字段少就当成教材自有内容。

**为什么不用单一游标记录投放进度**：包修订可能插入、删除或重排条目，一个整数 cursor 会
静默跳过新条目或重复投放旧条目。`lex_deck_cards` 按稳定 `source_ref + prompt_type +
variant_key` 记录每张候选卡是否已投放；重排只改 `ordinal`，不会改历史。`lex_daily_batches`
记录实际投放结果，`serve` 在同一学习日重复调用时直接返回原批次。

---

## 2. 新增文件清单

仿 `PROJECT_STRUCTURE.md` 13.1 的写法。

| 路径 | 用途 |
|---|---|
| `src/lexicon_schema.py` | 条目数据结构、稳定 ID、`prepare_pack` / `audit_pack`（对应 `exam_schema.py`） |
| `src/lexicon_import.py` | OCR 产物 → `pack.json`，三个子命令 `extract` / `assemble` / `validate`；保留身份与匹配裁决 |
| `src/lexicon_store.py` | `LexiconStore`（读盘与搜索）、`DeckStore`（计划与卡片投放）、`LexiconApiMixin`（`/api/lexicon*`、`/api/decks*` 路由） |
| `src/dictionary_build.py` | JMdict / KANJIDIC2 XML → SQLite + FTS5，含许可信息落盘 |
| `src/jp_inflection.py` | 去活用候选与变换链：`食べました → 食べる`，只在服务端，结果必须经词典验证 |
| `src/distribution_policy.py` | 通用发布边界：教材包拒绝进入发布候选，开放词典校验署名与字段许可 |
| `src/web/lexicon.html` | 词汇语法工作区（查词 / 浏览 / 背诵三个视图） |
| `src/web/lexicon.css` | 复用 `app.css` 设计变量，同 `exam.css` |
| `src/web/lexicon.js` | 工作区编排 |
| `src/web/lexicon_markup.js` | 条目文本 → DOM 渲染器，单独拆出以便单测（对应 `exam_markup.js`） |
| `src/web/lookup_panel.js` | 划词查询浮层，挂载在精听、真题、词汇三个页面 |
| `src/web/srs_scheduler.js` | 浏览器侧纯调度函数，供精听、个人中心与词汇页共用；与 Python 共用测试向量 |
| `src/web/learning_store.js` | IndexedDB 个人卡片快照仓库；outbox/墓碑仍由 `learning_data.js` 保存在 localStorage |
| `lexicon/N2-grammar-soumatome/` | 第一个内容包（该教材已 OCR 完成） |
| `tests/test_lexicon_schema.py` | 审计规则、稳定 ID、级别归属 |
| `tests/test_lexicon_import.py` | 单元编号规范化、跨页条目拼接、目次数量对不上必须报错 |
| `tests/test_lexicon_api.py` | 接口、搜索、计划投放、内容修订、授权边界、路径穿越 |
| `tests/test_lexicon_migration.py` | 旧 `vocab` 数据迁移、成熟卡继续到期、多计划关系与卡片快照刷新 |
| `tests/test_dictionary_build.py` | XML 解析、FTS5 可用性探测与降级、许可文件必须生成 |
| `tests/test_jp_inflection.py` | 去活用规则表 |
| `tests/lexicon_markup.test.mjs` | 渲染器，含注入回归 |
| `tests/lookup_panel.test.mjs` | 划词选区解析、挂载幂等 |
| `tests/srs_scheduler.test.mjs` | 浏览器调度与共享 JSON 向量一致，未知评分拒绝 |
| `tests/fixtures/srs_cases.json` | Python 与 JavaScript 共用的调度输入/期望值，显式带固定 `reviewedAtUtc` |
| `tests/learning_store.test.mjs` | IndexedDB 升级、旧 localStorage 迁移、容量失败与事务回滚 |
| `tests/sw_lexicon_cache.test.mjs` | 词包版本缓存、断网回退、中断更新不破坏旧版本 |
| `docs/LEXICON_PIPELINE.md` | 制作流水线与执行指南 |

改动的既有文件：`src/local_backend.py`（列迁移、3 表、索引、CRUD、序列化、筛选与调度语义）、
`src/serve_course.py`（mixin 与路由映射）、`src/web/sw.js`（`SHELL_ASSETS`、缓存版本、包缓存策略）、
`src/web/home.html` 与 `home.js`（第三个入口）、`src/web/me.html` 与 `personal.js`
（生词本按包与级别筛选；卡片身份不再只看 `term + reading`）、`personal_data_tools.js`
（多朝向去重键）、`app.js`（抽出客户端调度器并改用异步个人仓库）、
`learning_data.js`（继续只排队 mutation，不承担整份卡片正文的持久化）、`start_dictation.py`（多打印一行地址）、
`src/content_license.py` 与 `src/release_readiness.py`（接入第 8 节的通用发布策略）。

---

## 3. `pack.json` 结构

```jsonc
{
  "schemaVersion": 1,
  "packId": "N2-grammar-soumatome",
  "kind": "grammar",                    // "word" | "grammar"，一包只能一种
  "level": "N2",                        // N1..N5，包级默认
  "title": "新日语能力考试考前对策 N2 文法",
  "contentRevision": "…",               // 规范化内容哈希，不含自身与瞬时审计字段
  "attribution": {
    "sourceType": "textbook-ocr",
    "publisher": "世界图书出版公司北京公司",
    "originalPublisher": "ASK Publishing Co., Ltd.",
    "isbn": "978-7-5100-2795-6",
    "sourceSha256": "…",
    "redistributable": false            // 见第 8 节：其他值直接报错，不静默改写
  },
  "dictionary": {
    "required": false,
    "name": "jmdict",
    "version": "2026-08-01",
    "fileSha256": "…"
  },
  "units": [
    { "unitId": "w1d4", "label": "第1週 4日目", "title": "かゆくてたまらない",
      "entryIds": ["g_4fbd41a629f25ee8c0a7a03b", "…"] }
  ],
  "entries": [
    {
      "id": "g_4fbd41a629f25ee8c0a7a03b", // 96-bit 稳定 ID，算法见下
      "entryKey": "e0001",              // 在 entry-keys.json 中冻结，不从正文重算
      "kind": "grammar",
      "level": "N2",
      "headword": "〜てたまらない",
      "unitId": "w1d4",
      "order": 12,                      // 教材内顺序，背诵默认按这个走
      "gloss": {
        "zh": "……得受不了",
        "en": "can hardly stand ~",
        "ko": "참을 수 없을 정도로 ~하다"
      },
      "grammar": {
        "connection": [
          {"slot": "i-adjective", "form": "くて", "display": "イAくて"},
          {"slot": "na-adjective", "form": "で", "display": "ナAで"},
          {"slot": "verb-desiderative", "form": "たくて", "display": "Vたくて"}
        ],
        "notes": "表示感情、感覚或困扰的状态",
        "confusables": [
          {"sourceRef": "lex:N2-grammar-soumatome#g_111111111111111111111111", "note": "主观感情，口语常见"},
          {"sourceRef": "lex:N2-grammar-soumatome#g_222222222222222222222222", "note": "多用于负面、难以承受"}
        ]
      },
      "examples": [
        { "exampleId": "ex1",
          "ja": "子どものことが心配でたまらない。",
          "reading": "こどものことがしんぱいでたまらない",
          "readingSource": "manual",     // "dictionary" | "manual"；缺省即没有读音
          "zh": "孩子的事，担心得不得了。",
          "en": "I am so worried about my children.",
          "paraphrase": "とても心配だ" }
      ],
      "cardTemplates": [
        { "variantKey": "cloze-ex1", "promptType": "cloze", "exampleId": "ex1",
          "markedJa": "子どものことが心配⟦でたまらない⟧。" },
        { "variantKey": "usage-ex1", "promptType": "usage", "exampleId": "ex1",
          "choiceRefs": ["self", "lex:N2-grammar-soumatome#g_111111111111111111111111",
                         "lex:N2-grammar-soumatome#g_222222222222222222222222"],
          "answerRef": "self",
          "rationales": [
            {"choiceRef": "lex:N2-grammar-soumatome#g_111111111111111111111111", "reason": "…"},
            {"choiceRef": "lex:N2-grammar-soumatome#g_222222222222222222222222", "reason": "…"}
          ] }
      ],
      "source": {
        "pdfPages": [10],                // PDF 物理页，从 1 开始
        "printedPages": [6],             // 书上印刷页码；没有则省略
        "blockIds": ["p0010-b3"]
      },
      "flags": []                        // 仅允许 warning/info；error 条目不得随包下发
    }
  ]
}
```

`contentRevision` 是 64 个十六进制字符（256 bit）的 SHA256：复制整个 pack，把
`contentRevision` 设为空串，
再按 UTF-8、对象键排序、无多余空白的项目统一 JSON 规则序列化后计算。attribution、flags、
卡片模板和内容顺序都参与哈希；独立 audit report、文件时间和本机绝对路径不进入 pack，因而
也不参与。相同内容必须在 Windows/Linux 上得到相同 revision。

词条的 kind 专属字段：

```jsonc
{
  "kind": "word",
  "headword": "承る",
  "dictRef": {
    "source": "jmdict",
    "entSeq": 1610980,
    "writtenForm": "承る",
    "reading": "うけたまわる",
    "senseIndexes": [0, 1]
  },
  "snapshot": { "reading": "うけたまわる", "pos": ["v5r", "vt"], "glossEn": ["to hear", "to accept"] },
  "word": { "writtenForms": ["承る", "うけたまわる"], "commonness": "ichi1" }
}
```

`validate` 对引用完整性 fail-closed：`packId` 用
`[A-Za-z0-9][A-Za-z0-9._-]{0,63}`，`unitId / exampleId / variantKey` 用
`[a-z][a-z0-9-]{0,63}`，`entryKey` 用 `e[0-9]{4,}`，`entryId` 用
`[wg]_[0-9a-f]{24}`，并在各自作用域内唯一。每个 `units[].entryIds` 都必须指向同包条目，教材
条目必须恰好归属一个单元；entry 的 `kind` 必须和包一致；每个模板的
`(promptType, variantKey)` 唯一且引用现存 example。`cloze` 的 `markedJa` 至少有一对平衡的
`⟦⟧`；`usage.answerRef` 必须在 choices 中，
每个错误 choice 都必须有非空 rationale；包内 sourceRef、alias 和 confusable 必须能解析。
未知字段是否接受由 `schemaVersion` 决定，不能在同一版本里静默吞掉拼错的字段名。

### 稳定 ID 怎么算

正文不是身份。OCR 会改错字，教材条目会跨页拼接，也可能在补漏后换单元顺序；把見出し語、
`unitId` 或 `order` 放进 ID 都会在普通订正时让 SRS 历史断开。

`packId` 是不可变命名空间，不等于可修改的目录 slug 或展示标题；包改名不能改 `packId`。
首次接受一个条目时，在 `entry-keys.json` 给它分配包内唯一、以后不可变的 `entryKey`。页面
块通过 `sourceAnchor` 找到这条注册记录；即使块号因重新抽取而变化，也只更新 anchor 到 key
的映射，不创建新 key。生成 ID 时只使用包身份和这个不可变 key：

```
id = kind[0] + "_" + sha256(packId + US + entryKey)[:24]
```

24 个十六进制字符是 96 bit，与项目现有题库一致。6 个十六进制字符只有 24 bit：一个
2000 词的包至少发生一次碰撞的概率约 11.23%，不可使用。`prepare_pack()` 保留已有合法 ID，
审计拒绝重复 ID、重复 entryKey 和 registry 中的悬空记录。

普通 `assemble` 遇到新 sourceAnchor 时只生成待分配报告并失败；只有显式
`assemble --accept-new-keys` 才从 registry 的单调序列分配新 key，并要求人工审查
`entry-keys.json` diff。重新抽取导致 anchor 改变时，人工把旧 key 迁到新 anchor，不能用该
开关顺手生成一批新身份。

`normalized_headword` 仍然存在，但只用于搜索、匹配和重复候选提示：做 NFKC、去波浪号变体
（`〜～~`）、规范空白。它不参与身份计算。若人工确认条目确实被拆分或合并，必须写显式
`idAliases` / retired 映射，让已有卡片可迁移，而不是依赖哈希偶然变化。

---

## 4. 导入流水线

```
PDF ──(已有)──> pdf_ocr run ──> out/<书名>/document.json
                                       │
                    lexicon_import extract  ← 可选接 text_providers 的大模型
                                       ↓
                          lexicon/<slug>/pages/p<NNNN>.json   ← 人可编辑
                                       │
                    entry-keys.json + match-resolutions.json ← 人工决定，重跑保留
                                       │
                    lexicon_import assemble ← 对照 units.txt，解析身份与词典候选
                                       ↓
                             pack.json + match-report.json
                                       │
                    lexicon_import validate  → audit 报告
```

和 `exam_import.py` 的三段式一致，理由也一致：只有中间那步需要人或模型在环，其余两步
必须机械可重复。`extract` 若接大模型，走 `src/text_providers.py`，遵守 ADR-MODEL-001：
**源码里不出现任何模型名**。

### `pages/p<NNNN>.json` 契约

```jsonc
{
  "page": 10,
  "unitHeader": { "week": 1, "day": 4, "title": "かゆくてたまらない" },
  "blocks": [
    { "id": "p0010-b3", "sourceAnchor": "pdf:10:block:3", "type": "entry",
      "headword": "〜てたまらない",
      "gloss": {"zh": "…", "en": "…", "ko": "…"},
      "connectionRaw": ["Aくて", "naで", "Vたくて"],
      "examples": [{"ja": "…", "zh": "…", "paraphrase": "…"}],
      "continuesOnNextPage": false },
    { "id": "p0010-b7", "type": "note", "text": "…" }
  ],
  "issues": [
    {"severity": "error", "code": "extract.connection_truncated",
     "message": "接続框只读到一半", "blockId": "p0010-b3"}
  ]
}
```

`type` 取值：`entry`（一个条目）、`unit-header`（週/日目标题）、`note`（补充说明）、
`exercise`（第 7 日的实战问题，本模块**不收**，那是题库的职责）、`front-matter`
（前言、目次、版权页）。

`issues` 不是随手记事。每项必须带 `severity / code / message`；`error` 未清零时该页参与的
条目不得进入 `pack.json`，`warning` 才允许随条目下发。

### 五条必须挡住的坑

**一、单元编号必须规范化。** 实测这本书的 OCR 产物里同时出现 `第1週`、`第一週`、
`第２週` 三种写法。不规范化就会把同一週拆成三个单元，而且拆得毫无规律。`extract`
阶段统一转成 `(week:int, day:int)`，无法解析的整页停下报错，不猜。

**二、目次数量对不上必须报错。** `units.txt` 是人照着书的目次抄的（第N週 N日目加该
单元条目数），`assemble` 用它对账。缺条目意味着 OCR 漏了一整块——[docs/PDF_OCR.md](PDF_OCR.md)
已经记录过「整页 OCR 会系统性丢掉浮在右侧的接続框」这种整块缺失。**背了一半的语法表，
学习者没有任何办法发现少了哪一半**，这和答案串位是同一类错误，所以按题库的规矩：报错
停下，不放宽成警告。

**三、`> ` 引用行和 `<!-- ruby: -->` 注释是数据，不是噪声。** OCR 产物里例句、译文和
接続框大量以 `> ` 开头（`boxes` 二次通道合并的结果），振り仮名被包成 HTML 注释。
`extract` 必须把它们解析进结构，而不是当 Markdown 引用块丢掉。但 **ruby 注释只作为
提示，永远不写进 `reading` 字段**——理由见判断二。`reading` 只接受 `readingSource` 为
`dictionary`（词典匹配得来）或 `manual`（人工确认）的值。

**四、OCR 的接続缩写必须结构化，不能直接当成日文。** 当前样例页实际印的是拉丁缩写
`Aくて / naで / Vたくて`，OCR 产物曾把 `naで` 识别成日文 `なで`。`extract` 保存
`connectionRaw` 供逐字核对，`assemble` 再映射成 `{slot, form, display}`；未知缩写报错，
不靠字符串替换猜。

**五、`pack.json` 是生成物，不许手改。** 同 `PROJECT_STRUCTURE.md` 维护规则 14：改错字
改 `pages/`，重跑 `assemble`。

---

## 5. 词典层

### 数据源

- **JMdict**（EDRDG；[当前主许可](https://www.edrdg.org/edrdg/licence.html)为 Creative
  Commons BY-SA 4.0）：日语为枢轴的多语词典，
  本项目首期只导入英语义项，约 20 万条，含読み、品詞、多义项、常用度标记。
- **KANJIDIC2**（EDRDG；[项目与特殊条件](https://www.edrdg.org/wiki/KANJIDIC_Project.html)）：
  约 13,108 汉字的音训读、部首、笔画。主文件沿用 EDRDG 许可，但 SKIP 等部分字段另有
  条件；首期只白名单导入本项目实际需要且已核对许可的字段。

> **每次更新数据源都必须核对**：许可的确切版本号、特殊字段条款与署名文字以 EDRDG 官网
> 当时的声明为准，抄进 `assets/dictionary/SOURCES.md`，同时记录下载 URL、日期、原文件
> SHA256、导入字段白名单和生成数据库 SHA256。`distribution_policy.py` 检查的是这些字段，
> 不只是文件「存在且非空」。
> 不要拿本文的转述当授权依据。

### 构建

`src/dictionary_build.py` 把 XML 转成 SQLite：

```sql
entries(ent_seq PK, pos_json, common INT, misc_json)
forms(ent_seq, text, kind, priority_json,
      PRIMARY KEY(ent_seq, text, kind))  -- kind: kanji | kana，一条多形
senses(ent_seq, idx, gloss_en_json, field_json, PRIMARY KEY(ent_seq, idx))
CREATE INDEX idx_forms_text ON forms(text)
entries_fts USING fts5(text, ent_seq UNINDEXED)   -- 表記 + 読み + 罗马字
```

**FTS5 可用性必须探测，不能假设。** 启动时试建一次虚拟表，失败则降级到 `forms` 上的
精确匹配、前缀索引加转义后的 `LIKE 'x%'`。查询必须限制长度、转义 `%` / `_` 与 FTS
操作符。降级路径要有测试，否则换一台机器就整个查词功能消失，而且报的是一个原始 SQL
错误。

体积预估：完整 JMdict 建完索引约 150–250 MB。这是**服务端文件**，不进浏览器缓存
（见第 7 节）。

### 去活用

划词查到的经常是活用形。`src/jp_inflection.py` 给定一个词形，返回「候选辞书形 + 变换链 +
代价」，允许有限深度的多步逆变换，覆盖ます / て / た / ない / 可能 / 受身 / 使役 /
条件 / 意向以及一段、五段、变格动词。候选必须回查 JMdict 才能成为搜索结果；纯规则产物
不得直接展示为命中。排序按精确表記、词典常用度、变换代价，而不是只按规则长度。

这套逻辑只在服务端保留一份。浏览器离线时只浏览已缓存包和已经落成卡片的辞书形，不承诺
全量去活用查询。

---

## 6. 服务端

### 存储改动（`local_backend.py`）

新增 7 列，走已有的 `_ensure_schema_columns()`；迁移不只改表结构，还必须同步修改
`create_vocab / import_vocab / update_vocab / list_vocab / _row_to_vocab`、个人中心缓存与导入导出：

| 列 | 说明 |
|---|---|
| `entry_kind TEXT NOT NULL DEFAULT 'word'` | `word` / `grammar`。表名仍叫 `vocab` 是历史负担，**不改名**——改名要动多处查询、幂等回执和已有学习者的数据库，收益只是好看 |
| `source_ref TEXT NOT NULL DEFAULT ''` | `lex:<packId>#<entryId>`、`dict:<entSeq>#<formKey>` 或空（手工添加的生词）；直接词典卡不能只用 entSeq 吞掉不同表記/読み |
| `prompt_type TEXT NOT NULL DEFAULT 'recall'` | 卡片朝向，见第 9 节 |
| `variant_key TEXT NOT NULL DEFAULT 'default'` | 同一朝向的具体模板，如 `cloze-ex1`；多例句不会互相覆盖 |
| `card_payload_json TEXT NOT NULL DEFAULT '{}'` | 可离线渲染的已校验卡片快照；限制大小与允许字段，不能存任意 HTML |
| `source_revision TEXT NOT NULL DEFAULT ''` | 生成该快照的包修订；包更新时只刷新 payload，不重置 SRS |
| `review_suspended INTEGER NOT NULL DEFAULT 0` | 学习者主动暂停；调度器不得因为卡片成熟而自动写入 |

SQLite 保持 snake_case；`_row_to_vocab()` 和 API 继续沿用项目现有 camelCase，分别输出
`entryKind / sourceRef / promptType / variantKey / cardPayload / sourceRevision / reviewSuspended`；其中
`cardPayload` 是按 schema 校验后解析出的对象，不把数据库里的 JSON 字符串原样泄漏给前端。

旧 `mastered` 列在兼容期保留，但其含义收窄为「是否达到成熟 stage」；所有服务端到期查询只看
`review_suspended = 0` 与 `next_review_at`。旧客户端动作 `mark_mastered / mark_unmastered`
分别映射到暂停 / 恢复复习，界面文案同步改名；真正重置调度只允许显式 `reset_srs`。

直接词典卡的 `formKey = sha256(NFC(writtenForm) + US + NFC(reading))[:24]`，原文表記与读音留在
payload 供显示和审计。词典更新若确实更正或删除该 form，必须输出 alias/retired 报告后迁移，
不能因为重新构建 SQLite 就静默生成一张新卡。

一个部分唯一索引，防止同一条目、同一朝向、同一模板重复入库：

```sql
CREATE UNIQUE INDEX IF NOT EXISTS vocab_source_card
  ON vocab(source_ref, prompt_type, variant_key) WHERE source_ref <> '';
```

来源卡的 `vocab.id` 同样确定性生成：

```
card_id = "v_" + sha256(source_ref + US + prompt_type + US + variant_key)[:24]
```

这样离线客户端和服务端会得到同一个 ID，丢失响应后的 outbox 重放仍然幂等。手工生词继续
使用现有 `local_*` / 随机 `v_*` ID；前端去重时，来源卡使用上述三元身份，只有无来源的手工
生词才回退到 `term + reading`。

三张新表。`lex_deck_cards` 先保存候选身份，实际投放时才创建或复用全局 `vocab` 行；同一张卡
可属于多个计划，但只有一份 SRS 状态：

```sql
lex_decks(
  id TEXT PRIMARY KEY, name TEXT NOT NULL,
  pack_id TEXT NOT NULL DEFAULT '', level TEXT NOT NULL DEFAULT '',
  kind TEXT NOT NULL, daily_new INTEGER NOT NULL CHECK(daily_new >= 0),
  order_mode TEXT NOT NULL, study_timezone TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)
lex_deck_cards(
  deck_id TEXT NOT NULL REFERENCES lex_decks(id) ON DELETE CASCADE,
  source_ref TEXT NOT NULL, prompt_type TEXT NOT NULL, variant_key TEXT NOT NULL,
  ordinal INTEGER NOT NULL, vocab_id TEXT NULL REFERENCES vocab(id) ON DELETE SET NULL,
  introduced_at TEXT NOT NULL DEFAULT '',
  PRIMARY KEY(deck_id, source_ref, prompt_type, variant_key)
)
lex_daily_batches(
  deck_id TEXT NOT NULL REFERENCES lex_decks(id) ON DELETE CASCADE,
  local_day TEXT NOT NULL, position INTEGER NOT NULL CHECK(position >= 0),
  vocab_id TEXT NOT NULL REFERENCES vocab(id) ON DELETE CASCADE, served_at TEXT NOT NULL,
  PRIMARY KEY(deck_id, local_day, vocab_id),
  UNIQUE(deck_id, local_day, position)
)
```

`kind / level / order_mode / study_timezone` 还要用 CHECK 或规范表在数据库边界复验，不能只信
API。学习日使用 deck 的 IANA 时区计算，不使用服务器 `date.today()` 猜测；`position` 冻结当日
返回顺序，包在当天重排也不能改变幂等响应。启用 SQLite 外键检查，并为
`deck_id / vocab_id / ordinal / local_day` 建查询索引。删除计划只级联删除关系和日批次，绝不
自动删除全局 `vocab` 卡片或它的 SRS 历史；卡片删除必须是另一项显式用户操作。

**复用 `LearningStore` 的同一个连接和同一把锁**。当前项目已经选择在
`ThreadingHTTPServer` 下用一个 `check_same_thread=False` 连接加一把 `RLock` 串行化 SQLite
操作。多连接配合 WAL / busy timeout 理论上可行，但本模块不单独改变全项目的并发模型；
所有建卡、绑定计划和记录日批次在同一事务中完成。

### 内容更新与历史保留

包的 `contentRevision` 改变时，以 `source_ref + prompt_type + variant_key` 对账：

- 身份未变：更新 `card_payload_json` 与 `source_revision`，保留所有 SRS 字段；
- 条目重排：只更新 `lex_deck_cards.ordinal`；
- 条目改名或订正：身份不变，刷新 payload；
- 条目确实拆分、合并或删除：按 `idAliases / retired` 显式迁移，禁止靠删除重建解决；
- 来源暂时缺失：已有卡仍可用快照复习并显示 `sourceUnavailable`，不静默清除。

### 路由

`PreviewHandler` 加一个 `LexiconApiMixin`，`rewrite_entrypoint` 加一条
`"/lexicon": "/lexicon.html"`。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/lexicon/packs` | 包清单：级别、kind、条目数、授权状态、审计状态 |
| GET | `/api/lexicon/packs/<slug>` | 整包下发；仅此只读内容 API 可由 SW 专门缓存；审计有 error → **422** |
| GET | `/api/lexicon/search?q=&kind=&level=&limit=` | 查词：先去活用，再查词典 FTS，再并入包内条目（语法只从包里查） |
| GET | `/api/lexicon/entries/<id>` | 单条详情，词条带上词典层的全部义项 |
| GET / POST | `/api/decks` | 列出 / 创建学习计划 |
| GET / PATCH / DELETE | `/api/decks/<id>` | 读取 / 修改 / 删除计划；删除只清关系与日批次，不自动删除任何全局卡片 |
| POST | `/api/decks/<id>/serve` | 按 `daily_new` 投放今日新卡，落成 `vocab` 行；幂等（同一天重复调用返回同一批） |
| GET | `/api/review/due?scope=word\|grammar\|all&deckId=` | **扩展已有路径**并保持原响应兼容；不新增 `/queue` 口径 |
| POST | `/api/vocab/review` | 复用现有 `X-Learning-Operation-Id` 幂等回执；body 显式带 `reviewedAt`，新增严格 grade 枚举与 suspended 检查 |

`authorized_api()` 位于 `serve_course.py`，内部委托 `SecurityContext.authorize_api()`。新路由一律
走这条入口，和播放器、题库共用 Host / Origin / token 规则；路径参数先解码、再做 slug/ID
白名单校验，最后通过已解析根目录做 containment 检查。

评分事件是 `{vocabId, grade, reviewedAt}`。`reviewedAt` 必须是带时区的 RFC 3339 时间；在线评分
由页面取当前时间，离线 outbox 固化用户实际评分时间，重放时不得改成联网时间。服务端按同一
卡片的 outbox 顺序应用；早于该卡 `last_reviewed_at` 的新 operation 返回 409 并要求刷新，未来
时间超过允许时钟偏差则返回 400。相同 operationId 必须先命中旧回执，不能因重试变成冲突。

---

## 7. 前端

### 页面

一个工作区 `/lexicon`，三个视图，同 `exam.js` 的三种练习方式：

- **查词**：输入框、结果列表、详情。结果同时给词典命中和包内命中，标明来源。
- **浏览**：级别 → 包 → 单元 → 条目。语法条目按教材单元，词条按包内顺序或五十音。
- **背诵**：今日队列，四档评分（`again/hard/good/easy`），服务端权威结果与浏览器离线预测
  必须通过共享测试向量保持一致。

`home.html` 增加「独立模式 C：词汇语法」，与精听、真题同级。
个人中心把「成熟」徽标与「暂停复习」开关分开；`isDueForReview()` 不得再以 stage 3 或
`mastered` 为排除条件，只排除 API 字段 `reviewSuspended`，并比较 `nextReviewAt`。

### 划词浮层

`lookup_panel.js` 是唯一被三个页面共用的新组件，挂载在 `index.html`（精听时看不懂一个
词）、`exam.html`（读解文章里的词）和 `lexicon.html`。

接口只有三个：`mount(root, {request})`、`lookup(text)`、`unmount()`，`mount` 幂等。浮层
本身对 `app.js` 和 `exam.js` 这两个既有大文件的接入只包含脚本引用、授权 request 注入和一次
`mount()`；客户端调度器的抽取是 Phase C 的独立改动，不能和浮层接入混成一个不可审查的大
diff。

### 渲染安全

条目正文是 OCR 出来的数据。按维护规则 16：**永不经过 `innerHTML`**。所有条目文本走
`lexicon_markup.js` 的 `createElement` 路径，复用题库的标记约定（振假名用全角竖线
`｜漢字《かんじ》`，见维护规则 17），新增两个标记：

- `【…】` 语法接続的占位（`【V辞書形】＋うちに`）
- `⟦…⟧` 例句里被挖空的部分（`cloze` 卡片用）

### 离线策略

| 内容 | 策略 | 理由 |
|---|---|---|
| 页面壳（html/css/js） | 加进 `SHELL_ASSETS`，把实现时的 `SHELL_CACHE` 升到下一版本 | 同现有维护规则；不在长期方案里写死目标版本号 |
| 包清单 `/api/lexicon/packs` | 网络优先；断网回退到最近一次不含用户数据的清单快照 | 清单是指针，不是内容资产 |
| 整包 `/api/lexicon/packs/<slug>` | 以 `packId + contentRevision` 命名独立缓存，暂存、校验后发布指针 | 单包约 200 KB–2 MB；中断更新时继续保留旧 READY 版本 |
| 词典 SQLite | **不缓存，不下发** | 150–250 MB 进不了 Cache Storage 的合理预算 |
| 背诵队列 | `card_payload_json` 与卡片状态进 IndexedDB；评分 mutation 连同 `reviewedAt` 进 localStorage outbox 重放 | 避免 N1–N5 多语言正文撑爆同步 localStorage；保留现有顺序与 operationId |

当前 `sw.js` 对所有 `/api/` GET 都有一个「只走网络、失败返回 `{ok:false}`」的通用分支，
因此词包规则必须放在它之前，并且只允许上述两个只读内容端点进入 Cache Storage。会话 bootstrap、
搜索、计划、到期队列和其他用户数据 API 继续禁止缓存。缓存注册表只记录 packId、revision、
状态与校验尺寸，不记录 token；响应落盘前验证 HTTP 200、JSON schema、`packId`、
`contentRevision` 和完整字节数。

缓存发生在页面发出的正常授权 GET 上：SW 转发原请求，完整读取并验证响应副本，写入 revision
缓存后才更新 synthetic registry 指针。Cache Storage 的键必须是 SW 自建、无查询串和无授权头的
同源 synthetic URL（例如 `/__lexicon_cache__/<packId>/<revision>`），响应也只复制正文、状态码
和 `Content-Type` 等白名单头；不能直接拿原授权 Request/Response 当缓存键值，更不得把 session
token 通过 postMessage 持久化给 SW。断网请求从 registry 指向的 READY revision 返回。新响应
校验失败或下载中断时不动旧指针。

个人卡片快照不用 Cache Storage，也不继续整包写进 localStorage。`learning_store.js` 在
IndexedDB 中按 `vocab.id` 保存结构化快照和 SRS 状态；当前 localStorage 中的旧生词在首次
升级时以单事务导入，成功后才删除旧键。outbox 与墓碑体积小、强调同步写入和现有顺序，继续
留在 localStorage。IndexedDB 不可用或配额失败时禁止继续批量投卡，并给出可操作错误，不能
静默只保存一半。

**代价要说清楚**：断网时能背诵、能浏览已缓存的包，**不能全量查词**。界面要直说这一点，
而不是给一个查不出结果的搜索框——同 ADR-VIDEO-001 那句「一个点了没反应的循环按钮，比
没有这个按钮糟得多」。

---

## 8. 版权边界（不可让步）

本地源文件的准确路径是 `dist/N2语法  新日语能力考试考前对策_12684449.pdf`（文件名中有
两个连续空格）。版权页记载 ISBN 978-7-5100-2795-6、2010 年版本定价 19.80 元，并明确标注
版权所有；文档不对它今天是否仍「在售」作时效性判断。OCR 只是改变载体，不改变权利状态。

照搬 ADR-VIDEO-001 的强制机制：

1. `sourceType` 为 `textbook-ocr` 时，`attribution.redistributable` 只能显式为 `false`；
   `prepare_pack()` 遇到其他值直接失败，不能静默改写后掩盖错误的权利声明。
2. `audit_pack()` 对声称可分发的教材包判 **error**（`pack.redistributable_claim`）。
3. 新增通用 `distribution_policy.py`，由 `release_readiness.py` 以及任何未来会包含 `lexicon/`
   的产品级打包器调用。当前 `make_zip.py` / `repack_offline_bundle.py` 只打单课程 ZIP，本来
   不含词包；除非未来显式扩展其输入，不为不存在的路径添加假保护。
4. `.gitignore` 增加 `lexicon/*/pages/`、`lexicon/*/pack.json`、`lexicon/*/units.txt`、
   `lexicon/*/match-report.json`、`lexicon/*/match-resolutions.json` 和审计产物——**教材正文、
   目次转写与可反推出教材选词的映射都不进版本库**。进库的只允许 `pack-meta.json`、
   `source.pdf.sha256` 与不含正文/词典 ID 的 `entry-keys.json`；提交前由测试扫描禁入字段。
5. 这些元数据让另一台机器凭合法取得的 PDF 重建相同身份框架；`units.txt` 和匹配裁决要从
   该机器自己的素材重新产生。OCR 输出、人工裁决和
   `contentRevision` 不承诺逐字节相同；差异必须重新审计。
6. 词典层相反：必须按官方条件署名并遵守 ShareAlike。界面从词条详情与页脚都能到达
   「来源与许可」页；`SOURCES.md` 的许可版本、哈希、字段白名单或署名缺失时，
   `dictionary_build.py` 拒绝产出。

上述规则说明的是本项目的发布与版本库边界，不作「自用必然合法」的法律结论。要做可发布
版本，词汇包可使用经许可核对的词典层加自建级别表；语法释义、例句和辨析需要自行创作并
保留创作/审核记录。这条路存在，但不在本方案范围内。

---

## 9. 卡片类型

同一个调度契约，四种朝向。`prompt_type` 和 `variant_key` 决定渲染与卡片身份，调度器只接收
卡片当前状态与四档评分，不读取正文。

| `prompt_type` | 正面 | 背面 | 适用 |
|---|---|---|---|
| `recall` | 見出し語 / 文型 | 释义加例句 | 词、语法（默认） |
| `production` | 中文释义 | 見出し語加読み | 词 |
| `cloze` | 例句挖空（`⟦⟧` 标记处） | 完整例句 | 语法（**主力**） |
| `usage` | 例句加三个候选文型 | 正解，以及另外两个为什么不行 | 语法（显式 `choiceRefs` 与已审核理由驱动） |

**语法默认用 `cloze` 而不是 `recall`**：能背出「〜てたまらない＝……得受不了」不等于会用。
JLPT 文法題考的就是在句子里选对形式。`confusables` 可以提供候选，但不能自动证明某个
干扰项为什么错；`usage` 模板必须显式列出 `choiceRefs`，并为每个错误选项保存经过人工审核
的理由。理由缺失时只生成 `cloze`，不生成一个看似可判分但解释不完整的 `usage`。

一个条目可以同时存在多种朝向，同一朝向也可以来自多个例句，靠
`(source_ref, prompt_type, variant_key)` 区分并独立调度。默认只开一种，学习者可在计划里
加开。`production` 默认由学习者自评；中文提示可能对应多个同义词，除非模板显式给出允许
答案集合，否则不做字符串自动判错。

---

## 10. 分阶段

每阶段都能独立跑起来、独立验收。

### Gate 0：冻结契约（任何实现并行前）

- 签署第 11 节五条 ADR；
- 冻结 `entryKey / entryId / source_ref / prompt_type / variant_key` 身份关系；
- 冻结成熟、暂停、到期与学习日时区语义；
- 冻结浏览器个人数据分层：卡片快照进 IndexedDB，outbox/墓碑留 localStorage；
- 冻结词典字段白名单、匹配四态和教材包发布边界；
- 用最小 fixture 走通「订正正文、移动单元、增加例句、删除来源」四种内容修订，证明 SRS ID
  不变或按显式 alias 迁移。

**验收**：schema fixture、迁移 fixture 和发布策略测试通过；所有未决项有 ADR 结论，不能把
身份或版权问题留给 Phase D 的真实数据来撞。

### Phase A：地基（语法先行）

语法书已经 OCR 完了（`out/N2-grammar/`，157 页，quality-report 里 0 个 flagged 页），
先用它把只读链路走通，且**不依赖词典层**——语法条目本来就不需要词典。0 flagged 只表示
OCR 流程没有自报异常，不代表接続、例句和翻译已经正确；现有 `naで → なで` 就是反例。

- `lexicon_schema.py`、`lexicon_import.py`（extract / assemble / validate）
- `entry-keys.json`、结构化接続和 error/warning 分级
- `lexicon_store.py` 的只读部分与 `/api/lexicon/packs*`
- `lexicon.html` 的浏览视图与 `lexicon_markup.js`
- 产出 `lexicon/N2-grammar-soumatome/`

**验收**：`test_lexicon_schema.py`、`test_lexicon_import.py`（含「目次对不上必须报错」
与「単元編号三种写法归一」两条）、`lexicon_markup.test.mjs`（含注入回归与「整包都能
渲染」）；`audit_pack` 无 error；单元与条目数量、每条 headword、接続分支数、例句数做
100% 结构对账；每个日目至少抽一条逐字对照，并覆盖跨页、box、ruby、三语翻译等每类抽取
路径。抽检记录写明页面、检查人和结果。

### Phase B：词典层与查词

- `dictionary_build.py`、`jp_inflection.py`、`/api/lexicon/search`
- `match-resolutions.json` 与 matched / ambiguous / unmatched 报告
- `lookup_panel.js` 挂到三个页面

**验收**：`test_dictionary_build.py`（含 FTS5 降级路径）、`test_jp_inflection.py`、
`lookup_panel.test.mjs`；精听页面划词能查到词并一键入库；同形多义、变格、多步活用和无结果
四类 fixture 都返回可解释的候选链；词包只要还有 ambiguous/unmatched 就返回 422。

### Phase C：背诵

- `vocab` 七列、三张表和完整 CRUD/序列化迁移；`DeckStore` 与日批次幂等
- 修正 mature / suspended 语义，抽出 `srs_scheduler.js`，建立 Python/JS 共享向量
- 新增 `learning_store.js`，把旧 localStorage 生词单事务迁入 IndexedDB
- 背诵视图、四种卡片朝向、扩展 `/api/review/due`
- `me.html` 生词本按包与级别筛选；去重、缓存合并和导出保留多朝向/多 variant

**验收**：`test_lexicon_api.py` 与 `test_lexicon_migration.py` 覆盖投放幂等、计划多对多、学习日
时区、内容修订、授权边界和路径穿越；迁移 fixture 分别覆盖未复习人工暂停、自动成熟、复习后
人工暂停三类旧数据及报告/回滚；连续评分到 stage 3 后卡片仍会在未来到期；未知 grade 返回
400 且状态不变；同一词的 recall/production 和两个 cloze 同时经过 API、缓存、个人中心去重与
导出后仍是四张卡。断网背 20 张再联网，评分全部顺序重放且不重复计数。

### Phase D：词汇包与打通

- 用同一条流水线导入 N1–N5 词汇书（此时 `extract` 的匹配逻辑才真正用上词典层）
- 真题错题反查关联语法点；精听生词自动带上级别
- 按级别的掌握度汇总进 `/api/analytics`
- 完成词包 revision 缓存的暂存、发布、回滚和清理

**验收**：`match-report.json` 给出四态统计且上线包的 ambiguous/unmatched 均为 0；中断下载新
revision 后旧 READY 包仍可浏览；跨模块跳转不丢上下文；发布候选的实际 ZIP/目录扫描确认不含
教材 `pack.json`、pages、match-report 或卡片快照。

Gate 0 完成后 Phase A 与 B 可以并行；C 依赖 A 与 Gate 0 的调度契约，D 依赖 B 与 C。

---

## 11. 需要新增的 ADR

按 `docs/ADR.md` 的格式补五条，Gate 0 完成前签署：

**ADR-LEX-001 —— 词与语法共用一套内容与调度**
决定：一个顶层 schema（`kind` tagged union）、一张全局卡片表、一个到期口径、一个工作区；
词与语法保留独立的 kind 子对象、导入适配器和卡片模板生成规则。理由：共享学习基础设施，
同时不抹平来源和字段差异。`vocab` 暂不重命名，未来大版本另议。

**ADR-LEX-002 —— 读音与释义的权威来源**
决定：词条表記、读音、词性和英语词典义项由所选 JMdict 记录负责；读音只接受词典或人工
确认；教材负责级别、顺序、中文/韩文翻译、例句与语法说明。匹配采用四态并保存人工裁决；
两层分别记录许可。范围边界：可发布版本的中文释义来源与自行创作审核流程另立方案，当前
教材私有包不得把它冒充已经解决。

**ADR-LEX-003 —— 条目、卡片与计划的身份及修订协议**
决定：条目使用持久 `entryKey` 加 96-bit ID；卡片身份是
`source_ref + prompt_type + variant_key`；计划通过多对多表引用全局卡片；内容修订只刷新卡片
快照，拆分、合并、删除走显式 alias/retired 迁移。理由：普通 OCR 订正和教材重排不能清空
学习历史，同一卡也不能因为加入第二个计划而产生两份互相冲突的 SRS 状态。

**ADR-LEX-004 —— 长期复习、成熟与暂停**
决定：`srs_stage = 3` 表示成熟而不是退出复习；只有 `review_suspended` 排除到期队列；评分
只接受四个枚举；服务端为最终权威，浏览器离线预测与它共用测试向量。迁移保留回滚备份；
无复习记录的旧 `mastered` 行回填暂停，有复习记录的歧义行恢复按期复习、列入报告并允许用户
一次性批量重新暂停。兼容列 `mastered` 只派生展示成熟状态。理由：全量回填暂停会让现有自动
成熟卡继续永久消失，不能直接承载长期词汇学习。

**ADR-LEX-005 —— 浏览器个人卡片存储**
决定：卡片快照和 SRS 本地副本进 IndexedDB，按 `vocab.id` 管理；小而关键的 outbox 与删除
墓碑继续留在 localStorage。旧生词单事务迁移，成功后再删旧键，配额失败时停止批量投卡并
保留旧数据。理由：N1–N5 多语言例句与多 variant 会稳定超过 localStorage 的合理容量，且
同步 JSON 序列化会阻塞页面。

---

## 12. 风险与待决

| 项 | 状态 |
|---|---|
| 词典许可与字段级特殊条件 | **每次下载都核对官网**；当前主许可为 CC BY-SA 4.0，但 KANJIDIC 特殊字段不能靠本文概括 |
| 词汇书的 OCR 质量 | 未验证。语法书 0 flagged 页不能推断词汇书也如此——词表排版更密，很可能要走 `boxes` 二次通道或提分辨率 |
| 見出し語到词典的匹配率 | 未知。多义、旧字体、复合词会进入 ambiguous/unmatched；先用样本 spike 估算人工裁决量，再承诺 N1–N5 工期 |
| 词典 SQLite 体积 | 150–250 MB 是估计值，建完索引实测后再定要不要裁剪义项 |
| 旧 `mastered` 数据迁移 | 无复习时间的行按人工暂停处理；有复习时间的歧义行恢复到期、逐 ID 报告并提供批量重新暂停；迁移必须备份且允许按快照回滚 |
| IndexedDB 容量与迁移 | Phase C 用 1k/5k/10k 卡 fixture 实测占用和升级时间；配额失败、事务中断、旧键删除前崩溃都必须有恢复测试 |
| 包缓存与本地版权内容 | Cache Storage 中会保存教材派生内容；仅限当前浏览器 profile，UI 提供清除入口，发布扫描不得把缓存或包复制进制品 |
| 例句 TTS 与词条读音音频 | 本方案完全不含，是独立决策 |
| 手写与笔顺 | 不在范围内 |
