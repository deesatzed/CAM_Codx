"""GAP-COV-1 — direct unit tests for claw_codex_mcp.__main__ dispatch functions.

build_specs.md §6 + §10.2.  These tests import the functions directly (not via
subprocess) so coverage.py can instrument them.  They do not exercise the MCP
SDK stdio transport — that path is tested in test_stdio_integration.py.
"""

from __future__ import annotations

import asyncio
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ── helpers ──────────────────────────────────────────────────────────────────


def _req(method: str, params: dict | None = None, id_: int = 1) -> dict:
    r: dict = {"jsonrpc": "2.0", "method": method, "id": id_}
    if params is not None:
        r["params"] = params
    return r


def _notification(method: str, params: dict | None = None) -> dict:
    """A JSON-RPC notification has no 'id'."""
    r: dict = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        r["params"] = params
    return r


# ── _jsonrpc_result / _jsonrpc_error ─────────────────────────────────────────


def test_jsonrpc_result_shape() -> None:
    from claw_codex_mcp.__main__ import _jsonrpc_result
    r = _jsonrpc_result(42, {"tools": []})
    assert r["jsonrpc"] == "2.0"
    assert r["id"] == 42
    assert r["result"] == {"tools": []}
    assert "error" not in r


def test_jsonrpc_error_shape() -> None:
    from claw_codex_mcp.__main__ import _jsonrpc_error
    r = _jsonrpc_error(7, -32601, "Method not found")
    assert r["jsonrpc"] == "2.0"
    assert r["id"] == 7
    assert r["error"]["code"] == -32601
    assert "result" not in r


# ── _tool_definitions ────────────────────────────────────────────────────────


def test_tool_definitions_returns_four() -> None:
    from claw_codex_mcp.__main__ import _tool_definitions
    defs = _tool_definitions()
    assert len(defs) == 4
    names = [d["name"] for d in defs]
    assert "cam_recall" in names
    assert "cam_provenance" in names
    assert "cam_decisions_search" in names
    assert "cam_record_outcome" in names


# ── _load_tool ────────────────────────────────────────────────────────────────


def test_load_tool_known_names() -> None:
    from claw_codex_mcp.__main__ import _load_tool
    for name in ("cam_recall", "cam_provenance", "cam_decisions_search", "cam_record_outcome"):
        model, handler = _load_tool(name)
        assert model is not None, f"model missing for {name}"
        assert handler is not None, f"handler missing for {name}"


def test_load_tool_unknown_returns_none() -> None:
    from claw_codex_mcp.__main__ import _load_tool
    model, handler = _load_tool("not_a_real_tool")
    assert model is None
    assert handler is None


# ── _get_mode_info ────────────────────────────────────────────────────────────


def test_get_mode_info_returns_mode_info(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_get_mode_info must return a ModeInfo and cache on second call."""
    import claw_codex_mcp.__main__ as main_mod
    from claw_codex_mcp.db import ModeInfo

    # Reset module-level cache so a fresh detect_mode() runs.
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)

    info = main_mod._get_mode_info()
    assert isinstance(info, ModeInfo)
    # Second call returns cached instance.
    info2 = main_mod._get_mode_info()
    assert info is info2

    # Restore so other tests start clean.
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


# ── _handle_request ───────────────────────────────────────────────────────────


def test_handle_request_notification_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Notifications (no 'id') must not generate a response."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)

    result = main_mod._handle_request(_notification("initialized"))
    assert result is None
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_handle_request_initialize(monkeypatch: pytest.MonkeyPatch) -> None:
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)

    r = main_mod._handle_request(_req("initialize", {"protocolVersion": "2025-11-25"}))
    assert r is not None
    assert r["result"]["serverInfo"]["name"] == "claw_codex_mcp"
    assert r["result"]["capabilities"]["tools"] == {}
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_handle_request_ping(monkeypatch: pytest.MonkeyPatch) -> None:
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    main_mod._get_mode_info()  # warm cache

    r = main_mod._handle_request(_req("ping"))
    assert r is not None
    assert r["result"] == {}
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_handle_request_tools_list(monkeypatch: pytest.MonkeyPatch) -> None:
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    main_mod._get_mode_info()

    r = main_mod._handle_request(_req("tools/list"))
    assert r is not None
    assert len(r["result"]["tools"]) == 4
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_handle_request_unknown_method(monkeypatch: pytest.MonkeyPatch) -> None:
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    main_mod._get_mode_info()

    r = main_mod._handle_request(_req("no/such/method"))
    assert r is not None
    assert r["error"]["code"] == -32601
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_handle_request_tools_call_invalid_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """tools/call with non-string name returns -32602."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    main_mod._get_mode_info()

    r = main_mod._handle_request(_req("tools/call", {"name": 123, "arguments": {}}))
    assert r is not None
    assert r["error"]["code"] == -32602
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_handle_request_tools_call_unknown_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """tools/call with unknown tool name returns isError=True."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    main_mod._get_mode_info()

    r = main_mod._handle_request(_req("tools/call", {"name": "nonexistent_tool", "arguments": {}}))
    assert r is not None
    result = r["result"]
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "error" in payload
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


# ── _call_tool ────────────────────────────────────────────────────────────────


def test_call_tool_unknown_name_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)

    info = main_mod._get_mode_info()
    result = asyncio.run(main_mod._call_tool("bad_tool", {}, info))
    assert result["isError"] is True
    assert "unknown tool" in result["content"][0]["text"]
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


# ── _serve_stdio ──────────────────────────────────────────────────────────────


def test_serve_stdio_handles_ping(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """_serve_stdio reads lines from stdin, writes JSON-RPC responses to stdout."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    # Warm mode cache so initialize is not triggered by ping.
    main_mod._get_mode_info()

    ping = json.dumps({"jsonrpc": "2.0", "method": "ping", "id": 99}) + "\n"
    fake_stdin = io.StringIO(ping)
    output_lines: list[str] = []

    with patch.object(sys, "stdin", fake_stdin):
        with patch.object(main_mod, "_write_message", side_effect=lambda m: output_lines.append(json.dumps(m))):
            exit_code = main_mod._serve_stdio()

    assert exit_code == 0
    assert len(output_lines) == 1
    msg = json.loads(output_lines[0])
    assert msg["id"] == 99
    assert msg["result"] == {}
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_serve_stdio_handles_parse_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """_serve_stdio emits -32700 on malformed JSON and continues."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    main_mod._get_mode_info()

    bad_line = "not valid json\n"
    fake_stdin = io.StringIO(bad_line)
    output_lines: list[str] = []

    with patch.object(sys, "stdin", fake_stdin):
        with patch.object(main_mod, "_write_message", side_effect=lambda m: output_lines.append(json.dumps(m))):
            exit_code = main_mod._serve_stdio()

    assert exit_code == 0
    assert len(output_lines) == 1
    msg = json.loads(output_lines[0])
    assert msg["error"]["code"] == -32700
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_serve_stdio_notification_produces_no_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """A notification (no id) must not produce a response message."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    main_mod._get_mode_info()

    notif = json.dumps({"jsonrpc": "2.0", "method": "initialized"}) + "\n"
    fake_stdin = io.StringIO(notif)
    output_lines: list[str] = []

    with patch.object(sys, "stdin", fake_stdin):
        with patch.object(main_mod, "_write_message", side_effect=lambda m: output_lines.append(json.dumps(m))):
            exit_code = main_mod._serve_stdio()

    assert exit_code == 0
    assert output_lines == []
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


# ── main() ────────────────────────────────────────────────────────────────────


def test_main_version_flag(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(sys, "argv", ["claw_codex_mcp", "--version"])
    code = main_mod.main()
    assert code == 0
    out = capsys.readouterr().out.strip()
    from claw_codex_mcp import __version__
    assert out == __version__


def test_main_bad_args_returns_2(monkeypatch: pytest.MonkeyPatch) -> None:
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(sys, "argv", ["claw_codex_mcp", "--unknown-flag"])
    code = main_mod.main()
    assert code == 2


def test_main_transport_stdio_runs_serve(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() with --transport stdio delegates to _serve_stdio."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(sys, "argv", ["claw_codex_mcp", "--transport", "stdio"])
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)

    # Feed an empty stdin so _serve_stdio returns immediately.
    with patch.object(sys, "stdin", io.StringIO("")):
        code = main_mod.main()
    assert code == 0
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)


def test_main_transport_stdio_equals_form(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() with --transport=stdio (equals form) also works."""
    import claw_codex_mcp.__main__ as main_mod
    monkeypatch.setattr(sys, "argv", ["claw_codex_mcp", "--transport=stdio"])
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)

    with patch.object(sys, "stdin", io.StringIO("")):
        code = main_mod.main()
    assert code == 0
    monkeypatch.setattr(main_mod, "_MODE_INFO", None)
