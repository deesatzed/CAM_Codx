# AGENTS.md

## Project Source Boundary

This project brain was created only from the user request to build XTtape.

Do not use `XTtapeNotes.md`, CAM, `claw.db`, external memory systems, or unrelated prior context as source material for this initial project state. Future use of additional source files requires explicit user permission and must be recorded in `PROGRESS.md`.

## Project Source Of Truth

Before implementation work, read these files in this order when present:

1. `GOAL.md`
2. `DECISIONS.md`
3. `PROGRESS.md`

Treat these files as the current project contract until the user changes scope.

## Build Rules

- Do not write app code until the user explicitly approves moving from project-brain planning to implementation.
- Preserve secrets discipline: never expose API keys, X/xAI credentials, MCP tokens, private keys, cookies, or account-specific identifiers.
- Keep external source and tool access behind a clear MCP boundary.
- Prefer source-backed behavior over opaque summaries. News explanations should retain enough source metadata for traceability.
- Keep preference and signal storage durable, structured, and reviewable.
- Record assumptions, blockers, and meaningful scope changes in `PROGRESS.md`.
- Record architecture or product decisions in `DECISIONS.md`.

## Intended App Shape

XTtape is a professional ambient-awareness app, not a doomscrolling feed. Design decisions should optimize for:

- high-signal awareness,
- low interruption,
- source-backed explanations,
- user-tuned relevance,
- durable preference and signal learning,
- clear boundaries around external tools and credentials.

## Preferred Technical Direction

- Backend: FastAPI as the core application/API layer.
- Services: Node/TypeScript only where it is useful for feed workers, MCP clients, streaming adapters, or ecosystem-specific integrations.
- Persistence: Prisma for structured durable storage.
- Integrations: MCP boundary for external source/tool access.
- X/xAI: integrate only when credentials and account access are available.

## Verification Expectations

Before claiming implementation readiness, verify:

- source/feed integration plan is credential-aware,
- storage model accounts for source metadata, summaries, preferences, and learned signals,
- privacy and data-retention risks are documented,
- no secrets are committed or displayed,
- app scope still matches `GOAL.md`.
