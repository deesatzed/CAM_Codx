#!/usr/bin/env python3
"""Read-only CAM_Codx control-plane planning.

This module resolves one explicit CAM_Codx intent against the shared
capability contract.  It never imports CAM_CAM and never executes a CAM
operation; later control-plane phases consume its typed plan.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "agent-packs" / "contract" / "cam_agent_capabilities.json"


class ControlPlaneError(ValueError):
    """A fail-closed planning or runtime-identity error."""


@dataclass(frozen=True)
class RuntimePaths:
    """Pinned identities required for a future managed CAM operation."""

    command: Path
    database: Path
    config: Path
    model_profiles: Path | None = None


@dataclass(frozen=True)
class ControlPlaneRequest:
    """An explicit user request before any operation packet exists."""

    intent: str
    target: Path
    request: str
    runtime: RuntimePaths
    operation: str | None = None
    run_id: str | None = None
    mining_receipt: Path | None = None


@dataclass(frozen=True)
class RoutePlan:
    """Registry-backed route policy selected for one request."""

    command_path: str
    cam_codx_route: str
    memory_mode: str
    writes: str
    provider_spend: bool
    mining: bool
    approval_classes: tuple[str, ...]
    artifacts: tuple[str, ...]
    runtime_source_refs: tuple[str, ...]


@dataclass(frozen=True)
class ControlPlaneResult:
    """Read-only planning result; it is not execution authorization."""

    intent: str
    goal: str
    target: Path
    runtime: RuntimePaths
    route: RoutePlan
    run_id: str | None
    mining_receipt: Path | None
    planning_writes: str
    operation_executed: bool
    identity_hashes: dict[str, str]
    next_action: str


def _load_registry(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlPlaneError(f"Cannot read capability registry {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "2.0":
        raise ControlPlaneError("Capability registry must use schema 2.0")
    if not isinstance(payload.get("workflow_intents"), dict):
        raise ControlPlaneError("Capability registry has no workflow intents")
    if not isinstance(payload.get("command_routes"), list):
        raise ControlPlaneError("Capability registry has no command routes")
    return payload


def _route_rank(route: dict[str, Any]) -> tuple[int, int, int, str]:
    approvals = route.get("approval_classes", [])
    return (
        0 if approvals == ["none"] else 1,
        0 if route.get("risk_class") == "read_only" else 1,
        1 if route.get("provider_spend") else 0,
        str(route.get("command_path", "")),
    )


def _to_route_plan(route: dict[str, Any]) -> RoutePlan:
    return RoutePlan(
        command_path=route["command_path"],
        cam_codx_route=route["cam_codx_route"],
        memory_mode=route["default_mode"],
        writes=route["side_effect_class"],
        provider_spend=route["provider_spend"],
        mining=route["cam_codx_route"] == "mine",
        approval_classes=tuple(route["approval_classes"]),
        artifacts=tuple(route["artifacts"]),
        runtime_source_refs=tuple(route["runtime_source_refs"]),
    )


def select_route(
    registry: dict[str, Any], *, intent: str, operation: str | None = None
) -> RoutePlan:
    """Select one visible managed command, or validate an explicit operation."""
    intents = registry["workflow_intents"]
    if intent not in intents:
        raise ControlPlaneError(
            f"Unknown intent {intent!r}; expected one of: {', '.join(sorted(intents))}"
        )
    routes = registry["command_routes"]
    if operation is not None:
        matches = [
            route
            for route in routes
            if route.get("command_path") == operation
            and route.get("kind") == "command"
            and route.get("classification") == "managed"
            and route.get("command_status") == "canonical"
        ]
        if not matches:
            raise ControlPlaneError(f"CAM command {operation!r} is not registered as managed")
        route = matches[0]
        if route["cam_codx_route"] != intent:
            raise ControlPlaneError(
                f"CAM command {operation!r} belongs to intent {route['cam_codx_route']!r}, "
                f"not {intent!r}"
            )
        return _to_route_plan(route)

    candidates = [
        route
        for route in routes
        if route.get("cam_codx_route") == intent
        and route.get("kind") == "command"
        and route.get("classification") == "managed"
        and route.get("command_status") == "canonical"
        and not route.get("hidden")
    ]
    if not candidates:
        raise ControlPlaneError(f"Intent {intent!r} has no managed command in the registry")
    return _to_route_plan(min(candidates, key=_route_rank))


def _require_absolute_file(path: Path, label: str, *, executable: bool = False) -> Path:
    if not path.is_absolute():
        raise ControlPlaneError(f"{label} path must be absolute: {path}")
    resolved = path.resolve(strict=False)
    if not resolved.is_file():
        raise ControlPlaneError(f"{label} identity is unresolved or not a file: {resolved}")
    if executable and not os.access(resolved, os.X_OK):
        raise ControlPlaneError(f"{label} must be executable: {resolved}")
    return resolved


def _resolve_request(request: ControlPlaneRequest) -> ControlPlaneRequest:
    if not request.target.is_absolute():
        raise ControlPlaneError(f"Target path must be absolute: {request.target}")
    target = request.target.resolve(strict=False)
    if not target.exists():
        raise ControlPlaneError(f"Target identity is unresolved: {target}")
    if not request.request.strip():
        raise ControlPlaneError("Request text must not be empty")

    command = _require_absolute_file(request.runtime.command, "CAM command", executable=True)
    database = _require_absolute_file(request.runtime.database, "CAM database")
    config = _require_absolute_file(request.runtime.config, "CAM config")
    model_profiles = (
        _require_absolute_file(request.runtime.model_profiles, "CAM model profiles")
        if request.runtime.model_profiles is not None
        else None
    )
    identities = [command, database, config]
    if model_profiles is not None:
        identities.append(model_profiles)
    if len(identities) != len(set(identities)):
        raise ControlPlaneError("CAM runtime identities must resolve to distinct files")

    receipt = None
    if request.mining_receipt is not None:
        receipt = _require_absolute_file(request.mining_receipt, "Mining receipt")
    if request.run_id is not None and not request.run_id.strip():
        raise ControlPlaneError("Run ID must not be blank")
    return ControlPlaneRequest(
        intent=request.intent.strip(),
        target=target,
        request=request.request.strip(),
        runtime=RuntimePaths(
            command=command,
            database=database,
            config=config,
            model_profiles=model_profiles,
        ),
        operation=request.operation.strip() if request.operation else None,
        run_id=request.run_id.strip() if request.run_id else None,
        mining_receipt=receipt,
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_target(path: Path) -> str:
    if path.is_file():
        return _hash_file(path)
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if ".git" in item.parts or not item.is_file():
            continue
        digest.update(str(item.relative_to(path)).encode("utf-8"))
        with item.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _identity_hashes(request: ControlPlaneRequest) -> dict[str, str]:
    hashes = {
        "target": _hash_target(request.target),
        "database": _hash_file(request.runtime.database),
        "config": _hash_file(request.runtime.config),
    }
    if request.runtime.model_profiles is not None:
        hashes["model_profiles"] = _hash_file(request.runtime.model_profiles)
    return hashes


def plan_request(
    request: ControlPlaneRequest, *, registry_path: Path = DEFAULT_REGISTRY
) -> ControlPlaneResult:
    """Plan one registry-backed route without invoking CAM or writing state."""
    resolved = _resolve_request(request)
    before = _identity_hashes(resolved)
    registry = _load_registry(registry_path)
    route = select_route(registry, intent=resolved.intent, operation=resolved.operation)
    after = _identity_hashes(resolved)
    if after != before:
        raise ControlPlaneError("Planning changed a pinned target or CAM runtime identity")
    approval = ", ".join(route.approval_classes)
    return ControlPlaneResult(
        intent=resolved.intent,
        goal=resolved.request,
        target=resolved.target,
        runtime=resolved.runtime,
        route=route,
        run_id=resolved.run_id,
        mining_receipt=resolved.mining_receipt,
        planning_writes="none",
        operation_executed=False,
        identity_hashes=after,
        next_action=(
            f"Review route {route.command_path!r} and issue the required "
            f"approval ({approval}) before any execution packet is prepared."
        ),
    )


def _json_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def result_payload(result: ControlPlaneResult) -> dict[str, Any]:
    payload = _json_value(asdict(result))
    payload["provider_spend"] = "possible" if result.route.provider_spend else "none"
    payload["mining"] = "explicitly requested" if result.intent == "mine" else "not requested"
    payload["approval"] = list(result.route.approval_classes)
    return payload


def render_status_card(result: ControlPlaneResult) -> str:
    approval = ", ".join(result.route.approval_classes)
    mining = "explicitly requested" if result.intent == "mine" else "not requested"
    spend = "possible" if result.route.provider_spend else "none"
    return "\n".join(
        [
            "CAM_Codx plan (no operation executed)",
            f"Goal: {result.goal}",
            f"Route: {result.intent} -> {result.route.command_path}",
            f"Target: {result.target}",
            f"Memory mode: {result.route.memory_mode}",
            f"Writes: planning=none; operation={result.route.writes}",
            f"Provider spend: {spend}",
            f"Mining: {mining}",
            f"Approval: {approval}",
            f"Next action: {result.next_action}",
        ]
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="subcommand", required=True)
    plan = subcommands.add_parser("plan", help="resolve a read-only CAM_Codx route")
    plan.add_argument("--intent", required=True)
    plan.add_argument("--target", type=Path, required=True)
    plan.add_argument("--request", required=True)
    plan.add_argument("--cam-command", type=Path, required=True)
    plan.add_argument("--cam-db", type=Path, required=True)
    plan.add_argument("--cam-config", type=Path, required=True)
    plan.add_argument("--model-profiles", type=Path)
    plan.add_argument("--operation")
    plan.add_argument("--run-id")
    plan.add_argument("--mining-receipt", type=Path)
    plan.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    plan.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        request = ControlPlaneRequest(
            intent=args.intent,
            target=args.target,
            request=args.request,
            runtime=RuntimePaths(
                command=args.cam_command,
                database=args.cam_db,
                config=args.cam_config,
                model_profiles=args.model_profiles,
            ),
            operation=args.operation,
            run_id=args.run_id,
            mining_receipt=args.mining_receipt,
        )
        result = plan_request(request, registry_path=args.registry)
    except ControlPlaneError as exc:
        print(f"CAM_Codx plan error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result_payload(result), indent=2, sort_keys=True))
    else:
        print(render_status_card(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
