from dataclasses import replace
from pathlib import Path

import pytest

from tools.cam_pull_mine_dir import (
    DEFAULT_SOURCE_ROOT,
    PullMineConfig,
    assess_meaningful_mining,
    load_local_defaults,
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
