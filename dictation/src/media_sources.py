"""Recognise online video pages, fetch their captions, and turn them into segments.

This is the only module in the project that knows a video site exists. Everything
above it — the builder, the studio, the player — deals in the ``media`` block that
``course_schema`` validates, never in URLs or subtitle formats. Keep it that way:
a second URL regex somewhere else is how a project ends up with two disagreeing
ideas of what "a YouTube link" means.

Three things live here, in increasing order of how much they can hurt you:

1. ``parse_media_url`` — URL recognition. Its output later becomes an element of a
   ``yt-dlp`` argv, so it treats its input as hostile, not merely malformed.
2. Subtitle parsing and ``clean_segments`` — the quality of the whole feature. A
   naive importer of YouTube auto-captions produces a course in which every
   sentence repeats half of the previous one, because auto-captions are a rolling
   window, not a list of utterances.
3. The ``yt-dlp`` wrappers — the only code that touches the network, and the only
   code that ever writes media to disk. ``temporary_audio`` guarantees it does not
   stay there.

``yt-dlp`` is an OPTIONAL dependency and is resolved at call time, never imported.
Nothing in this module requires it to be installed to be importable or testable:
every network function takes a ``ytdlp=`` argument so tests can point it at a stub.
"""

from __future__ import annotations

import contextlib
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class MediaSourceError(SystemExit):
    """A user-facing failure with an actionable message.

    Subclasses SystemExit for the same reason the rest of this project's CLI errors
    do: it reaches ``main()`` as a clean message instead of a traceback, while a
    caller that wants to keep going (the studio server) can still catch it.
    """


# --------------------------------------------------------------------------
# Provider recognition
# --------------------------------------------------------------------------

PROVIDERS = frozenset({"youtube", "bilibili", "vimeo", "generic"})
CONTROLS = frozenset({"full", "seek-reload", "external"})

MAX_URL_LENGTH = 2048

_YOUTUBE_HOSTS = frozenset({
    "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
    "youtu.be", "www.youtu.be",
    "youtube-nocookie.com", "www.youtube-nocookie.com",
})
_BILIBILI_HOSTS = frozenset({"bilibili.com", "www.bilibili.com", "m.bilibili.com", "b23.tv"})
_VIMEO_HOSTS = frozenset({"vimeo.com", "www.vimeo.com", "player.vimeo.com"})

# YouTube ids are exactly 11 url-safe base64 characters. Accepting anything looser
# means a typo'd link silently becomes a "generic" course with no playback control,
# which is a much more confusing failure than being told the id is wrong.
_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_BILIBILI_BVID = re.compile(r"^BV[A-Za-z0-9]{10}$")
_BILIBILI_AVID = re.compile(r"^av[0-9]{1,12}$", re.IGNORECASE)
_VIMEO_ID = re.compile(r"^[0-9]{6,12}$")

# A host that is an IP literal is never a video site, but it *is* how you would
# point this at something on the local network. Refused outright.
_IPV4_LITERAL = re.compile(r"^[0-9]{1,3}(?:\.[0-9]{1,3}){3}$")


@dataclass(frozen=True)
class MediaRef:
    """A recognised online video, reduced to what the course manifest needs."""

    provider: str
    control: str
    video_id: str
    page_url: str
    embed_url: str

    def to_manifest_media(
        self,
        *,
        duration: float = 0.0,
        uploader: str = "",
        clip: tuple[float, float] | None = None,
        retrieved_at: str = "",
        rights_holder: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        """Return the ``media`` block described in course_schema.normalize_remote_media."""
        media: dict[str, Any] = {
            "kind": "remote",
            "provider": self.provider,
            "control": self.control,
            "videoId": self.video_id,
            "pageUrl": self.page_url,
            "embedUrl": self.embed_url,
            "durationSec": round(float(duration or 0.0), 3),
            "uploader": str(uploader or ""),
            "attribution": {
                "sourceName": _SOURCE_NAMES.get(self.provider, "在线视频"),
                "rightsHolder": str(rights_holder or uploader or ""),
                "retrievedAt": str(retrieved_at or ""),
                # Never negotiable: we hold no rights to the media and the transcript
                # derives from the site's captions. release_readiness/content_license
                # refuse a course carrying this flag.
                "redistributable": False,
                "notes": str(notes or ""),
            },
        }
        if clip is not None:
            start, end = float(clip[0]), float(clip[1])
            media["clip"] = {"startTime": round(start, 3), "endTime": round(end, 3)}
        return media


_SOURCE_NAMES = {
    "youtube": "YouTube",
    "bilibili": "哔哩哔哩",
    "vimeo": "Vimeo",
    "generic": "在线视频",
}

_CONTROL_LABELS = {
    "full": "可完全控制：逐句循环、盲听、变速都可用",
    "seek-reload": "只能重载定位：可反复重播某句，但没有自动循环",
    "external": "无法在页面内驱动：只能在新标签页按时间点打开",
}


def control_label(control: str) -> str:
    """One Chinese line stating what a tier can actually do, for CLI and UI alike."""
    return _CONTROL_LABELS.get(control, control)


def parse_media_url(url: Any) -> MediaRef:
    """Recognise a video page URL, or refuse it.

    The result is handed to ``yt-dlp`` as an argv element and is stored in a course
    manifest, so this is a validation boundary, not a convenience parser. Everything
    it rejects, it rejects because allowing it would put an attacker-chosen string
    somewhere it does not belong.
    """
    raw = str(url or "").strip()
    if not raw:
        raise MediaSourceError("请提供视频链接。/ A video URL is required.")
    if len(raw) > MAX_URL_LENGTH:
        raise MediaSourceError(
            f"链接过长（超过 {MAX_URL_LENGTH} 字符）。/ URL is longer than {MAX_URL_LENGTH} characters."
        )
    # A control character in a URL cannot survive a round trip through a subprocess
    # argument list or a JSON manifest with its meaning intact, so it is always either
    # a mistake or an attempt at one.
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in raw):
        raise MediaSourceError("链接含有控制字符。/ URL contains control characters.")
    # yt-dlp, like every argv-driven tool, reads a leading dash as a flag. urlsplit
    # would happily parse "-x" as a relative path, so this has to be checked on the
    # raw string before parsing, not after.
    if raw.startswith("-"):
        raise MediaSourceError("链接不能以「-」开头。/ A URL may not start with '-'.")

    parts = urlsplit(raw)
    if parts.scheme.lower() not in {"http", "https"}:
        raise MediaSourceError(
            f"只支持 http/https 链接，收到的是「{parts.scheme or '(空)'}」。"
            f" / Only http(s) URLs are supported, got {parts.scheme or '(none)'!r}."
        )
    if parts.username or parts.password:
        raise MediaSourceError("链接不能包含用户名或密码。/ URL must not carry credentials.")

    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise MediaSourceError("链接没有主机名。/ URL has no host.")
    if _IPV4_LITERAL.match(host) or ":" in host or host == "localhost" or host.endswith(".localhost"):
        raise MediaSourceError(
            "不接受指向 IP 地址或本机的链接。/ IP-literal and localhost URLs are refused."
        )
    try:
        port = parts.port
    except ValueError as exc:  # malformed port, e.g. "https://host:notaport/"
        raise MediaSourceError("链接的端口无效。/ URL has an invalid port.") from exc
    if port not in (None, 80, 443):
        raise MediaSourceError(
            f"不接受非标准端口 {port}。/ Refusing a non-standard port ({port})."
        )

    path = parts.path or "/"
    query = dict(parse_qsl(parts.query, keep_blank_values=False))

    if host in _YOUTUBE_HOSTS:
        return _youtube_ref(host, path, query, raw)
    if host in _BILIBILI_HOSTS:
        return _bilibili_ref(host, path, query, raw)
    if host in _VIMEO_HOSTS:
        return _vimeo_ref(path, raw)

    # Anything else that is a well-formed http(s) page. "external" here is a
    # CONSERVATIVE DEFAULT, not a measurement: we have not asked this site whether it
    # can be framed, and most can. Claiming "this site refuses embedding" would be
    # asserting something we never checked. Say what we do instead — open it in a tab.
    return MediaRef(
        provider="generic",
        control="external",
        video_id="",
        page_url=_canonical(parts),
        embed_url="",
    )


def _canonical(parts) -> str:
    """Rebuild the URL without a fragment, which never identifies the video."""
    return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path, parts.query, ""))


def _youtube_ref(host: str, path: str, query: dict[str, str], raw: str) -> MediaRef:
    video_id = ""
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = path.strip("/").split("/", 1)[0]
    elif path == "/watch":
        video_id = query.get("v", "")
    else:
        for prefix in ("/shorts/", "/live/", "/embed/", "/v/"):
            if path.startswith(prefix):
                video_id = path[len(prefix):].strip("/").split("/", 1)[0]
                break
    if not _YOUTUBE_ID.match(video_id):
        raise MediaSourceError(
            "这看起来是 YouTube 链接，但取不出 11 位视频 ID。请用视频页面的完整链接"
            "（形如 https://www.youtube.com/watch?v=XXXXXXXXXXX）。\n"
            f"  收到的是：{raw}\n"
            "  / Could not extract an 11-character YouTube video id from this URL."
        )
    return MediaRef(
        provider="youtube",
        control="full",
        video_id=video_id,
        page_url=f"https://www.youtube.com/watch?v={video_id}",
        # youtube-nocookie sets no tracking cookie until playback starts, and still
        # honours enablejsapi, so it costs nothing and leaks less.
        embed_url=f"https://www.youtube-nocookie.com/embed/{video_id}",
    )


def _bilibili_ref(host: str, path: str, query: dict[str, str], raw: str) -> MediaRef:
    if host == "b23.tv":
        # A short link resolves server-side; we cannot know the BV id without a
        # network round trip, and guessing would be worse than saying so.
        raise MediaSourceError(
            "b23.tv 短链接无法离线解析，请在浏览器里打开后复制地址栏的完整链接"
            "（形如 https://www.bilibili.com/video/BV1xx411c7XX）。\n"
            " / Resolve the b23.tv short link in a browser and pass the full URL."
        )
    video_id = ""
    if path.startswith("/video/"):
        video_id = path[len("/video/"):].strip("/").split("/", 1)[0]
    if not (_BILIBILI_BVID.match(video_id) or _BILIBILI_AVID.match(video_id)):
        raise MediaSourceError(
            "这看起来是哔哩哔哩链接，但取不出 BV/av 号。\n"
            f"  收到的是：{raw}\n"
            " / Could not extract a BV/av id from this bilibili URL."
        )
    page = query.get("p", "")
    page_url = f"https://www.bilibili.com/video/{video_id}"
    embed = f"https://player.bilibili.com/player.html?bvid={video_id}&autoplay=0"
    if page.isdigit() and page != "1":
        page_url += f"?p={page}"
        embed += f"&page={page}"
    return MediaRef(
        provider="bilibili",
        control="seek-reload",
        video_id=video_id,
        page_url=page_url,
        embed_url=embed,
    )


def _vimeo_ref(path: str, raw: str) -> MediaRef:
    candidate = path.strip("/").split("/", 1)[0]
    if candidate == "video":
        candidate = path.strip("/").split("/")[1] if len(path.strip("/").split("/")) > 1 else ""
    if not _VIMEO_ID.match(candidate):
        raise MediaSourceError(
            "这看起来是 Vimeo 链接，但取不出数字视频 ID。\n"
            f"  收到的是：{raw}\n"
            " / Could not extract a numeric Vimeo id from this URL."
        )
    return MediaRef(
        provider="vimeo",
        control="full",
        video_id=candidate,
        page_url=f"https://vimeo.com/{candidate}",
        embed_url=f"https://player.vimeo.com/video/{candidate}",
    )


def timestamp_url(ref: MediaRef, seconds: float) -> str:
    """Deep-link into the original page at a timestamp.

    Truncates rather than rounds: landing a fraction of a second early keeps the
    first syllable of the sentence, landing late clips it, and clipping the thing
    the learner is trying to hear is the failure that matters.
    """
    whole = max(0, int(float(seconds or 0.0)))
    parts = urlsplit(ref.page_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=False))
    if ref.provider == "youtube":
        query["t"] = f"{whole}s"
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
    if ref.provider == "bilibili":
        query["t"] = str(whole)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
    if ref.provider == "vimeo":
        return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, f"t={whole}s"))
    return ref.page_url


# --------------------------------------------------------------------------
# Subtitle parsing
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Token:
    """One recogniser token with its own absolute start time.

    YouTube's json3 auto-caption tracks carry a per-token offset inside each cue.
    That offset is the only signal in this whole pipeline that can tell a pause
    between two sentences from a line break in the middle of one, so it is kept
    here instead of being flattened away into the cue's text.
    """

    text: str
    start: float


@dataclass(frozen=True)
class Segment:
    """One timed utterance, in absolute seconds on the original video timeline.

    ``tokens`` is empty whenever the source cannot supply per-token times — SRT,
    WebVTT, most manual tracks, and ASR output. That is a normal state, not an
    error: the re-segmenter degrades to cue-level interpolation and records that
    it did so, rather than pretending to a resolution it does not have.

    When ``tokens`` is non-empty it is an invariant that concatenating the token
    texts reproduces ``text`` exactly. Every transform below that edits ``text``
    either re-derives the tokens or drops them; nothing is allowed to leave the
    two disagreeing, because the re-segmenter trusts this to map characters back
    to times.
    """

    start: float
    end: float
    text: str
    tokens: tuple[Token, ...] = ()


@dataclass(frozen=True)
class SubtitleTrack:
    language: str
    kind: str      # "manual" | "auto"
    format: str    # "vtt" | "srt" | "json3"
    text: str


_TIMECODE = re.compile(
    r"(?P<h>\d{1,3}):(?P<m>\d{2}):(?P<s>\d{2})[.,](?P<ms>\d{1,3})"
    r"\s*-->\s*"
    r"(?P<h2>\d{1,3}):(?P<m2>\d{2}):(?P<s2>\d{2})[.,](?P<ms2>\d{1,3})"
)
# WebVTT allows MM:SS.mmm as well as HH:MM:SS.mmm.
_TIMECODE_SHORT = re.compile(
    r"(?P<m>\d{1,3}):(?P<s>\d{2})[.,](?P<ms>\d{1,3})"
    r"\s*-->\s*"
    r"(?P<m2>\d{1,3}):(?P<s2>\d{2})[.,](?P<ms2>\d{1,3})"
)


def sniff_subtitle_format(text: str) -> str:
    """Identify a subtitle blob by its content, never by its filename."""
    stripped = text.lstrip("﻿").lstrip()
    if stripped.startswith("WEBVTT"):
        return "vtt"
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(payload, dict) and isinstance(payload.get("events"), list):
                return "json3"
    if _TIMECODE.search(stripped) or _TIMECODE_SHORT.search(stripped):
        return "srt"
    raise MediaSourceError(
        "无法识别字幕格式，支持 .srt / .vtt / .json3。"
        " / Unrecognised subtitle format; expected SRT, WebVTT or YouTube json3."
    )


def parse_subtitles(text: str, *, fmt: str | None = None) -> list[Segment]:
    """Parse SRT, WebVTT or YouTube json3 into raw, uncleaned segments."""
    body = text.lstrip("﻿")
    chosen = fmt or sniff_subtitle_format(body)
    if chosen == "json3":
        return _parse_json3(body)
    if chosen in {"vtt", "srt"}:
        return _parse_cue_based(body)
    raise MediaSourceError(f"不支持的字幕格式：{chosen} / Unsupported subtitle format: {chosen!r}")


def _parse_cue_based(text: str) -> list[Segment]:
    """Parse WebVTT and SRT with one reader.

    The two formats differ in the decimal separator, an optional cue index, and
    WebVTT's NOTE/STYLE/REGION blocks and cue settings — none of which change how
    the timing line is found, so splitting this into two near-identical parsers
    would only create two places for the same bug to live.
    """
    segments: list[Segment] = []
    # Normalise line endings first: a CRLF file read as text on one platform and
    # bytes on another otherwise leaves a stray \r glued to the last word of a cue.
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith(("NOTE", "STYLE", "REGION", "WEBVTT")):
            index += 1
            continue
        match = _TIMECODE.search(stripped) or _TIMECODE_SHORT.search(stripped)
        if not match:
            index += 1
            continue
        start, end = _timecode_seconds(match)
        index += 1
        body: list[str] = []
        while index < total and lines[index].strip():
            body.append(lines[index])
            index += 1
        segments.append(Segment(start=start, end=end, text="\n".join(body)))
    return segments


def _timecode_seconds(match: re.Match[str]) -> tuple[float, float]:
    groups = match.groupdict()
    def seconds(prefix: str) -> float:
        hours = float(groups.get("h" + prefix) or 0)
        minutes = float(groups.get("m" + prefix) or 0)
        secs = float(groups.get("s" + prefix) or 0)
        raw_ms = str(groups.get("ms" + prefix) or "0")
        # ".5" in WebVTT means 500ms, not 5ms.
        millis = float(raw_ms.ljust(3, "0")[:3])
        return hours * 3600 + minutes * 60 + secs + millis / 1000.0
    return seconds(""), seconds("2")


def _parse_json3(text: str) -> list[Segment]:
    """Parse YouTube's json3 caption format.

    Events without ``segs`` are window/style definitions, not speech. Events
    carrying ``aAppend`` are the rolling-window continuation records that make a
    naive import duplicate every line — they are dropped here rather than in
    clean_segments, because at this level we can still tell them apart by their
    flag instead of having to guess from the text.
    """
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MediaSourceError(f"json3 字幕不是有效 JSON：{exc} / Invalid json3 subtitle JSON.") from exc
    events = payload.get("events")
    if not isinstance(events, list):
        raise MediaSourceError("json3 字幕缺少 events 数组。/ json3 subtitle has no events array.")

    segments: list[Segment] = []
    for event in events:
        if not isinstance(event, dict) or event.get("aAppend"):
            continue
        segs = event.get("segs")
        if not isinstance(segs, list):
            continue
        start_ms = event.get("tStartMs")
        duration_ms = event.get("dDurationMs")
        if not isinstance(start_ms, (int, float)):
            continue
        start = float(start_ms) / 1000.0

        pieces: list[str] = []
        tokens: list[Token] = []
        carries_offsets = False
        for seg in segs:
            if not isinstance(seg, dict):
                continue
            piece = str(seg.get("utf8", ""))
            if not piece:
                continue
            pieces.append(piece)
            offset = seg.get("tOffsetMs")
            if isinstance(offset, (int, float)):
                carries_offsets = True
                tokens.append(Token(text=piece, start=start + float(offset) / 1000.0))
            else:
                tokens.append(Token(text=piece, start=start))
        body = "".join(pieces)
        if not body.strip():
            continue
        end = start + (float(duration_ms) / 1000.0 if isinstance(duration_ms, (int, float)) else 0.0)
        # Tokens that all sit on the cue's own start carry no information the cue
        # does not already have. Dropping them keeps "has tokens" meaning "has
        # resolution finer than the cue", which is what the re-segmenter tests.
        segments.append(
            Segment(start=start, end=end, text=body, tokens=tuple(tokens) if carries_offsets else ())
        )
    return segments


# --------------------------------------------------------------------------
# Cleaning
# --------------------------------------------------------------------------

_TAG = re.compile(r"<[^>]*>")
_NOISE_WORDS = (
    "music", "applause", "laughter", "laughs", "inaudible", "silence", "sound",
    "音楽", "拍手", "笑い", "笑", "無音", "咳", "音声", "掌声", "音乐",
)
_BRACKETED = re.compile(r"[\[\(（【][^\]\)）】]{0,24}[\]\)）】]")
_SPEAKER_TAG = re.compile(r"^\s*(?:-\s*)?(?:[A-Z][A-Z .'-]{1,20}|話者\s*\d+|发言人\s*\d+)\s*[:：]\s*")
_MUSIC_NOTE = re.compile(r"[♪♫]+")

# Languages written without spaces between words. Latin-script languages keep their
# single spaces; CJK text must not gain any, or every diff against the learner's
# answer would show phantom whitespace differences.
_SPACELESS = frozenset({"ja", "zh", "ko"})

# How close two cues must be to count as one rolling-window utterance rather than
# two separate ones. Auto-caption cues abut exactly; this leaves room for the
# rounding a caption file goes through without reaching real conversational pauses.
_SEAM_GAP = 0.75


def normalize_cue_text(value: str, *, language: str = "ja") -> str:
    """Reduce one cue to the text a learner should actually read.

    Strips WebVTT karaoke markup (``<00:00:01.000><c>…</c>``), HTML entities,
    speaker tags, and bracketed noise labels such as ``[音楽]`` or ``(laughs)``.
    A bracketed run is only removed when it reads as a noise label; ``（笑）`` goes,
    but a legitimate parenthetical in the transcript stays.
    """
    text = _TAG.sub("", str(value or ""))
    text = html.unescape(text)
    text = _MUSIC_NOTE.sub(" ", text)

    def drop_noise(match: re.Match[str]) -> str:
        inner = match.group(0)[1:-1].strip().casefold()
        if not inner:
            return " "
        return " " if any(word in inner for word in _NOISE_WORDS) else match.group(0)

    text = _BRACKETED.sub(drop_noise, text)
    text = "\n".join(_SPEAKER_TAG.sub("", line) for line in text.split("\n"))
    text = text.replace("\n", " ")
    if language in _SPACELESS:
        # Collapse whitespace away entirely: auto-captions for Japanese insert
        # spaces at recogniser token boundaries that no writer would type, and the
        # dictation grader compares against what a writer would type.
        text = re.sub(r"\s+", "", text)
    else:
        text = re.sub(r"\s+", " ", text).strip()
    return text.strip()


def clean_segments(
    segments: list[Segment],
    *,
    language: str = "ja",
    min_duration: float = 0.35,
    clip: tuple[float, float] | None = None,
    rolling_window: bool = True,
) -> list[Segment]:
    """Turn raw cues into segments a learner can practise against.

    ``rolling_window`` is the dangerous transform and is therefore a parameter, not
    a heuristic. YouTube AUTO captions repeat the previous cue's text as a prefix of
    the next one ("今日の" → "今日のニュースです" → "ニュースです。次は"); collapsing
    that is mandatory or every sentence in the course starts with half the previous
    one. MANUAL subtitles have no such artifact, and running the collapse over them
    can eat a genuinely repeated phrase — so the caller passes ``rolling_window=False``
    for a manual track. ``fetch_subtitles`` knows which kind it got; this function
    does not, and must not guess.
    """
    normalized: list[Segment] = []
    for segment in segments:
        text = normalize_cue_text(segment.text, language=language)
        if not text:
            continue
        start = max(0.0, float(segment.start))
        end = float(segment.end)
        if end <= start:
            end = start + min_duration
        normalized.append(
            Segment(
                start=start,
                end=end,
                text=text,
                tokens=_normalize_tokens(segment.tokens, text, language=language),
            )
        )

    if not normalized:
        return []

    if rolling_window:
        normalized = _collapse_rolling_window(normalized, language=language)

    normalized.sort(key=lambda item: (item.start, item.end))

    # Clamp overlaps forward. A cue that starts before the previous one ended makes
    # the player's "which sentence am I in" lookup ambiguous, and the audit flags it.
    clamped: list[Segment] = []
    for segment in normalized:
        start = segment.start
        if clamped and start < clamped[-1].end:
            start = clamped[-1].end
        if segment.end <= start:
            continue
        clamped.append(
            Segment(start=start, end=segment.end, text=segment.text, tokens=segment.tokens)
        )

    # Extend a cue that is too short to be practisable, but only into silence —
    # never past the start of the next cue, which would recreate the overlap we
    # just removed.
    extended: list[Segment] = []
    for position, segment in enumerate(clamped):
        end = segment.end
        if end - segment.start < min_duration:
            ceiling = clamped[position + 1].start if position + 1 < len(clamped) else end + min_duration
            end = min(max(end, segment.start + min_duration), ceiling)
        if end <= segment.start:
            continue
        extended.append(
            Segment(
                start=round(segment.start, 3),
                end=round(end, 3),
                text=segment.text,
                tokens=segment.tokens,
            )
        )

    if clip is not None:
        low, high = float(clip[0]), float(clip[1])
        extended = [s for s in extended if s.end > low and s.start < high]

    return extended


def _collapse_rolling_window(segments: list[Segment], *, language: str) -> list[Segment]:
    """Collapse auto-caption cues that grow by re-stating the previous cue.

    Two distinct artifacts, handled separately because they need different guards:

    * A cue whose text *contains the previous cue as a prefix* is the same utterance
      being re-emitted as more of it is recognised. The earlier, shorter copy is
      dropped and its start time is kept, since that is when the speech began.
    * Consecutive cues that *overlap at the seam* ("…ニュースです" then
      "ニュースです。次は") are trimmed at the seam. Only applied to adjacent cues,
      only when the overlap is at least two characters, and never when trimming
      would empty the later cue — the guard against eating a real repetition.
    """
    collapsed: list[Segment] = []
    for segment in segments:
        if collapsed:
            previous = collapsed[-1]
            # Adjacency is what separates a captioning artifact from ordinary speech.
            # A rolling window re-emits the same utterance continuously, so its cues
            # abut; two cues eight seconds apart are two things the speaker said, and
            # merging them would delete a sentence the learner is supposed to practise
            # ("もう一度" at 0s, "もう一度お願いします" at 10s).
            adjacent = segment.start - previous.end <= _SEAM_GAP
            if adjacent and segment.text.startswith(previous.text) and len(segment.text) > len(previous.text):
                collapsed[-1] = Segment(
                    start=previous.start,
                    end=segment.end,
                    text=segment.text,
                    tokens=segment.tokens,
                )
                continue
            if adjacent and segment.text == previous.text:
                collapsed[-1] = Segment(
                    start=previous.start,
                    end=max(previous.end, segment.end),
                    text=previous.text,
                    tokens=previous.tokens,
                )
                continue
        collapsed.append(segment)

    trimmed: list[Segment] = []
    minimum_overlap = 2 if language in _SPACELESS else 4
    for segment in collapsed:
        text = segment.text
        tokens = segment.tokens
        if trimmed:
            previous = trimmed[-1]
            # Only an adjacent seam. A gap means two separate utterances that happen
            # to share words, which is ordinary language, not a captioning artifact.
            if segment.start - previous.end <= _SEAM_GAP:
                overlap = _seam_overlap(previous.text, text, minimum_overlap)
                if overlap and len(text) > overlap:
                    text = text[overlap:].lstrip()
                    tokens = _drop_leading_chars(tokens, len(segment.text) - len(text))
        if text:
            trimmed.append(
                Segment(
                    start=segment.start,
                    end=segment.end,
                    text=text,
                    tokens=tokens if _tokens_match(tokens, text) else (),
                )
            )
    return trimmed


def _normalize_tokens(
    tokens: tuple[Token, ...], text: str, *, language: str
) -> tuple[Token, ...]:
    """Normalise tokens alongside their cue, or give up and return none.

    The tokens must keep reproducing the cue text exactly; when normalisation of
    the parts does not reassemble into normalisation of the whole (a tag spanning
    a token boundary, a bracketed noise label split across two), returning empty
    costs one cue's worth of resolution, while returning a mismatched mapping
    would silently mis-time every sentence cut inside it.

    Space-separated languages usually land in the give-up branch, because the
    per-token strip removes the spaces the joined cue keeps. That is a known
    limitation, not a bug to route around here: those courses fall back to
    cue-level interpolation and the manifest records it.
    """
    if not tokens:
        return ()
    cleaned: list[Token] = []
    for token in tokens:
        piece = normalize_cue_text(token.text, language=language)
        if piece:
            cleaned.append(Token(text=piece, start=token.start))
    result = tuple(cleaned)
    return result if _tokens_match(result, text) else ()


def _drop_leading_chars(tokens: tuple[Token, ...], count: int) -> tuple[Token, ...]:
    """Remove the first *count* characters from a token run, keeping the times."""
    if not tokens or count <= 0:
        return tokens
    remaining = count
    kept: list[Token] = []
    for token in tokens:
        if remaining <= 0:
            kept.append(token)
            continue
        if remaining >= len(token.text):
            remaining -= len(token.text)
            continue
        kept.append(Token(text=token.text[remaining:], start=token.start))
        remaining = 0
    return tuple(kept)


def _tokens_match(tokens: tuple[Token, ...], text: str) -> bool:
    return bool(tokens) and "".join(token.text for token in tokens) == text


def _seam_overlap(previous: str, current: str, minimum: int) -> int:
    """Length of the longest suffix of *previous* that prefixes *current*."""
    limit = min(len(previous), len(current))
    for size in range(limit, minimum - 1, -1):
        if previous.endswith(current[:size]):
            return size
    return 0


def segments_to_sentences(segments: list[Segment], language: str) -> list[dict[str, Any]]:
    """Shape cleaned segments the way the course manifest wants them.

    Kept here rather than in the builder so the studio and any future importer
    produce sentences with identical field names and rounding.
    """
    from language_support import set_source_text  # local import: keeps this module standalone

    sentences: list[dict[str, Any]] = []
    for segment in segments:
        item: dict[str, Any] = {
            "startTime": round(float(segment.start), 3),
            "endTime": round(float(segment.end), 3),
            "sourceText": segment.text,
            "translationText": "",
            "zhTranslation": "",
        }
        set_source_text(item, segment.text, language)
        sentences.append(item)
    return sentences


# --------------------------------------------------------------------------
# yt-dlp: the only code here that touches the network
# --------------------------------------------------------------------------

_YTDLP_MISSING = (
    "找不到 yt-dlp。在线视频课程需要它来读取站点字幕或临时取音频。\n"
    "  安装：pip install yt-dlp\n"
    "  或用 --ytdlp 指定可执行文件路径。\n"
    "  / yt-dlp was not found. Install it with 'pip install yt-dlp', or pass --ytdlp <path>."
)


def resolve_ytdlp(explicit: str | None = None) -> list[str]:
    """Return the argv prefix that runs yt-dlp, or refuse with an actionable message.

    Returns a list rather than a string because the fallback is ``python -m yt_dlp``,
    which is two elements. Callers append their own flags and must always place
    ``--`` before the URL.
    """
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            # A stub or a pinned build. Run a .py stub through this interpreter so
            # tests do not depend on the platform honouring a shebang.
            if candidate.suffix.lower() == ".py":
                return [sys.executable, str(candidate)]
            return [str(candidate)]
        found = shutil.which(explicit)
        if found:
            return [found]
        raise MediaSourceError(f"指定的 yt-dlp 不存在：{explicit} / No such yt-dlp executable: {explicit}")

    for name in ("yt-dlp", "yt-dlp.exe", "yt_dlp"):
        found = shutil.which(name)
        if found:
            return [found]

    # Installed as a library but not on PATH — common inside a virtualenv on Windows.
    probe = subprocess.run(
        [sys.executable, "-c", "import yt_dlp"],
        capture_output=True,
        check=False,
    )
    if probe.returncode == 0:
        return [sys.executable, "-m", "yt_dlp"]

    raise MediaSourceError(_YTDLP_MISSING)


def ytdlp_available(explicit: str | None = None) -> bool:
    """Whether a yt-dlp can be resolved, without raising. For the studio's UI."""
    try:
        resolve_ytdlp(explicit)
    except MediaSourceError:
        return False
    return True


def _run_ytdlp(argv: list[str], *, timeout: float, what: str) -> str:
    """Run yt-dlp with a fixed argv. Never a shell, never an unbounded wait."""
    env = os.environ.copy()
    # Section 11.2 of PROJECT_STRUCTURE.md: without these, non-ASCII output from a
    # child process on Windows arrives mangled by the console code page and the
    # damage is only noticed at the final audit.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # The build subprocess has no business inheriting this server's session token.
    env.pop("DICTATION_SESSION_TOKEN", None)
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:
        raise MediaSourceError(_YTDLP_MISSING) from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaSourceError(
            f"{what} 超时（{timeout:.0f} 秒）。网络太慢或视频过长。"
            f" / {what} timed out after {timeout:.0f}s."
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        tail = "\n  ".join(detail[-6:]) if detail else "(no output)"
        raise MediaSourceError(f"{what} 失败 / {what} failed (exit {completed.returncode}):\n  {tail}")
    return completed.stdout


def probe_media(url: str, *, ytdlp: str | None = None, timeout: float = 120.0) -> dict[str, Any]:
    """Read a video's metadata and caption inventory without downloading anything."""
    ref = parse_media_url(url)
    argv = resolve_ytdlp(ytdlp) + [
        "--no-playlist",
        "--skip-download",
        "--no-warnings",
        "--dump-single-json",
        "--",
        ref.page_url,
    ]
    raw = _run_ytdlp(argv, timeout=timeout, what="读取视频信息 / probe")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MediaSourceError(f"yt-dlp 返回的不是 JSON：{exc} / yt-dlp did not return JSON.") from exc

    tracks: list[dict[str, str]] = []
    for key, kind in (("subtitles", "manual"), ("automatic_captions", "auto")):
        available = payload.get(key)
        if isinstance(available, dict):
            for language in sorted(available):
                tracks.append({"language": str(language), "kind": kind})

    duration = payload.get("duration")
    return {
        "title": str(payload.get("title") or ""),
        "uploader": str(payload.get("uploader") or payload.get("channel") or ""),
        "durationSec": float(duration) if isinstance(duration, (int, float)) else 0.0,
        "webpageUrl": str(payload.get("webpage_url") or ref.page_url),
        "extractor": str(payload.get("extractor_key") or payload.get("extractor") or ""),
        "subtitles": tracks,
    }


_SUBTITLE_SUFFIXES = (".json3", ".srv3", ".vtt", ".srt", ".ttml")


def fetch_subtitles(
    url: str,
    *,
    languages: list[str],
    work_dir: Path,
    prefer_manual: bool = True,
    ytdlp: str | None = None,
    timeout: float = 300.0,
) -> SubtitleTrack | None:
    """Download only the caption track, never the video. None when there is none.

    Manual and automatic captions are fetched in two separate passes rather than one
    combined pass, because yt-dlp writes both to the same ``<id>.<lang>.<ext>``
    filename shape — after a combined run there is no way left to tell which kind a
    file holds, and that distinction decides whether ``clean_segments`` may apply its
    rolling-window collapse.
    """
    ref = parse_media_url(url)
    prefix = resolve_ytdlp(ytdlp)
    wanted = [lang for lang in languages if lang] or ["ja", "en"]
    work_dir.mkdir(parents=True, exist_ok=True)

    passes = [("manual", "--write-subs"), ("auto", "--write-auto-subs")]
    if not prefer_manual:
        passes.reverse()

    for kind, flag in passes:
        target = Path(tempfile.mkdtemp(dir=str(work_dir), prefix=f"subs-{kind}-"))
        argv = prefix + [
            "--no-playlist",
            "--skip-download",
            "--no-warnings",
            flag,
            "--sub-langs", ",".join(wanted),
            "--sub-format", "json3/vtt/srt/best",
            "--paths", str(target),
            "--output", "%(id)s.%(ext)s",
            "--",
            ref.page_url,
        ]
        try:
            _run_ytdlp(argv, timeout=timeout, what=f"下载{'人工' if kind == 'manual' else '自动'}字幕 / fetch {kind} subtitles")
        except MediaSourceError:
            # A site with no track of this kind is a normal outcome, not a failure:
            # the caller falls through to the next pass and then to ASR.
            shutil.rmtree(target, ignore_errors=True)
            continue
        track = _pick_subtitle_file(target, wanted, kind)
        if track is not None:
            shutil.rmtree(target, ignore_errors=True)
            persist_subtitle_track(track, work_dir, page_url=ref.page_url)
            return track
        shutil.rmtree(target, ignore_errors=True)
    return None


def persist_subtitle_track(
    track: SubtitleTrack, work_dir: Path, *, page_url: str
) -> Path:
    """Keep the raw caption track so re-segmentation never needs the network again.

    The track is the input the sentences were derived from. Without it, changing a
    segmentation parameter means re-fetching from the site — which is slow, is not
    reproducible (tracks change), and may not be possible later at all.

    This does not weaken the copyright position: what lands on disk is caption
    text, not media. ``temporary_audio`` still deletes audio in its ``finally``
    block, ``video-work/`` is gitignored, and nothing here reaches ``courses/`` or
    a ZIP.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    path = work_dir / f"subtitles.{track.language}.{track.format}"
    path.write_text(track.text, encoding="utf-8")
    (work_dir / "track.json").write_text(
        json.dumps(
            {
                "language": track.language,
                "kind": track.kind,
                "format": track.format,
                "retrievedAt": _today(),
                "sourceUrl": page_url,
                "file": path.name,
                "sha256": hashlib.sha256(track.text.encode("utf-8")).hexdigest(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def load_persisted_track(work_dir: Path) -> SubtitleTrack | None:
    """Read back a track written by :func:`persist_subtitle_track`, if there is one."""
    record = work_dir / "track.json"
    if not record.is_file():
        return None
    try:
        payload = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    path = work_dir / str(payload.get("file") or "")
    if not path.is_file():
        return None
    return SubtitleTrack(
        language=str(payload.get("language") or ""),
        kind=str(payload.get("kind") or "auto"),
        format=str(payload.get("format") or ""),
        text=path.read_text(encoding="utf-8-sig", errors="replace"),
    )


def _today() -> str:
    import datetime

    return datetime.date.today().isoformat()


def _pick_subtitle_file(directory: Path, wanted: list[str], kind: str) -> SubtitleTrack | None:
    """Choose the best downloaded track: requested language order wins."""
    candidates: list[tuple[int, int, Path, str]] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in _SUBTITLE_SUFFIXES:
            continue
        # yt-dlp names subtitles "<id>.<lang>.<ext>"; the language is the second
        # suffix from the right.
        language = path.suffixes[-2].lstrip(".") if len(path.suffixes) >= 2 else ""
        rank = _language_rank(language, wanted)
        if rank is None:
            continue
        format_rank = _SUBTITLE_SUFFIXES.index(path.suffix.lower())
        candidates.append((rank, format_rank, path, language))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    _, _, path, language = candidates[0]
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    suffix = path.suffix.lower()
    fmt = "json3" if suffix in {".json3", ".srv3"} else suffix.lstrip(".")
    return SubtitleTrack(language=language, kind=kind, format=fmt, text=text)


def _language_rank(language: str, wanted: list[str]) -> int | None:
    """Position of *language* in the wanted list, matching 'ja' against 'ja-JP'."""
    normalized = language.lower()
    for position, candidate in enumerate(wanted):
        target = candidate.lower()
        if normalized == target or normalized.startswith(target + "-") or target.startswith(normalized + "-"):
            return position
    return None


@contextlib.contextmanager
def temporary_audio(
    url: str,
    *,
    work_dir: Path,
    ytdlp: str | None = None,
    timeout: float = 1800.0,
) -> Iterator[Path]:
    """Extract the audio track, yield its path, and delete it — always.

    This is the only place in the project where media touches the disk, and it exists
    only because a video with no captions cannot otherwise be transcribed. The whole
    working directory is removed in ``finally``, which also takes yt-dlp's ``.part``
    and ``.ytdl`` leftovers with it: deleting only the file we know about would leave
    a half-downloaded copy behind on exactly the failure paths where it matters most.
    """
    ref = parse_media_url(url)
    prefix = resolve_ytdlp(ytdlp)
    work_dir.mkdir(parents=True, exist_ok=True)
    # mkdtemp, not a predictable name: two builds of the same video must not collide,
    # and nothing else should be able to guess the path and read it mid-build.
    target = Path(tempfile.mkdtemp(dir=str(work_dir), prefix="audio-"))
    try:
        argv = prefix + [
            "--no-playlist",
            "--no-warnings",
            "--extract-audio",
            "--audio-format", "mp3",
            "--format", "bestaudio/best",
            "--paths", str(target),
            "--output", "audio.%(ext)s",
            "--",
            ref.page_url,
        ]
        _run_ytdlp(argv, timeout=timeout, what="临时提取音频 / extract audio")
        produced = [p for p in sorted(target.iterdir()) if p.is_file() and p.suffix.lower() != ".part"]
        if not produced:
            raise MediaSourceError(
                "yt-dlp 没有产出音频文件。/ yt-dlp produced no audio file."
            )
        yield produced[0]
    finally:
        shutil.rmtree(target, ignore_errors=True)
