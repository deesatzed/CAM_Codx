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
