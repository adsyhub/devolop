// PWA-001: the Range reader must return exactly the requested bytes and must not
// retain the whole asset while doing it.
//
// The previous implementation called `response.arrayBuffer()` on the cached
// audio and sliced the result — 21.5MB of heap for every seek. These tests pin
// both the arithmetic and the bounded-retention property.

import test from "node:test";
import assert from "node:assert/strict";
import { loadServiceWorker, streamingResponse, invoke } from "./sw_harness.mjs";

const BYTES = new Uint8Array(256);
for (let i = 0; i < BYTES.length; i += 1) BYTES[i] = i;

function reader() {
  const { context } = loadServiceWorker();
  return async (start, end, chunkSize = 8) => {
    const response = streamingResponse(BYTES, { chunkSize });
    context.__stream = response.body;
    context.__start = start;
    context.__end = end;
    const result = await invoke(context, "readByteRange(__stream, __start, __end)");
    return { result, tracker: response.tracker };
  };
}

test("returns exactly the requested bytes from the middle", async () => {
  const read = reader();
  const { result } = await read(100, 149);
  assert.equal(result.byteLength, 50);
  assert.deepEqual([...result], [...BYTES.subarray(100, 150)]);
});

test("returns a range that starts at zero", async () => {
  const read = reader();
  const { result } = await read(0, 9);
  assert.deepEqual([...result], [...BYTES.subarray(0, 10)]);
});

test("returns a range that runs to the final byte", async () => {
  const read = reader();
  const { result } = await read(250, 255);
  assert.deepEqual([...result], [...BYTES.subarray(250, 256)]);
});

test("returns a single byte", async () => {
  const read = reader();
  const { result } = await read(42, 42);
  assert.deepEqual([...result], [42]);
});

test("handles a range that does not align with chunk boundaries", async () => {
  const read = reader();
  const { result } = await read(13, 27, 8);
  assert.deepEqual([...result], [...BYTES.subarray(13, 28)]);
});

test("stops reading once the range is satisfied", async () => {
  // The whole point of the rewrite: a small range near the start must not pull
  // the entire asset through the reader.
  const read = reader();
  const { tracker } = await read(0, 7, 8);
  assert.equal(tracker.bytesRead, 8, "should read one chunk, not the whole asset");
  assert.ok(tracker.bytesRead < BYTES.length);
});

test("reads only up to the end of the range, not to the end of the asset", async () => {
  const read = reader();
  const { tracker } = await read(32, 47, 8);
  // Chunks 0..5 cover bytes 0..47; nothing beyond byte 48 should be pulled.
  assert.equal(tracker.bytesRead, 48);
  assert.ok(tracker.bytesRead < BYTES.length);
});

test("returns null when the stream ends before the range is filled", async () => {
  // A truncated cache entry must be reported as unusable rather than padded out
  // with zeroes, which would be silent audio corruption.
  const read = reader();
  const { result } = await read(250, 300);
  assert.equal(result, null);
});
