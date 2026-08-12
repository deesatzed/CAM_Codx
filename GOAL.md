# GOAL.md

This is the active completion contract for making CAM_Codx the single normal
control plane for CAM_CAM. The approved design is
`docs/plans/2026-08-12-cam-codx-control-plane-design.md`.

## Outcome

A developer can say `Use CAM_Codx to <desired outcome>` for routine software
work, repository mining, knowledge inspection, model management, CAM
self-enhancement, evolution, setup, and troubleshooting. CAM_Codx safely routes
the request to CAM_CAM, carries evidence and run identity across phases, and
does not require the user to memorize CAM_CAM commands or several overlapping
skills.

Direct CAM_CAM CLI use remains supported for runtime troubleshooting,
development, recovery, and regression isolation.

## Canonical Paths

- CAM_Codx: `/Volumes/WS4TB/waswiki/CAM_Codx`
- CAM_CAM: `/Volumes/WS4TB/waswiki/CAM_CAM`
- Default mining source pool:
  `/Volumes/WS4TB/waswiki/repos2mine/repo622sn`
- Primary corpus: `/Volumes/WS4TB/waswiki/CAM_CAM/claw.db`
- Runtime config: `/Volumes/WS4TB/waswiki/CAM_CAM/claw.toml`

Historical documents may contain earlier workspace paths. Active setup,
routing, and verification must use resolved current paths and fail closed on
ambiguous runtime or database identity.

## Required Deliverables

1. One machine-readable CAM_Codx capability registry classifies every public
   CAM_CAM command as managed, troubleshooting-only, or hidden compatibility.
2. One canonical installed `cam-codx` skill semantically routes all normal SWE
   and CAM administration requests.
3. Existing setup, Development Brief, SWE, pull/mine, model, and
   self-enhancement logic becomes internal playbooks or helpers without runtime
   duplication.
4. The CAM_Codx manager supports every approved route with fixed list-form
   command prefixes, side-effect classification, scoped single-use approvals,
   and redacted receipts.
5. Managed SWE work uses the six intents `assess`, `plan`, `build`, `fix`,
   `verify`, and `record`.
6. A durable SWE Run links source evidence, selection decisions, application
   packets, landing events, verification, and outcomes through existing
   CAM-SEQ storage.
7. Mining remains explicit and produces a provenance-bearing corpus-delta and
   integrity receipt before mined evidence may be proposed for a build.
8. CAM_CAM aliases remain callable but hidden; direct canonical commands remain
   documented for troubleshooting and runtime development.
9. Active README, quickstart, cheatsheet, manager guide, setup report, and
   troubleshooting docs agree with the implemented state.
10. A real MatrAIx-Persona-8B plus SESA vertical slice proves the mine-to-build
    chain after the control-plane implementation passes its own gates.

## Proof Gates

- A registry coverage test fails for any unclassified CAM_CAM command.
- Help and docs contain no visible duplicate aliases.
- Router tests cover every intent and capability family.
- Read-only operations prove no target, corpus, profile, or configuration
  mutation.
- Mining tests prove explicit scope, budget, receipt, integrity, and delta
  behavior.
- Build/fix tests prove no mutation before the authorized phase.
- Verification failures cannot create positive outcome evidence.
- Promotion, swap, rollback, destructive actions, and production deployment
  remain separate approvals.
- Legacy expert commands continue to work in compatibility tests.
- CAM_Codx focused/full tests, CAM_CAM focused/full tests, skill validation,
  generated-doc checks, and `git diff --check` pass.

## Ownership

CAM_Codx owns semantic routing, workflow policy, approvals, receipts, Codex
skills, user documentation, and target-repository evidence orchestration.

CAM_CAM owns runtime CLI/MCP behavior, models, agents, mining, retrieval,
database schema, CAM-SEQ persistence, validation, self-enhancement, and
evolution.

Codex owns target-repository judgment, edits, tests, and final claims during
normal managed SWE work.

CAM_Codx must call CAM_CAM; it must not vendor, fork, or reimplement the
runtime.

## Safety Boundaries

- Normal SWE requests do not implicitly mine repositories.
- A retrieval hit is evidence, not permission to copy or edit.
- Provider spend requires a visible model, scope, time, and maximum cost.
- Model/profile promotion and live CAM swap each require distinct single-use
  approval and rollback evidence.
- Secrets are never written to packets, receipts, docs, or command arguments.
- Dirty or ambiguous repositories are reported and handled with an explicit
  safe strategy.
- Failed, partial, synthetic, or unverified evidence is never relabeled as a
  verified success.

## Completion State

This goal is active. The design is approved; the implementation plan and code
changes remain to be completed and verified.
