from dataclasses import replace
from pathlib import Path

import pytest

from tools.cam_pull_mine_dir import (
    CommandResult,
    DEFAULT_SOURCE_ROOT,
    PullMineConfig,
    assess_meaningful_mining,
    discover_git_repositories,
    load_local_defaults,
    update_repository,
    validate_config,
)


def _valid_config(tmp_path: Path, *, source_root: Path | None = None) -> PullMineConfig:
    root = source_root or tmp_path / "repositories"
    root.mkdir(exist_ok=True)
    cam_command = tmp_path / "cam"
    cam_command.write_text("#!/bin/sh\n", encoding="utf-8")
    cam_command.chmod(0o700)
    cam_db = tmp_path / "claw.db"
    cam_db.write_text("fixture", encoding="utf-8")
    cam_config = tmp_path / "claw.toml"
    cam_config.write_text("[cam]\n", encoding="utf-8")
    return PullMineConfig(
        source_root=root,
        cam_command=cam_command,
        cam_db=cam_db,
        cam_config=cam_config,
        profiles=None,
        wrapper=None,
        state_dir=tmp_path / "state",
        exact_model="provider/approved-model",
        max_repos=20,
        max_minutes=120,
        max_cost_usd=5.0,
    )


def test_default_source_root_is_the_approved_repositories_directory() -> None:
    assert DEFAULT_SOURCE_ROOT == Path("/Volumes/WS4TB/waswiki/repos2mine/repo622sn")


def test_explicit_source_root_is_preserved_by_validation(tmp_path: Path) -> None:
    config = _valid_config(tmp_path, source_root=tmp_path / "another-user-repositories")

    assert validate_config(config) == config
    assert config.to_dict()["source_root"] == str(tmp_path / "another-user-repositories")


def test_load_local_defaults_reads_only_operational_limits(tmp_path: Path) -> None:
    local_defaults = tmp_path / "cam-pull-mine-dir.toml"
    local_defaults.write_text(
        'exact_model = "provider/approved-model"\n'
        "max_repos = 3\n"
        "max_minutes = 45\n"
        "max_cost_usd = 1.5\n",
        encoding="utf-8",
    )

    assert load_local_defaults(local_defaults) == {
        "exact_model": "provider/approved-model",
        "max_repos": 3,
        "max_minutes": 45,
        "max_cost_usd": 1.5,
    }


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("source_root", "source_root does not exist"),
        ("cam_command", "cam_command does not exist"),
        ("cam_command_not_executable", "cam_command is not executable"),
        ("max_repos", "max_repos must be positive"),
        ("max_minutes", "max_minutes must be positive"),
        ("max_cost_usd_not_positive", "max_cost_usd must be positive"),
        ("max_cost_usd", "exact_model is required"),
        ("exact_model_without_budget", "max_cost_usd is required"),
    ],
)
def test_validation_rejects_invalid_operational_bounds(
    tmp_path: Path, replacement: str, message: str
) -> None:
    config = _valid_config(tmp_path)
    if replacement == "source_root":
        invalid = replace(config, source_root=tmp_path / "missing-root")
    elif replacement == "cam_command":
        invalid = replace(config, cam_command=tmp_path / "missing-cam")
    elif replacement == "cam_command_not_executable":
        config.cam_command.chmod(0o600)
        invalid = config
    elif replacement == "max_repos":
        invalid = replace(config, max_repos=0)
    elif replacement == "max_minutes":
        invalid = replace(config, max_minutes=0)
    elif replacement == "max_cost_usd_not_positive":
        invalid = replace(config, max_cost_usd=0.0)
    elif replacement == "exact_model_without_budget":
        invalid = replace(config, max_cost_usd=None)
    else:
        invalid = replace(config, exact_model=None)

    with pytest.raises(ValueError, match=message):
        validate_config(invalid)


@pytest.mark.parametrize(
    ("findings", "repositories", "repeated_pattern_or_gap", "expected"),
    [
        (4, 2, True, False),
        (5, 1, True, False),
        (5, 2, False, False),
        (5, 2, True, True),
    ],
)
def test_meaningful_mining_requires_all_evidence_gates(
    findings: int,
    repositories: int,
    repeated_pattern_or_gap: bool,
    expected: bool,
) -> None:
    assessment = assess_meaningful_mining(
        validated_provenance_findings=findings,
        source_repositories=repositories,
        repeated_pattern_or_gap=repeated_pattern_or_gap,
    )

    assert assessment.is_meaningful is expected
    assert assessment.findings == findings
    assert assessment.source_repositories == repositories
    assert assessment.repeated_pattern_or_gap is repeated_pattern_or_gap
    assert assessment.reasons


class FakeGitRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult] | None = None) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.responses = responses or {}

    def __call__(self, argv: list[str]) -> CommandResult:
        call = tuple(argv)
        self.calls.append(call)
        if call in self.responses:
            return self.responses[call]
        if call[-3:] == ("rev-parse", "--abbrev-ref", "HEAD"):
            return CommandResult(0, "main\n", "")
        if call[-3:] == ("rev-parse", "--abbrev-ref", "@{upstream}"):
            return CommandResult(0, "origin/main\n", "")
        if call[-3:] == ("status", "--porcelain=v1", "--branch"):
            return CommandResult(0, "## main...origin/main\n", "")
        return CommandResult(0, "", "")


def _git_call(repo: Path, *args: str) -> tuple[str, ...]:
    return ("git", "-C", str(repo), *args)


def test_discover_git_repositories_finds_nested_dot_git_entries(tmp_path: Path) -> None:
    (tmp_path / "alpha" / ".git").mkdir(parents=True)
    (tmp_path / "nested" / "beta" / ".git").mkdir(parents=True)
    (tmp_path / "not-a-repo").mkdir()

    assert discover_git_repositories(tmp_path) == (
        tmp_path / "alpha",
        tmp_path / "nested" / "beta",
    )


def test_git_update_uses_only_clean_attached_upstream_fast_forward_commands(tmp_path: Path) -> None:
    repo = tmp_path / "clean"
    repo.mkdir()
    runner = FakeGitRunner()

    update = update_repository(repo, runner)

    assert update.status == "updated"
    assert update.branch == "main"
    assert runner.calls == [
        _git_call(repo, "status", "--porcelain=v1", "--branch"),
        _git_call(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        _git_call(repo, "rev-parse", "--abbrev-ref", "@{upstream}"),
        _git_call(repo, "fetch", "origin"),
        _git_call(repo, "pull", "--ff-only"),
    ]


@pytest.mark.parametrize(
    ("responses", "expected_reason"),
    [
        (
            {("status", "--porcelain=v1", "--branch"): CommandResult(0, "## main...origin/main\n M file.py\n", "")},
            "dirty",
        ),
        (
            {("status", "--porcelain=v1", "--branch"): CommandResult(0, "## main...origin/main\nUU file.py\n", "")},
            "conflicts",
        ),
        ({("rev-parse", "--abbrev-ref", "HEAD"): CommandResult(0, "HEAD\n", "")}, "detached"),
        ({("rev-parse", "--abbrev-ref", "@{upstream}"): CommandResult(1, "", "no upstream")}, "upstream"),
    ],
)
def test_git_update_skips_repositories_outside_the_safe_boundary(
    tmp_path: Path,
    responses: dict[tuple[str, ...], CommandResult],
    expected_reason: str,
) -> None:
    repo = tmp_path / "ineligible"
    repo.mkdir()
    expanded = {_git_call(repo, *args): result for args, result in responses.items()}
    runner = FakeGitRunner(expanded)

    update = update_repository(repo, runner)

    assert update.status == "skipped"
    assert expected_reason in update.reason
    assert _git_call(repo, "fetch", "origin") not in runner.calls
    assert _git_call(repo, "pull", "--ff-only") not in runner.calls


@pytest.mark.parametrize(
    ("failed_command", "expected_reason"),
    [(("fetch", "origin"), "fetch failed"), (("pull", "--ff-only"), "fast-forward failed")],
)
def test_git_update_records_fetch_and_fast_forward_failures(
    tmp_path: Path, failed_command: tuple[str, ...], expected_reason: str
) -> None:
    repo = tmp_path / "failure"
    repo.mkdir()
    runner = FakeGitRunner(
        {_git_call(repo, *failed_command): CommandResult(1, "", "fixture failure")}
    )

    update = update_repository(repo, runner)

    assert update.status == "failed"
    assert expected_reason in update.reason


def test_git_update_does_not_prevent_a_later_eligible_repository_from_updating(tmp_path: Path) -> None:
    bad_repo = tmp_path / "bad"
    good_repo = tmp_path / "good"
    bad_repo.mkdir()
    good_repo.mkdir()
    runner = FakeGitRunner(
        {_git_call(bad_repo, "fetch", "origin"): CommandResult(1, "", "fixture failure")}
    )

    bad_update = update_repository(bad_repo, runner)
    good_update = update_repository(good_repo, runner)

    assert bad_update.status == "failed"
    assert good_update.status == "updated"


def test_git_update_never_constructs_a_destructive_command(tmp_path: Path) -> None:
    repo = tmp_path / "clean"
    repo.mkdir()
    runner = FakeGitRunner()

    update_repository(repo, runner)

    forbidden = {"reset", "merge", "rebase", "stash", "checkout", "switch", "--force"}
    assert all(forbidden.isdisjoint(call) for call in runner.calls)
