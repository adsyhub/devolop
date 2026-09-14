"""Assemble approved source pages; never generate question text or delete drafts."""
import argparse
import json
from pathlib import Path
from eju_bank.db import Database
from eju_bank.review import ContentWorkspace
from eju_bank.errors import EjuBankError
from eju_bank.util import write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-id')
    parser.add_argument('--out',type=Path)
    parser.add_argument('--review-id',help='Publish an existing signed review instead of assembling a candidate')
    args=parser.parse_args()
    db=Database(args.workspace/'library/eju.db')
    try:
        workspace=ContentWorkspace(args.workspace,db)
        if args.review_id:
            result=workspace.publish_review(args.review_id,'PRIVATE')
        else:
            source_id=args.source_id or json.loads((args.workspace/'work/2023-2-science/source-manifest.json').read_text())['sourceId']
            result=workspace.candidate(source_id)
        if args.out:
            if args.out.exists(): raise EjuBankError('Output already exists; choose a new revision file')
            write_json(args.out,result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except EjuBankError as exc:
        parser.exit(2,str(exc)+'\n')
    finally:db.close()


if __name__=='__main__':main()
