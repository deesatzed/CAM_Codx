"""Run a local MCP stdio demo against the real server process.

This is intentionally the same transport shape as the integration tests:
official MCP SDK client -> `python -m claw_codex_mcp --transport stdio`.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SLICE_DB = ROOT / "tests" / "fixtures" / "claw_slice.db"
DECISIONS_ROOT = ROOT / "tests" / "fixtures" / "sample_decisions"
DEFAULT_DEMO_DIR = Path("/private/tmp/cam_codex_mcp_demo")
MAX_STRING = 700


def _build_index(index_path: Path) -> None:
    from claw_codex_mcp.decisions_index import build_index

    blocks, files = build_index(index_path, [DECISIONS_ROOT])
    print(f"decisions_index={index_path} files={files} blocks={blocks}")


def _payload(result) -> dict:
    if not result.content:
        raise RuntimeError("empty tool response")
    return json.loads(result.content[0].text)


def _print_json(label: str, payload: dict) -> None:
    print(f"\n## {label}")
    print(json.dumps(_compact(payload), indent=2, sort_keys=True))


def _compact(value):
    if isinstance(value, dict):
        return {k: _compact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_compact(v) for v in value]
    if isinstance(value, str) and len(value) > MAX_STRING:
        return value[:MAX_STRING] + "... [truncated]"
    return value


async def _run(mode: str, demo_dir: Path) -> None:
    demo_dir.mkdir(parents=True, exist_ok=True)
    index_path = demo_dir / f"{mode}_decisions_index.db"
    outcome_path = demo_dir / f"{mode}_outcomes.db"
    _build_index(index_path)

    env = dict(os.environ)
    env["CAM_CODEX_MCP_DECISIONS_INDEX"] = str(index_path)
    env["CAM_CODEX_MCP_OUTCOME_DB_PATH"] = str(outcome_path)
    if mode == "connected":
        env["CAM_CODEX_MCP_DB_PATH"] = str(SLICE_DB)
    else:
        env.pop("CAM_CODEX_MCP_DB_PATH", None)

    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "claw_codex_mcp", "--transport", "stdio"],
        env=env,
        cwd=ROOT,
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            print(f"mode={mode} tools={tool_names}")

            recall = _payload(await session.call_tool(
                "cam_recall",
                {"query": "data", "k": 3, "include_embryonic": True},
            ))
            _print_json("cam_recall", recall)

            methodology_id = (
                recall["results"][0]["methodology_id"]
                if recall.get("results") else "demo-absent-methodology"
            )
            provenance = _payload(await session.call_tool(
                "cam_provenance",
                {"methodology_id": methodology_id},
            ))
            _print_json("cam_provenance", provenance)

            decisions = _payload(await session.call_tool(
                "cam_decisions_search",
                {"query": "mock data", "k": 2},
            ))
            _print_json("cam_decisions_search", decisions)

            outcome_methodology_id = (
                methodology_id if mode == "connected" else "standalone-demo-methodology"
            )
            run_hash = (
                f"local-demo-{mode}-"
                f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            )
            outcome = _payload(await session.call_tool(
                "cam_record_outcome",
                {
                    "methodology_ids": [outcome_methodology_id],
                    "task_id": f"local-demo-{mode}",
                    "repo": str(ROOT),
                    "outcome": "green",
                    "evidence": {"command": f"python tools/demo_stdio.py --mode {mode}"},
                    "run_hash": run_hash,
                },
            ))
            _print_json("cam_record_outcome", outcome)

    conn = sqlite3.connect(outcome_path)
    try:
        row = conn.execute(
            "SELECT outcome, run_hash FROM codex_outcome_log "
            "WHERE task_id = ? ORDER BY ts DESC LIMIT 1",
            (f"local-demo-{mode}",),
        ).fetchone()
    finally:
        conn.close()
    print(f"\noutcome_db={outcome_path}")
    print(f"outcome_row={row}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Codex-CAM MCP stdio demo.")
    parser.add_argument(
        "--mode",
        choices=["standalone", "connected"],
        default="standalone",
        help="Use standalone mode or connected mode against tests/fixtures/claw_slice.db.",
    )
    parser.add_argument(
        "--demo-dir",
        type=Path,
        default=DEFAULT_DEMO_DIR,
        help="Directory for demo decision/outcome SQLite files.",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.mode, args.demo_dir.expanduser()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
