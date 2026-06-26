# PROGRESS.md

## Status

2026-06-25: Final merged project brain created for XTtape. No app code has been written in this final run.

## Source Evidence Used

- `/Volumes/WS4TB/ccxt/showpiece/INITIAL_REQUEST.md`
- `/Volumes/WS4TB/ccxt/showpiece/CAM_CONTEXT_PACKET.md`
- `/Volumes/WS4TB/ccxt/showpiece/COMPARISON_SUMMARY.md`
- `/Volumes/WS4TB/ccxt/showpiece/runs/cam_recall`
- `/Volumes/WS4TB/ccxt/showpiece/runs/incumbent` as design evidence for browser-first proof screen, Grok/xAI first, and custom read-only X MCP stance
- `/Volumes/WS4TB/ccxt/showpiece/evidence`

## Completed

- Compared vanilla, implicit-CAM, explicit-CAM-recall, and incumbent project brains.
- Chose `runs/cam_recall` as the base implementation contract because it actually used the recalled methodology packet.
- Merged in the incumbent's useful showpiece decisions:
  - browser-first first proof screen,
  - Grok/xAI first provider stance,
  - custom narrow read-only X MCP,
  - one-frame proof containing official/RSS, X/social, AI explanation, and learning.
- Preserved CAM-recall requirements:
  - connector inventory,
  - allowlists and read-only defaults,
  - source receipts,
  - idempotent ingestion and replay,
  - confidence, freshness, and time-decay,
  - provider fallback,
  - learning reset, retention, and audit controls.

## Current Blockers

- Real X/social read credentials are not verified.
- xAI/Grok key presence is not verified for the app build.
- Source retention and API terms need confirmation before any production or public-data retention claim.
- Production deployment is out of scope until explicitly approved.

These blockers do not prevent local app scaffolding because replay fixtures and no-provider fallback are required.

## Active Assumptions

- Target app root: `/Volumes/WS4TB/ccxt/XTtape-app`.
- Local SQLite is acceptable for the MVP because Prisma keeps the migration path explicit.
- The app should run without live X or xAI credentials.
- Screenshots should avoid secrets and use replay data if credentials are unavailable.
- The showpiece should document each step for a novice user.

## Next Actions

1. Save the implementation plan under `/Volumes/WS4TB/ccxt/showpiece/docs/plans/2026-06-25-xttape-live-ai-news-ticker.md`.
2. If approved, initialize `/Volumes/WS4TB/ccxt/XTtape-app`.
3. Copy this final project brain into the app repo root.
4. Scaffold the first build slice.
5. Run evidence gates and save screenshots.
