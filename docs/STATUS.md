# Status

Current feature checkpoint: 2026-08-10. Historical XTtape publication details
remain below as provenance, not as the current feature inventory.

## Implemented

- CAM_Codx is documented as the Codex-native workflow hub.
- CAM_CAM remains the runtime/base engine.
- Repo Necromancer packet workflow is documented.
- Codex goal templates exist.
- Generated CAM Agent Packs exist for Claude Code, Gemini, and Grok Build.
- The packet/approval manager supports fixed operation packets, single-use
  approvals, digest-only receipts, and separately gated model/self-enhancement
  promotion or rollback.
- Four Codex skills are installable: setup, routine SWE, Development Brief, and
  `cam-codx-pull-mine-dir`.
- The Development Brief gives early new-project and continue/rescue guidance
  with direct-precedent, transferable-analogy, and new-hypothesis labels.
- Development Brief recall uses a supplied primary corpus only and is read-only:
  no mining, provider calls, target edits, retrieval telemetry, or sibling
  corpus search occurs by default.
- The Pull Mine Directory skill is an explicit bounded phase: `--source-root`
  selects another user's repository directory, `--dry-run` performs no Git/CAM
  writes, and a live pass can only reach one supervised `--skip-swap` candidate
  after its evidence gate. It cannot swap, promote, roll back, or edit live
  configuration.
- A shared capability contract exists at
  `agent-packs/contract/cam_agent_capabilities.json`.
- `docs/AGENT_PACKS.md` explains the generated-pack architecture.
- XTtape showpiece artifacts exist under
  `docs/showpieces/xttape-cam-comparison/`.
- The XTtape case study exists at
  `docs/examples/XTTAPE_CAM_SHOWPIECE_CASE_STUDY.md`.
- Local overlay directories exist at `/Volumes/WS4TB/CAM_ALL`.
- Archive staging exists at `/Volumes/WS4TB/CAM_ARCHIVE`.

## Verified Locally

- GitHub remotes for CAM_Codx, CAM_CAM, and moriahcareframe were queried.
- `CAM_CAM/data/claw.db` exists locally and was inspected using metadata-only
  SQLite commands.
- Clean clones were created under `/Volumes/WS4TB/CAM_ALL/repos`.
- CAM_CAM MCP runtime ownership was inspected from
  `src/claw/mcp_server.py`, `src/claw/tools/schemas.py`, and
  `docs/MCP_INTEGRATION_GUIDE.md`.
- XTtape showpiece evidence was checked for stale CAM paths, excluded source
  material, and obvious secret patterns before commit.
- The XTtape comparison published a final merged build brain and app
  implementation plan, but no XTtape runtime app code.

## Pushed To GitHub

Verified at `origin/main` on 2026-06-26 after the XTtape showpiece commit.

- CAM_Codx includes the XTtape showpiece results and public documentation
  framing. Verify the exact pushed head with `git rev-parse HEAD` and
  `git ls-remote origin refs/heads/main`.
- CAM_CAM through `9a9d71a chore: remove stale public cleanup artifacts`.
- MoriahCareFrame had no changes to push and remains at `a82e42c`.

## Verification Status

- Working-checkout cross-repo verification passed in the previous batch and is
  recorded in `docs/reports/CAM_REPO_REORG_VERIFICATION_2026-06-21.md`.
- `docs/repo_inventory/PUBLIC_REPO_CLEANUP_MANIFEST.json` now governs tracked
  public-file cleanup.
- Fresh-clone proof passed and is recorded at
  `docs/reports/CAM_PUBLIC_REPO_DONE_FOREVER_2026-06-21.md`.
- Agent pack verification is:
  `python tools/generate_agent_packs.py --check`,
  `python -m pytest -q tests/test_agent_packs.py`, and `git diff --check`.
- XTtape showpiece verification included `git diff --check`, secret-pattern
  scan over the committed showpiece docs, and remote head verification.

## 2026-08-10 Development Brief Verification

- CAM_Codx local `main` fast-forwarded to `f8f6ef3`; this was intentionally a
  local merge and was not pushed at this checkpoint.
- CAM_CAM local `main` fast-forwarded to `6b64ca4` under the same local-only
  integration decision.
- CAM_Codx verification passed: `python -m pytest -q -p no:cacheprovider tests`
  (`44 passed`), `python tools/generate_agent_packs.py --check`, and
  `git diff --check`.
- CAM_CAM focused verification passed:
  `PYTHONPATH=src python -m pytest -q tests/test_read_only_brief_query.py tests/test_tool_schemas.py tests/test_integration_wiring.py`
  (`78 passed`), `PYTHONPATH=src python -m claw.cli brief-query --help`, and
  `git diff --check`.
- The no-mutation proof is fixture-backed against a synthetic SQLite database;
  it is not a live-corpus read test.

## Intentionally Out Of Scope

- Deleting, moving, renaming, or archiving old folders.
- Publishing `claw.db`.
- Publishing real API keys or local-only config.
- Merging CAM_CAM, CAM_Codx, and generated products into one monorepo.
- Creating separate `CAM_Claude`, `CAM_Gemini`, or `CAM_Grok` product forks.
- Claiming that XTtape app runtime code has been built. The published XTtape
  artifact is a planning/evidence showpiece and implementation contract.
