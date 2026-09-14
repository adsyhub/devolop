"""Which model runs a build must be decidable before the build starts.

The regression these guard is the one that motivated the provider layer: a model
name living in a source constant, so nobody could tell from a command what had
produced a course, and a retired name failed at the first batch instead of at
startup.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from provider_config import (  # noqa: E402
    ConfigError,
    load_config_file,
    resolve_asr_provider,
    resolve_text_provider,
)

SAMPLE_CONFIG = {
    "defaultTextProfile": "hosted",
    "defaultAsrProfile": "local",
    "textProfiles": {
        "hosted": {
            "kind": "openai-compat",
            "baseUrl": "https://api.example.com/v1",
            "apiKeyEnv": "EXAMPLE_KEY",
            "model": "profile-model",
            "batchSize": 7,
        },
        "local": {
            "kind": "openai-compat",
            "baseUrl": "http://127.0.0.1:11434/v1",
            "model": "local-model",
        },
    },
    "asrProfiles": {
        "local": {"kind": "faster-whisper", "model": "small", "device": "cpu"},
    },
}


class EnvSandbox(unittest.TestCase):
    """Provider resolution reads the environment, so each test gets a clean one."""

    def setUp(self) -> None:
        self._saved = dict(os.environ)
        for name in list(os.environ):
            if name.startswith("DICTATION_"):
                del os.environ[name]

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._saved)


class NoHiddenDefaultsTests(EnvSandbox):
    def test_network_provider_without_a_model_fails_at_startup(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            resolve_text_provider(overrides={"kind": "openai-compat", "baseUrl": "http://127.0.0.1:1234/v1"})
        message = str(caught.exception)
        self.assertIn("No model set", message)
        # The error must be actionable: it names every way to supply one.
        self.assertIn("--model", message)
        self.assertIn("DICTATION_TEXT_MODEL", message)
        self.assertIn("providers.json", message)

    def test_network_provider_without_a_base_url_fails_at_startup(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            resolve_text_provider(overrides={"kind": "openai-compat", "model": "x"})
        self.assertIn("No baseUrl", str(caught.exception))

    def test_faster_whisper_without_a_model_fails_at_startup(self) -> None:
        with self.assertRaises(ConfigError):
            resolve_asr_provider(overrides={"kind": "faster-whisper"})

    def test_kinds_that_need_no_model_resolve(self) -> None:
        cli = resolve_text_provider(overrides={"kind": "cli", "command": "my-tool --json"})
        self.assertEqual(cli.command, ("my-tool", "--json"))
        manual = resolve_text_provider(overrides={"kind": "manual", "handoffDir": "./out"})
        self.assertEqual(manual.handoff_dir, "./out")
        self.assertTrue(resolve_text_provider(overrides={"kind": "echo"}).is_stub)


class PrecedenceTests(EnvSandbox):
    def test_profile_supplies_values(self) -> None:
        config = resolve_text_provider(config=SAMPLE_CONFIG, profile="hosted")
        self.assertEqual(config.model, "profile-model")
        self.assertEqual(config.batch_size, 7)

    def test_environment_beats_the_profile(self) -> None:
        os.environ["DICTATION_TEXT_MODEL"] = "env-model"
        config = resolve_text_provider(config=SAMPLE_CONFIG, profile="hosted")
        self.assertEqual(config.model, "env-model")

    def test_flags_beat_the_environment(self) -> None:
        os.environ["DICTATION_TEXT_MODEL"] = "env-model"
        config = resolve_text_provider(
            config=SAMPLE_CONFIG, profile="hosted", overrides={"model": "flag-model"}
        )
        self.assertEqual(config.model, "flag-model")

    def test_environment_selects_the_profile(self) -> None:
        os.environ["DICTATION_TEXT_PROFILE"] = "local"
        config = resolve_text_provider(config=SAMPLE_CONFIG)
        self.assertEqual(config.model, "local-model")

    def test_default_profile_applies_when_nothing_else_asks(self) -> None:
        config = resolve_text_provider(config=SAMPLE_CONFIG)
        self.assertEqual(config.label, "hosted")

    def test_unknown_profile_lists_what_exists(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            resolve_text_provider(config=SAMPLE_CONFIG, profile="nope")
        message = str(caught.exception)
        self.assertIn("hosted", message)
        self.assertIn("local", message)


class SecretsTests(EnvSandbox):
    def test_a_config_holding_a_literal_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "providers.json"
            path.write_text(
                json.dumps({"textProfiles": {"x": {"apiKey": "sk-real-secret"}}}),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError) as caught:
                load_config_file(path)
        message = str(caught.exception)
        self.assertIn("apiKey", message)
        self.assertIn("apiKeyEnv", message)
        # The rejection must not echo the secret it just found.
        self.assertNotIn("sk-real-secret", message)

    def test_describe_never_includes_the_key(self) -> None:
        os.environ["EXAMPLE_KEY"] = "sk-do-not-log-me"
        config = resolve_text_provider(config=SAMPLE_CONFIG, profile="hosted")
        self.assertEqual(config.api_key(), "sk-do-not-log-me")
        self.assertNotIn("sk-do-not-log-me", json.dumps(config.describe()))
        self.assertEqual(config.describe()["apiKeyEnv"], "EXAMPLE_KEY")

    def test_remote_endpoint_without_a_key_variable_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            resolve_text_provider(
                overrides={"kind": "openai-compat", "model": "m", "baseUrl": "https://api.example.com/v1"}
            )
        self.assertIn("apiKeyEnv", str(caught.exception))

    def test_local_endpoint_needs_no_key_variable(self) -> None:
        config = resolve_text_provider(
            overrides={"kind": "openai-compat", "model": "m", "baseUrl": "http://127.0.0.1:11434/v1"}
        )
        self.assertEqual(config.api_key_env, "")


class ValidationTests(EnvSandbox):
    def test_unknown_kind_is_rejected_by_name(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            resolve_text_provider(overrides={"kind": "telepathy", "model": "m"})
        self.assertIn("telepathy", str(caught.exception))

    def test_out_of_range_numbers_are_rejected(self) -> None:
        for overrides in (
            {"kind": "echo", "temperature": 9},
            {"kind": "echo", "batchSize": 0},
            {"kind": "echo", "timeout": -1},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ConfigError):
                resolve_text_provider(overrides=overrides)

    def test_asr_cache_key_changes_when_settings_change(self) -> None:
        first = resolve_asr_provider(config=SAMPLE_CONFIG, profile="local")
        second = resolve_asr_provider(
            config=SAMPLE_CONFIG, profile="local", overrides={"model": "large-v3"}
        )
        # A resumed build compares these; equal keys would silently reuse a
        # transcription made by a different model.
        self.assertNotEqual(first.cache_key(), second.cache_key())

    def test_cache_key_ignores_the_profile_name(self) -> None:
        first = resolve_asr_provider(config=SAMPLE_CONFIG, profile="local")
        second = resolve_asr_provider(
            overrides={"kind": "faster-whisper", "model": "small", "device": "cpu"}
        )
        self.assertEqual(first.cache_key(), second.cache_key())


class LanguageRoutingTests(EnvSandbox):
    """The right transcriber is language-specific, so picking it should not be
    something the operator has to remember on every single run."""

    ROUTED = {
        "defaultAsrProfile": "fallback",
        "asrLanguageProfiles": {"ja": "japanese", "en": "english"},
        "asrProfiles": {
            "japanese": {"kind": "faster-whisper", "model": "kotoba", "supportsWordTimestamps": False},
            "english": {"kind": "faster-whisper", "model": "distil-en"},
            "fallback": {"kind": "faster-whisper", "model": "large-v3"},
        },
    }

    def test_language_selects_its_profile(self) -> None:
        self.assertEqual(resolve_asr_provider(config=self.ROUTED, language="ja").model, "kotoba")
        self.assertEqual(resolve_asr_provider(config=self.ROUTED, language="en").model, "distil-en")

    def test_language_aliases_route_too(self) -> None:
        self.assertEqual(resolve_asr_provider(config=self.ROUTED, language="jp").model, "kotoba")
        self.assertEqual(resolve_asr_provider(config=self.ROUTED, language="en-US").model, "distil-en")

    def test_auto_does_not_route(self) -> None:
        """Language is unknown until the audio is read; a Japanese model
        transcribing English is worse than a slower general one."""
        self.assertEqual(resolve_asr_provider(config=self.ROUTED, language="auto").model, "large-v3")
        self.assertEqual(resolve_asr_provider(config=self.ROUTED).model, "large-v3")

    def test_unmapped_language_falls_back(self) -> None:
        self.assertEqual(resolve_asr_provider(config=self.ROUTED, language="ko").model, "large-v3")

    def test_explicit_profile_beats_routing(self) -> None:
        resolved = resolve_asr_provider(config=self.ROUTED, profile="fallback", language="ja")
        self.assertEqual(resolved.model, "large-v3")

    def test_routing_is_absent_when_no_map_is_configured(self) -> None:
        config = {"defaultAsrProfile": "fallback", "asrProfiles": self.ROUTED["asrProfiles"]}
        self.assertEqual(resolve_asr_provider(config=config, language="ja").model, "large-v3")


class DecodingOptionTests(EnvSandbox):
    """The knobs that address this project's recorded transcription failures:
    hallucination clusters, duplicated fragments, and a pause emitted as one
    35-second utterance."""

    def test_defaults_match_faster_whisper_so_old_profiles_behave_the_same(self) -> None:
        config = resolve_asr_provider(overrides={"kind": "faster-whisper", "model": "m"})
        self.assertTrue(config.condition_on_previous_text)
        self.assertEqual(config.no_speech_threshold, 0.6)
        self.assertIsNone(config.hallucination_silence_threshold)
        self.assertEqual(config.vad_options, {})

    def test_vad_options_are_translated_to_silero_names(self) -> None:
        config = resolve_asr_provider(
            overrides={
                "kind": "faster-whisper",
                "model": "m",
                "vadOptions": {"maxSpeechDurationS": 20, "minSilenceDurationMs": 500},
            }
        )
        self.assertEqual(
            config.vad_options, {"max_speech_duration_s": 20.0, "min_silence_duration_ms": 500}
        )

    def test_a_misspelled_vad_option_is_rejected_rather_than_ignored(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            resolve_asr_provider(
                overrides={"kind": "faster-whisper", "model": "m", "vadOptions": {"maxSpeechDuration": 20}}
            )
        message = str(caught.exception)
        self.assertIn("maxSpeechDuration", message)
        self.assertIn("maxSpeechDurationS", message)

    def test_decoding_settings_change_the_resume_cache_key(self) -> None:
        base = resolve_asr_provider(overrides={"kind": "faster-whisper", "model": "m"})
        tuned = resolve_asr_provider(
            overrides={"kind": "faster-whisper", "model": "m", "conditionOnPreviousText": False}
        )
        # Otherwise a resumed build would reuse a transcription decoded differently.
        self.assertNotEqual(base.cache_key(), tuned.cache_key())

    def test_word_timestamps_are_refused_when_the_model_cannot_survive_them(self) -> None:
        """Asking kotoba-whisper for word timestamps segfaults the process, and a
        segfault cannot be caught, so it has to be refused before loading."""
        with self.assertRaises(ConfigError) as caught:
            resolve_asr_provider(
                overrides={
                    "kind": "faster-whisper",
                    "model": "kotoba",
                    "supportsWordTimestamps": False,
                    "wordTimestamps": True,
                }
            )
        self.assertIn("word timestamps", str(caught.exception))

    def test_word_timestamps_are_allowed_by_default(self) -> None:
        config = resolve_asr_provider(
            overrides={"kind": "faster-whisper", "model": "large-v3", "wordTimestamps": True}
        )
        self.assertTrue(config.word_timestamps)


class ExampleConfigTests(unittest.TestCase):
    def test_the_shipped_example_config_loads_and_resolves(self) -> None:
        """A broken example is worse than none: it is the first thing copied."""
        config, path = load_config_file(PROJECT_DIR / "config" / "providers.example.json")
        self.assertIsNotNone(path)
        for name in config["textProfiles"]:
            with self.subTest(profile=name):
                resolved = resolve_text_provider(config=config, profile=name)
                self.assertEqual(resolved.label, name)
        for name in config["asrProfiles"]:
            with self.subTest(asr_profile=name):
                resolve_asr_provider(config=config, profile=name)

    def test_the_shipped_language_map_points_at_profiles_that_exist(self) -> None:
        config, _ = load_config_file(PROJECT_DIR / "config" / "providers.example.json")
        for code, profile in config["asrLanguageProfiles"].items():
            with self.subTest(language=code):
                self.assertIn(profile, config["asrProfiles"])
                self.assertEqual(resolve_asr_provider(config=config, language=code).label, profile)


if __name__ == "__main__":
    unittest.main()
