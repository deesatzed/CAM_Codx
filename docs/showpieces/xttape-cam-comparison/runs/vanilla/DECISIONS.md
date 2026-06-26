# DECISIONS.md

## Decision Log

### D-001: XTtape is an ambient-awareness app, not a feed clone

Status: Accepted

XTtape should optimize for professional ambient awareness and reduced doomscrolling. The default product behavior should be compact, prioritized, and calm rather than engagement-maximizing.

### D-002: FastAPI is the core backend

Status: Accepted

The main backend should be FastAPI. It should own application APIs, orchestration, authentication boundaries, and coordination between persistence, AI summarization, and external-source access.

### D-003: Node/TypeScript is selective, not mandatory everywhere

Status: Accepted

Node/TypeScript services should be used where useful, such as feed workers, streaming adapters, MCP clients, or X/social integrations. They should not replace FastAPI as the core backend without a later decision.

### D-004: Prisma is the structured persistence layer

Status: Accepted

Structured durable data should use Prisma. Expected persisted concepts include sources, feed items, summaries, source references, user preferences, learned signals, integration state, and feedback events.

### D-005: External source/tool access goes through an MCP boundary

Status: Accepted

External feeds, social data, source tools, and other tool-backed retrieval should be accessed through an explicit MCP boundary where practical. This keeps external capability access auditable and replaceable.

### D-006: X/xAI integration is credential-gated

Status: Accepted

X/xAI features should be implemented only when credentials and account/API access are available. The core app should still have a credential-free path for local development and non-X sources.

### D-007: Summaries must remain source-backed

Status: Accepted

AI summaries and explanations should preserve provenance. The app should distinguish source facts, model-generated synthesis, and inferred relevance.

### D-008: User learning must be durable and controllable

Status: Accepted

Useful preference and signal data should be stored durably, but the design must account for privacy, correction, retention, and explainability before implementation.

### D-009: No app code in the initial project-brain phase

Status: Accepted

This phase creates only `AGENTS.md`, `GOAL.md`, `DECISIONS.md`, and `PROGRESS.md`. Implementation starts only after user approval.
