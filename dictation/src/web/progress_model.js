"use strict";

/* Canonical sentence-progress model shared by the player and its tests.
 *
 * Browser history used {correct, bestScore}; the SQLite API used
 * {mastered, lastScore}. Explicit conversion here prevents a batch sync from
 * treating missing fields as false/zero and gives sentence review one owner.
 */
const ProgressModel = (() => {
  const DAY_MS = 24 * 60 * 60 * 1000;

  function finite(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function iso(value, fallback = "") {
    if (!value) return fallback;
    const timestamp = Date.parse(String(value));
    return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : fallback;
  }

  function normalize(entry = {}) {
    const attempts = Math.max(0, Math.trunc(finite(entry.attempts)));
    const mastered = Object.prototype.hasOwnProperty.call(entry, "mastered")
      ? Boolean(entry.mastered)
      : Boolean(entry.correct);
    const rawLastScore = Object.prototype.hasOwnProperty.call(entry, "lastScore")
      ? entry.lastScore
      : entry.bestScore;
    const lastScore = Math.max(0, Math.min(100, finite(rawLastScore)));
    const bestScore = Math.max(lastScore, Math.max(0, Math.min(100, finite(entry.bestScore))));
    return {
      completed: Object.prototype.hasOwnProperty.call(entry, "completed")
        ? Boolean(entry.completed)
        : attempts > 0,
      mastered,
      correct: mastered,
      attempts,
      bestScore,
      lastScore,
      revealed: Boolean(entry.revealed),
      exposures: Math.max(0, Math.trunc(finite(entry.exposures))),
      reviewStage: Math.max(0, Math.trunc(finite(entry.reviewStage))),
      reviewInterval: Math.max(0, Math.trunc(finite(entry.reviewInterval))),
      nextReviewAt: iso(entry.nextReviewAt),
      updatedAt: iso(entry.updatedAt),
    };
  }

  function nextSchedule(previous, now) {
    const reviewStage = previous.reviewStage + 1;
    let reviewInterval = 1;
    if (reviewStage === 2) reviewInterval = 3;
    else if (reviewStage > 2) {
      reviewInterval = Math.max(4, Math.round((previous.reviewInterval || 3) * 2.5));
    }
    return {
      reviewStage,
      reviewInterval,
      nextReviewAt: new Date(now.getTime() + reviewInterval * DAY_MS).toISOString(),
    };
  }

  function applyAttempt(entry, result = {}) {
    const previous = normalize(entry);
    const now = result.now instanceof Date ? result.now : new Date(result.now || Date.now());
    const revealed = Boolean(result.revealed);
    const correct = Boolean(result.correct) && !revealed;
    const score = Math.max(0, Math.min(100, finite(result.score)));
    const schedule = correct
      ? nextSchedule(previous, now)
      : revealed
        ? {
            reviewStage: previous.reviewStage,
            reviewInterval: previous.reviewInterval,
            nextReviewAt: previous.nextReviewAt,
          }
        : { reviewStage: 0, reviewInterval: 1, nextReviewAt: now.toISOString() };
    // Seeing an answer cannot grant mastery. It also should not erase mastery
    // earned earlier; only a later independent wrong answer does that.
    const mastered = revealed ? previous.mastered : correct;
    return normalize({
      ...previous,
      ...schedule,
      completed: true,
      mastered,
      attempts: previous.attempts + 1,
      bestScore: Math.max(previous.bestScore, score),
      lastScore: score,
      revealed: previous.revealed || revealed,
      updatedAt: now.toISOString(),
    });
  }

  function recordExposure(entry, nowValue = Date.now()) {
    const previous = normalize(entry);
    const now = nowValue instanceof Date ? nowValue : new Date(nowValue);
    return normalize({
      ...previous,
      revealed: true,
      exposures: previous.exposures + 1,
      updatedAt: now.toISOString(),
    });
  }

  function toApi(entry) {
    const value = normalize(entry);
    return {
      completed: value.completed,
      mastered: value.mastered,
      attempts: value.attempts,
      bestScore: value.bestScore,
      lastScore: value.lastScore,
      revealed: value.revealed,
      exposures: value.exposures,
      reviewStage: value.reviewStage,
      reviewInterval: value.reviewInterval,
      nextReviewAt: value.nextReviewAt,
      updatedAt: value.updatedAt,
    };
  }

  function merge(localEntry, remoteEntry) {
    if (!localEntry) return normalize(remoteEntry);
    if (!remoteEntry) return normalize(localEntry);
    const local = normalize(localEntry);
    const remote = normalize(remoteEntry);
    const localTime = Date.parse(local.updatedAt || "") || 0;
    const remoteTime = Date.parse(remote.updatedAt || "") || 0;
    const newest = remoteTime > localTime ? remote : local;
    return normalize({
      ...newest,
      attempts: Math.max(local.attempts, remote.attempts),
      bestScore: Math.max(local.bestScore, remote.bestScore),
      exposures: Math.max(local.exposures, remote.exposures),
      revealed: local.revealed || remote.revealed,
    });
  }

  function isDue(entry, nowValue = Date.now()) {
    const value = normalize(entry);
    if (value.attempts <= 0) return false;
    if (!value.mastered) return true;
    if (!value.nextReviewAt) return false;
    const now = nowValue instanceof Date ? nowValue.getTime() : Number(nowValue);
    return Date.parse(value.nextReviewAt) <= now;
  }

  function normalizeMap(map) {
    const result = {};
    if (!map || typeof map !== "object" || Array.isArray(map)) return result;
    Object.entries(map).forEach(([key, entry]) => {
      if (entry && typeof entry === "object") result[key] = normalize(entry);
    });
    return result;
  }

  function toApiMap(map) {
    const result = {};
    Object.entries(normalizeMap(map)).forEach(([key, entry]) => { result[key] = toApi(entry); });
    return result;
  }

  return { normalize, normalizeMap, applyAttempt, recordExposure, toApi, toApiMap, merge, isDue };
})();

if (typeof module !== "undefined" && module.exports) module.exports = ProgressModel;
if (typeof window !== "undefined") window.ProgressModel = ProgressModel;
