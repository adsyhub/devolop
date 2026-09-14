"use strict";

/** 本地音频 → 听写课程. The original pipeline; everything else is a front end onto it. */
const PipelineAudio = (() => {
  const { el, post } = StudioCore;

  const uploads = () => StudioState.uploads.audio;

  return {
    id: "audio",
    tabId: "tab-audio",
    fieldsId: "audio-field",
    titlePlaceholder: "留空则使用音频文件名",
    /** Shows 语言 / 转写 / 讲解 and the advanced block. */
    usesCommonFields: true,
    usesEnrichment: true,
    /** Ends in a verified ZIP, so the course library is one button away. */
    installable: true,
    destination: "课程库",

    count: () => uploads().length,
    hasSource: () => uploads().length > 0,
    modelReady: () => !el("enrich").checked || Boolean(el("text-profile").value),
    startLabel: (count) => (count > 1 ? `开始制作 ${count} 个课程` : "开始制作"),

    start() {
      const files = uploads();
      const options = StudioSetup.commonBuildOptions();
      options.noNormalize = el("no-normalize").checked;
      if (files.length === 1) {
        return post("/api/builds", Object.assign(options, {
          uploadId: files[0].uploadId,
          title: el("title").value.trim(),
        }));
      }
      return post("/api/batch-builds", Object.assign(options, {
        source: "audio",
        items: files.map((upload) => ({ uploadId: upload.uploadId, title: "" })),
      }));
    },
  };
})();

if (typeof module !== "undefined" && module.exports) module.exports = PipelineAudio;
if (typeof window !== "undefined") window.PipelineAudio = PipelineAudio;
