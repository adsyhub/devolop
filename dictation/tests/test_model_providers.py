"""Each provider kind must speak its own wire format correctly.

The HTTP kinds are exercised against a stub server on an ephemeral port rather
than mocked, because the bugs worth catching here live in the request and
response shapes, not in the code that calls them. Nothing reaches the network.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from asr_providers import (  # noqa: E402
    AsrError,
    Segment,
    parse_transcript_text,
    split_long_segments,
)
from provider_config import TextProviderConfig  # noqa: E402
from text_providers import (  # noqa: E402
    PendingHandoff,
    ProviderError,
    build_text_provider,
)

RECORDED: list[dict] = []
RESPONSES: dict[str, object] = {}


class StubHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - http.server's required name
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8")
        RECORDED.append(
            {
                "path": self.path,
                "headers": {key.lower(): value for key, value in self.headers.items()},
                "body": json.loads(body) if body else {},
            }
        )
        response = RESPONSES.get(self.path)
        if response is None:
            self.send_error(404, "no stub for this path")
            return
        if isinstance(response, int):
            self.send_error(response, "stubbed failure")
            return
        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: object) -> None:
        pass


class StubServer:
    """A real HTTP server on an ephemeral port, started and stopped per test."""

    def __init__(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        RECORDED.clear()
        RESPONSES.clear()
        self.thread.start()
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


BATCH = {
    "sourceLanguage": "ja",
    "items": [{"index": 0, "sourceText": "これはテストです。"}],
    "sourceDigest": "digest",
}


class OpenAiCompatTests(unittest.TestCase):
    def test_request_shape_and_authorization(self) -> None:
        with StubServer() as base:
            RESPONSES["/v1/chat/completions"] = {
                "model": "server-reported-model",
                "choices": [{"message": {"content": '{"items": []}'}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
            }
            import os

            os.environ["STUB_KEY"] = "sk-stub"
            provider = build_text_provider(
                TextProviderConfig(
                    kind="openai-compat",
                    base_url=f"{base}/v1",
                    model="requested-model",
                    api_key_env="STUB_KEY",
                    max_tokens=1234,
                    temperature=0.4,
                )
            )
            completion = provider.complete("system", "user", batch_name="batch_001.json", batch=BATCH)

        self.assertEqual(completion.text, '{"items": []}')
        self.assertEqual(completion.model, "server-reported-model")
        self.assertEqual(completion.usage["totalTokens"], 33)

        sent = RECORDED[0]
        self.assertEqual(sent["path"], "/v1/chat/completions")
        self.assertEqual(sent["headers"]["authorization"], "Bearer sk-stub")
        self.assertEqual(sent["body"]["model"], "requested-model")
        self.assertEqual(sent["body"]["max_tokens"], 1234)
        self.assertEqual(sent["body"]["response_format"], {"type": "json_object"})
        self.assertEqual(
            [message["role"] for message in sent["body"]["messages"]], ["system", "user"]
        )

    def test_local_runtime_needs_no_authorization_header(self) -> None:
        with StubServer() as base:
            RESPONSES["/v1/chat/completions"] = {"choices": [{"message": {"content": "ok"}}]}
            provider = build_text_provider(
                TextProviderConfig(kind="openai-compat", base_url=f"{base}/v1", model="local")
            )
            provider.complete("s", "u", batch_name="b", batch=BATCH)
        self.assertNotIn("authorization", RECORDED[0]["headers"])

    def test_content_parts_arrays_are_flattened(self) -> None:
        """Some OpenAI-compatible servers return content as parts, not a string."""
        with StubServer() as base:
            RESPONSES["/v1/chat/completions"] = {
                "choices": [{"message": {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}}]
            }
            provider = build_text_provider(
                TextProviderConfig(kind="openai-compat", base_url=f"{base}/v1", model="m")
            )
            completion = provider.complete("s", "u", batch_name="b", batch=BATCH)
        self.assertEqual(completion.text, "ab")

    def test_extra_body_is_merged_into_the_request(self) -> None:
        with StubServer() as base:
            RESPONSES["/v1/chat/completions"] = {"choices": [{"message": {"content": "ok"}}]}
            provider = build_text_provider(
                TextProviderConfig(
                    kind="openai-compat",
                    base_url=f"{base}/v1",
                    model="m",
                    extra_body={"thinking": {"type": "disabled"}},
                )
            )
            provider.complete("s", "u", batch_name="b", batch=BATCH)
        self.assertEqual(RECORDED[0]["body"]["thinking"], {"type": "disabled"})

    def test_http_error_names_the_status_and_hints_at_the_cause(self) -> None:
        with StubServer() as base:
            RESPONSES["/chat/completions"] = 404
            provider = build_text_provider(
                TextProviderConfig(kind="openai-compat", base_url=base, model="m")
            )
            with self.assertRaises(ProviderError) as caught:
                provider.complete("s", "u", batch_name="b", batch=BATCH)
        message = str(caught.exception)
        self.assertIn("404", message)
        self.assertIn("/v1", message)

    def test_empty_content_is_an_error_not_an_empty_course(self) -> None:
        with StubServer() as base:
            RESPONSES["/v1/chat/completions"] = {"choices": [{"message": {"content": "   "}}]}
            provider = build_text_provider(
                TextProviderConfig(kind="openai-compat", base_url=f"{base}/v1", model="m")
            )
            with self.assertRaises(ProviderError):
                provider.complete("s", "u", batch_name="b", batch=BATCH)


class AnthropicTests(unittest.TestCase):
    def test_messages_api_shape(self) -> None:
        with StubServer() as base:
            RESPONSES["/v1/messages"] = {
                "model": "reported",
                "content": [{"type": "text", "text": '{"items": []}'}],
                "usage": {"input_tokens": 5, "output_tokens": 7},
            }
            import os

            os.environ["ANTHROPIC_STUB_KEY"] = "sk-ant-stub"
            provider = build_text_provider(
                TextProviderConfig(
                    kind="anthropic",
                    base_url=base,
                    model="some-claude-model",
                    api_key_env="ANTHROPIC_STUB_KEY",
                )
            )
            completion = provider.complete("system text", "user text", batch_name="b", batch=BATCH)

        sent = RECORDED[0]
        self.assertEqual(sent["path"], "/v1/messages")
        self.assertEqual(sent["headers"]["x-api-key"], "sk-ant-stub")
        self.assertEqual(sent["headers"]["anthropic-version"], "2023-06-01")
        # The system prompt is a top-level field here, not a message.
        self.assertEqual(sent["body"]["system"], "system text")
        self.assertEqual(sent["body"]["messages"], [{"role": "user", "content": "user text"}])
        self.assertEqual(completion.usage["totalTokens"], 12)

    def test_base_url_already_ending_in_v1_is_not_doubled(self) -> None:
        with StubServer() as base:
            RESPONSES["/v1/messages"] = {"content": [{"type": "text", "text": "ok"}]}
            provider = build_text_provider(
                TextProviderConfig(kind="anthropic", base_url=f"{base}/v1", model="m")
            )
            provider.complete("s", "u", batch_name="b", batch=BATCH)
        self.assertEqual(RECORDED[0]["path"], "/v1/messages")


class OllamaTests(unittest.TestCase):
    def test_native_chat_shape(self) -> None:
        with StubServer() as base:
            RESPONSES["/api/chat"] = {
                "model": "qwen",
                "message": {"content": '{"items": []}'},
                "prompt_eval_count": 3,
                "eval_count": 4,
            }
            provider = build_text_provider(
                TextProviderConfig(kind="ollama", base_url=base, model="qwen", max_tokens=555)
            )
            completion = provider.complete("s", "u", batch_name="b", batch=BATCH)

        sent = RECORDED[0]
        self.assertEqual(sent["path"], "/api/chat")
        self.assertFalse(sent["body"]["stream"])
        self.assertEqual(sent["body"]["format"], "json")
        self.assertEqual(sent["body"]["options"]["num_predict"], 555)
        self.assertEqual(completion.usage["totalTokens"], 7)

    def test_a_v1_suffix_is_stripped_for_the_native_api(self) -> None:
        with StubServer() as base:
            RESPONSES["/api/chat"] = {"message": {"content": "ok"}}
            provider = build_text_provider(
                TextProviderConfig(kind="ollama", base_url=f"{base}/v1", model="m")
            )
            provider.complete("s", "u", batch_name="b", batch=BATCH)
        self.assertEqual(RECORDED[0]["path"], "/api/chat")


class CliProviderTests(unittest.TestCase):
    """The 'subscription seat as an API' path."""

    def _script(self, directory: Path, body: str) -> Path:
        path = directory / "tool.py"
        path.write_text(body, encoding="utf-8")
        return path

    def test_prompt_reaches_the_command_on_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            script = self._script(
                Path(raw),
                "import sys\n"
                "text = sys.stdin.read()\n"
                "print('SAW-SYSTEM' if 'system marker' in text else 'MISSING')\n",
            )
            provider = build_text_provider(
                TextProviderConfig(kind="cli", command=(sys.executable, str(script)))
            )
            completion = provider.complete("system marker", "user", batch_name="b", batch=BATCH)
        self.assertEqual(completion.text, "SAW-SYSTEM")

    def test_prompt_file_placeholder_is_substituted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            script = self._script(
                Path(raw),
                "import sys\nprint(open(sys.argv[1], encoding='utf-8').read().strip()[:6])\n",
            )
            provider = build_text_provider(
                TextProviderConfig(
                    kind="cli", command=(sys.executable, str(script), "{prompt_file}")
                )
            )
            completion = provider.complete("ABCDEF", "user", batch_name="b", batch=BATCH)
        self.assertEqual(completion.text, "ABCDEF")

    def test_non_ascii_survives_the_subprocess_boundary(self) -> None:
        """On Windows a child pipes with the console code page unless told not to.

        That silently turned Chinese output into replacement characters, which
        only surfaced as a failed quality audit at the very end of a build.
        """
        with tempfile.TemporaryDirectory() as raw:
            script = self._script(Path(raw), "print('这是中文 日本語')\n")
            provider = build_text_provider(
                TextProviderConfig(kind="cli", command=(sys.executable, str(script)))
            )
            completion = provider.complete("s", "u", batch_name="b", batch=BATCH)
        self.assertEqual(completion.text, "这是中文 日本語")
        self.assertNotIn("�", completion.text)

    def test_a_failing_command_reports_its_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            script = self._script(Path(raw), "import sys\nsys.stderr.write('boom')\nsys.exit(3)\n")
            provider = build_text_provider(
                TextProviderConfig(kind="cli", command=(sys.executable, str(script)))
            )
            with self.assertRaises(ProviderError) as caught:
                provider.complete("s", "u", batch_name="b", batch=BATCH)
        self.assertIn("boom", str(caught.exception))

    def test_a_missing_command_fails_preflight_not_the_first_batch(self) -> None:
        provider = build_text_provider(
            TextProviderConfig(kind="cli", command=("definitely-not-installed-xyz",))
        )
        with self.assertRaises(ProviderError) as caught:
            provider.preflight()
        self.assertIn("definitely-not-installed-xyz", str(caught.exception))


class ManualProviderTests(unittest.TestCase):
    def test_first_run_writes_a_prompt_and_waits(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            provider = build_text_provider(TextProviderConfig(kind="manual", handoff_dir=raw))
            with self.assertRaises(PendingHandoff) as caught:
                provider.complete("system", "user", batch_name="batch_001.json", batch=BATCH)
            prompt = Path(raw) / "batch_001.prompt.txt"
            self.assertTrue(prompt.is_file())
            self.assertIn("system", prompt.read_text(encoding="utf-8"))
            self.assertEqual(caught.exception.pending, [prompt])

    def test_second_run_reads_the_reply_a_human_saved(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            provider = build_text_provider(TextProviderConfig(kind="manual", handoff_dir=raw))
            with self.assertRaises(PendingHandoff):
                provider.complete("system", "user", batch_name="batch_001.json", batch=BATCH)
            (Path(raw) / "batch_001.reply.json").write_text(
                '{"items": [{"index": 0, "zhTranslation": "这是测试。", "explanationText": "讲解。"}]}',
                encoding="utf-8",
            )
            completion = provider.complete("system", "user", batch_name="batch_001.json", batch=BATCH)
        self.assertIn("这是测试。", completion.text)


class EchoProviderTests(unittest.TestCase):
    def test_output_is_marked_as_a_stub_and_translates_nothing(self) -> None:
        provider = build_text_provider(TextProviderConfig(kind="echo"))
        completion = provider.complete("s", "u", batch_name="b", batch=BATCH)
        payload = json.loads(completion.text)
        self.assertTrue(completion.stub)
        self.assertEqual(payload["items"][0]["zhTranslation"], "")
        self.assertIn("[stub]", payload["items"][0]["explanationText"])


class SegmentSplittingTests(unittest.TestCase):
    """A VAD-filtered transcription reports timestamps on the original timeline,
    so a segment spanning a removed silence carries that silence in its duration.
    Measured on the real N2 audio: 36 segments over 15s, the longest 51.6s."""

    @staticmethod
    def words(spans: list[tuple[float, float, str]]) -> list[dict]:
        return [{"start": start, "end": end, "word": word} for start, end, word in spans]

    def segment(self, spans: list[tuple[float, float, str]]) -> Segment:
        words = self.words(spans)
        return Segment(
            start=words[0]["start"],
            end=words[-1]["end"],
            text="".join(w["word"] for w in words),
            words=words,
        )

    def test_a_long_segment_is_cut_at_its_widest_pause(self) -> None:
        segment = self.segment([(0.0, 4.0, "A"), (4.0, 8.0, "B"), (20.0, 24.0, "C")])
        pieces, splits = split_long_segments([segment], max_seconds=15)
        self.assertEqual(splits, 1)
        self.assertEqual([(p.start, p.end) for p in pieces], [(0.0, 8.0), (20.0, 24.0)])
        self.assertEqual([p.text for p in pieces], ["AB", "C"])

    def test_splitting_repeats_until_every_piece_fits(self) -> None:
        segment = self.segment(
            [(0.0, 4.0, "A"), (20.0, 24.0, "B"), (40.0, 44.0, "C"), (60.0, 64.0, "D")]
        )
        pieces, _ = split_long_segments([segment], max_seconds=15)
        self.assertEqual(len(pieces), 4)
        self.assertTrue(all(p.end - p.start <= 15 for p in pieces))

    def test_a_cut_that_would_leave_a_fragment_is_not_made(self) -> None:
        """Fixing the long-segment defect must not manufacture the short-segment
        one: the audit rejects anything under 350 ms."""
        segment = self.segment([(0.0, 0.2, "A"), (18.0, 24.0, "B")])
        pieces, splits = split_long_segments([segment], max_seconds=15, min_piece=0.8)
        self.assertEqual(splits, 0)
        self.assertEqual(len(pieces), 1)

    def test_continuous_speech_is_left_alone_rather_than_cut_mid_phrase(self) -> None:
        spans = [(float(i), float(i) + 1.0, "x") for i in range(20)]
        pieces, splits = split_long_segments([self.segment(spans)], max_seconds=15)
        self.assertEqual(splits, 0)
        self.assertEqual(len(pieces), 1)

    def test_segments_without_word_timings_are_untouched(self) -> None:
        segment = Segment(start=0.0, end=40.0, text="no words here")
        pieces, splits = split_long_segments([segment], max_seconds=15)
        self.assertEqual((len(pieces), splits), (1, 0))

    def test_disabled_by_default(self) -> None:
        segment = self.segment([(0.0, 4.0, "A"), (30.0, 34.0, "B")])
        pieces, splits = split_long_segments([segment], max_seconds=0)
        self.assertEqual((len(pieces), splits), (1, 0))


class TranscriptParsingTests(unittest.TestCase):
    def test_srt(self) -> None:
        segments = parse_transcript_text(
            "1\n00:00:00,420 --> 00:00:03,700\nHello there.\n\n"
            "2\n00:01:02,000 --> 00:01:04,500\nSecond line.\n"
        )
        self.assertEqual([round(s.start, 2) for s in segments], [0.42, 62.0])
        self.assertEqual(segments[1].text, "Second line.")

    def test_webvtt_with_a_header_and_cue_ids(self) -> None:
        segments = parse_transcript_text(
            "WEBVTT\n\ncue-1\n00:00:01.000 --> 00:00:02.000\nOne\n\n"
            "cue-2\n00:00:03.000 --> 00:00:04.000\nTwo\n"
        )
        self.assertEqual([s.text for s in segments], ["One", "Two"])

    def test_whisper_verbose_json(self) -> None:
        segments = parse_transcript_text(
            json.dumps({"segments": [{"start": 0.4, "end": 3.7, "text": " padded ", "avg_logprob": -0.2}]})
        )
        self.assertEqual(segments[0].text, "padded")
        self.assertAlmostEqual(segments[0].avg_logprob, -0.2)

    def test_whisper_cpp_millisecond_offsets(self) -> None:
        segments = parse_transcript_text(
            json.dumps({"transcription": [{"offsets": {"from": 1500, "to": 2500}, "text": "x"}]})
        )
        self.assertEqual((segments[0].start, segments[0].end), (1.5, 2.5))

    def test_this_projects_own_raw_segments_round_trip(self) -> None:
        segments = parse_transcript_text(
            json.dumps({"segments": [{"startTime": 1.0, "endTime": 2.0, "sourceText": "はい"}]})
        )
        self.assertEqual(segments[0].text, "はい")

    def test_a_plain_text_transcript_is_refused_with_a_reason(self) -> None:
        with self.assertRaises(AsrError) as caught:
            parse_transcript_text("just some prose with no timings at all", hint="notes.txt")
        message = str(caught.exception)
        self.assertIn("notes.txt", message)
        self.assertIn("SRT", message)


if __name__ == "__main__":
    unittest.main()
