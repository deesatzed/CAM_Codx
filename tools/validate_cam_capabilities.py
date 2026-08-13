#!/usr/bin/env python3
"""Validate the CAM_Codx capability registry against a CAM_CAM manifest."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
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
    if route["kind"] not in {"command", "group"}:
        raise RegistryValidationError(f"{path}: invalid manifest kind")
    if not isinstance(route["hidden"], bool):
        raise RegistryValidationError(f"{path}: hidden must be boolean")
    if route["command_status"] not in COMMAND_STATUSES:
        raise RegistryValidationError(f"{path}: invalid command status")
    if route["classification"] not in CLASSIFICATIONS:
        raise RegistryValidationError(f"{path}: invalid classification")
    if route["cam_codx_route"] not in intents:
        raise RegistryValidationError(f"{path}: unknown CAM_Codx route")
    for field in ("risk_class", "side_effect_class", "default_mode", "approval_class"):
        if not isinstance(route[field], str) or not route[field]:
            raise RegistryValidationError(f"{path}: {field} must be a non-empty string")
    for field in ("provider_spend", "config_change", "promotion"):
        if not isinstance(route[field], bool):
            raise RegistryValidationError(f"{path}: {field} must be boolean")
    for field in ("artifacts", "runtime_source_refs"):
        if not isinstance(route[field], list) or not route[field] or not all(
            isinstance(value, str) and value for value in route[field]
        ):
            raise RegistryValidationError(f"{path}: {field} must be a non-empty string list")
    if route["hidden"] != (route["classification"] == "hidden_compatibility"):
        raise RegistryValidationError(f"{path}: hidden status and classification disagree")
    if route["hidden"] != (route["command_status"] == "alias"):
        raise RegistryValidationError(f"{path}: hidden status and command status disagree")


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

    routes_by_path = {route["command_path"]: route for route in routes}
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
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        summary = validate_registry(_load_json(args.contract), _load_json(args.manifest))
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
