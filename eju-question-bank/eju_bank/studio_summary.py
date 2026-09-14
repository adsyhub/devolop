"""工作台的聚合读模型：一个来源当前到底是什么状态，一次读清楚。

工作台原来自己拼状态：清单里的 ``pipelineStatus``、任务列表、本次会话的变量，
前端凑出八个阶段的完成情况。三个来源不一致时以谁为准没有定义，刷新一次答案就
可能变。更要命的是它拿 ``/candidate`` 当读接口——那个接口会真的组装一遍并把
``paper.json`` 写回工作目录。于是"看一眼列表"变成了"给每一行跑一次组装"。

这个模块给出唯一权威的快照，而且**只读**：不组装、不写修订、不签署、不发布。
规范 §11.3 把这条写成硬约束，因为读接口一旦有副作用，刷新页面就会改变数据。

状态按规范 §9.2 分成四个维度，不合并成一个绿色的"成功"：

``executionState``   程序跑到哪了。部分内容被隔离，任务仍然可以正常跑完。
``qualityState``     内容可验证到什么程度。与有没有人参与无关。
``publicationState`` 实际发布了什么。由版本和范围推出来，不是由"曾经发布过"。
``manualState``      人有没有接管。只有用户明确的动作才改变它。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import MACHINE_REVIEWER
from .util import load_json


def _latest_published(database: Any, source_id: str) -> dict[str, Any] | None:
    # 能不能练，由 paper_delivery_state 说了算：paper_versions.status 只有
    # 'PUBLISHED' 这一个取值，停用是另一张表记的。只看 status 会把已停用的卷
    # 报成已发布 —— 制作台因此看不出这套卷学习者其实取不到。
    row = database.connection.execute(
        "SELECT pv.id, pv.paper_id, pv.version_number, pv.status, pv.completeness,"
        "       pv.available_modes, pv.published_at, pv.payload_json,"
        "       ds.state AS delivery_state, ds.note AS delivery_note"
        "  FROM paper_versions pv"
        "  LEFT JOIN paper_delivery_state ds ON ds.paper_version_id=pv.id"
        " WHERE json_extract(pv.payload_json,'$.source.sourceId')=?"
        " ORDER BY pv.version_number DESC LIMIT 1", (source_id,)).fetchone()
    if not row:
        return None
    payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
    return {
        "paperVersionId": row["id"], "paperId": row["paper_id"],
        "version": row["version_number"], "status": row["status"],
        "deliveryState": row["delivery_state"], "deliveryNote": row["delivery_note"],
        "completeness": row["completeness"], "publishedAt": row["published_at"],
        "reviewGrade": payload.get("reviewGrade"),
        "questionCount": payload.get("questionCount"),
        "availableModes": json.loads(row["available_modes"] or "[]"),
    }


def _page_ownership(database: Any, source_id: str) -> dict[str, int]:
    """最新一版页修订按归属分类。人工持有的页要能单独数出来。"""
    rows = database.connection.execute(
        "SELECT role, page_number, signed_by, actor_kind FROM page_revisions pr"
        " WHERE source_id=? AND NOT EXISTS ("
        "   SELECT 1 FROM page_revisions later WHERE later.source_id=pr.source_id"
        "     AND later.role=pr.role AND later.page_number=pr.page_number"
        "     AND (later.created_at, later.rowid) > (pr.created_at, pr.rowid))",
        (source_id,)).fetchall()
    counts = {"pages": 0, "machineAttested": 0, "humanSigned": 0, "humanDraft": 0,
              "unsigned": 0}
    for row in rows:
        counts["pages"] += 1
        signed, actor = row["signed_by"], row["actor_kind"]
        if signed == MACHINE_REVIEWER:
            counts["machineAttested"] += 1
        elif signed:
            counts["humanSigned"] += 1
        elif actor == "HUMAN":
            counts["humanDraft"] += 1
        else:
            counts["unsigned"] += 1
    return counts


def _quality(work_dir: Path) -> dict[str, Any]:
    """上一次复核留下的结构化结果。没有就说没有，不编一个通过。"""
    path = work_dir / "quality-findings.json"
    if not path.is_file():
        return {"present": False, "total": 0, "quarantinedQuestions": [],
                "coverage": {"result": "NOT_APPLICABLE",
                             "explanation": "本来源尚未做过整卷复核。"}}
    try:
        data = load_json(path)
    except Exception:
        return {"present": False, "total": 0, "quarantinedQuestions": [],
                "coverage": {"result": "UNKNOWN",
                             "explanation": "复核结果文件读不出来，结论未知。"}}
    data["present"] = True
    return data


def _structure(database: Any, source_id: str) -> dict[str, Any] | None:
    row = database.connection.execute(
        "SELECT id, revision, signed_by, signed_at FROM source_structure_revisions"
        " WHERE source_id=? ORDER BY revision DESC LIMIT 1", (source_id,)).fetchone()
    return dict(row) if row else None


def _quality_state(pages: dict[str, int], quality: dict[str, Any],
                   published: dict[str, Any] | None) -> str:
    if not pages["pages"]:
        return "UNCHECKED"
    coverage = (quality.get("coverage") or {}).get("result")
    quarantined = len(quality.get("quarantinedQuestions") or [])
    if coverage in {"FAIL", "UNKNOWN"}:
        # 检查没做全，就不能说内容已验证 —— 没检查和检查通过是两件事。
        return "PARTIAL_VERIFIED" if published else "CHECKING"
    if quarantined:
        return "PARTIAL_VERIFIED"
    if published and published.get("completeness") == "COMPLETE":
        return "VERIFIED"
    return "PARTIAL_VERIFIED" if published else "UNCHECKED"


def _publication_state(published: dict[str, Any] | None) -> str:
    if not published:
        return "NOT_PUBLISHED"
    if published.get("deliveryState") in {"SUSPENDED", "REVIEW_REQUIRED"}:
        return published["deliveryState"]
    return "PUBLISHED" if published.get("completeness") == "COMPLETE" else "PUBLISHED_PARTIAL"


def _manual_state(pages: dict[str, int]) -> str:
    """人有没有接管。打开编辑器不算接管，留下修订才算。"""
    if pages["humanDraft"]:
        return "EDITING"
    if pages["humanSigned"]:
        return "AVAILABLE"
    return "OFF"


def _next_action(pages: dict[str, int], quality: dict[str, Any],
                 published: dict[str, Any] | None,
                 structure: dict[str, Any] | None) -> dict[str, str]:
    """下一步该发生什么。未发布不等于"等人工"，那是前端最容易做的错误推断。"""
    # 已停用要排在结构、覆盖率之前：一套学习者取不到的卷，最该先说的是它取不到，
    # 而不是它卡在哪一步 —— 后者是在暗示"补完这步就能用"。
    if published and published.get("deliveryState") in {"SUSPENDED", "REVIEW_REQUIRED"}:
        return {"type": "RETRY_SCHEDULED",
                "message": "最新版本已停用，学习者取不到这套卷；需要重新制作。"}
    if not pages["pages"]:
        return {"type": "WAITING_INPUT", "message": "还没有页面产物，先导入并识别。"}
    if not structure:
        return {"type": "RETRY_SCHEDULED", "message": "结构基线尚未签署，自动流程会补上。"}
    coverage = (quality.get("coverage") or {}).get("result")
    if coverage in {"FAIL", "UNKNOWN"}:
        return {"type": "RETRY_SCHEDULED",
                "message": (quality.get("coverage") or {}).get("explanation")
                           or "复核覆盖不完整，需要重跑。"}
    quarantined = len(quality.get("quarantinedQuestions") or [])
    if not published:
        return {"type": "RETRY_SCHEDULED", "message": "内容已验证，等待发布。"}
    if quarantined:
        return {"type": "OPTIONAL_HUMAN_REVIEW",
                "message": f"可练内容已发布，{quarantined} 题因未能确认而隔离。"}
    return {"type": "NONE", "message": "可练内容已发布，没有待处理的疑点。"}


def source_summary(workspace: Any, database: Any, source_id: str) -> dict[str, Any]:
    """一个来源的统一状态。纯读：不组装、不写修订、不签署、不发布。"""
    manifest_path, manifest = workspace.source(source_id)
    work_dir = manifest_path.parent

    pages = _page_ownership(database, source_id)
    quality = _quality(work_dir)
    published = _latest_published(database, source_id)
    structure = _structure(database, source_id)

    quarantined = quality.get("quarantinedQuestions") or []
    verified = published.get("questionCount") if published else None
    # 期望题量没有可靠证据时就是未知。用已识别题数充当分母会让覆盖率永远好看。
    expected = None
    ratio = None

    subject = manifest.get("subject") or ""
    display = f"{manifest.get('session')} · {subject}"
    if manifest.get("language"):
        display += f" · {manifest['language']}"

    return {
        "sourceId": source_id,
        "displayName": display,
        "session": manifest.get("session"),
        "subject": subject,
        "language": manifest.get("language"),
        "expectedForms": manifest.get("expectedForms") or [],
        "roles": sorted(f["role"] for f in manifest.get("files") or []),
        "executionState": "SUCCEEDED" if published else (
            "RUNNING" if pages["pages"] else "QUEUED"),
        "qualityState": _quality_state(pages, quality, published),
        "publicationState": _publication_state(published),
        "manualState": _manual_state(pages),
        "reviewGrade": (published or {}).get("reviewGrade"),
        "pages": pages,
        "structure": ({"revision": structure["revision"],
                       "signedBy": structure["signed_by"],
                       "signedAt": structure["signed_at"]} if structure else None),
        "coverage": {
            "verifiedQuestions": verified,
            "quarantinedQuestions": len(quarantined),
            "expectedQuestions": expected,
            "ratio": ratio,
        },
        "findings": {
            "total": quality.get("total", 0),
            "bySeverity": quality.get("bySeverity") or {},
            "quarantined": len(quarantined),
            "coverage": quality.get("coverage") or {},
        },
        "published": published,
        "nextAction": _next_action(pages, quality, published, structure),
    }


def delivery_overview(database: Any) -> dict[str, Any]:
    """每个来源最新一版的交付事实：学习者到底取不取得到这套卷。

    列表页要一次画两百多套。逐套跑 :func:`source_summary` 会去读每个工作目录
    的质量报告与结构记录 —— 实测 215 套要两分多钟。那是单套详情该付的代价，
    不该摊到整屏上。这里只回答"取不取得到"，而那件事全在数据库里：一条 SQL。

    取版本的规则与交付端一致（同一 paper 的最大 version_number），否则列表会
    显示一个学习者根本拿不到的旧版本。
    """
    rows = database.connection.execute(
        "SELECT json_extract(pv.payload_json,'$.source.sourceId') AS source_id,"
        "       pv.id, pv.version_number, pv.completeness, pv.published_at,"
        "       json_extract(pv.payload_json,'$.reviewGrade')   AS review_grade,"
        "       json_extract(pv.payload_json,'$.questionCount') AS question_count,"
        "       ds.state AS delivery_state, ds.note AS delivery_note"
        "  FROM paper_versions pv"
        "  LEFT JOIN paper_delivery_state ds ON ds.paper_version_id=pv.id"
        " WHERE pv.status='PUBLISHED'"
        "   AND pv.version_number=(SELECT MAX(v.version_number) FROM paper_versions v"
        "                          WHERE v.paper_id=pv.paper_id AND v.status='PUBLISHED')"
    ).fetchall()
    sources: dict[str, Any] = {}
    counts: dict[str, int] = {}
    for row in rows:
        source_id = row["source_id"]
        if not source_id:
            continue
        published = {
            "paperVersionId": row["id"], "version": row["version_number"],
            "completeness": row["completeness"], "publishedAt": row["published_at"],
            "reviewGrade": row["review_grade"], "questionCount": row["question_count"],
            "deliveryState": row["delivery_state"], "deliveryNote": row["delivery_note"],
        }
        state = _publication_state(published)
        sources[source_id] = {"publicationState": state, "published": published}
        counts[state] = counts.get(state, 0) + 1
    return {"sources": sources, "counts": counts,
            "basis": "按每个 paper 的最大版本号取一版，与学习者取卷的规则一致；"
                     "是否可练以 paper_delivery_state 为准。"}


def studio_summary(workspace: Any, database: Any, *, limit: int = 200) -> dict[str, Any]:
    """首屏汇总。按实际交付与质量状态统计，并说明统计口径。"""
    rows = []
    for entry in workspace.list_sources()[:limit]:
        try:
            rows.append(source_summary(workspace, database, entry["sourceId"]))
        except Exception as exc:  # 一套卷读不出来不该让整个首屏空白
            rows.append({"sourceId": entry["sourceId"],
                         "displayName": entry.get("session") or entry["sourceId"],
                         "executionState": "FAILED",
                         "error": f"{type(exc).__name__}: {str(exc)[:160]}"})
    by_publication: dict[str, int] = {}
    for row in rows:
        key = row.get("publicationState") or "UNKNOWN"
        by_publication[key] = by_publication.get(key, 0) + 1
    quarantined = sum(len(r.get("findings", {}).get("quarantined", 0) and [1] or [])
                      for r in rows)
    return {
        "sources": rows,
        "counts": {
            "total": len(rows),
            "byPublicationState": by_publication,
            "withQuarantine": quarantined,
        },
        "basis": ("按每个来源的最新已发布版本与最近一次复核结果统计；"
                  "期望题量没有可靠证据时覆盖率显示未知，不用已识别题数充当分母。"),
    }
