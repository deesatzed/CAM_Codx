# CAM Better Evidence Goal 2: Root Cause and Held-Out Mitigation

This is the second executable contract in the CAM Better Evidence Program. The
controlling plan is
`/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench/docs/plans/2026-08-19-cam-better-evidence-program.md`.
The machine-readable continuation state is
`/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench/PROGRAM_STATUS.json`.

Run this goal only when the status file names
`GOAL_CAM_BETTER_2_ROOT_CAUSE_MITIGATION.md` as `active_goal`, the Goal 1 gate
is committed, and that gate names one evidence-supported mitigation
hypothesis. Use `executing-plans`, `cam-codx-session`, test-driven development,
and `verification-before-completion`.

/goal

OUTCOME: Complete Tasks 9-13 of the controlling plan by reproducing the
earliest Goal 1 failure with a focused RED test, implementing one minimal
bounded mitigation in the owning layer, and determining on original Task A
plus preregistered held-out Tasks B and C whether the mitigation generalizes,
overfits, regresses other behavior, is unnecessary, or remains unresolved.

PROOF OF DONE:

1. The committed `artifacts/goal-1-gate.json` is validated against
   `PROGRAM_STATUS.json` and identifies the earliest supported failure stage,
   exact evidence, one bounded hypothesis, and frozen Tasks B and C.
2. A focused regression test fails for the diagnosed reason before production
   code changes. The RED command and output are preserved in the mitigation
   receipt.
3. The mitigation changes only the earliest failing owner: CAM_CAM retrieval
   or graph behavior, CAM_Codx brief/orchestration behavior, or benchmark
   measurement code. It does not encode Task A donor names, hidden terms,
   expected answers, or one-off prompt answers.
4. The focused test turns GREEN, and unrelated retrieval, sufficiency,
   provenance, read-only, safety, and control-plane regression tests pass.
5. Task A is rerun under a new mitigation trial ID. The original Goal 1 trial,
   contexts, requests, failures, candidates, scores, and receipts remain
   immutable and independently inspectable.
6. Held-out Tasks B and C retain their frozen public tasks, source identities,
   expected obligations, hidden tests, and arm packets. The mitigation is not
   revised after inspecting their results.
7. The minimum comparator arms needed to test the diagnosed failure class are
   executed under fixed controls, and every issued provider request has an
   immutable receipt. Any additional spending is separately authorized with
   exact model, calls, cost, task revisions, and run directory.
8. Task A, B, and C are scored for hidden behavior, safety, false sufficiency,
   irrelevant retrieval, provenance accuracy, technical failures, cost,
   latency, and repair iterations as applicable.
9. `artifacts/goal-2-gate.json` and the Goal 2 report classify the mitigation
   as exactly one of `generalized`, `task-specific`, `regressive`,
   `unnecessary`, or `unresolved`, with receipt citations and no favorable
   reinterpretation.
10. Focused and full affected-repository tests, artifact/JSON validation, and
    `git diff --check` pass. Caused regressions are fixed; unrelated baselines
    remain visible.
11. Each repository is committed separately, and only after the Goal 2 gate is
    committed may `PROGRAM_STATUS.json` name
    `GOAL_CAM_BETTER_3_REUSE_SYNTHESIS.md` as active.

SCOPE:

- Benchmark/evidence owner:
  `/Volumes/WS4TB/waswikiT/repos2mine/CAM_KnowledgeSourceBench`.
- Orchestration owner: `/Volumes/WS4TB/waswiki/CAM_Codx`.
- Runtime owner: `/Volumes/WS4TB/waswiki/CAM_CAM`.
- Follow Tasks 9-13 of the controlling plan and the exact hypothesis recorded
  by `artifacts/goal-1-gate.json`.
- Modify only the earliest failing layer and its focused/regression tests.
- Add new mitigation trial artifacts and reports; never rewrite Goal 1 data.
- Task A and held-out Tasks B/C may be used only within their preregistered
  public/hidden boundaries.
- Donor repositories remain read-only at pinned immutable revisions.
- Canonical CAM state, model profiles, configuration, provider policy, and
  deployments remain out of scope.

CONSTRAINTS:

- Fail closed if Goal 1 is not complete, the status ledger does not activate
  this goal, the gate has no supported hypothesis, or held-out Tasks B/C were
  not frozen before mitigation.
- Read the full master plan, status ledger, Goal 1 gate/report, this goal, and
  repository truth files before editing.
- Preserve one-variable causality. Use the same builder and evaluator as Goal
  1 unless the gate proves provider infrastructure was the causal failure; any
  changed variable requires a dated decision and new trial identity.
- Implement only one mitigation hypothesis. Do not bundle retrieval, ranking,
  prompts, models, and evaluator changes into an uninterpretable patch.
- Use TDD and run RED before production edits. Do not weaken tests, hide
  failures, tune on held-out expected answers, or select only favorable cases.
- A Task A improvement without held-out generalization is not a generalized
  CAM improvement.
- A higher false-sufficient rate, safety regression, provenance loss, or
  unrelated retrieval regression rejects the mitigation even if Task A rises.
- No model/profile promotion, live mining, canonical-state mutation,
  destructive action, provider spending, or deployment is implied.

AUTONOMOUS EXECUTION POLICY:

- Continue without approval through read-only inspection, RED/GREEN test work,
  bounded implementation, local/disposable evaluation, review, documentation,
  and scoped commits.
- Treat ordinary test failures and review findings as work to diagnose and
  remediate, not user checkpoints.
- Stop only at a consequential boundary listed below. After every task, update
  `PROGRAM_STATUS.json` and `PROGRESS.md`, validate, and commit.

SAFETY / PROVENANCE:

- Bind every mitigation trial to the original gate, code commits, frozen task
  revisions, model/provider identity, contexts, evaluator, and receipts.
- Keep Goal 1 evidence immutable and preserve negative, partial, abandoned,
  regressive, and unresolved results.
- Use disposable databases and isolated targets for write-bearing proof.
- Do not expose secrets, hidden tests, expected answers, private source, or
  unnecessary personal data to providers, artifacts, prompts, or subagents.
- Fail closed on digest mismatch, ambiguous runtime, hidden-task leakage,
  provider/model drift, duplicate request, cost overrun, or canonical mutation.
- Report the mitigation's tested task class and limitations. Do not generalize
  from A/B/C to production readiness or universal CAM superiority.

ITERATION:

1. Run the recovery checklist and validate the Goal 1 gate, status ledger,
   commits, and held-out-task freeze.
2. Write one focused RED regression for the earliest failure and preserve its
   expected failure output.
3. Record the hypothesis, implement the smallest change in the owning layer,
   and run focused GREEN plus unrelated regression suites.
4. Commit the owning repository before evaluation so implementation identity
   is immutable.
5. Create a new Task A mitigation trial. If provider spending is required,
   display one exact bounded authorization packet and pause; otherwise continue
   automatically.
6. Run frozen Tasks B and C without tuning between them, score all cases, and
   test false sufficiency and unrelated retrieval.
7. Write the Goal 2 classification report and gate, perform skeptical review,
   remediate evidence defects, commit, and advance the ledger to Goal 3.

STOP:

Pause and report the exact blocker only if:

- Goal 1 lacks a valid committed gate, supported hypothesis, or pre-mitigation
  held-out freeze;
- credentials, API access, provider spend, live mining, canonical mutation,
  model/profile change, destructive action, or deployment lacks authorization;
- fixing the failure requires more than one material layer or a product-scope
  decision not supported by Goal 1 evidence;
- hidden Task B/C answers leaked or the mitigation was already tuned on them;
- the same blocking condition persists after three distinct documented repair
  strategies;
- required verification cannot run and no safe local, fixture, disposable, or
  read-only alternative can prove the result; or
- continuing would overwrite Goal 1 evidence, discard user changes, weaken a
  safety/evidence gate, or expand beyond Goal 2.

COMPLETE:

Mark this goal complete only when Tasks 9-13 are committed, the original RED
and final GREEN are preserved, Task A and held-out B/C have current scored
receipts, regressions and false sufficiency are assessed, the Goal 2 gate gives
one honest classification, `PROGRAM_STATUS.json` activates Goal 3, and no
required work remains hidden behind future tense. A task-specific, regressive,
unnecessary, or unresolved mitigation is a valid completed finding when
supported by complete evidence; it is not a CAM success.
