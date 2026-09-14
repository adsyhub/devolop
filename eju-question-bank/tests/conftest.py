"""Keep the isolated package importable when pytest is launched from the parent repo."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))



def install_fixture_media(directory):
    import shutil
    shutil.copytree(PROJECT_ROOT / "tests/fixtures/media", directory, dirs_exist_ok=True)

# Tests use isolated synthetic workspaces.
import pytest
@pytest.fixture(autouse=True, scope="session")
def isolated_workspace_policy():
    monkeypatch=pytest.MonkeyPatch()
    monkeypatch.setenv("EJU_ALLOW_SYNTHETIC", "1")
    monkeypatch.delenv("EJU_ADMIN_TOKEN", raising=False)

    yield
    monkeypatch.undo()
