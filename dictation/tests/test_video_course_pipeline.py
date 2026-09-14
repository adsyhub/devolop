"""End-to-end online-video course builds, with no network and no yt-dlp installed.

The whole feature rests on one promise — the video is never downloaded and any
temporary audio does not survive the build — so the tests that check the promise on
the *failure* paths matter as much as the happy-path ones.

Everything is driven through a stub yt-dlp executable and a text provider that is a
local script, which is enough to exercise every real stage: recognise the URL, take
the captions, clean them, merge sentences, batch and merge enrichment, stabilise ids,
audit, and write courses/<name>/manifest.json.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

import build_video_course  # noqa: E402
from bundle_quality import audit_manifest  # noqa: E402
from content_patch import sentences_digest  # noqa: E402

VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

AUTO_VTT = """WEBVTT
Kind: captions
Language: ja

00:00:01.000 --> 00:00:02.200
今日の

00:00:02.200 --> 00:00:05.000
今日のニュースをお伝えします

00:00:05.000 --> 00:00:09.000
東京は朝から雨が降っています

00:00:09.000 --> 00:00:13.000
気温は十五度まで下がる見込みです
"""

MANUAL_SRT = """1
00:00:01,000 --> 00:00:04,000
おはようございます。

2
00:00:04,000 --> 00:00:08,000
今日はいい天気ですね。

3
00:00:08,000 --> 00:00:12,000
明日の会議は十時から始まります。
"""

# Impersonates yt-dlp. The plan lives in a JSON file so each test can rewrite it
# without touching the environment of a parallel test.
STUB = r'''
import json, os, sys
argv = sys.argv[1:]
plan = json.loads(open(os.environ["YTDLP_STUB_PLAN"], encoding="utf-8").read())

def value(flag):
    return argv[argv.index(flag) + 1] if flag in argv else ""

if "--dump-single-json" in argv:
    sys.stdout.write(json.dumps(plan.get("info", {})))
    raise SystemExit(0)

paths = value("--paths")

if "--extract-audio" in argv:
    open(os.path.join(paths, "audio.mp3"), "wb").write(b"ID3" + bytes(2048))
    raise SystemExit(0)

kind = "manual" if "--write-subs" in argv else "auto"
tracks = plan.get(kind) or {}
if not tracks:
    sys.stderr.write("ERROR: no subtitles\n")
    raise SystemExit(1)
for name, body in tracks.items():
    with open(os.path.join(paths, name), "w", encoding="utf-8") as handle:
        handle.write(body)
raise SystemExit(0)
'''

# Reads the enrichment prompt on stdin and answers with plausible Chinese.
FAKE_MODEL = """
import json, sys
prompt = sys.stdin.read()
payload = json.loads(prompt[prompt.index('{\\n  "batchFile"'):])
print(json.dumps({"items": [
    {
        "index": item["index"],
        "zhTranslation": "这是一句中文译文。",
        "explanationText": "这是讲解，说明语法与听力难点。",
    }
    for item in payload["items"]
]}, ensure_ascii=False))
"""


class VideoPipelineFixture(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import opencc  # noqa: F401
        except ImportError:
            self.skipTest("opencc not installed (build pipeline tests require requirements.txt)")
        self._temp = tempfile.TemporaryDirectory(prefix="dictation-video-")
        self.root = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)

        self.stub = self.root / "ytdlp_stub.py"
        self.stub.write_text(STUB, encoding="utf-8")
        self.plan_path = self.root / "plan.json"
        self.model = self.root / "fake_model.py"
        self.model.write_text(FAKE_MODEL, encoding="utf-8")
        self.courses = self.root / "courses"
        self.work = self.root / "work"

        self.config = self.root / "providers.json"
        self.config.write_text(json.dumps({
            "schemaVersion": 1,
            "defaultTextProfile": "fake",
            "textProfiles": {
                "fake": {
                    "kind": "cli",
                    "command": [sys.executable, str(self.model)],
                    "batchSize": 8,
                    "timeout": 120,
                    "retries": 1,
                    "sleep": 0,
                },
            },
            "asrProfiles": {},
        }, ensure_ascii=False), encoding="utf-8")

        import os
        os.environ["YTDLP_STUB_PLAN"] = str(self.plan_path)
        self.addCleanup(os.environ.pop, "YTDLP_STUB_PLAN", None)
        self.plan({"auto": {"vid.ja.vtt": AUTO_VTT}})

    def plan(self, payload: dict) -> None:
        self.plan_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def build(self, *extra: str, expect_failure: bool = False) -> str:
        argv = [
            "--url", VIDEO_URL,
            "--name", "video-course",
            "--courses-dir", str(self.courses),
            "--work-dir", str(self.work),
            "--config", str(self.config),
            "--ytdlp", str(self.stub),
            "--language", "ja",
            *extra,
        ]
        if "--no-enrich" not in extra and "--profile" not in extra:
            argv += ["--profile", "fake"]
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                build_video_course.main(argv)
        except SystemExit as exc:
            code = exc.code
            failed = not (code is None or code == 0)
            if failed and not expect_failure:
                raise AssertionError(f"build failed unexpectedly:\n{buffer.getvalue()}\n{exc}") from exc
            if failed:
                return f"{buffer.getvalue()}\n{exc}"
            if expect_failure:
                raise AssertionError(f"build was expected to fail but succeeded:\n{buffer.getvalue()}")
            return buffer.getvalue()
        if expect_failure:
            raise AssertionError(f"build was expected to fail but succeeded:\n{buffer.getvalue()}")
        return buffer.getvalue()

    def manifest(self, name: str = "video-course") -> dict:
        path = self.courses / name / "manifest.json"
        self.assertTrue(path.is_file(), f"no manifest at {path}")
        return json.loads(path.read_text(encoding="utf-8-sig"))


class SubtitlePathTests(VideoPipelineFixture):
    def test_a_course_is_built_from_site_captions_with_no_local_media(self) -> None:
        self.build()
        manifest = self.manifest()
        self.assertNotIn("audio", manifest)
        self.assertEqual(manifest["media"]["provider"], "youtube")
        self.assertEqual(manifest["media"]["control"], "full")
        self.assertEqual(manifest["media"]["pageUrl"], VIDEO_URL)
        self.assertTrue(manifest["sentences"])
        self.assertEqual(manifest["buildMetadata"]["transcriptSource"], "site-subtitles")

    def test_the_built_course_passes_its_own_audit(self) -> None:
        self.build()
        report = audit_manifest(self.manifest(), require_enrichment=True)
        self.assertEqual(report["summary"]["errors"], 0, report["issues"])

    def test_no_media_file_is_ever_written_into_the_course_folder(self) -> None:
        self.build()
        files = sorted(p.name for p in (self.courses / "video-course").iterdir())
        self.assertEqual(files, ["install-source.json", "manifest.json"])

    def test_sentence_times_are_absolute_on_the_video_timeline(self) -> None:
        self.build()
        starts = [s["startTime"] for s in self.manifest()["sentences"]]
        self.assertEqual(starts, sorted(starts))
        self.assertGreaterEqual(starts[0], 1.0)

    def test_rolling_window_auto_captions_do_not_repeat_across_sentences(self) -> None:
        # Without the collapse, the first two sentences would both begin "今日の".
        self.build()
        texts = [s["sourceText"] for s in self.manifest()["sentences"]]
        self.assertNotIn("今日の", texts)
        self.assertTrue(any("ニュース" in text for text in texts))

    def test_a_manual_track_is_preferred_over_the_auto_one(self) -> None:
        self.plan({"manual": {"vid.ja.srt": MANUAL_SRT}, "auto": {"vid.ja.vtt": AUTO_VTT}})
        self.build()
        manifest = self.manifest()
        self.assertEqual(manifest["buildMetadata"]["subtitle"]["kind"], "manual")
        self.assertIn("おはようございます。", [s["sourceText"] for s in manifest["sentences"]])

    def test_enrichment_fills_translation_and_explanation(self) -> None:
        self.build()
        for sentence in self.manifest()["sentences"]:
            self.assertTrue(str(sentence.get("zhTranslation") or "").strip())
            self.assertTrue(str(sentence.get("explanationText") or "").strip())

    def test_the_course_records_that_it_is_not_redistributable(self) -> None:
        self.build()
        manifest = self.manifest()
        self.assertIs(manifest["media"]["attribution"]["redistributable"], False)
        record = json.loads((self.courses / "video-course" / "install-source.json").read_text(encoding="utf-8"))
        self.assertIs(record["redistributable"], False)
        self.assertEqual(record["kind"], "online-video")


class ClipAndIdentityTests(VideoPipelineFixture):
    def test_a_clip_window_drops_the_sentences_that_fall_outside_it(self) -> None:
        # The captions run 1-5s, 5-9s and 9-13s. A window starting at 6s excludes the
        # first outright and keeps the two that overlap it.
        self.build("--clip", "6", "20")
        manifest = self.manifest()
        self.assertEqual(manifest["media"]["clip"], {"startTime": 6.0, "endTime": 20.0})
        starts = [s["startTime"] for s in manifest["sentences"]]
        self.assertTrue(all(start >= 5.0 for start in starts), starts)
        self.assertNotIn(1.0, starts)

    def test_a_clipped_course_keeps_absolute_video_times(self) -> None:
        # Rebasing onto the clip is the bug that makes every seek in a clipped course
        # land clip.startTime seconds away from the sentence.
        self.build("--clip", "4", "20")
        starts = [s["startTime"] for s in self.manifest()["sentences"]]
        # The 5s caption is still at 5s, not at 1s.
        self.assertIn(5.0, starts)

    def test_a_sentence_overlapping_the_window_edge_is_kept(self) -> None:
        self.build("--clip", "4", "20")
        starts = [s["startTime"] for s in self.manifest()["sentences"]]
        self.assertIn(1.0, starts)

    def test_rebuilding_the_same_video_keeps_the_course_identity(self) -> None:
        # Progress, notes and vocabulary are keyed by courseId and sentence id. A
        # rebuild that changed them would silently orphan the learner's work.
        self.build()
        first = self.manifest()
        self.build("--force")
        second = self.manifest()
        self.assertEqual(first["courseId"], second["courseId"])
        self.assertEqual(first["contentRevision"], second["contentRevision"])
        self.assertEqual(
            [s["id"] for s in first["sentences"]],
            [s["id"] for s in second["sentences"]],
        )

    def test_an_existing_course_folder_is_not_overwritten_without_force(self) -> None:
        self.build()
        output = self.build(expect_failure=True)
        self.assertIn("--force", output)


class TranscriptSourceTests(VideoPipelineFixture):
    def test_a_local_subtitle_file_can_be_imported_with_a_page_url(self) -> None:
        subtitle = self.root / "talk.srt"
        subtitle.write_text(MANUAL_SRT, encoding="utf-8")
        self.build("--transcript", "file", "--subtitles", str(subtitle), "--page-url", VIDEO_URL)
        manifest = self.manifest()
        self.assertEqual(manifest["buildMetadata"]["transcriptSource"], "imported-file")
        self.assertIn("おはようございます。", [s["sourceText"] for s in manifest["sentences"]])

    def test_subs_only_fails_clearly_when_the_site_has_no_captions(self) -> None:
        self.plan({})
        output = self.build("--transcript", "subs", expect_failure=True)
        self.assertIn("字幕", output)

    def test_no_audio_fetch_refuses_to_download_instead_of_doing_it_quietly(self) -> None:
        # The copyright promise: without captions and without permission, the build
        # stops rather than reaching for the audio.
        self.plan({})
        output = self.build("--no-audio-fetch", expect_failure=True)
        self.assertIn("no-audio-fetch", output.lower().replace("_", "-"))
        self.assertFalse((self.courses / "video-course").exists())

    def test_verified_compares_auto_captions_with_local_asr_and_records_evidence(self) -> None:
        asr_segments = [
            build_video_course.Segment(1.0, 4.0, "国債を買います。"),
            build_video_course.Segment(4.0, 8.0, "金利が上がりました。"),
            build_video_course.Segment(8.0, 12.0, "生活への影響を説明します。"),
        ]
        asr_meta = {
            "language": "ja",
            "transcriptSource": "asr",
            "asr": {"kind": "test", "config": {"model": "independent"}},
        }
        with mock.patch.object(
            build_video_course,
            "from_local_asr",
            return_value=(asr_segments, asr_meta),
        ):
            self.build("--transcript", "verified", "--no-enrich")

        manifest = self.manifest()
        verification = manifest["buildMetadata"]["verification"]
        self.assertEqual(manifest["buildMetadata"]["transcriptSource"], "asr")
        self.assertEqual(verification["mode"], "dual-source")
        self.assertEqual(verification["selected"], "asr")
        self.assertEqual(len(verification["candidates"]), 2)
        self.assertIn("textSimilarity", verification["comparison"])
        self.assertTrue((self.work / "transcript-verification.json").is_file())

    def test_verified_prefers_manual_captions_when_quality_is_tied(self) -> None:
        self.plan({"manual": {"vid.ja.srt": MANUAL_SRT}})
        asr_segments = [
            build_video_course.Segment(1.0, 4.0, "別の文章です。"),
            build_video_course.Segment(4.0, 8.0, "こちらも正常です。"),
            build_video_course.Segment(8.0, 12.0, "最後の文章です。"),
        ]
        asr_meta = {
            "language": "ja",
            "transcriptSource": "asr",
            "asr": {"kind": "test", "config": {"model": "independent"}},
        }
        with mock.patch.object(
            build_video_course,
            "from_local_asr",
            return_value=(asr_segments, asr_meta),
        ):
            self.build("--transcript", "verified", "--no-enrich")
        self.assertEqual(
            self.manifest()["buildMetadata"]["verification"]["selected"],
            "site-subtitles:manual",
        )

    def test_verified_cannot_silently_bypass_no_audio_fetch(self) -> None:
        with mock.patch.object(build_video_course, "from_local_asr") as local_asr:
            output = self.build(
                "--transcript", "verified", "--no-audio-fetch", expect_failure=True
            )
        self.assertIn("verified requires temporary audio", output)
        local_asr.assert_not_called()

    def test_an_approved_content_patch_is_applied_inside_the_build(self) -> None:
        self.build()
        source = self.manifest()
        sentence = source["sentences"][0]
        patch_path = self.root / "approved-fix.json"
        patch_path.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "sourceSentencesDigest": sentences_digest(source["sentences"]),
                    "description": "Reviewed homophone correction.",
                    "evidence": {"reviewed": True},
                    "operations": [
                        {
                            "type": "replace_range",
                            "startIndex": 0,
                            "endIndex": 0,
                            "expectedStartTime": sentence["startTime"],
                            "expectedEndTime": sentence["endTime"],
                            "items": [
                                {
                                    "startTime": sentence["startTime"],
                                    "endTime": sentence["endTime"],
                                    "jaText": "国債のニュースをお伝えします。",
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.build("--force", "--content-patch", str(patch_path))
        rebuilt = self.manifest()
        self.assertEqual(rebuilt["sentences"][0]["sourceText"], "国債のニュースをお伝えします。")
        self.assertEqual(
            rebuilt["buildMetadata"]["contentPatches"][0]["name"], "approved-fix.json"
        )

    def test_model_detected_homophones_are_written_as_review_candidates(self) -> None:
        self.build()
        manifest = self.manifest()
        manifest["sentences"][0]["explanationText"] = (
            "原文「国際」在金融语境中是误识别，应为「国債」。"
        )
        report = audit_manifest(manifest, require_enrichment=True)
        review = build_video_course.build_transcript_correction_review(manifest, report, None)
        self.assertEqual(review["candidateCount"], 1)
        self.assertEqual(review["items"][0]["suggestions"], ["国債"])


class GenericSiteTests(VideoPipelineFixture):
    def test_a_site_that_cannot_be_framed_still_produces_a_usable_course(self) -> None:
        subtitle = self.root / "talk.srt"
        subtitle.write_text(MANUAL_SRT, encoding="utf-8")
        self.build(
            "--transcript", "file",
            "--subtitles", str(subtitle),
            "--page-url", "https://www3.nhk.or.jp/news/easy/k100.html",
        )
        manifest = self.manifest()
        self.assertEqual(manifest["media"]["provider"], "generic")
        self.assertEqual(manifest["media"]["control"], "external")
        self.assertEqual(manifest["media"]["embedUrl"], "")
        self.assertEqual(audit_manifest(manifest, require_enrichment=True)["summary"]["errors"], 0)


class DryRunTests(VideoPipelineFixture):
    def test_a_dry_run_writes_nothing_and_fetches_nothing(self) -> None:
        output = self.build("--dry-run")
        self.assertIn("Dry run", output)
        self.assertFalse(self.courses.exists())

    def test_the_plan_names_the_control_tier_and_what_it_costs(self) -> None:
        output = self.build("--dry-run")
        self.assertIn("control tier", output)
        self.assertIn("full", output)


class UrlValidationTests(VideoPipelineFixture):
    def test_a_hostile_url_is_refused_before_any_subprocess_runs(self) -> None:
        for url in ("file:///C:/secrets.txt", "-x", "http://127.0.0.1:4173/v"):
            with self.subTest(url=url):
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        build_video_course.main([
                            "--url", url,
                            "--courses-dir", str(self.courses),
                            "--work-dir", str(self.work),
                            "--config", str(self.config),
                            "--ytdlp", str(self.stub),
                            "--no-enrich",
                            "--dry-run",
                        ])


class TimeParsingTests(unittest.TestCase):
    def test_clip_times_accept_seconds_mmss_and_hmmss(self) -> None:
        self.assertAlmostEqual(build_video_course.parse_time("90"), 90.0)
        self.assertAlmostEqual(build_video_course.parse_time("1:30"), 90.0)
        self.assertAlmostEqual(build_video_course.parse_time("1:01:30"), 3690.0)

    def test_a_decreasing_clip_window_is_refused(self) -> None:
        with self.assertRaises(SystemExit):
            build_video_course.parse_clip(["90", "30"])


if __name__ == "__main__":
    unittest.main()
