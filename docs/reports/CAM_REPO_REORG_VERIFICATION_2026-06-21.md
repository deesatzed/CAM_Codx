# CAM Repo Reorganization Verification - 2026-06-21

## Summary

This report records the verification pass for reorganizing the CAM repo family
around a hub-and-spoke model:

- `CAM_Codx`: Codex-native workflow hub.
- `CAM_CAM`: runtime/base engine.
- `moriahcareframe`: generated standalone product repo.
- `CAM_ALL`: local clean operating overlay.
- `CAM_ARCHIVE`: non-destructive archive staging area.

No old folders were deleted, moved, renamed, or archived.

## Repos Touched

| Repo | Path | Remote | Commit |
|---|---|---|---|
| CAM_Codx | `/Volumes/WS4TB/repo622sn/CAM_Codx` | `https://github.com/deesatzed/CAM_Codx.git` | `23ad6e5 docs: update CAM reorg push status` |
| CAM_CAM | `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM` | `https://github.com/deesatzed/CAM_CAM.git` | `9a9d71a chore: remove stale public cleanup artifacts` |
| MoriahCareFrame | `/Volumes/WS4TB/WS4TBr/MoriahCareFrame` | `https://github.com/deesatzed/moriahcareframe.git` | no changes, verified at `a82e42c` |

This report is added after the two implementation commits.

## Local Overlay

- `CAM_ALL`: `/Volumes/WS4TB/CAM_ALL`
- `CAM_ARCHIVE`: `/Volumes/WS4TB/CAM_ARCHIVE`

Created local files:

- `/Volumes/WS4TB/CAM_ALL/README_LOCAL.md`
- `/Volumes/WS4TB/CAM_ALL/MANIFEST.json`
- `/Volumes/WS4TB/CAM_ALL/repos/CAM_Codx`
- `/Volumes/WS4TB/CAM_ALL/repos/CAM_CAM`
- `/Volumes/WS4TB/CAM_ALL/repos/moriahcareframe`
- `/Volumes/WS4TB/CAM_ALL/local_state/CAM_CAM/data/claw.db.placeholder.md`
- `/Volumes/WS4TB/CAM_ALL/local_state/CAM_CAM/config/*.placeholder`
- `/Volumes/WS4TB/CAM_ALL/local_state/CAM_CAM/env/.env.placeholder`
- `/Volumes/WS4TB/CAM_ALL/local_state/CAM_Codx/config/codex.local.toml.placeholder`
- `/Volumes/WS4TB/CAM_ALL/local_state/adapters/README.md`
- `/Volumes/WS4TB/CAM_ALL/scripts/verify-all.sh`
- `/Volumes/WS4TB/CAM_ALL/scripts/check-config-drift.sh`
- `/Volumes/WS4TB/CAM_ARCHIVE/README.md`
- `/Volumes/WS4TB/CAM_ARCHIVE/2026-06-21-pre-cleanup/MANIFEST.json`

`CAM_ALL/local_state` uses placeholders instead of copying `claw.db`.

## Local-Only Config And Database Files

Intentionally not committed:

- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db`
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/clawBU.db` if retained locally
- local `.env` files
- local Codex/Claude/Grok adapter configs containing machine paths or keys

`CAM_CAM/claw.toml`, `CAM_CAM/claw_cheap.toml`,
`CAM_CAM/claw_dspro.toml`, `CAM_CAM/claw_grok.toml`, and
`CAM_CAM/.env.example` are tracked public-safe defaults/examples. Private
overrides, secrets, and local database files remain local-only. Public templates
were added under `templates/config/`.

## Commands Run

### Repo And Remote Verification

```bash
git status --short --branch
git remote -v
git ls-remote --heads https://github.com/deesatzed/CAM_Codx.git
git ls-remote --heads https://github.com/deesatzed/CAM_CAM.git
git ls-remote --heads https://github.com/deesatzed/moriahcareframe.git
```

Results:

- CAM_Codx remote head before the first reorganization batch: `d5df0a5` on
  `main`; current verified pushed head before final cleanup is `23ad6e5`.
- CAM_CAM remote head before the first reorganization batch: `40ba9f1` on
  `main`; pre-cleanup hub-linked head was `c911044`; current verified pushed
  head after public cleanup is `9a9d71a`.
- moriahcareframe remote head: `a82e42c` on `main`.

### Inventory

```bash
find /Volumes/WS4TB -maxdepth 4 -type d -name .git 2>/dev/null | sed 's#/.git$##' | sort
find /Volumes/WS4TB -maxdepth 5 -type d \( -iname '*CAM*' -o -iname '*moriah*' -o -iname '*careframe*' \) 2>/dev/null | sort
```

Results were summarized in:

- `docs/repo_inventory/CANONICAL_REPOS.md`
- `docs/repo_inventory/LOCAL_FOLDER_AUDIT.md`
- `docs/repo_inventory/RETIREMENT_MANIFEST.json`

### Config And Database Metadata

```bash
ls -lh /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw.toml \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw_cheap.toml \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw_grok.toml \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/.env.example
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db '.tables'
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db \
  "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 30;"
```

Results:

- `claw.db` exists locally and is 109 MB.
- Metadata-only table inspection succeeded.
- The DB was not copied into CAM_Codx or GitHub.

### CAM_Codx Verification

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
python -m json.tool docs/repo_inventory/RETIREMENT_MANIFEST.json >/dev/null
python - <<'PY'
import tomllib
from pathlib import Path
for path in Path("templates/config").glob("*.toml"):
    tomllib.loads(path.read_text())
    print(f"ok {path}")
PY
grep -R "Do not count" templates/goals
grep -R "runtime code, tests, README, provenance docs" templates/goals
grep -R "source repo" docs/integrations/CLAUDE_CODE.md templates/claude-code
grep -R "read-only" docs/integrations/CLAUDE_CODE.md templates/claude-code
grep -R "standalone repo" docs/integrations/GROK_BUILD.md templates/grok-build
grep -R "packet" docs/integrations/GROK_BUILD.md templates/grok-build
git diff --check
find docs templates -type f | sort
grep -R "CAM_Codx" README.md docs templates
grep -R "CAM_CAM" README.md docs templates
grep -R "Claude Code" README.md docs templates
grep -R "Grok Build" README.md docs templates
```

Result: passed. The secret-pattern scan only matched documented grep commands
containing `sk-`, `xai-`, and `AIza`; no real keys were found in templates/docs.

### CAM_CAM Verification

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
python -m pytest -q tests/test_repo_necromancer.py
git diff --check
```

Result: `6 passed`.

### MoriahCareFrame Verification

```bash
cd /Volumes/WS4TB/WS4TBr/MoriahCareFrame
PYTHONPATH=src python -m pytest -q
sh scripts/smoke.sh
git diff --check
```

Result:

- `5 passed`
- smoke command ran and wrote `patches/patch_plan.md`
- post-smoke git status remained clean

### CAM_ALL Verification

```bash
/Volumes/WS4TB/CAM_ALL/scripts/check-config-drift.sh
/Volumes/WS4TB/CAM_ALL/scripts/verify-all.sh
```

Result:

- TOML parsing succeeded.
- Clean clone status checks succeeded for CAM_Codx, CAM_CAM, and
  moriahcareframe.

## Remaining Dirty Files

Historical state before the first final-report commit:

- CAM_Codx: this report is uncommitted until the final report commit.
- CAM_CAM: pre-existing untracked `CAM_Codx_last5291pm.txt` remains untouched.
- MoriahCareFrame: clean.

Current final public cleanup state is recorded in
`docs/reports/CAM_PUBLIC_REPO_DONE_FOREVER_2026-06-21.md`.

## Cleanup Recommendations

1. Review `docs/repo_inventory/RETIREMENT_MANIFEST.json` before any cleanup.
2. Do not archive or delete workspace/container folders until the user approves
   exact manifest entries.
3. Keep `CAM_ALL` as the clean operating overlay for clone-and-run checks.
4. Keep `CAM_ARCHIVE` empty except for manifests until cleanup is approved.
5. Treat all local databases, env files, and adapter configs as local-only.

## GitHub URLs

- `https://github.com/deesatzed/CAM_Codx`
- `https://github.com/deesatzed/CAM_CAM`
- `https://github.com/deesatzed/moriahcareframe`

## Destructive Cleanup Status

No destructive cleanup was performed.
