import importlib.util
from pathlib import Path
import subprocess
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


def _git_repository(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    (path / "GOAL.md").write_text("# Goal\n\nDeliver a durable importer.\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "GOAL.md"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "-c",
            "user.name=Development Brief Test",
            "-c",
            "user.email=brief-test@example.invalid",
            "commit",
            "-qm",
            "initial target truth",
        ],
        check=True,
    )


def test_target_inspector_reports_truth_dirty_state_gaps_and_unrun_verification(
    tmp_path: Path,
) -> None:
    brief = _load_contract()
    target = tmp_path / "target"
    target.mkdir()
    _git_repository(target)
    source = target / "src" / "importer.py"
    source.parent.mkdir()
    source.write_text("def import_data():\n    # TODO: retain retry state\n    raise NotImplementedError\n", encoding="utf-8")
    before = {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}

    inspection = brief.inspect_target_read_only(target)

    assert inspection.is_git_repository is True
    assert "GOAL.md" in inspection.read_truth_files
    assert any("src/importer.py" in entry for entry in inspection.dirty_entries)
    assert any("TODO" in gap for gap in inspection.visible_gaps)
    assert any("NotImplemented" in gap for gap in inspection.visible_gaps)
    assert inspection.verification_status == "not_run"
    after = {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}
    assert after == before


def test_target_inspector_does_not_discover_sibling_repositories(tmp_path: Path) -> None:
    brief = _load_contract()
    target = tmp_path / "target"
    sibling = tmp_path / "sibling"
    target.mkdir()
    sibling.mkdir()
    _git_repository(sibling)
    (sibling / "src.py").write_text("# TODO: ignored sibling\n", encoding="utf-8")

    inspection = brief.inspect_target_read_only(target)

    assert inspection.is_git_repository is False
    assert inspection.read_truth_files == ()
    assert inspection.visible_gaps == ()


def test_continue_rescue_advice_is_explainable_for_all_outcomes(tmp_path: Path) -> None:
    brief = _load_contract()

    healthy = brief.TargetInspection(
        target_path=tmp_path,
        is_git_repository=True,
        branch="main",
        read_truth_files=("GOAL.md",),
        missing_truth_files=(),
        dirty_entries=(),
        visible_gaps=(),
        risks=(),
        verification_status="not_run",
    )
    continue_advice = brief.recommend_continue_rescue(healthy, current_test_receipt="passed")
    assert continue_advice.action == "continue"
    assert "does not prove product completeness" in continue_advice.limitation

    dirty = brief.TargetInspection(
        target_path=tmp_path,
        is_git_repository=True,
        branch="main",
        read_truth_files=("GOAL.md",),
        missing_truth_files=(),
        dirty_entries=(" M src/importer.py",),
        visible_gaps=(),
        risks=(),
        verification_status="not_run",
    )
    mitigate_advice = brief.recommend_continue_rescue(dirty)
    assert mitigate_advice.action == "mitigate"
    assert any("dirty" in reason.lower() for reason in mitigate_advice.reasons)

    structurally_risky = brief.TargetInspection(
        target_path=tmp_path,
        is_git_repository=False,
        branch=None,
        read_truth_files=(),
        missing_truth_files=("GOAL.md", "PROGRESS.md"),
        dirty_entries=(),
        visible_gaps=(),
        risks=("target is not a Git repository",),
        verification_status="not_run",
    )
    redevelop_advice = brief.recommend_continue_rescue(structurally_risky)
    assert redevelop_advice.action == "re-develop"
    assert "advisory" in redevelop_advice.limitation
