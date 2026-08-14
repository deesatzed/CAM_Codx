from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.cam_manager import load_operation_catalog


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
    "approval_classes",
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


def _manifest_core(manifest: dict) -> dict:
    return {"schema_version": manifest["schema_version"], "items": manifest["items"]}


def _manifest_digest(manifest: dict) -> str:
    encoded = json.dumps(
        _manifest_core(manifest), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    for intent, policy in contract["workflow_intents"].items():
        assert set(policy) == {"description", "default_command"}
        assert policy["description"].strip()
        defaults = [
            route
            for route in contract["command_routes"]
            if route["command_path"] == policy["default_command"]
        ]
        assert len(defaults) == 1, intent
        route = defaults[0]
        assert route["cam_codx_route"] == intent
        assert route["kind"] == "command"
        assert route["command_status"] == "canonical"
        assert route["classification"] == "managed"
        assert route["hidden"] is False


def test_validator_rejects_invalid_intent_default(tmp_path: Path) -> None:
    contract = _contract()
    contract["workflow_intents"]["assess"]["default_command"] = "models current"

    result = _run_validator(tmp_path, contract, _manifest_fixture())

    assert result.returncode != 0
    assert "invalid default command" in result.stderr


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
        assert isinstance(route["approval_classes"], list) and route["approval_classes"]
        assert route["approval_class"] in route["approval_classes"]
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
    ] == 11


def test_hidden_aliases_and_hidden_canonical_commands_are_distinct() -> None:
    routes = _contract()["command_routes"]
    by_path = {_route_path(route): route for route in routes}
    aliases = [route for route in routes if route["command_status"] == "alias"]
    hidden_canonical = {
        "evolution approve",
        "govern",
        "mine-report",
        "prism-demo",
    }

    assert {_route_path(route) for route in aliases} >= {
        "forge-export",
        "quickstart",
    }
    assert all(route["hidden"] for route in aliases)
    assert all(route["classification"] == "hidden_compatibility" for route in aliases)
    assert all(route.get("alias_target") for route in aliases)
    assert all(by_path[route["alias_target"]]["command_status"] == "canonical" for route in aliases)
    assert all(by_path[path]["hidden"] for path in hidden_canonical)
    assert all(by_path[path]["command_status"] == "canonical" for path in hidden_canonical)
    assert all(by_path[path]["classification"] == "managed" for path in hidden_canonical)

    policy_fields = {
        "cam_codx_route",
        "risk_class",
        "side_effect_class",
        "default_mode",
        "approval_class",
        "approval_classes",
        "provider_spend",
        "config_change",
        "promotion",
        "artifacts",
    }
    for route in aliases:
        target = by_path[route["alias_target"]]
        assert {field: route[field] for field in policy_fields} == {
            field: target[field] for field in policy_fields
        }


def test_manager_catalog_selects_every_and_only_executable_managed_canonical_route() -> None:
    routes = _contract()["command_routes"]
    expected = {
        route["command_path"]
        for route in routes
        if route["kind"] == "command"
        and route["classification"] == "managed"
        and route["command_status"] == "canonical"
    }

    assert set(load_operation_catalog()) == expected


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
    assert routes["kb community publish"]["risk_class"] == "external_network_mutation"
    assert routes["kb community import"]["risk_class"] == "external_network_read"
    assert "external_network" in routes["kb community publish"]["approval_classes"]
    assert "bounded_phase" in routes["kb community import"]["approval_classes"]
    assert routes["mine-report"]["risk_class"] == "read_only"
    assert not routes["mine-report"]["provider_spend"]

    for path in {"kb brains", "self-enhance status", "synergies"}:
        assert routes[path]["risk_class"] == "local_record_write"
        assert routes[path]["side_effect_class"] == "local_state_write"
        assert routes[path]["default_mode"] == "read_only_if_initialized"
        assert routes[path]["approval_class"] == "bounded_phase"


def test_validator_rejects_spend_without_provider_approval(tmp_path: Path) -> None:
    contract = _contract()
    route = next(route for route in contract["command_routes"] if route["command_path"] == "mine")
    route["approval_class"] = "bounded_phase"
    route["approval_classes"] = ["bounded_phase"]

    result = _run_validator(tmp_path, contract, _manifest_fixture())

    assert result.returncode != 0
    assert "provider spend lacks provider approval" in result.stderr.lower()


@pytest.mark.parametrize(
    ("path", "changes", "message"),
    [
        (
            "doctor keycheck",
            {"provider_spend": False, "approval_class": "none", "approval_classes": ["none"]},
            "external provider risk requires provider spend",
        ),
        (
            "init",
            {"config_change": False, "approval_class": "bounded_phase", "approval_classes": ["bounded_phase"]},
            "configuration write requires config change",
        ),
        (
            "evolution champion-db",
            {"promotion": False, "approval_class": "bounded_phase", "approval_classes": ["bounded_phase"]},
            "promotion risk requires promotion flag",
        ),
        (
            "preflight",
            {"default_mode": "read_only"},
            "incompatible risk and default mode",
        ),
        (
            "mine",
            {"side_effect_class": "none"},
            "incompatible risk and side effect",
        ),
        (
            "mine",
            {"default_mode": "read_only"},
            "incompatible risk and default mode",
        ),
        (
            "dashboard",
            {"default_mode": "read_only"},
            "incompatible risk and default mode",
        ),
    ],
)
def test_validator_rejects_incoherent_policy_tuples(
    tmp_path: Path, path: str, changes: dict, message: str
) -> None:
    contract = _contract()
    route = next(route for route in contract["command_routes"] if route["command_path"] == path)
    route.update(changes)

    result = _run_validator(tmp_path, contract, _manifest_fixture())

    assert result.returncode != 0
    assert message in result.stderr.lower()


def test_validator_handles_unhashable_enum_values_without_traceback(tmp_path: Path) -> None:
    contract = _contract()
    contract["command_routes"][0]["classification"] = []

    result = _run_validator(tmp_path, contract, _manifest_fixture())

    assert result.returncode != 0
    assert "invalid classification" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()


def test_validator_handles_unhashable_manifest_values_without_traceback(tmp_path: Path) -> None:
    manifest = _manifest_fixture()
    manifest["items"][0]["kind"] = []

    result = _run_validator(tmp_path, _contract(), manifest)

    assert result.returncode != 0
    assert "invalid values" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()


def test_live_validator_handles_malformed_source_metadata(tmp_path: Path) -> None:
    pinned = _manifest_fixture()
    pinned["source"] = []
    pinned_path = tmp_path / "pinned.json"
    pinned_path.write_text(json.dumps(pinned), encoding="utf-8")
    runtime_repo = Path(
        os.environ.get("CAM_CAM_RUNTIME_REPO", ROOT.parent / "CAM_CAM")
    ).resolve()
    if not (runtime_repo / "src" / "claw" / "cli").is_dir():
        pytest.skip(f"adjacent CAM_CAM checkout unavailable: {runtime_repo}")

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--runtime-repo",
            str(runtime_repo),
            "--pinned-manifest",
            str(pinned_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "source must be an object" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()


def test_validator_rejects_alias_policy_drift(tmp_path: Path) -> None:
    contract = _contract()
    route = next(
        route for route in contract["command_routes"] if route["command_path"] == "synergies"
    )
    route["default_mode"] = "preview"

    result = _run_validator(tmp_path, contract, _manifest_fixture())

    assert result.returncode != 0
    assert "alias policy differs from canonical target" in result.stderr.lower()


def test_manifest_fixture_records_source_revision_and_digest() -> None:
    manifest = _manifest_fixture()

    assert manifest["source"]["repo"] == "CAM_CAM"
    assert len(manifest["source"]["commit"]) == 40
    assert manifest["source"]["manifest_sha256"] == _manifest_digest(manifest)


def test_adjacent_cam_runtime_conforms_to_registry_and_pinned_manifest() -> None:
    runtime_repo = Path(
        os.environ.get("CAM_CAM_RUNTIME_REPO", ROOT.parent / "CAM_CAM")
    ).resolve()
    if not (runtime_repo / "src" / "claw" / "cli").is_dir():
        pytest.skip(f"adjacent CAM_CAM checkout unavailable: {runtime_repo}")

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--runtime-repo",
            str(runtime_repo),
            "--pinned-manifest",
            str(MANIFEST_FIXTURE_PATH),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "live manifest matches pinned digest" in result.stdout.lower()
    assert "live cam_cam revision matches pinned commit" in result.stdout.lower()


def test_live_validator_rejects_pinned_revision_mismatch(tmp_path: Path) -> None:
    pinned = _manifest_fixture()
    pinned["source"]["commit"] = "0" * 40
    pinned_path = tmp_path / "pinned.json"
    pinned_path.write_text(json.dumps(pinned), encoding="utf-8")
    runtime_repo = Path(
        os.environ.get("CAM_CAM_RUNTIME_REPO", ROOT.parent / "CAM_CAM")
    ).resolve()
    if not (runtime_repo / "src" / "claw" / "cli").is_dir():
        pytest.skip(f"adjacent CAM_CAM checkout unavailable: {runtime_repo}")

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            "--runtime-repo",
            str(runtime_repo),
            "--pinned-manifest",
            str(pinned_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "differs from pinned" in result.stderr.lower()
    assert "traceback" not in result.stderr.lower()


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
