# DECISIONS.md

## Decision Log Overview

This file records the final merged architecture and product decisions for the XTtape showpiece before app implementation. Future agents may supersede an accepted decision only by adding a dated replacement entry with rationale and verification impact.

## Active Decisions

| ID | Decision | Status | Rationale | Verification Impact |
|---|---|---|---|---|
| D-001 | Use FastAPI as the primary backend. | Accepted | Matches the requested stack and gives a clear API/control plane for ingestion, health, summaries, and ticker delivery. | Backend scaffold must expose health and contract endpoints before feature work is considered wired. |
| D-002 | Use Node/TypeScript where it adds ecosystem value. | Accepted | MCP tooling, source adapters, streaming UI support, and Prisma integration fit TypeScript well. | TypeScript packages need explicit ownership and integration tests at API boundaries. |
| D-003 | Use Prisma for structured persistence. | Accepted | Requested stack and suitable for modeled source, event, summary, receipt, ranking, and user-learning data. | Prisma validation and migrations are required early. |
| D-004 | Use local SQLite for MVP persistence. | Accepted | Keeps the showpiece runnable for a novice while preserving Prisma migration discipline. | Schema should avoid SQLite-only assumptions that block a later Postgres move. |
| D-005 | Put external source/tool access behind a registered connector boundary. | Accepted | CAM recall emphasized auditable inventory, scopes, allowlists, and safe registration. | Startup must report loaded connectors, scopes, and credential status without leaking secrets. |
| D-006 | Default external connectors to read-only and allowlisted access. | Accepted | The first proof does not need posting or account mutation. | Any write-capable tool must remain disabled until a later approval-flow decision and tests exist. |
| D-007 | Build a custom narrow read-only X/source MCP. | Accepted | The showpiece is stronger if external access is explicit and inspectable instead of hidden in app logic. | MCP smoke tests must prove inventory, allowlist, and no-write behavior. |
| D-008 | Treat idempotent ingestion and duplicate filtering as core product logic. | Accepted | Live news and social data produce retries, overlaps, and races. | Tests must prove replays and retries do not create duplicate ticker events. |
| D-009 | Store source receipts for every summary, ranking, and explanation. | Accepted | Professional trust requires traceability. | API/UI cannot show AI claims without receipt references and timestamps. |
| D-010 | Include confidence, freshness, and time-decay fields in the first data model. | Accepted | These fields materially improve the ticker over a generic feed. | Ranking tests must cover stale-source decay and confidence changes. |
| D-011 | Make Grok/xAI the first live AI provider, with fallback required. | Accepted | X/social context and xAI tooling match the product concept, but credentials may be absent. | Tests must cover configured-provider and no-provider paths. |
| D-012 | User-learning data must have reset, retention, and audit controls. | Accepted | Learning data is valuable product data and must remain user-controllable. | The learning action is incomplete unless it writes an audit record and reset path exists. |
| D-013 | Make the first UI browser-first. | Accepted | The showpiece needs screenshots, screen recording, and novice-visible progress. | Browser smoke and screenshot capture are required proof artifacts. |
| D-014 | First proof screen must combine RSS/official, X/social, Grok/xAI, and learning. | Accepted | This makes the product point visible in one frame. | A screenshot that lacks one of these pieces does not pass the first proof gate. |
| D-015 | CAM_Codx guides the build process only. | Accepted | XTtape should not embed CAM rows or turn CAM into product storage. | CAM evidence may be cited in docs; runtime data must live in XTtape's own database. |
| D-016 | Do not copy code from mined repositories. | Accepted | The experiment is about methodology transfer, not code import. | Any copied code later requires licensing and user approval. |
| D-017 | Exclude the legacy loose-notes file from this experiment. | Accepted | The comparison must start from the clean initial request and CAM recall packet. | Future agents should not use that file as source material for this showpiece build. |

## Initial Architecture

XTtape starts as a small monorepo:

- `apps/api`: FastAPI backend and ingestion orchestration.
- `apps/web`: React/Vite browser showpiece.
- `packages/db`: Prisma schema, migrations, and generated client.
- `packages/shared`: TypeScript types and OpenAPI-derived contracts where useful.
- `packages/source-mcp`: narrow read-only source/X MCP and connector inventory.
- `fixtures`: replayable source observations for no-credential and regression tests.
- `docs`: screenshots, runbooks, and showpiece evidence.

## Initial Data Model Expectations

The first schema should include durable records for:

- source adapters and connector inventory,
- source observations and raw receipts,
- deduplicated signal events,
- source receipt links,
- AI summaries and explanation records,
- ranking decisions,
- confidence, freshness, and time-decay inputs,
- user preference signals,
- learning audit records,
- reset and retention audit records,
- connector/tool approval records if write-capable tools are ever introduced.

## Deferred Or Rejected Decisions

| Topic | Decision | Reason |
|---|---|---|
| Social posting/write actions | Deferred | Requires approval flow, idempotent persistence, safety review, and credentials. |
| Browser automation ingestion | Deferred fallback only | It is useful for difficult sources but should not be the default source strategy. |
| Production deployment | Out of scope | The current objective is a local showpiece and documented build process. |
| Paid API calls | Deferred | User must approve cost boundaries first. |
| Engagement-maximizing feed mechanics | Rejected | Conflicts with ambient professional awareness. |
