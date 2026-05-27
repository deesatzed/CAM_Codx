"""verify_claim_3_learning.py — Claim 4 (LEARNING): the write flywheel closes.

After calling cam_record_outcome 10+ times with distinct methodology_ids
drawn from cam_recall, the codex_outcome_log row count delta must be >= 10,
and at least 3 distinct methodology_ids must appear in the new rows.

Pass condition (100% binary): delta >= 10 AND distinct_ids >= 3.

Design notes:
- methodology_ids are drawn LIVE from cam_recall for 5 different queries,
  so the test exercises the full read→write loop end-to-end with real corpus
  data.
- Each cam_record_outcome call uses a distinct run_hash (UUID) to bypass the
  UNIQUE(run_hash) dedup guard, ensuring every call produces a real insert.
- After the writes, the row count and distinct-id count are verified via an
  INDEPENDENT sqlite3 connection (not the tool's connection).
- The falsifier guard: if cam_recall returns zero results (corpus absent),
  the test fails explicitly rather than fabricating methodology_ids.

Run from the codex-cam-methodology-impl/ root with CAM_CODEX_MCP_DB_PATH set.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
CLAIM = "Claim 4 (LEARNING): write flywheel closes — outcome_log delta>=10, distinct_ids>=3"

RECALL_QUERIES = [
    "rate limiting",
    "retry exponential backoff",
    "database connection pooling",
    "error handling",
    "authentication",
    "caching strategy",
    "circuit breaker pattern",
    "input validation",
    "logging observability",
    "pagination",
]
REQUIRED_DELTA = 10
REQUIRED_DISTINCT = 3


def _fail(reason: str) -> None:
    print(f"FAIL  {CLAIM}\n      {reason}", file=sys.stderr)
    sys.exit(1)


def _pass(detail: str = "") -> None:
    suffix = f"\n      {detail}" if detail else ""
    print(f"PASS  {CLAIM}{suffix}")


def _payload(result) -> dict:
    if not result.content:
        raise ValueError("tool returned no content")
    return json.loads(result.content[0].text)


def _read_outcome_count(outcome_db: str) -> int:
    conn = sqlite3.connect(f"file:{outcome_db}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT COUNT(*) FROM codex_outcome_log").fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def _read_distinct_methodology_ids_since(outcome_db: str, before_rowid: int) -> set[str]:
    conn = sqlite3.connect(f"file:{outcome_db}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT methodology_ids FROM codex_outcome_log WHERE rowid > ?",
            (before_rowid,),
        ).fetchall()
    finally:
        conn.close()
    ids: set[str] = set()
    for (mid_json,) in rows:
        for mid in json.loads(mid_json):
            ids.add(mid)
    return ids


def _max_rowid(outcome_db: str) -> int:
    conn = sqlite3.connect(f"file:{outcome_db}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(rowid), 0) FROM codex_outcome_log"
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


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

    with open(os.devnull, "w", encoding="utf-8") as errlog:
        client = stdio_client(server, errlog=errlog)
        async with client as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Discover the outcome DB path from the server's corpus_status payload
                # by making one recall call and checking what mode the server is in.
                probe_result = _payload(
                    await session.call_tool("cam_recall", {"query": "rate limiting", "k": 1})
                )
                corpus_status = probe_result.get("corpus_status", "unknown")
                if corpus_status not in ("connected", "degraded"):
                    _fail(
                        f"corpus_status={corpus_status!r}; this claim requires corpus "
                        "to be connected or degraded so cam_recall returns real methodology_ids. "
                        "Verify CAM_CODEX_MCP_DB_PATH is set correctly."
                    )

                # The outcome log is in claw.db (same file, same DB for connected mode).
                # Establish pre-count baseline via independent connection.
                before_count = _read_outcome_count(db_path)
                before_rowid = _max_rowid(db_path)

                outcomes_written = 0
                for query in RECALL_QUERIES:
                    recall_result = _payload(
                        await session.call_tool("cam_recall", {"query": query, "k": 3})
                    )
                    results = recall_result.get("results", [])
                    if not results:
                        print(f"  WARN  query={query!r}: no results; skipping write for this query")
                        continue

                    # Use the first result's methodology_id for this outcome write.
                    mid = results[0]["methodology_id"]
                    run_hash = str(uuid.uuid4()).replace("-", "")

                    write_result = _payload(
                        await session.call_tool(
                            "cam_record_outcome",
                            {
                                "methodology_ids": [mid],
                                "task_id": f"verify-learning-{query.replace(' ', '-')}",
                                "repo": str(ROOT),
                                "outcome": "green",
                                "run_hash": run_hash,
                                "notes": f"verify_claim_3_learning probe: query={query!r}",
                            },
                        )
                    )
                    recorded = write_result.get("recorded", False)
                    if not recorded:
                        reason = write_result.get("reason", "unknown")
                        print(f"  WARN  cam_record_outcome not recorded for query={query!r}: {reason}")
                        continue
                    outcomes_written += 1

                    if outcomes_written >= REQUIRED_DELTA:
                        break

    # Independent verification via sqlite3 (not the tool's connection)
    after_count = _read_outcome_count(db_path)
    delta = after_count - before_count
    new_ids = _read_distinct_methodology_ids_since(db_path, before_rowid)
    distinct_count = len(new_ids)

    detail = (
        f"before={before_count} after={after_count} delta={delta} "
        f"distinct_methodology_ids={distinct_count}"
    )

    failures: list[str] = []
    if delta < REQUIRED_DELTA:
        failures.append(
            f"row delta {delta} < required {REQUIRED_DELTA}. "
            "cam_record_outcome wrote fewer rows than expected. "
            "Check corpus connectivity and outcome_log FK constraints."
        )
    if distinct_count < REQUIRED_DISTINCT:
        failures.append(
            f"distinct methodology_ids {distinct_count} < required {REQUIRED_DISTINCT}. "
            "Over-fit: all writes targeted the same methodology_id."
        )

    if failures:
        detail_lines = "\n      ".join(failures)
        _fail(
            f"{detail}\n      Failures:\n      {detail_lines}\n"
            "      Per workspace policy: <100% requires action plan in _coverage_gaps.md "
            "or explicit user waiver."
        )

    _pass(detail)


def main() -> int:
    asyncio.run(_verify())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
