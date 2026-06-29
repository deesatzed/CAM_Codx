# CAM_ORG_PLAN.md — Local CAM Repo & Data Organization Plan

Status: PROPOSED (awaiting approval before any move/delete)
Author: generated from evidence audit on 2026-06-29
Scope: organize CAM repos, claw.db corpora, and claw.toml profiles across `/Volumes`.

---

## 1. Verified facts (evidence base)

### GitHub = source of truth (Goal 1)

| GitHub repo | Role | HEAD (main) | Date |
|---|---|---|---|
| `deesatzed/CAM_CAM` | Runtime/base engine (the `cam` CLI) | `f900dfc` | 2026-06-22 |
| `deesatzed/CAM_Codx` | Codex-native program-manager / workflow hub | `6fe47bf` | 2026-06-27 |

CAM_Codx's own README defines the hub-and-spoke model:
`CAM_CAM runtime engine -> CAM_Codx workflow hub -> generated product repos`.
CAM_Codx owns docs/goal-contracts/templates; it does **not** vendor CAM_CAM code or DBs.

### The installed `cam` CLI

- Editable install maps `claw` -> `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw`.
- That checkout is **clean and == GitHub CAM_CAM HEAD `f900dfc`** (only stray untracked `CAM_Codx_last5291pm.txt`).
- **Decision: this is the canonical local engine checkout.**

### Clone audit (after `git fetch`, vs `origin/main`)

| Clone | ahead | behind | dirty | Verdict |
|---|---|---|---|---|
| `WS4TB/WS4TBr/CAM_Codx/CAM_CAM` | 0 | 0 | 1 (untracked txt) | **CANONICAL ENGINE** — keep |
| `WS4TB/repo622sn/CAM_Codx` | **4** | 10 | 23 | **HAS UNIQUE WORK** — push first, then keep as canonical hub working copy |
| `WS4TB/repo622sn/CAM_CAM` | 0 | 5 | 6 | fully-on-github; holds **live claw.db** — demote to data-only, then archive checkout |
| `WS4TB/repo421sn/CAM_CAM` | 0 | 9 | 0 | backup — archive |
| `WS4TB/camcxBU64/CAM_CAM` | 0 | 9 | 3 | backup — archive (capture dirty first) |
| `WS4TB/buccx623/CAM_CAM` | 0 | 5 | 0 | backup — archive |
| `WS4TB/buccx623/CAM_Codx` | 0 | 12 | 3 | backup — archive (capture dirty first) |
| `WS4TB/careframe/CAM_Codx` | 0 | 20 | 0 | backup — archive |
| `WS4TB/_MyGhRepos/CAM_CAM` | 0 | 20 | 0 | backup — archive |
| `WS4TB/ccxt/CAM_Codx` | 0 | 5 | 0 | backup — archive |

Only **one** clone (`repo622sn/CAM_Codx`) holds commits GitHub lacks (4 docs commits:
OpenRouter MCP plan/verification, session-skill design) plus 23 dirty files
(agent-packs, docs, tools). **Nothing is archived until this is pushed.**

### claw.db corpora (Goal 2)

~25 `claw.db` files exist on `/Volumes`. The **live working corpus** is
`WS4TB/repo622sn/CAM_CAM/claw.db` (122MB, 2,474 methodologies, 2026-04-27 -> 2026-06-29),
plus its ganglia `repo622sn/instances/{typescript,rust}/claw.db`. All others are
backups / per-experiment / ganglion DBs and are currently **undocumented**.

### claw.toml profiles (Goal 2)

All variants are identical except model ids + `db_path`:

| File | Profile / purpose | Models |
|---|---|---|
| `claw.toml` | **Active** — GLM + Kimi routing | z-ai/glm-5.2, moonshotai/kimi-k2.7-code, gpt-4.1-mini, grok-4.3 |
| `claw_cheap.toml` | Low-cost profile | deepseek-v4-flash, qwen3.6-flash, deepseek-v4-pro |
| `claw_dspro.toml` | DeepSeek-pro profile | (same deepseek/qwen family) |
| `claw_grok.toml` | Grok-oriented profile | (same deepseek/qwen family) |

---

## 2. Target canonical layout

```text
CANONICAL (keep, authoritative)
  /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM   <- engine, == GitHub CAM_CAM, installed cam CLI
  /Volumes/WS4TB/repo622sn/CAM_Codx        <- program-manager hub (after pushing 4 commits)
  <DATA_ROOT>/claw.<profile>.live.db       <- the live corpus (see naming below)

ARCHIVE (move, never delete; reversible)
  /Volumes/WS4TB/CAM_ARCHIVE/<orig-path-flattened>/   <- all 7 stale backup clones
```

Note: engine and hub are intentionally separate repos (different GitHub remotes).
The engine being nested under `WS4TBr/CAM_Codx/` is incidental; optionally re-clone
to a flat path later, but not required.

---

## 3. claw.db / claw.toml self-documentation (Goal 2)

### Naming convention

- Live corpus:    `claw.<profile>.live.db`     e.g. `claw.glm.live.db`
- Backups:        `claw.<profile>.backup-YYYYMMDD-HHMMSS.db`
- Experiments:    `claw.<profile>.exp-<slug>.db`
- Ganglia stay as `instances/<brain>/claw.db` (engine-managed; do not rename).

### DB_REGISTRY.md (lives in CAM_Codx hub)

A table maintained for every CAM database:

| path | purpose | owning_repo | profile | status (live/backup/exp/ganglion) | created_by | last_used | notes |

Seed it from this audit; CAM_Codx updates it on each run. This answers
"why does this DB exist / was it a feature-validation test?" at a glance.

### claw.toml headers

Add a top comment block to each profile stating: purpose, which models, when to use,
and the `db_path` it targets. (Profiles are otherwise indistinguishable at a glance.)

---

## 4. Execution order (each step reversible; nothing deleted)

1. **Preserve unique work**
   - In `repo622sn/CAM_Codx`: review the 23 dirty files, commit the keepers, push the
     4 unpushed commits to `deesatzed/CAM_Codx`. (GATE: human review of the diff.)
   - In `repo622sn/CAM_CAM`: revert the stray `src/claw/cli/_monolith.py` edit; preserve
     `RISK_NOTES.md` (E-001) and `mining_registry.json` deliberately.
2. **Lock canonical engine**: confirm `WS4TBr/CAM_Codx/CAM_CAM` clean == `f900dfc`;
   keep the editable install pointed there.
3. **Name + register the live corpus**: rename `repo622sn/CAM_CAM/claw.db` per convention,
   point `claw.toml` `db_path` at it, write `DB_REGISTRY.md` + per-DB rows.
4. **Capture dirty state on backups** (`camcxBU64/CAM_CAM`, `buccx623/CAM_Codx`) before archiving.
5. **Archive stale clones**: `mv` the 7 backup checkouts into `/Volumes/WS4TB/CAM_ARCHIVE/`.
   (Move only; a follow-up pass can delete after a retention window.)
6. **Document retention**: backups older than the canonical and fully-on-github may be
   deleted after N days; record the policy in DB_REGISTRY.md.

---

## 5. Open decisions for the human

- Where is `<DATA_ROOT>` for the live corpus? (default: keep in `repo622sn/CAM_CAM/`)
- Confirm the 23 dirty `repo622sn/CAM_Codx` files should be committed as-is or curated.
- Confirm archive destination `/Volumes/WS4TB/CAM_ARCHIVE/` (or another volume).
- Retention window for archived backups before deletion (or never auto-delete).
