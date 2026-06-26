# GOAL.md

## Ultimate Goal

Build XTtape, a live AI-based news ticker tape for professional ambient awareness that combines live source feeds, X/social signals, AI summarization, source-backed explanations, user learning, and durable preference/signal storage without encouraging doomscrolling.

## Current Phase

0% complete - project-brain initialization only. No app code has been written in this run.

## User Value

XTtape should let a professional user glance at a calm, trustworthy ticker and understand what matters, why it matters, which sources support it, and how the system learned their preferences, without opening a chaotic feed or losing source provenance.

## Primary Objectives

| Objective | Why It Matters | Success Signal |
|---|---|---|
| Ambient live ticker | The product is for awareness, not feed addiction. | User can monitor concise AI-ranked updates without entering an infinite scroll workflow. |
| Source-backed summaries | Professional users need traceability and confidence. | Every summary has source receipts, timestamps, freshness, confidence, and explanation metadata. |
| Idempotent ingestion | Live feeds and social signals will duplicate, race, and retry. | Re-running ingestion does not duplicate items and produces stable source identities. |
| MCP-governed external access | External tools and sources need auditable boundaries. | All external source/tool access is registered, allowlisted, logged, and read-only by default. |
| Provider-aware AI layer | AI credentials and model availability will vary. | Summarization and explanation degrade gracefully across providers, including no-provider fallback. |
| Durable user learning | Preferences and useful signals are product data, not session state. | Prisma-backed records store preference/signal history with reset, retention, and audit controls. |
| Evidence-first build gates | CAM recall identifies failure modes that should be tested early. | Acceptance tests cover duplicate ingestion, concurrent source fetches, stale feeds, approval flows, and provider fallback before UI polish is treated as complete. |

## Preferred Stack

- FastAPI backend for primary API, orchestration, health checks, and server-side control paths.
- Node/TypeScript services where useful for feed adapters, MCP clients, streaming UI support, or ecosystem integrations.
- Prisma for structured persistence and migrations.
- MCP boundary for external source/tool access.
- X/xAI integration where credentials are available.

## CAM Recall Difference From A Generic Plan

A generic XTtape plan would likely start with feeds, summaries, a ticker UI, and persistence. The CAM recall layer changes the initial product contract:

- Source adapters are metadata-rich components with inventory, scope, allowlists, deterministic cache keys, and startup reporting.
- Duplicate filtering, immediate persistence, replay, and dry-run modes are core ingestion behavior, not operational cleanup.
- Summaries and rankings require source receipts, confidence, freshness, and time-decay data from the first schema pass.
- AI summarization must include provider capability detection and fallback behavior before live integrations are trusted.
- User learning must include reset and retention controls from the start.
- Write-capable social actions are out of scope until approval flows and idempotent persistence exist.
- Evidence gates for concurrency, stale-source behavior, duplicate ingestion, tool approval, and provider fallback are part of the build definition, not later hardening.

## In Scope For First Implementation Phase

- Project scaffold using the preferred stack.
- API contracts for ticker items, source adapters, summaries, explanations, user preference signals, and connector health.
- Prisma schema for sources, raw observations, deduplicated events, summaries, receipts, rankings, user signals, preferences, and retention/reset audit records.
- MCP connector registry with inventory, allowlist, credential validation, and read-only defaults.
- Source adapter abstraction for RSS/news feeds, social/X signals where credentials exist, and replay fixtures.
- Idempotent ingestion pipeline with duplicate detection and source receipts.
- AI summarization and explanation interface with provider capability detection and graceful fallback.
- Initial non-doomscrolling ticker UX specification and API support.
- Test plan and evidence gates before treating implementation as build-ready.

## Out Of Scope Until Later Decision

- Production deployment.
- Paid API usage beyond local credential checks.
- Secret storage beyond environment-variable and config-validation design.
- Write actions to X/social platforms.
- Personalized recommendation claims without auditable preference records.
- Browser automation as a default ingestion path.
- Mobile-native apps.
- Monetization, billing, teams, or enterprise admin features.

## Assumptions

- The app starts as a local or developer-run prototype with professional-grade data contracts.
- X/xAI features are optional until credentials are available.
- MCP access should default to read-only source retrieval and tool inspection.
- Prisma is the source of truth for structured data; append-only raw source receipts should be retained where legally and operationally acceptable.
- The user wants a calm, glanceable interface, not a social-media replacement.
- The CAM packet is methodology guidance only and does not authorize copying code from mined repositories.

## Non-Goals

- Do not build a generic social feed clone.
- Do not maximize engagement time.
- Do not hide why an item appeared.
- Do not summarize untrusted source material without receipts.
- Do not require all AI providers to be configured for the app to run.
- Do not write app code in the project-brain phase.

## Proceed/No-Go Criteria For App Build

Proceed to implementation only when these are accepted:

- The first schema includes receipts, freshness, confidence, time decay, deduplication keys, and user learning controls.
- The connector design includes inventory, allowlists, startup validation, dry-run, and replay.
- The AI plan includes provider fallback and no-provider degradation.
- The test plan includes the CAM-derived edge cases.
- Secrets and credentials remain unexposed.
