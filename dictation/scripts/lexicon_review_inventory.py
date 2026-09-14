"""Reproducible qualification inventory, without copying private textbook prose."""
import json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lexicon_store import LexiconStore
from lexicon_exercise import capabilities,questions_for

def inventory():
    store=LexiconStore(ROOT/'lexicon');result=[]
    for summary in store.list_packs():
        pack=store.get_pack(summary['slug']);entries=[];qualified=Counter();pending=Counter()
        for entry in pack['entries']:
            questions=questions_for(pack,entry,include_pending=True)
            for q in questions:(qualified if q.get('qualified') else pending).update([q['type']])
            entries.append({'entryId':entry['id'],'entryKey':entry.get('entryKey'),
                            'capabilities':capabilities(pack,entry),
                            'pendingQuestions':[{'id':q['id'],'type':q['type'],'answerVersion':q['answerVersion'],'reasons':q.get('reasonCodes',[])} for q in questions if not q.get('qualified')]})
        result.append({'packId':pack['packId'],'contentRevision':pack['contentRevision'],
                       'reportsCurrent':pack.get('publication',{}).get('reportsCurrent'),
                       'qualified':dict(qualified),'pending':dict(pending),'entries':entries})
    return {'contract':'Formal qualification is distinct from human linguistic review.', 'packs':result}

if __name__=='__main__':
    result=inventory();out=ROOT/'docs/词汇语法内容资格清单.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(out)
    for pack in result['packs']:print(pack['packId'],len(pack['entries']),pack['qualified'],pack['pending'])
