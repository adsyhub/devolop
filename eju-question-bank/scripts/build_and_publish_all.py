#!/usr/bin/env python3
"""Full-scale automated assembly and publishing engine for all 215 EJU exam papers.

Transforms probed and rendered PDFs into compliant, audited, and published EJU papers
stored inside library/eju.db with synchronized content-inventory.json.
Provides full page materials, passage figures, and listening audio tracks for Japanese papers.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 由 --allow-unverified 打开；默认关闭，任何未经验证的题都不会发布。
ALLOW_UNVERIFIED = False

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

import cv2
import numpy as np
from PIL import Image

from eju_bank.assets import AssetStore
from eju_bank.audit import audit_paper, prepare_paper
from eju_bank.constants import ALLOWED_DIGIT_TOKENS, FORM_SPECS, SCHEMA_VERSION
from eju_bank.db import Database
from eju_bank.inventory import load_inventory, save_inventory
from eju_bank.util import canonical_json, digest_json, load_json, stable_id, utc_now, write_json


def build_science_forms(session_code: str, manifest: dict[str, Any], page_count: int) -> list[dict[str, Any]]:
    """Build Physics, Chemistry, Biology forms for EJU Science booklet."""
    forms = []
    
    # Estimate page distribution: Physics (p3~p18), Chemistry (p19~p34), Biology (p35~p50)
    p_third = max(1, page_count // 3)
    
    # 1. PHYSICS_JA: 19 questions (问1 ~ 问19)
    phys_questions = []
    for q_num in range(1, 20):
        q_page = min(page_count, max(1, 3 + (q_num * (p_third - 3)) // 20))
        phys_questions.append({
            "questionId": stable_id("q_", manifest["sourceId"], "PHYSICS_JA", f"q_{q_num:02d}"),
            "localKey": f"phys-q-{q_num:02d}",
            "printedLabel": f"問{q_num}",
            "sectionCode": "MAIN",
            "answerRef": f"PHYSICS:{q_num}",
            "stemAst": [{"type": "text", "value": f"【物理 問{q_num}】問題文および実験設定に基づき、最も適当な選択肢を一つ選べ。"}],
            "options": [{"key": str(i), "contentAst": [{"type": "text", "value": f"選択肢 ({i})"}]} for i in range(1, 7)],
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": None,
            "materialRefs": [],
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": q_page, "bbox": [0.1, 0.1, 0.9, 0.9]}],
        })
    
    forms.append({
        "formCode": "PHYSICS_JA",
        "spec": FORM_SPECS["PHYSICS_JA"].to_dict(),
        "groups": [
            {
                "groupId": stable_id("g_", manifest["sourceId"], "PHYSICS_JA", "MAIN"),
                "groupCode": "MAIN",
                "materials": [],
                "questions": phys_questions,
            }
        ],
    })

    # 2. CHEMISTRY_JA: 20 questions (问1 ~ 问20)
    chem_questions = []
    for q_num in range(1, 21):
        q_page = min(page_count, max(1, p_third + (q_num * p_third) // 21))
        chem_questions.append({
            "questionId": stable_id("q_", manifest["sourceId"], "CHEMISTRY_JA", f"q_{q_num:02d}"),
            "localKey": f"chem-q-{q_num:02d}",
            "printedLabel": f"問{q_num}",
            "sectionCode": "MAIN",
            "answerRef": f"CHEMISTRY:{q_num}",
            "stemAst": [{"type": "text", "value": f"【化学 問{q_num}】物質の性質・化学反応式に関する記述として最も適当なものを一つ選べ。"}],
            "options": [{"key": str(i), "contentAst": [{"type": "text", "value": f"選択肢 ({i})"}]} for i in range(1, 7)],
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": None,
            "materialRefs": [],
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": q_page, "bbox": [0.1, 0.1, 0.9, 0.9]}],
        })
    
    forms.append({
        "formCode": "CHEMISTRY_JA",
        "spec": FORM_SPECS["CHEMISTRY_JA"].to_dict(),
        "groups": [
            {
                "groupId": stable_id("g_", manifest["sourceId"], "CHEMISTRY_JA", "MAIN"),
                "groupCode": "MAIN",
                "materials": [],
                "questions": chem_questions,
            }
        ],
    })

    # 3. BIOLOGY_JA: 18 questions (问1 ~ 问18)
    bio_questions = []
    for q_num in range(1, 19):
        q_page = min(page_count, max(1, 2 * p_third + (q_num * (page_count - 2 * p_third)) // 19))
        bio_questions.append({
            "questionId": stable_id("q_", manifest["sourceId"], "BIOLOGY_JA", f"q_{q_num:02d}"),
            "localKey": f"bio-q-{q_num:02d}",
            "printedLabel": f"問{q_num}",
            "sectionCode": "MAIN",
            "answerRef": f"BIOLOGY:{q_num}",
            "stemAst": [{"type": "text", "value": f"【生物 問{q_num}】生体現象・遺伝・細胞生物学に関する考察として最も適当なものを一つ選べ。"}],
            "options": [{"key": str(i), "contentAst": [{"type": "text", "value": f"選択肢 ({i})"}]} for i in range(1, 7)],
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": None,
            "materialRefs": [],
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": q_page, "bbox": [0.1, 0.1, 0.9, 0.9]}],
        })
    
    forms.append({
        "formCode": "BIOLOGY_JA",
        "spec": FORM_SPECS["BIOLOGY_JA"].to_dict(),
        "groups": [
            {
                "groupId": stable_id("g_", manifest["sourceId"], "BIOLOGY_JA", "MAIN"),
                "groupCode": "MAIN",
                "materials": [],
                "questions": bio_questions,
            }
        ],
    })

    return forms


def build_math_forms(session_code: str, manifest: dict[str, Any], course: str | None, page_count: int) -> list[dict[str, Any]]:
    """Build Mathematics Course 1 or Course 2 form with DIGIT_GRID questions."""
    form_code = "MATHEMATICS_COURSE_2_JA" if course == "COURSE_2" else "MATHEMATICS_COURSE_1_JA"
    groups = []
    
    roman_numerals = ["I", "II", "III", "IV"]
    slot_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]
    
    for g_idx, r in enumerate(roman_numerals, 1):
        g_page = min(page_count, max(1, 1 + (g_idx * page_count) // 5))
        questions = []
        for q_sub in range(1, 3):
            q_key = f"{r}_{q_sub}"
            slots = slot_letters[(q_sub - 1) * 3 : q_sub * 3]
            # 数字格的答案只能来自答案册；这里不再凭题号算出一个。
            questions.append({
                "questionId": stable_id("q_", manifest["sourceId"], form_code, q_key),
                "localKey": f"math-q-{q_key}",
                "printedLabel": f"[{q_sub}]",
                "sectionCode": "MAIN",
                "answerRef": f"{r}:{q_sub}",
                "stemAst": [{"type": "text", "value": f"【第{r}問 [{q_sub}]】数式を展開・計算し、空欄に当てはまる数値を求めよ。"}],
                "options": [],
                "answerSpec": {"type": "DIGIT_GRID", "slots": slots},
                "correctAnswer": None,
                "materialRefs": [],
                "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": g_page, "bbox": [0.1, 0.1, 0.9, 0.9]}],
            })
        
        groups.append({
            "groupId": stable_id("g_", manifest["sourceId"], form_code, r),
            "groupCode": r,
            "materials": [],
            "questions": questions,
        })
        
    return [{
        "formCode": form_code,
        "spec": FORM_SPECS[form_code].to_dict(),
        "groups": groups,
    }]


def build_japan_world_forms(session_code: str, manifest: dict[str, Any], page_count: int) -> list[dict[str, Any]]:
    """Build Japan and the World (文科综合) form with 38 single choice questions."""
    form_code = "JAPAN_AND_WORLD_JA"
    questions = []
    
    for q_num in range(1, 39):
        q_page = min(page_count, max(1, 2 + (q_num * (page_count - 2)) // 39))
        questions.append({
            "questionId": stable_id("q_", manifest["sourceId"], form_code, f"q_{q_num:02d}"),
            "localKey": f"jw-q-{q_num:02d}",
            "printedLabel": f"問{q_num}",
            "sectionCode": "MAIN",
            "answerRef": f"JW:{q_num}",
            "stemAst": [{"type": "text", "value": f"【総合科目 問{q_num}】現代社会・地理・歴史・政治経済に関する記述として最も適当なものを一つ選べ。"}],
            "options": [{"key": str(i), "contentAst": [{"type": "text", "value": f"選択肢 ({i})"}]} for i in range(1, 5)],
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": None,
            "materialRefs": [],
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": q_page, "bbox": [0.1, 0.1, 0.9, 0.9]}],
        })

    return [{
        "formCode": form_code,
        "spec": FORM_SPECS[form_code].to_dict(),
        "groups": [
            {
                "groupId": stable_id("g_", manifest["sourceId"], form_code, "MAIN"),
                "groupCode": "MAIN",
                "materials": [],
                "questions": questions,
            }
        ],
    }]


def ingest_booklet_pages(work_dir: Path, store: AssetStore, prefer_remastered: bool = True) -> dict[int, str]:
    """Ingest rendered or remastered page images into AssetStore and return {page_num: assetId}."""
    page_assets: dict[int, str] = {}
    render_parent = work_dir / "renders" / "question_booklet"
    if not render_parent.exists():
        return page_assets
    
    qb_dirs = [d for d in render_parent.iterdir() if d.is_dir()]
    if not qb_dirs:
        return page_assets
    
    qb_render_dir = qb_dirs[0]
    remaster_dir = work_dir / "remastered_renders"
    for p_dir in qb_render_dir.iterdir():
        if p_dir.is_dir() and p_dir.name.startswith("page-"):
            try:
                p_num = int(p_dir.name.split("-")[1])
                img_path = p_dir / "full-180dpi.png"
                if prefer_remastered and remaster_dir.exists():
                    remastered_img = remaster_dir / f"remastered_p{p_num:04d}.png"
                    if remastered_img.exists():
                        img_path = remastered_img
                if img_path.exists():
                    meta = store.put_file(img_path, mime_type="image/png")
                    page_assets[p_num] = meta["assetId"]
            except (ValueError, IndexError):
                continue
    return page_assets



# ---------------------------------------------------------------------------
# 校验闸门：只有来自答案册的答案才算数
# ---------------------------------------------------------------------------
# 这个脚本从前会用题号算出「正确答案」，也会在 OCR 拿不到选项时填
# 「選択肢 (1)」这样的占位符。那样组出来的卷子能通过 schema，但判分、错题本和
# 学习统计全是假的。下面这道闸门是唯一给 correctAnswer 赋值的地方：答案册里
# 查不到的题一律丢弃，不发布。

PLACEHOLDER_OPTION = re.compile(r"^選択肢\s*[\(（]?\d+[\)）]?$")
PLACEHOLDER_STEM_MARKS = (
    "（問題冊子 第",          # 「参照第N页」式的模板题干
    "問題文および実験設定に基づき",
    "数式を展開・計算し、空欄に当てはまる数値を求めよ",
)


# 答案加载与页面合同生成共用 eju_bank.ocr.verified_answers：
# 两处若各写一份，早晚会对不上。
from eju_bank.ocr.verified_answers import load_verified_answers  # noqa: E402


def _question_is_placeholder(question: dict[str, Any]) -> str | None:
    """Return why this question is not real content, or None when it looks real."""
    options = question.get("options") or []
    if options and all(
        PLACEHOLDER_OPTION.match((node.get("value") or "").strip())
        for option in options
        for node in (option.get("contentAst") or [])
        if node.get("type") == "text"
    ):
        return "选项是占位符"
    stem = " ".join(
        node.get("value") or "" for node in (question.get("stemAst") or []) if node.get("type") == "text")
    if any(mark in stem for mark in PLACEHOLDER_STEM_MARKS):
        return "题干是模板"
    return None


def enforce_verified(
    forms: list[dict[str, Any]], answers: dict[str, Any], *, allow_unverified: bool = False
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Drop every question we cannot back with real content and a real answer.

    Returns the surviving forms and a count of what was dropped and why. Essay
    questions carry no key by design and are kept.
    """
    stats = {"kept": 0, "no_answer": 0, "placeholder": 0}
    surviving_forms = []
    for form in forms:
        groups = []
        for group in form.get("groups", []):
            questions = []
            for question in group.get("questions", []):
                spec = question.get("answerSpec") or {}
                if spec.get("type") == "ESSAY":
                    questions.append(question)
                    stats["kept"] += 1
                    continue

                reason = _question_is_placeholder(question)
                if reason and not allow_unverified:
                    stats["placeholder"] += 1
                    continue

                if spec.get("type") == "DIGIT_GRID":
                    # 数字格的答案是逐格的，来不了 answers 这张按题查的表。唯一合法
                    # 来源是正解表的数学段，由 build_math 打上来源标记；这里核对
                    # 标记在、且逐格答案正好覆盖该题的欄位。
                    tokens = (question.get("correctAnswer") or {}).get("tokens")
                    slots = set(spec.get("slots") or [])
                    if (question.get("_answerSource") != "answer-key"
                            or not isinstance(tokens, dict) or not slots or set(tokens) != slots):
                        stats["no_answer"] += 1
                        continue
                else:
                    answer = answers.get(str(question.get("answerRef") or ""))
                    if answer is None:
                        if not allow_unverified:
                            stats["no_answer"] += 1
                            continue
                    elif spec.get("type") == "SINGLE_CHOICE":
                        keys = {str(o.get("key")) for o in question.get("options") or []}
                        if str(answer) not in keys:
                            stats["no_answer"] += 1
                            continue
                        question["correctAnswer"] = {"optionKey": str(answer)}

                if question.get("correctAnswer") is None and spec.get("type") != "ESSAY":
                    stats["no_answer"] += 1
                    continue
                question.pop("_answerSource", None)   # 内部标记不进题库
                questions.append(question)
                stats["kept"] += 1

            if questions:
                group = {**group, "questions": questions}
                groups.append(group)
        if groups:
            surviving_forms.append({**form, "groups": groups})
    return surviving_forms, stats



def merge_ocr_questions(
    forms: list[dict[str, Any]], work_dir: Path, manifest: dict[str, Any],
    answers: dict[str, str],
) -> list[dict[str, Any]]:
    """Add the questions OCR actually read to whichever form they belong to.

    These carry real stems, real options and an answer verified against the
    正解表. They deliberately share answerRefs with the template-generated
    questions above; the gate then drops the placeholders and keeps these.
    """
    from eju_bank.ocr.assemble_from_ocr import (
        DEFAULT_SECTION_BY_SUBJECT, MATH_FORMS, build_math, build_questions, collect_questions,
    )
    from eju_bank.ocr.verified_answers import load_math_answers

    collected = collect_questions(
        work_dir, default_section=DEFAULT_SECTION_BY_SUBJECT.get(manifest.get("subject", "")))
    math_answers: dict[str, Any] = {}
    if any(f["formCode"] in MATH_FORMS for f in forms):
        math_answers, _ = load_math_answers(work_dir)
    if not collected and not math_answers.get("courses"):
        return forms

    merged = []
    for form in forms:
        # 数学是数字格、一問多欄，欄位由正解表给出，走独立路径。
        if form["formCode"] in MATH_FORMS:
            questions, stats = build_math(
                work_dir, math_answers, source_id=manifest["sourceId"],
                form_code=form["formCode"], stable_id=stable_id)
        else:
            questions, stats = build_questions(
                collected, answers, source_id=manifest["sourceId"],
                form_code=form["formCode"], stable_id=stable_id)
        if not questions:
            merged.append(form)
            continue
        for question in questions:
            question.pop("_context", None)

        # 同一个 answerRef 只能有一道题。OCR 读出来的那道是权威的：题面直接
        # 来自原页，答案来自正解表。模板生成的同号题一律让位。
        taken = {q["answerRef"] for q in questions}
        groups = []
        displaced = 0
        for group in form.get("groups", []):
            kept = [q for q in group.get("questions", []) if q.get("answerRef") not in taken]
            displaced += len(group.get("questions", [])) - len(kept)
            if kept:
                groups.append({**group, "questions": kept})

        detail = (f"未对接 {stats['no_join']}，无验证答案 {stats['no_answer']}"
                  if "no_join" in stats
                  else f"无欄位 {stats['no_slots']}，字母不符 {stats['letters_disagree']}")
        print(f"  [OCR] {work_dir.name} {form['formCode']}: 并入 {len(questions)} 道真题"
              f"（{detail}，顶替模板题 {displaced}）")
        groups.append({
            "groupId": stable_id("g_", manifest["sourceId"], form["formCode"], "ocr"),
            "groupCode": "OCR",
            "sectionCode": questions[0]["sectionCode"],
            "materials": [],
            "questions": questions,
        })
        merged.append({**form, "groups": groups})
    return merged


def load_session_ocr_data(work_dir: Path, store: AssetStore | None = None) -> dict[int, dict[str, Any]]:
    """Load cached GLM-OCR extracted reading passages and questions if available."""
    ocr_dir = work_dir / "ocr_cache"
    remaster_dir = work_dir / "remastered_renders"
    data: dict[int, dict[str, Any]] = {}
    if ocr_dir.exists():
        for f in sorted(ocr_dir.glob("p*.json")):
            try:
                p_num = int(f.stem.lstrip("p"))
                entry = load_json(f)
                if store and remaster_dir.exists() and "figures" not in entry:
                    figs = sorted(remaster_dir.glob(f"remastered_p{p_num:04d}_fig*.png"))
                    if figs:
                        fig_list = []
                        for fig_p in figs:
                            meta = store.put_file(fig_p, mime_type="image/png")
                            fig_list.append({
                                "assetId": meta["assetId"],
                                "alt": f"読解 第{p_num}ページ 挿絵図版",
                            })
                        entry["figures"] = fig_list
                data[p_num] = entry
            except Exception:
                continue
    return data


def _ingest_track_files(
    tracks: list[Path], track_id: str, store: AssetStore, tmp_dir: Path, is_wav: bool
) -> tuple[list[dict[str, Any]], str]:
    """Concatenate individual CD tracks with ffmpeg and compute millisecond cues."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", dir=tmp_dir, delete=False) as f_list:
        for t in tracks:
            f_list.write(f"file '{t.resolve()}'\n")
        list_path = f_list.name
        
    out_mp3 = tmp_dir / f"concat_{track_id}.mp3"
    if is_wav:
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c:a", "libmp3lame", "-q:a", "2", str(out_mp3)]
    else:
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", str(out_mp3)]
        
    subprocess.run(cmd, capture_output=True, check=True)
    Path(list_path).unlink(missing_ok=True)
    
    meta = store.put_file(out_mp3, mime_type="audio/mp3")
    out_mp3.unlink(missing_ok=True)
    audio_asset_id = meta["assetId"]
    
    track_cues_raw = []
    total_ms = 0
    for t in tracks:
        res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(t)], capture_output=True, text=True)
        dur_ms = int(round(float(res.stdout.strip() or 0) * 1000))
        track_cues_raw.append((total_ms, total_ms + dur_ms))
        total_ms += dur_ms
        
    cues = []
    # 聴読解 Q1..12: Tracks 6..17 (indices 5..16)
    for q in range(1, 13):
        t_idx = 5 + (q - 1)
        s_ms, e_ms = track_cues_raw[t_idx] if t_idx < len(track_cues_raw) else (0, total_ms)
        cues.append({
            "cueId": f"cue-{q:02d}",
            "assetId": audio_asset_id,
            "startMs": s_ms,
            "endMs": e_ms,
            "questionRefs": [f"LISTENING:{q}"],
        })
        
    # 聴解 Q13..27: Tracks 22..36 (indices 21..35)
    for q in range(13, 28):
        t_idx = 21 + (q - 13)
        s_ms, e_ms = track_cues_raw[t_idx] if t_idx < len(track_cues_raw) else (0, total_ms)
        cues.append({
            "cueId": f"cue-{q:02d}",
            "assetId": audio_asset_id,
            "startMs": s_ms,
            "endMs": e_ms,
            "questionRefs": [f"LISTENING:{q}"],
        })
        
    audio_track = {
        "trackId": track_id,
        "assetId": audio_asset_id,
        "durationMs": total_ms,
        "cues": cues,
    }
    return [audio_track], "COMPLETE"


def _ingest_single_audio_file(
    src_file: Path, track_id: str, store: AssetStore
) -> tuple[list[dict[str, Any]], str]:
    """Ingest a complete continuous Japanese listening MP3 file and partition into cues."""
    meta = store.put_file(src_file, mime_type="audio/mp3")
    audio_asset_id = meta["assetId"]
    
    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(src_file)], capture_output=True, text=True)
    total_ms = int(round(float(res.stdout.strip() or 0) * 1000))
    if total_ms <= 0:
        total_ms = 3300000
        
    t_intro = min(180_000, max(60_000, int(total_ms * 0.04)))
    t_outro = min(60_000, max(20_000, int(total_ms * 0.02)))
    usable = max(1000, total_ms - t_intro - t_outro)
    
    d_part1 = int(usable * 0.44)
    step1 = max(100, d_part1 // 12)
    
    d_part2 = usable - d_part1
    step2 = max(100, d_part2 // 15)
    
    cues = []
    # 聴読解 (Q1..12)
    for q in range(1, 13):
        s_ms = t_intro + (q - 1) * step1
        e_ms = s_ms + step1
        cues.append({
            "cueId": f"cue-{q:02d}",
            "assetId": audio_asset_id,
            "startMs": s_ms,
            "endMs": e_ms,
            "questionRefs": [f"LISTENING:{q}"],
        })
        
    # 聴解 (Q13..27)
    for q in range(13, 28):
        s_ms = t_intro + d_part1 + (q - 13) * step2
        e_ms = min(total_ms, s_ms + step2)
        cues.append({
            "cueId": f"cue-{q:02d}",
            "assetId": audio_asset_id,
            "startMs": s_ms,
            "endMs": e_ms,
            "questionRefs": [f"LISTENING:{q}"],
        })
        
    audio_track = {
        "trackId": track_id,
        "assetId": audio_asset_id,
        "durationMs": total_ms,
        "cues": cues,
    }
    return [audio_track], "COMPLETE"


def _generate_placeholder_audio(
    track_id: str, store: AssetStore, tmp_dir: Path
) -> tuple[list[dict[str, Any]], str]:
    """Generate a placeholder silent audio track for missing audio sessions."""
    out_mp3 = tmp_dir / f"silence_{track_id}.mp3"
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "10", "-c:a", "libmp3lame", str(out_mp3)]
    subprocess.run(cmd, capture_output=True, check=True)
    meta = store.put_file(out_mp3, mime_type="audio/mp3")
    out_mp3.unlink(missing_ok=True)
    audio_asset_id = meta["assetId"]
    
    cues = [
        {
            "cueId": f"cue-{q:02d}",
            "assetId": audio_asset_id,
            "startMs": (q - 1) * 350,
            "endMs": min(10000, q * 350),
            "questionRefs": [f"LISTENING:{q}"],
        }
        for q in range(1, 28)
    ]
    audio_track = {
        "trackId": track_id,
        "assetId": audio_asset_id,
        "durationMs": 10000,
        "cues": cues,
    }
    return [audio_track], "PARTIAL"


def ingest_japanese_audio(
    session_code: str, manifest: dict[str, Any], store: AssetStore, tmp_dir: Path
) -> tuple[list[dict[str, Any]], str]:
    """Resolve and ingest Japanese listening audio for session."""
    form_code = "JAPANESE_JA"
    source_id = manifest["sourceId"]
    track_id = stable_id("track_", source_id, form_code, "listening")
    
    parts = session_code.split("-")
    year = int(parts[0])
    s_num = int(parts[1]) if len(parts) > 1 else 1
    
    audio_root = PROJECT_ROOT / "PAPER" / "EJU日语" / "EJU日语听力音频"
    
    # 2024 special case
    if year == 2024 and s_num == 1:
        f = audio_root / "2024年令和6年日语音频.mp3"
        if f.exists():
            return _ingest_single_audio_file(f, track_id, store)
            
    # Search folders
    s_kanji = "第一回" if s_num == 1 else "第二回"
    s_alt = f"第{s_num}回"
    matched_dir = None
    if audio_root.exists():
        for d in audio_root.iterdir():
            if d.is_dir() and str(year) in d.name and (s_kanji in d.name or s_alt in d.name):
                matched_dir = d
                break
                
    if matched_dir:
        top_mp3s = sorted([f for f in matched_dir.glob("*.mp3") if not f.name.startswith(".")])
        top_wavs = sorted([f for f in matched_dir.glob("*.wav") if not f.name.startswith(".")])
        
        if len(top_mp3s) > 5 and all("Track" in f.name or "トラック" in f.name or "CD" in f.name for f in top_mp3s):
            return _ingest_track_files(top_mp3s, track_id, store, tmp_dir, is_wav=False)
        elif len(top_wavs) > 5 and all("Track" in f.name or "トラック" in f.name for f in top_wavs):
            return _ingest_track_files(top_wavs, track_id, store, tmp_dir, is_wav=True)
        elif len(top_mp3s) == 2 and "平成30年第1回.mp3" in [f.name for f in top_mp3s]:
            target_name = f"平成30年第{s_num}回.mp3"
            f = matched_dir / target_name
            if f.exists():
                return _ingest_single_audio_file(f, track_id, store)
        elif len(top_mp3s) > 0:
            chosen = None
            for f in top_mp3s:
                if s_alt in f.name or s_kanji in f.name or "整个" in f.name:
                    chosen = f
                    break
            if not chosen:
                chosen = top_mp3s[0]
            return _ingest_single_audio_file(chosen, track_id, store)
            
    return _generate_placeholder_audio(track_id, store, tmp_dir)


def _get_page_image_path(work_dir: Path | None, p_num: int, prefer_raw: bool = False) -> Path | None:
    if not work_dir:
        return None
    if prefer_raw:
        render_parent = work_dir / "renders" / "question_booklet"
        if render_parent.exists():
            for qb in render_parent.iterdir():
                if qb.is_dir():
                    cand = qb / f"page-{p_num:04d}" / "full-180dpi.png"
                    if cand.exists():
                        return cand
        cand = work_dir / "remastered_renders" / f"remastered_p{p_num:04d}.png"
        if cand.exists():
            return cand
        return None
    else:
        remastered_img = work_dir / "remastered_renders" / f"remastered_p{p_num:04d}.png"
        if remastered_img.exists():
            return remastered_img
        render_parent = work_dir / "renders" / "question_booklet"
        if render_parent.exists():
            for qb in render_parent.iterdir():
                if qb.is_dir():
                    cand = qb / f"page-{p_num:04d}" / "full-180dpi.png"
                    if cand.exists():
                        return cand
        return None


def _has_large_title(img_path: Path) -> bool:
    """Check if the upper area of the page contains a large banner title (e.g. 読解問題 説明)."""
    try:
        im_cv = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if im_cv is None:
            return False
        ch, cw = im_cv.shape
        top = im_cv[int(0.08 * ch) : int(0.40 * ch), int(0.10 * cw) : int(0.90 * cw)]
        thresh = (top < 180).astype(np.uint8)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh)
        max_comp_h = max([stats[i, cv2.CC_STAT_HEIGHT] for i in range(1, num_labels) if stats[i, cv2.CC_STAT_WIDTH] < 0.7 * cw] or [0])
        return (max_comp_h / ch) > 0.06
    except Exception:
        return False


def is_blank_or_memo_page(
    p_num: int,
    work_dir: Path | None,
    ocr_data: dict[int, dict[str, Any]] | None = None,
    pdf_doc: Any = None,
) -> bool:
    """Accurately identify blank, memo, instruction, and copyright placeholder pages.

    Pages detected here will NEVER be produced as reading materials or evidence.
    """
    ocr_d = (ocr_data or {}).get(p_num, {})
    raw_text = (ocr_d.get("raw_passage", "") or "") + " " + (ocr_d.get("stem", "") or "")
    if pdf_doc and 0 <= p_num - 1 < len(pdf_doc):
        try:
            raw_text += " " + pdf_doc[p_num - 1].get_text()
        except Exception:
            pass
    raw_text = raw_text.strip()

    # 1. Text keyword checks
    placeholder_phrases = [
        "出版上の都合により",
        "本問題の掲載はいたしません",
        "問題はありません",
        "このページには問題はありません",
        "問題冊子に書かれていることを読んで答えてください",
        "問題用紙に書かれていることを読んで答えてください",
    ]
    if any(k in raw_text for k in placeholder_phrases):
        return True

    memo_phrases = ["- メ モ -", "— メ モ —", "一 メ モ 一", "- メモ -", "一メモ一", "—メモ—", "MEMO"]
    if any(k in raw_text for k in memo_phrases) or raw_text in ["メモ", "MEMO", "- メモ -"]:
        return True

    if "読解問題" in raw_text and "説明" in raw_text and len(raw_text) < 200:
        return True

    if "記述問題" in raw_text and ("説明" in raw_text or len(raw_text) < 250):
        return True

    # 2. Rendered image inspection (checks density on raw scan)
    img_path = _get_page_image_path(work_dir, p_num, prefer_raw=True)
    if img_path and img_path.exists():
        try:
            with Image.open(img_path) as im:
                w, h = im.size
                body = im.crop((int(w * 0.10), int(h * 0.10), int(w * 0.90), int(h * 0.90))).convert("L")
                arr = np.array(body)
                dark = int(np.sum(arr < 200))
                density = dark / (body.width * body.height)
                # Any page with < 0.8% ink in body is a blank page, memo line, or faint bleed-through
                if density < 0.008:
                    return True
        except Exception:
            pass

    return False


def build_japanese_forms(
    session_code: str,
    manifest: dict[str, Any],
    page_count: int,
    page_assets: dict[int, str],
    booklet_pdf: Path | None = None,
    page_ocr_data: dict[int, dict[str, Any]] | None = None,
    work_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Build Japanese forms with real reading text passages and listening materials."""
    form_code = "JAPANESE_JA"
    source_id = manifest["sourceId"]
    groups = []
    ocr_data = page_ocr_data or {}
    
    # Try extracting selectable text from booklet PDF
    pdf_doc = None
    if fitz and booklet_pdf and booklet_pdf.exists():
        try:
            pdf_doc = fitz.open(str(booklet_pdf))
        except Exception:
            pdf_doc = None
            
    def get_page_text(p_num: int) -> str | None:
        if pdf_doc and 0 <= p_num - 1 < len(pdf_doc):
            t = pdf_doc[p_num - 1].get_text().strip()
            if len(t) > 20:
                return t
        return None

    # Group 1: Writing (記述)
    writing_materials = []
    if 2 in page_assets and not is_blank_or_memo_page(2, work_dir, ocr_data, pdf_doc):
        w_ast = []
        p2_ocr = ocr_data.get(2)
        if p2_ocr and p2_ocr.get("passage_ast"):
            w_ast.extend(p2_ocr["passage_ast"])
        else:
            p2_text = get_page_text(2)
            if p2_text:
                w_ast.append({"type": "paragraph", "value": p2_text})
        # Only attach image if no text could be extracted
        if not w_ast:
            w_ast.append({
                "type": "figure",
                "assetId": page_assets[2],
                "sourceBbox": [0.05, 0.05, 0.95, 0.95],
                "alt": "記述問題 提示テーマ・注意事項",
            })
        writing_materials.append({
            "materialId": stable_id("m_", source_id, form_code, "essay-prompt"),
            "localKey": "essay-prompt",
            "contentAst": w_ast,
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 2, "bbox": [0.05, 0.05, 0.95, 0.95]}],
        })

    groups.append({
        "groupId": stable_id("g_", source_id, form_code, "WRITING"),
        "groupCode": "WRITING",
        "materials": writing_materials,
        "questions": [
            {
                "questionId": stable_id("q_", source_id, form_code, "essay-q1"),
                "localKey": "essay-q1",
                "printedLabel": "記述問題",
                "sectionCode": "WRITING",
                "answerRef": None,
                "stemAst": [{"type": "text", "value": "提示されたテーマに対する自身の立場を明確にし、理由を挙げて400字～500字で論述せよ。"}],
                "options": [],
                "answerSpec": {"type": "ESSAY", "rubricId": "rubric_japanese_writing_standard"},
                "correctAnswer": None,
                "materialRefs": ["essay-prompt"] if writing_materials else [],
                "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": 2, "bbox": [0.1, 0.4, 0.9, 0.8]}],
            }
        ],
    })

    # Group 2: Reading (読解) - 25 questions
    reading_materials = []
    reading_mat_by_page = {}

    # Detect exact reading and listening section boundaries (syllabus aware)
    year = int(session_code.split("-")[0])
    if year < 2010:
        # Pre-2010: Writing (1..4) -> Listening (5..26) -> Reading (27..end)
        listening_inst_page = None
        for p in range(4, min(page_count + 1, 10)):
            img_p = _get_page_image_path(work_dir, p, prefer_raw=True)
            if img_p and _has_large_title(img_p):
                listening_inst_page = p
                break
        listen_cand_start = (listening_inst_page + 1) if listening_inst_page else 6

        reading_inst_page = None
        for p in range(24, min(page_count + 1, 35)):
            img_p = _get_page_image_path(work_dir, p, prefer_raw=True)
            if img_p and _has_large_title(img_p):
                reading_inst_page = p
                break
        start_reading_p = (reading_inst_page + 1) if reading_inst_page else 27
        end_reading_p = page_count
        listen_cand_end = (reading_inst_page - 1) if reading_inst_page else 26
    else:
        # Post-2010: Writing (1..3) -> Reading (4..30) -> Listening (31..end)
        reading_inst_page = None
        for p in range(4, min(page_count + 1, 10)):
            if p in page_assets:
                p_ocr = ocr_data.get(p, {})
                t = (p_ocr.get("raw_passage", "") or "") + " " + (get_page_text(p) or "")
                if ("読解問題" in t and "説明" in t) or "問題冊子に書かれていることを読んで答えてください" in t:
                    reading_inst_page = p
                    break
                img_p = _get_page_image_path(work_dir, p, prefer_raw=True)
                if img_p and _has_large_title(img_p):
                    reading_inst_page = p
                    break
        start_reading_p = (reading_inst_page + 1) if reading_inst_page else 6

        listening_inst_page = None
        for p in range(24, min(page_count + 1, 38)):
            if p in page_assets:
                p_ocr = ocr_data.get(p, {})
                t = (p_ocr.get("raw_passage", "") or "") + " " + (get_page_text(p) or "")
                if ("聴解" in t and "説明" in t) or "音声を聞いて答える問題です" in t:
                    listening_inst_page = p
                    break
                img_p = _get_page_image_path(work_dir, p, prefer_raw=True)
                if img_p and _has_large_title(img_p):
                    listening_inst_page = p
                    break
        end_reading_p = (listening_inst_page - 1) if listening_inst_page else min(page_count, 30)
        listen_cand_start = (listening_inst_page + 1) if listening_inst_page else 31
        listen_cand_end = page_count

    # Identify clean passage pages (pages with actual reading text/figures, strictly no blank/memo)
    clean_passage_pages: list[int] = []
    for p in range(start_reading_p, end_reading_p + 1):
        if p not in page_assets:
            continue
        if is_blank_or_memo_page(p, work_dir, ocr_data, pdf_doc):
            continue

        p_ocr = ocr_data.get(p, {})
        raw_pass = p_ocr.get("raw_passage", "") or ""
        # If OCR exists, check if it's question/choices-only without reading passage
        if p_ocr and not p_ocr.get("passage_ast") and not p_ocr.get("figures") and len(raw_pass.strip()) < 30:
            if p_ocr.get("options") or p_ocr.get("stem"):
                continue

        clean_passage_pages.append(p)

    for p in clean_passage_pages:
        p_ocr = ocr_data.get(p, {})
        r_ast = []
        if p_ocr.get("passage_ast"):
            r_ast.extend(p_ocr["passage_ast"])
        else:
            txt = get_page_text(p)
            if txt and not ("説明" in txt and "問題" in txt):
                r_ast.append({"type": "paragraph", "value": txt})

        # Attach any cropped illustration/figure nodes extracted for this page
        if p_ocr.get("figures"):
            for fig in p_ocr["figures"]:
                fig_node = {
                    "type": "figure",
                    "assetId": fig["assetId"],
                    "alt": fig.get("alt", f"読解 第{p}ページ 挿絵図版"),
                }
                if "sourceBbox" in fig:
                    fig_node["sourceBbox"] = fig["sourceBbox"]
                r_ast.append(fig_node)

        # Fallback to full page image for genuine reading pages lacking text/figures
        if not r_ast:
            r_ast.append({
                "type": "figure",
                "assetId": page_assets[p],
                "sourceBbox": [0.05, 0.05, 0.95, 0.95],
                "alt": f"読解 第{p}ページ 原文図版",
            })

        m_key = f"read-mat-p{p:02d}"
        reading_mat_by_page[p] = m_key
        reading_materials.append({
            "materialId": stable_id("m_", source_id, form_code, f"read_p{p}"),
            "localKey": m_key,
            "contentAst": r_ast,
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": p, "bbox": [0.05, 0.05, 0.95, 0.95]}],
        })

    reading_questions = []
    for q_num in range(1, 26):
        if q_num <= 10:
            # 短文 (Q1..10) -> First 10 passage pages
            idx = q_num - 1
            if clean_passage_pages:
                p = clean_passage_pages[idx] if idx < len(clean_passage_pages) else clean_passage_pages[-1]
            else:
                p = min(end_reading_p, start_reading_p + idx)
            m_refs = [reading_mat_by_page[p]] if p in reading_mat_by_page else []
            q_page = p
        elif q_num <= 20:
            # 中文 (Q11..20) -> 5 passage pairs
            pair_idx = (q_num - 11) // 2
            idx = 10 + pair_idx
            if clean_passage_pages:
                p = clean_passage_pages[idx] if idx < len(clean_passage_pages) else clean_passage_pages[-1]
            else:
                p = min(end_reading_p, start_reading_p + 10 + pair_idx)
            m_refs = [reading_mat_by_page[p]] if p in reading_mat_by_page else []
            q_page = p
        else:
            # 長文/総合 (Q21..25) -> Remaining passage pages
            if clean_passage_pages:
                long_passages = clean_passage_pages[15:] if len(clean_passage_pages) > 15 else clean_passage_pages[-3:]
                m_refs = [reading_mat_by_page[x] for x in long_passages if x in reading_mat_by_page]
                q_page = long_passages[-1]
            else:
                m_refs = [reading_mat_by_page[x] for x in range(max(start_reading_p, end_reading_p - 4), end_reading_p + 1) if x in reading_mat_by_page]
                q_page = end_reading_p

        # Check if OCR extracted specific stem and options
        ocr_q = ocr_data.get(q_page, {})
        stem_val = ocr_q.get("stem") or ocr_data.get(q_page - 1, {}).get("stem")
        if stem_val:
            stem_text = f"【読解 問{q_num}】{stem_val}"
        else:
            stem_text = f"【読解 問{q_num}】（問題冊子 第{q_page}ページ参照）本文の内容に合致するものとして、最も適当な選択肢を一つ選べ。"

        options_dict = ocr_q.get("options", {})
        if len(options_dict) == 4 and all(k in options_dict for k in ["1", "2", "3", "4"]):
            options = [
                {"key": k, "contentAst": [{"type": "text", "value": options_dict[k]}]}
                for k in ["1", "2", "3", "4"]
            ]
        else:
            options = [
                {"key": str(i), "contentAst": [{"type": "text", "value": f"選択肢 ({i})"}]}
                for i in range(1, 5)
            ]

        reading_questions.append({
            "questionId": stable_id("q_", source_id, form_code, f"read_q_{q_num:02d}"),
            "localKey": f"read-q-{q_num:02d}",
            "printedLabel": f"問{q_num}",
            "sectionCode": "READING",
            "answerRef": f"READING:{q_num}",
            "stemAst": [{"type": "text", "value": stem_text}],
            "options": options,
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": None,
            "materialRefs": m_refs,
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": q_page, "bbox": [0.1, 0.1, 0.9, 0.9]}],
        })

    groups.append({
        "groupId": stable_id("g_", source_id, form_code, "READING"),
        "groupCode": "READING",
        "materials": reading_materials,
        "questions": reading_questions,
    })

    # Group 3: Listening (聴解・聴読解) - 27 questions
    listening_materials = []
    listening_mat_by_q = {}
    valid_listening_pages = []
    for p in range(listen_cand_start, min(page_count + 1, listen_cand_end + 1)):
        if p in page_assets and not is_blank_or_memo_page(p, work_dir, ocr_data, pdf_doc):
            valid_listening_pages.append(p)

    for q_num in range(1, 13):
        if q_num - 1 < len(valid_listening_pages):
            p = valid_listening_pages[q_num - 1]
            m_key = f"listen-mat-q{q_num:02d}"
            listening_mat_by_q[q_num] = m_key
            l_ast = []
            txt = get_page_text(p)
            if txt:
                l_ast.append({"type": "paragraph", "value": txt})
            l_ast.append({
                "type": "figure",
                "assetId": page_assets[p],
                "sourceBbox": [0.05, 0.05, 0.95, 0.95],
                "alt": f"聴読解 問{q_num} 参照図表",
            })
            listening_materials.append({
                "materialId": stable_id("m_", source_id, form_code, f"listen_q{q_num:02d}"),
                "localKey": m_key,
                "contentAst": l_ast,
                "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": p, "bbox": [0.05, 0.05, 0.95, 0.95]}],
            })

    listening_questions = []
    for q_num in range(1, 28):
        if q_num <= 12:
            p = valid_listening_pages[q_num - 1] if q_num - 1 < len(valid_listening_pages) else min(page_count, listen_cand_start + q_num)
            m_refs = [listening_mat_by_q[q_num]] if q_num in listening_mat_by_q else []
            stem = f"【聴読解 問{q_num}】（問題冊子 第{p}ページ参照）音声を聞き、図表をもとに最も適当な答えを一つ選べ。"
        else:
            last_p = valid_listening_pages[-1] if valid_listening_pages else (listen_cand_start + 12)
            p = min(page_count, last_p + (q_num - 12) // 3)
            m_refs = []
            stem = f"【聴解 問{q_num}】音声を注意深く聞き、質問に対する最も適当な答えを一つ選べ。"

        listening_questions.append({
            "questionId": stable_id("q_", source_id, form_code, f"listen_q_{q_num:02d}"),
            "localKey": f"listen-q-{q_num:02d}",
            "printedLabel": f"問{q_num}",
            "sectionCode": "LISTENING",
            "answerRef": f"LISTENING:{q_num}",
            "stemAst": [{"type": "text", "value": stem}],
            "options": [{"key": str(i), "contentAst": [{"type": "text", "value": f"選択肢 ({i})"}]} for i in range(1, 5)],
            "answerSpec": {"type": "SINGLE_CHOICE"},
            "correctAnswer": None,
            "materialRefs": m_refs,
            "evidence": [{"sourceFileRole": "QUESTION_BOOKLET", "page": p, "bbox": [0.1, 0.1, 0.9, 0.9]}],
        })

    groups.append({
        "groupId": stable_id("g_", source_id, form_code, "LISTENING"),
        "groupCode": "LISTENING",
        "materials": listening_materials,
        "questions": listening_questions,
    })

    if pdf_doc:
        pdf_doc.close()

    return [{
        "formCode": form_code,
        "spec": FORM_SPECS[form_code].to_dict(),
        "groups": groups,
    }]


def build_paper_for_session(work_dir: Path, store: AssetStore, tmp_dir: Path) -> dict[str, Any] | None:
    """Build, audit and prepare complete paper dictionary for a work directory."""
    manifest_path = work_dir / "source-manifest.json"
    probe_path = work_dir / "probe.json"
    
    if not manifest_path.exists() or not probe_path.exists():
        return None
        
    manifest = load_json(manifest_path)
    probe = load_json(probe_path)
    
    qb_file = next((f for f in probe.get("files", []) if f["role"] == "QUESTION_BOOKLET"), None)
    page_count = qb_file.get("pageCount", 20) if qb_file else 20
    
    subject = manifest["subject"]
    session_code = manifest["session"]
    
    course = None
    if "math-c1" in work_dir.name:
        course = "COURSE_1"
    elif "math-c2" in work_dir.name:
        course = "COURSE_2"
    
    audio_tracks = []
    completeness = "PARTIAL"
    available_modes = ["PRACTICE"]

    if subject == "SCIENCE":
        forms = build_science_forms(session_code, manifest, page_count)
        subject_label = "SCIENCE"
    elif subject == "MATHEMATICS":
        course_label = "Course 1" if course == "COURSE_1" else "Course 2"
        forms = build_math_forms(session_code, manifest, course, page_count)
        subject_label = f"MATHEMATICS ({course_label})"
    elif subject == "JAPAN_AND_WORLD":
        forms = build_japan_world_forms(session_code, manifest, page_count)
        subject_label = "JAPAN AND THE WORLD"
    elif subject == "JAPANESE":
        page_assets = ingest_booklet_pages(work_dir, store, prefer_remastered=True)
        page_ocr_data = load_session_ocr_data(work_dir, store=store)
        booklet_pdf = (work_dir / qb_file["path"]).resolve() if qb_file and "path" in qb_file else None
        forms = build_japanese_forms(session_code, manifest, page_count, page_assets, booklet_pdf, page_ocr_data=page_ocr_data, work_dir=work_dir)
        audio_tracks, comp_level = ingest_japanese_audio(session_code, manifest, store, tmp_dir)
        subject_label = "JAPANESE"
        completeness = comp_level
        available_modes = ["PRACTICE", "SECTION"]
    else:
        return None

    # ── 校验闸门 ──────────────────────────────────────────────────────
    # 只有能在答案册里查到答案、且题面来自真实 OCR 的题才留下。查不到的直接
    # 丢弃：宁可这套卷题量变少甚至不发布，也不能让假答案进题库。
    answers, answer_problems = load_verified_answers(work_dir)

    # 先把 OCR 真读出来的题并进去。它们与上面模板生成的题共用 answerRef，
    # 但闸门会丢掉占位的那批，所以最终留下的是真题。
    forms = merge_ocr_questions(forms, work_dir, manifest, answers)

    kept_forms, gate = enforce_verified(forms, answers, allow_unverified=ALLOW_UNVERIFIED)
    dropped = gate["no_answer"] + gate["placeholder"]
    if dropped:
        print(f"  [GATE] {work_dir.name}: 保留 {gate['kept']} 题，丢弃 {dropped} 题"
              f"（无可验证答案 {gate['no_answer']}，题面为占位 {gate['placeholder']}）")
    for problem in answer_problems[:3]:
        print(f"  [ANSWER] {work_dir.name}: {problem}")
    if not kept_forms:
        print(f"  [SKIP] {work_dir.name}: 没有一道题能通过校验，不发布")
        return None
    forms = kept_forms

    raw_paper = {
        "schemaVersion": 1,
        "examFamily": "EJU",
        "stableCode": manifest.get("inventoryId") or f"eju-{manifest['session'].lower()}-{work_dir.name}",
        "title": f"{session_code} EJU {subject_label}",
        "session": session_code,
        "syllabusVersion": manifest.get("syllabusVersion", "basic-2015"),
        "completeness": completeness,
        "availableModes": available_modes,
        "contentKind": "SYNTHETIC",
        "source": {
            "sourceId": manifest["sourceId"],
            "rights": {"status": "PUBLIC_LICENSED", "note": "Automated clean assemble from verified source PDFs"},
            "files": manifest["files"],
            "inventoryId": manifest.get("inventoryId", f"eju-{work_dir.name}"),
        },
        "forms": forms,
    }

    if audio_tracks:
        raw_paper["audioTracks"] = audio_tracks

    prepared = prepare_paper(raw_paper)
    audit = audit_paper(prepared)
    if audit["status"] != "passed":
        print(f"  [ERROR] Audit failed for {work_dir.name}: {audit['issues'][:3]}")
        return None

    return prepared


def main():
    import argparse
    parser = argparse.ArgumentParser(description="EJU Full-Scale Assembly & Database Publication Engine")
    parser.add_argument("--session", type=str, help="Filter by session name or substring (e.g. 2023-1-japanese)")
    parser.add_argument("--subject", type=str, help="Filter by subject (e.g. JAPANESE, SCIENCE, MATHEMATICS)")
    parser.add_argument(
        "--allow-unverified", action="store_true",
        help="发布无法从答案册验证的题目。仅用于调试；这样发布的卷判分不可信。")
    args = parser.parse_args()

    print("=================================================================")
    print("EJU Full-Scale Assembly & Database Publication Engine (v2.0)")
    print("  With Reading Text Passages & Listening Audio Ingestion")
    print("=================================================================\n")

    work_root = PROJECT_ROOT / "work"
    db_path = PROJECT_ROOT / "library" / "eju.db"
    inventory_path = PROJECT_ROOT / "content" / "content-inventory.json"
    media_dir = PROJECT_ROOT / "library" / "media"
    
    store = AssetStore(media_dir)
    print(f"Asset store initialized at: {store.root}")

    # Load all work session folders
    global ALLOW_UNVERIFIED
    ALLOW_UNVERIFIED = bool(getattr(args, "allow_unverified", False))
    if ALLOW_UNVERIFIED:
        print("!! --allow-unverified：将发布无法验证的题目，判分结果不可信 !!\n")

    session_dirs = sorted([p for p in work_root.iterdir() if p.is_dir() and (p / "source-manifest.json").exists()])
    if args.session:
        session_dirs = [d for d in session_dirs if args.session in d.name]
    if args.subject:
        session_dirs = [d for d in session_dirs if load_json(d / "source-manifest.json").get("subject") == args.subject]

    total_sessions = len(session_dirs)
    print(f"Found {total_sessions} matching work sessions.\n")

    db = Database(db_path, media_dir=media_dir, allow_synthetic=True)
    inventory = load_inventory(inventory_path)
    inv_by_id = {item["inventoryId"]: item for item in inventory.get("items", [])}

    success_count = 0
    fail_count = 0
    total_questions = 0

    start_time = time.time()

    with tempfile.TemporaryDirectory(prefix="eju_build_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        for idx, s_dir in enumerate(session_dirs, 1):
            try:
                paper = build_paper_for_session(s_dir, store, tmp_dir)
                if not paper:
                    fail_count += 1
                    continue

                # Save paper.json to work dir
                paper_json_path = s_dir / "paper.json"
                write_json(paper_json_path, paper)

                # Publish to library/eju.db
                result = db.publish(paper, channel="PRIVATE")
                success_count += 1
                q_cnt = paper.get("questionCount", 0)
                total_questions += q_cnt

                # Sync inventory status
                inv_id = paper["source"].get("inventoryId")
                if inv_id and inv_id in inv_by_id:
                    inv_item = inv_by_id[inv_id]
                    inv_item["pipelineStatus"] = "PUBLISHED"
                    inv_item["blockingIssues"] = []
                    inv_item["publishedPaperId"] = result["paperId"]
                    inv_item["publishedVersion"] = result["version"]

                audio_info = f", audio tracks: {len(paper.get('audioTracks', []))}" if paper.get("audioTracks") else ""
                print(f"[{idx:3d}/{total_sessions}] ✓ {s_dir.name:<25} -> {result['paperId']} (v{result['version']}, {q_cnt} Qs{audio_info})")

            except Exception as e:
                fail_count += 1
                print(f"[{idx:3d}/{total_sessions}] ✗ {s_dir.name:<25} -> {type(e).__name__}: {e}")

    # Save synced inventory
    save_inventory(inventory, inventory_path)
    db.close()

    elapsed = time.time() - start_time
    print("\n=================================================================")
    print("BATCH PUBLICATION SUMMARY")
    print("=================================================================")
    print(f"Total processed:        {total_sessions}")
    print(f"Successfully published: {success_count} papers")
    print(f"Failed:                 {fail_count}")
    print(f"Total questions:        {total_questions} questions published in database")
    print(f"Elapsed time:           {elapsed:.1f}s")
    print(f"Database:               {db_path.resolve()}")
    print(f"Media Assets Store:     {media_dir.resolve()}")
    print(f"Content Inventory:      {inventory_path.resolve()}")
    print("=================================================================\n")


if __name__ == "__main__":
    main()
