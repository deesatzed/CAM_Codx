# PROGRESS.md

## Status Overview

0% complete - Initialization phase.

Only project-brain files have been created. No app code, scaffold, schema, service, connector, test, or deployment artifact has been written.

## Source Materials Used

| Source | Use |
|---|---|
| User product request | Defines XTtape name, purpose, preferred stack, scope, and no-code constraint. |
| `/Volumes/WS4TB/ccxt/showpiece/CAM_CONTEXT_PACKET.md` | Methodology guidance for stronger ingestion, connector, persistence, AI, and evidence-gate planning. |
| Current run directory inspection | Confirmed no existing local project truth files were present before initialization. |

## Current Assumptions

- XTtape begins as a new app, not a continuation of existing app code.
- The preferred stack is FastAPI, optional Node/TypeScript services, Prisma, MCP, and optional X/xAI integration.
- CAM context changes the plan through reusable methodology only.
- No secrets or credentials are available in this phase.
- X/social integration is read-only unless a later decision approves write-capable workflows.
- The first implementation phase should prioritize source integrity and evidence gates over UI polish.

## Task Tracker

| Task | Status | Owner | Notes |
|---|---|---|---|
| Create AGENTS.md | Complete | Codex | Includes standing rules and XTtape CAM-specific constraints. |
| Create GOAL.md | Complete | Codex | Defines product goal, scope, stack, and CAM-vs-generic differences. |
| Create DECISIONS.md | Complete | Codex | Records starting architecture and safety decisions. |
| Create PROGRESS.md | Complete | Codex | Records initialization state, assumptions, risks, blockers, and next actions. |
| Create CAM_MEMORY_APPLIED.md | Complete | Codex | Lists CAM packet items that materially changed the result. |
| Write app code | Not started | Future agent | Explicitly out of scope for this run. |
| Create scaffold | Not started | Future agent | Requires approval to enter implementation phase. |
| Add tests | Not started | Future agent | Test plan is defined as a future evidence gate. |

## CAM-Influenced Work Completed

- Converted the vanilla XTtape request into a source-receipt and evidence-gated build contract.
- Elevated idempotent ingestion, duplicate detection, replay, and dry-run modes into first-phase requirements.
- Added MCP connector inventory, allowlists, read-only defaults, and startup validation requirements.
- Required confidence, freshness, time-decay, and user-learning reset/retention controls in the first data model.
- Added provider fallback and graceful degradation as acceptance criteria.
- Added concurrency, duplicate-ingestion, stale-source, tool-approval, and provider-fallback tests to the future build gate.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Live source APIs can be expensive, rate-limited, or unavailable. | Build may fail or become costly if live APIs are required too early. | Start with dry-run, replay fixtures, and credential validation before live fetches. |
| X/xAI credentials may be unavailable. | Social signal and xAI features may be partial. | Make X/xAI optional and degrade cleanly. |
| AI summaries may obscure source truth. | Professional users may overtrust unsupported summaries. | Require receipts, timestamps, confidence, and source-backed explanations. |
| Ingestion duplicates may pollute the ticker. | User sees noisy repeated stories. | Make deduplication and idempotency core tests. |
| Personalization can become opaque. | User cannot understand or reset learned preferences. | Store preference signals durably with reset and retention controls. |
| MCP tool access can expand silently. | External access becomes hard to audit. | Require startup inventory, allowlists, and read-only defaults. |

## Blockers

No blocker exists for project-brain creation.

Implementation is intentionally blocked until the user approves moving from planning into app build. Future implementation may be blocked by missing credentials, paid API limits, source access restrictions, or unresolved retention policy decisions.

## Next Actions For Future Implementation

1. Confirm the first allowed source set and whether live credentials are available.
2. Scaffold the FastAPI backend, Prisma persistence, and minimal TypeScript service boundary if needed.
3. Define Prisma schema with sources, observations, events, receipts, summaries, rankings, confidence/freshness/time-decay, and user-learning controls.
4. Build connector inventory and config validation before live ingestion.
5. Add dry-run and replay fixtures before using paid or credentialed APIs.
6. Implement idempotent ingestion and duplicate tests.
7. Add AI provider capability detection and fallback summarization.
8. Build a minimal ambient ticker UI only after source receipts and API contracts exist.

## Questions For User Before Build

These should be answered when implementation begins, but they do not block this initialization:

- Which sources should be included in the first prototype?
- Are X/xAI credentials available, and should they be used in the first build?
- What retention policy should apply to raw source receipts and user-learning signals?
- Should the first UI optimize for desktop dashboard, menubar-style ambient display, or browser tab?
- Are write-capable social workflows permanently out of scope or just deferred?
