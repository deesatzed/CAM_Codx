# Codex-CAM Methodology — Implementation Handoff (Phase 7-9 Progress)

**Worktree:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl`
**Branch:** `feature/initial-impl`
**Date:** 2026-05-20

This handoff records the resumed `/goal` run that advanced Phase 7, Phase 8, Phase 9, and the feasible Phase 10 local gates while preserving the original objective. The goal remains incomplete because required end-state gates are not satisfied: the requested `x-ai/grok-build-0.1` model is not supported by the current Codex ChatGPT subscription path, and non-interactive `codex exec` cancels MCP tool calls before returning tool results.

## Current State

### Phase 7 — MCP stdio wire-up

Status: done for local stdio protocol coverage.

Evidence:

- `pytest tests/codex_mcp/test_stdio_integration.py -q` -> `4 passed`
- `pytest tests/codex_mcp/ -q` -> `64 passed`
- `python -m claw_codex_mcp --version` -> `0.1.0`
- `/usr/bin/time -l python -m claw_codex_mcp --transport stdio` -> `14614528 maximum resident set size`
- `python tools/demo_stdio.py --mode standalone` -> exited 0; listed 4 tools and called all 4
- `python tools/demo_stdio.py --mode connected` -> exited 0; listed 4 tools and called all 4

What changed:

- `tests/codex_mcp/test_stdio_integration.py` now launches the real MCP subprocess, lists exactly four tools, and calls all four tools in both connected and standalone modes.
- Connected-mode stdio tests use a temporary outcome DB so they do not keep mutating `tests/fixtures/claw_slice.db`.
- Standalone-mode tests assert honest empty `cam_recall`, absent `cam_provenance`, working `cam_decisions_search`, and a real `cam_record_outcome` row in a standalone SQLite DB.
- `src/claw_codex_mcp/__main__.py` now speaks newline JSON-RPC stdio directly, lazy-loads mode detection/schema bootstrap on the first MCP request, and lazy-loads handler/schema modules only on `call_tool`.
- `tests/codex_mcp/test_cli_metadata.py` prevents the lightweight CLI metadata from drifting away from the canonical 4-tool surface and guards against reintroducing the heavy `mcp.server` import path.
- `tools/demo_stdio.py` provides a direct local demo that launches the real server through the official MCP SDK client in standalone or connected mode.

### Phase 8 — Codex wiring and doctrine

Status: partially done; model swap blocked.

Workspace `.codex` changes:

- `.codex/config.toml` now has `[mcp_servers.cam_cam]` with:
  - command: `/Users/o2satz/miniforge3/envs/py313/bin/python`
  - args: `-m claw_codex_mcp --transport stdio`
  - env: `CAM_CODEX_MCP_DB_PATH=/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db`
  - env: `CAM_CODEX_MCP_DECISIONS_INDEX=/Users/o2satz/.cam_codex_mcp/codex_decisions_index.db`
- `.codex/AGENTS.md` now includes the four-tool surface rule, rejection rules, and the boundary test.
- The workspace decisions index was built at `/Users/o2satz/.cam_codex_mcp/codex_decisions_index.db`; verification query showed 3 indexed decision blocks.

Evidence:

- `CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex mcp list` shows `cam_cam` and `context7`.
- `CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex mcp get cam_cam` shows the expected command, args, and env.
- `.codex/AGENTS.md` markdown integrity check passed.
- After user re-login, `CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex login status` reports `Logged in using ChatGPT`.
- After user re-login, `CODEX_HOME=... codex exec --json ...` reaches the configured `cam_cam` MCP server and starts `cam_recall`, proving auth/discovery now reach the MCP layer.

Model swap status:

- Active default model was not changed from `gpt-5.5`.
- `codex debug models | rg 'x-ai/grok-build-0\.1|grok|x-ai'` returned no matches.
- `grok --version` failed because no `grok` CLI is installed.
- `codex exec --ephemeral --skip-git-repo-check -m x-ai/grok-build-0.1 "Reply with exactly: model-ok"` reached the provider and returned:
  `The 'x-ai/grok-build-0.1' model is not supported when using Codex with a ChatGPT account.`
- User confirmed OpenAI/Codex subscription auth is preferred over a separate API-key provider path. Therefore no OpenRouter/xAI provider was added and `model = "gpt-5.5"` remains the active subscription-backed model.

Per the goal, do not silently substitute another model. The model swap requires an external account/provider change or a different user-approved model.

### Phase 9 — Skills

Status: done for file-level skill integration and validation.

Workspace `.codex/skills` changes:

- Added `.codex/skills/cam_recall_and_cite/SKILL.md`
- Added `.codex/skills/rescue_ladder/SKILL.md`
- Added `.codex/skills/outcome_log/SKILL.md`
- Modified `.codex/skills/repo_recon/SKILL.md` to call `cam_decisions_search`
- Rewrote `.codex/skills/deepscientist-data-research/SKILL.md` stale calls:
  - `claw_query_memory(...)` -> `cam_recall(...)`
  - `claw_store_finding(...)` -> `cam_record_outcome(...)`

Validator improvement:

- Added `tests/codex_mcp/test_skill_frontmatter.py`.
- Updated `tools/trigger_schema.json` so valid Codex skill frontmatter may include `name` and `description` alongside strict `auto_fire`.
- Updated `tools/validate_skill_frontmatter.py` comments to match the real schema behavior.

Evidence:

- `python tools/validate_skill_frontmatter.py --dir ../.codex/skills` -> `validated 41 file(s); failures: 0`
- `rg -n "claw_query_memory|claw_store_finding" ../.codex/skills` -> no matches
- `pytest tests/codex_mcp/test_skill_frontmatter.py -q` -> `2 passed`

## Phase 10 Gate Status

Passed or partially satisfied:

- MCP stdio protocol gate: passed locally through official MCP SDK subprocess tests.
- Standalone behavior gate: passed in stdio integration tests with temp outcome DB.
- Connected behavior gate: passed in stdio integration tests against `tests/fixtures/claw_slice.db`.
- Workspace MCP discovery: passed when `CODEX_HOME` points at the workspace `.codex`.
- Skill frontmatter / phantom reference gates: passed.
- Product smoke wrapper: passed locally. `python tools/product_smoke.py` exits 0, verifies version, standalone absent-corpus behavior, connected real slice recall/provenance, decisions search, and append-only/idempotent outcome writes in both modes.
- Real-use-case pilot plan: added `docs/REAL_USE_CASE_TEST_PLAN.md` with MVP definition, three pilot workflows, exact commands, evidence template, pass/fail criteria, and current blockers/waivers.

Failed or not satisfied:

- Preferred model gate: failed because `x-ai/grok-build-0.1` is not supported by the current Codex ChatGPT account.
- Real Codex E2E gate: partial. After re-login, Codex reaches `cam_cam` and starts MCP tool calls, but non-interactive `codex exec` cancels the MCP calls with `user cancelled MCP tool call`. Tested overrides did not change this: `approval_policy="never"`, `default_tools_approval_mode` values `never`, `on-request`, `always`, and per-server `mcp_servers.cam_cam.approval_mode` values `always`, `enabled`, `never`.
- Lightness gate: passed locally after remediation. Measurement:
  - legacy RSS: `62554112`
  - initial new MCP RSS before remediation: `94142464`
  - initial ratio: `1.505`
  - remediated new MCP RSS: `14614528`
  - remediated ratio: `0.233630`
  The current new server meets the <=0.50 validation target and the stricter <=0.25 PRD/build-spec target under the static EOF startup measurement. The official MCP SDK client integration tests still pass; only the server-side boot path avoids `mcp.server`.

Not run:

- Real Codex end-to-end task that proves `cam_recall_and_cite` and `outcome_log` auto-fire in an actual Codex coding session with MCP tool calls approved and completed.
- Fresh-clone standalone install test.
- Rescue-rate gate, because the failure-corpus waiver remains in effect.

Open validation gaps and action plans are recorded in `meta/VALIDATION_GAPS_2026-05-20.md` and the local ignored `docs/_coverage_gaps.md`.

## Files Changed In This Run

Inside `codex-cam-methodology-impl`:

- `tests/codex_mcp/test_stdio_integration.py`
- `tests/codex_mcp/test_cli_metadata.py`
- `tests/codex_mcp/test_skill_frontmatter.py`
- `tools/demo_stdio.py`
- `tools/product_smoke.py`
- `tests/codex_mcp/test_product_smoke.py`
- `docs/REAL_USE_CASE_TEST_PLAN.md`
- `tools/trigger_schema.json`
- `tools/validate_skill_frontmatter.py`
- `meta/VALIDATION_GAPS_2026-05-20.md`
- `README.md`
- `baselines/new_mcp_rss.txt` (gitignored measurement)

Pre-existing dirty files preserved:

- `src/claw_codex_mcp/__main__.py`
- `tests/fixtures/claw_slice.db`
- `2026-05-20-104442-command-messagebrainstormingcommand-message.txt`

Outside this repo, under workspace `.codex`:

- `.codex/config.toml`
- `.codex/AGENTS.md`
- `.codex/skills/cam_recall_and_cite/SKILL.md`
- `.codex/skills/rescue_ladder/SKILL.md`
- `.codex/skills/outcome_log/SKILL.md`
- `.codex/skills/repo_recon/SKILL.md`
- `.codex/skills/deepscientist-data-research/SKILL.md`

Outside this repo, generated runtime state:

- `/Users/o2satz/.cam_codex_mcp/codex_decisions_index.db`
- `/Users/o2satz/.cam_codex_mcp/codex_outcome_log.db`

## Recommended Next Work

1. Run the real Codex E2E proof in an interactive Codex TUI session and approve the `cam_cam` MCP tool calls, or identify the supported config key for non-interactive MCP tool approval.
2. Keep `gpt-5.5` as the subscription-backed active model unless the user later approves a separate provider/API-key path or Codex subscription auth exposes `x-ai/grok-build-0.1`.
3. Run a real Codex session with workspace `CODEX_HOME` to prove the skill auto-fire path, not just the file-level skill contracts.
4. Run a fresh-clone standalone install test once the real Codex E2E approval path is resolved.
