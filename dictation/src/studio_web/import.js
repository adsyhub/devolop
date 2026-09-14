"use strict";

/**
 * 教材入库 — the page shell for the pipeline that ends at a draft.
 *
 * It is deliberately not part of 制课. A PDF never becomes a course here: OCR and
 * the suspicious-page retries run automatically, and then it stops, because an
 * answer key must not be guessed and a 目次 count must not be taken from the same
 * OCR that is supposed to be checked against it. The next step is a person.
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
      StudioPipelines.select("pdf");
      await StudioJobs.restoreLatest();
    } catch (error) {
      el("fatal").hidden = false;
      el("fatal-message").textContent = describeError(error);
    }
  }

  wire();
  bootstrap();
})();
