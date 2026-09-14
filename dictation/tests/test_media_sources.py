"""The media source layer: URL validation, subtitle parsing, and the yt-dlp seam.

Two things here are load-bearing and get most of the coverage:

* ``parse_media_url`` is a security boundary — its output becomes a yt-dlp argv
  element — so every rejection it makes has a test that proves it still rejects.
* ``clean_segments`` decides what a learner actually reads. A rolling-window
  auto-caption imported naively produces a course where every sentence repeats
  half the previous one, so the fixtures below are real captioning artifacts
  rather than tidy invented ones.

No test may require yt-dlp to be installed (it is not, on the machine this was
written on). The network functions are driven against a stub executable written
into a temp directory.
"""

from __future__ import annotations

import json
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from media_sources import (
    MediaSourceError,
    Segment,
    clean_segments,
    control_label,
    fetch_subtitles,
    normalize_cue_text,
    parse_media_url,
    parse_subtitles,
    probe_media,
    resolve_ytdlp,
    segments_to_sentences,
    sniff_subtitle_format,
    temporary_audio,
    timestamp_url,
    ytdlp_available,
)


class UrlRecognitionTests(unittest.TestCase):
    def test_youtube_watch_url_yields_a_fully_controllable_reference(self) -> None:
        ref = parse_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123")
        self.assertEqual(ref.provider, "youtube")
        self.assertEqual(ref.control, "full")
        self.assertEqual(ref.video_id, "dQw4w9WgXcQ")
        self.assertEqual(ref.page_url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(ref.embed_url, "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ")

    def test_every_youtube_url_shape_reaches_the_same_video_id(self) -> None:
        for url in (
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/live/dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        ):
            with self.subTest(url=url):
                self.assertEqual(parse_media_url(url).video_id, "dQw4w9WgXcQ")

    def test_a_youtube_url_with_an_unusable_id_is_refused_not_downgraded(self) -> None:
        # Silently becoming a "generic" course would strip every playback control
        # and give the learner no clue that their link was simply wrong.
        with self.assertRaises(MediaSourceError) as caught:
            parse_media_url("https://www.youtube.com/watch?v=tooshort")
        self.assertIn("11", str(caught.exception))

    def test_bilibili_is_recognised_as_seek_reload_with_a_player_embed(self) -> None:
        ref = parse_media_url("https://www.bilibili.com/video/BV1xx411c7XX?p=2")
        self.assertEqual((ref.provider, ref.control), ("bilibili", "seek-reload"))
        self.assertIn("bvid=BV1xx411c7XX", ref.embed_url)
        self.assertIn("page=2", ref.embed_url)

    def test_vimeo_is_recognised_as_fully_controllable(self) -> None:
        ref = parse_media_url("https://vimeo.com/123456789")
        self.assertEqual((ref.provider, ref.control), ("vimeo", "full"))
        self.assertEqual(ref.embed_url, "https://player.vimeo.com/video/123456789")

    def test_an_unknown_site_still_produces_a_usable_external_course(self) -> None:
        ref = parse_media_url("https://www3.nhk.or.jp/news/easy/k100.html?x=1#frag")
        self.assertEqual((ref.provider, ref.control), ("generic", "external"))
        self.assertEqual(ref.embed_url, "")
        # The fragment never identifies the video and must not reach the manifest.
        self.assertNotIn("#", ref.page_url)

    def test_a_bilibili_short_link_says_what_to_do_instead_of_guessing(self) -> None:
        with self.assertRaises(MediaSourceError) as caught:
            parse_media_url("https://b23.tv/abcdef")
        self.assertIn("b23.tv", str(caught.exception))


class UrlRejectionTests(unittest.TestCase):
    """Each of these would put an attacker-chosen string somewhere it does not belong."""

    def test_non_web_schemes_are_refused(self) -> None:
        for url in ("file:///etc/passwd", "ftp://example.com/v", "data:text/html,x", "javascript:alert(1)"):
            with self.subTest(url=url), self.assertRaises(MediaSourceError):
                parse_media_url(url)

    def test_a_leading_dash_can_never_become_a_yt_dlp_flag(self) -> None:
        # urlsplit parses "-x" as a relative path without complaint, so this has to
        # be caught on the raw string before parsing.
        for url in ("-x", "--exec=calc.exe", "-o/tmp/x"):
            with self.subTest(url=url), self.assertRaises(MediaSourceError):
                parse_media_url(url)

    def test_credentials_in_the_url_are_refused(self) -> None:
        with self.assertRaises(MediaSourceError):
            parse_media_url("https://user:secret@www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_ip_literals_and_localhost_are_refused(self) -> None:
        for url in ("http://127.0.0.1/v", "http://192.168.1.5/v", "http://localhost/v",
                    "http://[::1]/v", "http://app.localhost/v"):
            with self.subTest(url=url), self.assertRaises(MediaSourceError):
                parse_media_url(url)

    def test_non_standard_ports_are_refused(self) -> None:
        with self.assertRaises(MediaSourceError):
            parse_media_url("http://example.com:4173/video")

    def test_control_characters_and_overlong_urls_are_refused(self) -> None:
        with self.assertRaises(MediaSourceError):
            parse_media_url("https://example.com/v\nX-Injected: 1")
        with self.assertRaises(MediaSourceError):
            parse_media_url("https://example.com/" + "a" * 4000)

    def test_an_empty_url_is_refused(self) -> None:
        for value in ("", "   ", None):
            with self.subTest(value=value), self.assertRaises(MediaSourceError):
                parse_media_url(value)


class TimestampLinkTests(unittest.TestCase):
    def test_each_provider_gets_its_own_deep_link_shape(self) -> None:
        youtube = parse_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(
            timestamp_url(youtube, 65.9),
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=65s",
        )
        bilibili = parse_media_url("https://www.bilibili.com/video/BV1xx411c7XX")
        self.assertIn("t=65", timestamp_url(bilibili, 65.9))
        vimeo = parse_media_url("https://vimeo.com/123456789")
        self.assertTrue(timestamp_url(vimeo, 65.9).endswith("#t=65s"))

    def test_a_timestamp_truncates_rather_than_rounds(self) -> None:
        # Landing early keeps the first syllable; landing late clips the very thing
        # the learner is trying to hear.
        youtube = parse_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertIn("t=65s", timestamp_url(youtube, 65.99))
        self.assertIn("t=0s", timestamp_url(youtube, -3.0))


class ManifestMediaTests(unittest.TestCase):
    def test_a_remote_media_block_is_never_marked_redistributable(self) -> None:
        ref = parse_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        media = ref.to_manifest_media(duration=612.0, uploader="NHK", retrieved_at="2026-08-31")
        self.assertEqual(media["kind"], "remote")
        self.assertIs(media["attribution"]["redistributable"], False)
        self.assertEqual(media["attribution"]["rightsHolder"], "NHK")
        self.assertNotIn("clip", media)

    def test_a_clip_window_is_recorded_when_given(self) -> None:
        ref = parse_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        media = ref.to_manifest_media(clip=(30.0, 90.5))
        self.assertEqual(media["clip"], {"startTime": 30.0, "endTime": 90.5})

    def test_every_control_tier_has_a_chinese_label(self) -> None:
        for control in ("full", "seek-reload", "external"):
            with self.subTest(control=control):
                self.assertTrue(control_label(control).strip())


# --------------------------------------------------------------------------
# Subtitle fixtures — real captioning artifacts, not tidy invented ones
# --------------------------------------------------------------------------

MANUAL_SRT = "\r\n".join([
    "1",
    "00:00:01,000 --> 00:00:03,500",
    "おはようございます。",
    "",
    "2",
    "00:00:03,500 --> 00:00:07,000",
    "今日のニュースをお伝えします。",
    "",
])

AUTO_VTT = textwrap.dedent(
    """\
    WEBVTT
    Kind: captions
    Language: ja

    NOTE this block must be skipped

    00:00:01.000 --> 00:00:02.200 align:start position:0%
    今日の<00:00:01.500><c>ニュース</c>

    00:00:02.200 --> 00:00:04.000 align:start position:0%
    今日のニュースです

    00:00:04.000 --> 00:00:06.000 align:start position:0%
    ニュースです。次は天気です

    00:00:06.000 --> 00:00:08.000
    [音楽]

    00:00:08.000 --> 00:00:08.080
    はい
    """
)


def json3_fixture() -> str:
    """A YouTube json3 track with per-word timing and an aAppend continuation."""
    return json.dumps({
        "events": [
            {"tStartMs": 0, "dDurationMs": 500, "wWinId": 1},           # window definition
            {
                "tStartMs": 1000,
                "dDurationMs": 1200,
                "segs": [
                    {"utf8": "今日", "tOffsetMs": 0},
                    {"utf8": "の", "tOffsetMs": 200},
                    {"utf8": "ニュース", "tOffsetMs": 400},
                ],
            },
            # The rolling-window continuation record: same text re-emitted.
            {"tStartMs": 2200, "dDurationMs": 100, "aAppend": 1, "segs": [{"utf8": "今日のニュース"}]},
            {
                "tStartMs": 2200,
                "dDurationMs": 1800,
                "segs": [{"utf8": "今日のニュースです"}],
            },
            {"tStartMs": 4000, "dDurationMs": 500, "segs": [{"utf8": "\n"}]},   # whitespace only
        ],
    })


class SubtitleParsingTests(unittest.TestCase):
    def test_formats_are_identified_by_content_not_filename(self) -> None:
        self.assertEqual(sniff_subtitle_format(AUTO_VTT), "vtt")
        self.assertEqual(sniff_subtitle_format(MANUAL_SRT), "srt")
        self.assertEqual(sniff_subtitle_format(json3_fixture()), "json3")
        self.assertEqual(sniff_subtitle_format("\ufeffWEBVTT\n\n"), "vtt")
        with self.assertRaises(MediaSourceError):
            sniff_subtitle_format("this is just prose")

    def test_crlf_line_endings_do_not_glue_a_stray_return_to_the_text(self) -> None:
        segments = parse_subtitles(MANUAL_SRT)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].text, "おはようございます。")
        self.assertNotIn("\r", segments[1].text)
        self.assertAlmostEqual(segments[1].start, 3.5)
        self.assertAlmostEqual(segments[1].end, 7.0)

    def test_a_bom_does_not_break_the_first_cue(self) -> None:
        segments = parse_subtitles("\ufeff" + MANUAL_SRT)
        self.assertEqual(len(segments), 2)

    def test_vtt_notes_and_cue_settings_are_not_mistaken_for_text(self) -> None:
        segments = parse_subtitles(AUTO_VTT)
        self.assertEqual(len(segments), 5)
        self.assertNotIn("align:start", " ".join(s.text for s in segments))
        self.assertNotIn("must be skipped", " ".join(s.text for s in segments))

    def test_short_vtt_timecodes_without_an_hour_field_are_accepted(self) -> None:
        segments = parse_subtitles("WEBVTT\n\n01:02.500 --> 01:04.000\nhello\n")
        self.assertAlmostEqual(segments[0].start, 62.5)

    def test_a_one_digit_fraction_means_tenths_not_thousandths(self) -> None:
        segments = parse_subtitles("WEBVTT\n\n00:00:01.5 --> 00:00:03.0\nhi\n")
        self.assertAlmostEqual(segments[0].start, 1.5)

    def test_json3_window_and_append_records_are_not_speech(self) -> None:
        segments = parse_subtitles(json3_fixture())
        self.assertEqual([s.text for s in segments], ["今日のニュース", "今日のニュースです"])
        self.assertAlmostEqual(segments[0].start, 1.0)
        self.assertAlmostEqual(segments[0].end, 2.2)


class CleaningTests(unittest.TestCase):
    def test_rolling_window_auto_captions_collapse_to_one_sentence_each(self) -> None:
        # Without this, the course reads: "今日のニュース" / "今日のニュースです" /
        # "ニュースです。次は天気です" — every line repeating the previous one.
        cleaned = clean_segments(parse_subtitles(AUTO_VTT), language="ja")
        self.assertEqual([s.text for s in cleaned], ["今日のニュースです", "。次は天気です", "はい"])

    def test_a_growing_cue_keeps_the_earlier_start_time(self) -> None:
        cleaned = clean_segments(parse_subtitles(AUTO_VTT), language="ja")
        # The utterance began at 1.0s even though its final text only appeared at 2.2s.
        self.assertAlmostEqual(cleaned[0].start, 1.0)

    def test_noise_labels_are_removed_and_the_empty_cue_disappears(self) -> None:
        cleaned = clean_segments(parse_subtitles(AUTO_VTT), language="ja")
        self.assertNotIn("音楽", " ".join(s.text for s in cleaned))

    def test_a_manual_track_is_never_subjected_to_the_rolling_window_collapse(self) -> None:
        # A real speaker repeating themselves is ordinary language, not an artifact.
        repeated = [
            Segment(0.0, 2.0, "はい、そうですね"),
            Segment(2.0, 4.0, "そうですね、確かに"),
        ]
        collapsed = clean_segments(repeated, language="ja", rolling_window=True)
        preserved = clean_segments(repeated, language="ja", rolling_window=False)
        self.assertEqual([s.text for s in collapsed], ["はい、そうですね", "、確かに"])
        self.assertEqual([s.text for s in preserved], ["はい、そうですね", "そうですね、確かに"])

    def test_a_seam_trim_never_empties_a_cue(self) -> None:
        identical = [Segment(0.0, 2.0, "ありがとうございます"), Segment(2.0, 4.0, "ありがとうございます")]
        cleaned = clean_segments(identical, language="ja")
        self.assertEqual([s.text for s in cleaned], ["ありがとうございます"])

    def test_a_gap_between_cues_protects_a_genuine_repetition(self) -> None:
        spaced = [Segment(0.0, 2.0, "もう一度"), Segment(10.0, 12.0, "もう一度お願いします")]
        cleaned = clean_segments(spaced, language="ja")
        self.assertEqual([s.text for s in cleaned], ["もう一度", "もう一度お願いします"])

    def test_karaoke_markup_and_entities_are_stripped(self) -> None:
        self.assertEqual(
            normalize_cue_text("今日の<00:00:01.500><c>ニュース</c>&amp;天気", language="ja"),
            "今日のニュース&天気",
        )

    def test_japanese_text_never_gains_recogniser_spaces(self) -> None:
        # Auto-captions split at recogniser tokens; the grader compares against what
        # a writer would actually type, which has no such spaces.
        self.assertEqual(normalize_cue_text("今日 の ニュース", language="ja"), "今日のニュース")

    def test_latin_text_keeps_its_word_spacing(self) -> None:
        self.assertEqual(
            normalize_cue_text("  good   morning\neveryone ", language="en"),
            "good morning everyone",
        )

    def test_speaker_tags_are_removed(self) -> None:
        self.assertEqual(normalize_cue_text("- SPEAKER: hello there", language="en"), "hello there")

    def test_an_overlapping_cue_is_clamped_forward(self) -> None:
        overlapping = [Segment(0.0, 3.0, "いち"), Segment(2.0, 5.0, "に")]
        cleaned = clean_segments(overlapping, language="ja")
        self.assertAlmostEqual(cleaned[1].start, 3.0)
        self.assertGreater(cleaned[1].end, cleaned[1].start)

    def test_a_very_short_cue_is_extended_but_never_into_the_next_one(self) -> None:
        tight = [Segment(0.0, 0.08, "はい"), Segment(0.20, 2.0, "そうです")]
        cleaned = clean_segments(tight, language="ja", min_duration=0.35)
        self.assertLessEqual(cleaned[0].end, cleaned[1].start)
        self.assertGreater(cleaned[0].end, cleaned[0].start)

    def test_a_clip_window_keeps_only_the_overlapping_segments(self) -> None:
        wide = [Segment(0.0, 5.0, "いち"), Segment(30.0, 35.0, "に"), Segment(90.0, 95.0, "さん")]
        cleaned = clean_segments(wide, language="ja", clip=(20.0, 60.0))
        self.assertEqual([s.text for s in cleaned], ["に"])

    def test_clip_filtering_does_not_shift_times_onto_a_clip_relative_axis(self) -> None:
        # Sentence times stay absolute on the video timeline; the player seeks the
        # real video, not a virtual clip.
        cleaned = clean_segments([Segment(30.0, 35.0, "に")], language="ja", clip=(20.0, 60.0))
        self.assertAlmostEqual(cleaned[0].start, 30.0)

    def test_segments_become_manifest_sentences_with_the_source_language_field(self) -> None:
        sentences = segments_to_sentences([Segment(1.0, 2.0, "こんにちは")], "ja")
        self.assertEqual(sentences[0]["sourceText"], "こんにちは")
        self.assertEqual(sentences[0]["startTime"], 1.0)
        self.assertEqual(sentences[0]["translationText"], "")


# --------------------------------------------------------------------------
# The yt-dlp seam, driven against a stub executable
# --------------------------------------------------------------------------

STUB = r'''
"""A stand-in for yt-dlp. Reads a plan from YTDLP_STUB_PLAN and obeys the argv."""
import json
import os
import sys

argv = sys.argv[1:]
plan = json.loads(os.environ.get("YTDLP_STUB_PLAN") or "{}")

if plan.get("fail"):
    sys.stderr.write("ERROR: stub was told to fail\n")
    raise SystemExit(1)

def flag_value(name):
    return argv[argv.index(name) + 1] if name in argv else ""

if "--dump-single-json" in argv:
    sys.stdout.write(json.dumps(plan.get("info", {})))
    raise SystemExit(0)

paths = flag_value("--paths")

if "--extract-audio" in argv:
    if plan.get("noAudio"):
        raise SystemExit(0)
    open(os.path.join(paths, "audio.mp3"), "wb").write(b"\x00" * 16)
    open(os.path.join(paths, "audio.mp3.part"), "wb").write(b"\x00")
    raise SystemExit(0)

kind = "manual" if "--write-subs" in argv else "auto"
tracks = plan.get(kind) or {}
if not tracks:
    sys.stderr.write("ERROR: no subtitles of that kind\n")
    raise SystemExit(1)
for name, body in tracks.items():
    with open(os.path.join(paths, name), "w", encoding="utf-8") as handle:
        handle.write(body)
raise SystemExit(0)
'''


class StubbedYtdlpTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = TemporaryDirectory(prefix="media-sources-test-")
        self.root = Path(self._temp.name)
        self.stub = self.root / "ytdlp_stub.py"
        self.stub.write_text(STUB, encoding="utf-8")
        self.work = self.root / "work"
        self.addCleanup(self._temp.cleanup)

    def plan(self, payload: dict) -> None:
        import os
        os.environ["YTDLP_STUB_PLAN"] = json.dumps(payload)
        self.addCleanup(os.environ.pop, "YTDLP_STUB_PLAN", None)

    def test_probe_reduces_yt_dlp_json_to_what_the_manifest_needs(self) -> None:
        self.plan({"info": {
            "title": "NHK ニュース",
            "uploader": "NHK",
            "duration": 612.5,
            "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "extractor_key": "Youtube",
            "subtitles": {"ja": [{}]},
            "automatic_captions": {"ja": [{}], "en": [{}]},
        }})
        info = probe_media(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ", ytdlp=str(self.stub)
        )
        self.assertEqual(info["title"], "NHK ニュース")
        self.assertAlmostEqual(info["durationSec"], 612.5)
        self.assertIn({"language": "ja", "kind": "manual"}, info["subtitles"])
        self.assertIn({"language": "en", "kind": "auto"}, info["subtitles"])

    def test_a_manual_track_wins_over_an_auto_track(self) -> None:
        self.plan({
            "manual": {"vid.ja.vtt": "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n人工字幕\n"},
            "auto": {"vid.ja.vtt": "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n自動字幕\n"},
        })
        track = fetch_subtitles(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=["ja"], work_dir=self.work, ytdlp=str(self.stub),
        )
        self.assertIsNotNone(track)
        self.assertEqual(track.kind, "manual")
        self.assertIn("人工字幕", track.text)

    def test_auto_captions_are_used_when_there_is_no_manual_track(self) -> None:
        self.plan({"auto": {"vid.ja.json3": json3_fixture()}})
        track = fetch_subtitles(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=["ja"], work_dir=self.work, ytdlp=str(self.stub),
        )
        self.assertEqual((track.kind, track.format, track.language), ("auto", "json3", "ja"))

    def test_the_requested_language_order_decides_which_track_is_taken(self) -> None:
        self.plan({"manual": {
            "vid.en.vtt": "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nenglish\n",
            "vid.ja.vtt": "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n日本語\n",
        }})
        first = fetch_subtitles(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=["ja", "en"], work_dir=self.work, ytdlp=str(self.stub),
        )
        second = fetch_subtitles(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=["en", "ja"], work_dir=self.work, ytdlp=str(self.stub),
        )
        self.assertEqual(first.language, "ja")
        self.assertEqual(second.language, "en")

    def test_a_regional_track_satisfies_a_bare_language_request(self) -> None:
        self.plan({"manual": {"vid.ja-JP.vtt": "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n日本語\n"}})
        track = fetch_subtitles(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=["ja"], work_dir=self.work, ytdlp=str(self.stub),
        )
        self.assertEqual(track.language, "ja-JP")

    def test_a_video_with_no_captions_returns_none_rather_than_raising(self) -> None:
        # This is the normal path into the ASR fallback, not an error.
        self.plan({})
        track = fetch_subtitles(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            languages=["ja"], work_dir=self.work, ytdlp=str(self.stub),
        )
        self.assertIsNone(track)

    def test_temporary_audio_deletes_the_file_and_its_part_leftovers(self) -> None:
        self.plan({})
        seen: list[Path] = []
        with temporary_audio(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            work_dir=self.work, ytdlp=str(self.stub),
        ) as audio:
            seen.append(audio)
            self.assertTrue(audio.is_file())
        self.assertFalse(seen[0].exists())
        self.assertEqual(list(self.work.glob("**/*.mp3")), [])
        self.assertEqual(list(self.work.glob("**/*.part")), [])

    def test_temporary_audio_deletes_the_file_even_when_the_body_raises(self) -> None:
        # The copyright promise has to survive the failure paths, not just the happy one.
        self.plan({})
        captured: list[Path] = []
        with self.assertRaises(RuntimeError):
            with temporary_audio(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                work_dir=self.work, ytdlp=str(self.stub),
            ) as audio:
                captured.append(audio)
                raise RuntimeError("transcription blew up")
        self.assertFalse(captured[0].exists())
        self.assertEqual(list(self.work.glob("**/*.mp3")), [])

    def test_a_failing_yt_dlp_surfaces_its_own_stderr(self) -> None:
        self.plan({"fail": True})
        with self.assertRaises(MediaSourceError) as caught:
            probe_media("https://www.youtube.com/watch?v=dQw4w9WgXcQ", ytdlp=str(self.stub))
        self.assertIn("stub was told to fail", str(caught.exception))

    def test_a_url_is_validated_before_it_ever_reaches_the_subprocess(self) -> None:
        self.plan({"info": {}})
        with self.assertRaises(MediaSourceError):
            probe_media("--exec=calc.exe", ytdlp=str(self.stub))


class YtdlpResolutionTests(unittest.TestCase):
    def test_a_missing_yt_dlp_names_the_command_that_fixes_it(self) -> None:
        with self.assertRaises(MediaSourceError) as caught:
            resolve_ytdlp("C:/definitely/not/here/yt-dlp.exe")
        self.assertIn("yt-dlp", str(caught.exception))

    def test_availability_is_reported_without_raising(self) -> None:
        self.assertIsInstance(ytdlp_available("C:/definitely/not/here/yt-dlp.exe"), bool)
        self.assertFalse(ytdlp_available("C:/definitely/not/here/yt-dlp.exe"))


if __name__ == "__main__":
    unittest.main()
