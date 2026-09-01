"""Policy-gated, local-first external evidence acquisition for CAM_Codx."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Protocol


class EvidencePolicyError(ValueError):
    """An evidence request violates its declared task policy."""


class MonidExecutionError(RuntimeError):
    """The local MONID CLI could not return a valid structured result."""


def _nonempty_strings(values: frozenset[str], field: str) -> None:
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise EvidencePolicyError(f"{field} must contain non-empty strings")


@dataclass(frozen=True)
class EvidencePolicy:
    """The policy and spend limit that authorizes one task's evidence calls."""

    task_budget_usd: float
    freshness_seconds: float
    allowed_source_categories: frozenset[str]
    retention_class: str
    prohibited_data_classes: frozenset[str]

    def __post_init__(self) -> None:
        if not math.isfinite(self.task_budget_usd) or self.task_budget_usd < 0:
            raise EvidencePolicyError("task_budget_usd must be finite and non-negative")
        if not math.isfinite(self.freshness_seconds) or self.freshness_seconds <= 0:
            raise EvidencePolicyError("freshness_seconds must be finite and positive")
        _nonempty_strings(self.allowed_source_categories, "allowed_source_categories")
        if not isinstance(self.retention_class, str) or not self.retention_class.strip():
            raise EvidencePolicyError("retention_class must be a non-empty string")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in self.prohibited_data_classes
        ):
            raise EvidencePolicyError("prohibited_data_classes must contain non-empty strings")


@dataclass(frozen=True)
class EvidenceRequest:
    """A narrow, decision-linked request for public external evidence."""

    task_id: str
    question: str
    requested_data_classes: frozenset[str]
    policy: EvidencePolicy
    input_body: Mapping[str, Any] = field(default_factory=dict)
    input_query: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise EvidencePolicyError("task_id must be a non-empty string")
        if not isinstance(self.question, str) or not self.question.strip():
            raise EvidencePolicyError("question must be a non-empty string")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in self.requested_data_classes
        ):
            raise EvidencePolicyError("requested_data_classes must contain non-empty strings")
        prohibited = self.requested_data_classes & self.policy.prohibited_data_classes
        if prohibited:
            raise EvidencePolicyError("requested data class is prohibited by task policy")
        if not isinstance(self.input_body, Mapping):
            raise EvidencePolicyError("input_body must be a mapping")
        if not isinstance(self.input_query, Mapping):
            raise EvidencePolicyError("input_query must be a mapping")


@dataclass(frozen=True)
class EvidencePacket:
    """A redacted task-facing disposition for cached or newly acquired evidence."""

    cache_status: str
    disposition: str
    raw_sha256: str | None
    cost_usd: float
    source_category: str | None
    collected_at: float | None

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def _request_key(request: EvidenceRequest) -> str:
    payload = {
        "question": request.question,
        "requested_data_classes": sorted(request.requested_data_classes),
        "input_body": request.input_body,
        "input_query": request.input_query,
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


class MonidRunner(Protocol):
    """The narrow, shell-free execution boundary for the MONID CLI."""

    def run(self, argv: list[str]) -> dict[str, Any]: ...


class SubprocessMonidRunner:
    """Production list-form MONID runner; it never invokes a shell."""

    def run(self, argv: list[str]) -> dict[str, Any]:
        if not argv or argv[0] != "monid":
            raise MonidExecutionError("MONID runner accepts only monid argv")
        try:
            completed = subprocess.run(
                argv,
                check=False,
                shell=False,
                text=True,
                capture_output=True,
            )
        except OSError as exc:
            raise MonidExecutionError(f"MONID command could not start: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or str(completed.returncode)
            raise MonidExecutionError(f"MONID command failed: {detail}")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise MonidExecutionError("MONID command did not return JSON object") from exc
        if not isinstance(payload, dict):
            raise MonidExecutionError("MONID command did not return JSON object")
        return payload


class EvidenceBroker:
    """Local content-addressed cache for policy-compatible evidence reuse."""

    def __init__(
        self,
        state_dir: Path,
        *,
        runner: MonidRunner | None = None,
        now: Callable[[], float] | None = None,
    ) -> None:
        self._state_dir = state_dir.expanduser().resolve()
        self._runner = runner
        self._now = now or __import__("time").time

    def _entry_path(self, request: EvidenceRequest) -> Path:
        return self._state_dir / "entries" / f"{_request_key(request)}.json"

    def store_completed_result(
        self,
        request: EvidenceRequest,
        *,
        raw_result: Any,
        source_category: str,
        cost_usd: float,
    ) -> EvidencePacket:
        if source_category not in request.policy.allowed_source_categories:
            raise EvidencePolicyError("source category is not allowed by task policy")
        if not math.isfinite(cost_usd) or cost_usd < 0:
            raise EvidencePolicyError("cost_usd must be finite and non-negative")
        if cost_usd > request.policy.task_budget_usd:
            raise EvidencePolicyError("cost_usd exceeds task_budget_usd")

        raw = _canonical_json(raw_result)
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        raw_dir = self._state_dir / "raw"
        entry_path = self._entry_path(request)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._state_dir.chmod(0o700)
        raw_dir.mkdir(parents=True, exist_ok=True)
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        raw_dir.chmod(0o700)
        entry_path.parent.chmod(0o700)
        raw_path = raw_dir / f"{raw_sha256}.json"
        raw_path.write_bytes(raw)
        raw_path.chmod(0o600)
        entry = {
            "request_key": _request_key(request),
            "source_category": source_category,
            "retention_class": request.policy.retention_class,
            "allowed_source_categories": sorted(request.policy.allowed_source_categories),
            "raw_sha256": raw_sha256,
            "cost_usd": cost_usd,
            "collected_at": self._now(),
            "quarantined": False,
        }
        entry_path.write_bytes(_canonical_json(entry))
        entry_path.chmod(0o600)
        return EvidencePacket(
            cache_status="stored",
            disposition="available",
            raw_sha256=raw_sha256,
            cost_usd=cost_usd,
            source_category=source_category,
            collected_at=entry["collected_at"],
        )

    def resolve_cached(self, request: EvidenceRequest) -> EvidencePacket:
        entry_path = self._entry_path(request)
        try:
            entry = json.loads(entry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return EvidencePacket("miss", "unresolved", None, 0.0, None, None)
        collected_at = entry.get("collected_at")
        if (
            not isinstance(entry, dict)
            or entry.get("quarantined") is not False
            or entry.get("source_category") not in request.policy.allowed_source_categories
            or entry.get("retention_class") != request.policy.retention_class
            or not isinstance(collected_at, (int, float))
            or self._now() - collected_at > request.policy.freshness_seconds
        ):
            return EvidencePacket("miss", "unresolved", None, 0.0, None, None)
        raw_sha256 = entry.get("raw_sha256")
        if not isinstance(raw_sha256, str) or not (self._state_dir / "raw" / f"{raw_sha256}.json").is_file():
            return EvidencePacket("miss", "unresolved", None, 0.0, None, None)
        return EvidencePacket(
            cache_status="hit",
            disposition="reused",
            raw_sha256=raw_sha256,
            cost_usd=0.0,
            source_category=entry["source_category"],
            collected_at=float(collected_at),
        )

    def resolve(self, request: EvidenceRequest) -> EvidencePacket:
        """Reuse a valid result or perform discover-inspect-run in that order."""

        cached = self.resolve_cached(request)
        if cached.cache_status == "hit":
            return cached
        if self._runner is None:
            return EvidencePacket("miss", "unresolved", None, 0.0, None, None)

        discovered = self._runner.run(["monid", "discover", "-j", "-q", request.question])
        candidate = self._select_candidate(discovered, request)
        if candidate is None:
            return EvidencePacket("miss", "unresolved", None, 0.0, None, None)
        estimated_cost = candidate.get("estimated_cost_usd")
        if (
            not isinstance(estimated_cost, (int, float))
            or not math.isfinite(estimated_cost)
            or estimated_cost < 0
            or estimated_cost > request.policy.task_budget_usd
        ):
            return EvidencePacket("miss", "blocked_budget", None, 0.0, None, None)

        provider = candidate["provider"]
        endpoint = candidate["endpoint"]
        inspected = self._runner.run(
            ["monid", "inspect", "-j", "-p", provider, "-e", endpoint]
        )
        if not self._inputs_are_supported(inspected, request):
            return EvidencePacket("miss", "schema_mismatch", None, 0.0, None, None)
        argv = ["monid", "run", "-j", "-p", provider, "-e", endpoint]
        if request.input_body:
            argv.extend(["-i", _canonical_json(dict(request.input_body)).decode("utf-8")])
        if request.input_query:
            argv.extend(["--query", _canonical_json(dict(request.input_query)).decode("utf-8")])
        result = self._runner.run(argv)
        stored = self.store_completed_result(
            request,
            raw_result=result,
            source_category=candidate["source_category"],
            cost_usd=float(estimated_cost),
        )
        return EvidencePacket(
            cache_status="miss",
            disposition=stored.disposition,
            raw_sha256=stored.raw_sha256,
            cost_usd=stored.cost_usd,
            source_category=stored.source_category,
            collected_at=stored.collected_at,
        )

    @staticmethod
    def _select_candidate(
        discovered: dict[str, Any], request: EvidenceRequest
    ) -> dict[str, Any] | None:
        results = discovered.get("results")
        if not isinstance(results, list):
            return None
        valid = []
        for item in results:
            normalized = EvidenceBroker._normalize_candidate(item)
            if (
                normalized is not None
                and normalized["source_category"] in request.policy.allowed_source_categories
            ):
                valid.append(normalized)
        if not valid:
            return None
        health_rank = {"healthy": 0, "stable": 1, "degraded": 2, "unknown": 3}
        return min(valid, key=lambda item: health_rank.get(item.get("health"), 4))

    @staticmethod
    def _normalize_candidate(item: Any) -> dict[str, Any] | None:
        if not isinstance(item, dict):
            return None
        provider, endpoint = item.get("provider"), item.get("endpoint")
        if not isinstance(provider, str) or not provider or not isinstance(endpoint, str) or not endpoint:
            return None
        categories = item.get("categories")
        if not isinstance(categories, list):
            categories = [item.get("source_category")]
        category = next(
            (value for value in categories if isinstance(value, str) and value.strip()), None
        )
        price = item.get("price")
        amount = price.get("amount") if isinstance(price, dict) else None
        estimated_cost = (
            item.get("estimated_cost_usd")
            if "estimated_cost_usd" in item
            else amount.get("value") if isinstance(amount, dict) else None
        )
        metrics = item.get("metrics")
        health = item.get("health")
        if isinstance(metrics, dict) and isinstance(metrics.get("status"), str):
            health = metrics["status"]
        if category is None:
            return None
        return {
            "provider": provider,
            "endpoint": endpoint,
            "source_category": category,
            "estimated_cost_usd": estimated_cost,
            "health": health,
        }

    @staticmethod
    def _inputs_are_supported(inspected: dict[str, Any], request: EvidenceRequest) -> bool:
        input_schema = inspected.get("input")
        if not isinstance(input_schema, dict):
            return False
        return EvidenceBroker._fields_are_supported(
            input_schema.get("body"), request.input_body
        ) and EvidenceBroker._fields_are_supported(
            input_schema.get("queryParams"), request.input_query
        )

    @staticmethod
    def _fields_are_supported(schema: Any, values: Mapping[str, Any]) -> bool:
        if not values:
            return True
        if not isinstance(schema, dict):
            return False
        properties = schema.get("properties", schema)
        return isinstance(properties, dict) and set(values) <= set(properties)
