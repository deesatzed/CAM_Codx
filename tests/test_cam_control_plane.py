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
    (target / "empty-directory").mkdir()
    (target / ".git").mkdir()
    (target / ".git" / "HEAD").write_text("ref: refs/heads/test\n", encoding="utf-8")
    (target / "source-link.py").symlink_to("source.py")
    runtime = tmp_path / "runtime"
    runtime.mkdir(parents=True)
    command = runtime / "cam"
    marker = runtime / "CAM_WAS_INVOKED"
    command.write_text(
        f"#!/bin/sh\nprintf invoked > {marker}\nexit 99\n", encoding="utf-8"
    )
    command.chmod(0o755)
    database = runtime / "claw.db"
    database.write_bytes(b"fixture database")
    Path(f"{database}-wal").write_bytes(b"fixture wal")
    Path(f"{database}-shm").write_bytes(b"fixture shm")
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
        "marker": marker,
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


def _snapshot(path: Path) -> tuple[tuple[str, str, int, int, int, str], ...]:
    root = path.parent if path.is_file() or path.is_symlink() else path
    items = [path] if path.is_file() or path.is_symlink() else [path, *path.rglob("*")]
    rows = []
    for item in sorted(items, key=lambda value: str(value)):
        relative = "." if item == path else str(item.relative_to(root if item == path else path))
        stat = item.lstat()
        kind = "symlink" if item.is_symlink() else "directory" if item.is_dir() else "file"
        content = ""
        if item.is_symlink():
            content = os.readlink(item)
        elif item.is_file():
            content = hashlib.sha256(item.read_bytes()).hexdigest()
        rows.append((relative, kind, stat.st_mode, stat.st_size, stat.st_mtime_ns, content))
    return tuple(rows)


def _database_snapshot(path: Path) -> tuple:
    return tuple(
        (suffix, candidate.exists(), _snapshot(candidate) if candidate.exists() else ())
        for suffix in ("", "-wal", "-shm", "-journal")
        for candidate in (Path(str(path) + suffix),)
    )


@pytest.mark.parametrize(
    ("intent", "operation"),
    [
        ("knowledge", "kb search"),
        ("models", "models catalog"),
        ("self-enhance", "self-enhance status"),
        ("evolution", "evolution status"),
        ("doctor", "doctor capabilities"),
        ("setup", "setup"),
    ],
)
def test_prepare_admin_packet_is_registry_bound_and_preserves_pinned_inputs(
    tmp_path: Path, intent: str, operation: str
) -> None:
    from tools.cam_control_plane import prepare_admin_packet

    request = replace(_request(tmp_path, intent=intent), operation=operation)
    before = {
        "target": _snapshot(request.target),
        "database": _database_snapshot(request.runtime.database),
        "config": _snapshot(request.runtime.config),
        "profiles": _snapshot(request.runtime.model_profiles),
    }

    packet_path = prepare_admin_packet(
        request,
        wrapper=request.runtime.command,
        state_dir=tmp_path / "manager-state",
        registry_path=CONTRACT,
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["operation"] == operation
    assert packet["argv"][: 1 + len(operation.split())] == [
        str(request.runtime.command),
        *operation.split(),
    ]
    assert packet["workflow_id"] == "swe-run-001"
    assert packet["scope"]["operation"] == operation
    assert not request.runtime.command.parent.joinpath("CAM_WAS_INVOKED").exists()
    assert before == {
        "target": _snapshot(request.target),
        "database": _database_snapshot(request.runtime.database),
        "config": _snapshot(request.runtime.config),
        "profiles": _snapshot(request.runtime.model_profiles),
    }


def test_prepare_mining_packet_binds_coordinator_bounds_without_execution(
    tmp_path: Path,
) -> None:
    from tools.cam_control_plane import prepare_mining_packet
    from tools.cam_pull_mine_dir import PullMineConfig

    request = _request(tmp_path, intent="mine")
    config = PullMineConfig(
        source_root=request.target,
        cam_command=request.runtime.command,
        cam_db=request.runtime.database,
        cam_config=request.runtime.config,
        profiles=request.runtime.model_profiles,
        wrapper=request.runtime.command,
        state_dir=tmp_path / "manager-state",
        exact_model="fixture/approved-model",
        max_repos=3,
        max_minutes=7,
        max_cost_usd=1.25,
    )
    before = _database_snapshot(request.runtime.database)

    mining = prepare_mining_packet(request, config=config, registry_path=CONTRACT)
    packet = json.loads(mining.packet_path.read_text(encoding="utf-8"))

    assert packet["operation"] == "mine-workspace"
    assert packet["workflow_id"] == "swe-run-001"
    assert packet["budget_usd"] == 1.25
    assert packet["argv"][:3] == [str(request.runtime.command), "mine-workspace", str(request.target)]
    assert "--max-repos" in packet["argv"] and "3" in packet["argv"]
    assert "--max-minutes" in packet["argv"] and "7" in packet["argv"]
    assert "--max-cost-usd" in packet["argv"] and "1.25" in packet["argv"]
    assert str(mining.budget_receipt_path) in packet["argv"]
    assert not mining.budget_receipt_path.exists()
    assert not request.runtime.command.parent.joinpath("CAM_WAS_INVOKED").exists()
    assert before == _database_snapshot(request.runtime.database)


@pytest.mark.parametrize("intent", sorted(ALL_INTENTS))
def test_plan_supports_every_workflow_intent_without_execution(tmp_path: Path, intent: str) -> None:
    from tools.cam_control_plane import plan_request

    request = _request(tmp_path, intent=intent)
    before = {
        "target": _snapshot(request.target),
        "database": _database_snapshot(request.runtime.database),
        "config": _snapshot(request.runtime.config),
        "model_profiles": _snapshot(request.runtime.model_profiles),
    }

    result = plan_request(request, registry_path=CONTRACT)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    after = {
        "target": _snapshot(request.target),
        "database": _database_snapshot(request.runtime.database),
        "config": _snapshot(request.runtime.config),
        "model_profiles": _snapshot(request.runtime.model_profiles),
    }
    assert result.intent == intent
    assert result.goal == request.request
    assert result.target == request.target.resolve()
    assert result.run_id == "swe-run-001"
    assert result.mining_receipt == request.mining_receipt.resolve()
    assert result.route.command_path == contract["workflow_intents"][intent]["default_command"]
    assert result.route.cam_codx_route == intent
    assert result.planning_writes == "none"
    assert result.operation_executed is False
    assert result.next_action
    assert before == after
    assert set(result.identity_hashes) == set(before)
    assert not request.runtime.command.parent.joinpath("CAM_WAS_INVOKED").exists()


def test_plan_selects_a_registry_backed_safe_default() -> None:
    from tools.cam_control_plane import select_route

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    route = select_route(contract, intent="assess", request="Continue this build")

    assert route.command_path == "brief-query"
    assert route.memory_mode == "read_only"
    assert route.provider_spend is False
    assert route.approval_classes == ("none",)


def test_identity_hashes_cover_structure_metadata_and_sqlite_sidecars(tmp_path: Path) -> None:
    from tools.cam_control_plane import _identity_hashes

    request = _request(tmp_path)
    baseline = _identity_hashes(request)

    empty = request.target / "empty-directory"
    empty.chmod(0o700)
    assert _identity_hashes(request)["target"] != baseline["target"]

    wal = Path(f"{request.runtime.database}-wal")
    wal.write_bytes(b"changed wal")
    assert _identity_hashes(request)["database"] != baseline["database"]


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


def test_non_default_admin_operation_must_be_explicit() -> None:
    from tools.cam_control_plane import select_route

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert select_route(
        contract, intent="self-enhance", request="Rollback the failed self enhancement"
    ).command_path == "self-enhance status"
    assert select_route(
        contract, intent="models", request="Show the model catalog", operation="models catalog"
    ).command_path == "models catalog"


@pytest.mark.parametrize(
    "request_text",
    [
        "Do not set models; show current models",
        "Compare models set with models current",
        "The docs mention models set",
    ],
)
def test_free_text_cannot_select_a_risk_elevating_operation(request_text: str) -> None:
    from tools.cam_control_plane import select_route

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert select_route(contract, intent="models", request=request_text).command_path == "models current"


@pytest.mark.parametrize("field", ["database", "config"])
def test_ambiguous_runtime_identity_is_rejected(tmp_path: Path, field: str) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path)
    runtime = request.runtime
    bad_path = tmp_path / f"missing-{field}"
    bad_runtime = replace(runtime, **{field: bad_path})
    with pytest.raises(ControlPlaneError, match=f"CAM {field} identity"):
        plan_request(replace(request, runtime=bad_runtime), registry_path=CONTRACT)


def test_config_and_explicit_database_must_name_the_same_file(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path)
    different = request.runtime.database.parent / "different.db"
    different.write_bytes(b"different")
    request.runtime.config.write_text(
        f'[database]\ndb_path = "{different}"\n', encoding="utf-8"
    )

    with pytest.raises(ControlPlaneError, match="config/database identity mismatch"):
        plan_request(request, registry_path=CONTRACT)


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


def test_non_executable_cam_command_is_rejected(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path)
    request.runtime.command.chmod(0o644)
    with pytest.raises(ControlPlaneError, match="executable"):
        plan_request(request, registry_path=CONTRACT)


def test_unresolved_cam_command_is_rejected(tmp_path: Path) -> None:
    from tools.cam_control_plane import ControlPlaneError, plan_request

    request = _request(tmp_path)
    missing = request.runtime.command.parent / "missing-cam"
    with pytest.raises(ControlPlaneError, match="identity is unresolved"):
        plan_request(
            replace(request, runtime=replace(request.runtime, command=missing)),
            registry_path=CONTRACT,
        )


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


def test_malformed_config_fails_as_controlled_cli_error(tmp_path: Path) -> None:
    fixture = _runtime_fixture(tmp_path)
    fixture["config"].write_text('database = "not-a-table"\n', encoding="utf-8")

    completed = subprocess.run(
        [*_cli_args(fixture), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "CAM_Codx plan error:" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_malformed_registry_fails_as_controlled_cli_error(tmp_path: Path) -> None:
    fixture = _runtime_fixture(tmp_path)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["command_routes"][0].pop("approval_classes")
    registry = tmp_path / "malformed-registry.json"
    registry.write_text(json.dumps(contract), encoding="utf-8")

    completed = subprocess.run(
        [*_cli_args(fixture), "--registry", str(registry), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "CAM_Codx plan error:" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_optional_run_and_receipt_are_optional(tmp_path: Path) -> None:
    from tools.cam_control_plane import plan_request

    request = _request(tmp_path)
    result = plan_request(
        replace(request, run_id=None, mining_receipt=None), registry_path=CONTRACT
    )

    assert result.run_id is None
    assert result.mining_receipt is None


def test_assessment_start_packet_is_fixed_list_form_and_preserves_read_only_inputs(
    tmp_path: Path,
) -> None:
    from tools.cam_control_plane import assessment_start_packet

    request = _request(tmp_path)
    before = {
        "target": _snapshot(request.target),
        "database": _database_snapshot(request.runtime.database),
        "config": _snapshot(request.runtime.config),
        "model_profiles": _snapshot(request.runtime.model_profiles),
    }

    packet = assessment_start_packet(request, registry_path=CONTRACT)

    after = {
        "target": _snapshot(request.target),
        "database": _database_snapshot(request.runtime.database),
        "config": _snapshot(request.runtime.config),
        "model_profiles": _snapshot(request.runtime.model_profiles),
    }
    assert packet.argv[:2] == (str(request.runtime.command.resolve()), "managed-run")
    assert packet.argv[-2:] == ("--config", str(request.runtime.config.resolve()))
    payload = json.loads(packet.argv[2])
    assert payload["operation"] == "start"
    assert payload["run_id"] == request.run_id
    assert payload["plan"]["workspace_dir"] == str(request.target.resolve())
    assert payload["plan"]["plan_json"]["target_revision"]
    assert packet.provider_spend is False
    assert packet.mining is False
    assert before == after


def test_submit_managed_run_packet_uses_only_the_fixed_packet(tmp_path: Path) -> None:
    from tools.cam_control_plane import assessment_start_packet, submit_managed_run_packet

    packet = assessment_start_packet(_request(tmp_path), registry_path=CONTRACT)
    calls: list[tuple[str, ...]] = []

    def runner(argv: tuple[str, ...]) -> tuple[int, str, str]:
        calls.append(argv)
        return 0, '{"run_id":"swe-run-001","status":"planning"}\n', ""

    result = submit_managed_run_packet(packet, runner=runner)

    assert calls == [packet.argv]
    assert result == {"run_id": "swe-run-001", "status": "planning"}


def test_assess_composes_the_primary_only_brief_before_managed_run_start(
    tmp_path: Path,
) -> None:
    from tools.cam_control_plane import compose_assessment

    request = _request(tmp_path)
    calls: list[dict[str, object]] = []

    def brief_builder(**kwargs):
        calls.append(kwargs)
        return {"labels": ["direct_precedent", "transferable_analogy", "new_hypothesis"]}

    composition = compose_assessment(
        request,
        registry_path=CONTRACT,
        brief_builder=brief_builder,
    )

    assert composition.brief["labels"] == [
        "direct_precedent",
        "transferable_analogy",
        "new_hypothesis",
    ]
    assert calls[0]["cam_command"] == request.runtime.command.resolve()
    assert calls[0]["cam_database"] == request.runtime.database.resolve()
    assert calls[0]["target_path"] == request.target.resolve()
    assert composition.start_packet.argv[1] == "managed-run"


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
