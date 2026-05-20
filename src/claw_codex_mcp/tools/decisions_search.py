"""cam_decisions_search handler. build_specs.md §3.3."""

from __future__ import annotations

import os
from pathlib import Path

from claw_codex_mcp.db import ModeInfo, DEFAULT_STANDALONE_DIR
from claw_codex_mcp.decisions_index import search_index
from claw_codex_mcp.schemas import (
    CamDecisionsSearchInput, CamDecisionsSearchOutput, DecisionHit,
)

DEFAULT_INDEX_NAME = "codex_decisions_index.db"

SNIPPET_TRUNC = 320


def _index_path() -> Path:
    raw = os.environ.get("CAM_CODEX_MCP_DECISIONS_INDEX")
    if raw:
        return Path(raw)
    return DEFAULT_STANDALONE_DIR / DEFAULT_INDEX_NAME


async def handle_decisions_search(
    req: CamDecisionsSearchInput, info: ModeInfo,
) -> CamDecisionsSearchOutput:
    idx_path = _index_path()
    if not idx_path.exists():
        return CamDecisionsSearchOutput(
            results=[],
            corpus_status=info.corpus_status,
            degraded=True,
            reason="index missing — run `python -m claw_codex_mcp.decisions_index rebuild`",
        )

    raw_hits = search_index(idx_path, req.query, k=req.k, repo_filter=req.repo_filter)
    hits = [
        DecisionHit(
            repo=h["repo"], file_path=h["file_path"], block_anchor=h["block_anchor"],
            decided_at=h.get("decided_at"),
            snippet=(h["body"][: SNIPPET_TRUNC - 1] + "…") if len(h["body"]) > SNIPPET_TRUNC else h["body"],
            rank_score=float(h["rank_score"]),
        )
        for h in raw_hits
    ]
    return CamDecisionsSearchOutput(
        results=hits,
        corpus_status=info.corpus_status,
        degraded=False,
    )
