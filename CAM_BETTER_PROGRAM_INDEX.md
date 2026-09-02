# CAM Better Evidence Program Index

This index is the stable entry point for the autonomous CAM Better Evidence
Program. It does not itself claim that CAM is better.

## Authority

- Master plan:
  `/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench/docs/plans/2026-08-19-cam-better-evidence-program.md`
- Machine-readable status:
  `/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench/PROGRAM_STATUS.json`
- Benchmark root:
  `/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench`
- CAM_Codx root: `/Volumes/WS4TB/waswiki/CAM_Codx`
- CAM_CAM root: `/Volumes/WS4TB/waswiki/CAM_CAM`

Conversation history is not authority. After interruption, read the master
plan and status ledger, validate their referenced commits and receipts against
disk, and resume only the named active task.

## Sequential goals

1. `GOAL_CAM_BETTER_1_FALSIFICATION.md` measures discovery, CAM-generated
   sufficiency, source causality, and the isolated Task A comparison.
2. `GOAL_CAM_BETTER_2_ROOT_CAUSE_MITIGATION.md` tests one Goal 1 root-cause
   mitigation against Task A and frozen held-out Tasks B/C.
3. `GOAL_CAM_BETTER_3_REUSE_SYNTHESIS.md` measures mine-once reuse,
   portability, outcome memory, least-cost routing, and a final net-new build.

Run only the file named by `active_goal` in `PROGRAM_STATUS.json`. A goal may
advance the ledger only after its gate receipt is committed.

## Invocation

From a Codex session rooted at `/Volumes/WS4TB/waswiki/CAM_Codx`, start with:

```text
/goal GOAL_CAM_BETTER_1_FALSIFICATION.md
```

After Goal 1 legitimately completes and the ledger activates Goal 2:

```text
/goal GOAL_CAM_BETTER_2_ROOT_CAUSE_MITIGATION.md
```

After Goal 2 legitimately completes and the ledger activates Goal 3:

```text
/goal GOAL_CAM_BETTER_3_REUSE_SYNTHESIS.md
```

Do not run these goals concurrently or skip a transition gate.

## Autonomous boundary

Read-only inspection, fixtures, tests, disposable state, local scoring,
diagnosis, documentation, review remediation, and scoped commits continue
without routine approval. Explicit authorization remains required for paid
provider calls, live mining, canonical database/configuration mutation,
model/profile change, destructive action, deployment, and production mutation.

## Current state

Goal 1 is active at Task G1-T2: freeze identities and reconcile existing
evidence. The frozen Grok Task A plan is not currently authorized to execute;
Goal 1 must pass its preceding no-cost gates and re-audit the packet first.
