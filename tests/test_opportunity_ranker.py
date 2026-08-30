"""Target-aware opportunity ranking and abstention tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path

import pytest

from tools import opportunity_brief as brief
from tools import opportunity_ranker as ranker


EVIDENCE_HANDOFF = """# Current handoff

## Blockers

- Preserve unique experiment evidence with replayable verification after workspace relocation.

## Next Actions

- Keep the current continuation notes concise.
"""


def make_need(
    problem: str,
    query: str,
    *,
    category: str = "blocker",
) -> brief.NeedTheme:
    normalized = " ".join(
        "".join(character if character.isalnum() else " " for character in problem.casefold()).split()
    )
    need_id = f"need_{hashlib.sha256(f'{category}\0{normalized}'.encode()).hexdigest()[:24]}"
    return brief.NeedTheme(
        need_id=need_id,
        category=category,
        problem=problem,
        desired_improvement="Attach a transferable source-grounded mechanism.",
        existing_evidence="The handoff records the unresolved need.",
        gap="Independent replay and provenance evidence is absent.",
        query_text=query,
        handoff_span=problem,
    )


def make_record(
    *,
    source: str,
    problem: str,
    mechanism: str,
    context: str,
    boundary: str,
    status: str = "observed",
) -> brief.OpportunityRecordReceipt:
    digest = hashlib.sha256(source.encode()).hexdigest()
    return brief.OpportunityRecordReceipt(
        problem=problem,
        mechanism=mechanism,
        observed_effect=brief.OpportunityEffect(
            status=status,
            text={
                "observed": "Fixture tests observed the stated bounded behavior.",
                "intended": "The source describes this intended behavior.",
                "negative": "The source records this failure mode as a negative lesson.",
            }[status],
        ),
        context=context,
        boundary=boundary,
        evidence=brief.OpportunityEvidence(
            source_repo_id=f"repo-{source.casefold()}",
            source_repo_name=source,
            source_revision=digest[:40],
            source_revision_role="selection_time",
            license_type="MIT",
            license_sha256=digest,
            source_files=(f"src/{source.casefold()}.py",),
            source_symbols=(f"{source}Receipt",),
            source_sha256=(digest,),
        ),
        evidence_state="admitted",
        source_methodology_ids=(f"method-{source.casefold()}",),
    )


def record_id(record: brief.OpportunityRecordReceipt) -> str:
    canonical = json.dumps(
        record.to_mapping(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"opp_{hashlib.sha256(canonical.encode()).hexdigest()[:32]}"


def make_candidate(
    record: brief.OpportunityRecordReceipt,
    needs: tuple[brief.NeedTheme, ...],
    *,
    rank: int,
) -> brief.OpportunityCandidate:
    matches = tuple(
        brief.CandidateMatch(
            need_id=need.need_id,
            fts_rank=rank,
            semantic_rank=rank,
            rrf_score=2.0 / (60 + rank),
        )
        for need in needs
    )
    return brief.OpportunityCandidate(
        record_id=record_id(record),
        record=record,
        matches=matches,
    )


def make_receipt(
    tmp_path: Path,
    needs: tuple[brief.NeedTheme, ...],
    candidates: tuple[brief.OpportunityCandidate, ...],
) -> brief.AcquisitionReceipt:
    identity = (1, 2, 1, 10, 3, 4)
    digest = "a" * 64
    command = tmp_path / "cam"
    sidecar = tmp_path / "opportunities.sqlite"
    model = tmp_path / "model"
    closure = brief.ExecutionClosureReceipt(
        launcher_kind="native",
        launcher_path=command,
        launcher_identity=identity,
        launcher_sha256=digest,
        interpreter_path=None,
        interpreter_symlink_chain=(),
        resolved_interpreter_path=None,
        resolved_interpreter_identity=None,
        interpreter_sha256=None,
        python_home=None,
        python_home_identity=None,
        python_runtime_library_path=None,
        python_runtime_library_identity=None,
        python_runtime_library_sha256=None,
        editable_site_packages=None,
        editable_site_packages_identity=None,
        editable_metadata_sha256=None,
        cam_source_root=None,
        cam_source_root_identity=None,
        cam_source_revision=None,
        cam_source_branch=None,
        cam_source_dirty_entries=(),
        cam_source_sha256=None,
    )
    calls = tuple(
        brief.AcquisitionCall(
            need_id=need.need_id,
            query=need.query_text,
            argv=(
                str(command),
                "opportunity-query",
                need.query_text,
                "--db",
                str(sidecar),
                "--target-repo-id",
                "target-repo-01",
                "--semantic-model-path",
                str(model),
                "--limit",
                "20",
                "--json",
            ),
            executable_identity=identity,
            executable_sha256=digest,
            sidecar_identity=identity,
            sidecar_sha256=digest,
            semantic_model_identity=identity,
            semantic_model_sha256=digest,
            execution_closure_sha256=closure.sha256,
            status="ok",
            result_count=sum(
                need.need_id in {match.need_id for match in candidate.matches}
                for candidate in candidates
            ),
            rejection_count=0,
        )
        for need in needs
    )
    return brief.AcquisitionReceipt(
        target_repo_id="target-repo-01",
        model_id=str(model),
        cam_command=command,
        executable_identity=identity,
        executable_sha256=digest,
        sidecar=sidecar,
        sidecar_identity=identity,
        sidecar_sha256=digest,
        semantic_model_path=model,
        semantic_model_identity=identity,
        semantic_model_sha256=digest,
        execution_closure=closure,
        calls=calls,
        candidates=candidates,
        rejections=(),
        gaps=(),
    )


def evidence_fixtures() -> tuple[brief.OpportunityRecordReceipt, ...]:
    return (
        make_record(
            source="imbora",
            problem="Experiment evidence cannot be independently replayed after relocation.",
            mechanism=(
                "Append-only hash-chained evidence receipts and a root-independent replay "
                "manifest bind artifact digests to an exact replay command."
            ),
            context="Reproducible experiment evidence and verification across workspaces.",
            boundary="Not an off-device backup and does not verify target scientific claims.",
        ),
        make_record(
            source="buzz",
            problem="Long agent context windows overflow during extended conversations.",
            mechanism="Bounded in-memory self-summarization compacts agent context history.",
            context="Agent handoff continuity inside one running process.",
            boundary="No persistence and unrelated to preserving unique experiment evidence.",
            status="intended",
        ),
        make_record(
            source="GenericAgent",
            problem="A fixed agent tool surface cannot express every future capability.",
            mechanism="A minimal atomic toolset uses code execution as a dynamic escape hatch.",
            context="General agent capability extension during a build.",
            boundary="Not evidence preservation, replay, or scientific verification.",
            status="intended",
        ),
    )


def test_evidence_need_selects_only_imbora_with_exact_inspection_formula(
    tmp_path: Path,
) -> None:
    need = make_need(
        "Preserve unique experiment evidence with replayable verification after workspace relocation.",
        "experiment evidence replay verification relocation",
    )
    records = evidence_fixtures()
    acquired = make_receipt(
        tmp_path,
        (need,),
        tuple(
            make_candidate(record, (need,), rank=index)
            for index, record in enumerate(records, start=1)
        ),
    )

    result = ranker.rank_and_select(
        needs=(need,),
        handoff_text=EVIDENCE_HANDOFF,
        acquired=acquired,
        maximum=5,
    )

    assert ranker.MINIMUM_SELECTION_SCORE == 0.48
    assert [item.source_repo_name for item in result.selected] == ["imbora"]
    assert result.rejected_by_source["buzz"].reason in {
        "not_relevant_to_need",
        "not_additive_to_handoff",
    }
    assert result.rejected_by_source["GenericAgent"].reason == "not_relevant_to_need"
    for item in result.dispositions:
        components = item.components
        assert all(
            0.0 <= value <= 1.0
            for value in (
                components.normalized_rrf,
                components.need_relevance,
                components.additive_beyond_handoff,
                components.evidence_quality,
                components.cross_context_transfer,
                components.generic_match_penalty,
                components.redundancy_penalty,
            )
        )
        assert item.ranking_score == pytest.approx(
            0.35 * components.normalized_rrf
            + 0.25 * components.need_relevance
            + 0.20 * components.additive_beyond_handoff
            + 0.15 * components.evidence_quality
            + 0.05 * components.cross_context_transfer
            - 0.20 * components.generic_match_penalty
            - 0.25 * components.redundancy_penalty
        )
    with pytest.raises(FrozenInstanceError):
        result.selected[0].ranking_score = 1.0


def test_unrelated_need_abstains_from_every_candidate(tmp_path: Path) -> None:
    need = make_need(
        "Render a lunar shader with spectral caustics.",
        "lunar shader spectral caustics",
    )
    records = evidence_fixtures()
    acquired = make_receipt(
        tmp_path,
        (need,),
        tuple(
            make_candidate(record, (need,), rank=index)
            for index, record in enumerate(records, start=1)
        ),
    )

    result = ranker.rank_and_select(
        needs=(need,),
        handoff_text="## Blockers\n\n- Render a lunar shader with spectral caustics.\n",
        acquired=acquired,
    )

    assert result.selected == ()
    assert {item.reason for item in result.rejected} == {"not_relevant_to_need"}
    assert result.need_audit[0].selected_record_ids == ()


def test_handoff_duplicate_and_equivalent_mechanisms_are_audited(
    tmp_path: Path,
) -> None:
    need = make_need(
        "Preserve evidence with content-addressed receipts.",
        "preserve evidence content addressed receipts",
    )
    first = make_record(
        source="source-a",
        problem="Evidence receipts need content identity.",
        mechanism="Append-only hash-chained evidence receipt manifest.",
        context="Evidence replay after process failure.",
        boundary="Does not copy artifacts off device.",
    )
    equivalent = make_record(
        source="source-b",
        problem="Evidence receipts need content identity.",
        mechanism="Hash-chained append-only manifest for evidence receipts.",
        context="Evidence replay after process failure.",
        boundary="Does not copy artifacts off device.",
    )
    duplicate = make_record(
        source="source-c",
        problem="Evidence receipts need content identity.",
        mechanism="Per-artifact content-addressed receipts already named in the handoff.",
        context="Evidence replay after process failure.",
        boundary="Does not copy artifacts off device.",
    )
    acquired = make_receipt(
        tmp_path,
        (need,),
        (
            make_candidate(first, (need,), rank=1),
            make_candidate(equivalent, (need,), rank=2),
            make_candidate(duplicate, (need,), rank=3),
        ),
    )
    handoff = (
        "## Blockers\n\n- Preserve evidence with content-addressed receipts.\n"
        "- Per-artifact content-addressed receipts already named in the handoff.\n"
    )

    result = ranker.rank_and_select(
        needs=(need,),
        handoff_text=handoff,
        acquired=acquired,
    )

    assert len(result.selected) == 1
    assert result.rejected_by_source["source-b"].reason == "equivalent_mechanism"
    assert result.rejected_by_source["source-c"].reason == "not_additive_to_handoff"
    group = next(group for group in result.mechanism_audit if len(group.record_ids) == 2)
    assert set(group.record_ids) == {record_id(first), record_id(equivalent)}
    assert group.selected_record_id == result.selected[0].record_id


def test_source_diversity_and_cross_need_deduplication_precede_fill(
    tmp_path: Path,
) -> None:
    evidence_need = make_need(
        "Preserve evidence replay receipts.",
        "preserve evidence replay receipts",
    )
    integrity_need = make_need(
        "Detect artifact drift during replay.",
        "artifact drift replay detection",
        category="risk",
    )
    first = make_record(
        source="source-a",
        problem="Evidence replay lacks receipts.",
        mechanism="Bind replay receipts to artifact digests.",
        context="Evidence integrity across workspaces.",
        boundary="Does not provide remote backup.",
    )
    same_source = make_record(
        source="source-a",
        problem="Artifact drift can invalidate replay.",
        mechanism="Compare a ledger checksum before replay begins.",
        context="Artifact evidence drift detection.",
        boundary="Detects drift but does not repair data.",
    )
    other_source = make_record(
        source="source-b",
        problem="Artifact drift can invalidate evidence replay.",
        mechanism="Reject replay when a referenced artifact digest changes.",
        context="Independent evidence verification.",
        boundary="Rejects drift but does not recover the artifact.",
    )
    acquired = make_receipt(
        tmp_path,
        (evidence_need, integrity_need),
        (
            make_candidate(first, (evidence_need, integrity_need), rank=1),
            make_candidate(same_source, (integrity_need,), rank=2),
            make_candidate(other_source, (integrity_need,), rank=3),
        ),
    )

    result = ranker.rank_and_select(
        needs=(evidence_need, integrity_need),
        handoff_text="## Blockers\n\n- Preserve evidence integrity.\n",
        acquired=acquired,
        maximum=2,
    )

    assert len(result.selected) == 2
    assert len({item.source_repo_id for item in result.selected}) == 2
    assert sum(item.record_id == record_id(first) for item in result.selected) == 1
    first_item = next(item for item in result.selected if item.record_id == record_id(first))
    assert first_item.matched_need_ids == (evidence_need.need_id, integrity_need.need_id)
    assert result.rejected_by_source["source-a"].reason == "source_diversity"
    assert all(audit.selected_record_ids for audit in result.need_audit)


def test_negative_lessons_are_selectable_and_cardinality_is_zero_to_five(
    tmp_path: Path,
) -> None:
    need = make_need(
        "Prevent evidence loss during replay.",
        "prevent evidence loss replay",
    )
    negative = make_record(
        source="negative-source",
        problem="Mutable replay logs lose evidence after partial failure.",
        mechanism="Treat mutable replay logs as a negative lesson and require immutable receipts.",
        context="Evidence replay recovery.",
        boundary="The failed design is evidence to avoid, not a recommended implementation.",
        status="negative",
    )
    empty = make_receipt(tmp_path / "empty", (need,), ())
    assert ranker.rank_and_select(
        needs=(need,),
        handoff_text="## Risks\n\n- Prevent evidence loss during replay.\n",
        acquired=empty,
    ).selected == ()

    candidates = tuple(
        make_candidate(
            negative
            if index == 0
            else make_record(
                source=f"source-{index}",
                problem="Evidence replay can lose artifact integrity.",
                mechanism=f"Replay evidence receipt variant {index} binds artifact integrity digests.",
                context="Evidence replay integrity.",
                boundary="Does not provide remote recovery.",
            ),
            (need,),
            rank=index + 1,
        )
        for index in range(7)
    )
    acquired = make_receipt(tmp_path, (need,), candidates)
    result = ranker.rank_and_select(
        needs=(need,),
        handoff_text="## Risks\n\n- Prevent evidence loss during replay.\n",
        acquired=acquired,
        maximum=5,
    )

    assert 0 < len(result.selected) <= 5
    assert len(result.selected) == 5
    assert any(item.record.observed_effect.status == "negative" for item in result.selected)
    assert len(result.dispositions) == 7
    assert {item.disposition for item in result.dispositions} == {"selected", "rejected"}
    assert len(result.source_audit) == 7


def test_ranker_rejects_invalid_selection_bounds(tmp_path: Path) -> None:
    need = make_need("Preserve evidence replay.", "preserve evidence replay")
    acquired = make_receipt(tmp_path, (need,), ())

    for maximum in (True, 0, 6):
        with pytest.raises((TypeError, ValueError), match="maximum"):
            ranker.rank_and_select(
                needs=(need,),
                handoff_text=EVIDENCE_HANDOFF,
                acquired=acquired,
                maximum=maximum,
            )
