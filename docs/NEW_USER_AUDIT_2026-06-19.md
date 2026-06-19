# CAM_Codx New-User Audit - 2026-06-19

This audit records the live local state of `deesatzed/CAM_Codx.git` so CAM_CAM launch copy does not blur the product boundary.

## Verdict

`/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology` is the clean public-facing checkout for `https://github.com/deesatzed/CAM_Codx.git`.

`/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl` is a separate implementation workspace on `feature/initial-impl`. It is ahead of its remote branch and dirty. It should not be presented as launch-clean until its branch state is reconciled.

## Public Checkout

- Path: `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology`
- Remote: `https://github.com/deesatzed/CAM_Codx.git`
- Branch: `main`
- Status before this audit: clean and aligned with `origin/main`
- Recent commits:
  - `a69be8e docs: retroactive design approval record for Sections 1-6 (gate 0.6)`
  - `ec014b1 docs(plan): TDD implementation plan for Codex-CAM Methodology v1`
  - `b207c18 Standalone redesign: CAM_Codx is now standalone with optional CAM_CAM bridge`
  - `2ae4307 Strip Claude/Cursor framing; reframe new MCP as the repo's centerpiece`
  - `17baa38 Add Phase 0-1 baseline-measurement harness (prerequisites only, not executed)`

New-user interpretation:

- CAM_Codx is separate from CAM_CAM.
- CAM_Codx is the four-tool Codex/CAM methodology bridge design and planning repo.
- CAM_CAM is only an optional corpus producer through `CAM_CODEX_MCP_DB_PATH`.
- The public `main` branch should be read as the authoritative front door unless the implementation branch is explicitly promoted.

## Implementation Workspace

- Path: `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl`
- Remote: `https://github.com/deesatzed/CAM_Codx.git`
- Branch: `feature/initial-impl`
- Status before this audit: `feature/initial-impl...origin/feature/initial-impl [ahead 1]`
- Dirty state includes deleted files, modified README and code/tests, and untracked data/instance artifacts.
- Recent commits:
  - `b43c039 Build CAM-AMOE v0 evaluator`
  - `a159d20 docs: update HANDOFF with session 2 results -- uv venv, all tests green, 3 showpieces`
  - `b813cd5 docs: SBP-1 self-enhance showpiece -- CAM_CAM enhances itself`
  - `e6ae4b2 docs(showpiece): add enhancement demo artifact SBP-2 -- dspy-agent-skills`
  - `cef154d docs(showpiece): add synergy graph report SBP-3`

Launch implication:

- Do not copy implementation files into CAM_CAM for this launch-refresh goal.
- Do not claim the implementation workspace is ready for a new user.
- If CAM_Codx implementation is meant to launch, create a separate reconciliation goal to decide whether `feature/initial-impl` should be cleaned, merged, or archived.

## New-User README Requirements

The public README should continue to make these points in the first screen:

1. CAM_Codx is separate from CAM_CAM.
2. CAM_Codx is a Codex-facing MCP/methodology bridge, not the CAM_CAM product repo.
3. Standalone mode works without CAM_CAM; connected mode uses CAM_CAM's `claw.db`.
4. The supported public surface is four tools: `cam_recall`, `cam_provenance`, `cam_decisions_search`, and `cam_record_outcome`.
5. Any implementation-branch or CAM-AMOE evidence is branch-specific until promoted.
