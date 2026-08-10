import json
import os
from pathlib import Path

import pytest

from tools.cam_manager import (
    ManagerError,
    execute_packet,
    issue_approval,
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
    assert packet["phase"] == "run"
    assert packet["argv"][1:4] == ["models", "benchmark", "run"]
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
        execute_packet(packet_path, state_dir=state)

    approval_path = issue_approval(packet_path, state_dir=state, approved_by="test")
    monkeypatch.setenv("CAM_MANAGER_TEST_OUTPUT", str(output))
    receipt_path, returncode = execute_packet(
        packet_path,
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
        execute_packet(packet_path, approval_path=approval_path, state_dir=state)

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
    receipt_path, returncode = execute_packet(packet_path, state_dir=state)

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
        execute_packet(changed, approval_path=approval_path, state_dir=state)


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
