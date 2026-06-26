# XTtape Live AI News Ticker Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local, browser-first XTtape showpiece that proves a live AI news ticker can combine RSS/official items, X/social signals, Grok/xAI explanation, source receipts, and a learning action in one screenshot-ready app.

**Architecture:** Monorepo at `/Volumes/WS4TB/ccxt/XTtape-app` with FastAPI API, React/Vite UI, Prisma persistence, TypeScript shared contracts, and a narrow read-only source/X MCP connector package. Local SQLite is the MVP database; replay fixtures keep the app runnable without live credentials.

**Tech Stack:** FastAPI, Python pytest, React, Vite, TypeScript, Node, Prisma, SQLite, MCP, optional Grok/xAI provider, Playwright for browser evidence.

---

## Source Contract

Before implementation, copy the final build brain from:

- `/Volumes/WS4TB/ccxt/showpiece/runs/final/AGENTS.md`
- `/Volumes/WS4TB/ccxt/showpiece/runs/final/GOAL.md`
- `/Volumes/WS4TB/ccxt/showpiece/runs/final/DECISIONS.md`
- `/Volumes/WS4TB/ccxt/showpiece/runs/final/PROGRESS.md`
- `/Volumes/WS4TB/ccxt/showpiece/runs/final/CAM_MEMORY_APPLIED.md`

Do not use legacy loose notes as source material. Do not copy mined repo code.

## Phase 1: Initialize The App Repo

Create `/Volumes/WS4TB/ccxt/XTtape-app` as a fresh git repo with:

- `apps/api`
- `apps/web`
- `packages/db`
- `packages/shared`
- `packages/source-mcp`
- `fixtures`
- `docs/screenshots`
- `docs/evidence`

Acceptance:

- `git status` shows a new repo with only intentional files.
- Root truth files are copied from `showpiece/runs/final`.
- `.gitignore` excludes `.env`, SQLite runtime files, node modules, Python caches, and screenshots that contain secrets.

## Phase 2: FastAPI Control Plane

Implement `apps/api` with:

- `GET /health`
- `GET /api/ticker`
- `POST /api/ingest/replay`
- `POST /api/learning/signal`
- `GET /api/connectors`

Acceptance:

- `pytest` passes for health and response contracts.
- `/api/ticker` works with fixture data before live connectors exist.
- API responses include receipt references, freshness, confidence, and why-shown fields.

## Phase 3: Prisma Data Model

Implement `packages/db/prisma/schema.prisma` with SQLite and models for:

- `SourceAdapter`
- `ConnectorInventory`
- `SourceObservation`
- `SourceReceipt`
- `SignalEvent`
- `Summary`
- `RankingDecision`
- `UserSignal`
- `UserPreference`
- `LearningAudit`
- `RetentionAudit`

Acceptance:

- `npx prisma validate` passes.
- Initial migration applies locally.
- Seed or fixture load creates one official/RSS observation and one X/social observation.

## Phase 4: Shared Contracts

Implement `packages/shared` TypeScript types for:

- connector inventory,
- source observation,
- ticker item,
- source receipt,
- summary/explanation,
- learning signal,
- provider status.

Acceptance:

- TypeScript build passes.
- API and UI use the same ticker item contract, or a generated OpenAPI client is documented if used instead.

## Phase 5: Source Adapter And Replay Pipeline

Implement the source adapter interface with:

- deterministic source identity,
- deduplication key,
- source type,
- source timestamp,
- fetch timestamp,
- freshness score input,
- confidence score input,
- receipt payload,
- replay fixture loader.

Acceptance:

- Running replay twice does not duplicate `SignalEvent` records.
- A stale fixture ranks lower or carries a stale warning.
- Raw observations remain linked to receipts.

## Phase 6: Narrow Read-Only Source/X MCP

Implement `packages/source-mcp` as a local MCP-style connector package with:

- connector inventory,
- allowlist configuration,
- credential status reporting,
- read-only source fetch contract,
- disabled write-tool placeholder with explicit refusal.

Acceptance:

- Smoke test prints connector inventory without secrets.
- Test proves write actions are unavailable.
- Missing X credentials produce a degraded status, not a crash.

## Phase 7: AI Provider And Fallback

Implement an AI provider boundary with:

- Grok/xAI provider selected when `XAI_API_KEY` is present,
- provider capability/status check,
- no-provider fallback that creates a labeled deterministic explanation from receipts,
- no secrets in logs.

Acceptance:

- Test passes with no `XAI_API_KEY`.
- If `XAI_API_KEY` exists, provider status reports configured without printing the key.
- Ticker item always has either an AI summary or a fallback explanation.

## Phase 8: Browser First Proof Screen

Implement `apps/web` with a calm, dense ticker UI showing:

- official/RSS item,
- X/social signal,
- source-backed summary or why-shown label,
- source receipts,
- freshness/confidence indicator,
- visible learning action.

Acceptance:

- `npm run build` passes for the web app.
- Local browser screenshot shows all first proof screen requirements in one frame.
- UI runs against replay data when live credentials are missing.

## Phase 9: Learning Action

Implement one learning action such as "more like this" or "less like this" that:

- writes `UserSignal`,
- updates ranking inputs or stored preference state,
- writes `LearningAudit`,
- exposes reset behavior.

Acceptance:

- Test proves the action writes both signal and audit records.
- Ticker response changes or records a changed ranking input after the signal.
- Reset endpoint or command clears learned preference state and writes audit.

## Phase 10: Evidence And Showpiece Capture

Save evidence under `docs/evidence`:

- health check output,
- connector inventory output,
- Prisma validation output,
- duplicate replay test output,
- provider fallback test output,
- learning audit test output,
- no-secret grep output.

Save screenshots under `docs/screenshots`.

Acceptance:

- `PROGRESS.md` records exact commands and outputs.
- Screenshot contains RSS/official, X/social, Grok/xAI or fallback explanation, and learning action.
- No secrets are visible in docs or screenshots.

## Suggested Command Surface

Expected final commands may look like:

```bash
cd /Volumes/WS4TB/ccxt/XTtape-app
python -m pytest apps/api/tests
npm test
npx prisma validate --schema packages/db/prisma/schema.prisma
npm run build
```

Adjust package manager commands to the actual scaffold selected during Phase 1 and record changes in `DECISIONS.md`.

## Stop Rules

Stop and ask the user before:

- using paid APIs,
- posting or writing to X/social accounts,
- deploying publicly,
- committing credentials,
- deleting existing repos or data,
- changing the product scope away from browser-first live ticker.

## Completion Definition

This plan is complete when a novice can open the local browser app, see the first proof screen, run the documented verification commands, and understand from saved evidence how CAM recall improved the app design.
