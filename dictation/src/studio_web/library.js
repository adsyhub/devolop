"use strict";

/**
 * 课程库 — what is installed, and the way into the review editor.
 *
 * A list needs neither the provider config nor a build form, so this page loads
 * neither: opening it while a build runs elsewhere costs one request.
 */
(() => {
  const { el, describeError } = StudioCore;

  async function bootstrap() {
    try {
      await StudioCore.session();
      await StudioCourses.refresh();
    } catch (error) {
      el("fatal").hidden = false;
      el("fatal-message").textContent = describeError(error);
    }
  }

  StudioCourses.wire();
  bootstrap();
})();
