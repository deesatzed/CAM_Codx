"""Tests for handoff-first WIP inspection and bounded need themes."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import unicodedata

import pytest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "opportunity_brief.py"
PROJECT_ROOT = MODULE_PATH.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_need_id(category: str, problem: str) -> str:
    normalized = unicodedata.normalize("NFKC", problem).casefold()
    normalized = " ".join(re.sub(r"[^\w]+", " ", normalized).split())
    identity = f"{category}\0{normalized}".encode("utf-8")
    return f"need_{hashlib.sha256(identity).hexdigest()[:24]}"


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
    handoff = brief.HandoffEvidence(
        relative_path="HANDOFF_LATEST.md",
        sha256=sha256_text("x"),
        text="x",
    )
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
        need_id=canonical_need_id("blocker", "A problem."),
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
        is_handoff = Path(path) == handoff or (
            os.fspath(path) == handoff.name and kwargs.get("dir_fd") is not None
        )
        if is_handoff and not replaced:
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
        brief.HandoffEvidence(
            relative_path="HANDOFF_LATEST.md",
            sha256=sha256_text(text),
            text=text,
        )


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
                    sha256=sha256_text(
                        "## Blockers\n" + "".join(f"- Need {index}.\n" for index in range(4))
                    ),
                    text=(
                        "## Blockers\n"
                        + "".join(f"- Need {index}.\n" for index in range(4))
                    ),
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
        sha256=sha256_text("# Handoff\n"),
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
        need_id=canonical_need_id("blocker", "Problem."),
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
            need_id=canonical_need_id("blocker", "Problem."),
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
    derived = brief.inspect_wip_repository(first)
    explicit = brief.inspect_wip_repository(first, target_repo_id="target-repo-01")
    assert not derived.target_repo_id_is_exclusion_authoritative
    assert explicit.target_repo_id == "target-repo-01"
    assert explicit.target_repo_id_is_exclusion_authoritative
    with pytest.raises(brief.OpportunityBriefError, match="explicit.*target_repo_id"):
        brief.inspect_wip_repository(first, require_exclusion_identity=True)
    authoritative = brief.inspect_wip_repository(
        first,
        target_repo_id="target-repo-01",
        require_exclusion_identity=True,
    )
    assert authoritative.target_repo_id_is_exclusion_authoritative
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
    assert any("revision" in conflict and "malformed" in conflict for conflict in snapshot.conflicts)


def test_reader_pins_root_and_recursive_directories_with_nofollow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    calls: list[tuple[object, int, int | None]] = []
    original_open = brief.os.open

    def recording_open(path, flags, *args, **kwargs):
        calls.append((path, flags, kwargs.get("dir_fd")))
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(brief.os, "open", recording_open)
    brief.inspect_wip_repository(target)

    root_calls = [item for item in calls if Path(item[0]) == target and item[1] & os.O_DIRECTORY]
    assert len(root_calls) == 1
    assert root_calls[0][1] & os.O_NOFOLLOW
    assert root_calls[0][1] & os.O_CLOEXEC
    assert any(
        os.fspath(path) == "src"
        and flags & os.O_DIRECTORY
        and flags & os.O_NOFOLLOW
        and directory_fd is not None
        for path, flags, directory_fd in calls
    )
    assert any(
        os.fspath(path) == "HANDOFF_LATEST.md" and directory_fd is not None
        for path, _, directory_fd in calls
    )


def test_reader_rejects_target_root_swap_after_git_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    moved = tmp_path / "moved-original"
    original_snapshot = brief._read_git_snapshot

    def swapping_snapshot(*args, **kwargs):
        snapshot = original_snapshot(*args, **kwargs)
        target.rename(moved)
        target.mkdir()
        (target / "HANDOFF_LATEST.md").write_text("## Blockers\n- Replacement leak.\n", encoding="utf-8")
        (target / "leak.py").write_text("# TODO replacement leak\n", encoding="utf-8")
        return snapshot

    monkeypatch.setattr(brief, "_read_git_snapshot", swapping_snapshot)

    with pytest.raises(brief.OpportunityBriefError, match="target.*changed|root.*identity"):
        brief.inspect_wip_repository(target)


def test_reader_rejects_target_root_rename_away_and_back_during_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    moved = tmp_path / "transient-root"
    original_run = brief._run_git_bounded
    swapped = False

    def swapping_run(*args, **kwargs):
        nonlocal swapped
        result = original_run(*args, **kwargs)
        arguments = args[1]
        if arguments[0] == "rev-parse" and not swapped:
            target.rename(moved)
            moved.rename(target)
            swapped = True
        return result

    monkeypatch.setattr(brief, "_run_git_bounded", swapping_run)
    with pytest.raises(brief.OpportunityBriefError, match="root.*identity|target.*changed"):
        brief.inspect_wip_repository(target)
    assert swapped


def test_reader_rejects_recursive_directory_swap_without_reading_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = tmp_path / "directory-race"
    target.mkdir()
    (target / "HANDOFF_LATEST.md").write_text(HANDOFF_TEXT, encoding="utf-8")
    nested = target / "nested"
    nested.mkdir()
    (nested / "original.py").write_text("# TODO original evidence\n", encoding="utf-8")
    moved = target / "nested-original"
    original_open = brief.os.open
    swapped = False

    def swapping_open(path, flags, *args, **kwargs):
        nonlocal swapped
        descriptor = original_open(path, flags, *args, **kwargs)
        if os.fspath(path) == "nested" and kwargs.get("dir_fd") is not None and not swapped:
            nested.rename(moved)
            nested.mkdir()
            (nested / "leak.py").write_text("# TODO replacement leak\n", encoding="utf-8")
            swapped = True
        return descriptor

    monkeypatch.setattr(brief.os, "open", swapping_open)
    with pytest.raises(brief.OpportunityBriefError, match="directory.*changed|target.*changed"):
        brief.inspect_wip_repository(target)
    assert swapped


def test_reader_rejects_file_replacement_between_stat_and_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    target = tmp_path / "file-race"
    target.mkdir()
    (target / "HANDOFF_LATEST.md").write_text(HANDOFF_TEXT, encoding="utf-8")
    evidence = target / "evidence.py"
    evidence.write_text("# TODO original evidence\n", encoding="utf-8")
    original_open = brief.os.open
    swapped = False

    def swapping_open(path, flags, *args, **kwargs):
        nonlocal swapped
        descriptor = original_open(path, flags, *args, **kwargs)
        if os.fspath(path) == "evidence.py" and kwargs.get("dir_fd") is not None and not swapped:
            replacement = target / "replacement.py"
            replacement.write_text("# TODO replacement leak\n", encoding="utf-8")
            os.replace(replacement, evidence)
            swapped = True
        return descriptor

    monkeypatch.setattr(brief.os, "open", swapping_open)
    with pytest.raises(brief.OpportunityBriefError, match="file.*changed|target.*changed"):
        brief.inspect_wip_repository(target)
    assert swapped


def test_markdown_lexer_excludes_indented_code_and_raw_html_blocks(tmp_path: Path) -> None:
    brief = load_module()
    target = tmp_path / "markdown-examples"
    target.mkdir()
    text = """## Blockers
- [P0] Real blocker.
    - [P0] Four-space example must be ignored.
 \t- [P0] Mixed tab example must be ignored.
<pre class="example">
- [P0] Preformatted example must be ignored.
</pre>
<script>
- [P0] Script example must be ignored.
</script>
<style>
- [P0] Style example must be ignored.
</style>
<textarea>
- [P0] Textarea example must be ignored.
</textarea>

## Risks
- [P1] Real risk.

## Open Questions
- [P2] Real question?
"""
    (target / "HANDOFF_LATEST.md").write_text(text, encoding="utf-8")

    needs = brief.extract_need_themes(brief.inspect_wip_repository(target))

    assert [need.problem for need in needs] == ["Real blocker.", "Real risk.", "Real question?"]


def test_public_evidence_and_need_identity_are_content_bound() -> None:
    brief = load_module()
    with pytest.raises(ValueError, match="sha256.*text|digest.*text"):
        brief.HandoffEvidence(
            relative_path="HANDOFF_LATEST.md",
            sha256=sha256_text("different"),
            text="actual",
        )
    with pytest.raises(ValueError, match="need_id.*problem|canonical"):
        brief.NeedTheme(
            need_id=canonical_need_id("blocker", "Different problem."),
            category="blocker",
            problem="Actual problem.",
            desired_improvement="Improvement.",
            existing_evidence="Evidence.",
            gap="Gap.",
            query_text="query evidence",
            handoff_span="Actual problem.",
        )
    punctuation = "..."
    with pytest.raises(ValueError, match="problem.*canonical|normalized problem"):
        brief.NeedTheme(
            need_id=canonical_need_id("blocker", punctuation),
            category="blocker",
            problem=punctuation,
            desired_improvement="Improvement.",
            existing_evidence="Evidence.",
            gap="Gap.",
            query_text="query evidence",
            handoff_span=punctuation,
        )


def test_target_and_visible_gap_paths_reject_or_escape_controls(tmp_path: Path) -> None:
    brief = load_module()
    for suffix in ("bad\npath", "bad\tpath", "bad\u202epath"):
        unsafe_target = tmp_path / suffix
        unsafe_target.mkdir()
        with pytest.raises(brief.OpportunityBriefError, match="target path.*unsafe"):
            brief.inspect_wip_repository(unsafe_target)
    with pytest.raises(brief.OpportunityBriefError, match="target path.*unsafe"):
        brief.inspect_wip_repository(Path(f"{tmp_path}\x00invalid"))

    target = tmp_path / "escaped-gap"
    target.mkdir()
    (target / "HANDOFF_LATEST.md").write_text(HANDOFF_TEXT, encoding="utf-8")
    (target / "gap\nname.py").write_text("# TODO escaped path\n", encoding="utf-8")
    snapshot = brief.inspect_wip_repository(target)
    assert any(item.startswith("gap\\x0aname.py:1:") for item in snapshot.visible_gaps)
    assert not any("\n" in item for item in snapshot.visible_gaps)

    with pytest.raises(ValueError, match="unsafe"):
        brief.HandoffEvidence(
            relative_path="bad\nname.md",
            sha256=sha256_text("text"),
            text="text",
        )


def test_valid_revision_claim_without_live_git_revision_is_not_malformed(tmp_path: Path) -> None:
    brief = load_module()
    target = tmp_path / "non-git-revision"
    target.mkdir()
    text = "Revision: deadbeef\n\n" + HANDOFF_TEXT
    (target / "HANDOFF_LATEST.md").write_text(text, encoding="utf-8")

    snapshot = brief.inspect_wip_repository(target)

    assert not any("malformed" in conflict for conflict in snapshot.conflicts)


def test_need_parser_accepts_only_direct_section_list_children(tmp_path: Path) -> None:
    brief = load_module()
    target = tmp_path / "direct-needs"
    target.mkdir()
    text = """## Blockers
- [P0] Direct blocker.
 - [P0] One-space implementation step must be ignored.
  - [P0] Two-space implementation step must be ignored.
   1. [P0] Three-space implementation step must be ignored.

## Risks
- [P1] Direct risk.

## Open Questions
- [P2] Direct question?
"""
    (target / "HANDOFF_LATEST.md").write_text(text, encoding="utf-8")

    needs = brief.extract_need_themes(brief.inspect_wip_repository(target))

    assert [need.problem for need in needs] == ["Direct blocker.", "Direct risk.", "Direct question?"]


def test_markdown_lexer_masks_all_commonmark_html_block_families(tmp_path: Path) -> None:
    brief = load_module()
    target = tmp_path / "html-blocks"
    target.mkdir()
    text = """## Blockers
- [P0] Direct blocker.
<div class="example">
- [P0] Div example must be ignored.
</div>

<details>
- [P0] Details example must be ignored.
</details>

<table>
- [P0] Table example must be ignored.
</table>

<blockquote>
- [P0] Quote example must be ignored.
</blockquote>

<?example
- [P0] Processing example must be ignored.
?>

<!DOCTYPE
- [P0] Declaration example must be ignored.
>

<![CDATA[
- [P0] CDATA example must be ignored.
]]>

<custom-element data-example="true">
- [P0] Generic HTML example must be ignored.
</custom-element>

## Risks
- [P1] Direct risk.

## Open Questions
- [P2] Direct question?
"""
    (target / "HANDOFF_LATEST.md").write_text(text, encoding="utf-8")

    needs = brief.extract_need_themes(brief.inspect_wip_repository(target))

    assert [need.problem for need in needs] == ["Direct blocker.", "Direct risk.", "Direct question?"]


def test_checkout_claim_labels_record_all_malformed_values(tmp_path: Path) -> None:
    brief = load_module()
    target = make_wip_repository(tmp_path)
    malformed = (
        "Revision:",
        "Head: deadbeef annotated",
        "Commit: `deadbeef",
        "Revision: deadbeef`",
        "Commit: `dead beef`",
        "Branch:",
        "Branch: feature branch",
        "Branch: `feature/x` annotated",
    )
    valid_mismatches = (
        "Head: `deadbeef`",
        "Branch: `archived-work`",
    )
    text = "\n".join((*malformed, *valid_mismatches)) + "\n\n" + HANDOFF_TEXT
    (target / "HANDOFF_LATEST.md").write_text(text, encoding="utf-8")

    snapshot = brief.inspect_wip_repository(target)

    malformed_conflicts = [item for item in snapshot.conflicts if "malformed" in item]
    assert len(malformed_conflicts) == len(malformed)
    assert all(any(label.casefold() in item.casefold() for item in malformed_conflicts) for label in (
        "revision",
        "head",
        "commit",
        "branch",
    ))
    assert any("deadbeef" in item and "live revision" in item for item in snapshot.conflicts)
    assert any("archived-work" in item and "live branch" in item for item in snapshot.conflicts)


def test_public_snapshot_truth_and_conflict_cardinality_are_bounded(tmp_path: Path) -> None:
    brief = load_module()
    common = {
        "target_path": tmp_path,
        "target_revision": None,
        "target_repo_id": "target-repo-01",
        "branch": None,
        "dirty_entries": (),
        "handoff": None,
        "visible_gaps": (),
        "verification_status": "not_run",
    }
    with pytest.raises(ValueError, match="truth_files.*bound"):
        brief.WipSnapshot(
            **common,
            truth_files=tuple(f"TRUTH_{index}.md" for index in range(8)),
            conflicts=(),
        )
    with pytest.raises(ValueError, match="conflicts.*bound"):
        brief.WipSnapshot(
            **common,
            truth_files=(),
            conflicts=tuple(f"conflict {index}" for index in range(65)),
        )


def make_need(brief, problem: str, query: str, *, category: str = "blocker"):
    return brief.NeedTheme(
        need_id=canonical_need_id(category, problem),
        category=category,
        problem=problem,
        desired_improvement="Attach a transferable evidence mechanism.",
        existing_evidence="The handoff records the unresolved need.",
        gap="Independent source evidence is absent.",
        query_text=query,
        handoff_span=problem,
    )


def make_record_mapping(*, source_repo_id: str = "donor-repo-01") -> dict[str, object]:
    return {
        "problem": "Evidence receipts do not survive relocation.",
        "mechanism": "Bind append-only receipts to content digests.",
        "observed_effect": {
            "status": "observed",
            "text": "Relocated receipts retained a verifiable chain.",
        },
        "context": (
            "A local verification runner uses append-only content digests "
            "with disposable worktrees."
        ),
        "boundary": "This does not establish scientific correctness.",
        "evidence": {
            "source_repo_id": source_repo_id,
            "source_repo_name": "donor",
            "source_revision": "a" * 40,
            "source_revision_role": "historical_mined",
            "license_type": "MIT",
            "license_sha256": "b" * 64,
            "source_files": ["src/receipt.py"],
            "source_symbols": ["ReceiptChain"],
            "source_sha256": ["c" * 64],
        },
        "evidence_state": "admitted",
        "source_methodology_ids": ["method-receipt-chain"],
    }


def record_id_for(mapping: dict[str, object]) -> str:
    canonical = json.dumps(
        mapping,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"opp_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]}"


def make_ranking_acquisition(brief, tmp_path: Path, needs, candidates):
    identity = (1, 2, 1, 10, 3, 4)
    digest = "a" * 64
    command = (tmp_path / "cam").absolute()
    sidecar = (tmp_path / "opportunities.sqlite").absolute()
    model = (tmp_path / "model").absolute()
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


def render_record_mapping(brief, ranker, tmp_path: Path, mapping: dict[str, object]) -> str:
    problem = "Evidence receipts do not survive relocation."
    need = make_need(brief, problem, "evidence receipt relocation verification")
    record = brief._parse_opportunity_record(
        mapping,
        target_repo_id="target-repo-01",
    )
    candidate = brief.OpportunityCandidate(
        record_id=record_id_for(mapping),
        record=record,
        matches=(
            brief.CandidateMatch(
                need_id=need.need_id,
                fts_rank=1,
                semantic_rank=1,
                rrf_score=2 / 61,
            ),
        ),
    )
    acquired = make_ranking_acquisition(
        brief,
        tmp_path,
        (need,),
        (candidate,),
    )
    handoff_text = f"## Blockers\n\n- {problem}\n"
    ranking = ranker.rank_and_select(
        needs=(need,),
        handoff_text=handoff_text,
        acquired=acquired,
    )
    assert ranking.selected, "renderer fixture must meet the frozen threshold"
    snapshot = brief.WipSnapshot(
        target_path=tmp_path.absolute(),
        target_revision="d" * 40,
        target_repo_id="target-repo-01",
        target_repo_id_is_exclusion_authoritative=True,
        branch="feature/evidence",
        dirty_entries=(),
        handoff=brief.HandoffEvidence(
            relative_path="HANDOFF_LATEST.md",
            sha256=hashlib.sha256(handoff_text.encode()).hexdigest(),
            text=handoff_text,
        ),
        truth_files=(),
        visible_gaps=(),
        conflicts=(),
        verification_status="not_run",
    )
    return brief.render_opportunity_brief(snapshot, ranking)


def make_query_payload(
    query: str,
    *,
    target_repo_id: str,
    model_id: str,
    record: dict[str, object] | None = None,
) -> dict[str, object]:
    results: list[dict[str, object]] = []
    if record is not None:
        results.append(
            {
                "record_id": record_id_for(record),
                "record": record,
                "fts_rank": 1,
                "semantic_rank": 1,
                "rrf_score": 2 / 61,
            }
        )
    return {
        "schema_version": 1,
        "scope": "opportunity_sidecar",
        "query": query,
        "target_repo_id": target_repo_id,
        "model_id": model_id,
        "results": results,
        "rejections": [],
    }


def make_fake_cam(
    tmp_path: Path,
    responses: dict[str, object],
    *,
    interpreter: Path | None = None,
    implementation_root: Path | None = None,
) -> tuple[Path, Path]:
    log_path = tmp_path / "fake-cam-calls.jsonl"
    executable = tmp_path / "fake-cam"
    encoded_responses = json.dumps(responses, sort_keys=True)
    shebang = interpreter if interpreter is not None else Path(sys.executable)
    implementation_marker = (
        ""
        if implementation_root is None
        else f"# cam-implementation-root: {implementation_root}\n"
    )
    executable.write_text(
        f"#!{shebang}\n"
        f"{implementation_marker}"
        "import json\n"
        "import os\n"
        "import pathlib\n"
        "import signal\n"
        "import subprocess\n"
        "import sys\n"
        "import time\n"
        f"responses = json.loads({encoded_responses!r})\n"
        f"log_path = pathlib.Path({str(log_path)!r})\n"
        "with log_path.open('a', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:], sort_keys=True) + '\\n')\n"
        "entry = responses[sys.argv[2]]\n"
        "if isinstance(entry, dict) and 'sleep_seconds' in entry:\n"
        "    time.sleep(entry['sleep_seconds'])\n"
        "if isinstance(entry, dict) and 'mutate_path' in entry:\n"
        "    pathlib.Path(entry['mutate_path']).write_bytes(b'mutated')\n"
        "if isinstance(entry, dict) and 'background_marker' in entry:\n"
        "    code = ('import pathlib,time; time.sleep(%r); ' "
        "            'pathlib.Path(%r).write_text(\"survived\", encoding=\"utf-8\")' "
        "            % (entry.get('background_seconds', 0.5), "
        "               entry['background_marker']))\n"
        "    subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.DEVNULL, "
        "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        "if isinstance(entry, dict) and 'signal_number' in entry:\n"
        "    os.kill(os.getpid(), entry['signal_number'])\n"
        "if isinstance(entry, dict) and 'raw_stdout' in entry:\n"
        "    sys.stdout.write(entry['raw_stdout'])\n"
        "    raise SystemExit(entry.get('exit_code', 0))\n"
        "if isinstance(entry, dict) and 'exit_code' in entry:\n"
        "    if 'stdout' in entry:\n"
        "        sys.stdout.write(entry['stdout'])\n"
        "    sys.stderr.write(entry.get('stderr', ''))\n"
        "    raise SystemExit(entry['exit_code'])\n"
        "payload = entry.get('payload', entry) if isinstance(entry, dict) else entry\n"
        "sys.stdout.write(json.dumps(payload, sort_keys=True))\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable, log_path


def make_editable_venv_cam(
    tmp_path: Path,
    responses: dict[str, object],
    *,
    terminal_interpreter: Path,
) -> tuple[Path, Path, Path]:
    implementation = tmp_path / "cam-source"
    package = implementation / "src" / "claw"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        "FIXTURE_IDENTITY = 'editable-cam-source'\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", "-b", "main", str(implementation)], check=True)
    subprocess.run(["git", "-C", str(implementation), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(implementation),
            "-c",
            "user.name=Opportunity Brief Test",
            "-c",
            "user.email=opportunity-brief@example.invalid",
            "commit",
            "-qm",
            "fixture editable CAM source",
        ],
        check=True,
    )

    venv = tmp_path / "production-venv"
    bin_directory = venv / "bin"
    site_packages = venv / "lib" / "python3.9" / "site-packages"
    bin_directory.mkdir(parents=True)
    site_packages.mkdir(parents=True)
    lexical_interpreter = bin_directory / "python"
    lexical_interpreter.symlink_to(terminal_interpreter)
    finder_name = "__editable___claw_1_0_0_finder"
    (site_packages / f"{finder_name}.py").write_text(
        f"MAPPING = {{'claw': {str(package)!r}}}\n"
        "def install():\n"
        "    return None\n",
        encoding="utf-8",
    )
    (site_packages / "__editable__.claw-1.0.0.pth").write_text(
        f"import {finder_name}; {finder_name}.install()\n",
        encoding="utf-8",
    )
    distribution = site_packages / "claw-1.0.0.dist-info"
    distribution.mkdir()
    (distribution / "direct_url.json").write_text(
        json.dumps(
            {
                "url": implementation.as_uri(),
                "dir_info": {"editable": True},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (distribution / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: claw\nVersion: 1.0.0\n",
        encoding="utf-8",
    )

    log_path = tmp_path / "editable-cam-calls.jsonl"
    launcher = bin_directory / "cam"
    launcher.write_text(
        f"#!{lexical_interpreter}\n"
        "import claw\n"
        "import json\n"
        "import pathlib\n"
        "import sys\n"
        f"responses = json.loads({json.dumps(responses, sort_keys=True)!r})\n"
        f"log_path = pathlib.Path({str(log_path)!r})\n"
        "assert claw.FIXTURE_IDENTITY == 'editable-cam-source'\n"
        "assert sys.flags.no_site == 1\n"
        "with log_path.open('a', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:], sort_keys=True) + '\\n')\n"
        "sys.stdout.write(json.dumps(responses[sys.argv[2]], sort_keys=True))\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    return launcher, implementation, log_path


def test_acquisition_calls_once_per_unique_need_with_exact_offline_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    evidence_need = make_need(brief, "Receipt continuity is missing.", "receipt continuity")
    environment_need = make_need(
        brief,
        "Environment identity is missing.",
        "environment identity",
        category="risk",
    )
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"sidecar fixture is never opened by the fake")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    target_repo_id = "target-repo-01"
    record = make_record_mapping()
    responses = {
        evidence_need.query_text: make_query_payload(
            evidence_need.query_text,
            target_repo_id=target_repo_id,
            model_id=str(model_path.resolve()),
            record=record,
        ),
        environment_need.query_text: make_query_payload(
            environment_need.query_text,
            target_repo_id=target_repo_id,
            model_id=str(model_path.resolve()),
            record=record,
        ),
    }
    fake_cam, log_path = make_fake_cam(tmp_path, responses)
    popen_calls: list[tuple[tuple[str, ...], dict[str, object]]] = []
    real_popen = brief.subprocess.Popen

    def recording_popen(arguments, *args, **kwargs):
        popen_calls.append((tuple(arguments), dict(kwargs)))
        return real_popen(arguments, *args, **kwargs)

    monkeypatch.setenv("OPENAI_API_KEY", "private-provider-key")
    monkeypatch.setenv("GIT_TRACE", str(tmp_path / "must-not-be-used"))
    monkeypatch.setattr(brief.subprocess, "Popen", recording_popen)

    receipt = brief.acquire_opportunities(
        needs=(evidence_need, evidence_need, environment_need),
        cam_command=fake_cam,
        sidecar=sidecar,
        semantic_model_path=model_path,
        target_repo_id=target_repo_id,
    )

    assert [call.need_id for call in receipt.calls] == [
        evidence_need.need_id,
        environment_need.need_id,
    ]
    logged = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert logged == [
        [
            "opportunity-query",
            need.query_text,
            "--db",
            str(sidecar),
            "--target-repo-id",
            target_repo_id,
            "--semantic-model-path",
            str(model_path),
            "--limit",
            "20",
            "--json",
        ]
        for need in (evidence_need, environment_need)
    ]
    assert all(call[1]["shell"] is False for call in popen_calls)
    assert all("OPENAI_API_KEY" not in call[1]["env"] for call in popen_calls)
    assert all("GIT_TRACE" not in call[1]["env"] for call in popen_calls)
    assert receipt.provider_calls == 0
    assert receipt.mining_calls == 0
    assert len(receipt.candidates) == 1
    assert [match.need_id for match in receipt.candidates[0].matches] == [
        evidence_need.need_id,
        environment_need.need_id,
    ]
    assert receipt.gaps == ()


def test_acquisition_preserves_empty_results_and_audits_nonzero_query_failure(
    tmp_path: Path,
) -> None:
    brief = load_module()
    empty_need = make_need(brief, "No relevant source may exist.", "empty query")
    failed_need = make_need(
        brief,
        "A bounded query may fail.",
        "failed query",
        category="risk",
    )
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    target_repo_id = "target-repo-01"
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            empty_need.query_text: make_query_payload(
                empty_need.query_text,
                target_repo_id=target_repo_id,
                model_id=str(model_path.resolve()),
            ),
            failed_need.query_text: {
                "exit_code": 2,
                "stderr": "",
                "stdout": json.dumps(
                    {
                        "status": "error",
                        "error": "opportunity query backend failed",
                    },
                    sort_keys=True,
                ),
            },
        },
    )

    receipt = brief.acquire_opportunities(
        needs=(empty_need, failed_need),
        cam_command=fake_cam,
        sidecar=sidecar,
        semantic_model_path=model_path,
        target_repo_id=target_repo_id,
    )

    assert receipt.candidates == ()
    assert [call.status for call in receipt.calls] == ["ok", "query_failed"]
    assert receipt.calls[0].result_count == 0
    assert receipt.gaps == (
        brief.AcquisitionGap(
            need_id=failed_need.need_id,
            reason="query_failed",
        ),
    )
    assert "SECRET_BACKEND_DETAIL_9137" not in repr(receipt)


@pytest.mark.parametrize(
    ("mutation", "error_match"),
    (
        (lambda payload: payload.update(schema_version=2), "schema"),
        (lambda payload: payload.update(scope="canonical_database"), "scope"),
        (lambda payload: payload.update(query="different query"), "query"),
        (lambda payload: payload.update(target_repo_id="another-target"), "target"),
        (lambda payload: payload.update(model_id="another-model"), "model"),
        (lambda payload: payload["results"][0].update(fts_rank=True), "rank"),
        (lambda payload: payload["results"][0].update(rrf_score=0.5), "rank|RRF"),
        (lambda payload: payload["results"][0]["record"].pop("boundary"), "record"),
        (
            lambda payload: payload["results"][0]["record"]["observed_effect"].update(
                status="claimed"
            ),
            "record",
        ),
        (
            lambda payload: payload["results"][0]["record"]["evidence"].update(
                license_type="Unknown-License"
            ),
            "record",
        ),
        (
            lambda payload: payload["results"][0]["record"].update(
                evidence_state="exploratory"
            ),
            "record",
        ),
        (
            lambda payload: payload["results"][0]["record"].update(
                source_methodology_ids=[]
            ),
            "record",
        ),
        (
            lambda payload: payload["results"][0]["record"]["evidence"].update(
                source_repo_id="target-repo-01"
            ),
            "target|source",
        ),
        (lambda payload: payload.update(rejections=[{"record_id": "bad"}]), "rejection"),
    ),
)
def test_acquisition_fails_closed_on_corrupt_or_mismatched_query_response(
    tmp_path: Path,
    mutation,
    error_match: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Receipt validation is incomplete.", "validate receipt")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    target_repo_id = "target-repo-01"
    payload = make_query_payload(
        need.query_text,
        target_repo_id=target_repo_id,
        model_id=str(model_path.resolve()),
        record=make_record_mapping(),
    )
    mutation(payload)
    fake_cam, _log = make_fake_cam(tmp_path, {need.query_text: payload})

    with pytest.raises(brief.OpportunityBriefError, match=error_match):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id=target_repo_id,
        )


def test_acquisition_bounds_output_sanitizes_errors_and_requires_explicit_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Bound query output.", "bounded output")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    (target / "HANDOFF_LATEST.md").write_text(HANDOFF_TEXT, encoding="utf-8")
    with pytest.raises(brief.OpportunityBriefError, match="explicit.*target_repo_id"):
        brief.inspect_wip_repository(target, require_exclusion_identity=True)
    authoritative = brief.inspect_wip_repository(
        target,
        target_repo_id="target-repo-01",
        require_exclusion_identity=True,
    )
    payload = make_query_payload(
        need.query_text,
        target_repo_id=authoritative.target_repo_id,
        model_id=str(model_path.resolve()),
    )
    payload["padding"] = "private" * 100
    fake_cam, _log = make_fake_cam(tmp_path, {need.query_text: payload})
    monkeypatch.setattr(brief, "MAX_QUERY_RESPONSE_BYTES", 64)

    with pytest.raises(brief.OpportunityBriefError, match="output.*bound") as captured:
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id=authoritative.target_repo_id,
        )
    assert "private" not in str(captured.value)


def test_acquisition_rejects_canonical_database_name_before_spawning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Never query canonical state.", "canonical state")
    canonical = tmp_path / "claw.db"
    canonical.write_bytes(b"must remain untouched")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    fake_cam, _log = make_fake_cam(tmp_path, {})

    def forbidden_popen(*_args, **_kwargs):
        raise AssertionError("canonical rejection must happen before process creation")

    monkeypatch.setattr(brief.subprocess, "Popen", forbidden_popen)
    with pytest.raises(brief.OpportunityBriefError, match="canonical|claw.db"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=canonical,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )
    assert canonical.read_bytes() == b"must remain untouched"


def test_public_acquisition_receipts_reject_forged_call_and_relation_shapes(
    tmp_path: Path,
) -> None:
    brief = load_module()
    need_id = canonical_need_id("blocker", "Bound invocation shape.")
    identity = (1, 2, 1, 10, 3, 4)
    digest = "a" * 64
    binding = {
        "executable_identity": identity,
        "executable_sha256": digest,
        "sidecar_identity": identity,
        "sidecar_sha256": digest,
        "semantic_model_identity": identity,
        "semantic_model_sha256": digest,
        "execution_closure_sha256": digest,
    }
    with pytest.raises((TypeError, ValueError), match="argv|invocation"):
        brief.AcquisitionCall(
            need_id=need_id,
            query="bounded query",
            argv=("/absolute/fake", "mine"),
            status="ok",
            result_count=0,
            rejection_count=0,
            **binding,
        )
    forged_call = object.__new__(brief.AcquisitionCall)
    object.__setattr__(forged_call, "need_id", need_id)
    object.__setattr__(forged_call, "query", "bounded query")
    object.__setattr__(forged_call, "argv", ("/absolute/fake", "mine"))
    object.__setattr__(forged_call, "status", "ok")
    object.__setattr__(forged_call, "result_count", 0)
    object.__setattr__(forged_call, "rejection_count", 0)
    for field, value in binding.items():
        object.__setattr__(forged_call, field, value)
    with pytest.raises((TypeError, ValueError), match="call|argv|invocation"):
        brief.AcquisitionReceipt(
            target_repo_id="target-repo-01",
            model_id=str(tmp_path / "model"),
            cam_command=tmp_path / "fake",
            executable_identity=identity,
            executable_sha256=digest,
            sidecar=tmp_path / "sidecar.sqlite",
            sidecar_identity=identity,
            sidecar_sha256=digest,
            semantic_model_path=tmp_path / "model",
            semantic_model_identity=identity,
            semantic_model_sha256=digest,
            execution_closure=brief.ExecutionClosureReceipt(
                launcher_kind="native",
                launcher_path=tmp_path / "fake",
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
            ),
            calls=(forged_call,),
            candidates=(),
            rejections=(),
            gaps=(brief.AcquisitionGap(need_id=need_id, reason="query_failed"),),
        )


def test_acquisition_timeout_is_bounded_and_does_not_expose_backend_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Bound query duration.", "slow bounded query")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            need.query_text: {
                "sleep_seconds": 1,
                "exit_code": 9,
                "stderr": "SECRET_TIMEOUT_DETAIL_4412",
            }
        },
    )
    monkeypatch.setattr(brief, "QUERY_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(brief.OpportunityBriefError, match="timed out") as captured:
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )
    assert "SECRET_TIMEOUT_DETAIL_4412" not in str(captured.value)


def test_acquisition_pins_executable_and_rejects_atomic_path_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Pin command identity.", "pin command")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    payload = make_query_payload(
        need.query_text,
        target_repo_id="target-repo-01",
        model_id=str(model_path.resolve()),
    )
    fake_cam, original_log = make_fake_cam(tmp_path, {need.query_text: payload})
    replacement_marker = tmp_path / "replacement-ran"
    replacement = tmp_path / "replacement-cam"
    replacement.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "from pathlib import Path\n"
        f"Path({str(replacement_marker)!r}).write_text('ran', encoding='utf-8')\n"
        f"print(json.dumps({payload!r}, sort_keys=True))\n",
        encoding="utf-8",
    )
    replacement.chmod(0o755)
    real_popen = brief.subprocess.Popen
    replaced = False

    def replacing_popen(arguments, *args, **kwargs):
        nonlocal replaced
        if not replaced:
            os.replace(replacement, fake_cam)
            replaced = True
        return real_popen(arguments, *args, **kwargs)

    monkeypatch.setattr(brief.subprocess, "Popen", replacing_popen)

    with pytest.raises(brief.OpportunityBriefError, match="identity|changed"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )
    assert original_log.exists(), "the descriptor-pinned original must execute"
    assert not replacement_marker.exists()


@pytest.mark.parametrize("artifact_kind", ["command", "sidecar"])
def test_acquisition_rejects_hardlinked_file_artifacts_before_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact_kind: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Reject ambiguous links.", "hardlink identity")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    fake_cam, _log = make_fake_cam(tmp_path, {})
    if artifact_kind == "command":
        alias = tmp_path / "hardlinked-cam"
        os.link(fake_cam, alias)
        fake_cam = alias
    else:
        alias = tmp_path / "hardlinked.sqlite"
        os.link(sidecar, alias)
        sidecar = alias

    def forbidden_popen(*_args, **_kwargs):
        raise AssertionError("hardlink rejection must precede process creation")

    monkeypatch.setattr(brief.subprocess, "Popen", forbidden_popen)
    with pytest.raises(brief.OpportunityBriefError, match="hard.?link|single.?link"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )


@pytest.mark.parametrize("artifact_kind", ["sidecar", "model"])
def test_acquisition_rechecks_artifact_digests_between_every_query(
    tmp_path: Path,
    artifact_kind: str,
) -> None:
    brief = load_module()
    first = make_need(brief, "First stable need.", "first stable query")
    second = make_need(
        brief,
        "Second stable need.",
        "second stable query",
        category="risk",
    )
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"original sidecar")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    model_file = model_path / "config.json"
    model_file.write_text("original model", encoding="utf-8")
    target_repo_id = "target-repo-01"
    mutate_path = sidecar if artifact_kind == "sidecar" else model_file
    fake_cam, log_path = make_fake_cam(
        tmp_path,
        {
            first.query_text: {
                "mutate_path": str(mutate_path),
                "payload": make_query_payload(
                    first.query_text,
                    target_repo_id=target_repo_id,
                    model_id=str(model_path.resolve()),
                ),
            },
            second.query_text: make_query_payload(
                second.query_text,
                target_repo_id=target_repo_id,
                model_id=str(model_path.resolve()),
            ),
        },
    )

    with pytest.raises(brief.OpportunityBriefError, match="identity|changed|digest"):
        brief.acquire_opportunities(
            needs=(first, second),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id=target_repo_id,
        )
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.parametrize(
    "source_sha256",
    [
        ("f" * 64, "0" * 64),
        ("f" * 64, "f" * 64),
    ],
)
def test_acquisition_preserves_positional_source_digest_pairing(
    tmp_path: Path,
    source_sha256: tuple[str, str],
) -> None:
    brief = load_module()
    need = make_need(brief, "Keep evidence pairs.", "evidence pairs")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    record = make_record_mapping()
    evidence = record["evidence"]
    evidence["source_files"] = ["src/a.py", "src/b.py"]
    evidence["source_sha256"] = list(source_sha256)
    target_repo_id = "target-repo-01"
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            need.query_text: make_query_payload(
                need.query_text,
                target_repo_id=target_repo_id,
                model_id=str(model_path.resolve()),
                record=record,
            )
        },
    )

    receipt = brief.acquire_opportunities(
        needs=(need,),
        cam_command=fake_cam,
        sidecar=sidecar,
        semantic_model_path=model_path,
        target_repo_id=target_repo_id,
    )

    assert receipt.candidates[0].record.evidence.source_sha256 == source_sha256


@pytest.mark.parametrize("protocol_case", ["duplicate-key", "constant", "depth"])
def test_acquisition_rejects_noncanonical_json_protocol(
    tmp_path: Path,
    protocol_case: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Reject ambiguous JSON.", "strict json")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    payload = make_query_payload(
        need.query_text,
        target_repo_id="target-repo-01",
        model_id=str(model_path.resolve()),
    )
    if protocol_case == "duplicate-key":
        raw = json.dumps(payload)[:-1] + f', "query": {json.dumps(need.query_text)}}}'
    elif protocol_case == "constant":
        raw = json.dumps(payload)[:-1] + ', "padding": NaN}'
    else:
        raw = json.dumps(payload)[:-1] + ', "padding": ' + "[" * 40 + "0" + "]" * 40 + "}"
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {need.query_text: {"raw_stdout": raw}},
    )

    with pytest.raises(brief.OpportunityBriefError, match="JSON|duplicate|constant|depth"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )


@pytest.mark.parametrize(
    "protocol_case",
    ["duplicate-rank", "result-order", "rejection-reason", "observed-semantics"],
)
def test_acquisition_rejects_noncanonical_result_protocol(
    tmp_path: Path,
    protocol_case: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Validate result protocol.", "result protocol")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    target_repo_id = "target-repo-01"
    first_record = make_record_mapping(source_repo_id="donor-repo-01")
    second_record = make_record_mapping(source_repo_id="donor-repo-02")
    second_record["problem"] = "A second bounded opportunity."
    payload = make_query_payload(
        need.query_text,
        target_repo_id=target_repo_id,
        model_id=str(model_path.resolve()),
        record=first_record,
    )
    first_result = payload["results"][0]
    if protocol_case in {"duplicate-rank", "result-order"}:
        second_result = {
            "record_id": record_id_for(second_record),
            "record": second_record,
            "fts_rank": 2,
            "semantic_rank": 1,
            "rrf_score": 1 / 62 + 1 / 61,
        }
        if protocol_case == "duplicate-rank":
            second_result["fts_rank"] = 1
            second_result["rrf_score"] = 2 / 61
            payload["results"].append(second_result)
        else:
            first_result["fts_rank"] = 1
            first_result["semantic_rank"] = 2
            first_result["rrf_score"] = 1 / 61 + 1 / 62
            payload["results"] = [second_result, first_result]
    elif protocol_case == "rejection-reason":
        payload["rejections"] = [
            {
                "record_id": "opp_" + "d" * 32,
                "reason": "target source omitted",
            }
        ]
    else:
        first_record["observed_effect"] = {
            "status": "observed",
            "text": "Proposed outcome without observation.",
        }
        first_result["record_id"] = record_id_for(first_record)
    fake_cam, _log = make_fake_cam(tmp_path, {need.query_text: payload})

    with pytest.raises(
        brief.OpportunityBriefError,
        match="rank|order|rejection|observed|record",
    ):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id=target_repo_id,
        )


@pytest.mark.parametrize(
    "error_text",
    [
        "database is not a recognized opportunity sidecar",
        "opportunity sidecar schema version is unsupported",
        "local semantic model could not be loaded",
        "encoder model_id does not match sidecar metadata",
    ],
)
def test_acquisition_aborts_on_nonrecoverable_cam_error_envelopes(
    tmp_path: Path,
    error_text: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Classify fatal query failures.", "fatal query")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            need.query_text: {
                "exit_code": 2,
                "stdout": json.dumps(
                    {"status": "error", "error": error_text},
                    sort_keys=True,
                ),
            }
        },
    )

    with pytest.raises(brief.OpportunityBriefError, match="non-recoverable|fatal"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )


@pytest.mark.parametrize("failure_kind", ["signal", "malformed", "wrong-exit", "stderr"])
def test_acquisition_aborts_on_signal_or_malformed_recoverable_envelope(
    tmp_path: Path,
    failure_kind: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Reject ambiguous failures.", "ambiguous failure")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    recoverable = json.dumps(
        {"status": "error", "error": "opportunity query backend failed"},
        sort_keys=True,
    )
    if failure_kind == "signal":
        response = {"signal_number": 15}
    elif failure_kind == "malformed":
        response = {"exit_code": 2, "stdout": recoverable[:-1]}
    elif failure_kind == "wrong-exit":
        response = {"exit_code": 3, "stdout": recoverable}
    else:
        response = {
            "exit_code": 2,
            "stdout": recoverable,
            "stderr": "unexpected stderr",
        }
    fake_cam, _log = make_fake_cam(tmp_path, {need.query_text: response})

    with pytest.raises(brief.OpportunityBriefError, match="non-recoverable"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )


def test_acquisition_receipt_binds_all_artifact_digests_and_call_argv(
    tmp_path: Path,
) -> None:
    brief = load_module()
    need = make_need(brief, "Bind receipt artifacts.", "artifact binding")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            need.query_text: make_query_payload(
                need.query_text,
                target_repo_id="target-repo-01",
                model_id=str(model_path.resolve()),
            )
        },
    )

    receipt = brief.acquire_opportunities(
        needs=(need,),
        cam_command=fake_cam,
        sidecar=sidecar,
        semantic_model_path=model_path,
        target_repo_id="target-repo-01",
    )

    assert receipt.cam_command == fake_cam
    assert receipt.sidecar == sidecar
    assert receipt.semantic_model_path == model_path
    assert receipt.executable_sha256 == sha256_path(fake_cam)
    assert receipt.sidecar_sha256 == sha256_path(sidecar)
    assert re.fullmatch(r"[0-9a-f]{64}", receipt.semantic_model_sha256)
    call = receipt.calls[0]
    assert call.executable_sha256 == receipt.executable_sha256
    assert call.sidecar_sha256 == receipt.sidecar_sha256
    assert call.semantic_model_sha256 == receipt.semantic_model_sha256
    with pytest.raises((TypeError, ValueError), match="digest|identity|call"):
        replace(receipt, executable_sha256="0" * 64)
    with pytest.raises((TypeError, ValueError), match="digest|identity|call"):
        replace(
            receipt,
            calls=(replace(call, sidecar_sha256="0" * 64),),
        )


@pytest.mark.parametrize("selector_failure", ["register", "select"])
def test_acquisition_selector_failures_kill_and_reap_without_private_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector_failure: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Own subprocess cleanup.", "selector cleanup")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {need.query_text: {"sleep_seconds": 5, "exit_code": 2}},
    )
    processes: list[subprocess.Popen] = []
    real_popen = brief.subprocess.Popen
    real_selector_factory = brief.selectors.DefaultSelector

    def recording_popen(arguments, *args, **kwargs):
        process = real_popen(arguments, *args, **kwargs)
        processes.append(process)
        return process

    class FailingSelector:
        def __init__(self) -> None:
            self.inner = real_selector_factory()

        def register(self, *args, **kwargs):
            if selector_failure == "register":
                raise RuntimeError("SECRET_SELECTOR_REGISTER_6821")
            return self.inner.register(*args, **kwargs)

        def select(self, *_args, **_kwargs):
            raise RuntimeError("SECRET_SELECTOR_SELECT_6821")

        def get_map(self):
            return self.inner.get_map()

        def unregister(self, *args, **kwargs):
            return self.inner.unregister(*args, **kwargs)

        def close(self) -> None:
            self.inner.close()

    monkeypatch.setattr(brief.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(brief.selectors, "DefaultSelector", FailingSelector)
    try:
        with pytest.raises(brief.OpportunityBriefError, match="subprocess|output") as captured:
            brief.acquire_opportunities(
                needs=(need,),
                cam_command=fake_cam,
                sidecar=sidecar,
                semantic_model_path=model_path,
                target_repo_id="target-repo-01",
            )
        assert "SECRET_SELECTOR" not in str(captured.value)
        assert processes and all(process.poll() is not None for process in processes)
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=1)


def test_acquisition_pins_python_interpreter_chain_before_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Bind interpreter identity.", "interpreter identity")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    interpreter = tmp_path / "python3.13"
    shutil.copy2(Path(sys.executable).resolve(), interpreter)
    interpreter.chmod(0o755)
    second_link = tmp_path / "python-link-2"
    second_link.symlink_to(interpreter)
    first_link = tmp_path / "python3"
    first_link.symlink_to(second_link)
    target_repo_id = "target-repo-01"
    payload = make_query_payload(
        need.query_text,
        target_repo_id=target_repo_id,
        model_id=str(model_path.resolve()),
    )
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {need.query_text: payload},
        interpreter=first_link,
    )
    replacement_marker = tmp_path / "replacement-interpreter-ran"
    replacement = tmp_path / "replacement-python"
    replacement.write_text(
        f"#!{sys.executable}\n"
        "import os\n"
        "import pathlib\n"
        "import sys\n"
        f"pathlib.Path({str(replacement_marker)!r}).write_text('ran', encoding='utf-8')\n"
        f"os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    replacement.chmod(0o755)
    real_popen = brief.subprocess.Popen

    def replacing_popen(arguments, *args, **kwargs):
        os.replace(replacement, interpreter)
        return real_popen(arguments, *args, **kwargs)

    monkeypatch.setattr(brief.subprocess, "Popen", replacing_popen)
    with pytest.raises(brief.OpportunityBriefError, match="interpreter|closure|identity"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id=target_repo_id,
        )
    assert not replacement_marker.exists()


def test_acquisition_binds_editable_cam_source_and_git_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Bind CAM source.", "cam source identity")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    implementation = tmp_path / "cam-source"
    source = implementation / "src" / "claw" / "cli.py"
    source.parent.mkdir(parents=True)
    source.write_text("def app_main():\n    return 0\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(implementation)], check=True)
    subprocess.run(["git", "-C", str(implementation), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(implementation),
            "-c",
            "user.name=Opportunity Brief Test",
            "-c",
            "user.email=opportunity-brief@example.invalid",
            "commit",
            "-qm",
            "fixture CAM source",
        ],
        check=True,
    )
    target_repo_id = "target-repo-01"
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            need.query_text: make_query_payload(
                need.query_text,
                target_repo_id=target_repo_id,
                model_id=str(model_path.resolve()),
            )
        },
        implementation_root=implementation,
    )
    real_popen = brief.subprocess.Popen
    mutated = False

    def replacing_popen(arguments, *args, **kwargs):
        nonlocal mutated
        if arguments and Path(arguments[0]).name == "fake-cam" and not mutated:
            source.write_text("def app_main():\n    return 7\n", encoding="utf-8")
            mutated = True
        return real_popen(arguments, *args, **kwargs)

    monkeypatch.setattr(brief.subprocess, "Popen", replacing_popen)
    with pytest.raises(brief.OpportunityBriefError, match="CAM source|closure|identity|changed"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id=target_repo_id,
        )


@pytest.mark.parametrize("returncode", [0, 2])
def test_acquisition_kills_leaderless_query_process_groups(
    tmp_path: Path,
    returncode: int,
) -> None:
    brief = load_module()
    need = make_need(brief, "Own process groups.", "process group ownership")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    marker = tmp_path / "background-child-survived"
    target_repo_id = "target-repo-01"
    response: dict[str, object] = {
        "background_marker": str(marker),
        "background_seconds": 0.3,
    }
    if returncode == 0:
        response["payload"] = make_query_payload(
            need.query_text,
            target_repo_id=target_repo_id,
            model_id=str(model_path.resolve()),
        )
    else:
        response.update(exit_code=returncode, stdout="{}")
    fake_cam, _log = make_fake_cam(tmp_path, {need.query_text: response})

    with pytest.raises(brief.OpportunityBriefError, match="process group|subprocess|non-recoverable"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=fake_cam,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id=target_repo_id,
        )
    time.sleep(0.45)
    assert not marker.exists()


def test_acquisition_hashes_model_only_at_initial_and_final_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    needs = tuple(
        make_need(
            brief,
            f"Bound hashing for need {index}.",
            f"bounded hash query {index}",
            category="blocker" if index == 0 else "risk",
        )
        for index in range(3)
    )
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    target_repo_id = "target-repo-01"
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            need.query_text: make_query_payload(
                need.query_text,
                target_repo_id=target_repo_id,
                model_id=str(model_path.resolve()),
            )
            for need in needs
        },
    )
    real_snapshot = brief._snapshot_model_directory
    snapshots = 0

    def counting_snapshot(path):
        nonlocal snapshots
        snapshots += 1
        return real_snapshot(path)

    monkeypatch.setattr(brief, "_snapshot_model_directory", counting_snapshot)
    receipt = brief.acquire_opportunities(
        needs=needs,
        cam_command=fake_cam,
        sidecar=sidecar,
        semantic_model_path=model_path,
        target_repo_id=target_repo_id,
    )

    assert len(receipt.calls) == 3
    assert snapshots == 2


def test_acquisition_cleanup_failure_is_sanitized_and_verified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Verify private cleanup.", "private cleanup")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    fake_cam, _log = make_fake_cam(
        tmp_path,
        {
            need.query_text: make_query_payload(
                need.query_text,
                target_repo_id="target-repo-01",
                model_id=str(model_path.resolve()),
            )
        },
    )
    real_rmtree = brief.shutil.rmtree
    leaked: list[Path] = []

    def ineffective_rmtree(path, *args, **kwargs):
        leaked.append(Path(path))

    monkeypatch.setattr(brief.shutil, "rmtree", ineffective_rmtree)
    try:
        with pytest.raises(brief.OpportunityBriefError, match="cleanup") as captured:
            brief.acquire_opportunities(
                needs=(need,),
                cam_command=fake_cam,
                sidecar=sidecar,
                semantic_model_path=model_path,
                target_repo_id="target-repo-01",
            )
        assert "SECRET" not in str(captured.value)
        assert leaked and all(path.exists() for path in leaked)
    finally:
        monkeypatch.setattr(brief.shutil, "rmtree", real_rmtree)
        for path in leaked:
            real_rmtree(path, ignore_errors=True)


@pytest.mark.parametrize(
    "shebang",
    ["#!/usr/bin/env python3", "#!python3", "#!/bin/sh -e -x"],
)
def test_acquisition_rejects_unsupported_launcher_shebangs_before_spawn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    shebang: str,
) -> None:
    brief = load_module()
    need = make_need(brief, "Reject launcher ambiguity.", "launcher form")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    launcher = tmp_path / "fake-cam"
    launcher.write_text(f"{shebang}\nraise SystemExit(0)\n", encoding="utf-8")
    launcher.chmod(0o755)

    def forbidden_popen(*_args, **_kwargs):
        raise AssertionError("unsupported launcher must fail before spawn")

    monkeypatch.setattr(brief.subprocess, "Popen", forbidden_popen)
    with pytest.raises(brief.OpportunityBriefError, match="launcher|shebang|interpreter"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=launcher,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )


def test_rendered_cross_repo_brief_has_exact_sections_and_source_bound_fields(
    tmp_path: Path,
) -> None:
    from tools import opportunity_brief as brief
    from tools import opportunity_ranker as ranker

    problem = "Evidence receipts do not survive relocation."
    need = make_need(brief, problem, "evidence receipt relocation verification")
    mapping = make_record_mapping()
    record = brief._parse_opportunity_record(
        mapping,
        target_repo_id="target-repo-01",
    )
    candidate = brief.OpportunityCandidate(
        record_id=record_id_for(mapping),
        record=record,
        matches=(
            brief.CandidateMatch(
                need_id=need.need_id,
                fts_rank=1,
                semantic_rank=1,
                rrf_score=2 / 61,
            ),
        ),
    )
    acquired = make_ranking_acquisition(
        brief,
        tmp_path,
        (need,),
        (candidate,),
    )
    handoff_text = (
        "# Current handoff\n\n## Blockers\n\n"
        "- Evidence receipts do not survive relocation.\n"
    )
    ranking = ranker.rank_and_select(
        needs=(need,),
        handoff_text=handoff_text,
        acquired=acquired,
    )
    snapshot = brief.WipSnapshot(
        target_path=tmp_path,
        target_revision="d" * 40,
        target_repo_id="target-repo-01",
        target_repo_id_is_exclusion_authoritative=True,
        branch="feature/evidence",
        dirty_entries=(),
        handoff=brief.HandoffEvidence(
            relative_path="HANDOFF_LATEST.md",
            sha256=hashlib.sha256(handoff_text.encode()).hexdigest(),
            text=handoff_text,
        ),
        truth_files=("GOAL.md",),
        visible_gaps=(),
        conflicts=(),
        verification_status="not_run",
    )

    rendered = brief.render_opportunity_brief(snapshot, ranking)

    assert rendered.startswith("# Cross-Repo Opportunity Brief\n")
    assert "\n## Starting point\n" in rendered
    assert "\n## Cross-repo opportunities\n" in rendered
    assert "\n## What CAM did not find\n" in rendered
    assert "- Problem: Evidence receipts do not survive relocation." in rendered
    assert "- Mechanism: Bind append-only receipts to content digests." in rendered
    assert "- Observed effect: Observed — Relocated receipts retained" in rendered
    assert "- Context: A local verification runner" in rendered
    assert "- Boundary: This does not establish scientific correctness." in rendered
    assert "- Why it may help here (Inference):" in rendered
    assert "- Evidence: donor@" + "a" * 40 in rendered
    assert "src/receipt.py" in rendered
    assert "ReceiptChain" in rendered
    assert "MIT" in rendered
    assert "PRIVATE_SOURCE_EXCERPT" not in rendered
    lowered = rendered.casefold()
    for forbidden_claim in ("sufficient", "implemented", "confirmed"):
        assert forbidden_claim not in lowered
    assert "implementation steps" not in lowered


def test_rendered_cross_repo_brief_preserves_honest_empty_selection(
    tmp_path: Path,
) -> None:
    from tools import opportunity_brief as brief
    from tools import opportunity_ranker as ranker

    problem = "Render a lunar shader with spectral caustics."
    need = make_need(brief, problem, "lunar shader spectral caustics")
    acquired = make_ranking_acquisition(brief, tmp_path, (need,), ())
    ranking = ranker.rank_and_select(
        needs=(need,),
        handoff_text=f"## Blockers\n\n- {problem}\n",
        acquired=acquired,
    )
    snapshot = brief.WipSnapshot(
        target_path=tmp_path,
        target_revision=None,
        target_repo_id="target-repo-01",
        target_repo_id_is_exclusion_authoritative=True,
        branch=None,
        dirty_entries=(),
        handoff=None,
        truth_files=(),
        visible_gaps=("No handoff was selected.",),
        conflicts=(),
        verification_status="not_run",
    )

    rendered = brief.render_opportunity_brief(snapshot, ranking)

    assert "## Cross-repo opportunities\n\n- No opportunity met" in rendered
    assert "## What CAM did not find" in rendered
    assert need.problem in rendered


def test_renderer_neutralizes_dynamic_commonmark_claims_and_source_excerpts(
    tmp_path: Path,
) -> None:
    from tools import opportunity_brief as brief
    from tools import opportunity_ranker as ranker

    need = make_need(
        brief,
        "Preserve evidence receipts after relocation.",
        "preserve evidence receipts relocation",
    )
    mapping = make_record_mapping()
    mapping["problem"] = (
        "Evidence receipts [external](https://evil.invalid) fail after relocation "
        "<script>alert(1)</script>."
    )
    mapping["mechanism"] = (
        "Bind evidence receipts to digests; def leaked(): return source_excerpt"
    )
    mapping["observed_effect"] = {
        "status": "observed",
        "text": "Confirmed sufficient implemented behavior.",
    }
    evidence = mapping["evidence"]
    assert isinstance(evidence, dict)
    evidence["source_repo_name"] = "[donor](https://evil.invalid)"
    evidence["source_files"] = ["src/[receipt](evil).py"]
    evidence["source_symbols"] = ["<script>alert</script>"]
    record = brief._parse_opportunity_record(
        mapping,
        target_repo_id="target-repo-01",
    )
    candidate = brief.OpportunityCandidate(
        record_id=record_id_for(mapping),
        record=record,
        matches=(
            brief.CandidateMatch(
                need_id=need.need_id,
                fts_rank=1,
                semantic_rank=1,
                rrf_score=2 / 61,
            ),
        ),
    )
    acquired = make_ranking_acquisition(
        brief,
        tmp_path,
        (need,),
        (candidate,),
    )
    handoff_text = "## Blockers\n\n- Preserve evidence receipts after relocation.\n"
    ranking = ranker.rank_and_select(
        needs=(need,),
        handoff_text=handoff_text,
        acquired=acquired,
    )
    snapshot = brief.WipSnapshot(
        target_path=(tmp_path / "[target](evil)").absolute(),
        target_revision="d" * 40,
        target_repo_id="target-repo-01",
        target_repo_id_is_exclusion_authoritative=True,
        branch="[branch](evil)",
        dirty_entries=(),
        handoff=brief.HandoffEvidence(
            relative_path="[handoff](evil).md",
            sha256=hashlib.sha256(handoff_text.encode()).hexdigest(),
            text=handoff_text,
        ),
        truth_files=(),
        visible_gaps=(),
        conflicts=(),
        verification_status="not_run",
    )

    rendered = brief.render_opportunity_brief(snapshot, ranking)
    lowered = rendered.casefold()

    assert "- Target path:" in rendered
    assert "[target](evil)" not in rendered
    assert "[branch](evil)" not in rendered
    assert "[handoff](evil)" not in rendered
    assert not re.search(r"(?<!\\)!?\[[^\]\n]*\]\([^\n)]*\)", rendered)
    assert "<script" not in lowered
    assert "def leaked" not in lowered
    assert "source_excerpt" not in lowered
    assert "source statement withheld: ambiguous status language" in rendered
    assert not re.search(r"\b(?:sufficient|implemented|confirmed)\b", lowered)


@pytest.mark.parametrize(
    "payload",
    (
        "const value = compute();",
        "int main() { return 0; }",
        "go build ./cmd && ./app",
        'fn main() { println!("x"); }',
        "let value: Int = compute()",
        "SELECT value FROM evidence;",
        "name = execute()",
        "run_task() -> Result",
        "1. Install dependencies 2. Edit config 3. Deploy service",
    ),
)
def test_renderer_withholds_language_neutral_code_and_multistep_excerpts(
    tmp_path: Path,
    payload: str,
) -> None:
    from tools import opportunity_brief as brief
    from tools import opportunity_ranker as ranker

    mapping = make_record_mapping()
    observed_effect = mapping["observed_effect"]
    assert isinstance(observed_effect, dict)
    observed_effect["text"] = payload

    rendered = render_record_mapping(brief, ranker, tmp_path, mapping)

    assert payload not in rendered
    assert "source statement withheld: code-shaped content" in rendered


@pytest.mark.parametrize(
    "field",
    (
        "problem",
        "mechanism",
        "observed_effect",
        "context",
        "boundary",
        "source_repo_name",
        "source_files",
        "source_symbols",
    ),
)
def test_renderer_applies_code_filter_to_every_dynamic_record_field(
    tmp_path: Path,
    field: str,
) -> None:
    from tools import opportunity_brief as brief
    from tools import opportunity_ranker as ranker

    payload = "const private_value = source_call();"
    mapping = make_record_mapping()
    if field in {"problem", "mechanism", "context", "boundary"}:
        mapping[field] = f"{mapping[field]} {payload}"
    elif field == "observed_effect":
        observed_effect = mapping["observed_effect"]
        assert isinstance(observed_effect, dict)
        observed_effect["text"] = payload
    else:
        evidence = mapping["evidence"]
        assert isinstance(evidence, dict)
        if field == "source_repo_name":
            evidence[field] = f"donor {payload}"
        elif field == "source_files":
            evidence[field] = [f"src/{payload}.txt"]
        else:
            evidence[field] = [payload]

    rendered = render_record_mapping(brief, ranker, tmp_path, mapping)

    assert payload not in rendered
    assert "source statement withheld: code-shaped content" in rendered


def test_renderer_accepts_valid_maximum_length_evidence_path_aggregate(
    tmp_path: Path,
) -> None:
    from tools import opportunity_brief as brief
    from tools import opportunity_ranker as ranker

    mapping = make_record_mapping()
    evidence = mapping["evidence"]
    assert isinstance(evidence, dict)
    paths = tuple(f"src/{index:02d}-{'a' * 890}.py" for index in range(5))
    evidence["source_files"] = list(paths)
    evidence["source_sha256"] = [f"{index:x}" * 64 for index in range(1, 6)]

    rendered = render_record_mapping(brief, ranker, tmp_path, mapping)

    assert all(path in rendered for path in paths)


def test_renderer_labels_selected_negative_evidence_as_a_negative_lesson(
    tmp_path: Path,
) -> None:
    from tools import opportunity_brief as brief
    from tools import opportunity_ranker as ranker

    need = make_need(
        brief,
        "Prevent mutable evidence loss during replay.",
        "prevent mutable evidence loss replay",
        category="risk",
    )
    mapping = make_record_mapping()
    mapping["problem"] = "Mutable replay logs lose evidence after partial failure."
    mapping["mechanism"] = (
        "Treat mutable replay logs as a negative lesson and require immutable receipts."
    )
    mapping["observed_effect"] = {
        "status": "negative",
        "text": "The mutable log lost evidence after a partial write.",
    }
    mapping["context"] = "Evidence replay recovery."
    mapping["boundary"] = "The failed design is evidence to avoid, not a recommendation."
    record = brief._parse_opportunity_record(
        mapping,
        target_repo_id="target-repo-01",
    )
    candidate = brief.OpportunityCandidate(
        record_id=record_id_for(mapping),
        record=record,
        matches=(
            brief.CandidateMatch(
                need_id=need.need_id,
                fts_rank=1,
                semantic_rank=1,
                rrf_score=2 / 61,
            ),
        ),
    )
    acquired = make_ranking_acquisition(
        brief,
        tmp_path,
        (need,),
        (candidate,),
    )
    ranking = ranker.rank_and_select(
        needs=(need,),
        handoff_text="## Risks\n\n- Prevent evidence loss during replay.\n",
        acquired=acquired,
    )
    snapshot = brief.WipSnapshot(
        target_path=tmp_path.absolute(),
        target_revision=None,
        target_repo_id="target-repo-01",
        target_repo_id_is_exclusion_authoritative=True,
        branch=None,
        dirty_entries=(),
        handoff=None,
        truth_files=(),
        visible_gaps=(),
        conflicts=(),
        verification_status="not_run",
    )

    rendered = brief.render_opportunity_brief(snapshot, ranking)

    assert "### Negative lesson:" in rendered
    assert "Why this negative lesson matters here (Inference)" in rendered
    assert "Why it may help here (Inference)" not in rendered


def test_acquisition_rejects_python_named_link_to_non_python_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    brief = load_module()
    need = make_need(brief, "Reject false Python launchers.", "python identity")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    lexical_interpreter = tmp_path / "python"
    lexical_interpreter.symlink_to("/bin/sh")
    launcher = tmp_path / "fake-cam"
    launcher.write_text(
        f"#!{lexical_interpreter}\nraise SystemExit(0)\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    spawned = False

    def forbidden_popen(*_args, **_kwargs):
        nonlocal spawned
        spawned = True
        raise AssertionError("non-Python terminal must fail before spawn")

    monkeypatch.setattr(brief.subprocess, "Popen", forbidden_popen)
    with pytest.raises(brief.OpportunityBriefError, match="interpreter|Python|unsupported"):
        brief.acquire_opportunities(
            needs=(need,),
            cam_command=launcher,
            sidecar=sidecar,
            semantic_model_path=model_path,
            target_repo_id="target-repo-01",
        )
    assert not spawned


def test_production_style_editable_venv_launcher_works_with_different_caller_python(
    tmp_path: Path,
) -> None:
    brief = load_module()
    caller_interpreter = Path(sys.executable).resolve(strict=True)
    production_launcher = Path(
        "/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/.venv/bin/cam"
    )
    if not production_launcher.is_file():
        pytest.skip("production CAM virtualenv is not available")
    terminal_interpreter = Path(
        production_launcher.read_text(encoding="utf-8").splitlines()[0][2:]
    ).resolve(strict=True)
    assert sha256_path(terminal_interpreter) != sha256_path(caller_interpreter)
    need = make_need(brief, "Use the production CAM venv.", "production venv query")
    sidecar = tmp_path / "opportunities.sqlite"
    sidecar.write_bytes(b"fixture")
    model_path = tmp_path / "semantic-model"
    model_path.mkdir()
    target_repo_id = "target-repo-01"
    launcher, implementation, log_path = make_editable_venv_cam(
        tmp_path,
        {
            need.query_text: make_query_payload(
                need.query_text,
                target_repo_id=target_repo_id,
                model_id=str(model_path.resolve()),
            )
        },
        terminal_interpreter=terminal_interpreter,
    )
    before_source = tuple(
        (path.relative_to(implementation), path.read_bytes())
        for path in sorted((implementation / "src").rglob("*"))
        if path.is_file()
    )

    receipt = brief.acquire_opportunities(
        needs=(need,),
        cam_command=launcher,
        sidecar=sidecar,
        semantic_model_path=model_path,
        target_repo_id=target_repo_id,
    )

    closure = receipt.execution_closure
    lexical_interpreter = launcher.parent / "python"
    assert closure.launcher_path == launcher
    assert closure.launcher_identity == receipt.executable_identity
    assert closure.launcher_sha256 == receipt.executable_sha256
    assert closure.interpreter_path == lexical_interpreter
    assert closure.interpreter_symlink_chain[0].path == lexical_interpreter
    assert closure.resolved_interpreter_path == terminal_interpreter
    assert closure.interpreter_sha256 == sha256_path(terminal_interpreter)
    assert closure.python_home == terminal_interpreter.parent.parent
    assert closure.python_home_identity is not None
    assert closure.python_runtime_library_path is not None
    assert closure.python_runtime_library_identity is not None
    assert closure.python_runtime_library_sha256 is not None
    assert closure.editable_site_packages == (
        launcher.parent.parent / "lib" / "python3.9" / "site-packages"
    )
    assert closure.editable_site_packages_identity is not None
    assert closure.cam_source_root == implementation
    assert closure.cam_source_root_identity is not None
    assert closure.cam_source_dirty_entries == ()
    assert tuple(call.status for call in receipt.calls) == ("ok",)
    assert log_path.is_file()
    after_source = tuple(
        (path.relative_to(implementation), path.read_bytes())
        for path in sorted((implementation / "src").rglob("*"))
        if path.is_file()
    )
    assert after_source == before_source
    assert not tuple((implementation / "src").rglob("__pycache__"))
    assert not tuple((implementation / "src").rglob("*.pyc"))
    status = subprocess.run(
        ["git", "-C", str(implementation), "status", "--porcelain"],
        check=True,
        capture_output=True,
    )
    assert status.stdout == b""


def test_query_environment_disables_python_bytecode_writes() -> None:
    brief = load_module()

    assert brief._query_environment()["PYTHONDONTWRITEBYTECODE"] == "1"


def test_execution_closure_digest_is_derived_from_every_public_input() -> None:
    brief = load_module()
    identity = (1, 2, 1, 10, 3, 4)
    other_identity = (1, 3, 1, 11, 5, 6)
    link = brief.InterpreterSymlinkReceipt(
        path=Path("/opt/cam/.venv/bin/python"),
        identity=identity,
        target="/usr/bin/python3",
    )
    closure = brief.ExecutionClosureReceipt(
        launcher_kind="python",
        launcher_path=Path("/opt/cam/.venv/bin/cam"),
        launcher_identity=identity,
        launcher_sha256="1" * 64,
        interpreter_path=Path("/opt/cam/.venv/bin/python"),
        interpreter_symlink_chain=(link,),
        resolved_interpreter_path=Path("/usr/bin/python3"),
        resolved_interpreter_identity=other_identity,
        interpreter_sha256="2" * 64,
        python_home=Path("/opt/python/3.12"),
        python_home_identity=identity,
        python_runtime_library_path=Path("/opt/python/3.12/lib/libpython3.12.dylib"),
        python_runtime_library_identity=other_identity,
        python_runtime_library_sha256="6" * 64,
        editable_site_packages=Path("/opt/cam/.venv/lib/python3.9/site-packages"),
        editable_site_packages_identity=identity,
        editable_metadata_sha256="3" * 64,
        cam_source_root=Path("/opt/cam/source"),
        cam_source_root_identity=identity,
        cam_source_revision="4" * 40,
        cam_source_branch="main",
        cam_source_dirty_entries=("? src/claw/new.py",),
        cam_source_sha256="5" * 64,
    )

    assert next(field for field in fields(closure) if field.name == "sha256").init is False
    with pytest.raises(TypeError, match="sha256"):
        brief.ExecutionClosureReceipt(
            **{
                field.name: getattr(closure, field.name)
                for field in fields(closure)
                if field.name != "sha256"
            },
            sha256="0" * 64,
        )
    variants = (
        replace(closure, launcher_path=Path("/opt/cam/.venv/bin/cam-other")),
        replace(closure, launcher_identity=other_identity),
        replace(closure, launcher_sha256="a" * 64),
        replace(closure, interpreter_path=Path("/opt/cam/.venv/bin/python3")),
        replace(
            closure,
            interpreter_symlink_chain=(replace(link, identity=other_identity),),
        ),
        replace(closure, resolved_interpreter_path=Path("/usr/bin/python3-other")),
        replace(closure, resolved_interpreter_identity=identity),
        replace(closure, interpreter_sha256="b" * 64),
        replace(closure, python_home=Path("/opt/python/3.12-other")),
        replace(closure, python_home_identity=other_identity),
        replace(
            closure,
            python_runtime_library_path=Path(
                "/opt/python/3.12/lib/libpython3.12-other.dylib"
            ),
        ),
        replace(closure, python_runtime_library_identity=identity),
        replace(closure, python_runtime_library_sha256="f" * 64),
        replace(
            closure,
            editable_site_packages=Path("/opt/cam/.venv/lib/python3.10/site-packages"),
        ),
        replace(closure, editable_site_packages_identity=other_identity),
        replace(closure, editable_metadata_sha256="c" * 64),
        replace(closure, cam_source_root=Path("/opt/cam/other-source")),
        replace(closure, cam_source_root_identity=other_identity),
        replace(closure, cam_source_revision="d" * 40),
        replace(closure, cam_source_branch="release"),
        replace(closure, cam_source_dirty_entries=("? src/claw/other.py",)),
        replace(closure, cam_source_sha256="e" * 64),
    )
    assert all(variant.sha256 != closure.sha256 for variant in variants)
    assert replace(closure).sha256 == closure.sha256
    with pytest.raises(ValueError, match="sorted|unique"):
        replace(
            closure,
            cam_source_dirty_entries=("? src/claw/z.py", "? src/claw/a.py"),
        )
    with pytest.raises(ValueError, match="sorted|unique"):
        replace(
            closure,
            cam_source_dirty_entries=("? src/claw/a.py", "? src/claw/a.py"),
        )
