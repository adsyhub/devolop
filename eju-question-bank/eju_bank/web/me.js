"use strict";
/* ==========================================================================
   我的学习中心
   --------------------------------------------------------------------------
   四个 panel 共用一个壳：错题集 / 收藏笔记 / 练习记录 / 学习分析。
   这里只汇总记录，不是第三种练法——所有"去练习"都跳回 practice 工作区。
   ========================================================================== */

Object.assign(state, {
  wrongQuestions: [],
  bookmarks: new Set(),
  bookmarkRows: [],
  mistakeScope: "ALL",
  historyCursor: 0,
  historyCursors: [],
  historyNext: null,
});

const TABS = ["mistakes", "notes", "history", "analytics"];

function showPanel(tab) {
  for (const button of $$(".me-tabs button")) {
    button.classList.toggle("is-active", button.dataset.tab === tab);
    button.setAttribute("aria-selected", String(button.dataset.tab === tab));
  }
  for (const panel of $$(".me-panel")) panel.hidden = panel.dataset.panel !== tab;
}

for (const button of $$(".me-tabs button")) {
  button.addEventListener("click", () => Router.go(`#/${button.dataset.tab}`));
}

// ── 错题集 ────────────────────────────────────────────────────────────────
/* 按科目分段：不同科目的掌握度不该混成一个数字。 */
function renderMistakeScopes() {
  const box = $("#mistake-scopes");
  box.replaceChildren();
  const counts = new Map();
  for (const w of state.wrongQuestions) {
    const group = subjectGroupOfForm(w.formCode) || "OTHER";
    counts.set(group, (counts.get(group) || 0) + 1);
  }
  const entries = [{ id: "ALL", label: "全部" },
    ...SUBJECT_GROUPS.filter((g) => counts.has(g.id)).map((g) => ({ id: g.id, label: g.label }))];
  if (entries.length <= 1) return;
  for (const entry of entries) {
    const count = entry.id === "ALL" ? state.wrongQuestions.length : counts.get(entry.id) || 0;
    const button = el("button", state.mistakeScope === entry.id ? "is-active" : "");
    button.type = "button";
    button.append(document.createTextNode(entry.label), el("b", "", String(count)));
    button.addEventListener("click", () => {
      state.mistakeScope = entry.id;
      Router.replace(entry.id === "ALL" ? "#/mistakes" : `#/mistakes/${entry.id}`);
      renderMistakeScopes();
      renderWrongList();
    });
    box.append(button);
  }
}

async function loadWrongBook() {
  const { wrongQuestions } = await api("/api/v1/wrong-questions");
  state.wrongQuestions = wrongQuestions;
  renderMistakeScopes();
  renderWrongList();
}

function renderWrongList() {
  const list = $("#wrong-question-list");
  list.replaceChildren();
  const statusFilter = $("#filter-wrong-status").value;
  const rows = state.wrongQuestions.filter((w) =>
    (!statusFilter || w.status === statusFilter) &&
    (state.mistakeScope === "ALL" || subjectGroupOfForm(w.formCode) === state.mistakeScope));

  const pending = state.wrongQuestions.filter((w) => w.status !== "MASTERED").length;
  $("#summary-mistakes").textContent = pending;
  const badge = $("#badge-mistakes");
  badge.textContent = pending;
  badge.hidden = !pending;
  $("#mistakes-summary").textContent =
    `${rows.length} 道题 · 全部错题 ${state.wrongQuestions.length} 道 · 待复习 ${pending} 道`;

  if (!rows.length) {
    list.append(el("p", "empty-hint", "这个范围里没有错题。做几套卷之后再回来看。"));
    return;
  }

  for (const w of rows) {
    const row = el("article", `me-row subject-${subjectGroupOfForm(w.formCode)}`);
    const head = el("div", "me-row-head");
    head.append(el("h3", "me-row-title",
      `${I18N.translateShortForm(w.formCode)} · ${w.printedLabel || w.stableKey}`));
    head.append(el("span", `badge badge-${w.status === "MASTERED" ? "ok" : "wait"}`,
      I18N.translateStatus(w.status)));
    row.append(head);

    const meta = el("div", "me-row-meta");
    meta.append(
      el("span", "", `累计做错 ${w.wrongCount} 次`),
      el("span", "", `最近作答 ${new Date(w.lastAnsweredAt).toLocaleDateString()}`),
    );
    if (w.nextReviewAt) meta.append(el("span", "", `下次复习 ${new Date(w.nextReviewAt).toLocaleDateString()}`));
    if (w.sourceSession) meta.append(el("span", "", w.sourceSession));
    row.append(meta);

    if (w.stemAst) {
      const stem = el("div", "me-row-stem");
      stem.append(renderAst(w.stemAst));
      row.append(stem);
    }

    const cause = el("textarea", "mistake-note");
    cause.placeholder = "错因：概念、读题、计算、时间不足等";
    cause.value = w.notes || "";
    row.append(cause);

    const schedule = el("select");
    schedule.setAttribute("aria-label", "复习间隔");
    for (const [days, label] of [[0, "今天复习"], [1, "明天复习"], [3, "3天后复习"], [7, "一周后复习"]]) {
      const opt = el("option", "", label);
      opt.value = days;
      schedule.append(opt);
    }

    const actions = el("div", "me-row-actions");
    actions.append(
      actionButton("去重练", () => practiceQuestions([w.questionId]), "primary-button"),
      actionButton("标记为已掌握", async () => {
        await api(`/api/v1/wrong-questions/${w.questionId}`, {
          method: "PUT", body: JSON.stringify({ status: "MASTERED" }),
        });
        await loadWrongBook();
      }),
      schedule,
      actionButton("安排复习", async () => {
        await api(`/api/v1/wrong-questions/${w.questionId}/schedule`, {
          method: "POST", body: JSON.stringify({ days: Number(schedule.value) }),
        });
        await loadWrongBook();
      }),
      actionButton("保存错因", async () => {
        await api(`/api/v1/wrong-questions/${w.questionId}`, {
          method: "PUT", body: JSON.stringify({ status: w.status, notes: cause.value }),
        });
        showNotice("错因已保存。");
      }),
    );
    row.append(actions, createNoteEditor(w.questionId));
    list.append(row);
  }
}
$("#filter-wrong-status").addEventListener("change", renderWrongList);

/* 「我的」不自己开会话：把题目交回 practice 工作区，由它组题并进入作答。 */
function practiceQuestions(questionIds) {
  sessionStorage.setItem("eju.practiceQueue", JSON.stringify(questionIds));
  location.href = "./practice#/collect?queue=1";
}

// ── 收藏笔记 ──────────────────────────────────────────────────────────────
async function loadBookmarks() {
  const { bookmarks } = await api("/api/v1/bookmarks");
  state.bookmarkRows = bookmarks;
  state.bookmarks = new Set(bookmarks.map((b) => b.questionId));
  $("#summary-bookmarks").textContent = bookmarks.length;
  const badge = $("#badge-notes");
  badge.textContent = bookmarks.length;
  badge.hidden = !bookmarks.length;
  renderBookmarkList();
}

function renderBookmarkList() {
  const list = $("#bookmark-list");
  list.replaceChildren();
  const term = $("#notes-search").value.trim().toLowerCase();
  const rows = state.bookmarkRows.filter((b) => {
    if (!term) return true;
    return [b.printedLabel, b.stableKey, b.sourceSession, b.formCode, b.note]
      .some((v) => String(v || "").toLowerCase().includes(term));
  });
  $("#notes-summary").textContent = `${rows.length} 道收藏题`;

  if (!rows.length) {
    list.append(el("p", "empty-hint", "还没有收藏。作答或复盘时点题目右上角的「☆ 收藏」。"));
    return;
  }
  for (const b of rows) {
    const row = el("article", `me-row subject-${subjectGroupOfForm(b.formCode)}`);
    const head = el("div", "me-row-head");
    head.append(el("h3", "me-row-title",
      `${I18N.translateShortForm(b.formCode)} · ${b.printedLabel || b.stableKey}`));
    row.append(head);
    const meta = el("div", "me-row-meta");
    if (b.sourceSession) meta.append(el("span", "", b.sourceSession));
    if (b.bookmarkedAt) meta.append(el("span", "", `收藏于 ${new Date(b.bookmarkedAt).toLocaleDateString()}`));
    row.append(meta);
    if (b.stemAst) {
      const stem = el("div", "me-row-stem");
      stem.append(renderAst(b.stemAst));
      row.append(stem);
    }
    const actions = el("div", "me-row-actions");
    actions.append(
      actionButton("去练习", () => practiceQuestions([b.questionId]), "primary-button"),
      actionButton("取消收藏", async () => {
        await toggleBookmark(b.questionId, null);
        await loadBookmarks();
      }),
    );
    row.append(actions, createNoteEditor(b.questionId));
    list.append(row);
  }
}
$("#notes-search").addEventListener("input", renderBookmarkList);
$("#notes-practice-all").addEventListener("click", act(async () => {
  if (!state.bookmarkRows.length) throw new Error("还没有收藏的题目。");
  practiceQuestions(state.bookmarkRows.map((b) => b.questionId));
}));

// ── 练习记录 ──────────────────────────────────────────────────────────────
async function loadHistory() {
  const params = new URLSearchParams({ cursor: state.historyCursor || 0, limit: 30 });
  const status = $("#history-status").value;
  if (status) params.set("status", status);
  const page = await api(`/api/v1/history?${params}`);
  state.historyNext = page.nextCursor;
  $("#history-next").disabled = state.historyNext === null;
  $("#history-prev").disabled = !state.historyCursors.length;

  const tbody = $("#history-tbody");
  tbody.replaceChildren();
  if (!page.history.length) {
    const tr = document.createElement("tr");
    const td = el("td", "text-center", "暂无练习记录");
    td.colSpan = 7;
    tr.append(td);
    tbody.append(tr);
    return;
  }

  for (const h of page.history) {
    const tr = document.createElement("tr");
    tr.append(el("td", "", new Date(h.submittedAt || h.createdAt).toLocaleString()));
    tr.append(el("td", "", I18N.translatePaperTitle(h.paperTitle || "-")));
    tr.append(el("td", "", I18N.translateMode(h.mode)));
    tr.append(el("td", "", (h.selectedForms || []).map((f) => I18N.translateShortForm(f)).join("，")));
    tr.append(el("td", "", I18N.translateStatus(h.status)));
    const sum = h.summary;
    tr.append(el("td", "num", sum
      ? `${sum.objectiveCorrect} / ${sum.objectiveTotal}（${Math.round((sum.objectiveAccuracy || 0) * 100)}%）`
      : "-"));

    const opTd = el("td");
    if (h.status === "SUBMITTED") {
      const view = el("a", "btn btn-outline", "查看详情");
      view.href = `./practice#/result/${h.sessionId}`;
      opTd.append(view);
    } else if (h.status !== "ABANDONED") {
      const resume = el("a", "btn btn-outline", "继续练习");
      resume.href = `./practice#/session/${h.sessionId}`;
      opTd.append(resume);
    } else {
      opTd.append(el("span", "subtitle", "已放弃"));
    }
    tr.append(opTd);
    tbody.append(tr);
  }
}
$("#history-status").addEventListener("change", act(() => {
  state.historyCursor = 0; state.historyCursors = []; return loadHistory();
}));
$("#history-prev").addEventListener("click", act(() => {
  state.historyCursor = state.historyCursors.pop() ?? 0; return loadHistory();
}));
$("#history-next").addEventListener("click", act(() => {
  state.historyCursors.push(state.historyCursor || 0);
  state.historyCursor = state.historyNext;
  return loadHistory();
}));

// ── 学习分析 ──────────────────────────────────────────────────────────────
function analyticsCard(value, label, warn = false) {
  const card = el("div", `analytics-card${warn ? " is-warn" : ""}`);
  card.append(el("strong", "", String(value)), el("span", "", label));
  return card;
}

async function loadAnalytics() {
  const [stats, goals] = await Promise.all([
    api("/api/v1/learning/summary"), api("/api/v1/learning/goals"),
  ]);
  const box = $("#learning-summary");
  box.replaceChildren(
    analyticsCard(stats.uniqueQuestions, "独立题数 " + stats.uniqueQuestions),
    analyticsCard(stats.answeredAttempts, "已作答次数"),
    analyticsCard(stats.unansweredExposures, "未答曝光次数"),
  );
  for (const [key, name] of [["firstUnaided", "未看提示的首答"], ["repeatUnaided", "未看提示的重练"],
                             ["revealed", "看过提示"]]) {
    const m = stats[key];
    box.append(analyticsCard(
      m.accuracy === null ? "暂无样本" : `${(m.accuracy * 100).toFixed(1)}%`,
      `${name} · ${m.correct} / ${m.denominator}`));
  }
  if (stats.contentQuality?.affectedAnsweredAttempts) {
    box.append(analyticsCard(stats.contentQuality.affectedAnsweredAttempts,
      `次作答的来源待复核或停用。${stats.contentQuality.note}`, true));
  }
  box.append(analyticsCard("范围", stats.scope));

  $("#goal-new").value = goals.newQuestions;
  $("#goal-review").value = goals.reviewAttempts;
  $("#goal-timezone").value = goals.timezone;

  const calendar = await api("/api/v1/learning/calendar?timezone=" + encodeURIComponent(goals.timezone));
  const table = el("table", "data-table");
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const text of ["日期", "作答", "待复习", "未答"]) headRow.append(el("th", "", text));
  thead.append(headRow);
  const tbody = document.createElement("tbody");
  for (const day of calendar.days) {
    const row = document.createElement("tr");
    row.append(el("td", "", day.date), el("td", "num", String(day.answeredAttempts)),
      el("td", "num", String(day.due)), el("td", "num", String(day.unanswered)));
    tbody.append(row);
  }
  table.append(thead, tbody);
  $("#learning-calendar").replaceChildren(table);
}

$("#goals-form").addEventListener("submit", act(async (event) => {
  event.preventDefault();
  await api("/api/v1/learning/goals", {
    method: "PUT",
    body: JSON.stringify({
      newQuestions: Number($("#goal-new").value),
      reviewAttempts: Number($("#goal-review").value),
      timezone: $("#goal-timezone").value,
    }),
  });
  showNotice("学习目标已保存。");
  await loadAnalytics();
}));

// ── 概览与路由 ────────────────────────────────────────────────────────────
async function loadSummary() {
  try {
    const { history } = await api("/api/v1/history?limit=30");
    const submitted = history.filter((h) => h.status === "SUBMITTED" && h.summary);
    $("#summary-sessions").textContent = history.length;
    if (submitted.length) {
      const correct = submitted.reduce((n, h) => n + h.summary.objectiveCorrect, 0);
      const total = submitted.reduce((n, h) => n + h.summary.objectiveTotal, 0);
      $("#summary-accuracy").textContent = total ? `${Math.round((correct / total) * 100)}%` : "—";
    }
  } catch { /* 概览失败不该挡住四个 panel */ }
}

const loaded = new Set();
async function ensureLoaded(tab) {
  if (loaded.has(tab)) return;
  loaded.add(tab);
  try {
    if (tab === "mistakes") await loadWrongBook();
    if (tab === "notes") await loadBookmarks();
    if (tab === "history") await loadHistory();
    if (tab === "analytics") await loadAnalytics();
  } catch (error) {
    loaded.delete(tab);
    $("#page-status").textContent = error.message;
    $("#page-status").classList.add("is-error");
    throw error;
  }
}

Router
  .add(/^#\/mistakes(?:\/([A-Z_]+))?$/, async ([, scope]) => {
    state.mistakeScope = scope || "ALL";
    showPanel("mistakes");
    await ensureLoaded("mistakes");
    renderMistakeScopes();
    renderWrongList();
  })
  .add(/^#\/(notes|history|analytics)$/, async ([, tab]) => {
    showPanel(tab);
    await ensureLoaded(tab);
  })
  .setFallback(async () => {
    showPanel("mistakes");
    await ensureLoaded("mistakes");
  });

async function boot() {
  await loadLibraryInstanceId();
  const status = $("#connection-status");
  try {
    await api("/api/v1/health");
    status.textContent = "本地题库已连接";
    status.className = "me-connection online";
  } catch {
    status.textContent = "本地服务未连接";
    status.className = "me-connection offline";
  }
  await loadSummary();
  await Router.start();
}

boot().catch(showError);
