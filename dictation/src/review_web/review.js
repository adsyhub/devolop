"use strict";

const CHECK_FIELDS = [
  "transcriptMatchesAudio",
  "timingAligned",
  "translationAccurate",
  "explanationAccurate",
];
const STATUS_LABELS = {
  pending: "待审",
  approved: "已通过",
  changes_required: "待修正",
};
const LANGUAGE_PROFILES = {
  ja: {locale: "ja-JP", display: "日语"}, en: {locale: "en-US", display: "英语"},
  fr: {locale: "fr-FR", display: "法语"}, ko: {locale: "ko-KR", display: "韩语"},
  es: {locale: "es-ES", display: "西班牙语"}, de: {locale: "de-DE", display: "德语"},
  it: {locale: "it-IT", display: "意大利语"}, pt: {locale: "pt-BR", display: "葡萄牙语"},
  zh: {locale: "zh-CN", display: "中文"},
};

const elements = {};
let token = "";
let session = null;
let index = 0;
let baseline = "";
let segmentPlaying = false;

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  for (const id of [
    "app", "fatal-error", "fatal-message", "course-title", "review-meta", "approved-count",
    "pending-count", "issue-count", "previous-button", "next-pending-button", "next-button",
    "sentence-position", "sentence-meta", "status-badge", "audio", "play-button", "loop-toggle",
    "speed-select", "time-display", "source-label", "source-text", "translation-text", "explanation-text",
    "review-form", "notes", "save-pending-button", "changes-button", "approve-button", "message",
    "independent-attestation", "release-attestation", "finalize-button", "finalize-message",
    "transcript-check-label",
  ]) {
    const key = id.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    elements[key] = document.getElementById(id);
  }

  token = new URLSearchParams(location.search).get("token") || "";
  if (!token) return fatal("网址缺少本地审核权杖。请使用启动指令显示的完整网址。");
  bindEvents();
  try {
    session = await api("/api/session");
    const sentences = session?.course?.sentences;
    if (!Array.isArray(sentences) || !sentences.length) throw new Error("课程没有可审核句子。");
    elements.audio.src = `/audio?token=${encodeURIComponent(token)}`;
    elements.courseTitle.textContent = session.course.title || "未命名课程";
    const profile = courseLanguageProfile(session.course);
    elements.sourceLabel.textContent = `${profile.display}原文`;
    elements.transcriptCheckLabel.textContent = `${profile.display}转写稿与音频一致`;
    elements.sourceText.lang = profile.locale;
    const reviewer = session.review?.reviewer || {};
    elements.reviewMeta.textContent = `审核者：${reviewer.name || "未具名"}${reviewer.organization ? `／${reviewer.organization}` : ""} · 内容版本 ${session.course.contentRevision}`;
    elements.app.hidden = false;
    render();
  } catch (error) {
    fatal(error.message);
  }
}

function bindEvents() {
  elements.previousButton.addEventListener("click", () => navigate(index - 1));
  elements.nextButton.addEventListener("click", () => navigate(index + 1));
  elements.nextPendingButton.addEventListener("click", navigateToNextPending);
  elements.playButton.addEventListener("click", toggleSegment);
  elements.speedSelect.addEventListener("change", () => { elements.audio.playbackRate = Number(elements.speedSelect.value); });
  elements.audio.addEventListener("timeupdate", maintainSegment);
  elements.audio.addEventListener("pause", updatePlayLabel);
  elements.audio.addEventListener("play", updatePlayLabel);
  elements.reviewForm.addEventListener("input", updateDirtyState);
  elements.savePendingButton.addEventListener("click", () => save("pending", false));
  elements.changesButton.addEventListener("click", () => save("changes_required", false));
  elements.approveButton.addEventListener("click", () => save("approved", true));
  elements.finalizeButton.addEventListener("click", finalize);
  window.addEventListener("beforeunload", (event) => {
    if (!isDirty()) return;
    event.preventDefault();
    event.returnValue = "";
  });
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key === "Enter") {
      event.preventDefault();
      save("approved", true);
    }
  });
}

function render() {
  stopAudio();
  const sentence = currentSentence();
  const item = currentItem();
  elements.sentencePosition.textContent = `第 ${index + 1} 句，共 ${session.course.sentences.length} 句`;
  elements.sentenceMeta.textContent = `${formatTime(sentence.startTime)}–${formatTime(sentence.endTime)} · ${sentence.contentType || "未分类"} · ${sentence.practiceEligible === false ? "非练习片段" : "练习片段"} · ${sentence.id}`;
  elements.sourceText.textContent = sentence.sourceText || sentence.jaText || "";
  elements.translationText.textContent = sentence.translationText || sentence.zhTranslation || "（空白）";
  elements.explanationText.textContent = sentence.explanationText || "（空白）";
  elements.notes.value = item.notes || "";
  for (const field of CHECK_FIELDS) {
    document.querySelector(`[data-check="${field}"]`).checked = item.checks?.[field] === true;
  }
  elements.statusBadge.textContent = STATUS_LABELS[item.status] || item.status;
  elements.statusBadge.className = `status-badge status-${item.status}`;
  elements.previousButton.disabled = index === 0;
  elements.nextButton.disabled = index === session.course.sentences.length - 1;
  elements.timeDisplay.textContent = `${formatTime(sentence.startTime)} / ${formatTime(sentence.endTime)}`;
  updateCounts();
  setMessage("");
  baseline = formSnapshot();
  updateDirtyState();
}

function currentSentence() { return session.course.sentences[index]; }

function courseLanguageProfile(course) {
  const raw = course?.sourceLanguage || course?.language?.code || course?.locales?.source || "ja";
  const code = String(raw).toLowerCase().replace("_", "-").split("-", 1)[0];
  return LANGUAGE_PROFILES[code] || {locale: String(raw), display: "来源语言"};
}

function currentItem() {
  const id = currentSentence().id;
  const item = session.review.items.find((candidate) => candidate.sentenceId === id);
  if (!item) throw new Error(`审核档缺少句子 ${id}`);
  return item;
}

function readForm() {
  return {
    checks: Object.fromEntries(CHECK_FIELDS.map((field) => [field, document.querySelector(`[data-check="${field}"]`).checked])),
    notes: elements.notes.value.trim(),
  };
}

function formSnapshot() { return JSON.stringify(readForm()); }
function isDirty() { return Boolean(baseline) && formSnapshot() !== baseline; }

function updateDirtyState() {
  document.title = `${isDirty() ? "● " : ""}课程人工审听工作台`;
}

async function navigate(nextIndex) {
  if (nextIndex < 0 || nextIndex >= session.course.sentences.length) return;
  if (isDirty() && !confirm("目前修改尚未保存，仍要离开这一句吗？")) return;
  index = nextIndex;
  render();
}

function navigateToNextPending() {
  const total = session.course.sentences.length;
  for (let offset = 1; offset <= total; offset += 1) {
    const candidateIndex = (index + offset) % total;
    const id = session.course.sentences[candidateIndex].id;
    const item = session.review.items.find((candidate) => candidate.sentenceId === id);
    if (item?.status !== "approved") {
      navigate(candidateIndex);
      return;
    }
  }
  setMessage("所有句子都已通过。", false);
}

async function save(status, moveNext) {
  const form = readForm();
  if (status === "approved" && CHECK_FIELDS.some((field) => form.checks[field] !== true)) {
    setMessage("通过前必须明确勾选四项确认。", true);
    return;
  }
  if (status === "changes_required" && !form.notes) {
    setMessage("标记待修时必须写下具体问题。", true);
    elements.notes.focus();
    return;
  }
  setBusy(true);
  try {
    const sentenceId = currentSentence().id;
    const result = await api(`/api/items/${encodeURIComponent(sentenceId)}`, {
      method: "PUT",
      body: JSON.stringify({status, checks: form.checks, notes: form.notes}),
    });
    const itemIndex = session.review.items.findIndex((item) => item.sentenceId === sentenceId);
    session.review.items[itemIndex] = result.item;
    baseline = formSnapshot();
    updateCounts();
    const successMessage = status === "approved" ? "已记录通过。" : status === "changes_required" ? "已标记待修。" : "已保存为待审。";
    if (moveNext) {
      const target = findNextUnapproved();
      if (target === -1) {
        render();
        setMessage("已记录通过；所有句子都已通过。");
      } else {
        navigate(target);
      }
    } else {
      render();
      setMessage(successMessage);
    }
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    setBusy(false);
  }
}

function updateCounts() {
  const counts = {approved: 0, pending: 0, changes_required: 0};
  for (const item of session.review.items) if (item.status in counts) counts[item.status] += 1;
  session.counts = counts;
  elements.approvedCount.textContent = counts.approved;
  elements.pendingCount.textContent = counts.pending;
  elements.issueCount.textContent = counts.changes_required;
  elements.finalizeButton.disabled = counts.pending > 0 || counts.changes_required > 0;
}

function findNextUnapproved() {
  const total = session.course.sentences.length;
  for (let offset = 1; offset <= total; offset += 1) {
    const candidateIndex = (index + offset) % total;
    const id = session.course.sentences[candidateIndex].id;
    const item = session.review.items.find((candidate) => candidate.sentenceId === id);
    if (item?.status !== "approved") return candidateIndex;
  }
  return -1;
}

async function finalize() {
  if (!elements.independentAttestation.checked || !elements.releaseAttestation.checked) {
    setFinalizeMessage("请先勾选两项具名声明。", true);
    return;
  }
  if (isDirty()) {
    setFinalizeMessage("目前句子有未保存的修改。", true);
    return;
  }
  setBusy(true);
  try {
    const result = await api("/api/finalize", {
      method: "POST",
      body: JSON.stringify({independentHumanReview: true, commercialReleaseRecommendation: true}),
    });
    session.review.status = "approved";
    setFinalizeMessage(`定稿完成：${result.report.summary.approved} 句全部通过。`);
  } catch (error) {
    setFinalizeMessage(error.message, true);
  } finally {
    setBusy(false);
  }
}

function toggleSegment() {
  const audio = elements.audio;
  const sentence = currentSentence();
  if (!audio.paused && segmentPlaying) {
    stopAudio();
    return;
  }
  audio.currentTime = Number(sentence.startTime) || 0;
  audio.playbackRate = Number(elements.speedSelect.value);
  segmentPlaying = true;
  audio.play().catch((error) => setMessage(`无法播放音频：${error.message}`, true));
}

function maintainSegment() {
  if (!segmentPlaying) return;
  const sentence = currentSentence();
  if (elements.audio.currentTime >= Number(sentence.endTime) - .02) {
    if (elements.loopToggle.checked) {
      elements.audio.currentTime = Number(sentence.startTime) || 0;
      elements.audio.play().catch(() => {});
    } else stopAudio();
  }
  elements.timeDisplay.textContent = `${formatTime(elements.audio.currentTime)} / ${formatTime(sentence.endTime)}`;
}

function stopAudio() {
  segmentPlaying = false;
  elements.audio.pause();
  updatePlayLabel();
}

function updatePlayLabel() {
  elements.playButton.textContent = elements.audio.paused ? "▶ 播放本句" : "❚❚ 暂停";
}

function setBusy(busy) {
  for (const button of [elements.savePendingButton, elements.changesButton, elements.approveButton]) button.disabled = busy;
  if (busy) elements.finalizeButton.disabled = true;
  else updateCounts();
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-Review-Token", token);
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch(path, {...options, headers, cache: "no-store"});
  let payload = {};
  try { payload = await response.json(); } catch (_) { /* response may be empty */ }
  if (!response.ok) throw new Error(payload.error || `请求失败（HTTP ${response.status}）`);
  return payload;
}

function formatTime(value) {
  const seconds = Math.max(0, Number(value) || 0);
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${(seconds % 60).toFixed(1).padStart(4, "0")}`;
}

function setMessage(text, error = false) {
  elements.message.textContent = text;
  elements.message.classList.toggle("error", error);
}

function setFinalizeMessage(text, error = false) {
  elements.finalizeMessage.textContent = text;
  elements.finalizeMessage.classList.toggle("error", error);
}

function fatal(message) {
  elements.app.hidden = true;
  elements.fatalError.hidden = false;
  elements.fatalMessage.textContent = message;
}
