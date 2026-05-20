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


async def test_provenance_returns_links_when_available(
    connected_info: ModeInfo, slice_conn
) -> None:
    """For an id that participates in methodology_links, the response includes them."""
    # Find a real methodology id that has at least one link in the slice.
    row = slice_conn.execute(
        "SELECT m.id FROM methodologies m "
        "WHERE m.id IN (SELECT source_id FROM methodology_links) "
        "   OR m.id IN (SELECT target_id FROM methodology_links) "
        "LIMIT 1"
    ).fetchone()
    assert row is not None, "slice must contain at least one linked methodology"
    linked_id = row[0]
    out = await handle_provenance(
        CamProvenanceInput(methodology_id=linked_id, include_links=True),
        connected_info,
    )
    assert out.found is True
    assert len(out.links) >= 1, f"expected >=1 link; got {len(out.links)}"
    link = out.links[0]
    assert link.direction in ("parent", "child")
    assert link.target_id
    assert link.link_type
    assert isinstance(link.strength, float)
