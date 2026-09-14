"""API v1 and static web client server with Range streaming and security boundaries."""

from __future__ import annotations

import json
import os
import re
import secrets
import logging
import time
import uuid
from http.cookies import SimpleCookie
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__
from .assets import AssetStore
from .audio import parse_range_header
from .db import Database
from .errors import ContractError, EjuBankError, MediaError, SecurityError, SessionError
from .inventory import inventory_status_summary, load_inventory, upsert_inventory_item
from .ops import create_backup, run_doctor
from .review import ContentWorkspace
from .audit import review_content_digest
from .security import validate_host, validate_origin, verify_admin_token
from .studio_summary import delivery_overview, source_summary, studio_summary
from .util import utc_now


class WorkspaceHTTPServer(ThreadingHTTPServer):
    def server_close(self):
        worker = getattr(self, 'job_worker', None)
        if worker: worker.close()
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    server_version = "EjuBank/" + __version__

    def send_response(self,code,message=None):
        self.response_status=int(code)
        super().send_response(code,message)

    @property
    def database(self) -> Database:
        return self.server.database  # type: ignore[attr-defined]

    @property
    def asset_store(self) -> AssetStore:
        return self.server.asset_store  # type: ignore[attr-defined]

    @property
    def allow_remote(self) -> bool:
        return getattr(self.server, "allow_remote", False)

    @property
    def admin_token(self) -> str | None:
        return getattr(self.server, "admin_token", None)

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(15)
        self.request_id = uuid.uuid4().hex

    def _security_check(self) -> None:
        validate_host(self.headers.get("Host"), allow_remote=self.allow_remote,
                      host_allowlist=getattr(self.server, "host_allowlist", None))
        validate_origin(self.headers.get("Origin"), self.command, allow_remote=self.allow_remote,
                        allowed_origins=getattr(self.server, "allowed_origins", None), expected_host=self.headers.get("Host"))
        path = urlparse(self.path).path
        requires_auth = (self.allow_remote and path.startswith("/api/")) or path.startswith("/api/v1/admin")
        if requires_auth and path != "/api/v1/auth":
            cookie = SimpleCookie()
            try: cookie.load(self.headers.get("Cookie", ""))
            except Exception: raise SecurityError("Invalid authentication cookie")
            value = cookie.get("eju_access")
            if not value or not secrets.compare_digest(value.value, self.server.access_cookie):
                verify_admin_token(self.headers.get("Authorization"), self.admin_token)

    def _internal_error(self, exc) -> None:
        logging.error(json.dumps({"requestId": self.request_id, "errorType": type(exc).__name__}))
        self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", f"Internal error; reference {self.request_id}")

    def _json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Request-ID", self.request_id)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def _error(self, status: HTTPStatus, code: str, message: str) -> None:
        self.response_error_code=code
        self._json({"error": {"code": code, "message": message, "requestId": self.request_id}}, status)

    def _body(self) -> dict[str, Any]:
        te = self.headers.get("Transfer-Encoding")
        if te and te.strip().lower() != "identity":
            raise ContractError("Transfer-Encoding is not supported")
        if len(self.headers.get_all("Content-Length",[]))>1: raise ContractError("Duplicate Content-Length")
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError as exc:
            raise ContractError("Invalid Content-Length") from exc
        if length < 0 or length > 2_000_000:
            raise ContractError("Request body is too large")
        ct = self.headers.get("Content-Type", "")
        if ct and ct.split(";",1)[0].strip().lower() != "application/json":
            raise ContractError("Content-Type must be application/json")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"),parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON number"))) if length else {}
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise ContractError("Request body must be UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise ContractError("Request body must be an object")
        return value

    def _dispatch(self):
        parsed = urlparse(self.path)
        path, method = parsed.path, self.command
        query = parse_qs(parsed.query)
        q = lambda key, default=None: query.get(key, [default])[0]
        self._security_check()
        # 上传的是原卷 PDF，不是 JSON：_body() 只收 2 MB 的 application/json，
        # 所以这条路由必须在它之前拦下来，自己读自己的字节流。
        if method == "POST" and path == "/api/v1/admin/uploads":
            self._json(self._upload_source(), HTTPStatus.CREATED)
            return
        body = self._body() if method in {"POST", "PUT"} else {}
        db, ws = self.database, self.server.content_workspace
        from .http_workflows import dispatch
        if dispatch(self,method,path,body,q): return
        def route(verb, pattern, action, status=HTTPStatus.OK):
            match = re.fullmatch(pattern, path)
            if (method == verb or (verb == "GET" and method == "HEAD")) and match:
                self._json(action(*match.groups()), status)
                return True
            return False
        if method in {"GET", "HEAD"}:
            session_media=re.fullmatch(r'/api/v1/sessions/([^/]+)/media/([a-f0-9]{64})',path)
            if session_media:
                if not db.media_for_session(session_media[1],session_media[2]): raise KeyError(session_media[2])
                self._handle_media(session_media[2],allow_unpublished=True)
                return
            m = re.fullmatch(r"/api/v1/(admin/)?media/([a-f0-9]{64})", path)
            if m:
                self._handle_media(m.group(2), allow_unpublished=bool(m.group(1)))
                return
            if path in {"/api/health", "/api/v1/health"}:
                self._json({"status":"ok", "version":__version__, "timestamp":utc_now(), "libraryInstanceId":self.server.instance_id})
                return
            if route("GET", r"/(?:api/v1|api)/papers", lambda: {"papers":db.list_papers(session=q("session"),subject=q("subject"),language=q("language"),completeness=q("completeness"))}): return
            if route("GET", r"/api/v1/papers/([^/]+)/outline", lambda pid:{"outline":db.get_paper_outline(pid)}): return
            if route("GET", r"/api/v1/papers/([^/]+)/questions", lambda pid:db.get_paper_questions(pid,form_code=q("form"),cursor=int(q("cursor",0)),limit=int(q("limit",50)))): return
            if route("GET", r"/(?:api/v1|api)/papers/([^/]+)", lambda pid:{"paper":db.get_paper(pid)}): return
            if route("GET", r"/api/v1/questions", lambda:db.search_questions(query=q("q",""),form_code=q("form"),kind=q("kind","ALL"),topic=q("topic"),language=q("language"),status=q("status"),cursor=q("cursor",0),limit=int(q("limit",50)))): return
            if route("GET", r"/api/v1/sessions/([^/]+)/paper", lambda sid:{"paper":db.get_session_paper(sid)}): return
            if route("GET", r"/api/v1/sessions/([^/]+)/result", lambda sid:{"result":db.get_result(sid)}): return
            if route("GET", r"/(?:api/v1|api)/sessions/([^/]+)", lambda sid:{"session":db.get_session(sid)}): return
            if route("GET", r"/api/v1/history", lambda:{"history":db.get_history(limit=int(q("limit",50)))}): return
            if route("GET", r"/api/v1/wrong-questions", lambda:{"wrongQuestions":db.get_wrong_questions()}): return
            if route("GET", r"/api/v1/bookmarks", lambda:{"bookmarks":db.list_bookmarks()}): return
            if route("GET", r"/api/v1/questions/([^/]+)/note", db.note_detail): return
            if route("GET", r"/api/v1/content-issues", lambda:{"issues":db.list_content_issues(question_id=q("questionId"),session_id=q("sessionId"),status=q("status"))}): return
            if route("GET", r"/api/v1/admin/sources", lambda:{"sources":ws.list_sources()}): return
            # 聚合读模型：状态的唯一权威来源，且**纯读**。原来工作台拿 /candidate
            # 当读接口，而那个接口会真的组装一遍并把 paper.json 写回工作目录——
            # 于是"看一眼列表"变成"给每一行跑一次组装"（规范 §11.3、§8.5）。
            if route("GET", r"/api/v1/admin/studio/delivery", lambda:delivery_overview(db)): return
            if route("GET", r"/api/v1/admin/studio/summary",
                     lambda:studio_summary(ws, db, limit=int(q("limit", 200)))): return
            if route("GET", r"/api/v1/admin/sources/([^/]+)/summary",
                     lambda sid:source_summary(ws, db, sid)): return
            if route("GET", r"/api/v1/admin/sources/([^/]+)/structure", ws.read_source_structure): return
            if route("GET", r"/api/v1/admin/sources/([^/]+)/candidate", lambda sid:self._candidate(sid,q("scope","FULL"))): return
            m = re.fullmatch(r"/api/v1/admin/sources/([^/]+)/pages/([^/]+)/(\d+)/image",path)
            if m:
                data = ws.page_image(m.group(1), m.group(2), int(m.group(3)))
                self.send_response(200);self.send_header("Content-Type","image/png");self.send_header("Content-Length",str(len(data)));self.send_header("Cache-Control","no-store");self.end_headers()
                if self.command != "HEAD": self.wfile.write(data)
                return
            if route("GET", r"/api/v1/admin/sources/([^/]+)/pages/([^/]+)/(\d+)", lambda sid,role,num:ws.read_page(sid,role,int(num))): return
            if route("GET", r"/api/v1/admin/inventory", lambda:inventory_status_summary(ws.root / "content/content-inventory.json")): return
            if route("GET", r"/api/v1/admin/doctor", lambda:run_doctor(database_path=db.path,media_dir=self.asset_store.root)): return
            from .jobs import JobManager
            if route("GET", r"/api/v1/admin/jobs", lambda:JobManager.list_jobs(db,target_id=q("targetId"),status=q("status"),cursor=int(q("cursor",0)),limit=int(q("limit",50)))): return
            if route("GET", r"/api/v1/admin/jobs/([^/]+)", lambda jid:{"job":JobManager.get_job(db,jid)}): return
            if not path.startswith("/api/"):
                self._static(path);return
        if method == "POST":
            if path == "/api/v1/auth":
                verify_admin_token("Bearer " + str(body.get("token", "")),self.admin_token)
                self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store")
                self.send_header("Set-Cookie",f"eju_access={self.server.access_cookie}; HttpOnly; SameSite=Strict; Path=/")
                self.end_headers();self.wfile.write(b'{"authenticated":true}');return
            if route("POST", r"/(?:api/v1|api)/sessions", lambda:db.create_session(body.get("paperId",""),body.get("selectedForms",[]),mode=body.get("mode","PRACTICE"),question_ids=body.get("questionIds"),section_codes=body.get("sectionCodes")),HTTPStatus.CREATED): return
            if route("POST", r"/api/v1/practice", lambda:db.create_practice(body.get("questionIds"),random_order=body.get("randomOrder",False)),HTTPStatus.CREATED): return
            if route("POST", r"/api/v1/sessions/([^/]+)/responses:batch", lambda sid:db.record_responses_batch(sid,body.get("items",[]),expected_version=body.get("expectedVersion"),request_id=body.get("requestId"))): return
            if route("POST", r"/api/v1/sessions/([^/:]+):pause", db.pause_session): return
            if route("POST", r"/api/v1/sessions/([^/:]+):resume", db.resume_session): return
            if route("POST", r"/api/v1/sessions/([^/:]+):abandon", db.abandon_session): return
            if route("POST", r"/api/v1/sessions/([^/:]+):submit", lambda sid:{"result":db.submit_session(sid,expected_response_version=body.get("expectedResponseVersion",body.get("expectedVersion")))}): return
            if route("POST", r"/api/sessions/([^/:]+)/submit", lambda sid:{"result":db.submit_session(sid,expected_response_version=body.get("expectedResponseVersion",body.get("expectedVersion")))}): return
            if route("POST", r"/api/v1/wrong-questions/([^/]+)/schedule", lambda qid:db.schedule_review(qid,body.get("days"),notes=body.get("notes"))): return
            if route("POST", r"/api/v1/content-issues", lambda:{"issue":db.report_content_issue(body.get("questionId"),body.get("description"),issue_type=body.get("issueType","OTHER"),paper_version_id=body.get("paperVersionId"),question_version_id=body.get("questionVersionId"),session_id=body.get("sessionId"))},HTTPStatus.CREATED): return
            if route("POST", r"/api/v1/admin/sources/([^/]+)/pages/([^/]+)/(\d+)/sign", lambda sid,role,num:ws.sign_page(sid,role,int(num),body.get("revisionId"),body.get("reviewer"),body.get("confirmed"))): return
            if route("POST", r"/api/v1/admin/sources/([^/]+)/pages/([^/]+)/(\d+)/clip", lambda sid,role,num:self._clip(sid,role,int(num),body)): return
            if route("POST", r"/api/v1/admin/sources/([^/]+)/structure", lambda sid:ws.sign_source_structure(sid,body.get("structure"),body.get("reviewer"))): return
            if route("POST", r"/api/v1/admin/sources/([^/]+)/approve", lambda sid:ws.approve_paper(sid,body.get("contentDigest"),body.get("reviewer"),body.get("confirmed"),body.get("scope","FULL"))): return
            if route("POST", r"/api/v1/admin/reviews/([^/]+)/publish", lambda rid:ws.publish_review(rid,body.get("channel","PRIVATE"))): return
            if route("POST", r"/api/v1/admin/inventory", lambda:{"item":upsert_inventory_item(body,inventory_path=ws.root/"content/content-inventory.json")},HTTPStatus.CREATED): return
            if route("POST", r"/api/v1/admin/backup", lambda:{"backupFile":str(create_backup(database_path=db.path,inventory_path=ws.root/"content/content-inventory.json",media_dir=self.asset_store.root,output_dir=ws.root/"backups"))},HTTPStatus.CREATED): return
            from .jobs import JobManager
            if route("POST", r"/api/v1/admin/imports",lambda:self._import(body),HTTPStatus.ACCEPTED): return
            if route("POST", r"/api/v1/admin/jobs/([^/]+)/cancel",lambda jid:{"job":JobManager.cancel_job(db,jid,reason=body.get("reason","User requested cancellation"))}): return
            if route("POST", r"/api/v1/admin/jobs/([^/]+)/retry",lambda jid:{"job":JobManager.retry_job(db,jid,pages=body.get("pages"),failed_only=body.get("failedOnly",False))}): return
        if method == "PUT":
            if route("PUT", r"/api/v1/admin/sources/([^/]+)/pages/([^/]+)/(\d+)",lambda sid,role,num:ws.save_page(sid,role,int(num),body.get("contract"),body.get("baseRevision"))): return
            if route("PUT", r"/api/v1/sessions/([^/]+)/progress",lambda sid:db.save_progress(sid,body)): return
            if route("PUT", r"/(?:api/v1|api)/sessions/([^/]+)/responses/([^/]+)",lambda sid,qid:db.record_response(sid,qid,body.get("response"))): return
            if route("PUT", r"/api/v1/questions/([^/]+)/bookmark",lambda qid:self._bookmark(qid,body)): return
            if route("PUT", r"/api/v1/questions/([^/]+)/note",lambda qid:self._note(qid,body)): return
            if route("PUT", r"/api/v1/wrong-questions/([^/]+)",lambda qid:self._wrong(qid,body)): return
            if route("PUT", r"/api/v1/admin/content-issues/([^/]+)",lambda iid:{"issue":db.update_content_issue_status(iid,body.get("status"),reason=body.get("reason"))}): return
        if method == "DELETE":
            if path == "/api/v1/auth":
                self.send_response(200);self.send_header("Set-Cookie","eju_access=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/");self.end_headers();return
            if route("DELETE", r"/api/v1/questions/([^/]+)/bookmark",lambda qid:self._bookmark(qid,None)): return
        self._error(HTTPStatus.NOT_FOUND,"NOT_FOUND","Endpoint not found")

    def _candidate(self,sid,scope="FULL"):
        result=self.server.content_workspace.candidate(sid,scope)
        result["contentDigest"]=review_content_digest(result["paper"])
        return result

    def _clip(self,sid,role,num,body):
        from .assets import clip_figure_from_pdf, register_asset_origin
        from .source import source_file
        ws=self.server.content_workspace
        path,manifest=ws.source(sid)
        data,width,height=clip_figure_from_pdf(source_file(manifest,path,role),num,body.get("bbox"),dpi=200)
        meta=self.asset_store.put_bytes(data,mime_type="image/png",ext=".png");meta.pop("absolutePath",None)
        current=ws.read_page(sid,role,num)
        revision=current['revisionId']
        origin=register_asset_origin(self.database,meta['assetId'],sid,next(f['sha256'] for f in manifest['files'] if f['role']==role),num,body.get('bbox'),dpi=200,review_revision_id=revision if revision and not revision.startswith('file:') else None,role=role)
        return {**meta,"width":width,"height":height,"originId":origin}

    def _upload_source(self) -> dict[str, Any]:
        """收一份原卷 PDF。文件名只当推断依据，落盘名由服务端决定。"""
        from .uploads import MAX_BYTES, store
        if len(self.headers.get_all("Content-Length", [])) > 1:
            raise ContractError("Duplicate Content-Length")
        te = self.headers.get("Transfer-Encoding")
        if te and te.strip().lower() != "identity":
            raise ContractError("Transfer-Encoding is not supported")
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError as exc:
            raise ContractError("Invalid Content-Length") from exc
        if not 0 < length <= MAX_BYTES:
            raise ContractError("Upload must be between 1 byte and 150 MB")
        # 文件名走头部并且是百分号编码的：它会带中文和括号，塞不进 URL 路径。
        raw_name = self.headers.get("X-Upload-Filename") or ""
        try:
            filename = unquote(raw_name)
        except Exception:
            filename = ""
        data = b""
        while len(data) < length:
            chunk = self.rfile.read(min(length - len(data), 1 << 20))
            if not chunk:
                raise ContractError("Upload ended before the declared length")
            data += chunk
        return store(self.server.content_workspace.root, filename, data)

    def _import(self,body):
        from .jobs import JobManager
        from .job_worker import workspace_file
        from .inventory import get_inventory_item
        from .util import sha256_file
        ref=body.get("filePath",body.get("sourceRef"))
        root=self.server.content_workspace.root
        path=workspace_file(root,ref)
        if body.get("role") not in {"QUESTION_BOOKLET","ANSWER_KEY","AUDIO"}: raise ContractError("Invalid source role")
        if not isinstance(body.get("inventoryId"),str) or not get_inventory_item(body['inventoryId'],root/'content/content-inventory.json'):
            raise ContractError("Select an existing inventory item")
        return JobManager.create_job(self.database,"IMPORT_SOURCE",body["inventoryId"],
            {"sourceRef":ref,"sourceHash":sha256_file(path),"role":body["role"]})

    def _bookmark(self,qid,body):
        if body is None: self.database.remove_bookmark(qid)
        else: self.database.set_bookmark(qid,body.get("note"))
        return {"questionId":qid,"bookmarked":body is not None}

    def _note(self,qid,body):
        return self.database.save_note_revision(qid,body.get("note",""),body.get("baseRevision"))

    def _wrong(self,qid,body):
        self.database.update_wrong_question_status(qid,body.get("status",""),body.get("notes"))
        return {"questionId":qid,"updated":True}

    def _serve_request(self):
        self.request_id=uuid.uuid4().hex
        self.response_status=None;self.response_error_code=None
        started=time.perf_counter()
        try: self._dispatch()
        except KeyError: self._error(HTTPStatus.NOT_FOUND,"NOT_FOUND","Resource not found")
        except SecurityError as exc: self._error(HTTPStatus.FORBIDDEN,"FORBIDDEN",str(exc))
        except SessionError as exc: self._error(HTTPStatus.CONFLICT,"SESSION_CONFLICT",str(exc))
        except (ValueError,TypeError): self._error(HTTPStatus.BAD_REQUEST,"INVALID_INPUT","Invalid request parameters")
        except EjuBankError as exc: self._error(HTTPStatus.UNPROCESSABLE_ENTITY,type(exc).__name__,str(exc))
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception as exc: self._internal_error(exc)
        finally:
            logging.info(json.dumps({'timestamp':utc_now(),'level':'ERROR' if (self.response_status or 500)>=500 else 'INFO','action':'HTTP_'+self.command,'requestId':self.request_id,'durationMs':int((time.perf_counter()-started)*1000),'status':self.response_status,'result':'SUCCEEDED' if self.response_status and self.response_status<400 else 'FAILED','errorCode':self.response_error_code}))

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = _serve_request

    def _handle_media(self, asset_id, *, allow_unpublished=False):
        if not allow_unpublished and not self.database.media_is_published(asset_id): raise KeyError(asset_id)
        file_path=self.asset_store.get_path(asset_id)
        if not file_path.is_file(): raise KeyError(asset_id)
        size=file_path.stat().st_size
        start,end,status=0,size-1,HTTPStatus.OK
        if self.headers.get("Range"):
            try: start,end=parse_range_header(self.headers["Range"],size);status=HTTPStatus.PARTIAL_CONTENT
            except MediaError:
                self.send_response(416);self.send_header("Content-Range",f"bytes */{size}");self.send_header("Content-Length","0");self.end_headers();return
        self.send_response(status)
        self.send_header("Content-Type",mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length",str(end-start+1));self.send_header("Accept-Ranges","bytes")
        self.send_header("X-Request-ID",self.request_id);self.send_header("X-Content-Type-Options","nosniff");self.send_header("Cache-Control","private, no-store")
        if status==HTTPStatus.PARTIAL_CONTENT: self.send_header("Content-Range",f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command=="HEAD": return
        with file_path.open("rb") as handle:
            handle.seek(start);remaining=end-start+1
            while remaining:
                chunk=handle.read(min(remaining,65536))
                if not chunk: break
                self.wfile.write(chunk);remaining-=len(chunk)

    # Stable product routes. The address bar is part of the product: a learner who
    # bookmarks a workspace should get a path naming that workspace, not the .html
    # file that happens to implement it today. The old file names keep working, so
    # no existing link or bookmark breaks.
    PRODUCT_ROUTES = {
        "": "home.html",
        "/": "home.html",
        "/practice": "practice.html",
        "/me": "me.html",
        # 制作台的四个模块各是一个页面：制课、课程库、复核编辑器、运维。
        # /studio 仍然是入口，落在制课上。
        "/studio": "studio.html",
        "/studio/build": "studio.html",
        "/studio/library": "studio_library.html",
        "/studio/editor": "studio_editor.html",
        "/studio/ops": "studio_ops.html",
    }

    def _static(self, request_path: str) -> None:
        raw = self.PRODUCT_ROUTES.get(request_path.rstrip("/") or "/", request_path.lstrip("/"))
        posix = PurePosixPath(raw)
        if posix.is_absolute() or ".." in posix.parts:
            self._error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Static file not found")
            return
        resource = files("eju_bank").joinpath("web", raw)
        if not resource.is_file():
            self._error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Static file not found")
            return
        body = resource.read_bytes()
        content_type = mimetypes.guess_type(raw)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def finish(self) -> None:
        try:
            super().finish()
        finally:
            self.database.close()

    def log_message(self, format: str, *args: Any) -> None:
        pass


def create_server(
    database_path: Path | str,
    *,
    media_dir: Path | str | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    allow_remote: bool = False,
    admin_token: str | None = None,
    host_allowlist: set[str] | None = None,
    allowed_origins: set[str] | None = None,
    workspace_root: Path | str | None = None,
    start_worker: bool = True,
) -> ThreadingHTTPServer:
    admin_token = admin_token or os.environ.get("EJU_ADMIN_TOKEN")
    if host not in {"localhost", "127.0.0.1", "::1"} and not allow_remote:
        raise SecurityError("Non-loopback binding requires --allow-remote")
    if allow_remote and (not admin_token or len(admin_token) < 16 or not host_allowlist or not allowed_origins):
        raise SecurityError("Remote access requires a token of at least 16 characters, allowed hosts and allowed origins")
    # 回环绑定不再生成访问令牌：能连上 127.0.0.1 的就是本机用户本人，再让本人对
    # 自己的题库输一次口令只是仪式。跨站点的浏览器请求由 Host/Origin 校验挡住。
    # 令牌只对 --allow-remote 保留，那里它是唯一的身份凭证，上面的分支强制要求。
    database = Database(database_path, media_dir=media_dir, workspace_root=workspace_root)
    asset_store = AssetStore(Path(media_dir) if media_dir else Path(database_path).resolve().parent / "media")
    httpd = WorkspaceHTTPServer((host, port), Handler)
    httpd.database = database
    httpd.asset_store = asset_store
    httpd.allow_remote = allow_remote
    httpd.admin_token = admin_token
    httpd.host_allowlist = host_allowlist
    httpd.allowed_origins = allowed_origins
    httpd.access_cookie = secrets.token_urlsafe(32)
    database.connection.execute("INSERT OR IGNORE INTO library_metadata VALUES ('instanceId',?)",(uuid.uuid4().hex,))
    database.connection.commit()
    httpd.instance_id = database.connection.execute("SELECT value FROM library_metadata WHERE key='instanceId'").fetchone()[0]
    root = database.workspace_root
    httpd.content_workspace = ContentWorkspace(root, database)
    from .job_worker import JobWorker
    if start_worker:
        httpd.job_worker = JobWorker(database,httpd.content_workspace)
        httpd.job_worker.start()
    return httpd


def serve(database_path: Path | str, **kwargs) -> None:
    httpd = create_server(database_path, start_worker=False, **kwargs)
    host, port = httpd.server_address[:2]
    print(f"EJU question bank server running at http://{host}:{port}")
    if httpd.admin_token: print("Remote access token is configured; local access needs no token")
    import subprocess,sys
    worker=subprocess.Popen([sys.executable,'-m','eju_bank.worker','--database',str(httpd.database.path),'--workspace',str(httpd.content_workspace.root),'--media-dir',str(httpd.asset_store.root)])
    try:
        httpd.serve_forever()
    finally:
        worker.terminate()
        try:worker.wait(timeout=10)
        except subprocess.TimeoutExpired:worker.kill();worker.wait()
        httpd.server_close()
        httpd.database.close()
