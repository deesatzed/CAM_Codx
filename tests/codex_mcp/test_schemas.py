"""Pydantic v2 input/output model tests for the 4 MCP tools.

See build_specs.md §3 for the canonical schemas.
"""

import pytest
from pydantic import ValidationError

from claw_codex_mcp.schemas import (
    CamRecallInput, CamRecallOutput, MethodologyHit,
    CamProvenanceInput, CamProvenanceOutput, MethodologyLink,
    CamDecisionsSearchInput, CamDecisionsSearchOutput, DecisionHit,
    CamRecordOutcomeInput, CamRecordOutcomeOutput,
)


# --- cam_recall ---

def test_cam_recall_input_minimal_valid() -> None:
    m = CamRecallInput(query="rate limit serverless")
    assert m.k == 5
    assert m.include_embryonic is False
    assert m.include_stale is True

def test_cam_recall_input_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        CamRecallInput(query="")

def test_cam_recall_input_rejects_k_out_of_range() -> None:
    with pytest.raises(ValidationError):
        CamRecallInput(query="x", k=0)
    with pytest.raises(ValidationError):
        CamRecallInput(query="x", k=21)

def test_cam_recall_input_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        CamRecallInput(query="x", surprise_field=True)

def test_cam_recall_output_carries_corpus_status() -> None:
    out = CamRecallOutput(results=[], query_echo="x", corpus_status="absent")
    assert out.corpus_status == "absent"

def test_cam_recall_output_rejects_invalid_corpus_status() -> None:
    with pytest.raises(ValidationError):
        CamRecallOutput(results=[], query_echo="x", corpus_status="bogus")


# --- cam_provenance ---

def test_cam_provenance_input_rejects_empty_id() -> None:
    with pytest.raises(ValidationError):
        CamProvenanceInput(methodology_id="")

def test_cam_provenance_output_found_false_shape() -> None:
    out = CamProvenanceOutput(found=False, methodology_id="missing-id", corpus_status="absent")
    assert out.found is False
    assert out.provenance is None


# --- cam_decisions_search ---

def test_cam_decisions_search_input_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        CamDecisionsSearchInput(query="")


# --- cam_record_outcome ---

def test_cam_record_outcome_input_requires_at_least_one_methodology() -> None:
    with pytest.raises(ValidationError):
        CamRecordOutcomeInput(
            methodology_ids=[],
            task_id="t1", repo="/r", outcome="green",
            run_hash="abcdef01abcdef01",
        )

def test_cam_record_outcome_input_rejects_invalid_outcome() -> None:
    with pytest.raises(ValidationError):
        CamRecordOutcomeInput(
            methodology_ids=["m1"], task_id="t1", repo="/r",
            outcome="catastrophic",  # not in the literal set
            run_hash="abcdef01abcdef01",
        )

def test_cam_record_outcome_input_min_run_hash_length() -> None:
    with pytest.raises(ValidationError):
        CamRecordOutcomeInput(
            methodology_ids=["m1"], task_id="t1", repo="/r",
            outcome="green", run_hash="short",
        )
