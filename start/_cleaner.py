#!/usr/bin/env python3
"""通用旧进程清理与端口释放工具。

供 /workspace/Develop/start 下的所有启动脚本调用。
在拉起新服务前，先优雅终止并清理旧的进程、worker 以及占用对应端口的遗留进程，
并等待端口彻底释放，避免 "Address already in use" 或后台残留僵死任务。
"""

from __future__ import annotations

import argparse
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Set

# 保护清单：绝对不能误杀的关键系统与守护进程关键词
PROTECTED_PATTERNS = (
    "vscode-server",
    "antigravity",
    "agy",
    "sshd",
    "_cleaner.py",
)


def extract_port(argv: list[str], default_port: int) -> int:
    """从命令行参数中提取 --port 的值，若未指定则返回 default_port。"""
    for idx, arg in enumerate(argv):
        if arg == "--port" and idx + 1 < len(argv):
            try:
                return int(argv[idx + 1])
            except ValueError:
                pass
        elif arg.startswith("--port="):
            try:
                return int(arg.split("=", 1)[1])
            except ValueError:
                pass
    return default_port


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """检查指定端口是否处于监听/连接状态。"""
    if port <= 0:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def get_process_cmdline(pid: int) -> str:
    """获取进程的命令行内容。"""
    try:
        cmdline_file = Path(f"/proc/{pid}/cmdline")
        if cmdline_file.exists():
            return cmdline_file.read_bytes().decode("utf-8", errors="replace").replace("\x00", " ")
    except Exception:
        pass
    return ""


def is_safe_to_kill(pid: int) -> bool:
    """检查给定的 PID 是否安全可杀（防止误杀系统守护进程、VSCode、AI Agent 等）。"""
    if pid <= 1:
        return False
    if pid in (os.getpid(), os.getppid()):
        return False

    cmdline = get_process_cmdline(pid)
    if not cmdline:
        return False

    for protected in PROTECTED_PATTERNS:
        if protected in cmdline:
            return False

    return True


def find_pids_by_port(port: int) -> Set[int]:
    """通过 netstat 查找占用指定端口的进程 PID。"""
    pids: Set[int] = set()
    if port <= 0:
        return pids

    try:
        out = subprocess.check_output(["netstat", "-tlpn"], stderr=subprocess.DEVNULL, text=True)
        pattern = re.compile(rf":{port}\b.*?\s+(\d+)/")
        for line in out.splitlines():
            match = pattern.search(line)
            if match:
                pid = int(match.group(1))
                if is_safe_to_kill(pid):
                    pids.add(pid)
    except Exception:
        pass

    return pids


def find_pids_by_pattern(pattern: str) -> Set[int]:
    """通过 pgrep 查找匹配命令行模式的进程 PID。"""
    pids: Set[int] = set()
    if not pattern:
        return pids

    try:
        out = subprocess.check_output(["pgrep", "-f", pattern], stderr=subprocess.DEVNULL, text=True)
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if is_safe_to_kill(pid):
                    pids.add(pid)
    except subprocess.CalledProcessError:
        pass
    except Exception:
        pass

    return pids


def terminate_pids(pids: Iterable[int], sig: int = signal.SIGTERM) -> None:
    """向指定 PID 集合发送信号。"""
    for pid in pids:
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def is_pid_alive(pid: int) -> bool:
    """检查进程是否存活。"""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def clean_processes_and_ports(
    patterns: list[str] | None = None,
    ports: list[int] | int | None = None,
    wait_timeout: float = 3.0,
    verbose: bool = True,
) -> None:
    """核心清理函数：查找旧进程及端口占用者，先 SIGTERM 再 SIGKILL，并等待端口释放。"""
    patterns = patterns or []
    target_ports: list[int] = []
    if isinstance(ports, int):
        target_ports = [ports]
    elif ports:
        target_ports = list(ports)

    # 1. 收集目标 PID
    target_pids: Set[int] = set()
    for pat in patterns:
        target_pids.update(find_pids_by_pattern(pat))
    for p in target_ports:
        target_pids.update(find_pids_by_port(p))

    # 过滤保护进程
    target_pids = {pid for pid in target_pids if is_safe_to_kill(pid)}

    if target_pids:
        if verbose:
            pid_details = []
            for pid in sorted(target_pids):
                cmd = get_process_cmdline(pid)[:60].strip()
                pid_details.append(f"{pid} ({cmd})")
            print(f"[clean] 发现旧进程: {', '.join(pid_details)}，正在终止...", flush=True)

        # 先发 SIGTERM 优雅退出
        terminate_pids(target_pids, signal.SIGTERM)

        # 检查是否退出
        time.sleep(0.4)
        survived = {pid for pid in target_pids if is_pid_alive(pid)}
        if survived:
            if verbose:
                print(f"[clean] 强制终止残留旧进程: {sorted(survived)}", flush=True)
            terminate_pids(survived, signal.SIGKILL)
            time.sleep(0.2)

    # 2. 检查并确保端口完全释放
    ports_to_check = [p for p in target_ports if p > 0]
    if ports_to_check:
        deadline = time.time() + wait_timeout
        while time.time() < deadline:
            still_busy = [p for p in ports_to_check if is_port_in_use(p)]
            if not still_busy:
                break
            # 若端口仍被占用，再次检索并 kill 占用者
            for p in still_busy:
                pids = find_pids_by_port(p)
                if pids:
                    terminate_pids(pids, signal.SIGKILL)
            time.sleep(0.2)

        if verbose:
            busy_ports = [p for p in ports_to_check if is_port_in_use(p)]
            if busy_ports:
                print(f"[clean] 警告: 端口 {busy_ports} 仍在占用中", file=sys.stderr, flush=True)
            elif target_pids:
                print(f"[clean] 旧进程已清理完毕，端口就绪。", flush=True)


def parse_cli_args(argv: list[str]) -> tuple[list[str], list[int]]:
    """从 CLI 参数中智能解析 pattern 和 port。"""
    patterns: list[str] = []
    ports: list[int] = []

    idx = 0
    while idx < len(argv):
        arg = argv[idx]
        if arg in ("--pattern", "-p"):
            if idx + 1 < len(argv):
                patterns.append(argv[idx + 1])
                idx += 2
                continue
        elif arg.startswith("--pattern="):
            patterns.append(arg.split("=", 1)[1])
        elif arg == "--port":
            if idx + 1 < len(argv):
                try:
                    ports.append(int(argv[idx + 1]))
                except ValueError:
                    pass
                idx += 2
                continue
        elif arg.startswith("--port="):
            try:
                ports.append(int(arg.split("=", 1)[1]))
            except ValueError:
                pass
        idx += 1

    return patterns, ports


def main() -> int:
    argv = sys.argv[1:]
    patterns, ports = parse_cli_args(argv)
    clean_processes_and_ports(patterns=patterns, ports=ports, verbose=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

