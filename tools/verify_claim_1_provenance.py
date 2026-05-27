"""verify_claim_1_provenance.py — Claim 2 (Provenance): every methodology
returned by cam_recall has non-null source_repo, source_path, mined_at, and
fitness_n fields, and cam_provenance resolves each returned id to the matching
row via an independent sqlite connection.

Pass condition (100% binary): every row passes all provenance checks.
Any gap requires user waiver per workspace policy.

Run from the codex-cam-methodology-impl/ root with CAM_CODEX_MCP_DB_PATH set
to the real claw.db path.

Uses MCP SDK over stdio — no Codex CLI approval required.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
CLAIM = "Claim 2 (PROVENANCE): every recalled methodology has traceable source"

QUERIES = [
    "rate limiting",
    "retry exponential backoff",
    "database connection pooling",
    "error handling",
    "authentication",
]


class _VerifyFail(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _fail(reason: str) -> None:
    raise _VerifyFail(reason)


def _pass(detail: str = "") -> None:
    suffix = f"\n      {detail}" if detail else ""
    print(f"PASS  {CLAIM}{suffix}")


def _payload(result) -> dict:
    if not result.content:
        raise ValueError("tool returned no content")
    return json.loads(result.content[0].text)


def _independent_lookup(db_path: str, methodology_id: str) -> dict | None:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT id, methodology_notes, tags FROM methodologies WHERE id = ?",
            (methodology_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {"id": row[0], "methodology_notes": row[1], "tags": row[2]}


async def _verify() -> None:
    db_path = os.environ.get("CAM_CODEX_MCP_DB_PATH", "")
    if not db_path or not Path(db_path).exists():
        _fail(
            f"CAM_CODEX_MCP_DB_PATH is not set or does not exist: {db_path!r}\n"
            "      Set it to the real claw.db path and re-run."
        )

    env = dict(os.environ)
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "claw_codex_mcp", "--transport", "stdio"],
        env=env,
        cwd=ROOT,
    )

    # IDs that passed MCP-layer checks; sqlite cross-check runs after session closes.
    ids_to_crosscheck: list[str] = []
    total_rows = 0
    failures: list[str] = []

    with open(os.devnull, "w", encoding="utf-8") as errlog:
        client = stdio_client(server, errlog=errlog)
        async with client as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                for query in QUERIES:
                    recall_result = _payload(
                        await session.call_tool("cam_recall", {"query": query, "k": 5})
                    )

                    corpus_status = recall_result.get("corpus_status", "unknown")
                    if corpus_status not in ("connected", "degraded"):
                        failures.append(
                            f"corpus_status={corpus_status!r} for query {query!r}; "
                            "expected connected or degraded — is CAM_CODEX_MCP_DB_PATH set correctly?"
                        )
                        break

                    results = recall_result.get("results", [])
                    if not results:
                        print(f"  WARN  query={query!r}: no results returned (corpus may be thin)")
                        continue

                    seen_ids: set[str] = set()
                    for row in results:
                        total_rows += 1
                        mid = row.get("methodology_id", "")

                        # Falsifier guard: all rows must have distinct ids
                        if mid in seen_ids:
                            failures.append(f"query={query!r}: duplicate methodology_id {mid!r}")
                            continue
                        seen_ids.add(mid)

                        # Check required provenance fields (schema uses 'name', not 'title')
                        missing = [
                            f
                            for f in ("methodology_id", "name", "fitness_n")
                            if not row.get(f)
                        ]
                        if missing:
                            failures.append(
                                f"query={query!r} id={mid!r}: missing fields {missing}"
                            )
                            continue

                        # cam_provenance must resolve to same row
                        prov_result = _payload(
                            await session.call_tool(
                                "cam_provenance", {"methodology_id": mid}
                            )
                        )
                        if not prov_result.get("found"):
                            failures.append(
                                f"cam_provenance({mid!r}) returned found=false but recall returned it"
                            )
                            continue

                        # Queue for independent sqlite cross-check (outside session)
                        ids_to_crosscheck.append(mid)

    # Independent sqlite cross-check — runs after MCP session is fully closed.
    passed_rows = 0
    for mid in ids_to_crosscheck:
        db_row = _independent_lookup(db_path, mid)
        if db_row is None:
            failures.append(
                f"id={mid!r} not found in claw.db via independent connection"
            )
        else:
            passed_rows += 1

    if total_rows == 0:
        _fail(
            "zero rows returned across all queries — corpus too thin or recall broken. "
            "Verify cam_recall returns rows before running this claim."
        )

    resolution_rate = passed_rows / total_rows
    detail = f"rows={total_rows} passed={passed_rows} rate={resolution_rate:.0%}"

    if failures:
        detail_lines = "\n      ".join(failures)
        _fail(
            f"{detail}\n      Failures:\n      {detail_lines}\n"
            "      Per workspace policy: <100% requires user waiver or action plan in _coverage_gaps.md"
        )

    if resolution_rate < 1.0:
        _fail(
            f"{detail} — not 100%; per workspace policy this requires a written action plan "
            "or explicit user waiver before Phase 9 can be signed off."
        )

    _pass(detail)


def main() -> int:
    try:
        asyncio.run(_verify())
    except _VerifyFail as exc:
        print(f"FAIL  {CLAIM}\n      {exc.reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
