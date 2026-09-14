"""ASR providers: four ways to turn audio into timed segments.

The old pipeline could only transcribe one way - ``faster-whisper`` on CUDA with
``large-v3`` and ``float16`` baked in as module constants - so a machine without
an NVIDIA GPU could not build a course at all, and a transcript produced by any
other tool could not be used.

The kinds here:

``faster-whisper``
    Local CTranslate2 Whisper. Model, device and compute type are all config.
    The defaults are ``auto``/``int8`` so the pipeline runs on a laptop; a CUDA
    box just sets ``device: cuda`` and ``computeType: float16``.
``openai-audio``
    Any endpoint speaking ``POST {base_url}/audio/transcriptions`` with
    ``verbose_json``. Covers the hosted Whisper APIs and the local servers that
    imitate them (``faster-whisper-server``, ``whisper.cpp`` server, LocalAI).
``command``
    Run any transcriber that writes JSON, SRT or VTT - ``whisper.cpp``,
    ``whisperx``, ``mlx-whisper``, ``insanely-fast-whisper``, or a script of
    your own - and parse whatever it produced.
``import``
    Read a transcript that already exists. The escape hatch that makes every
    other tool in the world a usable front end for this pipeline.

Every kind returns the same :class:`Transcription`, so the stages downstream -
segment merging, enrichment, the quality gate - never learn which one ran.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from provider_config import AsrProviderConfig
from text_providers import utf8_environment


class AsrError(RuntimeError):
    """Transcription failed in a way the user has to act on."""


@dataclass
class Segment:
    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    compression_ratio: float | None = None
    words: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Transcription:
    segments: list[Segment]
    language: str = ""
    language_probability: float | None = None
    duration: float = 0.0
    provider: dict[str, Any] = field(default_factory=dict)


class AsrProvider:
    def __init__(self, config: AsrProviderConfig) -> None:
        self.config = config

    def transcribe(self, audio_path: Path, *, progress: Any = None) -> Transcription:
        raise NotImplementedError

    def preflight(self) -> None:
        """Fail before touching the audio when the setup obviously cannot work."""


def build_asr_provider(config: AsrProviderConfig) -> AsrProvider:
    builders = {
        "faster-whisper": FasterWhisperProvider,
        "openai-audio": OpenAiAudioProvider,
        "command": CommandAsrProvider,
        "import": ImportTranscriptProvider,
    }
    try:
        builder = builders[config.kind]
    except KeyError as exc:  # pragma: no cover - guarded by provider_config
        raise AsrError(f"Unknown ASR provider kind: {config.kind}") from exc
    return builder(config)


# --------------------------------------------------------------------------
# Local faster-whisper
# --------------------------------------------------------------------------


def configure_cuda_dll_search() -> None:
    """Make pip/Toolkit CUDA libraries visible before CTranslate2 loads them."""
    if os.name != "nt":
        configure_pip_cuda_libraries()
        return

    candidates: list[Path] = []
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        candidates.append(Path(cuda_path) / "bin")
    candidates.extend(
        [
            Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\bin"),
            Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin"),
            Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin"),
        ]
    )
    for candidate in candidates:
        if (candidate / "cublas64_12.dll").exists():
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(candidate))
            os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")
            return


def configure_pip_cuda_libraries() -> None:
    """Preload Linux CUDA wheels without requiring a manual LD_LIBRARY_PATH.

    NVIDIA's pip packages install shared libraries below ``site-packages/nvidia``.
    That directory is not necessarily in the dynamic linker's process-start search
    path, which made an otherwise healthy Studio build fail at the first CUDA call.
    Loading the libraries by absolute path and RTLD_GLOBAL makes their SONAMEs
    available to CTranslate2 while leaving system CUDA installations untouched.
    """
    if not sys.platform.startswith("linux"):
        return
    try:
        import ctypes
    except ImportError:  # pragma: no cover - ctypes is part of normal CPython
        return

    library_groups = (
        ("nvidia/cublas/lib", ("libcublasLt.so*", "libcublas.so*")),
        (
            "nvidia/cudnn/lib",
            (
                "libcudnn.so*",
                "libcudnn_ops.so*",
                "libcudnn_graph.so*",
                "libcudnn_heuristic.so*",
                "libcudnn_engines_precompiled.so*",
                "libcudnn_engines_runtime_compiled.so*",
                "libcudnn_cnn.so*",
                "libcudnn_adv.so*",
            ),
        ),
    )
    loaded: set[Path] = set()
    for entry in sys.path:
        if not entry:
            continue
        root = Path(entry)
        for relative, patterns in library_groups:
            directory = root / relative
            if not directory.is_dir():
                continue
            for pattern in patterns:
                for path in sorted(directory.glob(pattern)):
                    resolved = path.resolve()
                    if resolved in loaded or path.is_symlink():
                        continue
                    try:
                        ctypes.CDLL(str(resolved), mode=ctypes.RTLD_GLOBAL)
                    except OSError:
                        # Some optional cuDNN components depend on hardware/runtime
                        # features absent on this machine. WhisperModel will report a
                        # precise error if a library it actually needs is still missing.
                        continue
                    loaded.add(resolved)


class FasterWhisperProvider(AsrProvider):
    def preflight(self) -> None:
        try:
            import faster_whisper  # noqa: F401
        except ImportError as exc:
            raise AsrError(
                "ASR kind 'faster-whisper' needs the faster-whisper package:\n"
                "  python -m pip install -r requirements.txt\n"
                "  Or pick a provider that needs no local model: --asr-kind openai-audio,\n"
                "  --asr-kind command, or --asr-kind import."
            ) from exc

    def transcribe(self, audio_path: Path, *, progress: Any = None) -> Transcription:
        self.preflight()
        configure_cuda_dll_search()
        from faster_whisper import WhisperModel

        config = self.config
        try:
            model = WhisperModel(config.model, device=config.device, compute_type=config.compute_type)
        except Exception as exc:
            raise AsrError(
                f"Could not load faster-whisper model {config.model!r} on device={config.device!r} "
                f"compute_type={config.compute_type!r}: {exc}\n"
                "  On a machine without an NVIDIA GPU use --asr-device cpu --asr-compute-type int8."
            ) from exc

        language = None if config.language in {"", "auto"} else config.language
        options: dict[str, Any] = {
            "language": language,
            "beam_size": config.beam_size,
            "vad_filter": config.vad,
            "word_timestamps": config.word_timestamps,
            # The decoding settings this project's repair history asks for:
            # runaway repetition, hallucination over silence, and segments that
            # swallow a pause whole.
            "condition_on_previous_text": config.condition_on_previous_text,
            "no_speech_threshold": config.no_speech_threshold,
            "log_prob_threshold": config.log_prob_threshold,
            "compression_ratio_threshold": config.compression_ratio_threshold,
            "repetition_penalty": config.repetition_penalty,
            "no_repeat_ngram_size": config.no_repeat_ngram_size,
        }
        if config.hallucination_silence_threshold is not None:
            options["hallucination_silence_threshold"] = config.hallucination_silence_threshold
        if config.initial_prompt:
            options["initial_prompt"] = config.initial_prompt
        if config.vad_options:
            options["vad_parameters"] = dict(config.vad_options)

        try:
            segments_iter, info = model.transcribe(str(audio_path), **options)
        except TypeError as exc:
            # A pinned faster-whisper that predates one of these arguments should
            # say which one, rather than failing somewhere inside the library.
            raise AsrError(
                f"This faster-whisper build rejected a decoding option: {exc}\n"
                "  Remove that field from the ASR profile, or upgrade faster-whisper."
            ) from exc

        duration = float(getattr(info, "duration", 0.0) or 0.0)
        segments: list[Segment] = []
        for raw in segments_iter:
            segments.append(
                Segment(
                    start=float(raw.start),
                    end=float(raw.end),
                    text=str(raw.text or ""),
                    avg_logprob=_optional_float(getattr(raw, "avg_logprob", None)),
                    no_speech_prob=_optional_float(getattr(raw, "no_speech_prob", None)),
                    compression_ratio=_optional_float(getattr(raw, "compression_ratio", None)),
                    words=[
                        {
                            "start": round(float(word.start), 3),
                            "end": round(float(word.end), 3),
                            "word": word.word,
                            "probability": round(float(word.probability), 4),
                        }
                        for word in (getattr(raw, "words", None) or [])
                    ]
                    if config.word_timestamps
                    else [],
                )
            )
            if progress is not None:
                progress(current_time=float(raw.end or 0.0), total_duration=duration, count=len(segments))

        return Transcription(
            segments=segments,
            language=str(getattr(info, "language", "") or ""),
            language_probability=_optional_float(getattr(info, "language_probability", None)),
            duration=duration,
            provider=config.describe(),
        )


# --------------------------------------------------------------------------
# OpenAI-compatible audio transcription endpoints
# --------------------------------------------------------------------------


class OpenAiAudioProvider(AsrProvider):
    def endpoint(self) -> str:
        return f"{self.config.base_url}/audio/transcriptions"

    def preflight(self) -> None:
        if self.config.api_key_env and not self.config.api_key():
            raise AsrError(f"Environment variable {self.config.api_key_env} is empty.")

    def transcribe(self, audio_path: Path, *, progress: Any = None) -> Transcription:
        self.preflight()
        fields = {
            "model": self.config.model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "segment",
        }
        if self.config.language not in {"", "auto"}:
            fields["language"] = self.config.language

        headers = dict(self.config.headers)
        key = self.config.api_key()
        if key:
            headers.setdefault("Authorization", f"Bearer {key}")

        data = _post_multipart(
            self.endpoint(),
            fields=fields,
            file_field="file",
            file_path=audio_path,
            headers=headers,
            timeout=self.config.timeout,
        )
        segments = _segments_from_whisper_json(data)
        if not segments:
            raise AsrError(
                f"{self.endpoint()} returned no timed segments.\n"
                "  The endpoint must support response_format=verbose_json with segment timestamps;\n"
                "  a plain-text transcript cannot be turned into a dictation course."
            )
        return Transcription(
            segments=segments,
            language=str(data.get("language") or ""),
            duration=float(data.get("duration") or 0.0),
            provider=self.config.describe(),
        )


def _post_multipart(
    url: str,
    *,
    fields: dict[str, str],
    file_field: str,
    file_path: Path,
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    boundary = f"----dictation{uuid.uuid4().hex}"
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode()
    )
    parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
    parts.append(file_path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    request.add_header("Content-Length", str(len(body)))
    for name, value in headers.items():
        if value:
            request.add_header(name, value)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:  # pragma: no cover - defensive
            detail = exc.reason or ""
        hint = "\n  A 404 here usually means the base URL needs its /v1 suffix." if exc.code == 404 else ""
        raise AsrError(f"HTTP {exc.code} from {url}: {detail}{hint}") from exc
    except urllib.error.URLError as exc:
        raise AsrError(f"Cannot reach {url}: {exc.reason}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AsrError(f"Transcription response is not JSON: {raw[:300]}") from exc
    if not isinstance(data, dict):
        raise AsrError("Transcription response is not a JSON object.")
    return data


# --------------------------------------------------------------------------
# Arbitrary transcriber command
# --------------------------------------------------------------------------


class CommandAsrProvider(AsrProvider):
    """Run any transcriber CLI and read whatever transcript it wrote.

    Placeholders in the command:

    ``{audio}``        absolute path to the audio file
    ``{output}``       a path the command may write its transcript to
    ``{output_stem}``  the same path without extension (whisper.cpp ``-of``)
    ``{output_dir}``   a scratch directory the command may fill
    ``{model}``        ``model`` from the profile, if set
    ``{language}``     ``language`` from the profile, when not ``auto``

    If the command writes nothing, its stdout is parsed instead - which is what
    transcribers that stream JSON or SRT to stdout do.
    """

    def preflight(self) -> None:
        executable = self.config.command[0]
        if shutil.which(executable) is None and not Path(executable).exists():
            raise AsrError(f"Transcriber command not found on PATH: {executable}")

    def transcribe(self, audio_path: Path, *, progress: Any = None) -> Transcription:
        self.preflight()
        with tempfile.TemporaryDirectory(prefix="dictation-asr-") as raw_dir:
            work = Path(raw_dir)
            output = work / "transcript.json"
            substitutions = {
                "audio": str(audio_path),
                "output": str(output),
                "output_stem": str(output.with_suffix("")),
                "output_dir": str(work),
                "model": self.config.model,
                "language": "" if self.config.language == "auto" else self.config.language,
            }
            argv = [_substitute(arg, substitutions) for arg in self.config.command]

            try:
                completed = subprocess.run(
                    argv,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self.config.timeout,
                    # Same Windows code-page trap as the CLI text provider: a
                    # transcript printed to a pipe must not be re-encoded.
                    env=utf8_environment(),
                    shell=False,
                )
            except FileNotFoundError as exc:
                raise AsrError(f"Transcriber command not found: {argv[0]}") from exc
            except subprocess.TimeoutExpired as exc:
                raise AsrError(f"Transcriber timed out after {self.config.timeout:g}s.") from exc

            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()[:500]
                raise AsrError(f"Transcriber exited {completed.returncode}: {stderr or '(no stderr)'}")

            produced = sorted(
                path
                for path in work.rglob("*")
                if path.is_file() and path.suffix.lower() in {".json", ".srt", ".vtt", ".tsv"}
            )
            if produced:
                segments = parse_transcript_file(produced[0])
                source = produced[0].name
            else:
                segments = parse_transcript_text(completed.stdout or "", hint="stdout")
                source = "stdout"

        if not segments:
            raise AsrError(
                "The transcriber produced no timed segments.\n"
                "  Make sure the command writes JSON/SRT/VTT to {output} (or its stdout)."
            )
        describe = dict(self.config.describe())
        describe["transcriptSource"] = source
        return Transcription(
            segments=segments,
            language=self.config.language if self.config.language != "auto" else "",
            duration=max((segment.end for segment in segments), default=0.0),
            provider=describe,
        )


def _substitute(argument: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        argument = argument.replace("{" + key + "}", value)
    return argument


# --------------------------------------------------------------------------
# Over-long segment repair
# --------------------------------------------------------------------------


def split_long_segments(
    segments: list[Segment],
    *,
    max_seconds: float,
    min_gap: float = 0.4,
    min_piece: float = 0.8,
) -> tuple[list[Segment], int]:
    """Split segments that are too long to dictate, at their widest internal pause.

    A VAD-filtered transcription reports timestamps on the *original* timeline, so
    a segment spanning a removed silence carries that silence in its duration: a
    "20 second maximum speech chunk" becomes a 51-second sentence with half a
    minute of nothing in the middle. No VAD setting prevents this, because the
    length is an artefact of mapping back, not of the speech.

    This project has fixed exactly that by hand before - ``assets/content_patches``
    records repairing "a break encoded as a 35-second utterance". Word timings
    make the same repair mechanical: cut at the largest gap between consecutive
    words, and keep cutting until every piece is short enough or no real pause
    remains to cut at.

    ``min_piece`` stops the repair from causing the defect next door: cutting at
    the widest gap can leave a half-second tail, and the quality audit flags
    anything under 350 ms as unusable. A cut that would produce a fragment
    shorter than this is skipped in favour of the next-widest real pause.

    Returns the new list and how many splits were made. Segments without word
    timings are returned untouched - there is nothing to cut on, and guessing a
    boundary would put a cut in the middle of a word.
    """
    if max_seconds <= 0:
        return segments, 0

    result: list[Segment] = []
    splits = 0
    for segment in segments:
        pieces = _split_one(
            segment, max_seconds=max_seconds, min_gap=min_gap, min_piece=min_piece
        )
        splits += len(pieces) - 1
        result.extend(pieces)
    return result, splits


def _split_one(
    segment: Segment, *, max_seconds: float, min_gap: float, min_piece: float
) -> list[Segment]:
    if (segment.end - segment.start) <= max_seconds or len(segment.words) < 2:
        return [segment]

    candidates: list[tuple[float, int]] = []
    for index in range(1, len(segment.words)):
        gap = float(segment.words[index].get("start", 0.0)) - float(
            segment.words[index - 1].get("end", 0.0)
        )
        if gap <= min_gap:
            continue
        left_end = float(segment.words[index - 1].get("end", segment.start))
        right_start = float(segment.words[index].get("start", segment.end))
        if left_end - segment.start < min_piece or segment.end - right_start < min_piece:
            continue
        candidates.append((gap, index))

    if not candidates:
        # Genuinely continuous speech that is simply long, or every usable pause
        # sits too close to an edge. Cutting mid-phrase would be worse than
        # leaving it for the quality audit to flag.
        return [segment]

    _, best_index = max(candidates)
    left = _segment_from_words(segment, segment.words[:best_index])
    right = _segment_from_words(segment, segment.words[best_index:])
    if left is None or right is None:
        return [segment]
    return _split_one(
        left, max_seconds=max_seconds, min_gap=min_gap, min_piece=min_piece
    ) + _split_one(right, max_seconds=max_seconds, min_gap=min_gap, min_piece=min_piece)


def _segment_from_words(source: Segment, words: list[dict[str, Any]]) -> Segment | None:
    if not words:
        return None
    text = "".join(str(word.get("word") or "") for word in words).strip()
    if not text:
        return None
    return Segment(
        start=float(words[0].get("start", source.start)),
        end=float(words[-1].get("end", source.end)),
        text=text,
        avg_logprob=source.avg_logprob,
        no_speech_prob=source.no_speech_prob,
        compression_ratio=source.compression_ratio,
        words=words,
    )


# --------------------------------------------------------------------------
# Import an existing transcript
# --------------------------------------------------------------------------


class ImportTranscriptProvider(AsrProvider):
    def preflight(self) -> None:
        path = Path(self.config.transcript_path).expanduser()
        if not path.is_file():
            raise AsrError(f"Transcript file not found: {path}")

    def transcribe(self, audio_path: Path, *, progress: Any = None) -> Transcription:
        self.preflight()
        path = Path(self.config.transcript_path).expanduser().resolve()
        segments = parse_transcript_file(path)
        if not segments:
            raise AsrError(f"No timed segments found in {path}.")
        describe = dict(self.config.describe())
        describe["transcriptSource"] = path.name
        return Transcription(
            segments=segments,
            language=self.config.language if self.config.language != "auto" else "",
            duration=max((segment.end for segment in segments), default=0.0),
            provider=describe,
        )


# --------------------------------------------------------------------------
# Transcript parsing, shared by the command and import kinds
# --------------------------------------------------------------------------


def parse_transcript_file(path: Path) -> list[Segment]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return parse_transcript_text(text, hint=path.name)


def parse_transcript_text(text: str, *, hint: str = "transcript") -> list[Segment]:
    """Accept the transcript shapes real tools emit, and say so when one is not."""
    stripped = text.strip()
    if not stripped:
        return []

    if stripped[0] in "[{":
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            data = None
        if data is not None:
            segments = _segments_from_any_json(data)
            if segments:
                return segments

    if "-->" in stripped:
        return _segments_from_subtitles(stripped)

    raise AsrError(
        f"Could not read {hint} as a timed transcript.\n"
        "  Supported: Whisper verbose_json, whisper.cpp JSON, a {start,end,text} array,\n"
        "  this project's segments.raw.json, SRT, or WebVTT."
    )


def _segments_from_any_json(data: Any) -> list[Segment]:
    if isinstance(data, list):
        return _segments_from_items(data)
    if not isinstance(data, dict):
        return []
    for key in ("segments", "sentences", "transcription", "chunks", "results"):
        value = data.get(key)
        if isinstance(value, list):
            segments = _segments_from_items(value)
            if segments:
                return segments
    return []


def _segments_from_whisper_json(data: dict[str, Any]) -> list[Segment]:
    return _segments_from_any_json(data)


def _segments_from_items(items: list[Any]) -> list[Segment]:
    segments: list[Segment] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = str(
            item.get("text")
            or item.get("sourceText")
            or item.get("jaText")
            or item.get("sentence")
            or ""
        ).strip()
        start, end = _times_from_item(item)
        if start is None or end is None or not text:
            continue
        segments.append(
            Segment(
                start=start,
                end=end,
                text=text,
                avg_logprob=_optional_float(item.get("avg_logprob") or item.get("avgLogprob")),
                no_speech_prob=_optional_float(item.get("no_speech_prob") or item.get("noSpeechProb")),
                compression_ratio=_optional_float(
                    item.get("compression_ratio") or item.get("compressionRatio")
                ),
            )
        )
    return segments


def _times_from_item(item: dict[str, Any]) -> tuple[float | None, float | None]:
    start = _optional_float(item.get("start"))
    end = _optional_float(item.get("end"))
    if start is None:
        start = _optional_float(item.get("startTime"))
    if end is None:
        end = _optional_float(item.get("endTime"))

    # whisper.cpp: {"offsets": {"from": ms, "to": ms}}
    offsets = item.get("offsets")
    if start is None and isinstance(offsets, dict):
        from_ms = _optional_float(offsets.get("from"))
        to_ms = _optional_float(offsets.get("to"))
        if from_ms is not None and to_ms is not None:
            return from_ms / 1000.0, to_ms / 1000.0

    # transformers pipelines: {"timestamp": [start, end]}
    timestamp = item.get("timestamp")
    if start is None and isinstance(timestamp, (list, tuple)) and len(timestamp) == 2:
        return _optional_float(timestamp[0]), _optional_float(timestamp[1])

    return start, end


_TIMECODE = re.compile(
    r"(?P<h>\d+):(?P<m>\d{2}):(?P<s>\d{2})[.,](?P<ms>\d{1,3})"
    r"\s*-->\s*"
    r"(?P<h2>\d+):(?P<m2>\d{2}):(?P<s2>\d{2})[.,](?P<ms2>\d{1,3})"
)


def _segments_from_subtitles(text: str) -> list[Segment]:
    segments: list[Segment] = []
    blocks = re.split(r"\r?\n\s*\r?\n", text.strip())
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        match = None
        body_start = 0
        for index, line in enumerate(lines):
            match = _TIMECODE.search(line)
            if match:
                body_start = index + 1
                break
        if not match:
            continue
        body = " ".join(lines[body_start:]).strip()
        if not body:
            continue
        segments.append(
            Segment(
                start=_timecode_seconds(match.group("h"), match.group("m"), match.group("s"), match.group("ms")),
                end=_timecode_seconds(match.group("h2"), match.group("m2"), match.group("s2"), match.group("ms2")),
                text=body,
            )
        )
    return segments


def _timecode_seconds(hours: str, minutes: str, seconds: str, millis: str) -> float:
    fraction = float(f"0.{millis}")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + fraction


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number
