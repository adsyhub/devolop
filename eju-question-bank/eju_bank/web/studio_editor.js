"use strict";
/* ==========================================================================
   复核编辑器
   --------------------------------------------------------------------------
   逐页对照原图核对，然后签署。这是整条流水线上唯一由人下判断的地方：
   机器可以把字读出来，"这一页确实是这样"只能由人说。

   机器校验过的页在这里照样能改。人的签名会顶替机器证明，整卷的把关等级
   随之从 MACHINE_ATTESTED 升上去 —— 学习者看到的那个标记就是这么来的。
   ========================================================================== */

const main = $("#studio-main");

// ── L3：复核工作台 ────────────────────────────────────────────────────────
const reviewState = { page: null, contract: null, selectedBlock: 0, dirty: false };

async function loadReviewSources() {
  const select = $("#review-source");
  const old = select.value;
  select.replaceChildren();
  for (const source of state.sources) {
    const option = el("option", "", `${source.session} · ${source.subject} · ${source.language}`);
    option.value = source.sourceId;
    select.append(option);
  }
  if (state.sources.some((s) => s.sourceId === old)) select.value = old;
}

function reviewPath() {
  if (!reviewState.page) throw new Error("请先打开来源页");
  const p = reviewState.page;
  return `/api/v1/admin/sources/${p.sourceId}/pages/${p.role}/${p.page}`;
}

async function openReviewPage() {
  if (reviewState.dirty && !confirm("当前草稿尚未保存，确认切换页面吗？")) return;
  const sid = $("#review-source").value;
  const role = $("#review-role").value;
  const page = Number($("#review-page").value);
  if (!sid) throw new Error("当前工作目录尚无来源清单");
  reviewState.page = await api(`/api/v1/admin/sources/${sid}/pages/${role}/${page}`);
  reviewState.contract = structuredClone(reviewState.page.contract);
  reviewState.dirty = false;
  reviewState.selectedBlock = 0;
  $("#review-workbench").hidden = false;
  $("#review-source-image").src = reviewPath() + "/image";
  $("#review-page").max = reviewState.page.pageCount;
  $("#review-page-status").textContent = `第 ${page} / ${reviewState.page.pageCount} 页`;
  $("#review-confirmed").checked = false;
  state.sourceId = sid;
  rememberLocation(sid, role, page);
  renderReviewEditor();
}

function markReviewDirty() {
  reviewState.dirty = true;
  noteReviewChanged();
  $("#review-sign").disabled = true;
  $("#review-json").value = JSON.stringify(reviewState.contract, null, 2);
  renderReviewPreview();
}

function renderReviewPreview() {
  const preview = $("#review-preview-content");
  preview.replaceChildren();
  for (const block of reviewState.contract.blocks || []) {
    preview.append(el("h4", "", `${block.printedLabel || block.localKey || block.kind}`));
    if (block.stemAst || block.contentAst) {
      preview.append(renderAst(block.stemAst || block.contentAst, "/api/v1/admin/media/"));
    }
    for (const option of block.options || []) {
      const row = el("div", "", `${option.key}. `);
      row.append(renderAst(option.contentAst, "/api/v1/admin/media/"));
      preview.append(row);
    }
    if (block.kind === "answer-entry") {
      preview.append(el("p", "", `答案：${block.correctOption || JSON.stringify(block.tokens)}`));
    }
  }
  const original = reviewState.page.previousContract || reviewState.page.contract;
  const changed = [...new Set([...Object.keys(original), ...Object.keys(reviewState.contract)])]
    .filter((key) => JSON.stringify(original[key]) !== JSON.stringify(reviewState.contract[key]));
  $("#review-diff").textContent = changed.length
    ? changed.map((key) =>
        `${key}\n- ${JSON.stringify(original[key])}\n+ ${JSON.stringify(reviewState.contract[key])}`).join("\n\n")
    : "内容无差异";
}

function astEditor(nodes, parent) {
  for (const node of nodes || []) {
    const key = node.type === "inlineMath" || node.type === "displayMath" ? "latex"
      : node.type === "figure" ? "alt" : "value";
    if (["text", "paragraph", "inlineMath", "displayMath", "callout", "underline", "figure"].includes(node.type)) {
      const label = el("label", "", `${node.type} `);
      const input = el("textarea", "review-field");
      input.value = node[key] || "";
      input.addEventListener("input", () => { node[key] = input.value; markReviewDirty(); });
      label.append(input);
      parent.append(label);
    } else {
      parent.append(el("p", "subtitle", `${node.type} 节点可在「进阶」的完整 JSON 中编辑`));
    }
    if (node.children) astEditor(node.children, parent);
  }
}

function renderReviewEditor() {
  const fields = $("#review-fields"), layer = $("#review-bbox-layer");
  renderGeometryNotice();
  fields.replaceChildren();
  layer.replaceChildren();
  const page = reviewState.page;
  $("#review-signature").textContent = page.signedBy
    ? `已签署：${page.signedBy} · ${page.signedAt}；编辑后须重新签署`
    : "尚未签署";
  $("#review-json").value = JSON.stringify(reviewState.contract, null, 2);
  $("#review-sign").disabled =
    reviewState.dirty || !page.revisionId || page.revisionId.startsWith("file:") || !!page.signedBy;
  $("#review-withdraw").disabled = !page.signedBy;

  fields.append(blockToolbar());

  for (const [index, block] of (reviewState.contract.blocks || []).entries()) {
    const details = el("details", "review-block");
    details.open = index === reviewState.selectedBlock;
    const summary = el("summary", "",
      `${index + 1} · ${block.kind} · ${block.printedLabel || block.localKey || ""}`);
    summary.addEventListener("click", () => {
      reviewState.selectedBlock = index;
      $("#review-crop-bbox").value = (block.bbox || []).join(",");
    });
    details.append(summary);

    for (const key of ["localKey", "formCode", "sectionCode", "groupCode", "printedLabel", "answerRef", "correctOption"]) {
      if (!(key in block)) continue;
      const label = el("label", "", `${key} `);
      const input = el("input");
      input.value = block[key];
      input.addEventListener("input", () => { block[key] = input.value; markReviewDirty(); });
      label.append(input);
      details.append(label);
    }
    astEditor(block.stemAst || block.contentAst, details);
    for (const option of block.options || []) {
      details.append(el("h5", "", `选项 ${option.key}`));
      astEditor(option.contentAst, details);
    }

    const field = (label, value, change) => {
      const line = el("label", "", label);
      const input = el("input");
      input.value = value;
      input.addEventListener("change", () => {
        try { change(input.value); markReviewDirty(); } catch (e) { showError(e); }
      });
      line.append(input);
      details.append(line);
    };
    field("来源区域 ID（逗号分隔）",
      (block.regionIds || (block.regionId ? [block.regionId] : [])).join(","),
      (text) => {
        block.regionIds = text.split(",").map((x) => x.trim()).filter(Boolean);
        delete block.regionId;
      });
    field("区域 x0,y0,x1,y1", (block.bbox || []).join(","), (text) => {
      const bbox = text.split(",").map(Number);
      if (bbox.length !== 4 || bbox.some((x) => !Number.isFinite(x) || x < 0 || x > 1) ||
          bbox[0] >= bbox[2] || bbox[1] >= bbox[3]) throw new Error("请输入有效归一化区域");
      block.bbox = bbox;
    });
    if (block.answerSpec) {
      field("答案类型", block.answerSpec.type, (text) => {
        if (!["SINGLE_CHOICE", "DIGIT_GRID", "ESSAY"].includes(text)) throw new Error("无效答案类型");
        block.answerSpec.type = text;
      });
      field("数字格（逗号分隔）", (block.answerSpec.slots || []).join(","), (text) => {
        block.answerSpec.slots = text.split(",").map((x) => x.trim()).filter(Boolean);
      });
    }
    for (const option of block.options || []) {
      field("选项编号", option.key, (text) => { option.key = text; });
    }

    const up = el("button", "btn btn-outline", "上移");
    up.type = "button";
    up.disabled = index === 0;
    up.addEventListener("click", () => {
      const blocks = reviewState.contract.blocks;
      [blocks[index - 1], blocks[index]] = [blocks[index], blocks[index - 1]];
      blocks.forEach((b, i) => { b.readingOrder = i + 1; });
      markReviewDirty();
      renderReviewEditor();
    });
    const remove = el("button", "btn btn-outline danger-text", "删除此块");
    remove.type = "button";
    remove.addEventListener("click", () => {
      if (!confirm("删除后需要重新核对区域处置，确认删除？")) return;
      reviewState.contract.blocks.splice(index, 1);
      markReviewDirty();
      renderReviewEditor();
    });
    details.append(up, remove);
    fields.append(details);

    if (Array.isArray(block.bbox) && block.bbox.length === 4) {
      const [x0, y0, x1, y1] = block.bbox;
      const rect = el("button", "bbox-region", String(index + 1));
      rect.type = "button";
      /* 这个框未必是识别出来的。OCR 读的是字符不是坐标，绝大多数区域的 bbox 是
         整页正文占位（coverage.regionEvidence === 'TEXT_ORDER_ONLY'），区域身份
         来自文字顺序。照常画一个实线框，等于告诉复核者"系统精确定位到了这里"，
         而它没有——那会让人照着框去核对，核对的却是假的位置。 */
      if (regionGeometryUnverified()) {
        rect.classList.add("bbox-unverified");
        rect.title = "定位未验证：这个框是整页正文占位，区域身份来自文字顺序，"
          + "不是识别出来的坐标。";
      }
      rect.style.left = `${x0 * 100}%`;
      rect.style.top = `${y0 * 100}%`;
      rect.style.width = `${(x1 - x0) * 100}%`;
      rect.style.height = `${(y1 - y0) * 100}%`;
      rect.setAttribute("aria-label",
        `查看内容块 ${index + 1}` + (regionGeometryUnverified() ? "（定位未验证）" : ""));
      enableRegionDrag(rect, block, index);
      rect.addEventListener("click", () => {
        reviewState.selectedBlock = index;
        $("#review-crop-bbox").value = block.bbox.join(",");
        renderReviewEditor();
      });
      layer.append(rect);
    }
  }
  renderReviewPreview();
}

/* 这一页的区域几何有没有被真正验证过。合同自己会说：regionEvidence 记的是
   区域身份从哪来的，TEXT_ORDER_ONLY 意思是"按文字顺序排的占位"，不是坐标。 */
function regionGeometryUnverified() {
  const coverage = reviewState.contract?.coverage || {};
  return coverage.regionEvidence === "TEXT_ORDER_ONLY";
}

/* 把这条限制写在页面上，而不是留给复核者从框的样子去猜。 */
function renderGeometryNotice() {
  const notice = $("#review-geometry-notice");
  if (!notice) return;
  const unverified = regionGeometryUnverified();
  notice.hidden = !unverified;
  notice.textContent = unverified
    ? "定位未验证：本页区域按文字顺序排列，框是整页正文占位，不代表识别出的坐标。"
      + "请对照原图核对内容，不要依赖框的位置。"
    : "";
}

/* 新增内容块与整页覆盖登记：日常复核偶尔需要，放在字段列表最上面。 */
function blockToolbar() {
  const bar = el("div", "review-controls");
  const kind = el("select");
  kind.setAttribute("aria-label", "新内容块类型");
  for (const k of ["question", "material", "answer-entry", "instruction", "ignored"]) {
    kind.append(el("option", "", k));
  }
  const add = el("button", "btn btn-outline", "新增内容块");
  add.type = "button";
  add.addEventListener("click", () => {
    if (!reviewState.contract) return showError(new Error("先打开来源页"));
    const value = kind.value;
    const block = {
      kind: value, bbox: [.1, .1, .9, .3], localKey: "block-" + crypto.randomUUID().slice(0, 8),
      regionId: "", readingOrder: reviewState.contract.blocks.length + 1,
    };
    if (value === "question") {
      Object.assign(block, {
        formCode: "PHYSICS_JA", groupCode: "I", answerRef: "",
        stemAst: [{ type: "text", value: "待录入" }],
        options: ["1", "2", "3", "4"].map((key) => ({ key, contentAst: [{ type: "text", value: "待录入" }] })),
        answerSpec: { type: "SINGLE_CHOICE" },
      });
    }
    if (value === "material") block.contentAst = [{ type: "text", value: "待录入" }];
    if (value === "answer-entry") {
      Object.assign(block, { formCode: "PHYSICS_JA", answerRef: "", answerType: "SINGLE_CHOICE", correctOption: "" });
    }
    if (value === "ignored") block.reason = "";
    reviewState.contract.blocks.push(block);
    reviewState.selectedBlock = reviewState.contract.blocks.length - 1;
    markReviewDirty();
    renderReviewEditor();
  });

  const coverageLabel = el("label", "field");
  coverageLabel.append(el("span", "", "原页检测区域 ID（逗号分隔，逐一对照原图填写）"));
  const coverageInput = el("input");
  coverageInput.id = "review-region-ids";
  coverageInput.addEventListener("change", () => {
    if (!reviewState.contract) return;
    const regions = coverageInput.value.split(",").map((x) => x.trim()).filter(Boolean);
    const accounted = reviewState.contract.blocks
      .flatMap((b) => b.regionIds || (b.regionId ? [b.regionId] : []));
    reviewState.contract.coverage = {
      regionIds: regions, accountedRegionIds: accounted,
      inkRegions: regions.length, accountedRegions: accounted.length,
    };
    markReviewDirty();
  });
  coverageLabel.append(coverageInput);
  bar.append(kind, add, coverageLabel);
  return bar;
}

function enableRegionDrag(rect, block, index) {
  const resize = el("span", "bbox-resize", "↘");
  resize.title = "拖动调整区域大小";
  rect.append(resize);
  rect.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    const bounds = $("#review-bbox-layer").getBoundingClientRect();
    const original = [...block.bbox];
    const start = { x: event.clientX, y: event.clientY };
    const resizing = event.target === resize;
    let moved = false;
    rect.setPointerCapture(event.pointerId);
    const move = (e) => {
      const dx = (e.clientX - start.x) / bounds.width, dy = (e.clientY - start.y) / bounds.height;
      if (Math.abs(dx) + Math.abs(dy) < .002) return;
      moved = true;
      let [x0, y0, x1, y1] = original;
      if (resizing) {
        x1 = Math.max(x0 + .005, Math.min(1, x1 + dx));
        y1 = Math.max(y0 + .005, Math.min(1, y1 + dy));
      } else {
        const mx = Math.max(-x0, Math.min(1 - x1, dx)), my = Math.max(-y0, Math.min(1 - y1, dy));
        x0 += mx; x1 += mx; y0 += my; y1 += my;
      }
      block.bbox = [x0, y0, x1, y1].map((n) => Number(n.toFixed(5)));
      rect.style.left = `${x0 * 100}%`;
      rect.style.top = `${y0 * 100}%`;
      rect.style.width = `${(x1 - x0) * 100}%`;
      rect.style.height = `${(y1 - y0) * 100}%`;
      $("#review-crop-bbox").value = block.bbox.join(",");
    };
    const end = () => {
      rect.removeEventListener("pointermove", move);
      rect.removeEventListener("pointerup", end);
      rect.removeEventListener("pointercancel", end);
      if (moved) { reviewState.selectedBlock = index; markReviewDirty(); renderReviewEditor(); }
    };
    rect.addEventListener("pointermove", move);
    rect.addEventListener("pointerup", end);
    rect.addEventListener("pointercancel", end);
  });
}

async function saveReviewPage() {
  reviewState.page = await api(reviewPath(), {
    method: "PUT",
    body: JSON.stringify({ contract: reviewState.contract, baseRevision: reviewState.page.revisionId }),
  });
  reviewState.contract = structuredClone(reviewState.page.contract);
  reviewState.dirty = false;
  $("#review-confirmed").checked = false;
  renderReviewEditor();
  $("#review-page-status").textContent = "草稿已保存；签署前请确认已对照来源";
}

$("#review-open").addEventListener("click", act(openReviewPage));
for (const [id, delta] of [["review-prev", -1], ["review-next", 1]]) {
  $(`#${id}`).addEventListener("click", act(() => {
    $("#review-page").value = Math.max(1,
      Math.min(reviewState.page?.pageCount || 1, Number($("#review-page").value) + delta));
    return openReviewPage();
  }));
}
$("#review-save").addEventListener("click", act(saveReviewPage));
$("#review-apply-json").addEventListener("click", act(() => {
  const value = JSON.parse($("#review-json").value);
  if (!Array.isArray(value.blocks)) throw new Error("blocks 必须是数组");
  reviewState.contract = value;
  markReviewDirty();
  renderReviewEditor();
}));
$("#review-ignore").addEventListener("click", act(() => {
  const reason = $("#review-ignore-reason").value.trim();
  if (!reason) throw new Error("请填写非题目页说明");
  reviewState.contract.blocks = [{ kind: "ignored", regionIds: ["page"], bbox: [0, 0, 1, 1], reason, readingOrder: 1 }];
  reviewState.contract.coverage = {
    inkRegions: 1, accountedRegions: 1, regionIds: ["page"], accountedRegionIds: ["page"],
  };
  reviewState.contract.issues = [];
  markReviewDirty();
  renderReviewEditor();
}));
$("#review-sign").addEventListener("click", act(async () => {
  if (reviewState.dirty) throw new Error("请先保存草稿");
  reviewState.page = await api(reviewPath() + "/sign", {
    method: "POST",
    body: JSON.stringify({
      revisionId: reviewState.page.revisionId,
      reviewer: $("#review-signoff-reviewer").value,
      confirmed: $("#review-confirmed").checked,
    }),
  });
  reviewState.contract = structuredClone(reviewState.page.contract);
  renderReviewEditor();
  noteReviewChanged();
  showNotice("本页已签署。");
}));
$("#review-withdraw").addEventListener("click", act(async () => {
  const reason = prompt("撤回签署的原因（至少 3 个字符）；依赖该签署的版本将停止新交付。");
  if (reason === null) return;
  reviewState.page = await api(reviewPath() + "/withdraw", {
    method: "POST",
    body: JSON.stringify({
      revisionId: reviewState.page.revisionId,
      reviewer: $("#review-signoff-reviewer").value, reason,
    }),
  });
  reviewState.contract = structuredClone(reviewState.page.contract);
  reviewState.dirty = false;
  noteReviewChanged();
  renderReviewEditor();
}));
$("#review-clip").addEventListener("click", act(async () => {
  const block = reviewState.contract?.blocks?.[reviewState.selectedBlock];
  if (!block) throw new Error("先选择一个材料或题目内容块");
  const bbox = $("#review-crop-bbox").value.split(",").map(Number);
  const asset = await api(reviewPath() + "/clip", { method: "POST", body: JSON.stringify({ bbox }) });
  const key = block.kind === "question" ? "stemAst" : "contentAst";
  (block[key] ||= []).push({ type: "figure", assetId: asset.assetId, sourceBbox: bbox, alt: "" });
  markReviewDirty();
  renderReviewEditor();
}));



/* 改过页之后，课程库那边已经组装好的候选就不作数了。两个页面各自独立，
   所以这里只能记一笔状态，让人知道要回去重新组装 —— 不能假装那边没事。 */
function noteReviewChanged() {
  $("#module-status").textContent =
    "这一页有改动或新签署：回课程库的阶段 ⑥ 重新组装并预检，之前的候选卷已不作数。";
}

/* 地址栏是产品的一部分：刷新、加书签都应该回到同一页。 */
function rememberLocation(sourceId, role, page) {
  const query = new URLSearchParams({ source: sourceId, role, page: String(page) });
  history.replaceState(null, "", `${location.pathname}?${query}`);
}

async function boot() {
  await loadLibraryInstanceId();
  if (!(await ensureSources())) return;
  await loadReviewSources();
  const query = new URLSearchParams(location.search);
  const wanted = query.get("source");
  if (wanted && state.sources.some((s) => s.sourceId === wanted)) {
    $("#review-source").value = wanted;
    state.sourceId = wanted;
  }
  if (query.get("role")) $("#review-role").value = query.get("role");
  if (query.get("page")) $("#review-page").value = query.get("page");
  const back = $("#review-back");
  if (back) {
    back.href = $("#review-source").value
      ? `/studio/library#/source/${encodeURIComponent($("#review-source").value)}`
      : "/studio/library";
  }
  if (!$("#review-source").value) {
    $("#module-status").textContent = "当前工作目录还没有来源。先到制课上传 PDF，或在课程库里导入。";
    return;
  }
  // 带了具体页码就直接打开；只带来源时也打开第 1 页——人来这一页就是为了看页。
  await openReviewPage();
}

$("#review-source").addEventListener("change", () => {
  state.sourceId = $("#review-source").value;
  const back = $("#review-back");
  if (back) back.href = `/studio/library#/source/${encodeURIComponent(state.sourceId)}`;
});

boot().catch(showError);
