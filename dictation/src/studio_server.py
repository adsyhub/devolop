"""Localhost-only course studio: build a course without touching the command line.

Until now the entire pipeline was CLI-only, so making a course meant knowing a
dozen flags. This is the same pipeline behind a page: upload audio or PDF, or
paste a video URL, pick trusted provider profiles, and watch the build run.

Two boundaries make that safe to do from a browser, and both are load-bearing:

**The page can never construct a provider.** It selects a *profile name* that
already exists in ``config/providers.json`` - nothing else. Not a model, not a
base URL, and above all not a command. The ``cli`` text kind and the ``command``
ASR kind spawn subprocesses, so accepting a browser-supplied command would turn
any same-origin foothold into arbitrary code execution on the machine. The config
file is trusted because a person edited it; a request body is not, ever.

**Local inputs arrive as uploads, never as paths.** There is no endpoint that
reads or lists an arbitrary path, so there is no traversal surface and nothing
that can be used to probe the filesystem.

Everything else is inherited: :mod:`security_context` gates every request the
same way the player does (loopback Host allowlist, session token on every call,
Fetch Metadata and Origin on writes), which stops remote pages, DNS rebinding and
stray local clients. It does not stop a process already running as you - that is
outside this boundary, as it is for the player.

Builds run as child processes rather than threads: a build can be killed, its
output streams naturally, and a crash inside faster-whisper takes the child down
instead of the server. Segfaulting on a bad model is not hypothetical here - see
``supportsWordTimestamps`` in the provider config.

    python src/studio_server.py
"""

from __future__ import annotations

import argparse
import concurrent.futures
import glob
import hashlib
import importlib.util
import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
import urllib.error
import urllib.request
from urllib.parse import unquote, urlparse, urlsplit

from bundle_io import parse_jsonish, safe_filename, sha256_file, write_json
from bundle_quality import audit_manifest
from course_schema import prepare_course_manifest
from install_course import DEFAULT_COURSES_DIR, InstallError, install_bundle, list_courses
from studio_artifacts import resolve_course_manifest_path, resolve_course_audio_path
from language_support import (
    SUPPORTED_LANGUAGE_CODES,
    manifest_language_code,
    set_source_text,
    set_translation_text,
    transcript_text,
)
from media_sources import MediaSourceError, parse_media_url, probe_media, ytdlp_available
from provider_config import ConfigError, list_profiles, load_config_file, resolve_text_provider
from security_context import TOKEN_HEADER, SecurityContext, token_from_environment
from text_providers import ProviderError, build_text_provider
from studio_analysis import analyze_manifest
from studio_resources import get_slot_manager
from studio_repair import (
    CasConflictError,
    Patch,
    PatchError,
    PatchOp,
    PatchValidationError,
    RevisionMismatchError,
    apply_deterministic_repairs as apply_deterministic_repairs_op,
    apply_patch as apply_patch_op,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
STUDIO_WEB = Path(__file__).resolve().parent / "studio_web"
BUILD_SCRIPT = Path(__file__).resolve().parent / "build_course.py"
VIDEO_BUILD_SCRIPT = Path(__file__).resolve().parent / "build_video_course.py"
PDF_BUILD_SCRIPT = Path(__file__).resolve().parent / "build_pdf_course.py"

DEFAULT_PORT = 4174
MAX_UPLOAD_BYTES = 512 * 1024 * 1024
MAX_JSON_BODY = 512 * 1024
MAX_LOG_LINES = 4000
MAX_COURSE_FIELD_LENGTH = 20_000
MAX_DRAFT_PAGE_LENGTH = 200_000
MAX_ANALYSIS_CHUNK_CHARS = 30_000
MAX_BATCH_FILES = 50
LOCAL_MODELS_ROOT = Path(os.environ.get("DICTATION_LOCAL_MODELS_ROOT", "/workspace/ECGegg"))
LOCAL_MODEL_SERVICES = (
    ("qwen27", "Qwen3.8-27B-FP8", "听写翻译/讲解初稿", "http://127.0.0.1:8100/v1", "Qwen/Qwen3.8-27B-FP8"),
    ("glm46v", "GLM-4.6V-Flash", "PDF 与复杂版面复核", "http://127.0.0.1:8101/v1", "zai-org/GLM-4.6V-Flash"),
    ("glm-ocr", "GLM-OCR", "PDF 首轮 OCR", "http://127.0.0.1:8102/v1", "zai-org/GLM-OCR"),
    ("flash-next", "Qwen3.8-Flash-Next", "终稿与疑难裁决", "http://127.0.0.1:8103/v1", "Qwen/Qwen3.8-Flash-Next"),
)
LOCAL_MODEL_SCRIPT_NAMES = {
    "qwen27": "qwen",
    "glm46v": "vision",
    "glm-ocr": "ocr",
    "flash-next": "flash-next",
}
AUDIO_UPLOAD_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".mp4", ".webm", ".mpeg", ".mpga", ".ogg", ".opus", ".flac",
}
DOCUMENT_UPLOAD_EXTENSIONS = {".pdf"}
UPLOAD_EXTENSIONS = AUDIO_UPLOAD_EXTENSIONS | DOCUMENT_UPLOAD_EXTENSIONS

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; "
        "media-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


# --------------------------------------------------------------------------
# Build jobs
# --------------------------------------------------------------------------


@dataclass
class BuildJob:
    id: str
    title: str
    argv: list[str]
    out_path: Path
    work_dir: Path
    status: str = "running"
    log: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    exit_code: int | None = None
    installed_to: str | None = None
    kind: str = "audio"
    result_path: Path | None = None
    result: dict[str, Any] | None = None
    process: subprocess.Popen | None = None
    batch_id: str | None = None
    batch_index: int | None = None
    batch_size: int | None = None

    def snapshot(self, since: int = 0) -> dict[str, Any]:
        since = max(0, min(since, len(self.log)))
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "exitCode": self.exit_code,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "elapsed": round((self.finished_at or time.time()) - self.started_at, 1),
            "installedTo": self.installed_to,
            "kind": self.kind,
            "hasBundle": self.kind == "audio" and self.out_path.is_file(),
            "reviewRequired": bool((self.result or {}).get("reviewRequired")),
            "result": self.result,
            "batchId": self.batch_id,
            "batchIndex": self.batch_index,
            "batchSize": self.batch_size,
            "logCursor": len(self.log),
            "log": self.log[since:],
        }

@dataclass
class ModelControlJob:
    id: str
    service: str
    action: str
    status: str = "running"
    log: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    exit_code: int | None = None
    process: subprocess.Popen | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "service": self.service,
            "action": self.action,
            "status": self.status,
            "log": list(self.log),
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "exitCode": self.exit_code,
        }


@dataclass
class AnalysisJob:
    id: str
    target_kind: str
    target_id: str
    profile: str
    instruction: str
    status: str = "running"
    log: list[str] = field(default_factory=list)
    report: str = ""
    report_path: str = ""
    progress: int = 0
    total: int = 0
    source_revision: str = ""
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def snapshot(self, since: int = 0) -> dict[str, Any]:
        since = max(0, min(since, len(self.log)))
        return {
            "id": self.id,
            "targetKind": self.target_kind,
            "targetId": self.target_id,
            "profile": self.profile,
            "instruction": self.instruction,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "sourceRevision": self.source_revision,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "elapsed": round((self.finished_at or time.time()) - self.started_at, 1),
            "logCursor": len(self.log),
            "log": self.log[since:],
            "report": self.report,
            "reportPath": self.report_path,
        }


@dataclass
class BatchAnalysisJob:
    id: str
    targets: list[dict[str, Any]]
    profile: str
    instruction: str
    status: str = "running"
    progress: int = 0
    total: int = 0
    current_target_name: str = ""
    log: list[str] = field(default_factory=list)
    overall_report: str = ""
    report_path: str = ""
    target_reports: dict[str, str] = field(default_factory=dict)
    target_report_paths: dict[str, str] = field(default_factory=dict)
    target_statuses: dict[str, str] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def snapshot(self, since: int = 0) -> dict[str, Any]:
        since = max(0, min(since, len(self.log)))
        return {
            "id": self.id,
            "targets": self.targets,
            "profile": self.profile,
            "instruction": self.instruction,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "currentTargetName": self.current_target_name,
            "overallReport": self.overall_report,
            "reportPath": self.report_path,
            "targetReports": self.target_reports,
            "targetReportPaths": self.target_report_paths,
            "targetStatuses": self.target_statuses,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "elapsed": round((self.finished_at or time.time()) - self.started_at, 1),
            "logCursor": len(self.log),
            "log": self.log[since:],
        }


class Studio:
    """Owns the workspace, the running jobs, and the one trusted config."""

    def __init__(self, workspace: Path, courses_dir: Path, config_path: Path | None) -> None:
        self.workspace = workspace
        self.uploads_dir = workspace / "uploads"
        self.builds_dir = workspace / "builds"
        self.analyses_dir = workspace / "analyses"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.builds_dir.mkdir(parents=True, exist_ok=True)
        self.analyses_dir.mkdir(parents=True, exist_ok=True)
        self.courses_dir = courses_dir
        self.config_path = config_path
        self.jobs: dict[str, BuildJob] = {}
        self.model_control_jobs: dict[str, ModelControlJob] = {}
        self.model_control_history: list[ModelControlJob] = []
        self.analysis_jobs: dict[str, AnalysisJob] = {}
        self.batch_analysis_jobs: dict[str, BatchAnalysisJob] = {}
        self.shutting_down = False
        self.lock = threading.RLock()
        self._restore_review_drafts()
        self._restore_analyses()

    def _restore_review_drafts(self) -> None:
        """Make completed PDF review drafts editable again after a server restart."""
        for result_path in self.builds_dir.glob("*/build-result.json"):
            try:
                result = json.loads(result_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(result, dict) or not result.get("reviewRequired"):
                continue
            job_id = result_path.parent.name
            if not re.fullmatch(r"[0-9a-f]{32}", job_id):
                continue
            timestamp = result_path.stat().st_mtime
            self.jobs[job_id] = BuildJob(
                id=job_id,
                title=str(result.get("title") or job_id),
                argv=[],
                out_path=result_path.parent / "(no bundle)",
                work_dir=result_path.parent,
                status="needs_review",
                started_at=timestamp,
                finished_at=timestamp,
                exit_code=0,
                kind="pdf",
                result_path=result_path,
                result=result,
                installed_to=str(result.get("draftPath") or "") or None,
                log=["--- restored review draft ---"],
            )

    def _restore_analyses(self) -> None:
        """Keep completed analysis reports available across workbench restarts."""
        for metadata_path in self.analyses_dir.glob("*/metadata.json"):
            report_path = metadata_path.parent / "report.md"
            if not report_path.is_file() or not re.fullmatch(r"[0-9a-f]{32}", metadata_path.parent.name):
                continue
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
                report = report_path.read_text(encoding="utf-8")
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(metadata, dict):
                continue
            timestamp = report_path.stat().st_mtime
            analysis_id = metadata_path.parent.name
            self.analysis_jobs[analysis_id] = AnalysisJob(
                id=analysis_id,
                target_kind=str(metadata.get("targetKind") or ""),
                target_id=str(metadata.get("targetId") or ""),
                profile=str(metadata.get("profile") or ""),
                instruction=str(metadata.get("instruction") or ""),
                status="succeeded",
                log=["已恢复此前完成的整课分析报告。"],
                report=report,
                progress=1,
                total=1,
                source_revision=str(metadata.get("sourceRevision") or ""),
                started_at=timestamp,
                finished_at=timestamp,
            )

        for metadata_path in self.analyses_dir.glob("batch-*/metadata.json"):
            report_path = metadata_path.parent / "report.md"
            if not report_path.is_file():
                continue
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
                report = report_path.read_text(encoding="utf-8")
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(metadata, dict):
                continue
            analysis_id = str(metadata.get("id") or metadata_path.parent.name[len("batch-"):])
            targets = metadata.get("targets", [])
            target_reports: dict[str, str] = {}
            for sub_md in metadata_path.parent.glob("*.md"):
                if sub_md.name != "report.md":
                    sub_key = sub_md.stem.replace("_", ":", 1)
                    target_reports[sub_key] = sub_md.read_text(encoding="utf-8")
            self.batch_analysis_jobs[analysis_id] = BatchAnalysisJob(
                id=analysis_id,
                targets=targets,
                profile=str(metadata.get("profile") or ""),
                instruction=str(metadata.get("instruction") or ""),
                status="succeeded",
                progress=len(targets),
                total=len(targets),
                overall_report=report,
                target_reports=target_reports,
                target_statuses=metadata.get("targetStatuses", {}),
                started_at=report_path.stat().st_mtime,
                finished_at=report_path.stat().st_mtime,
                log=["已恢复此前完成的批量整课分析报告。"],
            )

    # ---- config ----

    def load_config(self) -> tuple[dict[str, Any], Path | None]:
        return load_config_file(self.config_path)

    def describe_config(self) -> dict[str, Any]:
        config, path = self.load_config()
        names = list_profiles(config)
        availability = _profile_availability_map(config)
        text_profiles = [
            _describe_profile(
                name,
                config["textProfiles"][name],
                availability.get(("text", name)),
            )
            for name in names["text"]
        ]
        asr_profiles = [
            _describe_profile(
                name,
                config["asrProfiles"][name],
                availability.get(("asr", name)),
            )
            for name in names["asr"]
        ]
        vision_pipelines = _describe_vision_pipelines(config, availability)
        return {
            "configPath": str(path) if path else None,
            "coursesDir": str(self.courses_dir),
            "availabilityCheckedAt": int(time.time()),
            "languages": list(SUPPORTED_LANGUAGE_CODES),
            "defaultTextProfile": str(config.get("defaultTextProfile") or ""),
            "defaultAsrProfile": str(config.get("defaultAsrProfile") or ""),
            "defaultVisionPipeline": str(config.get("defaultVisionPipeline") or ""),
            "languageRouting": dict(config.get("asrLanguageProfiles") or {}),
            "textProfiles": text_profiles,
            "asrProfiles": asr_profiles,
            "visionPipelines": vision_pipelines,
        }

    def known_profile(self, family: str, name: str) -> bool:
        """A profile the browser named must already exist in the trusted config."""
        if not name:
            return False
        config, _ = self.load_config()
        return name in list_profiles(config)[family]

    # ---- GPU status ----

    def gpu_status(self) -> dict[str, Any]:
        now = time.time()
        with self.lock:
            cached = getattr(self, "_gpu_status_cache", None)
            cache_time = getattr(self, "_gpu_status_time", 0.0)
            if cached is not None and (now - cache_time) < 2.0:
                return cached
        status = _probe_gpu_status(self.workspace)
        with self.lock:
            self._gpu_status_cache = status
            self._gpu_status_time = now
        return status

    # ---- local model services ----

    def local_models(self) -> dict[str, Any]:
        def describe(service: tuple[str, str, str, str, str]) -> dict[str, Any]:
            name, label, role, base_url, expected_model = service
            availability = _local_http_availability(
                {"kind": "openai-compat", "baseUrl": base_url, "model": expected_model}
            )
            return {
                "name": name,
                "label": label,
                "role": role,
                "baseUrl": base_url,
                "model": expected_model,
                "available": bool(availability.get("available")),
                "statusText": str(availability.get("statusText") or "状态未知"),
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(LOCAL_MODEL_SERVICES)) as pool:
            services = list(pool.map(describe, LOCAL_MODEL_SERVICES))
        start_script = LOCAL_MODELS_ROOT / "scripts" / "start_models.sh"
        stop_script = LOCAL_MODELS_ROOT / "scripts" / "stop_models.sh"
        with self.lock:
            controls = {name: job.snapshot() for name, job in self.model_control_jobs.items()}
            history = [job.snapshot() for job in self.model_control_history[-20:]]
        for service in services:
            service["control"] = controls.get(service["name"])
        return {
            "services": services,
            "ready": sum(1 for item in services if item["available"]),
            "total": len(services),
            "canStart": start_script.is_file(),
            "canStop": stop_script.is_file(),
            "controls": controls,
            "history": history,
        }

    def control_local_models(self, action: str, service: str = "all") -> dict[str, Any]:
        if action not in {"start", "stop"}:
            raise ValueError("Local model action must be start or stop.")
        script = LOCAL_MODELS_ROOT / "scripts" / f"{action}_models.sh"
        if not script.is_file():
            raise ValueError(f"Local model {action} script is not installed.")
        if service != "all" and service not in LOCAL_MODEL_SCRIPT_NAMES:
            raise ValueError("Unknown local model service.")
        targets = list(LOCAL_MODEL_SCRIPT_NAMES) if service == "all" else [service]
        jobs = [self._start_model_control(action, target, script) for target in targets]
        return {"jobs": [job.snapshot() for job in jobs]}

    def _start_model_control(self, action: str, service: str, script: Path) -> ModelControlJob:
        previous: ModelControlJob | None = None
        with self.lock:
            active = self.model_control_jobs.get(service)
            if active and active.status == "running":
                if active.action == action:
                    return active
                if action == "stop" and active.action == "start":
                    previous = active
                    active.status = "cancelling"
                    if active.process is not None:
                        active.process.terminate()
                else:
                    raise ValueError(f"A {service} model action is still running.")
            job = ModelControlJob(id=uuid.uuid4().hex, service=service, action=action)
            self.model_control_jobs[service] = job
            self.model_control_history.append(job)
            if len(self.model_control_history) > 40:
                del self.model_control_history[: len(self.model_control_history) - 40]
        threading.Thread(
            target=self._run_model_control, args=(job, script, previous), daemon=True
        ).start()
        return job

    def _run_model_control(
        self, job: ModelControlJob, script: Path, previous: ModelControlJob | None = None
    ) -> None:
        try:
            if previous is not None:
                deadline = time.time() + 10
                while previous.finished_at is None and time.time() < deadline:
                    time.sleep(0.05)
            if job.status == "cancelling":
                job.status = "cancelled"
                job.exit_code = -15
                return
            process = subprocess.Popen(
                ["bash", str(script), LOCAL_MODEL_SCRIPT_NAMES[job.service]],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=str(LOCAL_MODELS_ROOT),
                env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            )
            job.process = process
            if job.status == "cancelling":
                process.terminate()
            assert process.stdout is not None
            try:
                for line in process.stdout:
                    with self.lock:
                        job.log.append(line.rstrip())
                        if len(job.log) > MAX_LOG_LINES:
                            del job.log[: len(job.log) - MAX_LOG_LINES]
            finally:
                process.stdout.close()
            job.exit_code = process.wait()
            job.status = (
                "cancelled" if job.status == "cancelling"
                else "succeeded" if job.exit_code == 0
                else "failed"
            )
        except OSError as exc:
            job.log.append(f"Could not run local model control: {exc}")
            job.status = "failed"
            job.exit_code = 1
        finally:
            job.finished_at = time.time()

    # ---- uploads ----

    def store_upload(self, filename: str, data: bytes) -> dict[str, Any]:
        filename = unquote(filename)
        suffix = Path(filename).suffix.lower()
        if suffix not in UPLOAD_EXTENSIONS:
            raise ValueError(
                f"Unsupported upload type {suffix!r}. Use audio/video media or PDF."
            )
        if suffix == ".pdf" and not data.lstrip().startswith(b"%PDF-"):
            raise ValueError("The uploaded .pdf does not have a PDF file signature.")
        upload_id = uuid.uuid4().hex
        # The stored name is generated, not taken from the request: an uploaded
        # filename is attacker-controlled text and must never reach a path.
        target = self.uploads_dir / f"{upload_id}{suffix}"
        target.write_bytes(data)
        # Remember the name the person chose so an untitled build is named after
        # their file rather than after a random id.
        (self.uploads_dir / f"{upload_id}.origin").write_text(
            Path(filename).name, encoding="utf-8"
        )
        return {
            "uploadId": upload_id,
            "originalName": Path(filename).name,
            "storedName": target.name,
            "bytes": len(data),
            "kind": "pdf" if suffix == ".pdf" else "audio",
        }

    def upload_path(self, upload_id: str, *, kind: str | None = None) -> Path:
        if not upload_id or not upload_id.isalnum() or len(upload_id) != 32:
            raise ValueError("Unknown upload.")
        for candidate in self.uploads_dir.glob(f"{upload_id}.*"):
            if candidate.suffix.lower() in UPLOAD_EXTENSIONS:
                actual = "pdf" if candidate.suffix.lower() in DOCUMENT_UPLOAD_EXTENSIONS else "audio"
                if kind and kind != actual:
                    raise ValueError(f"This upload is {actual}, not {kind}.")
                return candidate
        raise ValueError("Unknown upload.")

    def upload_title(self, upload_id: str) -> str:
        return Path(self.upload_original_name(upload_id)).stem

    def upload_original_name(self, upload_id: str) -> str:
        origin = self.uploads_dir / f"{upload_id}.origin"
        if origin.is_file():
            return Path(origin.read_text(encoding="utf-8").strip()).name
        return ""

    # ---- builds ----

    def start_build(self, payload: dict[str, Any], *, defer: bool = False) -> BuildJob:
        audio = self.upload_path(str(payload.get("uploadId") or ""), kind="audio")

        upload_id = str(payload.get("uploadId") or "")
        title = (
            str(payload.get("title") or "").strip()
            or self.upload_title(upload_id)
            or audio.stem
        )
        if len(title) > 200:
            raise ValueError("Title is too long.")

        language = str(payload.get("language") or "auto").strip()
        if language != "auto" and language not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(f"Unsupported language {language!r}.")

        text_profile = str(payload.get("textProfile") or "").strip()
        asr_profile = str(payload.get("asrProfile") or "").strip()
        enrich = bool(payload.get("enrich", True))

        if enrich and not self.known_profile("text", text_profile):
            raise ValueError("Pick a text profile defined in the provider config.")
        if asr_profile and not self.known_profile("asr", asr_profile):
            raise ValueError("Pick an ASR profile defined in the provider config.")

        job_id = uuid.uuid4().hex
        work_dir = self.builds_dir / job_id
        out_path = work_dir / f"{safe_filename(title)}.zip"

        argv = [
            sys.executable,
            str(BUILD_SCRIPT),
            "--audio", str(audio),
            "--title", title,
            "--out", str(out_path),
            "--work-dir", str(work_dir / "work"),
            "--force",
            "--language", language,
        ]
        if self.config_path:
            argv += ["--config", str(self.config_path)]
        if asr_profile:
            argv += ["--asr-profile", asr_profile]
        if enrich:
            argv += ["--profile", text_profile]
        else:
            argv.append("--no-enrich")
        if payload.get("strictQuality"):
            argv.append("--strict-quality")
        if payload.get("noNormalize"):
            argv.append("--no-normalize")
        if payload.get("keepGoing"):
            argv.append("--keep-going")

        job = BuildJob(
            id=job_id, title=title, argv=argv, out_path=out_path, work_dir=work_dir,
            status="queued" if defer else "running",
        )
        with self.lock:
            self.jobs[job_id] = job
        if not defer:
            threading.Thread(target=self._run_job, args=(job,), daemon=True).start()
        return job

    # ---- PDF documents ----

    def start_pdf_build(self, payload: dict[str, Any], *, defer: bool = False) -> BuildJob:
        """Start the automatic half of the PDF pipeline.

        The page selects a named pipeline from the trusted config. It never sends
        an endpoint, model or command. The resulting exam/lexicon directory is a
        review draft, not silently installed content.
        """
        upload_id = str(payload.get("uploadId") or "")
        pdf = self.upload_path(upload_id, kind="pdf")
        title = str(payload.get("title") or "").strip() or self.upload_title(upload_id) or pdf.stem
        if len(title) > 200:
            raise ValueError("Title is too long.")

        document_kind = str(payload.get("documentKind") or "auto").strip()
        if document_kind not in {"auto", "exam", "grammar", "word", "document"}:
            raise ValueError("documentKind must be auto, exam, grammar, word, or document.")
        raw_level = str(payload.get("level") or "auto").strip()
        level = "auto" if raw_level.lower() == "auto" else raw_level.upper()
        if level not in {"auto", "N1", "N2", "N3", "N4", "N5"}:
            raise ValueError("PDF level must be auto or N1-N5.")

        config, resolved_config = self.load_config()
        pipelines = {item["name"]: item for item in _vision_pipeline_entries(config)}
        pipeline_name = str(payload.get("visionPipeline") or "").strip()
        if not pipeline_name:
            pipeline_name = str(config.get("defaultVisionPipeline") or "").strip()
        if not pipeline_name or pipeline_name not in pipelines:
            raise ValueError("Pick a vision pipeline defined in the provider config.")
        profile_names = pipelines[pipeline_name]["profiles"]
        if not profile_names:
            raise ValueError(f"Vision pipeline {pipeline_name!r} has no profiles.")

        job_id = uuid.uuid4().hex
        work_dir = self.builds_dir / job_id
        artifact_dir = work_dir / "artifact"
        result_path = work_dir / "build-result.json"
        argv = [
            sys.executable,
            str(PDF_BUILD_SCRIPT),
            "--pdf", str(pdf),
            "--source-name", self.upload_original_name(upload_id) or pdf.name,
            "--title", title,
            "--out", str(artifact_dir),
            "--result", str(result_path),
            "--kind", document_kind,
            "--level", level,
            "--vision-profile", profile_names[0],
        ]
        if resolved_config:
            argv += ["--config", str(resolved_config)]
        for profile in profile_names[1:]:
            argv += ["--review-profile", profile]

        job = BuildJob(
            id=job_id,
            title=title,
            argv=argv,
            out_path=work_dir / "(no bundle)",
            work_dir=work_dir,
            kind="pdf",
            result_path=result_path,
            status="queued" if defer else "running",
        )
        with self.lock:
            self.jobs[job_id] = job
        if not defer:
            threading.Thread(target=self._run_job, args=(job,), daemon=True).start()
        return job

    def start_batch_build(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate a group of uploads, then run their builds one at a time."""
        source = str(payload.get("source") or "").strip()
        if source not in {"audio", "pdf"}:
            raise ValueError("Batch source must be audio or pdf.")
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("A batch needs at least one uploaded file.")
        if len(items) > MAX_BATCH_FILES:
            raise ValueError(f"A batch can contain at most {MAX_BATCH_FILES} files.")

        shared = {key: value for key, value in payload.items() if key not in {"source", "items"}}
        jobs: list[BuildJob] = []
        try:
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("Every batch item must be an object.")
                item_payload = dict(shared)
                item_payload["uploadId"] = str(item.get("uploadId") or "")
                item_payload["title"] = str(item.get("title") or "").strip()
                job = (
                    self.start_pdf_build(item_payload, defer=True)
                    if source == "pdf"
                    else self.start_build(item_payload, defer=True)
                )
                jobs.append(job)
        except Exception:
            with self.lock:
                for job in jobs:
                    self.jobs.pop(job.id, None)
            raise

        batch_id = uuid.uuid4().hex
        for index, job in enumerate(jobs, start=1):
            job.batch_id = batch_id
            job.batch_index = index
            job.batch_size = len(jobs)
            self._append(job, f"--- queued ({index}/{len(jobs)}) ---")
        threading.Thread(target=self._run_batch, args=(jobs,), daemon=True).start()
        return {"batchId": batch_id, "jobs": [job.snapshot() for job in jobs]}

    def _run_batch(self, jobs: list[BuildJob]) -> None:
        for job in jobs:
            with self.lock:
                if self.shutting_down and job.status == "queued":
                    job.status = "cancelled"
                    job.finished_at = time.time()
                if job.status == "cancelled":
                    continue
                job.status = "running"
                job.started_at = time.time()
            self._append(job, f"--- batch item {job.batch_index}/{job.batch_size} started ---")
            self._run_job(job)

    # ---- online video ----

    def probe_video(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Describe a video page for the UI, without starting anything.

        ``parse_media_url`` is the validation boundary: everything below this line
        uses the reference it returns, never the string the browser sent.
        """
        ref = parse_media_url(payload.get("url"))
        available = ytdlp_available()
        info: dict[str, Any] = {
            "provider": ref.provider,
            "control": ref.control,
            "videoId": ref.video_id,
            "pageUrl": ref.page_url,
            "embedUrl": ref.embed_url,
            "ytdlpAvailable": available,
            "title": "",
            "durationSec": 0.0,
            "uploader": "",
            "subtitles": [],
            "ytdlpHint": "" if available else (
                "没有找到 yt-dlp，无法读取站点字幕或做本地转写。安装：pip install yt-dlp"
            ),
        }
        if not available:
            return info
        try:
            # A bounded timeout: this runs on the request thread, and a hung probe
            # would otherwise hold a studio connection open indefinitely.
            probed = probe_media(ref.page_url, timeout=60.0)
        except MediaSourceError as exc:
            info["error"] = str(exc)
            return info
        info.update({
            "title": probed.get("title", ""),
            "durationSec": probed.get("durationSec", 0.0),
            "uploader": probed.get("uploader", ""),
            "subtitles": probed.get("subtitles", []),
        })
        return info

    def start_video_build(self, payload: dict[str, Any]) -> BuildJob:
        """Start an online-video build from fields this server has validated itself.

        Every argv element below is either a literal, a profile name checked against
        the trusted config, or a value rebuilt by our own code from a parsed URL. The
        request body never describes a provider, a command, a model or a path — that
        is the boundary PROJECT_STRUCTURE.md section 12.2 sets, and a URL heading for
        a subprocess is exactly the kind of input that erodes it.
        """
        ref = parse_media_url(payload.get("url"))

        title = str(payload.get("title") or "").strip()
        if len(title) > 200:
            raise ValueError("Title is too long.")
        name = safe_filename(str(payload.get("name") or "").strip() or title or ref.video_id or "video-course")

        language = str(payload.get("language") or "auto").strip()
        if language != "auto" and language not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(f"Unsupported language {language!r}.")

        transcript = str(payload.get("transcript") or "auto").strip()
        if transcript not in {"verified", "auto", "subs", "asr"}:
            raise ValueError("transcript must be one of: verified, auto, subs, asr.")

        text_profile = str(payload.get("textProfile") or "").strip()
        asr_profile = str(payload.get("asrProfile") or "").strip()
        enrich = bool(payload.get("enrich", True))
        if enrich and not self.known_profile("text", text_profile):
            raise ValueError("Pick a text profile defined in the provider config.")
        if asr_profile and not self.known_profile("asr", asr_profile):
            raise ValueError("Pick an ASR profile defined in the provider config.")

        job_id = uuid.uuid4().hex
        work_dir = self.builds_dir / job_id
        destination = self.courses_dir / name

        argv = [
            sys.executable,
            str(VIDEO_BUILD_SCRIPT),
            # The canonical URL our own parser rebuilt, not the browser's string.
            "--url", ref.page_url,
            "--name", name,
            "--courses-dir", str(self.courses_dir),
            "--work-dir", str(work_dir),
            "--language", language,
            "--transcript", transcript,
            "--force",
        ]
        if title:
            argv += ["--title", title]
        if self.config_path:
            argv += ["--config", str(self.config_path)]
        if enrich:
            argv += ["--profile", text_profile]
        else:
            argv.append("--no-enrich")
        if asr_profile:
            argv += ["--asr-profile", asr_profile]
        sub_langs = _clean_sub_langs(payload.get("subLangs"))
        if sub_langs:
            argv += ["--sub-langs", sub_langs]
        clip = _clean_clip(payload.get("clipStart"), payload.get("clipEnd"))
        if clip:
            argv += ["--clip", clip[0], clip[1]]
        if not payload.get("allowAudioFetch", True):
            argv.append("--no-audio-fetch")
        if payload.get("strictQuality"):
            argv.append("--strict-quality")
        if payload.get("keepGoing"):
            argv.append("--keep-going")

        job = BuildJob(
            id=job_id,
            title=title or name,
            argv=argv,
            # A video build has no ZIP; this path is only ever reported, never read.
            out_path=work_dir / "(no bundle)",
            work_dir=work_dir,
            kind="video",
        )
        job.installed_to = str(destination)
        with self.lock:
            self.jobs[job_id] = job
        threading.Thread(target=self._run_job, args=(job,), daemon=True).start()
        return job

    def _run_job(self, job: BuildJob) -> None:
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
        # The studio's own session token must not be inherited by a build, which
        # runs third-party model code and CLI tools.
        env.pop("DICTATION_SESSION_TOKEN", None)

        if job.status == "cancelling":
            job.status = "cancelled"
            job.finished_at = time.time()
            return

        try:
            process = subprocess.Popen(
                job.argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                cwd=str(PROJECT_DIR),
            )
        except OSError as exc:
            self._append(job, f"Could not start the build: {exc}")
            job.status = "failed"
            job.finished_at = time.time()
            return

        job.process = process
        if job.status == "cancelling":
            process.terminate()
        assert process.stdout is not None
        for line in process.stdout:
            # faster-whisper redraws progress with \r; keep only the latest frame.
            self._append(job, line.rstrip("\n").split("\r")[-1])
        code = process.wait()
        job.exit_code = code
        job.finished_at = time.time()
        if job.status == "cancelling":
            job.status = "cancelled"
        else:
            if code == 0 and job.result_path and job.result_path.is_file():
                try:
                    loaded = json.loads(job.result_path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        job.result = loaded
                        job.installed_to = str(loaded.get("draftPath") or "") or None
                except (OSError, json.JSONDecodeError) as exc:
                    self._append(job, f"Could not read build result: {exc}")
                    code = 1
                    job.exit_code = code
            job.status = (
                "needs_review"
                if code == 0 and bool((job.result or {}).get("reviewRequired"))
                else "succeeded" if code == 0 else "failed"
            )
            if job.status == "succeeded" and job.kind == "audio" and job.out_path and job.out_path.is_file() and not job.installed_to:
                try:
                    destination = install_bundle(
                        job.out_path,
                        courses_dir=self.courses_dir,
                        course_name=None,
                        force=True,
                    )
                    job.installed_to = str(destination)
                    self._append(job, f"Auto-installed into course library: {destination}")
                except Exception as exc:
                    self._append(job, f"Auto-installation note: {exc}")
        self._append(job, f"--- {job.status} (exit {code}) ---")

    def _append(self, job: BuildJob, line: str) -> None:
        if not line.strip():
            return
        with self.lock:
            job.log.append(line)
            if len(job.log) > MAX_LOG_LINES:
                del job.log[: len(job.log) - MAX_LOG_LINES]

    def job(self, job_id: str) -> BuildJob:
        with self.lock:
            job = self.jobs.get(job_id)
        if job is None:
            raise ValueError("Unknown build.")
        return job

    def cancel(self, job_id: str) -> BuildJob:
        job = self.job(job_id)
        if job.status == "queued":
            job.status = "cancelled"
            job.finished_at = time.time()
            self._append(job, "--- cancelled while queued ---")
        elif job.status == "running":
            job.status = "cancelling"
            if job.process is not None:
                job.process.terminate()
        return job

    def install(self, job_id: str, name: str | None) -> dict[str, Any]:
        job = self.job(job_id)
        if job.status not in ("succeeded", "needs_review"):
            raise ValueError("Only a finished build can be installed.")
        if job.kind == "pdf":
            draft_path = Path(job.result.get("draftPath") or "") if isinstance(job.result, dict) else None
            if not draft_path or not draft_path.exists():
                raise ValueError("PDF draft directory does not exist.")
            kind = job.result.get("kind")
            slug = (name or "").strip() or job.result.get("slug") or draft_path.name
            if kind in {"grammar", "word"}:
                from lexicon_import import assemble_pack, load_pages, load_registry, parse_units_file
                from lexicon_schema import audit_pack
                units = parse_units_file((draft_path / "units.txt").read_text(encoding="utf-8"))
                meta = json.loads((draft_path / "pack-meta.json").read_text(encoding="utf-8"))
                registry = load_registry(draft_path / "entry-keys.json", slug)
                pages = load_pages(draft_path / "pages")
                pack, recon = assemble_pack(pages, units, registry, meta, accept_new_keys=True)
                audit = audit_pack(pack)
                if audit["summary"]["errors"] > 0 or not recon.get("ok"):
                    raise ValueError(f"Lexicon pack validation failed: {audit['summary']['errors']} errors")
                dest_dir = PROJECT_DIR / "lexicon" / slug
                dest_dir.mkdir(parents=True, exist_ok=True)
                write_json(dest_dir / "pack.json", pack)
                job.installed_to = str(dest_dir)
                return {"installedTo": str(dest_dir), "manifest": str(dest_dir / "pack.json")}
            elif kind == "exam":
                from exam_import import assemble_exam, load_pages as load_exam_pages, parse_answer_key
                from exam_store import check_exam_qualification
                key = parse_answer_key((draft_path / "answer-key.txt").read_text(encoding="utf-8"))
                meta = json.loads((draft_path / "exam-meta.json").read_text(encoding="utf-8"))
                pages = load_exam_pages(draft_path / "pages")
                exam = assemble_exam(pages, key, meta)
                qualified, reasons = check_exam_qualification(exam)
                if not qualified:
                    raise ValueError(f"Exam qualification failed: {'; '.join(reasons)}")
                dest_dir = PROJECT_DIR / "exams" / slug
                dest_dir.mkdir(parents=True, exist_ok=True)
                write_json(dest_dir / "exam.json", exam)
                job.installed_to = str(dest_dir)
                return {"installedTo": str(dest_dir), "manifest": str(dest_dir / "exam.json")}
            else:
                raise ValueError(f"Cannot install document kind: {kind}")
        if job.kind == "video":
            # build_video_course.py writes straight into courses/: there is no ZIP to
            # install, and demanding one would fail a build that already succeeded.
            return {"installedTo": job.installed_to or str(self.courses_dir),
                    "manifest": str(Path(job.installed_to or self.courses_dir) / "manifest.json"),
                    "alreadyInstalled": True}
        if not job.out_path.is_file():
            raise ValueError("The build produced no bundle.")
        destination = install_bundle(
            job.out_path,
            courses_dir=self.courses_dir,
            course_name=(name or "").strip() or None,
            force=True,
        )
        job.installed_to = str(destination)
        return {"installedTo": str(destination), "manifest": str(destination / "manifest.json")}

    def courses(self) -> list[dict[str, Any]]:
        rows = list_courses(self.courses_dir)
        # Content aggregation (F03): unify courses, exams, and lexicon under single library
        root_dir = self.courses_dir.parent
        lexicon_dir = root_dir / "lexicon"
        if lexicon_dir.is_dir():
            for d in sorted(lexicon_dir.iterdir()):
                if not d.is_dir() or d.name.startswith("."):
                    continue
                try:
                    from studio_artifacts import resolve_lexicon_pack_path
                    p = resolve_lexicon_pack_path(d)
                except Exception:
                    p = d / "pack.json"
                if p and p.is_file():
                    try:
                        data = json.loads(p.read_text(encoding="utf-8"))
                        entries = data.get("entries") or []
                        level = data.get("level") or ("N1" if "N1" in d.name else ("N2" if "N2" in d.name else ""))
                        rows.append({
                            "name": d.name,
                            "title": data.get("title") or d.name,
                            "sentences": len(entries),
                            "category": "pdf",
                            "categoryName": "PDF课程",
                            "subcategory": "textbook",
                            "subcategoryName": "课本和课本PDF",
                            "level": level,
                            "kind": "lexicon",
                            "sourceKind": "pdf",
                            "status": "passed",
                            "errors": 0,
                            "warnings": 0,
                        })
                    except Exception:
                        pass
        exams_dir = root_dir / "exams"
        if exams_dir.is_dir():
            for d in sorted(exams_dir.iterdir()):
                if not d.is_dir() or d.name.startswith("."):
                    continue
                try:
                    from studio_artifacts import resolve_exam_manifest_path
                    p = resolve_exam_manifest_path(d)
                except Exception:
                    p = d / "exam.json"
                if p and p.is_file():
                    try:
                        data = json.loads(p.read_text(encoding="utf-8"))
                        q_count = data.get("questionCount") or 0
                        level = data.get("level") or ("N1" if "-N1" in d.name else ("N2" if "-N2" in d.name else ""))
                        rows.append({
                            "name": d.name,
                            "title": data.get("title") or d.name,
                            "sentences": q_count,
                            "category": "pdf",
                            "categoryName": "PDF课程",
                            "subcategory": "jlpt",
                            "subcategoryName": "JLPT真题",
                            "level": level,
                            "kind": "exam",
                            "sourceKind": "pdf",
                            "status": "passed",
                            "errors": 0,
                            "warnings": 0,
                        })
                    except Exception:
                        pass
        return rows

    @staticmethod
    def _course_review_progress(manifest: dict[str, Any]) -> dict[str, int]:
        sentences = [item for item in manifest.get("sentences", []) if isinstance(item, dict)]
        metadata = manifest.get("buildMetadata") if isinstance(manifest.get("buildMetadata"), dict) else {}
        edits = metadata.get("workbenchEdits") if isinstance(metadata.get("workbenchEdits"), dict) else {}
        recorded = edits.get("sentenceIds") if isinstance(edits.get("sentenceIds"), list) else []
        known_ids = {str(item.get("id") or "") for item in sentences}
        reviewed = len({str(value) for value in recorded} & known_ids)
        if not recorded:
            reviewed = min(len(sentences), int(edits.get("count") or 0))
        return {"reviewed": reviewed, "total": len(sentences), "remaining": max(0, len(sentences) - reviewed)}

    def review_targets(self, filter_mode: str = "") -> dict[str, Any]:
        """List review targets. When filter_mode='issues', only genuine issues or explicit manual review requests are returned."""
        targets: list[dict[str, Any]] = []
        reviewed_drafts: list[dict[str, Any]] = []
        with self.lock:
            draft_jobs = [job for job in self.jobs.values() if job.status == "needs_review"]
        for job in sorted(draft_jobs, key=lambda item: item.finished_at or item.started_at, reverse=True):
            try:
                summary = self.draft(job.id)
            except ValueError:
                continue
            progress = summary["review"]
            item_data = {
                "targetKind": "draft",
                "targetId": job.id,
                "title": summary["title"],
                "kind": summary["kind"],
                "level": summary["level"],
                "reviewed": progress["reviewed"],
                "total": progress["total"],
                "remaining": progress["remaining"],
                "updatedAt": job.finished_at or job.started_at,
            }
            if progress["remaining"] <= 0:
                reviewed_drafts.append(item_data)
            else:
                targets.append(item_data)

        for listed in self.courses():
            name = str(listed.get("name") or "")
            try:
                path = self._course_manifest_path(name)
                manifest = json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError, OSError, json.JSONDecodeError):
                continue
            if not isinstance(manifest, dict):
                continue

            progress = self._course_review_progress(manifest)
            if progress["remaining"] <= 0:
                continue

            report = audit_manifest(manifest, require_enrichment=False)
            has_blocking = any(issue.get("severity") == "error" for issue in report.get("issues", []))
            review_requested = bool(manifest.get("manualReviewRequested") or manifest.get("reviewRequired"))
            critical_issues = [
                i for i in report.get("issues", [])
                if i.get("code") in {"sentence.transcript_review_flag", "manifest.transcript_mismatch"}
            ]

            if filter_mode == "issues" and not (has_blocking or review_requested or critical_issues):
                continue

            issue_count = len(report.get("issues", []))
            total_sentences = len(manifest.get("sentences", []))
            targets.append({
                "targetKind": "course",
                "targetId": name,
                "title": str(manifest.get("title") or name),
                "kind": "installed",
                "category": str(listed.get("category") or ""),
                "categoryName": str(listed.get("categoryName") or ""),
                "subcategory": str(listed.get("subcategory") or ""),
                "subcategoryName": str(listed.get("subcategoryName") or ""),
                "level": str(listed.get("level") or ""),
                "reviewed": progress["reviewed"],
                "total": total_sentences,
                "remaining": progress["remaining"],
                "qualityStatus": report.get("status"),
                "issues": report.get("issues", []),
                "issueCount": issue_count,
                "legacyProgress": progress,
                "updatedAt": path.stat().st_mtime,
            })
        return {
            "targets": targets,
            "reviewedDrafts": reviewed_drafts,
            "drafts": sum(1 for item in targets if item["targetKind"] == "draft"),
            "courses": sum(1 for item in targets if item["targetKind"] == "course"),
            "reviewed": len(reviewed_drafts),
        }

    # ---- review-draft editor ----

    def _draft_context(self, job_id: str) -> tuple[BuildJob, Path, Path]:
        job = self.job(job_id)
        if job.status != "needs_review" or not isinstance(job.result, dict):
            raise ValueError("Only a finished review draft can be edited.")
        artifact_root = (job.work_dir / "artifact").resolve()
        draft_value = str(job.result.get("draftPath") or "").strip()
        draft_root = Path(draft_value).resolve() if draft_value else artifact_root
        if draft_root != artifact_root and artifact_root not in draft_root.parents:
            raise ValueError("The draft path is outside this build.")
        pages_dir = (draft_root / "pages").resolve()
        if not pages_dir.is_dir() or (pages_dir != artifact_root and artifact_root not in pages_dir.parents):
            raise ValueError("This review draft has no editable pages.")
        return job, artifact_root, pages_dir

    def _draft_page_path(self, job_id: str, page_name: str) -> tuple[BuildJob, Path, Path]:
        job, artifact_root, pages_dir = self._draft_context(job_id)
        decoded = unquote(str(page_name or "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]+\.json", decoded):
            raise ValueError("Invalid draft page name.")
        path = (pages_dir / decoded).resolve()
        if path.parent != pages_dir or not path.is_file():
            raise ValueError("Draft page was not found.")
        return job, artifact_root, path

    def draft(self, job_id: str) -> dict[str, Any]:
        job, _, pages_dir = self._draft_context(job_id)
        pages = []
        for path in sorted(
            pages_dir.glob("*.json"),
            key=lambda item: [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", item.name)],
        ):
            try:
                document = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                document = {}
            blocks = document.get("blocks") if isinstance(document, dict) else []
            issues = document.get("issues") if isinstance(document, dict) else []
            pages.append({
                "name": path.name,
                "page": document.get("page") if isinstance(document, dict) else None,
                "blocks": len(blocks) if isinstance(blocks, list) else 0,
                "issues": len(issues) if isinstance(issues, list) else 0,
            })
        progress_path = job.work_dir / "review-progress.json"
        reviewed_names: set[str] = set()
        if progress_path.is_file():
            try:
                progress_data = json.loads(progress_path.read_text(encoding="utf-8-sig"))
                reviewed_names = {
                    str(value) for value in progress_data.get("reviewedPages", [])
                } if isinstance(progress_data, dict) else set()
            except (OSError, json.JSONDecodeError):
                pass
        existing_names = {page["name"] for page in pages}
        reviewed_count = len(reviewed_names & existing_names)
        return {
            "jobId": job.id,
            "title": job.title,
            "kind": str((job.result or {}).get("kind") or job.kind),
            "level": str((job.result or {}).get("level") or ""),
            "pages": pages,
            "reviewRequired": True,
            "review": {
                "reviewed": reviewed_count,
                "total": len(pages),
                "remaining": max(0, len(pages) - reviewed_count),
            },
        }

    def draft_page(self, job_id: str, page_name: str) -> dict[str, Any]:
        job, artifact_root, path = self._draft_page_path(job_id, page_name)
        try:
            document = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("The draft page JSON is unreadable.") from exc
        if not isinstance(document, dict):
            raise ValueError("The draft page must be a JSON object.")
        page_number = document.get("page")
        source_markdown = ""
        if isinstance(page_number, int) and page_number > 0:
            source_path = artifact_root / "ocr" / "pages" / f"page-{page_number:04d}.json"
            if source_path.is_file():
                try:
                    source = json.loads(source_path.read_text(encoding="utf-8-sig"))
                    source_markdown = str(source.get("markdown") or "") if isinstance(source, dict) else ""
                except (OSError, json.JSONDecodeError):
                    pass
        return {
            "jobId": job.id,
            "name": path.name,
            "page": page_number,
            "revision": sha256_file(path),
            "document": document,
            "sourceMarkdown": source_markdown,
            "imageUrl": f"/api/drafts/{job.id}/images/{page_number}" if isinstance(page_number, int) else "",
        }

    def save_draft_page(self, job_id: str, page_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        job, _, path = self._draft_page_path(job_id, page_name)
        current_revision = sha256_file(path)
        if str(payload.get("revision") or "") != current_revision:
            raise ValueError("Draft page changed after it was opened. Reload it before saving.")
        document = payload.get("document")
        if not isinstance(document, dict):
            raise ValueError("Draft page must be a JSON object.")
        encoded = json.dumps(document, ensure_ascii=False, indent=2)
        if len(encoded) > MAX_DRAFT_PAGE_LENGTH:
            raise ValueError("Draft page is too large.")
        current = json.loads(path.read_text(encoding="utf-8-sig"))
        if document.get("page") != current.get("page"):
            raise ValueError("The page number cannot be changed.")
        backup_dir = path.parent / ".workbench-backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"{path.stem}.{current_revision[:12]}.json"
        if not backup_path.exists():
            shutil.copy2(path, backup_path)
        write_json(path, document)
        progress_path = job.work_dir / "review-progress.json"
        progress: dict[str, Any] = {}
        if progress_path.is_file():
            try:
                loaded = json.loads(progress_path.read_text(encoding="utf-8-sig"))
                if isinstance(loaded, dict):
                    progress = loaded
            except (OSError, json.JSONDecodeError):
                pass
        reviewed_pages = {
            str(value) for value in progress.get("reviewedPages", [])
        } if isinstance(progress.get("reviewedPages"), list) else set()
        reviewed_pages.add(path.name)
        progress["reviewedPages"] = sorted(reviewed_pages)
        progress["lastReviewedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_json(progress_path, progress)
        return self.draft_page(job_id, page_name)

    def revise_draft_page(self, job_id: str, page_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        detail = self.draft_page(job_id, page_name)
        if str(payload.get("revision") or "") != detail["revision"]:
            raise ValueError("Draft page changed after it was opened. Reload it before using a model.")
        instruction = str(payload.get("instruction") or "").strip()
        if not instruction or len(instruction) > 4000:
            raise ValueError("Give the model a modification instruction of 1–4000 characters.")
        profile = str(payload.get("textProfile") or "").strip()
        if not self.known_profile("text", profile):
            raise ValueError("Pick a text profile defined in the provider config.")
        config, _ = self.load_config()
        entry = config.get("textProfiles", {}).get(profile, {})
        availability = _profile_availability(entry)
        if not availability.get("available"):
            raise ValueError(f"Selected model is unavailable: {availability.get('statusText')}")
        provider_config = resolve_text_provider(config=config, profile=profile)
        if provider_config.kind in {"manual", "echo"}:
            raise ValueError("Pick an automatic text model for assisted editing.")
        provider = build_text_provider(provider_config)
        provider.preflight()
        current = payload.get("document", detail["document"])
        if not isinstance(current, dict):
            raise ValueError("The draft page for model review must be a JSON object.")
        stored = detail["document"]
        if current.get("page") != stored.get("page") or set(current) != set(stored):
            raise ValueError("The draft page identity and top-level schema cannot be changed.")
        prompt = json.dumps({
            "instruction": instruction,
            "ocrSource": detail["sourceMarkdown"],
            "currentPage": current,
        }, ensure_ascii=False)
        if len(prompt) > MAX_DRAFT_PAGE_LENGTH:
            raise ValueError("This page is too large for model-assisted editing.")
        completion = provider.complete(
            "Review one OCR-derived Japanese learning-material page. Return the complete corrected page as JSON only. "
            "Keep the same top-level schema and page number. Correct only evidence-supported text or structure. "
            "Never invent answers, translations, citations, or facts. Do not add markdown commentary.",
            prompt,
            batch_name=f"draft-{job_id[:8]}-{Path(page_name).stem}.json",
        )
        proposal = parse_jsonish(completion.text)
        if not isinstance(proposal, dict):
            raise ProviderError("The model did not return a JSON object.")
        if proposal.get("page") != current.get("page") or set(proposal) != set(current):
            raise ProviderError("The model changed the page identity or top-level schema.")
        return {
            "proposal": proposal,
            "model": completion.model or provider_config.model or profile,
            "profile": profile,
            "saved": False,
        }

    def draft_image_path(self, job_id: str, page_number: str) -> Path:
        _, artifact_root, _ = self._draft_context(job_id)
        if not str(page_number).isdigit() or not 1 <= int(page_number) <= 100_000:
            raise ValueError("Invalid draft image page.")
        path = (artifact_root / "ocr" / "images" / f"page-{int(page_number):04d}.png").resolve()
        if artifact_root not in path.parents or not path.is_file():
            raise ValueError("Draft source image was not found.")
        return path

    # ---- installed course editor ----

    def _course_manifest_path(self, name: str) -> Path:
        decoded = unquote(str(name or "")).strip()
        if not decoded or decoded in {".", ".."} or Path(decoded).name != decoded:
            raise ValueError("Invalid course name.")
        folder = (self.courses_dir / decoded).resolve()
        if folder.parent != self.courses_dir.resolve():
            raise ValueError("Invalid course name.")
        manifest_path = resolve_course_manifest_path(folder)
        if not manifest_path or not manifest_path.is_file():
            raise ValueError("Installed course was not found.")
        return manifest_path

    def course(self, name: str) -> dict[str, Any]:
        manifest_path = self._course_manifest_path(name)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("The installed course manifest is unreadable.") from exc
        if not isinstance(manifest, dict):
            raise ValueError("The installed course manifest must be an object.")
        sentences = manifest.get("sentences")
        if not isinstance(sentences, list):
            raise ValueError("The installed course has no sentence list.")
        report = audit_manifest(manifest, require_enrichment=False)
        return {
            "name": manifest_path.parent.name,
            "title": str(manifest.get("title") or ""),
            "language": manifest_language_code(manifest),
            "revision": sha256_file(manifest_path),
            "sentences": [item for item in sentences if isinstance(item, dict)],
            "quality": report,
            "review": self._course_review_progress(manifest),
        }

    def save_course_sentence(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        manifest_path = self._course_manifest_path(name)
        expected = str(payload.get("revision") or "")
        current_revision = sha256_file(manifest_path)
        if not expected or expected != current_revision:
            raise ValueError("Course changed after it was opened. Reload it before saving.")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        sentences = manifest.get("sentences")
        if not isinstance(sentences, list):
            raise ValueError("The installed course has no sentence list.")
        sentence_id = str(payload.get("sentenceId") or "")
        sentence = next(
            (item for item in sentences if isinstance(item, dict) and str(item.get("id") or "") == sentence_id),
            None,
        )
        if sentence is None:
            raise ValueError("The sentence no longer exists. Reload the course.")

        fields = payload.get("fields")
        if not isinstance(fields, dict):
            raise ValueError("Sentence fields must be an object.")
        allowed = {
            "sourceText", "translationText", "explanationText", "startTime", "endTime",
            "confidence", "contentType", "practiceEligible",
        }
        if set(fields) - allowed:
            raise ValueError("The request contains unsupported sentence fields.")
        for key in ("sourceText", "translationText", "explanationText"):
            value = str(fields.get(key) or "").strip()
            if len(value) > MAX_COURSE_FIELD_LENGTH:
                raise ValueError(f"{key} is too long.")
            if key == "sourceText" and not value:
                raise ValueError("Source text cannot be empty.")
            if key == "sourceText":
                set_source_text(sentence, value, manifest_language_code(manifest))
            elif key == "translationText":
                set_translation_text(sentence, value)
            else:
                sentence[key] = value
        for key in ("startTime", "endTime"):
            try:
                sentence[key] = float(fields[key])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{key} must be a number.") from exc
        if sentence["startTime"] < 0 or sentence["endTime"] <= sentence["startTime"]:
            raise ValueError("Time range must satisfy 0 <= start < end.")
        if "confidence" in fields and fields["confidence"] not in (None, ""):
            try:
                confidence = float(fields["confidence"])
            except (TypeError, ValueError) as exc:
                raise ValueError("confidence must be a number between 0 and 1.") from exc
            if not 0 <= confidence <= 1:
                raise ValueError("confidence must be a number between 0 and 1.")
            sentence["confidence"] = confidence
        if "contentType" in fields:
            sentence["contentType"] = str(fields["contentType"] or "dialogue")
        if "practiceEligible" in fields:
            sentence["practiceEligible"] = bool(fields["practiceEligible"])

        title = str(payload.get("title") or manifest.get("title") or "").strip()
        if not title or len(title) > 200:
            raise ValueError("Course title must contain 1–200 characters.")
        manifest["title"] = title
        language = manifest_language_code(manifest)
        manifest["transcriptText"] = transcript_text(sentences, language)
        prepared = prepare_course_manifest(manifest)
        metadata = prepared.setdefault("buildMetadata", {})
        edits = metadata.setdefault("workbenchEdits", {}) if isinstance(metadata, dict) else {}
        if isinstance(edits, dict):
            edits["count"] = int(edits.get("count") or 0) + 1
            edits["lastEditedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            sentence_ids = edits.get("sentenceIds") if isinstance(edits.get("sentenceIds"), list) else []
            edits["sentenceIds"] = sorted({str(value) for value in sentence_ids} | {sentence_id})

        report = audit_manifest(prepared, require_enrichment=False)
        prepared["quality"] = report
        backup_dir = manifest_path.parent / ".workbench-backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"manifest.{current_revision[:12]}.json"
        if not backup_path.exists():
            shutil.copy2(manifest_path, backup_path)
        write_json(manifest_path, prepared)
        write_json(manifest_path.parent / "quality-report.json", report)
        return self.course(name)

    def revise_course_sentence(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        detail = self.course(name)
        if str(payload.get("revision") or "") != detail["revision"]:
            raise ValueError("Course changed after it was opened. Reload it before using a model.")
        sentence_id = str(payload.get("sentenceId") or "")
        sentence = next(
            (item for item in detail["sentences"] if str(item.get("id") or "") == sentence_id),
            None,
        )
        if sentence is None:
            raise ValueError("The sentence no longer exists. Reload the course.")
        instruction = str(payload.get("instruction") or "").strip()
        if not instruction or len(instruction) > 4000:
            raise ValueError("Give the model a modification instruction of 1–4000 characters.")
        profile = str(payload.get("textProfile") or "").strip()
        if not self.known_profile("text", profile):
            raise ValueError("Pick a text profile defined in the provider config.")
        config, _ = self.load_config()
        entry = config.get("textProfiles", {}).get(profile, {})
        availability = _profile_availability(entry)
        if not availability.get("available"):
            raise ValueError(f"Selected model is unavailable: {availability.get('statusText')}")
        provider_config = resolve_text_provider(config=config, profile=profile)
        if provider_config.kind in {"manual", "echo"}:
            raise ValueError("Pick an automatic text model for assisted editing.")
        provider = build_text_provider(provider_config)
        provider.preflight()
        editable = {
            "sourceText": str(sentence.get("sourceText") or sentence.get("jaText") or ""),
            "translationText": str(sentence.get("translationText") or sentence.get("zhTranslation") or ""),
            "explanationText": str(sentence.get("explanationText") or ""),
        }
        supplied = payload.get("fields")
        if isinstance(supplied, dict):
            editable = {
                key: str(supplied.get(key, value) or "").strip()
                for key, value in editable.items()
            }
            if not editable["sourceText"] or any(
                len(value) > MAX_COURSE_FIELD_LENGTH for value in editable.values()
            ):
                raise ValueError("The manually edited sentence is empty or too large.")
        system_prompt = (
            "You edit one language-learning course sentence. Return JSON only, with exactly "
            "sourceText, translationText, explanationText. Preserve facts and the original language. "
            "Do not add markdown, commentary, or extra keys."
        )
        user_prompt = json.dumps(
            {"instruction": instruction, "courseLanguage": detail["language"], "current": editable},
            ensure_ascii=False,
        )
        completion = provider.complete(system_prompt, user_prompt, batch_name=f"edit-{sentence_id}.json")
        proposal = parse_jsonish(completion.text)
        if not all(key in proposal for key in editable):
            raise ProviderError("The model response did not contain all editable fields.")
        cleaned = {key: str(proposal.get(key) or "").strip() for key in editable}
        if not cleaned["sourceText"] or any(len(value) > MAX_COURSE_FIELD_LENGTH for value in cleaned.values()):
            raise ProviderError("The model returned an empty or oversized source sentence.")
        return {
            "proposal": cleaned,
            "model": completion.model or provider_config.model or profile,
            "profile": profile,
            "saved": False,
        }

    def structured_analysis(self, name: str) -> dict[str, Any]:
        manifest_path = self._course_manifest_path(name)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        current_revision = sha256_file(manifest_path)
        report = analyze_manifest(manifest, subject_id=name, existing_revision=current_revision)
        return report.to_dict()

    def apply_patch(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        manifest_path = self._course_manifest_path(name)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        current_revision = sha256_file(manifest_path)

        patch_data = payload.get("patch") or payload
        raw_ops = patch_data.get("operations") or []
        ops = []
        for op in raw_ops:
            ops.append(
                PatchOp(
                    op=str(op.get("op") or "replace_field"),
                    item_id=str(op.get("itemId") or op.get("item_id") or ""),
                    field=str(op.get("field") or ""),
                    value=str(op.get("value") or ""),
                    expected_value_hash=str(op.get("expectedValueHash") or op.get("expected_value_hash") or ""),
                    evidence_refs=list(op.get("evidenceRefs") or op.get("evidence_refs") or []),
                )
            )
        patch = Patch(
            patch_id=str(patch_data.get("patchId") or patch_data.get("patch_id") or uuid.uuid4()),
            subject_id=name,
            base_revision=str(patch_data.get("baseRevision") or patch_data.get("base_revision") or current_revision),
            operations=ops,
            issue_ids=list(patch_data.get("issueIds") or patch_data.get("issue_ids") or []),
        )
        repaired_manifest, ok, msg = apply_patch_op(manifest, patch, current_revision=current_revision)

        backup_dir = manifest_path.parent / ".workbench-backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"manifest.{current_revision[:12]}.json"
        if not backup_path.exists():
            shutil.copy2(manifest_path, backup_path)

        prepared = prepare_course_manifest(repaired_manifest)
        report = audit_manifest(prepared, require_enrichment=False)
        prepared["quality"] = report
        write_json(manifest_path, prepared)
        write_json(manifest_path.parent / "quality-report.json", report)
        new_revision = sha256_file(manifest_path)
        return {
            "success": ok,
            "message": msg,
            "patchId": patch.patch_id,
            "newRevision": new_revision,
            "course": self.course(name),
        }

    def apply_deterministic_repairs(self, name: str) -> dict[str, Any]:
        manifest_path = self._course_manifest_path(name)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        current_revision = sha256_file(manifest_path)

        repaired_manifest, ops = apply_deterministic_repairs_op(manifest)
        if ops:
            backup_dir = manifest_path.parent / ".workbench-backups"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"manifest.{current_revision[:12]}.json"
            if not backup_path.exists():
                shutil.copy2(manifest_path, backup_path)
            prepared = prepare_course_manifest(repaired_manifest)
            report = audit_manifest(prepared, require_enrichment=False)
            prepared["quality"] = report
            write_json(manifest_path, prepared)
            write_json(manifest_path.parent / "quality-report.json", report)
            new_revision = sha256_file(manifest_path)
        else:
            new_revision = current_revision

        return {
            "appliedCount": len(ops),
            "appliedOps": [op.to_dict() for op in ops],
            "newRevision": new_revision,
            "course": self.course(name),
        }

    # ---- whole-course analysis ----

    def start_analysis(self, payload: dict[str, Any]) -> AnalysisJob:
        target_kind = str(payload.get("targetKind") or "").strip()
        target_id = str(payload.get("targetId") or "").strip()
        if target_kind == "course":
            self.course(target_id)
        elif target_kind == "draft":
            self.draft(target_id)
        else:
            raise ValueError("Analysis target must be course or draft.")
        profile = str(payload.get("textProfile") or "").strip()
        if not self.known_profile("text", profile):
            raise ValueError("Pick a text profile defined in the provider config.")
        config, _ = self.load_config()
        entry = config.get("textProfiles", {}).get(profile, {})
        availability = _profile_availability(entry)
        if not availability.get("available"):
            raise ValueError(f"Selected model is unavailable: {availability.get('statusText')}")
        provider_config = resolve_text_provider(config=config, profile=profile)
        if provider_config.kind in {"manual", "echo"}:
            raise ValueError("Pick an automatic text model for whole-course analysis.")
        instruction = str(payload.get("instruction") or "").strip() or (
            "从整门课程层面检查原文准确性、同音字、翻译、讲解一致性、重复内容、结构缺失和教学质量；"
            "按影响程度列出可执行的修改建议。"
        )
        if len(instruction) > 4000:
            raise ValueError("Analysis instruction must be at most 4000 characters.")
        job = AnalysisJob(
            id=uuid.uuid4().hex,
            target_kind=target_kind,
            target_id=target_id,
            profile=profile,
            instruction=instruction,
        )
        with self.lock:
            self.analysis_jobs[job.id] = job
            if len(self.analysis_jobs) > 100:
                finished = [item for item in self.analysis_jobs.values() if item.status != "running"]
                for old in sorted(finished, key=lambda item: item.started_at)[: len(self.analysis_jobs) - 100]:
                    self.analysis_jobs.pop(old.id, None)
        threading.Thread(target=self._run_analysis, args=(job,), daemon=True).start()
        return job

    def analysis(self, analysis_id: str) -> AnalysisJob:
        with self.lock:
            job = self.analysis_jobs.get(analysis_id)
        if job is None:
            raise ValueError("Unknown whole-course analysis.")
        return job

    def _analysis_items_by_target(self, target_kind: str, target_id: str) -> tuple[str, str, list[dict[str, str]]]:
        if target_kind == "course":
            detail = self.course(target_id)
            items = []
            for index, sentence in enumerate(detail["sentences"], start=1):
                items.append({
                    "location": f"句子 {index} / {sentence.get('id', '')}",
                    "content": json.dumps(sentence, ensure_ascii=False, separators=(",", ":")),
                })
            return detail["title"], detail["revision"], items

        summary = self.draft(target_id)
        items = []
        revision = hashlib.sha256()
        for page in summary["pages"]:
            _, _, path = self._draft_page_path(target_id, page["name"])
            raw = path.read_text(encoding="utf-8-sig")
            revision.update(page["name"].encode("utf-8"))
            revision.update(sha256_file(path).encode("ascii"))
            items.append({"location": f"第 {page.get('page', '?')} 页 / {page['name']}", "content": raw})
        return summary["title"], revision.hexdigest(), items

    def _analysis_items(self, job: AnalysisJob) -> tuple[str, str, list[dict[str, str]]]:
        return self._analysis_items_by_target(job.target_kind, job.target_id)

    def _target_validation_report_path(self, target_kind: str, target_id: str) -> Path:
        if target_kind == "course":
            return self._course_manifest_path(target_id).parent / "validation-report.md"
        if target_kind == "draft":
            job, _, _ = self._draft_context(target_id)
            return job.work_dir / "validation-report.md"
        raise ValueError(f"Unknown target kind: {target_kind}")

    @staticmethod
    def _analysis_chunks(items: list[dict[str, str]]) -> list[list[dict[str, str]]]:
        expanded: list[dict[str, str]] = []
        for item in items:
            content = item["content"]
            if len(content) <= MAX_ANALYSIS_CHUNK_CHARS:
                expanded.append(item)
                continue
            pieces = (len(content) + MAX_ANALYSIS_CHUNK_CHARS - 1) // MAX_ANALYSIS_CHUNK_CHARS
            for index in range(pieces):
                expanded.append({
                    "location": f"{item['location']}（片段 {index + 1}/{pieces}）",
                    "content": content[index * MAX_ANALYSIS_CHUNK_CHARS:(index + 1) * MAX_ANALYSIS_CHUNK_CHARS],
                })
        chunks: list[list[dict[str, str]]] = []
        current: list[dict[str, str]] = []
        size = 0
        for item in expanded:
            item_size = len(item["location"]) + len(item["content"]) + 100
            if current and size + item_size > MAX_ANALYSIS_CHUNK_CHARS:
                chunks.append(current)
                current = []
                size = 0
            current.append(item)
            size += item_size
        if current:
            chunks.append(current)
        return chunks

    def _run_analysis(self, job: AnalysisJob) -> None:
        try:
            config, _ = self.load_config()
            provider_config = resolve_text_provider(config=config, profile=job.profile)
            provider = build_text_provider(provider_config)
            provider.preflight()
            title, revision, items = self._analysis_items(job)
            job.source_revision = revision
            chunks = self._analysis_chunks(items)
            job.total = len(chunks) + (1 if len(chunks) > 1 else 0)
            self._append_analysis(job, f"读取完成：{len(items)} 个内容单元，分为 {len(chunks)} 批。")
            if not chunks:
                raise ValueError("The selected course has no analyzable content.")

            partials = []
            system_prompt = (
                "You are a meticulous senior reviewer of Japanese language-learning courses. "
                "Analyze every supplied item, answer in Chinese Markdown, cite exact locations, and distinguish "
                "confirmed errors from possible risks. Never invent source facts or answer keys. Include severity, "
                "category, evidence, and an actionable correction for each issue."
            )
            for index, chunk in enumerate(chunks, start=1):
                self._append_analysis(job, f"正在分析第 {index}/{len(chunks)} 批…")
                prompt = json.dumps({
                    "courseTitle": title,
                    "analysisInstruction": job.instruction,
                    "batch": index,
                    "batchCount": len(chunks),
                    "items": chunk,
                }, ensure_ascii=False)
                completion = provider.complete(
                    system_prompt, prompt,
                    batch_name=f"whole-course-{job.id[:8]}-{index:03d}.json",
                )
                partials.append(completion.text.strip())
                job.progress = index

            if len(partials) > 1:
                self._append_analysis(job, "正在汇总整课共性问题和优先级…")
                synthesis_input = [text[:6000] for text in partials]
                synthesis = provider.complete(
                    "You synthesize batch-level course reviews into one Chinese Markdown executive report. "
                    "Deduplicate issues, identify cross-course patterns, rank priorities, give statistics only when "
                    "supported, and retain exact location references. Do not invent facts.",
                    json.dumps({
                        "courseTitle": title,
                        "analysisInstruction": job.instruction,
                        "batchReports": synthesis_input,
                    }, ensure_ascii=False),
                    batch_name=f"whole-course-{job.id[:8]}-summary.json",
                )
                overview = synthesis.text.strip()
                job.progress = job.total
            else:
                overview = partials[0]

            generated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            details = "\n\n".join(
                f"### 分批报告 {index}/{len(partials)}\n\n{text}"
                for index, text in enumerate(partials, start=1)
            )
            job.report = (
                f"# 整课分析报告：{title}\n\n"
                f"- 分析模型：`{job.profile}`\n"
                f"- 内容版本：`{revision}`\n"
                f"- 生成时间：{generated}\n"
                f"- 分析范围：{len(items)} 个内容单元，{len(chunks)} 个批次\n\n"
                f"## 综合结论\n\n{overview}\n\n"
                f"## 分批分析明细\n\n{details}\n"
            )
            report_dir = self.analyses_dir / job.id
            report_dir.mkdir(parents=True, exist_ok=True)
            write_json(report_dir / "metadata.json", {
                "targetKind": job.target_kind,
                "targetId": job.target_id,
                "profile": job.profile,
                "instruction": job.instruction,
                "sourceRevision": revision,
                "generatedAt": generated,
            })
            if job.target_kind == "course":
                try:
                    manifest_path = self._course_manifest_path(job.target_id)
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                    struct_report = analyze_manifest(manifest, subject_id=job.target_id, existing_revision=revision)
                    write_json(report_dir / "structured-report.json", struct_report.to_dict())
                    if struct_report.markdown_report:
                        job.report += f"\n\n---\n\n## 结构化规则审计与诊断\n\n{struct_report.markdown_report}\n"
                except Exception as struct_exc:
                    self._append_analysis(job, f"结构化分析报告生成跳过：{struct_exc}")

            (report_dir / "report.md").write_text(job.report, encoding="utf-8")
            try:
                target_md_path = self._target_validation_report_path(job.target_kind, job.target_id)
                target_md_path.parent.mkdir(parents=True, exist_ok=True)
                target_md_path.write_text(job.report, encoding="utf-8")
                job.report_path = str(target_md_path)
                self._append_analysis(job, f"校验结果 MD 文档已输出至：{target_md_path}")
            except Exception as write_exc:
                self._append_analysis(job, f"校验结果 MD 写入目标目录跳过：{write_exc}")

            job.status = "succeeded"
            self._append_analysis(job, "整课分析报告已完成。")
        except Exception as exc:  # provider and content errors are reported to the editor
            job.status = "failed"
            self._append_analysis(job, f"整课分析失败：{exc}")
        finally:
            job.finished_at = time.time()

    def _append_analysis(self, job: AnalysisJob, line: str) -> None:
        with self.lock:
            job.log.append(line)
            if len(job.log) > MAX_LOG_LINES:
                del job.log[: len(job.log) - MAX_LOG_LINES]

    def start_batch_analysis(self, payload: dict[str, Any]) -> BatchAnalysisJob:
        raw_targets = payload.get("targets")
        if not isinstance(raw_targets, list) or not raw_targets:
            raise ValueError("Batch analysis requires a list of targets.")
        if len(raw_targets) > 50:
            raise ValueError("A batch analysis can contain at most 50 courses.")
        targets: list[dict[str, Any]] = []
        for item in raw_targets:
            if not isinstance(item, dict):
                raise ValueError("Every target must be an object.")
            kind = str(item.get("targetKind") or "").strip()
            t_id = str(item.get("targetId") or "").strip()
            if kind == "course":
                info = self.course(t_id)
                title = info["title"]
            elif kind == "draft":
                info = self.draft(t_id)
                title = info["title"]
            else:
                raise ValueError(f"Unknown target kind: {kind}")
            targets.append({"targetKind": kind, "targetId": t_id, "title": title})

        profile = str(payload.get("textProfile") or "").strip()
        if not self.known_profile("text", profile):
            raise ValueError("Pick a text profile defined in the provider config.")
        config, _ = self.load_config()
        entry = config.get("textProfiles", {}).get(profile, {})
        availability = _profile_availability(entry)
        if not availability.get("available"):
            raise ValueError(f"Selected model is unavailable: {availability.get('statusText')}")
        provider_config = resolve_text_provider(config=config, profile=profile)
        if provider_config.kind in {"manual", "echo"}:
            raise ValueError("Pick an automatic text model for whole-course analysis.")
        instruction = str(payload.get("instruction") or "").strip() or (
            "从整门课程层面检查原文准确性、同音字、翻译、讲解一致性、重复内容、结构缺失和教学质量；"
            "按影响程度列出可执行的修改建议。"
        )
        if len(instruction) > 4000:
            raise ValueError("Analysis instruction must be at most 4000 characters.")
        job = BatchAnalysisJob(
            id=uuid.uuid4().hex,
            targets=targets,
            profile=profile,
            instruction=instruction,
            total=len(targets),
            target_statuses={f"{t['targetKind']}:{t['targetId']}": "pending" for t in targets},
        )
        with self.lock:
            self.batch_analysis_jobs[job.id] = job
            if len(self.batch_analysis_jobs) > 100:
                finished = [item for item in self.batch_analysis_jobs.values() if item.status != "running"]
                for old in sorted(finished, key=lambda item: item.started_at)[: len(self.batch_analysis_jobs) - 100]:
                    self.batch_analysis_jobs.pop(old.id, None)
        threading.Thread(target=self._run_batch_analysis, args=(job,), daemon=True).start()
        return job

    def batch_analysis(self, analysis_id: str) -> BatchAnalysisJob:
        with self.lock:
            job = self.batch_analysis_jobs.get(analysis_id)
        if job is None:
            raise ValueError("Unknown batch analysis.")
        return job

    def _append_batch_analysis(self, job: BatchAnalysisJob, line: str) -> None:
        with self.lock:
            job.log.append(line)
            if len(job.log) > MAX_LOG_LINES:
                del job.log[: len(job.log) - MAX_LOG_LINES]

    def _run_batch_analysis(self, job: BatchAnalysisJob) -> None:
        try:
            config, _ = self.load_config()
            provider_config = resolve_text_provider(config=config, profile=job.profile)
            provider = build_text_provider(provider_config)
            provider.preflight()
            self._append_batch_analysis(job, f"开始多课程批量分析：共 {len(job.targets)} 门，使用模型 {job.profile}")

            syntheses: list[dict[str, Any]] = []
            for index, target in enumerate(job.targets, start=1):
                t_kind = target["targetKind"]
                t_id = target["targetId"]
                t_title = target.get("title") or t_id
                t_key = f"{t_kind}:{t_id}"
                job.target_statuses[t_key] = "running"
                job.current_target_name = t_title
                self._append_batch_analysis(job, f"[{index}/{len(job.targets)}] 正在分析：{t_title}…")

                try:
                    title, revision, items = self._analysis_items_by_target(t_kind, t_id)
                    chunks = self._analysis_chunks(items)
                    self._append_batch_analysis(job, f"  [{index}/{len(job.targets)}] 读取到 {len(items)} 个单元，分为 {len(chunks)} 批。")

                    partials = []
                    system_prompt = (
                        "You are a meticulous senior reviewer of Japanese language-learning courses. "
                        "Analyze every supplied item, answer in Chinese Markdown, cite exact locations, and distinguish "
                        "confirmed errors from possible risks. Never invent source facts or answer keys. Include severity, "
                        "category, evidence, and an actionable correction for each issue."
                    )
                    for c_idx, chunk in enumerate(chunks, start=1):
                        prompt = json.dumps({
                            "courseTitle": title,
                            "analysisInstruction": job.instruction,
                            "batch": c_idx,
                            "batchCount": len(chunks),
                            "items": chunk,
                        }, ensure_ascii=False)
                        completion = provider.complete(
                            system_prompt, prompt,
                            batch_name=f"batch-ana-{job.id[:6]}-{index:02d}-{c_idx:03d}.json",
                        )
                        partials.append(completion.text.strip())

                    if len(partials) > 1:
                        synthesis_input = [text[:6000] for text in partials]
                        synthesis = provider.complete(
                            "You synthesize batch-level course reviews into one Chinese Markdown executive report. "
                            "Deduplicate issues, identify cross-course patterns, rank priorities, give statistics only when "
                            "supported, and retain exact location references. Do not invent facts.",
                            json.dumps({
                                "courseTitle": title,
                                "analysisInstruction": job.instruction,
                                "batchReports": synthesis_input,
                            }, ensure_ascii=False),
                            batch_name=f"batch-ana-{job.id[:6]}-{index:02d}-summary.json",
                        )
                        overview = synthesis.text.strip()
                    else:
                        overview = partials[0] if partials else "无内容。"

                    details = "\n\n".join(
                        f"### 分批报告 {p_idx}/{len(partials)}\n\n{text}"
                        for p_idx, text in enumerate(partials, start=1)
                    )
                    single_report = (
                        f"# 课程分析报告：{title}\n\n"
                        f"- 目标类型：`{t_kind}`\n"
                        f"- 标识：`{t_id}`\n"
                        f"- 内容版本：`{revision}`\n\n"
                        f"## 综合结论\n\n{overview}\n\n"
                        f"## 分批明细\n\n{details}\n"
                    )
                    if t_kind == "course":
                        try:
                            manifest_path = self._course_manifest_path(t_id)
                            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                            struct_report = analyze_manifest(manifest, subject_id=t_id, existing_revision=revision)
                            if struct_report.markdown_report:
                                single_report += f"\n\n---\n\n## 结构化规则审计与诊断\n\n{struct_report.markdown_report}\n"
                        except Exception as struct_exc:
                            self._append_batch_analysis(job, f"  [{index}/{len(job.targets)}] 结构化分析报告生成跳过：{struct_exc}")

                    job.target_reports[t_key] = single_report
                    job.target_statuses[t_key] = "succeeded"
                    try:
                        target_md_path = self._target_validation_report_path(t_kind, t_id)
                        target_md_path.parent.mkdir(parents=True, exist_ok=True)
                        target_md_path.write_text(single_report, encoding="utf-8")
                        job.target_report_paths[t_key] = str(target_md_path)
                        self._append_batch_analysis(job, f"  [{index}/{len(job.targets)}] 校验结果 MD 文档已输出至：{target_md_path}")
                    except Exception as write_exc:
                        self._append_batch_analysis(job, f"  [{index}/{len(job.targets)}] 校验结果 MD 写入目标目录跳过：{write_exc}")

                    syntheses.append({"title": title, "kind": t_kind, "id": t_id, "summary": overview})
                    self._append_batch_analysis(job, f"[{index}/{len(job.targets)}] 《{title}》分析完成。")
                except Exception as exc:
                    job.target_statuses[t_key] = "failed"
                    job.target_reports[t_key] = f"分析失败：{exc}"
                    self._append_batch_analysis(job, f"[{index}/{len(job.targets)}] 《{t_title}》分析出错：{exc}")

                job.progress = index

            if len(job.targets) > 1 and syntheses:
                self._append_batch_analysis(job, "正在生成跨课程综合汇总报告…")
                cross_prompt = json.dumps({
                    "batchCount": len(job.targets),
                    "instruction": job.instruction,
                    "courses": syntheses,
                }, ensure_ascii=False)
                cross_synthesis = provider.complete(
                    "You are a lead curriculum quality inspector. Synthesize multi-course analysis findings into a "
                    "high-level Chinese Markdown overview. Group recurring errors, compare quality across courses, "
                    "highlight urgent fixes, and provide prioritized action steps.",
                    cross_prompt,
                    batch_name=f"batch-ana-{job.id[:6]}-cross-summary.json",
                )
                cross_overview = cross_synthesis.text.strip()
            elif syntheses:
                cross_overview = syntheses[0]["summary"]
            else:
                cross_overview = "批量分析未产出有效结论。"

            generated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            success_count = sum(1 for s in job.target_statuses.values() if s == "succeeded")
            job.overall_report = (
                f"# 多课程批量复核质检报告\n\n"
                f"- 分析模型：`{job.profile}`\n"
                f"- 课程数量：共 {len(job.targets)} 门（成功 {success_count} 门）\n"
                f"- 生成时间：{generated}\n\n"
                f"## 总体结论与跨课程质量汇总\n\n{cross_overview}\n"
            )

            batch_dir = self.analyses_dir / f"batch-{job.id}"
            batch_dir.mkdir(parents=True, exist_ok=True)
            (batch_dir / "report.md").write_text(job.overall_report, encoding="utf-8")
            write_json(batch_dir / "metadata.json", {
                "id": job.id,
                "targets": job.targets,
                "profile": job.profile,
                "instruction": job.instruction,
                "targetStatuses": job.target_statuses,
                "generatedAt": generated,
            })
            for k, rep in job.target_reports.items():
                safe_k = k.replace(":", "_").replace("/", "_")
                (batch_dir / f"{safe_k}.md").write_text(rep, encoding="utf-8")

            job.report_path = str(batch_dir / "report.md")
            self._append_batch_analysis(job, f"多课程汇总校验报告已输出：{batch_dir / 'report.md'}")
            job.status = "succeeded"
            self._append_batch_analysis(job, "批量整课分析已全部完成。")
        except Exception as exc:
            job.status = "failed"
            self._append_batch_analysis(job, f"批量整课分析失败：{exc}")
        finally:
            job.finished_at = time.time()

    def batch_approve(self, payload: dict[str, Any]) -> dict[str, Any]:
        targets = payload.get("targets")
        if not isinstance(targets, list) or not targets:
            raise ValueError("Must provide at least one target to approve.")
        if len(targets) > 50:
            raise ValueError("Cannot approve more than 50 targets at once.")
        note = str(payload.get("note") or "批量复核确认").strip()

        approved: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for item in targets:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("targetKind") or "").strip()
            target_id = str(item.get("targetId") or "").strip()
            title = str(item.get("title") or target_id).strip()

            try:
                if kind == "course":
                    manifest_path = self._course_manifest_path(target_id)
                    current_revision = sha256_file(manifest_path)
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                    sentences = manifest.get("sentences")
                    if not isinstance(sentences, list) or not sentences:
                        raise ValueError("该课程没有句子列表。")
                    report = audit_manifest(manifest, require_enrichment=False)
                    errors = int(report.get("summary", {}).get("errors") or 0)
                    if errors > 0:
                        reasons = [str(i.get("message") or "") for i in report.get("issues", []) if i.get("severity") == "error"]
                        raise ValueError(f"质量审计未通过（{errors} 个错误）：{'; '.join(reasons[:3])}")

                    if "audio" in manifest and isinstance(manifest["audio"], str):
                        audio_path = manifest_path.parent / manifest["audio"]
                        if not audio_path.is_file():
                            raise ValueError(f"音频文件不存在：{manifest['audio']}")

                    backup_dir = manifest_path.parent / ".workbench-backups"
                    backup_dir.mkdir(exist_ok=True)
                    backup_path = backup_dir / f"manifest.{current_revision[:12]}.json"
                    if not backup_path.exists():
                        shutil.copy2(manifest_path, backup_path)

                    all_ids = [str(s.get("id") or "") for s in sentences if isinstance(s, dict) and s.get("id")]
                    prepared = prepare_course_manifest(manifest)
                    metadata = prepared.setdefault("buildMetadata", {})
                    edits = metadata.setdefault("workbenchEdits", {}) if isinstance(metadata, dict) else {}
                    edits["count"] = int(edits.get("count") or 0) + 1
                    edits["lastEditedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    edits["batchApprovedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    edits["batchApprovedNote"] = note
                    edits["sentenceIds"] = sorted(set(all_ids))
                    prepared["quality"] = report
                    write_json(manifest_path, prepared)
                    write_json(manifest_path.parent / "quality-report.json", report)
                    target_md_path = manifest_path.parent / "validation-report.md"
                    approved_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    struct_report = analyze_manifest(manifest, subject_id=target_id)
                    validation_md = (
                        f"# 课程复核确认与质量报告：{title}\n\n"
                        f"- **复核状态**: 已通过批量复核标记\n"
                        f"- **复核时间**: `{approved_time}`\n"
                        f"- **复核备注**: {note}\n"
                        f"- **审核句子数**: {len(all_ids)} 句\n\n"
                        f"---\n\n"
                        f"{struct_report.markdown_report}\n"
                    )
                    target_md_path.write_text(validation_md, encoding="utf-8")
                    approved.append({
                        "targetKind": kind,
                        "targetId": target_id,
                        "title": title,
                        "reviewed": len(all_ids),
                        "reportPath": str(target_md_path),
                    })

                elif kind == "draft":
                    job, _, pages_dir = self._draft_context(target_id)
                    pages = list(pages_dir.glob("*.json"))
                    if not pages:
                        raise ValueError("该草稿没有页面数据。")
                    page_names = [p.name for p in pages]
                    approved_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    progress_path = job.work_dir / "review-progress.json"
                    write_json(progress_path, {
                        "reviewedPages": page_names,
                        "batchApprovedAt": approved_time,
                        "batchApprovedNote": note,
                    })
                    target_md_path = job.work_dir / "validation-report.md"
                    validation_md = (
                        f"# 草稿复核确认报告：{title}\n\n"
                        f"- **复核状态**: 已通过批量复核标记\n"
                        f"- **复核时间**: `{approved_time}`\n"
                        f"- **复核备注**: {note}\n"
                        f"- **页面数量**: 共 {len(page_names)} 页\n"
                        f"- **页面列表**: {', '.join(page_names)}\n"
                    )
                    target_md_path.write_text(validation_md, encoding="utf-8")
                    approved.append({
                        "targetKind": kind,
                        "targetId": target_id,
                        "title": title,
                        "reviewed": len(page_names),
                        "reportPath": str(target_md_path),
                    })
                else:
                    raise ValueError(f"Unsupported target kind: {kind}")
            except Exception as exc:
                failed.append({"targetKind": kind, "targetId": target_id, "title": title, "reason": str(exc)})

        return {"approved": approved, "failed": failed}

    def cleanup(self) -> None:
        with self.lock:
            self.shutting_down = True
            for job in self.jobs.values():
                if job.status == "queued":
                    job.status = "cancelled"
                    job.finished_at = time.time()
        for job in list(self.jobs.values()):
            if job.process is not None and job.process.poll() is None:
                job.process.terminate()
        for control in list(self.model_control_history):
            if control.process is not None and control.process.poll() is None:
                control.process.terminate()


def _clean_sub_langs(value: Any) -> str:
    """Language tags only. This becomes an argv element, so nothing else gets through."""
    text = str(value or "").strip()
    if not text:
        return ""
    tags = [tag.strip() for tag in text.split(",") if tag.strip()]
    for tag in tags:
        if not re.fullmatch(r"[A-Za-z]{2,8}(-[A-Za-z0-9]{2,8})*", tag):
            raise ValueError(f"Not a language tag: {tag!r}")
    if len(tags) > 8:
        raise ValueError("Too many subtitle languages.")
    return ",".join(tags)


def _clean_clip(start: Any, end: Any) -> tuple[str, str] | None:
    """A clip window, reduced to two plain numbers before it reaches an argv."""
    if start in (None, "") and end in (None, ""):
        return None
    try:
        low, high = float(start), float(end)
    except (TypeError, ValueError) as exc:
        raise ValueError("The clip window must be two numbers of seconds.") from exc
    if not (0 <= low < high) or high > 24 * 3600:
        raise ValueError("The clip window must satisfy 0 <= start < end.")
    return (f"{low:.3f}", f"{high:.3f}")


def _describe_profile(
    name: str,
    entry: Any,
    availability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """What the page may know about a profile. Never a key, never a raw command."""
    entry = entry if isinstance(entry, dict) else {}
    availability = availability or _profile_availability(entry)
    return {
        "name": name,
        "kind": str(entry.get("kind") or ""),
        "model": str(entry.get("model") or ""),
        "language": str(entry.get("language") or ""),
        "description": str(entry.get("description") or ""),
        "needsKeyEnv": str(entry.get("apiKeyEnv") or ""),
        "keyPresent": bool(os.environ.get(str(entry.get("apiKeyEnv") or ""), "")) if entry.get("apiKeyEnv") else None,
        "available": bool(availability.get("available")),
        "source": str(availability.get("source") or "unknown"),
        "statusText": str(availability.get("statusText") or "状态未知"),
    }


LOCAL_HTTP_HOSTS = frozenset(
    {"localhost", "127.0.0.1", "::1", "0.0.0.0", "host.docker.internal"}
)


def _profile_source(entry: dict[str, Any]) -> str:
    kind = str(entry.get("kind") or "").strip().lower()
    if kind in {"cli", "command"}:
        return "cli"
    if kind == "manual":
        return "manual"
    if kind == "import":
        return "file"
    base_url = str(entry.get("baseUrl") or "").strip()
    if base_url and (urlparse(base_url).hostname or "").lower() in LOCAL_HTTP_HOSTS:
        return "local"
    if base_url or entry.get("apiKeyEnv"):
        return "cloud"
    if kind == "faster-whisper":
        return "local"
    return "builtin"


def _command_available(entry: dict[str, Any]) -> bool:
    raw = entry.get("command")
    if isinstance(raw, str):
        try:
            parts = shlex.split(raw)
        except ValueError:
            return False
    elif isinstance(raw, list):
        parts = [str(item) for item in raw if str(item)]
    else:
        parts = []
    if not parts:
        return False
    executable = os.path.expanduser(parts[0])
    if os.path.isabs(executable) or os.sep in executable:
        return Path(executable).is_file() and os.access(executable, os.X_OK)
    return shutil.which(executable) is not None


def _local_http_availability(entry: dict[str, Any]) -> dict[str, Any]:
    kind = str(entry.get("kind") or "").strip().lower()
    base_url = str(entry.get("baseUrl") or "").strip().rstrip("/")
    model = str(entry.get("model") or "").strip()
    endpoint = f"{base_url}/api/tags" if kind == "ollama" else f"{base_url}/models"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=1.0) as response:
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        return {"available": False, "source": "local", "statusText": "本地服务未响应"}

    if kind == "ollama":
        rows = payload.get("models") if isinstance(payload, dict) else None
        ids = {
            str(row.get("name") or row.get("model") or "")
            for row in rows or []
            if isinstance(row, dict)
        }
    else:
        rows = payload.get("data") if isinstance(payload, dict) else None
        ids = {
            str(row.get("id") or "")
            for row in rows or []
            if isinstance(row, dict)
        }
    if model and ids and model not in ids:
        return {"available": False, "source": "local", "statusText": "服务在线，但指定模型未加载"}
    return {"available": True, "source": "local", "statusText": "本地服务在线"}


def _probe_gpu_status(workspace: Path | None = None) -> dict[str, Any]:
    """Detect NVIDIA GPUs and driver/NVML status with multi-level fallback."""
    driver_version: str | None = None
    proc_version_path = Path("/proc/driver/nvidia/version")
    if proc_version_path.exists():
        try:
            content = proc_version_path.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"Kernel Module\s+([0-9\.]+)", content)
            if m:
                driver_version = m.group(1)
        except Exception:
            pass

    # 1. Try nvidia-smi for real-time telemetry
    smi_err: str | None = None
    if shutil.which("nvidia-smi"):
        try:
            res = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,uuid,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,power.limit",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if res.returncode == 0 and res.stdout.strip():
                gpus: list[dict[str, Any]] = []
                for line in res.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 8:
                        def _num(val: str, typ=float):
                            try:
                                return typ(val)
                            except (ValueError, TypeError):
                                return None

                        total_mem = _num(parts[3])
                        used_mem = _num(parts[4])
                        free_mem = _num(parts[5])
                        mem_percent = (
                            round((used_mem / total_mem) * 100, 1)
                            if (total_mem and used_mem is not None and total_mem > 0)
                            else None
                        )
                        gpus.append(
                            {
                                "index": _num(parts[0], int) or 0,
                                "name": parts[1],
                                "uuid": parts[2],
                                "memory_total_mb": total_mem,
                                "memory_used_mb": used_mem,
                                "memory_free_mb": free_mem,
                                "memory_percent": mem_percent,
                                "utilization_gpu_percent": _num(parts[6]),
                                "temperature_gpu_c": _num(parts[7]),
                                "power_draw_w": _num(parts[8]) if len(parts) > 8 else None,
                                "power_limit_w": _num(parts[9]) if len(parts) > 9 else None,
                                "status": "active",
                            }
                        )
                if gpus:
                    summary = ", ".join(g["name"] for g in gpus)
                    return {
                        "available": True,
                        "nvml_ready": True,
                        "driver_version": driver_version,
                        "device_count": len(gpus),
                        "gpus": gpus,
                        "summary": summary,
                        "status_text": f"在线（{len(gpus)} 张 GPU 实时监控中）",
                        "error": None,
                    }
            else:
                smi_err = (res.stderr or res.stdout).strip() or "nvidia-smi returned non-zero"
        except Exception as exc:
            smi_err = str(exc)

    # 2. Fallback: Parse /proc/driver/nvidia/gpus/*/information
    proc_gpus: list[dict[str, Any]] = []
    for info_path in sorted(glob.glob("/proc/driver/nvidia/gpus/*/information")):
        bus_id = os.path.basename(os.path.dirname(info_path))
        info: dict[str, Any] = {"bus_id": bus_id, "status": "restricted"}
        try:
            with open(info_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if ":" in line:
                        k, v = [x.strip() for x in line.split(":", 1)]
                        if k == "Model":
                            info["name"] = v
                        elif k == "GPU UUID":
                            info["uuid"] = v
                        elif k == "Video BIOS":
                            info["bios"] = v
                        elif k == "Device Minor":
                            try:
                                info["index"] = int(v)
                            except ValueError:
                                pass
        except Exception:
            pass
        if "name" in info:
            proc_gpus.append(info)

    # Read project GPU config (e.g. current_gpu.json)
    h3_gpu_info: dict[str, Any] | None = None
    candidate_paths: list[Path] = []
    env_cfg = os.environ.get("DICTATION_GPU_CONFIG")
    if env_cfg:
        candidate_paths.append(Path(env_cfg))
    if workspace is not None:
        candidate_paths.extend([
            workspace / "current_gpu.json",
            workspace.parent / "H3" / "current_gpu.json",
            workspace.parent / "current_gpu.json",
        ])
    candidate_paths.extend([
        Path("/workspace/Develop/H3/current_gpu.json"),
        Path("/workspace/H3/current_gpu.json"),
    ])
    for cp in candidate_paths:
        if cp.is_file():
            try:
                h3_gpu_info = json.loads(cp.read_text(encoding="utf-8"))
                break
            except Exception:
                pass

    known_vram = {
        "H100": 80 * 1024,
        "RTX 6000 Ada": 48 * 1024,
        "RTX 4090": 24 * 1024,
        "RTX 3090": 24 * 1024,
        "A100": 80 * 1024,
        "L40": 48 * 1024,
    }

    if proc_gpus:
        for idx, gpu in enumerate(proc_gpus):
            if "index" not in gpu:
                gpu["index"] = idx
            if h3_gpu_info and (
                gpu.get("uuid") == h3_gpu_info.get("gpu_uuid")
                or str(gpu.get("index")) == str(h3_gpu_info.get("gpu_id"))
            ):
                gpu["is_current"] = True
                if "vram_total_gb" in h3_gpu_info:
                    gpu["memory_total_mb"] = round(float(h3_gpu_info["vram_total_gb"]) * 1024)
            if "memory_total_mb" not in gpu:
                for k, v in known_vram.items():
                    if k in str(gpu.get("name", "")):
                        gpu["memory_total_mb"] = v
                        break
        names = [g.get("name", "GPU") for g in proc_gpus]
        summary = f"{names[0]} 等 {len(proc_gpus)} 张显卡" if len(proc_gpus) > 1 else names[0]
        return {
            "available": True,
            "nvml_ready": False,
            "driver_version": driver_version,
            "device_count": len(proc_gpus),
            "gpus": proc_gpus,
            "summary": summary,
            "status_text": f"硬件与驱动已就绪（共 {len(proc_gpus)} 张 GPU；容器 NVML 受限）",
            "error": smi_err or "容器内设备节点权限受限，NVML 实时监控不可用",
        }

    # 3. Fallback to current_gpu.json if procfs not accessible
    if h3_gpu_info and h3_gpu_info.get("gpu_name"):
        single_gpu = {
            "index": int(h3_gpu_info.get("gpu_id", 0)),
            "name": h3_gpu_info.get("gpu_name"),
            "uuid": h3_gpu_info.get("gpu_uuid"),
            "memory_total_mb": round(float(h3_gpu_info.get("vram_total_gb", 0)) * 1024),
            "is_current": True,
            "status": "configured",
        }
        return {
            "available": True,
            "nvml_ready": False,
            "driver_version": driver_version,
            "device_count": 1,
            "gpus": [single_gpu],
            "summary": single_gpu["name"],
            "status_text": "已配置静态显卡（实时监控不可用）",
            "error": smi_err or "NVML 未初始化",
        }

    return {
        "available": False,
        "nvml_ready": False,
        "driver_version": None,
        "device_count": 0,
        "gpus": [],
        "summary": "未检测到显卡",
        "status_text": "未检测到可用 GPU 设备",
        "error": smi_err,
    }


def _profile_availability(entry: Any) -> dict[str, Any]:
    entry = entry if isinstance(entry, dict) else {}
    kind = str(entry.get("kind") or "").strip().lower()
    source = _profile_source(entry)

    if kind == "echo":
        return {"available": False, "source": "builtin", "statusText": "仅测试占位，不可用于正式课程"}
    if kind == "manual":
        return {"available": True, "source": "manual", "statusText": "手工接力模式可用"}
    if kind == "import":
        raw = str(entry.get("transcript") or "").strip()
        path = Path(raw).expanduser() if raw else None
        if path and not path.is_absolute():
            path = PROJECT_DIR / path
        ready = bool(path and path.is_file())
        return {
            "available": ready,
            "source": "file",
            "statusText": "导入文件存在" if ready else "导入文件不存在",
        }
    if kind in {"cli", "command"}:
        ready = _command_available(entry)
        return {
            "available": ready,
            "source": "cli",
            "statusText": "CLI 已安装" if ready else "CLI 未安装或不可执行",
        }
    if kind == "faster-whisper":
        if importlib.util.find_spec("faster_whisper") is None:
            return {"available": False, "source": "local", "statusText": "缺少 faster-whisper"}
        if str(entry.get("device") or "").lower() == "cuda":
            try:
                import ctranslate2  # type: ignore

                if ctranslate2.get_cuda_device_count() < 1:
                    return {"available": False, "source": "local", "statusText": "没有可用 CUDA 设备"}
            except (ImportError, OSError):
                return {"available": False, "source": "local", "statusText": "CUDA 转写运行时不可用"}
        return {"available": True, "source": "local", "statusText": "本地转写运行时可用"}

    key_env = str(entry.get("apiKeyEnv") or "").strip()
    if key_env and not os.environ.get(key_env, ""):
        return {"available": False, "source": source, "statusText": f"缺少环境变量 {key_env}"}

    base_url = str(entry.get("baseUrl") or "").strip()
    if base_url and (urlparse(base_url).hostname or "").lower() in LOCAL_HTTP_HOSTS:
        return _local_http_availability(entry)
    if source == "cloud":
        return {"available": True, "source": "cloud", "statusText": "云端凭据已配置"}
    return {"available": False, "source": source, "statusText": "配置不完整"}


def _availability_signature(entry: Any) -> str:
    entry = entry if isinstance(entry, dict) else {}
    fields = {
        key: entry.get(key)
        for key in ("kind", "baseUrl", "model", "apiKeyEnv", "command", "device", "transcript")
    }
    return json.dumps(fields, ensure_ascii=False, sort_keys=True, default=str)


def _profile_availability_map(config: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    entries: dict[tuple[str, str], Any] = {}
    for family, key in (("text", "textProfiles"), ("asr", "asrProfiles"), ("vision", "visionProfiles")):
        profiles = config.get(key) or {}
        if isinstance(profiles, dict):
            for name, entry in profiles.items():
                entries[(family, str(name))] = entry

    signatures = {_availability_signature(entry): entry for entry in entries.values()}
    results: dict[str, dict[str, Any]] = {}
    if signatures:
        workers = min(12, len(signatures))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_profile_availability, entry): signature
                for signature, entry in signatures.items()
            }
            for future, signature in futures.items():
                try:
                    results[signature] = future.result()
                except Exception:
                    results[signature] = {
                        "available": False,
                        "source": _profile_source(signatures[signature] if isinstance(signatures[signature], dict) else {}),
                        "statusText": "状态检测失败",
                    }
    return {
        identity: results[_availability_signature(entry)]
        for identity, entry in entries.items()
    }


def _vision_pipeline_entries(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate named OCR chains from the trusted config.

    A chain can contain at most three profiles: full-document OCR followed by
    up to two flagged-page reviewers. With no explicit chains, each configured
    vision profile remains usable on its own.
    """
    profiles = config.get("visionProfiles") or {}
    if not isinstance(profiles, dict):
        raise ConfigError("Provider config field 'visionProfiles' must be an object.")
    raw_pipelines = config.get("visionPipelines") or {}
    if not isinstance(raw_pipelines, dict):
        raise ConfigError("Provider config field 'visionPipelines' must be an object.")
    if not raw_pipelines:
        raw_pipelines = {
            name: {"description": str(entry.get("description") or ""), "profiles": [name]}
            for name, entry in profiles.items()
            if isinstance(entry, dict)
        }

    result: list[dict[str, Any]] = []
    for name in sorted(raw_pipelines):
        entry = raw_pipelines[name]
        if not isinstance(entry, dict):
            raise ConfigError(f"Vision pipeline {name!r} must be an object.")
        members = entry.get("profiles")
        if not isinstance(members, list) or not members:
            raise ConfigError(f"Vision pipeline {name!r} needs a non-empty profiles array.")
        cleaned = list(dict.fromkeys(str(member).strip() for member in members if str(member).strip()))
        if len(cleaned) > 3:
            raise ConfigError(f"Vision pipeline {name!r} may use at most three profiles.")
        unknown = [member for member in cleaned if member not in profiles]
        if unknown:
            raise ConfigError(
                f"Vision pipeline {name!r} names unknown profile(s): {', '.join(unknown)}."
            )
        result.append({
            "name": str(name),
            "description": str(entry.get("description") or ""),
            "profiles": cleaned,
        })
    return result


def _describe_vision_pipelines(
    config: dict[str, Any],
    availability: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    profiles = config.get("visionProfiles") or {}
    availability = availability or _profile_availability_map(config)
    described: list[dict[str, Any]] = []
    for pipeline in _vision_pipeline_entries(config):
        members = []
        for name in pipeline["profiles"]:
            entry = profiles[name] if isinstance(profiles.get(name), dict) else {}
            base_url = str(entry.get("baseUrl") or "")
            host = (urlparse(base_url).hostname or "").lower()
            item = _describe_profile(name, entry, availability.get(("vision", name)))
            item["local"] = host in {"localhost", "127.0.0.1", "::1", "0.0.0.0", "host.docker.internal"}
            members.append(item)
        ready = bool(members) and all(member["available"] for member in members)
        described.append({
            **pipeline,
            "members": members,
            "available": ready,
            "statusText": "整条管线可用" if ready else "存在离线或未配置的模型",
        })
    return described


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


class StudioHandler(BaseHTTPRequestHandler):
    server_version = "DictationStudio/1"
    security: SecurityContext
    studio: Studio

    def log_message(self, format: str, *args: Any) -> None:
        try:
            super().log_message(format, *args)
        except (OSError, ValueError):
            pass

    def deny(self, reason: str) -> None:
        self.log_message("denied %s %s (%s)", self.command, self.path, reason)
        self.send_response(HTTPStatus.FORBIDDEN)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def end_headers(self) -> None:
        for header, value in SECURITY_HEADERS.items():
            self.send_header(header, value)
        super().end_headers()

    # ---- routing ----

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if parsed.path == "/api/session/bootstrap":
            decision = self.security.authorize_bootstrap(self.headers)
            if not decision.allowed:
                self.deny(decision.reason)
                return
            self.send_json({"token": self.security.token})
            return

        if parsed.path.startswith("/api/"):
            if not self.authorized(parsed.path):
                return
            self.route_get(parsed)
            return

        decision = self.security.authorize_static(self.headers)
        if not decision.allowed:
            self.deny(decision.reason)
            return
        self.send_asset(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        if not parsed.path.startswith("/api/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.authorized(parsed.path):
            return
        self.route_post(parsed)

    def authorized(self, path: str) -> bool:
        decision = self.security.authorize_api(self.headers, method=self.command, path=path)
        if not decision.allowed:
            self.deny(decision.reason)
            return False
        return True

    def route_get(self, parsed) -> None:
        path = parsed.path
        try:
            if path == "/api/health":
                self.send_json({"ok": True})
            elif path == "/api/config":
                self.send_json(self.studio.describe_config())
            elif path == "/api/local-models":
                self.send_json(self.studio.local_models())
            elif path == "/api/gpu-status":
                self.send_json(self.studio.gpu_status())
            elif path == "/api/courses":
                self.send_json({"courses": self.studio.courses()})
            elif path == "/api/resources/status":
                self.send_json(get_slot_manager().get_status())
            elif path.startswith("/api/analysis/structured/"):
                name = path[len("/api/analysis/structured/") :]
                self.send_json(self.studio.structured_analysis(name))
            elif path == "/api/review-targets":
                filter_mode = ""
                for pair in parsed.query.split("&"):
                    if pair.startswith("filter="):
                        filter_mode = pair[len("filter=") :]
                self.send_json(self.studio.review_targets(filter_mode=filter_mode))
            elif path.startswith("/api/courses/"):
                name = path[len("/api/courses/") :]
                self.send_json(self.studio.course(name))
            elif path.startswith("/api/drafts/"):
                parts = path[len("/api/drafts/") :].split("/")
                job_id = parts[0]
                if len(parts) == 1:
                    self.send_json(self.studio.draft(job_id))
                elif len(parts) == 3 and parts[1] == "pages":
                    self.send_json(self.studio.draft_page(job_id, parts[2]))
                elif len(parts) == 3 and parts[1] == "images":
                    self.send_file(self.studio.draft_image_path(job_id, parts[2]), "image/png")
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
            elif path == "/api/batch-analyses":
                with self.studio.lock:
                    jobs = [job.snapshot(since=len(job.log)) for job in self.studio.batch_analysis_jobs.values()]
                self.send_json({"batchAnalyses": jobs})
            elif path.startswith("/api/batch-analyses/"):
                analysis_id = path[len("/api/batch-analyses/") :]
                since = 0
                for pair in parsed.query.split("&"):
                    if pair.startswith("since="):
                        since = int(pair[len("since=") :] or 0)
                self.send_json(self.studio.batch_analysis(analysis_id).snapshot(since=since))
            elif path.startswith("/api/analyses/"):
                analysis_id = path[len("/api/analyses/") :]
                since = 0
                for pair in parsed.query.split("&"):
                    if pair.startswith("since="):
                        since = int(pair[len("since=") :] or 0)
                self.send_json(self.studio.analysis(analysis_id).snapshot(since=since))
            elif path == "/api/builds":
                with self.studio.lock:
                    jobs = [job.snapshot(since=len(job.log)) for job in self.studio.jobs.values()]
                self.send_json({"builds": jobs})
            elif path.startswith("/api/builds/"):
                job_id = path[len("/api/builds/") :]
                since = 0
                for pair in parsed.query.split("&"):
                    if pair.startswith("since="):
                        since = int(pair[len("since=") :] or 0)
                self.send_json(self.studio.job(job_id).snapshot(since=since))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, ConfigError, InstallError, MediaSourceError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def route_post(self, parsed) -> None:
        path = parsed.path
        try:
            if path == "/api/uploads":
                self.send_json(self.handle_upload())
            elif path == "/api/builds":
                job = self.studio.start_build(self.read_json())
                self.send_json(job.snapshot(), HTTPStatus.ACCEPTED)
            elif path == "/api/pdf/builds":
                job = self.studio.start_pdf_build(self.read_json())
                self.send_json(job.snapshot(), HTTPStatus.ACCEPTED)
            elif path == "/api/batch-builds":
                self.send_json(
                    self.studio.start_batch_build(self.read_json()), HTTPStatus.ACCEPTED
                )
            elif path == "/api/batch-analyses":
                job = self.studio.start_batch_analysis(self.read_json())
                self.send_json(job.snapshot(), HTTPStatus.ACCEPTED)
            elif path == "/api/batch-review/approve":
                self.send_json(self.studio.batch_approve(self.read_json()))
            elif path == "/api/analyses":
                job = self.studio.start_analysis(self.read_json())
                self.send_json(job.snapshot(), HTTPStatus.ACCEPTED)
            elif path == "/api/video/probe":
                self.send_json(self.studio.probe_video(self.read_json()))
            elif path == "/api/video/builds":
                job = self.studio.start_video_build(self.read_json())
                self.send_json(job.snapshot(), HTTPStatus.ACCEPTED)
            elif path == "/api/local-models/start":
                payload = self.read_json()
                self.send_json(
                    self.studio.control_local_models("start", str(payload.get("service") or "all")),
                    HTTPStatus.ACCEPTED,
                )
            elif path == "/api/local-models/stop":
                payload = self.read_json()
                self.send_json(
                    self.studio.control_local_models("stop", str(payload.get("service") or "all")),
                    HTTPStatus.ACCEPTED,
                )
            elif path.endswith("/save") and path.startswith("/api/courses/"):
                name = path[len("/api/courses/") : -len("/save")]
                self.send_json(self.studio.save_course_sentence(name, self.read_json()))
            elif path.endswith("/revise") and path.startswith("/api/courses/"):
                name = path[len("/api/courses/") : -len("/revise")]
                self.send_json(self.studio.revise_course_sentence(name, self.read_json()))
            elif path.startswith("/api/drafts/"):
                parts = path[len("/api/drafts/") :].split("/")
                if len(parts) == 4 and parts[1] == "pages" and parts[3] in {"save", "revise"}:
                    payload = self.read_json()
                    result = (
                        self.studio.save_draft_page(parts[0], parts[2], payload)
                        if parts[3] == "save"
                        else self.studio.revise_draft_page(parts[0], parts[2], payload)
                    )
                    self.send_json(result)
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
            elif path.endswith("/cancel") and path.startswith("/api/builds/"):
                job_id = path[len("/api/builds/") : -len("/cancel")]
                self.send_json(self.studio.cancel(job_id).snapshot(since=0))
            elif path.endswith("/install") and path.startswith("/api/builds/"):
                job_id = path[len("/api/builds/") : -len("/install")]
                payload = self.read_json()
                self.send_json(self.studio.install(job_id, payload.get("name")))
            elif path.startswith("/api/patches/apply/"):
                name = path[len("/api/patches/apply/") :]
                self.send_json(self.studio.apply_patch(name, self.read_json()))
            elif path.startswith("/api/repairs/deterministic/"):
                name = path[len("/api/repairs/deterministic/") :]
                self.send_json(self.studio.apply_deterministic_repairs(name))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (CasConflictError, RevisionMismatchError) as exc:
            self.send_json({"error": str(exc), "code": "conflict"}, HTTPStatus.CONFLICT)
        except (ValueError, ConfigError, InstallError, MediaSourceError, ProviderError, PatchError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - defensive
            self.log_message("studio error: %s", exc)
            self.send_json({"error": "The studio could not complete that request."},
                           HTTPStatus.INTERNAL_SERVER_ERROR)

    # ---- bodies ----

    def handle_upload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            raise ValueError("Empty upload.")
        if length > MAX_UPLOAD_BYTES:
            raise ValueError(f"Upload is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
        filename = (self.headers.get("X-Dictation-Filename") or "audio.mp3").strip()
        return self.studio.store_upload(filename, self.rfile.read(length))

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_JSON_BODY:
            raise ValueError("Request body is too large.")
        if length <= 0:
            return {}
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be JSON.") from exc
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    # ---- responses ----

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def send_asset(self, url_path: str) -> None:
        name = "index.html" if url_path in ("", "/") else url_path.lstrip("/")
        target = (STUDIO_WEB / name).resolve()
        if not str(target).startswith(str(STUDIO_WEB.resolve())) or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type.endswith("javascript"):
            content_type += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


def build_studio_server(
    *,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    workspace: Path,
    courses_dir: Path,
    config_path: Path | None,
    token: str | None = None,
) -> tuple[ThreadingHTTPServer, Studio, SecurityContext]:
    studio = Studio(workspace, courses_dir, config_path)
    server = ThreadingHTTPServer((host, port), StudioHandler)
    security = SecurityContext(
        host,
        int(server.server_address[1]),
        token or token_from_environment(),
        # Remote development environments commonly expose the server through a
        # different loopback port on the user's desktop. Keep the hostname
        # allowlist and token/origin checks, but permit that port translation.
        allow_forwarded_loopback_ports=True,
    )

    class BoundHandler(StudioHandler):
        pass

    BoundHandler.security = security
    BoundHandler.studio = studio
    server.RequestHandlerClass = BoundHandler
    return server, studio, security


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="studio_server.py",
        description="Localhost-only GUI for building courses.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--workspace", help="Where uploads and builds are kept. Default: studio-work/")
    parser.add_argument("--courses-dir", help=f"Install destination. Default: {DEFAULT_COURSES_DIR}")
    parser.add_argument("--config", help="Provider config file. Default: config/providers.json")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else PROJECT_DIR / "studio-work"
    courses_dir = Path(args.courses_dir).expanduser().resolve() if args.courses_dir else DEFAULT_COURSES_DIR
    config_path = Path(args.config).expanduser().resolve() if args.config else None

    if not STUDIO_WEB.is_dir():
        raise SystemExit(f"Studio assets are missing: {STUDIO_WEB}")

    server, studio, _ = build_studio_server(
        port=args.port, workspace=workspace, courses_dir=courses_dir, config_path=config_path
    )
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Course studio: {url}")
    print(f"Workspace    : {workspace}")
    print(f"Courses      : {courses_dir}")
    config, path = studio.load_config()
    print(f"Providers    : {path or '(no config file found - copy config/providers.example.json)'}")
    if not path:
        print("  Without a config there are no profiles to pick, and the studio")
        print("  deliberately refuses to let the page invent one.")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        studio.cleanup()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
