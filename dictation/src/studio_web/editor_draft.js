"use strict";

/**
 * 待复核草稿 · 逐页编辑 — the scanned page beside the structured JSON it produced.
 *
 * The JSON is edited as text on purpose: a page file is the human-editable source
 * of truth for the whole lexicon pipeline, and a form would quietly drop the
 * fields it did not know about.
 */
const EditorDraft = (() => {
  const $ = StudioCore.el;
  const api = StudioCore.api;
  const fillSelect = StudioCore.fillSelect;
  const state = EditorState;
  const targetKey = EditorState.targetKey;

  async function openDraft(jobId) {
    state.mode = "draft";
    state.draft = await api(`/api/drafts/${encodeURIComponent(jobId)}`);
    $("draft-editor-page").hidden = false;
    $("editor-mode").textContent = "待复核草稿 · 逐页编辑";
    $("page-heading").textContent = state.draft.title;
    updateDraftMeta();
    renderDraftPageList();
    if (state.draft.pages.length) await loadDraftPage(state.draft.pages[0].name);
  }

  function updateDraftMeta() {
    const review = state.draft.review || { reviewed: 0, total: state.draft.pages.length };
    $("editor-meta").textContent = `${state.draft.kind} · ${state.draft.level || "未分级"} · ${state.draft.pages.length} 页 · 已复核 ${review.reviewed}/${review.total} · 修改会保留备份`;
  }

  function renderDraftPageList(preferred = "") {
    const query = $("draft-search").value.trim().toLowerCase();
    const options = state.draft.pages.filter((page) => {
      const label = `${page.name} ${page.page || ""}`.toLowerCase();
      return !query || label.includes(query);
    }).map((page) => ({
      value: page.name,
      label: `第 ${page.page ?? "?"} 页 · ${page.blocks} 块 · ${page.issues} 疑点`,
    }));
    const selected = preferred || $("draft-page-list").value;
    fillSelect($("draft-page-list"), options, options.some((item) => item.value === selected) ? selected : (options[0] || {}).value);
  }

  async function loadDraftPage(name) {
    if (!name) return;
    $("draft-save-state").textContent = "正在加载…";
    try {
      state.draftPage = await api(`/api/drafts/${encodeURIComponent(state.draft.jobId)}/pages/${encodeURIComponent(name)}`);
      $("draft-page-list").value = name;
      $("draft-json").value = JSON.stringify(state.draftPage.document, null, 2);
      $("draft-source").textContent = state.draftPage.sourceMarkdown || "没有 OCR 原始文本。";
      await loadDraftImage(state.draftPage.imageUrl);
      $("draft-save-state").textContent = "";
    } catch (error) {
      $("draft-save-state").textContent = String(error.message || error);
    }
  }

  async function loadDraftImage(path) {
    if (state.imageObjectUrl) URL.revokeObjectURL(state.imageObjectUrl);
    state.imageObjectUrl = "";
    $("draft-image").hidden = true;
    if (!path) return;
    try {
      const blob = await StudioCore.fetchBlob(path);
      state.imageObjectUrl = URL.createObjectURL(blob);
      $("draft-image").src = state.imageObjectUrl;
      $("draft-image").hidden = false;
    } catch (error) {
      $("draft-image").hidden = true;
      $("draft-save-state").textContent = `原图加载失败：${StudioCore.describeError(error)}`;
    }
  }

  function parsedDraftDocument() {
    let document;
    try {
      document = JSON.parse($("draft-json").value);
    } catch (error) {
      throw new Error(`JSON 格式错误：${error.message}`);
    }
    if (!document || Array.isArray(document) || typeof document !== "object") throw new Error("页面必须是一个 JSON 对象。");
    return document;
  }

  async function saveDraft() {
    if (!state.draftPage) return;
    const button = $("save-draft");
    button.disabled = true;
    $("draft-save-state").textContent = "正在验证并保存…";
    try {
      state.draftPage = await api(`/api/drafts/${encodeURIComponent(state.draft.jobId)}/pages/${encodeURIComponent(state.draftPage.name)}/save`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ revision: state.draftPage.revision, document: parsedDraftDocument() }),
      });
      $("draft-json").value = JSON.stringify(state.draftPage.document, null, 2);
      $("draft-save-state").textContent = "已保存当前页，并在 .workbench-backups 中保留修改前版本。";
      state.draft = await api(`/api/drafts/${encodeURIComponent(state.draft.jobId)}`);
      updateDraftMeta();
      renderDraftPageList(state.draftPage.name);
      await EditorTargets.load();
    } catch (error) {
      $("draft-save-state").textContent = String(error.message || error);
    } finally {
      button.disabled = false;
    }
  }


  function wire() {
    $("draft-search").addEventListener("input", () => renderDraftPageList());
    $("draft-page-list").addEventListener("change", (event) => loadDraftPage(event.target.value));
    $("save-draft").addEventListener("click", saveDraft);
    // The scan image is held as an object URL; without this the page leaks one per
    // page turn for as long as the editor stays open.
    window.addEventListener("beforeunload", () => {
      if (state.imageObjectUrl) URL.revokeObjectURL(state.imageObjectUrl);
    });
  }

  return { open: openDraft, renderDraftPageList, loadDraftPage, parsedDocument: parsedDraftDocument, save: saveDraft, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = EditorDraft;
if (typeof window !== "undefined") window.EditorDraft = EditorDraft;
