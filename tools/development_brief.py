#!/usr/bin/env python3
"""Typed, read-only presentation contract for CAM_Codx Development Briefs.

This module deliberately begins with pure data validation and Markdown
rendering.  Target inspection and CAM retrieval are added in later plan tasks.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class BriefValidationError(ValueError):
    """Raised when a Development Brief payload is incomplete or ambiguous."""


class EvidenceClass(str, Enum):
    DIRECT_PRECEDENT = "direct_precedent"
    TRANSFERABLE_ANALOGY = "transferable_analogy"
    NEW_HYPOTHESIS = "new_hypothesis"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_EVIDENCE_LABELS = {
    EvidenceClass.DIRECT_PRECEDENT: "Direct precedent",
    EvidenceClass.TRANSFERABLE_ANALOGY: "Transferable analogy",
    EvidenceClass.NEW_HYPOTHESIS: "New hypothesis",
}

_TRUTH_FILES = (
    "GOAL.md",
    "STANDARDS.md",
    "IMPLEMENT.md",
    "DECISIONS.md",
    "PROGRESS.md",
    "TASK_QUEUE.md",
    "AGENTS.md",
)
_GAP_MARKERS = ("TODO", "FIXME", "NotImplemented")
_SKIPPED_DIRECTORIES = {".git", ".venv", "node_modules", "vendor", "build", "dist", ".direnv"}
_SENSITIVE_NAME_MARKERS = (".env", "secret", "credential", "private", "token", "key")
_MAX_INSPECTED_FILES = 200
_MAX_FILE_BYTES = 256 * 1024
_TERM_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*")
_NON_SIGNAL_TERMS = {"a", "an", "and", "build", "for", "in", "of", "the", "to", "with"}


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BriefValidationError(f"{field_name} must be non-empty")
    return value.strip()


@dataclass(frozen=True)
class BriefRequest:
    mode: str
    task_text: str

    def __post_init__(self) -> None:
        if self.mode not in {"new", "continue-rescue"}:
            raise BriefValidationError("mode must be 'new' or 'continue-rescue'")
        object.__setattr__(self, "task_text", _required_text(self.task_text, "task_text"))


@dataclass(frozen=True)
class EvidenceItem:
    evidence_class: EvidenceClass
    title: str
    source_id: str
    source_kind: str
    why_it_applies: str
    confidence: Confidence
    limitation: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_class, EvidenceClass):
            raise BriefValidationError("evidence class must be a known EvidenceClass")
        if not isinstance(self.confidence, Confidence):
            raise BriefValidationError("confidence must be a known Confidence")
        for field_name in (
            "title",
            "source_id",
            "source_kind",
            "why_it_applies",
            "limitation",
        ):
            object.__setattr__(self, field_name, _required_text(getattr(self, field_name), field_name))


@dataclass(frozen=True)
class TargetEvidence:
    category: str
    summary: str
    source_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", _required_text(self.category, "category"))
        object.__setattr__(self, "summary", _required_text(self.summary, "summary"))
        if self.source_path is not None:
            object.__setattr__(self, "source_path", _required_text(self.source_path, "source_path"))


@dataclass(frozen=True)
class NextStep:
    kind: str
    summary: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _required_text(self.kind, "next-step kind"))
        object.__setattr__(self, "summary", _required_text(self.summary, "next-step summary"))


@dataclass(frozen=True)
class TargetInspection:
    """Facts collected from one named target without running its code."""

    target_path: Path
    is_git_repository: bool
    branch: str | None
    read_truth_files: tuple[str, ...]
    missing_truth_files: tuple[str, ...]
    dirty_entries: tuple[str, ...]
    visible_gaps: tuple[str, ...]
    risks: tuple[str, ...]
    verification_status: str

    def __post_init__(self) -> None:
        if self.verification_status != "not_run":
            raise BriefValidationError("verification_status must be 'not_run' for read-only inspection")


@dataclass(frozen=True)
class ContinueRescueAdvice:
    """An explicitly limited recommendation derived from target facts."""

    action: str
    reasons: tuple[str, ...]
    limitation: str
    recommended_next_step: NextStep

    def __post_init__(self) -> None:
        if self.action not in {"continue", "mitigate", "re-develop"}:
            raise BriefValidationError("continue/rescue action is invalid")
        if not self.reasons:
            raise BriefValidationError("continue/rescue advice requires reasons")
        object.__setattr__(self, "limitation", _required_text(self.limitation, "advice limitation"))


@dataclass(frozen=True)
class DevelopmentBrief:
    request: BriefRequest
    target_evidence: tuple[TargetEvidence, ...]
    evidence_items: tuple[EvidenceItem, ...]
    recommendation: str
    recommended_next_step: NextStep
    optional_next_steps: tuple[NextStep, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.request, BriefRequest):
            raise BriefValidationError("request must be a BriefRequest")
        if not isinstance(self.recommended_next_step, NextStep):
            raise BriefValidationError("recommended_next_step must be a NextStep")
        object.__setattr__(self, "recommendation", _required_text(self.recommendation, "recommendation"))
        for item in self.target_evidence:
            if not isinstance(item, TargetEvidence):
                raise BriefValidationError("target_evidence must contain TargetEvidence")
        for item in self.evidence_items:
            if not isinstance(item, EvidenceItem):
                raise BriefValidationError("evidence_items must contain EvidenceItem")
        for item in self.optional_next_steps:
            if not isinstance(item, NextStep):
                raise BriefValidationError("optional_next_steps must contain NextStep")
        cleaned_limits = tuple(_required_text(item, "limitation") for item in self.limitations)
        object.__setattr__(self, "limitations", cleaned_limits)


def _is_sensitive_path(path: Path) -> bool:
    name = path.name.lower()
    return any(marker in name for marker in _SENSITIVE_NAME_MARKERS)


def _read_limited_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _git_status_read_only(target: Path) -> tuple[bool, str | None, tuple[str, ...]]:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            ["git", "-C", str(target), "status", "--short", "--branch", "--untracked-files=all"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, None, ()
    if completed.returncode != 0:
        return False, None, ()
    lines = tuple(line for line in completed.stdout.splitlines() if line.strip())
    branch = lines[0][3:].strip() if lines and lines[0].startswith("## ") else None
    dirty = tuple(line for line in lines if not line.startswith("## "))
    return True, branch, dirty


def _visible_gap_markers(target: Path) -> tuple[str, ...]:
    findings: list[str] = []
    inspected = 0
    for path in sorted(target.rglob("*")):
        if inspected >= _MAX_INSPECTED_FILES:
            break
        if not path.is_file() or any(part in _SKIPPED_DIRECTORIES for part in path.parts):
            continue
        if _is_sensitive_path(path):
            continue
        text = _read_limited_text(path)
        if text is None or "\x00" in text:
            continue
        inspected += 1
        relative_path = path.relative_to(target)
        for line_number, line in enumerate(text.splitlines(), start=1):
            for marker in _GAP_MARKERS:
                if marker in line:
                    findings.append(f"{relative_path}:{line_number}: {marker}")
    return tuple(findings)


def inspect_target_read_only(target_path: Path) -> TargetInspection:
    """Inspect a single, explicitly named repository without executing it."""

    target = Path(target_path).expanduser().resolve()
    if not target.is_dir():
        raise BriefValidationError(f"target repository is not a directory: {target}")

    read_truth_files: list[str] = []
    missing_truth_files: list[str] = []
    for name in _TRUTH_FILES:
        candidate = target / name
        if candidate.is_file() and _read_limited_text(candidate) is not None:
            read_truth_files.append(name)
        else:
            missing_truth_files.append(name)

    is_git_repository, branch, dirty_entries = _git_status_read_only(target)
    risks: list[str] = []
    if not is_git_repository:
        risks.append("target is not a Git repository")
    if not read_truth_files:
        risks.append("target has no readable repository truth files")

    return TargetInspection(
        target_path=target,
        is_git_repository=is_git_repository,
        branch=branch,
        read_truth_files=tuple(read_truth_files),
        missing_truth_files=tuple(missing_truth_files),
        dirty_entries=dirty_entries,
        visible_gaps=_visible_gap_markers(target),
        risks=tuple(risks),
        verification_status="not_run",
    )


def recommend_continue_rescue(
    inspection: TargetInspection,
    *,
    current_test_receipt: str | None = None,
) -> ContinueRescueAdvice:
    """Give advisory, deterministic continuation advice from observable facts."""

    if not inspection.is_git_repository or inspection.risks or len(inspection.missing_truth_files) >= 2:
        reasons = list(inspection.risks)
        if inspection.missing_truth_files:
            reasons.append("repository truth is missing or incomplete")
        return ContinueRescueAdvice(
            action="re-develop",
            reasons=tuple(reasons),
            limitation="This is advisory; a human must review whether re-development is proportionate.",
            recommended_next_step=NextStep(
                kind="prepare_redevelopment_plan",
                summary="Preserve useful evidence, then create a bounded re-development plan.",
            ),
        )

    if (
        current_test_receipt == "passed"
        and not inspection.dirty_entries
        and not inspection.visible_gaps
        and not inspection.missing_truth_files
    ):
        return ContinueRescueAdvice(
            action="continue",
            reasons=("current test receipt passed and no structural red flags were observed",),
            limitation="This does not prove product completeness or replace a focused change review.",
            recommended_next_step=NextStep(
                kind="continue_smallest_step",
                summary="Implement the smallest planned increment and run its named verification.",
            ),
        )

    reasons: list[str] = []
    if inspection.dirty_entries:
        reasons.append("dirty worktree entries need review before further changes")
    if inspection.visible_gaps:
        reasons.append("visible gap markers need bounded investigation")
    if current_test_receipt != "passed":
        reasons.append("current verification evidence is unavailable or not passing")
    if inspection.missing_truth_files:
        reasons.append("some repository truth files are absent")
    return ContinueRescueAdvice(
        action="mitigate",
        reasons=tuple(reasons),
        limitation="The recommendation is advisory; confirm the named gap with focused verification.",
        recommended_next_step=NextStep(
            kind="prepare_mitigation_plan",
            summary="Choose one bounded gap, define its verification, and repair it before expanding scope.",
        ),
    )


def _terms(value: str) -> set[str]:
    return {term for term in _TERM_PATTERN.findall(value.lower()) if term not in _NON_SIGNAL_TERMS}


def _validate_primary_payload(payload: object, query: str) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise BriefValidationError("CAM brief-query output must be a JSON object")
    if payload.get("schema_version") != 1:
        raise BriefValidationError("CAM brief-query schema_version is unsupported")
    if payload.get("scope") != "primary_only":
        raise BriefValidationError("CAM brief-query response exceeds the primary-only scope")
    if payload.get("query") != query.strip():
        raise BriefValidationError("CAM brief-query response query does not match the request")
    results = payload.get("results")
    if not isinstance(results, list):
        raise BriefValidationError("CAM brief-query response results must be a list")
    required_keys = {
        "methodology_id",
        "problem_description",
        "methodology_notes",
        "tags",
        "language",
        "lifecycle_state",
        "text_score",
    }
    for result in results:
        if not isinstance(result, dict) or not required_keys.issubset(result):
            raise BriefValidationError("CAM brief-query result is missing provenance fields")
        if not isinstance(result["methodology_id"], str) or not result["methodology_id"].strip():
            raise BriefValidationError("CAM brief-query result methodology_id is invalid")
        if not isinstance(result["tags"], list) or not all(isinstance(tag, str) for tag in result["tags"]):
            raise BriefValidationError("CAM brief-query result tags are invalid")
    return payload


def query_primary_corpus_read_only(
    query: str,
    *,
    cam_command: Path,
    cam_database: Path,
    limit: int = 5,
) -> dict[str, object]:
    """Call CAM's explicit no-write primary query with an argv list only."""

    clean_query = _required_text(query, "query")
    command = Path(cam_command).expanduser()
    database = Path(cam_database).expanduser()
    if not command.is_absolute() or not database.is_absolute():
        raise BriefValidationError("cam_command and cam_database must be absolute paths")
    if not command.is_file() or not os.access(command, os.X_OK):
        raise BriefValidationError(f"cam_command is not executable: {command}")
    if not database.is_file():
        raise BriefValidationError(f"cam_database is not a file: {database}")
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise BriefValidationError("limit must be an integer between 1 and 20")

    try:
        completed = subprocess.run(
            [
                str(command),
                "brief-query",
                clean_query,
                "--db",
                str(database),
                "--limit",
                str(limit),
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BriefValidationError(f"CAM brief-query could not run: {exc}") from exc
    if completed.returncode != 0:
        raise BriefValidationError("CAM brief-query returned a nonzero exit status")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BriefValidationError("CAM brief-query did not return valid JSON") from exc
    return _validate_primary_payload(payload, clean_query)


def classify_cam_evidence(
    request: BriefRequest,
    results: list[object],
    *,
    target_language: str | None = None,
    analogy_rationales: dict[str, str] | None = None,
) -> tuple[EvidenceItem, ...]:
    """Label each included CAM result as direct or an explained analogy."""

    if not isinstance(request, BriefRequest):
        raise BriefValidationError("request must be a BriefRequest")
    target_terms = _terms(request.task_text)
    language = target_language.strip().lower() if target_language and target_language.strip() else None
    rationales = analogy_rationales or {}
    items: list[EvidenceItem] = []

    for result in results:
        if not isinstance(result, dict):
            raise BriefValidationError("CAM evidence result must be an object")
        methodology_id = result.get("methodology_id")
        description = result.get("problem_description")
        notes = result.get("methodology_notes")
        tags = result.get("tags")
        result_language = result.get("language")
        if not isinstance(methodology_id, str) or not isinstance(description, str):
            raise BriefValidationError("CAM evidence result is missing method provenance")
        if not isinstance(notes, str) or not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise BriefValidationError("CAM evidence result is malformed")
        result_terms = _terms(" ".join([description, notes, *tags]))
        overlapping_terms = sorted(target_terms & result_terms)
        same_language = language is not None and isinstance(result_language, str) and result_language.lower() == language

        if same_language and overlapping_terms:
            items.append(
                EvidenceItem(
                    evidence_class=EvidenceClass.DIRECT_PRECEDENT,
                    title=description,
                    source_id=methodology_id,
                    source_kind="cam_methodology",
                    why_it_applies=(
                        f"It shares the {language} target stack and task terms: "
                        f"{', '.join(overlapping_terms[:4])}."
                    ),
                    confidence=Confidence.MEDIUM,
                    limitation="Inspect the cited source before reusing it in this target.",
                )
            )
            continue

        rationale = rationales.get(methodology_id)
        if rationale:
            items.append(
                EvidenceItem(
                    evidence_class=EvidenceClass.TRANSFERABLE_ANALOGY,
                    title=description,
                    source_id=methodology_id,
                    source_kind="cam_methodology",
                    why_it_applies=_required_text(rationale, "transfer rationale"),
                    confidence=Confidence.LOW,
                    limitation="This is a transferable analogy, not a drop-in implementation.",
                )
            )

    return tuple(items)


def new_hypothesis(
    *,
    title: str,
    why_it_applies: str,
    validation_needed: str,
) -> EvidenceItem:
    """Represent a novel direction without misrepresenting it as recalled work."""

    clean_title = _required_text(title, "hypothesis title")
    source_id = "hypothesis:" + "-".join(_TERM_PATTERN.findall(clean_title.lower()))
    return EvidenceItem(
        evidence_class=EvidenceClass.NEW_HYPOTHESIS,
        title=clean_title,
        source_id=source_id,
        source_kind="development_brief_hypothesis",
        why_it_applies=_required_text(why_it_applies, "hypothesis rationale"),
        confidence=Confidence.LOW,
        limitation=f"Needs validation: {_required_text(validation_needed, 'hypothesis validation')}",
    )


def suggest_explicit_expansions(evidence_items: tuple[EvidenceItem, ...]) -> tuple[NextStep, ...]:
    """Offer a named-scope expansion only when default-scope evidence is thin."""

    if evidence_items:
        return ()
    return (
        NextStep(
            kind="request_named_source_scope",
            summary="Name local source folders to consider for a later scan-only expansion.",
        ),
    )


def _target_evidence_from_inspection(inspection: TargetInspection | None) -> tuple[TargetEvidence, ...]:
    if inspection is None:
        return ()
    evidence: list[TargetEvidence] = []
    if inspection.read_truth_files:
        evidence.append(
            TargetEvidence(
                category="repository truth",
                summary=f"Read: {', '.join(inspection.read_truth_files)}.",
                source_path=str(inspection.target_path),
            )
        )
    if inspection.is_git_repository:
        branch = inspection.branch or "unknown branch"
        summary = f"Git repository on {branch}; {len(inspection.dirty_entries)} dirty entry(s)."
        evidence.append(TargetEvidence(category="git state", summary=summary, source_path=str(inspection.target_path)))
    for gap in inspection.visible_gaps[:5]:
        evidence.append(TargetEvidence(category="visible gap", summary=gap, source_path=str(inspection.target_path)))
    for risk in inspection.risks:
        evidence.append(TargetEvidence(category="inspection risk", summary=risk, source_path=str(inspection.target_path)))
    return tuple(evidence)


def _infer_target_language(task_text: str, explicit_language: str | None) -> str | None:
    if explicit_language and explicit_language.strip():
        return explicit_language.strip().lower()
    task_terms = _terms(task_text)
    for language in ("python", "typescript", "javascript", "rust", "go", "swift", "java", "kotlin"):
        if language in task_terms:
            return language
    return None


def build_development_brief(
    request: BriefRequest,
    *,
    cam_command: Path,
    cam_database: Path,
    target_path: Path | None = None,
    limit: int = 5,
    target_language: str | None = None,
    analogy_rationales: dict[str, str] | None = None,
) -> DevelopmentBrief:
    """Assemble a read-only brief from one target and the primary CAM corpus."""

    inspection = inspect_target_read_only(target_path) if target_path is not None else None
    payload = query_primary_corpus_read_only(
        request.task_text,
        cam_command=cam_command,
        cam_database=cam_database,
        limit=limit,
    )
    evidence_items = classify_cam_evidence(
        request,
        payload["results"],
        target_language=_infer_target_language(request.task_text, target_language),
        analogy_rationales=analogy_rationales,
    )
    limitations = [
        "CAM recall used the explicitly supplied primary corpus only; it did not query federated siblings.",
        "Repository verification was not run by this brief.",
    ]
    optional_next_steps = suggest_explicit_expansions(evidence_items)

    if request.mode == "continue-rescue":
        if inspection is None:
            raise BriefValidationError("continue-rescue mode requires --target-repo")
        advice = recommend_continue_rescue(inspection)
        limitations.append(advice.limitation)
        return DevelopmentBrief(
            request=request,
            target_evidence=_target_evidence_from_inspection(inspection),
            evidence_items=evidence_items,
            recommendation=f"Recommended action: {advice.action}. " + " ".join(advice.reasons),
            recommended_next_step=advice.recommended_next_step,
            optional_next_steps=optional_next_steps,
            limitations=tuple(limitations),
        )

    if evidence_items:
        first = evidence_items[0]
        recommendation = "Start by inspecting the strongest labelled precedent before adapting any implementation."
        next_step = NextStep(
            kind="inspect_source",
            summary=f"Inspect CAM methodology {first.source_id} and create a bounded target plan.",
        )
    else:
        recommendation = "Default-scope recall is thin; define the smallest target plan before expanding search scope."
        next_step = NextStep(
            kind="create_plan",
            summary="Create a small goal and implementation plan with a first verification check.",
        )
    return DevelopmentBrief(
        request=request,
        target_evidence=_target_evidence_from_inspection(inspection),
        evidence_items=evidence_items,
        recommendation=recommendation,
        recommended_next_step=next_step,
        optional_next_steps=optional_next_steps,
        limitations=tuple(limitations),
    )


def _parse_analogy_rationales(values: list[str]) -> dict[str, str]:
    rationales: dict[str, str] = {}
    for value in values:
        methodology_id, separator, rationale = value.partition("=")
        if not separator:
            raise BriefValidationError("--analogy-rationale must use METHODOLOGY_ID=RATIONALE")
        rationales[_required_text(methodology_id, "analogy methodology id")] = _required_text(
            rationale, "analogy rationale"
        )
    return rationales


def _write_explicit_output(markdown: str, output_path: Path, target_path: Path | None) -> Path:
    destination = output_path.expanduser().resolve()
    if target_path is not None:
        target = target_path.expanduser().resolve()
        try:
            destination.relative_to(target)
        except ValueError:
            pass
        else:
            raise BriefValidationError("--output must be outside --target-repo to preserve the read-only target default")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markdown, encoding="utf-8")
    return destination


def render_markdown(brief: DevelopmentBrief) -> str:
    """Render a concise Development Brief without performing any I/O."""

    lines = [
        "# Development Brief",
        "",
        f"**Mode:** {brief.request.mode}",
        f"**Task:** {brief.request.task_text}",
        "**Scope:** Named target plus existing CAM primary knowledge only; no mutation performed.",
        "",
        "## Target evidence",
    ]
    if brief.target_evidence:
        for item in brief.target_evidence:
            origin = f" (`{item.source_path}`)" if item.source_path else ""
            lines.append(f"- **{item.category}:** {item.summary}{origin}")
    else:
        lines.append("- No target evidence was collected.")

    lines.extend(["", "## Evidence"])
    if brief.evidence_items:
        for item in brief.evidence_items:
            lines.extend(
                [
                    f"### {_EVIDENCE_LABELS[item.evidence_class]}: {item.title}",
                    f"- Source: `{item.source_kind}:{item.source_id}`",
                    f"- Why this applies: {item.why_it_applies}",
                    f"- Confidence: {item.confidence.value}",
                    f"- Limitation: {item.limitation}",
                    "",
                ]
            )
    else:
        lines.append("- No CAM evidence retrieved.")

    lines.extend(
        [
            "",
            "## Recommendation",
            brief.recommendation,
            "",
            "## Recommended next step",
            f"- **{brief.recommended_next_step.kind}:** {brief.recommended_next_step.summary}",
            "",
            "## Limitations",
        ]
    )
    if brief.limitations:
        lines.extend(f"- {item}" for item in brief.limitations)
    else:
        lines.append("- No additional limitations recorded.")

    if brief.optional_next_steps:
        lines.extend(["", "## Optional explicit next steps"])
        lines.extend(f"- **{item.kind}:** {item.summary}" for item in brief.optional_next_steps)

    return "\n".join(lines).rstrip() + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Development Brief from a named target and existing primary CAM knowledge; "
            "no mutation, mining, provider call, or test execution occurs by default."
        )
    )
    parser.add_argument("mode", choices=("new", "continue-rescue"), help="Brief mode")
    parser.add_argument("--task", required=True, help="Plain-language development request")
    parser.add_argument("--target-repo", type=Path, help="Explicit target repository; required for continue-rescue")
    parser.add_argument("--cam-command", type=Path, required=True, help="Absolute path to CAM's executable")
    parser.add_argument("--cam-db", type=Path, required=True, help="Absolute path to CAM's primary claw.db")
    parser.add_argument("--limit", type=int, default=5, help="Maximum primary-corpus methods to inspect")
    parser.add_argument("--target-language", help="Optional target language hint")
    parser.add_argument(
        "--analogy-rationale",
        action="append",
        default=[],
        metavar="METHODOLOGY_ID=RATIONALE",
        help="Explicit reason a dissimilar method transfers to this target",
    )
    parser.add_argument("--output", type=Path, help="Explicit Markdown output path outside the target repository")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Render a Development Brief to stdout or one explicit output file."""

    args = _parser().parse_args(argv)
    try:
        brief = build_development_brief(
            BriefRequest(mode=args.mode, task_text=args.task),
            cam_command=args.cam_command,
            cam_database=args.cam_db,
            target_path=args.target_repo,
            limit=args.limit,
            target_language=args.target_language,
            analogy_rationales=_parse_analogy_rationales(args.analogy_rationale),
        )
        markdown = render_markdown(brief)
        if args.output is None:
            print(markdown, end="")
        else:
            output = _write_explicit_output(markdown, args.output, args.target_repo)
            print(f"Wrote Development Brief: {output}")
        return 0
    except BriefValidationError as exc:
        print(f"Development Brief error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
