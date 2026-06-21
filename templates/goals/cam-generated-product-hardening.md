# CAM Generated Product Hardening Goal

## OUTCOME

Take a generated product repo from MVP to a stronger product while preserving
the source evidence and CAM/Codex provenance.

## PROOF OF DONE

- Product repo has passing tests and a smoke command.
- README explains the user value and provenance.
- Source receipts remain intact.
- New code is product-owned, not copied blindly from source repos.
- Git status and changed files are reported.

## SCOPE

Allowed:

- edit the generated product repo,
- improve tests, docs, CLI/API/UI, and packaging,
- add provenance notes.

Not allowed:

- mutate the original source repos,
- erase packet evidence,
- claim production readiness without deployment/security evidence.

## ITERATION

1. Read product README, tests, smoke scripts, and provenance docs.
2. Re-run current verification.
3. Pick the highest-value hardening slice.
4. Implement with focused tests.
5. Update docs and provenance.
6. Verify again.

## COMPLETE

Complete only when the generated repo can stand on its own without requiring a
reader to inspect the original packet.
