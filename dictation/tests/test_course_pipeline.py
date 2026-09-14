"""End-to-end course builds, with no model and no network involved.

The pipeline is driven through the two provider kinds that need neither: a
transcript imported from disk, and a text model that is a local script. That is
enough to exercise every stage a real build runs - merge, batch, validate, merge
back, normalize, stabilise ids, audit, package, install - which is exactly the
coverage the builder never had.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

import build_course  # noqa: E402
from install_course import InstallError, install_bundle, list_courses  # noqa: E402

TRANSCRIPT = """1
00:00:00,420 --> 00:00:03,700
これはテストの音声です。

2
00:00:03,900 --> 00:00:07,100
今日はいい天気ですね。

3
00:00:07,300 --> 00:00:11,000
明日の会議は十時から始まります。
"""

# Stands in for a subscription CLI: reads the prompt on stdin, prints JSON.
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


class PipelineFixture(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import opencc  # noqa: F401
        except ImportError:
            self.skipTest("opencc not installed (build pipeline tests require requirements.txt)")
        self._temp = tempfile.TemporaryDirectory(prefix="dictation-pipeline-")
        self.root = Path(self._temp.name)
        self.audio = self.root / "audio.mp3"
        self.audio.write_bytes(b"ID3" + bytes(2048))
        self.transcript = self.root / "transcript.srt"
        self.transcript.write_text(TRANSCRIPT, encoding="utf-8")
        self.model = self.root / "fake_model.py"
        self.model.write_text(FAKE_MODEL, encoding="utf-8")
        self.out = self.root / "course.zip"
        self.work = self.root / "work"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def build(self, *extra: str, expect_failure: bool = False) -> str:
        argv = [
            "--audio", str(self.audio),
            "--transcript", str(self.transcript),
            "--language", "ja",
            "--title", "Pipeline Test",
            "--out", str(self.out),
            "--work-dir", str(self.work),
            "--force",
            *extra,
        ]
        if not any(flag in extra for flag in ("--kind", "--no-enrich")):
            argv += ["--kind", "cli", "--command", f"{sys.executable} {self.model}"]

        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                build_course.main(argv)
        except SystemExit as exc:
            if not expect_failure:
                raise AssertionError(f"build failed unexpectedly:\n{buffer.getvalue()}\n{exc}") from exc
            return f"{buffer.getvalue()}\n{exc}"
        if expect_failure:
            raise AssertionError(f"build was expected to fail but succeeded:\n{buffer.getvalue()}")
        return buffer.getvalue()

    def manifest(self) -> dict:
        with zipfile.ZipFile(self.out) as bundle:
            return json.loads(bundle.read("manifest.json").decode("utf-8-sig"))


class BuildTests(PipelineFixture):
    def test_a_full_build_produces_a_playable_bundle(self) -> None:
        self.build()
        self.assertTrue(self.out.is_file())
        manifest = self.manifest()
        self.assertEqual(len(manifest["sentences"]), 3)
        self.assertEqual(manifest["sourceLanguage"], "ja")
        self.assertEqual(manifest["quality"]["errors"], 0)
        for sentence in manifest["sentences"]:
            self.assertTrue(sentence["zhTranslation"].strip())
            self.assertTrue(sentence["explanationText"].strip())
            self.assertTrue(sentence["id"].startswith("s_"))

    def test_the_bundle_records_which_models_made_it(self) -> None:
        """'Which model produced this course' has to be answerable from the course."""
        self.build()
        metadata = self.manifest()["buildMetadata"]
        self.assertEqual(metadata["asr"]["kind"], "import")
        self.assertEqual(metadata["enrichment"]["provider"]["kind"], "cli")
        self.assertEqual(metadata["enrichment"]["translations"], 3)
        self.assertFalse(metadata["enrichment"]["stub"])

    def test_no_api_key_ever_reaches_the_manifest(self) -> None:
        self.build()
        with zipfile.ZipFile(self.out) as bundle:
            raw = bundle.read("manifest.json").decode("utf-8")
        self.assertNotIn("apiKey\"", raw)
        self.assertNotIn("Authorization", raw)

    def test_transcribe_only_builds_without_translations(self) -> None:
        self.build("--no-enrich")
        manifest = self.manifest()
        self.assertEqual(len(manifest["sentences"]), 3)
        self.assertFalse(manifest["buildMetadata"]["enrichment"]["enabled"])

    def test_stub_enrichment_is_refused_by_default(self) -> None:
        output = self.build("--kind", "echo", expect_failure=True)
        self.assertIn("stub provider", output)
        self.assertFalse(self.out.exists())

    def test_dry_run_writes_nothing(self) -> None:
        self.build("--dry-run")
        self.assertFalse(self.out.exists())
        self.assertFalse(self.work.exists())

    def test_a_missing_model_stops_before_any_work_happens(self) -> None:
        # Explicitly clear a model inherited from the developer's local profile.
        # This case tests validation of missing configuration, not that user's settings.
        output = self.build("--kind", "openai-compat", "--model", "", "--base-url", "http://127.0.0.1:1/v1", expect_failure=True)
        self.assertIn("No model set", output)
        self.assertFalse(self.work.exists())


class ResumeTests(PipelineFixture):
    def test_resume_reuses_the_cached_transcription_and_results(self) -> None:
        self.build()
        output = self.build("--resume")
        self.assertIn("Reusing transcription", output)
        self.assertIn("reuse: batch_001", output)

    def test_resume_refuses_when_the_asr_settings_changed(self) -> None:
        self.build()
        other = self.root / "other.srt"
        other.write_text(TRANSCRIPT, encoding="utf-8")
        output = self.build("--resume", "--transcript", str(other), expect_failure=True)
        self.assertIn("ASR settings changed", output)

    def test_resume_refuses_when_the_audio_changed(self) -> None:
        self.build()
        self.audio.write_bytes(b"ID3" + bytes(4096))
        output = self.build("--resume", expect_failure=True)
        self.assertIn("different audio file", output)

    def test_resume_regenerates_enrichment_when_the_text_model_changes(self) -> None:
        self.build("--model", "draft-model")
        output = self.build("--resume", "--model", "final-model")
        self.assertIn("Reusing transcription", output)
        self.assertIn("text-provider settings do not match", output)
        self.assertIn("generating: batch_001", output)


class BatchIntegrityTests(PipelineFixture):
    def test_a_result_from_another_batch_is_not_merged(self) -> None:
        """The digest is the only thing standing between a course and someone
        else's translations, so corrupting it must break the merge."""
        self.build()
        result = next((self.work / "deepseek_batches" / "results").glob("*.explanations.json"))
        data = json.loads(result.read_text(encoding="utf-8"))
        data["_meta"]["sourceDigest"] = "0" * 64
        result.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        from enrichment import merge_results_into_manifest

        manifest = json.loads((self.work / "manifest.transcribed.json").read_text(encoding="utf-8-sig"))
        with self.assertRaises(ValueError) as caught:
            merge_results_into_manifest(manifest, self.work / "deepseek_batches" / "results")
        self.assertIn("digest", str(caught.exception))


class InstallTests(PipelineFixture):
    def test_install_copies_only_the_course_not_the_player(self) -> None:
        self.build()
        courses = self.root / "courses"
        destination = install_bundle(self.out, courses_dir=courses, course_name="test-course")

        installed = sorted(path.name for path in destination.iterdir())
        self.assertEqual(installed, ["audio.mp3", "install-source.json", "manifest.json", "quality-report.json"])
        # The ZIP carries the whole player; a course folder must not duplicate it.
        with zipfile.ZipFile(self.out) as bundle:
            self.assertIn("app.js", bundle.namelist())
        self.assertFalse((destination / "app.js").exists())

    def test_install_records_the_provenance_of_the_installed_course(self) -> None:
        self.build()
        destination = install_bundle(self.out, courses_dir=self.root / "courses", course_name="c")
        record = json.loads((destination / "install-source.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(record["enrichment"]["provider"]["kind"], "cli")
        self.assertEqual(record["quality"]["errors"], 0)

    def test_installing_over_an_existing_course_needs_force(self) -> None:
        self.build()
        courses = self.root / "courses"
        install_bundle(self.out, courses_dir=courses, course_name="dup")
        with self.assertRaises(InstallError):
            install_bundle(self.out, courses_dir=courses, course_name="dup")
        install_bundle(self.out, courses_dir=courses, course_name="dup", force=True)

    def test_a_failed_course_is_not_installed_silently(self) -> None:
        self.build()
        broken = self.root / "broken.zip"
        with zipfile.ZipFile(self.out) as source, zipfile.ZipFile(broken, "w") as sink:
            for name in source.namelist():
                data = source.read(name)
                if name == "manifest.json":
                    manifest = json.loads(data.decode("utf-8-sig"))
                    manifest["title"] = ""  # audits as manifest.title_missing
                    data = json.dumps(manifest, ensure_ascii=False).encode("utf-8")
                sink.writestr(name, data)
        with self.assertRaises(InstallError) as caught:
            install_bundle(broken, courses_dir=self.root / "courses", course_name="broken")
        self.assertIn("quality error", str(caught.exception))

    def test_a_bundle_escaping_its_folder_is_rejected(self) -> None:
        evil = self.root / "evil.zip"
        with zipfile.ZipFile(evil, "w") as bundle:
            bundle.writestr(
                "manifest.json",
                json.dumps({"schemaVersion": 1, "audio": "../escaped.mp3", "sentences": [{}]}),
            )
            bundle.writestr("../escaped.mp3", b"payload")
        with self.assertRaises(SystemExit):
            install_bundle(evil, courses_dir=self.root / "courses")

    def test_listing_audits_rather_than_trusting_the_manifest(self) -> None:
        self.build()
        courses = self.root / "courses"
        destination = install_bundle(self.out, courses_dir=courses, course_name="listed")
        manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8-sig"))
        # A course that lies about itself must still be reported as broken.
        manifest["quality"] = {"status": "passed", "errors": 0, "warnings": 0}
        manifest["title"] = ""
        (destination / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        row = next(item for item in list_courses(courses) if item["name"] == "listed")
        self.assertEqual(row["status"], "failed")
        self.assertGreaterEqual(row["errors"], 1)


class BackwardCompatibilityTests(unittest.TestCase):
    def test_the_old_module_still_exports_the_helpers_nine_modules_import(self) -> None:
        import build_deepseek_offline_bundle as legacy

        for name in ("load_json", "write_json", "sha256_file", "build_zip", "verify_zip"):
            self.assertTrue(callable(getattr(legacy, name)), name)

    def test_the_old_wrapper_no_longer_invents_a_model(self) -> None:
        import build_deepseek_offline_bundle as legacy

        with self.assertRaises(SystemExit) as caught:
            legacy.main(["--audio", "nope.mp3"])
        self.assertIn("--deepseek-model is now required", str(caught.exception))

    def test_the_old_flags_still_translate_onto_the_new_pipeline(self) -> None:
        """Flag-name drift between the wrapper and the pipeline would only show
        up as an argparse error in front of a user mid-build."""
        import os

        import build_deepseek_offline_bundle as legacy

        os.environ["DEEPSEEK_API_KEY"] = "sk-stub-for-translation-only"
        captured: dict[str, list[str]] = {}

        def fake_build(argv: list[str]) -> int:
            captured["argv"] = argv
            return 0

        import build_course

        original = build_course.main
        build_course.main = fake_build
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                legacy.main(
                    [
                        "--audio", "in.mp3",
                        "--deepseek-model", "some-model",
                        "--whisper-model", "small",
                        "--device", "cpu",
                        "--batch-size", "9",
                        "--thinking", "disabled",
                    ]
                )
        finally:
            build_course.main = original
            os.environ.pop("DEEPSEEK_API_KEY", None)

        argv = captured["argv"]
        # The translated arguments must be accepted by the real parser.
        parsed = build_course.parse_args(argv)
        self.assertEqual(parsed.model, "some-model")
        self.assertEqual(parsed.asr_model, "small")
        self.assertEqual(parsed.asr_device, "cpu")
        self.assertEqual(parsed.batch_size, 9)
        self.assertEqual(parsed.api_key_env, "DEEPSEEK_API_KEY")
        self.assertEqual(json.loads(parsed.extra_body), {"thinking": {"type": "disabled"}})

    def test_a_key_passed_on_the_command_line_is_moved_into_the_environment(self) -> None:
        """It must not be forwarded as an argument: argv is world-readable."""
        import os

        import build_deepseek_offline_bundle as legacy

        name = legacy.resolve_api_key_env("sk-inline-secret")
        try:
            self.assertEqual(os.environ[name], "sk-inline-secret")
            self.assertNotIn("sk-inline-secret", name)
        finally:
            os.environ.pop(name, None)


class CourseClassificationTests(unittest.TestCase):
    def test_course_classification(self) -> None:
        from install_course import classify_course

        self.assertEqual(
            classify_course("2010-07-N1", "JLPT N1 听力 2010年7月"),
            ("intensive", "精听课程", "audio", "音频精听", "N1"),
        )
        self.assertEqual(
            classify_course("2010-12-N2", "2010年12月N2"),
            ("intensive", "精听课程", "audio", "音频精听", "N2"),
        )
        self.assertEqual(
            classify_course("nhk-news-0001-uAiNvInSb6c", "NHK ONE ニュース", "remote"),
            ("intensive", "精听课程", "video", "视频精听", ""),
        )
        self.assertEqual(
            classify_course("tbs-news-0001", "TBS NEWS DIG", "remote"),
            ("intensive", "精听课程", "video", "视频精听", ""),
        )
        self.assertEqual(
            classify_course("librivox-test", "思索者の日記"),
            ("intensive", "精听课程", "audio", "音频精听", ""),
        )
        self.assertEqual(
            classify_course("pdf-exam-2023-n1", "2023年JLPT真题试卷", manifest={"sourceKind": "pdf"}),
            ("pdf", "PDF课程", "jlpt", "JLPT真题", "N1"),
        )
        self.assertEqual(
            classify_course("minna-nihongo-1", "大家的日语初级1 课本", manifest={"sourceKind": "pdf"}),
            ("pdf", "PDF课程", "textbook", "课本和课本PDF", ""),
        )
        self.assertEqual(
            classify_course("try-n2-grammar", "TRY! 日本语能力测试 N2 语法教材", manifest={"sourceKind": "pdf"}),
            ("pdf", "PDF课程", "textbook", "课本和课本PDF", "N2"),
        )


if __name__ == "__main__":
    unittest.main()

