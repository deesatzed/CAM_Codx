# Task 14 CAM/CAM_Codx Proof Scenario Plan

Date: 2026-08-18

## Purpose

Demonstrate the smallest useful CAM_Codx-first proof of the MatrAIx/SESA
concept without merging the projects, copying SESA code, swapping live CAM
state, calling a provider, or claiming product accuracy.

The intended demonstration is:

```text
MatrAIx population-evaluation concept
       + SESA adaptive-search concept
       -> CAM_Codx assessment and candidate ledger
       -> reviewed bounded plan
       -> isolated fixture/adaptation (only after boundary acceptance)
       -> verification and outcome receipt
       -> later CAM_Codx recall of verified evidence
```

## Pinned inputs

| Input | Path | Revision / identity |
|---|---|---|
| CAM_Codx | `/Volumes/WS4TB/waswiki/CAM_Codx` | canonical `main`, current published head |
| CAM_CAM | `/Volumes/WS4TB/waswiki/CAM_CAM` | canonical `main`, current published head |
| CAM corpus | `/Volumes/WS4TB/waswiki/CAM_CAM/claw.db` | one existing local database; read-only proof only |
| CAM config | `/Volumes/WS4TB/waswiki/CAM_CAM/claw.toml` | one existing tracked config; no changes |
| MatrAIx | `/Volumes/WS4TB/waswiki/repos2mine/repo622sn/MatrAIx-Persona-8B` | `3202a0bf6134776735c4ab4d50de79be8c6a5e8b`, MIT |
| SESA | `/Volumes/WS4TB/waswiki/repos2mine/repo622sn/SESA-Self-Evolving-Search-Agents` | `74de5d77a19774cfba53d6950d47633a2d632430`, root license unresolved |

## Execution phases

### Phase 1: Identity and source preflight

- Run `cam_session_preflight.py` for each named target.
- Confirm clean source trees, canonical CAM checkout, database, config, and
  environment-file presence by name only.
- Capture source revisions, license evidence, and target identity digests.
- Do not copy `.env`, print secrets, or write database WAL sidecars.

### Phase 2: Read-only Development Brief

- Run CAM_Codx `development_brief.py continue-rescue` once per target.
- Use only the supplied primary corpus and named target.
- Preserve direct precedent, transferable analogy, and new hypothesis labels.
- Treat missing target truth files or no retrieved methods as an honest result,
  not a failure or permission to mine.

### Phase 3: CAM_Codx control-plane plan

- Resolve `assess` for each target with `cam_control_plane.py plan`.
- Use one stable SWE Run ID: `task14-matraix-sesa-proof-20260818`.
- Confirm route `brief-query`, memory mode `read_only`, `writes=none`,
  `mining=false`, `provider_spend=false`, and `approval_classes=[none]`.
- Record target/database/config identity hashes before and after planning.

### Phase 4: Candidate and landing design

- Build a ledger containing only independently stated concepts: population
  evaluation, persona/task cohorting, adaptive search, proposer/solver
  feedback, and skill-bank-style retrieval where supported by inspection.
- Mark every row direct precedent, transferable analogy, or new hypothesis;
  states are selected, rejected, deferred, unresolved, or hypothetical.
- Do not copy SESA source, prompts, tests, datasets, or model artifacts. SESA
  root-code adaptation remains blocked until rights are recorded; nested
  third-party notices remain separate.
- Draft a CAM-side adapter/fixture landing map with exact paths, tests, and
  rollback. No target mutation occurs in this phase.

### Phase 5: Optional isolated implementation

- Only after the Task 14 product-boundary checkpoint is recorded, implement
  the smallest CAM-side clean-room adapter or fixture in a disposable target
  location.
- Use a temporary database/config and provider-disabled environment. Never use
  the canonical `claw.db` for a write proof.
- Run only bounded local tests; no dataset download, model load, training,
  Docker service, or paid/provider run is implicit.

### Phase 6: Verification, record, and recall

- Bind verification to the exact target revision and plan digest.
- Record failures and partial results as negative/inconclusive evidence.
- Start a fresh CAM_Codx assessment and verify only the corrected verified
  result is positive; rejected, deferred, hypothetical, and failed candidates
  remain distinct.
- Update `PROGRESS.md`, `DECISIONS.md`, and the Task 14 report with commands,
  receipts, limitations, and exact commits.

## Acceptance gates

1. Both source trees and canonical CAM identities are pinned and clean.
2. Assessment and planning are read-only; target, database, config, and model
   identities are unchanged.
3. No provider, mining, model load, target mutation, or live import occurs in
   the initial proof.
4. The candidate ledger distinguishes precedent, analogy, and hypothesis.
5. The plan states what is not copied and retains license/provenance evidence.
6. Any later fixture implementation is isolated, tested, receipt-backed, and
   honestly labeled as fixture proof.

## Stop conditions

Stop before implementation if SESA ownership/license authority, privacy/data
scope, provider policy, target writable paths, or rollback are ambiguous. A
successful read-only plan does not authorize a write, provider call, or live
database change.
