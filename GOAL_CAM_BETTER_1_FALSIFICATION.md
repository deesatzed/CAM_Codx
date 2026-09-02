# CAM Better Evidence Goal 1: Falsification and Failure Discovery

This is the first executable contract in the CAM Better Evidence Program. The
controlling plan is
`/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench/docs/plans/2026-08-19-cam-better-evidence-program.md`.
The machine-readable continuation state is
`/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench/PROGRAM_STATUS.json`.

Run this goal only when that status file names
`GOAL_CAM_BETTER_1_FALSIFICATION.md` as `active_goal`. Use
`executing-plans` for the task sequence, `cam-codx-session` for every CAM
operation, test-driven development for implementation, and
`verification-before-completion` before closing the goal.

/goal

OUTCOME: Complete Tasks 2-8 of the controlling plan and determine, without
assuming CAM wins, whether CAM can discover the required repositories, judge
knowledge sufficiency, react causally to missing sources, and improve an
isolated software-build outcome relative to base and Context7. Produce a
committed Goal 1 gate that identifies the earliest supported failure stage or
the specific evidence contributing to a bounded CAM win.

PROOF OF DONE:

1. Create and commit a recovery baseline recording exact paths, branches,
   commits, dirty states, database/config/profile digests, source revisions and
   licenses, benchmark-plan digests, and read-only SQLite integrity evidence.
2. Classify every existing artifact as foundation evidence, Goal 1 evidence,
   benchmark scaffolding, negative result, pending authorization, or
   superseded. Correct all language that presents the human-authored
   sufficiency ledger as CAM-generated output.
3. E1 contains 15-20 preregistered discovery cases spanning direct precedent,
   different-language analogy, multi-source conjunctions, decoys, absent,
   stale, conflicting, prior-failure, and current-public-API knowledge. A
   deterministic scorer reports Top-1/Top-3 required-source recall, omissions,
   irrelevant retrieval, immutable revision accuracy, and evidence labels.
4. E2 obtains a structured verdict from CAM_Codx itself using exactly one of
   `sufficient`, `partially_sufficient`, `insufficient`, `stale`, or
   `conflicted`. The output retains direct evidence, analogies, missing
   obligations, conflicts, stale sources, confidence, limitations,
   recommended route, and proof requirements. False-sufficient cases are hard
   failures and human preregistration cannot be substituted for runtime proof.
5. E3 proves or rejects each Task A donor's mechanical necessity and runs
   full, minus-X, minus-Y, minus-Z, and none CAM-corpus ablations using
   disposable databases. CAM's verdict and missing obligations change in the
   preregistered direction or the failure is preserved honestly.
6. Task A's public task, sources, contexts, evaluator, model/profile/catalog,
   repetition policy, call ceiling, cost ceiling, and arm isolation are
   re-audited after E1-E3. Changed identities produce a new frozen plan rather
   than silently altering the existing trial.
7. No provider generation occurs until one explicit authorization names the
   exact provider, model, calls, output ceiling, maximum cost, wall time, task
   and source revisions, and run directory. After authorization, each issued
   request has one immutable success or failure receipt and no request is
   duplicated on resume.
8. Every materialized base, CAM, Context7, and source-oracle candidate is
   scored by the same hidden deterministic evaluator. Safety and behavioral
   results, technical failures, tokens, tool calls, latency, and reconciled
   provider cost remain separate.
9. The Task A report states only `win`, `tie`, `loss`, or `unresolved`, names
   the exact task class, comparator, metric, and evidence, and never treats the
   raw-source oracle as normal user workflow.
10. `artifacts/goal-1-gate.json` and the Goal 1 report cite current E1-E3 and
    Task A receipts, locate the earliest supported failure among the twelve
    stages in the master plan, and freeze held-out Tasks B and C before any
    mitigation is implemented.
11. The benchmark suite, focused CAM_Codx/CAM_CAM tests changed by this goal,
    JSON validation, receipt validation, and `git diff --check` pass. Caused
    regressions are fixed; unrelated baselines remain explicitly labeled.
12. Each repository's changes are committed separately. Only after the Goal 1
    gate is committed may `PROGRAM_STATUS.json` name
    `GOAL_CAM_BETTER_2_ROOT_CAUSE_MITIGATION.md` as active.

SCOPE:

- Primary benchmark and evidence owner:
  `/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench`.
- Orchestration owner: `/Volumes/WS4TB/waswiki/CAM_Codx`.
- Runtime/retrieval owner: `/Volumes/WS4TB/waswiki/CAM_CAM`.
- Follow Tasks 2-8 and the fixed protocol in the controlling master plan.
- CAM_Codx may add the minimal structured sufficiency composition and tests
  required by E2, reusing CAM_CAM's read-only query rather than duplicating
  retrieval or provider logic.
- CAM_CAM may change only if a failing regression proves that E1-E3 require a
  runtime correction. Keep runtime ownership in CAM_CAM.
- Create experiment cases, deterministic scorers, disposable-corpus builders,
  receipts, gates, reports, and truth-document updates required by Goal 1.
- Read source repositories only at their pinned revisions. Do not edit donors.
- Do not modify canonical `claw.db`, `claw.toml`, `.env`, model profiles,
  provider configuration, source repositories, or deployed services.

CONSTRAINTS:

- Before acting, read the controlling plan in full, `PROGRAM_STATUS.json`,
  this goal, and `GOAL.md`, `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`,
  `PROGRESS.md`, and `TASK_QUEUE.md` when present in each repository phase.
- Resolve all runtime identities from disk. Historical paths and chat memory
  are not authority.
- Keep the same builder model, provider route, task, starter, system prompt,
  output ceiling, repetition schedule, tools, and hidden evaluator within a
  comparison block. Knowledge source is the only intentional independent
  variable.
- Use test-driven development. Do not weaken, skip, delete, or relabel a test
  or negative receipt to obtain a favorable result.
- Do not use an LLM judge. Retrieval similarity, row counts, plan prose,
  human labels, and model confidence are not executable outcome evidence.
- Queries and builder prompts must not reveal donor names, hidden obligation
  IDs, hidden tests, or expected answers.
- Preserve Trial 1 and every later failure immutably. A failed provider call is
  technical evidence, not a software score and not permission to retry.
- No model tournament, model/profile promotion, live mining, provider spend,
  target mutation, canonical database/configuration change, or deployment is
  implicitly authorized by this goal.
- Amend the experimental contract only through a dated decision, a new
  revision/trial identity, and a committed diff. Never rewrite observed data.

AUTONOMOUS EXECUTION POLICY:

- Continue without user approval through read-only inspection, fixture and
  scorer creation, disposable database copies, tests, local assessment,
  diagnosis, documentation, review remediation, and scoped commits.
- Do not pause merely because a test fails or CAM loses. Diagnose, preserve the
  evidence, and continue while an in-scope repair or measurement remains.
- Stop at the single Task A provider-spend boundary and resume from the same
  status ledger after exact authorization. Do not split routine implementation
  into approval-per-command checkpoints.
- After each master-plan task, update `PROGRAM_STATUS.json` and `PROGRESS.md`,
  validate them, and commit before proceeding.

SAFETY / PROVENANCE:

- Use disposable corpus copies for all ablations and write-bearing CAM proof.
- Hash and record every database, config, profile, plan, context, receipt,
  source revision, candidate, evaluator, and report used for a claim.
- Preserve repository/revision/file/license provenance and distinguish direct
  precedent, transferable analogy, hypothesis, failure, and verified outcome.
- Do not expose credentials, secrets, private keys, private source, hidden
  tests, or unnecessary personal data to providers, logs, artifacts, prompts,
  or subagents.
- Fail closed on ambiguous runtime identity, database drift, plan drift,
  fallback routing, unexpected model ID, hidden-test leakage, digest mismatch,
  duplicate request, cost overrun, or canonical-state mutation.
- Do not describe fixture evidence as general superiority, production
  readiness, safety, calibration, or capability gain.

ITERATION:

1. Run the crash-recovery checklist from the controlling plan and reconcile
   the current status ledger against disk.
2. Execute Tasks 2-5 sequentially: baseline, E1 discovery, E2 CAM-generated
   sufficiency, and E3 source ablation. For each, write RED tests, implement the
   smallest mechanism, run focused and regression tests, preserve receipts,
   update truth, and commit.
3. Re-audit the frozen Task A packet only after E1-E3 have scored evidence.
4. At the paid boundary, display one exact authorization packet and pause.
   After authorization, execute sequentially and never repeat a call already
   represented by a request or receipt.
5. Score all materialized candidates, reconcile spend, and publish a limited
   comparator-specific verdict.
6. Freeze held-out Tasks B and C, write `artifacts/goal-1-gate.json`, run an
   independent skeptical evidence review, and remediate blocking findings.
7. Commit final Goal 1 evidence and atomically advance the status ledger to
   Goal 2. Do not start mitigation within this goal.

STOP:

Pause and report the exact blocker only if:

- credentials, an API key, an account, or private data access is required and
  unavailable;
- provider spending, live mining, canonical state mutation, model/profile
  change, destructive action, deployment, or production mutation lacks its
  required explicit authorization;
- the fixed experimental identities drift and a safe new frozen revision
  cannot be created without a material product decision;
- hidden tests, expected answers, or donor identities leaked into an arm;
- the same blocking condition remains after three distinct documented repair
  strategies;
- required verification cannot run and no safe local, fixture, disposable, or
  read-only alternative can establish the named evidence; or
- continuing would require weakening evidence semantics, discarding negative
  results, overwriting user changes, or expanding beyond Goal 1.

COMPLETE:

Mark this goal complete only when every PROOF OF DONE item is backed by
current inspected artifacts and command output, Tasks 2-8 are committed in
their owning repositories, the Goal 1 gate and held-out-task freeze exist, the
benchmark status names Goal 2, intended worktrees are clean apart from
explicitly preserved pre-existing changes, and no Goal 1 work remains hidden
behind a future-tense claim. A CAM loss or unresolved result may complete this
goal if it is measured honestly and the failure-stage receipt is complete.
