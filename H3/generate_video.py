#!/usr/bin/env python3
"""MiniMax H3 命令行快速视频生成工具

该脚本将请求发送给本地运行的 MiniMax H3 (ComfyUI) 服务，支持文本生成音视频（T2V）
以及首尾帧图片生成音视频（I2V）。
生成的视频默认保存在独立大盘 /data/storage/outputs/minimax-h3 目录下。
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

try:
    import websocket
except ImportError:
    websocket = None


def check_server_running(server_url: str) -> bool:
    try:
        req = urllib.request.Request(f"{server_url}/system_stats")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def upload_image(server_url: str, image_path: str) -> str:
    """上传本地图片至 ComfyUI input 目录并返回文件名"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"未找到图片文件: {image_path}")

    filename = os.path.basename(image_path)
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{server_url}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("name", filename)


def build_prompt_graph(
    prompt: str,
    width: int = 1344,
    height: int = 768,
    length: int = 124,
    steps: int = 4,
    use_turbo: bool = True,
    seed: int = -1,
    first_frame_name: str = None,
    last_frame_name: str = None,
    output_prefix: str = "minimax_h3",
) -> dict:
    if seed < 0:
        seed = random.randint(1, 10**14)

    # 4-step 或 8-step Turbo LoRA
    if steps <= 4:
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
    if use_turbo:
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
        "prompt": prompt,
        "width": width,
        "height": height,
        "length": length,
    }

    node_counter = 20
    if first_frame_name:
        graph[str(node_counter)] = {
            "class_type": "LoadImage",
            "inputs": {"image": first_frame_name},
        }
        i2v_inputs["first_frame"] = [str(node_counter), 0]
        node_counter += 1

    if last_frame_name:
        graph[str(node_counter)] = {
            "class_type": "LoadImage",
            "inputs": {"image": last_frame_name},
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
            "steps": steps,
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
            "filename_prefix": output_prefix,
            "format": "auto",
            "codec": "auto",
        },
    }

    return graph


def run_generation(args):
    server = args.server.rstrip("/")
    print(f"正在检查服务状态: {server} ...")
    if not check_server_running(server):
        print(f"\n[错误] 无法连接到 MiniMax-H3 服务 ({server})")
        print("请先执行以下命令启动服务：")
        print("  cd /workspace/Develop/H3 && ./start_comfyui.sh")
        print("启动成功后重新运行本脚本即可。\n")
        sys.exit(1)

    print("服务连接正常！准备提交任务...")

    first_frame_name = None
    last_frame_name = None
    if args.first_frame:
        print(f"上传首帧图像: {args.first_frame} ...")
        first_frame_name = upload_image(server, args.first_frame)
    if args.last_frame:
        print(f"上传尾帧图像: {args.last_frame} ...")
        last_frame_name = upload_image(server, args.last_frame)

    prompt_graph = build_prompt_graph(
        prompt=args.prompt,
        width=args.width,
        height=args.height,
        length=args.length,
        steps=args.steps,
        use_turbo=args.turbo,
        seed=args.seed,
        first_frame_name=first_frame_name,
        last_frame_name=last_frame_name,
        output_prefix=args.prefix,
    )

    client_id = str(uuid.uuid4())
    payload = json.dumps({"prompt": prompt_graph, "client_id": client_id}).encode("utf-8")
    req = urllib.request.Request(f"{server}/prompt", data=payload, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        prompt_id = res["prompt_id"]

    print(f"任务已提交，Task ID: {prompt_id}")
    print(f"提示词: \"{args.prompt}\"")
    print(f"规格: {args.width}x{args.height}, 时长帧数: {args.length} (~{args.length/24:.1f}s), 采样步数: {args.steps}")
    print("正在执行生成，请稍候...")

    # 如果安装了 websocket-client，实时监听执行进度
    ws_url = server.replace("http://", "ws://").replace("https://", "wss://") + f"/ws?clientId={client_id}"
    if websocket is not None:
        try:
            ws = websocket.create_connection(ws_url, timeout=10)
            while True:
                msg = ws.recv()
                if not isinstance(msg, str):
                    continue
                data = json.loads(msg)
                msg_type = data.get("type")
                if msg_type == "progress":
                    val = data["data"]["value"]
                    max_val = data["data"]["max"]
                    sys.stdout.write(f"\r进度: [{val}/{max_val}] 步...")
                    sys.stdout.flush()
                elif msg_type == "executing":
                    node = data["data"]["node"]
                    if node is None and data["data"]["prompt_id"] == prompt_id:
                        print("\n推理与渲染完成！")
                        break
                    elif node is not None:
                        # 正在执行特定节点
                        pass
                elif msg_type == "execution_error":
                    print(f"\n[执行错误]: {data['data']}")
                    sys.exit(1)
            ws.close()
        except Exception as e:
            print(f"(进度监听跳过: {e}，轮询历史中...)")

    # 轮询获取输出结果
    for _ in range(600):
        try:
            with urllib.request.urlopen(f"{server}/history/{prompt_id}") as resp:
                history = json.loads(resp.read().decode("utf-8"))
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    # 查找 SaveVideo 节点或视频输出
                    found_files = []
                    for node_out in outputs.values():
                        if "videos" in node_out:
                            for vid in node_out["videos"]:
                                found_files.append(vid.get("filename") if isinstance(vid, dict) else str(vid))
                        elif "video" in node_out:
                            for vid in node_out["video"]:
                                found_files.append(vid.get("filename") if isinstance(vid, dict) else str(vid))
                        elif "images" in node_out:
                            for img in node_out["images"]:
                                fname = img.get("filename") if isinstance(img, dict) else str(img)
                                if fname.endswith((".mp4", ".mkv", ".webm")):
                                    found_files.append(fname)

                    print("\n==================== 生成成功 ====================")
                    output_dir = "/data/storage/outputs/minimax-h3"
                    if found_files:
                        for fname in found_files:
                            full_path = os.path.join(output_dir, fname)
                            print(f"视频文件: {full_path}")
                    else:
                        print(f"输出目录: {output_dir}")
                    print("==================================================")
                    return
        except Exception:
            pass
        time.sleep(2)

    print("\n等待生成超时，请检查服务日志: /workspace/Develop/H3/comfyui.log")


def main():
    parser = argparse.ArgumentParser(description="MiniMax H3 视频快速生成命令行工具")
    parser.add_argument("--prompt", type=str, required=True, help="视频生成文本提示词（中文或英文）")
    parser.add_argument("--first-frame", type=str, default=None, help="首帧参考图片路径（可选）")
    parser.add_argument("--last-frame", type=str, default=None, help="尾帧参考图片路径（可选）")
    parser.add_argument("--width", type=int, default=1344, help="视频宽度（默认: 1344，须为32倍数）")
    parser.add_argument("--height", type=int, default=768, help="视频高度（默认: 768，须为32倍数）")
    parser.add_argument("--length", type=int, default=124, help="帧数（默认: 124，约 5.1 秒，须符合 17k+5）")
    parser.add_argument("--steps", type=int, default=4, help="采样步数（Turbo 模式下推荐 4 或 8 步）")
    parser.add_argument("--no-turbo", dest="turbo", action="store_false", help="禁用 Turbo LoRA 加速")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子（-1 表示随机）")
    parser.add_argument("--prefix", type=str, default="minimax_h3", help="输出视频前缀名称")
    parser.add_argument("--server", type=str, default="http://127.0.0.1:8188", help="ComfyUI 服务地址")

    parser.set_defaults(turbo=True)
    args = parser.parse_args()
    run_generation(args)


if __name__ == "__main__":
    main()

