# Validation Gaps - 2026-05-20

This tracked companion file records Phase 10 gates that remain blocked or deferred after the Phase 7-10 resume. The ignored local file `docs/_coverage_gaps.md` may contain the same working notes, but this file is the durable in-repo record.

## Blocked - Preferred model

- **Required state:** active preferred model may be changed to `x-ai/grok-build-0.1` only after local/provider verification.
- **Current evidence:**
  - `codex debug models | rg 'x-ai/grok-build-0\.1|grok|x-ai'` returned no matches.
  - `grok --version` failed because no `grok` CLI is installed.
  - `codex exec --ephemeral --skip-git-repo-check -m x-ai/grok-build-0.1 "Reply with exactly: model-ok"` returned: `The 'x-ai/grok-build-0.1' model is not supported when using Codex with a ChatGPT account.`
  - Re-probe on 2026-05-20T21:14 confirmed the same unsupported-model error.
- **Current product decision:** user confirmed OpenAI/Codex subscription auth is preferred and a separate API-key provider should not be introduced just to use Grok.
- **Status:** blocked for the exact Grok slug, no waiver. Active model remains `gpt-5.5` because it is available through ChatGPT subscription auth.
- **Next action:** keep `gpt-5.5` unless the user later approves a separate provider/API-key path or OpenAI subscription auth exposes `x-ai/grok-build-0.1`.

## Partial - Real Codex E2E session

- **Required state:** real Codex session proves the workspace MCP config and skill path invoke the four-tool MCP surface.
- **Earlier evidence:** before re-login, `CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex exec ...` failed with `refresh_token_reused` and `Provided authentication token is expired. Please try signing in again.`
- **Current evidence after user re-login:** `CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex login status` reports `Logged in using ChatGPT`, and `codex exec --json` reaches the `cam_cam` MCP server and starts `cam_recall`.
- **Remaining issue:** non-interactive `codex exec` cancels MCP tool calls with `user cancelled MCP tool call`. Overrides tested without success: `approval_policy="never"`, `default_tools_approval_mode="never"`, `default_tools_approval_mode="on-request"`, `default_tools_approval_mode="always"`, and per-server `mcp_servers.cam_cam.approval_mode` values `always`, `enabled`, and `never`.
- **Status:** partial. Auth and discovery are fixed; a full real Codex E2E tool-result transcript still needs an interactive approval path or a documented Codex config key that permits non-interactive MCP tool approval.
- **Next action:** run the E2E proof in an interactive Codex TUI session and approve the MCP tool calls, or identify the supported config key for trusted MCP tool auto-approval.

## Passed - Lightness

- **Required state:** new four-tool MCP server RSS must be <=25% of the legacy 17-tool baseline under the static EOF startup measurement.
- **Current evidence:**
  - legacy baseline RSS: `62554112`
  - new MCP RSS after raw stdio/lazy boot changes: `14614528`
  - ratio: `0.233630`
- **Status:** passed locally.
- **Notes:** The server still interoperates with the official MCP SDK client in `tests/codex_mcp/test_stdio_integration.py`; the server no longer imports `mcp.server` on the stdio boot path.

## Deferred - Fresh-clone standalone install

- **Required state:** clean install with no `CAM_CODEX_MCP_DB_PATH`, then real Codex session exercising all four tools.
- **Current evidence:** local standalone subprocess behavior passes through the official MCP SDK client, but the real Codex session is blocked by workspace auth and model availability.
- **Local demo evidence:** `python tools/demo_stdio.py --mode standalone` and `python tools/demo_stdio.py --mode connected` both exited 0, listed the four tools, called each tool, and wrote queryable outcome rows under `/private/tmp/cam_codex_mcp_demo`.
- **Status:** deferred, no waiver.
- **Next action:** run after auth/model gates are resolved.
