"""Read bounded WIP evidence and derive source-linked opportunity needs.

This module stops at target inspection and need description. It never runs the
target, loads a provider, opens CAM data, or creates implementation steps.
"""

from __future__ import annotations

import ast
from contextvars import ContextVar
from dataclasses import dataclass, field as dataclass_field
from datetime import date
import errno
import hashlib
import html
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import signal
import shutil
import stat
import subprocess
import tempfile
import time
from typing import Literal
import unicodedata
from urllib.parse import unquote, urlparse


VerificationStatus = Literal["not_run"]
NeedCategory = Literal["blocker", "risk", "next_action", "open_question"]
QueryStatus = Literal["ok", "query_failed"]
EffectStatus = Literal["observed", "intended", "negative"]
SourceRevisionRole = Literal["historical_mined", "selection_time"]
DirectoryIdentity = tuple[int, int, int, int, int, int]

MAX_HANDOFF_BYTES = 256 * 1024
MAX_TARGET_ENTRIES = 2_048
MAX_INSPECTED_DIRECTORIES = 256
MAX_INSPECTED_FILES = 512
MAX_GAPS = 128
MAX_DIRTY_ENTRIES = 256
MAX_GIT_ROOT_BYTES = 4_096
MAX_GIT_STATUS_BYTES = 256 * 1024
MAX_GIT_ERROR_BYTES = 16 * 1024
MAX_BULLET_CHARS = 2_000
MAX_SECTION_BULLETS = 128
MAX_MARKDOWN_LINES = 16_384
MAX_PUBLIC_TEXT = 4_096
MAX_REPO_ID_CHARS = 256
GIT_TIMEOUT_SECONDS = 5.0
QUERY_TIMEOUT_SECONDS = 30.0
MAX_QUERY_RESPONSE_BYTES = 12 * 1024 * 1024
MAX_QUERY_ERROR_BYTES = 16 * 1024
MAX_QUERY_RESULTS = 20
MAX_QUERY_REJECTIONS = 1_000
MAX_ACQUISITION_NEEDS = 7
MAX_OPPORTUNITY_TEXT = 4_096
MAX_OPPORTUNITY_RECORD_BYTES = 512 * 1024
MAX_EVIDENCE_ITEMS = 128
MAX_METHODOLOGY_IDS = 64
MAX_COMMAND_BYTES = 64 * 1024 * 1024
MAX_SIDECAR_BYTES = 768 * 1024 * 1024
MAX_MODEL_ENTRIES = 16_384
MAX_MODEL_BYTES = 16 * 1024 * 1024 * 1024
MAX_CLOSURE_METADATA_FILES = 128
MAX_CLOSURE_METADATA_BYTES = 8 * 1024 * 1024
MAX_INTERPRETER_LINKS = 16
HASH_PHASE_TIMEOUT_SECONDS = 15.0
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 50_000

_HASH_DEADLINE: ContextVar[float | None] = ContextVar(
    "opportunity_brief_hash_deadline",
    default=None,
)

TRUTH_FILE_NAMES = (
    "GOAL.md",
    "STANDARDS.md",
    "IMPLEMENT.md",
    "DECISIONS.md",
    "PROGRESS.md",
    "TASK_QUEUE.md",
    "AGENTS.md",
)
MAX_TRUTH_FILES = len(TRUTH_FILE_NAMES)
MAX_CONFLICTS = 64

_SKIPPED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        ".benchmarks",
        "node_modules",
        "vendor",
        "dependencies",
        "deps",
        "build",
        "dist",
        "generated_candidates",
        "generated_evidence",
        "hidden_evaluators",
        "run_artifacts",
    }
)

_TEXT_SUFFIXES = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".go",
        ".h",
        ".hpp",
        ".java",
        ".js",
        ".json",
        ".jsx",
        ".kt",
        ".md",
        ".py",
        ".rs",
        ".sh",
        ".swift",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
)

_GAP_PATTERN = re.compile(r"\b(?:TODO|FIXME|NotImplemented(?:Error)?)\b", re.IGNORECASE)
_DATED_HANDOFF_PATTERN = re.compile(
    r"^handoff[^/]*?(?P<date>\d{4}-\d{2}-\d{2})[^/]*\.md$",
    re.IGNORECASE,
)
_ATX_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_PLAIN_HEADING_PATTERN = re.compile(r"^\s*([A-Za-z][A-Za-z /&-]{1,48}):\s*$")
_SETEXT_PATTERN = re.compile(r"^\s{0,3}(?:={3,}|-{3,})\s*$")
_FENCE_PATTERN = re.compile(r"^\s{0,3}(`{3,}|~{3,}).*$")
_BULLET_PATTERN = re.compile(r"^(?:[-*+]\s+|\d{1,3}[.)]\s+)(.+?)\s*$")
_PRIORITY_PATTERN = re.compile(
    r"^\s*(?:\[\s*(P[0-2])\s*\]\s*:?\s*|\*{0,2}(P[0-2])\*{0,2}\s*:)\s*",
    re.IGNORECASE,
)
_CHECKOUT_CLAIM_PATTERN = re.compile(
    r"^\s*(?:[-*+]\s+)?\*{0,2}(?P<label>branch|revision|head|commit)"
    r"\*{0,2}\s*:(?P<value>.*)$",
    re.IGNORECASE,
)
_RAW_HTML_OPEN_PATTERN = re.compile(
    r"^\s{0,3}<(?P<tag>pre|script|style|textarea)(?:\s|>|$)",
    re.IGNORECASE,
)
_HEX_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REVISION_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_PYTHON_LAUNCHER_NAME_PATTERN = re.compile(r"^python(?:3(?:\.\d+)?)?$")
_PYTHON_TERMINAL_NAME_PATTERN = re.compile(r"^python(?P<version>3\.\d+)$")
_NEED_ID_PATTERN = re.compile(r"^need_[A-Za-z0-9._-]{4,64}$")
_RECORD_ID_PATTERN = re.compile(r"^opp_[0-9a-f]{32}$")
_SOURCE_REVISION_PATTERN = re.compile(
    r"^(?:[0-9a-f]{40}|[0-9a-f]{64}|git:(?:[0-9a-f]{40}|[0-9a-f]{64})|"
    r"sha256:[0-9a-f]{64})$"
)
_EXPLICITLY_NONOBSERVED_PREFIX = re.compile(
    r"^(?:intended|proposed|hypothetical)(?=\s|[:;,.!?\-\u2014\u2013]|$)",
    re.IGNORECASE,
)
_KNOWN_LICENSES = frozenset(
    {
        "0BSD",
        "AGPL-3.0-only",
        "AGPL-3.0-or-later",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "BSL-1.0",
        "CC0-1.0",
        "EPL-2.0",
        "GPL-2.0-only",
        "GPL-2.0-or-later",
        "GPL-3.0-only",
        "GPL-3.0-or-later",
        "ISC",
        "LGPL-2.1-only",
        "LGPL-2.1-or-later",
        "LGPL-3.0-only",
        "LGPL-3.0-or-later",
        "MIT",
        "MPL-2.0",
        "Unlicense",
        "Zlib",
    }
)

_SECTION_CATEGORIES: dict[str, NeedCategory] = {
    "blocker": "blocker",
    "blockers": "blocker",
    "risk": "risk",
    "risks": "risk",
    "unknown": "risk",
    "unknowns": "risk",
    "risk unknown": "risk",
    "risk unknowns": "risk",
    "risks unknown": "risk",
    "risks unknowns": "risk",
    "next action": "next_action",
    "next actions": "next_action",
    "open question": "open_question",
    "open questions": "open_question",
}
_CATEGORY_ORDER: dict[NeedCategory, int] = {
    "blocker": 0,
    "risk": 1,
    "next_action": 2,
    "open_question": 3,
}
_CATEGORY_LABELS: dict[NeedCategory, str] = {
    "blocker": "blocker",
    "risk": "risk or unknown",
    "next_action": "next action",
    "open_question": "open question",
}


class OpportunityBriefError(ValueError):
    """Raised when bounded WIP evidence cannot support safe inspection."""


def _checked_string(
    value: object,
    *,
    field: str,
    limit: int = MAX_PUBLIC_TEXT,
    allow_empty: bool = False,
    multiline: bool = False,
) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{field} must not be empty")
    if len(value) > limit:
        raise ValueError(f"{field} exceeds its bound")
    if _contains_unsafe_text(value, multiline=multiline):
        raise ValueError(f"{field} contains unsafe controls")
    return value


def _checked_canonical_string(
    value: object,
    *,
    field: str,
    limit: int = MAX_PUBLIC_TEXT,
) -> str:
    checked = _checked_string(value, field=field, limit=limit)
    if checked != checked.strip():
        raise ValueError(f"{field} must not have surrounding whitespace")
    return checked


def _contains_unsafe_text(value: str, *, multiline: bool = False) -> bool:
    for character in value:
        if multiline and character in "\t\n\r":
            continue
        if unicodedata.category(character).startswith("C"):
            return True
    return False


def _checked_repo_id(value: object) -> str:
    checked = _checked_string(value, field="target_repo_id", limit=MAX_REPO_ID_CHARS)
    if checked != checked.strip():
        raise ValueError("target_repo_id must not have surrounding whitespace")
    return checked


def _checked_tuple(value: object, *, field: str, item_limit: int) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be a tuple")
    checked = tuple(
        _checked_string(item, field=f"{field} item", limit=item_limit) for item in value
    )
    if len(checked) != len(set(checked)):
        raise ValueError(f"{field} must not contain duplicates")
    return checked


def _checked_relative_path(value: object, *, field: str) -> str:
    checked = _checked_string(value, field=field, limit=1_024)
    candidate = PurePosixPath(checked)
    if (
        candidate.is_absolute()
        or ".." in candidate.parts
        or "." in candidate.parts
        or "\\" in checked
        or candidate.as_posix() != checked
    ):
        raise ValueError(f"{field} must be a normalized relative path")
    return checked


@dataclass(frozen=True, slots=True)
class HandoffEvidence:
    """Exact descriptor-read evidence selected as the current handoff."""

    relative_path: str
    sha256: str
    text: str

    def __post_init__(self) -> None:
        _checked_relative_path(self.relative_path, field="relative_path")
        digest = _checked_string(self.sha256, field="sha256", limit=64)
        if not _HEX_DIGEST_PATTERN.fullmatch(digest):
            raise ValueError("sha256 must be a lowercase hexadecimal digest")
        text = _checked_string(
            self.text,
            field="text",
            limit=MAX_HANDOFF_BYTES,
            multiline=True,
        )
        if len(text.encode("utf-8")) > MAX_HANDOFF_BYTES:
            raise ValueError("text exceeds its byte bound")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
            raise ValueError("sha256 must equal the digest of UTF-8 text")


@dataclass(frozen=True, slots=True)
class WipSnapshot:
    """Deeply immutable snapshot of bounded target evidence.

    The authority flag records how :func:`inspect_wip_repository` was called.
    Exclusion consumers must require an explicit identity during inspection;
    they must not trust the flag on a manually constructed snapshot.
    """

    target_path: Path
    target_revision: str | None
    target_repo_id: str
    branch: str | None
    dirty_entries: tuple[str, ...]
    handoff: HandoffEvidence | None
    truth_files: tuple[str, ...]
    visible_gaps: tuple[str, ...]
    conflicts: tuple[str, ...]
    verification_status: VerificationStatus
    target_repo_id_is_exclusion_authoritative: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.target_path, Path):
            raise TypeError("target_path must be a pathlib.Path")
        if not self.target_path.is_absolute():
            raise ValueError("target_path must be absolute")
        _checked_string(str(self.target_path), field="target_path", limit=4_096)
        if self.target_revision is not None:
            revision = _checked_string(
                self.target_revision,
                field="target_revision",
                limit=64,
            )
            if not _REVISION_PATTERN.fullmatch(revision):
                raise ValueError("target_revision must be a complete hexadecimal object ID")
        _checked_repo_id(self.target_repo_id)
        if self.branch is not None:
            _checked_string(self.branch, field="branch", limit=256)
        dirty = _checked_tuple(self.dirty_entries, field="dirty_entries", item_limit=4_096)
        if len(dirty) > MAX_DIRTY_ENTRIES:
            raise ValueError("dirty_entries exceeds its bound")
        if self.handoff is not None and type(self.handoff) is not HandoffEvidence:
            raise TypeError("handoff must be HandoffEvidence or None")
        truth = _checked_tuple(self.truth_files, field="truth_files", item_limit=1_024)
        if len(truth) > MAX_TRUTH_FILES:
            raise ValueError("truth_files exceeds its cardinality bound")
        for item in truth:
            _checked_relative_path(item, field="truth_files item")
        gaps = _checked_tuple(self.visible_gaps, field="visible_gaps", item_limit=4_096)
        if len(gaps) > MAX_GAPS:
            raise ValueError("visible_gaps exceeds its bound")
        conflicts = _checked_tuple(self.conflicts, field="conflicts", item_limit=4_096)
        if len(conflicts) > MAX_CONFLICTS:
            raise ValueError("conflicts exceeds its cardinality bound")
        if self.verification_status != "not_run":
            raise ValueError("verification_status must be 'not_run'")
        if type(self.target_repo_id_is_exclusion_authoritative) is not bool:
            raise TypeError("target_repo_id_is_exclusion_authoritative must be a bool")


@dataclass(frozen=True, slots=True)
class NeedTheme:
    """A source-linked need theme, never an implementation plan."""

    need_id: str
    category: NeedCategory
    problem: str
    desired_improvement: str
    existing_evidence: str
    gap: str
    query_text: str
    handoff_span: str
    implementation_steps: tuple[()] = ()

    def __post_init__(self) -> None:
        if type(self.category) is not str or self.category not in _CATEGORY_ORDER:
            raise ValueError("category is not supported")
        for field in (
            "problem",
            "desired_improvement",
            "existing_evidence",
            "gap",
            "query_text",
            "handoff_span",
        ):
            _checked_string(getattr(self, field), field=field, limit=MAX_PUBLIC_TEXT)
        if not _normalize_span(self.problem):
            raise ValueError("problem must have a canonical normalized problem identity")
        need_id = _checked_string(self.need_id, field="need_id", limit=69)
        if not _NEED_ID_PATTERN.fullmatch(need_id):
            raise ValueError("need_id has an invalid format")
        if need_id != _canonical_need_id(self.category, self.problem):
            raise ValueError("need_id must equal the canonical category and problem identity")
        if type(self.implementation_steps) is not tuple or self.implementation_steps:
            raise ValueError("implementation_steps must be the empty tuple")


@dataclass(frozen=True, slots=True)
class OpportunityEffect:
    """Validated observed-effect projection from an opportunity record."""

    status: EffectStatus
    text: str

    def __post_init__(self) -> None:
        if type(self.status) is not str or self.status not in {
            "observed",
            "intended",
            "negative",
        }:
            raise ValueError("observed effect status is unsupported")
        _checked_canonical_string(
            self.text,
            field="observed effect text",
            limit=MAX_OPPORTUNITY_TEXT,
        )
        if self.status == "observed" and _EXPLICITLY_NONOBSERVED_PREFIX.search(
            self.text
        ):
            raise ValueError("observed effect text describes a non-observed effect")


@dataclass(frozen=True, slots=True)
class OpportunityEvidence:
    """Immutable, complete provenance and license evidence for a candidate."""

    source_repo_id: str
    source_repo_name: str
    source_revision: str
    source_revision_role: SourceRevisionRole
    license_type: str
    license_sha256: str
    source_files: tuple[str, ...]
    source_symbols: tuple[str, ...]
    source_sha256: tuple[str, ...]

    def __post_init__(self) -> None:
        _checked_canonical_string(self.source_repo_id, field="source_repo_id", limit=256)
        _checked_canonical_string(
            self.source_repo_name,
            field="source_repo_name",
            limit=256,
        )
        revision = _checked_canonical_string(
            self.source_revision,
            field="source_revision",
            limit=80,
        )
        if _SOURCE_REVISION_PATTERN.fullmatch(revision) is None:
            raise ValueError("source_revision is not an immutable identity")
        if type(self.source_revision_role) is not str or self.source_revision_role not in {
            "historical_mined",
            "selection_time",
        }:
            raise ValueError("source_revision_role is unsupported")
        license_type = _checked_canonical_string(
            self.license_type,
            field="license_type",
            limit=64,
        )
        if license_type not in _KNOWN_LICENSES:
            raise ValueError("license_type is unsupported")
        license_digest = _checked_canonical_string(
            self.license_sha256,
            field="license_sha256",
            limit=64,
        )
        if _HEX_DIGEST_PATTERN.fullmatch(license_digest) is None:
            raise ValueError("license_sha256 must be a lowercase SHA-256 digest")
        _validate_evidence_tuple(
            self.source_files,
            field="source_files",
            limit=1_024,
        )
        _validate_evidence_tuple(
            self.source_symbols,
            field="source_symbols",
            limit=512,
        )
        _validate_digest_tuple(self.source_sha256, field="source_sha256")
        if not self.source_files or not self.source_symbols or not self.source_sha256:
            raise ValueError("admitted opportunity evidence must be complete")
        if len(self.source_sha256) != len(self.source_files):
            raise ValueError("source_sha256 must correspond to source_files")
        for source_file in self.source_files:
            _checked_relative_path(source_file, field="source_files item")
        if any(_HEX_DIGEST_PATTERN.fullmatch(item) is None for item in self.source_sha256):
            raise ValueError("source_sha256 contains a malformed digest")


@dataclass(frozen=True, slots=True)
class OpportunityRecordReceipt:
    """The complete six-part opportunity plus its admission provenance."""

    problem: str
    mechanism: str
    observed_effect: OpportunityEffect
    context: str
    boundary: str
    evidence: OpportunityEvidence
    evidence_state: Literal["admitted"]
    source_methodology_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("problem", "mechanism", "context", "boundary"):
            _checked_canonical_string(
                getattr(self, field_name),
                field=field_name,
                limit=MAX_OPPORTUNITY_TEXT,
            )
        if type(self.observed_effect) is not OpportunityEffect:
            raise TypeError("observed_effect must be an OpportunityEffect")
        if type(self.evidence) is not OpportunityEvidence:
            raise TypeError("evidence must be OpportunityEvidence")
        if type(self.evidence_state) is not str or self.evidence_state != "admitted":
            raise ValueError("query candidates must be admitted records")
        _validate_evidence_tuple(
            self.source_methodology_ids,
            field="source_methodology_ids",
            limit=256,
            maximum=MAX_METHODOLOGY_IDS,
        )
        if not self.source_methodology_ids:
            raise ValueError("source_methodology_ids must not be empty")

    def to_mapping(self) -> dict[str, object]:
        """Return the canonical Task 2 record projection."""

        return {
            "problem": self.problem,
            "mechanism": self.mechanism,
            "observed_effect": {
                "status": self.observed_effect.status,
                "text": self.observed_effect.text,
            },
            "context": self.context,
            "boundary": self.boundary,
            "evidence": {
                "source_repo_id": self.evidence.source_repo_id,
                "source_repo_name": self.evidence.source_repo_name,
                "source_revision": self.evidence.source_revision,
                "source_revision_role": self.evidence.source_revision_role,
                "license_type": self.evidence.license_type,
                "license_sha256": self.evidence.license_sha256,
                "source_files": list(self.evidence.source_files),
                "source_symbols": list(self.evidence.source_symbols),
                "source_sha256": list(self.evidence.source_sha256),
            },
            "evidence_state": self.evidence_state,
            "source_methodology_ids": list(self.source_methodology_ids),
        }


@dataclass(frozen=True, slots=True)
class CandidateMatch:
    """Per-need query ranks retained for a deduplicated candidate."""

    need_id: str
    fts_rank: int | None
    semantic_rank: int | None
    rrf_score: float

    def __post_init__(self) -> None:
        need_id = _checked_string(self.need_id, field="need_id", limit=69)
        if _NEED_ID_PATTERN.fullmatch(need_id) is None:
            raise ValueError("need_id has an invalid format")
        for name in ("fts_rank", "semantic_rank"):
            rank = getattr(self, name)
            if rank is not None and (
                isinstance(rank, bool) or type(rank) is not int or not 1 <= rank <= 1_000
            ):
                raise ValueError(f"{name} is outside its rank bound")
        if self.fts_rank is None and self.semantic_rank is None:
            raise ValueError("a candidate must have at least one component rank")
        if type(self.rrf_score) is not float:
            raise TypeError("rrf_score must be a float")
        expected = sum(
            1.0 / (60 + rank)
            for rank in (self.fts_rank, self.semantic_rank)
            if rank is not None
        )
        if not math.isfinite(float(self.rrf_score)) or not math.isclose(
            float(self.rrf_score),
            expected,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise ValueError("rrf_score does not match the component ranks")


@dataclass(frozen=True, slots=True)
class OpportunityCandidate:
    """A cross-need deduplicated, source-grounded opportunity candidate."""

    record_id: str
    record: OpportunityRecordReceipt
    matches: tuple[CandidateMatch, ...]

    def __post_init__(self) -> None:
        record_id = _checked_string(self.record_id, field="record_id", limit=36)
        if _RECORD_ID_PATTERN.fullmatch(record_id) is None:
            raise ValueError("record_id has an invalid format")
        if type(self.record) is not OpportunityRecordReceipt:
            raise TypeError("record must be an OpportunityRecordReceipt")
        if type(self.matches) is not tuple or not self.matches:
            raise ValueError("matches must be a non-empty tuple")
        if any(type(match) is not CandidateMatch for match in self.matches):
            raise TypeError("matches must contain CandidateMatch values")
        if len({match.need_id for match in self.matches}) != len(self.matches):
            raise ValueError("matches must not repeat a need_id")
        if record_id != _record_id(self.record):
            raise ValueError("record_id does not match the canonical record")


@dataclass(frozen=True, slots=True)
class InterpreterSymlinkReceipt:
    """One lexical link in the absolute Python-interpreter chain."""

    path: Path
    identity: DirectoryIdentity
    target: str

    def __post_init__(self) -> None:
        _validate_absolute_path(self.path, field="interpreter symlink path")
        _validate_identity(self.identity, field="interpreter symlink")
        _checked_canonical_string(
            self.target,
            field="interpreter symlink target",
            limit=4_096,
        )


@dataclass(frozen=True, slots=True)
class ExecutionClosureReceipt:
    """Auditable binding for the launcher and every executable CAM dependency."""

    launcher_kind: Literal["python", "native"]
    launcher_path: Path
    launcher_identity: DirectoryIdentity
    launcher_sha256: str
    interpreter_path: Path | None
    interpreter_symlink_chain: tuple[InterpreterSymlinkReceipt, ...]
    resolved_interpreter_path: Path | None
    resolved_interpreter_identity: DirectoryIdentity | None
    interpreter_sha256: str | None
    python_home: Path | None
    python_home_identity: DirectoryIdentity | None
    python_runtime_library_path: Path | None
    python_runtime_library_identity: DirectoryIdentity | None
    python_runtime_library_sha256: str | None
    editable_site_packages: Path | None
    editable_site_packages_identity: DirectoryIdentity | None
    editable_metadata_sha256: str | None
    cam_source_root: Path | None
    cam_source_root_identity: DirectoryIdentity | None
    cam_source_revision: str | None
    cam_source_branch: str | None
    cam_source_dirty_entries: tuple[str, ...]
    cam_source_sha256: str | None
    sha256: str = dataclass_field(init=False)

    def __post_init__(self) -> None:
        if self.launcher_kind not in {"python", "native"}:
            raise ValueError("execution closure launcher kind is unsupported")
        _validate_absolute_path(self.launcher_path, field="execution closure launcher")
        _validate_artifact_binding(
            self.launcher_identity,
            self.launcher_sha256,
            field="execution closure launcher",
            require_single_link=True,
        )
        _validate_typed_tuple(
            self.interpreter_symlink_chain,
            field="interpreter symlink chain",
            item_type=InterpreterSymlinkReceipt,
            maximum=MAX_INTERPRETER_LINKS,
        )
        for link in self.interpreter_symlink_chain:
            link.__post_init__()
        if type(self.cam_source_dirty_entries) is not tuple:
            raise TypeError("CAM source dirty entries must be a tuple")
        if len(self.cam_source_dirty_entries) > MAX_DIRTY_ENTRIES:
            raise ValueError("CAM source dirty entries exceed their bound")
        for entry in self.cam_source_dirty_entries:
            _checked_canonical_string(entry, field="CAM source dirty entry", limit=4_096)
        if self.cam_source_dirty_entries != tuple(
            sorted(set(self.cam_source_dirty_entries))
        ):
            raise ValueError("CAM source dirty entries must be sorted and unique")
        if self.launcher_kind == "native":
            if any(
                value is not None
                for value in (
                    self.interpreter_path,
                    self.resolved_interpreter_path,
                    self.resolved_interpreter_identity,
                    self.interpreter_sha256,
                    self.python_home,
                    self.python_home_identity,
                    self.python_runtime_library_path,
                    self.python_runtime_library_identity,
                    self.python_runtime_library_sha256,
                    self.editable_site_packages,
                    self.editable_site_packages_identity,
                    self.editable_metadata_sha256,
                    self.cam_source_root,
                    self.cam_source_root_identity,
                    self.cam_source_revision,
                    self.cam_source_branch,
                    self.cam_source_sha256,
                )
            ) or self.interpreter_symlink_chain or self.cam_source_dirty_entries:
                raise ValueError("native execution closures cannot claim Python artifacts")
        else:
            self._validate_python_closure()
        object.__setattr__(self, "sha256", _execution_closure_public_digest(self))

    def _validate_python_closure(self) -> None:
        _validate_absolute_path(self.interpreter_path, field="Python interpreter path")
        _validate_absolute_path(
            self.resolved_interpreter_path,
            field="resolved Python interpreter path",
        )
        _validate_artifact_binding(
            self.resolved_interpreter_identity,
            self.interpreter_sha256,
            field="resolved Python interpreter",
            require_single_link=True,
        )
        runtime_values = (
            self.python_home,
            self.python_home_identity,
            self.python_runtime_library_path,
            self.python_runtime_library_identity,
            self.python_runtime_library_sha256,
        )
        if any(value is not None for value in runtime_values):
            if not all(value is not None for value in runtime_values):
                raise ValueError("Python runtime closure fields must be complete")
            _validate_absolute_path(self.python_home, field="Python runtime home")
            _validate_identity(self.python_home_identity, field="Python runtime home")
            _validate_absolute_path(
                self.python_runtime_library_path,
                field="Python runtime library",
            )
            _validate_artifact_binding(
                self.python_runtime_library_identity,
                self.python_runtime_library_sha256,
                field="Python runtime library",
                require_single_link=True,
            )
        metadata_values = (
            self.editable_site_packages,
            self.editable_site_packages_identity,
            self.editable_metadata_sha256,
        )
        if any(value is not None for value in metadata_values):
            if not all(value is not None for value in metadata_values):
                raise ValueError("editable CAM metadata closure fields must be complete")
            _validate_absolute_path(
                self.editable_site_packages,
                field="editable CAM site-packages",
            )
            _validate_identity(
                self.editable_site_packages_identity,
                field="editable CAM site-packages",
            )
            _validate_digest(
                self.editable_metadata_sha256,
                field="editable metadata digest",
            )
        source_values = (
            self.cam_source_root,
            self.cam_source_root_identity,
            self.cam_source_revision,
            self.cam_source_sha256,
        )
        if any(value is not None for value in source_values):
            if not all(value is not None for value in source_values):
                raise ValueError("CAM source closure fields must be complete")
            _validate_absolute_path(self.cam_source_root, field="CAM source root")
            _validate_identity(self.cam_source_root_identity, field="CAM source root")
            if (
                type(self.cam_source_revision) is not str
                or _REVISION_PATTERN.fullmatch(self.cam_source_revision) is None
            ):
                raise ValueError("CAM source revision must be an immutable Git identity")
            if self.cam_source_branch is not None:
                _checked_canonical_string(
                    self.cam_source_branch,
                    field="CAM source branch",
                    limit=256,
                )
            _validate_digest(self.cam_source_sha256, field="CAM source digest")
        elif self.cam_source_branch is not None or self.cam_source_dirty_entries:
            raise ValueError("CAM source state requires a CAM source root")


@dataclass(frozen=True, slots=True)
class AcquisitionCall:
    """Auditable query invocation without subprocess output or secrets."""

    need_id: str
    query: str
    argv: tuple[str, ...]
    executable_identity: DirectoryIdentity
    executable_sha256: str
    sidecar_identity: DirectoryIdentity
    sidecar_sha256: str
    semantic_model_identity: DirectoryIdentity
    semantic_model_sha256: str
    execution_closure_sha256: str
    status: QueryStatus
    result_count: int
    rejection_count: int

    def __post_init__(self) -> None:
        if _NEED_ID_PATTERN.fullmatch(
            _checked_string(self.need_id, field="need_id", limit=69)
        ) is None:
            raise ValueError("need_id has an invalid format")
        _checked_canonical_string(self.query, field="query", limit=MAX_PUBLIC_TEXT)
        _validate_evidence_tuple(
            self.argv,
            field="argv",
            limit=4_096,
            maximum=12,
            canonical=False,
        )
        if (
            len(self.argv) != 12
            or not Path(self.argv[0]).is_absolute()
            or self.argv[1] != "opportunity-query"
            or self.argv[2] != self.query
            or self.argv[3] != "--db"
            or not Path(self.argv[4]).is_absolute()
            or self.argv[5] != "--target-repo-id"
            or not self.argv[6]
            or self.argv[7] != "--semantic-model-path"
            or not Path(self.argv[8]).is_absolute()
            or self.argv[9:] != ("--limit", "20", "--json")
        ):
            raise ValueError("argv is not the supported opportunity-query invocation")
        _validate_artifact_binding(
            self.executable_identity,
            self.executable_sha256,
            field="executable",
            require_single_link=True,
        )
        _validate_artifact_binding(
            self.sidecar_identity,
            self.sidecar_sha256,
            field="sidecar",
            require_single_link=True,
        )
        _validate_artifact_binding(
            self.semantic_model_identity,
            self.semantic_model_sha256,
            field="semantic model",
            require_single_link=False,
        )
        _validate_digest(
            self.execution_closure_sha256,
            field="execution closure digest",
        )
        if self.status not in {"ok", "query_failed"}:
            raise ValueError("query call status is unsupported")
        for name, maximum in (
            ("result_count", MAX_QUERY_RESULTS),
            ("rejection_count", MAX_QUERY_REJECTIONS),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or type(value) is not int or not 0 <= value <= maximum:
                raise ValueError(f"{name} is outside its bound")
        if self.status == "query_failed" and (self.result_count or self.rejection_count):
            raise ValueError("failed query calls cannot claim results or rejections")


@dataclass(frozen=True, slots=True)
class AcquisitionGap:
    """Stable, sanitized record of one bounded query failure."""

    need_id: str
    reason: Literal["query_failed"]

    def __post_init__(self) -> None:
        if _NEED_ID_PATTERN.fullmatch(
            _checked_string(self.need_id, field="need_id", limit=69)
        ) is None:
            raise ValueError("need_id has an invalid format")
        if self.reason != "query_failed":
            raise ValueError("acquisition gap reason is unsupported")


@dataclass(frozen=True, slots=True)
class AcquisitionRejection:
    """Auditable rejection emitted by the read-only query command."""

    need_id: str
    record_id: str
    reason: str

    def __post_init__(self) -> None:
        if _NEED_ID_PATTERN.fullmatch(
            _checked_string(self.need_id, field="need_id", limit=69)
        ) is None:
            raise ValueError("need_id has an invalid format")
        if _RECORD_ID_PATTERN.fullmatch(
            _checked_string(self.record_id, field="record_id", limit=36)
        ) is None:
            raise ValueError("rejection record_id has an invalid format")
        _checked_canonical_string(
            self.reason,
            field="rejection reason",
            limit=MAX_PUBLIC_TEXT,
        )


@dataclass(frozen=True, slots=True)
class AcquisitionReceipt:
    """Frozen receipt for bounded, local-only opportunity acquisition."""

    target_repo_id: str
    model_id: str
    cam_command: Path
    executable_identity: DirectoryIdentity
    executable_sha256: str
    sidecar: Path
    sidecar_identity: DirectoryIdentity
    sidecar_sha256: str
    semantic_model_path: Path
    semantic_model_identity: DirectoryIdentity
    semantic_model_sha256: str
    execution_closure: ExecutionClosureReceipt
    calls: tuple[AcquisitionCall, ...]
    candidates: tuple[OpportunityCandidate, ...]
    rejections: tuple[AcquisitionRejection, ...]
    gaps: tuple[AcquisitionGap, ...]
    provider_calls: Literal[0] = 0
    mining_calls: Literal[0] = 0

    def __post_init__(self) -> None:
        _checked_repo_id(self.target_repo_id)
        model_id = _checked_canonical_string(
            self.model_id,
            field="model_id",
            limit=1_024,
        )
        if not Path(model_id).is_absolute():
            raise ValueError("model_id must be an absolute local path")
        for path, field in (
            (self.cam_command, "cam_command"),
            (self.sidecar, "sidecar"),
            (self.semantic_model_path, "semantic_model_path"),
        ):
            if not isinstance(path, Path) or not path.is_absolute():
                raise ValueError(f"{field} must be an absolute pathlib.Path")
            _checked_canonical_string(str(path), field=field, limit=4_096)
        if os.path.realpath(self.semantic_model_path) != self.model_id:
            raise ValueError("model_id must match semantic_model_path identity")
        _validate_artifact_binding(
            self.executable_identity,
            self.executable_sha256,
            field="executable",
            require_single_link=True,
        )
        _validate_artifact_binding(
            self.sidecar_identity,
            self.sidecar_sha256,
            field="sidecar",
            require_single_link=True,
        )
        _validate_artifact_binding(
            self.semantic_model_identity,
            self.semantic_model_sha256,
            field="semantic model",
            require_single_link=False,
        )
        if type(self.execution_closure) is not ExecutionClosureReceipt:
            raise TypeError("execution_closure must be an ExecutionClosureReceipt")
        self.execution_closure.__post_init__()
        _validate_typed_tuple(
            self.calls,
            field="calls",
            item_type=AcquisitionCall,
            maximum=MAX_ACQUISITION_NEEDS,
        )
        _validate_typed_tuple(
            self.candidates,
            field="candidates",
            item_type=OpportunityCandidate,
            maximum=MAX_ACQUISITION_NEEDS * MAX_QUERY_RESULTS,
        )
        _validate_typed_tuple(
            self.rejections,
            field="rejections",
            item_type=AcquisitionRejection,
            maximum=MAX_ACQUISITION_NEEDS * MAX_QUERY_REJECTIONS,
        )
        _validate_typed_tuple(
            self.gaps,
            field="gaps",
            item_type=AcquisitionGap,
            maximum=MAX_ACQUISITION_NEEDS,
        )
        for call in self.calls:
            call.__post_init__()
        for candidate in self.candidates:
            candidate.__post_init__()
            candidate.record.__post_init__()
            candidate.record.observed_effect.__post_init__()
            candidate.record.evidence.__post_init__()
            for match in candidate.matches:
                match.__post_init__()
        for rejection in self.rejections:
            rejection.__post_init__()
        for gap in self.gaps:
            gap.__post_init__()
        call_ids = tuple(call.need_id for call in self.calls)
        if len(call_ids) != len(set(call_ids)):
            raise ValueError("calls must not repeat a need_id")
        if len({candidate.record_id for candidate in self.candidates}) != len(
            self.candidates
        ):
            raise ValueError("candidates must not repeat a record_id")
        call_status = {call.need_id: call.status for call in self.calls}
        call_order = {call.need_id: index for index, call in enumerate(self.calls)}
        if any(call.argv[6] != self.target_repo_id for call in self.calls):
            raise ValueError("query call target identity does not match the receipt")
        if any(
            call.argv[0] != str(self.cam_command)
            or call.argv[4] != str(self.sidecar)
            or call.argv[8] != str(self.semantic_model_path)
            or call.executable_identity != self.executable_identity
            or call.executable_sha256 != self.executable_sha256
            or call.sidecar_identity != self.sidecar_identity
            or call.sidecar_sha256 != self.sidecar_sha256
            or call.semantic_model_identity != self.semantic_model_identity
            or call.semantic_model_sha256 != self.semantic_model_sha256
            or call.execution_closure_sha256 != self.execution_closure.sha256
            for call in self.calls
        ):
            raise ValueError("query call artifact identity or digest does not match receipt")
        if any(
            candidate.record.evidence.source_repo_id == self.target_repo_id
            for candidate in self.candidates
        ):
            raise ValueError("candidate source identity must not equal the target")
        if any(
            match.need_id not in call_status or call_status[match.need_id] != "ok"
            for candidate in self.candidates
            for match in candidate.matches
        ):
            raise ValueError("candidate matches must identify successful query calls")
        if any(
            tuple(call_order[match.need_id] for match in candidate.matches)
            != tuple(sorted(call_order[match.need_id] for match in candidate.matches))
            for candidate in self.candidates
        ):
            raise ValueError("candidate matches must preserve query-call order")
        if any(
            rejection.need_id not in call_status
            or call_status[rejection.need_id] != "ok"
            for rejection in self.rejections
        ):
            raise ValueError("rejections must identify successful query calls")
        gap_ids = tuple(gap.need_id for gap in self.gaps)
        if len(gap_ids) != len(set(gap_ids)) or any(
            call_status.get(gap_id) != "query_failed" for gap_id in gap_ids
        ):
            raise ValueError("gaps must identify unique failed query calls")
        failed_ids = {
            call.need_id for call in self.calls if call.status == "query_failed"
        }
        if failed_ids != set(gap_ids):
            raise ValueError("each failed query call must have one query_failed gap")
        for call in self.calls:
            candidate_count = sum(
                call.need_id in {match.need_id for match in candidate.matches}
                for candidate in self.candidates
            )
            rejection_count = sum(
                rejection.need_id == call.need_id for rejection in self.rejections
            )
            if (
                candidate_count != call.result_count
                or rejection_count != call.rejection_count
            ):
                raise ValueError("query call counts do not match receipt contents")
        if (
            type(self.provider_calls) is not int
            or type(self.mining_calls) is not int
            or self.provider_calls != 0
            or self.mining_calls != 0
        ):
            raise ValueError("acquisition must not use providers or mining")


def _validate_evidence_tuple(
    value: object,
    *,
    field: str,
    limit: int,
    maximum: int = MAX_EVIDENCE_ITEMS,
    canonical: bool = True,
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be a tuple")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds its item bound")
    checked = tuple(
        _checked_canonical_string(item, field=f"{field} item", limit=limit)
        for item in value
    )
    if canonical and (
        checked != tuple(sorted(checked)) or len(checked) != len(set(checked))
    ):
        raise ValueError(f"{field} must be sorted and unique")


def _validate_digest_tuple(value: object, *, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be a tuple")
    if len(value) > MAX_EVIDENCE_ITEMS:
        raise ValueError(f"{field} exceeds its item bound")
    for digest in value:
        checked = _checked_canonical_string(digest, field=f"{field} item", limit=64)
        if _HEX_DIGEST_PATTERN.fullmatch(checked) is None:
            raise ValueError(f"{field} contains a malformed digest")


def _validate_digest(value: object, *, field: str) -> None:
    checked = _checked_canonical_string(value, field=field, limit=64)
    if _HEX_DIGEST_PATTERN.fullmatch(checked) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def _validate_artifact_binding(
    identity: object,
    digest: object,
    *,
    field: str,
    require_single_link: bool,
) -> None:
    if type(identity) is not tuple or len(identity) != 6:
        raise TypeError(f"{field} identity must be a six-integer tuple")
    if any(type(item) is not int or item < 0 for item in identity):
        raise ValueError(f"{field} identity is malformed")
    if require_single_link and identity[2] != 1:
        raise ValueError(f"{field} identity must be single-link")
    checked = _checked_canonical_string(digest, field=f"{field} digest", limit=64)
    if _HEX_DIGEST_PATTERN.fullmatch(checked) is None:
        raise ValueError(f"{field} digest must be a lowercase SHA-256 digest")


def _validate_identity(identity: object, *, field: str) -> None:
    if type(identity) is not tuple or len(identity) != 6:
        raise TypeError(f"{field} identity must be a six-integer tuple")
    if any(type(item) is not int or item < 0 for item in identity):
        raise ValueError(f"{field} identity is malformed")


def _validate_absolute_path(path: object, *, field: str) -> None:
    if not isinstance(path, Path) or not path.is_absolute():
        raise ValueError(f"{field} must be an absolute pathlib.Path")
    _checked_canonical_string(str(path), field=field, limit=4_096)


def _validate_typed_tuple(
    value: object,
    *,
    field: str,
    item_type: type,
    maximum: int,
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be a tuple")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds its item bound")
    if any(type(item) is not item_type for item in value):
        raise TypeError(f"{field} contains an invalid item")


@dataclass(frozen=True, slots=True)
class _Candidate:
    category: NeedCategory
    priority: int
    source_order: int
    handoff_span: str
    problem: str
    normalized_problem: str


@dataclass(frozen=True, slots=True)
class _GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True, slots=True)
class _FileArtifactSnapshot:
    path: Path
    identity: DirectoryIdentity
    sha256: str


@dataclass(frozen=True, slots=True)
class _ModelManifestEntry:
    relative_path: str
    kind: Literal["directory", "file"]
    identity: DirectoryIdentity
    sha256: str


@dataclass(frozen=True, slots=True)
class _ModelArtifactSnapshot:
    path: Path
    identity: DirectoryIdentity
    entries: tuple[_ModelManifestEntry, ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class _SymlinkSnapshot:
    path: Path
    identity: DirectoryIdentity
    target: str


@dataclass(frozen=True, slots=True)
class _MetadataSnapshot:
    site_packages: Path
    site_packages_identity: DirectoryIdentity
    files: tuple[_FileArtifactSnapshot, ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class _PythonRuntimeSnapshot:
    home: Path
    home_identity: DirectoryIdentity
    library: _FileArtifactSnapshot


@dataclass(frozen=True, slots=True)
class _CamSourceSnapshot:
    root: Path
    root_identity: DirectoryIdentity
    git: _GitSnapshot
    manifest: _ModelArtifactSnapshot


@dataclass(frozen=True, slots=True)
class _ExecutionClosureSnapshot:
    receipt: ExecutionClosureReceipt
    lexical_interpreter: Path | None
    interpreter_links: tuple[_SymlinkSnapshot, ...]
    interpreter: _FileArtifactSnapshot | None
    runtime: _PythonRuntimeSnapshot | None
    metadata: _MetadataSnapshot | None
    source: _CamSourceSnapshot | None


@dataclass(frozen=True, slots=True)
class _PinnedCommandSnapshot:
    launcher: _FileArtifactSnapshot
    interpreter: _FileArtifactSnapshot | None
    runtime_library: _FileArtifactSnapshot | None
    python_home: Path | None
    python_path: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class _GitSnapshot:
    revision: str | None
    branch: str | None
    dirty_entries: tuple[str, ...]


@dataclass(slots=True)
class _WalkBudget:
    entries: int = 0
    directories: int = 0
    files: int = 0


def inspect_wip_repository(
    target_path: Path,
    *,
    target_repo_id: str | None = None,
    require_exclusion_identity: bool = False,
) -> WipSnapshot:
    """Inspect a local target through bounded, no-write evidence paths."""

    try:
        if not isinstance(target_path, Path):
            raise TypeError("target_path must be a pathlib.Path")
        _checked_string(os.fspath(target_path), field="target path", limit=4_096)
    except (TypeError, ValueError, OSError) as error:
        raise OpportunityBriefError("target path contains unsafe controls") from error
    try:
        target = target_path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise OpportunityBriefError("target path must be an existing directory") from error
    try:
        _checked_string(str(target), field="target path", limit=4_096)
    except (TypeError, ValueError) as error:
        raise OpportunityBriefError("target path contains unsafe controls") from error

    if type(require_exclusion_identity) is not bool:
        raise TypeError("require_exclusion_identity must be a bool")
    if require_exclusion_identity and target_repo_id is None:
        raise OpportunityBriefError(
            "source exclusion requires an explicit shared target_repo_id"
        )
    repository_id = (
        _default_target_repo_id(target)
        if target_repo_id is None
        else _checked_repo_id(target_repo_id)
    )
    root_descriptor: int | None = None
    try:
        root_descriptor, root_identity = _open_pinned_root(target)
        truth_files = _read_truth_file_names(root_descriptor)
        handoff = _read_selected_handoff(root_descriptor, truth_files)
        _assert_root_identity(target, root_descriptor, root_identity)
        git_snapshot = _read_git_snapshot(
            target,
            root_descriptor,
            root_identity,
        )
        _assert_root_identity(target, root_descriptor, root_identity)
        visible_gaps = _read_visible_gaps(root_descriptor)
        _assert_root_identity(target, root_descriptor, root_identity)
        conflicts = _find_checkout_conflicts(
            handoff,
            revision=git_snapshot.revision,
            branch=git_snapshot.branch,
        )
        return WipSnapshot(
            target_path=target,
            target_revision=git_snapshot.revision,
            target_repo_id=repository_id,
            branch=git_snapshot.branch,
            dirty_entries=git_snapshot.dirty_entries,
            handoff=handoff,
            truth_files=truth_files,
            visible_gaps=visible_gaps,
            conflicts=conflicts,
            verification_status="not_run",
            target_repo_id_is_exclusion_authoritative=target_repo_id is not None,
        )
    finally:
        if root_descriptor is not None:
            os.close(root_descriptor)


def extract_need_themes(
    snapshot: WipSnapshot,
    *,
    minimum: int = 3,
    maximum: int = 7,
) -> tuple[NeedTheme, ...]:
    """Extract three to seven ranked needs from allowed handoff sections."""

    if not isinstance(snapshot, WipSnapshot):
        raise TypeError("snapshot must be a WipSnapshot")
    _validate_need_bounds(minimum, maximum)
    if snapshot.handoff is None:
        raise OpportunityBriefError("a handoff or truth file is required to extract needs")

    candidates = _parse_candidates(snapshot.handoff.text)
    ranked = sorted(
        candidates,
        key=lambda item: (item.priority, _CATEGORY_ORDER[item.category], item.source_order),
    )
    selected: list[_Candidate] = []
    seen: set[str] = set()
    for candidate in ranked:
        if candidate.normalized_problem in seen:
            continue
        seen.add(candidate.normalized_problem)
        selected.append(candidate)
        if len(selected) == maximum:
            break
    if len(selected) < minimum:
        raise OpportunityBriefError(
            f"handoff must contain at least {minimum} unique needs in allowed sections"
        )
    return tuple(_to_need_theme(candidate) for candidate in selected)


@dataclass(frozen=True, slots=True)
class _ValidatedQueryResponse:
    results: tuple[tuple[str, OpportunityRecordReceipt, CandidateMatch], ...]
    rejections: tuple[AcquisitionRejection, ...]


def acquire_opportunities(
    needs: tuple[NeedTheme, ...],
    *,
    cam_command: Path,
    sidecar: Path,
    semantic_model_path: Path,
    target_repo_id: str,
) -> AcquisitionReceipt:
    """Acquire local sidecar candidates once for each stable unique need.

    ``target_repo_id`` is deliberately required. Callers may pass an identity
    supplied to :func:`inspect_wip_repository` with
    ``require_exclusion_identity=True``, or another explicitly validated shared
    identity. This function never accepts or trusts a snapshot authority flag.
    """

    unique_needs = _unique_acquisition_needs(needs)
    target = _checked_repo_id(target_repo_id)
    command = _validate_acquisition_path(
        cam_command,
        field="cam command",
        kind="executable",
    )
    database = _validate_acquisition_path(sidecar, field="sidecar", kind="file")
    if database.name.casefold() == "claw.db":
        raise OpportunityBriefError("refusing to query canonical claw.db")
    model_path = _validate_acquisition_path(
        semantic_model_path,
        field="semantic model path",
        kind="directory",
    )
    try:
        model_id = str(model_path.resolve(strict=True))
    except (OSError, RuntimeError, ValueError) as error:
        raise OpportunityBriefError("semantic model path identity is unavailable") from error
    executable_descriptor: int | None = None
    pinned_directory: Path | None = None
    try:
        hash_token = _HASH_DEADLINE.set(
            time.monotonic() + HASH_PHASE_TIMEOUT_SECONDS
        )
        try:
            executable_descriptor, executable = _pin_executable(command)
            closure = _snapshot_execution_closure(
                command,
                executable_descriptor,
                executable,
            )
            pinned_directory, pinned_snapshot = _materialize_pinned_executable(
                executable_descriptor,
                executable,
                closure,
            )
            sidecar_snapshot = _snapshot_single_link_file(
                database,
                label="sidecar",
                byte_limit=MAX_SIDECAR_BYTES,
            )
            model_snapshot = _snapshot_model_directory(model_path)
        finally:
            _HASH_DEADLINE.reset(hash_token)
        calls: list[AcquisitionCall] = []
        gaps: list[AcquisitionGap] = []
        rejections: list[AcquisitionRejection] = []
        candidates: list[OpportunityCandidate] = []
        candidate_indexes: dict[str, int] = {}
        for need in unique_needs:
            argv = (
                str(command),
                "opportunity-query",
                need.query_text,
                "--db",
                str(database),
                "--target-repo-id",
                target,
                "--semantic-model-path",
                str(model_path),
                "--limit",
                "20",
                "--json",
            )
            _assert_acquisition_identities_unchanged(
                executable_descriptor,
                executable,
                sidecar_snapshot,
                model_snapshot,
                closure,
                pinned_snapshot,
            )
            completed = _run_query_bounded(argv, pinned_snapshot)
            _assert_acquisition_identities_unchanged(
                executable_descriptor,
                executable,
                sidecar_snapshot,
                model_snapshot,
                closure,
                pinned_snapshot,
            )
            call_binding = {
                "executable_identity": executable.identity,
                "executable_sha256": executable.sha256,
                "sidecar_identity": sidecar_snapshot.identity,
                "sidecar_sha256": sidecar_snapshot.sha256,
                "semantic_model_identity": model_snapshot.identity,
                "semantic_model_sha256": model_snapshot.sha256,
                "execution_closure_sha256": closure.receipt.sha256,
            }
            if completed.returncode != 0:
                if not _is_recoverable_query_failure(completed):
                    raise OpportunityBriefError(
                        "opportunity query returned a non-recoverable error"
                    )
                calls.append(
                    AcquisitionCall(
                        need_id=need.need_id,
                        query=need.query_text,
                        argv=argv,
                        status="query_failed",
                        result_count=0,
                        rejection_count=0,
                        **call_binding,
                    )
                )
                gaps.append(
                    AcquisitionGap(need_id=need.need_id, reason="query_failed")
                )
                continue
            response = _validate_query_response(
                completed.stdout,
                need=need,
                target_repo_id=target,
                model_id=model_id,
            )
            calls.append(
                AcquisitionCall(
                    need_id=need.need_id,
                    query=need.query_text,
                    argv=argv,
                    status="ok",
                    result_count=len(response.results),
                    rejection_count=len(response.rejections),
                    **call_binding,
                )
            )
            rejections.extend(response.rejections)
            for record_id, record, match in response.results:
                prior_index = candidate_indexes.get(record_id)
                if prior_index is None:
                    candidate_indexes[record_id] = len(candidates)
                    candidates.append(
                        OpportunityCandidate(
                            record_id=record_id,
                            record=record,
                            matches=(match,),
                        )
                    )
                    continue
                prior = candidates[prior_index]
                if prior.record != record:
                    raise OpportunityBriefError(
                        "query responses disagree about a candidate record"
                    )
                candidates[prior_index] = OpportunityCandidate(
                    record_id=prior.record_id,
                    record=prior.record,
                    matches=(*prior.matches, match),
                )
        hash_token = _HASH_DEADLINE.set(
            time.monotonic() + HASH_PHASE_TIMEOUT_SECONDS
        )
        try:
            _assert_acquisition_artifacts_unchanged(
                executable_descriptor,
                executable,
                sidecar_snapshot,
                model_snapshot,
                closure,
                pinned_snapshot,
            )
        finally:
            _HASH_DEADLINE.reset(hash_token)
        return AcquisitionReceipt(
            target_repo_id=target,
            model_id=model_id,
            cam_command=command,
            executable_identity=executable.identity,
            executable_sha256=executable.sha256,
            sidecar=database,
            sidecar_identity=sidecar_snapshot.identity,
            sidecar_sha256=sidecar_snapshot.sha256,
            semantic_model_path=model_path,
            semantic_model_identity=model_snapshot.identity,
            semantic_model_sha256=model_snapshot.sha256,
            execution_closure=closure.receipt,
            calls=tuple(calls),
            candidates=tuple(candidates),
            rejections=tuple(rejections),
            gaps=tuple(gaps),
        )
    finally:
        if executable_descriptor is not None:
            os.close(executable_descriptor)
        if pinned_directory is not None:
            _cleanup_pinned_command(pinned_directory)


def _unique_acquisition_needs(needs: object) -> tuple[NeedTheme, ...]:
    if type(needs) is not tuple:
        raise TypeError("needs must be a tuple")
    if len(needs) > MAX_ACQUISITION_NEEDS:
        raise OpportunityBriefError("needs exceed the acquisition bound")
    unique: list[NeedTheme] = []
    by_id: dict[str, NeedTheme] = {}
    for need in needs:
        if type(need) is not NeedTheme:
            raise TypeError("needs must contain NeedTheme values")
        prior = by_id.get(need.need_id)
        if prior is None:
            by_id[need.need_id] = need
            unique.append(need)
        elif prior != need:
            raise OpportunityBriefError("duplicate need_id has conflicting content")
    return tuple(unique)


def _validate_acquisition_path(path: object, *, field: str, kind: str) -> Path:
    if not isinstance(path, Path):
        raise TypeError(f"{field} must be a pathlib.Path")
    try:
        _checked_string(str(path), field=field, limit=4_096)
    except (TypeError, ValueError) as error:
        raise OpportunityBriefError(f"{field} contains unsafe controls") from error
    if not path.is_absolute():
        raise OpportunityBriefError(f"{field} must be absolute")
    current = Path(path.anchor)
    try:
        for component in path.parts[1:]:
            current /= component
            identity = os.lstat(current)
            if stat.S_ISLNK(identity.st_mode):
                raise OpportunityBriefError(f"{field} must not contain a symlink")
        identity = os.lstat(path)
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError(f"{field} must exist") from error
    if kind == "directory":
        if not stat.S_ISDIR(identity.st_mode):
            raise OpportunityBriefError(f"{field} must be a directory")
    elif not stat.S_ISREG(identity.st_mode):
        raise OpportunityBriefError(f"{field} must be a regular file")
    if kind == "executable" and not os.access(path, os.X_OK):
        raise OpportunityBriefError(f"{field} must be executable")
    return path


def _pin_executable(path: Path) -> tuple[int, _FileArtifactSnapshot]:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise OpportunityBriefError("cam command could not be pinned") from error
    try:
        snapshot = _snapshot_open_file(
            descriptor,
            path,
            label="cam command",
            byte_limit=MAX_COMMAND_BYTES,
            require_executable=True,
        )
    except Exception:
        os.close(descriptor)
        raise
    return descriptor, snapshot


def _snapshot_execution_closure(
    command: Path,
    descriptor: int,
    launcher: _FileArtifactSnapshot,
) -> _ExecutionClosureSnapshot:
    raw = _read_open_file(descriptor, launcher.identity[3], label="CAM launcher")
    first_line = raw.partition(b"\n")[0].rstrip(b"\r")
    if not first_line.startswith(b"#!"):
        if not _is_native_executable(raw[:4]):
            raise OpportunityBriefError("CAM launcher format is unsupported")
        receipt = _execution_closure_receipt(
            launcher_kind="native",
            launcher=launcher,
            lexical_interpreter=None,
            interpreter=None,
            runtime=None,
            links=(),
            metadata=None,
            source=None,
        )
        return _ExecutionClosureSnapshot(
            receipt=receipt,
            lexical_interpreter=None,
            interpreter_links=(),
            interpreter=None,
            runtime=None,
            metadata=None,
            source=None,
        )
    try:
        shebang = first_line[2:].decode("utf-8")
    except UnicodeError as error:
        raise OpportunityBriefError("CAM launcher shebang is malformed") from error
    if (
        not shebang
        or shebang != shebang.strip()
        or any(character.isspace() for character in shebang)
        or not Path(shebang).is_absolute()
    ):
        raise OpportunityBriefError("CAM launcher shebang must name one absolute interpreter")
    lexical_interpreter = Path(shebang)
    if _PYTHON_LAUNCHER_NAME_PATTERN.fullmatch(lexical_interpreter.name) is None:
        raise OpportunityBriefError("CAM launcher interpreter name is unsupported")
    links, interpreter = _snapshot_interpreter_chain(lexical_interpreter)
    if _PYTHON_TERMINAL_NAME_PATTERN.fullmatch(interpreter.path.name) is None:
        raise OpportunityBriefError("CAM launcher terminal interpreter is unsupported")
    runtime = _snapshot_python_runtime(interpreter)
    source_root = _launcher_source_marker(raw)
    metadata: _MetadataSnapshot | None = None
    if source_root is None and re.search(rb"(?:from|import)\s+claw(?:\.|\s|$)", raw):
        metadata, source_root = _snapshot_editable_metadata(lexical_interpreter)
    source = _snapshot_cam_source(source_root) if source_root is not None else None
    receipt = _execution_closure_receipt(
        launcher_kind="python",
        launcher=launcher,
        lexical_interpreter=lexical_interpreter,
        interpreter=interpreter,
        runtime=runtime,
        links=links,
        metadata=metadata,
        source=source,
    )
    return _ExecutionClosureSnapshot(
        receipt=receipt,
        lexical_interpreter=lexical_interpreter,
        interpreter_links=links,
        interpreter=interpreter,
        runtime=runtime,
        metadata=metadata,
        source=source,
    )


def _read_open_file(descriptor: int, size: int, *, label: str) -> bytes:
    if size > MAX_COMMAND_BYTES:
        raise OpportunityBriefError(f"{label} exceeds its byte bound")
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        remaining = size
        while remaining:
            _check_hash_deadline()
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise OpportunityBriefError(f"{label} changed while being read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise OpportunityBriefError(f"{label} changed while being read")
        os.lseek(descriptor, 0, os.SEEK_SET)
        return b"".join(chunks)
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError(f"{label} could not be read") from error


def _is_native_executable(prefix: bytes) -> bool:
    return prefix in {
        b"\x7fELF",
        b"\xcf\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xca\xfe\xba\xbe",
        b"\xbe\xba\xfe\xca",
    }


def _snapshot_interpreter_chain(
    path: Path,
) -> tuple[tuple[_SymlinkSnapshot, ...], _FileArtifactSnapshot]:
    links: list[_SymlinkSnapshot] = []
    current = Path(os.path.normpath(path))
    seen: set[tuple[int, int]] = set()
    for _index in range(MAX_INTERPRETER_LINKS + 1):
        try:
            identity = os.lstat(current)
        except OSError as error:
            raise OpportunityBriefError("CAM interpreter chain could not be inspected") from error
        if not stat.S_ISLNK(identity.st_mode):
            if not stat.S_ISREG(identity.st_mode) or identity.st_mode & 0o111 == 0:
                raise OpportunityBriefError("CAM interpreter must resolve to an executable file")
            return tuple(links), _snapshot_single_link_file(
                current,
                label="CAM interpreter",
                byte_limit=MAX_COMMAND_BYTES,
            )
        inode = (identity.st_dev, identity.st_ino)
        if inode in seen or len(links) == MAX_INTERPRETER_LINKS:
            raise OpportunityBriefError("CAM interpreter symlink chain is unsupported")
        seen.add(inode)
        try:
            target = os.readlink(current)
        except OSError as error:
            raise OpportunityBriefError("CAM interpreter symlink could not be read") from error
        _checked_canonical_string(target, field="interpreter symlink target", limit=4_096)
        links.append(
            _SymlinkSnapshot(
                path=current,
                identity=_stat_identity(identity),
                target=target,
            )
        )
        target_path = Path(target)
        current = Path(
            os.path.normpath(
                target_path if target_path.is_absolute() else current.parent / target_path
            )
        )
    raise OpportunityBriefError("CAM interpreter symlink chain is unsupported")


def _snapshot_python_runtime(
    interpreter: _FileArtifactSnapshot,
) -> _PythonRuntimeSnapshot | None:
    match = _PYTHON_TERMINAL_NAME_PATTERN.fullmatch(interpreter.path.name)
    if match is None:
        return None
    home = interpreter.path.parent.parent
    validated_home = _validate_acquisition_path(
        home,
        field="Python runtime home",
        kind="directory",
    )
    try:
        home_status = os.lstat(validated_home)
    except OSError as error:
        raise OpportunityBriefError("Python runtime home could not be inspected") from error
    version = match.group("version")
    candidates: list[Path] = []
    for name in (
        f"libpython{version}.dylib",
        f"libpython{version}.so.1.0",
        f"libpython{version}.so",
    ):
        candidate = validated_home / "lib" / name
        try:
            candidate_status = os.lstat(candidate)
        except FileNotFoundError:
            continue
        except OSError as error:
            raise OpportunityBriefError("Python runtime library could not be inspected") from error
        if stat.S_ISREG(candidate_status.st_mode):
            candidates.append(candidate)
        elif not stat.S_ISLNK(candidate_status.st_mode):
            raise OpportunityBriefError("Python runtime library is unsupported")
    if not candidates:
        return None
    if len(candidates) != 1:
        raise OpportunityBriefError("Python runtime library is ambiguous")
    library = _snapshot_single_link_file(
        candidates[0],
        label="Python runtime library",
        byte_limit=MAX_COMMAND_BYTES,
    )
    return _PythonRuntimeSnapshot(
        home=validated_home,
        home_identity=_stat_identity(home_status),
        library=library,
    )


def _launcher_source_marker(raw: bytes) -> Path | None:
    marker = b"# cam-implementation-root: "
    values = [line[len(marker) :] for line in raw.splitlines() if line.startswith(marker)]
    if not values:
        return None
    if len(values) != 1:
        raise OpportunityBriefError("CAM launcher implementation root is ambiguous")
    try:
        value = values[0].decode("utf-8")
    except UnicodeError as error:
        raise OpportunityBriefError("CAM launcher implementation root is malformed") from error
    root = Path(_checked_canonical_string(value, field="CAM implementation root", limit=4_096))
    if not root.is_absolute():
        raise OpportunityBriefError("CAM implementation root must be absolute")
    return _validate_acquisition_path(root, field="CAM implementation root", kind="directory")


def _materialize_pinned_executable(
    descriptor: int,
    expected: _FileArtifactSnapshot,
    closure: _ExecutionClosureSnapshot,
) -> tuple[Path, _PinnedCommandSnapshot]:
    directory = Path(tempfile.mkdtemp(prefix="cam-opportunity-command-"))
    bin_directory = directory / "bin"
    destination = bin_directory / "cam-command"
    completed = False
    try:
        bin_directory.mkdir(mode=0o700)
        raw = _read_open_file(descriptor, expected.identity[3], label="CAM launcher")
        pinned_interpreter: _FileArtifactSnapshot | None = None
        pinned_runtime_library: _FileArtifactSnapshot | None = None
        if closure.interpreter is not None:
            interpreter_path = bin_directory / "python-interpreter"
            _copy_snapshot_file(closure.interpreter, interpreter_path, mode=0o500)
            pinned_interpreter = _snapshot_single_link_file(
                interpreter_path,
                label="pinned Python interpreter",
                byte_limit=MAX_COMMAND_BYTES,
            )
            first, separator, remainder = raw.partition(b"\n")
            if not separator or not first.startswith(b"#!"):
                raise OpportunityBriefError("CAM Python launcher shebang changed")
            raw = b"#!" + os.fsencode(interpreter_path) + b" -S\n" + remainder
        if closure.runtime is not None:
            lib_directory = directory / "lib"
            lib_directory.mkdir(mode=0o700)
            runtime_library_path = lib_directory / closure.runtime.library.path.name
            _copy_snapshot_file(
                closure.runtime.library,
                runtime_library_path,
                mode=0o400,
            )
            pinned_runtime_library = _snapshot_single_link_file(
                runtime_library_path,
                label="pinned Python runtime library",
                byte_limit=MAX_COMMAND_BYTES,
            )
            os.chmod(lib_directory, 0o500)
        _write_private_file(destination, raw, mode=0o500)
        copied = _snapshot_single_link_file(
            destination,
            label="pinned cam command copy",
            byte_limit=MAX_COMMAND_BYTES,
        )
        if closure.interpreter is None and (
            copied.sha256 != expected.sha256 or copied.identity[3] != expected.identity[3]
        ):
            raise OpportunityBriefError("pinned cam command copy digest is inconsistent")
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.chmod(bin_directory, 0o500)
        os.chmod(directory, 0o500)
        completed = True
        python_path: tuple[Path, ...] = ()
        if closure.source is not None:
            python_path = (closure.source.root / "src",)
        if closure.metadata is not None:
            python_path = (*python_path, closure.metadata.site_packages)
        return directory, _PinnedCommandSnapshot(
            launcher=copied,
            interpreter=pinned_interpreter,
            runtime_library=pinned_runtime_library,
            python_home=None if closure.runtime is None else closure.runtime.home,
            python_path=python_path,
        )
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError("cam command could not be pinned for execution") from error
    finally:
        if not completed:
            _cleanup_pinned_command(directory)


def _write_private_file(path: Path, content: bytes, *, mode: int) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
            mode,
        )
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OpportunityBriefError("private command copy could not be written")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.chmod(path, mode)
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError("private command copy could not be written") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _copy_snapshot_file(
    source: _FileArtifactSnapshot,
    destination: Path,
    *,
    mode: int,
) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(source.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        before = os.fstat(descriptor)
        if _stat_identity(before) != source.identity:
            raise OpportunityBriefError("execution closure identity changed")
        content = _read_open_file(descriptor, before.st_size, label="execution closure")
        after = os.fstat(descriptor)
        path_after = os.lstat(source.path)
        if (
            _stat_identity(after) != source.identity
            or _stat_identity(path_after) != source.identity
            or hashlib.sha256(content).hexdigest() != source.sha256
        ):
            raise OpportunityBriefError("execution closure identity or digest changed")
        _write_private_file(destination, content, mode=mode)
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError("execution closure could not be copied") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _cleanup_pinned_command(directory: Path) -> None:
    try:
        if os.path.lexists(directory):
            os.chmod(directory, 0o700)
            for current, directories, _files in os.walk(directory):
                os.chmod(current, 0o700)
                for child in directories:
                    os.chmod(Path(current) / child, 0o700)
            shutil.rmtree(directory)
        if os.path.lexists(directory):
            raise OpportunityBriefError("private command cleanup could not be verified")
    except OpportunityBriefError:
        raise
    except Exception as error:
        raise OpportunityBriefError("private command cleanup failed") from error


def _snapshot_editable_metadata(
    lexical_interpreter: Path,
) -> tuple[_MetadataSnapshot, Path]:
    prefix = lexical_interpreter.parent.parent
    candidates: list[tuple[Path, Path, Path, Path]] = []
    try:
        site_directories = sorted((prefix / "lib").glob("python*/site-packages"))
        for site in site_directories:
            pth_files = sorted(site.glob("__editable__.claw-*.pth"))
            finder_files = sorted(site.glob("__editable___claw_*_finder.py"))
            dist_directories = sorted(site.glob("claw-*.dist-info"))
            if len(pth_files) == len(finder_files) == len(dist_directories) == 1:
                candidates.append(
                    (site, pth_files[0], finder_files[0], dist_directories[0])
                )
    except OSError as error:
        raise OpportunityBriefError("editable CAM metadata could not be inspected") from error
    if len(candidates) != 1:
        raise OpportunityBriefError("editable CAM metadata is missing or ambiguous")
    site_packages, pth_path, finder_path, dist_directory = candidates[0]
    try:
        site_identity = os.lstat(site_packages)
    except OSError as error:
        raise OpportunityBriefError("editable CAM site-packages could not be inspected") from error
    if not stat.S_ISDIR(site_identity.st_mode):
        raise OpportunityBriefError("editable CAM site-packages is unsupported")
    metadata_paths = [pth_path, finder_path]
    try:
        dist_entries = sorted(dist_directory.iterdir(), key=lambda item: item.name)
    except OSError as error:
        raise OpportunityBriefError("editable CAM distribution metadata could not be read") from error
    if len(dist_entries) > MAX_CLOSURE_METADATA_FILES - len(metadata_paths):
        raise OpportunityBriefError("editable CAM metadata exceeds its file bound")
    if any(not entry.is_file() or entry.is_symlink() for entry in dist_entries):
        raise OpportunityBriefError("editable CAM metadata contains an unsupported entry")
    metadata_paths.extend(dist_entries)
    snapshots: list[_FileArtifactSnapshot] = []
    total = 0
    for path in metadata_paths:
        snapshot = _snapshot_single_link_file(
            path,
            label="editable CAM metadata",
            byte_limit=MAX_CLOSURE_METADATA_BYTES,
        )
        total += snapshot.identity[3]
        if total > MAX_CLOSURE_METADATA_BYTES:
            raise OpportunityBriefError("editable CAM metadata exceeds its byte bound")
        snapshots.append(snapshot)
    by_path = {snapshot.path: snapshot for snapshot in snapshots}
    pth_text = _read_snapshot_text(by_path[pth_path], label="editable CAM .pth metadata")
    finder_text = _read_snapshot_text(
        by_path[finder_path],
        label="editable CAM mapping metadata",
    )
    finder_module = finder_path.stem
    if pth_text.strip() != f"import {finder_module}; {finder_module}.install()":
        raise OpportunityBriefError("editable CAM .pth metadata is unsupported")
    mapping_root = _parse_editable_claw_mapping(finder_text)
    direct_url_path = dist_directory / "direct_url.json"
    if direct_url_path not in by_path:
        raise OpportunityBriefError("editable CAM direct URL metadata is missing")
    direct_url = _decode_strict_json(
        _read_snapshot_bytes(by_path[direct_url_path], label="editable CAM direct URL"),
        label="editable CAM direct URL metadata",
    )
    if type(direct_url) is not dict or set(direct_url) != {"url", "dir_info"}:
        raise OpportunityBriefError("editable CAM direct URL metadata is unsupported")
    if direct_url.get("dir_info") != {"editable": True}:
        raise OpportunityBriefError("CAM installation is not an editable source mapping")
    parsed_url = urlparse(direct_url.get("url") if type(direct_url.get("url")) is str else "")
    if parsed_url.scheme != "file" or parsed_url.netloc or not parsed_url.path:
        raise OpportunityBriefError("editable CAM source URL is unsupported")
    source_root = Path(unquote(parsed_url.path))
    if not source_root.is_absolute() or mapping_root != source_root / "src" / "claw":
        raise OpportunityBriefError("editable CAM mapping does not match its source root")
    aggregate = _metadata_digest(tuple(snapshots))
    return (
        _MetadataSnapshot(
            site_packages=site_packages,
            site_packages_identity=_stat_identity(site_identity),
            files=tuple(snapshots),
            sha256=aggregate,
        ),
        source_root,
    )


def _parse_editable_claw_mapping(text: str) -> Path:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError) as error:
        raise OpportunityBriefError("editable CAM mapping metadata is malformed") from error
    values: list[object] = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "MAPPING" for target in targets):
                try:
                    values.append(ast.literal_eval(node.value))
                except (ValueError, TypeError) as error:
                    raise OpportunityBriefError(
                        "editable CAM mapping metadata is malformed"
                    ) from error
    if len(values) != 1 or type(values[0]) is not dict or set(values[0]) != {"claw"}:
        raise OpportunityBriefError("editable CAM mapping metadata is unsupported")
    value = values[0]["claw"]
    if type(value) is not str:
        raise OpportunityBriefError("editable CAM mapping path is malformed")
    path = Path(_checked_canonical_string(value, field="editable CAM mapping", limit=4_096))
    if not path.is_absolute():
        raise OpportunityBriefError("editable CAM mapping path must be absolute")
    return path


def _read_snapshot_bytes(snapshot: _FileArtifactSnapshot, *, label: str) -> bytes:
    descriptor: int | None = None
    try:
        descriptor = os.open(snapshot.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        if _stat_identity(os.fstat(descriptor)) != snapshot.identity:
            raise OpportunityBriefError(f"{label} identity changed")
        raw = _read_open_file(descriptor, snapshot.identity[3], label=label)
        if hashlib.sha256(raw).hexdigest() != snapshot.sha256:
            raise OpportunityBriefError(f"{label} digest changed")
        return raw
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError(f"{label} could not be read") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_snapshot_text(snapshot: _FileArtifactSnapshot, *, label: str) -> str:
    try:
        return _read_snapshot_bytes(snapshot, label=label).decode("utf-8")
    except UnicodeError as error:
        raise OpportunityBriefError(f"{label} is not UTF-8") from error


def _metadata_digest(files: tuple[_FileArtifactSnapshot, ...]) -> str:
    payload = [
        [str(item.path), list(item.identity), item.sha256]
        for item in files
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _snapshot_cam_source(root: Path) -> _CamSourceSnapshot:
    validated = _validate_acquisition_path(
        root,
        field="CAM source root",
        kind="directory",
    )
    descriptor: int | None = None
    try:
        descriptor, identity = _open_pinned_root(validated)
        git = _read_git_snapshot(validated, descriptor, identity)
        if git.revision is None:
            raise OpportunityBriefError("CAM source root must have an immutable Git HEAD")
        source_path = validated / "src" / "claw"
        try:
            manifest = _snapshot_model_directory(source_path)
        except OpportunityBriefError as error:
            raise OpportunityBriefError("CAM source content manifest is invalid") from error
        _assert_root_identity(validated, descriptor, identity)
        return _CamSourceSnapshot(
            root=validated,
            root_identity=identity,
            git=git,
            manifest=manifest,
        )
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _execution_closure_receipt(
    *,
    launcher_kind: Literal["python", "native"],
    launcher: _FileArtifactSnapshot,
    lexical_interpreter: Path | None,
    interpreter: _FileArtifactSnapshot | None,
    runtime: _PythonRuntimeSnapshot | None,
    links: tuple[_SymlinkSnapshot, ...],
    metadata: _MetadataSnapshot | None,
    source: _CamSourceSnapshot | None,
) -> ExecutionClosureReceipt:
    return ExecutionClosureReceipt(
        launcher_kind=launcher_kind,
        launcher_path=launcher.path,
        launcher_identity=launcher.identity,
        launcher_sha256=launcher.sha256,
        interpreter_path=lexical_interpreter,
        interpreter_symlink_chain=tuple(
            InterpreterSymlinkReceipt(
                path=link.path,
                identity=link.identity,
                target=link.target,
            )
            for link in links
        ),
        resolved_interpreter_path=None if interpreter is None else interpreter.path,
        resolved_interpreter_identity=None if interpreter is None else interpreter.identity,
        interpreter_sha256=None if interpreter is None else interpreter.sha256,
        python_home=None if runtime is None else runtime.home,
        python_home_identity=None if runtime is None else runtime.home_identity,
        python_runtime_library_path=None if runtime is None else runtime.library.path,
        python_runtime_library_identity=(
            None if runtime is None else runtime.library.identity
        ),
        python_runtime_library_sha256=(
            None if runtime is None else runtime.library.sha256
        ),
        editable_site_packages=None if metadata is None else metadata.site_packages,
        editable_site_packages_identity=(
            None if metadata is None else metadata.site_packages_identity
        ),
        editable_metadata_sha256=None if metadata is None else metadata.sha256,
        cam_source_root=None if source is None else source.root,
        cam_source_root_identity=None if source is None else source.root_identity,
        cam_source_revision=None if source is None else source.git.revision,
        cam_source_branch=None if source is None else source.git.branch,
        cam_source_dirty_entries=() if source is None else source.git.dirty_entries,
        cam_source_sha256=None if source is None else source.manifest.sha256,
    )


def _execution_closure_public_digest(receipt: ExecutionClosureReceipt) -> str:
    payload = {
        "launcher_kind": receipt.launcher_kind,
        "launcher_path": str(receipt.launcher_path),
        "launcher_identity": list(receipt.launcher_identity),
        "launcher_sha256": receipt.launcher_sha256,
        "interpreter_path": (
            None if receipt.interpreter_path is None else str(receipt.interpreter_path)
        ),
        "interpreter_symlink_chain": [
            [str(link.path), list(link.identity), link.target]
            for link in receipt.interpreter_symlink_chain
        ],
        "resolved_interpreter_path": (
            None
            if receipt.resolved_interpreter_path is None
            else str(receipt.resolved_interpreter_path)
        ),
        "resolved_interpreter_identity": (
            None
            if receipt.resolved_interpreter_identity is None
            else list(receipt.resolved_interpreter_identity)
        ),
        "interpreter_sha256": receipt.interpreter_sha256,
        "python_home": None if receipt.python_home is None else str(receipt.python_home),
        "python_home_identity": (
            None
            if receipt.python_home_identity is None
            else list(receipt.python_home_identity)
        ),
        "python_runtime_library_path": (
            None
            if receipt.python_runtime_library_path is None
            else str(receipt.python_runtime_library_path)
        ),
        "python_runtime_library_identity": (
            None
            if receipt.python_runtime_library_identity is None
            else list(receipt.python_runtime_library_identity)
        ),
        "python_runtime_library_sha256": receipt.python_runtime_library_sha256,
        "editable_site_packages": (
            None
            if receipt.editable_site_packages is None
            else str(receipt.editable_site_packages)
        ),
        "editable_site_packages_identity": (
            None
            if receipt.editable_site_packages_identity is None
            else list(receipt.editable_site_packages_identity)
        ),
        "editable_metadata_sha256": receipt.editable_metadata_sha256,
        "cam_source_root": (
            None if receipt.cam_source_root is None else str(receipt.cam_source_root)
        ),
        "cam_source_root_identity": (
            None
            if receipt.cam_source_root_identity is None
            else list(receipt.cam_source_root_identity)
        ),
        "cam_source_revision": receipt.cam_source_revision,
        "cam_source_branch": receipt.cam_source_branch,
        "cam_source_dirty_entries": list(receipt.cam_source_dirty_entries),
        "cam_source_sha256": receipt.cam_source_sha256,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _snapshot_single_link_file(
    path: Path,
    *,
    label: str,
    byte_limit: int,
) -> _FileArtifactSnapshot:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise OpportunityBriefError(f"{label} could not be opened safely") from error
    try:
        return _snapshot_open_file(
            descriptor,
            path,
            label=label,
            byte_limit=byte_limit,
            require_executable=False,
        )
    finally:
        os.close(descriptor)


def _snapshot_open_file(
    descriptor: int,
    path: Path,
    *,
    label: str,
    byte_limit: int,
    require_executable: bool,
) -> _FileArtifactSnapshot:
    try:
        opened_before = os.fstat(descriptor)
        path_before = os.lstat(path)
        identity = _stat_identity(opened_before)
        if (
            not stat.S_ISREG(opened_before.st_mode)
            or not stat.S_ISREG(path_before.st_mode)
            or _stat_identity(path_before) != identity
        ):
            raise OpportunityBriefError(f"{label} identity changed")
        if opened_before.st_nlink != 1:
            raise OpportunityBriefError(f"{label} must be a single-link regular file")
        if require_executable and opened_before.st_mode & 0o111 == 0:
            raise OpportunityBriefError("cam command must be executable")
        if opened_before.st_size > byte_limit:
            raise OpportunityBriefError(f"{label} exceeds its byte bound")
        digest = _hash_descriptor(descriptor, byte_limit=byte_limit, label=label)
        opened_after = os.fstat(descriptor)
        path_after = os.lstat(path)
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError(f"{label} identity could not be read") from error
    if (
        _stat_identity(opened_after) != identity
        or _stat_identity(path_after) != identity
        or not stat.S_ISREG(path_after.st_mode)
    ):
        raise OpportunityBriefError(f"{label} identity changed")
    return _FileArtifactSnapshot(path=path, identity=identity, sha256=digest)


def _hash_descriptor(descriptor: int, *, byte_limit: int, label: str) -> str:
    digest = hashlib.sha256()
    total = 0
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        while True:
            _check_hash_deadline()
            chunk = os.read(descriptor, min(1024 * 1024, byte_limit + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > byte_limit:
                raise OpportunityBriefError(f"{label} exceeds its byte bound")
            digest.update(chunk)
        os.lseek(descriptor, 0, os.SEEK_SET)
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError(f"{label} content could not be hashed") from error
    return digest.hexdigest()


def _check_hash_deadline() -> None:
    deadline = _HASH_DEADLINE.get()
    if deadline is not None and time.monotonic() > deadline:
        raise OpportunityBriefError("execution closure hashing exceeded its time bound")


def _snapshot_model_directory(path: Path) -> _ModelArtifactSnapshot:
    descriptor: int | None = None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        before = os.lstat(path)
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        identity = _stat_identity(opened)
        if (
            not stat.S_ISDIR(before.st_mode)
            or not stat.S_ISDIR(opened.st_mode)
            or _stat_identity(before) != identity
        ):
            raise OpportunityBriefError("semantic model directory identity changed")
        entries: list[_ModelManifestEntry] = []
        budget = [0, 0]
        _check_hash_deadline()
        _walk_model_manifest(descriptor, (), entries, budget)
        opened_after = os.fstat(descriptor)
        path_after = os.lstat(path)
        if (
            _stat_identity(opened_after) != identity
            or _stat_identity(path_after) != identity
            or not stat.S_ISDIR(path_after.st_mode)
        ):
            raise OpportunityBriefError("semantic model directory identity changed")
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError("semantic model manifest could not be read") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    manifest = [
        [entry.relative_path, entry.kind, entry.sha256]
        for entry in entries
    ]
    encoded = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _ModelArtifactSnapshot(
        path=path,
        identity=identity,
        entries=tuple(entries),
        sha256=hashlib.sha256(encoded).hexdigest(),
    )


def _walk_model_manifest(
    directory_descriptor: int,
    relative_parts: tuple[str, ...],
    entries: list[_ModelManifestEntry],
    budget: list[int],
) -> None:
    try:
        with os.scandir(directory_descriptor) as iterator:
            names = sorted(
                (entry.name for entry in iterator),
                key=lambda item: (item.casefold(), os.fsencode(item)),
            )
    except OSError as error:
        raise OpportunityBriefError("semantic model manifest could not be scanned") from error
    for name in names:
        _check_hash_deadline()
        _checked_relative_path("/".join((*relative_parts, name)), field="model entry")
        budget[0] += 1
        if budget[0] > MAX_MODEL_ENTRIES:
            raise OpportunityBriefError("semantic model manifest exceeds its entry bound")
        try:
            before = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
        except OSError as error:
            raise OpportunityBriefError("semantic model entry identity changed") from error
        relative = "/".join((*relative_parts, name))
        if stat.S_ISLNK(before.st_mode):
            raise OpportunityBriefError("semantic model manifest must not contain symlinks")
        if stat.S_ISDIR(before.st_mode):
            _walk_model_directory(
                directory_descriptor,
                name,
                before,
                (*relative_parts, name),
                entries,
                budget,
            )
            entries.append(
                _ModelManifestEntry(
                    relative_path=relative,
                    kind="directory",
                    identity=_stat_identity(before),
                    sha256="",
                )
            )
            continue
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise OpportunityBriefError(
                "semantic model entries must be single-link regular files"
            )
        descriptor: int | None = None
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory_descriptor,
            )
            opened = os.fstat(descriptor)
            identity = _stat_identity(opened)
            if identity != _stat_identity(before) or not stat.S_ISREG(opened.st_mode):
                raise OpportunityBriefError("semantic model file identity changed")
            budget[1] += opened.st_size
            if budget[1] > MAX_MODEL_BYTES:
                raise OpportunityBriefError("semantic model content exceeds its byte bound")
            digest = _hash_descriptor(
                descriptor,
                byte_limit=opened.st_size,
                label="semantic model file",
            )
            after = os.fstat(descriptor)
            path_after = os.stat(
                name,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            if _stat_identity(after) != identity or _stat_identity(path_after) != identity:
                raise OpportunityBriefError("semantic model file identity changed")
        except OpportunityBriefError:
            raise
        except OSError as error:
            raise OpportunityBriefError("semantic model file could not be read") from error
        finally:
            if descriptor is not None:
                os.close(descriptor)
        entries.append(
            _ModelManifestEntry(
                relative_path=relative,
                kind="file",
                identity=identity,
                sha256=digest,
            )
        )


def _walk_model_directory(
    parent_descriptor: int,
    name: str,
    before: os.stat_result,
    relative_parts: tuple[str, ...],
    entries: list[_ModelManifestEntry],
    budget: list[int],
) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_descriptor,
        )
        opened = os.fstat(descriptor)
        identity = _stat_identity(opened)
        if identity != _stat_identity(before) or not stat.S_ISDIR(opened.st_mode):
            raise OpportunityBriefError("semantic model directory identity changed")
        _walk_model_manifest(descriptor, relative_parts, entries, budget)
        after = os.fstat(descriptor)
        path_after = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if _stat_identity(after) != identity or _stat_identity(path_after) != identity:
            raise OpportunityBriefError("semantic model directory identity changed")
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError("semantic model directory could not be read") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _assert_acquisition_identities_unchanged(
    executable_descriptor: int,
    executable: _FileArtifactSnapshot,
    sidecar: _FileArtifactSnapshot,
    model: _ModelArtifactSnapshot,
    closure: _ExecutionClosureSnapshot,
    pinned: _PinnedCommandSnapshot,
) -> None:
    _assert_open_file_identity(
        executable_descriptor,
        executable,
        label="cam command",
        require_executable=True,
    )
    _assert_file_identity(sidecar, label="sidecar")
    _assert_tree_identity(model, label="semantic model")
    _assert_execution_closure_identity(closure)
    _assert_file_identity(pinned.launcher, label="pinned cam command copy")
    if pinned.interpreter is not None:
        _assert_file_identity(pinned.interpreter, label="pinned Python interpreter")
    if pinned.runtime_library is not None:
        _assert_file_identity(
            pinned.runtime_library,
            label="pinned Python runtime library",
        )


def _assert_acquisition_artifacts_unchanged(
    executable_descriptor: int,
    executable: _FileArtifactSnapshot,
    sidecar: _FileArtifactSnapshot,
    model: _ModelArtifactSnapshot,
    closure: _ExecutionClosureSnapshot,
    pinned: _PinnedCommandSnapshot,
) -> None:
    current_executable = _snapshot_open_file(
        executable_descriptor,
        executable.path,
        label="cam command",
        byte_limit=MAX_COMMAND_BYTES,
        require_executable=True,
    )
    if current_executable != executable:
        raise OpportunityBriefError("cam command identity or digest changed")
    if (
        _snapshot_single_link_file(
            sidecar.path,
            label="sidecar",
            byte_limit=MAX_SIDECAR_BYTES,
        )
        != sidecar
    ):
        raise OpportunityBriefError("sidecar identity or digest changed")
    if _snapshot_model_directory(model.path) != model:
        raise OpportunityBriefError("semantic model identity or digest changed")
    if (
        _snapshot_execution_closure(
            executable.path,
            executable_descriptor,
            current_executable,
        )
        != closure
    ):
        raise OpportunityBriefError("CAM execution closure identity or digest changed")
    current_pinned = _PinnedCommandSnapshot(
        launcher=_snapshot_single_link_file(
            pinned.launcher.path,
            label="pinned cam command copy",
            byte_limit=MAX_COMMAND_BYTES,
        ),
        interpreter=None
        if pinned.interpreter is None
        else _snapshot_single_link_file(
            pinned.interpreter.path,
            label="pinned Python interpreter",
            byte_limit=MAX_COMMAND_BYTES,
        ),
        runtime_library=None
        if pinned.runtime_library is None
        else _snapshot_single_link_file(
            pinned.runtime_library.path,
            label="pinned Python runtime library",
            byte_limit=MAX_COMMAND_BYTES,
        ),
        python_home=pinned.python_home,
        python_path=pinned.python_path,
    )
    if current_pinned != pinned:
        raise OpportunityBriefError("pinned CAM execution closure changed")


def _assert_open_file_identity(
    descriptor: int,
    expected: _FileArtifactSnapshot,
    *,
    label: str,
    require_executable: bool,
) -> None:
    try:
        opened = os.fstat(descriptor)
        current = os.lstat(expected.path)
    except OSError as error:
        raise OpportunityBriefError(f"{label} identity could not be inspected") from error
    if (
        _stat_identity(opened) != expected.identity
        or _stat_identity(current) != expected.identity
        or not stat.S_ISREG(current.st_mode)
        or (require_executable and current.st_mode & 0o111 == 0)
    ):
        raise OpportunityBriefError(f"{label} identity changed")


def _assert_file_identity(expected: _FileArtifactSnapshot, *, label: str) -> None:
    try:
        current = os.lstat(expected.path)
    except OSError as error:
        raise OpportunityBriefError(f"{label} identity could not be inspected") from error
    if not stat.S_ISREG(current.st_mode) or _stat_identity(current) != expected.identity:
        raise OpportunityBriefError(f"{label} identity changed")


def _assert_tree_identity(expected: _ModelArtifactSnapshot, *, label: str) -> None:
    try:
        root = os.lstat(expected.path)
    except OSError as error:
        raise OpportunityBriefError(f"{label} identity could not be inspected") from error
    if not stat.S_ISDIR(root.st_mode) or _stat_identity(root) != expected.identity:
        raise OpportunityBriefError(f"{label} identity changed")
    current = _tree_identity_entries(expected.path)
    wanted = tuple(
        (entry.relative_path, entry.kind, entry.identity) for entry in expected.entries
    )
    if current != wanted:
        raise OpportunityBriefError(f"{label} identity changed")


def _tree_identity_entries(
    root: Path,
) -> tuple[tuple[str, Literal["directory", "file"], DirectoryIdentity], ...]:
    entries: list[tuple[str, Literal["directory", "file"], DirectoryIdentity]] = []
    budget = [0]

    def walk(directory: Path, parts: tuple[str, ...]) -> None:
        try:
            children = sorted(
                directory.iterdir(),
                key=lambda item: (item.name.casefold(), os.fsencode(item.name)),
            )
        except OSError as error:
            raise OpportunityBriefError("artifact identity manifest could not be scanned") from error
        for child in children:
            budget[0] += 1
            if budget[0] > MAX_MODEL_ENTRIES:
                raise OpportunityBriefError("artifact identity manifest exceeds its bound")
            try:
                identity = os.lstat(child)
            except OSError as error:
                raise OpportunityBriefError("artifact identity changed") from error
            relative = "/".join((*parts, child.name))
            if stat.S_ISLNK(identity.st_mode):
                raise OpportunityBriefError("artifact identity manifest contains a symlink")
            if stat.S_ISDIR(identity.st_mode):
                walk(child, (*parts, child.name))
                entries.append((relative, "directory", _stat_identity(identity)))
            elif stat.S_ISREG(identity.st_mode) and identity.st_nlink == 1:
                entries.append((relative, "file", _stat_identity(identity)))
            else:
                raise OpportunityBriefError("artifact identity manifest contains an entry")

    walk(root, ())
    return tuple(entries)


def _assert_execution_closure_identity(closure: _ExecutionClosureSnapshot) -> None:
    for link in closure.interpreter_links:
        try:
            current = os.lstat(link.path)
            target = os.readlink(link.path)
        except OSError as error:
            raise OpportunityBriefError("CAM interpreter closure identity changed") from error
        if _stat_identity(current) != link.identity or target != link.target:
            raise OpportunityBriefError("CAM interpreter closure identity changed")
    if closure.interpreter is not None:
        _assert_file_identity(closure.interpreter, label="CAM interpreter closure")
    if closure.runtime is not None:
        try:
            runtime_home = os.lstat(closure.runtime.home)
        except OSError as error:
            raise OpportunityBriefError("Python runtime closure identity changed") from error
        if (
            not stat.S_ISDIR(runtime_home.st_mode)
            or _stat_identity(runtime_home) != closure.runtime.home_identity
        ):
            raise OpportunityBriefError("Python runtime closure identity changed")
        _assert_file_identity(
            closure.runtime.library,
            label="Python runtime library closure",
        )
    if closure.metadata is not None:
        try:
            site_packages = os.lstat(closure.metadata.site_packages)
        except OSError as error:
            raise OpportunityBriefError(
                "editable CAM site-packages closure identity changed"
            ) from error
        if (
            not stat.S_ISDIR(site_packages.st_mode)
            or _stat_identity(site_packages) != closure.metadata.site_packages_identity
        ):
            raise OpportunityBriefError(
                "editable CAM site-packages closure identity changed"
            )
        for item in closure.metadata.files:
            _assert_file_identity(item, label="editable CAM metadata closure")
    if closure.source is not None:
        source = closure.source
        try:
            root_descriptor, root_identity = _open_pinned_root(source.root)
        except OpportunityBriefError as error:
            raise OpportunityBriefError("CAM source closure identity changed") from error
        try:
            if root_identity != source.root_identity:
                raise OpportunityBriefError("CAM source closure identity changed")
            git = _read_git_snapshot(source.root, root_descriptor, root_identity)
            if git != source.git:
                raise OpportunityBriefError("CAM source Git closure changed")
            _assert_tree_identity(source.manifest, label="CAM source closure")
        finally:
            os.close(root_descriptor)


def _query_environment(
    python_path: tuple[Path, ...] = (),
    *,
    python_home: Path | None = None,
) -> dict[str, str]:
    environment = {
        "HOME": "/var/empty",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "XDG_CACHE_HOME": "/var/empty",
        "XDG_CONFIG_HOME": "/var/empty",
    }
    if python_path:
        environment["PYTHONPATH"] = os.pathsep.join(str(path) for path in python_path)
    if python_home is not None:
        environment["PYTHONHOME"] = str(python_home)
    return environment


def _run_query_bounded(
    argv: tuple[str, ...],
    pinned_executable: _PinnedCommandSnapshot,
) -> _GitResult:
    process: subprocess.Popen[bytes] | None = None
    process_group: int | None = None
    selector: selectors.BaseSelector | None = None
    group_handled = False
    output = bytearray()
    errors = bytearray()
    try:
        _assert_file_identity(
            pinned_executable.launcher,
            label="pinned cam command copy",
        )
        if pinned_executable.interpreter is not None:
            _assert_file_identity(
                pinned_executable.interpreter,
                label="pinned Python interpreter",
            )
        if pinned_executable.runtime_library is not None:
            _assert_file_identity(
                pinned_executable.runtime_library,
                label="pinned Python runtime library",
            )
        process = subprocess.Popen(
            list(argv),
            executable=str(pinned_executable.launcher.path),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=_query_environment(
                pinned_executable.python_path,
                python_home=pinned_executable.python_home,
            ),
            close_fds=True,
            start_new_session=True,
        )
        process_group = process.pid
        if process.stdout is None or process.stderr is None:
            raise OpportunityBriefError("opportunity query pipes were unavailable")
        selector = selectors.DefaultSelector()
        selector.register(
            process.stdout,
            selectors.EVENT_READ,
            (output, MAX_QUERY_RESPONSE_BYTES),
        )
        selector.register(
            process.stderr,
            selectors.EVENT_READ,
            (errors, MAX_QUERY_ERROR_BYTES),
        )
        deadline = time.monotonic() + QUERY_TIMEOUT_SECONDS
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise OpportunityBriefError("opportunity query timed out")
            events = selector.select(min(remaining, 0.1))
            if not events:
                continue
            for key, _ in events:
                buffer, limit = key.data
                chunk = os.read(
                    key.fileobj.fileno(),
                    min(8_192, limit + 1 - len(buffer)),
                )
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                buffer.extend(chunk)
                if len(buffer) > limit:
                    raise OpportunityBriefError(
                        "opportunity query output exceeds its bound"
                    )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise OpportunityBriefError("opportunity query timed out")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            raise OpportunityBriefError("opportunity query timed out") from error
        if _process_group_exists(process_group):
            _kill_query_process_group(process, process_group)
            group_handled = True
            raise OpportunityBriefError(
                "opportunity query process group survived its leader"
            )
        if returncode != 0:
            _kill_query_process_group(process, process_group)
            group_handled = True
        _assert_file_identity(
            pinned_executable.launcher,
            label="pinned cam command copy",
        )
        if pinned_executable.interpreter is not None:
            _assert_file_identity(
                pinned_executable.interpreter,
                label="pinned Python interpreter",
            )
        if pinned_executable.runtime_library is not None:
            _assert_file_identity(
                pinned_executable.runtime_library,
                label="pinned Python runtime library",
            )
        return _GitResult(
            returncode=returncode,
            stdout=bytes(output),
            stderr=bytes(errors),
        )
    except OpportunityBriefError:
        raise
    except Exception as error:
        raise OpportunityBriefError("opportunity query subprocess output failed") from error
    finally:
        if process is not None and process_group is not None and not group_handled:
            _kill_query_process_group(process, process_group)
        if selector is not None:
            try:
                selector.close()
            except Exception:
                pass
        if process is not None:
            if process.stdout and not process.stdout.closed:
                process.stdout.close()
            if process.stderr and not process.stderr.closed:
                process.stderr.close()


def _process_group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as error:
        if error.errno == errno.ESRCH:
            return False
        raise OpportunityBriefError("opportunity query process group could not be inspected") from error
    return True


def _kill_query_process_group(
    process: subprocess.Popen[bytes],
    process_group: int,
) -> None:
    try:
        os.killpg(process_group, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as error:
        if error.errno != errno.ESRCH:
            try:
                process.kill()
            except OSError:
                pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except OSError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass


def _is_recoverable_query_failure(completed: _GitResult) -> bool:
    if completed.returncode != 2 or completed.stderr:
        return False
    try:
        envelope = _decode_strict_json(
            completed.stdout,
            label="opportunity query error envelope",
        )
    except OpportunityBriefError:
        return False
    return envelope == {
        "status": "error",
        "error": "opportunity query backend failed",
    }


def _decode_strict_json(raw: bytes, *, label: str) -> object:
    def reject_constant(_value: str) -> object:
        raise ValueError("non-finite JSON constants are unsupported")

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object key")
            result[key] = value
        return result

    try:
        decoded = raw.decode("utf-8")
        value = json.loads(
            decoded,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        raise OpportunityBriefError(f"{label} is not strict JSON") from error
    _validate_json_shape(value, label=label)
    return value


def _validate_json_shape(value: object, *, label: str) -> None:
    stack: list[tuple[object, int]] = [(value, 1)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise OpportunityBriefError(f"{label} exceeds its node bound")
        if depth > MAX_JSON_DEPTH:
            raise OpportunityBriefError(f"{label} exceeds its depth bound")
        if type(item) is dict:
            stack.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            stack.extend((child, depth + 1) for child in item)


def _validate_query_response(
    raw: bytes,
    *,
    need: NeedTheme,
    target_repo_id: str,
    model_id: str,
) -> _ValidatedQueryResponse:
    value = _decode_strict_json(raw, label="opportunity query response JSON")
    response = _exact_mapping(
        value,
        field="query response",
        keys={
            "schema_version",
            "scope",
            "query",
            "target_repo_id",
            "model_id",
            "results",
            "rejections",
        },
    )
    if type(response["schema_version"]) is not int or response["schema_version"] != 1:
        raise OpportunityBriefError("opportunity query response schema is unsupported")
    if response["scope"] != "opportunity_sidecar":
        raise OpportunityBriefError("opportunity query response scope is unsupported")
    if response["query"] != need.query_text:
        raise OpportunityBriefError("opportunity query response query does not match")
    if response["target_repo_id"] != target_repo_id:
        raise OpportunityBriefError("opportunity query response target does not match")
    if response["model_id"] != model_id:
        raise OpportunityBriefError("opportunity query response model does not match")

    results_value = _bounded_json_list(
        response["results"],
        field="query results",
        maximum=MAX_QUERY_RESULTS,
    )
    parsed_results: list[tuple[str, OpportunityRecordReceipt, CandidateMatch]] = []
    seen_results: set[str] = set()
    for value in results_value:
        result = _exact_mapping(
            value,
            field="query result",
            keys={"record_id", "record", "fts_rank", "semantic_rank", "rrf_score"},
        )
        record_id = _canonical_string(
            result["record_id"],
            field="result record_id",
            limit=36,
        )
        if _RECORD_ID_PATTERN.fullmatch(record_id) is None:
            raise OpportunityBriefError("query result record_id is malformed")
        if record_id in seen_results:
            raise OpportunityBriefError("query results repeat a record_id")
        seen_results.add(record_id)
        record = _parse_opportunity_record(
            result["record"],
            target_repo_id=target_repo_id,
        )
        if record_id != _record_id(record):
            raise OpportunityBriefError("query result record identity is inconsistent")
        try:
            match = CandidateMatch(
                need_id=need.need_id,
                fts_rank=result["fts_rank"],
                semantic_rank=result["semantic_rank"],
                rrf_score=result["rrf_score"],
            )
        except (TypeError, ValueError) as error:
            raise OpportunityBriefError("query result rank or RRF score is malformed") from error
        parsed_results.append((record_id, record, match))
    for rank_name in ("fts_rank", "semantic_rank"):
        ranks = [
            getattr(match, rank_name)
            for _record_id, _record, match in parsed_results
            if getattr(match, rank_name) is not None
        ]
        if len(ranks) != len(set(ranks)):
            raise OpportunityBriefError(f"query result {rank_name} values are not unique")
    infinity = 1_001
    expected_results = sorted(
        parsed_results,
        key=lambda item: (
            -item[2].rrf_score,
            min(item[2].fts_rank or infinity, item[2].semantic_rank or infinity),
            item[2].fts_rank or infinity,
            item[2].semantic_rank or infinity,
            item[0],
        ),
    )
    if parsed_results != expected_results:
        raise OpportunityBriefError("query results are not in canonical result order")

    rejections_value = _bounded_json_list(
        response["rejections"],
        field="query rejections",
        maximum=MAX_QUERY_REJECTIONS,
    )
    parsed_rejections: list[AcquisitionRejection] = []
    seen_rejections: set[str] = set()
    for value in rejections_value:
        rejection = _exact_mapping(
            value,
            field="query rejection",
            keys={"record_id", "reason"},
        )
        try:
            parsed = AcquisitionRejection(
                need_id=need.need_id,
                record_id=rejection["record_id"],
                reason=rejection["reason"],
            )
        except (TypeError, ValueError) as error:
            raise OpportunityBriefError("query rejection is malformed") from error
        if parsed.reason != "source_repo_id equals target_repo_id":
            raise OpportunityBriefError("query rejection reason is unsupported")
        if parsed.record_id in seen_rejections:
            raise OpportunityBriefError("query rejections repeat a record_id")
        if parsed.record_id in seen_results:
            raise OpportunityBriefError("a query record is both returned and rejected")
        seen_rejections.add(parsed.record_id)
        parsed_rejections.append(parsed)
    if tuple(item.record_id for item in parsed_rejections) != tuple(
        sorted(item.record_id for item in parsed_rejections)
    ):
        raise OpportunityBriefError("query rejections are not in canonical order")
    return _ValidatedQueryResponse(
        results=tuple(parsed_results),
        rejections=tuple(parsed_rejections),
    )


def _parse_opportunity_record(
    value: object,
    *,
    target_repo_id: str,
) -> OpportunityRecordReceipt:
    record = _exact_mapping(
        value,
        field="opportunity record",
        keys={
            "problem",
            "mechanism",
            "observed_effect",
            "context",
            "boundary",
            "evidence",
            "evidence_state",
            "source_methodology_ids",
        },
    )
    effect = _exact_mapping(
        record["observed_effect"],
        field="observed_effect",
        keys={"status", "text"},
    )
    evidence = _exact_mapping(
        record["evidence"],
        field="evidence",
        keys={
            "source_repo_id",
            "source_repo_name",
            "source_revision",
            "source_revision_role",
            "license_type",
            "license_sha256",
            "source_files",
            "source_symbols",
            "source_sha256",
        },
    )
    source_repo_id = _canonical_string(
        evidence["source_repo_id"],
        field="source_repo_id",
        limit=256,
    )
    if source_repo_id == target_repo_id:
        raise OpportunityBriefError("query result source_repo_id identifies the target")
    try:
        parsed = OpportunityRecordReceipt(
            problem=_canonical_string(record["problem"], field="problem"),
            mechanism=_canonical_string(record["mechanism"], field="mechanism"),
            observed_effect=OpportunityEffect(
                status=effect["status"],
                text=_canonical_string(
                    effect["text"],
                    field="observed effect text",
                ),
            ),
            context=_canonical_string(record["context"], field="context"),
            boundary=_canonical_string(record["boundary"], field="boundary"),
            evidence=OpportunityEvidence(
                source_repo_id=source_repo_id,
                source_repo_name=_canonical_string(
                    evidence["source_repo_name"],
                    field="source_repo_name",
                    limit=256,
                ),
                source_revision=_canonical_string(
                    evidence["source_revision"],
                    field="source_revision",
                    limit=80,
                ),
                source_revision_role=evidence["source_revision_role"],
                license_type=_canonical_string(
                    evidence["license_type"],
                    field="license_type",
                    limit=64,
                ),
                license_sha256=_canonical_string(
                    evidence["license_sha256"],
                    field="license_sha256",
                    limit=64,
                ),
                source_files=_canonical_json_string_tuple(
                    evidence["source_files"],
                    field="source_files",
                    item_limit=1_024,
                ),
                source_symbols=_canonical_json_string_tuple(
                    evidence["source_symbols"],
                    field="source_symbols",
                    item_limit=512,
                ),
                source_sha256=_canonical_json_string_tuple(
                    evidence["source_sha256"],
                    field="source_sha256",
                    item_limit=64,
                    canonical=False,
                ),
            ),
            evidence_state=record["evidence_state"],
            source_methodology_ids=_canonical_json_string_tuple(
                record["source_methodology_ids"],
                field="source_methodology_ids",
                item_limit=256,
                maximum=MAX_METHODOLOGY_IDS,
            ),
        )
    except (TypeError, ValueError) as error:
        raise OpportunityBriefError("opportunity record is malformed") from error
    try:
        encoded = json.dumps(
            parsed.to_mapping(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise OpportunityBriefError("opportunity record is malformed") from error
    if len(encoded) > MAX_OPPORTUNITY_RECORD_BYTES:
        raise OpportunityBriefError("opportunity record exceeds its byte bound")
    return parsed


def _exact_mapping(value: object, *, field: str, keys: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise OpportunityBriefError(f"{field} has an unsupported schema")
    return value


def _bounded_json_list(value: object, *, field: str, maximum: int) -> list[object]:
    if type(value) is not list:
        raise OpportunityBriefError(f"{field} must be a JSON array")
    if len(value) > maximum:
        raise OpportunityBriefError(f"{field} exceed their item bound")
    return value


def _canonical_string(
    value: object,
    *,
    field: str,
    limit: int = MAX_OPPORTUNITY_TEXT,
) -> str:
    try:
        checked = _checked_string(value, field=field, limit=limit)
    except (TypeError, ValueError) as error:
        raise OpportunityBriefError(f"{field} is malformed") from error
    if checked != checked.strip():
        raise OpportunityBriefError(f"{field} is not canonical text")
    return checked


def _canonical_json_string_tuple(
    value: object,
    *,
    field: str,
    item_limit: int,
    maximum: int = MAX_EVIDENCE_ITEMS,
    canonical: bool = True,
) -> tuple[str, ...]:
    items = _bounded_json_list(value, field=field, maximum=maximum)
    result = tuple(
        _canonical_string(item, field=f"{field} item", limit=item_limit)
        for item in items
    )
    if canonical and (
        result != tuple(sorted(result)) or len(result) != len(set(result))
    ):
        raise OpportunityBriefError(f"{field} must be sorted and unique")
    return result


def _record_id(record: OpportunityRecordReceipt) -> str:
    canonical = json.dumps(
        record.to_mapping(),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"opp_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]}"


def _directory_identity(result: os.stat_result) -> DirectoryIdentity:
    return (
        result.st_dev,
        result.st_ino,
        result.st_nlink,
        result.st_size,
        result.st_mtime_ns,
        result.st_ctime_ns,
    )


def _open_pinned_root(target: Path) -> tuple[int, DirectoryIdentity]:
    descriptor: int | None = None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        before = os.lstat(target)
        if not stat.S_ISDIR(before.st_mode):
            raise OpportunityBriefError("target path must be an existing directory")
        descriptor = os.open(target, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode) or _directory_identity(opened) != _directory_identity(
            before
        ):
            raise OpportunityBriefError("target root changed during descriptor open")
        return descriptor, _directory_identity(opened)
    except OpportunityBriefError:
        if descriptor is not None:
            os.close(descriptor)
        raise
    except OSError as error:
        if descriptor is not None:
            os.close(descriptor)
        raise OpportunityBriefError("target root could not be pinned safely") from error


def _assert_root_identity(
    target: Path,
    root_descriptor: int,
    expected: DirectoryIdentity,
) -> None:
    try:
        descriptor_identity = os.fstat(root_descriptor)
        path_identity = os.lstat(target)
    except OSError as error:
        raise OpportunityBriefError("target root identity changed") from error
    if (
        not stat.S_ISDIR(descriptor_identity.st_mode)
        or not stat.S_ISDIR(path_identity.st_mode)
        or _directory_identity(descriptor_identity) != expected
        or _directory_identity(path_identity) != expected
    ):
        raise OpportunityBriefError("target root identity changed")


def _read_truth_file_names(root_descriptor: int) -> tuple[str, ...]:
    names: list[str] = []
    for name in TRUTH_FILE_NAMES:
        try:
            os.stat(name, dir_fd=root_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError as error:
            raise OpportunityBriefError("truth-file identity could not be inspected") from error
        names.append(name)
    return tuple(names)


def _read_selected_handoff(
    root_descriptor: int,
    truth_files: tuple[str, ...],
) -> HandoffEvidence | None:
    latest = "HANDOFF_LATEST.md"
    if _path_exists_nofollow(root_descriptor, latest):
        return _read_evidence(root_descriptor, latest)

    dated: list[tuple[date, str, bytes, str]] = []
    for name in _scan_directory_names(root_descriptor, _WalkBudget()):
        match = _DATED_HANDOFF_PATTERN.fullmatch(name)
        if match is None:
            continue
        try:
            parsed_date = date.fromisoformat(match.group("date"))
        except ValueError:
            continue
        dated.append((parsed_date, name.casefold(), os.fsencode(name), name))
    if dated:
        return _read_evidence(root_descriptor, max(dated)[3])
    if truth_files:
        return _read_evidence(root_descriptor, truth_files[0])
    return None


def _path_exists_nofollow(root_descriptor: int, path: str) -> bool:
    try:
        os.stat(path, dir_fd=root_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError as error:
        raise OpportunityBriefError("preferred handoff identity could not be inspected") from error
    return True


def _stat_identity(result: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        result.st_dev,
        result.st_ino,
        result.st_nlink,
        result.st_size,
        result.st_mtime_ns,
        result.st_ctime_ns,
    )


def _read_evidence(root_descriptor: int, path: str) -> HandoffEvidence:
    descriptor: int | None = None
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        before = os.stat(path, dir_fd=root_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise OpportunityBriefError("preferred handoff is not a safe regular file")
        if before.st_nlink != 1:
            raise OpportunityBriefError("preferred handoff must have exactly one link")
        descriptor = os.open(path, flags, dir_fd=root_descriptor)
        opened = os.fstat(descriptor)
        if _stat_identity(opened) != _stat_identity(before):
            raise OpportunityBriefError("preferred handoff changed during descriptor open")
        if opened.st_size > MAX_HANDOFF_BYTES:
            raise OpportunityBriefError("selected handoff exceeds the bounded size")
        raw = _read_descriptor_bounded(descriptor, MAX_HANDOFF_BYTES)
        after_descriptor = os.fstat(descriptor)
        after_path = os.stat(path, dir_fd=root_descriptor, follow_symlinks=False)
        if (
            _stat_identity(after_descriptor) != _stat_identity(opened)
            or _stat_identity(after_path) != _stat_identity(opened)
        ):
            raise OpportunityBriefError("selected handoff changed during read race")
        text = raw.decode("utf-8")
        if _contains_unsafe_text(text, multiline=True):
            raise OpportunityBriefError("selected handoff contains unsafe controls")
        return HandoffEvidence(
            relative_path=path,
            sha256=hashlib.sha256(raw).hexdigest(),
            text=text,
        )
    except OpportunityBriefError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise OpportunityBriefError("selected handoff could not be read safely") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_descriptor_bounded(descriptor: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(descriptor, min(64 * 1024, limit + 1 - total))
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        total += len(chunk)
        if total > limit:
            raise OpportunityBriefError("selected handoff exceeds the bounded size")


def _git_base_arguments(target: Path) -> list[str]:
    executable = shutil.which("git", path=os.defpath)
    if executable is None:
        raise OpportunityBriefError("Git executable is unavailable")
    return [
        executable,
        "--no-pager",
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "fetch.auto=0",
        "-c",
        "maintenance.auto=false",
        "-c",
        "submodule.recurse=false",
        "-c",
        "status.submoduleSummary=false",
        "-C",
        str(target),
    ]


def _git_environment() -> dict[str, str]:
    return {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": "/var/empty",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "XDG_CONFIG_HOME": "/var/empty",
    }


def _run_git_bounded(
    target: Path,
    arguments: tuple[str, ...],
    *,
    stdout_limit: int,
    label: str,
) -> _GitResult:
    command = [*_git_base_arguments(target), *arguments]
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_environment(),
            close_fds=True,
        )
    except OSError as error:
        raise OpportunityBriefError(f"{label} could not start") from error
    if process.stdout is None or process.stderr is None:
        _stop_process(process)
        raise OpportunityBriefError(f"{label} pipes were unavailable")

    output = bytearray()
    errors = bytearray()
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, (output, stdout_limit))
    selector.register(process.stderr, selectors.EVENT_READ, (errors, MAX_GIT_ERROR_BYTES))
    deadline = time.monotonic() + GIT_TIMEOUT_SECONDS
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _stop_process(process)
                raise OpportunityBriefError(f"{label} timed out")
            events = selector.select(min(remaining, 0.1))
            if not events:
                continue
            for key, _ in events:
                buffer, limit = key.data
                try:
                    chunk = os.read(key.fileobj.fileno(), min(8_192, limit + 1 - len(buffer)))
                except OSError as error:
                    _stop_process(process)
                    raise OpportunityBriefError(f"{label} output could not be read") from error
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                buffer.extend(chunk)
                if len(buffer) > limit:
                    _stop_process(process)
                    raise OpportunityBriefError(f"{label} output exceeds its bound")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _stop_process(process)
            raise OpportunityBriefError(f"{label} timed out")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            _stop_process(process)
            raise OpportunityBriefError(f"{label} timed out") from error
    finally:
        selector.close()
        if process.stdout and not process.stdout.closed:
            process.stdout.close()
        if process.stderr and not process.stderr.closed:
            process.stderr.close()
    return _GitResult(returncode=returncode, stdout=bytes(output), stderr=bytes(errors))


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass


def _read_git_snapshot(
    target: Path,
    root_descriptor: int,
    root_identity: DirectoryIdentity,
) -> _GitSnapshot:
    _assert_root_identity(target, root_descriptor, root_identity)
    root = _run_git_bounded(
        target,
        ("rev-parse", "--path-format=absolute", "--show-toplevel"),
        stdout_limit=MAX_GIT_ROOT_BYTES,
        label="Git root verification",
    )
    _assert_root_identity(target, root_descriptor, root_identity)
    if root.returncode != 0:
        if b"not a git repository" in root.stderr.lower():
            return _GitSnapshot(revision=None, branch=None, dirty_entries=())
        raise OpportunityBriefError("Git root verification failed")
    if root.stdout != os.fsencode(target) + b"\n":
        raise OpportunityBriefError("target path must be the exact Git worktree root")

    _assert_root_identity(target, root_descriptor, root_identity)
    status_result = _run_git_bounded(
        target,
        (
            "status",
            "--porcelain=v2",
            "-z",
            "--branch",
            "--no-renames",
            "--no-ahead-behind",
            "--ignore-submodules=all",
            "--untracked-files=normal",
        ),
        stdout_limit=MAX_GIT_STATUS_BYTES,
        label="Git status snapshot",
    )
    _assert_root_identity(target, root_descriptor, root_identity)
    if status_result.returncode != 0:
        raise OpportunityBriefError("Git status snapshot failed")
    return _parse_git_status(status_result.stdout)


def _parse_git_status(raw: bytes) -> _GitSnapshot:
    if raw and not raw.endswith(b"\0"):
        raise OpportunityBriefError("Git status snapshot is truncated")
    records = raw[:-1].split(b"\0") if raw else []
    revision: str | None = None
    branch: str | None = None
    saw_revision = False
    saw_branch = False
    dirty: list[str] = []
    entry_count = 0
    for record in records:
        if record.startswith(b"# branch.oid "):
            if saw_revision:
                raise OpportunityBriefError("Git status snapshot repeats revision metadata")
            saw_revision = True
            value = record.removeprefix(b"# branch.oid ")
            if value != b"(initial)":
                try:
                    revision = value.decode("ascii")
                except UnicodeError as error:
                    raise OpportunityBriefError("Git revision metadata is malformed") from error
                if not _REVISION_PATTERN.fullmatch(revision):
                    raise OpportunityBriefError("Git revision metadata is malformed")
            continue
        if record.startswith(b"# branch.head "):
            if saw_branch:
                raise OpportunityBriefError("Git status snapshot repeats branch metadata")
            saw_branch = True
            value = record.removeprefix(b"# branch.head ")
            if value != b"(detached)":
                branch = _display_filesystem_bytes(value)
            continue
        if record.startswith(b"# "):
            continue
        entry_count += 1
        if entry_count > MAX_DIRTY_ENTRIES:
            raise OpportunityBriefError("Git dirty-entry status exceeds its bound")
        status_code, path_bytes = _parse_status_entry(record)
        raw_path = os.fsdecode(path_bytes)
        _validate_git_relative_path(raw_path)
        if _path_is_skipped(raw_path):
            continue
        dirty.append(f"{status_code} {_display_filesystem_path(raw_path)}")
    if not saw_revision or not saw_branch:
        raise OpportunityBriefError("Git status snapshot is missing branch metadata")
    return _GitSnapshot(
        revision=revision,
        branch=branch,
        dirty_entries=tuple(sorted(set(dirty))),
    )


def _parse_status_entry(record: bytes) -> tuple[str, bytes]:
    if record.startswith(b"? "):
        return "?", record[2:]
    if record.startswith(b"! "):
        return "!", record[2:]
    if record.startswith(b"1 "):
        parts = record.split(b" ", 8)
        if len(parts) == 9 and len(parts[1]) == 2:
            try:
                return parts[1].decode("ascii"), parts[8]
            except UnicodeError as error:
                raise OpportunityBriefError("Git status code is malformed") from error
    if record.startswith(b"u "):
        parts = record.split(b" ", 10)
        if len(parts) == 11 and len(parts[1]) == 2:
            try:
                return parts[1].decode("ascii"), parts[10]
            except UnicodeError as error:
                raise OpportunityBriefError("Git status code is malformed") from error
    raise OpportunityBriefError("Git status snapshot contains a malformed entry")


def _validate_git_relative_path(value: str) -> None:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise OpportunityBriefError("Git status snapshot contains an unsafe path")


def _display_filesystem_bytes(value: bytes) -> str:
    return _display_filesystem_path(os.fsdecode(value))


def _display_filesystem_path(value: str) -> str:
    display: list[str] = []
    for character in value:
        codepoint = ord(character)
        if character == "\\":
            display.append("\\\\")
        elif 0x20 <= codepoint <= 0x7E:
            display.append(character)
        elif codepoint <= 0xFF:
            display.append(f"\\x{codepoint:02x}")
        elif codepoint <= 0xFFFF:
            display.append(f"\\u{codepoint:04x}")
        else:
            display.append(f"\\U{codepoint:08x}")
    return "".join(display)


def _scan_directory_names(directory_descriptor: int, budget: _WalkBudget) -> tuple[str, ...]:
    names: list[str] = []
    try:
        with os.scandir(directory_descriptor) as iterator:
            for entry in iterator:
                budget.entries += 1
                if budget.entries > MAX_TARGET_ENTRIES:
                    raise OpportunityBriefError("target entry inspection exceeds its bound")
                names.append(entry.name)
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError("target directory could not be inspected") from error
    return tuple(sorted(names, key=lambda item: (item.casefold(), os.fsencode(item))))


def _read_visible_gaps(root_descriptor: int) -> tuple[str, ...]:
    gaps: list[str] = []
    budget = _WalkBudget()
    _walk_visible_gaps(root_descriptor, (), budget, gaps)
    return tuple(gaps)


def _walk_visible_gaps(
    directory_descriptor: int,
    relative_parts: tuple[str, ...],
    budget: _WalkBudget,
    gaps: list[str],
) -> None:
    budget.directories += 1
    if budget.directories > MAX_INSPECTED_DIRECTORIES:
        raise OpportunityBriefError("target directory inspection exceeds its bound")
    for name in _scan_directory_names(directory_descriptor, budget):
        child_parts = (*relative_parts, name)
        raw_relative = "/".join(child_parts)
        try:
            identity = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
        except OSError as error:
            raise OpportunityBriefError("target changed during file inspection") from error
        if stat.S_ISLNK(identity.st_mode):
            continue
        if stat.S_ISDIR(identity.st_mode):
            if _path_is_skipped(raw_relative):
                continue
            _walk_child_directory(
                directory_descriptor,
                name,
                identity,
                child_parts,
                budget,
                gaps,
            )
            continue
        if not stat.S_ISREG(identity.st_mode) or _path_is_skipped(raw_relative):
            continue
        budget.files += 1
        if budget.files > MAX_INSPECTED_FILES:
            raise OpportunityBriefError("target file inspection exceeds its bound")
        if Path(name).suffix.casefold() not in _TEXT_SUFFIXES:
            continue
        text = _read_gap_text(directory_descriptor, name, identity)
        if text is None:
            continue
        display_relative = _display_filesystem_path(raw_relative)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not _GAP_PATTERN.search(line):
                continue
            if len(gaps) >= MAX_GAPS:
                raise OpportunityBriefError("visible gap inspection exceeds its bound")
            excerpt = " ".join(line.strip().split())[:240]
            if _contains_unsafe_text(excerpt):
                continue
            gaps.append(f"{display_relative}:{line_number}: {excerpt}")


def _walk_child_directory(
    parent_descriptor: int,
    name: str,
    before: os.stat_result,
    relative_parts: tuple[str, ...],
    budget: _WalkBudget,
    gaps: list[str],
) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_descriptor,
        )
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or _directory_identity(opened) != _directory_identity(before)
        ):
            raise OpportunityBriefError("target directory changed during descriptor open")
        _walk_visible_gaps(descriptor, relative_parts, budget, gaps)
        after_descriptor = os.fstat(descriptor)
        after_path = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            not stat.S_ISDIR(after_path.st_mode)
            or _directory_identity(after_descriptor) != _directory_identity(opened)
            or _directory_identity(after_path) != _directory_identity(opened)
        ):
            raise OpportunityBriefError("target directory changed during inspection")
    except OpportunityBriefError:
        raise
    except OSError as error:
        raise OpportunityBriefError("target directory changed during inspection") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_gap_text(
    directory_descriptor: int,
    name: str,
    before: os.stat_result,
) -> str | None:
    if before.st_nlink != 1 or before.st_size > MAX_HANDOFF_BYTES:
        return None
    descriptor: int | None = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory_descriptor,
        )
        opened = os.fstat(descriptor)
        if _stat_identity(opened) != _stat_identity(before):
            raise OpportunityBriefError("target file changed during descriptor open")
        raw = _read_descriptor_bounded(descriptor, MAX_HANDOFF_BYTES)
        after = os.fstat(descriptor)
        after_path = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
        if (
            _stat_identity(after) != _stat_identity(opened)
            or _stat_identity(after_path) != _stat_identity(opened)
        ):
            raise OpportunityBriefError("target file changed during inspection")
        return raw.decode("utf-8")
    except OpportunityBriefError:
        raise
    except UnicodeError:
        return None
    except OSError as error:
        raise OpportunityBriefError("target file changed during inspection") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _path_is_skipped(relative_path: str) -> bool:
    for part in PurePosixPath(relative_path).parts:
        normalized = re.sub(r"[\s-]+", "_", part.casefold())
        if normalized in _SKIPPED_DIRECTORY_NAMES:
            return True
    return False


def _default_target_repo_id(target: Path) -> str:
    name = unicodedata.normalize("NFKC", target.name).casefold()
    slug = re.sub(r"[^a-z0-9._-]+", "-", name).strip("-.") or "repository"
    digest = hashlib.sha256(os.fsencode(target)).hexdigest()[:24]
    return f"local:{slug}:{digest}"


def _find_checkout_conflicts(
    handoff: HandoffEvidence | None,
    *,
    revision: str | None,
    branch: str | None,
) -> tuple[str, ...]:
    if handoff is None:
        return ()
    conflicts: list[str] = []
    for line in _visible_markdown_lines(handoff.text):
        if line is None:
            continue
        claim = _CHECKOUT_CLAIM_PATTERN.fullmatch(line)
        if claim is None:
            continue
        label = claim.group("label").casefold()
        raw_value = claim.group("value").strip()
        token = _balanced_claim_token(raw_value)
        if label == "branch":
            if token is None:
                conflicts.append(
                    f"handoff branch claim {raw_value!r} is malformed"
                )
            elif branch is not None and token != branch:
                conflicts.append(
                    f"handoff branch {token!r} conflicts with live branch {branch!r}"
                )
        elif token is None or re.fullmatch(r"[0-9a-f]{7,64}", token, re.IGNORECASE) is None:
            conflicts.append(
                f"handoff {label} claim {raw_value!r} is malformed"
            )
        elif revision is not None and not revision.casefold().startswith(token.casefold()):
            conflicts.append(
                f"handoff {label} {token!r} conflicts with live revision {revision!r}"
            )
    return tuple(dict.fromkeys(conflicts))


def _balanced_claim_token(value: str) -> str | None:
    if not value:
        return None
    if value.startswith("`") or value.endswith("`"):
        if len(value) < 3 or not value.startswith("`") or not value.endswith("`"):
            return None
        if value.count("`") != 2:
            return None
        value = value[1:-1]
    elif "`" in value:
        return None
    if not value or any(character.isspace() for character in value):
        return None
    return value


def _validate_need_bounds(minimum: int, maximum: int) -> None:
    if (
        isinstance(minimum, bool)
        or isinstance(maximum, bool)
        or not isinstance(minimum, int)
        or not isinstance(maximum, int)
        or minimum < 3
        or maximum > 7
        or minimum > maximum
    ):
        raise OpportunityBriefError("need bounds must satisfy 3 <= minimum <= maximum <= 7")


def _visible_markdown_lines(text: str) -> tuple[str | None, ...]:
    if _contains_unsafe_text(text, multiline=True):
        raise OpportunityBriefError("handoff Markdown contains unsafe controls")
    visible: list[str | None] = []
    in_comment = False
    fence_character: str | None = None
    fence_length = 0
    html_mode: str | None = None
    html_token = ""
    for raw_line in text.splitlines():
        if len(visible) >= MAX_MARKDOWN_LINES:
            raise OpportunityBriefError("handoff Markdown line count exceeds its bound")
        line, in_comment = _without_html_comments(raw_line, in_comment)
        if fence_character is not None:
            closing = re.match(
                rf"^\s{{0,3}}{re.escape(fence_character)}{{{fence_length},}}\s*$",
                line,
            )
            if closing:
                fence_character = None
                fence_length = 0
            visible.append(None)
            continue
        if html_mode is not None:
            if _html_block_finished(html_mode, html_token, line):
                html_mode = None
                html_token = ""
            visible.append(None)
            continue
        if _is_indented_markdown_code(raw_line):
            visible.append(None)
            continue
        fence = _FENCE_PATTERN.match(line)
        if fence:
            marker = fence.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            visible.append(None)
            continue
        html_block = _html_block_start(line)
        if html_block is not None:
            mode, token = html_block
            if not _html_block_finished(mode, token, line):
                html_mode, html_token = mode, token
            visible.append(None)
            continue
        visible.append(line)
    return tuple(visible)


def _html_block_start(line: str) -> tuple[str, str] | None:
    raw_html = _RAW_HTML_OPEN_PATTERN.match(line)
    if raw_html:
        return "closing_tag", raw_html.group("tag").casefold()
    if re.match(r"^\s{0,3}<\?", line):
        return "terminator", "?>"
    if re.match(r"^\s{0,3}<!\[CDATA\[", line):
        return "terminator", "]]>"
    if re.match(r"^\s{0,3}<![A-Z]", line):
        return "terminator", ">"
    if re.match(r"^\s{0,3}</?[A-Za-z][A-Za-z0-9-]*(?:\s|/?>|$)", line):
        return "blank", ""
    return None


def _html_block_finished(mode: str, token: str, line: str) -> bool:
    if mode == "blank":
        return not line.strip()
    if mode == "closing_tag":
        return re.search(rf"</\s*{re.escape(token)}\s*>", line, re.IGNORECASE) is not None
    return token in line


def _is_indented_markdown_code(line: str) -> bool:
    columns = 0
    for character in line:
        if character == " ":
            columns += 1
        elif character == "\t":
            columns += 4 - (columns % 4)
        else:
            break
        if columns >= 4:
            return True
    return False


def _without_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    remaining = line
    parts: list[str] = []
    while remaining:
        if in_comment:
            end = remaining.find("-->")
            if end < 0:
                return "".join(parts), True
            remaining = remaining[end + 3 :]
            in_comment = False
            continue
        start = remaining.find("<!--")
        if start < 0:
            parts.append(remaining)
            break
        parts.append(remaining[:start])
        remaining = remaining[start + 4 :]
        in_comment = True
    return "".join(parts), in_comment


def _parse_candidates(text: str) -> tuple[_Candidate, ...]:
    lines = _visible_markdown_lines(text)
    current_category: NeedCategory | None = None
    candidates: list[_Candidate] = []
    source_order = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        if line is None:
            index += 1
            continue
        if (
            index + 1 < len(lines)
            and lines[index + 1] is not None
            and _SETEXT_PATTERN.fullmatch(lines[index + 1] or "")
            and line.strip()
            and _BULLET_PATTERN.fullmatch(line) is None
        ):
            current_category = _category_for_heading(line.strip())
            index += 2
            continue
        heading = _heading_text(line)
        if heading is not None:
            current_category = _category_for_heading(heading)
            index += 1
            continue
        if _SETEXT_PATTERN.fullmatch(line):
            current_category = None
            index += 1
            continue
        if current_category is not None:
            bullet = _BULLET_PATTERN.fullmatch(line)
            if bullet is not None:
                source_order += 1
                if source_order > MAX_SECTION_BULLETS:
                    raise OpportunityBriefError("handoff bullet count exceeds its bound")
                handoff_span = bullet.group(1).strip()
                if not handoff_span:
                    index += 1
                    continue
                if len(handoff_span) > MAX_BULLET_CHARS:
                    raise OpportunityBriefError("handoff bullet length exceeds its bound")
                priority, problem = _strip_priority(handoff_span)
                normalized = _normalize_span(problem)
                if normalized:
                    candidates.append(
                        _Candidate(
                            category=current_category,
                            priority=priority,
                            source_order=source_order,
                            handoff_span=handoff_span,
                            problem=problem,
                            normalized_problem=normalized,
                        )
                    )
        index += 1
    return tuple(candidates)


def _heading_text(line: str) -> str | None:
    atx = _ATX_HEADING_PATTERN.fullmatch(line)
    if atx:
        return atx.group(1)
    plain = _PLAIN_HEADING_PATTERN.fullmatch(line)
    if plain:
        return plain.group(1)
    return None


def _category_for_heading(heading: str) -> NeedCategory | None:
    normalized = unicodedata.normalize("NFKC", heading).casefold()
    normalized = normalized.replace("&", " ").replace("/", " ")
    normalized = " ".join(re.sub(r"[^a-z ]+", " ", normalized).split())
    return _SECTION_CATEGORIES.get(normalized)


def _strip_priority(handoff_span: str) -> tuple[int, str]:
    match = _PRIORITY_PATTERN.match(handoff_span)
    if match is None:
        return 3, handoff_span.strip()
    label = (match.group(1) or match.group(2)).casefold()
    return int(label[1]), handoff_span[match.end() :].strip()


def _normalize_span(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized)
    return " ".join(normalized.split())


def _canonical_need_id(category: NeedCategory, problem: str) -> str:
    identity_input = f"{category}\0{_normalize_span(problem)}".encode("utf-8")
    return f"need_{hashlib.sha256(identity_input).hexdigest()[:24]}"


def _to_need_theme(candidate: _Candidate) -> NeedTheme:
    label = _CATEGORY_LABELS[candidate.category]
    return NeedTheme(
        need_id=_canonical_need_id(candidate.category, candidate.problem),
        category=candidate.category,
        problem=candidate.problem,
        desired_improvement=(
            f"Resolve the recorded {label} with an auditable, transferable improvement."
        ),
        existing_evidence=(
            f"The selected handoff records this {label}: {candidate.handoff_span}"
        ),
        gap="Independent source-grounded evidence for a transferable mechanism is not attached.",
        query_text=(
            f"{candidate.problem} source-grounded evidence transferable mechanism verification"
        ),
        handoff_span=candidate.handoff_span,
    )


def render_opportunity_brief(snapshot: WipSnapshot, ranking: object) -> str:
    """Render selected opportunities without converting them into a build plan."""

    from tools.opportunity_ranker import RankingResult

    if type(snapshot) is not WipSnapshot:
        raise TypeError("snapshot must be a WipSnapshot")
    snapshot.__post_init__()
    if type(ranking) is not RankingResult:
        raise TypeError("ranking must be a RankingResult")
    ranking.__post_init__()

    revision = snapshot.target_revision or "not available"
    branch = snapshot.branch or "not available"
    handoff = snapshot.handoff.relative_path if snapshot.handoff is not None else "not available"
    lines = [
        "# Cross-Repo Opportunity Brief",
        "",
        "## Starting point",
        "",
        f"- Target: {_brief_scalar(snapshot.target_repo_id)}",
        f"- Target path: {_brief_scalar(str(snapshot.target_path))}",
        f"- Revision: {_brief_scalar(revision)}",
        f"- Branch: {_brief_scalar(branch)}",
        f"- Handoff: {_brief_scalar(handoff)}",
        "- Verification: Not run; candidates remain inspection hypotheses.",
        "",
        "## Cross-repo opportunities",
        "",
    ]
    if not ranking.selected:
        lines.append(
            f"- No opportunity met the frozen inspection threshold ({ranking.minimum_score:.2f})."
        )
    for item in ranking.selected:
        record = item.record
        effect_label = {
            "observed": "Observed",
            "intended": "Intended",
            "negative": "Negative",
        }[record.observed_effect.status]
        evidence = record.evidence
        files = ", ".join(evidence.source_files)
        symbols = ", ".join(evidence.source_symbols)
        negative = record.observed_effect.status == "negative"
        title_prefix = "Negative lesson: " if negative else ""
        inference_label = (
            "Why this negative lesson matters here (Inference)"
            if negative
            else "Why it may help here (Inference)"
        )
        lines.extend(
            (
                f"### {title_prefix}{_brief_scalar(record.mechanism)}",
                f"- Problem: {_brief_scalar(record.problem)}",
                f"- Mechanism: {_brief_scalar(record.mechanism)}",
                (
                    f"- Observed effect: {effect_label} — "
                    f"{_brief_scalar(record.observed_effect.text)}"
                ),
                f"- Context: {_brief_scalar(record.context)}",
                f"- Boundary: {_brief_scalar(record.boundary)}",
                f"- {inference_label}: {_brief_scalar(item.inference)}",
                (
                    f"- Evidence: {_brief_scalar(evidence.source_repo_name)}@"
                    f"{_brief_scalar(evidence.source_revision)}; "
                    f"files: {_brief_scalar(files)}; "
                    f"symbols: {_brief_scalar(symbols)}; "
                    f"{_brief_scalar(evidence.license_type)}"
                ),
                "",
            )
        )

    lines.extend(("## What CAM did not find", ""))
    if ranking.rejected:
        for item in ranking.rejected:
            lines.append(
                f"- {_brief_scalar(item.source_repo_name)}: {item.reason.replace('_', ' ')}."
            )
    elif not ranking.selected:
        for audit in ranking.need_audit:
            lines.append(
                f"- No selected source-grounded candidate for: {_brief_scalar(audit.problem)}"
            )
    else:
        lines.append("- No additional acquired candidate was rejected.")
    rendered = "\n".join(lines).rstrip() + "\n"
    _validate_rendered_brief(rendered)
    return rendered


def _brief_scalar(value: str) -> str:
    """Keep record prose inside one Markdown field without adding source text."""

    checked = _checked_string(value, field="brief field", limit=MAX_PUBLIC_TEXT)
    collapsed = " ".join(checked.split())
    if re.search(r"\b(?:sufficient|implemented|confirmed)\b", collapsed, re.I):
        collapsed = "source statement withheld: ambiguous status language"
    elif _looks_code_shaped(collapsed):
        collapsed = "source statement withheld: code-shaped content"
    escaped = html.escape(collapsed, quote=True)
    return re.sub(r"([\\`*_\[\]])", r"\\\1", escaped)


def _looks_code_shaped(value: str) -> bool:
    return bool(
        re.search(
            r"(?:```|~~~|source[_ -]?excerpt|"
            r"<\s*/?\s*(?:script|style|pre|code)\b|"
            r"(?:^|\s)(?:def|class|function|import)\s+[A-Za-z_]|"
            r"(?:^|\s)return\s+|=>|:=)",
            value,
            re.I,
        )
    )


def _validate_rendered_brief(rendered: str) -> None:
    lowered = rendered.casefold()
    if re.search(r"\b(?:sufficient|implemented|confirmed)\b", lowered):
        raise OpportunityBriefError("brief contains ambiguous CAM status language")
    if _looks_code_shaped(rendered):
        raise OpportunityBriefError("brief contains code-shaped source content")
    if re.search(r"(?<!\\)!?\[[^\]\n]*\]\([^\n)]*\)", rendered):
        raise OpportunityBriefError("brief contains an unsafe dynamic Markdown link")
    if re.search(r"<\s*[A-Za-z!/?]", rendered):
        raise OpportunityBriefError("brief contains unsafe raw HTML")


__all__ = [
    "AcquisitionCall",
    "AcquisitionGap",
    "AcquisitionReceipt",
    "AcquisitionRejection",
    "CandidateMatch",
    "ExecutionClosureReceipt",
    "HandoffEvidence",
    "InterpreterSymlinkReceipt",
    "NeedTheme",
    "OpportunityCandidate",
    "OpportunityBriefError",
    "OpportunityEffect",
    "OpportunityEvidence",
    "OpportunityRecordReceipt",
    "WipSnapshot",
    "acquire_opportunities",
    "extract_need_themes",
    "inspect_wip_repository",
    "render_opportunity_brief",
]
