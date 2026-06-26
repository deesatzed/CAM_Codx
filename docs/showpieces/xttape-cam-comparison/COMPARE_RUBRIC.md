# XTtape Project-Brain Comparison Rubric

Score each run from 0 to 3 in each category.

0 means absent or actively harmful. 1 means generic. 2 means useful but incomplete. 3 means specific, actionable, and tied to XTtape risk.

## Categories

1. Live-first architecture
   - Does the plan make live ingestion the core loop rather than an afterthought?
   - Does it distinguish polling, streaming, source refresh cadence, and stale data?

2. MCP/source boundary safety
   - Does it isolate external tools and APIs behind source adapters or MCP boundaries?
   - Does it handle read/write tool allowlists, credential boundaries, rate limits, and provenance?

3. Learning system
   - Does it define what the app learns, how consent is handled, and how learned signals improve the ticker?
   - Does it distinguish user preference learning from source credibility learning?

4. News quality and trust
   - Does it include source attribution, duplicate detection, clustering, confidence, time decay, and explainability?

5. Data model and persistence
   - Does it give concrete storage boundaries for sources, events, summaries, user signals, audit trails, and model outputs?
   - Does it fit FastAPI, Node/TypeScript, and Prisma without unnecessary complexity?

6. AI workflow realism
   - Does it include summarization, ranking, entity/topic extraction, source-backed explanations, and fallback behavior?
   - Does it avoid unsupported claims about models or credentials?

7. Build readiness
   - Are the four files enough for another agent to start implementation without guessing?
   - Are assumptions, blockers, tests, and first milestones explicit?

8. Showpiece clarity
   - Would a new CAM_Codx viewer understand why the CAM run is better, worse, or not different?
   - Are evidence and decision points documented clearly?

## Interpretation

- If CAM and vanilla are nearly identical, CAM did not add enough value for this story.
- If CAM is wildly different from vanilla but not clearly better, the experiment is noisy.
- If CAM keeps the same product core but adds concrete source safety, learning loops, auditability, confidence scoring, and implementation gates, proceed with CAM.
- If the incumbent beats both, use the incumbent as the app build source and treat this experiment as a lesson about needing better prompt/run setup.
