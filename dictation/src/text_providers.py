"""Text providers: one interface, six ways to reach a model.

Every provider answers the same question - "given a system prompt and a user
prompt, return the model's text" - so the enrichment stage never learns which
one it is talking to. That is what makes the model swappable at the command
line instead of at the source line.

The kinds, and why each exists:

``openai-compat``
    Any endpoint speaking ``POST {base_url}/chat/completions``. One kind covers
    hosted APIs (DeepSeek, OpenAI, Groq, Together, OpenRouter, SiliconFlow) *and*
    local runtimes (Ollama's OpenAI shim, LM Studio, llama.cpp ``llama-server``,
    vLLM, LocalAI, Xinference). A local model is not a special case here; it is
    an ordinary ``baseUrl``.
``anthropic``
    The Messages API, whose request and response shapes differ enough to need
    their own adapter.
``ollama``
    Ollama's native ``/api/chat``, for people who never enable its OpenAI shim.
``cli``
    Runs a command and reads its stdout. This is the "subscription AI as an API"
    path: a seat in an AI coding CLI is not an API key, but it *is* a process
    that answers prompts, so anything that answers on stdout works here.
``manual``
    No automation at all. The build writes prompt files, you answer them in
    whatever chat window your subscription gives you, save the replies next to
    the prompts, and re-run. Slow, but it needs nothing except a browser.
``echo``
    A deterministic offline stub for tests and dry runs. It fabricates nothing:
    it writes a visible placeholder, and the pipeline refuses to package its
    output unless explicitly told to.

Transport is ``urllib`` from the standard library. The player already runs on the
stdlib alone; making the *builder* require an SDK only to POST JSON would have
been the one thing forcing an install step on every provider.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from provider_config import TextProviderConfig

#: Placeholder the stub provider writes. Deliberately unmistakable as a translation.
STUB_EXPLANATION = "[stub] 此句尚未生成讲解，需要接入真实模型或人工校对。"


class ProviderError(RuntimeError):
    """A single attempt failed. The caller decides whether to retry."""


class PendingHandoff(Exception):
    """A manual provider is waiting on a human. Not a failure - an interruption."""

    def __init__(self, pending: list[Path], handoff_dir: Path) -> None:
        self.pending = pending
        self.handoff_dir = handoff_dir
        super().__init__(f"{len(pending)} prompt(s) awaiting a reply in {handoff_dir}")


@dataclass
class Completion:
    """What every provider returns, whatever it is underneath."""

    text: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    stub: bool = False


class TextProvider:
    """Base class. Subclasses implement :meth:`complete` for a single attempt."""

    #: Set on kinds whose output must never be mistaken for real teaching content.
    stub = False

    def __init__(self, config: TextProviderConfig) -> None:
        self.config = config

    def complete(self, system_prompt: str, user_prompt: str, *, batch_name: str, batch: dict[str, Any] | None = None) -> Completion:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return self.config.describe()

    def preflight(self) -> None:
        """Fail before the first batch when the setup obviously cannot work."""


def build_text_provider(config: TextProviderConfig) -> TextProvider:
    builders = {
        "openai-compat": OpenAICompatProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "cli": CliProvider,
        "manual": ManualProvider,
        "echo": EchoProvider,
    }
    try:
        builder = builders[config.kind]
    except KeyError as exc:  # pragma: no cover - guarded by provider_config
        raise ProviderError(f"Unknown text provider kind: {config.kind}") from exc
    return builder(config)


# --------------------------------------------------------------------------
# HTTP transport
# --------------------------------------------------------------------------


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    """POST JSON and return the parsed object, turning transport faults into ProviderError."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for name, value in headers.items():
        if value:
            request.add_header(name, value)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = _read_error_body(exc)
        hint = ""
        if exc.code == 404 and "/v1/" not in url:
            hint = "\n  A 404 here usually means the base URL needs its /v1 suffix."
        if exc.code in {401, 403}:
            hint = "\n  Check that the environment variable named by apiKeyEnv is set in this shell."
        raise ProviderError(f"HTTP {exc.code} from {url}: {detail}{hint}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Cannot reach {url}: {exc.reason}") from exc

    if not raw.strip():
        raise ProviderError(f"Empty response body from {url}.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Response from {url} is not JSON: {raw[:300]}") from exc
    if not isinstance(data, dict):
        raise ProviderError(f"Response from {url} is not a JSON object.")
    return data


def _read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        detail = exc.read().decode("utf-8", errors="replace").strip()
    except Exception:  # pragma: no cover - defensive
        detail = ""
    return detail[:500] or exc.reason or "no error body"


# --------------------------------------------------------------------------
# OpenAI-compatible chat completions
# --------------------------------------------------------------------------


class OpenAICompatProvider(TextProvider):
    """Hosted APIs and local runtimes alike, over /chat/completions."""

    def endpoint(self) -> str:
        return f"{self.config.base_url}/chat/completions"

    def headers(self) -> dict[str, str]:
        headers = dict(self.config.headers)
        key = self.config.api_key()
        if key:
            headers.setdefault("Authorization", f"Bearer {key}")
        return headers

    def preflight(self) -> None:
        if self.config.api_key_env and not self.config.api_key():
            raise ProviderError(
                f"Environment variable {self.config.api_key_env} is empty.\n"
                f'  Set it in this shell, e.g. $env:{self.config.api_key_env}="..."'
            )

    def complete(self, system_prompt: str, user_prompt: str, *, batch_name: str, batch: dict[str, Any] | None = None) -> Completion:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if self.config.json_mode:
            payload["response_format"] = {"type": "json_object"}
        payload.update(self.config.extra_body)

        data = post_json(
            self.endpoint(),
            payload,
            headers=self.headers(),
            timeout=self.config.timeout,
        )
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError(f"Response has no choices: {json.dumps(data)[:300]}")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = (message or {}).get("content") if isinstance(message, dict) else None
        text = _flatten_content(content)
        if not text.strip():
            raise ProviderError("Model returned empty content.")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return Completion(
            text=text,
            model=str(data.get("model") or self.config.model),
            usage={
                "promptTokens": int(usage.get("prompt_tokens") or 0),
                "completionTokens": int(usage.get("completion_tokens") or 0),
                "totalTokens": int(usage.get("total_tokens") or 0),
            },
        )


def _flatten_content(content: Any) -> str:
    """Accept both a plain string and the content-parts array some servers return."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    return ""


# --------------------------------------------------------------------------
# Anthropic Messages API
# --------------------------------------------------------------------------


class AnthropicProvider(TextProvider):
    """The Messages API. Model ids come from config, so nothing here ages."""

    ANTHROPIC_VERSION = "2023-06-01"

    def endpoint(self) -> str:
        base = self.config.base_url
        return f"{base}/v1/messages" if not base.endswith("/v1") else f"{base}/messages"

    def headers(self) -> dict[str, str]:
        headers = dict(self.config.headers)
        headers.setdefault("anthropic-version", self.ANTHROPIC_VERSION)
        key = self.config.api_key()
        if key:
            headers.setdefault("x-api-key", key)
        return headers

    def preflight(self) -> None:
        if self.config.api_key_env and not self.config.api_key():
            raise ProviderError(f"Environment variable {self.config.api_key_env} is empty.")

    def complete(self, system_prompt: str, user_prompt: str, *, batch_name: str, batch: dict[str, Any] | None = None) -> Completion:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        payload.update(self.config.extra_body)

        data = post_json(
            self.endpoint(),
            payload,
            headers=self.headers(),
            timeout=self.config.timeout,
        )
        text = _flatten_content(data.get("content"))
        if not text.strip():
            raise ProviderError("Model returned empty content.")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        prompt_tokens = int(usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("output_tokens") or 0)
        return Completion(
            text=text,
            model=str(data.get("model") or self.config.model),
            usage={
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "totalTokens": prompt_tokens + completion_tokens,
            },
        )


# --------------------------------------------------------------------------
# Ollama native API
# --------------------------------------------------------------------------


class OllamaProvider(TextProvider):
    """Ollama's own /api/chat, for setups that never enable its OpenAI shim."""

    def endpoint(self) -> str:
        base = self.config.base_url
        if base.endswith("/v1"):
            base = base[: -len("/v1")]
        return f"{base}/api/chat"

    def complete(self, system_prompt: str, user_prompt: str, *, batch_name: str, batch: dict[str, Any] | None = None) -> Completion:
        options: dict[str, Any] = {
            "temperature": self.config.temperature,
            "num_predict": self.config.max_tokens,
        }
        payload: dict[str, Any] = {
            "model": self.config.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": options,
        }
        if self.config.json_mode:
            payload["format"] = "json"
        payload.update(self.config.extra_body)

        data = post_json(
            self.endpoint(),
            payload,
            headers=dict(self.config.headers),
            timeout=self.config.timeout,
        )
        message = data.get("message")
        text = _flatten_content(message.get("content")) if isinstance(message, dict) else ""
        if not text.strip():
            raise ProviderError("Model returned empty content.")
        return Completion(
            text=text,
            model=str(data.get("model") or self.config.model),
            usage={
                "promptTokens": int(data.get("prompt_eval_count") or 0),
                "completionTokens": int(data.get("eval_count") or 0),
                "totalTokens": int(data.get("prompt_eval_count") or 0) + int(data.get("eval_count") or 0),
            },
        )


# --------------------------------------------------------------------------
# Command-line bridge: a subscription seat used as an API
# --------------------------------------------------------------------------


class CliProvider(TextProvider):
    """Run a command, feed it the prompt, read the answer from stdout.

    Placeholders in the command, each substituted with a real path or value:

    ``{prompt_file}``  a UTF-8 file holding system prompt + batch prompt
    ``{system_file}``  the system prompt alone
    ``{user_file}``    the batch prompt alone
    ``{model}``        ``model`` from the profile, if set
    ``{batch}``        the batch file name, useful for the command's own logging

    With no ``{prompt_file}``/``{user_file}`` placeholder the prompt is written to
    stdin instead, which is what most one-shot CLIs expect.
    """

    def preflight(self) -> None:
        executable = self.config.command[0]
        if shutil.which(executable) is None and not Path(executable).exists():
            raise ProviderError(
                f"Command not found on PATH: {executable}\n"
                "  Check the profile's command, or use an absolute path to the executable."
            )

    def complete(self, system_prompt: str, user_prompt: str, *, batch_name: str, batch: dict[str, Any] | None = None) -> Completion:
        combined = f"{system_prompt}\n\n{user_prompt}\n"
        with tempfile.TemporaryDirectory(prefix="dictation-cli-") as raw_dir:
            work = Path(raw_dir)
            prompt_file = work / "prompt.txt"
            system_file = work / "system.txt"
            user_file = work / "user.txt"
            prompt_file.write_text(combined, encoding="utf-8")
            system_file.write_text(system_prompt, encoding="utf-8")
            user_file.write_text(user_prompt, encoding="utf-8")

            substitutions = {
                "prompt_file": str(prompt_file),
                "system_file": str(system_file),
                "user_file": str(user_file),
                "model": self.config.model,
                "batch": batch_name,
            }
            argv = [_substitute(arg, substitutions) for arg in self.config.command]
            uses_file = any(
                token in arg
                for arg in self.config.command
                for token in ("{prompt_file}", "{user_file}")
            )
            stdin_text = None if uses_file else combined

            try:
                completed = subprocess.run(
                    argv,
                    input=stdin_text,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self.config.timeout,
                    env=utf8_environment(),
                    # Never shell=True: the command comes from a config file, and a
                    # shell would turn every quoting mistake into an injection.
                    shell=False,
                )
            except FileNotFoundError as exc:
                raise ProviderError(f"Command not found: {argv[0]}") from exc
            except subprocess.TimeoutExpired as exc:
                raise ProviderError(f"Command timed out after {self.config.timeout:g}s: {argv[0]}") from exc

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()[:500]
            raise ProviderError(f"Command exited {completed.returncode}: {stderr or '(no stderr)'}")
        text = (completed.stdout or "").strip()
        if not text:
            stderr = (completed.stderr or "").strip()[:300]
            raise ProviderError(f"Command produced no stdout. stderr: {stderr or '(empty)'}")
        return Completion(text=text, model=self.config.model or f"cli:{Path(self.config.command[0]).name}")


def _substitute(argument: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        argument = argument.replace("{" + key + "}", value)
    return argument


def utf8_environment() -> dict[str, str]:
    """Child environment that will not mangle non-ASCII output.

    On Windows a subprocess writing to a pipe encodes with the active code page,
    not UTF-8, so Chinese and Japanese come back as replacement characters. That
    corruption is invisible until the quality audit rejects the finished course,
    which is a long way to travel for a wrong environment variable. Both settings
    are ignored by tools that do not read them.
    """
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return env


# --------------------------------------------------------------------------
# Manual handoff: any chat window, no API at all
# --------------------------------------------------------------------------


class ManualProvider(TextProvider):
    """Write prompts to disk, read human-supplied replies back.

    The build stops the first time a reply is missing, listing what to answer.
    Re-running picks up every reply that has appeared since, so a course can be
    enriched across several sittings without an API key of any kind.
    """

    def directory(self) -> Path:
        path = Path(self.config.handoff_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def complete(self, system_prompt: str, user_prompt: str, *, batch_name: str, batch: dict[str, Any] | None = None) -> Completion:
        directory = self.directory()
        stem = Path(batch_name).stem
        prompt_path = directory / f"{stem}.prompt.txt"
        reply_path = directory / f"{stem}.reply.json"
        legacy_reply = directory / f"{stem}.reply.txt"

        prompt_text = f"{system_prompt}\n\n{user_prompt}\n"
        if not prompt_path.exists() or prompt_path.read_text(encoding="utf-8") != prompt_text:
            prompt_path.write_text(prompt_text, encoding="utf-8")

        for candidate in (reply_path, legacy_reply):
            if candidate.exists() and candidate.read_text(encoding="utf-8-sig").strip():
                return Completion(
                    text=candidate.read_text(encoding="utf-8-sig"),
                    model=self.config.model or "manual",
                )
        raise PendingHandoff([prompt_path], directory)


# --------------------------------------------------------------------------
# Offline stub
# --------------------------------------------------------------------------


class EchoProvider(TextProvider):
    """Deterministic placeholder output for tests and dry runs.

    It must never look like a translation. Everything it writes is prefixed and
    the build refuses to package it without an explicit opt-in flag, because a
    stub that quietly passes the quality gate is exactly the failure mode this
    project already had once with corrupted enrichment.
    """

    stub = True

    def complete(self, system_prompt: str, user_prompt: str, *, batch_name: str, batch: dict[str, Any] | None = None) -> Completion:
        items = (batch or {}).get("items")
        if not isinstance(items, list):
            raise ProviderError("Echo provider needs the batch it is answering.")
        echoed = [
            {
                "index": int(item["index"]),
                "zhTranslation": "",
                "explanationText": STUB_EXPLANATION,
            }
            for item in items
            if isinstance(item, dict) and "index" in item
        ]
        return Completion(
            text=json.dumps({"items": echoed}, ensure_ascii=False),
            model="echo",
            stub=True,
        )


def provider_env_summary(config: TextProviderConfig) -> str:
    """One printable line describing the provider, never including the key."""
    parts = [f"kind={config.kind}", f"profile={config.label}"]
    if config.model:
        parts.append(f"model={config.model}")
    if config.base_url:
        parts.append(f"baseUrl={config.base_url}")
    if config.api_key_env:
        state = "set" if os.environ.get(config.api_key_env) else "MISSING"
        parts.append(f"apiKeyEnv={config.api_key_env}({state})")
    if config.command:
        parts.append(f"command={config.command[0]}")
    return ", ".join(parts)
