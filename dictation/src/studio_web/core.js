"use strict";

/**
 * What both workbench pages need before anything else: a session, a request
 * helper that carries it, and the three DOM primitives every panel uses.
 *
 * These five functions existed twice — once in studio.js and once in editor.js.
 * `api()` was the same request helper written out twice; `fillSelect()` was the
 * same *name* over two different behaviours, which is worse, because a panel
 * moved between the pages would silently change what an empty list looks like.
 */
const StudioCore = (() => {
  let token = "";
  let _sessionPromise = null;
  let _resolveSession = null;
  const sessionReady = new Promise((resolve) => { _resolveSession = resolve; });
  const cache = new Map();

  /** Claim the localhost session token the server hands out on first load. */
  async function session() {
    if (!_sessionPromise) {
      _sessionPromise = (async () => {
        const response = await fetch("/api/session/bootstrap", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        token = payload.token;
        if (_resolveSession) _resolveSession(token);
        return payload;
      })();
    }
    return _sessionPromise;
  }

  async function fetchBlob(path, options = {}) {
    if (!token && _sessionPromise) {
      try { await _sessionPromise; } catch (_) {}
    }
    const headers = Object.assign({}, options.headers || {});
    if (token) headers["X-Dictation-Token"] = token;
    const response = await fetch(path, Object.assign({}, options, { headers, cache: "no-store" }));
    if (!response.ok) {
      const type = response.headers.get("Content-Type") || "";
      const payload = type.includes("application/json") ? await response.json() : null;
      throw new Error((payload && payload.error) || `请求资源失败（HTTP ${response.status}）`);
    }
    return response.blob();
  }

  async function api(path, options = {}) {
    if (!token && _sessionPromise) {
      try { await _sessionPromise; } catch (_) {}
    }
    const headers = Object.assign({}, options.headers || {});
    if (token) headers["X-Dictation-Token"] = token;
    const response = await fetch(path, Object.assign({}, options, { headers, cache: "no-store" }));
    const type = response.headers.get("Content-Type") || "";
    const payload = type.includes("application/json") ? await response.json() : null;
    if (!response.ok) throw new Error((payload && payload.error) || `请求失败（HTTP ${response.status}）`);
    return payload;
  }

  /** POST JSON — the shape of nearly every write in this workbench. */
  function post(path, body) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  /**
   * One element by id, looked up once.
   *
   * Returns null for an absent element rather than throwing: panels are allowed
   * to be missing from a page (the GPU pill is on one page and the GPU cards on
   * the other), and `tests/studio_web.test.mjs` is what catches a genuine typo.
   */
  function el(id) {
    if (!cache.has(id)) cache.set(id, document.getElementById(id));
    return cache.get(id);
  }

  function text(tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = content;
    return node;
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[char]));
  }

  /**
   * Replace a <select>'s options.
   *
   * `placeholder` is opt-in because the two original copies disagreed about it:
   * the model pickers want "当前没有可用模型" when nothing is selectable, while a
   * sentence list wants to stay empty rather than claim a model is missing.
   */
  function fillSelect(select, options, selected = "", { placeholder = "" } = {}) {
    if (!select) return;
    select.replaceChildren();
    let list = options;
    if (placeholder && (!list.length || !list.some((option) => !option.disabled))) {
      list = [{ value: "", label: placeholder, disabled: true }].concat(list);
    }
    const selectable = list.filter((option) => !option.disabled);
    const chosen = selectable.some((option) => option.value === selected)
      ? selected
      : ((selectable[0] || {}).value || "");
    for (const option of list) {
      const node = document.createElement("option");
      node.value = option.value;
      node.textContent = option.label;
      node.disabled = Boolean(option.disabled);
      if (option.value === chosen) node.selected = true;
      select.append(node);
    }
  }

  /**
   * Write text into an element that may not exist on this page.
   *
   * Panels are split across pages now, so a shared module routinely runs where
   * half its elements are absent. Returning quietly is right here — the guard
   * against a genuine typo is `tests/studio_web.test.mjs`, not a runtime crash.
   */
  function setText(id, value) {
    const node = el(id);
    if (node) node.textContent = value;
    return Boolean(node);
  }

  /** Text of an error box that hides itself when there is nothing to say. */
  function showMessage(id, message) {
    const box = el(id);
    if (!box) return;
    box.hidden = !message;
    box.textContent = message || "";
  }

  const describeError = (error) => String((error && error.message) || error);

  return { session, sessionReady, fetchBlob, api, post, el, text, setText, escapeHtml, fillSelect, showMessage, describeError,
    token: () => token };
})();

if (typeof module !== "undefined" && module.exports) module.exports = StudioCore;
if (typeof window !== "undefined") window.StudioCore = StudioCore;
