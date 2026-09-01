# MONID Evidence Broker Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CAM_Codx-managed, policy-gated MONID evidence broker that acquires, caches, reuses, and receipts public external evidence for a bounded task.

**Architecture:** A new `tools/monid_evidence_broker.py` owns typed policy, request, cache, receipt, and CLI boundaries. `cam_control_plane.py` may report an evidence gap and cache disposition but cannot run MONID implicitly. Raw artifacts reside in a caller-provided secure state directory; normalized packets are redacted and distinguish observations from inference.

**Tech Stack:** Python standard library, pytest, existing CAM_Codx capability contract/manager, installed MONID CLI.

---

### Task 1: Define policy, request, and receipt types

**Files:**
- Create: `tools/monid_evidence_broker.py`
- Create: `tests/test_monid_evidence_broker.py`

**Step 1: Write the failing test**

```python
def test_policy_requires_finite_task_budget_and_freshness() -> None:
    with pytest.raises(EvidencePolicyError, match="task_budget_usd"):
        EvidencePolicy(task_budget_usd=float("nan"), freshness_seconds=3600)
    with pytest.raises(EvidencePolicyError, match="freshness_seconds"):
        EvidencePolicy(task_budget_usd=1.0, freshness_seconds=0)
```

Add rejection cases for empty task ID/question, empty allowed-source set, and
prohibited data classes requested by the task.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest -q tests/test_monid_evidence_broker.py -k policy`

Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Create frozen `EvidencePolicy`, `EvidenceRequest`, `EvidenceReceipt`, and
`EvidencePacket` dataclasses plus `EvidencePolicyError`. Validate finite,
non-negative task budgets; positive freshness; nonempty source policy; explicit
retention class; and explicit prohibited data classes. Give packets a redacted
public serializer that never contains secrets or raw data.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest -q tests/test_monid_evidence_broker.py -k policy`

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/monid_evidence_broker.py tests/test_monid_evidence_broker.py
git commit -m "feat: define MONID evidence policy"
```

### Task 2: Add content-addressed local cache and policy-compatible reuse

**Files:**
- Modify: `tools/monid_evidence_broker.py`
- Modify: `tests/test_monid_evidence_broker.py`

**Step 1: Write the failing test**

```python
def test_compatible_fresh_cache_hit_skips_external_runner(tmp_path: Path) -> None:
    broker = EvidenceBroker(tmp_path / "state", runner=FailIfCalledRunner())
    stored = broker.store_completed_result(request, raw_result={"status": "ok"}, cost_usd=0.12)
    packet = broker.resolve(request)
    assert packet.cache_status == "hit"
    assert packet.raw_sha256 == stored.raw_sha256
```

Add controls proving an expired entry, altered parameters, incompatible
retention class/source policy, or a quarantined entry cannot be reused.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest -q tests/test_monid_evidence_broker.py -k cache`

Expected: FAIL because caching does not exist.

**Step 3: Write minimal implementation**

Canonicalize JSON and hash it with SHA-256. Store raw JSON and receipts below
the supplied `state_dir` using owner-only permissions; reject path traversal.
Index by evidence-question and parameter fingerprints, but decide reuse only
after checking policy compatibility, quarantine state, invalidation, and the
new task freshness rule. Preserve original collection timestamp/cost and write
a zero-cost reuse receipt for the new task.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest -q tests/test_monid_evidence_broker.py -k cache`

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/monid_evidence_broker.py tests/test_monid_evidence_broker.py
git commit -m "feat: cache MONID evidence safely"
```

### Task 3: Implement discover-inspect-run with budget gates

**Files:**
- Modify: `tools/monid_evidence_broker.py`
- Modify: `tests/test_monid_evidence_broker.py`

**Step 1: Write the failing test**

```python
def test_cache_miss_discovers_then_inspects_before_running() -> None:
    packet = EvidenceBroker(state_dir, runner=recording_runner).resolve(request)
    assert [call[:2] for call in recording_runner.calls] == [
        ("monid", "discover"), ("monid", "inspect"), ("monid", "run")
    ]
```

Add tests for unavailable or forbidden endpoints, malformed JSON, unknown
price, schema mismatch, and blocked spend before `run`.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest -q tests/test_monid_evidence_broker.py -k execution`

Expected: FAIL because no runner exists.

**Step 3: Write minimal implementation**

Use an injected list-form runner protocol. Construct `monid discover -j`,
`monid inspect -j`, and `monid run -j` with no shell. Select only
policy-allowed endpoints; use health only to break a valid tie. Require the
inspected schema before forming body/query/path input, check remaining task
budget before `run`, and retain sanitized failure receipts as non-positive
evidence.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. pytest -q tests/test_monid_evidence_broker.py -k execution`

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/monid_evidence_broker.py tests/test_monid_evidence_broker.py
git commit -m "feat: execute bounded MONID evidence requests"
```

### Task 4: Wire read-only CAM_Codx planning and document the proof gate

**Files:**
- Modify: `tools/cam_control_plane.py`
- Modify: `tests/test_cam_control_plane.py`
- Modify: `tools/README.md`
- Modify: `tests/test_cam_codx_skill.py`
- Modify: `PROGRESS.md`

**Step 1: Write the failing test**

```python
def test_assessment_plan_reports_evidence_gap_without_execution(tmp_path: Path) -> None:
    result = plan_control_plane(request_with_evidence_question, registry=registry)
    assert result.external_evidence.status == "cache_miss"
    assert result.operation_executed is False
```

Add a live-proof test asserting the run is skipped unless explicit bounded
provider, cost, and data-scope authorization is supplied.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. pytest -q tests/test_cam_control_plane.py tests/test_cam_codx_skill.py -k evidence`

Expected: FAIL because the control plane does not model external evidence.

**Step 3: Write minimal implementation**

Extend control-plane request/result types with an optional evidence need and
read-only cache disposition. Do not add MONID as a CAM_CAM command. Document
that dedicated tools take precedence, MONID observations are untrusted, and
`show evidence`, `reuse only`, `refresh`, and `do not retain` are user
controls. Gate any real paid endpoint test behind explicit opt-in and record
only its receipt-backed status in `PROGRESS.md`.

**Step 4: Run verification**

Run: `PYTHONPATH=. pytest -q tests/test_monid_evidence_broker.py tests/test_cam_control_plane.py tests/test_cam_manager.py tests/test_cam_codx_skill.py && python -m ruff check tools/monid_evidence_broker.py tools/cam_control_plane.py tests/test_monid_evidence_broker.py tests/test_cam_control_plane.py && git diff --check`

Expected: PASS; a live MONID run remains skipped unless separately authorized.

**Step 5: Commit**

```bash
git add tools/monid_evidence_broker.py tests/test_monid_evidence_broker.py tools/cam_control_plane.py tests/test_cam_control_plane.py tools/README.md tests/test_cam_codx_skill.py PROGRESS.md
git commit -m "feat: route MONID evidence through CAM_Codx"
```
