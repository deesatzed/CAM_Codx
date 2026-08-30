"""Tests for handoff-first WIP inspection and bounded need themes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "opportunity_brief.py"

HANDOFF_TEXT = """# Current handoff

## Blockers

- [P1] The current evidence replay cannot prove artifact continuity.
- [P0] Verification receipts do not bind the environment identity.

## Risks / Unknowns

- [P0] Observed outputs may be mistaken for confirmed scientific results.
- [P1] Capability claims can drift beyond checked evidence.
- [p1]   capability claims can drift beyond checked evidence.

## Next Actions

- [P2] Establish an auditable evidence boundary for future verification.

## Open Questions

- [P1] Which evidence is sufficient to replay a prior run?

## Completed

- [P0] This completed item must not become a need theme.
"""

NOISE_DIRECTORIES = (
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".benchmarks",
    "node_modules",
    "vendor",
    "dependencies",
    "build",
    "dist",
    "generated_candidates",
    "generated_evidence",
    "hidden_evaluators",
    "run_artifacts",
)


def load_module():
    assert MODULE_PATH.is_file(), "Opportunity Brief module is missing"
    spec = importlib.util.spec_from_file_location("opportunity_brief", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def make_wip_repository(tmp_path: Path) -> Path:
    target = tmp_path / "target-repo"
    target.mkdir()
    (target / "HANDOFF_LATEST.md").write_text(HANDOFF_TEXT, encoding="utf-8")
    (target / "HANDOFF_2026-08-01.md").write_text(
        "## Blockers\n\n- [P0] STALE_HANDOFF_ONLY must not be selected.\n",
        encoding="utf-8",
    )
    (target / "GOAL.md").write_text("# Goal\n\nPreserve inspectable evidence.\n", encoding="utf-8")
    (target / "PROGRESS.md").write_text("# Progress\n\nWork is active.\n", encoding="utf-8")
    source = target / "src" / "worker.py"
    source.parent.mkdir()
    source.write_text("def run() -> None:\n    return None\n", encoding="utf-8")

    subprocess.run(["git", "init", "-q", "-b", "main", str(target)], check=True)
    subprocess.run(["git", "-C", str(target), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(target),
            "-c",
            "user.name=Opportunity Brief Test",
            "-c",
            "user.email=opportunity-brief@example.invalid",
            "commit",
            "-qm",
            "initial WIP evidence",
        ],
        check=True,
    )

    source.write_text(
        "def run() -> None:\n    # TODO: bind replay evidence\n    raise NotImplementedError\n",
        encoding="utf-8",
    )
    (target / "analysis_notes.md").write_text(
        "# Analysis\n\nTODO: reconcile the live implementation.\n",
        encoding="utf-8",
    )
    for directory in NOISE_DIRECTORIES:
        noise = target / directory / "noise.py"
        noise.parent.mkdir(parents=True, exist_ok=True)
        noise.write_text("# TODO: generated noise\n", encoding="utf-8")
    return target


def test_reader_prefers_latest_handoff_and_ignores_generated_noise(
    tmp_path: Path,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    before = {
        path.relative_to(target): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    }

    snapshot = brief.inspect_wip_repository(target)

    assert snapshot.target_path == target.resolve()
    assert snapshot.target_revision == git_output(target, "rev-parse", "HEAD")
    assert snapshot.target_repo_id == "local:target-repo"
    assert snapshot.branch == "main"
    assert snapshot.handoff.relative_path == "HANDOFF_LATEST.md"
    assert snapshot.handoff.sha256 == sha256_path(target / "HANDOFF_LATEST.md")
    assert snapshot.handoff.text == HANDOFF_TEXT
    assert snapshot.truth_files == ("GOAL.md", "PROGRESS.md")
    assert any("analysis_notes.md" in item for item in snapshot.dirty_entries)
    assert any("src/worker.py" in item for item in snapshot.dirty_entries)
    assert any("src/worker.py" in item for item in snapshot.visible_gaps)
    assert not any(
        directory in item
        for item in (*snapshot.dirty_entries, *snapshot.visible_gaps)
        for directory in NOISE_DIRECTORIES
    )
    assert snapshot.verification_status == "not_run"
    after = {
        path.relative_to(target): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_reader_prefers_newest_dated_handoff_then_truth_files(tmp_path: Path) -> None:
    brief = load_module()
    target = tmp_path / "dated"
    target.mkdir()
    older = target / "HANDOFF_2026-08-01.md"
    newer = target / "HANDOFF_2026-08-28.md"
    older.write_text("## Blockers\n- Older blocker.\n", encoding="utf-8")
    newer.write_text("## Blockers\n- Newer blocker.\n", encoding="utf-8")
    (target / "GOAL.md").write_text("## Blockers\n- Truth blocker.\n", encoding="utf-8")

    dated = brief.inspect_wip_repository(target)
    assert dated.handoff.relative_path == newer.name

    older.unlink()
    newer.unlink()
    truth_only = brief.inspect_wip_repository(target)
    assert truth_only.handoff.relative_path == "GOAL.md"
    assert truth_only.truth_files == ("GOAL.md",)


def test_reader_records_handoff_branch_and_revision_conflicts(tmp_path: Path) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    (target / "HANDOFF_LATEST.md").write_text(
        "Branch: archived-work\nRevision: deadbeef\n\n" + HANDOFF_TEXT,
        encoding="utf-8",
    )

    snapshot = brief.inspect_wip_repository(target)

    assert len(snapshot.conflicts) == 2
    assert any("branch" in conflict and "archived-work" in conflict for conflict in snapshot.conflicts)
    assert any("revision" in conflict and "deadbeef" in conflict for conflict in snapshot.conflicts)


def test_need_extraction_is_bounded_source_linked_and_not_an_implementation_plan(
    tmp_path: Path,
) -> None:
    brief = load_module()
    snapshot = brief.inspect_wip_repository(make_wip_repository(tmp_path))

    needs = brief.extract_need_themes(snapshot, minimum=3, maximum=7)

    assert 3 <= len(needs) <= 7
    assert [need.category for need in needs[:2]] == ["blocker", "risk"]
    assert all("[P0]" in need.handoff_span for need in needs[:2])
    assert any("evidence" in need.query_text.lower() for need in needs)
    assert all(need.handoff_span and need.handoff_span in snapshot.handoff.text for need in needs)
    assert all(need.problem and need.desired_improvement for need in needs)
    assert all(need.existing_evidence and need.gap for need in needs)
    assert all(not need.implementation_steps for need in needs)
    assert len({need.need_id for need in needs}) == len(needs)
    assert not any("STALE_HANDOFF_ONLY" in need.handoff_span for need in needs)
    assert sum("capability claims" in need.problem.casefold() for need in needs) == 1


def test_generic_section_parser_supports_allowed_heading_forms_only(tmp_path: Path) -> None:
    brief = load_module()
    target = tmp_path / "generic"
    target.mkdir()
    handoff_text = """# Handoff

Blockers:
- [P1] Preserve a bounded local receipt.

## Unknowns
- [P0] Whether the receipt survives a restart is unknown.

### Next Actions
1. [P2] Define the desired evidence boundary.

OPEN QUESTIONS:
* [P1] Which verification result is authoritative?

## Completed
- [P0] Ignore this historical implementation task.
"""
    (target / "HANDOFF_LATEST.md").write_text(handoff_text, encoding="utf-8")
    snapshot = brief.inspect_wip_repository(target)

    needs = brief.extract_need_themes(snapshot)

    assert {need.category for need in needs} == {
        "blocker",
        "risk",
        "next_action",
        "open_question",
    }
    assert not any("historical implementation" in need.problem for need in needs)


def test_need_extraction_deduplicates_normalized_spans_and_honors_cap(
    tmp_path: Path,
) -> None:
    brief = load_module()
    target = tmp_path / "bounded"
    target.mkdir()
    bullets = "\n".join(f"- [P1] Unique bounded gap {index}." for index in range(10))
    (target / "HANDOFF_LATEST.md").write_text(
        "## Blockers\n- [P0] Duplicate gap.\n"
        "- [p0]   duplicate GAP.\n"
        f"{bullets}\n",
        encoding="utf-8",
    )
    snapshot = brief.inspect_wip_repository(target)

    needs = brief.extract_need_themes(snapshot, minimum=3, maximum=3)

    assert len(needs) == 3
    assert sum("duplicate gap" in need.problem.casefold() for need in needs) == 1


def test_need_extraction_fails_closed_when_bounds_or_sources_are_insufficient(
    tmp_path: Path,
) -> None:
    brief = load_module()
    target = tmp_path / "insufficient"
    target.mkdir()
    (target / "HANDOFF_LATEST.md").write_text(
        "## Blockers\n- Only one bounded need.\n",
        encoding="utf-8",
    )
    snapshot = brief.inspect_wip_repository(target)

    with pytest.raises(brief.OpportunityBriefError, match="at least 3"):
        brief.extract_need_themes(snapshot)
    for minimum, maximum in ((2, 7), (3, 8), (True, 7), (4, 3)):
        with pytest.raises(brief.OpportunityBriefError, match="bounds"):
            brief.extract_need_themes(snapshot, minimum=minimum, maximum=maximum)


def test_public_types_are_frozen_and_need_steps_are_always_empty(tmp_path: Path) -> None:
    brief = load_module()
    handoff = brief.HandoffEvidence(relative_path="HANDOFF_LATEST.md", sha256="a" * 64, text="x")
    snapshot = brief.WipSnapshot(
        target_path=tmp_path,
        target_revision=None,
        target_repo_id="local:fixture",
        branch=None,
        dirty_entries=(),
        handoff=handoff,
        truth_files=(),
        visible_gaps=(),
        conflicts=(),
        verification_status="not_run",
    )
    need = brief.NeedTheme(
        need_id="need_1234",
        category="blocker",
        problem="A problem.",
        desired_improvement="A desired improvement.",
        existing_evidence="The handoff records the problem.",
        gap="Independent evidence is absent.",
        query_text="problem evidence mechanism",
        handoff_span="A problem.",
    )

    assert need.implementation_steps == ()
    with pytest.raises(FrozenInstanceError):
        snapshot.branch = "other"
    with pytest.raises(FrozenInstanceError):
        need.problem = "changed"


def test_production_parser_contains_no_tabletop_or_donor_vocabulary() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").casefold()

    for forbidden in ("agnomine", "imbora", "genericagent"):
        assert forbidden not in source
