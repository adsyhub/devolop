"""Run the production job worker in a separate process from the HTTP server."""
import argparse
import signal
from pathlib import Path
from .db import Database
from .errors import ContractError
from .job_worker import JobWorker
from .review import ContentWorkspace


def inside(root,ref):
    if not isinstance(ref,str) or Path(ref).is_absolute():raise ContractError('Expected workspace relative path')
    path=(root/ref).resolve()
    if not path.is_relative_to(root):raise ContractError('Path is outside the workspace')
    return path


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--database',required=True);parser.add_argument('--workspace',required=True);parser.add_argument('--media-dir');args=parser.parse_args()
    db=Database(args.database,workspace_root=args.workspace,media_dir=args.media_dir)
    worker=JobWorker(db,ContentWorkspace(args.workspace,db))
    for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,lambda *_:worker.stopping.set())
    try:worker._loop()
    finally:db.close()

if __name__=='__main__':main()
