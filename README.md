# Codex-CAM Methodology

*A thin librarian bridge between OpenAI Codex CLI and the CAM_CAM research engine.*

**Status: local MCP implementation is runnable on branch `feature/initial-impl`; final Codex E2E sign-off is blocked by non-interactive MCP approval behavior and unavailable `x-ai/grok-build-0.1` provider support. Tracking documents: PRD.md, build_specs.md, build_to_do_checklist.md, meta/HANDOFF_LATEST.md.**

---

## What this is

`cam-codex-mcp` is a **standalone MCP server** that gives OpenAI Codex CLI four tools for working with mined software methodologies and cross-repo decision records. It runs in one of two modes auto-detected on MCP initialization:

- **Standalone mode** (default): three of the four tools work fully — cross-repo decision search and the local outcome flywheel — with no external dependencies beyond Codex itself. `cam_recall` returns an honest empty result (no fabrication) with a clear remediation hint.
- **Connected mode**: when `CAM_CODEX_MCP_DB_PATH` points at a CAM_CAM `claw.db` file, all four tools light up — recall returns ranked methodologies with full provenance, and outcomes are recorded back into `claw.db` so CAM_CAM's bandit can ingest them.

CAM_CAM (the heavy Python research engine that mines methodologies, runs the bandit, and produces `claw.db`) is an **optional** corpus producer. This repo works without it. If you have it installed, point one env var at its data file and the recall layer activates.

A Codex skill (`deepscientist-data-research`) in the workspace today carries a **phantom contract** — it references MCP tools (`claw_query_memory`, `claw_store_finding`) that are not wired anywhere. This methodology supersedes that with a clean four-tool surface and rewrites the skill to use it.

This README frames scope honestly. The corpus has **107 methodologies** (95 viable, 12 embryonic), not the 889 the CAM_CAM README still claims. The bandit has never received outcome signal (`bandit_outcomes = 0`, `fitness_log = 0`) even though there are 96 `usage_log` entries — the loop is open at the "record outcome" step. The design is therefore framed as **seed corpus plus loop closure**, not "mature library on tap." Closing the loop is the v1 centerpiece; everything else in the design exists to make that loop reliable.

The doctrine adds one line on top of the existing three:
> *Codex decides. Tests arbitrate. Markdown remembers. **CAM librarian cites.***

---

## Run locally

This repo does not start a browser app. The runnable surface is an MCP stdio server consumed by Codex or by an MCP SDK client.

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python -m claw_codex_mcp --version
python -m claw_codex_mcp --transport stdio
```

The second command waits for newline-delimited JSON-RPC on stdin and exits cleanly on EOF. It is normally launched by Codex through `.codex/config.toml`.

Run the local standalone demo:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/product_smoke.py
```

That one-command product smoke wraps the version check plus standalone and connected MCP stdio checks. The real-use-case pilot plan is tracked at [`docs/REAL_USE_CASE_TEST_PLAN.md`](docs/REAL_USE_CASE_TEST_PLAN.md).

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/demo_stdio.py --mode standalone
```

Run the connected demo against the real slice fixture:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/demo_stdio.py --mode connected
```

Both demos launch `python -m claw_codex_mcp --transport stdio` as a subprocess through the official MCP SDK client, list the four tools, call each tool at least once, and print the resulting JSON. Demo SQLite files are written under `/private/tmp/cam_codex_mcp_demo/` by default; pass `--demo-dir <path>` to keep them somewhere else.

Run the validation suite:

```bash
pytest tests/codex_mcp/ -q
```

The latest local run in this branch reported `65 passed`.

Run through the workspace Codex MCP configuration:

```bash
CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex mcp list
CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex mcp get cam_cam
```

Real Codex-agent E2E use is not signed off yet. Current blockers are recorded in `meta/VALIDATION_GAPS_2026-05-20.md`: non-interactive `codex exec` cancels MCP tool calls before returning tool results, and the requested `x-ai/grok-build-0.1` slug is not supported by the current Codex ChatGPT account.

---

## What this repo builds

This repository's deliverable is **`cam-codex-mcp`** — a thin, four-tool, standalone MCP server. It is the core of the methodology. The server code lives in `src/claw_codex_mcp/`; local stdio protocol coverage and standalone/connected fixture behavior are implemented on the current branch.

| Component | Role | Coupling |
|---|---|---|
| **`cam-codex-mcp`** (this repo's deliverable) | 4-tool MCP server consumed by Codex CLI over stdio | none required; works standalone |
| OpenAI Codex CLI | orchestrator that consumes `cam-codex-mcp` via `.codex/config.toml` | required at runtime |
| CAM_CAM heavy engine (`claw.db`) | optional corpus producer; mining + bandit run out-of-band | optional; enables `cam_recall` and richer `cam_provenance` |
| Legacy 17-tool MCP (`claw.mcp_server`) | pre-existing, never wired to Codex; unrelated to this design | not used, not modified |

This repo speaks raw SQL to `claw.db` when present; it has no Python import dependency on the `claw` package. CAM_CAM's installation, mining cadence, and bandit are entirely its own concern.

### Tool surface preview

The full schemas live in `build_specs.md`. This is the one-line summary, including how each tool behaves with and without a CAM_CAM corpus connected.

| Tool | I/O | Connected mode | Standalone mode |
|---|---|---|---|
| `cam_recall` | read | top-N viable methodologies with fitness, tags, anti-pattern | `{results: [], corpus_status: "absent", reason: ...}` — honest empty, never fabricates |
| `cam_provenance` | read | citation block for a `methodology_id` (source repo, path, commit, mined_at, fitness denominators) | `{found: false, corpus_status: "absent"}` |
| `cam_decisions_search` | read | FTS5 search across cross-repo `DECISIONS.md` records | **identical** — this tool has zero CAM_CAM dependency |
| `cam_record_outcome` | append-only write | row inserted into `codex_outcome_log` table inside `claw.db` (CAM_CAM's bandit ingests) | row inserted into local SQLite at `~/.cam_codex_mcp/codex_outcome_log.db` |

Every tool response carries a `corpus_status` field with one of: `connected` / `empty` / `absent` / `degraded`. Skills inspect this and surface the mode to the user honestly.

A fifth tool, `cam_match_failure`, was considered and explicitly deferred to v2 — the live `failure_knowledge` table has one row, which is not enough corpus to support the contract.

---

## How it works

`cam-codex-mcp` runs in one of two modes, auto-detected on MCP initialization and then kept immutable for the process lifetime. Configuration is three optional environment variables; all have sensible defaults; mode is logged on initialization so you always know what you have.

### Standalone mode (default)

Activates when `CAM_CODEX_MCP_DB_PATH` is unset or points to a missing file. Three of the four tools work fully: cross-repo `DECISIONS.md` search via `cam_decisions_search`, outcome logging to a local SQLite ledger at `~/.cam_codex_mcp/codex_outcome_log.db` via `cam_record_outcome`, and the server reports its state honestly. The fourth tool, `cam_recall`, returns an empty result with `corpus_status: "absent"` and a remediation hint — it never fabricates methodologies. This mode is fully useful: cross-repo decision search and the local outcome flywheel both work, just without the mined-pattern recall layer.

### Connected mode

Activates when you set `CAM_CODEX_MCP_DB_PATH` to a CAM_CAM `claw.db` file. `cam_recall` returns ranked methodologies with full provenance (commit SHA, source repo, fitness score with denominator). Outcomes are recorded into the same `claw.db` so CAM_CAM's bandit can ingest them. All four tools fully active.

### Configuration

Three optional environment variables, all with sensible defaults:

| Variable | Purpose | Default |
|---|---|---|
| `CAM_CODEX_MCP_DB_PATH` | corpus location (presence triggers connected mode) | unset → standalone |
| `CAM_CODEX_MCP_OUTCOME_DB_PATH` | outcome ledger location | mode-dependent default |
| `CAM_CODEX_MCP_DECISIONS_INDEX` | cross-repo decision FTS index | `~/.cam_codex_mcp/codex_decisions_index.db` |

The 4-tool ceiling is enforced by CI in both modes. **No mode silently synthesizes data.**

---

## Repository layout

This is its **own git repository** (initialized 2026-05-17, branch `main`), a sibling of `CAM_CAM/`. CAM_CAM stays in its own repo and is **not modified** by this methodology.

```
/Volumes/WS4TB/WS4TBr/CAM_Codx/
├── codex-cam-methodology/              ← THIS REPO
│   ├── .git/
│   ├── .gitignore
│   ├── LICENSE                          MIT (matches CAM_CAM)
│   ├── README.md                        this file — the front door
│   ├── PRD.md                           product requirements: problem, users, success criteria, scope, risks
│   ├── build_specs.md                   engineering spec: MCP tool schemas, skill contracts, module layout, DB additions
│   ├── build_to_do_checklist.md         ordered atomic build tasks; every checkbox has a validation gate
│   ├── docs/
│   │   └── _validation_gates.md         per-phase and cross-cutting validation gates (referenced by checklist)
│   ├── migrations/                      DDL for additive outcome ledger tables
│   ├── src/claw_codex_mcp/              thin librarian MCP package
│   ├── tests/                           unit and stdio integration tests
│   └── tools/demo_stdio.py              local runnable demo
│
├── CAM_CAM/                             heavy Python research engine; unchanged by this methodology
├── .codex/                              Codex CLI install (38 skills, 10 agents, AGENTS.md doctrine); separate config
└── HANDOFF_LATEST.md                    session continuity packet (symlink to dated handoff)
```

The README, PRD, build_specs, build_to_do_checklist, and latest handoff form the current contract. When they disagree, `meta/HANDOFF_LATEST.md` records the latest verified state.

---

## Quick orientation commands

Three commands a reader can run today to ground themselves in the live state.

**1. Verify the corpus is still in the expected state.** If these numbers have changed, the design framing in PRD.md must be revisited.

```bash
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db \
  "SELECT lifecycle_state, COUNT(*) FROM methodologies GROUP BY lifecycle_state;"
```

Expected output:
```
viable|95
embryonic|12
```

**2. List the Codex skills already present.** Two of them (`repo_recon`, `deepscientist-data-research`) are explicitly touched by this design.

```bash
ls /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills | head
```

**3. Read the doctrine.** The new methodology adds one line; everything else is preserved.

```bash
cat /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md
```

---

## Core concepts

A short glossary. Each term appears in PRD.md and build_specs.md with the same meaning.

**Methodology.** A mined, scored, lifecycle-tracked pattern stored in `claw.db`. Every row carries `notes` and `tags` populated at mining time. 107 rows live today.

**Provenance.** The one-line citation Codex must show before applying any recalled pattern. Shape: `{methodology_id, source_repo, source_path, source_commit_sha, mined_at, last_verified_at, fitness_score, green_count, red_count}`. The display contract is *"fitness 0.87, 8 green / 0 red, source: <repo>/<path>"* — score with denominator, never bare.

**Fitness.** An outcome-based score that today sits at zero across the corpus because no outcomes have been written. The v1 of this methodology exists to start populating it via `cam_record_outcome`.

**The boundary rule.** A single decision everything follows from:
> Stateful + cross-repo + computational → MCP.
> Doctrine + workflow + output schema → Skill.
> Anything that fits in markdown → Markdown.

This rule is what keeps the MCP surface at four tools.

**Rescue ladder.** A Codex skill that auto-fires on the **second consecutive verification failure**, before the user is asked. It queries `cam_recall` for `error_handling` patterns matching the failure surface, applies the top result with provenance, and escalates if the third attempt also fails. It is doctrine, not an auto-fix engine.

**The flywheel.** The loop the methodology is built to close: *recall → cite → apply → verify → record outcome → corpus improves → next recall is smarter.* Today the loop is open at the "record outcome" step; closing it is the v1 deliverable.

**Phantom contract.** What currently exists: `.codex/skills/deepscientist-data-research/SKILL.md` references `claw_query_memory` and `claw_store_finding` on lines 25, 65, 135, 162, and 168, but `.codex/config.toml` has no `[mcp_servers.cam_cam]` block. The skill silently no-ops. v1 rewrites this skill to the new four-tool surface; no back-compat is pursued.

**Out-of-band.** CAM_CAM mining, bandit updates, and defense-chain runs happen on a schedule the user controls, never inline during a Codex turn. The librarian reads what mining has already produced; it does not trigger mining.

---

## Design guardrails

These are non-negotiable for v1. They appear again in PRD.md (success criteria) and build_specs.md (CI enforcement).

- **Four-tool ceiling on the librarian MCP**, enforced by a test that fails CI if a fifth tool is registered. The boundary rule above is the only reason to add a tool; scope creep through the librarian is the failure mode the seventeen-tool server already proves.
- **No write tool besides `cam_record_outcome`**, and that one is append-only. The librarian never mutates a methodology row, never edits provenance, never deletes.
- **Provenance is mandatory before application.** No recalled pattern may be applied without its provenance row first written to `IMPLEMENT.md`. This is a doctrine line in `.codex/AGENTS.md`, not a soft convention.
- **Out-of-band only for mining/bandit/defense-chain.** The librarian never triggers CAM_CAM jobs. If a tool implementation reaches for the miner or the dispatcher, the boundary has been crossed.
- **No silent application above a fitness threshold.** Fitness informs ranking; it never bypasses citation. Every applied pattern is cited regardless of score.
- **Honest corpus framing in every artifact.** 107 methodologies, not 889. Where the 889 number appears in CAM_CAM's own README, that is a documentation issue tracked separately and not propagated here.

## How a developer will interact

Three short scenarios. "Now" is the present state; "proposed" is the design target. The provenance shape in each example is the contract — score with denominator, plus source repo and path. No bare numbers.

**1. Adding rate limiting to an existing repo.**
*Now:* Codex grep-searches the local repo, finds nothing relevant, writes a plausible-looking implementation, lands a subtle off-by-one.
*Proposed:* the `cam_recall_and_cite` skill fires on the user's request; `cam_recall` returns the top viable pattern (e.g. `token-bucket-rate-limit-ts`, fitness 0.87, 8 green / 0 red, source: `ABXorcist/lib/rate-limit.ts`) plus one anti-pattern. Codex writes the provenance row into `IMPLEMENT.md` *before* any code, then applies the pattern, then `outcome_log` records the verification result via `cam_record_outcome`. The bandit gains its first real signal.

**2. Codex hits two consecutive test failures.**
*Now:* Codex retries with a slightly different patch, sometimes spirals into a third or fourth attempt, eventually asks the user.
*Proposed:* `rescue_ladder` auto-fires on the second failure (doctrine, not opt-in). It calls `cam_recall` filtered to `error_handling` patterns matching the failure signature, applies the top result with provenance, and on a third failure escalates to the user with the full ladder trace recorded in `DECISIONS.md`. The escalation is structured — the user sees what was tried, what was cited, and why each attempt failed.

**3. Greenfield repo.**
*Now:* Codex scaffolds from its own priors and whatever the user pastes.
*Proposed:* `repo_recon` (modified) calls `cam_decisions_search` for similar greenfield setups, composes a blueprint from cited fragments, and writes lineage (`source_repo + commit_sha` for each fragment) into `AGENTS.md` so the next session can audit what came from where. The scaffolding becomes auditable rather than an opaque guess.

---

## What this is NOT

- Not a fork or rewrite of CAM_CAM. CAM_CAM is an *optional* corpus producer in this design; this repo runs without it.
- Not a real-time runtime for the bandit, miner, or defense chain. The librarian reads; CAM_CAM's heavy engine writes new methodologies on its own schedule.
- Not "the 889 patterns." When connected, the live corpus is 107 viable methodologies — framed honestly as a seed corpus, not a mature library.
- Not bundled with a seed/demo corpus. Standalone mode returns an honest empty for `cam_recall`, with a remediation hint pointing at CAM_CAM. **Per workspace policy (no mock / no placeholder / no demo data), a frozen fixture corpus would walk that line.** Install CAM_CAM to get a real corpus.
- Not production ready. Final Codex E2E sign-off is still blocked by MCP approval/model availability, even though the local MCP server and SDK-client demo run.
- Not opt-in once installed. The Codex skills auto-fire on declared triggers (the `cam_recall_and_cite` skill on feature requests, `rescue_ladder` on the second failure, `outcome_log` after any verified step that used a recalled pattern). Opt-in would mean the loop never closes.
- Not a carve-out of the existing seventeen-tool MCP. It is a **new** thin server with a separate module, separate process, separate auth token, separate config block.

---

## How to contribute / what's next

The four documents in this folder are designed to be read in order.

1. **PRD.md** — start here. Problem framing, user definition, success criteria, scope decisions, open questions, and the explicit v2 deferrals (notably `cam_match_failure`, which the live `failure_knowledge = 1` row cannot yet support).
2. **build_specs.md** — read second. MCP tool schemas for `cam_recall`, `cam_provenance`, `cam_decisions_search`, and `cam_record_outcome`. Skill contracts for `cam_recall_and_cite`, `rescue_ladder`, `outcome_log`, the modified `repo_recon`, and the rewritten `deepscientist-data-research`. Module layout. Any additive (never destructive) `claw.db` schema needs for the fitness ledger.
3. **build_to_do_checklist.md** — execute in order. Every checkbox has an explicit validation gate; no checkbox is closed without its gate passing. The workspace rule of "no step advances without validation" applies. Baseline measurements on five unfamiliar real repos must land before any methodology code, per the validation plan.
4. **HANDOFF_LATEST.md** (one level up) — the session continuity packet. Re-read before resuming a paused dialogue.

All open decisions are tracked in PRD.md under "Open Questions." If a question is not in that list and you find yourself making an assumption, add it to that list before proceeding. The build_to_do_checklist references PRD decisions by anchor — if an anchor moves, both files update together.

---

## References

- [`./PRD.md`](./PRD.md) — product requirements
- [`./build_specs.md`](./build_specs.md) — engineering spec
- [`./build_to_do_checklist.md`](./build_to_do_checklist.md) — ordered build tasks with validation gates
- [`../HANDOFF_LATEST.md`](../HANDOFF_LATEST.md) — session continuity packet
- [`../.codex/AGENTS.md`](../.codex/AGENTS.md) — Codex doctrine (the one line this methodology extends)

---

## License and attribution

License: MIT (matches CAM_CAM's `pyproject.toml`).

Built on:
- **OpenAI Codex CLI** — orchestrator plane
- **`mcp` (official Python SDK)** — stdio transport for the new librarian server
- **`claw` package (CAM_CAM)** — corpus, schemas, and the engine the librarian reads from
