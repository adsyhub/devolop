"""自动放行的五个前提，每一个都用一个能真正失败的反例钉住。

这些用例对应 ``docs/STUDIO_AUTOMATION_OPTIMIZATION_SPEC_2026-09-12.md`` 的
F01–F05，也就是规范里"扩大自动化之前必须修复"的那一组。它们检查的不是函数
返回了哪些字段，而是**错误的输入能不能被挡住**：

F01  题答错位：所有题的选项编号都一样时，错位配对与正确配对同样"通过"。
F02  证明脱钩：改了合同正文或 OCR 缓存，旧证明仍然验得过。
F03  人工被覆盖：人签过的页，自动重跑把它存回机器版本。
F04  无变化重签：输入没变的重跑，重签结构并撤销既有证书。
F05  来源误用：换了新扫描件，流水线沿用工作目录里的旧 PDF。

每条都是"通过即错"的方向：断言写的是应有行为，不是当前行为。
"""

from __future__ import annotations

import json

import pymupdf
import pytest

from eju_bank.constants import MACHINE_REVIEWER
from eju_bank.db import Database
from eju_bank.errors import ContractError, QualityGateError
from eju_bank.ocr.attested_contracts import attestation, verify_attestation
from eju_bank.ocr.slot_join import join_sections
from eju_bank.review import ContentWorkspace
from eju_bank.source import create_source_manifest
from eju_bank.util import write_json


# ── F01 题答映射 ──────────────────────────────────────────────────────────────

def _q(slot, options, *, section="物理", boxed=True):
    """一道读到了选项的题；``boxed`` 决定它是否带印在原页上的框号。"""
    return {"page": 1, "section": section, "label": f"問{slot}", "number": str(slot),
            "sub": None, "slot": None, "boxed_slot": str(slot) if boxed else None,
            "answer_prefix": "PHYSICS", "context": None, "stem": f"stem {slot}",
            "options": options, "pages": [1]}


def test_uniform_options_cannot_witness_the_pairing():
    """规范 4.1 的反例：四道题选项都是 1–4，错位配对的一致率同样是 4/4。

    ``option_agreement`` 只问"正解是不是这道题读到的某个选项"。所有题的选项域
    相同时，这个问题对正确配对和错位配对给出一模一样的答案，因此它不含任何关于
    配对的信息。放行必须看出这一点，而不是把 4/4 当成证据。
    """
    from eju_bank.ocr.slot_join import option_agreement, passes

    uniform = {str(i): f"opt{i}" for i in (1, 2, 3, 4)}
    items = [_q(n, dict(uniform), boxed=False) for n in (1, 2, 3, 4)]
    answers = {f"PHYSICS:{n}": str(n) for n in (1, 2, 3, 4)}

    # 先确认这正是规范描述的处境：正配与错配的一致率都是满分。
    correct = [(item, f"PHYSICS:{n}") for n, item in zip((1, 2, 3, 4), items)]
    shifted = [(item, f"PHYSICS:{n}") for n, item in zip((2, 3, 4, 1), items)]
    assert option_agreement(correct, answers) == (4, 4)
    assert option_agreement(shifted, answers) == (4, 4)
    assert passes(4, 4)

    # 所以顺序补号不能仅凭它放行：没有框号这类独立锚点时，映射保持未验证。
    accepted, filled, report = join_sections(items, answers, {"PHYSICS": 4})
    assert filled == 0, "选项域完全相同时，一致率不能支持顺序补号"
    assert not any(item.get("boxed_slot") for item in items)
    assert "PHYSICS" in report


def test_distinguishing_options_still_witness_the_pairing():
    """反过来也要成立：选项域能区分错位时，这份证据仍然有效。

    F01 的修复如果把所有顺序补号都关掉，就是用覆盖率换正确性。真正要去掉的只有
    "不可区分"的那一类。
    """
    # 每道题的选项域各不相同，错位一位就会立刻对不上。
    items = [{**_q(n, {str(n): "ok", "9": "no"}, boxed=False)} for n in (1, 2, 3)]
    answers = {f"PHYSICS:{n}": str(n) for n in (1, 2, 3)}

    accepted, filled, report = join_sections(items, answers, {"PHYSICS": 3})
    assert filled == 3
    assert [item["boxed_slot"] for item in items] == ["1", "2", "3"]
    assert all(item["slotSource"] == "SECTION_SEQUENCE" for item in items)


def test_gap_recovery_also_needs_a_distinguishing_check():
    """缺口之上的答案同样不能靠不可区分的一致率恢复。

    这里配对本身有框号支撑，被检验的是另一件事：正解表是否被整份读到。选项域
    完全相同时，一行错位的正解表与正确的正解表同样通过，所以它不能作为依据。
    """
    uniform = {str(i): f"opt{i}" for i in (1, 2, 3, 4)}
    items = [_q(n, dict(uniform)) for n in (1, 3, 4, 5)]
    full = {"PHYSICS:1": "1", "PHYSICS:3": "2", "PHYSICS:4": "3", "PHYSICS:5": "4"}

    accepted, _filled, report = join_sections(items, full, {"PHYSICS": 1})
    assert accepted == set(), "选项域相同时，缺口之上的答案没有得到独立验证"
    assert "PHYSICS" in report


def test_module_no_longer_claims_an_unfounded_error_rate():
    """代码里那句"错位只有约 1/5 概率通过"必须删掉。

    规范 4.1 说得很直接：由它推导出的置信度不适用于这个检查。留着这句话，下一个
    读代码的人会重新相信它。
    """
    from pathlib import Path

    text = Path(__file__).resolve().parents[1].joinpath(
        "eju_bank/ocr/slot_join.py").read_text(encoding="utf-8")
    assert "1/5" not in text
    assert "0.2^n" not in text
    assert "about one time in five" not in text


# ── F02–F04 的共用工作区 ──────────────────────────────────────────────────────

@pytest.fixture
def workspace(tmp_path):
    """一套最小但完整的来源：两份真 PDF、清单条目、OCR 缓存和数据库。"""
    sources = tmp_path / "sources"
    sources.mkdir()
    for name, text in [("question.pdf", "Choose: 1 or 2"), ("answer.pdf", "Answer: 2")]:
        doc = pymupdf.open()
        doc.new_page().insert_text((50, 50), text)
        doc.save(sources / name)
        doc.close()
    manifest = create_source_manifest(
        session="test", subject="SCIENCE", language="ja", syllabus_version="2015",
        question_booklet=sources / "question.pdf", answer_key=sources / "answer.pdf",
        rights_status="PRIVATE_STUDY", rights_note="Test only",
        output_path=tmp_path / "work/test/source-manifest.json")
    manifest["inventoryId"] = "fixture-source"
    manifest["expectedForms"] = ["PHYSICS_JA"]
    write_json(tmp_path / "work/test/source-manifest.json", manifest)

    from eju_bank.inventory import upsert_inventory_item
    upsert_inventory_item(
        {"inventoryId": "fixture-source", "session": manifest["session"],
         "subject": "SCIENCE", "language": "ja", "syllabusId": "basic-2015",
         "requiredFiles": ["QUESTION_BOOKLET", "ANSWER_KEY"],
         "rightsStatus": "PRIVATE_STUDY", "pipelineStatus": "RECEIVED",
         "expectedForms": ["PHYSICS_JA"]},
        tmp_path / "content/content-inventory.json")
    write_json(tmp_path / "work/test/ocr_cache/p0001.json",
               {"raw_text": "Choose one. ① 1 ② 2", "ocrModel": "test"})

    db = Database(tmp_path / "library/eju.db")
    workspace = ContentWorkspace(tmp_path, db)
    yield workspace, db, manifest["sourceId"], tmp_path / "work/test"
    db.close()


def _contract(work_dir, *, stem="Choose one."):
    """一份流水线会认为可以证明的题册页合同。"""
    block = {"kind": "question", "localKey": "q1", "formCode": "PHYSICS_JA", "groupCode": "I",
             "answerRef": "PHYSICS:1", "printedLabel": "1", "bbox": [.08, .08, .92, .92],
             "stemAst": [{"type": "text", "value": stem}],
             "options": [{"key": str(i), "contentAst": [{"type": "text", "value": str(i)}]}
                         for i in (1, 2)],
             "answerSpec": {"type": "SINGLE_CHOICE"}, "materialRefs": [],
             "answerRefEvidence": "PRINTED_SLOT",
             "regionIds": ["p0001-text-01"], "readingOrder": 1}
    contract = {"schemaVersion": 2, "page": 1, "sourceFileRole": "QUESTION_BOOKLET",
                "blocks": [block],
                "coverage": {"inkRegions": 1, "accountedRegions": 1,
                             "regionIds": ["p0001-text-01"],
                             "accountedRegionIds": ["p0001-text-01"],
                             "regionEvidence": "TEXT_ORDER_ONLY"},
                "issues": []}
    from eju_bank.ocr.attested_contracts import REQUIRED_CHECKS

    contract["attestation"] = attestation(
        work_dir, 1, answer_cache=None,
        checks=sorted(REQUIRED_CHECKS["QUESTION_BOOKLET"]), contract=contract)
    return contract


def _answer_contract(work_dir):
    """配套的正解表页合同，组卷时的答案台账由它提供。"""
    from eju_bank.ocr.attested_contracts import REQUIRED_CHECKS

    block = {"kind": "answer-entry", "formCode": "PHYSICS_JA", "answerRef": "PHYSICS:1",
             "answerType": "SINGLE_CHOICE", "correctOption": "2",
             "bbox": [.08, .08, .92, .92], "regionIds": ["p0001-text-01"],
             "readingOrder": 1}
    contract = {"schemaVersion": 2, "page": 1, "sourceFileRole": "ANSWER_KEY",
                "blocks": [block],
                "coverage": {"inkRegions": 1, "accountedRegions": 1,
                             "regionIds": ["p0001-text-01"],
                             "accountedRegionIds": ["p0001-text-01"],
                             "regionEvidence": "TEXT_ORDER_ONLY"},
                "issues": []}
    contract["attestation"] = attestation(
        work_dir, 1, answer_cache=None,
        checks=sorted(REQUIRED_CHECKS["ANSWER_KEY"]), contract=contract)
    return contract


def _attest_page(workspace, source_id, role, contract):
    current = workspace.read_page(source_id, role, 1)
    saved = workspace.save_page(source_id, role, 1, contract, current["revisionId"])
    return workspace.attest_page(source_id, role, 1, saved["revisionId"])


def _attest(workspace, source_id, work_dir, contract=None):
    """题册页；组卷用的正解表页一并备好。"""
    _attest_page(workspace, source_id, "ANSWER_KEY", _answer_contract(work_dir))
    return _attest_page(workspace, source_id, "QUESTION_BOOKLET",
                        contract or _contract(work_dir))


# ── F02 证明必须绑定正文与真实产物 ────────────────────────────────────────────

def test_attestation_does_not_survive_an_edited_stem(workspace):
    """改掉题干，原来的证明必须失效。

    证明说的是"这页的正文来自这份 OCR"。如果它只对自己的摘要自洽，那么换掉题干
    之后它依然验得过 —— 它证明的就只是它自己。
    """
    _ws, _db, _source_id, work_dir = workspace
    contract = _contract(work_dir)
    assert verify_attestation(contract, work_dir=work_dir) == []

    tampered = json.loads(json.dumps(contract))
    tampered["blocks"][0]["stemAst"] = [{"type": "text", "value": "Something else entirely."}]
    problems = verify_attestation(tampered, work_dir=work_dir)
    assert problems, "改了题干，证明仍然成立"


def test_attestation_does_not_survive_an_edited_answer_reference(workspace):
    """换掉 answerRef 等于换掉这道题的正解，证明必须跟着失效。"""
    _ws, _db, _source_id, work_dir = workspace
    tampered = json.loads(json.dumps(_contract(work_dir)))
    tampered["blocks"][0]["answerRef"] = "PHYSICS:7"
    assert verify_attestation(tampered, work_dir=work_dir)


def test_attestation_does_not_survive_a_rewritten_ocr_cache(workspace):
    """证明记下了 OCR 缓存的摘要，就必须真的拿它和盘上的文件比。"""
    _ws, _db, _source_id, work_dir = workspace
    contract = _contract(work_dir)
    assert verify_attestation(contract, work_dir=work_dir) == []

    write_json(work_dir / "ocr_cache/p0001.json",
               {"raw_text": "完全不同的一页", "ocrModel": "test"})
    problems = verify_attestation(contract, work_dir=work_dir)
    assert problems, "OCR 缓存被改写，证明仍然成立"


def test_a_self_consistent_forgery_is_refused(workspace):
    """自己算一个自洽的摘要不构成证明。

    只要重算 ``payloadDigest`` 就能让伪造的证明自洽，所以自洽不能是验证的全部。
    """
    from eju_bank.util import digest_json

    ws, _db, source_id, work_dir = workspace
    contract = _contract(work_dir)
    forged = json.loads(json.dumps(contract))
    forged["blocks"][0]["stemAst"] = [{"type": "text", "value": "Forged stem."}]
    att = forged["attestation"]
    att.pop("payloadDigest", None)
    att["payloadDigest"] = digest_json(att)

    assert verify_attestation(forged, work_dir=work_dir)
    current = ws.read_page(source_id, "QUESTION_BOOKLET", 1)
    saved = ws.save_page(source_id, "QUESTION_BOOKLET", 1, forged, current["revisionId"])
    with pytest.raises(QualityGateError):
        ws.attest_page(source_id, "QUESTION_BOOKLET", 1, saved["revisionId"])


def test_unknown_or_missing_checks_are_refused(workspace):
    """检查项集合由服务端登记：不认识的项、缺了必需项，都不能获得证明。"""
    _ws, _db, _source_id, work_dir = workspace
    unknown = _contract(work_dir)
    unknown["attestation"]["checks"] = ["answer.definitely_fine"]
    assert verify_attestation(unknown, work_dir=work_dir)

    empty = _contract(work_dir)
    empty["attestation"]["checks"] = []
    assert verify_attestation(empty, work_dir=work_dir)


# ── F03 人工成果不被自动流程覆盖 ──────────────────────────────────────────────

def test_rerun_does_not_overwrite_a_signed_page(workspace):
    """人签过的页，自动重跑不能把它存回机器版本。

    ``already_cleared`` 见到 ``signed_by`` 不是机器身份就返回 False，于是
    ``clear_source`` 落到 ``save_page`` 那一支 —— 人的修订被机器合同顶掉，
    基于它的证书也一并撤销。
    """
    from eju_bank.attest import already_cleared, human_locked, publishable

    ws, _db, source_id, work_dir = workspace
    contract = _contract(work_dir)
    _attest(ws, source_id, work_dir, contract)

    human = json.loads(json.dumps(contract))
    human["blocks"][0]["stemAst"] = [{"type": "text", "value": "人工订正过的题干"}]
    human.pop("attestation", None)
    current = ws.read_page(source_id, "QUESTION_BOOKLET", 1)
    saved = ws.save_page(source_id, "QUESTION_BOOKLET", 1, human, current["revisionId"])
    signed = ws.sign_page(source_id, "QUESTION_BOOKLET", 1, saved["revisionId"],
                          "审校 A", True)
    assert signed["signedBy"] == "审校 A"

    # 自动流水线带着它自己的合同回来了。逐字比较当然不等，但那不是覆盖的理由。
    assert human_locked(signed) is True, "人签页必须被认作人工持有"
    assert publishable(signed) is True, "人签页照旧进发布范围"
    assert already_cleared(signed, contract) is False

    after = ws.read_page(source_id, "QUESTION_BOOKLET", 1)
    assert after["signedBy"] == "审校 A"
    assert after["contract"]["blocks"][0]["stemAst"][0]["value"] == "人工订正过的题干"


def test_rerun_does_not_overwrite_an_unsigned_human_draft(workspace):
    """人保存过但还没签的修订同样受保护。

    规范 7.3：不能只靠 ``signed_by`` 判断人工成果 —— 草稿也是人做的。保护它和
    发布它是两件事：草稿留着，但不进发布范围。
    """
    from eju_bank.attest import human_locked, publishable

    ws, _db, source_id, work_dir = workspace
    contract = _contract(work_dir)
    _attest(ws, source_id, work_dir, contract)

    human = json.loads(json.dumps(contract))
    human["blocks"][0]["stemAst"] = [{"type": "text", "value": "人工草稿"}]
    human.pop("attestation", None)
    current = ws.read_page(source_id, "QUESTION_BOOKLET", 1)
    draft = ws.save_page(source_id, "QUESTION_BOOKLET", 1, human,
                         current["revisionId"], reviewer="审校 A")

    assert draft["actorKind"] == "HUMAN" and draft["authoredBy"] == "审校 A"
    assert human_locked(draft) is True, "人工草稿不能被机器合同顶掉"
    assert publishable(draft) is False, "没签的草稿不因为被保护就获得发布资格"


def test_machine_pages_are_still_refreshed_when_the_content_changes(workspace):
    """保护不能变成僵死：机器自己写的页，内容变了就该更新。"""
    from eju_bank.attest import already_cleared, human_locked

    ws, _db, source_id, work_dir = workspace
    contract = _contract(work_dir)
    attested = _attest(ws, source_id, work_dir, contract)

    assert human_locked(attested) is False
    assert already_cleared(attested, contract) is True
    assert already_cleared(attested, _contract(work_dir, stem="新的识别结果")) is False


# ── F04 无变化重跑零副作用 ────────────────────────────────────────────────────

def _structure(workspace, source_id):
    ws, _db, _sid, _work = workspace
    return ws.proposed_structure(source_id, cleared_pages={"QUESTION_BOOKLET": [1],
                                                           "ANSWER_KEY": [1]},
                                 expected_forms=["PHYSICS_JA"])[0]


def test_unchanged_structure_is_not_resigned(workspace):
    """内容和依赖都没变时，重签必须是空操作。

    现在每次 ``sign_source_structure`` 都插入新修订，并撤销这个来源上所有整卷
    证书 —— 一次无意义的重跑就把已发布的卷全挂起了。
    """
    ws, db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    structure = _structure(workspace, source_id)

    first = ws.sign_source_structure(source_id, structure, MACHINE_REVIEWER)
    second = ws.sign_source_structure(source_id, structure, MACHINE_REVIEWER)

    assert second["revision"] == first["revision"], "结构没变却产生了新的基线修订"
    assert second["structureRevisionId"] == first["structureRevisionId"]
    count = db.connection.execute(
        "SELECT COUNT(*) FROM source_structure_revisions WHERE source_id=?",
        (source_id,)).fetchone()[0]
    assert count == 1


def test_unchanged_structure_does_not_revoke_existing_certificates(workspace):
    """无变化重跑不能撤销既有的整卷证书。"""
    ws, db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    structure = _structure(workspace, source_id)
    ws.sign_source_structure(source_id, structure, MACHINE_REVIEWER)

    revoked_before = db.connection.execute(
        "SELECT COUNT(*) FROM paper_review_revocations").fetchone()[0]
    ws.sign_source_structure(source_id, structure, MACHINE_REVIEWER)
    revoked_after = db.connection.execute(
        "SELECT COUNT(*) FROM paper_review_revocations").fetchone()[0]

    assert revoked_after == revoked_before, "结构没变却撤销了证书"


def test_a_changed_structure_is_still_signed_afresh(workspace):
    """真的变了就必须换基线 —— 幂等不能变成"永远不更新"。"""
    ws, _db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    structure = _structure(workspace, source_id)
    first = ws.sign_source_structure(source_id, structure, MACHINE_REVIEWER)

    changed = json.loads(json.dumps(structure))
    changed["forms"]["PHYSICS_JA"] = list(changed["forms"]["PHYSICS_JA"]) + ["PHYSICS:99"]
    second = ws.sign_source_structure(source_id, changed, MACHINE_REVIEWER)

    assert second["revision"] == first["revision"] + 1


# ── F05 来源身份 ──────────────────────────────────────────────────────────────

def _upload(root, name, text):
    """按真实上传通道落一份 PDF，返回它的上传句柄。"""
    from eju_bank.uploads import store

    doc = pymupdf.open()
    doc.new_page().insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return store(root, name, data)["uploadId"]


def test_a_new_scan_is_not_silently_replaced_by_the_old_one(tmp_path):
    """同一场次科目换了新扫描件，不能沿用工作目录里的旧 PDF。

    ``register()`` 只看 ``work/<name>/source-manifest.json`` 在不在，在就整份复用。
    用户上传的是新文件，流水线读的是旧文件，而且什么都不会说。
    """
    from eju_bank.make_paper import Run, register

    root = tmp_path
    first_booklet = _upload(root, "booklet-v1.pdf", "First scan, question 1")
    first_key = _upload(root, "key-v1.pdf", "First scan, answer 1")
    second_booklet = _upload(root, "booklet-v2.pdf", "Second scan, corrected question 1")
    second_key = _upload(root, "key-v2.pdf", "Second scan, corrected answer 1")

    db = Database(root / "library/eju.db")
    try:
        params = {"session": "2023-2", "subject": "SCIENCE", "course": "PHYSICS",
                  "language": "ja"}
        first = register(Run(lambda _: None), root, db,
                         {**params, "questionBooklet": first_booklet,
                          "answerKey": first_key})[1]
        original = {f["role"]: f["sha256"] for f in first["files"]}

        # 第二次提交的是不同的文件。沿用旧清单是错的答案。
        try:
            second = register(Run(lambda _: None), root, db,
                              {**params, "questionBooklet": second_booklet,
                               "answerKey": second_key})[1]
        except ContractError:
            return  # 明确拒绝也是正确处置：用户得到的是错误，不是错的卷。

        replaced = {f["role"]: f["sha256"] for f in second["files"]}
        assert replaced["QUESTION_BOOKLET"] != original["QUESTION_BOOKLET"], \
            "上传了新扫描件，流水线却沿用了旧 PDF"
        assert second["sourceId"] != first["sourceId"], \
            "文件变了就是新的来源版本，不能复用同一个 sourceId"
    finally:
        db.close()


def test_resubmitting_the_same_files_reuses_the_source(tmp_path):
    """反过来，同样的文件再提交一次必须复用，不能每次都新建来源。"""
    from eju_bank.make_paper import Run, register

    root = tmp_path
    booklet = _upload(root, "booklet.pdf", "Question 1")
    key = _upload(root, "key.pdf", "Answer 1")

    db = Database(root / "library/eju.db")
    try:
        params = {"session": "2023-2", "subject": "SCIENCE", "course": "PHYSICS",
                  "language": "ja", "questionBooklet": booklet, "answerKey": key}
        first = register(Run(lambda _: None), root, db, dict(params))[1]
        second = register(Run(lambda _: None), root, db, dict(params))[1]
        assert second["sourceId"] == first["sourceId"]
    finally:
        db.close()


def test_a_late_answer_key_is_accepted_without_a_new_source(tmp_path):
    """后补答案册是正常流程，不能被来源身份检查一并挡掉。

    sourceId 由题册内容派生，题册没变它就不变，所以补一份正解表既不是新来源，
    也不该要求用户换工作目录。
    """
    from eju_bank.make_paper import Run, register

    root = tmp_path
    booklet = _upload(root, "booklet.pdf", "Question 1")
    key = _upload(root, "key.pdf", "Answer 1")

    db = Database(root / "library/eju.db")
    try:
        params = {"session": "2023-2", "subject": "SCIENCE", "course": "PHYSICS",
                  "language": "ja", "questionBooklet": booklet}
        first = register(Run(lambda _: None), root, db, dict(params))[1]
        assert [f["role"] for f in first["files"]] == ["QUESTION_BOOKLET"]

        second = register(Run(lambda _: None), root, db,
                          {**params, "answerKey": key})[1]
        assert second["sourceId"] == first["sourceId"], "补答案册不改变来源身份"
        assert {f["role"] for f in second["files"]} == {"QUESTION_BOOKLET", "ANSWER_KEY"}
    finally:
        db.close()


def test_a_replaced_answer_key_is_refused(tmp_path):
    """换掉已登记的正解表会改变全部题答对应，不能就地覆盖。"""
    from eju_bank.make_paper import Run, register

    root = tmp_path
    booklet = _upload(root, "booklet.pdf", "Question 1")
    first_key = _upload(root, "key-v1.pdf", "Answer 1")
    other_key = _upload(root, "key-v2.pdf", "Answer 2 corrected")

    db = Database(root / "library/eju.db")
    try:
        params = {"session": "2023-2", "subject": "SCIENCE", "course": "PHYSICS",
                  "language": "ja", "questionBooklet": booklet}
        register(Run(lambda _: None), root, db, {**params, "answerKey": first_key})
        with pytest.raises(ContractError):
            register(Run(lambda _: None), root, db, {**params, "answerKey": other_key})
    finally:
        db.close()


# ── F20 完整卷不能被写死成部分卷 ──────────────────────────────────────────────

def test_scope_is_chosen_not_hardcoded(workspace):
    """自动发布原来写死 REVIEWED_PARTIAL，识别改好也永远发不出完整卷。

    完整性由 ``candidate(scope="FULL")`` 的门禁判断，这里只验证「会去试」：
    这套 fixture 的正解表还有没收录的欄位，所以结果应当是带理由的部分卷，
    而不是一个没人问过的默认值。
    """
    from eju_bank.attest import choose_scope

    ws, _db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    structure = _structure(workspace, source_id)
    ws.sign_source_structure(source_id, structure, MACHINE_REVIEWER)

    scope, candidate, why = choose_scope(ws, source_id)
    assert scope in {"FULL", "REVIEWED_PARTIAL"}
    assert why, "退回部分卷必须说得出原因"
    assert candidate["paper"]["reviewScope"] == scope
    if scope == "REVIEWED_PARTIAL":
        assert candidate["paper"]["completeness"] == "PARTIAL"
        assert "未达完整卷条件" in why
    else:
        assert candidate["paper"]["completeness"] == "COMPLETE"


def test_the_published_scope_matches_the_assembled_one(workspace):
    """签署用的 scope 必须和组装候选时的一致，否则摘要对不上。"""
    from eju_bank.attest import baseline_and_candidate

    ws, _db, source_id, work_dir = workspace
    _attest(ws, source_id, work_dir)
    staged = baseline_and_candidate(ws, {"sourceId": source_id,
                                         "expectedForms": ["PHYSICS_JA"]},
                                    {"QUESTION_BOOKLET": [1], "ANSWER_KEY": [1]})
    assert staged["scope"] == staged["candidate"]["paper"]["reviewScope"]
    assert staged["scopeReason"]
