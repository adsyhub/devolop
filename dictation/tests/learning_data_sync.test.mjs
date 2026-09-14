import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SOURCE = fs.readFileSync(path.join(HERE, "..", "src", "web", "learning_data.js"), "utf8");

function loadSync() {
  const values = new Map();
  const context = vm.createContext({
    console,
    Date,
    Math,
    setTimeout,
    clearTimeout,
    localStorage: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, String(value)),
      removeItem: (key) => values.delete(key),
    },
  });
  vm.runInContext(`${SOURCE}\n;globalThis.__learningSync = LearningDataSync;`, context);
  return { sync: context.__learningSync, values };
}

test("offline mutations survive and flush in dependency order", async () => {
  const { sync } = loadSync();
  let isOnline = false;
  const sent = [];
  sync.configure({
    isOnline: () => isOnline,
    sender: async (operation) => {
      sent.push(`${operation.method} ${operation.path}`);
      return { ok: true };
    },
  });

  await sync.mutate("POST", "./api/vocab", { id: "local_1", term: "語" }, {
    entityType: "vocab", entityKey: "local_1",
  });
  await sync.mutate("PATCH", "./api/vocab/local_1", { meaning: "word" }, {
    entityType: "vocab", entityKey: "local_1",
  });
  assert.equal(sync.pendingCount(), 2);

  isOnline = true;
  const result = await sync.flush();
  assert.deepEqual(sent, ["POST ./api/vocab", "PATCH ./api/vocab/local_1"]);
  assert.equal(result.pending, 0);
});

test("a failed head operation is retained and blocks dependent writes", async () => {
  const { sync } = loadSync();
  let calls = 0;
  sync.configure({
    isOnline: () => false,
    sender: async () => {
      calls += 1;
      throw new Error("offline");
    },
  });
  await sync.mutate("POST", "./api/vocab", { id: "local_2" }, {
    entityType: "vocab", entityKey: "local_2",
  });
  await sync.mutate("PATCH", "./api/vocab/local_2", { meaning: "x" }, {
    entityType: "vocab", entityKey: "local_2",
  });

  sync.configure({ isOnline: () => true, sender: async () => { calls += 1; throw new Error("down"); } });
  const result = await sync.flush();
  assert.equal(calls, 1);
  assert.equal(result.pending, 2);
});

test("delete tombstones prevent stale server snapshots from resurrecting data", async () => {
  const { sync } = loadSync();
  sync.configure({ isOnline: () => false, sender: async () => ({ ok: true }) });
  await sync.mutate("DELETE", "./api/vocab/v_1", undefined, {
    entityType: "vocab", entityKey: "v_1",
  });

  const merged = sync.mergeItems([], [
    { id: "v_1", term: "stale", updatedAt: "2026-01-01T00:00:00Z" },
    { id: "v_2", term: "keep", updatedAt: "2026-01-01T00:00:00Z" },
  ], { entityType: "vocab", keyOf: (item) => item.id });
  assert.deepEqual(JSON.parse(JSON.stringify(merged)), [
    { id: "v_2", term: "keep", updatedAt: "2026-01-01T00:00:00Z" },
  ]);
});


test("an operation is durable before it is sent, and cleared only on a receipt", async () => {
  const { sync, values } = loadSync();
  let seenDuringSend = null;
  sync.configure({
    isOnline: () => true,
    sender: async () => {
      // The point of persist-before-send: if the process died here, or the response
      // were lost, the replay would carry this same id rather than a fresh one.
      seenDuringSend = JSON.parse(values.get(sync.storageKeys.outbox) || "[]");
      return { ok: true };
    },
  });

  const { operation, queued } = await sync.mutate("POST", "./api/vocab/review", { grade: "good" }, {
    entityType: "vocab-review", entityKey: "v_1",
  });
  assert.equal(queued, false);
  assert.equal(seenDuringSend.length, 1);
  assert.equal(seenDuringSend[0].id, operation.id);
  assert.equal(sync.pendingCount(), 0);
});

test("a retryable failure keeps the operation; a business error archives it", async () => {
  const { sync } = loadSync();
  let status = 503;
  sync.configure({
    isOnline: () => true,
    sender: async () => { const error = new Error("nope"); error.status = status; throw error; },
  });

  await sync.mutate("POST", "./api/vocab/review", { grade: "good" }, {
    entityType: "vocab-review", entityKey: "v_1",
  });
  assert.equal(sync.pendingCount(), 1, "a 503 is worth retrying");

  status = 409;
  await assert.rejects(sync.mutate("POST", "./api/vocab/review", { grade: "good" }, {
    entityType: "vocab-review", entityKey: "v_2",
  }));
  // The server has decided: replaying cannot change the answer, so it leaves the queue
  // for the learner to deal with instead of being reported as synced.
  assert.equal(sync.pendingCount(), 1);
  const archived = sync.rejectedOperations();
  assert.equal(archived.length, 1);
  assert.equal(archived[0].httpStatus, 409);
  assert.equal(archived[0].entityKey, "v_2");
});

test("a rejected operation does not stall the ones behind it", async () => {
  const { sync } = loadSync();
  sync.configure({ isOnline: () => false, sender: async () => ({ ok: true }) });
  await sync.mutate("POST", "./api/vocab", { id: "local_a" }, { entityType: "vocab", entityKey: "local_a" });
  await sync.mutate("POST", "./api/vocab", { id: "local_b" }, { entityType: "vocab", entityKey: "local_b" });
  assert.equal(sync.pendingCount(), 2);

  const sent = [];
  sync.configure({
    isOnline: () => true,
    sender: async (operation) => {
      if (operation.entityKey === "local_a") { const e = new Error("gone"); e.status = 422; throw e; }
      sent.push(operation.entityKey);
      return { ok: true };
    },
  });
  const result = await sync.flush();
  assert.deepEqual(sent, ["local_b"]);
  assert.equal(result.pending, 0);
  assert.equal(result.rejected, 1);
  assert.equal(sync.rejectedOperations()[0].entityKey, "local_a");
  sync.clearRejected();
  assert.equal(sync.rejectedOperations().length, 0);
});
