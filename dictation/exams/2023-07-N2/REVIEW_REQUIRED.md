# 2023-07-N2 — pages/ 是未复核草稿

`pages/` 由 `src/exam_ocr_to_pages.py` 从 `exam-work/2023-07-N2/ocr` 机械转换而来，
**不是**已核对的转写。`exam.json` 尚未生成，本卷不会被任何接口提供。

## 当前状态（2026-09-11）

- OCR：31 页全部转写完成（Qwen2.5-VL-7B，本地 GPU），质量报告见 `exam-work/2023-07-N2/ocr/quality-report.json`
- 草稿：31 页（0 页卷首页不属于页面集合，已按 47 套已验收卷的惯例跳过）
- 其中 11 页无 issue，20 页共 141 条 issue；识别出 45 道题
- 答案表：无
- 装配：尚无 `answer-key.txt`，未尝试装配。另：`exam-work/IMPORT-STATUS.md` 记录「2023-07 弃用」
  的范围是否包含 N2 尚未确认——本卷是独立扫描件，没有 N1 那卷的错字问题，但入库前要先定这件事。

## 入库前要做的事

1. 逐页对照 `exam-work/2023-07-N2/pages/`（150dpi 整页图 + 260dpi 横条）核对 `pages/pNN.json`，
   补全机械转换认不出的读解题干与选项，清空 `issues`。
2. `python3 src/exam_import.py assemble --pages exams/2023-07-N2/pages --key exams/2023-07-N2/answer-key.txt --meta exams/2023-07-N2/exam-meta.json --out exams/2023-07-N2/exam.json`
3. `python3 src/exam_import.py validate --exam exams/2023-07-N2/exam.json`

不要用 `--allow-failed-audit` 绕过第 2 步：它报的每一条都是真实的转写缺口。
