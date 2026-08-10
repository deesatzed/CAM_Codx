# CAM_Codx Program Manager Implementation Plan

> **For Codex:** Implement this plan task-by-task with tests and evidence at
> every boundary.

**Goal:** Add an auditable CAM_Codx manager and routine Codex SWE workflow,
then close the CAM_CAM tournament correctness gates and run one bounded,
approval-controlled self-enhancement attempt.

**Architecture:** CAM_Codx owns a dependency-light packet/approval CLI and
Codex skill. CAM_CAM remains the runtime owner. The manager invokes only a
fixed operation allowlist through the setup-generated `cam-codx` wrapper and
records immutable scope/exit receipts. Self-enhancement is staged and never
implicitly swapped.

**Tech Stack:** Python 3.11+ standard library for the manager, pytest,
Typer/CAM_CAM runtime, JSON/TOML/Markdown, SHA-256 content addressing.

---

### Task 1: Add the manager protocol and packet/approval tests

**Files:**
- Create: `tools/cam_manager.py`
- Create: `tests/test_cam_manager.py`

Implement deterministic scope hashing, packet creation, approval issuance,
single-use consumption, expiry/mismatch rejection, mode `0700/0600` state,
and fixed operation allowlisting. Use `subprocess.run` with an argv list only;
never invoke a shell. Add `prepare`, `approve`, `execute`, and `status`
subcommands. Read-only operations execute without approval; spend/live-mutation
operations require a matching approval.

### Task 2: Install the routine Codex skill

**Files:**
- Create: `templates/skills/cam-codx-swe/SKILL.md`
- Modify: `tools/cam_setup_wizard.py`
- Modify: `tests/test_cam_setup_wizard.py`

Install the routine skill alongside the existing setup skill while preserving
the existing function/API behavior. Document the inspect → plan → approve →
execute → verify path and explicitly prohibit implicit mining, provider spend,
profile promotion, or self-enhancement swap.

### Task 3: Document the manager and routine path

**Files:**
- Create: `docs/CAM_CODEX_PROGRAM_MANAGER.md`
- Modify: `README.md`
- Modify: `docs/QUICKSTART_CODEX.md`
- Modify: `PROGRESS.md`
- Modify: `DECISIONS.md`

Document ownership, exact commands, approval state location, receipt hygiene,
the bounded self-enhance flow, and the distinction between ordinary SWE work
and explicit mining/model-comparison work.

### Task 4: Close CAM_CAM tournament correctness gates

**Files:**
- Modify: `/Volumes/WS4TB/repo622sn/CAM_CAM/src/claw/models/benchmark.py`
- Modify: `/Volumes/WS4TB/repo622sn/CAM_CAM/src/claw/models/scoring.py`
- Modify: `/Volumes/WS4TB/repo622sn/CAM_CAM/src/claw/models/tournament.py`
- Modify: corresponding benchmark/scoring/tournament tests

Make failed charged receipts visible in stage evidence and preserve their
conservative cost. Ensure resume never overwrites or silently retries a
terminal failed receipt. Ensure advancement filters exclusions before ranking,
uses conservative parent spend, and repeat plans preserve the original
first-round fixture/request controls. Make repeat stability compare the same
model and same fixture across first-round and repeat reports.

### Task 5: Verify and run bounded self-enhancement

Run CAM_Codx focused tests and CAM_CAM focused benchmark/profile/self-enhance
tests. Run the manager against a fake wrapper for protocol verification. Then,
only with an explicit manager approval receipt, run CAM self-enhancement in
supervised mode with a small task cap and `--skip-swap`; inspect the validation
artifact. A live swap is a separate action and is not implied by this task.

### Task 6: Publish both repositories

Run the full relevant suites, `git diff --check`, secret/database scans, and
runtime identity checks. Update durable truth with exact results. Commit and
push CAM_Codx and CAM_CAM separately; do not commit private manager state,
benchmark artifacts, databases, or environment files.

