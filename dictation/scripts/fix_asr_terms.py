"""Apply a reviewed term map to a course work directory's cached transcription.

Whisper mishears a handful of JLPT broadcast terms the same way in every paper
(ちょうかい -> 懲戒 instead of 聴解). Fixing them by hand in 20 manifests would be
unreviewable, so the map lives in scripts/n2_asr_terms.json and every applied
replacement is logged to <work-dir>/asr-corrections.json.

The cached transcription stays resumable: only sentence text changes, never the
audio hash or the transcription config build_course.py validates on --resume.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from language_support import manifest_language_code, set_source_text, source_text


def load_map(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise SystemExit(f"{path}: only schemaVersion 1 is supported.")
    rules = data.get("replacements")
    if not isinstance(rules, list) or not rules:
        raise SystemExit(f"{path}: no replacements defined.")
    for rule in rules:
        if not rule.get("from") or not rule.get("to"):
            raise SystemExit(f"{path}: every replacement needs 'from' and 'to'.")
    return rules


def load_sentence_fixes(path: Path) -> list[dict]:
    """Per-course corrections that only context can settle (地震/自信, names, ...).

    Each entry pins the exact text it expects to replace, so a fix written against
    one transcription can never silently rewrite a different one.
    """
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise SystemExit(f"{path}: only schemaVersion 1 is supported.")
    fixes = data.get("fixes") or []
    for fix in fixes:
        if "sentenceIndex" not in fix or "before" not in fix or "after" not in fix:
            raise SystemExit(f"{path}: every fix needs sentenceIndex, before and after.")
        if not fix.get("why"):
            raise SystemExit(f"{path}: fix at index {fix['sentenceIndex']} has no 'why'.")
    return fixes


def fix_manifest(
    manifest_path: Path,
    rules: list[dict[str, str]],
    sentence_fixes: list[dict] | None = None,
) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    language = manifest_language_code(manifest)
    sentences = manifest.get("sentences")
    if not isinstance(sentences, list):
        raise SystemExit(f"{manifest_path}: no sentences array.")

    edits: list[dict] = []
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            continue
        before = source_text(sentence, language)
        after = before
        applied: list[str] = []
        for rule in rules:
            if rule["from"] in after:
                after = after.replace(rule["from"], rule["to"])
                applied.append(f"{rule['from']}->{rule['to']}")
        if after != before:
            set_source_text(sentence, after, language)
            edits.append(
                {"sentenceIndex": index, "rules": applied, "before": before, "after": after}
            )

    for fix in sentence_fixes or []:
        index = int(fix["sentenceIndex"])
        if index >= len(sentences) or not isinstance(sentences[index], dict):
            raise SystemExit(f"{manifest_path}: sentence fix index {index} is out of range.")
        current = source_text(sentences[index], language)
        if current == fix["after"]:
            continue
        if current != fix["before"]:
            raise SystemExit(
                f"{manifest_path}: sentence fix {index} expected: "
                f"{fix['before']!r} but the transcription says {current!r}"
            )
        set_source_text(sentences[index], fix["after"], language)
        edits.append(
            {
                "sentenceIndex": index,
                "rules": ["sentence-fix"],
                "why": fix["why"],
                "before": fix["before"],
                "after": fix["after"],
            }
        )

    if edits:
        # transcriptText is derived; build_course recomputes it on resume, but keep
        # the cache self-consistent for anyone reading it directly.
        joined = "".join(source_text(s, language) for s in sentences if isinstance(s, dict))
        manifest["transcriptText"] = joined
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return {"manifest": str(manifest_path), "edits": edits}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_dirs", nargs="+", help="Course work directories.")
    parser.add_argument("--terms", default=str(PROJECT_DIR / "scripts" / "n2_asr_terms.json"))
    parser.add_argument(
        "--fixes-dir",
        default=str(PROJECT_DIR / "scripts" / "n2_sentence_fixes"),
        help="Directory of <work-dir-name>.json per-course sentence corrections.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rules = load_map(Path(args.terms))
    total = 0
    for raw in args.work_dirs:
        work_dir = Path(raw)
        manifest_path = work_dir / "manifest.transcribed.json"
        if not manifest_path.exists():
            print(f"SKIP {work_dir}: no manifest.transcribed.json")
            continue
        fixes = load_sentence_fixes(Path(args.fixes_dir) / f"{work_dir.name}.json")
        if args.dry_run:
            original = manifest_path.read_text(encoding="utf-8")
            report = fix_manifest(manifest_path, rules, fixes)
            manifest_path.write_text(original, encoding="utf-8")
        else:
            report = fix_manifest(manifest_path, rules, fixes)
            if report["edits"]:
                (work_dir / "asr-corrections.json").write_text(
                    json.dumps(
                        {"schemaVersion": 1, "terms": str(args.terms), **report},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
        total += len(report["edits"])
        print(f"{work_dir.name}: {len(report['edits'])} sentence(s) corrected")
        for edit in report["edits"]:
            print(f"    [{edit['sentenceIndex']}] {','.join(edit['rules'])}: {edit['after'][:60]}")
    print(f"\nTotal corrected sentences: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
