# XTtape CAM Showpiece Case Study

XTtape is the current novice-facing CAM_Codx showpiece. It does not claim that
CAM_Codx automatically generated a finished app. It shows a more useful and
more defensible workflow: use CAM_Codx before coding to improve the build
contract.

## What XTtape Is

XTtape is a proposed browser-first live AI news ticker. The target app would
combine official/RSS feeds, X/social signals, Grok/xAI explanations, source
receipts, and learning actions for a professional user.

The published artifact is the planning and evidence bundle, not the runtime
app. The next app build should start from the final project brain and
implementation plan in the showpiece folder.

## What Was Compared

The showpiece compared multiple planning outputs before writing app code:

| Run | Purpose |
|---|---|
| Vanilla | Same initial request, no CAM recall. |
| Implicit CAM | CAM-shaped habits, but no real use of the mined methodology packet. |
| CAM recall | Corrected run that explicitly used the recalled CAM methodology packet. |
| Incumbent | Prior human-guided XTtape direction used only as design evidence. |

The important lesson is that "using CAM" is not enough. The first CAM-shaped
run did not prove much because it did not actually use the recalled corpus. The
corrected CAM recall run was the meaningful comparison.

## What CAM Recall Added

Compared with the vanilla plan, the CAM recall run added requirements that make
the future app more trustworthy and easier to verify:

- source receipts for AI summaries and ranking decisions,
- read-only connector boundaries and allowlists,
- replay fixtures for no-credential testing,
- duplicate-ingestion protection,
- freshness, confidence, and time-decay fields,
- fallback behavior when Grok/xAI is unavailable,
- user-learning reset, retention, and audit records,
- tests for stale sources, duplicate ingestion, provider fallback, and tool
  approval boundaries.

These are not cosmetic features. They are the difference between a generic AI
feed demo and a product plan that can be tested.

## What The Result Proves

XTtape proves that CAM_Codx can help Codex produce a better planning contract
when the workflow is controlled:

1. Freeze the initial request.
2. Generate a vanilla plan.
3. Generate a CAM-recall plan.
4. Compare the outputs with a rubric.
5. Merge the useful parts into final project truth files.
6. Save an implementation plan before app scaffolding.

For a new user, the inference is simple: CAM_Codx is most valuable as a
methodology and evidence layer before implementation. It helps decide what
should be built, what risks must be tested, and what proof is required.

## What The Result Does Not Prove

The showpiece does not prove that:

- XTtape runtime code exists,
- live X/social credentials work,
- Grok/xAI is configured for every user,
- CAM_Codx should copy code from mined repositories,
- merely having `claw.db` makes a plan better.

The value came from selective recall, comparison, and evidence discipline.

## Where To Inspect The Artifacts

- [Comparison summary](../showpieces/xttape-cam-comparison/COMPARISON_SUMMARY.md)
- [Initial request](../showpieces/xttape-cam-comparison/INITIAL_REQUEST.md)
- [CAM context packet](../showpieces/xttape-cam-comparison/CAM_CONTEXT_PACKET.md)
- [Final build brain](../showpieces/xttape-cam-comparison/runs/final/)
- [Implementation plan](../showpieces/xttape-cam-comparison/docs/plans/2026-06-25-xttape-live-ai-news-ticker.md)

## Recommended Next Step

Use the final XTtape build brain as the source of truth for a separate product
repo. The planned app root from the local run was
`/Volumes/WS4TB/ccxt/XTtape-app`, but a new user can choose any clean product
repo path as long as the final truth files and evidence gates are preserved.
