"""FND-001b: compare the shipped course against the recovery candidate.

The shipped course fails its audit with 90 errors. A manifest for the *same
audio* that audits 0/0 exists inside `dist/2010-12-N2-commercial-candidate.zip`,
so it is the best known recovery candidate — but it is only a candidate:

* its human listening review is still `pending`, so it cannot be called canonical;
* it has 517 segments where the shipped course has 629, and that difference has
  never been explained;
* the two share **no** sentence ids at all, and even the courseId differs, so
  every piece of saved progress, every note and every vocabulary entry would be
  orphaned by a naive swap.

This tool therefore produces evidence, never a switch. It writes a segment-level
diff, two revision-bound alias tables, and a queue of the cases a human has to
decide. Promoting the candidate is a separate, explicit act that should not
happen before the listening review clears.

    python src/content_candidate.py --out assets/content_candidates/2010-12-N2

Matching runs in two passes, deliberately conservative:

1. **Exact** — identical rounded start/end and identical normalized text. These
   are safe to migrate automatically.
2. **Fuzzy** — overlapping in time and similar in text. A segment with exactly
   one plausible partner is offered as a suggestion; anything with several
   goes to the human queue rather than picking a winner by score.

Everything else is reported as unmatched. The plan is explicit that ambiguous
segments must not be guessed.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CURRENT = PROJECT_DIR / "courses" / "2010-12-N2" / "manifest.json"
DEFAULT_CANDIDATE = PROJECT_DIR / "dist" / "2010-12-N2-commercial-candidate.zip"

# A segment pair must clear both bars to count as a fuzzy match. Chosen to be
# strict enough that a match implies "the same utterance", not merely "nearby".
MIN_TIME_IOU = 0.5
MIN_TEXT_SIMILARITY = 0.75
# Gaps in audio coverage longer than this are reported as holes.
HOLE_SECONDS = 1.0

PUNCTUATION = re.compile(r"[\s、。，．,.!！?？「」『』（）()･・…‥\-—~〜:：;；]+")


def normalize_text(value: str) -> str:
    """NFKC-fold and strip punctuation so cosmetic differences don't block a match."""
    folded = unicodedata.normalize("NFKC", str(value or ""))
    return PUNCTUATION.sub("", folded).casefold()


def to_ms(value: Any) -> int | None:
    try:
        return round(float(value) * 1000)
    except (TypeError, ValueError):
        return None


def segment_view(sentence: dict[str, Any], index: int) -> dict[str, Any]:
    text = str(sentence.get("sourceText") or sentence.get("jaText") or "").strip()
    return {
        "index": index,
        "id": str(sentence.get("id") or ""),
        "startMs": to_ms(sentence.get("startTime")),
        "endMs": to_ms(sentence.get("endTime")),
        "text": text,
        "normalized": normalize_text(text),
        "translation": str(sentence.get("translationText") or sentence.get("zhTranslation") or "").strip(),
        "explanation": str(sentence.get("explanationText") or "").strip(),
        "practiceEligible": bool(sentence.get("practiceEligible")),
        "confidence": sentence.get("confidence"),
        "asrQuality": sentence.get("asrQuality"),
    }


def time_iou(left: dict[str, Any], right: dict[str, Any]) -> float:
    if None in (left["startMs"], left["endMs"], right["startMs"], right["endMs"]):
        return 0.0
    overlap = min(left["endMs"], right["endMs"]) - max(left["startMs"], right["startMs"])
    if overlap <= 0:
        return 0.0
    union = max(left["endMs"], right["endMs"]) - min(left["startMs"], right["startMs"])
    return overlap / union if union > 0 else 0.0


def text_similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return difflib.SequenceMatcher(None, left, right).ratio()


def build_segment_aliases(current: list[dict], candidate: list[dict]) -> dict[str, Any]:
    """Map shipped segments onto candidate segments, refusing to guess."""
    exact: list[dict[str, Any]] = []
    suggested: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    by_key: dict[tuple, list[dict]] = {}
    for segment in candidate:
        by_key.setdefault((segment["startMs"], segment["endMs"], segment["normalized"]), []).append(segment)

    claimed: set[int] = set()

    # Pass 1: exact identity on time and normalized text.
    for segment in current:
        key = (segment["startMs"], segment["endMs"], segment["normalized"])
        matches = [m for m in by_key.get(key, []) if m["index"] not in claimed]
        if len(matches) == 1:
            claimed.add(matches[0]["index"])
            exact.append({
                "fromId": segment["id"],
                "toId": matches[0]["id"],
                "method": "exact",
                "startMs": segment["startMs"],
                "endMs": segment["endMs"],
            })

    matched_from = {entry["fromId"] for entry in exact}

    # Pass 2: overlap in time and similarity in text.
    for segment in current:
        if segment["id"] in matched_from:
            continue
        scored = []
        for other in candidate:
            if other["index"] in claimed:
                continue
            iou = time_iou(segment, other)
            if iou < MIN_TIME_IOU:
                continue
            similarity = text_similarity(segment["normalized"], other["normalized"])
            if similarity < MIN_TEXT_SIMILARITY:
                continue
            scored.append((iou, similarity, other))

        if not scored:
            unmatched.append({
                "fromId": segment["id"],
                "startMs": segment["startMs"],
                "endMs": segment["endMs"],
                "text": segment["text"][:80],
                "practiceEligible": segment["practiceEligible"],
            })
        elif len(scored) == 1:
            iou, similarity, other = scored[0]
            claimed.add(other["index"])
            suggested.append({
                "fromId": segment["id"],
                "toId": other["id"],
                "method": "time-and-text",
                "timeIou": round(iou, 4),
                "textSimilarity": round(similarity, 4),
                "requiresHumanConfirmation": True,
            })
        else:
            ambiguous.append({
                "fromId": segment["id"],
                "startMs": segment["startMs"],
                "endMs": segment["endMs"],
                "text": segment["text"][:80],
                "practiceEligible": segment["practiceEligible"],
                "candidates": [
                    {"toId": other["id"], "timeIou": round(iou, 4), "textSimilarity": round(similarity, 4)}
                    for iou, similarity, other in sorted(scored, key=lambda item: -item[0])[:5]
                ],
            })

    orphaned = [
        {"toId": segment["id"], "startMs": segment["startMs"], "endMs": segment["endMs"],
         "text": segment["text"][:80]}
        for segment in candidate
        if segment["index"] not in claimed
    ]

    return {
        "exact": exact,
        "suggested": suggested,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "candidateOnly": orphaned,
    }


def coverage(segments: list[dict]) -> dict[str, Any]:
    spans = sorted(
        (s["startMs"], s["endMs"]) for s in segments if s["startMs"] is not None and s["endMs"] is not None
    )
    if not spans:
        return {"coveredMs": 0, "spanMs": 0, "holes": []}
    merged: list[list[int]] = [list(spans[0])]
    for start, end in spans[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    covered = sum(end - start for start, end in merged)
    holes = [
        {"fromMs": merged[i][1], "toMs": merged[i + 1][0], "gapMs": merged[i + 1][0] - merged[i][1]}
        for i in range(len(merged) - 1)
        if merged[i + 1][0] - merged[i][1] > HOLE_SECONDS * 1000
    ]
    return {
        "coveredMs": covered,
        "spanMs": merged[-1][1] - merged[0][0],
        "firstMs": merged[0][0],
        "lastMs": merged[-1][1],
        "holes": holes,
    }


def field_coverage(segments: list[dict]) -> dict[str, Any]:
    """Separate 'absent' from 'present but poor'.

    The plan insists on this split: a quality report that treats a missing
    confidence score as a passing one is worse than no report, because it
    launders unknown provenance into apparent quality.
    """
    total = len(segments)
    with_confidence = [s for s in segments if isinstance(s["confidence"], (int, float))]
    low_confidence = [s for s in with_confidence if float(s["confidence"]) < 0.6]
    return {
        "segments": total,
        "confidencePresent": len(with_confidence),
        "confidenceMissing": total - len(with_confidence),
        "confidenceLow": len(low_confidence),
        "asrQualityPresent": sum(1 for s in segments if s["asrQuality"] is not None),
        "asrQualityMissing": sum(1 for s in segments if s["asrQuality"] is None),
        "note": "Missing is unknown provenance, not verified quality. Do not report unknown as pass.",
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_candidate(zip_path: Path) -> tuple[dict[str, Any], str]:
    """Read *only* the manifest and audio hash out of the published ZIP.

    The ZIP also contains app.js/app.css/sw.js from the build that produced it.
    Those have since drifted from the current player and restoring them would
    silently roll back the fixes in this repo, so they are never extracted.
    """
    with zipfile.ZipFile(zip_path) as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8-sig"))
        audio_hash = sha256_bytes(archive.read("audio.mp3"))
    return manifest, audio_hash


def build_report(current_path: Path, candidate_path: Path) -> dict[str, Any]:
    current_manifest = json.loads(current_path.read_text(encoding="utf-8-sig"))
    candidate_manifest, candidate_audio_hash = load_candidate(candidate_path)

    current_audio = current_path.parent / str(current_manifest.get("audio") or "audio.mp3")
    current_audio_hash = sha256_bytes(current_audio.read_bytes()) if current_audio.is_file() else None

    current_segments = [segment_view(s, i) for i, s in enumerate(current_manifest.get("sentences", []))]
    candidate_segments = [segment_view(s, i) for i, s in enumerate(candidate_manifest.get("sentences", []))]

    aliases = build_segment_aliases(current_segments, candidate_segments)
    current_ids = {s["id"] for s in current_segments}
    candidate_ids = {s["id"] for s in candidate_segments}
    current_coverage = coverage(current_segments)
    candidate_coverage = coverage(candidate_segments)

    matched_practice = sum(
        1
        for entry in aliases["exact"] + aliases["suggested"]
        if next((s for s in current_segments if s["id"] == entry["fromId"]), {}).get("practiceEligible")
    )

    return {
        "schemaVersion": "content-candidate-v1",
        "audio": {
            "currentSha256": current_audio_hash,
            "candidateSha256": candidate_audio_hash,
            "sameAudio": current_audio_hash == candidate_audio_hash,
            "note": "A candidate for different audio is not a recovery candidate at all.",
        },
        "course": {
            "currentCourseId": current_manifest.get("courseId"),
            "candidateCourseId": candidate_manifest.get("courseId"),
            "currentContentRevision": current_manifest.get("contentRevision"),
            "candidateContentRevision": candidate_manifest.get("contentRevision"),
            "sentenceIdIntersection": len(current_ids & candidate_ids),
        },
        "counts": {
            "currentSegments": len(current_segments),
            "candidateSegments": len(candidate_segments),
            "currentPracticeEligible": sum(1 for s in current_segments if s["practiceEligible"]),
            "candidatePracticeEligible": sum(1 for s in candidate_segments if s["practiceEligible"]),
        },
        "mapping": {
            "exact": len(aliases["exact"]),
            "suggested": len(aliases["suggested"]),
            "ambiguous": len(aliases["ambiguous"]),
            "unmatched": len(aliases["unmatched"]),
            "candidateOnly": len(aliases["candidateOnly"]),
            "practiceSegmentsMapped": matched_practice,
        },
        "coverage": {
            "current": current_coverage,
            "candidate": candidate_coverage,
            # The headline reason not to promote on the strength of "0 errors"
            # alone: a shorter transcript audits more cleanly precisely because
            # there is less of it to be wrong about. Losing audio coverage is a
            # content regression even when every remaining segment is perfect.
            "delta": {
                "coveredMsChange": candidate_coverage["coveredMs"] - current_coverage["coveredMs"],
                "holesChange": len(candidate_coverage["holes"]) - len(current_coverage["holes"]),
                "note": "Negative coveredMsChange means the candidate transcribes less of the audio "
                        "than the shipped course. Explain the difference before promoting it.",
            },
        },
        "fieldCoverage": {
            "current": field_coverage(current_segments),
            "candidate": field_coverage(candidate_segments),
        },
        "reviewState": {
            "current": current_manifest.get("review"),
            "candidate": candidate_manifest.get("review"),
            "note": "humanListening=pending means technical candidate only. Not canonical, not releasable.",
        },
        "patchChain": (candidate_manifest.get("buildMetadata") or {}).get("contentPatches"),
    }, aliases, current_manifest, candidate_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FND-001b content candidate diff and alias generation.")
    parser.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--out", type=Path, default=PROJECT_DIR / "assets" / "content_candidates" / "2010-12-N2")
    args = parser.parse_args(argv)

    report, aliases, current_manifest, candidate_manifest = build_report(args.current, args.candidate)

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    # Alias tables are bound to the exact revisions they were computed from. An
    # alias table applied to a different revision is silent data corruption.
    alias_document = {
        "schemaVersion": "course-aliases-v1",
        "courseAliases": [
            {
                "fromCourseId": current_manifest.get("courseId"),
                "toCourseId": candidate_manifest.get("courseId"),
                "fromContentRevision": current_manifest.get("contentRevision"),
                "toContentRevision": candidate_manifest.get("contentRevision"),
                "humanConfirmed": False,
            }
        ],
        "segmentAliases": aliases["exact"] + aliases["suggested"],
        "unresolved": {
            "ambiguous": aliases["ambiguous"],
            "unmatched": aliases["unmatched"],
            "candidateOnly": aliases["candidateOnly"],
        },
    }

    (out_dir / "candidate-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "aliases.json").write_text(
        json.dumps(alias_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts, mapping = report["counts"], report["mapping"]
    print(f"audio identical      : {report['audio']['sameAudio']}")
    print(f"segments             : {counts['currentSegments']} current -> {counts['candidateSegments']} candidate")
    print(f"practice eligible    : {counts['currentPracticeEligible']} -> {counts['candidatePracticeEligible']}")
    print(f"sentence id overlap  : {report['course']['sentenceIdIntersection']}")
    print(f"exact matches        : {mapping['exact']}")
    print(f"suggested (needs OK) : {mapping['suggested']}")
    print(f"ambiguous            : {mapping['ambiguous']}")
    print(f"unmatched            : {mapping['unmatched']}")
    print(f"candidate-only       : {mapping['candidateOnly']}")
    print(f"candidate confidence : {report['fieldCoverage']['candidate']['confidencePresent']} present, "
          f"{report['fieldCoverage']['candidate']['confidenceMissing']} missing")
    print(f"human listening      : current={(report['reviewState']['current'] or {}).get('humanListening')}, "
          f"candidate={(report['reviewState']['candidate'] or {}).get('humanListening')}")
    delta = report["coverage"]["delta"]
    if delta["coveredMsChange"] < 0:
        print(
            f"\nWARNING: the candidate covers {abs(delta['coveredMsChange']) / 1000:.0f}s LESS audio "
            f"({delta['holesChange']:+d} holes). Part of its clean audit is simply less content."
        )
    print(f"\nwritten to {out_dir}")
    print("The default course was NOT changed. Promotion requires the listening review to clear.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
