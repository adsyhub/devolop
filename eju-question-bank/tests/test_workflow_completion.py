import copy
import json
import sqlite3
import threading
from pathlib import Path
import pytest
from conftest import install_fixture_media
from eju_bank.db import Database
from eju_bank.audit import iter_questions,prepare_paper
from eju_bank.errors import ContractError,SessionError,QualityGateError
from eju_bank.http_workflows import csv_safe,report_export
from eju_bank.security import sanitize_paper_for_learner

@pytest.fixture
def bank(tmp_path):
    db=Database(tmp_path/'library/eju.db',workspace_root=tmp_path)
    install_fixture_media(db.media_dir)
    paper=json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    db.publish(paper,channel='PUBLIC')
    yield db,paper
    db.close()

def one(paper,code='PHYSICS_JA'):
    return next(q for f,g,q in iter_questions(paper) if f['formCode']==code)

def test_attempt_facts_first_repeat_unanswered_and_idempotence(bank):
    db,paper=bank;q=one(paper)
    for option in ['wrong',q['correctAnswer']['optionKey'],None]:
        sid=db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId']
        if option:
            choice=next(x['key'] for x in q['options'] if x['key']!=q['correctAnswer']['optionKey']) if option=='wrong' else option
            db.record_response(sid,q['questionId'],{'type':'SINGLE_CHOICE','optionKey':choice})
        db.submit_session(sid);db.submit_session(sid)
    summary=db.learning_summary()
    assert (summary['uniqueQuestions'],summary['answeredAttempts'],summary['unansweredExposures'])==(1,2,1)
    assert summary['firstUnaided']['correct']==0
    assert summary['repeatUnaided']['correct']==1
    db.rebuild_attempts()
    assert db.learning_summary()==summary
    assert len(db.question_attempts(q['questionId']))==3
    assert sum(x['answeredAttempts'] for x in db.learning_calendar('Asia/Tokyo')['days'])==2

def test_preview_pins_old_version_and_receipt(bank):
    db,paper=bank;q=one(paper)
    preview=db.preview_practice({'questionIds':[q['questionId']],'seed':'test'})
    changed=copy.deepcopy(paper);one(changed)['stemAst']=[{'type':'text','value':'Changed question'}];changed=prepare_paper(changed);db.publish(changed,channel='PUBLIC')
    session=db.start_preview(preview['previewId'],'preview-request-1')
    assert db.start_preview(preview['previewId'],'preview-request-1')['sessionId']==session['sessionId']
    delivered=one(db.get_session_paper(session['sessionId']))
    assert delivered['stemAst']==one(sanitize_paper_for_learner(paper))['stemAst']
    later=db.preview_practice({'questionIds':[q['questionId']]})
    with pytest.raises(SessionError):db.start_preview(later['previewId'],'preview-request-1')
    db.set_delivery_state(later['paper']['sourceVersions'][0]['paperVersionId'],'SUSPENDED','Content review')
    with pytest.raises(SessionError):db.start_preview(later['previewId'],'preview-request-2')

def test_note_conflict_and_progress_conflict(bank):
    db,paper=bank;qid=one(paper)['questionId']
    assert db.save_note_revision(qid,'first',0)['revision']==1
    with pytest.raises(SessionError):db.save_note_revision(qid,'stale',0)
    assert db.note_detail(qid)['note']=='first'
    sid=db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId']
    assert db.save_progress(sid,{'currentQuestionId':qid,'expectedProgressVersion':0})['progressVersion']==1
    with pytest.raises(SessionError):db.save_progress(sid,{'viewMode':'SINGLE','expectedProgressVersion':0})

def test_explanation_revision_is_frozen_at_submission(bank):
    db,paper=bank;qid=one(paper)['questionId'];qv=db.search_questions(form_code='PHYSICS_JA')['questions'][0]['questionVersionId']
    payload={'kind':'EXPLANATION','language':'zh','contentAst':[{'type':'text','value':'First explanation'}]}
    first=db.save_explanation(qv,payload,status='REVIEWED',reviewer='tester')
    sid=db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId']
    with pytest.raises(SessionError):db.review_content(sid)
    assert 'First explanation' not in json.dumps(db.get_session_paper(sid))
    db.submit_session(sid)
    payload['contentAst'][0]['value']='Second explanation';db.save_explanation(qv,payload,status='REVIEWED',reviewer='tester',base_revision=1)
    assert db.review_content(sid)['items'][0]['revisionId']==first['revisionId']
    assert db.review_content(sid,latest=True)['items'][0]['content']['contentAst'][0]['value']=='Second explanation'
    db.save_explanation(qv,payload,status='WITHDRAWN',reviewer='tester',base_revision=2)
    assert db.review_content(sid)['items'][0]['content'] is None

def test_essay_empty_unicode_and_assessment_preserves_response(bank):
    db,paper=bank
    essay=next(q for _,_,q in iter_questions(paper) if q['answerSpec']['type']=='ESSAY')
    sid=db.create_session(paper['paperId'],['JAPANESE_JA'])['sessionId']
    empty=db.submit_session(sid)
    assert empty['essayEmpty']==1 and empty['essayPending']==0
    sid=db.create_session(paper['paperId'],['JAPANESE_JA'])['sessionId']
    response={'type':'ESSAY','text':'日本語😀\n文章'};db.record_response(sid,essay['questionId'],response);db.submit_session(sid)
    rubric=db.save_rubric({'name':'练习标准','official':False,'dimensions':[{'id':'structure','levels':['好','待改']} ]},'teacher')
    assessment={'rubricRevisionId':rubric['rubricRevisionId'],'ratings':{'structure':'好'},'comment':'继续练习'}
    saved=db.assess_essay(sid,essay['questionId'],assessment)
    assert saved['revision']==1 and saved['officialScore'] is False
    db.assess_essay(sid,essay['questionId'],assessment,kind='HUMAN',reviewer='teacher')
    assert len(db.essay_assessments(sid))==2
    assert db.get_session(sid)['responses'][essay['questionId']]['value']==response
    assert next(q for q in report_export(db,sid)['questions'] if q['questionId']==essay['questionId'])['correct'] is None

def test_section_enforces_selected_question_scope(bank):
    db,paper=bank
    q=one(paper);paper=copy.deepcopy(paper);paper['sections']=[{'sectionId':'physics','formCode':'PHYSICS_JA','questionRefs':[q['answerRef']]}];paper=prepare_paper(paper);db.publish(paper,channel='PUBLIC')
    with pytest.raises(ContractError):db.create_session(paper['paperId'],['PHYSICS_JA'],mode='SECTION')
    sid=db.create_session(paper['paperId'],['PHYSICS_JA'],mode='SECTION',section_codes=['physics'])['sessionId']
    assert db.get_session_paper(sid)['questionCount']==1
    with pytest.raises(SessionError):db.record_response(sid,one(paper,'CHEMISTRY_JA')['questionId'],{'type':'SINGLE_CHOICE','optionKey':'1'})

def test_keyset_cursor_filters_and_no_answer_leaks(bank):
    db,paper=bank
    first=db.search_questions(limit=4);second=db.search_questions(limit=4,cursor=first['nextCursor'])
    assert not {x['questionId'] for x in first['questions']} & {x['questionId'] for x in second['questions']}
    with pytest.raises(ContractError):db.search_questions(kind='WRONG',cursor=first['nextCursor'])
    private=copy.deepcopy(paper);private['reviewSummary']={'secret':'REVIEW-SECRET'};private['forms'][0]['groups'][0]['answerLedger']='LEDGER-SECRET'
    safe=json.dumps(sanitize_paper_for_learner(private));assert 'REVIEW-SECRET' not in safe and 'LEDGER-SECRET' not in safe and 'correctAnswer' not in safe
    assert csv_safe(' =SUM(A1)')=="' =SUM(A1)"

def test_default_workspace_rejects_synthetic_and_opens_local_admin(bank):
    db,paper=bank
    protected=Database(db.path,allow_synthetic=False)
    try:
        with pytest.raises(QualityGateError):protected.publish(paper,channel='PUBLIC')
    finally:protected.close()
    from eju_bank.server import create_server
    import urllib.request,urllib.error
    server=create_server(db.path,port=0,start_worker=False);thread=threading.Thread(target=server.serve_forever);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        # 回环绑定不再签发访问令牌，本机管理操作直接放行。
        assert server.admin_token is None
        with urllib.request.urlopen(base+'/api/v1/admin/sources') as response:assert response.status==200
        # 放行的只是本机：别的站点从浏览器发过来的请求仍被 Origin 校验挡住。
        hostile=urllib.request.Request(base+'/api/v1/admin/sources',headers={'Origin':'http://evil.example'})
        with pytest.raises(urllib.error.HTTPError) as error:urllib.request.urlopen(hostile)
        assert error.value.code==403
    finally:server.shutdown();thread.join();server.server_close();server.database.close()

def test_full_backup_restores_production_paths_and_history(bank):
    from eju_bank.ops import create_backup,restore_backup,verify_backup
    from eju_bank.util import write_json
    db,paper=bank;root=db.workspace_root
    write_json(root/'content/content-inventory.json',{'schemaVersion':1,'updatedAt':'2026-01-01T00:00:00Z','items':[]})
    write_json(root/'work/source/page-draft.json',{'draft':'preserved'})
    sid=db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId'];db.submit_session(sid)
    archive=create_backup(database_path=db.path,inventory_path=root/'content/content-inventory.json',media_dir=db.media_dir,workspace_root=root,mode='FULL')
    assert verify_backup(archive)['manifest']['mode']=='FULL'
    restore_backup(archive,root/'restored')
    assert json.loads((root/'restored/work/source/page-draft.json').read_text())['draft']=='preserved'
    restored=Database(root/'restored/eju.db')
    try:assert restored.get_result(sid)['objectiveTotal']==1
    finally:restored.close()

def test_strict_audio_only_exposes_current_segment_and_preserves_play_count(bank):
    db,paper=bank
    from eju_bank.assets import AssetStore
    import io
    import soundfile as sf
    import numpy as np
    output=io.BytesIO();sf.write(output,np.zeros(16000),16000,format='WAV')
    store=AssetStore(db.media_dir);full=store.put_bytes(output.getvalue(),mime_type='audio/wav',ext='.wav')['assetId']
    other=io.BytesIO();sf.write(other,np.zeros(32000),16000,format='WAV');second=store.put_bytes(other.getvalue(),mime_type='audio/wav',ext='.wav')['assetId']
    paper=copy.deepcopy(paper);ref=one(paper)['answerRef'];paper['audioTracks']=[{'trackId':'test-track','assetId':full,'durationMs':3000,'cues':[{'cueId':'one','startMs':0,'endMs':1000,'assetId':full,'questionRefs':[ref]},{'cueId':'two','startMs':1000,'endMs':3000,'assetId':second,'questionRefs':[ref]}]}];paper=prepare_paper(paper);db.publish(paper,channel='PUBLIC')
    sid=db.create_session(paper['paperId'],['PHYSICS_JA','CHEMISTRY_JA'],mode='MOCK')['sessionId']
    audio=db.session_audio(sid);assert audio['tracks'][0]['assetId']==full
    assert not db.media_for_session(sid,second)
    db.save_audio_progress(sid,'test-track',0,'PLAY')
    with pytest.raises(SessionError):db.save_audio_progress(sid,'test-track',0,'PLAY')
    with pytest.raises(SessionError):db.save_audio_progress(sid,'test-track',0,'SEEK')
    with pytest.raises(SessionError):db.save_audio_progress(sid,'test-track',1000,'ADVANCE')
    config=json.loads(db._state(sid)['config_json']);config['audioState']['test-track']['startedAt']='2000-01-01T00:00:00Z'
    db.connection.execute('UPDATE session_state SET config_json=? WHERE session_id=?',(json.dumps(config),sid));db.connection.commit()
    db.save_audio_progress(sid,'test-track',1000,'ADVANCE')
    assert db.session_audio(sid)['tracks'][0]['assetId']==second
    assert db.media_for_session(sid,second)

def test_diagnostics_retention_and_personal_delete_are_scoped(bank):
    from eju_bank.maintenance import diagnostics,retention_plan,personal_data_preview,delete_personal_data
    from eju_bank.util import write_json
    db,paper=bank;qid=one(paper)['questionId'];marker='PRIVATE-ESSAY-NOTE-TOKEN'
    db.save_note_revision(qid,marker,0)
    qv=db.search_questions(form_code='PHYSICS_JA')['questions'][0]['questionVersionId']
    db.save_explanation(qv,{'kind':'EXPLANATION','language':'zh','contentAst':[{'type':'text','value':'Reviewed explanation'}]},status='REVIEWED',reviewer='tester')
    sid=db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId'];db.submit_session(sid)
    assert db.connection.execute('SELECT COUNT(*) FROM session_review_annotations').fetchone()[0]==1
    assert marker not in json.dumps(diagnostics(db))
    source=db.workspace_root/'sources/original.pdf';source.parent.mkdir(exist_ok=True);source.write_bytes(b'original source')
    assert source.name not in json.dumps(retention_plan(db))
    plan=personal_data_preview(db);assert marker not in json.dumps(plan)
    with pytest.raises(ContractError):delete_personal_data(db,plan['planId'],False)
    write_json(db.workspace_root/'content/content-inventory.json',{'schemaVersion':1,'updatedAt':'2026-01-01T00:00:00Z','items':[]})
    result=delete_personal_data(db,plan['planId'],True)
    assert result['backupName']
    assert db.get_question_note(qid) is None and db.list_papers()
    assert source.read_bytes()==b'original source'

def test_rights_withdrawal_blocks_old_content_but_retains_history(bank):
    db,paper=bank
    sid=db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId'];db.submit_session(sid)
    version=db.get_session(sid)['paperVersionId']
    db.set_delivery_state(version,'SUSPENDED','Rights withdrawn by owner',reason_code='RIGHTS_WITHDRAWN')
    with pytest.raises(SessionError):db.get_session_paper(sid)
    with pytest.raises(SessionError):db.get_paper(paper['paperId'])
    assert db.history_page()['history'][0]['sessionId']==sid

def test_published_media_and_stopped_bookmark_preview(bank):
    from eju_bank.audit import iter_asset_nodes
    db,paper=bank
    assets={n['assetId'] for _,n in iter_asset_nodes(sanitize_paper_for_learner(paper))}
    assert assets and all(db.media_is_published(asset) for asset in assets)
    qid=one(paper)['questionId']
    db.set_bookmark(qid)
    version=db.search_questions()['questions'][0]['paperVersionId']
    db.set_delivery_state(version,'SUSPENDED','Review pending')
    listed=db.search_questions(kind='BOOKMARKED')['questions']
    assert len(listed)==1 and listed[0]['available'] is False and 'stemAst' not in listed[0]
    assert not any(db.media_is_published(asset) for asset in assets)
    with pytest.raises(ContractError):db.preview_practice({'kind':'BOOKMARKED'})

def test_foreground_time_is_not_doubled_across_sessions(bank):
    db,paper=bank
    sessions=[db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId'] for _ in range(2)]
    with db._transaction():
        for sid in sessions:db.connection.execute('UPDATE practice_sessions SET last_active_at=? WHERE id=?',('2026-01-01T00:00:00Z',sid))
        for sid in sessions:
            row,_=db._session_with_paper(sid);db._touch(row,'2026-01-01T00:00:10Z')
    assert sum(db.get_session(sid)['activeDurationSec'] for sid in sessions)==10

def test_session_question_pages_pin_version_and_cursor_scope(bank):
    db,paper=bank
    sid=db.create_session(paper['paperId'],['PHYSICS_JA','CHEMISTRY_JA'])['sessionId']
    other=db.create_session(paper['paperId'],['PHYSICS_JA'])['sessionId']
    outline=db.session_outline(sid)['paper']
    assert all('stemAst' not in q for _,_,q in iter_questions(outline))
    first=db.session_questions(sid,limit=1)
    newer=copy.deepcopy(paper);newer['title']='New version';db.publish(prepare_paper(newer),channel='PUBLIC')
    second=db.session_questions(sid,cursor=first['nextCursor'],limit=1)
    assert first['questions'][0]['question']['questionId']!=second['questions'][0]['question']['questionId']
    assert db.session_outline(sid)['paper']['title']==paper['title']
    assert 'correctAnswer' not in json.dumps([outline,first,second])
    with pytest.raises(ContractError):db.session_questions(other,cursor=first['nextCursor'])
