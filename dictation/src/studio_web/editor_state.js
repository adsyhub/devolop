"use strict";

/**
 * The editor's mutable state, in one named place.
 *
 * Two things share this object that are easy to confuse: `mode` / `course` /
 * `draft` say what the page is *showing*, while `analysisMode` / `batchAnalysis`
 * say what the server is *working on* — and those deliberately outlive a change
 * of target, so switching courses mid-batch does not cancel the batch.
 */
const EditorState = {
  /** Provider profiles, as the server reported them. */
  config: null,

  /** "course" | "draft" | "" while nothing is open. */
  mode: "",
  course: null,
  draft: null,
  draftPage: null,
  imageObjectUrl: "",

  /** 待复核列表 and the selection made on it. */
  reviewTargets: [],
  selectedTargetKeys: new Set(),
  multiQueue: [],
  multiIndex: 0,

  /** A server-side analysis, which outlives both this page and the open target. */
  analysisId: "",
  analysisMode: "single",
  batchAnalysis: null,
  analysisLogCursor: 0,
  analysisPolling: null,

  /** Stable identity of one review target, used as a selection key. */
  targetKey: (target) => `${target.targetKind}:${target.targetId}`,
};

if (typeof module !== "undefined" && module.exports) module.exports = EditorState;
if (typeof window !== "undefined") window.EditorState = EditorState;
