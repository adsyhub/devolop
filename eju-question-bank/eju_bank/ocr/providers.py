"""Providers that return one complete page contract per call."""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Protocol

from ..errors import ContractError
from ..util import digest_json


class PageProvider(Protocol):
    def transcribe(self, *, images: list[Path], prompt: str, page: int, role: str) -> dict[str, Any]: ...
    def identity(self) -> dict[str, Any]: ...


def _json_from_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if "</think>" in stripped:
        stripped = stripped.split("</think>", 1)[1].strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.S | re.I)
    if fence:
        stripped = fence.group(1)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError as exc:
        start, end = stripped.find("{"), stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                value = json.loads(stripped[start : end + 1])
            except json.JSONDecodeError:
                raise ContractError(f"OCR provider did not return valid JSON: {exc}") from exc
        else:
            raise ContractError(f"OCR provider did not return valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("OCR provider response must be one JSON object")
    return value


class OpenAICompatibleVisionProvider:
    """Calls a local or remote OpenAI-compatible chat-completions endpoint."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.cache_config_digest=digest_json(config)
        self.base_url = str(config.get("baseUrl") or "").rstrip("/")
        self.model = str(config.get("model") or "")
        self.api_key_env = str(config.get("apiKeyEnv") or "")
        self.timeout_sec = int(config.get("timeoutSec") or 300)
        self.max_tokens = int(config.get("maxTokens") or 8_192)
        self.image_mode = str(config.get("imageMode") or "all")
        if not self.base_url or not self.model:
            raise ContractError("openai-compatible provider needs baseUrl and model")

    def identity(self) -> dict[str, Any]:
        return {
            "providerType": "openai-compatible",
            "model": self.model,
            "revision": "UNKNOWN",
            "configurationHash":self.cache_config_digest,
            "imageMode": self.image_mode,
            "maxTokens": self.max_tokens,
        }

    def transcribe(self, *, images: list[Path], prompt: str, page: int, role: str) -> dict[str, Any]:
        images = _select_images(images, self.image_mode)
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image in images:
            encoded = base64.b64encode(image.read_bytes()).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{encoded}"},
                }
            )
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": content}],
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key_env:
            key = os.environ.get(self.api_key_env)
            if not key:
                raise ContractError(f"Missing provider API key environment variable: {self.api_key_env}")
            headers["Authorization"] = f"Bearer {key}"
        request = urllib.request.Request(
            self.base_url + "/chat/completions", data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ContractError(f"OCR provider request failed for {role} page {page}: {exc}") from exc
        try:
            text = payload["choices"][0]["message"]["content"]
            if isinstance(text, list):
                text = "".join(str(item.get("text") or "") for item in text if isinstance(item, dict))
        except (KeyError, IndexError, TypeError) as exc:
            raise ContractError("OCR provider response has no choices[0].message.content") from exc
        return _json_from_text(str(text))


def _select_images(images: list[Path], mode: str) -> list[Path]:
    if not images:
        raise ContractError("OCR provider received no images")
    if mode == "full":
        return images[:1]
    if mode == "tiles":
        return images[1:] or images[:1]
    if mode == "all":
        return images
    raise ContractError("imageMode must be full, tiles or all")


def _free_gpu_mib(torch_module: Any) -> int:
    """Use driver-wide free memory on Windows; torch may only see its WDDM budget."""
    executable = shutil.which("nvidia-smi")
    if executable:
        completed = subprocess.run(
            [
                executable,
                "--query-gpu=memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if completed.returncode == 0:
            first_line = completed.stdout.strip().splitlines()[0]
            try:
                return int(first_line.strip())
            except (ValueError, IndexError):
                pass
    free_bytes, _ = torch_module.cuda.mem_get_info()
    return free_bytes // (1024 * 1024)


class QwenLocalProvider:
    """Direct local Qwen2.5-VL provider for the isolated OCR virtualenv."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.cache_config_digest=digest_json(config)
        try:
            import torch
            from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        except ImportError as exc:  # pragma: no cover - optional heavyweight provider
            raise ContractError(
                "qwen-local requires torch, transformers, Pillow and a Qwen2.5-VL checkpoint"
            ) from exc
        self._torch = torch
        self._image_class = __import__("PIL.Image", fromlist=["Image"])
        self.model_id = str(config.get("model") or "Qwen/Qwen2.5-VL-7B-Instruct")
        self.max_new_tokens = int(config.get("maxTokens") or 4_096)
        self.image_mode = str(config.get("imageMode") or "full")
        self.repetition_penalty = float(config.get("repetitionPenalty") or 1.0)
        dtype_name = str(config.get("dtype") or "bfloat16")
        device = str(config.get("device") or "cuda")
        min_free_gpu_mib = int(config.get("minFreeGpuMiB") or 0)
        if device.startswith("cuda") and min_free_gpu_mib:
            if not torch.cuda.is_available():
                raise ContractError("qwen-local is configured for CUDA, but CUDA is unavailable")
            free_mib = _free_gpu_mib(torch)
            if free_mib < min_free_gpu_mib:
                raise ContractError(
                    f"qwen-local needs at least {min_free_gpu_mib} MiB free GPU memory; "
                    f"only {free_mib} MiB is currently free. Wait for other GPU jobs to finish."
                )
        local_only = bool(config.get("localFilesOnly", False))
        max_pixels = int(config.get("maxPixels") or 3_211_264)
        min_pixels = int(config.get("minPixels") or 200_704)
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_id,
            dtype=getattr(torch, dtype_name),
            attn_implementation=str(config.get("attention") or "sdpa"),
            device_map=device,
            local_files_only=local_only,
        )
        self.model.eval()
        self.processor = AutoProcessor.from_pretrained(
            self.model_id,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
            local_files_only=local_only,
        )
        self.processor.tokenizer.padding_side = "left"

    def identity(self) -> dict[str, Any]:
        return {
            "providerType": "qwen-local",
            "model": self.model_id,
            "revision": "UNKNOWN",
            "configurationHash":self.cache_config_digest,
            "imageMode": self.image_mode,
            "maxTokens": self.max_new_tokens,
            "repetitionPenalty": self.repetition_penalty,
        }

    def transcribe(self, *, images: list[Path], prompt: str, page: int, role: str) -> dict[str, Any]:
        selected = _select_images(images, self.image_mode)
        loaded = []
        try:
            for path in selected:
                with self._image_class.open(path) as raw:
                    loaded.append(raw.convert("RGB"))
            content = [{"type": "image"} for _ in loaded]
            content.append({"type": "text", "text": prompt})
            messages = [{"role": "user", "content": content}]
            template = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.processor(
                text=[template], images=loaded, return_tensors="pt", padding=True
            ).to(self.model.device)
            with self._torch.inference_mode():
                generated = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    repetition_penalty=self.repetition_penalty,
                )
            trimmed = generated[:, inputs.input_ids.shape[1] :]
            text = self.processor.batch_decode(
                trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            return _json_from_text(text)
        except self._torch.cuda.OutOfMemoryError as exc:  # pragma: no cover - hardware dependent
            self._torch.cuda.empty_cache()
            raise ContractError(
                "Qwen OCR ran out of GPU memory; use imageMode=full or lower maxPixels"
            ) from exc
        finally:
            for image in loaded:
                image.close()


class CommandProvider:
    """Runs an isolated executable; images are appended as positional arguments."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.cache_config_digest=digest_json(config)
        command = config.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
            raise ContractError("command provider needs a non-empty command string array")
        self.command = command
        self.timeout_sec = int(config.get("timeoutSec") or 300)

    def identity(self) -> dict[str, Any]:
        return {
            "providerType": "command",
            "commandHash": digest_json(self.command),
            "revision": "UNKNOWN",
            "configurationHash":self.cache_config_digest,
            "imageMode": "all",
        }

    def transcribe(self, *, images: list[Path], prompt: str, page: int, role: str) -> dict[str, Any]:
        env = os.environ.copy()
        env.update({"EJU_PAGE": str(page), "EJU_ROLE": role, "EJU_PROMPT": prompt})
        completed = subprocess.run(
            [*self.command, *(str(path) for path in images)],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self.timeout_sec,
            check=False,
        )
        if completed.returncode != 0:
            raise ContractError(
                f"OCR command failed ({completed.returncode}) for {role} page {page}: "
                f"{completed.stderr.strip()[:500]}"
            )
        return _json_from_text(completed.stdout)


class Glm4vLocalProvider:
    """Direct local GLM-4.6V provider using transformers."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.cache_config_digest = digest_json(config)
        try:
            import torch
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except ImportError as exc:
            raise ContractError(
                "glm4v-local requires torch, transformers and a GLM-4.6V checkpoint"
            ) from exc
        self._torch = torch
        self._image_class = __import__("PIL.Image", fromlist=["Image"])
        self.model_id = str(config.get("model") or "GLM-4.6V-Flash")
        self.max_new_tokens = int(config.get("maxTokens") or 4096)
        self.image_mode = str(config.get("imageMode") or "full")
        dtype_name = str(config.get("dtype") or "bfloat16")
        device = str(config.get("device") or "cuda")
        self.processor = AutoProcessor.from_pretrained(
            self.model_id, trust_remote_code=True,
            local_files_only=bool(config.get("localFilesOnly", True)),
        )
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_id,
            torch_dtype=getattr(torch, dtype_name),
            device_map=device,
            trust_remote_code=True,
            local_files_only=bool(config.get("localFilesOnly", True)),
        )
        self.model.eval()

    def identity(self) -> dict[str, Any]:
        return {
            "providerType": "glm4v-local",
            "model": self.model_id,
            "revision": "UNKNOWN",
            "configurationHash": self.cache_config_digest,
            "imageMode": self.image_mode,
            "maxTokens": self.max_new_tokens,
        }

    def transcribe(self, *, images: list[Path], prompt: str, page: int, role: str) -> dict[str, Any]:
        selected = _select_images(images, self.image_mode)
        loaded = []
        try:
            for path in selected:
                with self._image_class.open(path) as raw:
                    loaded.append(raw.convert("RGB"))
            # Build chat messages for GLM-4.6V
            content = [{"type": "image", "image": img} for img in loaded]
            content.append({"type": "text", "text": prompt})
            messages = [{"role": "user", "content": content}]
            inputs = self.processor.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True,
                return_tensors="pt", return_dict=True,
                enable_thinking=True,
            ).to(self.model.device)
            with self._torch.inference_mode():
                generated = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                )
            trimmed = generated[:, inputs["input_ids"].shape[1]:]
            text = self.processor.decode(trimmed[0], skip_special_tokens=True)
            return _json_from_text(text)
        except self._torch.cuda.OutOfMemoryError as exc:
            self._torch.cuda.empty_cache()
            raise ContractError(
                "GLM-4.6V ran out of GPU memory; use imageMode=full or reduce image resolution"
            ) from exc
        finally:
            for image in loaded:
                image.close()


def provider_from_config(config_path: Path, provider_name: str) -> PageProvider:
    try:
        root = json.loads(config_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot load OCR provider config {config_path}: {exc}") from exc
    config = (root.get("providers") or {}).get(provider_name)
    if not isinstance(config, dict):
        raise ContractError(f"OCR provider {provider_name!r} is not configured")
    kind = config.get("kind")
    if kind == "openai-compatible":
        return OpenAICompatibleVisionProvider(config)
    if kind == "qwen-local":
        return QwenLocalProvider(config)
    if kind == "command":
        return CommandProvider(config)
    if kind == "glm4v-local":
        return Glm4vLocalProvider(config)
    raise ContractError(f"Unsupported OCR provider kind: {kind!r}")
