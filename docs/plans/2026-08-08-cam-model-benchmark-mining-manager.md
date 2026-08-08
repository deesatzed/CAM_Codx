# CAM Model Benchmark, Mining Manager, and Enhancement Synthesis Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build and operate a CAM_Codx-managed, CAM_CAM-executed workflow that live-discovers mining models, benchmarks them under a $5 OpenRouter and 100 Codex-credit cap, promotes explicit role profiles, mines only content-new or content-updated repositories, and produces evidence-linked CAM enhancement packets.

**Architecture:** CAM_CAM gains modular model catalog, profile, benchmark, scoring, fingerprint, manifest-mining, verification, and modern Codex-host adapter surfaces. CAM_Codx owns the benchmark contract, operator documentation, candidate/suite manifests, durable receipts, and enhancement-packet validation. Live benchmark artifacts and databases remain local and isolated; the authoritative `claw.db` is not touched until a model profile is explicitly promoted and a content-frozen mining manifest is approved.

**Tech Stack:** Python 3.12+, Typer, Pydantic v2, `httpx`, TOML, SQLite/aiosqlite, GitPython and Git CLI, pytest/pytest-asyncio, JSON Schema, Markdown.

---

## Execution rules

- Use `@test-driven-development` for every runtime change.
- Use `@cam-codx-session` for path/config/corpus preflight.
- Use `@cam-mine-repos` for scan, live mining, and corpus verification.
- Use `@verification-before-completion` before any completion claim.
- Do not edit the dirty live CAM_CAM checkout directly.
- Do not reset, delete, stage, or commit its modified `claw.toml` or SQLite sidecars.
- Never print `.env` values; check key presence by name only.
- Do not execute repository code or install repository dependencies.
- Benchmark execution must disable cross-model fallback.
- Stop before a request that would exceed either approved budget.
- Commit CAM_CAM runtime and CAM_Codx workflow changes separately.

## Canonical paths

```text
CAM_Codx source:     /Volumes/WS4TB/repo622sn/CAM_Codx
CAM_Codx worktree:   /Volumes/WS4TB/repo622sn/.worktrees/CAM_Codx-model-benchmark
CAM_CAM source:      /Volumes/WS4TB/repo622sn/CAM_CAM
CAM_CAM worktree:    /Volumes/WS4TB/repo622sn/.worktrees/CAM_CAM-model-benchmark
Live config:         /Volumes/WS4TB/repo622sn/CAM_CAM/claw.toml
Live corpus:         /Volumes/WS4TB/repo622sn/CAM_CAM/claw.db
Live env:            /Volumes/WS4TB/repo622sn/CAM_CAM/.env
Repo root 1:         /Volumes/WS4TB/repo622sn
Repo root 2:         /Volumes/WS4TB/waswiki/repos2mine
```

### Task 1: Prove the clean two-repo implementation workspace

**Files:**
- Create: `CAM_Codx/docs/reports/model-benchmark/IMPLEMENTATION_BASELINE.md`
- Modify: none in the live CAM_CAM checkout

**Step 1: Verify the CAM_Codx worktree**

```bash
git -C /Volumes/WS4TB/repo622sn/.worktrees/CAM_Codx-model-benchmark status --short --branch
git -C /Volumes/WS4TB/repo622sn/.worktrees/CAM_Codx-model-benchmark rev-parse HEAD
```

Expected: branch `codex/cam-model-benchmark-manager`, based on `ae23006`, with a clean tree after the plan commit.

**Step 2: Record the dirty live CAM_CAM checkout**

```bash
git -C /Volumes/WS4TB/repo622sn/CAM_CAM status --short --branch
git -C /Volumes/WS4TB/repo622sn/CAM_CAM rev-parse HEAD
git -C /Volumes/WS4TB/repo622sn/CAM_CAM remote -v
```

Expected: `claw.toml` and any SQLite sidecars remain visible and untouched.

**Step 3: Create the clean CAM_CAM worktree**

```bash
git -C /Volumes/WS4TB/repo622sn/CAM_CAM worktree add \
  -b codex/cam-model-benchmark-runtime \
  /Volumes/WS4TB/repo622sn/.worktrees/CAM_CAM-model-benchmark \
  db5495a
```

**Step 4: Run baseline tests**

```bash
cd /Volumes/WS4TB/repo622sn/.worktrees/CAM_CAM-model-benchmark
python -m pytest -q tests/test_config.py tests/test_llm.py tests/test_openrouter.py \
  tests/test_miner.py tests/test_mining_enhancements.py tests/test_cli_ux.py
```

Expected: focused baseline tests pass. Record exact pre-existing failures without changing scope.

**Step 5: Write and commit the receipt**

Record both repo HEADs, branches, dirty state, Python and `cam` provenance, commands, and results.

```bash
git add docs/reports/model-benchmark/IMPLEMENTATION_BASELINE.md
git commit -m "docs: record CAM benchmark implementation baseline"
```

### Task 2: Add a typed OpenRouter catalog client

**Files:**
- Create: `CAM_CAM/src/claw/models/__init__.py`
- Create: `CAM_CAM/src/claw/models/catalog.py`
- Create: `CAM_CAM/tests/fixtures/openrouter_models.json`
- Create: `CAM_CAM/tests/test_model_catalog.py`

**Step 1: Write failing tests**

Cover all eight IDs, per-million price normalization, DeepSeek alias metadata, Gemini batch classification, Grok's >200K override, context/output limits, supported parameters, expiration, malformed responses, and stable digests.

```python
from claw.models.catalog import ModelCatalog

entry = ModelCatalog.from_payload(payload).require("openai/gpt-5.6-luna")
assert entry.pricing.prompt_per_million == 0.10
assert entry.supports("structured_outputs")
```

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_model_catalog.py
```

Expected: FAIL because the module is absent.

**Step 3: Implement the public contract**

```python
class ModelPricing(BaseModel):
    prompt_per_million: float = 0.0
    completion_per_million: float = 0.0
    cached_input_per_million: float | None = None
    reasoning_per_million: float | None = None
    overrides: list[dict[str, Any]] = Field(default_factory=list)

class ModelCatalogEntry(BaseModel):
    requested_id: str
    canonical_slug: str | None = None
    name: str
    context_length: int
    max_completion_tokens: int | None = None
    supported_parameters: frozenset[str]
    pricing: ModelPricing
    expiration_date: str | None = None
    catalog_digest: str

    @property
    def is_batch(self) -> bool:
        return self.requested_id.endswith(":batch")

class OpenRouterCatalogClient:
    async def fetch(self) -> ModelCatalog:
        ...
```

Use bounded `httpx` timeouts and the public models endpoint. Never log headers or keys.

**Step 4: Verify and commit**

```bash
python -m pytest -q tests/test_model_catalog.py
python -m ruff check src/claw/models tests/test_model_catalog.py
git add src/claw/models tests/test_model_catalog.py tests/fixtures/openrouter_models.json
git commit -m "feat(models): add live OpenRouter catalog client"
```

### Task 3: Add one model-profile authority

**Files:**
- Create: `CAM_CAM/model_profiles.toml`
- Create: `CAM_CAM/src/claw/models/profiles.py`
- Modify: `CAM_CAM/src/claw/core/config.py:575-735`
- Create: `CAM_CAM/tests/test_model_profiles.py`

**Step 1: Write failing tests**

Test schema and active-profile parsing; roles `mining-budget`, `mining-quality`, `mining-batch`, `verification`, and `fallback`; database-path immutability; unknown role/model rejection; atomic promotion; rollback; and base-config authority.

```toml
schema_version = 1
active_profile = "legacy-import"

[profiles.legacy-import.roles]
mining-budget = "z-ai/glm-5.2"
mining-quality = "z-ai/glm-5.2"
mining-batch = ""
verification = "x-ai/grok-4.3"
fallback = "openai/gpt-4.1-mini"
```

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_model_profiles.py
```

**Step 3: Implement profiles and atomic writes**

```python
class ModelProfileRegistry(BaseModel):
    schema_version: int = 1
    active_profile: str
    profiles: dict[str, ModelProfile]

def load_model_profiles(path: Path) -> ModelProfileRegistry: ...
def resolve_effective_config(base: ClawConfig, registry: ModelProfileRegistry) -> ClawConfig: ...
def promote_role(path: Path, profile: str, role: str, model_id: str) -> PromotionReceipt: ...
def rollback_promotion(path: Path, receipt: PromotionReceipt) -> None: ...
```

Use a sibling temporary file plus `Path.replace()`. Overlays cannot contain database, security, or secret fields. Keep legacy behavior unchanged unless a profile file is explicitly selected.

**Step 4: Verify and commit**

```bash
python -m pytest -q tests/test_model_profiles.py tests/test_config.py tests/test_fallback_path.py
git add model_profiles.toml src/claw/models/profiles.py src/claw/core/config.py tests/test_model_profiles.py
git commit -m "feat(models): add role-based model profiles"
```

### Task 4: Register the modular `cam models` CLI

**Files:**
- Create: `CAM_CAM/src/claw/cli/models.py`
- Modify: `CAM_CAM/src/claw/cli/_monolith.py:27-110,10092-10102`
- Modify: `CAM_CAM/src/claw/cli/__init__.py`
- Create: `CAM_CAM/tests/test_models_cli.py`

**Step 1: Write failing discovery tests**

Require `current`, `catalog --live`, profile list/show/use, `set`, and `rollback`. Verify `current` reports config/profile/database paths without environment values.

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_models_cli.py tests/test_cli_ux.py
```

**Step 3: Implement Typer sub-apps**

Define `models_app` and `profile_app` in `claw/cli/models.py`, then register:

```python
from claw.cli.models import models_app
app.add_typer(models_app, name="models")
```

Use a local `Console` to avoid circular imports. Catalog presents facts only; `set` validates live availability before promotion.

**Step 4: Verify and commit**

```bash
python -m pytest -q tests/test_models_cli.py tests/test_cli_ux.py tests/test_config.py
python -m claw.cli models --help
git add src/claw/cli/models.py src/claw/cli/_monolith.py src/claw/cli/__init__.py tests/test_models_cli.py
git commit -m "feat(cli): add CAM model management commands"
```

### Task 5: Capture frozen production mining prompts

**Files:**
- Modify: `CAM_CAM/src/claw/miner.py:1266-1360,2176-2240,3060-3115`
- Create: `CAM_CAM/src/claw/models/benchmark.py`
- Create: `CAM_CAM/benchmarks/mining-v1.toml`
- Create: `CAM_CAM/tests/test_mining_prompt_fixture.py`

**Step 1: Write failing tests**

```python
fixture = await miner.prepare_mining_prompt(repo_path, "fixture-repo", "python", set())
assert fixture.prompt_sha256 == sha256(fixture.prompt.encode()).hexdigest()
assert fixture.repo_content_sha256
assert fixture.source_manifest
assert db_write_spy.call_count == 0
```

Test stable output after mtime-only changes and changed hash after source changes.

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_mining_prompt_fixture.py
```

**Step 3: Refactor the production path**

Add `MiningPromptFixture` with repo identity, HEAD, dirty state, brain, prompt/hash, content hash, paths, bytes, and estimated tokens. Move the existing sequence into `prepare_mining_prompt` and call it from normal mining so production and benchmark cannot drift.

**Step 4: Add the logical suite**

`benchmarks/mining-v1.toml` contains names, languages, and stages but no private paths. Use `Codx_LoopKit`, `atomic-agent`, `RedaktSafe`, `OpenCLI`, and `OpenViking`, subject to clean fingerprint validation.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_mining_prompt_fixture.py tests/test_miner.py tests/test_mining_enhancements.py
git add src/claw/miner.py src/claw/models/benchmark.py benchmarks/mining-v1.toml tests/test_mining_prompt_fixture.py
git commit -m "feat(benchmark): freeze production mining prompts"
```

### Task 6: Build the no-spend planner and hard budget gate

**Files:**
- Modify: `CAM_CAM/src/claw/models/benchmark.py`
- Modify: `CAM_CAM/src/claw/cli/models.py`
- Modify: `CAM_CAM/.gitignore`
- Create: `CAM_CAM/tests/test_benchmark_planner.py`

**Step 1: Write failing tests**

Test frozen catalog digests, alias resolution, prompt hashes, repo commits, overrides, batch separation, three-fixture first round, top-four withheld round, top-two repeat, rejection above $5, no completion/DB calls, and no raw prompts in tracked summaries.

```python
plan = planner.plan(suite, catalog, budget_usd=5.0)
assert plan.maximum_cost_usd <= 5.0
assert plan.status == "planned"
```

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_benchmark_planner.py
```

**Step 3: Implement plans and local storage**

Add `BenchmarkPlan`, `PlannedCall`, `BudgetLedger`, and `CatalogReceipt`. Store ignored local data under `data/model_benchmarks/<run-id>/`; full prompts are mode `0600`, tracked summaries contain only hashes and relative manifests.

**Step 4: Add the CLI**

```text
cam models benchmark plan --suite benchmarks/mining-v1.toml \
  --repo-root ROOT --repo-root ROOT --budget-usd 5 --output RUN_DIR
```

It prints `NO PAID CALLS MADE`, projected maximum cost, and the outbound manifest.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_benchmark_planner.py tests/test_models_cli.py
git add .gitignore src/claw/models/benchmark.py src/claw/cli/models.py tests/test_benchmark_planner.py
git commit -m "feat(benchmark): add frozen budgeted run plans"
```

### Task 7: Execute exact candidates with actual usage receipts

**Files:**
- Modify: `CAM_CAM/src/claw/llm/client.py:31-275`
- Modify: `CAM_CAM/src/claw/models/benchmark.py`
- Modify: `CAM_CAM/tests/test_llm.py`
- Create: `CAM_CAM/tests/test_benchmark_runner.py`

**Step 1: Write failing receipt tests**

```python
assert response.input_tokens == 100
assert response.output_tokens == 20
assert response.reasoning_tokens == 5
assert response.cost_usd == 0.00123
assert response.request_id == "gen-123"
assert response.model == "deepseek/deepseek-v4-flash-0731"
```

Missing provider cost must be labelled `cost_source="estimated"`, never silently filled with a default.

**Step 2: Write failing runner tests**

Require one requested model per call, same-model retry only, no `complete_with_fallback`, authorization before each request, actual-cost reconciliation, alias-drift abort, prompt/source-drift abort, atomic receipts, resumability, and secret-redacted errors.

**Step 3: Verify failure**

```bash
python -m pytest -q tests/test_llm.py tests/test_benchmark_runner.py
```

**Step 4: Implement metadata parsing and the bounded runner**

Parse OpenRouter usage cost, cached/reasoning tokens, response ID, returned model, finish reason, and optional routing metadata. Before every call:

```python
ledger.authorize(maximum_call_cost)
assert fixture.still_matches_source()
assert catalog_entry.catalog_digest == plan.catalog_digest_for(model_id)
```

Use a fresh client or reset circuit state between candidate models. Persist each response before continuing.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_llm.py tests/test_benchmark_runner.py tests/test_openrouter.py tests/test_fallback_path.py
git add src/claw/llm/client.py src/claw/models/benchmark.py tests/test_llm.py tests/test_benchmark_runner.py
git commit -m "feat(benchmark): run models with exact cost receipts"
```

### Task 8: Add the Gemini batch compatibility lane

**Files:**
- Create: `CAM_CAM/src/claw/models/batch.py`
- Modify: `CAM_CAM/src/claw/models/benchmark.py`
- Modify: `CAM_CAM/src/claw/cli/models.py`
- Create: `CAM_CAM/tests/test_batch_benchmark.py`

**Step 1: Write failing state tests**

Cover `unsupported`, `submitted`, `queued`, `running`, `completed`, `failed`, and `timed_out`. Batch results cannot receive first-token or synchronous latency rankings.

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_batch_benchmark.py
```

**Step 3: Implement compatibility-first behavior**

The first paid action is a tiny smoke against `google/gemini-3.6-flash:batch`. If chat completions returns a response, record `transport="chat-completions-batch-variant"`. If it returns a job contract, persist the job ID and poll with bounded backoff. Otherwise mark `unsupported`; do not invent private endpoints.

Strip unsupported parameters from the frozen catalog entry. Do not send `temperature` or `seed` to this candidate; record the deviation.

**Step 4: Verify and commit**

```bash
python -m pytest -q tests/test_batch_benchmark.py tests/test_benchmark_runner.py
git add src/claw/models/batch.py src/claw/models/benchmark.py src/claw/cli/models.py tests/test_batch_benchmark.py
git commit -m "feat(benchmark): add explicit batch model lane"
```

### Task 9: Validate provenance and generate blinded quality reports

**Files:**
- Create: `CAM_CAM/src/claw/models/scoring.py`
- Modify: `CAM_CAM/src/claw/cli/models.py`
- Create: `CAM_CAM/tests/test_benchmark_scoring.py`

**Step 1: Write failing scoring tests**

Verify source paths remain inside the repo; files and symbols exist; invented provenance and secret-like output are hard failures; duplicate findings reduce novelty; malformed findings reduce reliability; model identity is absent from blinded packets; and quality weights total 100.

```python
score = score_candidate(findings, fixture, existing_methodologies)
assert score.grounded_correctness <= 35
assert score.novelty <= 25
assert score.hard_failures == []
```

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_benchmark_scoring.py
```

**Step 3: Implement scoring and review import**

Use stable anonymous candidate codes. Deterministic checks fill objective sub-scores and create a review packet for grounded/actionable/coverage judgment. Validate imported review JSON and reject identity leakage or out-of-range scores.

**Step 4: Add report commands**

```text
cam models benchmark review-export RUN_ID --output review.json
cam models benchmark review-import RUN_ID --input reviewed.json
cam models benchmark report RUN_ID --format markdown|json
```

Keep quality separate from cost/latency and show eligibility, three-point ties, and the Pareto frontier.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_benchmark_scoring.py tests/test_models_cli.py
git add src/claw/models/scoring.py src/claw/cli/models.py tests/test_benchmark_scoring.py
git commit -m "feat(benchmark): score grounded mining quality"
```

### Task 10: Gate promotion and rollback on benchmark evidence

**Files:**
- Modify: `CAM_CAM/src/claw/models/profiles.py`
- Modify: `CAM_CAM/src/claw/cli/models.py`
- Create: `CAM_CAM/tests/test_benchmark_promotion.py`

**Step 1: Write failing promotion tests**

Reject quality below 80, hard failures, incomplete reports, catalog drift, incompatible roles, benchmark/live DB equality, and missing rollback values. Prove `run` and `report` never promote automatically.

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_benchmark_promotion.py
```

**Step 3: Implement the receipt and live revalidation**

Store run/report digests, requested alias, resolved model, role/profile, previous model, timestamp, catalog digest, operator command, and rollback command. Re-fetch the catalog before atomic promotion.

**Step 4: Verify and commit**

```bash
python -m pytest -q tests/test_benchmark_promotion.py tests/test_model_profiles.py tests/test_models_cli.py
git add src/claw/models/profiles.py src/claw/cli/models.py tests/test_benchmark_promotion.py
git commit -m "feat(models): gate promotion on benchmark evidence"
```

### Task 11: Replace mtime eligibility with content-aware fingerprints

**Files:**
- Create: `CAM_CAM/src/claw/mining/fingerprint.py`
- Modify: `CAM_CAM/src/claw/miner.py:1020-1165,3962-4040`
- Modify: `CAM_CAM/tests/test_mining_enhancements.py`
- Create: `CAM_CAM/tests/test_repo_fingerprint.py`

**Step 1: Write failing fingerprint tests**

Require clean Git tree/HEAD identity, mtime invariance, tracked-content changes, relevant untracked `dirty_review`, ignored `.DS_Store`, content-based source trees, cross-root duplicates, and legacy ledger loading.

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_repo_fingerprint.py tests/test_mining_enhancements.py
```

Expected: the mtime regression fails under the current scan signature.

**Step 3: Implement versioned fingerprints**

```python
class RepoFingerprint(BaseModel):
    version: int = 2
    canonical_identity: str
    git_head: str | None
    tracked_tree: str | None
    content_sha256: str
    dirty_paths: list[str]
    classification: str
```

Clean Git uses canonical identity plus HEAD tree. Dirty Git records a diff/untracked digest but classifies `dirty_review`. Source trees stream eligible content through SHA-256.

**Step 4: Upgrade the ledger safely**

Add optional v2 fields. `should_mine` compares v2 fingerprint first, legacy content hash second, and mtime only when no content evidence exists. Save version 2 without dropping old records.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_repo_fingerprint.py tests/test_mining_enhancements.py tests/test_miner.py
git add src/claw/mining/fingerprint.py src/claw/miner.py tests/test_repo_fingerprint.py tests/test_mining_enhancements.py
git commit -m "fix(mining): use content-aware repository eligibility"
```

### Task 12: Execute exact mining manifests and verify all ganglia

**Files:**
- Create: `CAM_CAM/src/claw/mining/manifest.py`
- Create: `CAM_CAM/src/claw/mining/verification.py`
- Modify: `CAM_CAM/src/claw/cli/_monolith.py:5935-6140`
- Create: `CAM_CAM/tests/test_mining_manifest.py`
- Create: `CAM_CAM/tests/test_mining_verification.py`

**Step 1: Write failing manifest tests**

Test `new`, `content_updated`, `unchanged`, `duplicate`, `dirty_review`, `sensitive_quarantine`, `oversized_review`, and `self_mine_separate`. Require exact path/fingerprint/model profile/config/corpus/flags/time/cost fields.

**Step 2: Write failing CLI safety tests**

`cam mine --manifest PATH` mines only approved entries, rejects fingerprint drift, enforces corpus-only flags, rejects a different DB/config, leaves unrelated repos alone, and writes a partial receipt on interruption.

**Step 3: Write failing verifier tests**

Given temporary root/ganglion DBs, verify every methodology ID exists in the union or has an explicit duplicate reconciliation. Require SQLite integrity for every DB.

**Step 4: Implement planner, execution guard, and verifier**

Recompute fingerprints before initializing the LLM client or DB writer. Expose:

```text
cam mine-report ROOT --format json --content-aware
cam mine-verify RECEIPT.json --config ABSOLUTE_CLAW_TOML
```

Return expected/stored/missing/duplicates, per-DB integrity, ledger match, and source Git status.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_mining_manifest.py tests/test_mining_verification.py tests/test_miner.py tests/test_cli_ux.py
git add src/claw/mining/manifest.py src/claw/mining/verification.py src/claw/cli/_monolith.py tests/test_mining_manifest.py tests/test_mining_verification.py
git commit -m "feat(mining): execute frozen manifests with union verification"
```

### Task 13: Modernize the Codex subscription lane

**Files:**
- Modify: `CAM_CAM/src/claw/agents/codex.py:1-255`
- Create: `CAM_CAM/src/claw/models/codex_lane.py`
- Create: `CAM_CAM/tests/test_codex_subscription_lane.py`

**Step 1: Write failing command tests**

Require:

```text
codex exec --ephemeral --json --sandbox read-only \
  --output-schema SCHEMA --model MODEL --cd REPO -
```

Prohibit `--quiet` and unsafe bypasses; require timeout, stdin prompt, fixed CWD, and redacted environment.

**Step 2: Write failing state/parser tests**

Cover `subscription`, `api_billed`, `unavailable`, `quota_exhausted`, `policy_blocked`, malformed JSONL, and cancellation. An active Codex-host session must return `launch_packet_required`, not spawn recursively.

**Step 3: Verify failure**

```bash
python -m pytest -q tests/test_codex_subscription_lane.py
```

**Step 4: Implement the adapter and launch packet**

Use `asyncio.create_subprocess_exec`, explicit environment allowlisting, session/process cleanup, and JSONL usage parsing. Check auth only through `codex login status`; never read auth files. A launch packet contains argv, repo, schema, models, 100-credit ceiling, and receipt path for a separate clean terminal.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_codex_subscription_lane.py tests/test_openrouter.py tests/test_local_mode.py
git add src/claw/agents/codex.py src/claw/models/codex_lane.py tests/test_codex_subscription_lane.py
git commit -m "fix(codex): use safe subscription-backed exec adapter"
```

### Task 14: Make CAM_Codx the durable manager and enhancement gate

**Files:**
- Create: `docs/MODEL_BENCHMARK_AND_MINING_MANAGER.md`
- Create: `contracts/cam_enhancement_packet.schema.json`
- Create: `tools/validate_cam_enhancement_packets.py`
- Create: `tests/test_cam_enhancement_packets.py`
- Modify: `README.md`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`

**Step 1: Write failing enhancement-packet tests**

Require every packet to carry source methodology IDs, source repository/fingerprint, CAM owner, proposed destination, risk, consent boundary, acceptance checks, rollback, and one of `accepted`, `rejected`, `needs_investigation`, or `already_present`.

Reject packets with missing provenance, embedded source blobs, absolute secret paths, executable shell payloads, or an unsupported status.

**Step 2: Verify failure**

```bash
python -m pytest -q tests/test_cam_enhancement_packets.py
```

**Step 3: Implement the schema and validator**

The validator accepts JSON or YAML-derived JSON, validates one packet or a packet list, emits stable JSON diagnostics, and never imports or executes mined repository code.

**Step 4: Document the management boundary**

Document that CAM_Codx owns planning, budget approval, launch packets, review, promotion decisions, manifests, and enhancement packets. CAM_CAM owns catalog calls, model execution, mining, persistence, and verification. State that no model is promoted and no enhancement is applied automatically.

**Step 5: Verify and commit**

```bash
python -m pytest -q tests/test_cam_enhancement_packets.py
python tools/validate_cam_enhancement_packets.py --help
git diff --check
git add README.md DECISIONS.md PROGRESS.md \
  docs/MODEL_BENCHMARK_AND_MINING_MANAGER.md \
  contracts/cam_enhancement_packet.schema.json \
  tools/validate_cam_enhancement_packets.py tests/test_cam_enhancement_packets.py
git commit -m "feat: make CAM_Codx the mining program manager"
```

### Task 15: Run the complete implementation verification matrix

**Files:**
- Modify only files required to fix defects found by this task
- Create: `docs/reports/model-benchmark/IMPLEMENTATION_VERIFICATION.md`

**Step 1: Run the new focused tests in the CAM_CAM worktree**

```bash
python -m pytest -q \
  tests/test_model_catalog.py tests/test_model_profiles.py \
  tests/test_models_cli.py tests/test_mining_prompt_fixture.py \
  tests/test_benchmark_plan.py tests/test_benchmark_runner.py \
  tests/test_openrouter_batch.py tests/test_benchmark_scoring.py \
  tests/test_model_promotion.py tests/test_repo_fingerprint.py \
  tests/test_mining_manifest.py tests/test_mining_verification.py \
  tests/test_codex_subscription_lane.py
```

**Step 2: Run regression tests**

```bash
python -m pytest -q tests/test_config.py tests/test_llm.py tests/test_openrouter.py \
  tests/test_miner.py tests/test_mining_enhancements.py tests/test_cli_ux.py \
  tests/test_local_mode.py
```

**Step 3: Run CAM_Codx tests and static checks**

```bash
cd /Volumes/WS4TB/repo622sn/.worktrees/CAM_Codx-model-benchmark
python -m pytest -q tests/test_cam_enhancement_packets.py
python -m ruff check tools tests
git diff --check
```

**Step 4: Audit tracked outputs**

Confirm no `.env`, SQLite DB/WAL/SHM, raw prompts, credentials, provider responses containing private source, or paid-run artifacts are tracked. Record exact commands and results in the verification report.

**Step 5: Commit only defect fixes and the sanitized receipt**

```bash
git add docs/reports/model-benchmark/IMPLEMENTATION_VERIFICATION.md
git commit -m "test: verify CAM model and mining manager"
```

### Task 16: Produce a no-spend live benchmark plan

**Files:**
- Create: `docs/reports/model-benchmark/<run-id>-PLAN.md`
- Local only: benchmark plan JSON and outbound request manifest

**Step 1: Run the CAM session preflight**

Pin the source checkout, clean runtime worktree, installed CLI provenance, live config, live env, and authoritative corpus. Check only whether `OPENROUTER_API_KEY` is present; do not print its value.

**Step 2: Refresh the live catalog**

Resolve these requested candidates by exact returned ID or documented alias:

```text
google/gemini-3.6-flash:batch
qwen/qwen3.8-max
~deepseek/deepseek-v4-flash-latest
x-ai/grok-4.5
openai/gpt-5.6-terra
openai/gpt-5.6-luna
z-ai/glm-5.2
moonshotai/kimi-k3
```

Store timestamped pricing and capability metadata in the local run directory; commit only a sanitized summary.

**Step 3: Generate the benchmark plan without model calls**

```bash
cam models benchmark plan benchmarks/mining-v1.toml \
  --budget-usd 5 --codex-credits 100 --format json
```

Require catalog gate, tiny smoke, eight-candidate three-fixture stage, top-four heldout stage, top-two repeat, and isolated finalist mining. The Codex lane must be separate from the OpenRouter ranking.

**Step 4: Inspect the complete outbound manifest**

Confirm candidate IDs, prompts by hash, token ceilings, maximum calls, batch-vs-synchronous routing, no fallback, redactions, and worst-case spend `<= $5.00`. Do not execute until this inspection passes.

**Step 5: Save and commit the sanitized plan receipt**

```bash
git add docs/reports/model-benchmark/<run-id>-PLAN.md
git commit -m "docs: record capped CAM model benchmark plan"
```

### Task 17: Execute, review, and explicitly promote the capped benchmark

**Files:**
- Create: `docs/reports/model-benchmark/<run-id>-RESULTS.md`
- Create: `docs/reports/model-benchmark/<run-id>-REVIEW.json`
- Local only: raw responses, provider receipts, prompt bodies, and Codex launch/return packets

**Step 1: Execute the OpenRouter plan under the hard cap**

```bash
cam models benchmark run <plan.json> --budget-usd 5 --no-fallback
```

Stop before any request whose reserved maximum could cross the cap. Reconcile provider-reported usage and cost after every completed request. Poll the Gemini batch lane with bounded retries and preserve partial receipts on interruption.

**Step 2: Perform blinded quality review**

The current Codex orchestrator reviews anonymized outputs against the rubric: grounded correctness/provenance 35, novelty/nonduplication 25, actionable specificity 20, coverage/diversity 10, structured reliability 10. Record failure reasons and adjudication; do not use model identity during scoring.

**Step 3: Generate recommendations**

```bash
cam models benchmark report <run-dir> --format json
```

Enforce quality floor 80 and zero hard failures. When candidates are within three quality points, recommend the Pareto-cheaper/faster model. Produce proposed assignments for `mining-budget`, `mining-quality`, `mining-batch`, `verification`, and `fallback`.

**Step 4: Promote only evidence-qualified profiles**

```bash
cam models promote <review.json> --profile mining-budget --model <id>
```

Promotion must validate the review receipt, budget receipt, catalog snapshot, test suite, and explicit operator action. Record the previous profile for rollback. A profile with no qualifying candidate remains unchanged.

**Step 5: Generate the separate Codex subscription launch packet**

Because this run is already hosted by Codex, do not recursively invoke `codex exec`. Generate a clean-terminal launch packet capped at 100 credits; score its returned artifact separately and never mix it into raw-provider cost rankings.

**Step 6: Save and commit sanitized evidence**

```bash
git add docs/reports/model-benchmark/<run-id>-RESULTS.md \
  docs/reports/model-benchmark/<run-id>-REVIEW.json
git commit -m "docs: record CAM model benchmark evidence"
```

### Task 18: Mine only content-new or content-updated repositories

**Files:**
- Create: `docs/reports/mining/<run-id>-MANIFEST.md`
- Create: `docs/reports/mining/<run-id>-RESULTS.md`
- Local only: exact manifest JSON, per-batch receipts, rollback copy, and database sidecars

**Step 1: Build content-aware eligibility across both roots**

```bash
cam mine-report /Volumes/WS4TB/repo622sn --format json --content-aware
cam mine-report /Volumes/WS4TB/waswiki/repos2mine --format json --content-aware
```

Classify every discovered repository as `new`, `content_updated`, `unchanged`, `duplicate`, `dirty_review`, `sensitive_quarantine`, `oversized_review`, or `self_mine_separate`. Preserve canonical-path and cross-root duplicate evidence.

**Step 2: Inspect exceptional repositories**

Review dirty, oversized, sensitive, duplicate, and CAM self-mining entries individually. Do not infer eligibility from mtime. Do not execute repository code or ingest excluded secrets/build/vendor data.

**Step 3: Freeze small mining batches**

Each exact manifest pins canonical path, content fingerprint, selected model profile/model ID, live config, authoritative DB, flags, token/cost ceiling, and rollback receipt. Use `--no-tasks`, omit `--fast`, and omit `--self-assess`.

**Step 4: Dry-run every batch**

```bash
cam mine --manifest <batch.json> --scan-only
```

Require zero fingerprint drift, the correct source-loaded CLI, the explicit live config/env, and `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db` as the root corpus.

**Step 5: Mine and verify one batch at a time**

```bash
cam mine --manifest <batch.json>
cam mine-verify <receipt.json> \
  --config /Volumes/WS4TB/repo622sn/CAM_CAM/claw.toml
```

After every batch require SQLite integrity, methodology presence in the root-plus-ganglia union or explicit duplicate reconciliation, ledger/fingerprint match, charged cost, and unchanged source Git state. Stop immediately on a failed verification or budget breach risk.

**Step 6: Commit only sanitized mining reports**

```bash
git add docs/reports/mining/<run-id>-MANIFEST.md \
  docs/reports/mining/<run-id>-RESULTS.md
git commit -m "docs: record verified incremental CAM mining"
```

### Task 19: Synthesize mined ideas into reviewable enhancement packets

**Files:**
- Create: `docs/reports/enhancements/<run-id>-SYNTHESIS.md`
- Create: `docs/reports/enhancements/<run-id>-PACKETS.json`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`

**Step 1: Query only reconciled corpus entries**

Use the post-mining verification receipt to select methodology IDs. Include `/Volumes/WS4TB/repo622sn/camidea3.md` as an explicit source with its content fingerprint and keep source claims separate from CAM recommendations.

**Step 2: Assess prime-agent-style management ideas**

Evaluate durable goals, task queues, heartbeats, addressable specialists, and refinement history for CAM_Codx. Explicitly reject unrestricted Python REPL execution, uncontrolled fire-and-forget tasks, unreviewed self-editing, secret propagation, and any bypass of CAM consent/provider boundaries.

**Step 3: Produce enhancement packets**

For each idea, assign `accepted`, `rejected`, `needs_investigation`, or `already_present`, with evidence, target owner, risk, minimal implementation slice, tests, rollback, and provenance. Similar mined ideas must be reconciled rather than counted as independent support.

**Step 4: Validate and dry-run**

```bash
python tools/validate_cam_enhancement_packets.py \
  docs/reports/enhancements/<run-id>-PACKETS.json
cam camify docs/reports/enhancements/<run-id>-SYNTHESIS.md --dry-run
cam enhance docs/reports/enhancements/<run-id>-PACKETS.json --dry-run
```

Do not apply runtime enhancements in this task. Stop for explicit acceptance of named packets before any CAM_CAM or CAM_Codx behavior change.

**Step 5: Record decisions and commit**

```bash
git add DECISIONS.md PROGRESS.md docs/reports/enhancements/<run-id>-SYNTHESIS.md \
  docs/reports/enhancements/<run-id>-PACKETS.json
git commit -m "docs: synthesize mined CAM enhancement candidates"
```

## Final completion gate

The project is complete only when all of the following are true:

- Both implementation worktrees pass their focused and regression suites.
- The live model catalog and paid-run receipts are timestamped, budget-reconciled, and sanitized for committed reports.
- OpenRouter spend is at most $5 and Codex usage is at most 100 credits.
- No model profile was promoted without a quality score of at least 80, zero hard failures, and explicit promotion evidence.
- Every mined repository was selected by a versioned content fingerprint, not mtime alone.
- Every mining batch passed root-plus-ganglia union verification and SQLite integrity checks.
- Source repositories remained unchanged by mining.
- `camidea3.md` and reconciled new methods produced schema-valid enhancement packets with explicit dispositions.
- No enhancement was applied without a separate accepted packet.
- Dirty live files, SQLite sidecars, secrets, and the pre-existing untracked `GOAL_CAM_SUBSCIBED.md` were preserved and excluded from commits.
