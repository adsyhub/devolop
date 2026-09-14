"""Quality gate for hand/agent-written N2 enrichment, run before building a course.

Three things go wrong in this content and none of them are caught by bundle_quality:

1. An index in the batch has no reply, or a reply invents an index. The merge step
   would still succeed and the course would ship with silently missing sentences.
2. A placeholder or an empty string slips through. That puts text in front of a
   learner that nobody wrote.
3. A Japanese word quoted inside 「」 gets written with a Simplified character
   (問い合わせる -> 问い合わせる). The sentence still reads fine to a Chinese eye,
   which is exactly why it survives review -- but the learner is being shown a
   kanji that does not exist in Japanese. Chinese glosses in （） inside the quote
   are legitimate Simplified and are excluded.

Usage:
    python scripts/check_enrichment.py n2-jingting-work/2018-12-N2 [...]
    python scripts/check_enrichment.py --courses courses/2018-12-N2 [...]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

# Simplified-only forms: characters whose Japanese counterpart is a different glyph.
# Deliberately excludes 医/点/会/来/発 etc., which are identical in both scripts.
SIMPLIFIED_ONLY = {
    "开": "開", "闻": "聞", "见": "見", "问": "問", "读": "読", "书": "書",
    "话": "話", "买": "買", "饲": "飼", "绍": "紹", "时": "時", "应": "応",
    "变": "変", "觉": "覚", "验": "験", "证": "証", "说": "説", "实": "実",
    "对": "対", "气": "気", "难": "難", "请": "請", "运": "運", "动": "動",
    "长": "長", "门": "門", "车": "車", "东": "東", "样": "様", "员": "員",
    "关": "関", "际": "際", "绿": "緑", "练": "練", "习": "習", "议": "議",
    "认": "認", "识": "識", "济": "済", "业": "業", "产": "産", "术": "術",
    "药": "薬", "带": "帯", "层": "層", "态": "態", "职": "職", "团": "団",
}

QUOTE = re.compile(r"「([^「」]*)」")
PAREN = re.compile(r"[（(][^）)]*[）)]")
KANA = re.compile(r"[぀-ゟ゠-ヿ]")
PLACEHOLDER = re.compile(r"TODO|待补|待補|placeholder|PLACEHOLDER|占位|（略）|\(略\)")


def bad_kanji(text: str) -> list[tuple[str, str]]:
    """Simplified characters found inside a Japanese 「」 quote."""
    out = []
    for match in QUOTE.finditer(text or ""):
        span = PAREN.sub("", match.group(1))  # drop Chinese glosses
        if not KANA.search(span):
            continue  # no kana: this quote is Chinese, not Japanese
        for char in span:
            if char in SIMPLIFIED_ONLY:
                out.append((match.group(1), char))
    return out


def check_workdir(work_dir: str) -> list[str]:
    slug = os.path.basename(work_dir.rstrip("/\\"))
    problems: list[str] = []
    batches = sorted(glob.glob(os.path.join(work_dir, "deepseek_batches", "batch_*.json")))
    if not batches:
        return [f"{slug}: no batches in {work_dir}"]

    for batch_path in batches:
        name = os.path.basename(batch_path)[: -len(".json")]
        reply_path = os.path.join(work_dir, "handoff", f"{name}.reply.json")
        if not os.path.exists(reply_path):
            problems.append(f"{slug}/{name}: no reply file")
            continue
        batch = json.load(open(batch_path, encoding="utf-8"))
        try:
            reply = json.load(open(reply_path, encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            problems.append(f"{slug}/{name}: reply is not valid JSON ({exc})")
            continue

        want = [int(i["index"]) for i in batch["items"]]
        items = reply.get("items")
        if not isinstance(items, list):
            problems.append(f"{slug}/{name}: reply has no items array")
            continue
        got = [int(i.get("index", -1)) for i in items]
        if set(got) != set(want):
            missing = sorted(set(want) - set(got))
            extra = sorted(set(got) - set(want))
            problems.append(
                f"{slug}/{name}: index mismatch (missing={missing[:8]} extra={extra[:8]})"
            )
        if len(got) != len(set(got)):
            problems.append(f"{slug}/{name}: duplicate indexes in reply")

        for item in items:
            idx = item.get("index")
            for field in ("zhTranslation", "explanationText"):
                value = (item.get(field) or "").strip()
                if not value:
                    problems.append(f"{slug}/{name} idx {idx}: empty {field}")
                elif PLACEHOLDER.search(value):
                    problems.append(f"{slug}/{name} idx {idx}: placeholder in {field}")
            for quote, char in bad_kanji(item.get("explanationText") or ""):
                problems.append(
                    f"{slug}/{name} idx {idx}: 「{quote}」 uses Simplified "
                    f"{char} (should be {SIMPLIFIED_ONLY[char]})"
                )
    return problems


def check_course(course_dir: str) -> list[str]:
    slug = os.path.basename(course_dir.rstrip("/\\"))
    manifest = json.load(open(os.path.join(course_dir, "manifest.json"), encoding="utf-8"))
    problems: list[str] = []
    for index, sentence in enumerate(manifest.get("sentences") or []):
        for quote, char in bad_kanji(sentence.get("explanationText") or ""):
            problems.append(
                f"{slug} idx {index}: 「{quote}」 uses Simplified "
                f"{char} (should be {SIMPLIFIED_ONLY[char]})"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument(
        "--courses",
        action="store_true",
        help="Treat paths as installed course folders instead of work directories.",
    )
    args = parser.parse_args()

    total = 0
    for path in args.paths:
        problems = check_course(path) if args.courses else check_workdir(path)
        total += len(problems)
        label = os.path.basename(path.rstrip("/\\"))
        if problems:
            print(f"{label}: {len(problems)} problem(s)")
            for line in problems[:40]:
                print(f"    {line}")
            if len(problems) > 40:
                print(f"    ... and {len(problems) - 40} more")
        else:
            print(f"{label}: OK")
    print()
    print(f"total problems: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
