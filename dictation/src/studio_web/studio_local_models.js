"use strict";

/**
 * The local model services panel — the one part of this page that operates the
 * machine rather than the content.
 *
 * Starting a service can take minutes, so the panel polls itself while any
 * control is running and stops as soon as none is. When the last one finishes it
 * re-reads the provider config, because a service coming online is exactly what
 * turns a greyed-out profile in 准备 into a selectable one.
 */
const StudioLocalModels = (() => {
  const { el, api, post, text, describeError } = StudioCore;

  const POLL_MS = 2000;

  function render(payload) {
    el("local-model-summary").textContent = `在线 ${payload.ready}/${payload.total}；启动可能需要数分钟。`;
    const cards = (payload.services || []).map((service) => {
      const card = text("div", "model-card", "");
      card.append(text("strong", "", service.label));
      card.append(text("span", "hint", service.role));
      const control = service.control;
      const running = control && control.status === "running";
      const stateLabel = service.available ? "在线"
        : running && control.action === "start" ? "启动中"
          : running && control.action === "stop" ? "停止中"
            : control && control.status === "failed" ? "启动失败" : "未启动";
      const badgeClass = service.available ? "passed" : running ? "needs_review" : "broken";
      card.append(text("span", `badge ${badgeClass}`, stateLabel));

      const actions = text("div", "model-actions", "");
      const start = text("button", "course-action", "启动");
      start.type = "button";
      start.disabled = !payload.canStart || service.available || running;
      start.addEventListener("click", () => control_("start", service.name));
      const stop = text("button", "course-action danger", "停止");
      stop.type = "button";
      stop.disabled = !payload.canStop || (!service.available && !(running && control.action === "start"));
      stop.addEventListener("click", () => control_("stop", service.name));
      actions.append(start, stop);
      card.append(actions);
      return card;
    });
    el("local-models").replaceChildren(...cards);

    const controls = Object.values(payload.controls || {});
    const startingCount = controls.filter((item) => item.status === "running" && item.action === "start").length;
    const stoppingCount = controls.filter((item) => item.status === "running" && item.action === "stop").length;
    el("start-local-models").disabled = !payload.canStart
      || payload.ready === payload.total || startingCount === payload.total;
    el("stop-local-models").disabled = !payload.canStop
      || stoppingCount > 0 || (payload.ready === 0 && startingCount === 0);

    if ((payload.history || []).length) {
      el("local-model-log-wrap").hidden = false;
      el("local-model-log").textContent = payload.history.map((job) => {
        const heading = `[${job.service}] ${job.action} · ${job.status}`;
        return [heading].concat(job.log || []).join("\n");
      }).join("\n\n");
      el("local-model-log").scrollTop = el("local-model-log").scrollHeight;
    }
    el("local-model-error").hidden = true;
  }

  async function refresh() {
    try {
      const payload = await api("/api/local-models");
      render(payload);
      const running = Object.values(payload.controls || {}).some((item) => item.status === "running");
      const justFinished = StudioState.localModelRunning && !running;
      StudioState.localModelRunning = running;
      if (justFinished) {
        StudioState.config = await api("/api/config");
        StudioSetup.render();
      }
      clearTimeout(StudioState.localModelPolling);
      if (running) StudioState.localModelPolling = setTimeout(refresh, POLL_MS);
    } catch (error) {
      el("local-model-error").hidden = false;
      el("local-model-error").textContent = describeError(error);
    }
  }

  // `control` is a parameter name inside render(); the trailing underscore keeps
  // this function callable from there without shadowing confusion.
  async function control_(action, service = "all") {
    el("start-local-models").disabled = true;
    el("stop-local-models").disabled = true;
    el("local-model-error").hidden = true;
    try {
      await post(`/api/local-models/${action}`, { service });
    } catch (error) {
      el("local-model-error").hidden = false;
      el("local-model-error").textContent = describeError(error);
    }
    await refresh();
  }

  /** Re-read provider availability without touching the services themselves. */
  async function refreshModels() {
    const button = el("refresh-models");
    button.disabled = true;
    button.textContent = "检测中…";
    try {
      StudioState.config = await api("/api/config");
      StudioSetup.render();
      await refresh();
    } catch (error) {
      StudioSetup.showError(describeError(error));
    } finally {
      button.disabled = false;
      button.textContent = "刷新模型状态";
    }
  }

  function wire() {
    el("refresh-models").addEventListener("click", refreshModels);
    el("start-local-models").addEventListener("click", () => control_("start"));
    el("stop-local-models").addEventListener("click", () => control_("stop"));
  }

  return { render, refresh, control: control_, refreshModels, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioLocalModels;
if (typeof window !== "undefined") window.StudioLocalModels = StudioLocalModels;
