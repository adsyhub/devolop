"use strict";

/**
 * PDF 教材 / 真题 → 待复核草稿。
 *
 * This is the one pipeline that deliberately does not finish: OCR and the
 * suspicious-page retries are automatic, but an answer key is never guessed and
 * a 目次 count is never inferred from the same OCR it is meant to check. It ends
 * at a draft, and the result panel says what a person still has to do.
 */
const PipelinePdf = (() => {
  const { el, post, text } = StudioCore;

  const uploads = () => StudioState.uploads.pdf;

  const KIND_LABELS = {
    exam: "真题题库", grammar: "语法内容包", word: "单词内容包", document: "OCR 文档",
  };

  /** The draft summary a finished PDF job leaves behind. */
  function renderResult(result, jobId) {
    const box = el("result-summary");
    box.replaceChildren();
    box.append(text("h3", "result-title", "PDF 草稿已完成，尚未入库"));
    const stats = result.stats || {};
    const detected = result.detected || {};
    const ocr = result.ocr || {};
    const rows = [
      ["识别类型", `${KIND_LABELS[result.kind] || result.kind} · ${result.level || ""}`],
      ["自动判断", `${KIND_LABELS[detected.kind] || detected.kind || "未知"} · ${detected.confidence || ""}`],
      ["产物目录", result.draftPath || result.artifactRoot || ""],
      ["规模", `${stats.pages || 0} 页 · ${stats.questions || 0} 题 · ${stats.entries || 0} 条目`],
      ["OCR 模型", (ocr.usedProfiles || []).join(" → ") || "未记录"],
      ["OCR 异常页", String((ocr.flaggedPages || []).length)],
    ];
    for (const [label, value] of rows) {
      const row = document.createElement("div");
      row.className = "result-row";
      row.append(text("span", "result-label", label), text("span", "result-value", String(value)));
      box.append(row);
    }
    if ((result.nextSteps || []).length) {
      box.append(text("h4", "", "入库前必须完成"));
      const list = document.createElement("ol");
      for (const step of result.nextSteps) list.append(text("li", "", step));
      box.append(list);
    }
    if (result.reviewRequired && jobId) {
      const edit = text("a", "button-link primary draft-edit-link", "打开复核编辑器");
      edit.href = `/editor.html?build=${encodeURIComponent(jobId)}`;
      box.append(edit);
    }
    box.hidden = false;
  }

  return {
    id: "pdf",
    tabId: "tab-pdf",
    fieldsId: "pdf-fields",
    titlePlaceholder: "留空则使用 PDF 文件名",
    // OCR takes a vision pipeline, not 语言 / 转写 / 讲解 — those fields are hidden.
    usesCommonFields: false,
    usesEnrichment: false,
    // It ends at a draft a person must read, not at a course.
    installable: false,
    destination: "复核编辑器",

    count: () => uploads().length,
    hasSource: () => uploads().length > 0,
    modelReady: () => Boolean(el("vision-pipeline").value),
    startLabel: (count) => `开始后台制作${count > 1 ? ` ${count} 个` : ""} PDF 草稿`,

    start() {
      const files = uploads();
      const options = {
        documentKind: el("pdf-kind").value,
        level: el("pdf-level").value,
        visionPipeline: el("vision-pipeline").value,
      };
      if (files.length === 1) {
        return post("/api/pdf/builds", Object.assign(options, {
          uploadId: files[0].uploadId,
          title: el("title").value.trim(),
        }));
      }
      return post("/api/batch-builds", Object.assign(options, {
        source: "pdf",
        items: files.map((upload) => ({ uploadId: upload.uploadId, title: "" })),
      }));
    },

    renderResult,
  };
})();

if (typeof module !== "undefined" && module.exports) module.exports = PipelinePdf;
if (typeof window !== "undefined") window.PipelinePdf = PipelinePdf;
