"""Deterministic cross-repository fixture proof for the CAM_Codx evidence chain."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _cam_cam_root() -> Path:
    configured = os.environ.get("CAM_CAM_ROOT")
    candidates = [
        Path(configured).expanduser() if configured else None,
        ROOT.parent / "CAM_CAM",
        ROOT.parent / "CAM_CAM_goal3",
    ]
    for candidate in candidates:
        if candidate is not None and (candidate / "tests" / "test_managed_runs.py").is_file():
            return candidate.resolve()
    raise AssertionError("CAM_CAM test fixture checkout could not be resolved")


def _managed_run_fixture_module():
    cam_cam = _cam_cam_root()
    sys.path.insert(0, str(cam_cam / "src"))
    path = cam_cam / "tests" / "test_managed_runs.py"
    spec = importlib.util.spec_from_file_location("cam_cam_managed_run_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_fixture_chain_keeps_only_corrected_verified_outcome_positive(tmp_path: Path) -> None:
    fixture = _managed_run_fixture_module()
    from claw.core.config import DatabaseConfig
    from claw.core.models import LandingOrigin
    from claw.db.engine import DatabaseEngine
    from claw.db.repository import Repository
    from claw.managed_runs import (
        AssessmentLabel,
        CandidateDecision,
        ManagedOutcome,
        ManagedRunService,
        MiningReceiptLink,
        OutcomeStatus,
        SelectionDecision,
    )
    from tools.cam_control_plane import build_outcome_memory_assessment

    engine = DatabaseEngine(DatabaseConfig(db_path=":memory:"))
    await engine.connect()
    await engine.initialize_schema()
    try:
        repository = Repository(engine)
        plan, packet, card = await fixture._seed_packet(repository)
        service = ManagedRunService(repository)
        await service.start_run("fixture-run", plan)

        mining_receipt = tmp_path / "mining.json"
        mining_receipt.write_text('{"fixture":true}\n', encoding="utf-8")
        import hashlib

        await service.link_mining_receipt(
            "fixture-run",
            MiningReceiptLink(
                receipt_id="fixture-mining",
                receipt_path=str(mining_receipt),
                receipt_sha256=hashlib.sha256(mining_receipt.read_bytes()).hexdigest(),
                source_repositories=["fixture/donor@abc123"],
            ),
        )
        await service.record_candidate_decision(
            "fixture-run",
            CandidateDecision(
                candidate_id=card.id,
                label=AssessmentLabel.DIRECT_PRECEDENT,
                decision=SelectionDecision.SELECTED,
                reason="fixture direct precedent",
                provenance=["fixture/donor@abc123:retry.py"],
                limitations=["fixture only"],
                slot_id=packet.slot.slot_id,
            ),
        )
        await service.record_candidate_decision(
            "fixture-run",
            CandidateDecision(
                candidate_id="fixture-rejected",
                label=AssessmentLabel.NEW_HYPOTHESIS,
                decision=SelectionDecision.REJECTED,
                reason="not verified",
                provenance=["fixture/hypothesis"],
                limitations=["not evidence"],
            ),
        )
        await service.link_packet_pair("fixture-run", packet.packet_id)
        await service.record_landing(
            "fixture-run",
            packet_id=packet.packet_id,
            slot_id=packet.slot.slot_id,
            file_path="src/client.py",
            symbol="request",
            diff_hunk_id="fixture-hunk",
            origin=LandingOrigin.ADAPTED_COMPONENT,
        )
        failed = await service.record_outcome(
            "fixture-run",
            packet_id=packet.packet_id,
            slot_id=packet.slot.slot_id,
            outcome=ManagedOutcome(
                status=OutcomeStatus.VERIFIED_FAILURE,
                verifier_findings=["fixture failure"],
                test_refs=["fixture::verification"],
            ),
        )
        await fixture._mark_packet_verified(repository, packet)
        corrected = await service.record_outcome(
            "fixture-run",
            packet_id=packet.packet_id,
            slot_id=packet.slot.slot_id,
            outcome=ManagedOutcome(
                status=OutcomeStatus.VERIFIED_SUCCESS,
                verifier_findings=[],
                test_refs=["fixture::verification"],
                verification_evidence=[fixture._verification_evidence(tmp_path, plan=plan)],
                recipe_eligible=True,
                trust_delta=1,
                supersedes_outcome_id=failed.id,
            ),
        )
        report = await service.source_to_outcome_report("fixture-run")
        assessment = build_outcome_memory_assessment(report)
    finally:
        await engine.close()

    assert corrected.success is True and corrected.recipe_eligible is True
    assert report["status"] == "verified_success"
    assert report["outcomes"][0]["status"] == "verified_failure"
    assert report["outcomes"][1]["supersedes_outcome_id"] == failed.id
    assert report["outcomes"][1]["status"] == "verified_success"
    assert report["active_outcomes"][packet.slot.slot_id]["status"] == "verified_success"
    assert report["positive_evidence_count"] == 1
    assert [item["decision"] for item in report["candidate_decisions"]] == [
        "selected",
        "rejected",
    ]
    assert assessment["positive_evidence_count"] == 1
    assert assessment["positive_recommendations"][0]["outcome_id"] == corrected.id
    assert assessment["failure_warnings"][0]["outcome_id"] == failed.id
    assert assessment["unverified_hypotheses"][0]["candidate_id"] == "fixture-rejected"
