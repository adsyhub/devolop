# 在线视频课程制作流水线（修订版）

这份文档定义**正确的**视频课制作流程，重点是「一句话到底是怎么划出来的」。

三份文档的分工：

| 文档 | 讲什么 |
|---|---|
| [COURSE_PIPELINE.md](COURSE_PIPELINE.md) | 本地音频课：ASR → 分句 → 翻译讲解 → ZIP |
| [VIDEO_COURSES.md](VIDEO_COURSES.md) | 视频课**怎么用**：版权立场、三档控制、命令行、排错 |
| **本文** | 视频课**怎么做对**：从字幕轨到句子的每一步契约、参数、不变量、验收线 |

入口：[`src/build_video_course.py`](../src/build_video_course.py)。
唯一知道视频站点存在的模块：[`src/media_sources.py`](../src/media_sources.py)。

---

## 0. 这份文档为什么存在

2026-09-01 对 `courses/` 下全部 12 门视频课（1207 句）做了实测：

| 指标 | 实测 |
|---|---|
| 句尾没有终止标点（半句被切断） | **66.8%** |
| 长度正好卡在 18–19 字 | **36%**（20 字以上每档只剩 ~8 句） |
| 以助词开头（上一句被从中间劈开） | 14.5% |
| 一条里塞了多个完整句 | 18.6% |
| ≤4 字碎片 | 12.8%（含 47 条纯 `1` `2` `S`） |
| 被标为 practiceEligible | 96.3% |

长度直方图在 18–19 字处是悬崖式尖峰，之后断崖。**这是渲染宽度的指纹，不是语言的分布。**
当前流水线产出的不是句子，是 YouTube 自动字幕的显示行。

根因三处，全部在代码里：

1. **合并规则对字幕路径完全失效。**
   [`build_video_course.py:159`](../src/build_video_course.py#L159) 调 `merge_sentence_fragments`，
   但 [`sentence_segmentation.py:31`](../src/sentence_segmentation.py#L31) 的 `is_continuation_fragment`
   **只在结尾是逗号时才合并**（[`language_support.py:22`](../src/language_support.py#L22)，
   ja 的 `continuation_endings` = `("、", ",", "，", "､")`）。这条规则是为 Whisper 写的——ASR 会输出标点。
   自动字幕**在换行处没有任何标点**，所以这个合并一次都没生效。

2. **滚动窗口塌缩产出的是显示缓冲区，不是句子。**
   [`media_sources.py:606`](../src/media_sources.py#L606) `_collapse_rolling_window` 把增长链塌成
   「窗口最终状态」，那正好是 ≈2 行 ≈19 字；窗口迟迟不刷新时就塌成 195 字巨块。
   **同一段代码同时制造了两个极端。**

3. **质量门不看文本边界。**
   [`bundle_quality.py:102-104`](../src/bundle_quality.py#L102-L104) 只检查 <350ms / >30s。
   实跑 tbs-0008：67% 句子被切断的情况下，只报 5 条 `sentence.very_short` 警告就通过了。
   **下一批导入还会静默通过。**

对照：本地音频课 `2010-12-N2` 走 Whisper + 同一个合并函数，长度 9–16 字、无 19 字尖峰、无巨块。
**流水线本身是好的，坏的只有字幕这条路径。**

---

## 1. 三条数据结论（决定了下面的设计）

改法不是拍脑袋，是这三条实测结论逼出来的。

### 1.1 句终标点是可用的主力信号

把每门课的所有显示行拼成字符流后数标点：

```
1207 条显示行  →  流中 719 个 。！？
每分钟 4.3 – 8.9 句
```

新闻语速下这是合理的句密度。**日语自动字幕是带句号的，只是句号落在显示行中间。**
所以「按句终标点重切」是主力规则，不是权宜之计。

### 1.2 但只靠标点会做出没法练的长句

只按 `。！？` 重切后的长度分布：

| 课程 | 中位 | p90 | max |
|---|---|---|---|
| tbs-0004 | 26 | 66 | 138 |
| tbs-0005 | 49 | 105 | 159 |
| tbs-0008 | 26 | 67 | **209** |
| tbs-0009 | 38 | 79 | 198 |

日语新闻长句确实长。60 字以上的句子做听写没有意义。
**所以必须有第二级切分（长度上限 + 次级边界），这不是过度设计。**

### 1.3 存在完全没有标点的字幕轨

`tbs-test-01` 的字幕流 1509 字，**0 个终止标点**。只靠规则 A 会把整门课塌成一句。
**所以必须有停顿兜底。** 这是真实存在的 case，不是假想。

---

## 2. 目标流水线全图

```
URL
 │
 ├─(1) 取轨 ── yt-dlp，只要字幕 ─────────────► SubtitleTrack{kind: manual|auto}
 │                                                    │  ★ 原始轨落盘保留
 ├─(1') 无字幕 ── 临时音频 ── 本地 ASR ── 删音频 ──► Segment[]（已带句读）
 │                                                    │
 ▼                                                    ▼
(2) 解析  parse_subtitles  ────────────────────► Cue[] + ★ token 级时间
 │
(3) 去噪  normalize_cue_text  ─────────────────► Cue[]（去 tag / 噪声标签 / 说话人）
 │
(4) 去滚动窗口（仅 auto 轨）_collapse_rolling_window
 │        ★ 语义收窄：只负责「去重复」，不再负责「定句」
 ▼
(5) ★ 重建字符时间流   CharStream[(char, t)]
 │
(6) ★ 重分句  规则 A/B/C/D  ───────────────────► 句子边界
 │
(7) ★ 时间轴回填 + 不变量校验
 │
(8) ★ 碎片与非语音处理（marker / practiceEligible）
 │
 ▼
segments_to_sentences ──► course_schema（稳定 id、contentType）
 │
(9) 质量门 bundle_quality ── ★ 新增文本边界检查
 │
 ▼
翻译讲解 enrichment ──► courses/<name>/manifest.json
```

★ = 本文新增或修改的环节。没有星号的部分**保持原样**。

**顺序上唯一不能动的一条：重分句必须在 enrichment 之前。**
现有代码已经是对的（先分句再 enrich）。反过来会按错误的句子生成翻译讲解，钱和时间全白花。

---

## 3. 阶段 (1) 取轨：原始轨必须落盘

### 现状

[`fetch_subtitles`](../src/media_sources.py#L818) 把字幕下到临时目录，读成字符串后 `shutil.rmtree` 删掉。
**结果：想重新分句就必须重新联网抓一次。** 12 门已有课现在就卡在这里。

### 要求

原始字幕轨写入 `video-work/<name>/subtitles.<lang>.<fmt>`，连同一份 `track.json`：

```json
{
  "language": "ja",
  "kind": "auto",
  "format": "json3",
  "retrievedAt": "2026-09-01",
  "sourceUrl": "https://www.youtube.com/watch?v=...",
  "sha256": "…"
}
```

理由：

- **重分句是纯本地操作。** 调参数、修 bug、重跑，都不该再碰网络。
- **可复现。** 有原始轨才能证明「句子是从这份轨推出来的」，出问题能二分。
- **不违反版权立场。** 存的是字幕文本，不是媒体。`media.attribution.redistributable` 恒为 `false` 不变，
  `video-work/` 已在 gitignore 内，且不进 ZIP、不进 `courses/`。

> 音频路径的承诺不变：`temporary_audio` 仍然用完即删。**字幕留，音频不留。**

---

## 4. 阶段 (2) 解析：保留 token 级时间

### 现状

[`_parse_json3`](../src/media_sources.py#L444) 把 `segs[].utf8` 拼成一个字符串就扔掉了 `segs` 结构：

```python
pieces = [str(seg.get("utf8", "")) for seg in segs if isinstance(seg, dict)]
body = "".join(pieces)
```

YouTube json3 的每个 seg 还带 `tOffsetMs`（相对本 event 起点的偏移），自动轨里是**词/token 级时间戳**。
**当前实现把它整个丢了。** 这正是重分句最需要的东西。

> **已在真实数据上验证（2026-09-01）**：20 门重建课程中 14 门拿到 `timeResolution: token`，
> 其余 6 门是 vtt/srt 或无 offset 的 json3，按第 11 节降级为 `cue-interpolated`。
> 降级是常态而非异常，不要假设某条轨一定有 offset。

### 要求

`Segment` 增加可选的 token 时间：

```python
@dataclass(frozen=True)
class Token:
    text: str
    start: float          # 绝对时间 (tStartMs + tOffsetMs) / 1000

@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str
    tokens: tuple[Token, ...] = ()   # 新增，缺省为空
```

`tokens` 为空是**合法状态**，不是错误——srt / vtt / 部分人工轨本来就没有。
下游据此降级，见第 11 节的三档时间精度。

`aAppend` 事件仍然在解析层丢弃（现有行为正确，保留）。

---

## 5. 阶段 (4) 去滚动窗口：语义收窄

`_collapse_rolling_window` 现在同时承担了两件事，这是它出问题的原因：

| 它现在做的 | 之后 |
|---|---|
| 去掉重复的窗口前缀 | **保留**，这是它唯一该做的事 |
| 顺带决定了句子边界 | **移除**——边界由阶段 (6) 决定 |

具体改动：

1. 塌缩后的产物**不再直接当句子**，它只是「去重后的连续字符流的一段」。
2. seam 修剪的最小重叠 `minimum_overlap = 2`（spaceless 语言）**风险明确记录下来**：
   日语在接缝处天然重复 `です` `ます` `した` 这类 2 字序列，这个阈值有吃掉真字的可能。
   在阶段 (7) 的守恒律建立之前不要动它；守恒律只覆盖塌缩**之后**的环节，
   塌缩本身必须有独立的、针对真实重复的回归测试（`もう一度` / `もう一度お願いします`）。
3. 人工轨仍然**不做**塌缩（现有行为正确，保留）。

---

## 6. 阶段 (5) 重建字符时间流

把去重后的所有 cue 展平成一条序列，每个字符带一个时间：

```python
CharStream = list[tuple[str, float]]
```

规则：

- **有 token 时间**：字符时间 = 所在 token 的 start（token 内所有字符共用 token 起点）。
- **没有 token 时间**：在 cue 内按字符数线性插值 `start + (end - start) * i / len(text)`。
- cue 之间**不插入任何字符**（日语已经在 `normalize_cue_text` 里去掉了全部空白）。
- 展平后的纯文本记为 `stream_text`，它是后面守恒律的基准。

拼接时不做任何文本修改。**「分句」和「改文本」在这条流水线里必须是两件事。**

---

## 7. 阶段 (6) 重分句：四条规则

在 `CharStream` 上求切点。四条规则按优先级依次应用。

### 规则 A — 句终标点（主力）

在 `。！？!?` **之后**切。紧跟其后的闭合符（`」` `』` `）` `)` `】` `〉` `》` 引号）归**前**一句。

覆盖第 1.1 节测到的 719 个边界，是绝大多数句子的来源。

### 规则 B — 停顿（无标点时的唯一可靠信号）

相邻字符时间差 ≥ `PAUSE_HARD` 处切。

**只在有 token 级时间时生效。** cue 级时间做不到这件事——自动字幕的 cue 首尾相接，
cue 间隔恒为 0，插值出来的「停顿」是假的。这就是第 4 节非要保留 `tOffsetMs` 的原因。

没有 token 时间时规则 B 整条跳过，由规则 C 承担全部兜底。

### 规则 C — 长度上限 + 次级边界

对 A/B 切完后仍 > `MAX_CHARS` 的段，在段内找次级切点，递归直到全部达标。

候选切点按优先级：

| 优先级 | 切点 | 说明 |
|---|---|---|
| 1 | `、` `，` 之后 | 读点，日语最自然的次级停顿 |
| 2 | token 停顿 ≥ `PAUSE_SOFT` | 需要 token 时间 |
| 3 | 接续成分之后 | `て` `で` `が` `けど` `けれど` `ので` `から` `し` `ば` `たら` `なら` `ながら` |
| 4 | 接续词之前 | `そして` `しかし` `また` `一方` `ただ` |
| 5 | 硬切 | 都找不到时在 `MAX_CHARS` 处切，并计入 `forcedCuts` |

选点方式：候选必须落在 `[MIN_CHARS, len - MIN_CHARS]` 区间内（避免切出碎片）；
同优先级内选**最靠近 `TARGET_CHARS` 的那个**，而不是最靠近中点——目标是产出可练的长度，不是均分。

优先级 5 的硬切是**失败出口，不是正常路径**。它必须被计数并暴露给质量门（第 12 节）。

### 规则 D — 下限合并

长度 < `MIN_CHARS` 的段：

- 若与**前**段的时间间隔 < `PAUSE_HARD` → 并入前段；
- 否则若与**后**段间隔 < `PAUSE_HARD` → 并入后段；
- 两侧都远 → 保留为独立条目，但 `practiceEligible = false`。

第三种情况就是 `1` `2` `S` 这类画面数字和 `うん。` 这类应答词：
它们在时间上孤立，删掉会让时间轴出现空洞，留着又不该进听写队列。**标记，不删除。**

---

## 8. 阶段 (7) 时间轴回填与不变量

每句：

```
start = 首字符时间
end   = min(末字符时间 + TAIL_PAD, 下一句首字符时间)
```

最后一句的 `end` 取 `min(末字符时间 + TAIL_PAD, media.durationSec)`。

### 五条不变量（必须有测试）

| # | 不变量 | 为什么 |
|---|---|---|
| I1 | **字符守恒**：所有句子文本拼接后与 `stream_text` 逐字相等 | 最重要的一条。它把「分句」和「改文本」彻底分开，任何吃字的 bug 都会被它逮住 |
| I2 | **单调不重叠**：`sentences[i].end <= sentences[i+1].start` | 播放器「我现在在第几句」的查找靠它，重叠会让查找有歧义 |
| I3 | **绝对时间**：时间轴始终是视频绝对时间，`--clip` 只筛选不平移 | 沿用 VIDEO_COURSES.md 第 4.6 节已有的承诺 |
| I4 | **纯函数**：同一份字幕轨永远产出同一组句子。不看网络，不看模型，不看时钟 | 重分句要能反复跑、能二分、能在 CI 里断言 |
| I5 | **时长下限**：每句 `end - start >= MIN_DURATION` | 已有的 `min_duration` 保护，只向静音方向扩展，绝不越过下一句起点 |

I1 是这套东西的地基。有了它，第 5 节里 `minimum_overlap = 2` 那个吃字风险就被**限制在塌缩这一个环节内**，
不会再扩散到后面任何一步。

---

## 9. 阶段 (8) 内容模型：不动 schema

重分句需要留下痕迹，但**不新增 sentence 字段**——
`bundle_quality` 和 `course_schema` 对 sentence 的字段有强校验，加字段会牵动 schema 版本。

统计信息写进 `buildMetadata.segmentation`（课程级）：

```json
"segmentation": {
  "strategy": "sentence-boundary/v1",
  "timeResolution": "token",
  "sourceCues": 204,
  "sentences": 118,
  "forcedCuts": 3,
  "params": { "maxChars": 45, "minChars": 8, "targetChars": 24,
              "pauseHard": 0.60, "pauseSoft": 0.35 }
}
```

`timeResolution` 取 `token` / `cue-interpolated` / `none`，质量门据此调整阈值（第 12 节）。

sentence 层面只沿用现有字段：`contentType`（`CONTENT_TYPES` = dialogue / prompt / option / marker / instruction）
和 `practiceEligible`。规则 D 第三种情况写 `contentType = "marker"`，
[`course_schema.py:186`](../src/course_schema.py#L186) 会自动把 `practiceEligible` 置 false。

---

## 10. 参数表

| 参数 | 默认 | 理由 |
|---|---|---|
| `MAX_CHARS` | 45 | 硬上限。超过就必须找次级边界。第 1.2 节实测 p90 已达 60–105 字 |
| `TARGET_CHARS` | 24 | 次级切分的理想长度。对齐本地音频课的实际手感（`2010-12-N2` 中位 14 字，新闻语速偏长） |
| `MIN_CHARS` | 8 | 低于此值考虑并入邻句。实测 12.8% 的 ≤4 字碎片正是要处理的对象 |
| `PAUSE_HARD` | 0.60 s | 句间停顿。低于此值日语连读会被误切 |
| `PAUSE_SOFT` | 0.35 s | 次级停顿，仅用于规则 C 优先级 2 |
| `TAIL_PAD` | 0.15 s | 句尾留白，避免末音被切掉。永不越过下一句起点 |
| `MIN_DURATION` | 0.35 s | 沿用 `clean_segments` 现值 |
| `_SEAM_GAP` | 0.75 s | 沿用现值，不动（第 5 节） |

参数全部走一个 dataclass，写进 `buildMetadata.segmentation.params`。
**调参必须留痕**，否则两门课看起来一样却是不同规则做的。

---

## 11. 三档时间精度

不同来源能给的时间精度差别很大，**流水线不假装它们一样**（和 VIDEO_COURSES.md 第 2 节的三档控制同一个态度）：

| `timeResolution` | 来源 | 规则 B | 规则 C 优先级 2 | 后果 |
|---|---|---|---|---|
| `token` | json3 自动轨（有 `tOffsetMs`） | ✅ | ✅ | 完整能力 |
| `cue-interpolated` | vtt / srt / 无 offset 的 json3 | ❌ 跳过 | ❌ 跳过 | 只靠标点 + 长度；无标点的轨质量会明显下降 |
| `none` | 理论上不该出现 | ❌ | ❌ | 直接报错，不产出课程 |

降级发生时**必须打印出来**，并写进 `buildMetadata.segmentation.timeResolution`。
一门 `cue-interpolated` 且 `。` 密度极低的课，应该建议改走 `--transcript asr`，而不是硬做。

---

## 12. 阶段 (9) 质量门：新增文本边界检查

加在 [`bundle_quality.py`](../src/bundle_quality.py)。没有这一节，前面全部修完也守不住下一批导入。

### 句级

| code | 级别 | 触发条件 |
|---|---|---|
| `sentence.multi_sentence` | warning | 非末尾位置出现 `。！？`，且其后还有 ≥4 字 |
| `sentence.fragment` | warning | 无句终标点，且（以助词开头 或 悬空助词结尾），且长度 < `MIN_CHARS` |
| `sentence.rate_implausible` | warning | 字符数 / 时长 > 20 字/秒 —— 文本和时间轴脱节（对上实测的「138 字挤进 3.0 秒」） |
| `sentence.over_length` | warning | 长度 > `MAX_CHARS` |

### 课程级

| code | 级别 | 触发条件 |
|---|---|---|
| `course.width_capped` | **error** | 18–22 字区间内任一长度值占比 > 25% |
| `course.unterminated_ratio` | warning | 无句终标点的句子 > 50%（`timeResolution == "token"` 时收紧到 30%） |
| `course.forced_cut_ratio` | warning | `forcedCuts / sentences` > 10% |

`course.width_capped` 设成 **error** 是这一节的关键。
它是唯一能识别「这门课是按显示行切的」的检查——单看任何一句都正常，只有分布能出卖它。
实测当前 12 门课全部会被它拦下，这正是期望行为。

---

## 13. 已有 12 门课的重建

**现在是最好的时机：这 12 门课的翻译讲解全部为 0 条，重建不浪费任何 enrichment。**

代价只有重新抓一次字幕轨（原始轨当时没留，见第 3 节）。

```powershell
# pageUrl 从现有 manifest 里取
python -c "import json;print(json.load(open(r'courses\tbs-news-0008-9ZrpJfIGrRI\manifest.json',encoding='utf-8'))['media']['pageUrl'])"

# 单门重建
python src\build_video_course.py --url "<原 pageUrl>" --language ja --profile deepseek
```

重建顺序建议：

1. 先做 `tbs-test-01`（1509 字、0 标点）——它是最难的 case，规则 B 和 C 的兜底在这门课上不成立就别往下推。
2. 再做 `tbs-0008`（204 句、195 字巨块、5 条 very_short）——两个极端都在这一门里。
3. 其余 10 门批量跑，用第 14 节的验收线卡结果。

**旧 manifest 先备份再覆盖**（仓库里已经有 `.bak` 的先例）。

`courseId` 由 `course_schema` 从远程媒体信息稳定推导，重建后不变；
但**句子 id 会变**，而生词、笔记、打卡是按 `courseId` + 句子 id 记录的——学习进度会对不上。
当前这批课还没有学习记录，可以忽略；**以后再重分句就必须先想清楚这件事。**

### 顺带：文本本身的质量

重建之前先认清一件事——`ann-news-ja` 的自动字幕**文本本身**错得很重：

```
美祢市→峰市    血まみれ→ちまみれ    店主→天手    鈍器→ドンキ
凶器→狂器      犯行→反抗            捜査→操作
```

**断句修好了，答案还是错的。** 按 VIDEO_COURSES.md 第 8 节，
`buildMetadata.subtitle.kind == "auto"` 且错误率高的课应该走 `--transcript asr` 用本地模型重转写。
本文档只负责把「显示行」还原成「句子」，不负责把错字改对——这是两个问题，不要混在一次改动里。

---

## 14. 验收标准

重建后每门课必须同时满足：

| 指标 | 目标 | 改动前实测 |
|---|---|---|
| 18–22 字区间任一长度占比 | < 25%（与质量门同阈值） | **36%**（18–19 字） |
| 句尾有终止标点 | ≥ 70%（`token` 档 ≥ 85%） | 33.2% |
| 一条含多个完整句 | **0** | 18.6% |
| 长度 > 45 字 | **0** | 7.5% |
| ≤4 字碎片且 practiceEligible | **0** | 12.8% 碎片 / 96.3% 可练 |
| 字符守恒 I1 | **必须通过** | 无此测试 |
| 质量门 error | **0 条** | 0 条（因为根本没检查） |

「改动前实测」一列是 2026-09-01 的 12 门课合计，作为基线保留在这里。

### 实测结果（2026-09-01 完成）

全部 20 门视频课重建后，**全库质量门 error = 0**：

| 指标 | 目标 | 改动前 | 改动后 |
|---|---|---|---|
| 18–22 字任一长度占比 | < 25% | 29–39%（8 门超标） | 3.6–8.3% |
| 一条含多个完整句 | 0 | 217 条 | **0** |
| 长度 > 45 字 | 0 | 78 条 | **0** |
| ≤4 字碎片且可练 | 0 | 155 条碎片 / 96.3% 可练 | **0** |
| 质量门 error | 0 | （无此检查） | **0** |
| 字符守恒 I1 | 通过 | 无此测试 | 通过 |

两条需要记录的例外：

1. **`tbs-test-01` 句终标点率仍是 0%。** 它的字幕轨整轨没有一个句号，这是来源属性，
   不是分句缺陷。它靠规则 B（停顿）切成 64 句，`forcedCuts = 0`——
   这门课正是第 1.3 节说的「必须有停顿兜底」的实证。
2. **`nhk-news-*` 那几门只有 2–6 句**，占比类指标在这种样本量下没有意义。
   质量门的 `WIDTH_CAP_MIN_SENTENCES = 20` 就是为此设的。

`course.width_capped` 的判据在实现时**从单一占比扩展为「占比 > 25% 或（断崖 ≥ 8 倍且占比 ≥ 8%）」**。
原因是实测发现：39 门 ASR 音频课的断崖上限是 4.0 倍，而按显示行切的课程是 13–53 倍，
断崖比占比判别力更强。加上这一条后，改动前的 12 门课被拦下 10 门（原为 8 门），
且 39 门音频课误报仍为 0。

---

## 15. 测试清单

| 测试 | 断言 |
|---|---|
| `test_media_sources.py::json3_keeps_token_times` | `segs[].tOffsetMs` 进了 `Segment.tokens`，绝对时间正确 |
| `test_media_sources.py::rolling_window_keeps_real_repetition` | `もう一度` / 8 秒后 `もう一度お願いします` 两条都在（守住现有保护） |
| `test_segmentation.py::char_conservation` | **I1**：重分句前后逐字相等 |
| `test_segmentation.py::monotonic_non_overlapping` | **I2** |
| `test_segmentation.py::deterministic` | **I4**：同一输入跑两次结果完全相同 |
| `test_segmentation.py::splits_on_terminal_punctuation` | 规则 A |
| `test_segmentation.py::splits_on_pause_without_punctuation` | 规则 B，喂无标点但带 token 时间的轨 |
| `test_segmentation.py::long_run_finds_secondary_boundary` | 规则 C，200 字无标点段被切到 ≤45 字，优先级顺序正确 |
| `test_segmentation.py::isolated_numeral_is_marker` | 规则 D 第三种情况 |
| `test_segmentation.py::no_token_times_degrades_cleanly` | `cue-interpolated` 档不崩、规则 B 跳过、`timeResolution` 记录正确 |
| `test_quality_gate.py::width_capped_is_error` | 拿一门现有课当 fixture，断言 `course.width_capped` 报 error |
| `test_video_course_pipeline.py` | 端到端：字幕轨 → manifest，满足第 14 节全部验收线 |

`test_quality_gate.py` 那条建议直接把现在的 `tbs-news-0008` manifest 当 fixture 存进 `tests/`：
它是一份真实的、坏得很典型的输入，比构造的样例更能守住回归。

---

## 16. 明确不改的东西

改动范围要收得住，以下全部保持原样：

- **版权立场**：视频从不下载、音频用完即删、`redistributable` 恒 false、发布和打包工具照旧拦截。
- **三档控制**（`full` / `seek-reload` / `external`）和播放器适配器。
- **CSP 三份副本一致**的约束。
- **安全边界**：页面不能构造 provider；URL 走 `parse_media_url` 重建后才进 argv；全程无 shell。
- **本地音频课流水线**：`build_course.py` 和 `merge_sentence_fragments` 在 ASR 路径上工作正常，不动。
- **manifest sentence schema**：不加字段（见第 9 节）。
- **`--clip` 不平移时间轴**。

`merge_sentence_fragments` 的处置：**保留给 ASR 路径，从字幕路径移除**。
它不是坏函数，只是被用在了一个它的前提（文本带标点）不成立的地方。

---

## 17. 文件与职责

| 路径 | 本次改动 |
|---|---|
| [`src/media_sources.py`](../src/media_sources.py) | `Segment` 加 `tokens`；`_parse_json3` 保留 `tOffsetMs`；`fetch_subtitles` 落盘原始轨；`_collapse_rolling_window` 语义收窄 |
| `src/video_segmentation.py`（新） | `CharStream` 构建 + 规则 A/B/C/D + 不变量校验。**纯函数，不 import 网络相关模块** |
| [`src/build_video_course.py`](../src/build_video_course.py) | 字幕路径改调新分句器；写 `buildMetadata.segmentation`；ASR 路径不变 |
| [`src/bundle_quality.py`](../src/bundle_quality.py) | 第 12 节的句级和课程级检查 |
| [`src/sentence_segmentation.py`](../src/sentence_segmentation.py) | 不改。仅从字幕路径的调用点移除 |
| `tests/test_segmentation.py`（新） | 第 15 节 |

把重分句放进**独立模块**而不是塞进 `media_sources.py`，理由和现有设计一致：
`media_sources.py` 是「唯一知道视频站点存在的模块」，而分句和视频站点无关——
它只认字符和时间，所以它应该能在没有网络、没有 yt-dlp 的环境里被测试。

---

## 18. 落地顺序

按这个顺序做，每一步都能独立验证：

| # | 做什么 | 验证 |
|---|---|---|
| 1 | `_parse_json3` 保留 token 时间 + 原始轨落盘 | 抓一份 json3，确认 `tOffsetMs` 非空比例 |
| 2 | `video_segmentation.py` + 不变量测试 | I1–I5 全绿，用步骤 1 存下的真实轨跑 |
| 3 | 质量门新增检查 | 现有 12 门课全部报 `course.width_capped` error |
| 4 | `build_video_course.py` 接线 | `tbs-test-01` 和 `tbs-0008` 达到第 14 节验收线 |
| 5 | 批量重建其余 10 门 | 全部 0 error |
| 6 | 更新 VIDEO_COURSES.md 第 7 节 | 「滚动窗口」一节要改写，它现在描述的是旧行为 |

步骤 3 排在 4 前面是故意的：**先让门能拦住坏东西，再去修**，
否则没有任何客观标准判断步骤 4 是不是真的做对了。
