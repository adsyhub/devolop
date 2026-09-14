import copy
import json
from pathlib import Path
import pytest
from conftest import install_fixture_media
from eju_bank.audit import prepare_paper, iter_questions
from eju_bank.db import Database


@pytest.fixture
def bank(tmp_path):
    paper = json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    install_fixture_media(tmp_path / 'media')
    db = Database(tmp_path / 'test.db'); db.publish(paper, channel='PUBLIC')
    yield db, paper
    db.close()


def test_collection_pins_multiple_sources_and_keeps_material_group(bank):
    db, paper = bank
    p = copy.deepcopy(paper)
    form = next(f for f in p['forms'] if f['formCode'] == 'PHYSICS_JA')
    group = form['groups'][0]
    first = group['questions'][0]
    first['materialRefs'] = ['shared']
    group['materials'] = [{'localKey':'shared','contentAst':[{'type':'text','value':'Shared experiment'}]}]
    second = copy.deepcopy(first);second.update(questionId='q_second',localKey='q_second',answerRef='PHYSICS:2')
    group['questions'].append(second)
    db.publish(prepare_paper(p), channel='PUBLIC')
    other = copy.deepcopy(paper); other['paperId']='p_other';other['stableCode']='other';other['title']='Other paper'
    for _, _, q in iter_questions(other): q['questionId'] += '_other'
    db.publish(prepare_paper(other), channel='PUBLIC')
    other_q = next(q for f, _, q in iter_questions(other) if f['formCode'] == 'CHEMISTRY_JA')
    sid = db.create_practice([first['questionId'],other_q['questionId']])['sessionId']
    snapshot = db.get_session_paper(sid)
    assert snapshot['questionCount'] == 3
    assert len(snapshot['sourceVersions']) == 2
    assert 'correctAnswer' not in json.dumps(snapshot)
    assert any(g['materials'] for f in snapshot['forms'] for g in f['groups'])
    db.record_response(sid, first['questionId'], {'type':'SINGLE_CHOICE',**first['correctAnswer']})
    db.submit_session(sid)
    result = db.get_result(sid)
    assert result['objectiveTotal'] == 3 and result['objectiveCorrect'] == 1
    assert result['questions'][0]['question']['sourcePaperVersionId']


def test_notes_bookmarks_wrong_retry_and_schedule(bank):
    db,paper=bank
    q=next(q for f,_,q in iter_questions(paper) if f['formCode']=='PHYSICS_JA')
    qid=q['questionId']
    db.set_bookmark(qid)
    db.set_question_note(qid,'复习机械能')
    found=db.search_questions(kind='BOOKMARKED',query='机械能')['questions']
    assert len(found)==1 and found[0]['questionId']==qid
    assert 'correctAnswer' not in json.dumps(found)
    sid=db.create_practice([qid])['sessionId']
    wrong=next(o['key'] for o in q['options'] if o['key']!=q['correctAnswer']['optionKey'])
    db.record_response(sid,qid,{'type':'SINGLE_CHOICE','optionKey':wrong})
    db.submit_session(sid)
    db.schedule_review(qid,0,notes='读题错误')
    assert db.search_questions(kind='DUE')['questions'][0]['notes']=='读题错误'
    retry=db.create_practice([qid])['sessionId']
    db.record_response(retry,qid,{'type':'SINGLE_CHOICE',**q['correctAnswer']})
    db.submit_session(retry)
    assert db.get_wrong_questions()[0]['status']=='REVIEWING'
    assert len(db.get_history())==2
