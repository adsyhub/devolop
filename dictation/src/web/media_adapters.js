"use strict";

// MEDIA-001. The player was hard-wired to one HTMLAudioElement: app.js read
// `elements.audio.currentTime`, called `elements.audio.pause()`, and listened for the
// element's own `timeupdate`. A course whose media is an online video can never be
// that element — but 精听 needs exactly the same five verbs from it: play, pause,
// seek, rate, clock.
//
// So every media source here implements ONE deliberately HTMLMediaElement-shaped
// interface, and app.js keeps the shape it already had. What differs between sources
// is not the interface but how much of it is honest, which is what `control` records:
//
//   "full"         play/pause/seek/rate all really work (YouTube IFrame API, Vimeo).
//   "seek-reload"  the site frames but exposes no API; seeking means rebuilding the
//                  iframe at a timestamp. Replay works, automatic looping does not.
//   "external"     the site refuses to be framed at all; only timestamped deep links.
//
// A lower tier must never be dressed up as a higher one. `canSeek` and `describe()`
// exist so the UI can tell the learner what this course can actually do, rather than
// showing a loop button that silently does nothing.

const MediaAdapters = (() => {

  const YT_STATE = { UNSTARTED: -1, ENDED: 0, PLAYING: 1, PAUSED: 2, BUFFERING: 3, CUED: 5 };

  // 101 and 150 are the same condition reported two ways: the uploader disabled
  // embedding. For a feature aimed at news channels this is not an edge case, it is
  // Tuesday — hence a real degrade path rather than an error toast.
  const YT_ERROR_MESSAGES = {
    2: "这个视频链接无效，播放器无法加载。",
    5: "浏览器的 HTML5 播放器无法播放这个视频。",
    100: "视频已被删除或设为私享。",
    101: "上传者禁止了站外嵌入播放，只能在原站观看。",
    150: "上传者禁止了站外嵌入播放，只能在原站观看。",
    153: "视频播放器安全来源校验失败（缺少或阻止了 Referer 来源标头）。",
  };

  const DEFAULT_API_TIMEOUT_MS = 20000;

  // YouTube accepts only a fixed set of rates and silently ignores anything else,
  // which would leave the speed selector showing 0.75x while the audio plays at 1x.
  const YT_FALLBACK_RATES = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

  // ---------------------------------------------------------------- pure helpers

  function formatClock(seconds) {
    const total = Math.max(0, Math.floor(Number(seconds) || 0));
    const minutes = Math.floor(total / 60);
    const rest = total % 60;
    return `${minutes}:${String(rest).padStart(2, "0")}`;
  }

  /** Whole seconds, truncated. Landing early keeps the first syllable; landing late clips it. */
  function wholeSeconds(seconds) {
    return Math.max(0, Math.floor(Number(seconds) || 0));
  }

  function youTubeEmbedSrc(videoId, options = {}) {
    const params = new URLSearchParams({
      enablejsapi: "1",
      rel: "0",
      // Never let the site draw its own captions: they would hand the learner the
      // exact answer the dictation exercise is asking them to write down.
      cc_load_policy: "0",
      iv_load_policy: "3",
      modestbranding: "1",
      playsinline: "1",
      disablekb: "1",
      controls: options.controls === false ? "0" : "1",
    });
    if (options.origin) {
      params.set("origin", options.origin);
      params.set("widget_referrer", options.origin);
    }
    if (Number.isFinite(options.start) && options.start > 0) {
      params.set("start", String(wholeSeconds(options.start)));
    }
    const host = options.host || "https://www.youtube-nocookie.com";
    return `${host}/embed/${encodeURIComponent(String(videoId || ""))}?${params.toString()}`;
  }

  function timestampUrl(pageUrl, provider, seconds) {
    const whole = wholeSeconds(seconds);
    const raw = String(pageUrl || "");
    if (!raw) return "";
    let url;
    try {
      url = new URL(raw);
    } catch {
      return raw;
    }
    if (provider === "youtube") {
      url.searchParams.set("t", `${whole}s`);
      return url.toString();
    }
    if (provider === "bilibili") {
      url.searchParams.set("t", String(whole));
      return url.toString();
    }
    if (provider === "vimeo") {
      url.hash = `t=${whole}s`;
      return url.toString();
    }
    return raw;
  }

  /**
   * Build the iframe src that starts a seek-reload player at a timestamp.
   *
   * The timestamp is absolute on the original video timeline. media.clip narrows
   * which part of the video a course covers; it never shifts the axis, so nothing
   * here subtracts clip.startTime — doing so is the bug that makes every seek in a
   * clipped course land clip.startTime seconds early.
   */
  function embedSrcAt(media, seconds) {
    const base = String((media && media.embedUrl) || "");
    if (!base) return "";
    const whole = wholeSeconds(seconds);
    let url;
    try {
      url = new URL(base);
    } catch {
      return base;
    }
    if (media.provider === "bilibili") {
      url.searchParams.set("t", String(whole));
      url.searchParams.set("autoplay", "1");
      return url.toString();
    }
    if (media.provider === "vimeo") {
      url.hash = `t=${whole}s`;
      return url.toString();
    }
    url.searchParams.set("start", String(whole));
    return url.toString();
  }

  // ------------------------------------------------------------- event plumbing

  class Emitter {
    constructor() {
      this._handlers = new Map();
    }
    on(name, handler) {
      if (typeof handler !== "function") return;
      if (!this._handlers.has(name)) this._handlers.set(name, new Set());
      this._handlers.get(name).add(handler);
    }
    off(name, handler) {
      const set = this._handlers.get(name);
      if (set) set.delete(handler);
    }
    emit(name, payload) {
      const set = this._handlers.get(name);
      if (!set) return;
      // Copy first: a handler that calls off() during dispatch must not corrupt
      // the iteration, which is exactly what destroy()-on-degrade does.
      for (const handler of Array.from(set)) {
        try {
          handler(payload);
        } catch (error) {
          if (typeof console !== "undefined") console.error("media adapter handler failed", error);
        }
      }
    }
    removeAll() {
      this._handlers.clear();
    }
  }

  // ------------------------------------------------------- local audio (unchanged)

  /**
   * A faithful pass-through of the <audio> element the player already used.
   *
   * This adapter must not add behaviour. Every local course in the library is a
   * regression test for it, and "the video feature changed how local audio behaves"
   * is the one outcome that would not be worth the feature.
   */
  class AudioElementAdapter extends Emitter {
    constructor(element) {
      super();
      this.kind = "audio";
      this.control = "full";
      this.canSeek = true;
      this.ready = true;
      this._element = element;
      this._rate = 1;
      this._forward = {};
      for (const name of ["timeupdate", "play", "pause", "ended", "error", "loadedmetadata"]) {
        this._forward[name] = () => {
          if (name === "play" || name === "loadedmetadata") {
            try {
              if (this._element && this._element.playbackRate !== this._rate) {
                this._element.playbackRate = this._rate;
              }
            } catch {}
          }
          this.emit(name);
        };
        element.addEventListener(name, this._forward[name]);
      }
    }
    get paused() { return this._element.paused; }
    get duration() { return Number(this._element.duration) || 0; }
    get currentTime() { return Number(this._element.currentTime) || 0; }
    set currentTime(value) { this._element.currentTime = Number(value) || 0; }
    get playbackRate() { return this._rate; }
    set playbackRate(value) {
      const rate = Number(value) || 1;
      this._rate = rate;
      try {
        if (this._element) {
          this._element.defaultPlaybackRate = rate;
          this._element.playbackRate = rate;
        }
      } catch {}
    }
    get availableRates() { return null; }
    seek(seconds) { this.currentTime = seconds; }
    async play() {
      try {
        if (this._element && this._element.playbackRate !== this._rate) {
          this._element.playbackRate = this._rate;
        }
        await this._element.play();
      } catch (error) {
        // AbortError: a newer play()/pause() interrupted this one — routine during
        // fast navigation. NotAllowedError: autoplay without a fresh user gesture.
        // Both are expected; anything else is a real failure worth surfacing.
        if (error && error.name !== "AbortError" && error.name !== "NotAllowedError") throw error;
      }
    }
    pause() { this._element.pause(); }
    externalUrlAt() { return ""; }
    describe() {
      return { kind: this.kind, control: this.control, canSeek: true, label: "本地音频" };
    }
    destroy() {
      for (const name of Object.keys(this._forward)) {
        this._element.removeEventListener(name, this._forward[name]);
      }
      this.removeAll();
    }
  }

  // ------------------------------------------------------------------- YouTube

  let youTubeApiPromise = null;

  /**
   * Load the IFrame Player API once per page.
   *
   * Chains onto any pre-existing window.onYouTubeIframeAPIReady instead of replacing
   * it: the API only ever calls one global, so clobbering another owner's callback
   * would leave their player permanently un-initialised.
   */
  function loadYouTubeApi(win, doc, timeoutMs) {
    if (win.YT && typeof win.YT.Player === "function") return Promise.resolve(win.YT);
    if (youTubeApiPromise) return youTubeApiPromise;

    youTubeApiPromise = new Promise((resolve, reject) => {
      const previous = win.onYouTubeIframeAPIReady;
      let settled = false;
      const timer = win.setTimeout(() => {
        if (settled) return;
        settled = true;
        youTubeApiPromise = null;
        reject(new Error("timeout"));
      }, timeoutMs);

      win.onYouTubeIframeAPIReady = () => {
        if (typeof previous === "function") {
          try { previous(); } catch { /* another owner's callback is not our problem */ }
        }
        if (settled) return;
        settled = true;
        win.clearTimeout(timer);
        resolve(win.YT);
      };

      const script = doc.createElement("script");
      script.src = "https://www.youtube.com/iframe_api";
      script.async = true;
      script.onerror = () => {
        if (settled) return;
        settled = true;
        win.clearTimeout(timer);
        youTubeApiPromise = null;
        reject(new Error("script"));
      };
      (doc.head || doc.body || doc.documentElement).appendChild(script);
    });
    return youTubeApiPromise;
  }

  class YouTubeAdapter extends Emitter {
    constructor(media, options = {}) {
      super();
      this.kind = "youtube";
      this.control = "full";
      this.canSeek = true;
      this.ready = false;
      this._media = media;
      this._paused = true;
      this._duration = Number(media.durationSec) || 0;
      this._rate = 1;
      this._rates = null;
      this._destroyed = false;
      this._rafHandle = null;
      this._lastTime = Number(media.clip && media.clip.startTime) || 0;

      const win = options.window || (typeof window !== "undefined" ? window : undefined);
      const doc = options.document || (win && win.document);
      this._win = win;
      // An injectable clock is what lets a node test step the timeupdate loop
      // without a browser; in production these are the real ones.
      this._raf = options.raf || ((fn) => win.requestAnimationFrame(fn));
      this._cancelRaf = options.cancelRaf || ((handle) => win.cancelAnimationFrame(handle));

      this._frame = doc.createElement("iframe");
      this._frame.src = youTubeEmbedSrc(media.videoId, {
        origin: options.origin || (win && win.location && win.location.origin) || "",
        controls: options.controls !== false,
        start: media.clip && media.clip.startTime,
      });
      this._frame.title = options.frameTitle || "视频播放器";
      this._frame.allow = "autoplay; encrypted-media; picture-in-picture";
      this._frame.setAttribute("allowfullscreen", "");
      this._frame.setAttribute("frameborder", "0");
      this._frame.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
      if (options.container) options.container.appendChild(this._frame);

      const loader = options.loadApi || ((timeout) => loadYouTubeApi(win, doc, timeout));
      loader(options.apiTimeoutMs || DEFAULT_API_TIMEOUT_MS).then(
        (YT) => this._attach(YT),
        (error) => this._degrade(
          error && error.message === "timeout" ? "api-timeout" : "api-blocked",
          "无法加载 YouTube 播放器组件（可能被网络或浏览器扩展拦截）。",
        ),
      );
    }

    _attach(YT) {
      if (this._destroyed) return;
      try {
        this._player = new YT.Player(this._frame, {
          events: {
            onReady: () => this._onReady(),
            onStateChange: (event) => this._onStateChange(event),
            onError: (event) => this._onError(event),
          },
        });
      } catch (error) {
        this._degrade("api-blocked", "YouTube 播放器初始化失败。");
      }
    }

    _onReady() {
      if (this._destroyed) return;
      this.ready = true;
      const duration = Number(this._player.getDuration && this._player.getDuration()) || 0;
      if (duration > 0) this._duration = duration;
      if (typeof this._player.getAvailablePlaybackRates === "function") {
        const rates = this._player.getAvailablePlaybackRates();
        if (Array.isArray(rates) && rates.length) this._rates = rates.slice();
      }
      this.emit("ready");
    }

    _onStateChange(event) {
      if (this._destroyed) return;
      const state = event && typeof event.data === "number" ? event.data : null;
      if (state === YT_STATE.PLAYING) {
        this._paused = false;
        this._startClock();
        this.emit("play");
      } else if (state === YT_STATE.PAUSED) {
        this._paused = true;
        this._stopClock();
        this._sampleTime();
        this.emit("pause");
      } else if (state === YT_STATE.ENDED) {
        this._paused = true;
        this._stopClock();
        this.emit("ended");
      }
    }

    _onError(event) {
      const code = event && typeof event.data === "number" ? event.data : 0;
      const message = YT_ERROR_MESSAGES[code] || "视频无法播放。";
      // Embedding refused, video gone, or unplayable — in every case the learner can
      // still study this course by opening the original page, so degrade rather than
      // strand them on a dead player.
      this._degrade(code === 101 || code === 150 ? "embedding-disabled" : `yt-error-${code}`, message);
    }

    _degrade(reason, message) {
      if (this._destroyed) return;
      this._stopClock();
      this.emit("degrade", { reason, message });
    }

    _startClock() {
      if (this._rafHandle !== null || this._destroyed) return;
      const tick = () => {
        // Re-check on every frame: a destroy() or pause() between scheduling and
        // firing must end the loop, or it keeps waking a backgrounded tab forever.
        if (this._destroyed || this._paused) {
          this._rafHandle = null;
          return;
        }
        this._sampleTime();
        this.emit("timeupdate");
        this._rafHandle = this._raf(tick);
      };
      this._rafHandle = this._raf(tick);
    }

    _stopClock() {
      if (this._rafHandle === null) return;
      try { this._cancelRaf(this._rafHandle); } catch { /* already gone */ }
      this._rafHandle = null;
    }

    _sampleTime() {
      if (!this._player || typeof this._player.getCurrentTime !== "function") return;
      const value = Number(this._player.getCurrentTime());
      if (Number.isFinite(value)) this._lastTime = value;
    }

    get paused() { return this._paused; }
    get duration() { return this._duration; }
    get currentTime() {
      this._sampleTime();
      return this._lastTime;
    }
    set currentTime(value) { this.seek(value); }
    get availableRates() { return this._rates ? this._rates.slice() : YT_FALLBACK_RATES.slice(); }
    get playbackRate() { return this._rate; }
    set playbackRate(value) {
      // Snap to a rate YouTube will actually honour. Setting an unsupported rate is
      // silently ignored by the API, which would leave the UI claiming 0.8x while
      // the audio plays at 1x — the learner would think their ears were the problem.
      //
      // Deliberately NOT nearest-neighbour: with YouTube's set, 0.8 is closer to 1.0
      // than to 0.75, so nearest would answer a request to slow down by not slowing
      // down at all. Never hand back a rate faster than the one asked for; fall back
      // to the slowest available only when the request is below every option.
      const wanted = Number(value) || 1;
      const allowed = this.availableRates.slice().sort((a, b) => a - b);
      const notFaster = allowed.filter((rate) => rate <= wanted + 1e-9);
      const snapped = notFaster.length ? notFaster[notFaster.length - 1] : allowed[0];
      this._rate = snapped;
      if (this._player && typeof this._player.setPlaybackRate === "function") {
        this._player.setPlaybackRate(snapped);
      }
    }

    seek(seconds) {
      const target = Math.max(0, Number(seconds) || 0);
      this._lastTime = target;
      if (this._player && typeof this._player.seekTo === "function") {
        this._player.seekTo(target, true);
      }
      this.emit("timeupdate");
    }

    async play() {
      if (this._player && typeof this._player.playVideo === "function") this._player.playVideo();
    }

    pause() {
      if (this._player && typeof this._player.pauseVideo === "function") this._player.pauseVideo();
      // Do not wait for onStateChange to stop the clock: a paused player that keeps
      // emitting timeupdate makes app.js's loop logic fire against a frozen time.
      this._paused = true;
      this._stopClock();
    }

    externalUrlAt(seconds) {
      return timestampUrl(this._media.pageUrl, this._media.provider, seconds);
    }

    describe() {
      return { kind: this.kind, control: this.control, canSeek: true, label: "在线视频 · 可完全控制" };
    }

    destroy() {
      this._destroyed = true;
      this._stopClock();
      if (this._player && typeof this._player.destroy === "function") {
        try { this._player.destroy(); } catch { /* the iframe may already be gone */ }
      }
      if (this._frame && this._frame.parentNode) this._frame.parentNode.removeChild(this._frame);
      this._player = null;
      this.removeAll();
    }
  }

  // --------------------------------------------------------------- seek-reload

  /**
   * A framed player with no control API: seeking means rebuilding the iframe.
   *
   * Everything this adapter cannot do, it reports as not doing. `paused` is always
   * true because the page genuinely does not know — and a `paused` that guessed
   * would make app.js's loop believe it was driving something.
   */
  class EmbedAdapter extends Emitter {
    constructor(media, options = {}) {
      super();
      this.kind = "embed";
      this.control = "seek-reload";
      this.canSeek = true;
      this.ready = true;
      this._media = media;
      this._time = Number(media.clip && media.clip.startTime) || 0;
      const doc = options.document || (typeof document !== "undefined" ? document : undefined);
      this._frame = doc.createElement("iframe");
      this._frame.src = embedSrcAt(media, this._time);
      this._frame.title = options.frameTitle || "视频播放器";
      this._frame.allow = "autoplay; encrypted-media; picture-in-picture";
      this._frame.setAttribute("allowfullscreen", "");
      this._frame.setAttribute("frameborder", "0");
      this._frame.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
      if (options.container) options.container.appendChild(this._frame);
    }
    get paused() { return true; }
    get duration() { return Number(this._media.durationSec) || 0; }
    get currentTime() { return this._time; }
    set currentTime(value) { this.seek(value); }
    get playbackRate() { return 1; }
    set playbackRate(_value) { /* the site owns its own speed control */ }
    get availableRates() { return null; }
    seek(seconds) {
      this._time = Math.max(0, Number(seconds) || 0);
      // Rebuilding the src IS the seek here. It restarts the player, which is why
      // the UI calls this "重播本句" rather than pretending it is a loop.
      this._frame.src = embedSrcAt(this._media, this._time);
      this.emit("timeupdate");
    }
    async play() { this.seek(this._time); }
    pause() { /* not expressible; the learner uses the site's own controls */ }
    externalUrlAt(seconds) {
      return timestampUrl(this._media.pageUrl, this._media.provider, seconds);
    }
    describe() {
      return { kind: this.kind, control: this.control, canSeek: true, label: "在线视频 · 只能重载定位" };
    }
    destroy() {
      if (this._frame && this._frame.parentNode) this._frame.parentNode.removeChild(this._frame);
      this.removeAll();
    }
  }

  // ----------------------------------------------------------------- external

  /** The site refuses framing. All that is left is an honest deep link per sentence. */
  class ExternalAdapter extends Emitter {
    constructor(media, options = {}) {
      super();
      this.kind = "external";
      this.control = "external";
      this.canSeek = false;
      this.ready = true;
      this._media = media || {};
      this._time = Number(this._media.clip && this._media.clip.startTime) || 0;
      this._reason = options.reason || "";
    }
    get paused() { return true; }
    get duration() { return Number(this._media.durationSec) || 0; }
    get currentTime() { return this._time; }
    set currentTime(value) { this.seek(value); }
    get playbackRate() { return 1; }
    set playbackRate(_value) { /* nothing to set */ }
    get availableRates() { return null; }
    get reason() { return this._reason; }
    seek(seconds) {
      this._time = Math.max(0, Number(seconds) || 0);
      this.emit("timeupdate");
    }
    async play() { /* only the learner can start it, in the other tab */ }
    pause() { /* likewise */ }
    externalUrlAt(seconds) {
      return timestampUrl(this._media.pageUrl, this._media.provider, seconds);
    }
    describe() {
      return { kind: this.kind, control: this.control, canSeek: false, label: "在线视频 · 需在原站播放" };
    }
    destroy() { this.removeAll(); }
  }

  // ------------------------------------------------------------------- factory

  /**
   * Pick the adapter a manifest earns — never the one it asks for.
   *
   * A manifest declaring control "full" for a provider we cannot actually drive
   * would produce a player with a loop button that does nothing, so the dispatch
   * below keys off what this code can really do, not off the declared tier alone.
   */
  function create(manifest, options = {}) {
    if (manifest && typeof manifest.audio === "string" && manifest.audio) {
      return new AudioElementAdapter(options.audioElement);
    }
    const media = (manifest && manifest.media) || {};
    if (media.provider === "youtube" && media.embedUrl) {
      return new YouTubeAdapter(media, options);
    }
    if (media.control === "seek-reload" && media.embedUrl) {
      return new EmbedAdapter(media, options);
    }
    return new ExternalAdapter(media, options);
  }

  /** Replace a degraded remote adapter with the external presentation, in place. */
  function externalFallback(media, reason) {
    return new ExternalAdapter(media, { reason });
  }

  return {
    create,
    externalFallback,
    AudioElementAdapter,
    YouTubeAdapter,
    EmbedAdapter,
    ExternalAdapter,
    youTubeEmbedSrc,
    timestampUrl,
    embedSrcAt,
    formatClock,
    wholeSeconds,
    YT_STATE,
    YT_ERROR_MESSAGES,
    YT_FALLBACK_RATES,
    DEFAULT_API_TIMEOUT_MS,
  };
})();

if (typeof module !== "undefined" && module.exports) module.exports = MediaAdapters;
if (typeof window !== "undefined") window.MediaAdapters = MediaAdapters;
