#!/usr/bin/env python3
"""MiniMax H3 服务 Python 控制示例脚本
演示如何在 Python 代码中引入并控制 MiniMax H3 服务的启动、停止与状态监控。
"""

import time
from service_manager import ServiceManager


def demo():
    # 1. 实例化管理器
    mgr = ServiceManager()

    print("=== 1. 查询当前运行状态 ===")
    status = mgr.get_status()
    print(f"前端是否运行: {status['workbench']['running']} (端口: {status['workbench']['port']})")
    print(f"后端是否运行: {status['backend']['running']} (端口: {status['backend']['port']})")
    print(f"存储大盘剩余空间: {status['storage_free_gb']} GB")

    # 2. 打印漂亮的终端状态看板
    mgr.print_status()

    # 3. 显卡管理与切换
    # mgr.start_workbench()    # 启动前端
    # mgr.stop_backend()       # 停止后端
    # mgr.start_backend(gpu_id="0")  # 启动后端 (指定 GPU)

    # mgr.stop_all()           # 停止所有服务
    # mgr.start_all(gpu_id="0")# 启动所有服务


    demo()

