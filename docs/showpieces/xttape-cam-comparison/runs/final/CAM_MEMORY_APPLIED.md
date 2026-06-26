# CAM_MEMORY_APPLIED.md

## Purpose

This file records how CAM-derived methodology changed the final XTtape build brain. It exists so the showpiece can demonstrate the difference between a generic Codex plan and a CAM-recall-guided plan.

## CAM Evidence Used

- `showpiece/CAM_CONTEXT_PACKET.md`
- `showpiece/evidence/cam-stats.json.txt`
- `showpiece/evidence/mining-outcomes.tsv`
- `showpiece/evidence/primary-new-methodologies.tsv`
- `showpiece/evidence/typescript-new-methodologies.tsv`
- `showpiece/runs/cam_recall/CAM_MEMORY_APPLIED.md`

## What Changed Because Of CAM Recall

The final plan keeps these CAM-recall-derived requirements:

- connector inventory with source identity, scopes, allowlists, and credential status,
- read-only source/tool defaults,
- deterministic source identity and deduplication keys,
- idempotent ingestion with replay and dry-run behavior,
- source receipts for summaries, ranking decisions, and explanations,
- confidence, freshness, and time-decay data in the first schema,
- provider capability detection and no-provider fallback,
- user-learning reset, retention, and audit records,
- tests for duplicate ingestion, stale feeds, provider fallback, and tool approval boundaries.

## What Came From The Incumbent Design Evidence

The final plan imports these product-facing choices from the prior XTtape brain:

- browser-first showpiece stance,
- Grok/xAI as the first live AI provider where configured,
- custom narrow read-only X MCP,
- first proof screen containing official/RSS, X/social, AI explanation, and learning action together.

## What Was Not Used

- No CAM database rows are copied into XTtape runtime storage.
- No code is copied from mined repositories.
- No secrets or credentials are included here.
- The legacy loose-notes file is excluded from this clean comparison experiment.
