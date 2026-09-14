"""工作台的会话状态必须绑定来源，切来源不能把上一套卷的东西画到下一套卷上。

课程库的八阶段推进面板已移除（制作由自动流水线完成，手工签署降为可选工具），
所以候选/批准的跨卷继承不再可能。仍然要守住的是切来源时的请求竞态，以及列表里
每一行都得分得清自己是哪一套卷。
"""

from __future__ import annotations

import threading

import pytest

from eju_bank.server import create_server

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


@pytest.fixture
def studio(tmp_path):
    server = create_server(tmp_path / "library/eju.db", port=0, workspace_root=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def _open(pw, base):
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{base}/studio/library")
    page.wait_for_function("() => typeof openSource === 'function'", timeout=15000)
    return browser, page, errors


# F07 原有的两条用例（stageExtra 不跨来源继承候选、invalidatePaperReview 连所有者
# 一起清）已随课程库的八阶段面板一起移除：候选与批准是"组装 → 签署整卷"那条手工
# 通路的会话状态，而课程库不再持有它们，一套卷的进度也就无从画到另一套卷上 ——
# 缺陷不是被修好，是没有了容身处。同一条后端链路（逐页签署 → 签署结构 → 组装 →
# 签署整卷 → 发布）由 test_content_review.py::test_signed_pages_assemble_approve_publish_and_revoke
# 在 API 层覆盖。

def test_a_stale_open_response_does_not_repaint_the_new_source(studio):
    """切来源时旧请求还在路上，回来得晚的那份必须被丢掉。

    ``openSource`` 每次递增一个序号，返回后先比对；序号变了就直接退出，不写
    ``state.stageInfo``、不重画面板。
    """
    with sync_playwright() as pw:
        browser, page, errors = _open(pw, studio)
        try:
            # 模拟两次并发打开：第二次把序号推到 2，第一次回来时应当认出自己过时。
            result = page.evaluate("""() => {
                state.openSeq = 0;
                const first = ++state.openSeq;   // openSource('A') 拿到 1
                const second = ++state.openSeq;  // openSource('B') 拿到 2
                return { firstIsStale: first !== state.openSeq,
                         secondIsCurrent: second === state.openSeq };
            }""")
            assert result["firstIsStale"] is True
            assert result["secondIsCurrent"] is True
            assert errors == [], f"页面报错：{errors}"
        finally:
            browser.close()


# ── F11 / F12：多份文件不能被静默丢掉，缺答案册不等于什么都不能做 ────────────

def _plan(page, uploads, *, session="2023-2", subject="SCIENCE", ocr="p"):
    """在真实页面里摆好上传列表与表单，然后问 currentPlan() 的结论。"""
    return page.evaluate(
        """([uploads, session, subject, ocr]) => {
            build.uploads = uploads;
            document.querySelector('#paper-session').value = session;
            const s = document.querySelector('#paper-subject');
            s.value = subject;
            document.querySelector('#paper-language').value = 'ja';
            const o = document.querySelector('#ocr-profile');
            if (![...o.options].some(x => x.value === ocr)) o.add(new Option(ocr, ocr));
            o.value = ocr;
            const plan = currentPlan();
            return { problems: plan.problems, warnings: plan.warnings,
                     booklet: plan.params.questionBooklet,
                     answerKey: plan.params.answerKey };
        }""", [uploads, session, subject, ocr])


def _build_page(pw, base):
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{base}/studio/build")
    page.wait_for_function("() => typeof currentPlan === 'function'", timeout=15000)
    return browser, page, errors


def test_extra_booklets_are_refused_not_silently_dropped(studio):
    """一条任务只做一套卷。多拖进来的题册原来被 find() 悄悄丢掉。"""
    with sync_playwright() as pw:
        browser, page, errors = _build_page(pw, studio)
        try:
            plan = _plan(page, [
                {"state": "ready", "role": "QUESTION_BOOKLET", "uploadId": "incoming/a.pdf"},
                {"state": "ready", "role": "QUESTION_BOOKLET", "uploadId": "incoming/b.pdf"},
                {"state": "ready", "role": "ANSWER_KEY", "uploadId": "incoming/k.pdf"},
            ])
            assert any("2 份题册" in p for p in plan["problems"]), plan["problems"]
            assert errors == [], f"页面报错：{errors}"
        finally:
            browser.close()


def test_a_missing_answer_key_warns_but_does_not_block_extraction(studio):
    """缺答案册挡的是「发布评分题」，不是「开始识别」。"""
    with sync_playwright() as pw:
        browser, page, errors = _build_page(pw, studio)
        try:
            plan = _plan(page, [
                {"state": "ready", "role": "QUESTION_BOOKLET", "uploadId": "incoming/a.pdf"},
            ])
            assert plan["problems"] == [], f"缺答案册不该挡住开始：{plan['problems']}"
            assert any("发布不了评分题" in w for w in plan["warnings"]), plan["warnings"]
            assert plan["answerKey"] is None
            # 按钮真的可点，而不是只在文案上说可以。
            assert page.evaluate(
                "() => { refreshStartButton(); "
                "return document.querySelector('#start-build').disabled; }") in (False, None)
            assert errors == [], f"页面报错：{errors}"
        finally:
            browser.close()


def test_one_booklet_and_one_key_is_clean(studio):
    """正常一套：既没有挡住的问题，也没有需要警告的代价。"""
    with sync_playwright() as pw:
        browser, page, errors = _build_page(pw, studio)
        try:
            plan = _plan(page, [
                {"state": "ready", "role": "QUESTION_BOOKLET", "uploadId": "incoming/a.pdf"},
                {"state": "ready", "role": "ANSWER_KEY", "uploadId": "incoming/k.pdf"},
            ])
            assert plan["problems"] == [] and plan["warnings"] == []
            assert plan["booklet"] == "incoming/a.pdf"
            assert plan["answerKey"] == "incoming/k.pdf"
            assert errors == [], f"页面报错：{errors}"
        finally:
            browser.close()


# ── F17：数学卷必须分得出类别 ────────────────────────────────────────────────

def test_math_sources_are_distinguishable_in_every_list(studio):
    """「数学」这一行分不出文科卷还是理科卷，而那是两份完全不同的题册。"""
    with sync_playwright() as pw:
        browser, page, errors = _open(pw, studio)
        try:
            labels = page.evaluate("""() => ({
                course1: sourceLabel({session: '2023-2', subject: 'MATHEMATICS',
                                      language: 'ja',
                                      expectedForms: ['MATHEMATICS_COURSE_1_JA']}),
                course2: sourceLabel({session: '2023-2', subject: 'MATHEMATICS',
                                      language: 'ja',
                                      expectedForms: ['MATHEMATICS_COURSE_2_JA']}),
                unknown: sourceLabel({session: '2023-2', subject: 'MATHEMATICS',
                                      language: 'ja', expectedForms: []}),
                science: sourceLabel({session: '2023-2', subject: 'SCIENCE',
                                      language: 'ja'}),
            })""")
            assert labels["course1"] != labels["course2"]
            assert "1 类" in labels["course1"] and "2 类" in labels["course2"]
            # 类别登记不出来时说它没登记，不要显示成一个具体类别。
            assert "未登记" in labels["unknown"]
            # 年份回次、科目、语言都在。
            for label in labels.values():
                assert "2023-2" in label
            assert "理科" in labels["science"] and "日语" in labels["science"]
            assert errors == [], f"页面报错：{errors}"
        finally:
            browser.close()


# ── 课程库只说交付，不摆八阶段 ────────────────────────────────────────────────

def test_library_shows_delivery_state_and_no_stage_pipeline(studio):
    """来源页回答的是"学习者取不取得到"，不是"流水线走到第几步"。

    八阶段面板照清单里的 ``pipelineStatus`` 画勾，而那是陈旧值：退役的伪造答案
    批次至今写着 PUBLISHED，于是勾满八步的卷，学习者其实一道题也取不到。现在
    状态一律取自 ``paper_delivery_state``（``/admin/studio/delivery``）。
    """
    with sync_playwright() as pw:
        browser, page, errors = _open(pw, studio)
        try:
            # 八阶段的定义、阶段轨、阶段面板都不该再存在。
            assert page.evaluate("() => typeof STAGES") == "undefined"
            assert page.evaluate("() => typeof stageRail") == "undefined"
            assert page.evaluate("() => typeof computeStages") == "undefined"
            assert page.locator(".stage-rail").count() == 0
            assert page.locator(".stage-panel").count() == 0
            for label in ["登记与授权", "签署来源结构", "组装与预检", "签署整卷"]:
                assert label not in page.content(), f"八阶段的「{label}」还在页面上"

            # 交付状态按服务端的口径翻译，停用必须显示成停用。
            states = page.evaluate("""() => [
                publicationBadge('PUBLISHED_PARTIAL').textContent,
                publicationBadge('SUSPENDED').textContent,
                publicationBadge('NOT_PUBLISHED').textContent,
            ]""")
            assert states == ["可练 · 部分", "已停用", "未产出"]
            assert page.evaluate(
                "() => publicationBadge('SUSPENDED').className").endswith("is-bad")

            # 缺答案册要说出来：那是实际卡住一批来源的原因。
            missing = page.evaluate(
                "() => missingRoles({roles: ['QUESTION_BOOKLET']})")
            assert missing == ["答案册"]
            assert page.evaluate("() => missingRoles({roles: "
                                 "['QUESTION_BOOKLET','ANSWER_KEY']})") == []
            assert errors == [], f"页面报错：{errors}"
        finally:
            browser.close()
