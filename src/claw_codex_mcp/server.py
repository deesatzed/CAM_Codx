"""MCP server registration. Hard 4-tool ceiling enforced here.

build_specs.md §3 + §10.5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from claw_codex_mcp.tools.recall import handle_recall
from claw_codex_mcp.tools.provenance import handle_provenance
from claw_codex_mcp.tools.decisions_search import handle_decisions_search
from claw_codex_mcp.tools.record_outcome import handle_record_outcome


@dataclass(frozen=True)
class ToolRegistration:
    name: str
    handler: Callable[..., Any]
    description: str


REGISTERED_TOOLS: tuple[ToolRegistration, ...] = (
    ToolRegistration(
        name="cam_recall",
        handler=handle_recall,
        description="Top-K methodologies for a natural-language query.",
    ),
    ToolRegistration(
        name="cam_provenance",
        handler=handle_provenance,
        description="Full provenance envelope for a methodology_id.",
    ),
    ToolRegistration(
        name="cam_decisions_search",
        handler=handle_decisions_search,
        description="FTS5 search across cross-repo DECISIONS.md.",
    ),
    ToolRegistration(
        name="cam_record_outcome",
        handler=handle_record_outcome,
        description="Append-only outcome log for fitness ledger.",
    ),
)

assert len(REGISTERED_TOOLS) == 4, (
    "MCP surface drift: build_specs.md §3 specifies exactly 4 tools."
)
