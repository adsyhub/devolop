"use strict";

// Auto-purge outdated SW caches when running on localhost
if (typeof window !== "undefined" && (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost")) {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      for (const reg of registrations) reg.update();
    });
  }
}

const $ = (selector) => document.querySelector(selector);
const elements = {
  layout: $(".layout"),
  courseTitle: $("#course-title"),
  courseMeta: $("#course-meta"),
  languageBadge: $("#language-badge"),
  progressPercent: $("#progress-percent"),
  progressTrack: $("#progress-track"),
  progressFill: $("#progress-fill"),
  completedCount: $("#completed-count"),
  masteredCount: $("#mastered-count"),
  reviewCount: $("#review-count"),
  nextReviewButton: $("#next-review-button"),
  jumpLabel: $("#jump-label"),
  jumpInput: $("#jump-input"),
  jumpButton: $("#jump-button"),
  sidebarToggleButton: $("#sidebar-toggle-button"),
  libraryHomeButton: $("#library-home-button"),
  closeSidebarButton: $("#close-sidebar-button"),
  practiceCard: $("#practice-card"),
  dictationHeaderPane: $("#dictation-header-pane"),
  dictationFormPane: $("#dictation-form-pane"),
  dictationModeButton: $("#dictation-mode-button"),
  playbackModeButton: $("#playback-mode-button"),
  sentenceModeToggle: $("#sentence-mode-toggle"),
  sentenceModeDictation: $("#sentence-mode-dictation"),
  sentenceModeListen: $("#sentence-mode-listen"),
  sentencePosition: $("#sentence-position"),
  gradingMode: $("#grading-mode"),
  gradingControl: $("#grading-control"),
  accentModeOption: $("#accent-mode-option"),
  audio: $("#audio"),
  videoPanel: $("#video-panel"),
  videoFrame: $("#video-frame"),
  videoTierChip: $("#video-tier-chip"),
  videoHint: $("#video-hint"),
  videoNotice: $("#video-notice"),
  videoOpenLink: $("#video-open-link"),
  videoReplayButton: $("#video-replay-button"),
  blindToggle: $("#blind-toggle"),
  repeatSelect: $("#repeat-select"),
  playButton: $("#play-button"),
  playIcon: $("#play-icon"),
  waveform: $("#waveform"),
  seekRange: $("#seek-range"),
  currentTime: $("#current-time"),
  segmentTime: $("#segment-time"),
  loopButton: $("#loop-button"),
  speedSelect: $("#speed-select"),
  subtitlePanel: $("#subtitle-panel"),
  subtitlePosition: $("#subtitle-position"),
  subtitleShowTranslation: $("#subtitle-show-translation"),
  subtitleAutoscrollButton: $("#subtitle-autoscroll-button"),
  subtitleLocateButton: $("#subtitle-locate-button"),
  lyricsContainer: $("#lyrics-container"),
  lyricsList: $("#lyrics-list"),
  previousButton: $("#previous-button"),
  nextButton: $("#next-button"),
  sentenceDuration: $("#sentence-duration"),
  answerForm: $("#answer-form"),
  answerInput: $("#answer-input"),
  answerHelp: $("#answer-help"),
  hintButton: $("#hint-button"),
  hintLevel: $("#hint-level"),
  revealButton: $("#reveal-button"),
  checkButton: $("#check-button"),
  hintBox: $("#hint-box"),
  feedback: $("#feedback"),
  resultBadge: $("#result-badge"),
  feedbackTitle: $("#feedback-title"),
  score: $("#score"),
  hintUsage: $("#hint-usage"),
  expectedDiff: $("#expected-diff"),
  actualDiff: $("#actual-diff"),
  translation: $("#translation"),
  explanation: $("#explanation"),
  retryButton: $("#retry-button"),
  continueButton: $("#continue-button"),
  listenPanel: $("#listen-panel"),
  listenUnrevealedCard: $("#listen-unrevealed-card"),
  listenRevealedCard: $("#listen-revealed-card"),
  listenStatusText: $("#listen-status-text"),
  listenAutoReveal: $("#listen-auto-reveal"),
  listenRevealButton: $("#listen-reveal-button"),
  listenOriginalText: $("#listen-original-text"),
  listenSpeakButton: $("#listen-speak-button"),
  listenTranslation: $("#listen-translation"),
  listenExplanation: $("#listen-explanation"),
  listenAddVocabButton: $("#listen-add-vocab-button"),
  listenReplayButton: $("#listen-replay-button"),
  listenContinueButton: $("#listen-continue-button"),
  completionBanner: $("#completion-banner"),
  completionCopy: $("#completion-copy"),
  completionRestartButton: $("#completion-restart-button"),
  sessionBar: $("#session-bar"),
  sessionAttempts: $("#session-attempts"),
  sessionCorrect: $("#session-correct"),
  exitSpecialPracticeButton: $("#exit-special-practice-button"),
  fatalError: $("#fatal-error"),
  fatalErrorCopy: $("#fatal-error-copy"),
  shortcutButton: $("#shortcut-button"),
  shortcutDialog: $("#shortcut-dialog"),
  closeShortcutButton: $("#close-shortcut-button"),
  practiceHeading: $("#practice-heading"),
  streakChip: $("#streak-chip"),
  streakCount: $("#streak-count"),
  punchTodayDot: $("#punch-today-dot"),
  // The four personal modules share one dialog now; `personalDialog` is the
  // single surface, and `openPersonalCenter(tab)` picks which panel shows.
  personalDialog: $("#personal-dialog"),
  personalNavButton: $("#personal-nav-button"),
  personalNavBadge: $("#personal-nav-badge"),
  closePersonalButton: $("#close-personal-button"),
  personalTabs: Array.from(document.querySelectorAll("[data-personal-tab]")),
  personalPanels: Array.from(document.querySelectorAll("[data-personal-panel]")),
  personalStatus: $("#personal-status"),
  personalStatusText: $("#personal-status-text"),
  personalRetryButton: $("#personal-retry-button"),
  mistakesTotalBadge: $("#mistakes-total-badge"),
  vocabTotalBadge: $("#vocab-total-badge"),
  notesTotalBadge: $("#notes-total-badge"),
  moreButton: $("#more-button"),
  moreMenu: $("#more-menu"),
  starButton: $("#star-button"),
  notePopover: $("#note-popover"),
  noteStarCheckbox: $("#note-star-checkbox"),
  noteTextarea: $("#note-textarea"),
  noteCancelButton: $("#note-cancel-button"),
  noteSaveButton: $("#note-save-button"),
  addVocabButton: $("#add-vocab-button"),
  selectionBubble: $("#selection-bubble"),
  selectionAddVocabButton: $("#selection-add-vocab-button"),
  selectionAddNoteButton: $("#selection-add-note-button"),
  selectionAddButton: $("#selection-add-button"),
  vocabQuickadd: $("#vocab-quickadd"),
  vocabTermInput: $("#vocab-term-input"),
  vocabMeaningInput: $("#vocab-meaning-input"),
  vocabNoteInput: $("#vocab-note-input"),
  vocabQuickaddCancel: $("#vocab-quickadd-cancel"),
  vocabQuickaddSave: $("#vocab-quickadd-save"),
  notesCount: $("#notes-count"),
  notesScopeCurrent: $("#notes-scope-current"),
  notesScopeAll: $("#notes-scope-all"),
  notesSearchInput: $("#notes-search-input"),
  notesTagFilter: $("#notes-tag-filter"),
  notesFilterStarred: $("#notes-filter-starred"),
  notesExportButton: $("#notes-export-button"),
  notesExportMdButton: $("#notes-export-md-button"),
  notesList: $("#notes-list"),
  notesEmptyHint: $("#notes-empty-hint"),
  noteAddButton: $("#note-add-button"),
  noteAddForm: $("#note-add-form"),
  noteAddPosition: $("#note-add-position"),
  noteAddTag: $("#note-add-tag"),
  noteAddPreview: $("#note-add-preview"),
  noteAddText: $("#note-add-text"),
  noteAddStar: $("#note-add-star"),
  noteAddMessage: $("#note-add-message"),
  noteAddCancel: $("#note-add-cancel"),
  vocabCount: $("#vocab-count"),
  vocabTabAll: $("#vocab-tab-all"),
  vocabTabDue: $("#vocab-tab-due"),
  vocabTabNew: $("#vocab-tab-new"),
  vocabTabLearning: $("#vocab-tab-learning"),
  vocabTabMastered: $("#vocab-tab-mastered"),
  vocabBadgeAll: $("#vocab-badge-all"),
  vocabBadgeDue: $("#vocab-badge-due"),
  vocabBadgeNew: $("#vocab-badge-new"),
  vocabBadgeLearning: $("#vocab-badge-learning"),
  vocabBadgeMastered: $("#vocab-badge-mastered"),
  vocabSearchInput: $("#vocab-search-input"),
  vocabLevelFilter: $("#vocab-level-filter"),
  vocabTagFilter: $("#vocab-tag-filter"),
  flashcardStartButton: $("#flashcard-start-button"),
  vocabExportButton: $("#vocab-export-button"),
  vocabExportAnkiButton: $("#vocab-export-anki-button"),
  vocabImportButton: $("#vocab-import-button"),
  vocabBatchBar: $("#vocab-batch-bar"),
  vocabSelectAll: $("#vocab-select-all"),
  vocabSelectedCount: $("#vocab-selected-count"),
  vocabBatchMasterBtn: $("#vocab-batch-master-btn"),
  vocabBatchTagBtn: $("#vocab-batch-tag-btn"),
  vocabBatchResetBtn: $("#vocab-batch-reset-btn"),
  vocabBatchDeleteBtn: $("#vocab-batch-delete-btn"),
  vocabList: $("#vocab-list"),
  vocabEmptyHint: $("#vocab-empty-hint"),
  vocabAddButton: $("#vocab-add-button"),
  vocabAddForm: $("#vocab-add-form"),
  vocabAddTerm: $("#vocab-add-term"),
  vocabAddReading: $("#vocab-add-reading"),
  vocabAddLevel: $("#vocab-add-level"),
  vocabAddTags: $("#vocab-add-tags"),
  vocabAddMeaning: $("#vocab-add-meaning"),
  vocabAddNote: $("#vocab-add-note"),
  vocabAddLinkSentence: $("#vocab-add-link-sentence"),
  vocabAddLinkLabel: $("#vocab-add-link-label"),
  vocabAddMessage: $("#vocab-add-message"),
  vocabAddCancel: $("#vocab-add-cancel"),
  vocabAddSave: $("#vocab-add-save"),
  mistakesTabDictation: $("#mistakes-tab-dictation"),
  mistakesTabExam: $("#mistakes-tab-exam"),
  mistakesDictationBadge: $("#mistakes-dictation-badge"),
  mistakesExamBadge: $("#mistakes-exam-badge"),
  mistakesSummaryText: $("#mistakes-summary-text"),
  mistakesPracticeAllButton: $("#mistakes-practice-all-button"),
  mistakesList: $("#mistakes-list"),
  mistakesEmptyHint: $("#mistakes-empty-hint"),
  flashcardDialog: $("#flashcard-dialog"),
  closeFlashcardButton: $("#close-flashcard-button"),
  flashcardProgress: $("#flashcard-progress"),
  flashcard: $("#flashcard"),
  flashcardLevelChip: $("#flashcard-level-chip"),
  flashcardSpeakButton: $("#flashcard-speak-button"),
  flashcardTerm: $("#flashcard-term"),
  flashcardBack: $("#flashcard-back"),
  flashcardReading: $("#flashcard-reading"),
  flashcardMeaning: $("#flashcard-meaning"),
  flashcardNote: $("#flashcard-note"),
  flashcardSourceBox: $("#flashcard-source-box"),
  flashcardSource: $("#flashcard-source"),
  flashcardSourcePlayButton: $("#flashcard-source-play-button"),
  flashcardFlipRow: $("#flashcard-flip-row"),
  flashcardFlipButton: $("#flashcard-flip-button"),
  flashcardGradeActions: $("#flashcard-grade-actions"),
  flashcardGradeAgain: $("#flashcard-grade-again"),
  flashcardGradeHard: $("#flashcard-grade-hard"),
  flashcardGradeGood: $("#flashcard-grade-good"),
  flashcardGradeEasy: $("#flashcard-grade-easy"),
  srsGoodIntervalPreview: $("#srs-good-interval-preview"),
  srsEasyIntervalPreview: $("#srs-easy-interval-preview"),
  flashcardEmptyHint: $("#flashcard-empty-hint"),
  flashcardDone: $("#flashcard-done"),
  flashcardDoneStats: $("#flashcard-done-stats"),
  flashcardRestartButton: $("#flashcard-restart-button"),
  vocabImportDialog: $("#vocab-import-dialog"),
  closeVocabImportButton: $("#close-vocab-import-button"),
  vocabImportTextarea: $("#vocab-import-textarea"),
  vocabImportFile: $("#vocab-import-file"),
  vocabImportFileName: $("#vocab-import-file-name"),
  vocabImportMessage: $("#vocab-import-message"),
  vocabImportCancel: $("#vocab-import-cancel"),
  vocabImportSubmit: $("#vocab-import-submit"),
  statSrsNew: $("#stat-srs-new"),
  statSrsLearning: $("#stat-srs-learning"),
  statSrsReviewing: $("#stat-srs-reviewing"),
  statSrsMastered: $("#stat-srs-mastered"),
};

const VOCAB_STORAGE_KEY = "dictation-vocab:v1";
const ACTIVITY_STORAGE_KEY = "dictation-activity:v1";
const NOTES_ALL_STORAGE_KEY = "dictation-notes-all:v1";
const STUDY_LOGS_STORAGE_KEY = "dictation-study-logs:v1";
const SELECTION_VOCAB_CONTAINER_IDS = [
  "expected-diff",
  "translation",
  "explanation",
  "subtitle-text",
  "subtitle-translation",
  "listen-original-text",
  "listen-translation",
  "listen-explanation",
];

const flashcardState = { queue: [], current: null, flipped: false, totalThisRound: 0 };
let selectionAddPendingText = "";
let selectionAddPendingContext = null;

const LANGUAGE_PROFILES = {
  ja: { locale: "ja-JP", display: "日语", native: "日本語", placeholder: "ここに入力してください…", wordHints: false, latin: false },
  en: { locale: "en-US", display: "英语", native: "English", placeholder: "Type what you hear…", wordHints: true, latin: true },
  fr: { locale: "fr-FR", display: "法语", native: "Français", placeholder: "Écrivez ce que vous entendez…", wordHints: true, latin: true },
  ko: { locale: "ko-KR", display: "韩语", native: "한국어", placeholder: "들은 내용을 입력하세요…", wordHints: true, latin: false },
  es: { locale: "es-ES", display: "西班牙语", native: "Español", placeholder: "Escribe lo que escuchas…", wordHints: true, latin: true },
  de: { locale: "de-DE", display: "德语", native: "Deutsch", placeholder: "Gib ein, was du hörst…", wordHints: true, latin: true },
  it: { locale: "it-IT", display: "意大利语", native: "Italiano", placeholder: "Scrivi ciò che senti…", wordHints: true, latin: true },
  pt: { locale: "pt-BR", display: "葡萄牙语", native: "Português", placeholder: "Digite o que você ouve…", wordHints: true, latin: true },
  zh: { locale: "zh-CN", display: "中文", native: "中文", placeholder: "请输入你听到的内容…", wordHints: false, latin: false },
};

/* Lookup permissions and selection context for the listening workspace.
 * Declared here rather than inferred by the lookup panel (LEX-19, §11.2). */
window.LexLookupHost = {
  canLookup: () => true,
  getSelectionContext() {
    const sentence = state.manifest?.sentences?.[state.index] || null;
    return {
      hostType: "listening",
      courseId: state.manifest?.courseId || "",
      courseTitle: state.manifest?.title || "",
      sentenceId: sentence?.id || sentence?.sentenceId || "",
      sourceRevision: state.manifest?.contentRevision || state.manifest?.schemaVersion || "",
      text: sentence?.text || "",
      mode: state.sentenceMode || state.mode || "dictation",
    };
  },
};

const state = {
  manifest: null,
  // Set when the active course failed to load. The library still works; only
  // the practice view refuses.
  courseError: null,
  courseTitles: {},
  index: 0,
  mode: "dictation",
  sentenceMode: (() => {
    try {
      return localStorage.getItem("dictation_sentence_mode") || "dictation";
    } catch {
      return "dictation";
    }
  })(),
  listenRevealed: false,
  listenAutoReveal: (() => {
    try {
      return localStorage.getItem("dictation_auto_reveal") === "1";
    } catch {
      return false;
    }
  })(),
  subtitleIndex: -1,
  loop: false,
  // Video courses often burn the transcript into the frame. Start covered so a
  // first attempt remains listening practice; the learner can reveal it anytime.
  blindListening: true,
  awaitingSeekTo: null,
  // The standard 精听 drill the single loop toggle does not cover: play this
  // sentence N times, then stop, so the learner writes before hearing it again.
  repeatTarget: 1,
  repeatsPlayed: 0,
  playbackLoopSentenceIndex: null,
  composing: false,
  hintLevel: 0,
  attempts: 0,
  firstTryCorrect: 0,
  sentenceAttempts: 0,
  progress: {},
  practiceIndexes: [],
  // The immutable course universe and the currently active drill queue are
  // separate. A mistake drill must not change note numbering or analytics.
  coursePracticeIndexes: [],
  activeQueueKind: "course",
  storageKey: "",
  legacyStorageKeys: [],
  languageCode: "ja",
  vocab: [],
  selectedVocabIds: new Set(),
  vocabStatusFilter: "all",
  vocabLevelFilter: "",
  vocabTagFilter: "",
  notesByCourse: {},
  allNotes: [],
  notesScope: "current",
  notesTagFilter: "",
  notesStarredOnly: false,
  dictationMistakes: [],
  // JLPT wrong answers, pulled from /api/exams/<slug>/review. Kept separate from
  // dictationMistakes on purpose: two sources, one surface.
  examMistakes: [],
  mistakesScope: "dictation",
  activityDays: [],
  backendAvailable: false,
  autoScrollLyrics: true,
  showLyricsTranslation: true,
  isSeeking: false,
  sidebarCollapsed: (() => {
    try {
      return localStorage.getItem("dictation_sidebar_collapsed") === "1";
    } catch {
      return false;
    }
  })(),
};

/* Boot in two halves.
 *
 * The shell — nav, router, course library, personal centre — must come up even
 * when the active course is unopenable, because picking a different course is
 * exactly what a learner needs to do at that point. So a course failure is
 * caught and held: it degrades the practice view, not the whole page.
 */
let activeCourseLoadPromise = null;
let learningDataInitialized = false;

function routeNeedsCourse() {
  return location.hash === "#/practice";
}

async function ensureActiveCourseLoaded() {
  if (state.manifest) return state.manifest;
  if (activeCourseLoadPromise) return activeCourseLoadPromise;
  state.courseError = null;
  activeCourseLoadPromise = (async () => {
    try {
      await loadActiveCourse();
      if (learningDataInitialized && state.backendAvailable) {
        await Promise.all([loadNotesFromBackend(), loadProgressFromBackend()]);
      } else if (learningDataInitialized) {
        state.notesByCourse = loadStoredObject(notesStorageKey());
      }
      updateStarButtonUi();
      selectSentence(findFirstIncompleteIndex(), { focus: false, autoplay: false });
      registerOfflineCourse(state.manifest);
      return state.manifest;
    } catch (error) {
      state.courseError = error;
      throw error;
    } finally {
      activeCourseLoadPromise = null;
    }
  })();
  return activeCourseLoadPromise;
}

async function bootstrap() {
  createWaveform();
  bindEvents();
  updateSidebarUi();

  /* Put a view on screen before anything is awaited.
   *
   * Both views start hidden and `applyRoute` decides which one opens, so while
   * that call sat at the end of boot the whole page was hostage to the fetches
   * before it: one request that hung — not failed, hung — left a top bar floating
   * over nothing, with no way to reach the library and pick a different course,
   * and no error either, because nothing had thrown. The shell is not data; it
   * goes up first and the data fills it in. */
  applyRoute({ withData: false });

  if (routeNeedsCourse()) {
    try {
      await ensureActiveCourseLoaded();
    } catch {
      // The practice view reports the stored course error; the shell stays usable.
    }
  }

  // Vocabulary, notes and the backend probe are all optional decoration around a
  // course. None of them is worth losing the page over.
  try {
    await initLearningData();
  } catch (error) {
    console.warn("Learning data unavailable", error);
  }

  updatePersonalBadges();
  loadDictationMistakes()
    .then(updatePersonalBadges)
    .catch(() => { /* the badge just stays at what vocab knows */ });

  applyRoute();
}

/** Everything that depends on there being an openable course. */
async function loadActiveCourse() {
  const manifest = await fetchJson("./manifest.json");
  validateManifest(manifest);
  state.manifest = manifest;
  state.courseTitles[stableCourseId(manifest)] = String(manifest.title || stableCourseId(manifest));
  state.languageCode = manifestLanguageCode(manifest);
  state.coursePracticeIndexes = manifest.sentences
    .map((_, index) => index)
    .filter((index) => manifest.sentences[index].practiceEligible !== false);
  state.practiceIndexes = [...state.coursePracticeIndexes];
  state.activeQueueKind = "course";
  if (state.practiceIndexes.length === 0) {
    throw new Error("课程没有可练习的内容。请检查 practiceEligible 设置。");
  }
  state.storageKey = `dictation-progress:v2:${stableCourseId(manifest)}`;
  state.legacyStorageKeys = [
    `dictation-progress:v1:${legacyCourseId(manifest)}`,
    `dictation-progress:v1:${legacyTitleCourseId(manifest)}`,
  ];
  loadProgress();
  configureCourse();
  applyPendingPersonalJump();
}

function applyPendingPersonalJump() {
  const storageKey = "dictation-personal-jump:v1";
  try {
    const raw = sessionStorage.getItem(storageKey);
    if (!raw) return;
    const target = JSON.parse(raw);
    sessionStorage.removeItem(storageKey);
    if (!target || target.courseId !== stableCourseId(state.manifest)) return;
    const index = sentenceIndexForProgressKey(String(target.sentenceId || ""));
    if (index >= 0 && state.coursePracticeIndexes.includes(index)) {
      selectSentence(index, { focus: false, autoplay: false });
    }
  } catch {
    sessionStorage.removeItem(storageKey);
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`读取 ${url} 失败（HTTP ${response.status}）`);
  }
  try {
    return await response.json();
  } catch (error) {
    throw new Error(`课程 manifest 不是有效 JSON：${error.message}`);
  }
}

function manifestLanguageCode(manifest) {
  const raw = manifest?.sourceLanguage
    || manifest?.language?.code
    || manifest?.locales?.source
    || manifest?.locales?.transcript
    || "ja";
  const normalized = String(raw).trim().toLowerCase().replace("_", "-");
  const aliases = { jp: "ja", kr: "ko", cn: "zh" };
  const code = aliases[normalized] || normalized.split("-", 1)[0];
  if (!LANGUAGE_PROFILES[code]) {
    throw new Error(`课程语言「${raw}」尚未支持。`);
  }
  return code;
}

function currentLanguageProfile() {
  return LANGUAGE_PROFILES[state.languageCode] || LANGUAGE_PROFILES.ja;
}

function defaultAnswerHelpText() {
  return `${currentLanguageProfile().display}输入完成后按 Ctrl + Enter 检查`;
}

function speakText(text, lang = "") {
  if (!text || typeof window === "undefined" || !("speechSynthesis" in window)) return;
  try {
    window.speechSynthesis.cancel();
    const targetLang = lang || (state.languageCode === "ja" ? "ja-JP" : currentLanguageProfile().locale) || "ja-JP";
    const utterance = new SpeechSynthesisUtterance(String(text).trim());
    utterance.lang = targetLang;
    utterance.rate = 0.9;
    const voices = window.speechSynthesis.getVoices();
    const langPrefix = targetLang.split("-")[0].toLowerCase();
    const voice = voices.find((v) => v.lang.toLowerCase().startsWith(langPrefix)) || null;
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
  } catch (e) {
    console.warn("TTS playback failed", e);
  }
}

function calculateSm2Client(repetitions, interval, ease, grade) {
  const gradeStr = String(grade || "").toLowerCase();
  let nextReps = Number(repetitions) || 0;
  let nextInterval = Number(interval) || 0;
  let nextEase = Number(ease) || 2.5;
  let stage = 1;
  if (gradeStr === "again" || gradeStr === "1") {
    nextReps = 0;
    nextInterval = 1;
    nextEase = Math.max(1.3, nextEase - 0.2);
    stage = 1;
  } else if (gradeStr === "hard" || gradeStr === "2") {
    nextReps += 1;
    nextInterval = nextInterval > 0 ? Math.max(1, Math.round(nextInterval * 1.2)) : 1;
    nextEase = Math.max(1.3, nextEase - 0.15);
    stage = nextReps >= 3 ? 3 : 2;
  } else if (gradeStr === "good" || gradeStr === "3") {
    if (nextReps === 0) nextInterval = 1;
    else if (nextReps === 1) nextInterval = 3;
    else nextInterval = Math.max(1, Math.round(nextInterval * nextEase));
    nextReps += 1;
    stage = nextReps >= 3 ? 3 : 2;
  } else if (gradeStr === "easy" || gradeStr === "4") {
    if (nextReps === 0) nextInterval = 3;
    else if (nextReps === 1) nextInterval = 6;
    else nextInterval = Math.max(1, Math.round(nextInterval * nextEase * 1.3));
    nextReps += 1;
    nextEase = Math.min(3.5, nextEase + 0.15);
    stage = 3;
  }
  const nextDate = new Date();
  nextDate.setDate(nextDate.getDate() + nextInterval);
  return {
    repetitions: nextReps,
    interval: nextInterval,
    ease: Math.round(nextEase * 100) / 100,
    stage,
    nextReviewAt: nextDate.toISOString(),
  };
}

function sourceText(sentence, languageCode = state.languageCode) {
  if (languageCode === "ja" && String(sentence?.jaText || "").trim()) {
    return String(sentence.jaText).trim();
  }
  return String(sentence?.sourceText || sentence?.jaText || "").trim();
}

function translationText(sentence) {
  return String(sentence?.translationText || sentence?.zhTranslation || "").trim();
}

function validateManifest(manifest) {
  if (!manifest || manifest.schemaVersion !== 1) {
    throw new Error("只支持 schemaVersion 1 的课程包。请重新生成内容。");
  }
  if (!Array.isArray(manifest.sentences) || manifest.sentences.length === 0) {
    throw new Error("课程没有可练习的句子。");
  }
  // A course names its media exactly once: "audio" for a local file, "media" for an
  // online video that is never downloaded. Declaring both would leave the player
  // silently picking one while half the manifest described the other.
  const hasAudio = Object.prototype.hasOwnProperty.call(manifest, "audio");
  const hasMedia = Object.prototype.hasOwnProperty.call(manifest, "media");
  if (hasAudio && hasMedia) {
    throw new Error("课程同时声明了本地音档与在线视频，只能有一个。");
  }
  if (hasAudio) {
    if (
      typeof manifest.audio !== "string"
      || !manifest.audio.trim()
      || manifest.audio.includes("..")
      || manifest.audio.includes("/")
      || manifest.audio.includes("\\")
    ) {
      throw new Error("课程音档路径无效。");
    }
  } else if (hasMedia) {
    const media = manifest.media;
    if (!media || typeof media !== "object") {
      throw new Error("在线视频课程的 media 字段无效。");
    }
    if (!/^https:\/\//.test(String(media.pageUrl || ""))) {
      throw new Error("在线视频课程缺少有效的视频页面链接。");
    }
    if (media.control !== "external" && !/^https:\/\//.test(String(media.embedUrl || ""))) {
      throw new Error("这门在线视频课程标记为可嵌入播放，却没有嵌入地址。");
    }
  } else {
    throw new Error("课程既没有本地音档，也没有在线视频。");
  }
  const languageCode = manifestLanguageCode(manifest);
  manifest.sentences.forEach((sentence, index) => {
    const start = Number(sentence?.startTime);
    const end = Number(sentence?.endTime);
    if (!sentence || !Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end <= start) {
      throw new Error(`第 ${index + 1} 句的时间轴无效。`);
    }
    if (!sourceText(sentence, languageCode)) {
      throw new Error(`第 ${index + 1} 句没有原文答案。`);
    }
  });
}

function configureCourse() {
  const { manifest } = state;
  const profile = currentLanguageProfile();
  const total = state.practiceIndexes.length;
  const segments = manifest.sentences.length;
  elements.courseTitle.textContent = String(manifest.title || `${profile.display}听写课程`);
  elements.languageBadge.textContent = `${profile.native} · ${profile.display}`;
  const mediaLabel = manifest.media
    ? `在线视频 · ${String(manifest.media.provider || "原站")}`
    : "本地音频 · 可离线学习";
  elements.courseMeta.textContent = `${total} 个练习 · ${segments} 个音频片段 · ${profile.display} · ${mediaLabel}`;
  elements.practiceHeading.textContent = `听音频，输入你听到的${profile.display}`;
  elements.answerHelp.textContent = defaultAnswerHelpText();
  elements.answerInput.lang = profile.locale;
  elements.answerInput.placeholder = profile.placeholder;
  elements.answerInput.autocapitalize = profile.latin ? "sentences" : "off";
  elements.expectedDiff.lang = profile.locale;
  elements.actualDiff.lang = profile.locale;
  if (elements.noteAddPreview) elements.noteAddPreview.lang = profile.locale;
  if (elements.vocabAddTerm) elements.vocabAddTerm.lang = profile.locale;
  if (elements.vocabAddReading) elements.vocabAddReading.lang = profile.locale;
  if (elements.listenOriginalText) elements.listenOriginalText.lang = profile.locale;
  elements.accentModeOption.hidden = !profile.latin;
  elements.gradingMode.options[0].textContent = profile.latin
    ? "忽略大小写、空格与标点"
    : "忽略空格与标点";
  if (!profile.latin && elements.gradingMode.value === "accent-flexible") {
    elements.gradingMode.value = "forgiving";
  }
  document.title = `${manifest.title || profile.display} · 多语听写练习`;
  createMediaAdapter(manifest);
  elements.jumpInput.max = String(total);
  elements.nextReviewButton.disabled = true;
  renderLyricsList();
  updateProgressUi();
  updateSentenceModeUi();
}

// The one handle the whole player drives. For a local course it wraps the same
// <audio> element as before; for an online-video course it wraps a YouTube iframe,
// a reload-to-seek frame, or nothing at all. Its interface is deliberately
// HTMLMediaElement-shaped so every function below kept the shape it already had.
let media = null;

function isRemoteCourse() {
  return Boolean(state.manifest && state.manifest.media);
}

function currentMedia() {
  return (state.manifest && state.manifest.media) || null;
}

function createMediaAdapter(manifest) {
  if (media) media.destroy();
  media = MediaAdapters.create(manifest, {
    audioElement: elements.audio,
    container: elements.videoFrame,
    frameTitle: `${manifest.title || "课程"} 视频`,
  });
  if (elements.speedSelect) {
    const rate = Number(elements.speedSelect.value) || 1;
    media.playbackRate = rate;
  }
  bindMediaEvents();
  if (!isRemoteCourse()) {
    elements.audio.src = encodeURI(`./${manifest.audio}`);
  }
  configureVideoPanel();
}

function bindMediaEvents() {
  media.on("timeupdate", onAudioTimeUpdate);
  media.on("ready", updateTimelineUi);
  media.on("play", updatePlayState);
  media.on("pause", updatePlayState);
  media.on("error", () => showFatalError(new Error("媒体无法播放。请确认课程内容与网络。")));
  // A remote player that cannot start is not a fatal error: the learner can still
  // study the course through the original site, so swap in the external
  // presentation and say why, rather than throwing away the session.
  media.on("degrade", (detail) => degradeToExternal(detail));
}

function degradeToExternal(detail) {
  const source = currentMedia();
  if (!source || media.control === "external") return;
  const resumeTime = Number(media.currentTime) || Number(currentSentence()?.startTime) || 0;
  media.destroy();
  media = MediaAdapters.externalFallback(source, (detail && detail.reason) || "");
  bindMediaEvents();
  media.seek(resumeTime);
  configureVideoPanel();
  if (elements.videoNotice) {
    const reason = (detail && detail.reason) || "unknown";
    elements.videoNotice.textContent =
      `${(detail && detail.message) || "无法在页面内播放这个视频。"}`
      + `（原因代码：${reason}）`
      + " 你仍然可以按下方按钮到原站按时间点收听，练习进度不会丢失。";
    elements.videoNotice.hidden = false;
  }
}

/** Show the video panel a remote course needs, and nothing for a local one. */
function configureVideoPanel() {
  const panel = elements.videoPanel;
  if (!panel) return;
  if (!isRemoteCourse()) {
    panel.hidden = true;
    if (elements.practiceCard) elements.practiceCard.dataset.hasVideo = "false";
    return;
  }
  panel.hidden = false;
  if (elements.practiceCard) elements.practiceCard.dataset.hasVideo = "true";
  const described = media.describe();
  panel.dataset.control = described.control;
  if (elements.videoTierChip) elements.videoTierChip.textContent = "";
  if (elements.blindToggle) {
    // Blind listening is the pedagogically correct default for dictation: news
    // video routinely burns the answer into the picture as on-screen text.
    elements.blindToggle.hidden = described.control === "external";
    elements.blindToggle.disabled = described.control === "external";
  }
  if (elements.videoReplayButton) {
    elements.videoReplayButton.hidden = described.control !== "seek-reload";
  }
  if (elements.videoHint) {
    elements.videoHint.textContent = {
      "seek-reload": "这个站点没有开放播放接口：点「重播本句」会把播放器重新定位到该句开头。",
      "external": "这门课无法在页面内播放，请点击右上角按钮在原站打开收听。",
    }[described.control] || "";
    elements.videoHint.hidden = !elements.videoHint.textContent;
  }
  applyBlindMode();
  updateExternalLink();
}

function applyBlindMode() {
  if (!elements.videoPanel || !isRemoteCourse()) return;
  // Hidden picture, running sound: the <iframe> keeps playing while a wrapper
  // covers it, which is what makes this a listening exercise rather than a
  // reading one. Both dictation and full-text playback modes support blind listening.
  const blind = Boolean(state.blindListening);
  elements.videoPanel.classList.toggle("blind", blind);
  if (elements.blindToggle) {
    elements.blindToggle.classList.toggle("active", state.blindListening);
    elements.blindToggle.setAttribute("aria-pressed", String(state.blindListening));
    elements.blindToggle.textContent = state.blindListening ? "盲听中（点开画面）" : "盲听（遮住画面）";
  }
}

function updateExternalLink() {
  if (!elements.videoOpenLink || !isRemoteCourse()) return;
  const sentence = currentSentence();
  const at = Number(sentence?.startTime) || 0;
  const href = media.externalUrlAt(at);
  elements.videoOpenLink.href = href || "#";
  const source = currentMedia();
  const site = source && source.provider === "youtube" ? "YouTube" : "原站";
  elements.videoOpenLink.textContent = `在 ${site} 打开（${MediaAdapters.formatClock(at)}）`;
}

function bindEvents() {
  elements.dictationModeButton?.addEventListener("click", () => setLearningMode("dictation"));
  elements.playbackModeButton?.addEventListener("click", () => setLearningMode("playback"));
  elements.sentenceModeDictation?.addEventListener("click", () => setSentenceMode("dictation"));
  elements.sentenceModeListen?.addEventListener("click", () => setSentenceMode("listen"));
  elements.listenRevealButton?.addEventListener("click", revealListenAnswer);
  elements.listenAutoReveal?.addEventListener("change", (e) => setListenAutoReveal(e.target.checked));
  elements.listenSpeakButton?.addEventListener("click", () => {
    const sentence = currentSentence();
    if (sentence) speakText(sourceText(sentence));
  });
  elements.listenReplayButton?.addEventListener("click", () => playFromStart());
  elements.listenContinueButton?.addEventListener("click", () => navigate(1));
  elements.listenAddVocabButton?.addEventListener("click", () => {
    const sentence = currentSentence();
    openVocabQuickAdd({
      term: sourceText(sentence),
      meaning: translationText(sentence),
      sourceText: sourceText(sentence),
      anchor: elements.listenAddVocabButton,
    });
  });
  elements.playButton?.addEventListener("click", togglePlay);
  elements.loopButton?.addEventListener("click", () => {
    state.loop = !state.loop;
    elements.loopButton.classList.toggle("active", state.loop);
    elements.loopButton.setAttribute("aria-pressed", String(state.loop));
  });
  elements.speedSelect?.addEventListener("change", () => {
    media.playbackRate = Number(elements.speedSelect.value);
    // YouTube honours only a fixed set of rates, so show what was really applied
    // rather than what was asked for.
    const applied = String(media.playbackRate);
    if (elements.speedSelect.value !== applied
        && Array.from(elements.speedSelect.options).some((o) => o.value === applied)) {
      elements.speedSelect.value = applied;
    }
  });
  elements.blindToggle?.addEventListener("click", () => {
    state.blindListening = !state.blindListening;
    applyBlindMode();
  });
  elements.videoFrame?.addEventListener("click", () => {
    if (state.blindListening) {
      state.blindListening = false;
      applyBlindMode();
    }
  });
  elements.repeatSelect?.addEventListener("change", () => {
    state.repeatTarget = Math.max(1, Number(elements.repeatSelect.value) || 1);
    state.repeatsPlayed = 0;
  });
  elements.videoReplayButton?.addEventListener("click", () => {
    const sentence = currentSentence();
    if (sentence) media.seek(Number(sentence.startTime));
  });
  elements.seekRange?.addEventListener("input", seekWithinSegment);
  elements.seekRange?.addEventListener("change", finishSeeking);
  elements.seekRange?.addEventListener("pointerup", finishSeeking);
  elements.previousButton?.addEventListener("click", () => navigate(-1));
  elements.nextButton?.addEventListener("click", () => navigate(1));
  elements.subtitleShowTranslation?.addEventListener("change", (e) => toggleLyricsTranslation(e.target.checked));
  elements.subtitleAutoscrollButton?.addEventListener("click", toggleLyricsAutoScroll);
  elements.subtitleLocateButton?.addEventListener("click", locateActiveLyric);
  elements.sidebarToggleButton?.addEventListener("click", toggleSidebar);
  elements.closeSidebarButton?.addEventListener("click", () => setSidebarCollapsed(true));
  elements.answerForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.composing) checkAnswer(false);
  });
  elements.answerInput?.addEventListener("compositionstart", () => { state.composing = true; });
  elements.answerInput?.addEventListener("compositionend", () => { state.composing = false; });
  elements.hintButton?.addEventListener("click", showNextHint);
  elements.revealButton?.addEventListener("click", () => checkAnswer(true));
  elements.retryButton?.addEventListener("click", resetForRetry);
  elements.continueButton?.addEventListener("click", () => navigate(1));
  elements.completionRestartButton?.addEventListener("click", () => selectSentence(state.practiceIndexes[0]));
  elements.jumpButton?.addEventListener("click", jumpToSentence);
  elements.jumpInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") jumpToSentence();
  });
  elements.nextReviewButton?.addEventListener("click", jumpToNextReview);
  elements.shortcutButton?.addEventListener("click", () => elements.shortcutDialog.showModal());
  elements.closeShortcutButton?.addEventListener("click", () => elements.shortcutDialog.close());
  elements.shortcutDialog?.addEventListener("click", (event) => {
    if (event.target === elements.shortcutDialog) elements.shortcutDialog.close();
  });
  document.addEventListener("keydown", handleGlobalShortcut);
  document.addEventListener("keydown", handleAnswerFlowShortcut);
  bindLearningEvents();
}

function updateSidebarUi() {
  const isCollapsed = Boolean(state.sidebarCollapsed);
  elements.layout?.classList.toggle("sidebar-collapsed", isCollapsed);
  if (elements.sidebarToggleButton) {
    elements.sidebarToggleButton.classList.toggle("active", !isCollapsed);
    elements.sidebarToggleButton.setAttribute("aria-pressed", String(!isCollapsed));
  }
}

function setSidebarCollapsed(collapsed) {
  state.sidebarCollapsed = Boolean(collapsed);
  try {
    localStorage.setItem("dictation_sidebar_collapsed", state.sidebarCollapsed ? "1" : "0");
  } catch {}
  updateSidebarUi();
}

function toggleSidebar() {
  setSidebarCollapsed(!state.sidebarCollapsed);
}

function bindLearningEvents() {
  elements.starButton?.addEventListener("click", () => {
    openNotePopover(state.index, elements.starButton);
  });
  elements.noteCancelButton?.addEventListener("click", closeNotePopover);
  elements.noteSaveButton?.addEventListener("click", saveNoteFromPopover);

  elements.addVocabButton?.addEventListener("click", () => {
    const sentence = currentSentence();
    openVocabQuickAdd({
      term: sourceText(sentence),
      meaning: translationText(sentence),
      sourceText: sourceText(sentence),
      anchor: elements.addVocabButton,
    });
  });
  elements.vocabQuickaddCancel?.addEventListener("click", closeVocabQuickadd);
  elements.vocabQuickaddSave?.addEventListener("click", saveVocabQuickAdd);
  elements.selectionAddVocabButton?.addEventListener("mousedown", (event) => {
    event.preventDefault();
    const text = selectionAddPendingText;
    const ctx = selectionAddPendingContext;
    hideSelectionBubble();
    if (!text) return;
    openVocabQuickAdd({
      term: text,
      sourceText: ctx?.sourceText || text,
      sentenceId: ctx?.sentenceId,
      anchor: elements.selectionBubble || elements.selectionAddVocabButton,
    });
  });
  elements.selectionAddNoteButton?.addEventListener("mousedown", (event) => {
    event.preventDefault();
    const text = selectionAddPendingText;
    const ctx = selectionAddPendingContext;
    hideSelectionBubble();
    if (!text) return;
    openNotePopover(
      ctx?.sentenceIndex !== undefined ? ctx.sentenceIndex : state.index,
      elements.selectionBubble || elements.selectionAddNoteButton,
      `「${text}」: `,
    );
  });
  elements.selectionAddButton?.addEventListener("mousedown", (event) => {
    event.preventDefault();
    const text = selectionAddPendingText;
    const ctx = selectionAddPendingContext;
    hideSelectionBubble();
    if (!text) return;
    openVocabQuickAdd({
      term: text,
      sourceText: ctx?.sourceText || text,
      sentenceId: ctx?.sentenceId,
      anchor: elements.selectionBubble || elements.selectionAddButton,
    });
  });
  document.addEventListener("selectionchange", handleSelectionChange);

  document.addEventListener("mousedown", (event) => {
    if (
      !elements.notePopover.hidden
      && !elements.notePopover.contains(event.target)
      && event.target !== elements.starButton
      && !(event.target instanceof Element && event.target.closest(".lyric-star-btn, #selection-add-note-button"))
    ) {
      closeNotePopover();
    }
    if (
      !elements.vocabQuickadd.hidden
      && !elements.vocabQuickadd.contains(event.target)
      && !isVocabQuickaddTrigger(event.target)
    ) {
      closeVocabQuickadd();
    }
  });

  // 顶栏「更多」菜单：存储位置、快捷键、切换课程——都是低频设置，不占板块位。
  const closeMoreMenu = () => {
    if (!elements.moreMenu || elements.moreMenu.hidden) return;
    elements.moreMenu.hidden = true;
    elements.moreButton?.setAttribute("aria-expanded", "false");
  };
  elements.moreButton?.addEventListener("click", (event) => {
    event.stopPropagation();
    if (!elements.moreMenu) return;
    const willOpen = elements.moreMenu.hidden;
    elements.moreMenu.hidden = !willOpen;
    elements.moreButton.setAttribute("aria-expanded", String(willOpen));
  });
  elements.moreMenu?.addEventListener("click", (event) => {
    if (event.target.closest(".more-menu-item")) closeMoreMenu();
  });
  document.addEventListener("click", (event) => {
    if (!elements.moreMenu || elements.moreMenu.hidden) return;
    if (!event.target.closest(".more-wrap")) closeMoreMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMoreMenu();
  });

  // 「我的」板块入口。四个模块共用一个弹窗，导航按钮只负责挑面板。
  if (elements.personalNavButton?.tagName === "BUTTON") {
    elements.personalNavButton.addEventListener("click", () => openPersonalCenter());
  }
  elements.streakChip?.addEventListener("click", () => location.assign("./me#/analytics"));
  elements.closePersonalButton?.addEventListener("click", closePersonalCenter);
  elements.personalDialog?.addEventListener("click", (event) => {
    if (event.target === elements.personalDialog) closePersonalCenter();
  });
  elements.personalDialog?.addEventListener("close", () => {
    closeNoteAddForm();
    closeVocabAddForm();
    if (readPersonalHash()) {
      if (!routeBeneathPersonal && isStandalonePersonalPath()) {
        location.assign("./");
        return;
      }
      history.replaceState(null, "", routeBeneathPersonal || "./listening#/listening");
      routeBeneathPersonal = "";
      applyRoute({ withData: false });
    }
  });
  elements.personalTabs.forEach((tab) => {
    tab.addEventListener("click", () => openPersonalCenter(tab.dataset.personalTab));
    tab.addEventListener("keydown", (event) => {
      const keys = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End"];
      if (!keys.includes(event.key)) return;
      event.preventDefault();
      const current = elements.personalTabs.indexOf(tab);
      let next = current;
      if (event.key === "Home") next = 0;
      else if (event.key === "End") next = elements.personalTabs.length - 1;
      else if (["ArrowDown", "ArrowRight"].includes(event.key)) next = (current + 1) % elements.personalTabs.length;
      else next = (current - 1 + elements.personalTabs.length) % elements.personalTabs.length;
      const nextTab = elements.personalTabs[next];
      nextTab?.focus();
      if (nextTab?.dataset.personalTab) openPersonalCenter(nextTab.dataset.personalTab);
    });
  });
  elements.personalRetryButton?.addEventListener("click", () => refreshPersonalTab(activePersonalTab));
  window.addEventListener("hashchange", () => {
    if (!readPersonalHash() && elements.personalDialog?.open) closePersonalCenter();
    applyRoute();
  });

  // Notes module events
  elements.notesScopeCurrent?.addEventListener("click", () => setNotesScope("current"));
  elements.notesScopeAll?.addEventListener("click", () => setNotesScope("all"));
  elements.notesSearchInput?.addEventListener("input", renderNotesList);
  elements.notesTagFilter?.addEventListener("change", renderNotesList);
  elements.notesFilterStarred?.addEventListener("change", renderNotesList);
  elements.notesExportButton?.addEventListener("click", exportNotesCsv);
  elements.notesExportMdButton?.addEventListener("click", exportNotesMarkdown);
  elements.noteAddButton?.addEventListener("click", () => {
    if (elements.noteAddForm.hidden) openNoteAddForm();
    else closeNoteAddForm();
  });
  elements.noteAddCancel?.addEventListener("click", closeNoteAddForm);
  elements.noteAddPosition?.addEventListener("input", syncNoteAddTarget);
  elements.noteAddForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    saveNoteFromDialog();
  });

  // Vocab module events
  elements.vocabTabAll?.addEventListener("click", () => setVocabStatusFilter("all"));
  elements.vocabTabDue?.addEventListener("click", () => setVocabStatusFilter("due"));
  elements.vocabTabNew?.addEventListener("click", () => setVocabStatusFilter("new"));
  elements.vocabTabLearning?.addEventListener("click", () => setVocabStatusFilter("learning"));
  elements.vocabTabMastered?.addEventListener("click", () => setVocabStatusFilter("mastered"));
  elements.vocabLevelFilter?.addEventListener("change", (e) => {
    state.vocabLevelFilter = e.target.value;
    renderVocabList();
  });
  elements.vocabTagFilter?.addEventListener("change", (e) => {
    state.vocabTagFilter = e.target.value;
    renderVocabList();
  });
  elements.vocabSearchInput?.addEventListener("input", renderVocabList);
  elements.vocabSelectAll?.addEventListener("change", (e) => toggleVocabSelectAll(e.target.checked));
  elements.vocabBatchMasterBtn?.addEventListener("click", handleVocabBatchMaster);
  elements.vocabBatchTagBtn?.addEventListener("click", handleVocabBatchTag);
  elements.vocabBatchResetBtn?.addEventListener("click", handleVocabBatchReset);
  elements.vocabBatchDeleteBtn?.addEventListener("click", handleVocabBatchDelete);
  elements.vocabExportButton?.addEventListener("click", exportVocabCsv);
  elements.vocabExportAnkiButton?.addEventListener("click", exportVocabAnki);
  elements.vocabImportButton?.addEventListener("click", openVocabImportDialog);
  elements.closeVocabImportButton?.addEventListener("click", () => elements.vocabImportDialog?.close());
  elements.vocabImportCancel?.addEventListener("click", () => elements.vocabImportDialog?.close());
  elements.vocabImportFile?.addEventListener("change", handleVocabImportFileSelected);
  elements.vocabImportSubmit?.addEventListener("click", handleVocabImportSubmit);
  elements.vocabAddButton?.addEventListener("click", () => {
    if (elements.vocabAddForm.hidden) openVocabAddForm();
    else closeVocabAddForm();
  });
  elements.vocabAddCancel?.addEventListener("click", closeVocabAddForm);
  elements.vocabAddForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    saveVocabFromDialog();
  });

  // Mistakes module events
  elements.mistakesTabDictation?.addEventListener("click", () => setMistakesScope("dictation"));
  elements.mistakesTabExam?.addEventListener("click", () => setMistakesScope("exam"));
  elements.mistakesPracticeAllButton?.addEventListener("click", startMistakesPracticeQueue);
  elements.exitSpecialPracticeButton?.addEventListener("click", restoreCoursePracticeQueue);

  // Flashcards & SRS Review Events
  elements.flashcardStartButton?.addEventListener("click", () => startFlashcardSession("auto"));
  elements.flashcardRestartButton?.addEventListener("click", () => startFlashcardSession("auto"));
  elements.flashcardSpeakButton?.addEventListener("click", () => {
    if (flashcardState.current?.term) speakText(flashcardState.current.term);
  });
  elements.flashcardSourcePlayButton?.addEventListener("click", playFlashcardSourceAudio);
  elements.flashcardFlipButton?.addEventListener("click", flipFlashcard);
  elements.flashcardGradeAgain?.addEventListener("click", () => gradeFlashcardSrs("again"));
  elements.flashcardGradeHard?.addEventListener("click", () => gradeFlashcardSrs("hard"));
  elements.flashcardGradeGood?.addEventListener("click", () => gradeFlashcardSrs("good"));
  elements.flashcardGradeEasy?.addEventListener("click", () => gradeFlashcardSrs("easy"));
  elements.closeFlashcardButton?.addEventListener("click", () => elements.flashcardDialog?.close());
  elements.flashcardDialog?.addEventListener("click", (event) => {
    if (event.target === elements.flashcardDialog) elements.flashcardDialog.close();
  });

  document.addEventListener("keydown", (event) => {
    if (!elements.flashcardDialog.open) return;
    if (event.code === "Space") {
      event.preventDefault();
      flipFlashcard();
    } else if (event.key === "p" || event.key === "P" || event.key === "v" || event.key === "V") {
      event.preventDefault();
      if (flashcardState.current?.term) speakText(flashcardState.current.term);
    } else if (flashcardState.flipped) {
      if (event.key === "1") {
        event.preventDefault();
        gradeFlashcardSrs("again");
      } else if (event.key === "2") {
        event.preventDefault();
        gradeFlashcardSrs("hard");
      } else if (event.key === "3") {
        event.preventDefault();
        gradeFlashcardSrs("good");
      } else if (event.key === "4") {
        event.preventDefault();
        gradeFlashcardSrs("easy");
      }
    }
  });
}

function anyDialogOpen() {
  return Boolean(document.querySelector("dialog[open]"));
}

function handleAnswerFlowShortcut(event) {
  if (!state.manifest || anyDialogOpen()) return;
  if (event.key === "Escape") {
    if (closeAnyPopover()) {
      event.preventDefault();
      return;
    }
    if (state.mode === "dictation") {
      if (state.sentenceMode === "listen" && state.listenRevealed) {
        event.preventDefault();
        state.listenRevealed = false;
        renderListenPanel();
        return;
      }
      if (!elements.feedback.hidden && !state.composing) {
        event.preventDefault();
        resetForRetry();
      }
    }
    return;
  }
  if (state.mode !== "dictation") return;
  if (state.sentenceMode === "listen") {
    if (event.key === "Enter") {
      event.preventDefault();
      if (!state.listenRevealed) {
        revealListenAnswer();
      } else {
        navigate(1);
      }
    }
    return;
  }
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && !state.composing) {
    event.preventDefault();
    if (elements.feedback.hidden) checkAnswer(false);
    else navigate(1);
  }
}

function currentSentence() {
  return state.manifest.sentences[state.index];
}

function setLearningMode(mode, { resume = true } = {}) {
  if (!state.manifest || !["dictation", "playback"].includes(mode)) return;
  if (state.mode === mode) return;
  const wasPlaying = !media.paused;
  const currentAudioTime = Number(media.currentTime) || 0;
  media.pause();
  state.mode = mode;
  state.playbackLoopSentenceIndex = null;

  if (mode === "dictation") {
    const targetIndex = nearestPracticeIndex(currentAudioTime);
    selectSentence(targetIndex, { focus: false, autoplay: false });
  } else {
    if (sentenceIndexAtTime(currentAudioTime) === -1) {
      media.currentTime = Number(currentSentence().startTime);
    }
    state.subtitleIndex = -2;
    updateModeUi();
    renderLyricsList();
    syncSubtitleToTime(media.currentTime);
    updateTimelineUi();
    locateActiveLyric();
  }

  if (wasPlaying && resume) attemptPlay();
}

function setSentenceMode(mode) {
  if (!["dictation", "listen"].includes(mode)) return;
  state.sentenceMode = mode;
  try {
    localStorage.setItem("dictation_sentence_mode", mode);
  } catch {}
  updateSentenceModeUi();
  if (state.sentenceMode === "dictation") {
    elements.answerInput?.focus();
  }
}

function setListenAutoReveal(autoReveal) {
  state.listenAutoReveal = Boolean(autoReveal);
  try {
    localStorage.setItem("dictation_auto_reveal", state.listenAutoReveal ? "1" : "0");
  } catch {}
}

function updateSentenceModeUi() {
  const isPlayback = state.mode === "playback";
  const isListen = state.sentenceMode === "listen";

  elements.sentenceModeDictation?.classList.toggle("active", !isListen);
  elements.sentenceModeListen?.classList.toggle("active", isListen);
  elements.sentenceModeDictation?.setAttribute("aria-pressed", String(!isListen));
  elements.sentenceModeListen?.setAttribute("aria-pressed", String(isListen));

  if (elements.gradingControl) {
    elements.gradingControl.hidden = isPlayback || isListen;
  }

  if (elements.practiceHeading) {
    if (isPlayback) {
      elements.practiceHeading.textContent = "全文精听：边听音频，边看同步字幕与互动";
    } else if (isListen) {
      elements.practiceHeading.textContent = `听音频，理解句意后查看${currentLanguageProfile().display}原文`;
    } else {
      elements.practiceHeading.textContent = `听音频，输入你听到的${currentLanguageProfile().display}`;
    }
  }

  if (!isPlayback) {
    if (isListen) {
      if (elements.answerForm) elements.answerForm.hidden = true;
      if (elements.hintBox) elements.hintBox.hidden = true;
      if (elements.feedback) elements.feedback.hidden = true;
      if (elements.listenPanel) elements.listenPanel.hidden = false;
      renderListenPanel();
    } else {
      if (elements.listenPanel) elements.listenPanel.hidden = true;
      if (elements.answerForm) elements.answerForm.hidden = false;
      if (elements.hintBox) elements.hintBox.hidden = !elements.hintBox.textContent;
    }
  }
}

function renderListenPanel() {
  if (!elements.listenPanel || state.sentenceMode !== "listen") return;
  const sentence = currentSentence();
  if (!sentence) return;

  if (elements.listenAutoReveal) {
    elements.listenAutoReveal.checked = Boolean(state.listenAutoReveal);
  }

  if (state.listenRevealed) {
    if (elements.listenUnrevealedCard) elements.listenUnrevealedCard.hidden = true;
    if (elements.listenRevealedCard) elements.listenRevealedCard.hidden = false;

    const profile = currentLanguageProfile();
    if (elements.listenOriginalText) {
      elements.listenOriginalText.textContent = sourceText(sentence);
      elements.listenOriginalText.lang = profile.locale;
    }
    if (elements.listenTranslation) {
      elements.listenTranslation.textContent = translationText(sentence) || "本句暂无翻译。";
    }
    if (elements.listenExplanation) {
      elements.listenExplanation.textContent = String(sentence.explanationText || "本句暂无解析。建议先反复听辨。");
    }
    const position = state.practiceIndexes.indexOf(state.index);
    const total = state.practiceIndexes.length;
    if (elements.listenContinueButton) {
      elements.listenContinueButton.textContent = position === total - 1 ? "回到第一题" : "继续下一题";
    }
  } else {
    if (elements.listenUnrevealedCard) elements.listenUnrevealedCard.hidden = false;
    if (elements.listenRevealedCard) elements.listenRevealedCard.hidden = true;
  }
}

function revealListenAnswer() {
  if (state.mode !== "dictation" || state.sentenceMode !== "listen") return;
  state.listenRevealed = true;
  recordListenExposure();
  recordActivity();
  renderListenPanel();
  updateProgressUi();
}

function updateModeUi() {
  const playback = state.mode === "playback";
  elements.practiceCard.dataset.mode = state.mode;
  elements.dictationModeButton?.classList.toggle("active", !playback);
  elements.playbackModeButton?.classList.toggle("active", playback);
  elements.dictationModeButton?.setAttribute("aria-pressed", String(!playback));
  elements.playbackModeButton?.setAttribute("aria-pressed", String(playback));
  if (elements.gradingControl) elements.gradingControl.hidden = playback || state.sentenceMode === "listen";
  if (elements.loopButton) {
    elements.loopButton.hidden = playback || Boolean(media && media.control !== "full");
  }
  if (elements.repeatSelect && elements.repeatSelect.parentElement) {
    elements.repeatSelect.parentElement.hidden =
      playback || Boolean(media && media.control !== "full");
  }
  if (elements.subtitlePanel) elements.subtitlePanel.hidden = !playback;
  if (elements.dictationHeaderPane) elements.dictationHeaderPane.hidden = playback;
  if (elements.dictationFormPane) elements.dictationFormPane.hidden = playback;
  if (elements.answerForm) elements.answerForm.hidden = playback || state.sentenceMode === "listen";
  if (elements.hintBox) elements.hintBox.hidden = playback || state.sentenceMode === "listen" || !elements.hintBox.textContent;
  if (elements.feedback) elements.feedback.hidden = playback || state.sentenceMode === "listen" || elements.feedback.hidden;
  if (elements.listenPanel) elements.listenPanel.hidden = playback || state.sentenceMode !== "listen";
  if (elements.completionBanner) elements.completionBanner.hidden = playback || elements.completionBanner.hidden;
  if (elements.sessionBar) elements.sessionBar.hidden = playback;
  if (elements.jumpLabel) elements.jumpLabel.textContent = playback ? "跳至字幕" : "跳至句子";
  if (elements.jumpInput) {
    elements.jumpInput.max = String(playback ? state.manifest.sentences.length : state.practiceIndexes.length);
    elements.jumpInput.value = String(playback
      ? state.index + 1
      : Math.max(0, state.practiceIndexes.indexOf(state.index)) + 1);
  }
  updateSentenceModeUi();
  if (elements.seekRange) {
    elements.seekRange.setAttribute("aria-label", playback ? "整段音频播放位置" : "目前句子播放位置");
  }
  // Keep blind mode aligned with user preference in both dictation and playback.
  applyBlindMode();
  updatePlayState();
}

function selectSentence(index, { focus = true, autoplay = true } = {}) {
  state.mode = "dictation";
  state.listenRevealed = false;
  const total = state.practiceIndexes.length;
  const boundedIndex = Math.max(0, Math.min(state.manifest.sentences.length - 1, index));
  const requestedPosition = state.practiceIndexes.indexOf(boundedIndex);
  const position = requestedPosition === -1 ? 0 : requestedPosition;
  state.index = state.practiceIndexes[position];
  state.hintLevel = 0;
  state.sentenceAttempts = 0;
  state.repeatsPlayed = 0;
  state.awaitingSeekTo = null;
  const sentence = currentSentence();
  media.pause();
  media.currentTime = Number(sentence.startTime);
  elements.sentencePosition.textContent = `第 ${position + 1} 题，共 ${total} 题`;
  elements.jumpInput.value = String(position + 1);
  elements.previousButton.disabled = position === 0;
  elements.nextButton.disabled = position === total - 1;
  elements.continueButton.textContent = position === total - 1 ? "回到第一题" : "继续下一题";
  if (elements.listenContinueButton) {
    elements.listenContinueButton.textContent = position === total - 1 ? "回到第一题" : "继续下一题";
  }
  elements.sentenceDuration.textContent = `本句 ${formatTime(Number(sentence.endTime) - Number(sentence.startTime))}`;
  elements.segmentTime.textContent = formatTime(Number(sentence.endTime) - Number(sentence.startTime));
  state.sentenceStartTime = Date.now();
  clearExerciseUi();
  updateModeUi();
  updateTimelineUi();
  updateStarButtonUi();
  updateExternalLink();
  if (focus && state.sentenceMode === "dictation") elements.answerInput.focus();
  if (autoplay) attemptPlay();
}

function nearestPracticeIndex(time) {
  const activeIndex = sentenceIndexAtTime(time);
  if (state.practiceIndexes.includes(activeIndex)) return activeIndex;
  return state.practiceIndexes.reduce((best, index) => {
    const start = Number(state.manifest.sentences[index].startTime);
    const bestStart = Number(state.manifest.sentences[best].startTime);
    return Math.abs(start - time) < Math.abs(bestStart - time) ? index : best;
  }, state.practiceIndexes[0]);
}

function clearExerciseUi() {
  state.listenRevealed = false;
  elements.answerInput.value = "";
  elements.answerInput.disabled = false;
  elements.checkButton.disabled = false;
  elements.hintLevel.textContent = "0/3";
  elements.hintBox.hidden = true;
  elements.hintBox.textContent = "";
  elements.feedback.hidden = true;
  elements.completionBanner.hidden = true;
  elements.answerHelp.textContent = defaultAnswerHelpText();
  elements.expectedDiff.replaceChildren();
  elements.actualDiff.replaceChildren();
  if (elements.listenPanel) {
    if (elements.listenUnrevealedCard) elements.listenUnrevealedCard.hidden = false;
    if (elements.listenRevealedCard) elements.listenRevealedCard.hidden = true;
  }
  closeAnyPopover();
}

function navigate(delta) {
  if (!state.manifest || state.mode !== "dictation") return;
  const total = state.practiceIndexes.length;
  const currentPosition = Math.max(0, state.practiceIndexes.indexOf(state.index));
  let nextPosition = currentPosition + delta;
  if (nextPosition >= total) nextPosition = 0;
  if (nextPosition < 0) nextPosition = total - 1;
  selectSentence(state.practiceIndexes[nextPosition]);
}

async function attemptPlay() {
  try {
    await media.play();
  } catch (error) {
    // AbortError: a newer play()/pause() call interrupted this one — expected during fast navigation.
    // NotAllowedError: the browser blocked an autoplay attempt that lacked a fresh user gesture.
    // Both are safe to ignore; the play button remains available either way.
    if (error.name !== "AbortError" && error.name !== "NotAllowedError") {
      showFatalError(new Error(`无法开始播放：${error.message}`));
    }
  }
}

async function playFromStart() {
  const sentence = currentSentence();
  media.currentTime = Number(sentence.startTime);
  if (state.mode === "playback") syncSubtitleToTime(media.currentTime);
  await attemptPlay();
}

async function togglePlay() {
  if (!state.manifest) return;
  if (media.paused) {
    const now = media.currentTime;
    if (state.mode === "playback") {
      if (now >= playbackEndTime() - 0.03) media.currentTime = 0;
      syncSubtitleToTime(media.currentTime);
    } else {
      const sentence = currentSentence();
      if (now < Number(sentence.startTime) || now >= Number(sentence.endTime) - 0.03) {
        media.currentTime = Number(sentence.startTime);
      }
    }
    await attemptPlay();
  } else {
    media.pause();
  }
}

function onAudioTimeUpdate() {
  if (!state.manifest) return;
  if (state.mode === "playback") {
    if (state.playbackLoopSentenceIndex !== null && state.playbackLoopSentenceIndex !== undefined) {
      const loopSentence = state.manifest.sentences[state.playbackLoopSentenceIndex];
      if (loopSentence) {
        const loopStart = Number(loopSentence.startTime);
        const loopEnd = Number(loopSentence.endTime);
        if (media.currentTime >= loopEnd - 0.02 || media.currentTime < loopStart - 0.05) {
          media.currentTime = loopStart;
          if (media.paused) attemptPlay();
        }
      }
    } else if (media.currentTime >= playbackEndTime() - 0.02) {
      media.pause();
    }
    syncSubtitleToTime(media.currentTime);
    updateTimelineUi();
    return;
  }
  const sentence = currentSentence();
  const start = Number(sentence.startTime);
  const end = Number(sentence.endTime);

  // A remote player's clock is polled, not pushed, and its seek is asynchronous:
  // after asking it to jump back, the next few samples can still report the old
  // past-the-end time. Without this guard each of those samples would fire another
  // seek, and the sentence would stutter instead of looping.
  if (state.awaitingSeekTo !== null) {
    if (media.currentTime <= state.awaitingSeekTo + 0.5) state.awaitingSeekTo = null;
    else { updateTimelineUi(); return; }
  }

  if (media.currentTime >= end - endTolerance()) {
    state.repeatsPlayed += 1;
    const moreRepeats = state.repeatsPlayed < state.repeatTarget;
    if ((state.loop || moreRepeats) && !media.paused) {
      state.awaitingSeekTo = start;
      media.currentTime = start;
    } else {
      media.pause();
      media.currentTime = end;
      state.repeatsPlayed = 0;
      if (state.mode === "dictation" && state.sentenceMode === "listen" && state.listenAutoReveal && !state.listenRevealed) {
        revealListenAnswer();
      }
    }
  }
  updateTimelineUi();
}

/**
 * How close to the sentence end counts as reaching it.
 *
 * A local <audio> element pushes timeupdate about four times a second and its
 * currentTime is exact, so 20ms was always enough. A remote player is sampled from
 * requestAnimationFrame and its reported time can jump, so the boundary needs room
 * or the sentence overruns into the next one — which for dictation means hearing
 * the answer to the question you have not answered yet.
 */
function endTolerance() {
  return media && media.kind !== "audio" ? 0.12 : 0.02;
}

function updateTimelineUi() {
  if (!state.manifest) return;
  const sentence = currentSentence();
  const start = state.mode === "playback" ? 0 : Number(sentence.startTime);
  const end = state.mode === "playback" ? playbackEndTime() : Number(sentence.endTime);
  const duration = Math.max(0, end - start);
  const elapsed = Math.max(0, Math.min(duration, media.currentTime - start));
  const ratio = duration > 0 ? elapsed / duration : 0;
  if (!state.isSeeking) {
    if (elements.currentTime) elements.currentTime.textContent = formatTime(elapsed);
    if (elements.segmentTime) elements.segmentTime.textContent = formatTime(duration);
    if (elements.seekRange) elements.seekRange.value = String(Math.round(ratio * 1000));
    const bars = elements.waveform ? elements.waveform.children : [];
    for (let index = 0; index < bars.length; index += 1) {
      bars[index].classList.toggle("played", index / bars.length <= ratio);
    }
  }
}

function seekWithinSegment() {
  if (!state.manifest) return;
  state.isSeeking = true;
  const sentence = currentSentence();
  const start = state.mode === "playback" ? 0 : Number(sentence.startTime);
  const end = state.mode === "playback" ? playbackEndTime() : Number(sentence.endTime);
  const duration = Math.max(0, end - start);
  const ratio = Math.max(0, Math.min(1, Number(elements.seekRange.value) / 1000));
  const targetTime = start + duration * ratio;

  if (elements.currentTime) elements.currentTime.textContent = formatTime(duration * ratio);
  const bars = elements.waveform ? elements.waveform.children : [];
  for (let index = 0; index < bars.length; index += 1) {
    bars[index].classList.toggle("played", index / bars.length <= ratio);
  }

  media.currentTime = targetTime;
  if (state.mode === "playback") {
    syncSubtitleToTime(targetTime, { isSeeking: true });
  }
}

function finishSeeking() {
  if (!state.manifest || !state.isSeeking) return;
  state.isSeeking = false;
  const sentence = currentSentence();
  const start = state.mode === "playback" ? 0 : Number(sentence.startTime);
  const end = state.mode === "playback" ? playbackEndTime() : Number(sentence.endTime);
  const duration = Math.max(0, end - start);
  const ratio = Math.max(0, Math.min(1, Number(elements.seekRange.value) / 1000));
  const targetTime = start + duration * ratio;
  media.currentTime = targetTime;
  if (state.mode === "playback") {
    syncSubtitleToTime(targetTime, { forceScroll: true });
  }
  updateTimelineUi();
}

function renderLyricsList() {
  if (!elements.lyricsList || !state.manifest) return;
  const fragment = document.createDocumentFragment();
  const sentences = state.manifest.sentences || [];
  if (elements.subtitlePosition) {
    elements.subtitlePosition.textContent = `共 ${sentences.length} 句`;
  }

  sentences.forEach((sentence, index) => {
    const item = document.createElement("div");
    item.className = "lyric-item";
    item.dataset.index = String(index);
    item.id = `lyric-item-${index}`;

    const num = document.createElement("span");
    num.className = "lyric-index";
    num.textContent = String(index + 1).padStart(2, "0");

    const content = document.createElement("div");
    content.className = "lyric-content";

    const text = document.createElement("p");
    text.className = "lyric-text";
    text.textContent = sourceText(sentence);
    text.lang = currentLanguageProfile().locale;

    content.appendChild(text);

    const trans = translationText(sentence);
    if (trans) {
      const transEl = document.createElement("p");
      transEl.className = "lyric-translation";
      transEl.textContent = trans;
      if (!state.showLyricsTranslation) transEl.hidden = true;
      content.appendChild(transEl);
    }

    const actions = document.createElement("div");
    actions.className = "lyric-actions";

    const note = noteForSentence(index);
    const starred = Boolean(note?.starred);
    const hasText = Boolean(note?.text);

    const starBtn = document.createElement("button");
    starBtn.type = "button";
    starBtn.className = `lyric-action-btn lyric-star-btn${starred || hasText ? " active" : ""}`;
    starBtn.textContent = starred ? "★" : (hasText ? "✎" : "☆");
    starBtn.title = starred ? "已标为重点句（点击编辑笔记）" : (hasText ? "已有笔记（点击编辑）" : "标为重点句 / 写笔记");
    starBtn.setAttribute("aria-label", `第 ${index + 1} 句笔记与重点`);
    starBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openNotePopover(index, starBtn);
    });

    const vocabBtn = document.createElement("button");
    vocabBtn.type = "button";
    vocabBtn.className = "lyric-action-btn lyric-vocab-btn";
    vocabBtn.textContent = "📖";
    vocabBtn.title = "加入生词本（整句）";
    vocabBtn.setAttribute("aria-label", `将第 ${index + 1} 句加入生词本`);
    vocabBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openVocabQuickAdd({
        term: sourceText(sentence),
        meaning: translationText(sentence) || "",
        sourceText: sourceText(sentence),
        sentenceId: sentenceProgressKey(index),
        anchor: vocabBtn,
      });
    });

    const isLooping = state.playbackLoopSentenceIndex === index;
    const loopBtn = document.createElement("button");
    loopBtn.type = "button";
    loopBtn.className = `lyric-action-btn lyric-loop-btn${isLooping ? " active" : ""}`;
    loopBtn.textContent = isLooping ? "🔂" : "🔁";
    loopBtn.title = isLooping ? "正在单句循环（点击取消循环）" : "单句循环播放本句";
    loopBtn.setAttribute("aria-label", `单句循环播放第 ${index + 1} 句`);
    loopBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      togglePlaybackSentenceLoop(index);
    });

    const playBtn = document.createElement("button");
    playBtn.type = "button";
    playBtn.className = "lyric-action-btn lyric-play-btn";
    playBtn.textContent = "▶";
    playBtn.title = "播放本句";
    playBtn.setAttribute("aria-label", `播放第 ${index + 1} 句`);
    playBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      selectPlaybackSentence(index, { autoplay: true });
    });

    actions.append(starBtn, vocabBtn, loopBtn, playBtn);

    item.appendChild(num);
    item.appendChild(content);
    item.appendChild(actions);

    item.addEventListener("click", (e) => {
      if (e.target.closest(".lyric-action-btn")) return;
      const selection = window.getSelection();
      if (selection && selection.toString().trim().length > 0) {
        // User was highlighting/selecting text; do not jump playback.
        return;
      }
      selectPlaybackSentence(index, { autoplay: true });
    });

    fragment.appendChild(item);
  });

  elements.lyricsList.innerHTML = "";
  elements.lyricsList.appendChild(fragment);
}

function toggleLyricsTranslation(show) {
  state.showLyricsTranslation = Boolean(show);
  if (!elements.lyricsList) return;
  const translations = elements.lyricsList.querySelectorAll(".lyric-translation");
  translations.forEach((el) => {
    el.hidden = !state.showLyricsTranslation;
  });
}

function toggleLyricsAutoScroll() {
  state.autoScrollLyrics = !state.autoScrollLyrics;
  if (elements.subtitleAutoscrollButton) {
    elements.subtitleAutoscrollButton.classList.toggle("active", state.autoScrollLyrics);
    elements.subtitleAutoscrollButton.setAttribute("aria-pressed", String(state.autoScrollLyrics));
  }
  if (state.autoScrollLyrics) {
    locateActiveLyric();
  }
}

function locateActiveLyric() {
  if (state.subtitleIndex >= 0) {
    scrollLyricIntoView(state.subtitleIndex, { smooth: true, force: true });
  }
}

function scrollLyricIntoView(index, { smooth = true, force = false } = {}) {
  if (!elements.lyricsContainer || (!state.autoScrollLyrics && !force)) return;
  const item = document.getElementById(`lyric-item-${index}`);
  if (!item) return;

  const container = elements.lyricsContainer;
  const containerHeight = container.clientHeight;
  const itemTop = item.offsetTop;
  const itemHeight = item.offsetHeight;

  const targetScrollTop = itemTop - (containerHeight / 2) + (itemHeight / 2);

  if (smooth && !state.isSeeking) {
    container.scrollTo({
      top: Math.max(0, targetScrollTop),
      behavior: "smooth",
    });
  } else {
    container.scrollTop = Math.max(0, targetScrollTop);
  }
}

function syncSubtitleToTime(time, { isSeeking = false, forceScroll = false } = {}) {
  if (state.mode !== "playback" || !state.manifest) return;
  const exactIndex = sentenceIndexAtTime(time);
  let targetIndex = exactIndex !== -1 ? exactIndex : nearestSubtitleIndex(time);

  const total = state.manifest.sentences.length;
  const items = elements.lyricsList ? elements.lyricsList.children : [];
  if (total === 0 || items.length === 0) return;

  targetIndex = Math.max(0, Math.min(total - 1, targetIndex));
  const changed = targetIndex !== state.subtitleIndex;

  state.subtitleIndex = targetIndex;
  state.index = targetIndex;

  for (let i = 0; i < items.length; i += 1) {
    const it = items[i];
    if (i === targetIndex) {
      it.classList.add("active");
      it.classList.remove("passed");
    } else if (i < targetIndex) {
      it.classList.remove("active");
      it.classList.add("passed");
    } else {
      it.classList.remove("active");
      it.classList.remove("passed");
    }
  }

  const sentence = currentSentence();
  if (elements.sentencePosition) elements.sentencePosition.textContent = `全文精听 · 第 ${targetIndex + 1} 句，共 ${total} 句`;
  if (elements.subtitlePosition) elements.subtitlePosition.textContent = `第 ${targetIndex + 1} 句，共 ${total} 句`;
  if (elements.jumpInput) elements.jumpInput.value = String(targetIndex + 1);
  if (elements.sentenceDuration) elements.sentenceDuration.textContent = `本句 ${formatTime(Number(sentence.endTime) - Number(sentence.startTime))}`;
  if (elements.segmentTime) elements.segmentTime.textContent = formatTime(playbackEndTime());

  updateStarButtonUi();

  if (changed || forceScroll) {
    scrollLyricIntoView(targetIndex, { smooth: !isSeeking, force: forceScroll });
  }
}

function togglePlaybackSentenceLoop(index) {
  if (!state.manifest || state.mode !== "playback") return;
  if (state.playbackLoopSentenceIndex === index) {
    state.playbackLoopSentenceIndex = null;
  } else {
    state.playbackLoopSentenceIndex = index;
    selectPlaybackSentence(index, { autoplay: true, keepLoop: true });
  }
  updateLyricsLoopUi();
}

function updateLyricsLoopUi() {
  if (!elements.lyricsList) return;
  const items = elements.lyricsList.querySelectorAll(".lyric-item");
  items.forEach((item) => {
    const idx = Number(item.dataset.index);
    if (!Number.isInteger(idx)) return;
    const isLooping = state.playbackLoopSentenceIndex === idx;
    const loopBtn = item.querySelector(".lyric-loop-btn");
    if (loopBtn) {
      loopBtn.textContent = isLooping ? "🔂" : "🔁";
      loopBtn.classList.toggle("active", isLooping);
      loopBtn.setAttribute("aria-pressed", String(isLooping));
      loopBtn.title = isLooping ? "正在单句循环（点击取消循环）" : "单句循环播放本句";
    }
  });
}

function selectPlaybackSentence(index, { autoplay = true, keepLoop = false } = {}) {
  if (!state.manifest || state.mode !== "playback") return;
  const boundedIndex = Math.max(0, Math.min(state.manifest.sentences.length - 1, index));
  if (!keepLoop && state.playbackLoopSentenceIndex !== null && state.playbackLoopSentenceIndex !== boundedIndex) {
    state.playbackLoopSentenceIndex = null;
    updateLyricsLoopUi();
  }
  state.index = boundedIndex;
  state.subtitleIndex = -2;
  media.currentTime = Number(currentSentence().startTime);
  syncSubtitleToTime(media.currentTime, { forceScroll: true });
  updateTimelineUi();
  if (autoplay) attemptPlay();
}

function stepPlaybackSubtitle(delta) {
  if (!state.manifest || state.mode !== "playback") return;
  const targetIndex = Math.max(0, Math.min(state.manifest.sentences.length - 1, state.index + delta));
  selectPlaybackSentence(targetIndex);
}

function updatePlayState() {
  const playing = !media.paused;
  elements.playIcon.textContent = playing ? "Ⅱ" : "▶";
  if (state.mode === "playback") {
    elements.playButton.setAttribute("aria-label", playing ? "暂停整段音频" : "播放整段音频");
  } else {
    elements.playButton.setAttribute("aria-label", playing ? "暂停目前句子" : "播放目前句子");
  }
}

function playbackEndTime() {
  const audioDuration = Number(media.duration);
  if (Number.isFinite(audioDuration) && audioDuration > 0) return audioDuration;
  return state.manifest.sentences.reduce(
    (latest, sentence) => Math.max(latest, Number(sentence.endTime) || 0),
    0,
  );
}

function sentenceIndexAtTime(time) {
  const seconds = Number(time);
  if (!Number.isFinite(seconds)) return -1;
  let activeIndex = -1;
  state.manifest.sentences.forEach((sentence, index) => {
    const start = Number(sentence.startTime);
    const end = Number(sentence.endTime);
    if (start <= seconds + 0.015 && seconds < end - 0.015) activeIndex = index;
  });
  return activeIndex;
}

function nearestSubtitleIndex(time) {
  const activeIndex = sentenceIndexAtTime(time);
  if (activeIndex !== -1) return activeIndex;
  const nextIndex = state.manifest.sentences.findIndex((sentence) => Number(sentence.startTime) > time);
  return nextIndex === -1 ? state.manifest.sentences.length - 1 : nextIndex;
}

function createWaveform() {
  const fragment = document.createDocumentFragment();
  for (let index = 0; index < 64; index += 1) {
    const bar = document.createElement("i");
    const height = 20 + ((index * 37 + index * index * 11) % 74);
    bar.style.setProperty("--bar-height", `${height}%`);
    fragment.appendChild(bar);
  }
  elements.waveform.appendChild(fragment);
}

function showNextHint() {
  if (!state.manifest) return;
  state.hintLevel = Math.min(3, state.hintLevel + 1);
  const answer = sourceText(currentSentence());
  const profile = currentLanguageProfile();
  const hintData = buildHint(answer, state.hintLevel, profile.wordHints);
  elements.hintLevel.textContent = `${state.hintLevel}/3`;
  elements.hintBox.textContent = state.hintLevel < 3
    ? `提示 ${state.hintLevel}：${hintData.masked}`
    : `最后提示：共 ${hintData.unitCount} 个${profile.wordHints ? "词" : "字符"}，开头是「${hintData.opening}」。`;
  elements.hintBox.hidden = false;
}

function buildHint(answer, level, useWords) {
  return DictationScoring.buildHint(answer, level, useWords);
}

function checkAnswer(revealed) {
  const rawExpected = sourceText(currentSentence());
  const rawActual = String(elements.answerInput.value || "").trim();
  if (!revealed && !rawActual) {
    elements.answerInput.setAttribute("aria-invalid", "true");
    elements.hintBox.textContent = "请先输入你听到的内容，再检查答案。";
    elements.hintBox.hidden = false;
    elements.answerInput.focus();
    return;
  }
  elements.answerInput.removeAttribute("aria-invalid");
  state.attempts += 1;
  state.sentenceAttempts += 1;
  const mode = elements.gradingMode.value;
  const expected = normalizeAnswer(rawExpected, mode);
  const actual = normalizeAnswer(rawActual, mode);
  const scoringComparison = compareCharacters(expected, actual);
  const visualComparison = compareCharacters(rawExpected, rawActual);
  const correct = !revealed && expected === actual;
  const score = correct ? 100 : similarityPercent(expected, actual, scoringComparison.distance);
  if (correct && state.sentenceAttempts === 1) state.firstTryCorrect += 1;
  recordProgress(correct, revealed, score);
  recordActivity();
  renderFeedback({ rawExpected, rawActual, comparison: visualComparison, correct, revealed, score });
  const progressSummary = updateProgressUi();
  if (correct && progressSummary.mastered === progressSummary.total) {
    showCompletionBanner(progressSummary.total);
  }
  elements.sessionAttempts.textContent = String(state.attempts);
  elements.sessionCorrect.textContent = String(state.firstTryCorrect);
}

function renderFeedback({ rawExpected, rawActual, comparison, correct, revealed, score }) {
  elements.feedback.hidden = false;
  elements.feedback.scrollIntoView({ behavior: "smooth", block: "nearest" });
  elements.resultBadge.classList.toggle("correct", correct);
  if (correct) {
    elements.resultBadge.textContent = "答对了";
    elements.feedbackTitle.textContent = "很好，你完整听懂了";
  } else if (revealed) {
    elements.resultBadge.textContent = "已揭晓";
    elements.feedbackTitle.textContent = "先理解答案，再重听一次";
  } else {
    elements.resultBadge.textContent = "再听一次";
    elements.feedbackTitle.textContent = score >= 75 ? "很接近，修正标记处即可" : "拆小一点，逐段再听一次";
  }
  elements.score.textContent = `${score}%`;
  elements.answerHelp.textContent = "按 Ctrl + Enter 继续下一句 · Esc 清空再试";
  elements.retryButton.classList.toggle("primary-button", !correct);
  elements.retryButton.classList.toggle("secondary-button", correct);
  elements.continueButton.classList.toggle("primary-button", correct);
  elements.continueButton.classList.toggle("secondary-button", !correct);
  if (revealed) {
    elements.hintUsage.hidden = false;
    elements.hintUsage.textContent = "这次是直接看的答案，还不算独立听懂——建议稍后清空再挑战一次这句。";
  } else if (state.hintLevel > 0) {
    elements.hintUsage.hidden = false;
    elements.hintUsage.textContent = `本次使用了 ${state.hintLevel}/3 次提示。`;
  } else {
    elements.hintUsage.hidden = true;
    elements.hintUsage.textContent = "";
  }
  renderDiff(elements.expectedDiff, comparison.operations, "expected", rawExpected);
  renderDiff(elements.actualDiff, comparison.operations, "actual", rawActual || "（未输入）");
  const sentence = currentSentence();
  elements.translation.textContent = translationText(sentence) || "本句暂无翻译。";
  elements.explanation.textContent = String(sentence.explanationText || "本句暂无解析。建议先反复听辨。");
}

function normalizeAnswer(value, mode) {
  return DictationScoring.normalizeAnswer(value, mode, currentLanguageProfile());
}

function compareCharacters(expected, actual) {
  return DictationScoring.compareCharacters(expected, actual);
}

function renderDiff(container, operations, side, fallback) {
  container.replaceChildren();
  const hasVisible = operations.some((operation) => operation[side]);
  if (!hasVisible) {
    const span = document.createElement("span");
    span.className = "diff-placeholder";
    span.textContent = fallback;
    container.appendChild(span);
    return;
  }
  operations.forEach((operation) => {
    const value = operation[side];
    if (!value) return;
    const span = document.createElement("span");
    if (operation.type === "match") span.className = "diff-match";
    else if (side === "expected") span.className = "diff-missing";
    else span.className = "diff-extra";
    span.textContent = value;
    container.appendChild(span);
  });
}

function similarityPercent(expected, actual, distance) {
  return DictationScoring.similarityPercent(expected, actual, distance);
}

function recordProgress(correct, revealed, score) {
  const key = sentenceProgressKey(state.index);
  state.progress[key] = ProgressModel.applyAttempt(state.progress[key], { correct, revealed, score });
  saveProgress();
  const courseId = stableCourseId(state.manifest);
  const durationMs = state.sentenceStartTime ? Math.max(0, Date.now() - state.sentenceStartTime) : 0;
  if (state.backendAvailable) {
    const apiProgress = ProgressModel.toApi(state.progress[key]);
    backendRequest("POST", "./api/progress", {
      courseId,
      sentenceId: key,
      ...apiProgress,
      // Single-row POST counts one new attempt; batch sync carries absolute totals.
      attempts: 1,
    });
  }
  const logId = `local_log_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const logPayload = {
    id: logId,
    courseId,
    sentenceId: key,
    userInput: String(elements.answerInput?.value || ""),
    isCorrect: Boolean(correct),
    score,
    durationMs,
    hintCount: state.hintLevel || 0,
    mode: state.mode || "dictation",
    localDay: todayIso(),
    createdAt: new Date().toISOString(),
  };
  const cachedLogs = loadStoredArray(STUDY_LOGS_STORAGE_KEY);
  saveStoredValue(STUDY_LOGS_STORAGE_KEY, [logPayload, ...cachedLogs].slice(0, 5000));
  syncLearningMutation("POST", "./api/study-log", logPayload, {
    entityType: "studyLog",
    entityKey: logId,
  });
}

function recordListenExposure() {
  const key = sentenceProgressKey(state.index);
  state.progress[key] = ProgressModel.recordExposure(state.progress[key]);
  saveProgress();
  if (state.backendAvailable) {
    backendRequest("POST", "./api/progress/exposure", {
      courseId: stableCourseId(state.manifest),
      sentenceId: key,
      updatedAt: state.progress[key].updatedAt,
    });
  }
}

function loadProgress() {
  state.progress = ProgressModel.normalizeMap(loadStoredObject(state.storageKey));
  if (Object.keys(state.progress).length > 0) return;

  for (const legacyKey of [...new Set(state.legacyStorageKeys)]) {
    const legacy = loadStoredObject(legacyKey);
    const migrated = {};
    Object.entries(legacy).forEach(([rawIndex, entry]) => {
      const index = Number(rawIndex);
      if (Number.isInteger(index) && state.practiceIndexes.includes(index) && entry && typeof entry === "object") {
        migrated[sentenceProgressKey(index)] = ProgressModel.normalize(entry);
      }
    });
    if (Object.keys(migrated).length > 0) {
      state.progress = migrated;
      saveProgress();
      return;
    }
  }
}

function loadStoredObject(key) {
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "{}");
    return saved && typeof saved === "object" && !Array.isArray(saved) ? saved : {};
  } catch {
    return {};
  }
}

function saveProgress() {
  try {
    localStorage.setItem(state.storageKey, JSON.stringify(state.progress));
  } catch {
    // Practice remains usable in private browsing or storage-denied contexts.
  }
}

function updateProgressUi() {
  if (!state.manifest) return;
  const total = state.practiceIndexes.length;
  const entries = state.practiceIndexes
    .map((index) => state.progress[sentenceProgressKey(index)])
    .filter(Boolean);
  const completed = entries.filter((entry) => Number(entry?.attempts || 0) > 0).length;
  const mastered = entries.filter((entry) => Boolean(entry?.correct)).length;
  const reviewIndexes = state.practiceIndexes.filter((index) =>
    ProgressModel.isDue(state.progress[sentenceProgressKey(index)]));
  const percent = Math.round((mastered / total) * 100);
  elements.progressPercent.textContent = `${percent}%`;
  elements.progressFill.style.width = `${percent}%`;
  elements.progressTrack.setAttribute("aria-valuenow", String(percent));
  elements.completedCount.textContent = String(completed);
  elements.masteredCount.textContent = String(mastered);
  elements.reviewCount.textContent = String(reviewIndexes.length);
  elements.nextReviewButton.disabled = reviewIndexes.length === 0;
  return { total, mastered };
}

function showCompletionBanner(total) {
  elements.completionCopy.textContent = `恭喜，全部 ${total} 句都已经独立听懂并答对。可以换一门课程，或回到第一题再巩固一遍。`;
  elements.completionBanner.hidden = false;
}

function findFirstIncompleteIndex() {
  if (!state.manifest) return 0;
  return state.practiceIndexes.find((index) => {
    const entry = state.progress[sentenceProgressKey(index)];
    return !entry?.correct || ProgressModel.isDue(entry);
  })
    ?? state.practiceIndexes[0];
}

function resetForRetry() {
  elements.answerInput.disabled = false;
  elements.checkButton.disabled = false;
  elements.answerInput.value = "";
  elements.feedback.hidden = true;
  elements.completionBanner.hidden = true;
  elements.answerHelp.textContent = defaultAnswerHelpText();
  state.sentenceStartTime = Date.now();
  elements.answerInput.focus();
  playFromStart();
}

function jumpToSentence() {
  if (!state.manifest) return;
  const requested = Number(elements.jumpInput.value);
  const total = state.mode === "playback" ? state.manifest.sentences.length : state.practiceIndexes.length;
  if (!Number.isInteger(requested) || requested < 1 || requested > total) {
    elements.jumpInput.focus();
    return;
  }
  if (state.mode === "playback") selectPlaybackSentence(requested - 1);
  else selectSentence(state.practiceIndexes[requested - 1]);
}

function jumpToNextReview() {
  const reviewIndexes = state.practiceIndexes.filter((index) =>
    ProgressModel.isDue(state.progress[sentenceProgressKey(index)]));
  const next = reviewIndexes.find((index) => index > state.index) ?? reviewIndexes[0];
  if (Number.isInteger(next)) {
    if (state.mode === "playback") setLearningMode("dictation", { resume: false });
    selectSentence(next);
  }
}

function handleGlobalShortcut(event) {
  if (!state.manifest || anyDialogOpen()) return;
  const target = event.target;
  const editing = target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement;
  if (editing || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.code === "Space") {
    event.preventDefault();
    togglePlay();
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    if (state.mode === "playback") stepPlaybackSubtitle(-1);
    else navigate(-1);
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    if (state.mode === "playback") stepPlaybackSubtitle(1);
    else navigate(1);
  } else if (event.key.toLowerCase() === "h" && state.mode === "dictation") {
    event.preventDefault();
    showNextHint();
  } else if (event.key.toLowerCase() === "r") {
    event.preventDefault();
    playFromStart();
  } else if (event.key.toLowerCase() === "l" && state.mode === "dictation") {
    event.preventDefault();
    state.loop = !state.loop;
    elements.loopButton?.classList.toggle("active", state.loop);
    elements.loopButton?.setAttribute("aria-pressed", String(state.loop));
  }
}

function stableCourseId(manifest) {
  if (!manifest) return "";
  if (typeof manifest.courseId === "string" && manifest.courseId) return manifest.courseId;
  return legacyCourseId(manifest);
}

function legacyCourseId(manifest) {
  const sourceHash = manifest.buildMetadata?.sourceAudioSha256;
  if (sourceHash) return sourceHash.slice(0, 24);
  return legacyTitleCourseId(manifest);
}

function legacyTitleCourseId(manifest) {
  const value = `${manifest.title}|${manifest.audio}|${manifest.sentences.length}`;
  let hash = 2166136261;
  for (const character of value) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
}

function sentenceProgressKey(index) {
  const sentenceId = state.manifest?.sentences?.[index]?.id;
  return typeof sentenceId === "string" && sentenceId ? sentenceId : `legacy:${index}`;
}

async function registerOfflineCourse(manifest) {
  if (!("serviceWorker" in navigator) || !window.isSecureContext) return;
  try {
    const registration = await navigator.serviceWorker.register("./sw.js", { scope: "./" });
    const worker = registration.active || registration.waiting || registration.installing;
    const message = {
      type: "CACHE_COURSE",
      courseId: stableCourseId(manifest),
      revision: manifest.contentRevision || "legacy",
      audio: manifest.audio || "",
    };
    if (worker?.state === "activated") worker.postMessage(message);
    else if (worker) worker.addEventListener("statechange", () => {
      if (worker.state === "activated") worker.postMessage(message);
    });
  } catch {
    // The online player remains usable when service workers are unavailable.
  }
}

// ---------------------------------------------------------------------------
// Local-first learning data: vocab notebook, per-sentence notes, study streak.
// `localStorage` is always written to and is the only required store. When this
// page happens to be served by `serve_course.py` (same-origin `/api/*`), writes
// are also mirrored to its local SQLite backend so the notebook can span course
// previews instead of being siloed per static-site origin. See local_backend.py.
// ---------------------------------------------------------------------------

// SEC-001. Every /api/* call carries a session token the server minted at
// startup. The page obtains it once, over a same-origin request the server gates
// on its own bind address, and keeps it in memory only: not in localStorage (any
// script on the origin could read it back later), not in a URL (browser history,
// access logs), and not in Cache Storage (sw.js explicitly bypasses this path).
// A page reached through DNS rebinding fails the server's Host check and never
// gets a token at all.
let sessionToken = "";

async function acquireSessionToken() {
  try {
    const response = await fetch("./api/session/bootstrap", { cache: "no-store" });
    if (!response.ok) return "";
    const data = await response.json().catch(() => null);
    return typeof data?.token === "string" ? data.token : "";
  } catch {
    return "";
  }
}

function apiHeaders(extra) {
  const headers = new Headers(extra || undefined);
  if (sessionToken) headers.set("X-Dictation-Token", sessionToken);
  return headers;
}

async function apiFetch(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", ...options, headers: apiHeaders(options.headers) });
  // The server restarts with a fresh token, so a token from a previous run is
  // rejected. Re-handshake once and retry rather than degrading to "no backend"
  // for the rest of the session.
  if (response.status === 403 && sessionToken) {
    await response.text().catch(() => undefined);
    sessionToken = await acquireSessionToken();
    if (sessionToken) {
      return fetch(path, { cache: "no-store", ...options, headers: apiHeaders(options.headers) });
    }
  }
  return response;
}

// ---------------------------------------------------------------------------
// Library — the 精听 board's course browser
// ---------------------------------------------------------------------------
//
// The second level of the 精听 board: pick 视频精听 or 音频精听, then pick a
// course. A course is "video" when its manifest names `media` (an online video
// that is never downloaded) and "audio" when it names `audio` (a local file) —
// the same single-media rule `validateManifest` enforces.
//
// Opening a course is a server-side switch plus a reload, because the player
// reads its course from `./manifest.json` and the server decides which course
// that is. This replaced the old CoursePicker dialog: one place lists courses now.

const Library = (() => {
  const CATEGORIES = ["video", "audio"];
  const MENU_CATEGORIES = ["all", "video", "audio"];

  let courses = [];
  let category = "video";
  let menuCategory = "all";
  let menuQuery = "";
  let gridQuery = "";
  let gridLevel = "all";
  let gridStatus = "all";
  let gridSort = "title";
  let loaded = false;

  const grid = () => document.getElementById("course-grid");
  const status = () => document.getElementById("library-status");
  const empty = () => document.getElementById("library-empty");
  const menu = () => document.getElementById("library-menu");
  const menuButton = () => document.getElementById("library-home-button");
  const menuList = () => document.getElementById("library-menu-list");
  const menuStatus = () => document.getElementById("library-menu-status");
  const menuEmpty = () => document.getElementById("library-menu-empty");
  const menuSearchInput = () => document.getElementById("library-menu-search-input");
  const menuSearchClear = () => document.getElementById("library-menu-search-clear");
  const menuTotalCount = () => document.getElementById("library-menu-total-count");

  function init() {
    // 课程大厅的分类 Tab
    document.querySelectorAll("[data-category]").forEach((tab) => {
      tab.addEventListener("click", () => {
        const name = tab.dataset.category;
        location.hash = `#/listening/${name}`;
      });
    });

    document.getElementById("library-search-input")?.addEventListener("input", (event) => {
      gridQuery = String(event.target.value || "");
      renderGrid();
    });
    document.getElementById("library-level-filter")?.addEventListener("change", (event) => {
      gridLevel = String(event.target.value || "all");
      renderGrid();
    });
    document.getElementById("library-status-filter")?.addEventListener("change", (event) => {
      gridStatus = String(event.target.value || "all");
      renderGrid();
    });
    document.getElementById("library-sort")?.addEventListener("change", (event) => {
      gridSort = String(event.target.value || "title");
      renderGrid();
    });

    // 顶栏切换课程按钮
    menuButton()?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleMenu();
    });
    document.getElementById("library-menu-close")?.addEventListener("click", closeMenu);
    document.getElementById("library-menu-more")?.addEventListener("click", closeMenu);

    // 下拉菜单内分类 Tab 切换
    document.querySelectorAll("[data-menu-category]").forEach((tab) => {
      tab.addEventListener("click", (e) => {
        e.stopPropagation();
        setMenuCategory(tab.dataset.menuCategory || "all");
      });
    });

    // 下拉菜单内搜索
    const searchInput = menuSearchInput();
    const searchClear = menuSearchClear();
    searchInput?.addEventListener("input", (e) => {
      menuQuery = e.target.value;
      if (searchClear) searchClear.hidden = !menuQuery;
      renderMenu();
    });
    searchClear?.addEventListener("click", (e) => {
      e.stopPropagation();
      if (searchInput) {
        searchInput.value = "";
        menuQuery = "";
        searchClear.hidden = true;
        searchInput.focus();
        renderMenu();
      }
    });

    // 点击外部或按 Esc 键关闭
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".library-wrap")) closeMenu();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenu();
    });
  }

  function closeMenu() {
    const node = menu();
    if (!node || node.hidden) return;
    node.hidden = true;
    menuButton()?.setAttribute("aria-expanded", "false");
  }

  /* Opened from the practice view, so the course list may never have been
   * fetched yet — the learner can land straight on #/practice. */
  async function toggleMenu() {
    const node = menu();
    if (!node) return;
    if (!node.hidden) {
      closeMenu();
      return;
    }
    const more = document.getElementById("more-menu");
    if (more) more.hidden = true;
    document.getElementById("more-button")?.setAttribute("aria-expanded", "false");
    node.hidden = false;
    menuButton()?.setAttribute("aria-expanded", "true");
    renderMenu();
    await load();
  }

  function setMenuCategory(cat) {
    menuCategory = MENU_CATEGORIES.includes(cat) ? cat : "all";
    document.querySelectorAll("[data-menu-category]").forEach((tab) => {
      const active = (tab.dataset.menuCategory || "all") === menuCategory;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });
    renderMenu();
  }

  function kindOf(course) {
    return CourseLibraryModel.kindOf(course);
  }

  function isCurrentCourse(course, currentStableId) {
    return CourseLibraryModel.isCurrent(course, currentStableId);
  }

  function getCourseProgress(course, isCurrent) {
    const total = Number(course.practiceSentenceCount || course.sentenceCount) || 0;
    if (total <= 0) return { completed: 0, mastered: 0, total: 0, percent: 0, updatedAt: "" };

    const summarize = (data) => {
      const entries = Object.values(data || {});
      const completed = entries.filter((entry) => Boolean(
        entry?.completed || entry?.correct || entry?.mastered
          || Number(entry?.attempts || 0) > 0 || Number(entry?.exposures || 0) > 0,
      )).length;
      const mastered = entries.filter((entry) => Boolean(entry?.correct || entry?.mastered)).length;
      const percent = Math.min(100, Math.round((mastered / total) * 100));
      const updatedAt = entries
        .map((entry) => String(entry?.updatedAt || ""))
        .sort().at(-1) || "";
      return { completed, mastered, total, percent, updatedAt };
    };

    if (isCurrent && state.progress) {
      return summarize(state.progress);
    }

    try {
      const raw = localStorage.getItem(`dictation-progress:v2:${course.courseId || course.id}`);
      if (raw) {
        const data = JSON.parse(raw);
        if (data && typeof data === "object") {
          return summarize(data);
        }
      }
    } catch {}

    return { completed: 0, mastered: 0, total, percent: 0, updatedAt: "" };
  }

  /** Fetch once per page load; the list only changes when courses/ changes. */
  async function load() {
    if (loaded) return;
    const statusEl = status();
    const menuStatusEl = menuStatus();
    if (!state.backendAvailable) {
      loaded = true;
      const msg = "没有连上本地服务，只能练习当前打开的这门课程。";
      if (statusEl) {
        statusEl.textContent = msg;
        statusEl.classList.add("is-error");
      }
      if (menuStatusEl) {
        menuStatusEl.textContent = msg;
        menuStatusEl.classList.add("is-error");
        menuStatusEl.hidden = false;
      }
      render();
      return;
    }
    if (statusEl) statusEl.textContent = "正在读取课程列表…";
    if (menuStatusEl) {
      menuStatusEl.textContent = "正在读取课程列表…";
      menuStatusEl.hidden = false;
    }
    try {
      const response = await apiFetch("./api/courses");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      courses = Array.isArray(data.courses) ? data.courses : [];
      courses.forEach((course) => {
        if (course?.id) state.courseTitles[course.id] = course.title || course.id;
      });
      loaded = true;
      if (statusEl) {
        statusEl.textContent = "";
        statusEl.classList.remove("is-error");
      }
      if (menuStatusEl) {
        menuStatusEl.textContent = "";
        menuStatusEl.classList.remove("is-error");
        menuStatusEl.hidden = true;
      }
    } catch (error) {
      const errMsg = `课程列表读取失败：${error.message}`;
      if (statusEl) {
        statusEl.textContent = errMsg;
        statusEl.classList.add("is-error");
      }
      if (menuStatusEl) {
        menuStatusEl.textContent = errMsg;
        menuStatusEl.classList.add("is-error");
        menuStatusEl.hidden = false;
      }
    }
    render();
  }

  function setCategory(name) {
    category = CATEGORIES.includes(name) ? name : "video";
    document.querySelectorAll("[data-category]").forEach((tab) => {
      const isActive = tab.dataset.category === category;
      tab.classList.toggle("is-active", isActive);
      tab.setAttribute("aria-selected", String(isActive));
    });
    render();
  }

  function render() {
    renderGrid();
    renderMenu();
  }

  function courseQualityState(course) {
    return CourseLibraryModel.qualityState(course);
  }

  function filterGridCourses(currentId) {
    return CourseLibraryModel.filterAndSort(courses, {
      category,
      query: gridQuery,
      level: gridLevel,
      status: gridStatus,
      sort: gridSort,
      currentId,
      progressOf: getCourseProgress,
    });
  }

  function renderGrid() {
    const node = grid();
    if (!node) return;

    const counts = { video: 0, audio: 0 };
    courses.forEach((course) => {
      const k = kindOf(course);
      if (counts[k] !== undefined) counts[k] += 1;
    });
    CATEGORIES.forEach((name) => {
      const badge = document.getElementById(`category-count-${name}`);
      if (badge) badge.textContent = String(counts[name]);
    });

    const currentId = stableCourseId(state.manifest);
    const shown = filterGridCourses(currentId);
    node.replaceChildren();
    const emptyEl = empty();
    if (emptyEl) emptyEl.hidden = shown.length > 0 || !loaded;
    if (loaded && status() && !status().classList.contains("is-error")) {
      status().textContent = shown.length === courses.length ? "" : `显示 ${shown.length} / ${courses.length} 门课程`;
    }

    shown.forEach((course) => node.appendChild(card(course, isCurrentCourse(course, currentId))));
  }

  function menuCard(course, isCurrent) {
    const item = document.createElement("div");
    item.className = `library-menu-card${isCurrent ? " is-current" : ""}`;
    item.setAttribute("role", "button");
    item.setAttribute("tabindex", "0");
    item.setAttribute("aria-label", `${course.title || course.id}${isCurrent ? " (当前练习中)" : ""}`);

    // Left media icon avatar
    const kind = kindOf(course);
    const iconWrap = document.createElement("div");
    iconWrap.className = "library-card-icon-wrap";
    const avatar = document.createElement("div");
    avatar.className = `library-card-avatar ${kind}`;
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = kind === "video" ? "🎬" : "🎧";
    iconWrap.appendChild(avatar);
    item.appendChild(iconWrap);

    // Center body info
    const body = document.createElement("div");
    body.className = "library-card-body";

    const titleRow = document.createElement("div");
    titleRow.className = "library-card-title-row";
    const title = document.createElement("h4");
    title.className = "library-card-title";
    title.textContent = course.title || course.id;
    title.title = course.title || course.id;
    titleRow.appendChild(title);
    body.appendChild(titleRow);

    const metaRow = document.createElement("div");
    metaRow.className = "library-card-meta-row";

    // Sentence count
    const countTag = document.createElement("span");
    countTag.className = "library-tag";
    countTag.textContent = `${course.sentenceCount || 0} 句`;
    metaRow.appendChild(countTag);

    // Language
    const lang = languageLabel(course.language);
    if (lang) {
      const langTag = document.createElement("span");
      langTag.className = "library-tag lang";
      langTag.textContent = lang;
      metaRow.appendChild(langTag);
    }

    // Media Provider / Tier
    if (kind === "video" && course.mediaProvider) {
      const providerTag = document.createElement("span");
      providerTag.className = "library-tag tier";
      const pName = { youtube: "YouTube", bilibili: "哔哩哔哩", vimeo: "Vimeo" }[course.mediaProvider] || course.mediaProvider;
      providerTag.textContent = pName;
      metaRow.appendChild(providerTag);
    } else if (kind === "audio") {
      const audioTag = document.createElement("span");
      audioTag.className = "library-tag";
      audioTag.textContent = "本地音频";
      metaRow.appendChild(audioTag);
    }
    body.appendChild(metaRow);

    // Progress bar & mastery info
    const prog = getCourseProgress(course, isCurrent);
    if (prog.total > 0) {
      const progRow = document.createElement("div");
      progRow.className = "library-card-progress";

      const track = document.createElement("div");
      track.className = "library-progress-mini-track";
      const fill = document.createElement("span");
      fill.className = "library-progress-mini-fill";
      fill.style.width = `${prog.percent}%`;
      track.appendChild(fill);
      progRow.appendChild(track);

      const progText = document.createElement("span");
      progText.className = "library-progress-mini-text";
      progText.textContent = prog.completed > 0
        ? `已练 ${prog.completed}/${prog.total} · 掌握 ${prog.percent}% (${prog.mastered}/${prog.total})`
        : `未开始 · 0/${prog.total}`;
      progRow.appendChild(progText);

      body.appendChild(progRow);
    }
    item.appendChild(body);

    // Right Action / Status
    const actionWrap = document.createElement("div");
    actionWrap.className = "library-card-action";

    if (isCurrent) {
      const activeBadge = document.createElement("span");
      activeBadge.className = "library-active-pill";
      const pulse = document.createElement("span");
      pulse.className = "library-pulse-dot";
      pulse.setAttribute("aria-hidden", "true");
      activeBadge.appendChild(pulse);
      activeBadge.appendChild(document.createTextNode("当前练习"));
      actionWrap.appendChild(activeBadge);
    } else {
      const switchBtn = document.createElement("span");
      switchBtn.className = "library-switch-btn";
      switchBtn.textContent = "切换 →";
      actionWrap.appendChild(switchBtn);
    }
    item.appendChild(actionWrap);

    // Click to switch
    const onSelect = () => {
      if (isCurrent) {
        closeMenu();
        return;
      }
      item.classList.add("is-switching");
      const switchBtn = item.querySelector(".library-switch-btn");
      if (switchBtn) switchBtn.textContent = "载入中…";
      switchTo(course.id, {
        isCurrent,
        onBusy: (busy) => { item.classList.toggle("is-switching", busy); },
        onError: (text) => {
          if (switchBtn) switchBtn.textContent = "切换 →";
          const statusEl = menuStatus();
          if (statusEl) {
            statusEl.textContent = `打不开：${text}`;
            statusEl.classList.add("is-error");
            statusEl.hidden = false;
          }
        },
      });
    };

    item.addEventListener("click", onSelect);
    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelect();
      }
    });

    return item;
  }

  function renderMenu() {
    const list = menuList();
    if (!list) return;
    const statusEl = menuStatus();
    const emptyEl = menuEmpty();
    const totalCountEl = menuTotalCount();
    const currentId = stableCourseId(state.manifest);

    list.replaceChildren();

    // 更新各分类数量徽章
    const counts = { all: courses.length, video: 0, audio: 0 };
    courses.forEach((c) => { counts[kindOf(c)] += 1; });
    const countAllEl = document.getElementById("library-menu-count-all");
    const countVideoEl = document.getElementById("library-menu-count-video");
    const countAudioEl = document.getElementById("library-menu-count-audio");
    if (countAllEl) countAllEl.textContent = String(counts.all);
    if (countVideoEl) countVideoEl.textContent = String(counts.video);
    if (countAudioEl) countAudioEl.textContent = String(counts.audio);
    if (totalCountEl) {
      totalCountEl.textContent = `${counts.all} 门`;
      totalCountEl.hidden = counts.all === 0;
    }

    if (!loaded) {
      if (statusEl) {
        statusEl.textContent = "正在读取课程列表…";
        statusEl.hidden = false;
      }
      if (emptyEl) emptyEl.hidden = true;
      return;
    }
    if (courses.length === 0) {
      if (statusEl) {
        statusEl.textContent = "还没有安装课程。";
        statusEl.hidden = false;
      }
      if (emptyEl) emptyEl.hidden = true;
      return;
    }
    if (statusEl && !statusEl.classList.contains("is-error")) {
      statusEl.hidden = true;
    }

    // 过滤课程
    let filtered = courses;
    if (menuCategory !== "all") {
      filtered = filtered.filter((c) => kindOf(c) === menuCategory);
    }
    const q = menuQuery.trim().toLowerCase();
    if (q) {
      filtered = filtered.filter((c) => {
        const title = (c.title || c.id || "").toLowerCase();
        const lang = languageLabel(c.language).toLowerCase();
        const id = (c.id || "").toLowerCase();
        return title.includes(q) || lang.includes(q) || id.includes(q);
      });
    }

    if (filtered.length === 0) {
      if (emptyEl) emptyEl.hidden = false;
      return;
    }
    if (emptyEl) emptyEl.hidden = true;

    // 分类展示：当未搜索且选的是全部时，分组显示视频与音频；否则直接平铺
    if (menuCategory === "all" && !q) {
      for (const kind of ["video", "audio"]) {
        const group = filtered.filter((c) => kindOf(c) === kind);
        if (group.length === 0) continue;

        const heading = document.createElement("p");
        heading.className = "library-menu-group-heading";
        heading.textContent = kind === "video" ? `🎬 视频精听 (${group.length})` : `🎧 音频精听 (${group.length})`;
        list.appendChild(heading);

        group.forEach((course) => {
          const isCurrent = isCurrentCourse(course, currentId);
          list.appendChild(menuCard(course, isCurrent));
        });
      }
    } else {
      filtered.forEach((course) => {
        const isCurrent = isCurrentCourse(course, currentId);
        list.appendChild(menuCard(course, isCurrent));
      });
    }
  }

  function card(course, isCurrent) {
    const article = document.createElement("article");
    article.className = `course-card${isCurrent ? " is-current" : ""}`;

    const chip = document.createElement("div");
    chip.className = `course-kind-chip ${kindOf(course)}`;
    chip.textContent = kindLabel(course);
    article.appendChild(chip);

    const badgeRow = document.createElement("div");
    badgeRow.className = "course-status-row";
    const qualityBadge = document.createElement("span");
    const qualityState = courseQualityState(course);
    qualityBadge.className = `course-status-badge ${qualityState}`;
    qualityBadge.textContent = qualityLabel(course);
    badgeRow.appendChild(qualityBadge);
    const reviewBadge = document.createElement("span");
    reviewBadge.className = "course-status-badge review";
    reviewBadge.textContent = reviewLabel(course);
    badgeRow.appendChild(reviewBadge);
    article.appendChild(badgeRow);

    const title = document.createElement("h3");
    title.className = "course-card-title";
    title.textContent = course.title || course.id;
    article.appendChild(title);

    const meta = document.createElement("p");
    meta.className = "course-card-meta";
    meta.textContent = [`${course.practiceSentenceCount || course.sentenceCount || 0} 个练习`, course.level, languageLabel(course.language)]
      .filter(Boolean)
      .join(" · ");
    article.appendChild(meta);

    const progress = getCourseProgress(course, isCurrent);
    const progressWrap = document.createElement("div");
    progressWrap.className = "course-card-progress";
    const progressTrack = document.createElement("div");
    progressTrack.className = "course-card-progress-track";
    const progressFill = document.createElement("span");
    progressFill.style.width = `${progress.percent}%`;
    progressTrack.appendChild(progressFill);
    const progressText = document.createElement("span");
    progressText.textContent = progress.completed > 0
      ? `已练习 ${progress.completed}/${progress.total}；已掌握 ${progress.mastered}（${progress.percent}%）`
      : "尚未开始";
    progressWrap.append(progressTrack, progressText);
    article.appendChild(progressWrap);

    const message = document.createElement("p");
    message.className = "course-card-error";
    message.hidden = true;
    article.appendChild(message);

    const actions = document.createElement("div");
    actions.className = "course-card-actions";
    const button = document.createElement("button");
    button.className = isCurrent ? "secondary-button" : "primary-button";
    button.type = "button";
    button.textContent = isCurrent ? "继续学习" : "开始学习";
    button.addEventListener("click", () => switchTo(course.id, {
      isCurrent,
      onBusy: (busy) => { button.disabled = busy; },
      onError: (text) => {
        message.textContent = `打不开：${text}`;
        message.hidden = false;
      },
    }));
    actions.appendChild(button);
    article.appendChild(actions);

    return article;
  }

  /* A manifest's `language` is an object ({code, locale, displayName, …}), not a
   * string. The old picker interpolated it straight into the card and printed
   * "[object Object]" for every course. */
  function languageLabel(value) {
    return CourseLibraryModel.languageLabel(value);
  }

  function qualityLabel(course) {
    return CourseLibraryModel.qualityLabel(course);
  }

  function reviewLabel(course) {
    return CourseLibraryModel.reviewLabel(course);
  }

  /** Say which kind of course this is, and for a video one, what it can do. */
  function kindLabel(course) {
    if (kindOf(course) === "audio") return "🎧 本地音频";
    const provider = {
      youtube: "YouTube",
      bilibili: "哔哩哔哩",
      vimeo: "Vimeo",
    }[course.mediaProvider] || "在线视频";
    const tier = {
      "full": "可完全控制",
      "seek-reload": "只能重载定位",
      "external": "需在原站播放",
    }[course.mediaControl] || "";
    return `🎬 ${provider}${tier ? ` · ${tier}` : ""}`;
  }

  /* Opening the course that is already active needs no round trip — the player
   * already has it loaded, so this is only a view change. */
  async function switchTo(courseId, { isCurrent = false, onBusy, onError } = {}) {
    if (isCurrent && !state.courseError) {
      goToPractice();
      return;
    }
    onBusy?.(true);
    try {
      const response = await apiFetch("./api/courses/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ courseId }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      // The player reads its course from ./manifest.json, which the server has
      // just swapped, so a reload is what actually opens it.
      location.assign("./listening#/practice");
    } catch (error) {
      onBusy?.(false);
      onError?.(error.message);
    }
  }

  return { init, load, setCategory, closeMenu };
})();

// ---------------------------------------------------------------------------
// Router — 板块 → 分类 → 课程 → 学习
// ---------------------------------------------------------------------------
//
//   #/listening[/video|/audio]   课程库（默认落点）
//   #/practice                   当前课程的练习界面
//   #/me[/<模块>]                个人中心（浮在课程库之上）

const LISTENING_HASH = /^#\/listening(?:\/(video|audio))?$/;

function showView(name) {
  const library = document.getElementById("view-library");
  const practice = document.getElementById("view-practice");
  if (library) library.hidden = name !== "library";
  if (practice) practice.hidden = name !== "practice";

  // A course that failed to open reports itself where the course would be. Going
  // back to the library must clear it, or the banner outlives the view it belongs to.
  if (name !== "practice" && elements.fatalError) elements.fatalError.hidden = true;

  // The course panel toggle steers the practice layout; it means nothing while
  // browsing the library.
  if (elements.sidebarToggleButton) elements.sidebarToggleButton.hidden = name !== "practice";
  if (elements.libraryHomeButton) elements.libraryHomeButton.hidden = name !== "practice";
  if (name !== "practice") Library.closeMenu();
}

/* Leaving the personal centre for one sentence.
 *
 * Every 去练习 / 立即重练 / 跳到该句 button used to close the centre and call
 * selectSentence. That was right when the player was one page: closing the dialog
 * revealed the practice view underneath. It is wrong now — the centre floats over
 * the course library, so closing it drops the learner back in the library with the
 * practice view still hidden and the sentence they picked nowhere on screen. The
 * route has to move with them.
 */
async function goToPractice(index = null, { dictation = true } = {}) {
  routeBeneathPersonal = "./listening#/practice";
  closePersonalCenter();
  showView("practice");
  if (location.hash !== "#/practice" || location.pathname.endsWith("/me")) {
    history.replaceState(null, "", "./listening#/practice");
  }

  try {
    await ensureActiveCourseLoaded();
  } catch {
    showFatalError(state.courseError || new Error("课程无法加载。"));
    return;
  }

  if (state.courseError) {
    showFatalError(state.courseError);
    return;
  }
  if (dictation && state.mode === "playback") setLearningMode("dictation", { resume: false });
  if (typeof index === "number" && index >= 0) selectSentence(index);
}

/* `withData: false` is the first pass, before anything has been fetched: pick a
 * view and show it, but do not start the loads that depend on a backend probe
 * that has not run yet. The second pass, after boot, does the rest. */
function applyRoute({ withData = true } = {}) {
  const hash = location.hash || "";
  const personalRoute = readPersonalRoute();

  if (personalRoute.tab && !isStandalonePersonalPath()) {
    const subtab = personalRoute.subtab ? `/${personalRoute.subtab}` : "";
    location.replace(`./me#/${personalRoute.tab}${subtab}`);
    return;
  }

  setPersonalRoutePresentation(Boolean(personalRoute.tab));

  if (hash === "#/practice") {
    showView("practice");
    // Asked for a course that will not open: say so where the course would be,
    // and leave the library one click away rather than blanking the page.
    if (withData && state.courseError) showFatalError(state.courseError);
    else if (withData && !state.manifest) {
      ensureActiveCourseLoaded().catch((error) => showFatalError(error));
    }
    return;
  }

  showView("library");
  Library.setCategory((LISTENING_HASH.exec(hash) || [])[1] || "video");
  if (!withData) return;

  if (personalRoute.tab) {
    openPersonalCenter(personalRoute.tab, personalRoute.subtab);
    return;
  }
  Library.load();
}

// ---------------------------------------------------------------------------
// BackendManager & StatsManager — UI for backend status & learning stats
// ---------------------------------------------------------------------------

const BackendManager = (() => {
  let dbPath = "";

  function init(backendAvailable, serverDbPath = "") {
    dbPath = serverDbPath;
    const btn = document.getElementById("backend-status-button");
    const dot = document.getElementById("backend-status-dot");
    const text = document.getElementById("backend-status-text");
    const dialog = document.getElementById("backend-dialog");
    const closeBtn = document.getElementById("close-backend-button");
    const pathEl = document.getElementById("backend-dialog-db-path");

    if (dot) {
      if (backendAvailable) {
        dot.className = "status-dot";
        if (text) text.textContent = "本地后端已连接 (SQLite)";
        if (text) text.textContent = "资料本地存储位置";
      } else {
        dot.className = "status-dot offline";
        if (text) text.textContent = "离线单机模式 (localStorage)";
        if (text) text.textContent = "资料本地存储 (离线单机)";
      }
    }

    if (btn && dialog) {
      btn.addEventListener("click", () => {
        if (pathEl) pathEl.textContent = dbPath || "(未连接本地后端，当前使用浏览器本地存储)";
        if (pathEl) pathEl.textContent = dbPath || "(未连接本地存储服务，当前使用浏览器本地存储)";
        dialog.showModal();
      });
    }
    if (closeBtn && dialog) {
      closeBtn.addEventListener("click", () => dialog.close());
    }
    if (dialog) {
      dialog.addEventListener("click", (e) => {
        if (e.target === dialog) dialog.close();
      });
    }
  }

  function setDbPath(p) { dbPath = p; }

  return { init, setDbPath };
})();

const AnalyticsManager = (() => {
  let activeTab = "punch";
  let chartPeriod = 7;
  let calendarMonthOffset = 0;
  let cachedAnalytics = null;
  let logsPage = 0;
  const LOGS_PER_PAGE = 15;

  function init() {
    // Showing and hiding is the personal centre's job now; this module only owns
    // the 打卡 / 分析 / 记录 sub-tabs and their data.
    // Sub-tab switching
    const tabConfigs = [
      { btnId: "tab-btn-punch", panelId: "panel-punch", tabName: "punch" },
      { btnId: "tab-btn-analytics", panelId: "panel-analytics", tabName: "analytics" },
      { btnId: "tab-btn-logs", panelId: "panel-logs", tabName: "logs" },
    ];

    tabConfigs.forEach(({ btnId, tabName }) => {
      const b = document.getElementById(btnId);
      if (b) {
        b.addEventListener("click", () => switchTab(tabName));
      }
    });

    // Punch in button and mood selector
    const punchBtn = document.getElementById("punch-action-button");
    if (punchBtn) {
      punchBtn.addEventListener("click", handlePunchIn);
    }
    const moodBtns = document.querySelectorAll("#punch-mood-selector .mood-btn");
    moodBtns.forEach((mBtn) => {
      mBtn.addEventListener("click", () => {
        moodBtns.forEach((b) => b.classList.remove("active"));
        mBtn.classList.add("active");
      });
    });

    // Calendar navigation
    const prevMonthBtn = document.getElementById("calendar-prev-month");
    const nextMonthBtn = document.getElementById("calendar-next-month");
    if (prevMonthBtn) {
      prevMonthBtn.addEventListener("click", () => {
        calendarMonthOffset -= 1;
        renderCalendar();
      });
    }
    if (nextMonthBtn) {
      nextMonthBtn.addEventListener("click", () => {
        calendarMonthOffset += 1;
        renderCalendar();
      });
    }

    // Chart period switch
    [7, 14, 30].forEach((p) => {
      const pBtn = document.getElementById(`chart-period-${p}`);
      if (pBtn) {
        pBtn.addEventListener("click", () => {
          chartPeriod = p;
          [7, 14, 30].forEach((x) => {
            const el = document.getElementById(`chart-period-${x}`);
            if (el) el.classList.toggle("active", x === p);
          });
          renderTrendChart();
        });
      }
    });

    const analyticsScope = document.getElementById("analytics-scope");
    if (analyticsScope) {
      analyticsScope.addEventListener("change", async () => {
        cachedAnalytics = null;
        await refreshData();
      });
    }

    // Study logs filters & export & pagination
    const filterStatus = document.getElementById("logs-filter-status");
    const filterDays = document.getElementById("logs-filter-days");
    if (filterStatus) filterStatus.addEventListener("change", () => { logsPage = 0; loadStudyLogs(); });
    if (filterDays) filterDays.addEventListener("change", () => { logsPage = 0; loadStudyLogs(); });

    const exportBtn = document.getElementById("logs-export-csv-button");
    if (exportBtn) exportBtn.addEventListener("click", exportStudyLogsCsv);

    const clearLogsBtn = document.getElementById("logs-clear-button");
    if (clearLogsBtn) clearLogsBtn.addEventListener("click", handleClearLogs);

    const prevPageBtn = document.getElementById("logs-prev-page");
    const nextPageBtn = document.getElementById("logs-next-page");
    if (prevPageBtn) {
      prevPageBtn.addEventListener("click", () => {
        if (logsPage > 0) {
          logsPage -= 1;
          loadStudyLogs();
        }
      });
    }
    if (nextPageBtn) {
      nextPageBtn.addEventListener("click", () => {
        logsPage += 1;
        loadStudyLogs();
      });
    }
  }

  function switchTab(tabName) {
    activeTab = tabName;
    const tabConfigs = [
      { btnId: "tab-btn-punch", panelId: "panel-punch", tabName: "punch" },
      { btnId: "tab-btn-analytics", panelId: "panel-analytics", tabName: "analytics" },
      { btnId: "tab-btn-logs", panelId: "panel-logs", tabName: "logs" },
    ];
    tabConfigs.forEach(({ btnId, panelId, tabName: t }) => {
      const btn = document.getElementById(btnId);
      const panel = document.getElementById(panelId);
      const isActive = t === tabName;
      if (btn) {
        btn.classList.toggle("active", isActive);
        btn.setAttribute("aria-selected", String(isActive));
      }
      if (panel) {
        panel.hidden = !isActive;
      }
    });

    if (tabName === "punch") {
      renderPunchView();
    } else if (tabName === "analytics") {
      renderAnalyticsView();
    } else if (tabName === "logs") {
      logsPage = 0;
      loadStudyLogs();
    }
    if (activePersonalTab === "analytics" && elements.personalDialog?.open) {
      history.replaceState(null, "", `#/me/analytics/${tabName}`);
    }
  }

  /** Activate the analytics panel. The centre has already shown the dialog. */
  async function open(defaultTab = "punch") {
    switchTab(defaultTab);
    await refreshData();
  }

  async function refreshData() {
    const courseId = state.manifest ? stableCourseId(state.manifest) : "";
    const scope = document.getElementById("analytics-scope")?.value || "current";
    if (state.backendAvailable) {
      try {
        const response = await apiFetch(
          `./api/analytics?scope=${encodeURIComponent(scope)}&courseId=${encodeURIComponent(courseId)}`,
        );
        if (response.ok) {
          const data = await response.json();
          cachedAnalytics = data.analytics;
        }
      } catch (e) {
        console.warn("Failed to fetch analytics from backend", e);
      }
    }

    if (!cachedAnalytics) {
      cachedAnalytics = buildLocalAnalyticsFallback();
    }

    updateStreakUi();

    if (activeTab === "punch") renderPunchView();
    else if (activeTab === "analytics") renderAnalyticsView();
    else if (activeTab === "logs") loadStudyLogs();

    const dbPathEl = document.getElementById("analytics-db-path");
    if (dbPathEl) {
      if (cachedAnalytics.dbPath) {
        dbPathEl.textContent = `本地 SQLite 数据库文件：${cachedAnalytics.dbPath}`;
      } else {
        dbPathEl.textContent = "运行模式：浏览器本地模式 (localStorage)";
      }
    }
  }

  function buildLocalAnalyticsFallback() {
    const courseIndexes = state.coursePracticeIndexes?.length
      ? state.coursePracticeIndexes
      : (state.practiceIndexes || []);
    const totalPractice = courseIndexes.length;
    const entries = courseIndexes
      .map((index) => state.progress[sentenceProgressKey(index)])
      .filter(Boolean);
    const completed = entries.filter((entry) => Number(entry?.attempts || 0) > 0).length;
    const mastered = entries.filter((entry) => Boolean(entry?.correct)).length;
    const totalAttempts = entries.reduce((sum, entry) => sum + Number(entry?.attempts || 0), 0);
    const currStreak = computeStreak(state.activityDays || []);
    const isTodayPunched = (state.activityDays || []).includes(todayIso());

    return {
      summary: {
        totalStudyDays: (state.activityDays || []).length,
        currentStreak: currStreak,
        maxStreak: currStreak,
        totalPracticed: completed,
        totalCompleted: completed,
        totalMastered: mastered,
        totalAttempts: totalAttempts || completed,
        totalCorrect: mastered,
        overallAccuracy: completed > 0 ? Math.round((mastered / completed) * 100) : 0,
        firstTryCorrect: state.firstTryCorrect || 0,
        totalVocab: state.vocab?.length || 0,
        masteredVocab: state.vocab?.filter((v) => (v.srsStage || 0) === 3 || v.mastered)?.length || 0,
        totalNotes: Object.keys(state.notesByCourse || {}).length,
        starredNotes: Object.values(state.notesByCourse || {}).filter((n) => n.starred).length,
        totalDurationMs: 0,
        isTodayPunched: isTodayPunched,
        todayPunch: null,
      },
      heatmap: (state.activityDays || []).map((day) => ({
        day,
        attempts: 1,
        correct: 1,
        accuracy: 100,
        durationMs: 0,
        punched: true,
        mood: "🔥",
        note: "",
      })),
      trends: {
        last7Days: { days: 7, attempts: totalAttempts, correct: mastered, accuracy: completed > 0 ? Math.round((mastered / completed) * 100) : 0 },
        last14Days: { days: 14, attempts: totalAttempts, correct: mastered, accuracy: completed > 0 ? Math.round((mastered / completed) * 100) : 0 },
        last30Days: { days: 30, attempts: totalAttempts, correct: mastered, accuracy: completed > 0 ? Math.round((mastered / completed) * 100) : 0 },
      },
      weakPoints: [],
      courseBreakdown: state.manifest ? [{
        courseId: stableCourseId(state.manifest),
        practicedCount: completed,
        masteredCount: mastered,
        attempts: totalAttempts,
        avgScore: 100,
      }] : [],
      diagnostics: [
        { type: isTodayPunched ? "success" : "info", title: isTodayPunched ? "今日已打卡" : "开启今日打卡", text: isTodayPunched ? "今天已完成打卡，继续保持好习惯！" : "练习几道题目或点击打卡即可点亮今日火苗。" }
      ],
      dbPath: "",
    };
  }

  function renderPunchView() {
    if (!cachedAnalytics) return;
    const summary = cachedAnalytics.summary || {};
    const today = new Date();
    const todayStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;
    const elDate = document.getElementById("punch-today-date");
    if (elDate) elDate.textContent = todayStr;

    const elCurrentStreak = document.getElementById("punch-current-streak");
    const elMaxStreak = document.getElementById("punch-max-streak");
    const elTotalDays = document.getElementById("punch-total-days");
    if (elCurrentStreak) elCurrentStreak.textContent = String(summary.currentStreak || 0);
    if (elMaxStreak) elMaxStreak.textContent = String(summary.maxStreak || summary.currentStreak || 0);
    if (elTotalDays) elTotalDays.textContent = String(summary.totalStudyDays || 0);

    const isPunched = summary.isTodayPunched || (state.activityDays || []).includes(todayIso());
    const punchIcon = document.getElementById("punch-status-icon");
    const punchText = document.getElementById("punch-status-text");
    const punchBtn = document.getElementById("punch-action-button");
    const punchDot = document.getElementById("punch-today-dot");

    if (punchDot) {
      punchDot.classList.toggle("is-pending", !isPunched);
      punchDot.title = isPunched ? "今日已打卡" : "今日待打卡";
    }

    if (isPunched) {
      if (punchIcon) punchIcon.textContent = summary.todayPunch?.mood || "🔥";
      if (punchText) punchText.textContent = "今日已完成打卡！";
      if (punchBtn) {
        punchBtn.textContent = `已打卡 ${summary.todayPunch?.mood || "🔥"}`;
        punchBtn.classList.add("is-punched");
        punchBtn.disabled = true;
      }
    } else {
      if (punchIcon) punchIcon.textContent = "⚡";
      if (punchText) punchText.textContent = "今日尚未打卡";
      if (punchBtn) {
        punchBtn.textContent = "🔥 立即完成今日打卡";
        punchBtn.classList.remove("is-punched");
        punchBtn.disabled = false;
      }
    }

    // Milestones
    const milestones = [
      { id: "badge-3days", target: 3 },
      { id: "badge-7days", target: 7 },
      { id: "badge-14days", target: 14 },
      { id: "badge-30days", target: 30 },
      { id: "badge-100days", target: 100 },
    ];
    const maxDays = Math.max(summary.maxStreak || 0, summary.currentStreak || 0, summary.totalStudyDays || 0);
    milestones.forEach(({ id, target }) => {
      const bEl = document.getElementById(id);
      if (!bEl) return;
      const unlocked = maxDays >= target;
      bEl.classList.toggle("unlocked", unlocked);
      const statusEl = bEl.querySelector(".badge-status");
      if (statusEl) {
        statusEl.textContent = unlocked ? "已达成" : `还需 ${target - maxDays} 天`;
      }
    });

    renderCalendar();
  }

  function renderCalendar() {
    const grid = document.getElementById("calendar-grid");
    const monthTitle = document.getElementById("calendar-month-title");
    if (!grid || !monthTitle) return;

    const baseDate = new Date();
    baseDate.setDate(1);
    baseDate.setMonth(baseDate.getMonth() + calendarMonthOffset);

    const year = baseDate.getFullYear();
    const month = baseDate.getMonth();
    monthTitle.textContent = `${year}年 ${month + 1}月`;

    const firstDayIndex = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const prevMonthDays = new Date(year, month, 0).getDate();

    const heatmapMap = new Map();
    if (cachedAnalytics?.heatmap) {
      cachedAnalytics.heatmap.forEach((item) => {
        heatmapMap.set(item.day, item);
      });
    }

    grid.replaceChildren();

    // Previous month filler days
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      const cell = document.createElement("div");
      cell.className = "calendar-day-cell other-month";
      cell.textContent = String(prevMonthDays - i);
      grid.appendChild(cell);
    }

    const todayString = todayIso();

    // Days of current month
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const heatData = heatmapMap.get(dateStr);
      const attempts = heatData?.attempts || (state.activityDays?.includes(dateStr) ? 1 : 0);
      const isPunched = heatData?.punched || state.activityDays?.includes(dateStr);
      const mood = heatData?.mood || (isPunched ? "🔥" : "");

      let lvl = "lvl-0";
      if (attempts >= 30) lvl = "lvl-4";
      else if (attempts >= 16) lvl = "lvl-3";
      else if (attempts >= 6) lvl = "lvl-2";
      else if (attempts >= 1) lvl = "lvl-1";

      const cell = document.createElement("div");
      cell.className = `calendar-day-cell ${lvl}${dateStr === todayString ? " is-today" : ""}`;
      cell.dataset.date = dateStr;

      const numSpan = document.createElement("span");
      numSpan.className = "calendar-day-num";
      numSpan.textContent = String(d);
      cell.appendChild(numSpan);

      if (mood) {
        const moodSpan = document.createElement("span");
        moodSpan.className = "calendar-day-mood";
        moodSpan.textContent = mood;
        cell.appendChild(moodSpan);
      }

      cell.addEventListener("click", () => selectCalendarDay(dateStr, heatData, d));
      grid.appendChild(cell);
    }

    const totalCells = firstDayIndex + daysInMonth;
    const remaining = (totalCells % 7 === 0) ? 0 : 7 - (totalCells % 7);
    for (let i = 1; i <= remaining; i++) {
      const cell = document.createElement("div");
      cell.className = "calendar-day-cell other-month";
      cell.textContent = String(i);
      grid.appendChild(cell);
    }
  }

  function selectCalendarDay(dateStr, heatData, dayNum) {
    const detailBox = document.getElementById("calendar-day-detail");
    if (!detailBox) return;

    document.querySelectorAll(".calendar-day-cell").forEach((c) => c.classList.remove("selected"));
    const targetCell = document.querySelector(`.calendar-day-cell[data-date="${dateStr}"]`);
    if (targetCell) targetCell.classList.add("selected");

    const dateHeader = document.getElementById("day-detail-date");
    const punchTag = document.getElementById("day-detail-punch-tag");
    const statsEl = document.getElementById("day-detail-stats");
    const noteEl = document.getElementById("day-detail-note");

    detailBox.hidden = false;
    if (dateHeader) dateHeader.textContent = dateStr;

    const isPunched = heatData?.punched || state.activityDays?.includes(dateStr);
    if (punchTag) {
      punchTag.textContent = isPunched ? `已打卡 ${heatData?.mood || "🔥"}` : "未打卡";
      punchTag.style.background = isPunched ? "#dcfce7" : "#fee2e2";
      punchTag.style.color = isPunched ? "#166534" : "#991b1b";
    }

    const attempts = heatData?.attempts || 0;
    const correct = heatData?.correct || 0;
    const acc = heatData?.accuracy || (attempts > 0 ? Math.round((correct / attempts) * 100) : 0);
    const durMin = Math.round((heatData?.durationMs || 0) / 60000);

    if (statsEl) {
      statsEl.innerHTML = `作答：<strong>${attempts}</strong> 题 · 满分：<strong>${correct}</strong> 题 · 正确率：<strong>${acc}%</strong> · 学习时长：<strong>${durMin}</strong> 分钟`;
    }
    if (noteEl) {
      noteEl.textContent = heatData?.note ? `打卡心得：“${heatData.note}”` : "无打卡寄语";
    }
  }

  async function handlePunchIn() {
    const noteInput = document.getElementById("punch-note-input");
    const activeMoodBtn = document.querySelector("#punch-mood-selector .mood-btn.active");
    const note = (noteInput ? noteInput.value : "").trim();
    const mood = (activeMoodBtn ? activeMoodBtn.dataset.mood : "🔥") || "🔥";

    const payload = {
      day: todayIso(),
      note,
      mood,
      // A manual check-in is a habit marker, not invented learning activity.
      // Actual sentence counts and durations come from study logs.
      sentencesCount: 0,
      studyDurationMs: 0,
    };

    await syncLearningMutation("POST", "./api/punch-in", payload, {
      entityType: "punch",
      entityKey: payload.day,
    });

    await recordActivity();
    await refreshData();
  }

  function renderAnalyticsView() {
    if (!cachedAnalytics) return;
    const summary = cachedAnalytics.summary || {};

    const elAcc = document.getElementById("ana-overall-accuracy");
    const elMasterRate = document.getElementById("ana-mastered-rate");
    const elPracticed = document.getElementById("ana-total-practiced");
    const elAttempts = document.getElementById("ana-total-attempts");
    const elDuration = document.getElementById("ana-total-duration");
    const elVocab = document.getElementById("ana-vocab-mastered");
    const elExamAnswered = document.getElementById("ana-exam-answered");
    const elExamAccuracy = document.getElementById("ana-exam-accuracy");
    const scopeNote = document.getElementById("analytics-scope-note");

    const isAllListening = cachedAnalytics.scope === "allListening";
    const totalPractice = isAllListening
      ? (summary.totalPracticed || 0)
      : (state.coursePracticeIndexes?.length || state.practiceIndexes?.length || summary.totalPracticed || 0);
    const masterRate = totalPractice > 0 ? Math.round((summary.totalMastered / totalPractice) * 100) : 0;
    const durationMin = Math.round((summary.totalDurationMs || 0) / 60000);

    if (elAcc) elAcc.textContent = `${summary.overallAccuracy || 0}%`;
    if (elMasterRate) elMasterRate.textContent = `${masterRate}%`;
    if (elPracticed) elPracticed.textContent = `${summary.totalPracticed || 0} / ${totalPractice}`;
    if (elAttempts) elAttempts.textContent = String(summary.totalAttempts || 0);
    if (elDuration) elDuration.textContent = `${durationMin} 分钟`;
    if (elVocab) elVocab.textContent = `${summary.masteredVocab || 0} / ${summary.totalVocab || 0}`;
    if (elExamAnswered) elExamAnswered.textContent = String(cachedAnalytics.examStats?.totalQuestionsAnswered || 0);
    if (elExamAccuracy) elExamAccuracy.textContent = `${cachedAnalytics.examStats?.accuracy || 0}%`;
    if (scopeNote) {
      scopeNote.textContent = isAllListening
        ? "正确率、作答、趋势和时长按全部听写课程统计；生词与课程矩阵为全库，JLPT 单独列示。"
        : "正确率、作答、趋势和时长按当前听写课程统计；生词与课程矩阵为全库，JLPT 单独列示。";
    }

    renderTrendChart();
    renderCourseMatrix();
    renderWeakPoints();
    renderDiagnostics();
  }

  function renderTrendChart() {
    const container = document.getElementById("analytics-trend-chart");
    if (!container || !cachedAnalytics) return;

    const daysCount = chartPeriod;
    const heatmap = cachedAnalytics.heatmap || [];
    const recent = heatmap.slice(-daysCount);

    if (recent.length === 0) {
      container.innerHTML = `<p class="empty-hint">暂无走势数据</p>`;
      return;
    }

    const width = 640;
    const height = 160;
    const padL = 35;
    const padR = 20;
    const padT = 20;
    const padB = 25;
    const chartW = width - padL - padR;
    const chartH = height - padT - padB;

    const maxAttempts = Math.max(5, ...recent.map((d) => d.attempts || 0));

    const step = chartW / recent.length;
    let barsHtml = "";
    const points = [];

    recent.forEach((item, idx) => {
      const x = padL + idx * step + step / 2;
      const barW = Math.max(8, step * 0.55);
      const barH = ((item.attempts || 0) / maxAttempts) * chartH;
      const barY = padT + (chartH - barH);

      barsHtml += `<rect x="${x - barW / 2}" y="${barY}" width="${barW}" height="${barH}" rx="3" fill="#e0f2fe" />`;

      const acc = item.accuracy || (item.attempts > 0 ? Math.round((item.correct / item.attempts) * 100) : 0);
      const lineY = padT + chartH * (1 - acc / 100);
      points.push({ x, y: lineY, acc, day: item.day.slice(5), attempts: item.attempts || 0 });
    });

    const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

    let dotsHtml = "";
    let labelsHtml = "";
    points.forEach((p, i) => {
      dotsHtml += `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#059669" stroke="#ffffff" stroke-width="2"><title>${p.day}: 练习 ${p.attempts} 题, 正确率 ${p.acc}%</title></circle>`;
      if (recent.length <= 14 || i % 3 === 0 || i === points.length - 1) {
        labelsHtml += `<text x="${p.x}" y="${height - 5}" font-size="10" fill="#9ca3af" text-anchor="middle">${p.day}</text>`;
      }
    });

    const svg = `
      <svg class="svg-chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <line x1="${padL}" y1="${padT}" x2="${width - padR}" y2="${padT}" stroke="#f1f5f9" />
        <line x1="${padL}" y1="${padT + chartH / 2}" x2="${width - padR}" y2="${padT + chartH / 2}" stroke="#f1f5f9" stroke-dasharray="3,3" />
        <line x1="${padL}" y1="${padT + chartH}" x2="${width - padR}" y2="${padT + chartH}" stroke="#cbd5e1" />

        <text x="${padL - 5}" y="${padT + 4}" font-size="10" fill="#9ca3af" text-anchor="end">100%</text>
        <text x="${padL - 5}" y="${padT + chartH / 2 + 4}" font-size="10" fill="#9ca3af" text-anchor="end">50%</text>
        <text x="${padL - 5}" y="${padT + chartH + 4}" font-size="10" fill="#9ca3af" text-anchor="end">0%</text>

        ${barsHtml}
        <path d="${pathD}" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
        ${dotsHtml}
        ${labelsHtml}
      </svg>
    `;

    container.innerHTML = svg;
  }

  function renderCourseMatrix() {
    const list = document.getElementById("course-matrix-list");
    if (!list) return;
    const courses = cachedAnalytics?.courseBreakdown || [];
    if (courses.length === 0) {
      list.innerHTML = `<p class="empty-hint">当前暂无更多课程数据</p>`;
      return;
    }
    list.replaceChildren();
    courses.forEach((c) => {
      const row = document.createElement("div");
      row.className = "course-matrix-row";
      const percent = c.practicedCount > 0 ? Math.round((c.masteredCount / c.practicedCount) * 100) : 0;
      row.innerHTML = `
        <span class="matrix-course-name" title="${escapeHtml(c.courseId)}">${escapeHtml(state.courseTitles[c.courseId] || c.courseId)}</span>
        <div class="matrix-bar-wrap">
          <div class="matrix-bar-fill" style="width: ${percent}%;"></div>
        </div>
        <span class="matrix-stats-text">${c.masteredCount}/${c.practicedCount} (${percent}%)</span>
      `;
      list.appendChild(row);
    });
  }

  function renderWeakPoints() {
    const list = document.getElementById("weak-points-list");
    const empty = document.getElementById("weak-points-empty");
    if (!list) return;
    const weakPoints = cachedAnalytics?.weakPoints || [];
    list.replaceChildren();
    if (weakPoints.length === 0) {
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;

    weakPoints.forEach((w, idx) => {
      const item = document.createElement("div");
      item.className = "weak-point-item";
      const sentenceIdx = sentenceIndexForProgressKey(w.sentenceId);
      const posLabel = sentenceIdx !== -1 ? practicePositionLabel(sentenceIdx) : w.sentenceId;
      const sentenceText = (sentenceIdx !== -1 && state.manifest?.sentences?.[sentenceIdx])
        ? sourceText(state.manifest.sentences[sentenceIdx])
        : w.sentenceId;

      item.innerHTML = `
        <span class="weak-point-rank">#${idx + 1}</span>
        <div class="weak-point-content">
          <span class="weak-point-title">${escapeHtml(posLabel)}: ${escapeHtml(sentenceText)}</span>
          <span class="weak-point-meta">作答 ${w.attempts} 次 · 错误 ${w.failCount} 次 · 最近得分: ${w.lastScore}%</span>
        </div>
        <button class="quiet-button weak-point-btn" type="button">去练习</button>
      `;

      item.querySelector("button").addEventListener("click", () => {
        goToPractice(sentenceIdx);
      });
      list.appendChild(item);
    });
  }

  function renderDiagnostics() {
    const list = document.getElementById("diagnostics-list");
    if (!list) return;
    const diagnostics = cachedAnalytics?.diagnostics || [];
    list.replaceChildren();
    diagnostics.forEach((d) => {
      const item = document.createElement("div");
      item.className = `diagnostic-item is-${d.type || "info"}`;
      const icon = d.type === "success" ? "🎉" : (d.type === "warning" ? "⚠️" : "💡");
      item.innerHTML = `
        <span class="diagnostic-icon">${icon}</span>
        <div class="diagnostic-content">
          <strong>${escapeHtml(d.title)}</strong>
          <p>${escapeHtml(d.text)}</p>
        </div>
      `;
      list.appendChild(item);
    });
  }

  function studyLogFilters() {
    return {
      status: document.getElementById("logs-filter-status")?.value || "all",
      days: document.getElementById("logs-filter-days")?.value || "all",
      courseId: state.manifest ? stableCourseId(state.manifest) : "",
    };
  }

  function studyLogUrl(limit, offset) {
    const filters = studyLogFilters();
    let url = `./api/study-logs?courseId=${encodeURIComponent(filters.courseId)}&limit=${limit}&offset=${offset}`;
    if (filters.status !== "all") url += `&status=${encodeURIComponent(filters.status)}`;
    if (filters.days === "today") url += `&day=${todayIso()}`;
    else if (filters.days === "7days") url += `&dateFrom=${dateDaysAgoIso(6)}&dateTo=${todayIso()}`;
    else if (filters.days === "30days") url += `&dateFrom=${dateDaysAgoIso(29)}&dateTo=${todayIso()}`;
    return url;
  }

  function filteredCachedStudyLogs() {
    const filters = studyLogFilters();
    const firstDay = filters.days === "7days"
      ? dateDaysAgoIso(6)
      : (filters.days === "30days" ? dateDaysAgoIso(29) : "");
    return loadStoredArray(STUDY_LOGS_STORAGE_KEY)
      .filter((item) => !filters.courseId || item.courseId === filters.courseId)
      .filter((item) => {
        if (filters.status === "wrong") return !item.isCorrect || Number(item.score || 0) < 100;
        if (filters.status === "correct") return item.isCorrect && Number(item.score || 0) >= 100;
        return true;
      })
      .filter((item) => {
        const localDay = item.localDay || String(item.createdAt || "").slice(0, 10);
        if (filters.days === "today") return localDay === todayIso();
        if (firstDay) return localDay >= firstDay && localDay <= todayIso();
        return true;
      })
      .sort((a, b) => String(b.createdAt || "").localeCompare(String(a.createdAt || "")));
  }

  async function loadStudyLogs() {
    const list = document.getElementById("logs-list");
    const empty = document.getElementById("logs-empty-hint");
    const info = document.getElementById("logs-count-info");
    const pagination = document.getElementById("logs-pagination");
    const pageInd = document.getElementById("logs-page-indicator");
    const prevBtn = document.getElementById("logs-prev-page");
    const nextBtn = document.getElementById("logs-next-page");

    if (!list) return;
    let data = null;
    if (state.backendAvailable) {
      try {
        const res = await apiFetch(studyLogUrl(LOGS_PER_PAGE, logsPage * LOGS_PER_PAGE));
        if (res.ok) data = await res.json();
      } catch (e) {
        console.warn("Failed to load study logs", e);
      }
    }

    if (data) {
      const cached = loadStoredArray(STUDY_LOGS_STORAGE_KEY);
      const merged = new Map(cached.map((item) => [item.id, item]));
      (data.items || []).forEach((item) => merged.set(item.id, item));
      saveStoredValue(STUDY_LOGS_STORAGE_KEY, [...merged.values()]
        .sort((a, b) => String(b.createdAt || "").localeCompare(String(a.createdAt || "")))
        .slice(0, 5000));
    } else {
      const cached = filteredCachedStudyLogs();
      const offset = logsPage * LOGS_PER_PAGE;
      data = {
        items: cached.slice(offset, offset + LOGS_PER_PAGE),
        total: cached.length,
        hasMore: offset + LOGS_PER_PAGE < cached.length,
        offline: true,
      };
    }

    const items = data.items || [];
    const total = data.total || 0;

    if (info) info.textContent = `${data.offline ? "离线缓存 · " : ""}共找到 ${total} 条练习记录 (第 ${logsPage + 1} 页)`;
    if (pageInd) pageInd.textContent = `第 ${logsPage + 1} / ${Math.max(1, Math.ceil(total / LOGS_PER_PAGE))} 页`;
    if (prevBtn) prevBtn.disabled = logsPage === 0;
    if (nextBtn) nextBtn.disabled = !data.hasMore;
    if (pagination) pagination.hidden = total <= LOGS_PER_PAGE;

    list.replaceChildren();
    if (items.length === 0) {
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;

    items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "log-item-card";
      const sentenceIdx = sentenceIndexForProgressKey(item.sentenceId);
      const posLabel = sentenceIdx !== -1 ? practicePositionLabel(sentenceIdx) : item.sentenceId;
      const targetText = (sentenceIdx !== -1 && state.manifest?.sentences?.[sentenceIdx])
        ? sourceText(state.manifest.sentences[sentenceIdx])
        : "";

      const timeStr = item.createdAt ? new Date(item.createdAt).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "";
      const durSec = Math.round((item.durationMs || 0) / 1000);

      card.innerHTML = `
        <div class="log-item-top">
          <span class="log-status-pill ${item.isCorrect ? "is-correct" : "is-wrong"}">
            ${item.isCorrect ? "✓ 满分" : `✗ 得分 ${item.score}%`}
          </span>
          <span class="log-time">${timeStr} · 耗时 ${durSec}s · 提示 ${item.hintCount || 0}次</span>
        </div>
        <div class="log-sentence-row">
          <strong>${escapeHtml(posLabel)}: ${escapeHtml(targetText)}</strong>
          <button class="quiet-button weak-point-btn" type="button">重练此句</button>
        </div>
        <div class="log-input-box">
          作答内容：${escapeHtml(item.userInput || "（未作答）")}
        </div>
      `;

      card.querySelector("button").addEventListener("click", () => {
        goToPractice(sentenceIdx);
      });
      list.appendChild(card);
    });
  }

  async function exportStudyLogsCsv() {
    let items = [];
    if (state.backendAvailable) {
      try {
        let offset = 0;
        while (true) {
          const res = await apiFetch(studyLogUrl(200, offset));
          if (!res.ok) break;
          const data = await res.json();
          items.push(...(data.items || []));
          if (!data.hasMore || !(data.items || []).length) break;
          offset += data.items.length;
        }
      } catch (e) {
        console.warn("Export failed", e);
      }
    }
    if (items.length === 0) items = filteredCachedStudyLogs();

    const header = ["createdAt", "courseId", "sentenceId", "userInput", "isCorrect", "score", "durationMs", "hintCount", "mode"];
    const rows = [header, ...items.map((i) => [
      i.createdAt || "",
      i.courseId || "",
      i.sentenceId || "",
      i.userInput || "",
      i.isCorrect ? "1" : "0",
      i.score || 0,
      i.durationMs || 0,
      i.hintCount || 0,
      i.mode || "dictation",
    ])];
    downloadCsv(`study-logs-${todayIso()}.csv`, rows);
  }

  async function handleClearLogs() {
    if (!confirm("确定要清空当前课程的做题记录吗？这不会影响生词本与笔记。")) return;
    const courseId = state.manifest ? stableCourseId(state.manifest) : "";
    await syncLearningMutation(
      "DELETE",
      `./api/study-logs?courseId=${encodeURIComponent(courseId)}`,
      undefined,
    );
    saveStoredValue(
      STUDY_LOGS_STORAGE_KEY,
      loadStoredArray(STUDY_LOGS_STORAGE_KEY).filter((item) => item.courseId !== courseId),
    );
    logsPage = 0;
    await refreshData();
  }

  return { init, open, refreshData, refreshStats: refreshData };
})();

const StatsManager = AnalyticsManager;

// ---------------------------------------------------------------------------

async function initLearningData() {
  sessionToken = await acquireSessionToken();
  const probe = await probeBackend();
  state.backendAvailable = probe.ok;
  LearningDataSync.configure({
    sender: sendLearningSyncOperation,
    isOnline: () => Boolean(state.backendAvailable && navigator.onLine),
  });
  LearningDataSync.subscribe((pending) => {
    const status = document.getElementById("sync-pending-status");
    if (status) {
      status.textContent = pending > 0
        ? `${pending} 项离线更改等待同步；本地副本已安全保存。`
        : "离线同步队列为空，所有更改均已保存。";
      status.classList.toggle("is-pending", pending > 0);
    }
  });
  if (state.backendAvailable) {
    BackendManager.setDbPath(probe.dbPath || "");
    const syncResult = await LearningDataSync.flush();
    if (syncResult.needsAttention) {
      console.warn("Some offline learning-data operations still need attention.");
    }
    const loaders = [loadVocabFromBackend(), loadNotesFromBackend(), loadActivityFromBackend()];
    if (state.manifest) loaders.push(loadProgressFromBackend());
    await Promise.all(loaders);
  } else {
    state.vocab = loadStoredArray(VOCAB_STORAGE_KEY);
    state.notesByCourse = loadStoredObject(notesStorageKey());
    state.allNotes = loadStoredArray(NOTES_ALL_STORAGE_KEY);
    if (state.allNotes.length === 0) state.allNotes = Object.values(state.notesByCourse);
    state.activityDays = loadStoredArray(ACTIVITY_STORAGE_KEY);
  }

  updateVocabCount();
  updateStarButtonUi();
  updateStreakUi();
  Library.init();
  BackendManager.init(state.backendAvailable, probe.dbPath);
  AnalyticsManager.init();
  learningDataInitialized = true;

  window.addEventListener("online", async () => {
    const nextProbe = await probeBackend();
    state.backendAvailable = nextProbe.ok;
    if (!state.backendAvailable) return;
    await LearningDataSync.flush();
    const loaders = [loadVocabFromBackend(), loadNotesFromBackend(), loadActivityFromBackend()];
    if (state.manifest) loaders.push(loadProgressFromBackend());
    await Promise.all(loaders);
    updateVocabCount();
    updatePersonalBadges();
  });
}

async function loadProgressFromBackend() {
  if (!state.manifest) return;
  try {
    const courseId = stableCourseId(state.manifest);
    const response = await apiFetch(`./api/progress?courseId=${encodeURIComponent(courseId)}`);
    if (!response.ok) return;
    const data = await response.json();
    if (data && data.progress && typeof data.progress === "object") {
      const keys = new Set([...Object.keys(state.progress), ...Object.keys(data.progress)]);
      const mergedProgress = {};
      keys.forEach((sentenceId) => {
        mergedProgress[sentenceId] = ProgressModel.merge(
          state.progress[sentenceId],
          data.progress[sentenceId],
        );
      });
      state.progress = mergedProgress;
      saveProgress();
      updateProgressUi();
      if (Object.keys(state.progress).length > 0) {
        await backendRequest("POST", "./api/progress", {
          courseId,
          progress: ProgressModel.toApiMap(state.progress),
        });
      }
    }
  } catch (e) {
    console.warn("Backend progress sync failed, using local copy.", e);
  }
}

async function probeBackend() {
  if (!navigator.onLine) return { ok: false, dbPath: "" };
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1500);
    const response = await apiFetch("./api/health", { signal: controller.signal });
    clearTimeout(timeout);
    const data = await response.json().catch(() => null);
    const isOk = Boolean(response.ok && data && data.ok === true);
    return { ok: isOk, dbPath: data?.dbPath || "" };
  } catch {
    return { ok: false, dbPath: "" };
  }
}

function notesStorageKey(courseId = "") {
  const cId = courseId || stableCourseId(state.manifest);
  return `dictation-notes:v1:${cId}`;
}

function loadStoredArray(key) {
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function saveStoredValue(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Learning data remains usable for this session in private browsing
  }
}

async function backendRequest(method, path, body) {
  if (!state.backendAvailable) return null;
  try {
    const response = await apiFetch(path, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      await response.text().catch(() => undefined);
      throw new Error(`${method} ${path} failed (HTTP ${response.status})`);
    }
    return await response.json();
  } catch (error) {
    console.warn("Local backend sync failed; the change is still saved locally.", error);
    return null;
  }
}

/** Authenticated transport used by the durable offline outbox.
 *
 * The service worker turns a transport failure on /api/* into HTTP 200 with
 * `{ok:false}` so routine health probes remain quiet. A mutation must treat that
 * synthetic body as a failure, otherwise the outbox would discard unsent data.
 */
async function sendLearningSyncOperation(operation) {
  const response = await apiFetch(operation.path, {
    method: operation.method,
    headers: {
      ...(operation.body !== null && operation.body !== undefined ? { "Content-Type": "application/json" } : {}),
      "X-Learning-Operation-Id": operation.id,
    },
    body: operation.body !== null && operation.body !== undefined
      ? JSON.stringify(operation.body)
      : undefined,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok || data?.ok === false) {
    throw new Error(`${operation.method} ${operation.path} failed (HTTP ${response.status})`);
  }
  return data;
}

async function syncLearningMutation(method, path, body, options = {}) {
  return LearningDataSync.mutate(method, path, body, options);
}

async function loadVocabFromBackend() {
  const localItems = loadStoredArray(VOCAB_STORAGE_KEY);
  try {
    const response = await apiFetch("./api/vocab");
    if (!response.ok) throw new Error("vocab fetch failed");
    const data = await response.json();
    state.vocab = PersonalDataTools.dedupeVocabEntries(LearningDataSync.mergeItems(
      localItems,
      Array.isArray(data.items) ? data.items : [],
      { entityType: "vocab", keyOf: (item) => item.id },
    ));
    saveStoredValue(VOCAB_STORAGE_KEY, state.vocab);
  } catch (error) {
    console.warn("Falling back to the local vocab cache.", error);
    state.vocab = loadStoredArray(VOCAB_STORAGE_KEY);
  }
}

async function loadNotesFromBackend() {
  const courseId = stableCourseId(state.manifest);
  const localCurrent = courseId ? Object.values(loadStoredObject(notesStorageKey(courseId))) : [];
  const localAll = loadStoredArray(NOTES_ALL_STORAGE_KEY);
  try {
    const response = await apiFetch("./api/notes?allCourses=true");
    if (!response.ok) throw new Error("notes fetch failed");
    const data = await response.json();
    const items = LearningDataSync.mergeItems(
      [...localAll, ...localCurrent],
      Array.isArray(data.items) ? data.items : [],
      { entityType: "note", keyOf: (item) => `${item.courseId}/${item.sentenceId}` },
    );
    state.allNotes = items;
    const byCourse = Object.create(null);
    items.filter((item) => item.courseId === courseId).forEach((item) => {
      byCourse[item.sentenceId] = item;
    });
    state.notesByCourse = byCourse;
    if (courseId) saveStoredValue(notesStorageKey(courseId), state.notesByCourse);
    saveStoredValue(NOTES_ALL_STORAGE_KEY, state.allNotes);
  } catch (error) {
    console.warn("Falling back to the local notes cache.", error);
    state.notesByCourse = courseId ? loadStoredObject(notesStorageKey(courseId)) : {};
    state.allNotes = localAll.length > 0 ? localAll : Object.values(state.notesByCourse);
  }
}

async function loadActivityFromBackend() {
  const localDays = loadStoredArray(ACTIVITY_STORAGE_KEY);
  try {
    const response = await apiFetch("./api/activity");
    if (!response.ok) throw new Error("activity fetch failed");
    const data = await response.json();
    state.activityDays = [...new Set([
      ...localDays,
      ...(Array.isArray(data.days) ? data.days : []),
    ])].sort();
    saveStoredValue(ACTIVITY_STORAGE_KEY, state.activityDays);
  } catch (error) {
    console.warn("Falling back to the local activity cache.", error);
    state.activityDays = loadStoredArray(ACTIVITY_STORAGE_KEY);
  }
}

function hideSelectionBubble() {
  if (elements.selectionBubble) elements.selectionBubble.hidden = true;
  selectionAddPendingText = "";
  selectionAddPendingContext = null;
}

function showSelectionBubble(text, rect, context = null) {
  if (!elements.selectionBubble || !text) return;
  selectionAddPendingText = text;
  selectionAddPendingContext = context;
  elements.selectionBubble.hidden = false;
  const bubbleWidth = elements.selectionBubble.offsetWidth || 160;
  const bubbleHeight = elements.selectionBubble.offsetHeight || 38;
  let left = rect.left + rect.width / 2 - bubbleWidth / 2;
  left = Math.max(10, Math.min(window.innerWidth - bubbleWidth - 10, left));
  let top = rect.top - bubbleHeight - 8;
  if (top < 10) top = rect.bottom + 8;
  elements.selectionBubble.style.left = `${left}px`;
  elements.selectionBubble.style.top = `${top}px`;
}

function handleSelectionChange() {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) {
    hideSelectionBubble();
    return;
  }
  const text = sel.toString().trim();
  if (!text || text.length > 80) {
    hideSelectionBubble();
    return;
  }

  const range = sel.getRangeAt(0);
  const commonAncestor = range.commonAncestorContainer;
  const element = commonAncestor.nodeType === Node.ELEMENT_NODE ? commonAncestor : commonAncestor.parentElement;

  const lyricItem = element ? element.closest(".lyric-item") : null;
  const dictationPane = element ? element.closest("#dictation-form-pane, .feedback-card, .practice-card") : null;

  if (lyricItem) {
    const idx = Number(lyricItem.dataset.index);
    const sentence = (Number.isInteger(idx) && state.manifest?.sentences?.[idx]) || currentSentence();
    const rect = range.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      showSelectionBubble(text, rect, {
        sourceText: sentence ? sourceText(sentence) : text,
        sentenceId: sentence ? sentenceProgressKey(idx) : "",
        sentenceIndex: Number.isInteger(idx) ? idx : state.index,
      });
    }
  } else if (dictationPane) {
    const sentence = currentSentence();
    const rect = range.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      showSelectionBubble(text, rect, {
        sourceText: sentence ? sourceText(sentence) : text,
        sentenceId: sentence ? sentenceProgressKey(state.index) : "",
        sentenceIndex: state.index,
      });
    }
  } else {
    hideSelectionBubble();
  }
}

function closeAnyPopover() {
  let closedSomething = false;
  if (!elements.notePopover.hidden) {
    closeNotePopover();
    closedSomething = true;
  }
  if (!elements.vocabQuickadd.hidden) {
    closeVocabQuickadd();
    closedSomething = true;
  }
  if (elements.selectionBubble && !elements.selectionBubble.hidden) {
    hideSelectionBubble();
    closedSomething = true;
  }
  return closedSomething;
}

function positionPopover(popoverEl, anchorEl) {
  anchorEl.scrollIntoView({ block: "nearest", inline: "nearest" });
  const anchorRect = anchorEl.getBoundingClientRect();
  const width = popoverEl.offsetWidth || 340;
  const height = popoverEl.offsetHeight || 220;
  let left = anchorRect.left;
  if (left + width > window.innerWidth - 16) left = window.innerWidth - width - 16;
  left = Math.max(16, left);
  let top = anchorRect.bottom + 8;
  if (top + height > window.innerHeight - 16) {
    top = anchorRect.top - height - 8;
  }
  top = Math.max(16, Math.min(top, window.innerHeight - height - 16));
  popoverEl.style.left = `${left}px`;
  popoverEl.style.top = `${top}px`;
}

// ---------------------------------------------------------------------------
// Notes & Key Sentences Notebook
// ---------------------------------------------------------------------------

let activeNoteSentenceIndex = null;

function noteForSentence(sentenceIndex) {
  if (!state.notesByCourse) return null;
  return state.notesByCourse[sentenceProgressKey(sentenceIndex)] || null;
}

function currentNote() {
  return noteForSentence(state.index);
}

function updateLyricsStarUi() {
  if (!elements.lyricsList) return;
  const items = elements.lyricsList.querySelectorAll(".lyric-item");
  items.forEach((item) => {
    const idx = Number(item.dataset.index);
    if (!Number.isInteger(idx)) return;
    const note = noteForSentence(idx);
    const starred = Boolean(note?.starred);
    const hasText = Boolean(note?.text);
    const starBtn = item.querySelector(".lyric-star-btn");
    if (starBtn) {
      starBtn.textContent = starred ? "★" : (hasText ? "✎" : "☆");
      starBtn.classList.toggle("active", starred || hasText);
      starBtn.setAttribute("aria-pressed", String(starred || hasText));
      starBtn.title = starred ? "已标为重点句（点击编辑笔记）" : (hasText ? "已有笔记（点击编辑）" : "标为重点句 / 写笔记");
    }
  });
}

function updateStarButtonUi() {
  const starred = Boolean(currentNote()?.starred);
  elements.starButton.textContent = starred ? "★" : "☆";
  elements.starButton.classList.toggle("active", starred);
  elements.starButton.setAttribute("aria-pressed", String(starred));
  updateLyricsStarUi();
}

function openNotePopover(sentenceIndex = null, anchorEl = null, prefillText = "") {
  const targetIndex = sentenceIndex !== null && sentenceIndex !== undefined ? sentenceIndex : state.index;
  if (!elements.notePopover.hidden && activeNoteSentenceIndex === targetIndex && !prefillText) {
    closeNotePopover();
    return;
  }
  activeNoteSentenceIndex = targetIndex;
  const note = noteForSentence(targetIndex);
  elements.noteStarCheckbox.checked = Boolean(note?.starred);
  if (note?.text) {
    elements.noteTextarea.value = note.text;
  } else if (prefillText) {
    elements.noteTextarea.value = prefillText;
  } else {
    elements.noteTextarea.value = "";
  }
  elements.notePopover.hidden = false;
  const anchor = anchorEl || elements.starButton;
  positionPopover(elements.notePopover, anchor);
  elements.noteTextarea.focus();
}

function closeNotePopover() {
  elements.notePopover.hidden = true;
  activeNoteSentenceIndex = null;
}

async function saveNoteFromPopover() {
  const targetIndex = activeNoteSentenceIndex !== null ? activeNoteSentenceIndex : state.index;
  const text = elements.noteTextarea.value.trim();
  const starred = elements.noteStarCheckbox.checked;
  closeNotePopover();
  await saveNoteEntry(targetIndex, { text, starred });
}

async function saveNoteEntry(sentenceIndex, { text, tag = "", sourceText: sText = "", starred }) {
  const courseId = stableCourseId(state.manifest);
  const sentenceId = sentenceProgressKey(sentenceIndex);
  const sentenceObj = state.manifest?.sentences?.[sentenceIndex];
  const autoSourceText = sText || (sentenceObj ? sourceText(sentenceObj) : "");

  if (!text && !starred) {
    await deleteNoteEntry(courseId, sentenceId);
    return;
  }
  const timestamp = new Date().toISOString();
  const existing = state.notesByCourse[sentenceId];
  const itemData = {
    id: existing?.id || `local_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    courseId,
    sentenceId,
    text,
    tag: tag || existing?.tag || "",
    sourceText: autoSourceText || existing?.sourceText || "",
    starred,
    createdAt: existing?.createdAt || timestamp,
    updatedAt: timestamp,
  };
  state.notesByCourse[sentenceId] = itemData;
  const allIdx = state.allNotes.findIndex((n) => n.courseId === courseId && n.sentenceId === sentenceId);
  if (allIdx >= 0) state.allNotes[allIdx] = itemData;
  else state.allNotes.unshift(itemData);

  persistNotesForCourse();
  updateStarButtonUi();
  renderNotesList();
  const { result } = await syncLearningMutation(
    "PUT",
    `./api/notes/${encodeURIComponent(courseId)}/${encodeURIComponent(sentenceId)}`,
    { text, tag: itemData.tag, sourceText: itemData.sourceText, starred },
    { entityType: "note", entityKey: `${courseId}/${sentenceId}` },
  );
  if (result?.item) {
    state.notesByCourse[sentenceId] = result.item;
    const idx2 = state.allNotes.findIndex((n) => n.courseId === courseId && n.sentenceId === sentenceId);
    if (idx2 >= 0) state.allNotes[idx2] = result.item;
    persistNotesForCourse();
    renderNotesList();
  }
}

async function deleteNoteEntry(courseId, sentenceId) {
  if (courseId === stableCourseId(state.manifest)) {
    delete state.notesByCourse[sentenceId];
    persistNotesForCourse();
  }
  state.allNotes = state.allNotes.filter((n) => !(n.courseId === courseId && n.sentenceId === sentenceId));
  persistNotesForCourse();
  renderNotesList();
  if (courseId === stableCourseId(state.manifest) && sentenceId === sentenceProgressKey(state.index)) {
    updateStarButtonUi();
  }
  await syncLearningMutation(
    "DELETE",
    `./api/notes/${encodeURIComponent(courseId)}/${encodeURIComponent(sentenceId)}`,
    undefined,
    { entityType: "note", entityKey: `${courseId}/${sentenceId}` },
  );
}

function persistNotesForCourse() {
  saveStoredValue(notesStorageKey(), state.notesByCourse);
  saveStoredValue(NOTES_ALL_STORAGE_KEY, state.allNotes);
}

function setNotesScope(scope) {
  state.notesScope = scope;
  if (elements.notesScopeCurrent) elements.notesScopeCurrent.classList.toggle("active", scope === "current");
  if (elements.notesScopeAll) elements.notesScopeAll.classList.toggle("active", scope === "all");
  renderNotesList();
}

function showInlineMessage(node, text, isError = false) {
  if (!node) return;
  node.textContent = text;
  node.classList.toggle("is-error", Boolean(isError));
  node.hidden = false;
}

function hideInlineMessage(node) {
  if (!node) return;
  node.textContent = "";
  node.classList.remove("is-error");
  node.hidden = true;
}

function openNoteAddForm() {
  if (!state.manifest) return;
  const indexes = allCoursePracticeIndexes();
  const position = indexes.indexOf(state.index);
  elements.noteAddPosition.max = String(indexes.length);
  elements.noteAddPosition.value = String(position === -1 ? 1 : position + 1);
  elements.noteAddText.value = "";
  if (elements.noteAddTag) elements.noteAddTag.value = "";
  elements.noteAddStar.checked = false;
  noteAddLoadedIndex = -2;
  noteAddLoadedText = "";
  hideInlineMessage(elements.noteAddMessage);
  syncNoteAddTarget();
  elements.noteAddForm.hidden = false;
  elements.noteAddButton.setAttribute("aria-expanded", "true");
  elements.noteAddText.focus();
}

function closeNoteAddForm() {
  elements.noteAddForm.hidden = true;
  elements.noteAddButton.setAttribute("aria-expanded", "false");
  hideInlineMessage(elements.noteAddMessage);
  noteAddLoadedIndex = -2;
}

let noteAddLoadedIndex = -2;
let noteAddLoadedText = "";
let editingVocabId = "";

function syncNoteAddTarget() {
  const targetIndex = noteAddTargetIndex();
  if (targetIndex === noteAddLoadedIndex) return;
  const sentence = targetIndex === -1 ? null : state.manifest.sentences[targetIndex];
  elements.noteAddPreview.textContent = sentence
    ? sourceText(sentence)
    : `请输入 1–${allCoursePracticeIndexes().length} 之间的编号。`;
  const existing = targetIndex === -1 ? null : state.notesByCourse[sentenceProgressKey(targetIndex)];
  const existingText = existing?.text || "";
  if (elements.noteAddText.value === noteAddLoadedText) {
    elements.noteAddText.value = existingText;
    elements.noteAddStar.checked = Boolean(existing?.starred);
    if (elements.noteAddTag) elements.noteAddTag.value = existing?.tag || "";
    noteAddLoadedText = existingText;
    hideInlineMessage(elements.noteAddMessage);
  } else if (existingText || existing?.starred) {
    showInlineMessage(elements.noteAddMessage, "这句已经有笔记了，保存会覆盖原来的内容。");
  } else {
    hideInlineMessage(elements.noteAddMessage);
  }
  noteAddLoadedIndex = targetIndex;
}

function noteAddTargetIndex() {
  const position = Number(elements.noteAddPosition.value);
  if (!Number.isInteger(position)) return -1;
  const index = allCoursePracticeIndexes()[position - 1];
  return Number.isInteger(index) ? index : -1;
}

async function saveNoteFromDialog() {
  const targetIndex = noteAddTargetIndex();
  if (targetIndex === -1) {
    showInlineMessage(
      elements.noteAddMessage,
      `请输入 1–${allCoursePracticeIndexes().length} 之间的句子编号。`,
      true,
    );
    elements.noteAddPosition.focus();
    return;
  }
  const text = elements.noteAddText.value.trim();
  const tag = elements.noteAddTag ? elements.noteAddTag.value.trim() : "";
  const starred = elements.noteAddStar.checked;
  if (!text && !starred) {
    showInlineMessage(elements.noteAddMessage, "写点笔记内容，或勾选「标为重点句」。", true);
    elements.noteAddText.focus();
    return;
  }
  closeNoteAddForm();
  await saveNoteEntry(targetIndex, { text, tag, starred });
}

function sentenceIndexForProgressKey(key) {
  if (!state.manifest || !key) return -1;
  if (key.startsWith("legacy:")) {
    const index = Number(key.slice("legacy:".length));
    return Number.isInteger(index) ? index : -1;
  }
  return state.manifest.sentences.findIndex((sentence) => sentence.id === key);
}

function practicePositionLabel(sentenceIndex) {
  const position = allCoursePracticeIndexes().indexOf(sentenceIndex);
  return position === -1 ? "?" : String(position + 1);
}

function notesSortKey(sentenceId) {
  const index = sentenceIndexForProgressKey(sentenceId);
  if (index === -1) return Number.MAX_SAFE_INTEGER;
  const position = allCoursePracticeIndexes().indexOf(index);
  return position === -1 ? Number.MAX_SAFE_INTEGER : position;
}

function renderNotesList() {
  const isAll = state.notesScope === "all";
  const query = (elements.notesSearchInput?.value || "").trim().toLowerCase();
  const selectedTag = elements.notesTagFilter?.value || "";
  const starredOnly = Boolean(elements.notesFilterStarred?.checked);

  let rawList = isAll
    ? (state.allNotes.length > 0 ? state.allNotes : Object.values(state.notesByCourse))
    : Object.values(state.notesByCourse);

  const filtered = rawList.filter((note) => {
    if (!note.starred && !note.text) return false;
    if (starredOnly && !note.starred) return false;
    if (selectedTag && note.tag !== selectedTag) return false;
    if (query) {
      const hay = `${note.text || ""} ${note.sourceText || ""} ${note.tag || ""} ${note.courseId || ""}`.toLowerCase();
      if (!hay.includes(query)) return false;
    }
    return true;
  });

  if (!isAll) {
    filtered.sort((a, b) => notesSortKey(a.sentenceId) - notesSortKey(b.sentenceId));
  } else {
    filtered.sort((a, b) => (b.updatedAt || "").localeCompare(a.updatedAt || ""));
  }

  if (elements.notesCount) elements.notesCount.textContent = String(filtered.length);
  updatePersonalBadges();

  elements.notesList.replaceChildren();
  elements.notesEmptyHint.hidden = filtered.length > 0;

  filtered.forEach((note) => {
    const isCurrentCourse = !note.courseId || note.courseId === stableCourseId(state.manifest);
    const sentenceIndex = isCurrentCourse ? sentenceIndexForProgressKey(note.sentenceId) : -1;
    const row = document.createElement("div");
    row.className = "entry-row";

    const head = document.createElement("div");
    head.className = "entry-row-head";
    const term = document.createElement("span");
    term.className = "entry-term";

    if (isCurrentCourse) {
      term.textContent = `${note.starred ? "★ " : ""}第 ${practicePositionLabel(sentenceIndex)} 题`;
    } else {
      term.textContent = `${note.starred ? "★ " : ""}[${state.courseTitles[note.courseId] || note.courseId || "跨课程"}]`;
    }
    head.appendChild(term);

    if (note.tag) {
      const tagChip = document.createElement("span");
      tagChip.className = "tag-chip";
      tagChip.textContent = note.tag;
      head.appendChild(tagChip);
    }
    row.appendChild(head);

    const sText = (isCurrentCourse && sentenceIndex !== -1)
      ? sourceText(state.manifest.sentences[sentenceIndex])
      : (note.sourceText || "");

    if (sText) {
      const meta = document.createElement("div");
      meta.className = "entry-meta";
      meta.textContent = sText;
      row.appendChild(meta);
    }

    if (note.text) {
      const noteEl = document.createElement("p");
      noteEl.className = "entry-note";
      noteEl.textContent = note.text;
      row.appendChild(noteEl);
    }

    const actions = document.createElement("div");
    actions.className = "entry-actions";

    if (isCurrentCourse && sentenceIndex !== -1) {
      const jumpButton = document.createElement("button");
      jumpButton.className = "quiet-button";
      jumpButton.type = "button";
      jumpButton.textContent = "跳转练这句";
      jumpButton.addEventListener("click", () => {
        goToPractice(sentenceIndex, { dictation: false });
      });
      actions.appendChild(jumpButton);
    }

    const deleteButton = document.createElement("button");
    deleteButton.className = "quiet-button danger-text";
    deleteButton.type = "button";
    deleteButton.textContent = "删除";
    deleteButton.addEventListener("click", () => {
      if (window.confirm("确定要删除这条笔记吗？")) deleteNoteEntry(note.courseId, note.sentenceId);
    });
    actions.appendChild(deleteButton);
    row.appendChild(actions);

    elements.notesList.appendChild(row);
  });
}

function exportNotesMarkdown() {
  const isAll = state.notesScope === "all";
  const notes = isAll ? state.allNotes : Object.values(state.notesByCourse);
  let md = `# 学习笔记与重点句汇编 (${isAll ? "全部课程" : state.manifest?.title || "听写"})\n\n`;
  md += `导出时间：${new Date().toLocaleString()}\n\n---\n\n`;

  notes.forEach((note, i) => {
    md += `### ${i + 1}. ${note.starred ? "★ " : ""}${note.courseId || "本课程"} · ${note.tag || "笔记"}\n\n`;
    if (note.sourceText) md += `> **原文例句**：${note.sourceText}\n\n`;
    if (note.text) md += `**笔记分析**：\n${note.text}\n\n`;
    md += `---\n\n`;
  });

  const blob = new Blob(["\uFEFF", md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `notes-${todayIso()}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Vocab Notebook & SRS Spaced Repetition
// ---------------------------------------------------------------------------

function isVocabQuickaddTrigger(target) {
  return Boolean(
    target instanceof Element && target.closest(
      "#add-vocab-button, #selection-add-button, #selection-bubble, .selection-bubble-btn, .lyric-vocab-btn"
    )
  );
}

let vocabQuickAddContext = null;

function openVocabQuickAdd({ term, meaning, reading, note, sourceText: quickAddSourceText, sentenceId, anchor }) {
  elements.vocabTermInput.value = term || "";
  elements.vocabMeaningInput.value = meaning || "";
  elements.vocabNoteInput.value = note || "";
  vocabQuickAddContext = {
    sourceText: quickAddSourceText || "",
    sentenceId: sentenceId !== undefined ? sentenceId : sentenceProgressKey(state.index),
    reading: reading || "",
  };
  elements.vocabQuickadd.hidden = false;
  if (anchor) positionPopover(elements.vocabQuickadd, anchor);
  elements.vocabTermInput.focus();
  elements.vocabTermInput.select();
}

function closeVocabQuickadd() {
  elements.vocabQuickadd.hidden = true;
  vocabQuickAddContext = null;
}

async function saveVocabQuickAdd() {
  const term = elements.vocabTermInput.value.trim();
  if (!term) {
    elements.vocabTermInput.focus();
    return;
  }
  const context = vocabQuickAddContext;
  closeVocabQuickadd();
  await addVocabEntry({
    term,
    reading: context?.reading || "",
    meaning: elements.vocabMeaningInput.value,
    note: elements.vocabNoteInput.value,
    sourceText: context?.sourceText || "",
    sentenceId: context?.sentenceId,
  });
}

async function addVocabEntry({ term, reading, level = "", tags = [], meaning, note, sourceText: entrySourceText, sentenceId }) {
  const trimmedTerm = String(term || "").trim();
  if (!trimmedTerm) return null;
  const tagList = Array.isArray(tags) ? tags : String(tags || "").split(/[,，]/).map((t) => t.trim()).filter(Boolean);
  const payload = {
    term: trimmedTerm,
    reading: String(reading || "").trim(),
    meaning: String(meaning || "").trim(),
    note: String(note || "").trim(),
    level: String(level || "").trim(),
    tags: tagList,
    courseId: state.manifest ? stableCourseId(state.manifest) : "",
    sentenceId: sentenceId === undefined ? sentenceProgressKey(state.index) : String(sentenceId || ""),
    sourceText: String(entrySourceText || "").trim(),
    srsStage: 0,
    srsInterval: 0,
    srsEase: 2.5,
    srsRepetitions: 0,
    nextReviewAt: "",
  };
  const timestamp = new Date().toISOString();
  const localEntry = {
    id: `local_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    mastered: false,
    createdAt: timestamp,
    updatedAt: timestamp,
    ...payload,
  };
  payload.id = localEntry.id;
  state.vocab.unshift(localEntry);
  persistVocabList();
  renderVocabList();
  updateVocabCount();
  const { result } = await syncLearningMutation("POST", "./api/vocab", payload, {
    entityType: "vocab",
    entityKey: localEntry.id,
  });
  if (result?.item) {
    const index = state.vocab.findIndex((entry) => entry.id === localEntry.id);
    if (index !== -1) state.vocab[index] = result.item;
    persistVocabList();
    renderVocabList();
  }
  return localEntry;
}

async function updateVocabEntry(id, patch) {
  const index = state.vocab.findIndex((entry) => entry.id === id);
  if (index === -1) return;
  state.vocab[index] = { ...state.vocab[index], ...patch, updatedAt: new Date().toISOString() };
  persistVocabList();
  renderVocabList();
  await syncLearningMutation("PATCH", `./api/vocab/${encodeURIComponent(id)}`, patch, {
    entityType: "vocab",
    entityKey: id,
  });
}

function allCoursePracticeIndexes() {
  return state.coursePracticeIndexes?.length
    ? state.coursePracticeIndexes
    : (state.practiceIndexes || []);
}

async function deleteVocabEntry(id) {
  const target = state.vocab.find((entry) => entry.id === id);
  if (target && !window.confirm(`确定要删除生词「${target.term}」吗？`)) return;
  state.vocab = state.vocab.filter((entry) => entry.id !== id);
  state.selectedVocabIds.delete(id);
  persistVocabList();
  renderVocabList();
  updateVocabCount();
  await syncLearningMutation("DELETE", `./api/vocab/${encodeURIComponent(id)}`, undefined, {
    entityType: "vocab",
    entityKey: id,
  });
}

function persistVocabList() {
  saveStoredValue(VOCAB_STORAGE_KEY, state.vocab);
}

function setVocabStatusFilter(status) {
  state.vocabStatusFilter = status;
  [
    elements.vocabTabAll,
    elements.vocabTabDue,
    elements.vocabTabNew,
    elements.vocabTabLearning,
    elements.vocabTabMastered,
  ].forEach((tab) => {
    if (!tab) return;
    const isThis = tab.id === `vocab-tab-${status}`;
    tab.classList.toggle("active", isThis);
    tab.setAttribute("aria-selected", String(isThis));
  });
  renderVocabList();
}

function openVocabAddForm(entry = null) {
  clearVocabAddFields();
  editingVocabId = entry?.id || "";
  if (entry) {
    elements.vocabAddTerm.value = entry.term || "";
    elements.vocabAddReading.value = entry.reading || "";
    elements.vocabAddMeaning.value = entry.meaning || "";
    elements.vocabAddNote.value = entry.note || "";
    if (elements.vocabAddLevel) elements.vocabAddLevel.value = entry.level || "";
    if (elements.vocabAddTags) elements.vocabAddTags.value = Array.isArray(entry.tags) ? entry.tags.join(", ") : "";
    elements.vocabAddLinkSentence.checked = false;
    elements.vocabAddLinkSentence.disabled = true;
    elements.vocabAddLinkLabel.textContent = "编辑时保留原有关联例句";
  } else {
    syncVocabAddSentenceLink();
  }
  hideInlineMessage(elements.vocabAddMessage);
  elements.vocabAddForm.hidden = false;
  elements.vocabAddButton.setAttribute("aria-expanded", "true");
  elements.vocabAddButton.textContent = entry ? "正在编辑生词" : "+ 新增生词";
  if (elements.vocabAddSave) elements.vocabAddSave.textContent = entry ? "保存修改" : "加入生词本";
  elements.vocabAddTerm.focus();
}

function closeVocabAddForm() {
  elements.vocabAddForm.hidden = true;
  elements.vocabAddButton.setAttribute("aria-expanded", "false");
  elements.vocabAddButton.textContent = "+ 新增生词";
  if (elements.vocabAddSave) elements.vocabAddSave.textContent = "加入生词本";
  hideInlineMessage(elements.vocabAddMessage);
  editingVocabId = "";
}

function clearVocabAddFields() {
  elements.vocabAddTerm.value = "";
  elements.vocabAddReading.value = "";
  elements.vocabAddMeaning.value = "";
  elements.vocabAddNote.value = "";
  if (elements.vocabAddLevel) elements.vocabAddLevel.value = "";
  if (elements.vocabAddTags) elements.vocabAddTags.value = "";
}

function syncVocabAddSentenceLink() {
  const example = state.manifest ? sourceText(currentSentence()) : "";
  const position = state.manifest ? allCoursePracticeIndexes().indexOf(state.index) : -1;
  elements.vocabAddLinkSentence.disabled = !example;
  elements.vocabAddLinkSentence.checked = Boolean(example);
  if (!example) {
    elements.vocabAddLinkLabel.textContent = "没有可关联的例句";
  } else if (position === -1) {
    elements.vocabAddLinkLabel.textContent = "关联当前句子作为例句";
  } else {
    elements.vocabAddLinkLabel.textContent = `关联第 ${position + 1} 题作为例句`;
  }
}

async function saveVocabFromDialog() {
  const term = elements.vocabAddTerm.value.trim();
  if (!term) {
    showInlineMessage(elements.vocabAddMessage, "请先填写词条。", true);
    elements.vocabAddTerm.focus();
    return;
  }
  const linked = !editingVocabId && elements.vocabAddLinkSentence.checked && !elements.vocabAddLinkSentence.disabled;
  const entry = {
    term,
    reading: elements.vocabAddReading.value.trim(),
    level: elements.vocabAddLevel ? elements.vocabAddLevel.value : "",
    tags: elements.vocabAddTags ? elements.vocabAddTags.value : "",
    meaning: elements.vocabAddMeaning.value.trim(),
    note: elements.vocabAddNote.value.trim(),
    sourceText: linked ? sourceText(currentSentence()) : "",
    sentenceId: linked ? sentenceProgressKey(state.index) : "",
  };
  if (!matchesVocabQuery(entry, elements.vocabSearchInput.value.trim().toLowerCase())) {
    elements.vocabSearchInput.value = "";
  }
  if (editingVocabId) {
    const id = editingVocabId;
    closeVocabAddForm();
    await updateVocabEntry(id, {
      term: entry.term,
      reading: entry.reading,
      level: entry.level,
      tags: Array.isArray(entry.tags) ? entry.tags : String(entry.tags || "").split(/[,，]/).map((tag) => tag.trim()).filter(Boolean),
      meaning: entry.meaning,
      note: entry.note,
    });
    return;
  }
  clearVocabAddFields();
  elements.vocabAddTerm.focus();
  showInlineMessage(elements.vocabAddMessage, `已加入「${term}」，可以接着添加下一个。`);
  await addVocabEntry(entry);
}

function updateVocabCount() {
  elements.vocabCount.textContent = String(state.vocab.length);
  updatePersonalBadges();
}

function matchesVocabQuery(entry, query) {
  if (!query) return true;
  const tagsStr = Array.isArray(entry.tags) ? entry.tags.join(" ") : String(entry.tags || "");
  const haystack = `${entry.term} ${entry.reading || ""} ${entry.meaning || ""} ${entry.note || ""} ${entry.level || ""} ${tagsStr}`.toLowerCase();
  return haystack.includes(query);
}

function isDueForReview(entry) {
  if (entry.mastered || (entry.srsStage || 0) === 3) return false;
  if (!entry.nextReviewAt) return true;
  return new Date(entry.nextReviewAt) <= new Date();
}

function renderVocabList() {
  const query = elements.vocabSearchInput.value.trim().toLowerCase();
  const status = state.vocabStatusFilter || "all";
  const levelFilter = state.vocabLevelFilter || "";
  const tagFilter = state.vocabTagFilter || "";

  // Compute status counts for badges
  const countAll = state.vocab.length;
  const countDue = state.vocab.filter(isDueForReview).length;
  const countNew = state.vocab.filter((v) => (v.srsStage || 0) === 0 && !v.mastered).length;
  const countLearning = state.vocab.filter((v) => ((v.srsStage || 0) === 1 || (v.srsStage || 0) === 2) && !v.mastered).length;
  const countMastered = state.vocab.filter((v) => (v.srsStage || 0) === 3 || v.mastered).length;

  if (elements.vocabBadgeAll) elements.vocabBadgeAll.textContent = String(countAll);
  if (elements.vocabBadgeDue) elements.vocabBadgeDue.textContent = String(countDue);
  if (elements.vocabBadgeNew) elements.vocabBadgeNew.textContent = String(countNew);
  if (elements.vocabBadgeLearning) elements.vocabBadgeLearning.textContent = String(countLearning);
  if (elements.vocabBadgeMastered) elements.vocabBadgeMastered.textContent = String(countMastered);
  if (elements.vocabCount) elements.vocabCount.textContent = String(countAll);

  // Dynamically populate tag filter dropdown if not active
  if (elements.vocabTagFilter) {
    const existingVal = elements.vocabTagFilter.value;
    const allTags = new Set();
    state.vocab.forEach((v) => {
      (Array.isArray(v.tags) ? v.tags : []).forEach((t) => allTags.add(t));
    });
    elements.vocabTagFilter.replaceChildren();
    const optAll = document.createElement("option");
    optAll.value = "";
    optAll.textContent = "全部标签";
    elements.vocabTagFilter.appendChild(optAll);
    Array.from(allTags).sort().forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      elements.vocabTagFilter.appendChild(opt);
    });
    elements.vocabTagFilter.value = existingVal;
  }

  const filtered = state.vocab.filter((entry) => {
    if (!matchesVocabQuery(entry, query)) return false;
    if (levelFilter && entry.level !== levelFilter) return false;
    if (tagFilter && !(Array.isArray(entry.tags) && entry.tags.includes(tagFilter))) return false;

    if (status === "due") return isDueForReview(entry);
    if (status === "new") return (entry.srsStage || 0) === 0 && !entry.mastered;
    if (status === "learning") return ((entry.srsStage || 0) === 1 || (entry.srsStage || 0) === 2) && !entry.mastered;
    if (status === "mastered") return (entry.srsStage || 0) === 3 || entry.mastered;
    return true;
  });

  elements.vocabList.replaceChildren();
  elements.vocabEmptyHint.hidden = filtered.length > 0;

  // Update batch bar
  updateBatchBarUi(filtered);

  filtered.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "entry-row";

    const head = document.createElement("div");
    head.className = "entry-row-head";

    // Batch checkbox
    const selectCheck = document.createElement("input");
    selectCheck.type = "checkbox";
    selectCheck.checked = state.selectedVocabIds.has(entry.id);
    selectCheck.style.marginRight = "8px";
    selectCheck.addEventListener("change", () => {
      if (selectCheck.checked) state.selectedVocabIds.add(entry.id);
      else state.selectedVocabIds.delete(entry.id);
      updateBatchBarUi(filtered);
    });
    head.appendChild(selectCheck);

    if (entry.level) {
      const lvl = document.createElement("span");
      lvl.className = "level-badge";
      lvl.textContent = entry.level;
      head.appendChild(lvl);
    }

    const term = document.createElement("span");
    term.className = `entry-term${entry.mastered ? " mastered" : ""}`;
    term.textContent = entry.term;
    head.appendChild(term);

    // Audio pronunciation button
    const speakBtn = document.createElement("button");
    speakBtn.type = "button";
    speakBtn.className = "tts-speaker-btn";
    speakBtn.title = "发音朗读";
    speakBtn.setAttribute("aria-label", `朗读 ${entry.term}`);
    speakBtn.textContent = "🔊";
    speakBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      speakText(entry.term);
    });
    head.appendChild(speakBtn);

    // SRS stage badge
    const stage = entry.mastered ? 3 : (entry.srsStage || 0);
    const stageLabels = ["🌱 新词", "🔄 学习中", "⚡ 强化中", "⭐ 稳固"];
    const stageBadge = document.createElement("span");
    stageBadge.className = `srs-stage-badge srs-stage-${stage}`;
    stageBadge.textContent = stageLabels[stage] || "生词";
    head.appendChild(stageBadge);

    // Tag chips
    if (Array.isArray(entry.tags)) {
      entry.tags.forEach((t) => {
        const chip = document.createElement("span");
        chip.className = "tag-chip";
        chip.textContent = t;
        head.appendChild(chip);
      });
    }

    const masteredLabel = document.createElement("label");
    masteredLabel.className = "note-star-check";
    masteredLabel.style.marginLeft = "auto";
    const masteredCheckbox = document.createElement("input");
    masteredCheckbox.type = "checkbox";
    masteredCheckbox.checked = Boolean(entry.mastered || stage === 3);
    masteredCheckbox.addEventListener("change", () => {
      updateVocabEntry(entry.id, { mastered: masteredCheckbox.checked, srsStage: masteredCheckbox.checked ? 3 : 1 });
    });
    masteredLabel.append(masteredCheckbox, document.createTextNode(" 掌握"));
    head.appendChild(masteredLabel);
    row.appendChild(head);

    if (entry.reading || entry.meaning) {
      const meta = document.createElement("div");
      meta.className = "entry-meta";
      meta.textContent = [entry.reading, entry.meaning].filter(Boolean).join(" · ");
      row.appendChild(meta);
    }
    if (entry.note) {
      const noteEl = document.createElement("p");
      noteEl.className = "entry-note";
      noteEl.textContent = entry.note;
      row.appendChild(noteEl);
    }
    if (entry.sourceText) {
      const source = document.createElement("div");
      source.className = "entry-meta";
      source.textContent = `例句：${entry.sourceText}`;
      row.appendChild(source);
    }

    const actions = document.createElement("div");
    actions.className = "entry-actions";

    const editButton = document.createElement("button");
    editButton.className = "quiet-button";
    editButton.type = "button";
    editButton.textContent = "编辑";
    editButton.addEventListener("click", () => openVocabAddForm(entry));
    actions.appendChild(editButton);

    const deleteButton = document.createElement("button");
    deleteButton.className = "quiet-button danger-text";
    deleteButton.type = "button";
    deleteButton.textContent = "删除";
    deleteButton.addEventListener("click", () => deleteVocabEntry(entry.id));
    actions.appendChild(deleteButton);
    row.appendChild(actions);

    elements.vocabList.appendChild(row);
  });
}

function updateBatchBarUi(currentFilteredList = []) {
  if (!elements.vocabBatchBar) return;
  const count = state.selectedVocabIds.size;
  if (count > 0) {
    elements.vocabBatchBar.hidden = false;
    elements.vocabSelectedCount.textContent = `已选 ${count} 项`;
    if (elements.vocabSelectAll) {
      elements.vocabSelectAll.checked = currentFilteredList.length > 0 && currentFilteredList.every((v) => state.selectedVocabIds.has(v.id));
    }
  } else {
    elements.vocabBatchBar.hidden = true;
    if (elements.vocabSelectAll) elements.vocabSelectAll.checked = false;
  }
}

function toggleVocabSelectAll(checked) {
  const query = elements.vocabSearchInput.value.trim().toLowerCase();
  const status = state.vocabStatusFilter || "all";
  const filtered = state.vocab.filter((entry) => {
    if (!matchesVocabQuery(entry, query)) return false;
    if (status === "due") return isDueForReview(entry);
    if (status === "new") return (entry.srsStage || 0) === 0 && !entry.mastered;
    if (status === "learning") return ((entry.srsStage || 0) === 1 || (entry.srsStage || 0) === 2) && !entry.mastered;
    if (status === "mastered") return (entry.srsStage || 0) === 3 || entry.mastered;
    return true;
  });

  if (checked) {
    filtered.forEach((v) => state.selectedVocabIds.add(v.id));
  } else {
    filtered.forEach((v) => state.selectedVocabIds.delete(v.id));
  }
  renderVocabList();
}

async function handleVocabBatchMaster() {
  const ids = Array.from(state.selectedVocabIds);
  if (ids.length === 0) return;
  ids.forEach((id) => {
    const entry = state.vocab.find((v) => v.id === id);
    if (entry) {
      entry.mastered = true;
      entry.srsStage = 3;
    }
  });
  persistVocabList();
  state.selectedVocabIds.clear();
  renderVocabList();
  await syncLearningMutation("POST", "./api/vocab/batch", { action: "mark_mastered", ids });
}

async function handleVocabBatchTag() {
  const ids = Array.from(state.selectedVocabIds);
  if (ids.length === 0) return;
  const tag = window.prompt("请输入要批量添加的标签名称：");
  if (!tag || !tag.trim()) return;
  const cleanTag = tag.trim();

  ids.forEach((id) => {
    const entry = state.vocab.find((v) => v.id === id);
    if (entry) {
      if (!Array.isArray(entry.tags)) entry.tags = [];
      if (!entry.tags.includes(cleanTag)) entry.tags.push(cleanTag);
    }
  });
  persistVocabList();
  state.selectedVocabIds.clear();
  renderVocabList();
  await syncLearningMutation("POST", "./api/vocab/batch", { action: "add_tag", ids, tag: cleanTag });
}

async function handleVocabBatchReset() {
  const ids = Array.from(state.selectedVocabIds);
  if (ids.length === 0) return;
  ids.forEach((id) => {
    const entry = state.vocab.find((v) => v.id === id);
    if (entry) {
      entry.mastered = false;
      entry.srsStage = 0;
      entry.srsInterval = 0;
      entry.srsRepetitions = 0;
      entry.nextReviewAt = "";
    }
  });
  persistVocabList();
  state.selectedVocabIds.clear();
  renderVocabList();
  await syncLearningMutation("POST", "./api/vocab/batch", { action: "reset_srs", ids });
}

async function handleVocabBatchDelete() {
  const ids = Array.from(state.selectedVocabIds);
  if (ids.length === 0) return;
  if (!window.confirm(`确定要删除选中的 ${ids.length} 个生词吗？`)) return;

  state.vocab = state.vocab.filter((v) => !ids.includes(v.id));
  persistVocabList();
  state.selectedVocabIds.clear();
  renderVocabList();
  updateVocabCount();
  ids.forEach((id) => LearningDataSync.markDeleted("vocab", id));
  await syncLearningMutation("POST", "./api/vocab/batch", { action: "delete", ids });
}

// ---- Anki export & batch import ----

function exportVocabAnki() {
  let tsv = "#separator:tab\n#html:true\n#tags column:5\n";
  state.vocab.forEach((v) => {
    const front = v.term;
    const reading = v.reading || "";
    const meaning = v.meaning || "";
    let noteAndContext = v.note || "";
    if (v.sourceText) {
      noteAndContext += noteAndContext ? `<br><small>例句: ${v.sourceText}</small>` : `<small>例句: ${v.sourceText}</small>`;
    }
    const tags = Array.isArray(v.tags) ? v.tags.join(" ") : (v.level || "");
    tsv += `${front}\t${reading}\t${meaning}\t${noteAndContext}\t${tags}\n`;
  });

  const blob = new Blob(["\uFEFF", tsv], { type: "text/tab-separated-values;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `anki-deck-${todayIso()}.txt`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function openVocabImportDialog() {
  if (!elements.vocabImportDialog) return;
  elements.vocabImportTextarea.value = "";
  if (elements.vocabImportFile) elements.vocabImportFile.value = "";
  if (elements.vocabImportFileName) elements.vocabImportFileName.textContent = "";
  hideInlineMessage(elements.vocabImportMessage);
  elements.vocabImportDialog.showModal();
}

function handleVocabImportFileSelected(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  elements.vocabImportFileName.textContent = file.name;
  const reader = new FileReader();
  reader.onload = (evt) => {
    elements.vocabImportTextarea.value = evt.target.result || "";
  };
  reader.readAsText(file);
}

async function handleVocabImportSubmit() {
  const raw = elements.vocabImportTextarea.value.trim();
  if (!raw) {
    showInlineMessage(elements.vocabImportMessage, "请粘贴词条内容或选择文件。", true);
    return;
  }

  const parsed = PersonalDataTools.parseVocabImport(raw);
  if (parsed.items.length === 0) {
    showInlineMessage(elements.vocabImportMessage, "没有识别到有效词条，请检查 CSV/TSV 格式。", true);
    return;
  }

  const known = new Set(state.vocab.map(PersonalDataTools.vocabNaturalKey));
  const timestamp = new Date().toISOString();
  const imported = [];
  let duplicates = 0;
  parsed.items.forEach((item, index) => {
    const naturalKey = PersonalDataTools.vocabNaturalKey(item);
    if (!naturalKey || known.has(naturalKey)) {
      duplicates += 1;
      return;
    }
    known.add(naturalKey);
    imported.push({
      id: `local_import_${Date.now()}_${index}_${Math.random().toString(36).slice(2, 7)}`,
      term: item.term,
      reading: item.reading,
      meaning: item.meaning,
      note: item.note,
      tags: item.tags,
      level: item.level,
      courseId: "",
      sentenceId: "",
      sourceText: "",
      srsStage: 0,
      srsInterval: 0,
      srsEase: 2.5,
      srsRepetitions: 0,
      nextReviewAt: "",
      mastered: false,
      createdAt: timestamp,
      updatedAt: timestamp,
    });
  });

  if (imported.length === 0) {
    showInlineMessage(elements.vocabImportMessage, `没有新增词条；${duplicates} 项已存在。`);
    return;
  }

  state.vocab = [...imported, ...state.vocab];
  persistVocabList();
  renderVocabList();
  updateVocabCount();
  const { result, queued } = await syncLearningMutation(
    "POST",
    "./api/vocab/import",
    { items: imported },
  );
  if (result?.items) {
    state.vocab = PersonalDataTools.dedupeVocabEntries([
      ...result.items,
      ...state.vocab.filter((item) => !imported.some((added) => added.id === item.id)),
    ]);
    persistVocabList();
    renderVocabList();
  }

  elements.vocabImportDialog.close();
  const detail = [
    `新增 ${imported.length} 个`,
    duplicates ? `跳过重复 ${duplicates} 个` : "",
    parsed.errors ? `忽略无效行 ${parsed.errors} 行` : "",
    queued ? "已进入离线同步队列" : "已保存到本地数据库",
  ].filter(Boolean).join("；");
  window.alert(detail);
}

// ---------------------------------------------------------------------------
// 「我的」中心 — the personal section
// ---------------------------------------------------------------------------
//
// 错题集 / 生词本 / 收藏笔记 / 学习分析 used to be four sibling buttons in the
// top bar, each opening its own dialog. They are one section now: a single
// dialog with a tab rail, deep-linkable as `#/me/<tab>` so the JLPT page (and a
// bookmark) can land straight on a module.
//
// The four modules keep their own data sources — 听写 reads /api/mistakes,
// /api/vocab, /api/notes and /api/analytics; 真题 reads /api/exams/<slug>/review.
// Only the surface is merged.

const PERSONAL_TABS = ["mistakes", "vocab", "notes", "analytics"];
const PERSONAL_HASH = /^#\/me(?:\/([a-z]+))?(?:\/([a-z]+))?$/;

let activePersonalTab = "mistakes";
// The route the centre was opened on top of, restored when it closes so that
// reloading from behind the dialog lands where the learner actually was.
let routeBeneathPersonal = "";

function isStandalonePersonalPath() {
  return location.pathname.replace(/\/+$/, "").endsWith("/me");
}

function readPersonalRoute() {
  const match = PERSONAL_HASH.exec(location.hash || "");
  if (!match) {
    return isStandalonePersonalPath()
      ? { tab: "mistakes", subtab: "" }
      : { tab: "", subtab: "" };
  }
  return {
    tab: PERSONAL_TABS.includes(match[1]) ? match[1] : "mistakes",
    subtab: match[2] || "",
  };
}

/** The tab named by the current URL hash, or "" when the hash is not ours. */
function readPersonalHash() {
  return readPersonalRoute().tab;
}

function setPersonalRoutePresentation(active) {
  document.body.classList.toggle("is-personal-route", active);
  const current = document.getElementById("mode-context-current");
  const label = document.getElementById("mode-context-label");
  const mark = document.getElementById("workspace-brand-mark");
  const title = document.getElementById("workspace-brand-title");
  const subtitle = document.getElementById("workspace-brand-subtitle");
  current?.classList.toggle("personal", active);
  current?.classList.toggle("listening", !active);
  if (label) label.textContent = active ? "我的学习中心" : "精听工作区";
  if (mark) mark.textContent = active ? "我" : "听";
  if (title) title.textContent = active ? "我的学习中心" : "精听模式";
  if (subtitle) subtitle.textContent = active ? "跨模式学习资产" : "听辨、理解与跟读";
  document.title = active
    ? "我的学习中心 · 日语学习中心"
    : "精听模式 · 日语学习中心";
}

function openPersonalCenter(tab = activePersonalTab, requestedSubtab = "") {
  const name = PERSONAL_TABS.includes(tab) ? tab : "mistakes";
  const subtab = name === "mistakes" && ["dictation", "exam"].includes(requestedSubtab)
    ? requestedSubtab
    : (name === "analytics" && ["punch", "analytics", "logs"].includes(requestedSubtab) ? requestedSubtab : "");
  if (!elements.personalDialog?.open && !isStandalonePersonalPath()) {
    const fallbackHash = location.hash || "#/listening";
    routeBeneathPersonal = `${location.pathname}${location.search}${fallbackHash}`;
  }
  activePersonalTab = name;
  setPersonalRoutePresentation(true);

  elements.personalTabs.forEach((button) => {
    const isActive = button.dataset.personalTab === name;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
    button.tabIndex = isActive ? 0 : -1;
  });
  elements.personalPanels.forEach((panel) => {
    panel.hidden = panel.dataset.personalPanel !== name;
  });

  if (elements.personalDialog && !elements.personalDialog.open) {
    elements.personalDialog.showModal();
  }
  const scroller = document.querySelector(".personal-panels");
  if (scroller) scroller.scrollTop = 0;

  const wantedHash = `#/me/${name}${subtab ? `/${subtab}` : ""}`;
  if (!isStandalonePersonalPath() || location.hash !== wantedHash) {
    history.replaceState(null, "", `./me${wantedHash}`);
  }

  return refreshPersonalTab(name, subtab);
}

function closePersonalCenter() {
  elements.personalDialog?.close();
}

/** Load whatever the freshly-shown module needs. Each one owns its own fetch. */
async function refreshPersonalTab(name, subtab = "") {
  setPersonalLoadStatus("正在加载…");
  try {
    if (name === "mistakes") {
      if (subtab) setMistakesScope(subtab);
      await loadMistakes();
    } else if (name === "vocab") {
      closeVocabAddForm();
      renderVocabList();
    } else if (name === "notes") {
      closeNoteAddForm();
      if (!state.manifest) setNotesScope("all");
      if (elements.notesScopeCurrent) elements.notesScopeCurrent.disabled = !state.manifest;
      if (elements.noteAddButton) elements.noteAddButton.disabled = !state.manifest;
      await renderNotesList();
    } else if (name === "analytics") {
      const scope = document.getElementById("analytics-scope");
      const currentOption = scope?.querySelector('option[value="current"]');
      if (currentOption) currentOption.disabled = !state.manifest;
      if (scope && !state.manifest) scope.value = "all";
      await AnalyticsManager.open(subtab || "punch");
    }
    if (activePersonalTab === name) setPersonalLoadStatus("");
  } catch (error) {
    console.warn(`Failed to refresh personal tab ${name}`, error);
    if (activePersonalTab === name) setPersonalLoadStatus("加载失败，现有本地数据仍可使用。", true);
  }
  updatePersonalBadges();
}

function setPersonalLoadStatus(message, isError = false) {
  if (!elements.personalStatus || !elements.personalStatusText) return;
  elements.personalStatus.hidden = !message;
  elements.personalStatus.classList.toggle("is-error", isError);
  elements.personalStatusText.textContent = message;
  if (elements.personalRetryButton) elements.personalRetryButton.hidden = !isError;
}

/** Counts on the tab rail, and the "needs attention" dot on the section nav. */
function updatePersonalBadges() {
  const dueVocab = state.vocab.filter(isDueForReview).length;
  const mistakes = state.dictationMistakes.length + state.examMistakes.length;
  const notes = state.allNotes.length || Object.values(state.notesByCourse).length;

  setBadge(elements.mistakesTotalBadge, mistakes);
  setBadge(elements.vocabTotalBadge, state.vocab.length);
  setBadge(elements.notesTotalBadge, notes);

  // The nav badge is a call to action, not an inventory: only what is due today
  // plus outstanding mistakes earns the red dot. The badge itself is aria-hidden,
  // so the count reaches a screen reader through the button's label instead.
  const pending = dueVocab + mistakes;
  setBadge(elements.personalNavBadge, pending);
  elements.personalNavButton?.setAttribute(
    "aria-label",
    pending > 0 ? `我的（${pending} 项待处理）` : "我的",
  );
}

function setBadge(node, count) {
  if (!node) return;
  node.textContent = String(count);
  node.hidden = count <= 0;
}

// ---------------------------------------------------------------------------
// Dictation & Exam Mistakes Hub
// ---------------------------------------------------------------------------

async function loadDictationMistakes() {
  state.dictationMistakes = [];
  if (state.backendAvailable) {
    try {
      const courseId = state.manifest ? stableCourseId(state.manifest) : "";
      const res = await apiFetch(`./api/mistakes?courseId=${encodeURIComponent(courseId)}`);
      if (res.ok) {
        const data = await res.json();
        state.dictationMistakes = data.items || [];
      }
    } catch (e) {
      console.warn("Mistakes fetch failed", e);
    }
  }

  if (state.dictationMistakes.length === 0 && state.manifest) {
    // Fallback: extract mistakes from local progress
    allCoursePracticeIndexes().forEach((idx) => {
      const pKey = sentenceProgressKey(idx);
      const prog = state.progress[pKey];
      if (prog && prog.attempts > 0 && !prog.correct) {
        const sObj = state.manifest.sentences[idx];
        state.dictationMistakes.push({
          courseId: stableCourseId(state.manifest),
          sentenceId: pKey,
          attempts: prog.attempts,
          lastScore: prog.bestScore || 0,
          mastered: false,
          sourceText: sourceText(sObj),
          lastUserInput: "",
        });
      }
    });
  }
}

/** Both sources, then render. Used when the 错题集 panel is actually opened. */
async function loadMistakes() {
  await loadDictationMistakes();
  await loadExamMistakes();
  renderMistakesList();
}

/* JLPT wrong answers.
 *
 * The exam side keeps per-question review state rather than a mistake list, so a
 * "mistake" here is a question whose last result was wrong, skipped or guessed —
 * the same rule 错题复习 uses inside the exam page, so the two counts agree.
 *
 * One aggregate request reads the shared SQLite review-state table. This avoids
 * a 1+N request fan-out as the installed paper library grows.
 */
async function loadExamMistakes() {
  state.examMistakes = [];
  if (!state.backendAvailable) return;

  try {
    const response = await apiFetch("./api/exams/review-summary");
    if (!response.ok) return;
    const exams = (await response.json()).exams || [];
    state.examMistakes = exams.flatMap((exam) => (exam.questions || []).map((record) => ({
      questionId: record.questionId,
      examSlug: exam.examSlug,
      examTitle: exam.examTitle || exam.examSlug,
      examLevel: exam.examLevel || "",
      wrong: record.wrong || 0,
      seen: record.seen || 0,
      due: Boolean(record.due),
      marked: Boolean(record.marked),
      lastResult: record.lastResult,
      lastAt: record.lastAt || "",
    })));
  } catch (error) {
    console.warn("Exam review summary fetch failed", error);
    return;
  }

  // Due first, then the ones missed most often — the order you would work through.
  state.examMistakes.sort((a, b) => {
    if (a.due !== b.due) return a.due ? -1 : 1;
    return (b.wrong || 0) - (a.wrong || 0);
  });
}

function setMistakesScope(scope) {
  state.mistakesScope = scope;
  if (elements.mistakesTabDictation) elements.mistakesTabDictation.classList.toggle("active", scope === "dictation");
  if (elements.mistakesTabExam) elements.mistakesTabExam.classList.toggle("active", scope === "exam");
  if (activePersonalTab === "mistakes" && elements.personalDialog?.open) {
    history.replaceState(null, "", `#/me/mistakes/${scope}`);
  }
  renderMistakesList();
}

function renderMistakesList() {
  const isDictation = state.mistakesScope === "dictation";
  const list = isDictation ? state.dictationMistakes : state.examMistakes;

  if (elements.mistakesDictationBadge) elements.mistakesDictationBadge.textContent = String(state.dictationMistakes.length);
  if (elements.mistakesExamBadge) elements.mistakesExamBadge.textContent = String(state.examMistakes.length);
  updatePersonalBadges();

  if (elements.mistakesSummaryText) {
    if (list.length === 0) {
      elements.mistakesSummaryText.textContent = isDictation
        ? "所有练习均已满分掌握！"
        : "真题还没有错题记录。";
    } else if (isDictation) {
      elements.mistakesSummaryText.textContent = `检测到 ${list.length} 个弱项句子需要巩固。`;
    } else {
      const due = state.examMistakes.filter((item) => item.due).length;
      elements.mistakesSummaryText.textContent = due > 0
        ? `${list.length} 道真题错题，其中 ${due} 道今天该复习。`
        : `${list.length} 道真题错题。`;
    }
  }

  if (elements.mistakesPracticeAllButton) {
    elements.mistakesPracticeAllButton.hidden = list.length === 0 || !isDictation;
  }

  elements.mistakesList.replaceChildren();
  elements.mistakesEmptyHint.hidden = list.length > 0;

  if (!isDictation) {
    renderExamMistakeRows(list);
    return;
  }

  list.forEach((item) => {
    const row = document.createElement("div");
    row.className = "entry-row";

    const head = document.createElement("div");
    head.className = "entry-row-head";

    const sentenceIndex = sentenceIndexForProgressKey(item.sentenceId);
    const term = document.createElement("span");
    term.className = "entry-term";
    term.textContent = sentenceIndex !== -1 ? `第 ${practicePositionLabel(sentenceIndex)} 题` : `句子 ${item.sentenceId}`;
    head.appendChild(term);

    const attemptsBadge = document.createElement("span");
    attemptsBadge.className = "tag-chip";
    attemptsBadge.textContent = `练习 ${item.attempts || 1} 次`;
    head.appendChild(attemptsBadge);

    const scoreBadge = document.createElement("span");
    scoreBadge.className = "level-badge";
    scoreBadge.textContent = `得分: ${Math.round(item.lastScore || 0)}分`;
    head.appendChild(scoreBadge);

    row.appendChild(head);

    // Sentence Expected text
    const sText = (sentenceIndex !== -1 && state.manifest?.sentences?.[sentenceIndex])
      ? sourceText(state.manifest.sentences[sentenceIndex])
      : (item.sourceText || "");

    const diffBox = document.createElement("div");
    diffBox.className = "mistake-diff-box";

    if (item.lastUserInput) {
      const wrongLine = document.createElement("div");
      wrongLine.className = "mistake-wrong-line";
      wrongLine.textContent = `✕ 你的作答：${item.lastUserInput}`;
      diffBox.appendChild(wrongLine);
    }

    const expectedLine = document.createElement("div");
    expectedLine.className = "mistake-expected-line";
    expectedLine.textContent = `✓ 正确原文：${sText}`;
    diffBox.appendChild(expectedLine);
    row.appendChild(diffBox);

    const actions = document.createElement("div");
    actions.className = "entry-actions";

    if (sentenceIndex !== -1) {
      const practiceBtn = document.createElement("button");
      practiceBtn.className = "primary-button";
      practiceBtn.type = "button";
      practiceBtn.textContent = "立即重练";
      practiceBtn.addEventListener("click", () => {
        goToPractice(sentenceIndex);
      });
      actions.appendChild(practiceBtn);

      const playAudioBtn = document.createElement("button");
      playAudioBtn.className = "quiet-button";
      playAudioBtn.type = "button";
      playAudioBtn.textContent = "▶ 听原音";
      playAudioBtn.addEventListener("click", () => {
        const sObj = state.manifest.sentences[sentenceIndex];
        if (sObj) {
          media.seek(Number(sObj.startTime));
          media.play();
        }
      });
      actions.appendChild(playAudioBtn);
    }

    row.appendChild(actions);
    elements.mistakesList.appendChild(row);
  });
}

/* Rows for the 真题 tab.
 *
 * The question text lives in the exam JSON, which is far too large to pull in
 * just to label a list, so a row carries what /review already knows — which
 * paper, which question, how often it was missed — and hands off to the JLPT
 * page, which has the paper loaded and can drill the wrong-answer set properly.
 */
function renderExamMistakeRows(list) {
  const grouped = new Map();
  list.forEach((item) => {
    if (!grouped.has(item.examSlug)) grouped.set(item.examSlug, []);
    grouped.get(item.examSlug).push(item);
  });

  grouped.forEach((items, slug) => {
    const first = items[0];
    const row = document.createElement("div");
    row.className = "entry-row exam-mistake-row";

    const head = document.createElement("div");
    head.className = "entry-row-head";

    const term = document.createElement("span");
    term.className = "entry-term";
    const chip = document.createElement("span");
    chip.className = "source-chip";
    chip.textContent = first.examLevel ? `JLPT ${first.examLevel}` : "JLPT";
    term.append(chip, document.createTextNode(first.examTitle));
    head.appendChild(term);

    const countBadge = document.createElement("span");
    countBadge.className = "tag-chip";
    countBadge.textContent = `${items.length} 道错题`;
    head.appendChild(countBadge);

    const dueCount = items.filter((item) => item.due).length;
    if (dueCount > 0) {
      const dueBadge = document.createElement("span");
      dueBadge.className = "level-badge";
      dueBadge.textContent = `今天该复习 ${dueCount}`;
      head.appendChild(dueBadge);
    }

    row.appendChild(head);

    const detail = document.createElement("div");
    detail.className = "mistake-diff-box";
    const worst = items.slice().sort((a, b) => (b.wrong || 0) - (a.wrong || 0)).slice(0, 4);
    const line = document.createElement("div");
    line.className = "mistake-expected-line";
    line.textContent = `错得最多：${worst.map((item) => `第 ${item.questionId} 题（${item.wrong || 1} 次）`).join("、")}`;
    detail.appendChild(line);
    row.appendChild(detail);

    const actions = document.createElement("div");
    actions.className = "entry-actions";
    const go = document.createElement("a");
    go.className = "primary-button";
    go.href = `./exams#/exam/${encodeURIComponent(slug)}?mode=review&scope=wrong`;
    go.textContent = "去真题错题复习";
    actions.appendChild(go);
    row.appendChild(actions);

    elements.mistakesList.appendChild(row);
  });
}

function startMistakesPracticeQueue() {
  if (state.dictationMistakes.length === 0) return;
  const mistakeIndexes = state.dictationMistakes
    .map((m) => sentenceIndexForProgressKey(m.sentenceId))
    .filter((idx) => idx !== -1);

  if (mistakeIndexes.length === 0) return;
  state.practiceIndexes = mistakeIndexes;
  state.activeQueueKind = "mistakes";
  if (elements.exitSpecialPracticeButton) elements.exitSpecialPracticeButton.hidden = false;
  configureCourse();
  goToPractice(state.practiceIndexes[0]);
}

function restoreCoursePracticeQueue() {
  if (state.activeQueueKind === "course") return;
  const previousIndex = state.index;
  state.practiceIndexes = [...allCoursePracticeIndexes()];
  state.activeQueueKind = "course";
  if (elements.exitSpecialPracticeButton) elements.exitSpecialPracticeButton.hidden = true;
  configureCourse();
  const nextIndex = state.practiceIndexes.includes(previousIndex)
    ? previousIndex
    : state.practiceIndexes[0];
  if (Number.isInteger(nextIndex)) selectSentence(nextIndex, { autoplay: false });
}

// ---------------------------------------------------------------------------
// Flashcard SRS Spaced Repetition Session
// ---------------------------------------------------------------------------

function shuffleArray(list) {
  const copy = [...list];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function startFlashcardSession(mode = "auto") {
  closePersonalCenter();
  let candidateVocabs = state.vocab;

  if (mode === "auto") {
    const dueList = state.vocab.filter(isDueForReview);
    candidateVocabs = dueList.length > 0 ? dueList : state.vocab.filter((v) => !v.mastered);
    if (candidateVocabs.length === 0) candidateVocabs = state.vocab;
  }

  if (candidateVocabs.length === 0) {
    elements.flashcard.hidden = true;
    elements.flashcardFlipRow.hidden = true;
    elements.flashcardGradeActions.hidden = true;
    elements.flashcardDone.hidden = true;
    elements.flashcardEmptyHint.hidden = false;
    elements.flashcardProgress.textContent = "";
    elements.flashcardDialog.showModal();
    return;
  }

  flashcardState.queue = shuffleArray(candidateVocabs.map((entry) => entry.id));
  flashcardState.totalThisRound = flashcardState.queue.length;
  flashcardState.roundResults = { again: 0, hard: 0, good: 0, easy: 0 };
  elements.flashcardEmptyHint.hidden = true;
  elements.flashcardDone.hidden = true;
  elements.flashcardDialog.showModal();
  showNextFlashcard();
}

function showNextFlashcard() {
  if (flashcardState.queue.length === 0) {
    flashcardState.current = null;
    elements.flashcard.hidden = true;
    elements.flashcardFlipRow.hidden = true;
    elements.flashcardGradeActions.hidden = true;
    elements.flashcardDone.hidden = false;
    elements.flashcardProgress.textContent = "复习完成";
    if (elements.flashcardDoneStats && flashcardState.roundResults) {
      const res = flashcardState.roundResults;
      elements.flashcardDoneStats.textContent = `本轮掌握：良好 ${res.good || 0} / 简单 ${res.easy || 0}，待强化：${res.again || 0} 词。`;
    }
    return;
  }
  const id = flashcardState.queue[0];
  const entry = state.vocab.find((item) => item.id === id);
  if (!entry) {
    flashcardState.queue.shift();
    showNextFlashcard();
    return;
  }
  flashcardState.current = entry;
  flashcardState.flipped = false;
  elements.flashcard.hidden = false;
  elements.flashcardFlipRow.hidden = false;
  elements.flashcardGradeActions.hidden = true;
  elements.flashcardBack.hidden = true;

  if (elements.flashcardLevelChip) {
    elements.flashcardLevelChip.textContent = entry.level || "";
    elements.flashcardLevelChip.hidden = !entry.level;
  }

  elements.flashcardTerm.textContent = entry.term;
  elements.flashcardReading.textContent = entry.reading || "";
  elements.flashcardMeaning.textContent = entry.meaning || "（暂无释义）";
  elements.flashcardNote.textContent = entry.note || "";

  if (entry.sourceText && elements.flashcardSourceBox) {
    elements.flashcardSourceBox.hidden = false;
    elements.flashcardSource.textContent = entry.sourceText;
    const sentenceIndex = sentenceIndexForProgressKey(entry.sentenceId);
    if (elements.flashcardSourcePlayButton) {
      elements.flashcardSourcePlayButton.hidden = sentenceIndex === -1;
    }
  } else if (elements.flashcardSourceBox) {
    elements.flashcardSourceBox.hidden = true;
  }

  // Pre-calculate SM-2 predicted intervals for the buttons
  const reps = entry.srsRepetitions || 0;
  const interval = entry.srsInterval || 0;
  const ease = entry.srsEase || 2.5;

  const goodPrediction = calculateSm2Client(reps, interval, ease, "good");
  const easyPrediction = calculateSm2Client(reps, interval, ease, "easy");

  if (elements.srsGoodIntervalPreview) {
    elements.srsGoodIntervalPreview.textContent = `${goodPrediction.interval}天后 (键 3)`;
  }
  if (elements.srsEasyIntervalPreview) {
    elements.srsEasyIntervalPreview.textContent = `${easyPrediction.interval}天后 (键 4)`;
  }

  const remaining = flashcardState.queue.length;
  const seen = flashcardState.totalThisRound - remaining + 1;
  elements.flashcardProgress.textContent = `第 ${seen}／共 ${flashcardState.totalThisRound} 张`;

  // Auto pronunciation when new card appears
  speakText(entry.term);
}

function flipFlashcard() {
  if (!flashcardState.current || flashcardState.flipped) return;
  flashcardState.flipped = true;
  elements.flashcardBack.hidden = false;
  elements.flashcardFlipRow.hidden = true;
  elements.flashcardGradeActions.hidden = false;
}

function playFlashcardSourceAudio() {
  if (!flashcardState.current) return;
  const sentenceIndex = sentenceIndexForProgressKey(flashcardState.current.sentenceId);
  if (sentenceIndex !== -1 && state.manifest?.sentences?.[sentenceIndex]) {
    const sObj = state.manifest.sentences[sentenceIndex];
    media.seek(Number(sObj.startTime));
    media.play();
  }
}

async function gradeFlashcardSrs(grade) {
  if (!flashcardState.current) return;
  const entry = flashcardState.current;
  flashcardState.queue.shift();

  if (flashcardState.roundResults) {
    flashcardState.roundResults[grade] = (flashcardState.roundResults[grade] || 0) + 1;
  }

  const reps = entry.srsRepetitions || 0;
  const interval = entry.srsInterval || 0;
  const ease = entry.srsEase || 2.5;

  const srsUpdate = calculateSm2Client(reps, interval, ease, grade);
  const patch = {
    srsRepetitions: srsUpdate.repetitions,
    srsInterval: srsUpdate.interval,
    srsEase: srsUpdate.ease,
    srsStage: srsUpdate.stage,
    nextReviewAt: srsUpdate.nextReviewAt,
    mastered: srsUpdate.stage === 3,
  };

  if (grade === "again") {
    // Put back into queue for same-session reinforcement
    flashcardState.queue.push(entry.id);
  }

  const index = state.vocab.findIndex((item) => item.id === entry.id);
  if (index !== -1) {
    state.vocab[index] = {
      ...state.vocab[index],
      ...patch,
      updatedAt: new Date().toISOString(),
    };
    persistVocabList();
  }

  // One authoritative server mutation. The operation id is persisted with the
  // outbox and deduplicated by the backend, so a lost response cannot grade the
  // same card twice. The client calculation above keeps offline review instant.
  const { result } = await syncLearningMutation(
    "POST",
    "./api/vocab/review",
    { id: entry.id, grade },
    { entityType: "vocab", entityKey: entry.id, clearTombstone: false },
  );
  if (result?.item && index !== -1) {
    state.vocab[index] = result.item;
    persistVocabList();
  }

  showNextFlashcard();
}

// ---------------------------------------------------------------------------
// Study Streak & Activity
// ---------------------------------------------------------------------------

function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function todayIso() {
  return formatLocalDate(new Date());
}

function dateDaysAgoIso(daysAgo) {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() - Math.max(0, Number(daysAgo || 0)));
  return formatLocalDate(date);
}

async function recordActivity() {
  const day = todayIso();
  if (!state.activityDays.includes(day)) {
    state.activityDays.push(day);
    state.activityDays.sort();
    saveStoredValue(ACTIVITY_STORAGE_KEY, state.activityDays);
    updateStreakUi();
  }
  await syncLearningMutation("POST", "./api/activity", { day }, {
    entityType: "activity",
    entityKey: day,
  });
}

function computeStreak(days) {
  const daySet = new Set(days);
  let streak = 0;
  const cursor = new Date();
  while (daySet.has(formatLocalDate(cursor))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

function updateStreakUi() {
  const streak = computeStreak(state.activityDays || []);
  if (elements.streakCount) elements.streakCount.textContent = String(streak);
  if (elements.streakChip) elements.streakChip.hidden = false;
  const punchDot = document.getElementById("punch-today-dot");
  if (punchDot) {
    const isPunched = (state.activityDays || []).includes(todayIso());
    punchDot.classList.toggle("is-pending", !isPunched);
    punchDot.title = isPunched ? "今日已打卡" : "今日待打卡";
  }
}

// ---------------------------------------------------------------------------
// CSV & Export Helpers
// ---------------------------------------------------------------------------

function csvEscape(value) {
  let text = String(value ?? "");
  if (/^[=+\-@\t]/.test(text)) {
    text = `'${text}`;
  }
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function downloadCsv(filename, rows) {
  const csvBody = rows.map((row) => row.map(csvEscape).join(",")).join("\r\n");
  const blob = new Blob(["\uFEFF", csvBody, "\r\n"], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function exportVocabCsv() {
  const header = ["term", "reading", "meaning", "note", "level", "tags", "srsStage", "srsInterval", "nextReviewAt", "sourceText", "mastered", "createdAt"];
  const rows = [header, ...state.vocab.map((entry) => [
    entry.term,
    entry.reading || "",
    entry.meaning || "",
    entry.note || "",
    entry.level || "",
    Array.isArray(entry.tags) ? entry.tags.join(";") : "",
    entry.srsStage || 0,
    entry.srsInterval || 0,
    entry.nextReviewAt || "",
    entry.sourceText || "",
    entry.mastered ? "yes" : "no",
    entry.createdAt || "",
  ])];
  downloadCsv(`vocab-${todayIso()}.csv`, rows);
}

function exportNotesCsv() {
  const header = ["courseId", "position", "tag", "sourceText", "note", "starred", "updatedAt"];
  const isAll = state.notesScope === "all";
  const entries = isAll ? state.allNotes : Object.values(state.notesByCourse);
  const rows = [header, ...entries.map((note) => {
    const isCurrent = !note.courseId || note.courseId === stableCourseId(state.manifest);
    const sentenceIndex = isCurrent ? sentenceIndexForProgressKey(note.sentenceId) : -1;
    return [
      note.courseId || "本课程",
      isCurrent ? practicePositionLabel(sentenceIndex) : note.sentenceId,
      note.tag || "",
      (isCurrent && sentenceIndex !== -1) ? sourceText(state.manifest.sentences[sentenceIndex]) : (note.sourceText || ""),
      note.text || "",
      note.starred ? "yes" : "no",
      note.updatedAt || "",
    ];
  })];
  downloadCsv(`notes-${todayIso()}.csv`, rows);
}

function formatTime(value) {
  const seconds = Math.max(0, Math.round(Number(value) || 0));
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function showFatalError(error) {
  elements.layout.hidden = true;
  elements.fatalErrorCopy.textContent = error instanceof Error ? error.message : String(error);
  elements.fatalError.hidden = false;
}

bootstrap().catch(showFatalError);
