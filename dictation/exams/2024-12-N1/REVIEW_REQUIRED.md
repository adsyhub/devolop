# 2024-12-N1 — pages/ 是未复核草稿

`pages/` 由 `src/exam_ocr_to_pages.py` 从 `exam-work/2024-12-N1/ocr` 机械转换而来，
**不是**已核对的转写。`exam.json` 尚未生成，本卷不会被任何接口提供。

## 当前状态（2026-09-11）

- OCR：38 页全部转写完成（Qwen2.5-VL-7B，本地 GPU），质量报告见 `exam-work/2024-12-N1/ocr/quality-report.json`
- 草稿：37 页（1 页卷首页不属于页面集合，已按 47 套已验收卷的惯例跳过）
- 其中 18 页无 issue，19 页共 237 条 issue；识别出 33 道题
- 答案表：有
- 装配：`assemble` 停在 `問題1 has a scored question with no printed number.`
  原因：本卷聴解分册的页眉只印「2024年12月・N1」，没有分册标记，聴解的 1番/2番 被当成
  笔试题。复核时要在聴解首页的 JSON 里写 `"sectionHeader"`（见已验收卷 `exams/2020-12-N1`）。

## 入库前要做的事

1. 逐页对照 `exam-work/2024-12-N1/pages/`（150dpi 整页图 + 260dpi 横条）核对 `pages/pNN.json`，
   补全机械转换认不出的读解题干与选项，清空 `issues`。
2. `python3 src/exam_import.py assemble --pages exams/2024-12-N1/pages --key exams/2024-12-N1/answer-key.txt --meta exams/2024-12-N1/exam-meta.json --out exams/2024-12-N1/exam.json`
3. `python3 src/exam_import.py validate --exam exams/2024-12-N1/exam.json`

不要用 `--allow-failed-audit` 绕过第 2 步：它报的每一条都是真实的转写缺口。
