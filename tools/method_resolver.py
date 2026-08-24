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
MAX_LOCAL_DECLARATIONS = 16


_PERSISTENCE_OBJECT = (
    r"(?:state|settings?|configs?|configurations?|data|records?|results?|artifacts?|"
    r"checkpoints?|progress|files?|documents?|entries|events?|queues?|journals?|"
    r"snapshots?|metadata|caches?|sessions?|receipts?|outputs?|work|collections?|"
    r"mappings?|contents?|payloads?|messages?|logs?|indexes?|baselines?|bytes|"
    r"evidence|trails?|storage)"
)
_PERSISTENCE_ACTION = r"(?:persist|save|store|write|append|restore|reload)"
_PERSISTENCE_ACTION_INFLECTED = (
    r"(?:persists?|persisted|saved|stored|writes?|wrote|written|appends?|appended|"
    r"restores?|restored|reloads?|reloaded)"
)
_PERSISTENCE_MODIFIER = (
    r"(?:(?!(?:after|and|before|but|during|for|when|while|with)\b)"
    r"[a-z0-9_-]+\s+){0,3}"
)
_PERSISTENCE_PREFIX = (
    r"(?:^|[,;:]\s+|\b(?:first|then|next|finally|must|should|shall|will|can|to)\s+)"
)
_PERSISTENCE_DIRECT_OBJECT_PATTERN = re.compile(
    rf"{_PERSISTENCE_PREFIX}{_PERSISTENCE_ACTION}\b\s+"
    rf"(?:the\s+|a\s+|an\s+)?{_PERSISTENCE_MODIFIER}{_PERSISTENCE_OBJECT}\b"
    r"\s*[.!?]?$"
)


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
            rf"{_PERSISTENCE_PREFIX}persist\b\s+(?:the\s+|a\s+|an\s+)?"
            rf"{_PERSISTENCE_MODIFIER}[a-z0-9_-]+"
        ),
        re.compile(
            rf"{_PERSISTENCE_PREFIX}{_PERSISTENCE_ACTION}\b\s+"
            rf"(?:the\s+|a\s+|an\s+)?{_PERSISTENCE_MODIFIER}{_PERSISTENCE_OBJECT}\b"
        ),
        re.compile(
            rf"\b{_PERSISTENCE_ACTION_INFLECTED}\b\s+"
            rf"(?:the\s+|a\s+|an\s+)?{_PERSISTENCE_MODIFIER}{_PERSISTENCE_OBJECT}\b"
        ),
        re.compile(
            rf"\b{_PERSISTENCE_OBJECT}\b\s+"
            rf"(?:(?:is|are|was|were|has|have|had|must|should|will)\s+){{0,2}}"
            rf"{_PERSISTENCE_ACTION_INFLECTED}\b"
        ),
        re.compile(
            rf"(?:^|[,;:]\s+)(?:the\s+)?(?:[a-z0-9_-]+\s+){{0,2}}"
            rf"{_PERSISTENCE_OBJECT}\b\s+"
            rf"(?:(?:must|should|shall|will|can)\s+)?(?:survive|survives|survived)\b"
            r"\s+(?:(?:across|after|through)\s+)?(?:a\s+|the\s+)?"
            r"(?:restart|restarts|reboot|relaunch|shutdown|interruption)\b"
        ),
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
    re.compile(r"(?<![a-z0-9])[cn][\W_]*\d{2}(?![a-z0-9])"),
    re.compile(r"\bhidden[\W_]*tests?\b"),
    re.compile(r"\bheld[\W_]*out\b"),
    re.compile(r"\bdonor\b"),
    re.compile(r"https?://(?:www\.)?(?:github|gitlab|bitbucket)\.com/[^\s/]+/[^\s/]+"),
)

_METHOD_ARTIFACT = (
    r"(?:method|pattern|algorithm|implementation|approach|strategy|technique|"
    r"procedure|workflow|mechanism|recipe|design|code)"
)
_IDENTIFIER_TOKEN = r"[\w-]+(?:\.[\w-]+)*"
_BACKTICK_IDENTIFIER = r"`[^`\r\n]{1,128}`"
_ATTRIBUTION_TOKEN = rf"(?:{_BACKTICK_IDENTIFIER}|{_IDENTIFIER_TOKEN})"
_POSSESSIVE_ATTRIBUTION_PATTERN = re.compile(
    rf"(?P<owner>{_ATTRIBUTION_TOKEN}(?:\s+{_ATTRIBUTION_TOKEN}){{0,7}})['’]s\s+"
    rf"(?:[\w-]+\s+){{0,5}}{_METHOD_ARTIFACT}\b",
    flags=re.IGNORECASE,
)
_DIRECTIONAL_ATTRIBUTION_PATTERN = re.compile(
    rf"\b{_METHOD_ARTIFACT}\b\s+(?:from|by|according\s+to)\s+(?P<definite>the\s+)?"
    rf"(?P<source>{_BACKTICK_IDENTIFIER}|{_IDENTIFIER_TOKEN}"
    rf"(?:\s+{_IDENTIFIER_TOKEN}){{0,3}})",
    flags=re.IGNORECASE,
)
_DECLARATION_PATTERN = re.compile(
    r"(?:^|(?<=[.!?;]))\s*(?:create|define|declare|construct|instantiate|introduce|"
    r"build)\s+(?:a\s+|an\s+|the\s+)?"
    rf"(?P<entity>{_BACKTICK_IDENTIFIER}|{_IDENTIFIER_TOKEN}"
    rf"(?:\s+{_IDENTIFIER_TOKEN}){{0,3}})",
    flags=re.IGNORECASE,
)
_DECLARATION_STOP_WORDS = {
    "about",
    "and",
    "for",
    "from",
    "that",
    "to",
    "using",
    "which",
    "with",
}
_GENERIC_LOCAL_ROLES = {
    "caller",
    "client",
    "handler",
    "reader",
    "runner",
    "server",
    "user",
    "worker",
    "writer",
}
_GENERIC_LOCAL_REFERENCE_NOUNS = {
    "configuration",
    "description",
    "instructions",
    "requirements",
    "schema",
    "specification",
    "text",
}
_GENERIC_LOCAL_REFERENCE_MODIFIERS = {
    "current",
    "input",
    "local",
    "provided",
    "repository",
    "supplied",
    "task",
    "this",
}
_POLITE_PREFIXES = {"kindly", "please"}
_ATTRIBUTION_ACTION_WORDS = {
    "adopt",
    "apply",
    "borrow",
    "follow",
    "implement",
    "port",
    "reuse",
    "review",
    "use",
}

_GENERIC_ACTION_WORDS = {
    "add",
    "apply",
    "build",
    "call",
    "collect",
    "compute",
    "convert",
    "create",
    "emit",
    "execute",
    "generate",
    "handle",
    "invoke",
    "implement",
    "load",
    "normalize",
    "parse",
    "process",
    "produce",
    "render",
    "return",
    "set",
    "transform",
    "update",
    "use",
    "validate",
}
_MODAL_WORDS = {
    "can",
    "could",
    "may",
    "might",
    "must",
    "shall",
    "should",
    "will",
    "would",
}
_PREPOSITIONAL_COORDINATION_PATTERN = re.compile(
    r"\b(?:for|of|with|between|among|in|on|to|from|by)\s+"
    r"(?:[a-z0-9_-]+\s+){0,2}[a-z0-9_-]+\s*$"
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


def _leakage_normal_form(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    separated_camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", normalized)
    return separated_camel.casefold()


def _entity_identity(value: str) -> str:
    separated_camel = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])", " ", unicodedata.normalize("NFKC", value)
    )
    return "".join(
        character for character in separated_camel.casefold() if character.isalnum()
    )


def _declared_entities(task_text: str) -> tuple[tuple[str, int], ...]:
    declarations: list[tuple[str, int]] = []
    for match in _DECLARATION_PATTERN.finditer(task_text):
        retained: list[str] = []
        for token in match.group("entity").split():
            if token.casefold().strip("._-") in _DECLARATION_STOP_WORDS:
                break
            retained.append(token)
        if retained:
            declarations.append((_entity_identity(" ".join(retained)), match.end()))
        if len(declarations) == MAX_LOCAL_DECLARATIONS:
            break
    return tuple(declarations)


def _matches_prior_declaration(
    value: str,
    position: int,
    declarations: tuple[tuple[str, int], ...],
) -> bool:
    declared_before = {identity for identity, end in declarations if end <= position}
    return _entity_identity(value) in declared_before


def _attributed_entity(owner: str) -> str:
    tokens = owner.split()
    if tokens and _normalize(tokens[0]) in _POLITE_PREFIXES:
        tokens = tokens[1:]
    if tokens and _normalize(tokens[0]) in _ATTRIBUTION_ACTION_WORDS:
        tokens = tokens[1:]
    if tokens and _normalize(tokens[0]) in {"a", "an", "the"}:
        tokens = tokens[1:]
    return " ".join(tokens)


def _is_generic_local_role(owner: str) -> bool:
    tokens = tuple(token.casefold().strip("._-") for token in owner.split())
    return (
        len(tokens) >= 2
        and tokens[-2] == "the"
        and tokens[-1] in _GENERIC_LOCAL_ROLES
    )


def _is_generic_local_reference(source: str, definite: str | None) -> bool:
    tokens = tuple(token.casefold().strip("._-") for token in source.split())
    return (
        definite is not None
        and bool(tokens)
        and tokens[-1] in _GENERIC_LOCAL_REFERENCE_NOUNS
        and all(token in _GENERIC_LOCAL_REFERENCE_MODIFIERS for token in tokens[:-1])
    )


def _contains_structural_source_attribution(task_text: str) -> bool:
    declarations = _declared_entities(task_text)
    for match in _POSSESSIVE_ATTRIBUTION_PATTERN.finditer(task_text):
        owner = match.group("owner")
        if not _matches_prior_declaration(
            _attributed_entity(owner), match.start(), declarations
        ) and not (_is_generic_local_role(owner)):
            return True
    for match in _DIRECTIONAL_ATTRIBUTION_PATTERN.finditer(task_text):
        source = match.group("source")
        if not _matches_prior_declaration(source, match.start(), declarations) and not (
            _is_generic_local_reference(source, match.group("definite"))
        ):
            return True
    return False


def _validate_task_text(task_text: object) -> str:
    if not isinstance(task_text, str) or not task_text.strip():
        raise TaskDecompositionError("task text must be a non-empty string")
    if len(task_text.encode("utf-8")) > MAX_TASK_BYTES:
        raise TaskDecompositionError(f"task text exceeds {MAX_TASK_BYTES}-byte limit")
    normalized = _normalize(task_text)
    leakage_form = _leakage_normal_form(task_text)
    attribution_form = unicodedata.normalize("NFKC", task_text)
    if any(pattern.search(leakage_form) for pattern in _LEAKAGE_PATTERNS) or (
        _contains_structural_source_attribution(attribution_form)
    ):
        raise TaskDecompositionError("task text contains prohibited source or evaluation leakage")
    if _TERM_PATTERN.search(normalized) is None:
        raise TaskDecompositionError("task text must contain a bounded textual term")
    return task_text


def _looks_like_inflected_predicate(tokens: tuple[str, ...]) -> bool:
    if len(tokens) < 3:
        return False
    predicate = tokens[1]
    return predicate.endswith(("s", "ed", "ing"))


def _left_is_prepositional_coordination(value: str) -> bool:
    return _PREPOSITIONAL_COORDINATION_PATTERN.search(_normalize(value)) is not None


def _has_unambiguous_predicate_evidence(
    tokens: tuple[str, ...], normalized: str
) -> bool:
    if re.match(r"^[a-z0-9_-]+\s+`", normalized):
        return True
    if len(tokens) >= 3 and tokens[1] in _MODAL_WORDS:
        return True
    if tokens and tokens[0] in _GENERIC_ACTION_WORDS:
        return True
    return re.match(
        r"^[a-z0-9_-]+\s+(?:the|a|an|each|every|this|that|these|those|it|them|to)\b",
        normalized,
    ) is not None


def _left_has_completed_direct_object(value: str) -> bool:
    return _PERSISTENCE_DIRECT_OBJECT_PATTERN.match(_normalize(value)) is not None


def _starts_independent_clause(value: str, left_value: str) -> bool:
    normalized = _normalize(value)
    if not normalized:
        return False
    tokens = tuple(match.group(0) for match in _TERM_PATTERN.finditer(normalized))
    if _has_unambiguous_predicate_evidence(tokens, normalized):
        return True
    if _left_is_prepositional_coordination(left_value):
        return False
    if _left_has_completed_direct_object(left_value) and len(tokens) >= 2:
        return True
    if len(tokens) >= 2 and tokens[1].endswith("s"):
        return False
    if _looks_like_inflected_predicate(tokens):
        return True
    if tokens and tokens[0].endswith(("ate", "ify", "ise", "ize", "en")):
        return True
    if len(tokens) == 2 and not tokens[1].endswith("s"):
        return _matched_kinds(_normalize(left_value)) != (ObligationKind.UNRESOLVED,)
    if _matched_kinds(normalized) != (ObligationKind.UNRESOLVED,):
        return len(tokens) != 2 or not tokens[1].endswith("s")
    return False


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
        previous_end = candidates[candidate_index - 1][1] if candidate_index else 0
        next_start = (
            candidates[candidate_index + 1][0]
            if candidate_index + 1 < len(candidates)
            else len(span)
        )
        left_clause = span[previous_end:start]
        right_clause = span[end:next_start]
        if delimiter in {";", "but"} or _starts_independent_clause(
            right_clause, left_clause
        ):
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
