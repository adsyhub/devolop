/* JLPT question bank — interactive answering, scoring and a wrong-answer book.
 *
 * Runs against `/api/exams*` when this page is served by `serve_course.py`, and
 * falls back to `localStorage` when it is not, so the page still works if it is
 * ever hosted as plain static files. The fallback is the same local-first shape
 * `app.js` uses for the vocabulary notebook: write locally always, mirror to the
 * backend when there is one.
 *
 * Nothing here ever assigns `innerHTML`. Question text carries markup (<u>, ruby,
 * boxed numbers, tables) and is turned into DOM nodes by `renderInline` /
 * `renderBlocks`, so a stray angle bracket in a transcription is text, not markup.
 */

"use strict";

const $ = (selector) => document.querySelector(selector);

const el = {
  brandTitle: $("#exam-brand-title"),
  brandSub: $("#exam-brand-sub"),
  timer: $("#exam-timer"),
  timerValue: $("#exam-timer-value"),
  progressChip: $("#exam-progress-chip"),
  answeredCount: $("#exam-answered-count"),
  totalCount: $("#exam-total-count"),
  sheetButton: $("#exam-sheet-button"),
  homeButton: $("#exam-home-button"),

  viewHome: $("#view-home"),
  viewPapers: $("#view-papers"),
  viewTopics: $("#view-topics"),
  viewParts: $("#view-parts"),
  viewSetup: $("#view-setup"),
  viewSession: $("#view-session"),
  viewReport: $("#view-report"),

  status: $("#exam-status"),
  list: $("#exam-list"),
  levelSwitch: $("#level-switch"),
  studyModeGrid: $("#study-mode-grid"),
  modeCardMock: $("#mode-card-mock"),
  modeCardTopic: $("#mode-card-topic"),
  mockStat: $("#mock-stat"),
  topicStat: $("#topic-stat"),
  papersBack: $("#papers-back"),
  papersMeta: $("#papers-meta"),
  topicsBack: $("#topics-back"),
  topicsMeta: $("#topics-meta"),
  topicStatus: $("#topic-status"),
  topicList: $("#topic-list"),
  partsBack: $("#parts-back"),
  partsHeading: $("#parts-heading"),
  partsMeta: $("#parts-meta"),
  partsStatus: $("#parts-status"),
  partsList: $("#parts-list"),
  empty: $("#exam-empty"),

  setupBack: $("#setup-back"),
  setupMeta: $("#setup-meta"),
  modeGrid: $("#mode-grid"),
  scopeGrid: $("#scope-grid"),
  startButton: $("#start-button"),
  setupHint: $("#setup-hint"),
  historyBlock: $("#history-block"),
  historyList: $("#history-list"),
  resetProgress: $("#reset-progress-button"),

  sessionBack: $("#session-back"),
  sessionLayout: $("#session-layout"),
  passagePane: $("#passage-pane"),
  passageLabel: $("#passage-label"),
  passageCollapse: $("#passage-collapse"),
  passageScroll: $("#passage-scroll"),

  questionBadge: $("#question-badge"),
  questionPart: $("#question-part"),
  markButton: $("#mark-button"),
  partInstruction: $("#part-instruction"),
  audioWarning: $("#audio-warning"),
  questionPrompt: $("#question-prompt"),
  questionFigure: $("#question-figure"),
  choices: $("#choices"),
  confidenceRow: $("#confidence-row"),
  confidenceButtons: $("#confidence-buttons"),
  verdict: $("#verdict"),
  verdictBadge: $("#verdict-badge"),
  verdictDetail: $("#verdict-detail"),
  keyNote: $("#key-note"),
  orderAnswer: $("#order-answer"),
  orderList: $("#order-list"),
  questionNote: $("#question-note"),

  prevButton: $("#prev-button"),
  revealButton: $("#reveal-button"),
  nextButton: $("#next-button"),
  submitButton: $("#submit-button"),

  answerSheet: $("#answer-sheet"),
  answerSheetBody: $("#answer-sheet-body"),
  answerSheetClose: $("#answer-sheet-close"),

  reportMeta: $("#report-meta"),
  scoreSummary: $("#score-summary"),
  scoringNote: $("#scoring-note"),
  partTable: $("#part-table"),
  wrongBlock: $("#wrong-block"),
  wrongList: $("#wrong-list"),
  reportReview: $("#report-review-button"),
  reportRestart: $("#report-restart-button"),
  reportHome: $("#report-home-button"),

  toast: $("#toast"),
};

const MODES = [
  {
    id: "practice",
    title: "分组练习",
    detail: "完成整组，交卷后统一判题并查看答案。",
  },
  {
    id: "exam",
    title: "计时练习",
    detail: "作答过程中不显示对错，有本地倒计时和答题卡，交卷后一次性看报告。（单机计时练习，不等同服务端严格模考）",
  },
  {
    id: "review",
    title: "错题复习",
    detail: "只抽出做错、蒙对、标记过或到期该复习的题，立刻反馈。",
  },
];

const CONFIDENCE = [
  { id: "sure", label: "有把握" },
  { id: "unsure", label: "不太确定" },
  { id: "guess", label: "蒙的" },
];

const STORAGE_PREFIX = "jlpt-exam:v1:";

// JLPT levels in the order learners think of them. Anything a paper declares
// outside this list still gets a tab, appended after these; a paper with no
// level at all lands under 其他.
// JLPT levels: only N1 and N2 are supported per official spec (K01).
const LEVEL_ORDER = ["N1", "N2"];
const NO_LEVEL = "其他";

/* What the lookup panel is allowed to do here, and what a selection belongs to.
 *
 * The panel used to match `location.pathname` and read this file's `state` from the
 * outside; that broke on any rename and could only guess. Declaring it here keeps the
 * decision with the page that knows it (LEX-19, §11.2).
 *
 * A timed sitting is closed to lookups. Practice and review are open: reading the
 * explanation is the point of them.
 */
window.LexLookupHost = {
  canLookup() {
    const session = state.session;
    if (session && !session.submitted && session.mode === "exam") return false;
    if (session && !session.submitted && session.deadline) return false;
    return true;
  },
  getSelectionContext() {
    const session = state.session;
    const question = session ? session.queue?.[session.index] : null;
    return {
      hostType: "exam",
      examSlug: state.slug || state.exam?.examSlug || "",
      examTitle: state.exam?.title || "",
      questionId: question?.questionId || question?.id || "",
      sourceRevision: state.exam?.contentRevision || "",
      mode: session?.mode || "review",
    };
  },
};

const state = {
  api: false,
  token: "",
  exams: [],
  exam: null,
  slug: "",
  review: {},
  stats: null,
  attempts: [],
  setup: { mode: "practice", scope: "all" },
  // Which JLPT level the list is filtered to.
  level: "N1",
  /* A 专题练习 session runs against a synthetic exam merged from every paper
   * of one level. `questionSource` maps each question back to the paper it
   * came from, so answers and marks still land on the right record; it is null
   * for an ordinary single-paper session. Question ids are content hashes and
   * are unique across papers, which is what makes the merge safe. */
  topic: null,
  questionSource: null,
  topicAttempts: null,
  /* Full papers, fetched once per level and kept: the 题型 breakdown needs the
   * questions, and walking back and forth between screens should not refetch
   * five megabytes. */
  loadedPapers: new Map(),
  activeTopic: null,
  // "papers" | "topics" — which list the setup screen was opened from.
  setupOrigin: "papers",
  session: null,
  lastScore: null,
  pendingAnswers: new Map(),
  flushTimer: 0,
  noteTimer: 0,
};

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function show(view) {
  for (const node of [el.viewHome, el.viewPapers, el.viewTopics, el.viewParts,
    el.viewSetup, el.viewSession, el.viewReport]) {
    node.hidden = node !== view;
  }
  const inSession = view === el.viewSession;
  el.sheetButton.hidden = !inSession;
  el.progressChip.hidden = !inSession;
  el.homeButton.hidden = view === el.viewHome;
  if (view !== el.viewSession && view !== el.viewReport && view !== el.viewSetup) {
    // Leaving the paper/topic entirely: drop any merged exam so the next entry
    // rebuilds it rather than practising a stale queue.
    clearTopic();
  }
  if (!inSession) {
    el.answerSheet.hidden = true;
    el.sheetButton.setAttribute("aria-expanded", "false");
  }
  window.scrollTo({ top: 0, behavior: "auto" });
}

let toastTimer = 0;
function toast(message) {
  el.toast.textContent = message;
  el.toast.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { el.toast.hidden = true; }, 2600);
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function formatClock(totalSeconds) {
  const sign = totalSeconds < 0 ? "-" : "";
  const seconds = Math.abs(Math.round(totalSeconds));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (value) => String(value).padStart(2, "0");
  return sign + (h ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`);
}

// ---------------------------------------------------------------------------
// Markup → DOM lives in exam_markup.js, loaded before this file. It is separated
// out because it is the one place where question text — a transcription of a
// scanned page — becomes DOM, and it must never do that through innerHTML.
// ---------------------------------------------------------------------------

const { renderInline, renderBlocks, plainText } = window.ExamMarkup;

// ---------------------------------------------------------------------------
// API layer
// ---------------------------------------------------------------------------

async function acquireToken() {
  try {
    const response = await fetch("./api/session/bootstrap", { headers: { Accept: "application/json" } });
    if (!response.ok) return false;
    const data = await response.json();
    state.token = String(data.token || "");
    return Boolean(state.token);
  } catch (error) {
    return false;
  }
}

async function api(method, path, body) {
  const options = {
    method,
    headers: { Accept: "application/json", "X-Dictation-Token": state.token },
  };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const error = new Error(data.error || `${method} ${path} failed (${response.status})`);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

// -- local fallback ---------------------------------------------------------

function localKey(suffix) {
  return `${STORAGE_PREFIX}${state.exam ? state.exam.examId : "none"}:${suffix}`;
}

function loadLocal(suffix, fallback) {
  try {
    const raw = window.localStorage.getItem(localKey(suffix));
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    return fallback;
  }
}

function saveLocal(suffix, value) {
  try {
    window.localStorage.setItem(localKey(suffix), JSON.stringify(value));
  } catch (error) {
    /* private mode, quota — the session still works, it just will not persist */
  }
}

// ---------------------------------------------------------------------------
// Exam access helpers
// ---------------------------------------------------------------------------

function* walkQuestions(exam) {
  for (const section of exam.sections || []) {
    for (const part of section.parts || []) {
      for (const question of part.questions || []) {
        yield { section, part, question };
      }
    }
  }
}

function scorableQuestions(exam) {
  return Array.from(walkQuestions(exam)).filter((entry) => !entry.question.example);
}

function passagesFor(part, question) {
  const ids = new Set(question.passageIds || []);
  return (part.passages || []).filter((passage) => ids.has(passage.id));
}

function reviewFor(questionId) {
  return state.review[questionId] || null;
}

// ---------------------------------------------------------------------------
// Home view
// ---------------------------------------------------------------------------

async function loadHome() {
  el.status.textContent = "正在读取题库…";
  el.status.classList.remove("is-error");
  clear(el.list);
  try {
    const data = state.api ? await api("GET", "./api/exams") : { exams: [] };
    state.exams = data.exams || [];
  } catch (error) {
    state.exams = [];
    el.status.textContent = `读取题库失败：${error.message}`;
    el.status.classList.add("is-error");
    return;
  }

  if (!state.api) {
    el.status.textContent = "未连接本地服务，题库需要通过 start_dictation.py 启动后访问。";
    el.status.classList.add("is-error");
  }

  renderHome();
}

function levelOf(summary) {
  const value = String(summary.level || "").trim().toUpperCase();
  return value || NO_LEVEL;
}

/** Levels that actually have papers, in canonical order. */
function levelsPresent() {
  const seen = new Set(state.exams.map(levelOf));
  const ordered = LEVEL_ORDER.filter((level) => seen.has(level));
  const extras = [...seen].filter((level) => level !== NO_LEVEL && !LEVEL_ORDER.includes(level)).sort();
  return [...ordered, ...extras, ...(seen.has(NO_LEVEL) ? [NO_LEVEL] : [])];
}

function setLevel(level) {
  const levels = levelsPresent();
  state.level = levels.includes(level) ? level : (levels[0] || "N1");
  renderHome();
}

/* The list, its level tabs and the status line all follow from `state.level`,
 * so every entry point — first load, coming back from a paper, a #/level/N2
 * link — goes through here rather than each rebuilding the list its own way. */
function renderHome() {
  const levels = levelsPresent();
  if (!levels.includes(state.level)) state.level = levels[0] || "N1";

  renderLevelSwitch(levels);

  const shown = state.exams.filter((summary) => levelOf(summary) === state.level);

  if (state.api) {
    el.status.classList.remove("is-error");
    el.status.textContent = state.exams.length === 0
      ? "共 0 套真题。"
      : `${state.level}：${shown.length} 套真题（全部 ${state.exams.length} 套）。`;
  }

  el.empty.hidden = state.exams.length > 0;
  renderStudyModes(shown);

  clear(el.list);
  for (const summary of shown) {
    el.list.appendChild(buildExamCard(summary));
  }
}

/* The two ways to study a level. They are genuinely different actions — sit one
 * paper under the clock, or drill one question type across every paper — so they
 * get a choice of their own rather than being two settings on a list. */
function renderStudyModes(shown) {
  if (!el.studyModeGrid) return;
  const usable = shown.filter((summary) => !summary.broken);
  el.studyModeGrid.hidden = state.exams.length === 0;

  if (el.mockStat) {
    el.mockStat.textContent = usable.length
      ? `${usable.length} 套可考`
      : "这个等级还没有可用的卷子";
  }
  if (el.topicStat) {
    const topics = topicsFor(usable);
    el.topicStat.textContent = topics.length
      ? `${topics.length} 个题型 · 共 ${topics.reduce((n, t) => n + t.count, 0)} 题`
      : "这个等级还没有可练的题型";
  }
  if (el.modeCardMock) el.modeCardMock.disabled = usable.length === 0;
  if (el.modeCardTopic) el.modeCardTopic.disabled = usable.length === 0;
}

/** Papers of the current filter that are actually openable. */
function usableExams() {
  const shown = state.exams.filter((summary) => levelOf(summary) === state.level);
  return shown.filter((summary) => !summary.broken);
}

/* Question types, merged across papers by section title.
 *
 * Section ids are per-paper (`s1`, `s2`, …) and collide, so the title is the key:
 * every N1 paper spells 聴解 the same way, which is what makes one drill out of
 * twenty papers possible without a lookup table to maintain. */
function topicsFor(summaries) {
  const groups = new Map();
  for (const summary of summaries) {
    for (const section of summary.sections || []) {
      const key = String(section.title || "").trim();
      if (!key) continue;
      const group = groups.get(key) || {
        key,
        title: key,
        kind: section.kind || "",
        audioRequired: Boolean(section.audioRequired),
        count: 0,
        papers: [],
      };
      group.count += Number(section.questionCount) || 0;
      group.papers.push(summary.slug);
      groups.set(key, group);
    }
  }
  return [...groups.values()];
}

// ---------------------------------------------------------------------------
// 整套计时练习 — the level's whole papers
// ---------------------------------------------------------------------------

function openPapers() {
  const usable = usableExams();
  if (el.papersMeta) {
    el.papersMeta.textContent = `${state.level} · ${usable.length} 套真题`;
  }
  show(el.viewPapers);
}

// ---------------------------------------------------------------------------
// 专题练习 — one question type, merged across the level's papers
// ---------------------------------------------------------------------------

function openTopics() {
  const usable = usableExams();
  const topics = topicsFor(usable);
  if (el.topicsMeta) {
    el.topicsMeta.textContent = `${state.level} · ${usable.length} 套卷合并`;
  }
  if (el.topicStatus) {
    el.topicStatus.textContent = "";
    el.topicStatus.classList.remove("is-error");
  }

  clear(el.topicList);
  for (const topic of topics) {
    el.topicList.appendChild(buildTopicCard(topic, usable));
  }
  show(el.viewTopics);
}

function buildTopicCard(topic, usable) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "topic-card";

  const kind = document.createElement("span");
  kind.className = topic.audioRequired ? "topic-card-kind is-audio" : "topic-card-kind";
  kind.textContent = topic.audioRequired ? "🔊 听力" : "📖 笔试";
  card.appendChild(kind);

  const title = document.createElement("h2");
  title.className = "topic-card-title";
  title.textContent = topic.title;
  card.appendChild(title);

  const facts = document.createElement("p");
  facts.className = "topic-card-facts";
  facts.textContent = `${topic.count} 题 · 来自 ${topic.papers.length} 套卷`;
  card.appendChild(facts);

  const go = document.createElement("span");
  go.className = "topic-card-go";
  go.textContent = "选题型 →";
  card.appendChild(go);

  card.addEventListener("click", () => { openTopicParts(topic, usable); });
  return card;
}

/* Building the breakdown needs every paper's full JSON — the summaries carry
 * section headlines but not the questions. Forty-odd papers is about five
 * megabytes over localhost, so it is fetched on demand with a running count and
 * then kept for the rest of the session. */
async function loadLevelPapers(slugs, onProgress) {
  const loaded = [];
  for (const [index, slug] of slugs.entries()) {
    const cached = state.loadedPapers.get(slug);
    if (cached) {
      loaded.push({ slug, exam: cached });
      continue;
    }
    onProgress(index + 1, slugs.length);
    try {
      const data = await api("GET", `./api/exams/${encodeURIComponent(slug)}`);
      state.loadedPapers.set(slug, data.exam);
      loaded.push({ slug, exam: data.exam });
    } catch (error) {
      // One unopenable paper must not sink the whole drill; it just contributes
      // nothing, exactly as it does to the paper list.
      console.warn(`skipping ${slug}: ${error.message}`);
    }
  }
  return loaded;
}

/* The fourth level: inside 言語知識 / 読解 / 聴解, split by question type.
 *
 * Grouped by `part.kind`, never by 問題 number. The number moves between paper
 * formats — 词汇填空 is 問題2 on an N1 paper and 問題4 on an N2 one — so grouping
 * by number would file the same drill under two headings and mix two drills under
 * one. `kind` is the format-independent identity; `localTitle` is its label.
 */
async function openTopicParts(topic, usable) {
  if (!state.api) {
    setTopicStatus("专题练习需要本地服务，请通过 start_dictation.py 启动。", true);
    return;
  }

  const slugs = usable
    .filter((summary) => (summary.sections || []).some((s) => String(s.title || "").trim() === topic.key))
    .map((summary) => summary.slug);

  setTopicStatus(`正在读取 ${slugs.length} 套卷…`, false);
  const loaded = await loadLevelPapers(slugs, (done, total) => {
    setTopicStatus(`正在读取第 ${done} / ${total} 套卷…`, false);
  });
  setTopicStatus("", false);

  if (loaded.length === 0) {
    setTopicStatus("没有一套卷子能打开，专题练习无法开始。", true);
    return;
  }

  state.activeTopic = { topic, loaded };
  renderParts(topic, loaded);
  show(el.viewParts);
}

/** Question types inside one section, merged across papers by `kind`. */
function partKindsFor(loaded, topicKey) {
  const groups = new Map();
  for (const { slug, exam } of loaded) {
    for (const section of exam.sections || []) {
      if (String(section.title || "").trim() !== topicKey) continue;
      for (const part of section.parts || []) {
        const key = part.kind || part.localTitle || part.title || "";
        if (!key) continue;
        const group = groups.get(key) || {
          kind: key,
          title: part.localTitle || part.title || key,
          numbers: new Set(),
          papers: new Set(),
          count: 0,
        };
        group.numbers.add(part.number);
        group.papers.add(slug);
        group.count += (part.questions || []).filter((q) => !q.example).length;
        groups.set(key, group);
      }
    }
  }
  return [...groups.values()].sort((a, b) => b.count - a.count);
}

function renderParts(topic, loaded) {
  const kinds = partKindsFor(loaded, topic.key);
  const total = kinds.reduce((n, k) => n + k.count, 0);

  if (el.partsHeading) el.partsHeading.textContent = topic.title;
  if (el.partsMeta) {
    el.partsMeta.textContent =
      `${state.level} · ${total} 题 · 来自 ${loaded.length} 套卷`;
  }
  if (el.partsStatus) {
    el.partsStatus.textContent = "";
    el.partsStatus.classList.remove("is-error");
  }

  clear(el.partsList);
  el.partsList.appendChild(buildPartCard(topic, {
    kind: "",
    title: `全部${topic.title}`,
    count: total,
    papers: new Set(loaded.map((item) => item.slug)),
    numbers: new Set(),
  }, true));
  for (const group of kinds) {
    el.partsList.appendChild(buildPartCard(topic, group, false));
  }
}

function buildPartCard(topic, group, isAll) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = isAll ? "topic-card is-all" : "topic-card";

  const kind = document.createElement("span");
  kind.className = topic.audioRequired ? "topic-card-kind is-audio" : "topic-card-kind";
  const numbers = [...group.numbers].filter((n) => n != null).sort((a, b) => a - b);
  kind.textContent = isAll ? "整个大类" : (numbers.length ? `問題${numbers.join(" / ")}` : topic.title);
  card.appendChild(kind);

  const title = document.createElement("h2");
  title.className = "topic-card-title";
  title.textContent = group.title;
  card.appendChild(title);

  const facts = document.createElement("p");
  facts.className = "topic-card-facts";
  facts.textContent = `${group.count} 题 · 来自 ${group.papers.size} 套卷`;
  card.appendChild(facts);

  const go = document.createElement("span");
  go.className = "topic-card-go";
  go.textContent = "连续练习 →";
  card.appendChild(go);

  card.disabled = group.count === 0;
  card.addEventListener("click", () => { startDrill(topic, group); });
  return card;
}

/** Open the merged drill for one section, optionally narrowed to one question type. */
async function startDrill(topic, group) {
  const available=state.activeTopic.loaded;
  const count=Math.max(1,Math.min(available.length,Number($("#topic-paper-count").value)||available.length));
  const loaded=available.slice(-count);
  state.drillGroup=group;
  const merged = buildTopicExam(topic, loaded, group.kind);
  if (merged.exam.questionCount === 0) {
    if (el.partsStatus) {
      el.partsStatus.textContent = "这个题型下没有可练的题目。";
      el.partsStatus.classList.add("is-error");
    }
    return;
  }

  state.topic = { ...topic, slugs: loaded.map((item) => item.slug), drillTitle: group.title };
  state.questionSource = merged.source;
  state.topicAttempts = new Map();
  state.exam = merged.exam;
  state.slug = "";
  state.setup = { mode: "practice", scope: "all" };
  state.setupOrigin = "topics";

  await refreshTopicReview(state.topic.slugs);
  renderSetup();
  show(el.viewSetup);
}

async function applyTopicPaperCount(){
  if(state.activeTopic&&state.drillGroup)await startDrill(state.activeTopic.topic||state.topic,state.drillGroup);
}

function setTopicStatus(text, isError) {
  if (!el.topicStatus) return;
  el.topicStatus.textContent = text;
  el.topicStatus.classList.toggle("is-error", Boolean(isError));
}

/* A synthetic exam that the rest of the page cannot tell from a real one.
 *
 * Everything downstream — the queue builder, the question renderer, the answer
 * sheet, the report — already works off "an exam", so the merge happens here and
 * nothing else has to learn about topics. Parts keep their own passages and get
 * their paper's label, so a 読解 passage still belongs to the right question and
 * the learner can see which sitting a question came from. */
/** The question type's own name, taken from the parts that survived the filter. */
function labelFor(parts) {
  const first = parts[0];
  if (!first) return "";
  // localTitle carries the paper label prefix by now, so read the source field.
  return first.kindLabel || "";
}

function buildTopicExam(topic, loaded, kindFilter = "") {
  const source = new Map();
  const parts = [];
  let sectionKind = topic.kind || "";
  let audioRequired = Boolean(topic.audioRequired);

  for (const { slug, exam } of loaded) {
    const label = exam.sessionLabel || exam.title || slug;
    for (const section of exam.sections || []) {
      if (String(section.title || "").trim() !== topic.key) continue;
      sectionKind = section.kind || sectionKind;
      audioRequired = audioRequired || Boolean(section.audioRequired);
      for (const part of section.parts || []) {
        // An empty filter means the whole section.
        if (kindFilter && (part.kind || part.localTitle || part.title || "") !== kindFilter) continue;
        parts.push({
          ...part,
          kindLabel: part.localTitle || part.title || "",
          // Part ids are per-paper too, and the answer sheet groups by them.
          id: `${slug}::${part.id}`,
          localTitle: `${label}　${part.localTitle || ""}`.trim(),
        });
        for (const question of part.questions || []) source.set(question.id, slug);
      }
    }
  }

  const scorable = parts.reduce(
    (total, part) => total + (part.questions || []).filter((q) => !q.example).length,
    0,
  );
  const points = parts.reduce(
    (total, part) => total + (part.questions || [])
      .filter((q) => !q.example)
      .reduce((sum, q) => sum + (Number(q.points) || 1), 0),
    0,
  );

  const drillLabel = kindFilter ? (labelFor(parts) || kindFilter) : "";

  return {
    source,
    exam: {
      examId: `topic:${state.level}:${topic.key}${kindFilter ? `:${kindFilter}` : ""}`,
      title: [state.level, topic.title, drillLabel]
        .filter(Boolean)
        .join(" · "),
      level: state.level,
      sessionLabel: "专题练习",
      questionCount: scorable,
      totalPoints: points,
      durationSec: 0,
      sections: [{
        id: "topic",
        title: topic.title,
        localTitle: topic.title,
        kind: sectionKind,
        questionCount: scorable,
        audioRequired,
        parts,
      }],
    },
  };
}

/** Review state for a merged exam is every source paper's, flatly combined. */
async function refreshTopicReview(slugs) {
  state.attempts = [];
  state.stats = null;
  state.review = {};
  const results = await Promise.all(slugs.map(async (slug) => {
    try {
      const data = await api("GET", `./api/exams/${encodeURIComponent(slug)}/review`);
      return (data.review || {}).questions || {};
    } catch {
      return {};
    }
  }));
  // Question ids are globally unique, so a flat merge cannot lose a record.
  for (const questions of results) Object.assign(state.review, questions);
}

function clearTopic() {
  state.topic = null;
  state.questionSource = null;
  state.topicAttempts = null;
}

function isTopicSession() {
  return Boolean(state.questionSource);
}

/** Which paper a question belongs to — itself, or the only one there is. */
function slugForQuestion(questionId) {
  if (!state.questionSource) return state.slug;
  return state.questionSource.get(questionId) || "";
}

function renderLevelSwitch(levels) {
  if (!el.levelSwitch) return;
  clear(el.levelSwitch);

  // Shown as soon as there is anything to classify, even when every paper is the
  // same level: the tab rail is how a learner discovers the level dimension
  // exists, and it fills itself in as other levels get imported.
  el.levelSwitch.hidden = state.exams.length === 0;
  if (el.levelSwitch.hidden) return;

  const counts = new Map();
  for (const summary of state.exams) {
    counts.set(levelOf(summary), (counts.get(levelOf(summary)) || 0) + 1);
  }

  const tabs = levels.map((l) => [l, l, counts.get(l) || 0]);
  for (const [id, label, count] of tabs) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `category-tab${state.level === id ? " is-active" : ""}`;
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", String(state.level === id));

    const text = document.createElement("span");
    text.className = "category-label";
    text.textContent = label;
    button.appendChild(text);

    const badge = document.createElement("span");
    badge.className = "tab-badge";
    badge.textContent = String(count);
    button.appendChild(badge);

    button.addEventListener("click", () => {
      location.hash = `#/level/${id}`;
      setLevel(id);
    });
    el.levelSwitch.appendChild(button);
  }
}

function buildExamCard(summary) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "exam-card";

  const level = document.createElement("span");
  level.className = "exam-card-level";
  level.textContent = summary.level || "JLPT";
  card.appendChild(level);

  const title = document.createElement("h2");
  title.className = "exam-card-title";
  title.textContent = summary.title || summary.slug;
  card.appendChild(title);

  if (summary.broken) {
    const facts = document.createElement("p");
    facts.className = "exam-card-facts";
    facts.textContent = summary.error
      ? `这套题读取失败：${summary.error}`
      : `这套题未通过质量检查（${(summary.quality || {}).errors || 0} 项错误），已停用。`;
    card.appendChild(facts);
    card.disabled = true;
    return card;
  }

  const facts = document.createElement("p");
  facts.className = "exam-card-facts";
  const bits = [
    `${summary.questionCount} 题`,
    `${summary.totalPoints} 分`,
  ];
  if (summary.durationSec) bits.push(`${Math.round(summary.durationSec / 60)} 分钟`);
  for (const bit of bits) {
    const span = document.createElement("span");
    span.textContent = bit;
    facts.appendChild(span);
  }
  card.appendChild(facts);

  const sections = document.createElement("div");
  sections.className = "exam-card-sections";
  for (const section of summary.sections || []) {
    const chip = document.createElement("span");
    chip.className = section.audioRequired ? "section-chip is-audio" : "section-chip";
    chip.textContent = `${section.title}（${section.questionCount}）`;
    sections.appendChild(chip);
  }
  card.appendChild(sections);

  const stats = document.createElement("div");
  stats.className = "exam-card-stats";
  stats.textContent = "点击选择练习方式";
  card.appendChild(stats);

  card.addEventListener("click", () => { openExam(summary.slug); });
  return card;
}

// ---------------------------------------------------------------------------
// Setup view
// ---------------------------------------------------------------------------

async function openExam(slug) {
  el.status.textContent = "正在载入试卷…";
  try {
    const data = await api("GET", `./api/exams/${encodeURIComponent(slug)}`);
    clearTopic();
    state.exam = data.exam;
    state.slug = slug;
  } catch (error) {
    el.status.textContent = `载入失败：${error.message}`;
    el.status.classList.add("is-error");
    return;
  }
  el.status.textContent = "";
  state.setupOrigin = "papers";
  await refreshProgress();
  renderSetup();
  show(el.viewSetup);
}

async function refreshProgress() {
  if (!state.api || !state.exam) {
    state.review = loadLocal("review", {});
    state.attempts = loadLocal("attempts", []);
    state.stats = null;
    return;
  }
  try {
    const [review, stats, attempts] = await Promise.all([
      api("GET", `./api/exams/${encodeURIComponent(state.slug)}/review`),
      api("GET", `./api/exams/${encodeURIComponent(state.slug)}/stats`),
      api("GET", `./api/exams/${encodeURIComponent(state.slug)}/attempts?limit=8`),
    ]);
    state.review = (review.review || {}).questions || {};
    state.stats = stats.stats || null;
    state.attempts = attempts.attempts || [];
  } catch (error) {
    state.review = {};
    state.stats = null;
    state.attempts = [];
  }
}

function scopeOptions() {
  const exam = state.exam;
  const options = [{ id: "all", label: `全卷（${exam.questionCount - countExamples()} 题）`, count: exam.questionCount - countExamples() }];

  for (const section of exam.sections || []) {
    const count = scorableQuestions(exam).filter((entry) => entry.section.id === section.id).length;
    options.push({ id: `section:${section.id}`, label: `${section.title}（${count}）`, count });
  }
  for (const section of exam.sections || []) {
    for (const part of section.parts || []) {
      const count = (part.questions || []).filter((question) => !question.example).length;
      options.push({
        id: `part:${part.id}`,
        label: `${section.kind === "listening" ? "听力" : ""}問題${part.number} ${part.localTitle || ""}（${count}）`,
        count,
      });
    }
  }

  const wrong = scorableQuestions(exam).filter((entry) => {
    const record = reviewFor(entry.question.id);
    return record && (record.lastResult === "wrong" || record.lastResult === "skipped" || record.lastResult === "guessed");
  }).length;
  const due = scorableQuestions(exam).filter((entry) => {
    const record = reviewFor(entry.question.id);
    return record && record.due;
  }).length;
  const marked = scorableQuestions(exam).filter((entry) => {
    const record = reviewFor(entry.question.id);
    return record && record.marked;
  }).length;

  options.push({ id: "wrong", label: `错题与蒙对（${wrong}）`, count: wrong });
  options.push({ id: "due", label: `今天该复习（${due}）`, count: due });
  options.push({ id: "marked", label: `已标记（${marked}）`, count: marked });
  return options;
}

function countExamples() {
  return Array.from(walkQuestions(state.exam)).filter((entry) => entry.question.example).length;
}

function renderSetup() {
  const countLabel=$("#topic-paper-count-label");countLabel.hidden=!isTopicSession();
  if(isTopicSession()){
    const selector=$("#topic-paper-count"),chosen=selector.value;clear(selector);
    for(let i=1;i<=(state.activeTopic?.loaded.length||1);i++){const option=document.createElement("option");option.value=String(i);option.textContent=String(i);selector.append(option);}
    selector.value=chosen||String(state.activeTopic?.loaded.length||1);
  }
  const exam = state.exam;
  el.brandTitle.textContent = exam.title;
  el.brandSub.textContent = `${exam.level} · ${exam.sessionLabel || ""}`.trim();

  const scorable = scorableQuestions(exam).length;
  const audio = (exam.sections || []).filter((section) => section.audioRequired).length;
  el.setupMeta.textContent =
    `共 ${scorable} 道计分题、${exam.totalPoints} 分` +
    (audio ? `。其中听力部分没有配套音频，只能对照答案复习。` : "。");

  clear(el.modeGrid);
  for (const mode of MODES) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mode-option";
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", String(state.setup.mode === mode.id));
    const strong = document.createElement("strong");
    strong.textContent = mode.title;
    const span = document.createElement("span");
    span.textContent = mode.detail;
    button.appendChild(strong);
    button.appendChild(span);
    button.addEventListener("click", () => {
      state.setup.mode = mode.id;
      if (mode.id === "review" && !state.setup.scope.startsWith("wrong")) state.setup.scope = "wrong";
      if (mode.id !== "review" && ["wrong", "due", "marked"].includes(state.setup.scope)) state.setup.scope = "all";
      renderSetup();
    });
    el.modeGrid.appendChild(button);
  }

  clear(el.scopeGrid);
  for (const scope of scopeOptions()) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "scope-option";
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", String(state.setup.scope === scope.id));
    button.textContent = scope.label;
    button.disabled = scope.count === 0;
    button.addEventListener("click", () => {
      state.setup.scope = scope.id;
      renderSetup();
    });
    el.scopeGrid.appendChild(button);
  }

  const selected = scopeOptions().find((scope) => scope.id === state.setup.scope);
  const count = selected ? selected.count : 0;
  el.startButton.disabled = count === 0;
  el.setupHint.textContent = count
    ? `将练习 ${count} 道题` + (state.setup.mode === "exam" ? `，限时 ${Math.round(examDuration(count) / 60)} 分钟` : "")
    : "这个范围下暂时没有题目";

  // A merged drill belongs to no single paper: there is nothing to reset, and
  // the history list is per-paper.
  el.resetProgress.hidden = isTopicSession();
  renderHistory();
}

function examDuration(questionCount) {
  const exam = state.exam;
  const total = scorableQuestions(exam).length || 1;
  const full = Number(exam.durationSec) || 10800;
  return Math.max(300, Math.round((full * questionCount) / total));
}

function renderHistory() {
  const attempts = (state.attempts || []).filter((attempt) => !attempt.abandonedAt);
  el.historyBlock.hidden = attempts.length === 0;
  clear(el.historyList);
  for (const attempt of attempts) {
    const item = document.createElement("li");
    const when = document.createElement("span");
    when.textContent = new Date(attempt.startedAt).toLocaleString();
    const mode = document.createElement("span");
    const modeInfo = MODES.find((entry) => entry.id === attempt.mode);
    mode.textContent = modeInfo ? modeInfo.title : attempt.mode;
    const scope = document.createElement("span");
    scope.textContent = attempt.scope || "全卷";
    const score = document.createElement("span");
    score.className = "history-score";
    const totals = attempt.totals || {};
    score.textContent = `${totals.earned ?? 0} / ${totals.points ?? 0} 分（${totals.percent ?? 0}%）`;
    item.append(when, mode, scope, score);
    if(!attempt.finishedAt){
      score.textContent="尚未完成";
      const resume=document.createElement("button");resume.textContent="继续作答";resume.type="button";
      resume.addEventListener("click",()=>resumeAttempt(attempt.id).catch(e=>toast(e.message)));
      const abandon=document.createElement("button");abandon.textContent="放弃本次";abandon.type="button";
      abandon.addEventListener("click",()=>abandonAttempt(attempt.id).catch(e=>toast(e.message)));
      item.append(resume,abandon);
    }
    el.historyList.appendChild(item);
  }
}

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

function buildQueue(scope) {
  const exam = state.exam;
  const all = scorableQuestions(exam);
  if (scope === "all") return all;
  if (scope.startsWith("section:")) {
    const id = scope.slice("section:".length);
    return all.filter((entry) => entry.section.id === id);
  }
  if (scope.startsWith("part:")) {
    const id = scope.slice("part:".length);
    return all.filter((entry) => entry.part.id === id);
  }
  if (scope === "wrong") {
    return all.filter((entry) => {
      const record = reviewFor(entry.question.id);
      return record && ["wrong", "skipped", "guessed"].includes(record.lastResult);
    });
  }
  if (scope === "due") {
    return all.filter((entry) => {
      const record = reviewFor(entry.question.id);
      return record && record.due;
    });
  }
  if (scope === "marked") {
    return all.filter((entry) => {
      const record = reviewFor(entry.question.id);
      return record && record.marked;
    });
  }
  return all;
}

function scopeLabel(scope) {
  const option = scopeOptions().find((entry) => entry.id === scope);
  return option ? option.label.replace(/（\d+）$/, "") : scope;
}

async function resumeAttempt(id){
  const {attempt}=await api("GET",`./api/exam-attempts/${encodeURIComponent(id)}`);
  if(attempt.finishedAt||attempt.abandonedAt)throw new Error("本次作答已结束。");
  await teardownSession();
  const selected=new Set(attempt.questionIds||[]);
  const queue=scorableQuestions(state.exam).filter(e=>!selected.size||selected.has(e.question.id));
  const answers=new Map(attempt.answers.map(a=>[a.questionId,{...a,revealed:false}]));
  const start=Date.parse(attempt.startedAt);
  state.session={mode:attempt.mode,scope:attempt.scope,scopeText:attempt.scope,queue,
    index:Math.max(0,queue.findIndex(e=>!answers.has(e.question.id))),answers,attemptId:id,
    startedAt:start,questionShownAt:Date.now(),deadline:attempt.mode==="exam"?start+examDuration(queue.length)*1000:0,submitted:false};
  el.totalCount.textContent=String(queue.length);startTimer();renderQuestion();renderAnswerSheet();show(el.viewSession);
}
async function abandonAttempt(id){
  if(!confirm("放弃这次未完成作答？已保存的记录会保留。"))return;
  await api("POST",`./api/exam-attempts/${encodeURIComponent(id)}/abandon`,{});
  state.attempts=(await api("GET",`./api/exams/${encodeURIComponent(state.slug)}/attempts`)).attempts;renderHistory();
}
async function teardownSession(){
  stopTimer();
  await flushAnswers();
  if(state.pendingAnswers.size)throw new Error("作答尚未保存，请重试后退出。");
  state.session = null;
}
async function exitSession(){
  await teardownSession();
  if(state.api&&!isTopicSession())state.attempts=(await api("GET",`./api/exams/${encodeURIComponent(state.slug)}/attempts`)).attempts;
  renderSetup();
  show(el.viewSetup);
}

async function startSession() {
  const { mode, scope } = state.setup;
  const queue = buildQueue(scope);
  if (!queue.length) {
    toast("这个范围下没有题目");
    return;
  }
  await beginSession(mode, scope, scopeLabel(scope), queue);
}

/** Open a session over a ready-made queue.
 *
 * Every entry point goes through here, including "review this one question" from
 * the report. That matters: an attempt already has a score written, so recording
 * further answers against its id would leave a stored sitting whose answers no
 * longer add up to its own score. A new queue always means a new attempt.
 */
async function beginSession(mode, scope, scopeText, queue) {
  // Stop the previous clock before the await, not after: a tick landing in the gap
  // would otherwise still belong to a session that is on its way out.
  stopTimer();
  await flushAnswers();

  state.session = {
    mode,
    scope,
    scopeText,
    queue,
    index: 0,
    answers: new Map(),
    attemptId: "",
    startedAt: Date.now(),
    questionShownAt: Date.now(),
    deadline: mode === "exam" ? Date.now() + examDuration(queue.length) * 1000 : 0,
    submitted: false,
  };

  // A topic drill spans papers, so it has no single attempt to open here; one is
  // created per source paper the first time a question from it is answered.
  if (state.api && !isTopicSession()) {
    try {
      const data = await api("POST", `./api/exams/${encodeURIComponent(state.slug)}/attempts`, {
        mode,
        scope: scopeText,
        // Send the queue so the stored score is out of what this sitting actually
        // asked, not out of the whole paper: a clean round of 問題1 should read
        // 6/6 in the history list, not 6/176.
        questionIds: queue.map((entry) => entry.question.id),
      });
      state.session.attemptId = data.attempt.id;
    } catch (error) {
      toast(`无法记录本次作答：${error.message}`);
    }
  }

  el.totalCount.textContent = String(queue.length);
  startTimer();
  renderQuestion();
  renderAnswerSheet();
  show(el.viewSession);
}

// The live interval id lives here rather than on the session object. It used to be
// `state.session.timerId`, which leaked: beginSession() replaces state.session and
// only then calls startTimer(), so the stopTimer() at the top of startTimer() read
// the *new* session's id (0) and left the previous interval running. Two clocks then
// wrote to the same display, and — worse — when the abandoned exam-mode session's
// deadline passed, its tick auto-submitted whatever session was current by then.
let timerHandle = 0;

function startTimer() {
  stopTimer();
  const session = state.session;
  el.timer.hidden = false;
  const tick = () => {
    // Belt and braces for the same failure: a tick that outlives its session does
    // nothing at all, rather than driving someone else's clock.
    if (!state.session || state.session !== session) return;
    if (session.mode === "exam") {
      const remaining = (session.deadline - Date.now()) / 1000;
      el.timerValue.textContent = formatClock(remaining);
      el.timer.classList.toggle("is-urgent", remaining <= 300);
      if (remaining <= 0) {
        toast("时间到，已自动交卷");
        submitSession();
        return;
      }
    } else {
      el.timerValue.textContent = formatClock((Date.now() - session.startedAt) / 1000);
    }
  };
  tick();
  timerHandle = window.setInterval(tick, 1000);
}

function stopTimer() {
  if (timerHandle) {
    window.clearInterval(timerHandle);
    timerHandle = 0;
  }
  el.timer.classList.remove("is-urgent");
}

function currentEntry() {
  const session = state.session;
  return session ? session.queue[session.index] : null;
}

function answerFor(questionId) {
  const session = state.session;
  if (!session.answers.has(questionId)) {
    session.answers.set(questionId, { chosen: null, confidence: "", revealed: false, elapsedMs: 0 });
  }
  return session.answers.get(questionId);
}

function renderQuestion() {
  const session = state.session;
  const entry = currentEntry();
  if (!entry) return;
  const { section, part, question } = entry;
  const answer = answerFor(question.id);
  const immediate = session.mode === "review";
  const revealed = immediate && answer.revealed;

  session.questionShownAt = Date.now();

  el.brandTitle.textContent = state.exam.title;
  el.brandSub.textContent = `${MODES.find((m) => m.id === session.mode).title} · ${session.scopeText}`;
  el.questionBadge.textContent = `第 ${session.index + 1} / ${session.queue.length} 题`;
  el.questionPart.textContent =
    `${section.title} · 問題${part.number} ${part.localTitle || ""} · 答题卡 ${question.answerSheetLabel} · ${question.points} 分`;

  el.partInstruction.textContent = plainText(part.instruction || "");
  el.partInstruction.hidden = !part.instruction;

  el.audioWarning.hidden = !section.audioRequired;

  clear(el.questionPrompt);
  el.questionPrompt.className = "question-prompt jp";
  if (question.prompt) renderInline(question.prompt, el.questionPrompt);

  if (question.figureNote) {
    el.questionFigure.hidden = false;
    el.questionFigure.textContent = question.figureNote;
  } else {
    el.questionFigure.hidden = true;
  }

  renderPassages(part, question);
  renderChoices(entry, answer, revealed);
  renderConfidence(answer, revealed);
  renderVerdict(entry, answer, revealed);
  renderMark(question);

  el.prevButton.disabled = session.index === 0;
  el.nextButton.disabled = session.index >= session.queue.length - 1;
  el.revealButton.hidden = !immediate || revealed;
  el.submitButton.hidden = false;
  el.submitButton.textContent = session.mode === "exam" ? "交卷" : "结束并查看报告";

  updateProgressChip();
  renderAnswerSheet();
}

function renderPassages(part, question) {
  const passages = passagesFor(part, question);
  clear(el.passageScroll);
  if (!passages.length) {
    el.passagePane.hidden = true;
    el.sessionLayout.classList.remove("has-passage");
    return;
  }
  el.passagePane.hidden = false;
  el.sessionLayout.classList.add("has-passage");
  el.passageLabel.textContent = passages.length > 1 ? "阅读材料（A・B）" : "阅读材料";

  for (const passage of passages) {
    const block = document.createElement("div");
    block.className = "passage-block";
    if (passage.label) {
      const label = document.createElement("span");
      label.className = "passage-block-label";
      label.textContent = passage.label;
      block.appendChild(label);
    }
    const body = document.createElement("div");
    body.className = passage.vertical ? "jp is-vertical" : "jp";
    renderBlocks(passage.text, body);
    block.appendChild(body);

    if ((passage.notes || []).length) {
      const notes = document.createElement("div");
      notes.className = "passage-notes jp";
      for (const note of passage.notes) {
        const paragraph = document.createElement("p");
        renderInline(note, paragraph);
        notes.appendChild(paragraph);
      }
      block.appendChild(notes);
    }
    el.passageScroll.appendChild(block);
  }
  el.passageScroll.scrollTop = 0;
}

function renderChoices(entry, answer, revealed) {
  const { question } = entry;
  clear(el.choices);
  const count = question.choicesSpoken ? question.choiceCount : (question.choices || []).length;

  for (let number = 1; number <= count; number += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "choice jp";
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", String(answer.chosen === number));

    const badge = document.createElement("span");
    badge.className = "choice-number";
    badge.textContent = String(number);
    button.appendChild(badge);

    const body = document.createElement("span");
    body.className = "choice-body";
    if (question.choicesSpoken) {
      body.textContent = `选项 ${number}（录音朗读，试卷上未印出）`;
      body.style.color = "var(--muted)";
    } else {
      renderInline(question.choices[number - 1], body);
    }
    button.appendChild(body);

    if (revealed) {
      button.disabled = true;
      if (number === question.answer) {
        button.classList.add("is-correct");
        const tag = document.createElement("span");
        tag.className = "choice-verdict";
        tag.textContent = "正确答案";
        button.appendChild(tag);
      } else if (number === answer.chosen) {
        button.classList.add("is-wrong");
        const tag = document.createElement("span");
        tag.className = "choice-verdict";
        tag.textContent = "你的选择";
        button.appendChild(tag);
      }
    } else {
      button.addEventListener("click", () => choose(number));
    }
    el.choices.appendChild(button);
  }
}

function renderConfidence(answer, revealed) {
  const immediate = state.session.mode !== "exam";
  el.confidenceRow.hidden = !immediate;
  clear(el.confidenceButtons);
  if (!immediate) return;
  for (const option of CONFIDENCE) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "confidence-button";
    button.setAttribute("aria-pressed", String(answer.confidence === option.id));
    button.textContent = option.label;
    button.disabled = revealed;
    button.addEventListener("click", () => {
      answer.confidence = answer.confidence === option.id ? "" : option.id;
      renderConfidence(answer, revealed);
    });
    el.confidenceButtons.appendChild(button);
  }
}

function renderVerdict(entry, answer, revealed) {
  const { question, part } = entry;
  el.verdict.hidden = !revealed;
  if (!revealed) return;

  const correct = answer.chosen !== null && answer.chosen === question.answer;
  const skipped = answer.chosen === null;
  el.verdictBadge.className = `verdict-badge ${correct ? "is-correct" : skipped ? "is-skipped" : "is-wrong"}`;
  el.verdictBadge.textContent = correct ? "答对了" : skipped ? "未作答" : "答错了";
  el.verdictDetail.textContent = correct
    ? (answer.confidence === "guess" ? "蒙对的题仍然会留在复习队列里。" : `正确答案是 ${question.answer}。`)
    : `正确答案是 ${question.answer}${skipped ? "" : `，你选了 ${answer.chosen}`}。`;

  // The published keys are 非标准答案. Where one is contested, say so at exactly the
  // moment the learner is being marked against it, rather than burying it in a doc.
  el.keyNote.hidden = !question.keyNote;
  el.keyNote.textContent = question.keyNote || "";

  const order = question.answerOrder;
  if (part.kind === "sentence-composition" && Array.isArray(order) && !question.choicesSpoken) {
    el.orderAnswer.hidden = false;
    clear(el.orderList);
    order.forEach((fragment, position) => {
      const item = document.createElement("li");
      item.className = position === 2 ? "jp is-star" : "jp";
      const number = document.createElement("span");
      number.className = "choice-number";
      number.textContent = String(fragment);
      item.appendChild(number);
      const body = document.createElement("span");
      renderInline(question.choices[fragment - 1] || "", body);
      item.appendChild(body);
      if (position === 2) item.appendChild(document.createTextNode(" ★"));
      el.orderList.appendChild(item);
    });
  } else {
    el.orderAnswer.hidden = true;
  }

  const record = reviewFor(question.id);
  el.questionNote.value = record ? record.note || "" : "";
}

function renderMark(question) {
  const record = reviewFor(question.id);
  const marked = Boolean(record && record.marked);
  el.markButton.setAttribute("aria-pressed", String(marked));
  el.markButton.textContent = marked ? "★ 已标记" : "☆ 标记";
}

function updateProgressChip() {
  const session = state.session;
  let answered = 0;
  for (const entry of session.queue) {
    const record = session.answers.get(entry.question.id);
    if (record && record.chosen !== null) answered += 1;
  }
  el.answeredCount.textContent = String(answered);
  el.totalCount.textContent = String(session.queue.length);
}

function choose(number) {
  const session = state.session;
  const entry = currentEntry();
  if (!entry) return;
  const answer = answerFor(entry.question.id);
  answer.chosen = number;
  answer.elapsedMs = Math.max(0, Date.now() - session.questionShownAt);
  queueAnswer(entry.question.id, answer);

  if (session.mode !== "review") {
    renderChoices(entry, answer, false);
    updateProgressChip();
    renderAnswerSheet();
    return;
  }
  answer.revealed = true;
  renderQuestion();
}

function revealCurrent() {
  if(state.session?.mode!=="review")return;
  const entry = currentEntry();
  if (!entry) return;
  const answer = answerFor(entry.question.id);
  answer.revealed = true;
  if (answer.chosen === null) {
    answer.elapsedMs = Math.max(0, Date.now() - state.session.questionShownAt);
    queueAnswer(entry.question.id, answer);
  }
  renderQuestion();
}

function navigate(delta) {
  const session = state.session;
  const next = session.index + delta;
  if (next < 0 || next >= session.queue.length) return;
  session.index = next;
  renderQuestion();
}

function jumpTo(index) {
  state.session.index = index;
  renderQuestion();
  el.answerSheet.hidden = true;
  el.sheetButton.setAttribute("aria-expanded", "false");
}

// -- answer sheet -----------------------------------------------------------

function renderAnswerSheet() {
  const session = state.session;
  if (!session) return;
  clear(el.answerSheetBody);

  const groups = new Map();
  session.queue.forEach((entry, index) => {
    const key = entry.part.id;
    if (!groups.has(key)) groups.set(key, { entry, items: [] });
    groups.get(key).items.push({ entry, index });
  });

  for (const group of groups.values()) {
    const wrapper = document.createElement("div");
    const title = document.createElement("p");
    title.className = "sheet-group-title";
    title.textContent = `${group.entry.section.title} · 問題${group.entry.part.number} ${group.entry.part.localTitle || ""}`;
    wrapper.appendChild(title);

    const cells = document.createElement("div");
    cells.className = "sheet-cells";
    for (const item of group.items) {
      const question = item.entry.question;
      const answer = session.answers.get(question.id);
      const record = reviewFor(question.id);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "sheet-cell";
      button.textContent = question.answerSheetLabel;
      if (answer && answer.chosen !== null) {
        button.classList.add("is-answered");
        if (answer.revealed || session.submitted) {
          button.classList.add(answer.chosen === question.answer ? "is-correct" : "is-wrong");
        }
      } else if (answer && answer.revealed) {
        button.classList.add("is-wrong");
      }
      if (record && record.marked) button.classList.add("is-marked");
      if (item.index === session.index) button.classList.add("is-current");
      const chosen = answer && answer.chosen !== null ? ` 已选 ${answer.chosen}` : " 未作答";
      button.setAttribute("aria-label", `第 ${item.index + 1} 题，答题卡 ${question.answerSheetLabel}，${chosen}`);
      button.addEventListener("click", () => jumpTo(item.index));
      cells.appendChild(button);
    }
    wrapper.appendChild(cells);
    el.answerSheetBody.appendChild(wrapper);
  }
}

// -- persistence ------------------------------------------------------------

function queueAnswer(questionId, answer) {
  state.pendingAnswers.set(questionId, {
    questionId,
    chosen: answer.chosen,
    confidence: answer.confidence,
    elapsedMs: answer.elapsedMs,
  });
  window.clearTimeout(state.flushTimer);
  state.flushTimer = window.setTimeout(flushAnswers, 600);
}

async function flushAnswers() {
  if (!state.pendingAnswers.size) return;
  const answers = Array.from(state.pendingAnswers.values());
  state.pendingAnswers.clear();

  if (state.api && state.session && isTopicSession()) {
    await flushTopicAnswers(answers);
    return;
  }

  if (!state.api || !state.session || !state.session.attemptId) {
    const stored = loadLocal("answers", {});
    for (const answer of answers) stored[answer.questionId] = answer;
    saveLocal("answers", stored);
    applyLocalReview(answers);
    return;
  }
  try {
    await api("POST", `./api/exams/${encodeURIComponent(state.slug)}/answers`, {
      attemptId: state.session.attemptId,
      answers,
    });
  } catch (error) {
    for (const answer of answers) state.pendingAnswers.set(answer.questionId, answer);
    toast(`作答未能保存：${error.message}`);
  }
}

/* A drill's answers belong to whichever paper each question came from, so the
 * batch is split by source and posted to each paper's own endpoint. That keeps
 * one drill feeding the same 错题本 and SRS records the papers already use — the
 * merge is a study surface, not a separate store. */
async function flushTopicAnswers(answers) {
  const bySlug = new Map();
  for (const answer of answers) {
    const slug = slugForQuestion(answer.questionId);
    if (!slug) continue;
    if (!bySlug.has(slug)) bySlug.set(slug, []);
    bySlug.get(slug).push(answer);
  }

  for (const [slug, batch] of bySlug) {
    try {
      const attemptId = await ensureTopicAttempt(slug);
      await api("POST", `./api/exams/${encodeURIComponent(slug)}/answers`, {
        attemptId,
        answers: batch,
      });
    } catch (error) {
      for (const answer of batch) state.pendingAnswers.set(answer.questionId, answer);
      toast(`作答未能保存：${error.message}`);
    }
  }
}

/** One attempt per source paper, opened lazily on its first answered question. */
async function ensureTopicAttempt(slug) {
  const existing = state.topicAttempts.get(slug);
  if (existing) return existing;

  const inQueue = new Set(state.session.queue.map((entry) => entry.question.id));
  const questionIds = [...state.questionSource.entries()]
    .filter(([id, source]) => source === slug && inQueue.has(id))
    .map(([id]) => id);

  const data = await api("POST", `./api/exams/${encodeURIComponent(slug)}/attempts`, {
    mode: state.session.mode,
    scope: `专题：${state.topic ? state.topic.title : ""}`,
    questionIds,
  });
  state.topicAttempts.set(slug, data.attempt.id);
  return data.attempt.id;
}

function applyLocalReview(answers) {
  const index = new Map(Array.from(walkQuestions(state.exam)).map((entry) => [entry.question.id, entry.question]));
  for (const answer of answers) {
    const question = index.get(answer.questionId);
    if (!question) continue;
    const correct = answer.chosen !== null && answer.chosen === question.answer;
    const previous = state.review[answer.questionId] || { seen: 0, wrong: 0, streak: 0, marked: false, note: "" };
    const result = correct
      ? (answer.confidence === "guess" ? "guessed" : "correct")
      : (answer.chosen === null ? "skipped" : "wrong");
    state.review[answer.questionId] = {
      ...previous,
      seen: previous.seen + 1,
      wrong: previous.wrong + (result === "wrong" ? 1 : 0),
      streak: result === "correct" ? previous.streak + 1 : 0,
      lastChosen: answer.chosen,
      lastResult: result,
      due: result !== "correct",
    };
  }
  saveLocal("review", state.review);
}

async function toggleMark() {
  const entry = currentEntry();
  if (!entry) return;
  const question = entry.question;
  const record = state.review[question.id] || { marked: false, note: "" };
  const marked = !record.marked;
  state.review[question.id] = { ...record, marked };
  renderMark(question);
  renderAnswerSheet();

  if (!state.api) {
    saveLocal("review", state.review);
    return;
  }
  const slug = slugForQuestion(question.id);
  if (!slug) return;
  try {
    await api("POST", `./api/exams/${encodeURIComponent(slug)}/mark`, {
      questionId: question.id,
      marked,
      note: record.note || "",
    });
  } catch (error) {
    toast(`标记未保存：${error.message}`);
  }
}

function saveNoteSoon() {
  window.clearTimeout(state.noteTimer);
  state.noteTimer = window.setTimeout(async () => {
    const entry = currentEntry();
    if (!entry) return;
    const question = entry.question;
    const record = state.review[question.id] || { marked: false, note: "" };
    const note = el.questionNote.value;
    state.review[question.id] = { ...record, note };
    if (!state.api) {
      saveLocal("review", state.review);
      return;
    }
    try {
      await api("POST", `./api/exams/${encodeURIComponent(state.slug)}/mark`, {
        questionId: question.id,
        marked: Boolean(record.marked),
        note,
      });
    } catch (error) {
      toast(`笔记未保存：${error.message}`);
    }
  }, 700);
}

// ---------------------------------------------------------------------------
// Submit & report
// ---------------------------------------------------------------------------

function scoreLocally() {
  const session = state.session;
  const totals = { points: 0, earned: 0, correct: 0, wrong: 0, unanswered: 0, questions: 0 };
  const sections = new Map();
  const parts = new Map();
  const questions = [];

  for (const entry of session.queue) {
    const { section, part, question } = entry;
    const answer = session.answers.get(question.id) || { chosen: null };
    const outcome = answer.chosen === null
      ? "unanswered"
      : answer.chosen === question.answer ? "correct" : "wrong";
    const points = Number(question.points) || 0;
    const earned = outcome === "correct" ? points : 0;

    for (const [map, key, seed] of [
      [sections, section.id, { id: section.id, title: section.title, kind: section.kind }],
      [parts, part.id, { id: part.id, sectionId: section.id, number: part.number, localTitle: part.localTitle, kind: part.kind }],
    ]) {
      if (!map.has(key)) map.set(key, { ...seed, points: 0, earned: 0, correct: 0, wrong: 0, unanswered: 0, questions: 0 });
      const row = map.get(key);
      row.points += points;
      row.earned += earned;
      row[outcome] += 1;
      row.questions += 1;
    }
    totals.points += points;
    totals.earned += earned;
    totals[outcome] += 1;
    totals.questions += 1;
    questions.push({ entry, chosen: answer.chosen, outcome, points });
  }

  const percent = (row) => (row.points ? Math.round((1000 * row.earned) / row.points) / 10 : 0);
  totals.percent = percent(totals);
  const finish = (rows) => Array.from(rows.values()).map((row) => ({ ...row, percent: percent(row) }));
  return { totals, sections: finish(sections), parts: finish(parts), questions };
}

async function submitSession() {
  const session = state.session;
  if (!session || session.submitted) return;
  session.submitted = true;
  stopTimer();
  await flushAnswers();

  const local = scoreLocally();
  state.lastScore = local;

  if (state.api && isTopicSession()) {
    // Every paper this drill touched has its own open attempt; close them all, or
    // they sit unfinished forever and never show a score in that paper's history.
    const elapsedMs = Date.now() - session.startedAt;
    await Promise.all([...state.topicAttempts.entries()].map(async ([slug, attemptId]) => {
      try {
        await api("POST", `./api/exams/${encodeURIComponent(slug)}/finish`, { attemptId, elapsedMs });
      } catch (error) {
        toast(`成绩未能保存：${error.message}`);
      }
    }));
  } else if (state.api && session.attemptId) {
    try {
      await api("POST", `./api/exams/${encodeURIComponent(state.slug)}/finish`, {
        attemptId: session.attemptId,
        elapsedMs: Date.now() - session.startedAt,
      });
    } catch (error) {
      toast(`成绩未能保存：${error.message}`);
    }
  }

  if (isTopicSession()) await refreshTopicReview(state.topic.slugs);
  else await refreshProgress();
  renderReport(local);
  show(el.viewReport);
  el.timer.hidden = true;
}

function renderReport(score) {
  const session = state.session;
  const totals = score.totals;
  el.reportMeta.textContent =
    `${state.exam.title} · ${MODES.find((m) => m.id === session.mode).title} · ${session.scopeText} · ` +
    `用时 ${formatClock((Date.now() - session.startedAt) / 1000)}`;

  clear(el.scoreSummary);
  el.scoreSummary.appendChild(scoreTile("总分", `${totals.earned} / ${totals.points}`, `${totals.percent}%`, true));
  el.scoreSummary.appendChild(scoreTile("答对", String(totals.correct), `共 ${totals.questions} 题`));
  el.scoreSummary.appendChild(scoreTile("答错", String(totals.wrong), totals.unanswered ? `另有 ${totals.unanswered} 题未答` : "全部作答"));
  for (const section of score.sections) {
    el.scoreSummary.appendChild(scoreTile(section.title, `${section.earned} / ${section.points}`, `${section.percent}%`));
  }

  const note = (state.exam.source || {}).answerKeyNote || "";
  el.scoringNote.hidden = !note;
  el.scoringNote.textContent = note
    ? `计分说明：${note}`
    : "";

  clear(el.partTable);
  for (const part of score.parts) {
    const row = document.createElement("div");
    row.className = "part-row";

    const name = document.createElement("div");
    name.className = "part-row-name";
    const strong = document.createElement("strong");
    strong.textContent = `問題${part.number} ${part.localTitle || ""}`;
    const sub = document.createElement("span");
    sub.textContent = `${part.correct} / ${part.questions} 题`;
    name.append(strong, sub);

    const value = document.createElement("div");
    value.textContent = `${part.earned} / ${part.points} 分（${part.percent}%）`;

    const bar = document.createElement("div");
    bar.className = part.percent < 60 ? "part-bar is-weak" : "part-bar";
    const fill = document.createElement("i");
    fill.style.width = `${Math.max(2, part.percent)}%`;
    bar.appendChild(fill);

    row.append(name, value, bar);
    el.partTable.appendChild(row);
  }

  const missed = score.questions.filter((item) => item.outcome !== "correct");
  el.wrongBlock.hidden = missed.length === 0;
  clear(el.wrongList);
  for (const item of missed) {
    const { entry, chosen, outcome } = item;
    const button = document.createElement("button");
    button.type = "button";
    button.className = outcome === "unanswered" ? "wrong-item is-skipped jp" : "wrong-item jp";

    const head = document.createElement("div");
    head.className = "wrong-head";
    const label = document.createElement("span");
    label.textContent = `${entry.section.title} · 問題${entry.part.number} · 答题卡 ${entry.question.answerSheetLabel}`;
    const verdict = document.createElement("span");
    verdict.className = "wrong-answer";
    verdict.textContent = outcome === "unanswered"
      ? `未作答，正确答案 ${entry.question.answer}`
      : `你选 ${chosen}，正确答案 ${entry.question.answer}`;
    head.append(label, verdict);
    button.appendChild(head);

    const body = document.createElement("div");
    const prompt = entry.question.prompt
      || (entry.question.choicesSpoken ? "（听力题，题干由录音朗读）" : "");
    renderInline(prompt.slice(0, 120), body);
    button.appendChild(body);

    button.addEventListener("click", () => {
      beginSession("practice", "review-one", `复习 ${entry.question.answerSheetLabel} 题`, [entry]);
    });
    el.wrongList.appendChild(button);
  }

  el.reportReview.hidden = missed.length === 0;
}

function scoreTile(eyebrowText, value, subText, isTotal) {
  const tile = document.createElement("div");
  tile.className = isTotal ? "score-tile is-total" : "score-tile";
  const eyebrow = document.createElement("span");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = eyebrowText;
  const strong = document.createElement("strong");
  strong.textContent = value;
  tile.append(eyebrow, strong);
  if (subText) {
    const sub = document.createElement("span");
    sub.className = "sub";
    sub.textContent = subText;
    tile.appendChild(sub);
  }
  return tile;
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

function bindEvents() {
  el.homeButton.addEventListener("click", async () => {
    if (state.session && !state.session.submitted && !window.confirm("离开会结束当前练习，确定吗？")) return;
    stopTimer();
    state.session = null;
    el.timer.hidden = true;
    el.brandTitle.textContent = "JLPT 题库";
    el.brandSub.textContent = "选择一套真题开始";
    await loadHome();
    show(el.viewHome);
  });

  el.modeCardMock.addEventListener("click", () => {
    location.hash = levelHash("papers");
    openPapers();
  });
  el.modeCardTopic.addEventListener("click", () => {
    location.hash = levelHash("topics");
    openTopics();
  });
  el.papersBack.addEventListener("click", () => {
    location.hash = levelHash("");
    show(el.viewHome);
  });
  el.topicsBack.addEventListener("click", () => {
    location.hash = levelHash("");
    show(el.viewHome);
  });
  el.partsBack.addEventListener("click", () => { openTopics(); });

  el.setupBack.addEventListener("click", async () => {
    if (state.setupOrigin === "topics") {
      // Back to the question types of the section that was being drilled, not all
      // the way out to the section list.
      if (state.activeTopic) {
        renderParts(state.activeTopic.topic, state.activeTopic.loaded);
        show(el.viewParts);
      } else {
        openTopics();
      }
      return;
    }
    await loadHome();
    openPapers();
  });

  el.sessionBack.addEventListener("click",()=>exitSession().catch(e=>toast(e.message)));
  $("#topic-paper-count").addEventListener("change",()=>applyTopicPaperCount().catch(e=>toast(e.message)));
  el.startButton.addEventListener("click", () => { startSession(); });

  el.resetProgress.addEventListener("click", async () => {
    if (!window.confirm("将清空这套题的全部作答记录、错题本和标记，无法撤销。确定吗？")) return;
    if (state.api) {
      try {
        await api("DELETE", `./api/exams/${encodeURIComponent(state.slug)}/progress`);
      } catch (error) {
        toast(`清空失败：${error.message}`);
        return;
      }
    } else {
      saveLocal("review", {});
      saveLocal("answers", {});
      saveLocal("attempts", []);
    }
    await refreshProgress();
    renderSetup();
    toast("记录已清空");
  });

  el.prevButton.addEventListener("click", () => navigate(-1));
  el.nextButton.addEventListener("click", () => navigate(1));
  el.revealButton.addEventListener("click", revealCurrent);
  el.submitButton.addEventListener("click", () => {
    const session = state.session;
    const unanswered = session.queue.length - session.queue.filter((entry) => {
      const answer = session.answers.get(entry.question.id);
      return answer && answer.chosen !== null;
    }).length;
    const message = unanswered
      ? `还有 ${unanswered} 题没有作答，确定要交卷吗？`
      : "确定交卷并查看报告吗？";
    if (window.confirm(message)) submitSession();
  });

  el.markButton.addEventListener("click", toggleMark);
  el.questionNote.addEventListener("input", saveNoteSoon);

  el.sheetButton.addEventListener("click", () => {
    const open = el.answerSheet.hidden;
    el.answerSheet.hidden = !open;
    el.sheetButton.setAttribute("aria-expanded", String(open));
    if (open) el.answerSheet.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
  el.answerSheetClose.addEventListener("click", () => {
    el.answerSheet.hidden = true;
    el.sheetButton.setAttribute("aria-expanded", "false");
  });

  el.passageCollapse.addEventListener("click", () => {
    const collapsed = el.passagePane.classList.toggle("is-collapsed");
    el.passageCollapse.textContent = collapsed ? "展开" : "收起";
    el.passageCollapse.setAttribute("aria-expanded", String(!collapsed));
  });

  el.reportHome.addEventListener("click", async () => {
    state.session = null;
    await loadHome();
    show(el.viewHome);
  });
  el.reportRestart.addEventListener("click", () => {
    startSession();
  });
  el.reportReview.addEventListener("click", () => {
    state.setup.mode = "review";
    state.setup.scope = "wrong";
    startSession();
  });

  document.addEventListener("keydown", onKeyDown);
  window.addEventListener("beforeunload", () => { flushAnswers(); });
}

function onKeyDown(event) {
  if (el.viewSession.hidden) return;
  if (event.key === "Escape") {event.preventDefault();exitSession().catch(e=>toast(e.message));return;}
  const target = event.target;
  if (target && (target.tagName === "TEXTAREA" || target.tagName === "INPUT")) return;
  if (event.metaKey || event.ctrlKey || event.altKey) return;

  const entry = currentEntry();
  if (!entry) return;

  if (event.key >= "1" && event.key <= "4") {
    const number = Number(event.key);
    const limit = entry.question.choicesSpoken
      ? entry.question.choiceCount
      : (entry.question.choices || []).length;
    if (number <= limit) {
      event.preventDefault();
      const answer = answerFor(entry.question.id);
      if (!(state.session.mode !== "exam" && answer.revealed)) choose(number);
    }
    return;
  }
  if (event.key === "ArrowRight" || event.key === "Enter") {
    event.preventDefault();
    navigate(1);
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    navigate(-1);
  } else if (event.key === " ") {
    event.preventDefault();
    if (state.session.mode !== "exam") revealCurrent();
  } else if (event.key === "m" || event.key === "M") {
    event.preventDefault();
    toggleMark();
  }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

/* `#/exam/<slug>?mode=review&scope=wrong`
 *
 * The personal centre's 真题错题本 links straight into a paper's wrong-answer
 * drill, so a learner who spots a weak paper in 我的 does not have to find it
 * again by hand here. An unknown slug simply falls back to the exam list.
 */
const LEVEL_HASH = /^#\/level\/([A-Za-z0-9\u4e00-\u9fff]+)(?:\/(papers|topics))?$/;

function readLevelHash() {
  const match = LEVEL_HASH.exec(location.hash || "");
  if (!match) return null;
  return { level: decodeURIComponent(match[1]).toUpperCase(), screen: match[2] || "" };
}

/** The hash for the current level, optionally at one of its two study screens. */
function levelHash(screen) {
  return screen ? `#/level/${state.level}/${screen}` : `#/level/${state.level}`;
}

/** Land on whichever screen the hash names. Returns false when it names none. */
function applyLevelHash() {
  const link = readLevelHash();
  if (!link) return false;
  const levels = levelsPresent();
  const targetLevel = (link.level === "ALL" || !levels.includes(link.level))
    ? (levels[0] || "N1")
    : link.level;
  setLevel(targetLevel);
  if (link.screen === "papers") openPapers();
  else if (link.screen === "topics") openTopics();
  else show(el.viewHome);
  return true;
}

function readExamHash() {
  const match = /^#\/exam\/([^?]+)(?:\?(.*))?$/.exec(location.hash || "");
  if (!match) return null;
  const params = new URLSearchParams(match[2] || "");
  return {
    slug: decodeURIComponent(match[1]),
    mode: params.get("mode") || "",
    scope: params.get("scope") || "",
  };
}

async function applyExamHash() {
  const link = readExamHash();
  if (!link) return false;
  await openExam(link.slug);
  if (state.slug !== link.slug) return false;
  if (MODES.some((mode) => mode.id === link.mode)) state.setup.mode = link.mode;
  if (link.scope && scopeOptions().some((scope) => scope.id === link.scope && scope.count > 0)) {
    state.setup.scope = link.scope;
  }
  renderSetup();
  show(el.viewSetup);
  return true;
}

async function boot() {
  bindEvents();
  state.api = await acquireToken();
  await loadHome();
  if (!applyLevelHash()) show(el.viewHome);
  await applyExamHash();
  window.addEventListener("hashchange", () => {
    if (applyLevelHash()) return;
    applyExamHash();
  });

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => { /* offline support is optional */ });
  }
}

boot();
