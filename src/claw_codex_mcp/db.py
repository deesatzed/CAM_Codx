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
    """True iff sqlite-vec extension loads and methodology_embeddings is queryable."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
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
        except sqlite3.OperationalError:
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
