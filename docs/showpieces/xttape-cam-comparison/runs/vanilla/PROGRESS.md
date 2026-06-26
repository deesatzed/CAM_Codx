# PROGRESS.md

## Status

Initial project brain created for XTtape on 2026-06-25.

No app code has been written.

## Source Boundary

Used only the supplied XTtape request.

Not used:

- `XTtapeNotes.md`
- CAM
- `claw.db`
- external memory systems
- credentials or private account data

## Files Created

- `AGENTS.md`
- `GOAL.md`
- `DECISIONS.md`
- `PROGRESS.md`

## Current Understanding

XTtape is a live AI-based news ticker tape for professional ambient awareness. It should combine live news/source feeds, X/social signals where credentials permit, AI summarization, source-backed explanations, user learning, and durable structured storage of preference and signal data.

The preferred stack is FastAPI, selective Node/TypeScript services, Prisma persistence, MCP-bounded external access, and credential-gated X/xAI integration.

## Assumptions

- The MVP should support useful behavior without X/xAI credentials by using credential-free or mockable source/feed pathways.
- Professional users value concise, trusted, inspectable updates more than high-volume engagement.
- Social signals should influence prioritization but should not be treated as verified facts without source support.
- User learning should start with bounded, explainable preference and feedback data rather than opaque personalization.
- Durable storage should be designed before implementation so source provenance and preference history are not bolted on later.

## Risks

- News/source feeds may have licensing, rate-limit, reliability, or terms-of-use constraints.
- X/xAI capabilities may be unavailable without credentials, paid access, or account approval.
- AI summaries can hallucinate or over-compress source nuance unless provenance and explanation rules are built in.
- Ambient awareness can drift toward doomscrolling if volume, priority, and interaction design are not constrained.
- Durable user-learning data creates privacy and retention responsibilities.

## Blockers Before Full Implementation

- Select MVP source/feed targets.
- Decide credential-free development path.
- Define MCP boundary responsibilities.
- Sketch persistence entities and retention expectations.
- Choose AI model/provider strategy and fallback behavior.
- Decide how users inspect, correct, or reset learned preferences.

## Recommended Next Step

Prepare an implementation plan for the MVP before writing code. The plan should define the first vertical slice: source ingestion, persistence, summarization, ticker delivery, source-backed explanation, and minimal user feedback loop.
