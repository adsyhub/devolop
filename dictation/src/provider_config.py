"""Resolve which model actually runs a build - from config, env, and flags.

The previous pipeline hard-coded ``deepseek-v4-flash`` and ``large-v3`` as module
constants, so "which model produced this course" was a property of the source
file rather than of the build. That is wrong twice over: it silently pins every
user to one vendor, and it means a model being retired breaks the tool at the
batch stage rather than at startup.

Here nothing is pinned. A provider is a *profile* resolved in this order, last
wins::

    built-in shape defaults -> config file profile -> environment -> CLI flags

and a network provider with no model resolved is a startup error naming the three
ways to set one, not a guess.

Secrets rule, inherited from the local API boundary: a profile stores the *name*
of the environment variable holding the key (``apiKeyEnv``), never the key. A
literal ``apiKey`` in a config file is rejected outright - config files get
committed, shared, and pasted into issues.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PROJECT_DIR = Path(__file__).resolve().parent.parent

TEXT_KINDS = ("openai-compat", "anthropic", "ollama", "cli", "manual", "echo")
ASR_KINDS = ("faster-whisper", "openai-audio", "command", "import")

# Kinds that reach a model over the network and therefore must name one.
NETWORK_TEXT_KINDS = frozenset({"openai-compat", "anthropic", "ollama"})
# Kinds that cannot be trusted to have produced real teaching content.
STUB_TEXT_KINDS = frozenset({"echo"})

CONFIG_ENV = "DICTATION_PROVIDERS_CONFIG"
PROJECT_CONFIG = PROJECT_DIR / "config" / "providers.json"
EXAMPLE_CONFIG = PROJECT_DIR / "config" / "providers.example.json"

_ENV_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class ConfigError(SystemExit):
    """Startup-time configuration failure, phrased as an action the user can take."""


@dataclass(frozen=True)
class TextProviderConfig:
    """How to obtain translations and explanations for one batch of sentences."""

    kind: str = "openai-compat"
    label: str = "inline"
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""
    timeout: float = 180.0
    max_tokens: int = 16000
    temperature: float = 0.2
    retries: int = 3
    sleep: float = 0.5
    batch_size: int = 25
    json_mode: bool = True
    headers: dict[str, str] = field(default_factory=dict)
    extra_body: dict[str, Any] = field(default_factory=dict)
    command: tuple[str, ...] = ()
    handoff_dir: str = ""

    @property
    def is_stub(self) -> bool:
        return self.kind in STUB_TEXT_KINDS

    def api_key(self) -> str:
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "")

    def describe(self) -> dict[str, Any]:
        """Metadata safe to print and to embed in a manifest. Never the key."""
        described: dict[str, Any] = {
            "kind": self.kind,
            "profile": self.label,
            "model": self.model or None,
            "baseUrl": self.base_url or None,
            "apiKeyEnv": self.api_key_env or None,
            "batchSize": self.batch_size,
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
        }
        if self.command:
            described["command"] = list(self.command)
        if self.handoff_dir:
            described["handoffDir"] = self.handoff_dir
        if self.extra_body:
            described["extraBody"] = self.extra_body
        return {key: value for key, value in described.items() if value is not None}

    def cache_key(self) -> dict[str, Any]:
        """Settings that make an enrichment result unsafe to reuse.

        The profile label is deliberately excluded: renaming a profile without
        changing what it calls should not invalidate a long build.  Secrets are
        never included; the environment-variable *name* is enough provenance.
        """
        described = self.describe()
        described.pop("profile", None)
        return described


@dataclass(frozen=True)
class AsrProviderConfig:
    """How to turn audio into timed segments.

    The decoding and VAD fields below exist because this project's own repair
    history names exactly what they control. ``assets/content_patches/`` records
    a 51-second hallucination cluster, duplicated fragments, and "a break encoded
    as a 35-second utterance" - none of which are accuracy problems a better
    model fixes. They are decoding-strategy problems, and until now not one of
    the knobs that address them was reachable from a config file.

    They also matter for the distilled models: a reduced decoder buys speed at
    the cost of timestamp precision and repetition resistance, so shipping one
    without these settings would be shipping a known-bad default.
    """

    kind: str = "faster-whisper"
    label: str = "inline"
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""
    device: str = "auto"
    compute_type: str = "int8"
    language: str = "auto"
    beam_size: int = 5
    vad: bool = True
    word_timestamps: bool = False
    min_duration: float = 0.2
    timeout: float = 1800.0
    headers: dict[str, str] = field(default_factory=dict)
    command: tuple[str, ...] = ()
    transcript_path: str = ""

    # Decoding strategy. Defaults match faster-whisper's own so an unset profile
    # behaves exactly as before.
    condition_on_previous_text: bool = True
    no_speech_threshold: float = 0.6
    log_prob_threshold: float = -1.0
    compression_ratio_threshold: float = 2.4
    hallucination_silence_threshold: float | None = None
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0
    initial_prompt: str = ""

    #: Silero VAD settings. ``maxSpeechDurationS`` is the one that prevents a
    #: pause from being emitted as a single 35-second "sentence".
    vad_options: dict[str, Any] = field(default_factory=dict)

    #: Split any segment longer than this at its widest internal pause, using
    #: word timings. 0 disables it. Requires wordTimestamps.
    max_segment_seconds: float = 0.0

    #: Some CTranslate2 conversions have no usable alignment heads, and asking
    #: them for word timestamps segfaults the interpreter rather than raising.
    #: A crash cannot be caught in-process, so the profile has to declare it.
    #: Measured true for kotoba-whisper-v2.0-faster; large-v3 and
    #: faster-distil-whisper-large-v3 are both fine.
    supports_word_timestamps: bool = True

    def api_key(self) -> str:
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "")

    def describe(self) -> dict[str, Any]:
        described: dict[str, Any] = {
            "kind": self.kind,
            "profile": self.label,
            "model": self.model or None,
            "baseUrl": self.base_url or None,
            "apiKeyEnv": self.api_key_env or None,
            "device": self.device,
            "computeType": self.compute_type,
            "language": self.language,
            "beamSize": self.beam_size,
            "vadFilter": self.vad,
            "wordTimestamps": self.word_timestamps,
            "minDuration": self.min_duration,
            "conditionOnPreviousText": self.condition_on_previous_text,
            "noSpeechThreshold": self.no_speech_threshold,
            "logProbThreshold": self.log_prob_threshold,
            "compressionRatioThreshold": self.compression_ratio_threshold,
            "hallucinationSilenceThreshold": self.hallucination_silence_threshold,
            "repetitionPenalty": self.repetition_penalty,
            "noRepeatNgramSize": self.no_repeat_ngram_size,
            "maxSegmentSeconds": self.max_segment_seconds,
        }
        if self.initial_prompt:
            described["initialPrompt"] = self.initial_prompt
        if self.vad_options:
            described["vadOptions"] = dict(self.vad_options)
        if self.command:
            described["command"] = list(self.command)
        if self.transcript_path:
            described["transcript"] = self.transcript_path
        return {key: value for key, value in described.items() if value is not None}

    def cache_key(self) -> dict[str, Any]:
        """The subset that invalidates a cached transcription when it changes."""
        described = self.describe()
        described.pop("profile", None)
        return described


def load_config_file(explicit: str | Path | None = None) -> tuple[dict[str, Any], Path | None]:
    """Return (config, path). A missing file is not an error; a broken one is."""
    for candidate in _config_candidates(explicit):
        if candidate is None or not candidate.is_file():
            continue
        try:
            with candidate.open("r", encoding="utf-8-sig") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Provider config is not valid JSON: {candidate}\n  {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"Provider config must be a JSON object: {candidate}")
        _reject_inline_secrets(data, candidate)
        return data, candidate

    if explicit:
        raise ConfigError(f"Provider config not found: {explicit}")
    return {}, None


def _config_candidates(explicit: str | Path | None) -> list[Path | None]:
    if explicit:
        return [Path(explicit).expanduser()]
    candidates: list[Path | None] = []
    from_env = os.environ.get(CONFIG_ENV, "").strip()
    if from_env:
        candidates.append(Path(from_env).expanduser())
    candidates.append(PROJECT_CONFIG)
    candidates.append(_user_config_path())
    return candidates


def _user_config_path() -> Path:
    appdata = os.environ.get("APPDATA", "").strip()
    if appdata:
        return Path(appdata) / "dictation" / "providers.json"
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "dictation" / "providers.json"


def _reject_inline_secrets(data: dict[str, Any], path: Path) -> None:
    """Refuse a config that stores a key instead of the name of a key's env var."""
    offenders: list[str] = []

    def walk(node: Any, trail: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                here = f"{trail}.{key}" if trail else key
                if key in {"apiKey", "api_key", "token", "secret"} and str(value or "").strip():
                    offenders.append(here)
                walk(value, here)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{trail}[{index}]")

    walk(data, "")
    if offenders:
        raise ConfigError(
            f"Provider config stores a secret in plain text: {path}\n"
            f"  Offending field(s): {', '.join(sorted(set(offenders)))}\n"
            '  Use "apiKeyEnv": "MY_KEY_VAR" and export the key in the environment instead.'
        )


def expand_env(value: Any) -> Any:
    """Substitute ${VAR} in header values so tokens stay out of the config file."""
    if isinstance(value, str):
        return _ENV_PLACEHOLDER.sub(lambda match: os.environ.get(match.group(1), ""), value)
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    return value


def resolve_text_provider(
    *,
    config: dict[str, Any] | None = None,
    profile: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> TextProviderConfig:
    config = config or {}
    profiles = _profiles(config, "textProfiles")
    name = (
        (profile or "").strip()
        or os.environ.get("DICTATION_TEXT_PROFILE", "").strip()
        or str(config.get("defaultTextProfile") or "").strip()
    )
    raw = _select_profile(profiles, name, "text")
    settings = dict(raw)
    settings.update(_env_overrides("DICTATION_TEXT", _TEXT_ENV_FIELDS))
    settings.update({key: value for key, value in (overrides or {}).items() if value is not None})

    resolved = _build_text_config(settings, label=name or "inline")
    _validate_text(resolved)
    return resolved


def resolve_asr_provider(
    *,
    config: dict[str, Any] | None = None,
    profile: str | None = None,
    overrides: dict[str, Any] | None = None,
    language: str | None = None,
) -> AsrProviderConfig:
    """Resolve the ASR provider, routing by source language when configured.

    The best transcriber is language-specific: a model fine-tuned on Japanese and
    an English-only distilled model are both better choices than one general
    model, and neither is a good choice for the other language. ``asrLanguage
    Profiles`` maps a language code to a profile name so that picking the right
    one is not a thing the operator has to remember on every run.

    An explicit ``--asr-profile`` still wins: routing is a default, not a rule.
    """
    config = config or {}
    profiles = _profiles(config, "asrProfiles")
    name = (
        (profile or "").strip()
        or os.environ.get("DICTATION_ASR_PROFILE", "").strip()
        or asr_profile_for_language(config, language)
        or str(config.get("defaultAsrProfile") or "").strip()
    )
    raw = _select_profile(profiles, name, "asr")
    settings = dict(raw)
    settings.update(_env_overrides("DICTATION_ASR", _ASR_ENV_FIELDS))
    settings.update({key: value for key, value in (overrides or {}).items() if value is not None})

    resolved = _build_asr_config(settings, label=name or "inline")
    _validate_asr(resolved)
    return resolved


_TEXT_ENV_FIELDS = {
    "KIND": "kind",
    "MODEL": "model",
    "BASE_URL": "baseUrl",
    "API_KEY_ENV": "apiKeyEnv",
    "BATCH_SIZE": "batchSize",
    "MAX_TOKENS": "maxTokens",
    "TEMPERATURE": "temperature",
    "TIMEOUT": "timeout",
    "RETRIES": "retries",
}

_ASR_ENV_FIELDS = {
    "KIND": "kind",
    "MODEL": "model",
    "BASE_URL": "baseUrl",
    "API_KEY_ENV": "apiKeyEnv",
    "DEVICE": "device",
    "COMPUTE_TYPE": "computeType",
    "LANGUAGE": "language",
    "TIMEOUT": "timeout",
}


def _env_overrides(prefix: str, fields: dict[str, str]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for suffix, key in fields.items():
        value = os.environ.get(f"{prefix}_{suffix}", "").strip()
        if value:
            found[key] = value
    return found


def _profiles(config: dict[str, Any], key: str) -> dict[str, Any]:
    profiles = config.get(key)
    if profiles is None:
        return {}
    if not isinstance(profiles, dict):
        raise ConfigError(f"Provider config field {key!r} must be an object of named profiles.")
    return profiles


def _select_profile(profiles: dict[str, Any], name: str, family: str) -> dict[str, Any]:
    if not name:
        return {}
    if name not in profiles:
        available = ", ".join(sorted(profiles)) or "(none defined)"
        raise ConfigError(
            f"Unknown {family} profile {name!r}.\n"
            f"  Available: {available}\n"
            f"  Define it in config/providers.json (see {EXAMPLE_CONFIG.name})."
        )
    raw = profiles[name]
    if not isinstance(raw, dict):
        raise ConfigError(f"{family} profile {name!r} must be an object.")
    return raw


def _build_text_config(settings: dict[str, Any], *, label: str) -> TextProviderConfig:
    base = TextProviderConfig()
    return replace(
        base,
        kind=_choice(settings.get("kind"), TEXT_KINDS, base.kind, "text provider kind"),
        label=str(settings.get("label") or label),
        model=str(settings.get("model") or "").strip(),
        base_url=str(settings.get("baseUrl") or "").strip().rstrip("/"),
        api_key_env=str(settings.get("apiKeyEnv") or "").strip(),
        timeout=_positive_float(settings.get("timeout"), base.timeout, "timeout"),
        max_tokens=_positive_int(settings.get("maxTokens"), base.max_tokens, "maxTokens"),
        temperature=_bounded_float(settings.get("temperature"), base.temperature, 0.0, 2.0, "temperature"),
        retries=_positive_int(settings.get("retries"), base.retries, "retries"),
        sleep=_non_negative_float(settings.get("sleep"), base.sleep, "sleep"),
        batch_size=_positive_int(settings.get("batchSize"), base.batch_size, "batchSize"),
        json_mode=_boolean(settings.get("jsonMode"), base.json_mode),
        headers=_string_map(settings.get("headers"), "headers"),
        extra_body=_object(settings.get("extraBody"), "extraBody"),
        command=_command(settings.get("command")),
        handoff_dir=str(settings.get("handoffDir") or "").strip(),
    )


def _build_asr_config(settings: dict[str, Any], *, label: str) -> AsrProviderConfig:
    base = AsrProviderConfig()
    return replace(
        base,
        kind=_choice(settings.get("kind"), ASR_KINDS, base.kind, "asr provider kind"),
        label=str(settings.get("label") or label),
        model=str(settings.get("model") or "").strip(),
        base_url=str(settings.get("baseUrl") or "").strip().rstrip("/"),
        api_key_env=str(settings.get("apiKeyEnv") or "").strip(),
        device=str(settings.get("device") or base.device).strip(),
        compute_type=str(settings.get("computeType") or base.compute_type).strip(),
        language=str(settings.get("language") or base.language).strip(),
        beam_size=_positive_int(settings.get("beamSize"), base.beam_size, "beamSize"),
        vad=_boolean(settings.get("vadFilter"), base.vad),
        word_timestamps=_boolean(settings.get("wordTimestamps"), base.word_timestamps),
        min_duration=_positive_float(settings.get("minDuration"), base.min_duration, "minDuration"),
        timeout=_positive_float(settings.get("timeout"), base.timeout, "timeout"),
        headers=_string_map(settings.get("headers"), "headers"),
        command=_command(settings.get("command")),
        transcript_path=str(settings.get("transcript") or "").strip(),
        condition_on_previous_text=_boolean(
            settings.get("conditionOnPreviousText"), base.condition_on_previous_text
        ),
        no_speech_threshold=_bounded_float(
            settings.get("noSpeechThreshold"), base.no_speech_threshold, 0.0, 1.0, "noSpeechThreshold"
        ),
        log_prob_threshold=_as_float(
            settings.get("logProbThreshold"), base.log_prob_threshold, "logProbThreshold"
        ),
        compression_ratio_threshold=_positive_float(
            settings.get("compressionRatioThreshold"),
            base.compression_ratio_threshold,
            "compressionRatioThreshold",
        ),
        hallucination_silence_threshold=_optional_positive_float(
            settings.get("hallucinationSilenceThreshold"), "hallucinationSilenceThreshold"
        ),
        repetition_penalty=_positive_float(
            settings.get("repetitionPenalty"), base.repetition_penalty, "repetitionPenalty"
        ),
        no_repeat_ngram_size=_non_negative_int(
            settings.get("noRepeatNgramSize"), base.no_repeat_ngram_size, "noRepeatNgramSize"
        ),
        initial_prompt=str(settings.get("initialPrompt") or "").strip(),
        vad_options=_vad_options(settings.get("vadOptions")),
        max_segment_seconds=_non_negative_float(
            settings.get("maxSegmentSeconds"), base.max_segment_seconds, "maxSegmentSeconds"
        ),
        supports_word_timestamps=_boolean(
            settings.get("supportsWordTimestamps"), base.supports_word_timestamps
        ),
    )


_VAD_FIELDS = {
    "threshold": "threshold",
    "negThreshold": "neg_threshold",
    "minSpeechDurationMs": "min_speech_duration_ms",
    "maxSpeechDurationS": "max_speech_duration_s",
    "minSilenceDurationMs": "min_silence_duration_ms",
    "speechPadMs": "speech_pad_ms",
}


def _vad_options(value: Any) -> dict[str, Any]:
    """Translate camelCase VAD settings into the names Silero's options take."""
    if not value:
        return {}
    if not isinstance(value, dict):
        raise ConfigError("vadOptions must be an object.")
    unknown = sorted(set(value) - set(_VAD_FIELDS))
    if unknown:
        raise ConfigError(
            f"Unknown vadOptions field(s): {', '.join(unknown)}.\n"
            f"  Supported: {', '.join(_VAD_FIELDS)}."
        )
    translated: dict[str, Any] = {}
    for camel, snake in _VAD_FIELDS.items():
        if camel not in value or value[camel] is None:
            continue
        number = _as_float(value[camel], 0.0, f"vadOptions.{camel}")
        if number < 0:
            raise ConfigError(f"vadOptions.{camel} must be >= 0.")
        translated[snake] = int(number) if camel.endswith("Ms") else number
    return translated


def _validate_text(config: TextProviderConfig) -> None:
    if config.kind in NETWORK_TEXT_KINDS and not config.model:
        raise ConfigError(
            f"No model set for text provider kind {config.kind!r}.\n"
            "  This project ships no default model on purpose. Set one of:\n"
            "    --model <name>\n"
            "    DICTATION_TEXT_MODEL=<name>\n"
            "    config/providers.json -> textProfiles.<profile>.model"
        )
    if config.kind in NETWORK_TEXT_KINDS and not config.base_url:
        raise ConfigError(
            f"No baseUrl set for text provider kind {config.kind!r}.\n"
            "  Set --base-url, DICTATION_TEXT_BASE_URL, or the profile's baseUrl.\n"
            "  A local runtime is an ordinary value here, e.g. http://127.0.0.1:11434/v1"
        )
    if config.kind == "cli" and not config.command:
        raise ConfigError(
            "Text provider kind 'cli' needs a command.\n"
            '  Example: --command "claude -p --output-format text"\n'
            "  The prompt goes to stdin unless the command contains {prompt_file}."
        )
    if config.kind == "manual" and not config.handoff_dir:
        raise ConfigError(
            "Text provider kind 'manual' needs a handoff directory.\n"
            "  Set --handoff-dir <path>; the build writes prompts there and reads answers back."
        )
    _require_local_or_key(config.kind, config.base_url, config.api_key_env, "text")


def _validate_asr(config: AsrProviderConfig) -> None:
    if config.kind == "faster-whisper" and not config.model:
        raise ConfigError(
            "No model set for ASR kind 'faster-whisper'.\n"
            "  Set --asr-model <name> (tiny, base, small, medium, large-v3, or a local path),\n"
            "  DICTATION_ASR_MODEL, or the profile's model field."
        )
    if config.kind == "openai-audio":
        if not config.model:
            raise ConfigError("No model set for ASR kind 'openai-audio'. Set --asr-model.")
        if not config.base_url:
            raise ConfigError("No baseUrl set for ASR kind 'openai-audio'. Set --asr-base-url.")
        _require_local_or_key(config.kind, config.base_url, config.api_key_env, "asr")
    if config.kind == "command" and not config.command:
        raise ConfigError(
            "ASR kind 'command' needs a command.\n"
            '  Example: --asr-command "whisper-cli -m ggml.bin -f {audio} -oj -of {output_stem}"'
        )
    if config.kind == "import" and not config.transcript_path:
        raise ConfigError("ASR kind 'import' needs --transcript pointing at an existing transcript file.")
    if config.max_segment_seconds > 0 and not config.word_timestamps:
        raise ConfigError(
            "maxSegmentSeconds needs word timings to know where a pause is.\n"
            '  Set "wordTimestamps": true in the same profile, or remove maxSegmentSeconds.'
        )
    if config.word_timestamps and not config.supports_word_timestamps:
        raise ConfigError(
            f"ASR profile {config.label!r} (model {config.model!r}) cannot produce word timestamps.\n"
            "  This conversion has no usable alignment heads: asking for them segfaults the\n"
            "  process instead of raising, so it is refused here rather than mid-transcription.\n"
            "  Drop --word-timestamps, or use a profile whose model supports them (e.g. large-v3)."
        )


def _require_local_or_key(kind: str, base_url: str, api_key_env: str, family: str) -> None:
    """A remote endpoint with no key is nearly always a misconfiguration."""
    if kind in {"cli", "manual", "echo", "import", "command", "faster-whisper"}:
        return
    if api_key_env:
        return
    if is_local_url(base_url):
        return
    raise ConfigError(
        f"Remote {family} endpoint {base_url!r} has no apiKeyEnv.\n"
        "  Set --api-key-env NAME (the variable name, not the key), or point baseUrl at a\n"
        "  local runtime such as http://127.0.0.1:11434/v1 which needs no key."
    )


def is_local_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1", "0.0.0.0", "host.docker.internal"}


def _choice(value: Any, allowed: tuple[str, ...], fallback: str, what: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    if text not in allowed:
        raise ConfigError(f"Unknown {what} {text!r}. Supported: {', '.join(allowed)}.")
    return text


def asr_profile_for_language(config: dict[str, Any], language: str | None) -> str:
    """Return the ASR profile mapped to *language*, or "" when nothing applies.

    ``auto`` deliberately routes nowhere: the language is not known until the
    audio has been read, and silently picking a language-specific model for
    unknown-language audio is how you get a Japanese model transcribing English.
    """
    mapping = config.get("asrLanguageProfiles")
    if not mapping:
        return ""
    if not isinstance(mapping, dict):
        raise ConfigError("Provider config field 'asrLanguageProfiles' must be an object.")
    code = normalize_language_for_routing(language)
    if not code:
        return ""
    return str(mapping.get(code) or "").strip()


def normalize_language_for_routing(language: str | None) -> str:
    """Lower-case base language code, or "" for auto/unset/unrecognised."""
    text = str(language or "").strip().lower().replace("_", "-")
    if not text or text == "auto":
        return ""
    aliases = {"jp": "ja", "kr": "ko", "cn": "zh", "zh-cn": "zh", "zh-tw": "zh"}
    return aliases.get(text, text.split("-", 1)[0])


def _non_negative_int(value: Any, fallback: int, name: str) -> int:
    if value is None or value == "":
        return fallback
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be an integer, got {value!r}.") from exc
    if number < 0:
        raise ConfigError(f"{name} must be >= 0, got {number}.")
    return number


def _optional_positive_float(value: Any, name: str) -> float | None:
    if value is None or value == "":
        return None
    number = _as_float(value, 0.0, name)
    if number <= 0:
        raise ConfigError(f"{name} must be > 0 when set, got {number}.")
    return number


def _positive_int(value: Any, fallback: int, name: str) -> int:
    if value is None or value == "":
        return fallback
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be an integer, got {value!r}.") from exc
    if number < 1:
        raise ConfigError(f"{name} must be >= 1, got {number}.")
    return number


def _positive_float(value: Any, fallback: float, name: str) -> float:
    number = _as_float(value, fallback, name)
    if number <= 0:
        raise ConfigError(f"{name} must be > 0, got {number}.")
    return number


def _non_negative_float(value: Any, fallback: float, name: str) -> float:
    number = _as_float(value, fallback, name)
    if number < 0:
        raise ConfigError(f"{name} must be >= 0, got {number}.")
    return number


def _bounded_float(value: Any, fallback: float, low: float, high: float, name: str) -> float:
    number = _as_float(value, fallback, name)
    if not low <= number <= high:
        raise ConfigError(f"{name} must be between {low} and {high}, got {number}.")
    return number


def _as_float(value: Any, fallback: float, name: str) -> float:
    if value is None or value == "":
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be a number, got {value!r}.") from exc


def _boolean(value: Any, fallback: bool) -> bool:
    if value is None or value == "":
        return fallback
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"Expected a boolean, got {value!r}.")


def _string_map(value: Any, name: str) -> dict[str, str]:
    if not value:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be an object of string values.")
    return {str(key): str(expand_env(item)) for key, item in value.items()}


def _object(value: Any, name: str) -> dict[str, Any]:
    if not value:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be an object.")
    return dict(value)


def _command(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        return tuple(shlex.split(value, posix=os.name != "nt"))
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    raise ConfigError("command must be a string or an array of arguments.")


def list_profiles(config: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "text": sorted(_profiles(config, "textProfiles")),
        "asr": sorted(_profiles(config, "asrProfiles")),
    }
