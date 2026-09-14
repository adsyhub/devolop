"""ERR-001A: the minimal error object every Phase 0 blocking path returns.

The plan asks for one shape, landed before the feature surface grows, so that
blocking failures are explainable and reportable instead of a bare stack trace::

    {code, stage, retryable, userAction, diagnosticId}

``diagnosticId`` is a short random handle the user can quote. It is deliberately
meaningless on its own: correlating it with a log line requires local access, so
quoting one in a bug report discloses nothing.

Nothing here may carry a stack trace, username, absolute path, Host header,
session token, or learning content — those are exactly what leaks when an error
page is screenshotted into a chat.
"""

from __future__ import annotations

import secrets
from dataclasses import asdict, dataclass
from typing import Any

# Stable codes for the P0 blocking classes named in the plan. Extending this list
# is expected; renaming an existing code is a breaking change.
E_COURSE_QUALITY = "E-COURSE-QUALITY"
E_DB_MIGRATION = "E-DB-MIGRATION"
E_SEC = "E-SEC"
E_CACHE = "E-CACHE"
E_IMPORT = "E-IMPORT"


@dataclass(frozen=True)
class AppError:
    code: str
    stage: str
    retryable: bool
    userAction: str
    diagnosticId: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_diagnostic_id() -> str:
    return f"d_{secrets.token_hex(6)}"


def make_error(code: str, stage: str, *, retryable: bool, user_action: str) -> AppError:
    return AppError(
        code=code,
        stage=stage,
        retryable=retryable,
        userAction=user_action,
        diagnosticId=new_diagnostic_id(),
    )
