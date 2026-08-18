# Task 14 Source Preflight

Date: 2026-08-18

This is a read-only identity and license preflight for the authorized
MatrAIx/SESA Task 14 sources. It does not execute project code, call a
provider, modify either source repository, modify CAM state, or authorize a
live import or target mutation.

## Canonical CAM roots

| Role | Path | State |
|---|---|---|
| CAM_Codx | `/Volumes/WS4TB/waswiki/CAM_Codx` | consolidated `main`, clean, pushed |
| CAM_CAM | `/Volumes/WS4TB/waswiki/CAM_CAM` | consolidated `main`, clean, pushed |
| CAM database | `/Volumes/WS4TB/waswiki/CAM_CAM/claw.db` | one existing local database; untouched |
| CAM config | `/Volumes/WS4TB/waswiki/CAM_CAM/claw.toml` | one existing tracked config; untouched |
| CAM secrets | `/Volumes/WS4TB/waswiki/CAM_CAM/.env` | one existing mode-0600 file; untouched |

The Downloads worktrees are recovery references only and are not a second CAM
runtime or state location.

## Source identities

| Source | Checkout | Remote | Branch/revision | Working tree | License evidence | Decision |
|---|---|---|---|---|---|---|
| MatrAIx-Persona-8B | `/Volumes/WS4TB/waswiki/repos2mine/repo622sn/MatrAIx-Persona-8B` | `https://github.com/MatrAIx-ai/MatrAIx-Persona-8B.git` | `main` / `3202a0bf6134776735c4ab4d50de79be8c6a5e8b` | clean | root `LICENSE`, MIT, Copyright 2026 MatrAIx | eligible for bounded local adaptation with attribution preserved |
| SESA-Self-Evolving-Search-Agents | `/Volumes/WS4TB/waswiki/repos2mine/repo622sn/SESA-Self-Evolving-Search-Agents` | `https://github.com/Zenghuang-Fu/SESA-Self-Evolving-Search-Agents.git` | `master` / `74de5d77a19774cfba53d6950d47633a2d632430` | clean | no root `LICENSE`; nested Apache-2.0 notices exist in `verl` and other bundled components | source inspection/read-only assessment only; adaptation/redistribution rights unresolved |

## Observed execution boundary

- MatrAIx README advertises a Docker-backed smoke test that does not require
  an API key, plus optional provider/model-backed runs. No smoke or model run
  was started by this preflight.
- SESA README describes a retrieval service, datasets, a training launcher,
  model paths, and a judge model supplied through environment variables. No
  service, training job, dataset download, provider call, or model load was
  started.
- No source `.env`, CAM `.env`, `claw.db`, or live config was copied, swapped,
  printed, or modified.

## Current Task 14 decision

The source paths and immutable revisions are now known. The next permitted
batch is bounded read-only assessment and license/attribution mapping. Before
any SESA code is adapted, copied, or redistributed, the root-repository rights
and the licenses of all selected components must be established. The exact
target writable paths, privacy/data boundary, provider policy, and test/rollback
plan remain to be recorded in the Task 14 product-boundary decision.
