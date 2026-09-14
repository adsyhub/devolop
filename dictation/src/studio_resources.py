"""Resource slot management, concurrency limiting, and model dependency readiness.

Coordinates local compute constraints:
- Heavy inference (GPU / local LLM / ASR) is throttled to 1 concurrent slot by default.
- CPU tasks (decompression, OCR preprocessing, audio slicing, hashing) have a bounded pool.
- Model service readiness polling with timeouts and cancellation checks.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import threading
import time
from typing import Any, Callable
import urllib.error
import urllib.request


class ResourceError(Exception):
    """Base exception for resource allocation and service readiness."""


class ResourceTimeoutError(ResourceError):
    """Timed out waiting for an execution resource slot or dependent service."""


class ResourceCancelledError(ResourceError):
    """Slot acquisition or service wait was cancelled."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SlotHolder:
    owner_id: str
    resource_type: str
    acquired_at: str


class SlotManager:
    """Thread-safe resource slot coordinator."""

    def __init__(
        self,
        gpu_concurrency: int = 1,
        cpu_concurrency: int | None = None,
    ) -> None:
        self.gpu_concurrency = max(1, gpu_concurrency)
        resolved_cpu = cpu_concurrency or min(8, max(2, (os.cpu_count() or 4) // 2))
        self.cpu_concurrency = max(1, resolved_cpu)

        self._lock = threading.RLock()
        self._gpu_semaphore = threading.BoundedSemaphore(self.gpu_concurrency)
        self._cpu_semaphore = threading.BoundedSemaphore(self.cpu_concurrency)

        self._active_holders: dict[str, SlotHolder] = {}

    @property
    def gpu_available(self) -> int:
        with self._lock:
            active = sum(1 for h in self._active_holders.values() if h.resource_type == "gpu")
            return max(0, self.gpu_concurrency - active)

    @property
    def cpu_available(self) -> int:
        with self._lock:
            active = sum(1 for h in self._active_holders.values() if h.resource_type == "cpu")
            return max(0, self.cpu_concurrency - active)

    @contextlib.contextmanager
    def acquire(
        self,
        resource_type: str,
        owner_id: str,
        timeout: float | None = 60.0,
        cancel_checker: Callable[[], bool] | None = None,
    ):
        """Acquire a resource slot (gpu or cpu) with timeout and cancellation checks."""
        res = resource_type.lower().strip()
        sem = self._gpu_semaphore if res in {"gpu", "model", "asr", "llm"} else self._cpu_semaphore
        res_key = "gpu" if sem is self._gpu_semaphore else "cpu"

        start_time = time.monotonic()
        acquired = False

        while not acquired:
            if cancel_checker and cancel_checker():
                raise ResourceCancelledError(f"Cancelled while waiting for {res_key} slot")

            step_timeout = 0.5 if timeout is not None else 1.0
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    raise ResourceTimeoutError(
                        f"Timed out after {timeout:.1f}s waiting for {res_key} resource slot"
                    )
                step_timeout = min(step_timeout, remaining)

            acquired = sem.acquire(timeout=step_timeout)

        holder = SlotHolder(
            owner_id=owner_id,
            resource_type=res_key,
            acquired_at=utc_now_iso(),
        )
        with self._lock:
            self._active_holders[owner_id] = holder

        try:
            yield holder
        finally:
            with self._lock:
                self._active_holders.pop(owner_id, None)
            sem.release()

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            gpu_holders = [
                {"ownerId": h.owner_id, "acquiredAt": h.acquired_at}
                for h in self._active_holders.values()
                if h.resource_type == "gpu"
            ]
            cpu_holders = [
                {"ownerId": h.owner_id, "acquiredAt": h.acquired_at}
                for h in self._active_holders.values()
                if h.resource_type == "cpu"
            ]
            return {
                "gpu": {
                    "total": self.gpu_concurrency,
                    "available": self.gpu_available,
                    "activeCount": len(gpu_holders),
                    "holders": gpu_holders,
                },
                "cpu": {
                    "total": self.cpu_concurrency,
                    "available": self.cpu_available,
                    "activeCount": len(cpu_holders),
                    "holders": cpu_holders,
                },
            }


_GLOBAL_SLOT_MANAGER: SlotManager | None = None
_GLOBAL_LOCK = threading.Lock()


def get_slot_manager() -> SlotManager:
    global _GLOBAL_SLOT_MANAGER
    if _GLOBAL_SLOT_MANAGER is None:
        with _GLOBAL_LOCK:
            if _GLOBAL_SLOT_MANAGER is None:
                _GLOBAL_SLOT_MANAGER = SlotManager()
    return _GLOBAL_SLOT_MANAGER


def wait_for_service(
    service_url: str,
    timeout: float = 60.0,
    check_interval: float = 1.0,
    cancel_checker: Callable[[], bool] | None = None,
) -> bool:
    """Probe an HTTP health or models endpoint until it answers or timeout is reached."""
    url = service_url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return True

    probe_url = url
    if not probe_url.endswith("/health") and not probe_url.endswith("/v1/models"):
        probe_url = f"{url.rstrip('/')}/v1/models"

    start_time = time.monotonic()
    req = urllib.request.Request(
        probe_url,
        headers={"User-Agent": "StudioPipeline/1.0", "Accept": "application/json"},
    )

    while True:
        if cancel_checker and cancel_checker():
            raise ResourceCancelledError(f"Wait cancelled for service {service_url}")

        try:
            with urllib.request.urlopen(req, timeout=check_interval) as resp:
                if 200 <= resp.status < 300:
                    return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError):
            pass

        elapsed = time.monotonic() - start_time
        if elapsed >= timeout:
            raise ResourceTimeoutError(
                f"Service {service_url} did not become ready within {timeout:.1f}s"
            )

        time.sleep(min(check_interval, timeout - elapsed))

