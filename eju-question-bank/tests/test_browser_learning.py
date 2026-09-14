"""User-visible learning flows on a temporary database, no external network."""
from conftest import install_fixture_media
import json
import threading
from pathlib import Path
import pytest
from eju_bank.db import Database
from eju_bank.server import create_server

pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright, expect


@pytest.fixture
def browser_app(tmp_path):
    paper = json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    db = Database(tmp_path / 'library.db')
    install_fixture_media(db.path.parent / 'media')
    db.publish(paper, channel='PUBLIC')
    httpd = create_server(db.path, port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context=browser.new_context()
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('https://**/*', lambda route: route.abort())
        url = f'http://127.0.0.1:{httpd.server_port}'
        try:
            yield page, db, paper, url
            assert not errors
        finally:
            browser.close()
            httpd.shutdown()
            thread.join(timeout=5)
            httpd.server_close()
            httpd.database.close()
            db.close()


def open_session(page, db, paper, url, forms):
    """Land straight in the answering view of a fresh session.

    The UI is split into three workspaces now; answering lives at
    /practice#/session/<id>, so the deep link is what a learner would follow
    from the entry page or from 我的.
    """
    sess = db.create_session(paper['paperId'], forms)
    page.goto(f"{url}/practice#/session/{sess['sessionId']}")
    expect(page.locator('#view-session')).to_be_visible()
    expect(page.locator('#question-container .question-card').first).to_be_visible()
    return sess['sessionId']


def open_reading_settings(page):
    """显示范围 / 排版 / 字号 live in the ⚙ popover, not the session bar."""
    if page.locator('#reading-settings').is_hidden():
        page.locator('#reading-settings-button').click()
        expect(page.locator('#reading-settings')).to_be_visible()


def test_save_reload_pause_submit_and_history(browser_app):
    page, db, paper, url = browser_app
    sid = open_session(page, db, paper, url, ['PHYSICS_JA', 'CHEMISTRY_JA'])
    questions = db.get_session_paper(sid)
    qid = questions['forms'][0]['groups'][0]['questions'][0]['questionId']
    page.locator(f'input[name="q_{qid}"][value="1"]').check()
    expect(page.locator('#save-status')).to_have_text('● 已保存')
    page.reload()
    expect(page.locator(f'input[name="q_{qid}"][value="1"]')).to_be_checked()
    page.locator('#btn-pause').click()
    expect(page.locator('#workspace-state')).to_contain_text('已暂停')
    expect(page.locator(f'input[name="q_{qid}"][value="1"]')).to_be_disabled()
    page.locator('#btn-pause').click()
    expect(page.locator(f'input[name="q_{qid}"][value="1"]')).to_be_enabled()
    page.on('dialog', lambda d: d.accept())
    page.locator('#btn-submit').click()
    expect(page.locator('#res-total')).to_have_text('2')
    expect(page.locator('#res-detail')).to_contain_text('未答 1')
    expect(page.locator('.correct-key')).to_have_count(2)
    # 练习记录搬到了 /me；那里的「查看详情」是回到 practice 的复盘深链。
    page.goto(f'{url}/me#/history')
    expect(page.locator('#history-tbody tr').first).to_be_visible()
    page.get_by_role('link', name='查看详情', exact=True).first.click()
    expect(page.locator('#view-result')).to_be_visible()
    expect(page.locator('.correct-key')).to_have_count(2)
    expect(page.locator('#res-total')).to_have_text('2')


def test_offline_save_does_not_submit(browser_app):
    page, db, paper, url = browser_app
    sid = open_session(page, db, paper, url, ['PHYSICS_JA'])
    page.route('**/responses:batch', lambda route: route.abort())
    page.locator('.option-item input').first.check()
    expect(page.locator('#save-status')).to_contain_text('保存失败')
    page.on('dialog', lambda d: d.accept())
    page.locator('#btn-submit').click()
    expect(page.locator('#btn-submit')).to_be_enabled()
    assert db.get_session(sid)['status'] == 'IN_PROGRESS'
    page.reload()
    expect(page.locator('.option-item input').first).to_be_checked()
    page.unroute('**/responses:batch')
    page.locator('#save-status').click()
    expect(page.locator('#save-status')).to_have_text('● 已保存')
    assert len(db.get_session(sid)['responses']) == 1


def test_essay_pending_and_offline_math(browser_app):
    page, db, paper, url = browser_app
    sid = open_session(page, db, paper, url, ['JAPANESE_JA'])
    page.locator('.essay-textarea').fill('これは記述の回答です。')
    expect(page.locator('#save-status')).to_have_text('● 已保存')
    page.on('dialog', lambda d: d.accept())
    page.locator('#btn-submit').click()
    page.locator('input[name="review-filter"][value="PENDING"]').check()
    expect(page.locator('#review-list .review-item')).to_have_count(1)
    expect(page.locator('#review-list')).to_contain_text('记述待评阅')
    expect(page.locator('.essay-review')).to_have_text('これは記述の回答です。')
    sid = open_session(page, db, paper, url, ['MATHEMATICS_COURSE_1_JA'])
    expect(page.locator('.katex')).to_have_count(1)
    page.locator('.slot-select').first.select_option('2')
    expect(page.locator('#save-status')).to_have_text('● 已保存')
    page.reload()
    expect(page.locator('.slot-select').first).to_have_value('2')


def test_bookmark_note_collection_and_image_zoom(browser_app):
    page, db, paper, url = browser_app
    sid = open_session(page, db, paper, url, ['PHYSICS_JA'])
    page.get_by_role('button', name='☆ 收藏', exact=True).click()
    page.locator('.note-editor summary').click()
    page.locator('.note-input').fill('检查受力方向')
    expect(page.locator('.note-save')).to_have_text('笔记已保存')
    page.locator('.figure-img').first.click()
    expect(page.locator('#modal-image-zoom')).not_to_have_class('modal hidden')
    expect(page.locator('#zoom-img')).to_be_visible()
    assert page.locator('#zoom-img').evaluate('(img) => img.naturalWidth') > 0
    page.locator('#modal-zoom-close').click()
    page.reload()
    expect(page.get_by_role('button', name='★ 已收藏', exact=True)).to_be_visible()
    page.locator('.note-editor summary').click()
    expect(page.locator('.note-input')).to_have_value('检查受力方向')
    page.goto(f'{url}/practice#/collect')
    expect(page.locator('#view-collect')).to_be_visible()
    page.locator('#collection-kind').select_option('BOOKMARKED')
    expect(page.locator('#collection-list .paper-card')).to_have_count(1)
    page.get_by_role('button', name='练习此题', exact=True).click()
    page.get_by_role('button', name='开始预览中的练习', exact=True).click()
    expect(page.locator('#top-paper-title')).to_have_text('专项练习')
    expect(page.locator('#question-container .question-card')).to_have_count(1)


def test_machine_attested_paper_says_so_before_the_learner_starts(browser_app):
    """一份只经机器校验的卷，必须在选卷和开始作答之前就把把关程度说清楚。"""
    page, db, paper, url = browser_app
    graded = {**paper, 'reviewGrade': 'MACHINE_ATTESTED',
              'missingContentReasons': ['PHYSICS_JA：正解表列出 19 个解答欄，本次发布收录 3 个。']}
    from eju_bank.audit import prepare_paper
    db.publish(prepare_paper(graded), channel='PUBLIC')

    page.goto(f"{url}/practice#/subject/SCIENCE/papers")
    card = page.locator('.paper-card').first
    expect(card).to_be_visible()
    badge = card.locator('.badge', has_text='机器校验')
    expect(badge).to_be_visible()
    # 徽标的 title 必须写明没有断言什么，而不是只给一个好看的标签。
    assert '未经人工' in (badge.get_attribute('title') or '')

    page.goto(f"{url}/practice#/paper/{paper['paperId']}")
    note = page.locator('#setup-review-note')
    expect(note).to_be_visible()
    expect(note).to_contain_text('机器校验')
    expect(note).to_contain_text('正解表列出 19 个解答欄')
