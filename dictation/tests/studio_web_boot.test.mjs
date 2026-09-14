/* Boot both workbench pages in a stub DOM.
 *
 * The static guards in studio_web.test.mjs read the source; they cannot tell that
 * `StudioJobs` calls `PipelinePdf.renderResult()` and that the pipeline module
 * actually exports it. Splitting one file into thirteen makes that class of
 * mistake — a call to a namespace method that does not exist — the likely one,
 * and it is invisible until the panel is used.
 *
 * So this loads each page's scripts in order into one context, exactly as the
 * browser would, lets the shell run its `wire()` and `bootstrap()`, and then
 * checks that every cross-module call site resolves against the objects that
 * really got built.
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

import { scriptsFor, stripNonCode } from "./web_scan.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STUDIO = path.join(HERE, "..", "src", "studio_web");

/** Read the front end's own constant rather than restating it here. */
const EDITOR_DEFAULT_FOCUS = (() => {
  const source = fs.readFileSync(path.join(STUDIO, "editor_analysis.js"), "utf8");
  const block = source.match(/const DEFAULT_FOCUS = ((?:\s*"[^"]*"\s*\+?)+);/);
  assert.ok(block, "editor_analysis.js must define DEFAULT_FOCUS");
  return [...block[1].matchAll(/"([^"]*)"/g)].map((match) => match[1]).join("");
})();

/** Canned server answers: enough shape for every bootstrap path to run. */
const RESPONSES = {
  "/api/session/bootstrap": { token: "test-token" },
  "/api/config": {
    configPath: "config/providers.json",
    coursesDir: "courses",
    languages: ["ja", "en"],
    languageRouting: { ja: "japanese-accurate" },
    defaultTextProfile: "text-one",
    defaultAsrProfile: "asr-one",
    defaultVisionPipeline: "vision-one",
    textProfiles: [{ name: "text-one", available: true, source: "local", kind: "openai-compat", model: "m" }],
    asrProfiles: [{ name: "asr-one", available: true, source: "local", kind: "faster-whisper", model: "large-v3" }],
    visionPipelines: [{ name: "vision-one", available: true, description: "d", members: [{ name: "a", local: true }] }],
  },
  "/api/gpu-status": { available: false, status_text: "no gpu", gpus: [] },
  "/api/local-models": { ready: 0, total: 1, services: [], controls: {}, canStart: true, canStop: true, history: [] },
  "/api/courses": { courses: [] },
  "/api/builds": { builds: [] },
  "/api/review-targets": { targets: [], drafts: 0, courses: 0 },
};

function stubElement(id) {
  const element = {
    id,
    hidden: false,
    textContent: "",
    value: "",
    checked: false,
    disabled: false,
    indeterminate: false,
    className: "",
    placeholder: "",
    title: "",
    href: "",
    src: "",
    type: "",
    innerHTML: "",
    scrollTop: 0,
    clientHeight: 0,
    scrollHeight: 0,
    dataset: {},
    style: {},
    children: [],
    listeners: {},
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    append(...nodes) { this.children.push(...nodes); },
    replaceChildren(...nodes) { this.children = nodes; },
    addEventListener(name, handler) { (this.listeners[name] ||= []).push(handler); },
    removeEventListener() {},
    setAttribute() {},
    getAttribute: () => null,
    closest: () => null,
    scrollIntoView() {},
    focus() {},
    querySelector: () => null,
    querySelectorAll: () => [],
  };
  return element;
}

function makeContext(ids, overrides = {}) {
  const answers = Object.assign({}, RESPONSES, overrides);
  const elements = new Map(ids.map((id) => [id, stubElement(id)]));
  const document = {
    hidden: true,
    getElementById: (id) => elements.get(id) || null,
    createElement: (tag) => stubElement(`<${tag}>`),
    createTextNode: (value) => ({ textContent: value }),
    addEventListener() {},
    querySelector: () => null,
  };
  const storage = new Map();
  const context = {
    document,
    console,
    setTimeout, clearTimeout,
    // Timers must not actually fire: a poll loop would outlive the test.
    setInterval: () => 0,
    clearInterval: () => {},
    localStorage: {
      getItem: (key) => (storage.has(key) ? storage.get(key) : null),
      setItem: (key, value) => storage.set(key, String(value)),
      removeItem: (key) => storage.delete(key),
    },
    navigator: { clipboard: { writeText: async () => {} } },
    URL: { createObjectURL: () => "blob:stub", revokeObjectURL() {} },
    URLSearchParams,
    location: { search: "", href: "/editor.html" },
    history: { pushState() {} },
    fetch: async (url) => {
      const key = String(url).split("?")[0];
      const body = answers[key];
      if (body === undefined) throw new Error(`unstubbed request: ${url}`);
      return {
        ok: true,
        status: 200,
        headers: { get: () => "application/json" },
        json: async () => body,
      };
    },
  };
  // Scripts reach for window-level events (popstate, beforeunload); the context
  // *is* the window here, so it needs the listener surface too.
  context.addEventListener = () => {};
  context.removeEventListener = () => {};
  context.window = context;
  context.globalThis = context;
  vm.createContext(context);
  return context;
}

/** Every `Namespace.method(` call site across a page's scripts. */
function namespaceCalls(sources) {
  const calls = [];
  for (const { script, code } of sources) {
    for (const match of stripNonCode(code).matchAll(/\b([A-Z][A-Za-z]+)\.([A-Za-z_$][\w$]*)\s*\(/g)) {
      calls.push({ script, namespace: match[1], method: match[2] });
    }
  }
  return calls;
}

for (const page of ["index.html", "import.html", "ops.html", "library.html", "editor.html"]) {
  test(`${page} boots in a stub DOM and every namespace call resolves`, async () => {
    const markup = fs.readFileSync(path.join(STUDIO, page), "utf8");
    const ids = [...markup.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
    const context = makeContext(ids);

    const scripts = scriptsFor(STUDIO, page);
    const sources = scripts.map((script) => ({
      script,
      code: fs.readFileSync(path.join(STUDIO, script), "utf8"),
    }));

    for (const { script, code } of sources) {
      vm.runInContext(code, context, { filename: script });
    }
    // The shells start an async bootstrap; let it settle so a rejected promise
    // surfaces here rather than as an unhandled rejection after the test ends.
    await new Promise((resolve) => setTimeout(resolve, 50));

    for (const { script, namespace, method } of namespaceCalls(sources)) {
      const target = context[namespace];
      if (!target) continue; // not one of ours (Object, Math, URLSearchParams…)
      assert.equal(
        typeof target[method], "function",
        `${script} calls ${namespace}.${method}() but ${namespace} exports no such function`,
      );
    }
  });
}

test("the build page reaches every pipeline through the same five questions", () => {
  // The registry only works if each pipeline answers all of them; a missing
  // `startLabel` shows up as a blank button rather than an error.
  const context = makeContext([]);
  for (const script of ["core.js", "studio_state.js", "studio_pipeline_audio.js",
    "studio_pipeline_video.js", "studio_pipeline_pdf.js"]) {
    vm.runInContext(fs.readFileSync(path.join(STUDIO, script), "utf8"), context, { filename: script });
  }
  for (const pipeline of [context.PipelineAudio, context.PipelineVideo, context.PipelinePdf]) {
    for (const key of ["id", "tabId", "fieldsId", "titlePlaceholder", "usesCommonFields", "usesEnrichment"]) {
      assert.ok(key in pipeline, `${pipeline.id} is missing ${key}`);
    }
    for (const method of ["count", "hasSource", "modelReady", "startLabel", "start"]) {
      assert.equal(typeof pipeline[method], "function", `${pipeline.id} is missing ${method}()`);
    }
  }
});

/** Load one page into a stub DOM and hand back its context. */
async function boot(page, overrides = {}) {
  const markup = fs.readFileSync(path.join(STUDIO, page), "utf8");
  const ids = [...markup.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
  const context = makeContext(ids, overrides);
  for (const script of scriptsFor(STUDIO, page)) {
    vm.runInContext(fs.readFileSync(path.join(STUDIO, script), "utf8"), context, { filename: script });
  }
  await new Promise((resolve) => setTimeout(resolve, 50));
  return context;
}

test("制课: switching pipelines and applying a job do not throw", async () => {
  const context = await boot("index.html");
  // Joined, not deep-equal: arrays built inside the vm have that realm's Array
  // prototype, which strict deepEqual counts as a difference.
  assert.equal(context.StudioPipelines.kinds().join(","), "audio,video",
    "the build page owns audio and video; PDF belongs to 教材入库");

  for (const pipeline of context.StudioPipelines.all) {
    context.StudioPipelines.select(pipeline.id);
    assert.equal(context.StudioPipelines.current().id, pipeline.id);
    assert.equal(typeof context.StudioPipelines.current().startLabel(2), "string");
  }
  context.StudioJobs.applyJob({ id: "j2", title: "t", status: "succeeded", elapsed: 1, kind: "audio", hasBundle: true });
  assert.equal(context.document.getElementById("install").hidden, false, "an audio bundle can be installed");
  context.StudioJobs.applyJob({ id: "j3", title: "t", status: "succeeded", elapsed: 1, kind: "video", installedTo: "courses/x" });
  assert.equal(context.document.getElementById("install").hidden, true, "a video build has nothing to install");
  context.StudioJobs.renderQueue();
});

test("教材入库: a PDF job renders its draft summary", async () => {
  const context = await boot("import.html");
  assert.equal(context.StudioPipelines.kinds().join(","), "pdf");
  context.StudioJobs.applyJob({
    id: "j1", title: "t", status: "needs_review", elapsed: 3, kind: "pdf", log: ["line"],
    result: {
      kind: "grammar", level: "N3", detected: { kind: "grammar", confidence: "high" },
      draftPath: "/x", stats: { pages: 1, questions: 0, entries: 2 },
      ocr: { usedProfiles: ["a"], flaggedPages: [1] }, nextSteps: ["核对"], reviewRequired: true,
    },
  });
  assert.equal(context.document.getElementById("result-summary").hidden, false);
  assert.equal(context.document.getElementById("install").hidden, true, "a draft is never installed as a course");
});

test("运维: GPU cards and model controls render", async () => {
  const context = await boot("ops.html");
  context.StudioGpu.renderCards({
    available: true, nvml_ready: true, status_text: "ok", summary: "1 card", driver_version: "1.0",
    gpus: [{ index: 0, name: "NVIDIA X", is_current: true, utilization_gpu_percent: 40, memory_total_mb: 24576,
      memory_used_mb: 8192, memory_free_mb: 16384, power_draw_w: 100, power_limit_w: 300, uuid: "u" }],
  });
  context.StudioLocalModels.render({
    ready: 1, total: 2, canStart: true, canStop: true, history: [{ service: "s", action: "start", status: "ok", log: ["x"] }],
    services: [{ name: "s", label: "S", role: "r", available: true, control: null }], controls: {},
  });
});

test("课程库: the installed list renders with categories, collapsible groups, and filtering", async () => {
  const context = await boot("library.html");
  const courses = [
    { name: "2010-07-N1", title: "JLPT N1 听力 2010年7月", sentences: 424, status: "passed", errors: 0, warnings: 0 },
    { name: "2010-12-N2", title: "2010年12月N2", sentences: 380, status: "passed", errors: 0, warnings: 0 },
    { name: "nhk-news-0001", title: "NHK News", sentences: 20, mediaKind: "remote", status: "passed", errors: 0, warnings: 0 },
    { name: "librivox-test", title: "思索者的日記", sentences: 50, status: "passed", errors: 0, warnings: 0 },
  ];
  context.StudioCourses.render(courses);
  const doc = context.document;
  assert.equal(doc.getElementById("count-all").textContent, "4");
  assert.equal(doc.getElementById("count-intensive").textContent, "4");
  assert.equal(doc.getElementById("count-pdf").textContent, "0");
  assert.equal(doc.getElementById("count-level-all").textContent, "4");
  assert.equal(doc.getElementById("count-level-n1").textContent, "1");
  assert.equal(doc.getElementById("count-level-n2").textContent, "1");

  // Groups are collapsed by default (open is falsy)
  assert.equal(Boolean(doc.getElementById("group-intensive-audio").open), false);
  assert.equal(Boolean(doc.getElementById("group-intensive-video").open), false);
  assert.equal(Boolean(doc.getElementById("group-pdf-jlpt").open), false);
  assert.equal(Boolean(doc.getElementById("group-pdf-textbook").open), false);

  // Check table bodies and badges
  const audioRows = doc.getElementById("audio-table-body").children;
  assert.equal(audioRows.length, 3);
  assert.equal(audioRows[0].children[0].children[0].textContent, "JLPT N1 听力");
  assert.equal(audioRows[1].children[0].children[0].textContent, "JLPT N2 听力");
  assert.equal(audioRows[2].children[0].children[0].textContent, "音频精听");

  const videoRows = doc.getElementById("video-table-body").children;
  assert.equal(videoRows.length, 1);
  assert.equal(videoRows[0].children[0].children[0].textContent, "视频精听");

  const jlptRows = doc.getElementById("jlpt-table-body").children;
  assert.equal(jlptRows.length, 1);
  assert.match(jlptRows[0].children[0].textContent, /暂无 PDF 真题课程/);

  const textbookRows = doc.getElementById("textbook-table-body").children;
  assert.equal(textbookRows.length, 1);
  assert.match(textbookRows[0].children[0].textContent, /暂无课本课程/);
});

test("the editor opens a course and a draft without throwing", async () => {
  const markup = fs.readFileSync(path.join(STUDIO, "editor.html"), "utf8");
  const ids = [...markup.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
  const context = makeContext(ids);
  for (const script of scriptsFor(STUDIO, "editor.html")) {
    vm.runInContext(fs.readFileSync(path.join(STUDIO, script), "utf8"), context, { filename: script });
  }
  await new Promise((resolve) => setTimeout(resolve, 50));

  context.EditorState.course = {
    name: "c", title: "T", language: "ja", revision: "r",
    quality: { status: "needs_review" }, review: { reviewed: 1, total: 2 },
    sentences: [{ id: "s1", sourceText: "あ", translationText: "a", explanationText: "", startTime: 0, endTime: 1 }],
  };
  context.EditorState.mode = "course";
  context.EditorCourse.renderSentenceList();
  context.EditorCourse.showSentence();
  assert.equal(typeof context.EditorCourse.fields().sourceText, "string");

  context.EditorState.draft = { jobId: "b1", title: "D", kind: "grammar", level: "N3", pages: [{ name: "p0001.json", page: 1, blocks: 2, issues: 0 }] };
  context.EditorState.mode = "draft";
  context.EditorDraft.renderDraftPageList();

  context.EditorTargets.updateSelection();
  context.EditorTargets.updateButtons();
  context.EditorTargets.showPrompt(false);
});

for (const page of ["index.html", "import.html"]) {
test(`${page}: each pipeline shows exactly the fields it actually sends`, async () => {
  // The wrappers used to carry the id of the *next* field down, so switching to
  // the PDF tab hid 课程标题 — which every pipeline sends — and left 生成中文翻译与讲解
  // on screen, where a PDF build ignores it. Both were invisible from the source:
  // the ids all existed, just one row out of step.
  const markup = fs.readFileSync(path.join(STUDIO, page), "utf8");
  const ids = [...markup.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
  const context = makeContext(ids);
  for (const script of scriptsFor(STUDIO, page)) {
    vm.runInContext(fs.readFileSync(path.join(STUDIO, script), "utf8"), context, { filename: script });
  }
  await new Promise((resolve) => setTimeout(resolve, 50));
  if (context.document.getElementById("enrich")) context.document.getElementById("enrich").checked = true;

  const transcribing = ["language-field", "asr-profile-field", "enrich-field", "text-profile-field", "common-advanced"];
  for (const pipeline of context.StudioPipelines.all) {
    context.StudioPipelines.select(pipeline.id);
    assert.equal(
      context.document.getElementById("title-field").hidden, false,
      `${pipeline.id} sends a title, so 课程标题 must stay on screen`,
    );
    for (const field of transcribing) {
      const node = context.document.getElementById(field);
      // 教材入库 does not carry the transcription fields at all.
      if (!node) continue;
      assert.equal(
        node.hidden, !pipeline.usesCommonFields,
        `${pipeline.id}: #${field} visibility must follow usesCommonFields`,
      );
    }
  }
});
}

test("the status pill says what the machine can do, and warns when it cannot", async () => {
  // The pill is the only machine status a working page carries, so what it says
  // has to be exact: 运维 is a nav click away, but only if the pill made it clear
  // that a service is missing.
  const context = await boot("index.html");
  const pill = context.document.getElementById("status-pill");
  assert.ok(pill, "制课 must carry a status pill");

  const busy = context.StudioStatusPill.compose({
    gpu: { available: true, nvml_ready: true, status_text: "ok", driver_version: "1.0", device_count: 2,
      gpus: [{ index: 0, name: "NVIDIA H100", utilization_gpu_percent: 40, memory_total_mb: 81920 },
        { index: 1, name: "NVIDIA A6000", memory_total_mb: 49152 }] },
    models: { ready: 4, total: 4, services: [{ label: "GLM-OCR", available: true }] },
  });
  assert.equal(busy.text, "GPU 40% · H100 (+1) · 模型 4/4");
  assert.equal(busy.warn, false, "nothing to warn about when every service is up");

  const short = context.StudioStatusPill.compose({
    gpu: { available: false, status_text: "no gpu", gpus: [] },
    models: { ready: 1, total: 4, services: [{ label: "GLM-OCR", available: false, statusText: "未启动" }] },
  });
  assert.equal(short.text, "GPU — · 模型 1/4");
  assert.equal(short.warn, true, "a missing service must be visible at a glance");
  assert.match(short.title, /到「运维」可以启动缺席的服务/);

  const broken = context.StudioStatusPill.compose({
    gpu: { available: false, gpus: [] },
    models: { error: "boom" },
  });
  assert.equal(broken.text, "GPU — · 模型 ?", "an unreadable status must not read as zero services");
});

test("the editor lets a model be chosen before any course is opened", async () => {
  // 批量整课模型分析 is launched from the list, so the model it will use has to be
  // visible from the list. It used to sit in a panel that only appeared after a
  // course was opened, which meant the batch ran on whichever profile happened to
  // be first — picked from a control the person had never seen.
  const context = await boot("editor.html");
  const doc = context.document;

  assert.equal(doc.getElementById("analysis-panel").hidden, false,
    "分析模型 must be reachable from the list screen");
  assert.equal(doc.getElementById("model-panel").hidden, true,
    "模型复核 edits an open target, so it stays hidden until there is one");
  assert.ok(doc.getElementById("analysis-model").children.length > 0,
    "the model picker must already be populated");

  // Nothing selected yet: the start buttons must say so rather than run on nothing.
  assert.equal(doc.getElementById("start-analysis").disabled, true);
  assert.equal(doc.getElementById("start-analysis").textContent, "开始分析所选课程");

  // Selecting a course in the list arms them.
  context.EditorState.reviewTargets = [{ targetKind: "course", targetId: "c", title: "T", reviewed: 0, total: 2, remaining: 2 }];
  context.EditorState.selectedTargetKeys.add("course:c");
  context.EditorTargets.updateSelection();
  assert.equal(doc.getElementById("start-analysis").disabled, false,
    "with a course selected the analysis can start");
});

test("returning to the list keeps a running batch analysis", async () => {
  // The batch belongs to the list, not to the course that happened to be open
  // when it was started; going back used to clear the poll and strand the report.
  const context = await boot("editor.html");
  context.EditorState.analysisMode = "batch";
  context.EditorState.batchAnalysis = { status: "running", progress: 1, total: 3, targets: [], elapsed: 5 };
  context.EditorState.analysisId = "batch-1";
  context.EditorState.mode = "course";

  context.EditorTargets.showPrompt(false);

  assert.equal(context.EditorState.analysisMode, "batch", "the batch must survive the trip back");
  assert.equal(context.EditorState.batchAnalysis.status, "running");
  assert.equal(context.EditorState.mode, "", "no course is open any more");
});

test("drafts and installed courses are two queues, each folded until asked for", async () => {
  // They were one table with a 类型 column, which added up two different jobs into
  // a single "12 things need you" — a draft is read page by page before it may
  // enter the library at all, a course is already installed and being corrected.
  const context = await boot("editor.html", {
    "/api/review-targets": {
      drafts: 2, courses: 1, reviewed: 1,
      targets: [
        { targetKind: "draft", targetId: "b1", title: "蓝宝书 N2文法", level: "N2", reviewed: 3, total: 157, remaining: 154 },
        { targetKind: "draft", targetId: "b2", title: "红宝书 N1文字词汇", level: "N1", reviewed: 0, total: 121, remaining: 121 },
        { targetKind: "course", targetId: "2010-07-N1", title: "2010-07-N1", level: "N1", reviewed: 20, total: 424, remaining: 404 },
      ],
      reviewedDrafts: [
        { targetKind: "draft", targetId: "b3", title: "新完全掌握 N3", level: "N3", reviewed: 120, total: 120, remaining: 0 },
      ],
    },
  });
  const doc = context.document;

  assert.equal(doc.getElementById("draft-table-body").children.length, 2);
  assert.equal(doc.getElementById("course-table-body").children.length, 1);
  assert.equal(doc.getElementById("reviewed-draft-table-body").children.length, 1);
  // The unit in 剩余 is the real one per queue, not the old "句/页".
  assert.equal(doc.getElementById("draft-group-count").textContent, "2 个草稿 · 剩余 275 页");
  assert.equal(doc.getElementById("course-group-count").textContent, "1 门课程 · 剩余 404 句");
  assert.equal(doc.getElementById("reviewed-draft-group-count").textContent, "1 个草稿 · 已全部复核");

  const markup = fs.readFileSync(path.join(STUDIO, "editor.html"), "utf8");
  for (const id of ["draft-group", "course-group", "reviewed-draft-group"]) {
    assert.match(markup, new RegExp(`<details class="target-group" id="${id}">`),
      `${id} must start folded — no open attribute`);
  }

  // Selecting one queue leaves the other's header checkbox alone.
  context.EditorState.selectedTargetKeys.add("draft:b1");
  context.EditorState.selectedTargetKeys.add("draft:b2");
  context.EditorTargets.updateSelection();
  assert.equal(doc.getElementById("toggle-all-drafts").checked, true);
  assert.equal(doc.getElementById("toggle-all-courses").checked, false);
  assert.equal(doc.getElementById("toggle-all-courses").indeterminate, false);
  assert.equal(doc.getElementById("toggle-all-reviewed-drafts").checked, false);
  assert.equal(doc.getElementById("selected-summary").textContent, "已选择 2 项");

  context.EditorState.selectedTargetKeys.delete("draft:b2");
  context.EditorTargets.updateSelection();
  assert.equal(doc.getElementById("toggle-all-drafts").indeterminate, true,
    "a partly selected queue must read as partly selected");
});

test("the editor no longer duplicates the nav with a back link", async () => {
  const markup = fs.readFileSync(path.join(STUDIO, "editor.html"), "utf8");
  assert.doesNotMatch(markup, /返回课程工作台/, "the nav's 制课 entry already goes there");
  assert.match(markup, /<nav class="nav"/, "…and the nav is what replaces it");
});

/** The fallback instruction the server uses when the box is empty. */
function serverDefaultFocus() {
  const source = fs.readFileSync(path.join(HERE, "..", "src", "studio_server.py"), "utf8");
  const block = source.match(
    /instruction = str\(payload\.get\("instruction"\) or ""\)\.strip\(\) or \(\s*((?:\s*"[^"]*"\s*)+)\)/,
  );
  assert.ok(block, "studio_server.py must still define a fallback analysis instruction");
  return [...block[1].matchAll(/"([^"]*)"/g)].map((match) => match[1]).join("");
}

test("the pre-filled 分析重点 is exactly what the server would have used", () => {
  // Showing a default is only honest if it is *the* default. A different string
  // here would quietly change what every analysis asks for, and the report would
  // be the first place anyone noticed.
  assert.equal(EDITOR_DEFAULT_FOCUS, serverDefaultFocus());
});

test("both instruction boxes arrive filled in and keep what is typed", async () => {
  const context = await boot("editor.html");
  const doc = context.document;

  const focus = doc.getElementById("analysis-instruction");
  const review = doc.getElementById("review-instruction");
  assert.equal(focus.value, serverDefaultFocus(), "分析重点 starts at the server's own default");
  assert.ok(review.value.length > 0, "复核要求 starts filled — the server refuses an empty one");

  // Opening a draft asks a different question than opening a course, so the
  // default follows the target — while it is still a default.
  context.EditorState.mode = "draft";
  context.EditorReview.applyDefaults();
  assert.equal(review.value, context.EditorReview.defaults.draft);
  context.EditorState.mode = "course";
  context.EditorReview.applyDefaults();
  assert.equal(review.value, context.EditorReview.defaults.course);

  // Anything typed survives both a mode switch and a second call.
  review.value = "只核对例句译文，其余不要动。";
  context.EditorState.mode = "draft";
  context.EditorReview.applyDefaults();
  assert.equal(review.value, "只核对例句译文，其余不要动。", "typed text is never overwritten");

  focus.value = "只看重复内容。";
  context.EditorAnalysis.applyDefaults();
  assert.equal(focus.value, "只看重复内容。");
});
