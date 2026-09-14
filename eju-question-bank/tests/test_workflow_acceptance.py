"""Cross-feature acceptance: pinned review, real job execution and paginated APIs."""
import copy
import json
from pathlib import Path
import threading
import urllib.request
import urllib.error

import pytest
from conftest import install_fixture_media
from eju_bank.db import Database
from eju_bank.audit import iter_questions, prepare_paper
from eju_bank.errors import ContractError, SessionError
from eju_bank.server import create_server


@pytest.fixture
def bank(tmp_path):
    paper=json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    install_fixture_media(tmp_path/'media')
    db=Database(tmp_path/'eju.db');db.publish(paper,channel='PUBLIC')
    yield db,paper
    db.close()


def objective(paper):
    return next(q for f,_,q in iter_questions(paper) if f['formCode']=='PHYSICS_JA')


def test_first_attempt_stats_skip_unanswered_exposures(bank):
    db,paper=bank;q=objective(paper);qid=q['questionId']
    empty=db.create_practice([qid])['sessionId'];db.submit_session(empty)
    correct=db.create_practice([qid])['sessionId']
    db.record_response(correct,qid,{'type':'SINGLE_CHOICE',**q['correctAnswer']});db.submit_session(correct)
    wrong=db.create_practice([qid])['sessionId']
    option=next(o['key'] for o in q['options'] if o['key']!=q['correctAnswer']['optionKey'])
    db.record_response(wrong,qid,{'type':'SINGLE_CHOICE','optionKey':option});db.submit_session(wrong)
    summary=db.learning_summary()
    assert summary['firstUnaided']=={'denominator':1,'correct':1,'accuracy':1.0}
    assert summary['repeatUnaided']=={'denominator':1,'correct':0,'accuracy':0.0}
    assert summary['unansweredExposures']==1
    assert len(db.question_attempts(qid))==3
    db.submit_session(wrong)
    assert len(db.question_attempts(qid))==3


def test_preview_is_pinned_idempotent_and_rechecks_delivery(bank):
    db,paper=bank;q=objective(paper)
    preview=db.preview_practice({'questionIds':[q['questionId']],'randomOrder':True,'seed':'fixed'})
    assert 'correctAnswer' not in json.dumps(preview)
    one=db.start_preview(preview['previewId'],'start-request-123')
    assert db.start_preview(preview['previewId'],'start-request-123')['sessionId']==one['sessionId']
    second=db.preview_practice({'questionIds':[q['questionId']]})
    with pytest.raises(SessionError):db.start_preview(second['previewId'],'start-request-123')
    db.set_delivery_state(one['paperVersionId'],'SUSPENDED','Acceptance test')
    with pytest.raises(SessionError):db.start_preview(second['previewId'],'start-request-456')
    assert db.get_session_paper(one['sessionId'])['questionCount']==1


def test_explanations_pin_at_submission_and_require_review(bank):
    db,paper=bank;q=objective(paper);qid=q['questionId']
    qvid=db.connection.execute('SELECT id FROM question_versions WHERE question_id=?',(qid,)).fetchone()[0]
    content={'kind':'EXPLANATION','language':'zh','contentAst':[{'type':'text','value':'Reviewed explanation'}]}
    first=db.save_explanation(qvid,content,status='REVIEWED',reviewer='reviewer')
    sid=db.create_practice([qid])['sessionId']
    with pytest.raises(SessionError):db.review_content(sid)
    db.submit_session(sid)
    draft=db.save_explanation(qvid,{**content,'contentAst':[{'type':'text','value':'Draft secret'}]},base_revision=1)
    assert db.review_content(sid)['items'][0]['revisionId']==first['revisionId']
    second=db.save_explanation(qvid,content,base_revision=draft['revision'],status='REVIEWED',reviewer='reviewer')
    assert db.review_content(sid)['items'][0]['revisionId']==first['revisionId']
    assert db.review_content(sid,latest=True)['items'][0]['revisionId']==second['revisionId']
    db.save_explanation(qvid,content,base_revision=second['revision'],status='WITHDRAWN',reviewer='reviewer')
    assert db.review_content(sid)['items'][0]['content'] is None
    assert db.review_content(sid)['items'][0]['status']=='WITHDRAWN'


def test_note_cas_and_assessment_never_changes_objective_score(bank):
    db,paper=bank;q=objective(paper)
    db.save_note_revision(q['questionId'],'first',0)
    with pytest.raises(SessionError):db.save_note_revision(q['questionId'],'stale',0)
    assert db.note_detail(q['questionId'])['note']=='first'
    essay=next(q for _,_,q in iter_questions(paper) if q['answerSpec']['type']=='ESSAY')
    sid=db.create_practice([essay['questionId']])['sessionId']
    db.record_response(sid,essay['questionId'],{'type':'ESSAY','text':'This is my response.'})
    before=db.submit_session(sid)
    rubric=db.save_rubric({'name':'Practice rubric','official':False,'dimensions':[{'id':'clarity','levels':['needs work','clear']}]},'teacher')
    result=db.assess_essay(sid,essay['questionId'],{'rubricRevisionId':rubric['rubricRevisionId'],'ratings':{'clarity':'clear'},'comment':'Revision suggestion'})
    assert result['officialScore'] is False
    assert db.get_result(sid)['objectiveTotal']==before['objectiveTotal']==0
    assert db.essay_assessments(sid)[0]['assessment']['responseHash']
    empty=db.create_practice([essay['questionId']])['sessionId'];db.submit_session(empty)
    with pytest.raises(ContractError):db.assess_essay(empty,essay['questionId'],{'rubricRevisionId':rubric['rubricRevisionId'],'ratings':{'clarity':'clear'}})


def request(base,path,body=None):
    r=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type':'application/json'} if body is not None else {})
    try:
        with urllib.request.urlopen(r) as response:return response.status,json.loads(response.read())
    except urllib.error.HTTPError as error:return error.code,json.loads(error.read())


def test_http_cursor_and_job_input_boundaries(bank):
    db,paper=bank
    server=create_server(db.path,port=0,start_worker=False)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        status,page=request(base,'/api/v1/questions?limit=1')
        assert status==200 and page['nextCursor']
        seen={page['questions'][0]['questionId']}
        while page['nextCursor']:
            status,page=request(base,'/api/v1/questions?limit=1&cursor='+page['nextCursor'])
            assert status==200,page
            for q in page['questions']:
                assert q['questionId'] not in seen
                seen.add(q['questionId'])
        assert len(seen)==paper['questionCount']
        status,error=request(base,'/api/v1/admin/jobs',{'jobType':'RENDER','sourceId':'missing','params':[]})
        assert status in {400,404,422}
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();server.database.close()


def test_suspended_version_keeps_only_its_session_media(bank):
    from eju_bank.audit import iter_asset_nodes
    from eju_bank.assets import AssetStore
    db,paper=bank
    q=next(q for _,_,q in iter_questions(paper) if list(iter_asset_nodes(q)))
    asset=next(iter_asset_nodes(q))[1]['assetId']
    sid=db.create_practice([q['questionId']])['sessionId']
    db.submit_session(sid)
    pv=db.get_session(sid)['paperVersionId']
    db.set_delivery_state(pv,'SUSPENDED','Needs review')
    assert not db.media_is_published(asset)
    assert db.media_for_session(sid,asset)
    unrelated=AssetStore(db.media_dir).put_bytes(b'unrelated private asset',mime_type='application/octet-stream',ext='.bin')['assetId']
    assert not db.media_for_session(sid,unrelated)
    server=create_server(db.path,port=0,start_worker=False)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        base=f'http://127.0.0.1:{server.server_port}'
        req=urllib.request.Request(base+f'/api/v1/sessions/{sid}/media/{asset}',method='HEAD')
        with urllib.request.urlopen(req) as response:
            assert response.status==200 and response.read()==b''
        req=urllib.request.Request(base+f'/api/v1/sessions/{sid}/media/{asset}',headers={'Range':'bytes=0-3'})
        with urllib.request.urlopen(req) as response:
            assert response.status==206 and len(response.read())==4
        status,_=request(base+f'/api/v1/sessions/{sid}/media/',unrelated)
        assert status==404
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();server.database.close()


def test_explanation_and_translation_have_independent_frozen_streams(bank):
    db,paper=bank;q=objective(paper)
    qv=db.search_questions(form_code='PHYSICS_JA')['questions'][0]['questionVersionId']
    explanation={'kind':'EXPLANATION','language':'zh','contentAst':[{'type':'text','value':'Explanation'}]}
    translation={'kind':'TRANSLATION','language':'zh','contentAst':[{'type':'text','value':'Translation'}]}
    db.save_explanation(qv,explanation,status='REVIEWED',reviewer='one')
    db.save_explanation(qv,translation,base_revision=1,status='REVIEWED',reviewer='one')
    sid=db.create_practice([q['questionId']])['sessionId'];db.submit_session(sid)
    assert {x['kind'] for x in db.review_content(sid)['items']}=={'EXPLANATION','TRANSLATION'}
    db.save_explanation(qv,translation,base_revision=2,status='WITHDRAWN',reviewer='one')
    items={x['kind']:x for x in db.review_content(sid)['items']}
    assert items['EXPLANATION']['content']==explanation
    assert items['TRANSLATION']['content'] is None
    db.rebuild_attempts()
    assert {x['kind']:x for x in db.review_content(sid)['items']}==items


def test_issue_from_old_session_stays_bound_to_old_version(bank):
    db,paper=bank;q=objective(paper)
    sid=db.create_practice([q['questionId']])['sessionId'];old=db.get_session(sid)['paperVersionId']
    changed=copy.deepcopy(paper);objective(changed)['stemAst']=[{'type':'text','value':'New wording'}]
    new=db.publish(prepare_paper(changed),channel='PUBLIC')['paperVersionId']
    issue=db.report_content_issue(q['questionId'],'The old wording needs review',session_id=sid)
    saved=next(i for i in db.list_content_issues() if i['issueId']==issue['issueId'])
    assert saved['paperVersionId']==old
    with pytest.raises(ContractError):db.report_content_issue(q['questionId'],'Wrong version binding',session_id=sid,paper_version_id=new)
    for status in ['IN_PROGRESS','FIXED_PENDING_REVIEW','CLOSED']:
        db.update_content_issue_status(issue['issueId'],status,reason='Resolved in reviewed replacement')
    assert db.connection.execute('SELECT COUNT(*) FROM content_issue_events WHERE issue_id=?',(issue['issueId'],)).fetchone()[0]==4
