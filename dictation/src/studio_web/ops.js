"use strict";

/**
 * 运维 — the page that operates the machine rather than the content.
 *
 * GPU telemetry and model services used to sit above the build form, so the two
 * things a person never looks at while making a course occupied the first screen
 * of the page they used to make courses. They are real, they just are not step 1.
 */
(() => {
  const { el, api, describeError } = StudioCore;

  const GPU_POLL_MS = 10000;

  function wire() {
    StudioLocalModels.wire();
    if (el("refresh-gpu-panel")) el("refresh-gpu-panel").addEventListener("click", StudioGpu.refreshCards);
  }

  async function bootstrap() {
    try {
      await StudioCore.session();
      StudioState.config = await api("/api/config");
      StudioSetup.render();
      await StudioGpu.refreshCards();
      StudioGpu.poll(StudioGpu.refreshCards, GPU_POLL_MS);
      await StudioLocalModels.refresh();
    } catch (error) {
      el("fatal").hidden = false;
      el("fatal-message").textContent = describeError(error);
    }
  }

  wire();
  bootstrap();
})();
