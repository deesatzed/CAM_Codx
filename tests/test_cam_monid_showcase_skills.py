from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "templates" / "skills" / "monid-showcase-contract.json"
SKILL_NAMES = (
    "cam-codx-monid-capability-spike",
    "cam-codx-monid-launch-week",
    "cam-codx-monid-competitive-surface",
    "cam-codx-monid-product-intelligence",
    "cam-codx-monid-incident-context",
)
SKILLS_ROOT = ROOT / "templates" / "skills"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_defines_exactly_five_unique_read_only_showcases() -> None:
    payload = _contract()
    assert payload["schema_version"] == 1
    skills = payload["skills"]
    assert tuple(item["name"] for item in skills) == SKILL_NAMES
    assert len({item["capability_id"] for item in skills}) == 5
    for item in skills:
        assert item["safety_class"] == "read_only_external_data"
        assert 1 <= len(item["discover_queries"]) <= 2
        assert all(2 <= len(query.split()) <= 7 for query in item["discover_queries"])
        assert 20 <= len(item["description"]) <= 180
        assert item["public_data_only"] is True


def test_each_showcase_has_installable_skill_and_ui_metadata() -> None:
    for name in SKILL_NAMES:
        skill_dir = SKILLS_ROOT / name
        entrypoint = skill_dir / "SKILL.md"
        ui = skill_dir / "agents" / "openai.yaml"
        assert entrypoint.is_file(), name
        assert ui.is_file(), name

        text = entrypoint.read_text(encoding="utf-8")
        assert text.startswith("---\n"), name
        assert f"name: {name}\n" in text, name
        assert len(text.splitlines()) <= 180, name

        ui_text = ui.read_text(encoding="utf-8")
        assert f"${name}" in ui_text, name
        assert "display_name:" in ui_text, name
        assert "short_description:" in ui_text, name


def test_showcases_share_no_spend_and_authorization_boundaries() -> None:
    required_concepts = (
        "existing dedicated tool",
        "inspect before",
        "max-cost-usd",
        "paid_endpoint_executed",
        "public data",
        "explicit authorization",
        "BLOCKED",
        "do not publish",
        "confidential",
    )
    for name in SKILL_NAMES:
        text = (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(text.lower().split())
        for concept in required_concepts:
            assert concept.lower() in normalized, f"{name}: missing {concept}"
        assert "tools/cam_monid_showcase.py" in text, name
        assert "monid run" in text, name
        assert "monid runs" in text, name


def test_showcase_outcomes_are_domain_specific() -> None:
    expected = {
        "cam-codx-monid-capability-spike": ("adapter", "go/no-go"),
        "cam-codx-monid-launch-week": ("launch", "mention"),
        "cam-codx-monid-competitive-surface": ("competitor", "positioning"),
        "cam-codx-monid-product-intelligence": ("price", "inventory"),
        "cam-codx-monid-incident-context": ("incident", "outage"),
    }
    for name, terms in expected.items():
        text = (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8").lower()
        assert all(term in text for term in terms), name
