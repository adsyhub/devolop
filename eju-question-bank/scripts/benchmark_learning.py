"""Synthetic benchmark: 10,000 questions, 100 published versions and 1,000 sessions."""
from pathlib import Path
import copy
import json
import platform
import statistics
import sys
import tempfile
import time
import resource
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from eju_bank.db import Database
from eju_bank.audit import prepare_paper,iter_questions
from eju_bank.util import write_json


def timed(fn,count=30):
    values=[];size=0
    for _ in range(count):
        start=time.perf_counter();result=fn();values.append((time.perf_counter()-start)*1000);size=len(json.dumps(result).encode())
    values.sort();return {'p50Ms':round(statistics.median(values),3),'p95Ms':round(values[int(.95*(len(values)-1))],3),'payloadBytes':size,'samples':count}


def main():
    fixture=json.loads((ROOT/'tests/fixtures/synthetic_paper.json').read_text())
    template=next(q for f,_,q in iter_questions(fixture) if f['formCode']=='PHYSICS_JA')
    template=copy.deepcopy(template);template['stemAst']=[{'type':'text','value':'合成性能测试：小球的速度是多少？'}];template['materialRefs']=[]
    with tempfile.TemporaryDirectory(prefix='eju-benchmark-') as directory:
        db=Database(Path(directory)/'eju.db',allow_synthetic=True)
        papers=[]
        for p in range(100):
            paper=copy.deepcopy(fixture);paper.update(paperId=f'bench-{p}',stableCode=f'bench-{p}',completeness='PARTIAL',availableModes=['PRACTICE']);paper.pop('expectedStructure',None)
            questions=[]
            for i in range(100):
                q=copy.deepcopy(template);q.update(questionId=f'bq-{p:03d}-{i:03d}',localKey=f'q-{i}',answerRef=f'PHYSICS:{i}',sequence=i+1,printedLabel=str(i+1));questions.append(q)
            form=copy.deepcopy(next(f for f in paper['forms'] if f['formCode']=='PHYSICS_JA'));form['groups']=[{'groupCode':'I','questions':questions,'materials':[]}];paper['forms']=[form];paper=prepare_paper(paper);db.publish(paper,channel='PUBLIC');papers.append(paper)
        for i in range(1000):db.create_session(papers[i%100]['paperId'],['PHYSICS_JA'],question_ids=[f'bq-{i%100:03d}-000'])
        preview=db.preview_practice({'questionIds':[f'bq-{p:03d}-{i:03d}' for p in [0,1] for i in range(100)]})
        session=db.start_preview(preview['previewId'],'benchmark-start-1');sid=session['sessionId']
        version=0
        def save():
            nonlocal version
            result=db.record_responses_batch(sid,[{'questionId':'bq-000-000','response':{'type':'SINGLE_CHOICE','optionKey':'1'}}],expected_version=version);version=result['responseVersion'];return result
        report={'benchmarkVersion':1,'environment':{'platform':platform.platform(),'python':platform.python_version(),'storage':'temporary local filesystem','cache':'warm','transport':'in-process database calls'},'dataset':{'questions':10000,'paperVersions':100,'sessions':1001,'activePracticeQuestions':200},'search':timed(lambda:db.search_questions(query='小球',limit=50)),'history':timed(lambda:db.history_page(limit=50)),'batchSave':timed(save),'sessionPaper':timed(lambda:db.get_session_paper(sid),count=10),'peakRssKiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        report['limits']='These are database timings. They do not establish browser interaction or HTTP p95 budgets.'
        db.close()
    path=ROOT/'docs/evidence/learning-benchmark-2026-09-08.json';write_json(path,report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
