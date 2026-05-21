"""Skill frontmatter validator tests for Codex-CAM auto_fire blocks."""

from __future__ import annotations

from pathlib import Path

from tools.validate_skill_frontmatter import main


def test_validator_accepts_codex_skill_metadata_with_auto_fire(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        """---
name: cam_recall_and_cite
description: Recall and cite CAM methodologies before pattern-shaped edits.
auto_fire:
  condition: verbs_match
  verbs: ["add", "fix"]
---

# Skill
""",
        encoding="utf-8",
    )

    assert main([str(skill), "--quiet"]) == 0


def test_validator_rejects_unknown_auto_fire_condition(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        """---
name: broken
description: Broken trigger.
auto_fire:
  condition: purple
---

# Skill
""",
        encoding="utf-8",
    )

    assert main([str(skill), "--quiet"]) == 1
