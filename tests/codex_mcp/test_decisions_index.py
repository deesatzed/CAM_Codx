"""build_specs.md §3.3 — cross-repo DECISIONS.md FTS5 index."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from claw_codex_mcp.decisions_index import build_index, search_index

FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "sample_decisions"


def test_build_index_discovers_all_decisions_md(tmp_path: Path) -> None:
    index_db = tmp_path / "idx.db"
    n_blocks, n_files = build_index(
        index_db_path=index_db,
        roots=[FIXTURE_ROOT / "repo_a", FIXTURE_ROOT / "repo_b"],
    )
    assert n_files == 2
    assert n_blocks == 3  # 2 in repo_a, 1 in repo_b


def test_search_returns_real_hit(tmp_path: Path) -> None:
    index_db = tmp_path / "idx.db"
    build_index(index_db, [FIXTURE_ROOT])
    hits = search_index(index_db, "mock data", k=5)
    assert len(hits) == 1
    assert "mock" in hits[0]["body"].lower()


def test_rebuild_is_idempotent(tmp_path: Path) -> None:
    index_db = tmp_path / "idx.db"
    build_index(index_db, [FIXTURE_ROOT])
    n1 = sqlite3.connect(index_db).execute(
        "SELECT COUNT(*) FROM decisions_docs"
    ).fetchone()[0]
    build_index(index_db, [FIXTURE_ROOT])  # rebuild
    n2 = sqlite3.connect(index_db).execute(
        "SELECT COUNT(*) FROM decisions_docs"
    ).fetchone()[0]
    assert n1 == n2, "rebuild must be idempotent"
