from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SMOKE_PATH = ROOT / "tools" / "grok_controller_smoke.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("grok_controller_smoke", SMOKE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_grok_project_config_points_at_cam_librarian_without_codex_executable():
    smoke = _load_smoke_module()
    failures = smoke.validate_project_config()
    assert failures == []

    config = smoke.load_project_config()
    server = smoke.cam_server_config(config)
    assert server["command"] == "python"
    assert server["args"] == ["-m", "claw_codex_mcp", "--transport", "stdio"]
    assert not smoke.command_invokes_codex(server)
    assert server["env"]["PYTHONPATH"] == str(ROOT / "src")


def test_standard_mcp_json_points_at_cam_librarian_without_codex_executable():
    smoke = _load_smoke_module()
    data = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = data["mcpServers"]["cam_cam"]
    assert server["command"] == "python"
    assert server["args"] == ["-m", "claw_codex_mcp", "--transport", "stdio"]
    assert server["env"]["PYTHONPATH"] == str(ROOT / "src")
    assert not smoke.command_invokes_codex(server)


def test_grok_project_rules_make_grok_the_controller():
    rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Grok is the primary controller" in rules
    assert "Grok controls. Tests arbitrate. Markdown remembers. CAM librarian cites." in rules
    assert "claw_codex_mcp" in rules
    assert "compatibility surfaces" in rules


def test_grok_inspect_discovers_project_config_when_grok_is_available():
    result = subprocess.run(
        ["grok", "inspect", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    project_paths = payload.get("configSources", {}).get("projectPaths", [])
    assert str((ROOT / ".grok" / "config.toml").resolve()) in project_paths


def test_grok_controller_smoke_script_passes_without_authenticated_headless():
    result = subprocess.run(
        [sys.executable, "tools/grok_controller_smoke.py", "--skip-headless"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "GROK CONTROLLER SMOKE PASS" in result.stdout
