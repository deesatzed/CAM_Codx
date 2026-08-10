import importlib.util
from pathlib import Path
import sys

import pytest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "development_brief.py"


def _load_contract():
    assert MODULE_PATH.is_file(), "Development Brief contract module is missing"
    spec = importlib.util.spec_from_file_location("development_brief", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_brief_request_only_accepts_new_or_continue_rescue() -> None:
    brief = _load_contract()

    assert brief.BriefRequest(mode="new", task_text="Build a durable import retry flow").mode == "new"
    assert (
        brief.BriefRequest(
            mode="continue-rescue", task_text="Decide the smallest safe next repair"
        ).mode
        == "continue-rescue"
    )
    with pytest.raises(brief.BriefValidationError, match="mode"):
        brief.BriefRequest(mode="explore", task_text="anything")
    with pytest.raises(brief.BriefValidationError, match="task"):
        brief.BriefRequest(mode="new", task_text="   ")


def test_evidence_item_requires_one_known_class_and_full_provenance() -> None:
    brief = _load_contract()

    item = brief.EvidenceItem(
        evidence_class=brief.EvidenceClass.DIRECT_PRECEDENT,
        title="Retry state machine",
        source_id="method-123",
        source_kind="cam_methodology",
        why_it_applies="It shares the target's Python retry concern.",
        confidence=brief.Confidence.MEDIUM,
        limitation="The source has not been inspected in this target.",
    )

    assert item.evidence_class is brief.EvidenceClass.DIRECT_PRECEDENT
    with pytest.raises(brief.BriefValidationError, match="evidence class"):
        brief.EvidenceItem(
            evidence_class="unlabelled",
            title="Missing class",
            source_id="method-456",
            source_kind="cam_methodology",
            why_it_applies="No classification.",
            confidence=brief.Confidence.LOW,
            limitation="Not safe to adopt.",
        )
    with pytest.raises(brief.BriefValidationError, match="source_id"):
        brief.EvidenceItem(
            evidence_class=brief.EvidenceClass.NEW_HYPOTHESIS,
            title="Missing provenance",
            source_id="",
            source_kind="cam_methodology",
            why_it_applies="It might help.",
            confidence=brief.Confidence.LOW,
            limitation="Needs validation.",
        )


def test_renderer_keeps_one_recommended_step_and_visible_limits() -> None:
    brief = _load_contract()
    request = brief.BriefRequest(mode="new", task_text="Build a durable import retry flow")
    evidence = brief.EvidenceItem(
        evidence_class=brief.EvidenceClass.TRANSFERABLE_ANALOGY,
        title="Transactional recovery pattern",
        source_id="method-789",
        source_kind="cam_methodology",
        why_it_applies="The recovery boundary transfers, despite a different domain.",
        confidence=brief.Confidence.LOW,
        limitation="It is an analogy, not a drop-in implementation.",
    )
    development_brief = brief.DevelopmentBrief(
        request=request,
        target_evidence=(),
        evidence_items=(evidence,),
        recommendation="Start with the bounded retry state machine.",
        recommended_next_step=brief.NextStep(
            kind="create_plan",
            summary="Create a small implementation plan with a retry-state test.",
        ),
        optional_next_steps=(
            brief.NextStep(kind="inspect_source", summary="Inspect method-789 before reuse."),
        ),
        limitations=("No target repository was supplied.",),
    )

    rendered = brief.render_markdown(development_brief)

    assert rendered.count("## Recommended next step") == 1
    assert "Transferable analogy" in rendered
    assert "Why this applies" in rendered
    assert "Confidence: low" in rendered
    assert "No target repository was supplied." in rendered
