#!/usr/bin/env python3
"""Create a deterministic, no-spend Monid capability plan.

This module may discover and inspect endpoints. It intentionally cannot run one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "templates" / "skills" / "monid-showcase-contract.json"
SECRET_PATTERN = re.compile(r"(?:monid_(?:live|test)_|api[_-]?key|bearer\s+)", re.IGNORECASE)


class MonidShowcaseError(RuntimeError):
    """Raised when a safe capability plan cannot be constructed."""


class SubjectRejected(MonidShowcaseError):
    """Raised before invocation when a subject may contain private material."""


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], dict[str, str]], CommandResult]


def _default_runner(args: list[str], env: dict[str, str]) -> CommandResult:
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


class MonidShowcasePlanner:
    """Select inspected endpoints without executing paid provider calls."""

    def __init__(
        self,
        *,
        runner: Runner = _default_runner,
        contract_path: Path = DEFAULT_CONTRACT,
    ) -> None:
        self.runner = runner
        self.contract_path = contract_path

    def plan(
        self,
        *,
        skill: str,
        subject: str,
        max_cost_usd: str,
        candidate_limit: int = 5,
        existing_tools: Sequence[str] = (),
        output: Path,
    ) -> dict[str, Any]:
        self._validate_subject(subject)
        ceiling = self._parse_ceiling(max_cost_usd)
        if candidate_limit < 1 or candidate_limit > 10:
            raise MonidShowcaseError("candidate_limit must be between 1 and 10")

        contract = self._skill_contract(skill)
        payload: dict[str, Any] = {
            "schema_version": 1,
            "skill": skill,
            "subject": subject,
            "status": "planned",
            "existing_tools": list(existing_tools),
            "max_cost_usd": _money(ceiling),
            "projected_cost_usd": "0.00",
            "paid_endpoint_executed": False,
            "queries": [],
            "selected": [],
            "rejected": [],
        }
        if existing_tools:
            payload["status"] = "dedicated_tool_preferred"
            self._write(output, payload)
            return payload

        env = dict(os.environ)
        env["NO_COLOR"] = "1"
        inspected: set[tuple[str, str]] = set()
        projected = Decimal("0")

        for discovery_query in contract["discover_queries"]:
            query = f"{discovery_query} {subject}"
            payload["queries"].append(query)
            discover_args = [
                "monid",
                "discover",
                "-q",
                query,
                "-l",
                str(candidate_limit),
                "-j",
            ]
            discovered = self._invoke_json(discover_args, env)
            for candidate in discovered.get("results", [])[:candidate_limit]:
                provider = str(candidate.get("provider", ""))
                endpoint = str(candidate.get("endpoint", ""))
                identity = (provider, endpoint)
                if not all(identity) or identity in inspected:
                    continue
                inspected.add(identity)

                health = candidate.get("metrics", {}).get("status", "unknown")
                if health == "outage":
                    payload["rejected"].append(
                        {"provider": provider, "endpoint": endpoint, "reason": "outage"}
                    )
                    continue

                details = self._invoke_json(
                    ["monid", "inspect", "-p", provider, "-e", endpoint, "-j"], env
                )
                price = details.get("price", {})
                amount = price.get("amount") or {}
                try:
                    cost = Decimal(str(amount.get("value")))
                except (InvalidOperation, TypeError):
                    payload["rejected"].append(
                        {"provider": provider, "endpoint": endpoint, "reason": "unknown_price"}
                    )
                    continue
                if price.get("type") != "PER_CALL" or amount.get("currency") != "USD":
                    payload["rejected"].append(
                        {"provider": provider, "endpoint": endpoint, "reason": "unsupported_price"}
                    )
                    continue
                if projected + cost > ceiling:
                    payload["rejected"].append(
                        {
                            "provider": provider,
                            "endpoint": endpoint,
                            "reason": "cost_exceeds_ceiling",
                            "price_usd": _money(cost),
                        }
                    )
                    continue

                payload["selected"].append(
                    {
                        "provider": provider,
                        "endpoint": endpoint,
                        "description": details.get("description", ""),
                        "health": details.get("metrics", {}).get("status", health),
                        "price": {
                            "type": "PER_CALL",
                            "value": _money(cost),
                            "currency": "USD",
                        },
                        "input": details.get("input", {}),
                    }
                )
                projected += cost

        payload["projected_cost_usd"] = _money(projected)
        if not payload["selected"]:
            payload["status"] = "no_suitable_endpoint"
        self._write(output, payload)
        return payload

    def _skill_contract(self, skill: str) -> dict[str, Any]:
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        for entry in contract.get("skills", []):
            if entry.get("name") == skill:
                return entry
        raise MonidShowcaseError(f"unknown showcase skill: {skill}")

    @staticmethod
    def _parse_ceiling(raw: str) -> Decimal:
        try:
            ceiling = Decimal(raw)
        except InvalidOperation as exc:
            raise MonidShowcaseError("max_cost_usd must be a decimal value") from exc
        if not ceiling.is_finite() or ceiling < 0:
            raise MonidShowcaseError("max_cost_usd must be finite and non-negative")
        return ceiling

    @staticmethod
    def _validate_subject(subject: str) -> None:
        if not subject.strip() or len(subject) > 200:
            raise SubjectRejected("subject must be 1-200 visible characters")
        if subject.startswith(("/", "~")) or "\n" in subject or "\r" in subject:
            raise SubjectRejected("subject must not contain a local path or newline")
        if SECRET_PATTERN.search(subject):
            raise SubjectRejected("subject appears to contain a credential")

    def _invoke_json(self, args: list[str], env: dict[str, str]) -> dict[str, Any]:
        result = self.runner(args, env)
        if result.returncode != 0:
            raise MonidShowcaseError(
                f"Monid command failed with exit code {result.returncode}; stderr suppressed"
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise MonidShowcaseError("Monid returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise MonidShowcaseError("Monid returned a non-object JSON payload")
        return payload

    @staticmethod
    def _write(output: Path, payload: dict[str, Any]) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(f".{output.name}.tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary.replace(output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--max-cost-usd", required=True)
    parser.add_argument("--candidate-limit", type=int, default=5)
    parser.add_argument("--existing-tool", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    MonidShowcasePlanner().plan(
        skill=args.skill,
        subject=args.subject,
        max_cost_usd=args.max_cost_usd,
        candidate_limit=args.candidate_limit,
        existing_tools=args.existing_tool,
        output=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
