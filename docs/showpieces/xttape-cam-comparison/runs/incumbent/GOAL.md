# XTtape Goal

Build a browser-first live AI news ticker showpiece that blends official/RSS feeds, X/social signals, Grok explanations, and learning actions for a clinician/informaticist faux user.

## Product Stance

XTtape is a live signal layer, not a generic AI RSS reader. It should help a professional user stay aware without doomscrolling by showing source-backed, relevance-ranked items in a calm ticker interface.

## CAM_Codx Stance

CAM_Codx guides and documents the build. XTtape owns the app code, product data model, runtime storage, and user experience.

Use the existing CAM database and configs for build-process recall, methodology checks, and provenance only:

- CAM database: `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db`
- CAM config template: `/Volumes/WS4TB/repo622sn/CAM_Codx/templates/config/cam-codx.env.example`
- CAM claw template: `/Volumes/WS4TB/repo622sn/CAM_Codx/templates/config/cam-cam-claw.example.toml`

Do not copy CAM database rows into XTtape product storage.

## Acceptance Gate

- Local browser app runs.
- FastAPI health endpoint works.
- Node/Prisma service stores normalized signals and feedback.
- Onboarding creates a starter source bundle.
- Live ticker shows at least one official/RSS item and one X/social item.
- Grok produces a source-backed summary or why-shown explanation.
- A learning action updates ranking and writes an audit record.
- Screenshot artifacts exist.
- No secrets are committed or visible in screenshots.

## First Proof Screen

The first proof screen must show all of these together:

- one official or RSS item,
- one X/social signal,
- one Grok-generated cluster, summary, or why-shown label,
- one visible learning action.
