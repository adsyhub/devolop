"""One reproducible release gate; all runtime data is isolated in temporary directories."""
from pathlib import Path
import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]

def run(argv,**kwargs):
    result=subprocess.run(argv,cwd=kwargs.pop('cwd',ROOT),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kwargs)
    if result.returncode:print(result.stdout);raise SystemExit(result.returncode)
    print(result.stdout.strip())
    return result.stdout

def input_hashes():
    from hashlib import sha256
    paths=[p for directory in ['eju_bank','scripts','tests','schemas'] for p in (ROOT/directory).rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.tmp'}]
    paths.append(ROOT/'pyproject.toml')
    return {str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/release-2026-09-08.json');parser.add_argument('--skip-browser',action='store_true');args=parser.parse_args()
    before=input_hashes()
    run([sys.executable,'scripts/sync_schemas.py','--check'])
    for path in [*ROOT.glob('eju_bank/**/*.py'),*ROOT.glob('scripts/*.py')]:ast.parse(path.read_text(),filename=str(path))
    for path in (ROOT/'eju_bank/web').glob('*.js'):run(['node','--check',str(path)])
    if not args.skip_browser:
        run([sys.executable,'-c','from playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n b=p.chromium.launch(headless=True);b.close()'])
    command=[sys.executable,'-m','pytest','--junitxml='+str(args.output.with_suffix('.junit.xml'))]
    if args.skip_browser:command+=['--ignore=tests/test_browser_learning.py','--ignore=tests/test_review_browser.py','--ignore=tests/test_browser_workflows.py','--ignore=tests/test_management_browser.py']
    tests=run(command)
    with tempfile.TemporaryDirectory(prefix='eju-release-') as tmp:
        temp=Path(tmp);wheels=temp/'wheels'
        run([sys.executable,'-m','pip','wheel',str(ROOT),'--no-deps','--no-build-isolation','-w',str(wheels)])
        run([sys.executable,'-m','venv','--system-site-packages',str(temp/'venv')])
        python=temp/'venv/bin/python'
        run([str(python),'-m','pip','install','--no-deps','--force-reinstall',str(next(wheels.glob('*.whl')))],cwd=temp)
        check="""from pathlib import Path
import eju_bank
from eju_bank.schema_validation import validator
from importlib.resources import files
for name in ['source-manifest','page-contract','paper','content-inventory','source-structure']: validator(name)
assert Path(eju_bank.__file__).is_relative_to(Path(__import__('sys').prefix))
for name in ['home.html','practice.html','me.html','index.html','tokens.css','core.js','home.js','practice.js','me.js','studio.html','studio_library.html','studio_editor.html','studio_ops.html','studio.css','studio_shell.js','studio_build.js','studio_library.js','studio_editor.js','studio_ops.js','vendor/katex/katex.min.js']:assert files('eju_bank').joinpath('web',name).is_file()
from eju_bank.server import create_server
from eju_bank.errors import SecurityError
import os;os.environ.pop('EJU_ADMIN_TOKEN',None)
server=create_server('data/library/eju.db',workspace_root='data',port=0,start_worker=False)
assert server.admin_token is None, 'loopback must not mint an access token'
server.server_close();server.database.close()
try:create_server('data/library/eju.db',workspace_root='data',port=0,allow_remote=True,start_worker=False)
except SecurityError:pass
else:raise AssertionError('remote access must still require a token')
print('Installed wheel: packaged schemas, offline web resources, separate workspace startup, tokenless loopback with guarded remote passed')
"""
        installed=run([str(python),'-I','-c',check],cwd=temp)
    after=input_hashes()
    if before!=after:
        changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
        raise SystemExit('Source files changed during verification; rerun on stable inputs: '+', '.join(changed))
    report={'sourceRoot':str(ROOT),'tests':tests.strip().splitlines()[-1],'browserRequired':not args.skip_browser,'wheel':installed.strip(),'files':after}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(args.output)
if __name__=='__main__':main()
