"""Read bounded WIP evidence and derive source-linked opportunity needs.

This module stops at target inspection and need description. It never runs the
target, loads a provider, opens CAM data, or creates implementation steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import shutil
import stat
import subprocess
import time
from typing import Literal
import unicodedata


VerificationStatus = Literal["not_run"]
NeedCategory = Literal["blocker", "risk", "next_action", "open_question"]
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

TRUTH_FILE_NAMES = (
    "GOAL.md",
    "STANDARDS.md",
    "IMPLEMENT.md",
    "DECISIONS.md",
    "PROGRESS.md",
    "TASK_QUEUE.md",
    "AGENTS.md",
)

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
_BULLET_PATTERN = re.compile(r"^\s*(?:[-*+]\s+|\d{1,3}[.)]\s+)(.+?)\s*$")
_PRIORITY_PATTERN = re.compile(
    r"^\s*(?:\[\s*(P[0-2])\s*\]\s*:?\s*|\*{0,2}(P[0-2])\*{0,2}\s*:)\s*",
    re.IGNORECASE,
)
_BRANCH_CLAIM_PATTERN = re.compile(
    r"^\s*(?:[-*+]\s+)?\*{0,2}branch\*{0,2}\s*:\s*`?([^`\s]+)`?\s*$",
    re.IGNORECASE,
)
_REVISION_CLAIM_PATTERN = re.compile(
    r"^\s*(?:[-*+]\s+)?\*{0,2}(?:revision|head|commit)\*{0,2}\s*:\s*"
    r"`?([0-9a-f]{7,64})`?\s*$",
    re.IGNORECASE,
)
_REVISION_CLAIM_ANY_PATTERN = re.compile(
    r"^\s*(?:[-*+]\s+)?\*{0,2}(?:revision|head|commit)\*{0,2}\s*:\s*"
    r"`?([^`\s]+)`?\s*$",
    re.IGNORECASE,
)
_RAW_HTML_OPEN_PATTERN = re.compile(
    r"^\s{0,3}<(?P<tag>pre|script|style|textarea)(?:\s|>|$)",
    re.IGNORECASE,
)
_HEX_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REVISION_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_NEED_ID_PATTERN = re.compile(r"^need_[A-Za-z0-9._-]{4,64}$")

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
    """Deeply immutable snapshot of bounded target evidence."""

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
        for item in truth:
            _checked_relative_path(item, field="truth_files item")
        gaps = _checked_tuple(self.visible_gaps, field="visible_gaps", item_limit=4_096)
        if len(gaps) > MAX_GAPS:
            raise ValueError("visible_gaps exceeds its bound")
        _checked_tuple(self.conflicts, field="conflicts", item_limit=4_096)
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
    return _GitSnapshot(revision=revision, branch=branch, dirty_entries=tuple(dirty))


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
        branch_match = _BRANCH_CLAIM_PATTERN.fullmatch(line)
        if branch_match:
            claimed_branch = branch_match.group(1)
            if branch is not None and claimed_branch != branch:
                conflicts.append(
                    f"handoff branch {claimed_branch!r} conflicts with live branch {branch!r}"
                )
            continue
        revision_match = _REVISION_CLAIM_PATTERN.fullmatch(line)
        if revision_match:
            if revision is not None:
                claimed_revision = revision_match.group(1)
                if not revision.casefold().startswith(claimed_revision.casefold()):
                    conflicts.append(
                        f"handoff revision {claimed_revision!r} conflicts with live revision {revision!r}"
                    )
            continue
        malformed_revision = _REVISION_CLAIM_ANY_PATTERN.fullmatch(line)
        if malformed_revision:
            conflicts.append(
                f"handoff revision claim {malformed_revision.group(1)!r} is malformed"
            )
    return tuple(dict.fromkeys(conflicts))


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
    raw_html_tag: str | None = None
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
        if raw_html_tag is not None:
            if re.search(rf"</\s*{re.escape(raw_html_tag)}\s*>", line, re.IGNORECASE):
                raw_html_tag = None
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
        raw_html = _RAW_HTML_OPEN_PATTERN.match(line)
        if raw_html:
            tag = raw_html.group("tag").casefold()
            if re.search(rf"</\s*{re.escape(tag)}\s*>", line, re.IGNORECASE) is None:
                raw_html_tag = tag
            visible.append(None)
            continue
        visible.append(line)
    return tuple(visible)


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


__all__ = [
    "HandoffEvidence",
    "NeedTheme",
    "OpportunityBriefError",
    "WipSnapshot",
    "extract_need_themes",
    "inspect_wip_repository",
]
