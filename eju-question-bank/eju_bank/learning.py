"""Question search and collections built from published, pinned source versions."""
from __future__ import annotations
import copy
import datetime as dt
import json
import random
import uuid
from .audit import iter_questions
from .constants import FORM_SPECS
from .errors import ContractError, SessionError
from .security import sanitize_paper_for_learner
from .util import canonical_json, utc_now


class LearningStoreMixin:
    def _require_question(self, question_id):
        if not self.connection.execute('SELECT 1 FROM questions WHERE id=?', (question_id,)).fetchone():
            raise KeyError(question_id)

    def _available_content(self):
        rows = self.connection.execute("SELECT pv.* FROM paper_versions pv LEFT JOIN paper_delivery_state ds ON ds.paper_version_id=pv.id "
                                      "WHERE pv.status='PUBLISHED' AND COALESCE(ds.state,'') NOT IN ('SUSPENDED','REVIEW_REQUIRED') "
                                      "AND pv.version_number=(SELECT MAX(version_number) FROM paper_versions WHERE paper_id=pv.paper_id AND status='PUBLISHED') "
                                      'ORDER BY pv.paper_id').fetchall()
        return [(r, json.loads(r['payload_json'])) for r in rows]

    def create_practice(self, question_ids, *, random_order=False, preview_only=False, seed=None):
        if not isinstance(question_ids, list) or not question_ids or len(question_ids) > 200 or not all(isinstance(q, str) for q in question_ids) or len(set(question_ids)) != len(question_ids):
            raise ContractError('Choose 1 to 200 unique questions')
        if type(random_order) is not bool:
            raise ContractError('randomOrder must be boolean')
        requested, found = set(question_ids), set()
        forms, sources = [], []
        with self._transaction():
            for version, paper in self._available_content():
                source_forms = []
                for form in paper['forms']:
                    groups = []
                    for group in form['groups']:
                        chosen = {q['questionId'] for q in group['questions'] if q['questionId'] in requested - found}
                        if not chosen: continue
                        if 'PRACTICE' not in paper.get('availableModes', ['PRACTICE']):
                            raise SessionError('Source paper does not allow practice')
                        # Shared materials and explicitly atomic groups are not split.
                        expanded = set(chosen)
                        while True:
                            refs = {ref for q in group['questions'] if q['questionId'] in expanded for ref in q.get('materialRefs', [])}
                            related = {q['questionId'] for q in group['questions'] if group.get('atomic') or refs.intersection(q.get('materialRefs', []))}
                            before = len(expanded); expanded |= related
                            if len(expanded) == before: break
                        copied = copy.deepcopy(group)
                        copied['groupCode'] = version['id'] + '/' + copied['groupCode']
                        copied['questions'] = [q for q in copied['questions'] if q['questionId'] in expanded]
                        for q in copied['questions']:
                            q['sourcePaperId'] = paper['paperId']; q['sourcePaperVersionId'] = version['id']; q['sourceSession'] = paper['session']
                        found |= expanded
                        groups.append(copied)
                    if groups:
                        source_forms.append({**copy.deepcopy(form), 'groups': groups})
                if source_forms:
                    forms.extend(source_forms)
                    sources.append({'paperId': paper['paperId'], 'paperVersionId': version['id'], 'session': paper['session']})
            if not requested <= found:
                raise SessionError('Some selected questions are unavailable or require content review')
            if len(found)>200: raise ContractError("Shared material expansion exceeds the 200 question limit")
            merged = {}
            for form in forms:
                if form['formCode'] not in merged: merged[form['formCode']] = form
                else: merged[form['formCode']]['groups'].extend(form['groups'])
            forms = list(merged.values())
            if random_order:
                for form in forms: random.Random(seed).shuffle(form['groups'])
            snapshot = {'paperId': sources[0]['paperId'], 'title': '专项练习', 'session': ' / '.join(dict.fromkeys(s['session'] for s in sources)),
                        'completeness': 'PARTIAL', 'availableModes': ['PRACTICE'], 'forms': forms, 'questionCount': len(found), 'sourceVersions': sources}
            if preview_only:
                pid='pre_'+uuid.uuid4().hex;expires=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=30)).isoformat().replace('+00:00','Z')
                self.connection.execute('INSERT INTO practice_previews VALUES (?,?,?,?)',(pid,canonical_json(snapshot),utc_now(),expires))
                return {'previewId':pid,'requestedCount':len(requested),'actualCount':len(found),'expandedCount':len(found-requested),'seed':seed,'expiresAt':expires,'paper':sanitize_paper_for_learner(snapshot),'expansionReason':'共享材料或不可拆分题组' if found-requested else None}
            sid = self._insert_session(sources[0]['paperVersionId'], list(merged), 'PRACTICE', {'paperSnapshot': snapshot})
        return self.get_session(sid)

    def schedule_review(self, question_id, days, *, notes=None):
        if type(days) is not int or not 0 <= days <= 365:
            raise ContractError('Review interval must be 0 to 365 days')
        if notes is not None and (not isinstance(notes, str) or len(notes) > 10000):
            raise ContractError('Invalid mistake notes')
        due = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).isoformat().replace('+00:00', 'Z')
        with self._transaction():
            if not self.connection.execute('SELECT 1 FROM wrong_question_state WHERE question_id=?', (question_id,)).fetchone(): raise KeyError(question_id)
            old=self.connection.execute('SELECT status FROM wrong_question_state WHERE question_id=?',(question_id,)).fetchone()[0]
            self.connection.execute('INSERT INTO review_events VALUES (?,?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,question_id,old,'RETRY_DUE',due,days,notes,None,utc_now()))
            self.connection.execute("UPDATE wrong_question_state SET next_review_at=?,status='RETRY_DUE',notes=COALESCE(?,notes) WHERE question_id=?", (due, notes, question_id))
        return {'questionId': question_id, 'nextReviewAt': due}

    def report_content_issue(
        self,
        question_id: str,
        description: str,
        issue_type: str = "OTHER",
        *,
        paper_version_id: str | None = None,
        question_version_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(description, str) or not 5 <= len(description.strip()) <= 5000:
            raise ContractError("Issue description must be between 5 and 5000 characters")
        if issue_type not in {"TEXT", "ANSWER", "FIGURE", "AUDIO", "OTHER"}:
            raise ContractError(f"Invalid issueType: {issue_type}")
        self._require_question(question_id)

        if session_id:
            session,paper=self._session_with_paper(session_id)
            selected=json.loads(session['selected_forms_json'])
            question=next((q for f,_,q in iter_questions(paper) if q['questionId']==question_id and f['formCode'] in selected),None)
            if not question:raise ContractError('Question is not part of the selected session')
            pinned=question.get('sourcePaperVersionId',session['paper_version_id'])
            if paper_version_id and paper_version_id!=pinned:raise ContractError('Issue version differs from the session snapshot')
            paper_version_id=pinned
        if question_version_id:
            row=self.connection.execute('SELECT id,question_id,paper_version_id FROM question_versions WHERE id=?',(question_version_id,)).fetchone()
        elif paper_version_id:
            row=self.connection.execute('SELECT id,question_id,paper_version_id FROM question_versions WHERE question_id=? AND paper_version_id=?',(question_id,paper_version_id)).fetchone()
        else:
            row=self.connection.execute('SELECT id,question_id,paper_version_id FROM question_versions WHERE question_id=? ORDER BY version_number DESC LIMIT 1',(question_id,)).fetchone()
        if not row or row['question_id']!=question_id or (paper_version_id and row['paper_version_id']!=paper_version_id):
            raise ContractError('Question and version do not match')
        question_version_id,paper_version_id=row['id'],row['paper_version_id']

        issue_id = "iss_" + uuid.uuid4().hex[:16]
        now = utc_now()
        with self._transaction():
            self.connection.execute(
                "INSERT INTO content_issues (id, issue_type, question_id, question_version_id, paper_version_id, session_id, description, status, reported_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)",
                (issue_id, issue_type, question_id, question_version_id, paper_version_id, session_id, description.strip(), now, now),
            )
            self.connection.execute('INSERT INTO content_issue_events VALUES (?,?,?,?,?)',(uuid.uuid4().hex,issue_id,'OPEN',None,now))
        return {
            "issueId": issue_id,
            "questionId": question_id,
            "issueType": issue_type,
            "status": "OPEN",
            "description": description.strip(),
            "reportedAt": now,
        }

    def list_content_issues(
        self,
        *,
        status: str | None = None,
        question_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if type(limit) is not int or not 1<=limit<=200:raise ContractError("Invalid issue page size")
        query = "SELECT * FROM content_issues WHERE 1=1"
        params: list[Any] = []
        if type(limit) is not int or not 1<=limit<=200:raise ContractError("Invalid content issue limit")
        if status:
            query += " AND status = ?"
            params.append(status)
        if question_id:
            query += " AND question_id = ?"
            params.append(question_id)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        query += " ORDER BY reported_at DESC LIMIT ?"
        params.append(limit)
        rows = self.connection.execute(query, params).fetchall()
        return [
            {
                "issueId": r["id"],
                "issueType": r["issue_type"],
                "questionId": r["question_id"],
                "questionVersionId": r["question_version_id"],
                "paperVersionId": r["paper_version_id"],
                "sessionId": r["session_id"],
                "description": r["description"],
                "status": r["status"],
                "statusReason": r["status_reason"],
                "reportedAt": r["reported_at"],
                "updatedAt": r["updated_at"],
            }
            for r in rows
        ]

    def update_content_issue_status(
        self,
        issue_id: str,
        status: str,
        *,
        reason: str | None = None,
    ) -> dict[str, Any]:
        valid_statuses = {"OPEN", "TRIAGED", "IN_PROGRESS", "FIXED_PENDING_REVIEW", "CLOSED", "DUPLICATE", "REJECTED"}
        if status not in valid_statuses:
            raise ContractError(f"Invalid content issue status: {status}")
        if reason is not None and (not isinstance(reason,str) or not 3<=len(reason.strip())<=5000):raise ContractError('Invalid issue resolution reason')
        if status in {'CLOSED','DUPLICATE','REJECTED'} and not reason:raise ContractError('A resolution reason is required')
        if not isinstance(reason,str) or not 3<=len(reason.strip())<=2000:raise ContractError('A resolution reason is required')
        with self._transaction():
            row=self.connection.execute('SELECT * FROM content_issues WHERE id=?',(issue_id,)).fetchone()
            if not row:raise KeyError(issue_id)
            transitions={'OPEN':{'TRIAGED','IN_PROGRESS','DUPLICATE','REJECTED'},'TRIAGED':{'IN_PROGRESS','DUPLICATE','REJECTED'},'IN_PROGRESS':{'FIXED_PENDING_REVIEW','REJECTED'},'FIXED_PENDING_REVIEW':{'CLOSED','IN_PROGRESS'}}
            if status not in transitions.get(row['status'],set()):raise ContractError('Invalid content issue transition')
            if status=='CLOSED':
                newer=self.connection.execute("SELECT 1 FROM question_versions q JOIN paper_versions p ON p.id=q.paper_version_id LEFT JOIN paper_delivery_state d ON d.paper_version_id=p.id WHERE q.question_id=? AND p.id<>? AND p.published_at>(SELECT published_at FROM paper_versions WHERE id=?) AND p.status='PUBLISHED' AND COALESCE(d.state,'') NOT IN ('SUSPENDED','REVIEW_REQUIRED')",(row['question_id'],row['paper_version_id'],row['paper_version_id'])).fetchone()
                if not newer:raise ContractError('Publish and review the corrected version before closing this issue')
            now=utc_now()
            self.connection.execute('UPDATE content_issues SET status=?,status_reason=?,updated_at=? WHERE id=?',(status,reason,now,issue_id))
            self.connection.execute('INSERT INTO content_issue_events VALUES (?,?,?,?,?)',(uuid.uuid4().hex,issue_id,status,reason,now))
        return {'issueId':issue_id,'status':status,'statusReason':reason,'updatedAt':now}
