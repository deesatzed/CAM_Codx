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


@pytest.mark.parametrize(
    "mutation",
    (
        "schema_bool",
        "schema_float",
        "task_text_subclass",
        "task_text_int",
        "obligations_list",
        "obligations_string",
        "obligation_id_subclass",
        "obligation_id_int",
        "kind_string",
        "task_span_subclass",
        "task_span_int",
        "span_start_float",
        "span_start_bool",
        "span_end_float",
        "span_end_bool",
        "terms_list",
        "terms_string",
        "term_subclass",
        "term_bool",
        "term_int",
        "required_int",
        "required_string",
        "resolution_subclass",
        "obligation_subclass",
    ),
)
def test_serializer_recursively_requires_exact_frozen_types(mutation: str) -> None:
    resolver = _load_resolver()
    clean = resolver.decompose_task("Persist the checkpoint.")
    obligation = clean.obligations[0]

    class TextSubclass(str):
        pass

    class ResolutionSubclass(resolver.TaskResolution):
        pass

    class ObligationSubclass(resolver.TaskObligation):
        pass

    if mutation == "schema_bool":
        forged = replace(clean, schema_version=True)
    elif mutation == "schema_float":
        forged = replace(clean, schema_version=1.0)
    elif mutation == "task_text_subclass":
        forged = replace(clean, task_text=TextSubclass(clean.task_text))
    elif mutation == "task_text_int":
        forged = replace(clean, task_text=1)
    elif mutation == "obligations_list":
        forged = replace(clean, obligations=list(clean.obligations))
    elif mutation == "obligations_string":
        forged = replace(clean, obligations="persistence")
    elif mutation == "obligation_id_subclass":
        forged_item = replace(
            obligation, obligation_id=TextSubclass(obligation.obligation_id)
        )
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "obligation_id_int":
        forged_item = replace(obligation, obligation_id=1)
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "kind_string":
        forged_item = replace(obligation, kind=obligation.kind.value)
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "task_span_subclass":
        forged_item = replace(obligation, task_span=TextSubclass(obligation.task_span))
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "task_span_int":
        forged_item = replace(obligation, task_span=1)
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "span_start_float":
        forged_item = replace(obligation, span_start=float(obligation.span_start))
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "span_start_bool":
        forged_item = replace(obligation, span_start=False)
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "span_end_float":
        forged_item = replace(obligation, span_end=float(obligation.span_end))
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "span_end_bool":
        forged_item = replace(obligation, span_end=True)
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "terms_list":
        forged_item = replace(
            obligation, discriminative_terms=list(obligation.discriminative_terms)
        )
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "terms_string":
        forged_item = replace(obligation, discriminative_terms="checkpoint")
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "term_subclass":
        forged_item = replace(
            obligation,
            discriminative_terms=(
                TextSubclass(obligation.discriminative_terms[0]),
                *obligation.discriminative_terms[1:],
            ),
        )
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "term_bool":
        forged_item = replace(obligation, discriminative_terms=(True,))
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "term_int":
        forged_item = replace(obligation, discriminative_terms=(1,))
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "required_int":
        forged_item = replace(obligation, required=1)
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "required_string":
        forged_item = replace(obligation, required="true")
        forged = replace(clean, obligations=(forged_item,))
    elif mutation == "resolution_subclass":
        forged = ResolutionSubclass(**clean.__dict__)
    elif mutation == "obligation_subclass":
        forged_item = ObligationSubclass(**obligation.__dict__)
        forged = replace(clean, obligations=(forged_item,))
    else:  # pragma: no cover - the parameter list is closed above
        raise AssertionError(mutation)

    with pytest.raises(resolver.TaskDecompositionError, match="canonical"):
        resolver.serialize_resolution(forged)


@pytest.mark.parametrize(
    "task",
    (
        "Use ZephyrWorks's recovery method.",
        "Apply ZephyrWorks’s retry pattern.",
        "Reuse the recovery method from ZephyrWorks.",
        "Adopt AtlasForge's validation algorithm.",
        "Follow the persistence pattern from OrionKit.",
    ),
)
def test_structural_source_attribution_variants_are_rejected(task: str) -> None:
    resolver = _load_resolver()

    with pytest.raises(resolver.TaskDecompositionError, match="leakage"):
        resolver.decompose_task(task)


@pytest.mark.parametrize(
    "task",
    (
        "Borrow QuasarForge's recovery approach.",
        "Borrow Quasar.Forge's recovery method.",
        "Borrow quasar_forge's recovery method.",
        "Borrow quasar-forge's recovery method.",
        "Borrow QuasarForge's Recovery Strategy.",
        "Borrow ＱｕａｓａｒＦｏｒｇｅ＇ｓ Recovery Strategy.",
        "Port QuasarForge’s retry strategy.",
        "Implement QuasarForge's failure algorithm.",
        "Review Quasar Forge's persistence implementation.",
        "Review QuasarForge team's recovery strategy.",
        "Review Quasar Forge team's recovery strategy.",
        "QuasarForge's recovery pattern must be followed.",
        "Port the recovery approach from QuasarForge.",
        "Apply the retry strategy by Quasar Forge.",
        "Implement the algorithm according to QuasarForge.",
    ),
)
def test_proper_source_attribution_rejects_without_leading_verb_dependency(task: str) -> None:
    resolver = _load_resolver()

    with pytest.raises(resolver.TaskDecompositionError, match="leakage"):
        resolver.decompose_task(task)


@pytest.mark.parametrize(
    "task",
    (
        "Preserve the runner's state.",
        "Use the caller's retry strategy.",
        "Validate the method's return value.",
        "Compute the strategy from the task description.",
        "Apply the method according to the current specification.",
    ),
)
def test_generic_possessives_and_unattributed_sources_remain_valid(task: str) -> None:
    resolver = _load_resolver()

    assert resolver.decompose_task(task).task_text == task


@pytest.mark.parametrize(
    "task",
    (
        "Implement C-01.",
        "Implement c_01.",
        "Implement C.01.",
        "Implement C 01.",
        "Implement N-07.",
        "Implement n_07.",
        "Implement N.07.",
        "Implement Ｃ－０１.",
        "Use hidden_tests.",
        "Use hidden‐tests.",
        "Use hidden.tests.",
        "Use HiddenTests.",
        "Use hiddenTests.",
        "Read held_out evidence.",
        "Read held.out evidence.",
        "Read HeldOut evidence.",
        "Read heldOut evidence.",
    ),
)
def test_leakage_seals_normalize_case_unicode_and_separators(task: str) -> None:
    resolver = _load_resolver()

    with pytest.raises(resolver.TaskDecompositionError, match="leakage"):
        resolver.decompose_task(task)


@pytest.mark.parametrize(
    "task",
    (
        "Handle hidden testability details.",
        "Use a held outcome value.",
        "Render C-010 palette entries.",
        "Use N.7 neighbors.",
    ),
)
def test_normalized_leakage_seals_do_not_overmatch_words_or_numbers(task: str) -> None:
    resolver = _load_resolver()

    assert resolver.decompose_task(task).task_text == task


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


def test_noun_coordination_is_not_split_into_false_unresolved_clause() -> None:
    resolver = _load_resolver()
    task = "Persist checkpoints for red and blue shaders."

    result = resolver.decompose_task(task)

    assert [item.kind.value for item in result.obligations] == ["persistence"]
    assert result.obligations[0].task_span == task


@pytest.mark.parametrize("separator", (" but ", "; "))
def test_adversative_and_semicolon_mixed_clauses_keep_exact_spans(separator: str) -> None:
    resolver = _load_resolver()
    task = f"Persist the checkpoint{separator}tint the lunar shader mauve."

    result = resolver.decompose_task(task)

    assert [(item.kind.value, item.task_span) for item in result.obligations] == [
        ("persistence", "Persist the checkpoint"),
        ("unresolved", "tint the lunar shader mauve."),
    ]
    assert all(task[item.span_start : item.span_end] == item.task_span for item in result.obligations)


@pytest.mark.parametrize(
    "task",
    (
        "Persist checkpoints for (`red and blue`) shaders.",
        "Persist the `red; blue` checkpoint.",
        "Persist checkpoints for (red but blue) shaders.",
    ),
)
def test_clause_lexer_ignores_delimiters_inside_code_and_nesting(task: str) -> None:
    resolver = _load_resolver()

    result = resolver.decompose_task(task)

    assert [item.kind.value for item in result.obligations] == ["persistence"]
    assert result.obligations[0].task_span == task


@pytest.mark.parametrize(
    ("task", "expected_unknown"),
    (
        ("Persist the checkpoint and render shader.", "render shader."),
        ("Persist the checkpoint and call `shade and glow`.", "call `shade and glow`."),
        ("Persist the checkpoint and worker renders shader.", "worker renders shader."),
        ("Persist the checkpoint and normalize colors.", "normalize colors."),
    ),
)
def test_clause_lexer_splits_imperative_and_subject_predicates(
    task: str, expected_unknown: str
) -> None:
    resolver = _load_resolver()

    result = resolver.decompose_task(task)

    assert [(item.kind.value, item.task_span) for item in result.obligations] == [
        ("persistence", "Persist the checkpoint"),
        ("unresolved", expected_unknown),
    ]
    assert all(task[item.span_start : item.span_end] == item.task_span for item in result.obligations)


@pytest.mark.parametrize(
    "task",
    (
        "Persist checkpoints for red and blue shaders.",
        "Persist fast and bright shaders.",
        "Persist settings for local and remote workers.",
    ),
)
def test_clause_lexer_preserves_noun_and_adjective_coordination(task: str) -> None:
    resolver = _load_resolver()

    result = resolver.decompose_task(task)

    assert [item.kind.value for item in result.obligations] == ["persistence"]
    assert result.obligations[0].task_span == task


def test_semicolon_clause_expansion_obeys_span_bound() -> None:
    resolver = _load_resolver()
    task = "; ".join(
        "persist checkpoint" for _ in range(resolver.MAX_TASK_SPANS + 1)
    )

    with pytest.raises(resolver.TaskDecompositionError, match="span limit"):
        resolver.decompose_task(task)


@pytest.mark.parametrize(
    "task",
    (
        "Tune the lunar shader state file icon.",
        "Render the storage checkpoint badge.",
        "Color the journal and backup symbols.",
        "Show the save icon.",
    ),
)
def test_persistence_rejects_incidental_storage_nouns_and_icons(task: str) -> None:
    resolver = _load_resolver()

    result = resolver.decompose_task(task)

    assert "persistence" not in _kinds(result)


@pytest.mark.parametrize(
    "task",
    (
        "Persist the shader settings.",
        "Save the shader settings.",
        "Restore settings after restart.",
        "Settings must survive a restart.",
        "Write settings durably.",
        "Settings persisted across restarts.",
    ),
)
def test_persistence_requires_action_survival_or_durability(task: str) -> None:
    resolver = _load_resolver()

    assert "persistence" in _kinds(resolver.decompose_task(task))


def test_ordinary_repository_language_is_not_mistaken_for_donor_leakage() -> None:
    resolver = _load_resolver()
    task = "Validate the repository root remains inside the workspace."

    result = resolver.decompose_task(task)

    assert {"invariant", "safety", "verification"} <= _kinds(result)


@pytest.mark.parametrize(
    "task",
    (
        "Use the repository root to persist task state.",
        "Apply the retry method after failure.",
        "Validate the task description before execution.",
    ),
)
def test_ordinary_task_and_repository_phrasing_remains_valid(task: str) -> None:
    resolver = _load_resolver()

    assert resolver.decompose_task(task).task_text == task


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
