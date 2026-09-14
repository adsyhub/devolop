"""A machine attestation must clear content for release without ever posing as a person."""
import copy
import json
import sqlite3
from pathlib import Path

import pymupdf
import pytest

from eju_bank.constants import MACHINE_REVIEWER
from eju_bank.db import Database
from eju_bank.errors import QualityGateError
from eju_bank.ocr.answer_key_contracts import build_answer_key_contract, trusted_runs, explained_gaps
from eju_bank.ocr.attested_contracts import (
    GRADE, attestation, build_question_contract, verify_attestation)
from eju_bank.review import ContentWorkspace
from eju_bank.source import create_source_manifest
from eju_bank.util import write_json


@pytest.fixture
def workspace(tmp_path):
    sources = tmp_path / 'sources'; sources.mkdir()
    for name, text in [('question.pdf', 'Choose: 1 or 2'), ('answer.pdf', 'Answer: 2')]:
        doc = pymupdf.open(); page = doc.new_page(); page.insert_text((50, 50), text)
        doc.save(sources / name); doc.close()
    manifest = create_source_manifest(
        session='test', subject='SCIENCE', language='ja', syllabus_version='2015',
        question_booklet=sources / 'question.pdf', answer_key=sources / 'answer.pdf',
        rights_status='PRIVATE_STUDY', rights_note='Test only',
        output_path=tmp_path / 'work/test/source-manifest.json')
    manifest['inventoryId'] = 'fixture-source'
    manifest['expectedForms'] = ['PHYSICS_JA']
    write_json(tmp_path / 'work/test/source-manifest.json', manifest)
    from eju_bank.inventory import upsert_inventory_item
    upsert_inventory_item({'inventoryId': 'fixture-source', 'session': manifest['session'],
                           'subject': 'SCIENCE', 'language': 'ja', 'syllabusId': 'basic-2015',
                           'requiredFiles': ['QUESTION_BOOKLET', 'ANSWER_KEY'],
                           'rightsStatus': 'PRIVATE_STUDY', 'pipelineStatus': 'RECEIVED',
                           'expectedForms': ['PHYSICS_JA']},
                          tmp_path / 'content/content-inventory.json')
    # 证明要记录它核对过的 OCR 缓存摘要，所以缓存必须真实存在。
    write_json(tmp_path / 'work/test/ocr_cache/p0001.json',
               {'raw_text': 'Choose one. ① 1 ② 2', 'ocrModel': 'test'})
    db = Database(tmp_path / 'library/eju.db')
    ws = ContentWorkspace(tmp_path, db)
    yield ws, db, manifest['sourceId'], tmp_path / 'work/test'
    db.close()


def attested(role, work_dir):
    """A contract shaped the way the pipeline emits an attestable one."""
    if role == 'QUESTION_BOOKLET':
        block = {'kind': 'question', 'localKey': 'q1', 'formCode': 'PHYSICS_JA', 'groupCode': 'I',
                 'answerRef': 'PHYSICS:1', 'printedLabel': '1', 'bbox': [.08, .08, .92, .92],
                 'stemAst': [{'type': 'text', 'value': 'Choose one.'}],
                 'options': [{'key': str(i), 'contentAst': [{'type': 'text', 'value': str(i)}]}
                             for i in (1, 2)],
                 'answerSpec': {'type': 'SINGLE_CHOICE'}, 'materialRefs': []}
    else:
        block = {'kind': 'answer-entry', 'formCode': 'PHYSICS_JA', 'answerRef': 'PHYSICS:1',
                 'answerType': 'SINGLE_CHOICE', 'correctOption': '2', 'bbox': [.08, .08, .92, .92]}
    block['regionIds'] = ['p0001-text-01']
    block['readingOrder'] = 1
    if role == 'QUESTION_BOOKLET':
        block['answerRefEvidence'] = 'PRINTED_SLOT'
    contract = {'schemaVersion': 2, 'page': 1, 'sourceFileRole': role, 'blocks': [block],
                'coverage': {'inkRegions': 1, 'accountedRegions': 1,
                             'regionIds': ['p0001-text-01'],
                             'accountedRegionIds': ['p0001-text-01'],
                             'regionEvidence': 'TEXT_ORDER_ONLY'},
                'issues': []}
    # 证明要绑定它所说的那份正文，并覆盖本角色登记的必需检查项。
    from eju_bank.ocr.attested_contracts import REQUIRED_CHECKS
    contract['attestation'] = attestation(
        work_dir, 1, answer_cache=None,
        checks=sorted(REQUIRED_CHECKS[role]), contract=contract)
    return contract


def clear(ws, source_id, work_dir, role):
    current = ws.read_page(source_id, role, 1)
    saved = ws.save_page(source_id, role, 1, attested(role, work_dir), current['revisionId'])
    return ws.attest_page(source_id, role, 1, saved['revisionId'])


def test_attested_pages_publish_and_stay_labelled_as_machine_work(workspace):
    ws, db, source_id, work_dir = workspace
    for role in ('QUESTION_BOOKLET', 'ANSWER_KEY'):
        page = clear(ws, source_id, work_dir, role)
        assert page['signedBy'] == MACHINE_REVIEWER

    cleared = {'QUESTION_BOOKLET': [1], 'ANSWER_KEY': [1]}
    structure, _, _ = ws.proposed_structure(source_id, cleared_pages=cleared,
                                            expected_forms=['PHYSICS_JA'])
    ws.sign_source_structure(source_id, structure, MACHINE_REVIEWER)
    candidate = ws.candidate(source_id, 'REVIEWED_PARTIAL')
    assert candidate['paper']['reviewGrade'] == 'MACHINE_ATTESTED'
    assert candidate['paper']['contentKind'] == 'SOURCE'

    from eju_bank.audit import review_content_digest
    review = ws.approve_paper(source_id, review_content_digest(candidate['paper']),
                              MACHINE_REVIEWER, True, 'REVIEWED_PARTIAL')
    result = ws.publish_review(review['reviewId'], 'PRIVATE')
    assert result['paperId']

    # 机器清出的页，决定类型永远不是 APPROVED：审计追溯时两者必须能分开。
    decisions = {row[0] for row in db.connection.execute('SELECT decision FROM review_decisions')}
    assert decisions == {'MACHINE_ATTESTED'}
    # 学习者看到的卷单上也带着这个等级。
    listed = {p['paperId']: p for p in db.list_papers()}
    assert listed[result['paperId']]['reviewGrade'] == 'MACHINE_ATTESTED'


def test_attestation_cannot_be_forged_or_used_on_a_draft(workspace):
    ws, db, source_id, work_dir = workspace
    role = 'QUESTION_BOOKLET'

    # 没有证明的合约不能走证明通道。
    plain = attested(role, work_dir); plain.pop('attestation')
    current = ws.read_page(source_id, role, 1)
    saved = ws.save_page(source_id, role, 1, plain, current['revisionId'])
    with pytest.raises(QualityGateError):
        ws.attest_page(source_id, role, 1, saved['revisionId'])

    # 改了内容却不改摘要：证明不成立。
    tampered = attested(role, work_dir)
    tampered['attestation']['checks'] = ['everything.is.fine']
    saved = ws.save_page(source_id, role, 1, tampered, ws.read_page(source_id, role, 1)['revisionId'])
    with pytest.raises(QualityGateError):
        ws.attest_page(source_id, role, 1, saved['revisionId'])

    # 草稿、或仍有未解决问题的合约，都不能被证明。
    for mutate in ({'needsReview': True}, {'issues': [{'severity': 'error', 'code': 'x', 'message': 'y'}]}):
        draft = attested(role, work_dir); draft.update(mutate)
        saved = ws.save_page(source_id, role, 1, draft,
                             ws.read_page(source_id, role, 1)['revisionId'])
        with pytest.raises(QualityGateError):
            ws.attest_page(source_id, role, 1, saved['revisionId'])

    # 区域与块不是一一对应时也不成立。
    broken = attested(role, work_dir)
    broken['blocks'][0]['regionIds'] = ['p0001-text-01', 'p0001-text-01']
    assert verify_attestation(broken)


def test_human_signature_replaces_the_machine_attestation(workspace):
    ws, db, source_id, work_dir = workspace
    role = 'ANSWER_KEY'
    clear(ws, source_id, work_dir, role)
    latest = ws.read_page(source_id, role, 1)
    assert latest['contract']['attestation']['grade'] == GRADE

    signed = ws.sign_page(source_id, role, 1, latest['revisionId'], 'human-reviewer', True)
    assert signed['signedBy'] == 'human-reviewer'
    # 人的签名取代机器证明，而不是继承它。
    assert 'attestation' not in signed['contract']
    # 这份合约的区域证据是什么性质，仍然照实保留。
    assert signed['contract']['coverage']['regionEvidence'] == 'TEXT_ORDER_ONLY'
    grades = ws.page_review_grades(source_id, [signed['revisionId']])
    assert set(grades.values()) == {'HUMAN_SIGNED'}


def _answer_page(text):
    return {'raw_text': text}


def test_unexplained_slot_gap_truncates_a_section_but_an_explained_one_does_not():
    forms = ['PHYSICS_JA']
    # 物理 1..3 与 5：4 号既没读到也没有说明，4 之后一概不采用。
    contracts = {1: build_answer_key_contract(1, _answer_page(
        '物理\n解答欄 1 2 3 5\n答 1 2 3 4'), forms=forms)}
    refs = [b['answerRef'] for b in contracts[1]['blocks'] if b['kind'] == 'answer-entry']
    if refs:
        trusted, notes = trusted_runs(contracts, explained_gaps(contracts))
        assert trusted.get('PHYSICS', 0) <= 3
        if trusted.get('PHYSICS', 0) < 5:
            assert 'PHYSICS' in notes and '缺口' in notes['PHYSICS']

    # 解析器自己报告「某欄的正解读不出」时，那个空缺是有解释的，不截断后面的号。
    explained = {1: {'blocks': [
        {'kind': 'answer-entry', 'answerType': 'SINGLE_CHOICE', 'answerRef': 'PHYSICS:1'},
        {'kind': 'answer-entry', 'answerType': 'SINGLE_CHOICE', 'answerRef': 'PHYSICS:3'}],
        'sectionDisputes': {'PHYSICS': ['表格: 物理 解答番号 2 的正解读不出：\'\'']}}}
    trusted, _ = trusted_runs(explained, explained_gaps(explained))
    assert trusted['PHYSICS'] == 3


def test_unverifiable_questions_are_excluded_with_a_stated_reason(tmp_path):
    work = tmp_path / 'work/src'
    write_json(work / 'ocr_cache/p0005.json',
               {'raw_text': '問1 これは本文です。 ① 甲 ② 乙'})
    items = [{'page': 5, 'section': '物理', 'label': '問1', 'number': '1', 'sub': None,
              'slot': '1', 'boxed_slot': None, 'answer_prefix': 'PHYSICS', 'context': None,
              'stem': 'これは本文です。', 'options': {'1': '甲', '2': '乙'}}]

    # 正解表里没有这一欄时，题目不是被悄悄丢掉，而是留下一个写明理由的处置。
    contract = build_question_contract(work, 5, forms=['PHYSICS_JA'], items=items, answers={})
    assert contract.get('needsReview') is True
    assert 'attestation' not in contract
    ignored = [b for b in contract['blocks'] if b['kind'] == 'ignored']
    assert ignored and '正解表' in ignored[0]['reason']
    assert contract['excludedOnThisPage']

    # 答案齐备时同一道题可以被证明，且证明声明了区域证据的性质。
    ok = build_question_contract(work, 5, forms=['PHYSICS_JA'], items=items,
                                 answers={'PHYSICS:1': '2'})
    assert not ok.get('needsReview')
    assert ok['attestation']['grade'] == GRADE
    assert ok['attestation']['regionEvidence'] == 'TEXT_ORDER_ONLY'
    assert ok['coverage']['regionEvidence'] == 'TEXT_ORDER_ONLY'
    assert verify_attestation(ok) == []
    # 答案必须确实在读到的选项里，否则同样不收录。
    wrong = build_question_contract(work, 5, forms=['PHYSICS_JA'], items=items,
                                    answers={'PHYSICS:1': '9'})
    assert wrong.get('needsReview') is True


def test_session_answer_key_registration_is_factual_and_idempotent(tmp_path):
    """A session's key belongs to every source of that session, and saying so twice changes nothing."""
    from eju_bank.ocr.session_keys import register_all, session_answer_keys
    sources = tmp_path / 'sources'; sources.mkdir()
    for name, text in [('q1.pdf', 'Paper one'), ('q2.pdf', 'Paper two'), ('key.pdf', 'Answers')]:
        doc = pymupdf.open(); page = doc.new_page(); page.insert_text((50, 50), text)
        doc.save(sources / name); doc.close()
    create_source_manifest(session='2099-1', subject='SCIENCE', language='ja',
                           syllabus_version='2015', question_booklet=sources / 'q1.pdf',
                           answer_key=sources / 'key.pdf', rights_status='PRIVATE_STUDY',
                           rights_note='t', output_path=tmp_path / 'work/a/source-manifest.json')
    # b 卷没有自己的答案册：清单里只有题册，答案册角色整个缺席。
    without = create_source_manifest(
        session='2099-1', subject='JAPANESE', language='ja', syllabus_version='2015',
        question_booklet=sources / 'q2.pdf', answer_key=sources / 'key.pdf',
        rights_status='PRIVATE_STUDY', rights_note='t',
        output_path=tmp_path / 'work/b/source-manifest.json')
    without['files'] = [f for f in without['files'] if f['role'] != 'ANSWER_KEY']
    write_json(tmp_path / 'work/b/source-manifest.json', without)

    assert set(session_answer_keys(tmp_path / 'work')) == {'2099-1'}
    first = register_all(tmp_path / 'work')
    assert first['added'] == ['b'] and first['alreadyHad'] == ['a']

    registered = json.loads((tmp_path / 'work/b/source-manifest.json').read_text())
    entry = next(f for f in registered['files'] if f['role'] == 'ANSWER_KEY')
    # 登记的是磁盘上真实的那份文件，哈希现读现算，而且标明它是回次级别的。
    from eju_bank.util import sha256_file
    assert entry['sha256'] == sha256_file(sources / 'key.pdf')
    assert entry['registeredFrom'] == 'SESSION_ANSWER_KEY'
    from eju_bank.source import validate_source_manifest
    validate_source_manifest(registered, tmp_path / 'work/b/source-manifest.json', verify_files=True)

    again = register_all(tmp_path / 'work')
    assert again['added'] == [] and sorted(again['alreadyHad']) == ['a', 'b']


ROW_KEY_HTML = """<table>
<thead><tr><th colspan="3">物理</th></tr>
<tr><th>問</th><th>解答欄</th><th>正解</th></tr></thead>
<tbody>
<tr><td rowspan="2">I</td><td>問1</td><td>1</td><td>6</td></tr>
<tr><td>問2</td><td>2</td><td>2</td></tr>
<tr><td>問3</td><td>3</td><td>5</td></tr>
<tr><td>問1</td><td>1</td><td>5</td></tr>
<tr><td>問2</td><td>2</td><td>4</td></tr>
</tbody>
<thead><tr><th colspan="3">化学</th></tr></thead>
</table>"""
ROW_KEY_FLAT = "〈理科〉\n物理\n問 1 1 6\n問 2 2 2\n問 3 3 5\n化学\n問 1 1 5\n問 2 2 4\n"


def test_row_per_question_key_files_each_section_under_its_own_subject():
    """Chemistry answers must never be served as physics answers.

    The real 2010-2 key puts its 化学 <thead> *after* some of chemistry's own
    rows, so splitting the grid where the heading appears filed 化学 問1 (5) as
    PHYSICS:1, whose printed answer is 6. A learner answering physics correctly
    would have been marked wrong.
    """
    from eju_bank.ocr import answer_table as T
    parsed = T.parse_answer_tables(ROW_KEY_HTML,
                                   default_section=T.heading_in_text(ROW_KEY_FLAT),
                                   section_order=T.headings_in_text(ROW_KEY_FLAT))
    refs = T.to_answer_refs(parsed)
    assert T.headings_in_text(ROW_KEY_FLAT) == ['物理', '化学']
    assert refs['PHYSICS:1'] == '6' and refs['PHYSICS:3'] == '5'
    assert refs['CHEMISTRY:1'] == '5' and refs['CHEMISTRY:2'] == '4'
    # 每个小节各自独立：物理只有 3 欄，化学只有 2 欄。
    assert sum(1 for k in refs if k.startswith('PHYSICS:')) == 3
    assert sum(1 for k in refs if k.startswith('CHEMISTRY:')) == 2


def test_a_slot_read_twice_with_two_different_answers_is_dropped_alone():
    """One unreadable 解答番号 must cost that 解答番号, not its whole section."""
    from eju_bank.ocr import answer_table as T
    broken = ROW_KEY_HTML.replace(
        "<tr><td>問2</td><td>2</td><td>4</td></tr>",
        "<tr><td>問2</td><td>2</td><td>4</td></tr><tr><td>問2</td><td>2</td><td>1</td></tr>")
    parsed = T.parse_answer_tables(broken, default_section='物理',
                                   section_order=['物理', '化学'])
    refs = T.to_answer_refs(parsed)
    # 这一欄读到两个互相矛盾的正解，无从取舍，只有它不采用。
    assert 'CHEMISTRY:2' not in refs
    assert any('不采用' in p for p in parsed['problems'])
    # 同节的其他欄与隔壁小节都不受影响。
    assert refs['CHEMISTRY:1'] == '5'
    assert refs['PHYSICS:1'] == '6' and refs['PHYSICS:3'] == '5'


# ── 用题册反验来放行，而不是盲目截断 ────────────────────────────────────────

def _q(slot, options, section='物理', label=None):
    return {'page': 1, 'section': section, 'label': label or f'問{slot}', 'number': str(slot),
            'sub': None, 'slot': None, 'boxed_slot': str(slot), 'answer_prefix': 'PHYSICS',
            'context': None, 'stem': f'stem {slot}', 'options': options, 'pages': [1]}


def test_answers_above_a_numbering_hole_are_kept_when_the_booklet_confirms_them():
    """缺口之上的答案不再一律作废：题册自己印的选项就是那份独立证据。"""
    from eju_bank.ocr.slot_join import join_sections
    # 正解表读到 1、3、4、5（2 号缺失且无解释），所以只有 1 号在"可信前缀"里。
    full = {'PHYSICS:1': '2', 'PHYSICS:3': '4', 'PHYSICS:4': '1', 'PHYSICS:5': '3'}
    trusted = {'PHYSICS': 1}
    items = [_q(1, {'1': 'a', '2': 'b'}), _q(3, {'1': 'a', '4': 'd'}),
             _q(4, {'1': 'a', '2': 'b'}), _q(5, {'3': 'c', '9': 'z'})]
    accepted, filled, report = join_sections(items, full, trusted)
    assert accepted == {'PHYSICS'} and filled == 0
    assert '4/4' in report['PHYSICS']

    # 正解给的答案多数不在题册读到的选项里 —— 那正是错位的样子，仍然拒绝。
    shifted = [_q(1, {'1': 'a', '2': 'b'}), _q(3, {'7': 'x', '8': 'y'}),
               _q(4, {'7': 'x', '8': 'y'}), _q(5, {'7': 'x', '8': 'y'})]
    accepted, _, report = join_sections(shifted, full, trusted)
    assert accepted == set()
    assert '未通过题册反验' in report['PHYSICS']


def test_section_sequence_fills_slots_only_when_both_checks_agree():
    """题数与欄位数相等时顺序配对唯一确定，但仍要过框号与选项两道验。"""
    from eju_bank.ocr.slot_join import join_sections
    full = {'PHYSICS:1': '1', 'PHYSICS:2': '2', 'PHYSICS:3': '3'}
    trusted = {'PHYSICS': 3}
    blank = lambda n: {**_q(n, {str(n): 'ok', '9': 'no'}), 'boxed_slot': None, 'slot': None,
                       'label': '問?', 'number': None}
    items = [blank(1), blank(2), blank(3)]
    accepted, filled, report = join_sections(items, full, trusted)
    assert filled == 3
    assert [i['boxed_slot'] for i in items] == ['1', '2', '3']
    assert all(i['slotSource'] == 'SECTION_SEQUENCE' for i in items)

    # 已读到的框号与顺序配对冲突时，框号说了算，整段不补。
    clashing = [blank(1), blank(2), blank(3)]
    clashing[1]['boxed_slot'] = '7'
    accepted, filled, report = join_sections(clashing, full, trusted)
    assert filled == 0 and '框号' in report['PHYSICS']


def test_two_captures_of_one_answer_page_merge_by_agreement():
    """两次识别：只有一次读到的采用，两次读到而不一致的谁也不采用。"""
    from eju_bank.ocr.answer_key_contracts import parse_answer_page
    coarse = {'raw_flat': '物理\n解答欄 1 2\n答 3 4\n', 'ocrDpi': 180}
    fine = {'raw_flat': '物理\n解答欄 1 2 3\n答 3 4 5\n', 'ocrDpi': 400}
    refs, _math, problems = parse_answer_page([coarse, fine])
    # 高分辨率补上了 3 号；1、2 号两次一致。
    assert refs.get('PHYSICS:3') == '5'
    assert refs.get('PHYSICS:1') == '3'

    conflicting = {'raw_flat': '物理\n解答欄 1 2\n答 3 9\n', 'ocrDpi': 400}
    refs, _math, problems = parse_answer_page([coarse, conflicting])
    assert 'PHYSICS:2' not in refs
    assert any('两次识别给出不同的正解' in p for p in problems)
    assert refs.get('PHYSICS:1') == '3'


def test_a_question_whose_options_land_on_the_next_page_is_still_read():
    """题干在一页、选项在下一页的题不再整道丢掉。"""
    from eju_bank.ocr.question_blocks import parse_page
    first = '問3 次の文の内容に合うものはどれですか。正しいものを一つ選びなさい。'
    second = '$\\textcircled{1}$ 甲である\n$\\textcircled{2}$ 乙である\n$\\textcircled{3}$ 丙である'
    done, carry = parse_page(first, page=7)
    assert done == [] and (carry or {}).get('block')      # 本页还没闭合
    done, carry = parse_page(second, carry=carry, page=8)
    assert not (carry or {}).get('block') and len(done) == 1
    question = done[0]
    assert question['label'] == '問3'
    assert set(question['options']) == {'1', '2', '3'}
    # 它占了哪几页要记下来，逐字校验才能在页集合上做。
    assert question['pages'] == [7, 8]

    # 下一页开头不是选项时，照旧当它不是题目。
    done, carry = parse_page(first, page=7)
    done, carry = parse_page('別の本文が始まる。', carry=carry, page=8)
    assert done == [] and not (carry or {}).get('block')


def test_transposed_mathematics_key_is_read_by_letter_runs():
    """转置版式的数学正解表：字母回到 A 就是大題分界，別解行不会被吞进答案。"""
    from eju_bank.ocr.math_answers import parse_math_vertical
    text = ('〈数 学〉\nコース1\nI\nII\n問1\n問2\n解答棚\n'
            + '\n'.join('ABCDE') + '\n' + '\n'.join('ABC') + '\n答\n'
            + '\n'.join(['1', '4', '1', '3', '5']) + '\n'
            + '\n'.join(['7', '—', '8']) + '\nAB=14または41\n')
    out = parse_math_vertical(text)
    groups = out['groups']['MATHEMATICS_COURSE_1']
    assert groups['I'] == {'A': '1', 'B': '4', 'C': '1', 'D': '3', 'E': '5'}
    # 破折号是负号占一格，不该截断答案串；「AB=14または41」是別解注记，不是答案。
    assert groups['II'] == {'A': '7', 'B': '-', 'C': '8'}


def test_a_group_is_used_only_when_its_questions_account_for_every_blank():
    """逐問欄位由题干给出，但一个大題的各問字母必须恰好覆盖正解表的字母全集。"""
    from eju_bank.ocr.math_questions import closed_groups
    parsed = {'groups': {'MATHEMATICS_COURSE_1': {'II': {'A': '1', 'B': '2', 'C': '3'}}}}
    whole = [{'group': 'II', 'question': '1', 'stem_letters': {'A', 'B'}},
             {'group': 'II', 'question': '2', 'stem_letters': {'C'}}]
    assert closed_groups(whole, parsed, 'MATHEMATICS_COURSE_1') == {
        'II': {'A': '1', 'B': '2', 'C': '3'}}

    # 少读到一格就不闭合：否则会发布一道比原题少填一格的题。
    partial = [{'group': 'II', 'question': '1', 'stem_letters': {'A', 'B'}}]
    assert closed_groups(partial, parsed, 'MATHEMATICS_COURSE_1') == {}
    # 两問抢同一格也不闭合。
    overlap = [{'group': 'II', 'question': '1', 'stem_letters': {'A', 'B', 'C'}},
               {'group': 'II', 'question': '2', 'stem_letters': {'C'}}]
    assert closed_groups(overlap, parsed, 'MATHEMATICS_COURSE_1') == {}


def test_parse_pages_reports_the_run_limit_and_what_sits_above_it(tmp_path):
    """提议—反验这条链的入口必须有测试：缺了它整条链会静默失效。"""
    from eju_bank.ocr.answer_key_contracts import (
        above_run_answers, build_all, parse_pages)
    work = tmp_path / 'work/src'
    # 物理读到 1、2、4：3 号缺失且无解释，所以可信前缀停在 2。
    write_json(work / 'answer_ocr/p0001.json',
               {'raw_flat': '物理\n解答欄 1 2 4\n答 3 4 5\n'})
    (work / 'source-manifest.json').write_text(json.dumps(
        {'session': 't', 'files': [{'role': 'ANSWER_KEY', 'path': 'x'}]}), encoding='utf-8')

    contracts, trusted, notes = parse_pages(work, forms=['PHYSICS_JA'])
    assert contracts and trusted.get('PHYSICS') == 2
    assert 'PHYSICS' in notes and '缺口' in notes['PHYSICS']
    assert above_run_answers(contracts, trusted) == {'PHYSICS': {4: '5'}}

    # 不传裁决时照旧截断；裁决通过时那一条才留下，并标明它凭什么留下。
    plain = build_all(work, forms=['PHYSICS_JA'])
    refs = {b['answerRef']: b for c in plain.values() for b in c['blocks']
            if b.get('kind') == 'answer-entry'}
    assert 'PHYSICS:4' not in refs

    kept = build_all(work, forms=['PHYSICS_JA'], accepted_provisional={'PHYSICS'},
                     evidence={'PHYSICS': '题册反验 5/5 通过'})
    refs = {b['answerRef']: b for c in kept.values() for b in c['blocks']
            if b.get('kind') == 'answer-entry'}
    assert refs['PHYSICS:4']['answerEvidence'] == 'ABOVE_RUN_CONFIRMED_BY_BOOKLET'
    assert any('题册反验' in v for c in kept.values()
               for v in (c.get('provisionalSections') or {}).values())


def test_sub_questions_keep_their_parent_and_its_passage_across_a_page_break(tmp_path):
    """子问跨页时若丢了父級，题号会变成「問?」，那段共用文章也会跟着丢 —— 题就无法作答。"""
    from eju_bank.ocr.question_blocks import parse_page
    from eju_bank.ocr.attested_contracts import build_question_contract

    passage = '問7 次の会話を読み，下の問い(1),(2)に答えなさい。'
    first = (passage + '\n甲：これは共用の文章です。\n'
             '(1) 下線部について正しいものを一つ選びなさい。\n'
             '$\\textcircled{1}$ 甲\n$\\textcircled{2}$ 乙')
    second = ('(2) もう一つの問いに答えなさい。正しいものを一つ選びなさい。\n'
              '$\\textcircled{1}$ 丙\n$\\textcircled{2}$ 丁')

    one, carry = parse_page(first, page=11)
    two, carry = parse_page(second, carry=carry, page=12)
    assert [q['label'] for q in one] == ['問7(1)']
    # (1) 在上一页就闭合了，(2) 仍然要认得自己的父題与那段文章。
    assert [q['label'] for q in two] == ['問7(2)']
    assert '共用の文章' in (two[0]['context'] or '')
    # 文章出自第 11 页，核对要在那一页上做，而不是 (2) 所在的第 12 页。
    assert two[0]['contextPages'] == [11]

    # 合约里，用到这段材料的题要指名它 —— 否则前端会把它当整组共用，
    # 挂在同页每一道无关的题上面。
    write_json(tmp_path / 'work/src/ocr_cache/p0011.json', {'raw_text': first})
    write_json(tmp_path / 'work/src/ocr_cache/p0012.json', {'raw_text': second})
    items = [{**two[0], 'section': '総合科目', 'answer_prefix': 'JW',
              'page': 12, 'boxed_slot': '6'}]
    contract = build_question_contract(tmp_path / 'work/src', 12, forms=['JAPAN_AND_WORLD_JA'],
                                        items=items, answers={'JW:6': '1'})
    material = next(b for b in contract['blocks'] if b['kind'] == 'material')
    question = next(b for b in contract['blocks'] if b['kind'] == 'question')
    assert question['materialRefs'] == [material['localKey']]
    # 材料的字出自第 11 页，按页集合核对才通不报错。
    assert not contract.get('needsReview'), contract.get('issues')
