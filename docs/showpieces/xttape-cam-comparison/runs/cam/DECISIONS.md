# DECISIONS.md

## Decision Log Overview

This file records durable XTtape architecture and scope decisions. Future agents should update this file when a decision changes implementation direction, security posture, data ownership, product scope, or verification requirements.

## Active Decisions

| ID | Decision | Status | Rationale | Verification / Follow-up |
| --- | --- | --- | --- | --- |
| D-000 | Create only project-brain files in this phase. | Accepted | The user explicitly requested no app code yet. | Only `AGENTS.md`, `GOAL.md`, `DECISIONS.md`, `PROGRESS.md`, and `CAM_MEMORY_APPLIED.md` should exist from this pass. |
| D-001 | XTtape is a standalone app, not a CAM runtime or generic agent platform. | Accepted | Keeps product scope clean and prevents architecture drift. | Future scaffolding should use app-specific package names and boundaries. |
| D-002 | FastAPI is the main backend/API orchestration layer. | Accepted | Matches preferred stack and fits streaming APIs, AI orchestration, and app control surfaces. | Implementation plan must define API, auth, and streaming boundaries. |
| D-003 | TypeScript services are optional and must justify themselves. | Accepted | Node/TypeScript is useful for Prisma, SDK-heavy connectors, and realtime workers, but should not become parallel app logic by default. | Each TypeScript service needs a clear owner, interface, and failure mode. |
| D-004 | Prisma owns structured schema and migrations. | Accepted | User requested Prisma for structured persistence. | Before coding, choose whether FastAPI writes through a TypeScript persistence service, direct SQL repository layer, or another single-writer pattern. |
| D-005 | Postgres is the default structured store. | Proposed | Best initial fit for durable records, joins, audits, and later pgvector if needed. | Confirm no hosted DB preference conflicts with this. |
| D-006 | External sources and tools must cross an MCP boundary or equivalent connector boundary. | Accepted | Improves auditability, credential containment, tool replacement, and testing. | Connector contracts must log source receipts without exposing secrets. |
| D-007 | Every displayed AI summary requires source receipts. | Accepted | Core trust requirement for professional source-backed explanations. | Add tests that reject orphan summaries without linked receipts. |
| D-008 | X/xAI integration is credential-gated and optional for V0. | Accepted | Credentials, terms, rate limits, and cost are unknown. | V0 must remain useful with RSS/news/source feeds if X/xAI is unavailable. |
| D-009 | Store preference/signal data durably but explainably. | Accepted | User learning is a core product requirement, but opaque personalization is risky. | Separate explicit feedback from derived weights and provide "why shown" explanations. |
| D-010 | UX should be ambient and bounded, not an infinite social feed. | Accepted | The product promise is awareness without doomscrolling. | UI requirements should include cadence limits, quiet mode, save/review queue, and source diversity controls. |
| D-011 | Do not use `XTtapeNotes.md`. | Accepted | The user explicitly prohibited it. | Future agents should ignore the file unless explicitly instructed otherwise. |

## Initial Default Decisions

- Start with a private/single-user or private-team design unless the user requests public multi-tenant SaaS.
- Treat authentication as required for any non-local deployment, even if V0 is single-user.
- Treat source licensing as a first-class data model concern.
- Prefer storing metadata, hashes, links, short snippets, summaries, and receipts over full source bodies.
- Use mocks and fixtures for credential-gated connectors until credentials and terms are confirmed.
- Make model/provider usage cost-visible before any large ingestion or summarization run.
- Keep all secrets out of Markdown, logs, commits, prompts, and saved artifacts.

## Pending Decision Questions

| ID | Question | Impact If Unanswered | Safe Default |
| --- | --- | --- | --- |
| Q-001 | Is V0 single-user, private-team, or multi-tenant? | Affects auth, schema, tenancy, privacy, and deployment. | Single-user/private-team architecture with a path to multi-user. |
| Q-002 | Which source classes are must-have for V0? | Affects connector priority and licensing checks. | RSS/news API connectors first; X/social optional. |
| Q-003 | Are X/xAI credentials available and approved for test use? | Determines whether real X/xAI integration can be built early. | Mock/stub connector contract only. |
| Q-004 | What AI provider and budget guardrails are approved? | Affects summarization, ranking, and cost controls. | Provider-agnostic interface with local/mock tests. |
| Q-005 | What frontend stack should be used? | Affects project scaffold and realtime implementation. | TypeScript web UI, framework to be selected before scaffolding. |
| Q-006 | Are there compliance, employer, or industry restrictions for source use? | Affects storage, retention, audit, and source terms. | Minimal retention and conservative source storage. |
| Q-007 | What is the acceptable ticker cadence? | Affects product UX and anxiety/doomscrolling risk. | Calm defaults with user-configurable frequency and quiet mode. |

## Superseded Decisions

None yet.

## Decision Rules For Future Agents

- Update this file when a decision changes scope, architecture, credentials, data storage, privacy, or verification.
- Do not quietly convert proposed decisions into accepted decisions without evidence or user approval.
- Keep credential-dependent work blocked, mocked, or explicitly approved.
- If implementation pressure conflicts with source provenance, source provenance wins.
- If app usefulness depends on a paid or unavailable provider, design a fallback path before coding that dependency.
- When in doubt, preserve the ambient-awareness product promise over engagement-heavy features.
