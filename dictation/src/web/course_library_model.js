"use strict";

/* Pure course-library rules. Keeping them outside app.js makes filtering and
 * release-state labels testable without constructing the whole player DOM. */
const CourseLibraryModel = (() => {
  function kindOf(course) {
    return course?.mediaKind === "remote" ? "video" : "audio";
  }

  function languageLabel(value) {
    if (!value) return "";
    if (typeof value === "string") return value;
    return value.displayName || value.nativeName || value.name || value.code || "";
  }

  function isCurrent(course, stableId) {
    return Boolean(stableId) && String(course?.courseId || course?.id) === String(stableId);
  }

  function qualityState(course) {
    const quality = course?.quality || {};
    return quality.status === "passed" && !quality.stale && Number(quality.errors || 0) === 0
      ? "ready"
      : "review";
  }

  function qualityLabel(course) {
    const quality = course?.quality || {};
    if (quality.stale) return "⚠ 质量报告已过期";
    if (Number(quality.errors || 0) > 0 || quality.status === "failed") {
      return `✕ 质量失败 ${Number(quality.errors || 0)}`;
    }
    if (quality.status === "passed") return "✓ 质量通过";
    if (quality.status === "needs_review") return `⚠ 待复核 ${Number(quality.warnings || 0)}`;
    return "○ 尚未质量检测";
  }

  function reviewLabel(course) {
    const review = course?.review || {};
    const accepted = new Set(["passed", "approved", "verified", "complete", "completed"]);
    const listeningReady = accepted.has(String(review.humanListening || "").toLowerCase());
    const rightsReady = accepted.has(String(review.commercialRights || "").toLowerCase());
    const browserReady = accepted.has(String(review.browserAcceptance || "").toLowerCase());
    if (listeningReady && rightsReady && browserReady) return "✓ 发布审核完成";
    if (!rightsReady) return "版权待核验";
    if (!listeningReady) return "人工审听待完成";
    return "浏览器验收待完成";
  }

  function filterAndSort(courses, options = {}) {
    const category = options.category || "all";
    const levelFilter = options.level || "all";
    const status = options.status || "all";
    const query = String(options.query || "").trim().toLowerCase();
    const currentId = options.currentId || "";
    const progressOf = typeof options.progressOf === "function"
      ? options.progressOf
      : (() => ({ completed: 0, mastered: 0, percent: 0 }));
    const filtered = (courses || []).filter((course) => {
      if (category !== "all" && kindOf(course) !== category) return false;
      const courseLevel = String(course.level || "");
      if (levelFilter !== "all") {
        if (levelFilter === "other" ? Boolean(courseLevel) : courseLevel !== levelFilter) return false;
      }
      const progress = progressOf(course, isCurrent(course, currentId));
      if (status === "ready" && qualityState(course) !== "ready") return false;
      if (status === "review" && qualityState(course) !== "review") return false;
      if (status === "started" && Number(progress.completed || 0) <= 0) return false;
      if (status === "unstarted" && Number(progress.completed || 0) > 0) return false;
      if (query) {
        const haystack = [course.title, course.id, course.courseId, languageLabel(course.language), course.level]
          .filter(Boolean).join(" ").toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      return true;
    });
    filtered.sort((left, right) => {
      if (options.sort === "recent") return Number(right.lastModified || 0) - Number(left.lastModified || 0);
      if (options.sort === "progress") {
        const leftProgress = progressOf(left, isCurrent(left, currentId)).percent;
        const rightProgress = progressOf(right, isCurrent(right, currentId)).percent;
        return rightProgress - leftProgress
          || String(left.title || left.id).localeCompare(String(right.title || right.id), "zh-CN");
      }
      return String(left.title || left.id).localeCompare(
        String(right.title || right.id), "zh-CN", { numeric: true },
      );
    });
    return filtered;
  }

  return { kindOf, languageLabel, isCurrent, qualityState, qualityLabel, reviewLabel, filterAndSort };
})();

if (typeof module !== "undefined" && module.exports) module.exports = CourseLibraryModel;
if (typeof window !== "undefined") window.CourseLibraryModel = CourseLibraryModel;
