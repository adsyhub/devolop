"use strict";
/* ==========================================================================
   运维
   --------------------------------------------------------------------------
   跨来源的东西：后台任务、学习者报上来的内容问题、解析与评阅标准、备份与恢复、
   诊断与个人数据。它们不属于任何一套卷的流水线，所以不在课程库里。
   ========================================================================== */

const OPS = ["jobs", "issues", "explanations", "rubrics", "backups", "data"];

// ── 运维 ─────────────────────────────────────────────────────────────────
function showOps(name) {
  for (const tab of $$("#ops-switch .category-tab")) {
    tab.classList.toggle("is-active", tab.dataset.ops === name);
    tab.setAttribute("aria-selected", String(tab.dataset.ops === name));
  }
  for (const panel of $$(".ops-panel")) panel.hidden = panel.dataset.ops !== name;
}
for (const tab of $$("#ops-switch .category-tab")) {
  tab.addEventListener("click", () => Router.go(`#/ops/${tab.dataset.ops}`));
}

async function loadManagement() {
  const [jobs, sources, issues, backups] = await Promise.all([
    api("/api/v1/admin/jobs"),
    api("/api/v1/admin/sources"),
    api("/api/v1/admin/content-issues"),
    api("/api/v1/admin/backups"),
  ]);
  state.jobs = jobs.jobs;
  state.sources = sources.sources;

  const sourceSelect = $("#production-source");
  const old = sourceSelect.value;
  sourceSelect.replaceChildren();
  for (const s of sources.sources) {
    // 运维的来源选择器原来只写「场次 科目」：两份数学卷在这里长得一模一样，
    // 而选错的那一份会被真的跑起来。
    const o = el("option", "", sourceLabel(s));
    o.value = s.sourceId;
    sourceSelect.append(o);
  }
  if (old) sourceSelect.value = old;
  else if (state.sourceId) sourceSelect.value = state.sourceId;

  const list = $("#job-list");
  list.replaceChildren();
  if (!jobs.jobs.length) list.append(el("p", "subtitle", "还没有后台任务。"));
  for (const job of jobs.jobs) list.append(jobCard(job, loadManagement));

  const issueList = $("#issue-list");
  issueList.replaceChildren();
  const openIssues = issues.issues.filter((i) => !["CLOSED", "REJECTED", "DUPLICATE"].includes(i.status));
  $("#issue-badge").textContent = openIssues.length ? String(openIssues.length) : "";
  if (!issues.issues.length) issueList.append(el("p", "subtitle", "没有待处理的内容问题。"));
  for (const issue of issues.issues) {
    const card = el("article", "job-card");
    card.append(
      el("p", "", `${issue.status} · ${issue.issueType} · ${issue.description}`),
      el("p", "subtitle", `题版本：${issue.questionVersionId}`),
      /* 从问题跳到解析表单，ID 由上下文带过去。原来要在这里把题目版本 ID 抄下来，
         再切到另一个面板手工粘进去——抄错一位就是给另一道题写了解析。 */
      actionButton("给这道题写解析", async () => {
        Router.go("#/ops/explanations");
        const field = $("#explanation-qv");
        field.value = issue.questionVersionId;
        $("#explanation-text").focus();
      }),
      actionButton("更新处理状态", async () => {
        const status = prompt(
          "TRIAGED / IN_PROGRESS / FIXED_PENDING_REVIEW / CLOSED / DUPLICATE / REJECTED", issue.status);
        if (!status) return;
        const reason = prompt("处理说明");
        if (!reason) return;
        await api(`/api/v1/admin/content-issues/${issue.issueId}`, {
          method: "PUT", body: JSON.stringify({ status, reason }),
        });
        await loadManagement();
      }));
    issueList.append(card);
  }

  const backupList = $("#backup-list");
  backupList.replaceChildren();
  if (!backups.backups.length) backupList.append(el("p", "subtitle", "还没有备份。"));
  for (const backup of backups.backups) {
    const row = el("p");
    const link = el("a", "", `下载 ${backup.name}`);
    link.href = `/api/v1/admin/backups/${backup.id}/download`;
    row.append(link, document.createTextNode(` · ${backup.sizeBytes} 字节 `),
      actionButton("校验", async () => {
        await api(`/api/v1/admin/backups/${backup.id}/verify`, { method: "POST", body: "{}" });
        $("#management-status").textContent = "备份校验通过";
      }),
      actionButton("恢复到新目录", async () => {
        const dir = prompt("工作区中的新目录名称，例如 restored-2026-09");
        if (!dir) return;
        await api(`/api/v1/admin/backups/${backup.id}/restore`, {
          method: "POST", body: JSON.stringify({ targetDirectory: dir }),
        });
        $("#management-status").textContent = "已恢复到新目录，当前运行库未被替换";
      }));
    backupList.append(row);
  }
}

$("#management-refresh").addEventListener("click", act(loadManagement));
setInterval(() => {
  // 备份、制课都是后台任务：人停在这一页，列表就自己更新。
  if (!document.hidden) loadManagement().catch(showError);
}, 3000);

$("#production-form").addEventListener("submit", act(async (event) => {
  event.preventDefault();
  await api("/api/v1/admin/jobs", {
    method: "POST",
    body: JSON.stringify({
      jobType: $("#production-kind").value, sourceId: $("#production-source").value,
      params: {
        role: $("#production-role").value,
        pages: $("#production-pages").value || null,
        provider: $("#production-provider").value || undefined,
      },
    }),
  });
  await loadManagement();
}));

$("#backup-create").addEventListener("click", act(async () => {
  await api("/api/v1/admin/backup", { method: "POST", body: JSON.stringify({ mode: $("#backup-mode").value }) });
  await loadManagement();
}));

$("#explanation-form").addEventListener("submit", act(async (event) => {
  event.preventDefault();
  const result = await api(`/api/v1/admin/questions/${$("#explanation-qv").value}/explanations`, {
    method: "POST",
    body: JSON.stringify({
      payload: {
        kind: $("#explanation-kind").value, language: $("#explanation-language").value,
        contentAst: [{ type: "paragraph", value: $("#explanation-text").value }],
      },
      baseRevision: Number($("#explanation-base").value),
      status: $("#explanation-status").value, reviewer: $("#explanation-reviewer").value,
    }),
  });
  $("#explanation-base").value = result.revision;
  $("#explanation-result").textContent = `第 ${result.revision} 版已保存：${result.status}`;
}));

$("#rubric-form").addEventListener("submit", act(async (event) => {
  event.preventDefault();
  await api("/api/v1/admin/rubrics", {
    method: "POST",
    body: JSON.stringify({
      reviewer: $("#rubric-reviewer").value,
      rubric: {
        name: $("#rubric-name").value, official: false,
        dimensions: $("#rubric-dimensions").value.split("\n").map((x) => x.trim()).filter(Boolean)
          .map((name, i) => ({ id: "dimension-" + i, name, levels: ["待改进", "基本达到", "良好"] })),
      },
    }),
  });
  $("#management-status").textContent = "评阅标准已保存，可在记述复盘中选择";
}));

(function buildDataTools() {
  $("#data-tools").append(
    actionButton("下载脱敏诊断", async () => {
      const data = await api("/api/v1/admin/diagnostics");
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const a = el("a");
      a.href = url;
      a.download = "eju-diagnostics.json";
      a.click();
      URL.revokeObjectURL(url);
    }),
    actionButton("预览过期渲染缓存", async () => {
      const plan = await api("/api/v1/admin/retention/preview", { method: "POST", body: "{}" });
      if (!plan.files.length) { $("#management-status").textContent = "没有符合保留策略的缓存"; return; }
      if (!confirm(`将清理 ${plan.files.length} 个可重新生成的渲染缓存，释放 ${plan.bytes} 字节。` +
                   "源文件、媒体、历史和备份均保留。确认执行？")) return;
      await api("/api/v1/admin/retention/apply", { method: "POST", body: JSON.stringify({ planId: plan.planId }) });
      $("#management-status").textContent = "缓存已清理";
    }),
    actionButton("预览清空个人学习记录", async () => {
      const plan = await api("/api/v1/admin/personal-data/preview", { method: "POST", body: "{}" });
      if (!confirm(`清空范围：${JSON.stringify(plan.counts)}。保留题库、来源和内容问题报告。` +
                   "执行前会自动生成并校验备份。确认清空？")) return;
      await api("/api/v1/admin/personal-data/delete", {
        method: "POST", body: JSON.stringify({ planId: plan.planId, confirmed: true }),
      });
      localStorage.removeItem(`eju.activeSession.${state.libraryInstanceId}`);
      for (const key of Object.keys(localStorage)) {
        if (key.startsWith(`eju.draft.${state.libraryInstanceId}.`) ||
            key.startsWith(`eju.note.${state.libraryInstanceId}.`)) localStorage.removeItem(key);
      }
      $("#management-status").textContent = "个人学习记录已清空，恢复备份仍保留";
    }),
  );
})();



// ── 路由与启动 ───────────────────────────────────────────────────────────
Router
  .add(/^#\/ops\/(\w+)$/, async ([, name]) => {
    showOps(OPS.includes(name) ? name : "jobs");
    await refresh();
  })
  .setFallback(async () => {
    showOps("jobs");
    Router.replace("#/ops/jobs");
    await refresh();
  });

async function refresh() {
  try {
    await loadManagement();
  } catch (error) {
    if (error.status === 401 || error.status === 403) showAdminBlocked();
    else throw error;
  }
}

async function boot() {
  await loadLibraryInstanceId();
  await Router.start();
}

boot().catch(showError);
