"use strict";
/* ==========================================================================
   课程库
   --------------------------------------------------------------------------
   docs/PIPELINE.md 的状态流就是这个页面的骨架：
     RECEIVED → PROBED → RENDERED → EXTRACTED → REVIEWED
             → ASSEMBLED → VALIDATED → PUBLISHED
   「任何阶段产生未解决的 contract error 都不能进入下一阶段」——所以未到达的
   阶段是锁住的，而且锁上必须写明为什么。

   制课台按一下就走完这八步；这里是逐步来的地方：某一步要单独重跑、结构要手填、
   某一版要单独签署，都在这里做。两条路走的是同一套闸门。
   ========================================================================== */

const main = $("#studio-main");

function sessionSortKey(session) {
  if (!session) return 0;
  const match = /^(\d{4})-(\d+)$/.exec(session);
  if (match) {
    return Number(match[1]) * 10 + Number(match[2]);
  }
  return 0;
}

function compareSourcesBySession(a, b, order = "ASC") {
  const keyA = sessionSortKey(a.session);
  const keyB = sessionSortKey(b.session);
  if (keyA !== keyB) {
    return order === "DESC" ? keyB - keyA : keyA - keyB;
  }
  const formA = (a.expectedForms || [])[0] || a.inventoryId || a.sourceId || "";
  const formB = (b.expectedForms || [])[0] || b.inventoryId || b.sourceId || "";
  return formA.localeCompare(formB);
}

function getFilteredSources() {
  let list = state.sources || [];
  const q = (state.searchQuery || "").trim().toLowerCase();
  if (q) {
    list = list.filter((s) => {
      const parts = [
        s.session,
        s.sourceId,
        s.subject,
        I18N.subjects[s.subject],
        s.inventoryId,
        ...(s.expectedForms || []),
        I18N.languages[s.language],
      ].filter(Boolean).join(" ").toLowerCase();
      return parts.includes(q);
    });
  }
  const order = state.sortOrder || "ASC";
  list = [...list].sort((a, b) => compareSourcesBySession(a, b, order));
  return list;
}

function renderSubjectTabs() {
  const nav = $("#subject-tabs");
  if (!nav) return;
  nav.replaceChildren();

  const allFiltered = getFilteredSources();
  const counts = {};
  for (const s of allFiltered) {
    counts[s.subject] = (counts[s.subject] || 0) + 1;
  }

  const validSubjects = SUBJECT_DEFINITIONS.map((d) => d.id);
  if (!validSubjects.includes(state.selectedSubject) || !counts[state.selectedSubject]) {
    state.selectedSubject = validSubjects.find((id) => counts[id] > 0) || "JAPANESE";
  }

  for (const entry of SUBJECT_DEFINITIONS) {
    const count = counts[entry.id] || 0;
    const tab = el("button", "category-tab" + (state.selectedSubject === entry.id ? " is-active" : ""));
    tab.type = "button";
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", String(state.selectedSubject === entry.id));
    const dot = el("span", "category-dot");
    dot.style.background = entry.color;
    dot.setAttribute("aria-hidden", "true");
    tab.append(dot, el("span", "", entry.label), el("span", "tab-badge", String(count)));
    tab.addEventListener("click", () => {
      state.selectedSubject = entry.id;
      Router.replace(`#/subject/${entry.id}`);
      renderSubjectTabs();
      renderSourceRows();
    });
    nav.append(tab);
  }
}

async function renderSourceRows() {
  const container = $("#source-rows");
  container.replaceChildren();

  const sortSelect = $("#source-sort-order");
  if (sortSelect) sortSelect.value = state.sortOrder || "ASC";

  renderSubjectTabs();

  const filtered = getFilteredSources();
  const activeSubject = state.selectedSubject || "JAPANESE";
  const subDef = SUBJECT_DEFINITIONS.find((d) => d.id === activeSubject) || SUBJECT_DEFINITIONS[0];
  const sourcesInActive = filtered.filter((s) => s.subject === activeSubject);
  const total = state.sources.length;

  if (state.searchQuery) {
    $("#sources-status").textContent = `搜索匹配 ${sourcesInActive.length} 套${subDef.label}试卷（全库共 ${total} 套）`;
  } else {
    $("#sources-status").textContent = `${subDef.label}共 ${sourcesInActive.length} 套试卷（全库共 ${total} 套）`;
  }

  if (!sourcesInActive.length) {
    container.append(el("p", "empty-hint",
      state.searchQuery ? `未在该科目中找到匹配“${state.searchQuery}”的试卷来源。` :
      "该科目下还没有来源。先用 CLI 的 source-init 登记，再回到这里导入文件。"));
    return;
  }

  const targetSubjects = [activeSubject];

  for (const subId of targetSubjects) {
    const subDef = SUBJECT_DEFINITIONS.find((d) => d.id === subId) || {
      id: subId, label: I18N.subjects[subId] || subId, color: "var(--ai)", icon: "📄", desc: "",
    };
    const sourcesInGroup = filtered.filter((s) => s.subject === subId);
    if (!sourcesInGroup.length) continue;

    const groupSec = el("section", `subject-group subject-${subDef.id}`);

    // Group Header
    const header = el("div", `subject-group-header subject-${subDef.id}`);
    const lead = el("div", "subject-group-lead");
    lead.append(
      el("span", "subject-group-icon", subDef.icon),
      el("h2", "", subDef.label),
    );
    const meta = el("div", "subject-group-meta");
    if (subDef.desc) meta.append(el("span", "subject-group-desc", subDef.desc));
    meta.append(el("span", "subject-group-stats", `${sourcesInGroup.length} 套试卷`));
    header.append(lead, meta);
    groupSec.append(header);

    const rowsList = el("div", "source-rows-list");
    for (const source of sourcesInGroup) {
      const facts = deliveryOf(source.sourceId);
      const published = facts.published;
      const row = el("article", `source-row subject-${source.subject}`);

      const head = el("div", "source-row-head");
      head.append(el("strong", "", sourceLabel(source)));
      head.append(el("em", "", source.sourceId));
      head.append(publicationBadge(facts.publicationState));
      row.append(head);

      const foot = el("div", "source-row-foot");
      const left = el("span");
      if (published) {
        const bits = [`v${published.version}`];
        if (published.questionCount != null) bits.push(`${published.questionCount} 题`);
        bits.push(I18N.translateCompleteness(published.completeness));
        if (published.reviewGrade) {
          bits.push(REVIEW_GRADES[published.reviewGrade] || published.reviewGrade);
        }
        left.append(document.createTextNode(bits.join(" · ")));
      } else {
        left.append(document.createTextNode("还没有产出可练版本"));
      }
      const missing = missingRoles(source);
      if (missing.length) left.append(document.createTextNode(` · ⚠ 缺${missing.join("、")}`));
      foot.append(left);
      const link = el("a", "", "查看 →");
      link.href = `#/source/${source.sourceId}`;
      link.addEventListener("click", (e) => {
        e.preventDefault();
        Router.go(`#/source/${source.sourceId}`);
      });
      foot.append(link);
      row.append(foot);
      rowsList.append(row);
    }
    groupSec.append(rowsList);
    container.append(groupSec);
  }
}

$("#btn-refresh-inventory").addEventListener("click", act(async () => {
  await loadSources();
  await renderSourceRows();
}));
$("#source-search-input")?.addEventListener("input", (e) => {
  state.searchQuery = e.target.value;
  renderSourceRows();
});
$("#source-sort-order")?.addEventListener("change", (e) => {
  state.sortOrder = e.target.value;
  try { localStorage.setItem("eju.studio.sortOrder", state.sortOrder); } catch {}
  renderSourceRows();
});
$("#source-back").addEventListener("click", () => {
  Router.go(state.selectedSubject && state.selectedSubject !== "ALL" ? `#/subject/${state.selectedSubject}` : "#/");
});

// ── L2：单来源的生产状态 ─────────────────────────────────────────────────
/* 这一页只回答生产端关心的四件事：学习者取不取得到、产出了什么、输入缺不缺、
   还有什么没定下来。

   原来这里是八个阶段的推进面板（登记 → 导入 → 探测渲染 → 逐页复核 → 签署结构
   → 组装预检 → 签署整卷 → 发布）。那条路不是这个库的来路：在库的 149 套可练卷
   是自动流水线（制课页的 MAKE_PAPER，以及 scripts/attest_and_publish.py）做出来
   的，全程不经过这些按钮。把它们摆成待办，会让人以为非手工签完不可；而那些
   ✓ 又是照清单里的 pipelineStatus 画的——退役的伪造批次至今写着 PUBLISHED，
   于是勾满八步的卷，学习者其实一道题也取不到。 */
async function openSource(sourceId) {
  state.sourceId = sourceId;
  // 切来源时旧请求可能还在路上。带一个序号，回来得晚的那份直接丢掉。
  const ticket = ++state.openSeq;
  if (!(await ensureSources())) return;
  const source = state.sources.find((s) => s.sourceId === sourceId);
  if (!source) throw new Error(`找不到来源 ${sourceId}`);

  showOnly(main, "view-source");
  $("#source-eyebrow").textContent = source.sourceId;
  $("#source-heading").textContent = sourceLabel(source);
  $("#source-meta").textContent =
    `${I18N.languages[source.language] || source.language} · 已导入 ` +
    `${(source.roles || []).map((r) => I18N.roles?.[r] || r).join("、") || "（无文件）"}`;

  const box = $("#source-status");
  box.replaceChildren(el("p", "subtitle", "正在读取这套来源的状态…"));
  let summary;
  try {
    summary = await api(`/api/v1/admin/sources/${encodeURIComponent(sourceId)}/summary`);
  } catch (error) {
    if (ticket !== state.openSeq) return;
    box.replaceChildren(el("p", "status-line is-error", `读不到这套来源的状态：${error.message}`));
    return;
  }
  if (ticket !== state.openSeq) return;
  renderSourceStatus(source, summary);
}

function statusCard(title, rows, note) {
  const card = el("section", "status-card");
  card.append(el("h2", "", title));
  const body = el("div", "stage-facts");
  for (const [label, value] of rows) body.append(factRow(label, value));
  card.append(body);
  if (note) card.append(el("p", "subtitle", note));
  return card;
}

function renderSourceStatus(source, summary) {
  const box = $("#source-status");
  box.replaceChildren();
  const published = summary.published;
  const roles = new Set(source.roles || []);

  const head = el("section", "status-card");
  head.append(el("h2", "", "交付状态"));
  const headline = el("div", "status-headline");
  headline.append(publicationBadge(summary.publicationState));
  headline.append(el("span", "", summary.nextAction?.message || ""));
  head.append(headline);
  // 停用的理由是当初写进交付记录的原话，照抄，不复述。
  if (published?.deliveryNote) head.append(el("p", "subtitle", published.deliveryNote));
  box.append(head);

  box.append(statusCard("产出了什么", published ? [
    ["已发布版本", `v${published.version}`],
    ["题量", published.questionCount ?? "—"],
    ["完整度", I18N.translateCompleteness(published.completeness)],
    ["把关等级", REVIEW_GRADES[published.reviewGrade] || published.reviewGrade || "未记录"],
    ["发布时间", published.publishedAt || "—"],
  ] : [["已发布版本", "尚未产出可练版本"]]));

  box.append(statusCard("输入文件", [
    ["题册", roles.has("QUESTION_BOOKLET") ? "✓ 已导入" : "缺"],
    ["答案册", roles.has("ANSWER_KEY") ? "✓ 已导入" : "缺"],
    ["听力音频", roles.has("AUDIO") ? "✓ 已导入" : "未导入"],
  ], roles.has("ANSWER_KEY") ? null
     : "没有答案册就产不出可验证的答案：题面读得再准也没有正解可对，" +
       "这套卷不会被发布。先补上这一回次的正解表。"));

  const findings = summary.findings || {};
  box.append(statusCard("还没定下来的内容", [
    ["已验证题量", summary.coverage?.verifiedQuestions ?? "—"],
    ["隔离题量", findings.quarantined ?? 0],
    ["疑点总数", findings.total ?? 0],
  ], (findings.coverage || {}).explanation || null));

  const actions = el("section", "status-card");
  actions.append(el("h2", "", "在哪里继续"));
  const list = el("div", "stage-actions");
  for (const [label, href, cls] of [
    ["去制课（上传 PDF 一键做卷）", "/studio/build", "primary-button"],
    ["运维：任务与重试", "/studio/ops#/ops/jobs", "btn btn-outline"],
    ["运维：内容问题", "/studio/ops#/ops/issues", "btn btn-outline"],
    ["人工复核（可选）", `/studio/editor?source=${encodeURIComponent(source.sourceId)}`,
     "btn btn-outline"],
  ]) {
    const link = el("a", cls, label);
    link.href = href;
    list.append(link);
  }
  actions.append(list);
  actions.append(el("p", "subtitle",
    "逐页复核是可选工具，不是发布的必经步骤：自动流水线只发布能自证的内容，" +
    "证不出来的留在隔离区，不会被当作已核对。"));
  box.append(actions);
}

async function renderImportJobs() {
  const box = $("#import-jobs");
  box.replaceChildren();
  const jobs = await api("/api/v1/admin/jobs").catch(() => ({ jobs: [] }));
  state.jobs = jobs.jobs || [];
  const imports = state.jobs.filter((j) => j.jobType === "IMPORT_SOURCE").slice(0, 6);
  if (!imports.length) return;
  box.append(el("h3", "", "最近的导入"));
  for (const job of imports) box.append(jobCard(job, renderImportJobs));
}

$("#import-form").addEventListener("submit", act(async (event) => {
  event.preventDefault();
  await api("/api/v1/admin/imports", {
    method: "POST",
    body: JSON.stringify({
      filePath: $("#import-path").value, inventoryId: $("#import-inventory").value,
      role: $("#import-role").value,
    }),
  });
  $("#import-status").textContent = "导入任务已创建，正在后台校验并登记。";
  showNotice("导入任务已创建。");
  await loadSources();
  await renderImportJobs();
}));
$("#import-back").addEventListener("click", () => Router.go("#/"));



// ── 路由与启动 ───────────────────────────────────────────────────────────
Router
  .add(/^#\/source\/([^/]+)\/page\/([A-Z_]+)\/(\d+)$/, ([, sid, role, page]) => {
    // 逐页复核搬到了复核编辑器那一页；老书签仍然能用，直接送过去。
    location.replace(`/studio/editor?source=${encodeURIComponent(decodeURIComponent(sid))}`
      + `&role=${role}&page=${page}`);
  })
  /* 阶段页没有了。老书签不该变成死链，直接落到这套来源的状态页。 */
  .add(/^#\/source\/([^/]+)\/stage\/\d$/, async ([, sid]) => {
    await openSource(decodeURIComponent(sid));
  })
  .add(/^#\/source\/([^/]+)$/, async ([, sid]) => {
    await openSource(decodeURIComponent(sid));
  })
  .add(/^#\/import(?:\?(.*))?$/, async ([, query]) => {
    showOnly(main, "view-import");
    if (!(await ensureSources())) return;
    // 清单条目可以从下拉里挑，不必手打 ID。
    const options = $("#inventory-options");
    options.replaceChildren();
    for (const item of state.inventory?.items || []) {
      const option = el("option");
      option.value = item.inventoryId;
      option.label = sourceLabel(item);
      options.append(option);
    }
    const prefill = new URLSearchParams(query || "").get("inventory");
    if (prefill) $("#import-inventory").value = prefill;
    await renderImportJobs();
  })
  .add(/^#\/subject\/([A-Za-z_]+)$/, async ([, subject]) => {
    state.selectedSubject = subject.toUpperCase();
    try { localStorage.setItem("eju.studio.subject", state.selectedSubject); } catch {}
    showOnly(main, "view-sources");
    if (!(await ensureSources())) return;
    await renderSourceRows();
  })
  .setFallback(async () => {
    const valid = SUBJECT_DEFINITIONS.map((d) => d.id);
    if (!valid.includes(state.selectedSubject)) state.selectedSubject = "JAPANESE";
    showOnly(main, "view-sources");
    if (!(await ensureSources())) return;
    await renderSourceRows();
  });

async function boot() {
  await loadLibraryInstanceId();
  await Router.start();
}

boot().catch(showError);
