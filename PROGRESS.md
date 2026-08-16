# Progress

## 2026-08-15 control-plane crash recovery and Task 8 registry reconciliation

- Recreated the lost temporary worktrees as isolated writable clones under
  `/Users/o2satz/Downloads/crash814/worktrees`; the SSD checkouts remain
  untouched.
- Restored `UPDATED_AUTONOMOUS_GOAL.md` from the persisted session transcript.
  It is the active continuation contract for Tasks 7-14 and preserves the
  explicit stop at the Task 14 product-boundary decision.
- Re-pinned the capability fixture to CAM_CAM commit
  `dc37550ef18fe91a0e8f72acc22b2c278dafc444`: 140 command paths, 16 hidden
  paths, and manifest digest
  `f71dd15854dae850b36002e85a7a2ddca6bd5f59413f385b795352b87c7856c7`.
- Classified hidden canonical `managed-run` as a CAM_Codx-selectable `record`
  route with `local_record_write` risk and bounded-phase approval. It is not a
  competing user-facing alias, provider route, or live CAM mutation.
- Registry tests passed 25/25; the live validator confirmed both the digest and
  pinned CAM_CAM revision; generated agent packs are current. The managed
  sandbox cannot create optional pytest cache files under Downloads, but this
  did not affect test results.

## 2026-08-15 Task 8 assess/plan managed-run composition

- Added a fixed list-form `managed-run start` packet for explicit `assess` or
  `plan` requests with a named run ID. Packet construction hashes the target
  identity into the reviewed plan, pins the configured CAM runtime paths, and
  performs no CAM invocation, mining, provider call, or target/corpus/profile/
  config mutation.
- The packet submission boundary accepts only one fixed tuple argv and requires
  a zero-exit JSON-object receipt; it is dependency-injected for fixture proof
  and does not add a CAM runtime implementation to CAM_Codx.
- `compose_assessment` now invokes the existing primary-only Development Brief
  builder and target inspector before it creates the bounded managed-run start
  packet. Direct precedent, transferable analogy, and new-hypothesis labels
  remain owned by the Development Brief output rather than collapsed by the
  router.
- Focused verification: `51 passed` across `test_cam_control_plane.py` and
  `test_development_brief.py`; `git diff --check` passed. Optional pytest-cache
  writes remain sandbox-blocked under Downloads only.

## 2026-08-15 Task 9 target-mutation plan authorization

- Manager packets for registry policy `target_code_mutation` now require an
  existing target repository, reviewed managed-plan ID, and lowercase
  64-character plan SHA-256. The target and plan identity are inside the
  content-addressed packet scope, so an issued single-use approval cannot be
  reused for another plan or target.
- Test-first evidence: the new packet test initially failed because `create`
  accepted no plan identity; it passes after the minimal validation and scope
  binding change. Existing `validate` policy coverage now supplies an explicit
  target and plan identity.
- Focused verification: `37 passed` in `tests/test_cam_manager.py`; `88
  passed` across the manager, control-plane, and Development Brief tests; `git
  diff --check` passed. The only warning is the recovery sandbox declining
  optional pytest-cache writes under Downloads.

## 2026-08-15 Task 10 administrative packet routing (first slice)

- Added `prepare_admin_packet` to compose the read-only control-plane route
  resolver with the existing manager packet constructor for knowledge, models,
  self-enhancement, evolution, doctor, and setup. It accepts only one of those
  registry intents, uses the explicit canonical command path, preserves the
  named run ID as workflow identity, and never invokes CAM.
- The packet seam deliberately rejects mining. Mining remains bounded by the
  existing pull/mine coordinator's explicit source, corpus, model, time, cost,
  receipt, and delta contract until its canonical manager integration is
  implemented as the next Task 10 slice.
- Test-first evidence: the new six-family packet test initially failed because
  the seam did not exist. It now passes with registry-declared `kb search` and
  `doctor capabilities` routes; the failed shorthand names proved the registry
  remains the selection authority.
- Focused verification: `6 passed` for the new packet test; `79 passed` across
  router and manager tests. Optional pytest-cache writes remain sandbox-blocked
  under Downloads only.

## 2026-08-15 Task 10 mining packet preparation (second slice)

- Added `prepare_mining_packet`, which validates that the pull/mine
  coordinator configuration matches the pinned control-plane command, corpus,
  config, and profile identities before it prepares a single manager
  `mine-workspace` packet. It reuses the coordinator's live argv builder, so
  source root, exact model, repository cap, time cap, cost cap, and budget
  receipt path are all approval-bound without duplicating mining logic.
- This seam is preparation only: it creates no budget receipt, invokes no
  provider or CAM command, changes no corpus, and does not select or dispatch
  a build candidate. Execution/receipt linkage remains the next Task 10 batch.
- Test-first evidence: the mining packet regression initially failed because
  the seam did not exist. It now passes and proves fixed manager argv, cost and
  time/repository bounds, future receipt path, no CAM invocation, and unchanged
  fixture corpus identity.
- Focused verification: `1 passed` for the new test; `122 passed` across
  router, pull/mine, and manager tests. Optional pytest-cache writes remain
  sandbox-blocked under Downloads only.

## 2026-08-15 Task 10 mining receipt-to-run packet (third slice)

- Added a fixed `managed-run link-mining-receipt` packet builder. It reads one
  existing receipt buffer, hashes that exact buffer, requires source repository
  identities and the explicit managed run ID, and targets only the existing
  CAM_CAM persistence seam with the pinned config.
- This bridge intentionally does not submit the local-record operation, mine,
  create a budget receipt, mutate the corpus, or select a build candidate. The
  receiver validates the same absolute receipt path and SHA-256 before writing
  its managed-run event.
- Test-first evidence: the receipt-link regression initially failed because
  the builder did not exist. It now passes and proves the fixed list-form argv,
  receipt digest/path, source identity, run identity, and pinned config.
- Focused verification: `1 passed` for the new link packet test; `123 passed`
  across router, pull/mine, and manager tests; `git diff --check` passed.
  Optional pytest-cache writes remain sandbox-blocked under Downloads only.

## 2026-08-15 Task 11 CAM_Codx-first documentation contract (first slice)

- Added documentation-contract tests for README, cheatsheet, program-manager
  guide, quickstart, and status. Normal-user documentation now starts with
  `Use CAM_Codx to ...`, names canonical `cam-codx` as the normal skill, and
  removes legacy specialized-skill invocations from those surfaces.
- Direct CAM_CAM documentation remains positioned for troubleshooting, runtime
  development, recovery, regression isolation, or expert use; the contract
  rejects any claim that `cam chat` is a complete general router.
- Test-first evidence: the contract initially failed on the old README/four-
  skill framing. It passes after outcome-first replacement and the legacy-skill
  inventory scan is empty for the five normal-user documents.

## 2026-08-16 Task 12 focused release gates (in progress)

- CAM_Codx focused gate passed: `190 passed` across capability registry,
  control-plane, manager, canonical skill, setup wizard, Development Brief,
  and pull/mine tests. Generated packs are current, skill frontmatter is valid,
  and `git diff --check` passed. The recovery sandbox only blocked optional
  pytest-cache writes.
- The pull/mine documentation regression was repaired: its test now requires
  canonical `Use CAM_Codx to ...` language on overview surfaces and reserves
  detailed `--source-root`, `--dry-run`, `--skip-swap`, and `claw.db` assertions
  for the dedicated operator guide.
- CAM_CAM focused gate used the actual `tests/test_application_packet.py` path.
  The planned `tests/test_self_enhance.py` does not exist; available
  self-enhancement reconstruction coverage is `tests/test_reconstruct.py`.
  The equivalent available gate produced `238 passed, 1 failed`: clean CAM_CAM
  commit `dc37550` has intentional `moonshotai/kimi-k3` entries in `claw.toml`,
  but `TestApprovedModelConfig` excludes that ID from `APPROVED_MODEL_IDS`.
  This is an unrelated baseline policy conflict, not a passed release gate and
  not changed here; no model/config file was modified.
- CAM_CAM full suite was additionally isolated with `pytest -x`: `469 passed,
  6 skipped, 1 failed` before stopping in
  `tests/test_cag_convert.py::TestReadLanceDB::test_read_lancedb_table`.
  `claw.memory.rag_adapter.read_lancedb` calls the installed LanceDB table
  `to_pandas()` path, whose underlying `LanceDataset` lacks that method. This
  is a dependency/API compatibility baseline outside the control-plane diff;
  it was not repaired or relabeled as a release pass.

## 2026-08-16 Task 12 baseline remediation

- Corrected the stale evolution allowlist from retired
  `moonshotai/kimi-k2.7-code` to the intentionally configured
  `moonshotai/kimi-k3`; the active `claw.toml` profile already uses K3 for the
  `codex` agent and fallback chain.
- Updated LanceDB import to enumerate tables with `list_tables().tables` and
  convert via `table.to_arrow().to_pandas()`, avoiding the installed LanceDB
  0.33 `to_pandas()` path that delegates to a removed `LanceDataset` method.
- Red evidence was the two exact Task 12 failures. Green verification:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -q
  tests/test_serial_evolution.py tests/test_cag_convert.py` returned
  `103 passed`. The only remaining warning was sandbox-blocked optional pytest
  cache creation; no runtime database, live profile, provider, or target was
  changed.

## 2026-06-21

- Read active `GOAL.md` and implementation plan.
- Verified `/Volumes/WS4TB/repo622sn/CAM_Codx` is the Git-backed hub checkout
  on `main...origin/main`.
- Verified remotes:
  - `CAM_Codx`: `https://github.com/deesatzed/CAM_Codx.git`
  - `CAM_CAM`: `https://github.com/deesatzed/CAM_CAM.git`
  - `moriahcareframe`: `https://github.com/deesatzed/moriahcareframe.git`
- Confirmed `CAM_CAM` has untracked `CAM_Codx_last5291pm.txt`; left untouched.
- Created non-destructive local overlay directories:
  - `/Volumes/WS4TB/CAM_ALL`
  - `/Volumes/WS4TB/CAM_ARCHIVE/2026-06-21-pre-cleanup`
- Created clean GitHub clones under `/Volumes/WS4TB/CAM_ALL/repos`.
- Documented repo inventory, local folder audit, retirement manifest, config
  alignment, GitHub-safe config guide, and config drift checks.
- Rewrote README and added first-pass hub docs for architecture, Codex
  quickstart, Repo Necromancer workflow, MoriahCareFrame case study, status,
  FAQ, repo map, and launch checklist.
- Added Codex goal templates plus Claude Code and Grok Build adapter docs and
  templates.
- Added CAM_CAM backlink docs:
  - `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/README.md`
  - `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/docs/showpieces/repo_necromancer/USER_GUIDE.md`
  - `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/docs/integrations/CAM_CODEX.md`
- No old folders were deleted, moved, renamed, or archived.

### Verification After Commits

- CAM_Codx commit: `287ed4a docs: reorganize CAM_Codx as CAM workflow hub`.
- CAM_Codx verification report commit:
  `7eec8bc docs: record CAM repo reorg verification`.
- CAM_CAM commit: `c911044 docs: link CAM_CAM runtime to CAM_Codx hub`.
- Pushed CAM_Codx `main` to GitHub through `7eec8bc`.
- Pushed CAM_CAM `main` to GitHub through `c911044`.
- MoriahCareFrame had no changes to push and remained at `a82e42c`.
- CAM_Codx `git diff --check`: passed.
- CAM_CAM `python -m pytest -q tests/test_repo_necromancer.py`: `6 passed`.
- MoriahCareFrame `PYTHONPATH=src python -m pytest -q`: `5 passed`.
- MoriahCareFrame `sh scripts/smoke.sh`: passed and left git status clean.
- CAM_ALL `verify-all.sh`: passed for clean clones.

### Final Public Cleanup Continuation

- Re-read active `GOAL.md`; scope is now the final public repo cleanup and
  fresh-clone proof pass, not just the initial hub reorganization.
- Verified current pushed heads before cleanup:
  - `CAM_Codx`: `23ad6e555127dc2856eec5070c91f2c09c04b238`
  - `CAM_CAM`: `c9110447abff2047a8c4df7021679a0847fb151e`
  - `moriahcareframe`: `a82e42cedd2f70479d44f92bd2dcab7277f86168`
- Confirmed current dirty state before edits:
  - `CAM_Codx`: modified `GOAL.md`.
  - `CAM_CAM`: untracked `CAM_Codx_last5291pm.txt`, left untouched.
  - `MoriahCareFrame`: clean.
- Identified stale current-state references in status/report/inventory docs and
  public config docs that mislabeled tracked public-safe `CAM_CAM/claw*.toml`
  defaults as local-only.
- Started cleanup classification with generated CAM_CAM batch outputs, stale
  launch reports, and dated coverage baseline as low-risk public Git removal
  candidates.
- Committed and pushed CAM_CAM cleanup:
  `9a9d71ade8f6766c8fb564051b2baa308d9abfd1 chore: remove stale public cleanup artifacts`.
- Committed and pushed CAM_Codx cleanup manifest batch:
  `7a142e3e4957f270c5179693330030dabb9cbfd0 docs: record final public cleanup manifest`.
- Created fresh-clone proof directory:
  `/Volumes/WS4TB/CAM_ALL/clone_proofs/2026-06-21-public-cleanup-104001`.
- Fresh-clone verification passed for:
  - `CAM_Codx`: `git diff --check`, JSON validation, TOML validation,
    required docs/templates, and stale planned-status scan.
  - `CAM_CAM`: `python -m pytest -q tests/test_repo_necromancer.py`,
    `git diff --check`, and absence checks for removed stale artifacts.
  - `moriahcareframe`: `PYTHONPATH=src python -m pytest -q`,
    `sh scripts/smoke.sh`, and `git diff --check`.
- Updated `/Volumes/WS4TB/CAM_ALL/repos/*` to current `origin/main` and
  verified `/Volumes/WS4TB/CAM_ALL/scripts/verify-all.sh` passes.
- Narrow high-entropy secret scan found only CAM_CAM test fixture strings; no
  tracked `.env`, database, sqlite, pem, or key files were present in fresh
  clones.
- Post-claim validation found stale final-head/status wording in CAM_Codx docs.
  Updated final status/report/manifest wording so the current pushed CAM_Codx
  proof head is `ef1e20f14870bfcc55d0a508e06b1726e6f02e8f`, later containing
  commits are verified by `git rev-parse HEAD`, and tracked public-safe
  `CAM_CAM/claw*.toml` defaults are not mislabeled as uncommitted local-only
  files.

## 2026-06-23 CAM Agent Packs Goal

- Replaced the prior final-public-cleanup `GOAL.md` with a new autonomous
  completion contract for CAM Agent Packs.
- Locked the ownership decision: CAM_Codx remains the main workflow hub;
  CAM_CAM remains the runtime/MCP core; Claude Code, Gemini, and Grok Build are
  generated host-specific packs, not separate product forks.
- Included proof gates for a shared capability contract, deterministic pack
  generator, host-specific packs, tests, CAM_CAM runtime verification, official
  host-doc rechecks, and no-secret hygiene.
- Current local verification for this goal-authoring step: `git diff --check`
  passed after editing `GOAL.md`.
- Implemented `agent-packs/contract/cam_agent_capabilities.json` with the CAM
  runtime ownership model, checked external docs, required host packs, and 19
  CAM CLI/MCP capabilities.
- Added `tools/generate_agent_packs.py`, generated
  `agent-packs/contract/CAPABILITY_CONTRACT.md`, `docs/AGENT_PACKS.md`, and
  generated packs for Claude Code, Gemini, and Grok Build.
- Added `tests/test_agent_packs.py` covering required capabilities, host-pack
  required files, generated-output freshness, JSON example parsing, and
  no-secret/no-local-DB hygiene.
- Updated README, status, repo map, and integration docs for Claude Code,
  Gemini, and Grok Build.
- Rechecked CAM_CAM runtime ownership from `src/claw/mcp_server.py`,
  `src/claw/tools/schemas.py`, `docs/MCP_INTEGRATION_GUIDE.md`, and `cam premine`
  CLI wiring.
- CAM_Codx verification passed:
  `python -m json.tool agent-packs/contract/cam_agent_capabilities.json`,
  `python tools/generate_agent_packs.py --check`,
  `python -m pytest -q tests/test_agent_packs.py` with 6 tests, and
  `git diff --check`.
- CAM_CAM runtime verification passed:
  `python -m pytest -q tests/test_tool_schemas.py tests/test_integration_wiring.py`
  with 74 tests, and `git diff --check`.
- Host CLI availability checks:
  `claude mcp list` exits 0 but currently lists only Claude Google connectors
  that need authentication; CAM is not installed there yet.
  `gemini mcp list` exits 0 and reports no MCP servers configured.
  `grok inspect` exits 0 and reports no project MCP servers configured for this
  CAM_Codx checkout.
- Standardized the generated Claude Code, Gemini, and Grok Build pack READMEs
  around the same setup and test sections: Quick Start, Configure CAM MCP,
  Verify Discovery, Smoke Test, CAM Capabilities, Safety Policy, and Files.
- Added one executable `smoke.sh` per host pack and removed the Grok-only
  `headless-smoke.sh` name so every pack has the same test entrypoint.
- Added the uniform setup/test flow and smoke-script links to the CAM_Codx
  landing README and aligned the Claude, Gemini, and Grok integration docs.

## 2026-07-06 CAM_Codx Setup Wrapper

- Designed the third setup option for Codex/CAM permissions: generate a narrow
  `cam-codx` wrapper instead of asking users to grant broad writes to the
  CAM_CAM install directory.
- Added design and implementation-plan docs:
  - `docs/plans/2026-07-06-cam-codx-setup-wrapper-design.md`
  - `docs/plans/2026-07-06-cam-codx-setup-wrapper.md`
- Extended `tools/cam_setup_wizard.py` with wrapper generation and explicit
  `--wrapper-cam-cam`, `--wrapper-db`, `--wrapper-config`, and `--wrapper-env`
  arguments.
- Updated setup documentation to explain the Codex approval prefix:
  `<CAM_HOME>/scripts/cam-codx`.
- Current targeted verification:
  `python -m pytest -q tests/test_cam_setup_wizard.py` passed with 8 tests.
- Full targeted verification passed:
  `python -m pytest -q tests/test_cam_setup_wizard.py tests/test_agent_packs.py`
  passed with 17 tests, `python tools/generate_agent_packs.py --check` passed,
  and `git diff --check` passed.
- Live wrapper proof for this machine:
  `/Volumes/WS4TB/codxswarm/scripts/cam-codx status` passed and reported all
  four agents executable; `/Volumes/WS4TB/codxswarm/scripts/cam-codx stats`
  passed and reported 2,474 active methodologies.
- Added the final novice setup step: `tools/cam_setup_wizard.py
  --install-codex-skill` now installs
  `templates/skills/cam-codx-setup` into the user's Codex skills directory and
  auto-detects side-by-side clones at `<CAM_HOME>/CAM_CAM`.
- Verification for the novice setup path:
  `python -m pytest -q tests/test_cam_setup_wizard.py tests/test_agent_packs.py`
  passed with 19 tests, and
  `python tools/cam_setup_wizard.py --cam-home /Volumes/WS4TB/codxswarm
  --skip-clone --install-codex-skill --codex-home
  /tmp/cam_codx_fake_codex_home --non-interactive` created the wrapper and
  installed the skill into the temporary Codex home.
- Added the novice startup explanation to `docs/QUICKSTART_CODEX.md`, covering
  what Codex, CAM_Codx, CAM_CAM, `claw.db`, and `cam-codx` do; the exact
  clone/install/setup/start-Codex flow; and common CAM_Codx use cases.

## 2026-08-09 Post-Mining Cleanup And Augmentation Audit

- Preserved and tracked the validated `GOAL_CAM_SUBSCIBED.md` contract.
- Corrected active CAM_Codx runtime references from the older WS4TBr checkout
  to `/Volumes/WS4TB/repo622sn/CAM_CAM` in the goal, capability contract,
  architecture, repo map, and config guidance.
- Classified the successful 80-finding mining batch without additional model
  calls or provider spend.
- Recorded the audit in
  `docs/reports/2026-08-09-post-mining-cam-augmentation-audit.md`.
- CAM_CAM cleanup created a tracked database registry, retained but ignored
  SQLite WAL/SHM files, preserved intentional Kimi K3 configuration, and
  federated Go, misc, TypeScript, and Rust ganglia.
- Verified root corpus status: 2,668 methodologies, 215 source repositories,
  four configured siblings, and SQLite integrity `ok` for all five databases.
- Focused CAM_CAM verification passed: 161 tests, with two known non-fatal
  `aiosqlite` event-loop shutdown warnings recorded as separate audit debt.
- Chose runtime identity preflight and reviewed adoption manifests as the next
  P0 implementation batch. No automatic self-enhancement or CAG rebuild was
  performed in this audit.

## 2026-08-10 CAM_Codx Program Manager

- Approved and committed the CAM_Codx program-manager design and implementation
  plan in `docs/plans/2026-08-10-cam-codx-program-manager-{design,}.md`.
- Added `tools/cam_manager.py`, a fixed-operation, no-shell packet executor with
  content-addressed scope, short-lived single-use approvals, and digest-only
  execution receipts.
- Added `templates/skills/cam-codx-swe/SKILL.md` and setup-wizard installation
  of both the setup and routine SWE skills.
- The routine path explicitly separates ordinary CAM recall from mining,
  provider spend, model promotion, and self-enhancement swap.
- CAM_CAM tournament lineage hardening passed its focused 88-test gate.
- A manager-approved, supervised self-enhancement run executed one task against
  a disposable CAM_CAM copy with `--max-tasks 1 --skip-swap`. The generated
  candidate changed `src/claw/memory/auto_fix.py`, but its focused regression
  failed 5 tests, so the candidate was rejected and no live source, database,
  profile, or configuration was swapped. This is the intended fail-closed
  outcome; the candidate is not a proposed CAM change.
- The manager execution receipt recorded return code 0 for the CAM CLI, while
  CAM's own validation result is the acceptance authority. The disposable
  copy is retained only long enough to inspect the failed candidate and will
  not be published.
- Final runtime audit corrected the model-promotion allowlist to CAM_CAM's
  current `models set`, `models rollback`, and `models profile use` commands;
  focused tests cover all three approval-required prefixes.

## 2026-08-10 SWE Development Brief

- Added the approved Development Brief contract, target inspector, primary-only
  CAM recall adapter, direct/analogy/hypothesis labels, and explicit CLI.
- Default operation reads the named target and supplied primary corpus only;
  it does not write a target file, record retrieval usage, execute target
  tests, mine, invoke a provider, or query sibling corpora.
- Added the `cam-codx-development-brief` skill and setup-wizard installation
  alongside the setup and routine SWE skills.
- Named local source roots are validated under an approved parent and render
  only a later scan-only proposal. Missing configured sibling databases render
  a relocation gate rather than triggering a broader search.
- Focused Development Brief and setup-wizard tests are recorded by the final
  cross-repository verification task; no live corpus was queried for this work.
- Final CAM_Codx verification in the isolated Development Brief worktree:
  `python -m pytest -q -p no:cacheprovider tests` passed with `44 passed`;
  `python tools/generate_agent_packs.py --check` and `git diff --check` passed.
- The companion CAM_CAM worktree verification passed `78` focused tests across
  `test_read_only_brief_query.py`, `test_tool_schemas.py`, and
  `test_integration_wiring.py`; `python -m claw.cli brief-query --help` passed.
  The read-only proof uses a synthetic fixture database only, not a live corpus.

## 2026-08-11 Development Brief Documentation Alignment

- Updated the landing README, Codex quickstart, CAM cheat sheet, program-manager
  guide, and status page so users can choose between the Development Brief,
  routine SWE skill, and approval-gated manager workflow without confusing
  their boundaries.
- The setup documentation now lists all three installed skills. The early
  new-project and continue/rescue prompts are copy-pasteable from the quickstart
  and cheat sheet.
- Re-verified `python -m pytest -q -p no:cacheprovider tests` (`44 passed`) and
  `python tools/generate_agent_packs.py --check`; `git diff --check` passed.
- This documentation pass changed no CAM runtime, database, model profile,
  configuration, or target repository.

## 2026-08-11 Pull Mine Directory Skill

- Added `tools/cam_pull_mine_dir.py` and the installable
  `cam-codx-pull-mine-dir` skill for one explicit directory-level CAM cycle.
- The coordinator defaults to
  `/Volumes/WS4TB/waswiki/repos2mine/repo622sn` but accepts `--source-root`
  for another operator's repository directory.
- Eligible Git repositories receive only `git fetch origin` then `git pull
  --ff-only`; dirty, conflicted, detached, no-upstream, fetch-failed, and
  non-fast-forward repositories are reported without blocking later ones.
- The mining command is list-form, pins both CAM database environment variables
  to one `claw.db`, runs scan before live mining, requires a paired exact model
  and hard cost cap, uses `--changed-only --no-tasks`, and records only bounded
  redacted command evidence.
- The workflow reports read-only corpus integrity/deltas and ledger provenance.
  It can dispatch at most one manager-backed supervised `--skip-swap`
  candidate only after the five-findings/two-repository/repeated-gap gate. A
  swap, model/profile change, rollback, source edit, or live config change is
  outside this skill.
- The repeated-gap conclusion is an explicit `--repeated-pattern-or-gap`
  attestation because the current corpus/ledger do not prove that semantic
  conclusion on their own.
- Verification was fixture-only: `python -m pytest -q -p no:cacheprovider
  tests` passed with `86 passed in 1.09s`; `python
  tools/generate_agent_packs.py --check`, the new skill validator, and `git
  diff --check` exited successfully. No live repository pull, corpus mining,
  provider call, database/ledger update, or candidate was executed while
  implementing this feature.

## 2026-08-12 CAM_Codx Unified Control Plane Design

- Audited the current CAM_CAM Typer command tree, hidden aliases, nested
  command groups, CAM_Codx tools, installed skill templates, setup behavior,
  and CAM-SEQ persistence surfaces.
- Confirmed that `cam chat` currently executes the mining route but explicitly
  reports create/build and enhance/fix routing as not wired.
- Confirmed that setup currently installs four overlapping skills while a
  separate semantic session-router artifact also exists.
- Approved CAM_Codx as the normal user-facing manager for every CAM_CAM
  capability. Direct CAM_CAM usage is retained for troubleshooting, runtime
  development, recovery, and regression isolation.
- Approved six everyday SWE intents: `assess`, `plan`, `build`, `fix`,
  `verify`, and `record`.
- Approved one canonical future `cam-codx` skill, one machine-readable
  capability registry, hidden compatibility aliases, and explicit approval
  classes for corpus writes, provider spend, code mutation, promotion, and CAM
  live swaps.
- Approved a source-to-outcome SWE Run backed by the existing CAM-SEQ
  `task_plans`, component/application packets, pair/landing/outcome events, and
  run connectomes rather than a parallel database.
- Recorded the approved design in
  `docs/plans/2026-08-12-cam-codx-control-plane-design.md` and made it the
  active `GOAL.md` contract.
- This checkpoint is documentation and design only. The capability registry,
  canonical skill, router, migration, and MatrAIx/SESA proof remain
  unimplemented.
- Added the exhaustive current command/skill audit at
  `docs/CAM_CAPABILITY_AUDIT_2026-08-12.md`.
- Added the TDD implementation plan at
  `docs/plans/2026-08-12-cam-codx-control-plane.md`.
- Confirmed that `agent-packs/contract/cam_agent_capabilities.json` is the
  existing registry foundation to extend; the plan does not create a second
  competing capability registry.
- Added current-versus-approved-target notices to the landing README,
  cheatsheet, program-manager guide, quickstart, and active `IMPLEMENT.md`.
- Documentation/plan checkpoint verification passed: `86 passed` across agent
  packs, setup wizard, manager, Development Brief, and pull/mine coordinator;
  `python tools/generate_agent_packs.py --check` and `git diff --check` also
  passed.
## 2026-08-12 CAM runtime capability registry

- Extended the existing agent capability contract to schema `2.0`; it remains
  the single registry for host capabilities, the 13 approved CAM_Codx workflow
  intents, and every CAM_CAM command/group route.
- Captured an independent schema-version-1 manifest snapshot from CAM_CAM Task
  1 and validated exact coverage of `139` paths: `126` managed, `2`
  troubleshooting-only, and `11` hidden compatibility aliases.
- Added strict validation for missing, unknown, duplicate, multiply classified,
  kind-mismatched, hidden-mismatched, and incomplete-policy routes. Hidden
  compatibility commands remain callable but are omitted from generated normal
  and direct-runtime references.
- TDD RED produced `9 failed, 9 passed` before the schema, validator, and
  generator support existed. Focused GREEN passed `18` registry/agent-pack
  tests; the live snapshot validator, generator `--check`, and
  `git diff --check` also passed. These checks made no provider call and did
  not change a CAM database, model profile, or runtime configuration.
- Specification review found that shape-only policy validation had mislabeled
  several provider-backed, artifact-writing, service-starting, schema-writing,
  and target-executing commands as read-only. The follow-up audit corrected
  those route policies conservatively, added closed policy vocabularies and
  approval/flag invariants, and added named runtime-boundary regressions.
- The second policy-truth pass also corrected `synergies`, `kb brains`, and
  `self-enhance status`: each opens SQLite through an engine path that may
  create files or set WAL state, so none is represented as side-effect-free.
- Quality review separated the 11 genuine hidden aliases from four hidden
  canonical operations (`evolution approve`, `govern`, `mine-report`, and
  `prism-demo`) and added explicit alias targets. Hidden canonical operations
  remain manager-routable but are absent from normal choices.
- Added compound `approval_classes` plus a risk/side-effect/default/flag
  compatibility matrix. Corrected community publish/import external-network
  policies and restored read-only truth for `mine-report`.
- Pinned the independent manifest fixture to CAM_CAM commit `5075645` and its
  content digest. The cross-repo gate now generates the live manifest from an
  explicit runtime checkout, compares its digest and exact Git revision, and
  then validates registry coverage.
- Final specification review aligned all alias safety tuples with their
  canonical targets and made parity a validator invariant. It also corrected
  the report/delta/synergy pairs to local initialization/write policy with no
  provider spend, matching their current runtime implementations.
- The final quality pass extended alias parity to workflow routes and artifact
  promises, added a complete risk/default-mode matrix, and made malformed
  manifest values and provenance fail with controlled diagnostics.
## 2026-08-13 read-only CAM_Codx control-plane router

- Added a typed, registry-backed `cam_control_plane.py plan` surface for the
  six everyday SWE intents and seven explicit administrative families.
- Planning requires pinned absolute identities for the target, CAM executable,
  database, config, and optional model profile plus optional SWE Run and mining
  receipt references. Unknown intents, unresolved/non-executable paths,
  colliding runtime identities, intent/operation mismatch, and registry gaps
  fail closed.
- The JSON result and human status card expose the goal, selected route,
  target, memory mode, operation write boundary, provider-spend possibility,
  mining status, approvals, and next action. Planning does not import or invoke
  CAM_CAM and explicitly records `operation_executed=false`.
- TDD RED produced `24` expected failures while the module was absent. The
  first specification review found unsafe lexical route selection, no proof
  that `claw.toml` and the explicit database named the same identity, and
  incomplete no-write snapshots. The hardened router now uses explicit
  operation words with intent-specific safe fallbacks, validates the TOML
  database binding, and hashes structural metadata, symlinks, empty
  directories, `.git`, and SQLite sidecars. An executable tripwire proves the
  CAM command is never invoked during planning.
- GREEN now passes `28` focused tests and `63` combined control-plane,
  capability-registry, and agent-pack tests, plus CLI help and `git diff
  --check`. No CAM operation, provider call, database mutation, target write,
  model-profile change, or runtime-config change occurred.
- Quality review found that unordered free-text matching could interpret a
  negated mention as a mutating operation. Non-default operations now require
  the explicit `operation` field; ordinary text always uses the one default
  command declared by the capability contract for that intent. The registry
  validator proves each default is one visible managed canonical command in
  the matching family.
- Full selected-route/config shape checks now turn malformed registries and
  TOML database tables into controlled exit-code-2 errors without tracebacks.
  The hardened combined suite passes `69` tests and generated agent-pack drift
  checks pass.

## 2026-08-13 contract-driven CAM approval manager

- Replaced the duplicated manager prefix, phase, and read-only maps with a
  strict adapter over the shared capability contract. All `110` executable
  managed canonical CAM commands, including the four hidden canonical
  advanced operations, now receive a fixed list-form argv prefix and the
  contract's CAM_Codx phase. Groups, troubleshooting-only commands, and hidden
  compatibility aliases cannot be selected as canonical manager operations.
- Retained the existing hyphenated manager operation names only as translations
  to exact canonical command paths. They carry no separate risk, side-effect,
  approval, spend, configuration, or promotion policy.
- Packets now bind the canonical operation policy and trusted contract digest
  into their content-addressed scope. Preparation and execution fail closed on
  missing/malformed contracts, changed contract bytes, changed packet fields,
  changed policy, invalid prefixes, or an unexpected contract identity.
- Preserved secret rejection, digest-bound approvals, expiry, single-use
  consumption, secure receipts, and `shell=False` execution. Extended budget
  validation to reject NaN and infinities as well as negative values.
- TDD RED failed at collection because the new contract adapter did not exist.
  GREEN passes `56` focused manager/registry tests and `143` combined manager,
  registry, pull/mine, control-plane, and agent-pack tests. Generator drift,
  CLI help, and `git diff --check` also pass. Tests use fixture wrappers only;
  no live CAM operation, provider call, corpus write, target mutation,
  promotion, or configuration change occurred.
- Specification review found three fail-closed gaps: the manager's partial
  contract validation could accept contradictory spend/approval policy, a
  recomputed packet could substitute its executable wrapper, and approval
  reuse was guarded by a check-then-append race. The manager now calls the
  same strict policy validator as the registry gate, requires the trusted
  wrapper identity again at execution, and atomically claims each approval
  through an exclusive mode-0600 consumption record before dispatch.
- New regressions prove an unsafe `provider_spend=true`/`approval=none`
  contract is rejected, a recomputed wrapper substitution never runs, and two
  concurrent consumers produce exactly one success. The hardened combined
  suite passes `146` tests; direct-script CLI help, generator drift, and
  `git diff --check` pass.
- Quality review then found that a wrapper could be replaced in place at the
  same path and that `--dry-run` burned the single-use approval. Packet scope
  now binds the wrapper SHA-256 and verifies it both during validation and
  immediately before dispatch. Approval validation is separate from atomic
  consumption, so a dry run checks the supplied approval but leaves it usable
  for the later real execution.
- In-place replacement and dry-run-then-execute regressions pass. Final
  focused manager/registry verification is `61 passed`; the combined Task 4
  compatibility surface is `148 passed`, with direct CLI help, generator
  drift, and `git diff --check` green.

## 2026-08-14 canonical CAM_Codx skill

- Initialized the canonical `cam-codx` skill with the official skill-creator
  scaffold and UI metadata, then replaced the placeholder with one concise
  normal-work router and four one-level progressive references: SWE,
  knowledge/mining, administration, and safety/approvals.
- The required flow reads target truth first, resolves exact runtime
  identities, plans before execution, displays the route/write/spend/mining
  card, uses the contract-driven fixed-operation manager, makes evidence
  selection/rejection and landing explicit, verifies, and records only the
  proved outcome.
- The SWE playbook covers early new-project recall, in-progress continuation,
  rescue, mitigation, troubleshooting, re-development, dissimilar donor
  evidence, landing maps, and failed-verification handling. It reuses the
  existing Development Brief and pull/mine coordinator rather than copying
  their implementation.
- The skill exposes all six everyday intents and seven administrative
  families while stating no implicit mining, no implicit promotion, separate
  provider/target/promotion/live approvals, and direct CAM_CAM only for
  troubleshooting/runtime development/recovery.
- TDD RED produced seven failures against the generated placeholder. GREEN is
  `7 passed`; the repo frontmatter validator reports zero failures, the
  official quick validator reports `Skill is valid!`, and `git diff --check`
  passes. No CAM command, provider call, corpus write, target mutation,
  promotion, or configuration change occurred.
- Specification review found that the first draft still named two legacy
  skills as dependencies. The canonical playbooks now call
  `tools/development_brief.py` and `tools/cam_pull_mine_dir.py` directly, with
  pinned arguments and an explicit mining dry run. Tests forbid references to
  the legacy skill entrypoints, preserving one normal CAM_Codx skill.
- Quality review found that approval looked automatic, non-default operation
  and argument syntax was incomplete, and the mining example omitted the
  bounds promised by its prose. The skill now requires authorization covering
  every declared class, records the actual source with `--approved-by`, and
  forbids Codex from self-authorizing spend, configuration, promotion, or live
  mutation. Planner and manager examples show explicit canonical operations
  and list-form JSON arguments.
- The mining dry run now pins profiles/local defaults, exact provider/model,
  repository count, duration, and cost. A live run may remove only `--dry-run`
  from the reviewed command; any changed value requires new review.

## 2026-08-14 canonical skill setup migration

- Changed default Codex skill installation from four specialized skills to the
  single canonical `cam-codx` package. Existing legacy entries are detected
  and reported but remain untouched unless migration is explicitly requested.
- Added `--migrate-codex-skills`, valid only with canonical installation. It
  moves exactly `cam-codx-setup`, `cam-codx-swe`,
  `cam-codx-development-brief`, `cam-codx-pull-mine-dir`, and
  `cam-codx-session`; unrelated skills are never selected.
- Each explicit migration creates a timestamped mode-0700 backup and updates a
  mode-0600 `restore.json` after every move. The metadata records original and
  backup paths and remains `partial` if a move fails, so migration never
  silently deletes or strands already moved entries without a recovery map.
- Updated the setup skill to document canonical-only installation, explicit
  migration, backup, restoration metadata, and the unrelated-skill boundary.
- TDD RED failed at import before the migration helpers existed. GREEN passes
  `22` setup/canonical-skill tests; wizard help and `git diff --check` pass.
  Verification used temporary Codex homes only and did not alter installed
  user skills, CAM runtime state, a corpus, model, or configuration.
- Specification review found that legacy migration ran before canonical
  installation and that the partial-failure branch lacked proof. Setup now
  installs `cam-codx` successfully before moving any legacy entry. A forced
  second-move failure produces a controlled error pointing to `restore.json`,
  leaves the first move recoverable, leaves the unattempted legacy skill in
  place, and records `status=partial`. The selected suite is now `117 passed`.
- Quality review found two crash-safety gaps: replacing an installed canonical
  skill deleted it before the new copy was known-good, and the migration
  journal learned each move only after it happened. Canonical updates now copy
  to a sibling staging directory, durably journal and move the old install to
  a mode-0700 backup, atomically replace it, and restore it if the swap fails.
  The report exposes the backup and mode-0600 restore metadata.
- Legacy migration now durably writes the complete original-to-backup plan
  before its first move and records a per-entry state after each one. New
  regressions cover copy failure, swap rollback, successful canonical backup,
  second-move failure, and interruption after a move but before its state
  update. Focused setup/skill verification is `27 passed`; the selected Task 6
  compatibility surface is `121 passed`, with wizard help and `git diff
  --check` green. All tests used temporary Codex homes.
