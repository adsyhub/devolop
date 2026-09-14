/* Exam text markup → DOM nodes.
 *
 * Split out of exam.js so it can be tested on its own against a minimal DOM shim
 * (tests/exam_markup.test.mjs), the way sw.js is tested against sw_harness.mjs.
 * It is also the one piece where a bug is a security bug rather than a cosmetic
 * one, so it is worth isolating.
 *
 * The rule this file exists to keep: question text is a transcription of a scanned
 * exam paper, produced by a model reading an image. It is *data*. It is never
 * assigned to innerHTML, never passed to insertAdjacentHTML, and never used to
 * build a selector. Everything below constructs elements and text nodes, so a
 * stray "<script>" in a transcription renders as those nine characters.
 *
 * Recognised markup (see exam_schema.py for the authoritative description):
 *   <u>…</u>          the span the paper underlines
 *   ｜漢字《かんじ》      printed furigana → <ruby>漢字<rt>かんじ</rt></ruby>
 *                     (the marker is the FULL-WIDTH bar U+FF5C, as in Aozora
 *                      Bunko, so it cannot collide with a table's ASCII "|")
 *   【41】             a boxed question number printed inside a sentence
 *   ★                 the marked blank in a 並べ替え question
 *   | a | b |         a table row (a "| --- |" row after the first marks a header)
 *   > text            a callout box drawn around a paragraph on the page
 */

(function attach(root) {
  "use strict";

  // Ruby opens with the FULL-WIDTH bar U+FF5C, not ASCII "|". They look alike, and
  // that is the point: a table row is delimited by ASCII pipes, so an ASCII ruby
  // marker made furigana inside a table cell unparseable. Aozora Bunko uses the
  // full-width bar for exactly this reason.
  const INLINE_TOKEN = /｜([^｜《》\n]+)《([^》\n]+)》|【(\d+)】|(★)/g;
  const TABLE_ROW = /^\s*\|.*\|\s*$/;
  const TABLE_RULE = /^:?-{3,}:?$/;
  const QUOTE_LINE = /^\s*>\s?/;

  function doc(node) {
    return (node && node.ownerDocument) || root.document;
  }

  function renderTokens(text, target) {
    const d = doc(target);
    INLINE_TOKEN.lastIndex = 0;
    let last = 0;
    let match;
    while ((match = INLINE_TOKEN.exec(text)) !== null) {
      if (match.index > last) {
        target.appendChild(d.createTextNode(text.slice(last, match.index)));
      }
      if (match[1] !== undefined) {
        const ruby = d.createElement("ruby");
        ruby.appendChild(d.createTextNode(match[1]));
        const rt = d.createElement("rt");
        rt.textContent = match[2];
        ruby.appendChild(rt);
        target.appendChild(ruby);
      } else if (match[3] !== undefined) {
        const box = d.createElement("span");
        box.className = "boxed-number";
        box.textContent = match[3];
        target.appendChild(box);
      } else {
        const star = d.createElement("span");
        star.className = "star";
        star.textContent = "★";
        target.appendChild(star);
      }
      last = INLINE_TOKEN.lastIndex;
    }
    if (last < text.length) target.appendChild(d.createTextNode(text.slice(last)));
  }

  function renderInline(text, target) {
    const value = String(text == null ? "" : text);
    // Split on complete <u>…</u> pairs only. An unbalanced "<u>" therefore falls
    // through to renderTokens and becomes literal text — which is what a truncated
    // transcription should look like, not an element that swallows the rest.
    for (const segment of value.split(/(<u>[\s\S]*?<\/u>)/)) {
      if (!segment) continue;
      const underlined = /^<u>([\s\S]*?)<\/u>$/.exec(segment);
      if (underlined) {
        const u = doc(target).createElement("u");
        renderTokens(underlined[1], u);
        target.appendChild(u);
      } else {
        renderTokens(segment, target);
      }
    }
    return target;
  }

  function splitRow(line) {
    return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
  }

  function buildTable(rows, d) {
    const cells = rows.map(splitRow);
    const wrap = d.createElement("div");
    wrap.className = "table-scroll";
    const table = d.createElement("table");

    let start = 0;
    let header = null;
    if (cells.length > 1 && cells[1].length && cells[1].every((cell) => TABLE_RULE.test(cell))) {
      header = cells[0];
      start = 2;
    }
    if (header) {
      const thead = d.createElement("thead");
      const tr = d.createElement("tr");
      for (const cell of header) {
        const th = d.createElement("th");
        renderInline(cell, th);
        tr.appendChild(th);
      }
      thead.appendChild(tr);
      table.appendChild(thead);
    }
    const tbody = d.createElement("tbody");
    for (let index = start; index < cells.length; index += 1) {
      const tr = d.createElement("tr");
      for (const cell of cells[index]) {
        const td = d.createElement("td");
        renderInline(cell, td);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);
    return wrap;
  }

  function renderBlocks(text, container) {
    const d = doc(container);
    const lines = String(text == null ? "" : text).split("\n");
    let index = 0;
    while (index < lines.length) {
      const line = lines[index];
      if (TABLE_ROW.test(line)) {
        const rows = [];
        while (index < lines.length && TABLE_ROW.test(lines[index])) {
          rows.push(lines[index]);
          index += 1;
        }
        container.appendChild(buildTable(rows, d));
        continue;
      }
      if (QUOTE_LINE.test(line)) {
        const quoted = [];
        while (index < lines.length && QUOTE_LINE.test(lines[index])) {
          quoted.push(lines[index].replace(QUOTE_LINE, ""));
          index += 1;
        }
        const blockquote = d.createElement("blockquote");
        renderBlocks(quoted.join("\n"), blockquote);
        container.appendChild(blockquote);
        continue;
      }
      if (line.trim()) {
        const paragraph = d.createElement("p");
        renderInline(line, paragraph);
        container.appendChild(paragraph);
      }
      index += 1;
    }
    return container;
  }

  /** Markup stripped back to readable text, for titles and one-line summaries. */
  function plainText(markup) {
    return String(markup == null ? "" : markup)
      .replace(/<\/?u>/g, "")
      .replace(/｜([^｜《》\n]+)《[^》\n]+》/g, "$1")
      .replace(/【(\d+)】/g, "［$1］");
  }

  root.ExamMarkup = { renderInline, renderBlocks, plainText };
})(typeof globalThis !== "undefined" ? globalThis : this);
