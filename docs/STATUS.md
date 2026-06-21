# Status

Verified on 2026-06-21.

## Implemented

- CAM_Codx is documented as the Codex-native workflow hub.
- CAM_CAM remains the runtime/base engine.
- Repo Necromancer packet workflow is documented.
- Codex goal templates exist.
- Claude Code and Grok Build adapter docs/templates exist.
- Local overlay directories exist at `/Volumes/WS4TB/CAM_ALL`.
- Archive staging exists at `/Volumes/WS4TB/CAM_ARCHIVE`.

## Verified Locally

- GitHub remotes for CAM_Codx, CAM_CAM, and moriahcareframe were queried.
- `CAM_CAM/data/claw.db` exists locally and was inspected using metadata-only
  SQLite commands.
- Clean clones were created under `/Volumes/WS4TB/CAM_ALL/repos`.

## Pushed To GitHub

This reorganization batch has not been pushed yet.

## Planned

- Run cross-repo verification.
- Commit and push verified batches.

## Intentionally Out Of Scope

- Deleting, moving, renaming, or archiving old folders.
- Publishing `claw.db`.
- Publishing real API keys or local-only config.
- Merging CAM_CAM, CAM_Codx, and generated products into one monorepo.
