import json
import sqlite3
import subprocess
import sys
from hashlib import sha256
from dataclasses import replace
from pathlib import Path

import pytest
import tools.cam_pull_mine_dir as pull_mine_dir

from tools.cam_pull_mine_dir import (
    CommandResult,
    CommandSummary,
    CorpusSnapshot,
    DEFAULT_SOURCE_ROOT,
    MiningDelta,
    PullMineReceipt,
    PullMineConfig,
    RepositoryUpdate,
    assess_meaningful_mining,
    build_config_from_args,
    build_parser,
    build_live_argv,
    build_scan_argv,
    discover_git_repositories,
    derive_mining_delta,
    fingerprint_file,
    load_local_defaults,
    launch_candidate_if_warranted,
    pinned_cam_environment,
    render_markdown_report,
    run_pull_mine_directory,
    run_scan_then_live,
    summarize_command_result,
    snapshot_corpus,
    update_repository,
    validate_config,
    write_report,
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


def test_mining_command_builders_use_the_exact_bounded_cam_argv(tmp_path: Path) -> None:
    profiles = tmp_path / "model_profiles.toml"
    profiles.write_text("[profiles]\n", encoding="utf-8")
    config = replace(_valid_config(tmp_path), profiles=profiles)
    receipt_path = tmp_path / "budget-receipt.json"

    assert build_scan_argv(config) == [
        str(config.cam_command),
        "mine-workspace",
        str(config.source_root),
        "--target",
        str(config.source_root),
        "--changed-only",
        "--scan-only",
        "--no-tasks",
        "--max-repos",
        "20",
        "--max-minutes",
        "120",
        "--config",
        str(config.cam_config),
    ]
    assert build_live_argv(config, receipt_path) == [
        str(config.cam_command),
        "mine-workspace",
        str(config.source_root),
        "--target",
        str(config.source_root),
        "--changed-only",
        "--no-tasks",
        "--max-repos",
        "20",
        "--max-minutes",
        "120",
        "--config",
        str(config.cam_config),
        "--profiles",
        str(profiles),
        "--max-cost-usd",
        "5.0",
        "--exact-model",
        "provider/approved-model",
        "--budget-receipt",
        str(receipt_path),
    ]


def test_pinned_mining_environment_preserves_parent_and_overrides_both_db_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _valid_config(tmp_path)
    monkeypatch.setenv("CAM_PULL_MINE_DIR_TEST_PARENT", "preserved")

    environment = pinned_cam_environment(config)

    assert environment["CAM_PULL_MINE_DIR_TEST_PARENT"] == "preserved"
    assert environment["CLAW_DB_PATH"] == str(config.cam_db)
    assert environment["CAM_CODEX_MCP_DB_PATH"] == str(config.cam_db)


def test_mining_command_execution_stops_before_live_mining_when_scan_fails(tmp_path: Path) -> None:
    config = _valid_config(tmp_path)
    calls: list[tuple[list[str], Path, dict[str, str]]] = []

    def failed_scan_runner(
        argv: list[str], *, cwd: Path, env: dict[str, str]
    ) -> CommandResult:
        calls.append((argv, cwd, env))
        return CommandResult(1, "scan failed", "fixture")

    execution = run_scan_then_live(
        config,
        tmp_path / "budget-receipt.json",
        runner=failed_scan_runner,
    )

    assert execution.scan.returncode == 1
    assert execution.live is None
    assert len(calls) == 1
    assert "--scan-only" in calls[0][0]
    assert calls[0][1] == config.cam_command.parent.parent
    assert calls[0][2]["CLAW_DB_PATH"] == str(config.cam_db)


def test_live_mining_command_never_adds_task_generation_or_unsupported_flags(tmp_path: Path) -> None:
    config = _valid_config(tmp_path)
    command = build_live_argv(config, tmp_path / "budget-receipt.json")

    assert "--no-tasks" in command
    assert {"--tasks", "--fast", "--self-assess"}.isdisjoint(command)


def _write_methodologies(db_path: Path, methodology_ids: tuple[str, ...]) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE methodologies (id TEXT PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO methodologies (id) VALUES (?)",
            [(methodology_id,) for methodology_id in methodology_ids],
        )


def _write_mining_ledger(path: Path, records: dict[str, tuple[str, ...]]) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "records": {
                    repository: {
                        "repo_name": repository,
                        "methodology_ids": list(methodology_ids),
                    }
                    for repository, methodology_ids in records.items()
                },
            }
        ),
        encoding="utf-8",
    )


def test_snapshot_corpus_uses_read_only_integrity_and_ledger_provenance(tmp_path: Path) -> None:
    db_path = tmp_path / "claw.db"
    ledger_path = tmp_path / "mining_registry.json"
    _write_methodologies(db_path, ("method-1",))
    _write_mining_ledger(ledger_path, {"repo-a": ("method-1",)})

    before = snapshot_corpus(db_path, ledger_path)
    with sqlite3.connect(db_path) as connection:
        connection.executemany(
            "INSERT INTO methodologies (id) VALUES (?)",
            [("method-2",), ("method-3",)],
        )
    _write_mining_ledger(
        ledger_path,
        {"repo-a": ("method-1", "method-2"), "repo-b": ("method-3",)},
    )
    after = snapshot_corpus(db_path, ledger_path)

    delta = derive_mining_delta(before, after)

    assert before.integrity == "ok"
    assert after.integrity == "ok"
    assert after.methodology_count == 3
    assert after.ledger_entries == 2
    assert delta.methodologies_added == 2
    assert delta.ledger_entries_added == 1
    assert delta.findings == 2
    assert delta.source_repositories == frozenset({"repo-a", "repo-b"})


def test_snapshot_corpus_rejects_a_database_without_expected_methodology_id(tmp_path: Path) -> None:
    db_path = tmp_path / "claw.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE methodologies (name TEXT)")

    with pytest.raises(ValueError, match="methodologies.id"):
        snapshot_corpus(db_path, None)


def test_file_and_command_summaries_are_digest_only_and_redact_secrets(tmp_path: Path) -> None:
    content = "database fixture\n"
    output = "completed SENTINEL_SECRET " * 50
    path = tmp_path / "claw.db"
    path.write_text(content, encoding="utf-8")

    summary = summarize_command_result(
        CommandResult(0, output, ""),
        redaction_values=("SENTINEL_SECRET",),
    )

    assert fingerprint_file(path) == f"sha256:{sha256(content.encode()).hexdigest()}"
    assert summary.stdout_digest == f"sha256:{sha256(output.encode()).hexdigest()}"
    assert "SENTINEL_SECRET" not in summary.stdout_summary
    assert len(summary.stdout_summary) <= 320


def _receipt_with_secret(tmp_path: Path) -> PullMineReceipt:
    config = _valid_config(tmp_path)
    assessment = assess_meaningful_mining(
        validated_provenance_findings=5,
        source_repositories=2,
        repeated_pattern_or_gap=True,
    )
    summary = CommandSummary(
        returncode=0,
        stdout_digest="sha256:scan",
        stderr_digest="sha256:stderr",
        stdout_summary="scan completed",
        stderr_summary="",
    )
    return PullMineReceipt(
        source_root=config.source_root,
        database_fingerprint="sha256:database",
        config_fingerprint="sha256:config",
        before=CorpusSnapshot(2, 1, "ok"),
        after=CorpusSnapshot(7, 3, "ok"),
        delta=MiningDelta(
            methodologies_added=5,
            ledger_entries_added=2,
            findings=5,
            source_repositories=frozenset({"repo-a", "repo-b"}),
        ),
        updates=(
            RepositoryUpdate(
                path=tmp_path / "skipped",
                branch="main",
                status="skipped",
                reason="dirty SENTINEL_SECRET",
            ),
        ),
        assessment=assessment,
        scan=summary,
        live=summary,
        candidate_verdict="not_run",
        redaction_values=("SENTINEL_SECRET",),
    )


def test_reports_list_truthful_evidence_and_redact_secret_values(tmp_path: Path) -> None:
    receipt = _receipt_with_secret(tmp_path)

    markdown = render_markdown_report(receipt)
    json_path, markdown_path = write_report(receipt, tmp_path / "reports")
    json_report = json_path.read_text(encoding="utf-8")
    markdown_report = markdown_path.read_text(encoding="utf-8")

    for report in (markdown, json_report, markdown_report):
        assert str(receipt.source_root) in report
        assert "sha256:database" in report
        assert "sha256:config" in report
        assert "skipped" in report
        assert "SENTINEL_SECRET" not in report
        assert "[REDACTED]" in report
    assert "candidate verdict: not_run" in markdown.lower()
    assert "candidate verdict: not_run" in markdown_report.lower()
    assert '"candidate_verdict": "not_run"' in json_report
    assert json.loads(json_report)["assessment"]["is_meaningful"] is True
    assert json_path.stat().st_mode & 0o777 == 0o600
    assert markdown_path.stat().st_mode & 0o777 == 0o600
    assert json_path.parent.stat().st_mode & 0o777 == 0o700


def _candidate_config(tmp_path: Path) -> PullMineConfig:
    wrapper = tmp_path / "cam-codx"
    wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
    wrapper.chmod(0o700)
    return replace(_valid_config(tmp_path), wrapper=wrapper)


def test_candidate_dispatch_uses_one_manager_packet_and_rejects_a_failed_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _candidate_config(tmp_path)
    receipt = _receipt_with_secret(tmp_path)
    packet_path = tmp_path / "packet.json"
    approval_path = tmp_path / "approval.json"
    manager_receipt_path = tmp_path / "manager-receipt.json"
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_prepare_packet(**kwargs: object) -> Path:
        calls.append(("prepare", kwargs))
        return packet_path

    def fake_issue_approval(packet: Path, **kwargs: object) -> Path:
        calls.append(("approve", {"packet": packet, **kwargs}))
        return approval_path

    def fake_execute_packet(packet: Path, **kwargs: object) -> tuple[Path, int]:
        calls.append(("execute", {"packet": packet, **kwargs}))
        return manager_receipt_path, 1

    monkeypatch.setattr(pull_mine_dir, "prepare_packet", fake_prepare_packet)
    monkeypatch.setattr(pull_mine_dir, "issue_approval", fake_issue_approval)
    monkeypatch.setattr(pull_mine_dir, "execute_packet", fake_execute_packet)

    outcome = launch_candidate_if_warranted(receipt, config, mining_succeeded=True)

    assert outcome.verdict == "candidate_rejected"
    assert outcome.packet_path == packet_path
    assert outcome.approval_path == approval_path
    assert outcome.receipt_path == manager_receipt_path
    assert [name for name, _payload in calls] == ["prepare", "approve", "execute"]
    prepared = calls[0][1]
    assert prepared["operation"] == "self-enhance-start"
    assert prepared["args"] == ["--mode", "supervised", "--max-tasks", "1", "--skip-swap"]
    assert calls[1][1]["approved_by"] == "cam-codx-pull-mine-dir invocation"
    assert calls[2][1]["approval_path"] == approval_path


@pytest.mark.parametrize(
    ("mining_succeeded", "receipt_factory"),
    [
        (False, _receipt_with_secret),
        (
            True,
            lambda tmp_path: replace(
                _receipt_with_secret(tmp_path),
                assessment=assess_meaningful_mining(
                    validated_provenance_findings=4,
                    source_repositories=2,
                    repeated_pattern_or_gap=True,
                ),
            ),
        ),
    ],
)
def test_candidate_never_dispatches_without_successful_meaningful_mining(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mining_succeeded: bool,
    receipt_factory: object,
) -> None:
    config = _candidate_config(tmp_path)
    receipt = receipt_factory(tmp_path)  # type: ignore[operator]

    def unexpected_manager_call(**_kwargs: object) -> Path:
        raise AssertionError("manager must not be called")

    monkeypatch.setattr(pull_mine_dir, "prepare_packet", unexpected_manager_call)
    outcome = launch_candidate_if_warranted(receipt, config, mining_succeeded=mining_succeeded)

    assert outcome.verdict.startswith("not_run")


def test_candidate_arguments_cannot_include_swap_model_or_secret_controls(tmp_path: Path) -> None:
    config = _candidate_config(tmp_path)
    outcome = launch_candidate_if_warranted(
        _receipt_with_secret(tmp_path), config, mining_succeeded=False
    )

    forbidden = {"swap", "rollback", "models", "profile", "--force", "SENTINEL_SECRET"}
    assert forbidden.isdisjoint(outcome.args)
    assert outcome.args == ("--mode", "supervised", "--max-tasks", "1", "--skip-swap")


def test_cli_help_exposes_the_default_source_root() -> None:
    parser = build_parser()

    assert str(DEFAULT_SOURCE_ROOT) in parser.format_help()


def test_cli_script_help_runs_from_its_documented_absolute_path() -> None:
    script = Path(__file__).parents[1] / "tools" / "cam_pull_mine_dir.py"

    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=Path(__file__).parents[1],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "--source-root" in completed.stdout


def test_cli_argument_builder_preserves_explicit_source_root(tmp_path: Path) -> None:
    config = _valid_config(tmp_path, source_root=tmp_path / "other-user-root")
    parser = build_parser()
    args = parser.parse_args(
        [
            "--source-root",
            str(config.source_root),
            "--cam-command",
            str(config.cam_command),
            "--cam-db",
            str(config.cam_db),
            "--cam-config",
            str(config.cam_config),
            "--state-dir",
            str(config.state_dir),
            "--exact-model",
            str(config.exact_model),
            "--max-cost-usd",
            str(config.max_cost_usd),
        ]
    )

    assert build_config_from_args(args).source_root == config.source_root


def test_dry_run_writes_report_without_fetch_pull_mining_or_candidate(tmp_path: Path) -> None:
    config = _valid_config(tmp_path)
    (config.source_root / "sample" / ".git").mkdir(parents=True)
    runner = FakeGitRunner()

    def unexpected_mining_runner(**_kwargs: object) -> CommandResult:
        raise AssertionError("dry-run must not invoke CAM mining")

    result = run_pull_mine_directory(
        config,
        dry_run=True,
        git_runner=runner,
        mining_runner=unexpected_mining_runner,
    )

    assert result.json_path.is_file()
    assert result.markdown_path.is_file()
    assert all("fetch" not in call and "pull" not in call for call in runner.calls)
    assert "not_run_dry_run" in result.json_path.read_text(encoding="utf-8")
