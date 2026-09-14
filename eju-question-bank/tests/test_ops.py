import tempfile
from pathlib import Path
from eju_bank.ops import run_doctor, check_database, create_backup, verify_backup, restore_backup
from eju_bank.db import Database
from eju_bank.constants import DATABASE_SCHEMA_VERSION

def test_run_doctor():
    res = run_doctor()
    assert res["status"] in ("passed", "warning")
    assert len(res["checks"]) >= 5

def test_check_database(tmp_path):
    db_file = tmp_path / "test.db"
    db = Database(db_file)
    db.close()
    chk = check_database(db_file)
    assert chk["status"] == "passed"
    assert chk["foreignKeyViolations"] == 0
    assert chk["schemaVersion"] == DATABASE_SCHEMA_VERSION

def test_backup_create_verify_restore(tmp_path):
    db_file = tmp_path / "test.db"
    db = Database(db_file)
    db.close()
    
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "sample.txt").write_text("sample content")
    
    inv_file = tmp_path / "content-inventory.json"
    inv_file.write_text('{"schemaVersion": 1, "items": []}')
    
    out_dir = tmp_path / "backups"
    bk_file = create_backup(
        database_path=db_file,
        inventory_path=inv_file,
        media_dir=media_dir,
        output_dir=out_dir
    )
    assert bk_file.exists()
    
    verify_res = verify_backup(bk_file)
    assert verify_res["valid"] is True
    assert verify_res["hasDatabase"] is True
    assert verify_res["hasInventory"] is True
    
    restore_dir = tmp_path / "restored"
    restore_res = restore_backup(bk_file, restore_dir)
    assert restore_res["status"] == "restored"
    assert (restore_dir / "eju.db").exists()
    assert (restore_dir / "content-inventory.json").exists()
