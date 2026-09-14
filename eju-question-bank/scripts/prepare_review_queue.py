"""Inventory physical source pages without claiming their contents are reviewed."""
import argparse
import json
from pathlib import Path
import pymupdf as fitz
from eju_bank.source import validate_source_manifest
from eju_bank.util import load_json,resolve_manifest_file,write_json,utc_now


def prepare(root):
    root=Path(root).resolve()
    inventory={i['inventoryId']:i for i in load_json(root/'content/content-inventory.json')['items']}
    sources=[]
    for path in sorted((root/'work').glob('*/source-manifest.json')):
        manifest=load_json(path);validate_source_manifest(manifest,path,verify_files=True)
        item=inventory[manifest['inventoryId']]
        pages=[]
        for file in manifest['files']:
            if file['role'] not in {'QUESTION_BOOKLET','ANSWER_KEY'}:continue
            with fitz.open(resolve_manifest_file(path,file['path'])) as pdf:
                for number,page in enumerate(pdf,1):
                    pages.append({'role':file['role'],'physicalPage':number,'sourceHash':file['sha256'],
                                  'widthPoints':page.rect.width,'heightPoints':page.rect.height,
                                  'status':'PENDING_CONTENT_REVIEW','regionDisposition':None,
                                  'checks':['题号与顺序','全部区域处置','文字/选项/公式/图形','材料关联','独立答案引用'],
                                  'knownIssue':'SOURCE_PAGE_MISMATCH: original bio-q-01/bio-q-02' if item['inventoryId']=='eju-2023-2-science-ja' and file['role']=='QUESTION_BOOKLET' and number==41 else None})
        roles={f['role'] for f in manifest['files']}
        report={'generatedAt':utc_now(),'sourceId':manifest['sourceId'],'inventoryId':manifest['inventoryId'],
                'expectedForms':item['expectedForms'],'missingRoles':[r for r in item['requiredFiles'] if r not in roles],
                'blockingIssues':item.get('blockingIssues',[]),'pageCount':len(pages),'pages':pages,
                'notice':'This is a work queue, not a structure baseline or a review signature. All content needs independent verification.'}
        write_json(path.parent/'review-queue.json',report)
        sources.append({k:report[k] for k in ['sourceId','inventoryId','missingRoles','blockingIssues','pageCount']})
    return {'generatedAt':utc_now(),'sources':sources,'physicalPages':sum(s['pageCount'] for s in sources),'signedByThisScript':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workspace',type=Path,default=Path.cwd());args=parser.parse_args()
    report=prepare(args.workspace)
    write_json(args.workspace/'docs/evidence/real-source-review-queue-2026-09-08.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
