"""Real MCP stdio protocol integration. build_specs.md §10.2.

Launches `python -m claw_codex_mcp --transport stdio` as a subprocess
and sends real initialize + tools/list + tools/call requests.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3

import pytest

from claw_codex_mcp.decisions_index import build_index

# These imports come from the official mcp SDK.
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SLICE_DB = (Path(__file__).parent.parent / "fixtures" / "claw_slice.db").resolve()
DECISIONS_ROOT = (Path(__file__).parent.parent / "fixtures" / "sample_decisions").resolve()


def _server_params(env: dict[str, str]) -> StdioServerParameters:
    return StdioServerParameters(
        command="python",
        args=["-m", "claw_codex_mcp", "--transport", "stdio"],
        env=env,
    )


def _payload(result) -> dict:
    assert result.content
    return json.loads(result.content[0].text)


def _index_path(tmp_path: Path) -> Path:
    index_path = tmp_path / "decisions_index.db"
    build_index(index_path, [DECISIONS_ROOT])
    return index_path


@pytest.mark.asyncio
async def test_stdio_lists_exactly_four_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(SLICE_DB))
    server_params = _server_params({**os.environ})
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert names == {
                "cam_recall", "cam_provenance",
                "cam_decisions_search", "cam_record_outcome",
            }


@pytest.mark.asyncio
async def test_stdio_recall_returns_real_results(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(SLICE_DB))
    monkeypatch.setenv("CAM_CODEX_MCP_OUTCOME_DB_PATH", str(tmp_path / "outcome.db"))
    server_params = _server_params({**os.environ})
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "cam_recall", {"query": "data", "k": 3}
            )
            payload = _payload(result)
            assert payload["corpus_status"] in {"connected", "degraded"}
            assert payload["results"]


@pytest.mark.asyncio
async def test_stdio_connected_calls_all_four_tools(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(SLICE_DB))
    monkeypatch.setenv("CAM_CODEX_MCP_OUTCOME_DB_PATH", str(tmp_path / "outcome.db"))
    monkeypatch.setenv("CAM_CODEX_MCP_DECISIONS_INDEX", str(_index_path(tmp_path)))
    server_params = _server_params({**os.environ})

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {t.name for t in tools.tools} == {
                "cam_recall", "cam_provenance",
                "cam_decisions_search", "cam_record_outcome",
            }

            recall = _payload(await session.call_tool(
                "cam_recall", {"query": "data", "k": 3, "include_embryonic": True}
            ))
            assert recall["results"]
            methodology_id = recall["results"][0]["methodology_id"]

            provenance = _payload(await session.call_tool(
                "cam_provenance", {"methodology_id": methodology_id}
            ))
            assert provenance["found"] is True
            assert provenance["methodology_id"] == methodology_id

            decisions = _payload(await session.call_tool(
                "cam_decisions_search", {"query": "mock data", "k": 2}
            ))
            assert decisions["results"]
            assert "mock" in decisions["results"][0]["snippet"].lower()

            outcome = _payload(await session.call_tool(
                "cam_record_outcome",
                {
                    "methodology_ids": [methodology_id],
                    "task_id": "stdio-connected",
                    "repo": str(Path.cwd()),
                    "outcome": "green",
                    "evidence": {"test": "test_stdio_connected_calls_all_four_tools"},
                    "run_hash": "stdio-connected-" + ("a" * 16),
                },
            ))
            assert outcome["recorded"] is True
            assert outcome["duplicate"] is False


@pytest.mark.asyncio
async def test_stdio_standalone_calls_all_four_tools_without_fabrication(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    outcome_db = tmp_path / "standalone_outcome.db"
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    monkeypatch.setenv("CAM_CODEX_MCP_OUTCOME_DB_PATH", str(outcome_db))
    monkeypatch.setenv("CAM_CODEX_MCP_DECISIONS_INDEX", str(_index_path(tmp_path)))
    env = {k: v for k, v in os.environ.items() if k != "CAM_CODEX_MCP_DB_PATH"}
    server_params = _server_params(env)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 4

            recall = _payload(await session.call_tool("cam_recall", {"query": "x"}))
            assert recall["results"] == []
            assert recall["corpus_status"] == "absent"
            assert recall["remediation"]

            provenance = _payload(await session.call_tool(
                "cam_provenance", {"methodology_id": "absent-id"}
            ))
            assert provenance["found"] is False
            assert provenance["corpus_status"] == "absent"

            decisions = _payload(await session.call_tool(
                "cam_decisions_search", {"query": "mock data", "k": 2}
            ))
            assert decisions["results"]

            outcome = _payload(await session.call_tool(
                "cam_record_outcome",
                {
                    "methodology_ids": ["standalone-methodology"],
                    "task_id": "stdio-standalone",
                    "repo": str(Path.cwd()),
                    "outcome": "green",
                    "evidence": {"test": "test_stdio_standalone_calls_all_four_tools_without_fabrication"},
                    "run_hash": "stdio-standalone-" + ("b" * 16),
                },
            ))
            assert outcome["recorded"] is True
            assert outcome["corpus_status"] == "absent"

    conn = sqlite3.connect(outcome_db)
    try:
        row = conn.execute(
            "SELECT outcome, run_hash FROM codex_outcome_log WHERE task_id = ?",
            ("stdio-standalone",),
        ).fetchone()
    finally:
        conn.close()
    assert row == ("green", "stdio-standalone-" + ("b" * 16))
