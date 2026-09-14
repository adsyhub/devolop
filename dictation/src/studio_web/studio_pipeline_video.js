"use strict";

/**
 * 在线视频 → 听写课程，视频始终不下载。
 *
 * The page can name a profile and paste a URL. It cannot describe a provider, a
 * command or a path — the server rebuilds the URL from its own parser before that
 * value ever reaches an argv, and rejects anything it does not recognise.
 */
const PipelineVideo = (() => {
  const { el, post, text, describeError } = StudioCore;

  const CONTROL_NOTES = {
    "full": "可完全控制：逐句循环、盲听、变速都能用，精听体验完整。",
    "seek-reload": "只能重载定位：可以反复重播某一句，但没有自动循环。",
    "external": "无法在页面内驱动：只能在新标签页按时间点打开收听。"
      + "（我们没有实测该站点是否允许嵌入，这是保守默认值。）",
  };

  const TRANSCRIPT_NOTES = {
    verified: "同时取得站点字幕和本地 ASR，按质量门禁选源并保存对比证据；临时音频用完立即删除。",
    auto: "站点有字幕就直接用；没有就临时取音频做本地转写，音频用完立即删除。",
    subs: "只用站点字幕。没有字幕就停下，不会取任何音频。",
    asr: "跳过字幕，直接临时取音频本地转写。音频用完立即删除，视频始终不下载。",
  };

  function renderProbe(info) {
    const box = el("probe-result");
    box.replaceChildren();
    const rows = [
      ["站点", info.provider],
      ["控制档", `${info.control} — ${CONTROL_NOTES[info.control] || ""}`],
    ];
    if (info.title) rows.push(["标题", info.title]);
    if (info.uploader) rows.push(["上传者", info.uploader]);
    if (info.durationSec) rows.push(["时长", `${Math.round(info.durationSec / 60)} 分钟`]);
    const subtitles = info.subtitles || [];
    rows.push(["站点字幕", subtitles.length
      ? subtitles.map((item) => `${item.language}(${item.kind === "manual" ? "人工" : "自动"})`).join("、")
      : "没有找到 —— 会改用临时取音频本地转写"]);
    if (!info.ytdlpAvailable) rows.push(["yt-dlp", info.ytdlpHint || "未安装"]);
    if (info.error) rows.push(["读取失败", info.error]);

    for (const [label, value] of rows) {
      const row = document.createElement("div");
      row.className = "probe-row";
      row.append(text("span", "probe-label", label), text("span", "probe-value", String(value)));
      box.append(row);
    }
    box.hidden = false;
  }

  async function probe() {
    const url = el("video-url").value.trim();
    if (!url) return;
    StudioSetup.showError("");
    el("probe-button").disabled = true;
    el("probe-button").textContent = "探测中…";
    try {
      const info = await post("/api/video/probe", { url });
      StudioState.probe = info;
      renderProbe(info);
      if (!el("title").value.trim() && info.title) el("title").value = info.title;
    } catch (error) {
      StudioState.probe = null;
      el("probe-result").hidden = true;
      StudioSetup.showError(describeError(error));
    } finally {
      el("probe-button").disabled = false;
      el("probe-button").textContent = "探测";
      StudioPipelines.updateStartState();
    }
  }

  function updateTranscriptHint() {
    el("video-transcript-hint").textContent = TRANSCRIPT_NOTES[el("video-transcript").value] || "";
  }

  return {
    id: "video",
    tabId: "tab-video",
    fieldsId: "video-fields",
    titlePlaceholder: "留空则使用视频标题",
    usesCommonFields: true,
    usesEnrichment: true,
    // A video build writes straight into courses/, so there is nothing to install.
    installable: false,
    destination: "课程库",

    // A video build needs a URL, not an upload — probing first is encouraged but
    // not required, since the server validates the URL again anyway.
    count: () => 1,
    hasSource: () => Boolean(el("video-url") && el("video-url").value.trim()),
    modelReady: () => !el("enrich").checked || Boolean(el("text-profile").value),
    startLabel: () => "开始制作",

    start() {
      const transcript = el("video-transcript").value;
      return post("/api/video/builds", Object.assign(StudioSetup.commonBuildOptions(), {
        url: el("video-url").value.trim(),
        title: el("title").value.trim(),
        name: "",
        transcript,
        subLangs: el("video-sub-langs").value.trim(),
        // "只用站点字幕" is the learner saying: do not reach for the audio.
        allowAudioFetch: transcript !== "subs",
        clipStart: el("video-clip-start").value,
        clipEnd: el("video-clip-end").value,
      }));
    },

    probe,
    updateTranscriptHint,

    wire() {
      el("probe-button").addEventListener("click", probe);
      el("video-url").addEventListener("input", () => StudioPipelines.updateStartState());
      el("video-transcript").addEventListener("change", updateTranscriptHint);
      updateTranscriptHint();
    },
  };
})();

if (typeof module !== "undefined" && module.exports) module.exports = PipelineVideo;
if (typeof window !== "undefined") window.PipelineVideo = PipelineVideo;
