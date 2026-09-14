r"""Compatibility entry point for the old DeepSeek-only builder.

The pipeline now lives in :mod:`build_course`, where the ASR model and the text
model are both resolved at run time (see :mod:`provider_config`). This module
stays for two reasons, and does nothing else:

1. **Nine modules import their JSON, hashing and ZIP helpers from here.** Those
   helpers moved to :mod:`bundle_io`; they are re-exported below so every
   existing ``from build_deepseek_offline_bundle import load_json`` keeps working.
2. **The documented build command pointed at this file.** Running it still
   builds a course: the DeepSeek-shaped flags are translated onto the generic
   pipeline, which is exactly the ``openai-compat`` provider with DeepSeek's
   base URL.

The one behaviour that could not be preserved is the hard-coded default model.
``deepseek-v4-flash`` used to be a module constant, so a build silently targeted
whatever that name resolved to - and failed at the first batch once it stopped
resolving to anything. ``--deepseek-model`` is now required, and asking for it
up front is the whole point of the change.

New work should call :mod:`build_course` directly::

    python src/build_course.py --audio in.mp3 --profile deepseek
"""

from __future__ import annotations

import argparse
import os
import sys

# Re-exported for the modules that treat this file as the project's utility hub.
# Kept as explicit names rather than a star import so the public surface is
# visible here and an accidental removal breaks loudly.
from bundle_io import (  # noqa: F401
    build_zip,
    canonical_json_sha256,
    confidence_from_logprob,
    files_have_same_content,
    format_timestamp,
    load_json,
    normalize_text,
    parse_jsonish,
    safe_audio_name,
    safe_filename,
    sha256_file,
    verify_zip,
    write_json,
)
from enrichment import (  # noqa: F401
    merge_results_into_manifest,
    system_prompt_for_language,
    validate_output_file,
    validate_result_for_batch,
    write_batches,
)

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
#: Kept only so old callers can still read a batch size default from here.
DEFAULT_BATCH_SIZE = 25

# Historical aliases. They no longer select anything on their own; the values
# below are the shim's *fallbacks*, not the pipeline's defaults.
DEFAULT_DEEPSEEK_BASE_URL = DEEPSEEK_BASE_URL


def main(argv: list[str] | None = None) -> int:
    args, passthrough = parse_known(argv)

    print(
        "NOTE: src/build_deepseek_offline_bundle.py is a compatibility wrapper.\n"
        "      The pipeline is src/build_course.py, where any ASR and any text model\n"
        "      can be selected. This run is being translated onto it.\n",
        file=sys.stderr,
    )

    if not args.no_deepseek and not args.deepseek_model:
        raise SystemExit(
            "--deepseek-model is now required.\n"
            "  This wrapper used to default to a hard-coded model name, which meant a build\n"
            "  targeted whatever that name happened to resolve to - and broke at the first\n"
            "  batch when it resolved to nothing.\n"
            "  Pass --deepseek-model <name>, or move to:\n"
            "    python src/build_course.py --audio ... --profile deepseek"
        )

    forwarded: list[str] = ["--audio", args.audio]
    if args.title:
        forwarded += ["--title", args.title]
    if args.out:
        forwarded += ["--out", args.out]
    if args.work_dir:
        forwarded += ["--work-dir", args.work_dir]
    if args.force:
        forwarded.append("--force")
    if args.resume:
        forwarded.append("--resume")
    if args.strict_quality:
        forwarded.append("--strict-quality")
    if args.keep_going:
        forwarded.append("--keep-going")

    # ASR: the old flags only ever drove local faster-whisper.
    forwarded += ["--asr-kind", "faster-whisper", "--asr-model", args.whisper_model]
    forwarded += ["--asr-device", args.device, "--asr-compute-type", args.compute_type]
    forwarded += ["--language", args.language, "--beam-size", str(args.beam_size)]
    forwarded += ["--min-duration", str(args.min_duration)]
    if args.no_vad:
        forwarded.append("--no-vad")
    if args.word_timestamps:
        forwarded.append("--word-timestamps")

    if args.no_deepseek:
        forwarded.append("--no-enrich")
    else:
        forwarded += [
            "--kind",
            "openai-compat",
            "--base-url",
            args.deepseek_base_url,
            "--model",
            args.deepseek_model,
            "--batch-size",
            str(args.batch_size),
            "--max-tokens",
            str(args.max_tokens),
            "--temperature",
            str(args.temperature),
            "--retries",
            str(args.retries),
            "--sleep",
            str(args.sleep),
            "--timeout",
            str(args.api_timeout),
        ]
        if args.thinking != "omit":
            forwarded += ["--extra-body", f'{{"thinking": {{"type": "{args.thinking}"}}}}']
        forwarded += ["--api-key-env", resolve_api_key_env(args.api_key)]

    from build_course import main as build_main

    return build_main(forwarded + passthrough)


def resolve_api_key_env(explicit_key: str | None) -> str:
    """Return the NAME of the variable the pipeline should read the key from.

    A key passed on the command line is moved into this process's environment
    rather than forwarded as an argument, so it stays out of the child's argv the
    same way the launcher keeps its session token out of command lines.
    """
    if explicit_key:
        os.environ["DICTATION_WRAPPER_API_KEY"] = explicit_key
        return "DICTATION_WRAPPER_API_KEY"
    if os.environ.get("DEEPSEEK_API_KEY"):
        return "DEEPSEEK_API_KEY"
    raise SystemExit(
        "Missing DeepSeek API key. Set it before building:\n"
        '  $env:DEEPSEEK_API_KEY="your_api_key"'
    )


def parse_known(argv: list[str] | None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Deprecated wrapper around src/build_course.py. Use that directly for new work.",
    )
    parser.add_argument("--audio", required=True)
    parser.add_argument("--api-key", help="Prefer the DEEPSEEK_API_KEY environment variable.")
    parser.add_argument("--out")
    parser.add_argument("--title")
    parser.add_argument("--work-dir")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--resume", action="store_true")

    parser.add_argument("--whisper-model", default="large-v3")
    parser.add_argument("--device", default="auto", choices=["cuda", "cpu", "auto"])
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="ja")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--no-vad", action="store_true")
    parser.add_argument("--word-timestamps", action="store_true")
    parser.add_argument("--min-duration", type=float, default=0.2)

    parser.add_argument("--no-deepseek", action="store_true")
    parser.add_argument("--deepseek-base-url", default=DEEPSEEK_BASE_URL)
    parser.add_argument("--deepseek-model", help="Required: this wrapper no longer picks a model for you.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--api-timeout", type=float, default=180.0)
    parser.add_argument("--strict-quality", action="store_true")
    parser.add_argument("--thinking", choices=["enabled", "disabled", "omit"], default="omit")
    return parser.parse_known_args(argv)


if __name__ == "__main__":
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    raise SystemExit(main())
