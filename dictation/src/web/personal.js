"use strict";

/* Standalone personal learning centre.
 *
 * This page owns presentation and navigation for mistakes, vocabulary, notes and
 * analytics. It deliberately does not import app.js or fetch manifest.json: opening
 * personal records must never initialise the audio player or an active course.
 */

const TOKEN_HEADER = "X-Dictation-Token";
const CACHE_KEY = "dictation-personal-page:v1";
const TABS = ["mistakes", "vocab", "notes", "analytics"];
const LEXICON_TYPES = {
  recall: "回忆释义", meaning: "看词识义", reading: "看词写读音", production: "看释义回忆词语",
  listening: "听音识词", cloze: "例句填空", connection: "接续练习", usage: "近义辨析",
  collocation: "搭配辨析", order: "句子排序", context: "语境选择", writing: "造句 / 改写"
};
const LEXICON_KINDS = { word: "单词", grammar: "语法" };

const state = {
  token: "",
  online: false,
  activeTab: "mistakes",
  mistakeScope: "dictation",
  courses: new Map(),
  dictationMistakes: [],
  examMistakes: [],
  vocab: [],
  notes: [],
  analytics: null,
  logs: [],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function readCache() {
  try {
    const value = JSON.parse(localStorage.getItem(CACHE_KEY) || "{}");
    return value && typeof value === "object" ? value : {};
  } catch {
    return {};
  }
}

function writeCache() {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      courses: [...state.courses.entries()],
      dictationMistakes: state.dictationMistakes,
      examMistakes: state.examMistakes,
      // Review-card bodies live in IndexedDB. The personal hub only needs
      // lightweight metadata and must not duplicate textbook snapshots here.
      vocab: state.vocab.map(({ cardPayload: _cardPayload, ...item }) => item),
      notes: state.notes,
      analytics: state.analytics,
      logs: state.logs,
      savedAt: new Date().toISOString(),
    }));
  } catch { /* private mode/quota errors should not break the page */ }
}

function restoreCache() {
  const cached = readCache();
  state.courses = new Map(Array.isArray(cached.courses) ? cached.courses : []);
  state.dictationMistakes = Array.isArray(cached.dictationMistakes) ? cached.dictationMistakes : [];
  state.examMistakes = Array.isArray(cached.examMistakes) ? cached.examMistakes : [];
  state.vocab = Array.isArray(cached.vocab) ? cached.vocab : [];
  state.notes = Array.isArray(cached.notes) ? cached.notes : [];
  state.analytics = cached.analytics || null;
  state.logs = Array.isArray(cached.logs) ? cached.logs : [];
}

async function acquireToken() {
  const response = await fetch("./api/session/bootstrap", { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`本地服务连接失败（HTTP ${response.status}）`);
  const data = await response.json();
  state.token = String(data.token || "");
  if (!state.token) throw new Error("本地服务没有返回会话令牌");
}

async function api(path, options = {}) {
  const headers = { Accept: "application/json", ...(options.headers || {}) };
  if (state.token) headers[TOKEN_HEADER] = state.token;
  const response = await fetch(path, { cache: "no-store", ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data?.ok === false) {
    throw new Error(data?.error || `请求失败（HTTP ${response.status}）`);
  }
  return data;
}

async function sendSyncOperation(operation) {
  return api(operation.path, {
    method: operation.method,
    headers: {
      ...(operation.body !== null && operation.body !== undefined ? { "Content-Type": "application/json" } : {}),
      "X-Learning-Operation-Id": operation.id,
    },
    body: operation.body !== null && operation.body !== undefined ? JSON.stringify(operation.body) : undefined,
  });
}

function setConnection() {
  const node = $("#connection-status");
  if (!node) return;
  const pending = LearningDataSync.pendingCount();
  node.className = `me-connection ${state.online ? "online" : "offline"}`;
  node.textContent = state.online
    ? (pending ? `已连接 · ${pending} 项等待同步` : "本地资料库已连接")
    : (pending ? `离线 · ${pending} 项等待同步` : "离线浏览本地缓存");
}

function setStatus(message = "", isError = false) {
  const box = $("#page-status");
  const text = $("#page-status-text");
  if (!box || !text) return;
  box.hidden = !message;
  box.classList.toggle("is-error", isError);
  text.textContent = message;
  $("#retry-button").hidden = !isError;
}

function toast(message) {
  const node = $("#me-toast");
  if (!node) return;
  node.textContent = message;
  node.hidden = false;
  window.setTimeout(() => { node.hidden = true; }, 2600);
}

function courseTitle(courseId) {
  return state.courses.get(courseId) || courseId || "未标明课程";
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("zh-CN", { dateStyle: "medium", timeStyle: "short" });
}

function text(tag, value, className = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = value == null ? "" : String(value);
  return node;
}

function empty(message) {
  return text("div", message, "me-empty");
}

function action(label, handler, className = "") {
  const button = text("button", label, className);
  button.type = "button";
  button.addEventListener("click", handler);
  return button;
}

async function loadAll() {
  setStatus("正在加载学习资料…");
  const requests = await Promise.allSettled([
    api("./api/courses"),
    api("./api/mistakes"),
    api("./api/exams/review-summary"),
    api("./api/vocab"),
    api("./api/notes?allCourses=true"),
    api("./api/analytics?scope=all"),
    api("./api/study-logs?limit=50"),
  ]);

  const [courses, mistakes, exams, vocab, notes, analytics, logs] = requests;
  if (courses.status === "fulfilled") {
    state.courses = new Map((courses.value.courses || []).map((item) => [item.courseId || item.id, item.title || item.id]));
  }
  if (mistakes.status === "fulfilled") state.dictationMistakes = mistakes.value.items || [];
  if (exams.status === "fulfilled") {
    state.examMistakes = (exams.value.exams || []).flatMap((exam) => (exam.questions || []).map((question) => ({
      ...question,
      examSlug: exam.examSlug,
      examTitle: exam.examTitle || exam.examSlug,
      examLevel: exam.examLevel || "",
    })));
  }
  if (vocab.status === "fulfilled") {
    // Through the shared adapter, so a card deleted or paused in the lexicon workspace
    // is already gone here and a stale server snapshot cannot revive it (LEX-12, §8.4).
    const merged = await LearningCards.merge(vocab.value.items || []);
    state.vocab = PersonalDataTools.dedupeVocabEntries(merged);
  } else {
    const cached = await LearningCards.localCards();
    if (cached.length) state.vocab = PersonalDataTools.dedupeVocabEntries(cached);
  }
  if (notes.status === "fulfilled") state.notes = notes.value.items || [];
  if (analytics.status === "fulfilled") state.analytics = analytics.value.analytics || null;
  if (logs.status === "fulfilled") state.logs = logs.value.items || [];

  writeCache();
  renderAll();
  const failures = requests.filter((item) => item.status === "rejected").length;
  setStatus(failures ? `${failures} 类在线数据读取失败，当前显示已缓存内容。` : "", failures > 0);
}

function updateSummary() {
  const mistakes = state.dictationMistakes.length + state.examMistakes.length;
  const summary = state.analytics?.summary || {};
  $("#summary-mistakes").textContent = String(mistakes);
  $("#summary-vocab").textContent = String(state.vocab.length);
  $("#summary-notes").textContent = String(state.notes.length);
  $("#summary-streak").textContent = String(summary.currentStreak || 0);
  setBadge("#badge-mistakes", mistakes);
  setBadge("#badge-vocab", state.vocab.length);
  setBadge("#badge-notes", state.notes.length);
}

function setBadge(selector, count) {
  const node = $(selector);
  node.textContent = String(count);
  node.hidden = count < 1;
}

function route() {
  const match = /^#\/(mistakes|vocab|notes|analytics)(?:\/(dictation|exam|lexicon))?$/.exec(location.hash || "");
  return { tab: match?.[1] || "mistakes", scope: match?.[2] || "" };
}

function activateRoute() {
  const wanted = route();
  state.activeTab = wanted.tab;
  if (wanted.scope) state.mistakeScope = wanted.scope;
  $$("[data-tab]").forEach((button) => {
    const active = button.dataset.tab === state.activeTab;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });
  $$("[data-panel]").forEach((panel) => { panel.hidden = panel.dataset.panel !== state.activeTab; });
  renderActive();
}

function renderAll() {
  updateSummary();
  renderMistakes();
  renderVocab();
  renderNotes();
  renderAnalytics();
}

function renderActive() {
  if (state.activeTab === "mistakes") renderMistakes();
  else if (state.activeTab === "vocab") renderVocab();
  else if (state.activeTab === "notes") renderNotes();
  else renderAnalytics();
}

function renderMistakes() {
  $$("[data-mistake-scope]").forEach((button) => button.classList.toggle("is-active", button.dataset.mistakeScope === state.mistakeScope));
  $("#dictation-mistake-count").textContent = String(state.dictationMistakes.length);
  $("#exam-mistake-count").textContent = String(state.examMistakes.length);
  const list = $("#mistakes-list");
  list.replaceChildren();

  if (state.mistakeScope === "lexicon") {
    $("#mistakes-summary").textContent = "正在读取词汇与语法错题…";
    api("./api/lexicon/mistakes").then(data => {
      if (state.mistakeScope !== "lexicon") return;
      list.replaceChildren();
      const items = (data.items || []).filter(item => !item.resolved);
      $("#mistakes-summary").textContent = items.length
        ? `${items.length} 个词汇 / 语法方向待巩固`
        : "没有待处理的词汇语法错题。";
      if (!items.length) return list.appendChild(empty("词汇与语法错题已经清空。"));
      items.forEach((item) => list.appendChild(lexiconMistakeRow(item)));
    }).catch(error => { $("#mistakes-summary").textContent = `词汇语法错题读取失败：${error.message}`; });
    return;
  }
  if (state.mistakeScope === "dictation") {
    $("#mistakes-summary").textContent = state.dictationMistakes.length
      ? `${state.dictationMistakes.length} 个精听弱项句子待巩固。`
      : "没有待处理的精听错句。";
    if (!state.dictationMistakes.length) return list.appendChild(empty("精听错句已经清空。"));
    state.dictationMistakes.forEach((item) => list.appendChild(dictationMistakeRow(item)));
  } else {
    const due = state.examMistakes.filter((item) => item.due).length;
    $("#mistakes-summary").textContent = state.examMistakes.length
      ? `${state.examMistakes.length} 道真题错题${due ? `，其中 ${due} 道今天到期` : ""}。`
      : "没有待处理的真题错题。";
    if (!state.examMistakes.length) return list.appendChild(empty("真题错题已经清空。"));
    const grouped = new Map();
    state.examMistakes.forEach((item) => {
      if (!grouped.has(item.examSlug)) grouped.set(item.examSlug, []);
      grouped.get(item.examSlug).push(item);
    });
    grouped.forEach((items) => list.appendChild(examMistakeRow(items)));
  }
}

function lexiconMistakeRow(item) {
  const row = document.createElement("article");
  row.className = "me-row";
  const head = document.createElement("div"); head.className = "me-row-head";
  head.append(
    text("h3", item.headword || "待巩固条目", "me-row-title"),
    text("span", `${LEXICON_KINDS[item.kind] || item.kind || ""} · ${LEXICON_TYPES[item.type] || item.type || ""}`, "me-row-meta")
  );
  row.append(
    head,
    text("p", `首次不可靠回忆 ${item.wrongCount || 0} 次 · 连续答对 ${item.cleanStreak || 0} 次`, "me-row-copy")
  );
  const actions = document.createElement("div"); actions.className = "me-row-actions";
  const practiceLink = text("a", "复练此项");
  practiceLink.href = `./lexicon#/practice/new?refs=${encodeURIComponent(item.sourceRef)}&types=${encodeURIComponent(item.type)}`;
  const recordLink = text("a", "查看记录与解析");
  recordLink.href = `./lexicon#/records?focus=${encodeURIComponent(item.sourceRef)}`;
  actions.append(practiceLink, recordLink);
  row.append(actions);
  return row;
}

function dictationMistakeRow(item) {
  const row = document.createElement("article");
  row.className = "me-row";
  const head = document.createElement("div"); head.className = "me-row-head";
  head.append(text("h3", item.sourceText || item.sentenceId || "精听错句", "me-row-title"), text("span", courseTitle(item.courseId), "me-row-meta"));
  row.append(head);
  row.append(text("p", `尝试 ${item.attempts || 0} 次 · 最佳分数 ${Math.round(item.lastScore || 0)}${item.lastUserInput ? ` · 上次输入：${item.lastUserInput}` : ""}`, "me-row-copy"));
  const actions = document.createElement("div"); actions.className = "me-row-actions";
  actions.append(action("进入对应精听句", () => openDictationMistake(item)));
  row.append(actions);
  return row;
}

async function openDictationMistake(item) {
  try {
    if (item.courseId) await api("./api/courses/switch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ courseId: item.courseId }) });
    sessionStorage.setItem("dictation-personal-jump:v1", JSON.stringify({ courseId: item.courseId || "", sentenceId: item.sentenceId || "" }));
    location.assign("./listening#/practice");
  } catch (error) {
    toast(`无法打开课程：${error.message}`);
  }
}

function examMistakeRow(items) {
  const first = items[0];
  const row = document.createElement("article"); row.className = "me-row";
  const head = document.createElement("div"); head.className = "me-row-head";
  head.append(text("h3", first.examTitle, "me-row-title"), text("span", `${first.examLevel ? `JLPT ${first.examLevel} · ` : ""}${items.length} 道`, "me-row-meta"));
  row.append(head, text("p", `累计错答 ${items.reduce((sum, item) => sum + Number(item.wrong || 0), 0)} 次 · ${items.filter((item) => item.due).length} 道今天到期`, "me-row-copy"));
  const actions = document.createElement("div"); actions.className = "me-row-actions";
  const link = text("a", "去真题错题复习");
  link.href = `./exams#/exam/${encodeURIComponent(first.examSlug)}?mode=review&scope=wrong`;
  actions.append(link); row.append(actions);
  return row;
}

function filteredVocab() {
  const query = $("#vocab-search").value.trim().toLocaleLowerCase();
  const status = $("#vocab-status").value;
  const now = Date.now();
  return state.vocab.filter((item) => {
    const haystack = [item.term, item.reading, item.meaning, item.note, ...(item.tags || [])].join(" ").toLocaleLowerCase();
    const mature = Number(item.srsStage || 0) >= 3;
    const due = !item.reviewSuspended && (!item.nextReviewAt || new Date(item.nextReviewAt).getTime() <= now);
    const matchesStatus = !status || (status === "due" ? due : status === "mastered" ? mature : item.reviewSuspended);
    return (!query || haystack.includes(query)) && matchesStatus;
  }).sort((a, b) => String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")));
}

function renderVocab() {
  const list = $("#vocab-list"); list.replaceChildren();
  const items = filteredVocab();
  if (!items.length) return list.appendChild(empty(state.vocab.length ? "没有符合筛选条件的生词。" : "生词本还是空的。"));
  items.forEach((item) => list.appendChild(vocabRow(item)));
}

function vocabRow(item) {
  const row = document.createElement("article"); row.className = "me-row";
  const head = document.createElement("div"); head.className = "me-row-head";
  const mature = Number(item.srsStage || 0) >= 3;
  const schedule = item.reviewSuspended ? "已暂停复习" : (item.nextReviewAt ? `下次 ${formatDate(item.nextReviewAt)}` : "待复习");
  head.append(text("h3", `${item.term}${item.reading ? `【${item.reading}】` : ""}`, "me-row-title"), text("span", `${mature ? "成熟 · " : ""}${schedule}`, "me-row-meta"));
  row.append(head);
  if (item.meaning || item.note) row.append(text("p", [item.meaning, item.note].filter(Boolean).join("\n"), "me-row-copy"));
  if ((item.tags || []).length || item.level) {
    const tags = document.createElement("div"); tags.className = "me-tags";
    [...new Set([item.level, ...(item.tags || [])].filter(Boolean))].forEach((tag) => tags.append(text("span", tag, "me-tag")));
    row.append(tags);
  }
  const actions = document.createElement("div"); actions.className = "me-row-actions";
  if (!item.reviewSuspended) {
    actions.append(action("重来", () => gradeVocab(item, "again")), action("困难", () => gradeVocab(item, "hard")), action("记得", () => gradeVocab(item, "good")), action("简单", () => gradeVocab(item, "easy")));
  }
  actions.append(action(item.reviewSuspended ? "恢复复习" : "暂停复习", () => toggleVocabReview(item)), action("编辑", () => openVocabEditor(item)), action("删除", () => deleteVocab(item), "danger"));
  row.append(actions); return row;
}

function openVocabEditor(item = null) {
  $("#vocab-editor-title").textContent = item ? "编辑生词" : "新增生词";
  $("#vocab-edit-id").value = item?.id || "";
  $("#vocab-term").value = item?.term || "";
  $("#vocab-reading").value = item?.reading || "";
  $("#vocab-meaning").value = item?.meaning || "";
  $("#vocab-level").value = item?.level || "";
  $("#vocab-tags").value = (item?.tags || []).join(", ");
  $("#vocab-note").value = item?.note || "";
  $("#vocab-editor").showModal();
  $("#vocab-term").focus();
}

async function saveVocab(event) {
  if (event.submitter?.value === "cancel") return;
  event.preventDefault();
  const id = $("#vocab-edit-id").value;
  const now = new Date().toISOString();
  const payload = {
    term: $("#vocab-term").value.trim(), reading: $("#vocab-reading").value.trim(),
    meaning: $("#vocab-meaning").value.trim(), level: $("#vocab-level").value,
    tags: $("#vocab-tags").value.split(/[,，]/).map((tag) => tag.trim()).filter(Boolean),
    note: $("#vocab-note").value.trim(), updatedAt: now,
  };
  if (!payload.term) return toast("请输入词语");
  if (id) {
    const index = state.vocab.findIndex((item) => item.id === id);
    if (index >= 0) state.vocab[index] = { ...state.vocab[index], ...payload };
    await LearningDataSync.mutate("PATCH", `./api/vocab/${encodeURIComponent(id)}`, payload, { entityType: "vocab", entityKey: id });
  } else {
    const newId = `local_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const item = { id: newId, ...payload, createdAt: now, srsStage: 0, mastered: false };
    state.vocab.unshift(item);
    await LearningDataSync.mutate("POST", "./api/vocab", item, { entityType: "vocab", entityKey: newId });
  }
  state.vocab = PersonalDataTools.dedupeVocabEntries(state.vocab);
  $("#vocab-editor").close(); writeCache(); renderVocab(); updateSummary(); setConnection(); toast("生词已保存");
}

async function gradeVocab(item, grade) {
  const reviewedAt = new Date().toISOString();
  const { result, queued } = await LearningDataSync.mutate("POST", "./api/vocab/review", { vocabId: item.id, grade, reviewedAt }, { entityType: "vocab-review", entityKey: item.id, clearTombstone: false });
  const index = state.vocab.findIndex((entry) => entry.id === item.id);
  if (result?.item && index >= 0) state.vocab[index] = result.item;
  else if (index >= 0) state.vocab[index] = SrsScheduler.schedule(state.vocab[index], grade, reviewedAt);
  writeCache(); renderVocab(); setConnection(); toast(queued ? "复习结果已离线保存" : "复习结果已记录");
}

async function toggleVocabReview(item) {
  const suspended = !item.reviewSuspended;
  const index = state.vocab.findIndex((entry) => entry.id === item.id);
  if (index >= 0) state.vocab[index] = { ...state.vocab[index], reviewSuspended: suspended };
  await LearningDataSync.mutate(
    "POST", "./api/vocab/batch",
    { action: suspended ? "mark_mastered" : "mark_unmastered", ids: [item.id] },
    { entityType: "vocab", entityKey: item.id, clearTombstone: false },
  );
  writeCache(); renderVocab(); setConnection(); toast(suspended ? "已暂停复习" : "已恢复复习");
}

async function deleteVocab(item) {
  if (!window.confirm(`删除生词“${item.term}”？`)) return;
  state.vocab = state.vocab.filter((entry) => entry.id !== item.id);
  await LearningDataSync.mutate("DELETE", `./api/vocab/${encodeURIComponent(item.id)}`, null, { entityType: "vocab", entityKey: item.id, clearTombstone: false });
  writeCache(); renderVocab(); updateSummary(); setConnection();
}

async function importVocab(file) {
  const parsed = PersonalDataTools.parseVocabImport(await file.text());
  const existing = new Set(state.vocab.map(PersonalDataTools.vocabNaturalKey));
  const now = new Date().toISOString();
  const items = parsed.items.filter((item) => {
    const key = PersonalDataTools.vocabNaturalKey(item);
    if (!key || existing.has(key)) return false;
    existing.add(key); return true;
  }).map((item, index) => ({ id: `local_import_${Date.now()}_${index}`, ...item, createdAt: now, updatedAt: now }));
  if (!items.length) return toast(`没有可导入的新词${parsed.errors ? `（${parsed.errors} 行无效）` : ""}`);
  state.vocab = PersonalDataTools.dedupeVocabEntries([...items, ...state.vocab]);
  await LearningDataSync.mutate("POST", "./api/vocab/import", { items }, { entityType: "vocab-import", entityKey: String(Date.now()) });
  writeCache(); renderVocab(); updateSummary(); setConnection(); toast(`已导入 ${items.length} 个生词`);
}

function filteredNotes() {
  const query = $("#notes-search").value.trim().toLocaleLowerCase();
  const starred = $("#notes-starred").checked;
  return state.notes.filter((item) => {
    const haystack = [item.sourceText, item.text, item.tag, courseTitle(item.courseId)].join(" ").toLocaleLowerCase();
    return (!query || haystack.includes(query)) && (!starred || item.starred);
  }).sort((a, b) => String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")));
}

function renderNotes() {
  const list = $("#notes-list"); list.replaceChildren();
  const items = filteredNotes();
  if (!items.length) return list.appendChild(empty(state.notes.length ? "没有符合筛选条件的笔记。" : "还没有收藏或笔记。"));
  items.forEach((item) => list.appendChild(noteRow(item)));
}

function noteRow(item) {
  const row = document.createElement("article"); row.className = "me-row";
  const head = document.createElement("div"); head.className = "me-row-head";
  head.append(text("h3", `${item.starred ? "★ " : ""}${item.sourceText || item.sentenceId}`, "me-row-title"), text("span", `${courseTitle(item.courseId)} · ${formatDate(item.updatedAt)}`, "me-row-meta"));
  row.append(head);
  if (item.text) row.append(text("p", item.text, "me-row-copy"));
  if (item.tag) { const tags = document.createElement("div"); tags.className = "me-tags"; tags.append(text("span", item.tag, "me-tag")); row.append(tags); }
  const actions = document.createElement("div"); actions.className = "me-row-actions";
  actions.append(action("编辑", () => openNoteEditor(item)), action("删除", () => deleteNote(item), "danger"));
  row.append(actions); return row;
}

function openNoteEditor(item) {
  $("#note-course-id").value = item.courseId;
  $("#note-sentence-id").value = item.sentenceId;
  $("#note-source-preview").textContent = item.sourceText || item.sentenceId;
  $("#note-text").value = item.text || "";
  $("#note-tag").value = item.tag || "";
  $("#note-starred").checked = Boolean(item.starred);
  $("#note-editor").showModal();
}

async function saveNote(event) {
  if (event.submitter?.value === "cancel") return;
  event.preventDefault();
  const courseId = $("#note-course-id").value;
  const sentenceId = $("#note-sentence-id").value;
  const index = state.notes.findIndex((item) => item.courseId === courseId && item.sentenceId === sentenceId);
  if (index < 0) return;
  const payload = { text: $("#note-text").value.trim(), tag: $("#note-tag").value.trim(), starred: $("#note-starred").checked, sourceText: state.notes[index].sourceText || "", updatedAt: new Date().toISOString() };
  state.notes[index] = { ...state.notes[index], ...payload };
  await LearningDataSync.mutate("PUT", `./api/notes/${encodeURIComponent(courseId)}/${encodeURIComponent(sentenceId)}`, payload, { entityType: "note", entityKey: `${courseId}/${sentenceId}` });
  $("#note-editor").close(); writeCache(); renderNotes(); toast("笔记已保存"); setConnection();
}

async function deleteNote(item) {
  if (!window.confirm("删除这条笔记？")) return;
  state.notes = state.notes.filter((note) => note !== item);
  await LearningDataSync.mutate("DELETE", `./api/notes/${encodeURIComponent(item.courseId)}/${encodeURIComponent(item.sentenceId)}`, null, { entityType: "note", entityKey: `${item.courseId}/${item.sentenceId}`, clearTombstone: false });
  writeCache(); renderNotes(); updateSummary(); setConnection();
}

function renderAnalytics() {
  const cards = $("#analytics-cards"); cards.replaceChildren();
  const summary = state.analytics?.summary || {};
  [
    [summary.totalStudyDays || 0, "累计学习天数"], [summary.overallAccuracy || 0, "精听正确率", "%"],
    [summary.totalPracticed || 0, "已练句子"], [summary.totalDurationMs ? Math.round(summary.totalDurationMs / 60000) : 0, "学习时长", " 分钟"],
    [summary.totalVocab ?? state.vocab.length, "全库生词"], [summary.masteredVocab || 0, "已掌握生词"],
    [state.analytics?.examStats?.totalQuestionsAnswered || 0, "JLPT 已答题"], [state.analytics?.examStats?.accuracy || 0, "JLPT 正确率", "%"],
  ].forEach(([value, label, suffix = ""]) => {
    const card = document.createElement("div"); card.className = "analytics-card";
    card.append(text("strong", `${value}${suffix}`), text("span", label)); cards.append(card);
  });
  const trend = $("#analytics-trend"); trend.replaceChildren();
  const heatmap = state.analytics?.heatmap || [];
  const days = heatmap.slice(-30);
  const maxAttempts = Math.max(1, ...days.map((day) => Number(day.attempts || 0)));
  for (let index = 30 - days.length; index > 0; index -= 1) trend.append(text("span", ""));
  days.forEach((day) => {
    const bar = text("span", "");
    bar.style.height = `${Math.max(3, Math.round((Number(day.attempts || 0) / maxAttempts) * 100))}%`;
    bar.title = `${day.day}：${day.attempts || 0} 次练习，正确率 ${day.accuracy || 0}%`;
    trend.append(bar);
  });
  renderLogs();
}

function renderLogs() {
  const list = $("#study-logs-list"); list.replaceChildren();
  if (!state.logs.length) return list.appendChild(empty("还没有学习记录。"));
  state.logs.forEach((item) => {
    const row = document.createElement("article"); row.className = "me-row";
    const head = document.createElement("div"); head.className = "me-row-head";
    head.append(text("h3", `${item.isCorrect ? "✓" : "×"} ${courseTitle(item.courseId)} · ${item.sentenceId}`, "me-row-title"), text("span", formatDate(item.createdAt), "me-row-meta"));
    row.append(head, text("p", `得分 ${Math.round(item.score || 0)} · ${Math.round((item.durationMs || 0) / 1000)} 秒${item.userInput ? ` · ${item.userInput}` : ""}`, "me-row-copy"));
    list.append(row);
  });
}

async function punchIn() {
  const today = new Date();
  const day = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  await LearningDataSync.mutate("POST", "./api/punch-in", { day, mood: "🔥", note: "", sentencesCount: 0, studyDurationMs: 0 }, { entityType: "punch", entityKey: day });
  $("#punch-button").textContent = "✓ 今日已打卡";
  $("#punch-button").disabled = true;
  setConnection(); toast("今日打卡已记录");
}

function download(name, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a"); link.href = url; link.download = name; link.click();
  URL.revokeObjectURL(url);
}

function csvCell(value) { return `"${String(value ?? "").replaceAll('"', '""')}"`; }

function exportLogs() {
  const rows = [["date", "course", "sentence", "correct", "score", "durationMs", "input"], ...state.logs.map((item) => [item.createdAt, courseTitle(item.courseId), item.sentenceId, item.isCorrect, item.score, item.durationMs, item.userInput])];
  download("study-logs.csv", `\uFEFF${rows.map((row) => row.map(csvCell).join(",")).join("\n")}`, "text/csv;charset=utf-8");
}

function exportNotes() {
  const body = state.notes.map((item) => `## ${item.starred ? "★ " : ""}${item.sourceText || item.sentenceId}\n\n- 课程：${courseTitle(item.courseId)}\n- 标签：${item.tag || "无"}\n\n${item.text || ""}`).join("\n\n---\n\n");
  download("learning-notes.md", `# 学习笔记\n\n${body}\n`, "text/markdown;charset=utf-8");
}

function bindEvents() {
  $$("[data-tab]").forEach((button, index, buttons) => {
    button.addEventListener("click", () => { location.hash = `#/${button.dataset.tab}`; });
    button.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const delta = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1;
      const target = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (index + delta + buttons.length) % buttons.length;
      buttons[target].focus(); buttons[target].click();
    });
  });
  $$("[data-mistake-scope]").forEach((button) => button.addEventListener("click", () => { location.hash = `#/mistakes/${button.dataset.mistakeScope}`; }));
  window.addEventListener("hashchange", activateRoute);
  $("#retry-button").addEventListener("click", loadAll);
  $("#vocab-search").addEventListener("input", renderVocab);
  $("#vocab-status").addEventListener("change", renderVocab);
  $("#vocab-add-button").addEventListener("click", () => openVocabEditor());
  $("#vocab-form").addEventListener("submit", saveVocab);
  $("#vocab-import-button").addEventListener("click", () => $("#vocab-import-file").click());
  $("#vocab-import-file").addEventListener("change", async (event) => { if (event.target.files?.[0]) await importVocab(event.target.files[0]); event.target.value = ""; });
  $("#notes-search").addEventListener("input", renderNotes);
  $("#notes-starred").addEventListener("change", renderNotes);
  $("#notes-export-button").addEventListener("click", exportNotes);
  $("#note-form").addEventListener("submit", saveNote);
  $("#punch-button").addEventListener("click", punchIn);
  $("#logs-export-button").addEventListener("click", exportLogs);
  window.addEventListener("online", reconnect);
}

async function reconnect() {
  try {
    await acquireToken(); state.online = true; await LearningDataSync.flush(); await loadAll();
  } catch { state.online = false; }
  setConnection();
}

async function boot() {
  restoreCache(); bindEvents(); activateRoute(); renderAll();
  try {
    await acquireToken();
    state.online = true;
  } catch (error) {
    state.online = false;
    setStatus("本地服务未连接，当前显示上次缓存；修改会排队等待同步。", true);
  }
  LearningDataSync.configure({ sender: sendSyncOperation, isOnline: () => state.online && navigator.onLine });
  LearningDataSync.subscribe(setConnection);
  setConnection();
  await LearningCards.migrateLegacyStorage();
  // A long-lived subscription, so a change made in the lexicon workspace shows up here
  // without the learner reloading. Coalesced: a burst of edits redraws once.
  let pendingRefresh = null;
  LearningCards.subscribe(() => {
    clearTimeout(pendingRefresh);
    pendingRefresh = setTimeout(() => {
      if (state.online) loadAll().catch(() => {});
      else LearningCards.localCards().then((cards) => {
        if (cards.length) { state.vocab = PersonalDataTools.dedupeVocabEntries(cards); renderAll(); }
      });
    }, 300);
  });
  if (state.online) {
    await LearningDataSync.flush();
    await loadAll();
  }
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => {});
}

boot().catch((error) => setStatus(error.message || "个人中心启动失败", true));
