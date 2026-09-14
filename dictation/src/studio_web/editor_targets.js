"use strict";

/**
 * 待复核列表 — which courses and drafts still need a person, and which one the
 * page is currently showing.
 *
 * This module owns the selection: the checkbox set, the "连续复核" queue that walks
 * it, and `activateTarget`, the single door through which every other panel is
 * shown or hidden. Nothing else may decide what the page is looking at.
 */
const EditorTargets = (() => {
  const $ = StudioCore.el;
  const api = StudioCore.api;
  const fillSelect = StudioCore.fillSelect;
  const state = EditorState;
  const targetKey = EditorState.targetKey;

  /**
   * The two kinds of review target, which are not the same job.
   *
   * A draft is a PDF that has been OCR'd and must be read page by page before it
   * may enter the library at all; a course is already installed and is being
   * corrected sentence by sentence. They were one table with a 类型 column, which
   * made "12 things need you" out of two queues with different urgency and
   * different units. Each is its own collapsed section now, and the unit in the
   * 剩余 column is the real one rather than "句/页".
   */
  const GROUPS = [
    { kind: "draft", unit: "页", body: "draft-table-body", toggle: "toggle-all-drafts",
      count: "draft-group-count", noun: "个草稿" },
    { kind: "course", unit: "句", body: "course-table-body", toggle: "toggle-all-courses",
      count: "course-group-count", noun: "门课程" },
    { kind: "reviewed_draft", unit: "页", body: "reviewed-draft-table-body", toggle: "toggle-all-reviewed-drafts",
      count: "reviewed-draft-group-count", noun: "个草稿", isReviewed: true },
  ];

  const targetsOf = (groupOrKind) => {
    const group = typeof groupOrKind === "string"
      ? (GROUPS.find((g) => g.kind === groupOrKind) || { kind: groupOrKind })
      : groupOrKind;
    if (group.isReviewed) {
      return state.reviewTargets.filter((target) => target.targetKind === "draft" && target.isReviewed);
    }
    return state.reviewTargets.filter((target) => target.targetKind === group.kind && !target.isReviewed);
  };

  function updateButtons() {
    const queueBtn = $("start-queue-analysis");
    const singleBtn = $("start-analysis");
    if (!singleBtn) return;

    // Two separate reasons a start button can be dead, and they used to be set
    // from two places that overwrote each other: no model is configured at all,
    // or nothing has been picked to analyse yet.
    const noModels = typeof EditorReview !== "undefined" && !EditorReview.hasModels();
    const nothing = !state.mode && !(state.selectedTargetKeys && state.selectedTargetKeys.size);
    singleBtn.disabled = noModels || nothing;
    if (queueBtn) queueBtn.disabled = noModels || nothing;

    if (state.multiQueue && state.multiQueue.length > 1) {
      if (queueBtn) {
        queueBtn.hidden = false;
        queueBtn.textContent = `批量分析连续复核队列（共 ${state.multiQueue.length} 门）`;
      }
      singleBtn.textContent = "仅分析当前课程";
    } else if (state.selectedTargetKeys && state.selectedTargetKeys.size > 1) {
      if (queueBtn) {
        queueBtn.hidden = false;
        queueBtn.textContent = `批量分析所选课程（共 ${state.selectedTargetKeys.size} 门）`;
      }
      singleBtn.textContent = state.mode ? "仅分析当前课程" : "开始分析所选课程";
    } else {
      if (queueBtn) queueBtn.hidden = true;
      singleBtn.textContent = state.mode ? "开始分析整个课程" : "开始分析所选课程";
    }
  }

  function updateTargetSelectionUI() {
    const count = state.selectedTargetKeys.size;
    $("selected-summary").textContent = `已选择 ${count} 项`;
    $("start-multi-review").disabled = count === 0;
    $("start-batch-analysis-btn").disabled = count === 0;
    $("batch-approve-btn").disabled = count === 0;
    updateButtons();

    for (const group of GROUPS) {
      const rows = targetsOf(group);
      const chosen = rows.filter((target) => state.selectedTargetKeys.has(targetKey(target))).length;
      const toggle = $(group.toggle);
      if (toggle) {
        toggle.checked = rows.length > 0 && chosen === rows.length;
        toggle.indeterminate = chosen > 0 && chosen < rows.length;
        toggle.disabled = rows.length === 0;
      }
    }
  }

  async function load() {
    const payload = await api("/api/review-targets");
    const unreviewed = payload.targets || [];
    const reviewed = (payload.reviewedDrafts || []).map((item) => ({ ...item, isReviewed: true }));
    state.reviewTargets = [...unreviewed, ...reviewed];

    for (const group of GROUPS) {
      const rows = targetsOf(group);
      const tbody = $(group.body);
      if (!tbody) continue;
      tbody.replaceChildren();
      if (!rows.length) {
        const empty = document.createElement("tr");
        const emptyMsg = group.isReviewed ? "目前还没有已完成复核的草稿。" : "这一类目前没有待复核的内容。";
        empty.innerHTML = `<td colspan="5" class="target-empty">${emptyMsg}</td>`;
        tbody.append(empty);
      } else {
        for (const target of rows) tbody.append(renderRow(target, group));
      }
      if (group.isReviewed) {
        $(group.count).textContent = rows.length
          ? `${rows.length} ${group.noun} · 已全部复核`
          : "无";
      } else {
        const remaining = rows.reduce((sum, target) => sum + (target.remaining || 0), 0);
        $(group.count).textContent = rows.length
          ? `${rows.length} ${group.noun} · 剩余 ${remaining} ${group.unit}`
          : "无";
      }
    }

    updateTargetSelectionUI();

    const pendingCount = unreviewed.length;
    const reviewedCount = reviewed.length;
    let summaryText = pendingCount
      ? `共 ${pendingCount} 项尚未完成复核：${payload.drafts || 0} 个构建草稿，${payload.courses || 0} 门已装课程。展开任一类开始。`
      : "目前没有尚未完成复核的课程。";
    if (reviewedCount > 0) {
      summaryText += `另有 ${reviewedCount} 个已完成复核的草稿。`;
    }
    $("review-target-summary").textContent = summaryText;
    $("review-picker").hidden = Boolean(state.mode);
    if ($("top-model-panel")) $("top-model-panel").hidden = Boolean(state.mode);
  }

  function renderRow(target, group) {
    // The index is into the whole list, not into this group's slice: every other
    // handler resolves a row through `state.reviewTargets[index]`.
    const index = state.reviewTargets.indexOf(target);
    const key = targetKey(target);
    const selected = state.selectedTargetKeys.has(key);
    const percent = target.total > 0 ? Math.round((target.reviewed / target.total) * 100) : 0;
    const row = document.createElement("tr");
    if (selected) row.classList.add("selected");
    const remainingCol = group.isReviewed
      ? `<span class="badge success" style="font-size: .75rem; padding: .1rem .4rem;">已完成</span>`
      : `<span class="hint">${target.remaining} ${group.unit}</span>`;
    const actionText = group.isReviewed ? "查看 / 编辑" : "单独编辑";
    row.innerHTML = `
      <td><input type="checkbox" class="target-checkbox" data-key="${key}" data-index="${index}" ${selected ? "checked" : ""}></td>
      <td><strong>${StudioCore.escapeHtml(target.title)}</strong> ${target.level ? `<span class="hint">(${StudioCore.escapeHtml(target.level)})</span>` : ""}</td>
      <td>
        <div class="progress-bar-inline">
          <progress value="${target.reviewed}" max="${target.total}"></progress>
          <span class="hint">${target.reviewed}/${target.total} (${percent}%)</span>
        </div>
      </td>
      <td>${remainingCol}</td>
      <td>
        <button type="button" class="action-small open-single-btn" data-index="${index}">${actionText}</button>
      </td>
    `;
    return row;
  }

  function updateMultiNavUI() {
    const nav = $("multi-course-nav");
    if (!state.multiQueue || state.multiQueue.length <= 1) {
      if (nav) nav.hidden = true;
      updateButtons();
      return;
    }
    if (nav) nav.hidden = false;
    const curr = state.multiQueue[state.multiIndex] || {};
    $("multi-counter").textContent = `第 ${state.multiIndex + 1} / ${state.multiQueue.length} 门（${curr.title || ""}）`;
    $("multi-prev").disabled = state.multiIndex <= 0;
    $("multi-next").disabled = state.multiIndex >= state.multiQueue.length - 1;
    updateButtons();
  }

  async function startMultiCourseReview() {
    const selected = state.reviewTargets.filter((t) => state.selectedTargetKeys.has(targetKey(t)));
    if (selected.length === 0) return;
    state.multiQueue = selected;
    state.multiIndex = 0;
    await openMultiQueueTarget(0);
  }

  async function openMultiQueueTarget(index) {
    if (index < 0 || index >= state.multiQueue.length) return;
    state.multiIndex = index;
    const target = state.multiQueue[index];
    await activateTarget(target.targetKind, target.targetId, true);
    updateMultiNavUI();
  }

  function exitMultiReview() {
    state.multiQueue = [];
    state.multiIndex = 0;
    $("multi-course-nav").hidden = true;
    updateButtons();
  }

  async function activateTarget(kind, id, updateUrl = true) {
    const isBatchActive = state.analysisMode === "batch" && (state.analysisPolling !== null || (state.batchAnalysis && state.batchAnalysis.status === "running"));
    if (!isBatchActive) {
      if (state.analysisPolling) clearInterval(state.analysisPolling);
      state.analysisPolling = null;
      state.analysisId = "";
      state.analysisLogCursor = 0;
      $("analysis-result").hidden = true;
      $("analysis-log").hidden = true;
      $("analysis-status").dataset.status = "idle";
      $("analysis-status").textContent = "未开始";
    }
    state.course = null;
    state.draft = null;
    state.draftPage = null;
    $("course-editor-page").hidden = true;
    $("draft-editor-page").hidden = true;
    $("review-picker").hidden = true;
    if ($("top-model-panel")) $("top-model-panel").hidden = true;
    $("model-panel").hidden = true;
    $("analysis-panel").hidden = true;
    if (kind === "course") await EditorCourse.open(id);
    else await EditorDraft.open(id);
    if (updateUrl) {
      const query = kind === "course" ? `course=${encodeURIComponent(id)}` : `build=${encodeURIComponent(id)}`;
      window.history.pushState({}, "", `/editor.html?${query}`);
    }
    $("review-picker").hidden = true;
    $("model-panel").hidden = false;
    $("analysis-panel").hidden = false;
    // 逐页核对草稿和逐句订正课程问的不是同一件事，默认要求跟着切换——
    // 但只在这一栏还是默认文案时切，手写过的内容不动。
    EditorReview.applyDefaults();
    if (state.multiQueue && state.multiQueue.length > 1) {
      updateMultiNavUI();
    } else {
      $("multi-course-nav").hidden = true;
    }
    updateButtons();
    await load();
    $("review-picker").hidden = true;
    await EditorAnalysis.restore();
  }

  function showTargetPrompt(updateUrl = false) {
    // A batch analysis belongs to the list, not to any one course, so going back
    // to the list must not throw it away — the server keeps running it either way,
    // and dropping the poll here is how a finished report became unreachable.
    const batchAlive = state.analysisMode === "batch"
      && (state.analysisPolling !== null || (state.batchAnalysis && state.batchAnalysis.status === "running"));
    if (!batchAlive) {
      if (state.analysisPolling) clearInterval(state.analysisPolling);
      state.analysisPolling = null;
      state.analysisId = "";
      state.analysisMode = "single";
      state.batchAnalysis = null;
    }
    state.mode = "";
    state.course = null;
    state.draft = null;
    state.draftPage = null;
    state.multiQueue = [];
    state.multiIndex = 0;
    $("multi-course-nav").hidden = true;
    $("course-editor-page").hidden = true;
    $("draft-editor-page").hidden = true;
    $("review-picker").hidden = false;
    if ($("top-model-panel")) $("top-model-panel").hidden = false;
    // 模型复核 edits whatever is open, so it stays hidden until something is.
    $("model-panel").hidden = true;
    // 整课模型分析 does not need an open course — 批量整课模型分析 runs on the list
    // selection — so its model and 分析重点 are on screen from the start.
    $("analysis-panel").hidden = false;
    $("page-heading").textContent = "课件复核编辑器";
    $("editor-meta").textContent = "请从待复核列表中选择要编辑或分析的课程。可先选好分析模型再开始。";
    $("editor-mode").textContent = "等待选择";
    updateButtons();
    // A batch started from this list keeps running on the server; re-attach to it
    // so the report is reachable from the screen that launched it.
    EditorAnalysis.restore().catch(() => {});
    if (updateUrl) window.history.pushState({}, "", "/editor.html");
  }


  function selectAll(targets, on) {
    for (const target of targets) {
      if (on) state.selectedTargetKeys.add(targetKey(target));
      else state.selectedTargetKeys.delete(targetKey(target));
    }
    load();
  }

  function wire() {
    for (const group of GROUPS) {
      const toggle = $(group.toggle);
      if (toggle) {
        toggle.addEventListener("change", (event) => {
          event.stopPropagation();
          selectAll(targetsOf(group), event.target.checked);
        });
        toggle.addEventListener("click", (event) => event.stopPropagation());
      }

      $(group.body).addEventListener("click", (event) => {
        const button = event.target.closest(".open-single-btn");
        if (!button) return;
        const target = state.reviewTargets[Number(button.dataset.index)];
        if (target) activateTarget(target.targetKind, target.targetId);
      });
      $(group.body).addEventListener("change", (event) => {
        const box = event.target.closest(".target-checkbox");
        if (!box) return;
        if (box.checked) {
          state.selectedTargetKeys.add(box.dataset.key);
          box.closest("tr").classList.add("selected");
        } else {
          state.selectedTargetKeys.delete(box.dataset.key);
          box.closest("tr").classList.remove("selected");
        }
        updateTargetSelectionUI();
      });
    }

    $("select-all-targets").addEventListener("click", () => selectAll(state.reviewTargets, true));
    $("select-none-targets").addEventListener("click", () => selectAll(state.reviewTargets, false));
    $("start-multi-review").addEventListener("click", startMultiCourseReview);
    $("start-batch-analysis-btn").addEventListener("click", () => EditorAnalysis.startForSelection());
    $("batch-approve-btn").addEventListener("click", () => EditorAnalysis.approveSelection());
    $("multi-prev").addEventListener("click", () => openMultiQueueTarget(state.multiIndex - 1));
    $("multi-next").addEventListener("click", () => openMultiQueueTarget(state.multiIndex + 1));
    $("multi-exit").addEventListener("click", () => {
      exitMultiReview();
      showTargetPrompt(true);
    });
  }

  return { load, activate: activateTarget, showPrompt: showTargetPrompt, updateButtons, updateSelection: updateTargetSelectionUI, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = EditorTargets;
if (typeof window !== "undefined") window.EditorTargets = EditorTargets;
