import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const Model = require("../src/web/course_library_model.js");

const courses = [
  { id: "folder-a", courseId: "stable-a", title: "2021 N2", level: "N2", mediaKind: "audio", quality: { status: "passed" } },
  { id: "video-b", courseId: "stable-b", title: "新闻", mediaKind: "remote", language: { displayName: "日语" }, quality: { status: "needs_review", warnings: 2 } },
];

test("stable manifest id, not directory name, identifies the current course", () => {
  assert.equal(Model.isCurrent(courses[0], "stable-a"), true);
  assert.equal(Model.isCurrent(courses[0], "folder-a"), false);
});

test("filters combine category, level, text and release status", () => {
  const result = Model.filterAndSort(courses, {
    category: "audio", level: "N2", status: "ready", query: "2021",
  });
  assert.deepEqual(result.map((item) => item.id), ["folder-a"]);
});

test("quality and review labels expose incomplete release work", () => {
  assert.equal(Model.qualityLabel(courses[0]), "✓ 质量通过");
  assert.equal(Model.qualityLabel(courses[1]), "⚠ 待复核 2");
  assert.equal(Model.reviewLabel(courses[1]), "版权待核验");
});

test("a listened-to or attempted sentence counts as started without being mastered", () => {
  const learningCourses = [{ id: "heard", title: "Heard" }, { id: "new", title: "New" }];
  const progressOf = (course) => course.id === "heard"
    ? { completed: 1, mastered: 0, percent: 0 }
    : { completed: 0, mastered: 0, percent: 0 };
  assert.deepEqual(
    Model.filterAndSort(learningCourses, { status: "started", progressOf }).map((course) => course.id),
    ["heard"],
  );
  assert.deepEqual(
    Model.filterAndSort(learningCourses, { status: "unstarted", progressOf }).map((course) => course.id),
    ["new"],
  );
});
