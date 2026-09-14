"""Turn caption cues back into sentences.

A subtitle cue is a *display line*: the site broke it where its renderer ran out
of width, which has nothing to do with where the speaker finished a thought.
Importing cues as sentences produces a course whose every other item is half a
clause — measured on this project's own video courses, 66.8% of "sentences" had
no terminal punctuation and 36% were exactly 18–19 characters long, which is a
rendering width, not a property of Japanese.

So this module throws the cue boundaries away and finds real ones:

    cues ──► CharStream (every character carries a time) ──► cuts ──► sentences

Four rules, in priority order, each earning its place from measured data:

A. **Terminal punctuation.** Japanese auto-captions *do* carry 。！？ — they just
   put them in the middle of a display line. Across the 12 existing courses there
   were 719 of them for 1207 display lines, 4–9 per minute, which is a plausible
   sentence rate for news speech. This is the main source of boundaries.
B. **Pauses.** Needs per-token times (see :class:`media_sources.Token`). One real
   track carried 1509 characters and zero terminal punctuation; without a pause
   rule that course collapses into a single sentence.
C. **Length cap with a secondary boundary.** Splitting on punctuation alone left
   p90 lengths of 60–105 characters and a maximum of 209. A 60-character
   dictation item is not practice, so long runs get split again at the best
   secondary boundary available.
D. **Short-fragment merge.** 12.8% of existing items were ≤4 characters, including
   47 that were a bare on-screen digit. Those are merged into a neighbour when
   they are adjacent in time, and marked non-practisable when they are not.

The module is deliberately free of any notion of a video site: it knows only
characters and times, so it is testable with no network and no yt-dlp. The
invariants in :func:`verify_invariants` are what make it safe to iterate on —
above all I1, character conservation, which keeps "re-segmenting" and "editing
the text" strictly separate operations.

See ``docs/VIDEO_COURSE_PIPELINE.md`` for the full specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from language_support import language_profile, normalize_language_code, set_source_text

STRATEGY = "sentence-boundary/v1"

# Resolution labels, most to least capable. Recorded in the manifest so a course
# says what it was built from instead of leaving it to be guessed later.
RESOLUTION_TOKEN = "token"
RESOLUTION_CUE = "cue-interpolated"
RESOLUTION_NONE = "none"

TERMINALS = "。！？!?"
CLOSERS = "」』）)]】〉》”’\"'"
SECONDARY_PUNCT = "、，,；;：:"

# Japanese clause-continuation forms, longest first within each tier. Only ever
# consulted for a run that is already over the length cap and has neither a comma
# nor a pause to cut at — cutting after a bare "て" is a poor boundary, but it is
# a much better one than slicing at character 45 regardless of what is there.
_CONTINUATIONS_LONG = ("けれども", "けれど", "ながら", "ものの", "けど", "ので", "から", "たら", "なら", "つつ", "ては", "でも", "とか")
_CONTINUATIONS_SHORT = ("て", "で", "が", "し", "ば", "り")
_CONJUNCTIONS = ("そして", "しかし", "ところが", "そのため", "それから", "さらに", "また", "一方", "ただ", "なお", "つまり")

_LANGUAGE_RULES: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
    "ja": (_CONTINUATIONS_LONG, _CONTINUATIONS_SHORT, _CONJUNCTIONS),
}


class SegmentationError(ValueError):
    """An invariant was violated — a bug here, never bad input."""


@dataclass(frozen=True)
class SegmentationParams:
    """Tuning knobs. Recorded in the manifest so two courses are never silently
    the product of different rules."""

    max_chars: int = 45
    target_chars: int = 24
    min_chars: int = 8
    pause_hard: float = 0.60
    pause_soft: float = 0.35
    tail_pad: float = 0.15
    min_duration: float = 0.35

    def to_manifest(self) -> dict[str, Any]:
        return {
            "maxChars": self.max_chars,
            "targetChars": self.target_chars,
            "minChars": self.min_chars,
            "pauseHard": self.pause_hard,
            "pauseSoft": self.pause_soft,
            "tailPad": self.tail_pad,
            "minDuration": self.min_duration,
        }


DEFAULT_PARAMS = SegmentationParams()


@dataclass(frozen=True)
class CharStream:
    """Every character of the transcript with the time it was spoken.

    ``slack[i]`` is the estimated *silence* immediately before character ``i``:
    the wall-clock gap between two tokens minus the time the earlier token would
    take to say at this speaker's average rate. Measuring silence rather than the
    raw inter-token gap matters, because a long word followed immediately by the
    next one has a large gap and no pause at all.
    """

    text: str
    times: tuple[float, ...]
    slack: tuple[float, ...]
    resolution: str
    end: float
    cue_starts: frozenset[int] = frozenset()

    def __len__(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class Sentence:
    start: float
    end: float
    text: str
    practice_eligible: bool
    content_type: str


@dataclass(frozen=True)
class SegmentationResult:
    sentences: tuple[Sentence, ...]
    resolution: str
    forced_cuts: int
    source_cues: int
    params: SegmentationParams

    def to_manifest(self) -> dict[str, Any]:
        return {
            "strategy": STRATEGY,
            "timeResolution": self.resolution,
            "sourceCues": self.source_cues,
            "sentences": len(self.sentences),
            "forcedCuts": self.forced_cuts,
            "params": self.params.to_manifest(),
        }


# --------------------------------------------------------------------------
# Stage 5: the character stream
# --------------------------------------------------------------------------


def build_char_stream(segments: Sequence[Any], *, language: str = "ja") -> CharStream:
    """Flatten cues into one timed character sequence.

    Cues contribute no characters between them: for Japanese ``normalize_cue_text``
    has already removed every space, and inventing a separator here would break
    character conservation against the text the learner is graded on.
    """
    code = normalize_language_code(language)
    usable = [s for s in segments if str(getattr(s, "text", "") or "")]
    if not usable:
        return CharStream(
            text="", times=(), slack=(), resolution=RESOLUTION_NONE, end=0.0, cue_starts=frozenset()
        )

    total_chars = sum(len(s.text) for s in usable)
    span = max(float(s.end) for s in usable) - min(float(s.start) for s in usable)
    # Seconds per character for this speaker. Used only to tell silence from the
    # time a word itself occupies; a floor keeps a degenerate track from making
    # every gap look like a pause.
    rate = max(span / total_chars, 0.01) if total_chars and span > 0 else 0.08

    text_parts: list[str] = []
    times: list[float] = []
    slack: list[float] = []
    token_chars = 0
    cue_starts: list[int] = []
    previous_end_time: float | None = None   # when the previous character stopped
    previous_cue_end: float | None = None

    for segment in usable:
        cue_starts.append(len(text_parts))
        tokens = _usable_tokens(segment)
        if tokens:
            token_chars += len(segment.text)
            for token in tokens:
                start = float(token.start)
                gap = 0.0 if previous_end_time is None else start - previous_end_time
                for index, char in enumerate(token.text):
                    text_parts.append(char)
                    times.append(start)
                    slack.append(max(gap, 0.0) if index == 0 else 0.0)
                previous_end_time = start + len(token.text) * rate
        else:
            start = float(segment.start)
            end = float(segment.end)
            width = max(end - start, 0.0)
            length = len(segment.text)
            # Without token times the only honest gap is the one between cues, and
            # auto-caption cues abut exactly, so this is almost always zero. Rule B
            # is disabled for such a stream rather than fed a fabricated signal.
            gap = 0.0 if previous_cue_end is None else start - previous_cue_end
            for index, char in enumerate(segment.text):
                text_parts.append(char)
                times.append(start + width * index / length if length else start)
                slack.append(max(gap, 0.0) if index == 0 else 0.0)
            previous_end_time = end
        previous_cue_end = float(segment.end)

    text = "".join(text_parts)
    resolution = RESOLUTION_TOKEN if token_chars * 2 >= len(text) and token_chars else RESOLUTION_CUE
    return CharStream(
        text=text,
        times=_non_decreasing(times),
        slack=tuple(slack),
        resolution=resolution,
        end=max(float(s.end) for s in usable),
        cue_starts=frozenset(index for index in cue_starts if 0 < index < len(text)),
    )


def _usable_tokens(segment: Any) -> tuple[Any, ...]:
    """Tokens that still reproduce the cue text exactly, or nothing.

    ``media_sources`` maintains this as an invariant, but a caller can build a
    ``Segment`` by hand. Re-checking here costs one string join and removes the
    only way this module could silently mis-time a cut.
    """
    tokens = tuple(getattr(segment, "tokens", ()) or ())
    if not tokens:
        return ()
    if "".join(str(token.text) for token in tokens) != segment.text:
        return ()
    return tokens


def _non_decreasing(values: Iterable[float]) -> tuple[float, ...]:
    out: list[float] = []
    for value in values:
        out.append(value if not out else max(value, out[-1]))
    return tuple(out)


# --------------------------------------------------------------------------
# Stage 6: the cuts
# --------------------------------------------------------------------------


def resegment(
    segments: Sequence[Any],
    *,
    language: str = "ja",
    params: SegmentationParams = DEFAULT_PARAMS,
) -> SegmentationResult:
    """Re-derive sentences from cues. Pure: same input, same output, always."""
    stream = build_char_stream(segments, language=language)
    if not stream.text:
        return SegmentationResult(
            sentences=(), resolution=RESOLUTION_NONE, forced_cuts=0,
            source_cues=len(segments), params=params,
        )

    code = normalize_language_code(language)
    terminal = _terminal_boundaries(stream.text)
    if stream.resolution == RESOLUTION_TOKEN:
        terminal |= _pause_boundaries(stream.slack, params.pause_hard)
    elif not terminal and not cues_look_width_capped(segments):
        # Last resort. Cue boundaries are display lines and normally say nothing
        # about sentences — but a track with no punctuation, no token times, and
        # no width fingerprint has left us nothing else, and gluing several
        # utterances into one item is worse than trusting where the source broke
        # the line. Width-capped cues are excluded precisely because for them the
        # break really is arbitrary.
        terminal |= set(stream.cue_starts)
    boundaries = {0, len(stream)} | terminal

    spans = _to_spans(sorted(boundaries), len(stream))
    forced = 0
    split: list[tuple[int, int]] = []
    for low, high in spans:
        pieces, hard = _split_long(stream, low, high, params, code)
        split.extend(pieces)
        forced += hard

    merged = _merge_short(split, stream, params, terminal)
    sentences = _build_sentences(merged, stream, params)
    result = SegmentationResult(
        sentences=sentences,
        resolution=stream.resolution,
        forced_cuts=forced,
        source_cues=len(segments),
        params=params,
    )
    verify_invariants(result, stream)
    return result


def cues_look_width_capped(segments: Sequence[Any]) -> bool:
    """True when the source cues carry a renderer's line width, not a meaning.

    Same fingerprint the quality gate rejects a course for (see
    ``bundle_quality.check_width_cap``): one length holding a large share of the
    cues with a cliff to the next. Kept as its own function here because this
    module may not import the gate — the gate audits this module's output.
    """
    lengths = [len(s.text) for s in segments if str(getattr(s, "text", "") or "")]
    if len(lengths) < 20:
        return False
    histogram: dict[int, int] = {}
    for length in lengths:
        histogram[length] = histogram.get(length, 0) + 1
    peak_length = max(range(18, 23), key=lambda length: histogram.get(length, 0))
    peak = histogram.get(peak_length, 0)
    if not peak:
        return False
    share = peak / len(lengths)
    cliff = peak / max(histogram.get(peak_length + 1, 0), 1)
    return share > 0.25 or (cliff >= 8.0 and share >= 0.08)


def _terminal_boundaries(text: str) -> set[int]:
    """Rule A. A cut goes *after* the punctuation and after any closing bracket
    or quote riding on it, so 「…です。」 stays one sentence."""
    cuts: set[int] = set()
    for index, char in enumerate(text):
        if char not in TERMINALS:
            continue
        end = index + 1
        while end < len(text) and text[end] in CLOSERS:
            end += 1
        # "!?" and "。。" are one boundary, not two: wait for the last of the run.
        if end < len(text) and text[end] in TERMINALS:
            continue
        if 0 < end < len(text):
            cuts.add(end)
    return cuts


def _pause_boundaries(slack: tuple[float, ...], pause_hard: float) -> set[int]:
    """Rule B. Only meaningful on a token-resolution stream."""
    return {index for index, value in enumerate(slack) if index > 0 and value >= pause_hard}


def _to_spans(boundaries: list[int], length: int) -> list[tuple[int, int]]:
    spans = [(low, high) for low, high in zip(boundaries, boundaries[1:]) if high > low]
    return spans or [(0, length)]


def _split_long(
    stream: CharStream,
    low: int,
    high: int,
    params: SegmentationParams,
    language: str,
) -> tuple[list[tuple[int, int]], int]:
    """Rule C, applied until every piece fits. Returns the pieces and how many of
    the cuts were forced (no real boundary was available)."""
    if high - low <= params.max_chars:
        return [(low, high)], 0
    cut, forced = _secondary_cut(stream, low, high, params, language)
    left, left_forced = _split_long(stream, low, cut, params, language)
    right, right_forced = _split_long(stream, cut, high, params, language)
    return left + right, forced + left_forced + right_forced


def _secondary_cut(
    stream: CharStream,
    low: int,
    high: int,
    params: SegmentationParams,
    language: str,
) -> tuple[int, int]:
    """Best available cut inside an over-long run, plus 1 if it had to be forced."""
    window = range(low + params.min_chars, high - params.min_chars + 1)
    if len(window) <= 0:
        return (low + params.max_chars, 1)

    text = stream.text
    long_forms, short_forms, conjunctions = _LANGUAGE_RULES.get(language, ((), (), ()))
    spaced = language_profile(language).uses_spaces

    tiers: list[list[int]] = [
        # 1 — after a reading comma
        [i for i in window if text[i - 1] in SECONDARY_PUNCT],
        # 2 — at a soft pause, when the stream has the resolution to see one
        [i for i in window if stream.resolution == RESOLUTION_TOKEN and stream.slack[i] >= params.pause_soft]
        if stream.resolution == RESOLUTION_TOKEN
        else [],
        # 3a — after a multi-character clause connective
        [i for i in window if text[:i].endswith(long_forms)] if long_forms else [],
        # 3b — after a single-character one
        [i for i in window if text[:i].endswith(short_forms)] if short_forms else [],
        # 4 — before a sentence-opening conjunction
        [i for i in window if text[i:].startswith(conjunctions)] if conjunctions else [],
        # 4.5 — at a word space, for languages that have them
        [i for i in window if text[i - 1].isspace() or text[i].isspace()] if spaced else [],
    ]

    target = low + params.target_chars
    for candidates in tiers:
        if candidates:
            return (min(candidates, key=lambda i: (abs(i - target), i)), 0)

    # Nothing to cut at. Take the cap, but never leave a fragment behind.
    return (min(low + params.max_chars, high - params.min_chars), 1)


def _merge_short(
    spans: list[tuple[int, int]],
    stream: CharStream,
    params: SegmentationParams,
    terminal: set[int],
) -> list[tuple[int, int]]:
    """Rule D. A fragment joins the neighbour it is adjacent to in time, provided
    the join neither creates an over-long sentence nor crosses a real sentence end.

    The terminal guard is not a refinement, it is the difference between fixing the
    problem and moving it: without it a stray "うん。" merges into what follows and
    the result is a sentence with a full stop in the middle — precisely the defect
    (18.6% of items) this module exists to remove.
    """
    pending = list(spans)
    result: list[tuple[int, int]] = []
    index = 0
    while index < len(pending):
        low, high = pending[index]
        if high - low >= params.min_chars:
            result.append((low, high))
            index += 1
            continue
        if result and low not in terminal:
            previous_low, _ = result[-1]
            if stream.slack[low] < params.pause_hard and high - previous_low <= params.max_chars:
                result[-1] = (previous_low, high)
                index += 1
                continue
        if index + 1 < len(pending):
            next_low, next_high = pending[index + 1]
            if (
                next_low not in terminal
                and stream.slack[next_low] < params.pause_hard
                and next_high - low <= params.max_chars
            ):
                pending[index + 1] = (low, next_high)
                index += 1
                continue
        result.append((low, high))
        index += 1
    return result


def _build_sentences(
    spans: list[tuple[int, int]],
    stream: CharStream,
    params: SegmentationParams,
) -> tuple[Sentence, ...]:
    sentences: list[Sentence] = []
    previous_end: float | None = None
    for position, (low, high) in enumerate(spans):
        start = stream.times[low]
        if previous_end is not None and start < previous_end:
            start = previous_end
        ceiling = stream.times[spans[position + 1][0]] if position + 1 < len(spans) else max(stream.end, stream.times[high - 1])
        end = max(stream.times[high - 1] + params.tail_pad, start + params.min_duration)
        if ceiling > start:
            # I2 outranks I5: a segment may stay under the minimum duration, but it
            # may never run into the next one, or the player's "which sentence am I
            # in" lookup becomes ambiguous.
            end = min(end, ceiling)
        if end <= start:
            end = start + 0.001
        text = stream.text[low:high]
        # A run that survived the merge and is still short is an on-screen number,
        # a back-channel ("うん。"), or a caption artifact. Keep it — deleting it
        # would leave a hole in the timeline — but keep it out of the practice queue.
        is_fragment = high - low < params.min_chars
        sentences.append(
            Sentence(
                start=round(start, 3),
                end=round(end, 3),
                text=text,
                practice_eligible=not is_fragment,
                content_type="marker" if is_fragment else "dialogue",
            )
        )
        previous_end = end
    return tuple(sentences)


# --------------------------------------------------------------------------
# Stage 7: the invariants
# --------------------------------------------------------------------------


def verify_invariants(result: SegmentationResult, stream: CharStream) -> None:
    """Raise if the result is not a faithful re-cut of *stream*.

    I1 is the load-bearing one. As long as concatenating the sentences reproduces
    the stream character for character, re-segmentation provably cannot corrupt
    the text a learner is graded against — which confines every text-eating risk
    in this pipeline to the rolling-window collapse upstream, where it has its own
    dedicated tests.
    """
    rebuilt = "".join(sentence.text for sentence in result.sentences)
    if rebuilt != stream.text:
        raise SegmentationError(
            "I1 violated: re-segmentation changed the transcript "
            f"({len(rebuilt)} chars out, {len(stream.text)} in)."
        )
    previous_end: float | None = None
    for index, sentence in enumerate(result.sentences):
        if sentence.end <= sentence.start:
            raise SegmentationError(f"I5 violated: sentence {index} has a non-positive duration.")
        if previous_end is not None and sentence.start < previous_end - 1e-6:
            raise SegmentationError(f"I2 violated: sentence {index} starts before the previous one ends.")
        previous_end = sentence.end


# --------------------------------------------------------------------------
# Manifest shaping
# --------------------------------------------------------------------------


def result_to_sentences(result: SegmentationResult, language: str) -> list[dict[str, Any]]:
    """Shape sentences the way the course manifest wants them.

    Mirrors ``media_sources.segments_to_sentences`` and adds the two content-model
    fields this module is in a position to decide. No new manifest field is
    introduced: the per-course statistics go to ``buildMetadata.segmentation``.
    """
    sentences: list[dict[str, Any]] = []
    for sentence in result.sentences:
        item: dict[str, Any] = {
            "startTime": round(float(sentence.start), 3),
            "endTime": round(float(sentence.end), 3),
            "sourceText": sentence.text,
            "translationText": "",
            "zhTranslation": "",
            "contentType": sentence.content_type,
            "practiceEligible": sentence.practice_eligible,
        }
        set_source_text(item, sentence.text, language)
        sentences.append(item)
    return sentences


def segment_video_subtitles(
    segments: Sequence[Any],
    *,
    language: str = "ja",
    media_duration: float = 0.0,
    params: SegmentationParams = DEFAULT_PARAMS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """One call for the video builder: cues in, manifest sentences and stats out.

    Wraps :func:`resegment` + :func:`result_to_sentences` so the caller does not
    have to hold a :class:`SegmentationResult` just to reach its manifest block.

    *media_duration* is the probed length of the video, and is only ever used to
    pull the LAST sentence back inside it. ``_build_sentences`` pads every end by
    ``params.tail_pad`` (and floors it at ``params.min_duration``), so the final
    sentence routinely ends a fraction of a second after the video does; a player
    seeking there gets a range the media cannot satisfy. Clamping is skipped when
    it would leave a non-positive duration, because I5 outranks the tidier end
    time — an unplayable zero-length sentence is worse than a 0.15 s overhang.
    """
    result = resegment(segments, language=language, params=params)
    sentences = result_to_sentences(result, language)
    if media_duration > 0 and sentences:
        last = sentences[-1]
        if last["endTime"] > media_duration > last["startTime"]:
            last["endTime"] = round(float(media_duration), 3)
    return sentences, result.to_manifest()
