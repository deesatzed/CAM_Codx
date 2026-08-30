"""Deterministic target-aware ordering and abstention for opportunity records.

The score in this module orders human inspection candidates only. It cannot
confer implementation, target-value, or outcome status on a retrieved record.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field, replace
import hashlib
import json
import math
from types import MappingProxyType
from typing import Literal, Mapping
import re
import unicodedata

from tools.opportunity_brief import (
    AcquisitionReceipt,
    NeedTheme,
    OpportunityCandidate,
    OpportunityRecordReceipt,
)


MINIMUM_SELECTION_SCORE = 0.48
MAXIMUM_SELECTION = 5
MAXIMUM_NEEDS = 7
MAXIMUM_CANDIDATES = 140
MAXIMUM_TEXT = 256 * 1024
MAXIMUM_TOKENS = 4_096
MAXIMUM_PUBLIC_TEXT = 4_096
MAXIMUM_RRF = 2.0 / 61.0

GENERIC_MATCH_TOKENS = frozenset({"agent", "build", "context", "handoff", "system"})

Disposition = Literal["selected", "rejected"]
DispositionReason = Literal[
    "selected",
    "selected_negative_lesson",
    "not_relevant_to_need",
    "boundary_conflict",
    "not_additive_to_handoff",
    "below_minimum_score",
    "equivalent_mechanism",
    "source_diversity",
    "selection_limit",
]

_TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
_NEED_ID_PATTERN = re.compile(r"need_[0-9a-f]{24}")
_MECHANISM_ID_PATTERN = re.compile(r"mechanism_[0-9a-f]{24}")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")
_BOUNDARY_CONFLICT_CUES = frozenset(
    {
        "cannot",
        "exclude",
        "exclud",
        "inapplicable",
        "never",
        "no",
        "not",
        "outside",
        "unrelat",
        "without",
    }
)
_STOP_TOKENS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "here",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "source",
        "grounded",
        "the",
        "this",
        "to",
        "transferable",
        "with",
    }
)


@dataclass(frozen=True, slots=True)
class ScoreComponents:
    """Every bounded input to the fixed inspection-ordering formula."""

    normalized_rrf: float
    need_relevance: float
    additive_beyond_handoff: float
    evidence_quality: float
    cross_context_transfer: float
    generic_match_penalty: float
    redundancy_penalty: float

    def __post_init__(self) -> None:
        for field in (
            "normalized_rrf",
            "need_relevance",
            "additive_beyond_handoff",
            "evidence_quality",
            "cross_context_transfer",
            "generic_match_penalty",
            "redundancy_penalty",
        ):
            value = getattr(self, field)
            if type(value) is not float or not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{field} must be a finite float in [0, 1]")


@dataclass(frozen=True, slots=True)
class RankedOpportunity:
    """One candidate with its complete score and auditable disposition."""

    record_id: str
    record: OpportunityRecordReceipt
    matched_need_ids: tuple[str, ...]
    equivalent_mechanism_id: str
    components: ScoreComponents
    ranking_score: float
    disposition: Disposition
    reason: DispositionReason
    inference: str
    _integrity: str = dataclass_field(repr=False, compare=False, default="")

    def __post_init__(self) -> None:
        _validate_record_id(self.record_id)
        _validate_record(self.record)
        if self.record_id != _record_id(self.record):
            raise ValueError("record_id does not match the canonical record")
        _validate_string_tuple(
            self.matched_need_ids,
            field="matched_need_ids",
            maximum=MAXIMUM_NEEDS,
        )
        if not self.matched_need_ids or any(
            _NEED_ID_PATTERN.fullmatch(need_id) is None
            for need_id in self.matched_need_ids
        ):
            raise ValueError("matched_need_ids are malformed")
        if _MECHANISM_ID_PATTERN.fullmatch(self.equivalent_mechanism_id) is None:
            raise ValueError("equivalent_mechanism_id is malformed")
        if type(self.components) is not ScoreComponents:
            raise TypeError("components must be ScoreComponents")
        self.components.__post_init__()
        expected = _ranking_score(self.components)
        if type(self.ranking_score) is not float or not math.isclose(
            self.ranking_score,
            expected,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise ValueError("ranking_score does not match its components")
        if self.disposition not in {"selected", "rejected"}:
            raise ValueError("disposition is unsupported")
        selected_reason = self.reason in {"selected", "selected_negative_lesson"}
        if selected_reason != (self.disposition == "selected"):
            raise ValueError("disposition and reason disagree")
        _checked_text(self.inference, field="inference", limit=MAXIMUM_PUBLIC_TEXT)
        if _DIGEST_PATTERN.fullmatch(self._integrity) is None or self._integrity != (
            _ranked_integrity(
                record_id=self.record_id,
                record=self.record,
                matched_need_ids=self.matched_need_ids,
                mechanism_id=self.equivalent_mechanism_id,
                components=self.components,
                score=self.ranking_score,
                disposition=self.disposition,
                reason=self.reason,
                inference=self.inference,
            )
        ):
            raise ValueError("ranked opportunity canonical integrity mismatch")

    @property
    def source_repo_id(self) -> str:
        return self.record.evidence.source_repo_id

    @property
    def source_repo_name(self) -> str:
        return self.record.evidence.source_repo_name


@dataclass(frozen=True, slots=True)
class MechanismAudit:
    mechanism_id: str
    record_ids: tuple[str, ...]
    selected_record_id: str | None

    def __post_init__(self) -> None:
        if not self.mechanism_id.startswith("mechanism_"):
            raise ValueError("mechanism_id is malformed")
        _validate_string_tuple(self.record_ids, field="record_ids", maximum=MAXIMUM_CANDIDATES)
        if not self.record_ids:
            raise ValueError("mechanism audit must contain a record")
        if self.selected_record_id is not None and self.selected_record_id not in self.record_ids:
            raise ValueError("selected mechanism record is outside its group")


@dataclass(frozen=True, slots=True)
class SourceAudit:
    source_repo_id: str
    source_repo_name: str
    candidate_record_ids: tuple[str, ...]
    selected_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _checked_text(self.source_repo_id, field="source_repo_id", limit=256)
        _checked_text(self.source_repo_name, field="source_repo_name", limit=256)
        _validate_string_tuple(
            self.candidate_record_ids,
            field="candidate_record_ids",
            maximum=MAXIMUM_CANDIDATES,
        )
        _validate_string_tuple(
            self.selected_record_ids,
            field="selected_record_ids",
            maximum=MAXIMUM_SELECTION,
        )
        if not set(self.selected_record_ids).issubset(self.candidate_record_ids):
            raise ValueError("selected source records must be candidates")


@dataclass(frozen=True, slots=True)
class NeedAudit:
    need_id: str
    problem: str
    candidate_record_ids: tuple[str, ...]
    selected_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _checked_text(self.need_id, field="need_id", limit=69)
        _checked_text(self.problem, field="need problem", limit=MAXIMUM_PUBLIC_TEXT)
        _validate_string_tuple(
            self.candidate_record_ids,
            field="candidate_record_ids",
            maximum=MAXIMUM_CANDIDATES,
        )
        _validate_string_tuple(
            self.selected_record_ids,
            field="selected_record_ids",
            maximum=MAXIMUM_SELECTION,
        )
        if not set(self.selected_record_ids).issubset(self.candidate_record_ids):
            raise ValueError("selected need records must be candidates")


@dataclass(frozen=True, slots=True)
class RankingResult:
    """Complete immutable selection receipt, including every rejection."""

    minimum_score: float
    maximum: int
    selected: tuple[RankedOpportunity, ...]
    rejected: tuple[RankedOpportunity, ...]
    dispositions: tuple[RankedOpportunity, ...]
    mechanism_audit: tuple[MechanismAudit, ...]
    source_audit: tuple[SourceAudit, ...]
    need_audit: tuple[NeedAudit, ...]
    _integrity: str = dataclass_field(repr=False, compare=False, default="")

    def __post_init__(self) -> None:
        if type(self.minimum_score) is not float or self.minimum_score != MINIMUM_SELECTION_SCORE:
            raise ValueError("minimum_score must equal the frozen fixture threshold")
        _validate_maximum(self.maximum)
        _validate_typed_tuple(
            self.selected,
            field="selected",
            item_type=RankedOpportunity,
            maximum=self.maximum,
        )
        _validate_typed_tuple(
            self.rejected,
            field="rejected",
            item_type=RankedOpportunity,
            maximum=MAXIMUM_CANDIDATES,
        )
        _validate_typed_tuple(
            self.dispositions,
            field="dispositions",
            item_type=RankedOpportunity,
            maximum=MAXIMUM_CANDIDATES,
        )
        _validate_typed_tuple(
            self.mechanism_audit,
            field="mechanism_audit",
            item_type=MechanismAudit,
            maximum=MAXIMUM_CANDIDATES,
        )
        _validate_typed_tuple(
            self.source_audit,
            field="source_audit",
            item_type=SourceAudit,
            maximum=MAXIMUM_CANDIDATES,
        )
        _validate_typed_tuple(
            self.need_audit,
            field="need_audit",
            item_type=NeedAudit,
            maximum=MAXIMUM_NEEDS,
        )
        if any(item.disposition != "selected" for item in self.selected):
            raise ValueError("selected contains a rejected disposition")
        if any(item.disposition != "rejected" for item in self.rejected):
            raise ValueError("rejected contains a selected disposition")
        if self.dispositions != tuple((*self.selected, *self.rejected)):
            raise ValueError("dispositions must preserve selected then rejected ordering")
        record_ids = tuple(item.record_id for item in self.dispositions)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("dispositions repeat a candidate record")
        for item in self.dispositions:
            item.__post_init__()
        for audit in self.mechanism_audit:
            audit.__post_init__()
        for audit in self.source_audit:
            audit.__post_init__()
        for audit in self.need_audit:
            audit.__post_init__()
        if self.mechanism_audit != _mechanism_audit_from_ranked(
            self.dispositions,
            {item.record_id for item in self.selected},
        ):
            raise ValueError("mechanism audit is not canonical")
        if self.source_audit != _source_audit_from_ranked(
            self.dispositions,
            {item.record_id for item in self.selected},
        ):
            raise ValueError("source audit is not canonical")
        _validate_need_audit_relations(self)
        if _DIGEST_PATTERN.fullmatch(self._integrity) is None or self._integrity != (
            _result_integrity(
                minimum_score=self.minimum_score,
                maximum=self.maximum,
                selected=self.selected,
                rejected=self.rejected,
                mechanism_audit=self.mechanism_audit,
                source_audit=self.source_audit,
                need_audit=self.need_audit,
            )
        ):
            raise ValueError("ranking result canonical integrity mismatch")

    @property
    def rejected_by_source(self) -> Mapping[str, RankedOpportunity]:
        values: dict[str, RankedOpportunity] = {}
        for item in self.rejected:
            values.setdefault(item.source_repo_name, item)
        return MappingProxyType(values)


@dataclass(frozen=True, slots=True)
class _ScoredCandidate:
    candidate: object
    matched_need_ids: tuple[str, ...]
    best_need: object | None
    mechanism_id: str
    components: ScoreComponents
    score: float
    initial_reason: DispositionReason | None


def rank_and_select(
    needs: tuple[NeedTheme, ...],
    handoff_text: str,
    acquired: AcquisitionReceipt,
    *,
    maximum: int = MAXIMUM_SELECTION,
) -> RankingResult:
    """Order source-grounded candidates and honestly abstain when none fit."""

    checked_needs = _validate_needs(needs)
    handoff = _checked_text(handoff_text, field="handoff_text", limit=MAXIMUM_TEXT)
    _validate_maximum(maximum)
    if type(acquired) is not AcquisitionReceipt:
        raise TypeError("acquired must be an exact AcquisitionReceipt")
    acquired.__post_init__()
    expected_calls = tuple(
        (need.need_id, need.query_text)
        for need in checked_needs
    )
    actual_calls = tuple((call.need_id, call.query) for call in acquired.calls)
    if actual_calls != expected_calls:
        raise ValueError("needs must exactly match acquisition calls and queries")
    candidates = acquired.candidates
    if len(candidates) > MAXIMUM_CANDIDATES:
        raise ValueError("acquired candidates exceed their bound")

    handoff_terms = _token_set(handoff)
    handoff_spans = _handoff_term_spans(handoff)
    needs_by_id = {need.need_id: need for need in checked_needs}
    scored = tuple(
        _score_candidate(
            candidate,
            needs_by_id,
            handoff_terms,
            handoff_spans,
        )
        for candidate in candidates
    )
    scored = _group_equivalent_mechanisms(scored)
    selected_scored, rejected_reasons = _select(scored, maximum)
    selected_ids = {item.candidate.record_id for item in selected_scored}

    selected = tuple(
        _to_ranked(item, disposition="selected", reason=_selected_reason(item))
        for item in selected_scored
    )
    rejected = tuple(
        _to_ranked(
            item,
            disposition="rejected",
            reason=rejected_reasons[item.candidate.record_id],
        )
        for item in scored
        if item.candidate.record_id not in selected_ids
    )
    dispositions = (*selected, *rejected)
    mechanism_audit = _mechanism_audit(scored, selected_ids)
    source_audit = _source_audit(scored, selected_ids)
    need_audit = _need_audit(checked_needs, scored, selected_ids)
    integrity = _result_integrity(
        minimum_score=MINIMUM_SELECTION_SCORE,
        maximum=maximum,
        selected=selected,
        rejected=rejected,
        mechanism_audit=mechanism_audit,
        source_audit=source_audit,
        need_audit=need_audit,
    )
    return RankingResult(
        minimum_score=MINIMUM_SELECTION_SCORE,
        maximum=maximum,
        selected=selected,
        rejected=rejected,
        dispositions=dispositions,
        mechanism_audit=mechanism_audit,
        source_audit=source_audit,
        need_audit=need_audit,
        _integrity=integrity,
    )


def _score_candidate(
    candidate: OpportunityCandidate,
    needs_by_id: dict[str, NeedTheme],
    handoff_terms: frozenset[str],
    handoff_spans: tuple[frozenset[str], ...],
) -> _ScoredCandidate:
    _validate_candidate(candidate)
    matched_need_ids = tuple(match.need_id for match in candidate.matches)
    if any(need_id not in needs_by_id for need_id in matched_need_ids):
        raise ValueError("candidate match does not identify a requested need")
    matched_needs = tuple(needs_by_id[need_id] for need_id in matched_need_ids)
    positive_terms = _token_set(
        " ".join(
            (
                candidate.record.problem,
                candidate.record.mechanism,
                candidate.record.context,
            )
        )
    )
    match_by_need = {match.need_id: match for match in candidate.matches}
    ranked_need_scores: list[tuple[float, int, NeedTheme, frozenset[str]]] = []
    conflicts: set[str] = set()
    for index, need in enumerate(matched_needs):
        need_terms = _need_terms(need)
        overlap = need_terms & positive_terms
        discriminative = overlap - GENERIC_MATCH_TOKENS
        denominator = max(1, min(len(need_terms - GENERIC_MATCH_TOKENS), 8))
        relevance = _bounded(len(discriminative) / denominator)
        ranked_need_scores.append((relevance, -index, need, overlap))
        if _boundary_conflicts(candidate.record.boundary, need_terms):
            conflicts.add(need.need_id)
    _relevance, _order, best_need, overlap = max(
        ranked_need_scores,
        default=(0.0, 0, None, frozenset()),
        key=lambda item: (item[0], item[1]),
    )
    relevance = float(_relevance)
    mechanism_terms = _token_set(candidate.record.mechanism) - GENERIC_MATCH_TOKENS
    support_terms = (
        _need_terms(best_need)
        | _token_set(candidate.record.problem)
        | _token_set(candidate.record.context)
        if best_need is not None
        else frozenset()
    )
    source_supported = _source_supported_mechanism_terms(
        candidate.record.mechanism,
        support_terms,
    )
    novel_supported = source_supported - handoff_terms
    additive = _bounded(
        relevance * len(novel_supported) / max(1, len(mechanism_terms))
    )
    redundancy = max(
        (
            len(mechanism_terms & span_terms)
            / max(1, min(len(mechanism_terms), len(span_terms)))
            for span_terms in handoff_spans
            if span_terms
        ),
        default=0.0,
    )
    generic_penalty = 1.0 if overlap and not (overlap - GENERIC_MATCH_TOKENS) else 0.0
    conflict = bool(conflicts)
    transfer = 0.0 if conflict else relevance
    match = match_by_need.get(best_need.need_id) if best_need is not None else None
    normalized_rrf = 0.0 if match is None else _bounded(match.rrf_score / MAXIMUM_RRF)
    components = ScoreComponents(
        normalized_rrf=float(normalized_rrf),
        need_relevance=float(relevance),
        additive_beyond_handoff=float(additive),
        evidence_quality=float(_evidence_quality(candidate.record)),
        cross_context_transfer=float(transfer),
        generic_match_penalty=float(generic_penalty),
        redundancy_penalty=float(_bounded(redundancy)),
    )
    score = _ranking_score(components)
    reason: DispositionReason | None = None
    if conflict:
        reason = "boundary_conflict"
    elif relevance == 0.0:
        reason = "not_relevant_to_need"
    elif additive < 0.12 or redundancy >= 0.72:
        reason = "not_additive_to_handoff"
    elif score < MINIMUM_SELECTION_SCORE:
        reason = "below_minimum_score"
    return _ScoredCandidate(
        candidate=candidate,
        matched_need_ids=matched_need_ids,
        best_need=best_need,
        mechanism_id=_mechanism_id(candidate.record),
        components=components,
        score=score,
        initial_reason=reason,
    )


def _select(
    scored: tuple[_ScoredCandidate, ...],
    maximum: int,
) -> tuple[tuple[_ScoredCandidate, ...], dict[str, DispositionReason]]:
    reasons: dict[str, DispositionReason] = {
        item.candidate.record_id: item.initial_reason
        for item in scored
        if item.initial_reason is not None
    }
    eligible = [item for item in scored if item.initial_reason is None]
    eligible.sort(
        key=lambda item: (
            -item.score,
            item.candidate.record.evidence.source_repo_name.casefold(),
            item.candidate.record_id,
        )
    )
    leaders: list[_ScoredCandidate] = []
    seen_mechanisms: set[str] = set()
    for item in eligible:
        if item.mechanism_id in seen_mechanisms:
            reasons[item.candidate.record_id] = "equivalent_mechanism"
            continue
        seen_mechanisms.add(item.mechanism_id)
        leaders.append(item)
    eligible_mechanisms = {item.mechanism_id for item in eligible}
    leader_ids = {item.candidate.record_id for item in leaders}
    for item in scored:
        if (
            item.mechanism_id in eligible_mechanisms
            and item.candidate.record_id not in leader_ids
            and item.initial_reason in {"not_additive_to_handoff", "below_minimum_score"}
        ):
            reasons[item.candidate.record_id] = "equivalent_mechanism"

    selected: list[_ScoredCandidate] = []
    deferred: list[_ScoredCandidate] = []
    selected_sources: set[str] = set()
    for item in leaders:
        source_id = item.candidate.record.evidence.source_repo_id
        if source_id in selected_sources:
            deferred.append(item)
            continue
        if len(selected) == maximum:
            reasons[item.candidate.record_id] = "selection_limit"
            continue
        selected.append(item)
        selected_sources.add(source_id)
    for item in deferred:
        if len(selected) < maximum:
            selected.append(item)
        else:
            reasons[item.candidate.record_id] = "source_diversity"
    selected.sort(
        key=lambda item: (
            -item.score,
            item.candidate.record.evidence.source_repo_name.casefold(),
            item.candidate.record_id,
        )
    )
    return tuple(selected), reasons


def _to_ranked(
    item: _ScoredCandidate,
    *,
    disposition: Disposition,
    reason: DispositionReason,
) -> RankedOpportunity:
    need_problem = (
        "the recorded WIP need"
        if item.best_need is None
        else item.best_need.problem
    )
    if item.candidate.record.observed_effect.status == "negative":
        inference = (
            f"The source-grounded negative lesson overlaps the need '{need_problem}'. "
            "Its target relevance remains an unverified inspection hypothesis."
        )
    else:
        inference = (
            f"The source-grounded mechanism overlaps the need '{need_problem}'. "
            "Its target fit remains an unverified inspection hypothesis."
        )
    integrity = _ranked_integrity(
        record_id=item.candidate.record_id,
        record=item.candidate.record,
        matched_need_ids=item.matched_need_ids,
        mechanism_id=item.mechanism_id,
        components=item.components,
        score=item.score,
        disposition=disposition,
        reason=reason,
        inference=inference,
    )
    return RankedOpportunity(
        record_id=item.candidate.record_id,
        record=item.candidate.record,
        matched_need_ids=item.matched_need_ids,
        equivalent_mechanism_id=item.mechanism_id,
        components=item.components,
        ranking_score=item.score,
        disposition=disposition,
        reason=reason,
        inference=inference,
        _integrity=integrity,
    )


def _selected_reason(item: _ScoredCandidate) -> DispositionReason:
    if item.candidate.record.observed_effect.status == "negative":
        return "selected_negative_lesson"
    return "selected"


def _mechanism_audit(
    scored: tuple[_ScoredCandidate, ...],
    selected_ids: set[str],
) -> tuple[MechanismAudit, ...]:
    groups: dict[str, list[str]] = {}
    for item in scored:
        groups.setdefault(item.mechanism_id, []).append(item.candidate.record_id)
    return tuple(
        MechanismAudit(
            mechanism_id=mechanism_id,
            record_ids=tuple(sorted(record_ids)),
            selected_record_id=next(
                (record_id for record_id in sorted(record_ids) if record_id in selected_ids),
                None,
            ),
        )
        for mechanism_id, record_ids in sorted(groups.items())
    )


def _source_audit(
    scored: tuple[_ScoredCandidate, ...],
    selected_ids: set[str],
) -> tuple[SourceAudit, ...]:
    sources: dict[str, tuple[str, list[str]]] = {}
    for item in scored:
        evidence = item.candidate.record.evidence
        prior = sources.setdefault(evidence.source_repo_id, (evidence.source_repo_name, []))
        if prior[0] != evidence.source_repo_name:
            raise ValueError("one source_repo_id has conflicting names")
        prior[1].append(item.candidate.record_id)
    return tuple(
        SourceAudit(
            source_repo_id=source_id,
            source_repo_name=name,
            candidate_record_ids=tuple(sorted(record_ids)),
            selected_record_ids=tuple(
                record_id for record_id in sorted(record_ids) if record_id in selected_ids
            ),
        )
        for source_id, (name, record_ids) in sorted(sources.items())
    )


def _need_audit(
    needs: tuple[object, ...],
    scored: tuple[_ScoredCandidate, ...],
    selected_ids: set[str],
) -> tuple[NeedAudit, ...]:
    return tuple(
        NeedAudit(
            need_id=need.need_id,
            problem=need.problem,
            candidate_record_ids=tuple(
                sorted(
                    item.candidate.record_id
                    for item in scored
                    if need.need_id in item.matched_need_ids
                )
            ),
            selected_record_ids=tuple(
                sorted(
                    item.candidate.record_id
                    for item in scored
                    if need.need_id in item.matched_need_ids
                    and item.candidate.record_id in selected_ids
                )
            ),
        )
        for need in needs
    )


def _mechanism_audit_from_ranked(
    dispositions: tuple[RankedOpportunity, ...],
    selected_ids: set[str],
) -> tuple[MechanismAudit, ...]:
    groups: dict[str, list[str]] = {}
    for item in dispositions:
        groups.setdefault(item.equivalent_mechanism_id, []).append(item.record_id)
    return tuple(
        MechanismAudit(
            mechanism_id=mechanism_id,
            record_ids=tuple(sorted(record_ids)),
            selected_record_id=next(
                (
                    record_id
                    for record_id in sorted(record_ids)
                    if record_id in selected_ids
                ),
                None,
            ),
        )
        for mechanism_id, record_ids in sorted(groups.items())
    )


def _source_audit_from_ranked(
    dispositions: tuple[RankedOpportunity, ...],
    selected_ids: set[str],
) -> tuple[SourceAudit, ...]:
    sources: dict[str, tuple[str, list[str]]] = {}
    for item in dispositions:
        evidence = item.record.evidence
        prior = sources.setdefault(
            evidence.source_repo_id,
            (evidence.source_repo_name, []),
        )
        if prior[0] != evidence.source_repo_name:
            raise ValueError("one source_repo_id has conflicting names")
        prior[1].append(item.record_id)
    return tuple(
        SourceAudit(
            source_repo_id=source_id,
            source_repo_name=name,
            candidate_record_ids=tuple(sorted(record_ids)),
            selected_record_ids=tuple(
                record_id
                for record_id in sorted(record_ids)
                if record_id in selected_ids
            ),
        )
        for source_id, (name, record_ids) in sorted(sources.items())
    )


def _validate_need_audit_relations(result: RankingResult) -> None:
    audit_ids = tuple(audit.need_id for audit in result.need_audit)
    if len(audit_ids) != len(set(audit_ids)):
        raise ValueError("need audit repeats a need")
    audit_by_id = {audit.need_id: audit for audit in result.need_audit}
    disposition_need_ids = {
        need_id
        for item in result.dispositions
        for need_id in item.matched_need_ids
    }
    if not disposition_need_ids.issubset(audit_by_id):
        raise ValueError("need audit omits a candidate need")
    selected_ids = {item.record_id for item in result.selected}
    for audit in result.need_audit:
        expected_candidates = tuple(
            sorted(
                item.record_id
                for item in result.dispositions
                if audit.need_id in item.matched_need_ids
            )
        )
        expected_selected = tuple(
            record_id
            for record_id in expected_candidates
            if record_id in selected_ids
        )
        if (
            audit.candidate_record_ids != expected_candidates
            or audit.selected_record_ids != expected_selected
        ):
            raise ValueError("need audit relations are not canonical")
    if any(
        not any(item.record_id in audit.selected_record_ids for audit in result.need_audit)
        for item in result.selected
    ):
        raise ValueError("a selected record is absent from selected need audit")


def _ranked_integrity(
    *,
    record_id: str,
    record: OpportunityRecordReceipt,
    matched_need_ids: tuple[str, ...],
    mechanism_id: str,
    components: ScoreComponents,
    score: float,
    disposition: Disposition,
    reason: DispositionReason,
    inference: str,
) -> str:
    payload = {
        "components": _components_projection(components),
        "disposition": disposition,
        "inference": inference,
        "matched_need_ids": list(matched_need_ids),
        "mechanism_id": mechanism_id,
        "ranking_score": score,
        "reason": reason,
        "record": record.to_mapping(),
        "record_id": record_id,
        "schema": "ranked-opportunity-v2",
    }
    return _canonical_digest(payload)


def _result_integrity(
    *,
    minimum_score: float,
    maximum: int,
    selected: tuple[RankedOpportunity, ...],
    rejected: tuple[RankedOpportunity, ...],
    mechanism_audit: tuple[MechanismAudit, ...],
    source_audit: tuple[SourceAudit, ...],
    need_audit: tuple[NeedAudit, ...],
) -> str:
    payload = {
        "maximum": maximum,
        "minimum_score": minimum_score,
        "selected": [item._integrity for item in selected],
        "rejected": [item._integrity for item in rejected],
        "mechanism_audit": [
            {
                "mechanism_id": audit.mechanism_id,
                "record_ids": list(audit.record_ids),
                "selected_record_id": audit.selected_record_id,
            }
            for audit in mechanism_audit
        ],
        "source_audit": [
            {
                "candidate_record_ids": list(audit.candidate_record_ids),
                "selected_record_ids": list(audit.selected_record_ids),
                "source_repo_id": audit.source_repo_id,
                "source_repo_name": audit.source_repo_name,
            }
            for audit in source_audit
        ],
        "need_audit": [
            {
                "candidate_record_ids": list(audit.candidate_record_ids),
                "need_id": audit.need_id,
                "problem": audit.problem,
                "selected_record_ids": list(audit.selected_record_ids),
            }
            for audit in need_audit
        ],
        "schema": "ranking-result-v2",
    }
    return _canonical_digest(payload)


def _components_projection(components: ScoreComponents) -> dict[str, float]:
    return {
        "additive_beyond_handoff": components.additive_beyond_handoff,
        "cross_context_transfer": components.cross_context_transfer,
        "evidence_quality": components.evidence_quality,
        "generic_match_penalty": components.generic_match_penalty,
        "need_relevance": components.need_relevance,
        "normalized_rrf": components.normalized_rrf,
        "redundancy_penalty": components.redundancy_penalty,
    }


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _evidence_quality(record: object) -> float:
    evidence = record.evidence
    complete = (
        bool(evidence.source_repo_id)
        and bool(evidence.source_repo_name)
        and bool(evidence.source_revision)
        and bool(evidence.license_type)
        and bool(evidence.license_sha256)
        and bool(evidence.source_files)
        and bool(evidence.source_symbols)
        and bool(evidence.source_sha256)
        and record.evidence_state == "admitted"
        and bool(record.source_methodology_ids)
    )
    provenance = 1.0 if complete else 0.0
    status_quality = {
        "observed": 1.0,
        "intended": 0.75,
        "negative": 0.90,
    }[record.observed_effect.status]
    return _bounded(0.75 * provenance + 0.25 * status_quality)


def _ranking_score(components: ScoreComponents) -> float:
    return float(
        0.35 * components.normalized_rrf
        + 0.25 * components.need_relevance
        + 0.20 * components.additive_beyond_handoff
        + 0.15 * components.evidence_quality
        + 0.05 * components.cross_context_transfer
        - 0.20 * components.generic_match_penalty
        - 0.25 * components.redundancy_penalty
    )


def _need_terms(need: object) -> frozenset[str]:
    return _token_set(
        " ".join(
            (
                need.problem,
                need.query_text,
                need.handoff_span,
            )
        )
    )


def _mechanism_id(record: OpportunityRecordReceipt) -> str:
    mechanism_terms = _token_set(record.mechanism) - GENERIC_MATCH_TOKENS
    terms = sorted(mechanism_terms)
    identity = "\0".join(terms).encode("utf-8")
    return f"mechanism_{hashlib.sha256(identity).hexdigest()[:24]}"


def _group_equivalent_mechanisms(
    scored: tuple[_ScoredCandidate, ...],
) -> tuple[_ScoredCandidate, ...]:
    term_sets = tuple(
        _token_set(item.candidate.record.mechanism) - GENERIC_MATCH_TOKENS
        for item in scored
    )
    parents = list(range(len(scored)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = root(left)
        right_root = root(right)
        if left_root != right_root:
            parents[right_root] = left_root

    for left in range(len(scored)):
        for right in range(left + 1, len(scored)):
            smaller, larger = sorted(
                (term_sets[left], term_sets[right]),
                key=lambda terms: (len(terms), tuple(sorted(terms))),
            )
            if len(smaller) >= 3 and smaller.issubset(larger):
                union(left, right)

    groups: dict[int, list[int]] = {}
    for index in range(len(scored)):
        groups.setdefault(root(index), []).append(index)
    mechanism_ids: dict[int, str] = {}
    for indexes in groups.values():
        canonical_terms = min(
            (term_sets[index] for index in indexes),
            key=lambda terms: (len(terms), tuple(sorted(terms))),
        )
        identity = "\0".join(sorted(canonical_terms)).encode("utf-8")
        mechanism_id = f"mechanism_{hashlib.sha256(identity).hexdigest()[:24]}"
        for index in indexes:
            mechanism_ids[index] = mechanism_id
    return tuple(
        replace(item, mechanism_id=mechanism_ids[index])
        for index, item in enumerate(scored)
    )


def _source_supported_mechanism_terms(
    mechanism: str,
    support_terms: frozenset[str],
) -> frozenset[str]:
    sequence = _token_sequence(mechanism)
    supported_positions = {
        index
        for index, token in enumerate(sequence)
        if token in support_terms and token not in GENERIC_MATCH_TOKENS
    }
    admitted_positions = {
        nearby
        for position in supported_positions
        for nearby in (position - 1, position, position + 1)
        if 0 <= nearby < len(sequence)
    }
    return frozenset(
        sequence[index]
        for index in admitted_positions
        if sequence[index] not in GENERIC_MATCH_TOKENS
    )


def _handoff_term_spans(handoff: str) -> tuple[frozenset[str], ...]:
    spans: list[frozenset[str]] = []
    for line in handoff.splitlines():
        for segment in re.split(r"(?<=[.!?;])\s+", line):
            terms = _token_set(segment) - GENERIC_MATCH_TOKENS
            if terms:
                spans.append(terms)
            if len(spans) > 512:
                raise ValueError("handoff contains too many bounded spans")
    return tuple(spans)


def _boundary_conflicts(boundary: str, need_terms: frozenset[str]) -> bool:
    discriminative_need = (
        need_terms - GENERIC_MATCH_TOKENS - _BOUNDARY_CONFLICT_CUES
    )
    for sentence in re.split(r"(?<=[.!?;])\s+", boundary):
        sequence = _raw_token_sequence(sentence)
        overlap_positions = {
            index
            for index, token in enumerate(sequence)
            if token in discriminative_need
        }
        if not overlap_positions:
            continue
        cue_positions = {
            index
            for index, token in enumerate(sequence)
            if token in _BOUNDARY_CONFLICT_CUES
        }
        if any(
            abs(cue - overlap) <= 2
            for cue in cue_positions
            for overlap in overlap_positions
        ):
            return True
    return False


def _token_set(value: str) -> frozenset[str]:
    tokens = _token_sequence(value)
    if len(tokens) > MAXIMUM_TOKENS:
        raise ValueError("ranking text exceeds its token bound")
    return frozenset(tokens)


def _token_sequence(value: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in _raw_token_sequence(value)
        if token and token not in _STOP_TOKENS
    )


def _raw_token_sequence(value: str) -> tuple[str, ...]:
    normalized = _normalized_text(value)
    tokens = tuple(_stem(token) for token in _TOKEN_PATTERN.findall(normalized))
    if len(tokens) > MAXIMUM_TOKENS:
        raise ValueError("ranking text exceeds its token bound")
    return tokens


def _stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s"):
        return token[:-1]
    return token


def _normalized_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _validate_needs(needs: object) -> tuple[NeedTheme, ...]:
    if type(needs) is not tuple:
        raise TypeError("needs must be a tuple")
    if not needs or len(needs) > MAXIMUM_NEEDS:
        raise ValueError("needs must contain one to seven NeedTheme values")
    seen: set[str] = set()
    for need in needs:
        if type(need) is not NeedTheme:
            raise TypeError("needs must contain exact NeedTheme values")
        need.__post_init__()
        for field in (
            "need_id",
            "problem",
            "desired_improvement",
            "existing_evidence",
            "gap",
            "query_text",
            "handoff_span",
        ):
            _checked_text(getattr(need, field, None), field=f"need {field}", limit=MAXIMUM_PUBLIC_TEXT)
        if need.need_id in seen:
            raise ValueError("needs repeat a need_id")
        seen.add(need.need_id)
    return needs


def _validate_candidate(candidate: object) -> None:
    if type(candidate) is not OpportunityCandidate:
        raise TypeError("candidates must be exact OpportunityCandidate values")
    candidate.__post_init__()
    _validate_record_id(candidate.record_id)
    _validate_record(candidate.record)
    matches = candidate.matches
    if len(matches) > MAXIMUM_NEEDS:
        raise ValueError("candidate matches exceed the need bound")
    for match in matches:
        _checked_text(getattr(match, "need_id", None), field="match need_id", limit=69)
        score = getattr(match, "rrf_score", None)
        if type(score) is not float or not math.isfinite(score) or score <= 0.0:
            raise ValueError("candidate match RRF score is malformed")


def _validate_record(record: object) -> None:
    if type(record) is not OpportunityRecordReceipt:
        raise TypeError("record must be an exact OpportunityRecordReceipt")
    record.__post_init__()
    record.observed_effect.__post_init__()
    record.evidence.__post_init__()
    for field in ("problem", "mechanism", "context", "boundary"):
        _checked_text(getattr(record, field, None), field=f"record {field}", limit=MAXIMUM_PUBLIC_TEXT)
    effect = getattr(record, "observed_effect", None)
    if getattr(effect, "status", None) not in {"observed", "intended", "negative"}:
        raise ValueError("record observed effect status is malformed")
    _checked_text(getattr(effect, "text", None), field="record observed effect", limit=MAXIMUM_PUBLIC_TEXT)
    evidence = getattr(record, "evidence", None)
    for field in ("source_repo_id", "source_repo_name", "source_revision", "license_type"):
        _checked_text(getattr(evidence, field, None), field=f"evidence {field}", limit=MAXIMUM_PUBLIC_TEXT)


def _validate_record_id(value: object) -> None:
    checked = _checked_text(value, field="record_id", limit=36)
    if not re.fullmatch(r"opp_[0-9a-f]{32}", checked):
        raise ValueError("record_id is malformed")


def _record_id(record: OpportunityRecordReceipt) -> str:
    canonical = json.dumps(
        record.to_mapping(),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"opp_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]}"


def _checked_text(value: object, *, field: str, limit: int) -> str:
    if type(value) is not str or not value or len(value) > limit:
        raise ValueError(f"{field} is malformed")
    if "\0" in value or any(unicodedata.category(character) in {"Cc", "Cs"} and character not in "\n\r\t" for character in value):
        raise ValueError(f"{field} contains unsafe controls")
    return value


def _validate_maximum(maximum: object) -> None:
    if type(maximum) is not int or not 1 <= maximum <= MAXIMUM_SELECTION:
        raise ValueError("maximum must be an integer from 1 through 5")


def _validate_string_tuple(value: object, *, field: str, maximum: int) -> None:
    if type(value) is not tuple or len(value) > maximum:
        raise ValueError(f"{field} is malformed")
    for item in value:
        _checked_text(item, field=f"{field} item", limit=MAXIMUM_PUBLIC_TEXT)
    if value != tuple(dict.fromkeys(value)):
        raise ValueError(f"{field} must be unique")


def _validate_typed_tuple(
    value: object,
    *,
    field: str,
    item_type: type,
    maximum: int,
) -> None:
    if type(value) is not tuple or len(value) > maximum:
        raise ValueError(f"{field} is malformed")
    if any(type(item) is not item_type for item in value):
        raise TypeError(f"{field} contains an invalid item")


__all__ = [
    "GENERIC_MATCH_TOKENS",
    "MINIMUM_SELECTION_SCORE",
    "MechanismAudit",
    "NeedAudit",
    "RankedOpportunity",
    "RankingResult",
    "ScoreComponents",
    "SourceAudit",
    "rank_and_select",
]
