from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

from tools.monid_evidence_broker import (
    EvidencePolicy,
    EvidencePolicyError,
    EndpointCatalogLedger,
    EvidenceRequest,
    EvidenceBroker,
    MonidExecutionError,
    SubprocessMonidRunner,
)


def test_policy_requires_finite_task_budget_and_freshness() -> None:
    with pytest.raises(EvidencePolicyError, match="task_budget_usd"):
        EvidencePolicy(
            task_budget_usd=math.nan,
            freshness_seconds=3600,
            allowed_source_categories=frozenset({"public"}),
            retention_class="local",
            prohibited_data_classes=frozenset(),
        )

    with pytest.raises(EvidencePolicyError, match="freshness_seconds"):
        EvidencePolicy(
            task_budget_usd=1.0,
            freshness_seconds=0,
            allowed_source_categories=frozenset({"public"}),
            retention_class="local",
            prohibited_data_classes=frozenset(),
        )


def test_request_rejects_prohibited_data_class() -> None:
    policy = EvidencePolicy(
        task_budget_usd=1.0,
        freshness_seconds=3600,
        allowed_source_categories=frozenset({"public"}),
        retention_class="local",
        prohibited_data_classes=frozenset({"personal"}),
    )

    with pytest.raises(EvidencePolicyError, match="prohibited"):
        EvidenceRequest(
            task_id="task-1",
            question="Who maintains this package?",
            requested_data_classes=frozenset({"personal"}),
            policy=policy,
        )


def test_compatible_fresh_cache_hit_skips_external_runner(tmp_path: Path) -> None:
    request = EvidenceRequest(
        task_id="task-1",
        question="Who maintains this package?",
        requested_data_classes=frozenset({"public"}),
        policy=EvidencePolicy(
            task_budget_usd=1.0,
            freshness_seconds=3600,
            allowed_source_categories=frozenset({"public"}),
            retention_class="local",
            prohibited_data_classes=frozenset(),
        ),
    )
    broker = EvidenceBroker(tmp_path / "state", now=lambda: 1000.0)
    stored = broker.store_completed_result(
        request,
        raw_result={"status": "ok"},
        source_category="public",
        cost_usd=0.12,
    )

    packet = broker.resolve_cached(request)

    assert packet.cache_status == "hit"
    assert packet.raw_sha256 == stored.raw_sha256
    assert packet.cost_usd == 0.0


def test_expired_or_incompatible_cache_entry_is_not_reused(tmp_path: Path) -> None:
    policy = EvidencePolicy(
        task_budget_usd=1.0,
        freshness_seconds=60,
        allowed_source_categories=frozenset({"public"}),
        retention_class="local",
        prohibited_data_classes=frozenset(),
    )
    request = EvidenceRequest(
        task_id="task-1",
        question="Who maintains this package?",
        requested_data_classes=frozenset({"public"}),
        policy=policy,
    )
    broker = EvidenceBroker(tmp_path / "state", now=lambda: 1000.0)
    broker.store_completed_result(
        request,
        raw_result={"status": "ok"},
        source_category="public",
        cost_usd=0.12,
    )

    expired = EvidenceBroker(tmp_path / "state", now=lambda: 1061.0)
    assert expired.resolve_cached(request).cache_status == "miss"

    incompatible = EvidenceRequest(
        task_id="task-2",
        question="Who maintains this package?",
        requested_data_classes=frozenset({"public"}),
        policy=EvidencePolicy(
            task_budget_usd=1.0,
            freshness_seconds=3600,
            allowed_source_categories=frozenset({"another-source"}),
            retention_class="local",
            prohibited_data_classes=frozenset(),
        ),
    )
    assert broker.resolve_cached(incompatible).cache_status == "miss"


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: list[str]) -> dict[str, Any]:
        self.calls.append(tuple(argv))
        if argv[1] == "discover":
            return {
                "results": [
                    {
                        "provider": "fixture-provider",
                        "endpoint": "/maintainers",
                        "source_category": "public",
                        "estimated_cost_usd": 0.12,
                        "health": "healthy",
                    }
                ]
            }
        if argv[1] == "inspect":
            return {"input": {"body": {"package": "string"}}}
        if argv[1] == "run":
            return {"maintainers": ["Example Org"]}
        raise AssertionError(f"unexpected command: {argv}")


def test_cache_miss_discovers_then_inspects_before_running(tmp_path: Path) -> None:
    request = EvidenceRequest(
        task_id="task-1",
        question="Who maintains this package?",
        requested_data_classes=frozenset({"public"}),
        input_body={"package": "example"},
        policy=EvidencePolicy(
            task_budget_usd=1.0,
            freshness_seconds=3600,
            allowed_source_categories=frozenset({"public"}),
            retention_class="local",
            prohibited_data_classes=frozenset(),
        ),
    )
    runner = RecordingRunner()

    packet = EvidenceBroker(tmp_path / "state", runner=runner, now=lambda: 1000.0).resolve(request)

    assert [call[:2] for call in runner.calls] == [
        ("monid", "discover"),
        ("monid", "inspect"),
        ("monid", "run"),
    ]
    assert packet.cache_status == "miss"
    assert packet.disposition == "available"
    assert packet.cost_usd == 0.12


def test_unknown_or_over_budget_endpoint_stops_before_run(tmp_path: Path) -> None:
    request = EvidenceRequest(
        task_id="task-1",
        question="Who maintains this package?",
        requested_data_classes=frozenset({"public"}),
        policy=EvidencePolicy(
            task_budget_usd=0.1,
            freshness_seconds=3600,
            allowed_source_categories=frozenset({"public"}),
            retention_class="local",
            prohibited_data_classes=frozenset(),
        ),
    )
    runner = RecordingRunner()

    packet = EvidenceBroker(tmp_path / "state", runner=runner).resolve(request)

    assert packet.disposition == "blocked_budget"
    assert [call[1] for call in runner.calls] == ["discover"]


class LiveSchemaRunner(RecordingRunner):
    def run(self, argv: list[str]) -> dict[str, Any]:
        self.calls.append(tuple(argv))
        if argv[1] == "discover":
            return {
                "results": [
                    {
                        "provider": "surf",
                        "endpoint": "/prediction-market/analytics",
                        "categories": ["prediction-markets", "surf"],
                        "price": {"amount": {"value": 0.024, "currency": "USD"}},
                        "metrics": {"status": "unknown"},
                    }
                ]
            }
        if argv[1] == "inspect":
            return {"input": {"queryParams": {"properties": {"platform": {}, "limit": {}}}}}
        if argv[1] == "run":
            return {"data": {"momentum_markets": []}}
        raise AssertionError(f"unexpected command: {argv}")


def test_live_monid_schema_uses_disclosed_price_categories_and_query_params(tmp_path: Path) -> None:
    request = EvidenceRequest(
        task_id="kalshi-screen",
        question="Which AI market has the highest swing potential?",
        requested_data_classes=frozenset({"public"}),
        input_query={"platform": "kalshi", "limit": 20},
        policy=EvidencePolicy(
            task_budget_usd=0.05,
            freshness_seconds=1800,
            allowed_source_categories=frozenset({"prediction-markets"}),
            retention_class="local",
            prohibited_data_classes=frozenset(),
        ),
    )
    runner = LiveSchemaRunner()

    packet = EvidenceBroker(tmp_path / "state", runner=runner, now=lambda: 1000.0).resolve(request)

    assert packet.cost_usd == 0.024
    assert packet.source_category == "prediction-markets"
    run_call = runner.calls[-1]
    assert "--query" in run_call
    assert "platform" in run_call[run_call.index("--query") + 1]


def test_subprocess_runner_uses_list_form_and_requires_json_object(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> Any:
        calls.append((argv, kwargs))
        return type("Completed", (), {"returncode": 0, "stdout": '{"ok": true}', "stderr": ""})()

    monkeypatch.setattr("tools.monid_evidence_broker.subprocess.run", fake_run)

    result = SubprocessMonidRunner().run(["monid", "discover", "-j", "-q", "Kalshi"])

    assert result == {"ok": True}
    assert calls[0][0] == ["monid", "discover", "-j", "-q", "Kalshi"]
    assert calls[0][1]["shell"] is False


def test_subprocess_runner_rejects_non_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "tools.monid_evidence_broker.subprocess.run",
        lambda *_args, **_kwargs: type(
            "Completed", (), {"returncode": 0, "stdout": "not json", "stderr": ""}
        )(),
    )

    with pytest.raises(MonidExecutionError, match="JSON object"):
        SubprocessMonidRunner().run(["monid", "discover", "-j", "-q", "Kalshi"])


class CatalogRunner:
    def __init__(self, *, endpoints: list[str], schemas: dict[str, dict[str, Any]]) -> None:
        self.endpoints = endpoints
        self.schemas = schemas

    def run(self, argv: list[str]) -> dict[str, Any]:
        if argv[1] == "discover":
            return {
                "results": [
                    {
                        "provider": "surf",
                        "endpoint": endpoint,
                        "categories": ["prediction-markets"],
                        "price": {"amount": {"value": 0.024}},
                    }
                    for endpoint in self.endpoints
                ]
            }
        if argv[1] == "inspect":
            return self.schemas[argv[argv.index("-e") + 1]]
        raise AssertionError(f"unexpected command: {argv}")


def test_catalog_ledger_reports_added_endpoint_and_selected_schema_drift(tmp_path: Path) -> None:
    question = "Kalshi AI markets"
    first = CatalogRunner(
        endpoints=["/markets"],
        schemas={"/markets": {"input": {"queryParams": {"properties": {"limit": {}}}}}},
    )
    ledger = EndpointCatalogLedger(tmp_path / "state", runner=first, now=lambda: 1000.0)
    initial = ledger.refresh(question, selected_endpoint=("surf", "/markets"), cli_version="0.1.7")

    assert initial.has_drift is False

    second = CatalogRunner(
        endpoints=["/markets", "/analytics"],
        schemas={"/markets": {"input": {"queryParams": {"properties": {"ticker": {}}}}}},
    )
    changed = EndpointCatalogLedger(tmp_path / "state", runner=second, now=lambda: 2000.0).refresh(
        question, selected_endpoint=("surf", "/markets"), cli_version="0.1.7"
    )

    assert changed.added_endpoints == ("surf /analytics",)
    assert changed.schema_changed_endpoints == ("surf /markets",)
    assert changed.has_drift is True


def test_schema_drift_invalidates_cached_evidence_from_that_endpoint(tmp_path: Path) -> None:
    request = EvidenceRequest(
        task_id="task-1",
        question="Kalshi AI markets",
        requested_data_classes=frozenset({"public"}),
        policy=EvidencePolicy(1.0, 3600, frozenset({"prediction-markets"}), "local", frozenset()),
    )
    broker = EvidenceBroker(tmp_path / "state", now=lambda: 1000.0)
    broker.store_completed_result(
        request,
        raw_result={"ok": True},
        source_category="prediction-markets",
        cost_usd=0.024,
        endpoint_id="surf /markets",
    )

    assert broker.invalidate_endpoint_drift({"surf /markets"}) == 1
    assert broker.resolve_cached(request).cache_status == "miss"
