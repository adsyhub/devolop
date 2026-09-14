"""整卷复核的结果必须能改变结局，而且不能在没查成的时候说"没问题"。

对应规范 F06 / W06：疑点要变成结构化、由服务端定级、按依赖组隔离的 findings，
高风险的进入隔离而不是只留一份日志文件。
"""

from __future__ import annotations

import pytest

from eju_bank.quality import (
    Coverage, classify, dedup_key, quarantine_scope, summarise)


def _paper(*questions):
    return {"forms": [{"formCode": "PHYSICS_JA",
                       "groups": [{"groupCode": "I", "questions": list(questions)}]}]}


def _q(qid, *, stem="正常的题干", options=("1", "2", "3", "4"), answer="2"):
    return {"questionId": qid, "printedLabel": qid,
            "stemAst": [{"type": "text", "value": stem}],
            "options": [{"key": k, "contentAst": [{"type": "text", "value": f"选项{k}"}]}
                        for k in options],
            "correctAnswer": {"optionKey": answer}}


# ── 覆盖率：没检查 ≠ 检查通过 ────────────────────────────────────────────────

def test_a_failed_run_is_not_reported_as_clean():
    """一批都没查成时，空的 findings 不能读成"全卷无疑点"。"""
    nothing_ran = Coverage(planned=4, completed=0, failed=4)
    assert nothing_ran.result == "FAIL"
    assert not nothing_ran.complete
    assert "不能当作没有问题" in nothing_ran.explain()


def test_a_partial_run_is_unknown_not_pass():
    """查了一半：结论是未知，不是通过。"""
    half = Coverage(planned=4, completed=2, failed=2)
    assert half.result == "UNKNOWN"
    cancelled = Coverage(planned=4, completed=2, cancelled=True)
    assert cancelled.result == "UNKNOWN"


def test_a_complete_run_passes():
    """全查完且没有失败，才是通过。"""
    full = Coverage(planned=3, completed=3)
    assert full.result == "PASS" and full.complete


def test_no_questions_is_not_applicable():
    assert Coverage(planned=0).result == "NOT_APPLICABLE"


# ── 定级由服务端做，不采信检测器自报 ────────────────────────────────────────

def test_a_confirmable_finding_is_confirmed_before_it_blocks():
    """答案不在选项里：服务端自己算得出，算实了才升 BLOCKER。"""
    paper = _paper(_q("q_bad", options=("1", "2"), answer="7"))
    out = classify([{"questionId": "q_bad", "kind": "answer_missing",
                     "detail": "答案 7 不在选项里"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    assert len(out) == 1
    assert out[0]["severity"] == "BLOCKER"
    assert out[0]["status"] == "QUARANTINED"
    assert out[0]["code"] == "answer.value_not_in_options"
    assert "7" in out[0]["summary"]


def test_a_confirmable_finding_the_server_disproves_is_dismissed():
    """检测器看错了：服务端复核不成立，就不该制造一条待办。"""
    paper = _paper(_q("q_ok", options=("1", "2", "3", "4"), answer="2"))
    out = classify([{"questionId": "q_ok", "kind": "answer_missing",
                     "detail": "我觉得答案不在选项里"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    assert out[0]["status"] == "DISMISSED_WITH_EVIDENCE"
    assert out[0]["severity"] == "INFO"
    assert quarantine_scope(out) == set(), "被驳回的疑点不该隔离任何题"


def test_placeholder_text_left_in_the_product_is_a_blocker():
    """占位文字留在成品里，说明这一题根本没读到。"""
    paper = _paper(_q("q_ph", stem="選択肢 (1) について答えよ"))
    out = classify([{"questionId": "q_ph", "kind": "placeholder", "detail": "有占位"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    assert out[0]["severity"] == "BLOCKER"
    assert quarantine_scope(out) == {"q_ph"}


def test_an_unconfirmable_finding_stays_suspect_and_is_quarantined():
    """服务端证实不了的高风险疑点：既不升 BLOCKER，也不放行。"""
    paper = _paper(_q("q_cut"))
    out = classify([{"questionId": "q_cut", "kind": "truncated", "detail": "题干缺半句"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    assert out[0]["severity"] == "SUSPECT"
    assert out[0]["status"] == "QUARANTINED"
    assert quarantine_scope(out) == {"q_cut"}


def test_a_finding_about_a_question_not_in_this_paper_is_dropped():
    """模型报了一道不存在的题，那是它在编，不当成发现。"""
    paper = _paper(_q("q_real"))
    out = classify([{"questionId": "q_invented", "kind": "truncated", "detail": "x"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    assert out == []


def test_an_unknown_kind_is_dropped():
    paper = _paper(_q("q_real"))
    out = classify([{"questionId": "q_real", "kind": "vibes_are_off", "detail": "x"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    assert out == []


# ── 去重与隔离范围 ──────────────────────────────────────────────────────────

def test_the_same_problem_reported_twice_is_one_finding():
    """一处跨页问题只显示一项工作，不是两项。"""
    paper = _paper(_q("q_cut"))
    raw = [{"questionId": "q_cut", "kind": "truncated", "detail": "缺半句"},
           {"questionId": "q_cut", "kind": "truncated", "detail": "又报了一次"}]
    out = classify(raw, paper, source_id="src_x", generation=1, input_digest="d0")
    assert len(out) == 1


def test_dedup_key_separates_generations_and_targets():
    base = dedup_key("src_x", 1, "q1", "content.truncated_text", "d0")
    assert base != dedup_key("src_x", 2, "q1", "content.truncated_text", "d0")
    assert base != dedup_key("src_x", 1, "q2", "content.truncated_text", "d0")
    assert base != dedup_key("src_x", 1, "q1", "content.truncated_text", "d1")
    assert base == dedup_key("src_x", 1, "q1", "content.truncated_text", "d0")


def test_quarantine_is_per_question_not_per_paper():
    """一道题的疑点不能让另外几道已验证的题一起下架。"""
    paper = _paper(_q("q_ok"), _q("q_cut"), _q("q_fine"))
    out = classify([{"questionId": "q_cut", "kind": "truncated", "detail": "缺半句"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    assert quarantine_scope(out) == {"q_cut"}


def test_summary_reports_quarantine_and_coverage_together():
    """只报隔离量会让"全部隔离"看起来像零错误；只报覆盖率会漏掉实际损失。"""
    paper = _paper(_q("q_cut"))
    out = classify([{"questionId": "q_cut", "kind": "truncated", "detail": "缺半句"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    summary = summarise(out, Coverage(planned=2, completed=1, failed=1))
    assert summary["quarantinedQuestions"] == ["q_cut"]
    assert summary["bySeverity"]["SUSPECT"] == 1
    assert summary["coverage"]["result"] == "UNKNOWN"


def test_bad_severity_or_status_is_refused():
    """枚举是封闭的：拼错的严重程度不能悄悄变成一个新级别。"""
    from eju_bank.quality import finding

    with pytest.raises(ValueError):
        finding(source_id="s", generation=1, target_key="q", code="c",
                severity="CATASTROPHIC", status="OPEN", summary="x",
                input_digest="d", detector={})
    with pytest.raises(ValueError):
        finding(source_id="s", generation=1, target_key="q", code="c",
                severity="BLOCKER", status="PROBABLY_FINE", summary="x",
                input_digest="d", detector={})


# ── 依赖组：材料坏了，依赖它的题一起隔离 ────────────────────────────────────

def _paper_with_material(material="m1", dependents=("q1", "q2", "q3"), loner="q9"):
    questions = [{**_q(qid), "materialRefs": [material]} for qid in dependents]
    questions.append({**_q(loner), "materialRefs": []})
    return {"forms": [{"formCode": "JAPANESE",
                       "groups": [{"groupCode": "I", "questions": questions}]}]}


def test_a_broken_shared_material_quarantines_its_whole_group():
    """一段阅读材料对应五个小问：材料缺一段，五题都受影响。

    只把其中一题拿掉，剩下的题指着一段残缺的材料，照样是错的（规范 §6.5）。
    """
    from eju_bank.quality import finding, resolve_quarantine

    paper = _paper_with_material()
    material_issue = finding(
        source_id="src_x", generation=1, target_key="m1",
        target_kind="MATERIAL", code="content.truncated_text",
        severity="SUSPECT", status="QUARANTINED",
        summary="共用材料被截断", input_digest="d0", detector={"id": "t"})

    drop, reasons = resolve_quarantine([material_issue], paper)
    assert drop == {"q1", "q2", "q3"}, "依赖这段材料的题应当一起隔离"
    assert "q9" not in drop, "不依赖它的题不受影响"
    assert all("共用材料" in reasons[q] for q in ("q1", "q2", "q3"))


def test_one_questions_own_problem_does_not_take_its_neighbours():
    """一道题自己的题干被截断，与它共用文章的其他题并没有问题。

    把它们一起隔离是用覆盖率换来的虚假安全。
    """
    from eju_bank.quality import resolve_quarantine

    paper = _paper_with_material()
    out = classify([{"questionId": "q1", "kind": "truncated", "detail": "题干缺半句"}],
                   paper, source_id="src_x", generation=1, input_digest="d0")
    drop, reasons = resolve_quarantine(out, paper)
    assert drop == {"q1"}
    assert reasons["q1"]


def test_dependency_groups_map_materials_to_their_questions():
    from eju_bank.quality import dependency_groups

    groups = dependency_groups(_paper_with_material())
    assert groups["m1"] == {"q1", "q2", "q3"}
