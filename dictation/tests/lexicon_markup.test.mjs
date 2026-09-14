// Renderer tests for src/web/lexicon_markup.js.
//
// Loaded into a sandbox with a minimal DOM, the way exam_markup.js is loaded in
// exam_markup.test.mjs — asserting against a reimplementation of the renderer would
// test the copy rather than the code that ships.
//
// The load-bearing tests are the ones about text that only *looks* like markup. Entry
// text is a transcription of a scanned textbook produced by a model reading an image;
// if a stray "<script>" or a truncated "⟦" in that text could become structure, the
// transcription would be a script-injection channel into a page that also holds the
// learner's notebook.
//
// The second group is about the cloze blank, which is the grammar module's main card:
// a blank that leaks its answer — through its width, or by rendering both states —
// silently turns a recall test into a reading exercise.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const MARKUP_PATH = join(here, "..", "src", "web", "lexicon_markup.js");

// --- the smallest DOM the renderer actually touches ------------------------

class TextNode {
  constructor(text) {
    this.nodeType = 3;
    this.data = String(text);
  }
  get textContent() {
    return this.data;
  }
}

class Element {
  constructor(tag, ownerDocument) {
    this.nodeType = 1;
    this.tagName = String(tag).toLowerCase();
    this.ownerDocument = ownerDocument;
    this.children = [];
    this.className = "";
  }
  appendChild(node) {
    this.children.push(node);
    return node;
  }
  set textContent(value) {
    this.children = [new TextNode(value)];
  }
  get textContent() {
    return this.children.map((child) => child.textContent).join("");
  }
}

class FakeDocument {
  createElement(tag) {
    return new Element(tag, this);
  }
  createTextNode(text) {
    return new TextNode(text);
  }
}

function serialise(node) {
  if (node.nodeType === 3) return node.data;
  const attrs = node.className ? ` class="${node.className}"` : "";
  return `<${node.tagName}${attrs}>${node.children.map(serialise).join("")}</${node.tagName}>`;
}

function tags(node) {
  const found = [];
  const walk = (current) => {
    if (current.nodeType !== 1) return;
    found.push(current.tagName);
    current.children.forEach(walk);
  };
  node.children.forEach(walk);
  return found;
}

function loadMarkup() {
  const document = new FakeDocument();
  const sandbox = { document, globalThis: undefined };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(readFileSync(MARKUP_PATH, "utf8"), sandbox, { filename: "lexicon_markup.js" });
  return { markup: sandbox.LexiconMarkup, document };
}

const { markup, document } = loadMarkup();

function inline(text, options) {
  const host = document.createElement("div");
  markup.renderInline(text, host, options);
  return host;
}

function blocks(text) {
  const host = document.createElement("div");
  markup.renderBlocks(text, host);
  return host;
}

// --- plain text ------------------------------------------------------------

test("plain text passes through unchanged", () => {
  const host = inline("子どものことが心配でたまらない。");
  assert.equal(serialise(host), "<div>子どものことが心配でたまらない。</div>");
  assert.deepEqual(tags(host), []);
});

test("null and undefined render as nothing rather than the string 'null'", () => {
  assert.equal(inline(null).textContent, "");
  assert.equal(inline(undefined).textContent, "");
});

// --- injection -------------------------------------------------------------

test("a script tag in a transcription renders as characters, not as an element", () => {
  const host = inline("危ない<script>alert(1)</script>");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "危ない<script>alert(1)</script>");
});

test("an img with an onerror handler renders as characters", () => {
  const host = inline('<img src=x onerror="alert(1)">');
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, '<img src=x onerror="alert(1)">');
});

test("markup smuggled inside an underlined span is still text", () => {
  const host = inline("<u><script>alert(1)</script></u>");
  assert.deepEqual(tags(host), ["u"]);
  assert.equal(host.textContent, "<script>alert(1)</script>");
});

test("markup smuggled inside a connection slot is still text", () => {
  const host = inline("【<script>alert(1)</script>】＋うちに");
  assert.deepEqual(tags(host), ["span"]);
  assert.equal(host.textContent, "<script>alert(1)</script>＋うちに");
});

test("markup smuggled inside a cloze blank is still text", () => {
  const host = inline("これは⟦<script>alert(1)</script>⟧です。");
  assert.deepEqual(tags(host), ["span"]);
  assert.equal(host.textContent, "これは<script>alert(1)</script>です。");
});

test("an unclosed <u> stays literal text instead of swallowing the rest", () => {
  const host = inline("<u>心配でたまらない。");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "<u>心配でたまらない。");
});

// --- ruby ------------------------------------------------------------------

test("printed furigana becomes a ruby annotation", () => {
  const host = inline("｜心配《しんぱい》でたまらない");
  assert.equal(serialise(host), "<div><ruby>心配<rt>しんぱい</rt></ruby>でたまらない</div>");
});

test("an unclosed ruby marker stays literal text", () => {
  const host = inline("｜心配《しんぱい でたまらない");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "｜心配《しんぱい でたまらない");
});

// --- connection slots ------------------------------------------------------

test("a connection placeholder becomes its own element", () => {
  const host = inline("【V辞書形】＋うちに");
  assert.equal(
    serialise(host),
    '<div><span class="conn-slot">V辞書形</span>＋うちに</div>',
  );
});

test("a lone 【 is text, not an element that eats the sentence", () => {
  const host = inline("【V辞書形＋うちに");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "【V辞書形＋うちに");
});

// --- cloze blanks ----------------------------------------------------------

test("a blank shows its answer by default", () => {
  const host = inline("子どものことが心配⟦でたまらない⟧。");
  assert.equal(
    serialise(host),
    '<div>子どものことが心配<span class="cloze-answer">でたまらない</span>。</div>',
  );
});

test("a hidden blank renders no part of the answer", () => {
  const host = inline("子どものことが心配⟦でたまらない⟧。", { cloze: "hide" });
  assert.equal(host.textContent.includes("でたまらない"), false);
  assert.equal(tags(host).length, 1);
});

test("a hidden blank is at least two characters wide however short the answer", () => {
  // Otherwise the gap's width is a hint: a one-character blank rules out every
  // multi-character candidate before the learner has recalled anything.
  const host = inline("あ⟦だ⟧。", { cloze: "hide" });
  assert.equal(host.textContent, "あ＿＿。");
});

test("blank width counts code points, not UTF-16 units", () => {
  const host = inline("あ⟦𠮷野家𠮷野家⟧。", { cloze: "hide" });
  assert.equal(host.textContent, "あ＿＿＿＿＿＿。");
});

test("an unbalanced blank marker stays literal text", () => {
  const host = inline("これは⟦でたまらない。", { cloze: "hide" });
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "これは⟦でたまらない。");
});

// --- connection rows -------------------------------------------------------

test("a connection splits its word class from its inflection", () => {
  const host = document.createElement("div");
  markup.renderConnection({ slot: "i-adjective", form: "くて", display: "イAくて" }, host);
  assert.equal(
    serialise(host),
    '<div><span class="conn"><span class="conn-base">イA</span>'
      + '<span class="conn-form">くて</span></span></div>',
  );
});

test("a connection whose pattern tail is printed keeps the whole display form", () => {
  const host = document.createElement("div");
  markup.renderConnection({ slot: "noun", form: "", display: "Nがち" }, host);
  assert.equal(host.textContent, "Nがち");
});

test("a malformed connection renders as nothing rather than as 'undefined'", () => {
  const host = document.createElement("div");
  markup.renderConnection(null, host);
  assert.equal(host.textContent, "");
});

// --- blocks ----------------------------------------------------------------

test("each line of a note becomes its own paragraph", () => {
  const host = blocks("感情を表す。\n口語でよく使う。");
  assert.deepEqual(tags(host), ["p", "p"]);
  assert.equal(host.children.length, 2);
});

test("blank lines do not produce empty paragraphs", () => {
  assert.equal(blocks("あ\n\n\nい").children.length, 2);
});

// --- plainText -------------------------------------------------------------

test("plainText strips every convention", () => {
  assert.equal(
    markup.plainText("｜心配《しんぱい》で<u>たまらない</u>【V辞書形】⟦です⟧"),
    "心配でたまらない［V辞書形］です",
  );
});

test("plainText never returns the string 'null'", () => {
  assert.equal(markup.plainText(null), "");
});
