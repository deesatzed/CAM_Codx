from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates" / "skills" / "cam-codx"
SKILL_MD = SKILL / "SKILL.md"
REFERENCES = {
    "swe-playbooks.md",
    "knowledge-playbooks.md",
    "admin-playbooks.md",
    "safety-and-approvals.md",
}
TRUTH_FILES = (
    "AGENTS.md",
    "GOAL.md",
    "STANDARDS.md",
    "IMPLEMENT.md",
    "DECISIONS.md",
    "PROGRESS.md",
    "TASK_QUEUE.md",
)
SWE_INTENTS = {"assess", "plan", "build", "fix", "verify", "record"}
ADMIN_FAMILIES = {
    "mine",
    "knowledge",
    "models",
    "self-enhance",
    "evolution",
    "doctor",
    "setup",
}


def _frontmatter_and_body() -> tuple[dict, str]:
    text = SKILL_MD.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    return yaml.safe_load(frontmatter), body


def _all_skill_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SKILL.rglob("*"))
        if path.is_file()
    )


def test_skill_has_trigger_complete_minimal_frontmatter_and_ui_metadata() -> None:
    frontmatter, _body = _frontmatter_and_body()
    assert set(frontmatter) == {"name", "description"}
    assert frontmatter["name"] == "cam-codx"
    description = frontmatter["description"].lower()
    for trigger in ("software", "build", "debug", "troubleshoot", "cam", "mine"):
        assert trigger in description

    ui = yaml.safe_load((SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert ui["interface"]["display_name"] == "CAM Codex"
    assert 25 <= len(ui["interface"]["short_description"]) <= 64
    assert "$cam-codx" in ui["interface"]["default_prompt"]


def test_skill_is_concise_and_routes_to_all_progressive_references() -> None:
    _frontmatter, body = _frontmatter_and_body()
    assert len(body.splitlines()) < 220
    assert set(path.name for path in (SKILL / "references").glob("*.md")) == REFERENCES
    for reference in REFERENCES:
        assert f"references/{reference}" in body


def test_skill_inspects_truth_before_planning_and_exposes_all_intents() -> None:
    _frontmatter, body = _frontmatter_and_body()
    for truth_file in TRUTH_FILES:
        assert truth_file in body
    assert body.index("truth") < body.index("cam_control_plane.py plan")
    for intent in SWE_INTENTS | ADMIN_FAMILIES:
        assert re.search(rf"(?<![a-z-]){re.escape(intent)}(?![a-z-])", body.lower())


def test_skill_plans_before_execution_and_uses_contract_manager() -> None:
    _frontmatter, body = _frontmatter_and_body()
    assert "cam_control_plane.py plan" in body
    assert "cam_manager.py prepare" in body
    assert "cam_manager.py approve" in body
    assert "cam_manager.py execute" in body
    assert "--wrapper" in body
    assert body.index("cam_control_plane.py plan") < body.index("cam_manager.py prepare")
    assert "capability contract" in body.lower()


def test_skill_reuses_existing_helpers_and_has_explicit_unsafe_boundaries() -> None:
    text = _all_skill_text().lower()
    assert "tools/development_brief.py" in text
    assert "tools/cam_pull_mine_dir.py" in text
    assert "cam-codx-development-brief" not in text
    assert "cam-codx-pull-mine-dir" not in text
    for phrase in (
        "no implicit mining",
        "no implicit promotion",
        "single-use approval",
        "separate approval",
        "provider spend",
        "target mutation",
        "live cam mutation",
        "direct cam_cam",
        "troubleshooting",
    ):
        assert phrase in text


def test_playbooks_cover_new_continuing_rescue_and_evidence_selection_needs() -> None:
    swe = (SKILL / "references" / "swe-playbooks.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "new project",
        "in-progress",
        "continue",
        "rescue",
        "re-development",
        "gap",
        "troubleshoot",
        "selected",
        "rejected",
        "landing map",
        "verified outcome",
    ):
        assert phrase in swe


def test_skill_contains_no_stale_paths_secrets_or_implicit_live_actions() -> None:
    text = _all_skill_text()
    assert "/Volumes/WS4TB/repo622sn" not in text
    assert "/Volumes/WS4TB/WS4TBr" not in text
    assert not re.search(r"(?i)(api[_-]?key|token|password)\s*[=:]\s*['\"]?[A-Za-z0-9_-]{12,}", text)
    lowered = text.lower()
    assert "ordinary swe work never mines" in lowered
    assert "promotion is never part of mining" in lowered
