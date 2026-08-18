# CAM_Codx Unified Control Plane Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to
> implement this plan task-by-task.

**Goal:** Make one `cam-codx` skill the normal control plane for every CAM_CAM
feature while preserving direct CAM_CAM commands for troubleshooting and
providing a verified source-to-outcome SWE Run.

**Architecture:** Extend the existing
`agent-packs/contract/cam_agent_capabilities.json` into the single capability
registry. CAM_Codx performs semantic routing, risk disclosure, approvals, and
evidence orchestration. CAM_CAM exports its registered command manifest and
continues to own every runtime operation and CAM-SEQ record. Existing helpers
are composed, not rewritten.

**Tech Stack:** Python 3.11+, argparse/Typer, JSON, pytest, SQLite through
CAM_CAM's existing repository layer, Markdown generation.

**Design:** `docs/plans/2026-08-12-cam-codx-control-plane-design.md`

---

## Task 1: Export The Actual CAM_CAM Command Manifest

**CAM_CAM files:**

- Create: `src/claw/cli/capability_manifest.py`
- Modify: `src/claw/cli/_monolith.py`
- Modify: `src/claw/cli/__init__.py`
- Create: `tests/test_cli_capability_manifest.py`

1. Write a failing test that recursively inspects the Typer tree and expects a
   stable JSON payload containing every command/group path and `hidden` status.
   Assert `mine`, `models benchmark run`, hidden `forge-export`, and hidden
   `evolution approve`.
2. Run
   `PYTHONPATH=src python -m pytest -q tests/test_cli_capability_manifest.py`.
   Expected: FAIL because the helper and command do not exist.
3. Implement a pure recursive inventory function and read-only
   `cam doctor capabilities --json`. It must not load config, initialize a DB,
   call a provider, or write a file.
4. Test deterministic ordering and no filesystem changes in a temporary cwd.
5. Verify:

   ```bash
   PYTHONPATH=src python -m pytest -q tests/test_cli_capability_manifest.py tests/test_cli_ux.py
   PYTHONPATH=src python -m claw.cli doctor capabilities --json
   git diff --check
   ```

6. Commit: `feat: export CAM command capability manifest`.

## Task 2: Extend The Existing Capability Contract

**CAM_Codx files:**

- Modify: `agent-packs/contract/cam_agent_capabilities.json`
- Modify: `tools/generate_agent_packs.py`
- Create: `tools/validate_cam_capabilities.py`
- Modify: `tests/test_agent_packs.py`
- Create: `tests/test_cam_capability_registry.py`

1. Write failing tests requiring contract schema `2.0`, `workflow_intents`, and
   `command_routes`. Each route needs command path, canonical/alias status,
   CAM_Codx route, risk/side-effect class, default mode, approval class,
   spend/config/promotion flags, artifacts, and runtime source reference.
2. Feed the Task 1 manifest fixture to the validator. Fail for every missing,
   duplicate, or multiply classified command path.
3. Extend the existing agent capability contract. Do not create another
   registry. Classify every current top-level, grouped, nested, and hidden path
   as `managed`, `troubleshooting_only`, or `hidden_compatibility`.
4. Update the generator to produce managed-capability and direct-runtime
   troubleshooting references from the contract.
5. Verify:

   ```bash
   python -m pytest -q tests/test_agent_packs.py tests/test_cam_capability_registry.py
   python tools/validate_cam_capabilities.py --manifest /tmp/cam-command-manifest.json
   python tools/generate_agent_packs.py --check
   git diff --check
   ```

6. Commit: `feat: classify all CAM runtime capabilities`.

## Task 3: Build The Read-Only CAM_Codx Router

**Files:**

- Create: `tools/cam_control_plane.py`
- Create: `tests/test_cam_control_plane.py`

1. Write failing typed request/result tests for explicit intent, target,
   request, runtime paths, optional run ID, and optional mining receipt. Cover
   all six SWE intents and all administrative families.
2. Test rejection of unknown intents, unresolved executables, ambiguous DB or
   config identity, and registry-missing commands.
3. Implement `cam_control_plane.py plan` with JSON and a human status card:

   ```bash
   python tools/cam_control_plane.py plan \
     --intent assess --target /path/to/repo \
     --request "Continue this build" \
     --cam-command /path/to/cam --cam-db /path/to/claw.db \
     --cam-config /path/to/claw.toml
   ```

4. The card shows goal, route, target, memory mode, writes, provider spend,
   mining, approval, and next action. Planning executes no CAM operation.
5. Hash target, DB, config, and model profiles before/after a fixture plan.
6. Verify `python -m pytest -q tests/test_cam_control_plane.py`, CLI help, and
   `git diff --check`.
7. Commit: `feat: add CAM_Codx control plane router`.

## Task 4: Drive Manager Operations From The Contract

**Files:**

- Modify: `tools/cam_manager.py`
- Modify: `tests/test_cam_manager.py`
- Modify: `tests/test_cam_capability_registry.py`

1. Write failing tests proving every executable managed route has a fixed argv
   prefix and phase and that hidden aliases cannot be selected as canonical
   manager operations.
2. Preserve regressions for secret rejection, invalid budgets, digest binding,
   expiry, single-use approval, and no-shell execution.
3. Replace duplicated hard-coded mappings with a strict contract adapter. Fail
   closed if the contract is unavailable or malformed.
4. Test read-only, local-write, provider-spend, code-mutation, promotion, and
   live-CAM-mutation classes separately.
5. Verify the two focused test files and `git diff --check`.
6. Commit: `feat: derive CAM approvals from capability contract`.

## Task 5: Create The One Canonical Skill

**Files:**

- Create: `templates/skills/cam-codx/SKILL.md`
- Create: `templates/skills/cam-codx/references/swe-playbooks.md`
- Create: `templates/skills/cam-codx/references/knowledge-playbooks.md`
- Create: `templates/skills/cam-codx/references/admin-playbooks.md`
- Create: `templates/skills/cam-codx/references/safety-and-approvals.md`
- Create: `tests/test_cam_codx_skill.py`

1. Write failing tests requiring truth-file inspection, all six SWE intents,
   mining, knowledge, models, self-enhance, evolution, doctor, setup, planner
   use before execution, no implicit mining/promotion, all references, and no
   stale paths/secrets.
2. Keep `SKILL.md` concise. Put detailed flows in progressive references and
   reuse Development Brief and pull/mine helpers rather than copying logic.
3. Verify:

   ```bash
   python -m pytest -q tests/test_cam_codx_skill.py
   python tools/validate_skill_frontmatter.py templates/skills/cam-codx/SKILL.md
   python /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py templates/skills/cam-codx
   git diff --check
   ```

4. Commit: `feat: add unified CAM_Codx skill`.

## Task 6: Migrate Setup To One Skill Safely

**Files:**

- Modify: `tools/cam_setup_wizard.py`
- Modify: `tests/test_cam_setup_wizard.py`
- Modify: `templates/skills/cam-codx-setup/SKILL.md`

1. Write failing tests: default installation installs `cam-codx`; an explicit
   migration moves known CAM-managed legacy directories into a timestamped
   backup; unrelated skills remain untouched; restoration metadata exists.
2. Cover `cam-codx-setup`, `cam-codx-swe`,
   `cam-codx-development-brief`, `cam-codx-pull-mine-dir`, and
   `cam-codx-session`.
3. Never silently delete. Without migration, install canonical and report old
   entries. With migration, move only known CAM-owned entries.
4. Verify setup/skill tests, wizard help, and `git diff --check`.
5. Commit: `feat: migrate CAM_Codx to one installed skill`.

## Task 7: Add A CAM_CAM Managed-Run Persistence Seam

**CAM_CAM files:**

- Create: `src/claw/managed_runs.py`
- Modify: `src/claw/cli/_monolith.py`
- Modify: `src/claw/cli/__init__.py`
- Create: `tests/test_managed_runs.py`
- Modify: `tests/test_camseq_foundation.py`

1. Write fixture-DB tests to start a run using `task_plans` and
   `run_connectomes`; record selected/rejected/deferred/needs-inspection
   decisions; link packet/pair; record landing; store typed outcome; render a
   source-to-outcome report.
2. Prove failed verification cannot set positive trust or recipe eligibility.
3. Implement with existing tables and repository methods. Use `run_events` for
   decision and mining-receipt links not represented by typed event tables.
4. Add a hidden list-form CLI seam for CAM_Codx/troubleshooting. Do not
   duplicate build, enhance, or validation logic.
5. Verify:

   ```bash
   PYTHONPATH=src python -m pytest -q tests/test_managed_runs.py tests/test_camseq_foundation.py
   git diff --check
   ```

6. Commit: `feat: persist managed source-to-outcome runs`.

## Task 8: Integrate Assess And Plan

**CAM_Codx files:**

- Modify: `tools/development_brief.py`
- Modify: `tools/cam_control_plane.py`
- Modify: `tests/test_development_brief.py`
- Modify: `tests/test_cam_control_plane.py`

1. Write failing structured-result tests preserving direct precedent,
   transferable analogy, and new hypothesis with provenance and limits.
2. Require `assess` and `plan` to open/continue a managed run without target,
   corpus, provider, profile, or config mutation.
3. Compose the existing primary-only brief query and target inspector. Build a
   reviewed plan/landing-map proposal through the managed-run seam.
4. Recommend explicit mining only when evidence is weak; never start it.
5. Verify the two focused files and `git diff --check`.
6. Commit: `feat: route CAM assessment and planning`.

## Task 9: Integrate Build, Fix, Verify, And Record

**CAM_Codx files:**

- Modify: `tools/cam_control_plane.py`
- Modify: `tools/cam_manager.py`
- Modify: `tests/test_cam_control_plane.py`
- Modify: `tests/test_cam_manager.py`

**CAM_CAM file:** `tests/test_managed_runs.py`

1. Write phase-transition tests: build/fix plan before mutation; matching
   approval for target mutation; exact verification checks/findings; record
   preview before write; failed/not-run verification cannot become success;
   abandoned candidates remain negative/deferred evidence.
2. Route existing `create`, `enhance`, `validate`, doctor, and security through
   manager packets. Codex may edit/test the target while CAM records evidence.
3. Run focused tests in both repos and `git diff --check`.
4. Commit each repo separately with scoped messages.

## Task 10: Integrate Mining And CAM Administration

**CAM_Codx files:**

- Modify: `tools/cam_control_plane.py`
- Modify: `tools/cam_pull_mine_dir.py`
- Modify: `tools/cam_manager.py`
- Modify: `tests/test_cam_pull_mine_dir.py`
- Modify: `tests/test_cam_control_plane.py`

1. Write explicit-scope tests for mining, knowledge, models, benchmark,
   self-enhance, evolution, doctor, and setup.
2. Assert invocation authorizes only the named route and bounds. Attach mining
   receipt path/hash to the run; report corpus/ledger delta; stop before build
   selection. Promotion/swap/rollback remain separate.
3. Compose the existing pull/mine coordinator, manager operations, and secure
   wrapper. Add no provider client to CAM_Codx.
4. Verify focused pull/mine, router, manager tests and `git diff --check`.
5. Commit: `feat: route mining and CAM administration`.

## Task 11: Align Help, Cheatsheets, And Troubleshooting Docs

**CAM_Codx files:** `README.md`, `docs/CAM_CHEATSHEET.md`,
`docs/CAM_CODEX_PROGRAM_MANAGER.md`, `docs/QUICKSTART_CODEX.md`,
`docs/STATUS.md`, `tools/generate_agent_packs.py`, `PROGRESS.md`.

**CAM_CAM files:** `README.md`, `docs/CAM_COMMAND_DECISION_TREE.md`,
`docs/CAM_OPERATOR_CHEATSHEET.md`, `docs/integrations/CAM_CODEX.md`,
`PROGRESS.md`.

1. Write documentation-contract tests requiring normal docs to start with
   `Use CAM_Codx to ...`, direct CAM_CAM docs to say troubleshooting/runtime
   development, and generated references to match the registry.
2. Assert `cam chat` is not described as a complete general router and active
   paths use `/Volumes/WS4TB/waswiki/...`.
3. Remove approved-but-not-implemented notices only after the skill, migration,
   router, and cross-repo gates pass.
4. Verify generated docs, focused docs/skill/setup tests, CAM_CAM manifest/UX
   tests, and `git diff --check`.
5. Commit each repo separately.

## Task 12: Run Cross-Repository Release Gates

### CAM_Codx focused gate

```bash
cd /Volumes/WS4TB/waswiki/CAM_Codx
python -m pytest -q tests/test_cam_capability_registry.py tests/test_cam_control_plane.py tests/test_cam_manager.py tests/test_cam_codx_skill.py tests/test_cam_setup_wizard.py tests/test_development_brief.py tests/test_cam_pull_mine_dir.py
python tools/generate_agent_packs.py --check
python tools/validate_skill_frontmatter.py templates/skills/cam-codx/SKILL.md
git diff --check
```

### CAM_CAM focused gate

```bash
cd /Volumes/WS4TB/waswiki/CAM_CAM
PYTHONPATH=src python -m pytest -q tests/test_cli_capability_manifest.py tests/test_cli_ux.py tests/test_managed_runs.py tests/test_camseq_foundation.py tests/test_application_packet.py tests/test_read_only_brief_query.py tests/test_models_cli.py tests/test_self_enhance.py tests/test_serial_evolution.py
git diff --check
```

Run both current full suites. Record unrelated baseline failures without
relabeling them and fix regressions caused by this work. Then install into a
temporary Codex home, verify only the canonical skill is newly installed,
exercise read-only assess, and prove target/corpus hashes do not change.

## Task 13: Prove The Mine-To-Build Chain On Fixtures

**Files:**

- Create: `tests/test_cam_control_plane_e2e.py`
- Create: `docs/reports/2026-08-12-cam-control-plane-fixture-proof.md`

Run a deterministic fixture through assess, candidate decisions, plan,
simulated landing, failed verification, corrected verification, and record.
Start a later assessment and prove only the verified outcome is positive
evidence. Do not describe fixture proof as live product proof.

## Task 14: Design And Build The MatrAIx/SESA Vertical Slice

Begin only after Tasks 1-13 pass.

1. Use CAM_Codx to assess the actual mined MatrAIx-Persona-8B and SESA
   evidence. Produce selected/rejected candidates and a landing map for the
   smallest useful evolutionary population-testing slice.
2. Freeze a separate product slice contract including target path, licensing,
   providers, tests, and data/privacy constraints. Do not edit a product repo
   until that design is accepted.
3. Implement through a separate target-repository plan and record all source
   components, adaptations, tests, failures, and outcomes into the SWE Run.
4. Start a fresh CAM_Codx assessment and prove the verified result can be
   retrieved with provenance. Keep rejected/hypothetical candidates separate.

## Completion Handoff

Update `GOAL.md`, `PROGRESS.md`, `DECISIONS.md`, and the capability audit with
the actual implemented state. Report commits, tests, limitations, remaining
legacy skills, and whether the real MatrAIx/SESA proof is complete or remains a
successor task.
