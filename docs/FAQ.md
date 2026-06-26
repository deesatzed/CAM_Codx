# FAQ

## What is this?

CAM_Codx is the Codex-native workflow hub for CAM. It contains goals,
templates, onboarding docs, and adapter guidance for using CAM outputs from
Codex.

## Why are there multiple CAM repos?

The repos have different jobs. CAM_CAM is the runtime engine. CAM_Codx is the
Codex workflow hub. Generated product repos are standalone outputs.

## Why not one monorepo?

The current evidence favors separate ownership: runtime code and local
databases stay in CAM_CAM, public Codex workflows stay in CAM_Codx, and
generated products keep their own repo history and tests.

## What repo should a Codex user start with?

Start with CAM_Codx.

## What should a new user learn from the XTtape showpiece?

XTtape shows CAM_Codx working as a planning and evidence amplifier before app
code. The experiment compared a vanilla Codex plan with a CAM-recall-guided
plan for a live AI news ticker. The CAM recall run added source receipts,
read-only connector boundaries, replay fixtures, duplicate-ingestion
protection, freshness/confidence scoring, provider fallback, and learning audit
records.

The inference for a new user is practical: do not expect CAM_Codx to magically
make a complete app just because `claw.db` exists. Use CAM_Codx to mine or
recall relevant methods, compare alternatives, write better project truth
files, and only then build.

See `docs/examples/XTTAPE_CAM_SHOWPIECE_CASE_STUDY.md` and
`docs/showpieces/xttape-cam-comparison/`.

## What repo should a runtime contributor start with?

Start with CAM_CAM.

## What is a generated product repo?

It is a separate repo created from CAM/Codex evidence and goals. The packet is
not the product. The product repo needs its own runtime code, tests, README,
provenance, and smoke command.

## Is XTtape a generated product repo?

Not yet. The published XTtape artifact is a showpiece planning bundle and
implementation contract. It contains prompts, comparison evidence, final
project-brain files, and the next build plan. The app runtime should be created
later as a separate product repo from that contract.

## How do Claude Code and Grok Build fit?

They are adapter surfaces. They can consume CAM packets and source receipts,
but they should preserve the same read-only source boundaries and standalone
product proof gates.
