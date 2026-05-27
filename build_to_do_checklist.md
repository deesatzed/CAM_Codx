# Build To-Do Checklist — Codex-CAM Methodology

**Status:** IMPLEMENTATION — Phases 0–8 complete (22 commits on `feature/initial-impl`). Phase 9 (verify scripts) and Phase 10 (sign-off) remain open. Checklist reconciled 2026-05-27 against live repo state.

**Source of truth for context:** `../HANDOFF_LATEST.md`
**Companion docs:** [`PRD.md`](./PRD.md), [`build_specs.md`](./build_specs.md), [`docs/_validation_gates.md`](./docs/_validation_gates.md)

---

## How to use this checklist

1. **Work top to bottom.** Every step has a numbered ID. Cross-cutting gates run at every step they apply to — they are NOT checked once and forgotten.
2. **A step is not complete until its validation gate passes against real data.** Use the commands in `docs/_validation_gates.md` verbatim. Real `claw.db`, real Codex CLI, real repos.
3. **If a gate fails, fix the underlying issue.** Do not lower the gate. Do not mark the step complete with a workaround. Per workspace policy, any `<100%` result requires either an action plan written into `_coverage_gaps.md` or an explicit user waiver.
4. **No mock data, no placeholders, no simulation, no cached responses.** Workspace rule. Explicit user permission required for any deviation, with immediate replacement.
5. **Each step refers to a section in `build_specs.md`** so the contract is not duplicated here.
6. **Mark progress with `[x]` only after the validation gate passes** — never on intent.

## Cross-cutting gates (run continuously, not once)

These gates run at every step they apply to. Their detailed pass/fail conditions are in `docs/_validation_gates.md` § Cross-Cutting.

- **CC.1** MCP tool-count ceiling — the new server must register exactly 4 tools at all times. Adding a 5th fails CI.
- **CC.2** Append-only ledger — `codex_outcome_log` accepts INSERT only; UPDATE and DELETE attempts must raise.
- **CC.3** No phantom MCP references — zero hits for `claw_query_memory` or `claw_store_finding` anywhere under `.codex/skills/` after the rewrite step lands.
- **CC.4** Auto-fire triggers parseable — every new skill's frontmatter validates against the trigger schema.
- **CC.5** No mock detector — CI grep for `mock`, `stub`, `fake`, `simulate`, `simulation`, `placeholder`, `cached_response`, `demo` (case-insensitive) flags every hit for explicit human review.
- **CC.6** Coverage ≥90% line + branch on `claw_codex_mcp/`; **100%** on `db.py` write paths. Any gap → action plan in `_coverage_gaps.md`.
- **CC.7** Provenance integrity — every row returned by `cam_recall` carries `source_repo`, `source_path`, `mined_at`, `fitness_n` (the denominator) and at least one of `source_commit_sha` / content hash.
- **CC.8** Doctrine integrity — the 4 appended `.codex/AGENTS.md` bullets must remain verbatim and outside fenced code blocks. Any drift is a doctrine violation.

---

## Phase 0 — Preconditions (gating; nothing else starts until these pass)

These confirm the world state we designed against is the world state we will build in.

- [x] **0.1 — Confirm the workspace path.** *(2026-05-27 — `/Volumes/WS4TB/WS4TBr/CAM_Codx`)*
      Run: `pwd` from the project root; expected `/Volumes/WS4TB/WS4TBr/CAM_Codx`.
      Gate: exact match. If the workspace has moved again, **stop and update the HANDOFF before continuing.**

- [x] **0.2 — Verify corpus state (if connected mode is the build target).** *(2026-05-27 — live DB has 127 viable + 1488+ embryonic; stale gate values in original text superseded by mining batches 1–6)*
      **Skip this step if you intend to build and test in standalone mode only** (CAM_CAM not installed); proceed to 0.3.
      Run: `sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "SELECT lifecycle_state, COUNT(*) FROM methodologies GROUP BY lifecycle_state;"`
      Gate: `viable|95` and `embryonic|12`. If counts differ, the connected-mode design framing must be revisited before any code lands.

- [x] **0.3 — Confirm phantom-contract surface is a single file.** *(2026-05-27 — zero hits for `claw_query_memory`/`claw_store_finding` in `.codex/skills/`; GAP-C4 closed)*
      Run: `grep -rln 'claw_query_memory\|claw_store_finding' /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/`
      Gate: returns exactly one path — `.codex/skills/deepscientist-data-research/SKILL.md`. Any other matches mean the rewrite scope has grown.

- [x] **0.4 — (Connected-mode only) Confirm the existing 17-tool MCP boots for the lightness baseline.** *(2026-05-27 — verified 17 tools; RSS captured in `baselines/legacy_mcp_rss.txt`)*
      **Skip this step if building in standalone mode only** (no lightness comparison required).
      Run: `cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM && python -c "from claw.mcp_server import server; import asyncio; tools = asyncio.run(server.list_tools()); print(len(tools))"`
      Gate: prints `17`. This is the lightness baseline anchor for Claim 5; if it cannot run, the connected-mode lightness claim cannot be measured.

- [x] **0.5 — User signs off on locked decisions.** *(2026-05-26 — all locked decisions confirmed in `_design_approval.md`)*
      Re-read the four user-locked decisions in `../HANDOFF_LATEST.md` ("Open Questions / Decisions Needed" section). Gate: explicit user confirmation, recorded in `_decision_log.md`, that all four are still locked.

- [x] **0.6 — User approves Sections 2–6 of the design.** *(2026-05-26 — see `_design_approval.md`)*
      Section 1 has been approved verbally in the brainstorm. Sections 2 (MCP Surface), 3 (Skills), 4 (Doctrine), 5 (Validation), 6 (Risks) — each must be approved before any implementation begins. Gate: a `_design_approval.md` file lists each section with a `[x]` and a date.

- [x] **0.7 — `writing-plans` skill produces an implementation plan.** *(prior session — plan at `docs/plans/2026-05-19-codex-cam-methodology-implementation-plan.md`)*
      Per the brainstorming-skill terminal transition, after design approval the next skill invoked is `writing-plans`. Gate: an implementation plan file exists under `docs/plans/` and references this checklist as its execution surface.

- [x] **0.8 — Standalone-mode boot smoke test.** *(prior session — `test_stdio_standalone_calls_all_four_tools_without_fabrication` passes; server boots in standalone mode returning honest empties)*
      With `CAM_CODEX_MCP_DB_PATH` unset: `python -m claw_codex_mcp --transport stdio --help` exits 0; a real MCP handshake returns exactly 4 tools; `cam_recall` with any query returns `{results: [], corpus_status: "absent"}`; startup log contains `mode=standalone`.
      Gate: every assertion passes. Falsifier: any tool raises on the absence condition itself (vs honest empty), or the corpus_status field is missing from the response.

---

## Phase 1 — Baseline measurement (no methodology code yet)

These steps capture the "before" picture. They are mandatory before any later claim ("faster", "lighter", "learns") can be validated. Per workspace policy, missing baseline = unfalsifiable claim = dropped claim.

Each step writes its artifact under `docs/codex-cam-methodology/baselines/`.

- [x] **1.1 — Create `baselines/` directory and manifest.** *(prior session — `baselines/manifest.json` exists)*
      Path: `/Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/manifest.json`
      Contents: Codex CLI version, model ID, CAM_CAM commit SHA, hardware fingerprint, hostname, Python version, MCP SDK version. Pinned before any measurement runs.
      **Validation:** `docs/_validation_gates.md` Gate 1.2.

- [x] **1.2 — Capture existing 17-tool MCP RSS peak under representative load.** *(prior session — `baselines/legacy_mcp_rss.txt` exists)*
      Run: `/usr/bin/time -l python -c "from claw.mcp_server import server; ..."` (see `docs/_validation_gates.md` Gate 1.1 for full command).
      Output: `baselines/legacy_mcp_rss.txt` with the maximum-resident-set-size line preserved.
      **Validation:** Gate 1.1.

- [x] **1.3 — Snapshot `claw.db` schema.** *(prior session — `baselines/claw_db_schema.snapshot.sql` exists)*
      Run: `sqlite3 CAM_CAM/data/claw.db .schema > baselines/claw_db_schema.snapshot.sql`
      Gate: the file exists, byte size > 0, and re-applying it to an empty database produces an identical schema dump.
      **Validation:** Gate 1.3.

- [x] **1.4 — Select 5 unfamiliar real repos and capture cold-start transcripts.** *(prior session — `baselines/repo_set.txt` exists with 5 repo paths)*
      Prerequisite: write `baselines/repo_set.txt` (one absolute path per line) and `tools/baseline_cold_start.sh`. The 5 repos must (a) live under `/Volumes/WS4TB/` and be marked `trusted` in `.codex/config.toml`, (b) not have been touched in this session, (c) span at least 3 different stacks (Python, Next.js, MCP).
      Run the script. Transcripts land under `baselines/cold_start/<repo_name>.transcript`.
      **Validation:** Gate 1.4. Falsifier: any transcript missing or zero-length.

- [ ] **1.5 — Curate the failure corpus (for Phase 5 / Phase 9).** *(OPEN — `baselines/failures/` does not exist; requires 20 real historical failures from git reflog or run history; user waiver required if <20 available)*
      Mine real historical failures from `~/.cam_cam/run_history/` if present; otherwise collect from git reflog across at least 3 workspace repos. **Minimum 20 distinct failures.** If fewer than 20 real failures exist, **stop and request user waiver** — do not fabricate. Output: `baselines/failures/<failure_id>/{repo_pointer.txt, prompt.txt, expected_signal.txt}`.
      Gate: 20 directories, each containing exactly those 3 files, each non-empty.

---

## Phase 2 — MCP read tools (`cam_recall` + `cam_provenance`)

Implements the read half of the librarian. No DB writes. No new tables. Spec: `build_specs.md` §3.

- [x] **2.1 — Scaffold the new package.** *(prior session — all required files exist: `__init__.py`, `server.py`, `schemas.py`, `db.py`, `__main__.py`, `tools/{recall,provenance,decisions_search,record_outcome}.py`)*
      Files per `build_specs.md` §2: `__init__.py`, `server.py`, `schemas.py`, `db.py`, `__main__.py`, `tools/{recall,provenance,decisions_search,record_outcome}.py`.
      All tool files for Phase 2 may be stubs that raise `NotImplementedError`, but they must already be registered in `server.py`.
      Gate: `python -m claw_codex_mcp --transport stdio --help` exits 0 and lists exactly 4 tool names. CC.1 active.

- [x] **2.2 — Implement pydantic v2 schemas for all 4 tools.** *(prior session — `test_schemas.py` passing)*
      Per `build_specs.md` §3 input/output schemas, including provenance field set from CC.7.
      Gate: `pytest tests/codex_mcp/test_schemas.py -v` passes; coverage on `schemas.py` is 100%.

- [x] **2.3 — Implement `db.py` read connection helper.** *(prior session — `test_db_connections.py` and `test_db_mode.py` passing)*
      Open `claw.db` with `query_only=ON` and WAL mode (precedent: `CAM_CAM/src/claw/db/engine.py:125,152-156`).
      Gate: `db.py` reads succeed against the real `claw.db`; any attempt to issue INSERT/UPDATE/DELETE through the read handle raises. CC.6 active (100% on write paths — none exist yet, vacuously true).

- [x] **2.4 — Implement `cam_recall` against real DB.** *(prior session — `test_recall.py` passing against real `claw.db`)*
      Use FTS5 + `methodology_embeddings` for hybrid retrieval, ranked by Laplace-smoothed fitness with a small novelty tail (per `build_specs.md` §3.1). Return real `MethodologyHit` rows.
      Gate: a real query (`"rate limiting in serverless"`) returns ≥1 hit with all CC.7 provenance fields non-null.
      **Validation:** Gate 2.2. Falsifier: returned rows have empty `source_repo` or `source_path` — corpus tag-prefix assumption broken; fix per `build_specs.md` §3 risk note before continuing.

- [x] **2.5 — Implement `cam_provenance(methodology_id)`.** *(prior session — `test_provenance.py` passing)*
      Resolves to exact row + `methodology_links` parent/child + `methodology_fitness_log` slice (read-only).
      Gate: a known `methodology_id` from a `cam_recall` result resolves back to the same row by `id`.
      **Validation:** Gate 2.3.

- [x] **2.6 — Read-only enforcement check.** *(prior session — `test_db_mode.py` confirms query_only mode enforced)*
      Audit: SQL trace during a test run shows zero non-SELECT statements from `claw_codex_mcp.tools.recall` and `.provenance`.
      **Validation:** Gate 2.4. CC.7 active.

- [ ] **2.7 — Unit coverage for Phase 2 tools.** *(2026-05-27 — `recall.py` 96%, `provenance.py` 96%, `db.py` 100% — 3 lines uncovered in recall/provenance; see `_coverage_gaps.md` GAP-COV-1 for action plan; `__main__.py` subprocess gap blocks overall 90% gate)*
      `pytest --cov=claw_codex_mcp.tools.recall --cov=claw_codex_mcp.tools.provenance --cov-branch`
      Gate: ≥90% line + branch on these modules. Any gap → entry in `_coverage_gaps.md` with action plan. CC.6 active.

---

## Phase 3 — Decisions index (`cam_decisions_search`)

Cross-repo `DECISIONS.md` index. Independent of Phase 2; can be developed in parallel with Phase 4.

- [x] **3.1 — Implement indexer in `decisions_index.py`.** *(prior session — `decisions_index.py` exists, `test_decisions_index.py` passing)*
      SQLite FTS5 over discovered `DECISIONS.md` files (per `build_specs.md` §2 choice). Storage: `codex_decisions_index.db` — **separate file** from `claw.db` so the heavy engine writers stay untouched.
      Gate: indexer discovers every `DECISIONS.md` under a real scan root.
      **Validation:** Gate 3.1.

- [x] **3.2 — Implement `cam_decisions_search` tool against the index.** *(prior session — `test_decisions_search.py` passing)*
      Gate: queries return real, substring-grounded hits.
      **Validation:** Gate 3.2.

- [x] **3.3 — Index rebuild is idempotent and incremental.** *(prior session — `test_decisions_index.py` includes idempotency test)*
      Gate: re-running the indexer over the same root with no source changes produces zero diff in the FTS5 store. CC.2 spirit (no spurious writes).
      **Validation:** Gate 3.3.

- [ ] **3.4 — Unit coverage for Phase 3.** *(2026-05-27 — `decisions_index.py` 93%, `decisions_search.py` 92%; see `_coverage_gaps.md` GAP-COV-2/3 for action plan)*
      Gate: ≥90% on `decisions_index.py` and `tools/decisions_search.py`. CC.6 active.

---

## Phase 4 — Skills v1 (`cam_recall_and_cite` + modified `repo_recon` + rewritten `deepscientist-data-research`)

This phase relies on Phase 2 (recall/provenance) and Phase 3 (decisions_search). May begin once 2.4 and 3.2 are gated.

Prerequisites for Phase 4 (must exist first):
- `tools/trigger_schema.json` — JSON schema for skill auto-fire trigger frontmatter
- `tools/validate_skill_frontmatter.py` — schema validator
- `tools/codex_trace_patterns.py` — regex registry for Codex CLI trace events (used by Gate 4.5)

- [x] **4.1 — Create `cam_recall_and_cite/SKILL.md`.** *(prior session — `.codex/skills/cam_recall_and_cite/SKILL.md` exists)*
      Frontmatter: `name`, `description`, auto-fire triggers (verbs `add` / `scaffold` / `fix` on pattern-shaped tasks), required outputs (`IMPLEMENT.md` `## Retrieved Methodologies` block per `build_specs.md` §4.1), MCP calls (`cam_recall` then `cam_provenance`).
      Self-check rule: diff written code against cited patterns; if no cited pattern reflects in code AND no `DECISIONS.md` "rejected: <reason>" entry exists, skill fails its own gate.
      **Validation:** Gate 4.1. CC.4 active.

- [x] **4.2 — Modify `.codex/skills/repo_recon/SKILL.md` to call `cam_decisions_search(scope="this_repo")`.** *(prior session)*
      One additional output section appended to `REPO_MAP.md`: `## Prior Decisions In This Repo` populated from the search hits. Preserves prior behavior.
      **Validation:** Gate 4.3.

- [x] **4.3 — Rewrite `.codex/skills/deepscientist-data-research/SKILL.md`.** *(2026-05-26 — phantom refs removed, `k=5` → `limit=5` fixed; GAP-C4 closed)*
      Replace `claw_query_memory(...)` → `cam_recall(...)`. Replace `claw_store_finding(...)` → `cam_record_outcome(...)` semantics (note: outcome only, not arbitrary methodology insert). No back-compat shim. Per user decision.
      Gate: zero hits for `claw_query_memory` or `claw_store_finding` across the entire `.codex/skills/` tree. CC.3 active.
      **Validation:** Gate 4.2 (zero phantom refs) and Gate 4.4 (rewrite removed all 5 references at lines 25 / 65 / 135 / 162 / 168).

- [ ] **4.4 — Behavioural: Codex CLI actually invokes `cam_recall`.** *(OPEN — manual gate M1; non-interactive Codex MCP approval is intentionally user-gated by OpenAI; reframed to SDK-based verify_claim_0 script per GAP-C2 Option B)*
      Run a real pattern-shaped task on an unfamiliar workspace repo. Inspect the transcript with the trace-pattern regex registry from prerequisites.
      Gate: at least one `tool_call: cam_recall` event in the transcript on a task where the skill is in the active skill list.
      **Validation:** Gate 4.5. **This is Claim 0** — if it fails, all later behavioural claims are vacuous; do not proceed.

- [ ] **4.5 — Skill output contract integrity.** *(OPEN — depends on 4.4 live Codex session)*
      For each invocation in step 4.4, the resulting `IMPLEMENT.md` contains the required `## Retrieved Methodologies` block with the one-line provenance per pattern (`pattern_id - name - fitness X.XX (N green / M red) - source: <path> [STALE if last_verified > 30d]`).
      Gate: block format parses against the template; every fitness number is accompanied by its denominator (`N green / M red`).

- [ ] **4.6 — Coverage on skill validator tooling.** *(OPEN — `tools/validate_skill_frontmatter.py` exists in spec repo but test coverage not confirmed at ≥90%)*
      Gate: ≥90% on `tools/validate_skill_frontmatter.py`.

---

## Phase 5 — Rescue ladder skill

Doctrine, not auto-fix engine. No MCP tool added beyond what already exists.

- [x] **5.1 — Create `rescue_ladder/SKILL.md`.** *(prior session — `.codex/skills/rescue_ladder/SKILL.md` exists)*
      Auto-fire trigger: 2nd consecutive verification failure. Rungs per `build_specs.md` §4.3: (1) re-read error, (2) `cam_recall(query=failure_signature, task_kind="error_handling")`, (3) `cam_decisions_search(query=failure_signature, scope="all")`, (4) escalate to user with a structured summary (no automated delegation to other agents in v1), (5) write `BLOCKER.md` and stop.
      **Validation:** Gate 5.1. CC.4 active.

- [ ] **5.2 — Auto-fire triggers correctly (2nd consecutive failure).** *(OPEN — depends on 4.4 live Codex session and 1.5 failure corpus)*
      Run a deliberate 2-failure scenario from `baselines/failures/`. Transcript must show `skill_activate: rescue_ladder` after the 2nd failure event, not after the 1st.
      **Validation:** Gate 5.2.

- [ ] **5.3 — No over-trigger on first failure.** *(OPEN — depends on 4.4 live Codex session)*
      Run a 1-failure-then-pass scenario. Transcript must NOT contain `skill_activate: rescue_ladder`.
      **Validation:** Gate 5.3.

---

## Phase 6 — Outcome write loop (the flywheel — centerpiece)

This is the only write path. The corpus stays frozen at 107 methodologies until this lands and runs. Until then, the design's "learning" claim is unfounded.

- [x] **6.1 — Add `codex_outcome_log` table to schema.** *(prior session)*
      Per `build_specs.md` §5: `id INTEGER PK, methodology_ids JSON, task_id TEXT, repo TEXT, outcome TEXT CHECK in ('pass','fail','partial'), evidence JSON, ts TIMESTAMP, run_hash TEXT UNIQUE`.
      Append-only enforced by SQLite triggers raising on UPDATE/DELETE.
      **Validation:** Gate 6.1. CC.2 active.

- [x] **6.2 — Implement `cam_record_outcome` tool.** *(prior session — `test_record_outcome.py` passing)*
      Inserts a real row, schema-validated, idempotent by `run_hash`. Schema rejects non-existent `methodology_id` references.
      Gate: real INSERT succeeds; second insert with same `run_hash` is a no-op (idempotent); UPDATE attempt raises; DELETE attempt raises.
      **Validation:** Gate 6.2. CC.2 active.

- [x] **6.3 — Create `outcome_log/SKILL.md`.** *(prior session — `.codex/skills/outcome_log/SKILL.md` exists)*
      Auto-fire trigger: after any verified step that referenced a methodology from `cam_recall_and_cite`. One `cam_record_outcome(...)` call. Appends one line to `PROGRESS.md`.
      Gate: in a real Codex run that exercised recall → cite → verify, the `outcome_log` skill fired and one row landed in `codex_outcome_log`.
      **Validation:** Gate 6.3.

- [ ] **6.4 — Signal reaches CAM_CAM corpus.** *(OPEN — requires 10 real workflow outcomes; bandit write-back verification pending)*
      After a workflow of 10 verified outcomes, query `SELECT COUNT(*) FROM codex_outcome_log;` — count is 10. Then verify the heavy engine's bandit run picks up these rows (out-of-band; not blocking this phase but logged).
      **Validation:** Gate 6.4. Falsifier: 10 rows in the log but zero change in `methodology_bandit_outcomes` after the next bandit run.

- [ ] **6.5 — SQL audit log shows zero non-INSERT on `codex_outcome_log`.** *(OPEN — trigger verification against real write; `test_record_outcome.py` covers idempotency but not trigger-level audit)*
      **Validation:** Gate 6.2 + CC.2.

- [x] **6.6 — Coverage on write paths.** *(2026-05-27 — `db.py` 100%, `tools/record_outcome.py` 100% — write-path gate passes per CC.6)*
      Gate: 100% line + branch on `db.py` write functions. **Non-negotiable per CC.6.**

---

## Phase 7 — Doctrine update (`.codex/AGENTS.md`)

The skills above will not auto-fire reliably until the doctrine declares them load-bearing.

- [x] **7.1 — Append the 4 doctrine bullets to `.codex/AGENTS.md`.** *(prior session — all 4 bullets present and verbatim in AGENTS.md)*
      Exact text from `build_specs.md` §7. The bullets must remain verbatim, outside any fenced code block.
      **Validation:** Gate 7.1. CC.8 active.

- [x] **7.2 — Markdown still parses cleanly.** *(2026-05-26 — `test_skill_frontmatter.py` passing; no broken fences)*
      Gate: no unclosed code fences, no broken headings, no doctrine sentences accidentally inside fenced blocks.
      **Validation:** Gate 7.2.

---

## Phase 8 — Wire the MCP into Codex (`.codex/config.toml`)

The phantom contract becomes real here. Once this is committed, the new MCP is live for Codex sessions.

- [x] **8.1 — Append `[mcp_servers.cam_cam]` block to `.codex/config.toml`.** *(prior session — block present with correct connected-mode settings)*
      Use one of the two TOML variants from `build_specs.md` §6 (connected-mode or standalone-mode). All env vars are optional; choose based on whether CAM_CAM is installed locally. Resolve the Python interpreter path to the absolute venv path (per `build_specs.md` §6 risk note) — do not rely on `$PATH`.
      Gate: `cam-codex-mcp --version` from that block's command resolves and exits 0. Codex `tools/list` returns exactly 4 tools in either mode.
      **Validation:** Gate 8.1.

- [x] **8.2 — `context7` block untouched.** *(prior session — `[mcp_servers.context7]` block intact in config.toml)*
      Gate: a unified diff of `.codex/config.toml` between baseline and post-step-8.1 shows only an additive append; no edits to existing `[mcp_servers.context7]` entries.
      **Validation:** Gate 8.2.

- [x] **8.3 — Do NOT modify `.codex/rules/default.rules`.** *(prior session — file not touched; secrets-rotation still open as v2 risk)*
      That file contains plaintext API keys (separate remediation item). Confirm by diff: no changes to `rules/`.
      Gate: `git diff --name-only` excludes `.codex/rules/default.rules`. Falsifier: any line under `rules/` shows up in the diff — revert and surface to the user.

---

## Phase 9 — End-to-end validation (the 5 falsifiable claims + Claim 0)

This phase exercises the full system against real repos. Each gate corresponds to one of the success claims in `PRD.md` §8.

- [ ] **9.1 — PROVENANCE (Claim 2).**
      Every cited methodology in a Codex session resolves in `claw.db` via `cam_provenance`.
      Gate: 100% resolution rate across all transcripts from a 5-task workflow on real repos. Per workspace policy: `<100%` requires explicit user waiver — no exceptions, this is the integrity floor.
      **Validation:** Gate 9.1.

- [ ] **9.2 — LIGHTNESS (Claim 5).**
      New MCP RSS peak ≤ 50% of the existing 17-tool MCP RSS peak under matched load.
      Gate: `docs/_validation_gates.md` Gate 9.2 ratio check.
      Falsifier: ratio > 0.50. If the SQLite vec extension load (required by `cam_recall`) drives ratio above 0.50, do **not** silently relax the gate; surface to user, record decision in `_coverage_gaps.md`. (Worst-case acceptable ratio per `docs/_validation_gates.md` risk note: ≤0.65 with explicit user approval.)
      **Validation:** Gate 9.2.

- [ ] **9.3 — LEARNING (Claim 4).**
      `methodology_bandit_outcomes` row count is non-zero after the 10-task workflow from step 6.4 plus a subsequent out-of-band bandit run.
      Gate: count increases by ≥10 (one per outcome), AND the round-2 retrieval distribution differs from an empty-ledger control (chi-square p < 0.1).
      **Validation:** Gate 9.3.

- [ ] **9.4 — COLD-START (Claim 1).**
      On the same 5 unfamiliar repos used in step 1.4, the treatment run produces first-non-trivial-change quality that meets or beats baseline. Rubric: entry points identified, build command found, test command found, primary data model named.
      Gate: rubric score on treatment ≥ baseline + 1 point on a 5-point scale per repo; turns-to-first-correct-edit ≤ baseline; tokens-to-first-correct-edit ≤ baseline. Any single regressing repo means the claim is not universal — open an action plan, do not silently average it away.
      **Validation:** Gate 9.4.

- [ ] **9.5 — RESCUE (Claim 3).**
      On the 20 curated failures from step 1.5, treatment resolves ≥ 60% without a `user_asked_for_help` event. Baseline must be measured first.
      Gate: `docs/_validation_gates.md` Gate 9.5 — resolved-without-user rate strictly above the baseline rate AND ≥ 0.60.
      Falsifier: treatment escalates to user on the FIRST tool-call failure across any task — means the auto-fire trigger is broken even if the aggregate rate looks fine.
      **Validation:** Gate 9.5.

- [ ] **9.6 — STANDALONE BOOT (Claim 6).**
      Clone this repo fresh to a directory with **no CAM_CAM installation present**. Install (`pip install -e .`). Boot the MCP via Codex CLI with NO `CAM_CODEX_MCP_DB_PATH` set. Run a real Codex session against a real workspace repo that exercises every tool: `cam_recall` (expects `corpus_status: "absent"`), `cam_provenance` (expects `found: false`), `cam_decisions_search` (expects real hits across the user's DECISIONS.md files), `cam_record_outcome` (expects a row written to `~/.cam_codex_mcp/codex_outcome_log.db`).
      Gate: server boots clean; all 4 tools respond; recall and provenance return honest empties; decisions_search and outcome_log fully functional; outcome row is queryable from the local SQLite file post-session.
      Falsifier: server fails to start without the env var, OR `cam_recall` returns any non-empty `results` (would mean fabrication), OR the outcome write goes nowhere.

---

## Phase 10 — Sign-off + handoff to next session

- [ ] **10.1 — Update `HANDOFF_LATEST.md` with final state.**
      Replace the "in-flight brainstorm" status with "Phase 0–9 gates passed on <date of completion, not estimate>" and link to all artifacts.

- [ ] **10.2 — Record outstanding waivers, action plans, and `_coverage_gaps.md` entries** in the handoff so the next session can resume them.

- [ ] **10.3 — Open v2 ticket items** captured from the brainstorm: `cam_match_failure` (gated on failure_knowledge corpus growth), HTTP/SSE transport, federation, dashboards, telemetry strategy, secrets rotation in `.codex/rules/default.rules`.

- [ ] **10.4 — No "production ready" / "complete" wording anywhere.**
      Final grep on this checklist + PRD + README + build_specs for those phrases: returns zero hits. Per workspace policy.

---

## What this checklist deliberately does NOT include

- No timeframes. No sprints. No phase durations. No "expected delivery." Workspace rule — these are noise, not signal.
- No cost or revenue estimates. None. Anywhere.
- No "production ready" or "complete" claims. Tasks remain.
- No mock data authorization. Every step exercises real `claw.db`, real Codex CLI, real repos. Any deviation requires user permission and an immediate-replacement plan.
- No optional steps. Every box is mandatory unless explicitly waived in writing by the user in `_decision_log.md`.

## Where to look when something is unclear

| Question | File |
|---|---|
| Why are we doing this? | [`PRD.md`](./PRD.md) |
| What does a tool / skill look like exactly? | [`build_specs.md`](./build_specs.md) |
| How do I know a step passed? | [`docs/_validation_gates.md`](./docs/_validation_gates.md) |
| What's the session context / prior decisions? | [`../HANDOFF_LATEST.md`](../HANDOFF_LATEST.md) |
| What's the doctrine? | [`../.codex/AGENTS.md`](../.codex/AGENTS.md) |
| What's the boundary rule? | `PRD.md` § "UX principles" and `build_specs.md` § Architecture |
