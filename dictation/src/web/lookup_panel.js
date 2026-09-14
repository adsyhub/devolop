/* Shared selection lookup.
 *
 * Two things changed here (LEX-19, §11.2). The panel used to decide whether looking a
 * word up was allowed by matching `location.pathname` and reading a global called
 * `state` that belongs to another file — so it broke whenever a host renamed anything,
 * and it could only guess what a selection was part of. Hosts now register an adapter
 * that answers both questions for themselves. And the saved context was `page`, `text`
 * and `selection`, which cannot locate the sentence again; it now carries the host's own
 * identifiers and the selection offsets.
 *
 * Looking a word up is always an explicit act: selecting text offers the action, it
 * never fires the query.
 */
(function () {
  "use strict";
  if (document.querySelector("[data-lex-lookup]")) return;

  const panel = document.createElement("aside");
  panel.dataset.lexLookup = "true";
  panel.className = "lex-lookup-panel";
  panel.hidden = true;
  panel.setAttribute("aria-label", "划词查询");
  panel.setAttribute("aria-live", "polite");
  document.body.append(panel);

  const create = (tag, text) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    return node;
  };

  let selection = "";
  let hostContext = {};
  let savedToken = "";
  let generation = 0;
  let restoreFocus = null;

  /* ---- host adapter ---------------------------------------------------- */

  const DEFAULT_HOST = {
    /** Whether looking a word up is appropriate right now. */
    canLookup: () => !document.querySelector("dialog[open]"),
    /** What the current selection is part of, in the host's own identifiers. */
    getSelectionContext: () => ({}),
  };

  function host() {
    const registered = window.LexLookupHost;
    if (!registered || typeof registered !== "object") return DEFAULT_HOST;
    return {
      canLookup: typeof registered.canLookup === "function" ? registered.canLookup : DEFAULT_HOST.canLookup,
      getSelectionContext: typeof registered.getSelectionContext === "function"
        ? registered.getSelectionContext : DEFAULT_HOST.getSelectionContext,
    };
  }

  function permitted() {
    try {
      // A host that throws is treated as "not now": guessing yes would put a lookup
      // panel over a timed exam.
      return Boolean(host().canLookup()) && !document.querySelector("dialog[open]");
    } catch {
      return false;
    }
  }

  /* ---- transport -------------------------------------------------------- */

  async function request(path, body) {
    if (!savedToken) {
      const bootstrap = await fetch("./api/session/bootstrap");
      if (!bootstrap.ok) throw new Error("本地服务不可用。");
      savedToken = (await bootstrap.json()).token;
    }
    const response = await fetch(path, {
      method: body ? "PUT" : "GET",
      headers: {
        "X-Dictation-Token": savedToken,
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      if (response.status === 403) savedToken = "";
      throw new Error("查询未完成，请重试。");
    }
    return response.json();
  }

  function close() {
    // Abandon anything in flight, so a late response cannot repopulate a closed panel.
    generation += 1;
    panel.hidden = true;
    const target = restoreFocus;
    restoreFocus = null;
    if (target && document.contains(target)) {
      try { target.focus(); } catch { /* the element may no longer be focusable */ }
    }
  }

  function action(label, fn) {
    const button = create("button", label);
    button.type = "button";
    button.className = "quiet-button";
    button.setAttribute("aria-label", label);
    button.addEventListener("click", async () => {
      button.disabled = true;
      try { await fn(); } catch (error) { panel.append(create("p", error.message)); }
      finally { button.disabled = false; }
    });
    return button;
  }

  /* ---- rendering -------------------------------------------------------- */

  function detailHref(item) {
    const returnTarget = location.href || (location.pathname + (location.hash || ""));
    const ret = "?return=" + encodeURIComponent(returnTarget);
    if (item.sourceRef.startsWith("dict:")) {
      const reference = item.sourceRef.slice("dict:jmdict#".length);
      return "./lexicon" + ret + "#/dictionary/" + encodeURIComponent(reference);
    }
    if (item.sourceRef.startsWith("user:")) return "./lexicon" + ret + "#/personal/" + encodeURIComponent(item.sourceRef);
    return "./lexicon" + ret + "#/entry/" + encodeURIComponent(item.packSlug) + "/" + encodeURIComponent(item.id);
  }

  function readingPicker(item) {
    /* A dictionary hit reports which readings its matched spelling actually allows, so
     * the favourite records the learner's choice instead of the record's first reading. */
    const candidates = item.readingCandidates || (item.reading ? [item.reading] : []);
    if (candidates.length <= 1) return { node: null, value: () => candidates[0] || "" };
    const select = create("select");
    select.setAttribute("aria-label", "读音");
    candidates.forEach((reading) => {
      const option = create("option", reading);
      option.value = reading;
      select.append(option);
    });
    return { node: select, value: () => select.value };
  }

  async function lookup() {
    const serial = ++generation;
    const text = selection;
    const context = hostContext;
    const result = await request("./api/lexicon/search?q=" + encodeURIComponent(text) + "&limit=5");
    if (serial !== generation) return;

    panel.replaceChildren(create("strong", text), action("关闭", close));
    for (const item of result.results || []) {
      const row = create("div");
      row.className = "lex-lookup-result";
      row.append(create("b", item.headword));
      const reading = readingPicker(item);
      row.append(create("p", (reading.value() ? reading.value() + " · " : "")
        + (item.gloss?.zh || item.gloss?.en || "暂无释义")));
      // The chain that got from the typed form to this entry, so a match through
      // deinflection is visible rather than looking like a coincidence.
      if (item.chain?.length) row.append(create("p", "活用还原：" + item.chain.join(" → ")));
      if (item.senseCount > 1) row.append(create("p", `${item.senseCount} 个义项 · 在详情页选择后收藏更准确`));
      if (reading.node) row.append(reading.node);

      const link = create("a", "查看详情");
      link.href = detailHref(item);
      link.target = "_blank";
      link.rel = "noopener";
      row.append(link, action("收藏并保留原句", async () => {
        await request("./api/lexicon/user-entries", {
          sourceRef: item.sourceRef,
          headword: item.headword,
          reading: reading.value(),
          gloss: item.gloss || {},
          kind: item.kind || "word",
          // No level evidence from a lookup, so nothing is claimed (§11.2.6).
          level: item.level || "",
          starred: true,
          context: { ...context, selection: text },
        });
        row.append(create("span", " 已收藏"));
      }));
      panel.append(row);
    }
    if (!(result.results || []).length) {
      panel.append(create("p", "当前来源未找到结果。可在词库中添加个人条目。"));
    }
    const sources = result.availableSources || [];
    if (sources.length) panel.append(create("p", "已查询：" + sources.join("、")));
  }

  /* ---- selection -------------------------------------------------------- */

  function offer() {
    if (!permitted()) return;
    const current = window.getSelection();
    const text = current?.toString().trim();
    if (!text || text.length > 120 || panel.contains(current.anchorNode)) return;
    const parent = current.anchorNode?.parentElement;
    if (parent?.closest("input,textarea,select,button")) return;

    selection = text;
    const block = parent?.closest("p,li,article") || parent;
    let range = null;
    try { range = current.rangeCount ? current.getRangeAt(0) : null; } catch { range = null; }
    let asked = {};
    try { asked = host().getSelectionContext({ text, node: parent, range }) || {}; } catch { asked = {}; }
    hostContext = {
      // The host's own identifiers are what can find this sentence again; the page and
      // hash are kept only so older saved contexts stay comparable.
      ...asked,
      text: asked.text || block?.textContent?.trim().slice(0, 2000) || text,
      startOffset: Number.isInteger(asked.startOffset) ? asked.startOffset
        : (range && block ? offsetWithin(block, range) : null),
      endOffset: Number.isInteger(asked.endOffset) ? asked.endOffset
        : (range && block ? offsetWithin(block, range) + text.length : null),
      page: location.pathname + location.hash,
      capturedAt: new Date().toISOString(),
    };
    restoreFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    panel.replaceChildren(create("strong", text), action("查询词汇 / 语法", lookup), action("关闭", close));
    panel.hidden = false;
  }

  function offsetWithin(block, range) {
    try {
      const probe = range.cloneRange();
      probe.selectNodeContents(block);
      probe.setEnd(range.startContainer, range.startOffset);
      return probe.toString().length;
    } catch {
      return 0;
    }
  }

  document.addEventListener("mouseup", () => setTimeout(offer, 20));
  document.addEventListener("touchend", () => setTimeout(offer, 120));
  // Keyboard users never fire mouseup or touchend. Selecting with the keyboard and
  // pressing the shortcut is the same explicit act.
  document.addEventListener("keyup", (event) => {
    if (event.shiftKey && event.key.startsWith("Arrow")) setTimeout(offer, 20);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") { close(); return; }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      const current = window.getSelection()?.toString().trim();
      if (current) { event.preventDefault(); offer(); }
    }
  });
  window.addEventListener("hashchange", close);
})();
