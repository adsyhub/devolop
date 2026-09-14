"""SQLite publication, practice session, event stream and learning data store."""

from __future__ import annotations

import datetime
import os
import json
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any

from .audit import audit_paper, delivery_paper, iter_questions, iter_asset_nodes, prepare_paper
from .constants import FORM_SPECS, WRONG_QUESTION_STATES
from .errors import ContractError, QualityGateError, SessionError
from .grading import grade_paper
from .migrations import migrate_database
from .page_contract import validate_learner_response
from .security import sanitize_paper_for_learner
from .selection import validate_form_selection
from .util import canonical_json, digest_json, utc_now


from .sessions import SessionStoreMixin
from .learning import LearningStoreMixin


from .workflows import WorkflowMixin


class Database(WorkflowMixin, LearningStoreMixin, SessionStoreMixin):
    def __init__(self, path: Path | str, *, media_dir: Path | str | None = None, workspace_root: Path | str | None = None, allow_synthetic: bool | None = None) -> None:
        self.allow_synthetic = allow_synthetic if allow_synthetic is not None else os.environ.get("EJU_ALLOW_SYNTHETIC") == "1"
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.media_dir = Path(media_dir).expanduser().resolve() if media_dir else self.path.parent / "media"
        self.workspace_root = Path(workspace_root).expanduser().resolve() if workspace_root else (
            self.path.parent.parent if self.path.parent.name == "library" else self.path.parent
        )
        self._local = threading.local()
        # Ensure schema migrations are up to date
        migrate_database(self.connection)
        if self.connection.execute('SELECT 1 FROM question_versions q LEFT JOIN question_search s ON s.question_version_id=q.id WHERE s.question_version_id IS NULL LIMIT 1').fetchone():
            self.rebuild_search()
        if self.connection.execute("SELECT 1 FROM practice_sessions ps LEFT JOIN attempt_facts a ON a.session_id=ps.id WHERE ps.status='SUBMITTED' AND a.session_id IS NULL LIMIT 1").fetchone():
            self.rebuild_attempts()

    @property
    def connection(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 5000")
            self._local.connection = connection
        return connection

    def close(self) -> None:
        connection = getattr(self._local, "connection", None)
        if connection is not None:
            connection.close()
            self._local.connection = None

    def _log(self, action: str, target_type: str, target_id: str, details: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), action, target_type, target_id, canonical_json(details), utc_now()),
        )

    def publish(self, paper: dict[str, Any], *, channel: str) -> dict[str, Any]:
        with self._transaction():
            return self._publish_locked(paper, channel=channel)

    def _publish_locked(self, paper: dict[str, Any], *, channel: str) -> dict[str, Any]:
        if paper.get('contentKind') == 'SYNTHETIC' and not self.allow_synthetic:
            raise QualityGateError('Synthetic content requires an explicitly enabled example workspace')
        from .publish import assert_publish_rights
        assert_publish_rights(paper, channel)
        report = audit_paper(paper)
        if report["status"] != "passed":
            raise QualityGateError(f"Paper has {report['summary']['errors']} quality errors")
        if paper.get("contentRevision") != prepare_paper(paper)["contentRevision"]:
            raise QualityGateError("contentRevision does not match paper content; prepare a new revision")
        if paper.get("contentKind") != "SYNTHETIC":
            self.verify_paper_review(paper)
        from .assets import AssetStore
        from .util import sha256_file
        import mimetypes
        store = AssetStore(self.media_dir)
        media = {}
        for _, node in iter_asset_nodes(paper):
            asset_id = node["assetId"]
            path = store.get_path(asset_id)
            if sha256_file(path) != asset_id:
                raise QualityGateError("Media content hash mismatch")
            media[asset_id] = (path, mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        if channel not in {"PRIVATE", "PUBLIC", "COMMERCIAL"}:
            raise ContractError("channel must be PRIVATE, PUBLIC or COMMERCIAL")
        now = utc_now()
        paper_id = str(paper["paperId"])
        source = paper["source"]
        completeness = str(paper.get("completeness") or "SAMPLE")
        available_modes = canonical_json(paper.get("availableModes") or ["PRACTICE"])
        syllabus_id = str(paper.get("syllabusId") or paper.get("syllabusVersion") or "basic-2015")
        connection = self.connection

        existing = connection.execute(
            "SELECT id, version_number, channel FROM paper_versions WHERE paper_id = ? AND content_revision = ?",
            (paper_id, paper["contentRevision"]),
        ).fetchone()
        if existing:
            if existing["channel"] != channel:
                raise ContractError("This revision is already published in a different channel")
            return {
                "paperId": paper_id,
                "paperVersionId": existing["id"],
                "version": existing["version_number"],
                "cached": True,
            }

        latest = connection.execute(
            "SELECT COALESCE(MAX(version_number), 0) AS value FROM paper_versions WHERE paper_id = ?",
            (paper_id,),
        ).fetchone()["value"]
        version = int(latest) + 1
        version_id = f"pv_{uuid.uuid4().hex}"

        try:
            connection.execute(
                "INSERT OR IGNORE INTO sources VALUES (?, ?, ?, ?)",
                (
                    source["sourceId"],
                    source["rights"]["status"],
                    canonical_json(source),
                    now,
                ),
            )
            # Register source files
            for sf in source.get("files") or []:
                if isinstance(sf, dict) and sf.get("sha256"):
                    sf_id = "sf_" + digest_json([source["sourceId"], sf.get("role"), sf["sha256"]])[:24]
                    connection.execute(
                        "INSERT OR IGNORE INTO source_files VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            sf_id,
                            source["sourceId"],
                            sf.get("role", "OTHER"),
                            sf.get("path", ""),
                            sf.get("fileName", ""),
                            int(sf.get("sizeBytes") or 0),
                            sf["sha256"],
                            now,
                        ),
                    )

            connection.execute(
                "INSERT OR IGNORE INTO papers VALUES (?, ?, ?, ?)",
                (paper_id, paper["stableCode"], paper["title"], now),
            )
            connection.execute(
                "INSERT INTO paper_versions (id, paper_id, version_number, content_revision, status, channel, completeness, available_modes, syllabus_id, payload_json, created_at, published_at) "
                "VALUES (?, ?, ?, ?, 'PUBLISHED', ?, ?, ?, ?, ?, ?, ?)",
                (
                    version_id,
                    paper_id,
                    version,
                    paper["contentRevision"],
                    channel,
                    completeness,
                    available_modes,
                    syllabus_id,
                    canonical_json(paper),
                    now,
                    now,
                ),
            )

            for asset_id, (path, mime) in media.items():
                connection.execute("INSERT OR IGNORE INTO assets (id,sha256,mime_type,size_bytes,file_path,created_at) VALUES (?,?,?,?,?,?)",
                                   (asset_id,asset_id,mime,path.stat().st_size,path.relative_to(store.root).as_posix(),now))
                connection.execute("INSERT INTO paper_assets VALUES (?,?,?)", (version_id,asset_id,"CONTENT"))

            for form, _, question in iter_questions(paper):
                question_id = str(question["questionId"])
                connection.execute(
                    "INSERT OR IGNORE INTO questions VALUES (?, ?, ?)",
                    (question_id, str(question["localKey"]), now),
                )
                q_latest = connection.execute(
                    "SELECT COALESCE(MAX(version_number), 0) AS value FROM question_versions WHERE question_id = ?",
                    (question_id,),
                ).fetchone()["value"]
                q_delivery = dict(question)
                answer = q_delivery.pop("correctAnswer", None)
                explanation = q_delivery.pop("explanation", None)
                scoring_policy = q_delivery.get("scoringPolicy", "ALL_OR_NOTHING")
                connection.execute(
                    "INSERT INTO question_versions (id, question_id, paper_version_id, version_number, form_code, answer_type, content_hash, delivery_json, answer_json, explanation_json, scoring_policy, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"qv_{uuid.uuid4().hex}",
                        question_id,
                        version_id,
                        int(q_latest) + 1,
                        form["formCode"],
                        question["answerSpec"]["type"],
                        digest_json(question),
                        canonical_json(q_delivery),
                        canonical_json(answer) if answer is not None else None,
                        canonical_json(explanation) if explanation is not None else None,
                        scoring_policy,
                        now,
                    ),
                )

            self._log(
                "PUBLISH",
                "paper_version",
                version_id,
                {"channel": channel, "version": version, "completeness": completeness},
            )
            self.index_version(version_id,paper)
            if source.get('inventoryId'):
                connection.execute("INSERT INTO publication_outbox VALUES (?,?,?,?, 'PENDING',?)",('out_'+uuid.uuid4().hex,version_id,source['inventoryId'],canonical_json({'pipelineStatus':'PUBLISHED','publishedVersionId':version_id,'completeness':completeness,'reviewState':'REVIEWED','blockingIssues':[] if completeness=='COMPLETE' else ['PARTIAL_CONTENT']}),now))
        except Exception:
            connection.rollback()
            raise
        return {
            "paperId": paper_id,
            "paperVersionId": version_id,
            "version": version,
            "completeness": completeness,
            "cached": False,
        }

    def list_papers(
        self,
        *,
        session: str | None = None,
        subject: str | None = None,
        language: str | None = None,
        completeness: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT p.id, p.stable_code, p.title, pv.id AS paper_version_id, pv.version_number, "
            "pv.content_revision, pv.channel, pv.completeness, pv.available_modes, pv.published_at, "
            "pv.payload_json "
            "FROM papers p JOIN paper_versions pv ON pv.paper_id = p.id "
            "WHERE pv.status = 'PUBLISHED' AND pv.version_number = "
            "(SELECT MAX(x.version_number) FROM paper_versions x WHERE x.paper_id = p.id AND x.status = 'PUBLISHED') "
            "ORDER BY p.stable_code"
        ).fetchall()

        results = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            if session and payload.get("session") != session:
                continue
            if subject and not any(FORM_SPECS.get(f.get("formCode"), None) and (FORM_SPECS[f["formCode"]].subject == subject or (subject == "SCIENCE" and FORM_SPECS[f["formCode"]].subject in {"PHYSICS", "CHEMISTRY", "BIOLOGY"})) for f in payload.get("forms", [])):
                continue
            if language and not any(FORM_SPECS.get(f.get("formCode"), None) and FORM_SPECS[f["formCode"]].language == language for f in payload.get("forms", [])):
                continue
            if completeness and row["completeness"] != completeness:
                continue

            delivery = self.connection.execute("SELECT state,note FROM paper_delivery_state WHERE paper_version_id=?", (row["paper_version_id"],)).fetchone()
            results.append({
                "paperId": row["id"],
                "paperVersionId": row["paper_version_id"],
                "stableCode": row["stable_code"],
                "title": row["title"],
                "session": payload.get("session"),
                "syllabusVersion": payload.get("syllabusVersion"),
                "version": row["version_number"],
                "channel": row["channel"],
                "completeness": row["completeness"],
                "availableModes": json.loads(row["available_modes"] or '["PRACTICE"]'),
                "questionCount": payload.get("questionCount", 0),
                "forms": [f.get("formCode") for f in payload.get("forms", [])],
                "publishedAt": row["published_at"],
                "deliveryState": delivery["state"] if delivery else "AVAILABLE",
                "deliveryNote": delivery["note"] if delivery else "",
                # 把关程度随卷单一起给出，选卷时就能看见，而不是点进去才知道。
                # 缺这个字段的是本次改造之前发布的卷（其中包括已退役的那批），
                # 默认成 HUMAN_SIGNED 会把最弱的说成最强的，所以照实报"未标注"。
                "reviewGrade": payload.get("reviewGrade") or "UNRECORDED",
                "missingContentReasons": payload.get("missingContentReasons") or [],
            })
        return results

    def get_paper(self, paper_id: str, *, include_answers: bool = False) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT id,payload_json FROM paper_versions WHERE paper_id = ? AND status = 'PUBLISHED' "
            "ORDER BY version_number DESC LIMIT 1",
            (paper_id,),
        ).fetchone()
        if row is None:
            raise KeyError(paper_id)
        if not include_answers and self.content_withdrawn(row['id']):
            raise SessionError('Source rights have been withdrawn')
        paper = json.loads(row["payload_json"])
        return paper if include_answers else sanitize_paper_for_learner(paper)

    def get_paper_outline(self, paper_id: str) -> dict[str, Any]:
        paper = self.get_paper(paper_id, include_answers=False)
        outline = {
            "paperId": paper["paperId"],
            "title": paper["title"],
            "session": paper["session"],
            "forms": [],
        }
        for form in paper.get("forms", []):
            form_entry = {
                "formCode": form["formCode"],
                "spec": form.get("spec"),
                "groups": [],
            }
            for group in form.get("groups", []):
                group_entry = {
                    "groupCode": group.get("groupCode"),
                    "questions": [
                        {
                            "questionId": q.get("questionId"),
                            "printedLabel": q.get("printedLabel"),
                            "localKey": q.get("localKey"),
                            "answerType": q.get("answerSpec", {}).get("type"),
                        }
                        for q in group.get("questions", [])
                    ],
                }
                form_entry["groups"].append(group_entry)
            outline["forms"].append(form_entry)
        return outline

    def get_paper_questions(
        self, paper_id: str, *, form_code: str | None = None, cursor: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        if type(cursor) is not int or type(limit) is not int or cursor < 0 or not 1 <= limit <= 200:
            raise ContractError("cursor must be >= 0 and limit between 1 and 200")
        paper = self.get_paper(paper_id, include_answers=False)
        matched_questions = []
        for form in paper.get("forms", []):
            if form_code and form.get("formCode") != form_code:
                continue
            for group in form.get("groups", []):
                for q in group.get("questions", []):
                    matched_questions.append({
                        **q,
                        "formCode": form.get("formCode"),
                        "groupCode": group.get("groupCode"),
                    })

        total = len(matched_questions)
        slice_items = matched_questions[cursor : cursor + limit]
        next_cursor = cursor + limit if cursor + limit < total else None
        return {
            "total": total,
            "cursor": cursor,
            "nextCursor": next_cursor,
            "questions": slice_items,
        }

    def update_wrong_question_status(self, question_id: str, status: str, notes: str | None = None) -> None:
        if notes is not None and (not isinstance(notes,str) or len(notes)>10000):raise ContractError('Invalid mistake notes')
        if status not in WRONG_QUESTION_STATES:raise ContractError('Invalid wrong question status')
        with self._transaction():
            old=self.connection.execute('SELECT status FROM wrong_question_state WHERE question_id=?',(question_id,)).fetchone()
            if not old:raise KeyError(question_id)
            self.connection.execute('INSERT INTO review_events VALUES (?,?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,question_id,old['status'],status,None,None,notes,None,utc_now()))
            self.connection.execute("UPDATE wrong_question_state SET status=?,notes=COALESCE(?,notes),next_review_at=CASE WHEN ?='MASTERED' THEN NULL ELSE next_review_at END WHERE question_id=?",(status,notes,status,question_id))

    def set_bookmark(self, question_id: str, note: str | None = None) -> None:
        self._require_question(question_id)
        if note is not None and (not isinstance(note, str) or len(note) > 10000):
            raise ContractError("Bookmark note is invalid")
        self.connection.execute(
            "INSERT INTO bookmarks VALUES (?, ?, ?, ?) "
            "ON CONFLICT(question_id) DO UPDATE SET note = excluded.note",
            (f"bm_{uuid.uuid4().hex}", question_id, note, utc_now()),
        )
        self.connection.commit()

    def remove_bookmark(self, question_id: str) -> None:
        self.connection.execute("DELETE FROM bookmarks WHERE question_id = ?", (question_id,))
        self.connection.commit()

    def is_bookmarked(self, question_id: str) -> bool:
        row = self.connection.execute("SELECT 1 FROM bookmarks WHERE question_id = ?", (question_id,)).fetchone()
        return row is not None

    def set_question_note(self, question_id: str, note_text: str) -> None:
        self.save_note_revision(question_id,note_text)

    def get_question_note(self, question_id: str) -> str | None:
        row = self.connection.execute(
            "SELECT note_text FROM question_notes WHERE question_id = ?", (question_id,)
        ).fetchone()
        return row["note_text"] if row else None

    def set_delivery_state(self, version_id: str, state: str, note: str, *, reason_code="CONTENT_REVIEW") -> dict:
        if state not in {"REVIEW_REQUIRED", "SUSPENDED", "REVIEWED"} or not isinstance(note, str) or not note.strip():
            raise ContractError("A valid delivery state and reason are required")
        if reason_code not in {"CONTENT_REVIEW","RIGHTS_WITHDRAWN"}:raise ContractError("Invalid suspension reason")
        with self._transaction():
            if not self.connection.execute("SELECT 1 FROM paper_versions WHERE id=?", (version_id,)).fetchone():
                raise KeyError(version_id)
            if state == "REVIEWED":
                stored=json.loads(self.connection.execute("SELECT payload_json FROM paper_versions WHERE id=?",(version_id,)).fetchone()[0])
                if stored.get('contentKind') != 'SYNTHETIC' or not self.allow_synthetic: self.verify_paper_review(stored)
            self.connection.execute("INSERT INTO paper_delivery_state VALUES (?,?,?,?) ON CONFLICT(paper_version_id) "
                                    "DO UPDATE SET state=excluded.state,note=excluded.note,updated_at=excluded.updated_at", (version_id,state,note,utc_now()))
            self.connection.execute("INSERT INTO library_metadata VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",("restriction:"+version_id,reason_code if state!="REVIEWED" else ""))
            self._log("DELIVERY_STATE", "paper_version", version_id, {"state":state,"note":note})
        return {"paperVersionId": version_id, "state": state}

    def verify_paper_review(self, paper):
        # All source-derived releases, including partial practice, need a current certificate.
        from .audit import review_content_digest
        if not self.connection.execute("SELECT 1 FROM sqlite_master WHERE name='paper_reviews'").fetchone():
            raise QualityGateError("Source paper review certificate has not been recorded")
        review = paper.get("reviewSummary", {})
        row = self.connection.execute("SELECT * FROM paper_reviews WHERE id=? AND decision='APPROVED' AND id NOT IN (SELECT review_id FROM paper_review_revocations)", (review.get("reviewId"),)).fetchone()
        if not row or row["content_digest"] != review.get("contentDigest") or row["content_digest"] != review_content_digest(paper):
            raise QualityGateError("Missing or outdated paper review certificate")
        from .review import ContentWorkspace
        ws=ContentWorkspace(self.workspace_root,self)
        _,manifest=ws.source(row['source_id'])
        from .inventory import get_inventory_item
        iid=manifest.get('inventoryId')
        item=get_inventory_item(iid,self.workspace_root/'content/content-inventory.json') if iid else None
        if not item or paper['source'].get('inventoryId')!=iid or any(item[k]!=manifest[k] for k in ['session','subject','language']):
            raise QualityGateError('Source inventory binding changed; review again')
        if paper.get('expectedStructure',{}).get('sourceHashes')!={f['role']:f['sha256'] for f in manifest['files']}:
            raise QualityGateError('Source files changed after review')
        if paper['source']['rights'] != manifest['rights']:
            raise QualityGateError('Source rights changed after review')
        baseline=self.connection.execute('SELECT id,structure_json FROM source_structure_revisions WHERE source_id=? ORDER BY revision DESC LIMIT 1',(row['source_id'],)).fetchone()
        if not baseline or paper.get('expectedStructure',{}).get('structureRevisionId') != baseline['id']:
            raise QualityGateError('Source structure baseline changed; review again')
        for rid in json.loads(row['page_revision_ids_json']):
            page=self.connection.execute('SELECT * FROM page_revisions WHERE id=?',(rid,)).fetchone()
            if not page or ws._latest(row['source_id'],page['role'],page['page_number'])['id'] != rid:
                raise QualityGateError('A reviewed page has changed')


    def media_is_published(self, asset_id):
        rows=self.connection.execute("SELECT DISTINCT pv.id,pv.payload_json FROM paper_assets pa JOIN paper_versions pv ON pv.id=pa.paper_version_id "
            "LEFT JOIN paper_delivery_state ds ON ds.paper_version_id=pv.id WHERE pa.asset_id=? AND pv.status='PUBLISHED' "
            "AND COALESCE(ds.state,'') NOT IN ('SUSPENDED','REVIEW_REQUIRED')",(asset_id,)).fetchall()
        return any(node.get('assetId')==asset_id for row in rows if not self.content_withdrawn(row['id']) for _,node in iter_asset_nodes(sanitize_paper_for_learner(json.loads(row['payload_json']))))

    def media_for_session(self, session_id, asset_id):
        session,paper=self._session_with_paper(session_id)
        selected=json.loads(session['selected_forms_json'])
        paper={**paper,'forms':[f for f in paper['forms'] if f['formCode'] in selected]}
        content=paper if session['status']=='SUBMITTED' else sanitize_paper_for_learner(paper)
        refs={node['assetId'] for _,node in iter_asset_nodes(content)}
        refs.update(t['assetId'] for t in self.session_audio(session_id)['tracks'])
        if session['status']=='SUBMITTED':
            for item in self.review_content(session_id)['items']:
                if item['content']:refs.update(n['assetId'] for _,n in iter_asset_nodes(item['content']))
        return asset_id in refs

    def content_withdrawn(self,version_id):
        row=self.connection.execute('SELECT value FROM library_metadata WHERE key=?',('restriction:'+version_id,)).fetchone()
        return bool(row and row[0]=='RIGHTS_WITHDRAWN')
