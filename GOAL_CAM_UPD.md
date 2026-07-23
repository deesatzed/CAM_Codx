# CAM Model Configuration and Embedding Evaluation Update

## Outcome

Replace CAM's drifting model configuration with one explicit, CLI-managed
configuration system that is safe for the live corpus, queries OpenRouter's
live catalog and pricing, supports user-selected role-based models, and
compares embedding models on an approved cross-section of real repositories.

CAM_Codx owns this contract, user-facing workflow, migration plan, and test
gates. CAM_CAM owns the executable CLI, config loader, model catalog client,
profile persistence, embedding evaluation, and runtime tests.

## Current Truth

- Canonical workflow hub: `/Volumes/WS4TB/repo622sn/CAM_Codx`.
- Authoritative CAM run directory and corpus:
  `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db`.
- The active mining invocation must pin both `CLAW_DB_PATH` and
  `CAM_CODEX_MCP_DB_PATH` to that corpus.
- The existing full TOML profiles duplicate model configuration and can select
  stale `data/claw.db` paths.
- `CAM_MODEL_*` values in `.env` are display/setup metadata, not runtime model
  overrides. They must not remain a competing source of truth.

## Required Product Contract

### One configuration authority

1. Keep one base runtime configuration for database, budgets, safety, and
   non-model runtime behavior.
2. Add one versioned model-profile registry containing only:
   - active profile pointer;
   - named profiles such as `quality` and `budget`;
   - role assignments for `mining`, `analysis`, `verification`, `bulk`,
     `web-research`, `fallback`, and `local`;
   - embedding provider/model/dimension/index settings.
3. Make every normal CAM command resolve the same base config plus the active
   profile. `--config` must remain an explicit, documented override.
4. Remove duplicated runtime model choices from legacy alternate TOMLs, or
   convert them into thin, tested compatibility shims.
5. Synchronize the model validator/approved-model registry with profile data;
   no active profile can reference an unvalidated model ID.

### CLI-first model management

Provide a `cam models` command family:

```text
cam models current
cam models catalog [--embeddings] [--provider PROVIDER] [--live]
cam models profile list|show|create|use
cam models set ROLE MODEL_ID
cam models add-fallback MODEL_ID
cam models test ROLE
cam models migrate --dry-run|--apply
cam models embeddings evaluate --models MODELS --suite SUITE
cam models embeddings promote RUN_ID
```

- `catalog` always retrieves live OpenRouter model data. It presents facts only:
  exact model ID, provider, price, context, capabilities, and availability.
  It does not rank or recommend models.
- Changes are made only by explicit user selection. `test` is optional and
  records a local receipt; it is never an implicit prerequisite for saving.
- A catalog failure, unavailable model, or incompatible capability must fail
  before any profile write and must name the affected role/profile/model.
- Profile changes create readable local audit records and normal Git diffs.

### Embedding evaluation and promotion

1. Treat embeddings and their index as derived data, never as source content.
2. Maintain an explicitly approved, versioned evaluation manifest that samples
   a mixed, cross-repository set of real code, prompts, Markdown, PDFs, images,
   audio/transcripts, and configuration structures.
3. Every hosted evaluation must show/persist its exact outbound manifest,
   modality, byte/token count, provider, model, and estimated/actual cost.
4. Evaluate candidate models in isolated temporary index generations using the
   same sources, chunking, metadata, queries, and relevance labels.
5. Report Recall@k, MRR, citation/source support, modality coverage, latency,
   index time, index size, and cost. Do not activate a winner automatically.
6. Promotion creates a new index generation from source artifacts. Existing
   vectors remain available for rollback until explicitly removed; vectors from
   one embedding model are never converted or mixed with another.

## Required Migration

1. Implement `cam models migrate --dry-run` first. It must identify every
   existing TOML model assignment, model fallback, DB path, `.env` metadata
   value, and model-registry entry.
2. Import the live profile unchanged as `legacy-import`.
3. Require the operator to create/select any `quality` or `budget` profile;
   do not invent choices or recommendations.
4. Pin the authoritative corpus path and reject a legacy profile that would
   silently target a stale `data/claw.db`.
5. Deprecate `CAM_MODEL_*` as runtime-looking settings with a clear warning,
   while retaining API-key handling in `.env`.
6. Do not delete legacy configurations until the migration and compatibility
   tests pass and an operator explicitly approves removal.

## Proof Gates

### Unit and integration gates

- Config loader resolves an identical effective profile for normal commands;
  `--config` behavior is explicit and covered.
- The active profile and approved-model validation cannot drift.
- Catalog parser has recorded fixtures and validates live OpenRouter response
  fields without exposing credentials.
- Selection rejects unavailable, deprecated, malformed, or role-incompatible
  model IDs before writes.
- Migration dry run is non-mutating; apply is idempotent and preserves a
  rollback path.
- Existing provider calls, fallback logic, budgets, and secret handling retain
  their current protections.
- Embedding index fingerprints include provider, model, dimension, chunking,
  preprocessing, and source-manifest version.
- Evaluator indices are isolated; a failed evaluation cannot change the active
  index or corpus.
- Hosted evaluation receipts include the approved outbound manifest and cost.

### End-to-end gates

1. `cam models current` reports the effective profile, config source, live DB,
   role assignments, fallback chain, and embedding index generation.
2. `cam models catalog --live` returns current OpenRouter metadata and pricing.
3. An operator can create a profile, select an available model for a role, and
   see the unified config reflected by a normal CAM command.
4. Optional `cam models test ROLE` records a receipt without changing a
   selection.
5. A sample migration from the current TOMLs creates no silent DB switch.
6. An embedding evaluation across at least the current baseline plus two
   candidates produces a comparison report; promotion occurs only by explicit
   command.
7. Existing focused CAM model/config tests and full relevant suites pass.
8. `git diff --check` passes in both CAM_Codx and CAM_CAM, and source repos or
   the live corpus are not mutated by read-only CLI commands.

## Scope and Stop Rules

Allowed runtime changes belong in CAM_CAM. CAM_Codx changes are limited to
this goal, generated/operator documentation, migration instructions, and
cross-repo proof artifacts. Do not mine, enrich, enhance, deploy, or alter the
live corpus as part of this work unless separately approved.

Stop and ask before any destructive legacy-config deletion, broad database
migration, external spend beyond the explicit catalog/test/evaluation action,
or any change that would upload real repository material without an approved
embedding-evaluation manifest.
