import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(
  path.join(HERE, "..", "src", "web", "personal_data_tools.js"),
  "utf8",
);
const context = vm.createContext({ console });
vm.runInContext(`${source}\n;globalThis.__tools = PersonalDataTools;`, context);
const tools = context.__tools;

test("quoted CSV keeps commas and escaped quotes inside fields", () => {
  const parsed = tools.parseVocabImport(
    '言葉,ことば,"word, expression","He said ""hello""",N2 高频\n',
  );
  assert.equal(parsed.errors, 0);
  assert.equal(parsed.items.length, 1);
  assert.equal(parsed.items[0].meaning, "word, expression");
  assert.equal(parsed.items[0].note, 'He said "hello"');
  assert.deepEqual(JSON.parse(JSON.stringify(parsed.items[0].tags)), ["N2", "高频"]);
  assert.equal(parsed.items[0].level, "N2");
});

test("Anki-style TSV headers are ignored and tags are split", () => {
  const parsed = tools.parseVocabImport(
    "#separator:tab\n勉強\tべんきょう\t学习\t例句\tN3 verb\n",
  );
  assert.equal(parsed.items.length, 1);
  assert.equal(parsed.items[0].term, "勉強");
  assert.deepEqual(JSON.parse(JSON.stringify(parsed.items[0].tags)), ["N3", "verb"]);
});

test("dedupe uses term and reading and keeps the newest copy", () => {
  const result = tools.dedupeVocabEntries([
    { id: "old", term: "言葉", reading: "ことば", meaning: "old", updatedAt: "2026-01-01" },
    { id: "new", term: " 言葉 ", reading: "ことば", meaning: "new", updatedAt: "2026-02-01" },
    { id: "other", term: "言葉", reading: "げんよう", meaning: "different reading", updatedAt: "2026-01-01" },
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(result.map((item) => item.id))), ["new", "other"]);
});
