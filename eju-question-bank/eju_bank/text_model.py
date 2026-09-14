"""对已配置的文字模型说话。校对整卷与写真题详解都走这里。

只做一件事：把一条 prompt 发给某个已解析的档位，把回答拿回来。档位从
``model_profiles`` 解析，所以这里不必再校验地址 —— 能走到这里的端点已经过
回环校验，或者是配置所有者显式开的云端档位。

模型的回答一律当作**待核**内容：调用方负责校验、标注来源、存成草稿。
这个模块不写库，也不判断回答对不对。
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any

from .errors import ContractError


class TextModelError(RuntimeError):
    """模型没给出可用回答。重试过了仍然失败才抛。"""


def _headers(profile: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    env = profile.get("apiKeyEnv")
    if env:
        key = os.environ.get(str(env), "").strip()
        if not key:
            raise ContractError(f"Set {env} before using profile {profile['id']}")
        headers["Authorization"] = "Bearer " + key
    return headers


def ask(profile: dict[str, Any], prompt: str, *, system: str | None = None,
        max_tokens: int | None = None, temperature: float | None = None,
        retries: int = 3) -> str:
    """问一次，拿回答的正文。"""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": profile["model"],
        "messages": messages,
        "max_tokens": int(max_tokens or profile.get("maxTokens") or 4096),
        "temperature": float(temperature if temperature is not None
                             else profile.get("temperature", 0.2)),
        # 本地 vLLM/llama.cpp 上的思考模式会把 token 花在草稿上而不是回答上。
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    endpoint = profile["baseUrl"].rstrip("/") + "/chat/completions"
    last: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            request = urllib.request.Request(endpoint, data=body,
                                             headers=_headers(profile), method="POST")
            with urllib.request.urlopen(request,
                                        timeout=int(profile.get("timeoutSec") or 600)) as response:
                payload = json.load(response)
            content = payload["choices"][0]["message"]["content"]
            if isinstance(content, list):
                # 有些服务把回答拆成分段内容块。
                content = "".join(part.get("text", "") for part in content
                                  if isinstance(part, dict))
            if not str(content or "").strip():
                raise ValueError("empty completion")
            return str(content)
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError,
                ValueError, json.JSONDecodeError) as exc:
            last = exc
            if attempt + 1 < max(1, retries):
                time.sleep(2 * (attempt + 1))
    raise TextModelError(f"{profile['id']} did not answer after {retries} attempts: {last}")


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def ask_json(profile: dict[str, Any], prompt: str, *, system: str | None = None,
             **kwargs: Any) -> Any:
    """问一次，把回答解析成 JSON。模型爱加代码围栏，所以先把围栏剥掉。"""
    raw = ask(profile, prompt, system=system, **kwargs)
    text = raw.strip()
    fenced = _FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    candidates = [text]
    # 回答前后常带一句客套话。取第一个完整的 JSON 值也试一遍。
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = text.find(opener), text.rfind(closer)
        if 0 <= start < end:
            candidates.append(text[start:end + 1])
    for candidate in candidates:
        for attempt in (candidate, _repair_escapes(candidate)):
            try:
                return json.loads(attempt)
            except json.JSONDecodeError:
                continue
    raise TextModelError(f"{profile['id']} did not return JSON: {raw[:200]}")


# JSON 字符串里合法的转义只有这几个，模型写 LaTeX 时会吐出 \times、\alpha 这种
# 非法转义。补一个反斜杠比让整条回答报废好。
#
# 但这救不回 \frac、\beta：f 和 b 本身是合法转义字母，那两处会被静默读成换页符和
# 退格符，坏掉却不报错。所以要 JSON 的地方一律在 prompt 里禁止写公式；内容必然
# 带公式的真题详解根本不用 JSON 传，走的是 explain.py 的分段格式。
_BAD_ESCAPE = re.compile(r'\\(?!["\\/bfnrtu])')


def _repair_escapes(text: str) -> str:
    return _BAD_ESCAPE.sub(r"\\\\", text)
