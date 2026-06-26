# XTtape Goal A/B Build Comparison Design

## Purpose

This experiment tests whether CAM_Codx plus `claw.db` improves autonomous app
implementation and troubleshooting, not just planning quality.

The previous XTtape showpiece proved that CAM recall can produce a stronger
build contract than a vanilla plan. The next showpiece should ask a harder
question:

> Given the same app spec and the same `/goal GOAL.md` launch method, does the
> CAM-assisted run finish faster, use fewer tokens, recover from failures more
> effectively, and produce stronger evidence than the control run?

## Core Experiment

Create two sibling build workspaces:

```text
/Volumes/WS4TB/ccxt/xttape-build-ab/
  evaluator/
  control/
  cam/
  reports/
```

Each build arm gets a `GOAL.md` and is launched by the same user action:

```text
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/control/GOAL.md
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/cam/GOAL.md
```

After launch, there should be no human guidance. If an agent asks for
clarification, credentials, product choices, or debugging help, the attempt is
recorded as a human-intervention event.

## Experimental Arms

| Arm | Allowed | Forbidden |
|---|---|---|
| Control | Use the frozen XTtape app spec, local files in its workspace, normal shell/build/test tools, and public package docs already present in the repo. | CAM_Codx methodology recall, `claw.db`, CAM MCP/CLI troubleshooting, copied CAM context packets, or inspecting the CAM arm. |
| CAM | Use the same frozen XTtape app spec, normal shell/build/test tools, CAM_Codx methodology recall, and `claw.db` for initial orientation and after failures. | Inspecting the control arm during the run, copying code from mined repos, using secrets, paid API calls, or modifying the frozen evaluator. |

Both arms must build the same local app target:

- FastAPI API,
- React/Vite/TypeScript web app,
- Prisma/SQLite persistence,
- replayable source fixtures,
- read-only source/X connector boundary,
- source-backed ticker items,
- provider fallback when Grok/xAI is unavailable,
- visible learning action with audit record,
- screenshot and evidence capture.

## Frozen Evaluator

The evaluator is created before either run starts and is read-only to both
arms. It defines the acceptance gates and metrics schema.

Required evaluator files:

```text
evaluator/ACCEPTANCE.md
evaluator/METRICS_SCHEMA.json
evaluator/scripts/check_app.sh
evaluator/scripts/score_run.py
evaluator/fixtures/
```

The evaluator must not depend on live X/social credentials or paid AI calls.
Replay fixtures and no-provider fallback are part of the acceptance contract.

## Measurement Model

Each arm writes:

```text
RUN_METRICS.json
RUN_REPORT.md
docs/evidence/
docs/screenshots/
```

The metrics file captures:

- start timestamp,
- end timestamp,
- wall-clock minutes,
- token usage reported by the goal session or run transcript,
- tool/shell command count when available,
- failed command count,
- failed test/build cycle count,
- human-intervention attempts,
- autonomous recovery attempts,
- final acceptance status,
- evaluator score,
- screenshots produced,
- no-secret scan result.

The CAM arm also writes:

```text
CAM_USAGE_LEDGER.md
```

Each CAM recall event records:

- trigger,
- query or recall source,
- methodology used,
- methodology rejected,
- concrete change made,
- whether the recall resolved a failure.

The control arm writes:

```text
NO_CAM_ATTESTATION.md
```

It attests that the run did not use CAM memory, `claw.db`, CAM MCP/CLI
troubleshooting, or copied CAM context packets.

## Token And Time Capture

Time is captured by wrapper files and run reports:

- `RUN_STARTED_AT.txt`,
- `RUN_FINISHED_AT.txt`,
- `RUN_METRICS.json`.

Token usage is captured from the `/goal` session output when available. If the
host UI exposes a goal token total, record it verbatim. If not, record
`token_usage_status: "unavailable"` and preserve the run transcript or final
goal summary as evidence. Do not fabricate token estimates.

## Fairness Controls

- Same app requirements.
- Same evaluator.
- Same target acceptance gates.
- Same no-live-secret fallback requirement.
- Same time budget.
- Same model family where the host allows it.
- Same package manager and scaffold assumptions unless a run records a
  justified deviation.
- No human answers after launch.
- No cross-arm inspection until both runs are complete or stopped.
- The CAM arm may use CAM recall only for methodology and troubleshooting, not
  for copying mined code.

## Stop Rules

A run stops when one of these happens:

- evaluator passes,
- time budget expires,
- token budget expires,
- the agent asks for human help,
- the agent attempts to use secrets, paid APIs, production deployment, or
  social write actions,
- repeated failures leave no autonomous recovery path.

Each stop must produce a `RUN_REPORT.md` explaining the terminal state.

## Final Comparison Report

After both arms stop, create:

```text
reports/AB_COMPARISON_REPORT.md
reports/AB_METRICS_SUMMARY.json
reports/screenshots/
```

The report compares:

- completion status,
- wall-clock time,
- token usage availability and totals,
- failure/recovery loops,
- evaluator score,
- app quality and UX evidence,
- test coverage,
- secret-safety evidence,
- whether CAM recall materially changed debugging outcomes.

## Success Definition

The experiment succeeds if a new user can inspect the two `GOAL.md` files,
launch both runs with `/goal GOAL.md`, avoid all mid-run coaching, and compare
the resulting apps with objective metrics.

The CAM arm does not need to win for the experiment to be useful. A fair loss,
tie, or partial win is still valuable if the evidence is clean.
