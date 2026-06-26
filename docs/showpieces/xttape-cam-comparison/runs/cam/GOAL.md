# GOAL.md

## Ultimate Goal

Build XTtape, a live AI-based news ticker tape app for professional ambient awareness that provides concise, source-backed, personalized signal without encouraging doomscrolling.

## Current Phase Goal

Create a decision-ready project brain only. No app code has been written or requested in this phase.

## Primary Objectives

| Objective | Why It Matters | Success Signal |
| --- | --- | --- |
| Ambient live ticker | The core product is awareness without a feed addiction loop. | A user can keep XTtape open and see bounded, timely, prioritized updates without infinite scrolling. |
| Source-backed summaries | Professional users need trust, context, and traceability. | Every displayed AI summary links to source receipts and explains what is known, inferred, and uncertain. |
| Multi-source ingestion | News value depends on coverage, diversity, and timeliness. | The system can ingest configured news/source feeds and optional X/social signals through connector boundaries. |
| X/xAI integration where available | X/social signals and xAI may improve early signal detection when credentials permit. | X/xAI features are credential-gated, terms-aware, rate-limited, and replaceable by non-X sources. |
| User learning | Ambient relevance improves only if the app learns what the user considers useful. | Explicit feedback, saves, hides, topic controls, and derived preference/signal data are durably stored and explainable. |
| Durable structured persistence | Preferences, source receipts, and signal history must survive sessions and support later analysis. | Prisma-managed schema captures sources, items, receipts, summaries, user feedback, preferences, and audit records. |
| MCP external-access boundary | Tool/source access must stay auditable, swappable, and credential-safe. | External feeds, X/social providers, AI providers, and enrichment tools are routed through MCP adapters or equivalent boundary services. |
| Professional UX | The app should feel like a calm operations surface, not a social feed. | UI defaults emphasize ticker cadence, source confidence, concise explanations, quiet modes, and reviewable history. |

## Target Users

- Professional users who need situational awareness across news and social signals.
- Users who want fast context and source-backed explanations without spending time inside social feeds.
- Early target can be a single-user local or private deployment, with multi-user support planned only if approved.

## In Scope For The App Build

- FastAPI backend for API orchestration, auth-facing endpoints, streaming endpoints, summarization coordination, and app control surfaces.
- Node/TypeScript services where useful for realtime workers, connector orchestration, Prisma integration, or source APIs with stronger JS ecosystem support.
- Prisma schema and migrations for structured persistence.
- Postgres-backed data model for sources, feed items, source receipts, summaries, user feedback, preferences, signal scores, watchlists, and audit logs.
- MCP boundary for source/tool access and model/provider integration.
- Source connectors for RSS/news APIs and approved web/source feeds.
- Optional X/social and xAI connectors only after credentials, scopes, cost, and terms are confirmed.
- AI summarization, clustering, deduplication, entity/topic extraction, confidence scoring, and source-backed explanation generation.
- User controls for topics, sources, watchlists, priority, quiet mode, save/hide feedback, and explanation depth.
- Durable storage of preference and signal data that is useful for relevance tuning.
- Observability for ingestion latency, connector failures, model calls, rate limits, and summary quality checks.

## Out Of Scope Until Approved

- App code during the project-brain phase.
- Production deployment or cloud resource creation.
- Paid API usage beyond local planning or explicit test approval.
- Scraping sources in ways that bypass terms, paywalls, robots restrictions, or platform controls.
- Storing full copyrighted article bodies unless licensing permits it.
- Multi-tenant enterprise administration beyond architecture readiness.
- Financial, legal, medical, or emergency advice features.
- Autonomous trading, market-moving alerts, or decision automation.
- Using `XTtapeNotes.md` as a source.

## Architecture Stance

XTtape should be a standalone app with a clear separation between product logic, persistence, and external access:

- FastAPI is the main backend/API and orchestration layer.
- TypeScript services are added only where they earn their place: Prisma ownership, source connectors, realtime fanout, queues, or SDKs that are materially better in Node.
- Prisma owns structured schema/migrations. Avoid ambiguous dual ORM ownership between Python and TypeScript.
- Postgres is the initial structured store. Consider pgvector only if semantic retrieval or deduplication needs it.
- MCP adapters isolate external source/tool access, credentials, rate limits, and audit logging.
- The ticker UI should stream from backend state, not directly from connectors or model outputs.
- All displayed AI output must be tied to stored source receipts.

## Initial Data Domains

- `Source`: provider, type, terms class, trust metadata, connector config reference.
- `FeedItem`: normalized item headline/body excerpt/link/time/provider metadata.
- `SourceReceipt`: retrieval event, URL/API endpoint, timestamp, connector/tool, content hash, license/storage policy.
- `Topic` and `Entity`: extracted topics, entities, aliases, and user watchlist links.
- `Cluster`: deduplicated story group across sources and social signals.
- `Summary`: model output, prompt/model metadata, source receipt references, confidence, uncertainty notes.
- `SignalScore`: relevance, novelty, urgency, source diversity, user-fit, recency, and social velocity components.
- `UserPreference`: explicit topics, blocked sources/topics, priority weights, quiet hours, explanation preferences.
- `FeedbackEvent`: save, hide, mute, boost, mark-useful, mark-noisy, correction, or manual topic edit.
- `AuditLog`: connector calls, AI calls, admin changes, preference mutations, and failure records.

## Assumptions

- The first build can target a single professional user or private team rather than public multi-tenant SaaS.
- Browser-based UI is expected, but the frontend framework is not yet decided.
- Postgres is acceptable for initial durable storage.
- Redis or a queue may be useful for ingestion and realtime fanout, but should not be added until the implementation plan proves the need.
- X/xAI credentials may not be available at project start; the app must remain useful with non-X sources.
- AI provider choice is not fixed. Provider selection must be cost-aware and source-backed.
- Source licensing and platform terms will constrain what can be stored and displayed.

## Risks

- X/social API access may be unavailable, expensive, rate-limited, or terms-constrained.
- News source licensing may restrict storage of full content.
- AI summaries can hallucinate or overstate source support unless receipt checks are enforced.
- Personalization can drift into a filter bubble unless diversity and source controls are explicit.
- A ticker can still become anxiety-producing if cadence, priority, and quiet modes are not designed carefully.
- Polyglot persistence can become fragile unless Prisma ownership and FastAPI data access are designed upfront.

## Blockers Before Implementation

- Confirm whether the first app is single-user, private-team, or multi-user.
- Confirm whether real X/xAI integration should be in V0 or designed as a credential-gated later connector.
- Confirm source categories and any must-have providers.
- Confirm whether paid APIs may be used during development.
- Confirm acceptable AI providers and budget guardrails.
- Confirm frontend preference, if any.

## Definition Of Ready For App Build

The app build can start when:

- the user accepts or revises this architecture stance,
- unresolved product-scope blockers are answered or explicitly deferred,
- credential-dependent integrations are marked as mocked, optional, or approved for real testing,
- first implementation milestone and verification gates are written.
