"""CLI metadata checks for the lightweight stdio entrypoint."""

from __future__ import annotations

import inspect

import claw_codex_mcp.__main__ as cli
from claw_codex_mcp.__main__ import TOOL_METADATA
from claw_codex_mcp.server import REGISTERED_TOOLS


def test_cli_tool_metadata_matches_registered_surface() -> None:
    """Lazy stdio metadata must not drift from the canonical 4-tool surface."""
    assert {name for name, _description in TOOL_METADATA} == {
        tool.name for tool in REGISTERED_TOOLS
    }


def test_cli_server_does_not_import_sdk_server_transport() -> None:
    """The stdio entrypoint speaks JSON-RPC directly to keep startup RSS low."""
    source = inspect.getsource(cli)
    assert "mcp.server" not in source
    assert "mcp.server.stdio" not in source
