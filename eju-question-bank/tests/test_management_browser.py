"""The management UI must execute production jobs and verify real backup artifacts."""
import threading
import pytest
from eju_bank.server import create_server
from eju_bank.inventory import upsert_inventory_item

pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright, expect


def test_import_render_and_backup_from_management_ui(tmp_path):
    import pymupdf
    incoming=tmp_path/'incoming';incoming.mkdir()
    doc=pymupdf.open();p=doc.new_page();p.insert_text((50,50),'Source fixture');doc.save(incoming/'q.pdf');doc.close()
    upsert_inventory_item({'inventoryId':'browser-inventory','session':'TEST','subject':'SCIENCE','language':'ja',
        'syllabusId':'basic-2015','requiredFiles':['QUESTION_BOOKLET','ANSWER_KEY'],'expectedForms':['PHYSICS_JA'],
        'rightsStatus':'PRIVATE_STUDY','pipelineStatus':'RECEIVED'},tmp_path/'content/content-inventory.json')
    server=create_server(tmp_path/'library/eju.db',port=0,workspace_root=tmp_path)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);page=browser.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            base=f'http://127.0.0.1:{server.server_port}'
            page.goto(f'{base}/me#/analytics')
            expect(page.locator('#learning-summary')).to_contain_text('独立题数 0')
            # 导入是来源的诞生方式，课程库的来源列表和阶段 ② 都链到同一个导入视图。
            page.goto(f'{base}/studio/library')
            page.get_by_role('link',name='导入工作区内的文件',exact=True).click()
            expect(page.locator('#view-import')).to_be_visible()
            page.locator('#import-inventory').fill('browser-inventory')
            page.locator('#import-path').fill('incoming/q.pdf')
            page.locator('#import-form button').click()
            page.goto(f'{base}/studio/ops#/ops/jobs')
            expect(page.locator('#job-list')).to_contain_text('SUCCEEDED',timeout=15000)
            expect(page.locator('#production-source option')).to_have_count(1)
            page.locator('#production-kind').select_option('RENDER')
            page.locator('#production-pages').fill('1')
            page.locator('#production-form button').click()
            page.wait_for_function("() => [...document.querySelectorAll('#job-list article')].some(x=>x.textContent.includes('RENDER') && x.textContent.includes('SUCCEEDED'))",timeout=15000)
            page.goto(f'{base}/studio/ops#/ops/backups')
            page.locator('#backup-mode').select_option('FULL')
            page.locator('#backup-create').click()
            expect(page.locator('#backup-list a')).to_have_count(1,timeout=15000)
            page.locator('#backup-list button',has_text='校验').click()
            expect(page.locator('#management-status')).to_have_text('备份校验通过')
            assert list((tmp_path/'work').glob('*/renders/render-index-question_booklet.json'))
            assert not errors
            browser.close()
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();server.database.close()


from test_browser_learning import browser_app,open_session

def test_practice_audio_stops_at_cue_end_and_restores_position(browser_app,tmp_path):
    import copy
    import wave
    from eju_bank.assets import AssetStore
    from eju_bank.audio import probe_audio
    from eju_bank.audit import iter_questions,prepare_paper
    page,db,paper,url=browser_app
    track_file=tmp_path/'track.wav'
    with wave.open(str(track_file),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(8000);wav.writeframes(b'\x00\x00'*16000)
    duration=probe_audio(track_file)['durationMs']
    asset=AssetStore(db.media_dir).put_file(track_file)['assetId']
    question=next(q for f,_,q in iter_questions(paper) if f['formCode']=='JAPANESE_JA' and q['answerSpec']['type']=='SINGLE_CHOICE')
    changed=copy.deepcopy(paper)
    changed['audioTracks']=[{'trackId':'test-track','assetId':asset,'durationMs':duration,'cues':[{'cueId':'one','startMs':0,'endMs':300,'questionRefs':[question['answerRef']]}]}]
    db.publish(prepare_paper(changed),channel='PUBLIC')
    open_session(page,db,changed,url,['JAPANESE_JA'])
    expect(page.locator('#session-audio audio')).to_have_count(1)
    page.locator('#session-audio button',has_text='片段 one').click()
    page.wait_for_function("() => {const a=document.querySelector('#session-audio audio');return a.paused && a.currentTime>=.3 && a.currentTime<1}")
    sid=page.evaluate('state.activeSession.sessionId')
    page.wait_for_function("async sid=>(await (await fetch(`/api/v1/sessions/${sid}/audio`)).json()).progress?.position_ms>=300",arg=sid)
    page.reload()
    expect(page.locator('#session-audio audio')).to_have_count(1)
    page.wait_for_function("() => document.querySelector('#session-audio audio').currentTime>=.3")
