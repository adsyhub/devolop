"""详解的机器审核与交付选择。

对应规范 F15 / W14。详解原来生成成 ``DRAFT``，而学习端只读 ``REVIEWED``，于是每
一条都要人点一下才看得见。规范要的不是把 DRAFT 改名成 REVIEWED——那只是给没审过
的东西换个名字——而是一条独立的验证通路：验得过的以机器身份交付并标明来源，验不
过或验不了的留在草稿，宁可"暂缺详解"。
"""

from __future__ import annotations

import pytest

from eju_bank.constants import MACHINE_REVIEWER
from eju_bank.errors import ContractError
from eju_bank.explanation_quality import verify_explanation


def _question(*, options=("1", "2", "3", "4"), answer="2"):
    return {"questionId": "q1",
            "options": [{"key": k, "contentAst": [{"type": "text", "value": f"选项{k}"}]}
                        for k in options],
            "correctAnswer": {"optionKey": answer}}


def _payload(text, *, kind="EXPLANATION", language="zh"):
    return {"kind": kind, "language": language,
            "contentAst": [{"type": "paragraph", "value": text}]}


# ── 确定性验证 ──────────────────────────────────────────────────────────────

def test_a_sound_explanation_passes():
    verdict = verify_explanation(
        _payload("由能量守恒可得该过程的功为零，因此正确答案是 2，其余选项与守恒律矛盾。"),
        _question())
    assert verdict.result == "PASS" and verdict.deliverable


def test_an_explanation_contradicting_the_official_answer_fails():
    """解析说了另一个答案：这是确定性的矛盾，一定不能交付。"""
    verdict = verify_explanation(
        _payload("经过推导可以看出，正确答案是 4，因为其余选项都不满足条件。"),
        _question(answer="2"))
    assert verdict.result == "FAIL" and not verdict.deliverable
    assert any(c["id"] == "explanation.matches_official_answer" and c["result"] == "FAIL"
               for c in verdict.checks)


def test_an_explanation_citing_a_nonexistent_option_fails():
    verdict = verify_explanation(
        _payload("排除其他各项之后可知，正确答案是 9，这一点由题目条件直接给出。"),
        _question(options=("1", "2", "3", "4")))
    assert verdict.result == "FAIL"


def test_an_explanation_that_states_no_answer_is_unknown_not_pass():
    """没明确说答案就无法确定性比对。未知不是通过。"""
    verdict = verify_explanation(
        _payload("这道题考查能量守恒定律，需要先分析受力再讨论做功情况以得到结论。"),
        _question())
    assert verdict.result == "UNKNOWN"
    assert not verdict.deliverable, "验证不了的解析不能交付"


def test_placeholder_and_empty_explanations_fail():
    assert verify_explanation(_payload("待录入"), _question()).result == "FAIL"
    assert verify_explanation(_payload(""), _question()).result == "FAIL"
    assert verify_explanation(_payload("太短"), _question()).result == "FAIL"


def test_a_digit_grid_question_is_unknown_not_pass():
    """数字格题没有单选正解，确定性比对不适用——那就说不适用。"""
    question = {"questionId": "q1", "options": [],
                "correctAnswer": {"tokens": {"ア": "3"}}}
    verdict = verify_explanation(
        _payload("按照题意逐步代入求解，可得所求的各位数字依次为 3 和 5。"), question)
    assert verdict.result == "UNKNOWN" and not verdict.deliverable


def test_the_verdict_states_what_it_did_not_check():
    """机器审核必须说得出自己的边界，否则它会被读成完整的正确性保证。"""
    verdict = verify_explanation(
        _payload("由能量守恒可得该过程的功为零，因此正确答案是 2，其余选项与守恒律矛盾。"),
        _question())
    limitations = verdict.as_dict()["limitations"]
    assert any("未做模型层面的语义验证" in item for item in limitations)


# ── 写入与交付选择 ──────────────────────────────────────────────────────────

@pytest.fixture
def database(tmp_path):
    from eju_bank.db import Database

    db = Database(tmp_path / "library/eju.db")
    yield db
    db.close()


def _seed_question(db):
    """建出 explanation_revisions 的外键所需的最小一条链。"""
    now = "2026-09-12T00:00:00Z"
    db.connection.execute(
        "INSERT INTO papers VALUES ('p1','CODE1','2023-2 理科',?)", (now,))
    db.connection.execute(
        "INSERT INTO paper_versions (id,paper_id,version_number,content_revision,status,"
        "channel,payload_json,created_at,published_at,completeness,available_modes,syllabus_id)"
        " VALUES ('pv1','p1',1,'r1','PUBLISHED','PRIVATE','{}',?,?,'PARTIAL','[\"PRACTICE\"]','basic-2015')",
        (now, now))
    db.connection.execute("INSERT INTO questions VALUES ('q1','PHYSICS_JA|PHYSICS:1',?)", (now,))
    db.connection.execute(
        "INSERT INTO question_versions (id,question_id,paper_version_id,version_number,"
        "form_code,answer_type,content_hash,delivery_json,answer_json,created_at)"
        " VALUES ('qv1','q1','pv1',1,'PHYSICS_JA','SINGLE_CHOICE','h1','{}','{}',?)", (now,))
    db.connection.commit()
    return "qv1"


def test_machine_reviewed_requires_a_passing_server_verification(database):
    """MACHINE_REVIEWED 不能由请求直接声称。"""
    qvid = _seed_question(database)
    with pytest.raises(ContractError):
        database.save_explanation(qvid, _payload("随便写的解析内容，足够长以通过长度检查。"),
                                  base_revision=0, status="MACHINE_REVIEWED")
    with pytest.raises(ContractError):
        database.save_explanation(qvid, _payload("随便写的解析内容，足够长以通过长度检查。"),
                                  base_revision=0, status="MACHINE_REVIEWED",
                                  verification={"result": "UNKNOWN"})


def test_machine_reviewed_is_signed_by_the_machine_not_a_person(database):
    """机器不借用人名。署名由服务端设定。"""
    qvid = _seed_question(database)
    saved = database.save_explanation(
        qvid, _payload("由能量守恒可得，正确答案是 2。"), base_revision=0,
        status="MACHINE_REVIEWED", verification={"result": "PASS", "checks": []},
        reviewer="某位专家")
    row = database.connection.execute(
        "SELECT reviewer, payload_json FROM explanation_revisions WHERE id=?",
        (saved["revisionId"],)).fetchone()
    assert row["reviewer"] == MACHINE_REVIEWER
    assert '"MACHINE_ATTESTED"' in row["payload_json"]


def test_a_human_version_outranks_a_later_machine_one(database):
    """机器候选不能仅凭修订号更大就挤掉人工已交付的版本。"""
    qvid = _seed_question(database)
    database.save_explanation(qvid, _payload("人工写的解析，这是当前交付的版本。"),
                              base_revision=0, status="REVIEWED", reviewer="审校 A")
    database.save_explanation(qvid, _payload("机器写的解析，正确答案是 2。"),
                              base_revision=1, status="MACHINE_REVIEWED",
                              verification={"result": "PASS", "checks": []})

    chosen = database._latest_annotations(qvid)
    assert len(chosen) == 1
    assert chosen[0]["status"] == "REVIEWED", "人工版本被机器版本挤掉了"
    assert chosen[0]["reviewer"] == "审校 A"


def test_a_machine_version_delivers_where_no_human_one_exists(database):
    """人工没有覆盖的位置，机器审核过的解析要真的交付。"""
    qvid = _seed_question(database)
    database.save_explanation(qvid, _payload("机器写的解析，正确答案是 2。"),
                              base_revision=0, status="MACHINE_REVIEWED",
                              verification={"result": "PASS", "checks": []})
    chosen = database._latest_annotations(qvid)
    assert len(chosen) == 1 and chosen[0]["status"] == "MACHINE_REVIEWED"


def test_a_draft_is_never_delivered(database):
    """草稿不进交付选择——机器审核不通过的就该看不见。"""
    qvid = _seed_question(database)
    database.save_explanation(qvid, _payload("没验过的草稿内容，足够长以通过长度检查。"),
                              base_revision=0, status="DRAFT")
    assert database._latest_annotations(qvid) == []


def test_verification_evidence_is_rejected_on_ordinary_statuses(database):
    """验证证据只属于机器审核。别的状态带着它，说明调用方搞错了。"""
    qvid = _seed_question(database)
    with pytest.raises(ContractError):
        database.save_explanation(qvid, _payload("人工写的解析内容，足够长以通过检查。"),
                                  base_revision=0, status="REVIEWED", reviewer="审校 A",
                                  verification={"result": "PASS"})
