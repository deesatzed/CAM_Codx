"""Hard ceiling test: the MCP must expose exactly 4 tools.

See build_specs.md §10.5. This test must be present from the first commit
of the new package and must never be quarantined.
"""

from claw_codex_mcp.server import REGISTERED_TOOLS


def test_mcp_surface_is_exactly_four_tools() -> None:
    expected = {"cam_recall", "cam_provenance", "cam_decisions_search", "cam_record_outcome"}
    actual = {t.name for t in REGISTERED_TOOLS}
    assert actual == expected, (
        f"MCP surface drift: missing={expected - actual}, extra={actual - expected}. "
        f"Adding a tool requires updating build_specs.md §3 first."
    )
