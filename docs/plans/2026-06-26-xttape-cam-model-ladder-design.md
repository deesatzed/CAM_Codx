# XTtape CAM Model-Ladder Experiment Design

## Purpose

This experiment tests CAM_Codx as a cost-compression and capability-equalizing
layer.

The prior XTtape A/B build showed that both the no-CAM control and CAM arm
could pass the same evaluator. It also showed a weak positive signal for CAM:
fewer recorded failure cycles and one `claw.db`-derived learning-audit
improvement. The next question is sharper:

> How far down the model/cost/reasoning ladder can CAM_Codx carry the XTtape
> build before quality breaks?

## Fixed Baseline

Use the existing control result as the fixed high-end comparator:

| Baseline | Model label | CAM | Result |
|---|---|---|---|
| current-control | Codex GPT-5.5 medium/default | no | evaluator PASS, 10/10 |

The control run also has user-pasted goal summary values:

- 227,336 tokens,
- about 9 minutes 12 seconds elapsed.

Those values are useful context, but the previous harness did not capture them
directly into `RUN_METRICS.json`. The model-ladder experiment must capture
token and elapsed summaries explicitly before each arm is treated as complete.

## New CAM-Assisted Arms

Run four CAM-assisted arms against the same XTtape app spec and evaluator:

| Arm | Model label | Reasoning label | CAM |
|---|---|---|---|
| `cam-5.5-low` | `gpt-5.5` | `low` | yes |
| `cam-5.4` | `gpt-5.4` | default or available setting | yes |
| `cam-5.4-mini` | `gpt-5.4-mini` | default or available setting | yes |
| `cam-5.3-codex-spark` | `gpt-5.3-codex-spark` | default or available setting | yes |

These labels are user-provided experiment labels. The run must record the exact
host-visible model identity if available. If the host exposes only the label
selected by the user, record that and mark exact identity as unavailable.

## Hypothesis

CAM_Codx may let cheaper or lower-reasoning models match the existing
GPT-5.5-medium no-CAM control because `claw.db` supplies reusable methodology,
failure recovery patterns, evidence discipline, and source/audit architecture
that weaker models may not infer reliably.

## Primary Question

Which CAM-assisted model is the cheapest or lowest-reasoning arm that still
matches the fixed control on evaluator pass/fail and evidence quality?

## Secondary Questions

- Does model capability show a clear inflection point?
- Do weaker CAM-assisted arms fail in architecture, data model, frontend,
  evidence capture, or debugging recovery?
- Does CAM recall frequency increase as model capability decreases?
- Does CAM recall quality degrade with weaker models?
- Does cheaper-model CAM produce comparable evidence at lower estimated cost?

## Fairness Rules

- Same frozen evaluator.
- Same shared XTtape app spec.
- Same no-human-interference rule.
- Same source fixtures.
- Same acceptance gates.
- Each arm runs in its own folder.
- Each arm launches through `/goal GOAL.md`.
- Each arm may use CAM_Codx and `claw.db`.
- No arm may inspect another arm until all runs stop.
- No live secrets, paid API calls, production deploys, or social write actions.

## Required CAM Usage

Each model-ladder arm must use CAM_Codx at defined checkpoints:

1. Architecture recall before scaffold.
2. Schema/data-model recall before Prisma design.
3. Connector-safety recall before source/X boundary implementation.
4. Failure-recovery recall after each failed build, test, or smoke command.
5. Final evidence-audit recall before completion.

Each recall must be recorded in `CAM_USAGE_LEDGER.md` with:

- trigger,
- query or recall source,
- methodology used,
- methodology rejected,
- concrete change made,
- whether it prevented or fixed a failure.

## Metrics

Primary metrics:

- evaluator pass/fail,
- evaluator score,
- human interventions,
- exact model label selected,
- host-visible model identity,
- reasoning setting,
- goal-session token total,
- goal-session elapsed time.

Secondary metrics:

- failed command count,
- failed build/test cycles,
- autonomous recovery attempts,
- CAM recall count,
- useful CAM recall count,
- no-secret scan result,
- screenshot presence,
- server shutdown status,
- estimated cost if price data is available from a trusted source.

Do not fabricate token totals, model identity, or cost. If a value is not
available, record it as unavailable and explain why.

## Inflection-Point Interpretation

| Outcome | Interpretation |
|---|---|
| All four arms pass | CAM_Codx may allow substantially cheaper/lower-reasoning models to handle this app class. |
| `cam-5.5-low` and `cam-5.4` pass, smaller arms fail | CAM helps below default reasoning, but there is a lower model-capability floor. |
| Only `cam-5.5-low` passes | CAM helps reduce reasoning setting, but not model tier for this task. |
| All arms fail | Current CAM use is not enough to compensate for weaker models on this build. |

## When To Add New Controls

Do not create matching no-CAM controls yet. First identify the inflection
point. After that, add direct/no-CAM controls only around the break point.

Examples:

- If `cam-5.4-mini` fails but `cam-5.4` passes, later run `direct-5.4` and
  `direct-5.4-mini`.
- If all CAM arms pass, later run `direct-5.3-codex-spark`.
- If all CAM arms fail, improve the CAM usage protocol before adding more
  controls.

## Verdicts

Allowed verdicts:

- `CAM_MATCHES_CONTROL_AT_LOWER_TIER`
- `CAM_PARTIAL_COMPRESSION`
- `NO_COMPRESSION`
- `INCONCLUSIVE`

Use `INCONCLUSIVE` if model identity, token totals, or evaluator conditions are
not captured cleanly.

## Success Definition

The experiment succeeds if it identifies a credible model-capability inflection
point and records enough evidence for a new user to understand whether
CAM_Codx can reduce required model tier for this class of app build.
