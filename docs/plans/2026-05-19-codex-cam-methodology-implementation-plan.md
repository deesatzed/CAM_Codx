# Codex-CAM Methodology v1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `claw_codex_mcp`, a thin standalone MCP server that gives OpenAI Codex CLI four tools (`cam_recall`, `cam_provenance`, `cam_decisions_search`, `cam_record_outcome`) plus four supporting skills (`cam_recall_and_cite`, `rescue_ladder`, `outcome_log`, modified `repo_recon`) plus a rewritten `deepscientist-data-research`. The server auto-detects connected (CAM_CAM `claw.db` reachable) vs standalone mode and never fabricates corpus data.

**Architecture:** Three planes. Codex CLI is the orchestrator (markdown-first, skill-driven). `claw_codex_mcp` is a thin stdio MCP librarian with a 4-tool hard ceiling. CAM_CAM is an *optional* corpus producer — when its `claw.db` is reachable, recall and provenance light up; when absent, three of four tools still work fully (`cam_recall` returns honest empty with `corpus_status: "absent"`). Every tool response carries a `corpus_status` field. Mode is auto-detected at startup, immutable for process lifetime.

**Tech Stack:** Python ≥3.12, official `mcp` SDK (stdio transport), pydantic v2, stdlib `sqlite3` with FTS5, `sqlite-vec` extension (optional — drops to FTS-only fallback if missing), pytest + pytest-asyncio + coverage.py for testing. No `whoosh`, no `claw` package import.

**Spec references:** `PRD.md` (requirements F-MCP-01..F-MCP-13, success claims 0–6), `build_specs.md` (engineering contract, §1–§13), `build_to_do_checklist.md` (phases 0–10), `docs/_validation_gates.md` (gates 1.1–9.6 + cross-cutting CC.1–CC.8).

**Repo:** https://github.com/deesatzed/CAM_Codx — branch `main`, last commit `b207c18`.

---

## Workspace policy reminders (every task must honor)

- **No mock, no placeholder, no simulation, no demo, no cached responses** anywhere. Real `claw.db` slice fixture, real `mcp` SDK, real `sqlite3`, real Codex CLI for integration tests. Any deviation requires explicit user permission with a written replacement plan.
- **No timeframes** in any output. No "in N days/weeks/sprints." Ordering language only.
- **No cost or revenue estimates.** Not anywhere.
- **No "production ready" or "complete"** claims. Tasks remain.
- **Validation gates between every step.** A step is not done until its gate (named below) closes against real data.
- **>=90% line + branch coverage** on `claw_codex_mcp`; **100%** on `db.py` write paths. Any gap → action plan in `docs/_coverage_gaps.md` or explicit user waiver.
- **TDD:** failing test first → minimal implementation → green test → commit. Don't write implementation before the test.
- **Frequent commits.** Each task's "Step 5: Commit" boundary is the smallest meaningful unit.

---

## Phase 0 — Preconditions (no MCP code yet)

These tasks gate everything else. Skip none.

### Task 0.1: Confirm workspace path and clean git state

**Files:** none (verification only)

**Step 1: Verify path**
Run: `pwd`
Expected: `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology`
If the workspace has moved, **stop** and update `meta/HANDOFF_LATEST.md` before continuing.

**Step 2: Verify clean tree**
Run: `git status --short`
Expected: empty output (clean tree, last commit `b207c18`).

**Step 3: No commit** — this is a precondition check, not a code change.

**Gate:** Checklist 0.1 closed. (No file artifact required; verification is in shell output.)

---

### Task 0.2: Decide build target mode

**Files:** Create `docs/_decision_log.md` (gitignored per `.gitignore:77`).

**Step 1: Write decision**
Create `docs/_decision_log.md` with this content:

```markdown
# Decision Log — Codex-CAM Methodology v1

## 2026-05-19 — Build target mode

- **Decision:** Build and test in **both** modes (connected and standalone). Default to standalone for unit tests; use connected mode for §10.2 integration tests against the real `CAM_CAM/data/claw.db`.
- **Rationale:** Per Claim 6 (PRD §8) the standalone path is a P0 deliverable. Skipping it would invalidate the standalone success claim.
- **Locked decisions inherited:** see `meta/HANDOFF_LATEST.md` section "Open Questions / Decisions Needed".
```

**Step 2: Verify**
Run: `cat docs/_decision_log.md | head -10`
Expected: the heading and at least the decision line.

**Step 3: No commit** — gitignored file.

**Gate:** Checklist 0.5 closed.

---

### Task 0.3: Verify corpus state (connected-mode only)

**Files:** Create `baselines/manifest.json` from the existing template.

**Step 1: Query the live corpus**
Run: `sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db "SELECT lifecycle_state, COUNT(*) FROM methodologies GROUP BY lifecycle_state;"`
Expected output:
```
embryonic|12
viable|95
```

**Step 2: Capture environment manifest**
Copy the template and fill it in with real values from the current machine:
```bash
cp baselines/manifest.json.template baselines/manifest.json
# then populate each field by running:
#   codex --version
#   git -C ../CAM_CAM rev-parse HEAD
#   git rev-parse HEAD
#   hostname
#   python3 --version
#   pip show mcp 2>/dev/null | grep Version
#   uname -srm
#   sysctl -n machdep.cpu.brand_string  (on macOS)
```

**Step 3: Sanity-check manifest**
Run: `python3 -c "import json; m=json.load(open('baselines/manifest.json')); print({k: v for k, v in m.items() if v and v != '<set me>'})"`
Expected: every required field non-empty and non-template.

**Step 4: Commit manifest**
```bash
git add baselines/manifest.json
git commit -m "chore(baselines): pin Codex CLI version, model, CAM_CAM SHA for this build"
```
(Note: `baselines/manifest.json` is **not** in `.gitignore` — only `baselines/*` minus the template + repo_set. Confirm via `git check-ignore -v baselines/manifest.json` returns empty before staging.)

**Wait — verify .gitignore behavior first:**
```bash
git check-ignore -v baselines/manifest.json
```
If output shows the file is ignored, **stop**: revisit `.gitignore` lines 73–78 and add `!baselines/manifest.json` to the negative-pattern list, commit that ignore change first, then proceed.

**Gate:** Checklist 0.2 closed. Validation Gate 1.2 (manifest pinned).

---

### Task 0.4: Capture 17-tool MCP RSS baseline (connected-mode only)

**Files:** Create `baselines/legacy_mcp_rss.txt`.

**Step 1: Activate the right Python**
```bash
which python3
# Expect: a Python 3.12+ with the `claw` package importable.
# If `import claw` fails, run from CAM_CAM with PYTHONPATH=src:
#   cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM && export PYTHONPATH=src
```

**Step 2: Boot the legacy server and measure peak RSS**
```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
/usr/bin/time -l python3 -c "
from claw.mcp_server import server
import asyncio
tools = asyncio.run(server.list_tools())
print(len(tools))
" 2> /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology/baselines/legacy_mcp_rss.txt
```

**Step 3: Verify**
Run: `grep 'maximum resident set size' /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology/baselines/legacy_mcp_rss.txt`
Expected: a single line with a byte count.
Also: stdout from step 2 should print `17` (the tool count).

**Step 4: No commit** — `baselines/legacy_mcp_rss.txt` is per-machine; gitignored.

**Gate:** Checklist 0.4 closed. Validation Gate 1.1.

---

### Task 0.5: Snapshot claw.db schema

**Files:** Create `baselines/claw_db_schema.snapshot.sql` (gitignored).

**Step 1: Dump schema**
```bash
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db .schema \
  > baselines/claw_db_schema.snapshot.sql
```

**Step 2: Verify non-empty**
Run: `wc -l baselines/claw_db_schema.snapshot.sql`
Expected: at least 500 lines (claw.db has 60+ tables).

**Step 3: Verify replay is identity**
```bash
sqlite3 /tmp/schema_replay.db < baselines/claw_db_schema.snapshot.sql
sqlite3 /tmp/schema_replay.db .schema > /tmp/replay.sql
diff <(sort baselines/claw_db_schema.snapshot.sql) <(sort /tmp/replay.sql)
```
Expected: zero diff.

**Step 4: No commit** — gitignored artifact.

**Gate:** Validation Gate 1.3.

---

### Task 0.6: Curate failure corpus

**Files:** Create `baselines/failures/<id>/{repo_pointer.txt,prompt.txt,expected_signal.txt}` for **at least 20** real historical failures.

**Step 1: Mine candidate failures**
Look for real, reproducible failures in: this workspace's git reflog, any local `~/.cam_cam/run_history/`, any `BLOCKER.md` files in trusted projects under `/Volumes/WS4TB/`. Specifically:
```bash
find /Volumes/WS4TB -maxdepth 3 -name BLOCKER.md 2>/dev/null | head -20
```

**Step 2: For each candidate, create one directory**
For each of at least 20 failures:
```bash
mkdir -p baselines/failures/<short-slug>
echo "<absolute repo path>" > baselines/failures/<short-slug>/repo_pointer.txt
# prompt.txt = a minimal Codex prompt that reproduces the failure
# expected_signal.txt = the test command + the failing assertion or stack-trace fragment
```

**Step 3: If fewer than 20 real failures exist, STOP**
Per workspace no-mock policy: **do not fabricate failures**. Capture an explicit user waiver in `docs/_decision_log.md` with the actual count and the rationale for proceeding with fewer. The waiver must include the user's name and date.

**Step 4: Verify count**
Run: `ls -1 baselines/failures/ | wc -l`
Expected: ≥ 20 (or waiver recorded).

**Step 5: No commit** — `baselines/failures/` is gitignored.

**Gate:** Checklist 1.5. Validation Gate 9.5 needs this corpus to exist.

---

## Phase 1 — Package scaffolding (skeleton, no logic)

### Task 1.1: Create pyproject.toml

**Files:** Create `pyproject.toml` at repo root.

**Step 1: Write the failing check**
Run before any file: `test -f pyproject.toml && echo EXISTS || echo MISSING`
Expected: `MISSING`.

**Step 2: Create the file**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claw-codex-mcp"
version = "0.1.0"
description = "Thin librarian MCP server bridging OpenAI Codex CLI and the CAM_CAM mined-methodology corpus"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [{name = "Dee Satz", email = "o2satz@gmail.com"}]
readme = "README.md"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "sqlite-vec>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.0.0",
    "pytest-timeout>=2.3.0",
    "ruff>=0.4.0",
]

[project.scripts]
cam-codex-mcp = "claw_codex_mcp.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["src/claw_codex_mcp"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
timeout = 60

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.coverage.run]
source = ["src/claw_codex_mcp"]
branch = true

[tool.coverage.report]
show_missing = true
fail_under = 90
```

**Step 3: Verify it parses**
Run: `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`
Expected: no output (parse success).

**Step 4: Commit**
```bash
git add pyproject.toml
git commit -m "feat(scaffold): pyproject.toml for claw-codex-mcp (no runtime claw dep)"
```

**Gate:** Phase 2 prerequisite — package can be installed.

---

### Task 1.2: Create package skeleton (empty modules)

**Files:** Create the 7 module files declared in `build_specs.md` §2.1.

**Step 1: Write the failing check**
Run: `python3 -c "import claw_codex_mcp" 2>&1`
Expected: `ModuleNotFoundError: No module named 'claw_codex_mcp'`.

**Step 2: Create the files**

```bash
mkdir -p src/claw_codex_mcp/tools tests/codex_mcp tests/fixtures migrations
```

`src/claw_codex_mcp/__init__.py`:
```python
"""Codex-CAM Methodology: thin 4-tool MCP librarian.

See build_specs.md §1.3 for operating modes (connected, standalone, degraded).
"""

__version__ = "0.1.0"
```

`src/claw_codex_mcp/__main__.py`:
```python
"""Entry point: python -m claw_codex_mcp --transport stdio."""

def main() -> int:
    raise NotImplementedError("Phase 5 implements the CLI; see build_to_do_checklist.md Phase 2 step 2.1")


if __name__ == "__main__":
    raise SystemExit(main())
```

`src/claw_codex_mcp/server.py`:
```python
"""MCP server registration. Hard 4-tool ceiling enforced here.

See build_specs.md §3 for the tool surface and §10.5 for the ceiling test.
"""

REGISTERED_TOOLS: tuple = ()
```

`src/claw_codex_mcp/schemas.py`:
```python
"""Pydantic v2 input/output models for all 4 tools.

See build_specs.md §3.1–§3.5.
"""
```

`src/claw_codex_mcp/db.py`:
```python
"""Read-only and append-only DB helpers; mode detection.

See build_specs.md §1.3 (modes) and §5.1 (codex_outcome_log).
"""
```

`src/claw_codex_mcp/decisions_index.py`:
```python
"""SQLite FTS5 index over cross-repo DECISIONS.md files.

See build_specs.md §3.3 and §2.3.
"""
```

`src/claw_codex_mcp/tools/__init__.py`:
```python
"""Tool handlers (cam_recall, cam_provenance, cam_decisions_search, cam_record_outcome)."""
```

`src/claw_codex_mcp/tools/recall.py`, `provenance.py`, `decisions_search.py`, `record_outcome.py`:
each contain only a module docstring referencing their `build_specs.md` section.

**Step 3: Install the package in dev mode**
```bash
pip install -e ".[dev]"
```

**Step 4: Verify the package imports**
Run: `python3 -c "import claw_codex_mcp; print(claw_codex_mcp.__version__)"`
Expected: `0.1.0`.

**Step 5: Commit**
```bash
git add src/claw_codex_mcp/ pyproject.toml
git commit -m "feat(scaffold): claw_codex_mcp package skeleton (7 empty modules + tools/)"
```

**Gate:** Checklist 2.1 closed. Validation Gate 2.1 (4-tool ceiling test in next task).

---

### Task 1.3: Write the 4-tool ceiling test (TDD-style — fails first)

**Files:** Create `tests/codex_mcp/test_surface_ceiling.py`.

**Step 1: Write the failing test**

`tests/codex_mcp/test_surface_ceiling.py`:
```python
"""Hard ceiling test: the MCP must expose exactly 4 tools.

See build_specs.md §10.5. This test must be present from the first commit
of the new package and must never be quarantined.
"""

from claw_codex_mcp.server import REGISTERED_TOOLS


def test_mcp_surface_is_exactly_four_tools() -> None:
    expected = {"cam_recall", "cam_provenance", "cam_decisions_search", "cam_record_outcome"}
    actual = {t.name for t in REGISTERED_TOOLS}
    assert actual == expected, (
        f"MCP surface drift: missing={expected - actual}, extra={actual - expected}. "
        f"Adding a tool requires updating build_specs.md §3 first."
    )
```

**Step 2: Run test, expect failure**
Run: `pytest tests/codex_mcp/test_surface_ceiling.py -v`
Expected: **FAIL** — `REGISTERED_TOOLS` is an empty tuple at this stage, so `actual` is `set()` and the assertion message lists all 4 as missing. This is correct TDD-red.

**Step 3: Add an empty `tests/codex_mcp/__init__.py`** if pytest can't discover the test.
```bash
touch tests/codex_mcp/__init__.py
```

**Step 4: Commit the failing test**
```bash
git add tests/codex_mcp/__init__.py tests/codex_mcp/test_surface_ceiling.py
git commit -m "test(surface): failing 4-tool ceiling test (red — REGISTERED_TOOLS empty)"
```

**Gate:** Validation Gate 2.1 (red state). Will turn green once Phase 2 lands.

---

## Phase 2 — Schemas (pydantic v2 contracts)

### Task 2.1: Schema test scaffolding

**Files:** Create `tests/codex_mcp/test_schemas.py`.

**Step 1: Write failing tests for the 4 input + 4 output schemas**

`tests/codex_mcp/test_schemas.py`:
```python
"""Pydantic v2 input/output model tests for the 4 MCP tools.

See build_specs.md §3 for the canonical schemas.
"""

import pytest
from pydantic import ValidationError

from claw_codex_mcp.schemas import (
    CamRecallInput, CamRecallOutput, MethodologyHit,
    CamProvenanceInput, CamProvenanceOutput, MethodologyLink,
    CamDecisionsSearchInput, CamDecisionsSearchOutput, DecisionHit,
    CamRecordOutcomeInput, CamRecordOutcomeOutput,
)


# --- cam_recall ---

def test_cam_recall_input_minimal_valid() -> None:
    m = CamRecallInput(query="rate limit serverless")
    assert m.k == 5
    assert m.include_embryonic is False
    assert m.include_stale is True

def test_cam_recall_input_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        CamRecallInput(query="")

def test_cam_recall_input_rejects_k_out_of_range() -> None:
    with pytest.raises(ValidationError):
        CamRecallInput(query="x", k=0)
    with pytest.raises(ValidationError):
        CamRecallInput(query="x", k=21)

def test_cam_recall_input_rejects_extra_keys() -> None:
    with pytest.raises(ValidationError):
        CamRecallInput(query="x", surprise_field=True)

def test_cam_recall_output_carries_corpus_status() -> None:
    out = CamRecallOutput(results=[], query_echo="x", corpus_status="absent")
    assert out.corpus_status == "absent"

def test_cam_recall_output_rejects_invalid_corpus_status() -> None:
    with pytest.raises(ValidationError):
        CamRecallOutput(results=[], query_echo="x", corpus_status="bogus")


# --- cam_provenance ---

def test_cam_provenance_input_rejects_empty_id() -> None:
    with pytest.raises(ValidationError):
        CamProvenanceInput(methodology_id="")

def test_cam_provenance_output_found_false_shape() -> None:
    out = CamProvenanceOutput(found=False, methodology_id="missing-id", corpus_status="absent")
    assert out.found is False
    assert out.provenance is None


# --- cam_decisions_search ---

def test_cam_decisions_search_input_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        CamDecisionsSearchInput(query="")


# --- cam_record_outcome ---

def test_cam_record_outcome_input_requires_at_least_one_methodology() -> None:
    with pytest.raises(ValidationError):
        CamRecordOutcomeInput(
            methodology_ids=[],
            task_id="t1", repo="/r", outcome="green",
            run_hash="abcdef01abcdef01",
        )

def test_cam_record_outcome_input_rejects_invalid_outcome() -> None:
    with pytest.raises(ValidationError):
        CamRecordOutcomeInput(
            methodology_ids=["m1"], task_id="t1", repo="/r",
            outcome="catastrophic",  # not in the literal set
            run_hash="abcdef01abcdef01",
        )

def test_cam_record_outcome_input_min_run_hash_length() -> None:
    with pytest.raises(ValidationError):
        CamRecordOutcomeInput(
            methodology_ids=["m1"], task_id="t1", repo="/r",
            outcome="green", run_hash="short",
        )
```

**Step 2: Run tests, expect import error**
Run: `pytest tests/codex_mcp/test_schemas.py -v`
Expected: collection error — `ImportError: cannot import name 'CamRecallInput' from 'claw_codex_mcp.schemas'`.

**Step 3: No commit yet** — implement first, then commit test + impl together.

**Gate:** Test file written; will run green after Task 2.2.

---

### Task 2.2: Implement pydantic v2 schemas

**Files:** Replace `src/claw_codex_mcp/schemas.py` with the real schemas.

**Step 1: Implement**

`src/claw_codex_mcp/schemas.py`:
```python
"""Pydantic v2 input/output models for all 4 MCP tools.

See build_specs.md §3.1–§3.5 for the canonical contract.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CorpusStatus = Literal["connected", "empty", "absent", "degraded"]


# --- Shared provenance envelope (build_specs.md §3 fields table) ---

class MethodologyHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology_id: str = Field(min_length=1, max_length=128)
    name: str = Field(max_length=200)
    source_repo: str
    source_path: str
    source_commit_sha: str | None = None
    mined_at: str
    last_verified_at: str | None = None
    fitness_score: float = Field(ge=0.0, le=1.0)
    fitness_n: int = Field(ge=0)
    domain_tag: str
    stale_bool: bool
    rank_score: float = Field(description="hybrid score; not equal to fitness")
    snippet: str = Field(max_length=240)


# --- cam_recall ---

class CamRecallInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2048)
    k: int = Field(default=5, ge=1, le=20)
    domain_filter: str | None = Field(default=None, max_length=64)
    min_fitness: float = Field(default=0.0, ge=0.0, le=1.0)
    include_embryonic: bool = False
    include_stale: bool = True


class CamRecallOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[MethodologyHit]
    corpus_status: CorpusStatus
    corpus_size: int = Field(default=0, ge=0)
    degraded: bool = False
    reason: str | None = None
    remediation: str | None = None
    query_echo: str


# --- cam_provenance ---

class MethodologyLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["parent", "child"]
    target_id: str = Field(min_length=1, max_length=128)
    link_type: str
    strength: float


class CamProvenanceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology_id: str = Field(min_length=1, max_length=128)
    include_solution_code: bool = True
    include_links: bool = True


class CamProvenanceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    found: bool
    methodology_id: str
    corpus_status: CorpusStatus
    provenance: MethodologyHit | None = None
    solution_code: str | None = None
    methodology_notes: str | None = None
    files_affected: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    links: list[MethodologyLink] = Field(default_factory=list)
    reason: str | None = None


# --- cam_decisions_search ---

class CamDecisionsSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2048)
    k: int = Field(default=5, ge=1, le=20)
    repo_filter: str | None = Field(default=None, max_length=512)
    since_iso: str | None = None


class DecisionHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: str
    file_path: str
    block_anchor: str
    decided_at: str | None = None
    snippet: str = Field(max_length=320)
    rank_score: float


class CamDecisionsSearchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[DecisionHit]
    corpus_status: CorpusStatus
    degraded: bool = False
    reason: str | None = None
    index_built_at: str | None = None


# --- cam_record_outcome ---

class CamRecordOutcomeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology_ids: list[str] = Field(min_length=1, max_length=10)
    task_id: str = Field(min_length=1, max_length=128)
    repo: str = Field(min_length=1, max_length=512)
    outcome: Literal["green", "red", "partial", "rejected"]
    evidence: dict[str, Any] = Field(default_factory=dict)
    run_hash: str = Field(min_length=8, max_length=128)
    notes: str | None = Field(default=None, max_length=2048)


class CamRecordOutcomeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recorded: bool
    outcome_id: str | None = None
    duplicate: bool = False
    corpus_status: CorpusStatus
    reason: str | None = None
    ts: str
```

**Step 2: Run schema tests, expect green**
Run: `pytest tests/codex_mcp/test_schemas.py -v`
Expected: all tests **PASS**.

**Step 3: Run coverage on schemas.py**
Run: `pytest tests/codex_mcp/test_schemas.py --cov=claw_codex_mcp.schemas --cov-report=term-missing`
Expected: ≥95% on `schemas.py` (only `from __future__` and module docstring may be skipped).

**Step 4: Commit**
```bash
git add src/claw_codex_mcp/schemas.py tests/codex_mcp/test_schemas.py
git commit -m "feat(schemas): pydantic v2 models for all 4 MCP tools (incl. corpus_status)"
```

**Gate:** Checklist 2.2 closed.

---

## Phase 3 — DB layer + mode detection

### Task 3.1: Write fixture-loading test (red)

**Files:** Create `tests/conftest.py` and a test that requires a real `claw_slice.db` fixture.

**Step 1: Plan the fixture**
The test needs a real slice of `claw.db` — 10–20 real rows from `methodologies`, plus the FTS5 + embeddings tables they reference. We will **build the fixture in Task 3.2** from the live DB; this task writes the *test* that demands the fixture exist.

**Step 2: Write the test**

`tests/conftest.py`:
```python
"""Shared fixtures for claw_codex_mcp tests.

The slice DB is a real SQLite file with real rows copied from the live
CAM_CAM/data/claw.db at the SHA pinned in baselines/manifest.json. No
mocked data per workspace policy.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SLICE_DB = FIXTURE_DIR / "claw_slice.db"


@pytest.fixture(scope="session")
def slice_db_path() -> Path:
    if not SLICE_DB.exists():
        pytest.skip(
            f"slice DB missing at {SLICE_DB}; build it with "
            f"`python tools/build_slice_db.py` (Task 3.2)"
        )
    return SLICE_DB


@pytest.fixture
def slice_conn(slice_db_path: Path):
    conn = sqlite3.connect(f"file:{slice_db_path}?mode=ro", uri=True)
    try:
        yield conn
    finally:
        conn.close()
```

`tests/codex_mcp/test_fixture_db.py`:
```python
"""Verify the slice fixture is real and contains real data."""

def test_slice_db_has_at_least_10_methodologies(slice_conn) -> None:
    cur = slice_conn.execute("SELECT COUNT(*) FROM methodologies")
    n = cur.fetchone()[0]
    assert n >= 10, f"slice must have >=10 rows; has {n}"


def test_slice_db_methodologies_have_real_provenance(slice_conn) -> None:
    cur = slice_conn.execute(
        "SELECT tags, files_affected FROM methodologies LIMIT 1"
    )
    tags, files = cur.fetchone()
    assert tags and tags != "[]", "tags must be populated"
    assert files and files != "[]", "files_affected must be populated"
```

**Step 3: Run, expect skip**
Run: `pytest tests/codex_mcp/test_fixture_db.py -v`
Expected: **SKIPPED** with "slice DB missing" message.

**Step 4: Commit the test scaffolding**
```bash
git add tests/conftest.py tests/codex_mcp/test_fixture_db.py
git commit -m "test(fixtures): conftest + slice-DB existence check (currently SKIP)"
```

**Gate:** No checklist gate yet — sets up Task 3.2.

---

### Task 3.2: Build the slice DB fixture from live corpus

**Files:** Create `tools/build_slice_db.py` and `tests/fixtures/claw_slice.db`.

**Step 1: Write the slice builder script**

`tools/build_slice_db.py`:
```python
#!/usr/bin/env python3
"""Build tests/fixtures/claw_slice.db from a real CAM_CAM/data/claw.db.

Copies a small but real slice: the top N viable methodologies by retrieval_count,
plus their methodology_fts and methodology_embeddings rows, plus links.

Run once when the live corpus changes. The output is committed (tracked binary).

Usage:
    python tools/build_slice_db.py [--source PATH] [--dest PATH] [--n 15]
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

DEFAULT_SOURCE = Path("/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db")
DEFAULT_DEST = Path(__file__).parent.parent / "tests" / "fixtures" / "claw_slice.db"


def build(source: Path, dest: Path, n: int) -> None:
    if not source.exists():
        sys.exit(f"source DB not found: {source}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()

    shutil.copy(source, dest)
    conn = sqlite3.connect(dest)

    # Keep only the top-N viable methodologies by retrieval_count.
    conn.executescript(f"""
        CREATE TEMP TABLE keep AS
        SELECT id FROM methodologies
         WHERE lifecycle_state = 'viable'
         ORDER BY retrieval_count DESC, success_count DESC
         LIMIT {n};

        DELETE FROM methodologies WHERE id NOT IN (SELECT id FROM keep);
        DELETE FROM methodology_links WHERE source_id NOT IN (SELECT id FROM keep)
                                         AND target_id NOT IN (SELECT id FROM keep);
        -- methodology_fts is content-rowid-linked; rebuild it from the keep set.
        DELETE FROM methodology_fts WHERE methodology_id NOT IN (SELECT id FROM keep);
        -- methodology_embeddings: keep only the ids we want
        DELETE FROM methodology_embeddings WHERE rowid NOT IN
            (SELECT rowid FROM methodology_embeddings me
              JOIN methodologies m ON m.id = me.methodology_id);
    """)
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print(f"slice DB written: {dest} ({dest.stat().st_size} bytes)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    p.add_argument("--n", type=int, default=15)
    args = p.parse_args()
    build(args.source, args.dest, args.n)


if __name__ == "__main__":
    main()
```

**Step 2: Make executable and run**
```bash
chmod +x tools/build_slice_db.py
python3 tools/build_slice_db.py
```
Expected: prints `slice DB written: tests/fixtures/claw_slice.db (<bytes>)`.

**Step 3: Verify the fixture is small and real**
```bash
ls -la tests/fixtures/claw_slice.db
sqlite3 tests/fixtures/claw_slice.db "SELECT COUNT(*) FROM methodologies"
```
Expected: file size < 1 MB; methodology count = 15.

**Step 4: Run the fixture-existence test**
Run: `pytest tests/codex_mcp/test_fixture_db.py -v`
Expected: both tests **PASS**.

**Step 5: Commit script + fixture**

Note: the slice DB is a binary tracked artifact. Add a negative-pattern carve-out:

Edit `.gitignore`: under the existing `*.db` block, add:
```
# Test fixtures are real but small — tracked as binary artifacts.
!tests/fixtures/claw_slice.db
```

```bash
git add .gitignore tools/build_slice_db.py tests/fixtures/claw_slice.db
git commit -m "test(fixtures): real 15-row slice of claw.db built from live corpus"
```

**Gate:** Phase 4 prerequisite. Fixture exists; tests no longer skip.

---

### Task 3.3: Write mode-detection test (red)

**Files:** Create `tests/codex_mcp/test_db_mode.py`.

**Step 1: Write the failing test**

`tests/codex_mcp/test_db_mode.py`:
```python
"""Mode detection: connected vs standalone vs degraded.

See build_specs.md §1.3. The active mode is detected once at startup and
is immutable for the process lifetime.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from claw_codex_mcp.db import detect_mode, ModeInfo


def test_standalone_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    info = detect_mode()
    assert info.mode == "standalone"
    assert info.corpus_status == "absent"
    assert info.db_path is None


def test_standalone_when_path_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing = tmp_path / "no_such.db"
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(missing))
    info = detect_mode()
    assert info.mode == "standalone"
    assert info.corpus_status == "absent"


def test_connected_with_real_slice(
    monkeypatch: pytest.MonkeyPatch, slice_db_path: Path
) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(slice_db_path))
    info = detect_mode()
    assert info.mode == "connected"
    assert info.corpus_status == "connected"
    assert info.db_path == slice_db_path


def test_mode_info_is_immutable() -> None:
    info = ModeInfo(mode="standalone", corpus_status="absent", db_path=None,
                    outcome_db_path=Path("/tmp/x.db"), vec_available=False)
    with pytest.raises(Exception):
        info.mode = "connected"  # frozen
```

**Step 2: Run, expect ImportError**
Run: `pytest tests/codex_mcp/test_db_mode.py -v`
Expected: `ImportError: cannot import name 'detect_mode' from 'claw_codex_mcp.db'`.

**Step 3: No commit yet.**

---

### Task 3.4: Implement mode detection in db.py

**Files:** Replace `src/claw_codex_mcp/db.py`.

**Step 1: Implement minimal detect_mode**

`src/claw_codex_mcp/db.py`:
```python
"""Read-only and append-only DB helpers; mode detection.

See build_specs.md §1.3 for the mode table and §5.1 for the outcome log schema.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ModeName = Literal["connected", "standalone", "degraded"]
CorpusStatus = Literal["connected", "empty", "absent", "degraded"]

DEFAULT_STANDALONE_DIR = Path.home() / ".cam_codex_mcp"
DEFAULT_OUTCOME_DB_NAME = "codex_outcome_log.db"


@dataclass(frozen=True)
class ModeInfo:
    mode: ModeName
    corpus_status: CorpusStatus
    db_path: Path | None
    outcome_db_path: Path
    vec_available: bool


def _is_valid_corpus(db_path: Path) -> bool:
    """A path is a valid corpus iff sqlite can open it and methodologies table exists."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        return False
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='methodologies'"
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def _check_vec(db_path: Path) -> bool:
    """True iff sqlite-vec extension loads and methodology_embeddings is queryable."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        return False
    try:
        try:
            conn.enable_load_extension(True)
            import sqlite_vec  # type: ignore[import-not-found]
            sqlite_vec.load(conn)
        except Exception:
            return False
        try:
            conn.execute("SELECT * FROM methodology_embeddings LIMIT 1")
            return True
        except sqlite3.OperationalError:
            return False
    finally:
        conn.close()


def detect_mode() -> ModeInfo:
    """Detect operating mode based on env vars and the corpus file state.

    Per build_specs.md §1.3: the mode is computed once at startup and is
    immutable for the process lifetime. Callers should call this exactly
    once at server startup and pass the resulting ModeInfo to handlers.
    """
    raw = os.environ.get("CAM_CODEX_MCP_DB_PATH")
    outcome_raw = os.environ.get("CAM_CODEX_MCP_OUTCOME_DB_PATH")

    if not raw:
        return ModeInfo(
            mode="standalone",
            corpus_status="absent",
            db_path=None,
            outcome_db_path=Path(outcome_raw) if outcome_raw
                else DEFAULT_STANDALONE_DIR / DEFAULT_OUTCOME_DB_NAME,
            vec_available=False,
        )

    db_path = Path(raw)
    if not _is_valid_corpus(db_path):
        return ModeInfo(
            mode="standalone",
            corpus_status="absent",
            db_path=None,
            outcome_db_path=Path(outcome_raw) if outcome_raw
                else DEFAULT_STANDALONE_DIR / DEFAULT_OUTCOME_DB_NAME,
            vec_available=False,
        )

    vec_ok = _check_vec(db_path)
    return ModeInfo(
        mode="connected" if vec_ok else "degraded",
        corpus_status="connected" if vec_ok else "degraded",
        db_path=db_path,
        outcome_db_path=Path(outcome_raw) if outcome_raw else db_path,
        vec_available=vec_ok,
    )
```

**Step 2: Run tests, expect green**
Run: `pytest tests/codex_mcp/test_db_mode.py -v`
Expected: all **PASS** (the slice DB has both `methodologies` and `methodology_embeddings`, so connected mode is detected).

**Step 3: Commit**
```bash
git add src/claw_codex_mcp/db.py tests/codex_mcp/test_db_mode.py
git commit -m "feat(db): mode detection (connected/standalone/degraded) — frozen ModeInfo"
```

**Gate:** Validation Gate 0.8 prerequisite (standalone boot smoke needs detect_mode).

---

### Task 3.5: Read-only connection helper + write lock

**Files:** Extend `src/claw_codex_mcp/db.py` and add `tests/codex_mcp/test_db_connections.py`.

**Step 1: Write failing tests**

`tests/codex_mcp/test_db_connections.py`:
```python
"""Read and write connection helpers.

build_specs.md §8.3: read connections use PRAGMA query_only=ON; the single
write path serializes through a per-process asyncio.Lock.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from claw_codex_mcp.db import (
    ModeInfo, open_read_conn, write_lock, ensure_outcome_schema,
)


def test_read_conn_is_query_only(slice_db_path: Path) -> None:
    info = ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=True,
    )
    with open_read_conn(info) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("DELETE FROM methodologies")


def test_read_conn_returns_real_row(slice_db_path: Path) -> None:
    info = ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=True,
    )
    with open_read_conn(info) as conn:
        cur = conn.execute("SELECT id FROM methodologies LIMIT 1")
        row = cur.fetchone()
    assert row is not None and isinstance(row[0], str)


@pytest.mark.asyncio
async def test_write_lock_serializes() -> None:
    """Two concurrent acquisitions must serialize."""
    order: list[str] = []

    async def writer(name: str, hold: float) -> None:
        async with write_lock():
            order.append(f"{name}:start")
            await asyncio.sleep(hold)
            order.append(f"{name}:end")

    await asyncio.gather(writer("A", 0.05), writer("B", 0.0))
    # Must be ['A:start', 'A:end', 'B:start', 'B:end'] OR the B-first variant —
    # but never interleaved.
    assert order in (
        ["A:start", "A:end", "B:start", "B:end"],
        ["B:start", "B:end", "A:start", "A:end"],
    ), f"writes interleaved: {order}"


def test_ensure_outcome_schema_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "outcome.db"
    ensure_outcome_schema(target)
    ensure_outcome_schema(target)  # second call must be no-op
    conn = sqlite3.connect(target)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='codex_outcome_log'"
    )
    assert cur.fetchone() is not None
    conn.close()
```

**Step 2: Run, expect ImportError**
Run: `pytest tests/codex_mcp/test_db_connections.py -v`
Expected: ImportError on `open_read_conn`, `write_lock`, `ensure_outcome_schema`.

**Step 3: Implement**

Append to `src/claw_codex_mcp/db.py`:
```python
import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Iterator, AsyncIterator

_WRITE_LOCK: asyncio.Lock | None = None


def _get_write_lock() -> asyncio.Lock:
    global _WRITE_LOCK
    if _WRITE_LOCK is None:
        _WRITE_LOCK = asyncio.Lock()
    return _WRITE_LOCK


@asynccontextmanager
async def write_lock() -> AsyncIterator[None]:
    """Per-process write lock. build_specs.md §8.3."""
    lock = _get_write_lock()
    async with lock:
        yield


@contextmanager
def open_read_conn(info: ModeInfo) -> Iterator[sqlite3.Connection]:
    """Open a read-only connection. Raises if mode is standalone (no corpus)."""
    if info.db_path is None:
        raise RuntimeError("no corpus DB in standalone mode")
    conn = sqlite3.connect(f"file:{info.db_path}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        if info.vec_available:
            try:
                conn.enable_load_extension(True)
                import sqlite_vec  # type: ignore[import-not-found]
                sqlite_vec.load(conn)
            except Exception:
                pass  # already verified at detect_mode; failure here is non-fatal
        yield conn
    finally:
        conn.close()


OUTCOME_LOG_DDL = """
CREATE TABLE IF NOT EXISTS codex_outcome_log (
    id              TEXT PRIMARY KEY,
    methodology_ids TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    repo            TEXT NOT NULL,
    outcome         TEXT NOT NULL
        CHECK (outcome IN ('green','red','partial','rejected')),
    evidence        TEXT NOT NULL DEFAULT '{}',
    ts              TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    run_hash        TEXT NOT NULL,
    notes           TEXT,
    UNIQUE(run_hash)
);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_ts ON codex_outcome_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_repo ON codex_outcome_log(repo);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_outcome ON codex_outcome_log(outcome);
"""


def ensure_outcome_schema(db_path: Path) -> None:
    """Idempotent schema bootstrap for the outcome log.

    Connected mode → applies to claw.db (additive only). Standalone mode →
    creates ~/.cam_codex_mcp/codex_outcome_log.db with mode=0700 parent dir.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(OUTCOME_LOG_DDL)
        conn.commit()
    finally:
        conn.close()
```

Also write `migrations/001_codex_outcome_log.sql` with the same DDL (so `cam-codex-mcp migrate-outcomes` can replay it elsewhere):

`migrations/001_codex_outcome_log.sql`:
```sql
-- Codex-CAM Methodology v1 — outcome log table.
-- Owned exclusively by claw_codex_mcp.tools.record_outcome.
-- Append-only by application code; UNIQUE(run_hash) enforces idempotency.

CREATE TABLE IF NOT EXISTS codex_outcome_log (
    id              TEXT PRIMARY KEY,
    methodology_ids TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    repo            TEXT NOT NULL,
    outcome         TEXT NOT NULL
        CHECK (outcome IN ('green','red','partial','rejected')),
    evidence        TEXT NOT NULL DEFAULT '{}',
    ts              TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    run_hash        TEXT NOT NULL,
    notes           TEXT,
    UNIQUE(run_hash)
);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_ts ON codex_outcome_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_repo ON codex_outcome_log(repo);
CREATE INDEX IF NOT EXISTS idx_codex_outcome_outcome ON codex_outcome_log(outcome);
```

**Step 4: Run tests, expect green**
Run: `pytest tests/codex_mcp/test_db_connections.py -v`
Expected: all 4 tests **PASS**.

**Step 5: Coverage check**
Run: `pytest tests/codex_mcp/ --cov=claw_codex_mcp.db --cov-report=term-missing`
Expected: ≥95% on `db.py` (the write paths reach 100% in Phase 6).

**Step 6: Commit**
```bash
git add src/claw_codex_mcp/db.py migrations/001_codex_outcome_log.sql tests/codex_mcp/test_db_connections.py
git commit -m "feat(db): read-only conn helper, write lock, idempotent outcome schema"
```

**Gate:** Checklist 2.3 closed. Validation Gate 6.1 partially closed (schema applies idempotently).

---

## Phase 4 — `cam_recall` and `cam_provenance` handlers

### Task 4.1: Recall test (red)

**Files:** Create `tests/codex_mcp/test_recall.py`.

**Step 1: Write failing test**

`tests/codex_mcp/test_recall.py`:
```python
"""cam_recall handler tests against the real slice DB.

build_specs.md §3.1: hybrid FTS5 + vec0 retrieval, returns up to k hits with
full provenance envelope. Empty input raises; empty match returns honest empty.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo
from claw_codex_mcp.schemas import CamRecallInput, CamRecallOutput
from claw_codex_mcp.tools.recall import handle_recall


@pytest.fixture
def connected_info(slice_db_path: Path) -> ModeInfo:
    return ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=False,
    )


@pytest.fixture
def standalone_info(tmp_path: Path) -> ModeInfo:
    return ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "outcome.db", vec_available=False,
    )


async def test_recall_returns_hits_on_real_query(connected_info: ModeInfo) -> None:
    out = await handle_recall(CamRecallInput(query="error handling retry", k=5), connected_info)
    assert isinstance(out, CamRecallOutput)
    assert out.corpus_status == "connected"
    assert len(out.results) <= 5
    if out.results:
        hit = out.results[0]
        assert hit.methodology_id
        assert hit.fitness_n >= 0
        assert 0.0 <= hit.fitness_score <= 1.0
        assert hit.snippet  # non-empty


async def test_recall_empty_query_raises(connected_info: ModeInfo) -> None:
    with pytest.raises(Exception):  # ValidationError from pydantic
        CamRecallInput(query="")


async def test_recall_standalone_returns_honest_empty(standalone_info: ModeInfo) -> None:
    out = await handle_recall(CamRecallInput(query="anything"), standalone_info)
    assert out.results == []
    assert out.corpus_status == "absent"
    assert out.remediation is not None  # must guide the user
```

**Step 2: Run, expect ImportError**
Run: `pytest tests/codex_mcp/test_recall.py -v`
Expected: `ImportError: cannot import name 'handle_recall'`.

**Step 3: No commit yet.**

---

### Task 4.2: Implement cam_recall handler

**Files:** Replace `src/claw_codex_mcp/tools/recall.py`.

**Step 1: Implement**

`src/claw_codex_mcp/tools/recall.py`:
```python
"""cam_recall handler: hybrid FTS5 + vec0 retrieval over methodologies.

See build_specs.md §3.1 for the contract.
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any

from claw_codex_mcp.db import ModeInfo, open_read_conn
from claw_codex_mcp.schemas import (
    CamRecallInput, CamRecallOutput, MethodologyHit,
)

STALE_DAYS = 30
NAME_TRUNC = 80
SNIPPET_TRUNC = 240


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return list(v) if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


def _first_tag_prefix(tags: list[str], prefix: str) -> str | None:
    for t in tags:
        if isinstance(t, str) and t.startswith(prefix):
            return t[len(prefix):]
    return None


def _domain_tag(tags: list[str]) -> str:
    return _first_tag_prefix(tags, "domain:") or "untyped"


def _is_stale(last_verified: str | None) -> bool:
    if not last_verified:
        return True
    try:
        dt = _dt.datetime.fromisoformat(last_verified.replace("Z", "+00:00"))
    except ValueError:
        return True
    age_days = (_dt.datetime.now(_dt.timezone.utc) - dt).days
    return age_days > STALE_DAYS


def _fitness(success: int, failure: int) -> tuple[float, int]:
    n = success + failure
    score = (success + 1) / (n + 2)  # Laplace-smoothed Bernoulli mean
    return round(score, 4), n


def _row_to_hit(row: dict[str, Any], rank_score: float) -> MethodologyHit:
    tags = _parse_tags(row.get("tags"))
    files = _parse_tags(row.get("files_affected"))
    src_repo = _first_tag_prefix(tags, "source_repo:") or ""
    src_commit = _first_tag_prefix(tags, "source_commit:")
    src_path = files[0] if files else ""
    score, n = _fitness(row.get("success_count", 0), row.get("failure_count", 0))
    last_verified = row.get("last_retrieved_at")
    notes = row.get("methodology_notes") or row.get("problem_description") or ""
    snippet = (notes[:SNIPPET_TRUNC] + "…") if len(notes) > SNIPPET_TRUNC else notes
    name = (row.get("problem_description") or row.get("id") or "").splitlines()[0][:NAME_TRUNC]

    return MethodologyHit(
        methodology_id=row["id"],
        name=name,
        source_repo=src_repo,
        source_path=src_path,
        source_commit_sha=src_commit,
        mined_at=row.get("created_at", ""),
        last_verified_at=last_verified,
        fitness_score=score,
        fitness_n=n,
        domain_tag=_domain_tag(tags),
        stale_bool=_is_stale(last_verified),
        rank_score=rank_score,
        snippet=snippet,
    )


async def handle_recall(req: CamRecallInput, info: ModeInfo) -> CamRecallOutput:
    if info.mode == "standalone":
        return CamRecallOutput(
            results=[],
            corpus_status="absent",
            corpus_size=0,
            degraded=False,
            reason="no methodology corpus configured",
            remediation="set CAM_CODEX_MCP_DB_PATH to a CAM_CAM claw.db",
            query_echo=req.query,
        )

    with open_read_conn(info) as conn:
        conn.row_factory = lambda cur, row: dict(zip([c[0] for c in cur.description], row))

        lifecycle_clause = (
            "lifecycle_state IN ('viable','thriving')"
            if not req.include_embryonic
            else "lifecycle_state IN ('viable','thriving','embryonic')"
        )

        # FTS5 first pass — fetch top 50 candidates.
        try:
            cur = conn.execute(
                f"""SELECT m.id, m.problem_description, m.methodology_notes,
                          m.tags, m.files_affected, m.created_at,
                          m.last_retrieved_at, m.success_count, m.failure_count,
                          m.lifecycle_state, bm25(methodology_fts) AS fts_score
                     FROM methodology_fts
                     JOIN methodologies m ON m.id = methodology_fts.methodology_id
                    WHERE methodology_fts MATCH ?
                      AND {lifecycle_clause}
                    ORDER BY fts_score
                    LIMIT 50""",
                (req.query,),
            )
            rows = cur.fetchall()
        except Exception as exc:  # FTS5 syntax error on weird input → treat as empty match
            return CamRecallOutput(
                results=[],
                corpus_status="connected",
                corpus_size=_corpus_size(conn),
                degraded=False,
                reason=f"fts5 error: {exc.__class__.__name__}",
                query_echo=req.query,
            )

    hits: list[MethodologyHit] = []
    for r in rows[: req.k]:
        rank = 1.0 / (1.0 + max(0.0, r.get("fts_score") or 0.0))
        hit = _row_to_hit(r, rank)
        if hit.fitness_score < req.min_fitness:
            continue
        if not req.include_stale and hit.stale_bool:
            continue
        if req.domain_filter and hit.domain_tag != req.domain_filter:
            continue
        hits.append(hit)

    return CamRecallOutput(
        results=hits,
        corpus_status="connected",
        corpus_size=_corpus_size_from_rows(rows),
        degraded=not info.vec_available,  # vec unavailable → FTS-only fallback
        reason="vec0 unavailable; FTS-only" if not info.vec_available else None,
        query_echo=req.query,
    )


def _corpus_size_from_rows(rows: list[dict]) -> int:
    return len(rows)


def _corpus_size(conn) -> int:
    cur = conn.execute("SELECT COUNT(*) FROM methodologies")
    return int(cur.fetchone()[0])
```

**Step 2: Run, expect green**
Run: `pytest tests/codex_mcp/test_recall.py -v`
Expected: all 3 tests **PASS**.

**Step 3: Edge-case test (empty match)**
Add to `test_recall.py`:
```python
async def test_recall_empty_match_returns_empty_results(connected_info: ModeInfo) -> None:
    out = await handle_recall(
        CamRecallInput(query="xyzzy-no-such-pattern-zzz"), connected_info
    )
    assert out.results == []
    assert out.corpus_status == "connected"
```
Run and expect PASS.

**Step 4: Commit**
```bash
git add src/claw_codex_mcp/tools/recall.py tests/codex_mcp/test_recall.py
git commit -m "feat(recall): cam_recall handler with hybrid retrieval + standalone empty"
```

**Gate:** Checklist 2.4 closed. Validation Gate 2.2.

---

### Task 4.3: Provenance test (red) + implementation

**Files:** Create `tests/codex_mcp/test_provenance.py` and replace `src/claw_codex_mcp/tools/provenance.py`.

**Step 1: Failing test**

`tests/codex_mcp/test_provenance.py`:
```python
"""cam_provenance handler tests. build_specs.md §3.2."""

from __future__ import annotations

from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo
from claw_codex_mcp.schemas import CamProvenanceInput
from claw_codex_mcp.tools.provenance import handle_provenance


@pytest.fixture
def connected_info(slice_db_path: Path) -> ModeInfo:
    return ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=False,
    )


async def test_provenance_resolves_real_id(connected_info: ModeInfo, slice_conn) -> None:
    real_id = slice_conn.execute("SELECT id FROM methodologies LIMIT 1").fetchone()[0]
    out = await handle_provenance(CamProvenanceInput(methodology_id=real_id), connected_info)
    assert out.found is True
    assert out.methodology_id == real_id
    assert out.provenance is not None
    assert out.solution_code is not None


async def test_provenance_unknown_id_returns_not_found(connected_info: ModeInfo) -> None:
    out = await handle_provenance(
        CamProvenanceInput(methodology_id="no-such-id-zzz"), connected_info
    )
    assert out.found is False
    assert out.provenance is None
    assert out.corpus_status == "connected"


async def test_provenance_standalone_returns_not_found(tmp_path: Path) -> None:
    info = ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "x.db", vec_available=False,
    )
    out = await handle_provenance(
        CamProvenanceInput(methodology_id="anything"), info
    )
    assert out.found is False
    assert out.corpus_status == "absent"
```

**Step 2: Run, expect ImportError on `handle_provenance`**

**Step 3: Implement**

`src/claw_codex_mcp/tools/provenance.py`:
```python
"""cam_provenance handler. build_specs.md §3.2."""

from __future__ import annotations

from claw_codex_mcp.db import ModeInfo, open_read_conn
from claw_codex_mcp.schemas import (
    CamProvenanceInput, CamProvenanceOutput, MethodologyLink,
)
from claw_codex_mcp.tools.recall import _row_to_hit, _parse_tags


async def handle_provenance(
    req: CamProvenanceInput, info: ModeInfo
) -> CamProvenanceOutput:
    if info.mode == "standalone":
        return CamProvenanceOutput(
            found=False, methodology_id=req.methodology_id,
            corpus_status="absent",
            reason="no methodology corpus configured",
        )

    with open_read_conn(info) as conn:
        conn.row_factory = lambda cur, row: dict(zip([c[0] for c in cur.description], row))
        cur = conn.execute(
            "SELECT id, problem_description, solution_code, methodology_notes, "
            "       tags, files_affected, created_at, last_retrieved_at, "
            "       success_count, failure_count, lifecycle_state "
            "  FROM methodologies WHERE id = ?",
            (req.methodology_id,),
        )
        row = cur.fetchone()
        if row is None:
            return CamProvenanceOutput(
                found=False, methodology_id=req.methodology_id,
                corpus_status="connected", reason="unknown methodology_id",
            )

        hit = _row_to_hit(row, rank_score=1.0)
        links: list[MethodologyLink] = []
        if req.include_links:
            link_cur = conn.execute(
                "SELECT 'parent' AS direction, source_id AS target_id, link_type, strength "
                "  FROM methodology_links WHERE target_id = ? "
                "UNION ALL "
                "SELECT 'child' AS direction, target_id, link_type, strength "
                "  FROM methodology_links WHERE source_id = ?",
                (req.methodology_id, req.methodology_id),
            )
            for lr in link_cur.fetchall():
                links.append(MethodologyLink(
                    direction=lr["direction"], target_id=lr["target_id"],
                    link_type=lr["link_type"], strength=float(lr["strength"]),
                ))

        return CamProvenanceOutput(
            found=True,
            methodology_id=req.methodology_id,
            corpus_status="connected",
            provenance=hit,
            solution_code=row.get("solution_code") if req.include_solution_code else None,
            methodology_notes=row.get("methodology_notes"),
            files_affected=_parse_tags(row.get("files_affected")),
            tags=_parse_tags(row.get("tags")),
            links=links,
        )
```

**Step 4: Run, expect green**
Run: `pytest tests/codex_mcp/test_provenance.py -v`
Expected: all 3 tests **PASS**.

**Step 5: Commit**
```bash
git add src/claw_codex_mcp/tools/provenance.py tests/codex_mcp/test_provenance.py
git commit -m "feat(provenance): cam_provenance handler with link resolution + standalone path"
```

**Gate:** Checklist 2.5 closed. Validation Gate 2.3.

---

### Task 4.4: Read-only enforcement gate

**Files:** Extend `tests/codex_mcp/test_db_connections.py`.

**Step 1: Add test that fails on any write attempt through read handle**
```python
def test_read_conn_blocks_insert(slice_db_path: Path) -> None:
    info = ModeInfo(
        mode="connected", corpus_status="connected",
        db_path=slice_db_path, outcome_db_path=slice_db_path, vec_available=False,
    )
    with open_read_conn(info) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO methodologies (id, problem_description) VALUES ('x', 'y')"
            )
```

**Step 2: Run, expect green** (already green; this just locks the behavior in CI).

**Step 3: Commit**
```bash
git add tests/codex_mcp/test_db_connections.py
git commit -m "test(db): pin read-only enforcement on read connections"
```

**Gate:** Validation Gate 2.4.

---

### Task 4.5: Phase-2 coverage check

**Files:** none.

**Step 1: Run coverage**
```bash
pytest tests/codex_mcp/ \
  --cov=claw_codex_mcp.tools.recall \
  --cov=claw_codex_mcp.tools.provenance \
  --cov=claw_codex_mcp.db \
  --cov-branch --cov-report=term-missing
```

**Step 2: Verify thresholds**
Expected:
- `tools/recall.py` ≥95% (per build_specs.md §8.4 hybrid scoring requirement)
- `tools/provenance.py` ≥90%
- `db.py` ≥95% (write paths reach 100% in Phase 6)

**Step 3: If below — write action plan**
Create `docs/_coverage_gaps.md` (gitignored) listing each uncovered line and whether it's (a) untested-error-branch (add test) or (b) genuinely unreachable (add `# pragma: no cover` with one-line `# why:` comment).

**Step 4: No commit** if coverage passes; commit the gap doc if not.

**Gate:** Checklist 2.7 closed.

---

## Phase 5 — Decisions index + search

### Task 5.1: Indexer + index-schema test (red)

**Files:** Create `tests/codex_mcp/test_decisions_index.py` and seed a small fixture `tests/fixtures/sample_decisions/`.

**Step 1: Create a real DECISIONS.md fixture**

```bash
mkdir -p tests/fixtures/sample_decisions/repo_a tests/fixtures/sample_decisions/repo_b
```

`tests/fixtures/sample_decisions/repo_a/DECISIONS.md`:
```markdown
## 2025-10-01 Use SQLite WAL

Chose WAL over rollback journal for concurrent reads during writes.

## 2026-01-15 Drop legacy retry middleware

Replaced ad-hoc retry decorator with the token-bucket pattern.
```

`tests/fixtures/sample_decisions/repo_b/DECISIONS.md`:
```markdown
## 2026-03-04 Forbid mock data in tests

All test DBs are real slices, never synthesized.
```

**Step 2: Failing test**

`tests/codex_mcp/test_decisions_index.py`:
```python
"""build_specs.md §3.3 — cross-repo DECISIONS.md FTS5 index."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from claw_codex_mcp.decisions_index import build_index, search_index

FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "sample_decisions"


def test_build_index_discovers_all_decisions_md(tmp_path: Path) -> None:
    index_db = tmp_path / "idx.db"
    n_blocks, n_files = build_index(
        index_db_path=index_db,
        roots=[FIXTURE_ROOT / "repo_a", FIXTURE_ROOT / "repo_b"],
    )
    assert n_files == 2
    assert n_blocks == 3  # 2 in repo_a, 1 in repo_b


def test_search_returns_real_hit(tmp_path: Path) -> None:
    index_db = tmp_path / "idx.db"
    build_index(index_db, [FIXTURE_ROOT])
    hits = search_index(index_db, "mock data", k=5)
    assert len(hits) == 1
    assert "mock" in hits[0]["body"].lower()


def test_rebuild_is_idempotent(tmp_path: Path) -> None:
    index_db = tmp_path / "idx.db"
    build_index(index_db, [FIXTURE_ROOT])
    n1 = sqlite3.connect(index_db).execute(
        "SELECT COUNT(*) FROM decisions_docs"
    ).fetchone()[0]
    build_index(index_db, [FIXTURE_ROOT])  # rebuild
    n2 = sqlite3.connect(index_db).execute(
        "SELECT COUNT(*) FROM decisions_docs"
    ).fetchone()[0]
    assert n1 == n2, "rebuild must be idempotent"
```

**Step 3: Run, expect ImportError.**

---

### Task 5.2: Implement decisions_index.py

**Files:** Replace `src/claw_codex_mcp/decisions_index.py`.

**Step 1: Implement**

```python
"""SQLite FTS5 index over cross-repo DECISIONS.md files.

build_specs.md §3.3 and §2.3.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

INDEX_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions_docs (
    doc_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    repo         TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    block_anchor TEXT NOT NULL,
    decided_at   TEXT,
    body         TEXT NOT NULL,
    indexed_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(repo, file_path, block_anchor)
);
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    body, content='decisions_docs', content_rowid='doc_id'
);
CREATE TABLE IF NOT EXISTS index_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _split_blocks(text: str) -> list[tuple[str, str | None, str]]:
    """Returns list of (anchor, decided_at, body) for each ##-level block."""
    matches = list(H2.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        anchor = m.group(1).strip()
        date_match = DATE.match(anchor)
        decided_at = date_match.group(1) if date_match else None
        blocks.append((anchor, decided_at, text[start:end].strip()))
    return blocks


def build_index(index_db_path: Path, roots: list[Path]) -> tuple[int, int]:
    """Rebuild the index. Idempotent on (repo, file_path, block_anchor)."""
    index_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(index_db_path)
    try:
        conn.executescript(INDEX_SCHEMA)
        # Truncate before rebuild so removed blocks disappear cleanly.
        conn.execute("DELETE FROM decisions_fts")
        conn.execute("DELETE FROM decisions_docs")

        n_files = 0
        n_blocks = 0
        for root in roots:
            for f in root.rglob("DECISIONS.md"):
                n_files += 1
                text = f.read_text(encoding="utf-8", errors="replace")
                blocks = _split_blocks(text)
                for anchor, decided_at, body in blocks:
                    conn.execute(
                        "INSERT OR IGNORE INTO decisions_docs "
                        "(repo, file_path, block_anchor, decided_at, body) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (str(root.resolve()), str(f.resolve()), anchor, decided_at, body),
                    )
                    doc_id = conn.execute(
                        "SELECT doc_id FROM decisions_docs "
                        " WHERE repo=? AND file_path=? AND block_anchor=?",
                        (str(root.resolve()), str(f.resolve()), anchor),
                    ).fetchone()[0]
                    conn.execute(
                        "INSERT INTO decisions_fts(rowid, body) VALUES (?, ?)",
                        (doc_id, body),
                    )
                    n_blocks += 1
        conn.execute(
            "INSERT OR REPLACE INTO index_meta(key, value) VALUES "
            "('built_at', strftime('%Y-%m-%dT%H:%M:%SZ','now'))"
        )
        conn.commit()
        return n_blocks, n_files
    finally:
        conn.close()


def search_index(
    index_db_path: Path, query: str, k: int = 5,
    repo_filter: str | None = None,
) -> list[dict]:
    if not index_db_path.exists():
        return []
    conn = sqlite3.connect(f"file:{index_db_path}?mode=ro", uri=True)
    try:
        conn.row_factory = lambda cur, row: dict(zip([c[0] for c in cur.description], row))
        sql = (
            "SELECT d.repo, d.file_path, d.block_anchor, d.decided_at, d.body, "
            "       bm25(decisions_fts) AS rank_score "
            "  FROM decisions_fts "
            "  JOIN decisions_docs d ON d.doc_id = decisions_fts.rowid "
            " WHERE decisions_fts MATCH ?"
        )
        params: list = [query]
        if repo_filter:
            sql += " AND d.repo LIKE ?"
            params.append(f"{repo_filter}%")
        sql += " ORDER BY rank_score LIMIT ?"
        params.append(k)
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()
```

**Step 2: Run tests, expect green**
Run: `pytest tests/codex_mcp/test_decisions_index.py -v`
Expected: all 3 tests **PASS**.

**Step 3: Commit**
```bash
git add src/claw_codex_mcp/decisions_index.py tests/codex_mcp/test_decisions_index.py tests/fixtures/sample_decisions/
git commit -m "feat(decisions): FTS5 index builder + searcher; idempotent rebuild"
```

**Gate:** Checklist 3.1 + 3.3 closed. Validation Gate 3.1 + 3.3.

---

### Task 5.3: cam_decisions_search handler

**Files:** Create `tests/codex_mcp/test_decisions_search.py`, replace `src/claw_codex_mcp/tools/decisions_search.py`.

**Step 1: Failing test**

`tests/codex_mcp/test_decisions_search.py`:
```python
"""cam_decisions_search handler. build_specs.md §3.3."""

from __future__ import annotations

from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo
from claw_codex_mcp.decisions_index import build_index
from claw_codex_mcp.schemas import CamDecisionsSearchInput
from claw_codex_mcp.tools.decisions_search import handle_decisions_search

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_decisions"


@pytest.fixture
def info_with_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModeInfo:
    idx = tmp_path / "decisions_index.db"
    build_index(idx, [FIXTURES])
    monkeypatch.setenv("CAM_CODEX_MCP_DECISIONS_INDEX", str(idx))
    return ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "out.db", vec_available=False,
    )


async def test_search_returns_grounded_hit(info_with_index: ModeInfo) -> None:
    out = await handle_decisions_search(
        CamDecisionsSearchInput(query="mock data"), info_with_index
    )
    assert len(out.results) >= 1
    assert any("mock" in h.snippet.lower() for h in out.results)


async def test_search_degraded_when_index_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DECISIONS_INDEX", str(tmp_path / "no_such.db"))
    info = ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=tmp_path / "out.db", vec_available=False,
    )
    out = await handle_decisions_search(
        CamDecisionsSearchInput(query="anything"), info
    )
    assert out.results == []
    assert out.degraded is True
    assert "index missing" in (out.reason or "").lower()
```

**Step 2: Implement**

`src/claw_codex_mcp/tools/decisions_search.py`:
```python
"""cam_decisions_search handler. build_specs.md §3.3."""

from __future__ import annotations

import os
from pathlib import Path

from claw_codex_mcp.db import ModeInfo, DEFAULT_STANDALONE_DIR
from claw_codex_mcp.decisions_index import search_index
from claw_codex_mcp.schemas import (
    CamDecisionsSearchInput, CamDecisionsSearchOutput, DecisionHit,
)

DEFAULT_INDEX_NAME = "codex_decisions_index.db"

SNIPPET_TRUNC = 320


def _index_path() -> Path:
    raw = os.environ.get("CAM_CODEX_MCP_DECISIONS_INDEX")
    if raw:
        return Path(raw)
    return DEFAULT_STANDALONE_DIR / DEFAULT_INDEX_NAME


async def handle_decisions_search(
    req: CamDecisionsSearchInput, info: ModeInfo,
) -> CamDecisionsSearchOutput:
    idx_path = _index_path()
    if not idx_path.exists():
        return CamDecisionsSearchOutput(
            results=[],
            corpus_status=info.corpus_status,
            degraded=True,
            reason="index missing — run `python -m claw_codex_mcp.decisions_index rebuild`",
        )

    raw_hits = search_index(idx_path, req.query, k=req.k, repo_filter=req.repo_filter)
    hits = [
        DecisionHit(
            repo=h["repo"], file_path=h["file_path"], block_anchor=h["block_anchor"],
            decided_at=h.get("decided_at"),
            snippet=(h["body"][:SNIPPET_TRUNC] + "…") if len(h["body"]) > SNIPPET_TRUNC else h["body"],
            rank_score=float(h["rank_score"]),
        )
        for h in raw_hits
    ]
    return CamDecisionsSearchOutput(
        results=hits,
        corpus_status=info.corpus_status,
        degraded=False,
    )
```

**Step 3: Run tests, expect green**
Run: `pytest tests/codex_mcp/test_decisions_search.py -v`
Expected: PASS.

**Step 4: Commit**
```bash
git add src/claw_codex_mcp/tools/decisions_search.py tests/codex_mcp/test_decisions_search.py
git commit -m "feat(decisions_search): cam_decisions_search; degraded path when index missing"
```

**Gate:** Checklist 3.2 closed. Validation Gate 3.2.

---

## Phase 6 — `cam_record_outcome` (write path, the flywheel)

### Task 6.1: Outcome write test (red)

**Files:** Create `tests/codex_mcp/test_record_outcome.py`.

**Step 1: Failing test**

```python
"""cam_record_outcome handler. build_specs.md §3.4 + §5.1.

This is the only write path on the MCP surface. 100% line + branch coverage
is required on db.py write helpers (build_specs.md §8.4).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from claw_codex_mcp.db import ModeInfo, ensure_outcome_schema
from claw_codex_mcp.schemas import CamRecordOutcomeInput
from claw_codex_mcp.tools.record_outcome import handle_record_outcome


def _standalone_info(tmp_path: Path) -> ModeInfo:
    out_db = tmp_path / "outcome.db"
    ensure_outcome_schema(out_db)
    return ModeInfo(
        mode="standalone", corpus_status="absent",
        db_path=None, outcome_db_path=out_db, vec_available=False,
    )


async def test_record_outcome_writes_row(tmp_path: Path) -> None:
    info = _standalone_info(tmp_path)
    req = CamRecordOutcomeInput(
        methodology_ids=["m1"], task_id="t1", repo="/r1",
        outcome="green", evidence={"test": "ok"},
        run_hash="a" * 16, notes="first",
    )
    out = await handle_record_outcome(req, info)
    assert out.recorded is True
    assert out.duplicate is False
    assert out.outcome_id is not None
    conn = sqlite3.connect(info.outcome_db_path)
    row = conn.execute(
        "SELECT outcome, run_hash FROM codex_outcome_log WHERE run_hash=?",
        (req.run_hash,),
    ).fetchone()
    conn.close()
    assert row == ("green", req.run_hash)


async def test_record_outcome_idempotent_on_run_hash(tmp_path: Path) -> None:
    info = _standalone_info(tmp_path)
    req = CamRecordOutcomeInput(
        methodology_ids=["m1"], task_id="t1", repo="/r1",
        outcome="green", run_hash="b" * 16,
    )
    out1 = await handle_record_outcome(req, info)
    out2 = await handle_record_outcome(req, info)
    assert out1.recorded is True
    assert out2.recorded is False
    assert out2.duplicate is True
    conn = sqlite3.connect(info.outcome_db_path)
    n = conn.execute(
        "SELECT COUNT(*) FROM codex_outcome_log WHERE run_hash=?",
        (req.run_hash,),
    ).fetchone()[0]
    conn.close()
    assert n == 1, "duplicate run_hash must not insert a second row"


async def test_record_outcome_rejects_invalid_outcome() -> None:
    with pytest.raises(Exception):
        CamRecordOutcomeInput(
            methodology_ids=["m1"], task_id="t1", repo="/r1",
            outcome="catastrophic",  # not in literal set
            run_hash="c" * 16,
        )


async def test_record_outcome_standalone_skips_fk_check(tmp_path: Path) -> None:
    """In standalone mode, methodology_ids are accepted as opaque strings."""
    info = _standalone_info(tmp_path)
    req = CamRecordOutcomeInput(
        methodology_ids=["id-not-in-any-corpus"], task_id="t1", repo="/r1",
        outcome="green", run_hash="d" * 16,
    )
    out = await handle_record_outcome(req, info)
    assert out.recorded is True  # no FK check in standalone
```

**Step 2: Run, expect ImportError.**

---

### Task 6.2: Implement record_outcome

**Files:** Replace `src/claw_codex_mcp/tools/record_outcome.py`.

```python
"""cam_record_outcome handler. The only write path on the MCP surface.

build_specs.md §3.4 + §5.1. Append-only into codex_outcome_log; idempotent
via UNIQUE(run_hash) + INSERT OR IGNORE.
"""

from __future__ import annotations

import datetime as _dt
import json
import sqlite3
import uuid

from claw_codex_mcp.db import ModeInfo, write_lock
from claw_codex_mcp.schemas import CamRecordOutcomeInput, CamRecordOutcomeOutput

INSERT_SQL = """
INSERT OR IGNORE INTO codex_outcome_log
    (id, methodology_ids, task_id, repo, outcome, evidence, run_hash, notes)
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?)
"""


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_fk_connected(conn: sqlite3.Connection, ids: list[str]) -> str | None:
    """Returns the first unknown methodology_id, or None if all are present."""
    for mid in ids:
        cur = conn.execute("SELECT 1 FROM methodologies WHERE id = ?", (mid,))
        if cur.fetchone() is None:
            return mid
    return None


async def handle_record_outcome(
    req: CamRecordOutcomeInput, info: ModeInfo,
) -> CamRecordOutcomeOutput:
    new_id = str(uuid.uuid4())
    methodology_ids_json = json.dumps(sorted(req.methodology_ids))
    evidence_json = json.dumps(req.evidence, sort_keys=True)
    ts = _now_iso()

    async with write_lock():
        conn = sqlite3.connect(info.outcome_db_path)
        try:
            conn.execute("PRAGMA busy_timeout = 5000")
            # In connected mode, FK-check the methodology_ids against the corpus.
            if info.mode in ("connected", "degraded") and info.db_path is not None:
                # Attach the corpus DB read-only for FK check.
                conn.execute(
                    f"ATTACH DATABASE 'file:{info.db_path}?mode=ro' AS corpus"
                )
                try:
                    for mid in req.methodology_ids:
                        cur = conn.execute(
                            "SELECT 1 FROM corpus.methodologies WHERE id = ?", (mid,)
                        )
                        if cur.fetchone() is None:
                            return CamRecordOutcomeOutput(
                                recorded=False,
                                corpus_status=info.corpus_status,
                                reason=f"unknown methodology_id: {mid}",
                                ts=ts,
                            )
                finally:
                    conn.execute("DETACH DATABASE corpus")

            cur = conn.execute(
                INSERT_SQL,
                (new_id, methodology_ids_json, req.task_id, req.repo,
                 req.outcome, evidence_json, req.run_hash, req.notes),
            )
            conn.commit()
            if cur.rowcount == 0:
                return CamRecordOutcomeOutput(
                    recorded=False, duplicate=True,
                    corpus_status=info.corpus_status,
                    reason="duplicate run_hash",
                    ts=ts,
                )
            return CamRecordOutcomeOutput(
                recorded=True, outcome_id=new_id, duplicate=False,
                corpus_status=info.corpus_status,
                ts=ts,
            )
        finally:
            conn.close()
```

**Step 3: Run, expect green**
Run: `pytest tests/codex_mcp/test_record_outcome.py -v`
Expected: all 4 tests **PASS**.

**Step 4: Coverage on write paths must be 100%**
```bash
pytest tests/codex_mcp/test_record_outcome.py tests/codex_mcp/test_db_connections.py \
  --cov=claw_codex_mcp.tools.record_outcome --cov=claw_codex_mcp.db \
  --cov-branch --cov-report=term-missing
```
Required: **100%** on `record_outcome.py` and on `db.py` write paths (`ensure_outcome_schema`, `write_lock`). If below 100%: add a test for the missing branch. Do not advance until 100%.

**Step 5: Commit**
```bash
git add src/claw_codex_mcp/tools/record_outcome.py tests/codex_mcp/test_record_outcome.py
git commit -m "feat(record_outcome): append-only write, idempotent run_hash, FK-check in connected mode"
```

**Gate:** Checklist 6.1, 6.2, 6.5, 6.6 closed. Validation Gate 6.1 + 6.2.

---

### Task 6.3: Update surface ceiling test to green

**Files:** Edit `src/claw_codex_mcp/server.py` to register the 4 handlers.

**Step 1: Implement server.py registration**

```python
"""MCP server registration. Hard 4-tool ceiling enforced here.

build_specs.md §3 + §10.5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from claw_codex_mcp.tools.recall import handle_recall
from claw_codex_mcp.tools.provenance import handle_provenance
from claw_codex_mcp.tools.decisions_search import handle_decisions_search
from claw_codex_mcp.tools.record_outcome import handle_record_outcome


@dataclass(frozen=True)
class ToolRegistration:
    name: str
    handler: Callable[..., Any]
    description: str


REGISTERED_TOOLS: tuple[ToolRegistration, ...] = (
    ToolRegistration(
        name="cam_recall",
        handler=handle_recall,
        description="Top-K methodologies for a natural-language query.",
    ),
    ToolRegistration(
        name="cam_provenance",
        handler=handle_provenance,
        description="Full provenance envelope for a methodology_id.",
    ),
    ToolRegistration(
        name="cam_decisions_search",
        handler=handle_decisions_search,
        description="FTS5 search across cross-repo DECISIONS.md.",
    ),
    ToolRegistration(
        name="cam_record_outcome",
        handler=handle_record_outcome,
        description="Append-only outcome log for fitness ledger.",
    ),
)

assert len(REGISTERED_TOOLS) == 4, (
    "MCP surface drift: build_specs.md §3 specifies exactly 4 tools."
)
```

**Step 2: Run the ceiling test, expect green**
Run: `pytest tests/codex_mcp/test_surface_ceiling.py -v`
Expected: **PASS**.

**Step 3: Commit**
```bash
git add src/claw_codex_mcp/server.py
git commit -m "feat(server): register 4 tools; ceiling test goes green"
```

**Gate:** Validation Gate 2.1 turns green.

---

## Phase 7 — MCP wire-up (`__main__.py` + stdio server)

### Task 7.1: MCP protocol integration test (red)

**Files:** Create `tests/codex_mcp/test_stdio_integration.py`.

**Step 1: Failing test that exercises the real `mcp` SDK over stdio**

```python
"""Real MCP stdio protocol integration. build_specs.md §10.2.

Launches `python -m claw_codex_mcp --transport stdio` as a subprocess
and sends real initialize + tools/list + tools/call requests.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

# These imports come from the official mcp SDK.
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SLICE_DB = (Path(__file__).parent.parent / "fixtures" / "claw_slice.db").resolve()


@pytest.mark.asyncio
async def test_stdio_lists_exactly_four_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(SLICE_DB))
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "claw_codex_mcp", "--transport", "stdio"],
        env={**os.environ},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert names == {
                "cam_recall", "cam_provenance",
                "cam_decisions_search", "cam_record_outcome",
            }


@pytest.mark.asyncio
async def test_stdio_recall_returns_real_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CAM_CODEX_MCP_DB_PATH", str(SLICE_DB))
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "claw_codex_mcp", "--transport", "stdio"],
        env={**os.environ},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "cam_recall", {"query": "error handling", "k": 3}
            )
            assert result.content
            # Parsed pydantic shape arrives via the SDK as a dict.
            payload = result.content[0]
            assert "results" in payload.text or hasattr(payload, "results")
```

**Step 2: Run, expect failure**
Run: `pytest tests/codex_mcp/test_stdio_integration.py -v`
Expected: server fails to start because `__main__.py` still raises `NotImplementedError`.

**Step 3: No commit yet.**

---

### Task 7.2: Implement __main__.py with stdio server

**Files:** Replace `src/claw_codex_mcp/__main__.py`.

```python
"""Entry point: python -m claw_codex_mcp --transport stdio.

build_specs.md §6 (config) + §10.2 (integration).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from claw_codex_mcp import __version__
from claw_codex_mcp.db import detect_mode
from claw_codex_mcp.server import REGISTERED_TOOLS
from claw_codex_mcp.schemas import (
    CamRecallInput, CamProvenanceInput,
    CamDecisionsSearchInput, CamRecordOutcomeInput,
)

INPUT_MODELS = {
    "cam_recall": CamRecallInput,
    "cam_provenance": CamProvenanceInput,
    "cam_decisions_search": CamDecisionsSearchInput,
    "cam_record_outcome": CamRecordOutcomeInput,
}


def _setup_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("CAM_CODEX_MCP_LOG_LEVEL", "INFO"),
        stream=sys.stderr,  # never stdout (would corrupt MCP protocol)
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


async def _serve_stdio() -> int:
    _setup_logging()
    info = detect_mode()
    sys.stderr.write(
        f"claw_codex_mcp v{__version__} mode={info.mode} "
        f"corpus={info.db_path or 'absent'} "
        f"outcome_db={info.outcome_db_path} "
        f"vec={'available' if info.vec_available else 'unavailable'}\n"
    )

    # Bootstrap outcome schema on the active outcome DB.
    from claw_codex_mcp.db import ensure_outcome_schema
    ensure_outcome_schema(info.outcome_db_path)

    server = Server("claw_codex_mcp")

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(name=t.name, description=t.description, inputSchema={"type": "object"})
            for t in REGISTERED_TOOLS
        ]

    @server.call_tool()
    async def _call(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        model = INPUT_MODELS.get(name)
        if model is None:
            return [TextContent(type="text", text=json.dumps({"error": "unknown tool"}))]
        req = model(**arguments)
        handler = next((t.handler for t in REGISTERED_TOOLS if t.name == name), None)
        if handler is None:
            return [TextContent(type="text", text=json.dumps({"error": "no handler"}))]
        out = await handler(req, info)
        return [TextContent(type="text", text=out.model_dump_json())]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            server.create_initialization_options(),
        )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="claw_codex_mcp")
    p.add_argument("--transport", choices=["stdio"], default="stdio")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args()
    if args.transport == "stdio":
        return asyncio.run(_serve_stdio())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: Smoke test the CLI**
```bash
python -m claw_codex_mcp --version
```
Expected: `0.1.0`.

**Step 3: Run integration tests**
```bash
pytest tests/codex_mcp/test_stdio_integration.py -v --timeout=30
```
Expected: both tests **PASS**. If the `mcp` SDK isn't compatible, capture the exact stderr and follow the workspace error-handling rule (5–7 hypotheses → narrow to 1–2 → log → fix).

**Step 4: Commit**
```bash
git add src/claw_codex_mcp/__main__.py tests/codex_mcp/test_stdio_integration.py
git commit -m "feat(server): stdio MCP server entrypoint; lists 4 tools; dispatches handlers"
```

**Gate:** Phase 8 prerequisite (the server boots). Approaches Validation Gate 9.6.

---

### Task 7.3: Standalone-mode integration test (Claim 6)

**Files:** Extend `tests/codex_mcp/test_stdio_integration.py`.

**Step 1: Add standalone-mode tests**

```python
@pytest.mark.asyncio
async def test_stdio_standalone_returns_honest_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CAM_CODEX_MCP_DB_PATH", raising=False)
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "claw_codex_mcp", "--transport", "stdio"],
        env={k: v for k, v in os.environ.items() if k != "CAM_CODEX_MCP_DB_PATH"},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 4

            result = await session.call_tool("cam_recall", {"query": "x"})
            text = result.content[0].text
            import json as _json
            payload = _json.loads(text)
            assert payload["results"] == []
            assert payload["corpus_status"] == "absent"
            assert payload["remediation"]
```

**Step 2: Run, expect PASS**
Run: `pytest tests/codex_mcp/test_stdio_integration.py::test_stdio_standalone_returns_honest_empty -v`
Expected: **PASS**.

**Step 3: Commit**
```bash
git add tests/codex_mcp/test_stdio_integration.py
git commit -m "test(integration): standalone-mode stdio returns honest empty recall"
```

**Gate:** Validation Gate 9.6.

---

## Phase 8 — Codex CLI wiring

### Task 8.1: Append `[mcp_servers.cam_cam]` to `.codex/config.toml`

**Files:** Edit `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml`.

**Step 1: Check current state**
```bash
grep -n '\[mcp_servers' /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/config.toml
```
Expected: one match — `[mcp_servers.context7]` near line 276.

**Step 2: Resolve absolute python path**
```bash
which python
# Note this path; you'll use it instead of bare "python" in the TOML block.
```

**Step 3: Append the standalone-mode TOML block first** (safer; needs no CAM_CAM)
```toml

[mcp_servers.cam_cam]
command = "/absolute/path/to/python"
args = ["-m", "claw_codex_mcp", "--transport", "stdio"]
env = { CAM_CODEX_MCP_AUTH_TOKEN = "${CAM_CODEX_MCP_AUTH_TOKEN}" }
# CAM_CODEX_MCP_DB_PATH omitted → standalone mode
```

**Step 4: Verify the block is appended (no other lines changed)**
```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx && git diff .codex/config.toml | head -20
```
(If `.codex/` is not under any git repo, just diff against a backup copy you made first.)
Expected: only additive lines around the existing `[mcp_servers.context7]` block.

**Step 5: Smoke test — Codex sees 4 tools**
```bash
codex tools list --mcp cam_cam 2>&1 | head
```
Expected: 4 tool names. (Exact command depends on the Codex CLI version pinned in `baselines/manifest.json`.)

**Step 6: Do NOT modify `.codex/rules/default.rules`**
```bash
git -C /Volumes/WS4TB/WS4TBr/CAM_Codx diff --name-only 2>/dev/null
```
Confirm `default.rules` is not in the diff.

**Step 7: No commit in this repo** — `.codex/` lives outside it. Record the change in `meta/HANDOFF_LATEST.md` under "State changes outside the repo" so it survives the session.

**Gate:** Checklist 8.1 + 8.2 + 8.3 closed. Validation Gate 8.1 + 8.2.

---

### Task 8.2: Append `.codex/AGENTS.md` doctrine section

**Files:** Edit `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md`.

**Step 1: Confirm current state**

Check the current Core Rule (was already edited mid-session). Confirm the file ends with the four-clause Core Rule:
> Codex decides. Tests arbitrate. Markdown remembers. CAM librarian cites.

**Step 2: Append the `CAM Librarian Doctrine` section verbatim from `build_specs.md` §7**

Append the exact text shown in build_specs.md §7 (the `## CAM Librarian Doctrine` heading through the Updated Core Rule).

**Step 3: Verify markdown integrity**
```bash
python3 -c "
import re
text = open('/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/AGENTS.md').read()
# Doctrine line must NOT be inside a fenced code block.
fences = re.findall(r'```[^`]*```', text, flags=re.DOTALL)
for f in fences:
    assert 'Codex decides. Tests arbitrate. Markdown remembers. CAM librarian cites.' not in f, \
        'doctrine accidentally fenced'
print('doctrine integrity OK')
"
```
Expected: `doctrine integrity OK`.

**Step 4: No commit** — outside this repo.

**Gate:** Checklist 7.1 + 7.2 closed. Validation Gate 7.1 + 7.2.

---

## Phase 9 — Skills

### Task 9.1: Skill frontmatter validation harness

**Files:** Confirm `tools/validate_skill_frontmatter.py` (written in Phase 0) works against an example SKILL.md.

**Step 1: Run validator on existing skills**
```bash
python3 tools/validate_skill_frontmatter.py --dir /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills
```
Expected: zero failures on skills without `auto_fire` blocks; skills with malformed `auto_fire` would fail.

**Step 2: No commit** if everything passes.

**Gate:** Skill-creation prerequisite from `build_to_do_checklist.md` Phase 4 prerequisites.

---

### Task 9.2: Create `cam_recall_and_cite/SKILL.md`

**Files:** Create `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/cam_recall_and_cite/SKILL.md`.

**Step 1: Write the skill**

Use `build_specs.md` §4.1 verbatim for the frontmatter, MCP-call table, required output template, and self-check rule.

**Step 2: Validate frontmatter**
```bash
python3 tools/validate_skill_frontmatter.py \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/cam_recall_and_cite/SKILL.md
```
Expected: PASS.

**Step 3: No commit** — `.codex/skills/` is outside this repo. Record the file path in `meta/HANDOFF_LATEST.md` "State changes outside the repo."

**Gate:** Checklist 4.1 closed. Validation Gate 4.1.

---

### Task 9.3: Modify `repo_recon/SKILL.md`

**Files:** Edit `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/repo_recon/SKILL.md`.

**Step 1: Insert the new section**

Apply the additive change described in `build_specs.md` §4.4: insert the "Recall prior decisions" section after the existing "Inspect" section, before "REPO_MAP.md Format".

**Step 2: Verify prior behavior preserved**
```bash
grep -c '^## ' /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/repo_recon/SKILL.md
```
Expected: previous section count + 1 (the new "Recall prior decisions").

**Step 3: No commit** — outside this repo.

**Gate:** Checklist 4.2 closed. Validation Gate 4.3.

---

### Task 9.4: Rewrite `deepscientist-data-research/SKILL.md`

**Files:** Edit `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/deepscientist-data-research/SKILL.md`.

**Step 1: Apply the line-keyed replacements from `build_specs.md` §4.5**

Replace lines 65, 135, 162 per the spec table. No back-compat shim. Confirm by running:
```bash
grep -n 'claw_query_memory\|claw_store_finding' \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/deepscientist-data-research/SKILL.md
```
Expected: zero hits.

**Step 2: Sweep the entire skills tree**
```bash
grep -rln 'claw_query_memory\|claw_store_finding' \
  /Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/
```
Expected: zero hits anywhere.

**Step 3: No commit** — outside this repo.

**Gate:** Checklist 4.3 closed. Validation Gate 4.2 + 4.4. CC.3 cross-cutting now green.

---

### Task 9.5: Create `rescue_ladder/SKILL.md`

**Files:** Create `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/rescue_ladder/SKILL.md`.

**Step 1: Write the skill verbatim from `build_specs.md` §4.2**

**Step 2: Validate frontmatter**

**Step 3: No commit** — outside this repo.

**Gate:** Checklist 5.1 closed. Validation Gate 5.1.

---

### Task 9.6: Create `outcome_log/SKILL.md` (centerpiece)

**Files:** Create `/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex/skills/outcome_log/SKILL.md`.

**Step 1: Write the skill verbatim from `build_specs.md` §4.3**

**Step 2: Validate frontmatter**

**Step 3: No commit** — outside this repo.

**Gate:** Checklist 6.3 closed. Validation Gate 6.3.

---

## Phase 10 — End-to-end + final gates

### Task 10.1: Provenance gate (Claim 2)

**Step 1: Real session against the slice DB**

Run a Codex session against any trusted workspace repo with `CAM_CODEX_MCP_DB_PATH` pointing at `tests/fixtures/claw_slice.db`. Ask Codex to do something pattern-shaped ("add rate limiting to the recommendation API"). Watch for a `## Retrieved Methodologies` block in `IMPLEMENT.md`.

**Step 2: Verify every cited id resolves**
For each `pattern_id` listed in the IMPLEMENT.md block:
```bash
sqlite3 tests/fixtures/claw_slice.db "SELECT id FROM methodologies WHERE id = '<id>'"
```
Expected: every id resolves to a real row. 100% required.

**Gate:** Validation Gate 9.1.

---

### Task 10.2: Lightness gate (Claim 5)

**Step 1: Measure new server peak RSS**
```bash
/usr/bin/time -l python -m claw_codex_mcp --transport stdio </dev/null \
  2> baselines/new_mcp_rss.txt
```
(Server will exit on EOF; that's fine.)

**Step 2: Compare to legacy baseline**
```bash
python3 - <<'EOF'
import re
def rss(path: str) -> int:
    with open(path) as f:
        for line in f:
            m = re.match(r'\s*(\d+)\s+maximum resident set size', line)
            if m:
                return int(m.group(1))
    raise SystemExit(f"no RSS line in {path}")
legacy = rss("baselines/legacy_mcp_rss.txt")
new = rss("baselines/new_mcp_rss.txt")
ratio = new / legacy
print(f"legacy={legacy} new={new} ratio={ratio:.3f}")
assert ratio <= 0.50, f"lightness target exceeded: {ratio:.3f} > 0.50"
EOF
```
Expected: ratio ≤ 0.50 (target) or 0.50–0.65 with user-approved waiver in `docs/_coverage_gaps.md`.

**Gate:** Validation Gate 9.2.

---

### Task 10.3: Standalone E2E (Claim 6)

**Step 1: Fresh clone, no CAM_CAM**

In a scratch directory:
```bash
mkdir /tmp/cam_codex_test && cd /tmp/cam_codex_test
git clone https://github.com/deesatzed/CAM_Codx.git
cd CAM_Codx
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
unset CAM_CODEX_MCP_DB_PATH
python -m claw_codex_mcp --version
python -m claw_codex_mcp --transport stdio </dev/null
```
Expected: stderr line `mode=standalone corpus=absent`, then EOF exit.

**Step 2: Real Codex session, exercise all 4 tools, verify standalone behavior**

Run a real Codex session against a trusted workspace repo with the standalone TOML block from §6. Confirm:
- `cam_recall` returns `{results: [], corpus_status: "absent", remediation: ...}` for any query
- `cam_decisions_search` returns real hits from your `DECISIONS.md` files
- `cam_record_outcome` writes a row to `~/.cam_codex_mcp/codex_outcome_log.db`

```bash
sqlite3 ~/.cam_codex_mcp/codex_outcome_log.db "SELECT outcome, run_hash FROM codex_outcome_log LIMIT 5"
```
Expected: at least one row from the test session.

**Gate:** Validation Gate 9.6. Claim 6 closed.

---

### Task 10.4: Update HANDOFF + close out

**Files:** Edit `meta/HANDOFF_2026-05-17.md` (or write `meta/HANDOFF_<today>.md` if you want a new dated snapshot).

**Step 1: Record final state**
- All 10 phases complete
- All validation gates that ran: list each with PASS/PARTIAL/WAIVER status
- Outstanding waivers from `docs/_coverage_gaps.md`
- v2 deferred items (cam_match_failure, HTTP/SSE, federation, dashboards)
- The `.codex/` edits that live outside this repo (config.toml, AGENTS.md, 4 SKILL.md files)

**Step 2: Verify no "production ready" / "complete" anywhere**
```bash
grep -rni '\bproduction[ -]ready\b' README.md PRD.md build_specs.md \
  build_to_do_checklist.md docs/ meta/ | grep -v 'no .production\|never claim'
```
Expected: zero hits. (Hits inside negations are fine.)

**Step 3: Commit and push**
```bash
git add meta/ docs/_coverage_gaps.md  # if it has content
git commit -m "docs(handoff): record final state, outstanding waivers, v2 deferred items"
git push
```

**Gate:** Checklist 10.1 + 10.2 + 10.3 + 10.4 closed.

---

## Cross-cutting gates (run continuously)

These gates run on **every commit** via CI (set up in a future task), and must remain green throughout the entire build:

| Gate | Source | Mitigation if violated |
|---|---|---|
| CC.1 — 4-tool ceiling | `test_surface_ceiling.py` | Adding a tool requires a `build_specs.md` §3 amendment first |
| CC.2 — Append-only ledger | sqlite trigger or test-only audit on UPDATE/DELETE | Fix the violating write path; do not loosen the gate |
| CC.3 — No phantom MCP refs | `grep -rln 'claw_query_memory\|claw_store_finding' .codex/skills/` returns empty | Replace with `cam_*` equivalents |
| CC.4 — Auto-fire trigger schema | `tools/validate_skill_frontmatter.py` exits 0 | Fix the malformed frontmatter |
| CC.5 — No-mock detector | `grep -rEi 'mock\|stub\|fake\|simulate\|placeholder\|cached_response\|demo' src/` flags hits for human review | Each hit gets an explicit waiver in `docs/_decision_log.md` or is removed |
| CC.6 — Coverage ≥90% (overall), 100% on db.py writes | `pytest --cov-fail-under=90` | Add tests or mark `# pragma: no cover` with `# why:` |
| CC.7 — Provenance integrity | `corpus_status` present in every output schema | Update schemas to add the field |
| CC.8 — Doctrine integrity | Doctrine line outside any fenced code block | Move text out of code fence |

---

## Notes on running this plan

- **Worktree:** This plan was written outside a git worktree. If executing via the subagent-driven flow, **create a worktree first** so the implementation can be safely abandoned without polluting `main`:
  ```bash
  git worktree add /tmp/cam-codex-impl -b feature/initial-impl
  ```

- **Codex CLI version pinning:** The integration tests assume `codex` is on `PATH`. Capture the exact version in `baselines/manifest.json` before Phase 7. If the Codex CLI updates mid-build, the trace regexes in `tools/codex_trace_patterns.py` may need re-tuning — that's an explicit risk surfaced in the harness's own README.

- **Real LLM calls in E2E:** Phase 10 tasks 10.1, 10.3 use real Codex CLI sessions. Per workspace policy: real calls only. Budget caps live in CAM_CAM's `claw.toml` if connected mode is exercised; pin them before starting.

- **Failure surfacing:** If any test fails repeatedly (≥2 times in a row), invoke the workspace error-handling rule: reflect on 5–7 hypothetical sources, narrow to 1–2 most likely, add a validation log line, then attempt a fix. Do not loop.

- **Out of scope for this plan:** Implementing `cam_match_failure`, HTTP/SSE transport, federation, dashboards, secrets rotation in `.codex/rules/default.rules`, modifying CAM_CAM. All v2 deferred.

---

## References

- `PRD.md` — F-MCP-01..F-MCP-13, Claims 0–6
- `build_specs.md` §1–§13
- `build_to_do_checklist.md` Phase 0–10
- `docs/_validation_gates.md` Gates 1.1–9.6, CC.1–CC.8
- `README.md` — front door, two-mode operation
- `meta/HANDOFF_LATEST.md` — session context, verified facts, locked decisions
