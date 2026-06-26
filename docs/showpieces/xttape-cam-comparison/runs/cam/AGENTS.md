# AGENTS.md

## Project

XTtape is a new app for professional ambient news awareness. It should help a user know what is happening without doomscrolling by combining live source feeds, X/social signals where credentials permit, AI summarization, source-backed explanations, user learning, and durable preference/signal storage.

## Source Of Truth

Before coding or planning implementation details, read these files if present:

1. `GOAL.md`
2. `DECISIONS.md`
3. `PROGRESS.md`
4. `CAM_MEMORY_APPLIED.md`

If later created, also read `STANDARDS.md`, `IMPLEMENT.md`, and `TASK_QUEUE.md`.

Do not use `XTtapeNotes.md` as source evidence or project direction. If that file appears later, ignore it unless the user explicitly reverses this rule.

## Current Boundary

This directory currently contains project-brain documents only. Do not write app code until the user explicitly approves proceeding to the implementation phase.

Allowed now:

- refine project-control Markdown files,
- perform repository reconnaissance,
- draft architecture and task plans,
- identify blockers and assumptions,
- propose verification gates.

Not allowed now:

- scaffold application source code,
- create API keys, accounts, deployments, databases, or cloud resources,
- read, print, store, or transmit secrets,
- perform production deployment,
- ingest real user data or private feeds without explicit approval.

## Preferred Stack

- FastAPI backend for API orchestration, auth-facing endpoints, streaming endpoints, and AI workflow coordination.
- Node/TypeScript services where they materially improve connector, realtime, worker, or Prisma integration.
- Prisma for structured persistence with a single schema/migration owner.
- Postgres as the expected primary structured store unless a later decision supersedes it.
- MCP boundary for external source/tool access, especially news providers, X/social providers, xAI/OpenAI/LLM providers, source lookup, and enrichment tools.
- X/xAI integration only where credentials, terms, and budget are confirmed.

## Architecture Rules

- Keep XTtape standalone. Do not turn it into a CAM runtime, Codex runtime, or generic agent platform.
- Treat MCP as the external-access boundary, not as a place to hide business logic.
- Keep source provenance attached to every generated claim: source URL/provider, retrieval time, connector/tool, source confidence, and summary/explanation lineage.
- Avoid dual-writer persistence. If Prisma owns schema and migrations, define clear service boundaries for Python and TypeScript access before implementation.
- Prefer resumable ingestion, explicit rate limits, and connector health checks over opaque background polling.
- Design for ambient awareness: bounded ticker cadence, source diversity, topic controls, quiet modes, and no infinite-scroll engagement loop by default.
- Make user learning explainable. Store explicit feedback and derived preference signals separately, with export/delete paths planned before storing real user data.

## Security And Privacy

- Never expose secrets, credentials, tokens, API keys, cookies, private messages, PHI, or unnecessary sensitive data in files, logs, prompts, or handoffs.
- Credentials must be supplied through environment variables or an approved secret manager only.
- X/social integrations must respect provider terms, rate limits, scopes, and user consent.
- Store only the source content needed for lawful summarization and explainability. Prefer metadata, links, hashes, short snippets, and summaries over full article bodies unless licensing permits storage.
- Add audit logs for connector calls, AI calls, preference updates, and administrative changes.

## AI Behavior Rules

- AI summaries must be source-backed and uncertainty-aware.
- The app must distinguish observed facts from model interpretation.
- No generated item should appear without traceable source receipts.
- User-facing explanations should answer why the item appeared, what sources support it, and what is uncertain.
- Do not present predictions, finance implications, legal conclusions, medical conclusions, or crisis interpretation as authoritative advice.

## Verification Rules

Before claiming any implementation complete, future agents must provide evidence:

- tests or smoke checks actually run,
- data model migrations validated,
- connector behavior tested with mocked and, where approved, real credentials,
- source receipt/provenance checks passing,
- no secrets printed or committed,
- `git status --short --branch` captured if this becomes a git repo,
- blocker list updated in `PROGRESS.md`.

## Autonomous Progress

If a safe assumption is needed, make it, record it in `PROGRESS.md`, and continue. Stop only for missing credentials, missing paid accounts, destructive actions, production deployment, sensitive data risk, legal/compliance uncertainty, repeated failure after mitigation attempts, or a product decision that materially changes scope.
