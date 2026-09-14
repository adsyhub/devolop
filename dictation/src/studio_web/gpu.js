"use strict";

/**
 * Server GPU status, rendered two ways from one payload.
 *
 * The build page shows a card per device; the editor shows a single pill in its
 * top bar. Both used to fetch and interpret `/api/gpu-status` on their own, so
 * the same nullable fields were unpacked twice with two sets of guards.
 */
const StudioGpu = (() => {
  const { api, el, text, describeError } = StudioCore;

  const status = () => api("/api/gpu-status");

  function hasDevices(payload) {
    return Boolean(payload && payload.available && (payload.gpus || []).length);
  }

  // ---------------------------------------------------------------- cards

  function memoryRow(card, payload, gpu) {
    if (!gpu.memory_total_mb) return;
    const totalGb = (gpu.memory_total_mb / 1024).toFixed(1);
    const row = text("div", "gpu-stat-row", "");
    if (!payload.nvml_ready || gpu.memory_used_mb === null || gpu.memory_used_mb === undefined) {
      row.append(text("span", "", "总显存容量:"));
      row.append(text("span", "gpu-stat-val", `~${totalGb} GB (${gpu.memory_total_mb} MiB)`));
      card.append(row);
      return;
    }
    const usedGb = (gpu.memory_used_mb / 1024).toFixed(1);
    const freeGb = (gpu.memory_free_mb
      ? gpu.memory_free_mb / 1024
      : (gpu.memory_total_mb - gpu.memory_used_mb) / 1024).toFixed(1);
    const percent = gpu.memory_percent !== undefined && gpu.memory_percent !== null
      ? gpu.memory_percent
      : Math.round((gpu.memory_used_mb / gpu.memory_total_mb) * 100);
    row.append(text("span", "", `显存: ${usedGb} GB / ${totalGb} GB (${percent}%)`));
    row.append(text("span", "gpu-stat-val", `剩余: ${freeGb} GB`));
    card.append(row);

    const barWrap = text("div", "gpu-bar-wrap", "");
    const fillClass = percent >= 90 ? "gpu-bar-fill danger" : percent >= 70 ? "gpu-bar-fill warn" : "gpu-bar-fill";
    const barFill = text("div", fillClass, "");
    barFill.style.width = `${Math.min(100, Math.max(2, percent))}%`;
    barWrap.append(barFill);
    card.append(barWrap);
  }

  function deviceCard(payload, gpu) {
    const card = text("div", "gpu-card", "");
    const header = text("div", "gpu-card-header", "");
    const title = text("span", "gpu-card-title",
      `GPU ${gpu.index !== undefined ? gpu.index : ""}: ${gpu.name || "NVIDIA GPU"}`);
    const badges = text("div", "gpu-card-badges", "");

    if (gpu.is_current) badges.append(text("span", "gpu-tag primary", "主卡 / 默认"));
    if (payload.nvml_ready) {
      if (gpu.utilization_gpu_percent !== null && gpu.utilization_gpu_percent !== undefined) {
        const used = gpu.utilization_gpu_percent;
        const badgeClass = used >= 85 ? "badge failed" : used >= 50 ? "badge needs_review" : "badge passed";
        badges.append(text("span", badgeClass, `利用率 ${used}%`));
      }
      if (gpu.temperature_gpu_c !== null && gpu.temperature_gpu_c !== undefined) {
        badges.append(text("span", "gpu-tag", `${gpu.temperature_gpu_c}°C`));
      }
    } else {
      badges.append(text("span", "badge passed", "驱动已就绪"));
    }
    header.append(title, badges);
    card.append(header);

    memoryRow(card, payload, gpu);

    if (payload.nvml_ready && gpu.power_draw_w !== null && gpu.power_draw_w !== undefined) {
      const row = text("div", "gpu-stat-row", "");
      const limit = gpu.power_limit_w ? ` / ${Math.round(gpu.power_limit_w)}W` : "";
      row.append(text("span", "", "实时功耗:"));
      row.append(text("span", "gpu-stat-val", `${Math.round(gpu.power_draw_w)}W${limit}`));
      card.append(row);
    } else if (gpu.bus_id) {
      const row = text("div", "gpu-stat-row", "");
      row.append(text("span", "", "PCIe 拓扑总线:"));
      row.append(text("span", "gpu-stat-val", gpu.bus_id + (gpu.bios ? ` · BIOS ${gpu.bios}` : "")));
      card.append(row);
    }

    if (gpu.uuid) card.append(text("div", "gpu-footer", `UUID: ${gpu.uuid}`));
    return card;
  }

  function renderCards(payload) {
    const cards = el("gpu-cards");
    if (!cards) return;
    if (!hasDevices(payload)) {
      el("gpu-summary").textContent = (payload && payload.status_text) || "未检测到可用 GPU 设备";
      cards.replaceChildren(text("p", "empty", (payload && payload.error)
        ? `未检测到显卡：${payload.error}`
        : "当前服务器未配置或未检测到可用显卡。"));
      if (el("gpu-meta")) el("gpu-meta").hidden = true;
      return;
    }

    el("gpu-summary").textContent = `${payload.status_text} · ${payload.summary || ""}`;
    cards.replaceChildren(...(payload.gpus || []).map((gpu) => deviceCard(payload, gpu)));

    const meta = el("gpu-meta");
    if (meta) {
      meta.hidden = false;
      meta.textContent = `NVIDIA 驱动内核版本: ${payload.driver_version || "未知"}` + (payload.nvml_ready
        ? " · 实时 NVML 遥测已连接，显存与利用率支持定时与手动刷新。"
        : " · 提示: 当前容器内 NVML 设备访问受限，已通过驱动与硬件拓扑识别显卡配置；"
          + "若在宿主机或开放设备映射环境运行，将自动切换为实时显存/利用率监控。");
    }
  }

  /**
   * Refresh the card panel.
   *
   * There used to be two buttons for this — one in the top bar and one in the
   * panel — calling the same function, on a panel that already polls itself. The
   * panel's own button is the one that stayed.
   */
  async function refreshCards() {
    const button = el("refresh-gpu-panel");
    if (button) { button.disabled = true; button.textContent = "检测中…"; }
    try {
      renderCards(await status());
      if (el("gpu-error")) el("gpu-error").hidden = true;
    } catch (error) {
      if (el("gpu-error")) {
        el("gpu-error").hidden = false;
        el("gpu-error").textContent = `获取显卡状态失败：${describeError(error)}`;
      }
    } finally {
      if (button) { button.disabled = false; button.textContent = "刷新显卡"; }
    }
  }

  // -------------------------------------------------------- compact summary

  /**
   * The same payload, reduced to one line and a tooltip.
   *
   * `status_pill.js` owns the indicator itself; what stays here is the reading of
   * these nullable fields, so the cards and the pill can never disagree about
   * whether a device counts as present.
   */
  function pillSummary(payload) {
    if (!hasDevices(payload)) {
      return {
        text: "GPU —",
        detail: [(payload && payload.status_text) || "未检测到显卡设备"],
      };
    }
    const count = payload.device_count || payload.gpus.length;
    const first = payload.gpus[0];
    const shortName = (first.name || "GPU").replace(/^NVIDIA\s+/i, "");
    const others = count > 1 ? ` (+${count - 1})` : "";
    const busy = payload.nvml_ready
      && first.utilization_gpu_percent !== null && first.utilization_gpu_percent !== undefined;
    return {
      text: busy
        ? `GPU ${first.utilization_gpu_percent}% · ${shortName}${others}`
        : `GPU ${shortName}${others}`,
      detail: [
        payload.status_text || "",
        `驱动: ${payload.driver_version || "未知"}`,
        ...payload.gpus.map((gpu) => {
          const memory = gpu.memory_total_mb ? ` (~${Math.round(gpu.memory_total_mb / 1024)}GB)` : "";
          const used = gpu.utilization_gpu_percent !== null && gpu.utilization_gpu_percent !== undefined
            ? ` [${gpu.utilization_gpu_percent}%]` : "";
          return `• GPU ${gpu.index !== undefined ? gpu.index : ""}: ${gpu.name}${memory}${used}`;
        }),
      ].filter(Boolean),
    };
  }

  /** Poll only while the tab is visible: a hidden workbench needs no telemetry. */
  function poll(refresh, intervalMs) {
    setInterval(() => { if (!document.hidden) refresh(); }, intervalMs);
  }

  return { status, renderCards, refreshCards, pillSummary, poll };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioGpu;
if (typeof window !== "undefined") window.StudioGpu = StudioGpu;
