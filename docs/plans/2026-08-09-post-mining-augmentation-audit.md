# Post-Mining CAM Augmentation Audit Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task by task.

**Goal:** Clean the current CAM_CAM and CAM_Codx Git state safely, convert intentional local truth into tracked artifacts, and publish a no-spend audit that turns newly mined findings into a ranked CAM enhancement backlog.

**Architecture:** Keep runtime/corpus ownership in CAM_CAM and program-management/adoption ownership in CAM_Codx. Treat SQLite sidecars as retained runtime state, mining findings as review inputs, and all enhancement recommendations as gated proposals rather than automatic self-modification.

**Tech Stack:** Git, Markdown, TOML, Python 3, SQLite, pytest, CAM CLI

---

### Task 1: Establish the approved design and isolated workspace

**Files:**
- Create: `docs/plans/2026-08-09-post-mining-augmentation-audit-design.md`
- Create: `docs/plans/2026-08-09-post-mining-augmentation-audit.md`

**Steps:**

1. Create a dedicated CAM_Codx worktree from the current local `main` commit.
2. Copy the existing untracked `GOAL_CAM_SUBSCIBED.md` into the worktree without changing its contents.
3. Record the approved cleanup and audit design.
4. Commit the design independently, then add this implementation plan.

**Verification:**

Run `git status --short --branch` and confirm only expected implementation files remain uncommitted.

### Task 2: Normalize CAM_CAM dirty runtime state

**Files:**
- Modify: `/Volumes/WS4TB/repo622sn/CAM_CAM/.gitignore`
- Modify: `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.toml`
- Modify: `/Volumes/WS4TB/repo622sn/CAM_CAM/tests/test_config.py`
- Create if needed: `/Volumes/WS4TB/repo622sn/CAM_CAM/DB_REGISTRY.md`

**Steps:**

1. Add `*.db-wal` and `*.db-shm` ignore patterns without deleting current sidecars.
2. Review every `claw.toml` delta and confirm each sibling path exists.
3. Resolve the configuration's DB registry reference against a real tracked document.
4. Align the stale live-config test assertion with the already tracked canonical `claw.db` path.
5. Parse `claw.toml` with Python `tomllib`.
6. Run SQLite integrity checks on the root and configured sibling databases.
7. Run focused configuration, model-profile, and mining tests with `PYTHONPATH` pinned to the current checkout.
8. Commit only the reviewed configuration, test, ignore rules, and registry documentation.

**Verification:**

Run `git status --short --branch`; it must be clean while the physical WAL/SHM files remain present.

### Task 3: Correct CAM_Codx active truth and publish the audit

**Files:**
- Modify: `GOAL.md`
- Create: `GOAL_CAM_SUBSCIBED.md`
- Modify: `agent-packs/contract/cam_agent_capabilities.json`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/REPO_MAP.md`
- Modify: `docs/config/CONFIG_DRIFT_CHECKS.md`
- Modify: `docs/config/LOCAL_CONFIG_ALIGNMENT.md`
- Create: `docs/reports/2026-08-09-post-mining-cam-augmentation-audit.md`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`

**Steps:**

1. Correct active runtime paths from the old WS4TBr checkout to `/Volumes/WS4TB/repo622sn/CAM_CAM` across the goal, capability contract, architecture, repo map, and config guidance.
2. Track the validated subscribed-goal contract without renaming it.
3. Record verified post-mining corpus state, existing CAM capabilities, candidate findings, decisions, owners, gates, and priorities.
4. Explicitly distinguish already-present capabilities from recommended adaptations and rejected duplication.
5. Record that the audit performs no new provider calls and does not run automatic self-enhancement.
6. Update durable progress and decision logs.

**Verification:**

Search active truth files for the old CAM_CAM path and confirm no active reference remains.

### Task 4: Verify both repositories and publish exact commits

**Files:**
- Verify all files changed in Tasks 1-3

**Steps:**

1. Run CAM_Codx agent-pack, setup, contract, and documentation checks.
2. Run the CAM session preflight against the live runtime, config, and database.
3. Run `git diff --check` in both repositories.
4. Fetch origin for each repository and stop on non-fast-forward divergence.
5. Commit exact intended files, push both repositories, and fast-forward the original CAM_Codx checkout.
6. Remove the original untracked goal only after byte-for-byte confirmation that it is committed.
7. Remove the temporary worktree only after its commits are reachable from `origin/main`.

**Verification:**

Confirm:

- local `main` equals `origin/main` in both repositories;
- both Git worktrees are clean;
- live database integrity is `ok`;
- live WAL/SHM files were retained; and
- the audit report is reachable from committed `main`.
