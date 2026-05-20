"""SQLite FTS5 index over cross-repo DECISIONS.md files.

build_specs.md §3.3 and §2.3.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

INDEX_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions_docs (
    doc_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    repo         TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    block_anchor TEXT NOT NULL,
    decided_at   TEXT,
    body         TEXT NOT NULL,
    indexed_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(repo, file_path, block_anchor)
);
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    body, content='decisions_docs', content_rowid='doc_id'
);
CREATE TABLE IF NOT EXISTS index_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _split_blocks(text: str) -> list[tuple[str, str | None, str]]:
    """Returns list of (anchor, decided_at, body) for each ##-level block."""
    matches = list(H2.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        anchor = m.group(1).strip()
        date_match = DATE.match(anchor)
        decided_at = date_match.group(1) if date_match else None
        blocks.append((anchor, decided_at, text[start:end].strip()))
    return blocks


def build_index(index_db_path: Path, roots: list[Path]) -> tuple[int, int]:
    """Rebuild the index. Idempotent on (repo, file_path, block_anchor)."""
    index_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(index_db_path)
    try:
        conn.executescript(INDEX_SCHEMA)
        # Truncate before rebuild so removed blocks disappear cleanly.
        conn.execute("DELETE FROM decisions_fts")
        conn.execute("DELETE FROM decisions_docs")

        n_files = 0
        n_blocks = 0
        for root in roots:
            for f in root.rglob("DECISIONS.md"):
                n_files += 1
                text = f.read_text(encoding="utf-8", errors="replace")
                blocks = _split_blocks(text)
                for anchor, decided_at, body in blocks:
                    # Combine anchor (which carries the H2 heading text, often the
                    # decision title) with body so FTS matches against either, and
                    # so the returned body lets callers see the heading context.
                    indexed_body = f"{anchor}\n{body}" if body else anchor
                    conn.execute(
                        "INSERT OR IGNORE INTO decisions_docs "
                        "(repo, file_path, block_anchor, decided_at, body) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (str(root.resolve()), str(f.resolve()), anchor, decided_at, indexed_body),
                    )
                    doc_id = conn.execute(
                        "SELECT doc_id FROM decisions_docs "
                        " WHERE repo=? AND file_path=? AND block_anchor=?",
                        (str(root.resolve()), str(f.resolve()), anchor),
                    ).fetchone()[0]
                    conn.execute(
                        "INSERT INTO decisions_fts(rowid, body) VALUES (?, ?)",
                        (doc_id, indexed_body),
                    )
                    n_blocks += 1
        conn.execute(
            "INSERT OR REPLACE INTO index_meta(key, value) VALUES "
            "('built_at', strftime('%Y-%m-%dT%H:%M:%SZ','now'))"
        )
        conn.commit()
        return n_blocks, n_files
    finally:
        conn.close()


def search_index(
    index_db_path: Path, query: str, k: int = 5,
    repo_filter: str | None = None,
) -> list[dict]:
    if not index_db_path.exists():
        return []
    conn = sqlite3.connect(f"file:{index_db_path}?mode=ro", uri=True)
    try:
        conn.row_factory = lambda cur, row: dict(zip([c[0] for c in cur.description], row))
        sql = (
            "SELECT d.repo, d.file_path, d.block_anchor, d.decided_at, d.body, "
            "       bm25(decisions_fts) AS rank_score "
            "  FROM decisions_fts "
            "  JOIN decisions_docs d ON d.doc_id = decisions_fts.rowid "
            " WHERE decisions_fts MATCH ?"
        )
        params: list = [query]
        if repo_filter:
            sql += " AND d.repo LIKE ?"
            params.append(f"{repo_filter}%")
        sql += " ORDER BY rank_score LIMIT ?"
        params.append(k)
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()
