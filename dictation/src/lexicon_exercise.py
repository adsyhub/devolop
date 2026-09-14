"""Deterministic lexicon question construction and scoring, independent of HTTP."""
from __future__ import annotations
import copy
import hashlib
import json
import re
from jp_inflection import normalize

TYPES = {
 'recall':'回忆释义','meaning':'看词识义','reading':'看词写读音','production':'看释义回忆词语',
 'listening':'听音识词','cloze':'例句填空','connection':'接续练习','usage':'近义辨析',
 'collocation':'搭配辨析','order':'句子排序','context':'语境选择','writing':'造句 / 改写',
}
GRADES = {'again','hard','good','easy'}

# LEX-04: generation is not review. `verified` predates this contract and was written
# by generators, so it can only ever mean "structure checked", never "a person read it".
REVIEW_STATES = ('draft','machine_checked','reviewed','withdrawn')
SCORING_VERSION = 2


def review_state(spec: dict) -> str:
    raw=str(spec.get('reviewStatus') or 'draft')
    if raw=='verified':raw='machine_checked'
    return raw if raw in REVIEW_STATES else 'draft'


def _digest(material) -> str:
    return hashlib.sha256(json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def review_content_hash(spec: dict) -> str:
    """Hash of exactly what a reviewer signs off on; unrelated UI metadata is excluded."""
    return _digest({'type':spec.get('type'),'mode':spec.get('mode','input'),'prompt':spec.get('prompt'),
      'acceptedAnswers':spec.get('acceptedAnswers'),'referenceAnswer':spec.get('referenceAnswer'),
      'explanation':spec.get('explanation'),'blankCount':spec.get('blankCount'),'normalizeReading':spec.get('normalizeReading'),
      'choices':[{'id':c.get('id'),'label':c.get('label'),'rationale':c.get('rationale')} for c in spec.get('choices') or []],
      'tokens':[{'id':t.get('id'),'label':t.get('label')} for t in spec.get('tokens') or []]})


def answer_version(spec: dict) -> str:
    """Version of the scoring content alone; a reworded prompt keeps earlier answers valid."""
    return 'sha256-'+_digest({'mode':spec.get('mode','input'),'acceptedAnswers':spec.get('acceptedAnswers'),
      'blankCount':spec.get('blankCount'),'normalizeReading':spec.get('normalizeReading'),
      'choiceIds':[c.get('id') for c in spec.get('choices') or []],
      'tokenIds':[t.get('id') for t in spec.get('tokens') or []]})[:39]


AUTO_QUALIFIED_TYPES = {'reading', 'recall', 'meaning', 'cloze', 'connection'}


def qualification(spec: dict) -> tuple[bool, list[str]]:
    """Whether one authored template may be served as a formal, countable question.

    Supports either:
    1. Valid human review record (review.reviewer, review.contentHash matching review_content_hash(spec))
    2. Valid machine verification (verification.status == 'auto_verified', matching contentHash, policyId, supported type)
    Hard vetoes (withdrawn, disputed, retired, draft entry status) are never bypassed.
    """
    state = review_state(spec)
    codes = []

    if state == 'withdrawn':
        codes.append('review.withdrawn')
        return (False, codes)
    entry_status = str(spec.get('entryStatus') or spec.get('_entryStatus') or '')
    if entry_status in {'draft', 'disputed', 'retired'}:
        codes.append(f'entry.{entry_status}')
        return (False, codes)

    has_valid_human_review = False
    if state == 'reviewed':
        review = spec.get('review') if isinstance(spec.get('review'), dict) else {}
        if not str(review.get('reviewer') or '').strip():
            codes.append('review.reviewer_missing')
        elif not review.get('contentHash'):
            codes.append('review.hash_missing')
        elif review['contentHash'] != review_content_hash(spec):
            codes.append('review.stale')
        else:
            has_valid_human_review = True

    has_valid_verification = False
    verification = spec.get('verification') if isinstance(spec.get('verification'), dict) else None
    if verification:
        v_status = str(verification.get('status') or '')
        v_policy = str(verification.get('policyId') or '')
        v_hash = str(verification.get('contentHash') or '')
        v_checks = verification.get('checkRefs')
        q_type = str(spec.get('type') or '')

        if v_status == 'auto_verified':
            if not v_policy:
                codes.append('verification.policy_missing')
            elif not v_hash:
                codes.append('verification.hash_missing')
            elif v_hash != review_content_hash(spec):
                codes.append('verification.stale')
            elif not isinstance(v_checks, list) or not v_checks:
                codes.append('verification.checks_missing')
            elif q_type not in AUTO_QUALIFIED_TYPES:
                codes.append('verification.unsupported_type')
            else:
                has_valid_verification = True

    if not has_valid_human_review and not has_valid_verification:
        if state != 'reviewed' and not verification:
            codes.append('review.required')

    if not spec.get('evidence') and not spec.get('review') and not spec.get('verification'):
        codes.append('evidence.missing')

    is_qualified = (has_valid_human_review or has_valid_verification) and not codes
    return (is_qualified, codes)


def review_target(source: str,prompt_type: str,variant_key: str) -> dict:
    """The long-term SRS identity behind a question or a plan card template.

    Question ids stay per-variant so recall and production never collide, but the
    automatic `<type>-default` variants fold onto the plan card's `default`, so one
    ability has one card however the learner reached it (LEX-01).
    """
    variant=str(variant_key or 'default')
    if variant==f'{prompt_type}-default':variant='default'
    return {'sourceRef':source,'promptType':str(prompt_type),'variantKey':variant}


def plain(text: str) -> str:
    text=re.sub(r'｜([^《]+)《[^》]+》',r'\1',str(text or ''))
    return re.sub(r'</?u>|[⟦⟧]', '', text)


def reading_of(entry: dict) -> str:
    return str(entry.get('reading') or entry.get('snapshot',{}).get('reading') or entry.get('dictRef',{}).get('reading') or '')


def source_ref(pack: dict,entry: dict) -> str:
    return entry.get('_sourceRef') or f"lex:{entry.get('_sourcePackId') or pack['packId']}#{entry['id']}"


def _question(pack: dict, entry: dict, spec: dict, variant: str) -> dict:
    ref=source_ref(pack,entry)
    key=hashlib.sha256((ref+'\x1f'+variant).encode()).hexdigest()[:24]
    return {'id':'q_'+key,'sourceRef':ref,'entryId':entry['id'],'kind':entry['kind'],
            'reviewTarget':review_target(ref,spec.get('type','recall'),variant),
            'answerVersion':answer_version(spec),'scoringVersion':SCORING_VERSION,
            'presentationMode':spec.get('mode','input'),'reviewStatus':review_state(spec),
            'level':entry.get('level',''),'unitId':entry.get('unitId',''),
            'packSlug':entry.get('_packSlug') or pack.get('slug',pack['packId']),
            'packId':entry.get('_sourcePackId') or pack['packId'],
            'sourceRevision':pack.get('contentRevision',''),
            'headword':entry['headword'],'reading':reading_of(entry),
            'meaning':entry.get('gloss',{}).get('zh') or entry.get('gloss',{}).get('en',''),
            'explanation':entry.get('grammar',{}).get('notes',''),
            'examples':entry.get('examples',[])[:3], 'variantKey':variant,
            **copy.deepcopy(spec)}


# Which answering modes each exercise type is allowed to use. A mode that cannot
# express the type's task would otherwise be scored as if it had (LEX-04, §6.2).
SPEC_MODES = {
 'recall':{'self'},'production':{'self','input'},'writing':{'self'},'reading':{'input'},
 'meaning':{'choice'},'usage':{'choice'},'collocation':{'choice'},'context':{'choice'},
 'connection':{'choice','input'},'listening':{'choice','input'},'cloze':{'input','choice'},'order':{'order'},
}


def validate_spec(spec: dict) -> None:
    if spec.get('type') not in TYPES: raise ValueError('未知题型。')
    if not isinstance(spec.get('prompt'),str) or not spec['prompt'].strip(): raise ValueError('题目缺少题面。')
    mode=spec.get('mode','input')
    if mode not in {'input','choice','order','self'}: raise ValueError('未知作答方式。')
    if mode not in SPEC_MODES[spec['type']]: raise ValueError(f"题型 {spec['type']} 不能使用「{mode}」作答方式。")
    if str(spec.get('reviewStatus') or 'draft') not in REVIEW_STATES+('verified',): raise ValueError('未知审核状态。')
    review=spec.get('review')
    if review is not None:
        if not isinstance(review,dict): raise ValueError('审核记录必须是对象。')
        for key in ('method','reviewer','contentHash'):
            if key in review and not isinstance(review[key],str): raise ValueError('审核记录字段类型无效。')
        if 'checks' in review and not isinstance(review['checks'],dict): raise ValueError('审核检查项必须是对象。')
    if mode=='self': return
    if not spec.get('explanation'): raise ValueError('自动判分题需要解析。')
    answers=spec.get('acceptedAnswers')
    if not isinstance(answers,list) or not answers: raise ValueError('题目需要明确的允许答案。')
    if len(answers)>50: raise ValueError('允许答案过多，请改为自评题。')
    if mode=='choice':
        choices=spec.get('choices',[]); ids=[c.get('id') for c in choices]
        if len(ids)<2 or len(set(ids))!=len(ids): raise ValueError('选项 ID 无效。')
        if any(not isinstance(i,str) or not i for i in ids): raise ValueError('选项 ID 无效。')
        labels=[str(c.get('label','')) for c in choices]
        if len(set(labels))!=len(labels): raise ValueError('选项文本不能重复。')
        if any(answer not in ids for answer in answers): raise ValueError('正确答案不在选项中。')
        if len(answers)>=len(ids): raise ValueError('选择题需要至少一个不正确的选项。')
        if any(not c.get('rationale') for c in choices): raise ValueError('每个选项必须有解析。')
    if mode=='order':
        ids=[t['id'] for t in spec.get('tokens',[])]
        if len(ids)<2 or len(set(ids))!=len(ids): raise ValueError('排序片段 ID 无效。')
        if any(not isinstance(a,list) or sorted(a)!=sorted(ids) for a in answers): raise ValueError('排序答案必须覆盖所有片段。')
    if mode=='input':
        blanks=spec.get('blankCount',1)
        if isinstance(blanks,bool) or not isinstance(blanks,int) or not 1<=blanks<=10: raise ValueError('空位数量无效。')
        if blanks>1 and any(not isinstance(a,list) or len(a)!=blanks for a in answers):
            raise ValueError('多空题每个答案必须与空位数量一致。')
        if blanks==1 and any(not isinstance(a,str) or not a.strip() for a in answers):
            raise ValueError('填空答案必须是非空文本。')


def questions_for(pack: dict, entry: dict, *, include_pending: bool=False) -> list[dict]:
    """Formal questions for one entry.

    Structural questions built here from the entry's own source fields stay qualified.
    Authored `exerciseTemplates` must carry a real review record: generation alone is
    not review, so they are withheld from formal practice until one exists (LEX-04).
    `include_pending` returns the withheld ones too, marked, for draft preview.
    """
    if entry.get('qualityStatus') in {'draft','disputed','retired'}: return []
    questions=[]; gloss=entry.get('gloss',{}); meaning=gloss.get('zh') or gloss.get('en','')
    if meaning:
        questions.append(_question(pack,entry,{'type':'recall','mode':'self','prompt':entry['headword'],'referenceAnswer':meaning,'explanation':meaning},'recall-default'))
        questions.append(_question(pack,entry,{'type':'production','mode':'self','prompt':meaning,'referenceAnswer':entry['headword'],'explanation':'允许按语境使用其他合适表达；本题自评。'},'production-default'))
    reading=reading_of(entry)
    if entry['kind']=='word' and reading and (entry.get('dictRef') or entry.get('fieldSources',{}).get('reading')):
        questions.append(_question(pack,entry,{'type':'reading','mode':'input','prompt':f"写出「{plain(entry['headword'])}」在本条义项中的读音：{meaning}",'acceptedAnswers':entry.get('acceptedReadings') or [reading],'normalizeReading':True,'explanation':f"本条读音：{reading}。{meaning}"},'reading-default'))
    for template in entry.get('cardTemplates',[]):
        marked=template.get('markedJa','')
        blanks=re.findall(r'⟦([^⟦⟧]+)⟧',marked)
        if template.get('promptType')=='cloze' and blanks and meaning:
            questions.append(_question(pack,entry,{'type':'cloze','mode':'input',
              'prompt':'按本条例句补回空缺（多空用 / 分隔）：\n'+re.sub(r'⟦[^⟦⟧]+⟧','＿＿',plain_keep_cloze(marked)),
              'acceptedAnswers':[blanks] if len(blanks)>1 else blanks,'blankCount':len(blanks),
              'explanation':plain(marked)+'\n'+meaning,'referenceAnswer':' / '.join(blanks)},template.get('variantKey','cloze-default')))
        if template.get('promptType')=='usage' and meaning:
            index={source_ref(pack,e):e for e in pack.get('entries',[])}; index['self']=entry
            example=next((e for e in entry.get('examples',[]) if e.get('exampleId')==template.get('exampleId')),None)
            rationales={r.get('choiceRef'):r.get('reason') for r in template.get('rationales',[])}
            choices=[]
            for i,ref in enumerate(template.get('choiceRefs',[])):
                other=index.get(ref)
                if other: choices.append({'id':ref,'label':other['headword'],'rationale':meaning if ref==template.get('answerRef') else rationales.get(ref,'')})
            if example and len(choices)>=2:
                spec={'type':'usage','mode':'choice','prompt':template.get('question') or example.get('markedJa') or example['ja'],'choices':choices,'acceptedAnswers':[template.get('answerRef')],'explanation':meaning}
                # Without an explicit blank, the example already discloses its answer.
                if '⟦' in spec['prompt']:
                    spec['prompt']=re.sub(r'⟦[^⟦⟧]+⟧','＿＿',spec['prompt'])
                    try: validate_spec(spec)
                    except ValueError: continue
                    questions.append(_question(pack,entry,spec,template['variantKey']))
    for question in questions: question.update(qualified=True,reasonCodes=[])
    for spec in entry.get('exerciseTemplates',[]):
        validate_spec(spec)
        qualified,codes=qualification(spec)
        if not qualified and not include_pending: continue
        question=_question(pack,entry,spec,spec['variantKey'])
        question.update(qualified=qualified,reasonCodes=codes)
        questions.append(question)
    return questions


def plain_keep_cloze(text: str) -> str:
    return re.sub(r'｜([^《]+)《[^》]+》',r'\1',str(text))


def capabilities(pack: dict,entry: dict) -> dict:
    """Per-type eligibility with reasons, so a plan can never be created empty in silence."""
    try: questions=questions_for(pack,entry,include_pending=True)
    except (ValueError,KeyError,TypeError): questions=[]
    by_type: dict[str,dict]={}
    for question in questions:
        slot=by_type.setdefault(question['type'],{'available':False,'reasonCodes':[],'questionCount':0,'pendingCount':0})
        if question.get('qualified'):
            slot['available']=True; slot['questionCount']+=1
        else:
            slot['pendingCount']+=1
            for code in question.get('reasonCodes',[]):
                if code not in slot['reasonCodes']: slot['reasonCodes'].append(code)
    if 'listening' in by_type and not reading_of(entry):
        by_type['listening'].update(available=False,reasonCodes=sorted(set(by_type['listening']['reasonCodes'])|{'audio.unavailable'}))
    for slot in by_type.values():
        if slot['available']: slot['reasonCodes']=[]
    missing=[]
    if not entry.get('gloss',{}).get('zh'): missing.append('中文释义')
    if not entry.get('examples'): missing.append('例句')
    if entry['kind']=='word' and not reading_of(entry): missing.append('可靠读音')
    return {'types':sorted(t for t,v in by_type.items() if v['available']),
            'pendingTypes':sorted(t for t,v in by_type.items() if not v['available']),
            'byType':by_type,'missing':missing,
            'questionCount':sum(v['questionCount'] for v in by_type.values()),
            'pendingCount':sum(v['pendingCount'] for v in by_type.values())}


def choice_alias(question: dict, scope: str) -> dict:
    """Map each private choice id to an opaque public one.

    The authored ids carry meaning — the correct option of a generated `usage` item is
    literally called `answer` — so publishing them hands over the answer no matter how
    the options are ordered. The alias is derived, not stored, so the same session and
    question always produce the same public ids (LEX-10, §10.1).
    """
    aliases={}
    for choice in question.get('choices') or []:
        key=hashlib.sha256(f"{scope}\x1f{question.get('id','')}\x1f{choice.get('id','')}".encode()).hexdigest()
        aliases[choice['id']]='c_'+key[:16]
    return aliases


def resolve_choice(question: dict, scope: str, answer):
    """Translate a submitted public choice id back to the id scoring understands."""
    if question.get('mode')!='choice' or not isinstance(answer,str): return answer
    for private,public in choice_alias(question,scope).items():
        if answer==public: return private
    return answer


def public_question(question: dict, *, answers: bool=False, scope: str='') -> dict:
    result=copy.deepcopy(question)
    aliases=choice_alias(question,scope) if scope else {}
    if aliases:
        for choice in result.get('choices',[]): choice['id']=aliases.get(choice['id'],choice['id'])
        if 'acceptedAnswers' in result:
            result['acceptedAnswers']=[aliases.get(a,a) for a in result['acceptedAnswers']]
    if not answers:
        for key in ('acceptedAnswers','referenceAnswer','explanation','reading','meaning','examples','headword','evidence'):
            result.pop(key,None)
        if question.get('type')=='listening': result['speech']=question.get('speech') or question.get('reading')
        for choice in result.get('choices',[]): choice.pop('rationale',None)
    return result


def public_result(question: dict, result: dict, scope: str) -> dict:
    """Re-express a score's option references in the same public id space."""
    if not scope or question.get('mode')!='choice': return result
    aliases=choice_alias(question,scope)
    result=dict(result)
    result['choices']=[{**c,'id':aliases.get(c['id'],c['id'])} for c in result.get('choices') or []]
    reference=result.get('referenceAnswer')
    if isinstance(reference,list): result['referenceAnswer']=[aliases.get(a,a) for a in reference]
    return result


def score(question: dict, answer, *, hinted: bool=False, guessed: bool=False, skipped: bool=False) -> dict:
    mode=question.get('mode','input'); grade=None
    correct=None; parts=[]
    if skipped: classification='skipped'
    elif mode=='self':
        grade=answer.get('grade') if isinstance(answer,dict) else answer
        if grade not in GRADES: raise ValueError('请选择有效的自评等级。')
        classification='self_assessed'
    else:
        allowed=question.get('acceptedAnswers',[])
        if mode=='choice':
            if answer not in [c['id'] for c in question.get('choices',[])]: raise ValueError('所选答案不存在。')
            correct=answer in allowed
        elif mode=='order':
            ids=[t['id'] for t in question.get('tokens',[])]
            if not isinstance(answer,list) or sorted(answer)!=sorted(ids): raise ValueError('请排列全部片段。')
            correct=answer in allowed
        elif int(question.get('blankCount',1))>1:
            values=answer if isinstance(answer,list) else str(answer).split('/')
            normalized=[normalize(v,reading=question.get('normalizeReading',False)) for v in values]
            accepted=[[normalize(v,reading=question.get('normalizeReading',False)) for v in row] for row in allowed]
            correct=normalized in accepted
            parts=[any(i<len(row) and i<len(normalized) and normalized[i]==row[i] for row in accepted) for i in range(int(question['blankCount']))]
        else:
            if not isinstance(answer,str) or len(answer)>4000: raise ValueError('答案必须是 4000 字以内的文本。')
            correct=normalize(answer,reading=question.get('normalizeReading',False)) in [normalize(a,reading=question.get('normalizeReading',False)) for a in allowed]
        classification='correct' if correct else 'wrong'
        if correct and (hinted or guessed): classification='assisted'
    reliable=classification=='correct'
    effective_grade=(grade if not hinted and not guessed else 'again') if mode=='self' else ('good' if reliable else 'again')
    needs_retry=not skipped and (classification in {'wrong','assisted'} or mode=='self' and effective_grade in {'again','hard'})
    return {'correct':correct,'classification':classification,'hinted':bool(hinted),'guessed':bool(guessed),'skipped':bool(skipped),'selfGrade':grade,'suggestedGrade':None if skipped else effective_grade,'needsRetry':needs_retry,'parts':parts,
            'referenceAnswer':question.get('referenceAnswer') or question.get('acceptedAnswers',[]),
            'explanation':question.get('explanation',''),'choices':question.get('choices',[]),'headword':question.get('headword',''),'examples':question.get('examples',[])}
