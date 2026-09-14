"use strict";

/**
 * Panel 3 · 已装课程 — what is in the course library, and the way into the editor.
 *
 * Provides two-tier categorized browsing (精听课程: 音频/视频; PDF课程: JLPT真题/课本),
 * level filtering for PDF courses, real-time search, and collapsible course groups.
 */
const StudioCourses = (() => {
  const { el, api, text, describeError } = StudioCore;

  const GROUPS = [
    {
      id: "group-intensive-audio",
      tbodyId: "audio-table-body",
      countId: "count-group-audio",
      category: "intensive",
      subcategory: "audio",
      title: "音频精听",
      emptyText: "暂无音频精听课程。",
    },
    {
      id: "group-intensive-video",
      tbodyId: "video-table-body",
      countId: "count-group-video",
      category: "intensive",
      subcategory: "video",
      title: "视频精听",
      emptyText: "暂无视频精听课程。",
    },
    {
      id: "group-pdf-jlpt",
      tbodyId: "jlpt-table-body",
      countId: "count-group-jlpt",
      category: "pdf",
      subcategory: "jlpt",
      title: "JLPT真题",
      emptyText: "暂无 PDF 真题课程（JLPT 听力精听位于上方「音频精听」中）。可通过「教材入库」导入真题 PDF。",
    },
    {
      id: "group-pdf-textbook",
      tbodyId: "textbook-table-body",
      countId: "count-group-textbook",
      category: "pdf",
      subcategory: "textbook",
      title: "课本和课本PDF",
      emptyText: "暂无课本课程。可通过「教材入库」导入 PDF 课本。",
    },
  ];

  let allCourses = [];
  let activeCategory = "all";
  let activeLevel = "all";
  let searchQuery = "";

  function courseCategory(course) {
    if (course && course.category) return course.category;
    const subcat = courseSubcategory(course);
    if (subcat === "audio" || subcat === "video") return "intensive";
    if (subcat === "jlpt" || subcat === "textbook") return "pdf";
    return "other";
  }

  function courseSubcategory(course) {
    if (course && course.subcategory) return course.subcategory;
    const name = ((course && course.name) || "").toUpperCase();
    const title = ((course && course.title) || "").toUpperCase();
    const nameLower = ((course && course.name) || "").toLowerCase();
    const titleLower = ((course && course.title) || "").toLowerCase();

    // Check if this course is explicitly a PDF document/exam (not an audio dictation course)
    const sk = (course && (course.sourceKind || "")).toLowerCase();
    const k = (course && (course.kind || "")).toLowerCase();
    const isPdfSource =
      ["pdf", "ocr", "textbook", "exam"].includes(sk) ||
      ["exam", "grammar", "word", "document", "pdf-upload"].includes(k);

    if (isPdfSource) {
      if (
        name.includes("-N1") ||
        name.includes("-N2") ||
        name.includes("-N3") ||
        title.includes("JLPT") ||
        title.includes("真题")
      ) {
        return "jlpt";
      }
      return "textbook";
    }

    // Video intensive listening
    if (
      (course && course.mediaKind === "remote") ||
      ["nhk", "tbs", "ann", "news", "youtube", "video"].some((t) => nameLower.includes(t))
    ) {
      return "video";
    }

    // Audio intensive listening (including JLPT 听力精听 and other audio)
    return "audio";
  }

  function courseLevel(course) {
    if (course && course.level) return course.level;
    const name = ((course && course.name) || "").toUpperCase();
    const title = ((course && course.title) || "").toUpperCase();
    for (const lvl of ["N1", "N2", "N3", "N4", "N5"]) {
      if (name.includes(`-${lvl}`) || name.includes(`_${lvl}`) || title.includes(lvl)) return lvl;
    }
    return "";
  }

  function courseBadgeInfo(course) {
    const subcat = courseSubcategory(course);
    const lvl = courseLevel(course);
    if (subcat === "audio") {
      return {
        className: "badge-cat intensive-audio",
        label: lvl ? `JLPT ${lvl} 听力` : "音频精听",
      };
    }
    if (subcat === "video") {
      return {
        className: "badge-cat intensive-video",
        label: "视频精听",
      };
    }
    if (subcat === "jlpt") {
      return {
        className: "badge-cat pdf-jlpt",
        label: lvl ? `JLPT ${lvl} (PDF)` : "JLPT真题 (PDF)",
      };
    }
    if (subcat === "textbook") {
      return {
        className: "badge-cat pdf-textbook",
        label: lvl ? `课本 ${lvl}` : "课本PDF",
      };
    }
    return {
      className: "badge-cat other",
      label: "其他",
    };
  }

  function updateCategoryCounts() {
    const counts = {
      all: allCourses.length,
      intensive: 0,
      pdf: 0,
      levelAll: allCourses.length,
      levelN1: 0,
      levelN2: 0,
      levelN3: 0,
    };

    for (const course of allCourses) {
      const cat = courseCategory(course);
      const lvl = courseLevel(course);

      if (cat === "intensive") counts.intensive++;
      if (cat === "pdf") counts.pdf++;

      if (lvl === "N1") counts.levelN1++;
      if (lvl === "N2") counts.levelN2++;
      if (lvl === "N3") counts.levelN3++;
    }

    const updateBadge = (id, count) => {
      const elem = el(id);
      if (elem) elem.textContent = String(count);
    };

    updateBadge("count-all", counts.all);
    updateBadge("count-intensive", counts.intensive);
    updateBadge("count-pdf", counts.pdf);
    updateBadge("count-level-all", counts.levelAll);
    updateBadge("count-level-n1", counts.levelN1);
    updateBadge("count-level-n2", counts.levelN2);
    updateBadge("count-level-n3", counts.levelN3);
  }

  function buildCourseRow(course) {
    const row = document.createElement("tr");

    // 分类
    const catTd = document.createElement("td");
    const badgeInfo = courseBadgeInfo(course);
    const catBadge = document.createElement("span");
    catBadge.className = badgeInfo.className;
    catBadge.textContent = badgeInfo.label;
    catTd.append(catBadge);
    row.append(catTd);

    // 文件夹
    row.append(text("td", "", course.name));

    // 标题
    row.append(text("td", "", course.title || ""));

    // 句数
    row.append(text("td", "", String(course.sentences)));

    // 状态
    const status = document.createElement("td");
    status.append(text("span", `badge ${course.status}`, course.status));
    if (course.errors) status.append(document.createTextNode(` ${course.errors} 错误`));
    if (course.warnings) status.append(document.createTextNode(` ${course.warnings} 警告`));
    row.append(status);

    // 操作
    const actions = document.createElement("td");
    if (course.kind === "exam") {
      const study = text("button", "course-action", "做题练习");
      study.type = "button";
      study.addEventListener("click", () => {
        window.location.href = `/exam.html?slug=${encodeURIComponent(course.name)}`;
      });
      actions.append(study);
    } else if (course.kind === "lexicon") {
      const study = text("button", "course-action", "词汇练习");
      study.type = "button";
      study.addEventListener("click", () => {
        window.location.href = `/lexicon.html?slug=${encodeURIComponent(course.name)}`;
      });
      actions.append(study);
    } else {
      const edit = text("button", "course-action", "查看 / 编辑");
      edit.type = "button";
      edit.addEventListener("click", () => {
        window.location.href = `/editor.html?course=${encodeURIComponent(course.name)}`;
      });
      actions.append(edit);
    }
    row.append(actions);

    return row;
  }

  function render(courses) {
    if (courses !== undefined) {
      allCourses = courses || [];
      updateCategoryCounts();
    }

    let totalVisible = 0;
    const isSearching = Boolean(searchQuery);

    for (const group of GROUPS) {
      const groupElem = el(group.id);
      const tbody = el(group.tbodyId);
      const countElem = el(group.countId);
      if (!groupElem || !tbody) continue;

      const categoryMatches = activeCategory === "all" || group.category === activeCategory;

      const matchingCourses = allCourses.filter((course) => {
        const cat = courseCategory(course);
        const subcat = courseSubcategory(course);
        if (cat !== group.category || subcat !== group.subcategory) return false;

        if (activeLevel !== "all") {
          const lvl = courseLevel(course);
          if (lvl !== activeLevel) return false;
        }

        if (isSearching) {
          const target = `${course.name || ""} ${course.title || ""}`.toLowerCase();
          if (!target.includes(searchQuery)) return false;
        }
        return true;
      });

      if (countElem) {
        if (group.subcategory === "audio" && activeLevel === "all" && !isSearching) {
          const n1Count = matchingCourses.filter((c) => courseLevel(c) === "N1").length;
          const n2Count = matchingCourses.filter((c) => courseLevel(c) === "N2").length;
          countElem.textContent = `${matchingCourses.length} 门课程 (JLPT 听力: N1 ${n1Count} · N2 ${n2Count})`;
        } else {
          countElem.textContent = `${matchingCourses.length} 门课程`;
        }
      }

      if (matchingCourses.length > 0) {
        const rows = matchingCourses.map(buildCourseRow);
        tbody.replaceChildren(...rows);
      } else {
        const emptyTr = document.createElement("tr");
        emptyTr.className = "empty-row";
        const emptyTd = document.createElement("td");
        emptyTd.colSpan = 6;
        emptyTd.className = "course-group-empty";
        emptyTd.textContent = isSearching || activeLevel !== "all"
          ? "本分类下没有匹配筛选条件的课程。"
          : group.emptyText;
        emptyTr.append(emptyTd);
        tbody.replaceChildren(emptyTr);
      }

      if (!categoryMatches) {
        groupElem.hidden = true;
      } else if (isSearching || activeLevel !== "all") {
        if (matchingCourses.length > 0) {
          groupElem.hidden = false;
          groupElem.open = true;
          totalVisible += matchingCourses.length;
        } else {
          groupElem.hidden = true;
        }
      } else {
        groupElem.hidden = false;
        totalVisible += matchingCourses.length;
      }
    }

    const noneMatched = el("courses-none-matched");
    if (noneMatched) {
      noneMatched.hidden = totalVisible > 0;
    }

    const summary = el("courses-summary");
    if (summary) {
      const total = allCourses.length;
      summary.textContent = isSearching || activeCategory !== "all" || activeLevel !== "all"
        ? `显示 ${totalVisible} / ${total} 门课程。点击分类卡片展开查看课程列表。`
        : `共 ${total} 门已装课程。点击分类卡片展开查看课程列表。`;
    }
  }

  async function refresh() {
    try {
      const payload = await api("/api/courses");
      render(payload.courses || []);
    } catch (error) {
      const summary = el("courses-summary");
      if (summary) summary.textContent = describeError(error);
    }
  }

  function wire() {
    const refreshBtn = el("refresh-courses");
    if (refreshBtn) refreshBtn.addEventListener("click", refresh);

    const expandAllBtn = el("expand-all-groups");
    if (expandAllBtn) {
      expandAllBtn.addEventListener("click", () => {
        for (const g of GROUPS) {
          const groupElem = el(g.id);
          if (groupElem && !groupElem.hidden) groupElem.open = true;
        }
      });
    }

    const collapseAllBtn = el("collapse-all-groups");
    if (collapseAllBtn) {
      collapseAllBtn.addEventListener("click", () => {
        for (const g of GROUPS) {
          const groupElem = el(g.id);
          if (groupElem) groupElem.open = false;
        }
      });
    }

    // Category tabs
    const categoryTabs = el("category-tabs");
    if (categoryTabs) {
      categoryTabs.addEventListener("click", (event) => {
        const target = event.target || {};
        const btn = target.closest ? target.closest(".category-btn") : target;
        if (!btn || !btn.dataset) return;
        const cat = btn.dataset.category;
        if (!cat) return;
        activeCategory = cat;
        activeLevel = "all";

        const buttons = categoryTabs.children || [];
        for (let i = 0; i < buttons.length; i++) {
          const b = buttons[i];
          if (b && b.classList) b.classList.remove("active");
        }
        if (btn.classList) btn.classList.add("active");

        const levelFilters = el("level-filters");
        if (levelFilters) {
          const levelButtons = levelFilters.children || [];
          for (let i = 0; i < levelButtons.length; i++) {
            const b = levelButtons[i];
            if (b && b.classList && b.dataset) {
              b.classList.toggle("active", b.dataset.level === "all");
            }
          }
        }
        render();
      });
    }

    // Level filters
    const levelFilters = el("level-filters");
    if (levelFilters) {
      levelFilters.addEventListener("click", (event) => {
        const target = event.target || {};
        const btn = target.closest ? target.closest(".sub-filter-btn") : target;
        if (!btn || !btn.dataset) return;
        const lvl = btn.dataset.level;
        if (!lvl) return;
        activeLevel = lvl;

        const levelButtons = levelFilters.children || [];
        for (let i = 0; i < levelButtons.length; i++) {
          const b = levelButtons[i];
          if (b && b.classList) b.classList.remove("active");
        }
        if (btn.classList) btn.classList.add("active");
        render();
      });
    }

    // Real-time search
    const searchInput = el("course-search");
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        searchQuery = searchInput.value.trim().toLowerCase();
        render();
      });
    }
  }

  return { render, refresh, wire, courseCategory, courseSubcategory, courseLevel };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioCourses;
if (typeof window !== "undefined") window.StudioCourses = StudioCourses;

