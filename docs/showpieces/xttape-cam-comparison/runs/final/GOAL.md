# GOAL.md

## Ultimate Goal

Build XTtape, a browser-first live AI news ticker showpiece that blends official/RSS feeds, X/social signals, Grok/xAI explanations, and durable learning actions for a clinician/informaticist faux user.

XTtape should let a professional user glance at a calm ticker and understand what matters, why it matters, which sources support it, and how the system learned their preferences, without opening a chaotic feed.

## Current Phase

Project-brain merge and implementation planning. No XTtape app code has been written in this final run.

## Primary Success Gate

The first implementation is successful when all of these are true:

- local browser app runs,
- FastAPI health endpoint works,
- Node/TypeScript plus Prisma layer stores normalized source signals, summaries, rankings, feedback, and audit records,
- onboarding or seed setup creates a starter source bundle,
- live ticker shows at least one official/RSS item and one X/social signal,
- Grok/xAI produces a source-backed summary, cluster label, or why-shown explanation when configured,
- no-provider fallback produces a clearly labeled non-AI explanation when Grok/xAI is not configured,
- a visible learning action updates ranking inputs and writes an audit record,
- screenshot artifacts exist,
- no secrets are committed or visible in screenshots.

## What CAM Recall Adds

The useful CAM result is not "use claw.db because it exists." The useful result is that recalled methodology changes the app contract in ways a generic prompt could miss:

- source adapters need inventory, scopes, allowlists, deterministic cache keys, and startup reporting,
- ingestion needs idempotency, duplicate filtering, dry-run, and replay from the first slice,
- summaries and rankings need source receipts, confidence, freshness, and time-decay data,
- AI provider routing needs capability detection and graceful degradation,
- learning data needs reset, retention, and audit controls,
- write-capable social actions stay out of scope until approval and idempotency are proven,
- tests must cover duplicate ingestion, concurrent fetches, stale sources, provider fallback, and tool approval boundaries.

## Preferred Stack

- FastAPI for the backend API, orchestration, health checks, ingestion control paths, and ticker delivery.
- React, Vite, and TypeScript for the browser showpiece UI.
- Node/TypeScript where useful for MCP connectors, source adapters, streaming support, and Prisma integration.
- Prisma for structured persistence and migrations.
- SQLite for the local MVP database unless a later decision chooses Postgres.
- Custom narrow read-only X/source MCP for X/social access and connector inventory.
- Grok/xAI as the first live AI provider when credentials are present, with no-provider fallback.

## First Implementation Scope

- Create the app repo under `/Volumes/WS4TB/ccxt/XTtape-app`.
- Copy these final truth files into the app repo root.
- Scaffold FastAPI, React/Vite, Prisma, shared types, and a TypeScript MCP/source connector package.
- Implement source adapter contracts for RSS/official feeds, X/social signals, and replay fixtures.
- Implement idempotent ingestion with receipts, deduplication keys, confidence, freshness, and time-decay inputs.
- Implement AI summary/explanation provider interface with Grok/xAI optional and fallback behavior required.
- Implement a ticker API and browser first proof screen.
- Implement one learning action with durable audit.
- Produce screenshots and verification logs for the showpiece.

## Out Of Scope

- Production deployment.
- Billing, teams, enterprise administration, or monetization.
- Mobile-native apps.
- Social posting or write actions.
- Browser automation as default ingestion.
- Personalization claims without audit records.
- Paid API calls without explicit user approval.
- Copying code from mined repositories.
- Using the legacy loose-notes file as input to this experiment.

## Assumptions

- The first build is local and demo-ready, not production-hosted.
- The app must run in replay/no-provider mode if X or xAI credentials are missing.
- The user will add real API keys to `.env` when ready.
- Source receipt retention is configurable and defaults to local development retention.
- The first persona is a clinician/informaticist because it makes source trust and professional ambient awareness easy to judge.
