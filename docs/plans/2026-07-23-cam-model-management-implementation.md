# CAM Model Management and Embedding Evaluation Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a canonical, CLI-first model/profile/catalog workflow and an evidence-gated embedding comparison path without changing the live corpus accidentally.

**Architecture:** CAM_CAM owns runtime behavior in one base config plus a small model-profile registry. CAM_Codx owns the contract and docs. OpenRouter is queried live for catalog facts; embedding candidates are built into isolated, fingerprinted index generations and promoted explicitly.

**Tech Stack:** Python, Typer, Pydantic/TOML, SQLite/sqlite-vec, OpenRouter-compatible HTTP, pytest, Markdown.

---

### Task 1: Capture the current configuration contract

**Files:**
- Create: `CAM_Codx/GOAL_CAM_UPD.md`
- Create: `CAM_Codx/docs/plans/2026-07-23-cam-model-management-design.md`
- Test: none (documentation gate)

**Steps:**

1. Record current config paths, model assignments, fallback order, approved IDs, and live corpus path.
2. Run `cam stats`, `cam models` discovery/help if present, and `git status --short --branch` in both repos.
3. Confirm the live database is not tracked or copied into CAM_Codx.
4. Commit only the approved design/goal artifacts.

### Task 2: Add the profile schema and deterministic loader

**Files:**
- Create: `CAM_CAM/models.toml` or the selected canonical profile path
- Modify: `CAM_CAM/src/claw/core/config.py`
- Modify: `CAM_CAM/claw.toml`
- Test: `CAM_CAM/tests/test_model_profiles.py`

**Steps:**

1. Write failing tests for profile parsing, active-profile selection, role maps, and explicit/default config equivalence.
2. Implement a small validated profile schema with `quality`, `budget`, active pointer, role capability requirements, and schema version.
3. Make the loader apply the selected profile after base TOML parsing while preserving the authoritative database binding.
4. Add dry-run migration support for legacy full TOMLs.
5. Run the focused profile tests.

### Task 3: Implement `cam models current` and profile commands

**Files:**
- Modify: `CAM_CAM/src/claw/cli/_monolith.py` or the current CLI module
- Create/modify: `CAM_CAM/src/claw/models/` runtime module as needed
- Test: `CAM_CAM/tests/test_models_cli.py`

**Steps:**

1. Add failing CLI tests for `current`, profile list/show/use, set, fallback, and migration dry-run.
2. Implement machine-readable and human-readable output with effective config/profile/corpus paths.
3. Validate exact model IDs and role capabilities before profile writes.
4. Add explicit rollback/migration receipts.
5. Run focused CLI tests and `cam models --help`.

### Task 4: Implement the live OpenRouter catalog client

**Files:**
- Create: `CAM_CAM/src/claw/models/catalog.py`
- Modify: `CAM_CAM/src/claw/cli/_monolith.py`
- Test: `CAM_CAM/tests/test_model_catalog.py`
- Fixture: `CAM_CAM/tests/fixtures/openrouter_models.json`

**Steps:**

1. Record a sanitized fixture for successful, unavailable, malformed, and deprecated model responses.
2. Write failing tests for live query parsing, price normalization, capability filters, and no-write failure behavior.
3. Implement the client using the existing HTTP/config conventions and bounded timeouts.
4. Implement `cam models catalog --live` with factual output and no ranking.
5. Run tests without credentials using fixtures, then one live catalog smoke when credentials are available.

### Task 5: Synchronize approved-model validation and legacy surfaces

**Files:**
- Modify: `CAM_CAM/src/claw/evolution/serial.py`
- Modify: `CAM_CAM/claw.toml`, `claw_cheap.toml`, `claw_dspro.toml`, `claw_grok.toml`
- Modify: `CAM_Codx/README.md`, integration/config docs
- Test: `CAM_CAM/tests/test_model_consistency.py`

**Steps:**

1. Add a failing consistency test that detects model IDs in profiles/TOMLs absent from approved validation.
2. Replace stale Kimi K2.7 references with profile-derived validation while preserving explicit compatibility history.
3. Convert duplicate alternate TOMLs to documented profile shims or remove them only through an approved migration.
4. Mark `CAM_MODEL_*` as deprecated display metadata and remove any implication that it overrides runtime config.
5. Run consistency tests and `git diff --check`.

### Task 6: Add optional role smoke tests and receipts

**Files:**
- Modify: `CAM_CAM/src/claw/cli/_monolith.py`
- Create: `CAM_CAM/src/claw/models/smoke.py`
- Test: `CAM_CAM/tests/test_model_smoke.py`

**Steps:**

1. Write failing tests for bounded request construction, receipt shape, and provider failure handling.
2. Implement `cam models test ROLE` with no automatic rollback.
3. Record model ID, role, timestamp, status, latency, token/cost metadata, and provider request ID where available.
4. Run fixture tests and one explicitly authorized live smoke.

### Task 7: Implement embedding evaluation and index generations

**Files:**
- Create: `CAM_CAM/src/claw/embeddings/evaluator.py`
- Create: `CAM_CAM/src/claw/embeddings/index_generations.py`
- Modify: `CAM_CAM/src/claw/cli/_monolith.py`
- Test: `CAM_CAM/tests/test_embedding_evaluator.py`
- Fixture: `CAM_CAM/tests/fixtures/embedding_suite.yml`

**Steps:**

1. Define the reusable approved manifest and relevance-label format.
2. Write failing tests for identical inputs, fingerprinting, isolated indexes, Recall@k/MRR, outbound receipts, promotion, and rollback.
3. Implement temporary per-model indexes and deterministic scoring.
4. Implement `cam models embeddings evaluate` and no-write behavior.
5. Implement explicit `promote` with integrity checks and atomic active-pointer update.
6. Run the fixture suite, then the approved real-repository suite when its manifest exists.

### Task 8: Document, integrate, and verify

**Files:**
- Modify: `CAM_Codx/README.md`, `docs/AGENT_PACKS.md`, relevant config/integration docs
- Modify: `CAM_Codx/PROGRESS.md`, `DECISIONS.md`
- Test: both repositories' focused suites and required existing suites

**Steps:**

1. Document CLI commands, profile ownership, live catalog behavior, embedding privacy, and rollback.
2. Run CAM_Codx contract/generator tests.
3. Run CAM_CAM focused model/embedding tests and existing runtime tests.
4. Run `git diff --check` and inspect all diffs for secret/database leakage.
5. Record exact model/catalog/index/test receipts and residual limitations.
6. Commit CAM_Codx and CAM_CAM changes separately with reviewable messages.

