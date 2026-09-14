"use strict";
/* ==========================================================================
   制课
   --------------------------------------------------------------------------
   拖 PDF 进来 → 确认这是哪套卷 → 选模型 → 一条后台任务做到底。

   这一页刻意只有两件事：准备、看流水线跑。中间任何一步的细节要改，去课程库
   课程库里改 —— 那里说的是这套卷现在取不取得到，这里是"按一下就走完"的地方。

   界面上不隐瞒机器与人的分别：默认跑到 MACHINE_ATTESTED 发布，卷子带着这个
   把关等级到学习者屏幕上；勾「停在待复核」就停在组装预检，等人逐页签。
   ========================================================================== */

const POLL_MS = 2000;

/* 与 eju_bank/make_paper.py 的 STEPS 一一对应。放在这里是为了让人**开跑前**
   就看见这条流水线会做什么 —— 空着一栏等任务开始，等于让人对着空白猜。
   任务一开跑，同一个列表就被服务端的真实进度覆盖。 */
const PIPELINE_STEPS = [
  ["REGISTER", "登记与导入"],
  ["PROBE", "探测页面"],
  ["RENDER", "渲染原页"],
  ["OCR_TEXT", "读文本"],
  ["OCR_SLOTS", "读解答欄号"],
  ["PROOFREAD_PAGES", "校对 · 复读异常页"],
  ["ATTEST", "页面合同与机器校验"],
  ["ASSEMBLE", "组装与预检"],
  ["PROOFREAD_PAPER", "校对 · 复核整卷"],
  ["PUBLISH", "发布到题库"],
  ["EXPLAIN", "真题详解草稿"],
];
const build = {
  uploads: [],        // {uploadId, fileName, role, detected, sizeBytes}
  jobId: null,
  timer: null,
  logLines: 0,
};

// ── 模型档位 ──────────────────────────────────────────────────────────────

const PICKERS = [
  { select: "ocr-profile", hint: "ocr-hint", family: "vision", required: true,
    prefer: ["local-glm-ocr"], none: null },
  { select: "proofread-profile", hint: "proofread-hint", family: "vision", required: false,
    prefer: ["local-glm46v", "local-flash-next-vision"], none: "不复读异常页" },
  { select: "text-profile", hint: "text-hint", family: "text", required: false,
    prefer: ["local-qwen27", "local-flash-next"], none: "不复核整卷" },
  { select: "explain-profile", hint: "explain-hint", family: "text", required: false,
    prefer: ["local-flash-next", "local-qwen27"], none: "不写详解" },
];

function fillPickers(catalog) {
  for (const picker of PICKERS) {
    const select = $("#" + picker.select);
    const previous = select.value;
    select.replaceChildren();
    if (picker.none) select.append(el("option", "", picker.none));
    for (const profile of catalog[picker.family] || []) {
      const option = el("option", "",
        `${profile.id}${profile.available ? "" : "（" + profile.statusText + "）"}`);
      option.value = profile.id;
      // 服务没在跑的档位仍然列出来：选不了和不知道有这回事是两件事。
      option.disabled = !profile.available;
      select.append(option);
    }
    const wanted = previous || picker.prefer.find((id) =>
      (catalog[picker.family] || []).some((p) => p.id === id && p.available));
    if (wanted && [...select.options].some((o) => o.value === wanted && !o.disabled)) {
      select.value = wanted;
    }
    select.dispatchEvent(new Event("change"));
  }
  const offline = [...(catalog.vision || []), ...(catalog.text || [])]
    .filter((p) => !p.available);
  const pill = $("#model-pill");
  pill.textContent = offline.length
    ? `模型 ${offline.length} 个未就绪` : "本地模型全部在线";
  pill.classList.toggle("is-warn", offline.length > 0);
  for (const problem of catalog.problems || []) {
    showNotice(`档位 ${problem.profile} 配置有问题：${problem.message}`);
  }
}

function describeProfile(family, id) {
  const profile = (state.models?.[family] || []).find((p) => p.id === id);
  if (!profile) return "";
  return `${profile.model} · ${profile.description || profile.baseUrl}`;
}

for (const picker of PICKERS) {
  document.addEventListener("DOMContentLoaded", () => {
    $("#" + picker.select).addEventListener("change", (event) => {
      $("#" + picker.hint).textContent = describeProfile(picker.family, event.target.value);
      refreshStartButton();
      renderPlannedSteps();
    });
  });
}

// ── 上传与「这是哪套卷」 ─────────────────────────────────────────────────

const ROLE_LABEL = { QUESTION_BOOKLET: "题册", ANSWER_KEY: "答案册" };

async function uploadOne(file) {
  const row = { fileName: file.name, state: "uploading" };
  build.uploads.push(row);
  renderUploads();
  try {
    const result = await fetch("/api/v1/admin/uploads", {
      method: "POST",
      headers: {
        "Content-Type": "application/pdf",
        "X-Upload-Filename": encodeURIComponent(file.name),
      },
      body: file,
    });
    const data = await result.json();
    if (!result.ok) throw new Error(data.error?.message || `HTTP ${result.status}`);
    Object.assign(row, data, { state: "ready", role: data.detected.role });
  } catch (error) {
    Object.assign(row, { state: "failed", message: error.message });
  }
  renderUploads();
  adoptDetection();
}

/* 推断只填空着的栏位，不覆盖人已经改过的 —— 人改过的就是对的。 */
function adoptDetection() {
  const detections = build.uploads.filter((u) => u.detected).map((u) => u.detected);
  const first = detections.find((d) => d.session && d.subject) || detections[0];
  if (!first) return;
  if (!$("#paper-session").value && first.session) $("#paper-session").value = first.session;
  if (!$("#paper-subject").value && first.subject) $("#paper-subject").value = first.subject;
  if (first.course && !$("#paper-course").dataset.touched) $("#paper-course").value = first.course;
  onSubjectChange();

  const unsure = detections.filter((d) => (d.needsConfirmation || []).length);
  $("#detect-hint").textContent = unsure.length
    ? `有 ${unsure.length} 个文件的「${[...new Set(unsure.flatMap((d) => d.needsConfirmation))]
        .map((k) => ({ year: "年份", session: "回次", subject: "科目", course: "数学类别" }[k] || k))
        .join("、")}」没能从文件名认出来（答案册常常只写「答案」），请确认上面几栏。`
    : "已从文件名认出年度、回次与科目。不对就直接改。";
  refreshStartButton();
}

function renderUploads() {
  const box = $("#upload-list");
  box.replaceChildren();
  for (const [index, upload] of build.uploads.entries()) {
    const row = el("div", "upload-row" + (upload.state === "failed" ? " is-bad" : ""));
    row.append(el("span", "upload-name", upload.fileName));
    if (upload.state === "uploading") {
      row.append(el("span", "hint", "上传中…"));
    } else if (upload.state === "failed") {
      row.append(el("span", "hint", upload.message || "上传失败"));
    } else {
      const role = el("select", "upload-role");
      for (const [value, label] of Object.entries(ROLE_LABEL)) {
        const option = el("option", "", label);
        option.value = value;
        role.append(option);
      }
      role.value = upload.role;
      role.setAttribute("aria-label", `${upload.fileName} 是哪一份`);
      role.addEventListener("change", () => { upload.role = role.value; refreshStartButton(); });
      row.append(role);
      row.append(el("span", "hint", `${Math.round(upload.sizeBytes / 1024)} KB`));
    }
    const drop = actionButton("移除", async () => {
      build.uploads.splice(index, 1);
      renderUploads();
      refreshStartButton();
    }, "quiet-button");
    row.append(drop);
    box.append(row);
  }
}

function onSubjectChange() {
  $("#course-field").hidden = $("#paper-subject").value !== "MATHEMATICS";
}

function currentPlan() {
  const ready = build.uploads.filter((u) => u.state === "ready");
  const booklets = ready.filter((u) => u.role === "QUESTION_BOOKLET");
  const answers = ready.filter((u) => u.role === "ANSWER_KEY");
  const booklet = booklets[0];
  const answer = answers[0];
  const subject = $("#paper-subject").value;
  const params = {
    questionBooklet: booklet?.uploadId,
    answerKey: answer?.uploadId,
    session: $("#paper-session").value.trim(),
    subject,
    course: subject === "MATHEMATICS" ? $("#paper-course").value : null,
    language: $("#paper-language").value,
    ocrProfile: $("#ocr-profile").value || null,
    proofreadProfile: $("#proofread-profile").value || null,
    textProfile: $("#text-profile").value || null,
    explainProfile: $("#explain-profile").value || null,
    proofreadPages: Boolean($("#proofread-profile").value),
    proofreadPaper: Boolean($("#text-profile").value),
    explain: Boolean($("#explain-profile").value),
    explainLimit: Number($("#opt-explain-limit").value || 0),
    stopAtDraft: $("#opt-stop-draft").checked,
    force: $("#opt-force").checked,
  };
  const problems = [];
  const warnings = [];
  if (!booklet) problems.push("还没有题册 PDF");
  /* 一条任务只处理一组文件。多拖进来的那些原来被 find() 静默丢掉——界面显示
     "准备就绪"，而其中几份根本不会被读。批次配对做好之前，这里必须明说。 */
  if (booklets.length > 1) {
    problems.push(`有 ${booklets.length} 份题册，一次只能做一套卷；` +
      "请只留下这一套的题册，其余的做完再上传");
  }
  if (answers.length > 1) {
    problems.push(`有 ${answers.length} 份答案册，一次只能做一套卷；请只留下这一套的`);
  }
  /* 缺答案册不挡"开始提取"，只挡"发布评分题"。这是两件事：题册自己就能识别，
     没有正解表的是答案。原来这里一票否决，于是先传到的题册什么都做不了。 */
  if (!answer) {
    warnings.push("没有答案册：可以先识别题册，但在正解表到位之前不能定稿答案，"
      + "这套卷发布不了评分题");
  }
  if (!/^(19|20)\d{2}-[12]$/.test(params.session)) problems.push("年度与回次要写成 2023-2 这样");
  if (!subject) problems.push("还没确认科目");
  if (!params.ocrProfile) problems.push("还没选 OCR 模型");
  return { params, problems, warnings };
}

function refreshStartButton() {
  const { problems, warnings } = currentPlan();
  $("#start-build").disabled = problems.length > 0 || Boolean(build.jobId);
  // 挡住开始的原因和"能开始但有代价"的提醒分开说：把警告混进错误里，用户会以为
  // 自己被挡住了；把错误混进警告里，他会以为点了就能跑。
  $("#setup-error").textContent = build.jobId
    ? "已有一条制课任务在跑，等它结束再开下一条。"
    : problems.join("；");
  const notice = $("#setup-warning");
  if (notice) {
    notice.textContent = problems.length ? "" : warnings.join("；");
    notice.hidden = Boolean(problems.length) || warnings.length === 0;
  }
}

// ── 流水线视图 ────────────────────────────────────────────────────────────

const STEP_MARK = { done: "✓", running: "▶", pending: "○", skipped: "–", failed: "✗" };

function renderSteps(progress) {
  const list = $("#pipeline-steps");
  list.replaceChildren();
  for (const step of progress.steps || []) {
    const item = el("li", `pipeline-step is-${step.status}`);
    item.append(el("span", "pipeline-mark", STEP_MARK[step.status] || "○"));
    const body = el("div", "pipeline-body");
    body.append(el("strong", "", step.label));
    if (step.detail) body.append(el("span", "pipeline-detail", step.detail));
    item.append(body);
    list.append(item);
  }
}

function renderLog(progress) {
  const log = $("#build-log");
  const lines = progress.log || [];
  if (lines.length === build.logLines) return;
  build.logLines = lines.length;
  const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 40;
  log.textContent = lines.join("\n");
  if (atBottom) log.scrollTop = log.scrollHeight;
}

const RUN_LABEL = {
  QUEUED: "排队中", RUNNING: "进行中", SUCCEEDED: "已完成", FAILED: "失败",
  PARTIAL_FAILED: "部分失败", CANCEL_REQUESTED: "正在停止", CANCELLED: "已停止",
  INTERRUPTED: "已中断",
};

function renderResult(job) {
  const box = $("#result-summary");
  const progress = job.progress || {};
  if (!["SUCCEEDED", "PARTIAL_FAILED"].includes(job.status)) { box.hidden = true; return; }
  box.replaceChildren();
  const published = progress.published;
  box.append(el("h3", "result-title",
    published ? "已发布到私人题库" : "已做到待复核，尚未发布"));
  const rows = [
    ["来源", progress.sourceId || "—"],
    ["工作目录", progress.workDir || "—"],
    ["题量", `${progress.questionCount ?? "—"} 题 · ${progress.completeness || "—"}`],
    ["把关等级", progress.reviewGrade || "—"],
    ["机器校验", progress.attest
      ? `题册 ${progress.attest.booklet_attested}/${progress.attest.booklet_pages} 页 · `
        + `答案 ${progress.attest.answer_attested}/${progress.attest.answer_pages} 页`
      : "—"],
  ];
  const quality = progress.quality || {};
  const coverage = quality.coverage || null;
  const quarantined = (quality.quarantinedQuestions || []).length;
  // 隔离量和覆盖率一起报。只报其中一个都会误导：全部隔离看起来像零错误，
  // 只看覆盖率则漏掉实际损失。
  rows.push(["自动隔离", quarantined ? `${quarantined} 题（其余照常发布）` : "无"]);
  if (coverage && coverage.result) {
    rows.push(["复核覆盖", coverage.result === "PASS" ? "完整"
      : (coverage.explanation || coverage.result)]);
  }
  if (published) rows.push(["发布版本", `${published.paperId} 第 ${published.version} 版`]);
  // 题目和详解分开说：详解失败不能让已经发布的题看起来整套都失败了。
  if (progress.explanations) rows.push(["详解", String(progress.explanations)]);
  for (const [label, value] of rows) {
    const row = el("div", "result-row");
    row.append(el("span", "result-label", label), el("span", "result-value", String(value)));
    box.append(row);
  }

  /* 结果先说系统做完了什么、自己处理了什么、隔离了什么。人工复核是可选的下一步，
     不是"还欠着的作业"——默认自动模式下正常通过的内容不需要任何人签名。 */
  const handled = [];
  if (progress.reviewGrade === "MACHINE_ATTESTED") {
    handled.push("机器校验：题干与选项逐字来自 OCR，答案取自正解表并与读到的选项对过；"
      + "没有人逐页比对原图，页面区域几何也未验证。");
  }
  if (quarantined) {
    handled.push(`${quarantined} 题未能确认，已隔离并写明理由；其余内容照常发布，不受影响。`);
  }
  if (coverage && coverage.result && coverage.result !== "PASS") {
    handled.push(coverage.explanation || "整卷复核没有覆盖完整，未覆盖部分的结论未知。");
  }
  if ((progress.attestErrors || []).length) {
    handled.push(`有 ${progress.attestErrors.length} 页没通过机器校验，未收录进这一版。`);
  }
  if (progress.stopAtDraft) {
    handled.push("按要求停在待复核：内容已通过自动校验，等你确认后再发布。");
  }
  if (handled.length) {
    box.append(el("h4", "", "系统做了什么"));
    const list = document.createElement("ul");
    for (const line of handled) list.append(el("li", "", line));
    box.append(list);
  }

  const links = el("div", "result-links");
  // 主按钮是"去用它"，不是"去复核它"：正常通过的内容不需要任何人签名。
  const practise = el("a", "primary-button", "查看可练内容");
  practise.href = published ? "/practice" : "/studio/library" + (progress.sourceId
    ? `#/source/${encodeURIComponent(progress.sourceId)}` : "");
  links.append(practise);
  const library = el("a", "btn btn-outline", "查看自动处理详情");
  library.href = "/studio/library" + (progress.sourceId
    ? `#/source/${encodeURIComponent(progress.sourceId)}` : "");
  links.append(library);
  const editor = el("a", "btn btn-outline", "开启人工复核");
  editor.href = "/studio/editor" + (progress.sourceId
    ? `?source=${encodeURIComponent(progress.sourceId)}` : "");
  links.append(editor);
  box.append(links);
  box.hidden = false;
}

function applyJob(job) {
  const progress = job.progress || {};
  $("#run-status").textContent = RUN_LABEL[job.status] || job.status;
  $("#run-status").dataset.status =
    job.status === "SUCCEEDED" ? "ok"
      : ["QUEUED", "RUNNING", "CANCEL_REQUESTED"].includes(job.status) ? "run" : "bad";
  $("#run-meta").textContent =
    `任务 ${job.jobId} · ${progress.stage || job.status}`
    + (progress.percent != null ? ` · ${progress.percent}%` : "");
  renderSteps(progress);
  renderLog(progress);
  renderResult(job);
  const live = ["QUEUED", "RUNNING", "CANCEL_REQUESTED"].includes(job.status);
  $("#cancel-build").hidden = !live;
  $("#refresh-build").hidden = false;
  if (!live) {
    stopPolling();
    build.jobId = null;
    refreshStartButton();
    if (job.status === "FAILED") {
      // 任务失败时进度里只有一条通用说明；把它显示出来，别让人对着空面板猜。
      $("#build-log").textContent =
        (progress.log || []).join("\n")
        + `\n✗ 任务失败（${progress.errorCode || "未知原因"}）：${progress.message || ""}`;
    }
  }
}

async function pollOnce() {
  if (!build.jobId) return;
  const { job } = await api(`/api/v1/admin/jobs/${build.jobId}`);
  applyJob(job);
}

function startPolling() {
  stopPolling();
  build.timer = setInterval(() => {
    if (document.hidden) return;
    pollOnce().catch((error) => { stopPolling(); showError(error); });
  }, POLL_MS);
}

function stopPolling() {
  if (build.timer) clearInterval(build.timer);
  build.timer = null;
}

async function renderRecentRuns() {
  const box = $("#recent-runs");
  const { jobs } = await api("/api/v1/admin/jobs").catch(() => ({ jobs: [] }));
  const runs = (jobs || []).filter((j) => j.jobType === "MAKE_PAPER").slice(0, 8);
  box.replaceChildren();
  if (!runs.length) { box.append(el("p", "subtitle", "还没有制课任务。")); return; }
  for (const job of runs) {
    const card = jobCard(job, renderRecentRuns);
    card.append(actionButton("查看这条", async () => {
      build.jobId = job.jobId;
      build.logLines = 0;
      await pollOnce();
      if (["QUEUED", "RUNNING"].includes(job.status)) startPolling();
    }, "quiet-button"));
    box.append(card);
  }
}

// ── 启动 ──────────────────────────────────────────────────────────────────

/* 还没开跑时的步骤表。跟着模型下拉走：没选复核模型，那一步现在就显示会跳过。 */
function renderPlannedSteps() {
  if (build.jobId) return;
  const skipped = {
    PROOFREAD_PAGES: !$("#proofread-profile").value,
    PROOFREAD_PAPER: !$("#text-profile").value,
    EXPLAIN: !$("#explain-profile").value || $("#opt-stop-draft").checked,
    PUBLISH: $("#opt-stop-draft").checked,
  };
  renderSteps({
    steps: PIPELINE_STEPS.map(([key, label]) => ({
      key, label,
      status: skipped[key] ? "skipped" : "pending",
      detail: skipped[key] ? "本次跳过" : "",
    })),
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const input = $("#pdf-input");
  const zone = $("#dropzone");
  input.addEventListener("change", act(async () => {
    for (const file of [...input.files]) await uploadOne(file);
    input.value = "";
  }));
  for (const type of ["dragenter", "dragover"]) {
    zone.addEventListener(type, (event) => {
      event.preventDefault();
      zone.classList.add("is-hot");
    });
  }
  for (const type of ["dragleave", "drop"]) {
    zone.addEventListener(type, () => zone.classList.remove("is-hot"));
  }
  zone.addEventListener("drop", act(async (event) => {
    event.preventDefault();
    for (const file of [...(event.dataTransfer?.files || [])]) {
      if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
        await uploadOne(file);
      } else {
        showNotice(`${file.name} 不是 PDF，已跳过。`);
      }
    }
  }));

  $("#paper-subject").addEventListener("change", () => { onSubjectChange(); refreshStartButton(); });
  $("#paper-course").addEventListener("change", (e) => { e.target.dataset.touched = "1"; });
  for (const id of ["paper-session", "paper-language", "opt-stop-draft", "opt-force"]) {
    $("#" + id).addEventListener("change", refreshStartButton);
  }
  $("#opt-stop-draft").addEventListener("change", renderPlannedSteps);
  $("#paper-session").addEventListener("input", refreshStartButton);

  $("#model-pill").addEventListener("click", act(async () => {
    $("#model-pill").textContent = "检测中…";
    fillPickers(await loadModels(true));
  }));

  $("#start-build").addEventListener("click", act(async () => {
    const { params, problems } = currentPlan();
    if (problems.length) throw new Error(problems.join("；"));
    const job = await api("/api/v1/admin/papers", {
      method: "POST", body: JSON.stringify(params),
    });
    build.jobId = job.jobId;
    build.logLines = 0;
    $("#build-log").textContent = "";
    $("#result-summary").hidden = true;
    applyJob(job);
    startPolling();
    refreshStartButton();
    showNotice("制课任务已创建，在后台执行。可以离开这个页面。");
    await renderRecentRuns();
  }));

  $("#cancel-build").addEventListener("click", act(async () => {
    if (!build.jobId) return;
    await api(`/api/v1/admin/jobs/${build.jobId}/cancel`, { method: "POST", body: "{}" });
    showNotice("已请求停止，任务会在下一个检查点停下；已完成的产物都留着。");
    await pollOnce();
  }));
  $("#refresh-build").addEventListener("click", act(pollOnce));

  (async () => {
    try {
      fillPickers(await loadModels());
    } catch (error) {
      if (error.status === 401 || error.status === 403) showAdminBlocked();
      else showError(error);
    }
    renderPlannedSteps();
    await renderRecentRuns().catch(() => {});
    // 页面刷新后接回仍在跑的那条任务，不让人以为任务丢了。
    const { jobs } = await api("/api/v1/admin/jobs?status=RUNNING").catch(() => ({ jobs: [] }));
    const live = (jobs || []).find((j) => j.jobType === "MAKE_PAPER");
    if (live) {
      build.jobId = live.jobId;
      await pollOnce().catch(() => {});
      startPolling();
    }
    refreshStartButton();
  })();
});
