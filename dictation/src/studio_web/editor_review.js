"use strict";

/**
 * 模型复核与复合编辑 — ask a model for a candidate, never for a commit.
 *
 * The proposal is written into the edit boxes and nowhere else; saving stays a
 * separate, human action in the panel that owns the content. The model list is
 * here too, because this panel and the analysis panel are the only two that use
 * one, and both must refuse to offer `manual` or `echo`.
 */
const EditorReview = (() => {
  const $ = StudioCore.el;
  const api = StudioCore.api;
  const fillSelect = StudioCore.fillSelect;
  const state = EditorState;
  const targetKey = EditorState.targetKey;

  /**
   * A starting 复核要求, per kind of target.
   *
   * The server refuses an empty instruction (1–4000 characters), so an empty box
   * meant every session began by typing one — and what it should say depends on
   * what is open: a draft page is corrected against its OCR source and returned as
   * the same JSON, a course sentence is three text fields in a known language.
   *
   * These are *defaults*, not a fixed prompt: `applyDefaults()` only writes when
   * the box is empty or still holds one of them, so edited text is never lost.
   */
  const DEFAULT_INSTRUCTIONS = {
    draft: "对照扫描原页和 OCR 原文逐字核对本页：修正同音字与误识别的假名、补回漏掉的结构，"
      + "只改有原文依据的地方；拿不准的保持原样，不要臆造答案、译文或出处。",
    course: "对照日语原文核对本句：修正转写里的同音字与误识别，检查中文翻译是否准确、"
      + "讲解是否与原文一致；只改有依据的地方，不要臆造事实或改变原文语言。",
  };

  const isDefault = (value) => Object.values(DEFAULT_INSTRUCTIONS).includes(value.trim());

  /** Put the right starting instruction in the box, without overwriting edits. */
  function applyDefaults() {
    const box = $("review-instruction");
    if (!box) return;
    const wanted = DEFAULT_INSTRUCTIONS[state.mode] || DEFAULT_INSTRUCTIONS.course;
    if (!box.value.trim() || isDefault(box.value)) box.value = wanted;
  }

  let available = 0;

  /** Whether this editor has any model it is allowed to call. */
  const hasModels = () => available > 0;

  function fillModels() {
    const profiles = (state.config.textProfiles || []).filter((profile) =>
      profile.available && !["manual", "echo"].includes(profile.kind)
    );
    available = profiles.length;
    const options = profiles.map((profile) => ({
      value: profile.name,
      label: `${profile.name} · ${profile.source} · ${profile.model || profile.kind}`,
    }));
    const saved = typeof localStorage !== "undefined" && localStorage.getItem("dictation-selected-text-profile");
    const initial = (saved && profiles.some((p) => p.name === saved))
      ? saved
      : (profiles[0] ? profiles[0].name : "");
    fillSelect($("review-model"), options, initial);
    fillSelect($("analysis-model"), options, initial);
    $("run-model-review").disabled = !hasModels();
    if (!hasModels()) $("model-state").textContent = "当前没有可用的自动模型，请到工作台的「运维」启动本地模型，或配置 CLI/API。";
    EditorTargets.updateButtons();
  }

  async function runModelReview() {
    const instruction = $("review-instruction").value.trim();
    if (!instruction) {
      $("model-state").textContent = "请先填写复核要求。";
      return;
    }
    const button = $("run-model-review");
    button.disabled = true;
    $("model-state").textContent = "模型正在基于当前手工修改生成候选稿…";
    try {
      if (state.mode === "course") {
        const sentence = EditorCourse.selectedSentence();
        const result = await api(`/api/courses/${encodeURIComponent(state.course.name)}/revise`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            revision: state.course.revision, sentenceId: sentence.id,
            textProfile: $("review-model").value, instruction, fields: EditorCourse.fields(),
          }),
        });
        $("sentence-source").value = result.proposal.sourceText;
        $("sentence-translation").value = result.proposal.translationText;
        $("sentence-explanation").value = result.proposal.explanationText;
        $("model-state").textContent = `候选稿来自 ${result.model}；尚未保存，请人工检查。`;
      } else {
        const result = await api(`/api/drafts/${encodeURIComponent(state.draft.jobId)}/pages/${encodeURIComponent(state.draftPage.name)}/revise`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            revision: state.draftPage.revision, textProfile: $("review-model").value,
            instruction, document: EditorDraft.parsedDocument(),
          }),
        });
        $("draft-json").value = JSON.stringify(result.proposal, null, 2);
        $("model-state").textContent = `候选稿来自 ${result.model}；尚未保存，请对照扫描页检查。`;
      }
    } catch (error) {
      $("model-state").textContent = String(error.message || error);
    } finally {
      button.disabled = false;
    }
  }


  function wire() {
    $("run-model-review").addEventListener("click", runModelReview);
    applyDefaults();
    const saveAndSync = (sourceId, targetId) => {
      const src = $(sourceId);
      const tgt = $(targetId);
      if (!src) return;
      src.addEventListener("change", () => {
        const val = src.value;
        if (typeof localStorage !== "undefined") {
          localStorage.setItem("dictation-selected-text-profile", val);
        }
        if (tgt && tgt.value !== val) tgt.value = val;
      });
    };
    saveAndSync("analysis-model", "review-model");
    saveAndSync("review-model", "analysis-model");
  }

  return { fillModels, hasModels, applyDefaults, defaults: DEFAULT_INSTRUCTIONS, run: runModelReview, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = EditorReview;
if (typeof window !== "undefined") window.EditorReview = EditorReview;
