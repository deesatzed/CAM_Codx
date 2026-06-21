# Local Config Alignment

Verified on 2026-06-21 using metadata-only commands.

## Runtime-Critical Local Files

| Local file | Observed state | Role | Public handling |
|---|---|---|---|
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db` | 109 MB SQLite DB | CAM runtime corpus and outcome/state database | Never copy into CAM_Codx or GitHub. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw.toml` | tracked public-safe TOML | CAM runtime default config | Safe to keep tracked while secrets and local overrides stay out of Git. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw_cheap.toml` | tracked public-safe TOML | Alternate runtime route | Safe to keep tracked while secrets and local overrides stay out of Git. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw_dspro.toml` | tracked public-safe TOML | DeepSeek-oriented runtime route | Safe to keep tracked while secrets and local overrides stay out of Git. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw_grok.toml` | tracked public-safe TOML | Grok-oriented runtime route | Safe to keep tracked while secrets and local overrides stay out of Git. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/.env.example` | 3.4 KB | Public environment example in CAM_CAM | Safe to reference; do not copy secrets. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml` | present | Local Codex wiring | Do not publish directly; use placeholder template. |

## Database Role

`claw.db` is the canonical local CAM runtime database for this workspace. It is
used by CAM runtime tools for methodology/corpus retrieval, provenance, mining
state, and outcome logs. CAM_Codx may point at it through
`CAM_CODEX_MCP_DB_PATH`, but CAM_Codx does not own the database.

Metadata inspection found tables such as:

```text
methodologies
methodology_embeddings
codex_outcome_log
evolution_runs
failure_knowledge
fleet_repos
projects
tasks
```

New users should create or obtain their own CAM_CAM runtime database, then set
their local `CAM_CODEX_MCP_DB_PATH` to that file. They should not commit the DB.

## Local Overlay

The local overlay path is `/Volumes/WS4TB/CAM_ALL/local_state`. It contains
documented placeholders for local-only runtime state. This pass did not copy
`claw.db`; the placeholder points back to the current local DB path. Tracked
public-safe `CAM_CAM/claw*.toml` defaults are not local state; only private
overrides, real `.env` files, endpoints, machine paths, and databases are
local-only.
