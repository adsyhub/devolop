"use strict";

/**
 * Panel 2 · 构建 — one running job, its log, and the batch queue behind it.
 *
 * Everything here is pipeline-agnostic on purpose: a job is started by whichever
 * pipeline owns the form, and from that moment on it is just an id with a status,
 * a log cursor and possibly a bundle to install. The two places that do need to
 * know which pipeline produced it — the install button and the PDF draft summary
 * — ask the job's own `kind` rather than the form's current tab, because the form
 * may have moved on while the job was still running.
 */
const StudioJobs = (() => {
  const { el, api, post, text, showMessage, describeError } = StudioCore;

  const ACTIVE = ["queued", "running", "cancelling"];
  const STATUS_LABELS = {
    queued: "排队中", running: "构建中", cancelling: "正在停止", succeeded: "完成",
    needs_review: "待复核", failed: "失败", cancelled: "已停止",
  };
  const QUEUE_LABELS = Object.assign({}, STATUS_LABELS, { running: "制作中", cancelling: "停止中" });

  const isRunning = () => ACTIVE.includes(el("status-chip").dataset.status);
  const showError = (message) => showMessage("run-error", message);

  function appendLog(line) {
    const log = el("log");
    const atBottom = log.scrollTop + log.clientHeight >= log.scrollHeight - 24;
    log.textContent += (log.textContent ? "\n" : "") + line;
    if (atBottom) log.scrollTop = log.scrollHeight;
  }

  function applyJob(job) {
    el("status-chip").dataset.status = job.status;
    el("status-chip").textContent = STATUS_LABELS[job.status] || job.status;
    const batchLabel = job.batchSize ? ` · 队列 ${job.batchIndex}/${job.batchSize}` : "";
    el("run-meta").textContent = `${job.title}${batchLabel} · 已用 ${job.elapsed}s`;

    for (const line of job.log || []) appendLog(line);
    if (typeof job.logCursor === "number") StudioState.logCursor = job.logCursor;

    el("cancel").hidden = job.status !== "running" && job.status !== "queued";

    // What happens after a job succeeds is the producing pipeline's business, not
    // this module's: a video build writes straight into courses/ and has no ZIP to
    // install, and a PDF build ends at a draft with its own summary. Asking the
    // job's own kind — not the form's current tab — matters because the form may
    // have moved on while the job was still running.
    const pipeline = StudioPipelines.byKind(job.kind);
    el("install").hidden = !(pipeline && pipeline.installable)
      || !(job.status === "succeeded" && job.hasBundle && !job.installedTo);
    if (pipeline && !pipeline.installable && job.status === "succeeded" && job.installedTo) {
      el("run-meta").textContent = `${job.title} · 已装入 ${job.installedTo}`;
    }
    if (pipeline && pipeline.renderResult && job.result) {
      pipeline.renderResult(job.result, job.id);
      el("run-meta").textContent = `${job.title} · 草稿等待人工复核`;
    }
    el("install").disabled = false;
    StudioPipelines.updateStartState();
  }

  // ------------------------------------------------------------ batch queue

  function renderQueue() {
    const box = el("batch-queue");
    if (!StudioState.batchJobs.length) {
      box.hidden = true;
      box.replaceChildren();
      return;
    }
    const heading = text("p", "batch-heading",
      `批次队列 · ${StudioState.batchJobs.length} 个文件 · 后台逐个制作`);
    const list = text("div", "batch-list", "");
    for (const job of StudioState.batchJobs) {
      const button = text("button", `batch-item${job.id === StudioState.jobId ? " active" : ""}`, "");
      button.type = "button";
      button.append(text("span", "batch-title", `${job.batchIndex || ""}. ${job.title}`));
      button.append(text("span", `batch-status ${job.status}`, QUEUE_LABELS[job.status] || job.status));
      button.addEventListener("click", () => view(job.id));
      list.append(button);
    }
    box.replaceChildren(heading, list);
    box.hidden = false;
  }

  async function view(jobId) {
    StudioState.jobId = jobId;
    StudioState.logCursor = 0;
    el("log").textContent = "";
    renderQueue();
    try {
      applyJob(await api(`/api/builds/${jobId}?since=0`));
    } catch (error) {
      showError(describeError(error));
    }
  }

  // --------------------------------------------------------------- polling

  function startPolling() {
    stopPolling();
    StudioState.polling = setInterval(poll, 1000);
    poll();
  }

  function stopPolling() {
    if (StudioState.polling) clearInterval(StudioState.polling);
    StudioState.polling = null;
  }

  async function poll() {
    if (!StudioState.jobId) return;
    try {
      if (StudioState.batchJobs.length) {
        const payload = await api("/api/builds");
        const current = new Map((payload.builds || []).map((job) => [job.id, job]));
        StudioState.batchJobs = StudioState.batchJobs.map((job) => current.get(job.id) || job);
        renderQueue();
        const active = StudioState.batchJobs.find((job) => ACTIVE.includes(job.status));
        if (active && active.id !== StudioState.jobId) {
          StudioState.jobId = active.id;
          StudioState.logCursor = 0;
          el("log").textContent = "";
        }
      }
      const job = await api(`/api/builds/${StudioState.jobId}?since=${StudioState.logCursor}`);
      applyJob(job);
      if (StudioState.batchJobs.length) {
        const index = StudioState.batchJobs.findIndex((item) => item.id === job.id);
        if (index >= 0) {
          StudioState.batchJobs[index] = Object.assign({}, StudioState.batchJobs[index], job, { log: [] });
        }
        renderQueue();
      }
      const queueRunning = StudioState.batchJobs.some((item) => ACTIVE.includes(item.status));
      if (!queueRunning && job.status !== "running" && job.status !== "cancelling") stopPolling();
    } catch (error) {
      stopPolling();
      showError(describeError(error));
    }
  }

  // ----------------------------------------------------------- job control

  async function startBuild() {
    StudioSetup.showError("");
    showError("");
    el("log").textContent = "";
    el("result-summary").hidden = true;
    el("result-summary").replaceChildren();
    StudioState.logCursor = 0;
    try {
      const result = await StudioPipelines.start();
      const job = result.jobs ? result.jobs[0] : result;
      StudioState.batchId = result.batchId || null;
      StudioState.batchJobs = result.jobs || [];
      StudioState.jobId = job.id;
      renderQueue();
      applyJob(job);
      startPolling();
    } catch (error) {
      StudioSetup.showError(describeError(error));
    }
    StudioPipelines.updateStartState();
  }

  async function cancel() {
    if (!StudioState.jobId) return;
    try {
      await post(`/api/builds/${StudioState.jobId}/cancel`, {});
    } catch (error) {
      showError(describeError(error));
    }
  }

  async function install() {
    if (!StudioState.jobId) return;
    el("install").disabled = true;
    showError("");
    try {
      const result = await post(`/api/builds/${StudioState.jobId}/install`, { name: "" });
      appendLog(`装入完成：${result.installedTo}`);
      el("install").hidden = true;
      // The library is its own entry point now; refresh it only when it is here.
      if (typeof StudioCourses !== "undefined") await StudioCourses.refresh();
    } catch (error) {
      showError(describeError(error));
      el("install").disabled = false;
    }
  }

  /** After a reload, re-attach to whatever the server is still working on. */
  async function restoreLatest() {
    try {
      const payload = await api("/api/builds");
      // Each entry point restores only the kinds it can render. Before the split
      // the build page would happily re-attach to a PDF job and then describe it
      // with an audio form — two panels telling the user different things.
      const mine = new Set(StudioPipelines.kinds());
      const jobs = (payload.builds || [])
        .filter((job) => mine.has(job.kind))
        .sort((a, b) => b.startedAt - a.startedAt);
      if (!jobs.length) return;
      const newest = jobs[0];
      if (newest.batchId) {
        StudioState.batchId = newest.batchId;
        StudioState.batchJobs = jobs
          .filter((job) => job.batchId === newest.batchId)
          .sort((a, b) => a.batchIndex - b.batchIndex);
      }
      const selected = StudioState.batchJobs.find((job) => ACTIVE.includes(job.status))
        || StudioState.batchJobs[StudioState.batchJobs.length - 1] || newest;
      const latest = await api(`/api/builds/${selected.id}?since=0`);
      StudioState.jobId = latest.id;
      StudioState.logCursor = 0;
      // Show the form that produced what panel 2 is about to display.
      if (StudioPipelines.byKind(latest.kind)) StudioPipelines.select(latest.kind);
      renderQueue();
      applyJob(latest);
      if (ACTIVE.includes(latest.status)
        || StudioState.batchJobs.some((job) => ACTIVE.includes(job.status))) startPolling();
    } catch (error) {
      showError(describeError(error));
    }
  }

  function wire() {
    el("start").addEventListener("click", startBuild);
    el("cancel").addEventListener("click", cancel);
    el("install").addEventListener("click", install);
  }

  return { isRunning, applyJob, appendLog, renderQueue, view, startPolling, stopPolling,
    startBuild, cancel, install, restoreLatest, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioJobs;
if (typeof window !== "undefined") window.StudioJobs = StudioJobs;
