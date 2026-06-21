# Decisions

## 2026-06-21: Keep Hub-And-Spoke Repo Ownership

Decision: keep CAM_Codx, CAM_CAM, generated products, and adapter surfaces as
separate repos/docs surfaces rather than merging them into one monorepo.

Reason: CAM_CAM owns runtime code and local databases; CAM_Codx owns Codex
workflow docs and goal templates; generated products need standalone repo
history and verification. This keeps public onboarding cleaner and limits the
risk of publishing local runtime state.

## 2026-06-21: Use Placeholders For CAM_ALL Local State First

Decision: create `/Volumes/WS4TB/CAM_ALL/local_state` with documented
placeholders instead of copying `CAM_CAM/data/claw.db` in this batch.

Reason: `claw.db` is local runtime state. The goal allows documented
placeholders, and avoiding a second copy reduces risk of stale databases or
accidental publication.

## 2026-06-21: Remove Only Classified Public Artifacts

Decision: remove tracked public files only after listing them in
`docs/repo_inventory/PUBLIC_REPO_CLEANUP_MANIFEST.json` and the local archive
manifest. Retain legacy-looking plans and design records when their current
replacement is not obvious.

Reason: the final cleanup goal requires a cleaner public GitHub state, but the
repo family has useful historical design material. Generated batch outputs,
stale launch reports, and old coverage snapshots are low-risk public removals;
broader plan/history deletion would risk losing context without improving
clone-and-run behavior.
