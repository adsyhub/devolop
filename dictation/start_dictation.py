"""Start the local dictation website and open it in the default browser."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from security_context import TOKEN_ENV_VAR, TOKEN_HEADER, generate_token  # noqa: E402


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_DIR / "src"
DEFAULT_MANIFEST = (
    PROJECT_DIR
    / "courses"
    / "2010-12-N2"
    / "manifest.json"
)
# DAT-001: one fixed origin, always. A browser scopes localStorage, IndexedDB,
# Cache Storage and the service worker registration to the *origin*, and the port
# is part of the origin — so the previous default of picking a free port at every
# launch handed the learner a brand-new, empty storage area each time, and left
# the real progress stranded under a port number nobody recorded. Those old
# origins cannot be enumerated or recovered by any tool; see BKP-001.
DEFAULT_PORT = 4173


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动听写网页，并用默认浏览器打开。")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="课程 manifest 文件路径（默认打开当前 N2 课程）。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"本地端口，默认 {DEFAULT_PORT}。学习进度按端口隔离，换端口等于换一份空进度。",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="只启动服务，不自动打开浏览器。",
    )
    parser.add_argument(
        "--allow-failed-course",
        action="store_true",
        help="开发预览：允许打开未通过质量审计的课程，页面会持续标注为不可发布。",
    )
    return parser.parse_args()


def port_is_available(port: int) -> bool:
    if not 1 <= port <= 65535:
        raise ValueError("端口必须在 1 到 65535 之间。")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def describe_occupied_port(port: int) -> str:
    """Report what is already listening, without trusting or writing to it.

    Silently sliding to a different port is what created the stranded-progress
    problem, so a busy port is now a hard stop. We probe the health endpoint only
    to help the user recognise their own already-running copy — a response here
    proves nothing about identity, so the message never claims it is safe.
    """
    try:
        request = urllib.request.Request(f"http://127.0.0.1:{port}/api/health")
        with urllib.request.urlopen(request, timeout=1.5) as response:
            body = response.read(200).decode("utf-8", "replace").strip()
        return f"该端口已有服务在响应 /api/health：HTTP {response.status} {body}"
    except urllib.error.HTTPError as exc:
        return f"该端口有服务，但 /api/health 返回 HTTP {exc.code}（可能不是本项目）。"
    except (urllib.error.URLError, OSError, TimeoutError):
        return "该端口被占用，但没有响应 /api/health（很可能是别的程序）。"


def wait_until_ready(process: subprocess.Popen[bytes], url: str, token: str, timeout: float = 15) -> None:
    """Wait for the server, then prove the token handshake actually works.

    Readiness now means more than "the socket answers". A server whose token
    pipeline is broken would still pass a bare health probe and then fail every
    single learning-data request once the browser was already open, which is a
    confusing way to find out. Checking a token-protected endpoint here turns
    that into a clean startup failure.
    """
    deadline = time.monotonic() + timeout
    health_url = f"{url}api/health"
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(f"听写服务启动失败，退出代码：{exit_code}")
        try:
            request = urllib.request.Request(health_url, headers={TOKEN_HEADER: token})
            with urllib.request.urlopen(request, timeout=0.5) as response:
                if response.status == 200:
                    break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    else:
        raise TimeoutError("等待听写服务启动超时。")

    probe = urllib.request.Request(f"{url}api/vocab", headers={TOKEN_HEADER: token})
    try:
        with urllib.request.urlopen(probe, timeout=3) as response:
            if response.status != 200:
                raise RuntimeError(f"学习数据接口返回 HTTP {response.status}。")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"会话令牌未被服务接受（HTTP {exc.code}）。启动器与服务的令牌不一致，已中止。"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"无法验证学习数据接口：{exc}") from exc


def verify_course_assets(url: str) -> None:
    """Verify the same manifest and audio requests that the web player will make."""
    try:
        with urllib.request.urlopen(f"{url}manifest.json", timeout=5) as response:
            manifest = json.load(response)
        audio_name = manifest.get("audio")
        if not isinstance(audio_name, str) or not audio_name:
            raise RuntimeError("课程文件没有指定音频。")

        request = urllib.request.Request(
            f"{url}{urllib.parse.quote(audio_name)}",
            headers={"Range": "bytes=0-65535"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            content_type = response.headers.get_content_type()
            first_chunk = response.read(64 * 1024)
            if response.status not in {200, 206} or not content_type.startswith("audio/"):
                raise RuntimeError(f"音频响应异常：HTTP {response.status}，{content_type}")
            if len(first_chunk) < 1024:
                raise RuntimeError("音频响应内容不完整。")
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        raise RuntimeError(f"课程资源检查失败：{exc}") from exc


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> int:
    args = parse_args()
    manifest = args.manifest.expanduser()
    if not manifest.is_absolute():
        manifest = (Path.cwd() / manifest).resolve()
    if manifest.is_dir():
        from studio_artifacts import resolve_course_manifest_path

        manifest = resolve_course_manifest_path(manifest)
    elif manifest.is_file() and manifest.name == "manifest.json":
        from studio_artifacts import resolve_course_manifest_path

        manifest = resolve_course_manifest_path(manifest.parent)
    if not manifest or not manifest.is_file():
        print(f"找不到课程文件：{manifest}", file=sys.stderr)
        return 1

    port = args.port
    try:
        available = port_is_available(port)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not available:
        print(f"端口 {port} 已被占用，已停止启动。", file=sys.stderr)
        print(f"  {describe_occupied_port(port)}", file=sys.stderr)
        print(
            "  没有自动换端口：学习进度按 origin（含端口）隔离，换端口会打开一份空进度，\n"
            "  而原来的进度留在旧端口下、无法自动找回。\n"
            "  请先关闭占用该端口的程序，或用 --port 显式指定另一个端口。",
            file=sys.stderr,
        )
        return 1

    # SEC-001: the token is minted here and handed to the child through an
    # inherited environment variable, which the server pops on startup. It never
    # goes on the command line (visible to every process on the machine via the
    # process table) and never into a URL (which would land in browser history
    # and any access log).
    token = generate_token()
    environment = {**os.environ, TOKEN_ENV_VAR: token}

    url = f"http://127.0.0.1:{port}/"
    command = [
        sys.executable,
        "-u",
        str(SOURCE_DIR / "serve_course.py"),
        str(manifest),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    if args.allow_failed_course:
        command.append("--allow-failed-course")
    process = subprocess.Popen(command, cwd=PROJECT_DIR, env=environment)

    try:
        wait_until_ready(process, url, token)
        verify_course_assets(url)
        print(f"听写网页已启动：{url}")
        if not args.no_browser:
            if not webbrowser.open(url, new=2):
                print("未能自动打开浏览器，请手动复制上面的地址。")
        print("保持此窗口运行；学习结束后按 Ctrl+C 关闭服务。")
        return process.wait()
    except KeyboardInterrupt:
        print("\n正在关闭听写服务……")
        return 0
    except (RuntimeError, TimeoutError) as exc:
        print(exc, file=sys.stderr)
        return 1
    finally:
        stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
