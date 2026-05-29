"""Entry point: python -m claw_codex_mcp --transport stdio.

build_specs.md §6 (config) + §10.2 (integration).
"""

from __future__ import annotations

import json
import sys
from typing import Any

from claw_codex_mcp import __version__

TOOL_METADATA = (
    ("cam_recall", "Top-K methodologies for a natural-language query."),
    ("cam_provenance", "Full provenance envelope for a methodology_id."),
    ("cam_decisions_search", "FTS5 search across cross-repo DECISIONS.md."),
    ("cam_record_outcome", "Append-only outcome log for fitness ledger."),
)

_MODE_INFO = None


def _load_tool(name: str):
    """Lazy-load schemas and handlers after the MCP call path names a tool."""
    if name == "cam_recall":
        from claw_codex_mcp.schemas import CamRecallInput
        from claw_codex_mcp.tools.recall import handle_recall
        return CamRecallInput, handle_recall
    if name == "cam_provenance":
        from claw_codex_mcp.schemas import CamProvenanceInput
        from claw_codex_mcp.tools.provenance import handle_provenance
        return CamProvenanceInput, handle_provenance
    if name == "cam_decisions_search":
        from claw_codex_mcp.schemas import CamDecisionsSearchInput
        from claw_codex_mcp.tools.decisions_search import handle_decisions_search
        return CamDecisionsSearchInput, handle_decisions_search
    if name == "cam_record_outcome":
        from claw_codex_mcp.schemas import CamRecordOutcomeInput
        from claw_codex_mcp.tools.record_outcome import handle_record_outcome
        return CamRecordOutcomeInput, handle_record_outcome
    return None, None


def _get_mode_info() -> Any:
    global _MODE_INFO
    if _MODE_INFO is None:
        from claw_codex_mcp.db import detect_mode, ensure_outcome_schema

        info = detect_mode()
        sys.stderr.write(
            f"claw_codex_mcp v{__version__} mode={info.mode} "
            f"corpus={info.db_path or 'absent'} "
            f"outcome_db={info.outcome_db_path} "
            f"vec={'available' if info.vec_available else 'unavailable'}\n"
        )
        ensure_outcome_schema(info.outcome_db_path)
        _MODE_INFO = info
    return _MODE_INFO


def _jsonrpc_result(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _jsonrpc_error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {"code": code, "message": message},
    }


def _write_message(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _write_framed_message(message: dict[str, Any]) -> None:
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header + payload)
    sys.stdout.buffer.flush()


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {"name": name, "description": description, "inputSchema": {"type": "object"}}
        for name, description in TOOL_METADATA
    ]


async def _call_tool(name: str, arguments: dict[str, Any], info: Any) -> dict[str, Any]:
    model, handler = _load_tool(name)
    if model is None or handler is None:
        return {
            "content": [
                {"type": "text", "text": json.dumps({"error": "unknown tool"})}
            ],
            "isError": True,
        }
    req = model(**arguments)
    out = await handler(req, info)
    return {
        "content": [{"type": "text", "text": out.model_dump_json()}],
        "isError": False,
    }


def _handle_request(
    request: dict[str, Any],
) -> dict[str, Any] | None:
    method = request.get("method")
    message_id = request.get("id")

    # Notifications do not carry an id and must not receive a response.
    if message_id is None:
        return None

    if method == "initialize":
        _get_mode_info()
        params = request.get("params") or {}
        protocol_version = params.get("protocolVersion") or "2025-11-25"
        return _jsonrpc_result(
            message_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "claw_codex_mcp",
                    "version": __version__,
                },
            },
        )

    if method == "ping":
        return _jsonrpc_result(message_id, {})

    if method == "tools/list":
        return _jsonrpc_result(message_id, {"tools": _tool_definitions()})

    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or not isinstance(arguments, dict):
            return _jsonrpc_error(message_id, -32602, "Invalid tool call params")
        try:
            import asyncio
            result = asyncio.run(_call_tool(name, arguments, _get_mode_info()))
        except Exception as exc:  # pragma: no cover
            # why: exercised manually by malformed external clients; tests cover
            # valid SDK calls and unknown-tool behavior without fabricating
            # handler internals.
            return _jsonrpc_result(
                message_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"error": str(exc)}),
                        }
                    ],
                    "isError": True,
                },
            )
        return _jsonrpc_result(message_id, result)

    return _jsonrpc_error(message_id, -32601, f"Method not found: {method}")


def _parse_content_length(header_line: str) -> int | None:
    name, _, value = header_line.partition(":")
    if name.lower() != "content-length":
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def _serve_stdio() -> int:
    for line in sys.stdin:
        if line.lower().startswith("content-length:"):
            content_length = _parse_content_length(line)
            while True:
                header = sys.stdin.readline()
                if header in {"", "\n", "\r\n"}:
                    break
                if header.lower().startswith("content-length:"):
                    content_length = _parse_content_length(header)
            if content_length is None:
                _write_framed_message(_jsonrpc_error(None, -32700, "Parse error"))
                continue
            line = sys.stdin.read(content_length)
            write_response = _write_framed_message
        else:
            write_response = _write_message
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            write_response(_jsonrpc_error(None, -32700, "Parse error"))
            continue
        response = _handle_request(request)
        if response is not None:
            write_response(response)
    return 0


def main() -> int:
    args = sys.argv[1:]
    if args == ["--version"]:
        print(__version__)
        return 0

    transport = "stdio"
    if args:
        if args == ["--transport", "stdio"] or args == ["--transport=stdio"]:
            transport = "stdio"
        else:
            sys.stderr.write(
                "usage: claw_codex_mcp [--version] [--transport stdio]\n"
            )
            return 2

    if transport == "stdio":
        return _serve_stdio()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
