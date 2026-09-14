// The media adapter layer, exercised without a browser.
//
// Two things here would break the feature silently rather than loudly, so they get
// the most coverage:
//
//   * the requestAnimationFrame clock. YouTube's API has no timeupdate event, so the
//     adapter synthesises one. A loop that fails to stop keeps waking a backgrounded
//     tab forever; a loop that fails to start makes every sentence overrun its end.
//   * the degrade paths. The API script may never load, and errors 101/150 mean the
//     uploader disabled embedding — routine for the news channels this targets. The
//     player must hand the learner a working fallback, not a dead frame.

import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const MediaAdapters = require(path.join(HERE, "..", "src", "web", "media_adapters.js"));

// --------------------------------------------------------------------- fakes

function fakeElement(tag) {
  return {
    tagName: tag,
    children: [],
    attributes: {},
    parentNode: null,
    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      return child;
    },
    removeChild(child) {
      this.children = this.children.filter((item) => item !== child);
      child.parentNode = null;
      return child;
    },
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener() {},
    removeEventListener() {},
  };
}

function fakeDocument() {
  const head = fakeElement("head");
  return { head, body: fakeElement("body"), documentElement: head, createElement: fakeElement };
}

/** A manual clock: nothing runs until the test says so. */
function manualRaf() {
  let next = 1;
  const pending = new Map();
  return {
    raf(callback) {
      const handle = next++;
      pending.set(handle, callback);
      return handle;
    },
    cancelRaf(handle) { pending.delete(handle); },
    get pendingCount() { return pending.size; },
    // One frame: take what is scheduled now and run it, so a callback that
    // reschedules itself does not spin inside this call.
    tick() {
      const batch = Array.from(pending.entries());
      pending.clear();
      for (const [, callback] of batch) callback();
      return batch.length;
    },
  };
}

function fakeYT(state = {}) {
  const created = [];
  const YT = {
    Player: class {
      constructor(frame, config) {
        this.frame = frame;
        this.events = (config && config.events) || {};
        this.time = state.time || 0;
        this.rate = 1;
        this.seeks = [];
        this.calls = [];
        this.destroyed = false;
        created.push(this);
      }
      getDuration() { return state.duration === undefined ? 612 : state.duration; }
      getCurrentTime() { return this.time; }
      getAvailablePlaybackRates() { return state.rates || [0.25, 0.5, 1, 1.5, 2]; }
      setPlaybackRate(rate) { this.rate = rate; this.calls.push(["rate", rate]); }
      seekTo(seconds, allow) { this.time = seconds; this.seeks.push([seconds, allow]); }
      playVideo() { this.calls.push(["play"]); }
      pauseVideo() { this.calls.push(["pause"]); }
      destroy() { this.destroyed = true; }
    },
  };
  return { YT, created };
}

const YOUTUBE_MEDIA = {
  kind: "remote",
  provider: "youtube",
  control: "full",
  videoId: "dQw4w9WgXcQ",
  pageUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  embedUrl: "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
  durationSec: 612,
};

const BILIBILI_MEDIA = {
  kind: "remote",
  provider: "bilibili",
  control: "seek-reload",
  videoId: "BV1xx411c7XX",
  pageUrl: "https://www.bilibili.com/video/BV1xx411c7XX",
  embedUrl: "https://player.bilibili.com/player.html?bvid=BV1xx411c7XX&autoplay=0",
  durationSec: 300,
};

/** Build a YouTubeAdapter with every seam faked, and hand back the seams. */
async function makeYouTubeAdapter(options = {}) {
  const doc = fakeDocument();
  const container = fakeElement("div");
  const clock = manualRaf();
  const { YT, created } = fakeYT(options.ytState);
  let rejectApi;
  const apiPromise = options.failApi
    ? new Promise((_, reject) => { rejectApi = reject; })
    : Promise.resolve(YT);

  const adapter = new MediaAdapters.YouTubeAdapter(options.media || YOUTUBE_MEDIA, {
    document: doc,
    window: { location: { origin: "http://127.0.0.1:4173" } },
    container,
    origin: "http://127.0.0.1:4173",
    raf: clock.raf,
    cancelRaf: clock.cancelRaf,
    loadApi: () => apiPromise,
  });
  if (options.failApi) {
    rejectApi(new Error(options.failApi));
    await apiPromise.catch(() => {});
  }
  // Let the loader's .then run.
  await new Promise((resolve) => setImmediate(resolve));
  return { adapter, doc, container, clock, player: created[0], created };
}

// ------------------------------------------------------------- pure helpers

test("formatClock renders minutes and padded seconds", () => {
  assert.equal(MediaAdapters.formatClock(0), "0:00");
  assert.equal(MediaAdapters.formatClock(65.9), "1:05");
  assert.equal(MediaAdapters.formatClock(-4), "0:00");
  assert.equal(MediaAdapters.formatClock(3600), "60:00");
});

test("a timestamp truncates rather than rounds, so the first syllable survives", () => {
  assert.equal(MediaAdapters.wholeSeconds(65.99), 65);
  assert.equal(MediaAdapters.wholeSeconds(-2), 0);
});

test("the youtube embed src never enables the site's own captions", () => {
  // Showing YouTube's captions would hand the learner the exact answer the
  // dictation exercise asks them to write down.
  const src = MediaAdapters.youTubeEmbedSrc("dQw4w9WgXcQ", { origin: "http://127.0.0.1:4173" });
  const url = new URL(src);
  assert.equal(url.origin + url.pathname, "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ");
  assert.equal(url.searchParams.get("cc_load_policy"), "0");
  assert.equal(url.searchParams.get("enablejsapi"), "1");
  assert.equal(url.searchParams.get("origin"), "http://127.0.0.1:4173");
});

test("the embed src carries a start time only when there is one", () => {
  assert.equal(new URL(MediaAdapters.youTubeEmbedSrc("abc")).searchParams.get("start"), null);
  const withStart = MediaAdapters.youTubeEmbedSrc("abc", { start: 30.9 });
  assert.equal(new URL(withStart).searchParams.get("start"), "30");
});

test("a video id that needs escaping cannot break out of the path", () => {
  const src = MediaAdapters.youTubeEmbedSrc("a/../b?x=1");
  assert.ok(!src.includes("/../"));
  assert.equal(new URL(src).pathname, "/embed/a%2F..%2Fb%3Fx%3D1");
});

test("each provider gets its own deep-link shape", () => {
  assert.equal(
    MediaAdapters.timestampUrl("https://www.youtube.com/watch?v=abc", "youtube", 65.9),
    "https://www.youtube.com/watch?v=abc&t=65s",
  );
  assert.ok(MediaAdapters.timestampUrl("https://www.bilibili.com/video/BV1", "bilibili", 65).includes("t=65"));
  assert.ok(MediaAdapters.timestampUrl("https://vimeo.com/123456", "vimeo", 65).endsWith("#t=65s"));
  assert.equal(
    MediaAdapters.timestampUrl("https://example.com/watch", "generic", 65),
    "https://example.com/watch",
  );
});

test("a malformed page url is returned untouched rather than throwing", () => {
  assert.equal(MediaAdapters.timestampUrl("not a url", "youtube", 5), "not a url");
  assert.equal(MediaAdapters.timestampUrl("", "youtube", 5), "");
});

test("embedSrcAt keeps absolute video times even for a clipped course", () => {
  // Subtracting clip.startTime here is the bug that makes every seek in a clipped
  // course land clip.startTime seconds early.
  const clipped = Object.assign({}, BILIBILI_MEDIA, { clip: { startTime: 100, endTime: 200 } });
  const url = new URL(MediaAdapters.embedSrcAt(clipped, 130));
  assert.equal(url.searchParams.get("t"), "130");
  assert.equal(url.searchParams.get("autoplay"), "1");
});

// ----------------------------------------------------------------- dispatch

test("create() picks the adapter the manifest earns", () => {
  const audioElement = { paused: true, addEventListener() {}, removeEventListener() {} };
  assert.ok(MediaAdapters.create({ audio: "audio.mp3" }, { audioElement })
    instanceof MediaAdapters.AudioElementAdapter);

  const doc = fakeDocument();
  assert.ok(MediaAdapters.create({ media: BILIBILI_MEDIA }, { document: doc, container: fakeElement("div") })
    instanceof MediaAdapters.EmbedAdapter);

  assert.ok(MediaAdapters.create(
    { media: { provider: "generic", control: "external", pageUrl: "https://x.test/v", embedUrl: "" } },
    { document: doc },
  ) instanceof MediaAdapters.ExternalAdapter);
});

test("a framed tier with no embed url falls back to external rather than an empty box", () => {
  const broken = Object.assign({}, BILIBILI_MEDIA, { embedUrl: "" });
  const adapter = MediaAdapters.create({ media: broken }, { document: fakeDocument() });
  assert.ok(adapter instanceof MediaAdapters.ExternalAdapter);
  assert.equal(adapter.canSeek, false);
});

test("every adapter reports a control tier and a Chinese label", () => {
  const doc = fakeDocument();
  const adapters = [
    MediaAdapters.create({ media: BILIBILI_MEDIA }, { document: doc, container: fakeElement("div") }),
    MediaAdapters.create({ media: { provider: "generic", control: "external", pageUrl: "https://x.test/v" } }, { document: doc }),
  ];
  for (const adapter of adapters) {
    const described = adapter.describe();
    assert.ok(["full", "seek-reload", "external"].includes(described.control));
    assert.ok(described.label.length > 0);
    assert.equal(typeof described.canSeek, "boolean");
  }
});

// ----------------------------------------------------- YouTube state machine

test("the adapter becomes ready and learns the real duration", async () => {
  const { adapter, player } = await makeYouTubeAdapter();
  const seen = [];
  adapter.on("ready", () => seen.push("ready"));
  player.events.onReady();
  assert.deepEqual(seen, ["ready"]);
  assert.equal(adapter.ready, true);
  assert.equal(adapter.duration, 612);
});

test("the synthetic clock runs while playing and stops on pause", async () => {
  const { adapter, player, clock } = await makeYouTubeAdapter();
  player.events.onReady();

  let ticks = 0;
  adapter.on("timeupdate", () => { ticks += 1; });

  player.events.onStateChange({ data: MediaAdapters.YT_STATE.PLAYING });
  assert.equal(adapter.paused, false);

  player.time = 1.5;
  clock.tick();
  player.time = 2.0;
  clock.tick();
  assert.equal(ticks, 2);
  assert.equal(adapter.currentTime, 2.0);

  player.events.onStateChange({ data: MediaAdapters.YT_STATE.PAUSED });
  assert.equal(adapter.paused, true);
  // Nothing is scheduled any more, so the tab stops being woken.
  assert.equal(clock.pendingCount, 0);
  clock.tick();
  assert.equal(ticks, 2);
});

test("pause() stops the clock immediately, without waiting for the state event", async () => {
  // A paused player that keeps emitting timeupdate makes app.js's sentence-loop
  // logic fire repeatedly against a frozen time.
  const { adapter, player, clock } = await makeYouTubeAdapter();
  player.events.onReady();
  player.events.onStateChange({ data: MediaAdapters.YT_STATE.PLAYING });
  assert.equal(clock.pendingCount, 1);
  adapter.pause();
  assert.equal(clock.pendingCount, 0);
  assert.equal(adapter.paused, true);
});

test("destroy() stops the clock, tears down the player and removes the iframe", async () => {
  const { adapter, player, clock, container } = await makeYouTubeAdapter();
  player.events.onReady();
  player.events.onStateChange({ data: MediaAdapters.YT_STATE.PLAYING });
  assert.equal(container.children.length, 1);

  adapter.destroy();
  assert.equal(clock.pendingCount, 0);
  assert.equal(player.destroyed, true);
  assert.equal(container.children.length, 0);

  // A frame already in flight when destroy() ran must not reschedule itself.
  clock.tick();
  assert.equal(clock.pendingCount, 0);
});

test("seeking goes through seekTo and reports the new time at once", async () => {
  const { adapter, player } = await makeYouTubeAdapter();
  player.events.onReady();
  let updates = 0;
  adapter.on("timeupdate", () => { updates += 1; });
  adapter.currentTime = 42.5;
  assert.deepEqual(player.seeks, [[42.5, true]]);
  assert.equal(adapter.currentTime, 42.5);
  assert.equal(updates, 1);
});

test("an ended video emits ended and stops the clock", async () => {
  const { adapter, player, clock } = await makeYouTubeAdapter();
  player.events.onReady();
  player.events.onStateChange({ data: MediaAdapters.YT_STATE.PLAYING });
  let ended = 0;
  adapter.on("ended", () => { ended += 1; });
  player.events.onStateChange({ data: MediaAdapters.YT_STATE.ENDED });
  assert.equal(ended, 1);
  assert.equal(clock.pendingCount, 0);
});

test("playback rate snaps to a rate YouTube will actually honour", async () => {
  // Setting an unsupported rate is silently ignored by the API, which would leave
  // the UI claiming 0.8x while the audio plays at 1x.
  const { adapter, player } = await makeYouTubeAdapter({ ytState: { rates: [0.5, 1, 1.5, 2] } });
  player.events.onReady();
  adapter.playbackRate = 1.5;
  assert.equal(adapter.playbackRate, 1.5);
  assert.equal(player.rate, 1.5);
});

test("snapping never answers 'slow this down' with a faster rate", async () => {
  // Nearest-neighbour would put 0.8 at 1.0, because it is 0.2 away rather than
  // 0.05 — so a learner asking to slow down would get no slowdown at all.
  const { adapter, player } = await makeYouTubeAdapter({
    ytState: { rates: [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2] },
  });
  player.events.onReady();
  adapter.playbackRate = 0.8;
  assert.equal(adapter.playbackRate, 0.75);
  assert.equal(player.rate, 0.75);
  adapter.playbackRate = 1.4;
  assert.equal(adapter.playbackRate, 1.25);
});

test("a request below every available rate gets the slowest one, not nothing", async () => {
  const { adapter, player } = await makeYouTubeAdapter({ ytState: { rates: [0.5, 1, 2] } });
  player.events.onReady();
  adapter.playbackRate = 0.1;
  assert.equal(adapter.playbackRate, 0.5);
});

test("available rates are exposed so the UI can offer only real ones", async () => {
  const { adapter, player } = await makeYouTubeAdapter({ ytState: { rates: [1, 2] } });
  player.events.onReady();
  assert.deepEqual(adapter.availableRates, [1, 2]);
});

// ------------------------------------------------------------ degrade paths

test("an API that never loads degrades instead of leaving a dead frame", async () => {
  const doc = fakeDocument();
  const container = fakeElement("div");
  const adapter = new MediaAdapters.YouTubeAdapter(YOUTUBE_MEDIA, {
    document: doc,
    window: { location: { origin: "http://127.0.0.1:4173" } },
    container,
    loadApi: () => Promise.reject(new Error("timeout")),
  });
  const degraded = await new Promise((resolve) => {
    adapter.on("degrade", resolve);
  });
  assert.equal(degraded.reason, "api-timeout");
  assert.ok(degraded.message.length > 0);
});

test("a blocked API script degrades with its own reason code", async () => {
  const doc = fakeDocument();
  const adapter = new MediaAdapters.YouTubeAdapter(YOUTUBE_MEDIA, {
    document: doc,
    window: { location: { origin: "http://127.0.0.1:4173" } },
    container: fakeElement("div"),
    loadApi: () => Promise.reject(new Error("script")),
  });
  const degraded = await new Promise((resolve) => adapter.on("degrade", resolve));
  assert.equal(degraded.reason, "api-blocked");
});

test("an uploader who disabled embedding degrades with an explanation, not an error", async () => {
  for (const code of [101, 150]) {
    const { adapter, player } = await makeYouTubeAdapter();
    player.events.onReady();
    const degraded = await new Promise((resolve) => {
      adapter.on("degrade", resolve);
      player.events.onError({ data: code });
    });
    assert.equal(degraded.reason, "embedding-disabled");
    assert.ok(degraded.message.includes("嵌入"));
  }
});

test("other player errors degrade too, each keeping its code", async () => {
  const { adapter, player } = await makeYouTubeAdapter();
  player.events.onReady();
  const degraded = await new Promise((resolve) => {
    adapter.on("degrade", resolve);
    player.events.onError({ data: 100 });
  });
  assert.equal(degraded.reason, "yt-error-100");
});

test("degrading stops the clock so a dead player cannot keep waking the tab", async () => {
  const { adapter, player, clock } = await makeYouTubeAdapter();
  player.events.onReady();
  player.events.onStateChange({ data: MediaAdapters.YT_STATE.PLAYING });
  assert.equal(clock.pendingCount, 1);
  player.events.onError({ data: 101 });
  assert.equal(clock.pendingCount, 0);
});

test("the external fallback preserves the deep links the learner still needs", () => {
  const adapter = MediaAdapters.externalFallback(YOUTUBE_MEDIA, "embedding-disabled");
  assert.equal(adapter.control, "external");
  assert.equal(adapter.canSeek, false);
  assert.equal(adapter.reason, "embedding-disabled");
  assert.equal(
    adapter.externalUrlAt(65.9),
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=65s",
  );
});

// -------------------------------------------------------- seek-reload tier

test("seeking a seek-reload player rebuilds the frame at that timestamp", () => {
  const container = fakeElement("div");
  const adapter = new MediaAdapters.EmbedAdapter(BILIBILI_MEDIA, {
    document: fakeDocument(),
    container,
  });
  adapter.seek(90.7);
  const url = new URL(adapter._frame.src);
  assert.equal(url.searchParams.get("t"), "90");
  assert.equal(url.searchParams.get("autoplay"), "1");
  assert.equal(adapter.currentTime, 90.7);
});

test("a seek-reload player never claims to be playing", () => {
  // app.js must not believe it is driving something it cannot observe.
  const adapter = new MediaAdapters.EmbedAdapter(BILIBILI_MEDIA, {
    document: fakeDocument(),
    container: fakeElement("div"),
  });
  assert.equal(adapter.paused, true);
  adapter.play();
  assert.equal(adapter.paused, true);
  assert.equal(adapter.describe().control, "seek-reload");
});

// -------------------------------------------------------------- local audio

test("the local audio adapter forwards the element's own events unchanged", async () => {
  const listeners = {};
  const element = {
    paused: true,
    currentTime: 0,
    duration: 120,
    playbackRate: 1,
    addEventListener(name, fn) { listeners[name] = fn; },
    removeEventListener(name) { delete listeners[name]; },
    play() { this.paused = false; return Promise.resolve(); },
    pause() { this.paused = true; },
  };
  const adapter = new MediaAdapters.AudioElementAdapter(element);
  let ticks = 0;
  adapter.on("timeupdate", () => { ticks += 1; });
  listeners.timeupdate();
  assert.equal(ticks, 1);

  adapter.currentTime = 12.5;
  assert.equal(element.currentTime, 12.5);
  assert.equal(adapter.duration, 120);
  await adapter.play();
  assert.equal(adapter.paused, false);

  adapter.destroy();
  assert.equal(Object.keys(listeners).length, 0);
});

test("an autoplay rejection is swallowed, any other play failure is not", async () => {
  const make = (error) => new MediaAdapters.AudioElementAdapter({
    paused: true,
    addEventListener() {}, removeEventListener() {},
    play: () => Promise.reject(error),
  });
  const notAllowed = Object.assign(new Error("blocked"), { name: "NotAllowedError" });
  const aborted = Object.assign(new Error("interrupted"), { name: "AbortError" });
  await make(notAllowed).play();
  await make(aborted).play();
  await assert.rejects(() => make(new Error("decode failed")).play());
});
