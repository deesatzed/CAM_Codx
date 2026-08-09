# Post-Mining CAM Augmentation Audit Design

**Date:** 2026-08-09  
**Status:** Approved for execution by the user's instruction to proceed with cleanup and audit

## Objective

Turn the latest successful mining run into durable CAM program-management truth without spending more model budget, deleting live database state, or automatically changing CAM behavior.

## Scope

This pass covers two repositories with distinct ownership:

- `CAM_CAM` owns the live mining runtime, `claw.toml`, `claw.db`, database sidecars, model controls, and corpus operations.
- `CAM_Codx` owns the program-management contract, adoption audit, capability documentation, and prioritized enhancement backlog.

The live runtime is `/Volumes/WS4TB/repo622sn/CAM_CAM`. The live corpus is `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db`.

## Cleanup Decisions

1. Preserve the intentional `claw.toml` changes and validate them before committing.
2. Preserve `claw.db-wal` and `claw.db-shm` on disk. They are SQLite runtime state, not disposable build artifacts.
3. Ignore future `*.db-wal` and `*.db-shm` files so live SQLite state does not make Git appear dirty.
4. Preserve and track `GOAL_CAM_SUBSCIBED.md`; its misspelled filename is an explicit compatibility choice in the contract.
5. Correct active CAM_Codx path references that still point to the older `/Volumes/WS4TB/WS4TBr` checkout.
6. Publish only explicitly reviewed files. Do not stage databases, credentials, receipts, or unrelated changes.

## Audit Method

The audit is no-spend and evidence-gated:

1. Verify the post-mining database counts and integrity.
2. Review high-value findings from the latest mined repositories.
3. Compare each candidate idea with capabilities already present in CAM_CAM and CAM_Codx.
4. Classify candidates as adopt now, adapt later, already present, or reject/defer.
5. Record provenance, rationale, owner, verification gate, and priority.

Mining output is evidence for review, not authorization for self-modification. `cam self-enhance status` is treated as a threshold signal, not proof that an enhancement is safe or valuable.

## Recommended Enhancement Shape

The audit should prioritize:

- authoritative runtime/corpus identity checks;
- a reviewed post-mining adoption gate;
- quality- and outcome-aware self-enhancement triggers;
- generated capability/documentation conformance;
- explicit handling for documentation-only repositories;
- controlled CAG refresh after approved mining; and
- outcome logging for adopted methodologies.

It should avoid duplicating existing specialist routing, PULSE, staged self-enhancement, transaction receipts, or model tournament controls. It should reject wholesale adoption of persistent-agent or automatic self-editing patterns that bypass CAM's approval and rollback boundaries.

## Deliverables

- Clean Git status in CAM_CAM and CAM_Codx, with live sidecars retained but ignored.
- Validated and committed CAM_CAM configuration.
- Corrected CAM_Codx runtime paths and tracked subscribed goal contract.
- A dated post-mining augmentation audit with ranked, actionable recommendations.
- Updated progress and decision records.
- Verification evidence and pushed commits for both repositories.

## Stop Rules

Stop rather than improvise if cleanup would require deleting an unverified database, if repository history diverges from origin, if credentials are missing for an explicitly required operation, or if verification indicates database corruption.
