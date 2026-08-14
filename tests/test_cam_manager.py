from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest

from tools.cam_manager import (
    DEFAULT_CONTRACT,
    ManagerError,
    consume_approval,
    execute_packet,
    issue_approval,
    load_operation_catalog,
    prepare_packet,
    scope_digest,
)


def _fake_wrapper(tmp_path: Path) -> tuple[Path, Path]:
    wrapper = tmp_path / "cam-codx"
    output = tmp_path / "wrapper-output.json"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "path = os.environ['CAM_MANAGER_TEST_OUTPUT']\n"
        "with open(path, 'w', encoding='utf-8') as handle:\n"
        "    json.dump(sys.argv[1:], handle)\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o700)
    return wrapper, output


def test_scope_digest_is_order_stable() -> None:
    assert scope_digest({"b": 2, "a": 1}) == scope_digest({"a": 1, "b": 2})


def test_prepare_packet_freezes_allowlisted_argv_and_secure_state(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="benchmark-run",
        wrapper=wrapper,
        args=["plan.json", "--fixtures", "fixtures.json", "--output", "run"],
        workflow_id="workflow-1",
        target_repo=tmp_path,
        budget_usd=2.5,
        state_dir=state,
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["requires_approval"] is True
    assert packet["operation"] == "models benchmark run"
    assert packet["phase"] == "models"
    assert packet["argv"][1:4] == ["models", "benchmark", "run"]
    assert packet["contract_path"] == str(DEFAULT_CONTRACT.resolve())
    assert len(packet["contract_sha256"]) == 64
    assert packet["operation_policy"]["risk_class"] == "local_record_write"
    assert packet["operation_policy"]["approval_classes"] == [
        "bounded_phase",
        "provider_spend",
    ]
    assert packet["scope_digest"] == scope_digest(packet["scope"])
    assert state.stat().st_mode & 0o777 == 0o700
    assert packet_path.stat().st_mode & 0o777 == 0o600


def test_mutating_packet_requires_matching_single_use_approval(tmp_path: Path, monkeypatch) -> None:
    wrapper, output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="self-enhance-start",
        wrapper=wrapper,
        args=["--mode", "supervised", "--max-tasks", "1", "--skip-swap"],
        workflow_id="workflow-2",
        target_repo=tmp_path,
        state_dir=state,
    )

    with pytest.raises(ManagerError, match="requires an approval"):
        execute_packet(packet_path, state_dir=state, wrapper=wrapper)

    approval_path = issue_approval(packet_path, state_dir=state, approved_by="test")
    monkeypatch.setenv("CAM_MANAGER_TEST_OUTPUT", str(output))
    receipt_path, returncode = execute_packet(
        packet_path,
        wrapper=wrapper,
        approval_path=approval_path,
        state_dir=state,
    )

    assert returncode == 0
    assert receipt_path is not None and receipt_path.is_file()
    assert json.loads(output.read_text(encoding="utf-8")) == [
        "self-enhance",
        "start",
        "--mode",
        "supervised",
        "--max-tasks",
        "1",
        "--skip-swap",
    ]
    with pytest.raises(ManagerError, match="already been consumed"):
        execute_packet(
            packet_path, approval_path=approval_path, state_dir=state, wrapper=wrapper
        )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert "stdout" not in receipt and "stderr" not in receipt


def test_read_only_packet_runs_without_approval(tmp_path: Path, monkeypatch) -> None:
    wrapper, output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="models-current",
        wrapper=wrapper,
        args=["--format", "json"],
        state_dir=state,
    )
    monkeypatch.setenv("CAM_MANAGER_TEST_OUTPUT", str(output))
    receipt_path, returncode = execute_packet(
        packet_path, state_dir=state, wrapper=wrapper
    )

    assert returncode == 0
    assert receipt_path is not None
    assert json.loads(output.read_text(encoding="utf-8")) == [
        "models",
        "current",
        "--format",
        "json",
    ]


def test_changed_packet_scope_cannot_use_old_approval(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="benchmark-run",
        wrapper=wrapper,
        args=["plan.json"],
        state_dir=state,
    )
    approval_path = issue_approval(packet_path, state_dir=state)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["argv"].append("--different")
    packet["scope"]["argv"].append("--different")
    packet["scope_digest"] = scope_digest(packet["scope"])
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(ManagerError, match="scope mismatch"):
        execute_packet(
            changed, approval_path=approval_path, state_dir=state, wrapper=wrapper
        )


def test_secret_bearing_arguments_are_rejected(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    with pytest.raises(ManagerError, match="Secret-bearing"):
        prepare_packet(
            operation="models-catalog",
            wrapper=wrapper,
            args=["--api-key", "not-a-secret"],
            state_dir=tmp_path / "state",
        )


@pytest.mark.parametrize(
    ("operation", "expected_prefix"),
    [
        ("models-promote", ["models", "set"]),
        ("models-rollback", ["models", "rollback"]),
        ("models-profile-use", ["models", "profile", "use"]),
    ],
)
def test_model_mutation_operations_use_current_cam_cli_prefixes(
    tmp_path: Path, operation: str, expected_prefix: list[str]
) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    packet_path = prepare_packet(
        operation=operation,
        wrapper=wrapper,
        args=["example"],
        state_dir=tmp_path / "state",
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["requires_approval"] is True
    assert packet["argv"][1 : 1 + len(expected_prefix)] == expected_prefix


def test_catalog_covers_exactly_managed_canonical_commands_with_fixed_prefixes_and_phases() -> None:
    registry = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    expected = {
        route["command_path"]: route
        for route in registry["command_routes"]
        if route["kind"] == "command"
        and route["classification"] == "managed"
        and route["command_status"] == "canonical"
    }

    catalog = load_operation_catalog()

    assert set(catalog) == set(expected)
    for command_path, policy in catalog.items():
        route = expected[command_path]
        assert policy.argv_prefix == tuple(command_path.split())
        assert policy.phase == route["cam_codx_route"]
        assert policy.risk_class == route["risk_class"]
        assert policy.side_effect_class == route["side_effect_class"]
        assert policy.approval_classes == tuple(route["approval_classes"])
        assert policy.requires_approval is (route["approval_classes"] != ["none"])


def test_hidden_canonical_operations_are_selectable_but_runtime_aliases_and_groups_are_not() -> None:
    catalog = load_operation_catalog()

    assert "evolution approve" in catalog
    assert "govern" in catalog
    assert "mine-report" in catalog
    assert "prism-demo" in catalog
    assert "forge-export" not in catalog
    assert "quickstart" not in catalog
    assert "models" not in catalog
    assert "chat" not in catalog
    assert "mcp" not in catalog


@pytest.mark.parametrize(
    ("operation", "risk_class", "side_effect_class", "approval_classes", "requires_approval"),
    [
        ("brief-query", "read_only", "none", ("none",), False),
        ("task add", "local_record_write", "local_state_write", ("bounded_phase",), True),
        (
            "mine",
            "corpus_write",
            "corpus_or_ledger_write",
            ("bounded_phase", "provider_spend"),
            True,
        ),
        (
            "validate",
            "target_code_mutation",
            "validation_command_execution",
            ("target_mutation",),
            True,
        ),
        (
            "models set",
            "promotion_configuration",
            "configuration_or_selection_write",
            ("configuration_change", "promotion"),
            True,
        ),
        (
            "self-enhance swap",
            "cam_live_mutation",
            "live_runtime_and_configuration_write",
            ("configuration_change", "promotion", "live_cam_mutation"),
            True,
        ),
    ],
)
def test_packets_preserve_each_contract_policy_class(
    tmp_path: Path,
    operation: str,
    risk_class: str,
    side_effect_class: str,
    approval_classes: tuple[str, ...],
    requires_approval: bool,
) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)

    packet_path = prepare_packet(
        operation=operation,
        wrapper=wrapper,
        state_dir=tmp_path / "state",
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet["operation"] == operation
    assert packet["operation_policy"]["risk_class"] == risk_class
    assert packet["operation_policy"]["side_effect_class"] == side_effect_class
    assert tuple(packet["operation_policy"]["approval_classes"]) == approval_classes
    assert packet["requires_approval"] is requires_approval


@pytest.mark.parametrize("operation", ["models", "chat", "forge-export", "quickstart"])
def test_noncanonical_manager_routes_fail_closed(tmp_path: Path, operation: str) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)

    with pytest.raises(ManagerError, match="Unsupported manager operation"):
        prepare_packet(
            operation=operation,
            wrapper=wrapper,
            state_dir=tmp_path / "state",
        )


def test_missing_or_malformed_contract_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    malformed = tmp_path / "malformed.json"
    malformed.write_text(
        '{"schema_version":"2.0","workflow_intents":{"assess":{"description":"x","default_command":"brief-query"}},"command_routes":[]}',
        encoding="utf-8",
    )

    with pytest.raises(ManagerError, match="capability contract"):
        load_operation_catalog(missing)
    with pytest.raises(ManagerError, match="command_routes"):
        load_operation_catalog(malformed)


def test_contract_policy_contradiction_fails_closed(tmp_path: Path) -> None:
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    mine = next(
        route for route in contract["command_routes"] if route["command_path"] == "mine"
    )
    mine["approval_class"] = "none"
    mine["approval_classes"] = ["none"]
    malformed = tmp_path / "unsafe-contract.json"
    malformed.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ManagerError, match="policy is invalid"):
        load_operation_catalog(malformed)


def test_packet_execution_fails_when_contract_drifts(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    contract = tmp_path / "contract.json"
    contract.write_bytes(DEFAULT_CONTRACT.read_bytes())
    packet_path = prepare_packet(
        operation="models current",
        wrapper=wrapper,
        state_dir=tmp_path / "state",
        contract_path=contract,
    )
    payload = json.loads(contract.read_text(encoding="utf-8"))
    payload["checked_date"] = "2099-01-01"
    contract.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ManagerError, match="contract.*drift"):
        execute_packet(
            packet_path,
            state_dir=tmp_path / "state",
            wrapper=wrapper,
            contract_path=contract,
        )


def test_read_only_packet_rejects_recomputed_scope_tampering(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="models current",
        wrapper=wrapper,
        state_dir=state,
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["argv"].append("--tampered")
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(ManagerError, match="scope digest"):
        execute_packet(changed, state_dir=state, wrapper=wrapper)


def test_execution_rejects_recomputed_wrapper_substitution(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="models current",
        wrapper=wrapper,
        state_dir=state,
    )
    marker = tmp_path / "evil-ran"
    evil = tmp_path / "evil-wrapper"
    evil.write_text(f"#!/bin/sh\nprintf evil > {marker}\n", encoding="utf-8")
    evil.chmod(0o700)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["wrapper"] = str(evil)
    packet["argv"][0] = str(evil)
    packet["scope"]["wrapper"] = str(evil)
    packet["scope"]["argv"][0] = str(evil)
    packet["scope_digest"] = scope_digest(packet["scope"])
    changed = tmp_path / "changed-wrapper.json"
    changed.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(ManagerError, match="trusted CAM wrapper"):
        execute_packet(changed, state_dir=state, wrapper=wrapper)
    assert not marker.exists()


def test_execution_rejects_in_place_wrapper_replacement(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="models current",
        wrapper=wrapper,
        state_dir=state,
    )
    marker = tmp_path / "replacement-ran"
    wrapper.write_text(f"#!/bin/sh\nprintf replaced > {marker}\n", encoding="utf-8")
    wrapper.chmod(0o700)

    with pytest.raises(ManagerError, match="wrapper content has changed"):
        execute_packet(packet_path, state_dir=state, wrapper=wrapper)
    assert not marker.exists()


def test_packet_rejects_top_level_policy_that_differs_from_bound_scope(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="models current",
        wrapper=wrapper,
        state_dir=state,
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["operation_policy"]["approval_classes"] = ["none", "provider_spend"]
    changed = tmp_path / "changed-policy.json"
    changed.write_text(json.dumps(packet), encoding="utf-8")

    with pytest.raises(ManagerError, match="scope"):
        execute_packet(changed, state_dir=state, wrapper=wrapper)


@pytest.mark.parametrize("budget", [-1.0, math.inf, -math.inf, math.nan])
def test_invalid_budgets_are_rejected(tmp_path: Path, budget: float) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)

    with pytest.raises(ManagerError, match="budget_usd"):
        prepare_packet(
            operation="models current",
            wrapper=wrapper,
            budget_usd=budget,
            state_dir=tmp_path / "state",
        )


def test_expired_approval_is_rejected(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="task add",
        wrapper=wrapper,
        state_dir=state,
    )
    approval_path = issue_approval(packet_path, state_dir=state)
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval["expires_at"] = "2000-01-01T00:00:00Z"
    approval_path.write_text(json.dumps(approval), encoding="utf-8")

    with pytest.raises(ManagerError, match="expired"):
        execute_packet(
            packet_path, approval_path=approval_path, state_dir=state, wrapper=wrapper
        )


def test_approval_consumption_is_atomic_under_concurrency(tmp_path: Path) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(operation="task add", wrapper=wrapper, state_dir=state)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    approval_path = issue_approval(packet_path, state_dir=state)
    barrier = Barrier(2)

    def consume() -> str:
        barrier.wait()
        try:
            consume_approval(approval_path, packet, state_dir=state)
        except ManagerError as exc:
            return str(exc)
        return "consumed"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: consume(), range(2)))

    assert results.count("consumed") == 1
    assert sum("already been consumed" in result for result in results) == 1


def test_dry_run_validates_but_does_not_consume_approval(
    tmp_path: Path, monkeypatch
) -> None:
    wrapper, output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(operation="task add", wrapper=wrapper, state_dir=state)
    approval_path = issue_approval(packet_path, state_dir=state)

    assert execute_packet(
        packet_path,
        state_dir=state,
        wrapper=wrapper,
        approval_path=approval_path,
        dry_run=True,
    ) == (None, None)

    monkeypatch.setenv("CAM_MANAGER_TEST_OUTPUT", str(output))
    receipt, returncode = execute_packet(
        packet_path,
        state_dir=state,
        wrapper=wrapper,
        approval_path=approval_path,
    )
    assert receipt is not None
    assert returncode == 0


def test_execution_uses_list_form_subprocess_without_a_shell(tmp_path: Path, monkeypatch) -> None:
    wrapper, _output = _fake_wrapper(tmp_path)
    state = tmp_path / "state"
    packet_path = prepare_packet(
        operation="models current",
        wrapper=wrapper,
        state_dir=state,
    )
    calls: list[tuple[list[str], dict]] = []

    def fake_run(argv: list[str], **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("tools.cam_manager.subprocess.run", fake_run)

    execute_packet(packet_path, state_dir=state, wrapper=wrapper)

    assert calls == [
        (
            [str(wrapper.resolve()), "models", "current"],
            {
                "cwd": None,
                "text": True,
                "stdout": pytest.importorskip("subprocess").PIPE,
                "stderr": pytest.importorskip("subprocess").PIPE,
                "check": False,
                "shell": False,
            },
        )
    ]
