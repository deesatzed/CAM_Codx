"""Read and write connection helpers.

build_specs.md §8.3: read connections use PRAGMA query_only=ON; the single
write path serializes through a per-process asyncio.Lock.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from claw_codex_mcp.db import (
    ModeInfo, open_read_conn, write_lock, ensure_outcome_schema,
)


def test_read_conn_is_query_only(slice_db_path: Path) -> None:
    info = ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=True,
    )
    with open_read_conn(info) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("DELETE FROM methodologies")


def test_read_conn_returns_real_row(slice_db_path: Path) -> None:
    info = ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=True,
    )
    with open_read_conn(info) as conn:
        cur = conn.execute("SELECT id FROM methodologies LIMIT 1")
        row = cur.fetchone()
    assert row is not None and isinstance(row[0], str)


@pytest.mark.asyncio
async def test_write_lock_serializes() -> None:
    """Two concurrent acquisitions must serialize."""
    order: list[str] = []

    async def writer(name: str, hold: float) -> None:
        async with write_lock():
            order.append(f"{name}:start")
            await asyncio.sleep(hold)
            order.append(f"{name}:end")

    await asyncio.gather(writer("A", 0.05), writer("B", 0.0))
    # Must be ['A:start', 'A:end', 'B:start', 'B:end'] OR the B-first variant —
    # but never interleaved.
    assert order in (
        ["A:start", "A:end", "B:start", "B:end"],
        ["B:start", "B:end", "A:start", "A:end"],
    ), f"writes interleaved: {order}"


def test_ensure_outcome_schema_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "outcome.db"
    ensure_outcome_schema(target)
    ensure_outcome_schema(target)  # second call must be no-op
    conn = sqlite3.connect(target)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='codex_outcome_log'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_read_conn_blocks_insert(slice_db_path: Path) -> None:
    """Pin read-only enforcement on read connections."""
    info = ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=False,
    )
    with open_read_conn(info) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO methodologies (id, problem_description) VALUES ('x', 'y')"
            )
