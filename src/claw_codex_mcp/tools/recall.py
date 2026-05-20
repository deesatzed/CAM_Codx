"""cam_recall handler: hybrid FTS5 + vec0 retrieval over methodologies.

See build_specs.md §3.1 for the contract.
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any

from claw_codex_mcp.db import ModeInfo, open_read_conn
from claw_codex_mcp.schemas import (
    CamRecallInput, CamRecallOutput, MethodologyHit,
)

STALE_DAYS = 30
NAME_TRUNC = 80
SNIPPET_TRUNC = 240


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return list(v) if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


def _first_tag_prefix(tags: list[str], prefix: str) -> str | None:
    for t in tags:
        if isinstance(t, str) and t.startswith(prefix):
            return t[len(prefix):]
    return None


def _domain_tag(tags: list[str]) -> str:
    return _first_tag_prefix(tags, "domain:") or "untyped"


def _is_stale(last_verified: str | None) -> bool:
    if not last_verified:
        return True
    try:
        dt = _dt.datetime.fromisoformat(last_verified.replace("Z", "+00:00"))
    except ValueError:
        return True
    age_days = (_dt.datetime.now(_dt.timezone.utc) - dt).days
    return age_days > STALE_DAYS


def _fitness(success: int, failure: int) -> tuple[float, int]:
    n = success + failure
    score = (success + 1) / (n + 2)  # Laplace-smoothed Bernoulli mean
    return round(score, 4), n


def _row_to_hit(row: dict[str, Any], rank_score: float) -> MethodologyHit:
    tags = _parse_tags(row.get("tags"))
    files = _parse_tags(row.get("files_affected"))
    src_repo = _first_tag_prefix(tags, "source_repo:") or ""
    src_commit = _first_tag_prefix(tags, "source_commit:")
    src_path = files[0] if files else ""
    score, n = _fitness(row.get("success_count", 0), row.get("failure_count", 0))
    last_verified = row.get("last_retrieved_at")
    notes = row.get("methodology_notes") or row.get("problem_description") or ""
    # Pydantic max_length=240 on the snippet field requires the ellipsis
    # to fit inside the budget. Truncate to (SNIPPET_TRUNC - 1) so the
    # appended ellipsis lands at exactly SNIPPET_TRUNC.
    snippet = (notes[: SNIPPET_TRUNC - 1] + "…") if len(notes) > SNIPPET_TRUNC else notes
    name = (row.get("problem_description") or row.get("id") or "").splitlines()[0][:NAME_TRUNC]

    return MethodologyHit(
        methodology_id=row["id"],
        name=name,
        source_repo=src_repo,
        source_path=src_path,
        source_commit_sha=src_commit,
        mined_at=row.get("created_at", ""),
        last_verified_at=last_verified,
        fitness_score=score,
        fitness_n=n,
        domain_tag=_domain_tag(tags),
        stale_bool=_is_stale(last_verified),
        rank_score=rank_score,
        snippet=snippet,
    )


def _corpus_size(conn) -> int:
    # Alias the count so it's accessible regardless of the connection's
    # row_factory (the handler installs a dict factory before calling this).
    cur = conn.execute("SELECT COUNT(*) AS n FROM methodologies")
    row = cur.fetchone()
    return int(row["n"] if isinstance(row, dict) else row[0])


async def handle_recall(req: CamRecallInput, info: ModeInfo) -> CamRecallOutput:
    if info.mode == "standalone":
        return CamRecallOutput(
            results=[],
            corpus_status="absent",
            corpus_size=0,
            degraded=False,
            reason="no methodology corpus configured",
            remediation="set CAM_CODEX_MCP_DB_PATH to a CAM_CAM claw.db",
            query_echo=req.query,
        )

    with open_read_conn(info) as conn:
        conn.row_factory = lambda cur, row: dict(zip([c[0] for c in cur.description], row))

        lifecycle_clause = (
            "lifecycle_state IN ('viable','thriving')"
            if not req.include_embryonic
            else "lifecycle_state IN ('viable','thriving','embryonic')"
        )

        # FTS5 first pass — fetch top 50 candidates.
        try:
            cur = conn.execute(
                f"""SELECT m.id, m.problem_description, m.methodology_notes,
                          m.tags, m.files_affected, m.created_at,
                          m.last_retrieved_at, m.success_count, m.failure_count,
                          m.lifecycle_state, bm25(methodology_fts) AS fts_score
                     FROM methodology_fts
                     JOIN methodologies m ON m.id = methodology_fts.methodology_id
                    WHERE methodology_fts MATCH ?
                      AND {lifecycle_clause}
                    ORDER BY fts_score
                    LIMIT 50""",
                (req.query,),
            )
            rows = cur.fetchall()
        except Exception as exc:  # FTS5 syntax error on weird input → treat as empty match
            return CamRecallOutput(
                results=[],
                corpus_status="connected",
                corpus_size=_corpus_size(conn),
                degraded=False,
                reason=f"fts5 error: {exc.__class__.__name__}",
                query_echo=req.query,
            )
        size = _corpus_size(conn)

    hits: list[MethodologyHit] = []
    for r in rows[: req.k]:
        rank = 1.0 / (1.0 + max(0.0, r.get("fts_score") or 0.0))
        hit = _row_to_hit(r, rank)
        if hit.fitness_score < req.min_fitness:
            continue
        if not req.include_stale and hit.stale_bool:
            continue
        if req.domain_filter and hit.domain_tag != req.domain_filter:
            continue
        hits.append(hit)

    return CamRecallOutput(
        results=hits,
        corpus_status="connected",
        corpus_size=size,
        degraded=not info.vec_available,  # vec unavailable → FTS-only fallback
        reason="vec0 unavailable; FTS-only" if not info.vec_available else None,
        query_echo=req.query,
    )
