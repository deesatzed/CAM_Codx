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
from urllib.parse import unquote, urlsplit


SCHEMA_VERSION = 1
MAX_TASK_BYTES = 16 * 1024
MAX_TASK_SPANS = 64
MAX_OBLIGATIONS = 256
MAX_DISCRIMINATIVE_TERMS = 12
MAX_TERM_CHARACTERS = 64
MAX_LOCAL_DECLARATIONS = 16
MAX_ATTRIBUTION_OWNER_TOKENS = 8


_PERSISTENCE_ACTIONS = {"append", "persist", "reload", "restore", "save", "store", "write"}
_PERSISTENCE_INFLECTIONS = {
    "appended",
    "appends",
    "persisted",
    "persists",
    "reloaded",
    "reloads",
    "restored",
    "restores",
    "saved",
    "saves",
    "stored",
    "stores",
    "writes",
    "written",
    "wrote",
}
_PERSISTENCE_OBJECT_HEADS = {
    "artifact",
    "artifacts",
    "baseline",
    "baselines",
    "bytes",
    "cache",
    "caches",
    "checkpoint",
    "checkpoints",
    "collection",
    "collections",
    "config",
    "configs",
    "configuration",
    "configurations",
    "content",
    "contents",
    "data",
    "document",
    "documents",
    "entry",
    "entries",
    "event",
    "events",
    "evidence",
    "file",
    "files",
    "index",
    "indexes",
    "journal",
    "journals",
    "log",
    "logs",
    "mapping",
    "mappings",
    "message",
    "messages",
    "metadata",
    "output",
    "outputs",
    "payload",
    "payloads",
    "progress",
    "queue",
    "queues",
    "receipt",
    "receipts",
    "record",
    "records",
    "result",
    "results",
    "session",
    "sessions",
    "setting",
    "settings",
    "shader",
    "shaders",
    "snapshot",
    "snapshots",
    "state",
    "storage",
    "trail",
    "trails",
    "work",
}
_PERSISTENCE_SAFE_MODIFIERS = {
    "and",
    "application",
    "bright",
    "cached",
    "canonical",
    "code_identifier",
    "completed",
    "current",
    "durable",
    "encrypted",
    "fast",
    "local",
    "pending",
    "prior",
    "remote",
    "result",
    "runtime",
    "serialized",
    "session",
    "shader",
    "source",
    "target",
    "task",
    "user",
    "workflow",
}
_PERSISTENCE_PREFIX_WORDS = {
    "and",
    "but",
    "can",
    "finally",
    "first",
    "must",
    "next",
    "please",
    "shall",
    "should",
    "then",
    "to",
    "will",
}
_PERSISTENCE_AUXILIARIES = {
    "are",
    "had",
    "has",
    "have",
    "is",
    "must",
    "shall",
    "should",
    "was",
    "were",
    "will",
}


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


@dataclass(frozen=True)
class _ScanToken:
    raw: str
    core: str
    word: str
    start: int
    ends_statement: bool


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
    re.compile(r"\bhidden[\W_]*tests?\b"),
    re.compile(r"\bheld[\W_]*out\b"),
    re.compile(r"\bdonor\b"),
)
_REPOSITORY_HOSTS = {
    "bitbucket.com",
    "bitbucket.org",
    "github.com",
    "gitlab.com",
}
_REPOSITORY_SCHEMES = {"git", "http", "https", "ssh"}

_METHOD_ARTIFACT_WORDS = {
    "algorithm",
    "approach",
    "code",
    "design",
    "implementation",
    "mechanism",
    "method",
    "pattern",
    "procedure",
    "recipe",
    "strategy",
    "technique",
    "workflow",
}
_APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'", "＇": "'"})
_IDENTIFIER_TOKEN = r"[\w-]+(?:\.[\w-]+)*"
_BACKTICK_IDENTIFIER = r"`[^`\r\n]{1,128}`"
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


def _contains_case_identifier(value: str) -> bool:
    """Recognize C/N plus exactly two digits with arbitrary separators, linearly."""

    index = 0
    while index < len(value):
        if value[index] not in {"c", "n"} or (
            index > 0 and value[index - 1].isalnum()
        ):
            index += 1
            continue

        cursor = index + 1
        while cursor < len(value) and not value[cursor].isalnum():
            cursor += 1
        if cursor == len(value) or not value[cursor].isdigit():
            index += 1
            continue

        cursor += 1
        while cursor < len(value) and not value[cursor].isalnum():
            cursor += 1
        if cursor == len(value) or not value[cursor].isdigit():
            index += 1
            continue

        after = cursor + 1
        if after == len(value) or not value[after].isalnum():
            return True
        index += 1
    return False


def _repository_path_has_identity(path: str) -> bool:
    return len(tuple(part for part in path.split("/") if part)) >= 2


def _canonical_repository_candidate(raw: str) -> str:
    candidate = unicodedata.normalize("NFKC", raw).strip(
        "\"'“”‘’()[]{}<>,;!?*`"
    )
    candidate = unquote(candidate).replace("\\", "/")
    candidate = re.sub(
        r"^([a-z][a-z0-9+.-]*):/+", r"\1://", candidate, count=1, flags=re.IGNORECASE
    )
    return candidate


def _is_repository_url_candidate(raw: str) -> bool:
    candidate = _canonical_repository_candidate(raw)
    if "://" in candidate:
        try:
            parsed = urlsplit(candidate)
            host = (parsed.hostname or "").casefold().rstrip(".")
        except ValueError:
            return False
        return (
            parsed.scheme.casefold() in _REPOSITORY_SCHEMES
            and host.removeprefix("www.") in _REPOSITORY_HOSTS
            and _repository_path_has_identity(parsed.path)
        )

    if ":" not in candidate:
        return False
    authority, path = candidate.split(":", 1)
    if "/" not in path:
        return False
    host = authority.rsplit("@", 1)[-1].casefold().rstrip(".")
    return host in _REPOSITORY_HOSTS and _repository_path_has_identity(path)


def _contains_repository_url(value: str) -> bool:
    return any(_is_repository_url_candidate(match.group(0)) for match in re.finditer(r"\S+", value))


def _entity_identity(value: str) -> str:
    separated_camel = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])", " ", unicodedata.normalize("NFKC", value)
    )
    return "".join(
        character for character in separated_camel.casefold() if character.isalnum()
    )


def _validate_balanced_syntax(task_text: str) -> None:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    in_code = False
    for character in task_text:
        if character == "`":
            in_code = not in_code
        elif not in_code and character in "([{":
            stack.append(character)
        elif not in_code and character in pairs:
            if not stack or stack.pop() != pairs[character]:
                raise TaskDecompositionError(
                    "task text contains unbalanced or mismatched syntax"
                )
    if in_code or stack:
        raise TaskDecompositionError("task text contains unbalanced or mismatched syntax")


_TEXT_WRAPPER_PAIRS = (
    ("**", "**"),
    ("__", "__"),
    ("\"", "\""),
    ("“", "”"),
    ("‘", "’"),
    ("'", "'"),
    ("`", "`"),
    ("*", "*"),
    ("_", "_"),
)


def _unwrap_text_token(raw: str) -> str:
    core = raw.strip(".,!?;:()[]{}<>")
    changed = True
    while changed and core:
        changed = False
        for opening, closing in _TEXT_WRAPPER_PAIRS:
            if core.startswith(opening) and core.endswith(closing) and len(core) > len(
                opening
            ) + len(closing):
                core = core[len(opening) : -len(closing)]
                changed = True
                break
    core = core.lstrip("\"“‘`*_").rstrip("\"”’`*_")
    return core.translate(_APOSTROPHE_TRANSLATION)


def _token_ends_statement(token: str) -> bool:
    return token.rstrip(")]}'\"”’`*_").endswith((".", "!", "?", ";"))


def _attribution_tokens(task_text: str) -> tuple[_ScanToken, ...]:
    return tuple(
        _ScanToken(
            raw=match.group(0),
            core=_unwrap_text_token(match.group(0)),
            word=_normalize(_unwrap_text_token(match.group(0))),
            start=match.start(),
            ends_statement=_token_ends_statement(match.group(0)),
        )
        for match in re.finditer(r"\S+", task_text)
    )


def _possessive_attributions(
    tokens: tuple[_ScanToken, ...],
) -> tuple[tuple[str, int], ...]:
    artifact_later = [False] * len(tokens)
    seen_artifact = False
    for index in range(len(tokens) - 1, -1, -1):
        token = tokens[index]
        if token.ends_statement:
            seen_artifact = False
        artifact_later[index] = seen_artifact
        if token.word in _METHOD_ARTIFACT_WORDS:
            seen_artifact = True

    attributions: list[tuple[str, int]] = []
    for index, token in enumerate(tokens):
        if not token.core.casefold().endswith("'s") or not artifact_later[index]:
            continue
        owner_parts = [token.core[:-2]]
        preceding = index - 1
        while preceding >= 0 and len(owner_parts) < MAX_ATTRIBUTION_OWNER_TOKENS:
            previous = tokens[preceding]
            if previous.ends_statement:
                break
            owner_parts.insert(0, previous.core)
            preceding -= 1
        attributions.append((" ".join(owner_parts), token.start))
    return tuple(attributions)


def _directional_attributions(
    tokens: tuple[_ScanToken, ...],
) -> tuple[tuple[str, bool, int], ...]:
    attributions: list[tuple[str, bool, int]] = []
    for index, token in enumerate(tokens):
        if token.word not in _METHOD_ARTIFACT_WORDS:
            continue
        cursor = index + 1
        if cursor >= len(tokens):
            continue
        if tokens[cursor].word == "according":
            cursor += 1
            if cursor >= len(tokens) or tokens[cursor].word != "to":
                continue
        elif tokens[cursor].word not in {"by", "from"}:
            continue
        cursor += 1
        definite = cursor < len(tokens) and tokens[cursor].word == "the"
        if definite:
            cursor += 1
        source_parts: list[str] = []
        while cursor < len(tokens) and len(source_parts) < 4:
            source_parts.append(tokens[cursor].core)
            if tokens[cursor].ends_statement:
                break
            cursor += 1
        attributions.append((" ".join(source_parts), definite, token.start))
    return tuple(attributions)


def _declared_entities(task_text: str) -> tuple[tuple[str, int], ...]:
    declarations: list[tuple[str, int]] = []
    for match in _DECLARATION_PATTERN.finditer(task_text):
        retained: list[str] = []
        for token in match.group("entity").split():
            if token.casefold().strip("._-") in _DECLARATION_STOP_WORDS:
                break
            retained.append(token)
        if retained:
            identity = _entity_identity(" ".join(retained))
            if not identity:
                raise TaskDecompositionError(
                    "task text contains prohibited source or evaluation leakage"
                )
            declarations.append((identity, match.end()))
        if len(declarations) == MAX_LOCAL_DECLARATIONS:
            break
    return tuple(declarations)


def _matches_prior_declaration(
    value: str,
    position: int,
    declarations: tuple[tuple[str, int], ...],
) -> bool:
    identity = _entity_identity(value)
    if not identity:
        return False
    declared_before = {identity for identity, end in declarations if end <= position}
    return identity in declared_before


def _attribution_owner_phrase(owner: str) -> str:
    tokens = owner.split()
    if tokens and _normalize(tokens[0]) in _POLITE_PREFIXES:
        tokens = tokens[1:]
    if tokens and _normalize(tokens[0]) in _ATTRIBUTION_ACTION_WORDS:
        tokens = tokens[1:]
    return " ".join(tokens)


def _attributed_entity(owner: str) -> str:
    tokens = _attribution_owner_phrase(owner).split()
    if tokens and _normalize(tokens[0]) in {"a", "an", "the"}:
        tokens = tokens[1:]
    return " ".join(tokens)


def _is_generic_local_role(owner: str) -> bool:
    normalized = _normalize(owner)
    return any(normalized == f"the {role}" for role in _GENERIC_LOCAL_ROLES)


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
    tokens = _attribution_tokens(task_text)
    for owner, position in _possessive_attributions(tokens):
        attributed_entity = _attributed_entity(owner)
        if not _entity_identity(attributed_entity):
            return True
        if not _matches_prior_declaration(
            attributed_entity, position, declarations
        ) and not (_is_generic_local_role(_attribution_owner_phrase(owner))):
            return True
    for source, definite, position in _directional_attributions(tokens):
        if not _entity_identity(source):
            return True
        if not _matches_prior_declaration(source, position, declarations) and not (
            _is_generic_local_reference(source, "the" if definite else None)
        ):
            return True
    return False


def _validate_task_text(task_text: object) -> str:
    if not isinstance(task_text, str) or not task_text.strip():
        raise TaskDecompositionError("task text must be a non-empty string")
    try:
        encoded_task = task_text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise TaskDecompositionError("task text must be valid UTF-8") from error
    if len(encoded_task) > MAX_TASK_BYTES:
        raise TaskDecompositionError(f"task text exceeds {MAX_TASK_BYTES}-byte limit")
    _validate_balanced_syntax(task_text)
    normalized = _normalize(task_text)
    leakage_form = _leakage_normal_form(task_text)
    case_identifier_form = unicodedata.normalize("NFKC", task_text).casefold()
    attribution_form = unicodedata.normalize("NFKC", task_text)
    if (
        _contains_case_identifier(case_identifier_form)
        or any(pattern.search(leakage_form) for pattern in _LEAKAGE_PATTERNS)
        or _contains_repository_url(attribution_form)
        or _contains_structural_source_attribution(attribution_form)
    ):
        raise TaskDecompositionError("task text contains prohibited source or evaluation leakage")
    if _TERM_PATTERN.search(normalized) is None:
        raise TaskDecompositionError("task text must contain a bounded textual term")
    return task_text


def _persistence_text(normalized_span: str) -> str:
    return re.sub(r"`[^`]*`", " code_identifier ", normalized_span)


def _persistence_word_matches(normalized_span: str) -> tuple[re.Match[str], ...]:
    return tuple(_TERM_PATTERN.finditer(_persistence_text(normalized_span)))


def _persistence_words(normalized_span: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in _persistence_word_matches(normalized_span))


def _has_closed_persistence_object(words: tuple[str, ...], start: int) -> bool:
    if start < len(words) and words[start] in {"a", "an", "the"}:
        start += 1
    modifiers = 0
    while start < len(words):
        word = words[start]
        if word in _PERSISTENCE_OBJECT_HEADS:
            return True
        if word not in _PERSISTENCE_SAFE_MODIFIERS or modifiers == 4:
            return False
        modifiers += 1
        start += 1
    return False


def _is_closed_persistence_subject(words: tuple[str, ...]) -> bool:
    if words and words[0] == "the":
        words = words[1:]
    if not words or words[-1] not in _PERSISTENCE_OBJECT_HEADS:
        return False
    return len(words) <= 5 and all(
        word in _PERSISTENCE_SAFE_MODIFIERS for word in words[:-1]
    )


def _matches_direct_persistence_action(normalized_span: str) -> bool:
    persistence_text = _persistence_text(normalized_span)
    matches = tuple(_TERM_PATTERN.finditer(persistence_text))
    words = tuple(match.group(0) for match in matches)
    for index, word in enumerate(words):
        if word not in _PERSISTENCE_ACTIONS | _PERSISTENCE_INFLECTIONS:
            continue
        if word in _PERSISTENCE_ACTIONS and index > 0:
            gap = persistence_text[matches[index - 1].end() : matches[index].start()]
            if (
                words[index - 1] not in _PERSISTENCE_PREFIX_WORDS
                and not any(character in ",;:" for character in gap)
            ):
                continue
        if _has_closed_persistence_object(words, index + 1):
            return True
    return False


def _matches_subject_persistence(normalized_span: str) -> bool:
    words = _persistence_words(normalized_span)
    for index, word in enumerate(words):
        if word in _PERSISTENCE_INFLECTIONS:
            subject_end = index
            while subject_end and words[subject_end - 1] in _PERSISTENCE_AUXILIARIES:
                subject_end -= 1
            if _is_closed_persistence_subject(words[:subject_end]):
                return True
        if word not in {"survive", "survived", "survives"}:
            continue
        subject_end = index
        while subject_end and words[subject_end - 1] in (
            _PERSISTENCE_AUXILIARIES | {"can"}
        ):
            subject_end -= 1
        durability_words = words[index + 1 : index + 5]
        if _is_closed_persistence_subject(words[:subject_end]) and any(
            candidate
            in {"interruption", "reboot", "relaunch", "restart", "restarts", "shutdown"}
            for candidate in durability_words
        ):
            return True
    return False


def _has_persistence_cue(normalized_span: str) -> bool:
    return _matches_direct_persistence_action(
        normalized_span
    ) or _matches_subject_persistence(normalized_span)


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
    return re.match(
        r"^[a-z0-9_-]+\s+(?:the|a|an|each|every|this|that|these|those|it|them|to)\b",
        normalized,
    ) is not None


def _left_has_completed_direct_object(value: str) -> bool:
    return _matches_direct_persistence_action(_normalize(value))


def _has_known_obligation_predicate(normalized: str) -> bool:
    return _matched_kinds(normalized) != (ObligationKind.UNRESOLVED,)


def _has_shared_plural_head(tokens: tuple[str, ...]) -> bool:
    return len(tokens) >= 2 and tokens[-1].endswith("s")


def _starts_independent_clause(value: str, left_value: str) -> bool:
    normalized = _normalize(value)
    if not normalized:
        return False
    tokens = tuple(match.group(0) for match in _TERM_PATTERN.finditer(normalized))
    if _has_known_obligation_predicate(normalized):
        return True
    if _has_unambiguous_predicate_evidence(tokens, normalized):
        return True
    if _left_is_prepositional_coordination(left_value) and _has_shared_plural_head(
        tokens
    ):
        return False
    if tokens and tokens[0] in _GENERIC_ACTION_WORDS:
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
    matched = [
        kind
        for kind, patterns in _CUE_PATTERNS.items()
        if any(pattern.search(normalized_span) for pattern in patterns)
    ]
    if _has_persistence_cue(normalized_span):
        matched.append(ObligationKind.PERSISTENCE)
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
