# Codex-CAM Methodology

*A thin librarian bridge between OpenAI Codex CLI and the CAM_CAM research engine.*

**Status: DESIGN PHASE (v0.1) — no code yet. Tracking documents: PRD.md, build_specs.md, build_to_do_checklist.md.**

---

## What this is

Two real things already live side-by-side in this workspace, and they do not talk to each other.

On one side, **CAM_CAM** is a substantial Python research engine — a methodology miner, a bandit scorer, a three-layer defense chain, an export pipeline, and a SQLite corpus indexed with FTS5 and sqlite-vec. It is heavy by design and intended to run out-of-band. It carries a seventeen-tool MCP server (`claw.mcp_server`) that was never wired to Codex; that server is removed as part of v1 (see `meta/HANDOFF_LATEST.md`).

On the other side, **OpenAI Codex CLI** is installed at `.codex/` with thirty-eight skills, ten agents, and a doctrine in `AGENTS.md`. Codex is markdown-first, fast, and decisive. It auto-fires skills on declared triggers rather than waiting for the user to ask. Today the two systems have no working contract: one Codex skill (`deepscientist-data-research`) references CAM MCP tools (`claw_query_memory`, `claw_store_finding`) that are not wired in `.codex/config.toml`. The skill is therefore a **phantom contract** — it silently no-ops or hallucinates the response shape.

The **Codex-CAM Methodology** is a design for a third, narrow plane that sits between them. It is a new, purpose-built MCP server with a hard four-tool ceiling, enforced by a CI test. Its job is to act as a *librarian* over `claw.db` — recall a relevant pattern, hand back its provenance, search cross-repo decisions, and write outcomes to an append-only fitness ledger. CAM_CAM keeps mining and scoring out-of-band; Codex keeps orchestrating in markdown; the librarian is the only thing that runs inline during a developer's turn. The librarian never triggers mining, never runs the bandit, never owns the defense chain. Those stay where they are.

This README frames scope honestly. The corpus has **107 methodologies** (95 viable, 12 embryonic), not the 889 the CAM_CAM README still claims. The bandit has never received outcome signal (`bandit_outcomes = 0`, `fitness_log = 0`) even though there are 96 `usage_log` entries — the loop is open at the "record outcome" step. The design is therefore framed as **seed corpus plus loop closure**, not "mature library on tap." Closing the loop is the v1 centerpiece; everything else in the design exists to make that loop reliable.

The doctrine adds one line on top of the existing three:
> *Codex decides. Tests arbitrate. Markdown remembers. **CAM librarian cites.***

---

## What this repo builds

This repository's deliverable is **`cam-codex-mcp`** — a new, thin, four-tool MCP server that connects Codex to the CAM_CAM corpus. It is the core of the methodology. Today the design is locked and the prerequisites are committed; the server code itself lands in `src/claw_codex_mcp/` once Phase 0 gates are green (see `build_to_do_checklist.md`).

| Component | Role | Status in this work |
|---|---|---|
| **`cam-codex-mcp`** (this repo's deliverable) | 4-tool librarian connecting Codex to `claw.db` | DESIGN COMPLETE, code pending Phase 0 gates |
| OpenAI Codex CLI | orchestrator that consumes `cam-codex-mcp` | already installed at `.codex/` (38 skills, 10 agents) |
| CAM_CAM heavy engine | mining + bandit + corpus producer; runs out-of-band | exists; only the 17-tool legacy MCP is touched (removed) |
| Legacy 17-tool MCP (`claw.mcp_server`) | the unused, never-wired-to-Codex MCP that this methodology obsoletes | **scheduled for removal** as part of v1 |
| `claw.db` corpus | methodologies + (future) fitness ledger | 107 methodologies; ledger empty (0 bandit_outcomes); v1 closes the loop |

The legacy seventeen-tool `claw.mcp_server` was **the bloat being escaped**. It was never wired to Codex (the phantom contract referenced above) and serves no current consumer in this workspace. v1 removes it cleanly and replaces it with `cam-codex-mcp`'s four-tool surface.

### Tool surface preview

The full schemas live in `build_specs.md`. This is the one-line summary so a reader knows what they are about to read.

| Tool | Read/Write | One-line purpose |
|---|---|---|
| `cam_recall` | read | return top-N viable methodologies for a task description with fitness, tags, and one anti-pattern |
| `cam_provenance` | read | return the citation block for a given `methodology_id` (source repo, path, commit, mined_at, fitness denominators) |
| `cam_decisions_search` | read | FTS5 + vector search across cross-repo decision records for similar prior choices |
| `cam_record_outcome` | append-only write | record a `{methodology_id, outcome, verification_signal, repo, commit}` row to the fitness ledger |

A fifth tool, `cam_match_failure`, was considered and explicitly deferred to v2 — the live `failure_knowledge` table has one row, which is not enough corpus to support the contract.

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
│   ├── migrations/                      (future) DDL for additive tables on `cam.db` — CAM_CAM's schema is not modified
│   ├── src/claw_codex_mcp/              (future) the thin librarian MCP — separate top-level package
│   └── tests/                           (future) unit + integration + e2e
│
├── CAM_CAM/                             heavy Python research engine; unchanged by this methodology
├── .codex/                              Codex CLI install (38 skills, 10 agents, AGENTS.md doctrine); separate config
└── HANDOFF_LATEST.md                    session continuity packet (symlink to dated handoff)
```

The README, PRD, build_specs, and build_to_do_checklist form a four-document contract. Nothing else in this repo is load-bearing yet.

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

- Not a replacement for CAM_CAM. The heavy engine continues to do mining, bandit updates, evolution, federation, and dashboards — out-of-band, on the user's schedule.
- Not a real-time runtime for the bandit, miner, or defense chain. The librarian reads. It does not run mining inline.
- Not "the 889 patterns." The live corpus has 107. The PRD frames this honestly as a seed corpus.
- Not production ready. Not complete. This is design phase; no code has been written.
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
