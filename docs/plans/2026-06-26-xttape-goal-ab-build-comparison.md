# XTtape Goal A/B Build Comparison Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a frozen `/goal GOAL.md` A/B experiment that builds two XTtape ticker apps with the same spec while allowing only the CAM arm to use CAM_Codx and `claw.db` for troubleshooting.

**Architecture:** Add an experiment setup under `/Volumes/WS4TB/ccxt/xttape-build-ab` with a read-only evaluator, two isolated build arms, metrics schemas, and comparison-report templates. The plan creates experiment scaffolding and goal contracts only; the actual app builds start later in two separate `/goal GOAL.md` sessions.

**Tech Stack:** Markdown goal contracts, Bash evaluator scripts, JSON metrics files, Python standard library scoring script, FastAPI/React/Vite/Prisma app requirements inherited from the XTtape final build brain.

---

## Source Inputs

Use these committed source artifacts:

- `docs/showpieces/xttape-cam-comparison/runs/final/AGENTS.md`
- `docs/showpieces/xttape-cam-comparison/runs/final/GOAL.md`
- `docs/showpieces/xttape-cam-comparison/runs/final/DECISIONS.md`
- `docs/showpieces/xttape-cam-comparison/runs/final/PROGRESS.md`
- `docs/showpieces/xttape-cam-comparison/runs/final/CAM_MEMORY_APPLIED.md`
- `docs/showpieces/xttape-cam-comparison/docs/plans/2026-06-25-xttape-live-ai-news-ticker.md`
- `docs/plans/2026-06-26-xttape-goal-ab-build-comparison-design.md`

Do not use legacy loose notes. Do not copy code from mined repositories.

## Task 1: Create Experiment Root

**Files:**

- Create directory: `/Volumes/WS4TB/ccxt/xttape-build-ab`
- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/README.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/.gitignore`

**Step 1: Create directories**

```bash
mkdir -p /Volumes/WS4TB/ccxt/xttape-build-ab/{evaluator/scripts,evaluator/fixtures,control/app,cam/app,reports/screenshots}
```

Expected: directories exist.

**Step 2: Write README**

Include:

- purpose,
- no-human-interference rule,
- exact `/goal` launch commands,
- artifact layout,
- warning that evaluator is frozen before runs.

**Step 3: Write `.gitignore`**

Ignore:

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
```

Do not ignore metrics, reports, screenshots, or evaluator output unless a
screenshot contains secrets.

**Step 4: Verify**

```bash
test -d /Volumes/WS4TB/ccxt/xttape-build-ab/evaluator
test -d /Volumes/WS4TB/ccxt/xttape-build-ab/control/app
test -d /Volumes/WS4TB/ccxt/xttape-build-ab/cam/app
```

Expected: all commands exit 0.

## Task 2: Create Frozen Acceptance Contract

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/ACCEPTANCE.md`

**Step 1: Write acceptance gates**

The file must require:

- FastAPI health endpoint works,
- browser app runs locally,
- Prisma/SQLite validates and stores data,
- replay fixtures create one official/RSS item and one X/social signal,
- ticker API returns receipt-backed items,
- provider fallback works with no `XAI_API_KEY`,
- one learning action writes signal and audit records,
- screenshot shows RSS/official, X/social, explanation, receipts, and learning action,
- no-secret scan passes,
- final `RUN_METRICS.json` validates against the schema.

**Step 2: Add non-goals**

State that live X credentials, paid AI calls, production deployment, and social
write actions are out of scope.

**Step 3: Verify**

```bash
rg -n "FastAPI|Prisma|screenshot|RUN_METRICS|no-secret" /Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/ACCEPTANCE.md
```

Expected: all required concepts appear.

## Task 3: Create Metrics Schema

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/METRICS_SCHEMA.json`

**Step 1: Define required fields**

Use this JSON shape:

```json
{
  "run_id": "control-or-cam",
  "arm": "control",
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601-or-null",
  "wall_clock_minutes": 0,
  "token_usage_status": "reported|unavailable",
  "token_usage_total": null,
  "tool_call_count": null,
  "shell_command_count": null,
  "failed_command_count": 0,
  "failed_test_or_build_cycles": 0,
  "human_intervention_attempts": 0,
  "autonomous_recovery_attempts": 0,
  "final_acceptance_status": "pass|partial|fail|blocked",
  "evaluator_score": 0,
  "screenshots_count": 0,
  "tests_passing": false,
  "no_secret_scan_passed": false,
  "notes": []
}
```

**Step 2: Verify valid JSON**

```bash
python -m json.tool /Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/METRICS_SCHEMA.json >/tmp/xttape_metrics_schema.json
```

Expected: command exits 0.

## Task 4: Create Evaluator Scripts

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/scripts/check_app.sh`
- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/scripts/score_run.py`

**Step 1: Write `check_app.sh`**

The script accepts one app root:

```bash
./evaluator/scripts/check_app.sh /Volumes/WS4TB/ccxt/xttape-build-ab/control/app
```

It should check for:

- `RUN_METRICS.json`,
- `RUN_REPORT.md`,
- app truth files copied into the app root,
- evidence directory,
- screenshot directory,
- no obvious secrets using `rg`.

It should print `PASS`, `PARTIAL`, or `FAIL`.

**Step 2: Write `score_run.py`**

The script accepts one arm root and outputs JSON:

```bash
python evaluator/scripts/score_run.py control
```

Score simple objective criteria:

- metrics file exists,
- report exists,
- tests evidence exists,
- screenshot evidence exists,
- no-secret scan passed,
- evaluator status is pass or partial,
- CAM ledger exists only for CAM arm,
- no-CAM attestation exists only for control arm.

**Step 3: Verify script syntax**

```bash
bash -n /Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/scripts/check_app.sh
python -m py_compile /Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/scripts/score_run.py
```

Expected: both commands exit 0.

## Task 5: Create Shared App Specification

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/SHARED_APP_SPEC.md`

**Step 1: Copy requirements from final XTtape brain**

Include the same requirements for both arms:

- FastAPI API,
- React/Vite/TypeScript UI,
- Prisma/SQLite persistence,
- read-only source/X connector boundary,
- replay fixtures,
- source receipts,
- provider fallback,
- learning action,
- screenshots and evidence.

**Step 2: Add implementation freedom**

Allow each autonomous run to choose package manager details and file layout
inside its own `app/` folder, as long as evaluator gates pass.

**Step 3: Verify**

```bash
rg -n "FastAPI|React|Prisma|replay|receipts|fallback|learning" /Volumes/WS4TB/ccxt/xttape-build-ab/evaluator/SHARED_APP_SPEC.md
```

Expected: all required terms appear.

## Task 6: Create Control GOAL.md

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/control/GOAL.md`

**Step 1: Write control goal**

The goal must:

- instruct Codex to build only inside `control/app`,
- read the frozen evaluator,
- build the XTtape app from `SHARED_APP_SPEC.md`,
- avoid CAM_Codx, `claw.db`, CAM MCP/CLI, and CAM context packets,
- avoid inspecting `../cam`,
- record all metrics,
- stop rather than ask the user for help,
- write `NO_CAM_ATTESTATION.md`.

**Step 2: Add exact launch command**

```text
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/control/GOAL.md
```

**Step 3: Verify prohibitions**

```bash
rg -n "claw.db|CAM_Codx|NO_CAM_ATTESTATION|do not inspect.*cam|stop rather than ask" /Volumes/WS4TB/ccxt/xttape-build-ab/control/GOAL.md
```

Expected: all control safeguards appear.

## Task 7: Create CAM GOAL.md

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/cam/GOAL.md`

**Step 1: Write CAM goal**

The goal must:

- instruct Codex to build only inside `cam/app`,
- read the frozen evaluator,
- build the same XTtape app from `SHARED_APP_SPEC.md`,
- use CAM_Codx and `claw.db` for initial methodology recall,
- use CAM_Codx and `claw.db` again after build/test/debug failures,
- record each recall in `CAM_USAGE_LEDGER.md`,
- avoid inspecting `../control`,
- avoid copying mined repo code,
- stop rather than ask the user for help,
- record all metrics.

**Step 2: Add exact launch command**

```text
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/cam/GOAL.md
```

**Step 3: Verify CAM requirements**

```bash
rg -n "claw.db|CAM_USAGE_LEDGER|failure|do not inspect.*control|stop rather than ask" /Volumes/WS4TB/ccxt/xttape-build-ab/cam/GOAL.md
```

Expected: all CAM safeguards appear.

## Task 8: Create Report Templates

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/reports/AB_COMPARISON_REPORT.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/reports/AB_METRICS_SUMMARY.json`

**Step 1: Write report template**

Sections:

- executive summary,
- run setup,
- control result,
- CAM result,
- metric table,
- app screenshots,
- failure/recovery comparison,
- CAM recall usefulness,
- verdict,
- limitations.

**Step 2: Write empty metrics summary**

Use valid JSON with placeholders:

```json
{
  "control": null,
  "cam": null,
  "verdict": "not-run"
}
```

**Step 3: Verify**

```bash
python -m json.tool /Volumes/WS4TB/ccxt/xttape-build-ab/reports/AB_METRICS_SUMMARY.json >/tmp/xttape_ab_metrics_summary.json
```

Expected: command exits 0.

## Task 9: Freeze Experiment Manifest

**Files:**

- Create: `/Volumes/WS4TB/ccxt/xttape-build-ab/EXPERIMENT_MANIFEST.md`

**Step 1: Record source artifacts**

List every source file copied from CAM_Codx, with commit hash.

**Step 2: Record run rules**

Include:

- no human guidance after `/goal`,
- no cross-arm inspection,
- evaluator frozen before run,
- same app spec,
- same acceptance gates,
- CAM recall allowed only in CAM arm,
- user questions count as intervention.

**Step 3: Record launch commands**

```text
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/control/GOAL.md
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/cam/GOAL.md
```

**Step 4: Verify**

```bash
rg -n "/goal|no human|frozen|same app spec|intervention" /Volumes/WS4TB/ccxt/xttape-build-ab/EXPERIMENT_MANIFEST.md
```

Expected: all run rules appear.

## Task 10: Commit Setup Artifacts

**Files:**

- Stage: `/Volumes/WS4TB/ccxt/xttape-build-ab`

**Step 1: Run final checks**

```bash
find /Volumes/WS4TB/ccxt/xttape-build-ab -maxdepth 3 -type f | sort
rg -n "s[k]-or-v1|OPENROUTER_API_KEY[[:space:]]*=|XAI_API_KEY[[:space:]]*=|api[_-]?key\\s*[=:]|Authorization:[[:space:]]+Bearer|password\\s*[=:]|secret\\s*[=:]" /Volumes/WS4TB/ccxt/xttape-build-ab
```

Expected: file list prints; secret scan returns no matches.

**Step 2: Commit if this is made into a git repo**

If `/Volumes/WS4TB/ccxt/xttape-build-ab` is initialized as its own repo:

```bash
cd /Volumes/WS4TB/ccxt/xttape-build-ab
git init
git add .
git commit -m "test: add XTtape goal A/B experiment harness"
```

If it remains a local experiment folder, record the file list and checks in
`EXPERIMENT_MANIFEST.md` instead.

## Task 11: Launch The Two Goal Runs

**Files:**

- Use: `/Volumes/WS4TB/ccxt/xttape-build-ab/control/GOAL.md`
- Use: `/Volumes/WS4TB/ccxt/xttape-build-ab/cam/GOAL.md`

**Step 1: Launch control in a fresh Codex session**

```text
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/control/GOAL.md
```

Do not answer clarification questions. If the run asks for help, record an
intervention and stop or let it mark blocked according to its goal.

**Step 2: Launch CAM in a fresh Codex session**

```text
/goal /Volumes/WS4TB/ccxt/xttape-build-ab/cam/GOAL.md
```

Do not answer clarification questions. CAM may use CAM_Codx and `claw.db`, but
only inside its own rules.

**Step 3: Preserve run outputs**

Ensure each arm produced:

- `RUN_METRICS.json`,
- `RUN_REPORT.md`,
- evidence directory,
- screenshot directory,
- attestation or CAM usage ledger.

## Task 12: Score And Publish Results

**Files:**

- Modify: `/Volumes/WS4TB/ccxt/xttape-build-ab/reports/AB_COMPARISON_REPORT.md`
- Modify: `/Volumes/WS4TB/ccxt/xttape-build-ab/reports/AB_METRICS_SUMMARY.json`

**Step 1: Run evaluator**

```bash
cd /Volumes/WS4TB/ccxt/xttape-build-ab
bash evaluator/scripts/check_app.sh control/app
bash evaluator/scripts/check_app.sh cam/app
python evaluator/scripts/score_run.py control
python evaluator/scripts/score_run.py cam
```

Expected: each command prints objective status or JSON.

**Step 2: Write comparison report**

Compare:

- completion,
- wall-clock time,
- token usage,
- failed cycles,
- human interventions,
- final app evidence,
- whether CAM recall directly fixed any failures.

**Step 3: Decide public verdict**

Allowed verdicts:

- `CAM_WINS`
- `CONTROL_WINS`
- `TIE`
- `INCONCLUSIVE`

Use `INCONCLUSIVE` if token data is unavailable for both runs or if run
conditions drift.

## Execution Choice

After this setup plan is approved, execute it as setup work only. The actual
two app builds should run later in separate fresh Codex `/goal` sessions so
there is no accidental cross-contamination from this planning thread.
