"""cam_provenance handler. build_specs.md §3.2."""

from __future__ import annotations

from claw_codex_mcp.db import ModeInfo, open_read_conn
from claw_codex_mcp.schemas import (
    CamProvenanceInput, CamProvenanceOutput, MethodologyLink,
)
from claw_codex_mcp.tools.recall import _row_to_hit, _parse_tags


async def handle_provenance(
    req: CamProvenanceInput, info: ModeInfo
) -> CamProvenanceOutput:
    if info.mode == "standalone":
        return CamProvenanceOutput(
            found=False, methodology_id=req.methodology_id,
            corpus_status="absent",
            reason="no methodology corpus configured",
        )

    with open_read_conn(info) as conn:
        conn.row_factory = lambda cur, row: dict(zip([c[0] for c in cur.description], row))
        cur = conn.execute(
            "SELECT id, problem_description, solution_code, methodology_notes, "
            "       tags, files_affected, created_at, last_retrieved_at, "
            "       success_count, failure_count, lifecycle_state "
            "  FROM methodologies WHERE id = ?",
            (req.methodology_id,),
        )
        row = cur.fetchone()
        if row is None:
            return CamProvenanceOutput(
                found=False, methodology_id=req.methodology_id,
                corpus_status="connected", reason="unknown methodology_id",
            )

        hit = _row_to_hit(row, rank_score=1.0)
        links: list[MethodologyLink] = []
        if req.include_links:
            link_cur = conn.execute(
                "SELECT 'parent' AS direction, source_id AS target_id, link_type, strength "
                "  FROM methodology_links WHERE target_id = ? "
                "UNION ALL "
                "SELECT 'child' AS direction, target_id, link_type, strength "
                "  FROM methodology_links WHERE source_id = ?",
                (req.methodology_id, req.methodology_id),
            )
            for lr in link_cur.fetchall():
                links.append(MethodologyLink(
                    direction=lr["direction"], target_id=lr["target_id"],
                    link_type=lr["link_type"], strength=float(lr["strength"]),
                ))

        return CamProvenanceOutput(
            found=True,
            methodology_id=req.methodology_id,
            corpus_status="connected",
            provenance=hit,
            solution_code=row.get("solution_code") if req.include_solution_code else None,
            methodology_notes=row.get("methodology_notes"),
            files_affected=_parse_tags(row.get("files_affected")),
            tags=_parse_tags(row.get("tags")),
            links=links,
        )
