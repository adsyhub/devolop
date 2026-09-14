"""Audio probe, cue validation and HTTP range parsing for EJU listening sections."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .errors import ContractError, MediaError
from .util import utc_now


def probe_audio(audio_path: Path) -> dict[str, Any]:
    path = audio_path.expanduser().resolve()
    if not path.is_file():
        raise MediaError(f"Audio file not found: {path}")

    # Compute sha256
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    sha256 = digest.hexdigest()
    size_bytes = path.stat().st_size

    # Try reading metadata using soundfile
    duration_ms = 0
    samplerate = 0
    channels = 1
    format_name = path.suffix.lstrip(".").upper()
    try:
        import soundfile as sf
        info = sf.info(str(path))
        if info.duration <= 0 or info.samplerate <= 0:
            raise MediaError(f"Invalid audio track properties: duration={info.duration}, samplerate={info.samplerate}")
        duration_ms = int(info.duration * 1000)
        samplerate = info.samplerate
        channels = info.channels
        format_name = info.format
    except ImportError as exc:
        raise MediaError("Audio probe backend (soundfile) is not installed") from exc
    except MediaError:
        raise
    except Exception as exc:
        raise MediaError("Audio decoding failed") from exc

    return {
        "filePath": str(path),
        "fileName": path.name,
        "sha256": sha256,
        "sizeBytes": size_bytes,
        "durationMs": duration_ms,
        "samplerate": samplerate,
        "channels": channels,
        "format": format_name,
        "probedAt": utc_now(),
    }


def validate_audio_cues(
    cues: list[dict[str, Any]],
    total_duration_ms: int,
) -> list[dict[str, Any]]:
    """Validates cues for listening questions against audio track duration."""
    issues: list[dict[str, Any]] = []
    if not isinstance(cues,list) or not cues or len(cues)>3000 or type(total_duration_ms) is not int or total_duration_ms<=0:
        return [{'code':'cue.invalid_input','message':'A nonempty cue list and positive track duration are required'}]
    if not isinstance(cues,list) or not cues or type(total_duration_ms) is not int or total_duration_ms<=0:
        return [{'code':'cue.invalid','message':'A positive duration and nonempty cue list are required'}]
    seen_cues: set[str] = set()
    prev_end = 0

    for idx, cue in enumerate(cues):
        if not isinstance(cue,dict):
            issues.append({"code":"cue.invalid","message":"Cue must be an object"});continue
        if not isinstance(cue,dict) or not isinstance(cue.get('cueId'),str) or not 1 <= len(cue['cueId']) <= 100:
            issues.append({'code':'cue.invalid_id','message':'Each cue requires a stable cueId'});continue
        cue_id = cue['cueId']
        ref = f"audio.cue[{cue_id}]"
        if cue_id in seen_cues:
            issues.append({"code": "cue.duplicate_id", "message": f"Duplicate cueId: {cue_id}", "ref": ref})
        seen_cues.add(cue_id)

        start = cue.get("startMs")
        end = cue.get("endMs")
        if type(start) is not int or start < 0:
            issues.append({"code": "cue.start_invalid", "message": "startMs must be non-negative integer", "ref": ref})
            continue
        if type(end) is not int or end <= start:
            issues.append({"code": "cue.end_invalid", "message": "endMs must be greater than startMs", "ref": ref})
            continue
        if total_duration_ms > 0 and end > total_duration_ms:
            issues.append({"code": "cue.out_of_bounds", "message": f"endMs ({end}) exceeds duration ({total_duration_ms})", "ref": ref})

        if start < prev_end and not cue.get("overlapReason"):
            issues.append({"code":"cue.overlap","message":"Overlapping cues require a reviewed reason","ref":ref})
        prev_end = end

    return issues


_RANGE_HEADER_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def parse_range_header(header_value: str, total_size: int) -> tuple[int, int]:
    """Parse HTTP Range header. Returns (start, end) inclusive."""
    match = _RANGE_HEADER_RE.match(header_value.strip())
    if not match:
        raise MediaError("Invalid Range header syntax")
    raw_start, raw_end = match.groups()

    if not raw_start and not raw_end:
        raise MediaError("Empty Range header")

    if not raw_start:
        # Suffix range: -N means last N bytes
        suffix_len = int(raw_end)
        if suffix_len <= 0:
            raise MediaError("Invalid suffix range length")
        start = max(0, total_size - suffix_len)
        end = total_size - 1
    elif not raw_end:
        # Range: N- means from N to end
        start = int(raw_start)
        end = total_size - 1
    else:
        start = int(raw_start)
        end = int(raw_end)

    if start < 0 or start >= total_size or end < start:
        raise MediaError(f"Range not satisfiable: {header_value} for size {total_size}")
    end = min(end, total_size - 1)
    return start, end
