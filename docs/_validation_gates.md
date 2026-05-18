# Codex-CAM Methodology — Validation Gates (working file)

> **Audience:** the coordinator who will fold these into `build_to_do_checklist.md`.
> **Producer:** Tester agent.
> **Rule:** every gate is runnable against the real workspace today. No mock, no placeholder, no simulation. Every gate has a falsifier.
> **Workspace root:** `/Volumes/WS4TB/WS4TBr/CAM_Codx`
> **Real DB:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db` (107 methodologies, 95 viable as of 2026-05-17)
> **Coverage target:** >90% line + branch on every new module in `claw_codex_mcp/`. Any deficit produces an action plan or an explicit user waiver.

---

## Phase 1 — Pre-implementation baseline

**Gate 1.1 — Existing 17-tool MCP RSS baseline captured**
- Command: `/usr/bin/time -l python -c "from claw.mcp_server import server; import asyncio; tools = asyncio.run(server.list_tools()); print(len(tools))" 2> /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/mcp17_rss.txt` (run from `CAM_CAM/`)
- Pass: stdout prints `17`; `baselines/mcp17_rss.txt` exists and contains a `maximum resident set size` line with a numeric byte count.
- Fail: stdout prints any number other than 17 (server has drifted), or the time output is missing the RSS line.
- Falsifier: the RSS captured is the Python interpreter alone because `list_tools()` short-circuits without instantiating the tool registry — verify by also dumping `[t.name for t in tools]` and confirming all 17 names from the handoff are present.
- Real-data requirement: real `claw.mcp_server` module, real registered tool list. No stubs.
- Regression scope: Phase 9 lightness gate compares new MCP RSS against this number; if baseline is wrong, every lightness claim is wrong.
- Coverage requirement: N/A (measurement, not code under test).

**Gate 1.2 — Codex CLI version + model pinned in baselines manifest**
- Command: `codex --version > /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/codex_version.txt && grep -E '^model\s*=' /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml >> /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/codex_version.txt`
- Pass: file contains both a `codex` version string and a line matching `model = "gpt-5.5"` (or whatever the user has locked at execution).
- Fail: either command writes empty output or the model line is absent.
- Falsifier: the captured model id does not match the model id used by the cold-start runs in Gate 1.4 — version skew silently invalidates every behavioural comparison.
- Real-data requirement: real `codex` binary on PATH, real `.codex/config.toml`.
- Regression scope: any later "Codex behaved differently" claim must be checked against this pin.
- Coverage requirement: N/A.

**Gate 1.3 — `claw.db` schema snapshot frozen**
- Command: `sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db ".schema" > /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/claw_db_schema.sql && sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "SELECT lifecycle_state, COUNT(*) FROM methodologies GROUP BY lifecycle_state;" > /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/corpus_counts.txt`
- Pass: `claw_db_schema.sql` contains a `CREATE TABLE methodologies` statement; `corpus_counts.txt` contains exactly the two lines `viable|95` and `embryonic|12` (in any order).
- Fail: schema file is empty, or counts diverge from the handoff (`viable|95`, `embryonic|12`).
- Falsifier: the table `codex_outcome_log` already appears in the schema dump (means someone wrote schema before Phase 6 — out-of-order build).
- Real-data requirement: live `claw.db` queried directly. No exporter.
- Regression scope: every read-tool gate (Phase 2) compares against this row count; corpus drift mid-build invalidates Phase 9.
- Coverage requirement: N/A.

**Gate 1.4 — Cold-start transcripts captured on 5 unfamiliar real repos**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/baseline_cold_start.sh` where the script runs `codex exec --skip-git-repo-check "Summarize this codebase in 5 bullets and propose the first non-trivial change" --cwd <repo>` for each of the 5 repos listed in `docs/codex-cam-methodology/baselines/repo_set.txt`. Each transcript saved as `baselines/cold_start/<repo_slug>.txt`.
- Pass: 5 transcript files exist, each non-empty, each contains a `## Summary` section or equivalent reasoning trace. `baselines/cold_start/manifest.json` records the 5 repo paths, commit SHAs, and wall-clock seconds per run.
- Fail: any transcript is empty, missing, or the manifest is incomplete.
- Falsifier: any of the 5 repos is actually familiar to Codex via existing skill memory (check by grepping `.codex/skills/*/SKILL.md` for the repo name — must return zero hits for each repo in `repo_set.txt`).
- Real-data requirement: 5 real third-party repos on disk, not synthetic; no fake README scaffolds.
- Regression scope: Phase 9 cold-start claim measures *delta* against this baseline.
- Coverage requirement: N/A.

---

## Phase 2 — MCP read tools (`cam_recall`, `cam_provenance`)

**Gate 2.1 — Tool-count ceiling enforced from day one**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_tool_count.py -v`
- Pass: test asserts `len(asyncio.run(server.list_tools())) == 2` for Phase 2, increments to 3 in Phase 3, 4 in Phase 6. The test file is parameterized by `EXPECTED_TOOL_COUNT` env var or by a constant the build phases update. Exit 0.
- Fail: any other count, or test errors.
- Falsifier: the test imports a different `server` symbol than the one wired into `.codex/config.toml` — verify by reading `[mcp_servers.cam_cam].command` from `config.toml` and confirming it resolves to the same module the test imports.
- Real-data requirement: real `mcp.Server` instance from the new `claw_codex_mcp.server` module.
- Regression scope: violation here means the boundary doctrine has already broken — every subsequent gate is suspect.
- Coverage requirement: 100% on the tool-registration code path in `server.py`.

**Gate 2.2 — `cam_recall` returns real methodologies with non-null provenance for a real query**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_cam_recall.py -v --cov=claw_codex_mcp --cov-report=term-missing`
- Pass: test invokes `cam_recall(query="rate limit", k=5)` against the live `claw.db`, asserts at least 1 returned row, asserts every returned row has non-empty `notes`, non-empty `tags`, non-empty `source_path`, and the `source_path` value passes `Path(...).exists()` OR is a documented URL. Coverage report shows >=90% on `claw/codex_mcp/recall.py`.
- Fail: zero rows, any null provenance field, any `source_path` that does not resolve, or coverage <90%.
- Falsifier: the test passes with `k=5` returning 5 rows but they are all from the same methodology id (recall is broken but row-count check is satisfied) — assert `len({r.id for r in results}) == len(results)`.
- Real-data requirement: live `claw.db`, real FTS5 query, no fixture DB.
- Regression scope: every skill that calls `cam_recall_and_cite` depends on this contract.
- Coverage requirement: >=90% line and branch on `claw/codex_mcp/recall.py`.

**Gate 2.3 — `cam_provenance(methodology_id)` resolves to the exact row in `claw.db`**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_cam_provenance.py -v`
- Pass: for a random sample of 10 ids drawn live from `SELECT id FROM methodologies WHERE lifecycle_state='viable' ORDER BY RANDOM() LIMIT 10`, `cam_provenance(id)` returns a row whose `id` matches and whose `source_path`, `notes`, and `tags` byte-equal the columns read directly from sqlite. Exit 0.
- Fail: any id returns null, or any returned field diverges from a direct sqlite read.
- Falsifier: the test always passes because both the tool and the assertion read from the same cached pydantic model — verify the assertion uses a fresh `sqlite3.connect(...)` independent of the tool's connection.
- Real-data requirement: live `claw.db`, two independent connections.
- Regression scope: the "every recalled methodology has a real source row" invariant.
- Coverage requirement: 100% on `claw/codex_mcp/provenance.py` (small surface).

**Gate 2.4 — Read tools are truly read-only (no INSERT/UPDATE/DELETE on `methodologies` table)**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_read_only.py -v` — test enables `PRAGMA query_only=ON` on the connection used by recall/provenance, then runs 100 invocations of each and confirms zero exceptions.
- Pass: 200 successful invocations under `query_only=ON`; exit 0.
- Fail: any `SQLITE_READONLY` exception, indicating a write path snuck in.
- Falsifier: the test connection is not the same connection the production tool uses — assert that the tool factory accepts an injected connection and the same factory is used by the production entry point.
- Real-data requirement: live `claw.db` opened with `query_only`.
- Regression scope: append-only ledger invariant (only `cam_record_outcome` may write).
- Coverage requirement: covered by Gate 2.2 / 2.3.

---

## Phase 3 — Decisions index (`cam_decisions_search`)

**Gate 3.1 — Indexer discovers every `DECISIONS.md` under a real scan root**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology/src/claw_codex_mcp/decisions_indexer.py --scan-root /Volumes/WS4TB/WS4TBr/CAM_Codx --rebuild && diff <(find /Volumes/WS4TB/WS4TBr/CAM_Codx -type f -name 'DECISIONS.md' -not -path '*/node_modules/*' -not -path '*/.git/*' | sort) <(sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/decisions_index.db "SELECT path FROM decisions ORDER BY path;")`
- Pass: `diff` exits 0 (every on-disk `DECISIONS.md` appears in the index exactly once).
- Fail: `diff` shows any `<` or `>` lines (missing or phantom entries).
- Falsifier: the indexer found zero files and the on-disk find also found zero — the diff is vacuously empty. Add: `test -s` on the indexed-paths output; require at least 1 row, or document the empty result as expected.
- Real-data requirement: real filesystem scan, real on-disk `DECISIONS.md` files.
- Regression scope: cross-repo learning claim (Phase 9) depends on this index being complete.
- Coverage requirement: >=90% on `claw/codex_mcp/decisions_indexer.py`.

**Gate 3.2 — `cam_decisions_search` returns substring-grounded hits**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_decisions_search.py -v`
- Pass: for a query term picked from a real `DECISIONS.md` file (test pre-extracts a 3-word phrase live at test setup), `cam_decisions_search(query=<phrase>)` returns at least one row, and the returned `excerpt` field contains the phrase as a literal substring (case-insensitive).
- Fail: zero rows, or the excerpt does not contain the queried phrase.
- Falsifier: the same phrase appears in 20 different files but only 1 is returned with no pagination signal — assert `total_hits` is reported and matches `grep -c` on the filesystem.
- Real-data requirement: real `DECISIONS.md` corpus across the workspace.
- Regression scope: the cross-project learning falsifier.
- Coverage requirement: >=90% on `claw/codex_mcp/decisions_search.py`.

**Gate 3.3 — Index rebuild is idempotent and incremental**
- Command: `python -m claw_codex_mcp.decisions_indexer --rebuild && sqlite3 .../decisions_index.db "SELECT COUNT(*) FROM decisions;" > /tmp/n1.txt && python -m claw_codex_mcp.decisions_indexer --rebuild && sqlite3 .../decisions_index.db "SELECT COUNT(*) FROM decisions;" > /tmp/n2.txt && diff /tmp/n1.txt /tmp/n2.txt`
- Pass: two consecutive rebuilds produce identical row counts; diff exits 0.
- Fail: counts diverge (duplicate insertion or non-deterministic ordering).
- Falsifier: counts are identical because the second rebuild was a no-op due to a stale lock or unchanged-mtime fast path that never actually re-read the files — verify by `touch`ing one `DECISIONS.md` between runs and confirming its `updated_at` column changes.
- Real-data requirement: real index DB.
- Regression scope: the index will be rebuilt many times; non-idempotence corrupts the corpus.
- Coverage requirement: covered by Gate 3.1.

---

## Phase 4 — Skills v1 (`cam_recall_and_cite`, `repo_recon` mod, `deepscientist-data-research` rewrite)

**Gate 4.1 — `cam_recall_and_cite` skill frontmatter parses and declares only real tools**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/validate_skill_frontmatter.py /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/cam_recall_and_cite/SKILL.md`
- Pass: validator exits 0; reports `tools: [cam_recall, cam_provenance]` (or strict subset); zero references to deprecated `claw_*` names.
- Fail: validator reports a missing/extra tool, or any `claw_query_memory` / `claw_store_finding` literal in the file body.
- Falsifier: the validator only inspects frontmatter and the body still contains a literal `claw_query_memory` string — grep the file body separately and require zero hits.
- Real-data requirement: real new skill folder on disk.
- Regression scope: phantom-MCP class of bugs.
- Coverage requirement: 100% on `tools/validate_skill_frontmatter.py`.

**Gate 4.2 — Zero `claw_query_memory` / `claw_store_finding` references remain anywhere in `.codex/skills/`**
- Command: `! grep -rEi 'claw_query_memory|claw_store_finding' /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/`
- Pass: grep returns exit code 1 (no matches), and the leading `!` flips it to 0.
- Fail: any match anywhere under `.codex/skills/`.
- Falsifier: the grep excludes hidden files or binary skill assets — confirm with `grep --include='*.md' --include='*.toml' --include='*.txt'` re-run.
- Real-data requirement: real `.codex/skills/` tree.
- Regression scope: cross-cutting; explicitly enforced as cross-cutting gate too.
- Coverage requirement: N/A.

**Gate 4.3 — `repo_recon` modification preserves prior behaviour AND adds `cam_decisions_search` call**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_repo_recon_skill.py -v` — test diffs the SKILL.md against a captured pre-modification snapshot, asserts: (a) all prior section headers still present, (b) exactly one new mention of `cam_decisions_search`, (c) frontmatter `tools` list contains `cam_decisions_search`.
- Pass: all three assertions hold; exit 0.
- Fail: any prior section header removed, more than one new tool reference (scope creep), or frontmatter missing.
- Falsifier: the snapshot file is older than the actual prior commit — verify the snapshot was generated from `git show <last-commit-before-phase-4>:./repo_recon/SKILL.md`.
- Real-data requirement: real `repo_recon/SKILL.md`, real prior-state snapshot from git.
- Regression scope: any user relying on `repo_recon`'s existing prompt structure.
- Coverage requirement: 100% on the test file itself.

**Gate 4.4 — `deepscientist-data-research` rewrite removes all 5 phantom references at original line numbers**
- Command: `grep -nEi 'claw_query_memory|claw_store_finding|CAM MCP|RL bandit' /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/deepscientist-data-research/SKILL.md; test $? -eq 1`
- Pass: grep exits 1 (no matches); the surrounding `test $? -eq 1` returns 0.
- Fail: any match remains.
- Falsifier: file shrank to a stub that has no content at all — assert `wc -l < SKILL.md` is at least 50 (the rewrite must be a real replacement, not a delete).
- Real-data requirement: real `.codex/skills/deepscientist-data-research/SKILL.md`.
- Regression scope: the phantom-contract bug.
- Coverage requirement: N/A.

**Gate 4.5 — Codex CLI actually invokes `cam_recall` in a recall-shaped task (claim 0 — invocation, not registration)**
- Command: `codex exec --skip-git-repo-check "Recall any methodology related to rate limiting and cite its provenance" --cwd /Volumes/WS4TB/WS4TBr/CAM_Codx 2>&1 | tee /tmp/cam_invoke_trace.txt && grep -E 'tool_call.*cam_recall|invoking cam_recall' /tmp/cam_invoke_trace.txt`
- Pass: the trace contains at least one literal occurrence of a `cam_recall` tool invocation marker (exact regex tuned to the Codex CLI trace format pinned in Gate 1.2).
- Fail: trace contains the tool registered but never called.
- Falsifier: Codex called the tool but the result was discarded and not cited in the final answer — additionally grep the final assistant message for at least one provenance line matching `source:` and a methodology id.
- Real-data requirement: real Codex CLI, real new MCP server, real `claw.db`.
- Regression scope: every Phase 9 claim is vacuous without this gate green.
- Coverage requirement: N/A (behavioural).

---

## Phase 5 — Rescue ladder skill

**Gate 5.1 — Rescue ladder skill frontmatter declares parseable auto-fire trigger**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/validate_skill_frontmatter.py --require-trigger /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/rescue_ladder/SKILL.md`
- Pass: validator confirms the frontmatter contains an `auto_fire.trigger` field that matches the workspace trigger schema (e.g., `on: second_consecutive_verification_failure`) and exits 0.
- Fail: missing trigger, malformed YAML, or unknown trigger kind.
- Falsifier: trigger parses but no skill loader actually wires it — separately assert that the canonical skill loader at `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/_loader.py` (or equivalent referenced in AGENTS.md) recognises the trigger string.
- Real-data requirement: real SKILL.md, real loader.
- Regression scope: any auto-fire skill silently failing to trigger.
- Coverage requirement: 100% on `tools/validate_skill_frontmatter.py`.

**Gate 5.2 — Auto-fire actually triggers after the 2nd consecutive verification failure (behavioural)**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/test_rescue_autofire.sh` — script runs a scripted Codex session that deliberately fails a verification twice, captures the trace, and greps for `rescue_ladder` activation.
- Pass: trace contains `skill_activate: rescue_ladder` (or pinned format) after the second failure and before any user prompt.
- Fail: no activation, OR activation fires on first failure (over-trigger).
- Falsifier: rescue_ladder fires but immediately exits without invoking any of its prescribed steps — assert the trace also contains at least one `cam_recall` call inside the rescue context.
- Real-data requirement: real Codex CLI session with real failing verification.
- Regression scope: rescue ladder claim in Phase 9.
- Coverage requirement: N/A (behavioural).

**Gate 5.3 — Rescue ladder does NOT fire on first failure (no over-trigger)**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/test_rescue_no_premature.sh` — runs a single failing verification and confirms no rescue activation in the trace.
- Pass: trace contains zero `skill_activate: rescue_ladder` lines.
- Fail: any activation on a single failure.
- Falsifier: the script's "failing verification" is actually passing — assert the trace shows exactly one verification with `result: fail` before checking activation count.
- Real-data requirement: real Codex session.
- Regression scope: avoids rescue-ladder flapping.
- Coverage requirement: N/A.

---

## Phase 6 — Outcome write loop (`cam_record_outcome`, `outcome_log` skill, `codex_outcome_log` table)

**Gate 6.1 — `codex_outcome_log` table created with append-only constraints**
- Command: `sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db ".schema codex_outcome_log" | tee /tmp/col_schema.txt && grep -E 'CREATE TRIGGER.*codex_outcome_log.*(BEFORE UPDATE|BEFORE DELETE).*RAISE' /tmp/col_schema.txt | wc -l`
- Pass: schema dump contains a `CREATE TABLE codex_outcome_log`, AND grep finds at least 2 triggers (one blocking UPDATE, one blocking DELETE) that `RAISE` an abort.
- Fail: table missing, or triggers missing.
- Falsifier: triggers exist but only guard one column, allowing other columns to be mutated — assert triggers fire `WHEN OLD.rowid IS NOT NULL` covering whole-row mutation.
- Real-data requirement: real `claw.db` post-migration.
- Regression scope: the append-only ledger invariant; the entire flywheel.
- Coverage requirement: 100% on the migration script.

**Gate 6.2 — `cam_record_outcome` appends real rows; UPDATE and DELETE attempts raise**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_cam_record_outcome.py -v --cov=claw_codex_mcp.outcome --cov-report=term-missing`
- Pass: test inserts 3 outcomes via the tool, confirms 3 new rows by direct sqlite count, then attempts `UPDATE codex_outcome_log SET status='changed' WHERE id=...` and `DELETE FROM codex_outcome_log WHERE id=...` directly via sqlite and asserts both `sqlite3.OperationalError` with the trigger-abort message. Coverage >=90%.
- Fail: any of: insert count wrong, UPDATE silently succeeds, DELETE silently succeeds, coverage <90%.
- Falsifier: the test connects with a user that bypasses triggers (none in sqlite, but verify the test does NOT set `PRAGMA recursive_triggers=OFF` or any guard-disabling pragma).
- Real-data requirement: real `claw.db`, real new table, real triggers.
- Regression scope: append-only ledger.
- Coverage requirement: >=90% line and branch on `claw/codex_mcp/outcome.py`.

**Gate 6.3 — `outcome_log` skill writes after every verified step that used a recalled methodology**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/test_outcome_log_closure.sh` — script runs a Codex session that recalls a methodology, applies it, verifies the result, then asserts `SELECT COUNT(*) FROM codex_outcome_log WHERE methodology_id=<recalled_id>` increased by exactly 1.
- Pass: row count delta is exactly 1; the new row's `result` field is non-null and one of `{green, red}`.
- Fail: delta is 0 (loop did not close) or >1 (double-write).
- Falsifier: delta is 1 but the inserted row's `methodology_id` is null or points to a non-existent row — assert FK integrity via `PRAGMA foreign_key_check;` returns zero rows.
- Real-data requirement: real Codex run, real recall, real verification.
- Regression scope: the centerpiece — flywheel claim in Phase 9.
- Coverage requirement: covered by 6.2 + behavioural confirmation here.

**Gate 6.4 — Bandit-outcome counter increases over a run of 10 verified outcomes (signal reaches CAM_CAM)**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/run_10_outcomes.sh && sqlite3 .../claw.db "SELECT COUNT(*) FROM codex_outcome_log;"`
- Pass: count is >=10 after the run; baseline before the run was captured to a file and the delta is exactly the number of verified outcomes.
- Fail: delta < verified-outcome count.
- Falsifier: the 10 outcomes are all identical (same methodology_id, same query) — accept only if at least 3 distinct `methodology_id` values appear, so we know the loop is not over-fitting to one path.
- Real-data requirement: real Codex sessions, real verifications.
- Regression scope: signal-to-bandit pipeline.
- Coverage requirement: N/A (integration).

---

## Phase 7 — AGENTS.md doctrine update

**Gate 7.1 — All 4 doctrine bullets appended verbatim and exactly once**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/check_doctrine.py /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md` — script asserts each of the 4 doctrine sentences (defined in `tools/doctrine_expected.txt`) appears exactly once in AGENTS.md.
- Pass: all 4 present, each `grep -c` returns 1; exit 0.
- Fail: any sentence missing, duplicated, or paraphrased.
- Falsifier: sentences are present but inside a fenced code block (cosmetic, ignored by Codex) — assert each match is outside any triple-backtick block.
- Real-data requirement: real `.codex/AGENTS.md`.
- Regression scope: any later doctrine edit accidentally removing a bullet.
- Coverage requirement: 100% on `tools/check_doctrine.py`.

**Gate 7.2 — AGENTS.md still parses as Codex sees it (no markdown breakage)**
- Command: `python -c "import pathlib, sys; t = pathlib.Path('/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md').read_text(); assert len(t) > 0 and t.count('```') % 2 == 0, 'unbalanced code fences'; print('ok')"`
- Pass: prints `ok`.
- Fail: assertion error.
- Falsifier: file parses but Codex's actual loader rejects it — also run `codex exec --print-doctrine` (if available) and check exit 0.
- Real-data requirement: real file.
- Regression scope: any user session loading a broken AGENTS.md.
- Coverage requirement: N/A.

---

## Phase 8 — `.codex/config.toml` MCP registration

**Gate 8.1 — `[mcp_servers.cam_cam]` block exists and resolves to a runnable command**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/validate_config_toml.py /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml` — script parses TOML, asserts presence of `[mcp_servers.cam_cam]` with `command` and `args`, then `subprocess.run([command, *args, '--help'], timeout=10)` returns exit 0.
- Pass: TOML valid, block present, `--help` exits 0 and prints recognizable MCP server help.
- Fail: block missing, command not found, or `--help` non-zero.
- Falsifier: `--help` succeeds because it short-circuits before importing the actual server class — additionally run a 1-second `stdio` handshake and confirm a `tools/list` response with the expected tool names.
- Real-data requirement: real `config.toml`, real installed module.
- Regression scope: registration → invocation pipeline.
- Coverage requirement: 100% on the validator script.

**Gate 8.2 — `context7` MCP wiring untouched**
- Command: `python -c "import tomllib, pathlib; c = tomllib.loads(pathlib.Path('/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml').read_text()); assert 'context7' in c.get('mcp_servers', {}), 'context7 dropped'; print(c['mcp_servers']['context7'])"`
- Pass: prints the existing `context7` block; exit 0.
- Fail: block missing or altered.
- Falsifier: the block is present but its `command` changed to something else (silent corruption) — assert the printed dict equals a pinned snapshot in `baselines/context7_config.json`.
- Real-data requirement: real `config.toml`.
- Regression scope: preserves existing user value.
- Coverage requirement: N/A.

---

## Phase 9 — End-to-end validation (5 falsifiable claims)

**Gate 9.1 — PROVENANCE: every cited methodology in a Codex session resolves in `claw.db`**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/verify_provenance.sh` — runs 20 recall-shaped Codex tasks, captures every `source: <path>` and `methodology_id: <id>` cited in transcripts, then for each id runs `sqlite3 claw.db "SELECT COUNT(*) FROM methodologies WHERE id='<id>';"` and asserts exactly 1.
- Pass: 100% of cited ids resolve (binary, no partial credit).
- Fail: any cited id returns 0 from sqlite, or any cited `source:` path does not exist on disk and is not a documented URL.
- Falsifier: 100% of cited ids are the same id (Codex only ever cited one methodology across 20 tasks — recall has collapsed) — assert at least 5 distinct ids across the 20 tasks.
- Real-data requirement: real Codex sessions, real `claw.db`.
- Regression scope: trust in every recommendation Codex makes.
- Coverage requirement: 100% binary on provenance resolution; gap analysis required if <100%.

**Gate 9.2 — LIGHTNESS: new MCP RSS at idle is <= 50% of the 17-tool MCP baseline**
- Command: `/usr/bin/time -l python -m claw_codex_mcp --self-test 2> /tmp/new_rss.txt && python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/compare_rss.py /tmp/new_rss.txt /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/mcp17_rss.txt`
- Pass: `compare_rss.py` reports new RSS / baseline RSS <= 0.50; exit 0.
- Fail: ratio > 0.50, OR either file missing.
- Falsifier: the new MCP does not actually instantiate the tool registry during `--self-test` (skipping the DB connection setup) — require `--self-test` to perform one round-trip per tool and dump the RSS only AFTER all four round-trips.
- Real-data requirement: real both binaries, same machine, same Python version.
- Regression scope: the entire "thin librarian" thesis.
- Coverage requirement: N/A.

**Gate 9.3 — LEARNING: bandit-outcome row count is non-zero after a 10-task workflow**
- Command: `sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "SELECT COUNT(*) FROM codex_outcome_log;" > /tmp/before.txt && bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/run_10_diverse_tasks.sh && sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "SELECT COUNT(*) FROM codex_outcome_log;" > /tmp/after.txt && python -c "before=int(open('/tmp/before.txt').read()); after=int(open('/tmp/after.txt').read()); assert after - before >= 10, f'only {after-before} outcomes'; print('ok')"`
- Pass: delta >= 10; script prints `ok`.
- Fail: delta < 10.
- Falsifier: all 10 new rows share `methodology_id` (over-fit) — assert `SELECT COUNT(DISTINCT methodology_id) FROM codex_outcome_log WHERE rowid > <before_max_rowid>` >= 3.
- Real-data requirement: real Codex sessions, real recall, real verification, real ledger writes.
- Regression scope: the flywheel claim — without this green, the methodology has not delivered its core value.
- Coverage requirement: N/A.

**Gate 9.4 — COLD-START: first-non-trivial-change quality on 5 unfamiliar repos beats the pre-implementation baseline**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/cold_start_after.sh && python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/compare_cold_starts.py /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/baselines/cold_start/ /Volumes/WS4TB/WS4TBr/CAM_Codx/docs/codex-cam-methodology/runs/cold_start_after/`
- Pass: comparison reports, for each of the 5 repos, at least one cited methodology id in the "after" transcript that was NOT cited in the "before" transcript; exit 0.
- Fail: any repo's after-transcript cites zero methodologies, OR all citations match before-transcript citations (no new ground gained).
- Falsifier: the after-transcripts cite methodologies but the cited ids do not appear in the methodology rows the recall tool actually returned (Codex hallucinated the ids) — cross-check every cited id against the corresponding `cam_recall` tool-call result in the same transcript.
- Real-data requirement: same 5 unfamiliar repos from Gate 1.4, same Codex CLI version.
- Regression scope: cold-start claim.
- Coverage requirement: N/A.

**Gate 9.5 — RESCUE: 2nd-failure trigger produces a different next-step than the 1st-failure attempt**
- Command: `bash /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/verify_rescue_ladder.sh` — runs a verification that fails twice with the same root cause, captures the 1st-failure response and the post-rescue response, asserts they are not byte-identical AND the post-rescue response references at least one methodology recalled via the rescue ladder.
- Pass: responses differ; post-rescue response contains at least one `methodology_id: <id>` citation AND the id is one returned by the rescue's `cam_recall` invocation visible in the same trace.
- Fail: responses identical, OR no recall citation post-rescue.
- Falsifier: responses differ only in cosmetic whitespace — diff after normalizing whitespace must still show a real difference (e.g., new methodology reference or new approach verb).
- Real-data requirement: real verification, real rescue ladder, real recall.
- Regression scope: rescue ladder claim.
- Coverage requirement: N/A.

---

## Cross-cutting gates (run at multiple phases)

**CC.1 — MCP tool-count ceiling (<=4)**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/test_tool_count_ceiling.py -v`
- Pass: `len(asyncio.run(server.list_tools())) <= 4` at all times; in Phase 9 the value is exactly 4.
- Fail: any value > 4.
- Falsifier: the test imports a different `server` symbol than the one wired into `config.toml` (see Gate 2.1 falsifier).
- Real-data requirement: real production server module.
- Regression scope: the boundary doctrine.
- Coverage requirement: 100% on the tool-registration code path.
- Runs at: end of every phase from Phase 2 onward.

**CC.2 — Provenance integrity (100% binary)**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/audit_provenance.py` — for every row returned by 100 sampled `cam_recall` invocations, resolve `source_path` and require it to exist (or match a `^https?://` URL pattern).
- Pass: 100% resolution; exit 0.
- Fail: any failed resolution.
- Falsifier: the audit only checks the first row per invocation — assert it iterates over all returned rows.
- Real-data requirement: real `claw.db`, real filesystem.
- Regression scope: provenance trust.
- Coverage requirement: 100% binary; <100% requires action plan or user waiver.
- Runs at: end of Phase 2, Phase 4, Phase 9.

**CC.3 — Append-only ledger (no UPDATE/DELETE on `codex_outcome_log` in SQL audit log)**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/audit_sql_log.py --table codex_outcome_log --since-phase 6` — parses the workspace SQL audit log (enabled in Phase 6 via `PRAGMA query_log` or equivalent sqlite tracer) and asserts zero UPDATE or DELETE statements against `codex_outcome_log`.
- Pass: 0 UPDATE + 0 DELETE; exit 0.
- Fail: any such statement.
- Falsifier: the audit log is empty (tracer never ran) — assert audit log has >=1 INSERT against `codex_outcome_log` to prove the tracer is wired.
- Real-data requirement: real audit log.
- Regression scope: append-only invariant.
- Coverage requirement: 100% binary.
- Runs at: end of Phase 6, end of Phase 9, and before every release-candidate cut.

**CC.4 — No phantom MCP references in `.codex/skills/`**
- Command: `! grep -rEi 'claw_query_memory|claw_store_finding' /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/`
- Pass: zero hits.
- Fail: any hit.
- Falsifier: grep excludes file types where references could hide — re-run with explicit `--include='*.md' --include='*.toml' --include='*.txt' --include='*.yaml'`.
- Real-data requirement: real skills tree.
- Regression scope: phantom-contract class of bugs.
- Coverage requirement: 100% binary.
- Runs at: end of Phase 4, on every commit to `.codex/skills/`, and before every release-candidate cut.

**CC.5 — Auto-fire trigger schema validity**
- Command: `python /Volumes/WS4TB/WS4TBr/CAM_Codx/tools/validate_all_triggers.py /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/` — for every SKILL.md whose frontmatter contains an `auto_fire` block, validate the trigger against the workspace trigger schema (JSON schema file at `tools/trigger_schema.json`).
- Pass: every trigger validates; exit 0.
- Fail: any schema violation.
- Falsifier: validator is permissive and accepts any string — assert the schema rejects an obvious bad string (`auto_fire.trigger: "purple"`) by including a negative test case in the validator's own test.
- Real-data requirement: real skills tree, real schema.
- Regression scope: any new auto-fire skill.
- Coverage requirement: 100% on `tools/validate_all_triggers.py`.
- Runs at: end of Phase 5 and after any new skill addition.

**CC.6 — No-mock detector (CI grep flags hits for human review)**
- Command: `grep -rEi -n '\b(mock|stub|fake|simulate|simulation|placeholder|cached[ _-]response|demo)\b' /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology/src/claw_codex_mcp/ /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/ /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/ | tee /tmp/mock_audit.txt; test ! -s /tmp/mock_audit.txt`
- Pass: empty audit file; exit 0.
- Fail: any hit; CI emits the audit for human review.
- Falsifier: a hit is allowlisted via a comment like `# noqa: mock-detector` that the grep doesn't recognise — explicitly forbid allowlisting; every hit requires a documented user approval recorded in `docs/codex-cam-methodology/mock_approvals.md`.
- Real-data requirement: real source tree.
- Regression scope: workspace mock policy.
- Coverage requirement: 100% binary.
- Runs at: every phase boundary.

**CC.7 — Coverage ceiling on `claw_codex_mcp/`**
- Command: `pytest /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/tests/codex_mcp/ --cov=claw_codex_mcp --cov-branch --cov-report=term-missing --cov-fail-under=90`
- Pass: coverage >=90% line AND >=90% branch; exit 0.
- Fail: either below 90%.
- Falsifier: the coverage report excludes write-path modules (`outcome.py`, `db.py`) via `.coveragerc` omit lines — assert no `omit` entries reference any file under `claw/codex_mcp/`.
- Real-data requirement: real test suite, real source modules.
- Regression scope: workspace test-coverage policy.
- Coverage requirement: >=90% line + branch (gap analysis required if below).
- Runs at: end of every phase from Phase 2 onward.

---

## Gate-ordering note for the coordinator

Per the Tester sub-agent's findings recorded in the handoff: validation gates should be ordered **provenance first, lightness second, learning third, cold-start fourth, rescue fifth** at the Phase 9 end-to-end stage. The within-phase gates above follow construction order; Phase 9 reflects that priority.

## Coverage gap-handling protocol

Any test invocation that reports <100% on a 100%-required gate (CC.2, CC.3, CC.4, CC.6) or <90% on `claw_codex_mcp/` (CC.7) requires a written action plan appended to `docs/codex-cam-methodology/_coverage_gaps.md` or an explicit user waiver, before the next phase can begin. This is mandated by workspace policy.
