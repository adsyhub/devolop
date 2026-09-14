import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const Scoring = require("../src/web/dictation_scoring.js");

test("forgiving Japanese scoring ignores punctuation and spaces", () => {
  const profile = { latin: false, locale: "ja-JP" };
  assert.equal(Scoring.normalizeAnswer("これは、テストです。", "forgiving", profile), "これはテストです");
  assert.equal(Scoring.normalizeAnswer("これは テストです", "forgiving", profile), "これはテストです");
});

test("accent-flexible Latin scoring removes case and accents", () => {
  const profile = { latin: true, locale: "fr-FR" };
  assert.equal(Scoring.normalizeAnswer("École !", "accent-flexible", profile), "ecole");
});

test("character comparison reports substitutions and a stable similarity", () => {
  const result = Scoring.compareCharacters("聞く", "聴く");
  assert.equal(result.distance, 1);
  assert.equal(result.operations[0].type, "replace");
  assert.equal(Scoring.similarityPercent("聞く", "聴く", result.distance), 50);
});

test("character hints count meaningful characters, not punctuation", () => {
  const hint = Scoring.buildHint("はい、そうです。", 1, false);
  assert.equal(hint.unitCount, 6);
  assert.match(hint.masked, /、/);
  assert.match(hint.masked, /□/);
});
