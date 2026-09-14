import json
import re
import threading
from pathlib import Path
import pytest
import pymupdf
from eju_bank.db import Database
from eju_bank.server import create_server
from eju_bank.source import create_source_manifest
from test_content_review import contract
pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright, expect


def test_review_from_page_to_publication_in_browser(tmp_path):
    (tmp_path/'sources').mkdir()
    for name,text in [('q.pdf','Choose 1 or 2'),('a.pdf','Answer 2')]:
        doc=pymupdf.open();page=doc.new_page();page.insert_text((40,40),text);doc.save(tmp_path/'sources'/name);doc.close()
    manifest=create_source_manifest(session='TEST',subject='SCIENCE',language='ja',syllabus_version='2015',
        question_booklet=tmp_path/'sources/q.pdf',answer_key=tmp_path/'sources/a.pdf',rights_status='PRIVATE_STUDY',rights_note='Synthetic browser fixture',
        output_path=tmp_path/'work/test/source-manifest.json')
    from eju_bank.inventory import upsert_inventory_item
    from eju_bank.util import write_json
    manifest['inventoryId']='fixture-source'
    write_json(tmp_path/'work/test/source-manifest.json',manifest)
    upsert_inventory_item({'inventoryId':'fixture-source','session':manifest['session'],'subject':'SCIENCE','language':'ja',
        'syllabusId':'basic-2015','requiredFiles':['QUESTION_BOOKLET','ANSWER_KEY'],'rightsStatus':'PRIVATE_STUDY',
        'pipelineStatus':'RECEIVED','expectedForms':['PHYSICS_JA']},tmp_path/'content/content-inventory.json')
    server=create_server(tmp_path/'library/eju.db',port=0,workspace_root=tmp_path)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);page=browser.new_page();errors=[]
            page.on('pageerror',lambda e: errors.append(str(e)))
            base=f'http://127.0.0.1:{server.server_port}'
            # 课程库不再有八阶段面板：从来源列表点进去是这套卷的交付状态页，
            # 人工复核作为可选工具从那里进入复核编辑器。
            page.goto(f'{base}/studio/library')
            expect(page.locator('.source-row').first).to_be_visible()
            page.locator('.source-row a').first.click()
            expect(page.locator('#source-status .delivery-badge')).to_be_visible()
            page.locator('#source-status a', has_text='人工复核').click()
            page.wait_for_url(re.compile(r'/studio/editor'))
            expect(page.locator('#view-review')).to_be_visible()
            expect(page.locator('#review-source option')).to_have_count(1)
            for role in ['QUESTION_BOOKLET','ANSWER_KEY']:
                page.locator('#review-role').select_option(role)
                page.locator('#review-open').click()
                expect(page.locator('#review-workbench')).to_be_visible()
                page.locator('summary',has_text='进阶：裁图').click()
                page.locator('#review-json').fill(json.dumps(contract(role)))
                page.locator('#review-apply-json').click()
                if role=='QUESTION_BOOKLET':
                    region=page.locator('.bbox-region').first
                    region.scroll_into_view_if_needed()
                    box=region.bounding_box()
                    page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
                    page.mouse.down();page.mouse.move(box['x']+box['width']/2+12,box['y']+box['height']/2+8,steps=4);page.mouse.up()
                    assert page.evaluate('reviewState.contract.blocks[0].bbox[0]')>.1
                page.locator('#review-save').click()
                expect(page.locator('#review-page-status')).to_contain_text('草稿已保存')
                page.locator('#review-signoff-reviewer').fill('browser-reviewer')
                page.locator('#review-confirmed').check()
                page.locator('#review-sign').click()
                expect(page.locator('#review-signature')).to_contain_text('已签署：browser-reviewer')
                page.locator('summary',has_text='进阶：裁图').click()
            page.locator('#review-back').click()
            # 签署结构 → 组装 → 签署整卷 → 发布原本是课程库的阶段 ⑤～⑧ 按钮。
            # 那些按钮已移除（自动流水线自己走完这条链），所以这里走它们当初调用的
            # 同一组接口，覆盖不丢。整条链路另由
            # test_content_review.py::test_signed_pages_assemble_approve_publish_and_revoke
            # 在 API 层单独覆盖。
            from eju_bank.audit import review_content_digest
            from eju_bank.review import ContentWorkspace
            sid = manifest['sourceId']
            ws = ContentWorkspace(tmp_path, server.database)
            ws.sign_source_structure(
                sid, {'forms': {'PHYSICS_JA': ['PHYSICS:1']},
                      'pages': {'QUESTION_BOOKLET': 1, 'ANSWER_KEY': 1}}, 'browser-reviewer')
            candidate = ws.candidate(sid)
            approved = ws.approve_paper(
                sid, review_content_digest(candidate['paper']), 'browser-reviewer', True)
            assert ws.publish_review(approved['reviewId'], 'PRIVATE')['version'] == 1
            assert not errors
            assert server.database.list_papers()[0]['completeness']=='COMPLETE'
            browser.close()
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close();server.database.close()
