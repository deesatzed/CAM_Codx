# XTtape CAM vs Vanilla Runbook

## Purpose

This folder runs a controlled comparison for the XTtape showpiece.

The question is not "can Codex make Markdown files?" The question is whether a CAM cockpit, pre-mined with relevant repo methodology, creates a better project brain than vanilla Codex from the same initial request.

## Current Evidence

- Primary CAM DB: `/Volumes/WS4TB/ccxt/data/claw.db`
- Primary methodology count: `2315`
- TypeScript ganglion DB: `/Volumes/WS4TB/ccxt/instances/typescript/claw.db`
- TypeScript methodology count: `31`
- Booster mining run: five repos, `42` findings
- Local CAM config for comparison: `/Volumes/WS4TB/ccxt/claw_xttape.toml`

## Booster Corpus

- `xdevplatform/xmcp`: X MCP structure, OpenAPI tool surface, allowlist safety.
- `ThePhoenix77/ai-twitter-bot`: news fetch, summarize, score, dedupe, persist pipeline.
- `prisma/prisma-next`: agent-readable data contracts and Prisma-adjacent design patterns.
- `vercel/chatbot`: AI provider abstraction, persistence, tool call UX, model routing.
- `DIYgod/RSSHub`: source/feed normalization and route-scale content ingestion patterns.

## Run Order

1. Freeze evidence from CAM mining.
2. Run vanilla Codex from `INITIAL_REQUEST.md`.
3. Run CAM Codex from the exact same `INITIAL_REQUEST.md`.
4. Copy the existing incumbent XTtape files into `runs/incumbent`.
5. Compare all three outputs with `COMPARE_RUBRIC.md`.
6. Decide whether to proceed to app implementation.

## Evidence Commands

Run these from `/Volumes/WS4TB/ccxt`:

```bash
export CLAW_DB_PATH=/Volumes/WS4TB/ccxt/data/claw.db

cam stats --json -c /Volumes/WS4TB/ccxt/claw_xttape.toml \
  > /Volumes/WS4TB/ccxt/showpiece/evidence/cam-stats.json

sqlite3 /Volumes/WS4TB/ccxt/data/claw.db \
  "SELECT repo_name, findings_count, tokens_used, duration_seconds, created_at FROM mining_outcomes WHERE created_at >= '2026-06-25T13:50:00Z' ORDER BY created_at;" \
  > /Volumes/WS4TB/ccxt/showpiece/evidence/mining-outcomes.tsv

sqlite3 /Volumes/WS4TB/ccxt/instances/typescript/claw.db \
  "SELECT COUNT(*) FROM methodologies; SELECT substr(tags,1,80), COUNT(*) FROM methodologies GROUP BY substr(tags,1,80) ORDER BY COUNT(*) DESC;" \
  > /Volumes/WS4TB/ccxt/showpiece/evidence/typescript-ganglion-counts.tsv
```

## Vanilla Run

Run vanilla in an empty folder with no CAM environment variables:

```bash
cd /Volumes/WS4TB/ccxt/showpiece/runs/vanilla
unset CLAW_DB_PATH
codex exec --cd . --sandbox workspace-write "$(cat /Volumes/WS4TB/ccxt/showpiece/prompts/VANILLA_PROMPT.md)"
```

## CAM Run

Run CAM in an empty folder with the self-contained CAM cockpit available:

```bash
cd /Volumes/WS4TB/ccxt/showpiece/runs/cam
export CLAW_DB_PATH=/Volumes/WS4TB/ccxt/data/claw.db
export CLAW_CONFIG=/Volumes/WS4TB/ccxt/claw_xttape.toml
codex exec --cd . --add-dir /Volumes/WS4TB/ccxt --sandbox workspace-write "$(cat /Volumes/WS4TB/ccxt/showpiece/prompts/CAM_PROMPT.md)"
```

## Incumbent Reference

Copy the existing human-guided reference files:

```bash
cp /Volumes/WS4TB/repo622sn/XTtape/AGENTS.md /Volumes/WS4TB/ccxt/showpiece/runs/incumbent/
cp /Volumes/WS4TB/repo622sn/XTtape/GOAL.md /Volumes/WS4TB/ccxt/showpiece/runs/incumbent/
cp /Volumes/WS4TB/repo622sn/XTtape/DECISIONS.md /Volumes/WS4TB/ccxt/showpiece/runs/incumbent/
cp /Volumes/WS4TB/repo622sn/XTtape/PROGRESS.md /Volumes/WS4TB/ccxt/showpiece/runs/incumbent/
```

## Stop Rule

Do not build XTtape until the comparison shows that one project brain is materially better and the decision is recorded.
