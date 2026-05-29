# Action Plans & Showpiece Build Plans — 2026-05-29

---

## PART 1: Test Failure Action Plans

---

### AP-1: test_novelty — `test_with_similar_neighbors`

**File:** `tests/test_novelty.py:TestNearestNeighborNovelty::test_with_similar_neighbors`
**Status:** Pre-existing failure. Not introduced by recent changes.

#### Root Cause

The test creates 5 "similar" methodologies using `embedding_engine.encode()` where
`embedding_engine = EmbeddingEngine(config.embeddings)`. Because `config.embeddings` loads
`claw.toml` which sets `model = "hash-embedding-384"`, the encoder produces deterministic
hash vectors with no semantic relationship. All 5 "similar" texts produce hash vectors that
are essentially random in semantic space. The nearest-neighbor cosine similarity returns ~0
for all pairs, and the novelty scorer interprets near-zero similarity as "no close neighbors"
→ returns `novelty = 1.0`. The test expects `< 0.5`.

This is the same root cause as the verifier drift bug fixed in commit e10e298, manifesting
in the test layer instead of production code.

#### Fix

**Option A (preferred — real embeddings, no mock):** Create the test's `EmbeddingEngine`
with a real `EmbeddingsConfig()` (default `all-MiniLM-L6-v2`) rather than reading from
`config.embeddings`. The novelty scorer itself doesn't hardcode the model — only the test
fixture does.

```python
# tests/test_novelty.py — change in test_with_similar_neighbors
from claw.core.config import EmbeddingsConfig as _EmbeddingsConfig
embedding_engine = EmbeddingEngine(_EmbeddingsConfig())   # real semantic model
# (remove the line: embedding_engine = EmbeddingEngine(config.embeddings))
```

This mirrors the fix already applied in `factory.py` for the verifier.

**Option B (alternative):** Patch `config.embeddings.model` in the test fixture to
`"all-MiniLM-L6-v2"` before constructing the engine.

**Steps:**
1. Edit `tests/test_novelty.py` line ~340: replace `EmbeddingEngine(config.embeddings)` with
   `EmbeddingEngine(_EmbeddingsConfig())`.
2. Add import `from claw.core.config import EmbeddingsConfig as _EmbeddingsConfig` at top of
   the test class or at module level.
3. Run `pytest tests/test_novelty.py::TestNearestNeighborNovelty::test_with_similar_neighbors -v`
   — expect PASS (similar texts will have cosine similarity ~0.8–0.95, novelty will return < 0.5).
4. Run full `pytest tests/test_novelty.py -v` to confirm no regressions in sibling tests.

**Validation:** `assert result < 0.5` with real embeddings for semantically similar texts
(all "web scraping with BeautifulSoup" variants) should reliably score 0.05–0.25.

---

### AP-2: test_serial_evolution — `test_openrouter_agents_and_fallbacks_use_only_approved_models`

**File:** `tests/test_serial_evolution.py:TestApprovedModelConfig::test_openrouter_agents_and_fallbacks_use_only_approved_models[config_path0]`
**Config tested:** `claw.toml`
**Status:** Pre-existing failure introduced when `qwen/qwen3.5-9b` and `openai/gpt-4o-mini`
were added to `[llm] fallback_models` in a prior session.

#### Root Cause

`APPROVED_MODEL_IDS` in `src/claw/evolution/serial.py` contains 4 models:
```
qwen/qwen3.6-flash, deepseek/deepseek-v4-flash, deepseek/deepseek-v4-pro, openai/gpt-mini-latest
```

`claw.toml [llm] fallback_models` contains 5 models including 2 not in the approved list:
- `qwen/qwen3.5-9b` — not approved
- `openai/gpt-4o-mini` — not approved (approved list has `openai/gpt-mini-latest` instead)

The test asserts `set(fallback_models) <= set(APPROVED_MODEL_IDS)` — a strict subset check.

#### Fix

Two choices — pick one based on intent:

**Option A — Add the two models to `APPROVED_MODEL_IDS`** (if they are genuinely intended
as approved fallbacks):

```python
# src/claw/evolution/serial.py
APPROVED_MODEL_IDS = (
    "qwen/qwen3.6-flash",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-pro",
    "openai/gpt-mini-latest",
    "qwen/qwen3.5-9b",        # add
    "openai/gpt-4o-mini",     # add
)
```

**Option B — Remove the two non-approved models from `claw.toml`** (if the intent is that
only serial-evolution-approved models may appear in the fallback chain):

```toml
# claw.toml [llm]
fallback_models = [
    "qwen/qwen3.6-flash",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4-pro",
]
```

**User decision required:** The user must confirm which models are approved. Per global rules,
the user selects all LLM model versions. **Do not implement either option without explicit
user approval on which model list is correct.**

**Steps after user approves:**
1. Make the approved edit (serial.py or claw.toml).
2. Run `pytest tests/test_serial_evolution.py::TestApprovedModelConfig -v` — expect all 4
   parametrized configs to pass.
3. Run `pytest tests/test_serial_evolution.py -q` — confirm no regressions.

---

### AP-3: test_preflight_cli — `test_create_async_execute_unblocks_when_answers_cover_must_questions`

**File:** `tests/test_preflight_cli.py:TestPreflightAnswerHandling::test_create_async_execute_unblocks_when_answers_cover_must_questions`
**Status:** Pre-existing failure. Hangs until pytest-timeout kills it.

#### Root Cause

The test monkeypatches `cli._quickstart_async` and `cli._run_preflight_async` on the `cli`
module object. However, `_create_async` (in `src/claw/cli/_monolith.py`) calls
`_quickstart_async` and `_run_preflight_async` as **bare module-local names**, not as
`cli._quickstart_async`. Python resolves bare names against the module's own global namespace
at call time — the monkeypatch on the `cli` module attribute has no effect on the internal
call inside `_monolith.py`.

The real `_quickstart_async` runs, which:
1. Initializes `ClawContext` (connects to the real `claw.db`)
2. Creates a real task in the database
3. Starts the full MicroClaw execution loop
4. Hangs waiting for a real LLM response

The test output confirms: `"Quickstart goal created. Task ID: c580e533..."` — a real task
was created in the production database during the test.

#### Fix

**Option A (cleanest — fix the patch target):** Patch the function inside `_monolith` where
it is actually called, not on the `cli` module:

```python
# tests/test_preflight_cli.py
import claw.cli._monolith as _monolith

monkeypatch.setattr(_monolith, "_run_preflight_async", fake_preflight_async)
monkeypatch.setattr(_monolith, "_quickstart_async", fake_quickstart_async)
```

This patches the name in the namespace where `_create_async` resolves it — the module where
both functions live.

**Option B (alternative):** Refactor `_create_async` to call the functions through an
injectable dependency, but that's a larger change and not required by any gate.

**Steps:**
1. Edit `tests/test_preflight_cli.py` around lines 94–95: add
   `import claw.cli._monolith as _monolith` and change both `monkeypatch.setattr` lines to
   target `_monolith` instead of `cli`.
2. Check the sibling test `test_create_async_execute_still_blocks_when_must_questions_remain`
   (line 122) — it has the same bug, fix both.
3. Run `pytest tests/test_preflight_cli.py -v` — both tests should pass in < 2s (no real
   LLM calls, no real DB writes).
4. Verify no spurious tasks were created in `claw.db` during the test run.

---

## PART 2: Showpiece Build Plans

---

### SBP-1: Self-Improvement Loop Demo — CAM_CAM Enhancing Itself

**Goal:** Run `cam enhance` against the CAM_CAM repository itself, capture the full output,
commit it as a recorded artifact. Demonstrates the closed self-improvement loop: the system
uses its own knowledge to improve its own code, records the outcome, which feeds back into
the corpus.

**Why this is the strongest showpiece move:** No other AI coding tool demo can say "the
system you are watching just used its own pattern library to improve its own source code, and
that outcome is now training data for the next run." It is a live proof of the flywheel.

#### Pre-conditions

- [ ] `cam enhance` working end-to-end (confirmed — autoresearch, M-RAG-5904)
- [ ] `cam learn ingest-codex-outcomes` available to close the loop after

#### Build Steps

**Step 1 — Identify a real gap in CAM_CAM to enhance.**
Run structural analysis only:
```bash
cam enhance /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM --dry-run 2>&1 | head -60
```
Confirm at least 1 verifiable gap exists (missing docstrings, coverage gap, missing type
hints on a public function). Do not proceed if analysis finds no actionable gap — pick a
different target file.

**Step 2 — Run enhance and capture full transcript.**
```bash
cam enhance /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM 2>&1 | tee /tmp/cam_self_enhance.txt
```
Must see: `approved=True, violations=0` in output. If it fails, diagnose before proceeding
— do not mark this step done on a failed run.

**Step 3 — Run full test suite to confirm enhance didn't break anything.**
```bash
pytest tests/ -q --ignore=tests/test_cag_convert.py 2>&1 | tail -5
```
Must show ≥ 4,169 passed, same 3 pre-existing failures, no new failures.

**Step 4 — Ingest the outcome.**
```bash
cam learn ingest-codex-outcomes -v
```
Confirm the enhance outcome row appears in output. Captures the flywheel closing.

**Step 5 — Commit transcript and outcome evidence.**
```bash
cp /tmp/cam_self_enhance.txt \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl/meta/SHOWPIECE_SELF_ENHANCE_2026-05-29.txt
```
Commit to both repos. The transcript is the artifact — a viewer can read it without running
the system.

**Step 6 — Document lifecycle change.**
Query the methodology promoted by the enhance run:
```bash
sqlite3 data/claw.db "
  SELECT id, lifecycle_state, success_count, failure_count
  FROM methodologies
  WHERE success_count > (SELECT success_count FROM methodologies WHERE id='<id>' LIMIT 1)
  ORDER BY updated_at DESC LIMIT 5;" 
```
Record before/after lifecycle state in the transcript header.

**Validation:** Transcript shows `approved=True`. Test suite unchanged. Codex outcome log
shows new `green` row. At least 1 methodology shows updated `success_count`.

---

### SBP-2: Recorded Enhancement Demo — External Repo With Before/After Diff

**Goal:** Pick one of the 937 pending architecture tasks targeting a recognizable open-source
repo, run `cam enhance`, and produce a `SHOWPIECE_DEMO.md` with before/after diffs that a
reviewer can read without running the system.

**Why this showpiece:** Gives a concrete, readable artifact that explains the value
proposition — "here is what the repo looked like, here is what CAM added, here is why
(citation to the methodology used)."

#### Candidate Repos (pick one)

Priority order:
1. `RAG-Anything` — pending architecture task, Python, recognizable project name
2. `dspy-agent-skills` — pending architecture task, Python, AI-adjacent
3. `autoresearch` — already has a successful enhance run (quality 1.00), good baseline

#### Build Steps

**Step 1 — Choose target and capture baseline.**
```bash
TARGET=/Volumes/WS4TB/repo421sn/RAG-Anything
git -C $TARGET diff HEAD > /tmp/before_baseline.diff   # should be empty/clean
git -C $TARGET log --oneline -3
```
Confirm repo is in a clean git state before enhance.

**Step 2 — Run enhance and capture full output.**
```bash
cam enhance $TARGET 2>&1 | tee /tmp/cam_enhance_demo.txt
```
Must achieve `approved=True`. If it fails, try next candidate. Do not force — the demo
must show a real success.

**Step 3 — Capture after-diff.**
```bash
git -C $TARGET diff HEAD > /tmp/after_diff.diff
git -C $TARGET diff --stat HEAD
```

**Step 4 — Extract the methodology citation.**
From the enhance output, find the methodology ID used (appears in the `cam_recall` section).
Run:
```bash
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "
  SELECT id, substr(problem_description,1,200), lifecycle_state, success_count
  FROM methodologies WHERE id='<id from output>';"
```

**Step 5 — Write `SHOWPIECE_DEMO.md`.**
File: `meta/SHOWPIECE_DEMO_2026-05-29.md`

Structure:
```
# CAM-Codx Enhancement Demo — <repo name>

## Target Repository
<name, purpose, github link if public>

## Gap Identified
<what structural_analysis found — missing tests/docs/type hints>

## Methodology Applied
ID: <id>
Source: <source repo it was mined from>
Lifecycle: <state> | Successes: <count>

## What Changed (diff summary)
<git diff --stat output>

## Detailed Diff
<full git diff — truncated to key files if very long>

## Verification Result
approved=True, violations=0, quality=<score>

## Outcome Recorded
codex_outcome_log row ID: <id>
cam learn ingest-codex-outcomes output: <row>
```

**Step 6 — Commit both repos.**
```bash
git add meta/SHOWPIECE_DEMO_2026-05-29.md && git commit
# in CAM_CAM: git add data/claw.db (don't — DB is gitignored)
# just commit the meta doc
```

**Validation:** `SHOWPIECE_DEMO.md` is self-contained and readable without running any
commands. The before/after diff shows real code was written and verified by the 7-gate
pipeline.

---

### SBP-3: Synergy Graph Report — Making the Knowledge Graph Visible

**Goal:** Run `cam learn synergies --report` (or equivalent query) to produce a human-readable
synergy graph summary. Publish it as `SHOWPIECE_SYNERGY_2026-05-29.md`. Demonstrates the
dimension of CAM that pure vector search databases don't have: discovered relationships
between patterns.

**Why this showpiece:** 43,082 pairs explored. 14 synergy matches. 772 methodology links.
That is a knowledge graph, not a lookup table. Making it visible makes the system feel alive
rather than like a static index.

#### Build Steps

**Step 1 — Check if `cam learn synergies --report` exists.**
```bash
cam learn synergies --help 2>&1
```
If `--report` flag doesn't exist, proceed with direct SQL (Step 2 only).

**Step 2 — Query the synergy graph directly.**
```bash
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "
SELECT
  s.result,
  s.synergy_type,
  ROUND(s.synergy_score, 3) as score,
  substr(a.problem_description, 1, 80) as method_a,
  substr(b.problem_description, 1, 80) as method_b
FROM synergy_exploration_log s
JOIN methodologies a ON s.cap_a_id = a.id
JOIN methodologies b ON s.cap_b_id = b.id
WHERE s.result = 'synergy'
ORDER BY s.synergy_score DESC;"
```

```bash
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "
SELECT link_type, COUNT(*) as count FROM methodology_links
GROUP BY link_type ORDER BY count DESC;"
```

**Step 3 — Query top co-retrieval pairs** (patterns that appear together in searches).
```bash
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "
SELECT
  link_type,
  substr(a.problem_description, 1, 70) as from_method,
  substr(b.problem_description, 1, 70) as to_method
FROM methodology_links ml
JOIN methodologies a ON ml.source_id = a.id
JOIN methodologies b ON ml.target_id = b.id
WHERE link_type = 'co_retrieval'
ORDER BY RANDOM()
LIMIT 10;"
```

**Step 4 — If `cam learn synergies --report` doesn't exist, add it.**
In `src/claw/cli/_monolith.py`, add a `--report` flag to the `synergies` subcommand that
prints a formatted table of the 14 synergy matches with scores and methodology descriptions.
This is a read-only addition — no data changes, no gate impact.

Implementation sketch (only if Step 1 confirms the flag is missing):
```python
if report:
    rows = db.execute("""
        SELECT s.synergy_type, ROUND(s.synergy_score,3),
               substr(a.problem_description,1,60), substr(b.problem_description,1,60)
        FROM synergy_exploration_log s
        JOIN methodologies a ON s.cap_a_id=a.id
        JOIN methodologies b ON s.cap_b_id=b.id
        WHERE s.result='synergy'
        ORDER BY s.synergy_score DESC
    """).fetchall()
    # print as rich Table
```

**Step 5 — Write `SHOWPIECE_SYNERGY_2026-05-29.md`.**
Structure:
```
# CAM-Codx Synergy Graph — 2026-05-29

## Exploration Summary
- 43,082 pairs explored
- 14 synergy matches found
- 772 total methodology links (co-retrieval, feeds_into, contradicts, enhances)

## Proven Synergy Pairs
| Score | Type | Method A | Method B |
|-------|------|----------|----------|
<rows from Step 2>

## Link Type Breakdown
<link_type counts from Step 2 query>

## What This Means
<plain-English paragraph: these are patterns that empirically appear together in 
successful builds — the equivalent of a recipe book that tracks which spices 
complement each other based on what real chefs actually cooked>
```

**Step 6 — Commit.**
Add to `codex-cam-methodology-impl/meta/` and commit.

**Validation:** The document is self-contained. A non-technical reader can understand what
synergy means from the plain-English section. The 14 pairs are real — not curated by hand,
discovered by the system.

---

## Execution Order Recommendation

| Priority | Plan | Prerequisite | Effort |
|----------|------|-------------|--------|
| 1 | AP-1 (test_novelty fix) | None | Single edit, 5 min |
| 2 | AP-2 (model list — user decision required) | User confirms approved models | Single edit after decision |
| 3 | AP-3 (preflight test hang fix) | None | Single edit, 10 min |
| 4 | SBP-3 (synergy report) | None — read-only queries | 30 min |
| 5 | SBP-2 (external repo demo) | Clean git state on target repo | 1 enhance run |
| 6 | SBP-1 (self-enhance CAM_CAM) | AP-1 done (tests clean before self-enhance) | 1 enhance run + ingest |
