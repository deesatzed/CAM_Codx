# CAM Hub-And-Spoke Architecture

CAM_Codx is the Codex-facing hub for a repo family that should remain split by
ownership:

```text
CAM_CAM runtime engine -> CAM_Codx workflow hub -> generated product repos
                         -> Claude Code adapter
                         -> Grok Build adapter
```

## Ownership Boundaries

`CAM_CAM` owns runtime-heavy behavior: mining, corpus handling, Repo
Necromancer, dashboards, generators, and tests. `CAM_Codx` owns Codex-native
workflows: goal contracts, packet handoffs, onboarding docs, integration
guides, and templates.

Generated products such as `moriahcareframe` remain standalone repos. CAM_Codx
can explain their provenance and provide hardening goals, but it does not store
their app runtime code.

## Why Not A Monorepo

The current evidence favors a hub-and-spoke model:

- runtime code and local databases stay in CAM_CAM,
- Codex users get a clean public front door in CAM_Codx,
- generated products keep their own commit history and verification surface,
- Claude Code and Grok Build can consume the same packet contracts without
  changing core ownership.

CAM_Codx does not vendor, duplicate, or import CAM_CAM internals. It points to
CAM_CAM artifacts by path, GitHub URL, or generated packet contract.

## Runtime State

Local runtime state is not GitHub content. The canonical local CAM database in
this workspace is:

```text
/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db
```

Public templates use placeholders. Local config stays in local-only files or in
the `/Volumes/WS4TB/CAM_ALL/local_state` overlay.
