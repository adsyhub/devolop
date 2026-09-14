from conftest import install_fixture_media
import json
import sqlite3
import zipfile
from pathlib import Path
import pytest
import eju_bank.migrations as migrations
from eju_bank.db import Database
from eju_bank.constants import DATABASE_SCHEMA_VERSION
from eju_bank.errors import DoctorError, MigrationError
from eju_bank.ops import create_backup, verify_backup, restore_backup


def legacy_connection(path):
    conn = sqlite3.connect(path)
    conn.executescript(migrations.MIGRATION_V1.replace("'IN_PROGRESS','PAUSED','SUBMITTED','ABANDONED'", "'IN_PROGRESS','SUBMITTED'"))
    conn.execute("INSERT INTO papers VALUES ('p','code','title','now')")
    conn.execute("INSERT INTO paper_versions VALUES ('pv','p',1,'rev','PUBLISHED','PRIVATE','{}','now','now')")
    conn.execute("INSERT INTO questions VALUES ('q','key','now')")
    conn.execute("INSERT INTO practice_sessions VALUES ('s','pv','PRACTICE','[]','SUBMITTED','now','now')")
    conn.execute("INSERT INTO responses VALUES ('s','q','{}','now')")
    conn.execute("INSERT INTO results VALUES ('s','{\"old\":true}','now')")
    conn.commit()
    return conn


def test_legacy_migration_preserves_answers_and_results(tmp_path):
    conn = legacy_connection(tmp_path / 'old.db')
    try:
        assert migrations.migrate_database(conn) == DATABASE_SCHEMA_VERSION
        assert migrations.migrate_database(conn) == DATABASE_SCHEMA_VERSION
        assert conn.execute('SELECT result_json FROM results').fetchone()[0] == '{"old":true}'
        assert conn.execute('SELECT count(*) FROM responses').fetchone()[0] == 1
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
    finally:
        conn.close()


def test_failed_migration_rolls_back_every_change(tmp_path, monkeypatch):
    conn = legacy_connection(tmp_path / 'old.db')
    before = conn.execute("SELECT sql FROM sqlite_master WHERE name='practice_sessions'").fetchone()[0]
    monkeypatch.setattr(migrations, 'MIGRATION_V2_ADDITIONS', 'CREATE TABLE temporary_table(x); INVALID SQL;')
    with pytest.raises(sqlite3.Error): migrations.migrate_database(conn)
    assert conn.execute("SELECT sql FROM sqlite_master WHERE name='practice_sessions'").fetchone()[0] == before
    assert not conn.execute("SELECT 1 FROM sqlite_master WHERE name='temporary_table'").fetchone()
    assert conn.execute('SELECT count(*) FROM responses').fetchone()[0] == 1
    conn.close()


def test_wal_backup_restores_committed_rows(tmp_path):
    db = Database(tmp_path / 'source.db')
    db.connection.execute('PRAGMA journal_mode=WAL')
    paper = json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    install_fixture_media(db.path.parent / 'media')
    db.publish(paper, channel='PUBLIC')
    sid = db.create_session(paper['paperId'], ['PHYSICS_JA'])['sessionId']
    db.submit_session(sid)
    inventory = tmp_path / 'inventory.json'; inventory.write_text('{"items": []}')
    backup = create_backup(database_path=db.path, inventory_path=inventory, output_dir=tmp_path / 'backups')
    assert verify_backup(backup)['valid']
    restore_backup(backup, tmp_path / 'restored')
    restored = Database(tmp_path / 'restored/eju.db')
    try:
        assert restored.get_result(sid)['objectiveTotal'] == 1
        assert restored.get_session(sid)['status'] == 'SUBMITTED'
    finally:
        restored.close(); db.close()


def test_bad_backup_never_overwrites_target(tmp_path):
    bad = tmp_path / 'bad.zip'
    with zipfile.ZipFile(bad, 'w') as z: z.writestr('unrelated.txt', 'x')
    target = tmp_path / 'target';target.mkdir();(target / 'keep.txt').write_text('original')
    with pytest.raises(DoctorError): verify_backup(bad)
    with pytest.raises(DoctorError): restore_backup(bad, target, overwrite=True)
    assert (target / 'keep.txt').read_text() == 'original'


def test_media_reference_missing_rejects_backup(tmp_path):
    db = Database(tmp_path / 'test.db')
    paper = json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    install_fixture_media(db.path.parent / 'media')
    db.publish(paper, channel='PUBLIC')
    for media in (tmp_path/'media').rglob('*.png'): media.unlink()
    inventory = tmp_path / 'inventory.json';inventory.write_text('{"items": []}')
    try:
        with pytest.raises(DoctorError, match='media'):
            create_backup(database_path=db.path, inventory_path=inventory, output_dir=tmp_path / 'backups')
        assert not list((tmp_path / 'backups').glob('*.zip'))
    finally:
        db.close()
