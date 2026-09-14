"""Version-bound learning projections, annotations and assessment workflows."""
from __future__ import annotations
import base64
import copy
import datetime as dt
import json
import random
import uuid
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
from .audit import iter_questions
from .constants import FORM_SPECS
from .errors import ContractError,SessionError
from .security import sanitize_paper_for_learner
from .util import canonical_json,digest_json,utc_now


def text_value(value):
    if isinstance(value,str):return value
    if isinstance(value,list):return ' '.join(text_value(v) for v in value)
    if isinstance(value,dict):return ' '.join(text_value(v) for k,v in value.items() if k in {'value','latex','alt','children','rows','contentAst','stemAst','options','materials'})
    return ''


def cursor_encode(value):return base64.urlsafe_b64encode(canonical_json(value).encode()).decode().rstrip('=')
def cursor_decode(value):
    try:return json.loads(base64.urlsafe_b64decode(value+'='*(-len(value)%4)))
    except Exception:raise ContractError('Invalid or expired cursor')


class WorkflowMixin:
    def index_version(self,version_id,paper):
        safe=sanitize_paper_for_learner(paper)
        for form,group,q in iter_questions(safe):
            row=self.connection.execute('SELECT id FROM question_versions WHERE paper_version_id=? AND question_id=?',(version_id,q['questionId'])).fetchone()
            metadata={**q,'questionVersionId':row['id'],'paperVersionId':version_id,'paperId':paper['paperId'],'paperTitle':paper['title'],'sourceSession':paper['session'],'formCode':form['formCode'],'groupCode':group['groupCode'],'materials':group.get('materials',[]),'delivery':q,'stableKey':q.get('localKey')}
            self.connection.execute('INSERT OR REPLACE INTO question_search VALUES (?,?,?,?,?,?,?,?,?)',(row['id'],q['questionId'],version_id,form['formCode'],FORM_SPECS[form['formCode']].language,q['answerSpec']['type'],text_value([q,group.get('materials',[])]).casefold(),canonical_json(metadata),q['questionId']))

    def rebuild_search(self):
        with self._transaction():
            self.connection.execute('DELETE FROM question_search')
            for row in self.connection.execute('SELECT id,payload_json FROM paper_versions').fetchall():self.index_version(row['id'],json.loads(row['payload_json']))

    def search_questions(self,*,query='',form_code=None,kind='ALL',topic=None,language=None,status=None,cursor=0,limit=50):
        if not isinstance(query,str) or len(query)>300 or type(limit) is not int or not 1<=limit<=200:raise ContractError('Invalid search parameters')
        if kind not in {'ALL','WRONG','BOOKMARKED','UNSEEN','DUE','NOTES','UNANSWERED'}:raise ContractError('Invalid collection')
        filters={'query':query,'form':form_code,'kind':kind,'topic':topic,'language':language,'status':status};key=digest_json(filters)
        where=["pv.status='PUBLISHED'","COALESCE(ds.state,'') NOT IN ('REVIEW_REQUIRED','SUSPENDED')","pv.version_number=(SELECT MAX(v.version_number) FROM paper_versions v WHERE v.paper_id=pv.paper_id AND v.status='PUBLISHED')"]
        if kind in {"BOOKMARKED","NOTES","WRONG"}:where.remove("COALESCE(ds.state,'') NOT IN ('REVIEW_REQUIRED','SUSPENDED')")
        args=[]
        for column,value in [('s.form_code',form_code),('s.language',language),('w.status',status)]:
            if value is not None:
                if not isinstance(value,str):raise ContractError('Invalid filter')
                where.append(column+'=?');args.append(value)
        if query:where.append("instr(s.search_text || COALESCE(lower(n.note_text),''),?)>0");args.append(query.casefold())
        if topic:where.append("EXISTS(SELECT 1 FROM json_each(json_extract(s.metadata_json,'$.topicTags')) WHERE value=?)");args.append(topic)
        conditions={'WRONG':'w.question_id IS NOT NULL','BOOKMARKED':'b.question_id IS NOT NULL','NOTES':"COALESCE(n.note_text,'')<>''",'UNSEEN':"NOT EXISTS(SELECT 1 FROM attempt_facts a WHERE a.question_id=s.question_id AND a.answered=1)",'UNANSWERED':"EXISTS(SELECT 1 FROM attempt_facts a WHERE a.question_id=s.question_id AND a.answered=0)",'DUE':"w.status<>'MASTERED' AND w.next_review_at IS NOT NULL AND w.next_review_at<=?"}
        if kind in conditions:where.append(conditions[kind])
        if kind=='DUE':args.append(utc_now())
        joined=' FROM question_search s JOIN paper_versions pv ON pv.id=s.paper_version_id LEFT JOIN paper_delivery_state ds ON ds.paper_version_id=pv.id LEFT JOIN bookmarks b ON b.question_id=s.question_id LEFT JOIN wrong_question_state w ON w.question_id=s.question_id LEFT JOIN question_notes n ON n.question_id=s.question_id WHERE '
        total=self.connection.execute('SELECT COUNT(*)'+joined+' AND '.join(where),args).fetchone()[0]
        offset=0
        if isinstance(cursor,str) and cursor.isdigit():cursor=int(cursor)
        if type(cursor) is int:
            if cursor<0:raise ContractError('Invalid cursor')
            offset=cursor
        elif isinstance(cursor,str):
            value=cursor_decode(cursor)
            if not isinstance(value,dict) or value.get('filters')!=key:raise ContractError('Cursor does not match search filters')
            where.append('s.question_id>?');args.append(value['after'])
        else:raise ContractError('Invalid cursor')
        rows=self.connection.execute('SELECT ds.state delivery_state,ds.note delivery_note,s.metadata_json,b.question_id bookmarked,b.created_at,w.status,w.wrong_count,w.last_answered_at,w.next_review_at,w.notes,n.note_text'+joined+' AND '.join(where)+' ORDER BY s.question_id LIMIT ? OFFSET ?',[*args,limit+1,offset]).fetchall()
        items=[]
        for row in rows[:limit]:
            item=json.loads(row['metadata_json']);item.update(bookmarked=bool(row['bookmarked']),note=row['note_text'] or '',status=row['status'],wrongCount=row['wrong_count'] or 0,lastAnsweredAt=row['last_answered_at'],nextReviewAt=row['next_review_at'],notes=row['notes'] or '',createdAt=row['created_at'],available=row['delivery_state'] not in {'SUSPENDED','REVIEW_REQUIRED'},deliveryNote=row['delivery_note']);
            if not item['available']:item={k:v for k,v in item.items() if k in {'questionId','questionVersionId','paperVersionId','paperId','paperTitle','sourceSession','formCode','localKey','printedLabel','bookmarked','note','status','wrongCount','lastAnsweredAt','nextReviewAt','notes','createdAt','available','deliveryNote'}}
            items.append(item)
        return {'questions':items,'total':total,'nextCursor':cursor_encode({'filters':key,'after':items[-1]['questionId']}) if len(rows)>limit else None}

    def _all_collection(self,kind):
        result=[];cursor=0
        while True:
            page=self.search_questions(kind=kind,cursor=cursor,limit=200);result.extend(page['questions']);cursor=page['nextCursor']
            if cursor is None:return result
    def get_wrong_questions(self):return self._all_collection('WRONG')
    def list_bookmarks(self):return self._all_collection('BOOKMARKED')

    def record_attempt_facts(self,session,paper,result,now):
        lookup={q['questionId']:(f,q) for f,_,q in iter_questions(paper)}
        for item in result['questions']:
            form,q=lookup[item['questionId']];pv=q.get('sourcePaperVersionId',session['paper_version_id'])
            version=self.connection.execute('SELECT id FROM question_versions WHERE paper_version_id=? AND question_id=?',(pv,q['questionId'])).fetchone()
            if not version:raise ContractError('Historical question version is missing')
            revealed=self.connection.execute("SELECT 1 FROM session_events WHERE practice_session_id=? AND event_type='REVEAL' AND json_extract(payload_json,'$.questionId')=?",(session['id'],q['questionId'])).fetchone()
            self.connection.execute('INSERT OR IGNORE INTO attempt_facts VALUES (?,?,?,?,?,?,?,?,?,?,?)',(session['id'],version['id'],q['questionId'],pv,form['formCode'],q['answerSpec']['type'],int(item['answered']),None if item['correct'] is None else int(item['correct']),int(bool(revealed)),str(result['scoringVersion']),now))
            frozen=self.connection.execute('SELECT 1 FROM session_review_content WHERE session_id=? AND question_version_id=?',(session['id'],version['id'])).fetchone()
            if not frozen:
                rows=self._latest_annotations(version['id'],as_of=now)
                self.connection.execute('INSERT INTO session_review_content VALUES (?,?,?)',(session['id'],version['id'],rows[0]['id'] if rows else None))
                for row in rows:
                    payload=json.loads(row['payload_json'])
                    self.connection.execute('INSERT INTO session_review_annotations VALUES (?,?,?,?,?)',
                        (session['id'],version['id'],payload['kind'],payload['language'],row['id']))

    def _latest_annotations(self,qvid,as_of=None):
        """这道题每个 kind/language 当前交付哪一版。

        人工那条轨（REVIEWED / WITHDRAWN）整体优先于机器审核，与修订号无关：机器
        候选不能仅凭序号更大就把人工已交付的版本挤掉（规范 §12.1）。机器审核过的
        解析只填人工没有覆盖的位置；人工一旦在这个位置留下版本，选择权就回到人工
        那一轨，撤回也照旧生效。"""
        return self.connection.execute("""SELECT * FROM (
            SELECT *,row_number() OVER(
                PARTITION BY json_extract(payload_json,'$.kind'),json_extract(payload_json,'$.language')
                ORDER BY CASE WHEN status IN ('REVIEWED','WITHDRAWN') THEN 0 ELSE 1 END, revision DESC) rank
            FROM explanation_revisions WHERE question_version_id=? AND status IN ('REVIEWED','WITHDRAWN','MACHINE_REVIEWED') AND created_at<=?
        ) WHERE rank=1 ORDER BY revision""",(qvid,as_of or utc_now())).fetchall()

    def rebuild_attempts(self):
        from .grading import grade_paper
        with self._transaction():
            for row in self.connection.execute("SELECT id FROM practice_sessions WHERE status='SUBMITTED' ORDER BY submitted_at,id").fetchall():
                session,paper=self._session_with_paper(row['id'])
                result=grade_paper(paper,{k:v['value'] for k,v in self._responses(row['id']).items()},selected_forms=json.loads(session['selected_forms_json']))
                self.record_attempt_facts(session,paper,result,session['submitted_at'])

    def learning_summary(self,*,form=None,start=None,end=None):
        clauses=['1=1'];args=[]
        for column,op,value in [('form_code','=',form),('submitted_at','>=',start),('submitted_at','<=',end)]:
            if value:clauses.append(column+op+'?');args.append(value)
        rows=self.connection.execute('WITH ranked AS (SELECT *,row_number() OVER(PARTITION BY question_id ORDER BY submitted_at,session_id) attempt_number FROM attempt_facts WHERE answered=1 AND answer_type<>\'ESSAY\') SELECT * FROM ranked WHERE '+' AND '.join(clauses),args).fetchall()
        untrusted={r[0] for r in self.connection.execute("SELECT paper_version_id FROM paper_delivery_state WHERE state IN ('REVIEW_REQUIRED','SUSPENDED')")}
        quality={'affectedAnsweredAttempts':sum(r['paper_version_id'] in untrusted for r in rows),'note':'来源待复核或停用的历史作答仍保留；其正确率不作为已核准内容的学习结论'}
        def metric(subset):return {'denominator':len(subset),'correct':sum(r['correct'] or 0 for r in subset),'accuracy':round(sum(r['correct'] or 0 for r in subset)/len(subset),4) if subset else None}
        return {'analyticsVersion':1,'contentQuality':quality,'uniqueQuestions':len({r['question_id'] for r in rows}),'answeredAttempts':len(rows),'firstUnaided':metric([r for r in rows if r['attempt_number']==1 and not r['revealed']]),'repeatUnaided':metric([r for r in rows if r['attempt_number']>1 and not r['revealed']]),'revealed':metric([r for r in rows if r['revealed']]),'unansweredExposures':self.connection.execute('SELECT COUNT(*) FROM attempt_facts WHERE answered=0 AND '+' AND '.join(clauses),args).fetchone()[0],'scope':'已提交的客观作答；首答按提交时间及会话 ID 排序；未答与记述独立统计'}

    def learning_calendar(self,timezone='Asia/Tokyo'):
        try:zone=ZoneInfo(timezone)
        except (ZoneInfoNotFoundError,ValueError):raise ContractError('Unknown learning timezone')
        days={}
        for row in self.connection.execute('SELECT submitted_at,answered FROM attempt_facts'):
            day=dt.datetime.fromisoformat(row['submitted_at'].replace('Z','+00:00')).astimezone(zone).date().isoformat();entry=days.setdefault(day,{'answeredAttempts':0,'unanswered':0,'due':0});entry['answeredAttempts' if row['answered'] else 'unanswered']+=1
        for row in self.connection.execute("SELECT next_review_at FROM wrong_question_state WHERE next_review_at IS NOT NULL AND status<>'MASTERED'"):
            day=dt.datetime.fromisoformat(row[0].replace('Z','+00:00')).astimezone(zone).date().isoformat();days.setdefault(day,{'answeredAttempts':0,'unanswered':0,'due':0})['due']+=1
        return {'timezone':timezone,'days':[{'date':day,**values} for day,values in sorted(days.items())]}

    def goals(self,config=None):
        if config is not None:
            if not isinstance(config,dict) or set(config)-{'newQuestions','reviewAttempts','timezone'}:raise ContractError('Invalid goals')
            for key in ['newQuestions','reviewAttempts']:
                if type(config.get(key)) is not int or not 0<=config[key]<=1000:raise ContractError('Goal must be 0 to 1000')
            try:ZoneInfo(config.get('timezone','Asia/Tokyo'))
            except (ZoneInfoNotFoundError,ValueError,TypeError):raise ContractError('Invalid timezone')
            config={**config,'timezone':config.get('timezone','Asia/Tokyo')}
            with self._transaction():self.connection.execute("INSERT INTO learning_goals VALUES ('default',?,?) ON CONFLICT(id) DO UPDATE SET config_json=excluded.config_json,updated_at=excluded.updated_at",(canonical_json(config),utc_now()))
        row=self.connection.execute("SELECT config_json FROM learning_goals WHERE id='default'").fetchone()
        return json.loads(row[0]) if row else {'newQuestions':10,'reviewAttempts':10,'timezone':'Asia/Tokyo'}

    def question_attempts(self,qid):
        self._require_question(qid)
        return [dict(row) for row in self.connection.execute('SELECT * FROM attempt_facts WHERE question_id=? ORDER BY submitted_at,session_id',(qid,))]

    def note_detail(self,qid):
        row=self.connection.execute('SELECT revision,note_text FROM note_revisions WHERE question_id=? ORDER BY revision DESC LIMIT 1',(qid,)).fetchone()
        return {'note':row['note_text'] if row else self.get_question_note(qid),'revision':row['revision'] if row else 0}

    def save_note_revision(self,qid,text,base_revision=None):
        self._require_question(qid)
        if not isinstance(text,str) or len(text)>10000:raise ContractError('Note must contain at most 10000 characters')
        with self._transaction():
            latest=self.note_detail(qid)
            if base_revision is not None and (type(base_revision) is not int or latest['revision']!=base_revision):raise SessionError('Note changed in another page')
            rev=latest['revision']+1;now=utc_now()
            self.connection.execute('INSERT INTO note_revisions VALUES (?,?,?,?)',(qid,rev,text,now))
            self.connection.execute('INSERT INTO question_notes VALUES (?,?,?,?) ON CONFLICT(question_id) DO UPDATE SET note_text=excluded.note_text,updated_at=excluded.updated_at',('nt_'+uuid.uuid4().hex,qid,text,now))
        return {'questionId':qid,'saved':True,'revision':rev}

    def save_explanation(self,qvid,payload,*,base_revision=0,status='DRAFT',reviewer=None,verification=None):
        """写一版详解。

        ``MACHINE_REVIEWED`` 不是一个可以由请求直接声称的状态：它必须带着服务端
        算出来的验证结论（``verification``），而且署名固定为机器身份。少了这一条，
        "机器审核通过"就退化成一个任何管理请求都能设的字段，和把 DRAFT 改名成
        REVIEWED 没有区别（规范 §12.1）。"""
        from .page_contract import validate_ast
        from .constants import MACHINE_REVIEWER
        if not self.connection.execute('SELECT 1 FROM question_versions WHERE id=?',(qvid,)).fetchone():raise KeyError(qvid)
        if status not in {'DRAFT','IN_REVIEW','REVIEWED','MACHINE_REVIEWED','WITHDRAWN'} or not isinstance(payload,dict):raise ContractError('Invalid explanation revision')
        if payload.get('kind') not in {'EXPLANATION','TRANSLATION'} or payload.get('language') not in {'ja','zh','en'} or validate_ast(payload.get('contentAst'),ref='explanation'):raise ContractError('Invalid explanation content')
        if status in {'REVIEWED','WITHDRAWN'} and (not isinstance(reviewer,str) or not reviewer.strip()):raise ContractError('Reviewer required')
        if status=='MACHINE_REVIEWED':
            if not isinstance(verification,dict) or verification.get('result')!='PASS':
                raise ContractError('Machine-reviewed explanations require a passing server-side verification')
            # 机器不借用人名，人也不冒用机器身份。署名由服务端设定。
            reviewer=MACHINE_REVIEWER
            payload={**payload,'reviewState':'MACHINE_REVIEWED','reviewGrade':'MACHINE_ATTESTED',
                     'verification':verification}
        elif verification is not None:
            raise ContractError('Verification evidence only applies to machine-reviewed explanations')
        with self._transaction():
            latest=self.connection.execute('SELECT COALESCE(MAX(revision),0) FROM explanation_revisions WHERE question_version_id=?',(qvid,)).fetchone()[0]
            if type(base_revision) is not int or base_revision!=latest:raise SessionError('Explanation revision conflict')
            rid='exp_'+uuid.uuid4().hex
            self.connection.execute('INSERT INTO explanation_revisions VALUES (?,?,?,?,?,?,?)',(rid,qvid,latest+1,status,canonical_json(payload),reviewer,utc_now()))
        return {'revisionId':rid,'revision':latest+1,'status':status}

    def review_content(self,sid,*,latest=False):
        session,paper=self._session_with_paper(sid)
        if session['status']!='SUBMITTED':raise SessionError('Submit before reading review content')
        result=[]
        for form,_,q in iter_questions(paper):
            if form['formCode'] not in json.loads(session['selected_forms_json']):continue
            pv=q.get('sourcePaperVersionId',session['paper_version_id'])
            qv=self.connection.execute('SELECT id FROM question_versions WHERE question_id=? AND paper_version_id=?',(q['questionId'],pv)).fetchone()[0]
            rows=self._latest_annotations(qv) if latest else self.connection.execute('SELECT e.* FROM session_review_annotations c JOIN explanation_revisions e ON c.revision_id=e.id WHERE c.session_id=? AND c.question_version_id=? ORDER BY e.revision',(sid,qv)).fetchall()
            if not rows:
                result.append({'questionId':q['questionId'],'questionVersionId':qv,'revisionId':None,'status':'UNAVAILABLE','content':None})
            for row in rows:
                payload=json.loads(row['payload_json'])
                withdrawn=self.connection.execute("SELECT 1 FROM explanation_revisions WHERE question_version_id=? AND status='WITHDRAWN' AND revision>=? AND json_extract(payload_json,'$.kind')=? AND json_extract(payload_json,'$.language')=?",(qv,row['revision'],payload['kind'],payload['language'])).fetchone()
                result.append({'questionId':q['questionId'],'questionVersionId':qv,'revisionId':row['id'],'kind':payload['kind'],'language':payload['language'],
                    'status':'WITHDRAWN' if withdrawn else row['status'],'content':payload if row['status'] in ('REVIEWED','MACHINE_REVIEWED') and not withdrawn else None})
        return {'items':result,'usingLatest':latest}

    def save_rubric(self,payload,reviewer):
        if not isinstance(payload,dict) or not isinstance(payload.get('name'),str) or not isinstance(payload.get('dimensions'),list) or not payload['dimensions'] or not isinstance(reviewer,str) or not reviewer.strip():raise ContractError('Rubric requires a name, dimensions and reviewer')
        for dimension in payload['dimensions']:
            if not isinstance(dimension,dict) or not isinstance(dimension.get('id'),str) or not isinstance(dimension.get('levels'),list) or not all(isinstance(x,str) for x in dimension['levels']):raise ContractError('Invalid rubric dimension')
        if len({d['id'] for d in payload['dimensions']})!=len(payload['dimensions']):raise ContractError('Duplicate rubric dimension')
        if payload.get('official') and not payload.get('sourceEvidence'):raise ContractError('Official rubric needs source evidence')
        rid='rub_'+uuid.uuid4().hex
        with self._transaction():self.connection.execute('INSERT INTO rubric_revisions VALUES (?,?,?,?)',(rid,canonical_json(payload),reviewer,utc_now()))
        return {'rubricRevisionId':rid,**payload}

    def assess_essay(self,sid,qid,payload,*,kind='SELF',reviewer=None,base_revision=0):
        session,paper=self._session_with_paper(sid)
        if session['status']!='SUBMITTED':raise SessionError('Submit before assessing an essay')
        question=next((q for f,_,q in iter_questions(paper) if q['questionId']==qid and f['formCode'] in json.loads(session['selected_forms_json'])),None)
        if not question or question['answerSpec']['type']!='ESSAY':raise ContractError('Essay is not in this session')
        if kind not in {'SELF','HUMAN'} or not isinstance(payload,dict):raise ContractError('Invalid assessment')
        if kind=='HUMAN' and (not isinstance(reviewer,str) or not reviewer.strip()):raise ContractError('Human reviewer is required')
        rubric=self.connection.execute('SELECT payload_json FROM rubric_revisions WHERE id=?',(payload.get('rubricRevisionId'),)).fetchone()
        if not rubric:raise ContractError('Reviewed rubric revision is required')
        dimensions=json.loads(rubric[0])['dimensions'];ratings=payload.get('ratings',{})
        if not isinstance(ratings,dict) or set(ratings)!={d['id'] for d in dimensions} or any(ratings[d['id']] not in d['levels'] for d in dimensions):raise ContractError('Ratings do not match the rubric')
        if not isinstance(payload.get('comment',''),str) or len(payload.get('comment',''))>20000:raise ContractError('Invalid assessment comment')
        response=self._responses(sid).get(qid,{}).get('value',{})
        if not response.get('text','').strip():raise ContractError('An empty essay cannot be assessed')
        payload={**payload,'responseHash':digest_json(response),'status':'SUBMITTED'}
        with self._transaction():
            revision=self.connection.execute('SELECT COALESCE(MAX(revision),0) FROM essay_reviews WHERE session_id=? AND question_id=? AND kind=?',(sid,qid,kind)).fetchone()[0]
            if type(base_revision) is not int or revision!=base_revision:raise SessionError('Essay assessment revision conflict')
            rid='ess_'+uuid.uuid4().hex
            self.connection.execute('INSERT INTO essay_reviews VALUES (?,?,?,?,?,?,?,?,?)',(rid,sid,qid,revision+1,kind,payload['rubricRevisionId'],canonical_json(payload),reviewer,utc_now()))
        return {'assessmentId':rid,'revision':revision+1,'kind':kind,'officialScore':False}

    def preview_practice(self,params):
        if not isinstance(params,dict):raise ContractError('Invalid practice conditions')
        ids=params.get('questionIds')
        seed=params.get('seed',uuid.uuid4().hex)
        if not isinstance(seed,(str,int)) or isinstance(seed,bool):raise ContractError('Invalid random seed')
        if ids is None:
            count=params.get('count',10)
            if type(count) is not int or not 1<=count<=200:raise ContractError('Choose 1 to 200 questions')
            ids=[];cursor=0
            while True:
                page=self.search_questions(query=params.get('query',''),form_code=params.get('form'),kind=params.get('kind','ALL'),topic=params.get('topic'),language=params.get('language'),status=params.get('status'),cursor=cursor,limit=200)
                ids.extend(q['questionId'] for q in page['questions'] if q.get('available',True));cursor=page['nextCursor']
                if cursor is None:break
            if params.get('randomOrder'):random.Random(seed).shuffle(ids)
            ids=ids[:count]
        return self.create_practice(ids,random_order=params.get('randomOrder',False),preview_only=True,seed=seed)

    def start_preview(self,pid,request_id):
        if not isinstance(request_id,str) or not 8<=len(request_id)<=100:raise ContractError('A start request ID is required')
        with self._transaction():
            receipt=self.connection.execute("SELECT payload_hash,result_json FROM action_receipts WHERE scope='start-preview' AND request_id=?",(request_id,)).fetchone()
            if receipt:
                if receipt['payload_hash']!=digest_json(pid):raise SessionError('Request ID used for a different preview')
                sid=json.loads(receipt['result_json'])['sessionId']
            else:
                row=self.connection.execute('SELECT * FROM practice_previews WHERE id=?',(pid,)).fetchone()
                if not row:raise KeyError(pid)
                if row['expires_at']<utc_now():raise SessionError('Practice preview expired')
                snapshot=json.loads(row['payload_json'])
                for source in snapshot['sourceVersions']:
                    version=self.connection.execute("SELECT pv.status,ds.state FROM paper_versions pv LEFT JOIN paper_delivery_state ds ON ds.paper_version_id=pv.id WHERE pv.id=?",(source['paperVersionId'],)).fetchone()
                    if not version or version['status']!='PUBLISHED' or version['state'] in {'SUSPENDED','REVIEW_REQUIRED'}:raise SessionError('A preview source is no longer available')
                sid=self._insert_session(snapshot['sourceVersions'][0]['paperVersionId'],[f['formCode'] for f in snapshot['forms']],'PRACTICE',{'paperSnapshot':snapshot,'previewId':pid})
                self.connection.execute("INSERT INTO action_receipts VALUES ('start-preview',?,?,?)",(request_id,digest_json(pid),canonical_json({'sessionId':sid})))
        return self.get_session(sid)

    def history_page(self,*,cursor=0,limit=50,status=None):
        if type(limit) is not int or not 1<=limit<=200:raise ContractError('Invalid history limit')
        where=[];args=[];offset=0
        if status:
            if status not in {'IN_PROGRESS','PAUSED','SUBMITTED','ABANDONED'}:raise ContractError('Invalid history status')
            where.append('ps.status=?');args.append(status)
        if isinstance(cursor,str) and cursor.isdigit():cursor=int(cursor)
        if type(cursor) is int:
            if cursor<0:raise ContractError('Invalid cursor')
            offset=cursor
        elif isinstance(cursor,str):
            data=cursor_decode(cursor)
            if data.get('status')!=status:raise ContractError('Cursor filter mismatch')
            where.append('(ps.created_at,ps.id)<(?,?)');args.extend([data['createdAt'],data['id']])
        else:raise ContractError('Invalid cursor')
        sql="SELECT ps.*,pv.paper_id,pv.version_number,json_extract(pv.payload_json,'$.title') title,r.result_json FROM practice_sessions ps JOIN paper_versions pv ON pv.id=ps.paper_version_id LEFT JOIN results r ON r.practice_session_id=ps.id"
        if where:sql+=' WHERE '+' AND '.join(where)
        rows=self.connection.execute(sql+' ORDER BY ps.created_at DESC,ps.id DESC LIMIT ? OFFSET ?',[*args,limit+1,offset]).fetchall()
        items=[]
        for r in rows[:limit]:
            result=json.loads(r['result_json']) if r['result_json'] else None
            items.append({'sessionId':r['id'],'paperId':r['paper_id'],'paperVersionId':r['paper_version_id'],'paperTitle':r['title'],'paperVersion':r['version_number'],'mode':r['mode'],'status':r['status'],'selectedForms':json.loads(r['selected_forms_json']),'createdAt':r['created_at'],'submittedAt':r['submitted_at'],'activeDurationSec':r['active_duration_sec'],'summary':{k:result.get(k) for k in ['scoringVersion','objectiveCorrect','objectiveTotal','objectiveAccuracy']} if result else None})
        return {'history':items,'nextCursor':cursor_encode({'status':status,'createdAt':rows[limit-1]['created_at'],'id':rows[limit-1]['id']}) if len(rows)>limit else None}

    def get_history(self,limit=50):return self.history_page(limit=limit)['history']

    def essay_assessments(self,sid):
        session,_=self._session_with_paper(sid)
        if session['status']!='SUBMITTED':raise SessionError('Submit before reading assessments')
        return [{'assessmentId':r['id'],'questionId':r['question_id'],'revision':r['revision'],'kind':r['kind'],'reviewer':r['reviewer'],'createdAt':r['created_at'],'assessment':json.loads(r['payload_json'])} for r in self.connection.execute('SELECT * FROM essay_reviews WHERE session_id=? ORDER BY created_at,id',(sid,))]

    def expire_sessions(self):
        rows=self.connection.execute("SELECT id FROM practice_sessions WHERE status='IN_PROGRESS' AND deadline IS NOT NULL AND deadline<=?",(utc_now(),)).fetchall()
        for row in rows:self.submit_session(row['id'],submission_type='EXPIRED_SUBMIT')
        return len(rows)

    def register_audio(self,source_id,asset_id,cues,reviewer):
        from .audio import probe_audio,validate_audio_cues
        from .assets import AssetStore
        from .review import ContentWorkspace
        _,manifest=ContentWorkspace(self.workspace_root,self).source(source_id)
        if not isinstance(reviewer,str) or not reviewer.strip():raise ContractError('Audio listening reviewer is required')
        if not any(f['role']=='AUDIO' and f['sha256']==asset_id for f in manifest['files']):raise ContractError('Audio must match the file bound to this source')
        store=AssetStore(self.media_dir);meta=probe_audio(store.get_path(asset_id))
        if validate_audio_cues(cues,meta['durationMs']):raise ContractError('Audio cue validation failed')
        baseline=self.connection.execute('SELECT structure_json FROM source_structure_revisions WHERE source_id=? ORDER BY revision DESC LIMIT 1',(source_id,)).fetchone()
        if not baseline:raise ContractError('Sign the source structure before mapping audio')
        structure=json.loads(baseline[0]);refs={x for values in structure['forms'].values() for x in values}
        if any(not isinstance(cue.get('questionRefs'),list) or not cue['questionRefs'] or not set(cue['questionRefs'])<=refs for cue in cues):raise ContractError('Cue questions are not in the signed source structure')
        # Create actual per-cue PCM segments. Future cue bytes are never exposed in MOCK.
        import io
        import soundfile as sf
        cues=copy.deepcopy(cues)
        with sf.SoundFile(store.get_path(asset_id)) as audio:
            for cue in cues:
                audio.seek(round(cue['startMs']*audio.samplerate/1000))
                samples=audio.read(round((cue['endMs']-cue['startMs'])*audio.samplerate/1000),dtype='float32',always_2d=True)
                output=io.BytesIO();sf.write(output,samples,audio.samplerate,format='WAV',subtype='PCM_16')
                segment=store.put_bytes(output.getvalue(),mime_type='audio/wav',ext='.wav')
                cue['assetId']=segment['assetId']
        track='aud_'+uuid.uuid4().hex
        with self._transaction():
            self.connection.execute("INSERT INTO audio_tracks VALUES (?,NULL,?,?,?,'REVIEWED',?,?,?)",(track,source_id,asset_id,meta['durationMs'],canonical_json(cues),reviewer,utc_now()))
            self.connection.execute('INSERT OR IGNORE INTO assets (id,sha256,mime_type,size_bytes,duration_ms,file_path,created_at) VALUES (?,?,?,?,?,?,?)',(asset_id,asset_id,'audio/'+store.get_path(asset_id).suffix.lstrip('.'),meta['sizeBytes'],meta['durationMs'],str(store.get_path(asset_id).relative_to(store.root)),utc_now()))
        return {'trackId':track,'durationMs':meta['durationMs'],'status':'REVIEWED'}

    def session_audio(self,sid):
        session,paper=self._session_with_paper(sid)
        selected=json.loads(session['selected_forms_json'])
        refs={q.get('answerRef') for f,_,q in iter_questions(paper) if f['formCode'] in selected}
        tracks=[]
        config=json.loads(self._state(sid)['config_json']);audio_state=config.get('audioState',{})
        for track in paper.get('audioTracks',[]):
            cues=[{k:v for k,v in cue.items() if k in {'cueId','startMs','endMs','questionRefs','replayPolicy','assetId'}} for cue in track['cues'] if refs.intersection(cue.get('questionRefs',[]))]
            if not cues:continue
            if session['mode']=='MOCK' and session['status']!='SUBMITTED':
                index=audio_state.get(track['trackId'],{}).get('index',0)
                if index>=len(cues):continue
                current=cues[index]
                if not current.get('assetId'):raise SessionError('Strict listening requires a reviewed audio segment')
                cue={**current,'startMs':0,'endMs':current['endMs']-current['startMs']}
                tracks.append({'trackId':track['trackId'],'assetId':current['assetId'],'durationMs':cue['endMs'],'cues':[cue],'strict':True,'playCount':audio_state.get(track['trackId'],{}).get('playCount',0),'cueIndex':index,'totalCues':len(cues),'positionMs':audio_state.get(track['trackId'],{}).get('positionMs',0)})
            else:tracks.append({'trackId':track['trackId'],'assetId':track['assetId'],'durationMs':track['durationMs'],'cues':cues,'strict':False})
        events=self.connection.execute('SELECT track_id,position_ms,action FROM session_audio_events WHERE session_id=? ORDER BY created_at DESC LIMIT 1',(sid,)).fetchone()
        return {'tracks':tracks,'progress':dict(events) if events else None}

    def save_audio_progress(self,sid,track_id,position,action):
        with self._transaction():
            tracks=self.session_audio(sid)['tracks'];track=next((t for t in tracks if t['trackId']==track_id),None)
            if not track or type(position) is not int or not 0<=position<=track['durationMs'] or action not in {'PLAY','RESUME','PAUSE','SEEK','ENDED','PROGRESS','ADVANCE'}:raise ContractError('Invalid audio progress')
            session,_=self._session_with_paper(sid);self._assert_writable(session)
            if track['strict']:
                config=json.loads(self._state(sid)['config_json']);current=config.setdefault('audioState',{}).setdefault(track_id,{'index':0,'playCount':0,'positionMs':0})
                if action=='SEEK':raise SessionError('Seeking is disabled in strict listening')
                if action=='PLAY':
                    if current['playCount']>=1:raise SessionError('This cue has already started; replay is not allowed')
                    current['playCount']+=1;current['startedAt']=utc_now()
                if action=='RESUME' and (current['playCount']!=1 or position<current.get('positionMs',0)):raise SessionError('Invalid strict audio resume')
                if action=='ADVANCE':
                    if not current.get('startedAt') or (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(current['startedAt'].replace('Z','+00:00'))).total_seconds()*1000<track['durationMs']:raise SessionError('Current audio cue time has not elapsed')
                    current.update(index=current['index']+1,playCount=0,positionMs=0);current.pop('startedAt',None)
                else:current['positionMs']=position
                self.connection.execute('UPDATE session_state SET config_json=? WHERE session_id=?',(canonical_json(config),sid))
            self.connection.execute('INSERT INTO session_audio_events VALUES (?,?,?,?,?,?)',(uuid.uuid4().hex,sid,track_id,action,position,utc_now()))
        return {'saved':True}
