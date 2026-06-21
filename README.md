# CAM_Codx

CAM_Codx is the Codex-native command center for CAM: it lets a developer use
CAM_CAM's repo intelligence, provenance, and generators from inside the Codex
workflow they already use.

Start here when you want Codex to consume CAM artifacts, continue from a
generated `CAM_CODEX_GOAL.md`, or harden a standalone product created by CAM.
Use `CAM_CAM` when you are changing the runtime engine, mining corpus, Repo
Necromancer generator, dashboards, or tests.

## What This Is

CAM_Codx is a workflow hub. It owns docs, goal contracts, adapter templates,
case studies, and the clean public explanation for how Codex works with CAM.
It does not vendor CAM_CAM code, copy CAM_CAM databases, or store generated
product runtime code.

The current repo family is organized as a hub-and-spoke system:

```text
CAM_CAM runtime engine -> CAM_Codx workflow hub -> generated product repos
                         -> Claude Code adapter
                         -> Grok Build adapter
```

## Repo Roles

| Repo | Role | Start here when |
|---|---|---|
| `CAM_Codx` | Codex-native workflow hub | You want Codex goals, handoffs, templates, and onboarding. |
| `CAM_CAM` | Runtime/base engine | You are mining repos, running Repo Necromancer, or changing CAM internals. |
| `moriahcareframe` | Generated standalone product | You want to inspect or harden the product repo produced by CAM/Codex. |
| `MyLoc` | Generated product dogfood proof | You want to see CAM evaluate and harden a Repo Necromancer output repo. |

Claude Code and Grok Build are adapter surfaces. They consume CAM packets,
source receipts, and generated goals; they do not change the ownership model.

## Quickstart

Clone the hub and engine side by side:

```bash
git clone https://github.com/deesatzed/CAM_Codx.git
git clone https://github.com/deesatzed/CAM_CAM.git
```

Or use the setup wizard from a cloned `CAM_Codx` checkout:

```bash
python tools/cam_setup_wizard.py
```

Then read:

- [Codex quickstart](docs/QUICKSTART_CODEX.md)
- [New computer setup walkthrough](docs/NEW_COMPUTER_SETUP_WALKTHROUGH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Repo Necromancer workflow](docs/WORKFLOW_REPO_NECROMANCER.md)
- [MoriahCareFrame case study](docs/examples/MORIAH_CAREFRAME_CASE_STUDY.md)
- [MyLoc hardening case study](docs/examples/MYLOC_HARDENING_CASE_STUDY.md)

## Repo Necromancer Example

Repo Necromancer runs from `CAM_CAM` and emits a packet that Codex can continue
from. The tested command shape is:

```bash
python scripts/repo_necromancer.py \
  --repo-a /path/to/source-a \
  --repo-b /path/to/source-b \
  --out-dir docs/showpieces/repo_necromancer/my_pair \
  --product-name MyProduct \
  --standalone-repo /path/to/MyProduct
```

The packet is evidence. The standalone repo is the product. Do not count a
packet directory as completion unless the goal explicitly asks only for a
packet.

The current dogfood proof is MyLoc: CAM generated the repo, then CAM evaluated,
preflighted, camified, self-mined, security-scanned, and helped harden it with
source-boundary verification plus JSON patch-plan output. See the
[MyLoc hardening case study](docs/examples/MYLOC_HARDENING_CASE_STUDY.md).

## Compatibility

- [Claude Code integration](docs/integrations/CLAUDE_CODE.md) explains how
  Claude Code should consume CAM packets while preserving source read-only
  boundaries.
- [Grok Build integration](docs/integrations/GROK_BUILD.md) explains the same
  packet and receipt contract for Grok Build.

Templates live under:

- `templates/goals/`
- `templates/claude-code/`
- `templates/grok-build/`
- `templates/config/`

## Local Runtime State

Runtime-critical local state stays out of this repo. In this workspace,
`CAM_CAM/data/claw.db` is a local database used by CAM runtime tools. CAM_Codx
documents how to point at it, but does not copy it into GitHub.

The local clean operating overlay is:

```text
/Volumes/WS4TB/CAM_ALL
```

The non-destructive cleanup staging area is:

```text
/Volumes/WS4TB/CAM_ARCHIVE
```

## Current Status

Verified on 2026-06-21:

- `CAM_Codx` remote: `https://github.com/deesatzed/CAM_Codx.git`
- `CAM_CAM` remote: `https://github.com/deesatzed/CAM_CAM.git`
- `moriahcareframe` remote: `https://github.com/deesatzed/moriahcareframe.git`
- `CAM_CAM/data/claw.db` exists locally and is treated as local runtime state.
- No old folders should be deleted, moved, renamed, or archived without a
  separate explicit approval.

See [status](docs/STATUS.md), [repo map](docs/REPO_MAP.md), and
[FAQ](docs/FAQ.md) for the live public framing.
