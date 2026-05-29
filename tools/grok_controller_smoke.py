"""Smoke checks for the Grok controller surface.

This script intentionally verifies Grok discovery and project MCP config without
mutating user-level ``~/.grok/config.toml``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG = ROOT / ".grok" / "config.toml"
MCP_JSON = ROOT / ".mcp.json"
PROJECT_RULES = ROOT / "AGENTS.md"


def load_project_config(path: Path = PROJECT_CONFIG) -> dict[str, Any]:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def cam_server_config(config: dict[str, Any]) -> dict[str, Any]:
    servers = config.get("mcp_servers", {})
    server = servers.get("cam_cam")
    if not isinstance(server, dict):
        raise ValueError("missing [mcp_servers.cam_cam] in .grok/config.toml")
    return server


def command_invokes_codex(server: dict[str, Any]) -> bool:
    command = str(server.get("command", ""))
    args = [str(arg) for arg in server.get("args", [])]
    executable = Path(command).name.lower()
    return executable == "codex" or any(Path(arg).name.lower() == "codex" for arg in args)


def validate_project_config() -> list[str]:
    config = load_project_config()
    server = cam_server_config(config)
    failures: list[str] = []
    if command_invokes_codex(server):
        failures.append("Grok project MCP server shells out to codex")
    if server.get("command") != "python":
        failures.append("cam_cam MCP command should be python")
    if server.get("args") != ["-m", "claw_codex_mcp", "--transport", "stdio"]:
        failures.append("cam_cam MCP args do not launch claw_codex_mcp over stdio")
    env = server.get("env", {})
    if not isinstance(env, dict) or not env.get("CAM_CODEX_MCP_DB_PATH"):
        failures.append("CAM_CODEX_MCP_DB_PATH is missing")
    if not PROJECT_RULES.exists():
        failures.append("AGENTS.md project rules are missing")
    if not MCP_JSON.exists():
        failures.append(".mcp.json compatibility config is missing")
    else:
        data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
        mcp_server = data.get("mcpServers", {}).get("cam_cam")
        if not isinstance(mcp_server, dict):
            failures.append(".mcp.json missing mcpServers.cam_cam")
        elif command_invokes_codex(mcp_server):
            failures.append(".mcp.json cam_cam shells out to codex")
    return failures


def run_command(args: list[str], *, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def inspect_grok() -> tuple[dict[str, Any] | None, str]:
    result = run_command(["grok", "inspect", "--json"])
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip()
    try:
        return json.loads(result.stdout), ""
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON from grok inspect: {exc}"


def grok_discovers_project_config(inspect_payload: dict[str, Any]) -> bool:
    sources = inspect_payload.get("configSources", {})
    project_paths = [Path(path).resolve() for path in sources.get("projectPaths", [])]
    return PROJECT_CONFIG.resolve() in project_paths


def run_headless_smoke() -> tuple[bool, str]:
    result = run_command(
        [
            "grok",
            "-p",
            "Reply with exactly: grok-cam-ok",
            "--cwd",
            str(ROOT),
            "--output-format",
            "json",
            "--max-turns",
            "1",
            "--disallowed-tools",
            "run_terminal_cmd,search_replace",
        ],
        timeout=60,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0 and "grok-cam-ok" in output, output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Grok controller discovery for CAM.")
    parser.add_argument(
        "--skip-headless",
        action="store_true",
        help="Skip authenticated Grok headless prompt check.",
    )
    args = parser.parse_args(argv)

    failures = validate_project_config()

    version = run_command(["grok", "--version"])
    if version.returncode != 0:
        failures.append(f"grok --version failed: {(version.stderr or version.stdout).strip()}")
    else:
        print(version.stdout.strip())

    inspect_payload, inspect_error = inspect_grok()
    if inspect_payload is None:
        failures.append(f"grok inspect --json failed: {inspect_error}")
    elif not grok_discovers_project_config(inspect_payload):
        failures.append("grok inspect did not discover repo-local .grok/config.toml")
    else:
        print("grok inspect discovered repo-local .grok/config.toml")

    if not args.skip_headless:
        ok, output = run_headless_smoke()
        if not ok:
            failures.append(f"grok headless smoke blocked or failed: {output}")
        else:
            print("grok headless smoke passed")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("GROK CONTROLLER SMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
