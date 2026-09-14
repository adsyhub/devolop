"""Durable, leased workspace jobs. Heavy work runs outside HTTP request threads."""
from __future__ import annotations

import os
import random
import shutil
import tempfile
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .errors import ContractError
from .jobs import JobManager
from .util import canonical_json, digest_json, load_json, sha256_file, utc_now, write_json


class JobCancelled(Exception):
    pass


def workspace_file(root, ref):
    if not isinstance(ref,str) or not ref or Path(ref).is_absolute():
        raise ContractError('A workspace relative file is required')
    path = (root / ref).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > 150_000_000:
        raise ContractError('Import file is absent, too large or outside this workspace')
    return path


class JobWorker:
    # 一条任务自动恢复几次就不再自动恢复。不是越多越好：同样的输入、同样的策略
    # 失败之后再跑一遍还是失败，剩下的只有等人看一眼。
    MAX_ATTEMPTS = 3
    RETRY_BASE_SECONDS = 15

    def __init__(self, database, workspace):
        self.db, self.workspace = database, workspace
        self.owner = uuid.uuid4().hex
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self._loop, name='eju-jobs', daemon=True)

    def start(self):
        self.thread.start()

    def close(self):
        self.stopping.set()
        self.thread.join(timeout=10)

    def _claim(self):
        now = utc_now()
        lease = (datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat().replace('+00:00','Z')
        with self.db._transaction():
            expired = self.db.connection.execute("SELECT id FROM jobs WHERE status IN ('RUNNING','CANCEL_REQUESTED') AND (lease_until IS NULL OR lease_until<?)",(now,)).fetchall()
            for row in expired:
                self.db.connection.execute("UPDATE jobs SET status='INTERRUPTED',lease_owner=NULL,lease_until=NULL,updated_at=? WHERE id=?",(now,row['id']))
                self.db.connection.execute("INSERT INTO job_events VALUES (?,?, 'INTERRUPTED',?,?)",(uuid.uuid4().hex,row['id'],canonical_json({'reason':'Worker lease expired'}),now))
            self._recover_interrupted(now)
            if self.db.connection.execute("SELECT 1 FROM jobs WHERE status IN ('RUNNING','CANCEL_REQUESTED') LIMIT 1").fetchone(): return None
            row = self.db.connection.execute("SELECT id FROM jobs WHERE status='QUEUED' AND (next_attempt_at IS NULL OR next_attempt_at<=?) ORDER BY created_at,id LIMIT 1",(now,)).fetchone()
            if not row: return None
            self.db.connection.execute("UPDATE jobs SET status='RUNNING',lease_owner=?,lease_until=?,updated_at=? WHERE id=? AND status='QUEUED'",(self.owner,lease,now,row['id']))
            self.db.connection.execute("INSERT INTO job_events VALUES (?,?,'STATUS_RUNNING','{}',?)",(uuid.uuid4().hex,row['id'],now))
        return JobManager.get_job(self.db,row['id'])

    def _recover_interrupted(self, now):
        """把中断的任务自动排回队列。必须在同一个事务里调用。

        worker 崩溃或租约过期之后，任务停在 INTERRUPTED 就不动了——除非有人回到
        页面上手工点重试。规范 §9.5 要求这一类故障默认不需要用户参与。

        两条边界：
        * **用户主动取消的不复活。**CANCELLED 是一个决定，不是一次故障。
        * **重试有预算。**同样的输入、同样的策略失败之后再跑一遍还是失败，无限
          重试只是把故障变成忙等。超出预算的留在 INTERRUPTED 等人看。
        """
        rows = self.db.connection.execute(
            "SELECT id, attempts FROM jobs WHERE status='INTERRUPTED' AND attempts<?",
            (self.MAX_ATTEMPTS,)).fetchall()
        for row in rows:
            attempts = int(row['attempts'] or 0) + 1
            # 退避带抖动：连续故障时不要所有任务同时回来。
            delay = min(self.RETRY_BASE_SECONDS * (2 ** (attempts - 1)), 900)
            delay = delay * (0.75 + 0.5 * random.random())
            when = (datetime.now(timezone.utc) + timedelta(seconds=delay)
                    ).isoformat().replace('+00:00', 'Z')
            self.db.connection.execute(
                "UPDATE jobs SET status='QUEUED',attempts=?,next_attempt_at=?,updated_at=? WHERE id=?",
                (attempts, when, now, row['id']))
            self.db.connection.execute(
                "INSERT INTO job_events VALUES (?,?,'RETRY_SCHEDULED',?,?)",
                (uuid.uuid4().hex, row['id'],
                 canonical_json({'attempt': attempts, 'limit': self.MAX_ATTEMPTS,
                                 'nextAttemptAt': when,
                                 'reason': '中断后自动恢复'}), now))

    def _heartbeat(self, jid, finished):
        try:
            while not finished.wait(10):
                lease=(datetime.now(timezone.utc)+timedelta(seconds=60)).isoformat().replace('+00:00','Z')
                with self.db._transaction():
                    self.db.connection.execute('UPDATE jobs SET lease_until=? WHERE id=? AND lease_owner=?',(lease,jid,self.owner))
        finally: self.db.close()

    def _cancelled(self,jid):
        row=self.db.connection.execute('SELECT status,lease_owner FROM jobs WHERE id=?',(jid,)).fetchone()
        return self.stopping.is_set() or not row or row['lease_owner']!=self.owner or row['status']=='CANCEL_REQUESTED'

    def _checkpoint(self,jid):
        if self._cancelled(jid): raise JobCancelled()

    def _progress(self,jid,progress):
        with self.db._transaction():
            self.db.connection.execute('UPDATE jobs SET progress_json=?,updated_at=? WHERE id=? AND lease_owner=?',
                                       (canonical_json(progress),utc_now(),jid,self.owner))

    def _loop(self):
        try:
            while not self.stopping.is_set():
                try:
                    self.db.expire_sessions()
                    job=self._claim()
                except Exception:
                    self.stopping.wait(1); continue
                if not job:
                    self.stopping.wait(.2); continue
                finished=threading.Event()
                heartbeat=threading.Thread(target=self._heartbeat,args=(job['jobId'],finished),daemon=True);heartbeat.start()
                try:
                    result=self.execute(job)
                    status=result.pop('jobStatus','SUCCEEDED')
                    progress={'percent':100,'stage':status,**result}
                except JobCancelled:
                    status='INTERRUPTED' if self.stopping.is_set() else 'CANCELLED'
                    progress={'stage':status,'message':'Stopped at a safe checkpoint; completed artifacts are retained'}
                except Exception as exc:
                    status='FAILED';progress={'stage':'FAILED','errorCode':type(exc).__name__,
                        'message':'任务失败，请检查文件、来源配置和依赖；详细产物保留在任务目录'}
                finally:
                    finished.set();heartbeat.join(timeout=2)
                with self.db._transaction():
                    row=self.db.connection.execute('SELECT lease_owner FROM jobs WHERE id=?',(job['jobId'],)).fetchone()
                    if row and row['lease_owner']==self.owner:
                        self.db.connection.execute('UPDATE jobs SET status=?,progress_json=?,updated_at=?,lease_owner=NULL,lease_until=NULL WHERE id=?',
                            (status,canonical_json(progress),utc_now(),job['jobId']))
                        self.db.connection.execute('INSERT INTO job_events VALUES (?,?,?,?,?)',(uuid.uuid4().hex,job['jobId'],'STATUS_'+status,canonical_json(progress),utc_now()))
        finally: self.db.close()

    def execute(self,job):
        from .pdf_pipeline import render_manifest
        jid,params,kind=job['jobId'],job['params'],job['jobType']
        self._checkpoint(jid)
        if kind=='IMPORT_SOURCE': return self._import(job)
        if kind=='MAKE_PAPER': return self._make_paper(job)
        if kind=='BACKUP':
            from .ops import create_backup, verify_backup
            path=create_backup(database_path=self.db.path,inventory_path=self.workspace.root/'content/content-inventory.json',
                               media_dir=self.db.media_dir,output_dir=self.workspace.root/'backups',workspace_root=self.workspace.root,mode=params.get('mode','LEARNING'))
            verify_backup(path)
            return {'backupFile':path.name,'sizeBytes':path.stat().st_size,'verified':True}
        manifest_path,manifest=self.workspace.source(job['targetId'])
        if kind=='PROBE':
            from .pdf_pipeline import probe_manifest
            return probe_manifest(manifest_path,manifest_path.parent/'probe.json')
        if kind in {'OCR_TEXT','OCR_SLOTS','OCR_CONTRACTS'}:
            return self._ocr(job, manifest_path, manifest)
        role=params.get('role')
        if role not in {'QUESTION_BOOKLET','ANSWER_KEY'}: raise ContractError('Invalid render role')
        pages=job['progress'].get('retryPages') or params.get('pages')
        if isinstance(pages,list): pages=','.join(map(str,pages))
        render_root=manifest_path.parent/'renders'
        if kind=='RENDER':
            index=render_manifest(manifest_path,role=role,output_dir=render_root,pages=pages,
                cancelled=lambda:self._cancelled(jid),on_progress=lambda done,total:self._progress(jid,{'stage':'RENDERING','pagesCompleted':done,'pagesTotal':total,'percent':round(100*done/total)}))
            self._checkpoint(jid)
            return {'pagesCompleted':len(index['pages']),'profileId':index['profileId']}
        if kind=='EXTRACT':
            from .ocr.pipeline import extract_pages
            config=self.workspace.root/'config/providers.json'
            provider=params.get('provider')
            if not isinstance(provider,str) or provider not in load_json(config).get('providers',{}): raise ContractError('Select a configured provider')
            def progress(rows):
                self._progress(jid,{'stage':'EXTRACTING','pagesCompleted':len(rows), 'pagesFailed':sum(p['status']!='passed' for p in rows)})
            result=extract_pages(manifest_path=manifest_path,render_index_path=render_root/f'render-index-{role.lower()}.json',
                output_dir=manifest_path.parent/'pages',provider_config=config,provider_name=provider,pages=pages,
                retry_failed=job['progress'].get('failedOnly',params.get('retryFailed',False)),resume_run=params.get('resumeRun'),database=self.db,
                cancelled=lambda:self._cancelled(jid),on_progress=progress)
            self._checkpoint(jid)
            return {'jobStatus':result['runStatus'],'runId':result['runId'],'pagesCompleted':len(result['pages']),
                    'pagesFailed':sum(p['status']!='passed' for p in result['pages'])}
    def _make_paper(self, job):
        """制课：一条任务把上传的 PDF 做成可练的卷。

        来源在这一步里才被建出来，所以它排在 ``workspace.source()`` 之前 ——
        对别的任务类型那句是前提，对这一条它是产物。
        """
        from .make_paper import run_pipeline
        jid = job['jobId']
        return run_pipeline(
            root=self.workspace.root, database=self.db, workspace=self.workspace,
            params=job['params'],
            report=lambda progress: self._progress(jid, progress),
            cancelled=lambda: self._cancelled(jid),
            checkpoint=lambda: self._checkpoint(jid))

    def _ocr(self, job, manifest_path, manifest):
        jid, params, kind = job['jobId'], job['params'], job['jobType']
        # ── 本地视觉模型 OCR ───────────────────────────────────────────
        # 这三步把原页变成可复核的内容：读文本 → 读解答欄方框号 → 生成页面
        # 合同草稿。都走同一套 lease/心跳/进度，所以工作台能看到实时进展，
        # 也能中途取消。三步都可断点续跑，重跑不会重复识别已完成的页。
        if kind == 'OCR_TEXT':
            from .ocr.local_vision import ocr_source_pages
            result = ocr_source_pages(
                manifest_path.parent, roles=params.get('roles') or ['question_booklet', 'answer_key'],
                url=params.get('url'), model=params.get('model'), force=bool(params.get('force')),
                cancelled=lambda: self._cancelled(jid),
                on_progress=lambda done, total, failed: self._progress(
                    jid, {'stage': 'OCR_TEXT', 'pagesCompleted': done, 'pagesTotal': total,
                          'pagesFailed': failed, 'percent': round(100 * done / total) if total else 100}))
            self._checkpoint(jid)
            return result

        if kind == 'OCR_SLOTS':
            from .ocr.local_vision import ocr_source_slots
            result = ocr_source_slots(
                manifest_path.parent, url=params.get('url'), model=params.get('model'),
                force=bool(params.get('force')),
                cancelled=lambda: self._cancelled(jid),
                on_progress=lambda done, total, failed: self._progress(
                    jid, {'stage': 'OCR_SLOTS', 'pagesCompleted': done, 'pagesTotal': total,
                          'pagesFailed': failed, 'percent': round(100 * done / total) if total else 100}))
            self._checkpoint(jid)
            return result

        if kind == 'OCR_CONTRACTS':
            from .ocr.assemble_from_ocr import DEFAULT_SECTION_BY_SUBJECT, write_page_contracts
            from .ocr.verified_answers import load_verified_answers
            answers, problems = load_verified_answers(manifest_path.parent)
            self._progress(jid, {'stage': 'OCR_CONTRACTS', 'verifiedAnswers': len(answers),
                                 'answerProblems': len(problems)})
            result = write_page_contracts(
                manifest_path.parent,
                forms=params.get('forms') or _forms_for_subject(manifest.get('subject', '')),
                answers=answers,
                default_section=DEFAULT_SECTION_BY_SUBJECT.get(manifest.get('subject', '')),
                overwrite=bool(params.get('force')))
            self._checkpoint(jid)
            return {**result, 'verifiedAnswers': len(answers), 'answerProblems': len(problems)}

        raise ContractError('Unsupported OCR job type')

    def _import(self,job):
        from .source import create_source_manifest, file_record, validate_source_manifest
        from .inventory import get_inventory_item
        from .pdf_pipeline import probe_pdf
        jid,params,root=job['jobId'],job['params'],self.workspace.root
        item=get_inventory_item(job['targetId'],root/'content/content-inventory.json')
        if not item: raise ContractError('Inventory item not found')
        source=workspace_file(root,params['sourceRef'])
        role=params['role'];digest=sha256_file(source)
        if digest!=params['sourceHash']: raise ContractError('Import input changed since submission')
        self._progress(jid,{'stage':'PROBING','percent':10})
        if role=='AUDIO':
            from .audio import probe_audio
            probe=probe_audio(source)
            from .assets import AssetStore
            audio_asset=AssetStore(self.db.media_dir).put_file(source)
        else: probe=probe_pdf(source,role)
        self._checkpoint(jid)
        # Content-addressed, immutable input copy; retries reuse only verified bytes.
        folder=root/'sources/imports';folder.mkdir(parents=True,exist_ok=True)
        target=folder/(digest+('.pdf' if role!='AUDIO' else source.suffix.lower()))
        fd,temp=tempfile.mkstemp(dir=folder,suffix='.tmp');os.close(fd)
        try:
            shutil.copyfile(source,temp)
            if sha256_file(temp)!=digest: raise ContractError('Import input changed during copy')
            self._checkpoint(jid)
            os.replace(temp,target)
        finally:
            if os.path.exists(temp):os.unlink(temp)
        existing=[(p,m) for p,m in self.workspace._sources() if m.get('inventoryId')==job['targetId']]
        if len(existing)>1: raise ContractError('Inventory has multiple source manifests')
        if existing:
            path,manifest=existing[0]
            current=next((f for f in manifest['files'] if f['role']==role),None)
            if current and current['sha256']!=digest:
                raise ContractError('Role already has another source; create a separate inventory edition')
            record=file_record(target,role,stored_path=Path(os.path.relpath(target,path.parent)).as_posix())
            manifest['files']=[f for f in manifest['files'] if f['role']!=role]+[record]
        else:
            if role!='QUESTION_BOOKLET': raise ContractError('Import question booklet before other roles')
            path=root/'work'/('import-'+digest_json(job['targetId'])[:20])/'source-manifest.json'
            # Build separately so a crash cannot expose an unbound manifest.
            with tempfile.TemporaryDirectory(dir=root) as tempdir:
                manifest=create_source_manifest(session=item['session'],subject=item['subject'],language=item['language'],
                    syllabus_version=item['syllabusId'],question_booklet=target,answer_key=None,
                    rights_status=item['rightsStatus'],rights_note=item.get('notes','Imported source'),output_path=Path(tempdir)/'manifest.json')
            manifest['sourceId']='src_'+digest_json([job['targetId'],digest])[:24]
            manifest['files']=[file_record(target,role,stored_path=Path(os.path.relpath(target,path.parent)).as_posix())]
        manifest['inventoryId']=job['targetId']
        manifest['expectedForms']=item['expectedForms']
        validate_source_manifest(manifest,path,verify_files=True)
        self._checkpoint(jid)
        write_json(path,manifest)
        probe.pop('path',None);probe.pop('filePath',None)
        write_json(path.parent/('probe-'+role.lower()+'.json'),probe)
        return {'sourceId':manifest['sourceId'],'sourceHash':digest,'role':role,'assetId':audio_asset['assetId'] if role=='AUDIO' else None,'pageCount':probe.get('pageCount'),
                'message':'来源已验证并导入，尚需页面复核与签署'}


def _forms_for_subject(subject: str) -> list[str]:
    """Which forms a booklet of this subject carries."""
    return {
        "JAPANESE": ["JAPANESE_JA"],
        "SCIENCE": ["PHYSICS_JA", "CHEMISTRY_JA", "BIOLOGY_JA"],
        "JAPAN_AND_WORLD": ["JAPAN_AND_WORLD_JA"],
        "MATHEMATICS": ["MATHEMATICS_COURSE_1_JA", "MATHEMATICS_COURSE_2_JA"],
    }.get(subject, [])
