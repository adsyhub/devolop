"use strict";

/**
 * 已装课程 · 逐句编辑 — the sentence list, the fields, and one save.
 *
 * A save sends the manifest revision it was loaded at, so a second editor open on
 * the same course is rejected by the server rather than silently overwriting.
 */
const EditorCourse = (() => {
  const $ = StudioCore.el;
  const api = StudioCore.api;
  const fillSelect = StudioCore.fillSelect;
  const state = EditorState;
  const targetKey = EditorState.targetKey;

  async function openCourse(name) {
    state.mode = "course";
    state.course = await api(`/api/courses/${encodeURIComponent(name)}`);
    $("course-editor-page").hidden = false;
    $("editor-mode").textContent = "已装课程 · 逐句编辑";
    $("page-heading").textContent = state.course.title || name;
    updateCourseMeta();
    $("course-title").value = state.course.title;
    renderSentenceList();
  }

  function updateCourseMeta() {
    const review = state.course.review || { reviewed: 0, total: state.course.sentences.length };
    $("editor-meta").textContent = `${state.course.language} · ${state.course.sentences.length} 句 · 已复核 ${review.reviewed}/${review.total} · 质量状态 ${state.course.quality.status}`;
  }

  function sentenceLabel(sentence, ordinal) {
    const source = String(sentence.sourceText || sentence.jaText || "").replace(/\s+/g, " ");
    return `${ordinal + 1}. ${source.slice(0, 70)}`;
  }

  function renderSentenceList(preferredId = "") {
    const query = $("course-search").value.trim().toLowerCase();
    const options = [];
    state.course.sentences.forEach((sentence, index) => {
      const haystack = [sentence.sourceText, sentence.jaText, sentence.translationText,
        sentence.zhTranslation, sentence.explanationText].join(" ").toLowerCase();
      if (!query || haystack.includes(query)) options.push({ value: sentence.id, label: sentenceLabel(sentence, index) });
    });
    const existing = preferredId || $("sentence-list").value;
    fillSelect($("sentence-list"), options, options.some((item) => item.value === existing) ? existing : (options[0] || {}).value);
    showSentence();
  }

  function selectedSentence() {
    return state.course && state.course.sentences.find((sentence) => sentence.id === $("sentence-list").value);
  }

  function showSentence() {
    const sentence = selectedSentence();
    if (!sentence) return;
    $("sentence-start").value = sentence.startTime ?? "";
    $("sentence-end").value = sentence.endTime ?? "";
    $("sentence-confidence").value = sentence.confidence ?? "";
    $("sentence-content-type").value = sentence.contentType || "dialogue";
    $("sentence-practice").checked = sentence.practiceEligible !== false;
    $("sentence-source").value = sentence.sourceText || sentence.jaText || "";
    $("sentence-translation").value = sentence.translationText || sentence.zhTranslation || "";
    $("sentence-explanation").value = sentence.explanationText || "";
    $("course-save-state").textContent = "";
  }

  function sentenceFields() {
    return {
      sourceText: $("sentence-source").value,
      translationText: $("sentence-translation").value,
      explanationText: $("sentence-explanation").value,
      startTime: $("sentence-start").value,
      endTime: $("sentence-end").value,
      confidence: $("sentence-confidence").value,
      contentType: $("sentence-content-type").value,
      practiceEligible: $("sentence-practice").checked,
    };
  }

  async function saveSentence() {
    const sentence = selectedSentence();
    if (!sentence) return;
    const button = $("save-sentence");
    button.disabled = true;
    $("course-save-state").textContent = "保存并重新审计中…";
    try {
      state.course = await api(`/api/courses/${encodeURIComponent(state.course.name)}/save`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          revision: state.course.revision, sentenceId: sentence.id,
          title: $("course-title").value, fields: sentenceFields(),
        }),
      });
      $("course-save-state").textContent = `已保存并留存备份；质量状态 ${state.course.quality.status}。`;
      $("page-heading").textContent = state.course.title;
      updateCourseMeta();
      renderSentenceList(sentence.id);
      await EditorTargets.load();
    } catch (error) {
      $("course-save-state").textContent = String(error.message || error);
    } finally {
      button.disabled = false;
    }
  }


  function wire() {
    $("course-search").addEventListener("input", () => renderSentenceList());
    $("sentence-list").addEventListener("change", showSentence);
    $("save-sentence").addEventListener("click", saveSentence);
  }

  return { open: openCourse, renderSentenceList, showSentence, selectedSentence, fields: sentenceFields, save: saveSentence, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = EditorCourse;
if (typeof window !== "undefined") window.EditorCourse = EditorCourse;
