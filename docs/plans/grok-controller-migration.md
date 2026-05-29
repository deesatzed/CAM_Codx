# Grok Controller Migration Plan

**Goal:** Make Grok the primary CAM_Codx controller while preserving the existing four-tool CAM MCP librarian.

**Architecture:** Keep the proven MCP server intact and move controller discovery into Grok-native project rules plus project-scoped MCP configuration. Preserve `claw_codex_mcp` naming as compatibility surface; change active docs, smoke checks, and tests so Grok is the controller and Codex is legacy context.

**Tech Stack:** Python 3.12, stdlib `tomllib`, pytest, Grok CLI 0.2.3, MCP stdio.

---

## Current State

- Workspace root: `/Volumes/WS4TB/CAM_grok_build`.
- Active implementation repo: `/Volumes/WS4TB/CAM_grok_build/CAM_Codx/codex-cam-methodology-impl`.
- `CAM_Codx` itself is a workspace container, not a git repository.
- Implementation repo branch: `feature/initial-impl`.
- Pre-existing dirty state before this migration: modified `meta/HANDOFF_2026-05-28.md`, deleted `meta/NON_TECH_ASSESSMENT_2026-05-29.md`, untracked `data/`, untracked `instances/`.
- `CAM_CAM` repo branch: `main`.
- `codex-cam-methodology` repo branch: `main`, ahead by one commit.

## Grok Reality Check

`grokdocs.md` says the active commands are `grok build` and `grok --headless`, but local Grok CLI `0.2.3` reports different commands:

- TUI/default entry: `grok`
- Headless single prompt: `grok -p "..."` or `grok --single "..."`
- Agent modes: `grok agent stdio`, `grok agent headless`, `grok agent serve`
- MCP management: `grok mcp list`, `grok mcp add`, `grok mcp doctor`
- Configuration inspection: `grok inspect --json`

The migration must follow the installed CLI behavior and document the mismatch.

## Dependency Inventory

| Dependency | Current Role | Grok Replacement / Status |
|---|---|---|
| `.codex/config.toml` `[mcp_servers.cam_cam]` | Legacy Codex MCP wiring | Replace active path with project `.grok/config.toml` `[mcp_servers]` inline `cam_cam` plus `.mcp.json`; keep `.codex` as legacy compatibility only. |
| `.codex/AGENTS.md` | Legacy Codex doctrine | Add root `AGENTS.md` for Grok discovery; leave `.codex/AGENTS.md` as compatibility unless a later cleanup removes Codex support. |
| `.codex/skills/*` | Legacy Codex skill workflows | Preserve as archived/compatibility assets; Grok can discover project rules and MCP tools without rewriting every skill in this pass. |
| `tools/baseline_cold_start.sh` | Codex transcript baseline harness | Mark historical; do not use as primary runtime. A future Grok baseline harness can be added after authenticated headless is proven. |
| `tools/codex_trace_patterns.py` | Codex transcript parser | Mark historical; do not use as Grok runtime parser. |
| `claw_codex_mcp` package name | Python package and console compatibility | Keep for now to avoid breaking imports, tests, and installed entrypoints. |
| README and specs saying Codex is orchestrator | Public active-doc drift | Update active status to Grok-first and classify older Codex mentions as legacy/historical until a larger docs rewrite. |
| `meta/VALIDATION_GAPS_2026-05-20.md` Grok blocker | Prior unsupported Grok via Codex model slug | Superseded by direct Grok CLI controller path; still relevant as historical evidence that Grok should not be routed through Codex auth. |

## Task 1: Grok Project Rules

**Files:**
- Create: `AGENTS.md`

**Steps:**

1. Add Grok-native controller instructions.
2. Preserve the CAM rule: recall, cite, verify, record.
3. State that `claw_codex_mcp` is compatibility naming, not active controller naming.
4. Verify with `grok inspect --json` that the file is loaded.

## Task 2: Grok Project MCP Config

**Files:**
- Create: `.grok/config.toml`
- Create: `.mcp.json`

**Steps:**

1. Configure `.grok/config.toml` with a project-scoped `[mcp_servers]` inline `cam_cam` entry.
2. Use stdio transport: `python -m claw_codex_mcp --transport stdio`.
3. Point `CAM_CODEX_MCP_DB_PATH` at the local CAM_Grok build checkout's TypeScript `claw.db`.
4. Point `CAM_CODEX_MCP_DECISIONS_INDEX` at the existing local outcome/index directory.
5. Mirror the same server in `.mcp.json` for Grok MCP compatibility probing.
6. Verify with `grok inspect --json` and `grok mcp doctor cam_cam --json`.

## Task 3: Grok Smoke Script

**Files:**
- Create: `tools/grok_controller_smoke.py`
- Test: `tests/codex_mcp/test_grok_controller.py`

**Steps:**

1. Write tests for `.grok/config.toml` structure.
2. Write tests for `.mcp.json` compatibility config.
3. Write tests proving the primary Grok config does not shell out to `codex`.
4. Preserve MCP stdio behavior and add Content-Length framed stdio coverage for Grok-style MCP clients.
5. Implement a smoke script that runs `grok --version`, `grok inspect --json`, and optionally a headless prompt.
6. Keep headless optional because authentication can block it.

## Task 4: Active Documentation

**Files:**
- Modify: `README.md`
- Modify: `PROGRESS.md`

**Steps:**

1. Update README opening status to Grok-first.
2. Add a compatibility note that older Codex docs/scripts remain historical until removed by a separate cleanup.
3. Append final command evidence and remaining blockers to `PROGRESS.md`.

## Task 5: Verification

Run:

```bash
python -m claw_codex_mcp --version
pytest tests/codex_mcp/test_grok_controller.py -q
pytest tests/codex_mcp/ -q
python tools/product_smoke.py
python tools/grok_controller_smoke.py --skip-headless
grok inspect --json
git diff --check
```

If Grok authentication blocks headless E2E, record the exact output and do not claim E2E.

## Known Grok Blockers

- `grok inspect --json` exits 0 and discovers repo-local `AGENTS.md` and `.grok/config.toml`, but reports `projectTrusted: false`.
- `grok mcp doctor cam_cam --json` currently reports `server_count: 0` from project config and a failed MCP initialize handshake while also skipping `grok.com` because authentication is expired.
- `grok -p ...` currently fails before a model response with settings/session setup errors, including `FS_PERMISSION_DENIED`.

These are recorded as external Grok trust/auth/session blockers. They do not change the local CAM MCP server contract or the verified pytest/product-smoke behavior.
