"""Contracts for the bounded CAM pull, mine, and review workflow.

This module deliberately keeps its first layer side-effect free.  Command
execution, database writes, and candidate dispatch are added in later tasks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import tomllib
from typing import Any


DEFAULT_SOURCE_ROOT = Path("/Volumes/WS4TB/waswiki/repos2mine/repo622sn")
_LOCAL_DEFAULT_KEYS = {"exact_model", "max_repos", "max_minutes", "max_cost_usd"}


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
