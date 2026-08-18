# CAM_CAM and CAM_Codx Capability Audit

**Audited:** 2026-08-12  
**CAM_CAM head:** `d8334ab` at audit start  
**CAM_Codx head:** `cf035c8` at audit start  
**Status:** Current-state audit plus approved target classification

> Historical snapshot dated 2026-08-12. Tasks 1-13 subsequently implemented
> and release-audited the approved control plane; the old approved-target gap
> statements below are retained as audit provenance. See
> `docs/reports/2026-08-18-task-10-13-release-audit.md` and
> `GOAL_TASK_14_MATRAIX_SESA.md` for current status and successor scope.

## Conclusion

CAM does not need another collection of commands. It needs CAM_Codx to manage
the capabilities that already exist through one outcome-oriented control
plane.

The audit found:

- a broad, working CAM_CAM runtime surface;
- eight historical top-level workflow verbs plus many expert/admin commands;
- hidden aliases that already preserve some compatibility;
- an incomplete `cam chat` implementation that only executes mining;
- four setup-installed CAM_Codx skills plus a separate semantic-session skill;
- CAM-SEQ storage that already represents candidate selection, target landing,
  outcomes, and run lineage;
- no single reviewed workflow that visibly connects one mining receipt to one
  build decision and its verified outcome.

The approved target is one user-facing `cam-codx` skill. Direct CAM_CAM CLI
usage remains available for troubleshooting, recovery, runtime development,
and regression isolation.

## Current CAM_Codx Surface

### Setup-installed skills

| Skill | Current purpose | Approved target |
| --- | --- | --- |
| `cam-codx-setup` | Install/repair wrapper, DB, config, and skills | Internal setup playbook |
| `cam-codx-swe` | Routine build/update/debug workflow | Core of canonical `cam-codx` skill |
| `cam-codx-development-brief` | Read-only new/continue-rescue recall | Internal `assess` playbook |
| `cam-codx-pull-mine-dir` | Bounded repo update and mining cycle | Internal explicit `mine` playbook |

The separately installed `cam-codx-session` semantic router is also related
and should be consolidated into the canonical skill rather than becoming a
fifth public choice.

### Current CAM_Codx tools

| Tool | Capability | Approved role |
| --- | --- | --- |
| `cam_setup_wizard.py` | Layout, runtime import, wrapper, skill install | Setup playbook helper |
| `cam_manager.py` | Fixed-operation packets, approvals, execution receipts | Shared approval/execution engine |
| `development_brief.py` | Read-only primary-corpus project brief | `assess` helper |
| `cam_pull_mine_dir.py` | Safe pull, bounded mine, delta assessment | Explicit `mine` helper |
| `generate_agent_packs.py` | Shared host capability contract and packs | Extend as the single registry/doc source |

## Current CAM_CAM Top-Level Commands

### Visible commands

These commands were registered and visible in the Typer tree at audit time:

```text
init
chat
evaluate
camify
enhance
fleet-enhance
status
brief-query
preflight
create
ideate
premine
mine
mine-workspace
mine-all
mine-self
enrich
validate
benchmark
setup
stats
gaps
dashboard
mcp
federate
```

Approved classification:

- all capabilities are CAM_Codx-managed;
- their direct CLI forms remain troubleshooting/runtime-development commands;
- normal product docs start with CAM_Codx rather than this list.

### Hidden compatibility commands

These were already hidden and remain callable:

```text
results
runbook
quickstart
add-goal
keycheck
mine-report
forge-export
forge-benchmark
govern
synergies
assimilation-report
assimilation-delta
reassess
prism-demo
```

They stay hidden. Where a grouped canonical replacement exists, docs name only
that replacement.

## Current CAM_CAM Command Groups

| Group | Subcommands | CAM_Codx route |
| --- | --- | --- |
| `ab-test` | `start`, `status`, `stop` | evidence comparison / verify |
| `cag` | `rebuild`, `status`, `convert` | knowledge administration |
| `doctor` | `keycheck`, `status`, `expectations`, `audit`, `routing` | doctor/setup/fix |
| `evolution` | `register`, `run`, `loop`, `status`, `champion-db`; hidden `approve` | evolution |
| `forge` | `export`, `benchmark` | knowledge export / verify |
| `kb` | `seed`, `bootstrap`, `insights`, `search`, `capability`, `patterns`, `domains`, `synergies`, `brains`, `export-kit` | knowledge |
| `kb community` | `publish`, `browse`, `import`, `approve`, `status` | knowledge administration with external/write policy |
| `kb instances` | `list`, `manifest`, `query`, `add`, `remove` | federation administration |
| `learn` | `report`, `delta`, `reassess`, `synergies`, `usage`, `search`, `backfill-components`, `proof`, `ingest-codex-outcomes` | assess/record/knowledge |
| `models` | `current`, `catalog`, `set`, `rollback` | models |
| `models benchmark` | `fixtures`, `plan`, `advance`, `run`, `report`, `select` | models benchmark |
| `models profile` | `list`, `show`, `use` | models/profile promotion |
| `pulse` | `scan`, `daemon`, `status`, `discoveries`, `scans`, `report`, `preflight`, `ingest`, `ingest-hf`, `freshness`, `refresh` | knowledge acquisition/maintenance |
| `security` | `scan`, `status` | assess/fix/verify |
| `self-enhance` | `status`, `start`, `validate`, `swap`, `rollback` | CAM self-enhancement |
| `task` | `add`, `quickstart`, `runbook`, `results` | plan/build/fix |

## Duplicate and Confusing Surfaces

### `cam chat`

Docs currently describe chat as the general command chooser. Runtime code only
routes `mine`; `create` and `enhance` requests receive a not-wired message.
Chat must not be advertised as the normal front door.

### Mining variants

`mine`, `mine-workspace`, `mine-all`, `mine-self`, `premine`, PULSE ingestion,
and CAG conversion are different runtime scopes, but are difficult for a normal
user to distinguish. CAM_Codx should select among them from the stated source,
target, and desired outcome. It must not flatten their safety differences.

### Creation and repair variants

`evaluate`, `preflight`, `camify`, `create`, `enhance`, task commands, and
validation form useful stages. They should be composed behind CAM_Codx's
`assess`, `plan`, `build`, `fix`, and `verify` intents rather than presented as
competing ways to begin.

### Skill overlap

Setup, SWE, Development Brief, pull/mine, and session routing are legitimate
playbooks but not legitimate product choices. One canonical skill should route
to them internally.

## Approved Normal CAM_Codx Routes

| Route | User outcome | Main CAM_CAM capabilities |
| --- | --- | --- |
| `assess` | Understand a new idea or existing repo and recall prior work | `brief-query`, `evaluate`, KB/learn/federation |
| `plan` | Define scope, gaps, risks, checks, and next milestone | `preflight`, `camify`, task planning, application packets |
| `build` | Start or continue a bounded implementation | `create`, task execution, Codex edits |
| `fix` | Diagnose, mitigate, repair, or recommend redevelopment | `evaluate`, doctor, security, `enhance` |
| `verify` | Test a result and its claims | `validate`, benchmark, audit, A/B, repository tests |
| `record` | Persist verified outcome and limitations | learn usage/proof/outcome ingestion, CAM-SEQ outcomes |
| `mine` | Add knowledge from an explicit source | premine/mine variants/PULSE as selected by scope |
| `knowledge` | Inspect or maintain existing knowledge | KB, learn, federation, CAG, Forge |
| `models` | Inspect, compare, promote, or roll back models | models and benchmark groups |
| `self-enhance` | Evaluate or improve CAM itself | self-enhance group with separate swap approval |
| `evolution` | Manage champion/challenger evolution | evolution group |
| `doctor` | Diagnose CAM or environment health | doctor, status, stats, security |
| `setup` | Install or repair CAM_Codx and CAM_CAM | setup/init/wrapper/skill migration |

## Existing Mine-to-Build Structures

The requested reusable-mine-to-build concept is not absent; it is fragmented
across existing labels and structures:

- Repo-to-Repo Reuse Finder;
- Development Brief;
- methodologies and component cards;
- application packets;
- task plans and run connectomes;
- pair, landing, and outcome events;
- usage attribution and compiled recipes;
- Repo Necromancer and Forge exports.

The missing product capability is the reviewed, visible chain from a specific
mining receipt through candidate acceptance/rejection, target landing,
verification, and later recall. The approved SWE Run provides that chain
without adding a second knowledge store.

## Current Versus Approved Target

At this audit checkpoint:

- the command inventory is verified from the runtime registration tree;
- compatibility aliases are already hidden;
- the Development Brief, pull/mine coordinator, and secure manager exist;
- the canonical `cam-codx` skill, full registry classifications, managed SWE
  Run integration, and migration are **not yet implemented**.

See:

- `docs/plans/2026-08-12-cam-codx-control-plane-design.md`;
- `docs/plans/2026-08-12-cam-codx-control-plane.md`;
- `GOAL.md`.
