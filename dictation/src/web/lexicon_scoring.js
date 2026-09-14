/* Pure offline mirror of lexicon_exercise.score. No timers or network access. */
(function(root) {
  "use strict";
  function normalize(value, reading = false) {
    let s = String(value ?? "").normalize("NFKC").trim().toLowerCase().replace(/[〜～~]/g, "");
    if (reading) s = s.replace(/[ァ-ヶ]/g, c => String.fromCharCode(c.charCodeAt(0) - 0x60));
    return s.replace(/\s+/g, " ");
  }
  const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  function score(q, answer, { hinted = false, guessed = false, skipped = false } = {}) {
    const mode = q.mode || "input"; let correct = null, grade = null, parts = [], classification;
    if (skipped) classification = "skipped";
    else if (mode === "self") {
      grade = typeof answer === "object" ? answer?.grade : answer;
      if (!["again", "hard", "good", "easy"].includes(grade)) throw new Error("请选择有效的自评等级。");
      classification = "self_assessed";
    } else {
      const allowed = q.acceptedAnswers || [];
      if (mode === "choice") {
        if (!(q.choices || []).some(c => c.id === answer)) throw new Error("所选答案不存在。");
        correct = allowed.includes(answer);
      } else if (mode === "order") {
        const ids = (q.tokens || []).map(t => t.id).sort();
        if (!Array.isArray(answer) || !equal([...answer].sort(), ids)) throw new Error("请排列全部片段。");
        correct = allowed.some(a => equal(a, answer));
      } else if (Number(q.blankCount || 1) > 1) {
        const actual = (Array.isArray(answer) ? answer : String(answer).split("/")).map(v => normalize(v, q.normalizeReading));
        const accepted = allowed.map(a => a.map(v => normalize(v, q.normalizeReading)));
        correct = accepted.some(a => equal(a, actual));
        parts = Array.from({length: q.blankCount}, (_, i) => accepted.some(a => a[i] !== undefined && actual[i] !== undefined && a[i] === actual[i]));
      } else {
        if (typeof answer !== "string" || answer.length > 4000) throw new Error("答案必须是 4000 字以内的文本。");
        correct = allowed.some(a => normalize(a, q.normalizeReading) === normalize(answer, q.normalizeReading));
      }
      classification = correct ? (hinted || guessed ? "assisted" : "correct") : "wrong";
    }
    const effectiveGrade = mode === "self" ? (hinted || guessed ? "again" : grade) : classification === "correct" ? "good" : "again";
    return { correct, classification, hinted: Boolean(hinted), guessed: Boolean(guessed), skipped: Boolean(skipped), selfGrade: grade,
      suggestedGrade: skipped ? null : effectiveGrade,
      needsRetry: !skipped && (["wrong", "assisted"].includes(classification) || mode === "self" && ["again", "hard"].includes(effectiveGrade)), parts,
      referenceAnswer: q.referenceAnswer || q.acceptedAnswers || [], explanation: q.explanation || "", choices: q.choices || [], headword: q.headword || "", examples: q.examples || [] };
  }
  root.LexiconScoring = { normalize, score };
  if (typeof module !== "undefined") module.exports = root.LexiconScoring;
})(typeof globalThis !== "undefined" ? globalThis : this);
