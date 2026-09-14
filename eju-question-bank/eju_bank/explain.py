"""真题详解：让文字模型给已定稿的题写一份解析初稿。

这个项目里的详解本来是一篇一篇手写进 ``scripts/generate_*_explanations.py``
的 —— 128 个脚本，每个里面钉着一套卷的解析正文。那条路产出的质量很高，
但它不能规模化，也没法在制课台上按一下就有。

所以这里做的是**初稿**，而且刻意停在初稿：

* 存成 ``DRAFT``。``_latest_annotations`` 只取 ``REVIEWED``/``WITHDRAWN``，
  所以草稿一个字都到不了学习者眼前，要人改成 REVIEWED 才会。
* 官方答案是输入，不是模型的结论。模型被要求解释**给定的那个答案**为什么对；
  没有记录答案的题直接跳过，不让模型去猜。
* 转写有疑点的题不写详解。给一段占位文字配一篇解析，只会让错的内容看起来更可信。

每条草稿都记下是哪个模型写的，人复核时知道自己在改谁的话。
"""

from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from .util import utc_now

SYSTEM = (
    "You write solution explanations for EJU (Examination for Japanese University Admission) "
    "questions that a student will read while reviewing a practice attempt. "
    "The official answer is given to you: explain why that answer is correct. "
    "Never contradict the given answer, never re-derive a different one, and never "
    "invent numbers, graphs or option text that is not in the input. "
    "Answer with JSON only."
)

TEMPLATE = """为下面这道 EJU 真题写一份中文解析初稿。官方答案已给出，你的任务是讲清它为什么对。

要求：
- 讲题目考什么、怎么一步步得到官方答案、其他选项错在哪
- 数学与物理化学的式子用 LaTeX 行内写法（$...$），保留单位、上下标、符号
- 题干里没有的数据不要编。若原文有缺口（图看不到、数据缺失），直接写明"原文此处为图/数据缺失"，不要脑补
- 用简体中文写，专有名词可保留日文原词

严格按下面的分段格式回答，不要用 JSON、不要加代码围栏：

###TITLE
一句话题目主题
###POINTS
考点一
考点二
###SOLUTION
分段正文，段之间空一行

题目：
{question}
"""

MAX_POINTS = 8


_SECTION = re.compile(r"^###\s*(TITLE|POINTS|SOLUTION)\s*$", re.M | re.I)


def parse_sections(raw: str) -> dict[str, Any]:
    """读分段格式。

    这里刻意不用 JSON。解析要求模型把 $\\frac{a}{b}$ 这样的式子放进 JSON 字符串，
    每个反斜杠都得转义成 \\\\ —— 实测本地模型做不到，一道带公式的题就足以让
    整个回答解析失败。分段格式对反斜杠完全免疫。
    """
    parts = _SECTION.split(str(raw or "").strip())
    if len(parts) < 3:
        raise ValueError("model did not return the ###TITLE/###POINTS/###SOLUTION sections")
    sections: dict[str, str] = {}
    for index in range(1, len(parts) - 1, 2):
        sections[parts[index].upper()] = parts[index + 1].strip()
    points = [line.strip(" -·\t") for line in sections.get("POINTS", "").splitlines()]
    return {
        "title": sections.get("TITLE", "").strip().splitlines()[0] if sections.get("TITLE") else "",
        "points": [p for p in points if p],
        "solution": sections.get("SOLUTION", "").strip(),
    }


def _payload(question: dict[str, Any], answer: dict[str, Any], model: str,
             language: str = "zh") -> dict[str, Any]:
    """把模型回答装成这个库认的 explanation 修订版内容。"""
    from .page_contract import validate_ast

    solution = str(answer.get("solution") or "").strip()
    if not solution:
        raise ValueError("model returned no solution text")
    nodes = [{"type": "paragraph", "value": part.strip()}
             for part in solution.split("\n\n") if part.strip()]
    if not nodes:
        raise ValueError("solution text is empty after splitting")
    issues = validate_ast(nodes, ref="explanation")
    if issues:
        raise ValueError(f"explanation AST rejected: {issues[:2]}")
    points = [str(p).strip() for p in (answer.get("points") or []) if str(p).strip()]
    return {
        "kind": "EXPLANATION",
        "language": language,
        "title": str(answer.get("title") or question["label"] or "")[:200],
        "points": points[:MAX_POINTS],
        "officialAnswer": question["answer"],
        "contentAst": nodes,
        "generatedBy": model,
        "reviewState": "MACHINE_DRAFT",
        "updatedAt": utc_now(),
    }


def question_versions(database: Any, paper_version_id: str) -> dict[str, str]:
    """questionId → questionVersionId，取这一版里的。"""
    rows = database.connection.execute(
        "SELECT question_id, id FROM question_versions WHERE paper_version_id=?",
        (paper_version_id,)).fetchall()
    return {row[0]: row[1] for row in rows}


def delivered_explanation(database: Any, question_version_id: str, language: str) -> bool:
    """这道题这个语言的解析已经在交付了吗？

    判断依据是"有没有一版正在给学习者看的解析"，而不是"有没有留下过任何修订"。
    后者会让一版翻译草稿或一次失败的尝试永久挡住这道题——它再也不会被重写，
    哪怕现在已经能写对了。
    """
    row = database.connection.execute(
        "SELECT 1 FROM explanation_revisions WHERE question_version_id=?"
        " AND status IN ('REVIEWED','MACHINE_REVIEWED')"
        " AND json_extract(payload_json,'$.kind')='EXPLANATION'"
        " AND json_extract(payload_json,'$.language')=? LIMIT 1",
        (question_version_id, language)).fetchone()
    return row is not None


def latest_revision(database: Any, question_version_id: str) -> int:
    row = database.connection.execute(
        "SELECT COALESCE(MAX(revision),0) FROM explanation_revisions WHERE question_version_id=?",
        (question_version_id,)).fetchone()
    return int(row[0] or 0)


def generate(paper: dict[str, Any], profile: dict[str, Any], database: Any,
             paper_version_id: str, *, language: str = "zh",
             skip_question_ids: set[str] | None = None,
             explanation_policy: str = "DRAFT_ONLY",
             limit: int = 0, concurrency: int = 3,
             cancelled: Callable[[], bool] | None = None,
             on_progress: Callable[[int, int, int], None] | None = None,
             on_log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """给这份卷里能写的题写详解草稿。返回写了多少、跳过了哪些、为什么跳过。"""
    from .explanation_quality import verify_explanation
    from .proofread import paper_questions
    from .quality import _question_index
    from .text_model import TextModelError, ask

    versions = question_versions(database, paper_version_id)
    rows = paper_questions(paper)
    # 验证要看真实的选项与官方答案，不是压扁给模型看的那份摘要。
    questions_by_id = _question_index(paper)
    skip = set(skip_question_ids or ())
    todo: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in rows:
        qid = row["questionId"]
        if qid in skip:
            skipped.append({"questionId": qid, "reason": "转写有疑点，先处理疑点再写详解"})
        elif row["answer"] in (None, "", []):
            skipped.append({"questionId": qid, "reason": "没有记录官方答案，不让模型猜"})
        elif qid not in versions:
            skipped.append({"questionId": qid, "reason": "这一版里找不到对应题目版本"})
        elif delivered_explanation(database, versions[qid], language):
            # 只有"这个语言的解析已经交付"才跳过。原来是"有任何修订就跳过"——
            # 一版翻译草稿、一次失败的尝试，都会永久挡住这道题以后再也写不出正确
            # 解析来（规范 §12.1.7）。
            skipped.append({"questionId": qid, "reason": "已有交付中的解析，不覆盖"})
        else:
            todo.append(row)
    if limit:
        for row in todo[limit:]:
            skipped.append({"questionId": row["questionId"], "reason": "超出本次生成上限"})
        todo = todo[:limit]

    written: list[dict[str, Any]] = []
    errors: list[str] = []
    # 本地推理服务能同时接几条请求，一道题一道题排队等的是网络和解码，不是显卡。
    # 并发 3 条是实测下来既能压住排队、又不会把别的任务挤掉的档位。
    # 写库仍然串行：save_explanation 要读最新修订号再写，两条并发会互相撞乐观锁。
    write_lock = threading.Lock()
    done = 0

    def one(row: dict[str, Any]) -> None:
        nonlocal done
        qvid = versions[row["questionId"]]
        try:
            raw = ask(profile, TEMPLATE.format(
                question=json.dumps(row, ensure_ascii=False, indent=1)), system=SYSTEM)
            payload = _payload(row, parse_sections(raw), profile["model"], language)
            # 生成和验证分开留证据。给了模型官方答案再要它解释，属于条件生成 ——
            # "解释支持这个答案"不是独立的正确性证明，所以验证只认确定性的那几项，
            # 验不过或验不了的留在草稿，宁可"暂缺详解"也不放不可信的解析出去。
            status, verification = "DRAFT", None
            if explanation_policy == "AUTO_VERIFIED":
                verdict = verify_explanation(payload, questions_by_id.get(row["questionId"], {}))
                if verdict.deliverable:
                    status, verification = "MACHINE_REVIEWED", verdict.as_dict()
                else:
                    payload = {**payload, "verification": verdict.as_dict()}
            with write_lock:
                saved = database.save_explanation(
                    qvid, payload, base_revision=latest_revision(database, qvid),
                    status=status, verification=verification)
                written.append({"questionId": row["questionId"], "questionVersionId": qvid,
                                "revisionId": saved["revisionId"],
                                "revision": saved["revision"], "status": status})
            if on_log:
                label = "机审通过" if status == "MACHINE_REVIEWED" else "草稿"
                on_log(f"  ✓ {row['label']} 详解{label}第 {saved['revision']} 版")
        except (TextModelError, ValueError, TypeError, KeyError) as exc:
            with write_lock:
                errors.append(f"{row['label']}: {type(exc).__name__}: {str(exc)[:160]}")
            if on_log:
                on_log(f"  ✗ {row['label']} 写不成：{str(exc)[:120]}")
        finally:
            with write_lock:
                done += 1
                if on_progress:
                    on_progress(done, len(todo), len(errors))

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = [pool.submit(one, row) for row in todo]
        for future in as_completed(futures):
            future.result()
            if cancelled and cancelled():
                for pending in futures:
                    pending.cancel()
                break

    return {"model": profile["model"], "language": language,
            "policy": explanation_policy,
            "status": "MACHINE_REVIEWED" if explanation_policy == "AUTO_VERIFIED" else "DRAFT",
            "delivered": sum(1 for w in written if w.get("status") == "MACHINE_REVIEWED"),
            "candidates": len(todo), "written": written, "skipped": skipped,
            "errors": errors,
            "note": "草稿不会显示给学习者；要人改成 REVIEWED 才会。"}
