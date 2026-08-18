# CAM_Codx Tasks 10–13 Release Audit

Date: 2026-08-18

This report is the current evidence audit for
`GOAL_TASK_10_11_12_13.md`. It covers the recovered isolated worktrees, not
the historical `/Volumes/WS4TB/...` checkouts named by older documents.

## Repository and ref identity at audit execution

| Repository | Checkout | Feature and `main` head |
|---|---|---|
| CAM_Codx | `/Users/o2satz/Downloads/crash814/worktrees/CAM_Codx` | `2eabca81108623da34ce484af4d12967486b9ac9` |
| CAM_CAM | `/Users/o2satz/Downloads/crash814/worktrees/CAM_CAM` | `e5693a30ef5b535309b71bd6cc7214cb2a578e8f` |

The table records the exact execution refs used for the audit. The CAM_Codx
report was published in the subsequent `5a82122` documentation commit; later
documentation synchronization may advance the refs without changing the
test receipts below. Both worktrees were clean and `git diff --check` passed at
audit time.

## Requirement evidence

1. **Task 10 routing and packets.** `tests/test_cam_control_plane.py`,
   `tests/test_cam_manager.py`, `tests/test_cam_capability_registry.py`, and
   `tests/test_knowledge_graph_route.py` cover the six SWE intents and mining,
   knowledge, models/benchmark, self-enhancement, evolution, doctor, and
   setup families. The manager catalog derives fixed list-form prefixes from
   the single registry and rejects groups, aliases, unknown routes, policy
   contradictions, changed wrappers, changed contracts, and scope tampering.

2. **Mining boundary.** `prepare_mining_packet` composes
   `tools/cam_pull_mine_dir.py`, the secure wrapper, explicit source/corpus,
   model, repository/time/cost bounds, and a future receipt path. Receipt
   linking hashes one captured file and remains separate from build selection.
   No provider client exists in CAM_Codx and no live mining was run.

3. **Approval separation.** Manager policy tests distinguish read-only,
   local-record, corpus/provider spend, target mutation, promotion/configuration,
   and live-CAM mutation. Approval digests are expiring and single-use; dry
   runs do not consume them.

4. **Task 11 documentation.** `tests/test_cam_documentation_contract.py`,
   `tests/test_cam_codx_skill.py`, generated-pack checks, and the current
   CAM_CAM documentation checks pass. Normal docs use `Use CAM_Codx to ...`;
   direct CAM_CAM use is framed as troubleshooting/runtime development/recovery;
   `cam chat` is not presented as a complete general router.

5. **Generated surface.** `python tools/generate_agent_packs.py --check`
   passes. The capability validator reports `142` paths: `129` managed,
   `2` troubleshooting-only, and `11` hidden compatibility. The pinned
   manifest matches the current CAM_CAM head.

6. **Task 12 release gates.** CAM_Codx focused Task 10–13 gate: `179 passed`.
   CAM_Codx full suite: `208 passed`. CAM_CAM graph/adapter gate: `22 passed`.
   CAM_CAM full suite: `4457 passed, 22 skipped, 9 failed`; seven failures
   are recovery-checkout write-permission failures in pre-existing artifact /
   trace tests, and two are inaccessible real-ganglia databases. No adapter,
   graph, control-plane, or registry regression is among those failures.
   The active implementation plan now uses the actual
   `tests/test_application_packet.py` path.

7. **Temporary installation and read-only identity.** A fresh temporary
   Codex home installed only `cam-codx`. A fixture `assess` plan returned
   `operation_executed=false`, and target/database/config/model-profile identity
   hashes were unchanged. This was local fixture proof; it did not execute CAM,
   mine, call a provider, write a corpus, mutate a target, or change a profile.

8. **Task 13 fixture chain.**
   `tests/test_cam_control_plane_e2e.py` and
   `docs/reports/2026-08-12-cam-control-plane-fixture-proof.md` prove
   assessment, candidate decisions, reviewed plan, simulated landing, failed
   verification, corrected verification, recording, and later recall. Exactly
   the corrected verified result is positive; rejected, deferred, failed, and
   synthetic records remain visible and distinct. This is fixture proof, not
   live-product accuracy or acceptance.

9. **Truth and publication.** `PROGRESS.md` and `DECISIONS.md` contain the
   batch receipts, assumptions, limitations, and policy choices. The owning
   commits are pushed to both feature branches and both `main` refs. No live
   mining, provider spend, production mutation, promotion, deployment, or
   destructive operation was performed.

## Boundary after completion

Tasks 10–13 are complete on the evidence above. Task 14 remains a separate
product-slice contract and approval boundary; it is not implied by this report.
