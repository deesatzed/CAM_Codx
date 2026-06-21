# MyLoc Hardening Case Study

MyLoc is the second Repo Necromancer product proof in the CAM repo family. It
shows a different success mode from MoriahCareFrame: not just "CAM created a
repo," but "CAM can evaluate and harden a repo that CAM created."

## What MyLoc Is

MyLoc turns workspace inventory plus code-grafting logic into a local subsystem
transplant desk. It reads captured source evidence, shows a compatibility map,
prints a merge ledger, and produces a safe patch plan before any copy step.

## Source Inputs

- Source A: `/Volumes/WS4TB/repo622sn/skratched`
- Source B: `/Volumes/WS4TB/repo421sn/LocalRecall`
- Generated product repo: `/Volumes/CAMADA/CAM_ALL/repos/MyLoc`

The source repos are evidence only. MyLoc verifies their current git head,
branch, and status receipt against `evidence/source_profiles.json`.

## CAM Dogfood Evidence

| Step | Result |
|---|---|
| `cam evaluate --mode structural` | MyLoc was recognized as a Python git repo with README, tests, and `pyproject.toml`; expectation baseline match score was `1.000`. |
| `cam preflight` | The hardening task was low complexity, medium confidence, and recommended `proceed_now`. |
| `cam camify` | CAM wrote `docs/camify_myloc_plan.md` and `.json` with 10 KB matches and 8 plan steps. |
| `cam mine-self --quick` | CAM classified MyLoc as `cli_ux` with secondary `ai_integration`, `testing`, and `algorithm` signals. |
| `cam security scan` | TruffleHog reported `CLEAN - 0 findings`. |

## Hardened Behavior

MyLoc now exposes:

```bash
python -m my_loc.cli plan --evidence evidence/source_profiles.json --json
python -m my_loc.cli verify-boundaries --evidence evidence/source_profiles.json
sh scripts/smoke.sh
```

The JSON plan gives Codex and CAM a machine-readable compatibility map, merge
ledger, safe patch plan, and contract errors. The boundary verifier fails if
source repo receipts drift from the captured evidence.

## Why This Matters For CAM_Codx

CAM_Codx needs concrete continuation targets, not abstract claims. MyLoc is a
small, inspectable product repo that proves the Repo Necromancer handoff can be
continued through evaluation, planning, hardening, and verification.
