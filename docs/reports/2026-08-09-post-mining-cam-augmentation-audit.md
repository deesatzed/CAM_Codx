# Post-Mining CAM Augmentation Audit

**Date:** 2026-08-09

## Executive Verdict

The latest mining batch is usable now, but mining alone does not enhance CAM's runtime. The 80 new findings are stored as embryonic evidence and must pass a reviewed adoption gate before they influence code, prompts, or policy.

One operational defect was safe to fix immediately: 40 findings landed in the TypeScript and Rust ganglia, while the live root configuration federated only Go and misc. `claw.toml` and `DB_REGISTRY.md` now bind all four sibling ganglia. The remaining recommendations below are proposals, not silently enacted self-modifications.

No provider call or additional model spend was used for this audit. `cam self-enhance start` was not run.

## Verified Post-Mining State

Source evidence: CAM_CAM `docs/reports/2026-08-09-priority15-grok-mining-results.md` and receipt `data/mining_runs/2026-08-09-repos-txt-priority15-grok-4.5-5usd.json`.

| Evidence | Verified result |
|---|---|
| Model | Exact `x-ai/grok-4.5` on every call |
| Spend | `$3.0921648` against a `$5.00` authorization |
| Calls | 96 completed, 0 failed |
| Repositories | 15 processed; 14 source-bearing repos mined |
| Findings | 80 stored: root 30, Go 10, TypeScript 35, Rust 5 |
| Root corpus | 2,668 methodologies from 215 source repositories |
| Lifecycle | 2,504 embryonic, 144 viable, 3 thriving, 17 declining |
| Integrity | Root, Go, misc, TypeScript, and Rust databases all return `ok` |
| Federation after cleanup | Enabled with four siblings: Go, misc, TypeScript, Rust |
| CAG | Stale, not loaded, zero cached methodologies |

`taste-skill` remains a durable no-spend skip: discovery recognizes the Git repository, but the miner finds no supported source files.

## Completed During This Audit

### P0: authoritative corpus and federation binding

- Created CAM_CAM `DB_REGISTRY.md` for the canonical root and selected ganglia.
- Kept SQLite WAL/SHM files on disk and ignored them in Git.
- Corrected active CAM_Codx paths to `/Volumes/WS4TB/repo622sn/CAM_CAM`.
- Added TypeScript and Rust to `[[instances.siblings]]`; `cam stats --json` now reports `sibling_count: 4`.
- Aligned the stale config test with the already canonical `claw.db` root path.

This adapts finding `fac7d317-063a-4b02-9394-f3411dae3527` from CAM_Codx: authoritative corpus registry with split-brain binding.

## Existing Capabilities: Do Not Duplicate

| Candidate concept | Existing CAM evidence | Decision |
|---|---|---|
| Family/agent messaging | Specialist routing and stored external exchanges in `src/claw/mcp_server.py` and `external_specialist_exchanges` | Do not transplant prime-agent messaging wholesale |
| Persistent autonomous agent loop | CAM-PULSE daemon in `src/claw/pulse/orchestrator.py` | Do not add a second daemon |
| Staged self-enhancement | `self-enhance start`, `validate`, `swap`, and `rollback` in `src/claw/cli/_monolith.py` | Harden gates; do not replace pipeline |
| Model comparison and selection | Budget ledger, tournament, profile promotion, rollback, exact model receipts under `src/claw/models/` | Extend user guidance/contract only where drift remains |
| Host capability packs | 19-capability shared contract plus deterministic agent-pack generator in CAM_Codx | Refresh from runtime; do not hand-maintain parallel packs |

## Ranked Enhancement Backlog

### P0: add a reviewed post-mining adoption gate

**Owner:** CAM_Codx program manager with CAM_CAM proposal/runtime support.

Require a selected-finding manifest before implementation. Each entry must contain methodology ID, source repo, applicability, conflicting existing capability, proposed owner, risk, tests, rollback, and explicit approval state. Real provider spend and self-modification remain blocked until the manifest is reviewed.

Adapt:

- `f96b216b-2a32-4653-a4f0-a3b6670b058e` — SkillOpt staged proposal plus backup-before-adopt.
- `b7f3dbce-363a-4be0-9bae-22d623e4f5ea` — reviewed-tasks gate before provider spend.
- `5dbfe521-324b-4c8b-8ee5-c6c0c49025bb` — validation-gated bounded text edits.

**Proof gate:** a no-spend command produces a deterministic adoption manifest; an unreviewed manifest cannot invoke provider calls, edit active files, or run `self-enhance swap`.

### P0: add runtime identity/provenance preflight

**Owner:** CAM_Codx setup/preflight.

An unpinned `python -c 'import claw'` currently resolves the older editable checkout at `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`, while `PYTHONPATH=/Volumes/WS4TB/repo622sn/CAM_CAM/src` resolves the authoritative checkout. Add a preflight that prints and validates module path, Git head, config path, DB path, DB integrity, and registry digest before mutation or paid work.

**Proof gate:** preflight fails closed on a mismatched module/config/database tuple and passes for the canonical tuple without revealing keys.

### P1: make self-enhancement eligibility evidence-based

**Owner:** CAM_CAM.

`cam self-enhance status` currently recommends work when total methodology count exceeds a threshold. Replace that weak signal with post-last-run delta, selected high-potential findings, lifecycle/evidence quality, observed outcomes, and an approved adoption manifest.

**Proof gate:** a large but unchanged embryonic corpus cannot trigger readiness; a reviewed, evidence-bearing delta can.

### P1: derive CLI, MCP, and agent-pack documentation from runtime registries

**Owner:** CAM_CAM command/tool registry plus CAM_Codx generator.

Adapt the Guild patterns:

- `5e9646fc-f3c2-4954-8979-e655a147a539` — unified CLI/MCP command metadata.
- `f6c10586-286a-4024-9e8c-8685d4ff0114` — documentation generated from live CLI/MCP discovery.

CAM already has a deterministic host-pack generator, but its capability input is manually curated and was still bound to an old runtime path. Prefer a machine-readable runtime export and a conformance test over duplicating command registries prematurely.

**Proof gate:** a runtime tool/command change causes the contract check to fail until generated documentation is refreshed.

### P1: make documentation-only mining eligibility explicit

**Owner:** CAM_CAM discovery/miner boundary.

Classify repositories such as `taste-skill` as `docs_or_skill_only`, either route them through a bounded Markdown/skill miner or persist a stable unsupported receipt. Do not repeatedly offer the same repository as changed-only eligible when the miner will always skip it.

**Proof gate:** a second unchanged scan is excluded without an LLM request and explains the durable classification.

### P1: rebuild CAG only after an approved corpus checkpoint

**Owner:** CAM_CAM operations.

The root CAG is currently stale and empty. Add an explicit post-mining checkpoint that verifies database integrity and finding reconciliation before rebuilding each configured ganglion cache.

**Proof gate:** rebuilt caches report current methodology counts and retrieval smoke tests pass per ganglion. This audit intentionally did not rebuild them.

### P2: close the outcome loop for adopted methodologies

**Owner:** CAM_Codx plus CAM_CAM outcome ledger.

For every adopted finding, record implementation commit, verification result, rollback result if any, and methodology outcome. Promotion should depend on observed results, not potential score alone.

### P2: selectively adapt operational patterns

- `543e70ed-a6a3-4c6c-9cbc-10adc3e5079b`: use LocalRecall's transactional pre-embed migration only when embedding model/dimension changes.
- `d42bca52-7695-4eeb-8975-56cd771a5693`: use Markmap's serialized callback coalescing for overlapping filesystem or refresh events.
- `91d9df54-fbd7-4129-9d10-d51e1f89d4db`: consider the TTL/re-stat cache only for demonstrably expensive repo inventory scans.
- `e24c81f3-2d2d-44f5-ac0b-9c3afec52e7f`: preserve finESS's summaries-only privacy boundary when external LLM analysis can use local aggregates instead of raw sensitive data.

Each remains conditional on a concrete CAM bottleneck and targeted tests.

## Rejected or Deferred

- Reject wholesale prime-agent persistent REPL/manager architecture: it duplicates CAM-PULSE, routing, receipts, and specialist exchanges while weakening existing approval boundaries.
- Reject automatic prompt or skill self-editing based only on mined potential scores.
- Defer prime-agent steering/follow-up queue semantics (`28f5f4ba-c7b7-43d8-98fb-f15e2ca6e552`) until CAM has a demonstrated interruption-delivery problem.
- Defer the protected slow-update memory section (`48dadb04-dac8-4c15-8ac1-9e31cc91d9dc`) until a specific longitudinal CAM memory document needs controlled consolidation.

## Known Audit Debt

- The focused CAM_CAM suite passes but emits two non-fatal `aiosqlite` event-loop shutdown warnings in `tests/test_miner_brains.py`; connection cleanup should be repaired in a separate focused change.
- Historical plans, handoffs, and evidence packets still contain old WS4TBr paths. They were not rewritten because doing so would falsify historical context. Active truth surfaces were corrected.
- CAG remains stale by design pending a reviewed rebuild checkpoint.

## Recommended Next Execution Batch

Implement the two P0 gates together: runtime identity preflight plus reviewed adoption manifests. Then fix documentation-only eligibility. Only after those gates pass should CAM evaluate whether any selected finding warrants a staged `self-enhance` proposal.
