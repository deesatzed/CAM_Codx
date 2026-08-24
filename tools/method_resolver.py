#!/usr/bin/env python3
"""Pure, deterministic decomposition of public task text into method obligations.

This module intentionally performs no corpus access or semantic retrieval.  It
uses bounded normalization and generic syntactic cues only.  Unrecognized task
spans stay visible as unresolved obligations for later, evidence-backed work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re
import unicodedata


SCHEMA_VERSION = 1
MAX_TASK_BYTES = 16 * 1024
MAX_TASK_SPANS = 64
MAX_OBLIGATIONS = 256
MAX_DISCRIMINATIVE_TERMS = 12
MAX_TERM_CHARACTERS = 64


class TaskDecompositionError(ValueError):
    """Raised when public task text is invalid, unbounded, or leak-prone."""


class ObligationKind(str, Enum):
    """Closed set of method concerns surfaced by local decomposition."""

    CURRENT_API = "current_api"
    FAILURE = "failure"
    INVARIANT = "invariant"
    ORDER = "order"
    PERSISTENCE = "persistence"
    RECOVERY = "recovery"
    SAFETY = "safety"
    UNRESOLVED = "unresolved"
    VERIFICATION = "verification"


@dataclass(frozen=True)
class TaskObligation:
    obligation_id: str
    kind: ObligationKind
    task_span: str
    span_start: int
    span_end: int
    discriminative_terms: tuple[str, ...]
    required: bool


@dataclass(frozen=True)
class TaskResolution:
    schema_version: int
    task_text: str
    obligations: tuple[TaskObligation, ...]


# These are domain-independent method cues, not case identifiers or mappings.
# Each rule is intentionally inspectable and operates on one exact source span.
_CUE_PATTERNS: dict[ObligationKind, tuple[re.Pattern[str], ...]] = {
    ObligationKind.CURRENT_API: (
        re.compile(
            r"\b(?:current|latest|supported|documented)\b.{0,80}"
            r"\b(?:api|sdk|library|framework|python|schema|version)\b"
        ),
        re.compile(
            r"\b(?:api|sdk|library|framework|python|schema|version)\b.{0,80}"
            r"\b(?:current|latest|supported|documented)\b"
        ),
        re.compile(
            r"\b(?:api|sdk|library|framework|python)\s+"
            r"(?:v(?:ersion)?\s*)?\d+(?:\.\d+){1,2}\b"
        ),
    ),
    ObligationKind.FAILURE: (
        re.compile(
            r"\b(?:fail(?:s|ed|ure|ures)?|error|errors|exception|exceptions|invalid|"
            r"malformed|corrupt|denied|reject(?:s|ed|ion)?|unsafe|tamper(?:ing|ed)?|"
            r"incomplete|interruption)\b"
        ),
    ),
    ObligationKind.INVARIANT: (
        re.compile(r"\b(?:must|never|always|exactly|deterministic|unchanged)\b"),
        re.compile(r"\b(?:preserve|preserves|retain|retains|remain|remains)\b"),
        re.compile(r"\b(?:at most|at least|only when|no more than|no response)\b"),
    ),
    ObligationKind.ORDER: (
        re.compile(
            r"\b(?:before|after|then|first|finally|order|ordered|ordering|reordering|"
            r"precedence|contiguous|sequence|arrival order|previous|dependencies)\b"
        ),
    ),
    ObligationKind.PERSISTENCE: (
        re.compile(
            r"\b(?:persist(?:s|ed|ence|ent)?|durable|checkpoint|journal|storage|"
            r"store|stored|save|saved|write|writes|written|append|appends|backup)\b"
        ),
        re.compile(r"\bstate (?:file|store|path|record|snapshot)\b"),
        re.compile(r"\b(?:file|store|checkpoint) state\b"),
        re.compile(r"\b(?:atomic|atomically|replace-atomic)\b"),
    ),
    ObligationKind.RECOVERY: (
        re.compile(
            r"\b(?:recover(?:y|ed|able)?|resume|resumes|retry|retries|backoff|"
            r"rollback|restore|restored|fallback|backup|cleanup|clean up)\b"
        ),
        re.compile(r"\b(?:later work proceeds|complete(?:s|d)? .* later)\b"),
    ),
    ObligationKind.SAFETY: (
        re.compile(
            r"\b(?:safe|safely|safety|secure|secret|secrets|sanitize|sanitized|"
            r"redact|redacted|private|permission|permissions|encrypt|encrypted|"
            r"decrypt|authorize|authorization|containment|traversal|symlink|"
            r"owner-only|read-only|credential|credentials)\b"
        ),
        re.compile(r"\b(?:fail closed|do not|must not|never)\b"),
        re.compile(r"\binside (?:the )?(?:workspace|root|base)\b"),
    ),
    ObligationKind.VERIFICATION: (
        re.compile(
            r"\b(?:verify|verification|validate|validation|assert|check|checks|"
            r"audit|proof|evidence|receipt|integrity|detect|detects|match|matches)\b"
        ),
    ),
}

_LEAKAGE_PATTERNS = (
    re.compile(r"(?<![a-z0-9])[cn]\d{2}(?![a-z0-9])"),
    re.compile(r"\b(?:hidden[- ]tests?|held[- ]out)\b"),
    re.compile(r"\bdonor\b"),
    re.compile(r"\b(?:copy|reuse|follow|from)\b.{0,48}\b(?:repository|repo)\b"),
    re.compile(
        r"\b(?:copy|reuse|follow|adopt|use|apply)\s+[^.!?\n]{1,80}['’]s\s+"
        r"[^.!?\n]{0,80}\b(?:method|algorithm|implementation|pattern|code)\b"
    ),
    re.compile(
        r"\b(?:copy|reuse|follow|adopt|use|apply)\s+(?:the\s+)?[^.!?\n]{0,80}"
        r"\b(?:method|algorithm|implementation|pattern|code)\s+from\s+"
        r"[^.!?\n]{1,80}(?:[.!?]|$)"
    ),
    re.compile(r"https?://(?:www\.)?(?:github|gitlab|bitbucket)\.com/[^\s/]+/[^\s/]+"),
)

_TERM_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*")
_OPTIONAL_PATTERN = re.compile(r"\b(?:optional|optionally)\b")
_NON_SIGNAL_TERMS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "create",
    "do",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "its",
    "must",
    "no",
    "not",
    "of",
    "on",
    "only",
    "or",
    "return",
    "returns",
    "the",
    "then",
    "to",
    "use",
    "when",
    "with",
}


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _validate_task_text(task_text: object) -> str:
    if not isinstance(task_text, str) or not task_text.strip():
        raise TaskDecompositionError("task text must be a non-empty string")
    if len(task_text.encode("utf-8")) > MAX_TASK_BYTES:
        raise TaskDecompositionError(f"task text exceeds {MAX_TASK_BYTES}-byte limit")
    normalized = _normalize(task_text)
    if any(pattern.search(normalized) for pattern in _LEAKAGE_PATTERNS):
        raise TaskDecompositionError("task text contains prohibited source or evaluation leakage")
    if _TERM_PATTERN.search(normalized) is None:
        raise TaskDecompositionError("task text must contain a bounded textual term")
    return task_text


def _starts_independent_clause(value: str) -> bool:
    normalized = _normalize(value)
    if not normalized:
        return False
    if _matched_kinds(normalized) != (ObligationKind.UNRESOLVED,):
        return True
    return re.match(
        r"^[a-z0-9_-]+\s+(?:the|a|an|each|every|this|that|these|those|it|them|to)\b",
        normalized,
    ) is not None


def _clause_boundaries(span: str) -> tuple[tuple[int, int], ...]:
    """Find supported top-level clause delimiters without parsing code spans."""

    candidates: list[tuple[int, int, str]] = []
    in_code = False
    nesting = 0
    index = 0
    while index < len(span):
        character = span[index]
        if character == "`":
            in_code = not in_code
            index += 1
            continue
        if not in_code:
            if character in "([{":
                nesting += 1
            elif character in ")]}":
                nesting = max(0, nesting - 1)
            elif nesting == 0 and character == ";":
                candidates.append((index, index + 1, ";"))
                index += 1
                continue
            elif nesting == 0:
                matched_delimiter = next(
                    (
                        delimiter
                        for delimiter in ("and", "but")
                        if span[index : index + len(delimiter)].casefold() == delimiter
                    ),
                    None,
                )
                if matched_delimiter is not None:
                    before = span[index - 1] if index else " "
                    after_index = index + len(matched_delimiter)
                    after = span[after_index] if after_index < len(span) else " "
                    if not before.isalnum() and not after.isalnum():
                        candidates.append((index, after_index, matched_delimiter))
                        index = after_index
                        continue
        index += 1

    boundaries: list[tuple[int, int]] = []
    for candidate_index, (start, end, delimiter) in enumerate(candidates):
        next_start = (
            candidates[candidate_index + 1][0]
            if candidate_index + 1 < len(candidates)
            else len(span)
        )
        right_clause = span[end:next_start]
        if delimiter in {";", "but"} or _starts_independent_clause(right_clause):
            boundaries.append((start, end))
    return tuple(boundaries)


def _split_supported_conjunctions(
    start: int, end: int, span: str
) -> tuple[tuple[int, int, str], ...]:
    """Split mixed clauses only when the sentence contains a known method cue."""

    if _matched_kinds(_normalize(span)) == (ObligationKind.UNRESOLVED,):
        return ((start, end, span),)
    boundaries = _clause_boundaries(span)
    if not boundaries:
        return ((start, end, span),)

    clauses: list[tuple[int, int, str]] = []
    cursor = 0
    for conjunction_start, conjunction_end in (*boundaries, (len(span), len(span))):
        clause_start = cursor
        clause_end = conjunction_start
        while clause_start < clause_end and span[clause_start].isspace():
            clause_start += 1
        while clause_end > clause_start and span[clause_end - 1].isspace():
            clause_end -= 1
        if clause_start < clause_end:
            clause = span[clause_start:clause_end]
            if _TERM_PATTERN.search(_normalize(clause)) is not None:
                clauses.append((start + clause_start, start + clause_end, clause))
        cursor = conjunction_end
    return tuple(clauses) or ((start, end, span),)


def _task_spans(task_text: str) -> tuple[tuple[int, int, str], ...]:
    """Split sentences and mixed clauses while retaining exact source offsets."""

    boundaries: list[int] = []
    in_code = False
    for index, character in enumerate(task_text):
        if character == "`":
            in_code = not in_code
        if in_code or character not in ".!?":
            continue
        if index + 1 == len(task_text) or task_text[index + 1].isspace():
            boundaries.append(index + 1)

    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for boundary in (*boundaries, len(task_text)):
        start = cursor
        end = boundary
        while start < end and task_text[start].isspace():
            start += 1
        while end > start and task_text[end - 1].isspace():
            end -= 1
        if start < end:
            span = task_text[start:end]
            if _TERM_PATTERN.search(_normalize(span)) is not None:
                spans.extend(_split_supported_conjunctions(start, end, span))
        cursor = boundary

    if len(spans) > MAX_TASK_SPANS:
        raise TaskDecompositionError(f"task text exceeds {MAX_TASK_SPANS}-span limit")
    if not spans:
        raise TaskDecompositionError("task text has no resolvable source spans")
    return tuple(spans)


def _discriminative_terms(normalized_span: str) -> tuple[str, ...]:
    terms: list[str] = []
    seen: set[str] = set()
    for match in _TERM_PATTERN.finditer(normalized_span):
        term = match.group(0)[:MAX_TERM_CHARACTERS]
        if term in _NON_SIGNAL_TERMS or term in seen:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) == MAX_DISCRIMINATIVE_TERMS:
            break
    if terms:
        return tuple(terms)
    # A validated span has at least one token. Retain the first even if it is a
    # common syntactic word so every unresolved obligation remains queryable.
    first = _TERM_PATTERN.search(normalized_span)
    assert first is not None
    return (first.group(0)[:MAX_TERM_CHARACTERS],)


def _matched_kinds(normalized_span: str) -> tuple[ObligationKind, ...]:
    matched = tuple(
        kind
        for kind, patterns in _CUE_PATTERNS.items()
        if any(pattern.search(normalized_span) for pattern in patterns)
    )
    return tuple(sorted(matched, key=lambda kind: kind.value)) or (ObligationKind.UNRESOLVED,)


def _obligation_id(kind: ObligationKind, span_start: int, span_end: int, span: str) -> str:
    identity = json.dumps(
        [kind.value, span_start, span_end, span],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"obligation-{hashlib.sha256(identity).hexdigest()[:16]}"


def decompose_task(task_text: object) -> TaskResolution:
    """Return bounded typed obligations derived only from the supplied text."""

    validated_text = _validate_task_text(task_text)
    obligations: list[TaskObligation] = []
    for start, end, span in _task_spans(validated_text):
        normalized_span = _normalize(span)
        terms = _discriminative_terms(normalized_span)
        required = _OPTIONAL_PATTERN.search(normalized_span) is None
        for kind in _matched_kinds(normalized_span):
            obligations.append(
                TaskObligation(
                    obligation_id=_obligation_id(kind, start, end, span),
                    kind=kind,
                    task_span=span,
                    span_start=start,
                    span_end=end,
                    discriminative_terms=terms,
                    required=required,
                )
            )
            if len(obligations) > MAX_OBLIGATIONS:
                raise TaskDecompositionError(
                    f"task text exceeds {MAX_OBLIGATIONS}-obligation limit"
                )

    return TaskResolution(
        schema_version=SCHEMA_VERSION,
        task_text=validated_text,
        obligations=tuple(obligations),
    )


def serialize_resolution(resolution: TaskResolution) -> bytes:
    """Serialize one resolution as canonical, stable UTF-8 JSON bytes."""

    _validate_resolution_types(resolution)
    if resolution != decompose_task(resolution.task_text):
        raise TaskDecompositionError("resolution is not the canonical decomposition")
    payload = asdict(resolution)
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _validate_resolution_types(resolution: object) -> None:
    """Reject equality-compatible type confusion before canonical comparison."""

    if type(resolution) is not TaskResolution:
        raise TaskDecompositionError("resolution is not a canonical TaskResolution type")
    if type(resolution.schema_version) is not int or resolution.schema_version != SCHEMA_VERSION:
        raise TaskDecompositionError("resolution has a non-canonical schema version")
    if type(resolution.task_text) is not str:
        raise TaskDecompositionError("resolution task text has a non-canonical type")
    if type(resolution.obligations) is not tuple:
        raise TaskDecompositionError("resolution obligations have a non-canonical type")
    for obligation in resolution.obligations:
        if type(obligation) is not TaskObligation:
            raise TaskDecompositionError("resolution obligation has a non-canonical type")
        if type(obligation.obligation_id) is not str:
            raise TaskDecompositionError("obligation ID has a non-canonical type")
        if type(obligation.kind) is not ObligationKind:
            raise TaskDecompositionError("obligation kind has a non-canonical type")
        if type(obligation.task_span) is not str:
            raise TaskDecompositionError("obligation span has a non-canonical type")
        if type(obligation.span_start) is not int or type(obligation.span_end) is not int:
            raise TaskDecompositionError("obligation offsets have non-canonical types")
        if type(obligation.discriminative_terms) is not tuple or any(
            type(term) is not str for term in obligation.discriminative_terms
        ):
            raise TaskDecompositionError("obligation terms have non-canonical types")
        if type(obligation.required) is not bool:
            raise TaskDecompositionError("obligation required flag has a non-canonical type")
