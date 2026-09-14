"""The studio hands a browser control of a pipeline that spawns processes.

That is a bigger surface than the player's, so these tests are mostly about what
the page is *not* allowed to do. The load-bearing rule: a request may name a
profile that already exists in the trusted config, and nothing else. Accepting a
model, base URL or command from a request body would turn any same-origin
foothold into arbitrary code execution.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "tests"))

from studio_server import Studio, _profile_availability, build_studio_server  # noqa: E402
import studio_server as studio_server_module  # noqa: E402
from bundle_io import write_json  # noqa: E402
from course_schema import prepare_course_manifest  # noqa: E402
from test_course_pipeline import FAKE_MODEL, TRANSCRIPT  # noqa: E402

TOKEN = "s" * 64


class RunningStudio:
    """A studio on an ephemeral port, with a config the tests control."""

    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "model.py").write_text(FAKE_MODEL, encoding="utf-8")
        (root / "t.srt").write_text(TRANSCRIPT, encoding="utf-8")
        (root / "audio.mp3").write_bytes(b"ID3" + bytes(2048))
        (root / "providers.json").write_text(
            json.dumps(
                {
                    "asrProfiles": {
                        "test-import": {
                            "kind": "import",
                            "transcript": str((root / "t.srt").resolve()),
                            "language": "ja",
                        }
                    },
                    "textProfiles": {
                        "test-cli": {
                            "kind": "cli",
                            "command": [sys.executable, str((root / "model.py").resolve())],
                            "batchSize": 50,
                        }
                    },
                    "defaultVisionPipeline": "test-local-vision",
                    "visionProfiles": {
                        "test-vision": {
                            "kind": "openai-vlm",
                            "baseUrl": "http://127.0.0.1:9/v1",
                            "model": "test-vlm",
                        }
                    },
                    "visionPipelines": {
                        "test-local-vision": {
                            "description": "test only",
                            "profiles": ["test-vision"],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def __enter__(self) -> "RunningStudio":
        self.server, self.studio, _ = build_studio_server(
            port=0,
            workspace=self.root / "space",
            courses_dir=self.root / "courses",
            config_path=(self.root / "providers.json").resolve(),
            token=TOKEN,
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.studio.cleanup()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def call(self, path, *, method="GET", body=None, headers=None, token=TOKEN, host=None):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method, data=body)
        request.add_header("Host", host or f"127.0.0.1:{self.port}")
        if token:
            request.add_header("X-Dictation-Token", token)
        for name, value in (headers or {}).items():
            request.add_header(name, value)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def json_call(self, path, **kwargs):
        status, raw = self.call(path, **kwargs)
        return status, (json.loads(raw) if raw else {})

    def upload(self):
        return self.json_call(
            "/api/uploads",
            method="POST",
            body=(self.root / "audio.mp3").read_bytes(),
            headers={"X-Dictation-Filename": "audio.mp3"},
        )[1]

    def upload_pdf(self):
        return self.json_call(
            "/api/uploads",
            method="POST",
            body=b"%PDF-1.4\n%%EOF\n",
            headers={"X-Dictation-Filename": "paper.pdf"},
        )[1]

    def build(self, payload):
        return self.json_call(
            "/api/builds",
            method="POST",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def video_probe(self, url):
        return self.json_call(
            "/api/video/probe",
            method="POST",
            body=json.dumps({"url": url}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def video_build(self, payload):
        return self.json_call(
            "/api/video/builds",
            method="POST",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def pdf_build(self, payload):
        return self.json_call(
            "/api/pdf/builds",
            method="POST",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def batch_build(self, payload):
        return self.json_call(
            "/api/batch-builds",
            method="POST",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def wait(self, job_id, timeout=90):
        deadline = time.time() + timeout
        job = {}
        while time.time() < deadline:
            _, job = self.json_call(f"/api/builds/{job_id}")
            if job.get("status") not in ("queued", "running", "cancelling"):
                return job
            time.sleep(0.4)
        raise AssertionError(f"build did not finish: {job}")


class StudioFixture(unittest.TestCase):
    def setUp(self) -> None:
        try:
            import opencc  # noqa: F401
        except ImportError:
            self.skipTest("opencc not installed (studio build tests require requirements.txt)")
        self._temp = tempfile.TemporaryDirectory(prefix="dictation-studio-")
        self.root = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def make_review_draft(self) -> tuple[str, Path]:
        job_id = "a" * 32
        work = self.root / "space" / "builds" / job_id
        draft = work / "artifact" / "exam" / "sample"
        pages = draft / "pages"
        ocr_pages = work / "artifact" / "ocr" / "pages"
        images = work / "artifact" / "ocr" / "images"
        pages.mkdir(parents=True)
        ocr_pages.mkdir(parents=True)
        images.mkdir(parents=True)
        write_json(pages / "p01.json", {"page": 1, "blocks": [{"kind": "passage", "text": "誤字"}], "issues": []})
        write_json(ocr_pages / "page-0001.json", {"page": 1, "markdown": "原始 OCR"})
        (images / "page-0001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        write_json(work / "build-result.json", {
            "reviewRequired": True,
            "status": "needs_review",
            "title": "待复核真题",
            "kind": "exam",
            "level": "N2",
            "draftPath": str(draft),
        })
        return job_id, pages / "p01.json"


class AuthorizationTests(StudioFixture):
    def test_every_api_call_needs_the_session_token(self) -> None:
        with RunningStudio(self.root) as studio:
            for path in ("/api/config", "/api/local-models", "/api/courses", "/api/builds"):
                with self.subTest(path=path):
                    self.assertEqual(studio.call(path, token=None)[0], 403)

    def test_bootstrap_is_the_one_endpoint_that_needs_no_token(self) -> None:
        with RunningStudio(self.root) as studio:
            status, raw = studio.call("/api/session/bootstrap", token=None)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(raw)["token"], TOKEN)

    def test_a_rebound_host_is_refused_even_with_a_valid_token(self) -> None:
        """DNS rebinding: the attacker's page holds a token but arrives with its
        own Host. The player already closed this; the studio must not reopen it."""
        with RunningStudio(self.root) as studio:
            self.assertEqual(studio.call("/api/config", host="evil.example")[0], 403)
            self.assertEqual(studio.call("/api/session/bootstrap", token=None, host="evil.example")[0], 403)

    def test_vscode_forwarded_loopback_port_is_accepted(self) -> None:
        """Dev Containers may translate the remote port to another local port."""
        with RunningStudio(self.root) as studio:
            forwarded = f"localhost:{studio.port + 1000}"
            self.assertEqual(studio.call("/", token=None, host=forwarded)[0], 200)
            self.assertEqual(studio.call("/api/session/bootstrap", token=None, host=forwarded)[0], 200)
            self.assertEqual(studio.call("/api/config", host=forwarded)[0], 200)

    def test_forwarded_write_origin_must_match_forwarded_host(self) -> None:
        with RunningStudio(self.root) as studio:
            forwarded = f"localhost:{studio.port + 1000}"
            status, _ = studio.call(
                "/api/video/probe",
                method="POST",
                body=b"{}",
                host=forwarded,
                headers={"Content-Type": "application/json", "Origin": forwarded.replace("localhost", "http://localhost")},
            )
            # The request reached the handler (and failed on its empty URL), so
            # it was not rejected by the forwarded-port security gate.
            self.assertEqual(status, 400)

            status, _ = studio.call(
                "/api/video/probe",
                method="POST",
                body=b"{}",
                host=forwarded,
                headers={"Content-Type": "application/json", "Origin": "http://localhost:1"},
            )
            self.assertEqual(status, 403)

    def test_a_denial_does_not_echo_the_rejected_header_back(self) -> None:
        with RunningStudio(self.root) as studio:
            status, body = studio.call("/api/config", host="evil.example")
            self.assertEqual(status, 403)
            self.assertNotIn(b"evil.example", body)


class ProviderInjectionTests(StudioFixture):
    """The page may pick a profile. It may never describe one."""

    def test_a_profile_name_that_is_not_in_the_config_is_refused(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload()
            status, payload = studio.build(
                {"uploadId": upload["uploadId"], "textProfile": "not-a-real-profile"}
            )
            self.assertEqual(status, 400)
            self.assertIn("provider config", payload["error"])

    def test_a_command_in_the_request_body_is_ignored_entirely(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload()
            status, payload = studio.build(
                {
                    "uploadId": upload["uploadId"],
                    "textProfile": "test-cli",
                    "asrProfile": "test-import",
                    # None of these may reach the pipeline.
                    "command": "shutdown /s",
                    "model": "attacker-model",
                    "baseUrl": "http://attacker.example/v1",
                    "handoffDir": "/smuggled-handoff-dir",
                }
            )
            self.assertEqual(status, 202)
            argv = studio.studio.job(payload["id"]).argv
            joined = " ".join(argv)
            for smuggled in ("shutdown", "attacker-model", "attacker.example", "smuggled-handoff-dir"):
                self.assertNotIn(smuggled, joined)
            self.assertIn("--profile", argv)
            self.assertEqual(argv[argv.index("--profile") + 1], "test-cli")

    def test_an_unknown_asr_profile_is_refused(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload()
            status, _ = studio.build(
                {"uploadId": upload["uploadId"], "textProfile": "test-cli", "asrProfile": "nope"}
            )
            self.assertEqual(status, 400)

    def test_an_unsupported_language_is_refused(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload()
            status, _ = studio.build(
                {"uploadId": upload["uploadId"], "textProfile": "test-cli", "language": "klingon"}
            )
            self.assertEqual(status, 400)

    def test_the_config_response_never_carries_a_key_or_a_command(self) -> None:
        with RunningStudio(self.root) as studio:
            _, payload = studio.json_call("/api/config")
            raw = json.dumps(payload)
            self.assertNotIn("command", raw)
            self.assertNotIn(sys.executable.replace("\\", "\\\\"), raw)

    def test_config_marks_installed_cli_and_missing_local_service(self) -> None:
        with RunningStudio(self.root) as studio:
            _, payload = studio.json_call("/api/config")
            text = {item["name"]: item for item in payload["textProfiles"]}
            self.assertTrue(text["test-cli"]["available"])
            self.assertEqual(text["test-cli"]["source"], "cli")
            self.assertFalse(payload["visionPipelines"][0]["available"])


class ProviderAvailabilityTests(unittest.TestCase):
    def test_cli_requires_an_installed_executable(self) -> None:
        self.assertTrue(_profile_availability({"kind": "cli", "command": [sys.executable]})["available"])
        self.assertFalse(
            _profile_availability({"kind": "cli", "command": ["definitely-not-installed-xyz"]})["available"]
        )

    def test_cloud_profile_requires_its_declared_key(self) -> None:
        profile = {
            "kind": "openai-compat",
            "baseUrl": "https://api.example.com/v1",
            "apiKeyEnv": "DICTATION_TEST_MISSING_KEY",
            "model": "m",
        }
        previous = os.environ.pop("DICTATION_TEST_MISSING_KEY", None)
        try:
            self.assertFalse(_profile_availability(profile)["available"])
            os.environ["DICTATION_TEST_MISSING_KEY"] = "configured"
            self.assertTrue(_profile_availability(profile)["available"])
        finally:
            os.environ.pop("DICTATION_TEST_MISSING_KEY", None)
            if previous is not None:
                os.environ["DICTATION_TEST_MISSING_KEY"] = previous

    def test_stubs_are_not_presented_as_usable_models(self) -> None:
        self.assertFalse(_profile_availability({"kind": "echo"})["available"])


class LocalModelControlTests(StudioFixture):
    def test_all_services_start_as_independent_parallel_jobs(self) -> None:
        scripts = self.root / "models" / "scripts"
        scripts.mkdir(parents=True)
        for action in ("start", "stop"):
            path = scripts / f"{action}_models.sh"
            path.write_text(f"#!/usr/bin/env bash\necho {action}:$1\n", encoding="utf-8")
        with mock.patch.object(studio_server_module, "LOCAL_MODELS_ROOT", self.root / "models"):
            studio = Studio(self.root / "space", self.root / "courses", None)
            started = studio.control_local_models("start", "all")
            self.assertEqual(len(started["jobs"]), 4)
            deadline = time.time() + 5
            while time.time() < deadline:
                if all(job.status != "running" for job in studio.model_control_history):
                    break
                time.sleep(0.02)
            self.assertTrue(all(job.status == "succeeded" for job in studio.model_control_history))
            self.assertEqual(
                {job.log[0] for job in studio.model_control_history},
                {"start:qwen", "start:vision", "start:ocr", "start:flash-next"},
            )
            studio.cleanup()

    def test_one_service_can_be_controlled_without_touching_the_others(self) -> None:
        scripts = self.root / "models" / "scripts"
        scripts.mkdir(parents=True)
        for action in ("start", "stop"):
            (scripts / f"{action}_models.sh").write_text(
                f"#!/usr/bin/env bash\necho {action}:$1\n", encoding="utf-8"
            )
        with mock.patch.object(studio_server_module, "LOCAL_MODELS_ROOT", self.root / "models"):
            studio = Studio(self.root / "space", self.root / "courses", None)
            result = studio.control_local_models("start", "glm-ocr")
            self.assertEqual([job["service"] for job in result["jobs"]], ["glm-ocr"])
            deadline = time.time() + 5
            while studio.model_control_history[0].status == "running" and time.time() < deadline:
                time.sleep(0.02)
            self.assertEqual(studio.model_control_history[0].log, ["start:ocr"])
            with self.assertRaises(ValueError):
                studio.control_local_models("start", "not-configured")
            studio.cleanup()


class BatchBuildTests(StudioFixture):
    def make_studio(self) -> Studio:
        config = self.root / "providers.json"
        config.write_text(json.dumps({
            "asrProfiles": {"test-import": {"kind": "import", "transcript": str(self.root / "t.srt")}},
            "textProfiles": {"test-cli": {"kind": "cli", "command": [sys.executable]}},
        }), encoding="utf-8")
        (self.root / "t.srt").write_text(TRANSCRIPT, encoding="utf-8")
        return Studio(self.root / "space", self.root / "courses", config)

    def test_batch_runs_uploaded_files_strictly_one_at_a_time(self) -> None:
        studio = self.make_studio()
        uploads = [studio.store_upload(f"lesson-{index}.mp3", b"ID3data") for index in range(3)]
        order = []
        simultaneous = 0
        maximum = 0

        def fake_run(job):
            nonlocal simultaneous, maximum
            simultaneous += 1
            maximum = max(maximum, simultaneous)
            order.append(job.title)
            time.sleep(0.03)
            job.status = "succeeded"
            job.finished_at = time.time()
            simultaneous -= 1

        with mock.patch.object(studio, "_run_job", side_effect=fake_run):
            result = studio.start_batch_build({
                "source": "audio",
                "items": [{"uploadId": item["uploadId"]} for item in uploads],
                "asrProfile": "test-import",
                "textProfile": "test-cli",
            })
            deadline = time.time() + 3
            while any(studio.job(item["id"]).status in {"queued", "running"} for item in result["jobs"]) and time.time() < deadline:
                time.sleep(0.01)

        self.assertEqual(order, ["lesson-0", "lesson-1", "lesson-2"])
        self.assertEqual(maximum, 1)
        self.assertEqual({item["batchId"] for item in result["jobs"]}, {result["batchId"]})
        self.assertEqual([item["batchIndex"] for item in result["jobs"]], [1, 2, 3])

    def test_a_queued_batch_item_can_be_cancelled(self) -> None:
        studio = self.make_studio()
        first = studio.store_upload("first.mp3", b"ID3data")
        second = studio.store_upload("second.mp3", b"ID3data")
        release = threading.Event()

        def fake_run(job):
            release.wait(2)
            job.status = "succeeded"
            job.finished_at = time.time()

        with mock.patch.object(studio, "_run_job", side_effect=fake_run):
            result = studio.start_batch_build({
                "source": "audio",
                "items": [{"uploadId": first["uploadId"]}, {"uploadId": second["uploadId"]}],
                "asrProfile": "test-import",
                "textProfile": "test-cli",
            })
            queued = studio.cancel(result["jobs"][1]["id"])
            self.assertEqual(queued.status, "cancelled")
            release.set()
            deadline = time.time() + 2
            while studio.job(result["jobs"][0]["id"]).status == "running" and time.time() < deadline:
                time.sleep(0.01)
        self.assertEqual(studio.job(result["jobs"][1]["id"]).status, "cancelled")

    def test_batch_validation_is_atomic(self) -> None:
        studio = self.make_studio()
        valid = studio.store_upload("valid.mp3", b"ID3data")
        with self.assertRaises(ValueError):
            studio.start_batch_build({
                "source": "audio",
                "items": [{"uploadId": valid["uploadId"]}, {"uploadId": "missing"}],
                "asrProfile": "test-import",
                "textProfile": "test-cli",
            })
        self.assertEqual(studio.jobs, {})

    def test_batch_is_available_through_the_http_api(self) -> None:
        with RunningStudio(self.root) as studio:
            uploads = [studio.upload(), studio.upload()]
            status, result = studio.batch_build({
                "source": "audio",
                "items": [{"uploadId": item["uploadId"]} for item in uploads],
                "asrProfile": "test-import",
                "textProfile": "test-cli",
                "enrich": False,
                "language": "ja",
            })
            self.assertEqual(status, 202)
            self.assertEqual(len(result["jobs"]), 2)
            completed = [studio.wait(job["id"]) for job in result["jobs"]]
            self.assertTrue(
                all(job["status"] == "succeeded" for job in completed), completed
            )


class CourseEditorTests(StudioFixture):
    def install_course(self, studio: RunningStudio) -> dict:
        folder = self.root / "courses" / "editable"
        folder.mkdir(parents=True)
        (folder / "audio.mp3").write_bytes(b"ID3" + bytes(128))
        manifest = prepare_course_manifest(
            {
                "schemaVersion": 1,
                "title": "Editable",
                "audio": "audio.mp3",
                "sourceLanguage": "ja",
                "sentences": [
                    {
                        "startTime": 0.0,
                        "endTime": 2.0,
                        "sourceText": "今日は晴れです。",
                        "translationText": "今天天晴。",
                        "explanationText": "测试讲解。",
                    }
                ],
            }
        )
        write_json(folder / "manifest.json", manifest)
        return manifest

    def test_installed_sentence_can_be_opened_saved_and_backed_up(self) -> None:
        with RunningStudio(self.root) as studio:
            self.install_course(studio)
            status, opened = studio.json_call("/api/courses/editable")
            self.assertEqual(status, 200)
            self.assertEqual(opened["review"], {"reviewed": 0, "total": 1, "remaining": 1})
            _, pending = studio.json_call("/api/review-targets")
            self.assertTrue(any(item["targetId"] == "editable" for item in pending["targets"]))
            sentence = opened["sentences"][0]
            status, saved = studio.json_call(
                "/api/courses/editable/save",
                method="POST",
                body=json.dumps(
                    {
                        "revision": opened["revision"],
                        "sentenceId": sentence["id"],
                        "title": "Edited title",
                        "fields": {
                            "sourceText": "今日は快晴です。",
                            "translationText": "今天是晴天。",
                            "explanationText": "已人工核对。",
                            "startTime": 0,
                            "endTime": 2.1,
                            "confidence": 0.99,
                            "contentType": "dialogue",
                            "practiceEligible": True,
                        },
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(saved["title"], "Edited title")
            self.assertEqual(saved["sentences"][0]["sourceText"], "今日は快晴です。")
            self.assertEqual(saved["review"], {"reviewed": 1, "total": 1, "remaining": 0})
            status, pending = studio.json_call("/api/review-targets")
            self.assertEqual(status, 200)
            self.assertFalse(any(item["targetId"] == "editable" for item in pending["targets"]))
            self.assertTrue(list((self.root / "courses/editable/.workbench-backups").glob("manifest.*.json")))
            self.assertTrue((self.root / "courses/editable/quality-report.json").is_file())

    def test_a_stale_editor_cannot_overwrite_a_newer_change(self) -> None:
        with RunningStudio(self.root) as studio:
            self.install_course(studio)
            _, opened = studio.json_call("/api/courses/editable")
            sentence = opened["sentences"][0]
            payload = {
                "revision": "stale",
                "sentenceId": sentence["id"],
                "title": "No overwrite",
                "fields": {},
            }
            status, _ = studio.json_call(
                "/api/courses/editable/save", method="POST",
                body=json.dumps(payload).encode(), headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 400)

    def test_model_revision_returns_a_proposal_without_saving(self) -> None:
        reviser = self.root / "reviser.py"
        reviser.write_text(
            "import json,sys\n"
            "sys.stdin.read()\n"
            "print(json.dumps({'sourceText':'修正原文。','translationText':'修正翻译。','explanationText':'修正讲解。'}, ensure_ascii=False))\n",
            encoding="utf-8",
        )
        config_path = self.root / "providers.json"
        config = json.loads(config_path.read_text()) if config_path.exists() else None
        with RunningStudio(self.root) as studio:
            config = json.loads((self.root / "providers.json").read_text())
            config["textProfiles"]["reviser"] = {"kind": "cli", "command": [sys.executable, str(reviser)]}
            (self.root / "providers.json").write_text(json.dumps(config), encoding="utf-8")
            self.install_course(studio)
            _, opened = studio.json_call("/api/courses/editable")
            status, result = studio.json_call(
                "/api/courses/editable/revise",
                method="POST",
                body=json.dumps(
                    {
                        "revision": opened["revision"],
                        "sentenceId": opened["sentences"][0]["id"],
                        "textProfile": "reviser",
                        "instruction": "修正同音字",
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 200)
            self.assertFalse(result["saved"])
            self.assertEqual(result["proposal"]["sourceText"], "修正原文。")
            _, reopened = studio.json_call("/api/courses/editable")
            self.assertEqual(reopened["sentences"][0]["sourceText"], "今日は晴れです。")

    def test_course_paths_cannot_escape_the_library(self) -> None:
        with RunningStudio(self.root) as studio:
            self.assertEqual(studio.call("/api/courses/..%2fproviders.json")[0], 400)


class DraftEditorTests(StudioFixture):
    def test_review_draft_is_restored_saved_and_backed_up(self) -> None:
        job_id, page_path = self.make_review_draft()
        studio = Studio(self.root / "space", self.root / "courses", None)
        summary = studio.draft(job_id)
        self.assertEqual(summary["pages"][0]["page"], 1)
        opened = studio.draft_page(job_id, "p01.json")
        self.assertEqual(opened["sourceMarkdown"], "原始 OCR")
        document = opened["document"]
        document["blocks"][0]["text"] = "正字"
        saved = studio.save_draft_page(job_id, "p01.json", {
            "revision": opened["revision"], "document": document,
        })
        self.assertEqual(saved["document"]["blocks"][0]["text"], "正字")
        self.assertEqual(studio.draft(job_id)["review"], {"reviewed": 1, "total": 1, "remaining": 0})
        self.assertFalse(any(item["targetId"] == job_id for item in studio.review_targets()["targets"]))
        self.assertTrue(any(item["targetId"] == job_id for item in studio.review_targets()["reviewedDrafts"]))
        self.assertTrue(list((page_path.parent / ".workbench-backups").glob("p01.*.json")))

    def test_draft_page_identity_and_paths_are_protected(self) -> None:
        job_id, _ = self.make_review_draft()
        studio = Studio(self.root / "space", self.root / "courses", None)
        opened = studio.draft_page(job_id, "p01.json")
        changed = dict(opened["document"])
        changed["page"] = 2
        with self.assertRaises(ValueError):
            studio.save_draft_page(job_id, "p01.json", {
                "revision": opened["revision"], "document": changed,
            })
        with self.assertRaises(ValueError):
            studio.draft_page(job_id, "../build-result.json")

    def test_draft_and_editor_page_are_available_over_http(self) -> None:
        job_id, _ = self.make_review_draft()
        with RunningStudio(self.root) as studio:
            status, raw = studio.call("/editor.html", token=None)
            self.assertEqual(status, 200)
            self.assertIn(b"editor.js", raw)
            status, summary = studio.json_call(f"/api/drafts/{job_id}")
            self.assertEqual(status, 200)
            self.assertEqual(summary["title"], "待复核真题")
            status, pending = studio.json_call("/api/review-targets")
            self.assertEqual(status, 200)
            self.assertEqual(pending["drafts"], 1)
            self.assertEqual(pending["targets"][0]["targetId"], job_id)
            self.assertEqual(pending["targets"][0]["remaining"], 1)
            status, image = studio.call(f"/api/drafts/{job_id}/images/1")
            self.assertEqual(status, 200)
            self.assertTrue(image.startswith(b"\x89PNG"))

    def test_model_draft_revision_is_a_candidate_and_does_not_save(self) -> None:
        job_id, page_path = self.make_review_draft()
        reviser = self.root / "draft-reviser.py"
        reviser.write_text(
            "import json\n"
            "print(json.dumps({'page': 1, 'blocks': [{'kind': 'passage', 'text': '模型修正'}], 'issues': []}, ensure_ascii=False))\n",
            encoding="utf-8",
        )
        config = self.root / "providers.json"
        config.write_text(json.dumps({
            "textProfiles": {"reviser": {"kind": "cli", "command": [sys.executable, str(reviser)]}},
            "asrProfiles": {},
        }), encoding="utf-8")
        studio = Studio(self.root / "space", self.root / "courses", config)
        opened = studio.draft_page(job_id, "p01.json")
        result = studio.revise_draft_page(job_id, "p01.json", {
            "revision": opened["revision"],
            "textProfile": "reviser",
            "instruction": "核对错字",
            "document": opened["document"],
        })
        self.assertEqual(result["proposal"]["blocks"][0]["text"], "模型修正")
        self.assertEqual(json.loads(page_path.read_text())["blocks"][0]["text"], "誤字")


class WholeCourseAnalysisTests(StudioFixture):
    def test_installed_course_can_be_analyzed_in_the_background(self) -> None:
        analyzer = self.root / "analyzer.py"
        analyzer.write_text(
            "import sys\n"
            "sys.stdin.read()\n"
            "print('## 主要发现\\n\\n- 句子 1：发现全局问题。')\n",
            encoding="utf-8",
        )
        with RunningStudio(self.root) as studio:
            config_path = self.root / "providers.json"
            config = json.loads(config_path.read_text())
            config["textProfiles"]["analyzer"] = {
                "kind": "cli", "command": [sys.executable, str(analyzer)],
            }
            config_path.write_text(json.dumps(config), encoding="utf-8")
            folder = self.root / "courses" / "analysis-course"
            folder.mkdir(parents=True)
            (folder / "audio.mp3").write_bytes(b"ID3data")
            write_json(folder / "manifest.json", prepare_course_manifest({
                "schemaVersion": 1,
                "title": "整课分析测试",
                "audio": "audio.mp3",
                "sourceLanguage": "ja",
                "sentences": [
                    {"startTime": 0, "endTime": 1, "sourceText": "一。"},
                    {"startTime": 1, "endTime": 2, "sourceText": "二。"},
                ],
            }))
            status, started = studio.json_call(
                "/api/analyses", method="POST",
                body=json.dumps({
                    "targetKind": "course",
                    "targetId": "analysis-course",
                    "textProfile": "analyzer",
                    "instruction": "检查全课",
                }).encode(),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 202)
            deadline = time.time() + 5
            result = started
            while result["status"] == "running" and time.time() < deadline:
                time.sleep(0.02)
                _, result = studio.json_call(f"/api/analyses/{started['id']}")
            self.assertEqual(result["status"], "succeeded", result)
            self.assertIn("发现全局问题", result["report"])
            self.assertEqual(result["progress"], result["total"])
            self.assertTrue((self.root / "space" / "analyses" / started["id"] / "report.md").is_file())
            target_md = self.root / "courses" / "analysis-course" / "validation-report.md"
            self.assertTrue(target_md.is_file())
            self.assertIn("发现全局问题", target_md.read_text(encoding="utf-8"))
            self.assertEqual(result["reportPath"], str(target_md.resolve()))
            restored = Studio(self.root / "space", self.root / "courses", config_path)
            self.assertEqual(restored.analysis(started["id"]).status, "succeeded")
            self.assertIn("发现全局问题", restored.analysis(started["id"]).report)

    def test_analysis_input_is_split_to_protect_model_context(self) -> None:
        chunks = Studio._analysis_chunks([
            {"location": "a", "content": "x" * 20_000},
            {"location": "b", "content": "y" * 20_000},
        ])
        self.assertEqual(len(chunks), 2)

    def test_batch_analysis_lifecycle(self) -> None:
        analyzer = self.root / "batch_analyzer.py"
        analyzer.write_text(
            "import sys\n"
            "sys.stdin.read()\n"
            "print('## 批次问题\\n\\n- 跨课程核对发现。')\n",
            encoding="utf-8",
        )
        with RunningStudio(self.root) as studio:
            config_path = self.root / "providers.json"
            config = json.loads(config_path.read_text())
            config["textProfiles"]["analyzer"] = {
                "kind": "cli", "command": [sys.executable, str(analyzer)],
            }
            config_path.write_text(json.dumps(config), encoding="utf-8")

            for cid in ("course-1", "course-2"):
                f = self.root / "courses" / cid
                f.mkdir(parents=True)
                (f / "audio.mp3").write_bytes(b"ID3data")
                write_json(f / "manifest.json", prepare_course_manifest({
                    "schemaVersion": 1,
                    "title": f"课程标题 {cid}",
                    "audio": "audio.mp3",
                    "sourceLanguage": "ja",
                    "sentences": [
                        {"startTime": 0, "endTime": 1, "sourceText": "こんにちは。"},
                    ],
                }))

            status, started = studio.json_call(
                "/api/batch-analyses", method="POST",
                body=json.dumps({
                    "targets": [
                        {"targetKind": "course", "targetId": "course-1"},
                        {"targetKind": "course", "targetId": "course-2"},
                    ],
                    "textProfile": "analyzer",
                    "instruction": "批量检查",
                }).encode(),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 202)
            self.assertEqual(started["total"], 2)
            deadline = time.time() + 10
            result = started
            while result["status"] == "running" and time.time() < deadline:
                time.sleep(0.05)
                _, result = studio.json_call(f"/api/batch-analyses/{started['id']}")
            self.assertEqual(result["status"], "succeeded", result)
            self.assertEqual(result["progress"], 2)
            self.assertIn("多课程批量复核质检报告", result["overallReport"])
            self.assertIn("course:course-1", result["targetReports"])
            self.assertIn("course:course-2", result["targetReports"])
            self.assertEqual(result["targetStatuses"]["course:course-1"], "succeeded")
            self.assertEqual(result["targetStatuses"]["course:course-2"], "succeeded")
            c1_md = self.root / "courses" / "course-1" / "validation-report.md"
            c2_md = self.root / "courses" / "course-2" / "validation-report.md"
            self.assertTrue(c1_md.is_file())
            self.assertTrue(c2_md.is_file())
            batch_summary_md = self.root / "space" / "analyses" / f"batch-{started['id']}" / "report.md"
            self.assertTrue(batch_summary_md.is_file())
            self.assertEqual(result["targetReportPaths"]["course:course-1"], str(c1_md.resolve()))
            self.assertEqual(result["targetReportPaths"]["course:course-2"], str(c2_md.resolve()))
            self.assertEqual(result["reportPath"], str(batch_summary_md.resolve()))

            list_status, batch_list = studio.json_call("/api/batch-analyses")
            self.assertEqual(list_status, 200)
            self.assertTrue(any(item["id"] == started["id"] for item in batch_list.get("batchAnalyses", [])))

    def test_batch_review_approve_with_audit(self) -> None:
        draft_id, _ = self.make_review_draft()
        with RunningStudio(self.root) as studio:
            c1 = self.root / "courses" / "valid-course"
            c1.mkdir(parents=True)
            (c1 / "audio.mp3").write_bytes(b"ID3data")
            write_json(c1 / "manifest.json", prepare_course_manifest({
                "schemaVersion": 1,
                "title": "合法课程",
                "audio": "audio.mp3",
                "sourceLanguage": "ja",
                "sentences": [
                    {"startTime": 0, "endTime": 1, "sourceText": "テスト。"},
                ],
            }))

            c2 = self.root / "courses" / "broken-course"
            c2.mkdir(parents=True)
            write_json(c2 / "manifest.json", prepare_course_manifest({
                "schemaVersion": 1,
                "title": "损坏课程",
                "audio": "non-existent.mp3",
                "sourceLanguage": "ja",
                "sentences": [
                    {"startTime": 0, "endTime": 1, "sourceText": "壊れた。"},
                ],
            }))
            status, res = studio.json_call(
                "/api/batch-review/approve", method="POST",
                body=json.dumps({
                    "targets": [
                        {"targetKind": "course", "targetId": "valid-course", "title": "合法课程"},
                        {"targetKind": "course", "targetId": "broken-course", "title": "损坏课程"},
                        {"targetKind": "draft", "targetId": draft_id, "title": "待复核草稿"},
                    ],
                    "note": "批量复核测试",
                }).encode(),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(len(res["approved"]), 2)
            self.assertEqual(res["approved"][0]["targetId"], "valid-course")
            self.assertEqual(res["approved"][1]["targetId"], draft_id)
            self.assertEqual(len(res["failed"]), 1)
            self.assertEqual(res["failed"][0]["targetId"], "broken-course")

            updated_m = json.loads((c1 / "manifest.json").read_text(encoding="utf-8-sig"))
            edits = updated_m.get("buildMetadata", {}).get("workbenchEdits", {})
            self.assertTrue(len(edits.get("sentenceIds", [])) > 0)
            self.assertEqual(edits.get("batchApprovedNote"), "批量复核测试")
            validation_md = c1 / "validation-report.md"
            self.assertTrue(validation_md.is_file())
            self.assertIn("课程复核确认与质量报告", validation_md.read_text(encoding="utf-8"))
            self.assertEqual(res["approved"][0]["reportPath"], str(validation_md.resolve()))

            draft_md = self.root / "space" / "builds" / draft_id / "validation-report.md"
            self.assertTrue(draft_md.is_file())
            self.assertIn("草稿复核确认报告", draft_md.read_text(encoding="utf-8"))
            self.assertEqual(res["approved"][1]["reportPath"], str(draft_md.resolve()))


class UploadTests(StudioFixture):
    def test_an_uploaded_filename_never_becomes_a_path(self) -> None:
        """The stored name is generated; the client's name is only metadata."""
        with RunningStudio(self.root) as studio:
            _, payload = studio.json_call(
                "/api/uploads",
                method="POST",
                body=b"ID3" + bytes(64),
                headers={"X-Dictation-Filename": "../../escaped.mp3"},
            )
            self.assertEqual(payload["originalName"], "escaped.mp3")
            self.assertTrue(payload["storedName"].startswith(payload["uploadId"]))
            uploads_dir = self.root / "space" / "uploads"
            written = list(uploads_dir.iterdir())
            # Every file the upload created is named from the generated id, so
            # no part of the client's string reaches a path, and nothing landed
            # outside the uploads directory.
            self.assertTrue(written)
            for path in written:
                self.assertTrue(path.name.startswith(payload["uploadId"]), path.name)
                self.assertEqual(path.parent, uploads_dir)
            self.assertFalse((uploads_dir.parent.parent / "escaped.mp3").exists())

    def test_a_non_audio_extension_is_refused(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.json_call(
                "/api/uploads",
                method="POST",
                body=b"MZ",
                headers={"X-Dictation-Filename": "payload.exe"},
            )
            self.assertEqual(status, 400)
            self.assertIn("Unsupported upload type", payload["error"])

    def test_a_pdf_upload_is_labelled_and_its_signature_is_checked(self) -> None:
        with RunningStudio(self.root) as studio:
            payload = studio.upload_pdf()
            self.assertEqual(payload["kind"], "pdf")
            status, rejected = studio.json_call(
                "/api/uploads",
                method="POST",
                body=b"not really a PDF",
                headers={"X-Dictation-Filename": "fake.pdf"},
            )
            self.assertEqual(status, 400)
            self.assertIn("signature", rejected["error"])

    def test_a_pdf_cannot_be_sent_to_the_audio_pipeline(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload_pdf()
            status, payload = studio.build(
                {"uploadId": upload["uploadId"], "textProfile": "test-cli"}
            )
            self.assertEqual(status, 400)
            self.assertIn("not audio", payload["error"])

    def test_an_unknown_upload_id_cannot_start_a_build(self) -> None:
        with RunningStudio(self.root) as studio:
            status, _ = studio.build({"uploadId": "../../etc/passwd", "textProfile": "test-cli"})
            self.assertEqual(status, 400)


class BuildLifecycleTests(StudioFixture):
    def test_a_build_runs_streams_and_installs(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload()
            status, job = studio.build(
                {
                    "uploadId": upload["uploadId"],
                    "title": "Studio test",
                    "language": "ja",
                    "asrProfile": "test-import",
                    "textProfile": "test-cli",
                }
            )
            self.assertEqual(status, 202)
            finished = studio.wait(job["id"])
            self.assertEqual(finished["status"], "succeeded", finished.get("log"))
            self.assertTrue(finished["hasBundle"])

            _, installed = studio.json_call(
                f"/api/builds/{job['id']}/install",
                method="POST",
                body=b"{}",
                headers={"Content-Type": "application/json"},
            )
            destination = Path(installed["installedTo"])
            self.assertTrue((destination / "manifest.json").is_file())
            self.assertTrue((destination / "audio.mp3").is_file())

            _, courses = studio.json_call("/api/courses")
            self.assertEqual([c["name"] for c in courses["courses"]], [destination.name])
            self.assertEqual(courses["courses"][0]["status"], "passed")

    def test_the_log_is_delivered_incrementally(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload()
            _, job = studio.build(
                {
                    "uploadId": upload["uploadId"],
                    "asrProfile": "test-import",
                    "textProfile": "test-cli",
                    "language": "ja",
                }
            )
            studio.wait(job["id"])
            _, full = studio.json_call(f"/api/builds/{job['id']}?since=0")
            self.assertGreater(len(full["log"]), 3)
            _, tail = studio.json_call(f"/api/builds/{job['id']}?since={full['logCursor']}")
            self.assertEqual(tail["log"], [])

    def test_an_unfinished_build_cannot_be_installed(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload()
            _, job = studio.build(
                {"uploadId": upload["uploadId"], "asrProfile": "test-import", "textProfile": "test-cli"}
            )
            status, payload = studio.json_call(
                f"/api/builds/{job['id']}/install",
                method="POST",
                body=b"{}",
                headers={"Content-Type": "application/json"},
            )
            if status == 400:
                self.assertIn("finished build", payload["error"])
            studio.wait(job["id"])

    def test_the_build_does_not_inherit_the_studio_session_token(self) -> None:
        """A build runs third-party model code and CLI tools; handing it the
        token that authorizes this server would be a needless escalation."""
        import inspect

        source = inspect.getsource(Studio._run_job)
        self.assertIn('env.pop("DICTATION_SESSION_TOKEN", None)', source)


class PdfBuildTests(StudioFixture):
    def test_pdf_build_uses_only_a_named_trusted_vision_pipeline(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload_pdf()
            status, payload = studio.pdf_build(
                {
                    "uploadId": upload["uploadId"],
                    "title": "PDF test",
                    "documentKind": "exam",
                    "level": "N2",
                    "visionPipeline": "test-local-vision",
                    # Browser-supplied provider details must never reach argv.
                    "model": "attacker-model",
                    "baseUrl": "https://attacker.example/v1",
                    "command": "touch /tmp/pwned",
                }
            )
            self.assertEqual(status, 202)
            self.assertEqual(payload["kind"], "pdf")
            argv = studio.studio.job(payload["id"]).argv
            joined = " ".join(argv)
            self.assertEqual(argv[argv.index("--vision-profile") + 1], "test-vision")
            self.assertEqual(argv[argv.index("--kind") + 1], "exam")
            for smuggled in ("attacker-model", "attacker.example", "touch /tmp/pwned"):
                self.assertNotIn(smuggled, joined)

    def test_unknown_pdf_pipeline_and_invalid_kind_are_refused(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload_pdf()
            base = {"uploadId": upload["uploadId"], "visionPipeline": "not-configured"}
            self.assertEqual(studio.pdf_build(base)[0], 400)
            base["visionPipeline"] = "test-local-vision"
            base["documentKind"] = "delete-everything"
            self.assertEqual(studio.pdf_build(base)[0], 400)

    def test_pdf_auto_level_reaches_the_pipeline_as_auto(self) -> None:
        with RunningStudio(self.root) as studio:
            upload = studio.upload_pdf()
            status, payload = studio.pdf_build({
                "uploadId": upload["uploadId"],
                "visionPipeline": "test-local-vision",
                "level": "auto",
            })
            self.assertEqual(status, 202)
            argv = studio.studio.job(payload["id"]).argv
            self.assertEqual(argv[argv.index("--level") + 1], "auto")

    def test_config_exposes_vision_names_but_not_endpoints(self) -> None:
        with RunningStudio(self.root) as studio:
            _, payload = studio.json_call("/api/config")
            raw = json.dumps(payload)
            self.assertEqual(payload["defaultVisionPipeline"], "test-local-vision")
            self.assertIn("test-vision", raw)
            self.assertNotIn("127.0.0.1:9", raw)


class AssetTests(StudioFixture):
    def test_the_page_is_served_and_carries_a_strict_csp(self) -> None:
        with RunningStudio(self.root) as studio:
            request = urllib.request.Request(f"http://127.0.0.1:{studio.port}/")
            request.add_header("Host", f"127.0.0.1:{studio.port}")
            with urllib.request.urlopen(request, timeout=10) as response:
                csp = response.headers.get("Content-Security-Policy")
                body = response.read().decode("utf-8")
            self.assertIn("script-src 'self'", csp)
            self.assertIn("frame-ancestors 'none'", csp)
            # An inline handler would need 'unsafe-inline' and reopen XSS.
            self.assertNotIn("onclick=", body)

    def test_paths_cannot_escape_the_asset_directory(self) -> None:
        with RunningStudio(self.root) as studio:
            for path in ("/../provider_config.py", "/..%2fserve_course.py", "/studio_web/../../src/serve_course.py"):
                with self.subTest(path=path):
                    self.assertEqual(studio.call(path)[0], 404)


if __name__ == "__main__":
    unittest.main()


class OnlineVideoTests(unittest.TestCase):
    """A URL from a request body now reaches a subprocess argv. That is the risk."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory(prefix="studio-video-")
        self.root = Path(self._temp.name)
        self.addCleanup(self._temp.cleanup)

    def video_payload(self, **overrides):
        payload = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "textProfile": "test-cli",
            "language": "ja",
            "transcript": "auto",
        }
        payload.update(overrides)
        return payload

    def test_probing_a_non_web_url_is_refused(self) -> None:
        with RunningStudio(self.root) as studio:
            for url in ("file:///C:/secrets.txt", "ftp://x.test/v", "http://127.0.0.1:4174/api/config"):
                with self.subTest(url=url):
                    status, payload = studio.video_probe(url)
                    self.assertEqual(status, 400)
                    self.assertIn("error", payload)

    def test_a_url_starting_with_a_dash_can_never_become_a_flag(self) -> None:
        with RunningStudio(self.root) as studio:
            status, _ = studio.video_probe("--exec=calc.exe")
            self.assertEqual(status, 400)
            status, _ = studio.video_build(self.video_payload(url="-o/tmp/pwned"))
            self.assertEqual(status, 400)

    def test_probe_reports_a_missing_yt_dlp_without_failing(self) -> None:
        # yt-dlp is genuinely absent on the machine this was written on, and the UI
        # has to say so rather than throw.
        with RunningStudio(self.root) as studio:
            status, payload = studio.video_probe("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            self.assertEqual(status, 200)
            self.assertEqual(payload["provider"], "youtube")
            self.assertEqual(payload["control"], "full")
            self.assertIn("ytdlpAvailable", payload)
            if not payload["ytdlpAvailable"]:
                self.assertIn("yt-dlp", payload["ytdlpHint"])

    def test_a_video_build_argv_carries_only_validated_values(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.video_build(self.video_payload(
                # None of these may reach the pipeline.
                command="shutdown /s",
                model="attacker-model",
                baseUrl="http://attacker.example/v1",
                handoffDir="/smuggled-handoff-dir",
                ytdlp="C:/attacker/yt-dlp.exe",
                coursesDir="C:/attacker/courses",
            ))
            self.assertEqual(status, 202)
            argv = studio.studio.job(payload["id"]).argv
            joined = " ".join(argv)
            for smuggled in ("shutdown", "attacker-model", "attacker.example",
                             "smuggled-handoff-dir", "C:/attacker"):
                self.assertNotIn(smuggled, joined)
            self.assertIn("--profile", argv)
            self.assertEqual(argv[argv.index("--profile") + 1], "test-cli")
            # The canonical URL our own parser rebuilt, not the browser's string.
            self.assertEqual(argv[argv.index("--url") + 1], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_the_url_in_the_argv_is_the_canonical_one_not_the_raw_string(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.video_build(self.video_payload(
                url="https://m.youtube.com/watch?v=dQw4w9WgXcQ&list=PL&feature=share#frag"
            ))
            self.assertEqual(status, 202)
            argv = studio.studio.job(payload["id"]).argv
            self.assertEqual(argv[argv.index("--url") + 1], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_an_unknown_profile_is_refused_for_a_video_build_too(self) -> None:
        with RunningStudio(self.root) as studio:
            status, _ = studio.video_build(self.video_payload(textProfile="not-in-config"))
            self.assertEqual(status, 400)
            status, _ = studio.video_build(self.video_payload(asrProfile="not-in-config"))
            self.assertEqual(status, 400)

    def test_a_bogus_subtitle_language_never_reaches_the_argv(self) -> None:
        with RunningStudio(self.root) as studio:
            status, _ = studio.video_build(self.video_payload(subLangs="ja;rm -rf /"))
            self.assertEqual(status, 400)

    def test_an_impossible_clip_window_is_refused(self) -> None:
        with RunningStudio(self.root) as studio:
            for start, end in (("90", "30"), ("-5", "30"), ("x", "y")):
                with self.subTest(clip=(start, end)):
                    status, _ = studio.video_build(self.video_payload(clipStart=start, clipEnd=end))
                    self.assertEqual(status, 400)

    def test_only_site_subtitles_forbids_reaching_for_the_audio(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.video_build(self.video_payload(
                transcript="subs", allowAudioFetch=False))
            self.assertEqual(status, 202)
            argv = studio.studio.job(payload["id"]).argv
            self.assertIn("--no-audio-fetch", argv)

    def test_verified_transcript_mode_reaches_the_video_pipeline(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.video_build(self.video_payload(transcript="verified"))
            self.assertEqual(status, 202)
            argv = studio.studio.job(payload["id"]).argv
            self.assertEqual(argv[argv.index("--transcript") + 1], "verified")

    def test_a_video_job_is_labelled_and_needs_no_zip_to_install(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.video_build(self.video_payload())
            self.assertEqual(status, 202)
            self.assertEqual(payload["kind"], "video")
            job = studio.studio.job(payload["id"])
            job.status = "succeeded"
            # The audio path would raise "The build produced no bundle." here.
            result = studio.studio.install(job.id, None)
            self.assertTrue(result["alreadyInstalled"])

    def test_the_build_subprocess_does_not_inherit_the_session_token(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.video_build(self.video_payload())
            self.assertEqual(status, 202)
            argv = studio.studio.job(payload["id"]).argv
            self.assertNotIn(TOKEN, " ".join(argv))

    def test_gpu_status_endpoint_returns_json_and_requires_auth(self) -> None:
        with RunningStudio(self.root) as studio:
            unauth_status, _ = studio.json_call("/api/gpu-status", token=None)
            self.assertEqual(unauth_status, 403)

            status, payload = studio.json_call("/api/gpu-status")
            self.assertEqual(status, 200)
            self.assertIn("available", payload)
            self.assertIn("nvml_ready", payload)
            self.assertIn("device_count", payload)
            self.assertIn("gpus", payload)
            self.assertIn("status_text", payload)
            self.assertIsInstance(payload["gpus"], list)

    def test_gpu_probe_telemetry_parsing_with_mock_smi(self) -> None:
        mock_output = (
            "0, NVIDIA GeForce RTX 4090, GPU-aaa, 24576, 4096, 20480, 25, 48, 150.5, 450.0\n"
            "1, NVIDIA GeForce RTX 3090, GPU-bbb, 24576, 8192, 16384, 80, 62, 280.0, 350.0\n"
        )
        fake_result = mock.Mock(returncode=0, stdout=mock_output, stderr="")
        with mock.patch("shutil.which", return_value="/usr/bin/nvidia-smi"), \
             mock.patch("subprocess.run", return_value=fake_result):
            res = studio_server_module._probe_gpu_status(None)
            self.assertTrue(res["available"])
            self.assertTrue(res["nvml_ready"])
            self.assertEqual(res["device_count"], 2)
            self.assertEqual(len(res["gpus"]), 2)
            gpu0 = res["gpus"][0]
            self.assertEqual(gpu0["index"], 0)
            self.assertEqual(gpu0["name"], "NVIDIA GeForce RTX 4090")
            self.assertEqual(gpu0["memory_total_mb"], 24576.0)
            self.assertEqual(gpu0["memory_used_mb"], 4096.0)
            self.assertEqual(gpu0["memory_free_mb"], 20480.0)
            self.assertEqual(gpu0["utilization_gpu_percent"], 25.0)
            self.assertEqual(gpu0["temperature_gpu_c"], 48.0)
            self.assertEqual(gpu0["power_draw_w"], 150.5)

    def test_gpu_probe_no_hardware_fallback(self) -> None:
        with mock.patch("shutil.which", return_value=None), \
             mock.patch("pathlib.Path.exists", return_value=False), \
             mock.patch("pathlib.Path.is_file", return_value=False), \
             mock.patch("glob.glob", return_value=[]):
            res = studio_server_module._probe_gpu_status(None)
            self.assertFalse(res["available"])
            self.assertFalse(res["nvml_ready"])
            self.assertEqual(res["device_count"], 0)
            self.assertEqual(res["gpus"], [])


class RepairAndAnalysisEndpointsTests(StudioFixture):
    def test_resources_status_endpoint(self) -> None:
        with RunningStudio(self.root) as studio:
            status, payload = studio.json_call("/api/resources/status")
            self.assertEqual(status, 200)
            self.assertIn("gpu", payload)
            self.assertIn("cpu", payload)

    def test_structured_analysis_and_patches(self) -> None:
        with RunningStudio(self.root) as studio:
            course_dir = self.root / "courses" / "sample-course"
            course_dir.mkdir(parents=True, exist_ok=True)
            (course_dir / "audio.mp3").write_bytes(b"ID3" + bytes(1024))
            manifest = {
                "schemaVersion": 1,
                "courseId": "c_0123456789abcdef01234567",
                "title": "Sample Course",
                "language": "ja",
                "audio": "audio.mp3",
                "sentences": [
                    {
                        "id": "s_0123456789abcdef01234567",
                        "sourceText": "こんにちは　世界",
                        "zhTranslation": "你好世界",
                        "explanationText": "问候语",
                        "startTime": 0.0,
                        "endTime": 2.0,
                    }
                ],
            }
            write_json(course_dir / "manifest.json", manifest)

            # 1. Structured analysis
            status, analysis = studio.json_call("/api/analysis/structured/sample-course")
            self.assertEqual(status, 200)
            self.assertEqual(analysis["schemaVersion"], 1)
            self.assertIn("checkResults", analysis)

            # 2. Deterministic repair
            status, rep_res = studio.json_call(
                "/api/repairs/deterministic/sample-course",
                method="POST",
                body=b"{}",
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 200)
            self.assertIn("newRevision", rep_res)

            # 3. CAS Patch application
            current_rev = rep_res["newRevision"]
            patch_payload = {
                "baseRevision": current_rev,
                "operations": [
                    {
                        "op": "replace_field",
                        "itemId": "s_0123456789abcdef01234567",
                        "field": "zhTranslation",
                        "value": "你好，世界！",
                    }
                ],
            }
            status, patch_res = studio.json_call(
                "/api/patches/apply/sample-course",
                method="POST",
                body=json.dumps(patch_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(status, 200)
            self.assertTrue(patch_res["success"])
            self.assertEqual(patch_res["course"]["sentences"][0]["zhTranslation"], "你好，世界！")
