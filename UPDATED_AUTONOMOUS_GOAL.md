# Updated Autonomous Goal: Finish The CAM_Codx Control Plane

This is the continuation contract for the unfinished work in
`docs/plans/2026-08-12-cam-codx-control-plane.md`. It does not erase the
approved design or completed Tasks 1-6. It changes the execution policy so
routine implementation, testing, review remediation, documentation, and
commits continue without repeated user approval pauses.

Current verified starting point:

- CAM_Codx isolated worktree:
  `/private/tmp/cam-control-plane-20260812/CAM_Codx`
- CAM_CAM isolated worktree:
  `/private/tmp/cam-control-plane-20260812/CAM_CAM`
- Both worktrees use branch `feat/cam-codx-control-plane`.
- Tasks 1-6 are implemented, committed, and accepted.
- Task 7 is not accepted. CAM_CAM is at `6d7073a` with uncommitted RED tests
  for single-read receipt validation, immutable target revisions, and binding
  verification evidence to the exact managed-plan identity. Preserve and
  finish those tests; do not discard or bypass them.
- The hidden `managed-run` command increases the live CAM_CAM manifest from
  139 to 140 paths and from 15 to 16 hidden paths. Task 8 must update the
  pinned manifest, capability registry, and generated contract artifacts.

/goal

OUTCOME: Complete Tasks 7-14 of the approved CAM_Codx control-plane plan so
that CAM_Codx is the single normal user-facing manager for CAM_CAM, direct
CAM_CAM usage is positioned as a troubleshooting/runtime-development surface,
the source-to-outcome evidence chain is proven, and one bounded MatrAIx/SESA
vertical slice demonstrates useful mine-to-build reuse.

The normal developer experience must be:

```text
Use CAM_Codx to <desired outcome>.
```

The developer must not need to choose among legacy CAM_Codx skills or memorize
CAM_CAM commands. Every live CAM_CAM manifest path must be classified exactly
once. Every normal capability must have a CAM_Codx-managed route; explicitly
designated direct service/troubleshooting entrypoints and hidden compatibility
aliases must not appear as competing normal UX.

PROOF OF DONE:

1. Task 7 passes specification and independent quality review. Verification
   receipts are read once, and the exact bytes hashed are the bytes decoded and
   parsed. A typed receipt binds gate ID, list-form argv, exit code, canonical
   target path, immutable revision kind/value, plan ID, and the full managed
   plan SHA-256. Multi-slot run status is consistent at write and report time.
2. CAM_Codx's registry and pinned fixture exactly match the 140-path CAM_CAM
   manifest at the final CAM_CAM commit, including hidden `managed-run` as a
   canonical, manager-selectable local-record operation. Generated artifacts
   are current.
3. `assess` and `plan` compose the existing primary-only Development Brief,
   target inspector, and managed-run seam. Structured output preserves direct
   precedent, transferable analogy, and new hypothesis as distinct labels with
   provenance, confidence, limitations, selection state, proposed landing,
   adaptation burden, risk, and proof requirements.
4. Weak assessment evidence may recommend a separately scoped mining phase,
   but assessment never starts mining, calls a provider, changes the target,
   changes the corpus, changes a model/profile, or changes configuration.
5. `build`, `fix`, `verify`, and `record` enforce their phase transitions:
   plan before mutation, exact target-mutation authorization, receipt-backed
   verification, preview before record writes, and no positive trust from
   failed, partial, synthetic, unrun, or unverified evidence.
6. Mining, knowledge, models, benchmarks, self-enhancement, evolution, doctor,
   setup, and supported administration routes are selected from the single
   registry and executed through fixed list-form manager packets. No provider
   client or duplicate CAM runtime logic is added to CAM_Codx.
7. Normal help, quickstart, cheatsheets, status, generated packs, and manager
   documentation begin with CAM_Codx outcome language. CAM_CAM documentation
   describes direct CLI use as troubleshooting, runtime development, recovery,
   regression isolation, or expert integration. It must not claim `cam chat`
   is a complete general router.
8. Run the Task 12 focused gates using the actual checkout paths, correcting
   the stale plan reference `tests/planning/test_application_packet.py` to the
   real file `tests/test_application_packet.py`. Run both current full suites;
   caused regressions must be fixed, while unrelated baseline failures must be
   recorded without being relabeled as success.
9. Install into a temporary Codex home and prove that only the canonical
   `cam-codx` skill is newly installed. Exercise read-only assessment and prove
   target, corpus, model-profile, and configuration identities do not change.
10. Run the deterministic Task 13 fixture chain through assessment, candidate
    decisions, reviewed plan, simulated landing, failed verification,
    corrected verification, outcome recording, and later recall. Only the
    verified active result may appear as positive reuse evidence. Label this as
    fixture proof, not live-product proof.
11. Only after Tasks 1-13 pass, create the Task 14 MatrAIx/SESA slice contract,
    including the exact target repository, source revisions, license boundary,
    privacy/data boundary, provider policy, selected and rejected candidates,
    landing map, tests, rollback, and outcome-recording plan.
12. Build and verify the smallest useful evolutionary population-testing slice
    permitted by that contract. Start a fresh CAM_Codx assessment and prove the
    verified result is retrievable with provenance while rejected, deferred,
    and hypothetical candidates remain distinct.
13. Update `GOAL.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, the
    capability audit, and user documentation to the actual final state.
14. Provide final commit IDs, branch/publication status, test receipts,
    limitations, baseline failures, rollback notes, and an explicit verdict on
    whether the CAM_Codx-first UX and real MatrAIx/SESA proof are complete.
15. In both repositories, `git diff --check` passes and the final intended
    worktrees are clean. No completion claim may rely only on a subprocess exit
    code, fixture result, prompt assertion, or stale document.

SCOPE:

- Primary implementation owner: CAM_Codx.
- Runtime and persistence owner: CAM_CAM.
- Continue from the two isolated worktrees named above. Do not edit the user's
  active `main` checkouts while the feature branches are under development.
- Follow Tasks 7-14 in
  `docs/plans/2026-08-12-cam-codx-control-plane.md`, with documented file-list
  expansion where required to update the 140-path registry fixture, generated
  artifacts, truth documents, or regression tests.
- CAM_Codx may modify its router, manager, Development Brief, pull/mine
  coordinator, setup wizard, canonical skill, registry, generators, tests, and
  documentation needed by Tasks 8-14.
- CAM_CAM may modify its managed-run persistence seam, repository/transaction
  support where directly required, CLI manifest seam, tests, and
  troubleshooting documentation needed by Tasks 7-14.
- The MatrAIx/SESA product repository is out of implementation scope until the
  Task 14 slice contract fixes its exact path and boundaries.
- Do not modify live `claw.db`, `claw.toml`, model profiles, provider settings,
  or deployed services during control-plane development and fixture proof.
- Do not delete or rewrite unrelated user changes. Preserve dirty-worktree
  truth and use isolated worktrees or a bounded recovery strategy.

CONSTRAINTS:

- Read `GOAL.md`, `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`,
  `PROGRESS.md`, and `TASK_QUEUE.md` when present before each repository phase.
- CAM_Codx owns orchestration and must call CAM_CAM; it must not vendor, fork,
  or reimplement CAM_CAM runtime, mining, retrieval, provider, model,
  self-enhancement, or evolution logic.
- Use test-driven development. A failing regression must demonstrate each bug
  or missing behavior before production code is changed.
- Use exact list-form subprocess argv. Do not add shell execution paths.
- Do not weaken, delete, skip, or relabel tests to obtain a green result.
- Do not treat retrieval similarity, mined row counts, or a candidate proposal
  as proof of useful reuse.
- Only receipt-backed verified outcomes may strengthen positive trust or recipe
  eligibility. Retain failures, partial results, abandoned candidates,
  limitations, and negative evidence.
- Preserve secret-argument rejection and content-addressed, time-bounded,
  single-use operation authorization.
- No dependency addition, schema migration, public API break, or broad cleanup
  unless the current task proves it is necessary and records the decision.
- Fixture/synthetic proof must never be described as live accuracy,
  production readiness, or real-world acceptance.

AUTONOMOUS APPROVAL POLICY:

- Do not ask the user to approve routine file inspection, test creation,
  implementation, formatting, linting, internal review, review remediation,
  truth-document updates, or scoped commits on the isolated feature branches.
- Do not pause between Tasks 7-13 merely to ask permission to continue.
- Treat review findings and ordinary test failures as work to diagnose and
  repair, not as user approval checkpoints.
- Batch safe commands and use existing narrow command-prefix permissions where
  available. A host/sandbox permission prompt is an environment boundary, not
  a product-design approval.
- Read-only CAM_Codx operations require no product approval after runtime paths
  are resolved.
- One named, bounded phase authorization may cover its exact local-record or
  target-mutation operation. It must not silently authorize mining, provider
  spend, promotion, configuration change, or live CAM mutation.
- Live mining/provider spend requires an explicit source, database, model,
  time, and cost bound. Model/profile promotion, rollback, self-enhancement
  swap, destructive action, production deployment, and live configuration
  change remain separate explicit approvals.
- Task 14 requires one meaningful product checkpoint after its slice contract
  is written if the exact target, licensing, privacy, provider use, or product
  scope is not already unambiguously authorized. Do not replace this with many
  low-level implementation approvals.

SAFETY / PROVENANCE:

- Resolve and display the exact CAM_Codx checkout, CAM_CAM checkout, wrapper,
  configuration, primary database, model-profile file, target repository, and
  relevant revision before any mutating or paid operation.
- Fail closed on ambiguous or stale runtime identity, registry/manifest drift,
  missing receipts, mutable revision labels, digest mismatch, unknown command,
  stale approval, secret-bearing argument, or incomplete proof gate.
- Verification receipts must bind an immutable target identity and the exact
  digest-bound plan; hashing and parsing must operate on one captured byte
  buffer.
- Preserve source receipts and license information for every reused component.
  Separate direct reuse, transferred principle, and new hypothesis.
- Do not expose secrets, credentials, private keys, sensitive source, or
  unnecessary personal data to providers, logs, packets, docs, or subagents.
- Do not run code from repositories merely because they were mined or recalled.

ITERATION:

1. Resume Task 7 from the current RED tests. Make the smallest production
   change that closes the single-read, immutable-revision, and plan-binding
   failures. Run focused and selected regression gates, update CAM_CAM truth
   docs, commit, and obtain internal specification plus quality approval.
2. Execute Tasks 8-11 sequentially. For each task: add RED tests, implement the
   minimal composition over existing helpers/runtime, run focused gates,
   perform specification review and skeptical quality review, remediate all
   blocking findings, update truth docs, and commit each repository separately.
3. Run Task 12 focused and full release gates. Do not advance while a caused
   regression, registry drift, generated-output drift, or installation mismatch
   remains.
4. Run and document Task 13 fixture proof.
5. Begin Task 14 only after the Task 13 gate is green. Freeze the product slice
   before editing its target repository, then implement in small verified
   batches and record the source-to-outcome chain.
6. After every batch, record changed files, exact command results, receipts,
   assumptions, limitations, and next action in `PROGRESS.md`; update
   `DECISIONS.md` for material architecture, security, evidence, or UX choices.
7. Continue automatically while a safe in-scope mitigation remains. Use a
   different diagnosis or repair approach after a failed attempt rather than
   repeating the same command unchanged.

STOP:

Pause and report the exact blocker only if one of these is true:

- credentials, API keys, accounts, license rights, or private data access are
  required and unavailable;
- a live provider call, paid mining run, model/profile change, CAM swap,
  destructive action, production deployment, or live configuration/database
  mutation lacks its required explicit authorization;
- Task 14 exposes material uncertainty about target ownership, licensing,
  privacy, provider policy, or product scope;
- the same blocking condition remains after three distinct, documented repair
  strategies;
- required verification cannot be executed and no safe fixture, local,
  isolated, or read-only alternative can establish the needed evidence;
- continuing would require weakening evidence semantics, bypassing a safety
  gate, discarding user changes, or expanding beyond this scope.

Do not stop merely because a test fails, a reviewer finds a defect, a task is
difficult, a document needs alignment, or another safe repair iteration is
available.

COMPLETE:

Mark this goal complete only when every `PROOF OF DONE` item is supported by
current command output and inspected artifacts; Tasks 7-14 are committed in
their owning repositories; the final registry matches the live manifest; the
canonical skill installation proof passes; both cross-repository release gates
pass except for explicitly recorded unrelated baselines; Task 13 fixture proof
is honestly labeled; the Task 14 build and later-recall proof pass or is
explicitly blocked by one of the allowed STOP conditions; truth documents
match implementation; and no required work remains hidden behind a future-tense
claim.

If Task 14 is blocked by a legitimate STOP condition after Tasks 7-13 pass,
report the control plane as complete and the vertical slice as blocked—not as
fully complete—and preserve a precise successor contract.
