# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Convert the active controller surface for CAM_Codx from Codex to Grok while preserving the existing four-tool CAM MCP librarian and its verification behavior.

## Actual User Goal

Grok Build / Grok headless should be the primary controller/orchestrator. Codex references may remain only as historical, compatibility, package-name, transcript-baseline, or deprecated context.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `AGENTS.md` | Add Grok-native project rules and CAM provenance doctrine | Low |
| `.grok/config.toml` | Add project-scoped `cam_cam` MCP server config | Medium |
| `.mcp.json` | Add Grok-compatible MCP server config mirror | Medium |
| `docs/plans/grok-controller-migration.md` | Record dependency inventory and migration plan | Low |
| `tools/grok_controller_smoke.py` | Add local Grok inspect/MCP configuration verifier | Medium |
| `tests/codex_mcp/test_grok_controller.py` | Add focused regression tests for Grok controller surface | Low |
| `src/claw_codex_mcp/__main__.py` | Preserve newline stdio and add Content-Length framed stdio for Grok-style MCP clients | Medium |
| `claw_codex_mcp/__init__.py` | Add repo-local import shim so `python -m claw_codex_mcp` uses this checkout | Medium |
| `README.md` | Reframe active controller status as Grok-first | Medium |
| `PROGRESS.md` | Record assumptions, command evidence, and blockers | Low |
| `IMPLEMENT.md` | Record CAM recall/provenance block before edits | Low |

## Existing Patterns To Follow

- Keep the MCP surface at exactly four tools.
- Keep `claw_codex_mcp` as a compatibility package name unless a later plan proves a rename safe.
- Use stdio MCP because the current server and tests are stdio-first.
- Treat Grok local CLI output as stronger evidence than stale migration prose.

## Assumptions

- `codex-cam-methodology-impl` is the implementation target.
- `CAM_CAM` remains the corpus/heavy-engine dependency and is not migrated in this pass.
- Project-scoped Grok config belongs in `.grok/config.toml` because Grok local docs say project config supports `[mcp_servers]`.
- The current Grok CLI is version `0.2.3`, where non-interactive use is `grok -p` or `grok agent headless`, not `grok --headless`.

## Non-Goals For This Pass

- Do not rename the Python package or console script.
- Do not mutate `~/.grok/config.toml`.
- Do not delete `.codex/` compatibility assets.
- Do not modify CAM_CAM heavy-engine internals.
- Do not claim authenticated Grok headless E2E if authentication is unavailable.

## Step-by-Step Plan

1. Add failing tests that assert the repo-local Grok controller config exists, points at `claw_codex_mcp`, and does not shell out to the `codex` executable.
2. Add `.grok/config.toml` and `.mcp.json` with the `cam_cam` MCP stdio server.
3. Add `AGENTS.md` with Grok-native controller doctrine.
4. Add `tools/grok_controller_smoke.py` to verify `grok --version`, `grok inspect --json`, and project MCP config.
5. Preserve existing newline-delimited stdio and add Content-Length framed stdio handling.
6. Update the README status block so the active controller is Grok and Codex is legacy compatibility context.
7. Update `PROGRESS.md` and run verification.

## Acceptance Criteria

- `pytest tests/codex_mcp/test_grok_controller.py -q` passes.
- `grok inspect --json` discovers the repo-local `.grok/config.toml`.
- `grok mcp doctor cam_cam --json` can at least diagnose the project-scoped server.
- Content-Length framed stdio ping works without weakening newline JSON-RPC behavior.
- Existing MCP tests and product smoke still pass.

## Verification Plan

- `python -m claw_codex_mcp --version`
- `pytest tests/codex_mcp/test_grok_controller.py -q`
- `pytest tests/codex_mcp/ -q`
- `python tools/product_smoke.py`
- `python tools/grok_controller_smoke.py --skip-headless`
- `grok inspect --json`
- `git diff --check`

## Rollback Plan

Remove the new Grok files, revert README/PROGRESS/IMPLEMENT edits, and rerun the baseline MCP tests to confirm the original four-tool server remains unchanged.

## Risks

| Risk | Mitigation |
|---|---|
| Grok CLI docs drift from installed behavior | Verify local `grok --help` and record mismatch |
| Project-scoped MCP config not discovered because of worktree path metadata | Test `grok inspect --json` from the actual cwd |
| Existing Codex references are too numerous to rewrite safely | Classify compatibility/historical references and move only active controller docs/config |
| Grok authentication blocks headless E2E | Record blocker; do not claim E2E |

## Proceed / Block Decision

Proceed with the scoped repo-local migration. Do not mutate user-level Grok config or attempt production deployment.
