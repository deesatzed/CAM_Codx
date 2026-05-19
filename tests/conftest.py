"""Shared fixtures for claw_codex_mcp tests.

The slice DB is a real SQLite file with real rows copied from the live
CAM_CAM/data/claw.db at the SHA pinned in baselines/manifest.json. No
mocked data per workspace policy.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SLICE_DB = FIXTURE_DIR / "claw_slice.db"


@pytest.fixture(scope="session")
def slice_db_path() -> Path:
    if not SLICE_DB.exists():
        pytest.skip(
            f"slice DB missing at {SLICE_DB}; build it with "
            f"`python tools/build_slice_db.py` (Task 3.2)"
        )
    return SLICE_DB


@pytest.fixture
def slice_conn(slice_db_path: Path):
    conn = sqlite3.connect(f"file:{slice_db_path}?mode=ro", uri=True)
    try:
        yield conn
    finally:
        conn.close()
