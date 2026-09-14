// Renderer tests for src/web/exam_markup.js.
//
// Loaded into a sandbox with a minimal DOM, the way sw.js is loaded into
// sw_harness.mjs — asserting against a reimplementation of the renderer would test
// the copy rather than the code that ships.
//
// The load-bearing tests here are the ones about text that only *looks* like
// markup. Question text is a transcription of a scanned exam page produced by a
// model reading an image; if a stray "<script>" or a truncated "<u>" in that text
// could become structure, the transcription would be a script-injection channel
// into a page that also holds the learner's notebook.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const MARKUP_PATH = join(here, "..", "src", "web", "exam_markup.js");

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

/** Serialise the tree so assertions can talk about structure, not object graphs. */
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
  vm.runInContext(readFileSync(MARKUP_PATH, "utf8"), sandbox, { filename: "exam_markup.js" });
  return { markup: sandbox.ExamMarkup, document };
}

const { markup, document } = loadMarkup();

function inline(text) {
  const host = document.createElement("div");
  markup.renderInline(text, host);
  return host;
}

function blocks(text) {
  const host = document.createElement("div");
  markup.renderBlocks(text, host);
  return host;
}

// --- plain text ------------------------------------------------------------

test("plain text passes through unchanged", () => {
  const host = inline("勇敢に戦う主人公に子どもたちは夢中だ。");
  assert.equal(serialise(host), "<div>勇敢に戦う主人公に子どもたちは夢中だ。</div>");
  assert.deepEqual(tags(host), []);
});

test("null and undefined render as nothing rather than the string 'null'", () => {
  assert.equal(inline(null).textContent, "");
  assert.equal(inline(undefined).textContent, "");
});

// --- underline -------------------------------------------------------------

test("an underlined span becomes a real <u> element", () => {
  const host = inline("その件について、<u>忠告</u>すべきか。");
  assert.equal(serialise(host), "<div>その件について、<u>忠告</u>すべきか。</div>");
});

test("two underlined spans in one sentence both render", () => {
  const host = inline("<u>あ</u>と<u>い</u>");
  assert.deepEqual(tags(host), ["u", "u"]);
  assert.equal(host.textContent, "あとい");
});

test("an unclosed <u> stays literal text instead of swallowing the rest", () => {
  const host = inline("<u>勇敢に戦う。");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "<u>勇敢に戦う。");
});

test("a stray closing tag stays literal text", () => {
  const host = inline("勇敢</u>に戦う。");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "勇敢</u>に戦う。");
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

test("a table cell cannot introduce an element either", () => {
  const host = blocks("| <script>alert(1)</script> | b |");
  assert.deepEqual(tags(host), ["div", "table", "tbody", "tr", "td", "td"]);
  assert.equal(host.textContent, "<script>alert(1)</script>b");
});

// --- ruby ------------------------------------------------------------------

test("printed furigana becomes a ruby annotation", () => {
  const host = inline("｜前頭葉《ぜんとうよう》という部分");
  assert.equal(
    serialise(host),
    "<div><ruby>前頭葉<rt>ぜんとうよう</rt></ruby>という部分</div>",
  );
});

test("several ruby runs in one paragraph all render", () => {
  const host = inline("｜閃《ひらめ》きと｜莫大《ばくだい》な情報");
  assert.deepEqual(tags(host), ["ruby", "rt", "ruby", "rt"]);
  assert.equal(host.textContent, "閃ひらめきと莫大ばくだいな情報");
});

test("an ASCII pipe is not mistaken for ruby", () => {
  const host = inline("A | B");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "A | B");
});

test("an unclosed ruby bracket stays literal", () => {
  const host = inline("｜漢字《かんじ");
  assert.deepEqual(tags(host), []);
  assert.equal(host.textContent, "｜漢字《かんじ");
});

// --- boxed numbers and the star -------------------------------------------

test("a boxed question number becomes its own element", () => {
  const host = inline("そこ【41】に行って驚くのは");
  assert.equal(
    serialise(host),
    '<div>そこ<span class="boxed-number">41</span>に行って驚くのは</div>',
  );
});

test("the reordering star is marked up so it can be highlighted", () => {
  const host = inline("私は＿＿＿＿、＿＿★＿＿と思う。");
  assert.equal(tags(host).filter((tag) => tag === "span").length, 1);
  assert.ok(serialise(host).includes('<span class="star">★</span>'));
});

test("underline, ruby and a boxed number compose in one string", () => {
  const host = inline("<u>｜理解《りかい》する</u>ことは【59】である");
  assert.deepEqual(tags(host), ["u", "ruby", "rt", "span"]);
  assert.equal(host.textContent, "理解りかいすることは59である");
});

// --- blocks ----------------------------------------------------------------

test("each line becomes its own paragraph", () => {
  const host = blocks("一段落目。\n二段落目。");
  assert.deepEqual(tags(host), ["p", "p"]);
  assert.equal(host.children[0].textContent, "一段落目。");
  assert.equal(host.children[1].textContent, "二段落目。");
});

test("blank lines do not produce empty paragraphs", () => {
  const host = blocks("一段落目。\n\n\n二段落目。");
  assert.deepEqual(tags(host), ["p", "p"]);
});

test("a callout line becomes a blockquote", () => {
  const host = blocks("前の段落。\n> 枠で囲まれた注意書き。\n後ろの段落。");
  assert.deepEqual(tags(host), ["p", "blockquote", "p", "p"]);
  assert.equal(host.children[1].textContent, "枠で囲まれた注意書き。");
});

test("consecutive callout lines join into one blockquote", () => {
  const host = blocks("> 一行目\n> 二行目");
  assert.deepEqual(tags(host), ["blockquote", "p", "p"]);
});

// --- tables ----------------------------------------------------------------

test("a pipe table with a rule row gets a real header", () => {
  const host = blocks(
    "|  | 一つの講座の受講料 | 補助金額 |\n| --- | --- | --- |\n| A | 30,000円以上 | 25,000円 |",
  );
  assert.deepEqual(
    tags(host),
    ["div", "table", "thead", "tr", "th", "th", "th", "tbody", "tr", "td", "td", "td"],
  );
});

test("a table without a rule row is all body rows", () => {
  const host = blocks("| A | 30,000円以上 |\n| B | 30,000円未満 |");
  assert.deepEqual(tags(host), ["div", "table", "tbody", "tr", "td", "td", "tr", "td", "td"]);
});

test("a table is wrapped so a wide leaflet scrolls instead of breaking the layout", () => {
  const host = blocks("| A | B |");
  assert.equal(host.children[0].className, "table-scroll");
});

test("text around a table keeps its own paragraphs", () => {
  const host = blocks("前書き。\n| A | B |\n| C | D |\n後書き。");
  assert.deepEqual(tags(host).slice(0, 2), ["p", "div"]);
  assert.equal(tags(host).at(-1), "p");
});

test("ruby inside a table cell still renders", () => {
  const host = blocks("| ｜前頭葉《ぜんとうよう》 | b |");
  assert.ok(tags(host).includes("ruby"));
});

// --- plainText -------------------------------------------------------------

test("plainText strips markup for use in one-line summaries", () => {
  assert.equal(markup.plainText("<u>忠告</u>する"), "忠告する");
  assert.equal(markup.plainText("｜前頭葉《ぜんとうよう》"), "前頭葉");
  assert.equal(markup.plainText("そこ【41】に"), "そこ［41］に");
  assert.equal(markup.plainText(null), "");
});

// --- the real paper --------------------------------------------------------
//
// Rendering the fixture proves the parser works; rendering the shipped exam proves
// the transcription and the parser agree. A passage that renders to nothing, or a
// choice that renders blank, is a question the learner cannot answer — and neither
// shows up in the Python audit, which only checks the markup is balanced.

test("every question, passage and choice in the shipped exam renders", async (t) => {
  const examPath = join(here, "..", "exams", "2022-07-N1", "exam.json");
  let exam;
  try {
    exam = JSON.parse(readFileSync(examPath, "utf8"));
  } catch {
    t.skip("exams/2022-07-N1/exam.json is not present");
    return;
  }

  let questions = 0;
  let passages = 0;
  let choices = 0;
  const produced = { table: 0, ruby: 0, blockquote: 0, u: 0 };
  const tally = (node) => {
    for (const tag of tags(node)) {
      if (tag in produced) produced[tag] += 1;
    }
  };

  for (const section of exam.sections) {
    for (const part of section.parts) {
      for (const passage of part.passages) {
        const host = blocks(passage.text);
        assert.notEqual(host.textContent.trim(), "", `passage ${passage.id} rendered empty`);
        tally(host);
        passages += 1;
        for (const note of passage.notes) inline(note);
      }
      for (const question of part.questions) {
        const host = inline(question.prompt);
        tally(host);
        questions += 1;
        for (const choice of question.choices) {
          const rendered = inline(choice);
          assert.notEqual(
            rendered.textContent.trim(),
            "",
            `a choice on ${question.answerSheetLabel} rendered empty`,
          );
          choices += 1;
        }
      }
    }
  }

  assert.equal(questions, exam.questionCount);
  assert.equal(passages, 13);
  assert.equal(choices, 340);
  // The paper's awkward shapes actually reached the renderer rather than being
  // flattened away during import: 問題13's leaflet table and its callout box,
  // the furigana printed through 読解, and the underlined spans in 問題1/3/10/12.
  assert.equal(produced.table, 1, "問題13's fee table");
  assert.equal(produced.blockquote, 1, "問題13's callout box");
  assert.ok(produced.ruby >= 20, `expected the printed furigana, saw ${produced.ruby}`);
  assert.ok(produced.u >= 12, `expected the underlined spans, saw ${produced.u}`);
});
