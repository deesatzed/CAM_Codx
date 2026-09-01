from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

from tools.monid_evidence_broker import (
    EvidencePolicy,
    EvidencePolicyError,
    EvidenceRequest,
    EvidenceBroker,
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
