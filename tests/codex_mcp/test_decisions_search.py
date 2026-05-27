"""cam_decisions_search handler. build_specs.md §3.3."""

from __future__ import annotations

from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo
from claw_codex_mcp.decisions_index import build_index
from claw_codex_mcp.schemas import CamDecisionsSearchInput
from claw_codex_mcp.tools.decisions_search import handle_decisions_search

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_decisions"


@pytest.fixture
def info_with_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModeInfo:
    idx = tmp_path / "decisions_index.db"
    build_index(idx, [FIXTURES])
    monkeypatch.setenv("CAM_CODEX_MCP_DECISIONS_INDEX", str(idx))
    return ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "out.db", vec_available=False,
    )


async def test_search_returns_grounded_hit(info_with_index: ModeInfo) -> None:
    out = await handle_decisions_search(
        CamDecisionsSearchInput(query="mock data"), info_with_index
    )
    assert len(out.results) >= 1
    assert any("mock" in h.snippet.lower() for h in out.results)


async def test_search_degraded_when_index_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DECISIONS_INDEX", str(tmp_path / "no_such.db"))
    info = ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "out.db", vec_available=False,
    )
    out = await handle_decisions_search(
        CamDecisionsSearchInput(query="anything"), info
    )
    assert out.results == []
    assert out.degraded is True
    assert "index missing" in (out.reason or "").lower()


def test_index_path_default_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """GAP-COV-3 line 23: _index_path() fallback when env var is NOT set.

    All other tests set CAM_CODEX_MCP_DECISIONS_INDEX via monkeypatch.  This
    test explicitly removes it so the `else` branch (return DEFAULT_STANDALONE_DIR
    / DEFAULT_INDEX_NAME) is executed.
    """
    from claw_codex_mcp.db import DEFAULT_STANDALONE_DIR
    from claw_codex_mcp.tools.decisions_search import _index_path, DEFAULT_INDEX_NAME

    monkeypatch.delenv("CAM_CODEX_MCP_DECISIONS_INDEX", raising=False)
    result = _index_path()
    assert result == DEFAULT_STANDALONE_DIR / DEFAULT_INDEX_NAME
