#!/usr/bin/env python3
"""Check the four local model services used by the content pipelines."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    name: str
    role: str
    base_url: str
    expected_model: str


SERVICES = (
    Service("qwen27", "听写翻译/讲解初稿", "http://127.0.0.1:8100/v1", "Qwen/Qwen3.8-27B-FP8"),
    Service("glm46v", "扫描页视觉复核", "http://127.0.0.1:8101/v1", "zai-org/GLM-4.6V-Flash"),
    Service("glm-ocr", "PDF 首轮 OCR", "http://127.0.0.1:8102/v1", "zai-org/GLM-OCR"),
    Service("flash-next", "终稿/疑难裁决", "http://127.0.0.1:8103/v1", "Qwen/Qwen3.8-Flash-Next"),
)


def check(service: Service, timeout: float) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(f"{service.base_url}/models", timeout=timeout) as response:
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return False, str(exc)
    rows = payload.get("data") if isinstance(payload, dict) else None
    ids = [str(row.get("id")) for row in rows or [] if isinstance(row, dict) and row.get("id")]
    if service.expected_model not in ids:
        return False, f"endpoint returned {ids or ['no model ids']}"
    return True, service.expected_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args(argv)

    failed = 0
    for service in SERVICES:
        ok, detail = check(service, args.timeout)
        state = "READY" if ok else "DOWN"
        print(f"{state:<5} {service.name:<11} {service.base_url:<30} {service.role}")
        if not ok:
            failed += 1
            print(f"      {detail}")
    if failed:
        print(f"\n{failed} service(s) unavailable. Start them before a model-backed build.")
        return 1
    print("\nAll local model services are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
