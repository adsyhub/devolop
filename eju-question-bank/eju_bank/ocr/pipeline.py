"""Content-identified OCR attempts with resumable runs and atomic output."""
from __future__ import annotations
import hashlib
import time
import uuid
from pathlib import Path
from typing import Any
from ..constants import PAGE_CONTRACT_VERSION
from ..errors import ContractError
from ..page_contract import validate_page_contract
from ..prompts import page_prompt
from ..source import validate_source_manifest
from ..util import canonical_json, digest_json, load_json, sha256_file, utc_now, write_json
from .providers import PageProvider, provider_from_config


def compute_ocr_cache_key(*, source_hash, page_number, role, image_hashes, render_profile,
                          provider_identity, prompt_hash, contract_version=PAGE_CONTRACT_VERSION,
                          validator_version='2.2'):
    return digest_json({'sourceHash': source_hash, 'pageNumber': page_number, 'role': role,
                       'imageHashes': image_hashes, 'renderProfile': render_profile,
                       'provider': provider_identity, 'promptHash': prompt_hash,
                       'contractVersion': contract_version, 'validatorVersion': validator_version})


def extract_pages(*, manifest_path: Path, render_index_path: Path, output_dir: Path,
                  provider: PageProvider | None = None, provider_config=None, provider_name=None,
                  pages=None, retry_failed=False, resume_run=None, retry=False, database=None,
                  cancelled=None, on_progress=None):
    manifest_path = manifest_path.expanduser().resolve()
    render_index_path = render_index_path.expanduser().resolve()
    manifest = load_json(manifest_path)
    validate_source_manifest(manifest, manifest_path, verify_files=True)
    index = load_json(render_index_path)
    if index.get('sourceId') != manifest['sourceId']:
        raise ContractError('Render index belongs to a different source manifest')
    role = index.get('role')
    if role not in {'QUESTION_BOOKLET', 'ANSWER_KEY'}:
        raise ContractError('Invalid render role')
    source_hash = next(f['sha256'] for f in manifest['files'] if f['role'] == role)
    if index.get('sourceHash') != source_hash:
        raise ContractError('Render index source hash is missing or stale; render the source again')
    if provider is None:
        if provider_config is None or not provider_name:
            raise ContractError('Provider configuration is required')
        provider = provider_from_config(Path(provider_config).resolve(), provider_name)
    identity = provider.identity() if callable(getattr(provider, 'identity', None)) else {
        'providerType': type(provider).__name__, 'model': 'UNKNOWN', 'revision': 'UNKNOWN'}
    all_pages = index.get('pages', [])
    if any(type(p.get('page')) is not int or p['page'] < 1 for p in all_pages):
        raise ContractError('Invalid render page number')
    numbers = {p['page'] for p in all_pages}
    if len(numbers) != len(all_pages): raise ContractError('Duplicate render pages')
    if pages is None:
        selected = numbers
    elif isinstance(pages, str):
        selected = set()
        for piece in pages.split(','):
            bounds = piece.strip().split('-')
            if len(bounds) > 2: raise ContractError('Invalid page selection')
            start, end = int(bounds[0]), int(bounds[-1])
            if start > end or end-start > 10000: raise ContractError('Invalid page range')
            selected.update(range(start,end+1))
    elif isinstance(pages, (list, set)) and all(type(p) is int for p in pages):
        selected = set(pages)
    else:
        raise ContractError('Invalid page selection')
    if not selected or not selected <= numbers: raise ContractError('Selected page absent from render index')
    output_dir = output_dir.expanduser().resolve();output_dir.mkdir(parents=True,exist_ok=True)
    run_identity = digest_json({'source':source_hash,'sourceId':manifest['sourceId'],'role':role,
                                'provider':identity,'index':index, 'prompt':page_prompt(manifest,page=0,role=role),
                                'contractVersion':PAGE_CONTRACT_VERSION,'validatorVersion':'2.2'})
    runs = output_dir / 'runs'
    run_id = resume_run or 'run_' + uuid.uuid4().hex
    if not isinstance(run_id,str) or not run_id.startswith('run_') or not run_id[4:].isalnum():
        raise ContractError('Invalid run ID')
    run_root = runs / run_id
    metadata_path = run_root / 'run.json'
    if resume_run:
        if not metadata_path.is_file() or load_json(metadata_path).get('inputDigest') != run_identity:
            raise ContractError('Run belongs to different source or configuration')
    run_root.mkdir(parents=True,exist_ok=True)
    run_meta={'runId':run_id,'sourceId':manifest['sourceId'],'inputDigest':run_identity,
              'status':'RUNNING','provider':identity,'startedAt':utc_now()}
    write_json(metadata_path,run_meta)
    if database:
        database.connection.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?)',
            (manifest['sourceId'],manifest['rights']['status'],canonical_json(manifest),utc_now()))
        database.connection.execute("INSERT OR IGNORE INTO extraction_runs VALUES (?,?,?,?,?,?,?,'RUNNING',?)",
            (run_id,manifest['sourceId'],identity.get('providerType','UNKNOWN'),identity.get('model','UNKNOWN'),
             identity.get('revision','UNKNOWN'),'v2',canonical_json(identity),utc_now()))
        database.connection.commit()
    reports=[]
    try:
        for item in all_pages:
            number=int(item['page'])
            if number not in selected: continue
            if cancelled and cancelled():
                run_meta['status']='CANCELLED';break
            started=time.perf_counter()
            path=output_dir/f'p{number:04d}-{role.lower()}.json'
            cache_path=output_dir/'.cache'/f'{path.stem}.json'
            attempt_root=run_root/role/f'{number:04d}'
            attempt_root.mkdir(parents=True,exist_ok=True)
            attempt=len(list(attempt_root.glob('attempt-*.json')))+1
            cache_key=None
            try:
                images=[render_index_path.parent/item['full']['path']]
                images.extend(render_index_path.parent/t['path'] for t in item.get('tiles',[]))
                if any(not p.resolve().is_relative_to(render_index_path.parent) or not p.is_file() for p in images):
                    raise ContractError('Render image is missing or outside render directory')
                hashes=[sha256_file(p) for p in images]
                if hashes != [r.get('sha256') for r in [item['full'], *item.get('tiles',[])]]:
                    raise ContractError('Render image hash mismatch; render the source again')
                prompt=page_prompt(manifest,page=number,role=role)
                cache_key=compute_ocr_cache_key(source_hash=source_hash,page_number=number,role=role,
                    image_hashes=hashes,render_profile=index.get('settings',{}),provider_identity=identity,
                    prompt_hash=hashlib.sha256(prompt.encode()).hexdigest())
                cache=load_json(cache_path) if cache_path.is_file() else {}
                cached = False
                if path.is_file() and not retry and cache.get('key')==cache_key and cache.get('outputHash')==sha256_file(path):
                    report=validate_page_contract(load_json(path))
                    cached = not retry_failed or report['status']=='passed'
                if not cached:
                    raw=provider.transcribe(images=images,prompt=prompt,page=number,role=role)
                    write_json(attempt_root/f'raw-{attempt}.json',raw)
                    if not isinstance(raw,dict): raise ContractError('OCR result must be an object')
                    if raw.get('page') != number or type(raw.get('page')) is not int or raw.get('sourceFileRole') != role or raw.get('schemaVersion') != PAGE_CONTRACT_VERSION:
                        raise ContractError('OCR result page, role or schema version mismatch')
                    page={**raw,'sourceFileHash':source_hash}
                    report=validate_page_contract(page)
                    write_json(attempt_root/f'page-{attempt}.json',page)
                    if path.is_file():
                        previous = load_json(path)
                        if previous.get('reviewedBy') or previous.get('reviewedAt'):
                            raise ContractError('Signed output cannot be replaced by OCR')
                        write_json(attempt_root/f'previous-{attempt}.json',previous)
                    write_json(path,page)
                    write_json(cache_path,{'key':cache_key,'outputHash':sha256_file(path),'runId':run_id})
                entry={'page':number,'cached':cached,**report,'outputHash':sha256_file(path)}
            except Exception as exc:
                entry={'page':number,'cached':False,'status':'failed',
                       'issues':[{'code':type(exc).__name__,'message':'Page extraction failed; check source and provider configuration'}]}
            entry['durationMs']=int((time.perf_counter()-started)*1000)
            write_json(attempt_root/f'attempt-{attempt}.json',entry)
            if database:
                database.connection.execute('INSERT INTO extraction_page_attempts '
                    '(id,run_id,role,page_number,attempt_number,input_cache_key,output_digest,duration_ms,status,error_code,error_message,created_at) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    ('att_'+uuid.uuid4().hex,run_id,role,number,attempt,cache_key,entry.get('outputHash'),entry['durationMs'],
                     'SUCCEEDED' if entry['status']=='passed' else 'FAILED',
                     entry.get('issues',[{}])[0].get('code') if entry.get('issues') else None,
                     'Extraction failed' if entry['status']!='passed' else None,utc_now()))
                database.connection.commit()
            reports.append(entry)
            write_json(run_root/'quality.json',{'pages':reports})
            if on_progress:on_progress(reports)
        if run_meta['status']!='CANCELLED':
            run_meta['status']='SUCCEEDED' if all(p['status']=='passed' for p in reports) else 'PARTIAL_FAILED'
    except BaseException:
        run_meta['status']='INTERRUPTED'
        raise
    finally:
        run_meta['endedAt']=utc_now();write_json(metadata_path,run_meta)
        if database:
            database.connection.execute('UPDATE extraction_runs SET status=? WHERE id=?',(run_meta['status'],run_id))
            database.connection.commit()
    quality={'schemaVersion':PAGE_CONTRACT_VERSION,'sourceId':manifest['sourceId'],'role':role,'runId':run_id,
             'createdAt':utc_now(),'runStatus':run_meta['status'],'status':'passed' if run_meta['status']=='SUCCEEDED' else 'failed','pages':reports}
    write_json(output_dir/f'quality-report-{role.lower()}.json',quality)
    return quality
