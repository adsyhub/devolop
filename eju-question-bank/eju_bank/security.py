"""Security boundaries, host/origin validation, token checks and payload sanitization."""

from __future__ import annotations

import copy
import os
import re
import secrets
from typing import Any
from urllib.parse import urlparse

from .errors import SecurityError

_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "[::1]"})


def _extract_hostname(host_header: str | None) -> str:
    if not host_header or any(c.isspace() or c in "/\\?#@" for c in host_header):
        raise SecurityError("Invalid Host header")
    try:
        parsed = urlparse("//" + host_header)
        port = parsed.port
        hostname = parsed.hostname
    except ValueError as exc:
        raise SecurityError("Invalid Host header") from exc
    if not hostname:
        raise SecurityError("Missing Host header")
    return hostname.lower()


def validate_host(host_header, *, allow_remote=False, host_allowlist=None):
    hostname = _extract_hostname(host_header)
    if allow_remote:
        if not host_allowlist or hostname not in host_allowlist:
            raise SecurityError("Host is not in the configured allowlist")
    elif hostname not in _LOOPBACK_HOSTS:
        raise SecurityError("Server is restricted to local loopback access")


def validate_origin(origin_header, method, *, allow_remote=False, allowed_origins=None, expected_host=None):
    if not origin_header:
        return
    parsed = urlparse(origin_header)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.path or parsed.query or parsed.fragment:
        raise SecurityError("Invalid request Origin")
    if allow_remote:
        if not allowed_origins or origin_header not in allowed_origins:
            raise SecurityError("Origin is not in the configured allowlist")
    elif parsed.hostname not in _LOOPBACK_HOSTS or (expected_host and parsed.netloc.lower() != expected_host.lower()):
        raise SecurityError("Cross-origin request blocked")


def verify_admin_token(auth_header: str | None, required_token: str | None = None) -> None:
    token = required_token or os.environ.get("EJU_ADMIN_TOKEN")
    if not token:
        # If no admin token is configured in local loopback mode, allow local admin
        return
    if not auth_header:
        raise SecurityError("Admin authorization header required")
    parts = auth_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise SecurityError("Authorization must be 'Bearer <token>'")
    if not secrets.compare_digest(parts[1], token):
        raise SecurityError("Invalid admin token")


def sanitize_paper_for_learner(paper: dict[str, Any]) -> dict[str, Any]:
    """Explicit delivery DTO: no source evidence, answer ledger or review metadata."""
    allowed = {
        'schemaVersion','examFamily','paperId','stableCode','title','session','subject','language',
        'syllabusId','syllabusVersion','completeness','availableModes','questionCount','contentKind',
        'forms','formCode','spec','groups','groupCode','materials','questions','atomic','materialRefs',
        'questionId','questionVersionId','localKey','printedLabel','stemAst','options','key','contentAst',
        'answerSpec','type','slot','allowedTokens','slots','rubricId','minLength','maxLength','suggestedMinLength','suggestedMaxLength',
        'value','latex','alt','caption','assetId','children','rows','cells','header','rowspan','colspan','rowSpan','colSpan',
        'base','ruby','reading','label','width','height','topicTags','sectionCode','sectionId','sections','questionRefs',
        'durationSec','duration_sec','name','name_ja','name_en','course','shared_timing_group','subject_code',
        'sourcePaperId','sourcePaperVersionId','sourceSession','sourceVersions','paperVersionId',
        # 这份卷的把关程度与缺口，学习者有权知道：它既不是原卷证据也不是答案。
        'reviewGrade','missingContentReasons','reviewScope',
    }
    def clean(value):
        if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k in allowed}
        if isinstance(value,list):return [clean(v) for v in value]
        return copy.deepcopy(value)
    result=clean(paper)
    source=paper.get('source',{})
    if isinstance(source,dict):
        result['source']={k:copy.deepcopy(source[k]) for k in ['sourceId','examFamily','session','subject','language','syllabusVersion'] if k in source}
        result['source']['rights']={'status':source.get('rights',{}).get('status','UNKNOWN')}
    return result
