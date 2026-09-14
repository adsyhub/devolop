"""Dictionary install jobs that outlive the process that started them.

The previous installer kept its whole state in one in-memory dict, so a restart during a
download left the page polling a job the service had no memory of, there was no way to
cancel one, and a failure could only be retried by starting over blindly (LEX-18, §9.4).

State lives in a file beside the dictionary. A job whose file says `running` but whose
thread is gone is reported as `interrupted`, which is a fact the page can act on rather
than a spinner that never resolves.
"""
from __future__ import annotations

import json
import os
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

STAGES = ('queued', 'download', 'build', 'publish', 'complete', 'failed', 'cancelled', 'interrupted')
JOB_NAME = 'install-job.json'


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InstallJobs:
    """One dictionary install at a time, recorded durably."""

    def __init__(self, dictionary_path: Path):
        self.root = Path(dictionary_path).parent
        self.path = self.root / JOB_NAME
        self.lock = threading.RLock()
        self._thread: threading.Thread | None = None

    # ---- durable state ---------------------------------------------------

    def _read(self) -> dict:
        try:
            state = json.loads(self.path.read_text(encoding='utf-8'))
            return state if isinstance(state, dict) else {}
        except (OSError, ValueError):
            return {}

    def _write(self, state: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.root / f'.{JOB_NAME}.tmp'
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, self.path)

    def _update(self, **changes) -> dict:
        with self.lock:
            state = self._read()
            state.update(changes, updatedAt=_now())
            self._write(state)
            return state

    def status(self) -> dict:
        """The job as it stands, reconciled against whether a worker is still alive."""
        with self.lock:
            state = self._read()
            if not state:
                return {'status': 'idle', 'stage': 'queued'}
            running = bool(self._thread and self._thread.is_alive())
            if state.get('status') == 'running' and not running:
                # Nothing is working on it any more. Saying so beats an endless spinner.
                state = self._update(
                    status='interrupted', stage='interrupted',
                    errorCode='interrupted',
                    message='安装在上次运行中被中断（服务重启或进程退出）。可重新开始。',
                )
            state['active'] = running
            state['resumable'] = state.get('status') in {'failed', 'interrupted', 'cancelled'}
            return state

    # ---- control ---------------------------------------------------------

    def start(self, worker) -> dict:
        """Begin an install. Only an explicit request reaches here; lookups never do."""
        with self.lock:
            current = self.status()
            if current.get('status') == 'running':
                return current
            job_id = 'dj_' + secrets.token_hex(8)
            self._write({
                'jobId': job_id, 'status': 'running', 'stage': 'queued',
                'bytes': 0, 'entriesProcessed': 0, 'cancelRequested': False,
                'errorCode': '', 'message': '正在准备下载和建立本地词典索引。',
                'startedAt': _now(), 'updatedAt': _now(),
            })

            def progress(message: str, **detail) -> None:
                changes = {'message': str(message)}
                if 'stage' in detail:
                    changes['stage'] = str(detail['stage'])
                if 'bytes' in detail:
                    changes['bytes'] = int(detail['bytes'])
                if 'entries' in detail:
                    changes['entriesProcessed'] = int(detail['entries'])
                self._update(**changes)

            def cancelled() -> bool:
                return bool(self._read().get('cancelRequested'))

            def run() -> None:
                from dictionary_build import Cancelled
                try:
                    metadata = worker(progress, cancelled)
                    self._update(status='complete', stage='complete', errorCode='',
                                 metadata=metadata, message='词典安装完成。')
                except Cancelled as exc:
                    self._update(status='cancelled', stage='cancelled', errorCode='cancelled',
                                 message=str(exc) or '已取消安装；原词典未改变。')
                except Exception as exc:  # noqa: BLE001 - reported, not swallowed
                    self._update(status='failed', stage='failed',
                                 errorCode=type(exc).__name__,
                                 message=f'安装失败：{exc}。原词典未改变，可重新开始。')

            self._thread = threading.Thread(target=run, daemon=True)
            self._thread.start()
            return self.status()

    def cancel(self) -> dict:
        with self.lock:
            state = self.status()
            if state.get('status') != 'running':
                raise ValueError('当前没有正在进行的安装。')
            # Cooperative: the worker checks between batches, then unwinds without
            # touching the published version.
            return self._update(cancelRequested=True, message='已请求取消，正在收尾。')

    def clear(self) -> dict:
        """Forget a finished job so the page stops reporting it."""
        with self.lock:
            if self.status().get('status') == 'running':
                raise ValueError('安装仍在进行，请先取消。')
            try:
                self.path.unlink()
            except OSError:
                pass
            return {'status': 'idle', 'stage': 'queued'}
