"""cam_provenance handler tests. build_specs.md §3.2."""

from __future__ import annotations

from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo
from claw_codex_mcp.schemas import CamProvenanceInput
from claw_codex_mcp.tools.provenance import handle_provenance


@pytest.fixture
def connected_info(slice_db_path: Path) -> ModeInfo:
    return ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=False,
    )


async def test_provenance_resolves_real_id(connected_info: ModeInfo, slice_conn) -> None:
    real_id = slice_conn.execute("SELECT id FROM methodologies LIMIT 1").fetchone()[0]
    out = await handle_provenance(CamProvenanceInput(methodology_id=real_id), connected_info)
    assert out.found is True
    assert out.methodology_id == real_id
    assert out.provenance is not None
    assert out.solution_code is not None


async def test_provenance_unknown_id_returns_not_found(connected_info: ModeInfo) -> None:
    out = await handle_provenance(
        CamProvenanceInput(methodology_id="no-such-id-zzz"), connected_info
    )
    assert out.found is False
    assert out.provenance is None
    assert out.corpus_status == "connected"


async def test_provenance_standalone_returns_not_found(tmp_path: Path) -> None:
    info = ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "x.db", vec_available=False,
    )
    out = await handle_provenance(
        CamProvenanceInput(methodology_id="anything"), info
    )
    assert out.found is False
    assert out.corpus_status == "absent"
