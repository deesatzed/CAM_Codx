# Codex-CAM Methodology — Product Requirements Document

## 1. Document Metadata

| Field | Value |
|---|---|
| Title | Codex-CAM Methodology — PRD |
| Status | **Draft — under brainstorm** (Section 1 of 6 of the design dialogue has been presented; Sections 2–6 awaiting presentation and approval) |
| Document version | v0.1 |
| Last updated | 2026-05-17 |
| Owner | Solo developer (workspace `/Volumes/WS4TB/WS4TBr/CAM_Codx/`) |
| Source handoff | `/Volumes/WS4TB/WS4TBr/CAM_Codx/HANDOFF_LATEST.md` |
| Working name | "Codex-CAM Methodology" — not locked (see Open Questions) |

This document does not assign delivery dates, sprint boundaries, or duration estimates. Ordering is expressed as sequencing only ("first", "next", "after X validates"). No "next review date" is set — the document is updated when a decision lands.

---

## 2. Problem Statement

The workspace contains two assets that have failed to combine: a heavy Python research engine (CAM_CAM / `claw v0.1.0`) sitting on a real corpus of mined methodologies, and a Codex CLI install (38 skills, 10 agents) doing the actual daily work. Today they do not speak to each other. Concretely:

| Pain | Evidence (file:line or live query) | What it costs |
|---|---|---|
| **Phantom MCP contract.** A skill ships in `.codex/` that calls tools that are not wired anywhere. | `.codex/skills/deepscientist-data-research/SKILL.md:25,65,135,162,168` references `claw_query_memory` and `claw_store_finding`; `.codex/config.toml` only wires `context7`, no `[mcp_servers.cam_cam]` block exists. | Skill either no-ops silently or hallucinates results. The user cannot trust skill output. |
| **Fitness loop has never closed.** Patterns are recalled but outcomes are never recorded, so the bandit has no signal. | Live query on `CAM_CAM/data/claw.db` (2026-05-17): `methodology_usage_log = 96`, `methodology_bandit_outcomes = 0`, `methodology_fitness_log = 0`. | Every recall is unweighted by experience. The corpus does not improve with use. |
| **Stale "library" framing.** README claims `889 methodologies`. Reality is `107` (`95 viable + 12 embryonic`, zero `thriving` / `declining` / `dormant` / `dead`). | `CAM_CAM/README.md:11,119,143,388,459` vs live `SELECT lifecycle_state, COUNT(*) FROM methodologies`. | Design decisions made against a phantom library size produce wrong scope and false confidence. |
| **Heavy engine cannot run inline.** Codex turns must remain fast; CAM_CAM's mining, bandit, defense chain, and federation are too heavy. | `CAM_CAM/src/claw/_monolith.py` weight; `claw.mcp_server` registers 17 tools; HTTP transport unimplemented at `_monolith.py:13794`. | Without a bridge, the corpus is unreachable from the orchestrator that needs it. |
| **The existing MCP is the bloat being escaped.** | `CAM_CAM/src/claw/mcp_server.py:1689-1779` registers 17 tools spanning query, write, decomposition, application packets, run connectomes, failure tracing, recipe promotion, mining missions, specialist exchanges, webhooks, and bridges. | Wiring this surface into Codex would push a kitchen-sink contract into the orchestrator plane and dissolve the doctrine boundary. |
| **TypeScript surface in the corpus is thin** for a workspace heavy in Next.js. | Live query: 100% `PATTERN` type; language distribution = 50 Python, 53 untyped, 2 TypeScript, 1 markdown, 1 yaml. | Recall quality on TS-heavy projects (`dram-quest`, healthcare web apps) is weaker than nominal. |
| **Failure rescue corpus is too thin for v1.** | Live query: `failure_knowledge = 1` row. | A `cam_match_failure` tool would be answering one query with one answer. Out of scope for v1. |
| **No provenance discipline in skill output.** Existing skills can apply patterns without citing commit SHA, denominator, or fitness score. | None of the 38 skill `SKILL.md` files mandate provenance lines today. | "Provenance theater" risk — citation-shaped strings with no resolvable referent. |

The methodology defined in this PRD exists to close those gaps **without** running CAM_CAM inline.

---

## 3. Users and Primary Use Cases

### 3.1 User

One developer. Solo. Runs OpenAI Codex CLI (`gpt-5.5`, `model_reasoning_effort = "high"`, `personality = "pragmatic"` per `.codex/config.toml`) as the daily driver across roughly 80 trusted projects under `/Volumes/WS4TB/`. Mix of medical apps (HIPAA-relevant), MCP servers, Next.js, Python, and Agno multi-agent systems. Workflow is markdown-first; the doctrine `.codex/AGENTS.md` (as of v1 of this methodology) declares: *"Codex decides. Tests arbitrate. Markdown remembers. CAM librarian cites."*

### 3.2 Primary Use Cases (Named Scenarios)

These three scenarios come from the UX brainstorm and are the only scenarios v1 must serve well. Listed in the order Codex turns typically flow, not in temporal order.

**Scenario A — `feature-add`.** Developer asks Codex to add a feature in a project Codex has seen before (e.g., "add rate limiting to the new `/api/refer` route"). Codex should consult the corpus, propose at most one applicable pattern with one-line provenance, apply it, and record the outcome.

**Scenario B — `failure-rescue`.** Codex runs verification (tests/lint/build) and hits a failure. On the **second consecutive** verification failure on the same step, the `rescue_ladder` skill runs **before** the user is asked. The ladder consults `cam_decisions_search` for prior decisions tagged with the failure family before any model rotation or replanning. **`cam_match_failure` is not used in v1** — the failure corpus is too thin (1 row).

**Scenario C — `greenfield`.** Developer points Codex at an unfamiliar repo. `repo_recon` runs and now also calls `cam_decisions_search` to surface prior decisions from sibling projects in the same workspace (e.g., "ABXorcist chose Zod for input validation — cited at SHA `abc1234`"). Orientation output carries cross-repo provenance, not invented narrative.

A fourth scenario — **silent turn** — is not a use case; it is a constraint. Trivial turns (typo fix, comment edit, rename) MUST NOT invoke the MCP at all. The MCP is only consulted when the skill that owns the turn declares the dependency.

---

## 4. Goals

Every goal below is falsifiable and free of numeric time targets. Ordering language only.

1. **Provenance integrity.** Every applied pattern carries a one-line provenance row: `methodology_id`, fitness score, green/red denominator, source commit SHA, source path. Resolvable. No string-shaped citations without a SHA.
2. **Append-only fitness ledger.** Every verified step that used a recalled methodology produces exactly one append-only `outcome` row in `claw.db` (`bandit_outcomes` and/or `fitness_log`). No updates, no deletes. The ledger is the centerpiece — it is what closes the loop that has been open since the corpus was mined.
3. **Hard 4-tool MCP ceiling.** The new MCP surface exposes exactly four tools: `cam_recall`, `cam_provenance`, `cam_decisions_search`, `cam_record_outcome`. Enforced by a CI test that fails on a fifth registration.
4. **Doctrine-conformant skills.** The skill bundle (`cam_recall_and_cite`, `rescue_ladder`, `outcome_log`, modified `repo_recon`, rewritten `deepscientist-data-research`) follows the boundary rule: **stateful + cross-repo + computational → MCP; doctrine + workflow + output schema → Skill; anything that fits in markdown → Markdown.**
5. **Heavy engine stays out-of-band.** No CAM_CAM mining, bandit retraining, federation, or dashboard code runs inside a Codex turn. The MCP is a read-mostly librarian over `claw.db`, plus one append-only writer.
6. **Codex actually invokes the MCP.** When a skill declares MCP dependency, the corresponding turn produces at least one tool call to the new MCP. Verified by transcript inspection, not self-report.
7. **Honest framing.** No "889 methodologies" marketing claim anywhere in the new surface, skills, doctrine additions, or PRD prose. The pitch is "seed corpus of 95 viable patterns" or stronger only if the live query proves stronger.
8. **The phantom contract is closed.** `.codex/skills/deepscientist-data-research/SKILL.md` is rewritten to call only the four new tools (or omits tool calls entirely). No `claw_*` references remain.
9. **Workspace doctrine carries the new line.** `.codex/AGENTS.md` is updated (already applied 2026-05-18) to the four-clause Core Rule: *"Codex decides. Tests arbitrate. Markdown remembers. CAM librarian cites."* — and the three enforcement bullets listed in Requirements §6.1.

---

## 5. Non-Goals

The following are explicitly out of scope for v1. Inclusion here is a contract; adding any of these requires a new PRD revision and user approval.

- **No inline CAM_CAM engine.** No mining, no bandit retraining, no defense chain, no federation, no dashboards in Codex turns.
- **No daemons.** No background processes spawned by the MCP or skills.
- **No model dispatch / agent rotation tooling in v1.** Codex stays on its configured model; rotation belongs to a future methodology if at all.
- **No `cam_match_failure` tool in v1.** Failure-knowledge corpus is 1 row. Deferred to v2 pending corpus growth.
- **No HTTP transport.** stdio only. (`_monolith.py:13794` shows HTTP is unimplemented in the existing MCP; the new MCP does not change that.)
- **No write tools other than `cam_record_outcome`.** No update, no delete, no patch.
- **No silent pattern application above any fitness threshold.** Every applied pattern is visible in skill output with provenance.
- **No mock data, no simulation, no placeholder responses, no cached canned outputs anywhere in the build.** Real corpus, real tool calls, real append-only writes. (Workspace rule, repeated for emphasis.)
- **No "production ready" or "complete" claims.** Tasks always remain; v1 ships when the validation suite passes and the user accepts.
- **No modification of `.codex/rules/default.rules` as part of this methodology.** That file contains plaintext secrets (lines 95, 103, 107–117, 124–146) that require separate rotation; this design must not block on or touch that remediation.
- **No carve-out of the existing 17-tool MCP.** A new thin module is built. The legacy `CAM_CAM/src/claw/mcp_server.py` (never wired to Codex; the phantom contract origin) is **removed** as part of v1 — see the deletion task in `meta/HANDOFF_LATEST.md`.

---

## 6. Requirements

RFC-2119-style verbs: **MUST**, **SHOULD**, **MAY**. Every MUST is testable.

### 6.1 Functional — MCP Surface

| ID | Requirement | Verification |
|---|---|---|
| F-MCP-01 | The new MCP server **MUST** expose exactly four tools: `cam_recall`, `cam_provenance`, `cam_decisions_search`, `cam_record_outcome`. | CI test asserts `len(server.list_tools()) == 4` and the name set is exact. |
| F-MCP-02 | `cam_recall(query, language?, project_context?, k=3)` **MUST** return up to `k` methodologies ranked by `fitness * recency_decay` with full provenance fields populated (`id`, `name`, `fitness_score`, `green_count`, `red_count`, `source_commit_sha`, `source_path`, `notes`, `tags`). | Schema test against pydantic v2 model; row-count test on real DB. |
| F-MCP-03 | `cam_provenance(methodology_id)` **MUST** return the resolvable source row including commit SHA that exists in a real git history (or is recorded as `unresolved` with reason). | Live test resolves SHA via `git cat-file -e`. |
| F-MCP-04 | `cam_decisions_search(query, scope=workspace|repo, k=5)` **MUST** return prior decisions indexed across the workspace, each with `repo`, `file:line`, `commit_sha`, and a one-line summary. | Indexer test; cross-repo recall test on a curated query set. |
| F-MCP-05 | `cam_record_outcome(methodology_id, step_id, result, evidence_ref)` **MUST** append exactly one row to `methodology_bandit_outcomes` and/or `methodology_fitness_log`. Idempotent on `(step_id, methodology_id)`. **MUST NOT** update or delete any prior row. | DB-level test: row count delta == 1 per call; duplicate-key test returns the prior row, not a write. |
| F-MCP-06 | The MCP **MUST** be wired in `.codex/config.toml` under `[mcp_servers.cam_cam]` with stdio transport. | Config parse test; live launch test. |
| F-MCP-07 | The MCP **MUST NOT** register any tool whose name starts with `claw_`. | CI naming test. |
| F-MCP-08 | The MCP **MUST** read from a configurable DB path (default `CAM_CAM/data/claw.db`) and **MUST** use a separate auth token from the existing 17-tool server. | Env-var resolution test. |
| F-MCP-09 | The MCP **MUST** never invoke CAM_CAM mining, bandit retraining, defense chain, federation, or any other heavy subsystem. Imports from `claw.miner`, `claw.bandit_trainer`, `claw.defense_chain`, `claw.federation` are forbidden. | Import-graph test (`importlib` introspection in CI). |

### 6.2 Functional — Skills

| ID | Requirement | Verification |
|---|---|---|
| F-SK-01 | New skill `cam_recall_and_cite` **MUST** be added under `.codex/skills/cam_recall_and_cite/SKILL.md`. It calls `cam_recall`, formats one-line provenance, and refuses to proceed without a resolved SHA. | Skill loads in Codex; integration test on a known query returns a citation line containing a real SHA. |
| F-SK-02 | New skill `rescue_ladder` **MUST** be added. On the **second** consecutive verification failure on the same step, it calls `cam_decisions_search` scoped to the failure family **before** any model rotation, replanning, or `user_asked_for_help` event. | Test harness simulates two failures; transcript shows MCP call between fail-2 and any user-prompt event. |
| F-SK-03 | New skill `outcome_log` **MUST** call `cam_record_outcome` after any verified step that consumed a recalled methodology. Skipping it is a doctrine violation. | Doctrine-conformance test: every recall→verify pair in the transcript has a matching outcome row in the ledger. |
| F-SK-04 | Existing skill `repo_recon` **MUST** be modified to call `cam_decisions_search` once per recon run and surface cross-repo decisions inline. | Diff review; live recon on a target repo produces a "prior decisions" section. |
| F-SK-05 | Existing skill `deepscientist-data-research` **MUST** be rewritten to use only the four new tool names. No `claw_query_memory`, `claw_store_finding`, or other `claw_*` references remain. | `grep -r "claw_" .codex/skills/deepscientist-data-research/` returns zero matches. |
| F-SK-06 | All five skills above **MUST** emit a one-line provenance row in their output schema whenever they apply a methodology. The line **MUST** include: `methodology_id`, `fitness_score`, `green_count`, `red_count`, `source_commit_sha`, `source_path`. | Schema validation test on captured outputs. |
| F-SK-07 | All five skills above **MUST** be silent on turns where they are not invoked. No MCP call, no provenance line, no "I checked the corpus and found nothing relevant" prose. | Negative test: trivial turns (typo fix) produce zero MCP tool calls. |

### 6.3 Functional — Doctrine

| ID | Requirement | Verification |
|---|---|---|
| F-DOC-01 | `.codex/AGENTS.md` **MUST** be appended with the four enforcement clauses: (1) CAM_CAM is consulted as a librarian via MCP, never run inline. (2) No mined methodology may be applied without its provenance row written to `IMPLEMENT.md`. (3) On second consecutive verification failure, `rescue_ladder` runs before the user is asked. (4) After any verified step that used a recalled methodology, `outcome_log` must record the result. | Diff review against `.codex/AGENTS.md`. |
| F-DOC-02 | `.codex/AGENTS.md` **MUST** carry the Core Rule: *"Codex decides. Tests arbitrate. Markdown remembers. CAM librarian cites."* | grep match. |

### 6.4 Functional — UX

| ID | Requirement | Verification |
|---|---|---|
| F-UX-01 | Every applied pattern **MUST** be rejectable in one keystroke (the skill output presents the pattern with an explicit reject affordance documented in `SKILL.md`). | Skill template review. |
| F-UX-02 | Skill output **MUST** answer in the shape of the question. `cam_recall` is not a search engine — it returns at most `k` methodologies with verdict, not a list of candidates to browse. | UX test on the three named scenarios. |
| F-UX-03 | When a methodology was recalled but rejected by the skill (e.g., fitness below a threshold, no SHA resolved), the skill output **MUST** show the anti-pattern: "considered `methodology_id=X` (fitness 0.31, 1 green / 5 red) — rejected." | Captured-output test. |
| F-UX-04 | A `cam.silence(turn|session|repo)` escape hatch **MUST** be honored by all skills (the "5pm Friday bypass"). When silenced, no MCP call is made and no provenance line appears. | Silence test: setting `cam.silence(session)` produces zero MCP calls across a synthetic session. |

### 6.5 Non-Functional

| ID | Requirement | Verification |
|---|---|---|
| NF-01 | **Latency.** `cam_recall`, `cam_provenance`, and `cam_decisions_search` (read tools) **MUST** complete with p95 ≤ 500ms on the live `claw.db`. | Benchmark harness against the real DB on representative queries. |
| NF-02 | **Append-only ledger invariant.** `cam_record_outcome` **MUST NOT** issue any `UPDATE` or `DELETE` against `methodology_bandit_outcomes`, `methodology_fitness_log`, or `methodologies`. | SQL audit log in test mode; static analysis of the writer module. |
| NF-03 | **Test coverage.** The new MCP module and the five new/modified skills **MUST** be covered at >90% line coverage. Gaps **MUST** carry an action plan in this PRD or an explicit user waiver. | `pytest --cov` report committed alongside v1. |
| NF-04 | **Lightness.** New MCP RSS peak **MUST** be ≤25% of the existing 17-tool MCP RSS peak on the same DB. | Side-by-side `ps` / `psutil` measurement under matched load. |
| NF-05 | **No mock data anywhere in the build path.** Tests run against the real `claw.db` (or a hermetic copy of it). No simulated rows, no canned responses, no `Mock()` stubs for the corpus. | Code review; grep for `unittest.mock`, `Mock`, `fake_`, `stub_` in the new module returns zero in non-test contracts. (Mocks of *external network* dependencies are permitted; mocks of the corpus are not.) |
| NF-06 | **No HTTP transport** in v1. stdio only. | Transport flag inspection. |
| NF-07 | **Validation gates between every step.** No phase advances without the prior phase's tests green and provenance audit clean. | CI workflow definition. |
| NF-08 | **Real APIs in tests.** Where an integration test exercises Codex itself, it runs the real Codex CLI against the real MCP. No Codex emulator. | Test harness review. |

---

## 7. UX Principles (Five Invariants)

From the UX brainstorm. Every skill output that touches the MCP MUST honor all five.

1. **One-line provenance with denominator.** The citation is a single line and contains the green/red split. Example: `fitness 0.87, 8 green / 0 red, source: ABXorcist/lib/rate-limit.ts @ abc1234`.
2. **Silent on trivial turns.** If the turn is a typo fix, comment edit, rename, or other non-substantive change, the MCP is not called. No "I checked the corpus and found nothing" prose either.
3. **Rejectable in one keystroke.** Every applied pattern is presented with an explicit reject affordance. The user does not need to draft prose to refuse.
4. **Answer in the shape of the question.** `cam_recall` returns a verdict ("apply pattern X") or a refusal ("no qualifying pattern"). It does not return a browseable list.
5. **Show the anti-pattern.** When a candidate methodology was considered and rejected (low fitness, no SHA, scope mismatch), the rejection is visible in the output with its own one-line provenance. This is what keeps "provenance theater" from setting in.

---

## 8. Success Criteria (Falsifiable Claims)

Validation suite. Each claim has a runnable command and a pass condition. From the Tester brainstorm. Order matters: Claim 0 first, then Provenance, then Lightness, then Cross-Project Learning, then Cold-Start, then Failure Rescue.

| # | Claim | Falsifier (what would prove this false) | Type |
|---|---|---|---|
| **0** | **Codex actually invokes the new MCP** at least once per task where the active skill declares MCP dependency. | A transcript of an in-scope task contains zero calls to `cam_recall`, `cam_provenance`, `cam_decisions_search`, or `cam_record_outcome`. | Binary, transcript-audited |
| 1 | **Provenance:** 100% of applied patterns resolve to a real commit SHA. | Any applied-pattern row whose SHA fails `git cat-file -e`. | Binary |
| 2 | **Lightness:** New MCP peak RSS ≤ 25% of existing 17-tool MCP peak RSS on the same DB. | RSS measurement exceeds the bound. | Quantitative, no time component |
| 3 | **Cross-project learning:** The fitness ledger demonstrably influences round-2 retrieval distribution. | Chi-square test comparing round-2 retrievals against an empty-ledger control fails to reject the null at α=0.05. | Statistical |
| 4 | **Cold-start:** Orientation rubric score on five curated unfamiliar repos improves over the no-MCP baseline. | Baseline score ≥ proposed score on the same rubric. | Comparative, baseline-anchored |
| 5 | **Failure rescue:** ≥60% of curated failures are resolved by `rescue_ladder` without a `user_asked_for_help` event. | Resolution rate < 60% on the curated set. | Comparative |

**Baseline requirement.** Claims 3, 4, and 5 require baseline measurements captured **before** any methodology code lands. The five-repo orientation set and the curated-failure set must be fixed in writing first.

---

## 9. Risk Register

Top seven risks, drawn from the brainstorm. Each has a mitigation. None of the mitigations include a date.

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | **Phantom contract recurrence.** A skill ships referencing a tool that isn't wired (the original sin at `.codex/skills/deepscientist-data-research/SKILL.md:25,65,135,162,168`). | High | High | CI test that scans all `SKILL.md` files for tool names and asserts every name resolves to a registered tool in `.codex/config.toml`. Fails the build on phantom reference. |
| R-2 | **Corpus rot.** Live `claw.db` drifts away from the assumptions in this PRD (e.g., `bandit_outcomes` starts growing without us, or lifecycle states change). | Medium | High | Pre-flight check on every CI run: the corpus assumption query in `HANDOFF_LATEST.md` must produce the same shape (or the new shape is reviewed and the PRD updated). |
| R-3 | **Pattern monoculture.** `cam_recall` returns the same top-fitness pattern for every adjacent query, narrowing the developer's solution space. | Medium | Medium | Diversity-aware ranker: tie-break on `source_repo` and `tags` so consecutive recalls in the same session don't repeat. Logged in `cam_recall` output. |
| R-4 | **Provenance theater.** Citation-shaped strings appear in skill output but the SHA does not resolve, or the path is invented. | Medium | High | F-MCP-03 requires `cam_provenance` to call `git cat-file -e` against the recorded SHA. Failure marks the methodology `unresolved` and skills MUST NOT apply it. |
| R-5 | **Secrets exposure in `.codex/rules/default.rules`.** Plaintext `OPENROUTER_API_KEY` / `GOOGLE_API_KEY` at lines 95, 103, 107–117, 124–146. | Already happened | High | **Out of scope for this PRD.** Flagged for separate remediation. This methodology must not require modifying `default.rules`. Tracked in `HANDOFF_LATEST.md` → Known Issues. |
| R-6 | **5pm Friday bypass.** Developer disables the methodology to ship and never re-enables it. | High | Medium | The `cam.silence(turn|session|repo)` escape hatch is the *sanctioned* form of bypass; using it logs a one-line entry to `DECISIONS.md`. There is no other off switch, so silent disablement is visible. |
| R-7 | **Mocking temptation.** Under schedule pressure, a contributor stubs the corpus or fakes outcome rows to make tests green. | Medium | High | NF-05 prohibits mock data in the build path; CI grep for `Mock(`, `fake_`, `stub_corpus` in non-external-network contexts fails the build. Workspace rule: mock requires explicit approval with rationale and immediate replacement plan. |

---

## 10. Open Questions

Items the brainstorm flagged but did not lock. Each must be answered before v1 is accepted.

1. **Naming.** "Codex-CAM Methodology" is the working name. User has not objected; not yet locked.
2. **The "889 corpus."** README claims 889 methodologies; live DB has 107. Where does the 889 figure actually live — another drive, an archive, a federation peer, or is it aspirational? Not blocking; design is anchored to honest 107.
3. ~~**MCP module location.**~~ **Resolved 2026-05-17:** the new MCP module lives in a **separate sibling repository** at `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology/` as the top-level package `claw_codex_mcp` (not the `claw.` namespace inside CAM_CAM). Pydantic schemas and DB access helpers are duplicated where needed rather than shared — the two repos stay independently versioned.
4. **Telemetry / observability.** What does the new MCP log, where, and at what level? Defer to Section 6 of the design dialogue.
5. **Auth token strategy.** Separate token from the existing 17-tool MCP (F-MCP-08) — but generated how and stored where? Must not require touching `.codex/rules/default.rules` (R-5).
6. **`cam_decisions_search` indexer scope.** Does the indexer cover all 80 trusted projects under `/Volumes/WS4TB/`, or a curated subset? Performance and signal/noise tradeoff.
7. **Fitness ledger schema.** `methodology_bandit_outcomes` and `methodology_fitness_log` exist as empty tables. Are their current schemas adequate, or does `cam_record_outcome` need a new append-only table?
8. **Diversity-aware ranker policy** (R-3). Exact tie-break rule for `cam_recall` to avoid monoculture is not yet specified.
9. **`outcome_log` deferral.** What is the policy when verification is inconclusive (e.g., flaky test)? Skip the write, or write with `result=inconclusive`?
10. **Repo SHA resolution across drives.** Some methodologies in `claw.db` may cite SHAs in repos that are not currently checked out under `/Volumes/WS4TB/`. How is `cam_provenance` expected to behave — `unresolved` with reason, or look-aside resolution?

---

## 11. Out of Scope (v1) / Deferred to v2

Captured explicitly so future revisions know what was held back and why.

| Item | Why deferred | Re-evaluation trigger |
|---|---|---|
| `cam_match_failure` tool | `failure_knowledge` corpus is 1 row. One query, one possible answer. | Failure corpus grows enough to support meaningful matching (re-query the DB). |
| Federation tools | Heavy; cross-machine; doctrine-violating to run inline. | A separate methodology proposal. |
| Dashboards | Heavy; not a Codex-turn concern. | Out-of-band tooling lives with CAM_CAM. |
| Model dispatch / agent rotation | Not a librarian concern; risks coupling the methodology to model availability. | A separate methodology proposal. |
| Write tools beyond `cam_record_outcome` | Surface bloat; doctrine-violating mutability. | Never, unless boundary rule itself is revisited. |
| HTTP transport | Existing MCP also has no HTTP (`_monolith.py:13794`); stdio is sufficient for Codex CLI. | Out-of-process consumer requires it. |
| Modifying `.codex/rules/default.rules` to remove leaked secrets | Separate security remediation; entangling it with this methodology would block both. | Rotation of leaked keys is complete. |
| Carving a profile out of the existing 17-tool MCP | User-locked decision: build new. | None — locked. |
| Back-compat for `claw_*` tool names in skills | User-locked decision: rewrite `deepscientist-data-research`. | None — locked. |
| "889 methodologies" claim in any new surface | Stale; not supported by live query. | Live query supports a number ≥ 889. |
| `awesome-codex-subagents/` integration via `install_codex_subagents.sh` | Referenced sibling directory is missing from the checkout. | Source is restored or the script is removed. |
| Cleanup of empty `codex-primary-runtime/SKILL.md` | Out of scope; flag for cleanup elsewhere. | Maintenance pass on the skill bundle. |

---

## 12. References

| File | Why it matters |
|---|---|
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/HANDOFF_LATEST.md` | Full session context: verified facts, user-locked decisions, sub-agent findings index, corpus query results. The canonical source this PRD rests on. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/HANDOFF_2026-05-17.md` | Dated copy of the same handoff. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md` | Doctrine (current Core Rule): *"Codex decides. Tests arbitrate. Markdown remembers. CAM librarian cites."* — established via F-DOC-02. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml` | MCP server registry. Only `context7` is wired today. F-MCP-06 adds `[mcp_servers.cam_cam]`. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/deepscientist-data-research/SKILL.md` | Phantom-contract skill. Lines 25, 65, 135, 162, 168 reference `claw_query_memory` and `claw_store_finding`. Rewritten under F-SK-05. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/repo_recon/SKILL.md` | Existing skill modified under F-SK-04 to call `cam_decisions_search`. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/rules/default.rules` | Contains plaintext API keys at lines 95, 103, 107–117, 124–146. **Out of scope** for this methodology (R-5); must not be modified by it. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/mcp_server.py` | **The bloat being escaped.** Legacy 17-tool MCP (was registering at lines 1689–1779). Never wired to Codex. **Removed as part of v1.** |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db` | The corpus. 107 methodologies (95 viable / 12 embryonic), 96 usage-log rows, 0 bandit outcomes, 0 fitness-log rows, 1 failure-knowledge row. Source of truth for every claim in §2. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/README.md` | Stale: claims 889 methodologies at lines 11, 119, 143, 388, 459. Not modified by this methodology; flagged in R-2 and Open Question 2. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/docs/MCP_INTEGRATION_GUIDE.md` | Stale: documents 5 tools; implementation has 17. Out of scope for this PRD. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/_monolith.py` | HTTP transport unimplemented at line 13794; informs NF-06 (stdio only). |
| Workspace policy: `/Volumes/WS4TB/CLAUDE.md` | No mock / no placeholder / no simulation rule; >90% coverage target; validation gates between every step; no time or cost estimates. Baked into NF-03, NF-05, NF-07. |
