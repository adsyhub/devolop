import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const ProgressModel = require("../src/web/progress_model.js");

test("revealing an answer never grants mastery", () => {
  const result = ProgressModel.applyAttempt({}, {
    correct: true, revealed: true, score: 100, now: "2026-09-01T00:00:00Z",
  });
  assert.equal(result.mastered, false);
  assert.equal(result.attempts, 1);
});

test("listen-only exposure does not count as an attempt", () => {
  const result = ProgressModel.recordExposure({}, new Date("2026-09-01T00:00:00Z"));
  assert.equal(result.mastered, false);
  assert.equal(result.attempts, 0);
  assert.equal(result.exposures, 1);
});

test("an independent correct answer schedules sentence review", () => {
  const first = ProgressModel.applyAttempt({}, {
    correct: true, score: 100, now: "2026-09-01T00:00:00Z",
  });
  assert.equal(first.mastered, true);
  assert.equal(first.reviewStage, 1);
  assert.equal(first.nextReviewAt, "2026-09-02T00:00:00.000Z");
  assert.equal(ProgressModel.isDue(first, Date.parse("2026-09-02T00:00:00Z")), true);
});

test("API conversion keeps mastered and score fields", () => {
  const api = ProgressModel.toApi({
    correct: true, attempts: 3, bestScore: 96, updatedAt: "2026-09-01T00:00:00Z",
  });
  assert.equal(api.mastered, true);
  assert.equal(api.bestScore, 96);
  assert.equal(api.lastScore, 96);
});

test("merge uses newest mastery state and preserves counters", () => {
  const merged = ProgressModel.merge(
    { correct: true, attempts: 2, bestScore: 100, updatedAt: "2026-09-01T00:00:00Z" },
    { mastered: false, attempts: 3, lastScore: 40, updatedAt: "2026-09-02T00:00:00Z" },
  );
  assert.equal(merged.mastered, false);
  assert.equal(merged.attempts, 3);
  assert.equal(merged.bestScore, 100);
  assert.equal(merged.lastScore, 40);
});
