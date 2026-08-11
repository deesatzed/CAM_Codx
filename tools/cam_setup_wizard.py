#!/usr/bin/env python3
"""Guided CAM hub-and-spoke setup wizard.

This script creates a local CAM_ALL overlay, clones/updates the public repos,
copies public templates into local_state, and optionally imports private runtime
state from an existing CAM_CAM build. It never writes private runtime files into
public Git repos.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


REPOS = {
    "CAM_Codx": "https://github.com/deesatzed/CAM_Codx.git",
    "CAM_CAM": "https://github.com/deesatzed/CAM_CAM.git",
    "moriahcareframe": "https://github.com/deesatzed/moriahcareframe.git",
}

TOML_CONFIGS = ("claw", "claw_cheap", "claw_dspro", "claw_grok")


@dataclass(frozen=True)
class LocalStatePaths:
    cam_home: Path
    repos: Path
    cam_cam_data: Path
    cam_cam_config: Path
    cam_cam_env: Path
    cam_codx_config: Path
    adapters: Path
    reports: Path
    clone_proofs: Path
    scripts: Path


@dataclass
class ImportResult:
    copied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


@dataclass
class CommandResult:
    command: str
    cwd: Path | None
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class CamCodxWrapper:
    path: Path
    cam_cam: Path
    cam_cli: Path
    db: Path
    config: Path
    env_file: Path
    approval_prefix: str


@dataclass(frozen=True)
class CodexSkillInstall:
    source: Path
    dest: Path


def local_state_paths(cam_home: Path) -> LocalStatePaths:
    cam_home = cam_home.expanduser().resolve()
    return LocalStatePaths(
        cam_home=cam_home,
        repos=cam_home / "repos",
        cam_cam_data=cam_home / "local_state" / "CAM_CAM" / "data",
        cam_cam_config=cam_home / "local_state" / "CAM_CAM" / "config",
        cam_cam_env=cam_home / "local_state" / "CAM_CAM" / "env",
        cam_codx_config=cam_home / "local_state" / "CAM_Codx" / "config",
        adapters=cam_home / "local_state" / "adapters",
        reports=cam_home / "reports",
        clone_proofs=cam_home / "clone_proofs",
        scripts=cam_home / "scripts",
    )


def ensure_layout(cam_home: Path, cam_archive: Path) -> LocalStatePaths:
    paths = local_state_paths(cam_home)
    for path in (
        paths.repos,
        paths.cam_cam_data,
        paths.cam_cam_config,
        paths.cam_cam_env,
        paths.cam_codx_config,
        paths.adapters,
        paths.reports,
        paths.clone_proofs,
        paths.scripts,
        cam_archive.expanduser().resolve(),
    ):
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _copy_if_exists(src: Path, dest: Path, label: str, result: ImportResult) -> None:
    if not src.exists():
        result.skipped.append(label)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    result.copied.append(label)


def import_existing_runtime_state(existing_cam_cam: Path, cam_home: Path) -> ImportResult:
    existing_cam_cam = existing_cam_cam.expanduser().resolve()
    paths = local_state_paths(cam_home)
    result = ImportResult()

    _copy_if_exists(
        existing_cam_cam / "data" / "claw.db",
        paths.cam_cam_data / "claw.db",
        "data/claw.db",
        result,
    )
    _copy_if_exists(
        existing_cam_cam / "data" / "clawBU.db",
        paths.cam_cam_data / "clawBU.db",
        "data/clawBU.db",
        result,
    )
    _copy_if_exists(existing_cam_cam / ".env", paths.cam_cam_env / ".env", ".env", result)
    env_path = paths.cam_cam_env / ".env"
    if env_path.exists():
        env_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    for name in TOML_CONFIGS:
        _copy_if_exists(
            existing_cam_cam / f"{name}.toml",
            paths.cam_cam_config / f"{name}.local.toml",
            f"{name}.toml",
            result,
        )

    return result


def copy_public_templates(cam_codx: Path, cam_home: Path) -> ImportResult:
    cam_codx = cam_codx.expanduser().resolve()
    paths = local_state_paths(cam_home)
    result = ImportResult()
    templates = cam_codx / "templates" / "config"
    copies = [
        (
            templates / "cam-codx.env.example",
            paths.cam_codx_config / "cam-codx.env",
            "templates/config/cam-codx.env.example",
        ),
        (
            templates / "cam-cam-claw.example.toml",
            paths.cam_cam_config / "claw.local.toml",
            "templates/config/cam-cam-claw.example.toml",
        ),
        (
            templates / "adapter-config.example.toml",
            paths.adapters / "adapter-config.local.toml",
            "templates/config/adapter-config.example.toml",
        ),
    ]
    for src, dest, label in copies:
        if dest.exists():
            result.skipped.append(label)
            continue
        _copy_if_exists(src, dest, label, result)
    return result


def run_command(args: list[str], cwd: Path | None = None) -> CommandResult:
    proc = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(
        command=" ".join(args),
        cwd=cwd,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
    )


def clone_or_update_repos(cam_home: Path) -> list[CommandResult]:
    paths = local_state_paths(cam_home)
    results: list[CommandResult] = []
    for name, remote in REPOS.items():
        dest = paths.repos / name
        if (dest / ".git").is_dir():
            results.append(run_command(["git", "fetch", "origin"], cwd=dest))
            results.append(run_command(["git", "pull", "--ff-only"], cwd=dest))
        else:
            results.append(run_command(["git", "clone", remote, str(dest)]))
    return results


def repo_statuses(cam_home: Path) -> list[CommandResult]:
    paths = local_state_paths(cam_home)
    return [
        run_command(["git", "status", "--short", "--branch"], cwd=paths.repos / name)
        for name in REPOS
        if (paths.repos / name / ".git").is_dir()
    ]


def validate_local_state(cam_home: Path) -> list[str]:
    paths = local_state_paths(cam_home)
    lines: list[str] = []
    for path in sorted(paths.cam_cam_data.glob("*")):
        lines.append(f"data: {path.name} ({path.stat().st_size} bytes)")
    for path in sorted(paths.cam_cam_config.glob("*.toml")):
        lines.append(f"config: {path.name}")
    if (paths.cam_cam_env / ".env").exists():
        lines.append("env: .env present with private permissions expected")
    return lines


def _shell(value: Path | str) -> str:
    return shlex.quote(str(value))


def create_cam_codx_wrapper(
    cam_home: Path,
    cam_cam: Path,
    db: Path,
    config: Path,
    env_file: Path,
) -> CamCodxWrapper:
    paths = local_state_paths(cam_home)
    cam_cam = cam_cam.expanduser().resolve()
    db = db.expanduser().resolve()
    config = config.expanduser().resolve()
    env_file = env_file.expanduser().resolve()
    cam_cli = cam_cam / ".venv" / "bin" / "cam"
    wrapper = paths.scripts / "cam-codx"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    body = f"""#!/usr/bin/env bash
set -euo pipefail

CAM_CAM={_shell(cam_cam)}
CAM_CLI={_shell(cam_cli)}
CLAW_DB={_shell(db)}
CLAW_CONFIG={_shell(config)}
CAM_ENV={_shell(env_file)}

for required in "$CAM_CLI" "$CLAW_DB" "$CLAW_CONFIG" "$CAM_ENV"; do
  if [ ! -e "$required" ]; then
    echo "cam-codx missing required path: $required" >&2
    exit 2
  fi
done

cd "$CAM_CAM"
set -a
source "$CAM_ENV"
set +a
export CLAW_DB_PATH="$CLAW_DB"
export CAM_CODEX_MCP_DB_PATH="$CLAW_DB"

has_config=0
for arg in "$@"; do
  if [ "$arg" = "-c" ] || [ "$arg" = "--config" ] || [[ "$arg" == --config=* ]]; then
    has_config=1
  fi
done

if [ "$has_config" = "1" ]; then
  exec "$CAM_CLI" "$@"
fi
exec "$CAM_CLI" "$@" -c "$CLAW_CONFIG"
"""
    wrapper.write_text(body, encoding="utf-8")
    wrapper.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return CamCodxWrapper(
        path=wrapper,
        cam_cam=cam_cam,
        cam_cli=cam_cli,
        db=db,
        config=config,
        env_file=env_file,
        approval_prefix=str(wrapper),
    )


def create_default_cam_codx_wrapper(cam_home: Path) -> CamCodxWrapper | None:
    paths = local_state_paths(cam_home)
    cam_cam_roots = [
        cam_home.expanduser().resolve() / "CAM_CAM",
        paths.repos / "CAM_CAM",
    ]
    for cam_cam in cam_cam_roots:
        candidates = [
            (
                paths.cam_cam_data / "claw.db",
                paths.cam_cam_config / "claw.local.toml",
                paths.cam_cam_env / ".env",
            ),
            (
                cam_cam / "claw.db",
                cam_cam / "claw.toml",
                cam_cam / ".env",
            ),
            (
                cam_cam / "data" / "claw.db",
                cam_cam / "claw.toml",
                cam_cam / ".env",
            ),
        ]
        for db, config, env_file in candidates:
            if (cam_cam / ".venv" / "bin" / "cam").exists() and db.exists() and config.exists() and env_file.exists():
                return create_cam_codx_wrapper(cam_home, cam_cam, db, config, env_file)
    return None


def install_codex_skill(source: Path, codex_home: Path) -> Path:
    source = source.expanduser().resolve()
    codex_home = codex_home.expanduser().resolve()
    dest = codex_home / "skills" / source.name
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"skill template missing SKILL.md: {source}")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    return dest


def install_codex_skills(source_root: Path, codex_home: Path) -> list[CodexSkillInstall]:
    """Install the setup, routine SWE, brief, and pull/mine skills together."""

    source_root = source_root.expanduser().resolve()
    installs: list[CodexSkillInstall] = []
    for name in (
        "cam-codx-setup",
        "cam-codx-swe",
        "cam-codx-development-brief",
        "cam-codx-pull-mine-dir",
    ):
        source = source_root / name
        if not (source / "SKILL.md").is_file():
            # Older CAM_Codx checkouts may predate the routine skill. Keep setup
            # usable and let the report name the missing optional asset.
            continue
        installs.append(
            CodexSkillInstall(
                source=source,
                dest=install_codex_skill(source, codex_home),
            )
        )
    if not installs:
        raise FileNotFoundError(f"no CAM Codex skill templates found under {source_root}")
    return installs


def write_report(
    cam_home: Path,
    cam_archive: Path,
    clone_results: list[CommandResult],
    template_result: ImportResult,
    import_result: ImportResult | None,
    wrapper: CamCodxWrapper | None = None,
    skill_install: CodexSkillInstall | None = None,
    skill_installs: list[CodexSkillInstall] | None = None,
) -> Path:
    paths = local_state_paths(cam_home)
    report = paths.reports / "setup_report.md"
    status_results = repo_statuses(cam_home)
    lines = [
        "# CAM Setup Wizard Report",
        "",
        f"- CAM_HOME: `{paths.cam_home}`",
        f"- CAM_ARCHIVE: `{cam_archive.expanduser().resolve()}`",
        "",
        "## Clone Or Update Results",
        "",
    ]
    for item in clone_results:
        lines.append(f"- `{item.command}` -> `{item.returncode}`")
        if item.stderr:
            lines.append(f"  - stderr: `{item.stderr.splitlines()[-1]}`")
    lines.extend(["", "## Template Copies", ""])
    lines.extend(f"- copied `{item}`" for item in template_result.copied)
    lines.extend(f"- skipped `{item}`" for item in template_result.skipped)
    if import_result is not None:
        lines.extend(["", "## Existing Runtime Import", ""])
        lines.extend(f"- copied `{item}`" for item in import_result.copied)
        lines.extend(f"- skipped `{item}`" for item in import_result.skipped)
    lines.extend(["", "## Codex CAM Wrapper", ""])
    if wrapper is None:
        lines.append("- not created")
        lines.append("- create after CAM_CAM `.venv/bin/cam`, `.env`, `claw.db`, and `claw.toml` exist")
    else:
        lines.append(f"- wrapper: `{wrapper.path}`")
        lines.append(f"- CAM_CAM: `{wrapper.cam_cam}`")
        lines.append(f"- DB: `{wrapper.db}`")
        lines.append(f"- config: `{wrapper.config}`")
        lines.append(f"- env file: `{wrapper.env_file}`")
        lines.append(f"- Codex approval prefix: `{wrapper.approval_prefix}`")
    lines.extend(["", "## Codex Skill Install", ""])
    installed_skills = list(skill_installs or ([] if skill_install is None else [skill_install]))
    if not installed_skills:
        lines.append("- not installed")
    else:
        for installed in installed_skills:
            lines.append(f"- source: `{installed.source}`")
            lines.append(f"- installed: `{installed.dest}`")
    lines.extend(["", "## Local State", ""])
    local_state = validate_local_state(cam_home)
    lines.extend(f"- {item}" for item in local_state) if local_state else lines.append("- empty")
    lines.extend(["", "## Public Repo Status", ""])
    for item in status_results:
        lines.append(f"### {item.cwd.name if item.cwd else 'repo'}")
        lines.append("```text")
        lines.append(item.stdout or item.stderr or f"exit {item.returncode}")
        lines.append("```")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or (default or "")


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    marker = "Y/n" if default else "y/N"
    value = input(f"{prompt} [{marker}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes"}


def default_archive_for(cam_home: Path) -> Path:
    return cam_home.parent / "CAM_ARCHIVE"


def parse_args(argv: list[str]) -> argparse.Namespace:
    default_home = Path(os.environ.get("CAM_HOME", Path.home() / "CAM_ALL"))
    parser = argparse.ArgumentParser(description="Set up a local CAM_ALL workspace.")
    parser.add_argument("--cam-home", type=Path, default=default_home)
    parser.add_argument("--cam-archive", type=Path)
    parser.add_argument("--existing-cam-cam", type=Path)
    parser.add_argument("--wrapper-cam-cam", type=Path)
    parser.add_argument("--wrapper-db", type=Path)
    parser.add_argument("--wrapper-config", type=Path)
    parser.add_argument("--wrapper-env", type=Path)
    parser.add_argument("--skip-wrapper", action="store_true")
    parser.add_argument("--install-codex-skill", action="store_true")
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--skip-clone", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    cam_home = args.cam_home.expanduser().resolve()
    cam_archive = (args.cam_archive or default_archive_for(cam_home)).expanduser().resolve()

    if not args.non_interactive:
        cam_home = Path(ask("CAM_HOME", str(cam_home))).expanduser().resolve()
        cam_archive = Path(ask("CAM_ARCHIVE", str(cam_archive))).expanduser().resolve()

    paths = ensure_layout(cam_home, cam_archive)
    print(f"Created layout under {paths.cam_home}")

    clone_results: list[CommandResult] = []
    if not args.skip_clone:
        clone_results = clone_or_update_repos(cam_home)
        for result in clone_results:
            print(f"{result.command} -> {result.returncode}")
            if result.returncode != 0:
                print(result.stderr, file=sys.stderr)
                return result.returncode

    cam_codx = paths.repos / "CAM_Codx"
    if not cam_codx.exists():
        cam_codx = Path(__file__).resolve().parents[1]
    template_result = copy_public_templates(cam_codx, cam_home)

    import_result: ImportResult | None = None
    existing = args.existing_cam_cam
    if existing is None and not args.non_interactive:
        if ask_yes_no("Import private runtime state from an existing CAM_CAM build?"):
            existing_value = ask("Existing CAM_CAM path")
            existing = Path(existing_value) if existing_value else None
    if existing is not None:
        import_result = import_existing_runtime_state(existing, cam_home)

    wrapper: CamCodxWrapper | None = None
    if not args.skip_wrapper:
        if args.wrapper_cam_cam and args.wrapper_db and args.wrapper_config and args.wrapper_env:
            wrapper = create_cam_codx_wrapper(
                cam_home=cam_home,
                cam_cam=args.wrapper_cam_cam,
                db=args.wrapper_db,
                config=args.wrapper_config,
                env_file=args.wrapper_env,
            )
        else:
            wrapper = create_default_cam_codx_wrapper(cam_home)

    skill_installs: list[CodexSkillInstall] = []
    if args.install_codex_skill:
        skill_root = Path(__file__).resolve().parents[1] / "templates" / "skills"
        skill_installs = install_codex_skills(skill_root, args.codex_home)

    report = write_report(
        cam_home,
        cam_archive,
        clone_results,
        template_result,
        import_result,
        wrapper,
        skill_installs=skill_installs,
    )
    print(f"Setup report written: {report}")
    print("")
    if wrapper is not None:
        print("Codex CAM wrapper:")
        print(f"  {wrapper.path}")
        print("Approve this narrow command prefix in Codex when CAM needs DB writes:")
        print(f"  {wrapper.approval_prefix}")
        print("")
    if skill_installs:
        print("Codex skills installed:")
        for installed in skill_installs:
            print(f"  {installed.dest}")
        print("")
    print("Next:")
    print(f"  cd {paths.repos / 'CAM_Codx'}")
    print("  codex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
