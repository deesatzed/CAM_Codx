# Repo Necromancer Standalone Product Goal

## OUTCOME

Build a standalone product repo from a CAM_CAM Repo Necromancer packet.

## PROOF OF DONE

The task is incomplete unless the standalone repo path exists and contains
runtime code, tests, README, provenance docs, and a smoke command. Do not count
the packet directory as completion.

Required evidence:

- source repos stayed read-only,
- standalone repo has its own git status,
- tests pass,
- smoke command passes,
- README explains what was revived from each source,
- provenance docs cite source paths and commits.

## SCOPE

Allowed:

- read the packet,
- create or modify the standalone repo,
- write product docs and tests.

Not allowed:

- modifying source repos,
- copying secrets,
- claiming packet demos are complete products.

## ITERATION

1. Read `CAM_CODEX_GOAL.md`, `evidence.json`, and showpiece notes.
2. Verify source repo git status.
3. Inspect the standalone repo path.
4. Build the smallest complete product slice.
5. Add tests and smoke command.
6. Record provenance.
7. Verify and report.

## COMPLETE

Complete only when the standalone repo proof is stronger than the packet proof.
