# Repo Necromancer Workflow

Repo Necromancer is a CAM_CAM runtime tool. CAM_Codx documents how Codex should
consume its packets and continue the standalone product build.

## Tested Command Shape

Run this from `CAM_CAM`:

```bash
python scripts/repo_necromancer.py \
  --repo-a /path/to/source-a \
  --repo-b /path/to/source-b \
  --out-dir docs/showpieces/repo_necromancer/my_pair \
  --product-name MyProduct \
  --standalone-repo /path/to/MyProduct \
  --merger-brief "Build a small, inspectable CLI first; show what was borrowed, why, and what is safe to touch next."
```

For longer expectations, use:

```bash
python scripts/repo_necromancer.py \
  --repo-a /path/to/source-a \
  --repo-b /path/to/source-b \
  --out-dir docs/showpieces/repo_necromancer/my_pair \
  --product-name MyProduct \
  --standalone-repo /path/to/MyProduct \
  --merger-brief-file /path/to/merger-brief.md
```

The merger brief travels into `evidence.json`, `NECROMANCER_SHOWPIECE.md`,
`CAM_CODEX_GOAL.md`, and the standalone repo README. Treat it as the user's
product expectation for the Codex continuation step.

## Packet Versus Standalone Repo

The packet directory records evidence: source receipts, synthesis notes,
handoff goals, and demo material. The standalone repo is the generated product.
The `--standalone-repo` argument matters because it proves the workflow can
create a separate repo with its own app code and verification surface.

Do not count `docs/showpieces/repo_necromancer/...` as a finished product repo
unless the goal only asks for a packet.

## Files That Prove Progress

Useful packet evidence includes:

- `CAM_CODEX_GOAL.md`
- `NECROMANCER_SHOWPIECE.md`
- `evidence.json`
- `TEST_RESULTS.md`

Useful standalone product evidence includes:

- app source code,
- tests,
- README,
- provenance or patch docs,
- a smoke command.

## How Codex Continues

1. Read the packet `CAM_CODEX_GOAL.md`.
2. Read the merger guidance and preserve its outcome constraints unless the
   evidence proves a safer narrower scope.
3. Verify the source repos remain read-only unless the goal explicitly allows
   edits.
4. Work in the standalone repo path.
5. Run the product tests and smoke command.
6. Record exact changed files and verification output.
