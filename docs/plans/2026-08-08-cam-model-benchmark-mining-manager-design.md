# CAM Model Benchmark, Mining Manager, and Enhancement Synthesis Design

**Date:** 2026-08-08  
**Status:** Approved  
**Program manager:** CAM_Codx  
**Runtime and corpus owner:** CAM_CAM

## Purpose

Give CAM a user-friendly, evidence-based way to discover current models,
compare them on real CAM mining work, recommend role-specific profiles, and
promote a selected model without silently changing the live runtime. After
promotion, CAM_Codx will manage content-aware incremental mining across the two
approved repository roots and turn useful mined ideas into bounded,
verification-backed enhancement proposals for CAM_Codx and CAM_CAM.

The design extends the existing model-management contract in `GOAL_CAM_UPD.md`.
That contract already defines live catalog lookup, role-based profiles, and
explicit selection. This design adds task-specific benchmarking,
recommendation, promotion, content-fingerprint mining plans, and post-mining
synthesis.

## Ownership and boundaries

CAM_Codx is the program manager. It owns:

- the benchmark specification and candidate manifest;
- catalog snapshots, price/capability receipts, and budget approval;
- run planning, score reports, recommendations, and promotion approvals;
- repository eligibility manifests and mining batches;
- post-mining idea synthesis and enhancement decision packets;
- durable progress, decision, verification, and rollback records.

CAM_CAM is the runtime. It owns:

- exact mining-prompt construction and bounded prompt capture;
- OpenRouter and supported local/host adapter calls;
- model response parsing and deterministic validation;
- isolated benchmark databases and artifact persistence;
- model-profile loading and promotion mechanics;
- live mining, corpus writes, ganglion routing, and persistence verification.

The authoritative live corpus remains:

```text
/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db
```

Every corpus-dependent command must also pin `CAM_CODEX_MCP_DB_PATH` to the
same file and pass the matching absolute `claw.toml`. Benchmark runs must not
write to that database.

## Candidate model manifest

The first approved mining benchmark contains these OpenRouter identifiers:

```text
openai/gpt-5.6-luna
openai/gpt-5.6-terra
z-ai/glm-5.2
moonshotai/kimi-k3
google/gemini-3.6-flash:batch
qwen/qwen3.8-max
~deepseek/deepseek-v4-flash-latest
x-ai/grok-4.5
```

The manifest stores identifiers, not assumed capabilities or prices. Before
each run, CAM retrieves the live catalog and records:

- requested and resolved model identifiers;
- provider and endpoint availability;
- input, cached-input, output, reasoning, request, and tool prices where
  present;
- context and maximum-output limits;
- supported parameters and structured-output capability;
- expiration/deprecation state;
- retrieval time and a digest of the catalog entry.

The DeepSeek `~...-latest` alias is intentionally fluid. A run is invalid if
the alias resolves to different underlying models during one comparison. The
report shows both the alias result and the fixed resolved model so an operator
can choose freshness or reproducibility for production.

Gemini Flash batch is a distinct execution lane. It does not receive a latency
ranking against synchronous models, and unsupported parameters are never
silently treated as equivalent. A compatibility smoke determines whether the
current OpenRouter chat client can use it directly or whether CAM requires a
dedicated batch adapter.

## User-facing workflow

Extend the planned `cam models` family with a benchmark surface:

```text
cam models catalog --live
cam models benchmark plan --suite mining-v1 --budget-usd 5
cam models benchmark run RUN_ID
cam models benchmark show RUN_ID
cam models benchmark report RUN_ID
cam models benchmark promote RUN_ID --profile PROFILE
```

`plan` is read-only. It freezes the suite, repository commits, prompt hashes,
candidate catalog entries, supported-parameter intersection, maximum requests,
and worst-case estimated cost. It fails if the estimate exceeds the approved
budget.

`run` requires an approved plan identifier. It writes only local benchmark
artifacts and isolated temporary databases. It cannot promote a model or write
to the live corpus.

`report` produces human-readable Markdown and machine-readable JSON. It keeps
quality, reliability, latency, tokens, and cost as separate dimensions and
shows the Pareto frontier.

`promote` is explicit and auditable. It validates that the selected model is
still available and compatible, records the prior profile, changes only the
named role/profile, and provides a rollback command. No benchmark winner is
activated automatically.

## Benchmark design

### Frozen workload

`mining-v1` uses clean, previously mined repositories at recorded commits so
outputs can be checked against known source and prior CAM findings. The suite
covers:

- small Python;
- TypeScript;
- security-sensitive Python;
- Rust or Go;
- a larger polyglot agent or memory repository.

Candidate fixtures include clean, unchanged repositories such as
`Codx_LoopKit`, `atomic-agent`, `RedaktSafe`, `OpenCLI`, and `OpenViking`,
subject to pre-run fingerprint validation. The finalized suite manifest stores
the exact repo path, Git commit, dirty-state receipt, language zone, selected
files, prompt hash, input byte count, and estimated tokens.

Source repositories are read only. CAM does not execute their code, install
dependencies, or modify their worktrees.

### Stage 1: catalog and compatibility

For every candidate:

1. Resolve the live catalog entry.
2. Validate context capacity and structured-output requirements.
3. Determine the supported parameter set.
4. Estimate worst-case cost from the frozen prompts and output caps.
5. Reject or separately classify incompatible candidates before paid work.

### Stage 2: bounded smoke

Send one small structured mining request to every compatible model. Record:

- success or typed failure;
- requested and returned model;
- parse validity;
- input, cached, reasoning, and output tokens when available;
- actual provider cost or a catalog-derived estimate clearly labelled as
  estimated;
- queue, first-token, and total latency when available;
- request/provider receipt identifiers without credentials.

Fallback is disabled. A failure belongs to the requested candidate and cannot
be hidden by another model.

### Stage 3: common prompt replay

Every synchronous candidate receives the same CAM-produced prompt, input
content, output schema, and maximum output allowance. Parameters that are not
shared across candidates are omitted or recorded as a deliberate per-lane
deviation. Provider-default behavior is never presented as deterministic.

All eight candidates run on three first-round fixtures. The top four quality
passers advance to two withheld fixtures. The top two repeat one fixture to
measure stability. Successive halving limits spend without letting the cheapest
model win solely on price.

### Stage 4: isolated full mining

Finalists run through the complete CAM mining path against disposable database
copies or freshly initialized temporary corpora. This stage verifies parsing,
assimilation compatibility, ganglion routing, receipt accuracy, and the absence
of live-corpus writes. Temporary artifacts are retained long enough for review
and then removed through an explicit cleanup action.

## Scoring and selection

Quality is scored out of 100:

- 35 points: grounded correctness and provenance;
- 25 points: novelty and non-duplication against the current corpus;
- 20 points: actionable specificity;
- 10 points: coverage and diversity;
- 10 points: structured-output and parsing reliability.

Deterministic checks verify referenced paths and symbols, schema validity,
duplicate rates, forbidden secret material, and consistency between evidence
and claims. Outputs are anonymized before qualitative review so the judge does
not see the provider/model name.

Cost, latency, token use, batch completion time, and failure rate remain
separate metrics. A candidate is promotion-eligible only when it:

- scores at least 80/100 overall;
- has no secret/privacy or invented-provenance failure;
- completes the finalist suite without an unhandled parse failure;
- remains within the role's context and output limits.

Among models within three quality points, CAM recommends the least expensive
and faster Pareto option. Reports may recommend different models for:

- `mining-budget`;
- `mining-quality`;
- `mining-batch`;
- `verification`, preferably from a different provider family;
- `fallback`.

Recommendations do not equal promotion. The operator selects the profile.

## Codex subscription lane

Terra and Luna are also evaluated as a Codex-host workflow. This lane is kept
separate because `codex exec` is an agentic tool-using harness rather than the
same raw OpenRouter completion interface.

The adapter may run only when:

- `codex login status` confirms ChatGPT-managed authentication;
- the process is not recursively launched from an active Codex-hosted CAM
  session;
- it uses `codex exec --ephemeral`, a read-only sandbox, a fixed working
  directory, bounded timeout, and a structured output schema;
- the planned run stays below the approved 100-Codex-credit ceiling;
- no authentication files or tokens are read or logged.

If the current environment is already hosted by Codex, the manager writes a
separate launch packet for execution from a clean terminal rather than spawning
another Codex process recursively.

## Incremental mining plan

The current ledger uses a modification-time-based scan signature, which can
classify copied or retimestamped repositories as changed. Before live mining,
CAM_Codx creates an eligibility manifest using:

- canonical repository identity;
- Git HEAD when available;
- tracked-content digest;
- relevant untracked-content digest or quarantine reason;
- prior successful mining content hash and methodology receipt;
- duplicate-content detection across both approved roots.

The approved roots are:

```text
/Volumes/WS4TB/repo622sn
/Volumes/WS4TB/waswiki/repos2mine
```

Repositories are classified as `new`, `content_updated`, `unchanged`,
`duplicate`, `dirty_review`, `sensitive_quarantine`, `oversized_review`, or
`self_mine_separate`. Only `new` and `content_updated` enter normal mining.

Mining occurs in bounded batches by size and risk. Normal commands use
`--no-tasks`, do not use `--fast` or `--self-assess`, pin both corpus variables,
and record the exact model profile and cost ceiling. CAM_CAM and CAM_Codx
self-mining are separate supervised batches.

Completion requires:

- mining-result and ledger reconciliation;
- SQLite integrity checks;
- verification across the root database plus all configured language
  ganglia;
- exact methodology-ID reconciliation;
- unchanged source-repository Git status;
- a durable mining report in CAM_Codx.

## Idea synthesis and enhancement

After mining, CAM_Codx compares `camidea3.md` and newly mined findings against
the current CAM_Codx/CAM_CAM architecture. Each candidate becomes an
evidence-linked enhancement packet containing:

- source repo, file, symbol, and methodology provenance;
- the CAM problem it addresses;
- whether it is new, overlapping, or already implemented;
- ownership in CAM_Codx or CAM_CAM;
- security, privacy, cost, and operational risks;
- a bounded implementation outline;
- tests, rollback, and proof gates.

Prime-agent concepts such as durable goals, run queues, heartbeats, addressable
specialists, and refinement history may inform the CAM_Codx manager. CAM will
not adopt unrestricted persistent Python execution, uncontrolled fire-and-
forget work, or self-editing without review and rollback.

Enhancement proceeds through `cam camify`, `cam enhance --dry-run`, explicit
packet acceptance, one bounded implementation slice, tests, diff review, and
outcome recording. Mining consent does not authorize enhancement writes.

## Failure handling and stop rules

The manager stops without promotion or live mining when:

- live catalog retrieval fails or an ID disappears;
- an alias changes resolution during a run;
- projected or actual OpenRouter spend reaches $5;
- projected or actual Codex usage reaches 100 credits;
- a candidate silently falls back to a different model;
- a source fingerprint changes after plan approval;
- secret, PHI, credential, license, or policy risk is detected;
- the authoritative database/config cannot be pinned unambiguously;
- a benchmark or mining receipt cannot be reconciled;
- repeated provider or verification failure persists after bounded mitigation.

Partial results remain labelled partial. A successful API response, non-empty
finding list, or smoke test alone is not evidence of mining quality or corpus
completion.

## Verification requirements

Implementation must include unit and integration coverage for:

- catalog parsing, price normalization, alias resolution, and capability
  compatibility;
- dry-run cost estimation and hard budget enforcement;
- no-fallback candidate execution;
- batch-lane classification;
- prompt and source fingerprint immutability;
- structured parse and provenance validation;
- blinded scoring and deterministic tie-breaking;
- isolated database behavior and proof of no live-corpus mutation;
- explicit profile promotion and rollback;
- content-aware repo eligibility and cross-root deduplication;
- root-plus-ganglion persistence reconciliation;
- secret redaction and receipt hygiene.

The initial live benchmark is capped at $5 in OpenRouter spend and 100 Codex
credits. Paid calls begin only after implementation tests, a successful dry-run
plan, and inspection of the frozen outbound manifest.
