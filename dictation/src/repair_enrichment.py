"""Regenerate only missing or corrupted translations/explanations in a manifest.

Repair is the same enrichment stage as a build, aimed at a subset of sentences,
so it takes the same provider selection: the model that repairs a course need not
be - and often should not be - the one that produced it. Nothing is retranscribed
and no sentence outside the repair set is touched.

    python src/repair_enrichment.py courses/x/manifest.json --dry-run
    python src/repair_enrichment.py courses/x/manifest.json --profile ollama
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any

from bundle_io import load_json, write_json
from bundle_quality import audit_manifest, looks_corrupted
from enrichment import generate_results, merge_results_into_manifest, results_used_stub, write_batches
from language_support import translation_text, upgrade_manifest_language
from provider_config import TEXT_KINDS, ConfigError, load_config_file, resolve_text_provider
from text_providers import build_text_provider, provider_env_summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_json(manifest_path)
    upgrade_manifest_language(manifest)
    targets = find_repair_indexes(manifest, include_missing=args.include_missing)

    print(f"Repair targets: {len(targets)}")
    if targets:
        print("First indexes: " + ", ".join(str(index) for index in sorted(targets)[:30]))
    if args.dry_run:
        return 0
    if not targets:
        print("No enrichment needs repair.")
        return 0

    config, config_path = load_config_file(args.config)
    text_config = resolve_text_provider(
        config=config,
        profile=args.profile,
        overrides={
            "kind": args.kind,
            "model": args.model,
            "baseUrl": args.base_url,
            "apiKeyEnv": args.api_key_env,
            "command": args.command,
            "handoffDir": args.handoff_dir,
            "batchSize": args.batch_size,
            "maxTokens": args.max_tokens,
            "temperature": args.temperature,
            "retries": args.retries,
            "sleep": args.sleep,
            "timeout": args.timeout,
        },
    )
    print(f"Config   : {config_path or '(none found)'}")
    print(f"Provider : {provider_env_summary(text_config)}")

    out_path = (
        Path(args.out).expanduser().resolve()
        if args.out
        else manifest_path.with_name(f"{manifest_path.stem}.repaired.json")
    )
    if out_path.exists() and not args.force:
        raise SystemExit(f"Output already exists: {out_path}. Use --force to overwrite.")

    provider = build_text_provider(text_config)
    provider.preflight()

    work_context: tempfile.TemporaryDirectory[str] | None = None
    if args.work_dir:
        work_dir = Path(args.work_dir).expanduser().resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_context = tempfile.TemporaryDirectory(prefix="dictation-enrichment-repair-")
        work_dir = Path(work_context.name)

    try:
        batches_dir = work_dir / "batches"
        results_dir = batches_dir / "results"
        batches = write_batches(
            manifest,
            batches_dir,
            batch_size=text_config.batch_size,
            force=not args.resume,
            indexes=targets,
        )
        generate_results(
            provider,
            batches,
            results_dir,
            resume=args.resume,
            keep_going=args.keep_going,
            sleep=text_config.sleep,
            retries=text_config.retries,
        )
        merge_stats = merge_results_into_manifest(manifest, results_dir, required_indexes=targets)
        if results_used_stub(results_dir):
            raise SystemExit(
                "Refusing to write a repair produced by a stub provider.\n"
                "  The 'echo' kind writes placeholders; repairing corrupted text with placeholder\n"
                "  text would only hide the corruption. Use a real provider."
            )

        report = audit_manifest(manifest, require_enrichment=True)
        manifest["quality"] = {"status": report["status"], **report["summary"]}
        build_metadata = manifest.setdefault("buildMetadata", {})
        repairs = build_metadata.setdefault("enrichmentRepairs", [])
        repairs.append(
            {
                "repairedSentences": len(targets),
                "provider": text_config.describe(),
                "models": merge_stats["models"],
            }
        )

        write_json(out_path, manifest)
        write_json(out_path.with_name(f"{out_path.stem}.quality-report.json"), report)
        print(f"Repaired manifest: {out_path}")
        print(
            f"Quality after repair: {report['status']} "
            f"(errors={report['summary']['errors']}, warnings={report['summary']['warnings']})"
        )
    finally:
        if work_context is not None:
            work_context.cleanup()
    return 0


def find_repair_indexes(manifest: dict[str, Any], *, include_missing: bool) -> set[int]:
    sentences = manifest.get("sentences")
    if not isinstance(sentences, list):
        raise SystemExit("Manifest has no sentences array.")
    targets: set[int] = set()
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            continue
        translation = translation_text(sentence)
        explanation = str(sentence.get("explanationText") or "").strip()
        if looks_corrupted(translation) or looks_corrupted(explanation):
            targets.add(index)
        elif include_missing and (not translation or not explanation):
            targets.add(index)
    return targets


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair corrupted or missing enrichment without retranscribing audio.",
    )
    parser.add_argument("manifest", help="Input manifest path.")
    parser.add_argument("--out", help="Output manifest. Default: <manifest>.repaired.json")
    parser.add_argument("--work-dir", help="Keep batches and results here for a resumable repair.")
    parser.add_argument("--include-missing", action="store_true", help="Also retry empty fields.")
    parser.add_argument("--dry-run", action="store_true", help="Count targets without calling anything.")
    parser.add_argument("--force", action="store_true", help="Overwrite the output manifest.")
    parser.add_argument("--resume", action="store_true", help="Reuse valid existing results in --work-dir.")
    parser.add_argument("--keep-going", action="store_true", help="Continue after a failed batch.")

    provider = parser.add_argument_group("text provider")
    provider.add_argument("--config", help="Provider config file. Default: config/providers.json.")
    provider.add_argument("--profile", help="Named text profile from the config.")
    provider.add_argument("--kind", choices=TEXT_KINDS)
    provider.add_argument("--model")
    provider.add_argument("--base-url")
    provider.add_argument("--api-key-env", help="NAME of the env var holding the key.")
    provider.add_argument("--command", help='Command for --kind cli, e.g. "claude -p".')
    provider.add_argument("--handoff-dir", help="Prompt/reply folder for --kind manual.")
    provider.add_argument("--batch-size", type=int)
    provider.add_argument("--max-tokens", type=int)
    provider.add_argument("--temperature", type=float)
    provider.add_argument("--retries", type=int)
    provider.add_argument("--sleep", type=float)
    provider.add_argument("--timeout", type=float)
    return parser.parse_args(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigError as error:
        print(f"\n{error}", file=__import__("sys").stderr)
        raise SystemExit(2) from error
