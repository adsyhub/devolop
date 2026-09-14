"use strict";

/**
 * 制课 — the page shell for the two pipelines that end in a course.
 *
 * Audio and video share this entry point because they share a destination and
 * almost every field: both transcribe, both enrich, both land in courses/. PDF
 * does neither and lives at /import.html, which is why this page no longer needs
 * a branch asking whether the current tab is the odd one out.
 */
(() => {
  const { el, api, describeError } = StudioCore;

  function wire() {
    StudioSetup.wire();
    StudioUploads.wire();
    StudioPipelines.wire();
    StudioJobs.wire();
    if (el("refresh-models")) el("refresh-models").addEventListener("click", StudioSetup.reload);
  }

  async function bootstrap() {
    try {
      await StudioCore.session();
      StudioStatusPill.mount();
      StudioState.config = await api("/api/config");
      StudioSetup.render();
      StudioPipelines.select("audio");
      // Restores an audio or video job only; a PDF build belongs to 教材入库.
      await StudioJobs.restoreLatest();
    } catch (error) {
      el("fatal").hidden = false;
      el("fatal-message").textContent = describeError(error);
    }
  }

  wire();
  bootstrap();
})();
