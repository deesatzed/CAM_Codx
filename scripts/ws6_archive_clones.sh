#!/usr/bin/env bash
# WS6 — Archive stale CAM clones (GOAL_CAM_HYGIENE.md).
# REVIEW BEFORE RUNNING. Reversible: moves (never deletes) and saves dirty
# diffs to patches first. Requires explicit human go-ahead.
#
# Usage:
#   bash ws6_archive_clones.sh --dry-run   # print actions, change nothing (default)
#   bash ws6_archive_clones.sh --execute   # actually move
set -euo pipefail

MODE="${1:---dry-run}"
ARCHIVE_ROOT="/Volumes/WS4TB/CAM_ARCHIVE"
PATCH_DIR="$ARCHIVE_ROOT/_dirty_patches"

# Clones verified ahead=0 (fully on GitHub) on 2026-06-29. NOT including the
# canonical engine (WS4TBr/CAM_Codx/CAM_CAM), the hub (repo622sn/CAM_Codx),
# or the live-data working dir (repo622sn/CAM_CAM).
CLONES=(
  "/Volumes/WS4TB/repo421sn/CAM_CAM"
  "/Volumes/WS4TB/camcxBU64/CAM_CAM"
  "/Volumes/WS4TB/buccx623/CAM_CAM"
  "/Volumes/WS4TB/buccx623/CAM_Codx"
  "/Volumes/WS4TB/careframe/CAM_Codx"
  "/Volumes/WS4TB/_MyGhRepos/CAM_CAM"
  "/Volumes/WS4TB/ccxt/CAM_Codx"
)

run() { if [ "$MODE" = "--execute" ]; then eval "$1"; else echo "DRY: $1"; fi; }

echo "Mode: $MODE   Archive root: $ARCHIVE_ROOT"
run "mkdir -p '$PATCH_DIR'"

for c in "${CLONES[@]}"; do
  [ -d "$c" ] || { echo "SKIP (missing): $c"; continue; }
  flat=$(echo "${c#/Volumes/}" | tr '/' '_')
  # 1) safety re-check: refuse if the clone has unpushed commits
  ahead=$(cd "$c" && git fetch origin --quiet 2>/dev/null; git log --oneline origin/main..HEAD 2>/dev/null | wc -l | tr -d ' ')
  if [ "$ahead" != "0" ]; then echo "REFUSE (ahead=$ahead, has unpushed work): $c"; continue; fi
  # 2) preserve any dirty state as a patch
  if [ -n "$(cd "$c" && git status --porcelain)" ]; then
    run "(cd '$c' && git diff HEAD > '$PATCH_DIR/${flat}.patch'); (cd '$c' && git status --porcelain > '$PATCH_DIR/${flat}.untracked.txt')"
    echo "  captured dirty state -> $PATCH_DIR/${flat}.patch"
  fi
  # 3) move the clone into the archive
  run "mv '$c' '$ARCHIVE_ROOT/$flat'"
  echo "  archived: $c -> $ARCHIVE_ROOT/$flat"
done

echo "Done ($MODE). Nothing deleted. To reverse: mv back from $ARCHIVE_ROOT."
