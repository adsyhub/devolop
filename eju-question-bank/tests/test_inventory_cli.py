import subprocess
import sys
import json
from pathlib import Path
from eju_bank.inventory import inventory_status_summary, load_inventory

def test_inventory_status_summary():
    inv = load_inventory()
    summary = inventory_status_summary()
    assert summary["total"] == len(inv["items"])
    assert "completionRate" in summary
    assert "byStatus" in summary

def test_cli_subcommands():
    # 1. doctor
    p = subprocess.run([sys.executable, "-m", "eju_bank.cli", "doctor"], capture_output=True, text=True)
    assert p.returncode == 0
    data = json.loads(p.stdout)
    assert data["status"] in ("passed", "warning")

    # 2. db check
    p = subprocess.run([sys.executable, "-m", "eju_bank.cli", "db", "check"], capture_output=True, text=True)
    assert p.returncode == 0
    data = json.loads(p.stdout)
    assert data["status"] == "passed"

    # 3. inventory status
    p = subprocess.run([sys.executable, "-m", "eju_bank.cli", "inventory", "status"], capture_output=True, text=True)
    assert p.returncode == 0
    data = json.loads(p.stdout)
    assert data["total"] >= 1
