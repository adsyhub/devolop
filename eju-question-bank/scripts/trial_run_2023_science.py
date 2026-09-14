"""Inspect published content and trial an available paper on a temporary DB copy."""
import argparse
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path
from eju_bank.db import Database


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,default=Path(__file__).resolve().parents[1]/'library/eju.db')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='eju-trial-') as temp:
        target=Path(temp)/'eju.db'
        source=sqlite3.connect(f'file:{args.database.resolve()}?mode=ro',uri=True);snapshot=sqlite3.connect(target)
        try:source.backup(snapshot)
        finally:source.close();snapshot.close()
        db=Database(target)
        try:
            papers=db.list_papers();print(json.dumps({'papers':papers},ensure_ascii=False,indent=2))
            available=[p for p in papers if p['deliveryState'] not in {'REVIEW_REQUIRED','SUSPENDED'}]
            if available:
                p=available[0];session=db.create_session(p['paperId'],[p['forms'][0]],mode='PRACTICE')
                print(json.dumps(db.submit_session(session['sessionId']),ensure_ascii=False,indent=2))
            else:print('No reviewed, available paper to trial. Original database was not modified.')
        finally:db.close()


if __name__=='__main__':main()
