"""Redacted diagnostics and conservative retention for regenerable artifacts."""
import datetime as dt
import importlib.metadata
import json
import platform
import shutil
import time
from pathlib import Path
from .errors import ContractError
from .util import utc_now,digest_json


def diagnostics(db):
    checks={}
    for package in ['eju-question-bank','jsonschema','pymupdf','soundfile','playwright']:
        try:checks[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:checks[package]=None
    tables={r[0] for r in db.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts={name:db.connection.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0] for name in ['papers','paper_versions','practice_sessions','jobs','content_issues','attempt_facts'] if name in tables}
    failures=[dict(r) for r in db.connection.execute("SELECT job_type,status,json_extract(progress_json,'$.errorCode') errorCode FROM jobs WHERE status IN ('FAILED','INTERRUPTED','PARTIAL_FAILED') ORDER BY updated_at DESC LIMIT 30")]
    from .schema_validation import validator
    schema_status='passed'
    try:
        for name in ['page-contract','paper','content-inventory','source-structure']:validator(name)
    except Exception:schema_status='failed'
    return {'diagnosticsVersion':1,'createdAt':utc_now(),'platform':platform.system(),'python':platform.python_version(),'dependencies':checks,'schemaResources':schema_status,'integrity':db.connection.execute('PRAGMA integrity_check').fetchone()[0],'foreignKeyViolations':len(db.connection.execute('PRAGMA foreign_key_check').fetchall()),'counts':counts,'failedJobs':failures,'freeDiskBytes':shutil.disk_usage(db.workspace_root).free,'containsPrivateContent':False}


def retention_plan(db,*,older_than_days=30):
    if type(older_than_days) is not int or older_than_days<1:raise ContractError('Retention days must be a positive integer')
    active=db.connection.execute("SELECT 1 FROM jobs WHERE status IN ('RUNNING','QUEUED','CANCEL_REQUESTED')").fetchone()
    if active:raise ContractError('Wait for production jobs to finish before cache retention')
    threshold=time.time()-older_than_days*86400;files=[]
    root=db.workspace_root
    for source in (root/'work').glob('*'):
        for directory in ['render','renders']:
            for path in (source/directory).rglob('*'):
                if path.is_file() and (path.suffix in {'.png','.sha256'} or (path.name.startswith('render-index-') and path.suffix=='.json')) and not path.is_symlink() and path.resolve().is_relative_to(root) and path.stat().st_mtime<threshold:
                    stat=path.stat();files.append({'path':str(path.relative_to(root)),'sizeBytes':stat.st_size,'mtimeNs':stat.st_mtime_ns,'reason':'Regenerable PDF render cache'})
    return {'planId':digest_json(files),'files':files,'bytes':sum(f['sizeBytes'] for f in files),'preserves':['source PDFs','signed pages','OCR raw output','media','history','backups']}


def apply_retention(db,plan_id,*,older_than_days=30):
    with db._transaction():
        plan=retention_plan(db,older_than_days=older_than_days)
        if plan['planId']!=plan_id:raise ContractError('Retention plan changed; preview again')
        for record in plan['files']:
            path=(db.workspace_root/record['path']).resolve()
            if not path.is_relative_to(db.workspace_root):raise ContractError('Cache path escaped workspace')
            stat=path.stat()
            if stat.st_size!=record['sizeBytes'] or stat.st_mtime_ns!=record['mtimeNs']:raise ContractError('Cache changed since preview')
            path.unlink()
    return {'removedFiles':len(plan['files']),'removedBytes':plan['bytes']}

PERSONAL_TABLES=['essay_reviews','session_review_annotations','session_review_content','attempt_facts','session_audio_events','save_receipts','session_state','session_events','responses','results','practice_sessions','bookmarks','note_revisions','question_notes','wrong_question_state','review_events','learning_goals','action_receipts','practice_previews']

def personal_data_preview(db):
    counts={};fingerprints={}
    for table in PERSONAL_TABLES:
        rows=[list(r) for r in db.connection.execute(f'SELECT * FROM {table} ORDER BY rowid')]
        counts[table]=len(rows);fingerprints[table]=digest_json(rows)
    return {'planId':digest_json(fingerprints),'counts':counts,'preserves':['source files','published questions','content reviews','content issue reports','verified backups']}


def delete_personal_data(db,plan_id,confirmed):
    if confirmed is not True:raise ContractError('Explicit personal-data deletion confirmation is required')
    from .ops import create_backup,verify_backup
    backup=create_backup(database_path=db.path,inventory_path=db.workspace_root/'content/content-inventory.json',media_dir=db.media_dir,output_dir=db.workspace_root/'backups')
    verify_backup(backup)
    with db._transaction():
        plan=personal_data_preview(db)
        if plan['planId']!=plan_id:raise ContractError('Learning records changed; preview the deletion again')
        db.connection.execute('UPDATE content_issues SET session_id=NULL WHERE session_id IS NOT NULL')
        for table in PERSONAL_TABLES:db.connection.execute(f'DELETE FROM {table}')
        db._log('DELETE_PERSONAL_DATA','workspace','personal',{'counts':plan['counts'],'backupName':backup.name})
    return {'deleted':plan['counts'],'backupName':backup.name}
