// Loads sw.js into a sandbox with just enough of the service-worker globals to
// exercise its pure logic. The alternative — asserting against a reimplementation
// of the Range arithmetic — would test the copy rather than the code that ships.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const SW_PATH = join(here, "..", "src", "web", "sw.js");

class FakeCache {
  constructor() { this.entries = new Map(); }
  async put(key, response) { this.entries.set(String(key), response); }
  async match(key) { return this.entries.get(String(key)); }
  async delete(key) { return this.entries.delete(String(key)); }
  async keys() { return [...this.entries.keys()].map((url) => ({ url })); }
  async addAll() {}
}

class FakeCacheStorage {
  constructor() { this.caches = new Map(); }
  async open(name) {
    if (!this.caches.has(name)) this.caches.set(name, new FakeCache());
    return this.caches.get(name);
  }
  async keys() { return [...this.caches.keys()]; }
  async delete(name) { return this.caches.delete(name); }
  async match(request) {
    const url = String(request?.url ?? request);
    for (const cache of this.caches.values()) {
      const hit = await cache.match(url);
      if (hit) return hit;
    }
    return undefined;
  }
}

/** A Response whose body streams in fixed-size chunks, so a reader that stops
 *  early can be observed stopping early. */
export function streamingResponse(bytes, { chunkSize = 8, headers = {} } = {}) {
  let delivered = 0;
  const tracker = { chunksRead: 0, bytesRead: 0 };
  const body = {
    getReader() {
      return {
        async read() {
          if (delivered >= bytes.length) return { done: true, value: undefined };
          const value = bytes.subarray(delivered, Math.min(delivered + chunkSize, bytes.length));
          delivered += value.length;
          tracker.chunksRead += 1;
          tracker.bytesRead += value.length;
          return { done: false, value };
        },
        async cancel() { delivered = bytes.length; },
        releaseLock() {},
      };
    },
  };
  const headerMap = new Map(Object.entries({ "Content-Length": String(bytes.length), ...headers }));
  return {
    body,
    tracker,
    status: 200,
    ok: true,
    headers: {
      get: (name) => headerMap.get(name) ?? headerMap.get(Object.keys(Object.fromEntries(headerMap)).find((k) => k.toLowerCase() === name.toLowerCase())) ?? null,
      entries: () => headerMap.entries(),
      [Symbol.iterator]: () => headerMap.entries(),
    },
    clone() { return streamingResponse(bytes, { chunkSize, headers }); },
    async arrayBuffer() { return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.length); },
    async text() { return Buffer.from(bytes).toString("utf8"); },
    async json() { return JSON.parse(Buffer.from(bytes).toString("utf8")); },
  };
}

export function loadServiceWorker({ fetchImpl } = {}) {
  const scope = "http://127.0.0.1:4173/";
  const listeners = new Map();
  const cacheStorage = new FakeCacheStorage();

  const sandbox = {
    console,
    URL,
    Headers: class Headers {
      constructor(init) {
        this.map = new Map();
        if (init?.entries) for (const [k, v] of init.entries()) this.map.set(String(k).toLowerCase(), v);
        else if (init) for (const [k, v] of Object.entries(init)) this.map.set(String(k).toLowerCase(), v);
      }
      get(name) { return this.map.get(String(name).toLowerCase()) ?? null; }
      set(name, value) { this.map.set(String(name).toLowerCase(), String(value)); }
      has(name) { return this.map.has(String(name).toLowerCase()); }
      entries() { return this.map.entries(); }
    },
    Request: class Request {
      constructor(url, init = {}) { this.url = String(url); Object.assign(this, init); }
    },
    Response: class Response {
      constructor(body, init = {}) {
        this.body = body;
        this.status = init.status ?? 200;
        this.statusText = init.statusText ?? "";
        this.ok = this.status >= 200 && this.status < 300;
        this.headers = init.headers ?? new Map();
        this._body = body;
      }
      async text() { return String(this._body ?? ""); }
      async json() { return JSON.parse(String(this._body ?? "null")); }
      async arrayBuffer() { return this._body; }
      clone() { return this; }
    },
    caches: cacheStorage,
    fetch: fetchImpl ?? (async () => { throw new Error("network disabled in this test"); }),
    Number, Math, Promise, JSON, String, Boolean, Array, Object, Uint8Array, Error,
    encodeURIComponent, decodeURIComponent,
    setTimeout, clearTimeout,
  };
  sandbox.self = {
    addEventListener: (type, handler) => listeners.set(type, handler),
    registration: { scope },
    location: { origin: "http://127.0.0.1:4173" },
    skipWaiting() {},
    clients: { claim: async () => {} },
  };
  sandbox.globalThis = sandbox;

  const context = vm.createContext(sandbox);
  vm.runInContext(readFileSync(SW_PATH, "utf8"), context, { filename: "sw.js" });

  return { sandbox, context, listeners, cacheStorage, scope };
}

/** Call a top-level function declared inside sw.js. */
export function invoke(context, expression) {
  return vm.runInContext(expression, context);
}
