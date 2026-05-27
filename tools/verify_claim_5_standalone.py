"""verify_claim_5_standalone.py — Claim 6 (STANDALONE BOOT): the server starts
and all 4 tools function correctly with CAM_CODEX_MCP_DB_PATH unset (no corpus).

Pass condition (100% binary):
  1. Server boots and tools/list returns exactly the 4 expected tools.
  2. cam_recall returns corpus_status="absent" with results=[] (no fabrication).
  3. cam_provenance returns found=false with corpus_status="absent".
  4. cam_decisions_search returns (results may be empty, but no exception raised).
  5. cam_record_outcome writes to local SQLite (~/.cam_codex_mcp/codex_outcome_log.db)
     and the row is verifiable via an independent sqlite3 connection.

Falsifier guards:
  - cam_recall must not return ANY results when corpus is absent (fabrication).
  - cam_record_outcome must produce a verifiable row in the local DB, not just
    return recorded=True without writing.
  - The independent sqlite3 check opens ~/.cam_codex_mcp/codex_outcome_log.db
    directly — not the tool's own connection.

Run from the codex-cam-methodology-impl/ root.
Do NOT set CAM_CODEX_MCP_DB_PATH in the environment when running this script.
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
CLAIM = "Claim 6 (STANDALONE BOOT): all 4 tools function with no corpus"

EXPECTED_TOOLS = {
    "cam_recall",
    "cam_provenance",
    "cam_decisions_search",
    "cam_record_outcome",
}

STANDALONE_OUTCOME_DB = Path.home() / ".cam_codex_mcp" / "codex_outcome_log.db"


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


def _outcome_row_exists(outcome_id: str) -> bool:
    if not STANDALONE_OUTCOME_DB.exists():
        return False
    conn = sqlite3.connect(f"file:{STANDALONE_OUTCOME_DB}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT id FROM codex_outcome_log WHERE id = ?", (outcome_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


async def _verify() -> None:
    # Strip CAM_CODEX_MCP_DB_PATH from env to force standalone mode.
    env = {k: v for k, v in os.environ.items() if k != "CAM_CODEX_MCP_DB_PATH"}

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

                # --- Check 1: tool surface ---
                tools_result = await session.list_tools()
                found = {t.name for t in tools_result.tools}
                if found != EXPECTED_TOOLS:
                    _fail(
                        f"expected tools {sorted(EXPECTED_TOOLS)}, got {sorted(found)}"
                    )

                # --- Check 2: cam_recall must return absent + no results ---
                recall_result = _payload(
                    await session.call_tool(
                        "cam_recall", {"query": "rate limiting", "k": 5}
                    )
                )
                recall_status = recall_result.get("corpus_status")
                recall_results = recall_result.get("results", [])
                if recall_status != "absent":
                    _fail(
                        f"cam_recall corpus_status={recall_status!r}; "
                        "expected 'absent' in standalone mode. "
                        "Is CAM_CODEX_MCP_DB_PATH set in the caller's env?"
                    )
                if recall_results:
                    _fail(
                        f"cam_recall returned {len(recall_results)} results with no corpus — "
                        "this is fabrication. results must be [] when corpus_status='absent'."
                    )

                # --- Check 3: cam_provenance must return found=false + absent ---
                fake_id = "standalone-test-nonexistent-id"
                prov_result = _payload(
                    await session.call_tool(
                        "cam_provenance", {"methodology_id": fake_id}
                    )
                )
                prov_found = prov_result.get("found", True)
                prov_status = prov_result.get("corpus_status")
                if prov_found:
                    _fail(
                        f"cam_provenance returned found=true for a fabricated id in standalone mode"
                    )
                if prov_status != "absent":
                    _fail(
                        f"cam_provenance corpus_status={prov_status!r}; "
                        "expected 'absent' in standalone mode"
                    )

                # --- Check 4: cam_decisions_search must not raise ---
                try:
                    decisions_result = _payload(
                        await session.call_tool(
                            "cam_decisions_search", {"query": "rate limiting", "k": 5}
                        )
                    )
                except Exception as exc:
                    _fail(f"cam_decisions_search raised in standalone mode: {exc}")

                # --- Check 5: cam_record_outcome must write to local DB ---
                test_run_hash = str(uuid.uuid4()).replace("-", "")
                write_result = _payload(
                    await session.call_tool(
                        "cam_record_outcome",
                        {
                            "methodology_ids": ["standalone-test-id-" + test_run_hash[:8]],
                            "task_id": "verify-standalone-boot",
                            "repo": str(ROOT),
                            "outcome": "green",
                            "run_hash": test_run_hash,
                            "notes": "verify_claim_5_standalone probe",
                        },
                    )
                )
                if not write_result.get("recorded", False):
                    reason = write_result.get("reason", "unknown")
                    _fail(
                        f"cam_record_outcome returned recorded=false in standalone mode: {reason}\n"
                        "      Expected it to write to the local outcome DB."
                    )
                outcome_id = write_result.get("outcome_id")
                if not outcome_id:
                    _fail("cam_record_outcome returned recorded=true but no outcome_id")
                write_status = write_result.get("corpus_status")
                if write_status != "absent":
                    _fail(
                        f"cam_record_outcome corpus_status={write_status!r}; "
                        "expected 'absent' in standalone mode"
                    )

    # --- Independent verification (outside MCP session) ---
    if not _outcome_row_exists(outcome_id):
        _fail(
            f"outcome_id={outcome_id!r} not found in {STANDALONE_OUTCOME_DB} "
            "via independent sqlite3 connection. cam_record_outcome claimed success "
            "but the row is absent."
        )

    _pass(
        f"tools={sorted(found)} recall_status=absent recall_results=0 "
        f"prov_found=false decisions_ok=true outcome_id={outcome_id[:8]}... "
        f"outcome_row_verified=true"
    )


def main() -> int:
    if os.environ.get("CAM_CODEX_MCP_DB_PATH"):
        print(
            "WARN  CAM_CODEX_MCP_DB_PATH is set in the caller environment. "
            "This script strips it for the server subprocess, but confirm you "
            "intended to run the standalone claim with a corpus-aware caller env.",
            file=sys.stderr,
        )
    try:
        asyncio.run(_verify())
    except _VerifyFail as exc:
        print(f"FAIL  {CLAIM}\n      {exc.reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
