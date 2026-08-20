#!/usr/bin/env python3
"""Read-only CAM_Codx control-plane planning.

This module resolves one explicit CAM_Codx intent against the shared
capability contract.  It never imports CAM_CAM and never executes a CAM
operation; later control-plane phases consume its typed plan.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import sys
import tomllib
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "agent-packs" / "contract" / "cam_agent_capabilities.json"
_ADMIN_INTENTS = frozenset(
    {"knowledge", "models", "self-enhance", "evolution", "doctor", "setup"}
)
_ROUTE_FIELDS = {
    "command_path": str,
    "kind": str,
    "hidden": bool,
    "command_status": str,
    "classification": str,
    "cam_codx_route": str,
    "default_mode": str,
    "side_effect_class": str,
    "provider_spend": bool,
    "approval_classes": list,
    "artifacts": list,
    "runtime_source_refs": list,
}


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


@dataclass(frozen=True)
class ManagedRunStartPacket:
    """Fixed persistence-only packet for an assess/plan run start."""

    argv: tuple[str, ...]
    provider_spend: bool
    mining: bool


@dataclass(frozen=True)
class AssessmentComposition:
    """Read-only Development Brief plus its bounded managed-run start packet."""

    brief: Any
    start_packet: ManagedRunStartPacket


def _attach_runtime_sufficiency(brief: Any) -> Any:
    """Attach a validated CAM runtime verdict without consulting a ledger."""

    from tools.development_brief import (
        BriefValidationError,
        DevelopmentBrief,
        derive_runtime_sufficiency,
        validate_sufficiency_payload,
    )

    try:
        if isinstance(brief, dict):
            payload = dict(brief)
            raw = payload.get("sufficiency")
            assessment = (
                derive_runtime_sufficiency(())
                if raw is None
                else validate_sufficiency_payload(raw)
            )
            payload["sufficiency"] = assessment.to_payload()
            return payload
        if isinstance(brief, DevelopmentBrief):
            assessment = (
                derive_runtime_sufficiency(brief.evidence_items)
                if brief.sufficiency is None
                else validate_sufficiency_payload(brief.sufficiency)
            )
            return replace(brief, sufficiency=assessment)
    except BriefValidationError as exc:
        raise ControlPlaneError(f"invalid CAM runtime sufficiency: {exc}") from exc
    raise ControlPlaneError("CAM Development Brief has no supported runtime sufficiency shape")


@dataclass(frozen=True)
class ManagedMiningPacket:
    """One approval-bound mining packet and its future CAM budget receipt path."""

    packet_path: Path
    budget_receipt_path: Path


def _load_registry(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlPlaneError(f"Cannot read capability registry {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "2.0":
        raise ControlPlaneError("Capability registry must use schema 2.0")
    intents = payload.get("workflow_intents")
    if not isinstance(intents, dict) or not intents:
        raise ControlPlaneError("Capability registry has no workflow intents")
    for intent, policy in intents.items():
        if (
            not isinstance(intent, str)
            or not isinstance(policy, dict)
            or not isinstance(policy.get("description"), str)
            or not isinstance(policy.get("default_command"), str)
        ):
            raise ControlPlaneError(f"Capability registry intent {intent!r} is malformed")
    routes = payload.get("command_routes")
    if not isinstance(routes, list) or not routes:
        raise ControlPlaneError("Capability registry has no command routes")
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise ControlPlaneError(f"Capability registry route {index} is not an object")
        for field, expected_type in _ROUTE_FIELDS.items():
            if not isinstance(route.get(field), expected_type):
                raise ControlPlaneError(
                    f"Capability registry route {index} has invalid {field!r}"
                )
        for field in ("approval_classes", "artifacts", "runtime_source_refs"):
            if not route[field] or not all(isinstance(item, str) and item for item in route[field]):
                raise ControlPlaneError(
                    f"Capability registry route {index} has invalid {field!r} values"
                )
    return payload


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
    registry: dict[str, Any], *, intent: str, request: str = "", operation: str | None = None
) -> RoutePlan:
    """Select one explicit route, or the contract's safe intent default."""
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
    by_path = {route["command_path"]: route for route in candidates}
    default_path = intents[intent]["default_command"]
    default = by_path.get(default_path)
    if default is None:
        raise ControlPlaneError(
            f"Intent {intent!r} has no registered safe default {default_path!r}"
        )
    return _to_route_plan(default)


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
    try:
        config_payload = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ControlPlaneError(f"CAM config identity is unreadable or invalid: {exc}") from exc
    database_config = config_payload.get("database")
    if not isinstance(database_config, dict):
        raise ControlPlaneError("CAM config identity has no unambiguous [database] table")
    configured_database = database_config.get("db_path")
    if not isinstance(configured_database, str) or not configured_database.strip():
        raise ControlPlaneError("CAM config identity has no unambiguous database.db_path")
    configured_path = Path(configured_database).expanduser()
    if not configured_path.is_absolute():
        configured_path = config.parent / configured_path
    configured_path = configured_path.resolve(strict=False)
    if configured_path != database:
        raise ControlPlaneError(
            f"CAM config/database identity mismatch: config binds {configured_path}, "
            f"but --cam-db pins {database}"
        )

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


def _hash_path_identity(path: Path) -> str:
    """Hash content plus structural metadata without following symlinks."""
    digest = hashlib.sha256()
    root = path.parent if path.is_file() or path.is_symlink() else path
    items = [path] if path.is_file() or path.is_symlink() else [path, *path.rglob("*")]
    for item in sorted(items, key=lambda value: str(value)):
        relative = "." if item == path else str(item.relative_to(root if item == path else path))
        stat = item.lstat()
        if item.is_symlink():
            kind = "symlink"
        elif item.is_dir():
            kind = "directory"
        elif item.is_file():
            kind = "file"
        else:
            kind = "other"
        digest.update(
            f"{relative}\0{kind}\0{stat.st_mode}\0{stat.st_size}\0{stat.st_mtime_ns}\0".encode(
                "utf-8"
            )
        )
        if item.is_symlink():
            digest.update(os.readlink(item).encode("utf-8"))
        elif item.is_file():
            with item.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def _hash_sqlite_identity(database: Path) -> str:
    digest = hashlib.sha256()
    for suffix in ("", "-wal", "-shm", "-journal"):
        path = Path(str(database) + suffix)
        digest.update(f"{path.name}\0{path.exists()}\0".encode("utf-8"))
        if path.exists():
            digest.update(_hash_path_identity(path).encode("ascii"))
    return digest.hexdigest()


def _identity_hashes(request: ControlPlaneRequest) -> dict[str, str]:
    hashes = {
        "target": _hash_path_identity(request.target),
        "database": _hash_sqlite_identity(request.runtime.database),
        "config": _hash_path_identity(request.runtime.config),
    }
    if request.runtime.model_profiles is not None:
        hashes["model_profiles"] = _hash_path_identity(request.runtime.model_profiles)
    return hashes


def plan_request(
    request: ControlPlaneRequest, *, registry_path: Path = DEFAULT_REGISTRY
) -> ControlPlaneResult:
    """Plan one registry-backed route without invoking CAM or writing state."""
    resolved = _resolve_request(request)
    before = _identity_hashes(resolved)
    registry = _load_registry(registry_path)
    route = select_route(
        registry,
        intent=resolved.intent,
        request=resolved.request,
        operation=resolved.operation,
    )
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


def prepare_admin_packet(
    request: ControlPlaneRequest,
    *,
    wrapper: Path,
    state_dir: Path,
    args: list[str] | None = None,
    budget_usd: float = 0.0,
    registry_path: Path = DEFAULT_REGISTRY,
) -> Path:
    """Prepare one registry-selected administrative manager packet.

    This is packet construction only: it does not execute CAM. Mining is
    intentionally excluded because its source, corpus, provider, time, cost,
    receipt, and delta boundary belongs to ``cam_pull_mine_dir``.
    """
    resolved = _resolve_request(request)
    if resolved.intent not in _ADMIN_INTENTS:
        raise ControlPlaneError(
            "Administrative packet preparation requires one of: "
            + ", ".join(sorted(_ADMIN_INTENTS))
        )
    before = _identity_hashes(resolved)
    route = select_route(
        _load_registry(registry_path),
        intent=resolved.intent,
        request=resolved.request,
        operation=resolved.operation,
    )
    from tools.cam_manager import prepare_packet

    packet_path = prepare_packet(
        operation=route.command_path,
        wrapper=wrapper,
        args=args,
        workflow_id=resolved.run_id or "cam-codx-admin",
        budget_usd=budget_usd,
        state_dir=state_dir,
    )
    if _identity_hashes(resolved) != before:
        raise ControlPlaneError("Administrative packet preparation changed a pinned identity")
    return packet_path


def prepare_mining_packet(
    request: ControlPlaneRequest,
    *,
    config: Any,
    registry_path: Path = DEFAULT_REGISTRY,
) -> ManagedMiningPacket:
    """Bind existing pull/mine bounds to one manager packet without execution."""
    resolved = _resolve_request(request)
    if resolved.intent != "mine":
        raise ControlPlaneError("Managed mining packet preparation requires mine intent")
    if config.wrapper is None:
        raise ControlPlaneError("Managed mining requires the configured secure wrapper")
    expected_paths = {
        "cam_command": resolved.runtime.command,
        "cam_db": resolved.runtime.database,
        "cam_config": resolved.runtime.config,
    }
    if resolved.runtime.model_profiles is not None:
        expected_paths["profiles"] = resolved.runtime.model_profiles
    for field, expected in expected_paths.items():
        actual = getattr(config, field)
        if actual is None or Path(actual).expanduser().resolve() != expected:
            raise ControlPlaneError(f"Mining configuration {field} does not match pinned runtime")

    before = _identity_hashes(resolved)
    registry = _load_registry(registry_path)
    route = select_route(
        registry,
        intent="mine",
        request=resolved.request,
        operation="mine-workspace",
    )
    from tools.cam_manager import prepare_packet
    from tools.cam_pull_mine_dir import _budget_receipt_path, build_live_argv, validate_config

    validate_config(config)
    budget_receipt_path = _budget_receipt_path(config)
    live_argv = build_live_argv(config, budget_receipt_path)
    packet_path = prepare_packet(
        operation=route.command_path,
        wrapper=config.wrapper,
        args=live_argv[2:],
        workflow_id=resolved.run_id or "cam-codx-mine",
        budget_usd=config.max_cost_usd,
        state_dir=config.state_dir,
    )
    if _identity_hashes(resolved) != before:
        raise ControlPlaneError("Mining packet preparation changed a pinned identity")
    return ManagedMiningPacket(
        packet_path=packet_path,
        budget_receipt_path=budget_receipt_path,
    )


def mining_receipt_link_packet(
    request: ControlPlaneRequest,
    *,
    receipt_path: Path,
    source_repositories: list[str],
    registry_path: Path = DEFAULT_REGISTRY,
) -> ManagedRunStartPacket:
    """Build, but do not submit, one receipt-verified managed-run link packet."""
    resolved = _resolve_request(request)
    if resolved.intent != "mine":
        raise ControlPlaneError("Mining receipt linkage requires mine intent")
    if resolved.run_id is None:
        raise ControlPlaneError("Mining receipt linkage requires an explicit run_id")
    receipt = _require_absolute_file(receipt_path, "Mining receipt")
    sources = [source.strip() for source in source_repositories]
    if not sources or any(not source for source in sources):
        raise ControlPlaneError("Mining receipt linkage requires source repository identities")
    try:
        receipt_bytes = receipt.read_bytes()
    except OSError as exc:
        raise ControlPlaneError(f"Mining receipt could not be read: {receipt}") from exc
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    route = select_route(
        _load_registry(registry_path),
        intent="record",
        operation="managed-run",
    )
    payload = {
        "operation": "link-mining-receipt",
        "run_id": resolved.run_id,
        "receipt": {
            "receipt_id": f"mining:{receipt_sha256[:16]}",
            "receipt_path": str(receipt),
            "receipt_sha256": receipt_sha256,
            "source_repositories": sources,
        },
    }
    return ManagedRunStartPacket(
        argv=(
            str(resolved.runtime.command),
            "managed-run",
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
            "--config",
            str(resolved.runtime.config),
        ),
        provider_spend=route.provider_spend,
        mining=False,
    )


def assessment_start_packet(
    request: ControlPlaneRequest, *, registry_path: Path = DEFAULT_REGISTRY
) -> ManagedRunStartPacket:
    """Build, but do not execute, the local managed-run start packet.

    The packet is deliberately separate from read-only route planning: callers
    must choose when to submit this bounded local-record phase.
    """
    resolved = _resolve_request(request)
    if resolved.intent not in {"assess", "plan"}:
        raise ControlPlaneError("managed assessment starts require assess or plan intent")
    if resolved.run_id is None:
        raise ControlPlaneError("managed assessment start requires an explicit run_id")
    before = _identity_hashes(resolved)
    route = select_route(
        _load_registry(registry_path),
        intent="record",
        operation="managed-run",
    )
    plan = {
        "id": f"plan:{resolved.run_id}",
        "task_text": resolved.request,
        "workspace_dir": str(resolved.target),
        "task_archetype": "cam_codx_assessment",
        "status": "reviewed",
        "summary": {"evidence_items": 0},
        "approved_slot_ids": [],
        "plan_json": {"target_revision": f"sha256:{before['target']}"},
    }
    payload = {"operation": "start", "run_id": resolved.run_id, "plan": plan}
    argv = (
        str(resolved.runtime.command),
        "managed-run",
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        "--config",
        str(resolved.runtime.config),
    )
    if _identity_hashes(resolved) != before:
        raise ControlPlaneError("Managed assessment packet changed a pinned identity")
    return ManagedRunStartPacket(
        argv=argv,
        provider_spend=route.provider_spend,
        mining=route.cam_codx_route == "mine",
    )


def submit_managed_run_packet(
    packet: ManagedRunStartPacket,
    *,
    runner: Callable[[tuple[str, ...]], tuple[int, str, str]],
) -> dict[str, Any]:
    """Submit one fixed persistence packet and require a JSON success receipt."""
    return_code, stdout, stderr = runner(packet.argv)
    if return_code != 0:
        raise ControlPlaneError(
            "managed-run packet failed: " + (stderr.strip() or stdout.strip() or str(return_code))
        )
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ControlPlaneError("managed-run packet did not return JSON") from exc
    if not isinstance(payload, dict):
        raise ControlPlaneError("managed-run packet did not return one JSON object")
    return payload


def compose_assessment(
    request: ControlPlaneRequest,
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    brief_builder: Callable[..., Any] | None = None,
) -> AssessmentComposition:
    """Compose primary-only recall and target inspection before persistence starts."""
    resolved = _resolve_request(request)
    if resolved.intent not in {"assess", "plan"}:
        raise ControlPlaneError("assessment composition requires assess or plan intent")
    if brief_builder is None:
        from tools.development_brief import BriefRequest, build_development_brief

        brief_builder = build_development_brief
    else:
        from tools.development_brief import BriefRequest
    brief = brief_builder(
        request=BriefRequest(mode="new", task_text=resolved.request),
        cam_command=resolved.runtime.command,
        cam_database=resolved.runtime.database,
        target_path=resolved.target,
    )
    brief = _attach_runtime_sufficiency(brief)
    return AssessmentComposition(
        brief=brief,
        start_packet=assessment_start_packet(resolved, registry_path=registry_path),
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
