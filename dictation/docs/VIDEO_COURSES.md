# 在线视频课程

用网上的视频做听力精听，**视频本身从不下载**。

本地音频课程走 [COURSE_PIPELINE.md](COURSE_PIPELINE.md)；这一份讲的是另一种课程：
媒体在别人的服务器上，本地只留时间轴、逐句文本和我们自己写的翻译讲解。

---

## 1. 版权立场

这不是一句承诺，是代码结构：

| 事实 | 由什么保证 |
|---|---|
| 视频从不下载 | 没有任何代码路径会取视频流。`yt-dlp` 只被用来取字幕轨或音频轨。 |
| 音频用完即删 | `media_sources.temporary_audio` 是上下文管理器，在 `finally` 里整个删掉临时目录——异常路径也删，`.part` 残留一并带走。 |
| 课程不可再分发 | manifest 的 `media.attribution.redistributable` 恒为 `false`，`course_schema` 强制改写，审计会拒绝声称可分发的清单。 |
| 发布工具会拦住它 | `release_readiness.py` 报 `redistributable_media` 阻断项；`content_license.py` 拒绝建立版权台账（`RemoteMediaNotLicensable`）。 |
| 打包工具会拦住它 | `repack_offline_bundle.py` 拒绝；`review_server.py` 说明它只支持本地音频课程，而不是报「manifest.audio 缺失」这种误导信息。 |

逐句文本来自站点自己的字幕，或来自本地转写。翻译和讲解是我们生成的。
**这门课只能自己学，不能打包卖，也不能公开分发。** 项目文档第 9 节那句
「技术文件完整不等于取得授权」在这里同样成立，而且更严格。

---

## 2. 三档控制等级

不同站点开放给页面的能力差别极大。我们不假装它们一样：

| 档位 | 站点 | 精听能做到什么 | 做不到什么 |
|---|---|---|---|
| `full` | YouTube、Vimeo | 逐句自动循环、盲听、听 N 遍、变速、精确定位 | —— |
| `seek-reload` | 哔哩哔哩，以及可嵌入但无控制接口的站点 | 点句子把播放器重载到该句开头，可反复重播 | 没有自动循环，页面读不到播放进度，无法程序化暂停 |
| `external` | 拒绝被嵌入的站点（大多数新闻站） | 逐句字幕 + 听写题 + 「在原站 mm:ss 打开」深链 | 页面内不播放 |

档位由 `media_sources.parse_media_url` 判定，写进 manifest 的 `media.control`，
播放器据此决定显示哪些控件。UI 会直说这门课属于哪一档、失去了什么——
**一个点了没反应的循环按钮，比没有这个按钮糟得多。**

YouTube 还有一个额外的降级路径：上传者可以禁止站外嵌入（播放器错误码 101/150）。
这对新闻频道很常见。遇到时播放器不会卡死，而是切到 `external` 呈现并说明原因，
学习进度不丢。

---

## 3. 安装 yt-dlp（可选）

只有「抓站点字幕」和「临时取音频转写」这两条路径需要它。用本地字幕文件建课不需要。

```powershell
pip install yt-dlp
```

没装时：命令行会打印 `pip install yt-dlp` 并停下；工作台会在探测结果里显示
「yt-dlp 未安装」，而不是抛异常。

---

## 4. 命令行

```powershell
python src\build_video_course.py --url "<视频链接>" [选项]
```

### 4.1 日语新闻，用站点字幕

```powershell
python src\build_video_course.py `
  --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" `
  --language ja --profile deepseek
```

人工字幕优先于自动字幕。找到自动字幕时会额外做**滚动窗口去重**（见第 7 节）。

成品建议使用双源核验：

```powershell
python src\build_video_course.py `
  --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" `
  --language ja --transcript verified --asr-profile japanese-accurate `
  --profile local-flash-next --resume
```

它会同时处理站点字幕和本地 ASR，以确定性质量规则选源，并在工作目录保存
`transcript-verification.json`。自动字幕与 ASR 同分时选 ASR；人工字幕同分时选人工字幕。

### 4.2 英语视频

```powershell
python src\build_video_course.py `
  --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" `
  --language en --sub-langs en,en-US --profile deepseek
```

### 4.3 没有字幕：临时取音频跑本地转写

```powershell
python src\build_video_course.py `
  --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" `
  --language ja --transcript asr --asr-profile japanese-accurate --profile deepseek
```

`--transcript auto`（默认）会先找字幕，找不到自动走这条路。
若你不希望它这样做，加 `--no-audio-fetch`，没有字幕时直接失败。

构建过程会明确打印音频落盘和删除这两件事。

### 4.4 非 YouTube 站点

```powershell
python src\build_video_course.py --url "https://www.bilibili.com/video/BVxxxxxxxxxx" --profile deepseek
```

b23.tv 短链接无法离线解析，请在浏览器打开后复制地址栏的完整链接。

### 4.5 用你自己的字幕文件

零网络、零依赖：

```powershell
python src\build_video_course.py `
  --transcript file --subtitles .\talk.srt `
  --page-url "https://www.youtube.com/watch?v=XXXXXXXXXXX" `
  --profile deepseek
```

支持 `.srt` / `.vtt` / `.json3`。若这个文件本身是从自动字幕导出的，
加 `--rolling-window` 让它也走去重。

### 4.6 只学其中一段

长视频只取一段来精听：

```powershell
--clip 2:30 8:00
```

接受秒、`mm:ss`、`h:mm:ss`。**句子时间轴始终是视频的绝对时间**，
`clip` 只决定这门课覆盖哪一段，不会把时间轴平移。

### 4.7 常用选项

| 选项 | 作用 |
|---|---|
| `--transcript verified\|auto\|subs\|asr\|file` | 逐句文本来源；CLI 默认 `auto`，工作台默认 `verified` |
| `--no-audio-fetch` | 禁止 `auto` 回退取音频；与 `verified` 同用会直接失败 |
| `--sub-langs ja,ja-JP,en` | 字幕语言优先顺序 |
| `--name FOLDER` | `courses/<FOLDER>`，默认由标题生成 |
| `--content-patch PATCH.json` | 应用已审核、与当前句子摘要绑定的原文修正；可重复 |
| `--resume` | 只复用与视频、ASR 配置、批次原文和文本 provider 一致的缓存 |
| `--no-enrich` | 不生成翻译讲解 |
| `--dry-run` | 只打印计划，不抓取不调用不写入 |
| `--list-profiles` | 列出配置里可用的 profile |

provider 只能按 **profile 名**选择。`--kind`/`--model`/`--command` 这类临时构造
provider 的参数只在 `build_course.py` 有，这里刻意不提供——工作台要用同一套 argv。

---

## 5. 制课工作台

```powershell
python src\studio_server.py
```

在「1 · 准备」里切到 **在线视频** 标签：

1. 粘贴链接 → 点 **探测**。会显示站点、控制档、标题、时长、可用字幕语言，
   以及 yt-dlp 是否可用。
2. 选逐句文本来源（已验证双源核验 / 快速自动 / 只用站点字幕 / 直接本地转写）。
3. 可选：填剪辑窗口。
4. 选翻译讲解 profile（和音频流程同一份列表）。
5. **开始制作** → 同一个流式日志 → 完成后课程已经在 `courses/` 里。

视频课直接写进课程库，没有 ZIP，所以没有「装入课程库」这一步。

### 安全边界

工作台原有的两条边界（页面不能构造 provider；音频只能上传不能给路径）不变。
在线视频引入了第三类不可信输入：**请求体里的 URL 最终会成为 yt-dlp 的 argv 元素**。
处理方式：

- 服务端用 `parse_media_url` 校验，拒绝非 http(s)、带凭据、非标准端口、IP 字面量、
  localhost、含控制字符、以 `-` 开头的 URL；
- 进 argv 的是**我们自己的解析器重建出的规范 URL**，不是浏览器发来的字符串；
- 全程 argv 列表，没有 shell；
- 字幕语言、剪辑窗口都在服务端收敛成语言标签和数字才进 argv；
- 构建子进程照旧剥掉 `DICTATION_SESSION_TOKEN`。

`tests/test_studio_server.py` 的 `OnlineVideoTests` 逐条验证这些。

---

## 6. 精听怎么练

打开课程后（`python start_dictation.py --manifest courses\<name>\manifest.json`）：

| 操作 | 效果 |
|---|---|
| 默认进入听写模式 | **盲听默认开启**：画面被遮住，声音照常播放 |
| `空格` | 播放 / 暂停当前句 |
| `←` `→` | 上一句 / 下一句 |
| 「听 N 遍」 | 本句连续播 N 遍后停下，是标准精听节奏 |
| 「循环」 | 一直循环本句 |
| 速度选择 | 走适配器；YouTube 只接受固定档位，会吸附到**不超过你所选**的那一档 |
| `Ctrl + Enter` | 提交答案，出现逐字差异、翻译、讲解 |
| 「盲听」按钮 | 想看画面时点开 |

盲听默认开着是有原因的：新闻视频经常把答案以字幕形式烧在画面里，
看着画面做听写就不是听力练习了。同理，嵌入播放器一律带 `cc_load_policy=0`，
不显示站点自己的字幕。

`seek-reload` 档没有自动循环，用「重播本句」代替；
`external` 档用每句的「在原站 mm:ss 打开」按钮。

---

## 7. 从字幕到句子

站点字幕给的是**显示行**，不是句子。两个伪影叠在一起，必须分两步处理。

### 7.1 滚动窗口（去重复）

YouTube 自动字幕不是一句一条，而是一个滚动窗口：相邻 cue 会重复上一条的尾巴。

```
00:01.0 → 00:02.2   今日の
00:02.2 → 00:05.0   今日のニュースをお伝えします
00:05.0 → 00:09.0   ニュースです。次は天気です
```

直接导入会做出一门「每句都重复上句一半」的课。`clean_segments` 做两件事：

1. 后一条以前一条为前缀时，合并成一条，保留**较早的开始时间**（说话确实是那时开始的）；
2. 相邻两条在接缝处重叠时，把重叠部分从后一条切掉。

两条都只在**时间紧邻**（间隔 ≤ 0.75 秒）时生效。这个保护是必要的：
`もう一度` 和 8 秒后的 `もう一度お願いします` 是两句真话，不是伪影，
没有邻接判断就会被吞掉一句。

人工字幕**不做**这个处理——它本来就没有这个伪影，而合并可能吃掉真实的重复。
`fetch_subtitles` 知道拿到的是哪一种，`clean_segments` 不猜。

**去重之后得到的仍然是显示行，不是句子。** 这一步只负责「不重复」。

### 7.2 重分句（定句界）

去重后的 cue 交给 [`src/video_segmentation.py`](../src/video_segmentation.py)，
它把所有 cue 摊平成一条「每个字符都带时间」的流，丢掉 cue 边界，重新找真正的句界：

| 规则 | 依据 |
|---|---|
| A 句终标点 | 在 `。！？` 之后切。日语自动字幕**是带句号的**，只是句号落在显示行中间 |
| B 停顿 | 字符间静音 ≥ 0.6 秒处切。需要 token 级时间（见 7.3） |
| C 长度上限 | 仍超过 45 字的段，按 读点 → 软停顿 → 接续助词 → 接续词 的优先级再切，目标 24 字 |
| D 碎片合并 | 不足 8 字的段并入时间上紧邻的邻段；**不跨句号合并**；并不动的标 `marker`，不进听写队列 |

规则 D 那条「不跨句号」不是细节：少了它，一个孤立的 `うん。` 会并进下一句，
做出「句子中间有句号」的条目——正是这套东西要消灭的缺陷。

最重要的约束是**字符守恒**：所有句子拼起来必须和输入的字符流逐字相等，
有测试守着（`tests/test_segmentation.py`）。它把「分句」和「改文本」彻底分开，
任何吃字的 bug 都会被它逮住。

### 7.3 三档时间精度

能不能用规则 B，取决于字幕轨给不给逐词时间：

| 档位 | 来源 | 规则 B | 后果 |
|---|---|---|---|
| `token` | json3 自动轨（`segs[].tOffsetMs`） | ✅ | 完整能力 |
| `cue-interpolated` | vtt / srt / 无 offset 的 json3 | ❌ | 只靠标点和长度 |
| `none` | 空轨 | ❌ | 不产出课程 |

档位写进 `buildMetadata.segmentation.timeResolution`，构建时也会打印。
这不是学术区分：有一门实测课程整轨 1509 字、**零个句终标点**，
只有 `token` 档的停顿规则能把它切开。

### 7.4 原始轨会留下来

`fetch_subtitles` 把抓到的字幕轨写进 `video-work/<name>/subtitles.<lang>.<fmt>`，
附一份带 sha256 的 `track.json`。**调参数、修 bug、重新分句都不必再联网。**

存的是字幕文本，不是媒体——版权立场不变：`temporary_audio` 仍然用完即删，
`video-work/` 已 gitignore，不进 ZIP，不进 `courses/`。**字幕留，音频不留。**

### 7.5 质量门会拦住退化

`bundle_quality` 有一条课程级 **error**：`course.width_capped`。
它看长度分布——按显示行切的课程会把 29–39% 的句子堆在同一个长度上，
且到下一个长度有 13–53 倍的断崖；而 39 门 ASR 音频课的峰值只有 6.4%、断崖最多 4.0 倍。
**单看任何一句都正常，只有分布能出卖它。**

配套的警告：`sentence.multi_sentence`、`sentence.fragment`、`sentence.over_length`、
`course.unterminated_ratio`、`course.forced_cut_ratio`（只对字幕来源的课程生效），
以及 `sentence.rate_implausible`（所有课程——没人能一秒说 20 个字，
它只在文本被改而时间轴没跟着走时才响）。

完整规格见 [VIDEO_COURSE_PIPELINE.md](VIDEO_COURSE_PIPELINE.md)。

---

## 8. 排错

| 现象 | 原因与处理 |
|---|---|
| `找不到 yt-dlp` | `pip install yt-dlp`，或 `--ytdlp <路径>` |
| `站点没有可用字幕` | 用 `--transcript asr` 走本地转写，或自己提供 `--subtitles` |
| 播放器提示「上传者禁止了站外嵌入播放」 | YouTube 错误 101/150。播放器已自动切到原站深链模式，照常能练 |
| 页面里视频框空白 | 站点拒绝被嵌入。课程会是 `external` 档，用深链按钮 |
| 视频不动、控制台报 CSP 错误 | 检查 CSP 是否被改窄。三份副本（`serve_course.py`、`index.html` 的 meta、`_headers`）必须一致，有测试守着 |
| 自动字幕质量差 | 换 `--transcript asr` 用本地模型重转写，通常比自动字幕准 |
| 视频在你所在地区被封 | yt-dlp 会报错。换视频，或自己拿到字幕后用 `--transcript file` |
| 视频太长 | 用 `--clip` 只取一段。一次精听 3–5 分钟比 30 分钟有效得多 |
| `这看起来是 YouTube 链接，但取不出 11 位视频 ID` | 用视频页地址栏的完整链接，不要用分享短链的变体 |

---

## 9. CSP 增加了哪些域名

播放器的 CSP 为此放宽了几处，每一处只为一个原因：

| 指令 | 域名 | 为什么 |
|---|---|---|
| `script-src` | `www.youtube.com` | IFrame Player API 的加载脚本 `/iframe_api` |
| `script-src` | `s.ytimg.com` | 上面那个脚本再拉的 widget 包 |
| `frame-src` | `www.youtube-nocookie.com`、`www.youtube.com` | 嵌入的播放器本身 |
| `frame-src` | `player.vimeo.com`、`player.bilibili.com` | 另外两档可嵌入站点 |
| `img-src` | `i.ytimg.com`、`img.youtube.com` | 视频缩略图 |
| `connect-src` | `www.youtube.com` | 播放器自己的配置与统计请求 |

`frame-ancestors 'none'` **保持不变**——它管的是谁可以嵌入我们，
不是我们可以嵌入谁。没有任何 `*` 或 `'unsafe-inline'`，有测试守着。

---

## 10. 相关文件

| 路径 | 用途 |
|---|---|
| `src/media_sources.py` | 唯一知道视频站点存在的模块：URL 识别、字幕解析（含 token 级时间）、清洗、原始轨落盘、yt-dlp 封装 |
| `src/video_segmentation.py` | 重分句：字符时间流 + 四条规则 + 不变量。纯函数，不认识视频站点，无网络即可测 |
| `src/build_video_course.py` | 构建入口，复用 `build_course.py` 的转写与 enrichment |
| `src/web/media_adapters.js` | 三档控制的播放适配器，接口刻意做成 HTMLMediaElement 的形状 |
| `src/course_schema.py` | `media` 块的规范化与远程课的稳定 `courseId` |
| `src/bundle_quality.py` | 远程媒体审计 |
| `tests/test_media_sources.py` | URL 拒绝、字幕解析、清洗、yt-dlp 桩 |
| `tests/test_segmentation.py` | 四条规则、字符守恒等不变量、无 token 时间的降级 |
| `tests/test_video_course_pipeline.py` | 端到端构建 |
| `tests/media_adapters.test.mjs` | 适配器状态机与降级路径 |
| `tests/test_remote_media_player.py` | 服务远程课 + CSP 三份一致 |

### 10.1 与现有功能的接口

| 接触点 | 行为 |
|---|---|
| 切换课程（播放器） | 视频课带 `🎬 YouTube · 可完全控制` 前缀，一眼能和音频课区分 |
| `CourseStore.list_courses` | 每行多出 `mediaKind` / `mediaProvider` / `mediaControl` / `pageUrl`，原有字段不变 |
| `install_course.install_bundle` | 没有媒体成员的 ZIP 可以正常安装（`bundle_io.verify_zip` 同步放行） |
| `serve_course.py` | 不再要求本地音频文件；质量门照常拦截审计失败的课程 |
| Service Worker | 只缓存 manifest；跨源媒体永不进 Cache Storage |
| 学习数据 | 生词、笔记、进度按 `courseId` + 句子 ID 记录，和音频课走同一套 SQLite |
