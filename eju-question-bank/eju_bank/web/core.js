"use strict";
/* ==========================================================================
   EJU 题库 · 共用底座
   --------------------------------------------------------------------------
   四个页面（home / practice / me / studio）都加载本文件。这里只放与页面无关
   的东西：本地化字典、API 调用、AST 渲染、图片查看、个人笔记、收藏、以及
   hash 路由工具。页面专有逻辑在各自的 JS 里。
   ========================================================================== */

// ── 本地化 ────────────────────────────────────────────────────────────────
const I18N = {
  forms: {
    PHYSICS_JA: "物理", CHEMISTRY_JA: "化学", BIOLOGY_JA: "生物",
    MATHEMATICS_COURSE_1_JA: "数学 1 类（文科）", MATHEMATICS_COURSE_2_JA: "数学 2 类（理科）",
    JAPAN_AND_WORLD_JA: "综合科目", JAPANESE_JA: "日本语",
    PHYSICS_EN: "物理（英语版）", CHEMISTRY_EN: "化学（英语版）", BIOLOGY_EN: "生物（英语版）",
    MATHEMATICS_COURSE_1_EN: "数学 1 类（英语版）", MATHEMATICS_COURSE_2_EN: "数学 2 类（英语版）",
    JAPAN_AND_WORLD_EN: "综合科目（英语版）",
  },
  shortForms: {
    PHYSICS_JA: "物理", CHEMISTRY_JA: "化学", BIOLOGY_JA: "生物",
    MATHEMATICS_COURSE_1_JA: "数学1类", MATHEMATICS_COURSE_2_JA: "数学2类",
    JAPAN_AND_WORLD_JA: "综合科目", JAPANESE_JA: "日本语",
    PHYSICS_EN: "物理EN", CHEMISTRY_EN: "化学EN", BIOLOGY_EN: "生物EN",
    MATHEMATICS_COURSE_1_EN: "数学1类EN", MATHEMATICS_COURSE_2_EN: "数学2类EN",
    JAPAN_AND_WORLD_EN: "综合EN",
  },
  modes: { PRACTICE: "自由练习", MOCK: "全真模拟", SECTION: "单科专练" },
  completeness: { COMPLETE: "完整整套卷", PARTIAL: "部分练习卷", SAMPLE: "演示样卷" },
  // 这份卷是怎么过审的。学习者有权知道自己在练什么级别的把关结果。
  reviewGrade: {
    HUMAN_SIGNED: { label: "✓ 人工复核", cls: "ok",
      title: "每一页都由复核人对照原卷签署。" },
    MACHINE_ATTESTED: { label: "⚙ 机器校验", cls: "part",
      title: "题干与选项是原卷的逐字 OCR，答案取自官方正解表并核对过选项；"
           + "但未经人工逐页比对，页面区域位置也未核实。" },
    MIXED: { label: "⚙ 部分机器校验", cls: "part",
      title: "这份卷里既有人工签署的页，也有仅经机器校验的页。" },
    // 本次改造之前发布的卷没有记录把关等级。不知道就说不知道，
    // 不能默认成最高的那一档。
    UNRECORDED: { label: "⚠ 未标注把关等级", cls: "miss",
      title: "这份卷发布时没有记录它是怎么过审的，无法说明把关程度。" },
  },
  status: {
    IN_PROGRESS: "作答中", PAUSED: "已暂停", SUBMITTED: "已交卷", ABANDONED: "已放弃",
    NEW_WRONG: "新错题", REVIEWING: "复习中", RETRY_DUE: "待重做", MASTERED: "已掌握",
    RECEIVED: "原卷已接收", PROBED: "已探测", RENDERED: "已渲染", EXTRACTED: "已提取",
    REVIEWED: "已复核", ASSEMBLED: "已组装", VALIDATED: "已校验",
    BLOCKED: "待补充材料", PUBLISHED: "已装配发布",
  },
  rights: { PRIVATE_STUDY: "个人学习备考", PUBLIC: "公开发布", COMMERCIAL: "商业使用" },
  blocking: {
    MISSING_ANSWER: "待补充官方答案表", MISSING_AUDIO: "待补充官方听力录音",
    MISSING_TRANSCRIPT: "待补充听力原文",
  },
  subjects: { SCIENCE: "理科", JAPANESE: "日本语", MATHEMATICS: "数学", JAPAN_AND_WORLD: "综合科目" },
  languages: { ja: "日语", en: "英语" },
  syllabus: { "basic-2015": "2015年现行大纲", "japanese-2015": "2015年日本语大纲", 2015: "2015年现行大纲" },
  paperTitles: {
    "2023-2 EJU SCIENCE": "2023年度第2回 日本留学考试 理科试卷（物理/化学/生物）",
    "EJU Synthetic Full Suite (All 13 Forms)": "EJU 全 13 科目形式基准测试卷（标准对照）",
  },
  translatePaperTitle(raw) { return this.paperTitles[raw] || raw; },
  translateForm(code) { return this.forms[code] || code; },
  translateShortForm(code) { return this.shortForms[code] || code; },
  translateMode(mode) { return this.modes[mode] || mode; },
  translateStatus(s) { return this.status[s] || s; },
  translateCompleteness(c) { return this.completeness[c] || c; },
  translateReviewGrade(g) { return this.reviewGrade[g] || null; },
};

/* 科目分类：L2 的四个类别。formCode 与试卷 subject 都归到同一组，
   这样卷子卡的色条和分类标签用的是同一套判断。 */
const SUBJECT_GROUPS = [
  { id: "JAPANESE", label: "日本語", color: "var(--shu)", forms: ["JAPANESE_JA"] },
  { id: "SCIENCE", label: "理科", color: "var(--sci)",
    forms: ["PHYSICS_JA", "PHYSICS_EN", "CHEMISTRY_JA", "CHEMISTRY_EN", "BIOLOGY_JA", "BIOLOGY_EN"] },
  { id: "JAPAN_AND_WORLD", label: "総合科目", color: "var(--kohaku)",
    forms: ["JAPAN_AND_WORLD_JA", "JAPAN_AND_WORLD_EN"] },
  { id: "MATHEMATICS", label: "数学", color: "var(--midori)",
    forms: ["MATHEMATICS_COURSE_1_JA", "MATHEMATICS_COURSE_1_EN",
            "MATHEMATICS_COURSE_2_JA", "MATHEMATICS_COURSE_2_EN"] },
];

function subjectGroupOfForm(formCode) {
  return SUBJECT_GROUPS.find((g) => g.forms.includes(formCode))?.id || "";
}
function subjectGroupLabel(id) {
  return SUBJECT_GROUPS.find((g) => g.id === id)?.label || I18N.subjects[id] || id;
}

/* 一套卷在界面上的名字。所有列表、选择器、标题共用这一个，因为它们指的是同一
   套卷——各写一份的后果不是样式不一致，是"数学"这一行在某些地方分不出文科卷还是
   理科卷，而那是两份完全不同的题册。年份回次、科目、数学类别、语言，一次说全。 */
function sourceLabel(source) {
  if (!source) return "";
  const parts = [source.session];
  const subject = source.subject;
  let name = I18N.subjects[subject] || subject || "";
  if (subject === "MATHEMATICS") {
    const form = (source.expectedForms || [])[0] || "";
    const hint = `${form} ${source.inventoryId || ""}`;
    if (form.includes("COURSE_1") || /\bc1\b|-c1/.test(hint)) name = "数学 1 类（文科）";
    else if (form.includes("COURSE_2") || /\bc2\b|-c2/.test(hint)) name = "数学 2 类（理科）";
    else name = "数学（类别未登记）";
  }
  parts.push(name);
  if (source.language) parts.push(I18N.languages[source.language] || source.language);
  return parts.filter(Boolean).join(" · ");
}


// ── DOM 与网络 ────────────────────────────────────────────────────────────
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => root.querySelectorAll(s);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const data = await res.json();
  if (!res.ok) {
    const err = new Error(data.error?.message || `HTTP ${res.status}`);
    err.status = res.status;
    err.code = data.error?.code;
    err.data = data;
    throw err;
  }
  return data;
}

/* 每个页面各有一份 state，但笔记、收藏、草稿键都要用 libraryInstanceId，
   所以在这里给出共同的最小形状，页面再往上加自己的字段。 */
const state = {
  libraryInstanceId: "default",
  bookmarks: new Set(),
  // 候选/批准属于哪一套卷，以及"打开来源"这个动作的序号。两者都是为了不让
  // 上一套卷的结果画到下一套卷上：切来源不清理，界面就会说谎。
  reviewOwner: null,
  openSeq: 0,
};

async function loadLibraryInstanceId() {
  try {
    const health = await api("/api/v1/health");
    if (health?.libraryInstanceId) state.libraryInstanceId = health.libraryInstanceId;
  } catch { /* 离线时用默认命名空间，草稿仍可读写 */ }
  return state.libraryInstanceId;
}

// ── 提示条 ────────────────────────────────────────────────────────────────
let toastTimer = null;

/* showError 沿用旧名字：它既报错也报成功提示，调用点遍布各页。 */
function showError(error) {
  const message = error?.message || String(error);
  const isError = !(error instanceof Error) || !error.__notice;
  showToast(message, isError ? "error" : "notice");
}

function showNotice(message) { showToast(message, "notice"); }

function showToast(message, kind = "notice") {
  let toast = $("#toast");
  if (!toast) {
    toast = el("div", "toast");
    toast.id = "toast";
    toast.setAttribute("role", "status");
    document.body.append(toast);
  }
  toast.replaceChildren();
  toast.classList.toggle("is-error", kind === "error");
  toast.append(el("span", "", message));
  const close = el("button", "", "✕");
  close.type = "button";
  close.setAttribute("aria-label", "关闭提示");
  close.addEventListener("click", () => { toast.hidden = true; });
  toast.append(close);
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, kind === "error" ? 9000 : 4500);
}

/* 把异步动作包成"失败就提示"的处理器，表单提交自动阻止默认行为。 */
const act = (fn) => (...args) => {
  if (args[0]?.type === "submit") args[0].preventDefault();
  return Promise.resolve().then(() => fn(...args)).catch(showError);
};

function actionButton(text, fn, className = "btn btn-outline") {
  const b = el("button", className, text);
  b.type = "button";
  b.addEventListener("click", act(fn));
  return b;
}

// ── 图片查看 ──────────────────────────────────────────────────────────────
function openImageZoom(src) {
  const modal = $("#modal-image-zoom");
  if (!modal) return;
  $("#zoom-img").src = src;
  modal.classList.remove("hidden");
}

function closeImageZoom() { $("#modal-image-zoom")?.classList.add("hidden"); }

function pinFigure(src, title = "试卷配图") {
  const dock = $("#floating-figure-dock");
  if (!dock) return;
  dock.replaceChildren();
  dock.hidden = false;
  dock.classList.remove("hidden", "collapsed");

  const header = el("div", "dock-header");
  header.append(el("span", "dock-title", `📌 ${title}`));

  const actions = el("div", "dock-actions");
  const collapseBtn = el("button", "dock-btn", "折叠");
  collapseBtn.type = "button";
  collapseBtn.title = "折叠/展开浮窗";
  collapseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dock.classList.toggle("collapsed");
    collapseBtn.textContent = dock.classList.contains("collapsed") ? "展开" : "折叠";
  });
  const zoomBtn = el("button", "dock-btn", "放大");
  zoomBtn.type = "button";
  zoomBtn.title = "全屏查看高清大图";
  zoomBtn.addEventListener("click", (e) => { e.stopPropagation(); openImageZoom(src); });
  const closeBtn = el("button", "dock-btn", "✕");
  closeBtn.type = "button";
  closeBtn.title = "关闭悬浮窗";
  closeBtn.setAttribute("aria-label", "关闭悬浮窗");
  closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dock.hidden = true;
    dock.classList.add("hidden");
    dock.replaceChildren();
  });
  actions.append(collapseBtn, zoomBtn, closeBtn);
  header.append(actions);

  const body = el("div", "dock-body");
  const img = el("img");
  img.src = src;
  img.alt = title;
  img.title = "点击全屏放大";
  img.addEventListener("click", () => openImageZoom(src));
  body.append(img);
  dock.append(header, body);
}

// ── 题目内容 AST 渲染 ─────────────────────────────────────────────────────
function renderAst(nodes, mediaBase = "/api/v1/media/") {
  const fragment = document.createDocumentFragment();
  for (const node of nodes || []) {
    if (["text", "paragraph", "callout", "underline"].includes(node.type)) {
      fragment.append(el(node.type === "paragraph" ? "p" : "span", node.type, node.value || ""));
    } else if (node.type === "inlineMath" || node.type === "displayMath") {
      const container = el(node.type === "displayMath" ? "div" : "span", "math-node");
      if (window.katex && node.latex) {
        try {
          window.katex.render(node.latex, container, {
            displayMode: node.type === "displayMath", throwOnError: false,
          });
        } catch { container.textContent = node.latex; }
      } else {
        container.textContent = `$${node.latex}$`;
      }
      fragment.append(container);
    } else if (node.type === "ruby") {
      const ruby = document.createElement("ruby");
      ruby.append(document.createTextNode(node.base || ""));
      const rt = document.createElement("rt");
      rt.textContent = node.ruby || "";
      ruby.append(rt);
      fragment.append(ruby);
    } else if (node.type === "lineBreak") {
      fragment.append(document.createElement("br"));
    } else if (node.type === "figure") {
      const wrap = el("div", "figure-wrapper");
      if (node.assetId) {
        const toolbar = el("div", "figure-toolbar");
        const pinBtn = el("button", "figure-btn", "📌 悬浮固定");
        pinBtn.type = "button";
        pinBtn.title = "在右下角悬浮窗固定显示此图，滚动做题随时对照";
        const zoomBtn = el("button", "figure-btn", "🔍 放大");
        zoomBtn.type = "button";
        zoomBtn.title = "全屏高清大图查看";

        const img = el("img", "figure-img");
        img.loading = "lazy";
        img.src = mediaBase + node.assetId;
        img.alt = node.alt || "试卷原图";
        img.title = "点击放大试卷原图";
        img.tabIndex = 0;
        img.setAttribute("role", "button");
        img.addEventListener("click", () => openImageZoom(img.src));
        img.addEventListener("keydown", (e) => { if (e.key === "Enter") openImageZoom(img.src); });
        img.addEventListener("error", () => { img.alt = "图片加载失败，请稍后重试或报告内容问题"; });

        zoomBtn.addEventListener("click", (e) => { e.stopPropagation(); openImageZoom(img.src); });
        pinBtn.addEventListener("click", (e) => { e.stopPropagation(); pinFigure(img.src, node.alt || "试卷配图"); });

        toolbar.append(pinBtn, zoomBtn);
        wrap.append(toolbar, img);
        if (node.alt) wrap.append(el("p", "figure-caption", `【原卷配图】${node.alt}`));
      } else {
        wrap.append(el("div", "figure-placeholder", "图表：原卷矢量图切片"));
      }
      fragment.append(wrap);
    } else if (node.type === "answerSlot") {
      fragment.append(el("span", "answer-slot", `[${node.slot}]`));
    } else if (node.type === "table") {
      const table = document.createElement("table");
      table.className = "ast-table";
      for (const row of node.rows || []) {
        const tr = document.createElement("tr");
        for (const cell of (row || [])) {
          const td = document.createElement(cell?.header ? "th" : "td");
          if (cell && typeof cell === "object") {
            if (Number.isInteger(cell.rowspan) && cell.rowspan > 0) td.rowSpan = cell.rowspan;
            if (Number.isInteger(cell.colspan) && cell.colspan > 0) td.colSpan = cell.colspan;
          }
          if (typeof cell === "string" || typeof cell === "number") {
            td.textContent = String(cell);
          } else if (Array.isArray(cell)) {
            td.append(renderAst(cell, mediaBase));
          } else if (cell && typeof cell === "object") {
            if (cell.type) td.append(renderAst([cell], mediaBase));
            else if (cell.contentAst) td.append(renderAst(cell.contentAst, mediaBase));
            else td.textContent = String(cell.value || cell.text || "");
          } else {
            td.textContent = "";
          }
          tr.append(td);
        }
        table.append(tr);
      }
      fragment.append(table);
    }
    if (node.children) fragment.append(renderAst(node.children, mediaBase));
  }
  return fragment;
}

function astHasFigure(nodes) {
  if (!Array.isArray(nodes)) return false;
  return nodes.some((n) => n?.type === "figure" || (n?.children && astHasFigure(n.children)));
}

function astExtractFigures(nodes) {
  const figures = [], nonFigures = [];
  for (const n of nodes || []) (n?.type === "figure" ? figures : nonFigures).push(n);
  return { figures, nonFigures };
}

// ── 收藏 ──────────────────────────────────────────────────────────────────
async function toggleBookmark(questionId, btn) {
  const remove = state.bookmarks.has(questionId);
  await api(`/api/v1/questions/${questionId}/bookmark`, {
    method: remove ? "DELETE" : "PUT", ...(remove ? {} : { body: "{}" }),
  });
  if (remove) state.bookmarks.delete(questionId); else state.bookmarks.add(questionId);
  if (btn) {
    btn.classList.toggle("active", !remove);
    btn.textContent = remove ? "☆ 收藏" : "★ 已收藏";
  }
}

// ── 个人笔记编辑器 ────────────────────────────────────────────────────────
/* 作答页、复盘页、组题检索、我的·收藏笔记都用它。本机草稿按题目 ID 存，
   带 baseRevision，刷新后不会绕过服务端的 CAS 校验。 */
function createNoteEditor(questionId) {
  const box = el("details", "note-editor");
  box.append(el("summary", "", "个人笔记"));
  const input = el("textarea", "note-input");
  input.maxLength = 10000;
  input.placeholder = "写下自己的理解，笔记会自动保存。";
  input.setAttribute("aria-label", "个人笔记");
  const message = el("span", "note-save", "正在读取笔记……");
  const key = `eju.note.${state.libraryInstanceId}.${questionId}`;
  let noteRevision = 0;
  let acknowledged = "", saving = null, timer, ready = false;

  async function save() {
    if (!ready) return;
    if (saving) return saving;
    saving = (async () => {
      try {
        while (input.value !== acknowledged) {
          const snapshot = input.value;
          message.textContent = "笔记保存中……";
          try {
            const saved = await api(`/api/v1/questions/${questionId}/note`, {
              method: "PUT", body: JSON.stringify({ note: snapshot, baseRevision: noteRevision }),
            });
            noteRevision = saved.revision;
            localStorage.setItem(key, JSON.stringify({ text: input.value, baseRevision: noteRevision }));
          } catch (error) {
            if (error.status !== 409) throw error;
            const remote = await api(`/api/v1/questions/${questionId}/note`);
            if (!confirm("笔记在另一页面已更新。确定保留当前草稿；取消使用服务器版本。")) {
              input.value = remote.note || "";
              acknowledged = input.value;
            }
            noteRevision = remote.revision;
            continue;
          }
          acknowledged = snapshot;
        }
        localStorage.removeItem(key);
        message.textContent = "笔记已保存";
      } catch (error) {
        message.textContent = "保存失败，草稿已保留；点击重试";
        throw error;
      } finally { saving = null; }
    })();
    return saving;
  }

  input.disabled = true;
  api(`/api/v1/questions/${questionId}/note`).then(({ note, revision }) => {
    noteRevision = revision || 0;
    acknowledged = note || "";
    const savedDraft = localStorage.getItem(key);
    if (savedDraft !== null) {
      let draft;
      try { draft = JSON.parse(savedDraft); } catch { draft = null; }
      input.value = typeof draft?.text === "string" ? draft.text : savedDraft;
      // 恢复草稿真正依据的修订号，刷新不能绕过 CAS。
      noteRevision = Number.isInteger(draft?.baseRevision) ? draft.baseRevision : -1;
    } else {
      input.value = acknowledged;
    }
    ready = true;
    input.disabled = false;
    message.textContent = "笔记已加载";
    if (input.value !== acknowledged) save().catch(showError);
  }).catch(showError);

  input.addEventListener("input", () => {
    localStorage.setItem(key, JSON.stringify({ text: input.value, baseRevision: noteRevision }));
    message.textContent = "笔记待保存";
    clearTimeout(timer);
    timer = setTimeout(() => save().catch(showError), 500);
  });
  message.addEventListener("click", () => save().catch(showError));
  box.append(input, message);
  return box;
}

// ── hash 路由 ─────────────────────────────────────────────────────────────
/* 地址栏是产品的一部分：每一层视图都有自己的 hash，刷新停在原处，
   后退键在应用内导航，深链可以从别的工作区直接进来。 */
const Router = {
  routes: [],
  fallback: null,
  suspended: false,

  /* pattern 是正则，handler 收到 match 数组。第一个匹配的胜出。 */
  add(pattern, handler) { this.routes.push({ pattern, handler }); return this; },
  setFallback(handler) { this.fallback = handler; return this; },

  /* 只改地址栏，不重新分发——视图已经由调用方切好了。 */
  replace(hash) {
    if (location.hash === hash) return;
    this.suspended = true;
    history.replaceState(null, "", hash || location.pathname + location.search);
    this.suspended = false;
  },
  go(hash) {
    if (location.hash === hash) {
      Promise.resolve().then(() => this.apply()).catch(showError);
    } else {
      location.hash = hash;
    }
  },

  async apply() {
    const hash = location.hash || "";
    for (const { pattern, handler } of this.routes) {
      const match = pattern.exec(hash);
      if (match) return handler(match);
    }
    return this.fallback?.(hash);
  },

  start() {
    window.addEventListener("hashchange", () => {
      if (this.suspended) return;
      Promise.resolve().then(() => this.apply()).catch(showError);
    });
    return Promise.resolve().then(() => this.apply());
  },
};

/* 同一页面内的一组视图，任何时刻只显示一个。 */
function showOnly(container, id) {
  for (const view of container.querySelectorAll(":scope > .view")) view.hidden = view.id !== id;
}

// ── 图片模态框与全局错误兜底 ──────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  $("#modal-zoom-close")?.addEventListener("click", closeImageZoom);
  $("#modal-image-zoom")?.addEventListener("click", (event) => {
    if (event.target.id === "modal-image-zoom") closeImageZoom();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeImageZoom();
  });
});

window.addEventListener("unhandledrejection", (event) => {
  showError(event.reason);
  event.preventDefault();
});
