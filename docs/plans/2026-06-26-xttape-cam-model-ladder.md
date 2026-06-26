# XTtape CAM Model-Ladder Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a CAM-assisted model-ladder experiment harness that compares four lower-cost or lower-reasoning CAM_Codx arms against the existing XTtape no-CAM control.

**Architecture:** Extend the local XTtape A/B experiment family with a new `xttape-model-ladder` harness. Reuse the existing frozen evaluator and shared app spec, but create four isolated CAM-assisted `/goal GOAL.md` arms with stricter required model/token capture and mandatory CAM recall checkpoints.

**Tech Stack:** Markdown goal contracts, Bash/Python evaluator helpers, JSON metrics files, existing XTtape FastAPI/React/Vite/Prisma app requirements, CAM_Codx, local `claw.db`.

---

## Source Inputs

Use these source artifacts:

- `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/ACCEPTANCE.md`
- `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/METRICS_SCHEMA.json`
- `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/SHARED_APP_SPEC.md`
- `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/fixtures/`
- `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/scripts/`
- `/Volumes/WS4TB/ccxt/xttape-build-ab/control/app/RUN_METRICS.json`
- `/Volumes/WS4TB/ccxt/xttape-build-ab/reports/AB_COMPARISON_REPORT.md`
- `/Volumes/WS4TB/ccxt/CAM_Codx/docs/plans/2026-06-26-xttape-cam-model-ladder-design.md`

Do not use legacy loose notes. Do not copy code from mined repositories.

## Task 1: Create Model-Ladder Root

**Files:**

- Create directory: `/Volumes/WS4TB/ccxt/xttape-model-ladder`
- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/README.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/.gitignore`

**Step 1: Create directories**

```bash
mkdir -p /Volumes/WS4TB/ccxt/xttape-model-ladder/{baseline,evaluator,reports/screenshots,arms/cam-5.5-low/app,arms/cam-5.4/app,arms/cam-5.4-mini/app,arms/cam-5.3-codex-spark/app}
```

Expected: all directories exist.

**Step 2: Write README**

Include:

- purpose: CAM_Codx cost-compression/model-ladder test,
- fixed baseline: existing no-CAM GPT-5.5 medium/default control,
- four CAM-assisted arms,
- no-human-interference rule,
- exact `/goal` launch commands,
- statement that model/token capture is mandatory.

**Step 3: Write `.gitignore`**

Use the same ignores as the A/B harness:

```gitignore
.env
*.db
*.db-shm
*.db-wal
node_modules/
.venv/
__pycache__/
dist/
build/
.next/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

Do not ignore metrics, reports, screenshots, goal files, or evidence files.

**Step 4: Verify**

```bash
test -d /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.5-low/app
test -d /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.4/app
test -d /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.4-mini/app
test -d /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.3-codex-spark/app
```

Expected: all commands exit 0.

## Task 2: Copy Frozen Evaluator

**Files:**

- Copy into: `/Volumes/WS4TB/ccxt/xttape-model-ladder/evaluator/`

**Step 1: Copy evaluator files**

```bash
cp -R /Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/. /Volumes/WS4TB/ccxt/xttape-model-ladder/evaluator/
```

**Step 2: Extend metrics schema**

Modify `/Volumes/WS4TB/ccxt/xttape-model-ladder/evaluator/METRICS_SCHEMA.json` to require:

```json
{
  "selected_model_label": "gpt-5.4-mini",
  "host_model_identity": "unavailable",
  "reasoning_setting": "default-or-low",
  "goal_usage_tokens": null,
  "goal_usage_elapsed_seconds": null,
  "goal_usage_capture_status": "captured|unavailable",
  "cam_recall_count": 0,
  "useful_cam_recall_count": 0,
  "server_shutdown_verified": false
}
```

Preserve the existing A/B metrics fields.

**Step 3: Verify JSON**

```bash
python -m json.tool /Volumes/WS4TB/ccxt/xttape-model-ladder/evaluator/METRICS_SCHEMA.json >/tmp/xttape_model_ladder_schema.json
```

Expected: command exits 0.

## Task 3: Save Baseline Snapshot

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/baseline/CONTROL_BASELINE.md`
- Copy: `/Volumes/WS4TB/ccxt/xttape-build-ab/control/app/RUN_METRICS.json`
- Copy: `/Volumes/WS4TB/ccxt/xttape-build-ab/reports/AB_COMPARISON_REPORT.md`

**Step 1: Write baseline summary**

Include:

- existing control path,
- evaluator score `10/10`,
- final status `pass`,
- user-pasted token count `227336`,
- user-pasted elapsed time `552` seconds,
- caveat that previous `RUN_METRICS.json` did not capture tokens directly.

**Step 2: Verify**

```bash
rg -n "227336|552|10/10|RUN_METRICS" /Volumes/WS4TB/ccxt/xttape-model-ladder/baseline/CONTROL_BASELINE.md
```

Expected: baseline values are recorded.

## Task 4: Create Shared CAM Arm Template

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/arms/GOAL_TEMPLATE.md`

**Step 1: Write template**

The template must include placeholders:

- `{{ARM_ID}}`
- `{{MODEL_LABEL}}`
- `{{REASONING_SETTING}}`
- `{{APP_ROOT}}`

The template must require:

- build only inside `{{APP_ROOT}}`,
- use frozen evaluator,
- use CAM_Codx and `claw.db`,
- mandatory CAM recall at the five checkpoints,
- no cross-arm inspection,
- no user help,
- exact model/token capture,
- `CAM_USAGE_LEDGER.md`,
- `RUN_METRICS.json`,
- `RUN_REPORT.md`.

**Step 2: Verify placeholders**

```bash
rg -n "\\{\\{ARM_ID\\}\\}|\\{\\{MODEL_LABEL\\}\\}|\\{\\{REASONING_SETTING\\}\\}|\\{\\{APP_ROOT\\}\\}" /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/GOAL_TEMPLATE.md
```

Expected: all placeholders appear.

## Task 5: Generate Four GOAL.md Files

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.5-low/GOAL.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.4/GOAL.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.4-mini/GOAL.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.3-codex-spark/GOAL.md`

**Step 1: Generate from template**

Use these values:

| Arm | Model label | Reasoning setting |
|---|---|---|
| `cam-5.5-low` | `gpt-5.5` | `low` |
| `cam-5.4` | `gpt-5.4` | `default-or-host-available` |
| `cam-5.4-mini` | `gpt-5.4-mini` | `default-or-host-available` |
| `cam-5.3-codex-spark` | `gpt-5.3-codex-spark` | `default-or-host-available` |

**Step 2: Include launch commands**

Each `GOAL.md` must include its exact launch command:

```text
/goal /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/<arm-id>/GOAL.md
```

**Step 3: Verify**

```bash
rg -n "/goal|MODEL_LABEL|gpt-5|CAM_USAGE_LEDGER|goal_usage_tokens|server_shutdown_verified" /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/*/GOAL.md
```

Expected: each arm contains launch command, model label, CAM ledger, goal usage capture, and server shutdown requirement.

## Task 6: Create Report Templates

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/reports/MODEL_LADDER_REPORT.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/reports/MODEL_LADDER_SUMMARY.json`

**Step 1: Write report template**

Sections:

- executive summary,
- baseline,
- arm table,
- evaluator results,
- token/time/cost table,
- model inflection point,
- CAM recall usefulness,
- failures by model tier,
- verdict,
- limitations,
- next direct-control recommendation.

**Step 2: Write summary JSON**

Use:

```json
{
  "baseline": "current-control",
  "arms": {},
  "inflection_point": null,
  "verdict": "not-run"
}
```

**Step 3: Verify JSON**

```bash
python -m json.tool /Volumes/WS4TB/ccxt/xttape-model-ladder/reports/MODEL_LADDER_SUMMARY.json >/tmp/xttape_model_ladder_summary.json
```

Expected: command exits 0.

## Task 7: Create Experiment Manifest

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-model-ladder/EXPERIMENT_MANIFEST.md`

**Step 1: Record fixed rules**

Include:

- existing control is fixed baseline,
- four CAM-assisted arms,
- no new controls until inflection point,
- no human guidance after `/goal`,
- model/token capture required,
- evaluator frozen before runs,
- same shared app spec,
- CAM recall mandatory at five checkpoints.

**Step 2: Record launch order**

Recommended order:

1. `cam-5.5-low`
2. `cam-5.4`
3. `cam-5.4-mini`
4. `cam-5.3-codex-spark`

**Step 3: Verify**

```bash
rg -n "inflection|cam-5.5-low|cam-5.4-mini|gpt-5.3-codex-spark|no human|model/token" /Volumes/WS4TB/ccxt/xttape-model-ladder/EXPERIMENT_MANIFEST.md
```

Expected: core rules appear.

## Task 8: Initialize And Commit Harness

**Files:**

- Stage: `/Volumes/WS4TB/ccxt/xttape-model-ladder`

**Step 1: Run final checks**

```bash
cd /Volumes/WS4TB/ccxt/xttape-model-ladder
git diff --check || true
find . -maxdepth 4 -type f | sort
rg -n "s[k]-or-v1|OPENROUTER_API_KEY[[:space:]]*=|XAI_API_KEY[[:space:]]*=|api[_-]?key\\s*[=:]|Authorization:[[:space:]]+Bearer|password\\s*[=:]|secret\\s*[=:]" .
```

Expected:

- file list prints,
- secret scan returns no matches,
- if git is not initialized, `git diff --check` can be skipped after noting it.

**Step 2: Initialize repo**

```bash
cd /Volumes/WS4TB/ccxt/xttape-model-ladder
git init
git branch -m main
git add .
git commit -m "test: add XTtape CAM model ladder harness"
```

Expected: local repo has one setup commit.

## Task 9: Launch Arms Later In Fresh Sessions

Do not launch model arms from the setup session.

Launch each arm in its own fresh Codex session with the selected model/reasoning configuration:

```text
/goal /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.5-low/GOAL.md
/goal /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.4/GOAL.md
/goal /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.4-mini/GOAL.md
/goal /Volumes/WS4TB/ccxt/xttape-model-ladder/arms/cam-5.3-codex-spark/GOAL.md
```

After each run, require the model arm to update `RUN_METRICS.json` with:

- selected model label,
- host-visible model identity,
- reasoning setting,
- goal token total,
- goal elapsed seconds,
- CAM recall count,
- useful CAM recall count,
- server shutdown verification.

## Task 10: Score And Interpret

After all four arms stop:

```bash
cd /Volumes/WS4TB/ccxt/xttape-model-ladder
python evaluator/scripts/score_run.py arms/cam-5.5-low
python evaluator/scripts/score_run.py arms/cam-5.4
python evaluator/scripts/score_run.py arms/cam-5.4-mini
python evaluator/scripts/score_run.py arms/cam-5.3-codex-spark
```

If the copied `score_run.py` expects `control|cam`, adapt or wrap it before
scoring model-ladder arms.

Write `reports/MODEL_LADDER_REPORT.md` with:

- first failing arm,
- cheapest passing arm,
- whether CAM matched the fixed control,
- which direct/no-CAM controls should be run next.

## Execution Choice

Plan complete. Execute setup only in the current session. Launch model arms
later in separate fresh Codex sessions so model selection and token reporting
can be controlled arm by arm.
