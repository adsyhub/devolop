"use strict";

/* Durable client-side synchronization for the learner's personal data.
 *
 * The player is allowed to run without the Python service. Mutations made in
 * that state must therefore survive a reload and be replayed when the service
 * comes back. The queue is deliberately transport-agnostic: app.js supplies the
 * authenticated request function after it has obtained its session token.
 *
 * Operations are kept in creation order. Repeated updates/deletes to the same
 * entity are coalesced where doing so is safe, while creates stay ahead of the
 * later update/delete that refers to their client-generated id. Tombstones keep
 * a stale server snapshot from resurrecting something deleted while offline.
 */

const LearningDataSync = (() => {
  const OUTBOX_KEY = "dictation-learning-outbox:v1";
  const TOMBSTONE_KEY = "dictation-learning-tombstones:v1";
  const REJECTED_KEY = "dictation-learning-rejected:v1";
  const MAX_ATTEMPTS = 25;
  // A business error is an answer, not a transport failure: replaying it can only fail
  // again, so it leaves the queue and waits for the learner instead of blocking the
  // operations behind it. 408/429 are explicitly retryable (§8.1).
  const RETRYABLE_CLIENT_STATUSES = new Set([408, 429]);

  function isRejection(status) {
    const code = Number(status);
    return code >= 400 && code < 500 && !RETRYABLE_CLIENT_STATUSES.has(code);
  }

  let send = null;
  let online = () => false;
  let flushing = null;
  const listeners = new Set();

  function configure({ sender, isOnline }) {
    send = typeof sender === "function" ? sender : null;
    online = typeof isOnline === "function" ? isOnline : (() => false);
  }

  function readJson(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key) || "null");
      return value === null ? fallback : value;
    } catch {
      return fallback;
    }
  }

  function writeJson(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  }

  function readOutbox() {
    const value = readJson(OUTBOX_KEY, []);
    return Array.isArray(value) ? value.filter(validOperation) : [];
  }

  function readRejected() {
    const value = readJson(REJECTED_KEY, []);
    return Array.isArray(value) ? value : [];
  }

  function reject(operation, error) {
    const archive = readRejected();
    archive.push({
      ...operation,
      status: "rejected",
      httpStatus: Number(error?.status) || 0,
      lastError: String(error?.message || error || "rejected"),
      rejectedAt: new Date().toISOString(),
    });
    writeJson(REJECTED_KEY, archive.slice(-200));
  }

  function dequeue(id) {
    const queue = readOutbox().filter((item) => item.id !== id);
    writeJson(OUTBOX_KEY, queue);
    notify();
  }

  function readTombstones() {
    const value = readJson(TOMBSTONE_KEY, {});
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  }

  function validOperation(operation) {
    return Boolean(
      operation
      && typeof operation === "object"
      && operation.id
      && operation.method
      && operation.path,
    );
  }

  function operationId() {
    if (globalThis.crypto?.randomUUID) return `op_${globalThis.crypto.randomUUID()}`;
    return `op_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`;
  }

  function notify() {
    const pending = readOutbox().length;
    listeners.forEach((listener) => {
      try { listener(pending); } catch { /* one badge must not break syncing */ }
    });
  }

  function subscribe(listener) {
    if (typeof listener !== "function") return () => {};
    listeners.add(listener);
    listener(readOutbox().length);
    return () => listeners.delete(listener);
  }

  function tombstoneId(entityType, entityKey) {
    return entityType && entityKey ? `${entityType}:${entityKey}` : "";
  }

  function markDeleted(entityType, entityKey, deletedAt = new Date().toISOString()) {
    const key = tombstoneId(entityType, entityKey);
    if (!key) return;
    const tombstones = readTombstones();
    tombstones[key] = deletedAt;
    writeJson(TOMBSTONE_KEY, tombstones);
  }

  function clearDeleted(entityType, entityKey) {
    const key = tombstoneId(entityType, entityKey);
    if (!key) return;
    const tombstones = readTombstones();
    if (!(key in tombstones)) return;
    delete tombstones[key];
    writeJson(TOMBSTONE_KEY, tombstones);
  }

  function isDeleted(entityType, entityKey, itemUpdatedAt = "") {
    const deletedAt = readTombstones()[tombstoneId(entityType, entityKey)] || "";
    return Boolean(deletedAt && (!itemUpdatedAt || deletedAt >= itemUpdatedAt));
  }

  function enqueue(operation) {
    const queue = readOutbox();
    const method = String(operation.method || "POST").toUpperCase();
    const entityType = String(operation.entityType || "");
    const entityKey = String(operation.entityKey || "");

    // The newest update/delete supersedes an older mutation for the same entity,
    // but never remove its create: a later PATCH still needs the server row first.
    if (entityType && entityKey && method !== "POST") {
      for (let index = queue.length - 1; index >= 0; index -= 1) {
        const queued = queue[index];
        if (queued.entityType !== entityType || queued.entityKey !== entityKey) continue;
        if (String(queued.method).toUpperCase() === "POST") break;
        queue.splice(index, 1);
      }
    }

    queue.push({
      id: operation.id || operationId(),
      method,
      path: String(operation.path),
      body: operation.body === undefined ? null : operation.body,
      entityType,
      entityKey,
      createdAt: operation.createdAt || new Date().toISOString(),
      attempts: Number(operation.attempts || 0),
      lastError: "",
    });
    writeJson(OUTBOX_KEY, queue);
    notify();
    return queue[queue.length - 1];
  }

  async function mutate(method, path, body, options = {}) {
    const operation = {
      id: operationId(),
      method: String(method || "POST").toUpperCase(),
      path,
      body,
      entityType: options.entityType || "",
      entityKey: options.entityKey || "",
      createdAt: new Date().toISOString(),
    };

    if (operation.method === "DELETE") {
      markDeleted(operation.entityType, operation.entityKey, operation.createdAt);
    } else if (options.clearTombstone !== false) {
      clearDeleted(operation.entityType, operation.entityKey);
    }

    // Persist before sending. If the service applies the write but the response is
    // lost, the next flush replays this same operation id and the server recognises
    // it as a duplicate, instead of a second request being minted for it (LEX-05).
    const queued = enqueue(operation);

    if (send && online()) {
      try {
        const result = await send(queued);
        dequeue(queued.id);
        return { result, queued: false, operation: queued };
      } catch (error) {
        if (isRejection(error?.status)) {
          dequeue(queued.id);
          reject(queued, error);
          throw error;
        }
        queued.lastError = String(error?.message || error || "sync failed");
        writeJson(OUTBOX_KEY, readOutbox().map((item) => (item.id === queued.id ? queued : item)));
        notify();
      }
    }

    return { result: null, queued: true, operation: queued };
  }

  async function flush() {
    if (flushing) return flushing;
    flushing = flushNow().finally(() => { flushing = null; });
    return flushing;
  }

  async function flushNow() {
    if (!send || !online()) return { sent: 0, pending: readOutbox().length };
    let queue = readOutbox();
    let sent = 0;

    while (queue.length > 0 && online()) {
      const operation = queue[0];
      try {
        await send(operation);
        queue.shift();
        sent += 1;
        writeJson(OUTBOX_KEY, queue);
        notify();
      } catch (error) {
        if (isRejection(error?.status)) {
          // The server has decided; retrying cannot change the answer, and leaving it
          // at the head would stall every later operation for good.
          queue.shift();
          writeJson(OUTBOX_KEY, queue);
          reject(operation, error);
          notify();
          continue;
        }
        operation.attempts = Number(operation.attempts || 0) + 1;
        operation.lastError = String(error?.message || error || "sync failed");
        operation.lastAttemptAt = new Date().toISOString();
        // Preserve the failed operation at the head: later operations may depend
        // on it (notably an offline-created vocab row followed by an edit).
        queue[0] = operation;
        writeJson(OUTBOX_KEY, queue);
        notify();
        break;
      }
    }

    return {
      sent,
      pending: queue.length,
      rejected: readRejected().length,
      needsAttention: queue.some((item) => Number(item.attempts || 0) >= MAX_ATTEMPTS),
    };
  }

  function mergeItems(localItems, remoteItems, { entityType, keyOf }) {
    const merged = new Map();
    const add = (item, source) => {
      if (!item || typeof item !== "object") return;
      const key = String(keyOf(item) || "");
      if (!key || isDeleted(entityType, key, item.updatedAt || "")) return;
      const existing = merged.get(key);
      if (!existing) {
        merged.set(key, { item, source });
        return;
      }
      const existingAt = String(existing.item.updatedAt || existing.item.createdAt || "");
      const candidateAt = String(item.updatedAt || item.createdAt || "");
      if (candidateAt > existingAt || (candidateAt === existingAt && source === "local")) {
        merged.set(key, { item, source });
      }
    };
    (remoteItems || []).forEach((item) => add(item, "remote"));
    (localItems || []).forEach((item) => add(item, "local"));
    return [...merged.values()].map(({ item }) => item);
  }

  function pendingCount() {
    return readOutbox().length;
  }

  function rejectedOperations() {
    return readRejected();
  }

  function clearRejected(id = "") {
    writeJson(REJECTED_KEY, id ? readRejected().filter((item) => item.id !== id) : []);
  }

  return {
    configure,
    enqueue,
    flush,
    isDeleted,
    markDeleted,
    mergeItems,
    mutate,
    pendingCount,
    rejectedOperations,
    clearRejected,
    subscribe,
    storageKeys: { outbox: OUTBOX_KEY, tombstones: TOMBSTONE_KEY, rejected: REJECTED_KEY },
  };
})();
