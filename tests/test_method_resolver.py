import importlib.util
import json
from dataclasses import replace
from pathlib import Path
import re
import sys

import pytest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "method_resolver.py"

C01_PUBLIC_TASK = """Create `solution.py` with a `WorkflowRunner` class. Its constructor accepts a
checkpoint path, a list of step dictionaries (`id` and `dependencies`), a
mapping of step IDs to callables, an optional retry limit, and an optional
sleep callable. `run()` returns serializable workflow state.

The runner must respect dependencies, persist completed work, resume after an
abrupt interruption without repeating completed handlers, apply bounded
backoff retries to ordinary exceptions, and fail closed on malformed or
incompatible checkpoint state."""

C07_PUBLIC_TASK = """Create `solution.py` with `AutonomyLevel`, `ActionTracker`, and
`SecurityPolicy`. The tracker is a deterministic sliding-window counter and
accepts an injectable clock. The policy must enforce read-only autonomy,
separator-aware command allowlisting across the entire command, denial of
substitutions/backticks/redirection, lexical traversal checks, workspace
containment, an explicit resolved-path gate for symlink-safe callers, action
rate limiting, and a sanitized subprocess environment.

The path API must make the two-stage check available: a lexical precheck is
not sufficient proof that a symlink target remains inside the workspace."""

C11_PUBLIC_TASK = """Create `solution.py` with `FlightRecorder` and `validate_trace_integrity`.
Record events with deterministic IDs, canonical payload hashes, a previous
event hash, and an event hash. Build a trace whose hash commits to the ordered
event hashes. Accept an injectable timestamp callable for deterministic use.

Validation must recompute every layer and return a structured valid/invalid
result that detects payload edits, event deletion or reordering, previous-hash
tampering, and trace-hash tampering."""

C26_PUBLIC_TASK = """Create `solution.py` with `collect_runtime_metadata`. It receives a harness
name plus explicit runtime values and injected probe callables, and returns a
JSON-safe metadata mapping for a reproducible run receipt.

The result must distinguish an explicitly configured container engine from
automatic selection, normalize the Python version to its first whitespace-
delimited token, retain the platform and image references, and report stable
IDs for images that are actually used. Human harness runs have no harness
image. Probes must be lazy: do not resolve or inspect a harness image when the
harness is `human`, and do not call any probe more often than necessary."""

C31_PUBLIC_TASK = """Create `solution.py` with async-generator `sanitize_tool_responses`. It receives
tool keyword arguments, an async next-handler, and a sanitizer. Iterate every
response produced by the handler and yield it in original order.

For responses with content blocks, sanitize string-valued `text`. Mutate a
block only when sanitization changes its text. Missing, empty, non-text, and
already-safe content must pass through unchanged, and no response may be
dropped."""


def _load_resolver():
    assert MODULE_PATH.is_file(), "method resolver module is missing"
    spec = importlib.util.spec_from_file_location("method_resolver", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _kinds(result) -> set[str]:
    return {obligation.kind.value for obligation in result.obligations}


def test_public_tasks_emit_typed_method_obligations_from_exact_spans() -> None:
    resolver = _load_resolver()

    cases = (
        (C01_PUBLIC_TASK, {"invariant", "failure", "recovery", "order", "persistence"}),
        (C07_PUBLIC_TASK, {"invariant", "safety", "verification"}),
        (C11_PUBLIC_TASK, {"invariant", "failure", "order", "verification"}),
        (C26_PUBLIC_TASK, {"invariant", "safety", "order"}),
        (C31_PUBLIC_TASK, {"invariant", "safety", "order"}),
    )

    for task_text, expected_kinds in cases:
        result = resolver.decompose_task(task_text)

        assert result.task_text == task_text
        assert expected_kinds <= _kinds(result)
        assert all(isinstance(item, resolver.TaskObligation) for item in result.obligations)
        assert all(task_text[item.span_start : item.span_end] == item.task_span for item in result.obligations)
        assert all(item.task_span for item in result.obligations)
        assert all(item.discriminative_terms for item in result.obligations)
        assert len({item.obligation_id for item in result.obligations}) == len(result.obligations)


def test_generic_novel_cues_cover_every_obligation_kind() -> None:
    resolver = _load_resolver()
    task = (
        "Always preserve the aurora mask. "
        "If an invalid prism fails, report the error. "
        "Retry after failure and restore the prior state. "
        "Sanitize secrets and keep paths inside the workspace. "
        "First scan, then render, and finally publish. "
        "Persist the result atomically in a durable checkpoint. "
        "Verify the digest and assert the receipt matches. "
        "Use the current Nebula SDK API version."
    )

    result = resolver.decompose_task(task)

    assert _kinds(result) == {
        "invariant",
        "failure",
        "recovery",
        "safety",
        "order",
        "persistence",
        "verification",
        "current_api",
    }


def test_internal_api_name_and_runtime_version_do_not_invent_current_api_need() -> None:
    resolver = _load_resolver()
    task = "Expose a path API. Normalize the supplied Python version."

    result = resolver.decompose_task(task)

    assert "current_api" not in _kinds(result)


def test_lunar_shader_negative_control_stays_unresolved() -> None:
    resolver = _load_resolver()
    task = "Tune the lunar shader so crater rims look pearlescent."

    result = resolver.decompose_task(task)

    assert result.task_text == task
    assert len(result.obligations) == 1
    assert result.obligations[0].kind is resolver.ObligationKind.UNRESOLVED
    assert result.obligations[0].task_span == task
    assert result.obligations[0].required is True


def test_optional_unknown_span_is_preserved_but_not_required() -> None:
    resolver = _load_resolver()
    task = "Optionally tint the aurora mauve."

    result = resolver.decompose_task(task)

    assert len(result.obligations) == 1
    assert result.obligations[0].kind is resolver.ObligationKind.UNRESOLVED
    assert result.obligations[0].required is False


@pytest.mark.parametrize(
    "task",
    (
        "Reuse the algorithm from donor repository MoonShade.",
        "Copy repository LunarFlow's recovery method.",
        "Implement C01 using its hidden tests.",
        "Follow https://github.com/example/private-donor for persistence.",
    ),
)
def test_donor_case_and_hidden_test_injection_is_rejected(task: str) -> None:
    resolver = _load_resolver()

    with pytest.raises(resolver.TaskDecompositionError, match="leakage"):
        resolver.decompose_task(task)


def test_donor_name_only_attribution_is_rejected_before_serialization() -> None:
    resolver = _load_resolver()
    task = "Reuse MoonShade's recovery method."

    with pytest.raises(resolver.TaskDecompositionError, match="leakage"):
        resolver.decompose_task(task)


def test_serializer_rejects_forged_donor_identity() -> None:
    resolver = _load_resolver()
    clean = resolver.decompose_task("Persist the checkpoint.")
    forged_obligation = replace(
        clean.obligations[0],
        discriminative_terms=("moonshade", "checkpoint"),
    )
    forged = replace(clean, obligations=(forged_obligation,))

    with pytest.raises(resolver.TaskDecompositionError, match="canonical"):
        resolver.serialize_resolution(forged)


def test_mixed_known_and_unknown_clauses_keep_separate_exact_spans() -> None:
    resolver = _load_resolver()
    task = "Persist the checkpoint and tint the lunar shader mauve."

    result = resolver.decompose_task(task)
    persistence = [item for item in result.obligations if item.kind.value == "persistence"]
    unresolved = [item for item in result.obligations if item.kind.value == "unresolved"]

    assert [item.task_span for item in persistence] == ["Persist the checkpoint"]
    assert [item.task_span for item in unresolved] == ["tint the lunar shader mauve."]
    assert all(task[item.span_start : item.span_end] == item.task_span for item in result.obligations)


def test_incidental_state_word_does_not_hallucinate_persistence() -> None:
    resolver = _load_resolver()
    task = "Tune the lunar shader state until crater rims look pearlescent."

    result = resolver.decompose_task(task)

    assert [item.kind.value for item in result.obligations] == ["unresolved"]
    assert result.obligations[0].task_span == task


def test_ordinary_repository_language_is_not_mistaken_for_donor_leakage() -> None:
    resolver = _load_resolver()
    task = "Validate the repository root remains inside the workspace."

    result = resolver.decompose_task(task)

    assert {"invariant", "safety", "verification"} <= _kinds(result)


def test_public_output_has_no_case_donor_or_hidden_test_leakage() -> None:
    resolver = _load_resolver()

    for task in (C01_PUBLIC_TASK, C07_PUBLIC_TASK, C11_PUBLIC_TASK, C26_PUBLIC_TASK):
        output = resolver.serialize_resolution(resolver.decompose_task(task)).decode("utf-8")
        lowered = output.lower()
        assert "donor" not in lowered
        assert "hidden test" not in lowered
        assert "held-out" not in lowered
        assert re.search(r"(?<![a-z0-9])[cn]\d{2}(?![a-z0-9])", lowered) is None


def test_serialized_resolution_is_canonical_and_byte_identical() -> None:
    resolver = _load_resolver()

    first = resolver.serialize_resolution(resolver.decompose_task(C01_PUBLIC_TASK))
    second = resolver.serialize_resolution(resolver.decompose_task(C01_PUBLIC_TASK))
    decoded = json.loads(first)

    assert first == second
    assert first == json.dumps(
        decoded, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    assert decoded["schema_version"] == 1
    assert decoded["task_text"] == C01_PUBLIC_TASK


def test_obligation_order_and_ids_are_stable() -> None:
    resolver = _load_resolver()
    task = "First persist the state. Then verify the saved digest."

    first = resolver.decompose_task(task)
    second = resolver.decompose_task(task)

    assert first == second
    assert tuple(item.obligation_id for item in first.obligations) == tuple(
        item.obligation_id for item in second.obligations
    )
    assert [(item.span_start, item.kind.value) for item in first.obligations] == sorted(
        (item.span_start, item.kind.value) for item in first.obligations
    )


@pytest.mark.parametrize("task", (None, b"persist state", 1, True, "", "   \n"))
def test_invalid_task_types_and_empty_tasks_fail_closed(task: object) -> None:
    resolver = _load_resolver()

    with pytest.raises(resolver.TaskDecompositionError):
        resolver.decompose_task(task)


def test_task_and_span_counts_are_bounded() -> None:
    resolver = _load_resolver()

    with pytest.raises(resolver.TaskDecompositionError, match="byte limit"):
        resolver.decompose_task("x" * (resolver.MAX_TASK_BYTES + 1))
    with pytest.raises(resolver.TaskDecompositionError, match="span limit"):
        resolver.decompose_task(". ".join("persist state" for _ in range(resolver.MAX_TASK_SPANS + 1)))
