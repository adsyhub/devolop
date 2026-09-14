"""详解的机器审核：能确定性验证的部分，以及诚实地说"验证不了"。

详解是实际的人工瓶颈之一。生成出来是 ``DRAFT``，而 ``_latest_annotations`` 只取
``REVIEWED``，于是每一条都要人点一下才会显示给学习者 —— 1754 条存量解析全部标着
``REVIEWED``，但没有任何记录说得清那是谁审的。

规范 §12.1 要的不是"把 DRAFT 直接改成 REVIEWED"。那只是把没审过的东西改个名字。
它要的是一条独立的验证通路：验证通过的进 ``MACHINE_REVIEWED``，带着自己的
``reviewGrade``，学习端看得见它是机器审的；验证不了的**留在草稿**，宁可"暂缺详解"
也不放不可信的解析出去。

这个模块只做确定性的那一半 —— 不需要模型、每次结果相同、能写进测试的检查：

* 解析里陈述的答案必须与官方答案一致。给了模型官方答案再要它解释，属于条件生成，
  "解释支持这个答案"不构成独立的正确性证明（§12.1.3）；但解析**反过来说了别的
  答案**，那是确定性的矛盾，一定不能交付。
* 不能留占位文字、不能空、不能只是把题干抄一遍。
* 引用的选项编号必须在这道题真的存在。

模型层面的语义验证（公式推导对不对、单位换算对不对）这里不做，也不假装做了：
那种检查需要另一条独立的推理通路，没有它就返回 ``UNKNOWN``，草稿留着不交付。
"""

from __future__ import annotations

import re
from typing import Any

# 与 quality.py 共用同一套占位文字特征：成品里留着这些就说明内容没真正生成。
from .quality import _PLACEHOLDER

VERDICTS = ("PASS", "FAIL", "UNKNOWN")

# 解析正文里陈述答案的说法。只取"答案是 X"这种明确陈述，不去猜推导过程中的数字。
_STATED_ANSWER = re.compile(
    r"(?:正解|正确答案|正確答案|答案|答え|正答)\s*(?:是|为|為|：|:|は)\s*([0-9０-９A-Za-z]{1,3})")

_FULLWIDTH = str.maketrans("０１２３４５６７８９", "0123456789")


def _plain(nodes: Any) -> str:
    out: list[str] = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        if node.get("value"):
            out.append(str(node["value"]))
        if node.get("latex"):
            out.append(str(node["latex"]))
        if node.get("children"):
            out.append(_plain(node["children"]))
    return " ".join(part for part in out if part)


def _normalise_key(text: str) -> str:
    return str(text).translate(_FULLWIDTH).strip().upper()


class Verdict:
    """一次验证的结论，连同它为什么是这个结论。"""

    def __init__(self, result: str, checks: list[dict[str, Any]]) -> None:
        if result not in VERDICTS:
            raise ValueError(f"Unknown verdict {result!r}")
        self.result = result
        self.checks = checks

    @property
    def deliverable(self) -> bool:
        """只有全部通过才交付。UNKNOWN 不是通过，是"还不知道"。"""
        return self.result == "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {"result": self.result, "checks": self.checks,
                "verifierVersion": "1",
                "limitations": [
                    "仅确定性检查：答案一致性、占位文字、选项引用、非空。",
                    "未做模型层面的语义验证（推导、单位、数值代入）。",
                ]}


def _check(check_id: str, result: str, detail: str) -> dict[str, Any]:
    return {"id": check_id, "result": result, "detail": detail}


def verify_explanation(payload: dict[str, Any], question: dict[str, Any]) -> Verdict:
    """这条详解能不能直接交付给学习者。

    ``question`` 用组装后的题目，需要 ``options`` 与 ``correctAnswer``。
    """
    checks: list[dict[str, Any]] = []
    text = _plain(payload.get("contentAst"))
    worst = "PASS"

    def record(check_id: str, result: str, detail: str) -> None:
        nonlocal worst
        checks.append(_check(check_id, result, detail))
        if result == "FAIL" or (result == "UNKNOWN" and worst != "FAIL"):
            worst = result

    # ① 有实际内容。
    if not text.strip():
        record("explanation.non_empty", "FAIL", "解析正文是空的。")
    elif len(text.strip()) < 20:
        record("explanation.non_empty", "FAIL",
               f"解析正文只有 {len(text.strip())} 个字符，不足以构成解析。")
    else:
        record("explanation.non_empty", "PASS", f"正文 {len(text)} 字符。")

    # ② 没有占位文字。
    placeholder = _PLACEHOLDER.findall(text)
    if placeholder:
        record("explanation.no_placeholder", "FAIL",
               f"正文里留着占位文字「{placeholder[0]}」。")
    else:
        record("explanation.no_placeholder", "PASS", "没有占位文字。")

    # ③ 引用的选项必须存在。
    option_keys = {_normalise_key(o.get("key")) for o in question.get("options") or []}
    stated = [_normalise_key(m) for m in _STATED_ANSWER.findall(text)]
    unknown_refs = [s for s in stated if option_keys and s not in option_keys]
    if unknown_refs:
        record("explanation.option_refs_exist", "FAIL",
               f"解析提到的选项 {unknown_refs[0]} 不在这道题的选项 {sorted(option_keys)} 里。")
    else:
        record("explanation.option_refs_exist", "PASS", "引用的选项都存在。")

    # ④ 与官方答案一致。解析支持官方答案不构成独立证明（它是被告知的），但解析
    #    说出另一个答案是确定性的矛盾 —— 那种一定不能交付。
    official = (question.get("correctAnswer") or {}).get("optionKey")
    if official is None:
        record("explanation.matches_official_answer", "UNKNOWN",
               "这道题没有单选正解（可能是数字格或记述），确定性比对不适用。")
    elif not stated:
        record("explanation.matches_official_answer", "UNKNOWN",
               "解析没有明确陈述答案，无法确定性比对。")
    elif any(s != _normalise_key(official) for s in stated):
        record("explanation.matches_official_answer", "FAIL",
               f"解析陈述的答案 {stated} 与官方答案 {official} 不一致。")
    else:
        record("explanation.matches_official_answer", "PASS",
               f"解析陈述的答案与官方答案 {official} 一致。")

    return Verdict(worst, checks)
