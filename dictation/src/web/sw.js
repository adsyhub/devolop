"use strict";

// PWA-001. Three P0 defects lived in the previous version of this file:
//
//   1. `manifest.json` was served cache-first, so once a course was cached the
//      browser could never see a new contentRevision — the page asks for it with
//      `cache: "no-store"`, but a service worker sits in front of that and was
//      answering from Cache Storage regardless. A corrected course could not
//      reach a learner who had already opened the old one.
//
//   2. Caching a course deleted the previous cache *before* downloading the new
//      one. An interrupted download (closed tab, dropped network, evicted worker)
//      therefore left no offline copy at all — the old one was already gone.
//
//   3. Range requests read the entire cached audio into one ArrayBuffer and then
//      sliced it. For the 21.5MB course audio that is ~21.5MB of heap per seek,
//      repeated on every seek, to hand back a few kilobytes.
//
// Fixes below, in order: network-first for revision pointers; stage-then-promote
// so an old READY copy stays usable until a new one is verified; and a streaming
// Range reader that retains only the requested slice.

const SHELL_CACHE = "dictation-shell-v48";
const LEXICON_CACHE = "dictation-lexicon-packs-v1";
// The worker's own bookkeeping (which course is active, per-asset sizes). Its name
// is deliberately not versioned with the shell: bumping it would orphan the records
// that say which course is already downloaded, and `activate` skips it when it
// sweeps old shell caches.
const REGISTRY_CACHE = "dictation-registry-v1";
const SHELL_ASSETS = [
  "./",
  "./listening",
  "./exams",
  "./lexicon",
  "./me",
  "./home.html",
  "./home.js",
  "./me.html",
  "./me.css",
  "./personal.js",
  "./index.html",
  "./app.css",
  "./app.js",
  "./progress_model.js",
  "./dictation_scoring.js",
  "./course_library_model.js",
  "./learning_data.js",
  "./learning_store.js",
  "./learning_cards.js",
  "./srs_scheduler.js",
  "./personal_data_tools.js",
  "./media_adapters.js",
  "./exam.html",
  "./exam.css",
  "./exam.js",
  "./exam_markup.js",
  "./lexicon.html",
  "./lexicon.css",
  "./lexicon.js",
  "./lexicon_markup.js",
  "./lexicon_scoring.js",
  "./lookup_panel.js",
  "./manifest.webmanifest",
  "./icon.svg",
  "./icon-192.png",
  "./icon-512.png",
];

// Synthetic same-origin URLs used as keys for our own bookkeeping. They are never
// fetched; Cache Storage just needs a URL-shaped key.
const REGISTRY_KEY = new URL("__registry/active-course", self.registration.scope).toString();

// Size records are always keyed by the asset's absolute URL, so a lookup by
// request URL and a write by relative path ("./audio.mp3") land on the same key.
const absoluteUrl = (path) => new URL(path, self.registration.scope).toString();
const sizeKey = (cacheName, path) =>
  new URL(
    `__registry/size/${encodeURIComponent(cacheName)}/${encodeURIComponent(absoluteUrl(path))}`,
    self.registration.scope,
  ).toString();

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names
          .filter((name) => name.startsWith("dictation-shell-") && name !== SHELL_CACHE)
          .map((name) => caches.delete(name)),
      ))
      .then(() => reclaimAbandonedStagingCaches())
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type !== "CACHE_COURSE") return;
  const courseId = safeCachePart(event.data.courseId);
  const revision = safeCachePart(event.data.revision).slice(0, 16);
  // An online-video course has no local media at all: its manifest alone is the
  // cacheable part, and the video is deliberately never stored. Requiring an audio
  // filename here is what would silently leave those courses with no offline copy.
  const audioName = String(event.data.audio || "");
  if (!courseId || !revision) return;
  if (audioName && !isSafeRootFilename(audioName)) return;
  event.waitUntil(cacheCourse(courseId, revision, audioName));
});

const API_PREFIX = new URL("api/", self.registration.scope).pathname;
const BOOTSTRAP_PATH = new URL("api/session/bootstrap", self.registration.scope).pathname;
const EXAM_MEDIA_PREFIX = new URL("exam-media/", self.registration.scope).pathname;
const LEXICON_PACKS_PATH = new URL("api/lexicon/packs", self.registration.scope).pathname;

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // SEC-001: the session-token handshake must reach the network untouched and
  // must never be stored. Letting the generic /api/ branch below wrap it would
  // hand the page a synthesized `{ ok: false }` body on a transport failure,
  // which it would read as "no token" — and, worse, invites a future change to
  // start caching it. Bypassing entirely keeps the token out of Cache Storage.
  if (url.pathname === BOOTSTRAP_PATH) return;

  // Exam media is checked per request against its paper linkage and source file.
  // It must not enter Cache Storage, whose keys have no knowledge of that linkage.
  if (url.pathname.startsWith(EXAM_MEDIA_PREFIX)) {
    event.respondWith(fetch(request));
    return;
  }

  // Pack content is not personal data. Store it under synthetic token-free keys
  // so an installed pack and the last valid pack list remain available offline.
  if (url.pathname === LEXICON_PACKS_PATH || (
    url.pathname.startsWith(`${LEXICON_PACKS_PATH}/`)
    && !url.pathname.slice(LEXICON_PACKS_PATH.length + 1).includes("/")
  )) {
    event.respondWith(cacheLexiconResponse(request, url.pathname === LEXICON_PACKS_PATH));
    return;
  }

  if (url.pathname.startsWith(API_PREFIX)) {
    // Never cache the local backend API (it's dynamic, per-user data) — always hit the
    // network. But if that fetch rejects outright (offline, backend not running), hand back
    // a resolved response instead of letting the raw network failure reach the page: the
    // browser logs a "Failed to load resource" console message for *any* fetch that doesn't
    // resolve to a plain 2xx — a rejected promise (transport failure) and a synthesized
    // non-2xx status both trigger it equally, so the only way to stay console-clean for
    // app.js's routine "is a backend here at all" probe is to always resolve with 200 and
    // encode reachability in the body instead of the status code.
    event.respondWith(
      fetch(request).catch(() => new Response(
        JSON.stringify({ ok: false }),
        { status: 200, headers: { "Content-Type": "application/json", "X-Dictation-Offline": "1" } },
      )),
    );
    return;
  }

  if (request.headers.has("range")) {
    event.respondWith(serveRangeRequest(request));
    return;
  }
  if (request.mode === "navigate") {
    handleNavigation(event);
    return;
  }
  // The course manifest carries the contentRevision that tells the app whether
  // its cached course is still current, so it is a pointer, not an asset: it has
  // to be read from the network whenever the network is there. Falling back to
  // cache keeps offline study working.
  if (url.pathname.endsWith("/manifest.json")) {
    event.respondWith(networkFirst(request));
    return;
  }
  // For app.js, app.css, index.html, media_adapters.js, etc.: Network First, falling back to cache
  if (
    url.pathname.endsWith("/app.js")
    || url.pathname.endsWith("/app.css")
    || url.pathname.endsWith("/index.html")
    || url.pathname.endsWith("/media_adapters.js")
    || url.pathname.endsWith("/progress_model.js")
    || url.pathname.endsWith("/dictation_scoring.js")
    || url.pathname.endsWith("/course_library_model.js")
    || url.pathname.endsWith("/exam.js")
    || url.pathname.endsWith("/exam.css")
    || url.pathname.endsWith("/exam_markup.js")
    || url.pathname.endsWith("/lexicon.js")
    || url.pathname.endsWith("/lexicon.css")
    || url.pathname.endsWith("/lexicon_markup.js")
    || url.pathname.endsWith("/lexicon_scoring.js")
    || url.pathname.endsWith("/lookup_panel.js")
  ) {
    event.respondWith(networkFirst(request));
    return;
  }
  event.respondWith(cacheFirst(request));
});

function handleNavigation(event) {
  // One cache key per page.
  //
  // This used to read and write "./index.html" for every navigation, which was
  // correct while the player was the only page there was. It is not correct now:
  // visiting the home screen stored home.html *as* index.html, so a later offline
  // (or failed) navigation to the player answered with the home page's HTML —
  // markup that app.js cannot drive, giving a page that loads and then shows
  // nothing. Each page caches and restores under its own URL.
  const key = new URL(event.request.url);
  key.hash = "";
  key.search = "";
  const pageUrl = key.href;

  event.respondWith(
    fetch(event.request, { cache: "no-store" })
      .then(async (response) => {
        if (response.ok) {
          const cache = await caches.open(SHELL_CACHE);
          await cache.put(pageUrl, response.clone());
        }
        return response;
      })
      .catch(async () => {
        const cached = await caches.match(pageUrl);
        return cached || new Response("离线且未缓存页面", { status: 503 });
      }),
  );
}

async function cacheLexiconResponse(request, isList) {
  const cache = await caches.open(LEXICON_CACHE);
  const slug = isList ? "packs" : decodeURIComponent(new URL(request.url).pathname.split("/").pop() || "");
  const pointerKey = new URL(`__lexicon_cache__/pointer/${encodeURIComponent(slug)}`, self.registration.scope).toString();
  try {
    const response = await fetch(request, { cache: "no-store" });
    if (!response.ok || response.status !== 200) return response;
    const text = await response.clone().text();
    const declaredSize = Number(response.headers.get("Content-Length"));
    const actualSize = new TextEncoder().encode(text).byteLength;
    if (Number.isFinite(declaredSize) && declaredSize > 0 && declaredSize !== actualSize) {
      throw new Error("truncated lexicon response");
    }
    const parsed = JSON.parse(text);
    if (isList) {
      if (!Array.isArray(parsed.packs)) throw new Error("invalid pack list");
    } else if (
      !parsed.pack || !parsed.pack.packId || !parsed.pack.contentRevision
      || !Array.isArray(parsed.pack.entries)
      || Number(parsed.pack.entryCount) !== parsed.pack.entries.length
      || parsed.pack.quality?.blocked
    ) {
      throw new Error("invalid lexicon pack");
    }
    const revision = isList ? "latest" : String(parsed.pack.contentRevision).slice(0, 80);
    const dataKey = new URL(
      `__lexicon_cache__/data/${encodeURIComponent(slug)}/${encodeURIComponent(revision)}`,
      self.registration.scope,
    ).toString();
    const stored = new Response(text, { status: 200, headers: { "Content-Type": "application/json; charset=utf-8" } });
    await cache.put(dataKey, stored);
    await cache.put(pointerKey, new Response(JSON.stringify({ dataKey }), { headers: { "Content-Type": "application/json" } }));
    return response;
  } catch {
    const pointer = await cache.match(pointerKey);
    if (!pointer) return new Response(JSON.stringify({ ok: false }), { status: 200, headers: { "Content-Type": "application/json" } });
    const { dataKey } = await pointer.json();
    const cached = dataKey ? await cache.match(dataKey) : null;
    return cached || new Response(JSON.stringify({ ok: false }), { status: 200, headers: { "Content-Type": "application/json" } });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request, { cache: "no-store" });
    if (response.ok && response.status === 200) return response;
  } catch {
    // fall through to cache
  }
  const cached = await caches.match(request, { ignoreSearch: true });
  if (cached) return cached;
  return fetch(request);
}

// ---------------------------------------------------------------------------
// Recorded sizes
//
// A cache write can be interrupted mid-transfer and leave a truncated entry;
// trusting one means serving broken audio until someone manually clears site
// data. The previous check caught that by reading the whole cached body back and
// comparing its length — correct, but it made every cache hit cost a full read of
// the asset. Recording the verified length once, at write time, gives the same
// guarantee for the price of a tiny metadata lookup.
// ---------------------------------------------------------------------------

async function recordSize(cacheName, path, bytes) {
  const registry = await caches.open(REGISTRY_CACHE);
  await registry.put(sizeKey(cacheName, path), new Response(String(bytes)));
}

async function readRecordedSize(cacheName, path) {
  const registry = await caches.open(REGISTRY_CACHE);
  const entry = await registry.match(sizeKey(cacheName, path));
  if (!entry) return null;
  const value = Number(await entry.text());
  return Number.isFinite(value) && value >= 0 ? value : null;
}

async function forgetSizes(cacheName) {
  const registry = await caches.open(REGISTRY_CACHE);
  const keys = await registry.keys();
  const prefix = new URL(
    `__registry/size/${encodeURIComponent(cacheName)}/`,
    self.registration.scope,
  ).toString();
  await Promise.all(keys.filter((key) => key.url.startsWith(prefix)).map((key) => registry.delete(key)));
}

/** Copy a response into a cache, verifying it arrived whole, and record its length. */
async function cacheVerified(cache, cacheName, path, response) {
  if (!response.ok || response.status !== 200) {
    throw new Error(`fetch ${path} failed (HTTP ${response.status})`);
  }
  const declared = Number(response.headers.get("Content-Length"));
  const body = await response.clone().arrayBuffer();
  if (Number.isFinite(declared) && declared > 0 && body.byteLength !== declared) {
    throw new Error(`truncated ${path}: ${body.byteLength} of ${declared} bytes`);
  }
  await cache.put(path, response);
  await recordSize(cacheName, path, body.byteLength);
  return body.byteLength;
}

// ---------------------------------------------------------------------------
// Two-phase course caching
//
// Download into a staging cache, verify every asset, and only then publish the
// active pointer and drop the previous cache. At every intermediate point a
// crash leaves the previously READY course fully intact — the worst outcome is
// an abandoned staging cache, which the next activate() reclaims.
//
// This is a recoverable two-phase swap, not an atomic one: Cache Storage and the
// registry are separate stores and cannot be written in a single transaction.
// The ordering is chosen so that every possible interruption point leaves a
// usable state, which is the property that actually matters here.
// ---------------------------------------------------------------------------

async function readRegistry() {
  const registry = await caches.open(REGISTRY_CACHE);
  const entry = await registry.match(REGISTRY_KEY);
  if (!entry) return {};
  try {
    return await entry.json();
  } catch {
    return {};
  }
}

async function writeRegistry(value) {
  const registry = await caches.open(REGISTRY_CACHE);
  await registry.put(REGISTRY_KEY, new Response(JSON.stringify(value), {
    headers: { "Content-Type": "application/json" },
  }));
}

async function cacheCourse(courseId, revision, audioName) {
  const activeName = `dictation-course-${courseId}-${revision}`;
  const stagingName = `dictation-course-staging-${courseId}-${revision}`;

  const registry = await readRegistry();
  if (registry[courseId]?.cacheName === activeName && registry[courseId]?.state === "READY") {
    return; // Already published at this revision; re-downloading would be pure waste.
  }

  await caches.delete(stagingName); // Discard any partial attempt from a previous run.
  const staging = await caches.open(stagingName);
  // Only ever same-origin assets. A remote course's media lives on another origin
  // and must never be pulled into Cache Storage — we hold no rights to it, and an
  // opaque cross-origin response could not be verified for completeness anyway.
  const assets = audioName ? ["./manifest.json", `./${audioName}`] : ["./manifest.json"];

  try {
    for (const path of assets) {
      const response = await fetch(path, { cache: "no-store" });
      await cacheVerified(staging, stagingName, path, response);
    }
  } catch (error) {
    // The previously published course is untouched and still serving.
    await caches.delete(stagingName);
    await forgetSizes(stagingName);
    console.warn("Course download failed; the previously cached course is still available.", error);
    return;
  }

  // Promote: copy staged entries to the active cache name, publish the pointer,
  // then retire the old one. Only after the pointer is published is the previous
  // revision safe to delete.
  const active = await caches.open(activeName);
  for (const path of assets) {
    const staged = await staging.match(path);
    const size = await readRecordedSize(stagingName, path);
    await active.put(path, staged);
    await recordSize(activeName, path, size ?? 0);
  }

  const previous = registry[courseId];
  await writeRegistry({ ...registry, [courseId]: { cacheName: activeName, revision, state: "READY" } });

  await caches.delete(stagingName);
  await forgetSizes(stagingName);
  if (previous?.cacheName && previous.cacheName !== activeName) {
    await caches.delete(previous.cacheName);
    await forgetSizes(previous.cacheName);
  }
}

async function reclaimAbandonedStagingCaches() {
  const names = await caches.keys();
  await Promise.all(
    names
      .filter((name) => name.startsWith("dictation-course-staging-"))
      .map(async (name) => {
        await caches.delete(name);
        await forgetSizes(name);
      }),
  );
}

// ---------------------------------------------------------------------------

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached && (await cachedEntryLooksComplete(request, cached))) return cached;
  const response = await fetch(request);
  if (response.ok && response.status === 200) {
    const cache = await caches.open(SHELL_CACHE);
    try {
      await cacheVerified(cache, SHELL_CACHE, request.url, response.clone());
    } catch {
      // A truncated download is simply not cached; the live response still serves
      // this request, and the next load retries.
    }
  }
  return response;
}

async function cachedEntryLooksComplete(request, cached) {
  const declared = Number(cached.headers.get("Content-Length"));
  if (!Number.isFinite(declared) || declared <= 0) return true;
  const recorded = await findRecordedSize(request.url);
  // No recorded size means the entry predates this bookkeeping (e.g. written by
  // an older service worker). Verify it the expensive way exactly once, then let
  // the write path record it going forward.
  if (recorded === null) {
    const body = await cached.clone().arrayBuffer();
    return body.byteLength === declared;
  }
  return recorded === declared;
}

async function findRecordedSize(url) {
  for (const name of await caches.keys()) {
    if (name === REGISTRY_CACHE) continue;
    const recorded = await readRecordedSize(name, url);
    if (recorded !== null) return recorded;
  }
  return null;
}

/**
 * Answer a Range request from the cache without materialising the whole asset.
 *
 * Cache Storage has no partial-read API, so the bytes before `start` still have
 * to be pulled off the stream — but they are released as they go, and only the
 * requested slice is retained. Peak retention is the range size plus one chunk
 * rather than the full asset, which is what makes repeated seeking through a
 * 21.5MB file affordable.
 *
 * Chunked or per-sentence media storage would avoid the skipped read entirely.
 * That is ADR-PWA-001's open decision and needs a benchmark first, so it is
 * deliberately not pre-empted here.
 */
async function serveRangeRequest(request) {
  const cached = await caches.match(new Request(request.url));
  if (!cached || !cached.body) return fetch(request);

  const size = Number(cached.headers.get("Content-Length"));
  if (!Number.isFinite(size) || size <= 0) return fetch(request);
  const recorded = await findRecordedSize(request.url);
  if (recorded !== null && recorded !== size) return fetch(request); // truncated entry

  const range = request.headers.get("range") || "";
  const match = /^bytes=(\d*)-(\d*)$/i.exec(range.trim());
  if (!match) return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });

  let start;
  let end;
  if (!match[1] && match[2]) {
    start = Math.max(0, size - Number(match[2]));
    end = size - 1;
  } else {
    start = match[1] ? Number(match[1]) : 0;
    end = match[2] ? Math.min(Number(match[2]), size - 1) : size - 1;
  }
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || start > end || start >= size) {
    return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
  }

  const slice = await readByteRange(cached.body, start, end);
  if (!slice) return fetch(request);

  const headers = new Headers(cached.headers);
  headers.set("Accept-Ranges", "bytes");
  headers.set("Content-Range", `bytes ${start}-${end}/${size}`);
  headers.set("Content-Length", String(slice.byteLength));
  return new Response(slice, { status: 206, statusText: "Partial Content", headers });
}

async function readByteRange(stream, start, end) {
  const wanted = end - start + 1;
  const out = new Uint8Array(wanted);
  const reader = stream.getReader();
  let position = 0;
  let written = 0;
  try {
    while (written < wanted) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunkStart = position;
      const chunkEnd = position + value.byteLength;
      position = chunkEnd;
      if (chunkEnd <= start) continue; // entirely before the range; drop it
      const from = Math.max(0, start - chunkStart);
      const to = Math.min(value.byteLength, end - chunkStart + 1);
      if (to <= from) continue;
      const piece = value.subarray(from, to);
      out.set(piece, written);
      written += piece.byteLength;
    }
  } finally {
    // Releasing the lock lets the browser tear down the rest of the stream
    // instead of holding the remaining bytes for a reader that stopped early.
    reader.cancel().catch(() => undefined);
    reader.releaseLock?.();
  }
  return written === wanted ? out : null;
}

function isSafeRootFilename(value) {
  return Boolean(value) && !value.includes("/") && !value.includes("\\") && !value.includes("..");
}

function safeCachePart(value) {
  return String(value || "").replace(/[^a-zA-Z0-9_-]/g, "");
}
