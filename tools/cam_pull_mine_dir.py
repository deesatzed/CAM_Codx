"""Contracts for the bounded CAM pull, mine, and review workflow.

This module deliberately keeps its first layer side-effect free.  Command
execution, database writes, and candidate dispatch are added in later tasks.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
import tomllib
from typing import Any, Callable, Literal

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cam_manager import execute_packet, issue_approval, prepare_packet


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
    ledger_entries: int | None
    integrity: str
    methodology_ids: frozenset[str] = frozenset()
    methodology_sources: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, int | str | None]:
        return {
            "methodology_count": self.methodology_count,
            "ledger_entries": self.ledger_entries,
            "integrity": self.integrity,
        }


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
    status: Literal["updated", "already_current", "planned", "skipped", "failed"]
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


@dataclass(frozen=True)
class CommandSummary:
    returncode: int
    stdout_digest: str
    stderr_digest: str
    stdout_summary: str
    stderr_summary: str

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass(frozen=True)
class MiningDelta:
    methodologies_added: int
    ledger_entries_added: int | None
    findings: int
    source_repositories: frozenset[str]

    def to_dict(self) -> dict[str, int | None | list[str]]:
        return {
            "methodologies_added": self.methodologies_added,
            "ledger_entries_added": self.ledger_entries_added,
            "findings": self.findings,
            "source_repositories": sorted(self.source_repositories),
        }


@dataclass(frozen=True)
class PullMineReceipt:
    source_root: Path
    database_fingerprint: str
    config_fingerprint: str
    before: CorpusSnapshot
    after: CorpusSnapshot
    delta: MiningDelta
    updates: tuple[RepositoryUpdate, ...]
    assessment: MeaningfulAssessment
    scan: CommandSummary
    live: CommandSummary | None
    candidate_verdict: str
    redaction_values: tuple[str, ...] = ()
    candidate_packet_path: Path | None = None
    candidate_approval_path: Path | None = None
    candidate_receipt_path: Path | None = None
    candidate_returncode: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_root": str(self.source_root),
            "database_fingerprint": self.database_fingerprint,
            "config_fingerprint": self.config_fingerprint,
            "before": self.before.to_dict(),
            "after": self.after.to_dict(),
            "delta": self.delta.to_dict(),
            "updates": [update.to_dict() for update in self.updates],
            "assessment": self.assessment.to_dict(),
            "scan": self.scan.to_dict(),
            "live": self.live.to_dict() if self.live is not None else None,
            "candidate_verdict": self.candidate_verdict,
            "candidate_packet_path": str(self.candidate_packet_path)
            if self.candidate_packet_path is not None
            else None,
            "candidate_approval_path": str(self.candidate_approval_path)
            if self.candidate_approval_path is not None
            else None,
            "candidate_receipt_path": str(self.candidate_receipt_path)
            if self.candidate_receipt_path is not None
            else None,
            "candidate_returncode": self.candidate_returncode,
        }
        return _redact_value(payload, self.redaction_values)


@dataclass(frozen=True)
class CandidateOutcome:
    verdict: Literal[
        "not_run_mining_failed",
        "not_run_not_meaningful",
        "not_run_wrapper_unavailable",
        "candidate_dispatch_failed",
        "candidate_rejected",
        "candidate_completed_no_swap",
    ]
    args: tuple[str, ...]
    packet_path: Path | None = None
    approval_path: Path | None = None
    receipt_path: Path | None = None
    returncode: int | None = None


@dataclass(frozen=True)
class PullMineRun:
    receipt: PullMineReceipt
    json_path: Path
    markdown_path: Path


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


def fingerprint_file(path: Path) -> str:
    """Return a content digest without placing file contents in a receipt."""
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _load_ledger_snapshot(
    ledger_path: Path | None,
) -> tuple[int | None, tuple[tuple[str, str], ...]]:
    if ledger_path is None or not ledger_path.is_file():
        return None, ()
    try:
        payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, ()
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, dict):
        return None, ()

    sources: set[tuple[str, str]] = set()
    for record_key, record in records.items():
        if not isinstance(record, dict):
            continue
        repository = record.get("repo_name")
        if not isinstance(repository, str) or not repository.strip():
            repository = str(record_key)
        methodology_ids = record.get("methodology_ids", [])
        if not isinstance(methodology_ids, list):
            continue
        for methodology_id in methodology_ids:
            if isinstance(methodology_id, str) and methodology_id.strip():
                sources.add((methodology_id, repository))
    return len(records), tuple(sorted(sources))


def snapshot_corpus(db: Path, ledger_path: Path | None) -> CorpusSnapshot:
    """Read a corpus snapshot without allowing SQLite writes or migrations."""
    if not db.is_file():
        raise ValueError(f"corpus database does not exist: {db}")
    uri = f"{db.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.execute("PRAGMA query_only=ON")
        integrity_row = connection.execute("PRAGMA integrity_check").fetchone()
        integrity = str(integrity_row[0]) if integrity_row else "unavailable"
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(methodologies)").fetchall()
        }
        if "id" not in columns:
            raise ValueError("corpus database is missing methodologies.id")
        methodology_ids = frozenset(
            str(row[0])
            for row in connection.execute("SELECT id FROM methodologies").fetchall()
            if row[0] is not None
        )
    ledger_entries, methodology_sources = _load_ledger_snapshot(ledger_path)
    return CorpusSnapshot(
        methodology_count=len(methodology_ids),
        ledger_entries=ledger_entries,
        integrity=integrity,
        methodology_ids=methodology_ids,
        methodology_sources=methodology_sources,
    )


def derive_mining_delta(before: CorpusSnapshot, after: CorpusSnapshot) -> MiningDelta:
    """Derive only provenance-backed findings newly present after mining."""
    new_methodology_ids = after.methodology_ids.difference(before.methodology_ids)
    source_repositories = frozenset(
        repository
        for methodology_id, repository in after.methodology_sources
        if methodology_id in new_methodology_ids
    )
    provenance_backed_ids = {
        methodology_id
        for methodology_id, _repository in after.methodology_sources
        if methodology_id in new_methodology_ids
    }
    ledger_entries_added = (
        None
        if before.ledger_entries is None or after.ledger_entries is None
        else after.ledger_entries - before.ledger_entries
    )
    return MiningDelta(
        methodologies_added=after.methodology_count - before.methodology_count,
        ledger_entries_added=ledger_entries_added,
        findings=len(provenance_backed_ids),
        source_repositories=source_repositories,
    )


def _redact_text(value: str, redaction_values: tuple[str, ...]) -> str:
    redacted = value
    for secret in redaction_values:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def _redact_value(value: Any, redaction_values: tuple[str, ...]) -> Any:
    if isinstance(value, str):
        return _redact_text(value, redaction_values)
    if isinstance(value, list):
        return [_redact_value(item, redaction_values) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item, redaction_values) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _redact_value(item, redaction_values)
            for key, item in value.items()
        }
    return value


def summarize_command_result(
    result: CommandResult,
    *,
    redaction_values: tuple[str, ...] = (),
    summary_limit: int = 320,
) -> CommandSummary:
    """Keep command evidence digest-only with bounded, redacted summaries."""
    def summarize(value: str) -> str:
        normalized = " ".join(_redact_text(value, redaction_values).split())
        return normalized[:summary_limit]

    return CommandSummary(
        returncode=result.returncode,
        stdout_digest=f"sha256:{sha256(result.stdout.encode()).hexdigest()}",
        stderr_digest=f"sha256:{sha256(result.stderr.encode()).hexdigest()}",
        stdout_summary=summarize(result.stdout),
        stderr_summary=summarize(result.stderr),
    )


def render_markdown_report(receipt: PullMineReceipt) -> str:
    """Render a human-readable, redacted report from a durable receipt."""
    lines = [
        "# CAM Pull/Mine Directory Receipt",
        "",
        "## Scope",
        "",
        f"- Source root: `{receipt.source_root}`",
        f"- Database fingerprint: `{receipt.database_fingerprint}`",
        f"- Config fingerprint: `{receipt.config_fingerprint}`",
        "",
        "## Repository updates",
        "",
        "| Repository | Branch | Status | Reason |",
        "|---|---|---|---|",
    ]
    for update in receipt.updates:
        lines.append(
            f"| `{update.path}` | {update.branch or '-'} | {update.status} | {update.reason} |"
        )
    if not receipt.updates:
        lines.append("| - | - | none | no Git repositories were discovered |")
    lines.extend(
        [
            "",
            "## Corpus evidence",
            "",
            f"- Integrity: before `{receipt.before.integrity}`, after `{receipt.after.integrity}`",
            f"- Methodologies: before {receipt.before.methodology_count}, after {receipt.after.methodology_count}, delta {receipt.delta.methodologies_added}",
            f"- Ledger entries: before {receipt.before.ledger_entries if receipt.before.ledger_entries is not None else 'unavailable'}, after {receipt.after.ledger_entries if receipt.after.ledger_entries is not None else 'unavailable'}, delta {receipt.delta.ledger_entries_added if receipt.delta.ledger_entries_added is not None else 'unavailable'}",
            f"- Provenance-backed new findings: {receipt.delta.findings}",
            f"- Source repositories: {', '.join(sorted(receipt.delta.source_repositories)) or 'none'}",
            "",
            "## Meaningfulness gate",
            "",
            f"- Verdict: {'meaningful' if receipt.assessment.is_meaningful else 'not meaningful'}",
        ]
    )
    lines.extend(f"- Reason: {reason}" for reason in receipt.assessment.reasons)
    lines.extend(
        [
            "",
            "## Candidate",
            "",
            f"- Candidate verdict: {receipt.candidate_verdict}",
        ]
    )
    if receipt.candidate_packet_path is not None:
        lines.append(f"- Packet: `{receipt.candidate_packet_path}`")
    if receipt.candidate_approval_path is not None:
        lines.append(f"- Approval: `{receipt.candidate_approval_path}`")
    if receipt.candidate_receipt_path is not None:
        lines.append(f"- Manager receipt: `{receipt.candidate_receipt_path}`")
    if receipt.candidate_returncode is not None:
        lines.append(f"- Candidate return code: {receipt.candidate_returncode}")
    lines.append("")
    return _redact_text("\n".join(lines), receipt.redaction_values)


def write_report(receipt: PullMineReceipt, output_dir: Path) -> tuple[Path, Path]:
    """Persist redacted JSON and Markdown reports with private local modes."""
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    output_dir.chmod(0o700)
    payload = json.dumps(receipt.to_dict(), indent=2, sort_keys=True)
    receipt_id = sha256(payload.encode()).hexdigest()[:12]
    json_path = output_dir / f"pull-mine-{receipt_id}.json"
    markdown_path = output_dir / f"pull-mine-{receipt_id}.md"
    json_path.write_text(payload + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown_report(receipt), encoding="utf-8")
    json_path.chmod(0o600)
    markdown_path.chmod(0o600)
    return json_path, markdown_path


_CANDIDATE_ARGS = ("--mode", "supervised", "--max-tasks", "1", "--skip-swap")


def launch_candidate_if_warranted(
    receipt: PullMineReceipt,
    config: PullMineConfig,
    *,
    mining_succeeded: bool,
) -> CandidateOutcome:
    """Dispatch one supervised no-swap candidate only after all evidence gates."""
    if not mining_succeeded:
        return CandidateOutcome("not_run_mining_failed", _CANDIDATE_ARGS)
    if not receipt.assessment.is_meaningful:
        return CandidateOutcome("not_run_not_meaningful", _CANDIDATE_ARGS)
    if config.wrapper is None:
        return CandidateOutcome("not_run_wrapper_unavailable", _CANDIDATE_ARGS)

    workflow_seed = json.dumps(receipt.to_dict(), sort_keys=True, separators=(",", ":"))
    workflow_id = f"pull-mine-{sha256(workflow_seed.encode()).hexdigest()[:16]}"
    try:
        packet_path = prepare_packet(
            operation="self-enhance-start",
            wrapper=config.wrapper,
            args=list(_CANDIDATE_ARGS),
            workflow_id=workflow_id,
            target_repo=None,
            budget_usd=0.0,
            state_dir=config.state_dir,
        )
        approval_path = issue_approval(
            packet_path,
            state_dir=config.state_dir,
            approved_by="cam-codx-pull-mine-dir invocation",
        )
        manager_receipt_path, returncode = execute_packet(
            packet_path,
            state_dir=config.state_dir,
            wrapper=config.wrapper,
            approval_path=approval_path,
        )
    except Exception:
        return CandidateOutcome("candidate_dispatch_failed", _CANDIDATE_ARGS)

    if returncode != 0:
        return CandidateOutcome(
            "candidate_rejected",
            _CANDIDATE_ARGS,
            packet_path=packet_path,
            approval_path=approval_path,
            receipt_path=manager_receipt_path,
            returncode=returncode,
        )
    return CandidateOutcome(
        "candidate_completed_no_swap",
        _CANDIDATE_ARGS,
        packet_path=packet_path,
        approval_path=approval_path,
        receipt_path=manager_receipt_path,
        returncode=returncode,
    )


def _subprocess_git_runner(argv: list[str]) -> CommandResult:
    completed = subprocess.run(
        argv,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _dry_run_update(repo: Path, runner: CommandRunner) -> RepositoryUpdate:
    eligibility = inspect_update_eligibility(repo, runner)
    if eligibility.status == "eligible":
        return RepositoryUpdate(
            path=repo,
            branch=eligibility.branch,
            status="planned",
            reason="eligible; dry-run did not fetch or pull",
        )
    return RepositoryUpdate(
        path=repo,
        branch=eligibility.branch,
        status=eligibility.status,
        reason=eligibility.reason,
    )


def _initial_dry_run_receipt(
    config: PullMineConfig,
    updates: tuple[RepositoryUpdate, ...],
) -> PullMineReceipt:
    assessment = assess_meaningful_mining(
        validated_provenance_findings=0,
        source_repositories=0,
        repeated_pattern_or_gap=False,
    )
    planned = CommandSummary(
        returncode=0,
        stdout_digest="not-run",
        stderr_digest="not-run",
        stdout_summary="dry-run planned a scan-only CAM command",
        stderr_summary="",
    )
    snapshot = CorpusSnapshot(0, None, "not_checked")
    return PullMineReceipt(
        source_root=config.source_root,
        database_fingerprint=fingerprint_file(config.cam_db),
        config_fingerprint=fingerprint_file(config.cam_config),
        before=snapshot,
        after=snapshot,
        delta=MiningDelta(0, None, 0, frozenset()),
        updates=updates,
        assessment=assessment,
        scan=planned,
        live=None,
        candidate_verdict="not_run_dry_run",
    )


def _budget_receipt_path(config: PullMineConfig) -> Path:
    budgets_dir = config.state_dir / "budgets"
    budgets_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    budgets_dir.chmod(0o700)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return budgets_dir / f"mine-workspace-{timestamp}.json"


def run_pull_mine_directory(
    config: PullMineConfig,
    *,
    dry_run: bool,
    repeated_pattern_or_gap: bool = False,
    git_runner: CommandRunner = _subprocess_git_runner,
    mining_runner: MiningCommandRunner = _subprocess_mining_runner,
) -> PullMineRun:
    """Coordinate the bounded workflow and always return redacted report paths."""
    validate_config(config)
    repositories = discover_git_repositories(config.source_root)
    updates = tuple(
        _dry_run_update(repository, git_runner)
        if dry_run
        else update_repository(repository, git_runner)
        for repository in repositories
    )
    reports_dir = config.state_dir / "reports"
    if dry_run:
        receipt = _initial_dry_run_receipt(config, updates)
        json_path, markdown_path = write_report(receipt, reports_dir)
        return PullMineRun(receipt, json_path, markdown_path)

    ledger_path = config.cam_db.parent / "mining_registry.json"
    before = snapshot_corpus(config.cam_db, ledger_path)
    if before.integrity != "ok":
        raise ValueError(f"corpus integrity check failed before mining: {before.integrity}")
    execution = run_scan_then_live(
        config,
        _budget_receipt_path(config),
        runner=mining_runner,
    )
    after = snapshot_corpus(config.cam_db, ledger_path)
    delta = derive_mining_delta(before, after)
    assessment = assess_meaningful_mining(
        validated_provenance_findings=delta.findings,
        source_repositories=len(delta.source_repositories),
        repeated_pattern_or_gap=repeated_pattern_or_gap,
    )
    receipt = PullMineReceipt(
        source_root=config.source_root,
        database_fingerprint=fingerprint_file(config.cam_db),
        config_fingerprint=fingerprint_file(config.cam_config),
        before=before,
        after=after,
        delta=delta,
        updates=updates,
        assessment=assessment,
        scan=summarize_command_result(execution.scan),
        live=summarize_command_result(execution.live) if execution.live is not None else None,
        candidate_verdict="not_run_pending_assessment",
    )
    mining_succeeded = (
        execution.live is not None
        and execution.live.returncode == 0
        and after.integrity == "ok"
    )
    candidate = launch_candidate_if_warranted(
        receipt, config, mining_succeeded=mining_succeeded
    )
    receipt = replace(
        receipt,
        candidate_verdict=candidate.verdict,
        candidate_packet_path=candidate.packet_path,
        candidate_approval_path=candidate.approval_path,
        candidate_receipt_path=candidate.receipt_path,
        candidate_returncode=candidate.returncode,
    )
    json_path, markdown_path = write_report(receipt, reports_dir)
    return PullMineRun(receipt, json_path, markdown_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update eligible repositories, mine one pinned CAM corpus, and assess evidence."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help=f"directory containing repositories (default: {DEFAULT_SOURCE_ROOT})",
    )
    parser.add_argument("--cam-command", type=Path, required=True)
    parser.add_argument("--cam-db", type=Path, required=True)
    parser.add_argument("--cam-config", type=Path, required=True)
    parser.add_argument("--profiles", type=Path)
    parser.add_argument("--wrapper", type=Path)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--local-defaults", type=Path)
    parser.add_argument("--exact-model")
    parser.add_argument("--max-repos", type=int)
    parser.add_argument("--max-minutes", type=int)
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument(
        "--repeated-pattern-or-gap",
        action="store_true",
        help="attest that the reviewed mining evidence identifies a concrete repeated pattern or capability gap",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="inspect eligibility and write a plan report without fetch, pull, mining, or candidate dispatch",
    )
    return parser


def build_config_from_args(args: argparse.Namespace) -> PullMineConfig:
    defaults = load_local_defaults(args.local_defaults)

    def value(name: str, fallback: Any) -> Any:
        explicit = getattr(args, name)
        return explicit if explicit is not None else defaults.get(name, fallback)

    return PullMineConfig(
        source_root=args.source_root,
        cam_command=args.cam_command,
        cam_db=args.cam_db,
        cam_config=args.cam_config,
        profiles=args.profiles,
        wrapper=args.wrapper,
        state_dir=args.state_dir,
        exact_model=value("exact_model", None),
        max_repos=value("max_repos", 20),
        max_minutes=value("max_minutes", 120),
        max_cost_usd=value("max_cost_usd", None),
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = build_config_from_args(args)
        run = run_pull_mine_directory(
            config,
            dry_run=args.dry_run,
            repeated_pattern_or_gap=args.repeated_pattern_or_gap,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"JSON report: {run.json_path}")
    print(f"Markdown report: {run.markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
