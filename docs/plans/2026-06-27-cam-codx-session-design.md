# CAM_Codx Session Skill Design

## Purpose

CAM_Codx needs a semantic session layer so a user can state an outcome in
plain language and let Codex choose the right CAM/CAM_Codx workflow. The user
should not have to remember individual `cam mine`, `cam camify`, `cam enhance`,
database, config, or API-key commands for routine work.

The skill should make Codex act as the CAM_Codx manager:

- understand the user's intent;
- explain which CAM options apply;
- inspect local repo/runtime state;
- recommend the safest useful path;
- run read-only checks directly;
- gate mutating operations;
- save evidence and user-facing summaries.

## Scope

Create a Codex skill named `cam-codx-session` under the user's Codex skills
directory. It should cover the current CAM command surface plus the CAM_Codx
hub surfaces already present in this repo:

- CAM CLI: setup, inspect, learn, create, enhance, validate, benchmark,
  knowledge browsing, MCP, self-enhancement, evolution, security, CAG, and
  related grouped commands.
- CAM_Codx: Codex `/goal` workflows, agent packs, capability contract,
  setup wizard, templates, reports, and evidence-gated handoffs.
- Codex manager behavior: repo inspection, dirty-tree handling, config/db/env
  selection, command routing, safety gates, verification, and markdown session
  reporting.

## User Experience

The desired user prompt is semantic:

```text
CAM_Codx, mine these repos and enhance guardrails-suite.
```

or:

```text
Start a CAM_Codx session for this repo. What should CAM do here?
```

Codex should answer with a short option map, recommend one route, and begin
with safe checks. It should avoid dumping a command cookbook unless the user
asks for commands.

## Architecture

The skill is an orchestration guide, not a replacement runtime. CAM_CAM remains
the owner of runtime behavior, local databases, CLI commands, and MCP tools.
CAM_Codx remains the workflow hub. Codex remains the manager that connects
user intent to the right runtime path and verifies results.

The skill should include:

- `SKILL.md`: concise manager workflow and safety rules.
- `references/cam-command-map.md`: plain-language map of CAM commands to user
  intents.
- `references/session-playbooks.md`: reusable playbooks for common workflows.
- `scripts/cam_session_preflight.py`: deterministic local preflight that checks
  repo state, CAM CLI presence, config/db/env paths, and likely blockers
  without printing secrets.

## Safety

Default to read-only or dry-run actions first:

- `cam status`
- `cam doctor`
- `cam stats`
- `cam evaluate --mode structural`
- `cam premine`
- `cam kb`
- `cam gaps`
- `cam camify` when it only writes an explicit plan path
- `cam enhance --dry-run`

Gate mutating or high-risk actions:

- live mining into `claw.db`;
- `enhance`, `fleet-enhance`, `self-enhance`, `evolution`;
- `create`, `forge`, or generated repo creation;
- credential or config changes;
- production deployment;
- security actions that modify files;
- workflows touching PHI, clinical/safety semantics, or compliance-sensitive
  data.

## Default Session Flow

1. Read repo truth files if present.
2. Classify user intent: setup, inspect, learn, plan, enhance, create,
   validate, compare, integrate, or explain.
3. Locate or ask for repo path, CAM_CAM runtime path, `claw.db`, config TOML,
   and `.env`.
4. Run preflight and dirty-tree checks.
5. Recommend a route with rationale and risk level.
6. Execute safe checks.
7. Ask before live mutation unless the user's instruction already clearly
   authorizes the exact bounded action.
8. Run verification and inspect diffs.
9. Save a `CAM_SESSION_REPORT.md` or equivalent when the session produces
   durable changes or decisions.

## Success Criteria

- The skill validates with the Codex skill validator.
- The preflight script runs without writing to the target repo.
- A realistic TempleOE/guardrails-suite preflight can show repo, DB, config,
  and `.env` state without exposing secrets.
- The skill explains CAM choices in user language while preserving strict
  ownership: CAM_Codx manages workflow, CAM_CAM executes runtime behavior.
