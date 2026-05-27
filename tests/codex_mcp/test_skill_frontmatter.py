"""Skill frontmatter validator tests for Codex-CAM auto_fire blocks.

Covers validate_skill_frontmatter.py to ≥90% line + branch (Gate 4.6 / CC.5).
Tests use real YAML/schema validation — no mocks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.validate_skill_frontmatter import (
    _extract_frontmatter,
    _validate_file,
    _load_schema,
    main,
)
from jsonschema import Draft202012Validator


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_skill(tmp_path: Path, content: str, name: str = "SKILL.md") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _schema_validator() -> Draft202012Validator:
    schema = _load_schema()
    return Draft202012Validator(schema)


# ── _extract_frontmatter ──────────────────────────────────────────────────────

def test_extract_frontmatter_standard() -> None:
    text = "---\nname: test\n---\n# body"
    result = _extract_frontmatter(text)
    assert result == "name: test"


def test_extract_frontmatter_leading_blank_line() -> None:
    """Line 104: leading blank line before opening fence is tolerated."""
    text = "\n---\nname: test\n---\n# body"
    result = _extract_frontmatter(text)
    assert result == "name: test"


def test_extract_frontmatter_no_opening_fence() -> None:
    """Line 110: no opening fence returns None."""
    text = "name: test\n# body"
    assert _extract_frontmatter(text) is None


def test_extract_frontmatter_no_closing_fence() -> None:
    """Line 114/125: opening fence with no close returns None."""
    text = "---\nname: test\n"
    assert _extract_frontmatter(text) is None


def test_extract_frontmatter_empty_file() -> None:
    assert _extract_frontmatter("") is None


def test_extract_frontmatter_bom_stripped() -> None:
    """BOM at start of first line is stripped before fence check."""
    text = "﻿---\nname: bom_test\n---\n"
    result = _extract_frontmatter(text)
    assert result == "name: bom_test"


def test_extract_frontmatter_closing_fence_found() -> None:
    """Lines 117-121 (closing loop): confirm body between fences is returned."""
    text = "---\nkey1: a\nkey2: b\n---\nsome prose"
    result = _extract_frontmatter(text)
    assert result == "key1: a\nkey2: b"


# ── _validate_file ────────────────────────────────────────────────────────────

def test_validate_file_not_a_file(tmp_path: Path) -> None:
    """Line 148: path that is not a regular file returns False."""
    v = _schema_validator()
    ok, msg = _validate_file(tmp_path / "nonexistent.md", v)
    assert ok is False
    assert "not a regular file" in msg


def test_validate_file_no_frontmatter(tmp_path: Path) -> None:
    """Line 153: file with no frontmatter block is acceptable."""
    skill = _make_skill(tmp_path, "# No frontmatter here\n")
    v = _schema_validator()
    ok, msg = _validate_file(skill, v)
    assert ok is True
    assert "no frontmatter block" in msg


def test_validate_file_malformed_yaml(tmp_path: Path) -> None:
    """Lines 157-158: YAML parse error returns False with explanation."""
    skill = _make_skill(tmp_path, "---\nkey: [unclosed\n---\n")
    v = _schema_validator()
    ok, msg = _validate_file(skill, v)
    assert ok is False
    assert "malformed YAML" in msg


def test_validate_file_frontmatter_not_a_mapping(tmp_path: Path) -> None:
    """Line 163: frontmatter is a list (not a dict) returns False."""
    skill = _make_skill(tmp_path, "---\n- item1\n- item2\n---\n")
    v = _schema_validator()
    ok, msg = _validate_file(skill, v)
    assert ok is False
    assert "not a mapping" in msg


def test_validate_file_no_auto_fire_key(tmp_path: Path) -> None:
    """Line 166: frontmatter present but no auto_fire key is acceptable."""
    skill = _make_skill(tmp_path, "---\nname: plain_skill\ndescription: No auto-fire.\n---\n")
    v = _schema_validator()
    ok, msg = _validate_file(skill, v)
    assert ok is True
    assert "no auto_fire block" in msg


def test_validate_file_valid_verbs_match(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, (
        "---\n"
        "name: cam_recall_and_cite\n"
        "description: Recall and cite CAM methodologies.\n"
        "auto_fire:\n"
        "  condition: verbs_match\n"
        "  verbs: [add, fix]\n"
        "---\n"
    ))
    v = _schema_validator()
    ok, msg = _validate_file(skill, v)
    assert ok is True
    assert "auto_fire block valid" in msg


def test_validate_file_valid_consecutive_failures(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, (
        "---\n"
        "name: rescue_ladder\n"
        "description: Rescue on repeated failure.\n"
        "auto_fire:\n"
        "  condition: consecutive_failures\n"
        "  count: 2\n"
        "  failure_kind: verification\n"
        "---\n"
    ))
    v = _schema_validator()
    ok, msg = _validate_file(skill, v)
    assert ok is True


def test_validate_file_schema_violation_unknown_condition(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, (
        "---\n"
        "auto_fire:\n"
        "  condition: unicorn\n"
        "---\n"
    ))
    v = _schema_validator()
    ok, msg = _validate_file(skill, v)
    assert ok is False
    assert "schema violation" in msg


# ── _load_schema ──────────────────────────────────────────────────────────────

def test_load_schema_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 78-81: missing schema file exits with code 2."""
    import tools.validate_skill_frontmatter as mod
    monkeypatch.setattr(mod, "_SCHEMA_PATH", tmp_path / "no_such.json")
    with pytest.raises(SystemExit) as exc:
        mod._load_schema()
    assert exc.value.code == 2


# ── main() — CLI driver ───────────────────────────────────────────────────────

def test_main_accepts_codex_skill_metadata_with_auto_fire(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, (
        "---\n"
        "name: cam_recall_and_cite\n"
        "description: Recall and cite CAM methodologies before pattern-shaped edits.\n"
        "auto_fire:\n"
        "  condition: verbs_match\n"
        "  verbs: [add, fix]\n"
        "---\n\n# Skill\n"
    ))
    assert main([str(skill), "--quiet"]) == 0


def test_main_rejects_unknown_auto_fire_condition(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, (
        "---\n"
        "name: broken\n"
        "description: Broken trigger.\n"
        "auto_fire:\n"
        "  condition: purple\n"
        "---\n\n# Skill\n"
    ))
    assert main([str(skill), "--quiet"]) == 1


def test_main_no_args_exits_2(capsys) -> None:
    """Line 247: no files and no --dir is a usage error."""
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_main_dir_not_a_directory(tmp_path: Path) -> None:
    """Lines 203-211: --dir pointing to a non-directory exits 2."""
    with pytest.raises(SystemExit) as exc:
        main(["--dir", str(tmp_path / "no_such_dir")])
    assert exc.value.code == 2


def test_main_dir_no_skill_files(tmp_path: Path) -> None:
    """Lines 255-256: --dir with no SKILL.md files exits 2."""
    (tmp_path / "README.md").write_text("nothing")
    assert main(["--dir", str(tmp_path)]) == 2


def test_main_verbose_pass(tmp_path: Path, capsys) -> None:
    """Line 267: --verbose prints PASS line for each file."""
    skill = _make_skill(tmp_path, (
        "---\n"
        "name: myskill\n"
        "description: Test.\n"
        "auto_fire:\n"
        "  condition: always\n"
        "---\n"
    ))
    result = main([str(skill), "--verbose"])
    out = capsys.readouterr().out
    assert result == 0
    assert "PASS" in out
    assert "summary:" in out


def test_main_verbose_fail_with_stderr(tmp_path: Path, capsys) -> None:
    """Lines 270-273, 279, 281: failure with --verbose prints FAIL to stderr and summary."""
    skill = _make_skill(tmp_path, (
        "---\n"
        "auto_fire:\n"
        "  condition: not_valid\n"
        "---\n"
    ))
    result = main([str(skill), "--verbose"])
    captured = capsys.readouterr()
    assert result == 1
    assert "FAIL" in captured.err


def test_main_default_output_summary(tmp_path: Path, capsys) -> None:
    """Lines 278-280: non-quiet non-verbose prints 'validated N file(s); failures: K'."""
    skill = _make_skill(tmp_path, "# No frontmatter\n")
    result = main([str(skill)])
    out = capsys.readouterr().out
    assert result == 0
    assert "validated 1 file(s); failures: 0" in out


def test_main_dir_mode_passes_real_skills(tmp_path: Path) -> None:
    """--dir mode discovers SKILL.md files recursively and passes all valid ones."""
    subdir = tmp_path / "cam_recall_and_cite"
    subdir.mkdir()
    _make_skill(subdir, (
        "---\n"
        "name: cam_recall_and_cite\n"
        "description: Test skill.\n"
        "auto_fire:\n"
        "  condition: verbs_match\n"
        "  verbs: [scaffold]\n"
        "---\n"
    ))
    result = main(["--dir", str(tmp_path), "--quiet"])
    assert result == 0


def test_main_dir_mode_flags_invalid_skill(tmp_path: Path) -> None:
    subdir = tmp_path / "bad_skill"
    subdir.mkdir()
    _make_skill(subdir, (
        "---\n"
        "auto_fire:\n"
        "  condition: bad_value\n"
        "---\n"
    ))
    result = main(["--dir", str(tmp_path), "--quiet"])
    assert result == 1


def test_main_validate_all_live_codex_skills() -> None:
    """CC.5: every live .codex/skills SKILL.md with an auto_fire block validates."""
    skills_dir = Path("/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills")
    if not skills_dir.is_dir():
        pytest.skip("live .codex/skills not accessible from test environment")
    result = main(["--dir", str(skills_dir), "--quiet"])
    assert result == 0, "One or more live SKILL.md files has an invalid auto_fire block (CC.5 violation)"
