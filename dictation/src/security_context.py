"""SEC-001: decide whether a request to the local learning API is really same-origin.

The previous check derived the expected origin from the request's own ``Host``
header::

    expected = f"http://{self.headers.get('Host')}"
    return secrets.compare_digest(origin, expected)

That is self-certifying, and it is the exact shape DNS rebinding exploits. A page
on ``evil.com`` whose DNS answer points at ``127.0.0.1`` reaches this server with
``Host: evil.com`` and ``Origin: http://evil.com``; the two agree, so the check
passes and the attacker can read and write the learner's vocabulary and notes.
Reproduced against the pre-fix server, so this is a live hole, not a theoretical
one — see ``tests/test_security_origin.py``.

The replacement never infers anything from the request:

1. ``Host`` must be one of the loopback authorities the server actually bound to.
   A rebound request carries the attacker's own hostname and fails here.
2. Every ``/api/*`` call — reads included, since vocabulary and notes are personal
   data — carries a 256-bit session token the page can only obtain same-origin.
3. Writes additionally require an allowed ``Origin`` and non-cross-site Fetch
   Metadata, so a stolen-token replay from another site still fails.

Scope, stated plainly because the plan requires it: this stops remote web pages,
DNS rebinding and stray local clients. It does not stop a malicious process, a
browser extension, or malware running as the same user — those already have the
user's own filesystem access and are outside this boundary.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from urllib.parse import urlsplit

TOKEN_HEADER = "X-Dictation-Token"
TOKEN_ENV_VAR = "DICTATION_SESSION_TOKEN"

# Endpoints reachable without a token. Deliberately tiny:
#   - the bootstrap handshake itself (it is how the page gets a token),
#   - a liveness probe carrying no personal data at all.
PUBLIC_API_PATHS = frozenset({"/api/session/bootstrap", "/api/health"})


def generate_token() -> str:
    return secrets.token_hex(32)  # 256 bits


def token_from_environment() -> str:
    """Read the launcher-provided token, removing it from the environment.

    The launcher passes the token through an inherited environment variable and
    this process erases it immediately, so it does not leak into child processes
    or anything that dumps ``os.environ`` for diagnostics. When the server is run
    directly (no launcher), a fresh token is generated instead: the page still
    gets it through the same-origin bootstrap handshake.
    """
    token = os.environ.pop(TOKEN_ENV_VAR, "")
    return token if token else generate_token()


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str = ""


ALLOWED = Decision(True)


class SecurityContext:
    """Authorizes local API requests against the address the server really bound to."""

    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        *,
        allow_forwarded_loopback_ports: bool = False,
    ) -> None:
        self.port = port
        self.token = token
        self.allow_forwarded_loopback_ports = allow_forwarded_loopback_ports
        # Built from our own bind address, never from a request header. `localhost`
        # is included because browsers will use whichever name the user typed, and
        # both names resolve to the loopback interface we are listening on.
        self.allowed_hosts = frozenset(
            {
                f"127.0.0.1:{port}",
                f"localhost:{port}",
                f"[::1]:{port}",
            }
        )
        self.allowed_origins = frozenset(f"http://{authority}" for authority in self.allowed_hosts)

    # ---- individual checks ----

    def host_allowed(self, host_header: str | None) -> bool:
        if not host_header:
            return False
        authority = host_header.strip().lower()
        if authority in self.allowed_hosts:
            return True
        # VS Code Remote/Dev Containers can forward the bound port to a
        # different loopback port on the desktop. The studio opts into this
        # narrow exception; arbitrary hostnames are still rejected, so a DNS
        # rebinding request such as Host: evil.example cannot use it.
        return self.allow_forwarded_loopback_ports and self._loopback_authority(authority) is not None

    def token_valid(self, token_header: str | None) -> bool:
        if not token_header:
            return False
        return secrets.compare_digest(token_header.strip(), self.token)

    def origin_allowed(self, origin_header: str | None, host_header: str | None = None) -> bool:
        if not origin_header:
            # Non-browser clients (curl, the launcher's readiness probe) send no
            # Origin. They are still required to present a valid token, checked
            # separately, so an absent Origin is not on its own an escalation.
            return True
        origin = origin_header.strip().lower()
        if origin in self.allowed_origins:
            return True
        if not self.allow_forwarded_loopback_ports or not host_header:
            return False
        try:
            parsed = urlsplit(origin)
        except ValueError:
            return False
        if (
            parsed.scheme != "http"
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.username is not None
            or parsed.password is not None
        ):
            return False
        # A write through a forwarded port must still be same-origin: the
        # browser's Origin authority must exactly match its Host authority.
        origin_authority = self._loopback_authority(parsed.netloc)
        host_authority = self._loopback_authority(host_header)
        return origin_authority is not None and origin_authority == host_authority

    @staticmethod
    def _loopback_authority(authority: str | None) -> tuple[str, int | None] | None:
        if not authority:
            return None
        raw = authority.strip().lower()
        try:
            parsed = urlsplit(f"//{raw}")
            port = parsed.port
        except ValueError:
            return None
        if (
            parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        ):
            return None
        return parsed.hostname, port

    def fetch_metadata_ok(self, site_header: str | None) -> bool:
        """Reject explicitly cross-site requests.

        Browsers that support Fetch Metadata label a request from another site
        `cross-site`. Absence means an older browser or a non-browser client, and
        is not treated as a failure on its own — the Host and token checks are the
        load-bearing ones.
        """
        if not site_header:
            return True
        return site_header.strip().lower() in {"same-origin", "none"}

    # ---- composed policies ----

    def authorize_bootstrap(self, headers) -> Decision:
        """Gate the one endpoint that hands out the token."""
        if not self.host_allowed(headers.get("Host")):
            return Decision(False, "host-not-allowed")
        if not self.fetch_metadata_ok(headers.get("Sec-Fetch-Site")):
            return Decision(False, "cross-site")
        # A token must be fetched by script, not navigated to. Blocking `document`
        # keeps it out of a top-level navigation, an iframe, or anything else that
        # could leave it in history or a cached page.
        destination = (headers.get("Sec-Fetch-Dest") or "").strip().lower()
        if destination and destination not in {"empty", "script"}:
            return Decision(False, "bad-fetch-destination")
        return ALLOWED

    def authorize_api(self, headers, *, method: str, path: str) -> Decision:
        """Gate every other /api/* request, reads included."""
        if not self.host_allowed(headers.get("Host")):
            return Decision(False, "host-not-allowed")
        if path in PUBLIC_API_PATHS:
            return ALLOWED
        if not self.fetch_metadata_ok(headers.get("Sec-Fetch-Site")):
            return Decision(False, "cross-site")
        if not self.token_valid(headers.get(TOKEN_HEADER)):
            return Decision(False, "missing-or-invalid-token")
        if method.upper() not in {"GET", "HEAD"} and not self.origin_allowed(
            headers.get("Origin"), headers.get("Host")
        ):
            return Decision(False, "origin-not-allowed")
        return ALLOWED

    def authorize_static(self, headers) -> Decision:
        """Gate static assets too.

        Course text and audio are not as sensitive as the notebook, but a rebound
        origin should not be able to read the course either, and letting it load
        `app.js` would only give an attacker a same-origin-looking surface to work
        from. The check is Host-only so that ordinary browsing keeps working.
        """
        if not self.host_allowed(headers.get("Host")):
            return Decision(False, "host-not-allowed")
        return ALLOWED
