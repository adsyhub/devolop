import copy
import json
import sqlite3
from pathlib import Path
import pytest
import pymupdf
from eju_bank.db import Database
from eju_bank.review import ContentWorkspace
from eju_bank.source import create_source_manifest
from eju_bank.errors import QualityGateError, SessionError
from eju_bank.audit import audit_paper, review_content_digest, prepare_paper


@pytest.fixture
def workspace(tmp_path):
    sources=tmp_path/'sources';sources.mkdir()
    for name,text in [('question.pdf','Choose: 1 or 2'),('answer.pdf','Answer: 2')]:
        doc=pymupdf.open();page=doc.new_page();page.insert_text((50,50),text);doc.save(sources/name);doc.close()
    manifest=create_source_manifest(session='test',subject='SCIENCE',language='ja',syllabus_version='2015',
        question_booklet=sources/'question.pdf',answer_key=sources/'answer.pdf',rights_status='PRIVATE_STUDY',rights_note='Test only',
        output_path=tmp_path/'work/test/source-manifest.json')
    from eju_bank.inventory import upsert_inventory_item
    from eju_bank.util import write_json
    manifest['inventoryId']='fixture-source'
    write_json(tmp_path/'work/test/source-manifest.json',manifest)
    upsert_inventory_item({'inventoryId':'fixture-source','session':manifest['session'],'subject':'SCIENCE','language':'ja',
        'syllabusId':'basic-2015','requiredFiles':['QUESTION_BOOKLET','ANSWER_KEY'],'rightsStatus':'PRIVATE_STUDY',
        'pipelineStatus':'RECEIVED','expectedForms':['PHYSICS_JA']},tmp_path/'content/content-inventory.json')
    db=Database(tmp_path/'library/eju.db');ws=ContentWorkspace(tmp_path,db)
    ws.sign_source_structure(manifest['sourceId'], {'forms':{'PHYSICS_JA':['PHYSICS:1']},'pages':{'QUESTION_BOOKLET':1,'ANSWER_KEY':1}}, 'fixture-lead')
    yield ws,db,manifest['sourceId']
    db.close()


def contract(role):
    base={'schemaVersion':2,'page':1,'sourceFileRole':role,'coverage':{'inkRegions':1,'accountedRegions':1,'regionIds':['r1'],'accountedRegionIds':['r1']},'issues':[]}
    if role=='QUESTION_BOOKLET':
        block={'kind':'question','localKey':'q1','formCode':'PHYSICS_JA','groupCode':'I','answerRef':'PHYSICS:1',
            'printedLabel':'1','bbox':[.1,.1,.9,.5],'stemAst':[{'type':'text','value':'Choose'}],
            'options':[{'key':str(i),'contentAst':[{'type':'text','value':str(i)}]} for i in [1,2]],'answerSpec':{'type':'SINGLE_CHOICE'}}
    else:
        block={'kind':'answer-entry','formCode':'PHYSICS_JA','answerRef':'PHYSICS:1','answerType':'SINGLE_CHOICE','correctOption':'2','bbox':[.1,.1,.9,.5]}
    block['regionId']='r1'
    base['blocks']=[block];return base


def test_signed_pages_assemble_approve_publish_and_revoke(workspace):
    ws,db,sid=workspace
    with pytest.raises(QualityGateError):ws.candidate(sid)
    signed=[]
    for role in ['QUESTION_BOOKLET','ANSWER_KEY']:
        page=ws.save_page(sid,role,1,contract(role),None)
        page=ws.sign_page(sid,role,1,page['revisionId'],'test-reviewer',True)
        signed.append(page)
    candidate=ws.candidate(sid)
    assert audit_paper(candidate['paper'])['status']=='failed'
    approved=ws.approve_paper(sid,review_content_digest(candidate['paper']),'test-reviewer',True)
    result=ws.publish_review(approved['reviewId'],'PRIVATE')
    assert result['version']==1
    assert db.list_papers()[0]['completeness']=='COMPLETE'
    db.connection.execute('BEGIN')
    with pytest.raises(sqlite3.Error):
        db.connection.execute("UPDATE page_revisions SET contract_json='{}' WHERE id=?",(signed[0]['revisionId'],))
    db.connection.rollback()
    changed=copy.deepcopy(signed[0]['contract']);changed['blocks'][0]['stemAst'][0]['value']='Corrected'
    ws.save_page(sid,'QUESTION_BOOKLET',1,changed,signed[0]['revisionId'])
    with pytest.raises(QualityGateError):ws.publish_review(approved['reviewId'],'PRIVATE')
    assert db.list_papers()[0]['deliveryState']=='SUSPENDED'
    with pytest.raises(QualityGateError):ws.candidate(sid)


def test_page_signature_and_revision_cannot_be_faked(workspace):
    ws,db,sid=workspace
    page=ws.save_page(sid,'QUESTION_BOOKLET',1,contract('QUESTION_BOOKLET'),None)
    with pytest.raises(SessionError):ws.save_page(sid,'QUESTION_BOOKLET',1,contract('QUESTION_BOOKLET'),None)
    with pytest.raises(Exception):ws.sign_page(sid,'QUESTION_BOOKLET',1,page['revisionId'],'',True)
    with pytest.raises(Exception):ws.sign_page(sid,'QUESTION_BOOKLET',1,page['revisionId'],'reviewer',False)

def test_withdraw_signature_records_reason_and_preserves_signed_revision(workspace):
    ws,db,sid=workspace
    draft=ws.save_page(sid,'QUESTION_BOOKLET',1,contract('QUESTION_BOOKLET'),None)
    signed=ws.sign_page(sid,'QUESTION_BOOKLET',1,draft['revisionId'],'reviewer',True)
    after=ws.withdraw_page(sid,'QUESTION_BOOKLET',1,signed['revisionId'],'reviewer','Incorrect source region')
    assert not after['signedBy'] and after['revisionId']!=signed['revisionId']
    row=db.connection.execute("SELECT comments FROM review_decisions WHERE page_revision_id=? AND decision='WITHDRAWN'",(signed['revisionId'],)).fetchone()
    assert row[0]=='Incorrect source region'
    assert db.connection.execute('SELECT signed_by FROM page_revisions WHERE id=?',(signed['revisionId'],)).fetchone()[0]=='reviewer'
    with pytest.raises(SessionError):ws.withdraw_page(sid,'QUESTION_BOOKLET',1,signed['revisionId'],'reviewer','Stale withdrawal')


def test_source_structure_baseline_enforcement(workspace):
    ws, db, sid = workspace
    for role in ['QUESTION_BOOKLET', 'ANSWER_KEY']:
        p = ws.save_page(sid, role, 1, contract(role), None)
        ws.sign_page(sid, role, 1, p['revisionId'], 'reviewer', True)

    # Sign baseline requiring both PHYSICS_JA and CHEMISTRY_JA
    ws.sign_source_structure(sid, {'forms': {'PHYSICS_JA':['PHYSICS:1'],'CHEMISTRY_JA':['CHEMISTRY:1']}, 'pages':{'QUESTION_BOOKLET':1,'ANSWER_KEY':1}}, reviewer='lead')

    # Candidate should fail because page only has PHYSICS_JA
    with pytest.raises(QualityGateError, match="baseline"):
        ws.candidate(sid)

    # Sign baseline matching the actual forms ['PHYSICS_JA']
    ws.sign_source_structure(sid, {'forms': {'PHYSICS_JA':['PHYSICS:1']}, 'pages':{'QUESTION_BOOKLET':1,'ANSWER_KEY':1}}, reviewer='lead')
    candidate = ws.candidate(sid)
    assert 'PHYSICS_JA' in [f['formCode'] for f in candidate['paper']['forms']]


def test_math_c1_c2_inventory_isolation(tmp_path):
    from eju_bank.inventory import load_inventory, save_inventory
    inv_path = tmp_path / "content-inventory.json"
    inv_data = {
        "$schema": "https://eju.local/schemas/content-inventory.schema.json",
        "schemaVersion": 1,
        "items": [
            {
                "inventoryId": "2024-1-math-c1",
                "session": "2024-1",
                "subject": "MATHEMATICS",
                "language": "ja",
                "syllabusId": "2015",
                "requiredFiles": ["QUESTION_BOOKLET", "ANSWER_KEY"],
                "rightsStatus": "PRIVATE_STUDY",
                "pipelineStatus": "REVIEWING",
                "expectedForms": ["MATHEMATICS_COURSE_1_JA"]
            },
            {
                "inventoryId": "2024-1-math-c2",
                "session": "2024-1",
                "subject": "MATHEMATICS",
                "language": "ja",
                "syllabusId": "2015",
                "requiredFiles": ["QUESTION_BOOKLET", "ANSWER_KEY"],
                "rightsStatus": "PRIVATE_STUDY",
                "pipelineStatus": "REVIEWING",
                "expectedForms": ["MATHEMATICS_COURSE_2_JA"]
            }
        ]
    }
    save_inventory(inv_data, inv_path)

    # Verify inventory item update for Math C1 only touches C1
    from eju_bank.inventory import upsert_inventory_item
    updated_c1 = {
        "inventoryId": "2024-1-math-c1",
        "session": "2024-1",
        "subject": "MATHEMATICS",
        "language": "ja",
        "syllabusId": "2015",
        "requiredFiles": ["QUESTION_BOOKLET", "ANSWER_KEY"],
        "rightsStatus": "PRIVATE_STUDY",
        "pipelineStatus": "PUBLISHED",
        "expectedForms": ["MATHEMATICS_COURSE_1_JA"],
        "publishedVersionId": "ver_c1"
    }
    upsert_inventory_item(updated_c1, inv_path)

    reloaded = load_inventory(inv_path)
    c1 = next(it for it in reloaded["items"] if it["inventoryId"] == "2024-1-math-c1")
    c2 = next(it for it in reloaded["items"] if it["inventoryId"] == "2024-1-math-c2")
    assert c1["pipelineStatus"] == "PUBLISHED"
    assert c2["pipelineStatus"] == "REVIEWING"



def test_release_rechecks_rights_and_source_hash_after_approval(workspace):
    from eju_bank.util import load_json,write_json,sha256_file
    ws,db,sid=workspace
    for role in ['QUESTION_BOOKLET','ANSWER_KEY']:
        page=ws.save_page(sid,role,1,contract(role),None)
        ws.sign_page(sid,role,1,page['revisionId'],'reviewer',True)
    candidate=ws.candidate(sid)
    approved=ws.approve_paper(sid,review_content_digest(candidate['paper']),'reviewer',True)
    path,manifest=ws.source(sid)
    original=copy.deepcopy(manifest)
    manifest['rights']['status']='SUSPENDED';write_json(path,manifest)
    with pytest.raises(QualityGateError,match='rights changed'):ws.publish_review(approved['reviewId'],'PRIVATE')
    manifest=original
    pdf=ws.root/'sources/question.pdf'
    doc=pymupdf.open();p=doc.new_page();p.insert_text((50,50),'Different edition');doc.save(pdf);doc.close()
    manifest['files'][0]['sha256']=sha256_file(pdf);manifest['files'][0]['sizeBytes']=pdf.stat().st_size;write_json(path,manifest)
    with pytest.raises(QualityGateError,match='files changed'):ws.publish_review(approved['reviewId'],'PRIVATE')
    assert not db.list_papers()

def test_explicit_reviewed_partial_scope_does_not_claim_complete(workspace):
    ws,db,sid=workspace
    for role in ['QUESTION_BOOKLET','ANSWER_KEY']:
        page=ws.save_page(sid,role,1,contract(role),None)
        ws.sign_page(sid,role,1,page['revisionId'],'test-reviewer',True)
    baseline={'forms':{'PHYSICS_JA':['PHYSICS:1','PHYSICS:2']},'pages':{'QUESTION_BOOKLET':1,'ANSWER_KEY':1},'reviewedScope':{'forms':{'PHYSICS_JA':['PHYSICS:1']},'pages':{'QUESTION_BOOKLET':[1],'ANSWER_KEY':[1]},'missingReasons':['Second question is not transcribed']}}
    ws.sign_source_structure(sid,baseline,'test-reviewer')
    with pytest.raises(QualityGateError):ws.candidate(sid)
    candidate=ws.candidate(sid,'REVIEWED_PARTIAL')
    assert candidate['paper']['completeness']=='PARTIAL'
    assert candidate['paper']['availableModes']==['PRACTICE']
    approved=ws.approve_paper(sid,review_content_digest(candidate['paper']),'test-reviewer',True,'REVIEWED_PARTIAL')
    result=ws.publish_review(approved['reviewId'],'PRIVATE')
    assert db.list_papers()[0]['completeness']=='PARTIAL'


@pytest.mark.parametrize('field,value', [('pages',[{}]), ('pages',[True]), ('forms',[{}]), ('forms',['PHYSICS:1','PHYSICS:1'])])
def test_partial_scope_rejects_invalid_values_without_signing(workspace,field,value):
    from eju_bank.errors import ContractError
    ws,db,sid=workspace
    baseline={'forms':{'PHYSICS_JA':['PHYSICS:1']},'pages':{'QUESTION_BOOKLET':1,'ANSWER_KEY':1},'reviewedScope':{'forms':{'PHYSICS_JA':['PHYSICS:1']},'pages':{'QUESTION_BOOKLET':[1],'ANSWER_KEY':[1]},'missingReasons':['Remaining content awaits review']}}
    partial=baseline['reviewedScope']
    partial[field]['QUESTION_BOOKLET' if field=='pages' else 'PHYSICS_JA']=value
    count=db.connection.execute('SELECT COUNT(*) FROM source_structure_revisions').fetchone()[0]
    with pytest.raises(ContractError):ws.sign_source_structure(sid,baseline,'reviewer')
    assert db.connection.execute('SELECT COUNT(*) FROM source_structure_revisions').fetchone()[0]==count
