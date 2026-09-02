from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "monid_showcase"


class FixtureRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def __call__(self, args: list[str], env: dict[str, str]):
        from tools.cam_monid_showcase import CommandResult

        self.calls.append((args, env))
        source = "discover.json" if "discover" in args else "inspect.json"
        return CommandResult(0, (FIXTURES / source).read_text(encoding="utf-8"), "")


def test_plan_discovers_inspects_and_never_runs_paid_endpoint(tmp_path: Path) -> None:
    from tools.cam_monid_showcase import MonidShowcasePlanner

    runner = FixtureRunner()
    output = tmp_path / "plan.json"
    planner = MonidShowcasePlanner(runner=runner)

    payload = planner.plan(
        skill="cam-codx-monid-launch-week",
        subject="Example Product",
        max_cost_usd="1.00",
        candidate_limit=2,
        output=output,
    )

    commands = [args for args, _env in runner.calls]
    assert commands[0][:3] == ["monid", "discover", "-q"]
    assert commands[0][-3:] == ["-l", "2", "-j"]
    assert any(args[:2] == ["monid", "inspect"] for args in commands)
    assert not any("run" in args or "runs" in args for args in commands)
    assert all(env["NO_COLOR"] == "1" for _args, env in runner.calls)
    assert payload["status"] == "planned"
    assert payload["paid_endpoint_executed"] is False
    assert payload["selected"][0]["health"] == "unknown"
    assert payload["selected"][0]["price"]["value"] == "0.25"
    assert payload["selected"][0]["input"]["queryParams"]["required"] == ["query"]
    assert "body" in payload["selected"][0]["input"]
    assert "pathParams" in payload["selected"][0]["input"]
    assert json.loads(output.read_text(encoding="utf-8")) == payload


def test_existing_tool_precedes_monid_and_makes_no_calls(tmp_path: Path) -> None:
    from tools.cam_monid_showcase import MonidShowcasePlanner

    runner = FixtureRunner()
    payload = MonidShowcasePlanner(runner=runner).plan(
        skill="cam-codx-monid-launch-week",
        subject="Example Product",
        max_cost_usd="1.00",
        existing_tools=("owned-brand-monitor",),
        output=tmp_path / "plan.json",
    )

    assert runner.calls == []
    assert payload["status"] == "dedicated_tool_preferred"
    assert payload["existing_tools"] == ["owned-brand-monitor"]


def test_plan_rejects_secret_shaped_or_local_path_subjects(tmp_path: Path) -> None:
    from tools.cam_monid_showcase import MonidShowcasePlanner, SubjectRejected

    planner = MonidShowcasePlanner(runner=FixtureRunner())
    for subject in ("monid_live_do-not-log-this", "/Users/person/private-product"):
        with pytest.raises(SubjectRejected):
            planner.plan(
                skill="cam-codx-monid-launch-week",
                subject=subject,
                max_cost_usd="1.00",
                output=tmp_path / "plan.json",
            )


def test_plan_rejects_candidate_above_cost_ceiling(tmp_path: Path) -> None:
    from tools.cam_monid_showcase import MonidShowcasePlanner

    payload = MonidShowcasePlanner(runner=FixtureRunner()).plan(
        skill="cam-codx-monid-launch-week",
        subject="Example Product",
        max_cost_usd="0.10",
        candidate_limit=2,
        output=tmp_path / "plan.json",
    )

    assert payload["status"] == "no_suitable_endpoint"
    assert payload["selected"] == []
    assert "cost_exceeds_ceiling" in {item["reason"] for item in payload["rejected"]}
