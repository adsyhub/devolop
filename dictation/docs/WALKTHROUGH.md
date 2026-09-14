# 视频精听制作流水线升级与多播放列表课程制作总结

根据 [`docs/VIDEO_COURSE_PIPELINE.md`](file:///c:/Users/cribug/OneDrive/Desktop/dictation/docs/VIDEO_COURSE_PIPELINE.md) 完成了**四级重分句引擎与质量门拦截升级**，并完成了两个 YouTube 播放列表的高质量精听课程制作与重构。

---

## 🚀 核心架构升级 (对齐 VIDEO_COURSE_PIPELINE.md)

1. **Token 级时间戳与原始字幕落盘** ([`src/media_sources.py`](file:///c:/Users/cribug/OneDrive/Desktop/dictation/src/media_sources.py))：
   - 提取并保留 YouTube json3 中的 `tOffsetMs` 词级绝对时间戳，封装为 `Token(text, start)`。
   - `fetch_subtitles` 自动将原始字幕持久化到 `video-work/<name>/subtitles.<lang>.<fmt>` 与 `track.json`，实现重分句纯本地可复现。
2. **独立重分句引擎** ([`src/video_segmentation.py`](file:///c:/Users/cribug/OneDrive/Desktop/dictation/src/video_segmentation.py))：
   - 构建 `CharStream`，实现**规则 A（句终标点主力切分）**、**规则 B（Token 停顿切分）**、**规则 C（45 字上限次级切分）** 与 **规则 D（8 字下限合并与 marker 标记）**。
   - 严格保证 **I1 字符绝对守恒** 等 5 大不变量。
3. **文本边界质量门拦截** ([`src/bundle_quality.py`](file:///c:/Users/cribug/OneDrive/Desktop/dictation/src/bundle_quality.py))：
   - 增加 `course.width_capped`（18–22 字聚集超 25% 判定为 Error）、`sentence.multi_sentence`、`sentence.fragment` 等句级与课程级检查。
4. **自动化集成** ([`src/build_video_course.py`](file:///c:/Users/cribug/OneDrive/Desktop/dictation/src/build_video_course.py))：
   - 字幕路径全面接入 `video_segmentation.resegment`，并在 `buildMetadata.segmentation` 中完整记录分句统计与参数。

---

## 🎬 已生成的视频精听课程汇总

### 1. NHK 播放列表（新增 8 门高质量精听课）
播放列表：`https://www.youtube.com/playlist?list=PLcynJ47QaWNvG08VE_-ICzRpQlKmakmp-`

| 序号 | 课程目录 | 标题 | 状态 |
|:---|:---|:---|:---:|
| 01 | `nhk-news-0001-uAiNvInSb6c` | 次が見えるアプリ NHK ONE ニュース・防災アプリ | 4 句 (token 分句) |
| 02 | `nhk-news-0002-ygOeHL7QJIg` | 長期金利 3%に上昇 約30年ぶり 日銀の早期利上げ観測など背景 | 4 句 (token 分句) |
| 03 | `nhk-news-0003-LHGji8bNNKo` | 石川と富山 河川氾濫 堤防決壊も 川に近づかないよう呼びかけ | 3 句 (token 分句) |
| 04 | `nhk-news-0004-qLDgaZS8uJY` | 芸術家 草間彌生さん死去 97歳 水玉モチーフの作品で知られる | 3 句 (token 分句) |
| 05 | `nhk-news-0005-ucjy5vtVjsk` | 石川 富山にレベル5大雨特別警報 命の助かる行動を | 4 句 (token 分句) |
| 06 | `nhk-news-0006-UVH-G6juTfg` | 猛暑で消える？「雪渓」 北アルプス穂高連峰 | 4 句 (token 分句) |
| 07 | `nhk-news-0007-7ejapVm-GuE` | AI関連の展示会「フィジカルAI」に注目集まる 約100社が出展 | 4 句 (token 分句) |
| 08 | `nhk-news-0008-ZqK7sS66J1Q` | 福岡県議会 藏内議長「本日議員辞職する」理由説明せず | 3 句 (token 分句) |

### 2. TBS NEWS DIG 播放列表（前 10 门已基于新流水线全量重构）
播放列表：`https://www.youtube.com/playlist?list=PLhoNlZaJqDLb7bQe3wYDCxx-ZqKRHl-nB`

- `tbs-news-0001-0KeH-avaNI4` 至 `tbs-news-0010-M8IR-1CnA5s` 全部通过全新断句引擎重新生成，彻底消除了 18-19 字截断与半句分裂现象。

---

## 🎧 开始学习与使用

在终端启动本地精听服务：
```powershell
python .\start_dictation.py
```
在浏览器打开 **「🎧 精听」** -> **「视频精听」**，即可在所有新生成的课程间自由切换，享受完全对齐语法与语流的逐句听写、盲听遮挡与变速练习！
