// A <dialog> is hidden by one UA stylesheet rule — `dialog:not([open]) { display: none }`
// — and author styles beat the UA origin outright, with specificity never entering
// into it. So any author rule that sets `display` on a dialog without gating it on
// `[open]` silently disables closing: close() removes the open attribute and the
// backdrop, and the panel stays laid out on screen.
//
// This shipped once, on `.personal-modal { display: flex }`, and the symptom ("我的
// 打开后无法关闭") points nowhere near the stylesheet. Hence a test rather than a
// comment: it names every dialog in the project's HTML and checks each stylesheet
// rule that can match one.

import assert from "node:assert/strict";
import test from "node:test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.join(HERE, "..", "src", "web");

const PAGES = ["index.html", "exam.html", "home.html", "me.html"];
const STYLESHEETS = ["app.css", "exam.css", "me.css"];

/** Every id and class that appears on a <dialog> element in the project's pages. */
function dialogSelectors() {
  const ids = new Set();
  const classes = new Set();
  for (const page of PAGES) {
    const file = path.join(WEB, page);
    if (!fs.existsSync(file)) continue;
    const html = fs.readFileSync(file, "utf8");
    for (const tag of html.match(/<dialog\b[^>]*>/g) || []) {
      const id = /\sid="([^"]+)"/.exec(tag);
      if (id) ids.add(`#${id[1]}`);
      const cls = /\sclass="([^"]+)"/.exec(tag);
      if (cls) cls[1].trim().split(/\s+/).forEach((name) => classes.add(`.${name}`));
    }
  }
  return { ids, classes };
}

/** Flat list of {selector, body} for every top-level rule, skipping at-rule wrappers. */
function rules(css) {
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const found = [];
  const pattern = /([^{}]+)\{([^{}]*)\}/g;
  let match;
  while ((match = pattern.exec(stripped)) !== null) {
    const selector = match[1].trim();
    if (!selector || selector.startsWith("@")) continue;
    found.push({ selector, body: match[2] });
  }
  return found;
}

/** Does this comma-separated selector have a compound that can match a dialog? */
function matchingCompound(selector, { ids, classes }) {
  for (const part of selector.split(",")) {
    // Only the rightmost compound decides what the rule applies to.
    const compound = part.trim().split(/[\s>+~]+/).pop() || "";
    if (!compound) continue;
    const isDialog =
      /^dialog\b/.test(compound)
      || [...ids].some((id) => compound.startsWith(id))
      || [...classes].some((cls) => compound.split(/(?=[.#:[])/).includes(cls));
    if (isDialog) return compound;
  }
  return null;
}

test("no stylesheet sets display on a dialog without gating it on [open]", () => {
  const selectors = dialogSelectors();
  assert.ok(selectors.ids.size > 0, "found no <dialog> elements to check — the scan is broken");

  const offenders = [];
  for (const sheet of STYLESHEETS) {
    const file = path.join(WEB, sheet);
    if (!fs.existsSync(file)) continue;
    for (const { selector, body } of rules(fs.readFileSync(file, "utf8"))) {
      if (!/(^|[;{\s])display\s*:/.test(body)) continue;
      const compound = matchingCompound(selector, selectors);
      if (!compound) continue;
      // `[open]` on the compound, or `:not([open])` deliberately hiding it, are both fine.
      if (compound.includes("[open]")) continue;
      const display = /display\s*:\s*([^;]+)/.exec(body)[1].trim();
      if (display === "none") continue;
      offenders.push(`${sheet}: ${selector} { display: ${display} }`);
    }
  }

  assert.deepEqual(
    offenders,
    [],
    "these rules keep a closed <dialog> on screen; move `display` behind [open]:\n  "
      + offenders.join("\n  "),
  );
});

test("the personal centre still gets its column layout while open", () => {
  const css = fs.readFileSync(path.join(WEB, "app.css"), "utf8");
  const rule = rules(css).find((r) => r.selector === ".personal-modal[open]");
  assert.ok(rule, ".personal-modal[open] rule is missing — the dialog would lose its layout");
  assert.match(rule.body, /display\s*:\s*flex/);
  assert.match(rule.body, /flex-direction\s*:\s*column/);
});
