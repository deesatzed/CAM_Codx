# XTtape CAM vs Vanilla Comparison Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Status:** Superseded by the completed XTtape showpiece bundle in `docs/showpieces/xttape-cam-comparison/`. The completed run intentionally excludes `XTtapeNotes.md`; use `docs/showpieces/xttape-cam-comparison/INITIAL_REQUEST.md`, `COMPARISON_SUMMARY.md`, `runs/final/`, and `docs/plans/2026-06-25-xttape-live-ai-news-ticker.md` as the current source of truth.

**Goal:** Compare two independently generated XTtape project-brain outputs before building any app code, so we can decide whether CAM_Codx and `claw.db` materially improve the app plan.

**Architecture:** This is a controlled documentation experiment. One output is generated from the raw XTtape request without CAM memory; the second uses the same input plus CAM_Codx methodology recall from local `claw.db`. A scorecard decides whether to build, revise, or stop.

**Tech Stack:** Markdown, Git, Codex, CAM_Codx, local SQLite `claw.db`; no app runtime, no FastAPI, no Node, no Prisma, and no frontend code until the comparison gate passes.

---

## Non-Negotiable Drift Locks

- Do not build app code during this protocol.
- Do not scaffold FastAPI, Node, Prisma, React, or MCP app code.
- Do not modify the raw input after it is frozen.
- Do not read or print `.env` values.
- Do not commit `.env`, `claw.db`, `claw*.toml`, or private config.
- Do not let the vanilla run inspect CAM_Codx methodology docs, `claw.db`, existing XTtape generated docs, or the CAM comparison output.
- Do not let the CAM run change the core product request unless the change is explicitly justified in `CAM_MEMORY_APPLIED.md`.
- Do not proceed to app build until `COMPARISON_SCORECARD.md` has a clear verdict.

## Fixed Local Paths

- Showpiece cockpit: `/Volumes/WS4TB/ccxt`
- Fresh CAM_Codx clone: `/Volumes/WS4TB/ccxt/CAM_Codx`
- Local env file: `/Volumes/WS4TB/ccxt/.env`
- Local CAM database: `/Volumes/WS4TB/ccxt/claw.db`
- Local CAM TOML files:
  - `/Volumes/WS4TB/ccxt/claw.toml`
  - `/Volumes/WS4TB/ccxt/claw_grok.toml`
  - `/Volumes/WS4TB/ccxt/claw_cheap.toml`
  - `/Volumes/WS4TB/ccxt/claw_dspro.toml`
- Source notes: `/Volumes/WS4TB/repo622sn/XTtape/XTtapeNotes.md`

## Output Layout

Create this structure:

```text
/Volumes/WS4TB/ccxt/xttape-comparison/
  INPUTS/
    INITIAL_REQUEST.md
    XTtapeNotes.md
    INPUT_MANIFEST.md
  RUNS/
    vanilla/
      PROMPT.md
      AGENTS.md
      GOAL.md
      DECISIONS.md
      PROGRESS.md
      RUN_NOTES.md
    cam/
      PROMPT.md
      AGENTS.md
      GOAL.md
      DECISIONS.md
      PROGRESS.md
      CAM_MEMORY_APPLIED.md
      RUN_NOTES.md
  COMPARE/
    DIFF_SUMMARY.md
    COMPARISON_SCORECARD.md
    BUILD_DECISION.md
    DRIFT_LOG.md
```

## Task 1: Freeze The Shared Input

**Files:**
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/INPUTS/INITIAL_REQUEST.md`
- Copy: `/Volumes/WS4TB/repo622sn/XTtape/XTtapeNotes.md` to `/Volumes/WS4TB/ccxt/xttape-comparison/INPUTS/XTtapeNotes.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/INPUTS/INPUT_MANIFEST.md`

**Checklist:**
- [ ] Create the `xttape-comparison` folder structure.
- [ ] Copy `XTtapeNotes.md` into `INPUTS/`.
- [ ] Write `INITIAL_REQUEST.md` as the single shared user request.
- [ ] Record SHA256 hashes for `INITIAL_REQUEST.md` and `XTtapeNotes.md`.
- [ ] Record the date, source paths, and rule: "No app code before comparison verdict."

**Verification:**

Run:

```bash
test -f /Volumes/WS4TB/ccxt/xttape-comparison/INPUTS/INITIAL_REQUEST.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/INPUTS/XTtapeNotes.md
shasum -a 256 /Volumes/WS4TB/ccxt/xttape-comparison/INPUTS/*.md
```

Expected: both files exist and hashes are recorded in `INPUT_MANIFEST.md`.

## Task 2: Write The Vanilla Prompt

**Files:**
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/PROMPT.md`

**Checklist:**
- [ ] Prompt uses only `INPUTS/INITIAL_REQUEST.md` and `INPUTS/XTtapeNotes.md`.
- [ ] Prompt asks for exactly four files: `AGENTS.md`, `GOAL.md`, `DECISIONS.md`, `PROGRESS.md`.
- [ ] Prompt forbids app code, scaffolding, package installs, and source implementation.
- [ ] Prompt forbids using CAM_Codx, `claw.db`, existing XTtape docs, or prior CAM comparison outputs.
- [ ] Prompt requires `RUN_NOTES.md` listing what context was used.

**Vanilla Prompt Requirements:**

The vanilla run must answer:

- What app should be built?
- What constraints matter?
- What should be accepted as proof?
- What decisions were made from the notes?
- What is unknown or blocked?

It must not answer:

- What CAM methodologies apply?
- What `claw.db` says.
- How to build the app yet.

## Task 3: Run The Vanilla Project-Brain Generation

**Files:**
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/AGENTS.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/GOAL.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/DECISIONS.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/PROGRESS.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/RUN_NOTES.md`

**Checklist:**
- [ ] Run in a fresh context where possible.
- [ ] Do not export `CAM_CODEX_MCP_DB_PATH`.
- [ ] Do not inspect `/Volumes/WS4TB/ccxt/claw.db`.
- [ ] Do not inspect `/Volumes/WS4TB/repo622sn/XTtape/AGENTS.md`, `GOAL.md`, `DECISIONS.md`, or `PROGRESS.md`.
- [ ] Save only the five required run files.

**Verification:**

Run:

```bash
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/AGENTS.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/GOAL.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/DECISIONS.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/PROGRESS.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/vanilla/RUN_NOTES.md
```

Expected: all files exist and no app code exists under `RUNS/vanilla/`.

## Task 4: Write The CAM Prompt

**Files:**
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/PROMPT.md`

**Checklist:**
- [ ] Prompt uses the same `INPUTS/INITIAL_REQUEST.md` and `INPUTS/XTtapeNotes.md`.
- [ ] Prompt permits CAM_Codx to query `/Volumes/WS4TB/ccxt/claw.db`.
- [ ] Prompt requires selective methodology use, not blind retrieval.
- [ ] Prompt requires applied and rejected methodology sections.
- [ ] Prompt requires the same four project-brain files as vanilla.
- [ ] Prompt requires `CAM_MEMORY_APPLIED.md`.
- [ ] Prompt forbids app code and scaffolding.

**CAM Recall Requirements:**

The CAM run should look for methodology categories relevant to XTtape:

- confidence scoring and conservative fusion,
- time-decayed interest/ranking,
- source-boundary adapters,
- immutable audit trails,
- MCP/tool safety,
- URL/input/security guards,
- self-test and smoke-gate patterns,
- API cost/rate tracking,
- showpiece proof and screenshot discipline.

The CAM run must reject:

- stale or embryonic methods without clear value,
- methods that change the product away from a live AI news ticker,
- methods that add broad complexity without a testable benefit,
- methods that increase secret or social-platform compliance risk.

## Task 5: Run The CAM Project-Brain Generation

**Files:**
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/AGENTS.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/GOAL.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/DECISIONS.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/PROGRESS.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/CAM_MEMORY_APPLIED.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/RUN_NOTES.md`

**Checklist:**
- [ ] Use the same frozen input hashes from Task 1.
- [ ] Query CAM memory from `/Volumes/WS4TB/ccxt/claw.db`.
- [ ] Document every applied method with id or traceable search evidence.
- [ ] Document rejected methods and why they were not used.
- [ ] Keep product identity stable: XTtape remains a live AI news ticker.
- [ ] Save only the required run files.

**Verification:**

Run:

```bash
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/AGENTS.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/GOAL.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/DECISIONS.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/PROGRESS.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/CAM_MEMORY_APPLIED.md
test -f /Volumes/WS4TB/ccxt/xttape-comparison/RUNS/cam/RUN_NOTES.md
```

Expected: all files exist, `CAM_MEMORY_APPLIED.md` lists applied and rejected methods, and no app code exists under `RUNS/cam/`.

## Task 6: Compare The Two Project Brains

**Files:**
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/COMPARE/DIFF_SUMMARY.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/COMPARE/COMPARISON_SCORECARD.md`
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/COMPARE/DRIFT_LOG.md`

**Checklist:**
- [ ] Compare `AGENTS.md` side by side.
- [ ] Compare `GOAL.md` side by side.
- [ ] Compare `DECISIONS.md` side by side.
- [ ] Compare `PROGRESS.md` side by side.
- [ ] Mark differences as useful, neutral, harmful, or unclear.
- [ ] Identify whether CAM adds product value or only process ceremony.
- [ ] Identify whether CAM over-steers the product away from the request.
- [ ] Document all comparison findings before any build decision.

**Scorecard Categories:**

Score each category from 0 to 3:

- product fidelity,
- live-source readiness,
- trust and credibility model,
- user learning quality,
- safety and compliance,
- testability,
- auditability,
- cost/rate awareness,
- showpiece clarity,
- build feasibility.

**Verdict Rules:**

- `BUILD_CAM`: CAM keeps product fidelity and improves at least 5 categories without harmful scope drift.
- `BUILD_VANILLA`: CAM adds little value or mostly ceremony, while vanilla is clear and buildable.
- `REVISE_CAM_PROMPT`: CAM has useful ideas but over-steers, adds untestable scope, or uses weak memory.
- `STOP_COMPARE`: outputs are too similar to prove value or too different to compare fairly.

## Task 7: Decide Whether To Build

**Files:**
- Create: `/Volumes/WS4TB/ccxt/xttape-comparison/COMPARE/BUILD_DECISION.md`

**Checklist:**
- [ ] Record the final verdict from Task 6.
- [ ] Record whether any app build is approved.
- [ ] If approved, name exactly which output becomes the source of truth.
- [ ] If not approved, record why and what must be revised.
- [ ] Do not begin app code until this file has a verdict.

**Build Decision Template:**

```markdown
# XTtape Build Decision

Date: 2026-06-25

## Verdict

BUILD_CAM | BUILD_VANILLA | REVISE_CAM_PROMPT | STOP_COMPARE

## Reason

Short explanation.

## Source Of Truth For Any Build

Path to selected run folder, or "none".

## Required Next Step

Exact next action.
```

## Task 8: Commit The Protocol And Results

**Files:**
- Modify: Git state in `/Volumes/WS4TB/ccxt/CAM_Codx` for this checklist only.
- Optional local-only comparison outputs under `/Volumes/WS4TB/ccxt/xttape-comparison/`.

**Checklist:**
- [ ] Commit this protocol file in the fresh CAM_Codx clone.
- [ ] Keep private runtime state outside Git.
- [ ] After comparison outputs exist, decide whether to commit sanitized result summaries to CAM_Codx.
- [ ] Never commit `.env`, `claw.db`, or TOML files containing private local paths or secrets.

**Verification:**

Run:

```bash
git -C /Volumes/WS4TB/ccxt/CAM_Codx status --short --branch
```

Expected: only intended protocol docs are tracked in CAM_Codx; private files remain outside the clone.

## Final Stop Rule

Stop immediately after `BUILD_DECISION.md` is written.

Do not scaffold the app in the same step. A separate approved build plan must start from the selected source-of-truth run folder.
