"use strict";
/* ==========================================================================
   練習工作区
   --------------------------------------------------------------------------
   L1 科目首页 → L2 科目分类 → L3 练法 → L4 对象列表 → L5 setup
   → L6 作答 → L7 复盘。每一层一个 .view，同一时刻只显示一个，每一层有
   自己的 hash，刷新停在原处、后退键在应用内导航。
   ========================================================================== */

Object.assign(state, {
  papers: [],
  subject: "ALL",
  activePaper: null,
  activeSession: null,
  activeQuestions: [],
  responses: {},
  baseResponses: {},
  baseVersion: 0,
  notes: {},
  timerInterval: null,
  autoSaveTimer: null,
  dirtyResponses: false,
  pendingResponses: {},
  nextEdit: 0,
  saveRequest: null,
  saving: null,
  submitting: false,
  flags: new Set(),
  currentQuestionId: null,
  currentView: "view-subjects",
  viewMode: "ALL",
  layoutMode: localStorage.getItem("eju.layoutMode") || "SPLIT",
  sessionGeneration: 0,
  renderSessionId: null,
});

const main = $("#main");

/* 另一个标签页提交或保存了同一个会话时，这里同步过来，避免两边各写各的。 */
const sessionSyncChannel =
  typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("eju_session_sync") : null;
if (sessionSyncChannel) {
  sessionSyncChannel.onmessage = (event) => {
    const data = event.data;
    if (!data || data.libraryInstanceId !== state.libraryInstanceId ||
        !state.activeSession || data.sessionId !== state.activeSession.sessionId) return;
    if (data.type === "session_submitted") {
      state.activeSession.status = "SUBMITTED";
      applySessionState();
      showError(new Error("本会话已在另一标签页提交。"));
    } else if (data.type === "session_saved") {
      if (data.responseVersion > (state.activeSession.responseVersion || 0)) {
        if (state.dirtyResponses) scheduleAutoSave();
        else reconcileConflict(state.activeSession.sessionId).catch(showError);
      }
    }
  };
}

// ── 视图切换 ──────────────────────────────────────────────────────────────
const BRAND = {
  "view-subjects": ["開始練習", "選一個科目"],
  "view-papers": ["整卷模考", "选一套卷"],
  "view-forms": ["单科精练", "选一门"],
  "view-collect": ["专项组题", "跨卷检索"],
  "view-setup": ["开始练习", "确认选科与模式"],
  "view-session": ["作答中", "本次会话"],
  "view-result": ["作答复盘", "成绩与逐题解析"],
};

function showView(id) {
  state.currentView = id;
  showOnly(main, id);
  const [title, subtitle] = BRAND[id] || BRAND["view-subjects"];
  $("#brand-title").textContent = title;
  $("#brand-subtitle").textContent = subtitle;
  // 卷子切换浮层只在作答中有意义。
  $("#switcher-wrap").hidden = id !== "view-session";
  if (id !== "view-session") closeSwitcher();
  window.scrollTo({ top: 0, behavior: "instant" });
}

// ── L1 + L2 + L3：科目与练法 ──────────────────────────────────────────────
async function loadPapers() {
  const { papers } = await api("/api/v1/papers");
  state.papers = papers;
  return papers;
}

function papersOfSubject(subject = state.subject) {
  if (subject === "ALL") return state.papers;
  const group = SUBJECT_GROUPS.find((g) => g.id === subject);
  if (!group) return state.papers;
  return state.papers.filter((p) =>
    p.subject === subject || (p.forms || []).some((f) => group.forms.includes(f)));
}

function paperIsOpen(paper) {
  return !["REVIEW_REQUIRED", "SUSPENDED"].includes(paper.deliveryState);
}

function renderSubjectSwitch() {
  const nav = $("#subject-switch");
  nav.replaceChildren();
  const entries = [{ id: "ALL", label: "全部", color: "var(--ai)" }, ...SUBJECT_GROUPS];
  for (const entry of entries) {
    const count = papersOfSubject(entry.id).length;
    if (entry.id !== "ALL" && !count) continue;   // 没有该科目的卷子就不显示这一类
    const tab = el("button", "category-tab" + (state.subject === entry.id ? " is-active" : ""));
    tab.type = "button";
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", String(state.subject === entry.id));
    const dot = el("span", "category-dot");
    dot.style.background = entry.color;
    dot.setAttribute("aria-hidden", "true");
    tab.append(dot, el("span", "", entry.label), el("span", "tab-badge", String(count)));
    tab.addEventListener("click", () => {
      state.subject = entry.id;
      Router.replace(entry.id === "ALL" ? "#/" : `#/subject/${entry.id}`);
      renderSubjects();
    });
    nav.append(tab);
  }
}

function renderSubjects() {
  renderSubjectSwitch();
  const scoped = papersOfSubject();
  const open = scoped.filter(paperIsOpen);
  const complete = open.filter((p) => p.completeness === "COMPLETE");
  const forms = new Set(open.flatMap((p) => p.forms || []));
  const questions = open.reduce((n, p) => n + (p.questionCount || 0), 0);

  $("#mock-stat").textContent = complete.length
    ? `${complete.length} 套完整卷可计时`
    : "该科目暂无完整整套卷";
  $("#mode-card-mock").disabled = !complete.length;
  $("#form-stat").textContent = forms.size ? `${forms.size} 个分科` : "暂无可练分科";
  $("#mode-card-form").disabled = !forms.size;
  $("#collect-stat").textContent = questions ? `${questions} 题可检索` : "暂无可检索题目";

  const suspended = scoped.length - open.length;
  $("#subjects-status").textContent = scoped.length
    ? `共 ${scoped.length} 套卷` + (suspended ? ` · 其中 ${suspended} 套内容待复核，暂停新练习` : "")
    : "";
  $("#subjects-empty").hidden = state.papers.length > 0;
  $("#study-mode-grid").hidden = state.papers.length === 0;
}

$("#mode-card-mock").addEventListener("click", () => Router.go(subjectHash("papers")));
$("#mode-card-form").addEventListener("click", () => Router.go(subjectHash("forms")));
$("#mode-card-collect").addEventListener("click", () => Router.go("#/collect"));

function subjectHash(screen) {
  const base = state.subject === "ALL" ? "ALL" : state.subject;
  return screen ? `#/subject/${base}/${screen}` : (base === "ALL" ? "#/" : `#/subject/${base}`);
}

// ── L4a：整卷模考 → 卷子列表 ─────────────────────────────────────────────
function renderPaperList() {
  const list = $("#paper-list");
  list.replaceChildren();

  const sessionValue = $("#filter-session").value;
  const completeness = $("#filter-completeness").value;
  const scoped = papersOfSubject().filter((p) =>
    (!sessionValue || p.session === sessionValue) &&
    (!completeness || p.completeness === completeness) &&
    (!state.formFilter || (p.forms || []).includes(state.formFilter)));

  // 年度下拉按当前科目下真实存在的回次填充
  const select = $("#filter-session");
  const sessions = [...new Set(papersOfSubject().map((p) => p.session).filter(Boolean))].sort();
  const keep = select.value;
  select.replaceChildren(Object.assign(el("option", "", "全部年度与回次"), { value: "" }));
  for (const s of sessions) {
    const option = el("option", "", `${s} 回`);
    option.value = s;
    select.append(option);
  }
  select.value = sessions.includes(keep) ? keep : "";

  $("#papers-status").textContent = state.formFilter
    ? `${scoped.length} 套卷含「${I18N.translateForm(state.formFilter)}」`
    : `${scoped.length} 套卷`;
  if (!scoped.length) {
    list.append(el("p", "empty-hint", "没有符合筛选条件的试卷。"));
    return;
  }
  for (const paper of scoped) list.append(paperCard(paper));
}

/* 卷子卡：年度回次 + 科目色条 + 题量 + 复核状态 + 上次成绩。
   四种状态各有自己的徽章，"待复核暂停练习"不再只是一句灰字。 */
function paperCard(paper) {
  const subject = paper.subject || subjectGroupOfForm((paper.forms || [])[0]);
  const card = el("article", `paper-card subject-${subject}`);

  const head = el("div", "paper-card-head");
  head.append(el("span", "session-badge", paper.session || "留考"));
  head.append(el("span", "tag", I18N.languages[paper.language] || paper.language || "ja"));
  card.append(head);
  card.append(el("h3", "", I18N.translatePaperTitle(paper.title)));

  const meta = el("div", "paper-meta");
  meta.append(
    el("span", "", `${paper.questionCount || 0} 题`),
    el("span", "", `第 ${paper.version} 版`),
    el("span", "", I18N.syllabus[paper.syllabusVersion] || paper.syllabusVersion || "—"),
  );
  card.append(meta);

  const tags = el("div", "paper-forms-tags");
  for (const f of paper.forms || []) tags.append(el("span", "tag", I18N.translateShortForm(f)));
  card.append(tags);

  const badges = el("div", "paper-forms-tags");
  const open = paperIsOpen(paper);
  if (!open) badges.append(el("span", "badge badge-wait", "◷ 内容待复核"));
  else if (paper.completeness === "COMPLETE") badges.append(el("span", "badge badge-ok", "✓ 完整整套卷"));
  else badges.append(el("span", `badge badge-${paper.completeness === "PARTIAL" ? "part" : "sample"}`,
    I18N.translateCompleteness(paper.completeness)));
  if (paper.missingAudio || (paper.blockingIssues || []).includes("MISSING_AUDIO")) {
    badges.append(el("span", "badge badge-miss", "⚠ 缺少音频"));
  }
  const grade = I18N.translateReviewGrade(paper.reviewGrade);
  if (grade && paper.reviewGrade !== "HUMAN_SIGNED") {
    const tag = el("span", `badge badge-${grade.cls}`, grade.label);
    tag.title = grade.title;
    badges.append(tag);
  }
  card.append(badges);

  if (paper.deliveryNote) card.append(el("p", "content-warning", paper.deliveryNote));

  const foot = el("div", "paper-card-foot");
  const last = state.lastAttempts?.[paper.paperId];
  foot.append(el("span", "paper-card-last", last
    ? `上次 ${new Date(last.at).toLocaleDateString()} · 正确率 ${Math.round((last.accuracy || 0) * 100)}%`
    : "尚未练习过"));
  const btn = el("button", "primary-button", open ? "开始" : "内容待复核");
  btn.type = "button";
  btn.disabled = !open;
  btn.addEventListener("click", () => Router.go(
    state.formFilter ? `#/paper/${paper.paperId}?form=${state.formFilter}` : `#/paper/${paper.paperId}`));
  foot.append(btn);
  card.append(foot);
  return card;
}

$("#filter-session").addEventListener("change", renderPaperList);
$("#filter-completeness").addEventListener("change", renderPaperList);
$("#papers-back").addEventListener("click", () => Router.go(subjectHash("")));

// ── L4b：单科精练 → 分科列表 ─────────────────────────────────────────────
function renderFormList() {
  const list = $("#form-list");
  list.replaceChildren();
  const scoped = papersOfSubject().filter(paperIsOpen);

  /* 一个分科横跨多套卷：这里按 formCode 聚合，卡上写清有几套卷可练。 */
  const byForm = new Map();
  for (const paper of scoped) {
    for (const formCode of paper.forms || []) {
      if (state.subject !== "ALL" && subjectGroupOfForm(formCode) !== state.subject) continue;
      if (!byForm.has(formCode)) byForm.set(formCode, []);
      byForm.get(formCode).push(paper);
    }
  }

  $("#forms-status").textContent = `${byForm.size} 个分科`;
  if (!byForm.size) {
    list.append(el("p", "empty-hint", "该科目下还没有可练的分科。"));
    return;
  }

  for (const [formCode, papers] of [...byForm].sort()) {
    const card = el("article", `paper-card subject-${subjectGroupOfForm(formCode)}`);
    card.append(el("h3", "", I18N.translateForm(formCode)));
    const meta = el("div", "paper-meta");
    meta.append(
      el("span", "", `${papers.length} 套卷可练`),
      el("span", "", papers.map((p) => p.session).join("、")),
    );
    card.append(meta);
    const foot = el("div", "paper-card-foot");
    foot.append(el("span", "paper-card-last", "自由练习 · 无强制倒计时"));
    const btn = el("button", "primary-button", "选一套卷");
    btn.type = "button";
    btn.addEventListener("click", () => {
      state.pendingForm = formCode;
      if (papers.length === 1) Router.go(`#/paper/${papers[0].paperId}?form=${formCode}`);
      else {
        // 多套卷时回到卷子列表，但只列含这个分科的卷。
        state.formFilter = formCode;
        Router.go(subjectHash("papers"));
      }
    });
    foot.append(btn);
    card.append(foot);
    list.append(card);
  }
}
$("#forms-back").addEventListener("click", () => Router.go(subjectHash("")));
$("#collect-back").addEventListener("click", () => Router.go(subjectHash("")));

// ── L4c：专项组题（跨卷检索） ────────────────────────────────────────────
const collectionState = { cursor: 0, selected: new Set(), items: [], next: null, history: [], generation: 0 };

function updateCollectionCount(total) {
  $("#collection-count").textContent =
    `已选 ${collectionState.selected.size} 题` + (total !== undefined ? `，搜索结果 ${total} 题` : "");
}

async function loadCollection() {
  const generation = ++collectionState.generation;
  const forms = $("#collection-form");
  const selectedForm = forms.value;
  const codes = [...new Set(state.papers.flatMap((p) => p.forms || []))];
  for (const code of codes) {
    if (![...forms.options].some((o) => o.value === code)) {
      const option = el("option", "", I18N.translateForm(code));
      option.value = code;
      forms.append(option);
    }
  }
  forms.value = selectedForm;

  const params = new URLSearchParams({
    kind: $("#collection-kind").value, cursor: collectionState.cursor, limit: 20,
  });
  for (const [id, key] of [["collection-form", "form"], ["collection-query", "q"], ["collection-topic", "topic"]]) {
    if (document.getElementById(id).value.trim()) params.set(key, document.getElementById(id).value.trim());
  }
  const result = await api(`/api/v1/questions?${params}`);
  if (generation !== collectionState.generation) return;
  collectionState.items = result.questions;
  collectionState.next = result.nextCursor;

  const list = $("#collection-list");
  list.replaceChildren();
  if (!result.questions.length) list.append(el("p", "empty-hint", "当前没有符合条件的题目。"));

  for (const q of result.questions) {
    const card = el("article", `paper-card subject-${subjectGroupOfForm(q.formCode)}`);
    const label = el("label", "collection-select");
    const cb = el("input");
    cb.type = "checkbox";
    cb.disabled = q.available === false;
    cb.checked = collectionState.selected.has(q.questionId);
    cb.addEventListener("change", () => {
      if (cb.checked) collectionState.selected.add(q.questionId);
      else collectionState.selected.delete(q.questionId);
      updateCollectionCount(result.total);
    });
    label.append(cb, document.createTextNode(
      `${q.sourceSession} · ${I18N.translateShortForm(q.formCode)} · ${q.printedLabel || q.localKey}`));
    card.append(label);
    for (const mat of q.materials || []) card.append(renderAst(mat.contentAst));
    card.append(renderAst(q.stemAst));

    const actions = el("div", "collection-actions");
    const practice = el("button", "primary-button", "练习此题");
    practice.type = "button";
    practice.disabled = q.available === false;
    if (q.available === false) card.append(el("p", "subtitle", q.deliveryNote || "内容停用，个人记录保留"));
    practice.addEventListener("click", () => startCollection([q.questionId]).catch(showError));
    const bookmark = el("button", "btn btn-outline", q.bookmarked ? "★ 已收藏" : "☆ 收藏");
    bookmark.type = "button";
    if (q.bookmarked) state.bookmarks.add(q.questionId); else state.bookmarks.delete(q.questionId);
    bookmark.addEventListener("click", () => toggleBookmark(q.questionId, bookmark).catch(showError));
    actions.append(practice, bookmark);
    card.append(actions, createNoteEditor(q.questionId));
    list.append(card);
  }
  $("#collection-prev").disabled = collectionState.cursor === 0;
  $("#collection-next").disabled = result.nextCursor === null;
  updateCollectionCount(result.total);
}

/* 组题前先看预览：共享材料会把实际题量抬高，让人在开始前就知道。 */
async function startCollection(questionIds) {
  if (state.activeSession?.status === "IN_PROGRESS") await flushAutoSave();
  const preview = await api("/api/v1/practice/previews", {
    method: "POST",
    body: JSON.stringify({ questionIds, randomOrder: $("#collection-random")?.checked || false }),
  });
  const dialog = document.createElement("dialog");
  dialog.setAttribute("aria-label", "练习预览");
  dialog.append(
    el("h3", "", "练习预览"),
    el("p", "", `选择 ${preview.requestedCount} 题，包含共享材料后实际 ${preview.actualCount} 题。预览已固定题目版本。`),
  );
  const proceed = await new Promise((resolve) => {
    const start = el("button", "primary-button", "开始预览中的练习");
    const cancel = el("button", "btn btn-outline", "取消");
    start.type = cancel.type = "button";
    start.addEventListener("click", () => { resolve(true); dialog.close(); });
    cancel.addEventListener("click", () => { resolve(false); dialog.close(); });
    dialog.addEventListener("cancel", () => resolve(false));
    dialog.append(start, cancel);
    document.body.append(dialog);
    dialog.showModal();
  });
  dialog.remove();
  if (!proceed) return;
  const session = await api(`/api/v1/practice/previews/${preview.previewId}/start`, {
    method: "POST", body: JSON.stringify({ requestId: crypto.randomUUID() }),
  });
  await restoreSession(session.sessionId);
}

$("#collection-search").addEventListener("click", act(() => {
  collectionState.cursor = 0; collectionState.history = []; return loadCollection();
}));
$("#collection-kind").addEventListener("change", act(() => {
  collectionState.cursor = 0; collectionState.history = []; return loadCollection();
}));
$("#collection-prev").addEventListener("click", act(() => {
  collectionState.cursor = collectionState.history.pop() ?? 0; return loadCollection();
}));
$("#collection-next").addEventListener("click", act(() => {
  collectionState.history.push(collectionState.cursor);
  collectionState.cursor = collectionState.next ?? 0;
  return loadCollection();
}));
$("#collection-select-page").addEventListener("click", () => {
  for (const q of collectionState.items) if (q.available !== false) collectionState.selected.add(q.questionId);
  $$("#collection-list input[type=checkbox]").forEach((cb) => { cb.checked = !cb.disabled; });
  updateCollectionCount();
});
$("#collection-clear").addEventListener("click", () => {
  collectionState.selected.clear();
  $$("#collection-list input[type=checkbox]").forEach((cb) => { cb.checked = false; });
  updateCollectionCount();
});
$("#collection-start").addEventListener("click", act(() => startCollection([...collectionState.selected])));

// ── L5：开始练习 ─────────────────────────────────────────────────────────
let configuringPaper = null;
let setupPreselect = null;

/* 选科互斥是 EJU 的考试规则，不是本程序的限制：在开始前用文字讲清楚，
   而不是等提交后再报错。 */
const SELECTION_RULES = {
  MOCK: "全真模考按考试规则校验：理科需在物理・化学・生物中恰好选 2 门；" +
        "理科与総合科目属于同一时段，不能同时选；数学 1 类与 2 类二选一。",
  PRACTICE: "自由练习不校验互斥规则，可以只选一门，也可以任意组合。",
};

async function openSetup(paperId, options = {}) {
  state.renderSessionId = null;
  setupPreselect = options.form || null;
  const { paper } = await api(`/api/v1/papers/${paperId}`);
  configuringPaper = paper;

  $("#setup-heading").textContent = I18N.translatePaperTitle(paper.title);
  $("#setup-meta").textContent =
    `${paper.session || "留考"} · ${I18N.languages[paper.language] || paper.language || "ja"}` +
    ` · ${paper.questionCount || 0} 题 · ${I18N.translateCompleteness(paper.completeness)}`;

  // 把关程度与这份卷缺了什么，说在开始作答之前，而不是练完才发现。
  const gradeNote = $("#setup-review-note");
  if (gradeNote) {
    const grade = I18N.translateReviewGrade(paper.reviewGrade);
    const lines = [];
    if (grade && paper.reviewGrade !== "HUMAN_SIGNED") lines.push(`${grade.label}：${grade.title}`);
    for (const reason of paper.missingContentReasons || []) lines.push(reason);
    gradeNote.replaceChildren(...lines.map((text) => el("p", "", text)));
    gradeNote.hidden = lines.length === 0;
  }

  const container = $("#setup-form-selection");
  container.replaceChildren();
  for (const f of paper.forms || []) {
    const count = (f.groups || []).reduce((n, g) => n + g.questions.length, 0);
    const label = el("label", "checkbox-label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.value = f.formCode;
    cb.checked = setupPreselect ? f.formCode === setupPreselect : true;
    cb.addEventListener("change", validateSelection);
    label.append(cb, el("span", "", I18N.translateForm(f.formCode)),
      el("span", "form-count", `${count} 题`));
    container.append(label);
  }

  const sectionBox = $("#section-selection");
  sectionBox.replaceChildren();
  for (const section of paper.sections || []) {
    const label = el("label", "checkbox-label");
    const cb = el("input");
    cb.type = "checkbox";
    cb.value = section.sectionId;
    cb.checked = true;
    label.append(cb, el("span", "", `分区 ${section.sectionId}`));
    sectionBox.append(label);
  }

  const modes = paper.availableModes || ["PRACTICE"];
  for (const radio of $$('input[name="exam-mode"]')) {
    radio.disabled = !modes.includes(radio.value) ||
      (radio.value === "MOCK" && paper.completeness !== "COMPLETE");
  }
  // 从单科精练进来的，默认就是自由练习。
  if (setupPreselect || $('input[name="exam-mode"]:checked')?.disabled) {
    $('input[name="exam-mode"][value="PRACTICE"]').checked = true;
  }
  $("#mode-note").textContent = modes.includes("MOCK")
    ? (paper.completeness === "COMPLETE" ? "" : "这套卷不是完整整套卷，暂不开放全真模考。")
    : "这套卷暂未开放全真模考。";

  validateSelection();
  await renderSetupHistory(paperId);
}

function validateSelection() {
  const mode = $('input[name="exam-mode"]:checked').value;
  const selected = [...$$("#setup-form-selection input:checked")].map((c) => c.value);
  const errBox = $("#selection-error");
  const rules = $("#selection-rules");
  rules.textContent = SELECTION_RULES[mode];
  rules.classList.toggle("is-strict", mode === "MOCK");

  const fail = (message) => {
    errBox.textContent = message;
    errBox.classList.remove("hidden");
    $("#setup-start").disabled = true;
    $("#setup-hint").textContent = "";
  };

  if (!selected.length) return fail("请至少勾选一个作答科目。");

  if (mode === "MOCK") {
    const science = selected.filter((f) => /^(PHYSICS|CHEMISTRY|BIOLOGY)/.test(f));
    const hasWorld = selected.some((f) => f.startsWith("JAPAN_AND_WORLD"));
    const maths = selected.filter((f) => f.startsWith("MATHEMATICS"));
    if (science.length > 0 && science.length !== 2) {
      return fail("正式理科模考必须在物理、化学、生物 3 科中恰好选择 2 科作答。");
    }
    if (science.length > 0 && hasWorld) {
      return fail("理科与综合科目属于同时段考试，不能同时报考。");
    }
    if (maths.length > 1) {
      return fail("数学 1 类（文科）与数学 2 类（理科）只能二选一。");
    }
  }

  // 同时段的科目共用一份时长，不能简单相加。
  const timing = new Map();
  let questionCount = 0;
  for (const form of configuringPaper.forms.filter((f) => selected.includes(f.formCode))) {
    const spec = form.spec || {};
    const key = spec.shared_timing_group || form.formCode;
    timing.set(key, Math.max(timing.get(key) || 0, spec.duration_sec || 0));
    questionCount += (form.groups || []).reduce((n, g) => n + g.questions.length, 0);
  }
  const minutes = [...timing.values()].reduce((a, b) => a + b, 0) / 60;
  $("#duration-hint").innerHTML = "";
  $("#duration-hint").append(
    el("strong", "", `${questionCount} 题`),
    document.createTextNode(mode === "MOCK"
      ? ` · 作答限时 ${minutes} 分钟 · 交卷后锁定`
      : " · 自由练习无强制限时，作答会自动保存"),
  );
  errBox.classList.add("hidden");
  $("#setup-start").disabled = false;
  $("#setup-hint").textContent = mode === "MOCK" ? "选科符合考试规则" : "";
}

$$('input[name="exam-mode"]').forEach((r) => r.addEventListener("change", validateSelection));

async function renderSetupHistory(paperId) {
  const block = $("#setup-history-block");
  const rows = $("#setup-history");
  rows.replaceChildren();
  let history = [];
  try { ({ history } = await api("/api/v1/history?limit=50")); } catch { block.hidden = true; return; }
  const mine = history.filter((h) => h.paperId === paperId);
  block.hidden = !mine.length;
  if (!mine.length) return;

  // 卷子卡上的“上次成绩”也从这里来，顺手缓存。
  state.lastAttempts ||= {};
  const latest = mine.find((h) => h.summary);
  if (latest) {
    state.lastAttempts[paperId] = {
      at: latest.submittedAt || latest.createdAt, accuracy: latest.summary.objectiveAccuracy,
    };
  }

  for (const h of mine.slice(0, 8)) {
    const row = el("div", "history-row");
    const meta = el("div", "history-row-meta");
    meta.append(
      el("span", "", new Date(h.submittedAt || h.createdAt).toLocaleString()),
      el("span", "", I18N.translateMode(h.mode)),
      el("span", "", (h.selectedForms || []).map(I18N.translateShortForm.bind(I18N)).join("、")),
      el("span", "", h.summary
        ? `${h.summary.objectiveCorrect} / ${h.summary.objectiveTotal} 题正确`
        : I18N.translateStatus(h.status)),
    );
    row.append(meta);
    const actions = el("div", "history-row-actions");
    if (h.status === "SUBMITTED") {
      actions.append(actionButton("查看复盘", () => Router.go(`#/result/${h.sessionId}`)));
      actions.append(actionButton("重练本次错题", () => retryWrongOfSession(h.sessionId)));
    } else if (h.status !== "ABANDONED") {
      actions.append(actionButton("继续这次作答", () => Router.go(`#/session/${h.sessionId}`)));
    }
    row.append(actions);
    rows.append(row);
  }
}

async function retryWrongOfSession(sessionId) {
  const { result } = await api(`/api/v1/sessions/${sessionId}/result`);
  const ids = (result.questions || []).filter((q) => q.answered && q.correct === false).map((q) => q.questionId);
  if (!ids.length) throw new Error("这次作答没有需要重练的错题。");
  await startCollection(ids);
}

$("#setup-start").addEventListener("click", act(async () => {
  const mode = $('input[name="exam-mode"]:checked').value;
  const selected = [...$$("#setup-form-selection input:checked")].map((c) => c.value);
  await startExamSession(configuringPaper.paperId, selected, mode);
}));
$("#setup-back").addEventListener("click", () => Router.go(subjectHash("papers")));
$("#result-back").addEventListener("click", () => Router.go(subjectHash("")));

async function startExamSession(paperId, selectedForms, mode, questionIds = null, sectionCodes = null) {
  if (state.activeSession?.status === "IN_PROGRESS") await flushAutoSave();
  const sess = await api("/api/v1/sessions", {
    method: "POST",
    body: JSON.stringify({
      paperId, selectedForms, mode, questionIds,
      ...(mode === "SECTION"
        ? { sectionCodes: sectionCodes || [...$$("#section-selection input:checked")].map((x) => x.value) }
        : {}),
    }),
  });
  await restoreSession(sess.sessionId);
}

// ── L6：作答 ─────────────────────────────────────────────────────────────
async function loadSessionPaper(sessionId) {
  const { paper } = await api(`/api/v1/sessions/${sessionId}/outline`);
  const questions = new Map();
  let cursor = 0;
  do {
    const page = await api(`/api/v1/sessions/${sessionId}/questions?limit=100&cursor=${encodeURIComponent(cursor)}`);
    for (const item of page.questions) questions.set(item.question.questionId, item.question);
    cursor = page.nextCursor;
  } while (cursor !== null);
  for (const form of paper.forms) {
    for (const group of form.groups) group.questions = group.questions.map((q) => questions.get(q.questionId));
  }
  return { paper };
}

/* 全局函数：浏览器测试与「继续上次练习」深链都从这里进作答。 */
async function restoreSession(sessionId) {
  if (state.activeSession?.status === "IN_PROGRESS" && state.activeSession.sessionId !== sessionId) {
    await flushAutoSave();
  }
  clearTimeout(state.autoSaveTimer);
  state.sessionGeneration = (state.sessionGeneration || 0) + 1;
  const currentGeneration = state.sessionGeneration;

  const [{ session: sess }, { paper }, { bookmarks }] = await Promise.all([
    api(`/api/v1/sessions/${sessionId}`), loadSessionPaper(sessionId), api("/api/v1/bookmarks"),
  ]);
  if (currentGeneration !== state.sessionGeneration) return;

  state.activePaper = paper;
  state.activeSession = sess;
  state.renderSessionId = sess.sessionId;
  sess.receivedAt = performance.now();
  state.responses = Object.fromEntries(Object.entries(sess.responses).map(([q, v]) => [q, v.value]));
  state.baseResponses = JSON.parse(JSON.stringify(state.responses));
  state.baseVersion = sess.responseVersion;
  state.pendingResponses = {};
  state.saveRequest = null;
  state.nextEdit = 0;
  state.flags = new Set(sess.progress?.flaggedQuestionIds || []);
  state.currentQuestionId = sess.progress?.currentQuestionId;
  state.viewMode = sess.progress?.viewMode || "ALL";
  state.bookmarks = new Set(bookmarks.map((b) => b.questionId));

  const draft = readDraft(sessionId);
  if (draft && ["IN_PROGRESS", "PAUSED"].includes(sess.status)) {
    state.pendingResponses = draft.pendingResponses || {};
    state.saveRequest = draft.saveRequest || null;
    state.nextEdit = draft.nextEdit || 0;
    if (draft.baseResponses) state.baseResponses = draft.baseResponses;
    if (draft.baseVersion !== undefined) state.baseVersion = draft.baseVersion;
    if (Object.keys(state.pendingResponses).length) {
      state.activeSession.responseVersion = draft.responseVersion ?? sess.responseVersion;
      for (const [qid, entry] of Object.entries(state.pendingResponses)) state.responses[qid] = entry.response;
    }
    state.currentQuestionId = draft.progress?.currentQuestionId || state.currentQuestionId;
    state.flags = new Set(draft.progress?.flaggedQuestionIds || [...state.flags]);
  }
  state.dirtyResponses = Object.keys(state.pendingResponses).length > 0;
  localStorage.setItem(`eju.activeSession.${state.libraryInstanceId}`, sessionId);

  $("#top-paper-session").textContent = `${paper.session} · 第${sess.paperVersion}版`;
  $("#top-paper-title").textContent = I18N.translatePaperTitle(paper.title);
  $("#top-paper-mode").textContent = I18N.translateMode(sess.mode);

  state.activeQuestions = [];
  for (const form of paper.forms || []) {
    for (const group of form.groups || []) {
      for (const question of group.questions || []) state.activeQuestions.push({ form, group, question });
    }
  }
  renderPalette();
  renderQuestionsWorkspace();
  for (const { question } of state.activeQuestions) updatePaletteStatus(question.questionId);
  applySessionState();
  loadSessionAudio().catch(showError);
  applyQuestionView();
  renderSwitcherList();

  showView("view-session");
  Router.replace(`#/session/${sessionId}`);
  if (state.currentQuestionId) document.getElementById(`q-card-${state.currentQuestionId}`)?.scrollIntoView();
  if (state.dirtyResponses && sess.status === "IN_PROGRESS") scheduleAutoSave();
}

function applySessionState() {
  const sess = state.activeSession;
  const editable = sess?.status === "IN_PROGRESS" && !state.submitting;
  if (!editable) $$("#session-audio audio").forEach((player) => player.pause());
  $$("#question-container input, #question-container select, #question-container .essay-textarea")
    .forEach((x) => { x.disabled = !editable; });
  const live = sess && ["IN_PROGRESS", "PAUSED"].includes(sess.status);
  $("#btn-pause").hidden = !sess || sess.mode === "MOCK" || !live;
  $("#btn-pause").textContent = sess?.status === "PAUSED" ? "继续作答" : "暂停";
  $("#btn-abandon").hidden = !live;
  $("#btn-submit").disabled = !live || state.submitting;
  $("#workspace-state").textContent =
    sess?.status === "PAUSED" ? "已暂停，继续后才能作答"
    : sess?.status === "SUBMITTED" ? "已交卷，本次答卷只读" : "";
  setupTimer(sess?.status === "IN_PROGRESS" ? sess.deadline : null, sess?.serverTime);
  if (!state.dirtyResponses) setSaveStatus("已保存", "saved");
}

function renderPalette() {
  const palette = $("#question-palette");
  palette.replaceChildren();
  state.activeQuestions.forEach(({ question }, idx) => {
    const btn = el("button", "palette-btn", question.printedLabel || `第${idx + 1}题`);
    btn.type = "button";
    btn.dataset.qid = question.questionId;
    btn.id = `palette-btn-${question.questionId}`;
    btn.addEventListener("click", () => {
      const card = $(`#q-card-${question.questionId}`);
      state.currentQuestionId = question.questionId;
      persistDraft();
      applyQuestionView();
      if (card) card.scrollIntoView({ behavior: "smooth", block: "center" });
      saveProgress().catch(showError);
    });
    palette.append(btn);
  });
}

function updatePaletteStatus(questionId) {
  const btn = $(`#palette-btn-${questionId}`);
  if (!btn) return;
  const resp = state.responses[questionId];
  const isAnswered = resp && (
    (resp.type === "SINGLE_CHOICE" && resp.optionKey) ||
    (resp.type === "DIGIT_GRID" && resp.tokens && Object.keys(resp.tokens).length > 0) ||
    (resp.type === "ESSAY" && resp.text && resp.text.trim().length > 0));
  btn.classList.toggle("answered", Boolean(isAnswered));
  btn.classList.toggle("bookmarked", state.flags.has(questionId));
  btn.classList.toggle("active", questionId === state.currentQuestionId);
}

function getQuestionMaterials(group, question) {
  if (!group?.materials || !group.materials.length) return { specific: [], shared: [] };
  const allRefs = new Set();
  for (const q of group.questions || []) for (const ref of q.materialRefs || []) allRefs.add(ref);
  const qRefs = new Set(question.materialRefs || []);
  return {
    specific: group.materials.filter((m) => qRefs.has(m.materialId) || qRefs.has(m.localKey)),
    shared: group.materials.filter((m) => !allRefs.has(m.materialId) && !allRefs.has(m.localKey)),
  };
}

function renderQuestionsWorkspace() {
  const mediaBase = `/api/v1/sessions/${state.activeSession.sessionId}/media/`;
  const container = $("#question-container");
  container.replaceChildren();

  const isSplit = state.layoutMode === "SPLIT";
  let currentGroupKey = "";

  state.activeQuestions.forEach(({ form, group, question }) => {
    const groupKey = `${form.formCode}_${group.groupCode}`;
    const { specific: specificMats, shared: sharedMats } = getQuestionMaterials(group, question);

    if (groupKey !== currentGroupKey) {
      currentGroupKey = groupKey;
      for (const mat of sharedMats) {
        const matBox = el("div", "material-box group-shared-material");
        matBox.dataset.groupKey = groupKey;
        matBox.append(el("div", "material-title",
          `阅读材料 · ${I18N.translateShortForm(form.formCode)}（第 ${group.groupCode} 大题通用）`));
        matBox.append(renderAst(mat.contentAst, mediaBase));
        container.append(matBox);
      }
    }

    const card = el("article", "question-card");
    card.id = `q-card-${question.questionId}`;
    card.dataset.groupKey = groupKey;

    const stemHasFig = astHasFigure(question.stemAst);
    const hasVisuals = specificMats.length > 0 || stemHasFig;

    const head = el("div", "q-header");
    head.append(el("span", "q-label",
      `${I18N.translateShortForm(form.formCode)} · ${question.printedLabel || question.localKey}`));

    const actions = el("div", "q-actions");
    const flagBtn = el("button", "icon-btn", state.flags.has(question.questionId) ? "取消存疑" : "标记存疑");
    flagBtn.type = "button";
    flagBtn.classList.toggle("active", state.flags.has(question.questionId));
    flagBtn.addEventListener("click", () => {
      if (state.flags.has(question.questionId)) state.flags.delete(question.questionId);
      else state.flags.add(question.questionId);
      flagBtn.textContent = state.flags.has(question.questionId) ? "取消存疑" : "标记存疑";
      flagBtn.classList.toggle("active", state.flags.has(question.questionId));
      updatePaletteStatus(question.questionId);
      persistDraft();
      saveProgress().catch(showError);
    });
    actions.append(flagBtn);
    const bmBtn = el("button", "icon-btn", state.bookmarks.has(question.questionId) ? "★ 已收藏" : "☆ 收藏");
    bmBtn.type = "button";
    bmBtn.classList.toggle("active", state.bookmarks.has(question.questionId));
    bmBtn.addEventListener("click", () => toggleBookmark(question.questionId, bmBtn).catch(showError));
    actions.append(bmBtn);
    head.append(actions);

    const answerContainer = el("div", "q-answer-section");
    const type = question.answerSpec?.type;
    if (type === "SINGLE_CHOICE") {
      const optsGroup = el("div", "options-group");
      for (const opt of question.options || []) {
        const item = el("label", "option-item");
        const radio = document.createElement("input");
        radio.type = "radio";
        radio.name = `q_${question.questionId}`;
        radio.value = opt.key;
        radio.checked = state.responses[question.questionId]?.optionKey === opt.key;
        item.classList.toggle("selected", radio.checked);
        radio.addEventListener("change", () => {
          optsGroup.querySelectorAll(".option-item").forEach((it) => it.classList.remove("selected"));
          item.classList.add("selected");
          recordResponse(question.questionId, { type: "SINGLE_CHOICE", optionKey: opt.key });
        });
        item.append(radio, el("span", "opt-circle", opt.key));
        const contentSpan = el("span", "opt-text");
        contentSpan.append(renderAst(opt.contentAst, mediaBase));
        item.append(contentSpan);
        optsGroup.append(item);
      }
      answerContainer.append(optsGroup);
    } else if (type === "DIGIT_GRID") {
      const gridPanel = el("div", "digit-grid-panel");
      const slots = question.answerSpec.slots || [];
      const currentTokens = { ...(state.responses[question.questionId]?.tokens || {}) };
      for (const slot of slots) {
        const slotBox = el("div", "slot-box");
        slotBox.append(el("span", "slot-label", `[${slot}] 栏`));
        const sel = el("select", "slot-select");
        for (const tok of ["", "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]) {
          const opt = document.createElement("option");
          opt.value = tok;
          opt.textContent = tok || "·";
          sel.append(opt);
        }
        sel.setAttribute("aria-label", `${question.printedLabel || question.localKey} 第 ${slot} 格`);
        sel.value = currentTokens[slot] || "";
        sel.addEventListener("change", () => {
          if (sel.value) currentTokens[slot] = sel.value; else delete currentTokens[slot];
          recordResponse(question.questionId, { type: "DIGIT_GRID", tokens: { ...currentTokens } });
        });
        slotBox.append(sel);
        gridPanel.append(slotBox);
      }
      answerContainer.append(gridPanel);
    } else if (type === "ESSAY") {
      const essayBox = el("div", "essay-box");
      const textarea = el("textarea", "essay-textarea");
      textarea.placeholder = "请在此输入日文记述文章……（系统支持字数实时自动统计）";
      textarea.value = state.responses[question.questionId]?.text || "";
      const counter = el("div", "essay-counter", `当前字数：${[...textarea.value].length} 字`);
      textarea.addEventListener("input", () => {
        counter.textContent = `当前字数：${[...textarea.value].length} 字`;
        recordResponse(question.questionId, { type: "ESSAY", text: textarea.value });
      });
      essayBox.append(textarea, counter);
      answerContainer.append(essayBox);
    }

    const noteEditor = createNoteEditor(question.questionId);
    const issueBtn = reportIssueButton(question);

    if (isSplit && hasVisuals) {
      card.classList.add("layout-split");
      const splitWrapper = el("div", "q-split-wrapper");
      const mediaCol = el("div", "q-split-media");
      for (const mat of specificMats) {
        const matBox = el("div", "material-box embedded-material");
        matBox.append(el("div", "material-title",
          `本题材料 / 配图 · ${I18N.translateShortForm(form.formCode)}（第 ${group.groupCode} 大题）`));
        matBox.append(renderAst(mat.contentAst, mediaBase));
        mediaCol.append(matBox);
      }
      let stemContentNodes = question.stemAst;
      if (stemHasFig) {
        const { figures, nonFigures } = astExtractFigures(question.stemAst);
        for (const fig of figures) mediaCol.append(renderAst([fig], mediaBase));
        stemContentNodes = nonFigures;
      }
      splitWrapper.append(mediaCol);

      const contentCol = el("div", "q-split-content");
      contentCol.append(head);
      if (stemContentNodes && stemContentNodes.length) {
        const stem = el("div", "q-stem");
        stem.append(renderAst(stemContentNodes, mediaBase));
        contentCol.append(stem);
      }
      contentCol.append(answerContainer, noteEditor);
      if (issueBtn) contentCol.append(issueBtn);
      splitWrapper.append(contentCol);
      card.append(splitWrapper);
    } else {
      card.append(head);
      for (const mat of specificMats) {
        const matBox = el("div", "material-box embedded-material");
        matBox.append(el("div", "material-title",
          `本题材料 / 配图 · ${I18N.translateShortForm(form.formCode)}（第 ${group.groupCode} 大题）`));
        matBox.append(renderAst(mat.contentAst, mediaBase));
        card.append(matBox);
      }
      const stem = el("div", "q-stem");
      stem.append(renderAst(question.stemAst, mediaBase));
      card.append(stem, answerContainer, noteEditor);
      if (issueBtn) card.append(issueBtn);
    }
    container.append(card);
  });
}

function reportIssueButton(q) {
  return actionButton("报告内容问题", async () => {
    const description = prompt("请说明具体问题（至少 5 字）。不要在未交卷时填写推测答案。");
    if (!description) return;
    const issueType = prompt("问题类型：TEXT / ANSWER / FIGURE / AUDIO / OTHER", "TEXT");
    if (!issueType) return;
    await api("/api/v1/content-issues", {
      method: "POST",
      body: JSON.stringify({
        questionId: q.questionId, questionVersionId: q.questionVersionId,
        paperVersionId: q.sourcePaperVersionId || state.activeSession?.paperVersionId,
        sessionId: state.activeSession?.sessionId, description, issueType,
      }),
    });
    showNotice("问题已登记，可在制作台的「内容问题」中查看处理进度。");
  });
}

// ── 保存：四态明确，失败可重试，草稿始终留在本机 ─────────────────────────
const SAVE_CLASSES = ["is-saved", "is-saving", "is-dirty", "is-failed"];

function setSaveStatus(text, kind) {
  const node = $("#save-status");
  node.textContent = `● ${text}`;
  node.classList.remove(...SAVE_CLASSES);
  node.classList.add(`is-${kind}`);
}

function getDraftKey(sid) {
  return `eju.draft.${state.libraryInstanceId || "default"}.${sid}`;
}

function readDraft(sid) {
  try { return JSON.parse(localStorage.getItem(getDraftKey(sid)) || "null"); }
  catch { return null; }
}

function progressSnapshot() {
  return {
    currentQuestionId: state.currentQuestionId,
    flaggedQuestionIds: [...state.flags],
    viewMode: state.viewMode,
  };
}

function persistDraft() {
  if (!state.activeSession) return;
  try {
    localStorage.setItem(getDraftKey(state.activeSession.sessionId), JSON.stringify({
      baseResponses: state.baseResponses, baseVersion: state.baseVersion,
      pendingResponses: state.pendingResponses, nextEdit: state.nextEdit,
      saveRequest: state.saveRequest, responseVersion: state.activeSession.responseVersion,
      progress: progressSnapshot(), savedAt: new Date().toISOString(),
    }));
  } catch {
    showError(new Error("本地草稿空间不足，请保持页面打开并确认服务器保存成功。"));
  }
}

async function saveProgress() {
  if (state.activeSession?.status !== "IN_PROGRESS") return;
  if (state.progressSaving) return state.progressSaving;
  const sid = state.activeSession.sessionId;
  state.progressSaving = (async () => {
    try {
      const saved = await api(`/api/v1/sessions/${sid}/progress`, {
        method: "PUT",
        body: JSON.stringify({
          ...progressSnapshot(),
          expectedProgressVersion: state.activeSession.progressVersion || 0,
        }),
      });
      if (state.activeSession?.sessionId === sid) state.activeSession.progressVersion = saved.progressVersion;
    } catch (error) {
      if (error.status === 409) {
        const remote = await api(`/api/v1/sessions/${sid}`);
        if (state.activeSession?.sessionId === sid) {
          state.activeSession.progressVersion = remote.session.progressVersion;
        }
        throw new Error("另一页面更新了作答位置；当前本机位置已保留，下次操作将重新保存。");
      }
      throw error;
    } finally { state.progressSaving = null; }
  })();
  return state.progressSaving;
}

function recordResponse(questionId, responseObj) {
  if (state.activeSession?.status !== "IN_PROGRESS" || state.submitting) return;
  state.responses[questionId] = responseObj;
  state.pendingResponses[questionId] = { response: responseObj, edit: ++state.nextEdit };
  state.currentQuestionId = questionId;
  updatePaletteStatus(questionId);
  applyQuestionView();
  persistDraft();
  scheduleAutoSave();
}

function scheduleAutoSave() {
  state.dirtyResponses = Object.keys(state.pendingResponses).length > 0;
  setSaveStatus("待保存（已保留本机草稿）", "dirty");
  clearTimeout(state.autoSaveTimer);
  state.autoSaveTimer = setTimeout(() => flushAutoSave().catch(() => {}), 700);
}

async function reconcileConflict(sid) {
  setSaveStatus("检测到保存冲突，正在同步……", "saving");
  const generation = state.sessionGeneration;
  const { session: remoteSession } = await api(`/api/v1/sessions/${sid}`);
  if (generation !== state.sessionGeneration || sid !== state.activeSession?.sessionId) return;
  if (remoteSession.status !== "IN_PROGRESS") {
    state.activeSession = remoteSession;
    applySessionState();
    throw new Error("会话已暂停或交卷，本机草稿保留供核对。");
  }
  const remoteResponses = Object.fromEntries(
    Object.entries(remoteSession.responses || {}).map(([q, v]) => [q, v.value]));
  const remoteVersion = remoteSession.responseVersion;

  const conflicts = [];
  for (const [qid, entry] of Object.entries(state.pendingResponses)) {
    const localVal = JSON.stringify(entry.response);
    const baseVal = JSON.stringify(state.baseResponses[qid] ?? null);
    const remoteVal = JSON.stringify(remoteResponses[qid] ?? null);
    if (remoteVal === baseVal) {
      // 远端没动过这题：保留本机待保存的编辑
    } else if (remoteVal === localVal) {
      delete state.pendingResponses[qid];
      state.responses[qid] = entry.response;
    } else {
      conflicts.push({ qid, localVal: entry.response, remoteVal: remoteResponses[qid] });
    }
  }

  for (const conf of conflicts) {
    const qObj = state.activeQuestions.find((x) => x.question.questionId === conf.qid)?.question;
    const label = qObj?.printedLabel || conf.qid;
    const keepLocal = confirm(
      `检测到保存冲突：题目 ${label} 在其他页面已被修改。\n\n点击“确定”保留当前页面的修改，点击“取消”接受其他页面的修改。`);
    if (!keepLocal) {
      delete state.pendingResponses[conf.qid];
      if (conf.remoteVal !== undefined) state.responses[conf.qid] = conf.remoteVal;
      else delete state.responses[conf.qid];
      updatePaletteStatus(conf.qid);
    }
  }

  state.responses = {
    ...remoteResponses,
    ...Object.fromEntries(Object.entries(state.pendingResponses).map(([qid, e]) => [qid, e.response])),
  };
  renderQuestionsWorkspace();
  renderPalette();
  applyQuestionView();
  state.baseResponses = remoteResponses;
  state.baseVersion = remoteVersion;
  state.activeSession.responseVersion = remoteVersion;
  state.saveRequest = null;
  persistDraft();
}

async function flushAutoSave() {
  if (state.saving) return state.saving;
  if (!state.activeSession || !Object.keys(state.pendingResponses).length) return;
  const sid = state.activeSession.sessionId;
  const generation = state.sessionGeneration;
  state.saving = (async () => {
    try {
      while (Object.keys(state.pendingResponses).length) {
        if (generation !== state.sessionGeneration || state.activeSession?.sessionId !== sid) return;
        if (!state.saveRequest) {
          state.saveRequest = {
            requestId: crypto.randomUUID(),
            expectedVersion: state.activeSession.responseVersion,
            items: Object.entries(state.pendingResponses)
              .map(([questionId, entry]) => ({ questionId, response: entry.response })),
            edits: Object.fromEntries(
              Object.entries(state.pendingResponses).map(([qid, entry]) => [qid, entry.edit])),
          };
          persistDraft();
        }
        const batch = state.saveRequest;
        setSaveStatus("正在保存……", "saving");
        let response;
        try {
          response = await api(`/api/v1/sessions/${sid}/responses:batch`, {
            method: "POST", body: JSON.stringify(batch),
          });
        } catch (error) {
          if (error?.status === 409 || error?.code === "SESSION_CONFLICT") {
            await reconcileConflict(sid);
            continue;
          }
          throw error;
        }
        if (generation !== state.sessionGeneration || state.activeSession?.sessionId !== sid) return;
        for (const [qid, edit] of Object.entries(batch.edits)) {
          state.baseResponses[qid] = batch.items.find((i) => i.questionId === qid)?.response;
          if (state.pendingResponses[qid]?.edit === edit) delete state.pendingResponses[qid];
        }
        state.baseVersion = response.responseVersion;
        state.activeSession.responseVersion = response.responseVersion;
        state.saveRequest = null;
        state.dirtyResponses = Object.keys(state.pendingResponses).length > 0;
        persistDraft();
        sessionSyncChannel?.postMessage({
          type: "session_saved", libraryInstanceId: state.libraryInstanceId,
          sessionId: sid, responseVersion: response.responseVersion,
        });
      }
      setSaveStatus("已保存", "saved");
    } catch (error) {
      state.dirtyResponses = true;
      setSaveStatus("保存失败，点击重试；草稿已保留", "failed");
      showError(error);
      throw error;
    } finally { state.saving = null; }
  })();
  return state.saving;
}

$("#save-status").addEventListener("click", () => flushAutoSave().catch(showError));
window.addEventListener("beforeunload", (event) => {
  persistDraft();
  if (state.dirtyResponses) { event.preventDefault(); event.returnValue = ""; }
});
window.addEventListener("online", () => flushAutoSave().catch(showError));
setInterval(() => {
  if (!document.hidden && state.currentView === "view-session") saveProgress().catch(() => {});
}, 20000);

// ── 计时 ─────────────────────────────────────────────────────────────────
function setupTimer(deadlineStr, serverTime) {
  clearInterval(state.timerInterval);
  $("#timer-box").hidden = !deadlineStr;
  if (!deadlineStr) return;
  const remaining = new Date(deadlineStr).getTime()
    - new Date(serverTime || Date.now()).getTime()
    - (performance.now() - (state.activeSession.receivedAt || performance.now()));
  const start = performance.now();
  const tick = () => {
    const seconds = Math.max(0, Math.ceil((remaining - (performance.now() - start)) / 1000));
    $("#timer-display").textContent =
      `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
    if (seconds === 0) { clearInterval(state.timerInterval); submitExam(true).catch(showError); }
  };
  state.timerInterval = setInterval(tick, 1000);
  tick();
}

// ── 阅读设置浮层与答题卡抽屉 ─────────────────────────────────────────────
function questionComplete(q) {
  const r = state.responses[q.questionId];
  if (q.answerSpec.type === "SINGLE_CHOICE") return !!r?.optionKey;
  if (q.answerSpec.type === "DIGIT_GRID") return q.answerSpec.slots.every((slot) => !!r?.tokens?.[slot]);
  return !!r?.text?.trim();
}

function applyQuestionView() {
  const mode = state.viewMode || "ALL";
  $("#question-view").value = mode;
  if (!state.currentQuestionId) state.currentQuestionId = state.activeQuestions[0]?.question.questionId;
  const currentObj = state.activeQuestions.find((x) => x.question.questionId === state.currentQuestionId);
  const currentGroupKey = currentObj ? `${currentObj.form.formCode}_${currentObj.group.groupCode}` : "";

  for (const { question: q } of state.activeQuestions) {
    const card = document.getElementById(`q-card-${q.questionId}`);
    if (!card) continue;
    card.hidden =
      mode === "SINGLE" ? q.questionId !== state.currentQuestionId
      : mode === "UNANSWERED" ? questionComplete(q)
      : mode === "FLAGGED" ? !state.flags.has(q.questionId)
      : false;
  }
  // 单题模式下，只留当前大题的通用材料，其余收起。
  $$(".group-shared-material").forEach((box) => {
    box.hidden = mode === "SINGLE" && box.dataset.groupKey !== currentGroupKey;
  });
  for (const { question } of state.activeQuestions) updatePaletteStatus(question.questionId);
  const done = state.activeQuestions.filter((x) => questionComplete(x.question)).length;
  $("#question-progress").textContent = `已答 ${done} / ${state.activeQuestions.length}`;
}

$("#question-view").addEventListener("change", () => {
  state.viewMode = $("#question-view").value;
  applyQuestionView();
  persistDraft();
  saveProgress().catch(showError);
});

const layoutSelect = $("#question-layout");
layoutSelect.value = state.layoutMode || "SPLIT";
layoutSelect.addEventListener("change", () => {
  state.layoutMode = layoutSelect.value;
  localStorage.setItem("eju.layoutMode", state.layoutMode);
  if (state.activeSession) {
    renderQuestionsWorkspace();
    applyQuestionView();
    if (state.currentQuestionId) document.getElementById(`q-card-${state.currentQuestionId}`)?.scrollIntoView();
  }
  if (lastResult) renderReviewList(lastResult, currentReviewFilter());
});

const readingSize = $("#reading-size");
readingSize.value = localStorage.getItem("eju.readingSize") || 18;
$("#question-container").style.fontSize = `${readingSize.value}px`;
readingSize.addEventListener("input", () => {
  $("#question-container").style.fontSize = `${readingSize.value}px`;
  localStorage.setItem("eju.readingSize", readingSize.value);
});

for (const [id, delta] of [["question-prev", -1], ["question-next", 1]]) {
  $(`#${id}`).addEventListener("click", () => {
    const pos = state.activeQuestions.findIndex((x) => x.question.questionId === state.currentQuestionId);
    const next = state.activeQuestions[Math.max(0, Math.min(state.activeQuestions.length - 1, pos + delta))];
    if (!next) return;
    state.currentQuestionId = next.question.questionId;
    applyQuestionView();
    document.getElementById(`q-card-${state.currentQuestionId}`)?.scrollIntoView();
    persistDraft();
    saveProgress().catch(showError);
  });
}

/* 一组「点按钮开合、点外面关掉、Esc 关掉」的浮层。阅读设置、答题卡、
   卷子切换共用同一套行为。 */
function bindPopover(buttonId, panelId, { onOpen } = {}) {
  const button = $(`#${buttonId}`), panel = $(`#${panelId}`);
  const setOpen = (open) => {
    panel.hidden = !open;
    button.setAttribute("aria-expanded", String(open));
    if (open) onOpen?.();
  };
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    setOpen(panel.hidden);
  });
  document.addEventListener("click", (event) => {
    if (!panel.hidden && !panel.contains(event.target) && !button.contains(event.target)) setOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) setOpen(false);
  });
  return setOpen;
}

bindPopover("reading-settings-button", "reading-settings");

const setSheetOpen = bindPopover("answer-sheet-button", "answer-sheet");
$("#answer-sheet-close").addEventListener("click", () => setSheetOpen(false));
new MutationObserver(() => {
  $(".session-body").classList.toggle("sheet-open", !$("#answer-sheet").hidden);
}).observe($("#answer-sheet"), { attributes: true, attributeFilter: ["hidden"] });

const setSwitcherOpen = bindPopover("switcher-button", "switcher-menu");
function closeSwitcher() { setSwitcherOpen(false); }
$("#switcher-close").addEventListener("click", closeSwitcher);
$("#switcher-more").addEventListener("click", closeSwitcher);

/* 作答中换卷：浮层里直接列出别的卷，当前这道题留在原处不动。 */
function renderSwitcherList() {
  const list = $("#switcher-list");
  list.replaceChildren();
  for (const paper of state.papers.filter(paperIsOpen)) {
    const item = el("button", "switcher-item");
    item.type = "button";
    const isCurrent = paper.paperId === state.activePaper?.paperId;
    if (isCurrent) item.setAttribute("aria-current", "true");
    item.append(
      el("strong", "", I18N.translatePaperTitle(paper.title)),
      el("small", "", `${paper.session || "留考"} · ${paper.questionCount || 0} 题`),
    );
    item.addEventListener("click", () => {
      closeSwitcher();
      Router.go(`#/paper/${paper.paperId}`);
    });
    list.append(item);
  }
  if (!list.children.length) list.append(el("p", "subtitle", "没有其他可练的卷子。"));
}

// ── 暂停、退出、交卷 ─────────────────────────────────────────────────────
$("#btn-pause").addEventListener("click", act(async () => {
  const sid = state.activeSession?.sessionId;
  if (!sid) return;
  const action = state.activeSession.status === "PAUSED" ? "resume" : "pause";
  // 暂停前先落盘，避免暂停后输入被禁用而丢掉最后一次编辑。
  if (action === "pause") { await flushAutoSave(); await saveProgress(); }
  state.activeSession = await api(`/api/v1/sessions/${sid}:${action}`, { method: "POST", body: "{}" });
  state.activeSession.receivedAt = performance.now();
  applySessionState();
}));

$("#btn-exit").addEventListener("click", act(async () => {
  if (state.activeSession && ["IN_PROGRESS", "PAUSED"].includes(state.activeSession.status)) {
    await flushAutoSave();
    await saveProgress();
    showNotice("作答已保存，可以随时从入口页或历史记录继续。");
  }
  Router.go(subjectHash(""));
}));

$("#btn-abandon").addEventListener("click", act(async () => {
  const sess = state.activeSession;
  if (!sess) return;
  if (!confirm("确定要放弃本次作答吗？所有作答将被放弃且不可恢复。")) return;
  await api(`/api/v1/sessions/${sess.sessionId}:abandon`, { method: "POST", body: "{}" });
  localStorage.removeItem(`eju.activeSession.${state.libraryInstanceId}`);
  localStorage.removeItem(getDraftKey(sess.sessionId));
  state.activeSession = null;
  Router.go(subjectHash(""));
}));

$("#btn-submit").addEventListener("click", () => {
  const missing = state.activeQuestions.filter(({ question: q }) => !questionComplete(q));
  if (confirm(`还有 ${missing.length} 题未完成。确认交卷吗？交卷后本次答案将锁定。`)) {
    submitExam().catch(showError);
  }
});

async function submitExam(expired = false) {
  if (!state.activeSession || state.submitting || state.activeSession.status === "SUBMITTED") return;
  state.submitting = true;
  clearInterval(state.timerInterval);
  $$("#question-container input, #question-container select, #question-container .essay-textarea")
    .forEach((x) => { x.disabled = true; });
  $("#btn-submit").disabled = true;
  try {
    if (state.activeSession.status === "PAUSED") {
      state.activeSession = await api(`/api/v1/sessions/${state.activeSession.sessionId}:resume`,
        { method: "POST", body: "{}" });
    }
    if (expired) {
      try { await flushAutoSave(); }
      catch {
        showError(new Error("考试已到时，将以截止前服务器确认的答案交卷。本机未保存草稿保留供核对。"));
      }
    } else {
      await flushAutoSave();
    }
    const sid = state.activeSession.sessionId;
    const body = expired ? {} : { expectedResponseVersion: state.activeSession.responseVersion };
    await api(`/api/v1/sessions/${sid}:submit`, { method: "POST", body: JSON.stringify(body) });
    state.activeSession.status = "SUBMITTED";
    sessionSyncChannel?.postMessage({
      type: "session_submitted", sessionId: sid, libraryInstanceId: state.libraryInstanceId,
    });
    localStorage.removeItem(`eju.activeSession.${state.libraryInstanceId}`);
    if (!state.dirtyResponses) localStorage.removeItem(getDraftKey(sid));
    await openResult(sid);
  } finally {
    state.submitting = false;
    applySessionState();
  }
}

// ── L7：成绩与逐题复盘 ───────────────────────────────────────────────────
let lastResult = null;

function currentReviewFilter() {
  return $('input[name="review-filter"]:checked')?.value || "ALL";
}

async function openResult(sid) {
  const { result } = await api(`/api/v1/sessions/${sid}/result`);
  displayResult(result);
  await loadResultExtras(result);
}

function displayResult(result) {
  state.renderSessionId = result.sessionId;
  lastResult = result;
  $("#res-paper-title").textContent = I18N.translatePaperTitle(result.paperTitle || "作答结果");
  $("#res-accuracy").textContent =
    result.objectiveAccuracy === null ? "待评阅" : `${Math.round(result.objectiveAccuracy * 100)}%`;
  $("#res-correct").textContent = result.objectiveCorrect || 0;
  $("#res-total").textContent = result.objectiveTotal || 0;
  $("#res-detail").textContent =
    `已答 ${result.objectiveAnswered} · 未答 ${result.objectiveUnanswered} · 答错 ${result.objectiveWrong}` +
    ` · 记述待评阅 ${result.essayPending} · 记述未答 ${result.essayUnanswered || 0}` +
    (result.previousScoringVersion ? "；历史结果按新版统计口径展示，原始结果已保留。" : "");

  const perFormBox = $("#res-per-form");
  perFormBox.replaceChildren();
  for (const [form, stats] of Object.entries(result.perForm || {})) {
    perFormBox.append(el("span", "form-stat-pill",
      `${I18N.translateShortForm(form)}：${stats.correct} / ${stats.objective} 题正确`));
  }
  $('input[name="review-filter"][value="ALL"]').checked = true;
  renderReviewList(result, "ALL");
  showView("view-result");
  Router.replace(`#/result/${result.sessionId}`);
}

function renderReviewList(result, filter) {
  const mediaBase = `/api/v1/sessions/${result.sessionId}/media/`;
  const container = $("#review-list");
  container.replaceChildren();
  const isSplit = state.layoutMode === "SPLIT";

  for (const row of result.questions || []) {
    const status =
      ["PENDING_REVIEW", "ANSWERED_PENDING_REVIEW"].includes(row.status) ? "PENDING"
      : ["UNANSWERED", "EMPTY"].includes(row.status) ? "UNANSWERED"
      : row.correct ? "CORRECT" : "WRONG";
    if (filter !== "ALL" && filter !== status) continue;

    const q = row.question;
    const item = el("article", `review-item ${status.toLowerCase()}`);
    const title = el("h4", "", `${I18N.translateShortForm(row.formCode)} · ${q?.printedLabel || row.questionId}`);

    const hasMats = Boolean(row.materials && row.materials.length);
    const stemHasFig = Boolean(q && astHasFigure(q.stemAst));
    const hasVisuals = hasMats || stemHasFig;

    const contentBox = el("div", "review-main-content");
    if (q) {
      let stemNodes = q.stemAst;
      if (isSplit && stemHasFig) stemNodes = astExtractFigures(q.stemAst).nonFigures;
      if (stemNodes && stemNodes.length) contentBox.append(renderAst(stemNodes, mediaBase));
      for (const option of q.options || []) {
        const opt = el("div", "review-option", `${option.key}. `);
        opt.append(renderAst(option.contentAst, mediaBase));
        contentBox.append(opt);
      }
    }
    const labels = { PENDING: "记述待评阅", UNANSWERED: "未作答", CORRECT: "回答正确", WRONG: "回答错误" };
    contentBox.append(el("p", "", labels[status]), el("p", "", `你的作答：${formatResponse(row.response)}`));
    if (q?.answerSpec?.type === "ESSAY") {
      contentBox.append(el("pre", "essay-review", row.response?.text || "未提交记述内容"));
    } else if (q?.correctAnswer) {
      contentBox.append(el("p", "correct-key",
        `正确答案：${formatResponse({ type: q.answerSpec.type, ...q.correctAnswer })}`));
    }
    if (row.slotResults) {
      contentBox.append(el("p", "", Object.entries(row.slotResults)
        .map(([slot, ok]) => `${slot}：${ok ? "正确" : row.response?.tokens?.[slot] ? "错误" : "漏填"}`)
        .join("；")));
    }
    if (q?.explanationStatus === "REVIEWED" && q.explanationAst) {
      contentBox.append(renderAst(q.explanationAst, mediaBase));
    } else {
      contentBox.append(el("p", "subtitle", "暂无已复核解析"));
    }
    contentBox.append(createNoteEditor(row.questionId));

    if (isSplit && hasVisuals) {
      item.classList.add("layout-split");
      item.append(title);
      const splitWrapper = el("div", "q-split-wrapper");
      const mediaCol = el("div", "q-split-media");
      for (const material of row.materials || []) {
        const mBox = el("div", "material-box embedded-material");
        mBox.append(el("div", "material-title", "本题材料 / 配图"));
        mBox.append(renderAst(material.contentAst, mediaBase));
        mediaCol.append(mBox);
      }
      if (stemHasFig) {
        for (const fig of astExtractFigures(q.stemAst).figures) mediaCol.append(renderAst([fig], mediaBase));
      }
      splitWrapper.append(mediaCol, contentBox);
      item.append(splitWrapper);
    } else {
      item.append(title);
      for (const material of row.materials || []) {
        const mBox = el("div", "material-box embedded-material");
        mBox.append(renderAst(material.contentAst, mediaBase));
        item.append(mBox);
      }
      if (!isSplit && stemHasFig && q) item.append(renderAst(q.stemAst, mediaBase));
      item.append(contentBox);
    }
    container.append(item);
  }
}

function formatResponse(resp) {
  if (!resp) return "未作答";
  if (resp.type === "SINGLE_CHOICE") return `选项 ${resp.optionKey || "未选"}`;
  if (resp.type === "DIGIT_GRID") {
    return Object.entries(resp.tokens || {}).map(([s, t]) => `[${s}]=${t}`).join("，");
  }
  if (resp.type === "ESSAY") return `记述作答（已写 ${resp.text?.length || 0} 字）`;
  return "已作答";
}

$$('input[name="review-filter"]').forEach((r) => {
  r.addEventListener("change", (e) => { if (lastResult) renderReviewList(lastResult, e.target.value); });
});
$("#btn-restart-exam").addEventListener("click", () => {
  if (lastResult) Router.go(`#/paper/${lastResult.paperId}`);
});
$("#btn-retry-wrong").addEventListener("click", act(async () => {
  const ids = (lastResult?.questions || [])
    .filter((q) => q.answered && q.correct === false).map((q) => q.questionId);
  if (!ids.length) throw new Error("本次没有需要重练的错题");
  await startCollection(ids);
}));
$("#btn-export-result").addEventListener("click", () => window.print());

async function loadResultExtras(result) {
  const box = $("#result-extras");
  box.replaceChildren();
  const sid = result.sessionId;
  for (const suffix of ["export", "export.csv"]) {
    const a = el("a", "btn btn-outline", suffix.endsWith("csv") ? "下载统计 CSV" : "下载统计 JSON");
    a.href = `/api/v1/sessions/${sid}/${suffix}`;
    a.download = `learning-report${suffix.endsWith("csv") ? ".csv" : ".json"}`;
    box.append(a);
  }
  const content = await api(`/api/v1/sessions/${sid}/review-content`);
  if (lastResult?.sessionId !== sid) return;
  for (const item of content.items) {
    const section = el("section");
    section.append(el("p", "", `${item.questionId} · ${item.status}`));
    if (item.content) section.append(renderAst(item.content.contentAst, `/api/v1/sessions/${sid}/media/`));
    box.append(section);
  }

  const essays = result.questions.filter((x) => x.question?.answerSpec?.type === "ESSAY");
  if (!essays.length) return;
  const [{ rubrics }, { assessments }] = await Promise.all([
    api("/api/v1/rubrics"), api(`/api/v1/sessions/${sid}/assessments`),
  ]);
  if (lastResult?.sessionId !== sid) return;

  for (const essay of essays) {
    const panel = el("section", "paper-card");
    panel.append(
      el("h3", "", `记述 ${essay.question.printedLabel || ""}`),
      el("p", "", essay.response?.text || "未提交正文"),
    );
    for (const previous of assessments.filter((x) => x.questionId === essay.questionId)) {
      panel.append(el("p", "",
        `${previous.kind === "SELF" ? "自评" : "人工评阅"} 第 ${previous.revision} 版：${previous.assessment.comment || ""}`));
    }
    if (essay.response?.text?.trim() && rubrics.length) {
      const select = el("select");
      for (const r of rubrics) {
        const o = el("option", "", r.name);
        o.value = r.rubricRevisionId;
        select.append(o);
      }
      const fields = el("div");
      const draw = () => {
        fields.replaceChildren();
        for (const d of rubrics.find((r) => r.rubricRevisionId === select.value).dimensions) {
          const label = el("label", "", d.name || d.id);
          const input = el("select");
          input.dataset.dimension = d.id;
          for (const level of d.levels) input.append(el("option", "", level));
          label.append(input);
          fields.append(label);
        }
      };
      select.addEventListener("change", draw);
      draw();
      const comment = el("textarea");
      comment.placeholder = "评阅意见";
      const save = async (kind) => {
        const previous = assessments.filter((x) => x.questionId === essay.questionId && x.kind === kind);
        const baseRevision = Math.max(0, ...previous.map((x) => x.revision));
        const body = {
          baseRevision,
          assessment: {
            rubricRevisionId: select.value,
            ratings: Object.fromEntries(
              [...fields.querySelectorAll("select")].map((x) => [x.dataset.dimension, x.value])),
            comment: comment.value,
          },
        };
        if (kind === "HUMAN") {
          body.reviewer = prompt("人工复核人姓名");
          if (!body.reviewer) return;
        }
        await api(kind === "SELF"
          ? `/api/v1/sessions/${sid}/essays/${essay.questionId}/self-assessment`
          : `/api/v1/admin/sessions/${sid}/essays/${essay.questionId}/assessment`,
          { method: "POST", body: JSON.stringify(body) });
        await loadResultExtras(result);
      };
      panel.append(select, fields, comment,
        actionButton("保存自评", () => save("SELF")),
        actionButton("保存人工评阅（需管理凭证）", () => save("HUMAN")));
    }
    box.append(panel);
  }
}

// ── 听力音轨 ─────────────────────────────────────────────────────────────
async function loadSessionAudio() {
  const sid = state.activeSession.sessionId;
  const container = $("#session-audio");
  container.replaceChildren();
  const result = await api(`/api/v1/sessions/${sid}/audio`);
  if (state.activeSession?.sessionId !== sid) return;

  for (const track of result.tracks) {
    let cueEnd = null;
    const player = el("audio");
    player.controls = !track.strict;
    player.preload = "metadata";
    player.src = `/api/v1/sessions/${sid}/media/${track.assetId}`;
    player.setAttribute("aria-label", "听力音频");
    player.addEventListener("loadedmetadata", () => {
      if (track.strict) player.currentTime = (track.positionMs || 0) / 1000;
      else if (result.progress?.track_id === track.trackId) player.currentTime = result.progress.position_ms / 1000;
    });
    player.addEventListener("timeupdate", () => {
      if (cueEnd !== null && player.currentTime >= cueEnd) { player.pause(); cueEnd = null; }
    });
    let last = 0;
    for (const [event, action] of [["play", "PLAY"], ["pause", "PAUSE"], ["seeked", "SEEK"],
                                   ["ended", "ENDED"], ["timeupdate", "PROGRESS"]]) {
      player.addEventListener(event, () => {
        if (track.strict && ["PLAY", "SEEK"].includes(action)) return;
        if (action === "PROGRESS" && Date.now() - last < 5000) return;
        last = Date.now();
        if (state.activeSession?.sessionId === sid && state.activeSession.status === "IN_PROGRESS") {
          api(`/api/v1/sessions/${sid}/audio/progress`, {
            method: "POST",
            body: JSON.stringify({
              trackId: track.trackId,
              positionMs: Math.min(track.durationMs, Math.round(player.currentTime * 1000)),
              action,
            }),
          }).catch(showError);
        }
      });
    }
    player.addEventListener("error", () => showError(new Error("音频加载失败，请检查连接后重试。")));
    container.append(player, actionButton("重试加载", () => player.load()));

    if (track.strict) {
      container.append(
        el("span", "", `严格听力：片段 ${track.cueIndex + 1} / ${track.totalCues}`),
        actionButton(track.playCount ? "继续当前片段" : "开始当前片段", async () => {
          await api(`/api/v1/sessions/${sid}/audio/progress`, {
            method: "POST",
            body: JSON.stringify({
              trackId: track.trackId, positionMs: Math.round(player.currentTime * 1000),
              action: track.playCount ? "RESUME" : "PLAY",
            }),
          });
          await player.play();
          track.playCount = 1;
        }),
        actionButton("进入下一片段", async () => {
          await api(`/api/v1/sessions/${sid}/audio/progress`, {
            method: "POST",
            body: JSON.stringify({
              trackId: track.trackId, positionMs: Math.round(player.currentTime * 1000), action: "ADVANCE",
            }),
          });
          await loadSessionAudio();
        }));
    } else {
      for (const cue of track.cues) {
        container.append(actionButton(`片段 ${cue.cueId}`, () => {
          cueEnd = cue.endMs / 1000;
          player.currentTime = cue.startMs / 1000;
          return player.play();
        }));
      }
    }
  }
}

// ── 路由与启动 ───────────────────────────────────────────────────────────
Router
  .add(/^#\/subject\/([A-Z_]+)\/papers$/, async ([, subject]) => {
    state.subject = subject === "ALL" ? "ALL" : subject;
    renderPaperList();
    showView("view-papers");
    $("#papers-meta").textContent =
      state.subject === "ALL" ? "全部科目的已发布试卷" : `${subjectGroupLabel(state.subject)} · 已发布试卷`;
  })
  .add(/^#\/subject\/([A-Z_]+)\/forms$/, async ([, subject]) => {
    state.subject = subject === "ALL" ? "ALL" : subject;
    state.formFilter = null;
    renderFormList();
    showView("view-forms");
    $("#forms-meta").textContent =
      state.subject === "ALL" ? "全部可练分科" : `${subjectGroupLabel(state.subject)} 下的分科`;
  })
  .add(/^#\/subject\/([A-Z_]+)$/, async ([, subject]) => {
    state.subject = subject === "ALL" ? "ALL" : subject;
    state.formFilter = null;
    renderSubjects();
    showView("view-subjects");
  })
  /* 「我的」里点「去重练 / 去练习」会把题目 ID 放进 sessionStorage 再跳过来，
     这样跨工作区的深链不用把一长串 ID 塞进地址栏。 */
  .add(/^#\/collect(?:\?(.*))?$/, async ([, query]) => {
    showView("view-collect");
    const params = new URLSearchParams(query || "");
    if (params.get("queue")) {
      const raw = sessionStorage.getItem("eju.practiceQueue");
      sessionStorage.removeItem("eju.practiceQueue");
      Router.replace("#/collect");
      let queued = [];
      try { queued = JSON.parse(raw || "[]"); } catch { queued = []; }
      if (queued.length) {
        await loadCollection();
        await startCollection(queued);
        return;
      }
    }
    await loadCollection();
  })
  /* 支持 ?form= 预选分科，以及 ?mode=review&scope=wrong 从「我的」深链进来。 */
  .add(/^#\/paper\/([^?]+)(?:\?(.*))?$/, async ([, paperId, query]) => {
    const params = new URLSearchParams(query || "");
    showView("view-setup");
    await openSetup(decodeURIComponent(paperId), { form: params.get("form") });
    if (params.get("mode") === "review" && params.get("scope") === "wrong") {
      await retryWrongOfPaper(decodeURIComponent(paperId));
    }
  })
  .add(/^#\/session\/([^?]+)$/, async ([, sid]) => {
    if (state.activeSession?.sessionId === decodeURIComponent(sid) &&
        state.currentView === "view-session") return;
    await restoreSession(decodeURIComponent(sid));
  })
  .add(/^#\/result\/([^?]+)$/, async ([, sid]) => {
    if (lastResult?.sessionId === decodeURIComponent(sid) && state.currentView === "view-result") return;
    await openResult(decodeURIComponent(sid));
  })
  .setFallback(async () => {
    state.formFilter = null;
    renderSubjects();
    showView("view-subjects");
  });

/* 「我的」里点某套卷的「重练错题」时走这条：把这套卷做错过的题直接组一份练习。 */
async function retryWrongOfPaper(paperId) {
  const { wrongQuestions } = await api("/api/v1/wrong-questions");
  const ids = wrongQuestions
    .filter((w) => w.paperId === paperId && w.status !== "MASTERED")
    .map((w) => w.questionId);
  if (!ids.length) {
    showNotice("这套卷目前没有待重练的错题。");
    return;
  }
  $("#setup-hint").textContent = `已找到 ${ids.length} 道错题，正在准备重练…`;
  await startCollection(ids);
}

async function boot() {
  await loadLibraryInstanceId();
  try {
    await loadPapers();
  } catch (error) {
    $("#subjects-status").textContent = "无法读取试卷列表。";
    $("#subjects-status").classList.add("is-error");
    showError(error);
  }
  renderSubjects();
  await Router.start();
}

boot().catch(showError);
