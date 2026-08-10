#!/usr/bin/env python3
"""CAM_Codx's bounded program manager and phase-approval ledger.

The manager deliberately owns orchestration policy, not CAM runtime behavior.
It prepares a content-addressed argv packet, issues a short-lived approval for
that exact packet, and executes it through the setup-generated ``cam-codx``
wrapper. No shell is involved and terminal approvals are single-use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
DEFAULT_TTL_HOURS = 4.0

# The prefix is the safety boundary. Options may be appended, but a packet can
# never replace a benchmark/self-enhance command with an arbitrary CAM command.
OPERATION_PREFIXES: dict[str, tuple[str, ...]] = {
    "inspect": ("status",),
    "models-current": ("models", "current"),
    "models-catalog": ("models", "catalog"),
    "benchmark-plan": ("models", "benchmark", "plan"),
    "benchmark-run": ("models", "benchmark", "run"),
    "benchmark-report": ("models", "benchmark", "report"),
    "benchmark-advance": ("models", "benchmark", "advance"),
    "benchmark-select": ("models", "benchmark", "select"),
    "self-enhance-status": ("self-enhance", "status"),
    "self-enhance-start": ("self-enhance", "start"),
    "self-enhance-validate": ("self-enhance", "validate"),
    "self-enhance-swap": ("self-enhance", "swap"),
    "self-enhance-rollback": ("self-enhance", "rollback"),
    "models-promote": ("models", "embeddings", "promote"),
}

OPERATION_PHASE: dict[str, str] = {
    "inspect": "inspect",
    "models-current": "inspect",
    "models-catalog": "inspect",
    "benchmark-plan": "plan",
    "benchmark-run": "run",
    "benchmark-report": "report",
    "benchmark-advance": "advance",
    "benchmark-select": "select",
    "self-enhance-status": "inspect",
    "self-enhance-start": "self-enhance",
    "self-enhance-validate": "self-enhance",
    "self-enhance-swap": "promote",
    "self-enhance-rollback": "promote",
    "models-promote": "promote",
}

READ_ONLY_OPERATIONS = {
    "inspect",
    "models-current",
    "models-catalog",
    "benchmark-report",
    "benchmark-select",
    "self-enhance-status",
    "self-enhance-validate",
}

_SECRET_MARKERS = (
    "api-key",
    "api_key",
    "token",
    "password",
    "secret",
    "private-key",
    "private_key",
)


class ManagerError(ValueError):
    """A user-correctable manager or approval error."""


def _now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def scope_digest(scope: dict[str, Any]) -> str:
    """Return the stable digest used by packets and approvals."""

    return hashlib.sha256(_canonical(scope)).hexdigest()


def _secure_dir(path: Path) -> Path:
    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def _secure_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)
    path.chmod(0o600)


def _state_paths(state_dir: Path) -> dict[str, Path]:
    root = _secure_dir(state_dir)
    paths = {
        "root": root,
        "packets": root / "packets",
        "approvals": root / "approvals",
        "executions": root / "executions",
        "events": root / "events.jsonl",
    }
    for path in paths.values():
        if path.suffix:
            continue
        _secure_dir(path)
    return paths


def _append_event(state_dir: Path, event: dict[str, Any]) -> None:
    paths = _state_paths(state_dir)
    event = {"schema_version": SCHEMA_VERSION, "recorded_at": _timestamp(_now()), **event}
    with paths["events"].open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    paths["events"].chmod(0o600)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManagerError(f"Cannot read manager record: {path}") from exc
    if not isinstance(payload, dict):
        raise ManagerError(f"Manager record must be a JSON object: {path}")
    return payload


def _reject_secret_args(args: list[str]) -> None:
    for argument in args:
        lowered = argument.lower()
        if any(marker in lowered for marker in _SECRET_MARKERS):
            raise ManagerError(
                "Secret-bearing arguments are not allowed in manager packets; "
                "configure CAM through its private environment instead"
            )


def _normalise_args(args: list[str] | None, args_json: str | None) -> list[str]:
    if args is not None and args_json is not None:
        raise ManagerError("Use either --arg or --args-json, not both")
    if args_json is not None:
        try:
            parsed = json.loads(args_json)
        except json.JSONDecodeError as exc:
            raise ManagerError("--args-json must contain a JSON array") from exc
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise ManagerError("--args-json must contain a JSON array of strings")
        result = list(parsed)
    else:
        result = list(args or [])
    _reject_secret_args(result)
    return result


def prepare_packet(
    *,
    operation: str,
    wrapper: Path,
    args: list[str] | None = None,
    workflow_id: str = "default",
    target_repo: Path | None = None,
    budget_usd: float = 0.0,
    state_dir: Path,
) -> Path:
    """Create an immutable execution packet and return its path."""

    if operation not in OPERATION_PREFIXES:
        raise ManagerError(f"Unsupported manager operation: {operation}")
    wrapper = wrapper.expanduser().resolve()
    if not wrapper.is_file() or not os.access(wrapper, os.X_OK):
        raise ManagerError(f"CAM wrapper is not executable: {wrapper}")
    if not workflow_id.strip():
        raise ManagerError("workflow_id must not be empty")
    if budget_usd < 0:
        raise ManagerError("budget_usd cannot be negative")
    if target_repo is not None:
        target_repo = target_repo.expanduser().resolve()
        if not target_repo.is_dir():
            raise ManagerError(f"Target repository is not a directory: {target_repo}")
    extra_args = _normalise_args(args, None)
    argv = [str(wrapper), *OPERATION_PREFIXES[operation], *extra_args]
    phase = OPERATION_PHASE[operation]
    scope = {
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "phase": phase,
        "workflow_id": workflow_id,
        "wrapper": str(wrapper),
        "argv": argv,
        "target_repo": str(target_repo) if target_repo else None,
        "budget_usd": round(float(budget_usd), 12),
    }
    packet_id = f"packet-{_now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:10]}"
    packet = {
        "schema_version": SCHEMA_VERSION,
        "packet_id": packet_id,
        "created_at": _timestamp(_now()),
        "status": "prepared",
        "requires_approval": operation not in READ_ONLY_OPERATIONS,
        "workflow_id": workflow_id,
        "operation": operation,
        "phase": phase,
        "wrapper": str(wrapper),
        "argv": argv,
        "target_repo": str(target_repo) if target_repo else None,
        "budget_usd": round(float(budget_usd), 12),
        "scope": scope,
        "scope_digest": scope_digest(scope),
    }
    paths = _state_paths(state_dir)
    path = paths["packets"] / f"{packet_id}.json"
    _secure_write(path, packet)
    _append_event(
        state_dir,
        {
            "event": "packet_prepared",
            "packet_id": packet_id,
            "workflow_id": workflow_id,
            "phase": phase,
            "scope_digest": packet["scope_digest"],
        },
    )
    return path


def issue_approval(
    packet_path: Path,
    *,
    state_dir: Path,
    approved_by: str = "operator",
    ttl_hours: float = DEFAULT_TTL_HOURS,
) -> Path:
    """Issue a short-lived approval for one exact packet."""

    packet = _read_json(packet_path)
    if packet.get("schema_version") != SCHEMA_VERSION:
        raise ManagerError("Unsupported packet schema")
    if ttl_hours <= 0 or ttl_hours > 24 * 7:
        raise ManagerError("Approval TTL must be greater than zero and at most 168 hours")
    if not approved_by.strip():
        raise ManagerError("approved_by must not be empty")
    approval_id = f"approval-{_now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:10]}"
    issued = _now()
    approval = {
        "schema_version": SCHEMA_VERSION,
        "approval_id": approval_id,
        "packet_id": packet.get("packet_id"),
        "workflow_id": packet.get("workflow_id"),
        "operation": packet.get("operation"),
        "phase": packet.get("phase"),
        "scope_digest": packet.get("scope_digest"),
        "budget_usd": packet.get("budget_usd", 0.0),
        "approved_by": approved_by,
        "issued_at": _timestamp(issued),
        "expires_at": _timestamp(issued + timedelta(hours=ttl_hours)),
        "status": "issued",
    }
    paths = _state_paths(state_dir)
    path = paths["approvals"] / f"{approval_id}.json"
    _secure_write(path, approval)
    _append_event(
        state_dir,
        {
            "event": "approval_issued",
            "approval_id": approval_id,
            "packet_id": approval["packet_id"],
            "scope_digest": approval["scope_digest"],
            "phase": approval["phase"],
        },
    )
    return path


def _approval_was_consumed(state_dir: Path, approval_id: str) -> bool:
    paths = _state_paths(state_dir)
    if not paths["events"].exists():
        return False
    for line in paths["events"].read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event") == "approval_consumed" and event.get("approval_id") == approval_id:
            return True
    return False


def consume_approval(
    approval_path: Path,
    packet: dict[str, Any],
    *,
    state_dir: Path,
) -> dict[str, Any]:
    """Validate and consume a single approval for *packet*."""

    approval = _read_json(approval_path)
    if approval.get("schema_version") != SCHEMA_VERSION:
        raise ManagerError("Unsupported approval schema")
    if approval.get("status") != "issued":
        raise ManagerError("Approval is not in issued state")
    if _approval_was_consumed(state_dir, str(approval.get("approval_id"))):
        raise ManagerError("Approval has already been consumed")
    if approval.get("packet_id") != packet.get("packet_id"):
        raise ManagerError("Approval packet mismatch")
    if approval.get("workflow_id") != packet.get("workflow_id"):
        raise ManagerError("Approval workflow mismatch")
    if approval.get("phase") != packet.get("phase"):
        raise ManagerError("Approval phase mismatch")
    if approval.get("scope_digest") != packet.get("scope_digest"):
        raise ManagerError("Approval scope mismatch; prepare a new packet")
    try:
        expires = datetime.fromisoformat(str(approval["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ManagerError("Approval expiry is invalid") from exc
    if expires <= _now():
        raise ManagerError("Approval has expired")
    _append_event(
        state_dir,
        {
            "event": "approval_consumed",
            "approval_id": approval["approval_id"],
            "packet_id": packet["packet_id"],
            "scope_digest": packet["scope_digest"],
            "phase": packet["phase"],
        },
    )
    return approval


def execute_packet(
    packet_path: Path,
    *,
    state_dir: Path,
    approval_path: Path | None = None,
    dry_run: bool = False,
) -> tuple[Path | None, int | None]:
    """Execute one packet through its fixed wrapper, returning receipt/code."""

    packet = _read_json(packet_path)
    if packet.get("schema_version") != SCHEMA_VERSION:
        raise ManagerError("Unsupported packet schema")
    argv = packet.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
        raise ManagerError("Packet argv is invalid")
    operation = str(packet.get("operation"))
    if operation not in OPERATION_PREFIXES:
        raise ManagerError("Packet operation is not allowlisted")
    if tuple(argv[1 : 1 + len(OPERATION_PREFIXES[operation])]) != OPERATION_PREFIXES[operation]:
        raise ManagerError("Packet command prefix is not allowlisted")
    if packet.get("requires_approval"):
        if approval_path is None:
            raise ManagerError(f"Operation {operation} requires an approval receipt")
        consume_approval(approval_path, packet, state_dir=state_dir)
    if dry_run:
        return None, None

    target_repo = packet.get("target_repo")
    cwd = Path(target_repo) if target_repo else None
    if cwd is not None and not cwd.is_dir():
        raise ManagerError(f"Packet target repository is not a directory: {cwd}")
    started = _now()
    completed = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
    )
    finished = _now()
    execution_id = f"execution-{finished.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:10]}"
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "execution_id": execution_id,
        "packet_id": packet["packet_id"],
        "workflow_id": packet["workflow_id"],
        "operation": operation,
        "phase": packet["phase"],
        "scope_digest": packet["scope_digest"],
        "started_at": _timestamp(started),
        "finished_at": _timestamp(finished),
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "stdout_bytes": len(completed.stdout.encode()),
        "stderr_bytes": len(completed.stderr.encode()),
    }
    paths = _state_paths(state_dir)
    receipt_path = paths["executions"] / f"{execution_id}.json"
    _secure_write(receipt_path, receipt)
    _append_event(
        state_dir,
        {
            "event": "packet_executed",
            "execution_id": execution_id,
            "packet_id": packet["packet_id"],
            "scope_digest": packet["scope_digest"],
            "returncode": completed.returncode,
        },
    )
    # The command output is intentionally returned to the CLI, never persisted.
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return receipt_path, completed.returncode


def manager_status(state_dir: Path) -> dict[str, Any]:
    paths = _state_paths(state_dir)
    packets = sorted(paths["packets"].glob("*.json"))
    approvals = sorted(paths["approvals"].glob("*.json"))
    executions = sorted(paths["executions"].glob("*.json"))
    return {
        "state_dir": str(paths["root"]),
        "packets": len(packets),
        "approvals": len(approvals),
        "executions": len(executions),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="prepare a fixed CAM operation packet")
    prepare.add_argument("operation", choices=sorted(OPERATION_PREFIXES))
    prepare.add_argument("--wrapper", type=Path, required=True)
    prepare.add_argument("--arg", action="append", dest="args")
    prepare.add_argument("--args-json")
    prepare.add_argument("--workflow-id", default="default")
    prepare.add_argument("--target-repo", type=Path)
    prepare.add_argument("--budget-usd", type=float, default=0.0)
    prepare.add_argument("--state-dir", type=Path, required=True)
    prepare.add_argument("--output", type=Path)

    approve = sub.add_parser("approve", help="issue a one-use approval receipt")
    approve.add_argument("packet", type=Path)
    approve.add_argument("--state-dir", type=Path, required=True)
    approve.add_argument("--approved-by", default="operator")
    approve.add_argument("--ttl-hours", type=float, default=DEFAULT_TTL_HOURS)

    execute = sub.add_parser("execute", help="execute a packet through its wrapper")
    execute.add_argument("packet", type=Path)
    execute.add_argument("--approval", type=Path)
    execute.add_argument("--state-dir", type=Path, required=True)
    execute.add_argument("--dry-run", action="store_true")

    status = sub.add_parser("status", help="show manager state counts")
    status.add_argument("--state-dir", type=Path, required=True)
    status.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            packet = prepare_packet(
                operation=args.operation,
                wrapper=args.wrapper,
                args=_normalise_args(args.args, args.args_json),
                workflow_id=args.workflow_id,
                target_repo=args.target_repo,
                budget_usd=args.budget_usd,
                state_dir=args.state_dir,
            )
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(packet.read_text(encoding="utf-8"), encoding="utf-8")
                args.output.chmod(0o600)
            print(packet)
            return 0
        if args.command == "approve":
            print(
                issue_approval(
                    args.packet,
                    state_dir=args.state_dir,
                    approved_by=args.approved_by,
                    ttl_hours=args.ttl_hours,
                )
            )
            return 0
        if args.command == "execute":
            receipt, returncode = execute_packet(
                args.packet,
                state_dir=args.state_dir,
                approval_path=args.approval,
                dry_run=args.dry_run,
            )
            if receipt:
                print(f"Execution receipt: {receipt}")
            return 0 if returncode in (None, 0) else int(returncode)
        payload = manager_status(args.state_dir)
        if args.as_json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"CAM_Codx manager: {payload['state_dir']}")
            print(
                f"Packets: {payload['packets']} | Approvals: {payload['approvals']} | "
                f"Executions: {payload['executions']}"
            )
        return 0
    except ManagerError as exc:
        print(f"CAM_Codx manager error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

