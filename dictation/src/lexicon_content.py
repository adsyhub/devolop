"""Reproducible learning supplements and original vocabulary pack construction."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
from dictionary_store import DictionaryStore
from lexicon_schema import prepare_pack,audit_pack,default_card_templates,publish_pack
from lexicon_exercise import reading_of,questions_for,validate_spec
from jp_inflection import normalize

ROOT=Path(__file__).resolve().parent.parent


# A generator can attest to structure and provenance, never to meaning. Anything it
# writes therefore stops at `machine_checked`; `reviewed` is granted only by a review
# record naming a reviewer and the content hash it covers (LEX-04, §6.1).
def choice_spec(kind,prompt,correct,others,explanation,variant,evidence):
    choices=[{'id':'answer','label':correct,'rationale':explanation}]
    for i,(label,reason) in enumerate(others):choices.append({'id':f'other-{i}','label':label,'rationale':reason})
    return {'type':kind,'mode':'choice','prompt':prompt,'choices':choices,'acceptedAnswers':['answer'],
            'referenceAnswer':correct,'explanation':explanation,'variantKey':variant,'reviewStatus':'machine_checked','evidence':evidence}


def supplement_pack(pack,document):
    pack=copy.deepcopy(pack);pack['schemaVersion']=2
    meanings=document.get('entries')
    if meanings is None:
        # Convert the initial authored list into stable keys, never use current order.
        meanings={f'e{i+1:04d}':meaning for i,meaning in enumerate(document.get('meanings',[]))}
    evidence={'method':'source-example-and-connection-check','provenance':document.get('provenance',{}),'notHumanReview':True}
    for entry in pack['entries']:
        key=entry['entryKey'];meaning=meanings.get(key)
        if not meaning:continue
        entry.setdefault('gloss',{})['zh']=meaning
        entry.setdefault('fieldSources',{})['gloss.zh']=document['provenance']
        extra=document.get('examples',{}).get(key)
        if extra:
            ja,zh,target=extra
            example={'exampleId':'supplement-1','ja':ja,'zh':zh,'markedJa':ja.replace(target,f'⟦{target}⟧',1),'source':document['provenance']}
            entry['examples']=[e for e in entry.get('examples',[]) if e.get('exampleId')!='supplement-1']+[example]
        prior_templates=entry.get('cardTemplates',[])
        templates={(t['promptType'],t['variantKey']):t for t in prior_templates}
        for template in default_card_templates(entry):
            templates.setdefault((template['promptType'],template['variantKey']),template)
        entry['cardTemplates']=list(templates.values())
        entry['qualityStatus']='available';entry['exerciseTemplates']=[]
        others=[e for e in pack['entries'] if e['entryKey']!=key and meanings.get(e['entryKey'])][:2]
        if len(others)==2:
            spec=choice_spec('usage','选择符合以下学习概括的表达：\n'+meaning.split('：',1)[-1],entry['headword'],[(e['headword'],meanings[e['entryKey']]) for e in others],meaning,'usage-meaning',evidence)
            entry['exerciseTemplates'].append(spec)
        connections=entry.get('grammar',{}).get('connection',[])
        displays={c['display'] for c in connections}
        alternatives=[]
        for other in pack['entries']:
            for c in other.get('grammar',{}).get('connection',[]):
                if c['display'] not in displays and c['display'] not in {a[0] for a in alternatives}:alternatives.append((c['display'],'此项不在本条列出的接续形式中。'))
                if len(alternatives)>=2:break
            if len(alternatives)>=2:break
        if connections and len(alternatives)>=2:
            entry['exerciseTemplates'].append(choice_spec('connection',f'根据本条接续表，「{entry["headword"]}」可以采用哪一项形式？',connections[0]['display'],alternatives[:2],'本条接续：'+'、'.join(displays)+'。'+meaning,'connection-table',evidence))
        translated=next((e for e in entry.get('examples',[]) if e.get('ja') and e.get('zh')),None)
        if translated:
            ja=translated['ja'];zh=translated['zh']
            entry['exerciseTemplates'].append({'type':'writing','mode':'self','prompt':'用本条文型造句，或将下面的中文改写成日语：\n'+zh,'referenceAnswer':ja,'explanation':meaning+'\n参考例句：'+ja,'variantKey':'writing-example','reviewStatus':'machine_checked','evidence':evidence})
            # Context translation deliberately constrains the intended meaning.
            if len(others)==2:
                entry['exerciseTemplates'].append(choice_spec('context','哪一项表达与以下中文语境及指定用意相符？\n'+zh+'\n用意：'+meaning.split('：',1)[-1],entry['headword'],[(e['headword'],meanings[e['entryKey']]) for e in others],meaning+'\n'+ja,'context-example',evidence))
            if '、' in ja:
                left,right=ja.split('、',1)
                if left and right:
                    entry['exerciseTemplates'].append({'type':'order','mode':'order','prompt':'按所学例句的书面顺序排列（注意逗号）：\n'+zh,'tokens':[{'id':'first','label':left+'、'},{'id':'last','label':right}],'acceptedAnswers':[['first','last']],'referenceAnswer':ja,'explanation':ja+'\n'+meaning,'variantKey':'order-example','reviewStatus':'machine_checked','evidence':evidence})
    # Useful pairs retain source identities, not normalized word strings.
    groups=[list(range(1,5)),list(range(13,17)),[17,18,19,20],[53,54,55,56],[57,58,59,60],[68,69,70,71],[96,97,98,99],[133,134,135],[144,145,146,147],list(range(168,192))]
    by_key={e['entryKey']:e for e in pack['entries']}
    confusable_details=document.get('confusableDetails',{})
    for group in groups:
        for number in group:
            entry=by_key.get(f'e{number:04d}')
            if entry:
                c_list=[]
                for n in group:
                    if n==number:continue
                    other_key=f'e{n:04d}'
                    if other_key not in by_key:continue
                    other_id=by_key[other_key]['id']
                    ref=f"lex:{pack['packId']}#{other_id}"
                    detail=confusable_details.get(f'e{number:04d}',{}).get(other_key)
                    if detail:
                        c_list.append({
                            'sourceRef':ref,
                            'relationType':detail.get('relationType','nuance_contrast'),
                            'contrast':detail.get('contrast',''),
                            'scenario':detail.get('scenario','')
                        })
                    else:
                        c_list.append(ref)
                entry['grammar']['confusables']=c_list
    reviews=document.get('reviews',{})
    if reviews:
        from lexicon_exercise import review_content_hash
        for entry in pack['entries']:
            for template in entry.get('exerciseTemplates',[]):
                rev_key=f"{entry['entryKey']}:{template.get('variantKey')}"
                alt_key=f"{entry['id']}:{template.get('variantKey')}"
                review_info=reviews.get(rev_key) or reviews.get(alt_key)
                if review_info and isinstance(review_info,dict) and review_info.get('reviewer'):
                    template['reviewStatus']='reviewed'
                    template['review']={
                        'method':review_info.get('method','manual'),
                        'reviewer':str(review_info['reviewer']),
                        'reviewedAt':str(review_info.get('reviewedAt','2026-09-08T00:00:00+00:00')),
                        'contentHash':review_info.get('contentHash') or review_content_hash(template)
                    }
    return prepare_pack(pack)


def seed_key(word: str, reading: str) -> str:
    """A seed's identity is the word it names, not where it sits in the list."""
    return normalize(word,reading=False)+'|'+normalize(reading,reading=True)


def load_seed_registry(path: Path, pack_id: str) -> dict:
    if not Path(path).is_file():
        return {'schemaVersion':1,'packId':pack_id,'nextKey':1,'entries':[]}
    registry=json.loads(Path(path).read_text(encoding='utf-8'))
    if str(registry.get('packId') or '')!=pack_id:
        raise ValueError(f"{path} 属于内容包 {registry.get('packId')!r}，不是 {pack_id!r}。")
    return registry


def resolve_seed_keys(registry: dict, seeds: list[str]) -> dict:
    """Assign each seed a key once and never move it.

    Keys used to be handed out by traversal position, so inserting one word near the
    front renumbered every word after it and handed the learner a fresh card for each
    (§6.4.4). New seeds append; existing ones keep the key they were given.
    """
    known={str(item['seedKey']):str(item['entryKey']) for item in registry.get('entries') or []}
    next_key=int(registry.get('nextKey') or 1)
    for seed in seeds:
        if seed in known: continue
        known[seed]=f'e{next_key:04d}'; next_key+=1
        registry.setdefault('entries',[]).append({'seedKey':seed,'entryKey':known[seed]})
    registry['nextKey']=next_key
    registry['entries']=sorted(registry.get('entries') or [],key=lambda item:str(item['entryKey']))
    return known


def build_words(source=ROOT/'assets/lexicon_seed/words.json',out=ROOT/'lexicon/Everyday-words',dictionary=ROOT/'assets/dictionary/jmdict.sqlite3',registry_path=None,adjudications=None):
    source=Path(source);document=json.loads(source.read_text(encoding='utf-8'));store=DictionaryStore(Path(dictionary))
    if not store.status()['available']:raise ValueError('请先安装 JMdict 词典。')
    registry_path=Path(registry_path or source.parent/'word-keys.json')
    registry=load_seed_registry(registry_path,'Everyday-words')
    seeds=[seed_key(*raw.split('|')[:2]) for group in document['groups'] for raw in group['items'].split(';')]
    keys_by_seed=resolve_seed_keys(registry,seeds)
    adjudications=adjudications or source.parent/'word-adjudications.json'
    verdicts=json.loads(Path(adjudications).read_text(encoding='utf-8')) if adjudications and Path(adjudications).is_file() else {}
    entries=[];units=[];rejected=[];outcomes={'matched':0,'ambiguous':0,'unmatched':0,'manually-resolved':0,'model-resolved':0}
    for group_index,group in enumerate(document['groups']):
        unit_id=f'u{group_index+1}';keys=[]
        for raw in group['items'].split(';'):
            word,reading,meaning=raw.split('|');seed=seed_key(word,reading);key=keys_by_seed[seed]
            matches=[m for m in store.search(word,60) if any(normalize(r['text'],reading=True)==normalize(reading,reading=True) for r in m.get('readings',[])) and (word in m.get('writtenForms',[]) or any(normalize(word,reading=True)==normalize(r['text'],reading=True) for r in m.get('readings',[])))]
            verdict=verdicts.get(seed);resolved=False
            if len(matches)!=1 and verdict:
                # A recorded decision resolves what the matcher could not, and the
                # decision is persistent rather than re-made on every build (§6.4.3).
                chosen=[m for m in matches if str(m['id'])==str(verdict.get('entSeq'))] or \
                       [m for m in store.search(word,60) if str(m['id'])==str(verdict.get('entSeq'))]
                if chosen:
                    matches=chosen[:1];resolved=True
                    outcomes['model-resolved' if verdict.get('notHumanReview') else 'manually-resolved']+=1
            if len(matches)!=1:
                reason='ambiguous' if matches else 'unmatched'; outcomes[reason]+=1
                rejected.append({'seedKey':seed,'entryKey':key,'word':word,'reading':reading,'reason':reason,'candidates':[m['id'] for m in matches]});continue
            if not resolved: outcomes['matched']+=1
            match=matches[0];ja=group['ja'].format(word=word);zh=group['zh'].format(meaning=meaning)
            # Only the senses this spelling and reading actually allow, recorded by key so
            # a rebuilt dictionary can be checked against the choice (§6.4.2).
            compatible=store.senses_for(match,word,reading) or match.get('senses',[])
            if resolved and verdict.get('senseKeys'):
                selected=set(verdict['senseKeys'])
                compatible=[sense for sense in compatible if sense.get('key') in selected]
                if {sense['key'] for sense in compatible}!=selected:
                    raise ValueError(f'词典义项裁决已经过期：{seed}')
            sense_keys=[s['key'] for s in compatible if s.get('key')]
            entry={'entryKey':key,'kind':'word','level':'ungraded','headword':word,'unitId':unit_id,'gloss':{'zh':meaning},
              'dictRef':{'source':'jmdict','entSeq':int(match['id']),'writtenForm':word,'reading':reading,
                         'senseIndexes':[i for i,s in enumerate(match.get('senses',[])) if s in compatible],
                         'senseKeys':sense_keys,
                         'dictionaryVersion':str(store.status().get('sourceSha256') or '')},
              'snapshot':{'reading':reading,'pos':match['pos'],'glossEn':[g for s in compatible for g in s['gloss']]},
              'word':{'writtenForms':[word],'commonness':'ichi1' if match.get('common') else ''},
              'fieldSources':{'reading':{'source':'JMdict','entryId':match['id']},'gloss.zh':{'source':'original-editorial','author':'assistant'}},
              'examples':[{'exampleId':'original-1','ja':ja,'zh':zh,'source':{'sourceType':'original'}}],
              'source':{'sourceType':'original'},'flags':[],'qualityStatus':'available','cardTemplates':[{'variantKey':'default','promptType':'recall'}]}
            entries.append(entry);keys.append(key)
        units.append({'unitId':unit_id,'label':group['name'],'title':'日常主题词汇','entryIds':keys})
    evidence={'method':'dictionary-reading-match-and-authored-template','sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'notHumanReview':True}
    for i,e in enumerate(entries):
        word=e['headword'];reading=reading_of(e);meaning=e['gloss']['zh'];ex=e['examples'][0]
        others=[]
        for n in range(1,len(entries)):
            other=entries[(i+n*7)%len(entries)]
            if other['gloss']['zh']!=meaning and other['headword']!=word and other not in others:others.append(other)
            if len(others)>=2:break
        wrong=[(o['gloss']['zh'],f"这个意思对应「{o['headword']}」，本题「{word}」表示{meaning}。") for o in others]
        specs=[choice_spec('meaning',f'选择「{word}」在本条中的中文意思。',meaning,wrong,f'「{word}」（{reading}）：{meaning}。','meaning-select',evidence)]
        # Hearing tests ask for meaning, so reasonable alternate spellings are not marked wrong.
        listening=choice_spec('listening','听音并选择本条词语的含义。',meaning,wrong,f'听到的是「{word}」（{reading}）：{meaning}。','listening-select',evidence);listening['speech']=reading;specs.append(listening)
        specs.append({'type':'cloze','mode':'input','prompt':'根据中文，补出原例句中的词语：\n'+ex['zh']+'\n'+ex['ja'].replace(word,'＿＿',1),'acceptedAnswers':list(dict.fromkeys([word,reading])),'normalizeReading':True,'referenceAnswer':word,'explanation':ex['ja']+'\n'+ex['zh'],'variantKey':'cloze-original','reviewStatus':'machine_checked','evidence':evidence})
        specs.append(choice_spec('collocation','根据中文语境，选择组成原例句的词语：\n'+ex['zh']+'\n'+ex['ja'].replace(word,'＿＿',1),word,[(o['headword'],f"「{o['headword']}」表示{o['gloss']['zh']}，不符合本题中文语境。") for o in others],ex['ja']+'\n'+ex['zh'],'collocation-original',evidence))
        e['exerciseTemplates']=specs
    pack=prepare_pack({'schemaVersion':2,'packId':'Everyday-words','kind':'word','level':'ungraded','title':'日常主题词汇 · 中文释义与例句','attribution':{'sourceType':'original','redistributable':False,'publisher':'Dictation 原创学习资料','author':'Original learning examples; readings and POS from JMdict / EDRDG (CC BY-SA 4.0)','license':'CC BY-SA 4.0','licenseUrl':'https://www.edrdg.org/edrdg/licence.html'},'units':units,'entries':entries})
    report=audit_pack(pack)
    if report['summary']['errors']:raise ValueError(json.dumps(report,ensure_ascii=False))
    # The registry is source data: it is written before the pack so a later failure
    # cannot hand the same key to a different word on the next run.
    registry_path.parent.mkdir(parents=True,exist_ok=True)
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    match_report={'contentRevision':pack['contentRevision'],'dictionaryVersion':str(store.status().get('sourceSha256') or ''),
                  'candidates':len(seeds),'included':len(entries),'excluded':len(rejected),
                  'outcomes':outcomes,'rejected':rejected}
    publish_pack(Path(out),{
        # Every report states which revision it describes, so a stale one is detectable.
        'pack.json':pack,'quality-report.json':{'contentRevision':pack['contentRevision'],**report},
        'match-report.json':match_report,
        'entry-keys.json':{'schemaVersion':1,'packId':pack['packId'],
                           'entries':[{'entryKey':e['entryKey'],'sourceAnchor':'original:'+e['entryKey'],'retired':False} for e in entries]},
    },revision=pack['contentRevision'])
    return {'entries':len(entries),'rejected':rejected,'quality':report['summary'],'outcomes':outcomes}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['words']);args=parser.parse_args()
    print(json.dumps(build_words(),ensure_ascii=False,indent=2))
