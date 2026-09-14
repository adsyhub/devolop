"""校对：首轮读错的页要被找出来重读，组装出来的卷要被读一遍。

制课流水线里的"校对"是三件事，这里管其中两件：

* **复读异常页**。首轮 OCR 用的是快模型，版面一复杂它会丢字、串行、甚至
  开始复述同一句话。这些页有可检测的痕迹（替换字符、长度塌缩、整段自我
  重复），把它们挑出来交给更强的视觉模型重读一遍，比让人一页页翻要快得多。
  重读结果不是无条件替换：只有在确实更好的时候才顶上，两份读法都留在缓存里。
* **读一遍组装出来的卷**。确定性 assembler 只保证结构自洽，不保证内容像话。
  文字模型逐批读题干、选项和答案，把自相矛盾、占位残留、公式断裂的题标出来，
  产出一份**疑点清单**。清单不改内容、不挡发布 —— 它是给人看的。

第三件事（正解表答案与题册选项的交叉反验）不在这里：它已经长在
``ocr/slot_join`` 和 ``attested_contracts`` 的定稿判断里，制课台只负责把那份
判断结果显示出来。

这里的模型输出一律是待核材料。重读会记下是哪个模型读的，疑点清单会记下是
哪个模型提的，两者都不会变成"已核对"。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from .util import load_json, write_json

REPLACEMENT = "�"
MIN_CHARS = 60
# 重读要"明显更好"才顶上首轮。1.25 倍是个保守的线：低于它的差别可能只是
# 两个模型对空白行的处理不同，不值得动已经落盘的读法。
BETTER_RATIO = 1.25
_LOOP = re.compile(r"(.{12,}?)\1{3,}", re.S)
_ROLE_FOLDER = {"QUESTION_BOOKLET": "ocr_cache", "ANSWER_KEY": "answer_ocr"}

# 有思考模式的视觉模型会把推理过程一起吐出来。那不是页面上的字，参与不了
# "读得更全吗"的比较 —— 不剥掉的话，一段自言自语就能冒充一页正文。
_THINK = re.compile(r"<think>.*?</think>", re.S | re.I)
# GLM 系会把 <|begin_of_box|> 这类控制标记漏进正文。它们不是页面上的字。
_CONTROL = re.compile(r"<\|[a-z_]+\|>", re.I)
_FENCE_ONLY = re.compile(r"^[`\s]*(?:markdown|html|json)?[`\s]*$", re.I)


def clean_reading(text: str) -> str:
    """模型回答里真正属于这一页的部分。"""
    stripped = _CONTROL.sub("", _THINK.sub("", str(text or ""))).strip()
    # 只剩一对空代码围栏，等于什么都没读到。
    return "" if _FENCE_ONLY.fullmatch(stripped) else stripped


def _degenerate(text: str) -> bool:
    return bool(_LOOP.search(text or ""))


def _booklet_reasons(data: dict[str, Any]) -> list[str]:
    raw = str(data.get("raw_text") or "")
    reasons: list[str] = []
    if len(raw.strip()) < MIN_CHARS:
        reasons.append(f"读出来只有 {len(raw.strip())} 字，页面几乎没被读到")
    if REPLACEMENT in raw:
        reasons.append(f"含 {raw.count(REPLACEMENT)} 个无法识别的字符")
    if _degenerate(raw):
        reasons.append("整段自我重复，模型读到一半开始复述")
    options = data.get("options")
    if isinstance(options, dict) and options and all(
            len(str(v or "").strip()) < 4 for v in options.values()):
        reasons.append("选项全是空壳，只读到编号没读到内容")
    return reasons


def _answer_reasons(data: dict[str, Any]) -> list[str]:
    raw = str(data.get("raw_text") or "")
    flat = str(data.get("raw_flat") or "")
    reasons: list[str] = []
    if "<table" not in raw.lower():
        reasons.append("没读出表格结构，合并单元格里的解答欄归属会丢")
    if len(flat.strip()) < MIN_CHARS:
        reasons.append(f"纯文本读法只有 {len(flat.strip())} 字")
    if REPLACEMENT in raw or REPLACEMENT in flat:
        reasons.append("含无法识别的字符")
    if _degenerate(raw) or _degenerate(flat):
        reasons.append("整段自我重复")
    return reasons


def blank_pages(work_dir: Path) -> dict[str, set[int]]:
    """PROBE 判定没有墨的页。空页被读成空是对的，不是读漏。"""
    result: dict[str, set[int]] = {role: set() for role in _ROLE_FOLDER}
    probe = Path(work_dir) / "probe.json"
    if not probe.is_file():
        return result
    try:
        data = load_json(probe)
    except (OSError, ValueError):
        return result
    for entry in data.get("files") or []:
        role = str(entry.get("role") or "")
        if role not in result:
            continue
        for page in entry.get("pages") or []:
            if page.get("likelyBlank") and int(page.get("page") or 0):
                result[role].add(int(page["page"]))
    return result


def suspicious_pages(work_dir: Path) -> list[dict[str, Any]]:
    """首轮读法里带着出错痕迹的页。按角色与页码排好。

    空白页不算。一页没有墨，OCR 读回来空字符串就是正确答案；把它送去复读只会
    让第二个模型讲一段"这张图是白的"，再把那段话当正文顶替掉诚实的空读法。
    """
    blanks = blank_pages(work_dir)
    found: list[dict[str, Any]] = []
    for role, folder in _ROLE_FOLDER.items():
        for path in sorted((Path(work_dir) / folder).glob("p*.json")):
            number = _page_of(path)
            try:
                data = load_json(path)
            except (OSError, ValueError):
                found.append({"role": role, "page": number,
                              "reasons": ["缓存文件读不出来"], "cache": path.name})
                continue
            reasons = (_booklet_reasons if role == "QUESTION_BOOKLET" else _answer_reasons)(data)
            if number in blanks.get(role, set()):
                # 空页只保留"读出来的东西本身是坏的"这一类痕迹，长度不足不算问题。
                reasons = [r for r in reasons if "字" not in r or "无法识别" in r]
            if reasons:
                found.append({"role": role, "page": number, "reasons": reasons,
                              "cache": path.name,
                              "firstPassModel": data.get("ocrModel")})
    return found


def _page_of(path: Path) -> int:
    digits = "".join(c for c in path.stem if c.isdigit())
    return int(digits) if digits else 0


def _image_for(work_dir: Path, role: str, page: int) -> Path | None:
    """这一页的整页渲染图。渲染目录带一层渲染档位哈希，所以走 OCR 自己的枚举。"""
    from .ocr.local_vision import page_number, rendered_pages

    for image in rendered_pages(Path(work_dir), role.lower()):
        if page_number(image) == page:
            return image
    return None


def _quality(text: str) -> tuple[int, int]:
    """(可用字数, 坏字符数)。越多字、越少坏字符越好。思考段不算字。"""
    stripped = clean_reading(text)
    return len(stripped), stripped.count(REPLACEMENT) + (100 if _degenerate(stripped) else 0)


def _better(new: str, old: str) -> bool:
    new_len, new_bad = _quality(new)
    old_len, old_bad = _quality(old)
    if new_len < MIN_CHARS:
        return False
    if new_bad < old_bad:
        return True
    if new_bad > old_bad:
        return False
    return new_len >= max(MIN_CHARS, old_len * BETTER_RATIO)


def reread_pages(work_dir: Path, pages: list[dict[str, Any]], profile: dict[str, Any], *,
                 cancelled: Callable[[], bool] | None = None,
                 on_progress: Callable[[int, int, int], None] | None = None,
                 on_log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """用复核模型把这些页重读一遍，明显更好的顶上首轮读法。"""
    from .ocr.local_vision import PROMPTS, Cancelled, transcribe
    from .ocr.glm_ocr_worker import GlmOcrWorker

    url = profile["baseUrl"].rstrip("/") + "/chat/completions"
    model = profile["model"]
    timeout = int(profile.get("timeoutSec") or 600)
    total = len(pages)
    replaced: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    failed = 0
    for index, entry in enumerate(pages, 1):
        if cancelled and cancelled():
            raise Cancelled(f"proofread cancelled after {index - 1}/{total} pages")
        role, page = entry["role"], entry["page"]
        image = _image_for(work_dir, role, page)
        cache = Path(work_dir) / _ROLE_FOLDER[role] / f"p{page:04d}.json"
        if image is None or not cache.is_file():
            failed += 1
            if on_log:
                on_log(f"  · {role} p{page}：没有渲染图或缓存，跳过重读")
            if on_progress:
                on_progress(index, total, failed)
            continue
        try:
            data = load_json(cache)
            image_bytes = image.read_bytes()
            if role == "QUESTION_BOOKLET":
                raw = clean_reading(transcribe(image_bytes, prompt=PROMPTS["text"], url=url,
                                               model=model, timeout=timeout))
                won = _better(raw, str(data.get("raw_text") or ""))
                record = dict(data)
                # 两份读法都留着：顶上去的那份要能被追回来源，被否掉的那份要能被复查。
                record["secondPass"] = {"model": model, "raw_text": raw, "accepted": won,
                                        "reasons": entry["reasons"]}
                if won:
                    parsed = GlmOcrWorker.parse_reading_page(
                        GlmOcrWorker.__new__(GlmOcrWorker), raw)
                    record["firstPass"] = {k: data.get(k) for k in
                                           ("raw_text", "raw_passage", "stem", "options",
                                            "passage_ast", "ocrModel") if k in data}
                    record.update(parsed)
                    record["raw_text"] = raw
                    record["ocrModel"] = model
                    record["ocrProofread"] = True
            else:
                html = clean_reading(transcribe(image_bytes, prompt=PROMPTS["tables"], url=url,
                                                model=model, timeout=timeout))
                flat = clean_reading(transcribe(image_bytes, prompt=PROMPTS["text"], url=url,
                                                model=model, timeout=timeout))
                won = _better(html, str(data.get("raw_text") or "")) or (
                    "<table" in html.lower() and "<table" not in str(data.get("raw_text") or "").lower())
                record = dict(data)
                record["secondPass"] = {"model": model, "raw_text": html, "raw_flat": flat,
                                       "accepted": won, "reasons": entry["reasons"]}
                if won:
                    record["firstPass"] = {k: data.get(k) for k in
                                           ("raw_text", "raw_flat", "ocrModel") if k in data}
                    record.update({"raw_text": html, "raw_flat": flat,
                                   "ocrModel": model, "ocrProofread": True})
            write_json(cache, record)
            (replaced if won else kept).append(
                {"role": role, "page": page, "reasons": entry["reasons"]})
            if on_log:
                on_log(f"  {'✓ 已顶替' if won else '· 保留首轮'} {role} p{page}"
                       f"（{'；'.join(entry['reasons'])}）")
        except Cancelled:
            raise
        except Exception as exc:
            failed += 1
            if on_log:
                on_log(f"  ✗ {role} p{page} 重读失败：{type(exc).__name__}: {str(exc)[:120]}")
        if on_progress:
            on_progress(index, total, failed)
    return {"reviewModel": model, "pagesChecked": total, "replaced": replaced,
            "kept": kept, "failed": failed}


# ── 读一遍组装出来的卷 ────────────────────────────────────────────────────

REVIEW_SYSTEM = (
    "You are a proofreader for EJU examination content that was transcribed by OCR. "
    "You judge only whether the transcription is internally coherent and complete. "
    "You never solve the question, never correct the answer, and never invent missing text. "
    "Answer with JSON only."
)

REVIEW_TEMPLATE = """以下是从原卷 OCR 出来、已由确定性组装器装成题的内容。逐题检查**转写质量**，不要解题。

要报告的问题只有这几类：
- placeholder：残留占位文字（如「選択肢 (1)」「待录入」），说明这一题的内容没真正读到
- truncated：题干或选项明显被截断、缺半句
- broken_math：公式/上下标/单位残缺或明显串行
- inconsistent：题干与选项自相矛盾，或选项编号重复、缺号
- answer_missing：标了答案但答案不在选项编号范围内

没问题的题不要出现在结果里。detail 用一句纯中文说明，**不要写公式、不要出现反斜杠**
（JSON 字符串里的 \\f 之类会被当成控制字符，把说明本身弄坏）。

严格按这个 JSON 返回，不要加任何解释：
{{"findings":[{{"questionId":"...","kind":"placeholder","detail":"一句话说明"}}]}}

题目：
{questions}
"""


def _plain(nodes: Any) -> str:
    """把 AST 压成一行纯文本，够模型判断转写质量就行。"""
    out: list[str] = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        kind = node.get("type")
        if kind in {"text", "paragraph", "callout", "underline"}:
            out.append(str(node.get("value") or ""))
        elif kind in {"inlineMath", "displayMath"}:
            out.append("$" + str(node.get("latex") or "") + "$")
        elif kind == "figure":
            out.append("[图]")
        elif kind == "answerSlot":
            out.append("[" + str(node.get("slot") or "") + "]")
        elif kind == "table":
            out.append("[表]")
        if node.get("children"):
            out.append(_plain(node["children"]))
    return " ".join(part for part in out if part).strip()


def paper_questions(paper: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for form in paper.get("forms") or []:
        for group in form.get("groups") or []:
            for question in group.get("questions") or []:
                answer = question.get("correctAnswer") or {}
                rows.append({
                    "questionId": question.get("questionId"),
                    "form": form.get("formCode"),
                    "label": question.get("printedLabel") or question.get("localKey"),
                    "stem": _plain(question.get("stemAst"))[:900],
                    "options": [{"key": o.get("key"), "text": _plain(o.get("contentAst"))[:300]}
                                for o in question.get("options") or []],
                    "answer": answer.get("optionKey") or answer.get("tokens") or None,
                })
    return rows


KINDS = {"placeholder", "truncated", "broken_math", "inconsistent", "answer_missing"}


def review_paper(paper: dict[str, Any], profile: dict[str, Any], *, batch_size: int = 8,
                 cancelled: Callable[[], bool] | None = None,
                 on_progress: Callable[[int, int], None] | None = None,
                 on_log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """让文字模型逐批读这份卷，产出疑点清单。清单不改内容。"""
    from .quality import Coverage
    from .text_model import TextModelError, ask_json

    rows = paper_questions(paper)
    known = {row["questionId"] for row in rows}
    batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    # 检查了多少批、成了多少批。没有这个分母，"findings 是空的"既可能是"都查过
    # 没问题"，也可能是"一批都没查成"，而这两件事的结论正好相反。
    completed = 0
    was_cancelled = False
    for index, batch in enumerate(batches, 1):
        if cancelled and cancelled():
            was_cancelled = True
            break
        prompt = REVIEW_TEMPLATE.format(
            questions=json.dumps(batch, ensure_ascii=False, indent=1))
        try:
            answer = ask_json(profile, prompt, system=REVIEW_SYSTEM)
            items = answer.get("findings") if isinstance(answer, dict) else answer
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                qid = str(item.get("questionId") or "")
                kind = str(item.get("kind") or "")
                # 模型报了一道不在这份卷里的题，说明它在编。丢掉，不当成发现。
                if qid not in known or kind not in KINDS:
                    continue
                findings.append({"questionId": qid, "kind": kind,
                                 "detail": str(item.get("detail") or "")[:400],
                                 "reviewModel": profile["model"]})
            completed += 1
        except (TextModelError, ValueError, TypeError, AttributeError) as exc:
            errors.append(f"第 {index}/{len(batches)} 批：{type(exc).__name__}: {str(exc)[:160]}")
            if on_log:
                on_log(f"  ✗ 第 {index}/{len(batches)} 批复核失败：{str(exc)[:120]}")
        if on_progress:
            on_progress(index, len(batches))
    by_kind: dict[str, int] = {}
    for finding in findings:
        by_kind[finding["kind"]] = by_kind.get(finding["kind"], 0) + 1
    coverage = Coverage(planned=len(batches), completed=completed,
                        failed=len(errors), cancelled=was_cancelled)
    return {"reviewModel": profile["model"], "questionsReviewed": len(rows),
            "batches": len(batches), "findings": findings, "byKind": by_kind,
            "errors": errors, "coverage": coverage.as_dict()}
