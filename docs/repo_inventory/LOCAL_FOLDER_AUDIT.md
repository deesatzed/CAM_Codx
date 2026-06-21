# Local Folder Audit

This audit is non-destructive. It records evidence for cleanup planning but
does not move or delete any folder.

## Commands

```bash
find /Volumes/WS4TB -maxdepth 4 -type d -name .git 2>/dev/null | sed 's#/.git$##' | sort
git ls-remote --heads https://github.com/deesatzed/CAM_Codx.git
git ls-remote --heads https://github.com/deesatzed/CAM_CAM.git
git ls-remote --heads https://github.com/deesatzed/moriahcareframe.git
find /Volumes/WS4TB -maxdepth 5 -type d \( -iname '*CAM*' -o -iname '*moriah*' -o -iname '*careframe*' \) 2>/dev/null | sort
```

## Remote Heads

```text
CAM_Codx main: 23ad6e555127dc2856eec5070c91f2c09c04b238
CAM_Codx feature/initial-impl: a159d20f017bdcc2f79bae6fc21bb0e5eb17552a
CAM_CAM main: 9a9d71ade8f6766c8fb564051b2baa308d9abfd1
moriahcareframe main: a82e42cedd2f70479d44f92bd2dcab7277f86168
```

`d5df0a5` and `40ba9f1` are historical pre-reorganization heads from the first
audit pass. `c911044` is the pre-cleanup CAM_CAM head retained in the archive
manifest as the source commit for removed tracked files.

## Observations

- `/Volumes/WS4TB/repo622sn/CAM_Codx` is the Git-backed hub checkout for this
  goal.
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM` is the runtime checkout named in
  the goal and contains the Repo Necromancer showpieces.
- `/Volumes/WS4TB/WS4TBr/MoriahCareFrame` is the generated product checkout.
- `/Volumes/WS4TB/WS4TBr/CAM_Codx` is a workspace/container folder, not the
  canonical hub checkout for this goal.
- Many other local folders contain `CAM`, `moriah`, or `careframe` in their
  names. They require review before cleanup because names alone are not enough
  evidence to delete or archive them.

## Cleanup Rule

Local folder cleanup is only planned in `RETIREMENT_MANIFEST.json`. No local
folder was deleted, moved, renamed, or archived. Tracked public GitHub file
cleanup is governed separately by `PUBLIC_REPO_CLEANUP_MANIFEST.json`.
