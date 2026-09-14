"use strict";
/* ==========================================================================
   题库制作台 · 共用底座
   --------------------------------------------------------------------------
   制作台是四个模块，各是一个页面：

     制课        studio.html          上传 PDF，一条流水线做到可练的卷
     课程库      studio_library.html  来源清单与单套卷的交付状态
     复核编辑器  studio_editor.html   逐页对照原图核对、签署
     运维        studio_ops.html      跨来源的任务、问题、备份

   分成四个页面而不是一个 SPA，是因为这四件事的停留时长完全不同：复核编辑器
   一坐就是几十页，制课页开着等后台跑。同一个页面里切视图，意味着刷新一次就
   把另一件事的现场也丢了。

   这里只放四个页面都要的东西：模块导航、来源清单、阶段推导、任务卡。
   模块专有逻辑在各自的 JS 里。
   ========================================================================== */

const SUBJECT_DEFINITIONS = [
  { id: "JAPANESE", label: "日本語", color: "var(--shu)", icon: "⛩️",
    desc: "日本语（读解 · 听解 · 听读解 · 记述）" },
  { id: "SCIENCE", label: "理科", color: "var(--sci)", icon: "🧪",
    desc: "理科（物理 · 化学 · 生物 合订试卷）" },
  { id: "JAPAN_AND_WORLD", label: "総合科目", color: "var(--kohaku)", icon: "🌏",
    desc: "综合科目（政治 · 经济 · 地理 · 历史）" },
  { id: "MATHEMATICS", label: "数学", color: "var(--midori)", icon: "📐",
    desc: "数学（文科数学 1 类 · 理科数学 2 类）" },
];

const STUDIO_MODULES = [
  { id: "build", href: "/studio/build", label: "制课",
    hint: "上传 PDF，一条流水线做到可练的卷" },
  { id: "library", href: "/studio/library", label: "课程库",
    hint: "来源清单与单套卷的交付状态" },
  { id: "editor", href: "/studio/editor", label: "复核编辑器",
    hint: "逐页对照原图核对、签署" },
  { id: "ops", href: "/studio/ops", label: "运维",
    hint: "跨来源的任务、问题、备份" },
];

Object.assign(state, {
  sources: [],
  delivery: null,
  inventory: null,
  jobs: [],
  sourceId: null,
  models: null,
  selectedSubject: localStorage.getItem("eju.studio.subject") || "JAPANESE",
  sortOrder: localStorage.getItem("eju.studio.sortOrder") || "ASC",
  searchQuery: "",
});

/* 导航在每个页面的 <nav id="studio-modules"> 里生成，当前模块由
   body[data-module] 指明 —— 页面自己知道自己是谁，不靠地址栏猜。 */
function renderModuleNav() {
  const nav = $("#studio-modules");
  if (!nav) return;
  const current = document.body.dataset.module;
  nav.replaceChildren();
  for (const mod of STUDIO_MODULES) {
    const active = mod.id === current;
    const node = el(active ? "span" : "a", "studio-module" + (active ? " is-current" : ""),
                    mod.label);
    if (active) node.setAttribute("aria-current", "page");
    else node.href = mod.href;
    node.title = mod.hint;
    nav.append(node);
  }
}

// ── 来源清单 ──────────────────────────────────────────────────────────────

async function loadSources() {
  /* 三个 admin 请求同时失败时（例如服务以远程模式启动），用 allSettled，否则
     只有第一个被 Promise.all 消费，另外两个变成未处理的 rejection 弹出英文报错。 */
  const [sourcesResult, inventoryResult, jobsResult, deliveryResult] = await Promise.allSettled([
    api("/api/v1/admin/sources"),
    api("/api/v1/admin/inventory"),
    api("/api/v1/admin/jobs"),
    api("/api/v1/admin/studio/delivery"),
  ]);
  if (sourcesResult.status === "rejected") throw sourcesResult.reason;
  if (inventoryResult.status === "rejected") throw inventoryResult.reason;
  state.sources = sourcesResult.value.sources;
  state.inventory = inventoryResult.value;
  state.jobs = jobsResult.status === "fulfilled" ? (jobsResult.value.jobs || []) : [];
  /* 交付状态取不到时留 null，而不是退成空对象：空对象会让每一行都显示"未产出"，
     那是在报告一个并没有查到的事实。deliveryOf() 见到 null 同样给未产出，但
     这里保留区别，便于排查。 */
  state.delivery = deliveryResult.status === "fulfilled"
    ? (deliveryResult.value.sources || {}) : null;
  return state.inventory;
}

/* 本机制作台不需要任何凭证。真出现 403，说明服务是以 --allow-remote 启动的，
   那是启动参数的问题，不是这个页面能修的——把话说清楚，别再抛原始英文。 */
async function ensureSources() {
  if (state.sources.length && state.inventory) return true;
  try {
    await loadSources();
    return true;
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      showAdminBlocked();
      return false;
    }
    throw error;
  }
}

function showAdminBlocked() {
  const line = $("#sources-status") || $("#module-status") || $("#management-status");
  if (!line) return;
  line.textContent =
    "服务拒绝了管理操作。制作台需要服务以本机模式启动（python -m eju_bank serve）。";
  line.classList.add("is-error");
}

async function loadModels(force = false) {
  if (state.models && !force) return state.models;
  state.models = await api("/api/v1/admin/models");
  return state.models;
}

// ── 交付状态 ─────────────────────────────────────────────────────────────
/* 制作台只需要回答一件事：这套卷学习者取不取得到。

   那由 paper_delivery_state 决定，不是"流水线走到第几步"。清单里的
   pipelineStatus 是陈旧值——退役的那批伪造答案卷至今写着 PUBLISHED，照它显示
   会把已停用的卷说成在线。所以这里只认服务端按交付规则算出来的状态。 */
const PUBLICATION = {
  PUBLISHED: { label: "可练", cls: "ok" },
  PUBLISHED_PARTIAL: { label: "可练 · 部分", cls: "ok" },
  SUSPENDED: { label: "已停用", cls: "bad" },
  REVIEW_REQUIRED: { label: "待复核", cls: "warn" },
  NOT_PUBLISHED: { label: "未产出", cls: "warn" },
};

const REVIEW_GRADES = { MACHINE_ATTESTED: "机器校验", HUMAN_SIGNED: "人工签署" };

/* 整屏一次取完。逐套去问 /summary 要读每个工作目录的质量报告，实测 215 套
   两分多钟；这条只读数据库，15 毫秒。 */
async function loadDelivery(force = false) {
  if (state.delivery && !force) return state.delivery;
  const result = await api("/api/v1/admin/studio/delivery");
  state.delivery = result.sources || {};
  return state.delivery;
}

function deliveryOf(sourceId) {
  return (state.delivery || {})[sourceId]
    || { publicationState: "NOT_PUBLISHED", published: null };
}

function publicationBadge(publicationState) {
  const spec = PUBLICATION[publicationState] || { label: publicationState, cls: "warn" };
  return el("span", `delivery-badge is-${spec.cls}`, spec.label);
}

/* 题册与答案册缺哪一份。没有答案册就产不出可验证的答案——这是实际卡住
   一批来源的原因，直接说出来比让人逐步试有用。 */
function missingRoles(source) {
  const roles = new Set(source?.roles || []);
  const names = { QUESTION_BOOKLET: "题册", ANSWER_KEY: "答案册" };
  return Object.keys(names).filter((r) => !roles.has(r)).map((r) => names[r]);
}

// ── 小块 ──────────────────────────────────────────────────────────────────

function metricBox(label, value) {
  const box = el("div", "metric-box");
  box.append(el("div", "metric-val", String(value)), el("div", "metric-lbl", label));
  return box;
}

function factRow(label, value) {
  const row = el("div", "fact-row");
  row.append(el("strong", "", label), el("span", "num", String(value)));
  return row;
}

const JOB_LABELS = {
  MAKE_PAPER: "制课", IMPORT_SOURCE: "导入", PROBE: "探测", RENDER: "渲染",
  EXTRACT: "提取（外部 provider）", OCR_TEXT: "读文本", OCR_SLOTS: "读解答欄号",
  OCR_CONTRACTS: "生成页面合同草稿", BACKUP: "备份",
};

/* 任务卡。刷新由调用方给：制课页刷自己那一条，运维页刷整张列表。 */
function jobCard(job, onChange = async () => {}) {
  const kind = job.status === "SUCCEEDED" ? "is-ok"
    : ["QUEUED", "RUNNING"].includes(job.status) ? "is-run" : "is-bad";
  const card = el("article", `job-card ${kind}`);
  const head = el("div", "job-card-head");
  head.append(el("strong", "", `${JOB_LABELS[job.jobType] || job.jobType} · ${job.status}`),
              el("code", "", `${job.jobType} · ${job.jobId}`));
  card.append(head);
  const progress = job.progress || {};
  const summary = [];
  // 任务跑完之后 stage 就等于 status，而 status 已经写在标题里了 ——
  // 再显示一遍只是把同一个词说两次。
  if (progress.stage && progress.stage !== job.status) summary.push(progress.stage);
  if (progress.pagesTotal) {
    summary.push(`${progress.pagesCompleted || 0}/${progress.pagesTotal} 页`
      + (progress.pagesFailed ? `（${progress.pagesFailed} 失败）` : ""));
  }
  if (progress.message) summary.push(progress.message);
  if (summary.length) card.append(el("p", "job-card-progress", summary.join(" · ")));
  const actions = el("div", "job-card-actions");
  if (["FAILED", "PARTIAL_FAILED", "CANCELLED", "INTERRUPTED"].includes(job.status)) {
    actions.append(actionButton("重试失败页", async () => {
      await api(`/api/v1/admin/jobs/${job.jobId}/retry`, {
        method: "POST", body: JSON.stringify({ failedOnly: true }),
      });
      await onChange();
    }));
  }
  if (["QUEUED", "RUNNING"].includes(job.status)) {
    actions.append(actionButton("取消任务", async () => {
      await api(`/api/v1/admin/jobs/${job.jobId}/cancel`, { method: "POST", body: "{}" });
      await onChange();
    }));
  }
  if (actions.children.length) card.append(actions);
  return card;
}

document.addEventListener("DOMContentLoaded", renderModuleNav);
