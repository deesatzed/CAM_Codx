# Task 14 CAM/CAM_Codx Proof Scenario Report

Date: 2026-08-18
Plan: `docs/plans/2026-08-18-task14-cam-proof-scenario.md`
Run ID: `task14-matraix-sesa-proof-20260818`

## Scope

This run tested the CAM_Codx-first assessment and planning path against the
pinned MatrAIx and SESA checkouts. It did not execute project code, call a
provider, mine, write `claw.db`, modify `.env`/config, import a graph, or mutate
either target.

## Inputs

| Input | Revision / identity |
|---|---|
| MatrAIx-Persona-8B | `3202a0bf6134776735c4ab4d50de79be8c6a5e8b`, clean `main` |
| SESA-Self-Evolving-Search-Agents | `74de5d77a19774cfba53d6950d47633a2d632430`, clean `master` |
| CAM database | `/Volumes/WS4TB/waswiki/CAM_CAM/claw.db` |
| CAM config | `/Volumes/WS4TB/waswiki/CAM_CAM/claw.toml` |
| CAM executable | `/Volumes/WS4TB/waswiki/CAM_CAM/.venv/bin/cam` |

## Evidence

1. **Session preflight.** MatrAIx and SESA both resolved as clean targets;
   CAM_CAM, database, config, and environment-file identities were present.
   The preflight warned that the canonical directory is not writable for WAL
   sidecars, which is consistent with a read-only proof boundary.

2. **Development Brief.** Both `continue-rescue` runs completed without
   mutation, mining, provider calls, or test execution. MatrAIx had no readable
   repository truth files and no CAM evidence; SESA had no readable truth files,
   showed several visible `NotImplemented` markers, and also had no CAM
   evidence. Both briefs honestly recommended re-development rather than
   claiming reusable precedent.

3. **CAM_Codx plans.** Both `cam_control_plane.py plan` calls resolved:

   - intent: `assess`;
   - route: `brief-query`;
   - memory: `read_only`;
   - writes: `none`;
   - mining: `false`;
   - provider spend: `false`;
   - approval classes: `[none]`;
   - operation executed: `false`.

   The config hash remained
   `ba8952a4a1dc4705d722ff0704975c8d3af75e0287812c5154f55d6df33ea038` and
   the database hash remained
   `0b2d00b856e70ae618e1dc607ab3ff0152e08c8752afbd12bb9e465710b0a68e`.
   Target hashes were stable per checkout: MatrAIx
   `8e616b445485009f7d23f2002e62348094cc6a4fb3b63c6b332cc54fcb3b0c56` and
   SESA `d75bd8e62ba249a2a118cd72cc94017a86cd12ddaace7ec2f270dbb77321c604`.

4. **CAM runtime query.** The explicit primary-only command
   `cam brief-query 'population testing adaptive search provenance verified
   outcome' --db ... --limit 8 --json` completed with schema version `1` and
   `results: []`. This is an honest no-match result, not positive reuse proof.

5. **Fail-closed check.** A deliberately malformed rerun supplied `claw.toml`
   as both database and config. CAM_Codx rejected it with
   `CAM runtime identities must resolve to distinct files`, exit code `2`,
   before execution. The corrected SESA plan then passed.

## Verdict

**CAM_Codx-first safety/orchestration proof: PASS.** The normal route resolves
both named sources through CAM_Codx, preserves the single CAM runtime identity,
and fails closed on ambiguous runtime paths.

**Useful mine-to-build/product proof: NOT YET PROVEN.** The primary corpus
returned no matching evidence, no candidate ledger or landing map was created,
and no isolated implementation or verification was run. The scenario must not
be described as a successful MatrAIx/SESA integration.

## Next bounded step

Create an independent candidate ledger and clean-room landing map for the
high-level concepts only: population/task cohort evaluation, adaptive search,
proposer/solver feedback, and skill-bank-style retrieval. MatrAIx may be used
under its MIT notice. SESA root-code reuse remains unresolved until ownership
or licensing is recorded; nested third-party notices remain separate. Any
implementation must use temporary state and remain provider-disabled until its
product-boundary checkpoint is accepted.
