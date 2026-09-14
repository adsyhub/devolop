#!/usr/bin/env python3
"""Batch build video dictation courses from a YouTube playlist.

Usage Examples:
    # Process the first 10 videos (fast mode, no LLM required):
    python scripts/batch_youtube_playlist.py --limit 10

    # Process next 20 videos starting at index 10:
    python scripts/batch_youtube_playlist.py --offset 10 --limit 20

    # Process with DeepSeek AI translation and grammar breakdown:
    python scripts/batch_youtube_playlist.py --limit 5 --profile deepseek

    # Dry run to see planned videos:
    python scripts/batch_youtube_playlist.py --limit 10 --dry-run
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

import build_video_course
from bundle_io import safe_filename, write_json, load_json

DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLhoNlZaJqDLb7bQe3wYDCxx-ZqKRHl-nB"
DEFAULT_COURSES_DIR = PROJECT_DIR / "courses"
DEFAULT_WORK_DIR = PROJECT_DIR / "video-work"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 YouTube 播放列表批量制作视频精听课程。")
    parser.add_argument(
        "--playlist-url",
        default=DEFAULT_PLAYLIST_URL,
        help=f"YouTube 播放列表链接，默认：{DEFAULT_PLAYLIST_URL}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="最多制作几个视频课程（默认 20，设为 0 表示不限制全部制作）。",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="从播放列表的第几个视频开始制作（0-indexed，默认 0）。",
    )
    parser.add_argument(
        "--language",
        default="ja",
        help="课程语言代码（默认 ja）。",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="AI 富化模型 Profile（如 deepseek, openai, ollama）。不指定则使用快速字幕精听模式。",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="强制关闭 AI 富化（快速提取字幕与时间轴，无 API 调用）。",
    )
    parser.add_argument(
        "--prefix",
        default="tbs-news-",
        help="生成的课程目录名前缀，默认 'tbs-news-'。",
    )
    parser.add_argument(
        "--courses-dir",
        type=Path,
        default=DEFAULT_COURSES_DIR,
        help="课程输出根目录，默认 courses/。",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=DEFAULT_WORK_DIR,
        help="临时工作目录，默认 video-work/。",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="进度状态文件路径，用于断点续传（默认 video-work/playlist_batch_state.json）。",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="强制重新从 YouTube 获取播放列表元数据缓存。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="若课程已存在则强制覆盖重建。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅展示计划处理的视频列表，不实际抓取与生成。",
    )
    return parser.parse_args(argv)


def get_playlist_id(url: str) -> str:
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else "playlist"


def fetch_playlist_entries(url: str, work_dir: Path, refresh_cache: bool = False) -> list[dict[str, Any]]:
    playlist_id = get_playlist_id(url)
    cache_file = work_dir / f"playlist_cache_{playlist_id}.json"
    work_dir.mkdir(parents=True, exist_ok=True)

    if not refresh_cache and cache_file.is_file():
        try:
            print(f"正在从本地缓存读取播放列表: {cache_file.name} ...")
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(cached, list) and cached:
                print(f"成功读取缓存，共有 {len(cached)} 个视频。")
                return cached
        except Exception as exc:
            print(f"读取缓存失败 ({exc})，将重新从网络获取...")

    print(f"正在从 YouTube 解析播放列表信息: {url} ...")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "-J",
        "--no-warnings",
        "--",
        url,
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp 获取播放列表失败: {result.stderr or result.stdout}")

    data = json.loads(result.stdout)
    raw_entries = data.get("entries", [])
    entries: list[dict[str, Any]] = []

    for i, item in enumerate(raw_entries):
        vid = item.get("id")
        title = item.get("title")
        if not vid or not title or vid == "NA" or title in {"[Deleted video]", "[Private video]"}:
            continue
        entries.append({
            "playlistIndex": i + 1,
            "id": vid,
            "title": title,
            "duration": item.get("duration"),
            "url": f"https://www.youtube.com/watch?v={vid}",
        })

    print(f"成功解析播放列表，有效视频共 {len(entries)} 个。")
    write_json(cache_file, entries)
    return entries


def load_state(state_file: Path) -> dict[str, Any]:
    if state_file.is_file():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"updatedAt": "", "processed": {}}


def save_state(state_file: Path, state: dict[str, Any]) -> None:
    state["updatedAt"] = datetime.datetime.now().isoformat()
    write_json(state_file, state)


def make_course_name(prefix: str, index: int, video_id: str) -> str:
    return f"{prefix}{index:04d}-{video_id}"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    courses_dir = Path(args.courses_dir).expanduser().resolve()
    work_dir = Path(args.work_dir).expanduser().resolve()
    state_file = Path(args.state_file).expanduser().resolve() if args.state_file else work_dir / "playlist_batch_state.json"

    entries = fetch_playlist_entries(args.playlist_url, work_dir, refresh_cache=args.refresh_cache)
    if not entries:
        print("播放列表中没有可用的视频。")
        return 1

    start_idx = max(0, args.offset)
    end_idx = len(entries) if (args.limit is None or args.limit <= 0) else min(len(entries), start_idx + args.limit)
    selected = entries[start_idx:end_idx]

    enrich_mode = bool(args.profile and not args.no_enrich)

    print("=" * 65)
    print("YouTube 播放列表视频精听批量制作")
    print(f"播放列表    : {args.playlist_url}")
    print(f"视频总数    : {len(entries)}")
    print(f"本次处理区间: 第 {start_idx + 1} 至 {end_idx} 个视频（共 {len(selected)} 个）")
    print(f"语言代码    : {args.language}")
    profile_str = f"开启 ({args.profile})" if enrich_mode else "关闭 (快速字幕精听)"
    print(f"AI 富化模式 : {profile_str}")
    print(f"课程输出目录: {courses_dir}")
    print(f"状态存储文件: {state_file}")
    print("=" * 65)

    if args.dry_run:
        print("\n[DRY-RUN 模式] 待处理的视频列表：")
        for idx, entry in enumerate(selected, start=start_idx + 1):
            c_name = make_course_name(args.prefix, idx, entry["id"])
            dest = courses_dir / c_name
            exists = dest.is_dir() and (dest / "manifest.json").is_file()
            status_str = "[已存在]" if exists else "[待制作]"
            print(f"  {idx:04d}. {status_str} {entry['title']} ({entry['id']}) -> {c_name}")
        print("\nDry run 完成，未执行任何制作。")
        return 0

    state = load_state(state_file)
    processed_records = state.setdefault("processed", {})

    succeeded = 0
    skipped = 0
    failed = 0
    start_time = time.time()

    for idx, entry in enumerate(selected, start=start_idx + 1):
        vid = entry["id"]
        title = entry["title"]
        url = entry["url"]
        course_name = make_course_name(args.prefix, idx, vid)
        course_dest = courses_dir / course_name
        course_manifest = course_dest / "manifest.json"

        print(f"\n[{idx}/{len(entries)}] 处理视频: {title}")
        print(f"  URL : {url}")
        print(f"  目标: {course_name}")

        if course_manifest.is_file() and not args.force:
            print("  -> 课程已存在，跳过。使用 --force 可覆盖重建。")
            skipped += 1
            processed_records[vid] = {
                "status": "skipped",
                "reason": "already_exists",
                "courseName": course_name,
                "title": title,
                "updatedAt": datetime.datetime.now().isoformat(),
            }
            save_state(state_file, state)
            continue

        # Build video course command arguments
        build_argv = [
            "--url", url,
            "--name", course_name,
            "--language", args.language,
            "--courses-dir", str(courses_dir),
            "--work-dir", str(work_dir / course_name),
        ]
        if args.force:
            build_argv.append("--force")

        if enrich_mode:
            build_argv.extend(["--profile", args.profile])
        else:
            build_argv.append("--no-enrich")

        try:
            ret = build_video_course.main(build_argv)
            if ret != 0:
                raise RuntimeError(f"build_video_course 退出代码: {ret}")

            if not course_manifest.is_file():
                raise RuntimeError(f"构建未生成 manifest.json: {course_manifest}")

            manifest_data = json.loads(course_manifest.read_text(encoding="utf-8-sig"))
            sentences_count = len(manifest_data.get("sentences", []))
            print(f"  [OK] 制作成功！共 {sentences_count} 句。")
            succeeded += 1
            processed_records[vid] = {
                "status": "success",
                "courseName": course_name,
                "title": title,
                "sentenceCount": sentences_count,
                "updatedAt": datetime.datetime.now().isoformat(),
            }
        except SystemExit as exc:
            if exc.code == 0:
                succeeded += 1
                processed_records[vid] = {
                    "status": "success",
                    "courseName": course_name,
                    "title": title,
                    "updatedAt": datetime.datetime.now().isoformat(),
                }
            else:
                failed += 1
                err_msg = f"SystemExit({exc.code})"
                print(f"  [FAIL] 制作失败: {err_msg}")
                processed_records[vid] = {
                    "status": "failed",
                    "courseName": course_name,
                    "title": title,
                    "error": err_msg,
                    "updatedAt": datetime.datetime.now().isoformat(),
                }
        except Exception as exc:
            failed += 1
            print(f"  [FAIL] 制作失败: {exc}")
            processed_records[vid] = {
                "status": "failed",
                "courseName": course_name,
                "title": title,
                "error": str(exc),
                "updatedAt": datetime.datetime.now().isoformat(),
            }

        save_state(state_file, state)

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print("批量处理完成！")
    print(f"总耗时  : {elapsed:.1f} 秒")
    print(f"成功制作: {succeeded} 门")
    print(f"跳过已存: {skipped} 门")
    print(f"处理失败: {failed} 门")
    print("=" * 65)
    print("\n现在可以启动网页进行学习与验证：")
    print("  python start_dictation.py")
    print("在浏览器中打开 '🎧 精听' -> '视频精听' 即可看到新生成的课程！")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
