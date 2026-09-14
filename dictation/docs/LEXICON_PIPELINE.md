# 词汇 / 语法内容包制作流水线与操作指南

把一本 OCR 过的教材做成 `/lexicon` 能提供的 `pack.json`。

```text
教材 PDF ──► 1. pdf_ocr run（已有）──► out/<书名>/document.json
         ──► 2. extract 结构化抽取 ──► lexicon/<slug>/pages/p<NNNN>.json（可人工编辑）
         ──► 3. 人工：units.txt 数条目、修 pages/ 的 error
         ──► 4. assemble 装配对账 ──► pack.json + match-report.json
         ──► 5. validate 质量审计 ──► /api/lexicon/packs/<slug>
```

- **制作入口**：[`src/lexicon_import.py`](../src/lexicon_import.py)
- **数据结构与审计规则**：[`src/lexicon_schema.py`](../src/lexicon_schema.py)
- **版权边界判定**：[`src/distribution_policy.py`](../src/distribution_policy.py)
- **渲染器实现**：[`src/web/lexicon_markup.js`](../src/web/lexicon_markup.js)
- **设计方案**：[`docs/LEXICON.md`](LEXICON.md)

---

## 1. 三段式为什么这么分

和 [`JLPT_EXAM_PIPELINE.md`](JLPT_EXAM_PIPELINE.md) 的理由一样：**只有中间那一步需要人**，
两端必须机械可重复。

`extract` 的任务不是「把文字读出来」——那是 OCR 已经做完的事，而且做得不够好。它的任务是
**找出结构、把每个字段旁边的原始证据保留下来、并在没把握的地方大声说出来**。因此
`pages/*.json` 是可以手改的，改完重跑 `assemble` 不会丢失任何人工修正（身份由
`entry-keys.json` 固定，见第 5 节）。

`pack.json` 是**生成物**。改错字改 `pages/`，不要手改 `pack.json`——`audit_pack()` 会因为
`contentRevision` 对不上而拒绝它（`pack.revision_stale`）。

---

## 2. 目录布局

```
lexicon/N2-grammar-soumatome/
  pack-meta.json          书名、ISBN、级别、kind、出处与授权声明（人写，进版本库）
  source.pdf.sha256       原始 PDF 指纹（进版本库，不存 PDF 本身）
  entry-keys.json         条目身份注册表（进版本库，只含身份，不含正文）
  units.txt               教材目次的人工誊抄 + 每单元条目数（**不进版本库**）
  pages/p0018.json        逐页结构化抽取，可人工编辑（**不进版本库**）
  match-resolutions.json  词典匹配的人工裁决（Phase B；**不进版本库**）
  pack.json               生成物（**不进版本库**）
  match-report.json       对账报告（生成物；**不进版本库**）
```

**为什么大部分不进版本库**：OCR 只改变载体，不改变权利状态。教材正文、目次转写和任何
能反推出教材选词的映射都留在本机。见 ADR-LEX-006。

---

## 3. 第一步：`extract`

```bash
python src/lexicon_import.py extract \
    --document out/N2-grammar/document.json \
    --out lexicon/N2-grammar-soumatome
```

已有 `pages/` 时会拒绝覆盖（那是人工修正的所在地）；确实要重新抽取时加 `--force`，
**并且先确认 `entry-keys.json` 里的 anchor 还指得对**。

输出形如：

```
Wrote 157 page files into lexicon/N2-grammar-soumatome/pages
  entry blocks: 195
  issues      : 100 errors, 353 warnings
```

`error` 会挡住**该页所有条目**进入 `pack.json`；`warning` 随条目一起下发。

### 页面文件契约

```jsonc
{
  "page": 18,
  "unitHeader": { "week": 1, "day": 1, "title": "熱っぽい" },
  "blocks": [
    { "id": "p0018-b2", "sourceAnchor": "pdf:18:block:2", "type": "entry",
      "headword": "〜がち",
      "gloss": { "zh": "…", "en": "…", "ko": "…" },
      "connectionRaw": ["Nがち", "Vますがち"],
      "connectionSource": "box",
      "examples": [{ "ja": "…", "zh": "…", "en": "…", "paraphrase": "…" }],
      "notes": ["れい ありがち／遅れがち"],
      "rubyHints": [] }
  ],
  "issues": [
    { "severity": "error", "code": "extract.connection_missing",
      "message": "…", "blockId": "p0018-b2" }
  ]
}
```

`type` 取值：`entry` / `unit-header` / `note` / `exercise`（7日目的実戦問題，**本包不收**，
那是题库的职责）/ `front-matter`。

---

## 4. 抽取器挡住的五个坑

每一个都是这本书真实发生过的，不是假想。

**一、单元编号必须规范化。** 同一本书的 OCR 里同时出现 `第1週`、`第一週`、`第２週`。
不规范化就会把同一週拆成三个单元。全部归一成 `(week, day)` 整数，解析不出就停下报错。

**二、目次数量对不上必须报错。** `units.txt` 是人照着书的目次抄的，`assemble` 拿它对账。
缺条目意味着 OCR 漏了一整块——**背了一半的语法表，学习者没有任何办法发现少了哪一半**。
所以报错停下，不放宽成警告。

> 这也是 `units.txt` 里的条目数**不能从 OCR 推出来**的原因：那等于让检查项去核对它自己。
> 没数过的单元写 `?`，`assemble` 会点名报错，不会当成 0。

**三、`> ` 引用行和 `<!-- ruby: -->` 注释是数据。** OCR 的二次通道把浮动接続框和例句译文
合并成引用行，把振り仮名包成 HTML 注释。当 Markdown 噪声丢掉就丢掉了整张接続表。
但 **ruby 注释只作提示**，进 `rubyHints`，永不写入 `reading`（ADR-LEX-002）。

**四、接続缩写不是日文。** 书上印的是 `Aくて / naで / Vたくて`；这本书的 OCR 把 `naで`
读成了 `なで`。`connectionRaw` 保留原样供逐字核对，`assemble` 按书自己的
接続の表示方法（`lexicon_schema.CONNECTION_FORMS`）映射，未知缩写报错并指出可能的误读。

**五、`pack.json` 是生成物，不许手改。**

### 抽取器已知的弱点

它是规则驱动的，以下情况会漏或错，需要人工在 `pages/` 里补：

| 症状 | 原因 | 怎么修 |
|---|---|---|
| `extract.headword_missing` | 見出し語那一行 OCR 整行丢了 | 对照原书填 `headword` |
| `extract.connection_missing` | 浮动接続框两条通道都没读到 | 对照原书填 `connectionRaw` |
| `extract.unit_header_missing` | 该页的「N日目」行没读出来 | 手填 `unitHeader` |
| 条目被切多了 / 少了 | 見出し語判定靠「独占一行且下方留空」 | 合并或拆分 `blocks` |
| 第 8 週识别率低 | 接续词单元排版与前 7 週不同 | 逐条手工整理 |

判定规则刻意保守：漏判会变成一条看得见的 `headword_missing` 错误，而激进的规则会把
一个条目静默切成三个，且没有任何东西会提这件事。

---

## 5. 身份：`entry-keys.json`

```jsonc
{
  "schemaVersion": 1,
  "packId": "N2-grammar-soumatome",
  "nextKey": 196,
  "entries": [
    { "entryKey": "e0001", "sourceAnchor": "pdf:18:block:2" }
  ]
}
```

只允许 `entryKey / sourceAnchor / retired / aliasOf` 四个字段——它是唯一进版本库的包文件，
写入前和测试中都会扫一遍禁入字段（`audit_entry_key_registry()`）。

`entryId = kind[0] + "_" + sha256(packId + US + entryKey)[:24]`。正文、单元、顺序都不参与，
所以订正错字、移动单元、增加例句都不会切断学习者的 SRS 历史。

**新 anchor 需要显式开关**：普通 `assemble` 遇到没注册过的 anchor 会报告并失败。只有确认
「这些确实是新条目」时才加 `--accept-new-keys`，并审查 `entry-keys.json` 的 diff。
重新抽取导致 anchor 变化时，正确修法是**把旧 key 指向新 anchor**（一行可审查的 diff），
不是顺手生成一批新身份。

---

## 6. 第二步：人工 `units.txt`

```
# 格式：第N週 M日目 <单元标题> <该单元条目数>
第1週 1日目 熱っぽい 4
第1週 2日目 空を飛びたいんだもの ?
```

标题可以照抄目次，**条目数必须翻着书数**。`?` 表示还没数，`assemble` 会点名。

7日目 是実戦問題，属题库不属本包，不列在这里。

---

## 7. 第三步：`assemble`

```bash
python src/lexicon_import.py assemble --pack lexicon/N2-grammar-soumatome
# 首次导入、确认过条目确实是新的时：
python src/lexicon_import.py assemble --pack lexicon/N2-grammar-soumatome --accept-new-keys
```

它会：

1. 跳过 error 页上的条目；
2. 解析 `sourceAnchor → entryKey`（未注册就失败）；
3. 把 `connectionRaw` 映射成 `{slot, form, display}`（未知缩写就失败）；
4. 生成卡片模板：`recall` 一张，例句里能定位到文型的再加一张 `cloze`；
5. 对账 `units.txt`，逐单元报差额；
6. 跑 `audit_pack()`。

**语法默认用 `cloze` 而不是 `recall`**：能背出「〜てたまらない＝……得受不了」不等于会用，
JLPT 文法題考的就是在句子里选对形式。定位不到文型时不生成 cloze——挖错位置的空比没有空
更能高效地教错东西。

`usage`（三选一辨析）**永不自动生成**：它必须为每个错误选项带上经人工审核的理由，
否则就是一张能判你错却说不出为什么的卡片。

对账不通过或审计有 error 时不写 `pack.json`（`--allow-failed-audit` 只用于查看结果）。

---

## 8. 第四步：`validate`

```bash
python src/lexicon_import.py validate --pack lexicon/N2-grammar-soumatome
```

审计报告的形状和 `audit_exam` / `audit_manifest` 完全一致（`status` / `summary` / `issues`），
所以服务端用同一条 fail-closed 路径拒绝坏包：**有 error 的包 → HTTP 422，不提供学习**。

常见 error：

| code | 含义 |
|---|---|
| `pack.redistributable_claim` | 教材包声称可再分发 |
| `pack.revision_stale` | 手改过 `pack.json` |
| `entry.unit_missing` | 条目不属于任何单元（浏览视图走单元，它会被计数但看不见） |
| `entry.chinese_missing` | 条目和它的例句都没有中文，界面上没有一个字读得懂 |
| `grammar.connection_missing` | 语法条目没有接続 |
| `example.reading_unsourced` | 读音没有 `readingSource` |
| `card.cloze_unbalanced` | `markedJa` 的 `⟦⟧` 不成对 |
| `card.usage_rationale_missing` | 干扰项没有审核过的理由 |

`entry.gloss_zh_missing` 是 **warning**：这本书只在侧边框里给部分条目印释义，例句译文
仍是中文，条目照常显示但标注待核对。

---

## 9. 发布是一个整体，不是几次写文件

`assemble` 的最后一步走 `publish_pack()`：`pack.json`、`match-report.json`、
`quality-report.json` 先全部写进暂存目录并校验，再逐个 `os.replace` 就位，最后移动
`publish.json` 清单。清单记录本次的 `contentRevision` 与每个文件的摘要。

为什么必须这样：

- 逐文件 `os.replace` 只保证**单个文件**原子。中途失败会留下一份描述另一个版本的报告。
- `pack.json` 原来用 `write_text` 直接覆盖——那是就地截断，中断会留下解析不了的包。
- 报告原来在 `supplement_pack()` **之前**盖章。补充会改变 `contentRevision`，所以
  `lexicon/N2-grammar-soumatome/match-report.json` 至今记的还是 `109a4721…`，而包已经是
  `24adb2f2…`。现在 revision 在补充之后才盖，且 `LexiconStore` 会把这种不一致报出来
  （`pack.publication.staleReports`），包页面上也会显示。

构建时间只进清单，不进内容哈希：同样的源、裁决和词典版本必须得出同样的 revision。

**语法包的报告仍是过期的**，因为修好的是流水线，而重新盖章需要重跑 `assemble`；
手改生成物是这套机制存在的理由，不是它的用法。

## 10. 单词包：种子身份与人工裁决

`lexicon/Everyday-words/` 由 [`src/lexicon_content.py`](../src/lexicon_content.py) 的
`build_words()` 生成，源数据是三个文件：

| 文件 | 性质 | 说明 |
|---|---|---|
| `assets/lexicon_seed/words.json` | 源 | 词 / 读音 / 中文释义与例句模板 |
| `assets/lexicon_seed/word-keys.json` | 源 | 种子 → `entryKey` 注册表，**一次分配，永不移动** |
| `assets/lexicon_seed/word-adjudications.json` | 源 | 匹配歧义的人工裁决 |

注册表为什么必须存在：key 原来按遍历位置分配（`e0001`、`e0002`…），在列表前面插一个词
就会让后面每一个词换 ID，学习者背了一个月的卡片会全部变成新卡。现在种子的身份是
`normalize(词)|normalize(读音)`，新词追加到末尾，重排列表不改变任何 ID。当前注册表已按
已发布的 325 个种子（纳入 300、排除 25）冻结。

裁决文件为什么必须存在：325 个种子里有 25 个在 JMdict 里匹配到多个词目，自动匹配无法
选择。填入 `entSeq`（可选 `senseKeys`）后该条会被纳入，并计入 `outcomes.manually-resolved`。
**目前 25 条全部待裁决**，因此纳入数仍是 300。

义项不再整条照抄：`dictRef` 记录 `writtenForm`、`reading`、`senseKeys` 与
`dictionaryVersion`，只取该表记与读音真正允许的义项——`re_restr` / `stagk` / `stagr`
说得很清楚的事，之前没有人读。

## 11. 生成不是审核

生成函数只能写 `reviewStatus: machine_checked`。`reviewed` 需要一条能被审计的记录：

```json
"review": {"method": "manual", "reviewer": "姓名",
           "reviewedAt": "2026-09-07T00:00:00+00:00",
           "contentHash": "<review_content_hash(spec)>"}
```

`contentHash` 覆盖题面、选项、答案与解析。改动其中任何一项都会让审核失效
（`review.stale`），审计也会拒绝一条不指名审核人或不覆盖当前内容的记录。历史上的
`verified` 一律按 `machine_checked` 读取——它是生成器写的，证据里就写着
`notHumanReview: true`。

**当前状态**：两个包共 2,085 条自动模板处于 `machine_checked`，不计入正式客观练习；
界面按题型给出 `review.required`。逐条裁决是内容工作，不是代码工作。

## 12. 词典安装

```bash
python src/dictionary_build.py --download          # 下载并安装
python src/dictionary_build.py --input JMdict_e.gz # 从本地文件安装
```

发布同样是整体：构建产物进 `assets/dictionary/versions/<revision>/`（含
`dictionary.sqlite3` 与 `SOURCES.json` / `SOURCES.md`），完整后才移动
`assets/dictionary/current.json` 指针。`DictionaryStore` 每次访问都解析指针，所以
安装失败或被取消时仍然服务上一个版本，上一个版本目录会保留、更早的会清理。

界面上的安装是一个作业：`assets/dictionary/install-job.json` 记录 `jobId`、`stage`、
`bytes`、`entriesProcessed`、`errorCode` 与 `cancelRequested`，可以查询进度、取消、失败后
重新开始。进程重启后，文件说 `running` 而没有工作线程的作业会被报成 `interrupted`——
那是一个页面能处理的事实，不是一个永远转下去的进度条。轮询次数用尽时页面显示「仍在
处理」，不显示「已更新」。

没有 FTS5 的 SQLite 会降级：表记、读音与前缀查询照常，释义全文检索不可用，
`status().degraded` 与 `degradedReason` 会说明这件事。

## 13. 语法包的抽取现状（2026-09-02 记录，保留为历史快照）

`lexicon/N2-grammar-soumatome/` 已跑完 `extract`：

| 项 | 数 |
|---|---|
| 页面文件 | 157 |
| 抽出的条目块 | 195 |
| error 级 issue | 100 |
| warning 级 issue | 353 |
| 识别出的单元 | 47 / 48 |

其后该包已经出包并安装（191 条 / 48 单元，审计 0 error 0 warning）。上表是抽取阶段的
快照，不是当前状态。重新装配时仍需：

1. 翻书数每个单元的条目数，填进 `units.txt`；
2. 清掉 `pages/` 里的 error（多为 `connection_missing` 与 `headword_missing`）；
3. `assemble --accept-new-keys`，审查 `entry-keys.json` 的 diff；
4. 按 [`LEXICON.md`](LEXICON.md) 做结构对账：单元数、条目数、每条 headword、接続分支数、
   例句数 100% 核对，每个日目至少抽一条逐字对照，抽检记录写明页面、检查人和结果。

第 4 步不能省。0 flagged 页只表示 OCR 流程没有自报异常，不代表接続、例句和翻译是对的——
`naで → なで` 就是现成的反例。
