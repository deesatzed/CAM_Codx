"""verify_claim_2_lightness.py — Claim 5 (LIGHTNESS): new MCP RSS at idle is
<=50% of the legacy 17-tool MCP baseline captured in baselines/legacy_mcp_rss.txt.

Pass condition (100% binary): ratio <= 0.50.

The new MCP RSS is measured by running the server via `--transport stdio` under
`/usr/bin/time -l`, performing a real initialize + tools/list round-trip (one
per tool, four total), then measuring peak RSS.  This prevents the falsifier
where an early-exit mode skips loading the tool registry.

The legacy baseline is the `maximum resident set size` line from
baselines/legacy_mcp_rss.txt (captured when the 17-tool CAM_CAM MCP server
was booted and its tools listed).

If the ratio exceeds 0.50, the claim fails.  Per _validation_gates.md: a
worst-case acceptable ratio of ≤0.65 requires explicit user approval recorded
in _coverage_gaps.md.

Run from the codex-cam-methodology-impl/ root.  No CAM_CODEX_MCP_DB_PATH
required (RSS is measured in standalone mode, which still loads the full
tool registry).
"""

from __future__ import annotations

import asyncio
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_RSS_FILE = ROOT / "baselines" / "legacy_mcp_rss.txt"
NEW_RSS_FILE = ROOT / "baselines" / "new_mcp_rss.txt"
RATIO_CEILING = 0.50

CLAIM = "Claim 5 (LIGHTNESS): new MCP RSS at idle <= 50% of 17-tool MCP baseline"

RSS_RE = re.compile(r"^\s*(\d+)\s+maximum resident set size", re.MULTILINE)


def _fail(reason: str) -> None:
    print(f"FAIL  {CLAIM}\n      {reason}", file=sys.stderr)
    sys.exit(1)


def _pass(detail: str = "") -> None:
    suffix = f"\n      {detail}" if detail else ""
    print(f"PASS  {CLAIM}{suffix}")


def _parse_rss(text: str, label: str) -> int:
    m = RSS_RE.search(text)
    if not m:
        _fail(f"no 'maximum resident set size' line found in {label}")
    return int(m.group(1))


def _measure_new_rss() -> int:
    """Measure RSS of claw_codex_mcp by running a real initialize+tools/list session.

    Wraps the MCP stdio server in a small Python driver script that:
    1. Spawns `python -m claw_codex_mcp --transport stdio` as a child,
    2. Sends initialize + tools/list JSON-RPC messages,
    3. Reads the response, then exits.
    The whole driver is run under `/usr/bin/time -l` to capture peak RSS.
    """
    driver = textwrap.dedent(f"""\
        import asyncio, json, os, sys
        from pathlib import Path
        sys.path.insert(0, {str(ROOT / 'src')!r})
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def main():
            env = {{k: v for k, v in os.environ.items() if k != 'CAM_CODEX_MCP_DB_PATH'}}
            server = StdioServerParameters(
                command=sys.executable,
                args=['-m', 'claw_codex_mcp', '--transport', 'stdio'],
                env=env,
                cwd={str(ROOT)!r},
            )
            with open(os.devnull, 'w') as errlog:
                async with stdio_client(server, errlog=errlog) as (r, w):
                    async with ClientSession(r, w) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        print(len(result.tools))

        asyncio.run(main())
    """)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, prefix="rss_probe_"
    ) as tf:
        tf.write(driver)
        probe_path = tf.name

    try:
        cmd = ["/usr/bin/time", "-l", sys.executable, probe_path]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=ROOT,
        )
        # /usr/bin/time writes to stderr; stdout from the driver prints tool count
        time_output = result.stderr
        if result.returncode != 0:
            _fail(
                f"RSS probe script exited {result.returncode}\n"
                f"      stdout: {result.stdout[:400]}\n"
                f"      stderr: {time_output[:400]}"
            )
        # Verify the driver actually exercised the tool registry (4 tools)
        tool_count_str = result.stdout.strip()
        if tool_count_str != "4":
            _fail(
                f"RSS probe found {tool_count_str!r} tools; expected '4'. "
                "The server may not have loaded the full tool registry."
            )
    finally:
        Path(probe_path).unlink(missing_ok=True)

    return _parse_rss(time_output, "new MCP RSS probe output")


def main() -> int:
    if not LEGACY_RSS_FILE.exists():
        _fail(
            f"legacy RSS baseline not found: {LEGACY_RSS_FILE}\n"
            "      Run Phase 1 Gate 1.1 to capture it before running this claim."
        )

    legacy_text = LEGACY_RSS_FILE.read_text(encoding="utf-8")
    legacy_rss = _parse_rss(legacy_text, str(LEGACY_RSS_FILE))

    # If a pre-captured new_mcp_rss.txt exists (from a prior run), use it for
    # comparison but also re-measure to confirm the claim holds live.
    new_rss = _measure_new_rss()

    # Persist the measurement for audit trail
    NEW_RSS_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Write a minimal record; this does NOT cache the result — the gate re-runs
    # each time to ensure the claim holds against the live binary.
    NEW_RSS_FILE.write_text(
        f"measured_bytes={new_rss}\nlegacy_bytes={legacy_rss}\n",
        encoding="utf-8",
    )

    ratio = new_rss / legacy_rss
    detail = (
        f"new={new_rss:,} bytes  legacy={legacy_rss:,} bytes  "
        f"ratio={ratio:.2f} (ceiling={RATIO_CEILING})"
    )

    if ratio > RATIO_CEILING:
        _fail(
            f"{detail}\n"
            f"      Ratio {ratio:.2f} exceeds ceiling {RATIO_CEILING}. "
            "Per workspace policy: gap requires action plan or user waiver in _coverage_gaps.md."
        )

    _pass(detail)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
