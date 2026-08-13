from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "cam_control_plane.py"
CONTRACT = ROOT / "agent-packs" / "contract" / "cam_agent_capabilities.json"
ALL_INTENTS = {
    "assess",
    "plan",
    "build",
    "fix",
    "verify",
    "record",
    "mine",
    "knowledge",
    "models",
    "self-enhance",
    "evolution",
    "doctor",
    "setup",
}


def _runtime_fixture(tmp_path: Path) -> dict[str, Path]:
    target = tmp_path / "target"
    target.mkdir(parents=True)
    (target / "source.py").write_text("value = 1\n", encoding="utf-8")
    runtime = tmp_path / "runtime"
    runtime.mkdir(parents=True)
    command = runtime / "cam"
    command.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
    command.chmod(0o755)
    database = runtime / "claw.db"
    database.write_bytes(b"fixture database")
    config = runtime / "claw.toml"
    config.write_text('[database]\ndb_path = "claw.db"\n', encoding="utf-8")
    profiles = runtime / "model_profiles.toml"
    profiles.write_text('active_profile = "default"\n', encoding="utf-8")
    receipt = runtime / "mining-receipt.json"
    receipt.write_text('{"status":"verified"}\n', encoding="utf-8")
    return {
        "target": target,
        "command": command,
        "database": database,
        "config": config,
        "profiles": profiles,
        "receipt": receipt,
    }


def _request(tmp_path: Path, *, intent: str = "assess"):
    from tools.cam_control_plane import ControlPlaneRequest, RuntimePaths

    fixture = _runtime_fixture(tmp_path)
    return ControlPlaneRequest(
        intent=intent,
        target=fixture["target"],
        request="Continue this build using prior evidence",
        runtime=RuntimePaths(
            command=fixture["command"],
            database=fixture["database"],
            config=fixture["config"],
            model_profiles=fixture["profiles"],
        ),
        run_id="swe-run-001",
        mining_receipt=fixture["receipt"],
    )


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for item in sorted(path.rglob("*")):
        if ".git" in item.parts or not item.is_file():
            continue
        digest.update(str(item.relative_to(path)).encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


@pytest.mark.parametrize("intent", sorted(ALL_INTENTS))
def test_plan_supports_every_workflow_intent_without_execution(tmp_path: Path, intent: str) -> None:
    from tools.cam_control_plane import plan_request

    request = _request(tmp_path, intent=intent)
    before = {
        "target": _digest(request.target),
        "database": _digest(request.runtime.database),
        "config": _digest(request.runtime.config),
        "model_profiles": _digest(request.runtime.model_profiles),
    }

    result = plan_request(request, registry_path=CONTRACT)

    after = {
        "target": _digest(request.target),
        "database": _digest(request.runtime.database),
        "config": _digest(request.runtime.config),
        "model_profiles": _digest(request.runtime.model_profiles),
    }
    assert result.intent == intent
    assert result.goal == request.request
    assert result.target == request.target.resolve()
    assert result.run_id == "swe-run-001"
    assert result.mining_receipt == request.mining_receipt.resolve()
    assert result.route.command_path
    assert result.route.cam_codx_route == intent
    assert result.planning_writes == "none"
    assert result.operation_executed is False
    assert result.next_action
    assert before == after == result.identity_hashes


def test_plan_selects_a_registry_backed_safe_default() -> None:
    from tools.cam_control_plane import select_route

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    route = select_route(contract, intent="assess")

    assert route.command_path == "brief-query"
    assert route.memory_mode == "read_only"
    assert route.provider_spend is False
    assert route.approval_classes == ("none",)


def test_explicit_operation_must_exist_and_match_the_intent(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path, intent="models")
    with pytest.raises(ControlPlaneError, match="not registered"):
        plan_request(replace(request, operation="models imaginary"), registry_path=CONTRACT)
    with pytest.raises(ControlPlaneError, match="belongs to intent"):
        plan_request(replace(request, operation="brief-query"), registry_path=CONTRACT)


def test_unknown_intent_is_rejected(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    with pytest.raises(ControlPlaneError, match="Unknown intent"):
        plan_request(_request(tmp_path, intent="invent-magic"), registry_path=CONTRACT)


@pytest.mark.parametrize("field", ["database", "config"])
def test_ambiguous_runtime_identity_is_rejected(tmp_path: Path, field: str) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path)
    runtime = request.runtime
    bad_path = tmp_path / f"missing-{field}"
    bad_runtime = replace(runtime, **{field: bad_path})
    with pytest.raises(ControlPlaneError, match=f"CAM {field} identity"):
        plan_request(replace(request, runtime=bad_runtime), registry_path=CONTRACT)


def test_relative_and_colliding_runtime_paths_are_rejected(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path)
    with pytest.raises(ControlPlaneError, match="absolute"):
        plan_request(
            replace(request, runtime=replace(request.runtime, config=Path("claw.toml"))),
            registry_path=CONTRACT,
        )
    with pytest.raises(ControlPlaneError, match="distinct"):
        plan_request(
            replace(request, runtime=replace(request.runtime, config=request.runtime.database)),
            registry_path=CONTRACT,
        )


def test_unresolved_or_non_executable_cam_command_is_rejected(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path)
    request.runtime.command.chmod(0o644)
    with pytest.raises(ControlPlaneError, match="executable"):
        plan_request(request, registry_path=CONTRACT)


def test_registry_missing_commands_fail_closed(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["command_routes"] = [
        route for route in contract["command_routes"] if route["cam_codx_route"] != "setup"
    ]
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ControlPlaneError, match="no managed command"):
        plan_request(_request(tmp_path / "request", intent="setup"), registry_path=registry)


def test_optional_run_and_receipt_are_optional(tmp_path: Path) -> None:
    from tools.cam_control_plane import plan_request

    request = _request(tmp_path)
    result = plan_request(
        replace(request, run_id=None, mining_receipt=None), registry_path=CONTRACT
    )

    assert result.run_id is None
    assert result.mining_receipt is None


def _cli_args(fixture: dict[str, Path]) -> list[str]:
    return [
        sys.executable,
        str(TOOL),
        "plan",
        "--intent",
        "assess",
        "--target",
        str(fixture["target"]),
        "--request",
        "Continue this build",
        "--cam-command",
        str(fixture["command"]),
        "--cam-db",
        str(fixture["database"]),
        "--cam-config",
        str(fixture["config"]),
        "--model-profiles",
        str(fixture["profiles"]),
    ]


def test_cli_json_and_human_card_expose_required_fields(tmp_path: Path) -> None:
    fixture = _runtime_fixture(tmp_path)
    json_result = subprocess.run(
        [*_cli_args(fixture), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert json_result.returncode == 0, json_result.stderr
    payload = json.loads(json_result.stdout)
    assert payload["goal"] == "Continue this build"
    assert payload["route"]["command_path"] == "brief-query"
    assert payload["planning_writes"] == "none"
    assert payload["operation_executed"] is False
    assert payload["mining"] == "not requested"

    card = subprocess.run(
        _cli_args(fixture),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert card.returncode == 0, card.stderr
    for label in (
        "Goal:",
        "Route:",
        "Target:",
        "Memory mode:",
        "Writes:",
        "Provider spend:",
        "Mining:",
        "Approval:",
        "Next action:",
    ):
        assert label in card.stdout


def test_cli_help_lists_plan_without_touching_runtime(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "plan" in result.stdout
    assert list(tmp_path.iterdir()) == []
