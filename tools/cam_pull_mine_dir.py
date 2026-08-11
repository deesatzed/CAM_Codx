"""Contracts for the bounded CAM pull, mine, and review workflow.

This module deliberately keeps its first layer side-effect free.  Command
execution, database writes, and candidate dispatch are added in later tasks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import subprocess
import tomllib
from typing import Any, Callable, Literal


DEFAULT_SOURCE_ROOT = Path("/Volumes/WS4TB/waswiki/repos2mine/repo622sn")
_LOCAL_DEFAULT_KEYS = {"exact_model", "max_repos", "max_minutes", "max_cost_usd"}


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


CommandRunner = Callable[[list[str]], CommandResult]
MiningCommandRunner = Callable[..., CommandResult]


@dataclass(frozen=True)
class PullMineConfig:
    source_root: Path
    cam_command: Path
    cam_db: Path
    cam_config: Path
    profiles: Path | None
    wrapper: Path | None
    state_dir: Path
    exact_model: str | None
    max_repos: int
    max_minutes: int
    max_cost_usd: float | None

    def to_dict(self) -> dict[str, Any]:
        values = asdict(self)
        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in values.items()
        }


@dataclass(frozen=True)
class CorpusSnapshot:
    methodology_count: int
    ledger_entries: int
    integrity: str

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass(frozen=True)
class MeaningfulAssessment:
    is_meaningful: bool
    findings: int
    source_repositories: int
    repeated_pattern_or_gap: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Eligibility:
    status: Literal["eligible", "skipped", "failed"]
    branch: str | None
    reason: str


@dataclass(frozen=True)
class RepositoryUpdate:
    path: Path
    branch: str | None
    status: Literal["updated", "already_current", "skipped", "failed"]
    reason: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "path": str(self.path),
            "branch": self.branch,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MiningExecution:
    scan: CommandResult
    live: CommandResult | None


def load_local_defaults(path: Path | None) -> dict[str, str | int | float]:
    """Load explicit, non-secret operational defaults from a TOML file."""
    if path is None:
        return {}
    if not path.is_file():
        raise ValueError(f"local defaults file does not exist: {path}")

    with path.open("rb") as handle:
        loaded = tomllib.load(handle)
    unexpected = set(loaded).difference(_LOCAL_DEFAULT_KEYS)
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise ValueError(f"unsupported local defaults: {names}")

    defaults: dict[str, str | int | float] = {}
    for key, value in loaded.items():
        if key == "exact_model":
            if not isinstance(value, str) or not value.strip():
                raise ValueError("exact_model must be a non-empty string")
        elif key in {"max_repos", "max_minutes"}:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{key} must be an integer")
        elif key == "max_cost_usd":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError("max_cost_usd must be a number")
            value = float(value)
        defaults[key] = value
    return defaults


def validate_config(config: PullMineConfig) -> PullMineConfig:
    """Validate local paths and all-or-nothing provider budget boundaries."""
    if not config.source_root.is_dir():
        raise ValueError(f"source_root does not exist or is not a directory: {config.source_root}")
    if not config.cam_command.is_file():
        raise ValueError(f"cam_command does not exist: {config.cam_command}")
    if not os.access(config.cam_command, os.X_OK):
        raise ValueError(f"cam_command is not executable: {config.cam_command}")
    for field_name, path in (("cam_db", config.cam_db), ("cam_config", config.cam_config)):
        if not path.is_file():
            raise ValueError(f"{field_name} does not exist: {path}")
    if config.profiles is not None and not config.profiles.is_file():
        raise ValueError(f"profiles does not exist: {config.profiles}")
    if config.wrapper is not None:
        if not config.wrapper.is_file():
            raise ValueError(f"wrapper does not exist: {config.wrapper}")
        if not os.access(config.wrapper, os.X_OK):
            raise ValueError(f"wrapper is not executable: {config.wrapper}")
    if not config.state_dir.parent.is_dir():
        raise ValueError(f"state_dir parent does not exist: {config.state_dir.parent}")
    if config.max_repos <= 0:
        raise ValueError("max_repos must be positive")
    if config.max_minutes <= 0:
        raise ValueError("max_minutes must be positive")
    if config.max_cost_usd is not None and config.max_cost_usd <= 0:
        raise ValueError("max_cost_usd must be positive")
    if config.max_cost_usd is not None and not config.exact_model:
        raise ValueError("exact_model is required when max_cost_usd is set")
    if config.exact_model and config.max_cost_usd is None:
        raise ValueError("max_cost_usd is required when exact_model is set")
    return config


def assess_meaningful_mining(
    *,
    validated_provenance_findings: int,
    source_repositories: int,
    repeated_pattern_or_gap: bool,
) -> MeaningfulAssessment:
    """Apply the agreed threshold before a candidate test can be considered."""
    reasons: list[str] = []
    if validated_provenance_findings < 5:
        reasons.append("fewer than five validated, provenance-bearing findings")
    if source_repositories < 2:
        reasons.append("findings span fewer than two repositories")
    if not repeated_pattern_or_gap:
        reasons.append("no concrete repeated pattern or capability gap was identified")
    if not reasons:
        reasons.append("all meaningful-mining evidence gates were met")
    return MeaningfulAssessment(
        is_meaningful=len(reasons) == 1 and reasons[0].startswith("all "),
        findings=validated_provenance_findings,
        source_repositories=source_repositories,
        repeated_pattern_or_gap=repeated_pattern_or_gap,
        reasons=tuple(reasons),
    )


def discover_git_repositories(root: Path) -> tuple[Path, ...]:
    """Find nested Git worktrees without executing project code."""
    repositories: list[Path] = []
    for current, directories, files in os.walk(root):
        if ".git" in directories or ".git" in files:
            repositories.append(Path(current))
        directories[:] = [directory for directory in directories if directory != ".git"]
    return tuple(sorted(repositories, key=lambda path: path.relative_to(root).as_posix()))


def _git_argv(repo: Path, *args: str) -> list[str]:
    return ["git", "-C", str(repo), *args]


def inspect_update_eligibility(repo: Path, runner: CommandRunner) -> Eligibility:
    """Fail closed unless a repository is clean, attached, and tracks upstream."""
    status_result = runner(_git_argv(repo, "status", "--porcelain=v1", "--branch"))
    if status_result.returncode != 0:
        return Eligibility("failed", None, "git status inspection failed")
    status_lines = status_result.stdout.splitlines()
    changes = status_lines[1:] if status_lines[:1] and status_lines[0].startswith("##") else status_lines
    if any(line.startswith(("UU", "AA", "DD", "AU", "UD", "UA", "DU")) for line in changes):
        return Eligibility("skipped", None, "repository has unresolved conflicts")
    if changes:
        return Eligibility("skipped", None, "repository is dirty")

    branch_result = runner(_git_argv(repo, "rev-parse", "--abbrev-ref", "HEAD"))
    if branch_result.returncode != 0:
        return Eligibility("failed", None, "git branch inspection failed")
    branch = branch_result.stdout.strip()
    if not branch or branch == "HEAD":
        return Eligibility("skipped", None, "repository is detached")

    upstream_result = runner(
        _git_argv(repo, "rev-parse", "--abbrev-ref", "@{upstream}")
    )
    if upstream_result.returncode != 0 or not upstream_result.stdout.strip():
        return Eligibility("skipped", branch, "repository has no upstream")
    return Eligibility("eligible", branch, "clean attached repository with upstream")


def update_repository(repo: Path, runner: CommandRunner) -> RepositoryUpdate:
    """Perform the only permitted update: fetch followed by pull --ff-only."""
    eligibility = inspect_update_eligibility(repo, runner)
    if eligibility.status != "eligible":
        return RepositoryUpdate(
            path=repo,
            branch=eligibility.branch,
            status=eligibility.status,
            reason=eligibility.reason,
        )

    fetch_result = runner(_git_argv(repo, "fetch", "origin"))
    if fetch_result.returncode != 0:
        return RepositoryUpdate(repo, eligibility.branch, "failed", "git fetch failed")

    pull_result = runner(_git_argv(repo, "pull", "--ff-only"))
    if pull_result.returncode != 0:
        return RepositoryUpdate(
            repo,
            eligibility.branch,
            "failed",
            "git pull --ff-only fast-forward failed",
        )
    if "Already up to date" in pull_result.stdout:
        return RepositoryUpdate(repo, eligibility.branch, "already_current", "already current")
    return RepositoryUpdate(repo, eligibility.branch, "updated", "fast-forward update completed")


def _base_mining_argv(config: PullMineConfig) -> list[str]:
    return [
        str(config.cam_command),
        "mine-workspace",
        str(config.source_root),
        "--target",
        str(config.source_root),
        "--changed-only",
        "--no-tasks",
        "--max-repos",
        str(config.max_repos),
        "--max-minutes",
        str(config.max_minutes),
        "--config",
        str(config.cam_config),
    ]


def build_scan_argv(config: PullMineConfig) -> list[str]:
    """Build the no-provider scan command, with no task generation."""
    command = _base_mining_argv(config)
    command.insert(6, "--scan-only")
    return command


def build_live_argv(config: PullMineConfig, receipt_path: Path) -> list[str]:
    """Build the capped live command only after configuration validation."""
    validate_config(config)
    if config.exact_model is None or config.max_cost_usd is None:
        raise ValueError("live mining requires exact_model and max_cost_usd")
    command = _base_mining_argv(config)
    if config.profiles is not None:
        command.extend(["--profiles", str(config.profiles)])
    command.extend(
        [
            "--max-cost-usd",
            str(config.max_cost_usd),
            "--exact-model",
            config.exact_model,
            "--budget-receipt",
            str(receipt_path),
        ]
    )
    return command


def pinned_cam_environment(config: PullMineConfig) -> dict[str, str]:
    """Preserve the parent environment while pinning both CAM database paths."""
    environment = dict(os.environ)
    environment["CLAW_DB_PATH"] = str(config.cam_db)
    environment["CAM_CODEX_MCP_DB_PATH"] = str(config.cam_db)
    return environment


def _subprocess_mining_runner(
    argv: list[str], *, cwd: Path, env: dict[str, str]
) -> CommandResult:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def run_scan_then_live(
    config: PullMineConfig,
    receipt_path: Path,
    *,
    runner: MiningCommandRunner = _subprocess_mining_runner,
) -> MiningExecution:
    """Run a scan first and only start live mining after a successful scan."""
    validate_config(config)
    environment = pinned_cam_environment(config)
    cwd = config.cam_command.parent.parent
    scan = runner(build_scan_argv(config), cwd=cwd, env=environment)
    if scan.returncode != 0:
        return MiningExecution(scan=scan, live=None)
    live = runner(build_live_argv(config, receipt_path), cwd=cwd, env=environment)
    return MiningExecution(scan=scan, live=live)
