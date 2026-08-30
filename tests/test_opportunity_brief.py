"""Tests for handoff-first WIP inspection and bounded need themes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import importlib.util
import os
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
    assert snapshot.target_repo_id.startswith("local:target-repo:")
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


def test_git_snapshot_disables_external_execution_and_inherited_git_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    fsmonitor_marker = tmp_path / "fsmonitor-executed"
    trace_marker = tmp_path / "inherited-git-trace"
    monitor = tmp_path / "malicious-fsmonitor.sh"
    monitor.write_text(
        f"#!/bin/sh\nprintf executed > {fsmonitor_marker}\nexit 0\n",
        encoding="utf-8",
    )
    monitor.chmod(0o755)
    subprocess.run(
        ["git", "-C", str(target), "config", "core.fsmonitor", str(monitor)],
        check=True,
    )
    expected_revision = git_output(target, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_TRACE", str(trace_marker))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "attacker.gitconfig"))

    snapshot = brief.inspect_wip_repository(target)

    assert snapshot.target_revision == expected_revision
    assert not fsmonitor_marker.exists()
    assert not trace_marker.exists()


def test_git_snapshot_uses_one_bounded_porcelain_v2_snapshot_at_exact_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    calls: list[tuple[tuple[str, ...], dict[str, str]]] = []
    real_popen = brief.subprocess.Popen

    def recording_popen(arguments, *args, **kwargs):
        calls.append((tuple(arguments), dict(kwargs["env"])))
        return real_popen(arguments, *args, **kwargs)

    monkeypatch.setattr(brief.subprocess, "Popen", recording_popen)
    brief.inspect_wip_repository(target)

    assert len(calls) == 2
    status_arguments, environment = calls[-1]
    assert "--porcelain=v2" in status_arguments
    assert "-z" in status_arguments
    assert "--branch" in status_arguments
    assert "--no-renames" in status_arguments
    assert "core.fsmonitor=false" in status_arguments
    assert "core.hooksPath=/dev/null" in status_arguments
    assert environment["GIT_NO_LAZY_FETCH"] == "1"
    assert not any(name.startswith("GIT_") for name in environment if name not in {
        "GIT_CONFIG_NOSYSTEM",
        "GIT_NO_LAZY_FETCH",
        "GIT_OPTIONAL_LOCKS",
        "GIT_TERMINAL_PROMPT",
    })

    with pytest.raises(brief.OpportunityBriefError, match="worktree root"):
        brief.inspect_wip_repository(target / "src")


def test_evidence_read_rejects_symlink_hardlink_and_path_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    source = tmp_path / "source.md"
    source.write_text(HANDOFF_TEXT, encoding="utf-8")

    symlink_target = tmp_path / "symlink-target"
    symlink_target.mkdir()
    (symlink_target / "HANDOFF_LATEST.md").symlink_to(source)
    with pytest.raises(brief.OpportunityBriefError, match="unsafe|regular"):
        brief.inspect_wip_repository(symlink_target)

    hardlink_target = tmp_path / "hardlink-target"
    hardlink_target.mkdir()
    os.link(source, hardlink_target / "HANDOFF_LATEST.md")
    with pytest.raises(brief.OpportunityBriefError, match="link"):
        brief.inspect_wip_repository(hardlink_target)

    oversized_target = tmp_path / "oversized-target"
    oversized_target.mkdir()
    (oversized_target / "HANDOFF_LATEST.md").write_bytes(b"x" * (brief.MAX_HANDOFF_BYTES + 1))
    with pytest.raises(brief.OpportunityBriefError, match="bounded"):
        brief.inspect_wip_repository(oversized_target)

    race_target = tmp_path / "race-target"
    race_target.mkdir()
    handoff = race_target / "HANDOFF_LATEST.md"
    handoff.write_text(HANDOFF_TEXT, encoding="utf-8")
    original_open = brief.os.open
    replaced = False
    observed_flags = 0

    def replacing_open(path, flags, *args, **kwargs):
        nonlocal observed_flags, replaced
        descriptor = original_open(path, flags, *args, **kwargs)
        if Path(path) == handoff and not replaced:
            observed_flags = flags
            replacement = race_target / "replacement.md"
            replacement.write_text(HANDOFF_TEXT.replace("Current", "Changed"), encoding="utf-8")
            os.replace(replacement, handoff)
            replaced = True
        return descriptor

    monkeypatch.setattr(brief.os, "open", replacing_open)
    with pytest.raises(brief.OpportunityBriefError, match="changed|race"):
        brief.inspect_wip_repository(race_target)
    assert observed_flags & os.O_CLOEXEC
    assert observed_flags & os.O_NOFOLLOW


def test_git_status_paths_are_nul_parsed_and_controls_are_escaped(tmp_path: Path) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    unusual = target / "line\nbreak.py"
    unusual.write_text("# ordinary untracked file\n", encoding="utf-8")

    snapshot = brief.inspect_wip_repository(target)

    matching = [item for item in snapshot.dirty_entries if "line" in item and "break.py" in item]
    assert matching == ["? line\\x0abreak.py"]
    assert "\n" not in matching[0]


def test_markdown_lexer_excludes_fences_comments_and_honors_setext_boundaries(
    tmp_path: Path,
) -> None:
    brief = load_module()
    target = tmp_path / "markdown"
    target.mkdir()
    text = """# Handoff

```markdown
## Blockers
- [P0] Fenced fake blocker.
```

<!--
## Risks
- [P0] Commented fake risk.
-->

Blockers
========
- [P0] Real receipt blocker.

Risks / Unknowns
----------------
- [P1] Real replay uncertainty.

Completed
---------
- [P0] Disallowed historical item.

Open Questions
--------------
- [P2] Which real receipt is sufficient?
"""
    (target / "HANDOFF_LATEST.md").write_text(text, encoding="utf-8")

    needs = brief.extract_need_themes(brief.inspect_wip_repository(target))

    assert [need.problem for need in needs] == [
        "Real receipt blocker.",
        "Real replay uncertainty.",
        "Which real receipt is sufficient?",
    ]


@pytest.mark.parametrize("unsafe", ["\x00", "\x07", "\u202e"])
def test_reader_and_public_evidence_reject_unsafe_text_controls(
    tmp_path: Path,
    unsafe: str,
) -> None:
    brief = load_module()
    target = tmp_path / "unsafe-text"
    target.mkdir()
    text = f"## Blockers\n- Unsafe {unsafe} text.\n"
    (target / "HANDOFF_LATEST.md").write_text(text, encoding="utf-8")

    with pytest.raises(brief.OpportunityBriefError, match="unsafe"):
        brief.inspect_wip_repository(target)
    with pytest.raises((TypeError, ValueError), match="unsafe"):
        brief.HandoffEvidence(relative_path="HANDOFF_LATEST.md", sha256="a" * 64, text=text)


def test_all_inspection_and_parser_caps_fail_closed_instead_of_truncating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    dirty_parent = tmp_path / "dirty"
    dirty_parent.mkdir()
    dirty_target = make_wip_repository(dirty_parent)
    monkeypatch.setattr(brief, "MAX_DIRTY_ENTRIES", 1)
    with pytest.raises(brief.OpportunityBriefError, match="dirty|status"):
        brief.inspect_wip_repository(dirty_target)

    file_target = tmp_path / "files"
    file_target.mkdir()
    (file_target / "HANDOFF_LATEST.md").write_text(HANDOFF_TEXT, encoding="utf-8")
    (file_target / "one.py").write_text("# TODO one\n", encoding="utf-8")
    (file_target / "two.py").write_text("# TODO two\n", encoding="utf-8")
    monkeypatch.setattr(brief, "MAX_DIRTY_ENTRIES", 256)
    monkeypatch.setattr(brief, "MAX_INSPECTED_FILES", 1)
    with pytest.raises(brief.OpportunityBriefError, match="file|bound"):
        brief.inspect_wip_repository(file_target)

    monkeypatch.setattr(brief, "MAX_INSPECTED_FILES", 512)
    nested = file_target / "nested"
    nested.mkdir()
    (nested / "child.py").write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr(brief, "MAX_INSPECTED_DIRECTORIES", 1)
    with pytest.raises(brief.OpportunityBriefError, match="directory|bound"):
        brief.inspect_wip_repository(file_target)

    monkeypatch.setattr(brief, "MAX_INSPECTED_DIRECTORIES", 256)
    monkeypatch.setattr(brief, "MAX_TARGET_ENTRIES", 2)
    with pytest.raises(brief.OpportunityBriefError, match="entry|bound"):
        brief.inspect_wip_repository(file_target)

    monkeypatch.setattr(brief, "MAX_TARGET_ENTRIES", 2_048)
    monkeypatch.setattr(brief, "MAX_SECTION_BULLETS", 3)
    handoff = brief.inspect_wip_repository(file_target).handoff
    assert handoff is not None
    with pytest.raises(brief.OpportunityBriefError, match="bullet|bound"):
        brief.extract_need_themes(
            brief.WipSnapshot(
                target_path=file_target,
                target_revision=None,
                target_repo_id="target-repo-01",
                branch=None,
                dirty_entries=(),
                handoff=brief.HandoffEvidence(
                    relative_path="HANDOFF_LATEST.md",
                    sha256="b" * 64,
                    text="## Blockers\n" + "".join(f"- Need {index}.\n" for index in range(4)),
                ),
                truth_files=(),
                visible_gaps=(),
                conflicts=(),
                verification_status="not_run",
            ),
            maximum=3,
        )


def test_git_subprocess_output_cap_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    for index in range(20):
        (target / f"untracked-{index:02d}-with-a-long-name.py").write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr(brief, "MAX_GIT_STATUS_BYTES", 128, raising=False)

    with pytest.raises(brief.OpportunityBriefError, match="output|status"):
        brief.inspect_wip_repository(target)


def test_public_dataclasses_enforce_recursive_invariants_and_have_no_dict(
    tmp_path: Path,
) -> None:
    brief = load_module()
    handoff = brief.HandoffEvidence(
        relative_path="HANDOFF_LATEST.md",
        sha256="a" * 64,
        text="# Handoff\n",
    )
    snapshot = brief.WipSnapshot(
        target_path=tmp_path,
        target_revision=None,
        target_repo_id="target-repo-01",
        branch=None,
        dirty_entries=("? file.py",),
        handoff=handoff,
        truth_files=("GOAL.md",),
        visible_gaps=(),
        conflicts=(),
        verification_status="not_run",
    )
    need = brief.NeedTheme(
        need_id="need_1234",
        category="blocker",
        problem="Problem.",
        desired_improvement="Improvement.",
        existing_evidence="Evidence.",
        gap="Gap.",
        query_text="query evidence",
        handoff_span="Problem.",
    )

    assert not hasattr(handoff, "__dict__")
    assert not hasattr(snapshot, "__dict__")
    assert not hasattr(need, "__dict__")
    with pytest.raises((TypeError, ValueError)):
        brief.HandoffEvidence(relative_path="../escape.md", sha256="short", text="x")
    with pytest.raises((TypeError, ValueError)):
        brief.WipSnapshot(
            target_path=tmp_path,
            target_revision="not-a-revision",
            target_repo_id="target-repo-01",
            branch=None,
            dirty_entries=["mutable"],
            handoff=handoff,
            truth_files=(),
            visible_gaps=(),
            conflicts=(),
            verification_status="not_run",
        )
    with pytest.raises((TypeError, ValueError)):
        brief.NeedTheme(
            need_id="need_1234",
            category="blocker",
            problem="Problem.",
            desired_improvement="Improvement.",
            existing_evidence="Evidence.",
            gap="Gap.",
            query_text="query evidence",
            handoff_span="Problem.",
            implementation_steps=("mutate",),
        )


def test_target_repo_id_is_explicit_or_collision_resistant_by_default(tmp_path: Path) -> None:
    brief = load_module()
    first = tmp_path / "one" / "target"
    second = tmp_path / "two" / "target"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    for target in (first, second):
        (target / "HANDOFF_LATEST.md").write_text(HANDOFF_TEXT, encoding="utf-8")

    first_id = brief.inspect_wip_repository(first).target_repo_id
    second_id = brief.inspect_wip_repository(second).target_repo_id

    assert first_id.startswith("local:target:")
    assert second_id.startswith("local:target:")
    assert first_id != second_id
    assert brief.inspect_wip_repository(first, target_repo_id="target-repo-01").target_repo_id == (
        "target-repo-01"
    )
    for invalid in (True, "", " padded ", "unsafe\x00id"):
        with pytest.raises((TypeError, ValueError), match="target_repo_id"):
            brief.inspect_wip_repository(first, target_repo_id=invalid)


def test_dated_handoffs_require_iso_dates_and_revision_claims_require_hex_prefix(
    tmp_path: Path,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    (target / "HANDOFF_LATEST.md").unlink()
    (target / "HANDOFF_9999-99-99.md").write_text("invalid date", encoding="utf-8")
    tied = target / "HANDOFF_2026-08-28-z.md"
    tied.write_text("Revision: d\n\n" + HANDOFF_TEXT, encoding="utf-8")
    (target / "HANDOFF_2026-08-28-a.md").write_text("lower tie", encoding="utf-8")

    snapshot = brief.inspect_wip_repository(target)

    assert snapshot.handoff.relative_path == tied.name
    assert not any("revision" in conflict for conflict in snapshot.conflicts)
