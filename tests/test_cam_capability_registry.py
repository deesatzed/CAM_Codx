from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "agent-packs" / "contract" / "cam_agent_capabilities.json"
VALIDATOR_PATH = ROOT / "tools" / "validate_cam_capabilities.py"
MANIFEST_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "cam_command_manifest_v1.json"

WORKFLOW_INTENTS = {
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
CLASSIFICATIONS = {
    "managed",
    "troubleshooting_only",
    "hidden_compatibility",
}
ROUTE_KEYS = {
    "command_path",
    "kind",
    "hidden",
    "command_status",
    "classification",
    "cam_codx_route",
    "risk_class",
    "side_effect_class",
    "default_mode",
    "approval_class",
    "provider_spend",
    "config_change",
    "promotion",
    "artifacts",
    "runtime_source_refs",
}


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _route_path(route: dict) -> str:
    return route["command_path"]


def _manifest_fixture() -> dict:
    return json.loads(MANIFEST_FIXTURE_PATH.read_text(encoding="utf-8"))


def _run_validator(tmp_path: Path, contract: dict, manifest: dict) -> subprocess.CompletedProcess[str]:
    contract_path = tmp_path / "contract.json"
    manifest_path = tmp_path / "manifest.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--contract",
            str(contract_path),
            "--manifest",
            str(manifest_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_contract_schema_2_has_all_approved_workflow_intents() -> None:
    contract = _contract()

    assert contract["schema_version"] == "2.0"
    assert set(contract["workflow_intents"]) == WORKFLOW_INTENTS
    assert contract["command_routes"]
    assert contract["checked_date"] == "2026-08-12"
    assert contract["ownership"]["hub_path"] == "/Volumes/WS4TB/waswiki/CAM_Codx"
    assert contract["ownership"]["runtime_path"] == "/Volumes/WS4TB/waswiki/CAM_CAM"


def test_every_command_route_has_complete_policy_and_runtime_shape() -> None:
    contract = _contract()
    route_paths = []

    for route in contract["command_routes"]:
        assert ROUTE_KEYS <= set(route), route
        assert isinstance(route["command_path"], str) and route["command_path"].strip()
        assert route["command_path"] == " ".join(route["command_path"].split())
        assert route["kind"] in {"command", "group"}
        assert isinstance(route["hidden"], bool)
        assert route["command_status"] in {"canonical", "alias"}
        assert route["classification"] in CLASSIFICATIONS
        assert route["cam_codx_route"] in WORKFLOW_INTENTS
        assert route["risk_class"]
        assert route["side_effect_class"]
        assert route["default_mode"]
        assert route["approval_class"]
        assert isinstance(route["provider_spend"], bool)
        assert isinstance(route["config_change"], bool)
        assert isinstance(route["promotion"], bool)
        assert isinstance(route["artifacts"], list) and route["artifacts"]
        assert isinstance(route["runtime_source_refs"], list) and route["runtime_source_refs"]
        route_paths.append(_route_path(route))

    assert len(route_paths) == 139
    assert len(route_paths) == len(set(route_paths))
    assert Counter(route["classification"] for route in contract["command_routes"])[
        "hidden_compatibility"
    ] == 15


def test_hidden_paths_are_aliases_and_never_managed_choices() -> None:
    routes = _contract()["command_routes"]
    hidden = [route for route in routes if route["classification"] == "hidden_compatibility"]

    assert {_route_path(route) for route in hidden} >= {
        "forge-export",
        "evolution approve",
        "quickstart",
    }
    assert all(route["command_status"] == "alias" for route in hidden)
    assert all(route["hidden"] for route in hidden)
    assert not any(route["classification"] == "managed" for route in hidden)


def test_known_runtime_boundaries_have_conservative_policy() -> None:
    routes = {_route_path(route): route for route in _contract()["command_routes"]}

    provider_routes = {
        "chat",
        "doctor keycheck",
        "doctor status",
        "evaluate",
        "ideate",
        "learn search",
        "preflight",
        "pulse freshness",
        "quickstart",
        "status",
        "task quickstart",
    }
    assert all(routes[path]["provider_spend"] for path in provider_routes)
    assert all(routes[path]["approval_class"] == "provider_spend" for path in provider_routes)

    artifact_writers = {
        "benchmark",
        "doctor audit",
        "forge benchmark",
        "gaps",
        "kb export-kit",
        "kb instances manifest",
        "models benchmark fixtures",
        "models benchmark plan",
        "models benchmark report",
        "kb brains",
        "self-enhance status",
        "synergies",
    }
    assert all(routes[path]["side_effect_class"] != "none" for path in artifact_writers)
    assert all(routes[path]["approval_class"] != "none" for path in artifact_writers)

    for path in {"dashboard", "mcp"}:
        assert routes[path]["risk_class"] == "cam_live_mutation"
        assert routes[path]["default_mode"] == "service"
        assert routes[path]["approval_class"] == "live_cam_mutation"
        assert routes[path]["provider_spend"]
        assert routes[path]["promotion"]

    assert routes["dashboard"]["config_change"]
    assert routes["models catalog"]["risk_class"] == "external_network_read"
    assert routes["premine"]["side_effect_class"] == "external_or_filesystem_write"
    assert routes["validate"]["side_effect_class"] == "validation_command_execution"
    assert routes["evolution champion-db"]["promotion"]

    for path in {"kb brains", "self-enhance status", "synergies"}:
        assert routes[path]["risk_class"] == "local_record_write"
        assert routes[path]["side_effect_class"] == "local_state_write"
        assert routes[path]["default_mode"] == "read_only_if_initialized"
        assert routes[path]["approval_class"] == "bounded_phase"


def test_validator_rejects_spend_without_provider_approval(tmp_path: Path) -> None:
    contract = _contract()
    route = next(route for route in contract["command_routes"] if route["command_path"] == "mine")
    route["approval_class"] = "none"

    result = _run_validator(tmp_path, contract, _manifest_fixture())

    assert result.returncode != 0
    assert "provider spend lacks provider approval" in result.stderr.lower()


def test_validator_accepts_an_exact_manifest(tmp_path: Path) -> None:
    contract = _contract()

    result = _run_validator(tmp_path, contract, _manifest_fixture())

    assert result.returncode == 0, result.stderr
    assert "capability registry valid" in result.stdout.lower()


def test_validator_fails_when_manifest_path_is_missing_from_contract(tmp_path: Path) -> None:
    contract = _contract()
    manifest = _manifest_fixture()
    contract["command_routes"] = contract["command_routes"][1:]

    result = _run_validator(tmp_path, contract, manifest)

    assert result.returncode != 0
    assert "missing command paths" in result.stderr.lower()


def test_validator_fails_on_duplicate_contract_path(tmp_path: Path) -> None:
    contract = _contract()
    manifest = _manifest_fixture()
    contract["command_routes"].append(deepcopy(contract["command_routes"][0]))

    result = _run_validator(tmp_path, contract, manifest)

    assert result.returncode != 0
    assert "duplicate command paths" in result.stderr.lower()


def test_validator_fails_on_multiply_classified_path(tmp_path: Path) -> None:
    contract = _contract()
    manifest = _manifest_fixture()
    duplicate = deepcopy(contract["command_routes"][0])
    duplicate["classification"] = next(
        classification
        for classification in sorted(CLASSIFICATIONS)
        if classification != duplicate["classification"]
    )
    contract["command_routes"].append(duplicate)

    result = _run_validator(tmp_path, contract, manifest)

    assert result.returncode != 0
    assert "multiply classified command paths" in result.stderr.lower()
