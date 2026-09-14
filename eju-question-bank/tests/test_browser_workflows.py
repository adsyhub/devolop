from test_browser_learning import browser_app,open_session,open_reading_settings
from playwright.sync_api import expect


def test_cross_tab_conflict_accept_remote_and_draft_isolation(browser_app):
    page,db,paper,url=browser_app
    sid=open_session(page,db,paper,url,['PHYSICS_JA'])
    qid=db.get_session_paper(sid)['forms'][0]['groups'][0]['questions'][0]['questionId']
    second=page.context.new_page();second.goto(f'{url}/practice#/session/{sid}')
    expect(second.locator(f'input[name="q_{qid}"]')).to_have_count(4)
    second.route('**/responses:batch',lambda route:route.abort())
    second.locator(f'input[name="q_{qid}"][value="2"]').check()
    expect(second.locator('#save-status')).to_contain_text('保存失败')
    page.locator(f'input[name="q_{qid}"][value="1"]').check()
    expect(page.locator('#save-status')).to_have_text('● 已保存')
    second.on('dialog',lambda d:d.dismiss())
    second.unroute('**/responses:batch')
    second.evaluate('() => flushAutoSave()')
    expect(second.locator(f'input[name="q_{qid}"][value="1"]')).to_be_checked()
    assert db.get_session(sid)['responses'][qid]['value']['optionKey']=='1'
    assert second.evaluate('Object.keys(state.pendingResponses).length')==0
    assert second.evaluate('getDraftKey(state.activeSession.sessionId)').count('.')>=3
    second.close()


def test_navigation_stats_and_empty_essay(browser_app):
    page,db,paper,url=browser_app
    sid=open_session(page,db,paper,url,['PHYSICS_JA','CHEMISTRY_JA'])
    open_reading_settings(page)
    page.locator('#question-view').select_option('SINGLE')
    expect(page.locator('.question-card:visible')).to_have_count(1)
    first=page.locator('.question-card:visible').get_attribute('id')
    page.keyboard.press('Escape')
    page.locator('#question-next').click()
    assert page.locator('.question-card:visible').get_attribute('id')!=first
    page.goto(f'{url}/me#/analytics')
    expect(page.locator('#learning-summary')).to_contain_text('暂无样本')
    page.locator('#goal-new').fill('12');page.get_by_role('button',name='保存目标',exact=True).click()
    expect(page.locator('#goal-new')).to_have_value('12')
    assert db.goals()['newQuestions']==12


def test_management_backup_job_and_diagnostics(browser_app):
    from eju_bank.util import write_json
    page,db,paper,url=browser_app
    write_json(db.workspace_root/'content/content-inventory.json',{'schemaVersion':1,'updatedAt':'2026-01-01T00:00:00Z','items':[]})
    page.goto(f'{url}/studio/ops#/ops/backups')
    expect(page.locator('.ops-panel[data-ops="backups"]')).to_be_visible()
    page.locator('#backup-create').click()
    page.goto(f'{url}/studio/ops#/ops/jobs')
    expect(page.locator('#job-list')).to_contain_text('SUCCEEDED',timeout=15000)
    page.goto(f'{url}/studio/ops#/ops/backups')
    expect(page.locator('#backup-list a')).to_have_count(1)
    page.get_by_role('button',name='校验',exact=True).click()
    expect(page.locator('#management-status')).to_contain_text('备份校验通过')


def test_narrow_screen_navigation_and_modal_keyboard(browser_app):
    page,db,paper,url=browser_app
    page.set_viewport_size({'width':360,'height':800})
    sid=open_session(page,db,paper,url,['PHYSICS_JA'])
    open_reading_settings(page)
    page.locator('#question-view').select_option('SINGLE')
    page.keyboard.press('Escape')
    expect(page.locator('.question-card:visible')).to_have_count(1)
    assert page.evaluate('document.documentElement.scrollWidth')<=365, page.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>365 && e.getBoundingClientRect().width>0).map(e=>[e.tagName,e.id,e.className,e.getBoundingClientRect().width]).slice(0,20)")
    first=page.locator('.question-card input[type=radio]').first
    first.focus();page.keyboard.press('Space')
    expect(first).to_be_checked()
    expect(page.locator('#save-status')).to_have_text('● 已保存')
