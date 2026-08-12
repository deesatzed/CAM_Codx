# CAM_Codx

CAM_Codx is the Codex-native control plane for CAM: it lets a developer manage
CAM_CAM's repo intelligence, provenance, mining, models, generators, and
evidence gates from inside the Codex workflow they already use.

Start here when you want Codex to consume CAM artifacts, continue from a
generated `CAM_CODEX_GOAL.md`, or harden a standalone product created by CAM.
Direct `CAM_CAM` usage is for runtime troubleshooting, development, recovery,
and regression isolation. CAM_CAM still owns all runtime implementation and
local databases.

> **Current versus approved target (2026-08-12):** setup currently installs
> four specialized CAM_Codx skills. The approved next architecture consolidates
> them into one `cam-codx` skill that manages every CAM_CAM capability. That
> consolidation is designed and planned but not yet implemented. See the
> [capability audit](docs/CAM_CAPABILITY_AUDIT_2026-08-12.md),
> [approved design](docs/plans/2026-08-12-cam-codx-control-plane-design.md),
> and [implementation plan](docs/plans/2026-08-12-cam-codx-control-plane.md).

The clearest current showpiece is XTtape: a controlled vanilla-vs-CAM planning
comparison for a live AI news ticker app. It demonstrates that CAM_Codx is most
valuable before coding, when it helps Codex recall proven methods, compare
alternatives, and turn a rough product idea into an evidence-backed build
contract.

## What This Is

CAM_Codx is a workflow hub. It owns docs, goal contracts, adapter templates,
case studies, and the clean public explanation for how Codex works with CAM.
It does not vendor CAM_CAM code, copy CAM_CAM databases, or store generated
product runtime code.

The current repo family is organized as a hub-and-spoke system:

```text
CAM_CAM runtime engine -> CAM_Codx workflow hub -> generated product repos
                         -> Claude Code adapter
                         -> Gemini adapter
                         -> Grok Build adapter
```

## Repo Roles

| Repo | Role | Start here when |
|---|---|---|
| `CAM_Codx` | Codex-native workflow hub | You want Codex goals, handoffs, templates, and onboarding. |
| `CAM_CAM` | Runtime/base engine | You are troubleshooting, recovering, testing, or changing CAM internals. |
| `moriahcareframe` | Generated standalone product | You want to inspect or harden the product repo produced by CAM/Codex. |
| `MyLoc` | Generated product dogfood proof | You want to see CAM evaluate and harden a Repo Necromancer output repo. |

Claude Code, Gemini, and Grok Build are adapter surfaces. They consume CAM
packets, source receipts, generated goals, and CAM MCP/CLI tools; they do not
change the ownership model.

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

For Codex sessions, generate the narrow CAM wrapper after `CAM_CAM` has a venv,
`claw.db`, `claw.toml`, and `.env`:

```bash
python tools/cam_setup_wizard.py \
  --cam-home ~/CAM \
  --skip-clone \
  --install-codex-skill \
  --non-interactive
```

Then approve this narrow command prefix in Codex when CAM needs to update its
local DB or SQLite sidecars:

```text
~/CAM/scripts/cam-codx
```

After that, start Codex in a target repo and ask for the installed setup or
routine SWE skill:

```text
Use cam-codx-setup to verify CAM.
```

For normal build/update/debug work, use:

```text
Use cam-codx-swe to manage this SWE task with CAM recall and evidence gates.
```

For a focused new-project or continue/rescue decision, use:

```text
Use cam-codx-development-brief to start this project from relevant prior work.
```

For an explicitly authorized bounded directory update and mining cycle, use:

```text
Use cam-codx-pull-mine-dir to update and mine this repository directory. Start with --dry-run if I asked for a preview; otherwise use the pinned claw.db, a local hard-cap defaults file, and report the evidence gate and --skip-swap candidate verdict.
```

Use `--source-root /absolute/path/to/repos` when the default mining directory
does not apply. The skill never turns this invocation into `self-enhance swap`,
a model/profile change, or a configuration edit; those remain separately
approved operations. See [CAM Pull Mine Directory](docs/CAM_PULL_MINE_DIR.md).

The routine skill does not mine repositories or change CAM automatically. See
the [CAM_Codx program manager](docs/CAM_CODEX_PROGRAM_MANAGER.md) for the
packet, approval, tournament, and staged self-enhancement flow.

Read [CAM Development Brief](docs/CAM_DEVELOPMENT_BRIEF.md) for the read-only
recall and next-step workflow.

Choose the smallest workflow that fits the need:

| Need | Start with | Default boundary |
| --- | --- | --- |
| Shape a new project or decide how to resume an existing one | `cam-codx-development-brief` | Named target plus one explicit primary corpus; no mining, provider calls, edits, or telemetry writes. |
| Build, update, review, or debug a defined task | `cam-codx-swe` | Read-only CAM recall first; repository-native tests decide whether the change is accepted. |
| Update and mine one local repository directory | `cam-codx-pull-mine-dir` | Explicit source root (or default), pinned `claw.db`/config, hard cap, receipts, and at most one supervised `--skip-swap` candidate. |
| Compare models or promote/self-enhance CAM | `cam_manager.py` and the program-manager workflow | A separate phase, bounded packet, explicit approval, and evidence receipt. |

For the novice step-by-step flow and use cases, read:

- [Codex quickstart](docs/QUICKSTART_CODEX.md)
- [CAM Development Brief](docs/CAM_DEVELOPMENT_BRIEF.md)
- [CAM Pull Mine Directory](docs/CAM_PULL_MINE_DIR.md)
- [New computer setup walkthrough](docs/NEW_COMPUTER_SETUP_WALKTHROUGH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [XTtape CAM showpiece case study](docs/examples/XTTAPE_CAM_SHOWPIECE_CASE_STUDY.md)
- [XTtape showpiece artifact bundle](docs/showpieces/xttape-cam-comparison/COMPARISON_SUMMARY.md)
- [Repo Necromancer workflow](docs/WORKFLOW_REPO_NECROMANCER.md)
- [MoriahCareFrame case study](docs/examples/MORIAH_CAREFRAME_CASE_STUDY.md)
- [MyLoc hardening case study](docs/examples/MYLOC_HARDENING_CASE_STUDY.md)

## XTtape Showpiece

XTtape is a novice-friendly demonstration of how to use CAM_Codx without
drifting into app code too early. The experiment compared:

- a vanilla Codex project brain,
- a CAM-shaped run that did not actually use recalled methodology,
- a corrected CAM recall run using mined methodology context,
- a prior incumbent plan used only as design evidence.

The result was a final merged build brain and implementation plan for a
browser-first live AI news ticker. The CAM recall run scored higher than the
vanilla run because it added concrete engineering requirements: source
receipts, read-only connector boundaries, replay fixtures, duplicate-ingestion
protection, freshness/confidence scoring, provider fallback, and user-learning
audit records.

Start with the [case study](docs/examples/XTTAPE_CAM_SHOWPIECE_CASE_STUDY.md),
then inspect the full [artifact bundle](docs/showpieces/xttape-cam-comparison/).
The final app-build contract lives in
[`runs/final`](docs/showpieces/xttape-cam-comparison/runs/final/) and the next
implementation plan lives at
[`docs/plans/2026-06-25-xttape-live-ai-news-ticker.md`](docs/showpieces/xttape-cam-comparison/docs/plans/2026-06-25-xttape-live-ai-news-ticker.md).

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

## CAM Agent Packs

CAM_Codx now publishes generated host packs from one shared capability contract:

- [Agent pack overview](docs/AGENT_PACKS.md)
- [Capability contract](agent-packs/contract/CAPABILITY_CONTRACT.md)
- [Claude Code pack](agent-packs/claude-code/README.md)
- [Gemini pack](agent-packs/gemini/README.md)
- [Grok Build pack](agent-packs/grok-build/README.md)

The packs map the same CAM runtime capabilities to host-native instructions and
MCP configuration examples. CAM_CAM remains the runtime/MCP owner; CAM_Codx owns
the generated pack docs, tests, and generator.

Uniform setup and test flow:

1. Copy the chosen pack into the target project.
2. Copy or merge its MCP config example.
3. Replace local CAM_CAM placeholders outside Git.
4. Run the host discovery command.
5. Run the pack smoke script after host credentials are configured.
6. Record the output before claiming the pack is verified.

Smoke scripts:

- `agent-packs/claude-code/smoke.sh`
- `agent-packs/gemini/smoke.sh`
- `agent-packs/grok-build/smoke.sh`

## Compatibility

- [Claude Code integration](docs/integrations/CLAUDE_CODE.md) explains the
  Claude-specific pack and packet workflow.
- [Gemini integration](docs/integrations/GEMINI.md) explains the Gemini pack,
  CLI/API split, and Remote MCP caveats.
- [Grok Build integration](docs/integrations/GROK_BUILD.md) explains the Grok
  Build pack, skills/hooks layout, and receipt contract.

Templates live under:

- `templates/goals/`
- `templates/claude-code/`
- `agent-packs/gemini/`
- `templates/grok-build/`
- `templates/config/`

## Local Runtime State

Runtime-critical local state stays out of this repo. In this workspace,
`CAM_CAM/data/claw.db` is a local database used by CAM runtime tools. CAM_Codx
documents how to point at it, but does not copy it into GitHub.

Codex should use the setup-generated `cam-codx` wrapper for CAM runtime commands
that need DB writes. The wrapper pins the runtime directory, `.env`, `claw.db`,
and `claw.toml`, so users can approve one bounded command instead of broad
filesystem access.

> **New machine?** [`SETUP_ON_LAPTOP.md`](SETUP_ON_LAPTOP.md) is a beginner-friendly, step-by-step
> guide to stand up a working CAM copy on a laptop — clone both repos, install the engine, and
> hand-copy the gitignored `claw.db` brain and `.env`. The authoritative source of truth for
> which corpus is current is [`DB_REGISTRY.md`](DB_REGISTRY.md).

The local clean operating overlay is:

```text
/Volumes/WS4TB/CAM_ALL
```

The non-destructive cleanup staging area is:

```text
/Volumes/WS4TB/CAM_ARCHIVE
```

## Current Status

Verified on 2026-06-26:

- `CAM_Codx` remote: `https://github.com/deesatzed/CAM_Codx.git`
- `CAM_CAM` remote: `https://github.com/deesatzed/CAM_CAM.git`
- `moriahcareframe` remote: `https://github.com/deesatzed/moriahcareframe.git`
- XTtape showpiece results are published under
  `docs/showpieces/xttape-cam-comparison/`.
- `CAM_CAM/data/claw.db` exists locally and is treated as local runtime state.
- No old folders should be deleted, moved, renamed, or archived without a
  separate explicit approval.

See [status](docs/STATUS.md), [repo map](docs/REPO_MAP.md), and
[FAQ](docs/FAQ.md) for the live public framing.
