"""verify_claim_0.py — Claim 0: MCP server is invoked at all.

Gate: the server boots, responds to initialize, and tools/list returns exactly
the 4 expected tool names.  This is the precondition gate: if it fails, all
other claims are vacuous.

Uses the official MCP SDK client over stdio — same transport as Codex CLI.
No Codex TUI, no OpenRouter, no mock data.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = {
    "cam_recall",
    "cam_provenance",
    "cam_decisions_search",
    "cam_record_outcome",
}

CLAIM = "Claim 0: MCP server is invoked and responds correctly"


def _fail(reason: str) -> None:
    print(f"FAIL  {CLAIM}\n      {reason}", file=sys.stderr)
    sys.exit(1)


def _pass(detail: str = "") -> None:
    suffix = f"\n      {detail}" if detail else ""
    print(f"PASS  {CLAIM}{suffix}")


async def _verify() -> None:
    db_path = os.environ.get("CAM_CODEX_MCP_DB_PATH", "")
    env = dict(os.environ)
    if not db_path:
        env.pop("CAM_CODEX_MCP_DB_PATH", None)

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

                tools_result = await session.list_tools()
                found = {t.name for t in tools_result.tools}

                if found != EXPECTED_TOOLS:
                    _fail(
                        f"expected tools {sorted(EXPECTED_TOOLS)}, "
                        f"got {sorted(found)}"
                    )

                if len(found) != 4:
                    _fail(f"surface ceiling violated: {len(found)} tools (expected 4)")

    _pass(f"tools={sorted(found)}")


def main() -> int:
    asyncio.run(_verify())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
