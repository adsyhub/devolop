"""Real Chromium regressions. Run: python scripts/verify_lexicon_browser.py.
Requires development-only playwright + Chromium; uses a temporary learner database.
"""
from pathlib import Path
import json, sys, tempfile, threading
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from playwright.sync_api import sync_playwright
from support import write_course
from serve_course import build_preview_server


def main():
    with tempfile.TemporaryDirectory(prefix='lexicon-e2e-') as directory:
        root=Path(directory)
        server=build_preview_server(write_course(root/'courses/demo'),port=0,data_dir=root/'data',lexicon_root=ROOT/'lexicon')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
                context=browser.new_context(viewport={'width':1280,'height':900})
                page=context.new_page();errors=[];passed=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.port}/lexicon')
                page.wait_for_function('() => state.packs.length>=2')
                def create(count=1):
                    page.evaluate('''async count=>{const {session}=await post('./api/lexicon/sessions',{kind:'word',packSlugs:['Everyday-words'],types:['reading'],count},uid());navigate('#/practice/'+session.id);}''',count)
                    page.wait_for_selector('.lex-answer-form textarea')
                def answer():
                    return page.evaluate('''async ()=>{const {session}=await api('./api/lexicon/sessions/'+state.session.id+'/offline');return session.items.find(q=>q.id===state.session.state.queue[state.session.state.cursor].itemId).acceptedAnswers[0];}''')
                create();page.locator('.lex-answer-form textarea').fill('保存した答え')
                page.wait_for_timeout(650);page.reload();page.wait_for_selector('.lex-answer-form textarea')
                assert page.locator('.lex-answer-form textarea').input_value()=='保存した答え'
                passed.append('online draft recovery')
                page.locator('.lex-answer-form textarea').fill(answer())
                page.get_by_role('button',name='提交答案',exact=True).click()
                page.get_by_role('button',name='下一题',exact=True).wait_for()
                page.reload();page.get_by_role('button',name='下一题',exact=True).wait_for()
                assert '独立答对' in page.locator('#session-body').inner_text()
                passed.append('unread feedback recovery')
                create();value=answer()
                page.evaluate("() => {window.originalTransaction=IDBDatabase.prototype.transaction;IDBDatabase.prototype.transaction=function(...args){if(args[1]==='readwrite')throw new DOMException('Storage failure injected','QuotaExceededError');return originalTransaction.apply(this,args);};}")
                page.locator('.lex-answer-form textarea').fill(value)
                page.get_by_role('button',name='提交答案',exact=True).click()
                page.wait_for_function('() => !state.busy')
                assert page.evaluate('() => state.session.state.cursor')==0
                assert page.evaluate('async () => (await api("./api/lexicon/sessions/"+state.session.id)).session.attempts.length')==0
                page.evaluate('() => {IDBDatabase.prototype.transaction=originalTransaction;}')
                passed.append('IndexedDB quota failure does not send or advance answer')

                page.locator('#lex-tab-practice').click();page.wait_for_selector('#practice-form:visible')
                page.locator('#practice-kind').select_option('word');page.locator('#practice-pack').select_option('Everyday-words')
                page.locator('#practice-count').fill('1')
                for control in page.locator('#practice-types input').all():
                    if not control.is_disabled():control.set_checked(control.get_attribute('value')=='meaning')
                page.locator('#practice-drafts').check()
                page.get_by_role('button',name='开始练习',exact=True).click()
                page.wait_for_selector('.lex-answer-choice')
                assert '未通过内容审核' in page.locator('#session-body').inner_text()
                passed.append('explicit draft practice and qualification notice')
                create(2);page.locator('.lex-answer-form textarea').fill(answer())
                def drop_response(route):
                    response=route.fetch();assert response.status==200;route.abort('failed')
                page.route('**/sessions/*/answers',drop_response)
                page.get_by_role('button',name='提交答案',exact=True).click()
                page.wait_for_function('() => !state.busy')
                assert page.evaluate('async ()=>(await pendingOperations()).length')==1
                page.unroute('**/sessions/*/answers',drop_response)
                page.evaluate('async ()=>{await syncPractice();await loadSession(state.session.id);}')
                assert page.evaluate('() => state.session.state.cursor')==1
                assert page.evaluate('async ()=>(await pendingOperations()).length')==0
                assert page.evaluate('() => state.session.attempts.length')==1
                passed.append('lost response idempotent recovery')
                create()
                page.evaluate('''async ()=>{let s=state.session;for(let i=0;i<3;i++){const task=s.state.queue[s.state.cursor];({session:s}=await post('./api/lexicon/sessions/'+s.id+'/answers',{...task,answer:null,skipped:true,version:s.version},uid()));}await loadSession(s.id);}''')
                page.get_by_role('button',name='回到跳过的题',exact=True).click()
                page.wait_for_selector('.lex-answer-form textarea');page.locator('.lex-answer-form textarea').fill(answer())
                page.get_by_role('button',name='提交答案',exact=True).click();page.get_by_role('button',name='下一题',exact=True).wait_for()
                assert '独立答对' in page.locator('#session-body').inner_text()
                page.get_by_role('button',name='下一题',exact=True).click();page.get_by_role('button',name='提交并查看报告',exact=True).click()
                page.wait_for_function('()=>document.querySelector("#session-heading").textContent==="练习报告"')
                assert '100%' in page.locator('#session-body').inner_text()
                passed.append('skipped question resume and report')
                create();page.locator('#session-offline').click()
                page.wait_for_function('() => state.session.offlineQuestions?.length>0')
                value=answer();context.set_offline(True)
                page.locator('.lex-answer-form textarea').fill(value);page.get_by_role('button',name='提交答案',exact=True).click()
                page.get_by_role('button',name='下一题',exact=True).wait_for()
                context.set_offline(False)
                page.evaluate('async ()=>{await syncPractice();await loadSession(state.session.id);}')
                assert page.evaluate('async ()=>(await pendingOperations()).length')==0
                assert page.evaluate('() => state.session.attempts.length')==1
                passed.append('prepared offline answer and replay')
                create();page.locator('#session-offline').click()
                page.wait_for_function('() => state.session.offlineQuestions?.length>0')
                value=answer();context.set_offline(True)
                for _ in range(3):
                    page.get_by_role('button',name='跳过并稍后重试',exact=True).click()
                    page.get_by_role('button',name='下一题',exact=True).click()
                page.get_by_role('button',name='回到跳过的题',exact=True).click()
                page.wait_for_selector('.lex-answer-form textarea')
                page.locator('.lex-answer-form textarea').fill(value)
                page.get_by_role('button',name='提交答案',exact=True).click()
                page.get_by_role('button',name='下一题',exact=True).wait_for()
                context.set_offline(False)
                page.evaluate('async ()=>{await syncPractice();await loadSession(state.session.id);}')
                assert page.evaluate('async ()=>(await pendingOperations()).length')==0
                assert page.evaluate('()=>state.session.attempts.length')==4
                passed.append('offline skips, new round and ordered replay')

                create();page.locator('#session-offline').click()
                page.wait_for_function('() => state.session.offlineQuestions?.length>0')
                value=answer();port=server.port
                page.evaluate('async ()=>{await navigator.serviceWorker.ready;}')
                page.reload();page.wait_for_selector('.lex-answer-form textarea')
                server.shutdown();thread.join(timeout=5);server.close()
                page.reload();page.wait_for_selector('.lex-answer-form textarea')
                page.locator('.lex-answer-form textarea').fill(value)
                page.get_by_role('button',name='提交答案',exact=True).click()
                page.get_by_role('button',name='下一题',exact=True).wait_for()
                page.reload();page.get_by_role('button',name='下一题',exact=True).wait_for()
                server=build_preview_server(root/'courses/demo/manifest.json',port=port,data_dir=root/'data',lexicon_root=ROOT/'lexicon')
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                page.evaluate('async ()=>{await syncPractice();await loadSession(state.session.id);}')
                assert page.evaluate('async ()=>(await pendingOperations()).length')==0
                assert page.evaluate('()=>state.session.attempts.length')==1
                passed.append('stop local service, refresh, answer, refresh, restart and replay')

                page.set_viewport_size({'width':390,'height':844});page.goto(f'http://127.0.0.1:{server.port}/lexicon')
                page.wait_for_function('()=>state.packs.length>=2')
                assert page.evaluate('()=>document.documentElement.scrollWidth')<=390
                assert not errors,errors
                passed.append('mobile initial layout and no page exceptions')
                print(json.dumps({'passed':passed},ensure_ascii=False,indent=2));browser.close()
        finally:
            server.shutdown();thread.join(timeout=5);server.close()

if __name__=='__main__':main()
