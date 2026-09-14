"""Persistent practice sessions, personal entries and atomic scoring transactions."""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import json
import random
import re
import secrets
from lexicon_exercise import (TYPES, SCORING_VERSION, public_question, public_result, questions_for,
                              reading_of, resolve_choice, score, source_ref)


def dump(value): return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def now(): return datetime.now(timezone.utc).isoformat()


class ConflictError(ValueError): pass


def scoring_digest(payload: dict) -> str:
    """Digest of the fields that decide the score, so a replay is recognisable as one."""
    from local_backend import request_digest
    return request_digest({'itemId':payload.get('itemId'),'round':int(payload.get('round',0)),
      'answer':payload.get('answer'),'skipped':bool(payload.get('skipped')),'guessed':bool(payload.get('guessed'))})


class PracticeStore:
    def __init__(self,learning,lexicon,dictionary):
        self.learning=learning; self.lexicon=lexicon; self.dictionary=dictionary
        self.db=learning.connection; self.lock=learning.lock

    def user_entries(self,include_deleted=False):
        with self.lock:
            rows=self.db.execute('SELECT * FROM lex_user_entries'+('' if include_deleted else ' WHERE deleted=0')+' ORDER BY updated_at DESC').fetchall()
            return [{**json.loads(r['data_json']),'sourceRef':r['source_ref'],'version':r['version'],'deleted':bool(r['deleted']),'updatedAt':r['updated_at']} for r in rows]

    def save_user_entry(self,payload):
        with self.lock,self.db:
            return self._save_user_entry(payload)

    def _save_user_entry(self,payload):
        """The body, without its own transaction, so a batch import is one commit.

        Nesting `with connection` blocks committed each entry as it went, which meant a
        failure half way through left half a backup applied (§11.1).
        """
        ref=str(payload.get('sourceRef',''))
        # `dict:jmdict#1234/<senseKey>` is a specific sense of a dictionary entry. Two
        # senses of one entSeq are different things to learn and must not overwrite each
        # other, so the sense is part of the reference (LEX-09, §9.2.3).
        if not re.fullmatch(r'(?:lex:[A-Za-z0-9._-]+#[wg]_[a-f0-9]{24}|dict:jmdict#[0-9]+(?:/[0-9a-f]{20})?|user:[A-Za-z0-9_-]+)',ref): raise ValueError('条目引用无效。')
        if len(dump(payload))>24000: raise ValueError('条目过长。')
        old=self.db.execute('SELECT * FROM lex_user_entries WHERE source_ref=?',(ref,)).fetchone()
        if old and payload.get('version') is not None and int(payload['version'])!=old['version']: raise ConflictError('条目已更新，请重新载入后保存。')
        data=json.loads(old['data_json']) if old else {}
        for key in ('headword','reading','gloss','note','tags','starred','kind','level','examples','snapshot','custom','selection'):
            if key in payload: data[key]=payload[key]
        selection=data.get('selection')
        if selection is not None:
            if not isinstance(selection,dict): raise ValueError('义项选择必须是对象。')
            keys=selection.get('senseKeys')
            if keys is not None and (not isinstance(keys,list) or any(not re.fullmatch(r'[0-9a-f]{20}',str(k)) for k in keys)):
                raise ValueError('义项键无效。')
        if ref.startswith('user:') and not str(data.get('headword','')).strip():raise ValueError('个人条目需要词语或文型。')
        if 'tags' in data and not isinstance(data['tags'],list): raise ValueError('标签必须是数组。')
        if data.get('kind','word') not in {'word','grammar'}:raise ValueError('类型无效。')
        if not isinstance(data.get('gloss',{}),dict):raise ValueError('释义必须是对象。')
        version=(old['version'] if old else 0)+1; ts=now(); deleted=bool(payload.get('deleted',False))
        self.db.execute('INSERT INTO lex_user_entries VALUES (?,?,?,?,?) ON CONFLICT(source_ref) DO UPDATE SET data_json=excluded.data_json,version=excluded.version,deleted=excluded.deleted,updated_at=excluded.updated_at',(ref,dump(data),version,int(deleted),ts))
        context=payload.get('context')
        if isinstance(context,dict):
            key=hashlib.sha256(dump(context).encode()).hexdigest()
            self.db.execute('INSERT OR IGNORE INTO lex_entry_sources VALUES (?,?,?)',(ref,key,dump(context)))
        return {**data,'sourceRef':ref,'version':version,'deleted':deleted,'updatedAt':ts}

    def contexts(self,ref):
        with self.lock:return [json.loads(r[0]) for r in self.db.execute('SELECT data_json FROM lex_entry_sources WHERE source_ref=?',(ref,))]

    # ---- personal backup (LEX-16, §11.1) -----------------------------------

    BACKUP_VERSION = 2

    def export_personal(self,include_learning=False):
        """A backup that restores what it contains.

        Version 1 shipped `contexts` in a shape import ignored, so a round trip silently
        dropped every saved sentence a favourite came from. Learning data is only
        included when explicitly asked for: it is much larger and rarely what someone
        moving their notes wants (§11.1).
        """
        with self.lock:
            entries=self.user_entries(True)
            payload={'schemaVersion':self.BACKUP_VERSION,'exportedAt':now(),
                     'entries':entries,
                     'contexts':[{'sourceRef':ref,'contexts':self.contexts(ref)}
                                 for ref in sorted({e['sourceRef'] for e in entries})
                                 if self.contexts(ref)],
                     # Kept so a v1 file and a v2 file are both readable by either side.
                     'items':entries}
            if include_learning:
                payload['learning']=self._export_learning()
            return payload

    def _export_learning(self):
        rows=lambda sql:[dict(r) for r in self.db.execute(sql).fetchall()]
        return {
            'cards':rows("SELECT id,term,reading,meaning,note,tags,level,srs_stage,srs_interval,srs_ease,"
                         "srs_repetitions,srs_lapses,next_review_at,last_reviewed_at,mastered,entry_kind,"
                         "source_ref,prompt_type,variant_key,source_revision,review_suspended,review_version,"
                         "created_at,updated_at FROM vocab"),
            'tombstones':rows('SELECT * FROM lex_card_tombstones'),
            'decks':rows('SELECT * FROM lex_decks'),
            'deckSettings':rows('SELECT * FROM lex_deck_settings'),
            'deckCards':rows('SELECT * FROM lex_deck_cards'),
            'sessions':rows('SELECT * FROM lex_sessions'),
            'attempts':rows('SELECT * FROM lex_attempts'),
            'mistakes':rows('SELECT * FROM lex_mistakes'),
            'reviewEvents':rows('SELECT * FROM lex_review_events'),
            'receipts':rows('SELECT * FROM vocab_review_receipts'),
        }

    def preview_import(self,payload):
        """Say what an import would do before it does any of it."""
        entries=payload.get('entries')
        if not isinstance(entries,list): entries=payload.get('items')
        if not isinstance(entries,list): raise ValueError('备份文件缺少条目列表。')
        if len(entries)>5000: raise ValueError('一次最多导入 5000 条个人条目。')
        version=int(payload.get('schemaVersion') or 1)
        if version>self.BACKUP_VERSION:
            raise ValueError(f'备份格式版本 {version} 比本程序支持的 {self.BACKUP_VERSION} 更新，请先升级。')
        existing={e['sourceRef']:e for e in self.user_entries(True)}
        ready=[];errors=[];added=[];updated=[];conflicts=[];duplicates=[];unresolved=[]
        seen=set()
        for index,item in enumerate(entries):
            if not isinstance(item,dict):
                errors.append({'row':index+1,'error':'条目必须是对象'});continue
            entry=dict(item)
            ref=str(entry.get('sourceRef') or '')
            if not ref:
                # A hash of the whole object made the note part of the identity, so
                # editing a note produced a new entry on the next import (§11.1).
                head=str(entry.get('headword','')).strip()
                if not head:
                    errors.append({'row':index+1,'error':'缺少词语/文型'});continue
                ref=entry['sourceRef']='user:'+hashlib.sha256(
                    (head+'\x1f'+str(entry.get('reading',''))).encode()).hexdigest()[:24]
            if not str(entry.get('headword','')).strip() and not ref.startswith(('lex:','dict:')):
                errors.append({'row':index+1,'error':'缺少词语/文型'});continue
            if ref in seen: duplicates.append(ref);continue
            seen.add(ref)
            if ref in existing:
                incoming=str(entry.get('updatedAt') or '');current=str(existing[ref].get('updatedAt') or '')
                if incoming and current and incoming<current: conflicts.append(ref)
                updated.append(ref)
            else:
                added.append(ref)
                if ref.startswith('lex:') and not self.lexicon.find_pack(ref[4:].split('#')[0]):
                    unresolved.append(ref)
            entry.pop('version',None)
            ready.append(entry)
        contexts=[c for c in (payload.get('contexts') or []) if isinstance(c,dict)]
        return {'schemaVersion':version,'ready':ready,'errors':errors,'count':len(ready),
                'added':added,'updated':updated,'conflicts':conflicts,'duplicates':duplicates,
                'unresolvedReferences':unresolved,
                'contexts':sum(len(c.get('contexts') or []) for c in contexts),
                'includesLearning':bool(payload.get('learning'))}

    def import_personal(self,payload):
        """Apply a validated backup in one transaction, or none of it."""
        preview=self.preview_import(payload)
        if preview['errors']: raise ValueError('导入有错误，请先修正预览中标出的行。')
        contexts=[c for c in (payload.get('contexts') or []) if isinstance(c,dict)]
        with self.lock,self.db:
            saved=[]
            for entry in preview['ready']:
                current=self.db.execute('SELECT version FROM lex_user_entries WHERE source_ref=?',
                                        (entry['sourceRef'],)).fetchone()
                # The file's own version numbers mean nothing here; take the current one
                # so a restore is an update rather than a conflict.
                saved.append(self._save_user_entry(dict(entry,version=current[0] if current else None)))
            restored=0
            for record in contexts:
                ref=str(record.get('sourceRef') or '')
                if not ref: continue
                for context in record.get('contexts') or []:
                    if not isinstance(context,dict): continue
                    key=hashlib.sha256(dump(context).encode()).hexdigest()
                    self.db.execute('INSERT OR IGNORE INTO lex_entry_sources VALUES (?,?,?)',
                                    (ref,key,dump(context)));restored+=1
            return {'items':saved,'count':len(saved),'contexts':restored,
                    'added':len(preview['added']),'updated':len(preview['updated'])}

    def entries(self,config):
        slugs=set(config.get('packSlugs') or []); units=set(config.get('unitIds') or []); refs=set(config.get('sourceRefs') or [])
        personal={e['sourceRef']:e for e in self.user_entries()}
        if config.get('scope')=='favorites': refs=refs or {r for r,e in personal.items() if e.get('starred')}
        if config.get('scope')=='wrong': refs=refs or {m['sourceRef'] for m in self.mistakes() if not m['resolved']}
        restrict_refs=bool(config.get('sourceRefs')) or config.get('scope') in {'favorites','wrong'}
        for summary in self.lexicon.list_packs():
            if summary.get('broken') or slugs and summary['slug'] not in slugs: continue
            if config.get('kind') and summary.get('kind')!=config['kind']:continue
            if config.get('level') and summary.get('level')!=config['level']:continue
            pack=self.lexicon.get_pack(summary['slug'])
            if not pack or pack['quality']['blocked']:continue
            for entry in pack['entries']:
                ref=source_ref(pack,entry)
                if units and entry.get('unitId') not in units:continue
                if restrict_refs and ref not in refs:continue
                yield pack,entry
        # Selected dictionary entries can be learned without creating a fake textbook.
        for ref,user in personal.items():
            if slugs:continue
            if restrict_refs and ref not in refs:continue
            if not ref.startswith(('dict:','user:')):continue
            entry=dict(user)
            if ref.startswith('dict:'):
                key,_,sense_key=ref.split('#')[-1].partition('/')
                original=self.dictionary.get(key)
                if not original:continue
                selection=user.get('selection') if isinstance(user.get('selection'),dict) else {}
                written=str(selection.get('writtenForm') or '')
                reading=str(selection.get('reading') or user.get('reading') or '')
                wanted={str(k) for k in (selection.get('senseKeys') or ([sense_key] if sense_key else []))}
                senses=[s for s in original.get('senses') or [] if not wanted or str(s.get('key')) in wanted]
                gloss=dict(user.get('gloss') or {})
                if senses and not gloss.get('en'):
                    # Learn the sense that was chosen, not every sense the entry has.
                    gloss['en']='; '.join(g for s in senses for g in s.get('gloss',[]))
                if not reading:
                    readings=self.dictionary.readings_for(original,written)
                    reading=readings[0]['text'] if readings else original.get('reading','')
                entry={**original,**user,'gloss':gloss,'senses':senses or original.get('senses',[]),
                       'headword':user.get('headword') or written or original.get('headword',''),
                       'reading':reading,
                       'dictRef':{'source':'jmdict','entSeq':key,'writtenForm':written or original.get('headword',''),
                                  'reading':reading,'senseKeys':sorted(wanted),
                                  'dictionaryVersion':str(selection.get('dictionaryVersion') or '')}}
            entry.update({'id':ref,'_sourceRef':ref,'kind':entry.get('kind','word'),'headword':entry.get('headword','')})
            if config.get('kind') and entry['kind']!=config['kind']:continue
            if config.get('level') and entry.get('level','')!=config['level']:continue
            yield {'packId':'personal','slug':'personal','contentRevision':str(user['version'])},entry

    def create(self,payload,operation_id=''):
        count=payload.get('count',10)
        if isinstance(count,bool) or not isinstance(count,int) or not 1<=count<=100:raise ValueError('题量必须为 1–100 的整数。')
        types=payload.get('types') or ['reading','cloze','meaning','connection']
        if not isinstance(types,list) or any(t not in TYPES for t in types):raise ValueError('练习题型无效。')
        if payload.get('kind','') not in {'','word','grammar'}:raise ValueError('练习类型无效。')
        for field in ('packSlugs','unitIds','sourceRefs'):
            if field in payload and (not isinstance(payload[field],list) or len(payload[field])>2000 or any(not isinstance(s,str) for s in payload[field])):raise ValueError('学习范围无效。')
        feedback=payload.get('feedback','instant')
        if feedback not in {'instant','end'}:raise ValueError('反馈方式无效。')
        # A self-assessed item needs the reference answer to grade against, and end mode
        # withholds it until submit. Creating that pair produces a session the learner
        # cannot finish, so it is refused up front rather than blocked mid-session (§10.1).
        if feedback=='end' and any(t in {'recall','production','writing'} for t in types):
            raise ValueError('整组提交模式不能包含自评题（回忆释义 / 看释义回忆词语 / 造句）；请改为即时反馈，或去掉这些题型。')
        if operation_id:
            with self.lock:
                existing=self.db.execute('SELECT id FROM lex_sessions WHERE creation_key=?',(operation_id,)).fetchone()
            if existing:return self.get(existing['id'])
        config={k:payload[k] for k in ('kind','level','packSlugs','unitIds','sourceRefs','scope','feedback','review','count','order') if k in payload}
        config['types']=types
        # Unreviewed content is not verified practice, but it is still practice. The gate
        # decides whether an answer counts, not whether the learner may attempt it
        # (§6.1). A draft session says so, and its answers never touch the SRS or the
        # formal accuracy.
        config['includeDrafts']=bool(payload.get('includeDrafts'))
        items=[];drafts=[];pending={};withdrawn=self.withdrawn_questions()
        for pack,entry in self.entries(config):
            for question in questions_for(pack,entry,include_pending=True):
                if question['type'] not in types:continue
                # A withdrawn question is wrong, not merely unreviewed: it is never served.
                if question['id'] in withdrawn:
                    pending.setdefault(question['type'],set()).add('review.withdrawn');continue
                if question.get('qualified'):items.append(question)
                else:
                    drafts.append(question)
                    pending.setdefault(question['type'],set()).update(question.get('reasonCodes',[]))
        if config['includeDrafts']:items=items+drafts
        if not items:
            # "0 questions" is never an acceptable answer on its own; say what is missing.
            if pending:
                detail='；'.join(f"{TYPES.get(t,t)}（{'、'.join(sorted(codes))}）" for t,codes in sorted(pending.items()))
                usable=len([q for q in drafts if 'review.withdrawn' not in q.get('reasonCodes',[])])
                hint=(f'可勾选「包含未审核题目」先练（{usable} 道，不计入正式正确率），'
                      '或改选其他题型。' if usable else '可改选其他题型，或先完成内容审核。')
                raise ValueError(f'所选题型还没有通过审核的正式题目：{detail}。{hint}')
            raise ValueError('所选范围没有符合条件的题目，请调整题型、内容包或先收藏条目。')
        session_id='ls_'+secrets.token_hex(12); rng=random.Random(session_id)
        if config.get('order')!='source':rng.shuffle(items)
        # Spread different entries before adding a second ability of the same entry.
        seen=set(); first=[]; rest=[]
        for q in items:
            (rest if q['sourceRef'] in seen else first).append(q); seen.add(q['sourceRef'])
        available=len(items); items=(first+rest)[:count]
        for q in items:
            if q.get('choices'):rng.shuffle(q['choices'])
            if q.get('tokens'):rng.shuffle(q['tokens'])
        state={'cursor':0,'queue':[{'itemId':q['id'],'round':0} for q in items],'exposed':[], 'available':available,'requested':count}
        ts=now()
        with self.lock,self.db:
            self.db.execute('INSERT INTO lex_sessions(id,mode,config_json,items_json,state_json,created_at,updated_at,creation_key) VALUES (?,?,?,?,?,?,?,?)',(session_id,'practice',dump(config),dump(items),dump(state),ts,ts,operation_id or None))
        return self.get(session_id)

    def _next_sequence(self,session_id):
        """Answers, reveals and skips share one order, so a replay can rebuild it exactly."""
        highest=self.db.execute('SELECT MAX(s) FROM (SELECT MAX(sequence) AS s FROM lex_attempts WHERE session_id=?'
                                ' UNION ALL SELECT MAX(sequence) FROM lex_reveals WHERE session_id=?)',
                                (session_id,session_id)).fetchone()[0]
        return int(highest or 0)+1

    def _load(self,session_id):
        row=self.db.execute('SELECT * FROM lex_sessions WHERE id=?',(session_id,)).fetchone()
        if not row:raise KeyError('练习记录不存在。')
        return dict(row),json.loads(row['config_json']),json.loads(row['items_json']),json.loads(row['state_json'])

    def get(self,session_id,offline=False):
        with self.lock:
            row,config,items,state=self._load(session_id)
            attempts=self._attempts(session_id)
            done=row['status'] in {'completed','completed_with_skips'}; answers=config.get('feedback','instant')=='instant' or done
            visible=[]
            for a in attempts:
                if answers:visible.append(a)
                else:visible.append({k:a[k] for k in ('itemId','round','answer','createdAt')})
            withdrawn=self.withdrawn_questions()
            published=[]
            for question in items:
                shown=public_question(question,answers=offline or done,scope=session_id)
                # Withdrawn mid-session: say so and let it be skipped, rather than
                # leaving the learner stuck on a question that no longer counts (§10.3).
                if not question.get('qualified',True):
                    shown['draft']=True
                    shown['draftReason']='未通过内容审核：不计入正式正确率，也不推进长期复习。'
                if question['id'] in withdrawn:
                    shown['unavailable']=True
                    shown['unavailableReason']='这道题已被撤回，可跳过；本题不计入统计。'
                published.append(shown)
            draft_items=sorted(q['id'] for q in items if not q.get('qualified',True))
            return {'id':row['id'],'status':row['status'],'version':row['version'],'createdAt':row['created_at'],'updatedAt':row['updated_at'],'config':config,'state':state,
                    'items':published,'attempts':visible,'offlinePrepared':bool(offline),
                    'withdrawnItems':sorted(q['id'] for q in items if q['id'] in withdrawn),
                    'draftItems':draft_items,'draftCount':len(draft_items),
                    'scoringVersion':SCORING_VERSION}

    def list_sessions(self):
        with self.lock:
            rows=self.db.execute('SELECT id,status,created_at,updated_at,config_json,state_json FROM lex_sessions ORDER BY updated_at DESC LIMIT 200').fetchall()
        return [{'id':r['id'],'status':r['status'],'createdAt':r['created_at'],'updatedAt':r['updated_at'],'config':json.loads(r['config_json']),'state':json.loads(r['state_json'])} for r in rows]

    def expose(self,session_id,payload,operation_id=''):
        round_=int(payload.get('round',0))
        with self.lock,self.db:
            if operation_id:
                seen=self.db.execute('SELECT * FROM lex_reveals WHERE operation_id=?',(operation_id,)).fetchone()
                if seen:
                    if seen['session_id']!=session_id or seen['item_id']!=payload.get('itemId') or int(seen['round'])!=round_:
                        raise ConflictError('operationId 已用于其他提示请求。')
                    row,_,items,_=self._load(session_id)
                    question=next(q for q in items if q['id']==seen['item_id'])
                    return {'question':public_question(question,answers=True,scope=session_id),'version':row['version'],
                            'sequence':int(seen['sequence']),'duplicate':True}
            row,config,items,state=self._load(session_id)
            question=next((q for q in items if q['id']==payload.get('itemId')),None)
            if not question:raise KeyError('题目不存在。')
            if config.get('feedback')=='end' and row['status'] not in {'completed','completed_with_skips'}:raise ConflictError('整组提交模式中不能提前查看答案。')
            key=f"{question['id']}:{round_}"
            if key not in state['exposed']:state['exposed'].append(key)
            sequence=self._next_sequence(session_id)
            # A hint is part of the answer's version chain: replaying the session offline
            # has to reproduce the same order, not just the same answers (§8.2).
            self.db.execute('INSERT OR IGNORE INTO lex_reveals VALUES (?,?,?,?,?,?)',
                            (operation_id or 'rv_'+secrets.token_hex(12),session_id,question['id'],round_,sequence,now()))
            self.db.execute('UPDATE lex_sessions SET state_json=?,version=version+1,updated_at=? WHERE id=?',(dump(state),now(),session_id))
            return {'question':public_question(question,answers=True,scope=session_id),'version':row['version']+1,'sequence':sequence}

    def answer(self,session_id,payload,operation_id):
        if not operation_id or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}',operation_id):raise ValueError('需要有效的 operationId。')
        if len(dump(payload))>16000:raise ValueError('答案过长。')
        digest=scoring_digest(payload)
        with self.lock,self.db:
            receipt=self.db.execute('SELECT session_id,item_id,result_json,request_digest FROM lex_attempts WHERE operation_id=?',(operation_id,)).fetchone()
            if receipt:
                stored=str(receipt['request_digest'] or '')
                if receipt['session_id']!=session_id or receipt['item_id']!=payload.get('itemId') or (stored and stored!=digest):
                    raise ConflictError('operationId 已用于其他答案。')
                _,_,items,_=self._load(session_id)
                original=next((q for q in items if q['id']==receipt['item_id']),None)
                return self._answer_response(session_id,json.loads(receipt['result_json']),duplicate=True,question=original)
            row,config,items,state=self._load(session_id)
            if row['status']!='active':raise ConflictError('练习已经结束。')
            item_id=payload.get('itemId'); round_=int(payload.get('round',0))
            existing=self.db.execute('SELECT 1 FROM lex_attempts WHERE session_id=? AND item_id=? AND round=?',(session_id,item_id,round_)).fetchone()
            if existing:raise ConflictError('这次作答已经提交，请载入最新状态。')
            if state['cursor']>=len(state['queue']) or state['queue'][state['cursor']]!={'itemId':item_id,'round':round_}:raise ConflictError('题目顺序已改变，请继续当前题。')
            if payload.get('version') is not None and int(payload['version'])!=row['version']:raise ConflictError('另一页面已更新练习，请重新载入。')
            question=next(q for q in items if q['id']==item_id)
            exposed=f'{item_id}:{round_}' in state['exposed']
            submitted=resolve_choice(question,session_id,payload.get('answer'))
            result=score(question,submitted,hinted=(exposed or bool(payload.get('hinted'))) and question.get('mode')!='self',guessed=bool(payload.get('guessed')),skipped=bool(payload.get('skipped')))
            duration=payload.get('elapsedMs',0)
            if isinstance(duration,bool) or not isinstance(duration,(int,float)) or not 0<=duration<=4*3600000:raise ValueError('作答用时无效。')
            ts=payload.get('reviewedAt') or now()
            from local_backend import _parse_reviewed_at
            ts=_parse_reviewed_at(ts).isoformat()
            draft=not question.get('qualified',True)
            result.update({'elapsedMs':int(duration),'srsApplied':False,'draft':draft})
            if draft:
                result['draftNotice']='本题尚未通过内容审核：结果不计入正式正确率，也不推进长期复习。'
            first_answer=not any(not a['result']['skipped'] and a['itemId']==item_id for a in self._attempts(session_id))
            result['firstAnswer']=first_answer and not result['skipped']
            if config.get('review',True) and first_answer and config.get('feedback')!='end' and not result['skipped'] and not draft:
                self._apply_srs(question,result,operation_id,ts,digest)
            attempt_id='la_'+secrets.token_hex(12); sequence=self._next_sequence(session_id)
            result['sequence']=sequence
            self.db.execute('INSERT INTO lex_attempts(id,session_id,item_id,round,source_ref,kind,exercise_type,answer_json,result_json,operation_id,created_at,request_digest,sequence,validity)'
                            ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(attempt_id,session_id,item_id,round_,question['sourceRef'],question['kind'],question['type'],dump(payload.get('answer')),dump(result),operation_id,ts,digest,sequence,'draft' if draft else 'valid'))
            # In end mode nothing derived from this answer may exist before submit, or the
            # mistake book becomes a side channel that reports the result early (§10.1).
            # A draft answer never enters the mistake book: its answer key is unverified.
            if config.get('feedback')!='end' and not draft:
                self._mistake(question,result,attempt_id,ts,0 if first_answer and not result['skipped'] else 1)
            state['cursor']+=1
            if result['skipped']:
                # A skip is an unfinished task, not an answered one.
                state.setdefault('skipped',[])
                if item_id not in state['skipped']:state['skipped'].append(item_id)
            elif item_id in state.get('skipped',[]):
                state['skipped']=[i for i in state['skipped'] if i!=item_id]
            if config.get('feedback')!='end' and (result['needsRetry'] or result['skipped']) and round_<2:
                state['queue'].insert(min(len(state['queue']),state['cursor']+3),{'itemId':item_id,'round':round_+1})
            self.db.execute('UPDATE lex_sessions SET state_json=?,version=version+1,updated_at=? WHERE id=?',(dump(state),now(),session_id))
            return self._answer_response(session_id,result,question=question)

    def _answer_response(self,session_id,result,duplicate=False,question=None):
        session=self.get(session_id)
        if session['config'].get('feedback')=='end' and session['status'] not in {'completed','completed_with_skips'}:
            result={'saved':True,'sequence':result.get('sequence')}
        elif question is not None:
            result=public_result(question,result,session_id)
        return {'session':session,'result':result,'duplicate':duplicate}

    def review_target_of(self,q):
        """The card this question reviews. Older snapshots predate the field (LEX-01)."""
        target=q.get('reviewTarget')
        if not isinstance(target,dict):
            from lexicon_exercise import review_target
            target=review_target(q['sourceRef'],q['type'],q.get('variantKey','default'))
        return target

    def _apply_srs(self,q,result,operation_id,ts,digest=''):
        from local_backend import source_card_id,calculate_sm2,_row_to_vocab,card_tombstone
        target=self.review_target_of(q)
        vocab_id=source_card_id(target['sourceRef'],target['promptType'],target['variantKey'])
        # A deleted card stays deleted: the answer is kept, but nothing is scheduled.
        if card_tombstone(self.db,vocab_id) is not None:
            result['srsConflict']='这张复习卡已删除；作答记录保留，未新建卡片。';return
        row=self.db.execute('SELECT * FROM vocab WHERE id=?',(vocab_id,)).fetchone()
        if row and (row['review_suspended'] or row['last_reviewed_at'] and datetime.fromisoformat(row['last_reviewed_at'])>datetime.fromisoformat(ts)):
            result['srsConflict']='已保留作答记录；此卡已暂停或已有较新复习，未覆盖调度。';return
        # Respect a deleted personal entry instead of reviving it during replay.
        personal=self.db.execute('SELECT deleted FROM lex_user_entries WHERE source_ref=?',(q['sourceRef'],)).fetchone()
        if personal and personal[0]:result['srsConflict']='条目已删除，保留作答但不新建卡片。';return
        before=_row_to_vocab(row) if row else {}
        if row is None:
            payload={'exercise':q,'headword':q['headword'],'examples':q.get('examples',[]),
                     'reviewTarget':target,'answerVersion':q.get('answerVersion',''),
                     'scoringVersion':q.get('scoringVersion',SCORING_VERSION)}
            self.db.execute('''INSERT INTO vocab(id,term,reading,meaning,note,course_id,sentence_id,source_text,tags,level,
               next_review_at,last_reviewed_at,created_at,updated_at,entry_kind,source_ref,prompt_type,variant_key,card_payload_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (vocab_id,q['headword'],q.get('reading',''),q.get('meaning',''),'','','','',dump([]),q.get('level',''),ts,'',ts,ts,q['kind'],target['sourceRef'],target['promptType'],target['variantKey'],dump(payload)))
            row=self.db.execute('SELECT * FROM vocab WHERE id=?',(vocab_id,)).fetchone()
        reps,interval,ease,stage,next_at=calculate_sm2(row['srs_repetitions'],row['srs_interval'],row['srs_ease'],result['suggestedGrade'],datetime.fromisoformat(ts))
        self.db.execute('UPDATE vocab SET srs_repetitions=?,srs_interval=?,srs_ease=?,srs_stage=?,mastered=?,srs_lapses=srs_lapses+?,next_review_at=?,last_reviewed_at=?,review_version=review_version+1,updated_at=? WHERE id=?',(reps,interval,ease,stage,int(stage>=3),int(result['suggestedGrade']=='again'),next_at,ts,ts,vocab_id))
        after=_row_to_vocab(self.db.execute('SELECT * FROM vocab WHERE id=?',(vocab_id,)).fetchone())
        self.db.execute('INSERT INTO lex_review_events(operation_id,vocab_id,before_json,after_json,created_at,request_digest) VALUES (?,?,?,?,?,?)',(operation_id,vocab_id,dump(before),dump(after),ts,digest))
        result.update({'srsApplied':True,'vocabId':vocab_id,'reviewTarget':target,'nextReviewAt':next_at,'reviewVersion':after.get('reviewVersion',0)})

    def _mistake(self,q,result,attempt_id,ts,round_):
        if round_>0:return  # Immediate repeats cannot erase the first error.
        bad=result['needsRetry'] or result['skipped']; clean=result['classification']=='correct'
        existing=self.db.execute('SELECT * FROM lex_mistakes WHERE source_ref=? AND exercise_type=?',(q['sourceRef'],q['type'])).fetchone()
        if not bad and not existing:return
        streak=0 if bad else (existing['clean_streak'] if existing else 0)+int(clean)
        self.db.execute('INSERT INTO lex_mistakes VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(source_ref,exercise_type) DO UPDATE SET wrong_count=lex_mistakes.wrong_count+?,clean_streak=excluded.clean_streak,resolved=excluded.resolved,last_attempt_id=excluded.last_attempt_id,updated_at=excluded.updated_at',(q['sourceRef'],q['type'],q['kind'],int(bad),streak,int(streak>=2),attempt_id,ts,int(bad)))

    def resume_skipped(self, session_id, payload):
        with self.lock,self.db:
            row,config,items,state=self._load(session_id)
            if row['status']!='active':raise ConflictError('练习已经结束。')
            requested=payload.get('itemIds')
            if not isinstance(requested,list) or not all(isinstance(i,str) for i in requested):
                raise ValueError('需要题目 ID 列表。')
            outstanding=set(state.get('skipped',[]))-self._answered_items(session_id)
            if any(i not in outstanding for i in requested):raise ConflictError('跳过题目状态已改变，请载入最新状态。')
            pending={t['itemId'] for t in state['queue'][state['cursor']:]}
            changed=False
            for item_id in dict.fromkeys(requested):
                if item_id in pending:continue
                next_round=1+max((t['round'] for t in state['queue'] if t['itemId']==item_id),default=-1)
                state['queue'].append({'itemId':item_id,'round':next_round});changed=True
            if changed:
                self.db.execute('UPDATE lex_sessions SET state_json=?,version=version+1,updated_at=? WHERE id=?',
                                (dump(state),now(),session_id))
            return self.get(session_id)

    def submit(self,session_id,payload=None):
        payload=payload or {}
        with self.lock,self.db:
            row,config,items,state=self._load(session_id)
            if row['status'] in {'completed','completed_with_skips'}:return self.report(session_id)
            if state['cursor']<len(state['queue']):raise ConflictError('还有未完成的题目，请继续或保存后退出。')
            skipped=[i for i in state.get('skipped',[]) if i not in self._answered_items(session_id)]
            if skipped and not payload.get('acceptSkipped'):
                # Ending with unfinished tasks is allowed, but it has to be chosen, not
                # reported as "all done" by default (§10.2).
                raise ConflictError(f'还有 {len(skipped)} 道题被跳过；确认结束请带 acceptSkipped，或先完成这些题。')
            if config.get('feedback')=='end':
                by_id={q['id']:q for q in items}
                for attempt in self.db.execute('SELECT * FROM lex_attempts WHERE session_id=? ORDER BY sequence,rowid',(session_id,)).fetchall():
                    result=json.loads(attempt['result_json'])
                    question=by_id[attempt['item_id']]
                    # A draft answer stays out of both: its answer key is unverified.
                    if result.get('draft') or result['skipped']:continue
                    if not result.get('firstAnswer',attempt['round']==0):continue
                    # Feedback, mistakes and scheduling all become visible at the same moment.
                    self._mistake(question,result,attempt['id'],attempt['created_at'],attempt['round'])
                    if config.get('review',True) and not result['skipped'] and not result.get('srsApplied'):
                        self._apply_srs(question,result,attempt['operation_id'],attempt['created_at'],str(attempt['request_digest'] or ''))
                        self.db.execute('UPDATE lex_attempts SET result_json=? WHERE id=?',(dump(result),attempt['id']))
            status='completed_with_skips' if skipped else 'completed'
            self.db.execute("UPDATE lex_sessions SET status=?,version=version+1,updated_at=? WHERE id=?",(status,now(),session_id))
            return self.report(session_id)

    def _answered_items(self,session_id):
        return {row[0] for row in self.db.execute(
            "SELECT item_id FROM lex_attempts WHERE session_id=? AND json_extract(result_json,'$.skipped')=0",(session_id,))}

    def _attempts(self,session_id):
        return [{'id':r['id'],'itemId':r['item_id'],'round':r['round'],'sourceRef':r['source_ref'],'kind':r['kind'],'type':r['exercise_type'],'answer':json.loads(r['answer_json']),'result':json.loads(r['result_json']),'createdAt':r['created_at'],'validity':r['validity']} for r in self.db.execute('SELECT * FROM lex_attempts WHERE session_id=? ORDER BY rowid',(session_id,))]

    def report(self,session_id):
        with self.lock:
            row,config,items,state=self._load(session_id)
            if row['status'] not in {'completed','completed_with_skips'}:raise ConflictError('完成并提交练习后可查看报告。')
            attempts=[a for a in self._attempts(session_id) if a.get('validity','valid')=='valid']
            history=self._attempts(session_id)
            # A skip is not an attempt, so the first real answer counts even when it
            # arrives in a later round; a wrong first answer is still the one that counts.
            answered=[]
            for attempt in attempts:
                if attempt['result']['skipped']:continue
                if any(a['itemId']==attempt['itemId'] for a in answered):continue
                answered.append(attempt)
            first=[a for a in attempts if a['round']==0]
            objective=[a for a in answered if a['result']['correct'] is not None]
            correct=sum(a['result']['classification']=='correct' for a in objective)
            skipped=[a for a in first if a['result']['skipped'] and a['itemId'] not in {b['itemId'] for b in answered}]
            return {'sessionId':session_id,'status':row['status'],
                    'summary':{'entries':len({a['sourceRef'] for a in answered}),
                               # `processed` is every task touched; `answered` excludes skips.
                               'processed':len(first),'answered':len(answered),
                               'objectiveCount':len(objective),'correct':correct,
                               'accuracy':round(100*correct/len(objective),1) if objective else None,
                               'assisted':sum(a['result']['classification']=='assisted' for a in answered),
                               'selfAssessed':sum(a['result']['classification']=='self_assessed' for a in answered),
                               'skipped':len(skipped),'remaining':len(skipped),
                               'complete':not skipped,
                               'retries':len(attempts)-len(answered)-len(skipped),
                               'withdrawn':sum(1 for a in history if a.get('validity')=='withdrawn'),
                               # Drafts are reported, never folded into the accuracy.
                               'draft':sum(1 for a in history if a.get('validity')=='draft'),
                               'elapsedMs':sum(a['result'].get('elapsedMs',0) for a in attempts)},
                    'items':[public_question(q,answers=True,scope=session_id) for q in items],'attempts':attempts}

    def _withheld_sessions(self):
        """Sessions whose results are not public yet: group feedback, not submitted."""
        return [row[0] for row in self.db.execute(
            "SELECT id FROM lex_sessions WHERE status='active' AND json_extract(config_json,'$.feedback')='end'")]

    def mistakes(self):
        with self.lock:
            hidden=self._withheld_sessions()
            placeholders=','.join('?' for _ in hidden) or "''"
            rows=self.db.execute(f'SELECT m.*,a.session_id,a.item_id,a.result_json FROM lex_mistakes m JOIN lex_attempts a ON a.id=m.last_attempt_id'
                                 f" WHERE a.session_id NOT IN ({placeholders}) AND a.validity='valid'"
                                 f' ORDER BY m.updated_at DESC',hidden).fetchall()
        return [{'sourceRef':r['source_ref'],'type':r['exercise_type'],'kind':r['kind'],'wrongCount':r['wrong_count'],'cleanStreak':r['clean_streak'],'resolved':bool(r['resolved']),'updatedAt':r['updated_at'],'sessionId':r['session_id'],'itemId':r['item_id'],'headword':json.loads(r['result_json']).get('headword','')} for r in rows]

    def stats(self):
        with self.lock:
            hidden=self._withheld_sessions()
            placeholders=','.join('?' for _ in hidden) or "''"
            # Only valid events. A withdrawn question's answers stay in the table and
            # are reportable as history, but they do not move the accuracy (§10.4).
            rows=self.db.execute(f'SELECT kind,exercise_type,created_at,result_json FROM lex_attempts'
                                 f" WHERE (json_extract(result_json,'$.firstAnswer')=1 OR (round=0 AND json_extract(result_json,'$.firstAnswer') IS NULL)) AND validity='valid' AND session_id NOT IN ({placeholders})",hidden).fetchall()
            withdrawn_count=self.db.execute("SELECT COUNT(*) FROM lex_attempts WHERE validity='withdrawn'").fetchone()[0]
            draft_count=self.db.execute("SELECT COUNT(*) FROM lex_attempts WHERE validity='draft'").fetchone()[0]
        groups={}; days={}
        for row in rows:
            result=json.loads(row['result_json']); key=row['kind']+':'+row['exercise_type']
            g=groups.setdefault(key,{'kind':row['kind'],'type':row['exercise_type'],'answered':0,'objectiveCount':0,'correct':0,'assisted':0})
            g['answered']+=1; g['objectiveCount']+=result['correct'] is not None; g['correct']+=result['classification']=='correct';g['assisted']+=result['classification']=='assisted'
            day=row['created_at'][:10]; days[day]=days.get(day,0)+1
        for g in groups.values():g['accuracy']=round(g['correct']/g['objectiveCount']*100,1) if g['objectiveCount'] else None
        return {'groups':list(groups.values()),'days':days,'totalAttempts':len(rows),
                'withdrawnAttempts':withdrawn_count,'draftAttempts':draft_count,
                'openFeedback':len(self.feedback_items('open')),
                'pendingCorrections':len(self.corrections()),
                'unresolved':sum(not m['resolved'] for m in self.mistakes())}

    # ---- question feedback, triage and withdrawal (LEX-15, §10.3) ----------

    RESOLUTIONS = {'confirmed','rejected','resolved'}

    def feedback(self,session_id,payload):
        message=str(payload.get('message','')).strip()
        if not message or len(message)>2000:raise ValueError('请填写 1–2000 字的问题说明。')
        with self.lock,self.db:
            _,_,items,_=self._load(session_id)
            question=next((q for q in items if q['id']==payload.get('itemId')),None)
            if question is None:raise KeyError('题目不存在。')
            key='lf_'+secrets.token_hex(12)
            # Keyed by what actually identifies the problem, so it stays traceable when
            # the same entry has several questions and several answer versions.
            self.db.execute(
                'INSERT INTO lex_question_feedback(id,session_id,item_id,message,status,created_at,'
                'source_ref,question_id,answer_version,exercise_type,variant_key)'
                ' VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                (key,session_id,question['id'],message,'open',now(),question['sourceRef'],question['id'],
                 str(question.get('answerVersion') or ''),question['type'],str(question.get('variantKey') or '')))
            return {'id':key,'status':'open','sourceRef':question['sourceRef'],
                    'exerciseType':question['type'],'answerVersion':question.get('answerVersion','')}

    def feedback_items(self,status=''):
        with self.lock:
            sql='SELECT * FROM lex_question_feedback'
            params=[]
            if status: sql+=' WHERE status=?'; params.append(status)
            rows=self.db.execute(sql+' ORDER BY created_at DESC LIMIT 500',params).fetchall()
        return [{'id':r['id'],'sessionId':r['session_id'],'itemId':r['item_id'],'message':r['message'],
                 'status':r['status'],'createdAt':r['created_at'],'sourceRef':r['source_ref'],
                 'questionId':r['question_id'],'answerVersion':r['answer_version'],
                 'exerciseType':r['exercise_type'],'variantKey':r['variant_key'],
                 'resolution':r['resolution'],'resolvedBy':r['resolved_by'],'resolvedAt':r['resolved_at'],
                 'revisionRef':r['revision_ref'],'note':r['note']} for r in rows]

    def resolve_feedback(self,feedback_id,payload):
        """Record a decision on a reported problem, and act on it.

        `confirmed` withdraws the question: new sessions stop serving it, the answers
        already given against it stop counting, and any review it drove gets a
        correction proposal rather than a silent replay (§10.3).
        """
        resolution=str(payload.get('resolution','')).strip()
        if resolution not in self.RESOLUTIONS:raise ValueError('处理结论必须是 confirmed / rejected / resolved。')
        reviewer=str(payload.get('resolvedBy','')).strip()
        if not reviewer:raise ValueError('请填写处理人。')
        note=str(payload.get('note',''))[:2000]
        with self.lock,self.db:
            row=self.db.execute('SELECT * FROM lex_question_feedback WHERE id=?',(feedback_id,)).fetchone()
            if row is None:raise KeyError('问题反馈不存在。')
            ts=now()
            status='resolved' if resolution!='confirmed' else 'confirmed'
            self.db.execute('UPDATE lex_question_feedback SET status=?,resolution=?,resolved_by=?,resolved_at=?,'
                            'revision_ref=?,note=? WHERE id=?',
                            (status,resolution,reviewer,ts,str(payload.get('revisionRef','')),note,feedback_id))
            outcome={'id':feedback_id,'status':status,'resolution':resolution,'resolvedAt':ts}
            if resolution=='confirmed':
                outcome.update(self._withdraw(row,reviewer,note,ts))
            return outcome

    def _withdraw(self,row,reviewer,reason,ts):
        source_ref=str(row['source_ref'] or ''); question_id=str(row['question_id'] or row['item_id'])
        answer_version=str(row['answer_version'] or '')
        self.db.execute(
            'INSERT INTO lex_withdrawn_questions(source_ref,question_id,exercise_type,answer_version,reason,'
            'feedback_id,withdrawn_by,withdrawn_at) VALUES (?,?,?,?,?,?,?,?)'
            ' ON CONFLICT(source_ref,question_id,answer_version) DO UPDATE SET reason=excluded.reason,'
            'withdrawn_by=excluded.withdrawn_by,withdrawn_at=excluded.withdrawn_at',
            (source_ref,question_id,str(row['exercise_type'] or ''),answer_version,
             reason or '答案或题面有实质错误',row['id'],reviewer,ts))
        # The attempts stay; they stop being evidence.
        affected=self.db.execute('SELECT * FROM lex_attempts WHERE item_id=?',(question_id,)).fetchall()
        self.db.execute("UPDATE lex_attempts SET validity='withdrawn' WHERE item_id=?",(question_id,))
        proposals=self._propose_corrections(affected,source_ref,question_id,ts)
        self._recount_mistakes(source_ref,str(row['exercise_type'] or ''))
        return {'withdrawn':{'sourceRef':source_ref,'questionId':question_id,'answerVersion':answer_version},
                'invalidatedAttempts':len(affected),'corrections':proposals}

    def _propose_corrections(self,attempts,source_ref,question_id,ts):
        """Describe the review each invalidated answer drove, without undoing it.

        Replaying the chain backwards would overwrite reviews the learner has done
        since. The proposal names what was affected and leaves the decision explicit.
        """
        proposals=[]
        for attempt in attempts:
            result=json.loads(attempt['result_json'])
            vocab_id=str(result.get('vocabId') or '')
            if not result.get('srsApplied') or not vocab_id: continue
            # Any path that moved the schedule counts, not only practice: a daily review
            # writes a receipt rather than a lex_review_events row, and missing it would
            # propose a rollback over work the learner has since done.
            events=self.db.execute(
                'SELECT COUNT(*) FROM lex_review_events WHERE vocab_id=? AND created_at>?',
                (vocab_id,attempt['created_at'])).fetchone()[0]
            receipts=self.db.execute(
                'SELECT COUNT(*) FROM vocab_review_receipts WHERE vocab_id=? AND created_at>?',
                (vocab_id,attempt['created_at'])).fetchone()[0]
            card=self.db.execute('SELECT last_reviewed_at FROM vocab WHERE id=?',(vocab_id,)).fetchone()
            moved=bool(card and str(card[0] or '')>str(attempt['created_at']))
            later=max(events+receipts,1 if moved else 0)
            event=self.db.execute('SELECT before_json FROM lex_review_events WHERE operation_id=?',
                                  (attempt['operation_id'],)).fetchone()
            proposal={'vocabId':vocab_id,'attemptId':attempt['id'],'reviewedAt':attempt['created_at'],
                      'laterEvents':later,
                      # No later events: the state before this answer can simply be restored.
                      # Later events exist: a compensating entry is the only honest option.
                      'action':'restore-previous-state' if not later else 'record-compensating-event',
                      'previousState':json.loads(event['before_json']) if event else None}
            self.db.execute('INSERT INTO lex_srs_corrections(vocab_id,source_ref,reason,proposal_json,created_at)'
                            ' VALUES (?,?,?,?,?)',
                            (vocab_id,source_ref,'question-withdrawn:'+question_id,dump(proposal),ts))
            proposals.append(proposal)
        return proposals

    def corrections(self,status='proposed'):
        with self.lock:
            rows=self.db.execute('SELECT * FROM lex_srs_corrections WHERE status=? ORDER BY id',(status,)).fetchall()
        return [{'id':r['id'],'vocabId':r['vocab_id'],'sourceRef':r['source_ref'],'reason':r['reason'],
                 'status':r['status'],'createdAt':r['created_at'],**json.loads(r['proposal_json'])} for r in rows]

    def withdrawn_questions(self):
        with self.lock:
            rows=self.db.execute('SELECT * FROM lex_withdrawn_questions').fetchall()
        return {str(r['question_id']) for r in rows}

    def _recount_mistakes(self,source_ref,exercise_type):
        """Rebuild one mistake row from the attempts that still count."""
        if not source_ref or not exercise_type: return
        rows=self.db.execute(
            "SELECT * FROM lex_attempts WHERE source_ref=? AND exercise_type=? AND round=0"
            " AND validity='valid' ORDER BY sequence,rowid",(source_ref,exercise_type)).fetchall()
        if not rows:
            self.db.execute('DELETE FROM lex_mistakes WHERE source_ref=? AND exercise_type=?',
                            (source_ref,exercise_type))
            return
        wrong=0; streak=0; last=rows[-1]
        for row in rows:
            result=json.loads(row['result_json'])
            bad=result.get('needsRetry') or result.get('skipped')
            if bad: wrong+=1; streak=0
            elif result.get('classification')=='correct': streak+=1
        self.db.execute('INSERT INTO lex_mistakes VALUES (?,?,?,?,?,?,?,?)'
                        ' ON CONFLICT(source_ref,exercise_type) DO UPDATE SET wrong_count=excluded.wrong_count,'
                        'clean_streak=excluded.clean_streak,resolved=excluded.resolved,'
                        'last_attempt_id=excluded.last_attempt_id,updated_at=excluded.updated_at',
                        (source_ref,exercise_type,last['kind'],wrong,streak,int(streak>=2 or wrong==0),
                         last['id'],now()))
