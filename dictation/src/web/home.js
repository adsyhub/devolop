/* 应用首页 — three learning workspaces plus cross-mode personal assets.
 *
 * Deliberately tiny. It talks to the API directly rather than pulling in the
 * player's large module. An entrance works whether or not its numbers arrive;
 * a missing local service costs a stat line, not the route itself.
 *
 * Nothing here assigns innerHTML — course, exam and pack titles are transcribed text.
 */

"use strict";

const TOKEN_HEADER = "X-Dictation-Token";

let token = "";

async function acquireToken() {
  try {
    const response = await fetch("./api/session/bootstrap", { headers: { Accept: "application/json" } });
    if (!response.ok) return false;
    const data = await response.json();
    token = String(data.token || "");
    return Boolean(token);
  } catch {
    return false;
  }
}

async function api(path) {
  const response = await fetch(path, {
    cache: "no-store",
    headers: { Accept: "application/json", [TOKEN_HEADER]: token },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function setStat(id, text) {
  const node = document.getElementById(id);
  if (node) node.textContent = text;
}

async function loadListening() {
  try {
    const courses = (await api("./api/courses")).courses || [];
    if (courses.length === 0) {
      setStat("stat-listening", "还没有安装课程");
      return;
    }
    const video = courses.filter((course) => course.mediaKind === "remote").length;
    const audio = courses.length - video;
    const parts = [];
    if (video) parts.push(`${video} 门视频`);
    if (audio) parts.push(`${audio} 门音频`);
    setStat("stat-listening", `${courses.length} 门课程 · ${parts.join(" / ")}`);
  } catch {
    setStat("stat-listening", "课程列表读取失败");
  }
}

async function loadExams() {
  try {
    const exams = ((await api("./api/exams")).exams || []).filter((exam) => !exam.broken);
    if (exams.length === 0) {
      setStat("stat-exam", "还没有导入真题");
      return;
    }
    const levels = [...new Set(exams.map((exam) => exam.level).filter(Boolean))].sort();
    setStat("stat-exam", `${exams.length} 套真题${levels.length ? ` · ${levels.join(" / ")}` : ""}`);
  } catch {
    setStat("stat-exam", "真题列表读取失败");
  }
}

async function loadLexicon() {
  try {
    const packs = ((await api("./api/lexicon/packs")).packs || []).filter((pack) => !pack.broken);
    if (packs.length === 0) {
      setStat("stat-lexicon", "还没有导入词汇 / 语法包");
      return;
    }
    const entries = packs.reduce((total, pack) => total + (pack.entryCount || 0), 0);
    const levels = [...new Set(packs.map((pack) => pack.level).filter(Boolean))].sort();
    setStat("stat-lexicon", `${entries} 个条目${levels.length ? ` · ${levels.join(" / ")}` : ""}`);
  } catch {
    setStat("stat-lexicon", "词库读取失败");
  }
}

/* Keep the learning modes distinct even in the summary: listening mistakes and
 * exam mistakes get separate labels. The exam side is a single aggregate query,
 * so the home page does not fan out once per installed paper. */
async function loadPersonal() {
  try {
    const [due, vocab, examReview] = await Promise.all([
      api("./api/review/due").catch(() => ({})),
      api("./api/vocab").catch(() => ({})),
      api("./api/exams/review-summary").catch(() => ({})),
    ]);
    const dueVocab = (due.dueVocab || []).length;
    const dueMistakes = (due.dueMistakes || []).length;
    const vocabCount = (vocab.items || []).length;
    const examMistakes = (examReview.exams || []).reduce(
      (total, exam) => total + (exam.questions || []).length,
      0,
    );

    if (vocabCount === 0 && dueVocab === 0 && dueMistakes === 0 && examMistakes === 0) {
      setStat("stat-personal", "还没有学习记录");
      return;
    }
    const pending = [];
    if (dueVocab) pending.push(`${dueVocab} 词待复习`);
    if (dueMistakes) pending.push(`${dueMistakes} 个精听错句`);
    if (examMistakes) pending.push(`${examMistakes} 道真题错题`);
    setStat(
      "stat-personal",
      pending.length ? `${pending.join(" · ")} · 生词本 ${vocabCount} 词` : `生词本 ${vocabCount} 词`,
    );
  } catch {
    setStat("stat-personal", "学习记录读取失败");
  }
}

async function boot() {
  const online = await acquireToken();
  const chip = document.getElementById("home-backend");
  if (!online) {
    ["stat-listening", "stat-exam", "stat-lexicon", "stat-personal"].forEach(
      (id) => setStat(id, "本地服务未连接"),
    );
    return;
  }
  if (chip) chip.hidden = false;
  await Promise.all([loadListening(), loadExams(), loadLexicon(), loadPersonal()]);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => { /* offline support is optional */ });
  }
}

boot();
