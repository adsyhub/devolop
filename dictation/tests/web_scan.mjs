/* Static scanners shared by the front-end guard tests.
 *
 * Extracted from web_symbols.test.mjs so the studio workbench can be held to the
 * same three checks as the player without a second copy of the heuristics: one
 * copy that is wrong in one place is the failure mode these tests exist to stop.
 */

import fs from "node:fs";
import path from "node:path";


/* A call to a function nobody defines is a ReferenceError at the first line that runs
 * it. When that line is in the page's init, nothing gets wired up and the workspace
 * renders as an empty shell — which is exactly what shipped once, because an edit that
 * added the calls landed while the edit that added the definitions did not.
 *
 * Parsing catches syntax, not this. So each page is checked against the globals it
 * actually has: its own top-level declarations, the scripts its HTML loads before it,
 * and the browser API surface. */

/**
 * Strip comments and string literals.
 *
 * Without this the scan reads prose: a comment ending in "retryable (§8.1)" looks
 * exactly like a call to `retryable()`.
 */
export function stripNonCode(source) {
  let out = "";
  let index = 0;
  const n = source.length;
  while (index < n) {
    const two = source.slice(index, index + 2);
    if (two === "//") {
      const end = source.indexOf("\n", index);
      index = end < 0 ? n : end;
      continue;
    }
    if (two === "/*") {
      const end = source.indexOf("*/", index + 2);
      index = end < 0 ? n : end + 2;
      out += " ";
      continue;
    }
    const char = source[index];
    if (char === "/" && /[(,=:[!&|?{};+\-*%~^\n]\s*$/.test(out.slice(-40) + "")) {
      // A regex literal. `/^#\\/listening(?:…)?$/` otherwise reads as `listening(`.
      index += 1;
      while (index < n) {
        if (source[index] === "\\") { index += 2; continue; }
        if (source[index] === "[") {
          while (index < n && source[index] !== "]") {
            index += source[index] === "\\" ? 2 : 1;
          }
        }
        if (source[index] === "/" || source[index] === "\n") { index += 1; break; }
        index += 1;
      }
      out += "0";
      continue;
    }
    if (char === '"' || char === "'" || char === "`") {
      index += 1;
      let depth = 0;
      while (index < n) {
        if (source[index] === "\\") { index += 2; continue; }
        if (char === "`" && source.slice(index, index + 2) === "${") { depth += 1; index += 2; continue; }
        if (char === "`" && depth > 0 && source[index] === "}") { depth -= 1; index += 1; continue; }
        if (depth === 0 && source[index] === char) { index += 1; break; }
        index += 1;
      }
      out += '""';
      continue;
    }
    out += char;
    index += 1;
  }
  return out;
}

export const BROWSER_GLOBALS = new Set([
  "window", "document", "location", "navigator", "console", "localStorage", "sessionStorage",
  "fetch", "setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame",
  "alert", "confirm", "prompt", "structuredClone", "crypto", "indexedDB", "caches",
  "BroadcastChannel", "URL", "URLSearchParams", "Blob", "FormData", "Event", "CustomEvent",
  "SpeechSynthesisUtterance", "speechSynthesis", "Intl", "performance", "getSelection",
  "HTMLElement", "Audio", "Image", "AbortController", "TextEncoder", "TextDecoder",
  "matchMedia", "ResizeObserver", "IntersectionObserver", "MutationObserver", "FileReader",
  "requestIdleCallback", "queueMicrotask", "reportError", "close", "open", "self",
  "encodeURIComponent", "decodeURIComponent", "encodeURI", "decodeURI",
]);

/** Top-level `const`/`let`/`var`/`function`/`class` names an IIFE-free script exposes. */
export function declaredGlobals(source) {
  const names = new Set();
  const patterns = [
    /^(?:const|let|var)\s+([A-Za-z_$][\w$]*)/gm,
    /^async\s+function\s+([A-Za-z_$][\w$]*)/gm,
    /^function\s*\*?\s*([A-Za-z_$][\w$]*)/gm,
    /^class\s+([A-Za-z_$][\w$]*)/gm,
    // `window.Foo = ...` is how the lookup host and similar are published.
    /^(?:window|globalThis|self)\.([A-Za-z_$][\w$]*)\s*=/gm,
  ];
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) names.add(match[1]);
  }
  return names;
}

/** Every bare `name(` call site, excluding property calls and declarations. */
export function calledNames(source) {
  const names = new Set();
  for (const match of source.matchAll(/(^|[^.\w$])([A-Za-z_$][\w$]*)\s*\(/g)) {
    names.add(match[2]);
  }
  const declarations = new Set();
  for (const match of source.matchAll(/(?:function\s*\*?\s*|class\s+)([A-Za-z_$][\w$]*)/g)) {
    declarations.add(match[1]);
  }
  const keywords = new Set([
    "if", "for", "while", "switch", "catch", "return", "typeof", "new", "await", "function",
    "class", "do", "else", "try", "throw", "yield", "delete", "void", "in", "of", "instanceof",
    // `async (…) => …` reads as a call to `async`.
    "case", "with", "super", "import", "export", "const", "let", "var", "async", "static", "get", "set",
  ]);
  return [...names].filter((name) => !keywords.has(name) && !declarations.has(name));
}

export function declaredLocalNames(source) {
  const names = new Set();
  const patterns = [
    /\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)/g,
    /\bfunction\s*\*?\s*([A-Za-z_$][\w$]*)/g,
    /\bclass\s+([A-Za-z_$][\w$]*)/g,
    /\b([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(/g,
    /\b(?:const|let|var)\s*\{([^}]*)\}/g,
    /\bcatch\s*\(\s*([A-Za-z_$][\w$]*)/g,
    // Object-literal shorthand methods: `{ on(handler) { … } }` is a definition, and
    // reads to the call scanner exactly like `on(handler)`.
    /[{,]\s*(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{/g,
    // Class fields and methods, including accessors: `get paused() { … }` reads to the
    // call scanner as `paused()`.
    /^\s*(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{/gm,
    /\bfunction[^(]*\(([^)]*)\)/g,
    /\(([^()]*)\)\s*=>/g,
  ];
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) {
      for (const part of String(match[1]).split(",")) {
        const name = part.trim().split(/[:=\s]/)[0].replace(/^\.\.\./, "");
        if (/^[A-Za-z_$][\w$]*$/.test(name)) names.add(name);
      }
    }
  }
  return names;
}


/** Scripts a page loads, in order. Both `src="./x.js"` and `src="x.js"` are used. */
export function scriptsFor(dir, page) {
  const html = fs.readFileSync(path.join(dir, page), "utf8");
  return [...html.matchAll(/<script src="(?:\.\/)?([^"]+)"/g)].map((match) => match[1]);
}
