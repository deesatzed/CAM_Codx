# XTtape Project-Brain Comparison Summary

## Verdict

Use `runs/cam_recall` as the implementation contract, then merge in the incumbent first-proof-screen goals before app scaffolding.

The vanilla run is competent but generic. The first implicit CAM run did not use the mined CAM database, so it is not a valid CAM value proof. The corrected `cam_recall` run is the useful showpiece result because it applies mined methodology from the booster corpus and records exactly what changed in `CAM_MEMORY_APPLIED.md`.

## Final Merged Output

The merged build brain now exists at `runs/final`:

- `runs/final/AGENTS.md`
- `runs/final/GOAL.md`
- `runs/final/DECISIONS.md`
- `runs/final/PROGRESS.md`
- `runs/final/CAM_MEMORY_APPLIED.md`

The first implementation plan now exists at `docs/plans/2026-06-25-xttape-live-ai-news-ticker.md`.

## Artifacts Compared

| Run | Path | Notes |
|---|---|---|
| Vanilla | `runs/vanilla` | Same initial request, no CAM context. Produced 4 files. |
| Implicit CAM | `runs/cam` | Used general CAM/Codex habits but explicitly says no CAM database/source corpus was used. Keep as a teaching artifact, not the main comparison. |
| CAM Recall | `runs/cam_recall` | Same product request plus explicit `CAM_CONTEXT_PACKET.md`. Produced 5 files including CAM memory disclosure. |
| Incumbent | `runs/incumbent` | Prior human-guided XTtape brain. Strongest for showpiece proof-screen and Grok/X stance. |

## Evidence

- `evidence/cam-stats.json.txt`: primary brain has `2315` methodologies, `sibling_count=1`, DB path `/Volumes/WS4TB/ccxt/data/claw.db`.
- `evidence/mining-outcomes.tsv`: booster mining analyzed five repos and logged `42` findings.
- `evidence/primary-new-methodologies.tsv`: primary brain retained `ai-twitter-bot=8`, `xmcp=3`.
- `evidence/typescript-new-methodologies.tsv`: TypeScript ganglion retained `RSSHub=12`, `chatbot=9`, `prisma-next=10`.
- `showpiece/CAM_CONTEXT_PACKET.md`: exact recalled methodology packet used by the corrected CAM run.

## Rubric Scores

Scored 0-3 per category from `COMPARE_RUBRIC.md`.

| Category | Vanilla | CAM Recall | Incumbent |
|---|---:|---:|---:|
| Live-first architecture | 2 | 3 | 3 |
| MCP/source boundary safety | 2 | 3 | 3 |
| Learning system | 2 | 3 | 2 |
| News quality and trust | 2 | 3 | 2 |
| Data model and persistence | 2 | 3 | 2 |
| AI workflow realism | 2 | 3 | 3 |
| Build readiness | 2 | 3 | 2 |
| Showpiece clarity | 1 | 3 | 3 |
| Total | 15 | 24 | 20 |

## What CAM Recall Added Over Vanilla

- Source adapter inventory, scopes, allowlists, and credential status.
- Idempotent ingestion, deduplication, dry-run, and replay as first-phase contracts.
- Source receipts for every summary, ranking, explanation, and user-facing claim.
- Confidence, freshness, and time-decay fields in the first data model.
- Capability-aware AI provider routing with graceful degradation.
- User-learning reset and retention controls.
- Tests for duplicate ingestion, concurrent fetches, stale sources, provider fallback, and tool approval.
- Clear prohibition on write-capable X/social actions until approval flow and idempotent persistence exist.

## What The Incumbent Still Contributes

- Browser-first showpiece stance.
- Grok/xAI as first AI provider.
- Custom narrow read-only X MCP.
- First proof screen:
  - one official/RSS item,
  - one X/social signal,
  - one Grok-generated cluster, summary, or why-shown label,
  - one visible learning action.

## Recommended Next Step

Execute the saved implementation plan from `docs/plans/2026-06-25-xttape-live-ai-news-ticker.md`.

The target app root is `/Volumes/WS4TB/ccxt/XTtape-app`. The first build should copy `runs/final` into that app root, scaffold the local app, and stop only after the first proof screen and evidence artifacts exist.

## Showpiece Story

The best video/story arc is:

1. Start with copied CAM cockpit and clean initial request.
2. Mine five relevant repos.
3. Show the first CAM attempt was not enough because it did not actually use the mined corpus.
4. Run explicit CAM recall and show `CAM_MEMORY_APPLIED.md`.
5. Compare vanilla vs CAM recall.
6. Proceed with the merged project brain only after the evidence shows the difference.
