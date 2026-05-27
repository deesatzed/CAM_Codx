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


def test_build_index_empty_body_block(tmp_path: Path) -> None:
    """GAP-COV-2 line 103: indexed_body = anchor (the `else anchor` branch).

    A block with a heading but no body text exercises the `if body else anchor`
    path — the FTS body becomes just the anchor heading with no trailing content.
    """
    repo = tmp_path / "empty_body_repo"
    repo.mkdir()
    decisions_file = repo / "DECISIONS.md"
    # Block with a heading but an immediately-following heading (empty body).
    decisions_file.write_text(
        "## Headless Decision\n## 2026-01-01 Real Decision\n\nSome body text.\n",
        encoding="utf-8",
    )
    index_db = tmp_path / "idx.db"
    n_blocks, n_files = build_index(index_db, [repo])
    assert n_files == 1
    assert n_blocks == 2
    # The empty-body block should be stored as just the anchor heading.
    conn = sqlite3.connect(index_db)
    rows = conn.execute(
        "SELECT block_anchor, body FROM decisions_docs ORDER BY block_anchor"
    ).fetchall()
    conn.close()
    anchors = {r[0]: r[1] for r in rows}
    assert "Headless Decision" in anchors
    # Body stored as just the anchor text (no trailing newline/content).
    assert anchors["Headless Decision"] == "Headless Decision"


def test_search_with_repo_filter(tmp_path: Path) -> None:
    """GAP-COV-2 lines 116-117: repo_filter SQL branch in search_index."""
    index_db = tmp_path / "idx.db"
    build_index(index_db, [FIXTURE_ROOT / "repo_a", FIXTURE_ROOT / "repo_b"])
    # repo_b contains "mock data" — filter to repo_b should still find it.
    hits_filtered = search_index(index_db, "mock data", k=5, repo_filter=str(FIXTURE_ROOT / "repo_b"))
    assert len(hits_filtered) == 1
    assert "mock" in hits_filtered[0]["body"].lower()
    # Filter to repo_a should NOT find the mock-data hit (it's in repo_b).
    hits_a = search_index(index_db, "mock data", k=5, repo_filter=str(FIXTURE_ROOT / "repo_a"))
    assert len(hits_a) == 0
