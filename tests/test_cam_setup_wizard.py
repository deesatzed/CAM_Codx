from pathlib import Path

from tools.cam_setup_wizard import (
    ensure_layout,
    import_existing_runtime_state,
    local_state_paths,
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
