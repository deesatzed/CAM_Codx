"""Mode detection: connected vs standalone vs degraded.

See build_specs.md §1.3. The active mode is detected once at startup and
is immutable for the process lifetime.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from claw_codex_mcp.db import detect_mode, ModeInfo


def test_standalone_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    info = detect_mode()
    assert info.mode == "standalone"
    assert info.corpus_status == "absent"
    assert info.db_path is None


def test_standalone_when_path_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing = tmp_path / "no_such.db"
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(missing))
    info = detect_mode()
    assert info.mode == "standalone"
    assert info.corpus_status == "absent"


def test_connected_with_real_slice(
    monkeypatch: pytest.MonkeyPatch, slice_db_path: Path
) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(slice_db_path))
    info = detect_mode()
    assert info.mode == "connected"
    assert info.corpus_status == "connected"
    assert info.db_path == slice_db_path


def test_mode_info_is_immutable() -> None:
    info = ModeInfo(mode="standalone", corpus_status="absent", db_path=None,
                    outcome_db_path=Path("/tmp/x.db"), vec_available=False)
    with pytest.raises(Exception):
        info.mode = "connected"  # frozen
