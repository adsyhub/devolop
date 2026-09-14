"""Operations, environment doctor, database integrity checks and backup/restore."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Any

from .constants import DATABASE_SCHEMA_VERSION
from .errors import DoctorError, MigrationError
from .migrations import get_schema_version, migrate_database
from .util import canonical_json, utc_now, write_json


def run_doctor(*, database_path: Path | None = None, media_dir: Path | None = None) -> dict[str, Any]:
    """Inspects environment, dependencies, storage and database readiness."""
    db_path = (database_path or Path("library/eju.db")).expanduser().resolve()
    m_dir = (media_dir or Path("library/media")).expanduser().resolve()

    checks: list[dict[str, Any]] = []

    # 1. Python version
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 11)
    checks.append({
        "name": "python_version",
        "status": "passed" if py_ok else "failed",
        "details": f"Python {py_ver} (required >= 3.11)",
    })

    # 2. PyMuPDF
    try:
        import pymupdf
        checks.append({
            "name": "pymupdf",
            "status": "passed",
            "details": f"PyMuPDF {pymupdf.__version__} installed",
        })
    except ImportError:
        checks.append({
            "name": "pymupdf",
            "status": "failed",
            "details": "PyMuPDF not installed (required for PDF probe/render/cropping)",
        })

    # 3. Soundfile / Audio
    try:
        import soundfile as sf
        checks.append({
            "name": "soundfile",
            "status": "passed",
            "details": f"soundfile {sf.__version__} installed",
        })
    except ImportError:
        checks.append({
            "name": "soundfile",
            "status": "warning",
            "details": "soundfile not installed (optional for audio duration probing)",
        })

    # 4. Pillow / Image
    try:
        from PIL import Image
        checks.append({
            "name": "pillow",
            "status": "passed",
            "details": "Pillow installed",
        })
    except ImportError:
        checks.append({
            "name": "pillow",
            "status": "warning",
            "details": "Pillow not installed",
        })

    # 5. Media directory
    m_ok = m_dir.exists() and os.access(m_dir, os.W_OK)
    checks.append({
        "name": "media_directory",
        "status": "passed" if m_ok else "warning",
        "details": f"Path: {m_dir} (writable: {m_ok})",
    })

    # 6. Database schema check
    if db_path.is_file():
        try:
            conn = sqlite3.connect(db_path)
            ver = get_schema_version(conn)
            fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
            conn.close()
            db_status = "passed" if ver == DATABASE_SCHEMA_VERSION and not fk_check else "warning"
            checks.append({
                "name": "database_schema",
                "status": db_status,
                "details": f"Version: {ver}/{DATABASE_SCHEMA_VERSION}, FK violations: {len(fk_check)}",
            })
        except Exception as exc:
            checks.append({
                "name": "database_schema",
                "status": "failed",
                "details": f"Database check error: {exc}",
            })
    else:
        checks.append({
            "name": "database_schema",
            "status": "warning",
            "details": f"Database file not yet created at {db_path}",
        })

    # 7. Disk space check
    try:
        disk_stat = shutil.disk_usage(db_path.parent if db_path.exists() else Path("."))
        free_gib = round(disk_stat.free / (1024 ** 3), 2)
        space_ok = free_gib >= 1.0
        checks.append({
            "name": "disk_space",
            "status": "passed" if space_ok else "warning",
            "details": f"Free disk space: {free_gib} GiB",
        })
    except Exception as exc:
        checks.append({
            "name": "disk_space",
            "status": "warning",
            "details": f"Unable to query disk space: {exc}",
        })

    all_passed = all(c["status"] == "passed" for c in checks)
    has_failed = any(c["status"] == "failed" for c in checks)
    return {
        "status": "failed" if has_failed else ("passed" if all_passed else "warning"),
        "checks": checks,
        "timestamp": utc_now(),
    }


def check_database(database_path: Path | str) -> dict[str, Any]:
    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise DoctorError(f"Database file does not exist: {path}")

    conn = sqlite3.connect(path)
    try:
        ver = get_schema_version(conn)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        papers_count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        versions_count = conn.execute("SELECT COUNT(*) FROM paper_versions").fetchone()[0]
        questions_count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        sessions_count = conn.execute("SELECT COUNT(*) FROM practice_sessions").fetchone()[0]

        return {
            "databasePath": str(path),
            "schemaVersion": ver,
            "expectedVersion": DATABASE_SCHEMA_VERSION,
            "integrityCheck": integrity,
            "foreignKeyViolations": len(fk_violations),
            "statistics": {
                "papers": papers_count,
                "paperVersions": versions_count,
                "questions": questions_count,
                "sessions": sessions_count,
            },
            "status": "passed" if integrity == "ok" and not fk_violations else "failed",
        }
    finally:
        conn.close()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(*, database_path=None, inventory_path=None, media_dir=None, output_dir=None, workspace_root=None, mode="LEARNING") -> Path:
    import tempfile
    if mode not in {'LEARNING','FULL'}:raise DoctorError('Invalid backup mode')
    db_path = Path(database_path or 'library/eju.db').expanduser().resolve()
    inv_path = Path(inventory_path or 'content/content-inventory.json').expanduser().resolve()
    m_dir = Path(media_dir).expanduser().resolve() if media_dir else db_path.parent / 'media'
    out_dir = Path(output_dir).expanduser().resolve() if output_dir else db_path.parent / 'backups'
    if not db_path.is_file() or not inv_path.is_file():
        raise DoctorError('A database and content inventory are required for backup')
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().replace(':', '-').replace('.', '-')
    target = out_dir / f'eju_backup_{stamp}.zip'
    temporary = target.with_suffix('.zip.tmp')
    try:
        with tempfile.TemporaryDirectory(prefix='eju-snapshot-') as work:
            snapshot = Path(work) / 'eju.db'
            src = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
            dst = sqlite3.connect(snapshot)
            try:
                src.backup(dst)
            finally:
                src.close()
                dst.close()
            inventory_snapshot=Path(work)/'content-inventory.json'
            shutil.copyfile(inv_path,inventory_snapshot)
            files = {'eju.db': snapshot, 'content-inventory.json': inventory_snapshot}
            if mode=='FULL':
                root=Path(workspace_root or (db_path.parent.parent if db_path.parent.name=='library' else db_path.parent)).resolve()
                for directory in ['work','sources','config','content']:
                    for path in (root/directory).rglob('*'):
                        if path.is_symlink():raise DoctorError('Full backup does not accept symbolic links')
                        if path.is_file() and not path.name.endswith('.tmp'):
                            relative=path.relative_to(root);copied=Path(work)/'production'/relative
                            copied.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,copied)
                            files[relative.as_posix()]=copied
            if m_dir.exists():
                for path in sorted(m_dir.rglob('*')):
                    if path.is_symlink():
                        raise DoctorError('Media backup does not accept symbolic links')
                    if path.is_file():
                        files['media/' + path.relative_to(m_dir).as_posix()] = path
            snapshot_conn = sqlite3.connect(snapshot)
            try:
                snapshot_version = get_schema_version(snapshot_conn)
            finally:
                snapshot_conn.close()
            manifest = {'backupVersion': 2, 'createdAt': utc_now(), 'hasDatabase': True,
                        'hasInventory': True, 'hasMedia': m_dir.is_dir(),
                        'databaseSchemaVersion': snapshot_version,'mode':mode,'capabilities':['LEARNING','HISTORY']+(['SOURCE_REVIEW','PRODUCTION'] if mode=='FULL' else []), 'files': {}}
            with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for name, path in files.items():
                    manifest['files'][name] = {'sha256': _sha_file(path), 'sizeBytes': path.stat().st_size}
                    archive.write(path, name)
                archive.writestr('backup-manifest.json', canonical_json(manifest))
            verify_backup(temporary)
            os.replace(temporary, target)
        conn = sqlite3.connect(db_path)
        try:
            digest = _sha_file(target)
            conn.execute('INSERT INTO backup_history VALUES (?,?,?,?,?,?)',
                         ('bk_' + digest[:24], str(target), target.stat().st_size, digest, canonical_json(manifest), utc_now()))
            conn.commit()
        finally:
            conn.close()
        return target
    finally:
        temporary.unlink(missing_ok=True)


def _extract_verified(backup_path: Path, output: Path) -> dict:
    from pathlib import PurePosixPath
    from .audit import iter_questions
    with zipfile.ZipFile(backup_path) as archive:
        entries = archive.infolist()
        if len(entries) > 100_000 or sum(e.file_size for e in entries) > 20 * 1024**3:
            raise DoctorError('Backup exceeds entry or size limits')
        names = [e.filename for e in entries]
        if len(names) != len(set(names)):
            raise DoctorError('Duplicate entries in backup')
        for entry in entries:
            name = PurePosixPath(entry.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in entry.filename or ':' in entry.filename:
                raise DoctorError('Invalid backup entry path')
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise DoctorError('Symbolic links are not allowed in backup')
        if not {'eju.db', 'content-inventory.json', 'backup-manifest.json'} <= set(names):
            raise DoctorError('Backup is missing database, inventory or manifest')
        manifest = json.loads(archive.read('backup-manifest.json'))
        if manifest.get('backupVersion') not in {1, 2}:
            raise DoctorError('Unsupported backup version')
        if manifest['backupVersion'] == 2 and set(manifest.get('files', {})) != set(names) - {'backup-manifest.json'}:
            raise DoctorError('Backup manifest file list mismatch')
        for entry in entries:
            path = output / entry.filename
            if entry.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, path.open('wb') as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            if manifest['backupVersion'] == 2 and entry.filename != 'backup-manifest.json':
                expected = manifest['files'][entry.filename]
                if _sha_file(path) != expected['sha256'] or path.stat().st_size != expected['sizeBytes']:
                    raise DoctorError('Backup file checksum mismatch')
    inventory = json.loads((output / 'content-inventory.json').read_text())
    if not isinstance(inventory, dict) or not isinstance(inventory.get('items'), list):
        raise DoctorError('Invalid inventory in backup')
    conn = sqlite3.connect(f'file:{output}/eju.db?mode=ro', uri=True)
    try:
        version = get_schema_version(conn)
        if not 1 <= version <= DATABASE_SCHEMA_VERSION:
            raise DoctorError('Unsupported database version in backup')
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchone():
            raise DoctorError('Database in backup is not consistent')
        # Legacy papers can have media references even before assets were registered.
        refs = set()
        def walk(value):
            if isinstance(value, dict):
                if value.get('assetId'): refs.add(value['assetId'])
                for child in value.values(): walk(child)
            elif isinstance(value, list):
                for child in value: walk(child)
        for row in conn.execute('SELECT payload_json FROM paper_versions'):
            walk(json.loads(row[0]))
        tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table,column in [('page_revisions','contract_json'),('explanation_revisions','payload_json'),('session_state','config_json')]:
            if table in tables:
                for row in conn.execute(f'SELECT {column} FROM {table}'):walk(json.loads(row[0]))
        if 'audio_tracks' in tables:
            for row in conn.execute('SELECT asset_id,cues_json FROM audio_tracks'):refs.add(row[0]);walk(json.loads(row[1]))
        for asset_id in refs:
            if not isinstance(asset_id, str) or len(asset_id) != 64 or any(c not in '0123456789abcdef' for c in asset_id):
                raise DoctorError('Invalid media reference in backup')
            media_files = list((output / 'media' / asset_id[:2]).glob(asset_id + '.*'))
            if not media_files or any(_sha_file(f) != asset_id for f in media_files):
                raise DoctorError('Referenced media is missing or damaged')
    finally:
        conn.close()
    return {'manifest': manifest, 'entriesCount': len(names), 'schemaVersion': version}


def verify_backup(backup_path) -> dict:
    import tempfile
    path = Path(backup_path).expanduser().resolve()
    if not path.is_file():
        raise DoctorError('Backup does not exist')
    try:
        with tempfile.TemporaryDirectory(prefix='eju-verify-') as work:
            result = _extract_verified(path, Path(work))
    except (ValueError, KeyError, sqlite3.Error, zipfile.BadZipFile) as exc:
        raise DoctorError('Invalid backup structure or content') from exc
    return {**result, 'path': str(path), 'sizeBytes': path.stat().st_size, 'sha256': _sha_file(path),
            'valid': True, 'hasDatabase': True, 'hasInventory': True}


def restore_backup(backup_path, target_dir, *, overwrite=False) -> dict:
    import tempfile
    path, target = Path(backup_path).expanduser().resolve(), Path(target_dir).expanduser().resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())) and not overwrite:
        raise DoctorError('Restore target is not empty')
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.eju-restore-', dir=target.parent))
    previous = None
    try:
        _extract_verified(path, stage)
        conn = sqlite3.connect(stage / 'eju.db')
        try:
            migrate_database(conn)
        finally:
            conn.close()
        inventory_dir=stage/'content';inventory_dir.mkdir(exist_ok=True)
        shutil.copyfile(stage/'content-inventory.json',inventory_dir/'content-inventory.json')
        if target.exists():
            previous = target.with_name(target.name + '.previous-' + utc_now().replace(':', '-'))
            os.replace(target, previous)
        try:
            os.replace(stage, target)
        except Exception:
            if previous is not None:
                os.replace(previous, target)
            raise
        return {'status': 'restored', 'sourceBackup': str(path), 'targetDir': str(target),
                'previousTarget': str(previous) if previous else None, 'restoredAt': utc_now()}
    finally:
        if stage.exists(): shutil.rmtree(stage)
