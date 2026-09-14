"""A course may name its media exactly once, and an online video is never ours.

Two properties are load-bearing here:

* Adding online-video courses must not have changed local ones. The audit and the
  identifier derivation are shared code, and a course that has already been studied
  cannot be allowed to acquire a new courseId — that would orphan every note,
  vocabulary entry and progress row keyed to it.
* A remote course is not redistributable. The manifest says so, the audit refuses a
  manifest that claims otherwise, and neither statement is advisory.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from bundle_quality import audit_manifest
from course_schema import (
    is_remote_media_manifest,
    media_kind,
    normalize_remote_media,
    prepare_course_manifest,
)
REAL_COURSE = PROJECT_DIR / "courses" / "2010-12-N2" / "manifest.json"


def remote_manifest(**overrides) -> dict:
    manifest = {
        "schemaVersion": 1,
        "title": "NHK ニュース 2026-08-31",
        "sourceLanguage": "ja",
        "media": {
            "kind": "remote",
            "provider": "youtube",
            "control": "full",
            "videoId": "dQw4w9WgXcQ",
            "pageUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "embedUrl": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
            "durationSec": 612.0,
            "uploader": "NHK",
            "attribution": {
                "sourceName": "YouTube",
                "rightsHolder": "NHK",
                "retrievedAt": "2026-08-31",
                "redistributable": False,
                "notes": "",
            },
        },
        "sentences": [
            {
                "startTime": 1.0,
                "endTime": 3.5,
                "sourceText": "おはようございます。",
                "translationText": "早上好。",
                "explanationText": "朝の挨拶です。",
            },
            {
                "startTime": 3.5,
                "endTime": 7.0,
                "sourceText": "今日のニュースをお伝えします。",
                "translationText": "为您播报今天的新闻。",
                "explanationText": "「お伝えします」は丁寧な言い方です。",
            },
        ],
    }
    manifest.update(overrides)
    return manifest


class MediaDeclarationTests(unittest.TestCase):
    def test_a_remote_manifest_is_recognised_and_prepared(self) -> None:
        prepared = prepare_course_manifest(remote_manifest())
        self.assertTrue(is_remote_media_manifest(prepared))
        self.assertEqual(media_kind(prepared), "remote")
        self.assertNotIn("audio", prepared)
        self.assertTrue(prepared["courseId"].startswith("c_"))

    def test_declaring_both_audio_and_media_is_refused(self) -> None:
        # Not an ambiguity to resolve by preferring one: it is two different courses
        # in a single file.
        with self.assertRaises(ValueError):
            prepare_course_manifest(remote_manifest(audio="audio.mp3"))

    def test_declaring_neither_is_refused(self) -> None:
        manifest = remote_manifest()
        del manifest["media"]
        with self.assertRaises(ValueError):
            prepare_course_manifest(manifest)

    def test_preparation_is_idempotent_and_keeps_the_course_identity(self) -> None:
        # A rebuilt course must keep its id, or the learner's notes and progress
        # silently detach from it.
        once = prepare_course_manifest(remote_manifest())
        twice = prepare_course_manifest(copy.deepcopy(once))
        self.assertEqual(once["courseId"], twice["courseId"])
        self.assertEqual(once["contentRevision"], twice["contentRevision"])
        self.assertEqual(once["media"], twice["media"])

    def test_the_same_video_always_gets_the_same_course_id(self) -> None:
        first = prepare_course_manifest(remote_manifest())
        # A different title and different sentence text is still the same video.
        other = remote_manifest(title="別のタイトル")
        other["sentences"][0]["sourceText"] = "ぜんぜん違う文です。"
        second = prepare_course_manifest(other)
        self.assertEqual(first["courseId"], second["courseId"])

    def test_a_different_clip_window_is_a_different_course(self) -> None:
        whole = prepare_course_manifest(remote_manifest())
        clipped = remote_manifest()
        clipped["media"]["clip"] = {"startTime": 30.0, "endTime": 90.0}
        self.assertNotEqual(whole["courseId"], prepare_course_manifest(clipped)["courseId"])

    def test_an_existing_course_id_is_never_reassigned(self) -> None:
        manifest = remote_manifest(courseId="c_0123456789abcdef01234567")
        self.assertEqual(prepare_course_manifest(manifest)["courseId"], "c_0123456789abcdef01234567")


class MediaNormalizationTests(unittest.TestCase):
    def test_redistributable_is_forced_false_however_the_manifest_asks(self) -> None:
        media = remote_manifest()["media"]
        media["attribution"]["redistributable"] = True
        self.assertIs(normalize_remote_media(media)["attribution"]["redistributable"], False)

    def test_an_unknown_provider_or_control_is_refused(self) -> None:
        for field, value in (("provider", "vevo"), ("control", "telepathy")):
            media = remote_manifest()["media"]
            media[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_remote_media(media)

    def test_a_framed_tier_without_an_embed_url_is_refused(self) -> None:
        media = remote_manifest()["media"]
        media["embedUrl"] = ""
        with self.assertRaises(ValueError):
            normalize_remote_media(media)

    def test_an_external_tier_may_have_no_embed_url(self) -> None:
        media = remote_manifest()["media"]
        media.update({"provider": "generic", "control": "external", "videoId": "", "embedUrl": ""})
        self.assertEqual(normalize_remote_media(media)["control"], "external")

    def test_a_non_web_page_url_is_refused(self) -> None:
        media = remote_manifest()["media"]
        media["pageUrl"] = "file:///C:/secrets.txt"
        with self.assertRaises(ValueError):
            normalize_remote_media(media)


class RemoteAuditTests(unittest.TestCase):
    def audit(self, manifest: dict) -> dict:
        return audit_manifest(manifest, require_enrichment=False)

    def codes(self, manifest: dict) -> set[str]:
        return {issue["code"] for issue in self.audit(manifest)["issues"]}

    def test_a_healthy_remote_course_raises_no_media_errors(self) -> None:
        report = self.audit(prepare_course_manifest(remote_manifest()))
        media_errors = [
            issue for issue in report["issues"]
            if issue["severity"] == "error" and issue["code"].startswith(("manifest.media", "manifest.audio"))
        ]
        self.assertEqual(media_errors, [])

    def test_the_missing_audio_error_no_longer_fires_for_a_remote_course(self) -> None:
        # This is the regression that would make every online-video course refuse
        # to open: the audit used to demand an audio filename unconditionally.
        self.assertNotIn("manifest.audio_missing", self.codes(remote_manifest()))

    def test_each_new_issue_code_fires_on_a_manifest_that_earns_it(self) -> None:
        cases = {
            "manifest.media_and_audio_conflict": remote_manifest(audio="audio.mp3"),
            "manifest.media_provider_unknown": remote_manifest(),
            "manifest.media_page_url_missing": remote_manifest(),
            "manifest.media_embed_missing": remote_manifest(),
            "manifest.media_clip_invalid": remote_manifest(),
            "manifest.media_redistributable_claim": remote_manifest(),
            "manifest.media_invalid": remote_manifest(),
        }
        cases["manifest.media_provider_unknown"]["media"]["provider"] = "vevo"
        cases["manifest.media_page_url_missing"]["media"]["pageUrl"] = "not a url"
        cases["manifest.media_embed_missing"]["media"]["embedUrl"] = ""
        cases["manifest.media_clip_invalid"]["media"]["clip"] = {"startTime": 90.0, "endTime": 30.0}
        cases["manifest.media_redistributable_claim"]["media"]["attribution"]["redistributable"] = True
        cases["manifest.media_invalid"]["media"] = "https://youtu.be/dQw4w9WgXcQ"

        for code, manifest in cases.items():
            with self.subTest(code=code):
                self.assertIn(code, self.codes(manifest))

    def test_a_manifest_with_neither_media_nor_audio_still_reports_audio_missing(self) -> None:
        manifest = remote_manifest()
        del manifest["media"]
        self.assertIn("manifest.audio_missing", self.codes(manifest))

    def test_a_sentence_outside_the_clip_window_is_a_warning_not_an_error(self) -> None:
        # The sentence is still playable — the course points into the whole video —
        # so refusing to open the course over it would be out of proportion.
        manifest = remote_manifest()
        manifest["media"]["clip"] = {"startTime": 100.0, "endTime": 200.0}
        report = self.audit(manifest)
        outside = [i for i in report["issues"] if i["code"] == "sentence.outside_clip"]
        self.assertEqual(len(outside), 2)
        self.assertTrue(all(issue["severity"] == "warning" for issue in outside))

    def test_a_sentence_inside_the_clip_window_is_not_flagged(self) -> None:
        manifest = remote_manifest()
        manifest["media"]["clip"] = {"startTime": 0.0, "endTime": 600.0}
        self.assertNotIn("sentence.outside_clip", self.codes(manifest))


class LocalCoursesAreUnchangedTests(unittest.TestCase):
    """The regression bar: adding remote courses changed nothing for local ones."""

    def test_a_local_manifest_still_demands_a_safe_audio_filename(self) -> None:
        base = {
            "schemaVersion": 1,
            "title": "local",
            "sourceLanguage": "ja",
            "sentences": [{"startTime": 0.0, "endTime": 1.0, "sourceText": "はい。"}],
        }
        missing = audit_manifest(dict(base, audio=""), require_enrichment=False)
        unsafe = audit_manifest(dict(base, audio="../escape.mp3"), require_enrichment=False)
        self.assertIn("manifest.audio_missing", {i["code"] for i in missing["issues"]})
        self.assertIn("manifest.audio_unsafe", {i["code"] for i in unsafe["issues"]})

    @unittest.skipUnless(REAL_COURSE.is_file(), "the shipped course is not present")
    def test_the_shipped_course_prepares_byte_for_byte_as_before(self) -> None:
        original = json.loads(REAL_COURSE.read_text(encoding="utf-8-sig"))
        prepared = prepare_course_manifest(copy.deepcopy(original))
        self.assertEqual(prepared["courseId"], original.get("courseId", prepared["courseId"]))
        self.assertEqual(prepared["contentRevision"], original.get("contentRevision", prepared["contentRevision"]))
        self.assertEqual(
            [s["id"] for s in prepared["sentences"]],
            [s["id"] for s in original["sentences"]],
        )
        self.assertEqual(media_kind(prepared), "audio")

    @unittest.skipUnless(REAL_COURSE.is_file(), "the shipped course is not present")
    def test_preparing_the_shipped_course_is_a_fixed_point(self) -> None:
        original = json.loads(REAL_COURSE.read_text(encoding="utf-8-sig"))
        once = prepare_course_manifest(copy.deepcopy(original))
        twice = prepare_course_manifest(copy.deepcopy(once))
        self.assertEqual(json.dumps(once, sort_keys=True), json.dumps(twice, sort_keys=True))


class ReleaseGateTests(unittest.TestCase):
    """The legally important half: these courses must never look releasable."""

    def test_a_rights_ledger_cannot_be_opened_for_media_we_do_not_hold(self) -> None:
        from content_license import RemoteMediaNotLicensable, create_license_ledger

        # A ledger asserts what we may redistribute. Writing one for someone else's
        # video would produce a document that reads as a rights claim over it.
        with self.assertRaises(RemoteMediaNotLicensable):
            create_license_ledger(prepare_course_manifest(remote_manifest()))

    def test_a_local_course_can_still_open_a_rights_ledger(self) -> None:
        from content_license import create_license_ledger

        local = {
            "schemaVersion": 1,
            "title": "local",
            "audio": "audio.mp3",
            "sourceLanguage": "ja",
            "sentences": [{"startTime": 0.0, "endTime": 1.0, "sourceText": "はい。"}],
        }
        prepared = prepare_course_manifest(local, audio_sha256="d" * 64)
        ledger = create_license_ledger(prepared)
        self.assertEqual(ledger["type"], "commercial-content-rights-ledger")

    def test_release_readiness_blocks_an_online_video_course(self) -> None:
        import tempfile
        from release_readiness import build_report

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_report(
                prepare_course_manifest(remote_manifest()),
                manifest_path=root / "manifest.json",
                audio_path=root / "audio.mp3",   # deliberately absent
                web_dir=root,
                project_dir=root,
                approvals=None,
                artifact_path=None,
            )
        self.assertEqual(report["status"], "blocked")
        codes = {check["name"] for check in report["checks"]}
        self.assertIn("redistributable_media", codes)
        # It must say why, not fail obscurely on the missing audio file.
        blocker = next(c for c in report["checks"] if c["name"] == "redistributable_media")
        self.assertIn("不可再分发", blocker["detail"])


class CoursePickerTests(unittest.TestCase):
    """The picker has to be able to tell the two kinds of course apart."""

    def write(self, directory: Path, manifest: dict) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )

    def test_a_summary_reports_the_media_kind_and_its_control_tier(self) -> None:
        import tempfile
        from local_backend import CourseStore

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "video", prepare_course_manifest(remote_manifest()))
            local = {
                "schemaVersion": 1,
                "title": "local",
                "audio": "audio.mp3",
                "sourceLanguage": "ja",
                "sentences": [{"startTime": 0.0, "endTime": 1.0, "sourceText": "はい。"}],
            }
            self.write(root / "audio-course", prepare_course_manifest(local))
            rows = {row["id"]: row for row in CourseStore(root).list_courses()}

        self.assertEqual(rows["video"]["mediaKind"], "remote")
        self.assertEqual(rows["video"]["mediaProvider"], "youtube")
        self.assertEqual(rows["video"]["mediaControl"], "full")
        self.assertTrue(rows["video"]["pageUrl"].startswith("https://"))
        # Every existing key survives, and a local course is untouched.
        self.assertEqual(rows["audio-course"]["mediaKind"], "audio")
        self.assertEqual(rows["audio-course"]["audio"], "audio.mp3")
        self.assertEqual(rows["audio-course"]["mediaProvider"], "")

    def test_a_summary_exposes_quality_review_level_and_practice_count(self) -> None:
        import tempfile
        from local_backend import CourseStore

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            course = root / "2021-12-N2"
            manifest = prepare_course_manifest({
                "schemaVersion": 1,
                "title": "2021 年 12 月 N2",
                "audio": "audio.mp3",
                "sourceLanguage": "ja",
                "review": {
                    "humanListening": "approved",
                    "commercialRights": "verified",
                    "browserAcceptance": "complete",
                },
                "sentences": [
                    {"startTime": 0, "endTime": 1, "sourceText": "はい。", "practiceEligible": True},
                    {"startTime": 1, "endTime": 2, "sourceText": "次。", "practiceEligible": False},
                ],
            })
            self.write(course, manifest)
            (course / "quality-report.json").write_text(json.dumps({
                "status": "passed", "summary": {"errors": 0, "warnings": 0},
            }), encoding="utf-8")
            row = CourseStore(root).list_courses()[0]

        self.assertEqual(row["level"], "N2")
        self.assertEqual(row["practiceSentenceCount"], 1)
        self.assertEqual(row["quality"]["status"], "passed")
        self.assertEqual(row["review"]["commercialRights"], "verified")


class RemoteBundleInstallTests(unittest.TestCase):
    def test_a_bundle_with_no_media_member_installs(self) -> None:
        import tempfile
        import zipfile
        from install_course import install_bundle, list_courses

        manifest = prepare_course_manifest(remote_manifest())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "course.zip"
            with zipfile.ZipFile(bundle, "w") as archive:
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
            destination = install_bundle(bundle, courses_dir=root / "courses", course_name="video")
            self.assertTrue((destination / "manifest.json").is_file())
            # Nothing else: the media was never in the bundle and must not be invented.
            self.assertEqual(
                sorted(p.name for p in destination.iterdir()),
                ["install-source.json", "manifest.json"],
            )
            rows = list_courses(root / "courses")
        self.assertEqual(rows[0]["mediaKind"], "remote")
        self.assertEqual(rows[0]["mediaProvider"], "youtube")


if __name__ == "__main__":
    unittest.main()
