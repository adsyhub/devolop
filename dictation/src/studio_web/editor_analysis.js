"use strict";

/**
 * 整课模型分析 — one course, a selection of them, or the 连续复核 queue.
 *
 * Analysis runs on the server and outlives this page, so the job id is kept in
 * localStorage and re-attached on load: closing the tab in the middle of a
 * 20-minute batch must not lose the report.
 */
const EditorAnalysis = (() => {
  const $ = StudioCore.el;
  const api = StudioCore.api;
  const fillSelect = StudioCore.fillSelect;
  const state = EditorState;
  const targetKey = EditorState.targetKey;

  function updateFilePathDisplay(filePath) {
    const el = $("analysis-md-filepath");
    if (!el) return;
    if (filePath) {
      el.textContent = `本地保存路径：${filePath}`;
      el.hidden = false;
    } else {
      el.textContent = "";
      el.hidden = true;
    }
  }

  async function startWholeAnalysis() {
    if (state.mode) {
      const button = $("start-analysis");
      const queueBtn = $("start-queue-analysis");
      button.disabled = true;
      if (queueBtn) queueBtn.disabled = true;
      $("analysis-result").hidden = true;
      $("report-selector-bar").hidden = true;
      updateFilePathDisplay("");
      $("analysis-report-title").textContent = "分析报告";
      $("analysis-report").textContent = "";
      $("analysis-log").textContent = "";
      $("analysis-log").hidden = false;
      $("analysis-progress").textContent = "正在创建后台分析任务…";
      $("analysis-status").dataset.status = "running";
      $("analysis-status").textContent = "分析中";
      state.analysisMode = "single";
      try {
        const result = await api("/api/analyses", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            targetKind: state.mode,
            targetId: state.mode === "course" ? state.course.name : state.draft.jobId,
            textProfile: $("analysis-model").value,
            instruction: $("analysis-instruction").value.trim(),
          }),
        });
        state.analysisId = result.id;
        if (analysisStorageKey()) localStorage.setItem(analysisStorageKey(), result.id);
        state.analysisLogCursor = 0;
        clearInterval(state.analysisPolling);
        state.analysisPolling = setInterval(pollWholeAnalysis, 2000);
        await pollWholeAnalysis();
      } catch (error) {
        $("analysis-status").dataset.status = "failed";
        $("analysis-status").textContent = "失败";
        $("analysis-progress").textContent = String(error.message || error);
        button.disabled = false;
        if (queueBtn) queueBtn.disabled = false;
      }
    } else if (state.selectedTargetKeys && state.selectedTargetKeys.size > 0) {
      await startBatchAnalysisAction();
    }
  }

  async function runBatchAnalysisWithTargets(targets) {
    if (!targets.length) return;

    const button = $("start-analysis");
    const queueBtn = $("start-queue-analysis");
    const batchBtn = $("start-batch-analysis-btn");
    button.disabled = true;
    if (queueBtn) queueBtn.disabled = true;
    if (batchBtn) batchBtn.disabled = true;

    $("analysis-panel").hidden = false;
    $("analysis-result").hidden = true;
    $("report-selector-bar").hidden = true;
    updateFilePathDisplay("");
    $("analysis-report").textContent = "";
    $("analysis-log").textContent = "";
    $("analysis-log").hidden = false;
    $("analysis-progress").textContent = `正在创建后台批量分析任务（共 ${targets.length} 门）…`;
    $("analysis-status").dataset.status = "running";
    $("analysis-status").textContent = "分析中";
    $("analysis-panel").scrollIntoView({ behavior: "smooth" });

    try {
      const payload = {
        targets: targets.map((t) => ({ targetKind: t.targetKind, targetId: t.targetId })),
        textProfile: $("analysis-model").value,
        instruction: $("analysis-instruction").value.trim(),
      };
      const result = await api("/api/batch-analyses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      state.analysisId = result.id;
      state.analysisMode = "batch";
      state.batchAnalysis = result;
      localStorage.setItem("dictation-batch-analysis-id", result.id);
      state.analysisLogCursor = 0;
      clearInterval(state.analysisPolling);
      state.analysisPolling = setInterval(pollBatchAnalysis, 2000);
      await pollBatchAnalysis();
    } catch (error) {
      $("analysis-status").dataset.status = "failed";
      $("analysis-status").textContent = "失败";
      $("analysis-progress").textContent = String(error.message || error);
      button.disabled = false;
      if (queueBtn) queueBtn.disabled = false;
      if (batchBtn) batchBtn.disabled = false;
    }
  }

  async function startBatchAnalysisAction() {
    const selected = state.reviewTargets.filter((t) => state.selectedTargetKeys.has(targetKey(t)));
    if (!selected.length) return;
    const targets = selected.map((t) => ({ targetKind: t.targetKind, targetId: t.targetId }));
    await runBatchAnalysisWithTargets(targets);
  }

  async function startQueueAnalysisAction() {
    let targets = [];
    if (state.multiQueue && state.multiQueue.length > 0) {
      targets = state.multiQueue.map((t) => ({ targetKind: t.targetKind, targetId: t.targetId }));
    } else if (state.selectedTargetKeys && state.selectedTargetKeys.size > 0) {
      targets = state.reviewTargets
        .filter((t) => state.selectedTargetKeys.has(targetKey(t)))
        .map((t) => ({ targetKind: t.targetKind, targetId: t.targetId }));
    }
    if (!targets.length) return;
    await runBatchAnalysisWithTargets(targets);
  }

  async function pollBatchAnalysis() {
    if (!state.analysisId) return;
    try {
      const job = await api(`/api/batch-analyses/${encodeURIComponent(state.analysisId)}?since=${state.analysisLogCursor}`);
      for (const line of job.log || []) {
        $("analysis-log").textContent += ($("analysis-log").textContent ? "\n" : "") + line;
      }
      state.analysisLogCursor = job.logCursor;
      state.batchAnalysis = job;

      $("analysis-progress").textContent = `已分析 ${job.progress}/${job.total} 门课程 · 当前：${job.currentTargetName || "准备中"} · 用时 ${job.elapsed} 秒`;

      if ((job.targetReports && Object.keys(job.targetReports).length > 0) || job.overallReport) {
        renderBatchAnalysisResult(job);
        $("analysis-result").hidden = false;
      }

      if (job.status === "succeeded") {
        clearInterval(state.analysisPolling);
        state.analysisPolling = null;
        $("analysis-status").dataset.status = "succeeded";
        $("analysis-status").textContent = "完成";
        renderBatchAnalysisResult(job);
        $("analysis-result").hidden = false;
        $("start-analysis").disabled = false;
        if ($("start-queue-analysis")) $("start-queue-analysis").disabled = false;
        $("start-batch-analysis-btn").disabled = false;
      } else if (job.status === "failed") {
        clearInterval(state.analysisPolling);
        state.analysisPolling = null;
        $("analysis-status").dataset.status = "failed";
        $("analysis-status").textContent = "失败";
        $("start-analysis").disabled = false;
        if ($("start-queue-analysis")) $("start-queue-analysis").disabled = false;
        $("start-batch-analysis-btn").disabled = false;
      } else if (!state.analysisPolling) {
        state.analysisPolling = setInterval(pollBatchAnalysis, 2000);
      }
    } catch (error) {
      clearInterval(state.analysisPolling);
      state.analysisPolling = null;
      $("analysis-status").dataset.status = "failed";
      $("analysis-status").textContent = "失败";
      $("analysis-progress").textContent = String(error.message || error);
      $("start-analysis").disabled = false;
      if ($("start-queue-analysis")) $("start-queue-analysis").disabled = false;
      $("start-batch-analysis-btn").disabled = false;
    }
  }

  function renderBatchAnalysisResult(job) {
    const select = $("analysis-report-view-select");
    const previousValue = select.value;
    select.replaceChildren();

    const statusLabels = { succeeded: "已完成", running: "分析中", failed: "失败", pending: "排队中" };

    let currentKey = "";
    if (state.mode === "course" && state.course) currentKey = `course:${state.course.name}`;
    else if (state.mode === "draft" && state.draft) currentKey = `draft:${state.draft.jobId}`;

    if (job.overallReport) {
      const overallOpt = document.createElement("option");
      overallOpt.value = "overall";
      overallOpt.textContent = `跨课程综合汇总对比报告 (共 ${job.total} 门)`;
      select.append(overallOpt);
    }

    job.targets.forEach((target) => {
      const opt = document.createElement("option");
      const key = `${target.targetKind}:${target.targetId}`;
      const st = (job.targetStatuses && job.targetStatuses[key]) || "pending";
      const stText = statusLabels[st] || st;
      opt.value = key;
      opt.textContent = `单课报告 · ${target.title} [${stText}] (${target.targetKind === "draft" ? "草稿" : "课程"})`;
      select.append(opt);
    });

    $("analysis-report-title").textContent = `多课程批量分析报告（共 ${job.total} 门）`;
    $("report-selector-bar").hidden = false;

    let targetToSelect = "";
    if (previousValue && previousValue !== "overall" && job.targetReports && job.targetReports[previousValue]) {
      targetToSelect = previousValue;
    } else if (currentKey && job.targetReports && job.targetReports[currentKey]) {
      targetToSelect = currentKey;
    } else if (job.overallReport) {
      targetToSelect = "overall";
    } else if (job.targetReports && Object.keys(job.targetReports).length > 0) {
      targetToSelect = Object.keys(job.targetReports)[0];
    }

    if (targetToSelect) {
      select.value = targetToSelect;
      if (targetToSelect === "overall") {
        $("analysis-report").textContent = job.overallReport;
        updateFilePathDisplay(job.reportPath);
      } else {
        $("analysis-report").textContent = job.targetReports[targetToSelect] || "该课程分析报告尚在生成中…";
        updateFilePathDisplay((job.targetReportPaths && job.targetReportPaths[targetToSelect]) || "");
      }
    } else if (currentKey) {
      select.value = currentKey;
      $("analysis-report").textContent = "该课程分析报告尚在生成中…";
      updateFilePathDisplay((job.targetReportPaths && job.targetReportPaths[currentKey]) || "");
    }
  }

  function onReportViewSelectChange() {
    if (state.analysisMode !== "batch" || !state.batchAnalysis) return;
    const val = $("analysis-report-view-select").value;
    if (val === "overall") {
      $("analysis-report").textContent = state.batchAnalysis.overallReport || "汇总报告生成中…";
      updateFilePathDisplay(state.batchAnalysis.reportPath);
    } else {
      $("analysis-report").textContent = (state.batchAnalysis.targetReports && state.batchAnalysis.targetReports[val]) || "该课程分析报告生成中或未就绪。";
      updateFilePathDisplay((state.batchAnalysis.targetReportPaths && state.batchAnalysis.targetReportPaths[val]) || "");
    }
  }

  async function batchApproveAction() {
    const selected = state.reviewTargets.filter((t) => state.selectedTargetKeys.has(targetKey(t)));
    if (!selected.length) return;

    if (!confirm(`确定要对选中的 ${selected.length} 门课程/草稿执行规则审计并批量标记为“已复核”吗？\n（未通过质量审计的课程将被自动跳过以保安全）`)) {
      return;
    }

    const stateEl = $("batch-action-state");
    stateEl.textContent = "正在执行批量质量审计与复核标记…";
    $("batch-approve-btn").disabled = true;

    try {
      const payload = {
        targets: selected.map((t) => ({ targetKind: t.targetKind, targetId: t.targetId, title: t.title })),
        note: "工作台批量复核通过",
      };
      const result = await api("/api/batch-review/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let msg = `批量复核完成：成功标记 ${result.approved.length} 门（校验报告 validation-report.md 已输出）。`;
      if (result.failed && result.failed.length) {
        msg += ` 另有 ${result.failed.length} 门未通过审计：` + result.failed.map((f) => `${f.title} (${f.reason})`).join("；");
      }
      stateEl.textContent = msg;

      for (const item of result.approved) {
        state.selectedTargetKeys.delete(`${item.targetKind}:${item.targetId}`);
      }
      await EditorTargets.load();
    } catch (error) {
      stateEl.textContent = `批量标记失败：${error.message || error}`;
    } finally {
      $("batch-approve-btn").disabled = false;
    }
  }

  /**
   * Where a single-course analysis is remembered, or "" when nothing is open.
   *
   * This used to assume a target: on the list screen `state.draft` is null, so
   * reading `.jobId` threw — which is why restore was only ever called from
   * `activateTarget`, and why a batch started from the list vanished on reload.
   */
  /**
   * The 分析重点 the server falls back to when the box is empty.
   *
   * Kept character-for-character in step with `studio_server.py` (both the single
   * and the batch endpoint use this same string): showing it means a person can
   * see and edit what the analysis will actually ask for, instead of discovering
   * it in the report. A different string here would silently change the analysis.
   */
  const DEFAULT_FOCUS = "从整门课程层面检查原文准确性、同音字、翻译、讲解一致性、重复内容、结构缺失和教学质量；"
    + "按影响程度列出可执行的修改建议。";

  /** Fill the focus box on load, leaving anything already typed alone. */
  function applyDefaults() {
    const box = $("analysis-instruction");
    if (box && !box.value.trim()) box.value = DEFAULT_FOCUS;
  }

  function analysisStorageKey() {
    const target = state.mode === "course" ? (state.course && state.course.name)
      : state.mode === "draft" ? (state.draft && state.draft.jobId) : "";
    return target ? `dictation-whole-analysis:${state.mode}:${target}` : "";
  }

  async function restoreWholeAnalysis() {
    if (state.analysisMode === "batch" && state.batchAnalysis) {
      renderBatchAnalysisResult(state.batchAnalysis);
      $("analysis-panel").hidden = false;
      $("analysis-result").hidden = !(state.batchAnalysis.overallReport || (state.batchAnalysis.targetReports && Object.keys(state.batchAnalysis.targetReports).length > 0));
      return;
    }

    const savedBatchId = localStorage.getItem("dictation-batch-analysis-id");
    if (savedBatchId) {
      try {
        const job = await api(`/api/batch-analyses/${encodeURIComponent(savedBatchId)}`);
        if (job && (job.status === "running" || job.status === "succeeded")) {
          let currentKey = "";
          if (state.mode === "course" && state.course) currentKey = `course:${state.course.name}`;
          else if (state.mode === "draft" && state.draft) currentKey = `draft:${state.draft.jobId}`;

          const isTargetInBatch = currentKey && job.targets.some((t) => `${t.targetKind}:${t.targetId}` === currentKey);
          const shouldRestoreBatch = job.status === "running" || isTargetInBatch || state.multiQueue.length > 0 || !state.mode;

          if (shouldRestoreBatch) {
            state.analysisId = savedBatchId;
            state.analysisMode = "batch";
            state.batchAnalysis = job;
            state.analysisLogCursor = 0;
            $("analysis-log").textContent = "";
            $("analysis-log").hidden = false;
            $("analysis-status").dataset.status = job.status;
            $("analysis-status").textContent = job.status === "running" ? "分析中" : "完成";
            $("analysis-progress").textContent = `已分析 ${job.progress}/${job.total} 门课程 · 当前：${job.currentTargetName || "准备中"} · 用时 ${job.elapsed} 秒`;
            renderBatchAnalysisResult(job);
            $("analysis-result").hidden = !(job.overallReport || (job.targetReports && Object.keys(job.targetReports).length > 0));
            $("analysis-panel").hidden = false;
            if (job.status === "running") {
              clearInterval(state.analysisPolling);
              state.analysisPolling = setInterval(pollBatchAnalysis, 2000);
              await pollBatchAnalysis();
            }
            return;
          }
        } else if (job && job.status === "failed") {
          localStorage.removeItem("dictation-batch-analysis-id");
        }
      } catch (err) {
        localStorage.removeItem("dictation-batch-analysis-id");
      }
    }

    const storageKey = analysisStorageKey();
    const analysisId = storageKey ? localStorage.getItem(storageKey) : "";
    if (!analysisId) {
      if (!state.analysisPolling) {
        $("analysis-result").hidden = true;
        $("analysis-log").hidden = true;
        $("analysis-status").dataset.status = "idle";
        $("analysis-status").textContent = "未开始";
        $("analysis-progress").textContent = "";
      }
      return;
    }
    state.analysisId = analysisId;
    state.analysisMode = "single";
    state.analysisLogCursor = 0;
    $("analysis-log").textContent = "";
    $("analysis-log").hidden = false;
    $("analysis-status").dataset.status = "running";
    $("analysis-status").textContent = "恢复中";
    try {
      await pollWholeAnalysis();
      if (state.analysisPolling === null && $("analysis-status").dataset.status === "running") {
        state.analysisPolling = setInterval(pollWholeAnalysis, 2000);
      }
    } catch (error) {
      if (analysisStorageKey()) localStorage.removeItem(analysisStorageKey());
    }
  }

  async function pollWholeAnalysis() {
    if (!state.analysisId) return;
    try {
      const job = await api(`/api/analyses/${encodeURIComponent(state.analysisId)}?since=${state.analysisLogCursor}`);
      for (const line of job.log || []) {
        $("analysis-log").textContent += ($("analysis-log").textContent ? "\n" : "") + line;
      }
      state.analysisLogCursor = job.logCursor;
      const total = job.total || 0;
      $("analysis-progress").textContent = total
        ? `已完成 ${job.progress}/${total} 个分析阶段 · 用时 ${job.elapsed} 秒`
        : `正在读取整课内容 · 用时 ${job.elapsed} 秒`;
      if (job.status === "succeeded") {
        clearInterval(state.analysisPolling);
        state.analysisPolling = null;
        $("analysis-status").dataset.status = "succeeded";
        $("analysis-status").textContent = "完成";
        $("analysis-report-title").textContent = "分析报告";
        $("report-selector-bar").hidden = true;
        $("analysis-report").textContent = job.report;
        updateFilePathDisplay(job.reportPath);
        $("analysis-result").hidden = false;
        $("start-analysis").disabled = false;
      } else if (job.status === "failed") {
        clearInterval(state.analysisPolling);
        state.analysisPolling = null;
        $("analysis-status").dataset.status = "failed";
        $("analysis-status").textContent = "失败";
        $("start-analysis").disabled = false;
      } else if (!state.analysisPolling) {
        state.analysisPolling = setInterval(pollWholeAnalysis, 2000);
      }
    } catch (error) {
      clearInterval(state.analysisPolling);
      state.analysisPolling = null;
      $("analysis-status").dataset.status = "failed";
      $("analysis-status").textContent = "失败";
      $("analysis-progress").textContent = String(error.message || error);
      $("start-analysis").disabled = false;
      if (analysisStorageKey()) localStorage.removeItem(analysisStorageKey());
    }
  }

  async function copyAnalysis() {
    try {
      await navigator.clipboard.writeText($("analysis-report").textContent);
      $("copy-analysis").textContent = "已复制";
      setTimeout(() => { $("copy-analysis").textContent = "复制报告"; }, 1500);
    } catch (error) {
      $("analysis-progress").textContent = `复制失败：${error.message || error}`;
    }
  }

  function downloadAnalysis() {
    const text = $("analysis-report").textContent;
    if (!text || !text.trim()) return;

    let filename = "validation-report.md";
    if (state.analysisMode === "batch") {
      const select = $("analysis-report-view-select");
      const val = select ? select.value : "overall";
      if (val === "overall") {
        const idSuffix = (state.analysisId || "").slice(0, 8);
        filename = `batch-validation-report${idSuffix ? `-${idSuffix}` : ""}.md`;
      } else {
        const parts = val.split(":");
        const targetId = parts[1] || val;
        filename = `${targetId}_validation-report.md`;
      }
    } else if (state.mode === "course" && state.course) {
      filename = `${state.course.title || state.course.name}_validation-report.md`;
    } else if (state.mode === "draft" && state.draft) {
      filename = `${state.draft.title || state.draft.jobId}_validation-report.md`;
    }

    const safeName = filename.replace(/[\\/:*?"<>|]/g, "_");
    try {
      const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = safeName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      $("analysis-progress").textContent = `下载失败：${error.message || error}`;
    }
  }

  function wire() {
    applyDefaults();
    $("analysis-report-view-select").addEventListener("change", onReportViewSelectChange);
    $("start-analysis").addEventListener("click", startWholeAnalysis);
    if ($("start-queue-analysis")) $("start-queue-analysis").addEventListener("click", startQueueAnalysisAction);
    $("copy-analysis").addEventListener("click", copyAnalysis);
    if ($("download-analysis")) $("download-analysis").addEventListener("click", downloadAnalysis);
    window.addEventListener("beforeunload", () => {
      if (state.analysisPolling) clearInterval(state.analysisPolling);
    });
  }

  return { defaultFocus: DEFAULT_FOCUS, applyDefaults, startWhole: startWholeAnalysis, startForSelection: startBatchAnalysisAction, startForQueue: startQueueAnalysisAction, approveSelection: batchApproveAction, restore: restoreWholeAnalysis, download: downloadAnalysis, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = EditorAnalysis;
if (typeof window !== "undefined") window.EditorAnalysis = EditorAnalysis;
