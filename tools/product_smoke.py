"""One-command local product smoke test for the Codex-CAM MCP surface.

This command intentionally uses the same real transport as the user-facing demo:
official MCP SDK client -> `python -m claw_codex_mcp --transport stdio`.
It does not use Codex TUI approval, OpenRouter, external API keys, or fake rows.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from claw_codex_mcp.decisions_index import build_index


ROOT = Path(__file__).resolve().parents[1]
SLICE_DB = ROOT / "tests" / "fixtures" / "claw_slice.db"
DECISIONS_ROOT = ROOT / "tests" / "fixtures" / "sample_decisions"
DEFAULT_WORK_DIR = Path("/private/tmp/cam_codex_mcp_product_smoke")
EXPECTED_TOOLS = {
    "cam_recall",
    "cam_provenance",
    "cam_decisions_search",
    "cam_record_outcome",
}


class SmokeFailure(RuntimeError):
    """Raised when a product smoke assertion fails."""


def _pass(label: str, detail: str = "") -> None:
    suffix = f" {detail}" if detail else ""
    print(f"PASS {label}{suffix}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def _payload(result) -> dict:
    _require(bool(result.content), "tool returned no content")
    return json.loads(result.content[0].text)


def _run_version_check() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "claw_codex_mcp", "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    _require(result.returncode == 0, result.stderr.strip() or result.stdout.strip())
    version = result.stdout.strip()
    _require(bool(version), "version command printed no version")
    _pass("version", version)


def _build_decisions_index(work_dir: Path, mode: str) -> Path:
    index_path = work_dir / f"{mode}_decisions_index.db"
    blocks, files = build_index(index_path, [DECISIONS_ROOT])
    _require(files > 0, "no DECISIONS.md files were indexed")
    _require(blocks > 0, "no decision blocks were indexed")
    return index_path


def _outcome_row_count(outcome_db: Path, run_hash: str) -> int:
    conn = sqlite3.connect(outcome_db)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM codex_outcome_log WHERE run_hash = ?",
            (run_hash,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0])


async def _run_mode(mode: str, work_dir: Path) -> None:
    mode_dir = work_dir / mode
    mode_dir.mkdir(parents=True, exist_ok=True)
    outcome_db = mode_dir / "outcomes.db"
    index_path = _build_decisions_index(mode_dir, mode)

    env = dict(os.environ)
    env["CAM_CODEX_MCP_DECISIONS_INDEX"] = str(index_path)
    env["CAM_CODEX_MCP_OUTCOME_DB_PATH"] = str(outcome_db)
    if mode == "connected":
        _require(SLICE_DB.exists(), f"connected slice DB is missing: {SLICE_DB}")
        env["CAM_CODEX_MCP_DB_PATH"] = str(SLICE_DB)
    else:
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

                tools = await session.list_tools()
                tool_names = {tool.name for tool in tools.tools}
                _require(
                    tool_names == EXPECTED_TOOLS,
                    f"{mode} tool surface was {sorted(tool_names)}",
                )
                _pass(f"{mode} tools", ",".join(sorted(tool_names)))

                recall = _payload(await session.call_tool(
                    "cam_recall",
                    {"query": "data", "k": 3, "include_embryonic": True},
                ))
                if mode == "connected":
                    _require(recall["corpus_status"] in {"connected", "degraded"}, str(recall))
                    _require(bool(recall["results"]), "connected recall returned no methodology rows")
                    methodology_id = recall["results"][0]["methodology_id"]
                    _pass("connected recall_real_rows", methodology_id)
                else:
                    _require(recall["corpus_status"] == "absent", str(recall))
                    _require(recall["results"] == [], str(recall))
                    _require(bool(recall.get("remediation")), str(recall))
                    methodology_id = "standalone-product-smoke-methodology"
                    _pass("standalone recall_absent", "corpus_status=absent")

                provenance = _payload(await session.call_tool(
                    "cam_provenance",
                    {"methodology_id": methodology_id if mode == "connected" else "absent-id"},
                ))
                if mode == "connected":
                    _require(provenance.get("found") is True, str(provenance))
                    _require(provenance.get("methodology_id") == methodology_id, str(provenance))
                    _pass("connected provenance_resolves", methodology_id)
                else:
                    _require(provenance.get("found") is False, str(provenance))
                    _require(provenance.get("corpus_status") == "absent", str(provenance))
                    _pass("standalone provenance_absent", "found=false")

                decisions = _payload(await session.call_tool(
                    "cam_decisions_search",
                    {"query": "mock data", "k": 2},
                ))
                _require(bool(decisions.get("results")), str(decisions))
                _pass(f"{mode} decisions_search", f"results={len(decisions['results'])}")

                run_hash = f"product-smoke-{mode}-{uuid.uuid4().hex}"
                outcome_args = {
                    "methodology_ids": [methodology_id],
                    "task_id": f"product-smoke-{mode}",
                    "repo": str(ROOT),
                    "outcome": "green",
                    "evidence": {"command": "python tools/product_smoke.py", "mode": mode},
                    "run_hash": run_hash,
                }
                first = _payload(await session.call_tool("cam_record_outcome", outcome_args))
                second = _payload(await session.call_tool("cam_record_outcome", outcome_args))

                _require(first.get("recorded") is True, str(first))
                _require(first.get("duplicate") is False, str(first))
                _require(second.get("recorded") is False, str(second))
                _require(second.get("duplicate") is True, str(second))
                _require(
                    _outcome_row_count(outcome_db, run_hash) == 1,
                    "duplicate outcome row inserted",
                )
                _pass(f"{mode} outcome_idempotent", f"outcome_db={outcome_db}")


async def _run_all(work_dir: Path) -> None:
    _run_version_check()
    await _run_mode("standalone", work_dir)
    await _run_mode("connected", work_dir)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run local product smoke checks for the Codex-CAM MCP server.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=DEFAULT_WORK_DIR,
        help="Directory for temporary decision indexes and outcome ledgers.",
    )
    args = parser.parse_args()

    work_dir = args.work_dir.expanduser().resolve()
    try:
        asyncio.run(_run_all(work_dir))
    except Exception as exc:
        print(f"FAIL product_smoke {exc}", file=sys.stderr)
        return 1

    print(f"PRODUCT SMOKE PASS work_dir={work_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
