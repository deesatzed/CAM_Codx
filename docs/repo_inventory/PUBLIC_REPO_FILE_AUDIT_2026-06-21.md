# Public Repo File Audit - 2026-06-21

This audit classifies tracked public GitHub files for the final cleanup pass.
It does not authorize deleting, moving, renaming, or archiving local workspace
folders under `/Volumes/WS4TB`.

## Current Heads

| Repo | Head verified before cleanup | Dirty state before cleanup |
|---|---|---|
| `CAM_Codx` | pre-cleanup `23ad6e555127dc2856eec5070c91f2c09c04b238`; proofed pushed head `ef1e20f14870bfcc55d0a508e06b1726e6f02e8f`; exact containing commit is verified with `git rev-parse HEAD` | clean after final proof/status commits |
| `CAM_CAM` | pre-cleanup `c9110447abff2047a8c4df7021679a0847fb151e`; current pushed `9a9d71ade8f6766c8fb564051b2baa308d9abfd1` | untracked `CAM_Codx_last5291pm.txt` |
| `moriahcareframe` | `a82e42cedd2f70479d44f92bd2dcab7277f86168` | clean |

## Removed From Public Git Tracking

These files are classified as low-risk public removals because they are
generated outputs, stale launch snapshots, or old local measurement artifacts.
Archive provenance is recorded in
`/Volumes/WS4TB/CAM_ARCHIVE/2026-06-21-public-cleanup/MANIFEST.json`.

| Repo | Path | Classification | Replacement or current source |
|---|---|---|---|
| `CAM_CAM` | `batch_run/results/batch_results.json` | generated output | Re-run batch tooling locally when needed; do not use as public onboarding proof. |
| `CAM_CAM` | `batch_run/results/batch_summary.json` | generated output | Re-run batch tooling locally when needed; do not use as public onboarding proof. |
| `CAM_CAM` | `coverage-baseline-2026-03-31.txt` | stale coverage snapshot | Current verification should use live tests/CI. |
| `CAM_CAM` | `docs/LAUNCH_METRICS_2026-06-19.md` | stale launch metrics | Current public state is README plus active docs/showpieces. |
| `CAM_CAM` | `docs/reports/CAM_CAM_LAUNCH_AUDIT_2026-06-19.md` | stale launch audit | Current public state is README plus active docs/showpieces. |
| `CAM_CAM` | `docs/reports/CAM_CAM_LAUNCH_REFRESH_2026-06-19.md` | stale launch report | Current public state is README plus active docs/showpieces. |
| `CAM_CAM` | `docs/reports/CAM_CAM_TOP6_FEATURES_2026-06-19.md` | stale enhancement report | Current feature docs live with runtime docs and app README files. |

## Retained Legacy-Looking Files

| Repo | Path or pattern | Reason retained |
|---|---|---|
| `CAM_Codx` | `PRD.md`, `build_specs.md`, `build_to_do_checklist.md`, `_design_approval.md` | Source-of-truth background for why the hub exists; not runtime clutter. |
| `CAM_Codx` | `meta/HANDOFF_2026-05-17.md`, `meta/HANDOFF_LATEST.md` | Historical handoff evidence for the public workflow hub. |
| `CAM_Codx` | `docs/plans/*` | Planning provenance; retained until a broader docs-archive decision is made. |
| `CAM_Codx` | `docs/NEW_USER_AUDIT_2026-06-19.md` | Recent audit evidence that still supports onboarding claims. |
| `CAM_CAM` | `docs/plans/*` | Design and implementation provenance; many plans still explain runtime subsystems. |
| `CAM_CAM` | `docs/CAM_*`, `docs/*SHOWPIECE*`, `docs/showpieces/*` | Public runtime docs and showpiece evidence. |
| `CAM_CAM` | `docs/announcements/*`, `docs/blog/*` | Marketing/history docs retained for now because they do not block clone-and-run proof. |
| `CAM_CAM` | `claw.toml`, `claw_cheap.toml`, `claw_dspro.toml`, `claw_grok.toml`, `.env.example` | Tracked public-safe defaults/examples; private overrides and real `.env` files remain ignored. |
| `moriahcareframe` | `patches/patch_plan.md`, `docs/provenance/source_profiles.json` | Generated product proof artifacts required to explain provenance and smoke behavior. |

## Needs Later Review

- A broader CAM_CAM docs archive could move old plans/blog/announcement files
  into a historical docs area, but that is not required for this low-risk
  cleanup batch.
- Any future removal of runtime docs, plans, or showpieces should be treated as
  a separate manifest-reviewed cleanup.
