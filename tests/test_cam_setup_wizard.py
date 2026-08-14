import json
from pathlib import Path
import os
import subprocess

import pytest

from tools.cam_setup_wizard import (
    CodexSkillMigrationError,
    ImportResult,
    create_cam_codx_wrapper,
    create_default_cam_codx_wrapper,
    ensure_layout,
    install_codex_skill,
    import_existing_runtime_state,
    install_codex_skills,
    known_installed_legacy_skills,
    local_state_paths,
    migrate_codex_skills,
    write_report,
)


def test_ensure_layout_creates_overlay_directories(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM_ALL"
    cam_archive = tmp_path / "CAM_ARCHIVE"

    ensure_layout(cam_home, cam_archive)

    expected_dirs = [
        cam_home / "repos",
        cam_home / "local_state" / "CAM_CAM" / "data",
        cam_home / "local_state" / "CAM_CAM" / "config",
        cam_home / "local_state" / "CAM_CAM" / "env",
        cam_home / "local_state" / "CAM_Codx" / "config",
        cam_home / "local_state" / "adapters",
        cam_home / "reports",
        cam_home / "clone_proofs",
        cam_home / "scripts",
        cam_archive,
    ]

    assert all(path.is_dir() for path in expected_dirs)


def test_import_existing_runtime_state_copies_private_files_to_local_state(
    tmp_path: Path,
) -> None:
    cam_home = tmp_path / "CAM_ALL"
    cam_archive = tmp_path / "CAM_ARCHIVE"
    existing = tmp_path / "old" / "CAM_CAM"
    (existing / "data").mkdir(parents=True)
    (existing / "data" / "claw.db").write_text("private db", encoding="utf-8")
    (existing / "data" / "clawBU.db").write_text("private backup", encoding="utf-8")
    (existing / ".env").write_text("OPENROUTER_API_KEY=secret\n", encoding="utf-8")
    for name in ("claw", "claw_cheap", "claw_dspro", "claw_grok"):
        (existing / f"{name}.toml").write_text("[database]\npath='x'\n", encoding="utf-8")

    ensure_layout(cam_home, cam_archive)
    result = import_existing_runtime_state(existing, cam_home)
    paths = local_state_paths(cam_home)

    assert (paths.cam_cam_data / "claw.db").read_text(encoding="utf-8") == "private db"
    assert (paths.cam_cam_data / "clawBU.db").read_text(encoding="utf-8") == "private backup"
    assert (paths.cam_cam_env / ".env").read_text(encoding="utf-8").startswith("OPENROUTER")
    assert (paths.cam_cam_config / "claw.local.toml").is_file()
    assert (paths.cam_cam_config / "claw_cheap.local.toml").is_file()
    assert (paths.cam_cam_config / "claw_dspro.local.toml").is_file()
    assert (paths.cam_cam_config / "claw_grok.local.toml").is_file()
    assert "data/claw.db" in result.copied
    assert ".env" in result.copied


def test_import_existing_runtime_state_skips_missing_optional_files(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM_ALL"
    cam_archive = tmp_path / "CAM_ARCHIVE"
    existing = tmp_path / "old" / "CAM_CAM"
    existing.mkdir(parents=True)

    ensure_layout(cam_home, cam_archive)
    result = import_existing_runtime_state(existing, cam_home)

    assert result.copied == []
    assert "data/claw.db" in result.skipped
    assert ".env" in result.skipped


def create_fake_cam_runtime(tmp_path: Path) -> tuple[Path, Path]:
    cam_cam = tmp_path / "CAM_CAM"
    bin_dir = cam_cam / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    calls = tmp_path / "calls.txt"
    cam = bin_dir / "cam"
    cam.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$PWD\" > \"$CAM_FAKE_CALLS\"\n"
        "printf '%s\\n' \"$CLAW_DB_PATH\" >> \"$CAM_FAKE_CALLS\"\n"
        "printf '%s\\n' \"$CAM_CODEX_MCP_DB_PATH\" >> \"$CAM_FAKE_CALLS\"\n"
        "printf '%s\\n' \"$@\" >> \"$CAM_FAKE_CALLS\"\n",
        encoding="utf-8",
    )
    cam.chmod(0o700)
    (cam_cam / "claw.db").write_text("db", encoding="utf-8")
    (cam_cam / "claw.toml").write_text("[database]\n", encoding="utf-8")
    (cam_cam / ".env").write_text("CAM_FAKE_CALLS='%s'\n" % calls, encoding="utf-8")
    return cam_cam, calls


def test_create_cam_codx_wrapper_pins_runtime_paths(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM_ALL"
    cam_archive = tmp_path / "CAM_ARCHIVE"
    paths = ensure_layout(cam_home, cam_archive)
    cam_cam, _calls = create_fake_cam_runtime(tmp_path)

    wrapper = create_cam_codx_wrapper(
        cam_home=cam_home,
        cam_cam=cam_cam,
        db=cam_cam / "claw.db",
        config=cam_cam / "claw.toml",
        env_file=cam_cam / ".env",
    )
    text = wrapper.path.read_text(encoding="utf-8")

    assert wrapper.path == paths.scripts / "cam-codx"
    assert os.access(wrapper.path, os.X_OK)
    assert str(cam_cam) in text
    assert str(cam_cam / ".venv" / "bin" / "cam") in text
    assert str(cam_cam / "claw.db") in text
    assert str(cam_cam / "claw.toml") in text
    assert str(cam_cam / ".env") in text
    assert wrapper.approval_prefix == str(wrapper.path)


def test_cam_codx_wrapper_appends_default_config(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM_ALL"
    ensure_layout(cam_home, tmp_path / "CAM_ARCHIVE")
    cam_cam, calls = create_fake_cam_runtime(tmp_path)
    wrapper = create_cam_codx_wrapper(
        cam_home=cam_home,
        cam_cam=cam_cam,
        db=cam_cam / "claw.db",
        config=cam_cam / "claw.toml",
        env_file=cam_cam / ".env",
    )

    result = subprocess.run(
        [str(wrapper.path), "status"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert calls.read_text(encoding="utf-8").splitlines() == [
        str(cam_cam),
        str(cam_cam / "claw.db"),
        str(cam_cam / "claw.db"),
        "status",
        "-c",
        str(cam_cam / "claw.toml"),
    ]


def test_cam_codx_wrapper_preserves_explicit_short_config(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM_ALL"
    ensure_layout(cam_home, tmp_path / "CAM_ARCHIVE")
    cam_cam, calls = create_fake_cam_runtime(tmp_path)
    wrapper = create_cam_codx_wrapper(
        cam_home=cam_home,
        cam_cam=cam_cam,
        db=cam_cam / "claw.db",
        config=cam_cam / "claw.toml",
        env_file=cam_cam / ".env",
    )

    result = subprocess.run(
        [str(wrapper.path), "status", "-c", "other.toml"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert calls.read_text(encoding="utf-8").splitlines()[-3:] == [
        "status",
        "-c",
        "other.toml",
    ]


def test_cam_codx_wrapper_preserves_explicit_long_config(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM_ALL"
    ensure_layout(cam_home, tmp_path / "CAM_ARCHIVE")
    cam_cam, calls = create_fake_cam_runtime(tmp_path)
    wrapper = create_cam_codx_wrapper(
        cam_home=cam_home,
        cam_cam=cam_cam,
        db=cam_cam / "claw.db",
        config=cam_cam / "claw.toml",
        env_file=cam_cam / ".env",
    )

    result = subprocess.run(
        [str(wrapper.path), "status", "--config", "other.toml"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert calls.read_text(encoding="utf-8").splitlines()[-3:] == [
        "status",
        "--config",
        "other.toml",
    ]


def test_write_report_includes_cam_codx_wrapper(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM_ALL"
    cam_archive = tmp_path / "CAM_ARCHIVE"
    ensure_layout(cam_home, cam_archive)
    cam_cam, _calls = create_fake_cam_runtime(tmp_path)
    wrapper = create_cam_codx_wrapper(
        cam_home=cam_home,
        cam_cam=cam_cam,
        db=cam_cam / "claw.db",
        config=cam_cam / "claw.toml",
        env_file=cam_cam / ".env",
    )

    report = write_report(cam_home, cam_archive, [], ImportResult(), None, wrapper)
    text = report.read_text(encoding="utf-8")

    assert "cam-codx" in text
    assert "Codex approval prefix" in text
    assert str(wrapper.path) in text


def test_default_wrapper_detects_side_by_side_cam_cam_clone(tmp_path: Path) -> None:
    cam_home = tmp_path / "CAM"
    ensure_layout(cam_home, tmp_path / "CAM_ARCHIVE")
    cam_cam, _calls = create_fake_cam_runtime(cam_home)

    wrapper = create_default_cam_codx_wrapper(cam_home)

    assert wrapper is not None
    assert wrapper.cam_cam == cam_cam.resolve()
    assert wrapper.db == (cam_cam / "claw.db").resolve()
    assert wrapper.config == (cam_cam / "claw.toml").resolve()
    assert wrapper.env_file == (cam_cam / ".env").resolve()


def test_install_codex_skill_copies_template_to_codex_home(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    source = tmp_path / "CAM_Codx" / "templates" / "skills" / "cam-codx-setup"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text(
        "---\nname: cam-codx-setup\ndescription: test\n---\n",
        encoding="utf-8",
    )

    dest = install_codex_skill(source, codex_home)

    assert dest == codex_home / "skills" / "cam-codx-setup"
    assert (dest / "SKILL.md").read_text(encoding="utf-8").startswith("---")


def test_install_codex_skills_installs_only_canonical_cam_codx(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    source_root = tmp_path / "CAM_Codx" / "templates" / "skills"
    for name in (
        "cam-codx",
        "cam-codx-setup",
        "cam-codx-swe",
        "cam-codx-development-brief",
        "cam-codx-pull-mine-dir",
    ):
        source = source_root / name
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test\n---\n",
            encoding="utf-8",
        )

    installs = install_codex_skills(source_root, codex_home)

    assert {item.dest.name for item in installs} == {"cam-codx"}
    assert (codex_home / "skills" / "cam-codx" / "SKILL.md").is_file()
    assert not (codex_home / "skills" / "cam-codx-swe").exists()


def test_legacy_skills_are_reported_without_implicit_migration(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    skills = codex_home / "skills"
    for name in ("cam-codx-swe", "cam-codx-session", "unrelated-skill"):
        path = skills / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(name, encoding="utf-8")

    legacy = known_installed_legacy_skills(codex_home)

    assert [path.name for path in legacy] == ["cam-codx-session", "cam-codx-swe"]
    assert all(path.exists() for path in legacy)
    assert (skills / "unrelated-skill" / "SKILL.md").read_text(encoding="utf-8") == "unrelated-skill"


def test_explicit_migration_moves_only_known_cam_skills_and_writes_restore_metadata(
    tmp_path: Path,
) -> None:
    codex_home = tmp_path / ".codex"
    skills = codex_home / "skills"
    legacy_names = {
        "cam-codx-setup",
        "cam-codx-swe",
        "cam-codx-development-brief",
        "cam-codx-pull-mine-dir",
        "cam-codx-session",
    }
    for name in legacy_names | {"unrelated-skill"}:
        path = skills / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(name, encoding="utf-8")

    migration = migrate_codex_skills(codex_home, timestamp="20260814T010203Z")

    assert migration.backup_dir.name == "cam-codx-legacy-20260814T010203Z"
    assert {path.name for path in migration.moved} == legacy_names
    assert all(not (skills / name).exists() for name in legacy_names)
    assert all((migration.backup_dir / name / "SKILL.md").is_file() for name in legacy_names)
    unrelated = skills / "unrelated-skill" / "SKILL.md"
    assert unrelated.read_text(encoding="utf-8") == "unrelated-skill"
    assert migration.restore_metadata.is_file()
    metadata = json.loads(migration.restore_metadata.read_text(encoding="utf-8"))
    assert metadata["schema_version"] == 1
    assert metadata["status"] == "complete"
    assert {entry["name"] for entry in metadata["entries"]} == legacy_names
    assert all(entry["original_path"].startswith(str(skills)) for entry in metadata["entries"])
    assert migration.backup_dir.stat().st_mode & 0o777 == 0o700
    assert migration.restore_metadata.stat().st_mode & 0o777 == 0o600


def test_partial_migration_failure_preserves_recovery_metadata(
    tmp_path: Path, monkeypatch
) -> None:
    codex_home = tmp_path / ".codex"
    skills = codex_home / "skills"
    for name in ("cam-codx-development-brief", "cam-codx-swe"):
        path = skills / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(name, encoding="utf-8")

    from tools import cam_setup_wizard

    real_move = cam_setup_wizard.shutil.move
    calls = 0

    def fail_second_move(source: str, destination: str):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("fixture move failure")
        return real_move(source, destination)

    monkeypatch.setattr(cam_setup_wizard.shutil, "move", fail_second_move)

    with pytest.raises(CodexSkillMigrationError) as raised:
        migrate_codex_skills(codex_home, timestamp="20260814T020304Z")

    metadata_path = raised.value.restore_metadata
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "partial"
    assert len(metadata["entries"]) == 1
    moved = metadata["entries"][0]
    assert Path(moved["backup_path"]).is_dir()
    assert not Path(moved["original_path"]).exists()
    assert (skills / "cam-codx-swe").is_dir()


def test_setup_skill_documents_canonical_install_and_explicit_recoverable_migration() -> None:
    skill = (
        Path(__file__).resolve().parents[1]
        / "templates"
        / "skills"
        / "cam-codx-setup"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "--migrate-codex-skills" in skill
    assert "timestamped" in skill.lower()
    assert "restore" in skill.lower()
    assert "installs only `cam-codx`" in skill.lower()
