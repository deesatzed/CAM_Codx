#!/usr/bin/env python3
"""Build tests/fixtures/claw_slice.db from a real CAM_CAM/data/claw.db.

Copies a small but real slice: the top N viable methodologies by retrieval_count,
plus their methodology_fts and methodology_embeddings rows, plus links.

Run once when the live corpus changes. The output is committed (tracked binary).

Usage:
    python tools/build_slice_db.py [--source PATH] [--dest PATH] [--n 15]
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

DEFAULT_SOURCE = Path("/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db")
DEFAULT_DEST = Path(__file__).parent.parent / "tests" / "fixtures" / "claw_slice.db"


def build(source: Path, dest: Path, n: int) -> None:
    if not source.exists():
        sys.exit(f"source DB not found: {source}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()

    shutil.copy(source, dest)
    conn = sqlite3.connect(dest)

    # methodology_embeddings is a vec0 virtual table; we must load the extension
    # to interact with it. Without this, DELETE on methodology_embeddings fails
    # with "no such module: vec0".
    import sqlite_vec
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)

    # Keep top viable methodologies AND some embryonic ones.
    # Reality of the 2026-05-19 corpus (verified live):
    #   - All viable rows have files_affected = '[]' (provenance fields empty).
    #   - All embryonic rows have files_affected populated.
    # We need at least one row with populated files_affected so downstream
    # fixture tests can assert real provenance is present. We also need
    # mostly-viable rows to exercise the recall path against the lifecycle
    # filter (the default include_embryonic=False).
    # Slice composition: top (n-3) viable by retrieval_count + top 3 embryonic.
    #
    # NOTE: methodology_fts.methodology_id is a real UNINDEXED FTS5 column
    # (verified 2026-05-19), not content-rowid-linked. Plain DELETE works.
    # vec0 virtual tables (methodology_embeddings) do NOT expose `rowid` to
    # SQL — DELETE must use the primary key column (methodology_id) directly.
    n_viable = max(1, n - 3)
    n_embryonic = min(3, n - n_viable)
    conn.executescript(f"""
        CREATE TEMP TABLE keep AS
        SELECT id FROM methodologies
         WHERE lifecycle_state = 'viable'
         ORDER BY retrieval_count DESC, success_count DESC
         LIMIT {n_viable};

        INSERT INTO keep
        SELECT id FROM methodologies
         WHERE lifecycle_state = 'embryonic'
         ORDER BY retrieval_count DESC, success_count DESC, id ASC
         LIMIT {n_embryonic};

        DELETE FROM methodologies WHERE id NOT IN (SELECT id FROM keep);
        DELETE FROM methodology_links WHERE source_id NOT IN (SELECT id FROM keep)
                                         AND target_id NOT IN (SELECT id FROM keep);
        DELETE FROM methodology_fts WHERE methodology_id NOT IN (SELECT id FROM keep);
        DELETE FROM methodology_embeddings
         WHERE methodology_id NOT IN (SELECT id FROM methodologies);
    """)
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print(f"slice DB written: {dest} ({dest.stat().st_size} bytes)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    p.add_argument("--n", type=int, default=15)
    args = p.parse_args()
    build(args.source, args.dest, args.n)


if __name__ == "__main__":
    main()
