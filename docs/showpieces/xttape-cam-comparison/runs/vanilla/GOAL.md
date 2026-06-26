# GOAL.md

## Objective

Build a new app called XTtape: a live AI-based news ticker tape for professional users who want ambient awareness without doomscrolling.

The app should combine live news and source feeds, X/social signals, AI summarization, user learning, source-backed explanations, and durable storage of useful preference and signal data.

## User

The primary user is a professional who wants to stay aware of important developments while staying focused. XTtape should reduce the need to repeatedly open feeds, scan timelines, or doomscroll.

## Product Stance

XTtape should behave like an intelligent ambient ticker, not a social feed clone.

Core experience:

- live, compact updates,
- prioritized relevance,
- concise AI summaries,
- source-backed explanations,
- controllable signal intensity,
- learned user preferences,
- durable memory for useful preference and signal data.

## Preferred Architecture

- FastAPI backend as the main API and orchestration layer.
- Node/TypeScript services where they are genuinely useful, especially for feed workers, streaming adapters, MCP clients, or X/social integrations.
- Prisma for structured persistence.
- MCP boundary for external source and tool access.
- X/xAI integration only where valid credentials and access are available.

## Core Capabilities To Design For

1. Live ticker stream
   - Show timely, compact news items.
   - Support professional ambient awareness rather than infinite browsing.

2. Source and feed ingestion
   - Ingest live news and source feeds.
   - Preserve source metadata, timestamps, links, and provenance.

3. X/social signal integration
   - Integrate X/social signals where credentials and API access permit.
   - Treat social signals as signals, not unquestioned facts.

4. AI summarization
   - Summarize items into concise, source-backed updates.
   - Maintain enough traceability for users to inspect why a summary was shown.

5. Source-backed explanations
   - Provide explanations grounded in underlying sources.
   - Distinguish source facts, model interpretation, and inferred relevance.

6. User learning
   - Learn from explicit and implicit user preferences.
   - Store useful preference and signal data durably.
   - Keep learned data inspectable and correctable where practical.

7. Durable persistence
   - Store feeds, sources, items, summaries, user preferences, relevance signals, and integration state in structured persistence.

## Non-Goals For Initial Project-Brain Phase

- Do not write app code.
- Do not implement database schema yet.
- Do not connect to external feeds yet.
- Do not request or expose credentials.
- Do not rely on `XTtapeNotes.md`, CAM, `claw.db`, or external memory systems.

## Readiness Criteria Before Implementation

The project is ready to proceed to actual app build when the following are clear:

- MVP scope is selected.
- Credential-dependent integrations are separated from credential-free local/demo behavior.
- Persistence entities are sketched.
- MCP boundary responsibilities are defined.
- AI summarization and source-provenance rules are defined.
- User-learning behavior is bounded and privacy-aware.
- Blockers and risks are accepted or mitigated.

## Initial Blockers

- X/xAI integration depends on credentials and account/API access.
- Live news/source access depends on feed choices, licensing, rate limits, and terms of use.
- AI summarization depends on selected model provider, budget, latency targets, and safety expectations.
- Preference learning requires privacy, retention, and user-control decisions before durable storage is finalized.
- Professional-use quality requires clear provenance and source-backed explanations, not summary-only output.

## Success Definition

XTtape succeeds if a professional user can keep a passive, trustworthy awareness stream open, quickly understand why an item matters, inspect the source basis, and see the app improve relevance over time without requiring social-feed-style attention.
