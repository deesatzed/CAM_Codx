"""CAM_Codx's single read-only packet for graph context."""

from __future__ import annotations

import json
from pathlib import Path

from tools.cam_manager import execute_packet, prepare_packet


def _fake_wrapper(tmp_path: Path) -> tuple[Path, Path]:
    wrapper = tmp_path / "cam-codx"
    output = tmp_path / "argv.json"
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "Path = __import__('pathlib').Path\n"
        "Path(os.environ['CAM_MANAGER_TEST_OUTPUT']).write_text(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o700)
    return wrapper, output


def test_registry_exposes_graph_route_as_hidden_managed_read_only() -> None:
    from tools.cam_manager import load_operation_catalog

    policy = load_operation_catalog()["knowledge-graph-query"]
    assert policy.phase == "knowledge"
    assert policy.risk_class == "read_only"
    assert policy.side_effect_class == "none"
    assert policy.approval_classes == ("none",)


def test_graph_packet_uses_fixed_list_form_without_approval(tmp_path: Path, monkeypatch) -> None:
    wrapper, output = _fake_wrapper(tmp_path)
    packet = prepare_packet(
        operation="knowledge-graph-query",
        wrapper=wrapper,
        args=[
            "--db", "/tmp/fixture.db",
            "--snapshot-id", "fixture-auth-v1",
            "--seed-node-id", "source_file:auth_service",
            "--json",
        ],
        state_dir=tmp_path / "state",
    )
    monkeypatch.setenv("CAM_MANAGER_TEST_OUTPUT", str(output))
    _receipt, returncode = execute_packet(packet, wrapper=wrapper, state_dir=tmp_path / "state")

    assert returncode == 0
    assert json.loads(output.read_text())[:4] == [
        "knowledge-graph-query",
        "--db",
        "/tmp/fixture.db",
        "--snapshot-id",
    ]
