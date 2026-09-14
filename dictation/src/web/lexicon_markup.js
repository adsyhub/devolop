/* Lexicon entry text → DOM nodes.
 *
 * Split out of lexicon.js so it can be tested against a minimal DOM shim
 * (tests/lexicon_markup.test.mjs), the way exam_markup.js is. It is also the one
 * place where a bug is a security bug rather than a cosmetic one, so it is worth
 * isolating.
 *
 * The rule this file exists to keep: entry text is a transcription of a scanned
 * textbook page, produced by a model reading an image. It is *data*. It is never
 * assigned to innerHTML, never passed to insertAdjacentHTML, and never used to
 * build a selector. Everything below constructs elements and text nodes, so a
 * stray "<script>" in a transcription renders as those nine characters.
 *
 * Recognised markup (see lexicon_schema.py for the authoritative description):
 *   ｜漢字《かんじ》     printed furigana → <ruby>漢字<rt>かんじ</rt></ruby>
 *                    (the marker is the FULL-WIDTH bar U+FF5C, as in exam_markup.js,
 *                     so it cannot collide with anything ASCII)
 *   <u>…</u>         an underlined span
 *   【V辞書形】        a connection placeholder printed inside a pattern
 *   ⟦…⟧              the span a cloze card blanks out
 *
 * The two lexicon-only conventions are why this is a separate file from
 * exam_markup.js rather than a flag on it: 【…】 means a boxed *question number* in a
 * exam paper and a *grammatical slot* here, and one renderer that had to know which
 * document it was looking at would be one renderer that could get it wrong.
 */

(function attach(root) {
  "use strict";

  // Ruby opens with the FULL-WIDTH bar U+FF5C, not ASCII "|", matching the question
  // bank's convention (PROJECT_STRUCTURE maintenance rule 17).
  const INLINE_TOKEN = /｜([^｜《》\n]+)《([^》\n]+)》|【([^【】\n]+)】|⟦([^⟦⟧\n]*)⟧/g;

  function doc(node) {
    return (node && node.ownerDocument) || root.document;
  }

  function renderTokens(text, target, options) {
    const d = doc(target);
    const blankMode = (options && options.cloze) || "show";
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
        const slot = d.createElement("span");
        slot.className = "conn-slot";
        slot.textContent = match[3];
        target.appendChild(slot);
      } else {
        target.appendChild(blank(d, match[4], blankMode));
      }
      last = INLINE_TOKEN.lastIndex;
    }
    if (last < text.length) target.appendChild(d.createTextNode(text.slice(last)));
  }

  /* A cloze blank has two states and they are the same element, because the card
   * flips in place: hiding the answer by *removing* it would leave the sentence a
   * different width, and the learner would read the gap's size as a hint. */
  function blank(d, answer, mode) {
    const span = d.createElement("span");
    span.className = mode === "hide" ? "cloze-blank" : "cloze-answer";
    span.textContent = mode === "hide" ? "＿".repeat(Math.max(2, [...String(answer)].length)) : String(answer);
    return span;
  }

  function renderInline(text, target, options) {
    const value = String(text == null ? "" : text);
    // Split on complete <u>…</u> pairs only. An unbalanced "<u>" therefore falls
    // through to renderTokens and becomes literal text — which is what a truncated
    // transcription should look like, not an element that swallows the rest.
    for (const segment of value.split(/(<u>[\s\S]*?<\/u>)/)) {
      if (!segment) continue;
      const underlined = /^<u>([\s\S]*?)<\/u>$/.exec(segment);
      if (underlined) {
        const u = doc(target).createElement("u");
        renderTokens(underlined[1], u, options);
        target.appendChild(u);
      } else {
        renderTokens(segment, target, options);
      }
    }
    return target;
  }

  function renderBlocks(text, container, options) {
    const d = doc(container);
    for (const line of String(text == null ? "" : text).split("\n")) {
      if (!line.trim()) continue;
      const paragraph = d.createElement("p");
      renderInline(line, paragraph, options);
      container.appendChild(paragraph);
    }
    return container;
  }

  /* One connection row: "イAくて", "ナAで", "Vたくて".
   *
   * The base marker is rendered as its own element rather than as part of the string
   * so the two halves can be styled apart — the learner is looking for "which word
   * class does this attach to", and that is the first two characters. */
  function renderConnection(connection, target) {
    const d = doc(target);
    const display = String((connection && connection.display) || "");
    const form = String((connection && connection.form) || "");
    const base = form && display.endsWith(form) ? display.slice(0, display.length - form.length) : display;

    const row = d.createElement("span");
    row.className = "conn";
    const baseNode = d.createElement("span");
    baseNode.className = "conn-base";
    baseNode.textContent = base;
    row.appendChild(baseNode);
    if (display.length > base.length) {
      const tail = d.createElement("span");
      tail.className = "conn-form";
      tail.textContent = display.slice(base.length);
      row.appendChild(tail);
    }
    target.appendChild(row);
    return row;
  }

  /** Markup stripped back to readable text, for titles and one-line summaries. */
  function plainText(markup) {
    return String(markup == null ? "" : markup)
      .replace(/<\/?u>/g, "")
      .replace(/｜([^｜《》\n]+)《[^》\n]+》/g, "$1")
      .replace(/【([^【】\n]+)】/g, "［$1］")
      .replace(/⟦([^⟦⟧\n]*)⟧/g, "$1");
  }

  root.LexiconMarkup = { renderInline, renderBlocks, renderConnection, plainText };
})(typeof globalThis !== "undefined" ? globalThis : this);
