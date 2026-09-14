import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SOURCE = fs.readFileSync(path.join(HERE, "..", "src", "web", "lookup_panel.js"), "utf8");

/* The panel asks its host what is allowed and what a selection belongs to, instead of
 * matching `location.pathname` and reading another file's globals (LEX-19, §11.2). */
function mount({ host, selectionText = "承ります", pathname = "/lexicon" } = {}) {
  const listeners = new Map();
  const requests = [];
  let responder = async () => ({ results: [] });

  const makeNode = (tag) => {
    const node = {
      tagName: String(tag).toUpperCase(), children: [], dataset: {}, attributes: {},
      className: "", hidden: false, disabled: false, type: "", value: "", href: "",
      _text: "",
      get textContent() {
        return this._text || this.children.map((child) => child.textContent).join("");
      },
      set textContent(value) { this._text = String(value); this.children = []; },
      append(...items) { this.children.push(...items); },
      replaceChildren(...items) { this.children = [...items]; this._text = ""; },
      setAttribute(name, value) { this.attributes[name] = String(value); },
      addEventListener(name, fn) { (this.handlers ||= {})[name] = fn; },
      contains: () => false,
      closest: () => null,
      focus() { focused.push(this); },
      querySelector: () => null,
      remove() {},
    };
    return node;
  };
  const focused = [];
  const created = [];
  const body = makeNode("body");

  const document_ = {
    body,
    activeElement: makeNode("button"),
    createElement: (tag) => { const node = makeNode(tag); created.push(node); return node; },
    querySelector: () => null,
    addEventListener: (name, fn) => listeners.set(name, fn),
    contains: () => true,
  };

  const context = vm.createContext({
    console, Date, JSON, Number, String, Boolean, Error, Promise, Math,
    setTimeout: (fn) => fn(),
    document: document_,
    location: { pathname, hash: "#/x" },
    // The stub nodes are plain objects, so `instanceof HTMLElement` is taught to mean
    // "something focusable" for the purposes of the focus-restore path.
    HTMLElement: new Proxy(class {}, {
      get: (target, key) => (key === Symbol.hasInstance
        ? (value) => Boolean(value && typeof value.focus === "function")
        : Reflect.get(target, key)),
    }),
    encodeURIComponent,
    fetch: async (url, options) => {
      requests.push({ url, options });
      if (String(url).includes("bootstrap")) {
        return { ok: true, json: async () => ({ token: "t" }) };
      }
      return { ok: true, status: 200, json: async () => responder(url, options) };
    },
    getSelection: () => ({
      toString: () => selectionText,
      anchorNode: { parentElement: { closest: () => null, textContent: "ご意見を承ります。" } },
      rangeCount: 0,
    }),
  });
  context.window = {
    LexLookupHost: host,
    getSelection: context.getSelection,
    addEventListener: (name, fn) => listeners.set(`win:${name}`, fn),
  };
  context.globalThis = context;
  vm.runInContext(SOURCE, context);

  const panel = created[0];
  return {
    panel, listeners, requests, focused, document: document_,
    setResponder: (fn) => { responder = fn; },
    select: () => listeners.get("mouseup")(),
    press: (event) => listeners.get("keydown")(event),
    findButton: (label) => {
      const walk = (node) => {
        if (node.tagName === "BUTTON" && node.textContent === label) return node;
        for (const child of node.children || []) { const hit = walk(child); if (hit) return hit; }
        return null;
      };
      return walk(panel);
    },
  };
}

test("the host decides whether a lookup is offered at all", () => {
  const blocked = mount({ host: { canLookup: () => false } });
  blocked.select();
  assert.equal(blocked.panel.hidden, true, "a timed sitting stays closed");

  const open = mount({ host: { canLookup: () => true } });
  open.select();
  assert.equal(open.panel.hidden, false);
});

test("a host that throws is treated as not now", () => {
  const broken = mount({ host: { canLookup() { throw new Error("boom"); } } });
  broken.select();
  // Guessing "yes" would put a lookup panel over an exam.
  assert.equal(broken.panel.hidden, true);
});

test("with no host registered the panel still works", () => {
  const bare = mount({ host: undefined });
  bare.select();
  assert.equal(bare.panel.hidden, false);
});

test("selecting text offers the action and never fires the query", () => {
  const view = mount({ host: { canLookup: () => true } });
  view.select();
  assert.equal(view.requests.length, 0, "looking a word up is an explicit act");
  assert.ok(view.findButton("查询词汇 / 语法"));
});

test("the saved context carries the host's identifiers and the offsets", async () => {
  const view = mount({
    host: {
      canLookup: () => true,
      getSelectionContext: () => ({
        hostType: "listening", courseId: "c1", sentenceId: "s3",
        sourceRevision: "rev-1", text: "ご意見を承ります。", startOffset: 4, endOffset: 9,
      }),
    },
  });
  view.setResponder(() => ({
    results: [{ id: "1", sourceRef: "dict:jmdict#1", headword: "承る", reading: "うけたまわる",
                readingCandidates: ["うけたまわる"], gloss: { zh: "恭听" }, kind: "word" }],
  }));
  view.select();
  await view.findButton("查询词汇 / 语法").handlers.click();
  await view.findButton("收藏并保留原句").handlers.click();

  const save = view.requests.find((item) => item.options?.method === "PUT");
  const context = JSON.parse(save.options.body).context;
  // `page` alone cannot find the sentence again, which is all the old panel stored.
  assert.equal(context.courseId, "c1");
  assert.equal(context.sentenceId, "s3");
  assert.equal(context.sourceRevision, "rev-1");
  assert.equal(context.startOffset, 4);
  assert.equal(context.endOffset, 9);
  assert.equal(context.selection, "承ります");
  assert.ok(context.page, "the page is kept for compatibility");
});

test("a favourite records the chosen reading, not the record's first", async () => {
  const view = mount({ host: { canLookup: () => true } });
  view.setResponder(() => ({
    results: [{ id: "1", sourceRef: "dict:jmdict#1", headword: "大人",
                readingCandidates: ["おとな", "たいじん"], gloss: {}, kind: "word", senseCount: 2 }],
  }));
  view.select();
  await view.findButton("查询词汇 / 语法").handlers.click();
  const select = (function find(node) {
    if (node.tagName === "SELECT") return node;
    for (const child of node.children || []) { const hit = find(child); if (hit) return hit; }
    return null;
  })(view.panel);
  assert.ok(select, "a multi-reading hit offers a choice");
  select.value = "たいじん";
  await view.findButton("收藏并保留原句").handlers.click();
  const save = view.requests.find((item) => item.options?.method === "PUT");
  assert.equal(JSON.parse(save.options.body).reading, "たいじん");
});

test("closing abandons an in-flight lookup and restores focus", async () => {
  const view = mount({ host: { canLookup: () => true } });
  let release = () => {};
  const slow = new Promise((resolve) => {
    release = () => resolve({ results: [{ id: "1", sourceRef: "dict:jmdict#1", headword: "晚到", gloss: {} }] });
  });
  view.setResponder(() => slow);
  view.select();
  const pending = view.findButton("查询词汇 / 语法").handlers.click();
  view.findButton("关闭").handlers.click();
  release();
  await pending;
  // A late response must not repopulate a panel the learner already closed.
  assert.equal(view.panel.hidden, true);
  assert.equal(view.focused.length, 1);
});

test("escape closes the panel", () => {
  const view = mount({ host: { canLookup: () => true } });
  view.select();
  view.press({ key: "Escape" });
  assert.equal(view.panel.hidden, true);
});

test("a keyboard shortcut offers the lookup without a mouse", () => {
  const view = mount({ host: { canLookup: () => true } });
  let prevented = false;
  view.press({ key: "k", ctrlKey: true, preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(view.panel.hidden, false);
});
