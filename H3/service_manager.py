#!/usr/bin/env python3
"""MiniMax H3 服务控制器 (Service Manager)
纯 Python 标准库实现，零第三方依赖（无需安装 psutil 等），可直接在任何 Python 环境下运行。

功能：
- 统一管理 MiniMax H3 计算引擎 (ComfyUI 8188 端口)
- 统一管理 MiniMax H3 Video Studio 前端工作台 (7860 端口)
- 自动绑定系统底层 Conda 环境 (/opt/conda/bin/python) 确保 PyTorch/CUDA 正常加载

使用示例：
    # 命令行操作：
    python service_manager.py start           # 启动所有服务 (后端 + 前端)
    python service_manager.py stop            # 停止所有服务
    python service_manager.py restart         # 重启所有服务
    python service_manager.py status          # 查看运行状态与显存占用

    # Python 代码导入：
    from service_manager import ServiceManager
    mgr = ServiceManager()
    mgr.start_all()
    mgr.print_status()
    mgr.stop_all()
"""

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# 基础目录与执行环境路径
SCRIPT_DIR = Path(__file__).resolve().parent
COMFYUI_DIR = SCRIPT_DIR / "ComfyUI"

# 优先使用配置好完整 PyTorch / CUDA 的 Conda Python 环境
if Path("/opt/conda/bin/python").exists():
    PYTHON_BIN = "/opt/conda/bin/python"
else:
    PYTHON_BIN = sys.executable

OUTPUT_DIR = Path("/data/storage/outputs/minimax-h3")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BACKEND_PORT = 8188
DEFAULT_WORKBENCH_PORT = 7860
DEFAULT_GPU_ID = "3"  # 默认使用单卡 80GB 的 NVIDIA H100 PCIe


class ServiceManager:
    """MiniMax H3 服务综合管理器 (纯标准库实现)"""

    def __init__(self, base_dir: Path = SCRIPT_DIR):
        self.base_dir = base_dir
        self.comfy_dir = base_dir / "ComfyUI"
        self.backend_pid_file = base_dir / "comfyui.pid"
        self.workbench_pid_file = base_dir / "workbench.pid"
        self.backend_log = base_dir / "comfyui.log"
        self.workbench_log = base_dir / "workbench.log"

    # ==================== 纯标准库系统工具 ====================

    @staticmethod
    def is_port_open(host: str = "127.0.0.1", port: int = 8188, timeout: float = 1.0) -> bool:
        """检测指定端口是否处于监听状态"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0

    @staticmethod
    def is_pid_alive(pid: int) -> bool:
        """纯标准库检查进程是否存在且处于存活状态"""
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _read_pid(self, pid_file: Path) -> Optional[int]:
        """读取并验证 PID 文件"""
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                if self.is_pid_alive(pid):
                    return pid
            except Exception:
                pass
        return None

    def _write_pid(self, pid_file: Path, pid: int):
        """写入 PID 文件"""
        pid_file.write_text(str(pid))

    def _remove_pid(self, pid_file: Path):
        """删除 PID 文件"""
        if pid_file.exists():
            try:
                pid_file.unlink()
            except Exception:
                pass

    @staticmethod
    def _find_pids_by_cmd(pattern: str) -> List[int]:
        """使用标准 Linux 工具查找匹配模式的进程 PID"""
        pids = []
        try:
            out = subprocess.check_output(["pgrep", "-f", pattern], encoding="utf-8").strip()
            current_pid = os.getpid()
            for line in out.splitlines():
                line = line.strip()
                if line.isdigit():
                    p = int(line)
                    if p != current_pid:
                        pids.append(p)
        except Exception:
            pass
        return pids

    def _terminate_pid(self, pid: int, timeout: int = 10) -> bool:
        """安全终止进程 (SIGTERM -> SIGKILL)"""
        if not self.is_pid_alive(pid):
            return True

        # 1. 优先发送 SIGTERM 优雅退出
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return True

        # 2. 等待进程退出
        start_t = time.time()
        while time.time() - start_t < timeout:
            if not self.is_pid_alive(pid):
                return True
            time.sleep(0.5)

        # 3. 超时强制发送 SIGKILL
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

        time.sleep(0.5)
        return not self.is_pid_alive(pid)

    # ==================== GPU 显卡管理与切换 ====================

    def get_active_gpu(self) -> Dict:
        """获取当前配置绑定的 GPU"""
        gpu_file = self.base_dir / "current_gpu.json"
        if gpu_file.exists():
            try:
                import json
                return json.loads(gpu_file.read_text())
            except Exception:
                pass
        return {
            "gpu_id": "0",
            "gpu_uuid": "GPU-16d4523d-8777-6165-a8f1-c1a10fac67e1",
            "gpu_name": "NVIDIA H100 PCIe",
            "vram_total_gb": 80,
        }

    def get_gpu_list(self) -> List[Dict]:
        """获取系统全部可用 GPU 详细规格与实时负载"""
        gpus = []
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=index,name,uuid,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu",
                "--format=csv,noheader,nounits",
            ]
            out = subprocess.check_output(cmd, encoding="utf-8").strip()
            active_info = self.get_active_gpu()
            active_id = str(active_info.get("gpu_id", "0"))
            active_uuid = str(active_info.get("gpu_uuid", ""))

            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 8:
                    idx, name, uuid, total_mb, used_mb, free_mb, temp, util = parts[:8]
                    is_h100 = "H100" in name
                    is_active = (idx == active_id) or (uuid == active_uuid)
                    gpus.append(
                        {
                            "index": int(idx),
                            "id": idx,
                            "name": name,
                            "uuid": uuid,
                            "total_gb": round(float(total_mb) / 1024, 1),
                            "used_gb": round(float(used_mb) / 1024, 1),
                            "free_gb": round(float(free_mb) / 1024, 1),
                            "temp_c": int(temp),
                            "util_pct": int(util),
                            "is_h100": is_h100,
                            "is_active": is_active,
                            "description": "80GB 全显存极速模式 (推荐)" if is_h100 else "48GB 动态内存拓展模式",
                        }
                    )
        except Exception:
            pass
        return gpus

    def switch_gpu(self, target_gpu: str) -> Dict:
        """热切换 MiniMax H3 算力绑定的显卡"""
        import json

        gpus = self.get_gpu_list()
        matched = None
        target_str = str(target_gpu).strip()
        # 1. 优先根据数字编号或 UUID 精确匹配
        for g in gpus:
            if str(g["index"]) == target_str or g["uuid"].lower() == target_str.lower():
                matched = g
                break
        # 2. 其次根据名称模糊匹配 (长度至少3位，避免数字干扰)
        if not matched and len(target_str) >= 3:
            for g in gpus:
                if target_str.lower() in g["name"].lower():
                    matched = g
                    break

        if not matched:
            return {"success": False, "message": f"未找到指定的显卡: {target_gpu}"}

        # 保存新配置
        active_config = {
            "gpu_id": str(matched["index"]),
            "gpu_uuid": matched["uuid"],
            "gpu_name": matched["name"],
            "vram_total_gb": matched["total_gb"],
        }
        gpu_file = self.base_dir / "current_gpu.json"
        gpu_file.write_text(json.dumps(active_config, indent=2))

        print(f"正在无缝切换 MiniMax H3 算力引擎至 GPU {matched['index']} ({matched['name']})...")
        self.stop_backend()
        time.sleep(2)
        ok = self.start_backend(gpu_id=matched["uuid"], wait=True)

        return {
            "success": ok,
            "message": f"已成功切换算力引擎至 GPU {matched['index']} ({matched['name']})",
            "gpu": active_config,
        }

    # ==================== 后端 (ComfyUI) 管理 ====================

    def start_backend(
        self,
        gpu_id: Optional[str] = None,
        port: int = DEFAULT_BACKEND_PORT,
        host: str = "0.0.0.0",
        wait: bool = True,
        timeout: int = 40,
    ) -> bool:
        """启动 MiniMax H3 ComfyUI 后端引擎"""
        pid = self._read_pid(self.backend_pid_file)
        if pid or self.is_port_open("127.0.0.1", port):
            print(f"[提示] 后端服务已在运行 (PID: {pid or '未知'}, 端口: {port})")
            return True

        # 如果未显式传 gpu_id，则读取当前配置的 GPU
        if gpu_id is None:
            active_info = self.get_active_gpu()
            gpu_id = active_info.get("gpu_uuid", "GPU-16d4523d-8777-6165-a8f1-c1a10fac67e1")

        print("==================================================")
        print(f"正在启动 MiniMax H3 后端计算引擎 (ComfyUI)...")
        print(f"- 绑定 GPU: CUDA_VISIBLE_DEVICES={gpu_id}")
        print(f"- 运行环境: {PYTHON_BIN}")
        print(f"- 监听地址: http://{host}:{port}")
        print(f"- 输出目录: {OUTPUT_DIR}")
        print(f"- 日志文件: {self.backend_log}")
        print("==================================================")

        env = os.environ.copy()
        env["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

        cmd = [
            PYTHON_BIN,
            "main.py",
            "--listen",
            host,
            "--port",
            str(port),
            "--output-directory",
            str(OUTPUT_DIR),
        ]

        log_f = open(self.backend_log, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            cwd=str(self.comfy_dir),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # 独立会话组，关闭终端不被杀死
        )

        self._write_pid(self.backend_pid_file, proc.pid)

        if not wait:
            print(f"[成功] 后端进程已启动，PID: {proc.pid}")
            return True

        print(f"等待引擎就绪 (最多等待 {timeout} 秒)...")
        start_t = time.time()
        while time.time() - start_t < timeout:
            if self.is_port_open("127.0.0.1", port):
                print(f"[成功] 后端引擎已完全就绪！PID: {proc.pid}，地址: http://{host}:{port}")
                return True
            if proc.poll() is not None:
                print(f"[错误] 后端启动异常退出，退出码: {proc.returncode}。请查看日志: {self.backend_log}")
                self._remove_pid(self.backend_pid_file)
                return False
            time.sleep(1)

        print(f"[警告] 等待引擎就绪超时，进程仍在后台加载中 (PID: {proc.pid})。")
        return False

    def stop_backend(self) -> bool:
        """停止 MiniMax H3 ComfyUI 后端引擎"""
        pid = self._read_pid(self.backend_pid_file)
        stopped = False

        if pid:
            print(f"正在停止后端服务 (PID: {pid})...")
            if self._terminate_pid(pid):
                stopped = True

        # 清理可能残留的 main.py 进程
        candidates = (
            self._find_pids_by_cmd("main.py --listen")
            + self._find_pids_by_cmd("main.py --port")
            + self._find_pids_by_cmd("ComfyUI/main.py")
        )
        leftovers = list(set(candidates))
        for p in leftovers:
            print(f"清理残留后端进程 (PID: {p})...")
            self._terminate_pid(p)
            stopped = True

        self._remove_pid(self.backend_pid_file)

        # 等待端口彻底释放
        start_wait = time.time()
        while time.time() - start_wait < 10:
            if not self.is_port_open("127.0.0.1", DEFAULT_BACKEND_PORT):
                break
            time.sleep(0.5)

        if stopped:
            print("[成功] 后端服务已停止并释放端口。")
        else:
            print("[提示] 未发现运行中的后端服务。")
        return True

    # ==================== 网页浏览器拉起工具 ====================

    @staticmethod
    def open_browser(port: int = DEFAULT_WORKBENCH_PORT, host: str = "localhost"):
        """自动在用户的本地电脑浏览器中拉起前端操作页面"""
        url = f"http://{host}:{port}"
        print(f"👉 正在自动为您在浏览器中打开: {url} ...")

        opened = False
        # 1. 尝试 Python 标准库 webbrowser (在 VS Code Remote 下会自动转发并打开本地浏览器)
        try:
            import webbrowser
            opened = webbrowser.open(url)
        except Exception:
            pass

        # 2. 尝试系统环境变量 $BROWSER (VS Code 专用浏览器辅助脚本)
        if not opened:
            browser_env = os.environ.get("BROWSER")
            if browser_env and os.path.exists(browser_env):
                try:
                    subprocess.Popen([browser_env, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    opened = True
                except Exception:
                    pass

        # 3. 尝试 xdg-open
        if not opened:
            try:
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                opened = True
            except Exception:
                pass

        return opened

    # ==================== 前端 (Video Studio) 管理 ====================

    def start_workbench(
        self,
        port: int = DEFAULT_WORKBENCH_PORT,
        host: str = "0.0.0.0",
        wait: bool = True,
        timeout: int = 20,
        open_browser: bool = True,
    ) -> bool:
        """启动 MiniMax H3 Video Studio 前端工作台"""
        # 启动前端前，先确保后端处于运行中
        if not self.is_port_open("127.0.0.1", DEFAULT_BACKEND_PORT):
            print("[提示] 检测到后端计算引擎尚未运行，正在自动拉起后端...")
            self.start_backend(wait=True)

        pid = self._read_pid(self.workbench_pid_file)
        if pid or self.is_port_open("127.0.0.1", port):
            print(f"[提示] 前端工作台已在运行中 (PID: {pid or '未知'}, 端口: {port})")
            if open_browser:
                self.open_browser(port=port)
            return True

        print("==================================================")
        print(f"正在启动 MiniMax H3 Video Studio 前端工作台...")
        print(f"- 运行环境: {PYTHON_BIN}")
        print(f"- 访问地址: http://{host}:{port}")
        print(f"- 日志文件: {self.workbench_log}")
        print("==================================================")

        cmd = [PYTHON_BIN, "web_app.py"]

        log_f = open(self.workbench_log, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            cwd=str(self.base_dir),
            stdout=log_f,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        self._write_pid(self.workbench_pid_file, proc.pid)

        if not wait:
            print(f"[成功] 前端进程已启动，PID: {proc.pid}")
            if open_browser:
                self.open_browser(port=port)
            return True

        print(f"等待前端工作台就绪 (最多等待 {timeout} 秒)...")
        start_t = time.time()
        while time.time() - start_t < timeout:
            if self.is_port_open("127.0.0.1", port):
                print(f"[成功] 前端工作台启动就绪！PID: {proc.pid}")
                print(f"👉 浏览器访问: http://{host}:{port}")
                if open_browser:
                    self.open_browser(port=port)
                return True
            if proc.poll() is not None:
                print(f"[错误] 前端启动异常退出，退出码: {proc.returncode}。请查看日志: {self.workbench_log}")
                self._remove_pid(self.workbench_pid_file)
                return False
            time.sleep(1)

        print(f"[警告] 等待前端就绪超时，请检查日志: {self.workbench_log}")
        return False

    def stop_workbench(self) -> bool:
        """停止 MiniMax H3 Video Studio 前端工作台"""
        pid = self._read_pid(self.workbench_pid_file)
        stopped = False

        if pid:
            print(f"正在停止前端工作台 (PID: {pid})...")
            if self._terminate_pid(pid):
                stopped = True

        leftovers = self._find_pids_by_cmd("web_app.py")
        for p in leftovers:
            print(f"清理残留前端进程 (PID: {p})...")
            self._terminate_pid(p)
            stopped = True

        self._remove_pid(self.workbench_pid_file)
        if stopped:
            print("[成功] 前端工作台已停止。")
        else:
            print("[提示] 未发现运行中的前端工作台。")
        return True

    # ==================== 统一总控方法 ====================

    def start_all(self, gpu_id: str = DEFAULT_GPU_ID, open_browser: bool = True) -> bool:
        """一键启动所有服务 (后端引擎 + 前端工作台并拉起浏览器)"""
        b_ok = self.start_backend(gpu_id=gpu_id, wait=True)
        w_ok = self.start_workbench(wait=True, open_browser=open_browser)
        return b_ok and w_ok

    def stop_all(self) -> bool:
        """一键停止所有服务"""
        print("正在停止所有 MiniMax H3 服务...")
        self.stop_workbench()
        self.stop_backend()
        print("[完成] 所有服务已安全退出。")
        return True

    def restart_all(self, gpu_id: str = DEFAULT_GPU_ID) -> bool:
        """一键重启所有服务"""
        print("正在重启所有 MiniMax H3 服务...")
        self.stop_all()
        time.sleep(2)
        return self.start_all(gpu_id=gpu_id)

    def get_status(self) -> Dict:
        """获取各服务运行状态与硬件详情 (纯标准库)"""
        b_pid = self._read_pid(self.backend_pid_file)
        b_alive = self.is_port_open("127.0.0.1", DEFAULT_BACKEND_PORT)

        w_pid = self._read_pid(self.workbench_pid_file)
        w_alive = self.is_port_open("127.0.0.1", DEFAULT_WORKBENCH_PORT)

        # 硬件 GPU 显存与温度
        gpu_info = []
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,temperature.gpu",
                "--format=csv,noheader,nounits",
            ]
            out = subprocess.check_output(cmd, encoding="utf-8").strip()
            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpu_info.append(
                        {
                            "index": int(parts[0]),
                            "name": parts[1],
                            "total_gb": round(float(parts[2]) / 1024, 1),
                            "used_gb": round(float(parts[3]) / 1024, 1),
                            "free_gb": round(float(parts[4]) / 1024, 1),
                            "temp": parts[5],
                        }
                    )
        except Exception:
            pass

        # 存储大盘信息
        try:
            st = shutil.disk_usage("/data/storage")
            disk_free_gb = round(st.free / (1024**3), 1)
            disk_total_gb = round(st.total / (1024**3), 1)
        except Exception:
            disk_free_gb, disk_total_gb = 0, 0

        return {
            "backend": {
                "name": "ComfyUI 计算引擎",
                "running": b_alive,
                "pid": b_pid,
                "port": DEFAULT_BACKEND_PORT,
                "url": f"http://0.0.0.0:{DEFAULT_BACKEND_PORT}",
            },
            "workbench": {
                "name": "Video Studio 前端工作台",
                "running": w_alive,
                "pid": w_pid,
                "port": DEFAULT_WORKBENCH_PORT,
                "url": f"http://0.0.0.0:{DEFAULT_WORKBENCH_PORT}",
            },
            "gpus": gpu_info,
            "storage_free_gb": disk_free_gb,
            "storage_total_gb": disk_total_gb,
        }

    def print_status(self):
        """格式化打印服务运行状态卡片"""
        st = self.get_status()
        b = st["backend"]
        w = st["workbench"]

        print("\n" + "=" * 60)
        print("           MiniMax H3 服务运行状态看板")
        print("=" * 60)

        def status_str(running):
            return "\033[92m● 运行中 (ONLINE)\033[0m" if running else "\033[91m○ 已停止 (OFFLINE)\033[0m"

        print(f"【前端工作台】 : {status_str(w['running'])}")
        print(f"  - 访问地址   : {w['url']}")
        print(f"  - 进程 PID   : {w['pid'] or '未记录'}")

        print(f"\n【后端计算引擎】: {status_str(b['running'])}")
        print(f"  - 接口地址   : {b['url']}")
        print(f"  - 进程 PID   : {b['pid'] or '未记录'}")

        active_gpu = self.get_active_gpu()
        print(f"\n【硬件与存储概况】 (当前绑定: GPU {active_gpu.get('gpu_id', '0')} - {active_gpu.get('gpu_name', 'H100')}):")
        print(f"  - 存储大盘   : /data/storage (剩余: {st['storage_free_gb']} GB / 共 {st['storage_total_gb']} GB)")
        for g in self.get_gpu_list():
            active_mark = " \033[92m[★ 当前使用中]\033[0m" if g["is_active"] else ""
            desc = f" ({g['description']})" if g["is_h100"] else ""
            print(f"  - GPU {g['index']} ({g['name']}){desc}{active_mark}: 显存 {g['used_gb']}G / {g['total_gb']}G ({g['temp_c']}°C)")

        print("=" * 60 + "\n")


# ==================== CLI 命令行入口 ====================


def main():
    parser = argparse.ArgumentParser(description="MiniMax H3 服务综合控制工具 (零第三方依赖)")
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status", "gpus", "switch-gpu"],
        help="执行操作: start(启动), stop(停止), restart(重启), status(状态查看), gpus(显卡列表), switch-gpu(切换显卡)",
    )
    parser.add_argument(
        "--service",
        choices=["all", "backend", "workbench"],
        default="all",
        help="目标服务 (默认: all，全部服务)",
    )
    parser.add_argument(
        "--gpu",
        default="0",
        help="指定计算使用的 GPU 编号或 UUID (例如: 0, 1, 2, 3，默认 0 为 H100)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="启动后不自动在本地浏览器中打开页面",
    )

    args = parser.parse_args()
    mgr = ServiceManager()
    open_browser = not args.no_browser

    if args.action == "gpus":
        print("\n" + "=" * 65)
        print("                 MiniMax H3 可用显卡列表")
        print("=" * 65)
        gpus = mgr.get_gpu_list()
        for g in gpus:
            active_tag = " \033[92m[★ 当前绑定]\033[0m" if g["is_active"] else " [点击可切换]"
            print(f"● GPU {g['index']}: {g['name']}{active_tag}")
            print(f"    显存: {g['used_gb']} GB / {g['total_gb']} GB | 温度: {g['temp_c']}°C | 负载: {g['util_pct']}%")
            print(f"    模式: {g['description']}")
            print(f"    UUID: {g['uuid']}\n")
        print("提示: 可执行 'python service_manager.py switch-gpu --gpu <编号>' 一键切换")
        print("=" * 65 + "\n")
        return

    if args.action == "switch-gpu":
        res = mgr.switch_gpu(args.gpu)
        if res.get("success"):
            print(f"\n\033[92m✔ {res.get('message')}\033[0m\n")
        else:
            print(f"\n\033[91m✘ {res.get('message')}\033[0m\n")
        return

    if args.action == "status":
        mgr.print_status()
        return

    if args.action == "start":
        if args.service == "backend":
            mgr.start_backend(gpu_id=args.gpu)
        elif args.service == "workbench":
            mgr.start_workbench(open_browser=open_browser)
        else:
            mgr.start_all(gpu_id=args.gpu, open_browser=open_browser)

    elif args.action == "stop":
        if args.service == "backend":
            mgr.stop_backend()
        elif args.service == "workbench":
            mgr.stop_workbench()
        else:
            mgr.stop_all()

    elif args.action == "restart":
        if args.service == "backend":
            mgr.stop_backend()
            time.sleep(1)
            mgr.start_backend(gpu_id=args.gpu)
        elif args.service == "workbench":
            mgr.stop_workbench()
            time.sleep(1)
            mgr.start_workbench(open_browser=open_browser)
        else:
            mgr.stop_all()
            time.sleep(2)
            mgr.start_all(gpu_id=args.gpu, open_browser=open_browser)


if __name__ == "__main__":
    main()
