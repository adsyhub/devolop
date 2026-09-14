import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.join(HERE, "..", "src", "web");

import {
  BROWSER_GLOBALS, calledNames, declaredGlobals, declaredLocalNames, scriptsFor, stripNonCode,
} from "./web_scan.mjs";

const PAGES = ["lexicon.html", "me.html", "index.html", "exam.html"];

for (const page of PAGES) {
  test(`${page} defines every function its scripts call`, () => {
    const scripts = scriptsFor(WEB, page);
    assert.ok(scripts.length, `${page} loads no scripts`);
    const available = new Set(BROWSER_GLOBALS);
    const problems = [];
    for (const script of scripts) {
      const source = fs.readFileSync(path.join(WEB, script), "utf8");
      // Declarations are read from the raw text on purpose. Over-counting a definition
      // only weakens the check; missing one would fail the build for working code.
      for (const name of declaredGlobals(source)) available.add(name);
      for (const match of source.matchAll(/^\s*(?:const|let|var)?\s*(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)/gm)) {
        available.add(match[1]);
      }
      // An IIFE-wrapped module exposes nothing but may still declare inner helpers;
      // its own inner names are already in `available` from the pass above.
    }
    for (const script of scripts) {
      const raw = fs.readFileSync(path.join(WEB, script), "utf8");
      const local = new Set([...available, ...declaredLocalNames(raw)]);
      // Call sites, in contrast, come from the stripped text: a name mentioned only in
      // prose or inside a literal is not a call.
      for (const name of calledNames(stripNonCode(raw))) {
        if (!local.has(name) && !globalThis[name]) problems.push(`${script}: ${name}()`);
      }
    }
    assert.deepEqual(problems, [], `undefined functions called:\n  ${problems.join("\n  ")}`);
  });
}

/** Names bound anywhere inside a file: parameters, inner functions, destructuring. */

test("the service worker precaches every script the pages load", () => {
  const sw = fs.readFileSync(path.join(WEB, "sw.js"), "utf8");
  const precached = new Set([...sw.matchAll(/"\.\/([^"]+)"/g)].map((match) => match[1]));
  const missing = [];
  for (const page of PAGES) {
    for (const script of scriptsFor(WEB, page)) {
      if (!precached.has(script)) missing.push(`${page} -> ${script}`);
    }
  }
  // A page served from the cache with a script that is not cached is an offline page
  // whose init throws.
  assert.deepEqual(missing, [], `not in SHELL_ASSETS:\n  ${missing.join("\n  ")}`);
});

test("every workspace script parses on its own", () => {
  const scripts = new Set(PAGES.flatMap((page) => scriptsFor(WEB, page)));
  for (const script of scripts) {
    const source = fs.readFileSync(path.join(WEB, script), "utf8");
    assert.doesNotThrow(() => new vm.Script(source, { filename: script }), script);
  }
});
