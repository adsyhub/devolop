# JLPT 题库听力音频功能实现指导

> 文档性质：可执行的设计与实施说明，不包含本次功能代码改动。  
> 适用项目：当前仓库中的 `exams/` 真题系统、`courses/` 听力课程和本地预览服务。  
> 目标：开发者按本文实施后，JLPT 真题的听力章节可以播放项目中已有的配套音频，同时保留当前题库的练习、模考、专题练习、错题本与安全边界。

---

## 1. 结论与推荐实现

推荐采用下面这条实现路线：

1. `courses/<试卷 slug>/` 是音频的唯一正式运行时来源，例如：
   `courses/2017-07-N2/manifest.json` + `courses/2017-07-N2/audio.mp3`。
2. 在 `exam-meta.json` / 生成后的 `exam.json` 中增加一个可选的
   `listeningMedia` 显式引用，把试卷绑定到某个已安装课程，并记录音频哈希和字节数。
3. 服务端新增同源媒体地址
   `GET|HEAD /exam-media/<exam-slug>/audio`，从课程目录流式读取音频，并正确支持
   `Range`、`206` 和 `416`。
4. 答题页只保留一个 `<audio>` 实例。进入听力题时显示播放器；同一套卷翻题时不重置音轨，
   让整段官方录音连续播放。
5. 专题练习跨多套试卷时，根据当前题目的来源 slug 切换音频，并为每套试卷分别保存播放位置；
   切换后不自动播放，避免浏览器自动播放限制和错放另一套卷的录音。
6. 没有音频的试卷仍可打开、判分和复习答案，只显示准确的缺失原因；媒体缺失不能让整套笔试
   被质量门禁封锁。
7. 第一版不自动跳到“当前小题”。现有课程转写虽然有 `問題1`、`1番` 等 ASR marker，
   但没有可靠的 `questionId -> 时间点` 映射，自动猜测会把用户带到错误录音。首版使用整段音轨已经
   符合真实 JLPT 连续播放方式；题目级定位放到第二阶段，通过经人工核验的 cue 文件实现。

这条路线不复制音频、不依赖工作目录、不泄漏本机路径，也不需要把 API 会话令牌塞进媒体 URL。

---

## 2. 当前项目事实

### 2.1 前端已经识别听力题，但逻辑写死为“无音频”

当前页面已通过 `section.audioRequired` 区分听力和笔试：

- `src/web/exam.js` 的 `renderQuestion()` 会对听力章节显示 `#audio-warning`；
- `renderSetup()` 固定写着“听力部分没有配套音频，只能对照答案复习”；
- `src/web/exam.html` 只有缺音频警告，没有 JLPT 音频元素；
- 题库首页和专题入口已经用“🔊 听力”标识听力题型；
- `buildTopicExam()` 已有 `questionSource: questionId -> exam slug` 映射，这正好可以用于
  跨试卷专题练习时选择音频。

因此题型识别无需重做，缺的是“媒体绑定、服务端输送、播放器状态”这三层。

### 2.2 音频在课程库和工作目录中，不在 `exams/`

项目内可以看到两类音频：

- 正式已安装课程：`courses/<slug>/audio.mp3`；
- 构建工作目录：`n1-jingting-work/<slug>/audio.mp3`、
  `n2-jingting-work/<slug>/audio.mp3`。

同名课程的 `manifest.json` 已包含：

- `audio`：安全的根目录文件名，当前通常是 `audio.mp3`；
- `buildMetadata.sourceAudioSha256`；
- `buildMetadata.sourceAudioBytes`；
- 带 `startTime` / `endTime` 的转写句段。

运行时只能读取 `courses/`。`*-jingting-work/` 是中间产物，可能缺 manifest、质量报告未通过，
也可能在下一次构建时被替换。工作目录中的课程应先通过 `src/install_course.py` 安装，再与试卷绑定。

可用下面的 PowerShell 盘点当前实际匹配情况；不要把一次盘点得到的数量硬编码进程序：

```powershell
$examSlugs = Get-ChildItem .\exams -Directory | ForEach-Object Name
foreach ($slug in $examSlugs) {
  $courseAudio = Test-Path -LiteralPath ".\courses\$slug\audio.mp3"
  $n1WorkAudio = Test-Path -LiteralPath ".\n1-jingting-work\$slug\audio.mp3"
  $n2WorkAudio = Test-Path -LiteralPath ".\n2-jingting-work\$slug\audio.mp3"
  [pscustomobject]@{
    Slug = $slug
    Installed = $courseAudio
    WorkOnly = (-not $courseAudio) -and ($n1WorkAudio -or $n2WorkAudio)
  }
}
```

本次分析时已验证的正式匹配示例包括 `2010-07-N1`、`2010-12-N1`、`2011-12-N1`，
以及多套 N2。也验证了课程目录与工作目录中若干同名音频的 SHA-256 完全相同。

### 2.3 当前服务只能直接提供“正在预览的课程音频”

`src/serve_course.py` 启动时会把当前课程的 manifest 和音频复制到临时 web 目录，
所以 `/audio.mp3` 只代表当前听写课程，不代表题库里任意一套试卷。

服务端已有正确的 Range 算法：

- `parse_range_header()`；
- `PreviewHandler.serve_range_request()`；
- `tests/test_range_requests.py` 对显式区间、开放区间、后缀区间、重复 seek 和 `416` 已有回归。

新增题库音频时应复用/抽取这套能力，不能用 `read_bytes()` 把 20–50 MB 音频整体读入内存。

### 2.4 题目级时间点目前不能可靠自动生成

课程转写中可以找到 `contentType: "marker"`，文本也常出现 `問題1`、`1番`，但它们存在：

- ASR 把 marker 和正文合并；
- 数字漏识别或错识别；
- `問題5` 一段录音可能对应多个计分问题；
- 例题和重复朗读会造成编号重复；
- 句段没有 `questionId`。

因此不能用“正则搜第一个 `1番`”直接驱动自动 seek。错误时间点比没有自动定位更糟，因为用户会在
不知情时听错题。

---

## 3. 第一阶段的产品范围

### 3.1 必须完成

- 题库列表能显示某套卷“音频可用 / 暂无音频”。
- 试卷设置页不再统一声称没有音频，而是根据真实状态显示：
  - “听力音频已就绪”；
  - “未配置配套音频”；
  - “已配置但文件缺失/校验失败”。
- 当前题属于 `audioRequired` 章节且媒体可用时，显示播放器。
- 播放器至少支持：播放/暂停、系统原生 seek、当前时间/总时长、音量和播放速度。
- 同一套卷在上一题/下一题之间切换时不重新设置 `src`，不回到 0 秒，也不打断正在播放的音频。
- 从听力题切到笔试题、离开答题页或交卷时暂停音频并保存当前位置。
- 再回到同一套卷的听力题时恢复本次会话的位置，但不自动播放。
- 专题练习只默认纳入“音频可用”的来源试卷；界面说明有多少套因为无音频未纳入。
- 专题练习从 A 卷题目切到 B 卷题目时，先暂停 A、保存 A 的位置、切换到 B、恢复 B 的位置；
  不允许继续播放 A 的音频却显示 B 的题。
- 媒体接口支持 `GET`、`HEAD`、单 Range、开放 Range、后缀 Range和非法 Range。
- 音频路径不能由客户端任意指定，不能发生目录穿越，也不能把本机绝对路径返回给浏览器。
- 没有音频或音频损坏不会影响笔试作答、判分、错题本和历史记录。

### 3.2 第一阶段明确不做

- 不自动定位每道小题；
- 不自动播放，避免浏览器用户手势限制；
- 不把题库音频离线写入 Service Worker Cache Storage；
- 不复制一份音频到每个 `exams/<slug>/`；
- 不从 `n1-jingting-work/` / `n2-jingting-work/` 在线提供文件；
- 不把会话 token 放在查询字符串；
- 不在数据库记录播放位置；第一版的播放位置只需保留在当前页面会话中。

---

## 4. 数据契约

### 4.1 在 `exam-meta.json` 中声明音频引用

推荐增加下面这个可选字段：

```json
{
  "listeningMedia": {
    "kind": "course-audio",
    "courseSlug": "2017-07-N2",
    "expectedSha256": "0f2f832f0b3894d1ae717e76d7542bf79f5b56b073a4425aef1f0e3c2dcc4ce4",
    "expectedBytes": 22937364
  }
}
```

字段约束：

| 字段 | 规则 |
|---|---|
| `kind` | 第一版只接受固定值 `course-audio` |
| `courseSlug` | 课程目录名，不是 manifest 内部的 `courseId`；必须是安全单段 slug |
| `expectedSha256` | 64 位小写十六进制，绑定具体音频内容 |
| `expectedBytes` | 正整数，用于快速发现截断、替换和同步未完成 |

不要在这里存：

- `C:\...\audio.mp3` 这类绝对路径；
- `../` 相对路径；
- work 目录路径；
- 直接可访问 URL；
- token。

文件名也不必重复存。服务端应读取目标课程自己的 `manifest.audio`，再用安全文件名规则解析。

### 4.2 由 importer 把引用带入 `exam.json`

`exam.json` 是生成物，不应逐套手改。修改 `src/exam_import.py` 的 `assemble_exam()`：

1. 从 `exam-meta.json` 读取 `listeningMedia`；
2. 如果存在，将其复制到组装出的顶层 exam 对象；
3. 再调用 `prepare_exam()` 和 `audit_exam()`；
4. 重新 assemble 目标试卷。

这是可选、向后兼容的 schema v1 扩展：旧试卷没有 `listeningMedia` 时仍可正常使用，只是
媒体状态为 `unconfigured`。不需要为了这个可选字段立刻把整个试卷 schema 升到 v2。

### 4.3 Schema 与内容修订规则

在 `src/exam_schema.py` 中增加校验：

- `listeningMedia` 不存在：合法；
- 存在但不是对象：`exam.listening_media_invalid`；
- `kind` 不支持：`exam.listening_media_kind_invalid`；
- slug 不安全：`exam.listening_media_slug_invalid`；
- hash 格式错误：`exam.listening_media_hash_invalid`；
- bytes 非正数：`exam.listening_media_bytes_invalid`。

“配置格式不安全”属于内容错误，可以让试卷审计失败；“运行时找不到物理文件”不属于 exam 内容错误，
不能让整套试卷返回 `422`。

建议把规范化后的 `listeningMedia` 配置加入 `content_revision()` 的输入。这样绑定了另一条音轨后
revision 会变化，但 `examId` 和问题 ID 保持不变，学习记录不会丢失。

### 4.4 服务端交付 DTO

磁盘上的 `listeningMedia` 是配置，API 返回给浏览器的是解析后的状态。建议形状如下：

```json
{
  "listeningMedia": {
    "kind": "course-audio",
    "courseSlug": "2017-07-N2",
    "available": true,
    "status": "ready",
    "url": "./exam-media/2017-07-N2/audio",
    "bytes": 22937364,
    "revision": "0f2f832f0b3894d1ae717e76d7542bf79f5b56b073a4425aef1f0e3c2dcc4ce4"
  }
}
```

允许的状态建议固定为：

| status | 含义 | 是否显示播放器 |
|---|---|---|
| `ready` | 引用、课程 manifest、音频文件和快速校验都正常 | 是 |
| `unconfigured` | 试卷没有绑定音频 | 否 |
| `course-missing` | 绑定的课程不存在 | 否 |
| `manifest-invalid` | 课程 manifest 无法读取或 `audio` 不安全 | 否 |
| `file-missing` | manifest 指向的文件不存在 | 否 |
| `size-mismatch` | 实际大小与绑定值不一致 | 否 |
| `hash-mismatch` | 实际 SHA-256 与绑定值不一致 | 否 |

返回给浏览器的错误状态不要包含本机文件路径。详细路径可以只写本地服务日志。

`GET /api/exams` 的 summary 至少返回 `available` 和 `status`，让列表页无需加载整卷就能显示徽标；
`GET /api/exams/<slug>` 返回完整交付对象和媒体 URL。

---

## 5. 正式音频的安装与批量绑定

### 5.1 先把 work 产物安装到 `courses/`

对于 work 目录里已有完整 `course.zip` 的试卷，使用项目现有安装器：

```powershell
python .\src\install_course.py `
  ".\n2-jingting-work\2021-12-N2\course.zip" `
  --name 2021-12-N2
```

N1 同理。安装前后执行：

```powershell
python .\src\install_course.py --list
```

只有质量审计通过、`manifest.json` 和音频都存在的课程才能绑定。只有 `audio.mp3`、没有可审计
manifest 的 work 目录不能直接作为运行时来源，应先补完课程构建流程。

### 5.2 增加批量绑定脚本

建议新增 `scripts/link_exam_audio.py`，不要人工复制几十个 hash。脚本至少支持：

```text
python scripts/link_exam_audio.py --all-by-slug --dry-run
python scripts/link_exam_audio.py --exam 2017-07-N2 --course 2017-07-N2 --write
python scripts/link_exam_audio.py --all-by-slug --write
```

脚本流程：

1. 找 `exams/<exam-slug>/exam-meta.json`；
2. 找 `courses/<course-slug>/manifest.json`；
3. 校验 manifest 的 `audio` 是安全根文件名；
4. 校验音频是普通文件且非空；
5. 对实际文件计算 SHA-256 和 bytes，不能只相信 manifest 自报值；
6. 如果 manifest 的 `buildMetadata.sourceAudioSha256/sourceAudioBytes` 存在，要求与实际文件一致；
7. 更新 `exam-meta.json` 的 `listeningMedia`；
8. 用该试卷的 `pages/`、`answer-key.txt`、`exam-meta.json` 重新 assemble 到临时文件；
9. validate 通过后再原子替换 `exam.json`；
10. 输出 `linked / skipped / failed` 汇总。

`--all-by-slug` 只匹配同名目录，不能靠标题模糊匹配年份和 N 级别。模糊匹配很容易把 7 月与 12 月、
N1 与 N2 音频绑错。

建议脚本默认 dry-run；`--write` 才落盘。已有不同绑定时拒绝覆盖，除非明确传 `--force`。

---

## 6. 服务端实现

### 6.1 增加媒体解析器

建议在 `src/exam_store.py` 中增加独立的 `ExamMediaResolver`，不要把文件查找散落到 HTTP handler：

```text
ExamMediaResolver
  inspect(exam_slug, exam) -> delivery status
  resolve_path(exam_slug, exam) -> validated Path + metadata
```

构造参数为 `courses_root` 或现有 `CourseStore`。职责：

1. 读取 exam 的 `listeningMedia` 配置；
2. 校验 `courseSlug`；
3. 通过 `CourseStore.get_manifest_path(courseSlug)` 找课程，不能用客户端传入的路径；
4. 读取课程 manifest；
5. 校验 `manifest.audio` 是单个安全文件名；
6. `resolve()` 后确认音频仍位于目标课程目录内；
7. 检查文件、字节数和期望 hash；
8. 构造不含绝对路径的 DTO。

快速列表接口不应每次给全部音频重算 SHA-256。推荐两级校验：

- `inspect()`：检查配置、manifest、文件存在、实际 bytes、manifest 自报 hash 与 exam 期望 hash；
- 第一次真正打开媒体时：对实际音频计算 SHA-256，并按
  `(resolved path, size, mtime_ns)` 缓存结果。

这样既不会让 `/api/exams` 因扫描数百 MB 变慢，又能在播放前发现同大小替换文件。

### 6.2 把 resolver 注入现有服务

修改 `build_preview_server()`：

1. 已有 `resolved_courses_root` 和 `course_store`；
2. 创建 `ExamMediaResolver(course_store)`；
3. 让 `ExamStore.list_exams()` / `get_exam()` 使用 resolver 注入交付状态；
4. 把 resolver 绑定到 `BoundHandler`，供媒体 endpoint 使用。

不要根据“当前激活听写课程”决定题库音频。切换听写课程不应改变题库任意试卷的媒体映射。

### 6.3 新增非 API 的同源媒体 endpoint

推荐路径：

```text
GET  /exam-media/<exam-slug>/audio
HEAD /exam-media/<exam-slug>/audio
```

不要放在 `/api/` 下。当前 `/api/*` 每次请求需要 `X-Dictation-Token`，而浏览器原生 `<audio>`
不能为分段媒体请求稳定添加自定义 header。以下替代方案都不要使用：

- `?token=...`：会进入历史、日志、截图或错误报告；
- 先 `fetch()` 整个音频再转 Blob：会等待完整下载并占用几十 MB 内存；
- 放宽整个 `/api` 的 token 校验：破坏个人数据 API 的边界。

媒体 endpoint 应走当前静态资产使用的 `SecurityContext.authorize_static()`：限制 loopback Host，
和当前 `/audio.mp3` 的保护方式一致。它不需要访问学习记录，也不返回个人数据。

路由处理顺序建议：

```text
do_GET
  /api/*                    -> 原有 token API
  authorize_static          -> 原有 Host 校验
  /exam-media/*             -> 新媒体路由
  普通静态 Range            -> 原有静态文件路由
  普通静态文件              -> SimpleHTTPRequestHandler
```

`do_HEAD` 使用同样顺序。

### 6.4 抽取通用流式文件方法

把当前 `serve_range_request()` 中的核心逻辑抽为可接收已验证 `Path` 的方法，例如：

```python
serve_file_path(path: Path, *, include_body: bool, range_header: str | None) -> None
```

必须保持：

- 无 Range：`200`；
- 有效 Range：`206 Partial Content`；
- 不可满足 Range：`416` + `Content-Range: bytes */<size>`；
- `Content-Length` 精确；
- `Accept-Ranges: bytes`；
- `Content-Range` 精确；
- MIME 从实际音频文件推导，mp3 应为 `audio/mpeg`；
- 先 `seek(start)`，再以最多 64 KiB block 循环读取；
- 吞掉浏览器正常提前关闭导致的 `BrokenPipeError` / reset；
- `HEAD` 发送与 GET 相同的响应头，但不发送 body。

注意：`translate_path(self.path)` 只能继续用于临时 web 根目录。题库音频必须使用 resolver 已验证的
Path，不能把 URL 直接拼成本机路径。

### 6.5 错误响应

- 不存在/未配置：`404`；
- 配置不安全：试卷审计阶段应已拦截；endpoint 仍需 fail closed，返回 `404`；
- size/hash mismatch：建议 `409 Conflict` 或 `422`；
- 不满足的 Range：`416`；
- Host 不允许：原有 `403`。

媒体错误 body 可以为空或使用固定短文本，不能回显本机路径、manifest 内容或外部输入。

---

## 7. Service Worker 与缓存

`src/web/sw.js` 当前会缓存 shell，并对 Range 请求走自己的 Range 分支。题库音频第一版应明确为
network-only，避免非 Range 请求意外让 `cacheFirst()` 存下 20–50 MB 文件。

增加：

```javascript
const EXAM_MEDIA_PREFIX = new URL("exam-media/", self.registration.scope).pathname;
```

在通用 Range 和 `cacheFirst` 之前处理：

```javascript
if (url.pathname.startsWith(EXAM_MEDIA_PREFIX)) {
  event.respondWith(fetch(request));
  return;
}
```

`fetch(request)` 会保留浏览器的 Range header，服务端仍返回 `206`。不要把媒体 response 放入
`SHELL_CACHE` 或课程 cache。以后若要离线保存题库音频，应单独设计带配额提示、完整性校验和清理入口的
exam-media cache，不能顺手塞进 shell。

新增 `exam_audio.js` 或修改 shell 文件后，提升 `SHELL_CACHE` 版本，并把新脚本加入
`SHELL_ASSETS`。

当前 CSP 已包含 `media-src 'self' blob:`，同源 endpoint 不需要放宽 CSP。不要为了实现本功能添加
`*`、`unsafe-inline` 或外部媒体域名。

---

## 8. 前端播放器

### 8.1 HTML 结构

在 `src/web/exam.html` 的 `part-instruction` 与题干之间加入一个播放器区，保留现有 warning 作为
缺音频状态：

```html
<section class="exam-audio-panel" id="exam-audio-panel" hidden aria-label="听力音频">
  <div class="exam-audio-head">
    <div>
      <strong>听力音频</strong>
      <span id="exam-audio-source"></span>
    </div>
    <label>
      速度
      <select id="exam-audio-rate">
        <option value="0.75">0.75×</option>
        <option value="1" selected>1×</option>
        <option value="1.25">1.25×</option>
        <option value="1.5">1.5×</option>
      </select>
    </label>
  </div>
  <audio id="exam-audio" controls preload="metadata"></audio>
  <p class="exam-audio-status" id="exam-audio-status" aria-live="polite"></p>
</section>
```

可以先使用原生 `controls`，它已经提供无障碍较好的播放、暂停、seek、音量、时间显示。速度选择单独设置
`playbackRate`。第一版没有必要复制听写播放器的整套自定义控制栏。

更新 `const el = {...}`，把所有新 ID 纳入 `tests/web_integrity.test.mjs` 已有的 DOM 完整性检查。

### 8.2 建议拆出 `exam_audio.js`

推荐新增 `src/web/exam_audio.js`，把音频状态控制从 2000 多行的 `exam.js` 中分离。它只负责：

- 当前媒体 slug / URL；
- 每个 slug 的播放位置；
- 设置和切换 source；
- 处理 `loadedmetadata`、`error`、`play`、`pause`、`timeupdate`；
- 设置 playbackRate；
- `pause()` / `clear()` / `destroy()`。

暴露一个小接口，例如：

```javascript
const audioController = ExamAudio.create({
  audioElement: el.examAudio,
  rateElement: el.examAudioRate,
  onStatus: renderAudioStatus,
});
```

模块拆分后可以在 Node 中用 fake audio element 测试切源和位置恢复，不必启动完整 DOM。

### 8.3 不要在每次 `renderQuestion()` 重设 `src`

这是最重要的前端约束。错误写法：

```javascript
el.examAudio.src = media.url;
```

如果它在每次 `renderQuestion()` 都执行，上一题/下一题会重新载入音频、回到开头、打断播放。

正确逻辑：

```text
ensureSource(slug, url)
  如果 slug 和 url 与当前相同：什么都不做
  否则：
    保存旧 slug 的 currentTime
    pause 旧音频
    设置新 src 并 load
    loadedmetadata 后恢复新 slug 的已保存位置
    保持 paused，等待用户主动播放
```

设置 `currentTime` 要等 `loadedmetadata`，并用 `Math.min(savedTime, duration)` 截断。对 `NaN`、
Infinity、负数全部回退到 0。

### 8.4 找出当前题应该用哪套音频

已有函数：

```javascript
slugForQuestion(questionId)
```

普通试卷返回 `state.slug`；专题练习从 `state.questionSource` 返回题目来源 slug。新增：

```text
mediaForQuestion(questionId)
  slug = slugForQuestion(questionId)
  普通试卷 -> state.exam.listeningMedia
  专题练习 -> state.topicMedia.get(slug)
```

在 `startDrill()` 中建立：

```javascript
state.topicMedia = new Map(
  loaded.map(({ slug, exam }) => [slug, exam.listeningMedia])
);
```

`clearTopic()` 必须同时清空 `topicMedia`。

### 8.5 `renderQuestion()` 的状态分支

建议按以下顺序：

```text
如果 section.audioRequired 为 false：
  隐藏播放器
  隐藏缺音频警告
  暂停但保存当前媒体位置

如果是听力题且 media.available 为 true：
  隐藏 warning
  显示播放器
  ensureSource(sourceSlug, media.url)
  专题模式显示来源试卷标签

如果是听力题但媒体不可用：
  暂停音频
  隐藏播放器
  显示 warning
  根据 status 给出准确、非技术化提示
```

warning 文案示例：

- `unconfigured`：`这套试卷尚未配置配套听力音频，可继续对照答案复习。`
- `file-missing`：`配套听力音频文件缺失，可继续对照答案复习。`
- `size-mismatch/hash-mismatch`：`配套听力音频校验失败，已停止播放以避免使用错误音轨。`

不要显示本机路径或 hash。

### 8.6 页面生命周期

在以下位置暂停音频：

- `submitSession()`；
- 从 session 返回题库首页；
- 打开报告页；
- `beforeunload`；
- `visibilitychange` 进入 hidden（建议，但可选）；
- 当前题切为非听力题。

不要在 `renderQuestion()`、选择答案、显示解析时无条件暂停；真实录音可能仍在连续播放。

### 8.7 键盘与自动播放

当前 `Space` 已用于“看答案”，不要再把它全局绑定为播放/暂停。原生 audio 在获得焦点后自带键盘控制。
若以后增加 `P` 快捷键，必须在 input、textarea、select、button 和 audio 获得焦点时跳过。

不要在翻题或切源后调用 `play()`。浏览器可能拒绝非用户手势播放，而且跨试卷自动播放非常容易放错音轨。

---

## 9. 题库列表、设置页与专题练习

### 9.1 题库列表

修改 `buildExamCard(summary)`，在听力标记旁显示媒体状态：

- `🎧 音频已就绪`；
- `听力 · 暂无音频`；
- `听力 · 音频异常`。

列表只使用 API summary，不额外发 HEAD 请求。否则 41 套卷会产生大量并发媒体探测。

### 9.2 设置页

替换 `renderSetup()` 中写死的提示：

- 普通试卷、ready：`听力音频已就绪，进入听力题后可播放整段录音。`
- 普通试卷、missing：保留对照答案复习提示；
- 专题听力：`共 X 套来源试卷有音频，Y 套暂无音频；本次只纳入有音频的试卷。`

### 9.3 专题听力默认只纳入有音频的试卷

当前专题会合并同等级所有试卷。对于 `topic.audioRequired`：

1. `loadTopic()` 仍加载所有卷，用于展示总量；
2. `startDrill()` 在构建 merged exam 前筛选 `exam.listeningMedia.available === true`；
3. `questionSource` 只含筛选后的题；
4. 没有任何 ready 媒体时禁用“连续练习”，提示先安装/绑定音频；
5. 不要静默改变统计：卡片同时显示“总题数”和“可听练题数”。

普通单卷即使缺音频仍可进入，原因是用户可能只想看答案、笔记和解析；专题听力默认筛选则是为了保证
“连续练习”中的每道题都真的可听。

### 9.4 计时模式

第一版沿用当前 `beginSession()` 的计时语义：进入 session 后计时，用户主动点击音频播放。不要把 timer
与 `audio.play()` 强耦合，否则会同时改变普通笔试和各 scope 的时限逻辑。

界面可加一句：`计时已开始，请点击播放听力音频。` 当前项目本来就把 exam mode 描述为本地计时练习，
并非服务端严格模考。

---

## 10. 第二阶段：经核验的题目定位

如果后续需要“定位到本题”，建议使用独立 sidecar：

```text
exams/<slug>/listening-cues.json
```

格式示例：

```json
{
  "schemaVersion": 1,
  "audioSha256": "0f2f832f0b3894d1ae717e76d7542bf79f5b56b073a4425aef1f0e3c2dcc4ce4",
  "parts": {
    "s3-m1": { "startSec": 75.89, "endSec": 590.33 }
  },
  "questions": {
    "q_xxxxxxxxxxxxxxxxxxxxxxxx": { "startSec": 115.0, "endSec": 213.51 }
  },
  "review": {
    "humanVerified": true,
    "reviewedAt": "2026-09-01",
    "notes": ""
  }
}
```

规则：

- `audioSha256` 必须等于绑定音频；换音频后全部 cue 自动失效；
- `questionId` 必须属于该试卷的听力章节；
- `0 <= startSec < endSec <= duration + tolerance`；
- 同一 part 内 cue 顺序不能倒退；
- ASR marker 可以生成候选，但 `humanVerified` 前不提供自动定位；
- 第一版增强只加显式“定位到本题”按钮，不在翻题时自动跳转；
- 连续模考模式中隐藏定位按钮，避免破坏整段录音流程；练习/复习模式才显示。

这是独立阶段，不应阻塞整段音频播放器上线。

---

## 11. 测试计划

### 11.1 Python：媒体解析和 HTTP

新增 `tests/test_exam_audio.py`。使用 32 字节或几十字节 fixture，不要读取真实 20–50 MB 音频。

必须覆盖：

1. 同名课程 + 正确绑定返回 `available: true`；
2. 未配置返回 `unconfigured`，但 `GET /api/exams/<slug>` 仍为 `200`；
3. 课程缺失；
4. manifest 损坏；
5. `manifest.audio` 包含 `..`、`/`、`\` 时拒绝；
6. 文件缺失；
7. bytes mismatch；
8. hash mismatch；
9. `GET /exam-media/<slug>/audio` 返回完整内容；
10. `HEAD` 无 body、headers 正确；
11. `Range: bytes=4-9` 返回精确 6 字节和 `206`；
12. `bytes=28-`；
13. `bytes=-5`；
14. 越界 Range 返回 `416`；
15. 重复 seek 结果一致；
16. forged Host 返回 `403`；
17. `../`、编码后的 `/`、未知 slug 不能读取任意课程；
18. 切换当前听写课程后，exam media 内容不变；
19. 响应不包含绝对路径；
20. 列表接口不会对每套大文件重复计算 hash（可注入 fake hasher 断言调用次数）。

扩展 `tests/support.py` 的 `RunningServer`，允许显式传 `courses_root`，并增加创建 exam-media fixture 的 helper。

### 11.2 Python：schema 与 importer

扩展：

- `tests/test_exam_schema.py`：合法配置、非法 kind、slug、hash、bytes；旧试卷无配置仍通过；
- `tests/test_exam_import.py`：`exam-meta.json` 中的媒体引用能进入生成的 `exam.json`；
- `contentRevision` 在绑定变化时改变，但 `examId` / question IDs 不变；
- 物理文件缺失不由 `audit_exam()` 报错封锁试卷。

### 11.3 JavaScript：controller

新增 `tests/exam_audio.test.mjs`，对 `exam_audio.js` 使用 fake audio element，覆盖：

- 相同 slug/url 的 `ensureSource()` 不重复赋值和 `load()`；
- 切源先保存旧位置并暂停；
- 新源 `loadedmetadata` 后恢复自己的位置；
- 不自动调用 `play()`；
- playbackRate 保持；
- error 回调进入不可播放状态；
- 清理事件监听器；
- 非法 saved time 回退 0；
- `duration` 小于保存位置时正确截断。

扩展 `tests/web_integrity.test.mjs`：

- `exam_audio.js` 加入 `SCRIPTS` parse 列表；
- HTML 中所有新增 ID 存在且不重复；
- `exam_audio.js` 在 `exam.js` 之前加载。

### 11.4 Service Worker

在现有 `sw_*.test.mjs` 增加：

- `/exam-media/...` 不写入 shell/course cache；
- Range header 原样交给 network fetch；
- transport failure 不返回伪造的 `audio/mpeg 200`；
- shell cache 版本更新且包含 `exam_audio.js`。

### 11.5 手工验收矩阵

至少选：一套有音频 N1、一套有音频 N2、一套无音频试卷。

| 场景 | 预期 |
|---|---|
| 打开有音频试卷设置页 | 明确显示音频已就绪 |
| 做笔试题 | 播放器不显示、不漏出背景声音 |
| 进入第一道听力题 | 播放器显示，metadata 可加载 |
| 点击播放后翻下一题 | 音频继续，不回到 0 |
| 手工 seek | 很快从新位置播放，网络响应为 `206` |
| 调整 0.75×/1.25× | 播放速度真实改变，翻题不复位 |
| 从听力返回笔试 | 音频暂停，位置保留 |
| 再回听力 | 恢复位置但不自动播放 |
| 交卷/回首页 | 音频停止 |
| 打开无音频试卷 | 可正常答题，显示准确 warning |
| 跨试卷专题练习 | 来源标签正确，切卷不会播放上一卷音频 |
| 断开/删除音频后刷新 | 试卷仍能打开，媒体标为不可用 |
| forged Host 请求媒体 | `403` |
| 手机窄屏 | audio 控件不溢出题卡 |

浏览器开发者工具同时确认：没有整文件重复下载、没有每翻一题重新请求音频开头、没有 console error。

---

## 12. 推荐实施顺序

按以下顺序提交，可以让每一步都能单独验证：

### 提交 1：数据契约

- 扩展 `exam_schema.py`；
- 扩展 `exam_import.py`；
- 增加 schema/importer 测试；
- 增加 `link_exam_audio.py --dry-run`。

验收：旧卷仍通过，合法绑定可生成，非法绑定被拒绝。

### 提交 2：服务端媒体解析与流式 endpoint

- 增加 resolver；
- 列表和单卷 DTO 注入媒体状态；
- 抽取通用 Range file serving；
- 新增 GET/HEAD endpoint；
- 增加安全、Range 和错误测试。

验收：用测试 fixture 完成 `200/206/416/403` 全矩阵。

### 提交 3：单卷播放器

- `exam.html` / `exam.css`；
- `exam_audio.js`；
- `exam.js` 的 setup、render、生命周期接入；
- JS controller 与 DOM integrity 测试；
- Service Worker network-only 和 shell cache bump。

验收：同卷翻题连续播放且不重载。

### 提交 4：跨试卷专题练习

- `state.topicMedia`；
- 听力专题只纳入 ready 来源；
- per-slug position；
- 来源标签和数量提示；
- 专题切源测试与手工验收。

验收：A 卷/B 卷切换永不串音。

### 提交 5：安装和绑定现有内容

- 将合格 work bundle 安装到 `courses/`；
- 批量 dry-run；
- 批量写入 meta 并重组 exam；
- 全量 validate；
- 更新 `docs/JLPT_EXAM.md` 中“没有配套音频”的过期说明。

不要先批量改 41 套 exam 再写 resolver；先让代码和测试接受“无绑定”，再逐套启用，回滚和定位问题更容易。

---

## 13. 执行命令与最终质量门

实现完成后执行：

```powershell
# 盘点正式课程
python .\src\install_course.py --list

# 先查看将要绑定什么
python .\scripts\link_exam_audio.py --all-by-slug --dry-run

# 写入并重组（确认 dry-run 无误后）
python .\scripts\link_exam_audio.py --all-by-slug --write

# 逐套验证 exam（脚本也应内部执行）
Get-ChildItem .\exams -Directory | ForEach-Object {
  python .\src\exam_import.py validate --exam (Join-Path $_.FullName "exam.json")
  if ($LASTEXITCODE -ne 0) { throw "Exam validation failed: $($_.Name)" }
}

# 相关 Python 测试
python .\run_tests.py exam
python .\run_tests.py range

# 最终全量测试（包含 Node 前端与 Service Worker 测试）
python .\run_tests.py
```

随后启动本地服务，完成第 11.5 节手工矩阵：

```powershell
python .\start_dictation.py
```

题库入口：`http://127.0.0.1:4173/exam.html`（端口以启动输出为准）。

---

## 14. 完成定义

只有同时满足以下条件，才算“JLPT 听力功能补全”：

- 已安装且已绑定的真实音频能在对应试卷听力题中播放；
- 音频与试卷由 slug + SHA-256 + bytes 明确绑定，不靠标题猜测；
- 同卷翻题连续、跨卷切换不串音、离开 session 会停止；
- 现有无音频试卷仍可使用，提示与真实状态一致；
- 大文件按 Range 流式传输，不整体读内存、不复制到 exam 目录、不进入 shell cache；
- endpoint 通过路径穿越和 forged Host 测试；
- 专题听力默认不会把无音频题混进“可听练”队列；
- Python、Node、Service Worker 全量测试通过；
- `docs/JLPT_EXAM.md` 不再保留“全部试卷都没有配套音频”的过期描述。

题目级自动定位不是第一阶段完成条件；只有经音频哈希绑定并人工核验的 cue 才能上线。
