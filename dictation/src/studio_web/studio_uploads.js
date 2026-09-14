"use strict";

/**
 * Drag-and-drop intake for the two pipelines that take local files.
 *
 * Local inputs arrive as uploads, never as paths: there is no endpoint that reads
 * or lists an arbitrary path, so there is no traversal surface and nothing that
 * can be used to probe the filesystem.
 */
const StudioUploads = (() => {
  const { el, api, describeError } = StudioCore;

  /** The two intakes differ only in which elements they write to. */
  const ZONES = {
    audio: { dropzone: "dropzone", dropText: "dropzone-text", input: "audio-input", state: "upload-state" },
    pdf: { dropzone: "pdf-dropzone", dropText: "pdf-dropzone-text", input: "pdf-input", state: "pdf-upload-state" },
  };

  async function receive(files, source) {
    const selected = Array.from(files || []);
    if (!selected.length) return;
    const zone = ZONES[source];
    StudioSetup.showError("");
    const stateElement = el(zone.state);
    stateElement.hidden = false;
    StudioState.uploads[source] = [];
    if (el("start")) el("start").disabled = true;

    const errors = [];
    for (let index = 0; index < selected.length; index += 1) {
      const file = selected[index];
      stateElement.textContent = `正在上传 ${index + 1}/${selected.length}：${file.name}…`;
      try {
        const result = await api("/api/uploads", {
          method: "POST",
          headers: { "X-Dictation-Filename": encodeURIComponent(file.name).replace(/%20/g, " ") },
          body: file,
        });
        if (result.kind !== source) {
          throw new Error(`文件类型不符合当前的${source === "pdf" ? " PDF" : "音频"}入口。`);
        }
        StudioState.uploads[source].push(result);
      } catch (error) {
        errors.push(`${file.name}：${describeError(error)}`);
      }
    }

    const uploaded = StudioState.uploads[source];
    stateElement.textContent = uploaded.length
      ? `已上传 ${uploaded.length} 个：${uploaded.map((item) => item.originalName).join("、")}`
      : "没有文件上传成功。";
    el(zone.dropText).textContent = uploaded.length > 1 ? "重新选择一批文件" : "换一个文件";
    if (el("title")) {
      if (uploaded.length === 1 && !el("title").value.trim()) {
        el("title").value = uploaded[0].originalName.replace(/\.[^.]+$/, "");
      }
      if (uploaded.length > 1) el("title").value = "";
    }
    if (errors.length) StudioSetup.showError(errors.join("\n"));
    StudioPipelines.updateStartState();
  }

  function wireZone(source) {
    const zone = ZONES[source];
    const dropzone = el(zone.dropzone);
    // 制课 has the audio zone, 教材入库 has the PDF one; neither page has both.
    if (!dropzone) return;
    dropzone.addEventListener("dragover", (event) => {
      event.preventDefault();
      dropzone.classList.add("dragging");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragging"));
    dropzone.addEventListener("drop", (event) => {
      event.preventDefault();
      dropzone.classList.remove("dragging");
      receive(event.dataTransfer.files, source);
    });
    el(zone.input).addEventListener("change", (event) => receive(event.target.files, source));
  }

  function wire() {
    for (const source of Object.keys(ZONES)) wireZone(source);
  }

  return { receive, wire };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioUploads;
if (typeof window !== "undefined") window.StudioUploads = StudioUploads;
