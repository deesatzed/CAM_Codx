"""Read-only and append-only DB helpers; mode detection.

See build_specs.md §1.3 for the mode table and §5.1 for the outcome log schema.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ModeName = Literal["connected", "standalone", "degraded"]
CorpusStatus = Literal["connected", "empty", "absent", "degraded"]

DEFAULT_STANDALONE_DIR = Path.home() / ".cam_codex_mcp"
DEFAULT_OUTCOME_DB_NAME = "codex_outcome_log.db"


@dataclass(frozen=True)
class ModeInfo:
    mode: ModeName
    corpus_status: CorpusStatus
    db_path: Path | None
    outcome_db_path: Path
    vec_available: bool


def _is_valid_corpus(db_path: Path) -> bool:
    """A path is a valid corpus iff sqlite can open it and methodologies table exists."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        return False
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='methodologies'"
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def _check_vec(db_path: Path) -> bool:
    """True iff sqlite-vec extension loads and methodology_embeddings is queryable.

    Catches the broad sqlite3.Error (parent of OperationalError, DatabaseError,
    etc.) on the query path — a non-SQLite file raises DatabaseError, a missing
    table raises OperationalError, and both should mean "no usable corpus".
    """
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return False
    try:
        try:
            conn.enable_load_extension(True)
            import sqlite_vec  # type: ignore[import-not-found]
            sqlite_vec.load(conn)
        except Exception:
            return False
        try:
            conn.execute("SELECT * FROM methodology_embeddings LIMIT 1")
            return True
        except sqlite3.Error:
            return False
    finally:
        conn.close()


def detect_mode() -> ModeInfo:
    """Detect operating mode based on env vars and the corpus file state.

    Per build_specs.md §1.3: the mode is computed once at startup and is
    immutable for the process lifetime. Callers should call this exactly
    once at server startup and pass the resulting ModeInfo to handlers.
    """
    raw = os.environ.get("CAM_CODEX_MCP_DB_PATH")
    outcome_raw = os.environ.get("CAM_CODEX_MCP_OUTCOME_DB_PATH")

    if not raw:
        return ModeInfo(
            mode="standalone",
            corpus_status="absent",
            db_path=None,
            outcome_db_path=Path(outcome_raw) if outcome_raw
                else DEFAULT_STANDALONE_DIR / DEFAULT_OUTCOME_DB_NAME,
            vec_available=False,
        )

    db_path = Path(raw)
    if not _is_valid_corpus(db_path):
        return ModeInfo(
            mode="standalone",
            corpus_status="absent",
            db_path=None,
            outcome_db_path=Path(outcome_raw) if outcome_raw
                else DEFAULT_STANDALONE_DIR / DEFAULT_OUTCOME_DB_NAME,
            vec_available=False,
        )

    vec_ok = _check_vec(db_path)
    return ModeInfo(
        mode="connected" if vec_ok else "degraded",
        corpus_status="connected" if vec_ok else "degraded",
        db_path=db_path,
        outcome_db_path=Path(outcome_raw) if outcome_raw else db_path,
        vec_available=vec_ok,
    )


# --- Connection helpers (Task 3.5) ---

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Iterator, AsyncIterator

_WRITE_LOCK: asyncio.Lock | None = None


def _get_write_lock() -> asyncio.Lock:
    global _WRITE_LOCK
    if _WRITE_LOCK is None:
        _WRITE_LOCK = asyncio.Lock()
    return _WRITE_LOCK


@asynccontextmanager
async def write_lock() -> AsyncIterator[None]:
    """Per-process write lock. build_specs.md §8.3."""
    lock = _get_write_lock()
    async with lock:
        yield


@contextmanager
def open_read_conn(info: ModeInfo) -> Iterator[sqlite3.Connection]:
    """Open a read-only connection. Raises if mode is standalone (no corpus)."""
    if info.db_path is None:
        raise RuntimeError("no corpus DB in standalone mode")
    conn = sqlite3.connect(f"file:{info.db_path}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        if info.vec_available:
            try:
                conn.enable_load_extension(True)
                import sqlite_vec  # type: ignore[import-not-found]
                sqlite_vec.load(conn)
            except Exception:
                pass  # already verified at detect_mode; failure here is non-fatal
        yield conn
    finally:
        conn.close()


OUTCOME_LOG_DDL = """
CREATE TABLE IF NOT EXISTS codex_outcome_log (
    id              TEXT PRIMARY KEY,
    methodology_ids TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    repo            TEXT NOT NULL,
    outcome         TEXT NOT NULL
        CHECK (outcome IN ('green','red','partial','rejected')),
    evidence        TEXT NOT NULL DEFAULT '{}',
    ts              TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    run_hash        TEXT NOT NULL,
    notes           TEXT,
    UNIQUE(run_hash)
);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_ts ON codex_outcome_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_repo ON codex_outcome_log(repo);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_outcome ON codex_outcome_log(outcome);
"""


def ensure_outcome_schema(db_path: Path) -> None:
    """Idempotent schema bootstrap for the outcome log.

    Connected mode → applies to claw.db (additive only). Standalone mode →
    creates ~/.cam_codex_mcp/codex_outcome_log.db with mode=0700 parent dir.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(OUTCOME_LOG_DDL)
        conn.commit()
    finally:
        conn.close()
