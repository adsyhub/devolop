"use strict";

/* IndexedDB cache for review-card snapshots. Content-heavy cardPayload objects
 * intentionally do not live in localStorage; only the small mutation outbox does. */
const LearningCardStore = (() => {
  const DB_NAME = "dictation-learning";
  const STORE = "review-cards";
  let dbPromise;

  function open() {
    if (!globalThis.indexedDB) return Promise.reject(new Error("当前浏览器不支持离线卡片仓库"));
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 2);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE)) {
          const store = db.createObjectStore(STORE, { keyPath: "id" });
          store.createIndex("nextReviewAt", "nextReviewAt");
          store.createIndex("entryKind", "entryKind");
        }
        for (const name of ["lex-sessions", "lex-operations", "lex-meta"]) {
          if (!db.objectStoreNames.contains(name)) db.createObjectStore(name, { keyPath: "id" });
        }
      };
      request.onsuccess = () => {
        request.result.onversionchange = () => { request.result.close(); dbPromise = null; };
        resolve(request.result);
      };
      request.onerror = () => { dbPromise = null; reject(request.error || new Error("无法打开离线卡片仓库")); };
      request.onblocked = () => { dbPromise = null; reject(new Error("请关闭旧版本学习页面后重试。")); };
    });
    return dbPromise;
  }

  async function transact(mode, run) {
    const db = await open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      const store = tx.objectStore(STORE);
      let value;
      try { value = run(store); } catch (error) { reject(error); return; }
      tx.oncomplete = () => resolve(value);
      tx.onerror = () => reject(tx.error || new Error("离线卡片写入失败；请释放浏览器存储空间"));
      tx.onabort = () => reject(tx.error || new Error("离线卡片事务已回滚"));
    });
  }

  function putMany(cards) {
    return transact("readwrite", (store) => (cards || []).forEach((card) => store.put(card)));
  }

  function put(card) { return transact("readwrite", (store) => store.put(card)); }

  async function all() {
    const db = await open();
    return new Promise((resolve, reject) => {
      const request = db.transaction(STORE, "readonly").objectStore(STORE).getAll();
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  async function due({ scope = "all", ids = null } = {}) {
    const now = Date.now();
    const allowed = ids ? new Set(ids) : null;
    return (await all()).filter((card) => {
      const when = card.nextReviewAt ? new Date(card.nextReviewAt).getTime() : 0;
      return !card.reviewSuspended && when <= now
        && (scope === "all" || card.entryKind === scope)
        && (!allowed || allowed.has(card.id));
    }).sort((a, b) => String(a.nextReviewAt || "").localeCompare(String(b.nextReviewAt || "")));
  }

  async function getRecord(name, id) {
    const db = await open();
    return new Promise((resolve, reject) => {
      const r = db.transaction(name).objectStore(name).get(id);
      r.onsuccess = () => resolve(r.result || null); r.onerror = () => reject(r.error);
    });
  }
  async function listRecords(name) {
    const db = await open();
    return new Promise((resolve, reject) => {
      const r = db.transaction(name).objectStore(name).getAll();
      r.onsuccess = () => resolve(r.result || []); r.onerror = () => reject(r.error);
    });
  }
  async function writeRecords(records) {
    const db = await open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction([...new Set(records.map(r => r.store))], "readwrite");
      records.forEach(r => r.remove ? tx.objectStore(r.store).delete(r.id) : tx.objectStore(r.store).put(r.value));
      tx.oncomplete = () => resolve(); tx.onerror = tx.onabort = () => reject(tx.error || new Error("保存失败，原学习记录已保留。"));
    });
  }
  const saveSession = session => writeRecords([{ store: "lex-sessions", value: session }]);
  const saveOperation = (session, operation) => writeRecords([
    { store: "lex-sessions", value: session }, { store: "lex-operations", value: operation },
  ]);
  return { all, due, open, put, putMany, getRecord, listRecords, writeRecords, saveSession, saveOperation };
})();
