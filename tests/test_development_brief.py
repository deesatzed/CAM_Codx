import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "development_brief.py"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "development_brief_results.json"


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


def _fake_cam_command(tmp_path: Path) -> tuple[Path, Path, Path]:
    fixture = tmp_path / "results.json"
    fixture.write_bytes(FIXTURE_PATH.read_bytes())
    calls = tmp_path / "calls.json"
    command = tmp_path / "cam"
    command.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "import os\n"
        "from pathlib import Path\n"
        "import sys\n"
        "Path(os.environ['BRIEF_CALLS']).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n"
        "payload = json.loads(Path(os.environ['BRIEF_FIXTURE']).read_text(encoding='utf-8'))\n"
        "payload['query'] = sys.argv[2]\n"
        "print(json.dumps(payload))\n",
        encoding="utf-8",
    )
    command.chmod(0o700)
    return command, fixture, calls


def test_primary_query_adapter_uses_explicit_argv_and_validates_fixture_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    brief = _load_contract()
    command, fixture, calls = _fake_cam_command(tmp_path)
    database = tmp_path / "claw.db"
    database.write_text("fixture only", encoding="utf-8")
    monkeypatch.setenv("BRIEF_FIXTURE", str(fixture))
    monkeypatch.setenv("BRIEF_CALLS", str(calls))

    payload = brief.query_primary_corpus_read_only(
        "durable import retry",
        cam_command=command,
        cam_database=database,
        limit=2,
    )

    assert payload["scope"] == "primary_only"
    assert payload["results"][0]["methodology_id"] == "method-python-retry"
    assert json.loads(calls.read_text(encoding="utf-8")) == [
        "brief-query",
        "durable import retry",
        "--db",
        str(database),
        "--limit",
        "2",
        "--json",
    ]
    with pytest.raises(brief.BriefValidationError, match="absolute"):
        brief.query_primary_corpus_read_only(
            "retry", cam_command=Path("cam"), cam_database=database, limit=2
        )


def test_classifier_distinguishes_direct_analogy_and_hypothesis() -> None:
    brief = _load_contract()
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    request = brief.BriefRequest(mode="new", task_text="Build a Python durable import retry flow")

    items = brief.classify_cam_evidence(
        request,
        payload["results"],
        target_language="python",
        analogy_rationales={
            "method-go-transaction": "A durable transition boundary transfers despite the Go source stack."
        },
    )
    hypothesis = brief.new_hypothesis(
        title="Retry state snapshot before every external call",
        why_it_applies="The target needs a new recovery boundary beyond the retrieved patterns.",
        validation_needed="Add a failure-injection test before adoption.",
    )

    assert items[0].evidence_class is brief.EvidenceClass.DIRECT_PRECEDENT
    assert items[0].method_contract is not None
    assert items[0].method_contract.ordered_steps == (
        "read durable state",
        "attempt import",
        "persist completion",
    )
    assert items[0].method_contract.source_revision == "a" * 40
    assert items[1].evidence_class is brief.EvidenceClass.TRANSFERABLE_ANALOGY
    assert "despite the Go" in items[1].why_it_applies
    assert hypothesis.evidence_class is brief.EvidenceClass.NEW_HYPOTHESIS
    assert "validation" in hypothesis.limitation

    rendered = brief.render_markdown(
        brief.DevelopmentBrief(
            request=request,
            target_evidence=(),
            evidence_items=items,
            recommendation="Inspect the recalled method.",
            recommended_next_step=brief.NextStep(kind="inspect", summary="Inspect it."),
            optional_next_steps=(),
            limitations=(),
        )
    )
    assert "#### Method contract" in rendered
    assert "1. read durable state" in rendered
    assert "Source revision: `" + "a" * 40 + "`" in rendered
    assert "hidden_tests" not in rendered
    assert "must not appear" not in rendered


def test_low_evidence_requests_named_scope_without_silently_expanding() -> None:
    brief = _load_contract()

    next_steps = brief.suggest_explicit_expansions(())

    assert len(next_steps) == 1
    assert next_steps[0].kind == "request_named_source_scope"
    assert "name local source folders" in next_steps[0].summary.lower()
    assert "/" not in next_steps[0].summary


def test_module_help_states_the_no_write_primary_scope() -> None:
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    rendered_help = " ".join(result.stdout.split())
    assert "primary CAM knowledge" in rendered_help
    assert "no mutation" in rendered_help


def test_cli_new_mode_renders_to_stdout_without_target_or_database_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    brief = _load_contract()
    command, fixture, calls = _fake_cam_command(tmp_path)
    database = tmp_path / "claw.db"
    database.write_text("fixture only", encoding="utf-8")
    target = tmp_path / "new-target"
    target.mkdir()
    before_target = tuple(sorted(item.relative_to(target) for item in target.rglob("*")))
    before_database = database.read_bytes()
    monkeypatch.setenv("BRIEF_FIXTURE", str(fixture))
    monkeypatch.setenv("BRIEF_CALLS", str(calls))

    exit_code = brief.main(
        [
            "new",
            "--task",
            "Build a Python durable import retry flow",
            "--target-repo",
            str(target),
            "--cam-command",
            str(command),
            "--cam-db",
            str(database),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.startswith("# Development Brief")
    assert "Direct precedent" in output
    assert tuple(sorted(item.relative_to(target) for item in target.rglob("*"))) == before_target
    assert database.read_bytes() == before_database
    assert not (target / "CAM_DEVELOPMENT_BRIEF.md").exists()


def test_cli_continue_rescue_writes_only_an_explicit_named_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    brief = _load_contract()
    command, fixture, calls = _fake_cam_command(tmp_path)
    database = tmp_path / "claw.db"
    database.write_text("fixture only", encoding="utf-8")
    target = tmp_path / "existing-target"
    target.mkdir()
    _git_repository(target)
    output_path = tmp_path / "operator-brief.md"
    monkeypatch.setenv("BRIEF_FIXTURE", str(fixture))
    monkeypatch.setenv("BRIEF_CALLS", str(calls))

    exit_code = brief.main(
        [
            "continue-rescue",
            "--task",
            "Decide the smallest safe next repair",
            "--target-repo",
            str(target),
            "--cam-command",
            str(command),
            "--cam-db",
            str(database),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.is_file()
    assert "## Recommendation" in output_path.read_text(encoding="utf-8")
    assert "re-develop" in output_path.read_text(encoding="utf-8")
    assert "Wrote Development Brief" in capsys.readouterr().out
    assert not list(target.glob("*.md")) == []
    assert not (target / "operator-brief.md").exists()


def test_named_source_roots_must_be_explicit_existing_and_contained(tmp_path: Path) -> None:
    brief = _load_contract()
    approved_parent = tmp_path / "approved"
    allowed = approved_parent / "repo-a"
    outside = tmp_path / "outside"
    allowed.mkdir(parents=True)
    outside.mkdir()

    assert brief.validate_named_source_roots((allowed,), approved_parent) == (allowed.resolve(),)
    with pytest.raises(brief.BriefValidationError, match="approved source parent"):
        brief.validate_named_source_roots((allowed,), tmp_path / "missing-parent")
    with pytest.raises(brief.BriefValidationError, match="below the approved"):
        brief.validate_named_source_roots((outside,), approved_parent)
    with pytest.raises(brief.BriefValidationError, match="not a directory"):
        brief.validate_named_source_roots((approved_parent / "missing",), approved_parent)


def test_stale_ganglion_paths_block_expansion_with_a_relocation_gate(tmp_path: Path) -> None:
    brief = _load_contract()
    approved_parent = tmp_path / "approved"
    source_root = approved_parent / "repo-a"
    source_root.mkdir(parents=True)
    config = tmp_path / "claw.toml"
    config.write_text(
        "[instances]\n"
        "enabled = true\n"
        "[[instances.siblings]]\n"
        "name = 'go'\n"
        "db_path = '/old/workspace/instances/go/claw.db'\n",
        encoding="utf-8",
    )

    expansion = brief.prepare_scan_only_expansion(
        (source_root,),
        approved_source_parent=approved_parent,
        cam_config=config,
    )

    assert expansion.kind == "relocation_gate_not_satisfied"
    assert "relocation gate not satisfied" in expansion.summary.lower()
    assert "old/workspace" in expansion.summary


def test_development_brief_source_never_constructs_broader_cam_commands() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert '"federate"' not in source
    assert '"mine"' not in source
    assert '"preflight"' not in source
    assert '"self-enhance"' not in source
