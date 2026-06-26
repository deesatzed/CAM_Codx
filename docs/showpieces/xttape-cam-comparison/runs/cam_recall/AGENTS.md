# AGENTS.md

## Standing Codex Rules

Before coding, read these files if present:

1. GOAL.md
2. STANDARDS.md
3. IMPLEMENT.md
4. DECISIONS.md
5. PROGRESS.md
6. TASK_QUEUE.md

Treat these files as the project source of truth.

## Project-Specific Rule For XTtape

XTtape is currently in project-brain initialization only. Do not write app code until GOAL.md, DECISIONS.md, PROGRESS.md, and CAM_MEMORY_APPLIED.md have been reviewed and an implementation phase is explicitly started.

Use the CAM context packet as methodology guidance only:

- Do not copy app code from mined repositories.
- Do not import repository-specific implementation details unless they are expressed as reusable methodology.
- Do not expose secrets, credentials, private keys, tokens, account names, or private feed contents.
- Do not use XTtapeNotes.md.

## Autonomous Progress Rule

When running in autonomous mode, do not ask the user for clarification unless the project is truly blocked.

If information is missing but a safe assumption can be made:

- make the assumption,
- document it in PROGRESS.md,
- continue.

Stop only for:

- missing credentials,
- missing API keys,
- missing user accounts,
- destructive actions,
- production deployment,
- sensitive data risk,
- legal/compliance uncertainty,
- repeated failure after mitigation attempts,
- product decision that would materially change scope.

## CAM Recall Layer Requirements

The CAM recall layer changes XTtape from a generic news summarizer into an evidence-governed ambient intelligence system. Future agents must preserve these requirements unless DECISIONS.md records a replacement decision:

- Source adapters must publish inventory, scope, freshness, and credential status at startup.
- External-source and tool access must cross an MCP boundary with read-only allowlists by default.
- Ingestion must be idempotent, duplicate-aware, replayable, and safe to run in dry-run mode.
- Every summary, ranking, explanation, and user-facing claim must retain source receipts.
- Structured persistence must include confidence, freshness, time-decay, source identity, and user-learning records with reset and retention controls.
- AI provider routing must be capability-aware and degrade gracefully when credentials, rate limits, models, or providers are unavailable.
- Write-capable tools or social actions require explicit approval and idempotent persistence.
- Build acceptance must include evidence gates for duplicate ingestion, concurrency, stale sources, tool approval, provider fallback, and receipt-backed explanations.

## Claude Code Delegation

Codex may use Claude Code as a bounded second-opinion worker when the local `claude` CLI is installed.

Claude delegation is allowed for:

- bounded implementation tasks,
- code review,
- bug triage,
- test gap analysis,
- loophole search,
- first-principles alternatives,
- release readiness.

Codex remains the orchestrator and final decision-maker.

Before delegating:

- create a specific handoff prompt,
- include only relevant context,
- define what Claude may edit,
- define what Claude must not touch,
- request structured Markdown output.

After delegating:

- read Claude's response,
- classify each recommendation as Accepted / Rejected / Needs Investigation,
- implement only accepted recommendations,
- update PROGRESS.md,
- update DECISIONS.md if needed.

Do not let Claude perform broad repo rewrites.
Do not use unsafe permission bypass flags.
Do not pass secrets, PHI, credentials, private keys, or unnecessary sensitive data to Claude.
Prefer read-only delegation unless the task is tightly scoped and safe.

## Core Rule

Codex decides. Claude contributes. Tests arbitrate. Markdown remembers.
