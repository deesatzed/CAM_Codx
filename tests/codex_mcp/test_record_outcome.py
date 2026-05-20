"""cam_record_outcome handler. build_specs.md §3.4 + §5.1.

This is the only write path on the MCP surface. 100% line + branch coverage
is required on db.py write helpers (build_specs.md §8.4).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo, ensure_outcome_schema
from claw_codex_mcp.schemas import CamRecordOutcomeInput
from claw_codex_mcp.tools.record_outcome import handle_record_outcome


def _standalone_info(tmp_path: Path) -> ModeInfo:
    out_db = tmp_path / "outcome.db"
    ensure_outcome_schema(out_db)
    return ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=out_db, vec_available=False,
    )


async def test_record_outcome_writes_row(tmp_path: Path) -> None:
    info = _standalone_info(tmp_path)
    req = CamRecordOutcomeInput(
        methodology_ids=["m1"], task_id="t1", repo="/r1",
        outcome="green", evidence={"test": "ok"},
        run_hash="a" * 16, notes="first",
    )
    out = await handle_record_outcome(req, info)
    assert out.recorded is True
    assert out.duplicate is False
    assert out.outcome_id is not None
    conn = sqlite3.connect(info.outcome_db_path)
    row = conn.execute(
        "SELECT outcome, run_hash FROM codex_outcome_log WHERE run_hash=?",
        (req.run_hash,),
    ).fetchone()
    conn.close()
    assert row == ("green", req.run_hash)


async def test_record_outcome_idempotent_on_run_hash(tmp_path: Path) -> None:
    info = _standalone_info(tmp_path)
    req = CamRecordOutcomeInput(
        methodology_ids=["m1"], task_id="t1", repo="/r1",
        outcome="green", run_hash="b" * 16,
    )
    out1 = await handle_record_outcome(req, info)
    out2 = await handle_record_outcome(req, info)
    assert out1.recorded is True
    assert out2.recorded is False
    assert out2.duplicate is True
    conn = sqlite3.connect(info.outcome_db_path)
    n = conn.execute(
        "SELECT COUNT(*) FROM codex_outcome_log WHERE run_hash=?",
        (req.run_hash,),
    ).fetchone()[0]
    conn.close()
    assert n == 1, "duplicate run_hash must not insert a second row"


async def test_record_outcome_rejects_invalid_outcome() -> None:
    with pytest.raises(Exception):
        CamRecordOutcomeInput(
            methodology_ids=["m1"], task_id="t1", repo="/r1",
            outcome="catastrophic",  # not in literal set
            run_hash="c" * 16,
        )


async def test_record_outcome_standalone_skips_fk_check(tmp_path: Path) -> None:
    """In standalone mode, methodology_ids are accepted as opaque strings."""
    info = _standalone_info(tmp_path)
    req = CamRecordOutcomeInput(
        methodology_ids=["id-not-in-any-corpus"], task_id="t1", repo="/r1",
        outcome="green", run_hash="d" * 16,
    )
    out = await handle_record_outcome(req, info)
    assert out.recorded is True  # no FK check in standalone


# --- Connected-mode coverage (build_specs §8.4: 100% on write path) ---
#
# The 4 contract tests above only exercise standalone mode. Connected mode
# performs an ATTACH DATABASE against the real corpus and FK-checks every
# methodology_id. The tests below exercise both the pass-path and the
# reject-path of that branch using the real claw_slice.db fixture.
#
# The outcome_db_path is a tmp file with ensure_outcome_schema applied —
# NOT the slice DB itself, since the slice DB does not have the outcome
# log table (and per build_specs the slice is a read-only fixture).


def _connected_info(tmp_path: Path, slice_db_path: Path) -> ModeInfo:
    out_db = tmp_path / "outcome.db"
    ensure_outcome_schema(out_db)
    return ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=out_db, vec_available=True,
    )


async def test_record_outcome_connected_accepts_known_methodology_id(
    tmp_path: Path, slice_db_path: Path,
) -> None:
    """Connected mode + a real methodology_id from the slice → recorded=True."""
    info = _connected_info(tmp_path, slice_db_path)
    known_id = sqlite3.connect(
        f"file:{slice_db_path}?mode=ro", uri=True
    ).execute("SELECT id FROM methodologies LIMIT 1").fetchone()[0]
    req = CamRecordOutcomeInput(
        methodology_ids=[known_id], task_id="t-known", repo="/r-known",
        outcome="green", run_hash="e" * 16,
    )
    out = await handle_record_outcome(req, info)
    assert out.recorded is True
    assert out.outcome_id is not None
    assert out.corpus_status == "connected"


async def test_record_outcome_connected_rejects_unknown_methodology_id(
    tmp_path: Path, slice_db_path: Path,
) -> None:
    """Connected mode + an id absent from the corpus → recorded=False."""
    info = _connected_info(tmp_path, slice_db_path)
    req = CamRecordOutcomeInput(
        methodology_ids=["00000000-not-a-real-id-00000000"], task_id="t-x",
        repo="/r-x", outcome="green", run_hash="f" * 16,
    )
    out = await handle_record_outcome(req, info)
    assert out.recorded is False
    assert out.reason is not None
    assert "unknown methodology_id" in out.reason
    # And verify no row was written.
    conn = sqlite3.connect(info.outcome_db_path)
    n = conn.execute(
        "SELECT COUNT(*) FROM codex_outcome_log WHERE run_hash=?",
        (req.run_hash,),
    ).fetchone()[0]
    conn.close()
    assert n == 0
