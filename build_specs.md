# Codex-CAM Methodology — Engineering Build Specification (v1)

> **Status:** specification only. No code has been written. No claim of "production ready" or "complete" applies until every validation gate below is closed.
> **Source of truth for context:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/HANDOFF_LATEST.md`
> **Corpus reality (verified 2026-05-17):** 107 methodologies (95 `viable` + 12 `embryonic`), 96 `methodology_usage_log` rows, **0** `methodology_bandit_outcomes`, **0** `methodology_fitness_log`, **1** `failure_knowledge` row. The framing here is *seed corpus*, not mature library.
> **Hard constraints inherited from the workspace policy file at `/Volumes/WS4TB/CLAUDE.md`:** no mock / no placeholder / no simulation; no timeframes; no cost or revenue estimates; validation gates between every step; ≥90% line coverage with action plan for any gap; never claim "production ready" while remaining work exists.

---

## 0. Glossary and naming

| Term | Meaning |
|---|---|
| `claw` | Existing Python package at `CAM_CAM/src/claw/` |
| `claw.mcp_server` | The existing 17-tool MCP at `CAM_CAM/src/claw/mcp_server.py` (1,782 lines). **Out of scope; do not modify.** |
| `claw_codex_mcp` | The **new** thin MCP package built by this spec. Sibling module under the same package. |
| `cam.db` shorthand | `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db` |
| "Skill" | A `.codex/skills/<name>/SKILL.md` folder-based Codex skill |
| "Methodology" | A row in the `methodologies` table (schema at `CAM_CAM/src/claw/db/schema.sql:104-136`) |
| Outcome ledger | New append-only table `codex_outcome_log` (defined in §5) |

---

## 1. Architecture

### 1.1 The three planes

**Plane A — Codex (orchestrator).** OpenAI Codex CLI running `gpt-5.5` with `model_reasoning_effort = "high"` (see `.codex/config.toml:1-3`). It is markdown-native and reads `GOAL.md / STANDARDS.md / IMPLEMENT.md / DECISIONS.md / PROGRESS.md / TASK_QUEUE.md` first (see `.codex/AGENTS.md:5-14`). All workflow logic, doctrine, and output schema live here as skills and AGENTS.md text. **Codex is the sole decision-maker.**

**Plane B — Codex-CAM MCP (thin librarian).** A new Python module `claw_codex_mcp` exposing exactly four tools over stdio. Read-mostly facade over `cam.db`. Append-only write for the outcome ledger. The librarian metaphor is load-bearing: it answers questions about the corpus and records outcomes; it does not decide, mine, evolve, or invoke LLMs. Hard 4-tool ceiling enforced by a CI test (see §10.5).

**Plane C — CAM_CAM (heavy engine, optional).** Mining, bandit updates, evolution, federation, dashboards, prism analysis, capability synthesis. All ~40 modules under `CAM_CAM/src/claw/`. Runs **out of band** on its own schedule when installed. **Plane B does not require Plane C.** When `claw.db` is present, the MCP reads it for recall/provenance and writes outcomes into a Codex-tagged table. When absent, the MCP runs in standalone mode (see §1.3); CAM_CAM is then simply not part of the system.

### 1.3 Operating modes

The MCP detects its mode at startup. Three modes are observable:

| Mode | Trigger | `cam_recall` / `cam_provenance` | `cam_decisions_search` | `cam_record_outcome` | Logged at startup |
|---|---|---|---|---|---|
| `connected` | `CAM_CODEX_MCP_DB_PATH` set + path resolves + `methodologies` table present | Fully active, ranked results | Fully active | Writes to `claw.db.codex_outcome_log` (default) | `mode=connected corpus=<path> methodologies=<count>` |
| `standalone` | env var unset OR path missing OR open fails OR table absent | `{results: [], corpus_status: "absent", reason, remediation}` — honest empty, never fabricates | Fully active (this tool has zero CAM_CAM dependency) | Writes to `${CAM_CODEX_MCP_OUTCOME_DB_PATH:-~/.cam_codex_mcp/codex_outcome_log.db}` | `mode=standalone corpus=absent outcome_db=<path>` |
| `degraded` | claw.db reachable but `methodology_embeddings` (sqlite-vec) fails to load | Active with FTS-only fallback; results carry `corpus_status: "degraded"` | Active | Writes to connected location | `mode=connected corpus=<path> vec=unavailable` |

**Detection rule:** the mode check runs once at process startup. The active mode is immutable for the process lifetime — no per-call re-detection (avoids race conditions and ambiguous failure modes).

**Every tool response includes a `corpus_status` field** with one of: `connected`, `empty`, `absent`, `degraded`. Skills read this field and surface the mode to the user.

### 1.4 Boundary rule (single source of every other decision)

> **Stateful + cross-repo + computational → MCP tool.**
> **Doctrine + workflow + output schema → Skill (markdown).**
> **Anything that fits in markdown → Markdown.**

This rule is reproduced verbatim in `.codex/AGENTS.md` (see §7) and is the test applied when proposing any new capability.

---

## 2. Module layout

### 2.1 New package: `codex-cam-methodology/src/claw_codex_mcp/`

Sibling to `CAM_CAM/src/claw/mcp_server.py`. **Separate module, separate registry, separate auth token, separate DB connection pool.** No shared state with the 17-tool server beyond the read-only schema.

```
codex-cam-methodology/src/claw_codex_mcp/
├── __init__.py                 # Package marker. Exports `__version__`.
├── __main__.py                 # CLI: `python -m claw_codex_mcp --transport stdio`
├── server.py                   # MCP server entry, registers exactly 4 tools; raises on 5th.
├── schemas.py                  # pydantic v2 input/output models for all 4 tools.
├── db.py                       # Read-only connection helpers + append-only outcome-log writer.
├── decisions_index.py          # On-disk SQLite FTS5 index for cross-repo DECISIONS.md files.
└── tools/
    ├── __init__.py
    ├── recall.py               # cam_recall handler
    ├── provenance.py           # cam_provenance handler
    ├── decisions_search.py     # cam_decisions_search handler
    └── record_outcome.py       # cam_record_outcome handler (only write path)
```

### 2.2 `pyproject.toml` (this repo, not CAM_CAM)

This repo owns its own `pyproject.toml` (to be created in the next implementation phase). It declares `claw_codex_mcp` as a standalone package and provides the script entry point. CAM_CAM's own `pyproject.toml` is **not** modified.

```toml
[project]
name = "claw-codex-mcp"
version = "0.1.0"
description = "Thin librarian MCP server bridging OpenAI Codex CLI and the CAM_CAM mined-methodology corpus"
requires-python = ">=3.12"
license = {text = "MIT"}

[project.scripts]
cam-codex-mcp = "claw_codex_mcp.__main__:main"
```

No new top-level dependencies expected — `mcp`, `pydantic>=2`, and `sqlite-vec` are already declared for `claw.mcp_server`. The `decisions_index.py` module uses **stdlib `sqlite3` with FTS5** (already required for `methodology_fts`); no `whoosh` dependency added — see §2.3.

### 2.3 Decision: index backend for cross-repo DECISIONS.md

**Chosen: SQLite FTS5** (not Whoosh). Justification:
1. SQLite + FTS5 is already a transitive dependency of `claw` (see `methodology_fts` virtual table at `CAM_CAM/src/claw/db/schema.sql:150-155`). Adding a separate library increases supply-chain surface for zero benefit.
2. The index is small (one row per DECISIONS.md block across the workspace; expected O(10²–10³) rows). FTS5's `bm25()` ranking is sufficient.
3. Single backup/restore story — the index file is just another SQLite database.
4. Avoids Whoosh's pure-Python performance ceiling on the cold path.

The decisions index lives at a path supplied via `CAM_CODEX_MCP_DECISIONS_INDEX` (default suggestion: `~/.cam_codex_mcp/codex_decisions_index.db`). It is a **separate SQLite file** from `claw.db`, owned entirely by this repo's MCP server; the heavy engine's writers never touch it. Open question (deferred to implementation): whether to default the path to a user-home location or to the new repo's `data/` directory — see PRD Open Questions.

---

## 3. MCP tool specifications

These four tools are the **entire** contract Codex sees. The set is closed; v2 may add `cam_match_failure` once `failure_knowledge` corpus is non-trivial (currently 1 row — see `HANDOFF_LATEST.md` "Verified Facts").

Every methodology returned by any tool must carry the full provenance envelope:

| Field | Type | Source |
|---|---|---|
| `methodology_id` | str | `methodologies.id` |
| `name` | str | derived from `problem_description` (first line, truncated to 80 chars) |
| `source_repo` | str | parsed from `methodologies.tags` (JSON array) — tag prefix `source_repo:` |
| `source_path` | str | parsed from `methodologies.files_affected` (JSON array) first entry |
| `source_commit_sha` | str \| null | parsed from `methodologies.tags` — tag prefix `source_commit:`; null if absent |
| `mined_at` | str (ISO-8601) | `methodologies.created_at` |
| `last_verified_at` | str \| null (ISO-8601) | `methodologies.last_retrieved_at` |
| `fitness_score` | float | computed (see §3.5) |
| `fitness_n` | int | denominator: `success_count + failure_count` (from `methodologies`) |
| `domain_tag` | str | first tag matching `domain:*` in `methodologies.tags`; `"untyped"` otherwise |
| `stale_bool` | bool | true iff `last_verified_at` is null OR `now - last_verified_at > 30 days` |

### 3.1 `cam_recall`

| Aspect | Value |
|---|---|
| **Purpose** | Return top-K methodologies relevant to a natural-language query, ranked by hybrid score (FTS5 + vector similarity if embedding available, else FTS5 only). |
| **Idempotency / side effects** | None. Read-only. |
| **Backing store** | `methodologies`, `methodology_fts`, `methodology_embeddings` (vec0) in `cam.db`. |
| **Latency target** | p95 ≤500ms for k≤10 on the current 107-row corpus. Justification: FTS5 query is sub-ms on this size; embedding similarity over 107 vectors is sub-10ms; the budget is dominated by JSON marshalling and pydantic validation. Measured under §8. |
| **Error modes** | Raises `ToolError("query empty")` on empty/whitespace input; returns `{results: [], degraded: true, reason: "vec0 unavailable"}` on missing sqlite-vec extension; returns `{results: [], degraded: false}` on empty match. Never raises on empty results. |

**Input schema (pydantic v2):**

```python
class CamRecallInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=2048, description="natural-language query")
    k: int = Field(default=5, ge=1, le=20)
    domain_filter: str | None = Field(default=None, max_length=64,
        description="optional domain tag, e.g. 'rate-limit', 'auth', 'migration'")
    min_fitness: float = Field(default=0.0, ge=0.0, le=1.0,
        description="exclude methodologies below this fitness")
    include_embryonic: bool = Field(default=False,
        description="if false, only lifecycle_state='viable' or 'thriving' are returned")
    include_stale: bool = Field(default=True,
        description="if false, exclude methodologies marked stale_bool=true")
```

**Output schema:**

```python
class MethodologyHit(BaseModel):
    methodology_id: str
    name: str
    source_repo: str
    source_path: str
    source_commit_sha: str | None
    mined_at: str
    last_verified_at: str | None
    fitness_score: float
    fitness_n: int
    domain_tag: str
    stale_bool: bool
    rank_score: float = Field(description="hybrid score; not equal to fitness")
    snippet: str = Field(description="<=240 char excerpt from methodology_notes")

class CamRecallOutput(BaseModel):
    results: list[MethodologyHit]
    degraded: bool = False
    reason: str | None = None
    query_echo: str
```

**Backing SQL (illustrative; final form in `tools/recall.py`):**

```sql
-- Step 1: FTS5 candidates
SELECT methodology_id, bm25(methodology_fts) AS fts_score
  FROM methodology_fts
 WHERE methodology_fts MATCH :query
 ORDER BY fts_score
 LIMIT 50;

-- Step 2: vector candidates (only if embedding model loaded)
SELECT methodology_id, distance
  FROM methodology_embeddings
 WHERE embedding MATCH :query_vec
   AND k = 50;

-- Step 3: union, filter by lifecycle/fitness/stale/domain, rerank with
-- rank_score = 0.6 * (1 - normalized_fts) + 0.4 * (1 - distance), tied with fitness_score.
-- Final SELECT joins methodologies for provenance fields.
```

### 3.2 `cam_provenance`

| Aspect | Value |
|---|---|
| **Purpose** | Given a `methodology_id`, return the **full** provenance envelope plus solution code, methodology notes, and links to ancestors/descendants. Used by `cam_recall_and_cite` when the caller has a hit and wants to write the citation line. |
| **Idempotency / side effects** | None. Read-only. |
| **Backing store** | `methodologies`, `methodology_links` in `cam.db`. |
| **Latency target** | p95 ≤200ms. Single-row primary-key fetch plus two small joins. |
| **Error modes** | Returns `404` shape (`{found: false, methodology_id: ...}`) if the ID is unknown. Raises `ToolError("invalid id format")` if `methodology_id` is not a string of length 1–128. |

**Input schema:**

```python
class CamProvenanceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    methodology_id: str = Field(min_length=1, max_length=128)
    include_solution_code: bool = Field(default=True)
    include_links: bool = Field(default=True,
        description="parents and children via methodology_links")
```

**Output schema:**

```python
class MethodologyLink(BaseModel):
    direction: Literal["parent", "child"]
    target_id: str
    link_type: str  # 'co_retrieval', 'derived_from', etc.
    strength: float

class CamProvenanceOutput(BaseModel):
    found: bool
    methodology_id: str
    provenance: MethodologyHit | None = None  # the full envelope from §3
    solution_code: str | None = None
    methodology_notes: str | None = None
    files_affected: list[str] = []
    tags: list[str] = []
    links: list[MethodologyLink] = []
```

**Backing SQL (illustrative):**

```sql
SELECT id, problem_description, solution_code, methodology_notes,
       tags, files_affected, language, lifecycle_state,
       retrieval_count, success_count, failure_count,
       last_retrieved_at, created_at, fitness_vector
  FROM methodologies
 WHERE id = :methodology_id;

SELECT 'parent' AS direction, source_id AS target_id, link_type, strength
  FROM methodology_links WHERE target_id = :methodology_id
UNION ALL
SELECT 'child' AS direction, target_id, link_type, strength
  FROM methodology_links WHERE source_id = :methodology_id;
```

### 3.3 `cam_decisions_search`

| Aspect | Value |
|---|---|
| **Purpose** | Full-text search across `DECISIONS.md` files in trusted workspace repos. Lets Codex find "have we decided this before?" before writing a new decision. |
| **Idempotency / side effects** | None. Read-only against the index DB. The **indexer** runs out-of-band (see §3.3.4). |
| **Backing store** | `codex_decisions_index.db` (FTS5 virtual table `decisions_fts` + metadata table `decisions_docs`). |
| **Latency target** | p95 ≤500ms for the expected corpus size (O(10³) blocks). |
| **Error modes** | Returns `{results: [], degraded: true, reason: "index missing"}` if `codex_decisions_index.db` does not exist. Never raises. |

**Input schema:**

```python
class CamDecisionsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=2048)
    k: int = Field(default=5, ge=1, le=20)
    repo_filter: str | None = Field(default=None, max_length=256,
        description="absolute path prefix to scope the search")
    since_iso: str | None = Field(default=None,
        description="ISO-8601; only decisions on or after this timestamp")
```

**Output schema:**

```python
class DecisionHit(BaseModel):
    repo: str                # absolute path
    file_path: str           # absolute path to DECISIONS.md
    block_anchor: str        # heading text used as anchor
    decided_at: str | None   # ISO-8601 parsed from block frontmatter
    snippet: str             # <=320 chars
    rank_score: float

class CamDecisionsSearchOutput(BaseModel):
    results: list[DecisionHit]
    degraded: bool = False
    reason: str | None = None
    index_built_at: str | None = None  # ISO-8601 from index metadata
```

**Index schema (in `codex_decisions_index.db`):**

```sql
CREATE TABLE decisions_docs (
    doc_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    repo        TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    block_anchor TEXT NOT NULL,
    decided_at  TEXT,
    indexed_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(repo, file_path, block_anchor)
);
CREATE VIRTUAL TABLE decisions_fts USING fts5(
    body, content='decisions_docs', content_rowid='doc_id'
);
CREATE TABLE index_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
```

**Indexer (out of band).** A CLI subcommand `python -m claw_codex_mcp.decisions_index rebuild --roots <path> [<path>...]` walks each root, parses every `DECISIONS.md`, splits on `##`-level headings, writes one row per block, and refreshes the FTS5 index. This is not invoked by the MCP at request time; it is invoked by the user or a launchd/cron job. **The MCP never writes to this index.**

### 3.4 `cam_record_outcome`

| Aspect | Value |
|---|---|
| **Purpose** | Record the outcome of applying one or more recalled methodologies to a real task. **The only write path on the MCP surface.** Closes the fitness loop that has been open since corpus inception (`methodology_bandit_outcomes=0`). |
| **Idempotency / side effects** | Append-only into `codex_outcome_log` (new table, see §5). Idempotent by `run_hash` — a duplicate `run_hash` returns `{recorded: false, reason: "duplicate run_hash"}` and writes nothing. |
| **Backing store** | Mode-aware (see §1.3). **Connected mode:** `claw.db.codex_outcome_log` (so CAM_CAM's bandit can ingest). **Standalone mode:** `${CAM_CODEX_MCP_OUTCOME_DB_PATH:-~/.cam_codex_mcp/codex_outcome_log.db}`. In both modes: **never** writes to `methodology_bandit_outcomes` or `methodology_fitness_log` — those remain the heavy engine's exclusive write domain. |
| **Latency target** | p95 ≤300ms (single insert + 1–N foreign-key checks on `methodology_ids`). |
| **Error modes** | Raises `ToolError("unknown methodology_id: <id>")` if any cited ID is absent from `methodologies`. Raises `ToolError("invalid outcome")` if `outcome` not in the literal set. Returns `{recorded: false, reason: "duplicate run_hash"}` on collision. |

**Input schema:**

```python
class CamRecordOutcomeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    methodology_ids: list[str] = Field(min_length=1, max_length=10)
    task_id: str = Field(min_length=1, max_length=128,
        description="caller-defined; usually the IMPLEMENT.md step id")
    repo: str = Field(min_length=1, max_length=512,
        description="absolute path of the repo where the methodology was applied")
    outcome: Literal["green", "red", "partial", "rejected"]
    evidence: dict[str, Any] = Field(default_factory=dict,
        description="free-form JSON: test names, commit shas, error fragments")
    run_hash: str = Field(min_length=8, max_length=128,
        description="caller-computed sha256 of (methodology_ids|task_id|repo|outcome|evidence) "
                    "to make recording idempotent across re-runs")
    notes: str | None = Field(default=None, max_length=2048)
```

**Output schema:**

```python
class CamRecordOutcomeOutput(BaseModel):
    recorded: bool
    outcome_id: str | None = None     # uuid4 of the inserted row
    duplicate: bool = False
    reason: str | None = None
    ts: str                             # ISO-8601 of the write attempt
```

**Backing SQL:**

```sql
INSERT OR IGNORE INTO codex_outcome_log
    (id, methodology_ids, task_id, repo, outcome, evidence, ts, run_hash, notes)
VALUES
    (:id, :methodology_ids_json, :task_id, :repo, :outcome,
     :evidence_json, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), :run_hash, :notes);
-- changes() == 0 → duplicate run_hash.
```

### 3.5 `fitness_score` derivation

Computed at read time (no precomputation in v1):

```
fitness_n     = success_count + failure_count          -- from methodologies row
fitness_score = (success_count + 1) / (fitness_n + 2)  -- Laplace-smoothed Bernoulli mean
```

Both numerator and denominator are surfaced so the caller sees the *evidence behind the number*. With `fitness_n == 0`, `fitness_score == 0.5` and the caller is expected to treat it as "no signal yet" (UX invariant from the UX sub-agent: never present a smoothed prior as if it were measured).

---

## 4. Skill output contracts

Skills are Codex's markdown-level layer. Each skill below produces deterministic markdown blocks that the next skill in the chain can parse. The MCP is never invoked by the skill *itself*; the skill instructs Codex to invoke specific MCP tools and then asserts on the response shape.

### 4.1 `cam_recall_and_cite` (NEW)

**Frontmatter:**

```markdown
---
name: cam_recall_and_cite
description: Before writing new code, recall relevant methodologies from CAM and write a provenance citation block into IMPLEMENT.md. Fail the gate if cited patterns do not appear in code AND no rejection entry exists in DECISIONS.md.
auto_fire:
  triggers:
    - verb_in_user_message: ["implement", "add", "build", "wire", "scaffold", "introduce"]
    - file_about_to_be_created: ["*.ts", "*.tsx", "*.py", "*.go", "*.rs"]
    - implement_md_step_status_transition: "todo -> in_progress"
  not_when:
    - skill_active: ["repo_recon"]
    - file_about_to_be_created: ["*.md"]
---
```

**MCP calls made by this skill:**

| When | Call | Why |
|---|---|---|
| Before code is written for an IMPLEMENT.md step | `cam_recall(query=<step description>, k=5, include_embryonic=false)` | Find candidate patterns |
| For each hit the caller decides to use | `cam_provenance(methodology_id=<id>)` | Pull full envelope + solution_code for the citation block |

**Required output (appended to `IMPLEMENT.md` under the active step):**

````markdown
## Retrieved Methodologies (step: <step_id>)

| pattern_id | name | fitness | source | status |
|---|---|---|---|---|
| `<id>` | <name> | 0.87 (8 green / 0 red) | <repo>/<path> | viable |
| `<id>` | <name> | 0.50 (0 green / 0 red) | <repo>/<path> | embryonic STALE |

### One-line provenance citations

- `<id>` - <name> - fitness 0.87 (8 green / 0 red) - source: ABXorcist/lib/rate-limit.ts
- `<id>` - <name> - fitness 0.50 (0 green / 0 red) - source: HBRKR/utils/auth.py [STALE last_verified > 30d]

### Application plan

For each cited pattern:
- **APPLY** `<id>`: <one-sentence summary of how it informs this step>
- **REJECT** `<id>`: <one-sentence reason; must also be mirrored in DECISIONS.md>
````

**Self-check rule (skill must enforce before exiting):**

1. After Codex writes the implementation, the skill diffs the new code against each pattern marked **APPLY**.
2. If a cited pattern's distinctive tokens (function names, decorators, configuration keys — extracted from `solution_code` via simple lexical heuristics) appear in the diff → pass.
3. If no cited APPLY pattern is detectable in the diff **and** there is no `DECISIONS.md` entry with shape `## Rejected pattern: <id>\n<reason>` → the skill fails its own gate, writes a `BLOCKER.md` entry, and refuses to mark the step done.

This is the structural mechanism that prevents Codex from "shopping" for patterns and then ignoring them — the cost of citing is the obligation to either use or formally reject.

### 4.2 `rescue_ladder` (NEW)

**Frontmatter:**

```markdown
---
name: rescue_ladder
description: When a verification step fails twice consecutively, attempt a 3-rung rescue ladder before asking the user. Rung 1 cite alternate pattern; rung 2 binary-search the failing diff; rung 3 escalate to user with a structured BLOCKER.
auto_fire:
  triggers:
    - verification_command_consecutive_failures: ">= 2"
  not_when:
    - blocker_md_open_count: ">= 1"
---
```

**MCP calls made by this skill:**

| Rung | Call | Why |
|---|---|---|
| 1 | `cam_recall(query=<error fragment + step description>, k=3, min_fitness=0.6)` | Find a higher-fitness alternative pattern |
| 1 | `cam_decisions_search(query=<error class>, k=3)` | Check if this failure was already decided on elsewhere |
| 3 (escalate) | none | The user is the next layer; do not invoke MCP |

**Required output (appended to `PROGRESS.md`):**

````markdown
## Rescue Ladder — step `<step_id>` — attempt <n>

### Rung 1: alternate pattern
- Searched: `<query>`
- Considered: `<id_1>`, `<id_2>`, `<id_3>`
- Selected / Rejected: <decision + one-sentence reason>

### Rung 2: bisect
- Diff hunks tried: <n>
- Smallest failing hunk: <path:line-line>

### Rung 3: escalate
- BLOCKER.md updated: <yes/no>
- User question: <one sentence>
````

**Self-check rule:** if all three rungs run and the verification still fails, the skill **must** write a `BLOCKER.md` entry and **must not** loop again on the same step within the same Codex session. Repeated failure beyond the ladder is a stop condition under `.codex/AGENTS.md:35` ("repeated failure after mitigation attempts").

### 4.3 `outcome_log` (NEW — centerpiece; closes the loop)

This is the smallest skill and the most important one. Without it the fitness loop stays open and the corpus never matures.

**Frontmatter:**

```markdown
---
name: outcome_log
description: After any verified step that used a recalled methodology, record the outcome via cam_record_outcome. Fails the step if the recalled patterns appear in IMPLEMENT.md but no outcome row was written.
auto_fire:
  triggers:
    - implement_md_step_status_transition: "in_progress -> done"
    - implement_md_step_status_transition: "in_progress -> failed"
  not_when:
    - implement_md_step_has_retrieved_methodologies_block: false
---
```

**MCP calls made by this skill:**

| When | Call | Why |
|---|---|---|
| On step transition | `cam_record_outcome(methodology_ids=[...], task_id=<step_id>, repo=<abs path>, outcome=<green\|red\|partial\|rejected>, evidence={...}, run_hash=<sha256>, notes=<one line>)` | Record the result |

**Required output (appended to `PROGRESS.md`):**

````markdown
## Outcome — step `<step_id>` — `<green|red|partial|rejected>`

- Cited methodologies: `<id_1>`, `<id_2>`
- Outcome row: `<outcome_id>`
- run_hash: `<sha256-hex-16-chars>`
- Evidence: <test names / commit sha / error fragment summary>
````

**Self-check rule:**
1. The skill reads the active step's `## Retrieved Methodologies` block from `IMPLEMENT.md` (written by `cam_recall_and_cite`).
2. It computes `run_hash = sha256(json.dumps(sorted(methodology_ids) + [task_id, repo, outcome, evidence_canonical], sort_keys=True))`.
3. It calls `cam_record_outcome`. If the response is `{recorded: false, duplicate: true}` the skill accepts that as success (idempotent re-run).
4. **Gate:** if the IMPLEMENT.md step had a `## Retrieved Methodologies` block and `cam_record_outcome` did not return `recorded=true OR duplicate=true`, the skill fails and refuses to mark the step done.

### 4.4 `repo_recon` (MODIFY existing)

Existing file: `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/repo_recon/SKILL.md` (verified present; opens with `name: repo_recon`, line 2). **One additive change only**: insert a step that calls `cam_decisions_search` once with the repo path as `repo_filter`, and append its results to `REPO_MAP.md` under a new heading.

**Added section (to be inserted after the existing "Inspect" section, before "REPO_MAP.md Format" at line 40 of the current file):**

````markdown
## Recall prior decisions

Call `cam_decisions_search(query="<dominant tech stack> <dominant domain>", repo_filter="<absolute repo path>", k=5)`.

Append to `REPO_MAP.md`:

```markdown
## Prior Decisions (from cam_decisions_search)

| file | anchor | decided_at | snippet |
|---|---|---|---|
```

If the index reports `degraded: true, reason: "index missing"`, append a one-line note: `> Decisions index unavailable; run python -m claw_codex_mcp.decisions_index rebuild --roots <workspace>.` Do not block on this.
````

**No removals.** All existing repo_recon outputs (`REPO_MAP.md`, `RISK_NOTES.md`, etc.) remain.

### 4.5 `deepscientist-data-research` (REWRITE)

Existing file: `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/deepscientist-data-research/SKILL.md` (229 lines). Verified phantom MCP references at lines **65, 135, 162** (`claw_query_memory`, `claw_store_finding`). Per locked user decision in `HANDOFF_LATEST.md` ("phantom_skill_strategy: rewrite_deepscientist_data_research"), this is a **clean rewrite** — no back-compat shim, no aliasing layer.

**Replacements (line-keyed to the existing file):**

| Existing call | Replace with |
|---|---|
| line 65: `claw_query_memory("surrogate feature for <ideal_feature> from <available_signals>")` | `cam_recall(query="surrogate feature for <ideal_feature> from <available_signals>", k=5, domain_filter="data-research")` |
| line 135: `claw_store_finding(problem_description="...", solution_code="...", tags=[...])` | `cam_record_outcome(methodology_ids=[<ids cited during the step>], task_id=<step_id>, repo=<abs path>, outcome="green", evidence={"finding": "<summary>", "tags": [...]}, run_hash=<sha256>, notes="<one line>")` |
| line 162: same `claw_store_finding` pattern with success tag | same `cam_record_outcome` as above, with `outcome="green"` |

**New invariant in the rewritten skill:** every `cam_recall` call must be followed by either an APPLY/REJECT block in `IMPLEMENT.md` (per §4.1) **or** an immediate `cam_record_outcome` with `outcome="rejected"` and a reason in `notes`. No "silent shopping" allowed.

---

## 5. DB schema additions (additive only)

**Constraint:** never modify existing tables. The four read tools query only existing tables (`methodologies`, `methodology_fts`, `methodology_embeddings`, `methodology_links`, `methodology_usage_log`). The one write tool inserts into a new table tagged for Codex so the heavy-engine bandit writers (`methodology_bandit_outcomes`, `methodology_fitness_log`) are untouched.

### 5.1 New table: `codex_outcome_log`

```sql
-- =========================================================================
-- 30. CODEX_OUTCOME_LOG (Codex-session outcomes; isolated from heavy-engine writers)
-- Owned exclusively by claw_codex_mcp.tools.record_outcome.
-- Append-only. Never updated. Never deleted by application code.
-- =========================================================================
CREATE TABLE IF NOT EXISTS codex_outcome_log (
    id                TEXT PRIMARY KEY,                       -- uuid4
    methodology_ids   TEXT NOT NULL,                          -- JSON array of methodology.id strings
    task_id           TEXT NOT NULL,                          -- caller-defined step id
    repo              TEXT NOT NULL,                          -- absolute path
    outcome           TEXT NOT NULL
        CHECK (outcome IN ('green','red','partial','rejected')),
    evidence          TEXT NOT NULL DEFAULT '{}',              -- JSON
    ts                TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    run_hash          TEXT NOT NULL,                           -- idempotency key
    notes             TEXT,
    UNIQUE(run_hash)
);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_ts ON codex_outcome_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_repo ON codex_outcome_log(repo);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_outcome ON codex_outcome_log(outcome);
```

**Idempotency contract.** The `UNIQUE(run_hash)` constraint plus `INSERT OR IGNORE` makes `cam_record_outcome` safe to re-run with identical input. The bandit cannot be gamed by hitting the tool twice with the same arguments, and Codex skills can safely retry on transient errors without double-counting.

**Migration path.** The new CREATE statements live in **this repo only** at `migrations/001_codex_outcome_log.sql`. They are **not** added to `CAM_CAM/src/claw/db/schema.sql` — CAM_CAM stays untouched. The mode determines which DB receives the schema:
- **Connected mode:** `claw_codex_mcp.db.ensure_schema()` reads the migration file and applies `CREATE TABLE IF NOT EXISTS` against the live `claw.db`. Non-destructive; idempotent.
- **Standalone mode:** `ensure_schema()` creates the file at `${CAM_CODEX_MCP_OUTCOME_DB_PATH:-~/.cam_codex_mcp/codex_outcome_log.db}` if it does not exist, then applies the migration. The directory is created with `mode=0700` (user-only) since it will accumulate outcome data tied to the user's sessions.

A `cam-codex-mcp migrate-outcomes --from <local.db> --to <claw.db>` CLI subcommand is provided (additive, idempotent on `run_hash`) for users who later switch from standalone to connected mode and want to backfill CAM_CAM's bandit with their accumulated local outcomes. The subcommand is **not** an MCP tool — it does not count against the 4-tool ceiling.

### 5.2 Read paths (no schema change required)

Confirmed against `CAM_CAM/src/claw/db/schema.sql`:

| Need | Existing source |
|---|---|
| FTS5 over methodology text | `methodology_fts` (line 150) |
| Vector similarity | `methodology_embeddings` (line 144, float[384]) |
| Provenance fields | `methodologies` (line 104) — `tags`, `files_affected`, `created_at`, `last_retrieved_at`, `success_count`, `failure_count` |
| Co-retrieval / lineage | `methodology_links` (line 181) |
| Usage history (read-only audit) | `methodology_usage_log` (line 85) — read only; we do **not** write here |

---

## 6. `.codex/config.toml` change

Append exactly this block. The new server is sibling to the existing `[mcp_servers.context7]` (currently at line 276 of `.codex/config.toml`). No other lines change.

All env vars are **optional**. The MCP detects connected vs standalone mode at startup based on whether `CAM_CODEX_MCP_DB_PATH` is set and resolves to a valid `claw.db` (see §1.3).

### Connected-mode example (CAM_CAM installed locally)
```toml
[mcp_servers.cam_cam]
command = "python"
args = ["-m", "claw_codex_mcp", "--transport", "stdio"]
env = { CAM_CODEX_MCP_DB_PATH = "/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db", CAM_CODEX_MCP_AUTH_TOKEN = "${CAM_CODEX_MCP_AUTH_TOKEN}", CAM_CODEX_MCP_DECISIONS_INDEX = "${HOME}/.cam_codex_mcp/codex_decisions_index.db" }
```

### Standalone-mode example (no CAM_CAM)
```toml
[mcp_servers.cam_cam]
command = "python"
args = ["-m", "claw_codex_mcp", "--transport", "stdio"]
env = { CAM_CODEX_MCP_AUTH_TOKEN = "${CAM_CODEX_MCP_AUTH_TOKEN}" }
# CAM_CODEX_MCP_DB_PATH omitted → standalone mode
# CAM_CODEX_MCP_OUTCOME_DB_PATH and CAM_CODEX_MCP_DECISIONS_INDEX default to ~/.cam_codex_mcp/
```

Notes:
- The `python` interpreter must be the one with `claw_codex_mcp` (this repo's package) installed. Either set up a `.venv` and use its absolute path, or rely on `PATH` resolution. **This repo's package has zero runtime dependency on the `claw` package** — it speaks raw SQL to `claw.db` when present.
- `CAM_CODEX_MCP_AUTH_TOKEN` is **separate** from any CAM_CAM token. They must not share a value.
- This change does **not** modify `.codex/rules/default.rules`, which currently contains plaintext API keys (see `meta/HANDOFF_LATEST.md` "Secret exposure"). That file is out of scope for this methodology and must not be touched until the secrets there are rotated.

---

## 7. `.codex/AGENTS.md` doctrine additions

Append the following section to `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md` (currently 78 lines, ends at line 78 with the existing Core Rule). The new section sits after the existing "Core Rule" block and replaces it as the final word.

```markdown
## CAM Librarian Doctrine

CAM_CAM is consulted as a librarian via MCP, never run inline.

- No mined methodology may be applied without its provenance row written to `IMPLEMENT.md` under a `## Retrieved Methodologies` block.
- On the second consecutive verification failure, the `rescue_ladder` skill runs before the user is asked.
- After any verified step that used a recalled methodology, `outcome_log` must record the result via `cam_record_outcome`. A step is not "done" until the outcome row exists or is recorded as `duplicate`.
- The MCP surface is closed at four tools: `cam_recall`, `cam_provenance`, `cam_decisions_search`, `cam_record_outcome`. Do not call any other `cam_*` or `claw_*` tool name — those references are stale (see HANDOFF_LATEST.md "Phantom MCP references").

### Rejection rules (when to ignore a recall hit)

A recalled methodology must be rejected (with the reason captured in `DECISIONS.md` under `## Rejected pattern: <id>`) when any of these hold:

- `fitness_n == 0` and the task is destructive or production-bound — no evidence, no application.
- `stale_bool == true` and the source repo has had a major version bump since `last_verified_at`.
- The methodology's `language` differs from the active step's language and the pattern is language-specific (not an architectural invariant).
- A more recent `cam_decisions_search` hit explicitly overrides this pattern in the current repo's `DECISIONS.md`.

### Boundary test (apply before adding any new tool or skill)

> Stateful + cross-repo + computational → MCP tool.
> Doctrine + workflow + output schema → Skill (markdown).
> Anything that fits in markdown → Markdown.

### Updated Core Rule

Codex decides. Tests arbitrate. Markdown remembers. CAM librarian cites.
```

---

## 8. Non-functional requirements

### 8.1 Latency

| Tool | p95 target | Method |
|---|---|---|
| `cam_recall` (k≤10) | ≤500 ms | `/usr/bin/time -l` against `cam.db` with the live 107-row corpus, 100 sequential calls, drop top/bottom 5%, report 95th |
| `cam_provenance` | ≤200 ms | Same harness, single-id lookups across all 107 ids |
| `cam_decisions_search` (k≤10) | ≤500 ms | Same harness against `codex_decisions_index.db` once seeded |
| `cam_record_outcome` | ≤300 ms | Same harness; idempotent re-runs measured separately and must be ≤150 ms |

Measurements must be taken against the **real** SQLite files at `CAM_CAM/data/`. No synthetic data permitted (per workspace no-mock policy).

### 8.2 Memory

Peak resident set size (RSS) of the new server, measured under the §10.2 integration harness, must be **≤25% of the existing 17-tool server's peak RSS** on the same workload. Both measurements taken on the same machine, same `cam.db`, with `ru_maxrss` from `/usr/bin/time -l`. The baseline of `claw.mcp_server` must be captured **before** any work on `claw_codex_mcp` begins.

### 8.3 Concurrency

`cam.db` is already opened in WAL mode (`PRAGMA journal_mode=WAL` is set at `CAM_CAM/src/claw/db/engine.py:152`). The new server must:

- Open one **dedicated** connection pool — do not share connections with `claw.mcp_server`.
- Open all read connections with `PRAGMA query_only=ON` (precedent: `CAM_CAM/src/claw/db/engine.py:125`).
- Hold `PRAGMA busy_timeout=5000` (precedent: `engine.py:156`).
- The single write path (`cam_record_outcome`) must serialize through a per-process `asyncio.Lock`, **not** a database lock, so that read tools are never blocked by a write.

### 8.4 Coverage

| Module | Line coverage target | Action plan if below target |
|---|---|---|
| `claw_codex_mcp` package (whole) | ≥90% | Identify uncovered lines; add a fixture-driven test for each; if a line is genuinely unreachable, mark with `# pragma: no cover` accompanied by a one-line `# why:` comment cited in the test plan |
| `claw_codex_mcp.db` write paths (`record_outcome` insert + duplicate handling + schema bootstrap) | **100%** | Mandatory. Any gap is a release blocker. The write surface is small enough that 100% is achievable; gaps indicate untested error paths. |
| `claw_codex_mcp.tools.recall` reranking logic | ≥95% | Hybrid scoring branches (vec available / vec unavailable / both empty) must each have a test. |

Coverage measured with `coverage.py` running the test suite from §10.

### 8.5 Security

- **Bearer-token auth** required for every tool call. Token read from `CAM_CODEX_MCP_AUTH_TOKEN`. Empty or unset → server refuses to start (fail-closed).
- **Auth token must be separate** from `CLAW_MCP_AUTH_TOKEN`. The two servers' tokens are rotated independently. A leaked Codex token must not grant access to the 17-tool server.
- **No logging of tool arguments** beyond a truncated summary (precedent: `_truncate_args` at `CAM_CAM/src/claw/mcp_server.py:1666-1682`). Embeddings, query text, and outcome evidence may contain sensitive data.
- **Read-only DB connections** for the three read tools.
- **`.codex/rules/default.rules` constraint:** that file currently leaks `OPENROUTER_API_KEY` and `GOOGLE_API_KEY` in plaintext (per HANDOFF_LATEST.md "Secret exposure"). The new methodology **must not** require any change to that file. This decouples the methodology rollout from the (separate, pending) secrets-rotation work.

---

## 9. Backwards-compatibility & deprecations

### 9.1 The existing 17-tool MCP stays

`CAM_CAM/src/claw/mcp_server.py` (1,782 lines, registers 17 tools at lines 1689–1779) is **not modified by v1**. With the standalone redesign, this repo is decoupled from CAM_CAM's internal structure — it speaks raw SQL to `claw.db` when present, never imports from the `claw` package. CAM_CAM's legacy MCP server (which was never wired to Codex) is therefore neither used by this design nor affected by it. Whether to clean up that dead code is a CAM_CAM-internal decision, tracked as an out-of-scope cleanup item per `PRD.md` §11.

The two servers are deliberately allowed to coexist:
- **`claw.mcp_server`** — full-surface, for IDE assistants that expect the whole `claw_*` namespace.
- **`claw_codex_mcp`** — thin, for Codex CLI. 4 tools. Hard ceiling.

### 9.2 `deepscientist-data-research` SKILL.md rewrite

Per locked user decision, **no back-compat shim** is provided. The references at lines 65, 135, 162 of `.codex/skills/deepscientist-data-research/SKILL.md` are replaced with `cam_recall` / `cam_record_outcome` calls using the new schemas (see §4.5). The old call names (`claw_query_memory`, `claw_store_finding`) **do not exist** on the new MCP surface — calls to them must fail loudly with "unknown tool" rather than silently degrade.

### 9.3 Stale documentation flagged but not edited

The following documents have stale claims; they are **out of scope** for this spec (do not edit them as part of this build, but track them):

- `CAM_CAM/README.md` claims "889 methodologies" (live DB has 107).
- `CAM_CAM/docs/MCP_INTEGRATION_GUIDE.md` documents 5 tools (`claw.mcp_server` has 17).
- `CAM_CAM/scripts/install_codex_subagents.sh` expects a missing `awesome-codex-subagents/` sibling.
- `.codex/skills/codex-primary-runtime/SKILL.md` is empty.

---

## 10. Testing strategy

### 10.1 Unit tests

- **Scope:** every handler in `claw_codex_mcp.tools.*`, every helper in `db.py`, every model in `schemas.py`.
- **Fixture DB:** a **real, copied** slice of `cam.db` — 10–20 real rows sampled from the live corpus, copied to `tests/fixtures/claw_slice.db` inside this repo once and committed via Git LFS (or as a binary tracked artifact; size will be ≪ 1 MB). **Never mocked.** This satisfies the no-mock policy: the file format and SQL paths are real, only the data volume is reduced.
- **Per-tool tests** must cover: happy path, empty results, every error branch, and one boundary condition per pydantic constraint (min_length, max_length, ge, le, literal set).
- **Idempotency test** for `cam_record_outcome`: insert, re-insert with identical `run_hash`, assert `recorded=false, duplicate=true`, assert table row count unchanged.

### 10.2 Integration tests

- **Real MCP stdio protocol.** Start `python -m claw_codex_mcp --transport stdio` as a subprocess. Send a real `initialize` request, real `tools/list` request (assert exactly 4 tools), real `tools/call` requests for each of the 4 tools, assert the responses validate against the pydantic output models.
- **Real Codex CLI client (connected mode).** A second integration harness uses the actual `codex` binary with the connected-mode `[mcp_servers.cam_cam]` block from §6 wired to the test fixture DB. Exercises tool discovery end-to-end. No mocked client.
- **Real Codex CLI client (standalone mode).** A third harness boots the server with `CAM_CODEX_MCP_DB_PATH` unset. Asserts: server starts cleanly, `tools/list` returns exactly 4 tools, `cam_recall` returns `{results: [], corpus_status: "absent"}` (no fabrication, no raise), `cam_decisions_search` and `cam_record_outcome` are fully functional. Startup log contains `mode=standalone`.
- **Mode transition test.** Boot in standalone, write outcomes, kill server. Re-boot in connected (point at a real `claw.db`), call `cam-codex-mcp migrate-outcomes --from <local.db> --to <claw.db>`, assert rows are migrated idempotently (re-running the command produces zero new rows).
- **Conformance test for the 4-tool ceiling.** Boot the server; call `tools/list`; assert `len(tools) == 4` and the set is exactly `{cam_recall, cam_provenance, cam_decisions_search, cam_record_outcome}`. CI fails on any drift. Runs in both modes.

### 10.3 End-to-end test

A single Codex session against a **real unfamiliar repo** (selected from the workspace trusted-projects list at `.codex/config.toml:9-275`; suggested first target: `/Volumes/WS4TB/HBRKR` — a real Next.js codebase, trusted, not previously touched in this session). The session exercises:

1. `repo_recon` skill including the new `cam_decisions_search` step.
2. `cam_recall_and_cite` fires on an "implement" prompt; `## Retrieved Methodologies` block lands in `IMPLEMENT.md`.
3. Code is written; the self-check rule from §4.1 passes (or fails honestly).
4. `outcome_log` fires on step transition; `cam_record_outcome` writes a row to `codex_outcome_log`.
5. `run_hash` from step 4 is verifiable: re-running the skill returns `duplicate=true`.

E2E assertions are made against the **real `cam.db`** (cleaning the test's outcome rows afterward by filtering on a test-specific `task_id` prefix). No mocked LLM calls.

### 10.4 Skill tests

Skills are parsed by Codex from markdown. Skill tests load each `SKILL.md`, parse the frontmatter (must be valid YAML), and assert the documented MCP calls and required outputs are textually present. **Real markdown parsing**, no mocks.

### 10.5 The "5th tool" CI test (hard ceiling enforcement)

```python
def test_mcp_surface_is_exactly_four_tools():
    """Hard ceiling. Adding a 5th tool requires a spec amendment and a new test bump."""
    from claw_codex_mcp.server import REGISTERED_TOOLS
    expected = {"cam_recall", "cam_provenance", "cam_decisions_search", "cam_record_outcome"}
    actual = {t.name for t in REGISTERED_TOOLS}
    assert actual == expected, (
        f"MCP surface drift: missing={expected - actual}, extra={actual - expected}. "
        f"Adding a tool requires updating build_specs.md §3 first."
    )
```

This test must be present from the first commit of the new package and must never be quarantined.

### 10.6 Coverage and gap action plan

Per workspace policy: any coverage figure below 100% requires an action plan. Initial action plan:

- If `claw_codex_mcp` total line coverage lands at <90%: enumerate uncovered lines, classify each as (a) untested error branch — add a test, or (b) genuinely unreachable — mark `# pragma: no cover` with a one-line justification.
- If `db.py` write paths land at <100%: stop. Do not advance to release until they reach 100%. This is the only write surface; coverage gaps here are unacceptable.
- If integration test passes locally but fails in CI: capture the error log, add a validation log line per the workspace error-handling rule (5–7 possible sources → narrow to 1–2 → log → fix), then retry.

---

## 11. Out of scope (v1)

These are deferred. Each requires its own spec before any code is written.

- **`cam_match_failure` tool.** Justification: `failure_knowledge` has 1 row (verified in HANDOFF_LATEST.md "Verified Facts"). The corpus is too thin for a useful tool. Revisit when `failure_knowledge` reaches a non-trivial size (threshold to be set in v2 spec, not here).
- **HTTP / SSE transport.** stdio only in v1. The existing 17-tool server's HTTP path is itself unimplemented (referenced in HANDOFF_LATEST.md "Known Issues" → `_monolith.py:13794`); v1 mirrors that limitation rather than fixing it elsewhere.
- **Federation / cross-instance MCP bridges.** No multi-host coordination in v1.
- **Dashboards or live monitoring UI.** The heavy engine has its own dashboard module (`CAM_CAM/src/claw/dashboard.py`); the thin server does not add one.
- **Telemetry beyond local file logs.** Logs go to stderr (precedent: `CAM_CAM/src/claw/mcp_server.py:1708`). No metrics export, no remote sinks, no Sentry-style aggregation in v1.
- **Modifying `.codex/rules/default.rules`.** That file has plaintext secrets and is owned by a separate remediation track.
- **Auto-rebuilding `codex_decisions_index.db`.** v1 ships the indexer as a manual CLI subcommand. Scheduled rebuilds (cron, launchd) are v2.
- **Migrating existing skills beyond `repo_recon` and `deepscientist-data-research`.** Other skills may eventually benefit from `cam_recall`, but each migration requires its own decision in DECISIONS.md.

---

## 12. Validation gate ordering (between every step)

Per workspace rule, each step must be validated before the next begins. The build order and the gate that must close before advancing:

1. **Baseline RSS of `claw.mcp_server`** under §10.2 harness → captured as a number, written to `docs/codex-cam-methodology/baselines.md`. Gate: file exists with a measured value.
2. **`codex_outcome_log` schema migration applied to a copy of `cam.db`**. Gate: `sqlite3 <copy> ".schema codex_outcome_log"` shows the expected DDL; no existing-table DDL is altered.
3. **`claw_codex_mcp.db` module** with read connections + write lock. Gate: 100% coverage on this module before moving on.
4. **`schemas.py` pydantic models for all 4 tools.** Gate: every model has at least one valid and one invalid example test.
5. **Tool handlers in dependency order:** `cam_recall` → `cam_provenance` → `cam_record_outcome` → `cam_decisions_search` (the last is independent because the index is a separate DB). Gate per handler: unit tests green; the 5th-tool CI test (§10.5) still green.
6. **`server.py` registration + `__main__.py` CLI.** Gate: §10.2 integration harness green; stdio conformance passes.
7. **`.codex/config.toml` block appended.** Gate: a real `codex` process discovers exactly 4 tools.
8. **`.codex/AGENTS.md` doctrine section appended.** Gate: file diff matches §7 verbatim; no other edits.
9. **`.codex/skills/repo_recon/SKILL.md` modified.** Gate: skill test from §10.4 passes; existing outputs still produced.
10. **New skills written:** `cam_recall_and_cite`, `rescue_ladder`, `outcome_log`. Gate: skill tests green for each.
11. **`deepscientist-data-research` rewrite.** Gate: no surviving `claw_query_memory` / `claw_store_finding` references; skill tests green.
12. **End-to-end test against a real unfamiliar repo** (§10.3). Gate: outcome row present in `codex_outcome_log` with a verifiable `run_hash`.
13. **Coverage report.** Gate: ≥90% overall, 100% on `db.py` write paths; otherwise produce the §10.6 action plan and do not declare the work releasable.

No step may be marked complete in `PROGRESS.md` until its gate has closed. No claim of "production ready" applies until all 13 gates are closed and the end-to-end test has run against a second unfamiliar repo (independent confirmation; not selected before the first run finishes).

---

## 13. References (file:line citations used)

- `/Volumes/WS4TB/WS4TBr/CAM_Codx/HANDOFF_LATEST.md` — session context, verified facts, locked decisions (whole file)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/schema.sql:104-136` — `methodologies` table definition
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/schema.sql:144-147` — `methodology_embeddings` vec0 virtual table
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/schema.sql:150-155` — `methodology_fts` FTS5 virtual table
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/schema.sql:181-192` — `methodology_links` (parents/children)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/schema.sql:384-393` — `methodology_fitness_log` (read-only here)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/schema.sql:568-576` — `methodology_bandit_outcomes` (read-only here)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/schema.sql:969-991` — `failure_knowledge` (1 row; cam_match_failure deferred)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/engine.py:125` — `PRAGMA query_only=ON` precedent for read connections
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/db/engine.py:152-156` — WAL + foreign_keys + busy_timeout precedent
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/mcp_server.py:1626-1657` — `claw.mcp_server` registration pattern (reference; not modified)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/mcp_server.py:1666-1682` — `_truncate_args` log-redaction precedent
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/src/claw/mcp_server.py:1689-1779` — stdio entry-point precedent (referenced for `__main__.py` shape)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md:5-14` — required-files reading order (skills must produce these files)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md:35` — "repeated failure after mitigation attempts" stop condition (used by `rescue_ladder`)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md:77` — existing Core Rule (the new doctrine appends one clause)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml:1-3` — Codex model + reasoning effort (informs the assumption that Codex can correctly interpret the structured outputs)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml:276-278` — existing `[mcp_servers.context7]` (sibling for the new block)
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/repo_recon/SKILL.md:2-40` — skill to be modified; line 40 is the insertion point for the new "Recall prior decisions" section
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/deepscientist-data-research/SKILL.md:65,135,162` — phantom MCP references to be rewritten
