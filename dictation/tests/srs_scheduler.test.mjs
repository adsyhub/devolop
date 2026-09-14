import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const cases = JSON.parse(fs.readFileSync(path.join(here, "fixtures", "srs_cases.json"), "utf8"));
const source = fs.readFileSync(path.join(here, "..", "src", "web", "srs_scheduler.js"), "utf8");
const sandbox = { Date, Error, Math, Set };
vm.createContext(sandbox);
vm.runInContext(`${source}\nglobalThis.scheduler = SrsScheduler;`, sandbox);

for (const fixture of cases) {
  test(`SRS vector: ${fixture.name}`, () => {
    const actual = sandbox.scheduler.schedule(fixture.input, fixture.grade, fixture.reviewedAtUtc);
    for (const [key, value] of Object.entries(fixture.expected)) {
      if (key === "nextReviewAt") assert.equal(new Date(actual[key]).getTime(), new Date(value).getTime(), key);
      else assert.equal(actual[key], value, key);
    }
  });
}

test("unknown grades are rejected", () => {
  assert.throws(() => sandbox.scheduler.schedule({}, "almost", "2026-01-01T00:00:00Z"));
});
