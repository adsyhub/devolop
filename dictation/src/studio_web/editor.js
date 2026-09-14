"use strict";

/**
 * 课件复核编辑器 — the page shell.
 *
 * The editor is four panels over two kinds of target, and the only thing that is
 * genuinely the page's own job is the part below: claim a session, load the model
 * list once, let each panel wire itself, and keep the URL and the open target in
 * step so a link to `?course=` or `?build=` opens the right thing and the back
 * button still works.
 */
(() => {
  const { el, api, describeError } = StudioCore;

  function fail(error) {
    el("fatal").hidden = false;
    el("fatal-message").textContent = describeError(error);
  }

  /** Show whatever the query string names, or the picker when it names nothing. */
  async function openFromUrl(updateUrl = false) {
    const params = new URLSearchParams(window.location.search);
    const course = params.get("course");
    const build = params.get("build");
    if (course && !build) await EditorTargets.activate("course", course, updateUrl);
    else if (build && !course) await EditorTargets.activate("draft", build, updateUrl);
    else EditorTargets.showPrompt(updateUrl);
  }

  function wire() {
    EditorTargets.wire();
    EditorCourse.wire();
    EditorDraft.wire();
    EditorReview.wire();
    EditorAnalysis.wire();

    window.addEventListener("popstate", async () => {
      try {
        await openFromUrl(false);
      } catch (error) {
        fail(error);
      }
    });
  }

  async function bootstrap() {
    try {
      await StudioCore.session();
      StudioStatusPill.mount();
      EditorState.config = await api("/api/config");
      EditorReview.fillModels();
      await EditorTargets.load();
      await openFromUrl(false);
    } catch (error) {
      fail(error);
    }
  }

  wire();
  bootstrap();
})();
