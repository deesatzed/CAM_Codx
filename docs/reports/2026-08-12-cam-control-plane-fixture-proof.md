# CAM_Codx Control-Plane Fixture Proof

Date: 2026-08-16

## Scope

This is deterministic fixture proof only. It uses CAM_CAM's real in-memory
SQLite repository and managed-run service with synthetic source identities,
receipt contents, landing metadata, and verification evidence. It makes no
provider call, mining request, corpus write, target edit, model/profile change,
or live configuration change. It is not live-product proof, accuracy evidence,
or real-world acceptance.

## Exercised chain

`tests/test_cam_control_plane_e2e.py` creates a reviewed plan and managed run,
links a SHA-256-verified synthetic mining receipt, records a selected direct
precedent and rejected new hypothesis, links the application packet, records a
simulated landing, records a failed verification outcome, then records a
receipt-backed corrected verified-success outcome that supersedes the failure.

The final source-to-outcome report proves:

- both the selected and rejected candidate decisions remain visible;
- the failed outcome remains historical evidence;
- the corrected verified success is the active slot outcome;
- `positive_evidence_count` is exactly one; and
- recipe eligibility is granted only to the corrected verified result.

## Command and result

```bash
cd /Users/o2satz/Downloads/crash814/worktrees/CAM_Codx
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tests/test_cam_control_plane_e2e.py
```

Result: `1 passed` (the recovery sandbox only declined optional pytest-cache
writes under Downloads).

## Limitations and next boundary

The proof validates cross-repository persistence semantics in an isolated
fixture. A live mining run, provider spend, model/profile change, corpus write,
target mutation, or deployment remains outside this proof and requires its own
explicit authorization and receipt evidence.
