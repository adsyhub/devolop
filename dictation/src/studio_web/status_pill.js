"use strict";

/**
 * The one-line answer to "can this machine build right now?"
 *
 * 运维 has the full panels; every page where a person actually works gets this
 * instead: the GPU's load and how many local model services are up, in the top
 * bar, with the details in the tooltip. It exists because the alternative shipped
 * once already — two full-width telemetry panels above the form, which pushed
 * step 1 below the fold on the page whose entire purpose is step 1.
 *
 * Clicking re-checks immediately. Acting on what it says is one nav click away.
 */
const StudioStatusPill = (() => {
  const { el, api, describeError } = StudioCore;

  // Slower than the GPU panel's own poll: each check probes four local services,
  // and a build page needs a heartbeat, not a monitor.
  const POLL_MS = 30000;

  async function read() {
    const [gpu, models] = await Promise.all([
      StudioGpu.status().catch((error) => ({ error: describeError(error) })),
      api("/api/local-models").catch((error) => ({ error: describeError(error) })),
    ]);
    return { gpu, models };
  }

  function compose({ gpu, models }) {
    const summary = StudioGpu.pillSummary(gpu);
    const parts = [summary.text];
    const detail = summary.detail.slice();

    let short = false;
    if (models && !models.error && typeof models.total === "number") {
      parts.push(`模型 ${models.ready}/${models.total}`);
      short = models.ready < models.total;
      detail.push("", `本地模型 ${models.ready}/${models.total} 在线`);
      for (const service of models.services || []) {
        detail.push(`• ${service.label}：${service.available ? "在线" : (service.statusText || "未启动")}`);
      }
      if (short) detail.push("", "到「运维」可以启动缺席的服务。");
    } else if (models && models.error) {
      parts.push("模型 ?");
      detail.push("", `本地模型状态读取失败：${models.error}`);
    }

    detail.push("", "（点击可立即重新检测）");
    return { text: parts.join(" · "), title: detail.join("\n"), warn: short };
  }

  async function refresh() {
    const pill = el("status-pill");
    if (!pill) return;
    try {
      const { text, title, warn } = compose(await read());
      pill.textContent = text;
      pill.title = title;
      pill.classList.toggle("warn", warn);
    } catch (error) {
      pill.textContent = "状态未知";
      pill.title = describeError(error);
    }
  }

  /** Attach to the page's pill, if it has one. */
  function mount() {
    const pill = el("status-pill");
    if (!pill) return;
    pill.addEventListener("click", () => {
      pill.textContent = "检测中…";
      refresh();
    });
    refresh();
    StudioGpu.poll(refresh, POLL_MS);
  }

  return { read, compose, refresh, mount };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioStatusPill;
if (typeof window !== "undefined") window.StudioStatusPill = StudioStatusPill;
