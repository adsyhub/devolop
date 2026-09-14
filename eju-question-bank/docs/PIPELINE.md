# EJU PDF 到题库 Pipeline

本目录是独立实现，不依赖仓库外层的听写、JLPT、课程或网页代码。

## 0.2.0 制作合同与恢复

当前页面写入 v2，来源清单保持 v1；数据库为 v8。canonical Schema 由
`scripts/sync_schemas.py --check` 和安装包测试验证。运行时 registry 离线解析，禁止外部 `$ref` 网络取回。

区域覆盖以 `coverage.regionIds`、`accountedRegionIds` 集合及每块归属核对，数量相等不足以签署。
看不清的内容保留 issue；v1 草稿转换不会伪造真实区域证据。

制作顺序为：精确 inventoryId 绑定、文件真实性验证、probe/render、OCR 草稿、独立结构与逐页签署、
候选预检、整卷审批、发布。修改页、撤回、改变源文件或 baseline 后必须重新审批。发布事务写 outbox，
清单同步失败可重试；并发同步在数据库事务内串行执行。

缓存验证源文件、配置、图片、provider、prompt 和 schema 身份。run/attempt 独立保留，不能因为同名
JSON 存在就跳过。任务使用 lease/心跳，失败后按 jobId、页与错误码重试；OCR 配置为工作区
`config/providers.json`。

`python scripts/prepare_review_queue.py --workspace <工作区>` 可重建物理页待办，它只核验文件与页数，
不签署、不推导标准答案。六套真实来源的 254 页队列在 `work/<来源>/review-queue.json`。

音频必须真实可解码，来源 hash 和 cue 引用需审核；严格播放交付的是审核后的实际音频片段。
恢复制作环境选择 FULL 备份，LEARNING 包不保证保存原 PDF 和制作工作文件。

## 状态流

```text
RECEIVED -> PROBED -> RENDERED -> EXTRACTED -> REVIEWED
         -> ASSEMBLED -> VALIDATED -> PUBLISHED
```

任何阶段产生未解决的 contract error 都不能进入下一阶段。

## 两次读取与反验

答案页在 180 dpi 与 400 dpi 各读一遍（`scripts/reocr_answer_keys.py` → `answer_ocr_hi/`）。
两次当成独立测量：只有一次读到的采用，两次读到而不一致的谁也不采用。第二遍只能补欄位或撤回
可疑的，不会把一个答案换成另一个。

欄号与答案的配对不靠"敢不敢"，靠一个独立检验：**正解表给的答案必须在题册那一页印出的选项
里**。缺口之上的答案与按小节顺序补出的欄号都先提议、再逐段验（`eju_bank/ocr/slot_join.py`），
整段一致率不足就整段不用，并记录它达到的比率。错位时单题蒙对约 1/5，整段 n 道全蒙对约 0.2ⁿ，
所以这个比率就是"没有错位"的证据。

## 两种放行：人工签署与机器证明

`REVIEWED` 这一步有两条合法路径，它们在数据里是分开的，绝不互相冒充。

**人工签署**（`sign_page`）——复核人对照原页逐块确认，自己填区域身份与真实 bbox。
这是最强的放行，也是 `coverage.regionIds` 这套区域证据要求的本意。

**机器证明**（`attest_page`）——流水线只断言它真能核对的几件事，并把边界写进记录：

| 断言 | 依据 |
|---|---|
| `text.verbatim_ocr` | 每个块的文字逐字出现在该页 OCR 缓存里（记录缓存 SHA-256） |
| `answer.from_official_key` | 答案取自官方正解表，欄号可查（记录答案缓存） |
| `answer.is_a_read_option` | 答案确实是该页读到的选项之一 |
| `coverage.text_order_only` | **区域几何未验证**：bbox 是整页正文占位，区域身份来自文字顺序 |

证明里的 `notAsserted` 字段明写"未经人工逐页比对"。署名是保留身份
`machine:eju-ocr-pipeline`，复核决定记为 `MACHINE_ATTESTED`（永远不是 `APPROVED`），
组出来的卷带 `reviewGrade: MACHINE_ATTESTED` 一路显示到学习者界面。人工后来签署同一页时，
机器证明被**取代**而不是被继承。

机器证明比人工签署弱，并且在数据里说明自己弱。它存在的理由是 6514 页题册不可能逐页手签，
而把 2000 多道有真实题干、真实选项、官方答案的题锁在工作目录里同样不是诚实 —— 标明把关
程度地交付，比假装它不存在好。

任何一项核不过的页面仍然是草稿：`needsReview` 留在合约上，`attest_page` 拒绝签发。

## 页面事实合同

OCR/VLM 只负责生成 `pages/pNNNN-<role>.json`。最终 `paper.json` 由确定性
assembler 生成，不能直接由模型生成。

页面中的每个 block 必须提供归一化 `bbox`。`coverage.inkRegions` 与
`coverage.accountedRegions` 必须相等；看不清的区域要保留 issue，不能猜测后标记为完成。

### 图片与非文本视觉内容

题目、共用材料、题干或选项中凡是会影响理解和作答的非文本视觉内容，都必须进入题库，不能只
转录附近文字，也不能用文字描述替代原图。范围包括但不限于：示意图、函数/坐标图、几何图、
实验装置、电路图、化学结构、地图、照片，以及以图片呈现的选项。

提取时必须：

1. 在对应 `contentAst` 中保留 `figure` 节点和精确的归一化 `sourceBbox`；
2. 将图片关联到它实际所属的材料、题干或单个选项，保持原始阅读顺序；
3. 同时转录图内可读标签，但绝不因此删除 `figure` 节点；
4. 从原页生成无损或高质量裁剪，保存 SHA-256、尺寸、来源页码和 bbox；
5. 在前端显示真实图片并允许缩放；
6. 原页存在必要图片但页面合同、裁剪资产或题目引用任一缺失时，审计必须失败，禁止发布。

若一个印刷面板包含多个子图，应保持面板整体及子图标号；若多个选项分别是独立图片，则每个
选项分别绑定自己的图片，不得合并后丢失选项对应关系。

题目示例：

```json
{
  "kind": "question",
  "localKey": "physics-i-q1",
  "formCode": "PHYSICS_JA",
  "sectionCode": "MAIN",
  "groupCode": "I",
  "printedLabel": "問1",
  "answerRef": "PHYSICS:1",
  "stemAst": [
    {"type": "text", "value": "問題文"},
    {
      "type": "figure",
      "sourceBbox": [0.18, 0.31, 0.81, 0.62],
      "alt": "人工复核后填写的简短可访问性说明"
    }
  ],
  "options": [
    {"key": "1", "contentAst": [{"type": "inlineMath", "latex": "x^2"}]},
    {"key": "2", "contentAst": [{"type": "inlineMath", "latex": "2x"}]}
  ],
  "answerSpec": {"type": "SINGLE_CHOICE"},
  "materialRefs": [],
  "bbox": [0.08, 0.15, 0.92, 0.85]
}
```

## 答案隔离

题册 OCR prompt 禁止生成答案。答案 PDF 单独 OCR 成 `answer-entry`，然后生成
answer ledger。assembler 要求每道客观题恰好匹配一个答案，并拒绝所有未使用答案。

数学答案必须按字符串 token 保存，避免丢失 `04` 的前导零或 `-3` 的负号。

## 发布门禁

- `PRIVATE_STUDY` 只能发布到 PRIVATE。
- PUBLIC 需要 `PUBLIC_LICENSED` 或 `COMMERCIAL_LICENSED`。
- COMMERCIAL 只接受 `COMMERCIAL_LICENSED`。
- `SUSPENDED` 不能发布。
- 已发布 paper/question version 由 SQLite trigger 保持不可变。

## 真实样本

首个集成样本为 2023 年第 2 回 EJU 理科：题册 56 页、答案 PDF 8 页。两份文件
都是无文字层扫描件，且所有页面声明 90 度旋转。题册在同一 PDF 中包含物理、化学、
生物，答案 PDF 则同时包含日本语、理科、综合科目、数学与记述内容。
