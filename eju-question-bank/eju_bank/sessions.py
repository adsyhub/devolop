"""Transactional sessions, pinned paper versions and submission-only review."""
from __future__ import annotations

import copy
import datetime as dt
import json
import uuid
from contextlib import contextmanager
from typing import Any

from .audit import iter_questions
from .constants import FORM_SPECS
from .errors import ContractError, SessionError
from .grading import grade_paper, SCORING_VERSION
from .page_contract import validate_learner_response
from .security import sanitize_paper_for_learner
from .selection import validate_form_selection
from .util import canonical_json, digest_json, utc_now


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


def session_duration(codes: list[str]) -> int:
    groups = {}
    for code in codes:
        spec = FORM_SPECS[code]
        key = spec.shared_timing_group or code
        groups[key] = max(groups.get(key, 0), spec.duration_sec)
    return sum(groups.values())


class SessionStoreMixin:
    @contextmanager
    def _transaction(self):
        conn = self.connection
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _record_session_event(self, session_id, event_type, payload):
        self.connection.execute('INSERT INTO session_events VALUES (?, ?, ?, ?, ?)',
                                ('sev_' + uuid.uuid4().hex, session_id, event_type, canonical_json(payload), utc_now()))

    def _state(self, session_id):
        row = self.connection.execute('SELECT * FROM session_state WHERE session_id=?', (session_id,)).fetchone()
        return dict(row) if row else {'response_version': 0, 'progress_json': '{}', 'config_json': '{}'}

    def _session_with_paper(self, session_id):
        row = self.connection.execute('SELECT ps.*, pv.payload_json, pv.version_number FROM practice_sessions ps '
                                      'JOIN paper_versions pv ON pv.id=ps.paper_version_id WHERE ps.id=?', (session_id,)).fetchone()
        if row is None:
            raise KeyError(session_id)
        paper = json.loads(row['payload_json'])
        config = json.loads(self._state(session_id)['config_json'])
        if config.get('paperSnapshot'):
            paper = config['paperSnapshot']
        versions=[s['paperVersionId'] for s in paper.get('sourceVersions',[])] or [row['paper_version_id']]
        if any(self.content_withdrawn(v) for v in versions):raise SessionError('Source rights were withdrawn; historical metadata remains available but content delivery is blocked')
        ids = config.get('questionIds')
        if ids is not None:
            allowed = set(ids)
            for form in paper['forms']:
                for group in form['groups']:
                    group['questions'] = [q for q in group['questions'] if q['questionId'] in allowed]
                form['groups'] = [g for g in form['groups'] if g['questions']]
            paper['forms'] = [f for f in paper['forms'] if f['groups']]
            paper['questionCount'] = len(allowed)
        return row, paper

    def create_session(self, paper_id, selected_forms, *, mode='PRACTICE', question_ids=None, section_codes=None):
        if not isinstance(selected_forms, list) or not all(isinstance(c, str) for c in selected_forms):
            raise ContractError('selectedForms must be a list of form codes')
        with self._transaction():
            row = self.connection.execute("SELECT id,payload_json FROM paper_versions WHERE paper_id=? AND status='PUBLISHED' "
                                          'ORDER BY version_number DESC LIMIT 1', (paper_id,)).fetchone()
            if row is None:
                raise KeyError(paper_id)
            paper = json.loads(row['payload_json'])
            modes = paper.get('availableModes') or ['PRACTICE']
            if mode not in modes or (mode == 'MOCK' and paper.get('completeness') != 'COMPLETE'):
                raise ContractError('This paper does not support the requested mode')
            validate_form_selection(paper, selected_forms, mode=mode)
            delivery = self.connection.execute('SELECT state FROM paper_delivery_state WHERE paper_version_id=?', (row['id'],)).fetchone()
            if delivery and (delivery['state'] in {'SUSPENDED', 'REVIEW_REQUIRED'} or (mode == 'MOCK' and delivery['state'] != 'REVIEWED')):
                raise SessionError('Paper content requires review before this mode is available')
            if mode=='SECTION':
                if not isinstance(section_codes,list) or not section_codes or not all(isinstance(x,str) for x in section_codes) or len(set(section_codes))!=len(section_codes):raise ContractError('Select one or more section codes')
                sections=[x for x in paper.get('sections',[]) if x['sectionId'] in section_codes]
                if len(sections)!=len(section_codes) or any(x['formCode'] not in selected_forms for x in sections):raise ContractError('Selected section is unavailable')
                refs={ref for section in sections for ref in section['questionRefs']}
                question_ids=[q['questionId'] for f,_,q in iter_questions(paper) if f['formCode'] in selected_forms and (q.get('answerRef') or q['questionId']) in refs]
            elif section_codes is not None:raise ContractError('Section codes require SECTION mode')
            if question_ids is not None:
                if mode == 'MOCK' or not isinstance(question_ids, list) or not question_ids or not all(isinstance(q, str) for q in question_ids):
                    raise ContractError('Question selection requires a non-empty practice question list')
                available = {q['questionId'] for f, _, q in iter_questions(paper) if f['formCode'] in selected_forms}
                if len(set(question_ids)) != len(question_ids) or not set(question_ids) <= available:
                    raise ContractError('Selected questions are missing or duplicated')
            sid = self._insert_session(row['id'], selected_forms, mode, {'questionIds': question_ids,'sectionCodes':section_codes})
        return self.get_session(sid)

    def _insert_session(self, version_id, selected_forms, mode, config):
        sid, now = 'ses_' + uuid.uuid4().hex, utc_now()
        duration = session_duration(selected_forms) if mode == 'MOCK' else 0
        deadline = (parse_time(now) + dt.timedelta(seconds=duration)).isoformat().replace('+00:00', 'Z') if duration else None
        self.connection.execute("INSERT INTO practice_sessions (id,paper_version_id,mode,selected_forms_json,status,"
                                "active_duration_sec,deadline,last_active_at,created_at) VALUES (?,?,?,?,'IN_PROGRESS',0,?,?,?)",
                                (sid, version_id, mode, canonical_json(selected_forms), deadline, now, now))
        self.connection.execute('INSERT INTO session_state (session_id,config_json) VALUES (?,?)',
                                (sid, canonical_json(config)))
        self._record_session_event(sid, 'CREATE', {'mode': mode, 'forms': selected_forms, 'deadline': deadline})
        return sid

    def _assert_writable(self, session):
        if session['status'] != 'IN_PROGRESS':
            raise SessionError('Responses can only be saved while a session is in progress')
        if session['deadline'] and parse_time(utc_now()) >= parse_time(session['deadline']):
            raise SessionError('Session deadline has passed; responses can no longer be updated')

    def _touch(self, session, now):
        # Time between foreground heartbeats, capped so closing the browser is not study time.
        last=parse_time(session['last_active_at'] or now)
        credited=self.connection.execute("SELECT value FROM library_metadata WHERE key='last-active-credit'").fetchone()
        if credited:last=max(last,parse_time(credited[0]))
        elapsed = max(0, min(60, (parse_time(now) - last).total_seconds()))
        self.connection.execute("INSERT OR REPLACE INTO library_metadata VALUES ('last-active-credit',?)",(now,))
        self.connection.execute('UPDATE practice_sessions SET active_duration_sec=active_duration_sec+?,last_active_at=? WHERE id=?',
                                (int(elapsed), now, session['id']))

    def record_response(self, session_id, question_id, response):
        result = self.record_responses_batch(session_id, [{'questionId': question_id, 'response': response}])
        return {**result, 'questionId': question_id}

    def record_responses_batch(self, session_id, items, *, expected_version=None, request_id=None):
        if not isinstance(items, list) or len(items) > 500:
            raise ContractError('items must be an array of at most 500 responses')
        if expected_version is not None and (type(expected_version) is not int or expected_version < 0):
            raise ContractError('expectedVersion must be a nonnegative integer')
        if request_id is not None and (not isinstance(request_id, str) or not 1 <= len(request_id) <= 100):
            raise ContractError('Invalid requestId')
        payload_hash = digest_json({'items': items, 'expectedVersion': expected_version})
        with self._transaction():
            session, paper = self._session_with_paper(session_id)
            if request_id:
                receipt = self.connection.execute('SELECT * FROM save_receipts WHERE session_id=? AND request_id=?', (session_id, request_id)).fetchone()
                if receipt:
                    if receipt['payload_hash'] != payload_hash:
                        raise SessionError('requestId already used for different answers')
                    return json.loads(receipt['result_json'])
            self._assert_writable(session)
            version = self._state(session_id)['response_version']
            if expected_version is not None and expected_version != version:
                raise SessionError('Answer version conflict; reload the session before saving')
            selected = set(json.loads(session['selected_forms_json']))
            questions = {q['questionId']: q for f, _, q in iter_questions(paper) if f['formCode'] in selected}
            seen = set()
            for item in items:
                if not isinstance(item, dict) or not isinstance(item.get('questionId'), str):
                    raise ContractError('Every response needs questionId and response')
                qid = item['questionId']
                if qid not in questions or qid in seen:
                    raise SessionError('Question is missing, duplicated, or outside this session')
                seen.add(qid)
                validate_learner_response(questions[qid], item.get('response'))
            now = utc_now()
            for item in items:
                self.connection.execute('INSERT INTO responses VALUES (?,?,?,?) ON CONFLICT(practice_session_id,question_id) '
                                        'DO UPDATE SET response_json=excluded.response_json,updated_at=excluded.updated_at',
                                        (session_id, item['questionId'], canonical_json(item['response']), now))
            version += int(bool(items))
            self.connection.execute('INSERT INTO session_state (session_id,response_version) VALUES (?,?) '
                                    'ON CONFLICT(session_id) DO UPDATE SET response_version=excluded.response_version', (session_id, version))
            self._touch(session, now)
            if items:
                self._record_session_event(session_id, 'BATCH_ANSWER', {'items': items, 'version': version})
            result = {'sessionId': session_id, 'saved': len(items), 'savedAt': now, 'responseVersion': version}
            if request_id:
                self.connection.execute('INSERT INTO save_receipts VALUES (?,?,?,?)', (session_id, request_id, payload_hash, canonical_json(result)))
            return result

    def save_progress(self, session_id, progress):
        if not isinstance(progress, dict) or len(canonical_json(progress)) > 20000:
            raise ContractError('Invalid progress object')
        allowed = {'currentQuestionId', 'flaggedQuestionIds', 'viewMode','expectedProgressVersion'}
        if set(progress) - allowed:
            raise ContractError('Unsupported progress fields')
        with self._transaction():
            session, paper = self._session_with_paper(session_id)
            self._assert_writable(session)
            state=self._state(session_id)
            expected=progress.get('expectedProgressVersion')
            if expected is not None and (type(expected) is not int or expected!=state.get('progress_version',0)): raise SessionError('Progress version conflict')
            progress={k:v for k,v in progress.items() if k!='expectedProgressVersion'}
            ids = {q['questionId'] for f, _, q in iter_questions(paper) if f['formCode'] in json.loads(session['selected_forms_json'])}
            if progress.get('currentQuestionId') is not None and progress['currentQuestionId'] not in ids:
                raise ContractError('Unknown current question')
            flags = progress.get('flaggedQuestionIds', [])
            if not isinstance(flags, list) or not all(isinstance(q, str) and q in ids for q in flags):
                raise ContractError('Invalid question flags')
            if progress.get('viewMode', 'ALL') not in {'ALL', 'SINGLE', 'UNANSWERED', 'FLAGGED'}:
                raise ContractError('Invalid workspace view')
            self.connection.execute('INSERT INTO session_state (session_id,progress_json) VALUES (?,?) '
                                    'ON CONFLICT(session_id) DO UPDATE SET progress_json=excluded.progress_json,progress_version=session_state.progress_version+1', (session_id, canonical_json(progress)))
            self._touch(session, utc_now())
        return {'saved': True,'progressVersion':self._state(session_id).get('progress_version',0)}

    def _transition(self, session_id, status):
        with self._transaction():
            session, _ = self._session_with_paper(session_id)
            if status == 'PAUSED' and session['mode'] == 'MOCK':
                raise SessionError('MOCK mode cannot be paused')
            accepted = {'PAUSED': {'IN_PROGRESS'}, 'IN_PROGRESS': {'PAUSED'}, 'ABANDONED': {'IN_PROGRESS', 'PAUSED'}}
            if session['status'] not in accepted[status]:
                raise SessionError('Invalid session state transition')
            now = utc_now()
            if session['status'] == 'IN_PROGRESS':
                self._touch(session, now)
            self.connection.execute('UPDATE practice_sessions SET status=?,paused_at=?,last_active_at=? WHERE id=?',
                                    (status, now if status == 'PAUSED' else None, now, session_id))
            self._record_session_event(session_id, {'PAUSED': 'PAUSE', 'IN_PROGRESS': 'RESUME', 'ABANDONED': 'ABANDON'}[status], {})
        return self.get_session(session_id)

    def pause_session(self, session_id):
        return self._transition(session_id, 'PAUSED')

    def resume_session(self, session_id):
        return self._transition(session_id, 'IN_PROGRESS')

    def abandon_session(self, session_id):
        return self._transition(session_id, 'ABANDONED')

    def submit_session(self, session_id, *, expected_response_version=None, submission_type=None):
        with self._transaction():
            session, paper = self._session_with_paper(session_id)
            existing = self.connection.execute('SELECT result_json FROM results WHERE practice_session_id=?', (session_id,)).fetchone()
            if existing:
                return json.loads(existing['result_json'])
            if session['status'] not in {'IN_PROGRESS', 'PAUSED'}:
                raise SessionError('This session cannot be submitted')
            state = self._state(session_id)
            version = state['response_version']
            if expected_response_version is not None and (type(expected_response_version) is not int or version != expected_response_version):
                raise SessionError('Response version conflict during submission')

            is_expired = bool(session['deadline'] and parse_time(utc_now()) >= parse_time(session['deadline']))
            sub_type = submission_type or ('EXPIRED_SUBMIT' if is_expired else 'NORMAL')

            responses = self._responses(session_id)
            result = grade_paper(paper, {k: v['value'] for k, v in responses.items()}, selected_forms=json.loads(session['selected_forms_json']))
            result['submissionType'] = sub_type
            result['responseVersion'] = version
            if is_expired:
                result['deadline'] = session['deadline']
            now = utc_now()
            self.connection.execute('INSERT INTO results VALUES (?,?,?)', (session_id, canonical_json(result), now))
            if session['status'] == 'IN_PROGRESS':
                self._touch(session, now)
            self.connection.execute("UPDATE practice_sessions SET status='SUBMITTED',submitted_at=? WHERE id=?", (now, session_id))
            self.record_attempt_facts(session,paper,result,now)
            for item in result['questions']:
                previous=self.connection.execute('SELECT status FROM wrong_question_state WHERE question_id=?',(item['questionId'],)).fetchone()
                if item['answered'] and item['correct'] is not None:
                    new='NEW_WRONG' if item['correct'] is False else 'REVIEWING' if previous else None
                    if new:self.connection.execute('INSERT INTO review_events VALUES (?,?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,item['questionId'],previous['status'] if previous else None,new,None,None,'Submitted attempt',session_id,now))
                if item['answered'] and item['correct'] is False:
                    self.connection.execute("INSERT INTO wrong_question_state (question_id,status,wrong_count,last_answered_at) "
                                            "VALUES (?,'NEW_WRONG',1,?) ON CONFLICT(question_id) DO UPDATE SET "
                                            "status='NEW_WRONG',wrong_count=wrong_count+1,last_answered_at=excluded.last_answered_at",
                                            (item['questionId'], now))
                elif item['correct'] is True:
                    self.connection.execute("UPDATE wrong_question_state SET status='REVIEWING',last_answered_at=? WHERE question_id=?",
                                            (now, item['questionId']))
            self._record_session_event(session_id, 'SUBMIT', {
                'scoringVersion': SCORING_VERSION,
                'submissionType': sub_type,
                'deadline': session['deadline'],
                'responseVersion': version,
            })
            return result

    def _responses(self, session_id):
        return {r['question_id']: {'value': json.loads(r['response_json']), 'updatedAt': r['updated_at']}
                for r in self.connection.execute('SELECT * FROM responses WHERE practice_session_id=?', (session_id,)).fetchall()}

    def get_session(self, session_id):
        row, paper = self._session_with_paper(session_id)
        if row['status'] == 'IN_PROGRESS' and row['deadline'] and parse_time(utc_now()) >= parse_time(row['deadline']):
            self.submit_session(session_id, submission_type='EXPIRED_SUBMIT')
            row, paper = self._session_with_paper(session_id)
        state = self._state(session_id)
        return {'sessionId': row['id'], 'paperId': paper['paperId'], 'paperVersionId': row['paper_version_id'],
                'paperVersion': row['version_number'], 'paperTitle': paper['title'], 'status': row['status'],
                'mode': row['mode'], 'deadline': row['deadline'], 'serverTime': utc_now(),
                'durationSec': session_duration(json.loads(row['selected_forms_json'])) if row['mode'] == 'MOCK' else 0,
                'activeDurationSec': row['active_duration_sec'], 'pausedAt': row['paused_at'],
                'selectedForms': json.loads(row['selected_forms_json']), 'responses': self._responses(session_id),
                'responseVersion': state['response_version'], 'progressVersion':state.get('progress_version',0), 'progress': json.loads(state['progress_json'])}

    def get_session_paper(self, session_id):
        session, paper = self._session_with_paper(session_id)
        selected = json.loads(session['selected_forms_json'])
        paper['forms'] = [f for f in paper['forms'] if f['formCode'] in selected]
        paper['questionCount'] = sum(1 for _ in iter_questions(paper))
        return sanitize_paper_for_learner(paper)

    def session_outline(self,session_id):
        paper=self.get_session_paper(session_id)
        for form in paper['forms']:
            for group in form['groups']:
                group['questions']=[{k:q[k] for k in ['questionId','printedLabel','localKey','answerSpec'] if k in q} for q in group['questions']]
        return {'paper':paper}

    def session_questions(self,session_id,*,cursor=0,limit=50):
        from .workflows import cursor_encode,cursor_decode
        if type(limit) is not int or not 1<=limit<=100:raise ContractError('Question page limit must be 1 to 100')
        if cursor in (0,'0'):offset=0
        else:
            if not isinstance(cursor,str):raise ContractError('Invalid question cursor')
            value=cursor_decode(cursor)
            if not isinstance(value,dict) or value.get('session')!=session_id or type(value.get('offset')) is not int or value['offset']<0:raise ContractError('Cursor belongs to a different session')
            offset=value['offset']
        paper=self.get_session_paper(session_id)
        items=[{'formCode':f['formCode'],'groupCode':g['groupCode'],'question':q} for f,g,q in iter_questions(paper)]
        return {'questions':items[offset:offset+limit],'total':len(items),'nextCursor':cursor_encode({'session':session_id,'offset':offset+limit}) if offset+limit<len(items) else None}

    def get_result(self, session_id):
        session, paper = self._session_with_paper(session_id)
        if session['status'] != 'SUBMITTED':
            raise SessionError('Submit the session before viewing answers')
        stored = self.connection.execute('SELECT result_json FROM results WHERE practice_session_id=?', (session_id,)).fetchone()
        original = json.loads(stored['result_json'])
        responses = {k: v['value'] for k, v in self._responses(session_id).items()}
        result = grade_paper(paper, responses, selected_forms=json.loads(session['selected_forms_json']))
        result.update({'sessionId': session_id, 'paperId': paper['paperId'], 'paperVersionId': session['paper_version_id'],
                       'paperTitle': paper['title'], 'paperVersion': session['version_number'],
                       'activeDurationSec': session['active_duration_sec'], 'submittedAt': session['submitted_at'],
                       'submissionType': original.get('submissionType', 'NORMAL')})
        if original.get('scoringVersion', 1) != SCORING_VERSION:
            result['previousScoringVersion'] = original.get('scoringVersion', 1)
            result['originalSummary'] = {k: original.get(k) for k in ['objectiveTotal', 'objectiveCorrect', 'objectiveAccuracy']}
        lookup = {q['questionId']: (f, g, q) for f, g, q in iter_questions(paper)}
        for item in result['questions']:
            _, group, q = lookup[item['questionId']]
            item.update({'question': copy.deepcopy(q), 'materials': copy.deepcopy(group.get('materials', [])),
                         'response': responses.get(item['questionId'])})
        return result
