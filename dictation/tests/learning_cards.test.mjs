import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
/** Values crossing back from the VM realm carry that realm's prototypes. */
const plain = (value) => JSON.parse(JSON.stringify(value));
const WEB = path.join(HERE, "..", "src", "web");
const SYNC = fs.readFileSync(path.join(WEB, "learning_data.js"), "utf8");
const CARDS = fs.readFileSync(path.join(WEB, "learning_cards.js"), "utf8");

/* The shared adapter is what makes one card one card across three pages (LEX-12).
 * Its collaborators are stubbed: BroadcastChannel and IndexedDB are browser APIs, and
 * the behaviour under test is the merging, the announcing and the migration. */
function load({ withChannel = true, cards = [], failPut = false } = {}) {
  const posted = [];
  const channels = [];
  const values = new Map();
  const store = new Map(cards.map((card) => [card.id, card]));

  class FakeChannel {
    constructor(name) { this.name = name; this.closed = false; channels.push(this); }
    postMessage(message) { posted.push(message); }
    close() { this.closed = true; }
  }

  const listeners = new Map();
  const context = vm.createContext({
    console, Date, Math, setTimeout, clearTimeout, JSON, Set, Map, Array, Object,
    Number, String, Boolean, Error, Promise, CustomEvent: class { constructor(t, o) { this.type = t; Object.assign(this, o); } },
    BroadcastChannel: withChannel ? FakeChannel : undefined,
    localStorage: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, String(value)),
      removeItem: (key) => values.delete(key),
    },
    document: {
      visibilityState: "visible",
      addEventListener: (name, fn) => listeners.set(`doc:${name}`, fn),
    },
    LearningCardStore: {
      all: async () => [...store.values()],
      putMany: async (items) => {
        if (failPut) throw new Error("quota exceeded");
        items.forEach((item) => store.set(item.id, item));
      },
      writeRecords: async (records) => {
        records.forEach((record) => { if (record.remove) store.delete(record.id); });
      },
    },
  });
  context.window = { addEventListener: (name, fn) => listeners.set(`win:${name}`, fn), dispatchEvent: () => true };
  context.globalThis = context;
  vm.runInContext(`${SYNC}\n${CARDS}\n;globalThis.__cards = LearningCards; globalThis.__sync = LearningDataSync;`, context);
  return { cards: context.__cards, sync: context.__sync, posted, channels, values, store, listeners };
}

test("a change is announced to other tabs and to this page's own listeners", () => {
  const { cards, posted } = load();
  const seen = [];
  cards.subscribe((change) => seen.push(change));
  cards.announce({ entityType: "vocab", id: "v_1", version: 3, operationId: "op_9" });

  assert.equal(posted.length, 1);
  assert.deepEqual(
    { ...posted[0], at: undefined },
    { entityType: "vocab", id: "v_1", version: 3, operationId: "op_9", reason: "change", at: undefined },
  );
  // The page's own listeners are told directly, and told it was their own change: a
  // BroadcastChannel never delivers to the context that posted.
  assert.equal(seen.length, 1);
  assert.equal(seen[0].origin, "self");
});

test("one channel is opened for the page, not one per message", () => {
  const { cards, channels } = load();
  cards.subscribe(() => {});
  cards.announce({ id: "v_1" });
  cards.announce({ id: "v_2" });
  cards.announce({ id: "v_3" });
  // The previous code constructed a channel per message and closed none of them.
  assert.equal(channels.length, 1);
  assert.equal(channels[0].name, cards.channelName);
  assert.equal(channels[0].closed, false);
});

test("a browser without BroadcastChannel still delivers to this page", () => {
  const { cards, posted } = load({ withChannel: false });
  const seen = [];
  cards.subscribe((change) => seen.push(change));
  cards.announce({ id: "v_1" });
  assert.equal(posted.length, 0);
  assert.equal(seen.length, 1);
});

test("returning to the page triggers a compensating refresh", () => {
  const { cards, listeners } = load();
  const seen = [];
  cards.subscribe((change) => seen.push(change));
  listeners.get("win:pageshow")();
  listeners.get("doc:visibilitychange")();
  listeners.get("win:storage")({ key: "dictation-learning-outbox:v1" });
  // A frozen or discarded page misses channel messages entirely, so coming back re-checks.
  assert.equal(seen.filter((change) => change.reason === "resume").length, 3);
  listeners.get("win:storage")({ key: "unrelated-key" });
  assert.equal(seen.filter((change) => change.reason === "resume").length, 3);
});

test("a deleted card is not revived by a stale server snapshot", async () => {
  const { cards, sync, store } = load({
    cards: [{ id: "v_1", term: "残る", updatedAt: "2026-01-02T00:00:00Z" }],
  });
  sync.configure({ isOnline: () => false, sender: async () => ({ ok: true }) });
  await sync.mutate("DELETE", "./api/vocab/v_1", undefined, { entityType: "vocab", entityKey: "v_1" });

  const merged = await cards.merge([
    { id: "v_1", term: "残る", updatedAt: "2026-01-01T00:00:00Z" },
    { id: "v_2", term: "生きる", updatedAt: "2026-01-01T00:00:00Z" },
  ]);
  assert.deepEqual(plain(merged.map((card) => card.id)), ["v_2"]);
  // The row itself stays until the delete has been uploaded — removing it now would
  // destroy the only record of the intent — but nothing ever reads it back.
  assert.deepEqual(plain((await cards.localCards()).map((card) => card.id)), ["v_2"]);
});

test("once the delete is uploaded the local row is pruned", async () => {
  const { cards, sync, store } = load({
    cards: [{ id: "v_1", term: "残る", updatedAt: "2026-01-02T00:00:00Z" },
            { id: "v_2", term: "生きる", updatedAt: "2026-01-01T00:00:00Z" }],
  });
  sync.configure({ isOnline: () => true, sender: async () => ({ ok: true }) });
  await sync.mutate("DELETE", "./api/vocab/v_1", undefined, { entityType: "vocab", entityKey: "v_1" });
  assert.equal(sync.pendingCount(), 0);

  await cards.merge([{ id: "v_2", term: "生きる", updatedAt: "2026-01-01T00:00:00Z" }]);
  assert.equal(store.has("v_1"), false);
});

test("a card missing from the response is kept while anything is queued", async () => {
  const { cards, sync, store } = load({
    cards: [{ id: "local_1", term: "新しい", updatedAt: "2026-01-02T00:00:00Z" }],
  });
  sync.configure({ isOnline: () => false, sender: async () => ({ ok: true }) });
  await sync.mutate("POST", "./api/vocab", { id: "local_1" }, { entityType: "vocab", entityKey: "local_1" });

  await cards.merge([{ id: "v_2", term: "古い", updatedAt: "2026-01-01T00:00:00Z" }]);
  // The server has not seen local_1 yet; pruning it would delete the only copy.
  assert.equal(store.has("local_1"), true);
});

test("the newer of the two copies wins", async () => {
  const { cards } = load({ cards: [{ id: "v_1", term: "本地", updatedAt: "2026-02-01T00:00:00Z" }] });
  const merged = await cards.merge([{ id: "v_1", term: "服务端", updatedAt: "2026-01-01T00:00:00Z" }]);
  assert.equal(merged[0].term, "本地");
});

test("the entry note and the card note are different fields", () => {
  const { cards } = load();
  assert.equal(cards.noteFor({ note: "方向提示" }, { note: "条目笔记" }), "条目笔记");
  assert.equal(cards.noteFor({ note: "方向提示" }, {}), "方向提示");
  assert.equal(cards.noteFor({}, {}), "");
});

test("legacy localStorage cards move into the durable store and the old key goes", async () => {
  const { cards, values, store } = load();
  values.set("dictation-vocab:v1", JSON.stringify([{ id: "v_old", term: "旧卡" }]));
  const result = await cards.migrateLegacyStorage();
  assert.equal(result.migrated, 1);
  assert.deepEqual(plain(result.kept), []);
  assert.equal(store.has("v_old"), true);
  assert.equal(values.has("dictation-vocab:v1"), false);
});

test("a failed migration keeps the old copy rather than losing it", async () => {
  const { cards, values } = load({ failPut: true });
  values.set("dictation-vocab:v1", JSON.stringify([{ id: "v_old", term: "旧卡" }]));
  const result = await cards.migrateLegacyStorage();
  assert.equal(result.migrated, 0);
  assert.deepEqual(plain(result.kept), ["dictation-vocab:v1"]);
  // Quota exhausted or the upgrade blocked: the only copy stays where it was.
  assert.equal(values.has("dictation-vocab:v1"), true);
});
