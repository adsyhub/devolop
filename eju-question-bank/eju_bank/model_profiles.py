"""模型档位：哪个模型做 OCR、哪个做校对、哪个写真题详解。

页面只能从 ``config/providers.json`` 里已经写好的档位里挑，不能自己构造一个
端点或模型名 —— 那等于让浏览器决定把原卷图发到哪台机器上。所以这里做两件事：
读配置、探活。两者都不接受页面传进来的地址。

三个家族分工不同，所以分开列：

* ``vision``  读原页的视觉模型。OCR 首轮与校对复读都从这里挑。
* ``text``    读文字的模型。校对整卷与写真题详解从这里挑。

``visionProfiles`` / ``textProfiles`` 缺席时用内置档位兜底，它们对应本机已经
在跑的四个推理服务；配置文件写了同名档位就以配置为准。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .errors import ContractError
from .util import load_json

CONFIG_REF = "config/providers.json"

# 回环地址之外的视觉端点一律拒绝：原页图是受版权的原卷扫描，
# 把它发到本机之外是授权问题，不是配置口味问题。
LOOPBACK_PREFIXES = ("http://127.0.0.1", "http://localhost", "http://[::1]")

# 内置档位。它们描述的是本机常驻的四个服务，不是代码给出的"默认模型"：
# 配置文件里同名档位一律覆盖，配置里删掉这些名字它们仍可用，因为服务确实在那里。
BUILTIN_VISION: dict[str, dict[str, Any]] = {
    "local-glm-ocr": {
        "description": "本地 GLM-OCR，逐页首轮识别。快，版面简单的页足够。",
        "baseUrl": "http://127.0.0.1:8102/v1",
        "model": "zai-org/GLM-OCR",
        "role": "primary",
        "timeoutSec": 300,
    },
    "local-glm46v": {
        "description": "本地 GLM-4.6V-Flash，复杂版面与首轮异常页复读。",
        "baseUrl": "http://127.0.0.1:8101/v1",
        "model": "zai-org/GLM-4.6V-Flash",
        "role": "review",
        "timeoutSec": 600,
    },
    "local-flash-next-vision": {
        "description": "本地 Qwen3.8-Flash-Next，最后一轮疑难页裁决。慢。",
        "baseUrl": "http://127.0.0.1:8103/v1",
        "model": "Qwen/Qwen3.8-Flash-Next",
        "role": "review",
        "timeoutSec": 900,
    },
}

BUILTIN_TEXT: dict[str, dict[str, Any]] = {
    "local-qwen27": {
        "description": "本地 Qwen3.8-27B-FP8，整卷校对与详解初稿。",
        "baseUrl": "http://127.0.0.1:8100/v1",
        "model": "Qwen/Qwen3.8-27B-FP8",
        "temperature": 0.2,
        "maxTokens": 8000,
        "timeoutSec": 900,
    },
    "local-flash-next": {
        "description": "本地 Qwen3.8-Flash-Next，写详解与疑难裁决用的最强档。",
        "baseUrl": "http://127.0.0.1:8103/v1",
        "model": "Qwen/Qwen3.8-Flash-Next",
        "temperature": 0.2,
        "maxTokens": 12000,
        "timeoutSec": 1200,
    },
}

FAMILIES = ("vision", "text")
_CONFIG_KEY = {"vision": "visionProfiles", "text": "textProfiles"}
_BUILTIN = {"vision": BUILTIN_VISION, "text": BUILTIN_TEXT}


def config_path(root: Path) -> Path:
    return Path(root) / CONFIG_REF


def _config(root: Path) -> dict[str, Any]:
    path = config_path(root)
    if not path.is_file():
        return {}
    try:
        value = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _check(name: str, entry: dict[str, Any], family: str) -> dict[str, Any]:
    """一个档位只有配得齐才算存在。配错了要在挑之前就说出来。"""
    base_url = str(entry.get("baseUrl") or "").strip().rstrip("/")
    model = str(entry.get("model") or "").strip()
    if not base_url or not model:
        raise ContractError(f"Profile {name} needs both baseUrl and model")
    hosted = bool(str(entry.get("apiKeyEnv") or "").strip())
    if not base_url.startswith(LOOPBACK_PREFIXES):
        # 云端档位只有配置文件的所有者能开，而且必须显式写出取密钥的环境变量名。
        # 视觉档位没有这条路：原页图不出本机。
        if family == "vision" or not hosted:
            raise ContractError(
                f"Profile {name} must serve on the loopback interface"
                if family == "vision"
                else f"Profile {name} is not on loopback and declares no apiKeyEnv")
    return {
        "id": name,
        "family": family,
        "description": str(entry.get("description") or ""),
        "baseUrl": base_url,
        "model": model,
        "hosted": hosted,
        "apiKeyEnv": str(entry.get("apiKeyEnv") or "") or None,
        "role": str(entry.get("role") or ("review" if family == "vision" else "text")),
        "temperature": float(entry.get("temperature", 0.2)),
        "maxTokens": int(entry.get("maxTokens", 4096)),
        "timeoutSec": int(entry.get("timeoutSec", 600)),
    }


def load_profiles(root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """读出两个家族的全部档位。配错的档位被剔除并记下原因。"""
    config = _config(root)
    result: dict[str, dict[str, dict[str, Any]]] = {}
    problems: dict[str, str] = {}
    for family in FAMILIES:
        merged = dict(_BUILTIN[family])
        configured = config.get(_CONFIG_KEY[family])
        if isinstance(configured, dict):
            for name, entry in configured.items():
                if isinstance(entry, dict):
                    merged[name] = entry
        checked: dict[str, dict[str, Any]] = {}
        for name, entry in merged.items():
            try:
                checked[name] = _check(str(name), entry, family)
            except ContractError as exc:
                problems[str(name)] = str(exc)
        result[family] = checked
    result["problems"] = problems  # type: ignore[assignment]
    return result


def resolve(root: Path, family: str, name: str | None) -> dict[str, Any]:
    """把页面传来的档位名换成档位本身；不认识的名字直接拒绝。"""
    if family not in FAMILIES:
        raise ContractError(f"Unknown model family {family}")
    if not isinstance(name, str) or not name.strip():
        raise ContractError(f"Select a {family} profile from {CONFIG_REF}")
    profiles = load_profiles(root)[family]
    if name not in profiles:
        raise ContractError(f"Profile {name} is not defined in {CONFIG_REF}")
    return profiles[name]


def probe(profile: dict[str, Any], timeout: float = 1.5) -> dict[str, Any]:
    """服务在不在、要的模型加载了没有。探活失败不是错误，是一条状态。"""
    endpoint = profile["baseUrl"].rstrip("/") + "/models"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        return {"available": False, "statusText": "服务未响应"}
    rows = payload.get("data") if isinstance(payload, dict) else None
    ids = {str(row.get("id") or "") for row in rows or [] if isinstance(row, dict)}
    if profile["model"] and ids and profile["model"] not in ids:
        return {"available": False, "statusText": "服务在线，但这个模型没加载"}
    return {"available": True, "statusText": "在线"}


def describe(root: Path) -> dict[str, Any]:
    """制作台要显示的模型清单：档位 + 实时可用性。"""
    loaded = load_profiles(root)
    problems = loaded.pop("problems", {})  # type: ignore[arg-type]
    flat = [p for family in FAMILIES for p in loaded[family].values()]
    with ThreadPoolExecutor(max_workers=max(1, len(flat))) as pool:
        probes = list(pool.map(lambda p: probe(p) if not p["hosted"] else
                               {"available": True, "statusText": "云端档位（按配置的密钥调用）"}, flat))
    merged = [{**profile, **status} for profile, status in zip(flat, probes)]
    return {
        "configRef": CONFIG_REF,
        "configPresent": config_path(root).is_file(),
        "vision": [p for p in merged if p["family"] == "vision"],
        "text": [p for p in merged if p["family"] == "text"],
        "problems": [{"profile": k, "message": v} for k, v in sorted(problems.items())],
    }
