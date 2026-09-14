"""Exact HTTP routes for versioned production and learning workflows."""
from __future__ import annotations
import csv
import io
import json
import re
from pathlib import Path
from .errors import ContractError
from .jobs import JobManager
from .util import load_json,write_json,utc_now


def dispatch(h,method,path,body,q):
    db=h.database;ws=h.server.content_workspace
    def route(verb,pattern,action,status=200):
        match=re.fullmatch(pattern,path)
        if (method != verb and not (verb == 'GET' and method == 'HEAD')) or not match: return False
        h._json(action(*match.groups()),status);return True
    if route('POST',r'/api/v1/admin/sources/([^/]+)/pages/([^/]+)/(\d+)/withdraw',lambda sid,role,num:ws.withdraw_page(sid,role,int(num),body.get('revisionId'),body.get('reviewer'),body.get('reason'))):return True
    from .maintenance import diagnostics,retention_plan,apply_retention,personal_data_preview,delete_personal_data
    if route('POST',r'/api/v1/admin/personal-data/preview',lambda:personal_data_preview(db)):return True
    if route('POST',r'/api/v1/admin/personal-data/delete',lambda:delete_personal_data(db,body.get('planId'),body.get('confirmed'))):return True
    if route('GET',r'/api/v1/admin/diagnostics',lambda:diagnostics(db)):return True
    if route('POST',r'/api/v1/admin/retention/preview',lambda:retention_plan(db,older_than_days=body.get('olderThanDays',30))):return True
    if route('POST',r'/api/v1/admin/retention/apply',lambda:apply_retention(db,body.get('planId'),older_than_days=body.get('olderThanDays',30))):return True
    if route('POST',r'/api/v1/admin/paper-versions/([^/]+)/delivery',lambda vid:db.set_delivery_state(vid,body.get('state'),body.get('reason'),reason_code=body.get('reasonCode','CONTENT_REVIEW'))):return True
    if route('GET',r'/api/v1/learning/summary',lambda:db.learning_summary(form=q('form'),start=q('start'),end=q('end'))):return True
    if route('GET',r'/api/v1/learning/calendar',lambda:db.learning_calendar(q('timezone','Asia/Tokyo'))):return True
    if route('GET',r'/api/v1/learning/goals',db.goals):return True
    if route('PUT',r'/api/v1/learning/goals',lambda:db.goals(body)):return True
    if route('GET',r'/api/v1/questions/([^/]+)/attempts',lambda qid:{'attempts':db.question_attempts(qid)}):return True
    if route('GET',r'/api/v1/sessions/([^/]+)/outline',db.session_outline):return True
    if route('GET',r'/api/v1/sessions/([^/]+)/questions',lambda sid:db.session_questions(sid,cursor=q('cursor',0),limit=int(q('limit',50)))):return True
    if route('GET',r'/api/v1/sessions/([^/]+)/review-content',lambda sid:db.review_content(sid,latest=q('latest')=='true')):return True
    if route('GET',r'/api/v1/sessions/([^/]+)/assessments',lambda sid:{'assessments':db.essay_assessments(sid)}):return True
    if route('POST',r'/api/v1/sessions/([^/]+)/essays/([^/]+)/self-assessment',lambda sid,qid:db.assess_essay(sid,qid,body.get('assessment'),base_revision=body.get('baseRevision',0)),201):return True
    if route('POST',r'/api/v1/admin/sessions/([^/]+)/essays/([^/]+)/assessment',lambda sid,qid:db.assess_essay(sid,qid,body.get('assessment'),kind='HUMAN',reviewer=body.get('reviewer'),base_revision=body.get('baseRevision',0)),201):return True
    if route('GET',r'/api/v1/rubrics',lambda:{'rubrics':[{'rubricRevisionId':r['id'],**json.loads(r['payload_json'])} for r in db.connection.execute('SELECT * FROM rubric_revisions ORDER BY created_at,id')]}):return True
    if route('POST',r'/api/v1/admin/rubrics',lambda:db.save_rubric(body.get('rubric'),body.get('reviewer')),201):return True
    if route('GET',r'/api/v1/admin/questions/([^/]+)/explanations',lambda qvid:{'revisions':[{'revisionId':r['id'],'revision':r['revision'],'status':r['status'],'payload':json.loads(r['payload_json'])} for r in db.connection.execute('SELECT * FROM explanation_revisions WHERE question_version_id=? ORDER BY revision',(qvid,))]}):return True
    if route('POST',r'/api/v1/admin/questions/([^/]+)/explanations',lambda qvid:db.save_explanation(qvid,body.get('payload'),base_revision=body.get('baseRevision',0),status=body.get('status','DRAFT'),reviewer=body.get('reviewer')),201):return True
    if route('POST',r'/api/v1/practice/previews',lambda:db.preview_practice(body),201):return True
    if route('POST',r'/api/v1/practice/previews/([^/]+)/start',lambda pid:db.start_preview(pid,body.get('requestId')),201):return True
    if route('GET',r'/api/v1/history',lambda:db.history_page(cursor=q('cursor',0),limit=int(q('limit',50)),status=q('status'))):return True
    if route('GET',r'/api/v1/admin/content-issues',lambda:{'issues':db.list_content_issues(status=q('status'),question_id=q('questionId'),limit=int(q('limit',50)))}):return True
    if route('POST',r'/api/v1/admin/papers',lambda:create_make_paper_job(h,{'params':body}),202):return True
    if route('GET',r'/api/v1/admin/models',lambda:model_catalog(h)):return True
    if route('POST',r'/api/v1/admin/jobs',lambda:create_job(h,body),202):return True
    if route('POST',r'/api/v1/admin/backup',lambda:JobManager.create_job(db,'BACKUP','workspace',{'mode':body.get('mode','LEARNING')}),202):return True
    if route('GET',r'/api/v1/admin/backups',lambda:{'backups':[{'id':r['id'],'sizeBytes':r['size_bytes'],'createdAt':r['created_at'],'name':Path(r['backup_file']).name} for r in db.connection.execute('SELECT * FROM backup_history ORDER BY created_at DESC')]}):return True
    if route('POST',r'/api/v1/admin/backups/([^/]+)/verify',lambda bid:backup_action(h,bid,'verify')):return True
    if route('POST',r'/api/v1/admin/backups/([^/]+)/restore',lambda bid:backup_action(h,bid,'restore',body)):return True
    m=re.fullmatch(r'/api/v1/admin/backups/([^/]+)/download',path)
    if method=='GET' and m:
        path=backup_path(h,m[1]);data=path.read_bytes();h.send_response(200);h.send_header('Content-Type','application/zip');h.send_header('Content-Disposition','attachment; filename="eju-backup.zip"');h.send_header('Content-Length',str(len(data)));h.end_headers();h.wfile.write(data);return True
    if route('POST',r'/api/v1/admin/sources/([^/]+)/audio-import',lambda sid:import_audio(h,sid,body),201):return True
    if route('POST',r'/api/v1/admin/sources/([^/]+)/audio',lambda sid:db.register_audio(sid,body.get('assetId'),body.get('cues'),body.get('reviewer')),201):return True
    if route('GET',r'/api/v1/sessions/([^/]+)/audio',db.session_audio):return True
    if route('POST',r'/api/v1/sessions/([^/]+)/audio/progress',lambda sid:db.save_audio_progress(sid,body.get('trackId'),body.get('positionMs'),body.get('action'))):return True
    if route('POST',r'/api/v1/admin/sources/([^/]+)/bind-inventory',lambda sid:bind_inventory(h,sid,body.get('inventoryId'))):return True
    if route('POST',r'/api/v1/admin/publications/sync',lambda:(ws.sync_publications() or {'synced':True})):return True
    if route('GET',r'/api/v1/sessions/([^/]+)/export',lambda sid:report_export(db,sid)):return True
    m=re.fullmatch(r'/api/v1/sessions/([^/]+)/export.csv',path)
    if method=='GET' and m:
        data=report_export(db,m[1]);out=io.StringIO();writer=csv.writer(out);writer.writerow(['questionId','answered','correct','status'])
        for row in data['questions']:writer.writerow([csv_safe(row[k]) for k in ['questionId','answered','correct','status']])
        encoded=out.getvalue().encode('utf-8-sig');h.send_response(200);h.send_header('Content-Type','text/csv; charset=utf-8');h.send_header('Content-Disposition','attachment; filename="learning-report.csv"');h.send_header('Content-Length',str(len(encoded)));h.end_headers();h.wfile.write(encoded);return True
    return False


# 本地 OCR 三步走同一条任务队列，但参数形状与 PDF 渲染类任务不同：
# 它们没有 role/pages，只有 force 与可选的模型端点。分开校验，免得两边的
# 允许键互相污染。
OCR_JOBS = {'OCR_TEXT', 'OCR_SLOTS', 'OCR_CONTRACTS'}
OCR_PARAMS = {'force', 'url', 'model', 'roles', 'forms'}


def create_ocr_job(h, body):
    from .jobs import JobManager
    params = body.get('params') or {}
    if not isinstance(params, dict) or set(params) - OCR_PARAMS:
        raise ContractError('Invalid OCR job parameters')
    if type(params.get('force', False)) is not bool:
        raise ContractError('Invalid force flag')
    for key in ('url', 'model'):
        if params.get(key) is not None and (not isinstance(params[key], str) or len(params[key]) > 500):
            raise ContractError(f'Invalid {key}')
    if params.get('url') is not None and not params['url'].startswith(('http://127.0.0.1', 'http://localhost')):
        # 视觉服务必须在本机：让页面指定任意地址等于把原页图发到外部。
        raise ContractError('OCR endpoint must be on the loopback interface')
    for key in ('roles', 'forms'):
        value = params.get(key)
        if value is not None and (not isinstance(value, list) or len(value) > 16
                                  or not all(isinstance(x, str) and len(x) <= 64 for x in value)):
            raise ContractError(f'Invalid {key}')
    h.server.content_workspace.source(body.get('sourceId'))
    return JobManager.create_job(h.database, body['jobType'], body['sourceId'], params)


# 制课那条一键流水线的参数。档位名只能从 config/providers.json 里挑，
# 由 model_profiles.resolve 校验；这里管形状，不管模型对不对。
MAKE_PAPER_PARAMS = {
    'questionBooklet', 'answerKey', 'session', 'subject', 'course', 'language',
    'ocrProfile', 'proofreadProfile', 'textProfile', 'explainProfile',
    'proofreadPages', 'proofreadPaper', 'explain', 'explainLimit',
    'stopAtDraft', 'force', 'channel',
}
SUBJECTS = {'SCIENCE', 'MATHEMATICS', 'JAPAN_AND_WORLD', 'JAPANESE'}


def create_make_paper_job(h, body):
    from .model_profiles import resolve
    from .paper_naming import inventory_id
    from .uploads import resolve as resolve_upload

    params = body.get('params') or {}
    if not isinstance(params, dict) or set(params) - MAKE_PAPER_PARAMS:
        raise ContractError('Invalid 制课 parameters')
    root = h.server.content_workspace.root
    # 上传句柄必须现在就能解析成工作区里的文件：任务是异步的，让它跑起来再
    # 发现文件不存在，等于把一个必然失败的任务排进队列。
    resolve_upload(root, params.get('questionBooklet'))
    if params.get('answerKey'):
        resolve_upload(root, params['answerKey'])
    session = str(params.get('session') or '')
    if not re.fullmatch(r'(19|20)\d{2}-[12]', session):
        raise ContractError('Session must look like 2023-2')
    subject = str(params.get('subject') or '')
    if subject not in SUBJECTS:
        raise ContractError('Unsupported subject')
    course = params.get('course') or None
    if subject == 'MATHEMATICS' and course not in {'COURSE_1', 'COURSE_2'}:
        raise ContractError('Mathematics needs COURSE_1 or COURSE_2')
    if subject != 'MATHEMATICS' and course:
        raise ContractError('Only mathematics has course editions')
    language = str(params.get('language') or 'ja')
    if language not in {'ja', 'en'}:
        raise ContractError('language must be ja or en')
    if subject == 'JAPANESE' and language != 'ja':
        raise ContractError('The EJU Japanese subject is administered in Japanese only')
    resolve(root, 'vision', params.get('ocrProfile'))
    for family, key in (('vision', 'proofreadProfile'), ('text', 'textProfile'),
                        ('text', 'explainProfile')):
        if params.get(key):
            resolve(root, family, params[key])
    for flag in ('proofreadPages', 'proofreadPaper', 'explain', 'stopAtDraft', 'force'):
        if flag in params and type(params[flag]) is not bool:
            raise ContractError(f'Invalid {flag} flag')
    limit = params.get('explainLimit', 0)
    if type(limit) is not int or not 0 <= limit <= 500:
        raise ContractError('explainLimit must be 0 to 500')
    if params.get('channel', 'PRIVATE') != 'PRIVATE':
        # 发布到 PRIVATE 之外的渠道是授权决定，不是制课台按一下的事。
        raise ContractError('制课 publishes to the private library only')
    target = inventory_id(session, subject, course, language)
    return JobManager.create_job(h.database, 'MAKE_PAPER', target, params)


def create_job(h,body):
    if body.get('jobType')=='MAKE_PAPER':return create_make_paper_job(h,body)
    if body.get('jobType') in OCR_JOBS:return create_ocr_job(h,body)
    if body.get('jobType') not in {'PROBE','RENDER','EXTRACT'}:raise ContractError('Unsupported job type')
    h.server.content_workspace.source(body.get('sourceId'))
    params=body.get('params',{k:body[k] for k in ['role','pages','provider'] if k in body})
    if not isinstance(params,dict):raise ContractError('Invalid job parameters')
    params.setdefault('role','QUESTION_BOOKLET')
    if not isinstance(params,dict) or set(params)-{'role','pages','configRef','provider','retryFailed','resumeRun'}:raise ContractError('Invalid job parameters')
    if params.get('role','QUESTION_BOOKLET') not in {'QUESTION_BOOKLET','ANSWER_KEY'}:raise ContractError('Invalid PDF role')
    if params.get('pages') is not None and (not isinstance(params['pages'],str) or len(params['pages'])>10000):raise ContractError('Invalid page selection')
    if type(params.get('retryFailed',False)) is not bool:raise ContractError('Invalid retryFailed flag')
    if params.get('configRef','config/providers.json')!='config/providers.json':raise ContractError('Use the workspace provider configuration')
    if params.get('resumeRun') is not None and (not isinstance(params['resumeRun'],str) or not re.fullmatch(r'run_[a-zA-Z0-9]+',params['resumeRun'])):raise ContractError('Invalid run ID')
    if body['jobType']=='EXTRACT':
        config=h.server.content_workspace.root/'config/providers.json'
        if not isinstance(params.get('provider'),str) or not config.is_file() or params['provider'] not in load_json(config).get('providers',{}):raise ContractError('Select a provider from config/providers.json')
    return JobManager.create_job(h.database,body['jobType'],body['sourceId'],params)


def model_catalog(h):
    """制作台要显示的模型清单。页面只能从这里挑，不能自己写端点。"""
    from .model_profiles import describe
    return describe(h.server.content_workspace.root)


def bind_inventory(h,sid,iid):
    from .inventory import get_inventory_item
    ws=h.server.content_workspace;path,manifest=ws.source(sid);item=get_inventory_item(iid,ws.root/'content/content-inventory.json')
    if not item or any(item[k]!=manifest[k] for k in ['session','subject','language']):raise ContractError('Inventory target does not match the source')
    if manifest.get('inventoryId') and manifest['inventoryId']!=iid:raise ContractError('Create a separate source edition to change its inventory binding')
    manifest['inventoryId']=iid;write_json(path,manifest);return {'inventoryId':iid,'sourceId':sid}


def backup_path(h,bid):
    row=h.database.connection.execute('SELECT backup_file FROM backup_history WHERE id=?',(bid,)).fetchone()
    if not row:raise KeyError(bid)
    path=Path(row[0]).resolve()
    if not path.is_file():raise KeyError(bid)
    return path


def backup_action(h,bid,action,body=None):
    from .ops import verify_backup,restore_backup
    from .worker import inside
    path=backup_path(h,bid)
    if action=='verify':return verify_backup(path)
    target=inside(h.server.content_workspace.root,body.get('targetDirectory'))
    if target.exists():raise ContractError('Restore only into a new directory')
    return restore_backup(path,target)


def csv_safe(value):
    text='' if value is None else str(value)
    return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) else text


def report_export(db,sid):
    result=db.get_result(sid)
    return {'sessionId':sid,'scoringVersion':result['scoringVersion'],'officialScore':False,'objectiveCorrect':result['objectiveCorrect'],'objectiveTotal':result['objectiveTotal'],'questions':[{k:q.get(k) for k in ['questionId','answered','correct','status']} for q in result['questions']]}


def import_audio(h,sid,body):
    from .assets import AssetStore
    from .audio import probe_audio
    from .job_worker import workspace_file
    _,manifest=h.server.content_workspace.source(sid)
    path=workspace_file(h.server.content_workspace.root,body.get('filePath'))
    probe=probe_audio(path)
    declared=[f for f in manifest['files'] if f['role']=='AUDIO']
    if len(declared)!=1 or declared[0]['sha256']!=probe['sha256']:raise ContractError('Import and declare this audio source before attaching it')
    meta=AssetStore(h.database.media_dir).put_file(path);meta.pop('absolutePath',None)
    return {**meta,'durationMs':probe['durationMs']}
