# CAM Model Management and Embedding Evaluation Design

## Purpose

CAM currently stores model choices in duplicated TOMLs, exposes `CAM_MODEL_*`
environment metadata that does not control runtime selection, and allows a
profile to resolve a stale corpus path. This design establishes one
CLI-first model-management workflow for CAM while preserving explicit operator
control over model selection and external data routing.

## Design decisions

### Configuration structure

Use one base runtime configuration plus one small, versioned model-profile
registry. The base configuration owns the database, budgets, provider wiring,
and safety policy. The profile registry owns the active-profile pointer,
role-based cloud/local model choices, fallback chains, and embedding settings.

This replaces duplicated full TOMLs. Legacy files remain compatibility shims
until migration and tests prove they are safe to retire. The live corpus path
is explicitly pinned so a profile switch cannot select a stale `data/claw.db`.

### Roles, not vendor labels

The user selects models for functional roles: `mining`, `analysis`,
`verification`, `bulk`, `web-research`, `fallback`, and `local`. Legacy agent
slot names are an internal mapping, not a user-facing claim about a model's
vendor identity.

### Live catalog, explicit selection

`cam models catalog` always calls OpenRouter's live catalog endpoint. It shows
facts only: model identifier, provider, price, context, supported capabilities,
and availability/deprecation. It makes no model recommendations. A user makes
an explicit role assignment, optionally runs a tiny live smoke test, and can
inspect the local receipt.

### Embeddings

Embeddings are derived indexes, not user data. A model change cannot convert
prior vectors into a new semantic space, so it creates an isolated new index
generation from original source artifacts. The previous index stays active
until the new one passes integrity checks, then remains available for rollback.

The evaluator compares models on a reusable, operator-approved manifest of
mixed real repository material. The same data, chunking, queries, and labels
are used for every candidate. Hosted candidates must produce an outbound
manifest and cost receipt before data is sent.

## CLI shape

```text
cam models current
cam models catalog --live
cam models profile list|show|create|use
cam models set <role> <model-id>
cam models add-fallback <model-id>
cam models test <role>
cam models migrate --dry-run|--apply
cam models embeddings evaluate --models <ids> --suite <manifest>
cam models embeddings promote <run-id>
```

## Error handling

Catalog/select operations fail before writing when OpenRouter is unavailable,
a model is missing/deprecated, or a role requires a capability the model lacks.
CAM never silently substitutes a model. Read-only status/catalog commands must
not write a profile, corpus, or index.

## Verification

Tests cover consistent config resolution, profile/registry synchronization,
catalog fixtures, explicit model selection, migration idempotence, rejected
bad selections, optional test receipts, index-generation isolation, evaluation
metrics, and hosted-data manifests. End-to-end checks prove that normal CAM
commands honor the active profile and retain the authoritative live corpus.
