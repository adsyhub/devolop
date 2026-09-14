"""Extended lexicon API; called only after the existing security gate."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sqlite3
import threading
from urllib.parse import parse_qs,unquote
from dictionary_store import DictionaryStore
import lexicon_search
from dictionary_jobs import InstallJobs
from lexicon_index import LexiconIndex
from lexicon_learning import LexiconLearning
from lexicon_practice_store import PracticeStore,ConflictError
from lexicon_exercise import capabilities,source_ref,TYPES
from lexicon_store import PackQualityError


class LexiconServices:
    def __init__(self,store,lexicon):
        self.store=store;self.lexicon=lexicon
        self.dictionary=DictionaryStore(lexicon.root.parent/'assets/dictionary/jmdict.sqlite3')
        self.index=LexiconIndex(lexicon)
        self.learning=LexiconLearning(store,lexicon)
        self.practice=PracticeStore(store,lexicon,self.dictionary)
        self.jobs=InstallJobs(self.dictionary.nominal_path)

    @property
    def job(self):
        return self.jobs.status()

    def install_dictionary(self):
        """Start an install. Only an explicit request calls this: looking a word up
        never reaches the network (§9.4)."""
        from dictionary_build import download
        target=self.dictionary.nominal_path
        return self.jobs.start(lambda progress,cancelled:download(target,progress,cancelled))


def integer(value,default,minimum,maximum):
    try:result=int(value if value is not None else default)
    except (ValueError,TypeError):raise ValueError('分页或题量参数无效。')
    if not minimum<=result<=maximum:raise ValueError('分页或题量参数超出范围。')
    return result


class LexiconWorkspaceMixin:
    lexicon_services: LexiconServices

    def optional_learning_json(self):
        """Body for routes that only sometimes carry one; an empty request stays valid."""
        try:return self.read_learning_json()
        except ValueError:return {}

    def handle_lexicon_workspace(self,parsed):
        path=parsed.path
        prefixes=('/api/lexicon/','/api/dictionary/','/api/decks')
        if not path.startswith(prefixes):return False
        method=self.command;s=self.lexicon_services
        params={k:v[0] for k,v in parse_qs(parsed.query).items()}
        try:
            result=self._workspace_route(method,path,params,s)
            if result is NotImplemented:return False
            status=200
            if method=='POST' and path in {'/api/decks','/api/lexicon/sessions'}:status=201
            self.send_learning_json(result,status)
        except lexicon_search.CursorError as exc:self.send_learning_json({'error':str(exc),'code':'cursor-expired'},409)
        except PackQualityError as exc:self.send_learning_json({'error':str(exc)},422)
        except ConflictError as exc:self.send_learning_json({'error':str(exc),'code':'conflict'},409)
        except KeyError as exc:self.send_learning_json({'error':str(exc)},404)
        except (ValueError,TypeError) as exc:self.send_learning_json({'error':str(exc)},400)
        except sqlite3.IntegrityError:self.send_learning_json({'error':'数据已经更新，请重新载入。'},409)
        return True

    def _workspace_route(self,method,path,p,s):
        if method=='GET' and path=='/api/lexicon/search':
            return lexicon_search.search(s,p)
        if method=='GET' and path.startswith('/api/lexicon/entries/'):
            rest=unquote(path[len('/api/lexicon/entries/'):]);parts=rest.split('/')
            if len(parts)!=2:raise ValueError('entry reference must be <slug>/<entryId>')
            found=s.lexicon.get_entry(*parts)
            if not found:raise KeyError('条目不存在。')
            pack=s.lexicon.get_pack(parts[0]);found['capabilities']=capabilities(pack,found['entry'])
            ref=f"lex:{found['packId']}#{found['entry']['id']}"
            found['sourceRef']=ref;found['personal']=next((e for e in s.practice.user_entries() if e['sourceRef']==ref),None)
            found['contexts']=s.practice.contexts(ref)
            related=[]
            supp_details = {}
            supp_file = s.lexicon.root / parts[0] / 'learning-supplement.json'
            if supp_file.is_file():
                try:
                    supp_doc = json.loads(supp_file.read_text(encoding='utf-8'))
                    supp_details = supp_doc.get('confusableDetails', {})
                except Exception:
                    supp_details = {}
            current_key = found['entry'].get('entryKey')
            for item in found['entry'].get('grammar',{}).get('confusables',[]):
                reference=item.get('sourceRef') if isinstance(item,dict) else item
                if not isinstance(reference,str) or not reference.startswith('lex:') or '#' not in reference:continue
                pack_id,entry_id=reference[4:].split('#',1);related_pack=s.lexicon.find_pack(pack_id)
                if related_pack and not related_pack['quality']['blocked']:
                    related_entry=next((e for e in related_pack['entries'] if e['id']==entry_id),None)
                    if related_entry:
                        r_data={'sourceRef':reference,'packSlug':related_pack['slug'],'entryId':entry_id,'headword':related_entry['headword'],'gloss':related_entry.get('gloss',{})}
                        if isinstance(item, dict):
                            for k in ('relationType', 'contrast', 'scenario'):
                                if item.get(k): r_data[k] = item[k]
                        elif current_key and related_entry.get('entryKey'):
                            detail = supp_details.get(current_key, {}).get(related_entry['entryKey'])
                            if detail:
                                for k in ('relationType', 'contrast', 'scenario'):
                                    if detail.get(k): r_data[k] = detail[k]
                        related.append(r_data)
            found['related']=related
            return found
        if method=='GET' and path=='/api/dictionary/status':return {**s.dictionary.status(),'job':s.job}
        if method=='GET' and path=='/api/dictionary/install':return {'job':s.jobs.status()}
        if method=='POST' and path=='/api/dictionary/install':return {'job':s.install_dictionary()}
        if method=='POST' and path=='/api/dictionary/install/cancel':return {'job':s.jobs.cancel()}
        if method=='DELETE' and path=='/api/dictionary/install':return {'job':s.jobs.clear()}
        if method=='GET' and path.startswith('/api/dictionary/entries/'):
            reference=unquote(path[len('/api/dictionary/entries/'):])
            key,_,sense_key=reference.partition('/')
            entry=s.dictionary.get(key)
            if not entry:raise KeyError('词典条目不存在。')
            ref='dict:jmdict#'+key+('/'+sense_key if sense_key else '')
            saved=next((e for e in s.practice.user_entries() if e['sourceRef'] in {ref,'dict:jmdict#'+key}),None)
            selection=(saved or {}).get('selection') if isinstance((saved or {}).get('selection'),dict) else {}
            if sense_key and not selection:selection={'senseKeys':[sense_key]}
            return {'entry':entry,'sourceRef':ref,'personal':saved,
                    'contexts':s.practice.contexts(ref)+([] if ref=='dict:jmdict#'+key else s.practice.contexts('dict:jmdict#'+key)),
                    'options':s.dictionary.selection_options(entry),
                    # An old favourite carries no selection: it is "sense not yet chosen",
                    # not "the first sense" (§9.2.4).
                    'selection':s.dictionary.resolve_selection(entry,selection) if selection else
                                {'chosen':False,'resolved':False,'senses':[],'candidates':[],
                                 'missingSenseKeys':[],'dictionaryChanged':False,'writtenForm':'','reading':''}}
        if method=='GET' and path=='/api/lexicon/user-entries':return {'items':s.practice.user_entries(p.get('includeDeleted')=='1')}
        if method in {'PUT','POST'} and path=='/api/lexicon/user-entries':return {'item':s.practice.save_user_entry(self.read_learning_json())}
        if method=='GET' and path=='/api/lexicon/export':
            return s.practice.export_personal(include_learning=p.get('learning')=='1')
        if method=='POST' and path=='/api/lexicon/import':
            body=self.read_learning_json()
            if body.get('preview',True):return s.practice.preview_import(body)
            return s.practice.import_personal(body)
        if method=='POST' and path=='/api/lexicon/introduce':
            body=self.read_learning_json();refs=body.get('sourceRefs')
            if not isinstance(refs,list) or not refs or len(refs)>500:raise ValueError('请选择 1–500 个条目。')
            if any(not isinstance(r,str) for r in refs):raise ValueError('条目引用无效。')
            types=body.get('promptTypes') or ['recall']
            if not isinstance(types,list):raise ValueError('学习卡片方向无效。')
            found=list(s.practice.entries({'sourceRefs':refs}))
            missing=sorted(set(refs)-{source_ref(pack,entry) for pack,entry in found})
            result=s.learning.introduce(found,types)
            return {**result,'missing':missing}
        if method=='GET' and path=='/api/lexicon/today':return s.learning.today(p.get('deck',''))
        if method=='POST' and path=='/api/lexicon/today':
            body=self.read_learning_json();return s.learning.today(str(body.get('deck','')),introduce=True)
        if method=='GET' and path=='/api/decks':return {'decks':[s.learning.detail(d['id']) for d in s.store.list_decks()]}
        if method=='POST' and path=='/api/decks':
            body=self.read_learning_json();slugs=body.get('packSlugs') or [body.get('packSlug') or body.get('packId') or '']
            if not isinstance(slugs,list) or not slugs:raise ValueError('请选择内容包。')
            pack=s.lexicon.find_pack(slugs[0])
            if not pack:raise KeyError('内容包不存在。')
            if pack.get('quality',{}).get('blocked'):raise PackQualityError('内容包未通过质量审计。')
            deck=s.store.create_deck(body,pack)
            try:
                with s.store.atomic():
                    s.learning.save_settings(deck['id'],{**body,'packSlugs':slugs})
                    s.store.sync_deck_pack(deck['id'],s.learning.pack(deck['id']))
            except Exception:
                s.store.delete_deck(deck['id']);raise
            return {'deck':s.learning.detail(deck['id'])}
        match=re.fullmatch(r'/api/decks/(deck_[A-Za-z0-9_-]+)(/serve)?',path)
        if match:
            deck_id=match[1]
            if method=='GET' and not match[2]:return {'deck':s.learning.detail(deck_id)}
            if method=='POST' and match[2]:return s.learning.serve(deck_id)
            if method=='PATCH' and not match[2]:
                return {'deck':s.learning.update_plan(deck_id,self.read_learning_json())}
            if method=='DELETE' and not match[2]:s.store.delete_deck(deck_id);return {'ok':True}
        if method=='GET' and path=='/api/lexicon/exercise-types':return {'types':TYPES}
        if method=='GET' and path=='/api/lexicon/sessions':return {'sessions':s.practice.list_sessions()}
        if method=='POST' and path=='/api/lexicon/sessions':return {'session':s.practice.create(self.read_learning_json(),self.headers.get('X-Learning-Operation-Id',''))}
        if method=='GET' and path=='/api/lexicon/mistakes':return {'items':s.practice.mistakes()}
        if method=='GET' and path=='/api/lexicon/feedback':return {'items':s.practice.feedback_items(p.get('status','')),
                                                                   'corrections':s.practice.corrections()}
        match_feedback=re.fullmatch(r'/api/lexicon/feedback/(lf_[A-Za-z0-9_-]+)',path)
        if match_feedback and method=='POST':
            return {'feedback':s.practice.resolve_feedback(match_feedback[1],self.read_learning_json())}
        if method=='GET' and path=='/api/lexicon/stats':return s.practice.stats()
        match=re.fullmatch(r'/api/lexicon/sessions/(ls_[A-Za-z0-9_-]+)(?:/(answers|submit|report|reveal|offline|feedback|resume-skipped))?',path)
        if match:
            key,action=match.groups()
            if method=='GET' and action in {None,'offline'}:return {'session':s.practice.get(key,offline=action=='offline')}
            if method=='GET' and action=='report':return {'report':s.practice.report(key)}
            if method=='POST' and action=='answers':
                body=self.read_learning_json();return s.practice.answer(key,body,self.headers.get('X-Learning-Operation-Id') or body.get('operationId',''))
            if method=='POST' and action=='resume-skipped':return {'session':s.practice.resume_skipped(key,self.read_learning_json())}
            if method=='POST' and action=='submit':return {'report':s.practice.submit(key,self.optional_learning_json())}
            if method=='POST' and action=='reveal':
                body=self.read_learning_json();return s.practice.expose(key,body,self.headers.get('X-Learning-Operation-Id') or body.get('operationId',''))
            if method=='POST' and action=='feedback':return s.practice.feedback(key,self.read_learning_json())
        if method=='POST' and path=='/api/lexicon/sync':
            body=self.read_learning_json();operations=body.get('operations')
            if not isinstance(operations,list) or len(operations)>100:raise ValueError('一次最多同步 100 项。')
            results=[];blocked=set()
            for op in operations:
                session_id=op.get('sessionId','')
                if session_id in blocked:results.append({'id':op.get('id'),'status':'conflict','message':'此会话有前置冲突待处理。'});continue
                try:
                    if op.get('action')=='submit':r={'report':s.practice.submit(session_id,op.get('body',{}))}
                    elif op.get('action')=='resume-skipped':r={'session':s.practice.resume_skipped(session_id,op.get('body',{}))}
                    elif op.get('action')=='reveal':r=s.practice.expose(session_id,op.get('body',{}),op.get('id',''))
                    else:r=s.practice.answer(session_id,op.get('body',{}),op.get('id',''))
                    results.append({'id':op.get('id'),'status':'duplicate' if r.get('duplicate') else 'applied','result':r})
                except (ValueError,KeyError) as exc:
                    blocked.add(session_id);results.append({'id':op.get('id'),'status':'conflict' if isinstance(exc,ConflictError) else 'rejected','message':str(exc)})
            return {'results':results}
        return NotImplemented
