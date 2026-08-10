---
name: cam-codx-swe
description: Use CAM_Codx as an explicit workflow manager for Codex software-engineering build and update tasks, with CAM recall, evidence gates, phase approvals, and bounded verification.
---

# CAM_Codx SWE Workflow

Use this skill when Codex is building, debugging, reviewing, or updating a
software repository and CAM_Codx is available. CAM_Codx is a routine option,
not a hidden hook: ordinary Codex work remains possible when CAM is absent.

## Ownership

- CAM_Codx owns the workflow packet, phase approval, Codex skill, and evidence
  trail.
- CAM_CAM owns the `cam` runtime, model calls, local corpus, mining, and
  self-enhancement implementation.
- Codex owns task judgment, code edits, tests, and the final truth claim.

## Required flow

1. Inspect the target repository and read `GOAL.md`, `STANDARDS.md`,
   `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, `TASK_QUEUE.md`, and
   `AGENTS.md` when present.
2. Run read-only CAM identity/model status through the setup-generated wrapper
   when paths are known. Never print `.env` values or database contents.
3. Recall relevant CAM methods and use them as evidence-backed suggestions.
4. Create or update the target repository's goal and implementation plan.
5. Implement the smallest coherent change, then run the target tests and
   verification commands.
6. Record outcomes and limitations in the target repository's truth files.

The manager packet workflow is:

```text
python tools/cam_manager.py prepare models-current --wrapper <CAM_HOME>/scripts/cam-codx --state-dir <CAM_HOME>/local_state/CAM_Codx/manager
python tools/cam_manager.py approve <packet.json> --state-dir <CAM_HOME>/local_state/CAM_Codx/manager
python tools/cam_manager.py execute <packet.json> --approval <approval.json> --state-dir <CAM_HOME>/local_state/CAM_Codx/manager
```

Use the packet operation that matches the requested phase. Mutating or
provider-spend phases require a matching, unexpired, single-use approval.

## Explicit boundaries

- Do not mine repositories, run `cam mine`, or write to `claw.db` merely
  because a SWE task is being performed.
- Do not change a model profile because a catalog or benchmark recommends one.
- Do not run provider-spend operations without a frozen plan, visible budget,
  and a phase approval.
- Do not run `cam self-enhance ... swap` as part of a normal build task.
- Self-enhancement must be prepared with a bounded task count, validated, and
  separately approved before any live swap. Preserve the backup and rollback
  path.
- Treat CAM output as evidence to inspect, not as permission to edit files or
  claim completion.

## Self-enhancement packet

When the user explicitly requests CAM to improve itself, use this staged path:

1. `self-enhance-status` (read-only trigger assessment);
2. prepare and approve `self-enhance-start` with `--mode supervised`, a small
   `--max-tasks` value, and `--skip-swap`;
3. inspect the enhanced copy and run the validation gates;
4. present protected-file changes, tests, and diff evidence;
5. only after separate approval, prepare `self-enhance-swap`.

If a phase fails, stop at that phase and report the exact artifact. Never turn
an analysis-only result or a failed validation into a success claim.

