#!/usr/bin/env python3
"""Validate the CAM_Codx capability registry against a CAM_CAM manifest."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "agent-packs" / "contract" / "cam_agent_capabilities.json"
CLASSIFICATIONS = {
    "managed",
    "troubleshooting_only",
    "hidden_compatibility",
}
COMMAND_STATUSES = {"canonical", "alias"}
RISK_CLASSES = {
    "cam_live_mutation",
    "corpus_write",
    "external_network_mutation",
    "external_network_read",
    "external_provider_call",
    "local_record_write",
    "promotion_configuration",
    "read_only",
    "target_code_mutation",
}
SIDE_EFFECT_CLASSES = {
    "configuration_or_selection_write",
    "configuration_write",
    "corpus_or_ledger_write",
    "external_network_read",
    "external_or_filesystem_write",
    "external_provider_call",
    "live_runtime_and_configuration_write",
    "local_state_write",
    "none",
    "read_only_subprocess",
    "target_repository_write",
    "validation_command_execution",
}
DEFAULT_MODES = {
    "execute",
    "interactive_preview",
    "plan_only",
    "preview",
    "read_only",
    "read_only_if_initialized",
    "route_selection",
    "service",
}
APPROVAL_CLASSES = {
    "bounded_phase",
    "configuration_change",
    "external_network",
    "live_cam_mutation",
    "none",
    "promotion",
    "provider_spend",
    "target_mutation",
}
RISK_SIDE_EFFECTS = {
    "cam_live_mutation": {"live_runtime_and_configuration_write"},
    "corpus_write": {"corpus_or_ledger_write"},
    "external_network_mutation": {"external_or_filesystem_write"},
    "external_network_read": {"external_network_read", "external_or_filesystem_write"},
    "external_provider_call": {"external_provider_call"},
    "local_record_write": {"external_or_filesystem_write", "local_state_write"},
    "promotion_configuration": {"configuration_or_selection_write", "configuration_write"},
    "read_only": {"none", "read_only_subprocess"},
    "target_code_mutation": {"target_repository_write", "validation_command_execution"},
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
ALIAS_POLICY_FIELDS = (
    "risk_class",
    "side_effect_class",
    "default_mode",
    "approval_class",
    "approval_classes",
    "provider_spend",
    "config_change",
    "promotion",
)


class RegistryValidationError(ValueError):
    """Raised when registry coverage or policy data is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryValidationError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RegistryValidationError(f"expected JSON object in {path}")
    return payload


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _is_enum(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _manifest_core(manifest: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": manifest.get("schema_version"), "items": manifest.get("items")}


def _manifest_digest(manifest: dict[str, Any]) -> str:
    normalized = json.dumps(
        _manifest_core(manifest), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def load_runtime_manifest(runtime_repo: Path) -> dict[str, Any]:
    """Generate the live manifest from one explicit CAM_CAM checkout."""
    runtime_repo = runtime_repo.resolve()
    source_root = runtime_repo / "src"
    if not (source_root / "claw" / "cli").is_dir():
        raise RegistryValidationError(f"not a CAM_CAM source checkout: {runtime_repo}")
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(source_root)
        if not existing_pythonpath
        else os.pathsep.join((str(source_root), existing_pythonpath))
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "claw.cli", "doctor", "capabilities", "--json"],
            cwd=runtime_repo,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RegistryValidationError(f"cannot generate live CAM_CAM manifest: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RegistryValidationError(
            f"live CAM_CAM manifest command failed ({completed.returncode}): {detail}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RegistryValidationError(f"live CAM_CAM manifest is not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RegistryValidationError("live CAM_CAM manifest must be a JSON object")
    return payload


def _validate_route_shape(route: Any, index: int, intents: set[str]) -> None:
    label = f"command_routes[{index}]"
    if not isinstance(route, dict):
        raise RegistryValidationError(f"{label} must be an object")
    missing = sorted(ROUTE_KEYS - set(route))
    if missing:
        raise RegistryValidationError(f"{label} missing fields: {', '.join(missing)}")
    path = route["command_path"]
    if not isinstance(path, str) or not path.strip() or path != " ".join(path.split()):
        raise RegistryValidationError(f"{label}.command_path must be a normalized string")
    if not _is_enum(route["kind"], {"command", "group"}):
        raise RegistryValidationError(f"{path}: invalid manifest kind")
    if not isinstance(route["hidden"], bool):
        raise RegistryValidationError(f"{path}: hidden must be boolean")
    if not _is_enum(route["command_status"], COMMAND_STATUSES):
        raise RegistryValidationError(f"{path}: invalid command status")
    if not _is_enum(route["classification"], CLASSIFICATIONS):
        raise RegistryValidationError(f"{path}: invalid classification")
    if not _is_enum(route["cam_codx_route"], intents):
        raise RegistryValidationError(f"{path}: unknown CAM_Codx route")
    enumerated_fields = {
        "risk_class": RISK_CLASSES,
        "side_effect_class": SIDE_EFFECT_CLASSES,
        "default_mode": DEFAULT_MODES,
        "approval_class": APPROVAL_CLASSES,
    }
    for field, allowed in enumerated_fields.items():
        if not _is_enum(route[field], allowed):
            raise RegistryValidationError(f"{path}: invalid {field}")
    approval_classes = route["approval_classes"]
    if (
        not isinstance(approval_classes, list)
        or not approval_classes
        or not all(_is_enum(value, APPROVAL_CLASSES) for value in approval_classes)
        or len(approval_classes) != len(set(approval_classes))
    ):
        raise RegistryValidationError(f"{path}: approval_classes must be unique known values")
    if route["approval_class"] not in approval_classes:
        raise RegistryValidationError(f"{path}: primary approval missing from approval_classes")
    if ("none" in approval_classes) != (approval_classes == ["none"]):
        raise RegistryValidationError(f"{path}: none cannot be combined with other approvals")
    for field in ("provider_spend", "config_change", "promotion"):
        if not isinstance(route[field], bool):
            raise RegistryValidationError(f"{path}: {field} must be boolean")
    for field in ("artifacts", "runtime_source_refs"):
        if not isinstance(route[field], list) or not route[field] or not all(
            isinstance(value, str) and value for value in route[field]
        ):
            raise RegistryValidationError(f"{path}: {field} must be a non-empty string list")
    if route["command_status"] == "alias":
        alias_target = route.get("alias_target")
        if not route["hidden"] or route["classification"] != "hidden_compatibility":
            raise RegistryValidationError(f"{path}: aliases must be hidden compatibility paths")
        if not isinstance(alias_target, str) or not alias_target or alias_target == path:
            raise RegistryValidationError(f"{path}: alias must name a distinct canonical target")
    elif route["classification"] == "hidden_compatibility":
        raise RegistryValidationError(f"{path}: hidden compatibility path must be an alias")

    side_effect = route["side_effect_class"]
    risk = route["risk_class"]
    if side_effect not in RISK_SIDE_EFFECTS[risk]:
        raise RegistryValidationError(f"{path}: incompatible risk and side effect")
    if route["provider_spend"] and "provider_spend" not in approval_classes:
        raise RegistryValidationError(f"{path}: provider spend lacks provider approval")
    if "provider_spend" in approval_classes and not route["provider_spend"]:
        raise RegistryValidationError(f"{path}: provider approval requires provider spend flag")
    if risk == "external_provider_call" and not route["provider_spend"]:
        raise RegistryValidationError(f"{path}: external provider risk requires provider spend")
    if route["config_change"] and "configuration_change" not in approval_classes:
        raise RegistryValidationError(f"{path}: config change lacks configuration approval")
    if side_effect == "configuration_write" and not route["config_change"]:
        raise RegistryValidationError(f"{path}: configuration write requires config change")
    if "configuration_change" in approval_classes and not route["config_change"]:
        raise RegistryValidationError(f"{path}: configuration approval requires config change flag")
    if route["promotion"] and "promotion" not in approval_classes:
        raise RegistryValidationError(f"{path}: promotion lacks promotion approval")
    if side_effect == "configuration_or_selection_write" and not route["promotion"]:
        raise RegistryValidationError(f"{path}: promotion risk requires promotion flag")
    if "promotion" in approval_classes and not route["promotion"]:
        raise RegistryValidationError(f"{path}: promotion approval requires promotion flag")
    if risk in {"local_record_write", "corpus_write"} and "bounded_phase" not in approval_classes:
        raise RegistryValidationError(f"{path}: local write requires bounded phase approval")
    if side_effect == "external_or_filesystem_write" and "bounded_phase" not in approval_classes:
        raise RegistryValidationError(f"{path}: filesystem write requires bounded phase approval")
    if (
        risk in {"external_network_read", "external_network_mutation"}
        or side_effect in {"external_network_read", "external_or_filesystem_write"}
    ) and "external_network" not in approval_classes:
        raise RegistryValidationError(f"{path}: external access requires external network approval")
    if risk == "target_code_mutation" and "target_mutation" not in approval_classes:
        raise RegistryValidationError(f"{path}: target mutation lacks target approval")
    if side_effect in {"target_repository_write", "validation_command_execution"} and route[
        "default_mode"
    ] in {"read_only", "read_only_if_initialized", "route_selection"}:
        raise RegistryValidationError(f"{path}: target write cannot default to read only")
    if risk == "cam_live_mutation" and "live_cam_mutation" not in approval_classes:
        raise RegistryValidationError(f"{path}: live CAM mutation lacks live approval")
    if risk == "read_only" and approval_classes != ["none"]:
        raise RegistryValidationError(f"{path}: read-only route cannot require mutation approval")


def validate_registry(contract: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Return path/class counts after strict contract-to-manifest validation."""
    if contract.get("schema_version") != "2.0":
        raise RegistryValidationError("contract schema_version must be 2.0")
    intents_payload = contract.get("workflow_intents")
    if not isinstance(intents_payload, dict) or not intents_payload:
        raise RegistryValidationError("workflow_intents must be a non-empty object")
    intents = set(intents_payload)
    routes = contract.get("command_routes")
    if not isinstance(routes, list) or not routes:
        raise RegistryValidationError("command_routes must be a non-empty list")

    # Diagnose ownership ambiguity before detailed policy validation so an
    # accidental second classification cannot be obscured by a downstream
    # field-consistency error on the duplicate row.
    classifications_by_path: dict[str, set[str]] = defaultdict(set)
    route_paths: list[str] = []
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise RegistryValidationError(f"command_routes[{index}] must be an object")
        path = route.get("command_path")
        classification = route.get("classification")
        if isinstance(path, str):
            route_paths.append(path)
            if isinstance(classification, str):
                classifications_by_path[path].add(classification)
    multiply_classified = sorted(
        path for path, values in classifications_by_path.items() if len(values) > 1
    )
    if multiply_classified:
        raise RegistryValidationError(
            "multiply classified command paths: " + ", ".join(multiply_classified)
        )
    route_duplicates = _duplicates(route_paths)
    if route_duplicates:
        raise RegistryValidationError(
            "duplicate command paths: " + ", ".join(route_duplicates)
        )
    for index, route in enumerate(routes):
        _validate_route_shape(route, index, intents)
    routes_by_path = {route["command_path"]: route for route in routes}
    for route in routes:
        if route["command_status"] != "alias":
            continue
        target = routes_by_path.get(route["alias_target"])
        if target is None or target["command_status"] != "canonical":
            raise RegistryValidationError(
                f"{route['command_path']}: alias target must be a registered canonical path"
            )
        divergent = [
            field for field in ALIAS_POLICY_FIELDS if route[field] != target[field]
        ]
        if divergent:
            raise RegistryValidationError(
                f"{route['command_path']}: alias policy differs from canonical target "
                + ", ".join(divergent)
            )

    manifest_items = manifest.get("items")
    if manifest.get("schema_version") != 1 or not isinstance(manifest_items, list):
        raise RegistryValidationError("manifest must use schema_version 1 with an items list")
    manifest_paths: list[str] = []
    manifest_by_path: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(manifest_items):
        if not isinstance(item, dict) or set(item) != {"path", "kind", "hidden"}:
            raise RegistryValidationError(f"manifest items[{index}] has invalid shape")
        if item["kind"] not in {"command", "group"} or not isinstance(item["hidden"], bool):
            raise RegistryValidationError(f"manifest item {item.get('path', index)} has invalid values")
        path = item["path"]
        if not isinstance(path, str) or not path:
            raise RegistryValidationError(f"manifest items[{index}].path must be non-empty")
        manifest_paths.append(path)
        manifest_by_path[path] = item
    manifest_duplicates = _duplicates(manifest_paths)
    if manifest_duplicates:
        raise RegistryValidationError(
            "duplicate manifest paths: " + ", ".join(manifest_duplicates)
        )

    missing = sorted(set(manifest_paths) - set(route_paths))
    if missing:
        raise RegistryValidationError("missing command paths: " + ", ".join(missing))
    extra = sorted(set(route_paths) - set(manifest_paths))
    if extra:
        raise RegistryValidationError("unknown command paths: " + ", ".join(extra))

    mismatches = []
    for path in sorted(manifest_by_path):
        item = manifest_by_path[path]
        route = routes_by_path[path]
        if item["kind"] != route["kind"] or item["hidden"] != route["hidden"]:
            mismatches.append(path)
    if mismatches:
        raise RegistryValidationError(
            "manifest kind/hidden mismatches: " + ", ".join(mismatches)
        )

    class_counts = Counter(route["classification"] for route in routes)
    return {
        "path_count": len(route_paths),
        "class_counts": {
            classification: class_counts[classification]
            for classification in sorted(CLASSIFICATIONS)
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path)
    source.add_argument("--runtime-repo", type=Path)
    parser.add_argument(
        "--pinned-manifest",
        type=Path,
        help="With --runtime-repo, require the live manifest to match this pinned digest",
    )
    args = parser.parse_args(argv)

    try:
        manifest = (
            load_runtime_manifest(args.runtime_repo)
            if args.runtime_repo is not None
            else _load_json(args.manifest)
        )
        if args.pinned_manifest is not None:
            if args.runtime_repo is None:
                raise RegistryValidationError("--pinned-manifest requires --runtime-repo")
            pinned = _load_json(args.pinned_manifest)
            expected = pinned.get("source", {}).get("manifest_sha256")
            if not isinstance(expected, str) or len(expected) != 64:
                raise RegistryValidationError("pinned manifest lacks a valid source digest")
            if _manifest_digest(pinned) != expected:
                raise RegistryValidationError("pinned manifest content does not match its source digest")
            if _manifest_digest(manifest) != expected:
                raise RegistryValidationError("live manifest differs from pinned digest")
            print(f"Live manifest matches pinned digest: {expected}")
        summary = validate_registry(_load_json(args.contract), manifest)
    except RegistryValidationError as exc:
        print(f"Capability registry invalid: {exc}", file=sys.stderr)
        return 1
    print(
        "Capability registry valid: "
        f"{summary['path_count']} paths; "
        + ", ".join(
            f"{name}={count}" for name, count in summary["class_counts"].items()
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
