/* The studio workbench had none of the guards the player has.
 *
 * It is the same situation `web_integrity.test.mjs` was written for — no build
 * step, so nothing between an editor and the browser checks that the page is even
 * parseable — except that the workbench also *runs the machine*: it starts and
 * stops the local model services and launches builds. A silently dead panel there
 * is not a cosmetic bug, and one already shipped: `index.html` still carries a
 * whole 课程编辑器 section whose every handler is defined and never wired.
 *
 * The five checks below are the player's three, plus two the workbench earns on
 * its own: a page may not load two scripts that declare the same top-level name
 * (studio.js and editor.js each had their own `fillSelect`, with *different*
 * behaviour), and every handler a page's scripts define must actually be reachable.
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

import {
  BROWSER_GLOBALS, calledNames, declaredGlobals, declaredLocalNames, scriptsFor, stripNonCode,
} from "./web_scan.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STUDIO = path.join(HERE, "..", "src", "studio_web");

const PAGES = ["index.html", "import.html", "ops.html", "library.html", "editor.html"];

/** Element ids a script addresses, across every lookup idiom in this folder. */
function addressedIds(source) {
  const ids = new Set();
  const patterns = [
    /\bel\("([A-Za-z0-9_-]+)"\)/g,
    /\$\("#?([A-Za-z0-9_-]+)"\)/g,
    /getElementById\("([A-Za-z0-9_-]+)"\)/g,
    /querySelector\("#([A-Za-z0-9_-]+)"\)/g,
  ];
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) ids.add(match[1]);
  }
  // The pre-modularisation studio.js collected every id up front into one flat
  // array. Reading it here is what let this test cover that file before it was
  // split; it matches nothing once a page uses the shared `el()` lookup.
  for (const block of source.matchAll(/for \(const id of \[([\s\S]*?)\]\)/g)) {
    for (const literal of block[1].matchAll(/"([A-Za-z0-9_-]+)"/g)) ids.add(literal[1]);
  }
  return ids;
}

function pageIds(markup) {
  return [...markup.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
}

for (const page of PAGES) {
  const scripts = scriptsFor(STUDIO, page);
  const markup = fs.readFileSync(path.join(STUDIO, page), "utf8");

  test(`${page}: every script it loads parses`, () => {
    assert.ok(scripts.length, `${page} loads no scripts`);
    for (const script of scripts) {
      const source = fs.readFileSync(path.join(STUDIO, script), "utf8");
      assert.doesNotThrow(
        () => new vm.Script(source, { filename: script }),
        `${script} does not parse — the browser would not run a line of it`,
      );
    }
  });

  test(`${page}: declares no id twice`, () => {
    const ids = pageIds(markup);
    const seen = new Set();
    const dupes = [...new Set(ids.filter((id) => (seen.has(id) ? true : (seen.add(id), false))))].sort();
    assert.deepEqual(dupes, [], `${page} repeats id ${dupes.join(", ")} — getElementById would pick one at random`);
  });

  test(`${page}: defines every function its scripts call`, () => {
    const available = new Set(BROWSER_GLOBALS);
    for (const script of scripts) {
      const source = fs.readFileSync(path.join(STUDIO, script), "utf8");
      for (const name of declaredGlobals(source)) available.add(name);
      for (const match of source.matchAll(/^\s*(?:const|let|var)?\s*(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)/gm)) {
        available.add(match[1]);
      }
    }
    const problems = [];
    for (const script of scripts) {
      const raw = fs.readFileSync(path.join(STUDIO, script), "utf8");
      const local = new Set([...available, ...declaredLocalNames(raw)]);
      for (const name of calledNames(stripNonCode(raw))) {
        if (!local.has(name) && !globalThis[name]) problems.push(`${script}: ${name}()`);
      }
    }
    assert.deepEqual(problems, [], `undefined functions called:\n  ${problems.join("\n  ")}`);
  });

  test(`${page}: no two of its scripts declare the same top-level name`, () => {
    const owner = new Map();
    const clashes = [];
    for (const script of scripts) {
      const source = fs.readFileSync(path.join(STUDIO, script), "utf8");
      for (const name of declaredGlobals(source)) {
        // Two files may legitimately both mention `window.X = …`; what must not
        // happen is two *declarations* of one name, where load order silently
        // decides which behaviour the page gets.
        if (owner.has(name)) clashes.push(`${name}: ${owner.get(name)} and ${script}`);
        else owner.set(name, script);
      }
    }
    assert.deepEqual(clashes, [], `one page, two declarations:\n  ${clashes.join("\n  ")}`);
  });
}

test("every element id the workbench addresses exists on a page that loads it", () => {
  // A module shared by both pages may address an element only one of them has —
  // gpu.js draws cards on the build page and a pill in the editor's top bar — so
  // the union of its own pages is the right scope. An id that exists on no page
  // is still a typo, and still fails here.
  const pagesOf = new Map();
  for (const page of PAGES) {
    for (const script of scriptsFor(STUDIO, page)) {
      if (!pagesOf.has(script)) pagesOf.set(script, []);
      pagesOf.get(script).push(page);
    }
  }
  const missing = [];
  for (const [script, owners] of pagesOf) {
    const present = new Set(owners.flatMap((page) => pageIds(fs.readFileSync(path.join(STUDIO, page), "utf8"))));
    const source = fs.readFileSync(path.join(STUDIO, script), "utf8");
    for (const id of addressedIds(source)) {
      if (!present.has(id)) missing.push(`${script} -> #${id} (loaded by ${owners.join(", ")})`);
    }
  }
  assert.deepEqual(missing.sort(), [], `addressed but on no page that loads it:\n  ${missing.join("\n  ")}`);
});

test("every handler the workbench defines is reachable from its page", () => {
  // A function nobody calls and no element is bound to is a panel that cannot
  // open. `openCourseEditor` sat in studio.js for months in exactly that state.
  const unreachable = [];
  for (const page of PAGES) {
    const scripts = scriptsFor(STUDIO, page);
    // References are counted on the raw text, not the stripped text: a call that
    // only appears inside a template literal — `${escapeHtml(title)}` — is a real
    // call, and stripping discards it. Counting a mention in a comment as a use
    // only weakens this check; missing a real use would condemn working code.
    const sources = scripts.map((script) => ({
      script,
      code: fs.readFileSync(path.join(STUDIO, script), "utf8"),
    }));
    const whole = sources.map((item) => item.code).join("\n");
    for (const { script, code } of sources) {
      for (const match of code.matchAll(/^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)/gm)) {
        const name = match[1];
        // Referenced anywhere other than its own definition line: called,
        // passed as a listener, or exported through a namespace object.
        const references = [...whole.matchAll(new RegExp(`\\b${name}\\b`, "g"))].length;
        const definitions = [...whole.matchAll(new RegExp(`function\\s+${name}\\b`, "g"))].length;
        if (references <= definitions) unreachable.push(`${page} · ${script}: ${name}()`);
      }
    }
  }
  assert.deepEqual(unreachable, [], `defined but never reached:\n  ${unreachable.join("\n  ")}`);
});

test("the two review queues look like something you can open", () => {
  // The sections are the editor's entry points and both start shut, so the
  // affordance is the whole interface until one is opened: a tinted header that
  // darkens when open, and a label saying what a click will do.
  const css = fs.readFileSync(path.join(STUDIO, "editor.css"), "utf8");

  const head = css.match(/\.target-group-head \{([^}]*)\}/);
  assert.ok(head, ".target-group-head must be styled");
  assert.match(head[1], /background:/, "the header carries a tint of its own");

  const open = css.match(/\.target-group\[open\] \.target-group-head \{([^}]*)\}/);
  assert.ok(open, "an open section must be distinguishable from a shut one");
  assert.match(open[1], /background:/);
  assert.notEqual(
    head[1].match(/background:\s*([^;]+)/)[1].trim(),
    open[1].match(/background:\s*([^;]+)/)[1].trim(),
    "open and shut must not be the same colour",
  );

  assert.match(css, /\.target-group-head::after \{[^}]*content:\s*"展开/, "shut says 展开");
  assert.match(css, /\.target-group\[open\] \.target-group-head::after \{\s*content:\s*"收起/, "open says 收起");
});

test("the workbench nav stays sticky at the top when scrolling", () => {
  const css = fs.readFileSync(path.join(STUDIO, "studio.css"), "utf8");
  const nav = css.match(/\.nav\s*\{([^}]*)\}/);
  assert.ok(nav, ".nav must be styled");
  assert.match(nav[1], /position:\s*sticky/, ".nav must have position: sticky");
  assert.match(nav[1], /top:\s*0/, ".nav must stick at top: 0");
  assert.match(nav[1], /background:/, ".nav must have an opaque background to avoid content bleed");

  const topbar = css.match(/\.topbar\s*\{([^}]*)\}/);
  assert.ok(topbar, ".topbar must be styled");
  assert.ok(!/position:\s*sticky/.test(topbar[1]), ".topbar must not be sticky so nav sits at the top on scroll");
});
