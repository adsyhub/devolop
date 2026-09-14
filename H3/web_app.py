#!/usr/bin/env python3
"""MiniMax H3 视频生成控制台 Web 服务后端
基于 FastAPI 构建，提供 REST API、实时 WebSocket/SSE 进度流和静态前端托管。
"""

import asyncio
import json
import os
import random
import shutil
import subprocess
import time
import uuid
from typing import Optional

import aiohttp
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="MiniMax H3 Video Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COMFY_HOST = "127.0.0.1"
COMFY_PORT = 8188
COMFY_URL = f"http://{COMFY_HOST}:{COMFY_PORT}"
COMFY_WS_URL = f"ws://{COMFY_HOST}:{COMFY_PORT}/ws"

STORAGE_OUTPUT_DIR = "/data/storage/outputs/minimax-h3"
COMFY_INPUT_DIR = "/workspace/Develop/H3/ComfyUI/input"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

os.makedirs(STORAGE_OUTPUT_DIR, exist_ok=True)
os.makedirs(COMFY_INPUT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)


class GenerateRequest(BaseModel):
    prompt: str
    width: int = 1344
    height: int = 768
    length: int = 124
    steps: int = 4
    use_turbo: bool = True
    seed: int = -1
    first_frame: Optional[str] = None
    last_frame: Optional[str] = None
    prefix: str = "minimax_h3"


def get_gpu_info():
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.check_output(cmd, encoding="utf-8").strip()
        gpus = []
        for line in out.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                gpus.append(
                    {
                        "index": int(parts[0]),
                        "name": parts[1],
                        "total_mb": float(parts[2]),
                        "used_mb": float(parts[3]),
                        "free_mb": float(parts[4]),
                        "temp_c": int(parts[5]),
                        "util_pct": int(parts[6]),
                    }
                )
        return gpus
    except Exception:
        return []


def get_disk_info():
    try:
        st = shutil.disk_usage("/data/storage")
        return {
            "total_gb": round(st.total / (1024**3), 1),
            "used_gb": round(st.used / (1024**3), 1),
            "free_gb": round(st.free / (1024**3), 1),
            "used_pct": round((st.used / st.total) * 100, 1),
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "used_pct": 0}


from service_manager import ServiceManager


class SwitchGpuRequest(BaseModel):
    gpu_id: str


@app.get("/api/gpus")
async def get_gpus():
    mgr = ServiceManager()
    return {
        "gpus": mgr.get_gpu_list(),
        "active_gpu": mgr.get_active_gpu(),
    }


@app.post("/api/switch_gpu")
async def switch_gpu(req: SwitchGpuRequest):
    mgr = ServiceManager()
    result = await asyncio.to_thread(mgr.switch_gpu, req.gpu_id)
    return result


@app.post("/api/interrupt")
async def interrupt_execution():
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(f"{COMFY_URL}/queue", json={"clear": True})
            await session.post(f"{COMFY_URL}/interrupt")
        return {"status": "success", "message": "已中断当前生成任务"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/engine/start")
async def start_engine():
    """在前端一键启动底层推理引擎并绑定当前配置显卡"""
    mgr = ServiceManager()
    active_gpu = mgr.get_active_gpu()
    gpu_uuid = active_gpu.get("gpu_uuid")
    success = await asyncio.to_thread(mgr.start_backend, gpu_id=gpu_uuid, wait=True, timeout=25)
    if success:
        return {
            "success": True,
            "message": f"MiniMax H3 计算引擎已成功启动！已绑定 {active_gpu.get('gpu_name', 'GPU')}，随时可以开始生成。",
        }
    else:
        return {"success": False, "message": "启动计算引擎超时或失败，请查看 comfyui.log"}


@app.post("/api/engine/stop")
async def stop_engine():
    """在前端一键关闭底层推理引擎，100% 释放显卡显存"""
    mgr = ServiceManager()
    await asyncio.to_thread(mgr.stop_backend)
    return {
        "success": True,
        "message": "已成功停止 MiniMax H3 计算引擎！显卡显存已彻底释放 (0 GB 占用)。",
    }


@app.get("/api/status")
async def get_status():
    comfy_online = False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{COMFY_URL}/system_stats", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                if resp.status == 200:
                    comfy_online = True
    except Exception:
        comfy_online = False

    mgr = ServiceManager()
    active_gpu = mgr.get_active_gpu()

    return {
        "comfy_online": comfy_online,
        "gpus": mgr.get_gpu_list(),
        "active_gpu": active_gpu,
        "storage": get_disk_info(),
        "active_device": f"{active_gpu.get('gpu_name', 'H100')} (GPU {active_gpu.get('gpu_id', '0')})",
    }


@app.post("/api/upload")
async def upload_image_file(file: UploadFile = File(...)):
    filename = f"upload_{int(time.time())}_{uuid.uuid4().hex[:6]}_{file.filename}"
    filepath = os.path.join(COMFY_INPUT_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": filename, "url": f"/api/input/{filename}"}


@app.get("/api/input/{filename}")
async def get_input_file(filename: str):
    path = os.path.join(COMFY_INPUT_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


def build_h3_prompt_graph(req: GenerateRequest) -> dict:
    seed = req.seed if req.seed >= 0 else random.randint(1, 10**14)
    if req.steps <= 4:
        lora_name = "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"
    else:
        lora_name = "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"

    graph = {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "minimax_h3_fl2va_bf16.safetensors",
                "weight_dtype": "default",
            },
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen3vl_32b_minimax_h3_bf16.safetensors",
                "type": "minimax",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "minimax_h3_video_vae_fp16.safetensors",
            },
        },
        "4": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "minimax_h3_audio_vae_fp32.safetensors",
            },
        },
    }

    current_model = ["1", 0]
    if req.use_turbo:
        graph["5"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": current_model,
                "lora_name": lora_name,
                "strength_model": 1.0,
            },
        }
        current_model = ["5", 0]

    graph["6"] = {
        "class_type": "MiniMaxH3SigmaShift",
        "inputs": {
            "model": current_model,
            "shift_video": 12.0,
            "shift_audio": 3.0,
        },
    }

    i2v_inputs = {
        "clip": ["2", 0],
        "vae": ["3", 0],
        "prompt": req.prompt,
        "width": req.width,
        "height": req.height,
        "length": req.length,
    }

    node_counter = 20
    if req.first_frame:
        graph[str(node_counter)] = {
            "class_type": "LoadImage",
            "inputs": {"image": req.first_frame},
        }
        i2v_inputs["first_frame"] = [str(node_counter), 0]
        node_counter += 1

    if req.last_frame:
        graph[str(node_counter)] = {
            "class_type": "LoadImage",
            "inputs": {"image": req.last_frame},
        }
        i2v_inputs["last_frame"] = [str(node_counter), 0]
        node_counter += 1

    graph["7"] = {
        "class_type": "MiniMaxH3ImageToVideo",
        "inputs": i2v_inputs,
    }

    graph["8"] = {
        "class_type": "BasicGuider",
        "inputs": {
            "model": ["6", 0],
            "conditioning": ["7", 0],
        },
    }

    graph["9"] = {
        "class_type": "RandomNoise",
        "inputs": {
            "noise_seed": seed,
        },
    }

    graph["10"] = {
        "class_type": "KSamplerSelect",
        "inputs": {
            "sampler_name": "res_multistep",
        },
    }

    graph["11"] = {
        "class_type": "BasicScheduler",
        "inputs": {
            "model": ["6", 0],
            "scheduler": "simple",
            "steps": req.steps,
            "denoise": 1.0,
        },
    }

    graph["12"] = {
        "class_type": "SamplerCustomAdvanced",
        "inputs": {
            "noise": ["9", 0],
            "guider": ["8", 0],
            "sampler": ["10", 0],
            "sigmas": ["11", 0],
            "latent_image": ["7", 1],
        },
    }

    graph["13"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["12", 0],
            "vae": ["3", 0],
        },
    }

    graph["14"] = {
        "class_type": "VAEDecodeAudio",
        "inputs": {
            "samples": ["12", 0],
            "vae": ["4", 0],
        },
    }

    graph["15"] = {
        "class_type": "CreateVideo",
        "inputs": {
            "images": ["13", 0],
            "audio": ["14", 0],
            "fps": 24,
            "bit_depth": 8,
        },
    }

    graph["16"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "video": ["15", 0],
            "filename_prefix": req.prefix,
            "format": "auto",
            "codec": "auto",
        },
    }

    return graph


@app.post("/api/generate")
async def generate_video_stream(req: GenerateRequest):
    """通过 Server-Sent Events (SSE) 实时流式返回生成进度与最终视频"""
    prompt_graph = build_h3_prompt_graph(req)
    client_id = str(uuid.uuid4())

    async def event_generator():
        event_queue = asyncio.Queue()
        stop_heartbeat = asyncio.Event()

        # 发送初始进度
        await event_queue.put(
            f"data: {json.dumps({'stage': 'submitting', 'progress': 2, 'step_index': 1, 'message': '正在向 MiniMax H3 计算引擎提交任务...'})}\n\n"
        )

        async def heartbeat_worker():
            """持续向客户端发送 SSE 注释行 (: ping)，防止代理/VS Code 端口转发/浏览器因长时间无数据中断连接"""
            while not stop_heartbeat.is_set():
                try:
                    await asyncio.sleep(2.0)
                    if not stop_heartbeat.is_set():
                        await event_queue.put(": ping\n\n")
                except asyncio.CancelledError:
                    break

        hb_task = asyncio.create_task(heartbeat_worker())

        async def execution_worker():
            mgr = ServiceManager()
            # 若后端计算引擎未启动，自动拉起并绑定当前配置显卡
            if not mgr.is_backend_running():
                await event_queue.put(
                    f"data: {json.dumps({'stage': 'starting_engine', 'progress': 3, 'step_index': 1, 'message': '检测到计算引擎处于休眠状态，正在自动拉起引擎并唤醒显卡 (约 5 秒)...'})}\n\n"
                )
                active_gpu = mgr.get_active_gpu()
                started = await asyncio.to_thread(mgr.start_backend, gpu_id=active_gpu.get("gpu_uuid"), wait=True, timeout=25)
                if not started:
                    await event_queue.put(
                        f"data: {json.dumps({'stage': 'error', 'message': '自动启动计算引擎失败，请在顶栏点击「启动引擎」按钮重试'})}\n\n"
                    )
                    return

            prompt_id = None
            ws_url = f"{COMFY_WS_URL}?clientId={client_id}"
            found_file = None

            try:
                timeout = aiohttp.ClientTimeout(total=600)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.ws_connect(ws_url, heartbeat=15.0) as ws:
                        payload = {"prompt": prompt_graph, "client_id": client_id}
                        async with session.post(f"{COMFY_URL}/prompt", json=payload) as resp:
                            if resp.status != 200:
                                err_text = await resp.text()
                                await event_queue.put(
                                    f"data: {json.dumps({'stage': 'error', 'message': f'提交任务失败: {err_text}'})}\n\n"
                                )
                                return
                            res_json = await resp.json()
                            prompt_id = res_json.get("prompt_id")

                        await event_queue.put(
                            f"data: {json.dumps({'stage': 'queued', 'prompt_id': prompt_id, 'progress': 5, 'step_index': 1, 'message': '任务已进入流水线队列，准备就绪...'})}\n\n"
                        )

                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                msg_type = data.get("type")

                                if msg_type == "status":
                                    queue_rem = data.get("data", {}).get("status", {}).get("exec_info", {}).get("queue_remaining", 0)
                                    if queue_rem > 1:
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'queued', 'progress': 5, 'step_index': 1, 'message': f'前方队列等待中 ({queue_rem} 个任务)...'})}\n\n"
                                        )

                                elif msg_type == "execution_start":
                                    await event_queue.put(
                                        f"data: {json.dumps({'stage': 'started', 'progress': 8, 'step_index': 1, 'message': '初始化计算流，加载文本编码上下文...'})}\n\n"
                                    )

                                elif msg_type == "executing":
                                    node = data["data"].get("node")
                                    if node is None and data["data"].get("prompt_id") == prompt_id:
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'finalizing', 'progress': 98, 'step_index': 5, 'message': '渲染完成，正在校验输出文件...'})}\n\n"
                                        )
                                        break
                                    elif node in ("1", "2", "3", "4", "5", "6"):
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'loading_models', 'node': node, 'progress': 12, 'step_index': 1, 'message': '正在加载 BF16 旗舰模型与加速 LoRA 算力权重...'})}\n\n"
                                        )
                                    elif node == "7":
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'text_encoding', 'node': '7', 'progress': 18, 'step_index': 1, 'message': '[阶段 1/5] Qwen3-VL 32B 深度文本理解与时序语义对齐中...'})}\n\n"
                                        )
                                    elif node in ("8", "9", "10", "11"):
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'sampling_prep', 'node': node, 'progress': 22, 'step_index': 2, 'message': '[阶段 2/5] 采样引导器与多步调度器初始化就绪...'})}\n\n"
                                        )
                                    elif node == "12":
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'sampling_start', 'node': '12', 'progress': 25, 'step_index': 2, 'message': '[阶段 2/5] DiT 扩散骨干网络进入去噪采样阶段...'})}\n\n"
                                        )
                                    elif node == "14":
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'audio_decoding', 'node': '14', 'progress': 82, 'step_index': 3, 'message': '[阶段 3/5] MiniMax 音频 VAE 解码: 生成 32kHz 原生双声道音乐与音效...'})}\n\n"
                                        )
                                    elif node == "13":
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'video_decoding', 'node': '13', 'progress': 90, 'step_index': 4, 'message': '[阶段 4/5] MiniMax 视频 VAE 解码: 高保真像素帧序列还原与时序重构...'})}\n\n"
                                        )
                                    elif node in ("15", "16"):
                                        await event_queue.put(
                                            f"data: {json.dumps({'stage': 'saving', 'node': node, 'progress': 96, 'step_index': 5, 'message': '[阶段 5/5] 音视频流同步混音封装 (MP4 H.264) 并写入存储大盘...'})}\n\n"
                                        )

                                elif msg_type == "progress":
                                    val = data["data"]["value"]
                                    max_val = data["data"]["max"]
                                    step_ratio = val / max_val
                                    overall_pct = 25 + round(step_ratio * 55)
                                    pct = round(step_ratio * 100)
                                    await event_queue.put(
                                        f"data: {json.dumps({'stage': 'sampling', 'progress': overall_pct, 'step': val, 'total_steps': max_val, 'step_pct': pct, 'step_index': 2, 'message': f'[阶段 2/5] 扩散模型去噪采样: 第 {val}/{max_val} 步 ({pct}%)'})}\n\n"
                                    )

                                elif msg_type == "execution_error":
                                    err_details = data.get("data", {})
                                    await event_queue.put(
                                        f"data: {json.dumps({'stage': 'error', 'message': f'执行出错: {json.dumps(err_details, ensure_ascii=False)}'})}\n\n"
                                    )
                                    return
            except Exception as e:
                await event_queue.put(
                    f"data: {json.dumps({'stage': 'monitoring', 'progress': 50, 'step_index': 2, 'message': f'正在轮询任务执行状态 ({str(e)})...'})}\n\n"
                )

            # 轮询获取输出文件（最多 90 秒）
            for _ in range(90):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{COMFY_URL}/history/{prompt_id}") as resp:
                            if resp.status == 200:
                                history = await resp.json()
                                if prompt_id in history:
                                    outputs = history[prompt_id].get("outputs", {})
                                    for node_out in outputs.values():
                                        if "videos" in node_out:
                                            for v in node_out["videos"]:
                                                found_file = v.get("filename") if isinstance(v, dict) else str(v)
                                                break
                                        elif "video" in node_out:
                                            for v in node_out["video"]:
                                                found_file = v.get("filename") if isinstance(v, dict) else str(v)
                                                break
                                        elif "images" in node_out:
                                            for img in node_out["images"]:
                                                fname = img.get("filename") if isinstance(img, dict) else str(img)
                                                if fname.endswith((".mp4", ".mkv", ".webm")):
                                                    found_file = fname
                                                    break
                                    if found_file:
                                        break
                except Exception:
                    pass
                if found_file:
                    break
                await asyncio.sleep(1)

            # 备选：按时间查找最新的 mp4
            if not found_file and os.path.exists(STORAGE_OUTPUT_DIR):
                files = [f for f in os.listdir(STORAGE_OUTPUT_DIR) if f.endswith(".mp4")]
                if files:
                    files.sort(
                        key=lambda x: os.path.getmtime(os.path.join(STORAGE_OUTPUT_DIR, x)),
                        reverse=True,
                    )
                    found_file = files[0]

            if found_file:
                video_url = f"/api/video/{found_file}"
                await event_queue.put(
                    f"data: {json.dumps({'stage': 'completed', 'progress': 100, 'filename': found_file, 'video_url': video_url, 'message': '生成成功！'})}\n\n"
                )
            else:
                await event_queue.put(
                    f"data: {json.dumps({'stage': 'error', 'message': '任务执行完毕但未检测到输出视频文件'})}\n\n"
                )

        exec_task = asyncio.create_task(execution_worker())

        try:
            while not exec_task.done() or not event_queue.empty():
                try:
                    # 等待队列中的新消息或心跳，超时 2.0 秒以保证轮转
                    msg = await asyncio.wait_for(event_queue.get(), timeout=2.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            stop_heartbeat.set()
            hb_task.cancel()
            if not exec_task.done():
                await exec_task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/history")
async def get_history_videos():
    if not os.path.exists(STORAGE_OUTPUT_DIR):
        return []

    files = [f for f in os.listdir(STORAGE_OUTPUT_DIR) if f.endswith(".mp4")]
    items = []
    for fname in files:
        full_path = os.path.join(STORAGE_OUTPUT_DIR, fname)
        st = os.stat(full_path)
        size_mb = round(st.st_size / (1024 * 1024), 2)
        items.append(
            {
                "filename": fname,
                "url": f"/api/video/{fname}",
                "size_mb": size_mb,
                "mtime": st.st_mtime,
                "date_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
            }
        )

    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items


@app.api_route("/api/video/{filename}", methods=["GET", "HEAD"])
async def get_video(filename: str, request: Request):
    """支持 HTTP 206 Partial Content 断点续传与在线时间轴拖拽"""
    filepath = os.path.join(STORAGE_OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Video file not found")

    stat = os.stat(filepath)
    file_size = stat.st_size
    range_header = request.headers.get("Range")

    if request.method == "HEAD":
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
        }
        return Response(status_code=200, headers=headers)

    if not range_header:
        return FileResponse(filepath, media_type="video/mp4", filename=filename)

    # 解析 Range: bytes=start-end
    try:
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        end = int(bytes_range[1]) if bytes_range[1] else file_size - 1
    except Exception:
        start = 0
        end = file_size - 1

    length = end - start + 1

    def file_stream():
        with open(filepath, "rb") as f:
            f.seek(start)
            bytes_left = length
            chunk_size = 64 * 1024
            while bytes_left > 0:
                read_size = min(chunk_size, bytes_left)
                data = f.read(read_size)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Content-Type": "video/mp4",
    }
    return StreamingResponse(file_stream(), status_code=206, headers=headers)


@app.delete("/api/video/{filename}")
async def delete_video(filename: str):
    filepath = os.path.join(STORAGE_OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="File not found")


@app.api_route("/", methods=["GET", "HEAD"])
async def get_index(request: Request):
    index_path = os.path.join(STATIC_DIR, "index.html")
    if request.method == "HEAD":
        return Response(status_code=200, media_type="text/html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>MiniMax H3 Video Studio UI Loading...</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app:app", host="0.0.0.0", port=7860, reload=False)

