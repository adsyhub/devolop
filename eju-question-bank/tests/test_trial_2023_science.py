"""Real artifacts are inspected read-only; practice tests use temporary databases."""
from conftest import install_fixture_media
import json
import sqlite3
from pathlib import Path
import pytest
from eju_bank.db import Database
from eju_bank.errors import ContractError
from eju_bank.audit import prepare_paper


def test_published_2023_science_paper():
    path = Path('library/eju.db')
    if not path.exists():
        pytest.skip('Optional local content is absent')
    with sqlite3.connect(f'file:{path.resolve()}?mode=ro', uri=True) as conn:
        row = conn.execute("SELECT payload_json FROM paper_versions WHERE payload_json LIKE '%2023-2 EJU SCIENCE%' ORDER BY version_number DESC LIMIT 1").fetchone()
    assert row is not None
    paper = json.loads(row[0])
    assert set(f['formCode'] for f in paper['forms']) == {'PHYSICS_JA', 'CHEMISTRY_JA', 'BIOLOGY_JA'}


def test_mock_session_trial(tmp_path):
    paper = json.loads(Path('tests/fixtures/synthetic_paper.json').read_text())
    db = Database(tmp_path / 'test.db')
    try:
        install_fixture_media(db.path.parent / 'media')
        db.publish(paper, channel='PUBLIC')
        sess = db.create_session(paper['paperId'], ['PHYSICS_JA', 'CHEMISTRY_JA'], mode='MOCK')
        assert sess['durationSec'] == 4800
        assert db.submit_session(sess['sessionId'])['objectiveUnanswered'] == 2
        paper['completeness'] = 'PARTIAL'
        paper['availableModes'] = ['PRACTICE']
        db.publish(prepare_paper(paper), channel='PUBLIC')
        with pytest.raises(ContractError, match='mode'):
            db.create_session(paper['paperId'], ['PHYSICS_JA', 'CHEMISTRY_JA'], mode='MOCK')
    finally:
        db.close()
