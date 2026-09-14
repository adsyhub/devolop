"""Build a reviewable exam or lexicon draft from an uploaded PDF.

This is the PDF counterpart to ``build_course.py`` and
``build_video_course.py``.  It intentionally stops at the human-review gate:

* OCR and suspicious-page retries are automatic and use only named profiles
  from the trusted provider config;
* an exam answer key is never guessed;
* a textbook table-of-contents count is never inferred from the same OCR it is
  supposed to check.

The studio reads ``build-result.json`` to explain exactly what was produced and
what still needs review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bundle_io import write_json
from provider_config import ConfigError, load_config_file

PROJECT_DIR = Path(__file__).resolve().parent.parent
PDF_OCR_SCRIPT = Path(__file__).resolve().parent / "pdf_ocr" / "__main__.py"
EXAM_DRAFT_SCRIPT = Path(__file__).resolve().parent / "exam_ocr_to_pages.py"
LEXICON_SCRIPT = Path(__file__).resolve().parent / "lexicon_import.py"

DOCUMENT_KINDS = ("auto", "exam", "grammar", "word", "document")
LEVELS = ("auto", "N1", "N2", "N3", "N4", "N5")
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "0.0.0.0", "host.docker.internal"})


@dataclass(frozen=True)
class VisionProfile:
    name: str
    base_url: str
    model: str
    api_key_env: str
    max_tokens: int
    timeout: int
    prompt: str


_active_process: subprocess.Popen[str] | None = None


def _handle_stop(_signum: int, _frame: Any) -> None:
    """Do not leave an OCR child running after the studio cancels its parent."""
    global _active_process
    if _active_process is not None and _active_process.poll() is None:
        _active_process.terminate()
    raise SystemExit(130)


def _run(argv: list[str], *, required: bool = True) -> int:
    global _active_process
    print("\n$ " + " ".join(_display_arg(item) for item in argv), flush=True)
    _active_process = subprocess.Popen(
        argv,
        cwd=str(PROJECT_DIR),
        text=True,
    )
    try:
        code = _active_process.wait()
    finally:
        _active_process = None
    if required and code:
        raise RuntimeError(f"Pipeline stage exited with code {code}: {Path(argv[1]).name}")
    return code


def _display_arg(value: str) -> str:
    """Readable logs without pretending this string is fed to a shell."""
    return json.dumps(value, ensure_ascii=False) if any(ch.isspace() for ch in value) else value


def _profiles(config: dict[str, Any]) -> dict[str, Any]:
    value = config.get("visionProfiles") or {}
    if not isinstance(value, dict):
        raise ConfigError("Provider config field 'visionProfiles' must be an object.")
    return value


def resolve_vision_profile(config: dict[str, Any], name: str) -> VisionProfile:
    raw = _profiles(config).get(name)
    if not isinstance(raw, dict):
        raise ConfigError(f"Unknown vision profile {name!r}.")
    kind = str(raw.get("kind") or "openai-vlm")
    if kind != "openai-vlm":
        raise ConfigError(f"Vision profile {name!r} has unsupported kind {kind!r}.")
    base_url = str(raw.get("baseUrl") or "").rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ConfigError(f"Vision profile {name!r} needs an http(s) baseUrl.")
    model = str(raw.get("model") or "").strip()
    if not model:
        raise ConfigError(f"Vision profile {name!r} needs a model.")
    api_key_env = str(raw.get("apiKeyEnv") or "").strip()
    return VisionProfile(
        name=name,
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
        max_tokens=max(256, int(raw.get("maxTokens") or 4096)),
        timeout=max(10, int(raw.get("timeout") or 600)),
        prompt=str(raw.get("prompt") or "doc"),
    )


def profile_readiness(profile: VisionProfile) -> tuple[bool, str]:
    """Cheap local preflight; cloud profiles are checked by their real request."""
    if profile.api_key_env and not os.environ.get(profile.api_key_env, "").strip():
        return False, f"环境变量 {profile.api_key_env} 未设置"
    host = (urlparse(profile.base_url).hostname or "").lower()
    if host not in LOCAL_HOSTS:
        return True, "远程 profile 已显式选择"
    request = urllib.request.Request(f"{profile.base_url}/models", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            if response.status >= 400:
                return False, f"模型服务返回 HTTP {response.status}"
    except (OSError, urllib.error.URLError) as exc:
        return False, f"本地端点不可用：{exc}"
    return True, "本地端点可用"


def _ocr_argv(
    pdf: Path,
    ocr_dir: Path,
    profile: VisionProfile,
    *,
    retry_flagged: bool = False,
    mark_ruby: bool = False,
) -> list[str]:
    argv = [
        sys.executable,
        str(PDF_OCR_SCRIPT),
        "run",
        str(pdf),
        "-o",
        str(ocr_dir),
        "--backend",
        "openai-vlm",
        "--server-base-url",
        profile.base_url,
        "--model",
        profile.model,
        "--max-new-tokens",
        str(profile.max_tokens),
        "--server-timeout",
        str(profile.timeout),
        "--prompt",
        profile.prompt,
        "--force",
    ]
    if profile.api_key_env:
        argv += ["--server-api-key-env", profile.api_key_env]
    if retry_flagged:
        argv.append("--retry-flagged")
    if mark_ruby:
        argv.append("--mark-ruby-lines")
    return argv


def _boxes_argv(pdf: Path, ocr_dir: Path, profile: VisionProfile) -> list[str]:
    argv = [
        sys.executable,
        str(PDF_OCR_SCRIPT),
        "boxes",
        str(pdf),
        "-o",
        str(ocr_dir),
        "--backend",
        "openai-vlm",
        "--server-base-url",
        profile.base_url,
        "--model",
        profile.model,
        "--max-new-tokens",
        str(min(profile.max_tokens, 1200)),
        "--server-timeout",
        str(profile.timeout),
    ]
    if profile.api_key_env:
        argv += ["--server-api-key-env", profile.api_key_env]
    return argv


def _quality_report(ocr_dir: Path) -> dict[str, Any]:
    path = ocr_dir / "quality-report.json"
    if not path.is_file():
        raise RuntimeError("OCR did not produce quality-report.json.")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("OCR quality report is malformed.")
    return value


def _document(ocr_dir: Path) -> dict[str, Any]:
    path = ocr_dir / "document.json"
    if not path.is_file():
        raise RuntimeError("OCR did not produce document.json.")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("OCR document is malformed.")
    return value


def classify_document(document: dict[str, Any]) -> dict[str, Any]:
    text = "\n".join(
        str(page.get("markdown") or "")
        for page in document.get("pages") or []
        if isinstance(page, dict)
    )[:500_000]
    normalized = unicodedata.normalize("NFKC", text)
    scores = {
        "exam": (
            5 * len(re.findall(r"日本語能力試験|JLPT", normalized, re.I))
            + 2 * len(re.findall(r"(?:^|\n)\s*#*\s*問題\s*\d+", normalized))
            + 3 * len(re.findall(r"聴解|読解|言語知識", normalized))
            + len(re.findall(r"正解|解答", normalized))
        ),
        "grammar": (
            len(re.findall(r"第\s*\d+\s*週", normalized))
            + len(re.findall(r"\d+\s*日目", normalized))
            + 5 * len(re.findall(r"接続|文型|活用", normalized))
            + 4 * len(re.findall(r"文法", normalized))
        ),
        "word": (
            5 * len(re.findall(r"語彙|単語|ことば|慣用句", normalized))
            + len(re.findall(r"第\s*\d+\s*週", normalized))
            + len(re.findall(r"\d+\s*日目", normalized))
        ),
    }
    winner = max(scores, key=scores.get)
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - ordered[1]
    if scores[winner] < 5 or margin < 2:
        winner = "document"
    confidence = "high" if ordered[0] >= 15 and margin >= 5 else "medium" if winner != "document" else "low"
    level_match = re.search(r"(?<![A-Za-z0-9])N\s*([1-5])(?!\d)", normalized, re.I)
    return {
        "kind": winner,
        "confidence": confidence,
        "scores": scores,
        "level": f"N{level_match.group(1)}" if level_match else "",
    }


def _slug(value: str, digest: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    folded = re.sub(r"[^a-zA-Z0-9]+", "-", folded).strip("-").lower()
    if not folded:
        folded = f"pdf-{digest[:10]}"
    if not folded[0].isalpha():
        folded = f"pdf-{folded}"
    return folded[:64].rstrip("-")


def _page_stats(pages_dir: Path) -> dict[str, int]:
    page_count = question_count = entry_count = issue_pages = errors = warnings = 0
    for path in sorted(pages_dir.glob("p*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        page_count += 1
        blocks = value.get("blocks") or []
        question_count += sum(1 for block in blocks if block.get("kind") == "question")
        entry_count += sum(1 for block in blocks if block.get("type") == "entry")
        issues = value.get("issues") or []
        if issues:
            issue_pages += 1
        for issue in issues:
            severity = issue.get("severity") if isinstance(issue, dict) else "warning"
            errors += severity == "error"
            warnings += severity != "error"
    return {
        "pages": page_count,
        "questions": question_count,
        "entries": entry_count,
        "issuePages": issue_pages,
        "errors": errors,
        "warnings": warnings,
    }


def _try_extract_printed_answer_key(ocr_dir: Path, draft: Path) -> dict[str, Any] | None:
    doc_path = ocr_dir / "document.json"
    if not doc_path.exists():
        return None
    try:
        doc = json.loads(doc_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    pages = doc.get("pages") or []
    for page in reversed(pages):
        text = str(page.get("markdown") or "")
        ptype = str(page.get("pageType") or "")
        if ptype == "answers" or re.search(r"正解|解答|Answers", text):
            p_num = page.get("page")
            lines = text.splitlines()
            answer_rows = []
            for ln in lines:
                ln_norm = unicodedata.normalize("NFKC", ln).strip()
                matches = re.findall(r"(?:^|\s)(\d{1,2})[\s.、:：]+([1-4])(?:\s|$)", ln_norm)
                answer_rows.extend(matches)
            if len(answer_rows) >= 3:
                evidence_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                evidence = {
                    "source": "printed_answer_table",
                    "page": p_num,
                    "evidenceSha256": evidence_hash,
                    "extractedCount": len(answer_rows),
                    "confidence": "high",
                }
                write_json(draft / "answer-evidence.json", evidence)
                answers_map = {int(q): int(a) for q, a in answer_rows}
                min_q, max_q = min(answers_map.keys()), max(answers_map.keys())
                digits = "".join(str(answers_map.get(i, 1)) for i in range(min_q, max_q + 1))
                key_text = (
                    f"# 从第 {p_num} 页印刷正解表自动提取（哈希：{evidence_hash[:16]}）\n"
                    f"written {min_q}-{max_q} 1 {digits}\n"
                )
                (draft / "answer-key.txt").write_text(key_text, encoding="utf-8")
                return evidence
    return None


def _write_exam_draft(
    *,
    ocr_dir: Path,
    artifact_dir: Path,
    slug: str,
    title: str,
    level: str,
    source_name: str,
    digest: str,
    source_bytes: int,
    page_count: int,
) -> tuple[Path, dict[str, int], list[str]]:
    draft = artifact_dir / "exam" / slug
    pages = draft / "pages"
    _run([
        sys.executable,
        str(EXAM_DRAFT_SCRIPT),
        "--ocr",
        str(ocr_dir),
        "--out",
        str(pages),
        "--level",
        level,
    ])
    meta = {
        "schemaVersion": 1,
        "level": level,
        "slug": slug,
        "title": title,
        "sessionLabel": "",
        "durationSec": 10800,
        "source": {
            "kind": "pdf-upload",
            "fileName": source_name,
            "sha256": digest,
            "bytes": source_bytes,
            "pageCount": page_count,
            "importedOn": date.today().isoformat(),
            "rights": "Personal study copy supplied by the user; not cleared for redistribution.",
        },
    }
    write_json(draft / "exam-meta.json", meta)

    evidence = _try_extract_printed_answer_key(ocr_dir, draft)
    if evidence:
        next_steps = [
            f"已自动从第 {evidence['page']} 页提取印刷正解表（{evidence['extractedCount']} 题）。",
            "核对原图与 pages/pNN.json，清空疑点后即可入库。",
        ]
    else:
        (draft / "answer-key.txt").write_text(
            "# 未在文档中检测到印刷正解表；自动化契约拒绝由模型猜测答案。\n"
            "# 待人工逐格抄录卷末答案，格式见 docs/JLPT_EXAM_PIPELINE.md。\n",
            encoding="utf-8",
        )
        next_steps = [
            "卷末未检测到印刷正解表；自动化契约拒绝模型猜测答案。",
            "如需正式计分，请在 answer-key.txt 填入核验证据。",
        ]
    _write_review_file(draft, title, next_steps)
    return draft, _page_stats(pages), next_steps


def _unit_ledger(pages_dir: Path) -> str:
    units: dict[tuple[int, int], str] = {}
    for path in sorted(pages_dir.glob("p*.json")):
        page = json.loads(path.read_text(encoding="utf-8"))
        header = page.get("unitHeader")
        if not isinstance(header, dict):
            continue
        try:
            key = int(header.get("week")), int(header.get("day"))
        except (TypeError, ValueError):
            continue
        if key[1] == 7:
            continue
        units.setdefault(key, str(header.get("title") or "待核对标题"))
    lines = ["# 请对照印刷目录填写每单元条目数；? 不会通过 assemble。"]
    lines += [f"第{week}週 {day}日目 {title} ?" for (week, day), title in sorted(units.items())]
    return "\n".join(lines) + "\n"


def _write_lexicon_draft(
    *,
    ocr_dir: Path,
    artifact_dir: Path,
    slug: str,
    title: str,
    level: str,
    kind: str,
    digest: str,
) -> tuple[Path, dict[str, int], list[str]]:
    draft = artifact_dir / "lexicon" / slug
    _run([
        sys.executable,
        str(LEXICON_SCRIPT),
        "extract",
        "--document",
        str(ocr_dir / "document.json"),
        "--out",
        str(draft),
        "--kind",
        kind,
    ])
    meta = {
        "schemaVersion": 1,
        "packId": slug,
        "kind": kind,
        "level": level,
        "title": title,
        "attribution": {
            "sourceType": "textbook-ocr",
            "publisher": "待人工填写",
            "sourceSha256": digest,
            "redistributable": False,
        },
    }
    write_json(draft / "pack-meta.json", meta)
    (draft / "source.pdf.sha256").write_text(digest + "\n", encoding="ascii")
    write_json(
        draft / "entry-keys.json",
        {"schemaVersion": 1, "packId": slug, "nextKey": 1, "entries": []},
    )
    (draft / "units.txt").write_text(_unit_ledger(draft / "pages"), encoding="utf-8")
    next_steps = [
        "逐页对照 ocr/images 与 pages/，修复 error 并核对见出词、例句和译文。",
        "对照印刷目录填写 units.txt 中每个 ?，并补全出版社信息。",
        "运行 lexicon_import.py assemble --accept-new-keys 与 validate；通过后再复制到 lexicon/。",
    ]
    _write_review_file(draft, title, next_steps)
    return draft, _page_stats(draft / "pages"), next_steps


def _write_review_file(directory: Path, title: str, steps: list[str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    body = [f"# {title} — 待复核", "", "后台已完成可安全自动化的步骤。正式入库前还需：", ""]
    body += [f"{index}. {step}" for index, step in enumerate(steps, 1)]
    (directory / "REVIEW_REQUIRED.md").write_text("\n".join(body) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> dict[str, Any]:
    pdf = args.pdf.resolve()
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise RuntimeError(f"Not a PDF file: {pdf}")
    artifact_dir = args.out.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir = artifact_dir / "ocr"
    config, config_path = load_config_file(args.config)

    requested = list(dict.fromkeys([args.vision_profile, *args.review_profile]))
    profiles = [resolve_vision_profile(config, name) for name in requested]
    available: list[VisionProfile] = []
    unavailable: list[dict[str, str]] = []
    print("视觉模型预检：", flush=True)
    for profile in profiles:
        ready, note = profile_readiness(profile)
        print(f"  {'✓' if ready else '×'} {profile.name}: {note}", flush=True)
        if ready:
            available.append(profile)
        else:
            unavailable.append({"profile": profile.name, "reason": note})
    if not available:
        raise RuntimeError("选定 OCR 管线没有可用模型；请启动本地服务或显式选择已配置的云端管线。")

    used: list[str] = []
    for index, profile in enumerate(available):
        report_path = ocr_dir / "quality-report.json"
        if index and report_path.is_file() and not _quality_report(ocr_dir).get("flagged_pages"):
            break
        _run(_ocr_argv(pdf, ocr_dir, profile, retry_flagged=index > 0))
        used.append(profile.name)

    report = _quality_report(ocr_dir)
    page_rows = report.get("pages") or []
    readable = [row for row in page_rows if isinstance(row, dict) and not row.get("error")]
    if not readable or int(report.get("total_chars") or 0) <= 0:
        raise RuntimeError("所有 PDF 页面都未能识别；没有生成可供复核的正文。")

    document = _document(ocr_dir)
    detected = classify_document(document)
    selected_kind = detected["kind"] if args.kind == "auto" else args.kind
    selected_level = detected["level"] if args.level == "auto" and detected["level"] else args.level
    if selected_level == "auto":
        selected_level = "N2"
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    slug = _slug(args.name or args.title or args.source_name or pdf.stem, digest)
    title = args.title.strip() or Path(args.source_name or pdf.name).stem

    box_warning = ""
    if selected_kind == "grammar":
        # The second visual pass reads small connection panels at native resolution.
        box_profile = available[1] if len(available) > 1 else available[0]
        if _run(_boxes_argv(pdf, ocr_dir, box_profile), required=False) == 0:
            _run(_ocr_argv(pdf, ocr_dir, available[0], mark_ruby=True))
            report = _quality_report(ocr_dir)
        else:
            box_warning = "接続框二次识别失败；正文草稿仍保留，相关条目必须人工补录。"

    stats: dict[str, int] = {
        "pages": int(report.get("pages_transcribed") or 0),
        "questions": 0,
        "entries": 0,
        "issuePages": len(report.get("flagged_pages") or []),
        "errors": sum(1 for row in report.get("pages") or [] if "error" in (row.get("flags") or [])),
        "warnings": len(report.get("flagged_pages") or []),
    }
    if selected_kind == "exam":
        draft, stats, next_steps = _write_exam_draft(
            ocr_dir=ocr_dir,
            artifact_dir=artifact_dir,
            slug=slug,
            title=title,
            level=selected_level,
            source_name=args.source_name or pdf.name,
            digest=digest,
            source_bytes=pdf.stat().st_size,
            page_count=int(report.get("source", {}).get("pages") or stats["pages"]),
        )
    elif selected_kind in {"grammar", "word"}:
        draft, stats, next_steps = _write_lexicon_draft(
            ocr_dir=ocr_dir,
            artifact_dir=artifact_dir,
            slug=slug,
            title=title,
            level=selected_level,
            kind=selected_kind,
            digest=digest,
        )
    else:
        draft = ocr_dir
        next_steps = ["检查 quality-report.json 中的异常页，并对照 images/ 修订 document.json。"]
        _write_review_file(artifact_dir, title, next_steps)

    if box_warning:
        next_steps.insert(0, box_warning)
        _write_review_file(draft, title, next_steps)

    auto_install_flag = getattr(args, "auto_install", False)

    # D02: Handle zero-entry extraction failure
    if selected_kind in {"grammar", "word"} and stats.get("entries", 0) == 0:
        result = {
            "schemaVersion": 1,
            "sourceKind": "pdf",
            "status": "failed",
            "outcomeCode": "extraction_empty",
            "qualityDecision": "failed",
            "reviewRequired": False,
            "title": title,
            "slug": slug,
            "requestedKind": args.kind,
            "detected": detected,
            "kind": selected_kind,
            "level": selected_level,
            "artifactRoot": str(artifact_dir),
            "draftPath": str(draft),
            "primaryArtifact": str(draft / "pack-meta.json"),
            "ocr": {
                "configPath": str(config_path) if config_path else "",
                "requestedProfiles": requested,
                "usedProfiles": used,
                "unavailableProfiles": unavailable,
                "flaggedPages": report.get("flagged_pages") or [],
                "totalChars": int(report.get("total_chars") or 0),
            },
            "stats": stats,
            "error": "未从文档中提取到有效条目 (extraction_empty)。素材已自动隔离，未生成强制人工待办。",
            "nextSteps": ["素材已自动隔离。若需支持该排版，需编写针对该教材的版式适配器。"],
        }
        write_json(args.result.resolve(), result)
        print(f"\nPDF 词汇条目为 0，已自动隔离：{selected_kind} / {slug}", flush=True)
        return result

    auto_installed = False
    installed_to = ""

    if auto_install_flag and selected_kind in {"grammar", "word"} and stats["entries"] > 0 and stats["errors"] == 0:
        try:
            from lexicon_import import assemble_pack, load_pages, load_registry, parse_units_file
            from lexicon_schema import audit_pack
            units_file = draft / "units.txt"
            if units_file.exists() and "?" not in units_file.read_text(encoding="utf-8"):
                units = parse_units_file(units_file.read_text(encoding="utf-8"))
                meta = json.loads((draft / "pack-meta.json").read_text(encoding="utf-8"))
                registry = load_registry(draft / "entry-keys.json", slug)
                pages_data = load_pages(draft / "pages")
                pack, recon = assemble_pack(pages_data, units, registry, meta, accept_new_keys=True)
                pack_audit = audit_pack(pack)
                if pack_audit["summary"]["errors"] == 0 and recon.get("ok"):
                    dest_dir = PROJECT_DIR / "lexicon" / slug
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    write_json(dest_dir / "pack.json", pack)
                    auto_installed = True
                    installed_to = f"lexicon/{slug}"
        except Exception as e:
            print(f"Auto-assembly for lexicon failed: {e}", flush=True)

    if auto_install_flag and selected_kind == "exam" and stats["errors"] == 0:
        key_path = draft / "answer-key.txt"
        if key_path.exists() and "待人工逐格抄录" not in key_path.read_text(encoding="utf-8") and "未在文档中检测到" not in key_path.read_text(encoding="utf-8"):
            try:
                from exam_import import assemble_exam, load_pages as load_exam_pages, parse_answer_key
                from exam_store import check_exam_qualification
                key = parse_answer_key(key_path.read_text(encoding="utf-8"))
                meta = json.loads((draft / "exam-meta.json").read_text(encoding="utf-8"))
                pages_data = load_exam_pages(draft / "pages")
                exam = assemble_exam(pages_data, key, meta)
                qualified, reasons = check_exam_qualification(exam)
                if qualified:
                    dest_dir = PROJECT_DIR / "exams" / slug
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    write_json(dest_dir / "exam.json", exam)
                    auto_installed = True
                    installed_to = f"exams/{slug}"
                else:
                    print(f"Exam {slug} failed qualification: {reasons}", flush=True)
            except Exception as e:
                print(f"Auto-assembly for exam failed: {e}", flush=True)

    status = "succeeded" if auto_installed else "needs_review"
    outcome_code = "installed" if auto_installed else ("needs_review" if not auto_install_flag else "quarantined")
    review_required = not auto_installed and not auto_install_flag
    quality_decision = "passed" if auto_installed else ("failed" if stats["errors"] > 0 else "unknown")

    result = {
        "schemaVersion": 1,
        "sourceKind": "pdf",
        "status": status,
        "outcomeCode": outcome_code,
        "qualityDecision": quality_decision,
        "reviewRequired": review_required,
        "title": title,
        "slug": slug,
        "requestedKind": args.kind,
        "detected": detected,
        "kind": selected_kind,
        "level": selected_level,
        "artifactRoot": str(artifact_dir),
        "draftPath": str(draft),
        "installedTo": installed_to,
        "primaryArtifact": str(draft / ("exam-meta.json" if selected_kind == "exam" else "pack-meta.json"))
        if selected_kind in {"exam", "grammar", "word"}
        else str(ocr_dir / "document.json"),
        "ocr": {
            "configPath": str(config_path) if config_path else "",
            "requestedProfiles": requested,
            "usedProfiles": used,
            "unavailableProfiles": unavailable,
            "flaggedPages": report.get("flagged_pages") or [],
            "totalChars": int(report.get("total_chars") or 0),
        },
        "stats": stats,
        "nextSteps": next_steps,
    }
    write_json(args.result.resolve(), result)
    print("\nPDF 草稿处理完成：", flush=True)
    print(f"  类型：{selected_kind}（自动判断：{detected['kind']} / {detected['confidence']}）", flush=True)
    print(f"  状态：{status}（outcome: {outcome_code}）", flush=True)
    print(f"  目录：{draft}", flush=True)
    if installed_to:
        print(f"  已自动安装至：{installed_to}", flush=True)
    print(f"  异常页：{len(report.get('flagged_pages') or [])}", flush=True)
    return result


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--source-name", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--kind", default="auto", choices=DOCUMENT_KINDS)
    parser.add_argument("--level", default="auto", choices=LEVELS)
    parser.add_argument("--vision-profile", required=True)
    parser.add_argument("--review-profile", action="append", default=[])
    parser.add_argument("--auto-install", action="store_true", default=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    signal.signal(signal.SIGTERM, _handle_stop)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _handle_stop)
    args = make_parser().parse_args(argv)
    try:
        build(args)
    except (ConfigError, RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"\nPDF build failed: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
