# AGENTS.md

## Source Of Truth

Before coding, read these files in this order:

1. GOAL.md
2. DECISIONS.md
3. CAM_MEMORY_APPLIED.md
4. PROGRESS.md
5. docs/plans/2026-06-25-xttape-live-ai-news-ticker.md, if present

Treat these files as the active XTtape build contract. If they conflict, prefer the newer dated decision or progress entry and update the stale file before continuing.

## Product Stance

XTtape is a browser-first live AI news ticker for professional ambient awareness. It is not a generic RSS reader, social feed clone, or doomscrolling surface.

The first proof screen must show all of these together:

- one official or RSS item,
- one X/social signal,
- one Grok/xAI-generated cluster, summary, or why-shown label,
- one visible learning action that writes an audit record.

## CAM_Codx Stance

CAM_Codx guides and documents the build process. XTtape owns the app code, runtime data model, product storage, and user experience.

Use the copied showpiece CAM cockpit for methodology recall and provenance only:

- CAM database: `/Volumes/WS4TB/ccxt/data/claw.db`
- CAM config: `/Volumes/WS4TB/ccxt/claw_xttape.toml`
- TypeScript sibling database: `/Volumes/WS4TB/ccxt/instances/typescript/claw.db`
- Showpiece evidence: `/Volumes/WS4TB/ccxt/showpiece/evidence`

Do not copy CAM database rows into XTtape product storage. Do not copy code from mined repositories unless a later decision records licensing, provenance, and user approval.

## External Source Rules

All external source and tool access must go through a registered connector boundary.

For phase one:

- connectors are read-only by default,
- connector inventory must report source identity, scope, allowlist, credential status, freshness, and failure state,
- source fetches must support dry-run or replay fixtures,
- every summary, ranking, and why-shown explanation must have source receipts,
- X/social write actions are out of scope.

The custom X MCP must be narrow, read-only, and allowlisted. Write-capable tools require a new dated decision, approval flow, idempotent persistence, tests, and explicit user approval before implementation.

## Build Rules

- Prefer small, evidence-gated slices over broad scaffolding.
- Keep the app runnable without live AI or X credentials by using fixtures and fallback summarization.
- Do not expose secrets in logs, screenshots, fixtures, commits, or docs.
- If credentials are missing, implement the no-provider or replay path and document the blocker in PROGRESS.md.
- If a safe assumption can be made, make it, record it in PROGRESS.md, and continue.
- Stop for destructive actions, production deployment, sensitive data risk, legal/compliance uncertainty, paid API uncertainty, or scope-changing product choices.

## Verification Rules

Do not mark a slice complete until the relevant checks pass and evidence is recorded in PROGRESS.md.

Phase-one evidence must include:

- FastAPI health check,
- Prisma schema validation and migration status,
- source adapter inventory output,
- duplicate/replay ingestion test,
- stale/freshness ranking test,
- provider fallback test,
- user learning audit test,
- browser screenshot of the first proof screen,
- no-secret grep before any commit or screenshot publication.
