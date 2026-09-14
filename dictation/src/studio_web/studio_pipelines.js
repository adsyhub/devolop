"use strict";

/**
 * The three pipelines as a list, instead of three branches in every function.
 *
 * Tab switching, the start button's label and its enabled state all used to read
 * `state.source` and fan out with `source === "pdf" ? … : source === "video" ? …`,
 * once per question asked. Adding a fourth front end meant finding every one of
 * those. Here each pipeline answers the same five questions about itself and this
 * module never knows which one it is holding.
 */
const StudioPipelines = (() => {
  const { el } = StudioCore;

  // Which pipelines exist is decided by the page's <script> tags, not by a list
  // here: 制课 loads audio and video, 教材入库 loads pdf. Adding a front end means
  // adding a file and a tag, never editing a registry in the middle.
  const ALL = [
    typeof PipelineAudio !== "undefined" ? PipelineAudio : null,
    typeof PipelineVideo !== "undefined" ? PipelineVideo : null,
    typeof PipelinePdf !== "undefined" ? PipelinePdf : null,
  ].filter(Boolean);

  /** Fields that only make sense for a build that transcribes and enriches. */
  const COMMON_FIELD_IDS = [
    "language-field", "asr-profile-field", "enrich-field", "text-profile-field", "common-advanced",
  ];

  const current = () => ALL.find((pipeline) => pipeline.id === StudioState.source) || ALL[0];

  /** The pipeline a job of this kind came from, or null if not on this page. */
  const byKind = (kind) => ALL.find((pipeline) => pipeline.id === kind) || null;

  /** Job kinds this entry point is responsible for showing. */
  const kinds = () => ALL.map((pipeline) => pipeline.id);

  function select(id) {
    StudioState.source = id;
    for (const pipeline of ALL) {
      const active = pipeline.id === id;
      // An entry point with a single pipeline has no tab strip to update.
      if (el(pipeline.tabId)) {
        el(pipeline.tabId).classList.toggle("active", active);
        el(pipeline.tabId).setAttribute("aria-selected", String(active));
      }
      if (el(pipeline.fieldsId)) el(pipeline.fieldsId).hidden = !active;
    }
    const pipeline = current();
    for (const fieldId of COMMON_FIELD_IDS) {
      if (el(fieldId)) el(fieldId).hidden = !pipeline.usesCommonFields;
    }
    if (el("title")) el("title").placeholder = pipeline.titlePlaceholder;
    // The enrichment model field has its own condition on top of the pipeline's.
    StudioSetup.updateHints();
    updateStartState();
  }

  function updateStartState() {
    const pipeline = current();
    const ready = pipeline.hasSource() && pipeline.modelReady();
    const queueRunning = StudioState.batchJobs
      .some((job) => ["queued", "running", "cancelling"].includes(job.status));
    el("start").disabled = !ready || queueRunning || Boolean(StudioState.jobId && StudioJobs.isRunning());
    el("start").textContent = pipeline.startLabel(pipeline.count());
  }

  /** Hand the current pipeline the start button. Its answer is a job or a batch. */
  const start = () => current().start();

  function wire() {
    for (const pipeline of ALL) {
      if (el(pipeline.tabId)) el(pipeline.tabId).addEventListener("click", () => select(pipeline.id));
      if (pipeline.wire) pipeline.wire();
    }
  }

  return { all: ALL, current, byKind, kinds, select, updateStartState, start, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioPipelines;
if (typeof window !== "undefined") window.StudioPipelines = StudioPipelines;
