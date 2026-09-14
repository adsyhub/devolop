// PWA-001: an interrupted course download must never cost the learner the copy
// they already had.
//
// The previous implementation called removeOlderCourseCaches() *before*
// downloading, so any failure between "delete old" and "finish new" left no
// offline course at all — the exact situation an offline-first player must not
// create.

import test from "node:test";
import assert from "node:assert/strict";
import { loadServiceWorker, streamingResponse, invoke } from "./sw_harness.mjs";

const MANIFEST = new TextEncoder().encode(JSON.stringify({ courseId: "c_x" }));
const AUDIO = new Uint8Array(64).fill(7);

/** A fetch that serves the two course assets, optionally failing on the audio. */
function courseFetch({ failAudio = false } = {}) {
  return async (path) => {
    const name = String(path?.url ?? path);
    if (name.includes("manifest.json")) return streamingResponse(MANIFEST);
    if (name.includes("audio.mp3")) {
      if (failAudio) throw new Error("network dropped mid-download");
      return streamingResponse(AUDIO);
    }
    throw new Error(`unexpected fetch: ${name}`);
  };
}

async function cacheCourse(context, revision) {
  context.__rev = revision;
  await invoke(context, 'cacheCourse("cx", __rev, "audio.mp3")');
}

test("a successful download publishes the course and records it as READY", async () => {
  const { context, cacheStorage } = loadServiceWorker({ fetchImpl: courseFetch() });
  await cacheCourse(context, "rev1");

  const names = await cacheStorage.keys();
  assert.ok(names.includes("dictation-course-cx-rev1"), "active cache should exist");
  assert.ok(!names.some((n) => n.startsWith("dictation-course-staging-")), "staging should be cleaned up");

  const registry = await invoke(context, "readRegistry()");
  assert.equal(registry.cx.state, "READY");
  assert.equal(registry.cx.revision, "rev1");
});

test("a failed download leaves the previously cached course intact", async () => {
  const { context, cacheStorage, sandbox } = loadServiceWorker({ fetchImpl: courseFetch() });
  await cacheCourse(context, "rev1");

  // Now attempt a new revision whose audio download fails partway through.
  sandbox.fetch = courseFetch({ failAudio: true });
  await cacheCourse(context, "rev2");

  const names = await cacheStorage.keys();
  assert.ok(names.includes("dictation-course-cx-rev1"), "the old course must survive a failed update");
  assert.ok(!names.includes("dictation-course-cx-rev2"), "the failed revision must not be published");

  const registry = await invoke(context, "readRegistry()");
  assert.equal(registry.cx.revision, "rev1", "the active pointer must still name the working copy");
  assert.equal(registry.cx.state, "READY");
});

test("a failed download does not leave staging debris behind", async () => {
  const { context, cacheStorage } = loadServiceWorker({ fetchImpl: courseFetch({ failAudio: true }) });
  await cacheCourse(context, "rev1");

  const names = await cacheStorage.keys();
  assert.ok(!names.some((n) => n.startsWith("dictation-course-staging-")), "staging must be reclaimed");
});

test("a successful update retires the previous revision", async () => {
  const { context, cacheStorage } = loadServiceWorker({ fetchImpl: courseFetch() });
  await cacheCourse(context, "rev1");
  await cacheCourse(context, "rev2");

  const names = await cacheStorage.keys();
  assert.ok(names.includes("dictation-course-cx-rev2"));
  assert.ok(!names.includes("dictation-course-cx-rev1"), "the superseded revision should be freed");

  const registry = await invoke(context, "readRegistry()");
  assert.equal(registry.cx.revision, "rev2");
});

test("re-caching an already published revision does not re-download", async () => {
  let calls = 0;
  const counting = async (path) => {
    calls += 1;
    return courseFetch()(path);
  };
  const { context, sandbox } = loadServiceWorker({ fetchImpl: counting });
  await cacheCourse(context, "rev1");
  const afterFirst = calls;
  sandbox.fetch = counting;
  await cacheCourse(context, "rev1");
  assert.equal(calls, afterFirst, "an already-READY revision must not be fetched again");
});

test("abandoned staging caches are reclaimed on activate", async () => {
  const { context, cacheStorage } = loadServiceWorker({ fetchImpl: courseFetch() });
  // Simulate a worker that died mid-download on a previous run.
  await cacheStorage.open("dictation-course-staging-cx-oldrev");
  assert.ok((await cacheStorage.keys()).includes("dictation-course-staging-cx-oldrev"));

  await invoke(context, "reclaimAbandonedStagingCaches()");
  assert.ok(!(await cacheStorage.keys()).some((n) => n.startsWith("dictation-course-staging-")));
});
