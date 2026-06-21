# Canonical CAM Repos

Verified on 2026-06-21.

| Path | Classification | Remote | Branch/state | Role |
|---|---|---|---|---|
| `/Volumes/WS4TB/repo622sn/CAM_Codx` | canonical repo | `https://github.com/deesatzed/CAM_Codx.git` | `main...origin/main` | Codex-native workflow hub. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM` | runtime repo | `https://github.com/deesatzed/CAM_CAM.git` | `main...origin/main`, untracked `CAM_Codx_last5291pm.txt` | CAM runtime/base engine used by current showpieces. |
| `/Volumes/WS4TB/WS4TBr/MoriahCareFrame` | generated product repo | `https://github.com/deesatzed/moriahcareframe.git` | `main...origin/main` | Standalone generated product proof. |
| `/Volumes/WS4TB/repo622sn/CAM_CAM` | clean clone / keep | `https://github.com/deesatzed/CAM_CAM.git` | `main...origin/main` | Alternate clean clone of runtime repo. |
| `/Volumes/WS4TB/repo622sn/moriahcareframe` | clean clone / keep | `https://github.com/deesatzed/moriahcareframe.git` | `main...origin/main` | Alternate clean clone of generated product. |
| `/Volumes/WS4TB/CAM_ALL/repos/CAM_Codx` | clean operating clone | `https://github.com/deesatzed/CAM_Codx.git` | fresh clone | Local overlay clone for clean operations. |
| `/Volumes/WS4TB/CAM_ALL/repos/CAM_CAM` | clean operating clone | `https://github.com/deesatzed/CAM_CAM.git` | fresh clone | Local overlay clone for clean operations. |
| `/Volumes/WS4TB/CAM_ALL/repos/moriahcareframe` | clean operating clone | `https://github.com/deesatzed/moriahcareframe.git` | fresh clone | Local overlay clone for clean operations. |

## Confusing Or Duplicate Folders

| Path | Classification | Reason |
|---|---|---|
| `/Volumes/WS4TB/WS4TBr/CAM_Codx` | workspace container | Contains CAM_CAM, Codex config, and child repos; not the canonical CAM_Codx hub checkout for this goal. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology` | old implementation branch/worktree | Dirty/ahead implementation surface; not the clean hub repo. |
| `/Volumes/WS4TB/CAM_grok_build/CAM_Codx` | adapter/build workspace | Grok build workspace; needs review before any cleanup. |
| `/Volumes/WS4TB/camcxBU64` | old backup/duplicate | Backup-style CAM workspace; needs review before any cleanup. |
| `/Volumes/WS4TB/CAM_Locl` | local runtime workspace | Local-only CAM area; do not touch without a separate local-state decision. |
| `/Volumes/WS4TB/CAM_Codx` | old duplicate | Has same remote as CAM_Codx, but this goal runs from `/Volumes/WS4TB/repo622sn/CAM_Codx`. |
| `/Volumes/WS4TB/careframe` | related but separate product family | Not MoriahCareFrame; do not merge into CAM_Codx. |

No folder was deleted, moved, renamed, or archived during this inventory.
