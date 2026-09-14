"use strict";

/* Shared personal-card repository and change channel.
 *
 * Three pages read and write the learner's review cards — the listening workspace, the
 * personal centre and the lexicon workspace — and before this each kept its own copy:
 * the lexicon page cached cards in IndexedDB while the personal centre worked straight
 * off `/api/vocab`, so deleting a card in one place left it on screen in the other.
 * Changes were also announced on a BroadcastChannel that had no subscriber anywhere,
 * and a fresh channel was constructed for every message and never closed (LEX-12, §8.4).
 *
 * This module is the single adapter: one durable copy, one long-lived channel, and a
 * compensating refresh for the browsers and situations where the channel is not enough.
 *
 * Field ownership, made explicit because the two notes look like one field:
 *   - `lex_user_entries.note` is the learner's note about the ENTRY. Shared everywhere.
 *   - `vocab.note` is a memory hook for one review DIRECTION of that entry.
 * `noteFor()` reads them in that order so a page never shows one and save the other.
 */
const LearningCards = (() => {
  const CHANNEL = "dictation-learning-changes";
  const LEGACY_KEYS = ["dictation-vocab:v1", "dictation-learning-cards:v1"];

  const listeners = new Set();
  let channel = null;
  let started = false;

  function open() {
    if (channel || typeof BroadcastChannel === "undefined") return channel;
    try {
      channel = new BroadcastChannel(CHANNEL);
      // One receiver for the life of the page. Constructing a channel per message, as
      // the previous code did, means nothing is ever listening.
      channel.onmessage = (event) => deliver(event.data || {});
    } catch {
      channel = null;
    }
    return channel;
  }

  function deliver(change) {
    listeners.forEach((listener) => {
      try { listener(change); } catch { /* one page must not break the others */ }
    });
  }

  /** Subscribe to changes from this page and from every other tab. */
  function subscribe(listener) {
    if (typeof listener !== "function") return () => {};
    listeners.add(listener);
    start();
    return () => listeners.delete(listener);
  }

  function start() {
    if (started) return;
    started = true;
    open();
    // Channels are not delivered to a page that was frozen or discarded, and Safari
    // private windows have no channel at all, so returning to a page always re-checks.
    const compensate = () => deliver({ entityType: "*", reason: "resume" });
    window.addEventListener("storage", (event) => {
      if (event.key && event.key.startsWith("dictation-learning-")) compensate();
    });
    window.addEventListener("pageshow", compensate);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") compensate();
    });
  }

  /** Announce a change after it has been written locally. */
  function announce(change) {
    const message = {
      entityType: String(change.entityType || "vocab"),
      id: String(change.id || ""),
      version: Number(change.version || 0),
      operationId: String(change.operationId || ""),
      reason: String(change.reason || "change"),
      at: new Date().toISOString(),
    };
    open();
    try { channel?.postMessage(message); } catch { /* channel closed by the browser */ }
    // A page is not delivered its own BroadcastChannel messages, so this page's
    // listeners are told directly — and told that it was this page, so a subscriber
    // can skip a refresh for a change it already rendered.
    deliver({ ...message, origin: "self" });
    window.dispatchEvent(new CustomEvent("lexicon-data-changed", { detail: message }));
    return message;
  }

  /** Every row the durable copy holds, including ones a tombstone hides. */
  async function rawCards() {
    if (typeof LearningCardStore === "undefined") return [];
    try {
      return await LearningCardStore.all();
    } catch {
      return [];
    }
  }

  /** Cards to show: the durable copy with deletions applied. */
  async function localCards() {
    return (await rawCards()).filter(
      (card) => !LearningDataSync.isDeleted("vocab", card.id, card.updatedAt || ""));
  }

  /**
   * Merge a server list into the durable copy.
   *
   * Tombstones and pending mutations are applied first: writing a remote snapshot back
   * unconditionally is how a card deleted on another page came back to life.
   */
  async function merge(remoteItems) {
    const raw = await rawCards();
    const visible = raw.filter(
      (card) => !LearningDataSync.isDeleted("vocab", card.id, card.updatedAt || ""));
    const merged = LearningDataSync.mergeItems(visible, remoteItems || [], {
      entityType: "vocab", keyOf: (item) => item.id,
    });
    if (typeof LearningCardStore !== "undefined") {
      try {
        await LearningCardStore.putMany(merged);
        const keep = new Set(merged.map((item) => item.id));
        // Pruned from the raw rows, not the visible ones: a tombstoned row is invisible
        // but still occupying space, and it is exactly what needs removing once its
        // delete has been uploaded.
        const stale = raw.filter((item) => !keep.has(item.id))
          .map((item) => ({ store: "review-cards", id: item.id, remove: true }));
        // Only prune when nothing is queued: a card missing from the server response may
        // simply be one this browser has not managed to upload yet.
        if (stale.length && !LearningDataSync.pendingCount()) await LearningCardStore.writeRecords(stale);
      } catch { /* quota or a blocked upgrade: the in-memory merge is still correct */ }
    }
    return merged;
  }

  /** The note to show for a card: the entry-level note first, then the card's own. */
  function noteFor(card, entry) {
    const shared = String(entry?.note || "").trim();
    return shared || String(card?.note || "");
  }

  /**
   * Move review cards left in `localStorage` by older builds into IndexedDB.
   *
   * The old keys are removed only after the rows are read back and counted, so a quota
   * failure or a blocked upgrade leaves the only copy where it was.
   */
  async function migrateLegacyStorage() {
    if (typeof LearningCardStore === "undefined") return { migrated: 0, kept: [] };
    const pending = [];
    for (const key of LEGACY_KEYS) {
      let raw;
      try { raw = localStorage.getItem(key); } catch { continue; }
      if (!raw) continue;
      try {
        const parsed = JSON.parse(raw);
        const items = Array.isArray(parsed) ? parsed : parsed?.items;
        if (Array.isArray(items) && items.length) pending.push({ key, items: items.filter((i) => i?.id) });
      } catch { pending.push({ key, items: [] }); }
    }
    if (!pending.length) return { migrated: 0, kept: [] };
    const kept = [];
    let migrated = 0;
    for (const { key, items } of pending) {
      try {
        if (items.length) {
          await LearningCardStore.putMany(items);
          const stored = new Set((await LearningCardStore.all()).map((item) => item.id));
          if (!items.every((item) => stored.has(item.id))) throw new Error("verification failed");
          migrated += items.length;
        }
        localStorage.removeItem(key);
      } catch {
        kept.push(key);
      }
    }
    return { migrated, kept };
  }

  return { subscribe, announce, localCards, merge, noteFor, migrateLegacyStorage, channelName: CHANNEL };
})();

if (typeof module !== "undefined") module.exports = LearningCards;
