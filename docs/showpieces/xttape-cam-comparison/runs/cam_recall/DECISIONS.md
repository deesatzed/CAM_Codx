# DECISIONS.md

## Decision Log Overview

This file records initial architecture and product decisions for XTtape before app implementation. Decisions marked Accepted define the starting build contract. Future agents may supersede them only by adding a dated replacement entry with rationale and verification impact.

## Active Decisions

| ID | Decision | Status | Rationale | Verification Impact |
|---|---|---|---|---|
| D-001 | Use FastAPI as the primary backend. | Accepted | Matches the requested stack and gives a clear API/control plane for ingestion, health, summaries, and ticker delivery. | Backend scaffold must expose health and contract endpoints before feature work is considered wired. |
| D-002 | Use Node/TypeScript services only where they add ecosystem value. | Accepted | Feed tooling, streaming, MCP clients, and validation-heavy adapters may benefit from TypeScript without splitting the system unnecessarily. | Services need explicit ownership and integration tests at the API boundary. |
| D-003 | Use Prisma for structured persistence. | Accepted | Requested stack and suitable for strongly modeled source, event, summary, receipt, ranking, and user-learning data. | Migrations and typed fixture factories are required early. |
| D-004 | Put all external source/tool access behind an MCP boundary. | Accepted | CAM packet emphasizes auditable tool inventory, allowlists, and safe registration. | Startup must report loaded tools/connectors, scopes, and credential status without leaking secrets. |
| D-005 | Default all external connectors to read-only and allowlisted access. | Accepted | A professional news ticker does not need write actions for the first phase. | Any write-capable tool must be disabled until approval flow tests exist. |
| D-006 | Treat idempotent ingestion and duplicate filtering as core product logic. | Accepted | Live news and social data produce retries, overlapping syndication, and duplicate stories. | Tests must prove replays and retries do not create duplicate ticker events. |
| D-007 | Store source receipts for every summary, ranking, and explanation. | Accepted | Trust and professional use require traceability. | UI/API cannot show AI claims without receipt references and timestamps. |
| D-008 | Include confidence, freshness, and time-decay fields in the first data model. | Accepted | CAM packet identifies these as materially different from a generic plan. | Ranking tests must account for stale-source decay and confidence changes. |
| D-009 | AI provider routing must be capability-aware and fallback-friendly. | Accepted | Credentials and models may be unavailable; the app must still run in degraded mode. | Tests must cover no-provider, fallback summarizer, and configured-provider paths. |
| D-010 | User-learning data must have reset and retention controls. | Accepted | Preferences are durable product data and must remain user-controllable. | API must expose reset/retention behavior before personalization is called complete. |
| D-011 | Do not copy code from CAM-mined repositories. | Accepted | User explicitly requested methodology guidance only. | Any future copied code is out of policy unless separately authorized and licensed. |
| D-012 | Do not use XTtapeNotes.md. | Accepted | User explicitly excluded it from source material. | Future agents should ignore that file if it exists. |

## Initial Default Architecture

XTtape starts as a modular system:

- FastAPI control plane and public API.
- Prisma-backed persistence layer.
- Source adapter layer with metadata, inventory, deterministic identity, and receipts.
- MCP connector boundary for external tools and feeds.
- AI summarization/explanation service with provider capability detection.
- Ticker delivery layer designed for low-friction ambient awareness.
- User-learning layer with durable signal capture, retention policy, and reset controls.

## Initial Data Model Expectations

The first schema should include durable records for:

- source adapters and connector inventory,
- raw observations,
- deduplicated events,
- source receipts,
- AI summaries,
- ranking/explanation decisions,
- confidence and freshness signals,
- time-decay calculations or inputs,
- user preference signals,
- reset and retention audit records,
- connector/tool approval records if write-capable tools are later introduced.

## Rejected Or Deferred Decisions

| Topic | Decision | Reason |
|---|---|---|
| Social posting/write actions | Deferred | Requires explicit approval flow, idempotent persistence, safety review, and credentials. |
| Browser automation ingestion | Deferred fallback only | CAM packet supports it as a fallback for difficult sources, not the default path. |
| Production deployment | Out of scope | User requested project-brain files only. |
| Secret management implementation | Deferred | No app code in this phase; future implementation must validate credentials without exposing values. |
| Engagement-maximizing feed mechanics | Rejected | Conflicts with ambient awareness without doomscrolling. |

## Decision Rules For Future Agents

- If a feature would weaken source receipts, reject or redesign it.
- If a connector cannot report identity, freshness, scope, and credential status, do not treat it as production-ready.
- If an AI provider is unavailable, the system must degrade gracefully instead of failing the whole app.
- If personalization stores user signals, it must include retention and reset behavior.
- If a workflow touches external accounts, credentials, or paid APIs, stop unless credentials and cost boundaries are explicitly available.
- If a test passes only with live secrets, add replay fixtures or dry-run coverage before accepting it as a core evidence gate.

## Pending Decision Questions

These are not blockers for the project-brain phase, but they should be answered before implementation choices harden:

| Question | Default Assumption |
|---|---|
| Which news sources are allowed in the first prototype? | Start with configurable RSS/news adapters and replay fixtures. |
| Which X/xAI capabilities are available? | Treat as optional until credentials are present. |
| What is the retention period for raw source receipts? | Keep configurable retention with explicit default before launch. |
| Should the first UI be web-only? | Yes, unless the user requests native/mobile. |
| Should social write actions ever be part of XTtape? | No for phase one; revisit only with approval workflow and safety gates. |
