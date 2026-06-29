# CAM CLI Assessment — `cam --help` Surface Review
**Generated:** 2026-06-29
**Engine assessed:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM` (== GitHub CAM_CAM `f900dfc`, the installed `cam`)
**Method:** help-text capture + read-only smoke tests + source inspection. LLM-spending commands assessed from code/help, not executed (marked ⚠️ not-runtime-verified).

---

## Headline findings

1. **The surface is large and flat: ~25 top-level commands + 12 sub-groups (~60 commands total).** Several top-level commands duplicate sub-group commands (e.g. `enrich`, `status`, `stats`, the 4 `mine*` variants), and 14 hidden commands exist purely as aliases for grouped ones.
2. **The commands work; the failures observed are CONFIG, not code.** Every read-only command that "failed" (rc=2) did so because `claw.toml` references **stale/empty ganglion DBs** (`drive-ops`, `agentic-memory`, `typescript`, … under `/Volumes/WS4TB/a_aSatzClaw/multiclaw/`) that have no `methodologies` table → "Skipping … no such table" + nonzero exit. Fix the config and they pass.
3. **`--config` support is inconsistent** — accepted by `stats`, `status`, `gaps`, `mine`, `enrich`, `enhance`, `evaluate`; NOT by `kb *`, `security *`, `cag *`, `learn *`. This is a UX trap (I hit it during testing).
4. **Mining is split across 4 near-duplicate top-level commands** (`mine`, `mine-workspace`, `mine-all`, `mine-self`) — prime candidate for contraction into `mine` subcommands.

---

## Command inventory — purpose / works / verdict

Legend: ✅ verified working · ⚠️ exists, not runtime-verified (LLM/long) · ❌ broken · 🔁 redundant

### Core lifecycle (inspect → learn → create → validate)
| Command | Purpose | Works | Keep? | Notes |
|---|---|---|---|---|
| `init` | Guided first-run setup | ⚠️ | keep | onboarding |
| `setup` | Interactive API keys/models config | ⚠️ | keep | overlaps `init` + `doctor keycheck` — consider merging into `init` |
| `chat` | Conversational guide to workflows | ⚠️ | keep? | low-evidence value; verify usage before keeping |
| `evaluate` | Score a repo's enhancement potential | ⚠️ | **keep (core)** | first step of enhance |
| `camify` | Analyze repo + match KB → executable plan | ⚠️ | keep | overlaps `evaluate`+`enhance --dry-run`; clarify distinct value |
| `enhance` | evaluate→plan→dispatch→verify→learn | ⚠️ | **keep (core)** | the main pipeline |
| `fleet-enhance` | enhance many repos | ⚠️ | keep | fleet variant of enhance |
| `preflight` | Pre-examine task, ask questions, estimate | ⚠️ | keep | NOTE: "estimate time/budget" conflicts with user rule against time/cost estimates — review |
| `create` | Create/fix/augment a repo from an outcome | ⚠️ | keep | generation path |
| `ideate` | Novel app concepts from memory + repos | ⚠️ | keep | generation path |
| `validate` | Validate created repo vs saved spec | ⚠️ | **keep (core)** | closes the loop |
| `benchmark` | Benchmark Forge output | ⚠️ | 🔁 merge | duplicate of `forge benchmark` |

### Mining (OVER-SPLIT — 4 top-level + premine)
| Command | Purpose | Works | Keep? | Notes |
|---|---|---|---|---|
| `mine` | Mine local repos for patterns | ✅ (this session) | **keep** | canonical |
| `mine-workspace` | Mine across multiple dirs | ⚠️ | 🔁 → `mine workspace` | |
| `mine-all` | 5-phase bulk: scan→preview→schema→mine→report | ⚠️ | 🔁 → `mine all` | |
| `mine-self` | Mine the project's own code | ⚠️ | 🔁 → `mine self` | |
| `premine` | Assess GitHub repos remotely before cloning | ⚠️ | keep | distinct (remote, pre-clone) — but could be `mine premine` |
| `enrich` | Assimilate embryonic methodologies | ✅ primary / ❌ `--include-ganglia` | keep + FIX | ganglia path crashes: `g_engine.initialize()` undefined |

### Knowledge / status (read-only)
| Command | Purpose | Works | Keep? | Notes |
|---|---|---|---|---|
| `status` | CLAW system status | ✅ | 🔁 | duplicates `doctor status` |
| `stats` | methodology/repo/ganglion/CAG counts | ✅ | 🔁 → `kb stats` | |
| `gaps` | category×brain coverage matrix | ✅ | 🔁 → `kb gaps` | |
| `dashboard` | Browser knowledge explorer | ⚠️ | keep | |
| `federate` | Cross-brain pattern synthesis | ⚠️ (no subcmds shown) | keep/verify | empty Commands list — confirm it's a leaf cmd |
| `mcp` | Start MCP server for external agents | ⚠️ | **keep (core)** | integration surface |

### Sub-groups (well-formed)
| Group | Subcommands | Works | Keep? | Notes |
|---|---|---|---|---|
| `learn` | report, delta, reassess, synergies, usage, search, backfill-components, proof, ingest-codex-outcomes | ⚠️ (config-blocked in test) | **keep** | report/delta/reassess/synergies are aliases for hidden top-level cmds |
| `task` | add, quickstart, runbook, results | ⚠️ | keep | all 4 are aliases for hidden top-level cmds |
| `forge` | export, benchmark | ⚠️ | keep | aliases; `benchmark` dups top-level |
| `doctor` | keycheck, status, expectations, audit, routing | ⚠️ (config-blocked) | **keep** | good home for status/keycheck |
| `kb` | seed, bootstrap, insights, search, capability, patterns, domains, synergies, brains, export-kit, community, instances | ⚠️ (config-blocked) | **keep** | the richest group; natural home for stats/gaps |
| `pulse` | scan, daemon, status, discoveries, scans, report, preflight, ingest, ingest-hf, freshness, refresh | ⚠️ | keep | self-contained subsystem |
| `self-enhance` | status, start, validate, swap, rollback | ⚠️ | keep | self-contained |
| `ab-test` | start, status, stop | ⚠️ | keep | research feature — confirm still used |
| `evolution` | register, run, loop, status, champion-db | ⚠️ | keep | research feature — confirm still used |
| `security` | scan, status | ✅ (status) | **keep** | TruffleHog 3.95.6 available |
| `cag` | rebuild, status, convert | ✅ (status) | keep | |

### Hidden top-level commands (14) — alias targets / dev tools
`add-goal`, `keycheck`, `mine-report`, `forge-export`, `forge-benchmark`,
`assimilation-report`, `assimilation-delta`, `reassess` (and the unnamed ones at
4457/4876/4981/7822/8216/8251), `prism-demo`.
**Verdict:** these are the *real* implementations the grouped commands alias to. They
should stay hidden (or be removed as top-level and live only under their group) — keeping
both the hidden top-level AND the grouped alias is the main source of surface bloat.

---

## Does it work? (evidence)
- ✅ **Verified working this session:** `mine`, `enrich` (primary DB), `status`, `stats`, `gaps`, `security status`, `cag status`, all `--help`.
- ❌ **Confirmed broken:** `enrich --include-ganglia` (`DatabaseEngine` has no `initialize`).
- ⚠️ **Config-blocked (not code bugs):** `kb brains`, `learn report`, `doctor routing` etc. fail because `claw.toml` lists ganglia whose DBs lack a `methodologies` table. **Cleaning the ganglion config fixes these.**
- ⚠️ **Not runtime-verified (LLM/long-running):** enhance, create, ideate, camify, fleet-enhance, pulse*, evolution*, self-enhance*, ab-test*, premine, the mine-* variants.

---

## Recommended grouping / contraction

**Goal: ~10 top-level verbs + tight groups, remove duplicate top-level aliases.**

1. **Collapse mining**: `mine`, `mine-workspace`, `mine-all`, `mine-self`, `premine`, `mine-report`
   → one `mine` group: `mine <dir>` (default), `mine workspace`, `mine all`, `mine self`, `mine premine`, `mine report`.
2. **Move status/stats/gaps under existing groups**: `status`→`doctor status` (drop top-level), `stats`→`kb stats`, `gaps`→`kb gaps`. (Keep short top-level aliases only if measured as high-frequency.)
3. **Remove duplicate `benchmark`** top-level (keep `forge benchmark`).
4. **Stop exposing both hidden-top-level AND grouped alias.** Pick the group form as canonical; delete the hidden top-level command (or keep hidden purely for back-compat with a deprecation note).
5. **Standardize `--config`** across ALL commands that touch the corpus (currently missing on kb/security/cag/learn).
6. **Reconcile `evaluate` vs `camify`** — both "analyze a repo + plan." Document the distinction or merge.
7. **Review `preflight`'s "estimate time/budget"** against the standing rule that forbids time/cost estimates.
8. **Confirm-or-cut research surfaces**: `chat`, `ab-test`, `evolution`, `federate` — keep only if actively used; otherwise hide.

### Proposed top-level after contraction
```
init · evaluate · enhance · create · validate · mine · enrich · learn · kb · doctor · pulse · mcp · dashboard
(+ groups: task, forge, security, cag, self-enhance; research hidden behind a flag)
```

---

## Action items (separate from CAM_ORG_PLAN.md)
- [ ] P1: clean stale ganglion entries in `claw.toml` (the multiclaw/* paths) — unblocks kb/learn/doctor.
- [ ] P2: fix `enrich --include-ganglia` in the engine clone.
- [ ] P2: standardize `--config` flag coverage.
- [ ] P2: contract the 4 `mine*` commands into a `mine` group.
- [ ] P3: de-duplicate hidden-top-level vs grouped aliases; review `preflight` estimate language.
```
