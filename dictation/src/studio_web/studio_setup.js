"use strict";

/**
 * Panel 1 · 准备 — choosing what the build will run on.
 *
 * The page can only ever name a profile the server already read from the trusted
 * config file. Everything here is therefore rendering and explaining what the
 * server offered; nothing constructs a provider, a model id or a command.
 */
const StudioSetup = (() => {
  const { el, setText, fillSelect, showMessage } = StudioCore;

  const SOURCE_LABELS = {
    local: "本地", cli: "CLI", cloud: "云端", manual: "手工", file: "文件", builtin: "内置",
  };
  const NO_MODEL = "当前没有可用模型";

  /**
   * Draw whatever of this panel the current page actually has.
   *
   * Each entry point carries a different slice: 制课 has 语言 / 转写 / 讲解, 教材入库
   * has only the OCR pipeline. Filling a select that is not on the page is a
   * no-op rather than a branch, so no page needs a flag saying which one it is.
   */
  function render() {
    const config = StudioState.config;
    const available = config.textProfiles.filter((item) => item.available).length
      + config.asrProfiles.filter((item) => item.available).length
      + (config.visionPipelines || []).filter((item) => item.available).length;
    const configured = config.textProfiles.length + config.asrProfiles.length
      + (config.visionPipelines || []).length;
    setText("config-line", config.configPath
      ? `配置：${config.configPath} · 可用 ${available}/${configured} · 课程库：${config.coursesDir}`
      : "没有找到 config/providers.json —— 请先复制 config/providers.example.json");

    fillSelect(el("language"), [{ value: "auto", label: "自动检测" }].concat(
      config.languages.map((code) => ({ value: code, label: code }))
    ), "auto");

    fillProfiles(el("asr-profile"), config.asrProfiles, config.defaultAsrProfile, true);
    fillProfiles(el("text-profile"), config.textProfiles, config.defaultTextProfile, false);
    fillVisionPipelines(el("vision-pipeline"), config.visionPipelines || [], config.defaultVisionPipeline);

    // Only complain about the models this page can actually select.
    const needsTranscription = Boolean(el("asr-profile"));
    const needsVision = Boolean(el("vision-pipeline"));
    const ready = (!needsTranscription || (config.textProfiles.some((item) => item.available)
        && config.asrProfiles.some((item) => item.available)))
      && (!needsVision || (config.visionPipelines || []).some((item) => item.available));
    showError(ready ? "" : (needsVision && !needsTranscription
      ? "当前没有可用的视觉 OCR 管线。请到「运维」启动本地模型，或在 config/providers.json 中配置。"
      : "当前缺少可用的讲解模型或转写模型。请启动本地服务、安装配置中的 CLI，"
        + "或设置订阅 API 的环境变量，然后点击“刷新模型状态”。"));

    updateHints();
    // 运维 shows this panel's model availability without carrying a build form.
    if (typeof StudioPipelines !== "undefined") StudioPipelines.updateStartState();
  }

  /** Re-read the provider config and redraw, without touching the services. */
  async function reload() {
    const button = el("refresh-models");
    if (button) { button.disabled = true; button.textContent = "检测中…"; }
    try {
      StudioState.config = await StudioCore.api("/api/config");
      render();
    } catch (error) {
      showError(StudioCore.describeError(error));
    } finally {
      if (button) { button.disabled = false; button.textContent = "刷新模型状态"; }
    }
  }

  function fillVisionPipelines(select, pipelines, preferred) {
    fillSelect(select, pipelines.map((pipeline) => {
      const locality = pipeline.members.every((member) => member.local) ? "本地" : "云端";
      return {
        value: pipeline.name,
        label: `${pipeline.name} · ${locality} · ${pipeline.available ? "可用" : "不可用"} · ${pipeline.members.length} 模型`,
        disabled: !pipeline.available,
      };
    }), preferred || (pipelines[0] && pipelines[0].name) || "", { placeholder: NO_MODEL });
  }

  function fillProfiles(select, profiles, preferred, allowAuto) {
    const available = profiles.filter((profile) => profile.available);
    const options = allowAuto && available.length
      ? [{ value: "", label: "按语言自动选择 · 可用" }]
      : [];
    for (const profile of profiles) {
      const source = SOURCE_LABELS[profile.source] || profile.source || "未知";
      const bits = [profile.name, `${source}·${profile.available ? "可用" : "不可用"}`];
      if (profile.model) bits.push(profile.model);
      options.push({ value: profile.name, label: bits.join(" · "), disabled: !profile.available });
    }
    const selected = allowAuto && available.length ? "" : (preferred || (available[0] && available[0].name) || "");
    fillSelect(select, options, selected, { placeholder: NO_MODEL });
  }

  function findProfile(family, name) {
    const list = family === "asr" ? StudioState.config.asrProfiles : StudioState.config.textProfiles;
    return list.find((profile) => profile.name === name) || null;
  }

  function describe(profile) {
    if (!profile) return "";
    const parts = [];
    if (profile.kind) parts.push(`kind=${profile.kind}`);
    if (profile.model) parts.push(profile.model);
    if (profile.needsKeyEnv) {
      parts.push(`需要环境变量 ${profile.needsKeyEnv}${profile.keyPresent ? "（已设置）" : "（未设置！）"}`);
    }
    parts.push(profile.statusText || (profile.available ? "可用" : "不可用"));
    const head = parts.join(" · ");
    return profile.description ? `${head}\n${profile.description}` : head;
  }

  function updateHints() {
    if (!StudioState.config) return;

    if (el("language")) {
      const language = el("language").value;
      const routed = StudioState.config.languageRouting[language];
      setText("routing-hint", routed
        ? `语言 ${language} 会自动使用转写 profile「${routed}」。`
        : language === "auto"
          ? "自动检测时不做按语言路由，使用配置里的默认转写 profile。"
          : `语言 ${language} 没有配置专用转写 profile，使用默认的那个。`);
    }
    if (el("asr-profile")) {
      setText("asr-hint", describe(findProfile("asr", el("asr-profile").value))
        || "留空表示交给按语言路由决定。");
    }
    if (el("text-profile")) {
      setText("text-hint", describe(findProfile("text", el("text-profile").value)) || "");
      const pipeline = typeof StudioPipelines !== "undefined" ? StudioPipelines.current() : null;
      el("text-profile-field").hidden = (pipeline && !pipeline.usesEnrichment)
        || !el("enrich").checked;
    }
    if (el("vision-pipeline")) {
      const pipeline = (StudioState.config.visionPipelines || [])
        .find((item) => item.name === el("vision-pipeline").value);
      setText("vision-hint", pipeline
        ? `${pipeline.description}\n顺序：${pipeline.members.map((item) => item.name).join(" → ")}`
        : "请先在 config/providers.json 中配置 visionProfiles / visionPipelines。");
    }
  }

  const valueOf = (id, fallback = "") => (el(id) ? el(id).value : fallback);
  const checked = (id, fallback = false) => (el(id) ? el(id).checked : fallback);

  /** Options every transcribing build sends, whatever its front end. */
  function commonBuildOptions() {
    return {
      language: valueOf("language", "auto"),
      asrProfile: valueOf("asr-profile"),
      textProfile: valueOf("text-profile"),
      enrich: checked("enrich"),
      strictQuality: checked("strict-quality"),
      keepGoing: checked("keep-going"),
    };
  }

  const showError = (message) => showMessage("setup-error", message);

  function wire() {
    const rerender = () => {
      updateHints();
      if (typeof StudioPipelines !== "undefined") StudioPipelines.updateStartState();
    };
    if (el("language")) el("language").addEventListener("change", updateHints);
    if (el("asr-profile")) el("asr-profile").addEventListener("change", updateHints);
    if (el("text-profile")) el("text-profile").addEventListener("change", rerender);
    if (el("enrich")) el("enrich").addEventListener("change", rerender);
    if (el("vision-pipeline")) el("vision-pipeline").addEventListener("change", rerender);
  }

  return { render, reload, updateHints, describe, findProfile, commonBuildOptions, valueOf, checked, showError, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioSetup;
if (typeof window !== "undefined") window.StudioSetup = StudioSetup;
