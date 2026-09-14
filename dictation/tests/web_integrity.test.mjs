// The front end has no build step, so nothing between an editor and the browser
// checks that it is even parseable. Three separate corruptions have reached the
// working tree already — a truncated `configureVideoPanel` that left app.js with
// unbalanced braces, a deleted `REGISTRY_CACHE` declaration in sw.js, and two
// elements dropped from index.html that app.js still addressed.
//
// A parse failure and a missing element are invisible until a page loads and
// does nothing — the code guards its lookups, so it simply stops rendering that
// part rather than complaining. Both are cheap to catch here. (The deleted
// constant is already caught by tests/sw_cache.test.mjs, which executes sw.js.)

import assert from "node:assert/strict";
import test from "node:test";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.join(HERE, "..", "src", "web");

const SCRIPTS = ["app.js", "exam.js", "home.js", "personal.js", "sw.js", "progress_model.js", "dictation_scoring.js", "course_library_model.js", "media_adapters.js", "learning_data.js", "learning_store.js", "srs_scheduler.js", "personal_data_tools.js", "exam_markup.js", "lexicon.js", "lexicon_markup.js"];
const PAGES = [
  { html: "index.html", js: "app.js" },
  { html: "exam.html", js: "exam.js" },
  { html: "home.html", js: "home.js" },
  { html: "me.html", js: "personal.js" },
  { html: "lexicon.html", js: "lexicon.js" },
];

test("every front-end script parses", () => {
  for (const name of SCRIPTS) {
    const file = path.join(WEB, name);
    if (!fs.existsSync(file)) continue;
    const source = fs.readFileSync(file, "utf8");
    assert.doesNotThrow(
      // Compiling without running is exactly `node --check`: it catches an
      // unclosed brace or a stray edit without needing a DOM.
      () => new vm.Script(source, { filename: name }),
      `${name} does not parse — the browser would not run a line of it`,
    );
  }
});

test("every element id a page's script addresses exists in that page", () => {
  for (const { html, js } of PAGES) {
    const htmlFile = path.join(WEB, html);
    const jsFile = path.join(WEB, js);
    if (!fs.existsSync(htmlFile) || !fs.existsSync(jsFile)) continue;

    const markup = fs.readFileSync(htmlFile, "utf8");
    const source = fs.readFileSync(jsFile, "utf8");

    const present = new Set([...markup.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));
    const wanted = new Set([
      ...[...source.matchAll(/\$\("#([A-Za-z0-9_-]+)"\)/g)].map((m) => m[1]),
      ...[...source.matchAll(/getElementById\("([A-Za-z0-9_-]+)"\)/g)].map((m) => m[1]),
      ...[...source.matchAll(/querySelector\("#([A-Za-z0-9_-]+)"\)/g)].map((m) => m[1]),
    ]);

    const missing = [...wanted].filter((id) => !present.has(id)).sort();
    assert.deepEqual(missing, [], `${js} addresses #${missing.join(", #")} but ${html} has no such element`);
  }
});

test("no page declares the same id twice", () => {
  for (const { html } of PAGES) {
    const file = path.join(WEB, html);
    if (!fs.existsSync(file)) continue;
    const ids = [...fs.readFileSync(file, "utf8").matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]);
    const seen = new Set();
    const dupes = [...new Set(ids.filter((id) => (seen.has(id) ? true : (seen.add(id), false))))].sort();
    assert.deepEqual(dupes, [], `${html} repeats id ${dupes.join(", ")} — getElementById would pick one at random`);
  }
});

test("JLPT practice copy matches group-submit feedback", () => {
  const html = fs.readFileSync(path.join(WEB, "exam.html"), "utf8");
  const source = fs.readFileSync(path.join(WEB, "exam.js"), "utf8");
  assert.doesNotMatch(html, /选完立刻(?:看解析|判对错)/);
  assert.match(html, /完成整组并交卷后，统一判题和查看解析/);
  assert.match(source, /交卷后统一判题并查看答案/);
});

test("JLPT level switch filters by level without an 'all' tab", () => {
  const source = fs.readFileSync(path.join(WEB, "exam.js"), "utf8");
  assert.doesNotMatch(source, /\["all",\s*"全部"/, "JLPT真题练习不应包含'全部'标签选项");
  assert.match(source, /const tabs = levels\.map/, "等级标签应直接映射具体等级");
});

test("JLPT progress recovery and topic group sizing stay wired into the page", () => {
  const html = fs.readFileSync(path.join(WEB, "exam.html"), "utf8");
  const source = fs.readFileSync(path.join(WEB, "exam.js"), "utf8");
  assert.match(html, /id="topic-paper-count"/);
  assert.match(html, /以一套真题在当前题型下的全部题目为一组/);
  assert.match(source, /async function resumeAttempt\s*\(/);
  assert.match(source, /async function abandonAttempt\s*\(/);
  assert.match(source, /async function applyTopicPaperCount\s*\(/);
  assert.match(source, /available\.slice\(-count\)/, "topic sizing must keep each source paper intact");
});

test("a JLPT sitting can be left one level up without losing what was answered", () => {
  const html = fs.readFileSync(path.join(WEB, "exam.html"), "utf8");
  const source = fs.readFileSync(path.join(WEB, "exam.js"), "utf8");

  // The answering screen used to be the one screen with no way back: the only
  // exit was the top bar's 题库首页, which jumps past the setup screen entirely.
  assert.match(html, /id="session-back"/);
  assert.match(source, /el\.sessionBack\.addEventListener/);
  assert.match(source, /event\.key === "Escape"/);

  const exit = source.match(/async function exitSession\(\)\s*\{([\s\S]*?)\n\}/);
  assert.ok(exit, "exitSession must exist");
  assert.match(exit[1], /await teardownSession\(\)/);
  assert.match(exit[1], /show\(el\.viewSetup\)/, "退出 goes one level up, not to the exam list");
  assert.doesNotMatch(exit[1], /submitSession\(|abandon/, "leaving must neither score nor abandon the sitting");

  const teardown = source.match(/async function teardownSession\(\)\s*\{([\s\S]*?)\n\}/);
  assert.ok(teardown, "teardownSession must exist");
  // Order matters twice over: the clock has to stop before the flush is awaited,
  // or an exam-mode tick auto-submits the sitting someone just stepped out of;
  // and the session may only be dropped after the flush, which reads it to find
  // the attempt each answer belongs to.
  assert.ok(
    teardown[1].indexOf("stopTimer()") < teardown[1].indexOf("flushAnswers()"),
    "the timer must stop before answers are flushed",
  );
  assert.ok(
    teardown[1].indexOf("flushAnswers()") < teardown[1].indexOf("state.session = null"),
    "answers must be flushed before the session is dropped",
  );
});

test("app.js initiates bootstrap only after all module constants are declared", () => {
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  const bootstrapCallIndex = source.lastIndexOf("bootstrap().catch(");
  const libraryIndex = source.indexOf("const Library =");
  assert.ok(bootstrapCallIndex > libraryIndex, "bootstrap() must be called after Library is declared");
  const personalHashIndex = source.indexOf("const PERSONAL_HASH =");
  assert.ok(bootstrapCallIndex > personalHashIndex, "bootstrap() must be called after PERSONAL_HASH is declared");
});

test("inline message helpers showInlineMessage and hideInlineMessage are defined in app.js", () => {
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  assert.match(source, /function showInlineMessage\s*\(/);
  assert.match(source, /function hideInlineMessage\s*\(/);
});

test("applyBlindMode does not restrict blind listening to dictation mode only", () => {
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  const blindModeFnMatch = source.match(/function applyBlindMode\(\)\s*\{([\s\S]*?)\n\}/);
  assert.ok(blindModeFnMatch, "applyBlindMode function exists");
  assert.doesNotMatch(
    blindModeFnMatch[1],
    /state\.mode\s*===\s*["']dictation["']/,
    "applyBlindMode must not gate blind mode on dictation mode",
  );
});

test("app.css defines side-by-side 2-column layout for video courses in playback mode", () => {
  const css = fs.readFileSync(path.join(WEB, "app.css"), "utf8");
  assert.match(
    css,
    /\.practice-card\[data-mode="playback"\][\s\S]*?\.practice-body\s*\{[\s\S]*?display:\s*grid;[\s\S]*?grid-template-columns:/,
    "app.css must provide grid-template-columns for playback mode with video",
  );
  assert.match(
    css,
    /\.practice-card\[data-mode="playback"\][\s\S]*?\.dictation-content-grid\s*\{[\s\S]*?order:\s*1;/,
    "video and player media grid must be order 1 (left column)",
  );
  assert.match(
    css,
    /\.practice-card\[data-mode="playback"\][\s\S]*?\.subtitle-panel\s*\{[\s\S]*?order:\s*2;/,
    "subtitle panel must be order 2 (right column)",
  );
});

test("sentence mode (dictation vs listen-only) functions and elements are defined", () => {
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  assert.match(source, /function setSentenceMode\s*\(/);
  assert.match(source, /function updateSentenceModeUi\s*\(/);
  assert.match(source, /function renderListenPanel\s*\(/);
  assert.match(source, /function revealListenAnswer\s*\(/);
  assert.match(source, /"listen-original-text"/);
  assert.match(source, /"listen-translation"/);
  assert.match(source, /"listen-explanation"/);

  const html = fs.readFileSync(path.join(WEB, "index.html"), "utf8");
  assert.match(html, /id="sentence-mode-toggle"/);
  assert.match(html, /id="sentence-mode-dictation"/);
  assert.match(html, /id="sentence-mode-listen"/);
  assert.match(html, /id="listen-panel"/);
  assert.match(html, /id="listen-reveal-button"/);
  assert.match(html, /id="listen-original-text"/);
  assert.match(html, /id="listen-speak-button"/);
});

test("personal learning flows keep canonical course indexes and real date ranges", () => {
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  assert.match(source, /coursePracticeIndexes:\s*\[\]/);
  assert.match(source, /function restoreCoursePracticeQueue\s*\(/);
  assert.match(source, /dateFrom=\$\{dateDaysAgoIso\(6\)\}/);
  assert.match(source, /dateFrom=\$\{dateDaysAgoIso\(29\)\}/);
  assert.doesNotMatch(source, /sentencesCount:\s*1,\s*\n\s*studyDurationMs:\s*60000/);
  assert.match(source, /api\/exams\/review-summary/);
});

test("the course hall exposes search, quality filters and quality badges", () => {
  const html = fs.readFileSync(path.join(WEB, "index.html"), "utf8");
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  const model = fs.readFileSync(path.join(WEB, "course_library_model.js"), "utf8");
  for (const id of ["library-search-input", "library-level-filter", "library-status-filter", "library-sort"]) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  assert.match(source, /function qualityLabel\s*\(/);
  assert.match(model, /course\?\.quality/);
  assert.match(source, /practiceSentenceCount/);
});

test("listen-only reveal records exposure rather than a correct answer", () => {
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  const match = source.match(/function revealListenAnswer\(\)\s*\{([\s\S]*?)\n\}/);
  assert.ok(match);
  assert.match(match[1], /recordListenExposure\(\)/);
  assert.doesNotMatch(match[1], /recordProgress\s*\(/);
});

test("the course hall does not eagerly initialise the active media course", () => {
  const source = fs.readFileSync(path.join(WEB, "app.js"), "utf8");
  const bootstrap = source.match(/async function bootstrap\(\)\s*\{([\s\S]*?)\n\}/);
  assert.ok(bootstrap);
  assert.match(bootstrap[1], /if \(routeNeedsCourse\(\)\)/);
  assert.doesNotMatch(bootstrap[1], /await loadActiveCourse\(\)/);
  assert.match(source, /async function ensureActiveCourseLoaded\(\)/);
});

test("the three learning modes are separate workspaces with stable product routes", () => {
  const home = fs.readFileSync(path.join(WEB, "home.html"), "utf8");
  const listening = fs.readFileSync(path.join(WEB, "index.html"), "utf8");
  const exams = fs.readFileSync(path.join(WEB, "exam.html"), "utf8");
  const lexicon = fs.readFileSync(path.join(WEB, "lexicon.html"), "utf8");
  const personal = fs.readFileSync(path.join(WEB, "me.html"), "utf8");
  const app = fs.readFileSync(path.join(WEB, "app.js"), "utf8");

  assert.match(home, /href="\.\/listening#\/listening"/);
  assert.match(home, /href="\.\/exams"/);
  assert.match(home, /href="\.\/lexicon"/);
  assert.match(home, /class="personal-hub"/);
  assert.match(home, /href="\.\/me#\/mistakes"/);
  // 我的 is a cross-mode hub, not a fourth way to practise, so it must stay out of
  // the mode grid however many workspaces there are.
  assert.equal((home.match(/class="board-card /g) || []).length, 3);

  for (const page of [listening, exams, lexicon]) {
    assert.match(page, /class="mode-context"/);
    assert.match(page, />切换学习模式</);
    assert.doesNotMatch(page, /class="section-nav"/);
  }
  assert.match(app, /function isStandalonePersonalPath\s*\(/);
  assert.match(app, /location\.replace\(`\.\/me#\//);
  assert.match(personal, /id="personal-main"/);
  assert.match(personal, /src="\.\/personal\.js"/);
  assert.doesNotMatch(personal, /src="\.\/app\.js"/);
});

test("the home summary reports listening and exam review debt separately", () => {
  const source = fs.readFileSync(path.join(WEB, "home.js"), "utf8");
  assert.match(source, /api\/exams\/review-summary/);
  assert.match(source, /精听错句/);
  assert.match(source, /真题错题/);
});
