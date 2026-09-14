"use strict";

/**
 * The build page's mutable state, in one named place.
 *
 * It used to be a single `state` object that mixed the session token, the
 * provider config, pending uploads, the running job, the video probe and two
 * different polling timers — so any panel reading `state` was reading all of it,
 * and nothing recorded which fields belonged to which panel. The grouping below
 * is the only change: the fields and their meanings are unchanged.
 */
const StudioState = {
  /** Provider profiles and defaults, as the server reported them. */
  config: null,

  /** Uploaded-but-not-yet-built files, per pipeline. */
  uploads: { audio: [], pdf: [] },

  /** Which pipeline the form is currently showing. */
  source: "audio",

  /** The video pipeline's last probe result, or null. */
  probe: null,

  /** The build being watched, and the batch it belongs to. */
  jobId: null,
  batchId: null,
  batchJobs: [],
  logCursor: 0,
  polling: null,

  /** Local model service control. */
  localModelPolling: null,
  localModelRunning: false,
};

if (typeof module !== "undefined" && module.exports) module.exports = StudioState;
if (typeof window !== "undefined") window.StudioState = StudioState;
