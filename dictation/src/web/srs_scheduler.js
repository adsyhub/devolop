"use strict";

/* Pure browser-side mirror of local_backend.calculate_sm2. The server remains
 * authoritative; this copy exists so an offline grade immediately produces the
 * same next-review prediction that will later be accepted from the outbox. */
const SrsScheduler = (() => {
  const GRADES = new Set(["again", "hard", "good", "easy"]);

  function schedule(card, grade, reviewedAt = new Date().toISOString()) {
    if (!GRADES.has(grade)) throw new Error("未知复习评分");
    const base = new Date(reviewedAt);
    if (Number.isNaN(base.getTime())) throw new Error("复习时间无效");
    let repetitions = Number(card.srsRepetitions || 0);
    let interval = Number(card.srsInterval || 0);
    let ease = Number(card.srsEase || 2.5);
    let stage;
    let lapses = Number(card.srsLapses || 0);

    if (grade === "again") {
      repetitions = 0; interval = 1; ease = Math.max(1.3, ease - 0.2); stage = 1; lapses += 1;
    } else if (grade === "hard") {
      repetitions += 1; interval = interval > 0 ? Math.max(1, Math.round(interval * 1.2)) : 1;
      ease = Math.max(1.3, ease - 0.15); stage = repetitions >= 3 ? 3 : 2;
    } else if (grade === "good") {
      interval = repetitions === 0 ? 1 : repetitions === 1 ? 3 : Math.max(1, Math.round(interval * ease));
      repetitions += 1; stage = repetitions >= 3 ? 3 : 2;
    } else {
      interval = repetitions === 0 ? 3 : repetitions === 1 ? 6 : Math.max(1, Math.round(interval * ease * 1.3));
      repetitions += 1; ease = Math.min(3.5, ease + 0.15); stage = 3;
    }
    const next = new Date(base.getTime() + interval * 86400000).toISOString();
    return {
      ...card, srsRepetitions: repetitions, srsInterval: interval,
      srsEase: Math.round(ease * 100) / 100, srsStage: stage,
      srsLapses: lapses, nextReviewAt: next, lastReviewedAt: base.toISOString(),
      mastered: stage >= 3, updatedAt: base.toISOString(),
    };
  }

  return { grades: [...GRADES], schedule };
})();

